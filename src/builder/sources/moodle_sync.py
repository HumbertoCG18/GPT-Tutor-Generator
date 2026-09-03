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
                # entry url (referencia vinda do links.json) casa pelo URL do modulo, senao a sync
                # seguinte a veria como "sumida" e a removeria (FR 03/09: 2 videos apagados na 2a sync)
                urls = {str(c.get("fileurl") or "").strip() for c in (mod.get("contents") or [])} - {""}
                for e in entries:
                    if e.get("file_type") == "url" and str(e.get("source_path") or "").strip() in urls:
                        matched[str(e.get("id") or "")] = rec
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


# --- S2: plano de import do delta (puro) -------------------------------------------------------
from dataclasses import dataclass, field  # noqa: E402


@dataclass
class SyncPlan:
    add: list = field(default_factory=list)        # FileEntry novos (inclui os re-adds dos alterados)
    readd: list = field(default_factory=list)      # ids alterados: unprocess antes de re-entrar
    prune: list = field(default_factory=list)      # ids sumidos a remover (sync_prune_removed ligada)
    mark: list = field(default_factory=list)       # ids sumidos a marcar (flag desligada)
    links: list = field(default_factory=list)      # FileEntry url de referencia (links.json, acao == referencia)
    review: list = field(default_factory=list)     # links.json com acao == review (ficam no manual-review)
    ignorados: list = field(default_factory=list)  # nomes de arquivos do stash sem tipo (.html/.htm nao impressos)


def plan_import(diff, contents, scan, links, manifest_entries, *, nomes=None, defaults=None, prune_removed: bool = True) -> SyncPlan:
    """Traduz o diff (S1) + o stash varrido + links.json num plano de import. Puro: nao toca disco.

    novos/alterados -> FileEntry a partir dos itens do stash que CASAM o modulo (mesmo casador do
    backfill, com o item do stash como pseudo-entry: source_path, card, moodle_label do sidecar);
    alterados tambem em `readd` (unprocess antes); sumidos -> prune ou mark; links com acao
    "referencia" -> entries url (category references, card = secao), sem duplicar URL ja no manifest;
    acao "review" -> `review`; stash.skipped -> `ignorados` por nome."""
    from pathlib import Path
    from src.builder.core.stash_import import StashScanResult, build_stash_entries
    from src.builder.sources.moodle import sanitize_folder_name
    from src.models.core import FileEntry

    nomes = nomes or {}
    plan = SyncPlan()
    wanted = {(n["section"], n["module_index"]) for n in diff.get("novos", [])}
    wanted |= {(a["section"], a["module_index"]) for a in diff.get("alterados", [])}
    plan.readd = [a["id"] for a in diff.get("alterados", [])]
    pseudo = []
    for it in scan.items:
        base = Path(it.source_path).name
        pseudo.append({"_item": it, "source_path": it.source_path, "source_section": it.card_name,
                       "moodle_label": nomes.get(f"{it.card_name}/{base}") or None})
    picked = []
    for sec, in_sec, mods, n_name in iter_sections(pseudo, contents):
        for mi, mod in enumerate(mods):
            if (int(sec.get("section") or 0), mi) not in wanted:
                continue
            for pe in match_module_entries(in_sec, mod, n_name):
                if pe["_item"] not in picked:
                    picked.append(pe["_item"])
    existing = {str(e.get("source_path") or "") for e in manifest_entries or []}
    readd_paths = {str(e.get("source_path") or "") for e in manifest_entries or [] if str(e.get("id") or "") in set(plan.readd)}
    scan_delta = StashScanResult(items=picked, skipped=list(scan.skipped))
    for fe in build_stash_entries(scan_delta, existing - readd_paths, defaults or {}):
        base = Path(fe.source_path).name
        fe.moodle_label = str(nomes.get(f"{fe.source_section}/{base}") or "")
        plan.add.append(fe)
    if prune_removed:
        plan.prune = list(diff.get("sumidos", []))
    else:
        plan.mark = list(diff.get("sumidos", []))
    known_urls = {str(e.get("source_path") or "").strip() for e in manifest_entries or [] if e.get("file_type") == "url"}
    for l in links or []:
        acao = str(l.get("acao") or "")
        if acao == "review":
            plan.review.append(l)
        elif acao == "referencia" and str(l.get("url") or "").strip() and str(l.get("url")).strip() not in known_urls:
            plan.links.append(FileEntry(source_path=str(l["url"]).strip(), file_type="url", category="references",
                                        title=str(l.get("nome") or "").strip(),
                                        source_section=sanitize_folder_name(str(l.get("secao") or ""))))
    plan.ignorados = [Path(p).name for p in scan.skipped if not Path(p).name.startswith(".")]
    return plan


