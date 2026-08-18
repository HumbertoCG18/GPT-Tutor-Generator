# Medição — fix de perda de tópicos do plano de ensino (sandbox, 5 cursos)

date: 2026-08-18
código medido: working tree de `feat/motor-atribuicao` sobre `be62db9`
driver: `scripts/measure_taxonomy_fix.py <SIGLA> <SANDBOX_DIR>` (reusa a mecânica de
`measure_flip`: snapshot → `analyze` com gold de unidade, pinos e deltas)
sandboxes: cópia `robocopy /E /XD .git` dos 5 repos-tutor de produção

## Gates

| curso | tópicos na taxonomia | gold de unidade | régua por material | confiante-e-errado | pinos violados |
|---|---|---|---|---|---|
| SO | 31 → **36** | 9/11 = | 27/38 = | 0 → 0 | 0/4 |
| TCC | 14 → **26** | 13/13 = | 18/25 = | **2 → 1** | 0/3 |
| ES2 | 20 → **21** | 7/7 = | 22/28 = | 0 → 0 | 0/1 |
| MF | 23 → 23 | 12/14 = | 63/66 = | 1 → 1 | 0/18 |
| IA | 19 → 19 | 9/10 = | 43/44 = | 0 → 0 | 0/4 |

Nenhuma régua regride. Nenhum pino violado ou perdido. TCC melhora 1 confiante-e-errado.

## Atribuição isolada (worktree em `be62db9` vs working tree)

O reprocess aplica TUDO que está commitado e não foi para produção — inclusive o date-tier e o
`provider_ordinal` (item A do handoff). Para separar, o mesmo sandbox foi reprocessado a partir
de um worktree em `HEAD` e comparado campo a campo:

| curso | Δ bloco | Δ unit | Δ subunit |
|---|---|---|---|
| SO | **0** | 5 | 38 (21 são só renomeação de slug, 17 semânticas) |
| TCC | 3 | 1 | 12 semânticas |
| ES2 | **0** | 6 | 6 semânticas |
| MF | 0 | 1 | 1 |
| IA | 5 | 3 | 4 |

**Renomeação de slug de subtópico:** com o código numérico agora extraído, o label é limpo antes
de virar slug — `33-algoritmos-de-escalonamento` passa a ser `algoritmos-de-escalonamento`.
Afeta só o SO (único plano com numeração em negrito). Verificado: os únicos arquivos que carregam
os slugs antigos são **gerados** (`.content_taxonomy.json`, `.tag_catalog.json`,
`.timeline_index.json`, `FILE_MAP.md`, `manifest.json`, `.deeptutor/`), todos reescritos no
reprocess. Nenhum gold, sentinela ou curadoria manual depende deles.

**IA — as 5 mudanças de bloco não chegam ao tutor:** as 3 listas têm `temporal_block_id` com
método `disamb` e a busca informada tem `janela-1`; como `resolve_temporal_block` prioriza a
âncora, o `computed_block_id` alterado não muda o destino final. Sobram efeitos em unit/subunit.

O Δ bloco de 11 no SO visto no run completo é do date-tier/ordinal, **não** deste fix. Este fix
age onde deveria: unidade e subunidade.

## Investigação do ES2 (a fundo, 2026-08-18) — causa raiz era outra

O ES2 não regrediu por causa do tópico recuperado. O tópico `1.1 Conceito de arquitetura de
software` apenas **expôs um defeito latente do enriquecimento por headings**:

`build_content_taxonomy` anexa cada `strong_heading` como **alias** do tópico mais próximo. Os
headings coletados do ES2 incluem `ENGENHARIA DE SOFTWARE II ---` — o cabeçalho institucional de
TODO slide do curso — e `Trabalho FinalEngenharia de Software II`. Ambos viraram alias do tópico
novo, e com isso `engenharia`, `trabalho` e `finalengenharia` entraram nos `distinctive_tokens`
da unidade 01. Qualquer material do curso passou a casar com ela.

Evidência (score de `Kubernetes` por unidade, antes do segundo fix):

| taxonomia | u01 arquitetura | u02 devops | u03 testes |
|---|---|---|---|
| sem o 1.1 | 4.70 | **14.69** | 4.55 |
| com o 1.1 + alias institucional | 9.45 | 13.06 | 0.99 |

O próprio perfil semântico já marcava `engenharia-de-software-ii` em `generic_slug_blacklist`;
o bloco de enriquecimento é que nunca consultava essa lista. Correção: descartar heading cujo
slug está em `tag_generic_slugs` **ou** que contenha o nome do curso. Teste:
`test_heading_institucional_nao_vira_alias_de_topico`.

