# Brief para segunda opinião (Codex astra, read-only) — regime CRU do motor (sem LLM): partida, teto e o que atacar, 2026-09-12

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`. Sua revisão das runs do FR (hoje) já está incorporada.

## 1. O pedido e o momento

O usuário quer **melhorar o regime cru (sem LLM) e o "só Datalab"** antes de trazer outras engines de extração (MinerU e
derivados). Pediu que você analise o diagnóstico e o plano ANTES de medirmos: padrões nos erros, o que estamos perdendo, se o
raciocínio do teto está certo, e por onde atacar.

Vocabulário: subunidade = subtópico do plano de ensino dentro da unidade; "cru" = motor determinístico sem vocabulário
compilado por LLM, sem voter, sem resumo de código por LLM (o resumo já é determinístico desde 11/09); a curadoria humana
(sidecar manual, pinos) foi MANTIDA no regime "sem LLM" abaixo; "só código" tira tudo e deixa só o rótulo do plano.

## 2. Partida (MEDIDO hoje, `c1-3/replay_regime_cru_12-09.{py,log}`; replay igual ao produto, modo com, 0 chamadas; régua 251)
```
MF   n= 58 produto  55 ( 39 prim) · sem LLM  43 ( 23 prim) · so codigo  31 ( 24 prim)
SO   n= 15 produto  15 ( 14 prim) · sem LLM   9 (  8 prim) · so codigo   5 (  4 prim)
IA   n= 39 produto  36 ( 36 prim) · sem LLM   5 (  4 prim) · so codigo   6 (  4 prim)
ES2  n= 28 produto  25 ( 23 prim) · sem LLM  15 ( 13 prim) · so codigo   9 (  9 prim)
TCC  n= 11 produto  10 (  8 prim) · sem LLM   8 (  6 prim) · so codigo   8 (  5 prim)
CG   n= 82 produto  58 ( 44 prim) · sem LLM  52 ( 37 prim) · so codigo  49 ( 34 prim)
FR   n= 18 produto  18 ( 16 prim) · sem LLM   7 (  6 prim) · so codigo   7 (  6 prim)
TOTAL /251: {'produto': '217 aceito · 180 prim', 'sem_llm': '139 aceito · 97 prim', 'so_codigo': '115 aceito · 86 prim'}
```
Os 112 erros do regime sem LLM: 95 trocados e 17 vazios; **79 o produto acerta** (via vocab LLM) e 33 ninguém acerta. Por curso:
MF 15 (3 vazio), SO 6, IA 34 (0 vazio, 34 trocados), ES2 13 (5 vazio), TCC 3, CG 30 (7 vazio; 23 o produto também erra), FR 11.

## 3. Os 112 erros, material a material (MEDIDO; `sem LLM` = predição do cru, `produto` = predição atual, `produto_ok` = o produto acerta)
```
curso material                                       sem LLM                        produto                        produto_ok
MF   archive-of-formal-proofs-355fb8                abordagens-para-verificacao-fo abordagens-para-verificacao-fo False
MF   logicapredicados-semantica                     especificacao-de-funcoes-recur fundamentos-de-logica-de-prime True
MF   logicaproposicional-sintaxe                    especificacao-de-funcoes-recur linguagens-de-especificacao-e- True
MF   revisao                                        especificacao-de-conjuntos-ind sistemas-formais               True
MF   exerciciosespecificacao-respostas              especificacao-de-funcoes-recur linguagens-de-especificacao-e- True
MF   exerciciosespecificacao                        (vazio)                        linguagens-de-especificacao-e- True
MF   logicaproposicional-semantica                  (vazio)                        linguagens-de-especificacao-e- True
MF   arvores                                        abordagens-para-verificacao-fo provadores-de-teoremas         True
MF   exemplos                                       exemplos-de-aplicacoes         exemplos-de-aplicacoes         False
MF   intro                                          abordagens-para-verificacao-fo especificacao-de-conjuntos-ind True
MF   listas                                         abordagens-para-verificacao-fo provadores-de-teoremas         True
MF   provas                                         abordagens-para-verificacao-fo provadores-de-teoremas         True
MF   hoare                                          correcao-parcial-e-total       logica-de-hoare                True
MF   terminacao                                     (vazio)                        correcao-parcial-e-total       True
MF   tiposindutivos                                 verificacao-de-programas       verificacao-de-programas       False
SO   1903-estruturas-de-controle                    escalonamento                  conceitos-basicos              True
SO   3103-threads                                   escalonamento                  conceitos-basicos              True
SO   exercicios                                     (vazio)                        algoritmos-de-escalonamento    True
SO   exemplo-threads-em-c-exemplo1                  escalonamento                  conceitos-basicos              True
SO   exemplo-threads-em-c-exemplo2                  escalonamento                  conceitos-basicos              True
SO   exemplo-threads-em-c-exemplo3                  escalonamento                  conceitos-basicos              True
IA   algoritmo-de-classificacao-k-nn                introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   exemplo-com-k-nn                               introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   exemplo-2-k-nn-com-iriscsv-mais-completo       introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   exemplo-de-programa-com-k-nn-em-java           introducao-ao-aprendizado-de-m introducao-ao-aprendizado-de-m False
IA   artigo-usando-k-nn-em-texto                    introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   k-nn-para-classificacao-exemplo-cardio         introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   k-nn-para-regressao-exemplo-imc                introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   introducao-a-redes-neurais                     introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron                                introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron-classificacao-de-cliente       introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron-classificacao-planta-iris      introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron-exemplo-atualizado             introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron-or-em-python                   introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron-reconhecendo-letras            introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   exercicio-2-solucao-com-rede-perceptron-atuali introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   mlp                                            introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   mlp-xoripynb                                   introducao-ao-aprendizado-de-m (vazio)                        False
IA   mlp-classificacao-iris-atualizado              introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   mlp-regressao-cardio                           introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   rede-perceptron-e-equacao-de-reta              introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   xor-backpropagation-em-python                  introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   mlp-classificacao-inadimplencia-normalizacao-e introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   como-analisar-resultados-acc-pr-re-e-f1        introducao-ao-aprendizado-de-m metricas-de-avaliacao          True
IA   arvores-de-decisao                             introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   exemplo-1-arvores-de-decisao-classificacao-pla introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   exemplo-2-arvores-de-decisao-regressao-diabete introducao-ao-aprendizado-de-m modelos-preditivos             True
IA   aula-sobre-agrupamento-parte-1-particional     introducao-ao-aprendizado-de-m modelos-descritivos            True
IA   agrupamento-usando-k-means-exemplo-1-ipynb     introducao-ao-aprendizado-de-m modelos-descritivos            True
IA   agrupamento-usando-k-means-exemplo-2-ipynb     introducao-ao-aprendizado-de-m modelos-descritivos            True
IA   artigo-usando-agrupamento                      introducao-ao-aprendizado-de-m modelos-descritivos            True
IA   survey-on-clustering                           introducao-ao-aprendizado-de-m modelos-descritivos            True
IA   aula-sobre-agrupamento-parte-2-hierarquico     introducao-ao-aprendizado-de-m introducao-ao-aprendizado-de-m False
IA   agrupamento-hierarquico-exemplo-1              introducao-ao-aprendizado-de-m modelos-descritivos            True
IA   agrupamento-hierarquico-exemplo-2-use-o-datase introducao-ao-aprendizado-de-m modelos-descritivos            True
ES2  revisaoarquiteturapadroes                      (vazio)                        conceito-de-arquitetura-de-sof True
ES2  microsservicos                                 estilos-e-padroes-arquiteturai orientada-a-microsservicos     True
ES2  roteiro1                                       (vazio)                        estudo-de-caso-arquitetura-ori True
ES2  devops                                         integracao-continua-ci         gerenciamento-da-configuracao  True
ES2  kubernetes                                     (vazio)                        plataformas-de-devops          True
ES2  microsservicos2                                arquitetura-serverless         orientada-a-microsservicos     False
ES2  microsservicos3                                estilos-e-padroes-arquiteturai estilos-e-padroes-arquiteturai False
ES2  roteiro2-nameserver                            cliente-servidor               estudo-de-caso-arquitetura-ori True
ES2  roteiro3-gateway                               cliente-servidor               cliente-servidor               False
ES2  roteiro2                                       (vazio)                        estudo-de-caso-arquitetura-ori True
ES2  roteiro3                                       (vazio)                        estudo-de-caso-arquitetura-ori True
ES2  microsservicos6                                gerenciamento-da-configuracao  estudo-de-caso-integracao-e-im True
ES2  roteiro8-autenticacao-autorizacao              gerenciamento-da-configuracao  estudo-de-caso-integracao-e-im True
TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hier maquinas-de-turing             maquinas-de-turing             False
TCC  aula-09-variacoes-de-maquinas-de-turing        maquinas-de-turing             variacoes-de-maquinas-de-turin True
TCC  aula-10-linguagens-reconhecıveis-e-linguagens- maquinas-de-turing             linguagens-reconheciveis-e-dec True
CG   morfologiamatematicapptx                       (vazio)                        (vazio)                        False
CG   atividade                                      (vazio)                        conceito-de-camera-sintetica   True
CG   basico3d-py                                    perspectiva                    perspectiva                    False
CG   opengl3d                                       perspectiva                    conceito-de-camera-sintetica   True
CG   opengl3dcpp-vdi                                (vazio)                        paralela                       False
CG   opengl3dcpp                                    (vazio)                        paralela                       False
CG   vis3d                                          (vazio)                        paralela                       True
CG   programabasico3d                               metodos-de-sombreamento-flat-g metodos-de-sombreamento-flat-g False
CG   exercicio-com-animacao                         algoritmos-de-poligonos        (vazio)                        False
CG   matematica                                     (vazio)                        entidades-geometricas          True
CG   animacao-v2                                    desenho-de-linhas              desenho-de-linhas              False
CG   exercicios-teoricos-sobre-processo-de-visualiz desenho-de-linhas              desenho-de-linhas              False
CG   instanciamento                                 sistema-de-coordenadas-cartesi 2d-3d-mao-direita-e-mao-esquer False
CG   mapeamento                                     recorte                        sistema-de-coordenadas-cartesi True
CG   pagina-com-videos-sobre-instanciamento         desenho-de-linhas              desenho-de-linhas              False
CG   transformacoesgeometricas                      desenho-de-linhas              desenho-de-linhas              False
CG   transformacoesgl                               sistema-de-coordenadas-cartesi sistema-de-coordenadas-cartesi False
CG   bezier-python                                  tecnicas-de-modelagem-3d       tecnicas-de-modelagem-3d       False
CG   exercicios-sobre-curvas                        hermite                        hermite                        False
CG   remocaoderuido                                 cores-e-tipos-de-imagens       filtros                        True
CG   introducaoprocimg                              segmentacao                    filtros                        True
CG   exercicios-sobre-curvas-html                   hermite                        hermite                        False
CG   exercicios-teoricos-sobre-processo-de-visualiz desenho-de-linhas              desenho-de-linhas              False
CG   pagina-com-videos-sobre-fundamentos-matematico algoritmos-de-poligonos        algoritmos-de-poligonos        False
CG   pagina-com-videos-sobre-mapeamento-9f410e      (vazio)                        (vazio)                        False
CG   video-sobre-mapeamento-em-opengl-1dad3c        2d-3d-mao-direita-e-mao-esquer 2d-3d-mao-direita-e-mao-esquer False
CG   pagina-com-videos-sobre-curvas-parametricas-63 hermite                        hermite                        False
CG   pagina-com-videos-sobre-manipulacao-de-imagens segmentacao                    segmentacao                    False
CG   paginas-com-videos-sobre-modelagem-geometrica- geometria-solida-construtiva-c geometria-solida-construtiva-c False
CG   pagina-com-videos-sobre-visualizacao-3d-35a833 paralela                       paralela                       False
FR   01-protocolos-de-rede                          modelos-osi-e-tcpip            conceito-de-protocolo-de-redes True
FR   03-tipos-de-redes                              modelos-osi-e-tcpip            conceito-de-protocolo-de-redes True
FR   04-camada-de-aplicacao                         protocolos-de-aplicacao-para-o paradigmas-clienteservidor-e-p True
FR   04-protocolo-http                              paradigmas-clienteservidor-e-p protocolos-de-aplicacao-para-o True
FR   05-protocolo-dns                               protocolos-de-aplicacao-para-o protocolos-de-aplicacao-para-i True
FR   unidade2-exercicios-http                       paradigmas-clienteservidor-e-p protocolos-de-aplicacao-para-o True
FR   08-desenvolvimento-de-aplicacoes               (vazio)                        implementacao-de-sockets       True
FR   udp-example-c                                  paradigmas-clienteservidor-e-p implementacao-de-sockets       True
FR   udp-example-java                               paradigmas-clienteservidor-e-p implementacao-de-sockets       True
FR   tcp-chat-c                                     paradigmas-clienteservidor-e-p implementacao-de-sockets       True
FR   tcp-example                                    paradigmas-clienteservidor-e-p implementacao-de-sockets       True
```

## 4. O teto das fontes do professor (MEDIDO em 08/09, `c1-3/mede_fontes_do_professor.{py,log}`; 222 materiais com gold daquela data: CG 72, sem FR)

Definição (docstring do script): para cada material com gold de subunidade, cada fonte "nomeia" o subtópico certo se a frase do
rótulo está contida nela ou os tokens específicos do rótulo estão contidos, sem genéricos (critério do próprio motor,
`resolver_apply._secao_nomeia_subtopico`), restrito aos tópicos da unidade do material. PLANO = o rótulo do tópico (ou alias vindo
do plano) aparece no TEXTO do material · SARC = o label da sessão do SARC do bloco do material · SECAO = a seção do Moodle · TITULO =
título do material + label do Moodle · HEADINGS = headings do markdown · AL-CURADO = alias do sidecar curado (em 08/09 ainda derivado
do gold em IA/SO/ES2/TCC: contaminado) · AL-HEADING = alias vindo de heading · SEM-CURADO = qualquer fonte exceto AL-CURADO ·
QUALQUER = qualquer coluna · NENHUMA = nenhuma.
```
O SUBTOPICO CERTO E ALCANCAVEL POR CADA FONTE DO PROFESSOR? (% dos materiais com gold)
         n      PLANO  AL-CURADO  AL-HEADIN       SARC      SECAO     TITULO   HEADINGS  PLANO+SAR  SEM-CURAD   QUALQUER    NENHUMA
