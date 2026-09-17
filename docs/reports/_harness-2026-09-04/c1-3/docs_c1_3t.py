"""Registro (06/09 noite, sessao 6): tela de login (raiz + correcao na sync 6d68578), reparo registrado do CG (404f5f9) e seu efeito
no gold, placar consistente por material x regime (placar_100). Sem args."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
anchor = '## CAUSA RAIZ DAS DUVIDAS DE BLOCO — JANELA ∩ UNIDADE DA SECAO + FILA SEM CERIMONIA (06/09, sessao 6; user: "encontrar o real motivo")'
SEC = """## PLACAR CONSISTENTE POR MATERIAL x REGIME + TELA DE LOGIN (raiz e correcao) + REPARO DO CG (06/09 noite, sessao 6; user: "quantos arquivos estao 100%? qual versao do motor deu qual resultado?")
**Tela de login — raiz medida (nao e timeout nem desconexao):** a sync (`moodle_sync.plan_import`) criava, para cada pagina do Moodle
(`mod/page`), uma entry `url` -> `moodle.pucrs.br/mod/page/view.php?id=N`; o conversor de URL (`url_fetcher`) busca sem sessao e o Moodle
devolve a tela de login. O pull ja salvava o HTML real (com token) em `<pull>/raw/moodle/pages/<N>-<slug>.html` e a sync nao o usava.
**Correcao definitiva na sync (`6d68578`):** `plan_import(root=...)` prefere o HTML salvo (entry `html`, MESMO id via `id_override`) e so cai
para URL quando nao ha HTML; teste `test_pagina_do_moodle_com_html_salvo_vira_entry_html_com_o_mesmo_id`. Curso novo: a pagina nasce com texto.
**Reparo registrado do CG (`c1-3/repara_paginas_cg.py`, CG `404f5f9`, tripwire, 0 chamadas):** 16 entries url -> html com o texto real
(275-2281 chars, login=nao), ids/golds/curadoria intactos; bloco 0 mudancas; build incremental local + reprocess.
**Efeito do reparo no gold de subunidade do CG (82):** produto 58 -> 56 (+3 -5) · automatica 58 -> 55 · holdout puro 47 -> 45. Ganhou 3
(deteccao de colisao, introducao ao processamento, morfologia: paginas antes vazias). **Perdeu 5 paginas-INDICE de videos** (curvas
parametricas -> hermite 4,84; manipulacao de imagens -> segmentacao 4,46; modelagem geometrica -> csg 8,58; visualizacao 3d -> paralela 12,40;
mapeamento -> empate exato 4x): o texto real lista videos de varios filhos do topico, o vocabulario puxa o filho mais citado, e o gold (= a
secao do Moodle) e o topico-pai. Antes, com o texto de login, o titulo sozinho caia no pai por acaso (winner_score 0,12-0,94). E a classe
"pai x filho" ja diagnosticada (5): agora 10 dos 27 residuais. **Candidata (hipotese, nao medi):** texto que cobre >= N irmaos com forca
comparavel -> subtopico-pai / o que a secao nomeia (S1 "sempre" foi medida em 06/09 e perdia; esta e mais estreita). Fila: 93 -> 96 (+3
sub-empate/ambigua nas paginas com texto) = **27,6/100** (CG 47 = duvida 25 + mudou 22 · MF 11 · SO 10 · IA 4 · ES2 12 · TCC 7 · LR 0 · FR 5).
**Placar consistente (`c1-3/placar_100_runs.py` + `placar_100.py`; snapshots `snap_placar/{zero,vocab,auto}/`, produto = originais; tripwire, 0
chamadas; CG apos o reparo):** 288 materiais com algum gold nos 6 cursos (bloco 237, unidade 191, subunidade 233); 146 com os TRES golds
(so nos 5 cursos: o CG nao tem gold de unidade). "100% certo" = acerta todos os eixos em que tem gold.

| regime (o que usa de LLM) | 100% certo / 288 | 3 golds certos / 146 | bloco | unidade | subunidade |
|---|---|---|---|---|---|
| zero LLM: sem vocab, sem voter, sem curadoria | **155 (53,8%)** | 65 (44,5%) | 222/237 | 173/191 | 117/233 |
| vocab (1 chamada por curso), so os 5 cursos | 173/205 (84,4%) | 125 (85,6%) | 188/202 | 183/191 | 138/151 |
| automatica = vocab + voter com cache (tutor novo) | **238 (82,6%)** | 131 (89,7%) | 231/237 | 185/191 | 193/233 |
| produto = + curadoria humana | **253 (87,8%)** | 138 (94,5%) | 236/237 | 191/191 | 199/233 |

