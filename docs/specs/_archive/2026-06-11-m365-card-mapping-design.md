# Spec — Mapeamento de card do M365 pela API Moodle (mata o chute léxico)

date: 2026-06-11
status: aprovada (brainstorm na sessão de 11/06, noite)
base: `docs/reports/2026-06-11-reanalise-atribuicao.md` (causa raiz provada)

## Problema

O fluxo M365 (`download_subject_m365`, src/builder/sources/m365.py:222) decide em
qual card do stash cada arquivo cai por **afinidade léxica de tokens**
(`match_card`, threshold 0.34) entre o nome da subpasta do OneDrive do professor
e os nomes das seções Moodle. O professor organiza o OneDrive por tópico
("logica", "dafny"); o Moodle, por card. Resultado provado no caso real
Metodos-Formais: pasta `logica` → card "Revisão - Lógica e Especificação"
(score 1.0) enquanto a seção correta "Verificação de Programas" pontua 0.0 —
~15 arquivos no card errado, `source_section` contaminado via
`apply_source_section`, e toda a cadeia de atribuição de bloco envenenada a
jusante.

A verdade sempre esteve disponível: `section_file_index` (moodle.py:132) mapeia
basename→seção real a partir do MESMO `core_course_get_contents` que a UI já
busca para gerar `_ARQUIVOS_DO_CARD.txt`.

