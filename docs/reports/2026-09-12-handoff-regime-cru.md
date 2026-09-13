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
| teto das fontes cruas do professor (plano, SARC, seção, título, headings), 227 | não medido (o script só compara com o rótulo primário) | **44% = 100/227** na taxonomia do regime cru (`--so-llm`). O 64% e o 61% publicados antes mediam com vocabulário de LLM dentro do detector — ver a CORREÇÃO em §11.4 | `c1-3/mede_fontes_do_professor_corrigido_12-09.log` |
| FR do zero, /18 | crua 7 · só Datalab 8 · crua + vocab 18 · Datalab + vocab 18 · Datalab + LLM viva 18 · produto 18 | crua 6 · só Datalab 6 · crua + vocab 16 · Datalab + vocab 17 · Datalab + LLM viva 17 · produto 16 | `c1-3/mede_fr_sem_gold_run*_12-09.log` |

**Base e métrica não se misturam:** o teto de **44%** é PRIMÁRIO sobre 227 (exclui gold vazio e o FR inteiro); o cru é 58,6% aceito /
41,8% primário sobre 251. **A folga entre o cru e o teto das fontes do professor é de ~2 pontos, não 22** — as fontes posicionais do
professor estão praticamente esgotadas (§11.4, correção).

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

> **CORREÇÃO (12/09, noite) — o teto de 64% publicado acima estava errado, e o erro era meu.** `mede_fontes_do_professor.py` fazia `tops_ev = tops_limpos if LIMPO else tops`: a flag `--cru` que eu acrescentei alimentava o conjunto `curados` mas **nunca chegava ao detector**, então `--cru` sozinho devolvia byte a byte a linha da taxonomia do PRODUTO. Corrigido (`tops_ev` passa a respeitar o modo) e com o modo novo `--so-llm` (sem o sidecar do LLM, curadoria humana mantida = a taxonomia do regime cru da régua). Medido de novo, base 227, PRIMÁRIO:
>
> | modo | PROFESSOR | SARC | IA |
> |---|---|---|---|
> | taxonomia do produto (sem flag) | 146 = 64% | 85 = 37% | 37/39 = 95% |
> | `--limpo` (sem sidecar manual, LLM dentro) | 138 = 61% | 80 = 35% | 37 = 95% |
> | **`--so-llm` = o regime cru da régua** | **100 = 44%** | **55 = 24%** | **2/39 = 5%** |
> | `--cru` (sem os dois sidecares) | 85 = 37% | 44 = 19% | 0 = 0% |
>
> **Duas consequências.** (1) O teto das fontes cruas do professor é **44% primário**, não 64% — e o cru está em 41,8% primário: a folga é de ~2 pontos, não 22, e ainda em base mais fácil (227 exclui gold vazio e o FR). (2) A leitura de que 'o vocabulário do LLM estava SUPRIMINDO o teto (61% → 64%)' **se inverte**: os +3 pontos vieram de devolver ao detector os aliases da curadoria MANUAL, não de tirar os do LLM. Tirando o LLM de verdade, o teto CAI de 64% para 44%. E o 'bolsão do IA, cru de verdade a 87–95%' era vocabulário de LLM: no regime cru o IA vai a **5%**. Log: `c1-3/mede_fontes_do_professor_corrigido_12-09.log` (os 4 modos lado a lado).


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
| **cru** | 190 = 75,7% | **113/190 = 59,5%** | 83/190 = 43,7% | **77** | 27/104 = 26% |
| só código de outline | 183 = 72,9% | 93/183 = 50,8% | 70/183 = 38,3% | 90 | 48/138 = 35% |

**Sem o vocabulário do LLM o motor não sabe que está inseguro.** Ele entrega errado sem avisar em **77 dos 190
confiantes** (contra 15 de 193 no produto), e a fila pega só 26% dos erros (contra 44%). A cobertura quase não muda
(75,7% × 76,9%): **o que o vocab LLM compra não é decisão a mais, é decisão CERTA** — e, junto, a capacidade de abster.

Por curso, o aceito do confiante no cru: **IA 5/39 = 13%** (39 de 39 confiantes: o motor decide tudo, com confiança, e
erra 34) · FR 7/17 = 41% · ES2 13/19 = 68% · SO 8/11 = 73% · MF 36/48 = 75% · CG 36/46 = 78% · TCC 8/10 = 80%.
Os erros do cru que a fila pega têm motivo `sub-empate` (14), `conflito` (8), `sub-ambigua` (1) **Correção de contagem (12/09 tarde):** o bloco final do `calibra_fila_cru` contava por `motivos_de`, que não vê o gatilho "mudou" (`sync_changed`); 5 materiais caem só por ele. São **77** erros confiantes, não 82 (190 − 113). Os dois scripts e esta tabela já usam `revisar_de`; o commit c8c018a saiu com 82 na mensagem. — nenhum outro gatilho
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

## 14. "COMO AUMENTAR O NÚMERO DO CRU" — a pergunta do usuário, o que foi medido e o que o astra respondeu (12/09, noite)

Brief: `c1-3/brief_codex_astra_cru_como_subir.md` (377 linhas, com os 77 erros confiantes um a um).
Resposta: `c1-3/resposta_codex_astra_cru_como_subir.md` (75.748 tokens).

### 14.1 Correção de contagem: são 77 erros confiantes, não 82

O bloco final de `calibra_fila_cru_12-09.py` contava por `motivos_de`, que não vê o gatilho "mudou" (`sync_changed`);
5 materiais caem só por ele. **190 − 113 = 77.** Os dois scripts (`calibra_fila_cru` e `lista_erros_confiantes_cru`) já
usam `revisar_de`. O commit `c8c018a` saiu com 82 na mensagem.

### 14.2 Os 77, um a um (`c1-3/lista_erros_confiantes_cru_12-09.{py,log,csv}`)

**63 o produto acerta** (o vocab LLM resolve) e **14 ele também erra**. **53 decididos na 1ª passada, 24 na 2ª.**
3 têm predição VAZIA e mesmo assim ficam fora da fila. Colapso por destino: **IA manda 34 para
`introducao-ao-aprendizado-de-maquina`**, FR manda 6 para `paradigmas-clienteservidor-e-p2p`, MF manda 5 para
`abordagens-para-verificacao-formal` — quase metade dos erros confiantes do acervo inteiro é um curso indo para um destino.

### 14.3 O que a investigação paralela mediu (3 frentes, cada uma com refutador independente)

**(a) O colapso do IA é ausência de vocabulário, não desempate** (refutador sustenta). Nos 34 erros o tópico do gold tem
score **ZERO em 30**; a unidade está certa em 39/39. Contrafactual: matar o rótulo-aspirador vale **+2**; devolver só o
vocabulário de domínio dos 3 tópicos do gold vale **+31** (5 → 36, igual ao produto).
**AUTO-ENVENENAMENTO (achado novo):** `content_taxonomy.py:603-646` doa headings dos próprios materiais como alias de
tópico; no IA, 5 headings de slides foram arquivados no tópico errado, **não vêm do LLM e por isso sobrevivem ao corte do
regime cru** — `arvores-de-decisao` pontua 8,97 no tópico errado por casar a frase que é o H2 do próprio arquivo.
**A 2ª passada APAGA a abstenção da 1ª** (`resolver_apply.py:339` sobrescreve os reasons): 7 dos 39 materiais do IA
abstiveram na 1ª passada e terminaram confiantes no destino errado, sem rastro na fila. E **o plano do IA realmente não
numera** — os 0 aliases de código não são falha de captura.

**(b) Sinal de fragilidade** (recomendação principal REFUTADA). **Fecha:** margem absoluta entre 1º e 2º
(Spearman **0,948** com o próprio `winner_score` — é o piso global com outro nome, 5ª refutação), razão s2/s1, cobertura
de tokens, riqueza de alias, "sem competição". **Abre de graça** (sobreviveu intacto): alinhar a fila com as abstenções
que o matcher **já emite** — `auto_map_entry_subtopic` abstém em `winner_score <= 0` e em "revisao-sem-assunto-dominante",
mas `revisar._subunidade_em_duvida` só casa "ambiguous" e "empate-exato"; são **3 materiais no cru entregues com slug
VAZIO e sem aviso** (9 no só-código, 0 no produto). **Teto da abstenção, medido:** a união mais agressiva que não quebra o
produto leva o aceito do confiante de 59,5% para 67,3%, com a cobertura caindo de 75,7% para 64,5% — **a abstenção não
conserta o cru, só torna a falta de vocabulário visível.**

**(c) A 2ª passada no cru é quase neutra na métrica que ordena** (aceito do confiante 59,1% → 59,5%), embora compre +11
aceito bruto e +9 de cobertura. `partes de rótulo` paga (−6 aceito ao desligar); `propagação por headings` custa no cru
(isolada derruba para 56,1%, erros 74 → 82) mas **no produto é a maior alavanca** (−8 se desligada). Das 9 decisões que
ela tira da fila no cru, 3 estão certas e 6 erradas.
**REFUTA uma dívida que eu havia registrado (§11.5 item 2):** a doação de token de mídia é pequena (4 de 169 tokens) e
na conta real **ganha 3 e perde 1** — a higiene mínima custa −2 aceito no cru e −3 no produto. O alias é feio e o acerto é
acidental, mas remover piora o número.

### 14.4 O astra derrubou a métrica que eu propus — e está certo

Eu propus **"entrega confiável" = confiantes certos / 251** dizendo que não dá para inflar abstendo nem chutando.
**Metade errada:** não dá para inflar abstendo, mas dá para inflar **deixando de abster**. Verificado por aritmética
sobre o próprio log: esvaziar a fila sem mudar predição nenhuma leva a entrega de **113/251 = 45,0% para 147/251 = 58,6%**
e os erros confiantes de 77 para 104. Erro não entra no numerador, mas também não penaliza.

**A forma corrigida, que ele propõe:** maximizar entrega **sob precisão mínima**, publicando fila e resultado por curso.
E, para congelar a troca ANTES de medir alavanca, um custo explícito: **`saldo = ΔC − 4 × ΔE`** (um erro confiante custa
quatro entregas certas), com piso de entrega para "abster de tudo" nunca virar candidato. **O peso 4 é preferência
operacional proposta, não estimada do gold — é decisão do usuário.**
Alvos que ele separa: **imediato calculável** = encaminhar os 3 vazios errados (C=113, E=74, Q=64 → precisão 60,4%);
**marco de pesquisa proposto** = precisão ≥ 80% preservando ≥ 113 entregas certas, depois buscar 126/251 = 50,2% de
entrega. Os 70,9% do produto são referência, não promessa.

**E os 64% NÃO limitam a entrega confiável do cru:** é alcance do PRIMÁRIO, em outra base, por um instrumento que
consulta o gold e aceita a união das fontes — não demonstra que o motor escolhe a fonte certa quando elas discordam, nem
exclui combinação de sinais. É alcance daquele detector, não teto de informação.

### 14.5 As outras respostas dele

- **Os 14 que nem o vocab resolve FICAM no denominador.** "O produto também erra" prova que o vocabulário atual não
  basta, não que seja teto; não distingue extração, vínculo, scorer, propagação ou gold ruim. Só excluir por
  inelegibilidade independente do resultado. Para os 2 com gold vazio, verificar se vazio é "nenhum tópico aplicável"
  (resposta válida) ou "ainda não adjudicado". **E: 251 entradas não são 251 evidências independentes** — há duplicata
  (dois `entry_id` para o mesmo documento), então publicar também o resultado por documento distinto.
- **Não desligar a 2ª passada inteira pelos 24.** "24" é atribuição pela razão final, não erro causado incrementalmente:
  a comparação completa compra +6 confiantes certos e +3 erros confiantes; pelo custo dele, saldo −6 — justifica
  investigar restrição, não diz qual. "Só headings" não mede "tudo menos headings". Hipótese prioritária dele: **não
  liberar automaticamente uma abstenção quando a nova evidência deriva das próprias previsões que alimentaram a
  propagação**, preservando a predição candidata para revisão.
- **Não promover `exact_hits == 0` porque ganhou no PRIMÁRIO**: a régua decisória congelada é ACEITO, e trocar a régua
  depois do resultado é ajuste. Custo menor justifica considerá-la candidata, não trocar o critério.
- **O 67,3% não é teto da abstenção** — é o melhor entre ~20 regras varridas no mesmo 251, sem holdout.
- **Não dizer "custo zero, sem risco"** para o alinhamento da fila; "zero regressões observadas nesta base" é o que a
  evidência sustenta.

### 14.6 A ordem que ele deixa agora (substitui a do §12.5)

1. **Alinhar matcher e fila** — cobrir as abstenções explícitas que ainda não são resolvidas, preservando
   "não aplicável" legítimo.
2. **Medir a liberação de abstenção pela 2ª passada**, separando evidência independente de evidência produzida pelo
   próprio motor.
3. **Controle limpo + SARC no IA**, com vínculos congelados, contando entregas certas, erros e fila.
4. **Avaliar aquisição de vocabulário independente do gold**, com curso reservado (os 7 atuais já são desenvolvimento).
5. **base × advanced** só nos erros residuais e só onde o texto efetivamente consumido difere.

