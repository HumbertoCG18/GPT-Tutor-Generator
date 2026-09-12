# Handoff 2026-09-11 — PONTO DE ENTRADA: camada 3 cortada, vocabulário LLM nos 8 tutores, zips sem colisão

Único handoff vivo. Substitui `2026-09-08-handoff-confianca.md` (que passa a ser histórico).
**Leia nesta ordem:** (1) este arquivo; (2) `pendencias.md`, seção "CAMADA 3 MEDIDA COM VOCAB NOVO" (11/09) e o bloco
"CORTE FEITO E ROLLOUT"; (3) `2026-09-08-plano-confianca-antes-de-acuracia.md` — 2.2 e 2.4 fechadas, 2.1 e 2.3 abertas,
Fase 1 FECHADA no gate (ver §2b); Fase 3 (cobertura) não tocada.

---

## 1. O que aconteceu em 11/09, em uma frase

O motor ficou com **duas camadas LLM** (voter de bloco e vocabulário compilado): o resumo de código por Gemini virou
**produtor determinístico** (`determ v3`), os zips ganharam identidade por membro, e a subunidade no produto foi de
**161 para 214 em 251** nos 7 cursos com gold, sem mover bloco em nenhum tutor.

---

## 2. Estado ao terminar (tudo commitado; push feito na madrugada de 12/09 por ordem do user: gerador `feat/motor-atribuicao` + 9 tutores nas branches deles; SEM merge na `main` do gerador, 1002 commits à frente)

Gerador: `feat/motor-atribuicao` @ `b6512fc` + este handoff. Suite 2345 verde, goldens verdes (SO e TCC regenerados de propósito).
Tutores (HEAD): MF `b8eae43` · SO `8fbd818` · IA `2f4f983` · ES2 `d986c44` · TCC `cc20668` · LR `a744954` · FR `c28937a` · CG `be74ee7`.
Chamadas Gemini do dia: **26** (16 de compilação de vocabulário em SO/IA/ES2/TCC + 10 votos do voter liberados), `gemini-3.5-flash`.

### Subunidade no produto, gold por curso (base 251)
| curso | antes (HEAD de 10/09) | agora |
|---|---|---|
| SO | 10/15 | **15/15** |
| IA | 4/39 | **36/39** |
| ES2 | 15/28 | **25/28** |
| MF | 51/58 | **55/58** |
| TCC | 8/11 | **10/11** |
| FR | 15/18 | **18/18** |
| CG | 58/82 | **57/82** (55 no rollout; +2 com o rótulo meta do CG à noite) |
| **total** | **161/251** | **216/251** |

Bloco: igual nos 8 antes e depois (os 10 votos liberados não mudaram nenhum bloco). Unidade: não remedida no produto hoje.

### 2b. Fase 1 remedida e fechada (11/09, tarde)
Precisão do confiante da subunidade **174/192 = 90,6%** (08/09: 64,6%), erros confiantes 64 → 18, fila 22,4/100. Limiar de
confiança NÃO generaliza por curso (leave-one-course-out: o ganho é quase todo CG); abstenção por piso perde sempre; a causa dos falsos
positivos era rótulo meta recebendo doação ("1.2 Conceitos" do CG com `OpenGL`), corrigida: `META_LABELS` += conceitos, áreas relacionadas
(CG 55 → 57, 0 perdas). Segunda opinião do astra em `c1-3/resposta_codex_astra_fase1.clean.md`. Detalhe: `pendencias.md`, seção da Fase 1.

### De onde vem o 214 (medido em cópias, rota do produto, 0 chamadas; `c1-3/mede_contribuicao_llm.py`)
| regime | subunidade /251 |
|---|---|
| produto | 214 |
| sem vocabulário LLM | 138 |
| sem vocabulário LLM e sem voter | 137 |

Determinístico de ponta a ponta **137 = 64% do 214**; vocabulário compilado por LLM **76 = 36%** (1 chamada por unidade, em cache: a
atribuição em si não chama nada); voter **1 = 0,5%**. Sem o vocabulário LLM o IA cai de 36 para 5 e o FR de 18 para 7.

### Régua de decisão da camada 3 (motor puro em cópias, subunidade em 151 = MF+SO+IA+ES2+TCC, 0 chamadas)
| regime | com-extras | primário |
|---|---|---|
| Gemini (resumos do conteúdo colidido) | 137 | 115 |
| determ v3 | 138 | 121 |
| **determ v3 + zips corrigidos** | **142** | 121 |

