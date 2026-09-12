# Handoff 12/09 — C1 fechada, C5 aberta, regime cru como frente nova

last_updated: 2026-09-12 **tarde** (passo 0 feito, régua congelada, astra refez a análise: §§11 e 12). **Este é o ponto de entrada vivo**; `2026-09-11-handoff-camada3.md` passa a ser histórico.
Tracker: `docs/reports/pendencias.md` (seções de 11 e 12/09, do topo para baixo). Plano: `2026-09-08-plano-confianca-antes-de-acuracia.md`.
Placar publicado (12/09): https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de

## 1. Em uma frase

A C1 fechou no gate (precisão do confiante na subunidade 92,2%, unidade igual a 07/09 depois de desfeita uma regressão silenciosa), a
C5 abriu com o item 1 feito (régua de unidade virou curricular), e a frente que o usuário quer agora é **melhorar o motor cru (sem
LLM) e o "só Datalab"** antes de trazer outras engines de extração (MinerU e derivados); o astra já revisou o diagnóstico e deixou a
ordem das medições, que a próxima sessão executa.

## 2. Estado ao terminar (tudo commitado e no remoto; sem merge na `main`)

Gerador `feat/motor-atribuicao` @ ver `git log -1` (último commit desta sessão fecha o handoff); tutores SO, CG, ES2 no remoto (`main`),
FR/LR/MF/IA/TCC no remoto desde a madrugada. `main` do gerador: 1000+ commits atrás da branch, decisão de fronteira do usuário.

| régua CONGELADA (passo 0 feito em 12/09 tarde; produto em disco, 0 chamadas) | aceito | primário | fonte |
|---|---|---|---|
| subunidade no produto, 251 | **224 = 89,2%** (CG 64/82, MF 55/58, SO 15/15, IA 36/39, ES2 26/28, TCC 10/11, FR 18/18) | **186 = 74,1%** | `c1-3/congela_regua_cru_12-09.{log,csv}` |
| subunidade, precisão do confiante | **178/193 = 92,2%**, 15 erros confiantes, recall da fila 12/27 | **154/193 = 79,8%**, 39 erros confiantes, recall 26/65 | `c1-3/calibra_fila_como_regua_12-09.log` |
| unidade, régua CURRICULAR | 205/212 confiante = 96,7%; 21 erros = 17 adjudicados (o produto segue o bloco por desenho) + 4 do CG | eixo sem aceito/primário: a métrica é BRUTO × CERTO (precisão do confiante) | idem |
| bloco | 188/189 = 99,5% | eixo sem aceito (gold tem coluna única `true_block_id`) | idem |
| conflitos texto × bloco | 39; com gold 33; bloco certo 21, texto certo 12 (era 31 × 1 contra o gold por bloco: circular) | — | `c1-3/mede_conflito_unidade.log` |
| regime cru (sem vocab LLM, curadoria mantida), 251 | **147 = 58,6%** | **105 = 41,8%** | `c1-3/congela_regua_cru_12-09.log` |
| só código de outline (o mais cru), 251 | **113 = 45,0%** | **84 = 33,5%** | idem |
| teto das fontes cruas do professor (plano, SARC, seção, título, headings), 227 | não medido (o script só compara com o rótulo primário) | **64% = 146/227** com a taxonomia REALMENTE crua (SO 53, IA 95, ES2 71, TCC 70, MF 48, CG 60); "nenhuma" 22%. O 61% publicado media com 60% dos aliases de origem LLM dentro — ver §11.4 | `c1-3/mede_fontes_do_professor_cru_12-09.log` |
| FR do zero, /18 | crua 7 · só Datalab 8 · crua + vocab 18 · Datalab + vocab 18 · Datalab + LLM viva 18 · produto 18 | crua 6 · só Datalab 6 · crua + vocab 16 · Datalab + vocab 17 · Datalab + LLM viva 17 · produto 16 | `c1-3/mede_fr_sem_gold_run*_12-09.log` |

**Base e métrica não se misturam:** o teto de 64% é PRIMÁRIO sobre 227 (exclui gold vazio e o FR inteiro); o cru é 58,6% aceito /
41,8% primário sobre 251. A frase "o cru está em 39%/55% contra um teto de 61%" comparava métrica e base diferentes, e com um teto
que nem era cru.

Suite: 2347 passed, 4 skipped. **Replay reproduz o produto material a material nos 7 cursos: 0 divergências em 251/251**
(`c1-3/compara_replay_produto_12-09.log`), depois das duas correções do passo 0 abaixo. Antes eram 10, não 2.

## 3. O que entrou hoje (código e dados)

- `src/builder/artifacts/repo.py::load_glossary_curation`: **`"veto": [...]` por termo no sidecar manual** tira o sinônimo da fusão manual +
  LLM (normalizado sem acento); sobrevive a `--refiltrar`. Teste `tests/test_glossary_curation.py::test_veto_...`.
- `scripts/eval_entry_unit.py::_load_truth`: **régua de unidade curricular**: `material_gt_<sig>.csv` (uma unidade, scorable=yes,
  adjudicado) sobrepõe o gold por bloco; o bloco preenche o resto. Teste `tests/test_eval_ground_truth.py::test_load_truth_material_gt_sobrepoe_...`.
