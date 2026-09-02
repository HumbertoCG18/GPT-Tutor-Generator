# Handoff — fechamento da campanha do motor (sessão de 2 dias)

Sessão `7e940f5e-6bcb-4d2e-b179-e805be4ef933` — **18/08 18:09 → 20/08 15:14 (-0300)**.
63 prompts do user, 587 tool calls, 8,1 MB de transcript, 1 compactação de contexto no meio.

**Este documento SUBSTITUI** `2026-08-19-handoff-cardinalidade-do-motor.md` como estado corrente.
O de 19/08 continua válido para as seções A–H (tese, os 4 consumidores, as 5 previsões refutadas,
notas operacionais); o que ele diz na **I-7** está VENCIDO — a DECISION de granularidade foi
resolvida e as duplicatas foram removidas. Tracker vivo: `pendencias.md`.

---

## Boot da nova sessão

1. Ler este arquivo inteiro.
2. Ler `pendencias.md` — topo e as seções `CODE` das linhas ~1002–1110 (N:N, determinismo, card).
3. `git status` — **nada foi commitado**. HEAD ainda é `419aaff` (18/08). Duas sessões inteiras
   (19 e 20/08) vivem só como working tree, no gerador E nos 5 repos-tutor.
4. NÃO reprocessar produção antes de ler a seção "Estado" abaixo — ela já está reprocessada e
   idempotente; um reprocess a mais não muda nada, mas um reprocess com código diferente muda.

---

## A restrição-mestra da sessão

Prompt #5 virou lei para os dois dias:

> *"lembre-se de sempre ter informações com dados reais, nunca chutar ou começar algo sem
> verificar o estado, resultado, dados e etc"*

Consequência prática: **toda hipótese virou medição antes de virar código**. Cinco predições
minhas foram refutadas pela própria medição (seção E do handoff de 19/08). A causa comum das
cinco: remontar o caminho de atribuição a mão em vez de usar os montadores canônicos. Foi isso
que motivou o `scripts/explain_entry.py` no fim da sessão.

---

## O arco, em 7 fases

### 1. Poda dos achados do enxame (#1–#9)

`known_tools`: estruturalmente errado, **dano medido = ZERO** — taxonomia byte-idêntica com o
filtro ligado/desligado nos 5 cursos, 0 flips em bloco, 0 delta em 4 braços de unidade. Desceu
para higiene. A pergunta do user (*"mas essa mistura não é prejudicial para o motor?"*) foi o que
forçou medir em vez de deduzir.

### 2. Régua nova + calibração do gate (#11–#23)

- `scripts/eval_entry_unit.py` **criado** — a régua `entry→unidade` que o handoff anterior
  registrava como inexistente. Verdade = composição de dois golds já aprovados
  (`ground_truth_<C>.csv` |><| `gold_units_<C>.csv`), sem rotular nada novo.
- **Primeiro sweep de threshold da história do projeto**, medido ponta-a-ponta:
  `T.UNIT_TAG` 0.65 → **0.50**.
- **Corte do eco**: `auto_tags` era entrada *e* saída do scorer. Cortado em `entry_signals.py`
  (`_PREFIXOS_ESPELHO_DO_MOTOR`) e `tag_profile.py` (`_PREFIXOS_ESPELHO`).
  Resultado: reprocess virou **ponto fixo** — 0 entries mudam entre duas rodadas idênticas; antes
  deslocava 2. **Pré-requisito de qualquer medição futura.**
- Normalização de score por tamanho de unidade: **REJEITADA pela medição**.

### 3. Handoff + rotulagem manual (#24–#38)

O user abriu o Moodle das cadeiras antigas e rotulou. **64 casos, 0 pendentes.**
**Três rulings dele cobriram 41 deles** e viraram comportamento em `src/builder/routing/coverage_rules.py`:

