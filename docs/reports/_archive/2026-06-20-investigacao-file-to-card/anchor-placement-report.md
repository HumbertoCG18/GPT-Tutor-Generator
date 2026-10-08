# Anchor Placement — Relatório de Execução

## Status: COMPLETO (não commitado)

## Arquivos novos/tocados (working tree, NÃO commitados)

- `src/builder/routing/anchor_placement.py` — módulo novo (puro, sem I/O)
- `tests/test_anchor_placement.py` — 5 testes TDD

## Resumo de testes

```
1594 passed in ~14s
```

5 novos testes verdes; zero regressões.

## API do módulo

```python
from src.builder.routing.anchor_placement import resolve_placement, AnchorResult

result = resolve_placement(
    entry,          # dict da entry do manifest
    blocks,         # lista de blocos do timeline index (com block_uuid injetado)
    scorer_resolver=fn,  # callable(entry, blocks) -> block_uuid
    year=2026,      # ano civil para converter DD.MM em datas absolutas
)
# result.block_uuid, result.method ("manual"|"anchor"|"scorer")
# result.section, result.window_start, result.window_end (se anchor)
# result.changed (bool)
```

Função auxiliar para o canário:
```python
rows = compute_ia_canary(entries, blocks, year=2026, scorer_resolver=fn)
# lista de dicts: entry_id, current_uuid, new_uuid, method, changed, section, window_start, window_end
```

## Design — decisões

**Cadeia de precedência por entry:**
1. `manual_timeline_block_id` presente e válido no ledger → `method="manual"`
2. `source_section` tipo "semana" → parse datas + tópico → sessão real no período + overlap de tópico (stem 8 chars) → `method="anchor"`
3. fallback scorer → `method="scorer"`

**Dispatch plugável por tipo de seção:**
- `_detect_section_type()` detecta "semana" via regex `_SEMANA_RE`
- `"topico"` e `"label"` retornam `None` (fall-through; fases seguintes)

**Stemming leve (8 chars):** resolve flexão PT — "supervisionado"/"supervisionada" viram "supervis" e casam. Validado empiricamente nos dados reais do IA.

**Janela com virada de mês:** "30.03 a 01.04" → `win_end` avança um mês automaticamente.

**Validação de tópico obrigatória:** overlap == 0 → âncora falha → scorer. Capturou real mismatch: "Semana 12 - Algoritmos de Busca" mas bloco-12 tem sessões de "Correção P1 + Introdução a Agentes" — exatamente a lição SO.

## IA Breakdown (50 entries, computado em memória)

| Método | N |
|--------|---|
| anchor | 37 |
| manual | 5  |
| scorer | 8  |
| TOTAL  | 50 |

**Entradas que o anchor MOVEU vs computed_block_id atual:** 37 de 37 anchors.  
(Todos os entries com source_section semana válida tinham computed_block_id legacy `bloco-NN` ou uuid diferente.)

### Scorer fallback — por quê:
- 2 sem source_section: `aprendizadosupervisionado-arvoresdedecisao-duncan`, `inteligencia-artificial-aula-29-...`
- 1 TDE admin: `prova-1-2024-02` (seção "TDE Trabalho Discente Efetivo")
- 5 topic-mismatch real: `cap-sobre-algoritmos-geneticos`, `algoritmo-genetico`, `introducao-a-busca-informada`, `outros-operadores`, `programa-exemplo-ag` — todos em "Semana 12 - Algoritmos de Busca com Informação", mas bloco-12 na janela (18.05-22.05) tem sessões de "Correção P1 + Introdução a Agentes". Anchor FALHA corretamente.

### Nota sobre manual:
5 entries com `manual_timeline_block_id`, contra os 2 esperados pelo brief. Os 5 reais:
- 2 sem section (Oracle, IA Responsável)
- 1 em TDE section (p1-2024-02-ia → bloco-08)
- 2 com section semana normal (artigo-usando-k-nn-em-texto, artigo-usando-agrupamento)

### Delta estimado vs brief:
Brief previa ~44 anchor, 2 manual, 2 TDE, 2 sem-seção.  
Real: 37 anchor, 5 manual, 1 TDE→scorer, 2 no-section→scorer, 5 topic-mismatch→scorer.  
Diferença: 5 mismatch reais na Semana 12 que a estimativa não capturou (lição SO em ação).

## Prova read-only

- `manifest.json` mtime: 2026-06-20T13:45:46 (inalterado — Task 4)
- `.block_identity.json` mtime: 2026-06-20T13:45:46 (inalterado — Task 4)
- `git status` do IA: apenas arquivos pre-existentes modificados/untracked (nenhum do canário)
- Outros 4 repos: não tocados

## Concerns

1. **Semana 12 mismatch (5 entries):** O cronograma do professor nomeou a seção "Algoritmos de Busca com Informação" mas as aulas de 18-22/05 (bloco-12) foram de Correção P1 + Introdução a Agentes. O anchor falha corretamente; esses 5 entries ficam com o scorer. Ao curar o timeline, se o professor mover as sessões, os anchors passarão a funcionar automaticamente.

2. **5 entradas manual (vs 2 estimadas):** Dois artigos com `manual_timeline_block_id` também têm source_section válida — mas `manual` vence sempre por design (Tier 1). Correto conforme brief.

3. **bloco_uuid não no timeline_index:** O timeline_index não persiste `block_uuid` nos blocos (campo ausente). O canário injeta via ledger_map. Em produção, a injeção já ocorre em `reattach_block_uuids`. Módulo puro funciona com qualquer bloco que tenha `block_uuid` OU `id` (fallback ao display_id).