- Gold: `docs/reports/material_gt_CG.csv` (93, aprovado), `subunit_gt_CG.csv` (5 OpenGL → 1.4 `aplicacoes`; notas "aprovado 06/09"),
  `contradicoes_unidade_material_gt_vs_bloco.csv` (17 adjudicadas para material_gt), `tests/_golden/…SO__divisao_blocos.json` regenerado.
- Curadoria nos tutores: SO veta "Comunicação entre Processos" e "Pipes" em 3.1; CG "OpenGL" em 1.4, Catmull-Rom/Bézier/Casteljau/Curvas
  Paramétricas em 7.1.1.x; ES2 "gateway" em 1.5. Rollouts pela rota do produto com detector: 0 chamadas.
- Harness novo em `docs/reports/_harness-2026-09-04/c1-3/`: `mede_regressao_unidade.py` (diff 07/09 × pré × corrigido, unidade e subunidade),
  `mede_regressao_unidade_bloco.py` (verificação com assert), `mede_corte_nucleo_outra_unidade.py`, `monta_material_gt_CG.py`,
  `monta_contradicoes_unidade.py`, `replay_exp_{curadoria,u05,piso_semalias,pai}_12-09.py`, `replay_regime_cru_12-09.py`,
  `rebuild_fr.py` (refeito), `rebuild_fr_c.py`/`_c2.py` (paradas, ver §5), `fr_puro_com_vocab.py`, `fr_puro_datalab.py` (`--vocab`, `--llm`,
  `--llm-vivo`), `mede_fr_sem_gold.py`, `mede_fontes_do_professor.py` (+coluna PROFESSOR), `mede_conflito_precedencia_material_gt_12-09.log`.
- Briefs e respostas do astra (6 hoje): `brief_codex_astra_{fase2,gold_unidade_cg,estado_c1,regressao_unidade,contradicoes_unidade,fr_sem_gold,regime_cru}.md`
  e `resposta_codex_astra_*.md`. Cota do astra ao fechar: janela 5h 19%, semanal 37%.

## 4. Decisões TOMADAS pelo usuário hoje — não reabrir

1. OpenGL do CG = u01, subunidade 1.4 Aplicações (5 materiais). Bundles `opengl3dcpp*` = u06 pelo card 13. `exemplodemanipulacaodeimagens` = u03.
2. Ruling do u04 do CG mantido (SARC e Moodle acima do gold): os 9 erros do aglomerado u04 são TETO do motor (só abstenção corrigiria; refutada 4×).
3. Régua de unidade é CURRICULAR: as 17 contradições vão para `material_gt` (SO threads/sincronização u03; ES2 microsserviços u01; MF eth2/aws u02; t1 u01; t2 u02).
4. C1 fechada (= Fase 1 + Fase 2 pelo plano §4); C5 aberta na ordem: (1) contradições ✔, (2) gold de unidade FR e LR, (3) fila do CG, (4) insumo html/vídeo, (5) Matriz.
5. Nada de merge na `main`; push só por ordem explícita (dada hoje para tudo o que está no remoto).
6. Frente nova, prioritária: melhorar o cru e o só-Datalab; depois disso, outras engines de extração (MinerU e derivados).

## 5. Achados que o próximo trabalho precisa saber

- **Regressão de unidade de 11/09, achada e desfeita em 12/09:** o vocab LLM doou "Comunicação entre Processos" e "Pipes" a 3.1 do SO (u02)
  e o bloco-09 virou u03 → u02 (4 materiais); o M1 tirou "OpenGL" de 1.2 do CG e o bloco-02 perdeu a âncora (6). Os rollouts de 11/09
  mediram bloco e subunidade, não unidade. **Lei:** medir os 3 eixos em todo rollout; `mede_regressao_unidade.py` é o instrumento.
- **O motor pontua `base_markdown`; `advanced_markdown` (Datalab) é a última opção** (`navigation._entry_markdown_path_for_file_map`:
  approved > curated > base > advanced). 163 materiais nos 8 têm Datalab que o motor nunca leu. No FR, Datalab vale 0 sem vocab e +1 com.
- **O vocab compilado mexe no bloco**: FR do zero com vocab e sem voter, bloco = produto cai de 15/20 para 10/20; o voter recompõe (19/20).
  Nos 5 cursos (05/09) o vocab custou 1 bloco (187 × 186). Regressão de concordância, não defeito provado (FR sem gold de bloco).
- **Cache de votos não migra para um tutor do zero**: chave por conteúdo bate (11/20), mas o voto só é reaproveitado com a mesma janela de
  blocos; blocos novos têm outros uuids. Correto por desenho (astra).
- **"Bloco vence" 34/35 era circular** (gold de unidade era o próprio bloco); com a régua curricular: 21/33 × 12/33. As refutações de "texto
  vence" de 05/09 foram medidas contra o gold por bloco: reabrir só com a regra estreita (seção específica mapeada ao plano, corroborada
  pelo material, supera bloco misto), Gate 1.
- **Unidade 19/19 do FR do zero pela seção "U<n>" é reprodução do sinal, não validação** (o motor lê a mesma seção que a régua).
- **Estimativa em proxy infla**: os 4 itens da Fase 2 mediram +1, −6, "regra certa", +53 contra +5, +2, "48 itens", nada. Medir no produto.
- Sandbox fora do `subjects.json`: sem perfil o plano parseia 0 unidades e o guard "unidade nunca encolhe" aborta; forçar `store.find_by_repo_root`.
- Heredoc no Git Bash come barras invertidas e quebra em textos longos: escrever arquivos com a ferramenta de arquivo, não por heredoc.

