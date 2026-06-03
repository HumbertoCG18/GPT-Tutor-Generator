# Melhorar atribuição de arquivos a blocos do cronograma — Design

date: 2026-06-03
status: aprovado (aguardando review do spec)

## Problema

A atribuição material→bloco temporal hoje deixa órfãos e faz matches frágeis, e
o modelo de dados acumulou campos ambíguos/não-declarados durante o trabalho de
block-match. Baseline real: 88% de cobertura (14/16 materiais), 2 órfãos, 12
blocos vazios.

Causas concretas (mapeadas no código atual):

1. **Match de bloco fica atrás do match de unidade.** Em
   `resolve_unit_block_tags` (`src/builder/extraction/content_taxonomy.py`) o
   bloco só é tentado se `unit_confidence >= 0.55`. Material com unidade
   ambígua/fraca vira órfão garantido mesmo com título/data óbvios. **Maior
   fonte estrutural de órfãos.**
2. **Datas frágeis.** O boost de data (`src/builder/routing/file_map.py`) só
   dispara quando `raw_text` *começa* com `DD.MM`. Perde ISO, `DD/MM/YYYY`,
   data no meio do texto ou no título.
3. **Sem visibilidade de confiança.** `cronograma_health` mede só dois sinais
   grossos: órfãos e blocos vazios. Não há confiança por-atribuição, flag de
   baixa-confiança, nem detecção de atribuição duvidosa.
4. **Drift do modelo de dados.** Cinco campos são gravados no `manifest.json`
   mas não existem no `FileEntry` (`manual_subunit_slug`,
   `unit_match_confidence`, `unit_match_reasons`, `subunit_match_confidence`,
   `subunit_match_reasons`) — sobrevivem só porque build/UI usam dict cru;
   `FileEntry.from_dict` filtra chave desconhecida, então qualquer round-trip
   (ex.: save da fila em `app.py`) **perde silenciosamente** esses campos.
5. **Ponteiro de bloco em 3 formas** que podem divergir:
   `manual_timeline_block_id`, `auto_tags["bloco:<id>"]`, e o fallback ordinal
   `bloco-N`. Leitores divergem na precedência.
6. **Colisões de nome:** `manual_unit_slug` existe em escopo *entry* e em escopo
   *block* (curation); `unit_match_confidence` (persistido) coexiste com
   `_unit_match_confidence` (transiente em `navigation.py`).
7. **Sem `unit_slug`/`block_id` first-class no entry:** o slug resolvido vive
   só dentro da string da tag `unit:`; tudo faz parse de tag.

## Objetivo

Melhorar recall (menos órfãos) **e** precisão (menos atribuição errada
silenciosa), e de quebra limpar a confusão dos overrides manuais. Sem regressão
do fluxo manual. Determinístico primeiro; Gemini residual continua opt-in em
background (não faz parte desta entrega).

## Decisões (do brainstorm)

- **Dor:** itens 1 (recall) + 2 (precisão) principalmente, e 3 (limpar a
  confusão dos overrides).
- **Determinístico primeiro, Gemini opcional.** Resolver o estrutural sem rede.
  O `run_material_residual` (Gemini) permanece gated atrás de
  `enable_material_residual`, intocado.
- **Match fraco/ambíguo → atribui + flag baixa-confiança.** Sempre dá o melhor
  palpite (zero órfão quando há blocos), marca a faixa pra revisão. Erro
  silencioso some porque fica visível.
- **Overrides:** reconciliar no código **e** mostrar manual-vs-auto no
  health/UI (sem diálogo novo).
- **Abordagem A** (desacoplar bloco da unidade + faixas de confiança). A
  abordagem C (reescrita do scoring como ensemble ponderado) fica anotada como
  follow-up, fora desta entrega.

## Arquitetura — fases

A entrega é incremental. A Fase 0 (higiene do modelo) precede qualquer lógica
nova, porque adicionar `computed_*` sobre um modelo com drift propagaria a
confusão.

### Fase 0 — Higiene do modelo de dados

1. **Declarar no `FileEntry` (`src/models/core.py`) os 5 campos
   escritos-mas-ausentes**, com defaults seguros, para o round-trip
   `from_dict→to_dict` parar de perdê-los. Prioridade: `manual_subunit_slug`
   (override de subunidade, conf=1.0, hoje some em qualquer round-trip).
2. **Desfazer colisões de nome:**
   - bloco-escopo `manual_unit_slug` → `block_manual_unit_slug`
     (em `src/builder/timeline/index.py` serialização + `curation.py` merge).
   - `navigation.py` passa a ler o `unit_match_confidence` persistido em vez de
     recomputar num `_unit_match_confidence` transiente.
