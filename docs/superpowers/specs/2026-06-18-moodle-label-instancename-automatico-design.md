# Design — moodle_label por instancename automático + re-sync por fonte

date: 2026-06-18
branch: `feat/reconciliar-unit-bloco`
status: design aprovado (pendente review do spec escrito)

## Problema

A migração Moodle (S0) captura `moodle_label` (= `mod.name`, o instancename do
recurso, ex. "Aula 03 - Funções Recursivas…") e `posting_date` por arquivo. Mas
o casamento entry↔Moodle é feito por **basename do filename original**
(`backfill_moodle_label_from_api`, `backfill_posting_date_from_api`,
`moodle.py`). Quando o professor sobe vários recursos com o mesmo nome de arquivo
(TCC: todo recurso é `main.pdf`; SO: vários `slides.pdf`), o basename colide
(`counts[base] > 1`) e o backfill **pula** o arquivo → label não cola.

Evidência (probe via Moodle API, 2026/1):
- TCC: 24 entries, `source_section` 23/24 (vem da pasta do stash), `moodle_label`
  **1/24** — os 23 `main.pdf` colidiram. Os arquivos JÁ estão salvos sob o
  instancename (savename), mas o índice do backfill é chaveado pelo filename
  original (`main.pdf`) → mismatch.
- IA: 16 entries vs 68 arquivos no Moodle (import incompleto) + `source_section`
  com datas mutiladas ("Semana 8 - 20 04 a 24 4", espaço) por ser dado gerado
  ANTES do fix de sanitização e6d7fa1.

## Mapa de fonte por curso (confirmado pelo usuário)

Cada curso vem de UM canal (não há sobreposição por arquivo):
- **Moodle** (LMS, `core_course_get_contents`): TCC, IA, SO.
- **M365 / OneDrive** (Graph, nomes com data): MF, ES2 (mesmo professor, Julio).

Implicação: re-sync é por curso. Fix de matching beneficia principalmente os
cursos Moodle (label bom no instancename). Para MF/ES2 captura-se `posting_date`
(aditivo) e seção do Moodle também, mesmo com filename divergente.

## Objetivo

Tornar `moodle_label` (instancename) e `posting_date` colarem **automaticamente**
no import, robusto à colisão de filename (`main.pdf`/`slides.pdf`), reproduzindo
sem trabalho manual o que foi feito à mão no TCC. Re-sincronizar os 5 repos.

## Não-objetivos

- NÃO mudar o matching de `source_section` (caminho consumed / eval-gated). Para
  os cursos Moodle, `source_section` continua vindo da estrutura de pastas do
  stash (pasta = seção), preenchida no build — não do matching por filename.
- NÃO ligar o concept resolver nem mexer na pilha de precedência de atribuição.
- NÃO rotular gold aqui (vem depois, destravado pelo TCC limpo).

## Design

### 1. Chave de matching robusta (Fix A) — `src/builder/sources/moodle.py`

`backfill_moodle_label_from_api` e `backfill_posting_date_from_api` passam a
indexar o `SectionFile` por **dois keys**, ambos `casefold()`:
- `sf.disk_name` (= savename, derivado do instancename via
  `_savename_from_module` → `sanitize_folder_name`, com `/`→`.` para datas);
- `sf.filename` (nome original, fallback p/ repos M365 onde o arquivo mantém o
  nome de origem).

A unicidade é contada **por key**. O entry casa pelo basename do `source_path`:
1. tenta a key savename (única → resolve `main.pdf`);
2. senão, a key filename (comportamento legado, fallback).
Key com `count > 1` é ambígua e pulada (mesma semântica de segurança de hoje).

INVARIANTE: `moodle_label`/`posting_date` são **aditivos** (fill-if-empty no
caso do label) — não entram na atribuição. `rebuild_diff` deve ficar idêntico.