## 6. NÃO fazer — refutado por medição em 11 e 12/09

Abstenção por piso de score (global e só em tópico sem alias: 4×, −2 a −17) · irmãos empatados → pai (−25) · tópicos de u05 visíveis para
u04 (0) · "mapeamento"/"gluLookAt"/"pipeline"/"provadores" como alias (0: token genérico, resumo determinístico não traz) · regra 2 do §2.2
(núcleo em outra unidade: −6) · "microsservicos" como alias do estudo de caso (ajuste ao gold) · propagação por similaridade como 3ª passada
(+1 candidato) · peso global ao título sem rastrear por que a regra existente falhou (astra) · Datalab ao vivo esperando ganho no motor
(o motor não lê o advanced) · trocar a chave do cache de votos por conteúdo.

## 7. O QUE FAZER AGORA — as medições que o astra deixou (Gate 1 da frente "regime cru"), nesta ordem

Contexto para quem executa (números do passo 0, §11): o cru está em **41,8% primário / 58,6% aceito** (251); o teto das fontes cruas do
professor é 61% PRIMÁRIO sobre outra base (227) e nem ele é 100% cru (§11.4); os 22% de "nenhuma" não são prova de conhecimento externo
(falsos negativos por radical, sigla, sinônimo do plano); IA é o bolsão (SARC nomeia 87%, cru 5/39).

0. ~~**Congelar a régua**~~ **FEITO em 12/09 tarde. O que apareceu está em §11 — leia antes de tocar em qualquer número.**
   Resumo: eram 10 divergências, não 2, por duas causas independentes; a régua congelada é 224/186 (produto), 147/105 (cru),
   113/84 (só código); os 112 erros do cru viraram 104; e o "teto de 61%" não é 100% cru.
1. **SARC posicional limpo:** o material herda o subtópico que a sessão do SARC do seu bloco nomeia; vínculos material → bloco → unidade
   produzidos sem gold, pinos manuais separados; sessão que nomeia o pai NÃO escolhe o filho (fica indeterminado); com e sem SARC contra o
   gold, ganhos e perdas nominais, aceito e primário. Alvo: IA (34 trocados para "introdução"). Circularidade: usar o SARC em dois eixos não é
   circular por si; gold ou vínculo derivado da resposta esperada é.
2. **Por que a regra de título existente falha** nos literais perdidos (MF "hoare", ES2 "microsservicos", TCC "variações"): auditar
   candidatos, normalização e o veto da regra, antes de qualquer peso novo.
3. **Headings que nomeiam subtópico irmão** (2ª passada).
4. **Só Datalab nos 8** (`advanced_markdown` onde existe, 163 materiais): mesmos materiais, extração básica × avançada, **vocab AUSENTE**,
   voter desligado, por tipo pdf/html/vídeo, resultado separado da cobertura; LR precisa de régua.
5. **Léxico embarcado** (para o que passa do teto): teste LR ↔ FR mede transferência, não independência de LLM; congelar léxico e mapeamento
   antes de olhar o gold do destino; declarar a origem (determinístico em execução, origem LLM).

Gate por alavanca: ≥ +3 sem perda é filtro inicial, não garantia depois de empilhar regras na mesma régua. Gate 2 por diff.

## 8. Brief para o astra REFAZER a análise com o contexto inteiro (o usuário pediu isto para a próxima sessão)

Montar por script (padrão `scratchpad/monta_brief_*.py`: texto meu + logs verbatim; nunca heredoc). Embutir: §§2, 4, 5, 6 e 7 deste handoff;
a partida do cru (`replay_regime_cru_12-09.log` com a coluna gold acrescentada no passo 0); a tabela do teto com a coluna PROFESSOR
(`mede_fontes_do_professor_limpo_12-09.log`); as 5 famílias que ele nomeou (`resposta_codex_astra_regime_cru.md`); o resumo das runs do FR.
Perguntas: (1) com o contexto do produto (tutor por unidade do plano, curso novo sem gold, sem LLM em runtime), o que estamos tentando
resolver está bem posto? (2) padrões nos 112 além das 5 famílias; (3) desenho do experimento SARC posicional sem circularidade; (4) o que
descartar sem medir; (5) como o léxico embarcado deve nascer para não ser "vocab LLM com outro nome"; (6) o que mais ele mudaria na ordem.
Regras do brief: trecho, não arquivo; dado que decide vai bruto; `codex exec --profile astra --sandbox read-only --skip-git-repo-check -C <repo> - < brief.md > resposta.md`;
custo esperado 35-50k tokens de contexto e ~3-5 pontos da janela de 5h.

## 9. Leis (reafirmadas)

Gold só mede, nunca decide; SARC e Moodle acima do gold; dado antes de código, pela rota real. Medir conjuntos, não somas. Medir os 3
eixos em todo rollout. Ao publicar subunidade, dizer base (251) e regime, e aceito × primário. Nada é pushed sem ordem explícita;
tokens nunca impressos; `.claude/settings.local.json` fora do índice (saiu em 12/09). Estimativa em proxy não vale; medir no produto.