3. **`auto_tags["bloco:"]` vira cache derivado puro.** Nunca recomputado por um
   caminho paralelo; sempre = vencedor da precedência (ver Fase 4).
4. **Verify-then-remove** dos campos de bloco sem leitor encontrado no `src`
   (`unit_confidence`, `primary_topic_confidence`, `topic_ambiguous`,
   `topic_candidates` em `_serialize_timeline_index`). Cada remoção é guardada
   por um teste que prova ausência de leitor; se um teste/tooling externo ler,
   o campo fica.

### Fase 1 — Desacoplar bloco da unidade + fonte única de verdade

1. **Desacoplar.** Bloco passa a ser computado sempre, direto: para cada
   material instrucional, roda `score_entry_against_timeline_block` sobre
   **todos** os blocos instrucionais (não-`administrative_only`), pega o melhor.
   A unidade deixa de ser portão e continua entrando como *boost* (os preference
   adjustments `+0.35 + unit_confidence*0.25` que já existem em `file_map.py`).
   Remove o gate `unit_confidence >= 0.55` e unifica os gates inconsistentes
   (bloco em `0.55` vs tag `unit:` em `0.65`).
2. **Campos first-class no `FileEntry`:** `computed_unit_slug`,
   `computed_block_id`, `computed_block_confidence` (float),
   `computed_block_band` (str: `alta`/`media`/`baixa`). Resolve o "tudo é parse
   de tag".
3. **`auto_tags` espelham os `computed_*`.** `unit:` e `bloco:` são derivados
   dos campos, não calculados em paralelo.

### Fase 2 — Parsing de data robusto

Módulo novo `src/builder/routing/dates.py` com função única
`extract_dates(text) -> list[date]`, reusada por todos os scorers:

- Reconhece `DD.MM`, `DD/MM`, `DD-MM`, `DD.MM.YYYY`, `DD/MM/YYYY`, ISO
  `YYYY-MM-DD`, em **qualquer posição** (título, markdown, raw).
- Ano ausente: assume o ano do curso (lido do `course_meta`/timeline).
- O match de data compara datas extraídas do material contra
  `period_start..period_end` / `date_text` das sessões do bloco: data exata
  dentro do range → boost forte; mês compatível → boost fraco.
- Substitui o regex `DD.MM`-no-início. Mantém o peso exato atual (`+0.30`) como
  base calibrável.
- Determinístico, sem rede.

### Fase 3 — Faixas de confiança e comportamento

- `margin_confidence(winner, runner_up, k)` (já em
  `src/builder/routing/thresholds.py`) gera a confiança por atribuição.
- Três faixas novas em `thresholds.py`: `BAND_HIGH` (gap claro) e `BAND_LOW`
  (piso mínimo). Acima de HIGH = `alta`; entre HIGH e LOW = `media`; abaixo de
  LOW mas com candidato = `baixa`.
- **Comportamento:** sempre atribui o melhor candidato; grava
  `computed_block_band`. `media`/`baixa` ficam flagados pra revisão. Órfão
  **só** se não existe nenhum bloco instrucional (não deve ocorrer em curso
  real).
- `computed_block_confidence` + `computed_block_band` no entry → lidos por
  health e UI sem recálculo.

### Fase 4 — Reconcile de overrides + surfacing

**Reconcile:**

- Precedência única, explícita e documentada num só lugar:
  `manual_timeline_block_id` (entry) > `computed_block_id`.
  `auto_tags["bloco:"]` = espelho do vencedor, nunca contradiz.
- Função única `resolve_effective_block(entry)` (provável lar:
  `src/builder/routing/file_map.py`, ao lado de
  `resolve_entry_manual_timeline_block`). `cronograma_health` e
  `timeline_dashboard` passam a ler **a mesma** função, eliminando os 3
  leitores divergentes.
- Os renomes da Fase 0 já desfazem a colisão `manual_unit_slug`.

**Surfacing:**

- `CRONOGRAMA_HEALTH.md` (`src/builder/artifacts/cronograma_health.py`) ganha:
  distribuição de confiança (contagem alta/média/baixa), lista de
  **baixa-confiança** com os top-N blocos candidatos + score (cada material
  vira tarefa acionável), e marcador **manual vs auto** por atribuição.
- `timeline_dashboard` (UI): badge de faixa por material e ícone manual/auto.
  Sem diálogo novo — só leitura dos `computed_*` da Fase 1.

## Componentes (resumo de arquivos)

