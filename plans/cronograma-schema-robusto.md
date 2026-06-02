# Plano — Schema Robusto de Blocos do Cronograma (100% precisão)

**Status**: Backlog priorizado. **Pré-requisito** de `material-agnostic-refactor.md` — sem schema confiável, o renderer agnóstico mostra lixo (53% dos blocos hoje têm defeito).

**Origem**: Auditoria de 5 cursos (`scripts/audit_timeline.py`, 92 blocos analisados) revelou:

| Status atual | N | % |
|---|---|---|
| ok | 19 | 21% |
| missing_topic | 22 | 24% |
| missing_unit | 27 | 29% |
| non_academic (bucket genérico) | 26 | 28% |
| unknown_gap | 3 | 3% |
| assessment (com falso positivo) | 1 | 1% |

A causa raiz é dupla: (a) modelo do bloco mistura **entrada de calendário** (que dia) com **conteúdo pedagógico** (unidade/tópico/material); (b) heurísticas espalhadas em 3+ lugares (taxonomy, regex assessment em `_timeline_row_is_review_or_assessment`, gap detection na UI). Cada consumidor reinventa "isso é defeito ou não-aplicável?".

---

## Visão

Bloco do cronograma vira **contrato schema-driven**:

- `kind`: enum fechado com 14 valores (catalogados a partir de dados reais).
- `KIND_REQUIREMENTS`: dict declarando quais campos cada kind exige.
- `block_status`: **derivado em read-time** de `kind + campos_presentes`. Nunca persistido.
- Classificador único (`classifier.py`) consolida toda heurística de detecção.
- Matcher genérico (`matcher.py`) atribui materiais com base em `kind`, não em tipo de arquivo (PDF/repo/URL).
- UI dummy: lê `block.status` + `KIND_DISPLAY[kind]` → renderiza por lookup table. Zero heurística no dashboard.

Resultado: novo kind = 1 linha no enum + 1 entrada em REQUIREMENTS + 1 entrada em DISPLAY. Zero refactor de matcher/UI.

---

## Princípios não-negociáveis

1. **Single source of truth** para classificação (classifier.py). Nenhum outro módulo detecta kind.
2. **Status sempre derivado**, nunca persistido. Não há "esqueci de atualizar status".
3. **Schema versionado** (`.timeline_index.json` v4) + validação JSON Schema em CI.
4. **Audit contínuo**: `scripts/audit_timeline.py` roda em CI; drift de cobertura quebra build.
5. **Render derivado, não fonte** (princípio herdado de `material-agnostic-refactor.md`): nada de duplicar dados.
6. **Auto-tags sobrevivem**: `auto_tags=bloco:bloco-NN` continua sendo o canal de attachment de materiais (mantém compat com pipeline existente).

---

## Enum fechado — 14 kinds

```python
class BlockKind(str, Enum):
    CLASS          = "class"           # aula regular com conteúdo
    ASSESSMENT     = "assessment"      # prova, P1, P2, PF, avaliação
    REVIEW         = "review"          # revisão p/ prova
    HOLIDAY        = "holiday"         # feriado
    SUSPENDED      = "suspended"       # suspensão, greve, paralisação
    MAKEUP         = "makeup"          # substituição / reposição
    ACADEMIC_EVENT = "academic_event"  # evento acadêmico, semana, simpósio, congresso
    OFFICE_HOURS   = "office_hours"    # atendimento, dúvidas, plantão
    WORKSHOP       = "workshop"        # oficina, lançamento de enunciados, kick-off
    DELIVERABLE    = "deliverable"     # entrega de trabalho final
    PLANNING       = "planning"        # planejamento, reunião, conselho
    RESERVED       = "reserved"        # reserva técnica
    RESULTS        = "results"         # divulgação de resultados, devolução
    UNKNOWN        = "unknown"         # escape hatch — flag manual review
```

### Requirements matrix

| kind | unit | topic | files |
|---|---|---|---|
| class | obrig | obrig | obrig |
| assessment | opc | label | exam files |
| review | herda parent | opc | opc |
| makeup | herda parent | obrig | obrig |
| deliverable | obrig | obrig | submission |
| workshop | opc | obrig | opc |
| holiday / suspended / academic_event / office_hours / planning / reserved / results | — | — | — |
| unknown | flag | — | — |

### Keyword map (ordem de prioridade)

Mais específico primeiro. Empate → kind mais restritivo vence.