Depois da correção, `Kubernetes` volta para `unidade-02-devops`, `microsservicos6` para de mudar,
e `devops` (que estava SEM unidade) passa a ser atribuído à unidade 02.

## Mudanças de unidade causadas pelo fix (julgamento caso a caso, pós-correção)

**SO — 4 correções, todas em erros já catalogados** (handoff §B):
- `Exemplo threads em C - exemplo1/2/3`: `unidade-07-gerencia-de-entrada-e-saida` → `unidade-03-programacao-concorrente`
- `07.04 Exemplo threads em Java`: `unidade-04-deadlock` → `unidade-03-programacao-concorrente`
- causa: o tópico `4.1 Programas multithreads` voltou à unidade 03.
- `Exercícios P2` perde a unidade (`unidade-01` → vazio) — antes atribuía introdução sem sinal.

**TCC — 1 correção:**
- `Aula 14 - Problema da Correspondência de Post`: `unidade-04-hierarquia-de-classes` → `unidade-03-problemas-indecidiveis`. PCP é problema indecidível.

**ES2 — 6 movimentos, saldo positivo depois da correção do alias:**
- `devops`: SEM unidade → `unidade-02-devops` (ganho);
- `RevisaoArquiteturaPadroes`: subtópico `arquitetura-serverless` → `conceito-de-arquitetura-de-software` (ganho);
- `Roteiro8_autenticacao_autorizacao` (card `Microsserviços`): `testes-de-software` → arquitetura/`orientada-a-microsservicos` (ganho: testes estava claramente errado);
- `microsservicos3/4/5` (card `Microsserviços`): DevOps → arquitetura/`orientada-a-microsservicos` — plausível, o plano tem `1.3.4 Orientada a Microsserviços`;
- `t1_2026_1` (TDE, projeto extensionista): `testes-de-software` → arquitetura. Arbitrário nos dois lados, baixo impacto.

**TCC — os subtópicos recuperados corrigem o caso do handoff:**
- `Aula 16 - Classes de Problemas e Complexidade`: `tipos-de-problemas-computacionais` → `hierarquia-de-classes-de-complexidade`;
- `Aula 17 - NP-Completude` e `Cubic 3-Edge Coloring`: `complexidade-de-tempo-e-de-espaco` → `reducao-polinomial-de-problemas`;
- `Trabalho T2`: `classe-np` → `provas-de-np-completude`;
- `Aula 03/04 - Funções Recursivas Primitivas` e `T1`: `argumento-diagonal-de-cantor` → `funcoes-recursivas-primitivas-e-parciais`.

**MF:** `t2_2026_1` sai de sem-unidade para `unidade-02-verificacao-de-programas` (ganho).

**IA — misto:** `Introducao a redes neurais` vai de `solucao-de-problemas` para
`aprendizado-de-maquina` (ganho claro); `Visão Geral - Introdução e Histórico` perde
`aprendizado-de-maquina` e fica sem unidade (era errado, mas o certo seria `visao-geral`);
`Cap. sobre Algoritmos Geneticos` vai de `solucao-de-problemas` para `aprendizado-de-maquina`
(duvidoso).

## Buraco de medição (relevante para a fila)

Nenhuma régua atual mede `entry → unidade`. `eval_ground_truth` mede `entry → bloco temporal` e
`eval_units` mede `bloco → unidade`. Todo o efeito deste fix cai justamente no vão entre as duas,
então "não regrediu" é o máximo que os números atuais sustentam — o julgamento acima é qualitativo.
A régua de COBERTURA em construção (`scripts/eval_coverage.py`) mede exatamente esse eixo.


## Rodada 2 (mesmo dia): card do Moodle como sinal de unidade

Depois da medição acima, duas correções entraram e foram medidas juntas:

1. **`_topic_text` passa a tratar tópico-dict** (`{code, slug, label, aliases, ...}`), devolvendo o
   `label`. Defesa contra serialização do dict em `topic_phrases`. Medição: **neutra** nos 5 —
   o caminho de produção monta o índice de unidade a partir do `teaching_plan` (tuplas), não da
   taxonomia, então o defeito não estava ativo em produção. Registro de uma hipótese minha que a
   medição refutou.
2. **Frase igual ao título de OUTRA unidade é descartada do índice** — o glossário injetava na u01
   do MF duas frases `verificacao de programas`, que é o título da u02. Sozinho é neutro; com o
   card ativo, é o que impede o dano.
