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
Opcionalmente derivar um `topic_slugs` de **display** por seção (best-effort), com
**auto-sugestão + confirmação-dos-incertos + congelamento**.

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
- **Auto-sugere + confirma-os-incertos + congela** (`source`: "sarc"|"labels"|"manual";
  `confirmed`: bool). ~6 confirmações por curso (nível-seção, não por arquivo).
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
- Output no `.card_block_map.json` (a chave de join é `dates`):
  ```json
  {
    "Verificação de Programas": {
      "dates": ["2026-04-27", "2026-04-29", "2026-05-04", "2026-05-06", "2026-05-11"],
      "block_ids": ["bloco-10", "bloco-11"],
      "topic_slugs": ["logica-de-hoare", "logica-de-programas-dafny", "verificacao-de-modelos"],
      "source": "sarc",
      "confirmed": false
    }
  }
  ```
- **Confiança:** datas casam por label → forte; datas por cross-check SARC sem label → média,
  `confirmed:false` (não congelar mapa derivado de bloco possivelmente over-merged). Slug-rótulo
  forte (nome ≈ tópico) pode `confirmed:true`.
- **Retro-compat:** `block_ids`/`dates` preservados — são a chave de join, não descartados. A Spec A
  consome `dates`; `topic_slugs` é aditivo.

### 3. Confirmação + congelamento (UI)

- Painel lista as seções com slug sugerido + confiança + datas que casaram. Tu confirma/corrige só
  os `confirmed:false`. Confirmar grava `source:"manual"`, `confirmed:true`.
- `merge_card_block_map` já preserva manual sobre auto re-derivado — **reusar esse comportamento**.
- Volume: ~6 seções por curso (MF), não 60 arquivos.

### 4. SARC como insumo (sem novo artefato)

SARC já é parseado (HTML → markdown → `SYLLABUS.md` → `.timeline_index.json`). B reusa esse parse
como o sinal de cross-check do passo 2 (qual seção casa qual range de datas). **Não persiste
`_CRONOGRAMA.json` novo.**

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
