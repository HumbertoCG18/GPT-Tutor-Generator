# Régua CG — proposta de adjudicação dos 5 casos (23/09/2026, sem aplicar)

**Status: proposta para decisão do usuário.** Nenhum CSV da régua foi alterado. A régua v2 (22/09) e a cópia histórica
(`c1-3/regua_historica_22-09/`) ficam como estão. Se aprovada, a correção sai como **versão separada** da régua do CG,
com a baseline reavaliada nela e reportada à parte. Mudança de anotação não conta como ganho do algoritmo, e o 86/251
da base v2 continua sendo o resultado observado sob a régua v2.

## Método

- Fontes: conteúdo de cada material (markdown extraído do PDF/HTML; código-fonte dos `.zip` lido direto do
  `raw/zip/`), rótulo do Moodle, seção do Moodle e cronograma SARC do professor (`course/SYLLABUS.md`), e a taxonomia
  do plano de ensino (`course/.content_taxonomy.json` da base `.frzero/wv_importacao_22-09/Computacao-Grafica-Tutor`).
- **A leitura não foi cega às previsões do motor.** As CSVs da régua trazem as colunas `pred_unit`/`pred_subunit`, e os
  valores dos cinco materiais apareceram na leitura (`desenho-de-linhas`, `2d-3d-mao-direita-e-mao-esquerda`,
  `sistema-de-coordenadas-cartesianas`, todas da u04, e unidade u04). A decisão proposta usa só as fontes e a taxonomia
  listadas acima e não cita essas colunas, mas houve exposição a elas.
- A unidade segue a decisão do usuário de 22/09 (régua v2: u05 "pelo conteúdo"). Esta proposta só trata da subunidade e
  da coerência da coluna `unit_slug` do `subunit_gt_CG.csv`.

## Fatos das fontes que valem para os cinco

- Os cinco estão na seção do Moodle "6 - Processo de Visualização 2D". No cronograma, a aula 7 (25/08) é "Processo de
  Visualização 2D - Instanciamento" e a aula 8 (27/08) é "Recorte e mapeamento".
- O material `vis2d` do professor define o processo de visualização 2D em três etapas: **instanciamento, recorte e
  mapeamento**. Instanciamento é "criar cópias de um modelo, alterando em cada uma as propriedades necessárias", o que se
  faz com transformações geométricas.
- Na taxonomia, a u04 (Processo de Visualização 2D) não tem tópico de transformação. A u05 tem 5.1 "Transformações
  Geométricas e coordenadas homogêneas 2D", 5.3 "Pipeline de visualização 2D" e 5.4 "Composição de transformações 2D".
  A u07 tem 7.2.4 "Instanciamento de Primitivas" sob 7.2 "Técnicas de Modelagem 3D".
- O 7.2.4 é outro conceito: técnica de modelagem 3D por primitivas parametrizadas, dada em outra unidade. A coincidência
  com estes materiais é só a palavra "instanciamento". Os cinco são programas e páginas **2D** da etapa de
  instanciamento do processo de visualização 2D. Proposta: não usar 7.2.4 em nenhum deles.
- Inconsistência de migração nas cinco linhas: `subunit_gt_CG.csv` ainda diz `unidade-04-processo-de-visualizacao-2d`,
  enquanto `material_gt_CG.csv` (v2) diz u05. Proposta: alinhar para u05 na versão corrigida.

## Decisão proposta por material

| material | evidência (fonte) | primário proposto | aceitos | confiança |
|---|---|---|---|---|
| `instanciamento` (PDF, 13 mil caracteres) | "Processo de Visualização Bidimensional — INSTANCIAMENTO"; seções 3 "Transformações geométricas", 3.1–3.3 translação/escala/rotação, 3.4 matrizes, 3.5 "Combinação das Transformações", 3.6 "Coordenadas Homogêneas", 3.7 comutatividade | 5.1 | 5.4 (3.5 e 3.7); 5.3 (o material é a etapa de instanciamento do processo 2D) | alta no primário |
| `transformacoesgl` (HTML, 3,6 mil caracteres) | "Transformações Geométricas em OpenGL": translação, rotação, escala; "as transformações são cumulativas", matriz interna | 5.1 | 5.4 (acumulação = composição) | alta no primário |
| `transformacoesgeometricas` (zip; rótulo "Exemplo de Código para Instanciamento") | `ModelagemDePersonagens.cpp`, `ModelagemDePersonagensComInstancia.cpp`; 29 `glPushMatrix`, 22 `glTranslate`, 15 `glScale`, 10 `glRotate`: instâncias de um modelo montadas por transformações aninhadas | 5.4 | 5.1; 5.3 | média (5.4 × 5.1 no primário) |
| `pagina-com-videos-sobre-instanciamento` (HTML com código) | página de vídeos sobre instanciamento; código com `Modelo`, `Temporizador`, 6 `glPushMatrix`, `glTranslate`/`glRotate`/`glScale` | 5.4 | 5.1; 5.3 | média (5.4 × 5.1 no primário) |
| `animacao-v2` (zip; rótulo "Exemplo de Código para Animação") | animação de instâncias com `Temporizador` (20), "anima" (30), `glTranslate`/`glRotate`; o assunto principal é animação | **vazio** (mantido) | nenhum | média: o plano não tem tópico de animação; alternativa seria 5.4 como técnica usada |

Critério aplicado nos dois de confiança média: o primário é o assunto que o material demonstra (instâncias montadas por
transformações aninhadas, isto é, composição), e a transformação isolada (5.1) fica como aceita. Se o usuário preferir
"a técnica-base primeiro", o primário vira 5.1 e 5.4 passa a aceito; nos dois sentidos 7.2.4 fica fora.

## O que muda se aprovado (versão separada, não aplicada)

1. Nova versão do `subunit_gt_CG.csv` com as 5 linhas: `unit_slug` = u05, `gold_subunit`/`gold_subunits_extra`
   conforme a tabela, `gold_fonte` = conteúdo + seção/cronograma e nota de adjudicação datada. Cópia da v2 em pasta
   histórica.
2. Baseline reavaliada sob a nova versão e reportada separadamente: placar v2 e placar da versão corrigida lado a lado,
   com a diferença atribuída à anotação e não ao motor.
3. Nenhuma regra, peso ou alias do motor muda por causa desta adjudicação.
