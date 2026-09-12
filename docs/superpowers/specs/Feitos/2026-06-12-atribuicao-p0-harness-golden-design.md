# Spec — P0 da reforma da atribuição: harness de medição + golden set real

date: 2026-06-12
status: aprovada (brainstorm 2026-06-12)
base: `docs/reports/2026-06-11-plano-mestre-atribuicao.md` (P0)
contexto: `docs/reports/2026-06-11-reanalise-atribuicao.md` (B3 provado, ground truth)

## Por que P0 primeiro

Sem harness funcional medindo dados reais, nenhuma fase posterior (P1-P4) prova
melhora — qualquer mudança no matcher vira fé. O `scripts/eval_assignments.py`
existe mas degenera com o índice persistido real (bug B3): mede um shape de
brinquedo, não o que produção produz. Esta spec entrega a rede de medição.

## Escopo

DENTRO: (1) corrigir B3 em produção aceitando ambos os shapes de bloco;
(2) gerar e versionar um golden set real do Metodos-Formais com ground truth
ancorado no cronograma; (3) o harness consome o golden real e imprime o placar.

FORA:
- Qualquer mudança no scorer/confiança/method (isso é P1-P4).
- Reparo dos dados contaminados (manifest/stash) — sub-fase do P1.
- Segundo golden set de outra matéria (risco transversal, depois).

## Componente 1 — Fix B3 (produção, cirúrgico)

### Causa raiz (provada)

`select_probable_period_for_entry` (src/builder/routing/file_map.py:1108) decide se
`candidate_rows` já são blocos prontos ou linhas cruas do cronograma:

```python
if candidate_rows and "rows" in candidate_rows[0]:
    blocks = list(candidate_rows)              # já são blocos
else:
    timeline_index = build_timeline_index(candidate_rows, ...)   # reconstrói
    blocks = list(timeline_index.get("blocks", []) or [])
```

A detecção usa a chave `rows`. Mas um bloco JÁ CONSTRUÍDO e serializado
(`build_timeline_index`, index.py:902-921, e o `.timeline_index.json` persistido)
NÃO tem `rows` — tem `id` + `source_rows` + `sessions`. `rows` é o shape de
ENTRADA (linha crua do cronograma). Logo, ao receber blocos persistidos, a detecção
falha, trata blocos como linhas cruas e reconstrói o índice em cima de dados já
processados → degenera (todas as entries caem em bloco-01, band baixa). Reproduzido
na re-análise.

### Correção (decisão: aceitar AMBOS os shapes)

Alargar a detecção de bloco pré-construído. Predicado novo:

```python
def _is_prebuilt_block(item: dict) -> bool:
    """Bloco já construído (não linha crua de cronograma).

    Legado: shape com 'rows'. Persistido (build_timeline_index / .timeline_index.json):
    'id' + 'source_rows'/'sessions'. Aceita ambos para o harness exercitar o índice
    real (cf. bug B3, re-análise 2026-06-11)."""
    if not isinstance(item, dict):
        return False
    if "rows" in item:
        return True
    return "id" in item and ("source_rows" in item or "sessions" in item)
```

E em `select_probable_period_for_entry`:

```python
    if candidate_rows and _is_prebuilt_block(candidate_rows[0]):
        blocks = list(candidate_rows)
    else:
        timeline_index = build_timeline_index(candidate_rows, unit_index=[unit] if unit else [])
        blocks = list(timeline_index.get("blocks", []) or [])
```

O caminho `rows` legado FICA (não migrar a fixture sintética atual — os 5 testes de
`tests/fixtures/eval/assignments_gold.json` continuam válidos).

### Risco

Baixo: muda só a classificação "isto já é bloco?", não o scoring. O único jeito de
um bloco persistido cair no `else` hoje é o bug; o predicado novo só captura casos
que hoje degeneram. Conferir que nenhuma LINHA CRUA de cronograma tem `id` +
`source_rows`/`sessions` simultaneamente (não tem — linha crua é
`{date, description, ...}`); se houver dúvida, o teste de regressão cobre.