| regra | ruling do user | comportamento |
|---|---|---|
| **A** | cronograma cobre a matéria toda | todas as unidades para `cronograma`; ou quando o texto cita ≥80% dos títulos de unidade (`_FRACAO_META = 0.8`) |
| **B** | *"Lista PX = cobre as unidades da prova em questão"* | tópicos da taxonomia citados no enunciado, para `listas`/`gabaritos`/`provas` |
| **C** | card fica com a unidade de evidência máxima | `melhor = max(...)` — **esse desempate sozinho levou ES2 de 1/19 → 19/19** |

Regras são **comportamento, não rótulo**: um curso novo herda as três sem rotulagem manual.

> **A DESCOBERTA DA SESSÃO:** o **ES2 nunca esteve quebrado**. 8/27 contra a régua temporal virou
> **17/18** contra os rótulos de cobertura. A régua é que cobrava a resposta errada. O balde EIXO
> sumiu quando os rótulos chegaram — a cardinalidade N deixou de ser pré-requisito e virou
> melhoria de modelo.

### 4. Limpeza do manifest (#51–#56)

6 duplicatas exatas de conteúdo removidas (**233 → 227 entries**). Ruling do user virou guarda
não-negociável em `scripts/dedup_manifest.py` (modo `--by-content`):

> *"gabaritos são importantes e não são duplicatas... existem vezes que o professor passa a lista
> de exercícios, e o gabarito da lista de exercícios"*

O modo nunca remove automaticamente através de categorias (lista vs gabarito) e faz merge de
campos (`posting_date`, `moodle_label`, `source_section`, `notes`).

### 5. Eixo de bloco (#57–#60)

**Correção de medição minha:** eu vinha dizendo **57%** havia muitas mensagens — é **86%**. Eu
media `computed_block_id` cru em vez de `resolve_temporal_block`. Qualquer número de bloco
anterior a esta sessão deve ser relido com essa ressalva.

Diagnóstico: erros concentram em **AVALIAÇÃO (26%)** e **META (43%)** contra CONTEÚDO (9%);
`concept` é o termo decisor em **21 dos 25 erros**.

Duas propostas **rejeitadas pela medição**:
- `posting_date` — 41% de precisão, é upload em lote. O user matou a proposta lembrando dos
  professores que reusam material (*"como CG, onde todo o material já está upado pois o mesmo é antigo"*).
- janela de `assign_due` — só 4 de 37 cards têm o dado.

Ficou de pé: **data no nome do arquivo como fallback** (tier novo, commitado em `9b6ab28`).

### 6. `coverage_units` chegou nos consumidores (#61)

O campo N:N era **escrito e nunca lido** — 1 ocorrência em `src/`, e era a escrita
(`core/reference_summary.py:135`). Terceira instância da classe *"código certo, dano zero, porque
ninguém chega lá"* (as outras: `known_tools`, `TOOL_TOKENS`).

- `core/reference_navigation.py` ganhou `_ancoras(rec)`: devolve `[(unit_slug, topics)]` a partir
  de `coverage_units`, com fallback para o espelho `computed_ref_unit` (curation antiga segue
  funcionando). Emite a ref sob **cada** âncora, e não pula mais ref sem o espelho.
- `artifacts/repo.py` exibe todas as âncoras em `Relevante para:` separadas por `·`.
- Material também virou N:N no COURSE_MAP: `build_unit_topic_reference_index` devolve
  `material_by_unit` (mesmo encanamento `_reference_nav_index`, nenhum cano novo). Seção por
  unidade emite `🧪 Também cobre esta unidade: ...`, **só com as unidades EXTRAS**.
- **Medido:** MF sai de 2 → 4 âncoras (`eth2` e `archive-of-formal-proofs` passam a aparecer sob
  `metodos-formais` E `verificacao-de-programas`); IA e SO não mudam.
  Distribuição N nos 5 cursos: 213 entries com `coverage_units`, N = {1:190, 2:15, 3:3, 4:2, 7:3};
  23 multi-unidade, todas as 23 com ao menos uma unidade extra.
- `cronograma` fica FORA da renderização (`META_CATEGORIES`) — sozinho gerava 16 das 49 linhas.
  O manifest mantém a cobertura completa; só a linha do COURSE_MAP sai.

### 7. Determinismo + a pergunta do card (20/08, pós-compactação)

