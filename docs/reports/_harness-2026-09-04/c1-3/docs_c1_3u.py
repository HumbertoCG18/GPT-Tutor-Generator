"""Registro (06/09 noite): lei SARC/Moodle > gold reafirmada pelo user; gold do ES2 (bloco 04) corrigido pelo oraculo; deltas medidos por
regime; crivo das 7 divergencias gold x Moodle de 06/09 (6 mantidas com razao, MF t2 aberta). Sem args."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
anchor = '## ES2 UNIDADE SEM LLM — \'MICROSSERVICOS\' EM DUAS UNIDADES, CERCA DE PROVAS E GOLD SUSPEITO (06/09 noite, sessao 6; user: "como arrumar esse tipo de erro? o plano tem 3 entradas?")'
SEC = """## LEI REAFIRMADA: SARC E MOODLE > GOLD — GOLD DO ES2 CORRIGIDO PELO ORACULO E CRIVO DAS 7 DIVERGENCIAS (06/09 noite, sessao 6; user: "se o gold estiver diferente do SARC/Moodle, e mais provavel que eu tenha errado o gold")
**Correcao (docs, gold so mede):** `tests/fixtures/eval/gold_units_ES2.csv` bloco-04 (10/04-24/04: discovery, api gateway, exercicios de revisao
para P1) true_unit unidade-02 -> **unidade-01-arquitetura-de-software** (7 materiais: revisao-p1, roteiro2, roteiro3, microsservicos2,
microsservicos3, roteiro2-nameserver, roteiro3-gateway). `docs/reports/subunit_gt_ES2.csv`: os 6 pontuaveis 2.7 -> **1.5
`estudo-de-caso-arquitetura-orientada-a-microsservicos`** (revisao-p1 segue scorable=no). Evidencia do professor: plano "P1 contempla a secao 1",
P1 no SARC em 08/05, label do Moodle de 24/04 "exercicios de revisao para P1". Bloco-07 (circuit breaker, 15/05, apos a P1) fica na 2.7.
**Remedido (`placar_100_gold_es2.log`, snapshots de 06/09; produto `eval_eixos`):**

| regime | 100% certo / 288 | 3 golds certos / 146 | bloco | unidade | subunidade |
|---|---|---|---|---|---|
| zero LLM | 155 -> **156** | 65 | 222/237 | 173 -> **180/191** | 117/233 |
| vocab (5 cursos, 205) | 173 -> 166 | 125 -> 119 | 188/202 | 183 -> 176/191 | 138 -> 132/151 |
| automatica | 238 -> **231** | 131 -> 125 | 231/237 | 185 -> 178/191 | 193 -> 187/233 |
| produto | 253 -> **246** | 138 -> 132 | 236/237 | 191 -> **184/191** | 199 -> 193/233 |

ES2: zero 6 -> 7/31 (unidade 18 -> 25/28) · automatica 28 -> 21 (unidade 28 -> 21, sub 26 -> 20) · produto 29 -> 22 (unidade 28 -> 21, sub 27 -> 21).
Leitura: o produto e a automatica seguiam o alias 'API gateway'/'discovery' que o vocab LLM pendurou na 2.7; o gold, feito junto com a curadoria,
concordava (in-sample). O oraculo discorda dos dois: **7 erros de unidade e 6 de subunidade do LLM estavam escondidos pelo gold**; o motor puro
sem vocab, que preenche por posicao, estava certo. Nos 93 dos 4 cursos afinados o produto passa de 93/93 para 86/93 e a automatica de 87 para 81.
**Crivo das outras 7 divergencias gold x posicao no Moodle (`coerencia_moodle.log` / `auditoria_gold.csv`), pela mesma lei:**
- ES2 roteiro1, roteiro1-introducao (Moodle -> bloco-01; gold bloco-02): MANTIDO. Na secao 'Microsservicos' o Roteiro 1 esta entre o label
  "Semana 30/03 a 03/04: feriado" e o label "10/04: discovery"; a auditoria pulou o label do feriado (sem bloco-aula) ate o de 20/03. O
  professor o pos logo apos a aula de 27/03 "microsservicos no Spring (introducao)" = bloco-02. Artefato da heuristica, nao do professor.
- TCC 3dm-caetano..., programacao-inteira-01-20260617 (Moodle 'secao' -> bloco-22/23; gold bloco-25): MANTIDO. Secao "Semana 14 - Apresentacoes
  T2" sem data; SARC "oficina de problemas, entrega T2" em 12/06 = bloco-25.
- SO laminas-cs-4244-sockets, laminas-sockets-alternativo (Moodle 'faixa de irmaos' -> bloco-06/07; gold bloco-09): MANTIDO. No card, o label
  "Sockets" vem depois de "14/04 IPC (pipes, fifo)"; o SARC de 23/04 (bloco-09) e "comunicacao entre processos, pipes, filas". A 'faixa' e o
  intervalo dos irmaos datados, nao uma afirmacao sobre sockets.
- MF t2-2026-1 (Moodle label "Trabalho 1 (06/05)" -> bloco-11; gold bloco-18): a posicao do Moodle e artefato (o label "Trabalho 2:" nao tem
  data e a auditoria herdou o do T1). Mas o gold bloco-18 (aula "verificacao de modelos, ferramenta", 29/06; relabel de 25/08) nao tem
  evidencia do professor: o SARC diz "prova P2, entrega do T2" em **06/07 = bloco-20 (kind assessment)**, e o texto do T2 cita Dafny 3x (nao
  cita NuSMV/Kripke). Nenhum gold dos 6 cursos aponta para bloco de prova (kinds no gold: class, deliverable, review, overview). **ABERTO
  (decisao do user):** gold -> bloco-20 (bloco de prova passa a hospedar entrega) ou scorable=no.

"""
edit(T, anchor, SEC + anchor)

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "**Placar por material (06/09 noite):** `python docs/reports/_harness-2026-09-04/c1-3/placar_100.py` (snapshots em `c1-3/snap_placar/`; "
        "zero LLM 155/288 · automatica 238/288 · produto 253/288 com todos os golds certos; CG automatica 56/83). Tracker §PLACAR CONSISTENTE.\n",
        "**Placar por material (06/09 noite, gold do ES2 corrigido pelo oraculo):** `python docs/reports/_harness-2026-09-04/c1-3/placar_100.py` "
        "(snapshots em `c1-3/snap_placar/`; zero LLM 156/288 · automatica 231/288 · produto 246/288 com todos os golds certos; CG automatica 56/83; "
        "produto unidade 184/191, sub 193/233). Tracker §PLACAR CONSISTENTE e §LEI REAFIRMADA. **Lei: SARC e Moodle > gold** (user, 06/09 noite).\n"
        "**Aberto:** gold do MF `t2-2026-1` (SARC: entrega do T2 em 06/07 dentro do bloco da P2; gold bloco-18 sem evidencia do professor).\n")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `placar_100_gold_es2.log` (placar com o gold do ES2 corrigido pelo oraculo) · `docs_c1_3u.py`.\n", encoding="utf-8")
print("docs ok")