## 10. Como iniciar a próxima sessão

No terminal, na pasta do gerador:

    claude --model claude-opus-5

Primeira mensagem sugerida:

    Leia .mex/ROUTER.md e o handoff vivo docs/reports/2026-09-12-handoff-regime-cru.md. Estamos na frente "regime cru"
    (§7 do handoff). Passo 0: congelar a régua (2 divergências do CG, coluna gold nos 112 erros, aceito e primário). Depois
    monte o brief do §8 e coloque o astra para refazer a análise com o contexto inteiro; só então abra o Gate 1 do passo 1
    (SARC posicional). 0 chamadas de LLM nas medições; astra só por ordem minha.

## 11. PASSO 0 FEITO — a régua congelada (12/09 tarde). Leia antes de tocar em qualquer número.

### 11.1 As divergências replay × produto eram 10, não 2 — e por DUAS causas independentes

**Causa A, cópia defasada (7 divergências: 6 CG + 1 ES2).** As cópias `.ablacao/CG` e `.ablacao/ES2` foram feitas às 00:47 de
12/09; a curadoria E4 (curvas do CG: `7.1.1 Curvas Paramétricas`, `7.1.1.1 Bézier/Casteljau`, `7.1.1.4 Catmull-Rom`) e E5
(`1.5 gateway` do ES2) entrou no produto às 00:59–01:01. Medido por `cmp`: `course/.content_taxonomy.json`,
`course/.glossary_curation.json`, `course/GLOSSARY.md` e `manifest.json` diferiam; `content/` e `code_curation.json` eram
idênticos byte a byte. **Ação:** `course/` e `manifest.json` dos dois cursos recopiados do produto (backup do estado anterior no
scratchpad da sessão). Os outros 5 cursos já batiam.

**Causa B, bug de escopo no replay (3 divergências, todas CG) + VAZAMENTO do produto para dentro do regime cru.**
`replay_subunidade.CATEGORIAS` lista `"referencias"` (PT) e o Moodle grava `"references"` (EN). Resultado no CG: o replay
processava 68 das 93 entradas. As 25 puladas (a) não entravam no `df` nem nos `owners` da 2ª passada — e o teto de df é
*relativo a* `len(passe1)`, então a população menor apertava o corte e a propagação divergia; e (b) ficavam com o
`computed_subunit_slug` **do manifest do produto**, porque `pred` é montado sobre TODAS as entradas, inclusive as que o loop
pulou com `continue`. **23 ids do gold (22 CG + 1 MF) nunca foram recalculados: 16 aceito e 14 primário eram creditados ao
"regime cru" sem terem sido computados — decididos COM o vocabulário LLM.**
**Ação:** `replay_subunidade._no_escopo(e, escopo)`; `escopo="produto"` usa o predicado do produto
(`resolver_apply.py:421-436`: `_is_material` e (`computed_block_id` ou `temporal_block_id` ou categoria em
`_NO_TIMELINE_CATEGORIES`)). O default continua `"replay"`, para os asserts contra os logs de 11/09 não mudarem de significado.
Diagnóstico verificado por dois refutadores independentes: ambos `refutado=false`, reproduzindo o mecanismo alias a alias.

**Resultado: 0 divergências replay × produto em 251/251, nos 7 cursos** (`c1-3/compara_replay_produto_12-09.log`).

### 11.2 Régua congelada (a tabela do §2 já está corrigida)

| regime, base 251 | aceito | primário |
|---|---|---|
| produto | 224 = 89,2% | 186 = 74,1% |
| cru (sem vocab LLM, curadoria humana mantida) | 147 = 58,6% | 105 = 41,8% |
| só código de outline | 113 = 45,0% | 84 = 33,5% |

Contra o que o handoff publicava de manhã (139/97 aceito/primário no cru): +8 aceito e +8 primário vieram da causa A, e a
causa B trocou 2 acertos herdados por 2 acertos calculados (net 0 no aceito, +1 no primário; o `só código` CAIU de 116 para 113).
`c1-3/replay_regime_cru_12-09.log` está **SUPERADO** — o script não foi migrado para o escopo novo.

### 11.3 Os erros do cru: 104, não 112

`c1-3/congela_regua_cru_12-09.log` traz cada um com **GOLD (primário + extras), slug inteiro, predição nos 3 regimes,
tipo do erro e confiança da 1ª passada**; `c1-3/congela_regua_cru_12-09.csv` traz os 251 materiais com as mesmas colunas.
18 vazios · 86 trocados · produto acerta 80. Não-primários no mesmo regime: 146.
Por curso (erro de aceito): IA 34 · CG 26 · MF 15 · FR 11 · ES2 9 · SO 6 · TCC 3.

### 11.4 Fontes fora da tabela do teto: inventário com ganho LÍQUIDO medido

Existência em disco não é sinal. Cada candidata foi passada pelo MESMO critério `nomeia()` das 5 colunas atuais, no regime
limpo que produz o 61% publicado (base 227):