**Descartar agora, sem nova rodada:** numerar artificialmente o IA; desligar toda a 2ª passada por contagem bruta; limpar
tokens de mídia para melhorar este placar; excluir os 14 difíceis; tratar 64% como teto; repetir piso global com outro nome.

## 15. "FAÇA AS MEDIÇÕES, NÃO QUERO QUE CHUTE, MESMO QUE SEJA O ASTRA CHUTANDO" (12/09, noite)

O astra propôs dois números no ar: o peso "um erro confiante vale 4 entregas certas" e o piso de precisão de 80%.
O usuário mandou medir. **Um dos dois é medível e está medido; o outro não é, e agora se sabe exatamente por quê.**
Três medições rodaram, cada uma com um refutador independente. **Duas foram refutadas** — e as refutações são o
resultado mais honesto da rodada.

### 15.1 O peso do erro: NÃO é medível com o dado que existe (e a tentativa mostrou por quê)

A ideia era medir o custo real de errar contra o custo de abster no artefato que o aluno usa, pela régua de travessia
(`scripts/eval_travessia.py`, piso determinístico, 0 chamadas): trocar a subunidade em memória e ver quantas perguntas
do gold quebram.

**Resultado bruto:** errar nos 54 erros confiantes de CG/FR/IA custa **1 pergunta de 45** no acerto@1; abster nos mesmos
54 não custa nada — **ganha 1**. A razão pedida é 1/0: indefinida.

**E o refutador derrubou até isso, com razão:** em **31 das 45 perguntas o 1º lugar está EMPATADO** e é decidido pela
**ordem alfabética do `entry_id`** (`escolher_sem_llm` ordena por `(-score, id)`). Trocando o desempate por outro
igualmente arbitrário (id decrescente), o efeito inteiro evapora: D−B = 0, E−B = 0, e a própria linha de base vai de
24/45 para 20/45. **A oscilação do instrumento vale 8 perguntas; o efeito procurado vale 1 a 2. Ruído 4× maior que o
sinal.** Além disso, o canal medido não é o que o aluno lê: `navigation.py:686` renderiza o **label**
("1.2 - Modelos OSI e TCP/IP"), não o slug — e no canal label errar custa MAIS que apagar (−2 contra −1), porque um slug
errado **injeta** token falso enquanto apagar só remove.

**Conclusão registrada:** o peso 4 não é confirmado nem refutado — é **inestimável com este dado**. E o bloqueador não é
o tamanho do gold de travessia (45 perguntas, 3 cursos): é que **o piso determinístico empata em 69% das perguntas**.
Gold maior sobre esse piso só aumenta o n do ruído. Para medir de verdade seria preciso (a) desempate com informação
(TF-IDF/BM25 ou comprimento do hay), (b) o hay usando o label renderizado, e (c) instrumentar a fila na UI para ter o
tempo de correção — esse último é o dado que não existe e que resolveria a pergunta de vez.

Números secundários que sobrevivem: 25 dos 54 erros confiantes **nunca aparecem em nenhum top-3** (custo zero por
construção, não por medição), e **o IA é totalmente insensível** (0 de 15 perguntas mudam) — justo o curso com 34 dos 77
erros.

### 15.2 O piso de precisão: É medível, e está medido — a fronteira inteira

`c1-3/fronteira_*_12-09.py` + `fronteira_12-09.log` + `fronteira_sinais_12-09.csv` (47 colunas por material × regime).
~200 regras de abstenção varridas sistematicamente, com holdout leave-one-course-out. **O refutador NÃO derrubou.**

**A zona grátis (reproduzida por mim, à mão, no CSV):**

| regra | cru | produto |
|---|---|---|
| base | C 113 / E 77 — entrega 45,0%, precisão 59,5% | C 178 / E 15 — entrega 70,9%, precisão 92,2% |
| `pred vazia` | C 113 / E 74 — **60,4%** | C 178 / E 15 — 92,2% (não muda) |
| **`cobertura do tópico entregue < 0,2 E peso do campo doador ≤ 1,1`** | **C 112 / E 57 — 66,3%** | **C 178 / E 14 — 92,7%** |

Ou seja: **tira 20 dos 77 erros confiantes do cru custando 1 entrega certa, e no produto custa ZERO entregas e ainda
tira 1 erro.** No holdout com custo limitado, é a regra escolhida em **6 dos 7 folds** e fora da amostra custa 0 entregas
em 5 dos 7 cursos.

**O piso MEDIDO que substitui o 80%:** a zona em que o produto não regride (C ≥ 178 e precisão ≥ 92,2%) tem **teto em
66,3% de precisão do cru**, com entrega 44,6%. O ponto de quebra é o degrau seguinte (`pred vazia OU rota==2a-propagado`:
a entrega do produto cai de 178 para 170). **Acima de 66,3%, cada ponto de precisão do cru é comprado com entrega do
produto** — e isso é medição, não escolha.

**O preço do 80% que o astra pediu, medido:** a melhor regra que cruza 80% (`rota==2a-propagado OU peso_doador ≤ 1,1`)
leva o cru a 80,8% custando **33 das 113 entregas certas** (−29%) e **20 das 178 do produto**.

**O holdout diz algo sobre o k que a medição direta não conseguiu:** a k=1 (um erro vale uma entrega) a abstenção **não
generaliza** — ganho negativo fora da amostra em 3 dos 7 cursos, média caindo de +0,140 para +0,060 por material. A k=2 e
k=4 generaliza em **7 de 7**, com a mesma regra escolhida em 6 dos 7 folds. Não mede o valor de k, mas **mede que abaixo
de k=2 a abstenção não sobrevive fora da amostra**.

**Taxa de troca marginal medida, degrau a degrau** (entregas certas perdidas por erro removido):
0,00 → 0,06 → 1,50 → 0,20 → 0,33 → 0,22 → 2,20 → 1,08 → 0,50 → 0,75. **Os dois primeiros degraus compensam a qualquer
k ≥ 1** — são os dois da zona grátis.

**Controle obrigatório:** apesar de `exact_hits` e `peso_doador` terem Spearman +0,97 e +0,88 com o `winner_score`, o
piso global de score (refutado 5×) é **DOMINADO nos 22 pontos** da varredura, perdendo 8 a 12 pontos de precisão na mesma
entrega. **A família não é o piso refutado disfarçado.**

**A rota mais frágil, medida:** `2a-propagado` decide 37 confiantes no cru com **19 erros** (51,4% contra 59,5% da média);
no produto a mesma rota decide 9 com 1 erro.

### 15.3 O preço da fila: só o do PRODUTO é medível

A terceira medição (custo de revisão) foi **refutada no essencial**: a fila do "cru" é híbrida. O replay só recomputa
`computed_subunit_slug` e `subunit_match_reasons`; `unit_block_conflict`, `sync_changed` e `temporal_block_flag` vêm
**congelados do manifest do produto** — **59 dos 82 itens da fila do cru (72%) entram só por motivo congelado**. Então
"preço por regime" não existe: é o mesmo numerador quase fixo dividido por três contagens de erro diferentes.

**O que sobrevive, medido:** a fila do **produto** custa **58 materiais revisados por 12 erros de subunidade pegos =
4,8 materiais por correção, com 79% de alarme falso**. E um alerta do refutador: 5 dos materiais que a fila "corrigiria"
pelo eixo unidade são **contradições que o usuário já adjudicou** (SO threads u03, ES2 microsserviços u01) — contá-las
como defeito seria contar decisão curricular como erro do motor.

### 15.4 O que fica para decidir

O único número que continua sendo escolha, e não medição, é **quanto vale um erro confiante em relação a uma entrega
certa**. A medição diz: abaixo de k=2 a abstenção não generaliza; os dois primeiros degraus da fronteira compensam a
qualquer k ≥ 1; e acima de 66,3% de precisão do cru o produto começa a pagar. **Com isso a escolha deixa de ser um peso
abstrato e vira a escolha de um ponto numa curva com preço na mão.**

## 16. "O QUE PRECISAMOS PARA AUMENTAR O CRU" (12/09, noite) — a resposta medida

Três medições em paralelo. **Os três refutadores morreram por limite de sessão**, então o que está aqui é
**medido mas NÃO refutado** — exceto o que eu reproduzi com as próprias mãos, marcado como tal.

### 16.1 O rótulo certo quase nunca está escrito no material (reproduzido por mim)

`c1-3/onde_esta_o_rotulo_12-09.{py,log,csv}`. Para cada um dos 104 erros de aceito do cru, o label do tópico do gold
(e seus aliases que sobrevivem ao corte) aparece como frase no texto que o motor pontuou?

| | n | leitura |
|---|---|---|
| label inteiro presente | 3 (2,9%) | competição: o motor viu e escolheu outro |
| alias cru presente | 1 (1,0%) | idem |
| só um token do label | 26 (25,0%) | parcial |
| **nada do rótulo** | **74 (71,2%)** | **o texto não nomeia o tópico** |

Nos 77 erros **confiantes**: 54 são "nada". E dos 80 que o produto acerta, 53 são "nada" — é exatamente esse buraco
que o vocabulário do LLM preenche.

**O padrão é sempre o mesmo:** o plano usa a categoria (`Modelos Preditivos`, `Provadores de Teoremas`,
`Conceitos básicos`) e o material usa a técnica (k-NN, perceptron, MLP, árvore de decisão; Coq/Isabelle; threads).
A relação instância → categoria é o que falta, e **não está escrita em documento nenhum do professor**: verifiquei o
plano de ensino do IA inteiro (3.569 chars) — a ementa diz "Introdução ao Aprendizado de Máquina" e **não menciona
perceptron, k-NN, MLP, k-means nem árvore de decisão uma única vez**.

### 16.2 As fontes posicionais do professor estão esgotadas (correção de um erro meu, §11.4)

Ver a CORREÇÃO na §11.4: o teto que eu publiquei (64%) era o do produto. **O teto do regime cru é 44% primário**, o SARC
24%, e o IA **5%** (não 95%). Como o cru está em 41,8% primário, a diferença aritmética contra as fontes do professor é
de ~2 pontos e não 22 — **mas isso NÃO é folga: ver §17.2.** Medido na mesma base, teto 100 e motor cru 99 têm só **79
materiais em comum**; o motor acerta 20 que nenhuma fonte nomeia e erra 21 que uma fonte já nomeia.

Confirmação independente pelo inventário erro a erro (`inventario_fontes_104_cru.csv`): das 8 fontes testadas
(plano, SARC, seção, título, headings, corpo inteiro, week_label, nome original), **nenhuma alcança o gold em 72 dos 104
erros (69%)**; a união de todas cobre 32, e pelo critério estrito do motor, 25. E **alcance de fonte não é ganho de
motor**: dos 32 alcançados, só 10 teriam o tópico do gold como argmax.

**Em 51 dos 98 erros testáveis o tópico do gold tem score ZERO na 1ª passada** — não há o que reordenar. Em 9 o gold
**já é** o argmax da 1ª passada: esses nascem na 2ª passada, não no scorer.

### 16.3 SARC posicional: NEGATIVO MEDIDO — frente fechada

`scratchpad/sarc_posicional_12-09.*`. A regra literal do astra (§12.4), com vínculos congelados e abstenção por
identificação insuficiente, **perde nos dois regimes**:

| braço | cru: aceito / entrega / erros conf. | produto: aceito / entrega / erros conf. |
|---|---|---|
| controle | 147 / 113 / 77 | 224 / 178 / 15 |
| **SARC-A (sobrepõe)** | **141 / 110 / 85** | **209 / 165 / 34** |
| SARC-B (só preenche vazio) | 149 / 115 / 78 | 225 / 179 / 16 |

Com a **fila congelada** o sinal é o mesmo (cru 113/77 → 109/81), então não é artefato de cobertura. Eixos bloco e
unidade: efeito zero por construção, verificado por assert em 251×2×2 entries.

**A causa do negativo — CORRIGIDA pelo refutador, ver §17.1:** a regra perde onde **DECIDE**, não onde abstém. No cru o
IA é inerte (5/5/5 aceito, 34/34/34 erros, 5/5/5 entrega) e a perda é MF (−6 aceito), SO (−2) e FR (+1 erro). O que o IA
mostra é outra coisa: lá o SARC **abstém em 39 de 39** por "não nomeia nada". As sessões do SARC do IA são ricas em texto (`ml abordagem supervisionada k nn`, `ml abordagem nao supervisionada
k means`) — mas nenhum rótulo do plano casa com elas sem os sinônimos do LLM.

A variante B é o único braço não-negativo e é marginal: +2 entregas no cru (3 materiais, todos predição vazia que o SARC
preenche certo), e o holdout a elege em 7/7 folds mas ela **só generaliza em 1/7** (saldo fora da amostra +1 em k=1,
0 em k=2, −2 em k=4). **Não reabrir sem dado novo.**

### 16.4 A alavanca que resta, medida — e a ressalva que a desqualifica como plano

