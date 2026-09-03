"""Campanha SYNC (2026-09-03), S1: diff estrutural do Moodle (core_course_get_contents) contra o manifest.

READ-ONLY. Usa o casador UNICO do backfill (`moodle.match_module_entries`): basename/savename -> stem ->
moodle_label -> stem == nome do modulo. Vocabulario:
  novos      modulo de MATERIAL (arquivos, pasta ou pagina) sem entry casada
  alterados  entry casada cujo arquivo no Moodle tem `timemodified` DEPOIS do `posting_date` da entry
             (entry sem posting_date nao pode ser julgada -> igual)
  sumidos    entry COM card (source_section) que nenhum modulo casa (o professor removeu/renomeou)
  iguais     entry casada e sem mudanca
  links      modulos url (videos, sites, cronograma): entram no S2 como referencia, nao sao materiais
  fora       entries sem card (url/referencia sem secao): fora do escopo da sync estrutural
Rulings do user (03/09): sumido some do tutor (flag `sync_prune_removed`); decisao antiga que se mover por
material novo entra na fila como "mudou, confira"; alterado re-extrai automatico com cap.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from src.builder.sources.moodle import iter_sections, match_module_entries, module_files, posting_date_iso

_IGNORED_MODNAMES = frozenset({"label", "forum", "assign", "quiz", "groupselect", "choice", "feedback", "chat", "wiki", "workshop"})
_MATERIAL_MODNAMES = frozenset({"resource", "folder", "page", "book", "lesson"})


def _iso(ts) -> str:
    return posting_date_iso(ts)


def sync_diff(manifest_entries: list, contents: list) -> Dict[str, list]:
    entries = list(manifest_entries or [])
    matched: Dict[str, dict] = {}
    novos: List[dict] = []
    links: List[dict] = []
    alterados: List[dict] = []
    for sec, in_sec, mods, n_name in iter_sections(entries, contents):
        for mi, mod in enumerate(mods):
            modname = str(mod.get("modname") or "")
            name = str(mod.get("name") or "")
            files = module_files(mod)
            rec = {"section": int(sec.get("section") or 0), "section_name": str(sec.get("name") or ""),
                   "module_index": mi, "name": name, "modname": modname, "files": files}
            if modname == "url":
                links.append(rec)
                continue
            if modname in _IGNORED_MODNAMES or (modname not in _MATERIAL_MODNAMES and not files):
                continue
            ids = [e for e in match_module_entries(in_sec, mod, n_name) if str(e.get("id") or "") not in matched]
            if not ids:
                novos.append(rec)
                continue
            newest = max((int(c.get("timemodified") or 0) for c in (mod.get("contents") or []) if c.get("type") == "file"), default=0)
            for e in ids:
                eid = str(e.get("id") or "")
                matched[eid] = rec
                posted = str(e.get("posting_date") or "")
                if posted and newest and _iso(newest) > posted:
                    alterados.append({"id": eid, "name": name, "section": rec["section"], "module_index": mi,
                                      "posting_date": posted, "timemodified_iso": _iso(newest)})
    changed = {a["id"] for a in alterados}
    iguais = [str(e.get("id")) for e in entries if str(e.get("id")) in matched and str(e.get("id")) not in changed]
    sumidos = [str(e.get("id")) for e in entries if e.get("source_section") and str(e.get("id")) not in matched]
    fora = [str(e.get("id")) for e in entries if not e.get("source_section")]
    return {"novos": novos, "alterados": alterados, "sumidos": sumidos, "iguais": iguais, "links": links, "fora": fora}


def format_diff(diff: Dict[str, list]) -> str:
    lines = [f"novos {len(diff['novos'])} · alterados {len(diff['alterados'])} · sumidos {len(diff['sumidos'])} · "
             f"iguais {len(diff['iguais'])} · links {len(diff['links'])} · fora {len(diff['fora'])}"]
    for n in diff["novos"]:
        lines.append(f"  NOVO      s{n['section']:>2} m{n['module_index']:>2} [{n['modname']}] {n['name'][:60]} {n['files'][:3]}")
    for a in diff["alterados"]:
        lines.append(f"  ALTERADO  {a['id'][:44]} posting {a['posting_date']} -> moodle {a['timemodified_iso']} ({a['name'][:40]})")
    for s in diff["sumidos"]:
        lines.append(f"  SUMIDO    {s}")
    return "\n".join(lines)
