"""Parser dos labels temporais dos cards Moodle — formatos A-D do catálogo.

Cf. docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md. Funções puras
(recebem o payload de core_course_get_contents); nunca inventam: seção sem
sinal temporal fica FORA do resultado (formato E = degradação honesta).
"""
from __future__ import annotations

import html
import re
from datetime import date

from src.builder.sources.moodle import _savename_from_module, sanitize_folder_name

_WEEK_FULL = re.compile(r"Semana\s+(\d{1,2}/\d{1,2}/\d{4})\s*a\s*(\d{1,2}/\d{1,2}/\d{4})")
_LESSON_FULL = re.compile(r"\((\d{1,2}/\d{1,2}/\d{4})\)\s*:\s*(.+)")
_LOOSE_FULL = re.compile(r"\((\d{1,2}/\d{1,2}/\d{4})\)")
_ASYNC = re.compile(r"\(atividade\s+ass[ií]ncrona\)", re.IGNORECASE)

_WEEK_SHORT = re.compile(r"Semana\s*\d+\s*[-–]?\s*(\d{1,2}/\d{1,2})\s*a\s*(\d{1,2}/\d{1,2})")
# Semana sem ano e sem ordinal, DENTRO do card: "Semana 11/05 a 15/05".
_WEEK_BARE = re.compile(r"Semana\s+(\d{1,2}/\d{1,2})\s*a\s*(\d{1,2}/\d{1,2})\b")
# Aula sem ano, parênteses OPCIONAL: "(11/05): x" ou "11/05: x". O ano vem do
# param year (default do _iso). Compartilhado pelo formato A (year-less) e B.
_LESSON_SHORT = re.compile(r"^\(?(\d{1,2}/\d{1,2})\)?\s*[:\-]\s*(.+)")
_AULA_C = re.compile(r"Aula\s+\d+\s*[-–]\s*(\d{1,2}/\d{1,2})\b")
_WEEK_ORDINAL = re.compile(r"Semana\s+(\d+)\b")


def _strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "\n", s or ""))


def _iso(raw: str, year: int | None = None) -> str:
    """DD/MM[/AAAA] -> ISO; '' se inválida (30/02 etc.)."""
    parts = raw.split("/")
    try:
        d, m = int(parts[0]), int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else int(year or 0)
        return date(y, m, d).isoformat()
    except (ValueError, IndexError):
        return ""


def _label_texts(sec: dict) -> list:
    return [_strip_html(m.get("description") or m.get("name") or "")
            for m in sec.get("modules", []) or [] if m.get("modname") == "label"]


def _parse_format_a(texts: list, year: int = 0) -> dict | None:
    weeks, lessons, dates = [], [], []
    # year-less coletado à parte: só conta se houver semana SEM-ANO dentro do card
    # (resumo self-contained). Senão deixa o formato B pegar a semana do NOME — não
    # rouba o caso "semana no nome + aulas year-less".
    bare_lessons, bare_dates, bare_week = [], [], False
    for txt in texts:
        for line in txt.splitlines():
            line = line.strip()
            if not line or _ASYNC.search(line):
                continue
            w = _WEEK_FULL.search(line)
            if w:
                a, b = _iso(w.group(1)), _iso(w.group(2))
                if a and b:
                    weeks.append((a, b))
                continue
            l = _LESSON_FULL.search(line)
            if l:
                d = _iso(l.group(1))
                if d:
                    lessons.append({"date": d, "text": l.group(2).strip().rstrip(";.")})
                    dates.append(d)
                continue
            wb = _WEEK_BARE.search(line)
            if wb:
                a, b = _iso(wb.group(1), year), _iso(wb.group(2), year)
                if a and b:
                    weeks.append((a, b))
                    bare_week = True
                continue
            lb = _LESSON_SHORT.match(line)
            if lb:
                d = _iso(lb.group(1), year)
                if d:
                    bare_lessons.append({"date": d, "text": lb.group(2).strip().rstrip(";.")})
                    bare_dates.append(d)
                continue
            for m in _LOOSE_FULL.finditer(line):
                d = _iso(m.group(1))
                if d:
                    dates.append(d)
    if bare_week:
        lessons += bare_lessons
        dates += bare_dates
    if not dates and not weeks:
        return None
    return {"format": "A", "dates": sorted(set(dates)), "weeks": weeks, "lessons": lessons}


def _parse_format_b(sec_name: str, texts: list, year: int) -> dict | None:
    w = _WEEK_SHORT.search(sec_name)
    if not w:
        return None
    a, b = _iso(w.group(1), year), _iso(w.group(2), year)
    if not (a and b):
        return None
    lessons, dates = [], []
    for txt in texts:
        for line in txt.splitlines():
            m = _LESSON_SHORT.match(line.strip())
            if m:
                d = _iso(m.group(1), year)
                if d:
                    lessons.append({"date": d, "text": m.group(2).strip().rstrip(";.")})
                    dates.append(d)
    return {"format": "B", "dates": sorted(set(dates)) or [a, b],
            "weeks": [(a, b)], "lessons": lessons}