- `src/models/core.py` — `FileEntry`: declarar 5 campos faltantes + 4
  `computed_*` novos.
- `src/builder/extraction/content_taxonomy.py` — `resolve_unit_block_tags`:
  desacoplar, gravar `computed_*`, espelhar `auto_tags`.
- `src/builder/routing/file_map.py` — scorers usam `extract_dates`; novo
  `resolve_effective_block(entry)`.
- `src/builder/routing/dates.py` — **novo**, `extract_dates`.
- `src/builder/routing/thresholds.py` — `BAND_HIGH`/`BAND_LOW` + helper de
  faixa.
- `src/builder/timeline/index.py` + `src/builder/timeline/curation.py` —
  renome `block_manual_unit_slug`; verify-then-remove dos 4 campos sem leitor.
- `src/builder/artifacts/cronograma_health.py` — surfacing de faixas +
  candidatos + manual/auto, via `resolve_effective_block`.
- `src/ui/navigation.py` — ler `unit_match_confidence` persistido.
- `src/ui/...timeline_dashboard...` — badges de faixa + manual/auto.

## Fluxo de dados (após o refactor)

```
material (entry)
  → resolve_unit_block_tags:
      manual override? → fixa computed_block_id = manual
      senão → score_entry_against_timeline_block sobre TODOS blocos instrucionais
              (boosts: unidade, tópico, extract_dates) → melhor candidato
      grava computed_block_id / _confidence / _band
      espelha auto_tags[unit:|bloco:]
  → resolve_effective_block(entry) = manual_timeline_block_id or computed_block_id
  → cronograma_health + timeline_dashboard leem a MESMA resolução
```

## Tratamento de erros / bordas

- Curso sem nenhum bloco instrucional → material fica órfão (estado degradado
  legítimo, reportado no health).
- Data sem ano → ano do curso; texto sem data → match cai nos sinais textuais
  (título/markdown/unidade), comportamento atual preservado.
- Override manual apontando para id inexistente → mantém o fallback ordinal
  `bloco-N` já existente; se nada resolver, trata como sem-override e usa
  computed (logado).
- Round-trip de entry com os campos novos → preservado (garantido por teste de
  Fase 0).

## Testes (TDD por fase)

- **Fase 0:** round-trip `FileEntry.from_dict → to_dict` preserva os 5 campos
  antes-perdidos (teste vermelho hoje). Renomes não quebram leitores existentes.
  Cada verify-then-remove tem teste provando ausência de leitor.
- **Fase 2:** `extract_dates` — tabela cobrindo `DD.MM`, `DD/MM`, `DD-MM`,
  `DD.MM.YYYY`, `DD/MM/YYYY`, ISO, data no meio do texto, no título, e ano
  ausente → ano do curso.
- **Fase 1/3:** material com unidade fraca mas data/título óbvios **agora
  recebe bloco** (o caso que hoje vira órfão). Match ambíguo → atribui +
  `band="baixa"`. Manual sempre vence computed. `auto_tags["bloco:"]` espelha o
  efetivo.
- **Fase 4:** health reporta distribuição de faixas + candidatos top-N;
  `resolve_effective_block` é fonte única (health e dashboard concordam num
  fixture com manual e auto divergentes).
- **Regressão:** suíte cheia (`python -m pytest tests/ -q`), ignorando as 4
  falhas baseline conhecidas. Rodar `scripts/validate_materials.py` e
  `scripts/validate_timeline.py`: cobertura não pode cair (alvo: subir de 88%).

## Fora de escopo (YAGNI)

- Reescrita do scoring como ensemble ponderado (abordagem C) — ver follow-up.
- Reativar/fortalecer a camada Gemini residual como peça central.
- Diálogo de UI novo para edição de atribuição (reusa os controles atuais).
- Schema/pydantic formal do `manifest.json` (o dataclass declarado, após Fase 0,
  já remove o drift que motivava isso).

## Follow-up (próxima sessão, separado) — Abordagem C

Reescrita do scoring de atribuição como **ensemble ponderado explícito**:
puxar as constantes mágicas inline de `score_timeline_block` /
`score_entry_against_timeline_block` (os `1.15`, `0.18`, `2.25`, `0.35`,
`0.45`, `0.8`, `0.30`) para `thresholds.py`, com pesos documentados por sinal
(data, título, unidade, tópico, kind, exercício, card) e uma saída única de
confiança. Maior limpeza a longo prazo, maior risco de regressão — merece spec e
plano próprios. Também consolidar o `normalize_match_text` duplicado em 6-7
arquivos.