### Teste

`tests/test_eval_b3_persisted_index.py` (novo): monta um índice no shape persistido
(blocos com `id`/`source_rows`/`sessions`, sem `rows`) com 2 blocos de topics
distintos; uma entry cujo texto casa o bloco 2. ANTES do fix prevê bloco-01
(degenerado); DEPOIS prevê bloco-2. Marcar o teste como a prova viva do B3.

## Componente 2 — Golden set real versionado

### Gerador

`scripts/build_golden_metodos_formais.py` (novo, roda 1×, offline, determinístico).
Entradas (caminhos como constantes no topo, документados):
- manifest real: `<repo Metodos-Formais>/manifest.json`
- índice da API: `<course>/.timeline_index.json` (blocos) e
  `<course>/.card_block_map.json` (gabarito seção→blocos)
- seção real por basename: derivada do `.card_block_map` + estrutura de cards
  (a seção correta de cada arquivo, agora confiável pós-M365).

Para cada entry do manifest:
1. Resolver `source_section_real` pela seção do arquivo (não o `source_section`
   contaminado do manifest — usar a seção real conhecida).
2. Consultar o gabarito `card_block_map[secao_real]`:
   - 1 bloco único → `expected_block_id` = esse, `expected_origin: "gabarito_1bloco"`.
   - 2+ blocos → `expected_block_id: null`, `expected_origin: "precisa_decisao"`,
     `candidates: [...]`.
   - sem entrada no gabarito → `expected_block_id: null`,
     `expected_origin: "sem_gabarito"`.
3. Sem seção real derivável (fora do stash, ambíguo) → `expected_origin: "excluido"`.

Saída: `tests/fixtures/eval/metodos_formais_golden.json`, versionado:

```json
{
  "subject": "Metodos-Formais",
  "generated_from": {"manifest": "...", "timeline_index": "...", "card_block_map": "..."},
  "timeline": { "blocks": [ <blocos no shape persistido, copiados do .timeline_index.json> ] },
  "cases": [
    {"id": "logicapredicados-semantica", "title": "...", "category": "material-de-aula",
     "source_section_real": "Revisão - Lógica e Especificação",
     "expected_block_id": "bloco-03", "expected_origin": "gabarito_1bloco",
     "candidates": [], "note": ""},
    {"id": "logicadehoare", "title": "LogicaDeHoare", "category": "material-de-aula",
     "source_section_real": "Verificação de Programas",
     "expected_block_id": null, "expected_origin": "precisa_decisao",
     "candidates": ["bloco-10","bloco-11","bloco-12","bloco-13","bloco-15"], "note": ""}
  ]
}
```

O `timeline.blocks` é copiado do `.timeline_index.json` REAL (shape persistido) —
é o que faz o harness exercitar o B3 corrigido.

### Ground truth e edição manual

Casos `precisa_decisao`/`sem_gabarito` têm `expected_block_id: null` e são listados
no fim do run do gerador para o usuário preencher à mão no JSON (decisão humana,
ancorada no cronograma real). O JSON é a fonte da verdade versionada; regerar
sobrescreve só os automáticos — **preservar `expected_block_id` preenchido à mão**:
o gerador, ao reescrever, mantém valores não-null já presentes para o mesmo `id`
(merge), nunca apaga decisão humana.

### Teste do gerador

`tests/test_golden_generator.py`: com fixtures mínimas (manifest 3 entries, card_map
com 1 seção→1 bloco e 1 seção→2 blocos), verifica: seção 1-bloco vira
`expected_block_id` preenchido + origin `gabarito_1bloco`; seção 2-blocos vira
`null` + `precisa_decisao` + candidates; entry sem seção vira `excluido`; merge
preserva `expected_block_id` manual num segundo run.

## Componente 3 — Harness consome o golden real

### Mudanças em `scripts/eval_assignments.py`

- Aceitar o golden real (campo `cases` com `expected_origin`, `source_section_real`).
  Retrocompatível com a fixture sintética atual (sem esses campos).
