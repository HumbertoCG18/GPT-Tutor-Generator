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
  - horario
edges:
  - target: context/architecture.md
    condition: quando precisar de como os componentes processam estas fontes
  - target: context/repo-output.md
    condition: quando o foco é o formato do repo gerado
last_updated: 2026-06-17
---

# Contexto Institucional

Por que existe: o sistema de atribuição importa de plataformas reais da PUCRS. Confundir
o papel de cada uma leva a diagnóstico errado (ex.: tratar SARC como "cadeira"). Este
arquivo fixa o que cada plataforma é, o que fornece, e como entra no pipeline de
atribuição (arquivo→bloco→unidade/subunidade).

## Faculdade

- **PUCRS**, Escola Politécnica (ex-**FACIN** = Faculdade de Informática — nome antigo que
  ainda aparece em títulos de páginas legadas, ex.: SARC).

## Plataformas-fonte (alimentam o pipeline)

### Plano de Ensino (gerenciador de cadeiras)
- **SEMPRE importado** ao criar matéria nova; **todas as cadeiras atuais têm** o plano.
  Premissa forte do pipeline.
- **SEMPRE** hierarquia explícita unidade→tópico. **Nunca** cadeira de 1 unidade →
  `m >= 2` garantido. Nº de unidades varia por professor (uns condensam, outros espalham
  subunidades).
- Papel no código: fonte das **unidades/tópicos** (taxonomia). Vira `content_taxonomy`
  (`build_file_map_content_taxonomy_from_course`) E `unit_index`
  (`build_file_map_unit_index_from_course`), ambos via `parse_units_from_teaching_plan`.

### OpenSARC — cronograma (fonte real do timeline)
- Repo: https://github.com/mflash/OpenSARC (ASP.NET). SARC = Sistema de Alocação de
  Recursos Computacionais (labs/salas/equipamentos + solicitação no planejamento semestral).
- **O cronograma que o sistema parseia É uma EXPORTAÇÃO do OpenSARC**, não um sistema à
  parte. URL: `https://sarc.pucrs.br/Default/Export.aspx?id=<GUID>&ano=2026&sem=1`.
  - `id` = GUID de uma **TURMA** específica (não a matéria genérica; ex.: turma 01 de
    Métodos Formais). `idturma = new Guid(Request.QueryString["id"])`.
  - `ano`/`sem` → carrega o calendário acadêmico do período
    (`GetCalendarioByAnoSemestre`): início de aulas, feriados, período de provas (G2).
  - Monta a tabela via `AulaBO.GetAulas(idturma)`: **1 linha por encontro**. Colunas: nº
    aula · dia da semana · data · horário · **descrição da atividade** · **tipo de
    atividade** · **recursos alocados** (sala/lab).
  - Coluna "Recursos" = `alocBO.GetRecursoAlocadoByAula(...)` (a parte de alocação do SARC).
- **Reconciliação com o código:** o parser SARC ASP.NET (a DataGrid `dgAulas`, coluna
  "Atividade" + cor da linha → kind do bloco; `_aspnet_row_canonical_kind`/`ATIVIDADE_KIND_MAP`)
  lê exatamente essa tabela do `Export.aspx`. O "tipo de atividade" da coluna É o sinal de
  kind (aula/prova/feriado/apresentação).
- Variações na mesma pasta: `&prox=1` (só a próxima atividade, contagem natural-language);
  `ExportIcal.aspx` (iCal p/ Google Calendar/Outlook); `ExportPlan.aspx`.
- **Códigos de período PUCRS (2 letras) → horário real, +90 min de duração:**
  `AB`=08:00 · `CD`=09:45 · `EX`=11:30 · `FG`=14:00 · `HI`=15:45 · `JK`=17:30 · `LM`=19:15
  · `NP`=21:00. Ex.: "QUA LM" = quarta-feira 19:15.
- **Valores reais da coluna Atividade** (vistos): `Aula`, `Trabalho`, `Prova`, `Prova de
  Substituição`, `Prova de G2`, `Evento Academico`.
- **Kind = Atividade + COR da linha, e a cor de EXCLUSÃO vence a coluna Atividade.** O
  professor às vezes deixa "Aula" na coluna mas marca o tipo real pela cor. Ex. concreto
  (03/04/2026, cronograma da turma `9b679f12-...`): Atividade="Aula", Descrição="Feriado",
  **linha inteira vermelha** = suspensão. O código resolve certo: `_aspnet_row_canonical_kind`
  (helpers.py) checa a cor primeiro — `red`/`#ff0000` → `(suspension, ignored=True)` vence o
  "Aula". Demais cores (helpers.py `COLOR_MAP`): lightgrey=G2/devolução, orange=assessment,
  darkred=evento, yellow=deliverable.
- **Descrição traz o TÓPICO/conteúdo da aula** ("Lógica de Hoare", "Máquinas de Turing"),
  não só "Aula expositiva". Logo o bloco→unidade pode confiar no texto do cronograma
  (`topic_text` do bloco vem da Descrição) — o matcher posicional tem sinal real, e
  afinidade-zero é rara.
- **Avaliações (PUCRS Politécnica):** `P1` (Prova 1), `P2` (Prova 2), `P3` (Prova 3), `PS`
  (Prova Substituta), `G2` (prova de recuperação). Não há PF aqui (G2 = recuperação). Todas
  aparecem na Atividade com "Prova" → casam `assessment` via `ATIVIDADE_KIND_MAP`.

