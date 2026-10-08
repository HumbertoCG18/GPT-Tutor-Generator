# Ingestão Automatizada: Download + Auto-Mapeamento Seção→Slug — Design (Spec B)

last_updated: 2026-06-19
status: design revisado (revisão adversarial 2026-06-19 aplicada), pendente revisão final do user
escopo: dentro do refactor de atribuição A1-A7; produtor do contrato consumido pela Spec A
revisão: contrato entregue = `dates` (chave de join), não slug; slug vira `topic_slugs`-rótulo
  opcional. Correção factual: módulo M365 (`m365.py`) JÁ existe — B conecta, não constrói. Risco de
  auth M365 rebaixado; fallback drop-manual explícito.

## Problema

A atribuição correta (Spec A — `2026-06-19-cronograma-sessao-atomo-design.md`) depende de dois
sinais: o **slug canônico** de cada material (de qual tópico/unidade ele é) e o **cronograma SARC**
(quando o tópico é dado). Hoje, o lado da fonte é manual e frágil:

1. **Download.** Moodle tem `download_course`; **M365/OneDrive (canal de MF e ES2, prof Julio) JÁ
   tem download automatizado** — `src/builder/sources/m365.py` (`M365Client`, `download_subject_m365`,
   auth device-code read-only, token em `moddle/.m365_token.json`, sem app registration próprio).
   Correção da revisão: este módulo **não** é novo nem incógnita técnica. O gap residual é apenas
   **conectar** o download M365 ao auto-mapeamento. (Os 28% de `source_section` vazio do MF vêm de
   drops manuais legados, não da falta do canal.)
2. **Chave de join frágil hoje.** `.card_block_map.json` é auto-derivado dos labels Moodle
   (`derive_card_block_map`) e já carrega `dates` por card. A Spec A passa a usar **`dates` como
   chave de join** (não slug nem nome-string). O gap é garantir que todo card tenha um intervalo de
   datas confiável — inclusive nos cursos sem label Moodle (MF/ES2), via cross-check com o SARC.
3. **Rótulo de slug por seção (secundário).** A seção (card) pode ganhar um `topic_slugs` de
   display casando nome+datas contra `.content_taxonomy.json`. É **rótulo**, não chave — best-effort,
   com `confirmed` flag. Não bloqueia a atribuição (que roda por data).

## Objetivo

Automatizar a pipeline de **ingestão** que alimenta a Spec A: baixar materiais (Moodle API +
M365 já implementado) para as pastas-seção do professor e garantir que cada card tenha um
**intervalo de datas confiável** (a chave de join da Spec A) no `.card_block_map.json` —
auto-derivado de labels Moodle quando existem, ou por **cross-check com o SARC** quando não.
Opcionalmente derivar um `topic_slugs` de **display** por seção (best-effort). **Atribuição
automática**: tudo com sinal de data é colocado sem confirmação; revisão pelo `rebuild_diff`/
eval-gate (1/curso); fila de exceção só pro que não tem sinal. Congela correções manuais.

Reusa artefatos existentes; **não cria arquivos novos**. O resultado é um stash bem-mapeado +
`.card_block_map.json` com `dates` confiáveis (+ slug-rótulo opcional) — o contrato que a Spec A
consome por data.

## Decisões travadas (brainstorming 2026-06-19)

- **Manter as seções do professor** (Moodle/M365) como cards. Sem reorganização física do stash,
  sem esqueleto de pastas-tópico, sem sidecar no stash.
- **Gabarito repo-side:** `.card_block_map.json`. A chave de join é `dates` (já existe). Evoluir
  `derive_card_block_map` / `merge_card_block_map` para (a) garantir `dates` confiáveis por card
  (cross-check SARC quando faltam labels) e (b) opcionalmente sugerir `topic_slugs` de **display**
  (`.content_taxonomy.json`) por seção. O slug é rótulo, não chave.
- **Auto-atribui tudo que tem sinal + revisa o diff agregado + congela** (`source`:
  "sarc"|"labels"|"manual"; `confirmed`: bool). **Sem confirmação card-por-card** — revisão via
  `rebuild_diff`/eval-gate (1 por curso). Fila de exceção só pro que não tem sinal nenhum.
