# Plano — confiança antes de acurácia

last_updated: 2026-09-08
Entrada: `docs/reports/pendencias.md` (tracker vivo) · `.mex/context/audit-2026-09-07.md` (memória) ·
harness `docs/reports/_harness-2026-09-04/c1-3/`

## Por que esta ordem, e não a inversa

Medido em 08/09 (`c1-3/calibra_fila_como_regua.log`), a pergunta "num curso novo, sem gold, se eu aceitar tudo que o
motor **não** põe na fila, quanto está certo?":

| eixo | precisão do confiante | leitura |
|---|---|---|
| unidade | **157/157 = 100%** | um curso novo já dispensa gold de unidade |
| bloco | 177/178 = 99,4% | idem, na prática |
| **subunidade** | **117/181 = 64,6%** | **64 materiais saem errados sem aviso** |

O gold nunca foi insumo do motor; é instrumento de medida. O que o motor tem de próprio para saber se acertou é a
confiança, que vira a fila. Na unidade essa confiança é honesta. Na subunidade ela mente em um a cada três casos.

Subir acurácia com a confiança mentindo aumenta o número de acertos **e** o número de erros silenciosos. Produto que
erra calado é pior que produto que pergunta: o aluno não tem como saber que aquele material está no lugar errado.
Por isso a ordem é confiança primeiro.

## Estado de partida (08/09, produto em disco, Gemini bloqueado)

| medida | valor |
|---|---|
| materiais 100% certos | 199/288 |
| bloco | 235/237 |
| unidade | 190/190 |
| subunidade | **161/251** |
| fila | 96 em 348 = 27,6 por 100 |
| **erros confiantes** | **64** |

Cobertura do gold: bloco 68% do repo, unidade 55%, subunidade 72%. CG (93 materiais) e LR (7) não têm gold de unidade.

---

## FASE 1 — HONESTIDADE DA CONFIANÇA

**Objetivo:** que o motor mande para a fila o que hoje entrega calado.
**Régua:** precisão do confiante por eixo (`calibra_fila_como_regua.py`).
**Gate de saída:** precisão do confiante da subunidade **≥ 90%**, sem regressão em bloco e unidade, com o crescimento
da fila declarado e aceito.

### 1.1 Diagnosticar os 64 erros confiantes
Por que o scorer fica confiante e erra? Cruzar, para cada um: score do vencedor, margem para o segundo, origem do
sinal (rótulo do plano, alias de heading, alias compilado), tamanho do texto, classe do insumo.
Sem código, só medição. **0 chamadas.**
Saída esperada: uma ou duas famílias que expliquem a maioria — a hipótese de trabalho é que a margem alta vem de
alias longo casando por acaso em texto curto, mas **isso não está medido**.

### 1.2 Calibrar o limiar da subunidade
Uma varredura do limiar de confiança contra o gold, medindo os dois lados: quantos erros confiantes somem e quanto a
fila cresce. O gold é usado **uma vez**, aqui, para achar o ponto. Depois disso o limiar viaja para cursos novos sem
gold nenhum.
**Atenção:** a medição de 07/09 mostrou que piso sobre o *score* não funciona (todo piso perde). Este item é sobre o
limiar de **confiança/margem**, que é outra grandeza. Se também não houver ponto de corte útil, o item morre aqui e
vira registro.

### 1.3 Fazer a decisão fraca cair na fila
Só se 1.2 achar ponto. Regra no motor, com gate zero-diff, teste e reprocess registrado nos 8, como sempre.

---

## FASE 2 — ACURÁCIA

Só começa com a Fase 1 fechada. Os dois primeiros itens já estão medidos e não gastam chamada.

### 2.1 Propagação por similaridade — **+5 medido**
Material que continua indeciso depois da 1ª e da 2ª passada herda a subunidade do vizinho mais similar entre os que o
motor decidiu com confiança. Similaridade = Jaccard dos tokens distintivos, dentro da unidade.
Medido (`simula_propaga_similaridade.log`): regime atual 135 → 140, ganha 6 perde 1, piso 0,05–0,10.
**0 chamadas.**

