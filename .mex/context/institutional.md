---
name: institutional
description: Contexto institucional (faculdade, plataformas-fonte e papéis) que alimenta o sistema de atribuição
triggers:
  - faculdade
  - plataforma
  - moodle
  - sarc
  - opensarc
  - plano de ensino
  - cronograma
  - source_section
edges:
  - target: context/architecture.md
    condition: quando precisar de como os componentes processam estas fontes
  - target: context/repo-output.md
    condition: quando o foco é o formato do repo gerado
last_updated: 2026-06-17
---

# Contexto Institucional

Por que existe: o sistema de atribuição importa de plataformas reais da faculdade.
Confundir o papel de cada uma leva a diagnóstico errado (ex.: tratar SARC como
"cadeira"). Este arquivo fixa o que cada plataforma é, o que ela fornece, e como entra
no pipeline de atribuição (arquivo→bloco→unidade/subunidade).

## Faculdade

- Escola Politécnica da PUCRS (ex-**FACIN** = Faculdade de Informática — nome antigo que
  ainda aparece em títulos de páginas legadas, ex.: SARC). _Confirmar: universidade =
  PUCRS._

## Plataformas-fonte

### Plano de Ensino (gerenciador de cadeiras)
- **SEMPRE importado** ao criar uma matéria nova; **todas as cadeiras atuais têm** o
  plano no gerenciador. Premissa forte do pipeline.
- Papel no código: fonte das **unidades/tópicos** (taxonomia). Vira `content_taxonomy`
  (`build_file_map_content_taxonomy_from_course`) E `unit_index`
  (`build_file_map_unit_index_from_course`), ambos via `parse_units_from_teaching_plan`.
- Consequência de atribuição: como o plano sempre existe, as duas fontes de unidade têm a
  mesma contagem e o matcher posicional (`assign_units_positional`) está sempre alimentado.
  O caminho `_derive_unit_specs_from_repo` (fallback de `unit_index` quando NÃO há plano)
  fica latente — não exercitado no caminho normal. (Relevante ao P1.4: o fallback keyword
  de unidade só seria load-bearing sem plano, cenário que não ocorre em produção.)

### Moodle (LMS)
- Papel: **materiais** da disciplina (PDFs, links, código, imagens) + estrutura de
  seções/cards.
- Entra no pipeline como: `source_section` (seção Moodle do material), `card_block_map`
  (datas dos cards → blocos via `derive_card_block_map`), e labels temporais nos formatos
  A–D (`moodle_labels.py`, cf. `docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md`).

### OpenSARC / SARC
- Repo: https://github.com/mflash/OpenSARC (ASP.NET).
- O que é: sistema de **alocação de recursos computacionais** (labs/salas/equipamentos) +
  solicitação de recursos no planejamento semestral. Para o **aluno é READ-ONLY**: consulta
  de em qual lab/sala/auditório a aula acontece. Quem aloca = professores/secretaria/admin;
  o aluno só consulta.
- Página do aluno: **`Consulta.aspx`** (título legado "Sistema de Alocação de Recursos -
  FACIN"). Informa uma data (seletor de calendário, campo opcional) → "Visualizar
  Alocações" → tabela por data com colunas **Recurso · Disciplina/Evento · Curso ·
  Responsável**. Renderiza dois blocos: "atual" e "próximo" (o que ocupa o recurso agora e
  o que vem em seguida).
- Uso real do aluno: "em qual lab minha disciplina é hoje?", "esse lab está ocupado?",
  "que evento está nessa sala nessa data?". É um quadro de ocupação de espaços, por data.
- Conexão com o cronograma: via a coluna **"Recursos"** do cronograma.
- NÃO é uma cadeira/disciplina. NÃO é fonte de conteúdo pedagógico.

## Mapa fonte → pipeline de atribuição

| Fonte | Fornece | Onde entra no código |
|---|---|---|
| Plano de Ensino | unidades + tópicos (taxonomia) | `content_taxonomy`, `unit_index` |
| Cronograma | blocos + datas + kind | `_parse_syllabus_timeline`, `_build_timeline_index` |
| Moodle | materiais + seções + datas de card | `source_section`, `card_block_map`, `moodle_labels` |
| SARC | alocação de sala/recurso (read-only) | coluna "Recursos" do cronograma |

## A confirmar (perguntas abertas)

1. **Origem do cronograma**: de onde vem o cronograma de uma cadeira típica? Faz parte do
   Plano de Ensino, é um recurso à parte no Moodle, é exportado do SARC, ou colado manual?
2. **SARC `dgAulas` vs `Consulta.aspx`**: o código tem parser de cronograma SARC ASP.NET
   (`dgAulas`, coluna "Atividade" + cor da linha → kind do bloco). Isso é uma página
   DIFERENTE da `Consulta.aspx` do aluno (grade de alocação de prof/admin)? O aluno tem
   acesso a essa página, ou o cronograma com "Atividade" vem de outro lugar?
3. **Estrutura do Plano de Ensino**: tem sempre hierarquia explícita unidade→tópico
   ("Unidade 1: ...")? Quantas unidades, tipicamente (≥2 sempre, ou existe cadeira de 1
   unidade)?
4. **Outras plataformas**: além de Moodle, SARC e gerenciador de cadeiras, há portal
   acadêmico oficial (notas/matrícula) que seja fonte de algum dado?
5. **Convenções de identidade**: formato de semestre (ex.: `2026/1`), código de cadeira,
   convenção de nome de unidade — relevante a id/`source_section`.
