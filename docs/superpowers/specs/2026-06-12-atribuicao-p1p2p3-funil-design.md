# Spec — Reforma do funil de atribuição: P1 (labels) + P2 (confiança) + P3 (higiene)

date: 2026-06-12
status: aprovada (brainstorm 12/06; decisão do usuário: juntar P1+P2+P3, P4 condicional)
base: `docs/reports/2026-06-11-plano-mestre-atribuicao.md` (revisado pós-M365)
insumos: `docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md` (5 formatos reais),
golden v1 (`tests/fixtures/eval/metodos_formais_golden.json`, baseline 27/46 = 58.7%),
harness do P0 (medição por task).

## Objetivo

Subir a precisão da atribuição automática arquivo→bloco e tornar a confiança
honesta, medindo no golden após cada task. Metas:

| Métrica (golden v1) | Baseline | Meta pós-ciclo |
|---|---|---|
| Acurácia geral | 27/46 (58.7%) | ≥ 75% |
| Confiante-e-errado (band alta + errado) | 6 | ≤ 2 |
| Cobertura do card_block_map (MF) | 5/9 seções (manual) | todas as seções com labels |
| `computed_block_method` preenchido | só código (18/56) | toda entry com bloco |

**P4 (scorer) é condicional**: decidido pelos números no fim deste ciclo. Se a
acurácia ficar < 85%, avalia-se P4 (IDF no scorer de bloco, CamelCase, sinal de
ferramenta); se ≥ 85%, P4 encolhe ou morre.

## Escopo

DENTRO: P1 (parser de labels A-D + card_block_map automático com merge manual),
P2 (confiança calibrada + teto por método + `computed_block_method` universal),
P3 (bugs B1, B4-verificação, B5-dedup de ids no import).

FORA: P4 (condicional); reparo de manifests antigos contaminados (source_section/
source_path de MF — ciclo próprio); segundo golden set de outra cadeira;
roteamento arquivo→dia por casamento nome↔descrição-da-aula (futuro).

---

## P1 — Parser de labels + card_block_map automático

### P1.1 Parser (módulo novo `src/builder/sources/moodle_labels.py`)

Funções puras, sem rede (recebem o payload de `core_course_get_contents`):

```python
def parse_card_dates(contents, year: int) -> dict:
    """{nome_secao_sanitizado: {"dates": [date...], "weeks": [(ini,fim)...],
        "format": "A|B|C|D", "lessons": [{"date": d, "text": s}...]}}"""
```

Cascata por seção (primeiro formato que casar):
- **A** (MF/ES2/TCC): módulos `label`, campo `description` (HTML → strip +
  unescape). Regex de semana `Semana\s+(\d{1,2}/\d{1,2}/\d{4})\s*a\s*(\d{1,2}/\d{1,2}/\d{4})`
  e de aula `\((\d{1,2}/\d{1,2}/\d{4})\)\s*:\s*(.+)`. Linhas
  `(atividade assíncrona):` ignoradas. Datas avulsas `\((\d{1,2}/\d{1,2}/\d{4})\)`
  fora do padrão (ES2 TDE) entram como lesson sem semana.
- **B** (IA): NOME da seção `Semana\s*\d+\s*-?\s*(\d{1,2}/\d{1,2})\s*a\s*(\d{1,2}/\d{1,2})`
  (sem ano → `year`; tolerar hífen colado e dia/mês sem zero) + label "Roteiro"
  com linhas `(\d{1,2}/\d{1,2})\s*[:\-]\s*(.+)`.
- **C** (UX): labels `Aula\s+\d+\s*-\s*(\d{1,2}/\d{1,2})` (sem ano → `year`);
  texto da aula = linha(s) `CONTEÚDO:` seguinte(s).
- **D** (Teoria): NOME da seção `Semana\s+(\d+)\b` SEM data. Só converte se o
  chamador fornecer `week_anchor` (data da 1ª semana letiva, derivável do
  cronograma da matéria); senão a seção fica SEM datas (degrada pra E).
- **E**: nada casou → seção fora do dict (sem entrada; nunca inventa).

