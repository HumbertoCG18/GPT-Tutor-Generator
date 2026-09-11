**A proposta serve para adjudicação; ainda não sustenta “85 acertos e 8 erros” como resultado definitivo.** MEDIDO: o CSV inclui pendências na pontuação.

Referência **S**: [monta_material_gt_CG.py](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/monta_material_gt_CG.py). MEDIDO abaixo distingue recálculo local de confronto com os trechos fornecidos; HIPÓTESE identifica julgamento proposto.

1. **Seção → unidade.** HIPÓTESE: manter os mapeamentos abaixo. Seção 13 sustenta u06 como contexto, mas “3D” sozinho não distingue visualização, modelagem e síntese. A exceção importante é seção 6: u04 representa o ruling administrativo; não certifica aderência temática ao plano.

| Seções | Unidade | Evidência fornecida / ressalva |
|---|---|---|
| 1 | u01 | §2, 1.1 Origens |
| 2 | Pendente | §2 não vincula OpenGL; §3 só informa posição temporal |
| 3, 4, 5 | u02 | §2, 2.1–2.5; detecção/intersecção e Geometria Computacional explícitas |
| 6 | u04 pelo ruling | §1; há conflito com 5.1–5.4 e possível distinção de 7.2.4 |
| 7, 12, 14 | u07 | §2, 7.1.1 e 7.2 |
| 8, 9, 10, 11, Exercícios de Processamento de Imagens | u03 | §2, 3.2–3.5; morfologia não aparece nominalmente |
| 13, 15 | u06 | §2, 6.1–6.4; bundles exigem ressalva individual |
| 16, 17 | u08 | §2, 8.1–8.4 |

2. **OpenGL: escolher `scorable=no`, `status=pendente`.** HIPÓTESE: aula introdutória favorece u01, mas não prova vínculo curricular. O produto antigo em u01 também não constitui evidência independente. MEDIDO no §4: são **cinco candidatos a u01, incluindo `exercicios`**; o sexto material da seção é `texturas-v3`.

| Escolha | Custo para a régua | Resultado condicional, demais linhas iguais |
|---|---|---|
| u01 | Converte inferência cronológica em cinco erros definitivos | 85/93 |
| u02 | Usa a decisão atual como justificativa do próprio gold | 90/93 |
| u01\|u02 | Não distingue essas duas decisões; ainda rejeita outras unidades | 90/93 |
| Não pontuar os cinco | Perde cobertura explícita; preserva a incerteza | 85/88 |

Os resultados condicionais são **MEDIDOS por recálculo**, não acurácia adjudicada.

3. **Seção 6: manter u04 para o oráculo escolhido; não ampliar para `u04|u05` por dúvida.** HIPÓTESE: a união esconderia justamente a distinção investigada. Para medir aderência ao plano, seria necessária adjudicação temática separada. MEDIDO: existem **10 notas sobre u05**, não oito. A nota é gerada por palavras no ID, não por inspeção temática individual (S:45, S:92). Além disso, §2 coloca **Instanciamento de Primitivas em 7.2.4**: não generalizar todo “instanciamento” para u05.

4. **Provas e meta: a regra é coerente como conjunto de destinos aceitáveis, mediante confirmação de aplicação ao CG.** HIPÓTESE: exclusão no gold de subunidade não implica exclusão na unidade. Não acrescentaria u02 à prova 2D apenas por usar matemática/OpenGL; falta conteúdo avaliado de 2.1–2.5 (§5.4). Seu `u04|u05` mistura duas interpretações do mesmo conteúdo, sem demonstrar cobertura de ambas. MEDIDO: `|` significa “qualquer uma vale” (S:10); portanto, **não mede cobertura integral**. Os três meta aceitam qualquer unidade válida.

5. **Circularidade: compartilhar fonte não basta para provar contaminação.** HIPÓTESE: seção e cronograma podem sustentar erros correlacionados, mesmo por caminhos distintos. A dependência mais concreta é justificar OpenGL pelo produto de 06/09 (§1). `pred`, conflitos e ordenação por bloco expõem o adjudicador à ancoragem (S:103–115). “Colisão de token” explica uma causa candidata do erro; **8.4**, independentemente, fundamenta texturas. MEDIDO: **93/93 pontuáveis; oito notas pendentes; 85/93 por pertencimento; 78/86 nos golds unitários; sete conjuntos aceitos**. `status` nunca vira `pendente` neste gerador (S:112–113).

6. **Contestação individual.** HIPÓTESE: decisões abaixo; evidências textuais indicadas. Conflito entre dois sinais do motor, isoladamente, não justifica trocar os demais rótulos.

| ID | Unidade/estado que daria | Evidência e contestação |
|---|---|---|
| `exercicios` | Pendente; não pontuar | §4: OpenGL sem vínculo no plano; “texto queria u04” é sinal do motor |
| `opengl-cpp` | Pendente; não pontuar | §2/§3, aula 2 não determina unidade |
| `opengl-py` | Pendente; não pontuar | Mesma lacuna |
| `openglbasico` | Pendente; não pontuar | Mesma lacuna |
| `video-com-instrucoes-para-usar-opengl-na-vdi…` | Pendente; não pontuar | Mesma lacuna; instalação de ferramenta não prova u01 |
| `exemplodemanipulacaodeimagens` | **u03 candidato**; pendente | §4: nota identifica conteúdo de imagens/filtros, contra etiqueta “Classe Vetor”; §2, 3.4. Falta adjudicar a contradição |
| `opengl3dcpp` | Pendente; não pontuar | §4: bundle 2D/3D/Bézier/imagens; ruling do card explicitamente pendente |
| `opengl3dcpp-vdi` | Pendente; não pontuar | Mesma evidência; não inventar conjunto pelo nome do bundle |
| `resolucao-de-prova-de-computacao-grafica-2d` | u04 pelo ruling; u05 candidato temático | §5.4: somente transformações; `u04|u05` não demonstra dois conteúdos distintos |
| `resolucao-de-prova-de-computacao-grafica-2d-html` | Mesma decisão | §4: duplicata HTML; não constitui confirmação independente |

Nos dez materiais seguintes, **contesto a nota generalizante, não o u04 administrativo aprovado**:

| ID | Rótulo mantido / candidato temático | Evidência e ressalva |
|---|---|---|
| `animacao-v2` | u04 / indeterminado | §4; “animação” não prova transformação curricular |
| `exercicios-teoricos-sobre-processo-de-visualizacao-2d` — seção 6 | u04 / indeterminado | §4; título amplo, sem questões apresentadas |
| `instanciamento` | u04 / indeterminado | §2, 7.2.4 impede afirmar u05 pelo termo sozinho |
| `mapeamento` | u04 / u05 candidato | §2, 5.2, se efetivamente window/viewport |
| `pagina-com-videos-sobre-instanciamento` | u04 / indeterminado | Mesma ambiguidade de 7.2.4 |
| `pagina-com-videos-sobre-mapeamento-9f410e` | u04 / u05 candidato | §2, 5.2; confirmar objeto do mapeamento |
| `transformacoesgeometricas` | u04 / u05 candidato | §2, 5.1–5.6 |
| `transformacoesgl` | u04 / u05 candidato | §2, 5.1–5.6 |
| `video-sobre-mapeamento-em-opengl-1dad3c` | u04 / u05 candidato | §2, 5.2; OpenGL não define unidade |
| `vis2d` | u04 / indeterminado | §2 distingue rasterização/recorte de pipeline/transformações; título não resolve |
