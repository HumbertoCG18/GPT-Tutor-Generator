"""Camada de edicao xlsx pro gold de unidades (campanha 2, Task 7).

build:  le docs/reports/gold_templates/gold_units_<CURSO>.csv (5 cursos) e gera
        UM workbook com 1 aba por curso: true_unit com dropdown dos slugs reais
        do curso (taxonomia via course_probe), descritores travados, so
        true_unit/notes editaveis (amarelo). block_uuid fica oculto (chave do
        round-trip, nao mexer).
export: le o workbook editado e REESCREVE os 5 CSVs no mesmo formato utf-8-sig
        (fluxo da Task 7: user edita xlsx -> export -> congelar CSVs em fixtures).

Uso:
    python scripts/gold_units_xlsx.py build
    python scripts/gold_units_xlsx.py export
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openpyxl import Workbook, load_workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill, Protection  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from src.models.core import SubjectStore  # noqa: E402
from scripts.course_probe import compute_production_taxonomy  # noqa: E402
from scripts.eval_units import sigla_for_repo  # noqa: E402
from scripts.gold_units_template import FIELDS, OUT_DIR  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

XLSX = OUT_DIR / "gold_units_rotular.xlsx"
ORDER = ["MF", "SO", "ES2", "IA", "TCC"]

HDR_FILL = PatternFill("solid", fgColor="D9D9D9")
EDIT_FILL = PatternFill("solid", fgColor="FFF2CC")  # amarelo = preencher
HDR_FONT = Font(bold=True)
WRAP = Alignment(vertical="top", wrap_text=True)
TOP = Alignment(vertical="top")
LOCKED = Protection(locked=True)
UNLOCKED = Protection(locked=False)

COL_TRUE = FIELDS.index("true_unit") + 1
COL_NOTES = FIELDS.index("notes") + 1
WIDTHS = {"block_uuid": 4, "block_id": 10, "date_start": 11, "date_end": 11,
          "kind": 11, "topic_text": 58, "unit_slug_atual": 40, "true_unit": 46,
          "notes": 30}


def _slugs_por_sigla() -> dict:
    out = {}
    store = SubjectStore()
    for name in store.names():
        sp = store.get(name)
        if sp is None or not getattr(sp, "repo_root", ""):
            continue
        sig = sigla_for_repo(Path(sp.repo_root))
        if not sig:
            continue
        tax = compute_production_taxonomy(sp)
        out[sig] = [u.get("slug") for u in tax.get("units", []) if u.get("slug")]
    return out


def build() -> int:
    slugs = _slugs_por_sigla()
    wb = Workbook()
    wb.remove(wb.active)

    ws_s = wb.create_sheet("_slugs")
    ranges = {}
    for col, sig in enumerate([s for s in ORDER if s in slugs], start=1):
        ws_s.cell(1, col, sig)
        for i, slug in enumerate(slugs[sig], start=2):
            ws_s.cell(i, col, slug)
        letter = get_column_letter(col)
        ranges[sig] = f"'_slugs'!${letter}$2:${letter}${1 + len(slugs[sig])}"
    ws_s.sheet_state = "hidden"

    total = 0
    for sig in ORDER:
        csv_path = OUT_DIR / f"gold_units_{sig}.csv"
        if not csv_path.exists():
            print(f"[skip] {sig}: sem {csv_path.name}")
            continue
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        ws = wb.create_sheet(sig)
        ws.append(FIELDS)
        for c in range(1, len(FIELDS) + 1):
            cell = ws.cell(1, c)
            cell.font = HDR_FONT
            cell.fill = EDIT_FILL if c in (COL_TRUE, COL_NOTES) else HDR_FILL
        for r in rows:
            ws.append([r.get(k, "") for k in FIELDS])
            row = ws.max_row
            for c in range(1, len(FIELDS) + 1):
                cell = ws.cell(row, c)
                editable = c in (COL_TRUE, COL_NOTES)
                cell.protection = UNLOCKED if editable else LOCKED
                if editable:
                    cell.fill = EDIT_FILL
                cell.alignment = WRAP if FIELDS[c - 1] in ("topic_text", "notes") else TOP
        for c, name in enumerate(FIELDS, start=1):
            ws.column_dimensions[get_column_letter(c)].width = WIDTHS[name]
        ws.column_dimensions["A"].hidden = True  # block_uuid: chave, nao mexer
        ws.freeze_panes = "A2"
        if sig in ranges:
            dv = DataValidation(type="list", formula1=ranges[sig],
                                allow_blank=True, showDropDown=False)
            dv.error = "Escolha um slug da lista (ou deixe vazio = fora da regua)."
            dv.prompt = "Slug da unidade CERTA deste bloco."
            ws.add_data_validation(dv)
            dv.add(f"{get_column_letter(COL_TRUE)}2:{get_column_letter(COL_TRUE)}{ws.max_row}")
        ws.protection.sheet = True
        ws.protection.selectLockedCells = True
        ws.protection.selectUnlockedCells = True
        total += len(rows)
        print(f"  {sig}: {len(rows)} blocos, dropdown {len(slugs.get(sig, []))} slugs")

    wb.save(XLSX)
    print(f"OK  {total} blocos -> {XLSX}")
    return 0


def export() -> int:
    wb = load_workbook(XLSX, data_only=True)
    for sig in ORDER:
        if sig not in wb.sheetnames:
            continue
        ws = wb[sig]
        headers = [c.value for c in ws[1]][: len(FIELDS)]
        if headers != FIELDS:
            print(f"[erro] {sig}: header do xlsx != FIELDS ({headers})")
            return 2
        out = OUT_DIR / f"gold_units_{sig}.csv"
        n = fill = 0
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)
            for row in ws.iter_rows(min_row=2, values_only=True):
                vals = ["" if v is None else str(v).strip() for v in row[: len(FIELDS)]]
                if not any(vals):
                    continue
                w.writerow(vals)
                n += 1
                if vals[COL_TRUE - 1]:
                    fill += 1
        print(f"  {sig}: {n} linhas exportadas, {fill} com true_unit -> {out.name}")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "build":
        raise SystemExit(build())
    if mode == "export":
        raise SystemExit(export())
    print(__doc__)
    raise SystemExit(2)
