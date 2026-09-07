"""Registro (06/09, sessao 6): causa raiz das duvidas de bloco; janela ∩ unidade da secao (8856d89 + fix b421e92); fila sem janela-1
flagada/funil com voto; FR do zero A3/A4. Args: 1 = resumo do reprocess, 2 = determinismo, 3 = produto (eixos + sub 6 golds), 4 = fila/100."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
REP, DET, PROD, FILA = (sys.argv + ["?", "?", "?", "?"])[1:5]


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
anchor = "## FR DO ZERO — RUN A (06/09, sessao 6; user: \"faca FR em sandbox, numeros de precisao, sem gold\")"
SEC = f"""## CAUSA RAIZ DAS DUVIDAS DE BLOCO — JANELA ∩ UNIDADE DA SECAO + FILA SEM CERIMONIA (06/09, sessao 6; user: "encontrar o real motivo")
**Anatomia medida (produto, 8 cursos, 38 duvidas de bloco; gold de bloco onde existe):** janela-1 flagada 21 ("sinal indireto" por desenho; janela de
1 bloco por data no nome 9 / topico da secao 12) **14/14 certos** · funil com voto 16 (flag mantida por desenho apos o LLM decidir) **1/1 (+5/5 em
05/09)** · due-straddle 1 (1/1). **37 avisos por 0 erros de bloco = cerimonia**, como a camada llm. Nas copias automaticas: identico (14/14, 1/1).
**FR do zero (A2), 10 duvidas de bloco, causa ESTRUTURAL:** 8 vem do provider 'topic': os tokens do nome da secao ('camada', 'aplicacao') casam sessoes
do SARC de setembro a novembro -> janela de 6 blocos em 4 unidades com rotulos repetidos -> desempate flagado. O motor ja sabia a unidade (secao
'U2' = blocos 03 e 05) e nao a usava na janela. 2 sao sem janela nenhuma (poster png sem texto; lista da U1).
**Alavanca ENTROU (`8856d89` + fix `b421e92`, `window_provider.narrow_window_by_unit` no `anchor_engine.resolve_unscoped` logo apos
`resolve_window`; `MotorContext.units` carregado de `.content_taxonomy.json`):** janela ∩ blocos da unidade que a secao nomeia ('U<n>' via
`explicit_unit_number`, ou secao contida no/igual ao titulo da unidade). Nunca esvazia; **bloco SEM unidade (entrega/revisao/prova) fica na
janela** — a 1a versao o descartava e o MF `exercicioscorrecaoterminacao` perdeu a entrega bloco-11 (gold) da janela e virou erro confiante
(conf-err 0 -> 1 na automatica): corrigido, 4 testes (`tests/test_window_unit.py`). Alcance estatico: FR do zero 8 janelas, CG 23, SO 1, FR 10; gold
de bloco dentro da janela encolhida 16/16.
**Fila (`revisar.motivos_de`, `8856d89`):** janela-1 flagada e llm-funil com voto deixam de ser pendencia (a flag fica gravada como informacao).
Censo antes do reprocess: 57,5 -> 26,7 por 100 (duvida 71 + mudou 22). Testes adaptados (`test_revisar`, `test_moodle_sync`). Suite 2339.
**Gates (copias, tripwire, 0 chamadas; `janela2_*.log`):** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 138/151 · **holdout CG puro
bloco 31 -> 33/35** · CG sub puro 47 · automatica 193 conf-err 0 · 185 · 53 · 138 · holdout 35/35 · CG sub 58/82. Determinismo {DET}.
**FR do zero A4 (`rebuild_fr_a4.log`, 0 chamadas):** fila 11 -> 10/20 · concordancia com o produto bloco 11 -> 13/20, unidade 20/20, sub 11/20 ·
todos os materiais de U2 caem em blocos 03/05 (a janela encolhida). O que resta: 7 desempates 03 x 05 flagados (13/08 x 27/08: o SARC nao separa
"protocolos de aplicacao" de "desenvolvimento de aplicacoes" no texto de um zip de sockets) · 2 sem janela (poster png; lista da U1) · 1 empate de
subunidade. Candidata: sem janela + unidade nomeada -> janela = blocos da unidade (poster/lista da U1 -> [01, 02]).
**Reprocess registrado dos 8 (`c1-3/reprocess_8_janela.py`):** {REP}. **Produto:** {PROD}. **Fila {FILA} por 100.**

"""
edit(T, anchor, SEC + anchor)

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Unidade explicita da secao vence bloco (`1b41003`):",
        f"Janela ∩ unidade da secao (`8856d89`+`b421e92`) + fila sem janela-1 flagada/funil com voto: holdout CG puro 31 -> 33/35, FR do zero fila 11 -> 10, {FILA}/100; produto {PROD[:100]}.\n"
        "Unidade explicita da secao vence bloco (`1b41003`):")
edit(H, "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). ~~Fila de revisao: cortar a camada `llm`~~ (feito 06/09, `0673150`). Corrigir a extracao dos zips (2).",
        "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). ~~Fila: camada `llm`~~ (`0673150`), ~~janela-1 flagada e funil com voto~~ (`8856d89`). Resta: 'conflito' (53, 0 erros de unidade) e sub-ambigua (13, 1 erro). Corrigir a extracao dos zips (2).")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Janela de bloco ∩ blocos da unidade que a secao nomeia; janela-1 flagada e funil com voto deixam de ser pendencia

**Date:** 2026-09-06
**Status:** Active
**Decision:** (1) `narrow_window_by_unit`: quando a secao do Moodle nomeia a unidade ('U<n>' ou titulo), a janela de bloco fica so com os blocos dessa unidade mais os blocos sem unidade (entrega/revisao/prova); nunca esvazia (`8856d89`, fix `b421e92`). (2) `revisar.motivos_de`: janela-1 flagada e llm-funil com voto nao contam como duvida (`8856d89`).
**Reasoning:** Pedido do user: diminuir as duvidas sem LLM e sem fix especifico, pela causa raiz. Medido: no produto 37 de 38 duvidas de bloco eram flags por desenho com 0 erros de bloco no gold (14/14, 1/1); no FR do zero 8 de 10 vinham do provider 'topic' montando janela de 6 blocos em 4 unidades por tokens genericos do nome da secao. Gates: 5 cursos iguais; holdout CG puro 31 -> 33/35; a 1a versao descartava blocos sem unidade e criou 1 erro confiante no MF — corrigido antes de entrar. Determinismo {DET}.
**Consequences:** Reprocess registrado: {REP}. Produto: {PROD}. Fila {FILA}/100. Resta no FR sem LLM: desempate 03 x 05 dentro da unidade (SARC nao separa) e 2 sem janela — candidata: sem janela + unidade nomeada -> janela = blocos da unidade.
"""
assert "Janela de bloco ∩ blocos da unidade que a secao nomeia" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `reprocess_8_janela.py`; logs `janela_*.log` (v1, conf-err 1 no MF), `janela2_*.log` (fix), `rebuild_fr_a3.log`, `rebuild_fr_a4.log`, `reprocess_8_janela.log`, `determinismo_janela.log`.\n", encoding="utf-8")
print("docs ok")