```python
KIND_KEYWORDS = [
    (BlockKind.HOLIDAY,        ["feriado","carnaval","natal","pascoa","corpus","tiradentes","independencia","finados","consciencia negra","aparecida"]),
    (BlockKind.SUSPENDED,      ["suspensao","suspenso","suspensa","greve","paralisacao","assembleia"]),
    (BlockKind.MAKEUP,         ["substituicao","reposicao"]),
    (BlockKind.ACADEMIC_EVENT, ["evento academico","semana","simposio","congresso","jornada","ciclo de palestras"]),
    (BlockKind.RESULTS,        ["divulgacao","devolucao","devolutiva"]),
    (BlockKind.DELIVERABLE,    ["entrega trabalho","entrega final"]),
    (BlockKind.WORKSHOP,       ["oficina","lancamento","kick-off","kickoff"]),
    (BlockKind.OFFICE_HOURS,   ["atendimento","duvidas","plantao"]),
    (BlockKind.PLANNING,       ["planejamento","reuniao","conselho"]),
    (BlockKind.RESERVED,       ["reserva tecnica","reserva"]),
    (BlockKind.ASSESSMENT,     [r"\bp[1-4]\b","\\bpf\\b","prova","avaliacao","exame","recuperacao","substitutiva","teste"]),
    (BlockKind.REVIEW,         ["revisao"]),
]
```

**Exceção crítica**: bloco com keyword `disciplina`, `apresentacao`, `plano ensino`, `cronograma` → kind=`class` (intro). Bate **antes** do match de assessment, senão pega falso positivo (caso IA bloco-01).

---

## Fases

### Fase 0 — Lock & infraestrutura (já 70% pronto)

- [x] Audit script criado (`scripts/audit_timeline.py`)
- [x] Enum + keywords catalogados (este documento)
- [ ] Commitar audit script + adicionar comando `make audit` ou `python -m scripts.audit_timeline`
- [ ] JSON schema `schemas/timeline_index.v4.json` (campos obrigatórios: id, period_start, period_end, period_label, kind, sessions; opcionais: unit_slug, primary_topic_label, topic_text, topics, aliases, card_evidence, source_rows; bumpar `version: 4`)

### Fase 1 — Módulos novos (sem mexer pipeline)

Criar 3 arquivos isolados, com testes 100% cobertos por fixtures dos 5 cursos auditados:

- `src/builder/timeline/kinds.py` — `BlockKind` enum + `KIND_REQUIREMENTS` + `KIND_DISPLAY` (ícone, cor, label PT-BR).
- `src/builder/timeline/classifier.py` — `classify_block(block) -> BlockKind`. Aplica `KIND_KEYWORDS` em ordem. Consolida lógica de `_timeline_row_is_review_or_assessment` (mover de `index.py:576`).
- `src/builder/timeline/status.py` — `derive_block_status(block) -> Literal["ok","needs_unit","needs_topic","needs_files","non_applicable","needs_review"]`. Read-only, puro.
- `tests/test_timeline_kinds.py` — para cada um dos 92 blocos das fixtures, verifica que `classify_block` retorna o kind esperado catalogado.

**Entrega da fase**: módulos isolados + testes verdes. Pipeline ainda não usa.

### Fase 2 — Integração no index builder (write-side)

- `_finalize_timeline_blocks` em `src/builder/timeline/index.py` chama `classify_block(block)` e injeta `kind` no payload do bloco antes de serializar.
- Bump `version: 4` em `_serialize_timeline_index` (`index.py:1014`).
- Backfill: ao ler v3 sem `kind`, classifier roda lazy e popula.
- Re-roda pipeline nos 5 cursos. Validação: audit script com flag `--use-stored-kind` deve coincidir 100% com classificação inline. Drift = bug.

**Entrega da fase**: todo `.timeline_index.json` tem `kind` preenchido + schema v4 validado.

### Fase 3 — Fix `missing_unit` (root cause, 27 blocos / 29%)

Causa: matcher de unit (`_assign_unit_to_block` ou equivalente — investigar `taxonomy_match_unit` / `content_taxonomy.py`) falha quando `topic_text` rico mas não bate keyword da unit.

Casos reais: `microservicos spring circuit breaker` (ES2 bloco-06), `halting problem` (TCC bloco-10), `logica predicados` (MF bloco-03) — todos têm unit válida no SYLLABUS mas matcher não associa.

**Estratégia**:
1. Investigar score threshold do matcher atual + qual keyword index ele usa.
2. **Hipótese A**: keyword index da unit não contém termos derivados (só literal do título). Fix: expandir keywords com `topic_text` de blocos já casados (bootstrapping intra-curso).
3. **Hipótese B**: threshold alto demais. Fix: baixar threshold + adicionar fallback fuzzy match.
4. **Hipótese C**: matcher exige presença de termo da unit no `topic_text`, mas em alguns blocos o termo está no `date_text` (rótulo da linha) e não no topic. Fix: incluir ambos no input do matcher.

**Critério de aceite**: rodar audit → `missing_unit` cai pra ≤5% por curso (só os legitimamente sem unit, como `office_hours`, `holiday`, etc — mas esses agora são reclassificados via kind, não ficam no bucket `missing_unit`).

### Fase 4 — Fix `missing_topic` (root cause, 22 blocos / 24%)

Causa: taxonomy coverage gap. Bloco tem unit + topic_text rico mas taxonomy do curso não tem entrada que bate.

