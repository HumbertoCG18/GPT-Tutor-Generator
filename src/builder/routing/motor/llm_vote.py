"""TIER 3 (FASE 3): voto LLM nos flagged ∪ same-theme (spec §3 TIER 3 + §12).

Regras (sign-off condicional 03/07 + GO do user 09/07):
- Autoconfianca do LLM e IGNORADA (gravada so p/ auditoria; nenhum gate le).
- Voto BOUNDED a janela: fora da janela = invalido -> mantem FLAG.
- Sem-janela NAO vota (funil-piso responde).
- Cache por IDENTIDADE DE CONTEUDO (md5 do arquivo; fallback id) — gemeos
  compartilham 1 voto (coerente com TIER 0); write atomico; seed MARCO 1.
- Cap de chamadas API por rodada (cache hit nao conta).
- google-genai LAZY dentro do metodo (invariante spec §4).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel

from src.builder.text.normalize import normalize_match_text

MD_PROMPT_CAP = 3500   # protocolo MARCO 1
DEFAULT_CAP = 20       # orcamento D8 por rodada/reprocess

SYSTEM_TEMPLATE = (
    "Voce e o desambiguador de atribuicao material->bloco de um tutor de curso "
    "universitario ({course}). Dado um material didatico e os blocos candidatos "
    "da timeline do curso (com datas e topicos do roteiro do professor), escolha "
    "o bloco em que esse material foi usado em aula. Responda APENAS com um dos "
    "block_id candidatos, exatamente como escrito (ex.: bloco-13)."
)


class Voto(BaseModel):
    block_id: str
    confianca: str            # alta|media|baixa — auditoria; NUNCA lida por gate
    justificativa_curta: str


def content_key(entry: dict, repo_dir: Path) -> str:
    """Identidade de conteudo: md5 dos bytes de source_path; fallback = id."""
    rel = str(entry.get("source_path") or "")
    p = Path(repo_dir) / rel
    if rel and p.is_file():
        try:
            h = hashlib.md5()
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            pass
    return str(entry.get("id") or "")


def load_material_curation(path: Path) -> dict:
    if not Path(path).is_file():
        return {"version": 1, "votes": {}}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "votes": {}}
    if not isinstance(data, dict) or not isinstance(data.get("votes"), dict):
        return {"version": 1, "votes": {}}
    return data


def save_material_curation(path: Path, data: dict) -> None:
    """Write atomico: tmp + os.replace (spec §12 regra 5)."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def import_marco1_seed(seed_votes: dict, entries_by_id: dict, repo_dir: Path) -> dict:
    """Re-chaveia votos do MARCO 1 (por entry-id) para identidade de conteudo.

    Voto com erro/block_id vazio NAO entra (deve re-chamar a API);
    entry que sumiu do manifest NAO entra.
    """
    votes: dict = {}
    for rid, vote in (seed_votes or {}).items():
        if not str((vote or {}).get("block_id") or "").strip():
            continue
        e = entries_by_id.get(str(rid))
        if not e:
            continue
        votes[content_key(e, repo_dir)] = dict(vote)
    return votes


_DIGITS = re.compile(r"\d+")


def detect_same_theme_series(entries: List[dict]) -> Set[str]:
    """Membros de serie same-theme: mesmo card + mesmo stem, >=2 ordinais distintos.

    Porta detect_series do marco0 (metodologia validada no MARCO 1).
    Import lazy de is_out_of_disamb_scope: anchor_engine nao importa llm_vote,
    entao o lazy quebra o ciclo so por higiene de dependencia.
    """
    from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope

    groups: Dict[tuple, list] = defaultdict(list)
    for e in entries or []:
        if is_out_of_disamb_scope(e):
            continue
        rid = str(e.get("id") or "")
        name = str(e.get("title") or rid)
        nums = _DIGITS.findall(name)
        stem = _DIGITS.sub("", normalize_match_text(name)).strip()
        sec = str(e.get("source_section") or "").strip()
        if rid and nums and stem and sec:
            groups[(sec, stem)].append((rid, int(nums[-1])))
    members: Set[str] = set()
    for ms in groups.values():
        if len(ms) >= 2 and len({o for _, o in ms}) >= 2:
            members.update(rid for rid, _o in ms)
    return members