def _parse_format_c(texts: list, year: int) -> dict | None:
    dates, lessons = [], []
    for txt in texts:
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        for i, line in enumerate(lines):
            m = _AULA_C.search(line)
            if m:
                d = _iso(m.group(1), year)
                if d:
                    text = next((x.split(":", 1)[1].strip() for x in lines[i:i + 3]
                                 if x.upper().startswith("CONTE") and ":" in x), "")
                    lessons.append({"date": d, "text": text})
                    dates.append(d)
    if not dates:
        return None
    return {"format": "C", "dates": sorted(set(dates)), "weeks": [], "lessons": lessons}


def _parse_format_d(sec_name: str, week_anchor: str) -> dict | None:
    m = _WEEK_ORDINAL.search(sec_name)
    if not m or not week_anchor:
        return None
    from datetime import timedelta
    try:
        start = date.fromisoformat(week_anchor) + timedelta(weeks=int(m.group(1)) - 1)
    except ValueError:
        return None
    end = start + timedelta(days=4)
    return {"format": "D", "dates": [], "weeks": [(start.isoformat(), end.isoformat())],
            "lessons": []}


def derive_card_block_map(card_dates: dict, blocks: list) -> dict:
    """{secao: {block_ids, source:"labels", format, dates}} por interseção de
    datas de AULA (preferidas) ou semanas (formato D) com period_start..end
    dos blocos não-administrativos. Card sem match -> fora (nunca inventa)."""
    # D2: predicado unico (blocks aqui vem do .timeline_index.json serializado,
    # admin ja removido -> no-op; mantido p/ robustez se receber blocos runtime).
    from src.builder.timeline.index import timeline_block_is_administrative_only
    instructional = [b for b in blocks or [] if not timeline_block_is_administrative_only(b)]
    out: dict = {}
    for card, info in (card_dates or {}).items():
        hits = []
        for b in instructional:
            start = str(b.get("period_start") or "")
            end = str(b.get("period_end") or "") or start
            if not start:
                continue
            dates = info.get("dates") or []
            in_dates = any(start <= d <= end for d in dates)
            in_weeks = (not dates) and any(
                ws <= end and we >= start for ws, we in info.get("weeks") or [])
            if in_dates or in_weeks:
                hits.append((start, str(b.get("block_uuid") or b.get("id") or "")))
        if hits:
            out[card] = {"block_ids": [bid for _s, bid in sorted(hits)],
                         "source": "labels", "format": info.get("format", ""),
                         "dates": list(info.get("dates") or [])}
    return out


def merge_card_block_map(existing: dict, derived: dict) -> dict:
    """Merge do card map: manual NUNCA é sobrescrito; labels atualiza/adiciona."""
    out = dict(existing or {})
    for card, entry in (derived or {}).items():
        cur = out.get(card)
        if cur and str(cur.get("source") or "") == "manual":
            continue
        out[card] = entry
    return out


_DEADLINE_NAME = re.compile(r"\((\d{1,2}/\d{1,2}(?:/\d{4})?)\)")


def _module_due(mod, year: int = 0) -> tuple:
    """Cascata POR MÓDULO: (1) assign com dates[dataid=duedate] -> "structured";
    (2) assign/forum com "entrega" no nome e data `(DD/MM[/AAAA])` -> "named".
    Sem fonte -> ("", "")."""
    from datetime import datetime
    modname = str(mod.get("modname") or "")
    mod_name = str(mod.get("name") or "")
    if modname == "assign":
        for d in mod.get("dates") or []:
            if str(d.get("dataid") or "") == "duedate" and d.get("timestamp"):
                try:
                    return (datetime.fromtimestamp(
                        int(d["timestamp"])).date().isoformat(), "structured")
                except (ValueError, OSError, OverflowError):
                    pass
                break
    if modname in ("assign", "forum") and "entrega" in mod_name.lower():
        m = _DEADLINE_NAME.search(mod_name)
        if m:
            due = _iso(m.group(1), year)
            if due:
                return due, "named"
    return "", ""


