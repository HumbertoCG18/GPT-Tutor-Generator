# Approach C — Referências de apoio no COURSE_MAP (design)

last_updated: 2026-06-04
status: aprovado (brainstorming), pronto para plano

## Goal

Referência mapeada a uma unidade/tópico aparece **ativamente** no `course/COURSE_MAP.md`
(arquivo que o tutor carrega 1º na nav map-first) como **material de apoio/reflexão**,
conectada ao material principal daquele tópico. Fecha o gap atual: o mapeamento
ref→unidade/tópico já existe (`computed_ref_unit`/`computed_ref_topics` em
`references_curation.json`) mas só aparece na `BIBLIOGRAPHY.md` global, que está
**fora** da ordem de navegação default do tutor — então a referência nunca surge
sozinha quando o aluno está no tópico dela.

## Não-goal (YAGNI)

- Arquivos por-unidade (`course/units/<unit>/REFERENCES.md`) — Approach C-4, descartado.
- Injeção no `FILE_MAP.md` — C-2, descartado (ref é URL externa, não arquivo abrível).
- Resumo de 3-5 linhas inline no COURSE_MAP — fica o ponteiro pra BIBLIOGRAPHY (orçamento).
- Qualquer mapeamento em runtime do tutor — tudo é build-time (já é hoje).
- Incidência em prova / dependências para referências.

## Comportamento alvo (decidido no brainstorming)

- **Push ativo, enquadrado como apoio.** O tutor aponta a referência por conta própria
  quando o aluno chega no tópico, mas como material complementar — não fonte primária.
  Frase-modelo: *"além do conceito X estar no arquivo Y (material principal), este
  repo/doc também mostra X aplicado / traz reflexão sobre"*. A referência se conecta ao
  material principal do tópico, não fica solta.
- **Granularidade: unidade + tópico se houver.** Ancora na unidade sempre; refina pro
  tópico fino quando há `computed_ref_topics` casando um tópico renderizado.
- **Ponto de injeção: COURSE_MAP inline.** Linha compacta sob o tópico/unidade.

## Invariante crítico (modo degradado)

Sem `references_curation.json`, com curation vazia, ou sem referências mapeadas, o
`COURSE_MAP.md` gerado é **byte-idêntico ao atual**. A feature é puramente aditiva:
nenhuma linha de apoio ⇒ nenhuma mudança no artefato.

## Arquitetura

### Componente 1 — Helper puro (índice de referências por âncora)

Arquivo novo: `src/builder/core/reference_navigation.py`.

```python
def build_unit_topic_reference_index(
    manifest_entries: list,
    reference_curation: dict,
    *,
    normalize_unit_slug,   # Callable[[str], str]
    slugify,               # Callable[[str], str]
) -> dict:
    """Agrupa referências mapeadas por âncora, juntando curation + manifest.

    Retorna:
        {
            "by_unit":  {unit_slug: [ref, ...]},
            "by_topic": {(unit_slug, topic_slug): [ref, ...]},
        }
    onde ref = {
        "entry_id": str, "title": str, "source_path": str,
        "type": "repo" | "doc" | "artigo",
        "concepts": [str, ...],   # de ref_concepts, já cortado a 3
        "topics": [str, ...],     # computed_ref_topics (labels)
        "unit_slug": str,
    }
    """
```

- Curation é keyed por `entry_id` (`references_curation.json["entries"]`). Manifest
  entries trazem `id()`, `title`, `source_path`, `file_type`. Join por id.
- Inclui só refs com `computed_ref_unit` não-vazio. Ref sem unidade é ignorada (continua
  só na BIBLIOGRAPHY).
- `type` derivado: `file_type == "github-repo"` ou `"github.com" in source_path` → `repo`;
  senão `doc` (genérico para URL/documentação). `artigo` reservado para futuro — v1 usa
  só `repo`/`doc` (sem heurística de artigo; mantém simples).