| fonte | existe | nomeia o gold | ganho sobre as 5 colunas |
|---|---|---|---|
| `moodle_week_label` (label datado que o professor escreve na seção) | 98/227 | 19 | **+6** (todo em ES2 e MF) |
| nome ORIGINAL do arquivo (`raw/moodle/contents.json`, via casador oficial) | 183/227 casados | 35 | **+3** |
| `/Title` dos metadados do PDF | 57/227 | 5 | **+1** |
| limpar a coluna PLANO (tirar IMAGE_DESCRIPTION e code_curation) | — | — | **−1** (61% → 60%) |

- **`/Title` não paga**, apesar de parecer o de maior cobertura: dos 45 "não-triviais", 34 são template velho de PowerPoint
  — `"Algoritmos e Programação II"` 8×, que no MF é **disciplina errada** (entraria como sinal ativamente falso),
  `"Programação javaEE"` 10× no ES2, `"Apresentação do PowerPoint"` 4×, e 10 do TCC são o próprio nome do arquivo em UTF-16.
- **EMENTA: não acrescentar.** Existe nos 8 planos, mas é course-level e a cabeça do plano (25 a 43 linhas, onde moram ementa
  e objetivos) parseia **0 unidades nos 8 cursos** (`teaching_plan.py:183`, só acumula dentro de `if current_title is not None`).
  Não distingue material dentro do curso.
- **BIBLIOGRAFIA: não acrescentar.** Existe nos 8 planos com títulos reais, mas `_parse_bibliography_from_teaching_plan`
  devolve **0 básica / 0 complementar nos 8** (o regex exige `^BÁSICA\s*:` e os planos escrevem `## * **BASICA**` ou
  `BIBLIOGRAFIA BASICA:`), e nenhum caminho do motor de atribuição lê bibliografia. Se for usada um dia, é alavanca de
  vocabulário, não de atribuição, e o pré-requisito é consertar o regex.
- **ORDEM NO MOODLE: existe e está inerte nos eixos que importam.** `moodle_section_index`/`moodle_module_index` em 203/227,
  consumidos SÓ no eixo temporal (`card_stream.card_windows`, que ainda descarta toda entrada sem `moodle_week_label`,
  reduzindo o alcance real a 98/227) e em `anchor_engine.resolve_general_section`. **Zero consumo nos eixos unidade e subunidade.**
- Nunca lidos por ninguém: `indent` do módulo (75 módulos nos 8), `posting_date` (217 materiais em 5 cursos), `sortorder`,
  `mimetype`, `author`.
- Descartados por medição, não por suposição: número da seção do Moodle (só o CG numera, e a numeração é a sequência didática
  dele, não as 9 unidades do plano), `section.summary` (1–2 seções por curso, texto administrativo), cronograma do plano
  (o do TCC diz literalmente "Disponível no Moodle"), nome de pasta (é o slug do curso em 5 de 6).

**O teto de 61% não era cru — e o teto cru é MAIOR, 64%.** Duas contaminações, medidas depois da revisão do astra:
1. **A taxonomia.** `--limpo` só removia os aliases do sidecar MANUAL (`course/.glossary_curation.json`). Os sinônimos do
   sidecar do LLM já estão **fundidos na taxonomia** e sobreviviam: **501 dos 841 aliases dos 6 cursos (60%) são de origem
   LLM**. Modo `--cru` novo (tira os dois sidecares, igual ao regime `sem_llm` do replay).
2. **O texto.** A coluna PLANO varre `md + code_curation_signal_text`, e esse `md` carrega IMAGE_DESCRIPTION (visão do
   Gemini) em 74/227 e resumo de código do Gemini em 33/227. Modo `--sem-gemini` novo.

| modo (base 227, PRIMÁRIO) | PROFESSOR | SARC | TÍTULO | QUALQUER | NENHUMA |
|---|---|---|---|---|---|
| `--limpo` (o 61% publicado) | 138 = 61% | 80 = 35% | 83 = 37% | 178 = 78% | 49 = 22% |
| **`--cru`** (taxonomia sem os 2 sidecares) | **146 = 64%** | **85 = 37%** | **99 = 44%** | 178 = 78% | 49 = 22% |
| `--cru --sem-gemini` | 146 = 64% | 85 = 37% | 99 = 44% | 175 = 77% | 52 = 23% |

**O vocabulário de LLM estava SUPRIMINDO o teto, não inflando** — e isso é mecânico, não acidental: `nomeia()`
(`_secao_nomeia_subtopico`) exige que **exatamente um** tópico seja nomeado, e mais aliases significam mais empate, que
vira abstenção. O CG é o caso extremo: PROFESSOR 39 → 46 (51% → 60%). Corolário do astra, confirmado: **"NENHUMA" mede
ambiguidade do detector tanto quanto ausência de informação.** O SARC do IA fica em 34/39 = 87% nos dois modos — o bolsão
do IA é cru de verdade. Log: `c1-3/mede_fontes_do_professor_cru_12-09.log` (os 3 modos lado a lado).
**O teto honesto passa a ser 64% primário sobre 227, contra o cru de 41,8% primário sobre 251.**

### 11.5 Dívidas que o passo 0 abriu (nenhuma resolvida; nenhuma é do escopo do passo 0)