`scratchpad/alavanca_vocab_por_topico.py`. Os 104 erros se concentram em 38 pares (curso, tópico); **10 pares concentram
71 deles** e 62 dos 72 que nenhuma fonte alcança. O IA sozinho são 2 tópicos: `modelos-preditivos` (25) e
`modelos-descritivos` (8).

Devolvendo vocabulário de domínio **só nesses 10 tópicos**: cru 147 → **201 aceito**, 105 → **163 primário**, aceito do
confiante 59,5% → **81,3%** (ganho nominal 61, perda 7). Com os 36 tópicos do gold dos erros (17% dos 217 tópicos dos 7
cursos): **222/251 aceito e 180 primário, 90,3%** — praticamente o produto (224/186, 92,2%).

**A ressalva que impede chamar isso de plano:** os 10 (e os 36) tópicos foram escolhidos **olhando o gold**. É teto de
curadoria dirigida dentro da amostra, não ganho generalizável. **Nenhum seletor sem gold conseguiu ranquear:** "sem alias
textual no cru" marca 144 dos 217 tópicos e "nunca vence no cru" marca 137 — a união cobre 8 dos 10 alvos mas com 171
tópicos (79% do total). **Achar o seletor sem gold é o trabalho que falta**, e ele é pré-requisito de qualquer promessa
de ganho em curso novo.

### 16.5 A resposta em uma frase

**O que falta não é fonte, é conhecimento de domínio: o mapa técnica → categoria curricular.** As fontes posicionais do
professor estão medidas e esgotadas (teto 44% contra os 41,8% de hoje); o SARC posicional está fechado por negativo
medido; e 71% dos erros são materiais cujo texto não nomeia o tópico de jeito nenhum. O vocabulário resolve (medido:
+54 aceito com 10 tópicos), mas **hoje só sabemos escolher os tópicos olhando o gold** — e é isso que precisa ser
resolvido antes de qualquer coisa: um seletor de tópicos carentes que não use a resposta.

## 17. OS REFUTADORES RODARAM (12/09, noite, depois do limite de sessão) — duas afirmações minhas caíram

Os 3 refutadores que morreram às 19h foram re-executados por `resumeFromRunId` (as medições vieram do cache; só os
refutadores rodaram). Veredito: **1 confirmado, 2 refutados** — e os dois refutados derrubam frases que eu publiquei.

### 17.1 SARC posicional: CONFIRMADO no núcleo — mas eu errei a CAUSA

O refutador reproduziu **dígito a dígito**, com script próprio e usando o `_secao_nomeia_subtopico` do motor (não a
reimplementação do agente original): os 6 braços, as 7 linhas por curso, a fila congelada e os ganhos/perdas nominais.
O negativo do SARC está de pé, e ainda sobrevive a dois testes de robustez que ninguém tinha feito: desligar a
abstenção "só o pai" (cru 141/100, entrega 110) e não deixar a regra se autodeclarar confiante (braço A0, cobertura
intacta: cru 141/102, entrega 109).

**O que eu errei:** escrevi que "a causa do negativo é o SARC do IA abster em 39 de 39". **É o contrário — a regra perde
onde DECIDE, não onde abstém.** No cru o IA é inerte nos três números (aceito 5/5/5, erros confiantes 34/34/34, entrega
5/5/5); a perda inteira é **MF (−6 aceito, −5 entrega, +5 erros), SO (−2, −1, +2) e FR (+1 erro)**, contra ES2 (+1, +2) e
CG (+1, +1). No produto o IA é o **segundo melhor** curso do braço A (entrega 36 → 38) e a perda é ES2 −7, FR −4, SO −3,
MF −2. A abstenção do IA em 39/39 explica por que a regra não ajuda o alvo declarado; **não** explica por que ela perde.

### 17.2 A "folga de ~2 pontos" contra o teto: ERRADA, é subtração entre conjuntos que não se contêm

Eu escrevi que, com o teto corrigido para 44% e o cru em 41,8% primário, "a folga é de ~2 pontos". O refutador mediu na
**mesma base 227 e na mesma taxonomia**: teto PROFESSOR **100**, motor cru primário **99** — **mas só 79 são os mesmos
materiais**. O motor **acerta 20 que nenhuma das 5 fontes nomeia** e **erra 21 que uma fonte do professor já nomeia**.
A folga aritmética de 1 é o saldo de dois fluxos opostos de ~20. **44% não é teto do motor em direção nenhuma — é
alcance de detector.**

**E existe um recorte residual real, que minha frase negava:** dos 11 materiais em que uma fonte alcança e o motor erra o
**aceito**, 3 já são colhidos pelo SARC-B, 3 vêm da coluna PLANO (o rótulo está no texto que o motor já pontua — é
scorer, não fonte nova), e **5 vêm de SEÇÃO/TÍTULO/HEADINGS, que foram inventariados por alcance e NUNCA testados como
regra de motor**: ES2 `microsservicos6`, ES2 `roteiro8-autenticacao-autorizacao`, ES2 `devops`,
TCC `aula-10-linguagens-reconheciveis...`, CG `introducaoprocimg`. São **5/251 = 2,0 pp** — pequeno demais para reabrir a
frente, mas **é esse o argumento honesto para não reabrir, não a "folga de 2 pontos"**.

Menor: "a linha `--cru` é byte a byte a linha sem flag" é impreciso. Idênticas são as 5 colunas do detector mais
PROFESSOR/QUALQUER/NENHUMA (85 · 46 · 99 · 79 · 146 · 178 · 49); AL-CURADO (163 × 28), AL-HEADING (22 × 150) e
SEM-CURADO (149 × 178) divergem — porque a flag alimentava só o conjunto `curados`. A correção do teto continua de pé.

### 17.3 "Onde está a informação": REFUTADO nos números-manchete, não na direção

A alavanca de vocabulário reproduz byte a byte (147/105 → 201/163, aceito do confiante 81,3%, ganho 61 / perda 7).
O que cai: o agente publicou "teto cru real = 85/227 = 37%", que é o modo `--cru` (tira os **dois** sidecares, curadoria
humana inclusive). **O regime cru da régua mantém a curadoria humana, e o número dele é 44%** (`--so-llm`) — que é o que
está publicado na §11.4 e na §2. Ou seja: a correção que eu apliquei usou o número certo; o agente é que citou o outro.

### 17.4 "O vocabulário é reconstruível": REFUTADO na conclusão

Os números reproduzem, a conclusão não: **alcance de fonte foi confundido com ganho de motor**, e o ganho publicado só
existe com oráculo (a restauração devolve exatamente os aliases que a ablação já provou decisivos, filtrados por onde a
palavra existe — um colhedor real traria também os termos que atrapalham). **O achado que sobrevive é o negativo:** o
termo está no acervo, mas **a relação termo → tópico do plano não está em lugar nenhum** — que é exatamente o que a
§16.1 mostra por outro caminho.

## 18. A META 90/90/90 E O PLANO — o astra revisou tudo (12/09, noite)

Brief: `c1-3/brief_codex_astra_plano_90.md` (256 linhas, com os 3 refutadores embutidos).
Resposta: `c1-3/resposta_codex_astra_plano_90.md` (86.276 tokens).
**Veredito de uma linha: "90/90/90 no cru não foi demonstrado; impossibilidade também não. O produto passa apenas se
'90%' significar precisão dos confiantes."**

### 18.1 A tabela que faltava: os 3 eixos, acurácia TOTAL × precisão do confiante

O astra propôs (e eu verifiquei contra `calibra_fila_como_regua_12-09b.log`) que a meta seja cobrada como **acurácia
total sobre todos os materiais avaliáveis**: abstenção **não** tira o material do denominador, e vazio conta como acerto
quando o gold pede vazio.

| eixo | PRODUTO: acurácia total | PRODUTO: precisão do confiante | CRU: acurácia total |
|---|---|---|---|
| bloco | 235/237 = **99,2%** | 188/189 = 99,5% | **não medida** |
| unidade | 263/284 = **92,6%** | 209/216 = 96,8% | **não medida** |
| subunidade (aceito) | 224/251 = **89,2%** | 178/193 = 92,2% | 147/251 = **58,6%** |
| subunidade (primário) | 186/251 = 74,1% | 154/193 = 79,8% | 105/251 = 41,8% |

**A conta da meta, sobre 251: 90% = 226 acertos.**

| configuração | acerto | falta para 226 |
|---|---|---|
| produto (APIs pagas) | 224 = 89,2% | **+2** |
| cru + 36 tópicos com vocabulário (escolhidos com gold) | 222 = 88,4% | +4 |
| cru + 10 tópicos com vocabulário (escolhidos com gold) | 201 = 80,1% | +25 |
| **cru** | 147 = 58,6% | **+79** |

Se a meta for cobrada no **primário**, faltam **121** no cru.

**O buraco que o astra aponta e eu confirmo: unidade e bloco NUNCA foram medidos em regime cru.** O replay conserva a
unidade do manifest e recalcula a subunidade *dentro* dela — então nem os 58,6% são medição de um pipeline cru integral.
Medir exige rodar o motor completo por configuração, em cópias novas (não na `.ablacao/` congelada).

### 18.2 A terceira correção do dia (dele, sobre meu número)

Dos 104 erros, **6 têm gold vazio** — neles a resposta certa é não atribuir, e acrescentar vocabulário não é a correção.
Entre os 98 com tópico esperado, o "texto não nomeia o tópico" é **68/98 = 69,4%**, não 74/104 = 71,2%.
E uma ressalva sobre o meu instrumento: eu medi frases dos aliases mas **tokens só do label primário**, com corte de
tamanho e de prefixo genérico; o scorer usa tokens dos aliases, siglas e outros campos. Então **"nada" significa ausência
segundo aquele instrumento — não prova ausência de sinal no scorer**.

### 18.3 O seletor de tópicos carentes: o desenho que ele deixou

**Regra de seleção:** priorizar tópicos **sem suporte nos componentes reais do scorer** e **ausentes do top-2 com score
positivo** (empate em zero não conta). Concentração das vitórias entre irmãos entra como **sinal auxiliar**, e o número
de materiais potencialmente afetados como **desempate**.

**O que ele rejeita como gatilho sozinho:** rótulo genérico e razão materiais/tópicos. Distribuição desigual pode ser
legítima, e tópico sem vencedor pode simplesmente não ter material ainda. A concentração por unidade só deve ser
calculada **quando o vínculo material→unidade for confiável** — senão transforma erro de unidade em suposta carência
lexical.

**Protocolo:** escolher **top-K com orçamento fixado ANTES** do teste; entregar ao curador tópico, contexto e trechos
representativos, pedindo relações termo→categoria justificadas; **nunca** acrescentar alias para equilibrar contagem.

**A regra de ouro dele sobre o gold:** *"Gold pode entrar na avaliação; não pode orientar seleção, curadoria ou ajuste do
curso testado."* Congelar regra, orçamento e prompt; executar em curso novo; revelar o gold só depois. Comparar contra
três baselines: **nenhuma curadoria**, **seleção aleatória com o mesmo orçamento**, e **curadoria completa**.
E o aviso: os 7 cursos já examinados servem para desenvolvimento e regressão; **LOCO ajuda mas não recupera
independência depois de a regra ter sido desenhada olhando todos**.

### 18.4 O plano (5 passos) e o que descartar

1. Fixar o contrato de "cru", a proveniência de cada insumo e a métrica.
2. **Medir o motor completo nos 3 eixos, em cópias novas, separadas da `.ablacao/` congelada.**
3. Comparar curadoria **seletiva** contra curadoria **completa**.
4. Avaliar a configuração congelada em **cursos externos com gold cego**.
5. Escolher pelo ganho líquido e custo observado.

**Descartar como justificativa:** o teto de 44%; abstenção apresentada como aumento de acurácia; precisão do confiante
apresentada como acurácia total; ganho com oráculo apresentado como previsão para curso novo. **Despriorizar** SARC-A e
as regras de margem, já negativas.

**Datalab:** ele reproduziu (21/31 aceitos nos dois braços, 3 predições alteradas, primário 16→15). "Isso não sustenta
comprá-lo para melhorar essa atribuição; também não demonstra inutilidade geral da extração."

### 18.5 A pergunta que o usuário talvez esteja realmente fazendo

Eu perguntei ao astra se o alvo não deveria ser o produto (que já bate 90/90/90 na precisão do confiante) e "quanto custa
manter isso sem API paga". A resposta dele corrige o enquadramento: **"sem API em runtime" é diferente de "sem preparação
por LLM"**. Medido: o replay do produto mantém os resultados **com a rede bloqueada**, usando os artefatos existentes —
isso prova **reutilização local**, não custo zero para um curso novo. E a compilação de vocabulário faz **uma chamada por
unidade elegível**, não uma por curso.

**Custo monetário por curso: NÃO MEDIDO.** Faltam consumo faturado, retries e tempo de curadoria. **Não há base para
prometer "uma passada offline entrega 90/90/90 por R$ X".**

