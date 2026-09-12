# Brief para segunda opinião (Codex astra, read-only) — Fase 1 do plano "confiança antes de acurácia", 2026-09-11

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar. Responda em português,
no máximo 1 página mais tabelas; cada achado com evidência (trecho ou linha desta página, ou arquivo:linha) e marcado
MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` = `docs/reports/_harness-2026-09-04/c1-3/`.

## 1. O problema e o que aconteceu antes desta fase

O motor atribui cada material a bloco, unidade e subunidade, e mantém uma **fila de revisão humana** (`revisar` = `duvida` |
`mudou` | `ok`). "Confiante" = fora da fila (`ok`). A Fase 1 do plano pergunta: **o motor sabe quando está inseguro?** Régua:
precisão do confiante por eixo contra o gold (`c1-3/calibra_fila_como_regua.py`). Gate de saída da fase: precisão do confiante
da subunidade ≥ 90%, sem regressão em bloco e unidade, com o crescimento da fila declarado e aceito pelo usuário.

Hoje, antes da Fase 1 começar, o produto mudou (camada 3 cortada, vocabulário LLM nos 8 tutores, zips íntegros). Subunidade no
produto: 161 → 214 em 251. Remedimos a régua da Fase 1 sobre o produto atual:

| eixo (produto 11/09) | n | confiante&certo | confiante&ERRADO | fila&errado | fila&certo | precisão do confiante | 08/09 |
|---|---|---|---|---|---|---|---|
| bloco | 237 | 188 | 1 | 1 | 47 | 99,5% | 99,4% |
| unidade | 190 | 160 | **2** | 2 | 26 | 98,8% | 100% (0 erros) |
| subunidade | 251 | 174 | **18** | 19 | 40 | **90,6%** | 64,6% (64 erros) |

Fila hoje: 78/348 = 22,4 por 100 (08/09: 27,6). Recall da fila na subunidade: 19/37 = 51% (08/09: 29%).

## 2. Como o motor decide "confiante" (trechos do código)

`src/builder/routing/file_map.py:232-250` (decisão de subunidade):
```
    if _REVISAO_RE.search(titulo_e_id) and winner_score < T.SUBUNIT_REVISAO_FLOOR:   # piso 7.0, só para títulos "revisão/prova"
        return ... confidence=0.0, ambiguous=True, reasons=["revisao-sem-assunto-dominante ..."]
    if len(scored) == 1:
        confidence = 0.72; ambiguous = False
    else:
        confidence = max(0.0, min(1.0, rel_margin))          # margem relativa vencedor x segundo
        ambiguous = rel_margin < T.SUBUNIT_AMBIG_MARGIN       # 0.12
    if ambiguous:
        confidence = min(confidence, 0.45)
    reasons = [f"winner_score={winner_score:.2f}"] + (["ambiguous"] if ambiguous else [])
