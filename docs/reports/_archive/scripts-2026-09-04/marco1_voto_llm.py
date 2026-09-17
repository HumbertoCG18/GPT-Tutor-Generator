#!/usr/bin/env python3
"""MARCO 1 — voto LLM (Gemini) no conjunto FLAGGED do MARCO 0 (MF). READ-ONLY no repo.

Prova do TIER 3 (D8): o disambiguator deterministico flagou N casos (margem baixa/
silencio); o LLM vota SO nesses. Mede o lift real sobre o piso deterministico
(Config C do marco0) contra a regua oficial ground_truth_MF.csv.

- Voto cacheado em docs/reports/marco1_votes_MF.json (re-rodar NAO re-chama a API).
- Cap de chamadas = 20 (orcamento do D8). Prompt NUNCA ve o gabarito.
- Sem-janela: candidatos = timeline inteira (espelha o residuo do funil).

Uso:  python scripts/marco1_voto_llm.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from marco0_prova_deterministica import Motor, _md_text  # noqa: E402

REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
FLAGGED = ROOT / "docs" / "reports" / "marco0_flagged_MF.json"
VOTES = ROOT / "docs" / "reports" / "marco1_votes_MF.json"
CAP = 20
MD_PROMPT_CAP = 3500

SYSTEM = (
    "Voce e o desambiguador de atribuicao material->bloco de um tutor de curso "
    "universitario (Metodos Formais: logica, especificacao, inducao, Hoare, Dafny, "
    "Isabelle). Dado um material didatico e os blocos candidatos da timeline do "
    "curso (com datas e topicos do roteiro do professor), escolha o bloco em que "
    "esse material foi usado em aula. Responda APENAS com um dos block_id "
    "candidatos, exatamente como escrito (ex.: bloco-13)."
)


def block_lines(motor: Motor, blocks) -> str:
    out = []
    for b in blocks:
        did = motor.disp(b)
        datas = f"{str(b.get('period_start') or '')[:10]}..{str(b.get('period_end') or '')[:10]}"
        top = str(b.get("topic_text") or b.get("primary_topic_label") or "").strip()
        rot = " ; ".join(motor.roteiro.get(str(s.get("date") or ""), "")
                         for s in (b.get("sessions") or []) if motor.roteiro.get(str(s.get("date") or "")))
        out.append(f"- {did} [{datas}] topico: {top[:90]}  roteiro: {rot[:120]}")
    return "\n".join(out)


def build_prompt(motor: Motor, e, blocks) -> str:
    md = _md_text(motor.repo, e)[:MD_PROMPT_CAP]
    return (
        f"MATERIAL:\n"
        f"  titulo: {e.get('title')}\n"
        f"  categoria: {e.get('category')}\n"
        f"  secao/card do Moodle: {e.get('source_section') or '(sem secao)'}\n"
        f"  trecho do conteudo:\n---\n{md or '(sem markdown extraido)'}\n---\n\n"
        f"BLOCOS CANDIDATOS:\n{block_lines(motor, blocks)}\n\n"
        f"Qual bloco? Responda no schema."
    )


def collapse(correct_by_id: dict, rows: list) -> tuple:
    by_unit = defaultdict(list)
    for r in rows:
        if r["id"] in correct_by_id:
            by_unit[r["pair_key"] or r["id"]].append(correct_by_id[r["id"]])
    return sum(int(all(v)) for v in by_unit.values()), len(by_unit)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="monta prompts, nao chama API")
    args = ap.parse_args()

    flagged = json.loads(FLAGGED.read_text(encoding="utf-8"))
    rows = [r for r in csv.DictReader(open(GOLD, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    true_by_id = {r["id"]: r["true_block_id"] for r in rows}
    motor = Motor(REPO)
    votes = json.loads(VOTES.read_text(encoding="utf-8")) if VOTES.exists() else {}

    print(f"MARCO 1 — flagged={len(flagged)}  cache previo={len(votes)}  cap={CAP}")
    assert len(flagged) <= CAP, f"flagged {len(flagged)} > cap {CAP}: recorta antes"

    client = None
    if not args.dry_run:
        cfg_path = Path.home() / ".gpt_tutor_config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        from src.builder.runtime.gemini_client import get_gemini_client  # lazy
        client = get_gemini_client(cfg)
        if client is None:
            print("SEM CHAVE Gemini (config/env). Aborta sem chamar nada.")
            return 2
        from pydantic import BaseModel

        class Voto(BaseModel):
            block_id: str
            confianca: str  # alta | media | baixa
            justificativa_curta: str

    calls = 0
    for v in flagged:
        rid = v["id"]
        if rid in votes:
            continue
        e = motor.byid_entry.get(rid)
        if not e:
            votes[rid] = {"block_id": "", "confianca": "", "erro": "entry sumiu do manifest"}
            continue
        win = motor.window(e.get("source_section"))
        blocks = win if len(win) > 1 else motor.blocks  # sem-janela/janela-1 degenerada -> timeline
        prompt = build_prompt(motor, e, blocks)
        if args.dry_run:
            print(f"\n===== {rid} =====\n{prompt[:900]}\n...")
            continue
        calls += 1
        print(f"[{calls}] votando: {rid[:56]}")
        try:
            voto = client.summarize_bundle(prompt, Voto, SYSTEM)
            votes[rid] = {"block_id": str(voto.block_id).strip(),
                          "confianca": str(voto.confianca).strip(),
                          "justificativa": str(voto.justificativa_curta)[:200],
                          "model": client.model}
        except Exception as exc:  # noqa: BLE001 — probe: registra e segue
            votes[rid] = {"block_id": "", "confianca": "", "erro": str(exc)[:200]}
        VOTES.write_text(json.dumps(votes, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dry_run:
        return 0

    print(f"\nchamadas nesta rodada: {calls} (cache reusado: {len(flagged) - calls})")

    # ---- placar: LLM substitui a predicao SO nos flagged (escalada D8) ----
    flagged_ids = {v["id"] for v in flagged}
    det_correct = {v["id"]: v["correct"] for v in flagged}
    llm_correct, table = {}, []
    for v in flagged:
        rid = v["id"]
        vote = votes.get(rid, {})
        pred = vote.get("block_id", "")
        ok = pred == true_by_id.get(rid)
        llm_correct[rid] = ok
        table.append((rid, v["pred"], pred, true_by_id.get(rid), v["correct"], ok,
                      vote.get("confianca", "")))

    bar = "=" * 76
    print(f"\n{bar}\nVOTOS — deterministico vs LLM (true oculto do prompt)\n{bar}")
    for rid, dpred, lpred, true, dok, lok, conf in table:
        d = "ok" if dok else "X "
        l = "ok" if lok else "X "
        print(f"  {rid[:46]:46} det={dpred or '-':9}{d} llm={lpred or '-':9}{l} "
              f"true={true:9} [{conf}]")

    n_flag = len(flagged)
    d_ok = sum(det_correct.values())
    l_ok = sum(llm_correct.values())
    print(f"\n  no flagged: deterministico {d_ok}/{n_flag}  ->  LLM {l_ok}/{n_flag}")

    # placar global (escopo disambiguator do marco0): C com LLM nos flagged
    # reconstruimos correct-por-id do marco0 = flagged file tem so flagged;
    # p/ global, reusa o proprio marco0: correct = v0 dos nao-flagged + LLM nos flagged.
    # O marco0 nao emitiu os nao-flagged -> derivamos: roda o placar SO na variacao.
    delta = l_ok - d_ok
    print(f"  delta de acertos no flagged: {delta:+d} linhas")
    print(f"  (global escopo-disamb do marco0: Config C 36/62 = 58.1% -> "
          f"~{36 + delta}/62 = {(36 + delta) / 62 * 100:.1f}% com escalada LLM)")
    print(f"\nvotos salvos (uncommitted): {VOTES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
