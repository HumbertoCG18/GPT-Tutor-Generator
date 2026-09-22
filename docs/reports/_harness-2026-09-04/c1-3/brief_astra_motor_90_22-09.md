# Pedido de ideias de solução — motor de atribuição do GPT-Tutor-Generator

Você está recebendo este brief para propor **ideias de solução**, não para implementar. Responda em português. Ao final há o formato de resposta que precisamos. Não temos como executar nada do seu lado: tudo o que você propuser será medido aqui, num harness próprio, antes de qualquer decisão.

## 1. O projeto em uma página

O GPT-Tutor-Generator é um app desktop em Python (Tkinter) que transforma os materiais de uma disciplina universitária (PDFs, slides, códigos, links baixados do Moodle) num "tutor": um repositório organizado por **bloco temporal** (a aula/semana em que o material foi dado), **unidade** (a unidade do plano de ensino) e **subunidade** (o subtópico dentro da unidade). O coração é o **motor de atribuição**: dado um material, decidir esses três eixos.

Insumos que o motor tem por material: título, nome do arquivo, categoria detectada (slides, listas, provas, trabalhos, código…), seção/card do Moodle de onde veio (`source_section`, ex.: "Sincronização e Comunicação de Processos" ou "Semana 3 - 16.03 a 20.03"), rótulo do Moodle, data de postagem, texto extraído em Markdown (headings, lead, corpo), prazos de entrega quando são trabalhos/provas, e o **plano de ensino** do professor (unidades e tópicos, em texto). Além disso, um cronograma da disciplina vira um índice de blocos ordenados por data, com `kind` (class, assessment, review, deliverable, makeup, overview…) e, para blocos de aula, uma unidade posicional.

Regimes: hoje medimos o **regime cru** — 0 LLM, 0 rede, tudo léxico/heurístico, determinístico. Existe um regime opcional com declaração do professor e outro com LLM, mas a meta atual é o cru. Máquina fraca; embedding conta como LLM.

## 2. Como o motor decide hoje (resumo fiel)

1. **Bloco temporal** (`motor/apply.py`, cascata): pino manual > janela de prazo (`due-window`: trabalhos/provas casam o vencimento do Moodle com o bloco que o contém; se o vencimento cai em bloco de prova, ancora no último bloco de conteúdo anterior) > fora de escopo (bibliografia, cronograma, seção "TDE") > referência genérica > cache por hash de conteúdo > **engine** (janela de candidatos por seção/card/data no título → desambiguação léxica entre candidatos → sem voto de LLM no cru) > herança de irmão numerado. Métodos observados no MF: `disamb` 36, `janela-1` 16, `titulo-topico` 9, `prep-prova` 2, outros 4.
2. **Unidade** (`resolver_apply.apply_unit_subunit_fields` + `file_map`): um scorer léxico pontua título/headings/lead/corpo/seção/tags contra o índice de unidades do plano (frases dos tópicos, tokens distintivos por IDF entre unidades, glossário). Depois **reconcilia com o bloco**: a unidade do bloco temporal vence o texto quando discordam (medido em 08/2026: bloco 162/188 contra texto 130/188). Exceções já medidas e implementadas: unidade explícita no título ("U2 - …") vence; desde 21/09, seção do Moodle com vencedor único no plano **e** texto concordante vence a unidade herdada do bloco (+5, 0 perda).
3. **Subunidade**: dentro da unidade decidida, um scorer pontua os subtópicos da taxonomia (tópicos do plano + aliases); 1ª passada por material; **2ª passada** aprende, dos materiais confiantes do curso, tokens exclusivos de um subtópico como aliases e repontua só os indecisos. Abstém quando ambíguo ou abaixo do gate.

Um vazamento de desenho medido em 21/09: o vocabulário aprendido na 2ª passada acopla materiais entre si — mudar a unidade de um material muda a subunidade de outro cujo texto nem mudou (ex.: o token de formato `videos` virou alias de um subtópico).

## 3. Onde estamos (medido, builds de 15/17-09, 7 cursos, gold curado só para avaliar)

Meta: **> 90 % em cada eixo, separadamente**, acerto total sobre o denominador histórico (ausentes contam como erro; abstenção conta como erro).

| Eixo | Base 15/17-09 | Hoje (commit da regra da seção, 21/09) | Com a próxima regra já medida e aprovada | Mínimo para > 90 % |
|---|---:|---:|---:|---:|
| Bloco | 213/237 (89,9 %) | 213/237 | **214/237 (90,3 %)** | 214 |
| Unidade | 239/284 (84,2 %) | 244/284 (85,9 %) | **246/284 (86,6 %)** | 256 |
| Subunidade primária | 84/251 (33,5 %) | 84/251 | 84/251 | 226 |
| Subunidade "aceita" (auxiliar; gold aceita um conjunto) | 108/251 (43,0 %) | 107/251 | 107/251 | — |

Por curso (unidade / sub primária, base): MF 61/66 · 25/58; SO 27/37 · 7/15; IA 39/42 · 4/39; ES2 25/28 · 7/28; TCC 17/18 · 7/11; CG 70/93 · 28/82; FR — · 6/18.

