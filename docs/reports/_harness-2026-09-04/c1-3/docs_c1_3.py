"""Registro do C1 item 3 (medido, refutado) no tracker, handoff e decisions. Idempotente por assert."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str, count: int = 1) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == count, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


# ---------- tracker ----------
T = GEN / "docs/reports/pendencias.md"
edit(T, "last_updated: 2026-09-05 (sessao 5 encerrada; C0 FECHADA 11/11; C1 itens 1 e 2 FEITOS; gold pelo oraculo;",
        "last_updated: 2026-09-05 tarde (sessao 6; C0 FECHADA 11/11; C1 itens 1-3 FEITOS — o 3 por medicao, REFUTADO; gold pelo oraculo;")
SEC = """## C1 ITEM 3 — `title` DO MANIFEST = `moodle_label` (05/09 tarde, sessao 6, MEDIDO sem LLM; **FECHADO POR MEDICAO: REFUTADO, 0 codigo**)
**Premissa do handoff:** o rebuild grava `title` = nome do arquivo e o piso sem-llm do CG caiu 10 -> 5; "medir title := label (fallback nome); se 0, fecha".
**Lido antes de medir:** o piso (`eval_travessia.escolher_sem_llm`) e o `entry_tokens` do disamb somam title + label num CONJUNTO; title := label
nao ACRESCENTA token, so REMOVE os que vinham do nome do arquivo. Leitores do `title` sozinho no motor: 9 (`leitores_title.py`); em 211/348
entries reescriviveis, mudam de saida: ordinal 0 · `_exam_number` 0 · prep 0 · stems do due 0 · datas 0 · numero de unidade 0 · `_REVISAO_RE` 2 (ES2
`servicos`/`web`, label "revisao de conceitos") · `split_camel_case(title)` no texto combinado 133 · `entry_tokens` 103 (token so do title perdido).
**Medicao A — piso sem-llm, title := label em memoria (0 chamadas):** IA (14 titles) 10/15 -> 10/15, hit@3 12 -> 12, bloco 6/8 -> 6/8 · FR (0
titles: sem label) 9 -> 9 · CG (67 titles) 5 -> 5, hit@3 6 -> 6, bloco 10/11 -> 10/11. **0 flip.** A queda 10 -> 5 do CG foi medida entre manifests
diferentes (export 73 x rebuild 93, gold re-chaveado) e NAO e o title.
**Medicao B — motor puro +vocab nas copias (baseline reproduzido 186/199 conf-err 1 · 183/191 · 53/57 · sub 82/93; holdout CG 31/35 conf-err 0 flagados 14):**
| regua | antes | title := label (143 titles nos 5; 67 no CG) |
|---|---|---|
| bloco | 186/199, conf-err 1 | **184/199**, conf-err 1 — MF `exercicios-conjuntos`, `exercicios-arrays` 13 -> 12 (gold 13; label "Respostas" perde `conjuntos`/`arrays`) |
| confiantes | — | MF `colecoes-arrays`, `colecoes-sequences` alta -> media + flag (label "Exemplos (Arrays)" perde `colecoes`) |
| unidade · cobertura | 183/191 · 53/57 | iguais |
| subunidade | 82/93 | **81/93** — SO `0704-exemplo-threads-em-java` conceitos-basicos -> escalonamento (0 token perdido; texto combinado) |
| holdout CG | 31/35, conf-err 0, flag 14 | iguais; 10 subunidades mudam sem gold (4 somem, 3 nascem, 3 trocam) |
**0 flip positivo em regua nenhuma.** O nome do arquivo e o label do Moodle sao sinais COMPLEMENTARES: o label e generico onde o professor nomeia o
modulo pela funcao ("Respostas", "Exemplos (Arrays)", "Introducao"); o stem carrega o assunto. Nos 8: 103 entries tem token no title que o label nao
tem (MF 35, CG 34, ES2 23); 7 tem label sem token de conteudo e title com (MF 6 "Respostas", CG `vis2d` "Introducao").
**Decisao (registrada em decisions.md):** `title` do manifest FICA o stem; o label e coluna (FILE_MAP, item 1), nao substituto. Item 3 fecha por medicao,
sem codigo; entra em NAO fazer. Achados para a fila LLM (so com Gemini liberado): (a) prompt do voter (`llm_vote.py:241`) mostra so `titulo`: 90/125
materiais votados tem label != title (CG 31, MF 31, ES2 16, SO 7, IA 5) — o voter ve "Vis3d", nao "Visualizacao 3D - Projecao"; adicionar linha `label
do Moodle` ao prompt e re-votar (<= 90 chamadas) e a alavanca com numero; (b) FILE_MAP titulo = label perde o stem em 103 linhas (7 sem token de
conteudo): "label · stem quando o title tem token que o label nao tem" so se a travessia LLM errar dessa forma.
**Censo remedido nesta sessao (originais):** revisar/100 **57,8** (handoff 58,0) · votos/100 **35,9** (36,5): MF pinos 4 -> 6 (arvores, listas, gold pelo
oraculo) = 2 votos a menos (2/348 = 0,6) — consistente, nao isolado. FILE_MAP 100% nos 8 (SO 38/39 duplicata). Suite 2324 · `src/` intocado.
Harness: `_harness-2026-09-04/c1-3/` (medicao A, shim da B, snapshot/diff, leitores, logs).