- **Import na app (desde `939e483`):** o `HTMLImportDialog` aceita só a **URL do SARC**
  (auto-fetch via `fetch_schedule_html` → `parse_html_schedule` → `_parse_aspnet_schedule`,
  que lê a tabela `dgAulas`). O campo de paste de HTML foi removido da UI; o backend de
  parse de HTML colado segue existindo como fallback, não exposto. (Decisão: "manter scraper
  + só link" — link e paste sempre usaram o MESMO scraper; o link só auto-busca o HTML.)

### OpenSARC — Consulta.aspx (NÃO é fonte; página read-only do aluno)
- Página do aluno: `Consulta.aspx` (título legado "Sistema de Alocação de Recursos -
  FACIN"). Consulta por data → tabela Recurso · Disciplina/Evento · Curso · Responsável,
  com blocos "atual" e "próximo". Responde "em qual lab minha aula é hoje?". Quem aloca =
  prof/secretaria/admin; o aluno só consulta. **Não é fonte de conteúdo nem de cronograma**
  (o cronograma vem do `Export.aspx` acima).

### Moodle (LMS)
- Fonte dos **materiais** (PDFs, links, código, imagens) + estrutura de seções/cards.
- Entra como: `source_section` (seção Moodle), `card_block_map` (datas dos cards → blocos,
  `derive_card_block_map`), labels temporais formatos A–D (`moodle_labels.py`, cf.
  `docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md`). Códigos de cadeira aparecem
  aqui.
- **Nomenclatura dos cards é HETEROGÊNEA (depende do professor)** — não há esquema único:
  - por **semana** ("Semana N");
  - pelo **título principal da unidade** (pode divergir do nome no Plano de Ensino → ver
    Hipóteses);
  - por **tipo de conteúdo** em card separado: Exercícios/Listas, Revisões de prova, ou
    **TDE** (Trabalho Discente Efetivo — exercícios dados em aula entram no card de TDE).
  Consequência: o match `source_section`→unidade/bloco NÃO pode assumir nome=unidade; tem
  que tolerar card por-semana, por-tipo-de-conteúdo e por-título-divergente.

### Microsoft 365
- Fonte de material/seção (`m365.py` → `source_section`).

## Plataformas de consulta (não-fonte de conteúdo)

- **Portal do aluno**: calendário acadêmico, info acadêmica/financeira, acessos a sistemas.
- **Minha Biblioteca E-Books PUCRS**: e-books.

## Mapa fonte → pipeline de atribuição

| Fonte | Fornece | Onde entra no código |
|---|---|---|
| Plano de Ensino | unidades + tópicos (taxonomia) | `content_taxonomy`, `unit_index` |
| OpenSARC `Export.aspx` | cronograma: blocos + datas + kind (tipo de atividade) + recursos | `_parse_syllabus_timeline`, `_aspnet_row_canonical_kind`, `_build_timeline_index` |
| Moodle | materiais + seções + datas de card | `source_section`, `card_block_map`, `moodle_labels` |
| Microsoft 365 | materiais + seção | `m365.py` (`source_section`) |

## Convenções de identidade

- Semestre = `[Ano]/[Semestre]` (1 ano = 2 semestres), ex.: `2026/1`.
- Códigos de cadeira aparecem no Moodle.
- Turma do cronograma é identificada por GUID no SARC (não pelo nome da matéria).

## Hipóteses / problemas conhecidos (atribuição)

- **Nome da unidade × nome do card Moodle divergem** (teoria do usuário): às vezes a unidade
  do Plano de Ensino e o card/seção do Moodle são o MESMO conceito escrito diferente pelo
  professor → o match léxico falha onde deveria casar. Candidato a melhoria futura (match
  fuzzy unidade↔card, ou alias de unidade). Relacionado a `source_section`/`card_block_map`
  e ao scorer unidade.
- **"Evento Academico" no `ATIVIDADE_KIND_MAP` — RESOLVIDO (`939e483`):** antes não casava
  keyword → caía em `class` (aula) quando a linha SARC não tinha cor de exclusão. Agora
  `evento → event` (kind ignorado, igual ao evento marcado por cor darkred) → vira ignored
  → bloco administrative_only → fora da atribuição.

## Consequência para o sistema de atribuição

- Plano sempre presente + **`m >= 2` sempre** (nunca 1 unidade) → as duas fontes de unidade
  (`content_taxonomy.units` e `unit_index`) têm a mesma contagem e o matcher posicional
  (`assign_units_positional`) está **sempre alimentado com m>=2**. O retorno `[]` por `m<2`
  é **inalcançável** em produção.
- Logo o fallback keyword de unidade (P1.4: `_assign_timeline_block_to_unit` +
  `_vote_unit_from_topic_candidates` + `_score_timeline_row_against_unit`, no `else` de
  `index.py:2205`) é reachable só por **afinidade-zero** (m>=2 mas zero token-overlap) ou
  `n==0` (sem blocos-aula → laço vazio, no-op). O caso `_derive_unit_specs_from_repo`
  (fallback de `unit_index` sem plano) fica **latente** — não exercitado, pois plano sempre
  existe.
- Resíduo a tratar antes de deletar o fallback: a afinidade-zero, onde o scorer frágil
  ainda capta sinais que o posicional não tem (nº explícito de unidade "Unidade N",
  frases/âncoras). Fold desses sinais no posicional → deleção segura.