Ano para datas curtas: extraído do semestre do curso (`parse_moodle_course`).
Validação: data inválida (ex. 30/02) é descartada com log, não exception.

### P1.2 Derivação card→blocos (`derive_card_block_map`)

```python
def derive_card_block_map(card_dates: dict, blocks: list) -> dict:
    """{secao: {"block_ids": [...], "source": "labels", "format": F,
        "dates": [iso...]}} — block_ids = blocos instrucionais cujo
    period_start..period_end contém alguma data de aula do card."""
```

- Considera só blocos não-`administrative_only`; datas de aula (lessons), não os
  ranges de semana (a semana pode conter feriado/prova de outro bloco).
- Card sem nenhuma data dentro de bloco algum → sem entrada (não inventa).
- Ordena `block_ids` cronologicamente.

### P1.3 Persistência com merge (import Moodle)

Em `import_moodle_courses` (moodle.py, onde contents + `repo_root` já existem):
após o backfill atual, deriva o mapa e grava em
`<repo_root>/course/.card_block_map.json` com merge:
- entrada existente com `source: "manual"` → PRESERVADA (manual sobrepõe auto);
- entrada com `source: "labels"` (de run anterior) → atualizada;
- entrada nova → adicionada com `source: "labels"`.
Sem `repo_root`/sem labels → no-op silencioso com contagem no resumo do import
("card map: N seções por labels, M manuais preservadas").

`_card_scoped_block` e `load_card_block_map` NÃO mudam — só passam a ter um mapa
com cobertura total.

### P1.4 Medição (critério de aceite do P1)

Script utilitário regenera o `card_block_map` de MF pelos labels e o golden é
re-gerado com ele (merge preserva decisões humanas). Aceite:
- mapa derivado de MF reproduz: "Exercícios de Revisão para Provas"→{bloco-07}
  (corrigido hoje), "Verificação de Programas"→{bloco-10..15} (cobertura nova);
- "Revisão - Lógica e Especificação" vira {bloco-03, bloco-04} (labels citam
  09/03 e 11/03) — prior mais largo porém correto; scorer desempata dentro;
- acurácia geral no golden ≥ 75% (de 58.7%); zero regressão nos casos hoje certos.

---

## P2 — Confiança calibrada + method universal

### P2.1 Margem relativa (src/builder/routing/thresholds.py)

`margin_confidence` hoje: `(winner − runner) + 0.18·winner` clampado [0,1] —
satura em 1.0 com scores 4-8 (46/56 entries em 1.0). Substituir por margem
RELATIVA com termo de força absoluta:

```python
def margin_confidence(winner: float, runner_up: float, k: float = MARGIN_K) -> float:
    """Margem relativa: quão à frente o vencedor está, escalada pela força
    absoluta dele. Não satura com scores grandes (bug do clamp aditivo)."""
    if winner <= 0:
        return 0.0
    rel = (winner - max(runner_up, 0.0)) / winner          # 0..1
    strength = min(1.0, winner / STRONG_SCORE)             # força absoluta
    return max(0.0, min(1.0, rel * (0.55 + 0.45 * strength)))
```

`STRONG_SCORE` (novo, thresholds.py) calibrado no golden durante a implementação
(ponto de partida: 3.0). Bands (alta/média/baixa) recalibradas no golden: cutoffs
viram constantes nomeadas com os números justificados no relatório do ciclo.
Assinatura preservada (mesmos chamadores).

### P2.2 Teto por método (thresholds.py + content_taxonomy.py)

Constantes novas e aplicação no fim da resolução do bloco:

| método | teto |
|---|---|
| `manual` | 1.0 |
| `review_rule` | 0.95 |
| `card` (gabarito 1-bloco) | 0.85 (CARD_SINGLE_CONF já existe — vira o teto) |
| `card+scorer` (gabarito 2+, scorer desempata) | 0.80 |
| `scorer_only` | 0.70 |
| `consensus` (código) | min(0.95, conf) |

Razão: "não há como ter certeza só com léxico" — o teto materializa isso.

