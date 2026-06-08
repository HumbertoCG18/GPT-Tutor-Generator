# Design: Import de arquivos M365/OneDrive do professor

last_updated: 2026-06-08
status: aprovado para planejamento

## Problema

Parte do material de algumas disciplinas (ex.: Métodos Formais, curso Moodle
92717, Prof. Julio Machado) não fica no Moodle: o professor hospeda no OneDrive
for Business dele (`brpucrs-my.sharepoint.com/personal/10070245_pucrs_br/...`) e
distribui links org-scoped ("funciona para pessoas na PUCRS").

A API Web Services do Moodle (`core_course_get_contents`) **não expõe** esses
arquivos — confirmado: 0 ocorrências de sharepoint no JSON do curso 92717. O
importer atual (Moodle WS + token) não tem como vê-los nem baixá-los.

## Spike de viabilidade (concluído, positivo)

`scripts/m365_probe.py` validou contra o tenant PUCRS real:

| Etapa | Resultado |
|-------|-----------|
| Device-code OAuth, client público "Microsoft Graph Command Line Tools" (`14d82eec-204b-4c2f-b7e8-296a70dab67e`) | funciona (o client do Azure CLI dá `AADSTS65002`) |
| Escopo `Files.Read.All Sites.Read.All offline_access` | concedido |
| `/me/insights/shared?$top=200` | 153 itens; **59 do curso**, cobrindo TODAS as subpastas (dafny, logica_programas, isabelle, correcao_provasinducao, especificacao_indutiva, revisao, introducao, trabalhos, exercicios_revisao, plano.pdf) |
| `/me/insights/shared/{id}/resource` | resolve pro driveItem |
| download (`@microsoft.graph.downloadUrl` ou `/content`) | íntegro (`mcs.pdf` 13 MB, `%PDF`) |

Becos sem saída descartados pelo spike (NÃO tentar de novo):
- `/shares/{id}` com URL de visualizador (`_layouts/15/onedrive.aspx?id=`) → 403.
- Traversal por caminho no drive do professor (`/drives/{id}/root:/path`) → 404.
- Listar pasta-pai de item compartilhado avulso → 404 (share item-a-item).
- `/me/drive/sharedWithMe` → só 1 item (incompleto; a página web /shared usa insights, não esse endpoint).
- `$top` default do insights traz só ~10; **precisa `$top` explícito** (usar 200).

Conclusão: a descoberta completa vem de `insights/shared` com `$top` alto,
filtrado por path. Não precisa de share-link de pasta nem RPA.

## Decisões de arquitetura (do usuário)

1. **Escopo por matéria**: `SubjectProfile.m365_filter` (substring de path, ex.:
   `metodosformais`). Importer puxa insights e mantém itens cujo webUrl contém o
   filtro.
2. **Mapeamento subpasta→card = MESCLAR** com os cards do Moodle por similaridade
   de nome (fallback: card novo nomeado pela subpasta OneDrive). Ver matcher abaixo.
3. **Gatilho = INTEGRADO** ao diálogo de import Moodle: checkbox "Incluir
   material do OneDrive (M365)". Um fluxo só.
4. **`.zip` baixado como está** (sem extrair).
5. **Preenche `source_section`** de cada arquivo M365 (= card mesclado/criado),
   igual ao backfill do Moodle.

### Decisões menores (defaults)

- Card default (arquivos na raiz do curso, ex.: `plano.pdf`): pasta `_geral`.
- Paginação: seguir `@odata.nextLink` até o fim (não capar em 200).
- `m365_filter`: substring no path completo; campo de texto livre, sem auto-detecção.
- `skip_existing`: pular arquivo já baixado (re-run idempotente).
- Nome de arquivo: `name` do driveItem direto (único e descritivo).
- Token: um arquivo por máquina (desktop single-user).

### Matcher subpasta→card (merge)

`match_card(subfolder, moodle_sections) -> (card_name, matched: bool)`:
- Normaliza ambos: minúsculas, remove acentos, quebra em tokens por `_ - espaço`.
- Score = sobreposição de tokens (Jaccard sobre o conjunto menor).
- Casa se score ≥ limiar (ex.: ≥0.34 ou ≥1 token distintivo). Senão cria card
  com o nome da subpasta.
- Exemplos reais (curso 92717): `introducao`↔"Introdução a Métodos Formais" ✓;
  `correcao_provasinducao`↔"Provas por Indução" ✓; `logica_programas`↔
  "Verificação de Programas" (via "programas") ✓; `dafny`/`isabelle`→sem match,
  card novo. **Limitação assumida**: esquemas de nome divergem; merge é
  best-effort. O import REPORTA o mapeamento (subpasta→card, matched/criado) pra
  revisão; correção manual fica como melhoria futura, não bloqueia.

## Componentes

### `src/builder/sources/m365.py` (novo)

Usa `requests` (já é dependência; não seguir o stdlib-only do `moodle.py`).