Exemplos: `dafny`, `isabelle`, `interativa teoremas`, `theorema cook levin`, `devops` — termos legítimos do conteúdo mas ausentes do taxonomy gerado.

**Estratégia em camadas (a primeira que casar vence)**:
1. **Match exato no taxonomy** (atual).
2. **Match por sinônimo/alias** (taxonomy já tem `aliases` em algumas entradas — verificar uso).
3. **Fallback determinístico**: usar `topic_text` normalizado como `primary_topic_label` (capitalize + cortar em 60 chars). Marcar `topic_source = "topic_text_fallback"`.
4. **Manual override**: campo `manual_topic_label` em curation persiste.

Novo campo no bloco: `topic_source ∈ {"taxonomy","alias","topic_text_fallback","manual",""}` — driver de cor/badge na UI ("derivado automaticamente" vs "validado").

**Critério de aceite**: `missing_topic` cai pra 0%. Todo bloco com `topic_text` não vazio gera `primary_topic_label`, mesmo que fallback.

### Fase 5 — UI por kind

- `src/ui/timeline_dashboard.py` linhas 244-276: substituir heurística `has_gap = n_entries == 0` por leitura de `block_status` derivado.
- Lookup table `KIND_DISPLAY[kind]` controla:
  - ícone (📚 class, 📝 assessment, 🏖 holiday, ⏸ suspended, 🔁 makeup, 📅 academic_event, 💬 office_hours, 🛠 workshop, 📤 deliverable, 🗓 planning, ⏳ reserved, 📊 results, ❓ unknown)
  - cor do badge (verde ok, amarelo needs_topic, vermelho needs_unit/needs_files, neutro non_applicable)
  - label PT-BR ("Aula", "Prova", "Feriado", ...)
- Filtros na sidebar: checkboxes por kind. Default: todos visíveis.
- Dropdown de re-classificação manual (override do classifier) salva em curation.

### Fase 6 — Schema validation em CI

- `tests/test_timeline_schema.py`: para cada `.timeline_index.json` em fixtures, valida contra `schemas/timeline_index.v4.json`.
- GitHub Action `validate-timeline.yml`: roda script + audit em PR. Falha se:
  - schema drift
  - `unknown` kind > 5% dos blocos em qualquer curso
  - `needs_unit` ou `needs_files` em bloco `class` > 10%

### Fase 7 — Handshake com `material-agnostic-refactor.md`

Atualizar pré-reqs daquele plano:
- [x] (esta fase) Cada bloco tem `kind` confiável → renderer escolhe template por kind (aulas vs feriado vs prova).
- [x] (esta fase) `auto_tags=bloco:bloco-NN` injetado consistentemente → material attachment funciona.
- [ ] (continua naquele plano) Estender concept-match pra PDFs/imagens/exercícios.

---

## Anti-objetivos

- NÃO persistir `block_status` no JSON. Sempre derivado.
- NÃO ramificar lógica de kind em múltiplos módulos. Tudo em `classifier.py`.
- NÃO quebrar leitura de v3. Backfill lazy.
- NÃO atrasar `code-summarization-gemini.md`. Estes planos são paralelos.
- NÃO criar novo formato de output. `.timeline_index.json` continua sendo o artefato canônico.
- NÃO inferir kind via LLM. Só keywords + regex. Determinístico + barato + auditável.

---

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Falso positivo de classificação (ex: "avaliacao" no syllabus → assessment) | Regra de exceção `disciplina/plano ensino → class`. Auditar com fixtures. |
| `topic_text_fallback` polui badges com rótulos feios | Normalizar (capitalize, truncate, remover stopwords). Badge `topic_source` indica origem. |
| Re-classificação manual perdida em rebuild | Persistir em `curation.json`, não no index. Rebuild preserva. |
| Novo kind aparece num curso futuro | Audit roda em CI. Cobertura `unknown > 5%` quebra build → força adicionar ao enum. |

---

## Métricas de sucesso

- **Pré-refactor**: 21% ok, 53% defeito, 28% non_academic genérico.
- **Pós-Fase 4**: ≥90% `ok` em blocos `class`, 0% `missing_topic`, ≤5% `missing_unit`, 100% blocos têm `kind`.
- **Pós-Fase 6**: schema validado em CI, audit em CI, zero drift entre runs.

---

## Trigger pra iniciar

Imediato — é pré-req crítico de qualquer trabalho futuro em timeline/cronograma. Sem isso, `material-agnostic-refactor.md` produz output cheio de blocos quebrados.

Ordem recomendada de execução:
1. Fase 0 + 1 + 2 (fundação) — 1-2 sessões.
2. Validar com `make audit` + UI antes de Fase 3/4.
3. Fase 3 + 4 (root-cause fixes) — 1-2 sessões.
4. Fase 5 (UI) — 1 sessão.
5. Fase 6 (CI) — meia sessão.
6. Desbloquear `material-agnostic-refactor.md`.