E um alerta de nomenclatura que vale registrar: o "cru" de hoje remove os aliases do sidecar LLM mas **conserva
`code_curation.json`** (resumo de código do Gemini) e outros insumos já gerados. **Não é ausência de toda contribuição
anterior de LLM** — é uma ablação de aliases.

## 19. OS 3 EIXOS COM O MOTOR COMPLETO, POR CONFIGURAÇÃO (12/09, noite) — o buraco é UM eixo só

O passo que faltava: até aqui o regime cru só tinha número de subunidade, porque o replay herda `computed_unit_slug` e
`temporal_block_id` do manifest do produto. Aqui o motor roda **inteiro** (`reprocess_assignments.reprocess`) em cópia,
uma configuração por vez.

**Guardas:** cópia em `.motor3eixos/` (nunca `.ablacao/`, que é a régua congelada — verificado intacto depois);
`use_llm_voter=False` nas três; **rede bloqueada no processo** (qualquer chamada levanta `RuntimeError`), e as três
rodaram sem exceção: **0 chamadas**; voter confirmado off pelo manifest (nenhum `temporal_block_method: llm` nas cópias,
contra 1 no produto do TCC). Instrumento: `c1-3/motor_3eixos_12-09.py` + `c1-3/mede_3eixos_12-09.py`
(validado contra o produto: reproduz 99,2% / 92,6% / 89,2% exatos). Log: `c1-3/motor_3eixos_12-09.log`.

### 19.1 A tabela

Acurácia **TOTAL** (todo material avaliável no denominador; abster não tira ninguém):

| eixo | (1) NU<br>sem curadoria, sem vocab | (2) RÉGUA<br>curadoria humana, sem vocab | (3) VOCAB<br>+ vocab LLM, sem voter | (4) PRODUTO<br>+ voter |
|---|---|---|---|---|
| **bloco** (237) | 221 = **93,2%** | 222 = **93,7%** | 221 = 93,2% | 235 = **99,2%** |
| **unidade** (284) | 244 = 85,9% | 253 = **89,1%** | 255 = 89,8% | 263 = **92,6%** |
| **subunidade aceito** (251) | 125 = 49,8% | 146 = 58,2% | 220 = 87,6% | 224 = **89,2%** | *(corrigido na §20: o cache de resumo de codigo vazava vocabulario)*
| subunidade primário (251) | 85 = 33,9% | 103 = 41,0% | 184 = 73,3% | 186 = 74,1% |
| *cobertura (não vai para a fila)* | *54,2%* | *56,2–62,0%* | *58,2–68,4%* | *76,9–79,7%* |

### 19.2 O que cada camada compra (em pontos de acurácia total)

| camada | bloco | unidade | subunidade |
|---|---|---|---|
| curadoria humana (1 → 2) | +0,5 | **+3,2** | +8,8 |
| vocabulário do LLM (2 → 3) | −0,5 | +0,7 | **+29,8** |
| voter do LLM (3 → 4) | **+6,0** | +2,8 | +1,6 |

**Leitura, contra a meta de 90%:**
- **BLOCO: a meta JÁ está batida no motor cru** — 93,2% sem nada, 93,7% com curadoria humana. O voter compra os 6
  pontos que levam a 99,2%, mas 90% não precisa dele.
- **UNIDADE: falta menos de 1 ponto** — 89,1% no regime régua contra a meta de 90%. São **3 materiais** de 284.
- **SUBUNIDADE: é o único eixo longe** — 57,8% contra 90%. E é o único em que o vocabulário do LLM é decisivo (+29,8).

**Consequência para o plano: a frente "aumentar o cru" é, na verdade, uma frente de UM eixo.** Bloco e unidade
praticamente já cumprem a meta sem nenhuma API; a subunidade é o buraco inteiro.

### 19.3 Por curso (acurácia total), configuração RÉGUA

| curso | bloco | unidade | subunidade |
|---|---|---|---|
| MF | 89,4% | 92,4% | 79,3% |
| SO | 92,3% | **73,0%** | 60,0% |
| IA | 97,6% | 100,0% | **12,8%** |
| ES2 | 96,4% | 85,7% | 64,3% |
| TCC | 96,3% | 100,0% | 72,7% |
| CG | 94,3% | 87,1% | 63,4% |
| FR | — | — | 38,9% |

O IA continua sendo o caso extremo da subunidade (12,8%) **com unidade em 100%** — o material está na pasta certa e no
subtópico errado. E a unidade do SO (73,0%) é o pior número do eixo unidade: vale olhar antes de mexer em subunidade,
porque erro de unidade custa mais (§1 do brief do produto).

### 19.4 Ressalvas honestas

- **A cobertura cai muito no cru** (54–62% contra 77–80% no produto): mais material vai para a fila. A acurácia total já
  conta isso (o que a fila acerta entra no numerador), mas o custo de revisão sobe — e o preço da fila só está medido
  para o produto (4,8 materiais por correção, §15.3).
- **`nu` não é "sem LLM nenhum"**: `code_curation.json` (resumo de código do Gemini) continua na cópia, e o markdown do
  acervo já foi gerado com os pipelines de sempre. É ablação de curadoria e de vocabulário, não um gerador virgem.
- As bases dos três eixos são diferentes (237 / 284 / 251) e **isto não mede acerto simultâneo nos três** — um material
  pode acertar bloco e errar subunidade. A coluna "qualquer eixo" existe no calibra e não foi recalculada aqui.

## 20. O ASTRA REVISOU A MEDIÇÃO DOS 3 EIXOS — o isolamento estava furado, e eu consertei (12/09, noite)

Brief: `c1-3/brief_codex_astra_3eixos.md`. Resposta: `c1-3/resposta_codex_astra_3eixos.md` (114.674 tokens).
**Veredito: "as contagens conferem; a conclusão 'resta só um eixo' não. O isolamento do vocabulário está incompleto."**

### 20.1 Os três furos que ele achou — os três procedem

**(a) O cache de resumo de código preservava o vocabulário que eu removi.** `code_summarization.course_aliases()` lê a
taxonomia **e** o sidecar do LLM, mas `compute_entry_hash` faz hash só do **texto do bundle** — então vetar aliases
**não invalida o resumo salvo**. Medi eu mesmo: dos 1.453 conceitos gravados nos 42 registros dos 7 cursos, **202 são
aliases que só existem por causa do sidecar LLM** (CG 134, ES2 45, IA 9, FR 9, MF 5), e **37 dos 42 registros estão no
gold de 251**. Era o mesmo tipo de vazamento do bug de escopo do replay (§11.1), em outro lugar.

**(b) "Terminou sem exceção ⇒ 0 chamadas" NÃO era prova.** A camada de vocabulário
(`pedagogical_regeneration.py:104`) **captura** a exceção e deixa a execução seguir — uma tentativa bloqueada passaria
despercebida. E a mensagem "0 chamadas" do meu driver era **texto fixo, sem contador**.

**(c) O veto na taxonomia compilada não é idêntico ao veto do replay.** O reprocess reconstrói a taxonomia depois da
edição; ele contou 30 ocorrências de termos vetados que reaparecem (MF 14, SO 4, IA 4, ES2 5, TCC 3) — podem vir
legitimamente do plano, de headings ou da curadoria humana, mas **coincidência de texto não prova origem**, e o replay
elimina por texto independentemente da origem. São duas intervenções diferentes.

### 20.2 O conserto e a remedição

`motor_3eixos_12-09.py` ganhou: **`zera_cache_de_codigo()`** (nas configurações sem vocabulário, o `code_curation.json`
da cópia é esvaziado e o reprocess regenera os resumos com a taxonomia já vetada — `synthesize_all_code_entries` é
determinístico) e um **contador real de tentativas de rede** (o guard registra o stack e o número impresso vem do
contador). Log da remedição: `c1-3/motor_3eixos_v2_12-09.log`.

| eixo | (1) NU | (2) RÉGUA | (3) VOCAB | (4) PRODUTO |
|---|---|---|---|---|
| bloco (237) | 221 = 93,2% | 222 = **93,7%** | 221 = 93,2% | 235 = **99,2%** |
| unidade (284) | 244 = 85,9% | 253 = **89,1%** | 255 = 89,8% | 263 = **92,6%** |
| subunidade aceito (251) | **125 = 49,8%** | **146 = 58,2%** | 220 = 87,6% | 224 = **89,2%** |
| subunidade primário | 85 = 33,9% | 103 = 41,0% | 184 = 73,3% | 186 = 74,1% |

**Tentativas de rede bloqueadas: 0, 0 e 0** — agora medido por contador, não afirmado.

**Efeito do vazamento, medido:** +2 materiais no `nu` (123 → 125) e +1 na `régua` (145 → 146), **no sentido contrário ao
esperado** — o cru ficou levemente *melhor* sem o cache contaminado. Bloco e unidade não mudaram nenhum dígito.
**As conclusões principais sobrevivem**, e agora sobre um experimento isolado.

Deltas corrigidos (o astra apontou meu arredondamento): curadoria humana **+0,4 / +3,2 / +8,4**; vocabulário
**−0,4 / +0,7 / +29,4**; voter **+5,9 / +2,8 / +1,6**.

### 20.3 O que ele derrubou nas minhas conclusões (e eu aceito)

- **"Resta um eixo só" excede a evidência.** Priorizar subunidade faz sentido; concluir que só ela precisa de LLM, não —
  os aliases alimentam taxonomia, resumos e decisões anteriores, e restringir o efeito deles à subunidade seria uma
  configuração nova, **ainda não medida**.
- **"Os 10 são a única alavanca da unidade" é inferência errada.** O produto também errar **não estabelece teto**: os
  dois podem compartilhar uma falha determinística. Os 10 desacordos servem de diagnóstico, não de fronteira.
- **"Bloco resolvido" excede o dado.** 93,7% confere e não é efeito dos pinos manuais (sem eles, 216/231 = 93,5%). Mas:
  o CG tem **93 entradas e só 35 avaliadas em bloco** (13 linhas do CSV foram excluídas por "seção sem bloco casado" —
  justamente casos difíceis), o FR não participa desse eixo, e **os UUIDs dos 35 golds de bloco do CG não existem no
  índice atual** (o medidor aceita o id posicional). Isso precisa ser validado antes de tratar esses acertos como
  identidade temporal confirmada. E o MF fica em 89,4%: **a meta agregada passa, uma meta por curso não**.
- **A atribuição VOCAB → PRODUTO ao voter não é limpa:** a 4ª coluna é um produto salvo, sem braço contemporâneo
  reprocessado nas mesmas condições. O delta é válido; a causa ainda não.
- Correções numéricas dele que confirmei: cobertura de unidade no produto = **76,1%** (eu disse 76,9%); aliases vetados
  **51–98** por curso (eu disse 85–98).

### 20.4 O que ele recomenda como próximo passo

**"Corrigir o experimento antes do motor"** — e os itens (a) e (b) já foram corrigidos acima. Restam três:
1. **Validar a correspondência dos UUIDs do gold de bloco do CG** com o índice atual, antes de contar aqueles 35 acertos.
2. **Decidir e declarar o que a ablação remove**: a *fonte* LLM, ou *qualquer termo coincidente*? São coisas diferentes,
   e hoje o replay faz uma e o driver faz a outra.
3. **Incluir o quarto braço equivalente**, com voter ligado e reprocessado nas mesmas condições, para a atribuição
   causal do voter parar de depender de um produto salvo.

## 21. O EXPERIMENTO CONSERTADO — os 3 itens do astra, fechados (12/09, noite)

Os três pontos que restavam da revisão (§20.4) foram executados. **Nenhum derruba a conclusão; um deles a reforça.**

### 21.1 Os UUIDs do gold de bloco do CG: risco real, dissolvido por medição

`c1-3/valida_gold_bloco_12-09.{py,log}`. O medidor compara o bloco do material com o `true_block_id` **posicional**
("bloco-NN"). Se o índice tivesse sido renumerado, o acerto seria acidental.

| curso | scorable | `true_block_uuid` existe no índice | tem `data_real` | **a data cai no período do bloco do gold** |
|---|---|---|---|---|
| MF, SO, IA, ES2, TCC | 202 | **202 (100%)** | 0 | — (âncora forte já basta) |
| **CG** | 35 | **0** | 35 | **35 (100%)** |

Nos cinco cursos a âncora forte está de pé. No CG, onde ela falha (o gold foi escrito antes do rebuild do curso), a
verificação independente — **a data real da aula contra `period_start`/`period_end` do bloco que o id posicional
nomeia** — bate em **35 de 35**, com zero fora. **O gold do CG foi re-chaveado corretamente; os 35 acertos são válidos.**

### 21.2 O que a ablação remove: medido, e a escolha é inócua

`c1-3/proveniencia_alias_12-09.{py,log}`. Para cada alias vetado, procurei o mesmo texto em fontes independentes do LLM:

| | total | também no PLANO | nos HEADINGS do acervo | no sidecar MANUAL | **só no LLM** |
|---|---|---|---|---|---|
| aliases vetados (7 cursos) | 544 | 35 | 341 | 0 | **197** |

