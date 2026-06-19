# Ingestão Automatizada: Download + Auto-Mapeamento Seção→Slug — Design (Spec B)

last_updated: 2026-06-19
status: design (brainstorming), pendente revisão do spec
escopo: dentro do refactor de atribuição A1-A7; produtor do contrato consumido pela Spec A

## Problema

A atribuição correta (Spec A — `2026-06-19-cronograma-sessao-atomo-design.md`) depende de dois
sinais: o **slug canônico** de cada material (de qual tópico/unidade ele é) e o **cronograma SARC**
(quando o tópico é dado). Hoje, o lado da fonte é manual e frágil:

1. **Download incompleto/manual.** Moodle tem `download_course`, mas M365/OneDrive (canal de MF e
   ES2, prof Julio) não tem download automatizado. Arquivos entram por drops manuais → 28% das
   entries do MF têm `source_section` vazio (sem card) → espalham.
2. **Mapeamento card→destino frágil.** `.card_block_map.json` existe e é auto-derivado dos labels
   Moodle (`derive_card_block_map`), mas mapeia para `block_ids` (bloco heurístico, que a Spec A
   aposenta) e depende de labels que nem todo curso tem.
3. **Sem ponte explícita seção→slug canônico.** A seção Moodle/M365 (o card) não referencia os
   slugs do `.content_taxonomy.json`; a ligação é re-derivada por matching difuso a cada build.

## Objetivo

Automatizar a pipeline de **ingestão** que alimenta a Spec A: baixar materiais (Moodle API +
M365 Graph) para as pastas-seção do professor e **auto-derivar o gabarito seção→slug canônico**
no `.card_block_map.json`, com **auto-sugestão + confirmação-dos-incertos + congelamento**.

Reusa artefatos existentes; **não cria arquivos novos**. O resultado é um stash bem-mapeado +
`.card_block_map.json` populado — o contrato que a Spec A consome.

## Decisões travadas (brainstorming 2026-06-19)

- **Manter as seções do professor** (Moodle/M365) como cards. Sem reorganização física do stash,
  sem esqueleto de pastas-tópico, sem sidecar no stash.
- **Gabarito repo-side:** `.card_block_map.json`. Evoluir `derive_card_block_map` /
  `merge_card_block_map` para sugerir **slug canônico** (`.content_taxonomy.json`) por seção.
- **Auto-sugere + confirma-os-incertos + congela** (`source`: "sarc"|"labels"|"manual";
  `confirmed`: bool). ~6 confirmações por curso (nível-seção, não por arquivo).
- **Seção grossa** (ex.: "Verificação de Programas" = Hoare+Dafny+Modelos) → mapeia para um
  **conjunto** de slugs → colocação grão-unidade (material repete nas aulas do tópico — política
  já aceita na Spec A). Subpasta opcional para grão fino.
- **LLM nunca é autoridade de runtime** (sugestor congelado, se usado).

## Fronteira com a Spec A

B é o **produtor**; A é o **consumidor**. Contrato compartilhado:
- `.card_block_map.json` — seção→slug canônico (B escreve, A lê).
- Sessões SARC (datas+tópicos) no `.timeline_index.json` (parse SARC já existente).

B **não** mexe em atribuição nem render (isso é a Spec A). O trabalho da B termina num stash
mapeado + `.card_block_map.json` confirmado.

## Arquitetura

### 1. Download — dois canais

- **Moodle API** (`src/builder/sources/moodle.py:download_course`, já existe): reusar. Baixa para
  `<stash>/<section>/<savename>`; `skip_existing` por path exato (idempotente). Valida magic bytes.
- **M365 Graph (NOVO):** OneDrive/SharePoint via Microsoft Graph API. Read-only (prof compartilha
  a pasta). Lista `driveItems` (folders/files) + metadados (`name`, `lastModifiedDateTime`); baixa
  para `<stash>/<folder>/<name>`. **Espelha o contrato de `download_course`**: mesma assinatura de
  retorno `{total, downloaded, skipped, failed}`, mesmo `skip_existing` por path, mesma validação.
  Auth Graph (app registration / token; segredo fora do repo, padrão `moddle/.env`).

### 2. Auto-derivação seção→slug (evoluir `derive_card_block_map`)

- Hoje: `derive_card_block_map` mapeia seção→`block_ids` a partir dos labels Moodle (formatos A-C).
- Evolução: mapear seção→**slug canônico** (`.content_taxonomy.json`), combinando 3 sinais:
  1. **Nome da seção** → match contra `topic`/`unit` label+aliases do `.content_taxonomy.json`.
  2. **Datas SARC** → a seção cujo conteúdo casa o range de datas de um tópico do cronograma
     (cross-check temporal, usa o parse SARC existente).
  3. **Labels Moodle** → sinal já consumido hoje (quando existe).