**Não-determinismo no score de bloco — RESOLVIDO.**
Raiz: `sum(min(...) for tok in entry_vec.keys() & block_vec.keys())`. `keys() & keys()` devolve
**set**, e a ordem de iteração de set de `str` muda a cada processo (hash randomization). Somar
float em ordem diferente muda o resultado no último ULP.
Consequências medidas no TCC: 6 entries divergiam entre rodadas; a `band` flipava na fronteira
baixa/média; e em empate técnico o **bloco VENCEDOR trocava** (`aula-06`, confiança 0.0841,
alternava entre dois blocos conforme o `PYTHONHASHSEED`).

- Fix: a soma virou `concept_resolver.overlap_min()` — função nomeada, `sorted()` na interseção.
- Mesmo defeito corrigido em `routing/motor/disambiguator.py:_score` (`mat & set(sig)`).
- Rede: `tests/test_determinismo_do_score.py` roda o mesmo cálculo em 4 subprocessos com
  `PYTHONHASHSEED` diferentes e exige saída idêntica; um segundo teste impede que a entrada vire
  invariante à ordem (teste vacuoso não pega o bug de volta).
  **Verificado que o teste FALHA sem o fix** — 3 somas distintas nos 4 seeds.
- **Impacto na acurácia: ZERO** (bloco segue 86%; A/B na régua de unidade dá 103/188 nos dois
  casos). O empate era 50/50 mesmo — o valor é o reprocess ser idempotente, não o motor melhorar.
- Sentinela `tests/_golden/TCC-Tutor__casos_chave.json` regravada de propósito (coin-flip virou
  valor fixo).

**`scripts/explain_entry.py` criado** (read-only). Explica UM arquivo etapa a etapa pelo
**caminho de produção**: sinais → bloco (breakdown dos 6 termos da fusão) → `resolve_temporal_block`
→ texto da rota de unidade → unidade 1:1 + gate + `reconcile_unit_with_block` → cobertura N:N com
a regra que disparou → subunidade restrita à unidade reconciliada.
Achado **já na primeira entry** (TCC `aula-06`): os três eixos discordam entre si — bloco
concept-fused → u02, `resolve_temporal_block` sobrepõe para bloco-05, scorer de unidade → u04,
cobertura regra `card` → u03. **`reconcile_unit_with_block` NÃO corrige**: mantém u04 e só
registra o conflito.

**Último prompt da sessão:** *"Porque o termo card está morto?"*
Resposta: **parser sem produtor**. Cadeia de 4 elos, quebra no terceiro.

```
concept_resolver.py:392   card_term = score_card_evidence_against_entry(signals, block["card_evidence"])
file_map.py:796           if not card_items: return 0.0        <- sempre entra aqui
timeline/index.py:2040    "card_evidence": _extract_block_card_evidence(rows)
vision/card_evidence.py   regex casa SÓ `Card: <titulo>` e `Topico: <titulo>`
```

O cronograma real é tabela markdown do SARC. Medido nos 15 textos dos 5 cursos: `Card:` = 0,
`Tópico:` = 0. **Nada no código produz esse formato** — grep por `"Card:"` em `src/` dá 2 hits,
um comentário e a própria docstring do extrator. O módulo mora em `src/builder/vision/`, escrito
para um caminho de OCR que nunca chegou.

A ironia é a assimetria: a mesma informação está viva no outro eixo. `source_section`
("Semana 4 - Teoria de Autômatos") está em **222/227 materiais** e pontua na unidade
(`file_map.py:308`). No bloco o motor compara contra `card_evidence`, não contra `card_text`.

Passou despercebido porque falha em silêncio (`return 0.0`, não erro) — todo bloco recebe 0,
então não há distorção de ranking, só a fusão virar mono-termo (`concept` é o maior em 185/227).

---

## Estado verificado (as-of 2026-08-20)