**64% dos aliases vetados também vêm de fonte do professor.** E isso importa porque o construtor da taxonomia
(`content_taxonomy.py:603-646`) doa headings como alias **independentemente do LLM** — ou seja, o veto por texto
removia aliases que um curso sem LLM teria de qualquer forma, e o regime "cru" ficava **mais duro que a realidade**.

Implementei os dois modos (`--veto texto` = o do replay; `--veto fonte` = preserva os que vêm do plano ou dos headings)
e rodei os dois:

| eixo | `--veto texto` (544 vetados) | `--veto fonte` (197 vetados) |
|---|---|---|
| bloco | 93,7% | **93,7%** |
| unidade | 89,1% | **89,1%** |
| subunidade | 58,2% | 57,8% |

**A escolha não muda o resultado**: bloco e unidade idênticos, subunidade difere em 1 material de 251 — e no sentido
não-monotônico (vetar menos deu 1 a menos), o que é coerente com os efeitos não-monotônicos já medidos na 2ª passada.
**A ambiguidade que o astra levantou é real e é inócua.** Fica registrado qual modo cada número usa.

### 21.3 O quarto braço, com voter ligado nas mesmas condições

| eixo | VOCAB (voter off) | **PRODUTO-braço** (voter ON, reprocessado agora) | produto salvo em disco |
|---|---|---|---|
| bloco | 93,2% | **99,2%** | 99,2% |
| unidade | 89,8% | **92,6%** | 92,6% |
| subunidade | 87,6% | **89,2%** | 89,2% |
| subunidade primário | 73,3% | **74,1%** | 74,1% |

**O braço contemporâneo reproduz o produto salvo dígito a dígito.** A atribuição do delta ao voter deixa de depender de
um artefato antigo: **+5,9 no bloco, +2,8 na unidade, +1,6 na subunidade** são efeito do voter, medidos com controle.

**E um resultado que não estava na pergunta: o braço rodou com 0 tentativas de rede.** O voter foi inteiramente servido
pelo cache `material_curation.json`. Isso **prova com contador** o que o astra tinha dito em §18.5: o produto é
reprodutível localmente sem API — o que não diz nada sobre o custo de um curso novo, onde não há cache.

### 21.4 Onde o experimento está agora

| eixo | NU | RÉGUA (cru) | VOCAB | PRODUTO |
|---|---|---|---|---|
| bloco (237) | 93,2% | **93,7%** | 93,2% | **99,2%** |
| unidade (284) | 85,9% | **89,1%** | 89,8% | **92,6%** |
| subunidade aceito (251) | 49,8% | **58,2%** | 87,6% | **89,2%** |
| subunidade primário | 33,9% | 41,0% | 73,3% | 74,1% |

Tudo com **contador de rede em 0** nas quatro configurações, cache de resumo de código regenerado sem o vocabulário,
gold de bloco validado por âncora independente e quarto braço contemporâneo. **As três leituras de fundo continuam:**
o bloco bate a meta de 90% no cru, a unidade fica a menos de 1 ponto, e a subunidade é o eixo que precisa de vocabulário.

**O que continua NÃO resolvido, e que o astra tem razão em não deixar passar:** "resta um eixo só" continua excedendo a
evidência, porque restringir o efeito do vocabulário à subunidade seria uma configuração nova, ainda não medida; e a
meta **por curso** não passa (MF 89,4% no bloco, SO 73,0% na unidade).

## 22. ATACAR A SUBUNIDADE: o seletor de tópicos carentes, construído e medido (12/09, noite)

Ordem do usuário: *"vamos atacar a subunidade, pois 58% é bem ruim, delegue o astra"*. **O astra bateu o limite de uso
da conta** (volta 13/09 00:38) e não terminou o plano — mas alcançou a deixar um achado, e é justamente o que destrava
o seletor. O brief está pronto em `c1-3/brief_codex_astra_atacar_subunidade.md` para quando ele voltar.

### 22.1 O achado dele, verificado: "score > 0" não prova suporte lexical

> *"o scorer pode dar score positivo só pelo bônus estrutural do subtópico. O teste de presença no top-2 precisará
> exigir contribuição lexical real; caso contrário, contará suporte inexistente."*

Confirmado em `src/builder/timeline/index.py:1935`: **`if kind == "subtopic": score += 0.04`** — incondicional, sem
nenhum casamento de texto. Os dois seletores que eu havia testado usavam "nunca vence" e "sem alias textual", ambos
contaminados por isso.

### 22.2 O anatomia dos 105 erros no motor completo (`c1-3/erros_subunidade_motor_12-09.{py,log,csv}`)

105 de 251. **O produto acerta 80 e também erra 25.** 58 são confiantes e 47 estão na fila; 14 têm predição vazia.
**83 dos 105 estão DENTRO da unidade certa** — dano contido; só 9 vêm com a unidade também errada.
Por rota: **77 nascem na 1ª passada**, 23 na propagação por headings, 5 no rótulo decomposto.
**Concentração: 10 pares (curso, tópico) concentram 71 dos 105 = 68%**; o IA sozinho são 2 tópicos (25 + 8).

### 22.3 O seletor, com o critério corrigido (`c1-3/seletor_topicos_carentes_12-09.{py,log,csv}`)

**Critério, nenhum usa gold:** um tópico tem *suporte lexical* se existe pelo menos um material da sua unidade em que o
scorer registra `exact_hits > 0` (casou uma **frase** do rótulo/alias) ou `overlap ≥ 1` (casou um **token** específico).

| seletor | tópicos marcados | pega dos 10 alvos |
|---|---|---|
| "sem alias textual no cru" (antigo) | 144/217 = 66% | 5 |
| "nunca vence no cru" (antigo) | 137/217 = 63% | 6 |
| CARENTE-FORTE (nenhum suporte lexical) | 14/171 = 8% | **0** |
| **CARENTE-FRACO+FORTE (sem suporte por FRASE)** | **70/171 = 41%** | **7** |

O critério novo **marca bem menos e pega mais**. O CARENTE-FORTE puro é inútil para este alvo (os tópicos sem nenhum
suporte não são os que concentram erro).

**Os 3 alvos que escapam têm suporte por frase** (MF `provadores-de-teoremas` 2, ES2 `estudo-de-caso-...` 6,
CG `segmentacao` 8): neles o vocabulário existe e **perde a competição** — é outro problema, não ausência.

### 22.4 O ganho do seletor, medido contra o ganho dirigido pelo gold (`c1-3/ganho_do_seletor_12-09.{py,log}`)

Devolvendo vocabulário só nos K tópicos que cada critério aponta (proxy: os sinônimos que o sidecar do LLM já tem
para aqueles tópicos). Base cru = 147/251 aceito.

| K | SELETOR (sem gold) | dirigido pelo GOLD | custo de não ver o gold |
|---|---|---|---|
| 5 | **178 = 70,9%** | 188 = 74,9% | −10 |
| 10 | 175 = 69,7% | 195 = 77,7% | −20 |
| 15 | 176 = 70,1% | 202 = 80,5% | −26 |
| 20 | 173 = 68,9% | 205 = 81,7% | −32 |
| 30 | 184 = 73,3% | 211 = 84,1% | −27 |
| 40 | **191 = 76,1%** | 219 = 87,3% | −28 |

> **CORRIGIDO na §23:** a atribuicao abaixo esta errada. O ganho nao vem do criterio do seletor — vem de DOIS topicos
> de UM curso (IA), e o baseline ingenuo "maior unidade" chega ao mesmo 178 sem usar criterio lexical nenhum.

**Dois resultados:**
1. **O seletor cego funciona:** com 5 tópicos curados o cru vai de 58,6% para **70,9%** (+31 materiais). Com 40, 76,1%.
2. **A curva NÃO é monotônica** — K=10 (175) é pior que K=5 (178), e K=20 (173) é pior ainda. **Curar tópico que não
   precisa PIORA**, porque alias a mais vira empate no detector (o mesmo mecanismo que fez o teto subir quando tiramos
   aliases, §11.4). **O seletor tem que ser preciso, não abrangente** — e isso inverte a intuição de "curar mais é
   melhor", que era como eu vinha pensando o problema.

O top-5 do seletor, que é a fila que um curso novo receberia: IA `modelos-descritivos`, IA `modelos-preditivos`
(os dois alvos do IA, unidade com 39 materiais), MF `sistema-de-prova`, MF `softwares-de-suporte-a-verificacao-formal`,
ES2 `conceito-de-devops`.

### 22.5 O que falta (e é o que o astra vai responder quando voltar)

- **Validar o seletor fora da amostra.** O ranking usa "materiais na unidade" como dano potencial, o que não usa gold —
  mas o *critério* foi desenhado olhando estes 7 cursos. O teste honesto é o LR, que não tem gold de subunidade.
- **O proxy de curadoria é otimista:** devolver os sinônimos que o LLM já tem não é o mesmo que um curador escrever a
  lista. A não-monotonicidade sugere que uma lista humana com ruído pode render menos.
- **Os 3 alvos com suporte por frase** (competição, não ausência) precisam de outra alavanca — provavelmente no scorer.
- **Os 25 que o produto também erra** continuam sem diagnóstico.

## 23. "MAS ESSE NÚMERO SÓ AUMENTOU POR CONTA DO GOLD" — auditado, e a desconfiança achou outra coisa (12/09, noite)

O usuário desconfiou do ganho do seletor (§22). Auditoria em duas frentes, cada uma com refutador adversarial.
**Resultado: o gold não entra nos dados — mas a minha conclusão cai por um motivo pior, e as duas auditorias foram
elas mesmas refutadas em parte.**

### 23.1 O gold NÃO entra na cadeia de dados (MEDIDO)

- **O motor nunca lê arquivo de gold.** Varredura em `src/builder/**`: as únicas ocorrências de "gold", "*.csv" e
  "docs/reports" são **comentários de procedência**. Nenhum `open()`.
- **A entrada da compilação de vocabulário é só o curso**: nome da disciplina, título da unidade, rótulos dos tópicos do
  plano e, por material, título + label do Moodle + até 24 headings (`vocabulary_compile.py:167-180`).
- **552 dos 560 sinônimos publicados estão literalmente nos títulos/headings do próprio curso (98,6%).** Os 5 sem
  atestação nenhuma estão em MF/TCC/CG — **fora dos tópicos que produzem o ganho**.
- **Os filtros que foram escolhidos olhando o gold carregam ZERO do ganho:** devolvendo `_raw` (a saída crua do LLM,
  antes dos filtros) em vez dos `synonyms` publicados, K=5 = **178** e K=40 = **191** — idênticos. Os META_LABELS e o
  veto de título não movem um material.

**A única dependência de gold que sobra:** o **prompt** do compilador foi selecionado medindo contra o gold
(`vocabulary_compile.py:74`: *"Prompt v2 — o unico ajuste permitido, medido (IA 34 -> 37/39)"*) — **e o IA é exatamente
o curso que produz 100% do ganho**. Não é testável offline; exigiria recompilar o sidecar do IA com o prompt v1.

### 23.2 O que derruba a minha conclusão: não são 5 tópicos, são 2 — e de um curso só

| tópico liberado (meu top-5) | ganho |
|---|---|
| IA `modelos-preditivos` | **+23** |
| IA `modelos-descritivos` | **+6** |
| MF `sistema-de-prova` | **+0** |
| MF `softwares-de-suporte-a-verificacao-formal-de-programas` | **+0** |
| ES2 `conceito-de-devops` | **+0** |

**Os dois tópicos do IA sozinhos já dão 178.** E o baseline ingênuo **"maior unidade"** — que ignora inteiramente o meu
critério de suporte lexical — chega ao **mesmo 178** em K=5 e **ganha** em K=10 (182 × 175) e K=20 (190 × 173).
Os dois rankings coincidem exatamente nos 2 tópicos do IA.

**Conclusão honesta: o meu seletor não seleciona nada.** O que existe é **um curso com uma unidade de 39 materiais** em
que o vocabulário faz uma diferença enorme. Qualquer ranking que ponha esses 2 tópicos no topo chega ao mesmo lugar.
A frase que publiquei em §22 — *"5 tópicos curados levam o cru de 58,6% a 70,9%"* — está **errada na atribuição**:
o mecanismo não é o critério, é a concentração do problema num curso.

### 23.3 As auditorias também foram refutadas (e isso importa)

O refutador pegou a primeira auditoria **defendendo o número**: ela apresentou como "CONTRAPROVA DECISIVA" um teste
entre três variantes que, medidas antes de rodar o motor, **eram a mesma taxonomia** (0 aliases de diferença em K=5).
Um teste que não podia falhar, publicado como decisivo. E testava *conhecimento externo*, que não era a hipótese do
usuário — ele falou de **gold**, não de termo inventado.

O que sobreviveu das duas: a varredura de código, a atestação dos 560 sinônimos, a medição `_raw` × `synonyms`, a
decomposição por tópico e o baseline aleatório (7 sementes: 148,4 ± 2,6 em K=5, contra 178 do seletor e 178 do
"maior unidade").

### 23.4 O que fica de pé, com o número certo