- **Seção grossa** (ex.: "Verificação de Programas" = Hoare+Dafny+Modelos) → intervalo de datas
  largo → material cai em todas as sessões do intervalo (grão-unidade — política já aceita na
  Spec A). Grão fino = rachar a seção em subpastas mais finas (cada uma com seu intervalo de datas),
  NÃO desempate por nome de arquivo.
- **LLM nunca é autoridade de runtime** (sugestor congelado, se usado).

## Fronteira com a Spec A

B é o **produtor**; A é o **consumidor**. Contrato compartilhado:
- `.card_block_map.json` — card→`dates` (conjunto discreto de datas de sessão; chave de join por
  membership; B garante a completude, A lê) + `topic_slugs` rótulo opcional. Fallback `span_fallback`
  logado quando B não enumera.
- Sessões SARC (datas) no `.timeline_index.json` (parse SARC já existente).

B **não** mexe em atribuição nem render (isso é a Spec A). O trabalho da B termina num stash
mapeado + `.card_block_map.json` confirmado.

## Arquitetura

### 1. Download — dois canais

- **Moodle API** (`src/builder/sources/moodle.py:download_course`, já existe): reusar. Baixa para
  `<stash>/<section>/<savename>`; `skip_existing` por path exato (idempotente). Valida magic bytes.
