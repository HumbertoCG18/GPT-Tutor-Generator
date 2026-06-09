# Design: Escopo de prova por data + cores SARC (timeline)

last_updated: 2026-06-08
status: implementado

## Problema

Provas e revisão vêm do cronograma SARC (HTML, exportado em ASP.NET) como blocos
do timeline, sem escopo de unidade declarado. Hoje:

- Escopo de prova só vem do **plano de ensino** (seção AVALIAÇÃO); para SARC fica vazio.
- **PS e G2** caem em cores de exclusão → kind `"ps"`/`"g2"` em `_IGNORED_KINDS` →
  não viram ASSESSMENT (são tratados como ruído administrativo).
- Sem escopo, a prova ou fica sem conteúdo ou (se mis-classificada) tenta unidade.

Sabemos o escopo: P1 = tudo antes da data da P1; PN = entre P(N-1) e PN; **PS e G2 =
semestre inteiro**. E a **cor da linha SARC é o guia autoritativo** do tipo.

## Decisões (do usuário)

1. **Cores SARC = guia autoritativo do tipo** (combinado com a coluna Atividade):
   | Cor | Tipo | Escopo |
   |-----|------|--------|
   | `#FFA500` / orange | Prova regular (P1,P2,P3…) | janela de data |
   | `#FF8C00` / darkorange | PS (substitutiva) | **semestre inteiro** |
   | `LightGrey` / `#D3D3D3` | **G2** ou **Devolução de provas** | G2 → semestre inteiro; Devolução → results |
   | `#FFFF00` / yellow | Trabalho | deliverable |
   | `Red` / `#FF0000` | Suspensão de aula | suspended |
   | `#8B0000` / darkred | Evento acadêmico | academic_event |
2. **Janela** da prova regular: da prova anterior (exclusivo) até esta (inclusivo).
   P1 = início → data P1; PN = data P(N-1) → data PN.
3. **PS e G2 = SEMPRE o semestre inteiro** (todas as unidades da matéria).
4. **Escopo por data é FALLBACK**: unidades declaradas no plano de ensino vencem;
   senão deriva por data/cor.
