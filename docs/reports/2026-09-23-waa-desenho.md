# W-AA reformulado: desenho, novidade e conferências (23/09/2026)

> **Status: executado em 23/09 depois da autorização do usuário; resultado em `2026-09-23-waa-resultado.md`** (nenhum braço
> passou). Este documento é o desenho pré-declarado e fica como estava antes da execução, salvo a §7, escrita antes de rodar.

Pedido: texto colado pelo usuário em 23/09, depois do W-Z2 (reformular o W-AA antes de executar; entregar primeiro o
desenho, as diferenças para o que já foi medido e as conferências pontuais). **Nada do W-AA foi executado.** Nada em
`src/`, régua, defaults ou legado foi alterado; sem commit. Base de referência: W-Z2
(`2026-09-23-diagnostico-causal-tres-eixos.md`; capturas congeladas `.frzero/wz2_captura_*`).

## Conclusão

- **Existe hipótese nova, em duas peças, nenhuma medida antes.**
  - *S (seleção por função e extensão):* o primário é o tópico que ocupa mais seções de papel principal. Menções dentro de
    seções de revisão, pré-requisito, exemplo, comparação ou índice não contam como assunto principal. Heading só delimita
    seção; não é prova de principal. Isso é o que a separa do H2 de 21/09.
  - *G (geração local por subordinação):* uma expressão forte do material ganha o tópico T como candidato, só para aquele
    material, quando outro documento do pacote a coloca estruturalmente sob T (heading ancestral de outro material, ou linha
    sob o heading de T no plano/ementa do professor) e ela liga a um único tópico da unidade prevista. É isso que a separa do
    W-U, que só contou existência de relação, e do extrator de 14/09, que só lia relações explícitas "categoria: itens".
- **Parcela alcançável (teto diagnóstico, não previsão):**

  | peça | alvo | materiais em que age (sondagem sem gold) |
  |---|---|---|
  | S | os 67 erros de seleção (43 com evidência acima do resíduo) | 271 dos 341 elegíveis |
  | G | os 65 F6 (relação existe fora do índice) | 209 dos 341 (292 pares material-tópico) |

  Mesmo com conversão perfeita e sem perdas, o W-AA chega a 86 + 67 + 65 = **218/251 (86,9 %)**, abaixo de 226. Ficam sem
  caminho F7 (11), F1 (5, régua) e F2 (17, unidade). O W-AA decide direção; não é caminho suficiente até 90 %.
- **Evidência que o refuta:**
  - *S:* no teste de sinal, a ordem por função e extensão não põe o gold em 1º mais vezes que a ordem atual; ou o braço A tem
    saldo ≤ 0.
  - *G:* o braço B' tem saldo ≤ 0; ou a precisão das decisões que G muda não supera a das decisões que ele substitui.
  - *Ambos refutados:* as fontes léxico-estruturais do pacote ficam esgotadas para a subunidade. A próxima decisão passa a ser
    de regime (conhecimento externo ou declaração), não de ajuste.

## 1. Direção e aritmética

- Geração (76) + seleção (67) = 143 dos 165 erros.
- Corrigir só a seleção, sem nenhuma perda, leva a 86 + 67 = **153/251 (61 %)**. Não é caminho suficiente.
- Somar os 65 F6 leva a 218/251. Os 226 exigem também unidade (F2) e o que hoje não tem caminho no pacote (F7, F1).

## 2. O que já foi medido e onde o W-AA difere

