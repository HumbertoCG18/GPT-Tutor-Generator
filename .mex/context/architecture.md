---
name: architecture
description: APOSENTADO (2026-08-06) — estrutura do código vive no graphify; este stub só preserva os edges do MEX
last_updated: 2026-09-10
---

# Architecture — aposentado

Conteúdo removido na dieta MEX de 2026-08-06 (era inventário estrutural de junho:
componentes, contagens de arquivos, entry-points — tudo coberto melhor e sempre-fresco
pelo grafo de código).

- **Estrutura** (quem chama quem, onde símbolo vive, mapa de módulos): `graphify query
  "<pergunta>"`, `graphify path "<A>" "<B>"`, `graphify explain "<conceito>"`; visão ampla
  em `graphify-out/GRAPH_REPORT.md`.
- **Invariantes e porquês** de arquitetura: `.mex/context/decisions.md` + non-negotiables em
  `AGENTS.md` (ex.: `engine.py` é façade — lógica nova vai no subpacote correto).
- **Fluxo do produto** (import→process→curadoria→build): `README.md` do projeto.

## De onde a taxonomia vem (medido em 07/09)

`src/builder/extraction/content_taxonomy.py` (`build_content_taxonomy`) monta a taxonomia de tres fontes, e só três:

- **tópicos**: `parse_units_from_teaching_plan` sobre o plano de ensino (fallback COURSE_MAP).
- **aliases 1**: `_glossary_aliases_for_topic` sobre o `<repo-tutor>/GLOSSARY.md`, cujos sinônimos vêm do sidecar
  `<repo-tutor>/course/.glossary_curation.json`.
- **aliases 2**: `collect_strong_heading_candidates`, os headings dos próprios materiais.

**O SARC e o Moodle não entram na taxonomia.** Os labels de sessão do cronograma alimentam só o alinhamento
bloco→unidade (`src/builder/timeline/unit_matcher.py`, `assign_units_positional`); título, label e seção do Moodle entram como sinal no
scorer de entrada e na regra S1b, nunca como alias. O único canal de vocabulário concreto é o sidecar.

Teto medido de cada fonte contra 222 materiais com gold (`docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.log`): o rótulo literal do
plano alcança o subtópico certo em 12% dos materiais, título e label do Moodle em 42%, o label da sessão do SARC em
40%, os headings do material em 37%. Plano, SARC e Moodle juntos chegam a 62%, e 22% dos materiais não são alcançáveis
por fonte nenhuma do professor. O plano de ensino é a fonte mais fraca: ele nomeia a categoria, o material nomeia o
objeto.
