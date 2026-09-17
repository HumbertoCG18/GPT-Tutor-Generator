# Verificação: prova matemática versus avaliação

Teste autorizado em 15/09, somente em memória. Nenhuma correção em src ou
regravação dos tutores. Referência: pacote_fontes_15-09, 338 entradas em sete
cursos. Objetivo: conferir se a distinção recupera os três blocos de MF sem
alterar avaliações reais nem os demais materiais.

## Hipótese e regra experimental

A categoria provas já vinha do importador para os três arquivos
ProvasIndutivas_EspecificaçõesRecursivas, incluindo Arvores e Listas. Conteúdo
inspecionado: princípio de indução, indução estrutural, propriedades de árvores
e listas; não avaliações acadêmicas. A heurística atual em helpers.py:682 casa
a substring prova. O replay anterior já demonstrou categoria provas →
lexical=False → abstenção quando a janela tem vários blocos.

Regra candidata, confinada ao script: se a classificação original é provas e
o nome contém prova(s) indutiva(s) ou prova(s) por indução, classificar como
material-de-aula. Normalizar acentos e separadores; preservar a classificação
quando existe marcador explícito P1/P2/P3, AV1/AV2, exame, test, avaliação ou
Prova 1/2/3. Não usar IDs do gold nem nomes de curso na regra. Não habilitar
lexical globalmente e não alterar regras de prazo/avaliações do motor.

O classificador recebe o nome realmente usado no import: nome Moodle do sidecar,
quando disponível, mais nome do arquivo. As frases do plano são reconstruídas
do mesmo perfil salvo. Reproduzidas as categorias originais dos 338 inputs antes
da regra candidata. Nenhum nome de seção ampla usado para reclassificar arquivos.

## Resultado medido

| Medida | Antes | Depois | Ganhos | Perdas |
|---|---:|---:|---:|---:|
| Blocos MF | 50/66 | 53/66 | 3 | 0 |
| Blocos, sete cursos | 210/237 | 213/237 | 3 | 0 |
| Outros materiais com temporal alterado | 0 | 0 de 335 | 0 | 0 |

Três arquivos matemáticos passaram de sem bloco para bloco05, o gold existente.
Denominador fixo, sem excluir ausentes. Controle sem intervenção reproduziu os
campos temporal_* das 338 entradas. A regra mudou somente três categorias.
Os dois replays finais produziram JSONs idênticos.

Unidades, subtemas, FILE_MAP e build completo não foram reavaliados: campos
computed_* existentes não são evidência de invariância após reconstrução.
213/237 é resultado de replay temporal, não novo snapshot de produção.

## Controles e limites

- Quatro entradas de avaliações reais de IA, três PDFs distintos por SHA256:
  p2-202401, p2-202402, prova-1-2024-02, prova-1-202402. Corpo inspecionado:
  campo Nome, identificação P1/P2 e questões pontuadas. Categoria e todos os
  campos temporais preservados; invariância não afirma que o bloco anterior
  desses materiais estava correto.
- Outros 14 controles ligados a avaliações: listas de revisão e resoluções de
  MF/SO/ES2/TCC/CG. Categoria e temporal preservados. Mais uma imagem do FR
  classificada fotos-de-prova também preservada; isso não valida essa categoria.
- Seis nomes sintéticos, claramente separados dos documentos reais: prefixos
  P1 - e Prova 1 - aplicados aos três nomes matemáticos. Todos continuam provas.
  Proveniência do contrato: auto_detect_category recebe str; nomes-base vêm de
  _inputs_15-09.json; marcadores conferidos nas avaliações reais de IA. Esses
  casos testam o conflito avaliação + assunto matemático, não ampliam o corpus.
- 56 hashes de manifests e JSONs de course conferidos antes/depois, sem mudanças.
  Zero chamadas de rede/LLM registradas; rede bloqueada no processo de teste,
  voter=None. Nenhum processo permaneceu em execução.

Há somente três positivos matemáticos, todos conhecidos antes de definir a
regra; não existe holdout matemático independente nesta medição. Marcadores
adicionais previstos na regra, além dos seis casos sintéticos, não receberam
validação equivalente. Não chamar a heurística de classificador geral validado.
Nenhum MD Datalab foi substituído: este teste atua no nome de importação, não na
precedência de metadados documentais.

## Reprodução e verificação

Scripts e resultados em docs/reports/_harness-2026-09-04/c1-3:

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/verifica_categoria_prova_15-09.py
python -B docs/reports/_harness-2026-09-04/c1-3/verifica_categoria_prova_15-09.py --saida verificacao_categoria_prova_repetida_15-09.json
python -m ruff check docs/reports/_harness-2026-09-04/c1-3/verifica_categoria_prova_15-09.py
```

Saída padrão: verificacao_categoria_prova_verificada_15-09.json. Arquivos já
existentes são recusados; para outra execução escolher nome novo com _15-09.
Resultado preliminar verificacao_categoria_prova_15-09.json preservado. Ruff
identificou B023 no reprodutor inicial; função de replay extraída do loop,
Ruff passou e ambas as execuções finais foram repetidas após a mudança.

Skills systematic-debugging/eval-harness orientaram isolamento de uma variável,
controle real e separação de resultado temporal de validação completa. Graphify
explain/path confirmou a chamada scan_stash_cards → auto_detect_category; aviso
de skill0.9.42/package0.9.5 declarado, fonte atual conferida diretamente. Sem
rebuild semântico do grafo, agentes, chamadas externas, commit ou push.

Conclusão: distinção restrita é viável no replay e preservou os controles
medidos. Antes de promover: reconstrução em cópia com a categoria corrigida
na entrada, conferindo também unidades/subtemas e artefatos. Src permanece
intocado nesta etapa; a régua original continua com os sete cursos.