| experimento (data) | o que testou | resultado | relação com o W-AA |
|---|---|---|---|
| **H2** (21/09) | bônus por token exclusivo em heading/título | 86 (+4/−2), refutado | **Equivalência registrada:** o critério "frase em título ou heading" que propus no W-Z2 é variante de localização do H2 e sai do desenho. S não usa localização como prova: usa papel da seção e extensão. |
| H1 (21/09) | label do Moodle como título | +1/−0, descartado | outra fonte de localização; sem relação |
| H3/H3a/H3ad/H3b (21/09) | pontuador de unidade no lugar do de subtópico | 95 (+18/−7); abstenção → decisão 7 certas e 14 erradas | o W-AA não troca o pontuador; muda o critério de escolha (S) e os candidatos por material (G) |
| pai × filho (13–14/09) | parentesco entre tópicos | fechado: nenhuma regra separa erros de controles | S e G não usam parentesco |
| singular × plural, radical, prefixo (13–14/09) | forma do token | 0 ou refutado | G usa o radical de 6 letras só como chave de expressão do W-U, não como mecanismo |
| 2ª passada atual (05–06/09) | vocabulário doado pelas decisões confiantes da 1ª passada | parte da base (+11/−4 na base v2) | a fonte da propagação é saída do motor; G só usa documentos. Partes do rótulo e seção continuam como estão |
| vizinho confiante na seção (21/09) | voto dos vizinhos | 0 de 46 unânimes | o W-AA não vota por vizinhos |
| extrator de relações explícitas (14/09) | "categoria: itens" no pacote | 3 relações novas, +1 por autodoação, fechado | G usa subordinação estrutural (hierarquia de headings, linha sob heading do plano), exclusiva na unidade, injetada só no material; autodoação excluída |
| W-U (22/09) | existência de relação P1–P4 | recall sem precisão (177/179 conflitantes no curso) | G restringe a subordinação (P1 e P4 do professor), à unidade prevista e à exclusividade nela; o W-U não mediu critério nem decisão |
| braço V (13/09) | relações curadas dirigidas por gold | +33, não transferível | G não usa gold |
| W-P2'/W-S (22/09) | declaração do professor | fora por decisão do usuário | — |

**Localização × função.** O pontuador atual soma presença por campo (headings 4,4, título 3,8, lead 2,8, corpo 1,1;
`timeline/index.py:1859`), uma vez por campo. Um tópico citado uma vez num heading "Revisão" pesa o mesmo que um tópico que
ocupa dez seções. S muda duas coisas: (1) o papel da seção vem do rótulo dela; heading de revisão, pré-requisito, exemplo,
comparação ou índice rebaixa as menções; (2) conta **extensão**, isto é, em quantas seções principais o tópico aparece. Esse é
o critério das notas da régua ("tópico próprio", "guarda-chuva", "maioria das questões").

## 3. Mecanismo pré-declarado (congelado antes de rodar)

**Elegíveis:** todo material que passa pela 1ª passada da subunidade (sem pino manual, sem regra de meta-material): 341 nos 7
cursos. A mesma política vale para todos; os subconjuntos do diagnóstico só explicam resultados. A unidade não muda em nenhum
braço.

**S — função e extensão**
1. Seções: headings markdown do texto que o seletor já lê. Com menos de 2 headings, usa itens numerados de 1º nível. O título
   do material é a seção 0.
2. Papel da seção pelo rótulo, com léxico fixo:
   - revisão: revisao, relembrando, recapitulando, retomando;
   - pré-requisito: pre-requisito, prerequisito, conhecimentos previos, fundamentos previos;
   - exemplo: exemplo, exemplos, exemplificando;
   - comparação: comparacao, comparativo, versus, vs, diferencas;
   - índice ou referência: sumario, agenda, objetivos, referencias, bibliografia, leituras, links, proxima aula.

   Guarda sem gold: termo do léxico que apareça em rótulo ou alias de tópico do curso é ignorado naquele curso. Exemplo: um
   rótulo com "estudo de caso" não vira "exemplo".
3. Ocorrência de T numa seção: o mesmo casamento exato de frase do seletor atual (rótulo, aliases, slug de T).
4. Extensão(T) = número de seções de papel principal com ocorrência de T.
5. Decisão: primário = maior extensão. Empate: escore atual. Sem ocorrência em seção principal: decisão atual (S não age).
   Vale nas duas passadas.
6. Sem parâmetro livre (léxico fixo e contagem inteira), então não há o que escolher por LOCO. Se aparecer parâmetro, ele sai
   por LOCO e é declarado antes.

**G — geração local por subordinação**
1. Expressões fortes do material: as do W-P1 (título, arquivo, label do Moodle, headings, 1ª linha da curadoria de código).
2. Relações admissíveis:
   - P1: a expressão está em heading ou item de **outro** material, sob heading ancestral que menciona T;
   - P4: a expressão está em linha sob o heading de T, mas só no plano de ensino e na ementa de `_inputs`.

   Excluídos: P2 (mesma linha), P3 (texto do cronograma), GLOSSARY/COURSE_IDENTITY/SOURCE_REGISTRY (gerados no build), o
   próprio material, qualquer campo computado pelo motor, gold e IDs.