Material a material, determ ganha 6 que o Gemini erra e perde 1 (IA `mlp-xoripynb`). Baseline de 06/09 (87/93) **não é comparável**: régua diferente.

---

## 3. Achados que o próximo trabalho precisa saber

1. **Zip sem resumo é zip sem texto** (`resolver_apply.py:439`): o único texto que chega à unidade e à subunidade é o resumo em
   `code_curation.json`. "Sem resumos" nunca foi um regime válido para decidir a camada 3; o regime é "produtor determinístico".
2. **Colisão de zip tinha três causas**, todas corrigidas em `process_zip` (id do membro = zip + caminho relativo + extensão):
   entre zips (129 arquivos com conteúdo de outro zip em 23/44), dentro do zip (`src/main.py` × `tests/main.py`) e fonte ×
   cabeçalho (`Bezier.cpp` × `Bezier.h`, 150 de 273 membros do CG). O determ só foi a 142 depois da correção (MF 51 → 55).
3. **Vocabulário**: rótulo meta "Estudo de casos" (×5 no SO) recebia `Linux`, `Unix`, `Pthreads` e puxava 7 exemplos; o veto
   "termo igual a nome de arquivo" derrubava `Rede Perceptron`, `MLP`, `Kubernetes`. Generalizar "rótulo repetido" PERDE
   (`conceitos básicos` ×2 é alvo real). Somas iguais escondem conjuntos diferentes: os 8/15 do SO eram outros 7 erros.
4. **CG perdeu 3 no rollout, todos zips, causa lida**: `transformacoesgeometricas` tem `.md` próprio e a regra "sem resumo
   quando há `.md` próprio" nunca foi medida para zip; `bezier-python` porque nenhum alias do CG contém "bezier" (o label
   do tópico não entra em `course_aliases`) e o código diz `desenhaBezier`, que a regra de identificador só pega no início;
   `opengl3dcpp-vdi` porque a frase literal `PROJEÇÃO PARALELA` puxa para `paralela`.
5. **`_bundle` corta cada heading em 60 chars**; os membros do zip entram pelo nome-base (42 dos 44 zips entravam vazios).
6. **Voter** faz cache por md5 do arquivo; 10 materiais nunca tiveram voto (6 páginas Moodle do CG, 3 FR, 1 prova IA).

---

## 4. NÃO FAZER — refutado por medição em 11/09

| alavanca | resultado |
|---|---|
| Rótulo meta = todo rótulo que se repete no curso | SO 8 → 14 no determ mas 8 → 10 em sem/com; perde `1903-estruturas` e `3103-threads` (`replay_exp_regras.log`) |
| Léxico meta com "Conceitos", "Áreas relacionadas", "Introdução" | existem no CG e não foram medidos no holdout: fora até medir |
| "Sem resumos" como regime para decidir a camada 3 | mede zip sem texto, não o corte |
| Comparar a régua de 151 com os 87/93 de 06/09 | gold do MF entrou depois; incomparável |
| Refutar regressão pela soma | conjuntos diferentes com o mesmo total (SO) |

Os itens do §4 do handoff de 08/09 continuam valendo.

---

## 5. O que ENTROU (commits do gerador)

| commit | conteúdo |
|---|---|
| `cd54f64` | 2.4 com membros do zip no bundle; rótulo meta ("estudo de casos"); veto de título removido; refiltro dos 5 `.llm.json` |
| `75aa4eb` | id do membro leva o id do zip |
| `f637a11` | camada 3 cortada: `synthesize_all_code_entries` em todo build/reprocess; resumo Gemini de código fora do build; kill switch `TUTOR_NO_CODE_SYNTH` |
| `b6512fc` | id do membro = zip + caminho + extensão; rollout nos 8; goldens SO e TCC |

Tutores: 8 commits "chore(motor): vocab LLM compilado, zips sem colisao, resumo de codigo deterministico", árvores limpas.

## 5b. DECISÕES TOMADAS pelo user em 11/09 — não reabrir
- Cortar a camada 3: produtor determinístico `determ v3`; o botão manual de resumo por Gemini na UI fica.
- Regra de corte: `determ ≥ com − 2` na mesma régua (passou: 142 ≥ 135), com o critério do astra como ressalva (1 perda individual).
- Liberar 16 chamadas de compilação (2.4 com b) e 10 votos do voter.
- Merge em main: **não agora** (a branch está no remoto até `99cc514`; main tem 4 commits de junho fora dela).
- Codex `gpt-6-astra` como segunda opinião, read-only, só a pedido.

