"""Registro (07/09): consolidacao das duplicacoes (tiers A1, A2, B, C mecanico) com gate zero-diff; mapa das duplicacoes semanticas que
ficam documentadas. Args: 1 = hashes 'A1 A2 B C', 2 = suite final, 3 = README c1-3 extra (opcional)."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
HASHES, SUITE = (sys.argv + ["?", "?"])[1:3]


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
anchor = '## FILA DE REVISAO DO REGIME ZERO (SEM LLM) — ANATOMIA E RAIZES (07/09 madrugada; user: "um motor, camada LLM on/off; teto do puro; fila menor pela raiz")'
SEC = f"""## CONSOLIDACAO DAS DUPLICACOES DO MOTOR (07/09; user: "vamos antes resolver essas duplicacoes"; inventario em `c1-3/inventario_motor_2026-09-07.md`)
**Metodo:** refactor SEM mudanca de comportamento, um grupo por commit. Gate por commit: suite verde + **zero-diff nos 8 tutores**
(`c1-3/zero_diff.py --base|--check`: copia com `staging/`, 1 reprocess com tripwire, snapshot de 1017 artefatos derivados sem build/, raw/,
BUILD_REPORT, STUDENT_STATE, updated_at, last_seen; compara com a referencia do mesmo dia). Achado no caminho: o `determinismo.py` de
02/09 ignorava `staging/` e reprocessava LR/CG/FR/MF SEM o texto dos materiais (base_markdown em staging) — valia como determinismo, nao
como fidelidade; a referencia contra o original dava 56 arquivos por isso + datas. Auto-consistencia do gate novo: 0/1017.
**Commits (gerador, nada pushed): {HASHES}.**
- **A1** tokenizador de card/bloco unico (`text.tokens.card_stop_tokens`; `_tokens` era byte-identico em `timeline/card_block` e
  `timeline/block_identity`) · regex de numero de unidade so em `file_map` (`window_provider` importa) · leitor unico de `moodle_label`
  (`models.core.moodle_label_text`; 6 copias: disambiguator, window_provider, sources/moodle, resolver_apply, artifacts/navigation,
  core/vocabulary_compile). Suite 2341 · zero-diff 0.
- **A2** removido o caminho legado `routing/anchor_placement.py` (412 linhas atras de `use_anchor_placement`, default False, nunca ligado em
  produto) + `tests/test_anchor_placement.py` + ramo da flag em `ops/pedagogical_regeneration.py`; comentarios em `models/core.py` e
  `file_map.py`. Suite 2335 · zero-diff 0.
- **B** listas de genericos/stopwords centralizadas em `text/stopwords.py` com conteudo identico (bloco recortado, nao retipado) e alias no
  modulo de origem: `UNIT_MATCHER_GENERIC` (unit_matcher), `UNIT_TITLE_GENERIC` (content_taxonomy), `SEMANTIC_TOKEN_STOPWORDS`
  (semantic_config), `LABEL_PART_STOP` e `TOPIC_FALLBACK_STOPWORDS` (index), `MOTOR_GENERIC_STEMS` (disambiguator; coverage_rules e
  resolver_apply importam o canonico), `TOPIC_SUPPORT_STOP` (content_taxonomy inline), `FILE_MAP_TITLE_ANCHOR_STOP` e
  `FILE_MAP_TOPIC_ANCHOR_STOP` (file_map inline). Guard de identidade em `tests/test_stopwords_consolidation.py`. Suite 2336 · zero-diff 0.
- **C (mecanico)** regex identicas viram uma so em `text/patterns.py`: `SECTION_NUM_PREFIX_RE` (window_provider = resolver_apply) e
  `DATE_DMY_RE` (sources/moodle = motor/card_stream). Suite {SUITE} · zero-diff 0.
**Ficam DOCUMENTADAS, nao unificadas (semantica diferente; unificar = mudar comportamento = medir antes):**
- tokenizadores: `text.tokens.motor_tokens` (normalize_match_text, camelCase, digitos fora, stems genericos, short_vocab) x
  `unit_matcher._tokens` (norm_ascii_lower + `[a-z]+` >= 3 + UNIT_MATCHER_STOPWORDS) x `content_taxonomy._topic_support_tokens` (stem-5,
  >= 4) x `index._specific_tokens`/`_timeline_specific_tokens` x `resolver_apply._tokens_headings`/`_toks` x `concept_resolver._concept_tokens`.
  Regra daqui em diante: quem tocar um deles migra ESSE call site para `motor_tokens` parametrizado, com zero-diff ou medida.