3. Exclusividade: a expressão liga a exatamente um tópico da unidade prevista.
4. Uso: T recebe a expressão como alias **só para aquele material**; a pontuação desse material é refeita. Não existe alias
   global.
5. Proveniência gravada por par: expressão, tópico, documento, trecho literal, padrão.
6. Separado no relatório: candidato novo (T tinha pontuação zero) e reforço (T já era candidato).

**Braços** (fatorial 2 × 2, sem grade):

| braço | candidatos | seleção |
|---|---|---|
| base | atuais | atual (reutiliza o congelamento do W-Z2) |
| A | atuais | S |
| B' | atuais + G | atual |
| B | atuais + G | S |

B' é acréscimo ao pedido. Sem ele, uma falha de S contaminaria a leitura de G.

**Execução:** 3 replays da fase unidade + subunidade, com o seletor da subunidade trocado em memória e restaurado depois.
Bloco e unidade são reutilizados e conferidos por ID como idênticos. Cerca de 3 min por braço; nenhuma execução repetida.

## 4. Avaliação

**Teste de sinal (exploratório, relatado em separado):**
- Nos 251, quantas vezes a ordem de S põe o gold em 1º, contra a ordem atual.
- Quantos golds passam a ter pontuação > 0 com G, e quantos concorrentes G injeta.

**Política completa, por braço, sobre os 251:**
- acertos totais e por curso, primária e aceita;
- correções e perdas por ID;
- abstenções que viram decisão certa ou errada, e decisões que viram abstenção;
- precisão das decisões novas ou alteradas;
- materiais sem gold alterados (contados, não avaliáveis);
- bloco e unidade idênticos por ID.

**Aceite de integração, inalterado:** saldo > 0, zero perda de acerto atual (medida, sem lista protegida por gold), nenhum
curso regride, demais eixos idênticos em replay integral. Precisão nos acertos atuais não é aceite.

**Leitura de direção, decidida antes de rodar:**

| resultado | direção |
|---|---|
| A > base e B' > base, sem perdas | seleção e geração seguem para Gate 1 de implementação, em separado |
| só A passa | frente de seleção; F6 vai para decisão de regime |
| só B' passa | frente de geração; seleção por função fica fechada |
| nenhum passa | fontes léxico-estruturais do pacote esgotadas para a subunidade; decisão de regime |
| A e B' com saldo positivo mas com perdas | não integra; registra onde perde (papel mal lido ou relação espúria) e fecha, sem ajuste de pesos |

## 5. Conferências pontuais do W-Z2

### 5.1 Transições do oráculo de unidade: 86 → 92 é saldo, não recuperação bruta

**8 correções, 2 perdas, saldo +6.**

| material | como passou a acertar |
|---|---|
| CG `basico3d-py-zip`, `openglbasico` | 1ª passada, já na unidade certa |
| CG `aula-gravada-975b85`, `morfologiamatematicapptx`, `pagina-com-videos-sobre-morfologia-matematica-06265a` | propagação da 2ª passada |
| ES2 `microsservicos4`, `roteiro4` | seção do Moodle na 2ª passada |
| CG `pagina-com-videos-sobre-instanciamento` | abstenção aceita pela régua incoerente (gold vazio; ver 5.3) |

- **Perdas:** CG `bezier-py` e `bezier-python`, cuja unidade não muda. Na base acertavam pelo rótulo decomposto; no oráculo a
  propagação da 2ª passada os leva a outro tópico. É efeito colateral: a unidade de outros materiais mudou, e com ela os
  doadores de vocabulário.
- **Unidade mudou, subunidade continua errada:** 14 materiais (F6 5, F1 4, F4b 2, F7 2, F8 1).
- **2ª passada:** base 64 → 86 (+26/−4); oráculo 66 → 92 (+29/−3).
- **Saldo por conteúdo:** +5 (+6 menos a abstenção aceita pela régua).

### 5.2 Teto de 84,1 % no CG: fórmula, IDs, condições

- **Fórmula:** teto = n − |F1 ∪ F7| no modo oráculo de unidade. CG: 82 − (4 + 9) = **69/82 (84,1 %)**; o mínimo acima de 90 % é
  74.