1. **A régua de unidade trata material transversal por acidente.** `scripts/eval_entry_unit.py:86-92` descarta as linhas de
   `material_gt_*.csv` com `gold_units` multi-valorado (separador `|`) em vez de virar conjunto aceito, porque os consumidores
   comparam com `==`. São 24 materiais (ES2 12, CG 5, SO 5, MF 1, TCC 1): planos, cronogramas, listas transversais. **Medido
   depois da correção do astra: 19 desses 24 NÃO saem da régua — conservam a unidade que o bloco já tinha dado (o `material_gt`
   entra sobrepondo, e a linha com `|` só deixa de sobrepor); os 5 que ficam de fora são todos do CG**, que não tem gold de
   unidade por bloco. Ou seja, em 19 casos a régua pontua contra UMA unidade quando o usuário adjudicou que qualquer uma vale.
   Decidir com o usuário: vira conjunto aceito (troca `==` por `in` nos consumidores) ou fica declarado na tabela.
2. **A 2ª passada doa token de MÍDIA como alias de subtópico.** No CG, `pptx`, `video` e `duracao` viraram alias de
   `segmentacao` — o acerto do produto em `morfologiamatematicapptx` é acidental. `_tokens_headings`
   (`resolver_apply.py:178-180`) filtra só `MOTOR_GENERIC_STEMS`, que não cobre extensão de arquivo nem termo de mídia.
3. **`replay_subunidade.py` como `__main__` está quebrado no HEAD** (`NameError: _ALS`, modo `determ`, vindo do `exec` parcial
   do `shim_codigo.py`). Pré-existente — confirmado rodando a versão de HEAD. O modo `com`, que é o da frente do regime cru,
   funciona.
4. **`replay_regime_cru_12-09.py` continua no escopo antigo** e seu log está superado; usar `congela_regua_cru_12-09.py`.
5. **Eixos unidade e bloco não têm aceito/primário e o bloco não pode ter** (`ground_truth_*.csv` tem coluna única
   `true_block_id`). O par de métricas do eixo unidade chama-se BRUTO × CERTO (precisão do confiante), com abstenção explícita.
6. **O teto por ACEITO nunca foi medido** (`mede_fontes_do_professor.py` só compara com o rótulo primário). Enquanto não for,
   a comparação honesta com o cru é primário × primário: **41,8% contra 61%** — e ainda assim sobre bases diferentes (251 × 227).

## 12. O ASTRA REFEZ A ANÁLISE COM O CONTEXTO INTEIRO (brief §8 entregue; 12/09 tarde)

Brief: `c1-3/brief_codex_astra_regime_cru_v2.md` (348 linhas: contexto do produto, o passo 0, os 104 erros com gold e slug
inteiro, o teto, o inventário de fontes, as 5 famílias dele, as runs do FR, as decisões fechadas, os refutados, as 6
perguntas). Resposta: `c1-3/resposta_codex_astra_regime_cru_v2.md`. 107.729 tokens usados.

### 12.1 As três correções dele que eu VERIFIQUEI medindo (todas procedem)

1. **Ainda existem 3 regressões inversas** (o cru acerta e o produto erra), não zero. Matriz completa do aceito, base 251:

   | | produto acerta | produto erra |
   |---|---:|---:|
   | **cru acerta** | 144 | **3** |
   | **cru erra** | 80 | 24 |

   As 3: ES2 `microsservicos2` (produto → `orientada-a-microsservicos`), ES2 `microsservicos3` (→ `estilos-e-padroes-arquiteturais`),
   CG `pagina-com-videos-sobre-manipulacao-de-imagens-61ddde` (→ `segmentacao`). **O vocab LLM vale +77 líquidos, não +80.**
2. **Os 24 transversais**: 19 conservam a unidade do bloco, só 5 saem da régua (todos CG). Já corrigido no §11.5.
3. **O `--limpo` não limpava o LLM.** Já medido e corrigido no §11.4 — e o resultado inverte a hipótese dele: a
   contaminação estava SUPRIMINDO o teto (61% → **64%** quando removida de verdade).

### 12.2 O que ele mudou no enquadramento (a resposta à pergunta 1)

**"Maximizar primário da subunidade no regime cru" não é a meta certa.** Um extra validado pelo professor também organiza
corretamente um material multitemático; tratá-lo como erro confunde preferência editorial com atribuição inválida. A meta
que ele propõe: **precisão ACEITA do confiante, publicada junto com cobertura automática e tamanho da fila**, com o
primário publicado ao lado como diagnóstico (detecta escolha sistematicamente secundária). Unidade errada tem prioridade
sobre subunidade errada. Números que sustentam: dos 193 confiantes, 178 aceitos e 154 primários — **24 decisões
confiantes são válidas sem serem principais**; cobertura = 193/251 = 76,9%.

**Três ressalvas dele sobre o que o placar congelado é:**
- **147/251 é uma ablação de aliases condicionada ao produto, não a execução de um curso novo sem LLM.** O replay mantém a
  unidade já calculada e, no modo `com`, injeta `code_curation` (resumo do Gemini). "Só código" também mantém esses
  insumos. **O placar vale como benchmark de ablação, não como benchmark de autonomia.**
- **`calibra_fila_como_regua` lê o manifest do PRODUTO: a precisão do confiante do CRU nunca foi medida.**
- **"NENHUMA" mede ambiguidade do detector tanto quanto ausência de informação** (`nomeia()` devolve vazio quando há 2+
  candidatos). Confirmado pela medição do §11.4.

### 12.3 Padrões novos nos 104 (a resposta à pergunta 2)

