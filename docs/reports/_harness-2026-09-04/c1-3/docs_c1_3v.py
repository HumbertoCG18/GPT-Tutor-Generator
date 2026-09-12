"""Registro (06/09 noite): decisao do user 'bloco de prova hospeda entrega'; gold do T2 do MF -> bloco-20; datas de entrega ja no pull
(core_course_get_contents.dates.duedate); due-window do motor exclui prova por desenho (T17) -> candidata C. Sem args."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
anchor = '## LEI REAFIRMADA: SARC E MOODLE > GOLD — GOLD DO ES2 CORRIGIDO PELO ORACULO E CRIVO DAS 7 DIVERGENCIAS (06/09 noite, sessao 6; user: "se o gold estiver diferente do SARC/Moodle, e mais provavel que eu tenha errado o gold")'
SEC = """## BLOCO DE PROVA HOSPEDA ENTREGA (decisao do user 06/09 noite) — GOLD DO T2 DO MF -> BLOCO 20; DATAS DE ENTREGA JA ESTAO NO PULL
**Gold (docs):** `ground_truth_MF.csv` t2-2026-1 true_block bloco-18 -> **bloco-20** ("prova P2, entrega do T2", 06/07, kind assessment; Moodle
'Sala de entrega' vencimento 06/07/2026 23:59). Bloco de prova nao tem unidade (gold_units 'FORA DA REGUA'): o T2 sai da regua de unidade
(191 -> 190). **Remedido:** produto bloco 198 -> **197/199** (o motor ancora o T2 em bloco-18 por desenho, abaixo), unidade 183/190, sub 193/233;
placar por material zero 156 -> 155 · automatica 231 -> 230 · produto 246 -> 245 (`placar_100_gold_mf.log`).
**Datas de entrega pela API (pergunta do user):** SIM, e ja estao no pull: `core_course_get_contents` devolve, em cada modulo `assign` ("Sala de
entrega"), `dates: [{label: 'Vencimento:', dataid: 'duedate', timestamp}]`. Nos pulls de 06/09: IA 18/18 assigns com vencimento · LR 3/3 · MF 2/2
(06/05 e 06/07) · SO 2/3 · ES2 1/1 (Trabalho Final 06/07) · TCC 0/3 (salas sem prazo) · CG 0 · FR 0. `mod_assign_get_assignments` daria ainda
allowsubmissionsfromdate/cutoffdate/intro; nao e necessario para a data de entrega.
**O motor ja usa a data (tier 2 `motor/due_window.py`, spec 2026-07-22 + F5b):** casa arquivo -> vencimento por filename/stem e, por desenho
(T17, 2026-08-06), **so bloco de CONTEUDO ancora**: vencimento dentro de prova/revisao -> "ultimo bloco de conteudo anterior", confianca media +
FLAG (method `due-straddle`). Foi exatamente isso no T2: vencimento 06/07 dentro do bloco-20 (P2) -> bloco-18 (29/06). **Candidata C (a
decisao do user inverte o T17):** vencimento contido em bloco `assessment` ancora nele (review/feriado seguem excluidos). Alcance estatico: MF T2;
ES2 Trabalho Final (vencimento 06/07 dentro do bloco-13 "prova P2, entrega trabalho final"); TCC sem prazo nas salas. Gate: motor puro + suite.

"""
edit(T, anchor, SEC + anchor)

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "**Aberto:** gold do MF `t2-2026-1` (SARC: entrega do T2 em 06/07 dentro do bloco da P2; gold bloco-18 sem evidencia do professor).\n",
        "**Decidido (06/09 noite): bloco de prova hospeda entrega.** Gold do MF `t2-2026-1` -> bloco-20; produto bloco 197/199 (o due-window ancora na aula "
        "anterior por desenho T17: candidata C no tracker). Placar: zero 155 · automatica 230 · produto 245 / 288; unidade 183/190; sub 193/233.\n")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### SARC e Moodle valem mais que o gold; bloco de prova hospeda entrega

**Date:** 2026-09-06
**Status:** Active
**Decision:** (1) Lei reafirmada pelo user: onde o gold diverge do SARC/Moodle, o gold e que esta errado (o professor controla SARC e Moodle; o gold foi feito pelo user). (2) Bloco de prova (kind assessment) pode hospedar entrega de trabalho quando o vencimento cai nele.
**Reasoning:** ES2: 7 materiais postados antes da P1, que pelo plano contempla so a secao 1 (label do Moodle "exercicios de revisao para P1"), estavam no gold na unidade 02 porque o LLM pendurou 'API gateway' na 2.7 e a curadoria seguiu; o motor puro acertava. MF: SARC "prova P2, entrega do T2" em 06/07 e 'Sala de entrega' com vencimento 06/07; o gold bloco-18 era relabel de conteudo sem evidencia do professor.
**Consequences:** Golds corrigidos (`gold_units_ES2`, `subunit_gt_ES2`, `ground_truth_MF`). Produto: bloco 197/199, unidade 183/190, sub 193/233; placar por material zero 155 · automatica 230 · produto 245 / 288. Candidata C: `due_window` deixa bloco assessment ancorar quando contem o vencimento (inverte o T17 de 2026-08-06). As 6 outras divergencias gold x Moodle de 06/09 foram revistas e mantidas (artefatos da heuristica da auditoria; SARC concorda com o gold).
"""
assert "bloco de prova hospeda entrega" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `placar_100_gold_mf.log` (placar com o gold do T2 do MF no bloco da P2) · `docs_c1_3v.py`.\n", encoding="utf-8")
print("docs ok")
