# W-AA — resultado: seleção por função e extensão (S) e geração local por subordinação (G), 23/09/2026

Execução autorizada pelo usuário em 23/09 (literal: `_harness-2026-09-04/c1-3/waa_pedido_execucao_23-09.md`). Desenho,
definições e ajustes de interpretação registrados **antes** da execução: `2026-09-23-waa-desenho.md` §3 e §7.
Nada em `src/`, régua, defaults ou configuração persistida foi alterado; sem commit do código; sem implementação.

| artefato (`_harness-2026-09-04/c1-3/`) | versão |
|---|---|
| `waa_selecao_geracao_23-09.py` (medição; docstring = definições) | declaração sha256 `6d5dadd8…` |
| `waa_selecao_geracao_23-09.json` (dados por ID) | sha256 `00aea77b…` |
| `waa_selecao_geracao_23-09.md` (tabelas geradas) | sha256 `115abfb9…` |
| `.frzero/waa_captura_bracos_23-09.json` (decisões dos 3 braços, congeladas antes do gold) | conteúdo `b265091e…` |

**Controles de execução:**
- **D9 efetivo:** o harness chama `apply_anchor_engine(enabled=True)` (`replay_bloco_21-09.py:48`) e 337 dos 350 materiais
  receberam bloco temporal em todos os braços. Os 13 restantes seguem pelo fallback já descrito na issue #65.
- **Demais eixos:** bloco e unidade idênticos por ID nos três braços.
- **Unidade vista pelo seletor:** igual à da base em todas as chamadas.

## Resultado

**Nenhum braço passa o aceite.**

| braço | MF | SO | IA | ES2 | TCC | CG | FR | total primária | aceita | ganhos / perdas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| base (W-Z2) | 25 | 7 | 4 | 7 | 7 | 30 | 6 | **86** | 109 | — |
| A = S | 23 | 7 | 4 | 6 | 6 | 31 | 6 | **83** | 109 | +1 / −4 |
| B' = G | 13 | 6 | 15 | 1 | 6 | 29 | 6 | **76** | 98 | +19 / −29 |
| B = G + S | 11 | 6 | 15 | 0 | 6 | 29 | 6 | **73** | 96 | +20 / −33 |

**Leitura fatorial.** Efeito de S −3, efeito de G −10, interação 0, B − base −13. Nenhuma peça tem saldo positivo, nem
isolada nem combinada; não há sinergia que compense (ajuste de interpretação 1).

| braço | alteradas com gold | precisão das alteradas | alteradas sem gold | abstenção → certa | abstenção → errada | decisão → abstenção errada | cursos que regridem |
|---|---:|---:|---:|---:|---:|---:|---|
| A | 8 | 12,5 % | 4 | 1 | 2 | 0 | MF, ES2, TCC |
| B' | 121 | 15,7 % | 32 | 1 | 21 | 2 | MF, SO, ES2, TCC, CG |
| B | 130 | 15,4 % | 32 | 1 | 21 | 2 | MF, SO, ES2, TCC, CG |

Correções e perdas por ID estão em `waa_selecao_geracao_23-09.md` e no JSON (`mudancas`, `explicacao_ganhos_perdas`).

**Teste de sinal (exploratório, separado da política):** nos 251, a ordem atual põe o gold em 1º em 64 materiais; a ordem de
S, em 61. G liga alguma expressão do material ao tópico-gold em 37 dos 251.

## Por que S falhou

- **Quase não age.** Dos 341 elegíveis, 267 têm seções por heading, 4 por itens e 70 nenhuma. S só decide quando a frase exata
  de algum tópico aparece numa seção principal: aconteceu em 97 materiais, e mudou a decisão da 1ª passada em 9.
- **O papel da seção quase nunca está marcado no rótulo.** Das 8.407 seções, só 230 (2,7 %) têm rótulo de revisão, exemplo,
  comparação ou índice. A função da ocorrência, nesses materiais, não aparece nos headings.
- **Extensão favorece o assunto de fundo.** Nas 4 perdas, S escolheu o tópico que atravessa o material:
  - TCC `aula-10…`: "máquinas de Turing" em 29 seções contra o primário "linguagens reconhecíveis e decidíveis";
  - ES2 `web`: "camadas" em 6 seções contra "cliente-servidor" em 3;
  - MF `conjuntosindutivos` e `logicadehoare`: o gold não tem frase exata em nenhuma seção.

  O único ganho (CG `vis3d`) desfez um empate exato do seletor atual.
- **Pontos pedidos:**
  - *Perda de evidência quando exemplo, comparação ou revisão é o assunto principal:* em nenhuma das 97 ações o gold ocorria
    só em seção auxiliar. O rebaixamento de papel não causou perda; ele quase não disparou.
  - *Seções equivalentes contadas em dobro:* existe. Em 24 das 97 ações a extensão do escolhido inclui rótulos repetidos (slide
    com o mesmo título). Nenhuma das 4 perdas depende disso.
  - *Efeito indireto da 2ª passada:* 2 perdas de A vieram só da 2ª passada (a decisão da 1ª passada era igual à da base).

## Por que G falhou

- **Pares locais:** 742 pares material-tópico (P1 728, P4 14), sendo 207 candidatos novos e 535 reforços.
- **G acerta só quando injeta o tópico certo:** 17 dos 19 ganhos. Quando injeta outro tópico, perde: 25 das 29 perdas
  (MF: 14 perdas, 7 para "abordagens para verificação formal" e 5 para "especificação de conjuntos indutivos"; ES2
  "gerenciamento da configuração" em 4 roteiros; CG "segmentação" em 2 materiais de imagem). As outras 4 perdas vêm só da
  2ª passada.
