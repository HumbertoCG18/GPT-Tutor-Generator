"""Medicao pre/pos-flip `use_concept_resolver` em sandbox (mecanica F4, agora
reprodutivel — licao da F4: scripts ad-hoc de medicao nao commitados sao
irreprodutiveis, `docs/reports/2026-08-14-f4-medicao-unit-motor.md` §Limitacoes).

Uso:
    robocopy "<repo-tutor producao>" "<SANDBOX_DIR>/sandbox-<SIGLA>" /E /XD .git
    python scripts/measure_flip.py <SIGLA> <SANDBOX_DIR> [--analyze-only]

Roda BEFORE (flag OFF, perfil real do subjects.json, read-only) -> snapshot;
AFTER (`use_concept_resolver` ON) -> snapshot; analisa:
  - eval_units gold BEFORE vs AFTER (gate: sem regressao)
  - sobrevivencia de pinos `manual_timeline_block_id` (gate: 0 violados;
    `fora_do_motor` = computed vazio nos 2 lados, flip-neutro)
  - delta `computed_block_id`/unit/subunit por entry
  - candidatos M7 (mesmo bloco, unit muda por confianca)
Grava report_<SIGLA>.json no SANDBOX_DIR. Producao NUNCA escrita: SubjectStore
so e lido; root_dir do builder = sandbox.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.core import SubjectStore  # noqa: E402
from scripts.reprocess_assignments import reprocess  # noqa: E402
from scripts.eval_units import score_course  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

COURSES = {
    "MF": "Metodos-Formais",
    "IA": "Inteligencia Artificial",
    "TCC": "Teoria da Computabilidade e Complexidade",
    "SO": "Sistemas Operacionais",
    "ES2": "Engenharia de Software II",
}


class FixedStore:
    """Devolve sempre o perfil real (read-only) mesmo com repo_root do sandbox."""

    def __init__(self, profile):
        self._profile = profile

    def find_by_repo_root(self, repo):
        return self._profile


def snap(sandbox: Path, tag: str) -> None:
    shutil.copy2(sandbox / "manifest.json", sandbox / f"manifest_{tag}.json")
    shutil.copy2(sandbox / "course" / ".timeline_index.json",
                 sandbox / f"timeline_index_{tag}.json")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def analyze(sigla: str, sandbox: Path) -> dict:
    mb = load(sandbox / "manifest_before.json")
    ma = load(sandbox / "manifest_after.json")
    ib = load(sandbox / "timeline_index_before.json")
    ia = load(sandbox / "timeline_index_after.json")
    gold = ROOT / "tests" / "fixtures" / "eval" / f"gold_units_{sigla}.csv"

    rep: dict = {"sigla": sigla}
    rep["eval_before"] = score_course(gold, ib)
    rep["eval_after"] = score_course(gold, ia)
    rep["eval_regression"] = rep["eval_after"]["ok"] < rep["eval_before"]["ok"]

    uuids = {b.get("block_uuid") for b in ia.get("blocks", [])}
    by_display = {b.get("id"): b.get("block_uuid") for b in ia.get("blocks", [])}
    eb = {e.get("id"): e for e in mb.get("entries", [])}

    pins = []
    for e in ma.get("entries", []):
        pin = e.get("manual_timeline_block_id")
        if not pin:
            continue
        canonical = pin if pin in uuids else by_display.get(pin)
        got_after = e.get("computed_block_id") or ""
        got_before = (eb.get(e.get("id")) or {}).get("computed_block_id") or ""
        if canonical is None:
            status = "PIN_IRRESOLUVEL"
        elif got_after == canonical:
            status = "honrado"
        elif not got_after and not got_before:
            status = "fora_do_motor"  # motor nao computa esse entry em nenhum lado
        elif not got_after and got_before:
            status = "PERDIDO"
        else:
            status = "VIOLADO"
        pins.append({"title": e.get("title"), "pin": pin, "canonical": canonical,
                     "before": got_before, "after": got_after, "status": status})
    rep["pins"] = pins
    rep["pins_total"] = len(pins)
    rep["pins_violados"] = [p for p in pins
                            if p["status"] in ("VIOLADO", "PERDIDO", "PIN_IRRESOLUVEL")]

    block_delta, unit_delta, subunit_delta, m7 = [], [], [], []
    for e in ma.get("entries", []):
        b = eb.get(e.get("id")) or {}
        bb, ab = b.get("computed_block_id") or "", e.get("computed_block_id") or ""
        bu, au = b.get("computed_unit_slug") or "", e.get("computed_unit_slug") or ""
        bs, as_ = b.get("computed_subunit_slug") or "", e.get("computed_subunit_slug") or ""
        if bb != ab:
            block_delta.append({"title": e.get("title"), "before": bb, "after": ab})
        if bu != au:
            unit_delta.append({"title": e.get("title"), "before": bu, "after": au,
                               "block_changed": bb != ab})
        if bs != as_:
            subunit_delta.append({"title": e.get("title"), "before": bs, "after": as_})
        if bb == ab and bb and bu != au:
            m7.append({"title": e.get("title"), "block": bb,
                       "unit_before": bu, "unit_after": au,
                       "conf_before": b.get("computed_block_confidence"),
                       "conf_after": e.get("computed_block_confidence")})
    rep["block_delta"] = block_delta
    rep["unit_delta"] = unit_delta
    rep["subunit_delta"] = subunit_delta
    rep["m7_candidatos"] = m7
    rep["counts"] = {"entries": len(ma.get("entries", [])),
                     "block_delta": len(block_delta), "unit_delta": len(unit_delta),
                     "subunit_delta": len(subunit_delta), "m7": len(m7)}
    return rep


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2 or args[0] not in COURSES:
        print(__doc__)
        return 2
    sigla, base = args[0], Path(args[1])
    sandbox = base / f"sandbox-{sigla}"
    if not (sandbox / "manifest.json").exists():
        print(f"[erro] sandbox nao copiado: {sandbox}")
        return 2

    if "--analyze-only" not in sys.argv:
        profile = SubjectStore().get(COURSES[sigla])
        if profile is None:
            print(f"[erro] perfil nao achado: {COURSES[sigla]}")
            return 2
        fs = FixedStore(profile)

        print(f"=== {sigla} BEFORE (flag OFF) ===")
        reprocess(sandbox, [], store=fs)
        snap(sandbox, "before")
        print(f"=== {sigla} AFTER (flag ON) ===")
        reprocess(sandbox, ["use_concept_resolver"], store=fs)
        snap(sandbox, "after")

    rep = analyze(sigla, sandbox)
    out = base / f"report_{sigla}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    c = rep["counts"]
    print(f"\n=== RESUMO {sigla} ===")
    print(f"eval gold: BEFORE {rep['eval_before']['ok']}/{rep['eval_before']['total']}"
          f" -> AFTER {rep['eval_after']['ok']}/{rep['eval_after']['total']}"
          f" | regressao: {rep['eval_regression']}")
    print(f"pinos: {rep['pins_total']} | violados/perdidos: {len(rep['pins_violados'])}")
    for p in rep["pins_violados"]:
        print(f"  PIN {p['status']}: {p['title']} pin={p['pin']} after={p['after']}")
    print(f"delta bloco: {c['block_delta']}/{c['entries']} | unit: {c['unit_delta']}"
          f" | subunit: {c['subunit_delta']} | M7 (mesmo bloco, unit muda): {c['m7']}")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