- "data no nome": `window_provider._DATE_PREFIX_RE` (dd/mm prefixo, `\\b`) x `moodle._DATE_PREFIX` (aceita ano) x `card_stream._DATE_DM`
  (lookahead negativo) — tres contratos.
- "nome do curso e boilerplate": `window_provider._course_stems` (stems de _topic_tokens) x `disambiguator drop = _toks(course_name)` x
  `content_taxonomy course_norm` x `stopwords.resolve_unit_generic_tokens`.
- IDF/raridade x3 (file_map 1/df entre unidades; concept_resolver 1/freq entre blocos; stopwords df >= 0,4) e "token exclusivo" x3
  (unit_matcher, file_map distinctive, resolver_apply subtopico): eixos diferentes, formulas parecidas — candidatos a um helper quando um
  passo do plano os tocar.
- "a secao nomeia X" x2 (`window_provider.unit_named_by_section`, `resolver_apply._secao_nomeia_subtopico`): mesma forma, eixos diferentes;
  o passo 4 do plano (topico do bloco como ultimo recurso da subunidade) e o momento de unificar a forma.
- heranca de unidade por vizinho x2 (`file_map.unit_of_block_or_neighbor`, `index` soft-continuation): entry x bloco.
- codigo morto que FICA de proposito: `file_map.timeline_block_matches_preferred_topic` (passo 4 religa) e o parametro `block_confidence`
  de `reconcile_unit_with_block` (passo 2 religa).

"""
edit(T, anchor, SEC + anchor)

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "**Placar por material (06/09 noite, gold do ES2 corrigido pelo oraculo):**",
        f"**Consolidacao das duplicacoes (07/09, commits {HASHES}):** gate `c1-3/zero_diff.py --base` (referencia do dia) / `--check` (0 arquivos = comportamento "
        "preservado); tokenizador de card unico, leitor unico de moodle_label, legado anchor_placement removido, listas em `text/stopwords.py`, regex em "
        "`text/patterns.py`; o que fica diferente por semantica esta listado no tracker §CONSOLIDACAO. Regra: nenhum filtro/tokenizador novo; migrar call site "
        "para `motor_tokens` so com zero-diff ou medida.\n"
        "**Placar por material (06/09 noite, gold do ES2 corrigido pelo oraculo):**")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Um motor, camada LLM on/off; consolidacao antes de alavanca; gate zero-diff

**Date:** 2026-09-07
**Status:** Active
**Decision:** (1) Nao ha "duas versoes" do motor: o mesmo codigo com as camadas LLM (vocab, voter, resumos) ligadas ou desligadas; o nucleo deterministico deve ser honesto (duvida em vez de palpite) e a camada LLM so preenche duvida/vazio e acrescenta aliases, nunca vira decisao tomada pela estrutura do professor (secao, escopo de prova, vencimento). (2) Antes de qualquer alavanca nova, consolidar duplicacoes; refactor so com zero-diff nos 8 tutores (`c1-3/zero_diff.py`). (3) Nenhum filtro de token ou provedor novo: reusar `text/stopwords.py`, `text/patterns.py`, `text/tokens.motor_tokens`; religar codigo morto antes de escrever regra nova.
**Reasoning:** Pedido do user ("um motor, camada LLM on/off", "nao quero band-aid"). Inventario (`c1-3/inventario_motor_2026-09-07.md`): 14 duplicacoes, 8 tokenizadores, 5+ listas de genericos, codigo morto. ES2 mostrou o LLM vencendo o calendario do professor (7 unidades); IA mostrou o puro confiante-errado por ima de headings.
**Consequences:** Commits {HASHES} (comportamento identico por gate); mapa do que fica diferente por semantica no tracker. Plano seguinte: ima de headings (taxonomia), religar block_confidence + token compartilhado, prova como marco no F5 + due-window em prova, religar topico do bloco na subunidade, medir residuo do card_stream.
"""
assert "consolidacao antes de alavanca" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `zero_diff.py --base|--check` (gate do refactor: 1 reprocess nas copias COM staging x referencia do dia; 0 = comportamento preservado) · logs `zero_diff_*.log`, `tier*_pytest.log` · `inventario_motor_2026-09-07.md` · `docs_c1_3w.py`.\n", encoding="utf-8")
print("docs ok")