### P2.3 `computed_block_method` universal (content_taxonomy.py)

Hoje só o caminho de código grava method. Passa a ser gravado para TODA entry
com bloco computado, no ponto da decisão em `resolve_unit_block_tags`:
`manual` | `review_rule` | `card` | `card+scorer` | `scorer_only` (os valores
`consensus`/`llm_only` do caminho de código continuam como estão). O editor já
tem o campo "Match do bloco" — passa a valer para tudo (verificar exibição).

### P2.4 Consumidores (verificação obrigatória)

Antes de mudar: mapear consumidores de `computed_block_confidence`/
`computed_block_band` (editor, triagem/manual-review, retag, artefatos) e
confirmar que bands recalibrados não quebram filtros. Task própria no plano.

### P2.5 Medição (critério de aceite do P2)

- Confiante-e-errado no golden: 6 → ≤ 2.
- Distribuição: % de entries com conf = 1.0 cai de ~82% para só os casos
  `manual` (a fixture sintética antiga continua 5/5 com bands recalibrados —
  se os bands mudarem os esperados da fixture, atualizar a fixture JUNTO com
  justificativa).

---

## P3 — Higiene

### P3.1 B1 — `references` fura o filtro de timeline

`_NO_TIMELINE_CATEGORIES` (content_taxonomy.py:961) = `{"cronograma",
"bibliografia", "referencias"}` — adicionar `"references"` (paridade com
navigation.py:607, que já tem). Teste: entry categoria `references` não recebe
bloco. (Caso real: `archive-of-formal-proofs-355fb8` levou bloco-06 conf 1.0.)

### P3.2 B5 — ids duplicados no import

`FileEntry.id()` por slug do basename colide (`introducao` ×2, `t1-2026-1` ×2 no
manifest real) e diretórios de assets usam o id → risco de sobrescrita. Fix no
IMPORT (lifecycle_ops, onde a entry nova entra no manifest): se o id já existe
com `source_path` DIFERENTE, sufixar com a categoria (`introducao-codigo-professor`)
ou contador (`introducao-2`) — primeiro a categoria; se ainda colidir, contador.
NÃO retroativo (manifest existente intacto; reparo é ciclo separado). Teste:
importar 2 arquivos de mesmo basename em categorias distintas → 2 ids únicos.

### P3.3 B4 — verificação pós-F1 (não é código novo)

Rodar `scripts/retag_manifest.py` no repo real de MF e confirmar que
`formalizacaoalgoritmos-recursao` (unit u02 + bloco u01) reconcilia ou flagra
`unit_block_conflict` (F1 já implementado). Registrar resultado no relatório do
ciclo. Se falhar → bug de F1, tratar como fix neste ciclo.

### P3.4 Critério de aceite do P3

Suíte verde; golden não regride; teste B1 e B5 novos verdes.

---

## Sequência de execução e medição

```
P1.1 parser → P1.2 derivação → P1.3 persistência → P1.4 regen golden + MEDIR
→ P2.4 mapear consumidores → P2.1 margem → P2.2 tetos → P2.3 method → MEDIR
→ P3.1 B1 → P3.2 B5 → P3.3 B4 (verificação) → MEDIR final
```

Após cada MEDIR: registrar placar no plano-mestre (tabela de fases). No fim:
decisão sobre P4 pelos números.

## Riscos

- **Margem relativa muda números que outros leem** — mitigado por P2.4
  (mapeamento de consumidores ANTES) e pela fixture sintética como rede.
- **Labels mudam de formato durante o semestre** (professor edita) — parser
  tolerante + formato E como degradação; o mapa é regenerado a cada import.
- **Formato D frágil** (semana ordinal sem âncora) — só ativa com `week_anchor`;
  caso contrário degrada, nunca inventa.
- **Prior mais largo no card Revisão** ({03,04} vs {02,03} manual) pode mudar
  2 casos hoje certos por sorte — o golden pega; aceite exige zero regressão.
- **Golden é 1 cadeira** — metas valem para MF; generalização medida quando
  houver segundo golden (fora do escopo).