## 6. Decisões ABERTAS do user
| item | o que trava |
|---|---|
| Alavancas do CG (labels no conjunto de aliases · alias igual a parte CamelCase · zip com `.md` próprio também sintetiza) | medir no replay (5 cursos) + CG antes de tocar produto |
| Refiltrar `.llm.json` de CG, LR e FR com a regra nova | CG não medido no holdout |
| Gold de unidade do CG (93 materiais) e fila do CG regerada | trabalho humano |
| Posição da C7 (imagens): 1 material medido | ordenação |
| Merge em main | fronteira |

---

## 7. FILA DE CAMPANHAS
**C1 TRAVESSIA**: 2.2 (rótulo meta aplicado; corte por núcleo em outra unidade medido à noite, 212 → 206/251, descartado) e 2.4 fechadas; Fase 1 fechada no gate; 2.1 medido de novo no produto (+1 real, não vira código) e 2.3 medido
(bloco acerta 20/22 conflitos com gold; regra mantida): fechados sem código. Sobra a Fase 3; 3.2 em curso: 3.2 FECHADO: gold de unidade do CG em `docs/reports/material_gt_CG.csv` (93 materiais pela seção do Moodle e plano de ensino, revisado pelo astra, aprovado pelo user 11/09 à noite; produto acerta 84/93; 9 erros = 5 OpenGL u02 × u01, 3 texturas × u08, 1 exemplo × u03). 1.4 virou gold de subunidade dos 5 OpenGL: CG 57 → 55/82, 216 → 214/251 por mudança de gold. `_load_truth` cai para `material_gt` quando não há gold por bloco (11/09 noite, teste + 8 linhas): CG na régua de unidade, 79/88; conflitos com gold 22 → 36, bloco certo 32/36, regra mantida e astra revisou a Fase 2 (veredito, 3 correções e abstenção refutada de novo em `pendencias.md`). **Próxima decidida: C5 dívidas de dados** —
os zips fecharam hoje; falta o gold de unidade do CG e a fila do CG. Estacionadas: C7, C2, C4, C6. **DEFEITO CORRIGIDO 12/09 (veto no sidecar manual + curadoria SO/CG; unidade igual a 07/09 em SO e CG; subunidade 214 → 219/251; ver `pendencias.md`). **Ataque à subunidade 12/09: 9 alavancas medidas, 2 aplicadas (curvas CG, gateway ES2): 219 → 224/251, precisão do confiante 92,2%, 15 erros confiantes; o resto é gold (u04), insumo (C5) ou sinal que a taxonomia não tem.** Era: regressão de UNIDADE entre 07/09 e 11/09, SO 4 (vocab LLM doou 'Comunicação entre Processos' a 3.1 Conceitos básicos u02; bloco-09 virou u03 → u02) e CG 5 (card 2 OpenGL u01 → u02, provável M1); o gate da Fase 1 'sem regressão em unidade' não está cumprido. Astra: C1 = Fase 1 + 2 pelo plano §4; 3.x é C5. Ver `pendencias.md`.**

## 8. Leis (reafirmadas + uma nova)
- Gold só mede, nunca decide. SARC e Moodle acima do gold. Dado antes de código, pela rota real.
- **Medir conjuntos, não somas**: dois regimes com o mesmo total podem errar materiais diferentes.
- Ao publicar subunidade, dizer a base (251 no produto; 151 na régua de cópias) e o regime.
- Nada é pushed sem ordem explícita. Tokens nunca impressos. `.claude/settings.local.json` nunca em stage.

## 9. Ferramentas de 11/09 (`docs/reports/_harness-2026-09-04/c1-3/`, logs versionados)
`compila_vocab_um_curso.py <SIGLA> [--chamar|--refiltrar]` · `mede_opcao_b_zips.py` · `mede_zips_conteudo_perdido.py` ·
`replay_subunidade.py [experimentos]` (replay em memória, 17 s, reproduz os 3 regimes) · `replay_exp_regras.py`, `replay_exp_regras2.py` ·
`shim_codigo.py {sem|determ|com} puro` (env `VOCAB_ANTIGO`, `REIMPORTA_ZIPS`) · `rollout_camada3.py` (re-importa zips, apaga órfãos,
reprocessa com detector de chamadas) · `libera_votos.py` · brief e resposta do astra (`brief_codex_astra_camada3.md`,
`resposta_codex_astra_camada3{,.clean}.md`).

## 10. Artefatos publicados
Não atualizados em 11/09. O Placar do Motor e a Matriz de Atribuição ainda mostram o estado de 08/09 (subunidade 161/251).