- `concepts` cortado aos 3 primeiros não-vazios.
- `by_topic` indexado por `(unit_slug, slugify(topic_label))` para cada label em
  `computed_ref_topics`. A mesma ref pode entrar em vários `by_topic` (um por topic label)
  **e** em `by_unit` — a dedup tópico-vs-unidade é responsabilidade do renderer.
- Determinístico, sem I/O, sem rede. Ordena as listas por `entry_id` para saída estável.

### Componente 2 — Injeção no renderer do COURSE_MAP

Modificar `render_low_token_course_map_md` (`src/builder/artifacts/navigation.py:401`).
Adicionar dois kwargs novos, ambos com default que preserva o comportamento atual:

```python
def render_low_token_course_map_md(
    course_meta, subject_profile=None, *,
    ...,                       # deps atuais inalteradas
    reference_nav_index: dict | None = None,   # saída do Componente 1
    reference_slugify=None,                     # Callable[[str], str] p/ slug de topic
    ...
):
```

No loop de unidades/tópicos (hoje linhas ~438-447):

```python
for unit_title, topics in units:
    unit_slug = normalize_unit_slug(unit_title)
    lines.append(f"### {unit_title}")
    shown_ids = set()                      # dedup dentro da unidade
    if topics:
        for topic in topics:
            indent = "  " * topic_depth(topic)
            lines.append(f"{indent}- [ ] {topic_text(topic)}")
            topic_slug = reference_slugify(topic_text(topic)) if reference_slugify else ""
            for ref in _capped(by_topic.get((unit_slug, topic_slug), []), shown_ids):
                lines.append(f"{indent}  - {_ref_support_line(ref)}")
                shown_ids.add(ref["entry_id"])
    else:
        lines.append("- [ ] [tópicos a preencher]")
    # refs de unidade ainda não mostradas em nenhum tópico
    unit_leftovers = [r for r in by_unit.get(unit_slug, []) if r["entry_id"] not in shown_ids]
    for ref in _capped(unit_leftovers, shown_ids):
        lines.append(f"- {_ref_support_line(ref)}")
        shown_ids.add(ref["entry_id"])
    lines.append("")
```

Helpers locais ao renderer (ou no módulo do Componente 1, expostos):

```python
_REF_CAP_PER_ANCHOR = 2

def _ref_support_line(ref: dict) -> str:
    concepts = ", ".join(ref["concepts"][:3])
    tail = f" — {concepts}" if concepts else ""
    return f"📖 Apoio: {ref['title']} ({ref['type']}){tail} → content/BIBLIOGRAPHY.md"

def _capped(refs, shown_ids):
    """Até _REF_CAP_PER_ANCHOR refs não-já-mostradas; se sobrar, marca overflow."""
    fresh = [r for r in refs if r["entry_id"] not in shown_ids]
    head = fresh[:_REF_CAP_PER_ANCHOR]
    return head  # overflow tratado pelo caller (ver abaixo)
```

Overflow: quando uma âncora tem mais de `_REF_CAP_PER_ANCHOR` refs frescas, após as 2
linhas emite uma linha `  - (+N referência(s) em content/BIBLIOGRAPHY.md)` no mesmo
indent. (Detalhe exato fica no plano; o spec fixa o comportamento: nunca mais de 2
linhas `📖 Apoio:` por âncora + 1 linha de overflow opcional.)

Linha de apoio (exemplo renderizado):

```
### Desenvolvimento Web
- [ ] Rotas HTTP
  - 📖 Apoio: Flask (repo) — rotas http, WSGI, framework web → content/BIBLIOGRAPHY.md
- [ ] Templates
```

### Componente 3 — Wiring (injeção via `course_meta`, NÃO kwargs)

**Revisão pós-grounding:** a cadeia de wiring (`course_map_md` → `low_token_course_map_md_v2`
→ `render_low_token_course_map_md_v2` → `render_low_token_course_map_md`) passa só
`(course_meta, subject_profile)` em cada nível. Mas o renderer **já lê contexto de
`course_meta` via chaves `_`-prefixadas** (`course_meta["_timeline_context"]`,
`course_meta["_assessment_context"]` — `navigation.py:418,516`), setadas em
`pedagogical_regeneration.py:190,204`. Seguimos esse padrão: injetamos
`course_meta["_reference_nav_index"]`. **Nenhum wrapper muda de assinatura.**

