"""Code summarization engine + block matcher (Gemini-backed)."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


PedagogicalRole = Literal[
    "exemplo_demonstrativo",
    "exercicio_resolvido",
    "template_aluno",
    "solucao_referencia",
    "utilitario",
    "outro",
]


class CodeFileSummary(BaseModel):
    name: str
    role: str


class CodeSummary(BaseModel):
    inferred_title: str = Field(..., description="Título descritivo do conteúdo")
    language: str
    pedagogical_role: PedagogicalRole
    concepts: list[str] = Field(..., description="3-8 termos técnicos do domínio")
    summary: str = Field(..., description="2-3 linhas: o que faz, por que importa")
    files: list[CodeFileSummary] = Field(default_factory=list)


SYSTEM_INSTRUCTION = """Você analisa bundles de código acadêmico (Python, Jupyter,
Dafny, Java etc) e produz resumos estruturados em JSON.

Contexto: usuário é estudante; bundles vêm de matérias universitárias.

Sua saída alimenta um tutor LLM. Tutor precisa entender:
- O que código DEMONSTRA conceitualmente
- Qual papel pedagógico cumpre
- Que conceitos vincular ao glossário/unidades

Regras:
- inferred_title: descritivo e específico. NUNCA repita filename
  (ex: "Verificação de pré/pós-condições com Dafny", NÃO "introducao.dfy")
- concepts: 3-8 termos técnicos. Use terminologia do domínio
  (ex: "tripla de Hoare", "invariante de laço", "ghost predicate")
- summary: 2-3 frases. Foque no QUE ensina, não na sintaxe
- files: liste cada arquivo do bundle com role curto
- Responda em português brasileiro
- Saída APENAS JSON válido conforme schema"""


def _build_bundle_text(builder, entry_data: dict) -> str:
    parts = []
    parts.append(f"# Entry: {entry_data.get('title', '<sem título>')}")
    parts.append(f"Unidade: {entry_data.get('tags', '?')}")
    parts.append(f"Categoria: {entry_data.get('category', '?')}")
    parts.append("")

    base_md = entry_data.get("base_markdown")
    if base_md:
        path = builder.root_dir / base_md
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))

    for ef in entry_data.get("extracted_files") or []:
        ef_md = ef.get("base_markdown")
        if ef_md:
            path = builder.root_dir / ef_md
            if path.exists():
                parts.append(f"\n\n## Arquivo: {ef.get('title', '<sem nome>')}\n")
                parts.append(path.read_text(encoding="utf-8", errors="replace"))

    text = "\n".join(parts)
    if len(text) > 200_000:
        text = text[:200_000] + "\n\n[...truncado em 200k chars...]"
    return text


def compute_entry_hash(entry_data: dict, builder) -> str:
    bundle = _build_bundle_text(builder, entry_data)
    return hashlib.sha1(bundle.encode("utf-8", errors="replace")).hexdigest()


def _normalize(text: str) -> str:
    """Remove acentos, lowercase, strip. Para matching robusto."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def assign_code_to_block(
    concepts: list[str],
    timeline_blocks: list[dict],
    *,
    primary_threshold: float = 0.4,
    secondary_threshold: float = 0.25,
    margin_threshold: float = 0.15,
) -> tuple[str, list[str], float, str]:
    """Concept-match código → block.

    Compara concepts do Gemini contra block.topics + primary_topic_label +
    aliases + topic_text. Retorna (primary_id, secondary_ids, confidence, method).

    method ∈ {"auto_concept", "orphan"}.
    """
    if not concepts or not timeline_blocks:
        return ("", [], 0.0, "orphan")

    concepts_norm = {_normalize(c) for c in concepts if c}
    concepts_norm.discard("")
    if not concepts_norm:
        return ("", [], 0.0, "orphan")

    scores: list[tuple[str, float]] = []
    for blk in timeline_blocks:
        bag: set[str] = set()
        for t in blk.get("topics") or []:
            bag.add(_normalize(t))
        bag.add(_normalize(blk.get("primary_topic_label", "")))
        for a in blk.get("aliases") or []:
            bag.add(_normalize(a))
        for token in (blk.get("topic_text") or "").split():
            n = _normalize(token)
            if len(n) >= 4:
                bag.add(n)
        bag.discard("")
        if not bag:
            scores.append((blk["id"], 0.0))
            continue

        # Score = overlap parcial (substring match) / N concepts
        overlap = 0
        for c in concepts_norm:
            for b in bag:
                if c == b or (len(c) >= 5 and c in b) or (len(b) >= 5 and b in c):
                    overlap += 1
                    break
        score = overlap / len(concepts_norm)
        scores.append((blk["id"], score))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_id, top_score = scores[0]
    second_score = scores[1][1] if len(scores) > 1 else 0.0
    margin = top_score - second_score

    if top_score >= primary_threshold and margin >= margin_threshold:
        secondaries = [
            bid for bid, s in scores[1:]
            if s >= secondary_threshold and s >= top_score * 0.6
        ]
        return (top_id, secondaries[:2], top_score, "auto_concept")

    return ("", [], top_score, "orphan")


