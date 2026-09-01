"""Gate de frescor do cronograma: SARC VIVO (schedule_url) x SYLLABUS.md importado.

Achado 2026-08-08 (campanha 2, Task 7): os 5 cronogramas importados estavam STALE
(40 diffs reais — professores remarcaram durante o semestre: suspensoes Copa do
Mundo em junho, TPs movidos, conteudo deslocado). O gold/curas NAO podem medir um
cronograma que nao existe mais. Rodar ANTES de congelar gold e ANTES de cada cura.

READ-ONLY (HTTP + leitura). Exit 1 se qualquer curso tiver diff.
Uso: python scripts/check_sarc_freshness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.helpers import fetch_schedule_html, parse_html_schedule  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402
from scripts.eval_units import sigla_for_repo  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# linha do parse_html_schedule: "- (dd/mm/aaaa) DIA — Desc [Atividade] {kind=...}?"
# (o sufixo {kind=...} aparece nas linhas coloridas — prova/trabalho/suspensao)
_LIVE_RE = re.compile(
    r"- \((\d{2})/(\d{2})/(\d{4})\)\s+\S+\s+—\s+(.*?)\s*\[(.*?)\]\s*(\{.*\})?\s*$"
)
_DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def _norm_desc(text: str) -> str:
    """Colapsa whitespace pra comparação (import preserva espaço duplo do HTML;
    parse_html_schedule colapsa — 4 falsos-stale IA em 2026-08-11)."""
    return re.sub(r"\s+", " ", text or "").strip()


def parse_live(md: str) -> dict:
    rows = {}
    for line in md.splitlines():
        m = _LIVE_RE.match(line.strip())
        if m:
            rows[f"{m.group(3)}-{m.group(2)}-{m.group(1)}"] = (
                _norm_desc(m.group(4)), _norm_desc(m.group(5)))
    return rows


def parse_syllabus(text: str) -> dict:
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6 or cells[0] in ("#", "---"):
            continue
        m = _DATE_RE.search(cells[2])
        if not m:
            continue
        # Sessão agendada SEM descrição (fim de semestre; ex.: IA 15/07, SO 16/07)
        # é REAL no SARC, mas parse_html_schedule a descarta do lado vivo — pular
        # aqui também mantém os dois lados no mesmo universo (senão: falso-stale).
        if not _norm_desc(cells[4]):
            continue
        rows[f"{m.group(3)}-{m.group(2)}-{m.group(1)}"] = (
            _norm_desc(cells[4]), _norm_desc(cells[5]))
    return rows


def main() -> int:
    store = SubjectStore()
    total = 0
    for name in store.names():
        sp = store.get(name)
        if sp is None or not getattr(sp, "repo_root", ""):
            continue
        sig = sigla_for_repo(Path(sp.repo_root))
        syl_path = Path(sp.repo_root) / "course" / "SYLLABUS.md"
        url = getattr(sp, "schedule_url", "")
        if not url or not syl_path.exists():
            print(f"== {sig}: sem schedule_url/SYLLABUS — pulado")
            continue
        try:
            live = parse_live(parse_html_schedule(fetch_schedule_html(url)))
        except Exception as exc:  # noqa: BLE001
            print(f"== {sig}: FETCH FALHOU ({exc!r}) — sem veredito")
            continue
        imported = parse_syllabus(syl_path.read_text(encoding="utf-8"))
        diffs = [(d, imported.get(d), live.get(d))
                 for d in sorted(set(live) | set(imported))
                 if live.get(d) != imported.get(d)]
        total += len(diffs)
        status = "OK" if not diffs else f"STALE ({len(diffs)} diffs)"
        print(f"== {sig}: vivo={len(live)} importado={len(imported)} — {status}")
        for d, im, lv in diffs:
            print(f"   {d}  importado={im}")
            print(f"               vivo={lv}")
    print(f"TOTAL DIFFS: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