- **Os ganhos do IA (4 → 15) não demonstram a relação categoria → algoritmo.** Pela proveniência, as expressões ligadas são
  genéricas e casam por radical de 6 letras com um artigo em inglês. Exemplos: "generalização" ~ "**General Terms**",
  "predição" ~ "Noun classification from predicate-argument…", "categ" ~ "Categories and Subject Descriptors". Quase todas
  vêm de dois documentos (`artigo-usando-agrupamento`, `caracteristicas-dos-dados`). O ganho existe porque quase todo material
  de ML do IA tem gold "modelos preditivos/descritivos": qualquer injeção desse tópico acerta pela frequência da classe, não
  pela relação.
- **Unicidade só pela unidade prevista (ponto pedido):** 373 dos 742 pares são únicos só por causa da restrição à unidade.
  Entre os pares que decidiram o resultado, isso vale para 13 dos 17 ganhos e 17 das 25 perdas. A restrição não discrimina.
- **Efeito indireto da 2ª passada:** em B', 2 ganhos e 4 perdas mudaram só na 2ª passada. Nos quatro materiais de recursão do
  MF sem par local, a perda vem da troca de doadores.

## Conclusão (limitada aos mecanismos examinados)

- **S**, na forma testada (extensão por frase exata em seções markdown, papel pelo rótulo da seção com léxico fixo), não
  melhora a seleção: sinal pior que a ordem atual (61 × 64) e saldo −3. A função da ocorrência não está marcada nos headings
  desses materiais, e a extensão confunde assunto principal com assunto de fundo.
- **G**, na forma testada (relações de subordinação P1/P4 do índice do W-U, chave por radical de 6 letras, exclusividade na
  unidade prevista, alias local), não gera candidatos com precisão útil: 15,7 % de acerto nas decisões alteradas, saldo −10.
  Os ganhos aparentes do IA são colisões de radical sobre a classe majoritária do gold.
- Pela leitura decidida antes de rodar ("nenhum passa"), as **fontes léxico-estruturais examinadas** estão esgotadas para a
  subunidade. Isso não vale para qualquer mecanismo possível sobre o pacote.
- Os 218/251 do desenho eram o alcance ideal dos grupos-alvo sob as condições da §1 do desenho (conversão total, zero perda),
  não teto universal.
- Rotulação pelo professor não volta como requisito.

**Direções que ficam para decisão do usuário (nenhuma autorizada):**
1. **Regime separado de conhecimento externo** para a relação termo → tópico (tesauro por área versionado, ou compilação
   de vocabulário), com medição própria e guarda contra ajuste ao benchmark (o braço V de 13/09 foi dirigido por gold).
2. **Aceitar e publicar o teto medido do cru na subunidade**, por curso, mantendo a meta nos regimes em que ela é atingível.
3. **Outro mecanismo sobre o pacote**, com hipótese nova de fato. Não recomendo abrir sem uma fonte de sinal que as medições
   ainda não mostraram: W-U, W-Z2 e W-AA apontam relação existente, mas ambígua, e papel não marcado.

## Régua CG: evidência dos cinco casos (sem decisão; régua congelada)

**Premissa comum.**
- Em 06/09 a subunidade-gold foi anotada vazia sob a unidade u04. Nota da régua: "u04 pelo oráculo (SARC/Moodle 'Processo de
  Visualização 2D'); o plano põe transformações/instanciamento em u05: u04 não tem subtópico → vazio". A coluna `unit_slug` do
  `subunit_gt_CG.csv` ainda diz u04.
- Em 22/09 a régua v2 passou a unidade para u05 "pelo conteúdo (5.1 transformações geométricas)" (notas de
  `material_gt_CG.csv`), sem revisar a subunidade.
- O vazio foi, portanto, **intencional sob u04**, e há **inconsistência de migração** documentada nos cinco.
- Na taxonomia, a u05 tem 5.1 "Transformações Geométricas e coordenadas homogêneas 2D" e 5.4 "Composição de transformações
  2D"; a u07 tem 7.2.4 "Instanciamento de Primitivas".

| material | o que o material mostra | leitura possível sob u05 |
|---|---|---|
| `instanciamento` (PDF, 13 mil caracteres) | headings "3 TRANSFORMAÇÕES GEOMÉTRICAS", "3.1 Translação", "3.2 Escala", "3.3 Rotação", "3.4 Matrizes de transformação geométrica" | vazio ficaria **incompleto**: o conteúdo nomeia 5.1 |
| `transformacoesgl` (HTML) | "transformações", `glScalef`, transformações "cumulativas", "coordenadas" | **incompleto**, com primário entre 5.1 e 5.4 (cumulativas = composição) |
| `transformacoesgeometricas` (zip; resumo determinístico) | "Exemplo de Código para Instanciamento", "Modelagem de personagens com instância" | **ambíguo**: 5.1 ou 7.2.4, que é de outra unidade |
| `pagina-com-videos-sobre-instanciamento` (HTML com código) | `glPushMatrix`/`glPopMatrix`, `Modelo`, `Temporizador` | **ambíguo**: 5.1/5.4 ou 7.2.4 |
| `animacao-v2` (zip; resumo determinístico) | "Exemplo de Código para Animação", instância, polígono, temporizador | vazio **pode seguir intencional**: o plano não tem tópico de animação |

Qualquer correção deve sair como versão separada da régua, com baseline e candidatos reavaliados sob a mesma régua e sem
ajustar regras. Não decidi com base no oráculo nem no W-AA.
