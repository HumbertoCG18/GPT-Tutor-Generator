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

# Bump quando lógica de matching/schema muda — invalida cache
MATCHER_VERSION = 2


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
    suggested_block_id: str = Field(
        default="",
        description="ID do bloco do cronograma mais alinhado (ex: 'bloco-09'). Vazio se nenhum.",
    )
    suggested_secondary_ids: list[str] = Field(
        default_factory=list,
        description="Até 2 ids de blocos secundários relevantes.",
    )
    match_rationale: str = Field(
        default="",
        description="1 frase justificando a escolha de bloco (ou vazio se nenhum).",
    )


SYSTEM_INSTRUCTION = """Você analisa bundles de código acadêmico (Python, Jupyter,
Dafny, Java etc) e produz resumos estruturados em JSON.

Contexto: usuário é estudante; bundles vêm de matérias universitárias.

Sua saída alimenta um tutor LLM. Tutor precisa entender:
- O que código DEMONSTRA conceitualmente
- Qual papel pedagógico cumpre
- Que conceitos vincular ao glossário/unidades
- A QUAL aula/bloco do cronograma o material pertence

Regras:
- inferred_title: descritivo e específico. NUNCA repita filename
  (ex: "Verificação de pré/pós-condições com Dafny", NÃO "introducao.dfy")
- concepts: 3-8 termos técnicos. Use terminologia do domínio
  (ex: "tripla de Hoare", "invariante de laço", "ghost predicate")
- summary: 2-3 frases. Foque no QUE ensina, não na sintaxe
- files: liste cada arquivo do bundle com role curto
- suggested_block_id: escolha 1 id da lista "Blocos do cronograma" abaixo
  que melhor representa o tema do código. Use string vazia "" se NENHUM
  bloco se aplica. NUNCA invente ids.
- suggested_secondary_ids: até 2 ids adicionais (lista vazia se nenhum).
- match_rationale: 1 frase curta justificando a escolha. Vazio se orphan.
- Responda em português brasileiro
- Saída APENAS JSON válido conforme schema"""


def _format_blocks_for_prompt(blocks: list[dict]) -> str:
    """Compact block list for injection into bundle prompt."""
    if not blocks:
        return ""
    lines = ["", "## Blocos do cronograma (escolha suggested_block_id desta lista)"]
    for b in blocks:
        bid = b.get("id", "")
        if not bid:
            continue
        label = b.get("primary_topic_label", "") or "(sem rótulo)"
        topics = ", ".join((b.get("topics") or [])[:4])
        aliases = ", ".join((b.get("aliases") or [])[:6])
        line = f"- {bid} | {label}"
        if topics:
            line += f" | topics: {topics}"
        if aliases:
            line += f" | aliases: {aliases}"
        lines.append(line)
    return "\n".join(lines)


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


def _stem(token: str) -> str:
    """Stem leve: corta plural 's' final em tokens >=5. 'invariantes'→'invariante'."""
    if len(token) >= 5 and token.endswith("s"):
        return token[:-1]
    return token


def _expand_concept_tokens(concept_norm: str) -> set[str]:
    """Para um concept normalizado, devolve {concept, palavras>=4, stems}."""
    out: set[str] = {concept_norm, _stem(concept_norm)}
    for tok in concept_norm.split():
        if len(tok) >= 4:
            out.add(tok)
            out.add(_stem(tok))
    out.discard("")
    return out


def assign_code_to_block(
    concepts: list[str],
    timeline_blocks: list[dict],
    *,
    primary_threshold: float = 0.4,
    secondary_threshold: float = 0.25,
    margin_threshold: float = 0.15,
) -> dict:
    """Concept-match código → block.

    Returns dict: primary, secondaries, confidence, method, top_candidate, top_score.
    method ∈ {"auto_concept", "orphan"}.
    top_candidate = melhor bloco mesmo abaixo do threshold (pra detectar
    consenso fraco com Gemini sem perder a info).
    """
    if not concepts or not timeline_blocks:
        return {"primary": "", "secondaries": [], "confidence": 0.0,
                "method": "orphan", "top_candidate": "", "top_score": 0.0}

    concepts_norm = [_normalize(c) for c in concepts if c]
    concepts_norm = [c for c in concepts_norm if c]
    if not concepts_norm:
        return {"primary": "", "secondaries": [], "confidence": 0.0,
                "method": "orphan", "top_candidate": "", "top_score": 0.0}

    concept_token_sets = [_expand_concept_tokens(c) for c in concepts_norm]

    scores: list[tuple[str, float]] = []
    for blk in timeline_blocks:
        bag: set[str] = set()
        for t in blk.get("topics") or []:
            for tok in _normalize(t).split():
                if len(tok) >= 4:
                    bag.add(tok)
                    bag.add(_stem(tok))
        for tok in _normalize(blk.get("primary_topic_label", "")).split():
            if len(tok) >= 4:
                bag.add(tok)
                bag.add(_stem(tok))
        for a in blk.get("aliases") or []:
            n = _normalize(a)
            if len(n) >= 4:
                bag.add(n)
                bag.add(_stem(n))
        for token in (blk.get("topic_text") or "").split():
            n = _normalize(token)
            if len(n) >= 4:
                bag.add(n)
                bag.add(_stem(n))
        bag.discard("")
        if not bag:
            scores.append((blk["id"], 0.0))
            continue

        overlap = 0
        for ctoks in concept_token_sets:
            if ctoks & bag:
                overlap += 1
        score = overlap / len(concept_token_sets)
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
        return {"primary": top_id, "secondaries": secondaries[:2],
                "confidence": top_score, "method": "auto_concept",
                "top_candidate": top_id, "top_score": top_score}

    return {"primary": "", "secondaries": [], "confidence": top_score,
            "method": "orphan", "top_candidate": top_id, "top_score": top_score}