Em `pedagogical_regeneration`, antes de `course_map_md_fn(...)` (`:246`):

```python
from src.builder.core.reference_summary import load_reference_curation
from src.builder.core.reference_navigation import build_unit_topic_reference_index
import json

_manifest_entries = json.loads(
    (builder.root_dir / "manifest.json").read_text(encoding="utf-8")
).get("entries", [])
runtime_course_meta["_reference_nav_index"] = build_unit_topic_reference_index(
    _manifest_entries, load_reference_curation(builder.root_dir)
)
```

Defaults: `course_meta.get("_reference_nav_index") or {}` no renderer → sem índice/vazio,
toda a lógica de apoio é pulada (modo degradado idêntico ao atual).

**Nota sobre o helper:** `build_unit_topic_reference_index` **não** recebe
`normalize_unit_slug`/`slugify` (revisão): `computed_ref_unit` já é o slug correto
(alinhado — `routing/file_map.py:101` usa o mesmo `normalize_unit_slug` que o renderer),
e o tópico usa `_norm_topic` (normalizador trivial compartilhado renderer↔helper). Lê
entries do manifest como **dicts** (`entry.get("id")`), alinhados com as chaves da curation.

### Componente 5 — Limpeza da redundância de relevância na BIBLIOGRAPHY

Motivo: o Approach C move o mapa ref→unidade/tópico pro COURSE_MAP. A tabela
"## Mapa de relevância por tópico" em `bibliography_md` (`repo.py:739-746`) passa a
ser **redundante** — ela já duplica internamente a linha "Relevante para" de cada entry
(`repo.py:720-724`) **e** agora a mesma info vive no COURSE_MAP. Além disso a tabela
carrega duas colunas mortas (`Acessível` sempre "sim", `Incidência em prova` sempre "—").

Mudança em `bibliography_md` (`src/builder/artifacts/repo.py:654`):
- **Remover** a seção "## Mapa de relevância por tópico" (a tabela inteira, incluindo o
  fallback `[a preencher]` e as duas colunas mortas).
- **Substituir** por um ponteiro de uma linha:
  `> O mapa de relevância por tópico agora vive no \`course/COURSE_MAP.md\` (linhas \`📖 Apoio:\`). Esta página traz o resumo completo de cada referência.`
- **Manter** a seção "## Referências importadas" com `Resumo` + `Relevante para` por entry
  (é o registro detalhado, não redundante com a linha curta do COURSE_MAP).
- **Corrigir, de passagem** (estamos editando a função), o label errado do clamp
  (`repo.py:756`): `label="course/COURSE_MAP.md"` → `label="course/BIBLIOGRAPHY.md"`.

Invariante: nenhuma referência mapeada ⇒ o ponteiro ainda é emitido (texto fixo), mas
não há perda — o COURSE_MAP simplesmente não terá linhas de apoio. A seção de entries
permanece igual ao atual.

Teste (em `tests/test_course_map_references.py` ou um `tests/test_bibliography_cleanup.py`):
- BIBLIOGRAPHY gerada **não** contém mais o cabeçalho "Mapa de relevância por tópico" nem
  as colunas "Acessível"/"Incidência em prova".
- BIBLIOGRAPHY contém o ponteiro para `course/COURSE_MAP.md`.
- A seção "Referências importadas" com `Relevante para` continua presente.
- clamp chamado com `label="course/BIBLIOGRAPHY.md"`.

### Componente 4 — Instrução no prompt do tutor

Adicionar bloco curto em `src/builder/artifacts/prompts.py`, junto da descrição do
COURSE_MAP na seção "Arquivos principais" / "Ordem de navegação" (linha ~551). Texto:

> Linhas `📖 Apoio:` no COURSE_MAP são material complementar (repo/doc/artigo) mapeado
> àquele tópico. Use como apoio/reflexão, não como fonte principal: ao explicar o
> tópico, relacione a referência ao material principal — ex.: "além de X estar em
> `<arquivo principal>`, este repo mostra X aplicado". Só aprofunde a referência se o
> aluno demonstrar interesse ou o tópico pedir.