- **M365 (JÁ IMPLEMENTADO — `src/builder/sources/m365.py`):** `M365Client` +
  `download_subject_m365` já espelham o contrato (`{total, downloaded, failed}`, `skip_existing` por
  path, validação de magic bytes). Auth **device-code read-only** (client público "Microsoft Graph
  Command Line Tools", **sem app registration próprio**); token cacheado em `moddle/.m365_token.json`
  com refresh automático (`load_cached_token`). **Não construir do zero** — o trabalho da B é
  **conectar** este download ao auto-mapeamento (passo 2) e ao re-sync por curso.

### 2. Auto-derivação (evoluir `derive_card_block_map`)

- **Hoje:** `derive_card_block_map` (`moodle_labels.py:152-178`) intersecta as **datas** dos labels
  do card contra os **blocos** e emite `block_ids` (+ `dates`, `source:"labels"`). É inferência
  **temporal**, e o output já contém o intervalo de datas. NÃO toca `.content_taxonomy.json`.
- **Evolução — duas saídas, prioridades distintas:**
  1. **`dates` confiável por card (chave de join — prioritário).** É um **conjunto discreto** das
     datas das sessões SARC daquele card (a Spec A casa por membership `session.date ∈ dates`, não
     por intervalo). Onde há labels Moodle, as datas saem do label; onde não há (MF/ES2 via M365),
     **cross-check com o SARC enumera as sessões do tópico** (casar a seção por nome + âncora
     temporal) → as datas exatas. Marca `source:"sarc"`. **Fallback:** se o cross-check não
     enumerar as sessões, emite `dates:[min,max]` com `span_fallback:true` e `confirmed:false`
     (logado) — a UI sinaliza para placement manual.
  2. **`topic_slugs` de display (rótulo — best-effort).** Casar nome da seção contra `topic`/`unit`
     label+aliases do `.content_taxonomy.json`. Ambíguo → `confirmed:false`. **Nunca bloqueia a
     atribuição** (que roda por `dates`).
- **Precisão por arquivo (automático, mata o manual do card grosso) — `moodle_label` do arquivo:**
  cada arquivo já carrega seu próprio `moodle_label` no manifest (dado real: `LogicaDeHoare2.pdf` →
  "Lógica de Hoare (parte 2)"; `FormalizacaoAlgoritmos_Recursao2.pdf` → "Especificações recursivas -
  listas"). Resolução de datas em **dois níveis**:
  1. **Nível-arquivo (preferido):** se o `moodle_label` do arquivo casa um tópico do
     `.content_taxonomy.json` (match de alias, **determinístico** — é metadado que o professor
     escreveu, NÃO o filename nem inferência de conteúdo) → o arquivo herda as **datas das sessões
     SARC daquele tópico**. Ex.: `LogicaDeHoare2.pdf` → `logica-de-hoare` → `[27/04, 29/04]`, mesmo
     estando num card grosso. **Precisão grão-sessão, sem manual.**
  2. **Nível-card (fallback):** label genérico (ex.: "Introdução") ou sem match → herda `card.dates`
     (grão-unidade). Sempre coloca algo.
  Isto resolve o card grosso "Verificação de Programas" automaticamente: os arquivos com label de
  tópico (Hoare, Dafny) caem nas datas certas; só os genéricos repetem na unidade. **Zero subpasta
  manual.** Não é o scorer difuso (que lê conteúdo) — é match de label autorado pelo professor.
- Output no `.card_block_map.json` (a chave de join é `dates`):
  ```json
  {
    "Verificação de Programas": {
      "dates": ["2026-04-27","2026-04-29","2026-05-04","2026-05-06","2026-05-11","2026-05-13",
                "2026-05-18","2026-05-20","2026-05-25","2026-05-27","2026-06-01","2026-06-03",
                "2026-06-08","2026-06-10"],
      "block_ids": ["bloco-10","bloco-11","bloco-12","bloco-13","bloco-14","bloco-15"],
      "unit_slug": "unidade-02-verificacao-de-programas",
      "topic_slugs": ["logica-de-hoare", "softwares-de-suporte-a-verificacao-formal-de-programas"],
      "source": "labels",
      "confirmed": false
    }
  }
  ```
  > Dado REAL do MF (verbatim do `.card_block_map.json`): este card é **unidade-02 inteira**
  > (Hoare → Dafny), `source:"labels"` com 14 datas já enumeradas. Modelos (bloco-16) **não** está
  > neste card. Exemplo anterior (hoare/dafny/modelos) estava errado — corrigido.

- **Confiança:** datas casam por label → forte; datas por cross-check SARC sem label → média,
  `confirmed:false` (não congelar mapa derivado de bloco possivelmente over-merged). Slug-rótulo
  forte (nome ≈ tópico) pode `confirmed:true`.
- **Retro-compat:** `block_ids`/`dates` preservados — são a chave de join, não descartados. A Spec A
  consome `dates`; `topic_slugs` é aditivo.

### 3. Atribuição automática + revisão por diff (não confirmação por-card)

Decisão de automação (2026-06-19): **auto-atribui TUDO que tem sinal de data; o humano revisa o
diff agregado, não confirma card por card.** Habilitado pelo join-por-data: como o slug virou
display, slug errado é cosmético — não precisa confirmar slug pra colocar certo. O que importa
(`dates`) é objetivo (uma data está ou não no SARC), então é seguro automatizar.

- **Auto-assign:** todo card/arquivo com sinal (label de data, label de tópico, ou cross-check SARC)
  é atribuído automaticamente, `confirmed:false`. Nada bloqueia.
- **Superfície de revisão = `rebuild_diff` + eval-gate/gold (JÁ EXISTEM no A1-A7).** Você revisa o
  que **mudou** por curso (o diff) e o eval contra o gold — não 6 cards. Regressão aparece no diff/
  eval. Isto escala: 1 revisão de diff por curso, não N confirmações.
- **Fila de exceção (mínima):** só entra na fila o que **não tem sinal nenhum** (sem label de data,
  sem label de tópico, sem match SARC — ex.: legado solto, nome genérico). Não adivinha: sinaliza.
  Meta: fila pequena, encolhendo a cada melhoria de sinal.
- **Congelamento:** `merge_card_block_map` preserva `source:"manual"`/`confirmed:true` sobre auto
  re-derivado — **reusar**. Correção manual continua possível, mas é exceção, não rotina.
- **Manual override deixa de ser caminho primário.** O órfão real `21-logica-de-hoare` (+
  `unidade-01` errado em arquivo de Hoare) nasceu de override manual sem validação. Com auto-by-date
  confiável + guarda dura de slug, overrides caem a quase zero.

### 4. SARC como insumo (sem novo artefato)

SARC já é parseado (HTML → markdown → `SYLLABUS.md` → `.timeline_index.json`). B reusa esse parse
como o sinal de cross-check do passo 2 (qual seção casa qual range de datas). **Não persiste
`_CRONOGRAMA.json` novo.**

### 5. Classificação na ingestão: material datado vs bibliografia vs fila

Todo item importado cai em **uma de três trilhas** (determinístico, na ingestão):

1. **Material datado → cronograma.** Tem sinal de data (label de data, label de tópico que casa
   SARC, ou cross-check de card). Vai pro dia-a-dia via `dates` (seção 2-3). É a maioria.
2. **Bibliografia / material de apoio → seção de referências (NÃO o dia-a-dia).** Itens sem data por
   natureza: links/URLs e repos (`file_type` ∈ {`url`, `github-repo`}) e `category` ∈
   {`bibliografia`, `references`}. Dado real do MF: `eth2.0-dafny`, `aws-encryption-sdk`,
   `Archive of Formal Proofs`. **Não vão pra fila de exceção** — são referências, não material de
   aula sem lugar. Renderizam num bloco de referências separado (Spec A).
3. **Fila de exceção (mínima):** só material que **deveria** ter data (PDF/zip de aula) mas não tem
   sinal nenhum. Com a resolução por `moodle_label` (seção 2), isto encolhe a quase nada — no MF,
   os 14 itens de `source_section` vazio que **têm** label se auto-colocam; sobram só os 3 de
   bibliografia (trilha 2, não fila). **Fila MF ≈ 0.**

> Insight dos dados reais: o "espalhamento" (28% `source_section` vazio) NÃO é problema de
> atribuição — é classificação. 14/17 têm `moodle_label` → trilha 1 (auto-colocados por data);
> 3/17 são links → trilha 2 (referências). Nenhum precisa de fila.

## Fluxo de dados

```
download (Moodle API / M365 já existe)
   → <stash>/<seção>/<arquivos>
derive card→dates (labels Moodle; cross-check SARC quando faltam) [+ topic_slugs-rótulo opcional]
   → .card_block_map.json (com confirmed flags)
[você confirma os incertos na UI]  → merge_card_block_map (manual congela)
   → .card_block_map.json confirmado
        → Spec A consome (join arquivo→card→dates ∩ session.date → sessões)
```

## Reuso / o que é novo

- **Reusa:** `download_course`, **`m365.py` (`M365Client`/`download_subject_m365`, já implementado)**,
  `derive_card_block_map`/`merge_card_block_map`, `.card_block_map.json`, `.content_taxonomy.json`,
  parse SARC, `_ARQUIVOS_DO_CARD.txt` (guia).
- **Novo (pequeno):** (a) conectar o download M365 existente ao re-sync/auto-map; (b) cross-check
  SARC para `dates` em cards sem label; (c) derivação opcional de `topic_slugs`-rótulo; (d) painel
  de confirmação (rótulo, não chave). **NÃO** é novo: o módulo de download M365 (já existe).
- **NÃO cria:** sidecar no stash, `_CRONOGRAMA.json`, pastas-esqueleto.

## Invariantes (não-negociáveis)

- **Chave de join entregue = `dates`** (não slug). `topic_slugs` é rótulo aditivo opcional.
- SARC / OpenSARC **read-only** (nunca escrito). M365 **read-only** (device-code, escopo de leitura).
- Token Moodle em `moddle/.env` (`MOODLE_URL`/`MOODLE_TOKEN`); token M365 em `moddle/.m365_token.json`
  (já gerenciado por `m365.py`). Não logar nem commitar segredos.
- Download **idempotente** (skip por path exato); só baixa o que falta.
- **Não auto-commitar** os repos gerados durante re-sync — revisar `rebuild_diff` por repo.
- LLM nunca é autoridade de runtime (sugestor congelado, se usado).
- **Não criar arquivos/campos novos paralelos** — reusar `.card_block_map.json`.
- `topic_slugs` emitido sempre ∈ `.content_taxonomy.json` (guarda dura, mesma da Spec A).
- Gabarito repo-side; stash mantém as seções do professor.

## Testes

- **Download M365 (já existe):** testar a **conexão** ao re-sync/auto-map (não reimplementar o
  cliente). Mock; `skip_existing` por path; idempotência (re-rodar não re-baixa).
- **derive card→`dates`:** fixtures —
  - card com label Moodle → `dates` do label (conjunto discreto), `source:"labels"`.
  - card sem label, nome casa o tópico SARC → cross-check **enumera as datas das sessões** (discreto),
    `source:"sarc"`, `confirmed:false`.
  - card sem label, cross-check não enumera → `dates:[min,max]` + `span_fallback:true`, `confirmed:false`.
  - card sem label e sem match SARC → sem `dates` (vai pra fila / drop manual).
- **derive `topic_slugs`-rótulo:** nome ≈ tópico → slug; ambíguo → `confirmed:false`; slug emitido
  sempre ∈ `.content_taxonomy.json` (guarda dura falha senão).
- **merge:** entrada `source:"manual"`/`confirmed:true` preservada sobre auto re-derivado.
- **Retro-compat:** `.card_block_map.json` antigo (`block_ids`/`dates`) lê sob schema com `topic_slugs`
  aditivo; atribuição continua por `dates`.

## Riscos / decisões em aberto

1. ~~Auth M365 como maior incógnita~~ **REBAIXADO:** o módulo M365 já existe e roda (device-code
   read-only, sem app registration, refresh automático). Risco residual = prof revogar o
   compartilhamento → cai no **fallback drop-manual** (pasta-seção no stash; as datas vêm do SARC
   por cross-check, não do canal de download). O stash é a fronteira, não o canal.
2. **Rename de pasta no download** (fix de data-padding S0b): seção renomeada re-baixa em pasta
   nova → duplicata em disco. Tratar: normalizar/detectar rename de seção (liga ao S0b já feito).
3. **Seção multi-unidade** → intervalo de datas largo → grão-unidade (aceito). Grão fino = rachar
   em subpastas com intervalos próprios; **não** desempate por nome de arquivo (reintroduziria
   difuso).
4. **Normalização de slug** (não "autoridade"): `unit_index` e `content_taxonomy` partilham origem
   (`parse_units_from_teaching_plan` + `normalize_unit_slug`). Como a chave de join virou a data, a
   coerência de slug deixou de bloquear a atribuição — vira robustez do rótulo. Pré-req leve:
   normalizar consistente + guarda dura.
5. **Arquivos legados sem seção** (os 17 vazio do MF): o pipeline novo não os gera (todo download
   nasce numa seção), mas o legado precisa de placement manual uma vez.

## Ordem de execução (relativa à Spec A)

Faseamento revisado (a inversão v5 deixou de ser pré-req):
1. **Fatia render dia-a-dia + fix de normalização** (A seção 6, imediata, sem schema novo).
2. **Fix temporal do over-merge** (A, local, atrás do eval-gate).
3. **Atribuição por data** (A seção 3) + guarda dura de slug. Define o contrato real: card→`dates`.
4. **Spec B** (produz/garante `dates` confiáveis: conecta M365, cross-check SARC, UI de confirmação).
5. **Inversão v5** (A seção 1-2): só quando uma dor concreta a exigir.

B depende do contrato de dados (`dates`) fechado em A-passo-3; por isso vem depois dele, mas
**antes** da inversão v5.

## Fora de escopo (futuro — pós A+B)

Registrado para não esquecer; **não desenhar nem implementar agora** (depende das 2 refatorações
grandes estarem fechadas):

- **Consumo otimizado de bibliografia pelo tutor.** Hoje a ingestão já **captura** os links de
  material de apoio/bibliografia dos cards (dado real: os 3 URLs `github-repo`/`url` do MF já estão
  no manifest). O trabalho futuro é o **tutor consumir** essas referências de forma otimizada
  (indexar/resumir/linkar ao tópico relevante), não só listá-las. Pré-condição: A+B fechadas.
- **Garantir captura completa de links no import Moodle.** Ao importar, trazer **todos** os links
  embutidos nos cards de bibliografia/material de apoio (não só os arquivos baixáveis). Verificar a
  cobertura do parser de labels/conteúdo Moodle para URLs. Refinamento da trilha-2 (seção 5).