"""
edit(T, "## GOLD PELO ORACULO (05/09 ~04h30", SEC + "## GOLD PELO ORACULO (05/09 ~04h30")

# ---------- handoff ----------
Hf = GEN / "docs/reports/2026-09-05-handoff-fila-campanhas.md"
old_start = "## COMECE POR (proxima sessao) — C1 TRAVESSIA, item 3:"
old_end = ("   tracker; tutores so mudam por reprocess registrado (copia `.ablacao` antes); reprocess NAO commita quando so "
           "`updated_at` muda (caixa).\n")
t = Hf.read_text(encoding="utf-8")
i = t.index(old_start)
j = t.index(old_end) + len(old_end)
NEW = """## COMECE POR (proxima sessao) — C1 TRAVESSIA: itens 1-3 FEITOS (3 por medicao); o que falta e LLM (decisao do user: liberar Gemini)
0. Confirme o estado: `git status --short` (so `.claude/settings.local.json`, `.codex/` e `.mex/patterns/*` de outro agente podem aparecer),
   `git log --oneline -3`, HEAD dos 8 tutores iguais aos de "Estado ao comecar", `python scripts/censo_motor_llm.py` (revisar/100 57,8; votos/100
   35,9; FILE_MAP 100% nos 8, SO 38/39 por duplicata), `python -m pytest tests -q` (2324). Nada pushed.
1. **Item 3 FEITO por medicao (05/09 tarde, §C1 ITEM 3 no tracker): REFUTADO, 0 codigo.** Piso sem-llm com title := label: 0 flip nos 3 cursos;
   motor puro bloco 186 -> 184/199 (MF, label "Respostas" perde `conjuntos`/`arrays`), sub 82 -> 81, 2 confiantes viram flag; holdout CG igual.
   Nome do arquivo e label sao COMPLEMENTARES (103 entries tem token so no title); o motor ja soma os dois; o FILE_MAP ja mostra o label (item 1).
2. **Com Gemini liberado (decisao do user), nesta ordem, 1 rodada cada:** (a) travessia final IA/FR/CG modo LLM (~90 chamadas; alvo IA >= 14/15,
   FR 15/15, CG rerodado; ja medido apos o item 1: IA 14, FR 15, CG 10-11) — fecha a C1 se bater; (b) so se a travessia errar por indice: item 4
   (indice por unidade/termos) ou "FILE_MAP titulo = label · stem" (103 linhas); (c) prompt do voter com `label do Moodle` (90/125 votados tem
   label != title; re-voto <= 90 chamadas; entra so se conf-err cai sem regua regredir).
3. **Sem Gemini:** a C1 nao tem item sem LLM. Opcoes do user: liberar Gemini; ou adiantar da caixa um item byte-identico (reprocess nao commitar
   quando so `updated_at` muda; cache da normalizacao; `find_spec` no `write_build_report`) — e decisao de fila (C4 esta estacionada).
4. Gate de cada item: suite verde; sentinela 0 nos 8; determinismo 8/8 (so se `src/` mudar); curada intacta (198/199); commit com numero no
   tracker; tutores so mudam por reprocess registrado (copia `.ablacao` antes); reprocess NAO commita quando so `updated_at` muda (caixa).