def extract_assign_deadlines(contents, year: int = 0) -> dict:
    """{secao_sanitizada: iso_date} com o deadline de entrega de cada seção.

    Cascata por seção: (1) módulo assign com dates[dataid=duedate] (estruturado,
    precedência); (2) data `(DD/MM[/AAAA])` no NAME de módulo assign/forum cujo
    nome contenha "entrega" (ano ausente -> `year`). Seção sem fonte fica FORA
    do dict (nunca inventa)."""
    from datetime import datetime
    out: dict = {}
    for sec in contents or []:
        name = sanitize_folder_name(str(sec.get("name") or ""))
        if not name:
            continue
        structured = named = ""
        for mod in sec.get("modules", []) or []:
            modname = str(mod.get("modname") or "")
            mod_name = str(mod.get("name") or "")
            if modname == "assign" and not structured:
                for d in mod.get("dates") or []:
                    if str(d.get("dataid") or "") == "duedate" and d.get("timestamp"):
                        try:
                            structured = datetime.fromtimestamp(
                                int(d["timestamp"])).date().isoformat()
                        except (ValueError, OSError, OverflowError):
                            structured = ""
                        break
            if (not named and modname in ("assign", "forum")
                    and "entrega" in mod_name.lower()):
                m = _DEADLINE_NAME.search(mod_name)
                if m:
                    named = _iso(m.group(1), year)
        due = structured or named
        if due:
            out[name] = due
    return out


def extract_assign_deadlines_detailed(contents, year: int = 0) -> dict:
    """{secao_sanitizada: [{name, due, source}]} — UM item por módulo, sem colapsar.

    Cascata por módulo em _module_due. Módulo sem fonte fica fora; seção sem
    itens fica fora (nunca inventa). Consumidor: motor/due_window (fallback stem).
    """
    out: dict = {}
    for sec in contents or []:
        name = sanitize_folder_name(str(sec.get("name") or ""))
        if not name:
            continue
        items: list = []
        for mod in sec.get("modules", []) or []:
            due, source = _module_due(mod, year)
            if due:
                items.append({"name": str(mod.get("name") or ""), "due": due,
                              "source": source})
        if items:
            out[name] = items
    return out


def extract_file_dues(contents, year: int = 0) -> dict:
    """{secao_sanitizada: {key_casefold: {"due", "source"}}} — posicional (D-G).

    Cada arquivo herda o due do PRÓXIMO módulo-com-due da MESMA seção (grupo
    `label → resources → assign`). Keys: filename original E savename de disco,
    casefolded (mesma convenção do backfill de seções); key com 2+ ocorrências
    na seção é DESCARTADA (nunca chuta). Arquivo sem módulo-com-due depois
    fica fora. Consumidor: motor/due_window (matching posicional)."""
    from collections import Counter
    out: dict = {}
    for sec in contents or []:
        secname = sanitize_folder_name(str(sec.get("name") or ""))
        if not secname:
            continue
        counts: Counter = Counter()
        fdues: dict = {}
        pending: list = []
        for mod in sec.get("modules", []) or []:
            files = [f for f in (mod.get("contents", []) or [])
                     if f.get("type") == "file" and f.get("filename")]
            for f in files:
                original = str(f["filename"])
                save = _savename_from_module(mod.get("name"), original, len(files))
                keys = {original.casefold(), save.casefold()}
                for k in keys:
                    counts[k] += 1
                pending.append(keys)
            due, source = _module_due(mod, year)
            if due:
                for keys in pending:
                    for k in keys:
                        fdues.setdefault(k, {"due": due, "source": source})
                pending = []
        fdues = {k: v for k, v in fdues.items() if counts[k] == 1}
        if fdues:
            out[secname] = fdues
    return out


def parse_card_dates(contents, year: int, week_anchor: str = "") -> dict:
    """{secao_sanitizada: {format, dates[iso], weeks[(ini,fim)], lessons}}.

    Cascata A -> B -> C -> D por seção (Tasks 1-2 implementam A; B-D na Task 2).
    Seção sem sinal -> fora do dict."""
    out: dict = {}
    for sec in contents or []:
        raw_name = str(sec.get("name") or "")
        name = sanitize_folder_name(raw_name)
        if not name:
            continue
        texts = _label_texts(sec)
        parsed = (_parse_format_a(texts, year)
                  or _parse_format_b(raw_name, texts, year)
                  or _parse_format_c(texts, year)
                  or _parse_format_d(raw_name, week_anchor))
        if parsed:
            out[name] = parsed
    return out


def build_lesson_topic_index(contents, year: int, week_anchor: str = "") -> dict:
    """Índice course-level {date_iso: tópico} das lessons[].text (alavanca 0).

    Reusa parse_card_dates (formatos A-C populam lessons[{date,text}]); colapsa
    TODAS as lessons COM texto por data (colisão entre cards -> concat). Lesson
    sem texto (data avulsa/LOOSE, formato D/E) fica FORA — skip honesto, nunca
    inventa. Shape estável p/ serializar em course/.lessons_index.json:
    {"version": 1, "by_date": {...}}."""
    by_date: dict = {}
    for info in parse_card_dates(contents, year, week_anchor).values():
        for lesson in info.get("lessons") or []:
            d = str(lesson.get("date") or "")
            text = str(lesson.get("text") or "").strip()
            if not d or not text:
                continue
            cur = by_date.get(d)
            by_date[d] = f"{cur}; {text}" if cur and text not in cur else (cur or text)
    return {"version": 1, "by_date": by_date}