- **F7 (9):**
  - gold `conceito-de-camera-sintetica`: `atividade`, `opengl3dcpp`, `opengl3dcpp-vdi`;
  - gold `aplicacoes`: `exercicios`, `opengl-py`, `video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758`;
  - gold `operacoes-com-vetores`: `exercicio-com-animacao`;
  - gold `sistema-de-coordenadas-cartesianas`: `video-sobre-mapeamento-em-opengl-1dad3c`,
    `pagina-com-videos-sobre-mapeamento-9f410e`.
- **F1 (4):** `animacao-v2`, `instanciamento`, `transformacoesgeometricas`, `transformacoesgl`.
- **Condições:** unidade dada por oráculo; toda F2/F4/F5/F6/F8 convertida sem perda; F7 tratado como inalcançável; F1 tratado
  como inalcançável.
- **O que é teto de intervenção e o que é limite de informação:**
  - 84,1 % é teto de **intervenção ideal sobre as fontes inspecionadas, com a régua atual**. Não é limite de informação.
  - F7 significa "nenhuma relação no alcance inspecionado": radical, seção, tópicos do bloco e índice documental. A
    informação parece estar nos materiais (chamadas de câmera no código OpenGL; vídeos sobre mapeamento), mas falta a ponte
    léxica até o rótulo do plano. Para o regime cru, é limite do conteúdo léxico do pacote; fechar a ponte exige conhecimento
    de domínio, isto é, regime separado.
  - F1 é limite da régua (5.3).

### 5.3 Os cinco casos de régua incoerente

A subunidade-gold está vazia porque foi anotada em 06/09 sob a u04 ("u04 não tem subtópico → vazio"). A régua v2 (22/09)
passou a unidade para u05, que tem "transformações geométricas e coordenadas homogêneas 2D".

- **Na base (unidade u04):** os 5 erram (F1).
- **No oráculo (unidade u05):**
  - `instanciamento`, `transformacoesgeometricas` e `transformacoesgl` escolhem justamente
    `transformacoes-geometricas-e-coordenadas-homogeneas-2d` e contam como erro;
  - `animacao-v2` escolhe `mapeamento-window-e-viewport`;
  - `pagina-com-videos-sobre-instanciamento` se abstém e conta como acerto.
- **No teto do CG entram como 4 sem caminho.** Se a régua fosse revista para o tópico da u05 (não alterada nesta etapa), os 4
  virariam endereçáveis, 3 já estariam certos no oráculo e a abstenção passaria a erro. O teto iria para 82 − 9 =
  **73/82 (89,0 %)**, ainda abaixo de 74.

### 5.4 Motor D9 no fluxo real de criação de disciplina (ambiente isolado)

**Ambiente:** APPDATA temporário com `subjects.json` novo, duas cópias do TCC com os campos temporais apagados, e rede,
Gemini e Datalab bloqueados.

**Código real usado:** o diálogo `SubjectManagerDialog` (`_new`, `_on_select`, `_save`), `SubjectStore`,
`_build_options_from_config` (o que a UI passa ao `RepoBuilder`, `app.py:1835-1845`) e `RepoBuilder.incremental_build`
(botão Reprocessar). Substituídos só a janela modal de confirmação e o `grab_set`, e dois contadores que delegam às funções
reais. Script e saída: `_harness-2026-09-04/c1-3/waa_iso_d9_fluxo_real_23-09.{py,json}`. A sondagem sem gold da §3 está em
`c1-3/waa_sonda_sem_gold_23-09.py`.

| caso | flags do perfil | D9 chamado | resolvedor antigo chamado | materiais com bloco temporal |
|---|---|---:|---:|---|
| disciplina criada pelo diálogo | `{}` | 0 | 1 | 0 de 27 (26 só com `computed_block_id`) |
| mesma criação + flag gravada como faz `scripts/build_course.py:181` | `use_anchor_engine` | 1 | 1 | 26 de 27 |
| editar a matéria com flag e salvar no diálogo | a flag some (`{}`) | — | — | — |

Três achados, nenhum corrigido:

1. **Disciplina nova criada pela UI roda só o resolvedor antigo** para bloco e unidade. O D9 não é ligado em nenhum ponto do
   fluxo da UI: o diálogo não grava `feature_flags` (`dialogs.py:1503-1529`) e o padrão do código é desligado
   (`pedagogical_regeneration.py:598`).
2. **Salvar uma matéria existente no diálogo apaga as flags.** O `_save` monta o perfil sem `feature_flags` e
   `SubjectStore.add` substitui o perfil inteiro (`models/core.py:390-392`). Nos seus 8 cursos, editar e salvar pela UI
   desliga o D9, o votador e o vocabulário no próximo reprocessamento.
3. **`options` do manifest não mostra o que rodou.** A cópia manteve `use_anchor_engine: true` gravado de um build anterior,
   mas a UI não usou o D9. O script headless `reprocess_assignments.py` lê essas `options` antes das flags do perfil, então
   ligaria o D9 onde a UI não liga.

Nada removido nem alterado. Corrigir exige issue, proposta e replay próprios.

## 7. Ajustes de interpretação e detalhes de implementação (registrados antes da execução, sem gold)

Autorização de execução do usuário, 23/09 (literal em `c1-3/waa_pedido_execucao_23-09.md`). Sem grade nem variante nova.

1. **Leitura fatorial.** Efeito de S = A − base; efeito de G = B' − base; interação = B − A − B' + base. Saldo negativo de uma
   peça isolada não a reprova se a combinação B produzir melhoria que passe o aceite.
2. **Aceite de integração inalterado:** ganho positivo, zero perda entre acertos atuais, nenhum curso regride, demais eixos
   preservados, replay integral. As regras de acionamento não usam nenhum grupo identificado pelo gold.
3. **Cobertura não é ganho.** 271/341 e 209/341 medem onde S e G agem. A avaliação é sobre os 251 com gold. Os demais
   materiais participam como fontes: são documentos do índice de relações (P1), doadores da 2ª passada e decisões alteradas
   contadas como não avaliáveis.
4. **Definições preservadas** (papéis, segmentação, desempates, unicidade). O relatório examina: evidência perdida quando
   exemplo, comparação ou revisão é o assunto principal; seções equivalentes contadas em dobro; unicidade de G que só existe
   pela restrição à unidade prevista; efeitos indiretos da 2ª passada.
5. **Alcance.** 218/251 é o alcance ideal dos grupos-alvo com as condições da §1, não teto universal. Se o W-AA falhar, a
   conclusão se limita aos mecanismos examinados. Rotulação pelo professor não volta como requisito.

Detalhes que a §3 não fixava, decididos agora e antes de qualquer gold:

- **Seção 0:** o título mais o preâmbulo (texto antes do 1º heading ou item). O papel dela vem do título.
- **Rótulo de item numerado:** a própria linha do item.
- **Confiança de uma decisão de S que troca o tópico:** mantém a confiança original do seletor e marca "não ambígua". Assim a
  regra de doador e de proteção da 2ª passada continua presa à margem do pontuador atual.
- **Abstenção:** quando o seletor atual se abstém, S decide sempre que algum tópico ocorre em seção principal. Isso inclui a
  guarda de "revisão sem assunto dominante"; a §3 não a excetua.
- **Alias local de G:** a forma normalizada da expressão (tokens válidos do W-P1). Casa como frase quando é contígua no texto
  e sempre soma pelos tokens distintos do tópico. Formas das quais se removeu palavra de ligação ("arvore decisao") não casam
  como frase; é limitação declarada.
- **Unidade usada por G:** a unidade final da base (a mesma em todos os braços; conferida chamada a chamada).
- **Execução efetiva do D9 no harness:** `replay_bloco_21-09.py:48` chama `apply_anchor_engine(enabled=True)`. No W-Z2, 275 dos
  284 materiais com gold de unidade usaram bloco temporal do D9; o script do W-AA reconta isso a cada braço.

## 6. Custo e gates

- **Execução do W-AA:** 3 replays, ~3 min cada, mais a avaliação, no agente ativo (Opus). Sem Astra (medição).
- **Gate 1 pedido:** executar W-AA exatamente como na §3. A execução não autoriza implementação nem commit.
- **Decisões separadas suas:** régua do CG (5.3); se os três achados da 5.4 viram issue; Gate 2 documental dos artefatos de
  22–23/09.