### 2.2 Filtro mais duro no vocabulário compilado — **+2 medido**
Cortar termo doado cujo núcleo aparece no vocabulário ou nos materiais de outra unidade, e recusar doação a tópico de
rótulo meta ("Áreas relacionadas", "Conceitos", "Introdução").
Medido (`triagem_vocab_llm.log`): a unidade 01 do CG custa 2 pontos hoje; 3 outras chamadas são neutras.
**0 chamadas.**

### 2.3 `conflito` — 48 itens, metade da fila, nunca atacado
Quando o texto aponta uma unidade e o bloco aponta outra, o bloco vence por desenho e o desacordo só vira registro.
Há gold de unidade em 190 materiais para arbitrar quem acerta nesses casos. Medir antes de mexer.
**0 chamadas.**

### 2.4 Ligar o compilador de vocabulário nos 4 cursos bloqueados
SO 6 + IA 4 + ES2 2 + TCC 4 = **16 chamadas, uma vez**, depois cache.
Exige duas coisas: liberar o Gemini (decisão aberta) e tirar o sidecar do professor da frente
(`vocabulary_compile.py:222` não compila quando existe sidecar manual).
Referência de 02/09 citada no código: este prompt levou o IA de 5 para 37/39.

---

## FASE 3 — COBERTURA DA RÉGUA

### 3.1 Incluir o FR no conjunto padrão de medição
Descoberto em 08/09: `subunit_gt_FR.csv` tem 18 materiais pontuáveis que nunca entraram em nenhuma medição desta
campanha. FR faz 15/18. Todo script do harness que hoje usa 6 cursos passa a usar 7.

### 3.2 Gold de unidade para o CG
93 materiais, 27% do repositório, hoje sem régua nenhuma nesse eixo. A confirmação independente pelo professor cobre
só 17% deles. É o único jeito de fechar a pergunta "a unidade se sustenta fora do gold?".

---

## O que está ABERTO e depende do user

| item | o que trava |
|---|---|
| **Liberar o Gemini** | Fase 2.4 inteira, recompilar o vocab do CG, `gemini_auto_summarize` |
| **Qual camada LLM cortar** para ficar em duas | decisão de arquitetura registrada desde 06/09 |
| **Push/merge** dos 962 commits locais | nada técnico; é decisão de fronteira |
| **Posição da C7 (imagens)** na fila de campanhas | ordenação |
| **Artefatos publicados** | os 6 são de 07/09, de ANTES da descontaminação: mostram 254/288 e subunidade 201/233, que não valem mais. Hoje é 199/288 e 161/251. **Estão enganando quem abrir o link** |
| Revisão da fila do CG (`revisar_queue.md`) | trabalho humano |
| Correção da extração dos zips | bug conhecido (CG 168 nomes colidem entre 14 zips) |

## Campanha formal em curso

Pela fila registrada no tracker: **C1 TRAVESSIA** é a única aberta (FILE_MAP completo e magro), **C3 provas/listas** é
a próxima, e estão estacionadas C7 imagens, C2 bibliografia, C4 limpa, C5 dívidas de dados, C6 web.
Este plano não é uma campanha nova: é o conteúdo do que fazer no motor, e se encaixa como continuação de C1 (itens
1.x e 2.1–2.3) e C5 (itens 3.1–3.2).

## Regras que valem em todos os itens

- Dado antes de código: nenhuma alavanca entra sem medição prévia pela rota real.
- Gate zero-diff, teste e reprocess registrado nos 8 tutores em toda mudança de motor.
- Gold só mede, nunca decide; e nunca vira insumo (entrou duas vezes, foi retirado em 07 e 08/09).
- SARC e Moodle acima do gold quando divergirem.
- Nada é empurrado para `main` sem ordem explícita.
