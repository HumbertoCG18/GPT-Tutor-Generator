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
from typing import Dict, List, Set

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