Por curso (100% certo / com gold), zero -> automatica -> produto: MF 50 -> 56 -> 59 /66 · SO 27 -> 32 -> 39 /39 · IA 3 -> 39 -> 42 /42 ·
ES2 6 -> 28 -> 29 /31 · TCC 23 -> 27 -> 27 /27 · **CG 46 -> 56 -> 57 /83**. Leitura: sem vocab a subunidade e 50% e a IA vai a 4/39 (o plano
nomeia categorias, o material nomeia algoritmos; ES2 unidade 18/28 sem vocab, 28/28 com); o vocab (1 chamada) leva os 5 cursos afinados a 85%
por material; o voter paga bloco (+7 nos 5: 189 -> 196/202; CG 33 -> 35) e nada de subunidade; a curadoria paga 15 materiais. **O numero para planejar um tutor
novo e o do CG automatica: 56/83 = 67% dos materiais com bloco E subunidade certos (bloco 35/35, sub 55/82); sem LLM nenhum, 46/83 = 55%.**
Os 4 cursos afinados dao 94-100% no produto porque a curadoria nasceu com o gold (in-sample).
**Sem gold (FR do zero, 20 materiais, sandbox):** run A (0 chamadas) unidade 19/19 pela secao do professor; concorda com o FR curado em bloco
13/20, sub 11/20; fila 10/20. Run B (Gemini ~22 chamadas) concorda 19/20, 20/20, 17/20; fila 6/20.
**O que falta para o tutor 100% automatico (medido, nao opiniao):** (1) a ponte de vocabulario categoria -> algoritmo, unica coisa que hoje so o
LLM da (+57 sub/+10 unidade nos 93; sem ela IA 4/39); fontes deterministicas ja tentadas e refutadas: IDF/similaridade/card/stem; (2) posicao
datada no Moodle (labels "Semana dd/mm"): existe em 5 cursos, nao em CG/LR/FR, e e o que faz o bloco sem voter (CG puro 33/35); (3) ordem dos
modulos na secao (API do Moodle, ja no pull): alavancas medidas em 02/09 (+7/-1 e +12/-5) e ainda fora do motor; (4) regra pai x filho acima.
Gold: so mede; o aluno nunca cria gold.

"""
edit(T, anchor, SEC + anchor)

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Tutores (06/09 noite, apos fila + decomposicao): **MF `ed31d99`",
        "Tutores (06/09 noite, apos o reparo do CG): **MF `ed31d99` · SO `c60e2d1` · IA `d88cc53` · ES2 `0fe0f53` · TCC `79a9696` · LR `5201deb` · FR `5c9372a` · CG `404f5f9`** "
        "(reparo registrado das 16 paginas do Moodle, `c1-3/repara_paginas_cg.py`, 0 chamadas; gerador `6d68578` corrige a sync). Historico — Tutores (06/09 noite, apos fila + decomposicao): **MF `ed31d99`")
edit(H, "## Artefatos publicados (todos atualizados em 06/09 noite)",
        "## Artefatos publicados (todos atualizados em 06/09 noite; 2a rodada apos o reparo do CG e o placar por material)")
edit(H, "Revisao da fila `revisar_queue.md` (45) do CG.",
        "Revisao da fila `revisar_queue.md` (45) do CG. Fila 'conflito' (50, 0 erros de unidade) e sub-ambigua (13, 1 erro). Regra pai x filho "
        "para paginas-indice (10 dos 27 residuais do CG apos o reparo; hipotese, nao medida). Recompilar o vocab do CG sem o alias 'OpenGL' "
        "(9 gold-vazio; exige Gemini). Blocos sem unidade (entrega/revisao): adiado pelo user.")
edit(H, "## COMECE POR (proxima sessao) — tres decisoes do user antes de qualquer codigo\n",
        "## COMECE POR (proxima sessao) — tres decisoes do user antes de qualquer codigo\n"
        "**Placar por material (06/09 noite):** `python docs/reports/_harness-2026-09-04/c1-3/placar_100.py` (snapshots em `c1-3/snap_placar/`; "
        "zero LLM 155/288 · automatica 238/288 · produto 253/288 com todos os golds certos; CG automatica 56/83). Tracker §PLACAR CONSISTENTE.\n")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### Sync prefere o HTML salvo pelo pull para paginas do Moodle (tela de login era a sync, nao timeout); reparo registrado do CG

**Date:** 2026-09-06
**Status:** Active
**Decision:** `moodle_sync.plan_import(root=...)`: pagina do Moodle (`mod/page`) com HTML salvo em `raw/moodle/pages/<id>-*.html` vira entry `html` com o mesmo id (`id_override`); URL so quando nao ha HTML (`6d68578`, teste). CG reparado por script registrado (`c1-3/repara_paginas_cg.py`, CG `404f5f9`): 16 entries url -> html, ids/golds intactos, 0 chamadas.
**Reasoning:** Pergunta do user ("como assim tela de login? timeout?"). Medido: a entry url era buscada sem sessao pelo `url_fetcher`; o pull ja tinha o HTML real. Tratar a raiz na sync serve o curso novo automaticamente.
**Consequences:** CG com texto nas 16 paginas. No gold de subunidade do CG o texto real custou 2 no produto (58 -> 56: +3 -5) e 3 na automatica (58 -> 55): 5 paginas-indice de videos vao para o filho mais citado e o gold (= secao) e o pai — classe pai x filho, 10 dos 27 residuais; candidata registrada, nao medida. Fila 27,6/100. Placar por material (`placar_100.py`): zero LLM 155/288, automatica 238/288, produto 253/288.
"""
assert "tela de login era a sync" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `placar_100_runs.py` (snapshots por regime em `snap_placar/`, gitignored) + `placar_100.py` (placar por material: 100% certo por regime) · "
             "`repara_paginas_cg.py [--dry-run]` (reparo registrado das 16 paginas do Moodle do CG, 0 chamadas) · `docs_c1_3t.py`. Logs `placar_100_runs.log`, `placar_cg_zero.log`, `placar_cg_auto.log`, `audita_gold_pos_reparo.log` (auditoria identica a de 06/09).\n", encoding="utf-8")
print("docs ok")