**Liberar dois tópicos de uma unidade de 39 materiais no IA leva o cru de 147 para 178 (58,6% → 70,9%).** O vocabulário
usado é derivado do próprio curso (98,6% atestado nos headings e títulos), não do gabarito. **Mas isso é um resultado
sobre um curso e uma unidade, não sobre um método de seleção** — e o teste que decidiria o que sobra (recompilar o
sidecar do IA com o prompt v1, a única peça calibrada no gold) exige uma chamada de LLM e não foi feito.

**O que eu levo disso:** apresentei "o seletor funciona" a partir de um agregado que era um curso. A desconfiança do
usuário estava certa em substância, ainda que a causa fosse outra — e o baseline "maior unidade", que eu tinha rodado e
tinha na mão, já mostrava isso antes de eu publicar a conclusão.

## 24. ATACAR A UNIDADE: "faltam 3 materiais" é verdade aritmética e armadilha de método (13/09)

Ordem do usuário: *"vamos atacar a unidade primeiro, só faltam 3 materiais"*. É verdade — 253/284, e 90% exige 256.
Mas a decomposição dos 31 erros mostra que perseguir 3 seria ajuste ao benchmark, e mostra onde está a alavanca real.

### 24.1 Os 31 erros têm TRÊS naturezas, não uma

| n | natureza | o que significa |
|---|---|---|
| **17** | **contradição ADJUDICADA** | o motor segue o BLOCO por desenho; o usuário adjudicou a unidade CURRICULAR em 12/09 |
| **10** | alavanca de vocabulário | o produto acerta e o cru erra |
| 4 | resto | CG texturas/mapeamento: nem adjudicado, nem o produto acerta |

Os 17 são **exatamente** as linhas de `contradicoes_unidade_material_gt_vs_bloco.csv`: MF t1/t2/aws/eth2,
SO threads/semáforos/pthread, ES2 microsserviços/azure. **Não são defeito do motor** — são a régua curricular contra o
desenho dele. Corrigi-los exige mudar a precedência bloco → unidade, que é decisão de arquitetura, não conserto.

Para dimensionar (e **isto é cenário, não resultado** — tirar do denominador é decisão do usuário sobre o que a régua
cobra): sem os 17, o cru iria de 89,1% para **94,8%** e o produto de 92,6% para 98,5%.

### 24.2 A alavanca óbvia foi medida e REFUTADA

O padrão que salta nos 10 que o produto acerta: `resolucao-de-prova-de-computacao-grafica-**2d**` vai para
`unidade-08-sintese-de-imagens` existindo `unidade-04-processo-de-visualizacao-**2d**`; e a versão `-3d` vai para a
unidade **2D**. O título carrega o discriminante e o motor não usa.

Medido (`c1-3/titulo_nomeia_unidade_12-09.{py,log}`): o título sugere exatamente uma unidade em **48 de 284** materiais
e bate o gold em 30. Mas **sobrepor sempre PERDE**:

| corte | dispara (cru) | ganha | perde | saldo cru | saldo produto |
|---|---|---|---|---|---|
| sempre | 23 | 4 | 13 | **−9** | **−14** |
| só na fila | 15 | 4 | 7 | −3 | −4 |
| só com conflito | 5 | 1 | 2 | −1 | −2 |
| **só dimensional (2d/3d)** | 3 | 3 | 0 | **+3** | 0 |
| só com 2+ tokens | 0 | — | — | 0 | 0 |

### 24.3 Por que eu NÃO vou usar o corte que dá exatamente +3

O corte dimensional dá **+3 no cru e 0 no produto** — precisamente o que falta para 90,1%. E é por isso que ele tem que
ser recusado:

1. **Eu o desenhei olhando os erros.** Vi o padrão 2d/3d na lista de erros (que vem do gold) e escrevi a regra que os
   descreve. Ganhar 3 e perder 0 não prova generalidade — prova que descrevi bem os 3 casos que vi.
2. **Só pode disparar em 1 dos 6 cursos.** MF, SO, IA, ES2 e TCC têm **zero** unidades com token dimensional; só o CG
   tem duas (`...-2d` e `...-3d`).
3. **Os 3 materiais são 2 documentos.** `resolucao-...-2d` e `resolucao-...-2d-html` apontam para o **mesmo arquivo
   fonte** (`...-2d.html`), com o mesmo título — é a duplicata de documento que o astra já tinha apontado ao dizer que
   "251 entradas não são 251 evidências independentes".

**Ou seja: dá para cruzar a meta da unidade hoje, e seria trapaça.** Registro a regra como medida e recusada.

### 24.4 A alavanca que sobra, e ela reabre uma frente fechada

Os 10 em que o produto acerta e o cru erra são de novo **vocabulário** (SO: `laminas-sockets` → o cru manda para
`deadlock`, o gold quer `programacao-concorrente`; CG: `basico3d` → o cru manda para `fundamentos-matematicos`, o gold
quer `representacao-e-modelagem`).

E os 17 adjudicados apontam para a frente que o handoff §5 deixou explicitamente em aberto:

> *"'Bloco vence' 34/35 era circular (o gold de unidade era o próprio bloco); com a régua curricular: 21/33 × 12/33.
> As refutações de 'texto vence' de 05/09 foram medidas contra o gold por bloco: reabrir só com a regra estreita
> (seção específica mapeada ao plano, corroborada pelo material, supera bloco misto), Gate 1."*

**A régua mudou de temporal para curricular em 12/09, e as refutações de "o texto vence o bloco" foram medidas contra a
régua velha.** Os 17 adjudicados são exatamente os casos em que o texto queria uma coisa e o bloco outra. **Essa é a
alavanca real do eixo unidade** — e é Gate 1, porque mexe na precedência do motor.

## 25. "O MOTOR DEVERIA SEGUIR O PLANO, NÃO O BLOCO" — medido, e a implementação ingênua perde (13/09)

Decisão do usuário. Antes de desenhar a mudança, a medição — e ela muda o que a decisão significa na prática.

### 25.1 Onde a precedência mora, e por que ela é como é

`src/builder/routing/file_map.py:802-807`. Quando o texto e o bloco discordam, **o bloco decide** e o texto vira
registro de conflito. O comentário diz por quê:

> *"2026-08-21: a verdade de unidade é, por construção, a unidade do bloco (ground_truth |><| gold_units). Medido nos 5
> cursos (188 entries): scorer de texto 130, unidade do bloco temporal 162 ... O bloco decide; o texto discordante vira
> registro de conflito para auditoria, nunca decisão."*

**A medição que sustenta a precedência é circular por admissão própria** — a régua *era* a unidade do bloco. Em 12/09 a
régua virou CURRICULAR. Refiz a comparação contra ela.

### 25.2 "Texto vence sempre": REFUTADO, mesmo contra a régua curricular

| | conflitos | texto certo | bloco certo | trocar a precedência |
|---|---|---|---|---|
| CRU | 53 | 17 | **32** | **−15 materiais** |
| PRODUTO | 33 | 12 | **19** | **−7 materiais** |

Mesmo com a régua que o usuário adjudicou, **o bloco acerta quase o dobro** nos conflitos. A decisão está certa como
princípio; a implementação literal piora o motor.

### 25.3 A regra estreita: os cortes que eu supus falharam, os dados apontaram outro

Testei "bloco misto", "bloco de método fraco" e "texto confiante" — **todos perdem**. A distribuição por método do bloco
mostrou que eu tinha classificado ao contrário:

| método do bloco | texto certo | bloco certo | leitura |
|---|---|---|---|
| `disamb` (desempate ativo) | 1 | **19** | o bloco usou sinal: é forte |
| **`janela-1`** (proximidade temporal) | **11** | 6 | o bloco veio de proximidade, não de conteúdo: é fraco |

Cortes derivados disso, com o teste de aprovação (ganhar no cru **e** não regredir o produto):

| corte | cru | produto | passa? |
|---|---|---|---|
| sempre | −15 | −7 | não |
| só `janela-1` | +5 | +2 | **passa** |
| `janela-1` e texto confiante | +6 | +1 | **passa** |
| **`janela-1` ou `due-*`** | **+7** | **+5** | **passa** |
| tudo menos `disamb*` | +4 | −3 | não |

### 25.4 Por que eu NÃO chamo isso de regra pronta

**O ganho é concentrado e o sinal não é consistente por curso.** No corte melhor (J), no CRU:

| | MF | SO | IA | ES2 | TCC | CG |
|---|---|---|---|---|---|---|
| saldo | −1 | **+7** | −1 | +2 | −1 | +1 |

**3 cursos positivos, 3 negativos** — o +7 agregado é essencialmente o SO. E no produto o CG perde 3. É o mesmo padrão
que me enganou no seletor de tópicos (§23): agregado positivo, mecanismo concentrado num curso.

Além disso, **o corte foi derivado olhando a distribuição dos erros**, que vem do gold. A diferença em relação ao corte
dimensional que recusei em §24.3 é real mas não suficiente: aqui há **mecanismo plausível** (`janela-1` atribui por
proximidade temporal, não por conteúdo; `disamb` usou sinal para desempatar), dispara em **19 casos e 6 cursos** (contra
3 casos e 1 curso), e **não regride o produto**. Mas continua sendo hipótese, não regra validada.

### 25.5 O que isto deixa para decidir

A decisão "o motor deve seguir o plano" tem três implementações possíveis, e os números dizem coisas diferentes:

1. **Texto vence sempre** — o que a frase diz literalmente. **Medido: −15 no cru, −7 no produto.** Não fazer.
2. **Texto vence quando o bloco veio de proximidade temporal** (`janela-1`/`due-*`). **Medido: +7 no cru, +5 no
   produto**, mas concentrado no SO e negativo em 3 dos 6 cursos. É a única família com saldo positivo.
3. **A régua para de cobrar os 17 adjudicados** — se o motor está certo por desenho ao seguir o bloco, quem precisa
   mudar é o que a régua cobra, não o código. Sem tocar em nada, o cru vai de 89,1% para 94,8%.

As opções 2 e 3 não são excludentes. A 2 mexe no motor e precisa de validação fora da amostra; a 3 é decisão de régua.

## 26. OPÇÃO 3 FEITA (sem inflar nada) e o GATE 1 DA OPÇÃO 2 (13/09)

O usuário pediu a 3 primeiro, depois a 2.

### 26.1 A opção 3, como eu a tinha formulado, contradizia a decisão dele

Eu havia escrito a opção 3 como *"se o motor está certo por desenho ao seguir o bloco, quem muda é o que a régua
cobra"*. Mas a decisão foi **"o motor deveria seguir o plano"** — ou seja, o motor está **errado** nesses 17.
Tirá-los do denominador seria inflar o placar escondendo erros que o próprio usuário classificou como erros.

**Feito, então, na forma que não mente:** o placar principal **não muda**; o medidor passa a **separar a natureza** dos
erros de unidade e a publicar o **teto da mudança de precedência**, que é a fila da opção 2.

| natureza dos erros de unidade | CRU | PRODUTO |
|---|---|---|
| total | 31 | 21 |
| **divergência de DESENHO** (bloco × plano adjudicado) | **17** | **17** |
| conflito bloco × texto não adjudicado | 5 | 1 |
| falha de sinal (sem conflito registrado) | 9 | 3 |

**Teto da mudança de precedência, medido:** unidade no cru iria de **89,1% para 95,1%** (253 → 270) e no produto de
92,6% para **98,6%** (263 → 280). *Isto não é desconto — é o tamanho da opção 2.*

Implementado em `c1-3/mede_3eixos_12-09.py::adjudicados()`, lendo
`docs/reports/contradicoes_unidade_material_gt_vs_bloco.csv`.

### 26.2 Gate 1 da opção 2: o que a regra alcança dos 17

| dos 17 adjudicados que o cru erra | n | o que a regra faria |
|---|---|---|
| texto certo **e** bloco veio de `janela-1`/`due-*` | **11** | corrige |
| texto certo, mas bloco veio de `ref-generica`/`titulo-topico` | 3 | fora do corte |
| texto **também** errado | 3 | não corrige (precisa de vocabulário) |

Por método do bloco: `janela-1` 11 (9 com texto certo), `ref-generica` 2, `due-contain` 2, `due-straddle` 1,
`titulo-topico` 1.

**Efeito líquido medido do corte `janela-1`/`due-*`** (13 ganhos − 6 perdas): **+7 no cru, +5 no produto**.
A unidade iria a **260/284 = 91,5%** no cru — **acima da meta de 90%** — e a 268/284 = 94,4% no produto.

### 26.3 O que o Gate 1 precisa decidir antes de eu escrever a regra

1. **O ganho é concentrado.** No cru: SO **+7**, ES2 +2, CG +1, mas MF −1, IA −1, TCC −1. **Três cursos ganham, três
   perdem.** No produto, o CG perde 3. O saldo agregado é positivo nos dois regimes, mas a regra **não é uniforme**.
2. **O corte foi derivado olhando a distribuição dos erros.** Tem mecanismo plausível (`janela-1` atribui o bloco por
   proximidade no calendário, não por conteúdo; `disamb` usou sinal para desempatar) e dispara em 19 casos de 6 cursos —
   diferente do corte dimensional que recusei em §24.3 — mas continua sendo hipótese derivada da amostra.