3. **Card (`source_section`) entra como sinal do eixo de unidade**: `card_text` nos sinais, peso
   1,5 quando o card casa o TÍTULO da unidade (os cards do MF nomeiam unidade: `Verificação de
   Programas`, `Provas por Indução`), 2,5 quando casa a frase de um tópico e 0,40 no overlap
   parcial. Só no nível de frase — card administrativo (`Informações Gerais`, 10x no SO) não casa
   nada e fica inerte. Teste garante que os scorers de bloco do motor não leem `card_text`.

### Histórico da tentativa (por que o card falhou na primeira versão)

Primeira versão do card (só contra tópicos, sem o filtro de título cruzado) **regrediu o MF**:
6 entries do card `Verificação de Programas` saíam de `unidade-02-verificacao-de-programas`.
Bissecção: com `card_text` apenas no dict de sinais (sem scorer lendo), MF volta a delta 1 — o
dano vinha do consumo. Causa: a u01 carregava duas frases `verificacao de programas` (do
glossário), então o card dava 2 × 2,5 = 5,0 para a unidade ERRADA e nada para a certa, cujo
título ele nomeava. Daí as duas correções: comparar o card contra o título da unidade e descartar
frase que é título de outra unidade.

### Gates da rodada 2 (5 cursos, sandbox)

| curso | gold de unidade | régua por material | conf-errado | pinos violados | Δ unit |
|---|---|---|---|---|---|
| SO | 9/11 = | 27/38 = | 0 → 0 | 0/4 | 5 |
| TCC | 13/13 = | 18/25 = | 2 → 1 | 0/3 | 1 |
| MF | 12/14 = | 63/66 = | 1 → 1 | 0/18 | 1 |
| IA | 9/10 = | 43/44 = | 0 → 0 | 0/4 | 7 |
| ES2 | 7/7 = | 22/28 = | 0 → 0 | 0/1 | 12 |

Suite: 1886 passed / 1 skipped.

### Julgamento caso a caso (card como evidência independente)

**Ganhos** — `devops` (ES2) sai de sem-unidade para DevOps; `t2_2026_1` (MF) idem para
verificação de programas; `programa-exemplo AG` e `Programas-exemplo HC, SA` (IA) saem de
sem-unidade para solução de problemas, coerentes com o card `Algoritmos de Busca`;
`Introducao a redes neurais` e os dois exemplos de k-NN (IA) vão para aprendizado de máquina;
`Roteiro8_autenticacao_autorizacao` (ES2) sai de `testes-de-software`; `microsservicos3/4/5`
(ES2) saem de DevOps para arquitetura — confirmado pelos headings do material
(`MICROSSERVIÇOS / Decisões Arquiteturais / Padrões de Projeto / API Gateway`).

**Neutros** — `Exercícios P2` (SO) perde a unidade: o card é `Informações Gerais`, administrativo.
`Visão Geral - Introdução e Histórico` (IA) sai de `aprendizado-de-maquina` (errado) para vazio.
Os 7 `roteiro*` do ES2 são **zips de código sem markdown**: não têm sinal de conteúdo nenhum, o
card é o único sinal, e as duas unidades candidatas mencionam microsserviços (`1.3.4 Orientada a
Microsserviços` na u01, `2.7 Estudo de Caso: integração e implantação de microsserviços` na u02).
Trocaram um palpite por outro; nenhum dos dois é fundamentado.

**Regressão (1)** — `Cap. sobre Algoritmos Geneticos (Lacerda e outros)` (IA): card diz
`Semana 12 - Algoritmos de Busca com Informação`, e a entry vai para `aprendizado-de-maquina`.
Inconsistência conhecida com o gêmeo `programa-exemplo AG`, que tem o mesmo card e vai para
`solucao-de-problemas`: o capítulo tem texto corrido que puxa para ML e vence o card, o
programa-exemplo não tem texto e segue o card. Corrigível com pino manual.

Saldo: 13 ganhos, 9 neutros/indecidíveis, 1 regressão isolada.


## Rollout em produção (2026-08-18) e re-baseline dos sentinelas

`scripts/reprocess_assignments.py` nos 5 repos. Réguas em produção, todas sem regressão:
SO 27/38 · MF 63/66 · IA 43/44 · ES2 22/28 · TCC 18/25 (confiante-e-errado do TCC: 2 → 1).
Golds de unidade: ES2 7/7 · IA 9/10 · MF 12/14 · SO 9/11 · TCC 13/13 — idênticos ao baseline.
Órfãos do gold no MF e no IA (1 cada) conferidos contra o worktree em `be62db9`: pré-existentes.
Taxonomia em disco: SO 36 tópicos, TCC 26 (unidade 04 com 14), ES2 21. Auditoria: 0 ausentes.

