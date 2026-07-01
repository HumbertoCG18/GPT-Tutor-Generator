# Auditoria e limpeza de artefatos (#18) — Design

date: 2026-06-11
roadmap: #18
status: aprovado para plano

## Objetivo

Auditar o conjunto de ~70-90 artefatos gerados por build, registrar um contrato
de referência (verdito por artefato), e executar a única remoção realmente
segura identificada: o artefato morto `build/PROGRESS_SCHEMA.md`. Escopo
conservador e reversível — nada de consolidação agressiva.

## Achados da investigação (fatos, com file:line)

Inventário completo mapeado (write call sites + consumidores). Classificação em
4 classes: **código-lê**, **diagnóstico-humano**, **tutor-facing**, **morto**.

Verdito dos candidatos borderline:

- `course/CRONOGRAMA_DETALHADO.md` — referenciado em `MODES.md` (tutor). **MANTER.**
- `course/CODE_INDEX.md` — consumido por `pedagogy.py` (modo code_review). **MANTER.**
- `course/CODE_HEALTH.md` (`code_health_md`, repo.py:1026) e
  `course/CRONOGRAMA_HEALTH.md` (`cronograma_health_md`, cronograma_health.py:161)
  — diagnósticos reais (cobertura, bandas de confiança, conflitos). A UI **não**
  expõe isso ao vivo (`maintenance_panel` só detecta órfãos, diagnóstico
  distinto). São o **único** lugar do diagnóstico. **MANTER.**
- `course/COURSE_IDENTITY.md`, `course/SOURCE_REGISTRY.yaml` — write-only pelo
  código, mas valor de metadado/traceability pra humano. **MANTER.**
- `build/claude-knowledge/bundle.seed.json`, `.deeptutor/*`,
  `system/OUTPUT_TEMPLATES.md`, 5 JSONs internos — consumidos. **MANTER.**
- **`build/PROGRESS_SCHEMA.md`** (`progress_schema_md`, repo.py:42-92) — doc
  estático; **0 referências** fora dos write-sites; ausente de `prompts.py`;
  `STUDENT_STATE.md` é auto-descritivo; relatório já o marcou obsoleto.
  **MORTO → REMOVER.**

Conclusão honesta: o conjunto está bem curado. A limpeza desta passada é
pequena de propósito; não há outros artefatos mortos.

## Entregável 1 — Documento de auditoria

Arquivo: `docs/reports/2026-06-11-auditoria-artefatos.md` (Markdown, versionado).

Conteúdo: tabela única com TODOS os artefatos gerados, colunas:
`artefato (path) | gerador (file:line) | consumidor | classe | verdito | razão`.

Seções:
1. Tabela de inventário (todos os artefatos, com a classe e verdito).
2. Nota de manutenção: "A cada novo artefato adicionado a um build, acrescentar
   uma linha aqui com a classe e o consumidor." (cumpre o princípio do usuário:
   a cada adição, uma limpeza/registro).
3. Registro da ação desta passada: remoção de `build/PROGRESS_SCHEMA.md`.

Este doc é só conteúdo (não tem teste de código); a validação é revisão humana.

## Entregável 2 — Remover `PROGRESS_SCHEMA.md`

Remoção completa, threading por todos os sites (verificados):

1. **Gerador**: deletar `progress_schema_md()` em `src/builder/artifacts/repo.py:42-92`.
2. **Facade** `src/builder/facade/repo_docs.py`: remover linha 18
   (`progress_schema_md = repo_artifacts_module.progress_schema_md`) e a entrada
   `"progress_schema_md": progress_schema_md,` (linha 43).
3. **Engine** `src/builder/engine.py`:
   - remover alias `progress_schema_md = _repo_doc_aliases["progress_schema_md"]` (linha 2331);
   - remover `"progress_schema_md",` da lista de nomes (linha 2423);
   - remover os 3 kwargs `progress_schema_md_fn=progress_schema_md` nas chamadas
     de impl (linhas 1789, 2104, 2164).
4. **bootstrap_ops** `src/builder/ops/bootstrap_ops.py`:
   - remover o import/param `progress_schema_md_fn,` (linha 86) da assinatura de
     `write_root_files`;
   - remover o write `write_text(builder.root_dir / "build" / "PROGRESS_SCHEMA.md", progress_schema_md_fn())` (linha 156).
5. **incremental_build** `src/builder/ops/incremental_build.py`:
   - remover o param `progress_schema_md_fn` da assinatura de
     `incremental_build_impl` (linha 15);
   - remover o bloco condicional de write (linhas 105-107).
6. **pedagogical_regeneration** `src/builder/ops/pedagogical_regeneration.py`:
   - remover o param `progress_schema_md_fn,` (linha 166) da assinatura de
     `regenerate_pedagogical_files`;
   - remover o bloco condicional de write (linhas 416-418).
7. **Stale-delete (limpa repos existentes)** em
   `pedagogical_regeneration.py:176-181`: a lista `stale_files` já deleta
   `student/PROGRESS_SCHEMA.md` (legado). **Adicionar**
   `builder.root_dir / "build" / "PROGRESS_SCHEMA.md"` à lista, para que repos já
   construídos tenham o artefato removido no próximo build. Manter a entrada
   `student/` (legado, inofensiva).

## Ordem de edição (evitar quebra entre passos)

Remover do consumidor para o produtor: primeiro os write-sites + assinaturas
(passos 4-6) e os kwargs do engine (passo 3), depois facade (passo 2), por fim
o gerador (passo 1). Adicionar o stale-delete (passo 7) junto. Assim nenhum
estado intermediário referencia um símbolo já removido.

## Validação

- `grep -r "progress_schema" src/ tests/` após a remoção → só pode restar (se
  algo) o stale-delete do passo 7 referindo o path string `PROGRESS_SCHEMA.md`,
  nenhuma referência ao símbolo `progress_schema_md`.
- `grep -r "PROGRESS_SCHEMA" src/` → só o(s) path(s) em `stale_files`.
- Suíte completa verde (`pytest -q`); nenhum teste referencia PROGRESS_SCHEMA
  hoje, então não deve haver regressão. Se algum teste construir um repo e
  asseverar a existência de `build/PROGRESS_SCHEMA.md`, removê-lo/ajustá-lo.
- Sanity: um build de teste (via fixture existente) não deve mais emitir
  `build/PROGRESS_SCHEMA.md`.

## Não-objetivos

- Consolidar índices por categoria, health reports, COURSE_MAP+FILE_MAP, ou os
  5 JSONs internos (escopo agressivo, recusado).
- Remover qualquer artefato diagnóstico/metadado humano-facing.
- Tocar os 3 `INSTRUCOES_*` ou `.deeptutor/*`.