**Bloco** está resolvido no total; MF (54/66 após a próxima regra) é o único curso abaixo de 90 %, com 5 famílias de erro (3 links não ingeridos, 4 desempates errados do `disamb`, 3 erros de fronteira do `janela-1`, etc.); nenhum sinal de data no nome dos materiais errados.

**Unidade**: dos 38 erros restantes, 12 são links externos que nunca entram no pacote (teto real 272/284 sem entrada offline), 1 é PDF ausente por caminho, e ~25 vêm do bloco (unidade herdada de um bloco errado ou de um vizinho). Faltam 10 para 256.

**Subunidade é o eixo longe**, e é o foco deste pedido.

## 4. O que já foi medido na subunidade (para não repetir)

- Anatomia dos 159 erros (17/09): **95 com rótulo ausente** (o gold nomeia um subtópico cujo vocabulário não aparece no material nem no plano — o plano nomeia categorias, o material nomeia algoritmos: "Modelos Preditivos" ← perceptron, rede neural), 17 genéricos, 47 com token discriminante presente mas perdendo (30 em título/heading). Dos 95 sem rótulo: 68 markdown, 27 resumo de código, 5 com gold vazio; 93 têm vizinhos de seção confiantes, mas o consenso unânime dos vizinhos acerta zero.
- Replay fiel + hipóteses (21/09): H1 rótulo do Moodle +1; H2 token discriminante ponderado por campo 86 (+4/−2); H3 scorer de unidade reaproveitado como scorer de subunidade 88 (+18/−14, corrigido 95 (+18/−7) mas cria erros em 77 % das abstenções convertidas); H3b pós-hoc só nos indecisos 89 (+5/−0) mas 5 acertos por 11 erros novos. **Nenhuma alavanca léxica genérica alcança +20.** Selector-oráculo entre variantes recupera só 19 erros distintos.
- Pesquisa adversarial independente (21/09): o 33,5 % **não é artefato de medição**; teto condicional das somas de diagnóstico 52–59 %; nenhuma alavanca não medida com ganho esperado ≥ +20 identificada.
- **Vocabulário compilado por LLM uma vez por curso**: 73–74 % (IA 5/39 → 38/39 com +18 termos em 2 tópicos). É a alavanca dominante, mas está fora do regime cru; a decisão do usuário é que o professor possa **declarar uma vez** (regime 2) e que LLM/API sejam opcionais. Um selector de vocabulário automático já se mostrou sobreajustado (dois tópicos do IA concentram todo o ganho).
- Descrições de imagens geradas por Datalab em inglês contaminam a 2ª passada (aliases genéricos).
- Refutadas na unidade/bloco: "texto vence sempre" (−15), regra do título (−9), precedência por método do bloco (+38 dentro, −3 fora, LOCO), "bloco misto" isolado, "seção sozinha" (perde subunidade no TCC).

## 5. Restrições que qualquer proposta precisa respeitar

- **Regime cru**: 0 LLM, 0 rede, 0 embedding, determinístico, roda em máquina fraca.
- **Gold só avalia**; nada de regra por curso, lista de exceções ou ajuste ao gold. Cursos já estudados não valem como holdout novo — qualquer parâmetro precisa ser escolhido por LOCO (deixa um curso fora).
- Ausentes e abstenções continuam no denominador; não redefinir a métrica.
- Aceite de uma regra: saldo > 0, **0 perda entre os acertos atuais**, nenhum curso regride, os outros dois eixos preservados, e precisão medida das decisões novas (abstenção → decisão errada conta contra).
- O plano de ensino é o único "conhecimento de domínio" garantido; o professor pode, opcionalmente, declarar vocabulário uma vez (regime 2) — se sua ideia depender disso, diga explicitamente e estime o custo para o professor.

## 6. O que pedimos

1. **Ideias de solução para a subunidade** (prioridade) que possam, no regime cru, sair de 33,5 % em direção a 90 %, ou que expliquem por que isso é inatingível sem vocabulário externo — e, nesse caso, qual é o **menor pedido possível ao professor** (regime 2) que fecharia a lacuna, com estimativa de ganho por curso a partir dos números acima.
2. Secundário: ideias para os ~25 erros de unidade que vêm do bloco e para os 4 desempates errados do `disamb` no MF, sem regra por método (já refutada).
3. Para cada ideia: premissas, mecanismo, sinais que usa (só os listados na seção 1), ganho esperado com faixa e em quais cursos, riscos de perda (quais acertos atuais ela ameaça), como medi-la aqui com replay fiel e LOCO, e o que a refutaria. Marque hipótese como hipótese.
4. Não proponha: LLM/embedding no cru, regras por curso, mudar a métrica, remover ausentes, holdout com curso já estudado.

Formato: lista numerada, ideias ordenadas por ganho esperado ÷ risco; no máximo 6 ideias; cada uma em até 15 linhas. Termine com o que você precisaria ver (dados/medições) para refinar a melhor ideia.