**Três sentinelas de caracterização falharam e foram re-baselinados**
(`tests/_golden/{SO,TCC,IA}__casos_chave.json`; cópias do baseline anterior no scratchpad da
sessão). Revisão caso a caso antes de aceitar:

| caso | mudança | leitura |
|---|---|---|
| `0206-laminas-gerencia-de-i-o` (SO) | `computed_block_id` 599004b1 → a838bf45 | convergiu para o `temporal_block_id` que **já constava no próprio golden** |
| `0704-exemplo-threads-em-java` (SO) | 57df1003 → 1945c228, unidade e/s → concorrente | ganho já julgado (threads) + convergência com o temporal do golden |
| `0904-laminas-semaforos` (SO) | e4f7e22a → 1945c228 | convergência com o temporal do golden |
| `aula-01-apresentacao` (TCC) | e4678122 → 18a1092a | convergência com o temporal do golden |
| `aula-06-revisao-alfabeto` (TCC) | só `band` | efeito de score |
| `introducao-a-busca-informada` (IA) | 43b6f936 → 7aa48de9 | `temporal_block_id` (`janela-1`) manda; destino final inalterado |

Em 4 dos 6 casos o `computed_block_id` passou a concordar com a âncora temporal registrada no
próprio baseline — efeito do date-tier e do `provider_ordinal`, commitados na sessão anterior e
que só chegaram a produção neste reprocess. Ganho de coerência, não deriva.


## Camada de COBERTURA das referências — 4 fixes (mesmo dia)

Medido com a régua nova (`scripts/eval_coverage.py`) contra os 9 rótulos aprovados.

| curso | antes | depois |
|---|---|---|
| SO | 0/3 exact · F1 0,0 · **3 sem predição** | 1/3 exact · **F1 0,778** (P 0,667 / R 1,0) · 0 sem predição |
| IA | 0/3 exact · F1 0,0 · 3 sem predição | 0/3 exact · F1 0,222 · 1 sem predição |
| MF | 0/3 exact · F1 0,0 · 3 sem predição | 0/3 exact · F1 0,0 · 2 sem predição |

Global: "sem predição" caiu de **8 de 9 para 3 de 9**; F1 macro saiu de 0,0.

Os fixes:
1. **`fetch_reference_text` lê o markdown local do repo antes da rede** (`read_local_markdown`,
   pulando o sumário executivo injetado). Era a causa raiz: as referências do Moodle são PDFs
   locais já convertidos, e o fetch só olhava GitHub README e página HTML.
2. **`assign_concepts_to_unit` devolve `units[]`** — todas as unidades cobertas, com os tópicos
   que **de fato casaram** (antes devolvia todos os tópicos da unidade vencedora). As chaves
   antigas seguem apontando a vencedora, porque COURSE_MAP e BIBLIOGRAPHY consomem uma só.
3. **Categoria `references` reconhecida** — o dado real tem 3 grafias; 3 entries vivas nunca
   entravam na camada.
4. **Poda de órfãos na curation** — ES2 tinha 6/6 e TCC 2/2 apontando entries que sumiram.

Mais duas correções que a medição exigiu, cada uma com teste que documenta o número que a
motivou:

- **métrica invertida no fallback sem LLM**: sem Gemini os "conceitos" viram o texto inteiro
  (~2000 termos) e `overlap/len(termos)` fica diluído a zero — 0 de 10 refs mapeadas mesmo com o
  texto disponível. Com texto bruto a pergunta certa passa a ser quantos tópicos **da unidade** o
  texto cita;
- **casamento de frase por palavra, com contenção**: exigir que todas as variantes (token e
  radical) estivessem no texto era critério impossível; e "pthread"/"threads" precisa casar o
  tópico "Programas multithreads" do plano do SO, o que nenhum radical liga. Piso de 6 caracteres
  para a contenção.
- **corte por margem relativa (máx. 2 unidades, ≥50% da melhor confiança)**: sem ele o critério
  de frase distintiva enchia a lista e derrubava a precisão do SO de 0,667 para 0,528.

O card (`source_section`) também entrou no texto de fallback da referência, pelo mesmo motivo
pelo qual entrou no eixo de unidade.

### O teto agora é outro

Das 3 referências que seguem sem cobertura, **nenhuma é falha de matching**: `eth2` e
`aws-encryption-sdk` (MF) têm **0 byte** de texto local — são repositórios GitHub cujo README
depende da rede — e `ia-responsável` (IA) tem 258 bytes, só a URL, nunca foi convertido. As 6
referências que têm texto de verdade receberam cobertura. Próximo passo natural, se valer a pena:
cachear o README no repo em vez de buscar a cada build.