5. **Revisão**: `kind=REVIEW`. Exercício de revisão é **sempre a linha imediatamente
   anterior a uma prova** pela sequência (coluna `#` do SARC: se P2 é #36, a revisão
   é #35). A revisão **herda o escopo da prova que ela precede** (a P2, no exemplo).
   Implementação: liga a revisão à **próxima prova (bloco ASSESSMENT) em ordem
   cronológica/sequência de blocos** — o parser processa as linhas em ordem e
   provas/revisão são blocos standalone, então a ordem dos blocos preserva o `#`.
   (Não threadar o `#` cru pelo round-trip do markdown; usar a ordem dos blocos.)

## Estado atual (relevante)

- `helpers._ASPNET_COLOR_KIND_MAP`: já mapeia as cores, mas PS→`("ps",True)` e
  G2(lightgrey)→`("g2",True)` com `ignored=True` (exclusão). `#ffa500`→assessment.
- `helpers._aspnet_row_canonical_kind`: cor de exclusão vence Atividade.
- O kind da linha SARC é embutido no SYLLABUS.md como `{kind=...}` e relido por
  `index._build_timeline_candidate_rows` (`_KIND_TOKEN_RE`). `_IGNORED_KINDS =
  {"suspension","g2","ps","event"}`.
- `index._canonical_assessment_label`: P\d→`PN`, pf→`PF`. **Não reconhece PS/G2.**
- `finalize_block`: kind≠CLASS → `unit_slug=""`. ASSESSMENT exige `topic=True`.

## Componentes

### 1. Cores: promover PS/G2 a assessment (helpers.py)

- `_ASPNET_COLOR_KIND_MAP`: mudar PS (`#ff8c00`/`darkorange`) e G2 (`lightgrey`/
  `#d3d3d3`) de `ignored=True` para um kind de avaliação **full-scope**.
  Introduzir kinds canônicos `assessment` (regular) e distinguir variante full via
  um campo separado (não um BlockKind novo): a linha carrega
  `assessment_variant ∈ {"regular","full"}`.
- LightGrey é ambíguo: se a Atividade contém "devolu" (devolução/devolutiva) →
  `results` (excluído de escopo); senão → G2 (`assessment`, variante `full`).
- PS (`#ff8c00`): sempre `assessment` variante `full`.
- `#ffa500`: `assessment` variante `regular`.
- Manter `Red`→suspended, `#8b0000`→academic_event, `#ffff00`→deliverable.
- `ATIVIDADE_KIND_MAP`: adicionar reconhecimento de `ps`, `g2` (texto) → assessment.

A variante (`regular`/`full`) é propagada pro timeline via o token do SYLLABUS
(ex.: `{kind=assessment}` + `{scope=full}` ou um token único `{kind=assessment_full}`)
e relida em `_build_timeline_candidate_rows`. Detalhe do token no plano.

### 2. Rótulo canônico (index.py)

`_canonical_assessment_label`: reconhecer `PS` e `G2` (além de `PN`/`PF`/`EXAME`).

### 3. Helper puro de escopo por data

`assessment_scope_by_date(assessment_blocks, class_blocks, all_unit_slugs) -> {block_id: [unit_slug]}`:
- Exames regulares (variante `regular`, P1..PN) ordenados por `period_start`.
- Pk: janela = (data P(k-1) exclusiva, data Pk]; P1 = (−∞, data P1]. Escopo =
  `unit_slug` distintos dos blocos CLASS com `period_start` na janela.
- Variante `full` (PS, G2) → escopo = `all_unit_slugs` (semestre inteiro).
- Reutiliza `_parse_timeline_date_value`, `_canonical_assessment_label`.

### 4. Integração (fallback + saída)

Onde os blocos finais existem com datas/unidades (após `_serialize_timeline_index`):
para cada bloco ASSESSMENT:
- Se `_build_assessment_context` tem `declared_unit_slugs` p/ o mesmo rótulo →
  usa as declaradas (precedência do plano de ensino).
- Senão → `assessment_scope_by_date`.
- Grava no bloco: `scope_unit_slugs: [...]` + `primary_topic_label` legível
  (ex.: "Conteúdo até a P1: …" / "Semestre inteiro") satisfazendo `topic=True`.
- Revisão (`REVIEW`): herda `scope_unit_slugs` da **próxima prova** (bloco
  ASSESSMENT seguinte em ordem cronológica/sequência). Sem prova seguinte → vazio + log.

### 5. Consumo

`scope_unit_slugs` é lido por quem monta o gabarito/contexto do tutor; a prova
referencia o conjunto de unidades do seu escopo (não uma unidade única). Wiring
detalhado no plano.

## Erros e bordas

- Prova sem `period_start` → sem escopo por data; mantém vazio + log.
- Sem CLASS na janela → escopo vazio (prova antes de qualquer aula); log.
- LightGrey sem Atividade clara → trata como G2 (full) por padrão; "devolu" → results.
- `block_manual_unit_slug` preservado.
- Idempotente.

## Testes

- Cores: `_aspnet_row_canonical_kind` → PS→assessment/full; G2(lightgrey,sem devolu)
  →assessment/full; lightgrey+"devolução"→results; #ffa500→assessment/regular;
  #ffff00→deliverable; red→suspended; #8b0000→academic_event.
- `_canonical_assessment_label`: "Prova PS"→PS, "Prova G2"→G2, "P2"→P2, "PF"→PF.
- `assessment_scope_by_date`: 3 exames + CLASS datados → P1 só antes de P1; P2 entre
  P1 e P2; PS e G2 = todas as unidades.
- Fallback: declared_unit_slugs presentes → usa declaradas.
- Bordas: prova sem data → vazio; sem CLASS na janela → vazio.
- Revisão: REVIEW herda o escopo da próxima prova (bloco ASSESSMENT seguinte);
  ex.: revisão antes da P2 → escopo da P2. Sem prova seguinte → vazio.

## Fora de escopo (YAGNI)

- Refatorar a UI do cronograma (vem depois).
- Escopo por sub-unidade/tópico fino — só unidades.
- Novo BlockKind p/ PS/G2 (usam ASSESSMENT + `assessment_variant`).
- Detecção de conflito data×unidade (já existe em `_build_assessment_context`).
