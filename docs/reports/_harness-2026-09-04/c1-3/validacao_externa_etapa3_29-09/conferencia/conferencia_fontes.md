# Conferência física local das fontes da etapa 2 (read-only, 29/09/2026)

**Resultado: bytes conferem e o inventário está completo; nada foi alterado nem recalculado para aceitar divergência.**
Script: `confere_fontes.py` (sem rede, sem escrita nas fontes). Dados: `conferencia_fontes.json`.

Entradas conferidas: `inventario_downloads.json` (sha256 `d5098196…`, igual ao registrado em `fontes_congeladas.json`,
sha256 `cfc255e2…`) e `.frzero/validacao_externa_aquisicao_29-09/<id>/`.

| curso | arquivos congelados = em disco | itens API = inventário | ok | links | falhas | duplicatas (pares) | colisões | fora do recorte |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 90231 | 37 = 37 | 83 = 83 | 36 | 47 | 0 | 3 | 0 | — |
| 88738 | 83 = 83 | 97 = 97 | 82 | 15 | 0 | 5 | 2 | `.go` 33, `.mod` 1 |
| 81476 | 9 = 9 | 8 = 8 | 8 | 0 | 0 | 0 | 0 | — |
| 82667 | 35 = 35 | 82 = 82 | 34 | 48 | 0 | 0 | 0 | sem extensão 5 |
| 89447 | 21 = 21 | 55 = 55 | 20 | 35 | 0 | 0 | 0 | — |
| 90572 | 26 = 26 | 33 = 33 | 25 | 8 | 0 | 0 | 0 | — |
| 89100 | 22 = 22 | 56 = 56 | 21 | 12 | 23 | 0 | 0 | — |
| 80922 | 42 = 42 | 47 = 47 | 41 | 6 | 0 | 1 | 2 | `.asm` 9, `.jar` 1 |
| **total** | 275 | 461 | 267 | 171 | 23 | 9 | 4 | 49 arquivos |

1. **Bytes:** nenhum arquivo faltando, extra ou divergente contra a árvore congelada. Todo `caminho` do inventário
   tem, em disco, o sha256 registrado. Cada curso tem um arquivo a mais que os `ok`: o `contents.json`.
2. **Inventário × `contents.json`:** cada item listado pela API tem um registro, com a mesma multiplicidade por
   (módulo, arquivo). Não há registro sem item nem chave (módulo, arquivo) repetida. Todos os registros têm status
   conhecido. Módulos sem conteúdo, fora do escopo por tipo: 133 `label`, 21 `forum`, 9 `assign` sem arquivo,
   5 `board`, 4 `groupselect`, 3 `quiz`.
3. **Páginas:** 5 módulos `page` (4 em 82667, 1 em 89100), cada um com um `index.html` registrado `ok` em
   `raw/moodle/pages/`. Não há anexos de página no disco nem no inventário.
4. **Falhas:** as 23 estão em 89100, todas `tipo_inesperado` em `resource` (o servidor devolveu HTML/JSON): 11 `.pdf`,
   7 `.zip`, 5 `.hs`. Nenhuma foi descartada.
5. **Duplicatas:** 9 pares com os mesmos bytes dentro do curso (90231: 3; 88738: 5; 80922: 1); nenhuma entre cursos.
   São 4 colisões de nome na mesma seção, gravadas na pasta do módulo sem sobrescrever.
6. **Formatos fora do recorte** do pacote cego (allowlist v2 = v3), entre os `ok`: 49 arquivos em 3 cursos (tabela).
   Só listados; nada foi reclassificado.

Limite: a conferência cobre o que a etapa 2 gravou. Ela não refaz a aquisição e não verifica se o servidor mudou
depois de 29/09.