Bugs satélites no mesmo fluxo (mesma spec):
- `m365_filter` digitado nunca é persistido: `dialogs.py:1966-1969` faz
  `store.get(info0["name"])` com o nome vindo do Moodle ("Métodos Formais para
  Computação"), que não bate com o nome no SubjectStore ("Metodos-Formais") —
  save pulado em silêncio.
- Filtro com grafia divergente do caminho OneDrive (espaço, acento, nome do
  professor) degrada TUDO para `_geral`/pasta literal sem nenhum aviso.

## Escopo

DENTRO: mapeamento de card pela API Moodle; fallback honesto; persistência e
validação do filtro; `apply_source_section` só com verdade; testes.

FORA (decisões do brainstorm):
- Reparo dos dados existentes (mover arquivos do stash real, consertar
  `source_path` quebrados no manifest) — ciclo separado.
- Trocar `insights/shared` pela árvore real do OneDrive via Graph
  (driveItem/parents) — evolução futura; resolveria a incompletude da listagem,
  mas muda permissões e escopo.
- Qualquer uso de léxico como "segunda linha" — descartado explicitamente.

## Design

### 1. `download_subject_m365` passa a receber o índice da API

Assinatura nova (parâmetro `moodle_sections` morre):

```python
def download_subject_m365(client, m365_filter, section_index, dest,
                          skip_existing=True, progress_cb=None) -> dict
```

- `section_index`: resultado de `section_file_index(contents)`
  (moodle.py:132) — `{basename.casefold(): section_name}` — construído pelo
  CHAMADOR (UI) a partir dos contents que ela já busca. O índice deve ser
  estendido para marcar basenames AMBÍGUOS (mesmo nome em >1 seção) — ver §2.
- Resolução do card por arquivo, nesta ordem:
  1. `section_index` hit (não-ambíguo) → card = seção real, `matched=True`,
     origem `moodle_api`.
  2. Miss ou ambíguo → card = subpasta literal do OneDrive
     (`subfolder_for`, sanitizada) ou `_geral`; `matched=False`, origem
     `fallback_pasta`. SEM match léxico.
- Retorno: `mapping` vira lista de `(basename, card, origem)` por arquivo
  (não mais por subpasta); demais campos mantidos.
- `match_card`, `_token_affinity`, `_norm_tokens` (uso exclusivo do match) e
  `_DEFAULT_ALIASES` são REMOVIDOS — adição com limpeza. `subfolder_for` fica
  (fallback e diagnóstico). O parâmetro `aliases` morre junto.

### 2. Índice com detecção de ambiguidade

Novo helper em moodle.py (ao lado de `section_file_index`):

```python
def section_file_index_strict(contents) -> tuple[dict, set]:
    """({basename: secao} só para basenames únicos, {basenames ambíguos})"""
```

Basename presente em >1 seção entra no set de ambíguos e FICA FORA do dict —
ambíguo é tratado como miss (fallback pasta literal + aviso), espelhando o
contrato de `backfill_source_section_from_api` (moodle.py:140).

### 3. `apply_source_section` só grava verdade

`name_to_section` passa a conter SOMENTE arquivos com `matched=True`. Arquivos
em fallback não escrevem `source_section` no manifest — entry fica sem seção
(degradação visível na cadeia de atribuição, nunca seção inventada).

### 4. Persistência do filtro (dialogs.py)

Lookup do perfil por SLUG, não por nome exato: a UI já calcula
`info0 = parse_moodle_course(selected[0])` e usa `info0["slug"]` para `mdest`.
Procurar no store o perfil cujo `slug` (ou `moodle_course_id`) case; fallback
para o lookup por nome atual. Achou → grava `m365_filter`. Não achou → loga
aviso visível no resumo (não silencioso).

### 5. Validação do filtro (m365.py, pré-download)

Após `select_for_subject`:
- 0 itens → aborta o passo M365 com mensagem: "filtro não casou nenhum item
  compartilhado — confira a grafia (o filtro é substring da URL do OneDrive,
  sem espaços/acentos)".
- > 50% dos itens selecionados sem o filtro casando segmento do caminho
  (subfolder = `_geral` por miss de segmento) → download prossegue, mas o
  resumo ganha aviso: "filtro não aparece no caminho de N/M arquivos — layout
  pode cair todo em _geral".

### 6. Sem contents Moodle (API fora no momento do import M365)

`section_index` vazio/None → TODO arquivo em fallback pasta literal,
`matched=False`, aviso destacado no resumo: "API Moodle indisponível — nenhum
card atribuído; reimporte quando voltar". Nunca léxico, nunca chute.

### 7. UI (dialogs.py ~1947-1978)

- Constrói `section_index` com os contents já buscados (linhas 1952-1957 já
  iteram `get_course_contents` — reusar a MESMA resposta, não re-buscar).
- Resumo do import mostra: baixados, falhas, atribuídos pela API (N),
  fallback (M) com lista dos basenames em fallback (primeiros ~8).

## Erros e degradação

| Situação | Comportamento |
|---|---|
| Basename no índice | card = seção real, source_section gravado |
| Basename ambíguo | pasta literal, sem source_section, listado no aviso |
| Basename fora do índice | pasta literal, sem source_section, listado no aviso |
| Índice vazio (Moodle off) | tudo pasta literal + aviso destacado |
| Filtro casa 0 itens | passo M365 abortado com mensagem acionável |
| Filtro não casa caminho | aviso de layout degradado, download segue |

## Testes (tests/test_m365_card_mapping.py, novo)

Fixtures: contents Moodle sintético (3 seções, 1 basename ambíguo) + URLs no
formato SharePoint PUCRS. Sem rede — `M365Client` mockado/funções puras.

1. Hit: arquivo da pasta OneDrive "logica" cujo basename está na seção
   "Verificação de Programas" → card Verificação (o caso real do bug).
2. Miss: basename desconhecido → pasta literal da subpasta OneDrive.
3. Ambíguo: basename em 2 seções → pasta literal + presente no aviso.
4. Índice vazio → tudo fallback + flag de aviso no retorno.
5. `apply_source_section` ignora `matched=False`.
6. `section_file_index_strict`: unicidade e set de ambíguos.
7. Validação de filtro: 0 itens aborta; maioria `_geral` sinaliza.
8. Regressão de limpeza: `match_card` não existe mais (import falha) —
   garante que nenhum caminho léxico sobreviveu.

## Critérios de aceite

- Suíte completa verde (1218+ novos).
- Cenário real reproduzido em teste: pasta `logica` com LogicaDeHoare.pdf →
  card "Verificação de Programas" via índice (hoje: "Revisão...").
- `grep match_card src/` vazio.
- Import com Moodle off não inventa seção nenhuma.

## Riscos

- `download_subject_m365` tem 1 chamador de produção (dialogs.py:1964) e
  `tests/test_m365.py` (vários testes de match_card/download que serão
  reescritos para o contrato novo — parte do trabalho, não efeito colateral).
- `_DEFAULT_ALIASES` removido: perde-se o "empurrão" dafny→Verificação no
  fallback. Aceito: fallback honesto (pasta `dafny` literal) é o comportamento
  desejado; a seção real vem do índice quando o arquivo existe no Moodle.
- Stash existente NÃO é tocado (escopo); arquivos já errados continuam errados
  até o ciclo de reparo.
