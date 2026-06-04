# Referências como Contexto Base do Tutor — Design

last_updated: 2026-06-04
status: aprovado (aguardando revisão do spec escrito)

## Problema (medido em dados reais)

Em 5 repositórios-tutor gerados, todas as entries `category ∈ {referencias, bibliografia}` (repos GitHub, docs) chegam ao tutor como **título + URL, sem conteúdo**. Causas confirmadas no manifest real:

1. **Clone quebrado.** O caminho `process_github_repo` (`source_importers.py:235`) força o branch `main`; repos com default `master`/outro falham com `fatal: Remote branch main not found`. Repos grandes falham no checkout por long-path do Windows (`Filename too long`). Resultado: `base_markdown_len=0`, `extracted_files=0` em 8/8 referências.
2. **Sem resumo.** Mesmo quando há arquivos, nada é resumido para a bibliografia.
3. **Sem relevância por tópico.** `_NO_TIMELINE_CATEGORIES` exclui referência do resolve inteiro — ela não recebe bloco, unidade nem tópico. A tabela "Mapa de relevância por tópico" na `BIBLIOGRAPHY.md` é placeholder fixo.

Consequência: o tutor não tem do que "se basear" numa referência — só o link. O ganho real é zero.

## Objetivo

Dar ao tutor **contexto base real** de cada referência: buscar conteúdo leve (README do repo / texto da página), resumir com Gemini, mapear a unidade/tópico, e surfacear na `BIBLIOGRAPHY.md` com resumo + mapa de relevância. Sem depender do clone completo (que está quebrado e é exagero para uma referência).

## Escopo

Dentro do v1:
- Aquisição leve de conteúdo de referência **sem clone**: README via API do GitHub; **texto de página de doc/URL via o extrator HTML existente** (`url_markdown.html_to_structured_markdown`).
- Resumo via a camada Gemini já existente (lazy: sem `gemini_api_key`, pula o resumo).
- Mapeamento concept→unidade/tópico reusando o scorer existente (determinístico).
- Surfacing na `BIBLIOGRAPHY.md`: resumo por referência + tabela de relevância preenchida.
- Cache por content-hash em `references_curation.json`.
- **Sem token GitHub** (API anônima, 60 req/h por IP; o cache por hash protege o re-run e o volume normal por matéria é baixo).

Fora do v1 (YAGNI / issues separadas):
- Consertar o clone completo (branch default + long-path) — o README-fetch contorna; o clone completo só importa se quiser análise de código de verdade, vira issue própria.
- Injeção automática da referência no contexto de unidade/tópico que o tutor carrega (Approach C).
- Atribuição de **bloco** a referências — referência não é presa a data; continua excluída de bloco por design.

## Arquitetura

Pipeline por entry `category ∈ {referencias, bibliografia}`:

```
referência
  → reference_content.fetch_reference_text(entry)     # NOVO: README (github) ou texto de pagina, sem clone
  → reference_summary.summarize_reference(text, client) # reusa infra Gemini: resumo + concepts (lazy)
  → reference_topic.assign_concepts_to_unit(concepts|texto, unit_index)  # NOVO: concept→unidade/topico (nao bloco)
  → cache em references_curation.json (content-hash)
  → bibliography_md: render resumo + preenche "Mapa de relevancia por topico"
```

### Componente 1 — Aquisição de conteúdo: `src/builder/core/reference_content.py` (novo)

**`parse_github_repo(url: str) -> Optional[tuple[str, str]]`**
- Extrai `(owner, repo)` de formas de URL GitHub (`https://github.com/owner/repo`, com/sem `.git`, com path extra). `None` se não for GitHub.

**`fetch_github_readme(owner: str, repo: str, *, timeout: float = 10.0) -> str`**
- `GET https://api.github.com/repos/{owner}/{repo}/readme` com header `Accept: application/vnd.github.raw`. A API devolve o README do **branch default** — resolve o bug do `main` hardcoded sem detectar branch manualmente.
- Usa `requests` (já dependência do projeto, cf. `helpers.py:466`). Erros de rede/404 → retorna `""` (degrada, não levanta).