```
`src/builder/routing/revisar.py:46-75`: `revisar_de` = `duvida` se algum gatilho (`sem-bloco`, `flag:<metodo>`, `conflito`,
`sub-empate`/`sub-ambigua`), `mudou` se `sync_changed`, senão `ok`. Ou seja: na subunidade, hoje só **empate exato** e
**ambíguo (margem < 0,12)** põem na fila. `SUBUNIT_TAG` (0,10) é o mínimo de confiança para gravar subunidade; piso global de
score foi medido e refutado em 07/09 ("todo piso perde") — como piso do RESULTADO, não como gatilho de fila.

## 3. Item 1.1 — os 18 erros confiantes de subunidade (MEDIDO, `c1-3/erros_confiantes_11-09.log`)

`conf` = `subunit_match_confidence` (margem relativa), `score` = `winner_score`, `txt` = bytes do `.md` do material (0 = zip).
```
curso material                                     tipo  predito                    gold                        conf  score    txt
ES2  microsservicos2                              pdf   orientada-a-microsservicos estudo-de-caso-arquitetura  0.51  30.69  16423
ES2  microsservicos3                              pdf   estilos-e-padroes-arquitet estudo-de-caso-arquitetura  0.19  15.05  20767
ES2  roteiro3-gateway                             pdf   cliente-servidor           estudo-de-caso-arquitetura  0.27   9.32  16137
TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hi pdf   maquinas-de-turing         (vazio)                     0.43  20.54  38357
MF   archive-of-formal-proofs-355fb8              url   abordagens-para-verificaca provadores-de-teoremas      0.30  16.31    487
MF   exemplos                                     code  exemplos-de-aplicacoes     provadores-de-teoremas      0.67  13.74   1458
MF   tiposindutivos                               zip   verificacao-de-programas   softwares-de-suporte-a-ver  0.86   0.12      0
CG   animacao-v2                                  zip   desenho-de-linhas          (vazio)                     0.23   1.35  11586
CG   exercicios-teoricos-sobre-processo-de-visual html  desenho-de-linhas          sistema-de-coordenadas-car  0.30   1.41    957
CG   pagina-com-videos-sobre-instanciamento       html  desenho-de-linhas          (vazio)                     0.91   1.35  10638
CG   bezier-python                                zip   tecnicas-de-modelagem-3d   bezier-e-algoritmo-de-cast  0.28  15.12      0
CG   exercicios-teoricos-sobre-processo-de-visual html  desenho-de-linhas          sistema-de-coordenadas-car  0.30   1.41    957
CG   video-com-instrucoes-para-usar-opengl-na-vdi url   conceitos                  (vazio)                     1.00   7.06    438
CG   pagina-com-videos-sobre-fundamentos-matemati html  algoritmos-de-poligonos    entidades-geometricas       0.42  18.93   1620
CG   pagina-com-videos-sobre-curvas-parametricas- html  hermite                    representacao-de-curvas-pa  0.13   4.84   1745
CG   pagina-com-videos-sobre-manipulacao-de-image html  segmentacao                cores-e-tipos-de-imagens    0.77   4.46   1151
CG   paginas-com-videos-sobre-modelagem-geometric html  geometria-solida-construti tecnicas-de-modelagem-3d    0.33   8.58   1463
CG   pagina-com-videos-sobre-visualizacao-3d-35a8 html  paralela                   pipeline-de-visualizacao-3  0.28  12.40   2013
```
Os dois `exercicios-teoricos-...` são materiais distintos com o mesmo prefixo. "(vazio)" no gold = a subunidade certa é
nenhuma; o motor devia se abster. Unidade, os 2 erros confiantes (novos; em 08/09 eram 0): SO `lista-exercicios-p1` e
`lista-exercicios-p1-gabarito`, pdf, predito unidade-02-gerencia-do-processador, gold unidade-03-programacao-concorrente,
`unit_match_confidence` 0,24 e 0,19.

Leitura minha (HIPÓTESE): CG concentra 11 dos 18; 7 são páginas HTML curtas com `winner_score` 1,3–4,8, e `desenho-de-linhas`
é ímã em 4 delas; é o caso "alias casando por acaso em texto curto" que o plano previa. Os 3 do ES2 são vizinhos semânticos
do gold (tópico "estudo de caso" × tópico geral). `tiposindutivos` e `pagina-instanciamento` mostram que a confiança
(margem) pode ser alta com score ínfimo: a margem não sabe que o vencedor é fraco.

## 4. Item 1.2 — varredura do limiar contra o gold (MEDIDO, `c1-3/varre_limiar_subunidade_11-09.log`, 0 chamadas)

Regra simulada: material confiante, com subunidade gravada, e (condição) → vai para a fila. Precisão = certos/(certos+errados)
entre os que ficam confiantes. "fila +" conta sobre os 348 materiais dos 8 tutores.

| regra | erros pegos /18 | acertos que vão para a fila /174 | fila + (348) | precisão | fila/100 |
|---|---|---|---|---|---|
| hoje | 0 | 0 | 0 | 90,6% | 22,4 |
| conf < 0,25 | 3 | 5 | 17 | 91,8% | 27,3 |
| conf < 0,30 | 8 | 8 | 26 | 94,3% | 29,9 |
| conf < 0,35 | 10 | 11 | 33 | 95,3% | 31,9 |
| conf < 0,40 | 10 | 18 | 45 | 95,1% | 35,3 |
| conf < 0,50 | 12 | 28 | 66 | 96,1% | 41,4 |
| score < 1,5 | 5 | 13 | 24 | 92,5% | 29,3 |
| score < 2,0 | 5 | 14 | 25 | 92,5% | 29,6 |
| conf < 0,30 ou score < 1,5 | 10 | 21 | 46 | 95,0% | 35,6 |
| conf < 0,35 ou score < 1,5 | 12 | 24 | 51 | 96,2% | 37,1 |

O gold entrou uma vez, aqui, como o plano manda. O item 1.3 (regra no motor: subunidade fraca cai na fila) só entra se o
usuário aceitar o crescimento da fila; candidatos: `conf < 0,30` ou `conf < 0,35`.

## 5. Perguntas, em ordem

1. **O que ficou de fora.** Nos 18 e nos 2 de unidade, há padrão que eu não nomeei? Em especial: os 4 com gold vazio (o motor
   não tem "abster-se" como decisão além do `SUBUNIT_TAG`); os HTML curtos do CG; a margem relativa como sinal quando o
   `winner_score` é ínfimo (`tiposindutivos` 0,12 com conf 0,86).
2. **A varredura está bem desenhada?** Calibrar o limiar no mesmo gold que mede é ajuste ao gold; o que invalidaria a
   escolha de 0,30/0,35 num curso novo? Há regra melhor que um limiar em `conf`, usando só o que o manifest já guarda
   (`conf`, `winner_score`, `reasons`, tipo, tamanho do texto), sem gold?
3. **Unidade.** Os 2 erros novos do SO têm `unit_match_confidence` < 0,30; um limiar de unidade vale a pena ou é ruído de 2?
4. **Gate.** Com 90,6% já batido pelo trabalho de acurácia, a Fase 1 fecha, ou há razão medível para o 1.3 entrar mesmo assim?
5. **Risco.** O que nesta medição pode estar errado (seleção, definição de "confiante", `sync_changed`, materiais sem
   subunidade gravada)?
