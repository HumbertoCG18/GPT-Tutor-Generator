# Plano (FUTURO) — Refactor para Material-Agnostic Per-Block Aggregation

**Status**: Backlog / discussão futura. NÃO iniciar até `code-summarization-gemini.md` estar concluído e estabilizado.

**Origem**: discussão durante o plano de code summarization. Identificamos que o FILE_MAP atual é **fragmentado por categoria** (PDFs juntos, código junto, imagens juntas), mas o aluno pensa **por aula**: "o que vimos no dia X?".

---

## Problema

Hoje, quando o aluno pergunta ao tutor "Com base no cronograma, o que vimos hoje? Me dá um resumo", o tutor precisa **costurar manualmente** dados de:

- `SYLLABUS.md` (tabela ASPNET com data + linha)
- `.timeline_index.json` (blocks com `topics`, `primary_topic_label`)
- `FILE_MAP.md` (agrupado por categoria, NÃO por bloco)
- `CODE_INDEX.md` (agrupado por unidade, NÃO por aula — até a Fase 3 do plano code summarization)
- `EXERCISE_INDEX.md`, `GLOSSARY.md` (independentes)

A resposta fica incompleta ou requer múltiplas leituras cross-doc. LLM Projects funciona melhor com docs **explícitos e auto-contidos**.

## Visão

`CRONOGRAMA_DETALHADO.md` material-agnostic — um arquivo bloco-por-bloco que agrega TODO o material da aula:

```markdown
## Aula 7 — 2025-04-15 — Classes e ghosts em Dafny

**Unidade**: 4 — Verificação com tipos
**Tópicos cobertos**: classes, objetos, ghosts, autocontrato, type invariants

### Materiais
- **PDFs/Slides**:
  - `slide-aula-07.pdf` — Slides apresentados
  - `cap-4-livro.pdf` — Leitura prévia (cap. 4)
- **Códigos**:
  - `tiposindutivos.zip` — Verificação com classes (ghosts, autocontrato)
- **Imagens/Quadro**:
  - `quadro-15-04.jpg` — Diagrama de classes
- **Exercícios**:
  - Lista 3 questão 4 — Verificar invariante de classe

### Conceitos do glossário
- [ghost](../glossary/...) — Variável fantasma para especificação
- [autocontrato](../glossary/...) — ...

### Aulas relacionadas
- Aula 6 (08/04): Lógica de Hoare (pré-requisito)
- Aula 8 (22/04): Type theory (próximos passos)
```

## Pré-requisitos

- [x] `code-summarization-gemini.md` Fase 1-6 concluídas
- [x] **`cronograma-schema-robusto.md` Fases 0–6 concluídas** (handshake na Fase 7 daquele plano):
  - Cada bloco tem `kind` confiável — enum fechado de 14 valores, `classifier.py` como fonte única determinística. O renderer escolhe template por kind (aula vs feriado vs prova) sem reinventar heurística.
  - `block_status` derivado em read-time (`derive_block_status`) distingue defeito real de não-aplicável — o render agnóstico não mostra "feriado sem material" como erro.
  - Tópico/unidade resolvidos em camadas (matcher → voto → fallback humanizado) + curation durável (`.timeline_curation.json`) → `missing_unit`/`missing_topic` ≈ 0.
  - Schema v4 (`schemas/timeline_index.v4.json`) validado em CI (`validate-timeline.yml`).
- [x] Cada `FileEntry` tem `manual_timeline_block_id` ou auto-tag `bloco:bloco-NN` confiável. Regra de injeção (`content_taxonomy.py`): `bloco:` entra com `confidence ≥ 0.50 AND não-ambíguo`, ou precedência absoluta de `manual_timeline_block_id`. **Vale pro material que já resolve bloco** (código via concept-match + qualquer entry com unit/topic forte).
- [ ] PDFs/imagens/exercícios que **ainda não resolvem bloco** precisam de mecanismo análogo ao concept-match — summary leve via Gemini? Heurística de unit-match estendida? Discutir antes. (Único pré-req remanescente; é a Fase 3 da ordem de execução abaixo.)
- [ ] Decidir se SYLLABUS.md sobrevive em paralelo (tabela crua) ou se vira só CRONOGRAMA_DETALHADO (pode quebrar workflow existente).

## Pontos a investigar quando iniciar este plano

1. **FILE_MAP atual** — `src/builder/routing/file_map.py` agrupa por que critério? Refactor pra dual grouping (por categoria + por block)?
2. **Atribuição de block pra PDFs/imagens** — ~~hoje `auto_tags=bloco:XX` existe; em que critério ele é injetado? Vale pra PDFs? Confiável?~~ **RESPONDIDO (handshake Fase 7 do schema-robusto):** injetado em `content_taxonomy.py` (`add_managed_*_tags`) com `confidence ≥ 0.50 AND não-ambíguo`, ou precedência de `manual_timeline_block_id`. Vale pra qualquer entry (inclui PDF/imagem) **que pontue bloco acima do threshold** — material fraco/genérico fica sem tag (correto). O gap restante é elevar a taxa de match desses materiais (Fase 3 da ordem de execução).
3. **EXERCISE_INDEX** — quem renderiza? Linkagem com block existe?
4. **Glossário per-block** — termos do glossário têm linkagem com block? Ou só com unit?
5. **Performance de geração** — se rolar Gemini summary pra TODO material, custo escala. Cap? Filtros?

## Ordem de execução (estimativa)

| Fase | Entrega |
|------|---------|
| 0 | Discovery completo de FILE_MAP/EXERCISE_INDEX/material-block linkage atual |
| 1 | Material agnostic data model — função `get_materials_by_block(manifest, timeline, curations) -> dict[block_id, list[Material]]` |
| 2 | Renderer `cronograma_detalhado_md()` agregando todos materiais por block |
| 3 | Extensão de auto-block-match pra PDFs/imagens/exercícios (heurística + concept-match) |
| 4 | UI: aba "Cronograma Detalhado" mostrando aula-por-aula com edição inline de atribuição |
| 5 | Verificação: CRONOGRAMA_HEALTH.md (cobertura material-bloco, órfãos, blocks ricos vs pobres) |

## Anti-objetivos

- NÃO substituir FILE_MAP, CODE_INDEX existentes (eles seguem servindo categoria/unit lookups)
- NÃO criar duplicação de dados — `CRONOGRAMA_DETALHADO.md` é **render derivado**, não fonte
- NÃO forçar Gemini em todo material (PDFs já têm título, talvez basta heurística)
- NÃO atrasar a entrega do `code-summarization-gemini.md` discutindo isso

## Trigger pra iniciar

Quando code-summarization estiver em produção há **2+ semanas sem regressão**, e você sentir que respostas do tutor pra "o que vimos hoje?" ainda estão fracas, abrir este plano.