- `predict_block`: passar `timeline.blocks` (shape persistido) — já vai pelo caminho
  `_is_prebuilt_block` corrigido. Passar `source_section_real` para a entry sintética
  (campo `source_section`) para que o caminho do gabarito (`_card_scoped_block`)
  dispare quando houver seção — assim o harness mede COM e SEM seção.
- Métrica/placar impresso:
  - acurácia geral (sobre casos com `expected_block_id` não-null)
  - acurácia COM seção real vs SEM seção real
  - % confiante-e-errado (band alta + bloco errado)
  - **pendentes**: nº de casos `precisa_decisao`/`sem_gabarito` ainda com `null`
    (não contam como erro; reportados à parte)
  - excluídos: nº de casos `excluido`
- Casos com `expected_block_id: null` NUNCA contam como erro nem acerto — só
  engrossam "pendentes". O run não quebra por causa deles.

### Critério de aceite (do harness)

1. `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`
   roda sem erro e imprime o placar.
2. Reproduz erro conhecido: entries de Hoare/terminação caem no bloco errado pelo
   scorer (seção "Verificação de Programas" não tem entrada no `card_block_map`, então
   o gabarito não dispara nem com seção preenchida → decide o scorer fraco). É o
   sintoma que P1-P4 vão consertar; o harness só precisa EXIBI-lo, não corrigi-lo.
3. Casos `gabarito_1bloco` com seção real preenchida acertam (gabarito dispara).
4. Fixture sintética antiga (`assignments_gold.json`) continua 5/5 (retrocompat).
5. Suíte completa verde.

### Teste do harness

`tests/test_eval_golden_real.py`: golden mínimo inline (2 casos — 1
`gabarito_1bloco` que acerta, 1 `precisa_decisao` pendente); verifica que o placar
conta 1 acerto e 1 pendente, e que pendente não vira erro.

## Data flow

```
manifest real + .timeline_index.json + .card_block_map.json
   → [build_golden_metodos_formais.py] → metodos_formais_golden.json (versionado)
        (gabarito 1-bloco = auto; 2+/sem = null p/ decisão humana)
   → [eval_assignments.py <golden>] → resolve_unit_block_tags (scorer REAL, B3 ok)
   → placar: geral / com-seção / sem-seção / confiante-errado / pendentes
```

## Arquivos

- Modify: `src/builder/routing/file_map.py` (helper `_is_prebuilt_block` + uso em
  `select_probable_period_for_entry:1108`)
- Modify: `scripts/eval_assignments.py` (golden real + placar + pendentes)
- Create: `scripts/build_golden_metodos_formais.py`
- Create: `tests/fixtures/eval/metodos_formais_golden.json` (gerado, versionado)
- Create: `tests/test_eval_b3_persisted_index.py`
- Create: `tests/test_golden_generator.py`
- Create: `tests/test_eval_golden_real.py`

## Critérios de aceite (globais)

- B3 corrigido: índice persistido não degenera (teste de regressão verde).
- Golden set versionado existe, com ground truth automático onde há gabarito
  1-bloco e `null`+lista onde precisa decisão humana.
- Harness roda no golden real, imprime placar, reproduz os erros conhecidos,
  acerta os casos com gabarito.
- Pendentes/excluídos reportados, nunca contados como erro.
- Suíte completa verde; fixture sintética antiga intacta (retrocompat).
- Determinístico: sem disco/rede/Gemini.

## Riscos

- **Caminhos hardcoded no gerador** (repo Metodos-Formais, stash): documentar como
  constantes no topo; o gerador é um utilitário de dados, não código de produção.
- **Predicado `_is_prebuilt_block` capturar linha crua por engano**: mitigado pelo
  teste; linha crua de cronograma não tem `id`+`source_rows`/`sessions`.
- **Ground truth incompleto no 1º run**: esperado — os `precisa_decisao` ficam
  pendentes até o usuário preencher; o placar deixa isso explícito (não esconde).
- **Golden de 1 matéria só**: enviesa pra Isabelle/Dafny; segundo golden é trabalho
  futuro (risco transversal do plano-mestre).