## Fluxo de dados

```
build-time:
  manifest.json (entries) ─┐
                           ├─> build_unit_topic_reference_index ─> reference_nav_index
  references_curation.json ┘                                            │
                                                                        v
  teaching_plan (units/topics) ──> render_low_token_course_map_md ──> COURSE_MAP.md
                                          (injeta linhas 📖 Apoio)

runtime (tutor):
  lê COURSE_MAP.md (1º na nav) ─> vê 📖 Apoio sob o tópico ativo
                               ─> cruza com FILE_MAP (arquivo principal)
                               ─> apresenta como apoio (instrução do prompt)
```

## Tratamento de erro / degradação

| Situação | Comportamento |
|---|---|
| Sem `references_curation.json` | índice vazio → COURSE_MAP idêntico ao atual |
| Curation entry sem manifest correspondente | ref pulada (sem linha) |
| Ref com `computed_ref_unit` vazio | não injetada (fica só na BIBLIOGRAPHY) |
| Tópico mapeado não casa nenhum tópico renderizado | ref cai no balde da unidade |
| Mais de 2 refs por âncora | 2 linhas + 1 linha de overflow `(+N ...)` |
| Estouro do clamp 14k | clamp existente trunca (inalterado); caps mantêm adição pequena |

## Testes (TDD)

**Helper (`build_unit_topic_reference_index`):**
- ref com topic casando → entra em `by_topic[(unit, topic)]`.
- ref só com unidade → entra em `by_unit[unit]`, não em `by_topic`.
- ref com `computed_ref_unit` vazio → excluída de ambos.
- join: curation sem manifest correspondente → excluída.
- `type`: github-repo → `repo`; URL doc → `doc`.
- `concepts` cortado a 3; ordenação estável por entry_id.

**Renderer (`render_low_token_course_map_md`):**
- com índice: COURSE_MAP contém `📖 Apoio: <title>` no indent sob o tópico certo.
- ref só-unidade: linha aparece sob o `### <unidade>`, fora de tópico.
- dedup: ref mapeada a tópico **não** repete na seção da unidade.
- cap: âncora com 3 refs → no máx 2 linhas `📖 Apoio:` + linha overflow.
- **degradado:** `reference_nav_index=None` → saída byte-idêntica à atual (snapshot).

**Prompt (`prompts.py`):**
- prompt gerado contém a instrução de "material de apoio" / "📖 Apoio".

**Wiring (integração leve):**
- `course_map_md` com curation real (fixture pequena) → linha de apoio presente no
  output; sem curation → ausente.

## Arquivos tocados

| Arquivo | Ação |
|---|---|
| `src/builder/core/reference_navigation.py` | criar (helper + line/cap helpers) |
| `src/builder/artifacts/navigation.py` | modificar renderer + 3 wrappers (kwargs repassados) |
| `src/builder/ops/pedagogical_regeneration.py` | construir índice e passar ao course_map_md |
| `src/builder/artifacts/prompts.py` | bloco de instrução de apoio |
| `src/builder/artifacts/repo.py` | bibliography_md: remover tabela de relevância → ponteiro; corrigir label do clamp |
| `tests/test_reference_navigation.py` | criar (helper) |
| `tests/test_course_map_references.py` | criar (renderer + degradado + wiring) |
| `tests/test_prompts_reference_support.py` | criar (instrução no prompt) |
| `tests/test_bibliography_cleanup.py` | criar (remoção da tabela + ponteiro + label) |

## Dependências de código existente (reuso)

- `normalize_unit_slug`, `slugify`, `topic_text`, `topic_depth` — já injetados no renderer.
- `load_reference_curation` — `src/builder/core/reference_summary.py`.
- `computed_ref_unit`/`computed_ref_topics`/`ref_concepts` — já populados pela pipeline
  de referências validada (`summarize_all_reference_entries`).