- **O colapso pode NASCER na 2ª passada, não só na 1ª.** No IA há material sem sinal na 1ª que termina em `introducao`; no
  TCC `variacoes` VENCE a 1ª passada (ambíguo) e PERDE depois; no ES2 `microsservicos` passa de estudo de caso para
  estilos. **Corolário: "literal perdido" não prova que o scorer nunca achou o literal** — por isso o passo 2 (auditar a
  regra de título) tem que rastrear 1ª → 2ª passada, não só o scorer.
- **Confiança alta pode ser ausência de concorrência, não certeza.** `exemplo-com-k-nn` erra com score 0,11 e confiança
  1,000: a confiança é margem relativa, não probabilidade calibrada. (Ele não está repropondo piso global de score, que já
  foi refutado 4×.)
- **Estrutura visual que o extrator não vê:** no HTML de modelagem do CG, `TÉCNICAS DE MODELAGEM` está em **negrito** e
  CSG/varredura vêm abaixo; `H_RE` só reconhece `#`. O agrupador estrutural perde para o detalhe.
- **Dos 24 que o produto também erra, 6 têm gold VAZIO** (5 CG, 1 TCC): preencher subunidade neles É o erro. Os outros 18
  não formam causa única (CG 17 mistura código, página multitemática e o ruling u04; IA 3; MF 3; TCC 1).
- Aviso de higiene: as notas do gold de páginas do CG ainda dizem "login", mas os markdown atuais que ele inspecionou têm
  conteúdo acadêmico — **a descrição antiga da captura não serve para diagnosticar a entrada de hoje**.

### 12.4 SARC posicional: o desenho que ele deixou (a resposta à pergunta 3)

Reusar o SARC nos dois eixos **não é circular por si** — é dependência entre sinais. Vira circular se a subunidade
candidata ajudar a escolher o bloco e o SARC desse bloco for depois apresentado como confirmação independente da mesma
candidata. Desenho mínimo:
1. Produzir os vínculos material → bloco → unidade sem gold e sem artefato LLM de atribuição; registrar a origem de cada
   um; separar o resultado dos materiais com pino manual.
2. **Congelar esses vínculos entre os dois braços** (controle sem SARC na subunidade, tratamento com SARC). Nenhum retorno
   da subunidade nova para o bloco nessa comparação.
3. Gerar a proposta do SARC contra rótulos do plano e aliases de origem comprovada; registrar sessão, trecho
   discriminante, candidatos e o motivo da decisão ou da abstenção.
4. Avaliar **depois** das decisões: precisão aceita do confiante, cobertura, primário, ganhos/perdas nominais, por curso e
   nos 3 eixos.
5. Validar por último pela rota integrada (a comparação com vínculos fixos isola; o rollout verifica efeito em bloco e unidade).

**Regra de abstenção por identificação insuficiente, não por piso:** sessão nomeia só o pai, ou múltiplos filhos, ou
sessões discordantes → o SARC não escolhe o filho. Evidência própria do material continua podendo decidir; sem ela, a
unidade fica e a subunidade fica indeterminada. **Concordância entre bloco e subunidade apoiados na MESMA sessão não conta
como duas confirmações.** E: se o gold foi adjudicado pelo próprio SARC, reportar "concordância com a adjudicação
curricular", nunca "validação independente".

### 12.5 O que descartar (pergunta 4) e a ordem revisada (pergunta 6)

**Os +1/+3/+6 do inventário medem alcance adicional do DETECTOR, não acerto líquido de rollout — e não são somáveis**
(fontes diferentes podem alcançar o mesmo material).

| fonte | decisão dele | motivo |
|---|---|---|
| `/Title` do PDF | arquivar, fora da implementação | +1 com contaminação forte de template |
| filename original | adiar; reusar o casador quando a frente entrar | +3 não demonstra benefício operacional |
| `moodle_week_label` | **próximo candidato depois do SARC** | campo já em disco, com vínculo temporal e conteúdo do professor |
| ementa / bibliografia | não abrir nesta frente | sem ganho demonstrado para distinguir subunidade |
| `indent`, datas, ordem isolados | ficam no inventário | existência do campo não estabelece como ele identifica o subtópico |

Contraponto dele a mim: **a concentração do `week_label` em ES2/MF não prova sobreajuste** — haveria sobreajuste se a regra
dependesse desses cursos, de ids ou da resposta esperada; cobertura concentrada pode ser só professor que preenche
diferente. E **"ementa inútil" é mais forte que a evidência**: não haver consumo pelo parser não prova impossibilidade de
ajudar (mas também não há motivo para priorizá-la).

**Ordem revisada (substitui a de §7):**
1. Preparar o **controle limpo** do SARC, preservando o benchmark congelado e explicitando os insumos herdados.
2. **SARC posicional no IA**, com ganhos/perdas e cobertura; depois medir transferência nos outros cursos.
3. **Rastrear 1ª → 2ª passada nos literais**, junto com a higiene dos tokens de mídia (§11.5 item 2), ANTES de ampliar
   doação por headings.
4. Comparar base × advanced **efetivamente consumidos** (hoje `base_markdown` precede `advanced_markdown`: sem verificar
   qual arquivo entrou no scorer, "Datalab ligado" não identifica a intervenção medida).
5. Só então o léxico congelado, sobre as lacunas identificadas e com **curso alvo reservado**.