SO      15    4   27%    9   60%    2   13%    0    0%    4   27%    6   40%    9   60%    9   60%   12   80%   12   80%    3   20%
IA      39    0    0%   38   97%    1    3%   37   95%    2    5%   37   95%   23   59%   38   97%   39  100%   39  100%    0    0%
ES2     28    2    7%   24   86%    4   14%   16   57%   13   46%    9   32%   13   46%   23   82%   26   93%   28  100%    0    0%
TCC     10    2   20%    3   30%    7   70%    5   50%    4   40%    5   50%    5   50%    8   80%    9   90%   10  100%    0    0%
MF      58    4    7%    0    0%   38   66%    6   10%    4    7%   18   31%   18   31%   25   43%   41   71%   41   71%   17   29%
CG      72   15   21%    0    0%   24   33%   24   33%   17   24%   19   26%   14   19%   35   49%   44   61%   44   61%   28   39%
TOT    222   27   12%   74   33%   76   34%   88   40%   44   20%   94   42%   82   37%  138   62%  171   77%  174   78%   48   22%
```
Leitura minha: o cru pode subir de 55% até no máximo ~77% (SEM-CURADO) explorando o que o professor escreveu; os 22% de NENHUMA
(MF 29%, CG 39%) só entram por conhecimento de fora (vocab LLM hoje, ou léxico embarcado). **IA: o SARC nomeia o subtópico certo
em 95% e o título em 95%, e o cru faz 5/39** — o motor não usa o label da sessão do SARC como evidência de SUBUNIDADE do material
(SARC alimenta só o alinhamento bloco → unidade). Em 05/09 "alias = label de sessão do SARC" deu 0 efeito nos 93, mas virou alias
de TEXTO (o material teria de repetir as palavras do SARC); a alavanca posicional (material herda o subtópico que a sessão do SARC
do seu bloco nomeia) nunca foi medida.

## 5. Histórico do que já foi medido no cru (MEDIDO, Placar do Motor e tracker)

- Vocab determinístico por co-heading em vez de LLM: 26 → 31/93 (02/09); LLM no IA: 5 → 37/39. Refutado como substituto.
- Decomposição de rótulos compostos ("Bézier e Algoritmo de Casteljau" → "Bézier"; "Algoritmos de X" → "X"), 2ª passada, df ≤ 25%: entrou, CG 49 → 54 (06/09).
- Título nomeia outro subtópico e não o vencedor → vence a decisão confiante: entrou, +2 (06/09).
- Seção do Moodle nomeia exatamente um subtópico e nada decidiu → decide: entrou, +3; variantes que sobrepõem decisão confiante −13 (06/09).
- Propagação por headings (2ª passada, só onde a 1ª não decidiu): entrou, +5.
- Refutados: IDF intra-unidade (0 · +1/−5 · 0); código herda pelo nome do card / pelo irmão (0/−23 · 0/−2); alias = label de sessão do SARC (0 nos 93); similaridade nome × vocab (Jaccard/difflib); piso de score em 4 formas; irmãos empatados → pai (−25); título do vídeo no lugar do hash (0/−2).
- FR do zero hoje (`c1-3/mede_fr_sem_gold_run*_12-09.log`): cru 6/18 primário, só Datalab 6/18, cru + vocab 16/18, Datalab + vocab 17/18, produto 16/18; unidade 19/19 pela seção "U<n>" em todos (reprodução do sinal). Datalab = 0 sem vocab, +1 com.

## 6. O plano que eu propus ao usuário (HIPÓTESE, ainda não aprovado)

1. Triagem dos 79 recuperáveis por fonte que nomeia o gold (título, seção, SARC, headings) versus por que o cru erra mesmo assim
   (token genérico, tópico sem alias vencendo por rótulo, empate), remedindo o teto no gold atual (251, com FR e CG 82).
2. Alavancas determinísticas medidas no replay, uma a uma, ganho e perda nos 7 cursos: SARC posicional (material herda o subtópico
   nomeado pela sessão do bloco); peso do título/label do Moodle quando nomeiam subtópico; heading que nomeia subtópico irmão.
   Entra o que der ≥ +3 sem perda.
3. Léxico de domínio embarcado para os 22%: vocabulário por área construído uma vez fora do curso, determinístico em runtime.
   Teste barato: o vocab compilado do LR aplicado ao FR cru e vice-versa (mesma área), 0 chamadas.
4. "Só Datalab" nos 8: replay lendo `advanced_markdown` onde existe (163 materiais), por tipo, vocab fixo, voter off.
5. Gate 2 por alavanca.

## 7. Perguntas, em ordem

1. **Padrões nos 112.** Olhando o §3: que famílias você vê que eu não nomeei (por curso, por tipo de material, por par predito×gold,
   por "vazio" × "trocado")? Há erros que uma regra determinística já existente deveria pegar e não pega (título, seção, decomposição)?
2. **O teto.** O raciocínio "cru ≤ 77% por construção; 22% só com conhecimento de fora" está certo? O que o critério de "nomeia"
   (frase/tokens contidos, sem genéricos) esconde: radical, sinônimo dentro do próprio plano, tokens genéricos que não deviam ser?
   Que fonte do professor ficou de fora (ementa, bibliografia, nome de arquivo, pasta do stash, ordem no Moodle)?
3. **SARC posicional.** É a alavanca certa para IA (95% nomeável, 5/39 no cru)? Como medir sem circularidade, dado que o SARC já
   decide o bloco e o bloco decide a unidade? Que perda esperar em cursos onde a sessão do SARC nomeia o pai e o gold quer o filho?
4. **Ordem de ataque.** Entre SARC posicional, título/label com peso, headings irmãos, léxico embarcado e "só Datalab nos 8": qual
   primeiro, e qual você descartaria sem medir?
5. **Léxico embarcado.** O teste LR ↔ FR (mesma área) mede o que importa? Que desenho evita virar "vocab LLM com outro nome"?
6. **Risco.** O que nesta análise pode estar errado: teto de 08/09 numa régua diferente (222 × 251); "sem LLM" mantendo a curadoria
   humana; replay ≠ produto em 2 materiais do CG; contar "aceito" e não "primário".