def _consolidate_assignment(
    local: dict,
    gemini_pick: str,
    gemini_secondaries: list[str],
    valid_ids: set[str],
) -> tuple[str, list[str], float, str]:
    """Funde decisão local (matcher) + sugestão Gemini.

    Returns (primary_id, secondary_ids, confidence, method).
    method ∈ {"consensus", "auto_concept", "llm_only", "orphan"}.
    """
    local_primary = local.get("primary", "")
    local_secs = local.get("secondaries", []) or []
    local_conf = float(local.get("confidence", 0.0))
    local_method = local.get("method", "orphan")
    local_top = local.get("top_candidate", "")
    local_top_score = float(local.get("top_score", 0.0))

    g_primary = gemini_pick if gemini_pick in valid_ids else ""
    g_secs = [s for s in (gemini_secondaries or []) if s in valid_ids and s != g_primary][:2]

    # A: local forte + Gemini concorda → consensus alto
    if local_primary and g_primary and local_primary == g_primary:
        merged_secs = list(dict.fromkeys(local_secs + g_secs))[:2]
        return (local_primary, merged_secs, max(local_conf, 0.85), "consensus")

    # B: local fraco (orphan) MAS top_candidate == Gemini → consensus médio
    # (cobre caso onde matcher achou mesmo bloco mas threshold/margem reprovou)
    if not local_primary and g_primary and local_top == g_primary and local_top_score > 0:
        return (g_primary, g_secs, max(local_top_score, 0.75), "consensus")

    # C: local forte, Gemini diverge → respeita local; Gemini vira secondary
    if local_primary and local_method == "auto_concept":
        merged_secs = list(local_secs)
        if g_primary and g_primary not in merged_secs:
            merged_secs.append(g_primary)
        for s in g_secs:
            if s not in merged_secs and s != local_primary:
                merged_secs.append(s)
        return (local_primary, merged_secs[:2], local_conf, "auto_concept")

    # D: local orphan, Gemini válido (diverge de top_candidate) → llm_only
    if not local_primary and g_primary:
        return (g_primary, g_secs, 0.6, "llm_only")

    # E: ambos vazios → orphan
    return ("", [], local_conf, "orphan")


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
    # Try canonical location (course/.timeline_index.json) first; fall back to root for older repos.
    for rel in ("course/.timeline_index.json", ".timeline_index.json"):
        path = builder.root_dir / rel
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("blocks", []) or []
        except Exception:
            return []
    return []


def _get_or_load_code_curation(builder) -> dict:
    """Cache curation on builder for one-build read amortization."""
    cached = getattr(builder, "_code_curation", None)
    if cached is not None:
        return cached
    data = load_code_curation(builder.root_dir)
    try:
        builder._code_curation = data
    except Exception:
        pass
    return data


def _resolve_block_info(builder, block_id: str) -> Optional[dict]:
    """Return {period_label, primary_topic_label} for a timeline block id, or None."""
    if not block_id:
        return None
    cache = getattr(builder, "_timeline_blocks_by_id", None)
    if cache is None:
        blocks = _load_timeline_blocks(builder)
        cache = {b.get("id"): b for b in blocks if b.get("id")}
        try:
            builder._timeline_blocks_by_id = cache
        except Exception:
            pass
    blk = cache.get(block_id)
    if not blk:
        return None
    return {
        "period_label": blk.get("period_label", block_id),
        "primary_topic_label": blk.get("primary_topic_label", ""),
    }


def summarize_code_entry(builder, entry_data: dict, client) -> Optional[dict]:
    bundle_text = _build_bundle_text(builder, entry_data)
    if not bundle_text.strip():
        return None
    blocks = _load_timeline_blocks(builder)
    # Injeta lista de blocos no prompt — permite Gemini sugerir block_id
    blocks_prompt = _format_blocks_for_prompt(blocks)
    bundle_with_blocks = bundle_text + ("\n" + blocks_prompt if blocks_prompt else "")
    try:
        result: CodeSummary = client.summarize_bundle(
            bundle_text=bundle_with_blocks,
            schema=CodeSummary,
            system_instruction=SYSTEM_INSTRUCTION,
        )
        summary_dict = result.model_dump()
        # Matcher local determinístico
        local = assign_code_to_block(summary_dict["concepts"], blocks)
        # Consolida com sugestão Gemini (validada contra whitelist)
        valid_ids = {b.get("id", "") for b in blocks if b.get("id")}
        primary, secondaries, conf, method = _consolidate_assignment(
            local,
            summary_dict.get("suggested_block_id", "") or "",
            summary_dict.get("suggested_secondary_ids", []) or [],
            valid_ids,
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
        if (
            existing.get("content_hash") == new_hash
            and existing.get("summary")
            and existing.get("matcher_version") == MATCHER_VERSION
        ):
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
            "matcher_version": MATCHER_VERSION,
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


def detect_stale_code_curation(builder) -> list[str]:
    """Read-only: lista entry_ids em code_curation.json sem entry no manifest."""
    curation_path = builder.root_dir / "code_curation.json"
    manifest_path = builder.root_dir / "manifest.json"
    if not curation_path.exists() or not manifest_path.exists():
        return []
    try:
        curation = json.loads(curation_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    valid_ids = {e.get("id") for e in manifest.get("entries", []) if e.get("id")}
    return [eid for eid in (curation.get("entries") or {}) if eid not in valid_ids]


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