- `class M365Client`:
  - `device_login() -> token` — device-code; imprime/retorna `verification_uri`
    + `user_code` via callback pra UI mostrar; faz polling. Não imprime token.
  - `list_shared(top=200) -> list[dict]` — `GET /me/insights/shared?$top=...`;
    cada item normalizado em `{id, title, type, web_url}`.
  - `resolve(insight_id) -> dict` — `GET /me/insights/shared/{id}/resource`.
  - `download(item) -> bytes` — `@microsoft.graph.downloadUrl` ou `/content`.
- Token cache: `moddle/.m365_token.json` (refresh token; `offline_access`).
  Renova silenciosamente; re-login só quando refresh expira. Arquivo no
  `.gitignore`. Nunca logar token.
- Funções puras (testáveis sem rede):
  - `parse_onedrive_path(web_url) -> segments` — caminho server-relative.
  - `subfolder_for(web_url, m365_filter) -> str` — subpasta imediata após o
    filtro (ou `_geral` se na raiz). Sanitiza com `sanitize_folder_name`.
  - `select_for_subject(items, m365_filter) -> list` — filtra por substring no path.
  - `match_card(subfolder, moodle_sections) -> (card, matched)` — ver matcher acima.

### Reuso do que já existe (Moodle bugfix desta sessão)

- `looks_like_expected(filename, data)` (magic bytes) — valida antes de gravar.
  `.zip`→PK, `.pdf`→%PDF, `.thy`/desconhecido→aceita.
- Backstop anti-colisão (set de targets por execução).
- `disk_name`/nome descritivo: aqui o nome do arquivo OneDrive já é único e
  descritivo; usar o `name` do driveItem direto.

### `download_subject_m365(client, subject, moodle_sections, dest) -> dict`

Orquestra: `list_shared` (com paginação) → `select_for_subject(m365_filter)` →
para cada item: deriva `subfolder` → `match_card(subfolder, moodle_sections)` →
`resolve` → `download` → valida magic bytes → grava em `dest/<card>/<name>`
(skip_existing + backstop anti-colisão). Preenche `source_section=<card>` no
manifest (reusa a lógica de backfill do Moodle). Retorna
`{total, downloaded, failed, mapping:[(subfolder,card,matched)]}`.

### Modelo

`SubjectProfile.m365_filter: str = ""`. Retrocompatível (`from_dict` filtra por
campos válidos; perfis antigos recebem default).

### UI (`src/ui/dialogs.py`) — integrado ao import Moodle

No diálogo de import Moodle (junto do checkbox "Baixar arquivos PDF"):
1. Checkbox "Incluir material do OneDrive (M365)". Campo de texto `m365_filter`
   (pré-preenchido do `SubjectProfile` se houver).
2. Ao importar com M365 ligado: dispara `device_login`; mostra `verification_uri`
   + `user_code` num dialog copiável, aguarda em thread.
3. Após auth, roda `download_subject_m365` usando as seções Moodle do curso pro
   merge. Baixa pro `stash_folder` (mesma base do download Moodle).
4. Reporta no fim: Moodle (downloaded/failed) + M365 (downloaded/failed +
   mapping subpasta→card, marcando quais casaram com card Moodle e quais viraram
   card novo).
5. Persiste `m365_filter` no `SubjectProfile`.

## Erros e bordas

- Auth: `authorization_pending`/`slow_down` no polling; `expired_token` → re-login.
- Tenant bloqueia client (`AADSTS50059/53003`) → mensagem clara: "M365 indisponível
  neste tenant". Não quebra o resto do import.
- Insights vazio / filtro sem match → reporta 0, não falha.
- Tipos não-PDF (`.zip`, `.thy`) → baixados como source; pipeline decide downstream.
- Token expirado no meio → tenta refresh; se falhar, marca restante como failed.

## Testes (espelham `tests/test_moodle.py`)

- `parse_onedrive_path` / `subfolder_for` / `select_for_subject` — puros, sem rede.
- `match_card`: casa por token (introducao↔"Introdução...", provasinducao↔
  "Provas por Indução"); sem match → card novo pela subpasta.
- `download_subject_m365` com `requests` mockado (monkeypatch): item PDF ok,
  magic byte errado → failed, merge subpasta→card correto, source_section
  preenchido, colisão de nome → sem perda, paginação `@odata.nextLink`.
- `SubjectProfile` round-trip com `m365_filter`.
- Device-code: mock das respostas `devicecode`/`token` (pending→sucesso).

## Segurança

- Refresh token em `moddle/.m365_token.json`, no `.gitignore`. Permite revogar.
- Nunca imprimir/logar access ou refresh token.
- Client id é público (não é segredo). Escopo mínimo: leitura.

## Fora de escopo (YAGNI)

- RPA / automação de navegador (não necessário — Graph+Insights cobre).
- App Azure registrado próprio (client público basta).
- Share-link de pasta (insights dispensa).
- Upload/escrita no OneDrive (só leitura).
- Descoberta automática do `m365_filter` (usuário configura por matéria).
- Extração de `.zip` (baixado como está).
- Correção manual do mapeamento subpasta→card (best-effort + relatório; melhoria futura).