**`fetch_reference_text(entry, *, max_chars: int = 16000) -> str`**
- `file_type == "github-repo"` ou `source_path` é URL GitHub → `parse_github_repo` + `fetch_github_readme`.
- Outra URL/doc (página de documentação, artigo) → `requests.get` do HTML + `BeautifulSoup` + **reusa `url_markdown.pick_best_content_root` + `url_markdown.html_to_structured_markdown`** (já filtra menu/rodapé via `is_probably_noise_container`, escolhe o nó de conteúdo principal). Devolve markdown do corpo útil.
- Trunca em `max_chars` (reusa `url_markdown.truncate_markdown_blocks`). Erro de rede/HTML inválido → `""` (degrada). Determinístico dado o conteúdo remoto; o cache (content-hash) evita re-fetch.

### Componente 2 — Resumo: `src/builder/core/reference_summary.py` (novo, reusa Gemini)

**`summarize_reference(text: str, client) -> Optional[dict]`**
- Reusa o padrão de `code_summarization.summarize_code_entry`: prompt → Gemini → objeto com `summary` (prosa curta, contexto base) + `concepts` (3-8 termos do domínio).
- Lazy: `client is None` (sem `gemini_api_key`) → retorna `None` (sem resumo). Nunca quebra o build.
- Texto vazio (`fetch` falhou) → `None`.

### Componente 3 — Relevância de tópico: `src/builder/core/reference_topic.py` (novo)

**`assign_concepts_to_unit(concepts: list[str], fallback_text: str, unit_index: list, *, subtopic_fn) -> dict`**
- Análogo a `code_summarization.assign_code_to_block`, mas alvo = **unidade/subtópico**, não bloco.
- Com `concepts` (do Gemini) → overlap concept↔unidade reusando o scorer/índice de unidade existente. Sem concepts → usa `fallback_text` (título + texto fetchado) pelo mesmo scorer. Determinístico.
- Retorna `{"unit_slug": str, "topics": list[str], "confidence": float}` (vazio se nada casa).

### Componente 4 — Cache: `references_curation.json`

- Espelha `code_curation.json`: `{ entry_hash: {summary, concepts, unit_slug, topics} }`. Content-hash da referência (URL + texto fetchado) como chave. Re-run não re-fetcha nem re-resume se o hash bate. Prune de entradas stale (padrão do projeto).

### Componente 5 — Surfacing: `bibliography_md` (`src/builder/artifacts/repo.py:654`)

- Na seção "## Referências importadas" (já existente, `repo.py:695-708`), por referência adicionar:
  - `- **Resumo:** {ref_summary}` quando houver.
  - `- **Relevante para:** {unidade} / {tópicos}` quando houver.
- Preencher "## Mapa de relevância por tópico" (hoje placeholder, `repo.py:719-727`) a partir das atribuições: linha por referência com tópico → referência.

### Componente 6 — Storage nos campos da entry

- Novos campos na entry: `ref_summary: str`, `ref_concepts: list[str]`, `computed_ref_unit: str`, `computed_ref_topics: list[str]`. Auto-serializam via `FileEntry.to_dict()` (`dataclasses.asdict`, cf. obs 391). Espelhados em `references_curation.json`.

## Modo degradado (lazy, padrão do projeto)

| Condição | Comportamento |
|---|---|
| Com `gemini_api_key` + rede | fetch README → resumo + concepts → mapa de tópico + surfacing completo |
| Sem `gemini_api_key` | fetch README → **sem resumo**; mapa de unidade via título+texto fetchado (determinístico) + surfacing |
| Sem rede / fetch falha | título + URL (comportamento de hoje); nada quebra |
| Doc/URL com HTML vazio ou só-ruído | `fetch` devolve ""; degrada para título + URL |

## Guardrail — repo do tutor ≠ repo de referência

Há DUAS URLs de GitHub no sistema, e o pipeline só pode tocar uma:

| | Onde vive | O que é | Este pipeline |
|---|---|---|---|
| Repo-destino do tutor | `SubjectProfile.github_url` / `repo_root` (gerenciador de matérias) | a **saída** — onde o conhecimento gerado é publicado | **NUNCA fetch/resume** |
| Repo de referência | `FileEntry.source_path`, `category ∈ {referencias, bibliografia}` | uma **entrada** bibliográfica externa | alvo do fetch+resumo |

O fetch/resumo/tema processa **somente FileEntry com `category ∈ {referencias, bibliografia}`**. `SubjectProfile.github_url` e `repo_root` são o repositório-destino do próprio tutor (não são entries, não são fonte) e jamais entram no `fetch_reference_text`. `parse_github_repo` só é chamado sobre `entry.source_path` de referências — nunca sobre `github_url` do perfil.

## O que NÃO muda

- `_NO_TIMELINE_CATEGORIES` continua excluindo referência de **bloco** (correto — referência não é presa a data).
- O clone completo (`process_github_repo`) não é consertado aqui; o README-fetch o contorna. Bug do branch/long-path vira issue separada.
- Extração de data, scorer de bloco, sinal de sequência — intocados.

## Estratégia de testes

### Unitários
- `parse_github_repo`: formas de URL (`github.com/o/r`, `.git`, path extra, não-github → None).
- `fetch_github_readme`: mock de `requests.get` (200 com corpo, 404 → "", timeout → "").
- `fetch_reference_text` doc/URL: HTML de página com menu+rodapé+conteúdo → extrai só o corpo (via `pick_best_content_root`/`html_to_structured_markdown`); HTML vazio/só-ruído → "".
- `summarize_reference`: `client=None` → None; texto vazio → None; com client mockado → dict com summary+concepts.
- `assign_concepts_to_unit`: overlap concept→unidade (caso certo/errado); sem concepts → fallback por texto; nada casa → vazio.

### Integração / surfacing
- `bibliography_md` com entries de referência carregando `ref_summary`/`computed_ref_unit` → renderiza "Resumo", "Relevante para" e tabela de relevância preenchida.
- Degradado: entry sem summary → render só título+URL+unidade (se houver), sem linha de resumo, sem quebrar.

### Harness análogo (medição de valor)
- Gold de referências: `{repo_url, texto_readme_fixo, expected_unit}` contra um índice de unidades. Mede acerto de `assign_concepts_to_unit` (tema), sem rede (texto fixo no fixture). Gate de regressão como no harness de bloco.

### Cache
- Segunda chamada com mesmo hash não re-fetcha nem re-resume (mock conta as chamadas).

## Arquivos tocados

| Arquivo | Mudança |
|---|---|
| `src/builder/core/reference_content.py` | NOVO: `parse_github_repo`, `fetch_github_readme`, `fetch_reference_text` (doc/URL reusa `text/url_markdown.py`) |
| `src/builder/core/reference_summary.py` | NOVO: `summarize_reference` (reusa padrão Gemini) |
| `src/builder/core/reference_topic.py` | NOVO: `assign_concepts_to_unit` |
| `src/builder/artifacts/repo.py` | `bibliography_md`: render resumo + relevância; preenche mapa de tópico |
| `src/models/core.py` (ou FileEntry) | campos `ref_summary`, `ref_concepts`, `computed_ref_unit`, `computed_ref_topics` |
| pipeline de processamento (ops) | chama fetch→summary→topic para entries de referência; grava cache `references_curation.json` |
| `tests/test_reference_context.py` | NOVO: unit + integração + harness |

## Riscos e mitigação

- **Rate limit da API GitHub (sem token):** 60 req/h por IP. Mitigação: cache por hash evita re-fetch; v1 não autentica (volume baixo — poucas referências por matéria). Documentar; token opcional vira follow-up se necessário.
- **README não representa o repo:** alguns repos têm README pobre. Aceito no v1 — ainda é muito mais contexto que só o título. Análise de código completo fica para o conserto do clone (issue separada).
- **Conteúdo remoto muda (não determinístico):** o cache fixa o snapshot; o harness usa texto fixo no fixture (sem rede). Build real aceita variação (é conteúdo externo).