def load_code_curation(repo_dir: Path) -> dict:
    path = repo_dir / "code_curation.json"
    if not path.exists():
        return {"version": 1, "entries": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "entries": {}}


def write_code_curation(repo_dir: Path, data: dict) -> None:
    path = repo_dir / "code_curation.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_timeline_blocks(builder) -> list[dict]:
    path = builder.root_dir / ".timeline_index.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("blocks", []) or []
    except Exception:
        return []


def summarize_code_entry(builder, entry_data: dict, client) -> Optional[dict]:
    bundle_text = _build_bundle_text(builder, entry_data)
    if not bundle_text.strip():
        return None
    try:
        result: CodeSummary = client.summarize_bundle(
            bundle_text=bundle_text,
            schema=CodeSummary,
            system_instruction=SYSTEM_INSTRUCTION,
        )
        summary_dict = result.model_dump()
        # Block matching pós-summary
        blocks = _load_timeline_blocks(builder)
        primary, secondaries, conf, method = assign_code_to_block(
            summary_dict["concepts"], blocks
        )
        summary_dict["primary_block_id"] = primary
        summary_dict["secondary_block_ids"] = secondaries
        summary_dict["block_match_confidence"] = round(conf, 3)
        summary_dict["block_match_method"] = method
        return summary_dict
    except Exception as exc:
        logger.error("[CodeSummary] Falha em %s: %s",
                     entry_data.get("id"), exc)
        return None


def summarize_all_code_entries(builder, client, progress_cb=None) -> dict:
    """Summarize ALL code entries, cache by hash. Returns updated curation dict."""
    manifest_path = builder.root_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    curation = load_code_curation(builder.root_dir)
    entries_map = curation.setdefault("entries", {})

    code_entries = _collect_code_entries(manifest)
    total = len(code_entries)
    for idx, entry_data in enumerate(code_entries):
        eid = entry_data.get("id")
        if not eid:
            continue
        new_hash = compute_entry_hash(entry_data, builder)
        existing = entries_map.get(eid, {})
        if existing.get("content_hash") == new_hash and existing.get("summary"):
            if progress_cb:
                progress_cb(idx, total, entry_data.get("title", ""), "cached")
            continue

        if progress_cb:
            progress_cb(idx, total, entry_data.get("title", ""), "calling_api")

        summary = summarize_code_entry(builder, entry_data, client)
        if summary is None:
            continue
        entries_map[eid] = {
            "content_hash": new_hash,
            "model": client.model,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": summary,
        }
        write_code_curation(builder.root_dir, curation)

    if progress_cb:
        progress_cb(total, total, "", "done")
    return curation


def _collect_code_entries(manifest: dict) -> list[dict]:
    """Top-level code entries + flattened ZIP children."""
    result = []
    for e in manifest.get("entries", []):
        if e.get("file_type") == "code":
            result.append(e)
        elif e.get("file_type") == "zip":
            for ef in e.get("extracted_files") or []:
                # ZIP children são entries virtuais; tratamos ZIP como bundle único
                pass
            # Trata ZIP como entry único (bundle holístico)
            result.append(e)
    return result


def prune_stale_code_curation(builder) -> int:
    curation_path = builder.root_dir / "code_curation.json"
    if not curation_path.exists():
        return 0
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        return 0

    try:
        curation = json.loads(curation_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    valid_ids = {e.get("id") for e in manifest.get("entries", []) if e.get("id")}
    entries_map = curation.get("entries", {})
    stale = [eid for eid in entries_map if eid not in valid_ids]
    for eid in stale:
        entries_map.pop(eid, None)

    if stale:
        curation_path.write_text(
            json.dumps(curation, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("[CodeCuration] Pruned %d stale entries", len(stale))
    return len(stale)