3. **As 6 perdas são reais e nominais** (MF `classes-parte1`, `introducao-zip`, `classes-parte2`; IA
   `survey-on-clustering`; TCC `aula-14-problema-da-correspondencia-de-post`; CG `colisao`). Em todas elas o bloco
   estava certo e o texto passaria a valer errado.
4. **Restariam 6 dos 17** fora do alcance da regra: 3 por método de bloco não coberto e 3 porque o texto também erra.

**O que eu faria, e é o que levo ao gate:** implementar o corte na precedência (`file_map.py:802-807`), com o teste de
aceitação sendo *ganha no cru e não regride o produto*, **e** um leave-one-course-out antes do commit — se a regra só
sobrevive com o SO dentro, ela não é regra, é o SO.

## 27. O LEAVE-ONE-COURSE-OUT MATA A OPÇÃO 2 COMO DESENHADA (13/09)

O usuário pediu o LOCO antes de decidir. Ele foi feito, e o veredito é negativo e limpo.

### 27.1 O desenho do teste

A regra tem **um** parâmetro: quais métodos de bloco contam como "fracos". Eu escolhi `{janela-1, due-contain,
due-straddle}` **olhando a distribuição nos 6 cursos**. O LOCO refaz essa escolha por fold:

> para cada curso c: escolhe os métodos com saldo > 0 usando **só os outros 5**, aplica no curso c e mede lá.

### 27.2 O resultado

| regime | dentro da amostra | **fora da amostra** |
|---|---|---|
| CRU | +38 | **−3** |
| PRODUTO | +29 | **−4** |

Por fold, no CRU: MF **−3**, SO 0, IA **−2**, ES2 +2, TCC **−1**, CG +1 → **2 positivos, 3 negativos, 1 neutro**.
No PRODUTO: MF 0, SO 0, IA 0, ES2 0, TCC −1, CG **−3** → **nenhum fold positivo**.

**E não é instabilidade de seleção:** o conjunto escolhido é o mesmo em 5 dos 6 folds (`janela-1`, `due-contain`,
`due-straddle`). A escolha é estável; **o que não transfere é o ganho**. A diferença dentro × fora é de **41 pontos** no
cru — isso é a medida do overfitting do meu corte.

### 27.3 O que isso fecha e o que deixa aberto

**FECHADO por negativo medido:** a mudança de precedência `bloco → unidade` restrita a método de bloco fraco. Não
implementar. Os +7 do cru e +5 do produto eram ganho dentro da amostra; fora dela o saldo é negativo nos dois regimes.

**Continua de pé o que veio antes:** "texto vence sempre" já estava refutado (−15 no cru, −7 no produto), agora com a
versão restrita também refutada, **a família inteira de "trocar a precedência por regra derivada do método do bloco"
está fechada.**

**O que NÃO foi testado e continua aberto:** a mudança de precedência por **princípio de produto**, aceitando o custo.
A decisão do usuário — *"o motor deveria seguir o plano, não o bloco"* — pode ser um princípio de arquitetura, e não uma
busca por ganho de placar. Nesse caso o número honesto é: **o cru cairia de 89,1% para 83,8%** (253 → 238, o saldo −15) e
o produto de 92,6% para 90,2% (263 → 256). **Os 17 adjudicados seriam corrigidos, e outros 32 casos passariam a errar.**

Isso é escolha de produto, não medição: seguir o plano é conceitualmente o que o usuário quer, e custa 15 materiais no
cru. Registro os dois números para a decisão ser feita com o preço na mão.

### 27.4 O que sobra para o eixo unidade

1. **A unidade já está em 89,1% no cru e 92,6% no produto.** A meta de 90% no cru fica a 3 materiais — e nenhuma das
   duas alavancas testadas (título, precedência) os entrega honestamente.
2. **A única alavanca que resta com sinal positivo são os 10 em que o produto acerta e o cru erra** — e ela é
   vocabulário, o mesmo mecanismo da subunidade (SO `laminas-sockets` → o cru manda para `deadlock`, o gold quer
   `programacao-concorrente`).
3. **Isso reforça o que a §19 já dizia:** o eixo que precisa de trabalho é a subunidade, e o mecanismo é vocabulário —
   não precedência, não título, não SARC.

## 28. AQUISIÇÃO DE VOCABULÁRIO: o astra analisou e desenhou — e derrubou 4 afirmações minhas (13/09)

Ordem do usuário: *"coloque o astra para analisar e para desenhar a aquisição de vocabulário"*.
Brief: `c1-3/brief_codex_astra_aquisicao_vocabulario.md`.

**Duas corridas independentes responderam o mesmo brief** (o primeiro processo não tinha morrido e as duas terminaram):
`c1-3/resposta_codex_astra_aquisicao_vocabulario.md` e `..._corrida2.md`. **Elas convergem nas quatro correções e no
veredito**; divergem só nos números de ORÇAMENTO, que as duas marcam como decisão, não como parâmetro medido.
O acidente virou réplica: quatro correções encontradas duas vezes, por caminhos independentes.

**Veredito, nas palavras da corrida 2:** *"Vocabulário é a melhor alavanca demonstrada. Ainda não há evidência de que
aquisição, sozinha, entregue 90%. O desenho precisa selecionar relações termo→tópico e controlar aliases concorrentes."*

### 28.1 A descoberta que motivou o brief (minha, medida)

O sidecar que o regime cru conserva (`course/.glossary_curation.json`) **não é curadoria humana**: o `_nota` dele diz
*"GERADO automaticamente de fontes do PROFESSOR (SARC + seção do Moodle + título/headings), sem olhar gold nenhum —
`gera_sidecar_professor.py`, 2026-09-07"*. São **66 termos em 15 tópicos** contra **560** do sidecar do LLM, e boa parte
é token de nome de arquivo e de autor (`chiara`, `lacerda`, `luca`, `capitulo`, `demo`, `fato`, `massa`).

**A diferença entre cru e vocab não é humano × LLM — é ruído × vocabulário de domínio.** Os dois adquiridores leem o
mesmo acervo (98,6% dos sinônimos do LLM estão atestados nos headings do próprio curso); o determinístico devolve
`chiara`, o LLM devolve `k-NN`.

### 28.2 AS QUATRO CORREÇÕES — as três primeiras verificadas por mim, e procedem

**(1) "Só os 5 do CG são termos de domínio" está errado.** IA tem `crossover`, `geneticos`, `implementacaominimax`;
ES2 tem `circuitbreaker`, `fanout`, `nameserver`, `gateway`. **E o ponto é mais afiado que o meu:** `crossover` está em
`Algoritmos de Busca com Informação`, quando o operador é de algoritmo genético — pertence a `Problemas de Otimização`.
**Reconhecer o termo técnico não basta; ele precisa apontar para o tópico certo. A aquisição é de RELAÇÃO
termo→tópico, não de lista de termos.**

**(2) O sidecar "cru" tem proveniência MISTA, e parte dele foi escolhida medindo contra a régua. VERIFICADO.**
Os `_nota` por entrada dizem, com todas as letras:

| entrada | o que o `_nota` diz |
|---|---|
| ES2 `1.5 Estudo de caso` → `gateway` | *"12/09 ... medido no replay sincronizado ... E5 só 'gateway' +1 (roteiro3-gateway), 0 perdas; 'microsservicos' rejeitado como ajuste ao gold"* |
| CG `7.1.1*` → curvas (3 entradas) | *"12/09 ... medido no replay sincronizado ... E4 curvas +2 (exercicios-sobre-curvas x2), 0 perdas"* |
| CG `1.4 Aplicações` → `OpenGL` | *"12/09 (ruling do user 11/09) ... Medido: só 'OpenGL' em 1.4 -> u01"* |
| SO `3.1 Conceitos básicos` → `veto` | *"veto 12/09 (user, orch-fix-defect) ... Medido: ..."* |

**Consequência: minha frase "a única dependência de gold que sobra é o prompt v2" está errada.** O número do cru
carrega **+3 de subunidade** (2 curvas + 1 gateway) de intervenções selecionadas **medindo contra a régua**, mais o
pino de OpenGL e o veto do SO no eixo unidade. Não é leitura do arquivo de gold — é seleção pelo benchmark, o mesmo
vício que recusei em §24.3 e que o LOCO puniu em §27.

**(3) Os 10 da unidade NÃO são vocabulário. VERIFICADO, e derruba o que publiquei ontem.**

| unidade (284) | NU | RÉGUA | VOCAB | PRODUTO |
|---|---|---|---|---|
| acertos | 244 | **253** | **255** | **263** |

**RÉGUA → VOCAB é +2. VOCAB → PRODUTO é +8.** Dos 10, só 2 são vocabulário; **8 são o voter** — chamada de LLM em
runtime, não vocabulário offline. E o exemplo que eu dei ao usuário é justamente o que não funciona: **o SO fica em
27/37 em RÉGUA e em VOCAB** (`motor_3eixos_v2_12-09.log:42,91`), e só vai a 29/37 no produto.
Evidência: `motor_3eixos_v2_12-09.log:35,84,133` · `motor_3eixos_produto_12-09.log:34`.

**(4) Contagem dos erros compartilhados.** O produto erra **27**, não 25: os 25 compartilhados **não incluem 2
regressões só do produto**. Dos 25, **24 estão na unidade certa**, **6 têm gold vazio** e **16 são do CG** — e nos 5
vazios do CG as notas do gold registram *"assunto sem subtópico correspondente dentro da unidade exigida"*.
**Acrescentar alias positivo não representa uma ausência.**

### 28.3 O que separa `perceptron` de `chiara` — a resposta

> *"Função no contexto e relação com a taxonomia. Um designa técnica; o outro pode aparecer como autoria. Frequência,
> concentração e posição em heading não estabelecem essa diferença. Sobrenomes também nomeiam técnicas: banir nomes
> próprios derrubaria termos válidos."*

**É computável sem LLM quando existe conhecimento adicional:** marcação de autoria, definição explícita no texto,
ontologia técnica com relações categoria→técnica, ou curador humano. *"Um dicionário que apenas reconhece palavras
técnicas ainda não resolve `perceptron → Modelos Preditivos`."*

**Não há declaração de impossibilidade:** *"Não demonstramos que LLM seja indispensável; tampouco demonstramos
aquisição automática suficiente sem ele."*

E corrige o meu experimento mental: os dois adquiridores **não recebem a mesma entrada** — determinístico usa até 8
headings, tokens isolados, mínimo de 4 chars (que já derruba sigla curta), e herda o tópico da seção; o LLM usa até 24
headings cortados em 60 chars, expressões, siglas e nomes de membros de ZIP, e classifica semanticamente.
**Então "é só a seleção" é hipótese, não medição isolada.** (`gera_sidecar_professor.py:103-150` ·
`vocabulary_compile.py:173,239`)

### 28.4 O DESENHO (limites marcados por ele como orçamento, não como parâmetro medido)

**A unidade de aquisição deixa de ser palavra e passa a ser RELAÇÃO com evidência:**

```json
{"term": "k-NN", "topic_key": "<código e rótulo do plano>", "relation": "tecnica",
 "evidence": [{"entry_id": "<material>", "field": "heading", "quote": "<trecho literal>"}]}
```

*"Isso é mais precisamente um indicador de tópico: `k-NN` não é sinônimo de 'Modelos Preditivos'."*

- **Fonte:** plano como taxonomia; título, label do Moodle e headings originais como evidência. **Não** usar previsão
  de subunidade, alias propagado, confiança, fila, gold, nem resumo de código derivado do próprio vocabulário.
- **Escopo: a unidade prevista organiza lotes, não exclui destinos.** Cada chamada recebe o catálogo de tópicos do
  curso inteiro. Hoje a restrição existe em `vocabulary_compile.py:240-261` — *"um material mal colocado pode nunca
  mostrar ao compilador seu tópico correto"*.
- **Admissão:** expressão literal + material/campo/trecho + relação explícita (técnica, algoritmo, protocolo, conceito
  ou ferramenta ensinada naquele tópico). Menção bibliográfica e enumeração de assuntos não bastam. **Termo
  compartilhado entre tópicos não ganha exclusividade artificial: fica pendente.** Nome próprio **não** recebe veto
  universal.
- **Seleção de tópico: abandonar o "carente".** Examinar todos; publicar só onde houver relação aprovada. Ordenar lotes
  por quantidade de materiais, desempate pelo código curricular — *"é o baseline simples já competitivo"*.
- **Seleção dentro do tópico:** agrupar variantes do mesmo conceito; priorizar a expressão que cobre mais materiais
  **ainda não cobertos** por outra expressão aprovada. *"Isso mede cobertura textual, não acurácia."*
- **Gravação:** relações aprovadas em `.glossary_curation.llm.json` (formato que o loader já consome), evidência e
  rejeições em metadados; `.glossary_curation.json` reservado para intervenção humana.

**Orçamento — as duas corridas divergem, e as duas dizem que é decisão, não medida:**