"""
Hf.write_text(t[:i] + NEW + t[j:], encoding="utf-8")
edit(Hf, "Gerador `feat/motor-atribuicao` @ `77865a0`, 871 commits a frente de `main`.",
         "Gerador `feat/motor-atribuicao` @ `7c76a00` + docs do item 3 (sessao 6, 05/09 tarde), 871+ commits a frente de `main`.")
edit(Hf, "holdout CG puro 31/35 conf-err 0 (flagados 14) · curado 35/35 · censo revisar/100 58,0 · votos/100 36,5 ·",
         "holdout CG puro 31/35 conf-err 0 (flagados 14) · curado 35/35 · censo revisar/100 57,8 · votos/100 35,9 (remedido 05/09 tarde; 2 pinos MF) ·")
edit(Hf, "- **C1 TRAVESSIA — ABERTA; itens 1 e 2 FEITOS.** FILE_MAP completo e magro (80 KB, TRACE, titulo = label, Secoes 3/80) · titulo de bloco qualificado\n"
         "  so em colisao de aula (16) + CRONOGRAMA_DETALHADO em TCC e LR. Falta: item 3 (medir), item 4 (condicional), travessia final (LLM).",
         "- **C1 TRAVESSIA — ABERTA; itens 1, 2 e 3 FEITOS.** FILE_MAP completo e magro (80 KB, TRACE, titulo = label, Secoes 3/80) · titulo de bloco qualificado\n"
         "  so em colisao de aula (16) + CRONOGRAMA_DETALHADO em TCC e LR · item 3 medido e REFUTADO (title := label regride o motor puro 186 -> 184; piso 0).\n"
         "  Falta: travessia final (LLM), item 4 (condicional, LLM).")
edit(Hf, "### 1. ABERTA (05/09) — C1 TRAVESSIA (FILE_MAP completo e magro) — itens 1 e 2 FEITOS; falta 3 (medir, sem LLM), 4 (condicional) e a travessia final (LLM, so com liberacao do user)",
         "### 1. ABERTA (05/09) — C1 TRAVESSIA (FILE_MAP completo e magro) — itens 1, 2 e 3 FEITOS (3 refutado por medicao, §C1 ITEM 3); falta a travessia final (LLM) e o 4 (condicional, LLM) — so com liberacao do user")
edit(Hf, "**Medido e refutado em 05/09 (motor puro, copias):** peso do label do Moodle no desempate x2/x3 (50 -> 47/48 em 58) ·",
         "**Medido e refutado em 05/09 (motor puro, copias):** `title` do manifest := `moodle_label` (C1 item 3: piso 0; bloco 186 -> 184, sub 82 -> 81, 2 confiantes\n"
         "viram flag; label generico como \"Respostas\" apaga o assunto que o nome do arquivo carrega — stem e label sao complementares, o motor ja soma os dois) ·\n"
         "peso do label do Moodle no desempate x2/x3 (50 -> 47/48 em 58) ·")
edit(Hf, "## CAIXA DE IDEIAS (fora da campanha aberta; triagem so na fronteira)\nFormato: **ideia** · da para fazer? · quando (campanha)? · o que resolve no sistema?\n",
         "## CAIXA DE IDEIAS (fora da campanha aberta; triagem so na fronteira)\nFormato: **ideia** · da para fazer? · quando (campanha)? · o que resolve no sistema?\n"
         "- **Prompt do voter sem o `moodle_label`** (`llm_vote.py:241` mostra so `titulo`; 90/125 votados tem label != title: CG 31, MF 31, ES2 16 — o voter ve \"Vis3d\")\n"
         "  · sim, 1 linha no prompt + re-voto <= 90 chamadas · C1 fechamento (LLM) · voto com o nome humano; entra so se conf-err cai sem regua regredir.\n"
         "- **FILE_MAP titulo = label perde o stem** (103 linhas com token so no title; 7 com label sem conteudo: MF \"Respostas\" x6, CG `vis2d` \"Introducao\")\n"
         "  · sim: \"label · stem\" quando o title tem token que o label nao tem · C1 item 4 (so se a travessia LLM errar dessa forma) · roteador com os dois sinais.\n")

# ---------- decisions ----------
D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### C1 item 3: o `title` do manifest fica o nome do arquivo; o label do Moodle e coluna, nao substituto

**Date:** 2026-09-05
**Status:** Active
**Decision:** Nao substituir `title` por `moodle_label` no manifest (nem em `build_stash_entries`, nem por reprocess). O label ja e a coluna Titulo do FILE_MAP (item 1); o motor soma title + label em conjunto. Item 3 da C1 fecha por medicao, sem codigo; entra em NAO fazer.
**Reasoning:** Medido antes de codigo (sessao 6): piso sem-llm da travessia com title := label em memoria, 0 flip em IA/FR/CG; motor puro +vocab nas copias, bloco 186 -> 184/199 (MF `exercicios-conjuntos`/`exercicios-arrays`: label "Respostas" apaga `conjuntos`/`arrays`), sub 82 -> 81, 2 decisoes confiantes viram flag; holdout CG identico; 0 flip positivo. Nome de arquivo e label sao sinais complementares (103 entries tem token so no title; 7 labels sem token de conteudo). A queda do piso CG 10 -> 5 foi entre manifests diferentes, nao efeito do title.
**Consequences:** C1 so tem trabalho com LLM (travessia final; prompt do voter com label — 90/125 votados tem label != title; FILE_MAP "label · stem" so se a travessia errar). Sem Gemini, a proxima acao e decisao de fila do user.
"""
assert "C1 item 3: o `title` do manifest fica" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")
print("docs ok")