# --- S3: diff de decisoes + "mudou, confira" + SYNC_REPORT --------------------------------------
_DECISION_FIELDS = (("bloco", "temporal_block_id"), ("unidade", "computed_unit_slug"), ("subunidade", "computed_subunit_slug"))


def snapshot_decisions(entries: list) -> Dict[str, dict]:
    """{id: {bloco, unidade, subunidade, flag}} ANTES da sync (o pino manual vale como bloco)."""
    out = {}
    for e in entries or []:
        eid = str(e.get("id") or "")
        if not eid:
            continue
        snap = {campo: str(e.get(key) or "") for campo, key in _DECISION_FIELDS}
        pin = str(e.get("manual_timeline_block_id") or "").strip()
        if pin:
            snap["bloco"] = pin
        snap["flag"] = bool(e.get("temporal_block_flag"))
        out[eid] = snap
    return out


def decision_diff(before: Dict[str, dict], after_entries: list) -> Dict[str, list]:
    """moved = [{id, campo, antes, depois}] nas entries que existiam; added/removed = ids."""
    after = snapshot_decisions(after_entries)
    moved = []
    for eid in [e for e in after if e in before]:
        for campo, _key in _DECISION_FIELDS:
            a, d = before[eid].get(campo, ""), after[eid].get(campo, "")
            if a != d:
                moved.append({"id": eid, "campo": campo, "antes": a, "depois": d})
    return {"moved": moved, "added": [e for e in after if e not in before], "removed": [e for e in before if e not in after]}


def mark_sync_changes(entries: list, moved: list, *, when: str) -> int:
    """Grava `sync_changed` nas entries que se moveram (limpa nas outras) e recalcula `revisar`
    (materiais). Ruling do user 03/09: decisao antiga que se moveu entra como "mudou, confira"."""
    from src.builder.routing.revisar import revisar_de
    by_id: Dict[str, list] = {}
    for m in moved or []:
        by_id.setdefault(str(m["id"]), []).append(f"{m['campo']}: {m['antes'] or '-'} -> {m['depois'] or '-'}")
    n = 0
    for e in entries or []:
        eid = str(e.get("id") or "")
        if eid in by_id:
            e["sync_changed"] = "; ".join(by_id[eid]) + f" (sync {when})"
            n += 1
        else:
            e.pop("sync_changed", None)
        if e.get("category"):
            e["revisar"] = revisar_de(e)
    return n


def render_sync_report(diff: Dict[str, list], dd: Dict[str, list], *, when: str, curso: str,
                       ignorados=(), review=(), plan_counts=None) -> str:
    L = [f"# SYNC {when} — {curso}", "",
         f"Moodle x manifest: novos {len(diff['novos'])} · alterados {len(diff['alterados'])} · sumidos {len(diff['sumidos'])} · "
         f"iguais {len(diff['iguais'])} · links {len(diff['links'])}" + (f" · plano {plan_counts}" if plan_counts else ""), ""]
    L += ["## Entraram (novos no Moodle)"] + ([f"- s{n['section']} m{n['module_index']} [{n['modname']}] {n['name']} {n['files']}" for n in diff["novos"]] or ["- nenhum"]) + [""]
    L += ["## Alterados no Moodle (re-extraidos)"] + ([f"- {a['id']}: postado {a['posting_date']}, modificado {a['timemodified_iso']}" for a in diff["alterados"]] or ["- nenhum"]) + [""]
    L += ["## Sumidos do Moodle"] + ([f"- {s}" for s in diff["sumidos"]] or ["- nenhum"]) + [""]
    L += ["## Entries novas no tutor"] + ([f"- {e}" for e in dd["added"]] or ["- nenhuma"]) + [""]
    L += ["## Decisoes antigas que se moveram (mudou, confira)"] + ([f"- {m['id']}: {m['campo']} {m['antes'] or '-'} -> {m['depois'] or '-'}" for m in dd["moved"]] or ["- nenhuma"]) + [""]
    L += ["## Removidas do tutor"] + ([f"- {e}" for e in dd["removed"]] or ["- nenhuma"]) + [""]
    L += ["## Ignorados (sem tipo; .html/.htm nao impressos)"] + ([f"- {i}" for i in ignorados] or ["- nenhum"]) + [""]
    L += ["## Links para decidir (manual-review)"] + ([f"- {r.get('nome')} -> {r.get('url')}" for r in review] or ["- nenhum"]) + [""]
    return "\n".join(L)
