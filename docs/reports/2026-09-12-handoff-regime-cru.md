# Handoff 12/09 — C1 fechada, C5 aberta, regime cru como frente nova

last_updated: 2026-09-12 (madrugada). **Este é o ponto de entrada vivo**; `2026-09-11-handoff-camada3.md` passa a ser histórico.
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

| régua (produto em disco, 0 chamadas) | valor | fonte |
|---|---|---|
| subunidade no produto | **224/251** (CG 64/82, MF 55/58, SO 15/15, IA 36/39, ES2 26/28, TCC 10/11, FR 18/18) | `c1-3/erros_subunidade_produto_12-09b.log` |
| subunidade, precisão do confiante | **178/193 = 92,2%**, 15 erros confiantes, recall da fila 12/27 | `calibra_fila_como_regua.py` |
| unidade, régua CURRICULAR (12/09) | 205/212 confiante = 96,7%; 21 erros = 17 adjudicados (o produto segue o bloco por desenho) + 4 do CG | idem |
| bloco | 188/189 = 99,5% | idem |
| conflitos texto × bloco | 39; com gold 33; bloco certo 21, texto certo 12 (era 31 × 1 contra o gold por bloco: circular) | `c1-3/mede_conflito_unidade.log` |
| regime cru (sem vocab LLM, curadoria mantida), 251 | **139 aceito / 97 primário (39%)**; só rótulos do plano 115 / 86 | `c1-3/replay_regime_cru_12-09.log` |
| teto das fontes cruas do professor (plano, SARC, seção, título, headings; taxonomia limpa), 227 | **61%** (SO 53, IA 95, ES2 68, TCC 70, MF 48, CG 51); "nenhuma" 22% | `c1-3/mede_fontes_do_professor_limpo_12-09.log` |
| FR do zero, primário /18 | crua 6 · só Datalab 6 · crua + vocab 16 · Datalab + vocab 17 · Datalab + LLM viva 17 · produto 16 | `c1-3/mede_fr_sem_gold_run*_12-09.log` |

Suite: 2347 passed, 4 skipped. Replay `.ablacao/` recopiado do produto (7 tutores; `new=False`, modo `com` = produto; CG difere em 2
materiais estáveis: `morfologiamatematicapptx`, `exercicioduascores`, replay vazio e produto certo).

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

Contexto para quem executa: o cru está em 39% primário / 55% aceito; o teto das fontes cruas do professor é 61%; os 22% de "nenhuma"
não são prova de conhecimento externo (falsos negativos por radical, sigla, sinônimo do plano); IA é o bolsão (SARC nomeia 87%, cru 5/39).

0. **Congelar a régua:** resolver as 2 divergências replay × produto do CG; toda tabela com aceito E primário; a lista dos 112 erros com
   coluna GOLD e slugs inteiros (hoje `replay_regime_cru_12-09.log` não tem gold e trunca). Inventariar fontes fora da tabela: ementa,
   bibliografia, nome de arquivo, ordem no Moodle.
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