Restrição crítica de correção (motivada pelo `/` em datas): o matching usa o
savename **já sanitizado** dos dois lados (índice e basename do entry). Ambos
passam por `sanitize_folder_name`, que converte `/` entre dígitos em `.`
(verificado: `06/12`→`06.12`, `20/04 a 24/4`→`20.04 a 24.4`). Casar pelo
instancename CRU (com `/`) quebraria, porque o arquivo em disco tem `.`. Nunca
chavear pelo label cru.

Limite conhecido: se dois recursos gerarem o MESMO savename, `download_course`
desambigua o arquivo em disco com sufixo ` (2)`, mas o índice do backfill não vê
esse sufixo → esse arquivo perde o label (raro; aceitável).

### 2. Re-sync por fonte (execução de dados)

- **Moodle (TCC, IA, SO):** rodar `import_moodle_courses(download=True)`.
  `download_course` salva em `<seção>/<instancename>` →
  `source_section` (pasta) e savename (instancename) automáticos → backfill
  aditivo (Fix A) cola `moodle_label` + `posting_date` casando por savename.
  - IA: puxa os ~50 arquivos faltantes.
  - SO: ganha label/seção limpos (resolve a colisão `slides.pdf`).
  - TCC: já está sob savename (renomeado à mão) → re-download é idempotente
    (`skip_existing`); na prática só o re-backfill é necessário.
- **M365 (MF, ES2):** arquivos permanecem (fonte OneDrive). Rodar o backfill
  aditivo contra o conteúdo do Moodle para capturar `posting_date` (e `label`
  onde o filename casa). `source_section` segue pelo caminho atual.

### 3. Testes (TDD) — `tests/test_moodle_labels.py`

RED→GREEN. Fixture sintética de `core_course_get_contents` com:
- Dois módulos na MESMA seção, ambos com `contents=[{filename: "main.pdf", …}]`,
  `name` (instancename) distintos e `timemodified` distintos.
- Um módulo cujo instancename contém data com `/` (ex. "Aula 06/12 - Intro").

Asserções:
- `backfill_moodle_label_from_api`: os DOIS labels colam (casando por savename),
  não mais 0 por colisão.
- `backfill_posting_date_from_api`: os DOIS posting_date colam.
- Guard de data: o savename do módulo "Aula 06/12 - Intro" é
  "Aula 06.12 - Intro.pdf" (`/`→`.`, não espaço) e o entry com esse basename
  casa o label. Regressão direta do report do usuário ("06 12" quebrava o
  matcher).
- Fallback: entry cujo basename = filename original (sem savename) ainda casa
  pela key filename.

Suíte existente (`test_moodle.py`, `test_moodle_labels.py`, roundtrip) verde.

### 4. Eval-gate

- `python scripts/rebuild_diff.py` antes/depois: **idêntico** (drift pré-existente
  ES2 7 / IA 20 / SO 13 / MF 1 mantém-se — é dívida A7, não regressão). Mudança é
  só aditiva.
- `python scripts/eval_assignments.py`: golden PDF 5/5, confiante-errado 0.
- `python -m pytest tests -q`: verde (linha de base 1483 + novos testes).

### 5. Ordem de execução (após merge do código)

1. Implementar Fix A (TDD) + commit.
2. `import_moodle_courses(download=True)` em TCC/IA/SO (com `.apibak`/dry-run
   onde aplicável); backfill aditivo em MF/ES2.
3. Re-rodar `gold_by_card` nos 5 repos (agora com label/seção limpos).
4. Verificar `rebuild_diff` idêntico + golden 5/5 + suíte verde.

## Riscos

- Re-download de IA/SO pode trazer arquivos novos que mudam a estrutura de cards
  → revisar `rebuild_diff` antes de aceitar (não auto-commitar repos).
- `download_course` valida magic bytes; arquivos M365-redirect ou HTML caem em
  `failed` (não corrompe). Conferir `failed` no retorno.
- Colisão de savename (sufixo ` (2)`) é ponto cego do índice — raro; logar.