| | corrida 1 | corrida 2 |
|---|---|---|
| chamadas por curso | **B**, determinado pelo empacotamento antes da 1ª chamada | ≤ 8 |
| publicação | 8 conceitos/tópico × 3 variantes | 3 termos/tópico, 24 relações/lote |
| entrada | 24.000 chars por chamada | 24.000 chars por chamada |
| saída | 4.096 tokens | 2.000 tokens |

A corrida 1 recusa número fixo: *"Não existe número constante honesto para cursos de tamanhos diferentes."*
Nas duas: **sem retry invisível**; esgotou, para com cobertura parcial **explícita**.

**NÃO fazer:** aumentar K até melhorar o placar; usar `score > 0` como evidência; excluir termo porque aparece em
outra unidade; preencher tópico sem evidência; promover heading pela própria previsão; tratar toda ocorrência de uma
expressão como aula daquele assunto.

**E a ablação que o experimento tem que ter:** `content_taxonomy.py:603` recria alias errado depois da aquisição.
*"Comparar, como ablação previamente definida, ADIÇÃO versus SUBSTITUIÇÃO dos aliases adquiridos automaticamente.
Não presumir que desligar a doação melhora o resultado."*

### 28.5 O contrato de LLM e os 4 defeitos do compilador atual (com linha)

| defeito | linha |
|---|---|
| qualquer arquivo "manual" bloqueia TODA a compilação, mesmo parcial | `vocabulary_compile.py:227` |
| cache é a existência do arquivo, **sem chave de conteúdo** | `:230` |
| sem unidade prevista, não compila e espera outro reprocessamento | `:245` |
| `_raw` guarda termos mas **não conserva bundle, citação nem versão do prompt** | `:197` |

**Contrato proposto:** uma versão publicada por snapshot de entrada; cache por hash de (taxonomia + materiais
apresentados + prompt + schema + modelo); conservar entrada exata, resposta bruta, relações aprovadas **e rejeitadas**
com motivo, tentativas e consumo. *"A existência do arquivo manual deve proteger decisões humanas, não significar
'curso inteiro já coberto'."* — sem isso não há aquisição incremental.

**O curador humano pode substituir a chamada** — mesmo material, mesmo contrato de evidência. **Mas copiar
`.llm.json` para `.json` não dá comportamento idêntico:** o loader filtra nome de seção **só no arquivo LLM**
(`src/builder/artifacts/repo.py:1728,1732,1753`).

**"LLM é necessário?"** — *"Não necessariamente. Necessária é alguma fonte de competência semântica. O LLM é a
alternativa automatizada com sinal positivo disponível."* O número sem ele: **146/251 = 58,2%**, com a ressalva de que
*"não existe medição que autorize afirmar um teto para curadoria humana, glossário externo ou novo classificador
determinístico"*. A campanha determinística antiga (146/233 = 62,7%) **é outra base e não substitui esse número**.

**A frase que o usuário precisa decidir:** *"Atribuição determinística usando vocabulário previamente compilado por LLM
é possível. Porém, no experimento atual, isso corresponde ao braço VOCAB, não à RÉGUA. Se 'cru' proíbe LLM em toda a
cadeia, a alternativa é curador/ontologia; ainda não existe resultado que assegure 90% nessa condição."*

### 28.6 A validação — e por que o LR não basta

*"Não existe validação de '90% correto' sem alguma verdade de referência. Sem adjudicação, podemos verificar
procedência, cobertura, estabilidade e colisões. Nenhuma dessas medidas substitui acurácia."*

**O LR tem 7 entradas, 1 é cronograma → 6 materiais instrucionais, todos na mesma unidade** (verificado no manifest).
**E ele JÁ TEM `.glossary_curation.llm.json`** — *"portanto não é um teste de partida sem artefatos"*; os braços
precisam ser reconstruídos das fontes, sem herdar o sidecar. Adjudicar com dois julgamentos independentes e cegos
(unidade, tópico primário, alternativas aceitáveis, ausência legítima, trecho de sustentação), com o contrato de
elegibilidade escrito **antes**.

**Mas 6 materiais não validam transferência:** *"mesmo 6/6 resulta em limite inferior unilateral de 95% de
aproximadamente 60,7%"*. LR serve para verificar o **procedimento**, não a acurácia.

**Orçamento de avaliação — as duas corridas:** corrida 1 pede **300 materiais em 6 cursos novos, 50 por curso**;
corrida 2 pede **200 em pelo menos 4**. As duas marcam como compromisso operacional, não tamanho mágico.
A corrida 1 dá a conta: **279/300 = 93% passa o teste unilateral de 5% contra 90%; 270/300 só atinge a meta pontual** —
e avisa que material do mesmo curso é correlacionado, então isso não é certificado de generalização.

**Braços obrigatórios no mesmo snapshot:** base congelada · compilador v2 atual · **maior unidade** · aleatório com
sementes fixas · **todos os termos admissíveis** (para testar se a esparsidade evita dano). Orçamento igual, não só K
igual. Abstenção fica no denominador.

**Sobre o prompt v2:** congelar e testar prospectivamente mede transferência do v2, **não torna o desenvolvimento dele
independente do benchmark**. Para isolar v1→v2: recuperar o v1 exato do histórico, compilar os dois em cursos novos com
corpus/modelo/orçamento pareados, congelar e só então abrir a adjudicação. *"Recompilar o IA mede sensibilidade dentro
da amostra, não transferência."* E: *"a dependência não se limita ao prompt: há curadorias posteriores medidas no
benchmark, como `gateway`."*

### 28.7 A meta, e os 5 passos com parada

**90% = 226/251 na subunidade e 256/284 na unidade.** O VOCAB completo entrega **220/251**; a seleção dirigida por gold
entrega 222/251 — *"um resultado de uma seleção, não um teto matemático"*. **Faltam 6 na subunidade e 3 na unidade.**
*"Nenhum dado demonstra que o desenho proposto os entregará."* A faixa 87,6–88,4% é **capacidade histórica observada
com vocabulário, não previsão para curso novo**.

1. Congelar proveniência e denominadores. **Parar** se o baseline não reproduzir ou houver artefato sem origem.
2. Produzir candidatos com orçamento fixo. **Parar** ao esgotá-lo; publicar só relação com evidência válida.
3. Medir no motor completo dos 7 cursos, **separando aquisição de retirada de alias**. Não chamar isso de transferência.
4. Avaliar prospectivamente: LR primeiro, cursos novos como transferência. **Abrir os rótulos uma vez.**
5. Decidir pelo resultado. Se o resíduo for competição, ausência válida ou falta de conteúdo, **encerrar aquisição como
   explicação** e tratar a classe demonstrada.

**Sobre a unidade, ele desaconselha peça nova:** *"Não proporia peça nova de unidade antes de decompor esses 10 nos
três braços."* E não reabrir precedência — medir o trajeto completo do alias até a unidade final
(`file_map.py:788-789`).

**O próximo passo que as duas corridas nomeiam:** *"congelar os sidecars por entrada e proveniência. O snapshot atual
já contradiz a premissa 'todo o preservado veio do professor, sem seleção pelo benchmark'."*

## 29. OS SIDECARS CONGELADOS POR ENTRADA E PROVENIÊNCIA — e o cru perde 1,6 ponto (13/09)

Ordem do usuário: *"faça agora"* — o passo que as duas corridas do astra nomearam como próximo.
Instrumento: `c1-3/congela_sidecars_13-09.{py,csv,log}` e `c1-3/sem_curadoria_benchmark_13-09.log`.
Rede bloqueada e contada: **0 tentativas** nos três braços. `.ablacao/` verificada intacta depois.

### 29.1 O inventário: 628 pares (tópico, termo), e **0 sem proveniência**

A classe sai do metadado que a própria entrada carrega — não de julgamento meu.

| classe | termos | tópicos | cursos |
|---|---|---|---|
| `auto-professor` (script de 07/09, fontes do professor) | 60 | 9 | ES2, IA, SO, TCC |
| **`benchmark`** (a `_nota` diz que foi MEDIDA contra a régua antes de entrar) | **6** | 5 | CG, ES2 |
| **`veto`** (remoção, também medida) | **2** | 1 | SO |
| `llm-compilado` (1 chamada por unidade) | 560 | 114 | os 8 |
| `sem-metadado` | **0** | — | — |

**O critério de parada nº 1 do astra passa:** *"parar se houver artefato sem origem identificável"* — não há.

**Nominal, o que entrou no "cru" depois de ser medido:**

| classe | curso | tópico | termo | o que a `_nota` diz |
|---|---|---|---|---|
| benchmark | CG | `7.1.1.4 Catmull-Rom` | `Catmull-Rom` | *"E4 curvas +2 (exercicios-sobre-curvas x2), 0 perdas"* |
| benchmark | CG | `7.1.1.1 Bézier e Casteljau` | `Bézier`, `Casteljau` | idem |
| benchmark | CG | `7.1.1 Curvas Paramétricas` | `Curvas Paramétricas` | idem |
| benchmark | CG | `1.4 Aplicações` | `OpenGL` | *"ruling do user 11/09: OpenGL = u01 ... Medido: só 'OpenGL' em 1.4 -> u01"* |
| benchmark | ES2 | `1.5 Estudo de caso` | `gateway` | *"E5 só 'gateway' +1, 0 perdas; 'microsservicos' rejeitado como ajuste ao gold"* |
| veto | SO | `3.1 Conceitos básicos` | `Comunicação entre Processos`, `Pipes` | *"veto 12/09 (user, orch-fix-defect)"* |

### 29.2 A medição: três braços do motor COMPLETO, na mesma cópia, na mesma sessão

O braço A é reprodução do baseline — sem ele o delta dependeria do log de ontem.

| eixo | **A: régua (baseline)** | **C: sem o que o PLACAR escolheu** | **B: sem também o ruling do usuário** |
|---|---|---|---|
| bloco (237) | 222 = **93,7%** | 222 = **93,7%** | 222 = **93,7%** |
| unidade (284) | 253 = **89,1%** | 253 = **89,1%** | 248 = **87,3%** |
| subunidade (251) | 146 = **58,2%** | **142 = 56,6%** | 137 = **54,6%** |
| subunid. primário | 103 = 41,0% | 100 = 39,8% | 95 = 37,8% |

**O braço A reproduz o log de 12/09 dígito a dígito** (222 / 253 / 146 / 103). O baseline é reprodutível.

### 29.3 A separação é limpa, e cada peça faz uma coisa só

| o que foi removido | unidade | subunidade | onde |
|---|---|---|---|
| **ruling do usuário** (`OpenGL`, 1 termo) | **−5** | **−5** | CG |
| **curadoria escolhida pelo placar** (4 curvas do CG + `gateway` do ES2) | 0 | **−4** | CG −2, ES2 −2 |
| **veto do SO** (2 termos) | 0 | 0 | **inerte no cru** |

Três leituras que decorrem disso:

1. **O eixo unidade NÃO está contaminado por seleção do benchmark.** Os 5 materiais de unidade vêm inteiros do
   *ruling* do usuário sobre o OpenGL — decisão de produto do dono do curso, que um curso novo também teria. O
   **89,1% se mantém**.
2. **O eixo subunidade carrega +4 escolhidos por render ponto contra a régua.** O número honesto do cru é
   **142/251 = 56,6%**, não 58,2%. É 1,6 ponto, mas é exatamente o tipo de ganho que o LOCO mostrou não transferir.
3. **O veto do SO é inerte no regime cru**, como o loader já previa (`repo.py:1740-1746`: ele veta termos que o
   compilador LLM doou, e no cru o sidecar LLM está desligado). A medição confirma: SO idêntico nos três braços.

**E o efeito real é maior do que as notas declaravam.** As `_nota` diziam "+2 curvas" e "+1 gateway"; no motor
completo os 6 termos valem **5 de unidade e 9 de subunidade**, porque o efeito propaga para a reconciliação de
unidade — o que foi medido no replay subestima o que acontece no motor inteiro.

### 29.4 O placar do cru, corrigido

**Adoto o braço C como o cru de registro: 93,7% bloco · 89,1% unidade · 56,6% subunidade.**
Critério: curadoria humana é insumo legítimo do regime (o professor/dono decide, e um curso novo também teria isso);
curadoria **escolhida medindo contra a régua** não é — em curso novo não existe régua para escolher por ela.

| eixo | cru publicado até agora | **cru honesto** | meta |
|---|---|---|---|
| bloco | 93,7% | **93,7%** | ✅ bate |
| unidade | 89,1% | **89,1%** | faltam 3 materiais |
| subunidade | 58,2% | **56,6%** | faltam **84** materiais |

O buraco da subunidade cresce de 79 para **84 materiais**. Nada muda na conclusão estrutural — continua sendo um
eixo só, e o mecanismo continua sendo vocabulário.

### 29.5 O que este passo autoriza

Os dois critérios de parada do passo 1 do astra estão satisfeitos: **baseline reproduz** e **não há artefato sem
origem identificável**. O passo 2 (produzir candidatos de vocabulário com orçamento fixo) está liberado — e agora
com a linha de base certa, que é 142, não 146.