- Output no `.card_block_map.json` (schema evoluído):
  ```json
  {
    "Especificações Indutivas e Recursivas": {
      "unit_slug": "unidade-01",
      "topic_slugs": ["especificacao-conjuntos-indutivos"],
      "source": "sarc",
      "confirmed": false
    },
    "Verificação de Programas": {
      "unit_slug": null,
      "topic_slugs": ["logica-de-hoare", "logica-de-programas-dafny", "verificacao-de-modelos"],
      "source": "sarc",
      "confirmed": false
    }
  }
  ```
- **Confiança:** match forte (nome ≈ tópico E datas casam) → `confirmed:true` auto; fraco/ambíguo →
  `confirmed:false`, vai pra fila de confirmação.
- **Retro-compat:** preservar `block_ids` durante a transição (Spec A migra o consumo de
  `block_ids` para `topic_slugs`).

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
download (Moodle API / M365 Graph)
   → <stash>/<seção>/<arquivos>
derive seção→slug (nome + datas SARC + labels) [evolui derive_card_block_map]
   → .card_block_map.json (com confirmed flags)
[você confirma os incertos na UI]  → merge_card_block_map (manual congela)
   → .card_block_map.json confirmado
        → Spec A consome (join arquivo→seção→slug→sessões→datas)
```

## Reuso / o que é novo

- **Reusa:** `download_course`, `derive_card_block_map`/`merge_card_block_map`,
  `.card_block_map.json`, `.content_taxonomy.json`, parse SARC, `_ARQUIVOS_DO_CARD.txt` (guia).
- **Novo:** módulo de download M365 Graph; evolução do `derive_card_block_map` para emitir slug
  canônico (+ cross-check de datas SARC); painel de confirmação seção→slug.
- **NÃO cria:** sidecar no stash, `_CRONOGRAMA.json`, pastas-esqueleto.

## Invariantes (não-negociáveis)

- SARC / OpenSARC **read-only** (nunca escrito). M365/Graph **read-only** (prof compartilha).
- Token Moodle em `moddle/.env` (`MOODLE_URL`/`MOODLE_TOKEN`); segredo M365 idem. Não logar nem
  commitar segredos.
- Download **idempotente** (skip por path exato); só baixa o que falta.
- **Não auto-commitar** os repos gerados durante re-sync — revisar `rebuild_diff` por repo.
- LLM nunca é autoridade de runtime (sugestor congelado, se usado).
- **Não criar arquivos/campos novos paralelos** — reusar `.card_block_map.json`.
- Gabarito repo-side; stash mantém as seções do professor.

## Testes

- **Download M365 Graph:** mock de respostas Graph; `skip_existing` por path; validação de magic
  bytes; retorno `{total, downloaded, skipped, failed}`; idempotência (re-rodar não re-baixa).
- **derive seção→slug:** fixtures —
  - nome da seção == label do tópico → slug exato, `confirmed:true`.
  - nome ≠ tópico, mas datas SARC casam → slug por data, confiança média.
  - seção multi-tópico → `topic_slugs` lista (set), `unit_slug:null`.
  - seção sem match → `confirmed:false` (vai pra fila).
- **merge:** entrada `source:"manual"`/`confirmed:true` preservada sobre auto re-derivado.
- **Retro-compat:** `.card_block_map.json` antigo (só `block_ids`) lê sob schema evoluído.

## Riscos / decisões em aberto

1. **Auth/permissões M365 Graph** (app registration, prof compartilhar a pasta; escopo read-only).
   Maior incógnita técnica da B.
2. **Rename de pasta no download** (fix de data-padding S0b): seção renomeada re-baixa em pasta
   nova → duplicata em disco. Tratar: normalizar/detectar rename de seção (liga ao S0b já feito).
3. **Seção multi-unidade** → `topic_slugs` cruza unidades → colocação grão-unidade (aceito).
   Subpasta opcional para grão fino (refinamento, não default).
4. **Coerência do slug com `.content_taxonomy.json`** — mesma pré-condição da Spec A (slug
   canônico estável; divergência `unit_index` vs `content_taxonomy`). Pré-req do A1-A7.
5. **Arquivos legados sem seção** (os 17 vazio do MF): o pipeline novo não os gera (todo download
   nasce numa seção), mas o legado precisa de placement manual uma vez.

## Ordem de execução (relativa à Spec A)

Conforme decidido: pré-req (slug canônico estável) → fatia render dia-a-dia (A, imediata) →
Spec A núcleo (define o contrato) → **Spec B** (produz o contrato). B depende do contrato fechado
em A; por isso vem depois.