### 12.6 Léxico embarcado (pergunta 5)

**Determinismo de execução, origem sem LLM e transferência são três alegações distintas** — um JSON gerado por LLM roda
deterministicamente e continua tendo origem LLM. Para o requisito do produto, o conhecimento tem que estar congelado
**antes de o curso novo chegar**: compilar sidecar por disciplina nova continua exigindo LLM na atribuição dela, cache ou
não. Forma proposta: arquivo versionado pequeno com **termo, relação, contexto de uso, fonte verificável, autoria/revisão
e versão** — não uma coleção de `palavra → slug` dos 7 cursos. **Relação importa:** "k-NN é um modelo preditivo" não é
"k-NN é sinônimo do rótulo curricular Modelos Preditivos"; o léxico dá conhecimento, o plano do professor continua
definindo o destino, e relação ambígua não autoriza escolher um filho. Para alegar transferência: congelar léxico,
normalização e regras antes do gold do alvo, excluir aliases e curadoria do alvo, e avaliar sem ajuste posterior — **os 7
cursos já examinados servem para regressão, mas perderam condição de teste cego**. Para alegar determinismo: mesma
entrada, versão e configuração → mesma decisão, com rede bloqueada e sem cache de atribuição do curso. **Se houve LLM na
autoria, registrar; não renomear a proveniência.**

## 13. DECISÕES DO USUÁRIO NO GATE 1 (12/09 tarde) e o que já foi executado

**Decisões tomadas — não reabrir:**
1. **A métrica que ordena a frente do regime cru passa a ser a precisão ACEITA do confiante**, publicada sempre com
   cobertura automática e tamanho da fila; o primário sai ao lado, como diagnóstico.
2. **A régua de unidade passa a aceitar CONJUNTO** nos materiais transversais adjudicados com `|`.
3. Passo 0 vai para commit local, sem push.
4. **Antes do SARC posicional, medir a precisão do confiante no regime CRU** (o astra apontou que ela nunca foi medida:
   `calibra_fila_como_regua` lê o manifest do produto).

### 13.1 A precisão do confiante no regime CRU — MEDIDA, e é o número que redefine a frente

`c1-3/calibra_fila_cru_12-09.{py,log}`. A fila é recalculada a partir das decisões do replay (`revisar_de` é função pura
do entry; o único gatilho que muda entre regimes é o de subunidade — bloco, flag e conflito vêm do manifest e são iguais).

| regime, base 251 | cobertura (confiante/n) | **ACEITO do confiante** | primário do confiante | erros confiantes | recall da fila |
|---|---|---|---|---|---|
| produto | 193 = 76,9% | **178/193 = 92,2%** | 154/193 = 79,8% | 15 | 12/27 = 44% |
| **cru** | 190 = 75,7% | **113/190 = 59,5%** | 83/190 = 43,7% | **82** | 27/104 = 26% |
| só código de outline | 183 = 72,9% | 93/183 = 50,8% | 70/183 = 38,3% | 90 | 48/138 = 35% |

**Sem o vocabulário do LLM o motor não sabe que está inseguro.** Ele entrega errado sem avisar em **82 dos 190
confiantes** (contra 15 de 193 no produto), e a fila pega só 26% dos erros (contra 44%). A cobertura quase não muda
(75,7% × 76,9%): **o que o vocab LLM compra não é decisão a mais, é decisão CERTA** — e, junto, a capacidade de abster.

Por curso, o aceito do confiante no cru: **IA 5/39 = 13%** (39 de 39 confiantes: o motor decide tudo, com confiança, e
erra 34) · FR 7/17 = 41% · ES2 13/19 = 68% · SO 8/11 = 73% · MF 36/48 = 75% · CG 36/46 = 78% · TCC 8/10 = 80%.
Os erros do cru que a fila pega têm motivo `sub-empate` (14), `conflito` (8), `sub-ambigua` (1) — nenhum outro gatilho
reage à falta de vocabulário.

**Consequência para o passo 1:** o IA não é só o maior bolsão de erro, é onde a abstenção falha por completo. O SARC
posicional tem que ser medido nas duas pontas — quanto acerta E quanto passa a abster.

### 13.2 A régua de unidade agora aceita conjunto (FEITO, com teste)

`scripts/eval_entry_unit.carrega_regua_unidade` é a fonte única e devolve **tupla de unidades aceitas** (a 1ª é a
primária); `_load_truth` fica como wrapper que devolve a primária, para os ~60 pontos do harness antigo que comparam com
`==`. Consumidores vivos migrados para pertinência: `eval_entry_unit.score_course`, `eval_eixos`,
`c1-3/calibra_fila_como_regua`. Teste novo:
`tests/test_eval_ground_truth.py::test_carrega_regua_unidade_multivalorado_vira_conjunto_aceito`.

Efeito medido no placar (`c1-3/calibra_fila_como_regua_12-09b.log` × `_12-09.log`):
**unidade 205/212 = 96,7% → 209/216 = 96,8%**; entraram 4 materiais do CG que ficavam fora da régua e todos acertam;
nenhum dos 19 que eram pontuados contra uma única unidade regrediu. Bloco (188/189) e subunidade (178/193) inalterados,
como esperado. "Qualquer eixo": 219/241 → 223/245.