def _block_lines(window: List[str], ctx) -> str:
    out = []
    for ref in window:
        b = ctx.block_by_ref(ref) or {}
        did = str(b.get("id") or ref)
        datas = (f"{str(b.get('period_start') or '')[:10]}.."
                 f"{str(b.get('period_end') or '')[:10]}")
        top = str(b.get("topic_text") or b.get("primary_topic_label") or "").strip()
        rot = " ; ".join(
            ctx.lessons_index.get(str(s.get("date") or "")[:10], "")
            for s in (b.get("sessions") or [])
            if ctx.lessons_index.get(str(s.get("date") or "")[:10])
        )
        out.append(f"- {did} [{datas}] topico: {top[:90]}  roteiro: {rot[:120]}")
    return "\n".join(out)


def build_vote_prompt(entry: dict, window: List[str], ctx,
                      markdown: str = "") -> str:
    """Prompt do MARCO 1 generalizado (roteiro via ctx.lessons_index)."""
    md = (markdown or "")[:MD_PROMPT_CAP]
    return (
        f"MATERIAL:\n"
        f"  titulo: {entry.get('title')}\n"
        f"  categoria: {entry.get('category')}\n"
        f"  secao/card do Moodle: {entry.get('source_section') or '(sem secao)'}\n"
        f"  trecho do conteudo:\n---\n{md or '(sem markdown extraido)'}\n---\n\n"
        f"BLOCOS CANDIDATOS:\n{_block_lines(window, ctx)}\n\n"
        f"Qual bloco? Responda no schema."
    )


def match_window_ref(block_id_vote: str, window: List[str],
                     ctx) -> Optional[str]:
    """Voto -> ref da janela (bounded). Fora da janela = None (mantem FLAG)."""
    v = str(block_id_vote or "").strip()
    if not v:
        return None
    for ref in window:
        b = ctx.block_by_ref(ref) or {}
        if v in (str(ref), str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            return ref
    return None


class LlmVoter:
    """Voto Gemini cacheado com cap por rodada. vote() -> ref da janela ou None.

    client injetavel (testes); em producao lazy via get_gemini_client (spec §4).
    Erro de API NAO e cacheado (rodada seguinte re-tenta); voto fora da janela
    E cacheado (voto real, so nao ancora).
    """

    def __init__(self, config: Optional[dict], cache_path: Path, repo_dir: Path,
                 cap: int = DEFAULT_CAP, client=None):
        self._config = config or {}
        self._cache_path = Path(cache_path)
        self._repo_dir = Path(repo_dir)
        self._cap = int(cap)
        self._client = client
        self._client_loaded = client is not None
        self._data = load_material_curation(self._cache_path)
        self.calls = 0          # chamadas API na rodada (cache hit nao conta)
        self.skipped_cap = 0    # escopo sem voto por cap estourado
        self.errors = 0

    def _get_client(self):
        if not self._client_loaded:
            from src.builder.runtime.gemini_client import get_gemini_client  # lazy
            self._client = get_gemini_client(self._config)
            self._client_loaded = True
        return self._client

    def has_vote(self, entry: dict) -> bool:
        return content_key(entry, self._repo_dir) in self._data["votes"]

    def vote(self, entry: dict, window: List[str], ctx,
             markdown: str = "") -> Optional[str]:
        if not window:
            return None                      # sem-janela NAO vota (spec §12)
        key = content_key(entry, self._repo_dir)
        cached = self._data["votes"].get(key)
        if cached is None:
            if self.calls >= self._cap:
                self.skipped_cap += 1
                return None
            client = self._get_client()
            if client is None:
                return None                  # sem chave -> mantem FLAG
            prompt = build_vote_prompt(entry, window, ctx, markdown)
            system = SYSTEM_TEMPLATE.format(course=ctx.course_name or "curso")
            self.calls += 1
            try:
                voto = client.summarize_bundle(prompt, Voto, system)
            except Exception:  # noqa: BLE001 — voto falhou: FLAG fica, sem cache
                self.errors += 1
                return None
            cached = {
                "block_id": str(voto.block_id).strip(),
                "confianca": str(voto.confianca).strip(),  # auditoria; nunca gate
                "justificativa": str(voto.justificativa_curta)[:200],
                "model": getattr(client, "model", ""),
            }
            self._data["votes"][key] = cached
            save_material_curation(self._cache_path, self._data)
        return match_window_ref(str(cached.get("block_id") or ""), window, ctx)