| eixo | início da sessão | fim |
|---|---|---|
| unidade 1:1 | 127/191 = 66% | **166/188 = 88%** |
| cobertura N:N | régua não existia | **44/57 = 77% exato, F1 0,81** |
| bloco | 172/200 = 86% (eu media 57%) | **86%** |
| entries | 233 | **227** |
| suíte | 1898 | **1904 passed / 1 skipped / 0 falhas** |
| idempotência do reprocess | deslocava 2 | **ponto fixo (0)** |

Produção: 5 repos-tutor reprocessados e idempotentes, 33 arquivos alterados, **nada commitado**.
Gerador: 34 arquivos (18 modificados, 16 novos), **nada commitado**.
Rotulagem: **completa** — 64 casos, 0 pendentes.

---

## Erros meus nesta sessão (para não repetir)

- **Heredoc do Bash corrompeu conteúdo com `` ` `` e `\n` — duas vezes**, e a lição já estava
  escrita no handoff anterior. Para markdown/LaTeX/commit: usar Write.
- **Regenerar `material_gt_*.csv` destruiu todos os rulings do user.** Preservação de rótulos
  existentes virou requisito de `make_material_coverage_labels.py`.
- **Apaguei linhas com `id` vazio dos ground_truth** — são registros `scorable=no` legítimos, com
  proveniência. Restaurado via `git checkout`; a limpeza foi refeita tocando só linhas com id
  não-vazio ausente do manifest.
- **Introduzi BOM nos ground_truth CSVs** → `eval_ground_truth.py` reportava `Acuracia: 0/0`
  **em silêncio** para MF, SO e IA. Corrigido dos dois lados (leitor `utf-8-sig`, CSVs sem BOM).
- **Bloco a 57% por muitas mensagens** — campo errado.
- Contador de ubiquidade contava ocorrências, não unidades → falsos positivos.
- f-string com backslash → SyntaxError que **pulou um fix em silêncio**.

---

## Fila aberta

1. **[commitar]** — 34 arquivos no gerador + 33 nos repos-tutor, suíte verde. Nada commitado desde
   `419aaff`. É a primeira coisa a decidir na próxima sessão.
2. **K-1 · termo `card` morto** — `card_evidence` vazio em 120/120 blocos. **K-2 já refutou o
   conserto óbvio**: `source_section` como pontuador autoritativo tem teto de **144/199 = 72%**,
   abaixo dos 86% atuais (seção é mais grossa que bloco — MF tem 9 seções para 23 blocos). Se for
   revivido, entra como **filtro de intervalo**, nunca como pontuador.
3. **I-4 · SO tem 3 referências com ZERO âncora** — nem `coverage_units` nem `computed_ref_unit`.
   Somem do COURSE_MAP. Não é regressão (antes também sumiam), mas agora está medido.
4. **Os dois consumidores de `subunit:`** — `artifacts/navigation.py:35` e `ui/dialogs.py:4193`
   ainda leem a 1ª tag. É o que a subunidade-como-tags exigiria.
5. **Os 28 erros de bloco** — 26% em avaliação, 43% em meta. Sem hipótese barata: o sinal que
   resolveria (quando a avaliação foi aplicada) o Moodle não dá.
6. **`reconcile_unit_with_block` não reconcilia** — registra o conflito e mantém a unidade do
   scorer. Achado novo do `explain_entry.py`, ainda não investigado.
7. Cachear texto de bibliografia web (4 casos) · resumo mais rico para zip de código (6 casos) ·
   padrão "título de unidade vence tópico" · `EXAM_INDEX.md` existe em 1 de 5 cursos.

---

## Notas operacionais (herdadas, ainda valem)

- Reverter produção é `git checkout -- .` nos 5 repos — nada é commitado pelo reprocess, e
  `manifest.json.bak` fica ao lado.
- `.claude/worktrees/` deixa `grep -r` lento (>2 min). Usar a ferramenta Grep.
- Hook `code-review-graph` segue crashando com `UnicodeEncodeError` cp1252 — conhecido,
  não-bloqueante.
- Transcript completo desta sessão:
  `C:\Users\Humberto\.claude\projects\C--Users-Humberto-Documents-GitHub-GPT-Tutor-Generator\7e940f5e-6bcb-4d2e-b179-e805be4ef933.jsonl`
