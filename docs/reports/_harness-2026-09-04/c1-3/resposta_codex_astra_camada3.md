01:06:58
OpenAI Codex v0.154.0
--------
[1mworkdir:[0m C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[1mmodel:[0m gpt-6-astra
[1mprovider:[0m openai
[1mapproval:[0m never
[1msandbox:[0m read-only
[1mreasoning effort:[0m high
[1mreasoning summaries:[0m none
[1msession id:[0m 01a08ea5-b1db-74e3-9bee-642b8e217a61
--------
[36muser[0m
# Brief para segunda opinião (Codex, perfil astra, read-only) — camada 3 do motor de atribuição, 2026-09-11

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator (gerador). Tutores gerados ficam ao lado, em
C:/Users/Humberto/Documents/GitHub/<Nome>-Tutor. Você está em sandbox read-only: não edite, não rode nada que chame
Gemini, não proponha commit. Responda em português, no máximo 1 página mais tabelas, cada achado com evidência
(arquivo:linha ou log:linha) e marcado como MEDIDO ou HIPÓTESE.
Abreviação usada abaixo: `c1-3/` = `docs/reports/_harness-2026-09-04/c1-3/`.

## 1. O problema

O motor atribui cada material de um curso a bloco (semana), unidade e subunidade. Três camadas usam LLM: (1) voter de
bloco, (2) vocabulário compilado por LLM (1 chamada por unidade, `src/builder/core/vocabulary_compile.py`), (3) resumos
de código por Gemini (`src/builder/core/code_summarization.py`, 1 por arquivo/zip, gravados em `code_curation.json`).
O usuário quer no máximo duas camadas. A candidata a cortar é a 3, trocando o produtor de `code_curation.json` pelo
substituto determinístico v2 (sintetizado dos `.md` que o motor já gera para cada membro do zip).

Fato estrutural (MEDIDO, `src/builder/routing/resolver_apply.py:439-450`): material zip ou código não tem `.md`
próprio; o único texto que chega à decisão de unidade e subunidade é o resumo em `code_curation.json`. Sem resumo
nenhum, o zip entra vazio.

## 2. O que foi feito hoje (11/09)

1. `vocabulary_compile._bundle` passou a incluir os nomes-base dos membros do zip no bundle da compilação (antes o zip
   contribuía vazio). Diff: `git diff src/builder/core/vocabulary_compile.py`. Teste:
   `tests/test_vocabulary_compile.py::test_bundle_zip_leva_nomes_base_dos_membros`.
2. Compilação do vocabulário LLM nos 4 cursos que estavam bloqueados por sidecar manual: SO 6, IA 4, ES2 2, TCC 4
   chamadas (gemini-3.5-flash). Script e logs: `docs/reports/_harness-2026-09-04/c1-3/compila_vocab_um_curso.py`,
   `compila_vocab_{SO,IA,ES2,TCC}.log`. Arquivos gravados: `<Tutor>/course/.glossary_curation.llm.json`.
   Achado (MEDIDO, IA): o LLM propôs `Rede Perceptron` e `MLP` para "Modelos Preditivos" e `filter_terms`
   (`vocabulary_compile.py`, regra `tn in file_names`) derrubou os dois porque coincidem com títulos de materiais.
3. Medições em cópias (`.ablacao/`), tripwire de Gemini, 0 chamadas, regime "motor puro" (sem curadoria manual, sem
   voter, com vocabulário LLM; `scripts/motor_puro.py`, `scripts/ablacao_rapida.py`,
   `docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py`). Régua: `docs/reports/subunit_gt_<SIGLA>.csv`, linhas
   `scorable=yes`, 151 materiais em MF, SO, IA, ES2, TCC. Acerto "com-extras" = predição no gold ou nos extras aceitos;
   "primário" = igual ao gold.

## 3. Resultados (MEDIDO), subunidade, vocabulário NOVO nos 4 cursos

| curso | sem resumos | determ v2 | com resumos (Gemini) | n |
|---|---|---|---|---|
| MF | 52 | 50 | 51 | 58 |
| SO | 8 | 8 | 8 | 15 |
| IA | 36 | 36 | 38 | 39 |
| ES2 | 16 | 20 | 21 | 28 |
| TCC | 10 | 10 | 10 | 11 |
| total | 122 | 124 | 128 | 151 |
| primário | 103 | 105 | 105 | |

Bloco 185/199 e unidade 180/190 idênticos nos três regimes. Logs: `c1-3/codigo_sem_puro_b.log`,
`c1-3/codigo_sem_puro_b2.log` (repetição, mesmo 122), `c1-3/codigo_determ2_puro_b.log`, `c1-3/codigo_com_puro_b.log`.
Referência de 06/09 na régua antiga de 93 (não comparável): com 87, determ 78, sem 71 (`c1-3/b_prop_puro.log`,
`c1-3/codigo_determ2_puro.log`, `c1-3/codigo_sem_puro.log`).

Regra de decisão combinada com o usuário, traduzida: cortar a camada 3 se `determ >= com - 2`. Deu 124 contra 128.

Errados no estado DETERM: `c1-3/errados_determ_vocabnovo.txt`. Errados no estado SEM (id -> predito | gold):

```
MF   archive-of-formal-proofs-355fb8 -> abordagens-para-verificacao-formal | provadores-de-teoremas
MF   exemplos -> exemplos-de-aplicacoes | provadores-de-teoremas
MF   exercicios-conjuntos -> logica-de-hoare | softwares-de-suporte-a-verificacao
MF   introducao-zip -> (vazio) | softwares-de-suporte-a-verificacao
MF   tiposindutivos -> (vazio) | softwares-de-suporte-a-verificacao
MF   exemplos-zip -> (vazio) | softwares-de-suporte-a-verificacao
SO   exemplo-criacao-de-processos-no-unix-linux-{filho,teste x3} -> estudo-de-casos | chamadas-de-sistema
SO   exemplo-threads-em-c-exemplo{1,2,3} -> estudo-de-casos | conceitos-basicos
IA   rede-perceptron-or-em-python -> introducao-ao-aprendizado-de-maquina | modelos-preditivos
IA   mlp-xoripynb -> (vazio) | modelos-preditivos
IA   aula-sobre-agrupamento-parte-2-hierarquico -> introducao-ao-aprendizado-de-maquina | modelos-descritivos
ES2  roteiro1, roteiro2, roteiro3 -> (vazio) | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  roteiro3-gateway -> cliente-servidor | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  microsservicos2 -> orientada-a-microsservicos | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  microsservicos3 -> estilos-e-padroes-arquiteturais | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  kubernetes -> estudo-de-caso-integracao-e-implantacao | plataformas-de-devops
ES2  roteiro4, roteiro5, roteiro6, roteiro7, roteiro7-history-service -> gerenciamento-da-configuracao | estudo-de-caso-integracao-e-implantacao
TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia -> linguagens-reconheciveis-e-decidiveis | (vazio)
```

## 4. Regime "com resumos, vocabulário ANTIGO" (MEDIDO), mesma régua de 151, `c1-3/codigo_com_puro_vocabantigo.log`

Nesta régua "puro", `ablate` apaga o sidecar manual; logo "vocabulário antigo" para SO, IA, ES2 e TCC significa
NENHUM vocabulário (nem o sidecar do professor), que é exatamente o estado da baseline de 06/09.

| curso | com resumos, vocab antigo | com resumos, vocab novo | delta |
|---|---|---|---|
| MF | 51/58 | 51/58 | 0 |
| SO | 8/15 | 8/15 | 0 |
| IA | 4/39 | 38/39 | +34 |
| ES2 | 5/28 | 21/28 | +16 |
| TCC | 8/11 | 10/11 | +2 |
| total | 76/151 (primário 56) | 128/151 (primário 105) | +52 |

Leitura: nenhum curso regrediu com o vocabulário novo. Os 7 erros do SO existem nos dois regimes, então a hipótese da
pergunta 1(b) está REFUTADA por esta medição: o vocabulário novo não os causou; a pergunta que fica é por que o SO erra
esses 7 em qualquer regime. A lista de errados deste regime está no fim do log.

## 5. Outros fatos medidos hoje que pesam

- Colisão de nomes na extração de zip (`src/builder/core/source_importers.py`, `process_zip`, `safe_name_c` usa só o
  nome-base do membro): 129 arquivos de código mostram o conteúdo de OUTRO zip, em 23 dos 44 zips (CG 88 em 11 zips,
  MF 35 em 8, ES2 6 em 4). Script e log: `c1-3/mede_zips_conteudo_perdido.{py,log}`. Ainda não corrigido: decisão do
  usuário é corrigir depois da decisão sobre a camada 3, porque o reprocesso re-resume zips se a camada 3 ficar.
- 42 dos 44 zips entravam vazios na compilação do vocabulário antes da mudança 1 (`c1-3/mede_opcao_b_zips.{py,log}`).
- `_bundle` corta cada heading em 60 caracteres (`vocabulary_compile.py`, função `_bundle`).
- Os tutores SO, IA, ES2, TCC ainda NÃO foram reprocessados com o vocabulário novo; só as cópias de medição foram.

## 6. O que NÃO repropor (refutado por medição, `docs/reports/2026-09-08-handoff-confianca.md` §4)

Agrupar por palavras-chave no lugar do scorer; título do vídeo no lugar do hash; piso de score; título com vocabulário
completo; página-índice pelo cabeçalho; triagem da chamada de LLM por sinal determinístico (o sinal não prediz);
"prova é fronteira de unidade"; alias ambíguo como alavanca; automatizar o gold a partir de Moodle e SARC; regra
pai × filho; piso de força na 1ª passada; seção → unidade dona; zero-pad; número na chave.

## 7. Perguntas, em ordem

1. Regressões. (a) MF: sem 52 > com 51 > determ 50. (b) SO 8/15, os 7 errados todos preditos como `estudo-de-casos`;
   HIPÓTESE minha: o vocabulário novo do SO pôs `Pthreads`, `pthread_create`, `Linux`, `Unix` em "3.4 Estudo de
   casos" e "1.3 Estudo de casos" (ver `compila_vocab_SO.log`), puxando os exemplos para lá. O §4 já refuta a hipótese
   para o SO; explique então por que os 7 do SO e o 1 do MF erram, pelos arquivos, e como medir com 0 chamadas.
2. Onde melhorar: no máximo 5 alavancas, ordenadas por ganho esperado na régua de 151, cada uma com arquivo:função,
   custo em chamadas e o experimento de 0 chamadas que a confirma ou mata antes de tocar produto.
3. A regra `determ >= com - 2` é sã para decidir cortar a camada 3? Se não, qual usar, com número.
4. Falhas no desenho da medição: régua 151 contra a antiga 93, `ablate` apagando o sidecar manual, produto não
   reprocessado, `sem` como regime. O que invalidaria uma conclusão tirada daqui.
5. Os 8 roteiros do ES2: o determ recupera 4 dos 5 que o Gemini recupera. O que falta ao determinístico, no texto que
   ele produz (`shim_codigo.py`, função `_sintetico`), para pegar o resto sem LLM.

Arquivos para ler primeiro: `docs/reports/2026-09-08-handoff-confianca.md`,
`docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` (§1, §2.2, §2.4), `docs/reports/pendencias.md` (seção
"NO MAXIMO DUAS CAMADAS LLM", 06/09), e os scripts e logs citados acima.

[1mhook:[0m [2mSessionStart[0m
[1mhook:[0m [2mSessionStart[0m
[1mhook:[0m [2mSessionStart[0m Completed
[1mhook:[0m [2mSessionStart[0m Completed
[1mhook:[0m [2mUserPromptSubmit[0m
[1mhook:[0m [2mUserPromptSubmit[0m
[1mhook:[0m [2mUserPromptSubmit[0m Completed
[1mhook:[0m [2mUserPromptSubmit[0m Completed
[35m[3mcodex[0m[0m
Vou conferir logs, textos e scorer para separar causa reproduzida de hipótese, sem escrita nem chamadas Gemini. Usarei as skills `using-superpowers`, `troglodita` e `graphify` na leitura.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'Get-Content C:/Users/Humberto/.agents/skills/using-superpowers/SKILL.md; Get-Content C:/Users/Humberto/.codex/skills/troglodita/SKILL.md; Get-Content C:/Users/Humberto/.codex/skills/graphify/SKILL.md; Get-Content .mex/AGENTS.md; Get-Content .mex/ROUTER.md'[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 421ms:[0m
---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → superpowers:brainstorming first, then implementation skills.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
---
name: troglodita
description: >
  Modo de comunicação ultra-comprimido para PT-BR. Corta uso de tokens ~70% mantendo
  precisão técnica total. Diagnósticos em telegrafia, ações no imperativo.
  Níveis: leve, total (padrão), máximo.
  Ativa quando user diz "modo troglodita", "fala curta", "menos tokens",
  "seja breve", ou invoca /troglodita.
---

Responder compacto. Substância técnica intacta. Só enrolação morre.

# PERSISTÊNCIA

ATIVO TODA RESPOSTA. Sem reverter após muitos turnos. Sem drift pra verbose.
Ainda ativo se incerto. Desliga só com: "parar troglodita" / "modo normal".

# REGRAS DE COMPRESSÃO PT-BR

## Remover
- Muletas: "basicamente", "na verdade", "essencialmente", "simplesmente", "vale ressaltar"
- Amenidades: "claro!", "com certeza", "fico feliz em ajudar", "seria um prazer"
- Hesitações: "talvez valha a pena", "seria interessante considerar", "pode ser que"
- Verbos de ligação desnecessários: "está sendo", "foi feito", "tem que ser"
- Redundâncias: "subir pra cima", "voltar atrás", "a razão é porque"
- Pronomes de tratamento: "você", "o senhor" — contexto implícito

## Manter
- Artigos onde a remoção quebra compreensão (PT-BR precisa de artigos mais que EN)
- Termos técnicos exatos: nomes de função, flags, paths, comandos
- Preposições estruturais: "de", "em", "por", "com" quando removê-las gera ambiguidade
- Gênero/número quando a concordância é necessária pra clareza

## Padrão de frase
- Diagnóstico: `[coisa]: [causa] ([contexto]). [consequência].`
- Ação: `[Verbo infinitivo/imperativo] [o quê] [como].`
- Exemplo normal: "O problema é que o componente está re-renderizando porque uma nova referência de objeto está sendo criada em cada ciclo de renderização."
- Exemplo troglodita: "Re-render: ref nova cada ciclo (objeto inline recriado). Resolver com `useMemo`."

## Setas e operadores
- `→` para causa/efeito: "prop inline → ref nova → re-render"
- `=` para equivalência: "array vazio = sem dependência"
- `+` para adição: "guard clause + early return"
- `>` para preferência: "useMemo > useCallback aqui"

# NÍVEIS

## leve
Sem muletas/hesitações. Frases completas. Artigos mantidos. Tom profissional direto.
"O componente re-renderiza por causa da referência nova. Usar `useMemo` para resolver."

## total (padrão)
Telegrafia + imperativo. Fragmentos OK. Compressão agressiva de verbos.
"Re-render: ref nova cada ciclo. Usar `useMemo`."

## máximo
Abreviações permitidas. Sem conjunções. Setas pra causalidade. Mínimo absoluto.
"ref nova → re-render. `useMemo`."

# AUTO-CLAREZA

Voltar pra prosa normal temporariamente quando:
- Avisos de segurança (dados sensíveis, credenciais, vulnerabilidades)
- Ações irreversíveis (drop table, force push, rm -rf)
- Ambiguidade em multi-step que pode causar erro
- Usuário demonstra confusão

Retomar compressão após o trecho crítico.

# LIMITES

- Código: escrito normalmente (nunca comprimir syntax)
- Commits: formato convencional normal (usar /troglodita-commit pra commits compactos)
- PRs: descrição normal a menos que pedido contrário
- "parar troglodita" / "modo normal": desativa imediatamente
---
name: graphify
description: "Use for any question about a codebase, its architecture, file relationships, or project content — especially when graphify-out/ exists, where the question should be treated as a graphify query first. Turns any input (code, docs, papers, images, videos) into a persistent knowledge graph with god nodes, community detection, and query/path/explain tools."
---

# /graphify

Turn any folder of files into a navigable knowledge graph with community detection, an honest audit trail, and three outputs: interactive HTML, GraphRAG-ready JSON, and a plain-language GRAPH_REPORT.md.

## Usage

```
/graphify                                             # full pipeline on current directory (HTML viz; add --obsidian for a vault)
/graphify <path>                                      # full pipeline on specific path
/graphify https://github.com/<owner>/<repo>           # clone repo then run full pipeline on it
/graphify https://github.com/<owner>/<repo> --branch <branch>  # clone a specific branch
/graphify <url1> <url2> ...                           # clone multiple repos, build each, merge into one cross-repo graph
/graphify <path> --mode deep                          # thorough extraction, richer INFERRED edges
/graphify <path> --update                             # incremental - re-extract only new/changed files
/graphify <path> --directed                            # build directed graph (preserves edge direction: source→target)
/graphify <path> --whisper-model medium                # use a larger Whisper model for better transcription accuracy
/graphify <path> --cluster-only                       # rerun clustering on existing graph
/graphify <path> --no-viz                             # skip visualization, just report + JSON
/graphify <path> --html                               # (HTML is generated by default - this flag is a no-op)
/graphify <path> --svg                                # also export graph.svg (embeds in Notion, GitHub)
/graphify <path> --graphml                            # export graph.graphml (Gephi, yEd)
/graphify <path> --neo4j                              # generate graphify-out/cypher.txt for Neo4j
/graphify <path> --neo4j-push bolt://localhost:7687   # push directly to Neo4j
/graphify <path> --falkordb                           # generate graphify-out/cypher.txt for FalkorDB
/graphify <path> --falkordb-push falkordb://localhost:6379   # push directly to FalkorDB
/graphify <path> --mcp                                # start MCP stdio server for agent access
/graphify <path> --watch                              # watch folder, auto-rebuild on code changes (no LLM needed)
/graphify <path> --wiki                               # build agent-crawlable wiki (index.md + one article per community)
/graphify <path> --obsidian --obsidian-dir ~/vaults/my-project  # write vault to custom path (e.g. existing vault)
/graphify add <url>                                   # fetch URL, save to ./raw, update graph
/graphify add <url> --author "Name"                   # tag who wrote it
/graphify add <url> --contributor "Name"              # tag who added it to the corpus
/graphify query "<question>"                          # BFS traversal - broad context
/graphify query "<question>" --dfs                    # DFS - trace a specific path
/graphify query "<question>" --budget 1500            # cap answer at N tokens
/graphify path "AuthModule" "Database"                # shortest path between two concepts
/graphify explain "SwinTransformer"                   # plain-language explanation of a node
```

## What graphify is for

Drop any folder of code, docs, papers, images, or video into graphify and get a queryable knowledge graph. Persistent across sessions, honest audit trail (EXTRACTED/INFERRED/AMBIGUOUS), community detection surfaces cross-document connections you wouldn't think to ask about.

## What You Must Do When Invoked

If the user invoked `/graphify --help` or `/graphify -h` (with no other arguments), print the contents of the `## Usage` section above verbatim and stop. Do not run any commands, do not detect files, do not default the path to `.`. Just print the Usage block and return.

**Fast path — existing graph:** Before doing anything else, check whether `graphify-out/graph.json` exists. The expected location is `graphify-out/graph.json` relative to the **current working directory** (i.e. the project root where you are running commands). If it exists AND the user's request is a natural-language question about the codebase (e.g. "How does X work?", "What calls Y?", "Trace the data flow through Z") and NOT an explicit rebuild command (`--update`, `--cluster-only`, or a bare path/URL that implies fresh extraction): **skip Steps 1–5 entirely and jump straight to `## For /graphify query`.** Run `graphify query "<question>"` immediately. Do not run detect. Do not check corpus size. Do not ask the user to narrow. The graph is already built — use it.

If no path was given, use `.` (current directory). Do not ask the user for a path.

If the path argument starts with `https://github.com/` or `http://github.com/`, treat it as a GitHub URL - run Step 0 before anything else, then continue with the resolved local path.

Follow these steps in order. Do not skip steps.

### Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)

Only when the path is one or more `https://github.com/...` URLs, or several local subfolders to merge. See `references/github-and-merge.md` for the clone, cross-repo merge, and monorepo flow, then continue with the resolved local path. A plain local path skips this step.

### Step 1 - Ensure graphify is installed

```bash
# Detect the correct Python interpreter (handles uv tool, pipx, venv, system installs)
PYTHON=""
GRAPHIFY_BIN=$(which graphify 2>/dev/null)
# 1. uv tool installs — most reliable on modern Mac/Linux
if [ -z "$PYTHON" ] && command -v uv >/dev/null 2>&1; then
    _UV_PY=$(uv tool run --from graphifyy python -c "import sys; print(sys.executable)" 2>/dev/null)
    if [ -n "$_UV_PY" ]; then PYTHON="$_UV_PY"; fi
fi
# 2. Read shebang from graphify binary (pipx and direct pip installs)
if [ -z "$PYTHON" ] && [ -n "$GRAPHIFY_BIN" ]; then
    _SHEBANG=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
    case "$_SHEBANG" in
        *[!a-zA-Z0-9/_.@-]*) ;;
        *) "$_SHEBANG" -c "import graphify" 2>/dev/null && PYTHON="$_SHEBANG" ;;
    esac
fi
# 3. Fall back to python3
if [ -z "$PYTHON" ]; then PYTHON="python3"; fi
if ! "$PYTHON" -c "import graphify" 2>/dev/null; then
    if command -v uv >/dev/null 2>&1; then
        uv tool install --upgrade graphifyy -q 2>&1 | tail -3
        _UV_PY=$(uv tool run --from graphifyy python -c "import sys; print(sys.executable)" 2>/dev/null)
        if [ -n "$_UV_PY" ]; then PYTHON="$_UV_PY"; fi
    else
        "$PYTHON" -m pip install graphifyy -q 2>/dev/null \
          || "$PYTHON" -m pip install graphifyy -q --break-system-packages 2>&1 | tail -3
    fi
fi
# Write interpreter path for all subsequent steps (persists across invocations)
mkdir -p graphify-out
"$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w', encoding='utf-8').write(sys.executable)"
# Save scan root so `graphify update` (no args) knows where to look next time
echo "$(cd INPUT_PATH && pwd)" > graphify-out/.graphify_root
```

If the import succeeds, print nothing and move straight to Step 2.

**In every subsequent bash block, replace `python3` with `$(cat graphify-out/.graphify_python)` to use the correct interpreter.**

### Step 2 - Detect files

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('INPUT_PATH'))
# Write the sidecar from Python, not a shell redirect, so the same block renders
# on PowerShell hosts without console-encoding drift (#2528).
Path('graphify-out/.graphify_detect.json').write_text(json.dumps(result, ensure_ascii=False), encoding=\"utf-8\")
print(f'Detected {result[\"total_files\"]} files')
"
```

Replace INPUT_PATH with the actual path the user provided. Do NOT cat or print the JSON - read it silently and present a clean summary instead:

```
Corpus: X files · ~Y words
  code:     N files (.py .ts .go ...)
  docs:     N files (.md .txt ...)
  papers:   N files (.pdf ...)
  images:   N files
  video:    N files (.mp4 .mp3 ...)
```

Omit any category with 0 files from the summary.

Then act on it:
- If `total_files` is 0: stop with "No supported files found in [path]."
- If `skipped_sensitive` is non-empty: report the count and list the skipped file names, so a wrongly-flagged source or doc is visible and can be renamed or moved (#2106).
- If `total_words` > 2,000,000 OR `total_files` > 500: show the warning. Then compute the top 5 first-level subdirectories by file count:
  - Read `scan_root` from the detect JSON (always an absolute path to the resolved INPUT_PATH).
  - Concatenate all file lists across all types (`code`, `document`, `paper`, `image`, `video`).
  - Filter out any path that starts with `scan_root + "/graphify-out/"` to exclude converted sidecars.
  - For each file, strip the `scan_root` prefix and take the first path component. Files directly in `scan_root` with no subdirectory count as `(root)`.
  - If all files are in `(root)` with no subdirectories, do not ask to narrow — no subfolders exist. Instead suggest `--no-cluster` to skip the expensive clustering step and proceed.
  - Otherwise rank by count, show the top 5 with file counts, then ask which subfolder to run on. Wait for the user's answer before proceeding.
- Otherwise: proceed directly to Step 2.5 if video files were detected, or Step 3 if not.

### Step 2.5 - Video and audio (only if video files detected)

Skip this step entirely if `detect` returned zero `video` files. When the corpus has video or audio, see `references/transcribe.md` to transcribe them to text first, then treat the transcripts as doc files in Step 3.

### Step 3 - Extract entities and relationships

**Before starting:** note whether `--mode deep` was given. You must pass `DEEP_MODE=true` to every subagent in Step B2 if it was. Track this from the original invocation - do not lose it.

This step has two parts: **structural extraction** (deterministic, free) and **semantic extraction** (LLM, costs tokens).

> **graphify needs no API key. Never ask the user for one, and never block on one.** Code is extracted structurally (AST) with no LLM and no key at all — a code-only corpus (the common `/graphify .` on a repo) skips semantic extraction entirely, so it needs nothing here: go straight to Part A and skip Part B. Semantic extraction (only for docs, papers, and images) uses Gemini **only if** `GEMINI_API_KEY`/`GOOGLE_API_KEY` is already set; otherwise the host agent itself is the LLM. graphify does **not** read `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or any other provider key. If you catch yourself about to prompt for, wait on, or stop because of a missing API key, that is a misread of this skill — proceed without one.

**Before semantic extraction:** check whether `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set. If neither is set, print this one-liner to the user:
> Tip: set `GEMINI_API_KEY` or `GOOGLE_API_KEY` to use Gemini for semantic extraction (`pip install 'graphifyy[gemini]'`).

Print it once, then continue — do not wait for the user to supply a key. If `GEMINI_API_KEY` or `GOOGLE_API_KEY` IS set, use `graphify.llm.extract_corpus_parallel(files, backend="gemini")` for semantic extraction instead of dispatching subagents. The default Gemini model is `gemini-3-flash-preview`; set `GRAPHIFY_GEMINI_MODEL` or pass `--model` in headless CLI flows to override it.

> **No other API keys are read.** When `GEMINI_API_KEY`/`GOOGLE_API_KEY` are unset, semantic extraction falls to the host agent itself — the running session is the LLM. On a host that dispatches subagents (e.g. Claude Code), dispatch them as written in Part B. On a host that runs the CLI directly in a terminal and cannot dispatch subagents, do not stall: a code-only corpus has no semantic work, so write the empty semantic file (Part B "Fast path") and continue to Part C; for a corpus with docs/papers/images, either set a Gemini key or extract those inline yourself, but in no case prompt for `ANTHROPIC_API_KEY` — that prompt is a misread of this skill.

**Run Part A (AST) and Part B (semantic) in parallel. Dispatch all semantic subagents AND start AST extraction in the same message. Both can run simultaneously since they operate on different file types. Merge results in Part C as before.**

Note: Parallelizing AST + semantic saves 5-15s on large corpora. AST is deterministic and fast; start it while subagents are processing docs/papers.

#### Part A - Structural extraction for code files

For any code files detected, run AST extraction in parallel with Part B subagents:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.extract import collect_files, extract
from pathlib import Path
import json

code_files = []
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding=\"utf-8\"))
for f in detect.get('files', {}).get('code', []):
    code_files.extend(collect_files(Path(f)) if Path(f).is_dir() else [Path(f)])

if code_files:
    result = extract(code_files, cache_root=Path('INPUT_PATH'))
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding=\"utf-8\")
    print(f'AST: {len(result[\"nodes\"])} nodes, {len(result[\"edges\"])} edges')
else:
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}, ensure_ascii=False), encoding=\"utf-8\")
    print('No code files - skipping AST extraction')
"
```

#### Part B - Semantic extraction (parallel subagents)

**Fast path:** If detection found zero docs, papers, and images (code-only corpus), skip Part B entirely and go straight to Part C. AST handles code - there is nothing for semantic subagents to do. **First write an empty semantic file** so Part C's merge has its input (it reads `.graphify_semantic.json` unconditionally; without this a code-only run hits `FileNotFoundError`):

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps({'nodes':[],'edges':[],'hyperedges':[],'input_tokens':0,'output_tokens':0}), encoding='utf-8')
"
```

**MANDATORY: You MUST use the Agent tool here. Reading files yourself one-by-one is forbidden - it is 5-10x slower. If you do not use the Agent tool you are doing this wrong.**

Before dispatching subagents, print a timing estimate:
- Load `total_words` and file counts from `graphify-out/.graphify_detect.json`
- Estimate agents needed: `ceil(uncached_non_code_files / 22)` (chunk size is 20-25)
- Estimate time: ~45s per agent batch (they run in parallel, so total ≈ 45s × ceil(agents/parallel_limit))
- Print: "Semantic extraction: ~N files → X agents, estimated ~Ys"

**Step B0 - Check extraction cache first**

Before dispatching any subagents, check which files already have cached extraction results:

SPEC_PATH below is the **absolute** path of the `references/extraction-spec.md` that ships beside this SKILL.md — the same file Step B2 loads and hands to every subagent. It is the extraction prompt, so cache entries are attributed to it: when a graphify upgrade changes the prompt, entries produced by the old one are re-extracted instead of replayed, and unchanged prompts keep their entries (#1939). Substitute the real path in both Step B0 and Step B3 — pass the same one to each, and do not drop the argument.

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.cache import check_semantic_cache
from pathlib import Path

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding=\"utf-8\"))
# Only content files go to semantic extraction. Code is already covered structurally
# by the AST pass (Part A); flattening every category here makes subagents re-read
# every source file (#1392). Video is transcribed to a document in Step 2.5 first.
all_files = [f for cat in ('document', 'paper', 'image') for f in detect['files'].get(cat, [])]

cached_nodes, cached_edges, cached_hyperedges, uncached = check_semantic_cache(all_files, root='INPUT_PATH', prompt_file='SPEC_PATH')

# Always (re)write the cache file: write hits, else DELETE any leftover from a prior
# run so Part C never merges a stale .graphify_cached.json (#1392).
if cached_nodes or cached_edges or cached_hyperedges:
    Path('graphify-out/.graphify_cached.json').write_text(json.dumps({'nodes': cached_nodes, 'edges': cached_edges, 'hyperedges': cached_hyperedges}, ensure_ascii=False), encoding=\"utf-8\")
else:
    Path('graphify-out/.graphify_cached.json').unlink(missing_ok=True)
Path('graphify-out/.graphify_uncached.txt').write_text('\n'.join(uncached), encoding=\"utf-8\")
print(f'Cache: {len(all_files)-len(uncached)} files hit, {len(uncached)} files need extraction')
"
```

Only dispatch subagents for files listed in `graphify-out/.graphify_uncached.txt`. If all files are cached, skip to Part C directly.

**Step B1 - Split into chunks**

Load files from `graphify-out/.graphify_uncached.txt`. Split into chunks of 20-25 files each. Each image gets its own chunk (vision needs separate context). When splitting, group files from the same directory together so related artifacts land in the same chunk and cross-file relationships are more likely to be extracted.

**Step B2 - Dispatch ALL subagents in a single message (Codex)**

> **Codex platform:** Uses `spawn_agent` + `wait_agent` + `close_agent` instead of the Agent tool.
> Requires `multi_agent = true` under `[features]` in `~/.codex/config.toml`.
> If `spawn_agent` is unavailable, tell the user to add that config and restart Codex.

Call `spawn_agent` once per chunk — ALL in the same response so they run in parallel. Build the message by wrapping the extraction prompt in task-delegation framing:

```
spawn_agent(agent_type="worker", message="Your task is to perform the following. Follow the instructions below exactly.\n\n<agent-instructions>\n[extraction prompt, with FILE_LIST, CHUNK_NUM, TOTAL_CHUNKS, DEEP_MODE substituted]\n</agent-instructions>\n\nExecute this now. Output ONLY the structured JSON response.")
```

After all agents are dispatched, collect results sequentially in memory:
```
result = wait_agent(handle); close_agent(handle)   # repeat per handle
```

Parse each result as JSON. Accumulate nodes/edges/hyperedges across all results and write to `graphify-out/.graphify_semantic_new.json`. Codex collects in memory, so there are no per-chunk files on disk; the disk-based success checks in Step B3 do not apply — a chunk that returns invalid JSON is the failure signal instead.

Subagent prompt template:

See `references/extraction-spec.md` for the compact subagent prompt (rules, node-ID format, confidence rubric, hyperedge and vision rules, JSON schema). Load it only here, only when at least one chunk holds a doc, paper, or image; a pure-code corpus has skipped Part B and never reads it. Pass each agent that prompt verbatim with FILE_LIST, CHUNK_NUM, TOTAL_CHUNKS, and DEEP_MODE substituted, and have it return the JSON inline.

**Step B3 - Collect, cache, and merge**

Wait for all subagents. For each result:
- Check that `graphify-out/.graphify_chunk_NN.json` exists on disk — this is the success signal
- If the file exists and contains valid JSON with `nodes` and `edges`, include it and save to cache
- If the file is missing, the subagent was likely dispatched as read-only (Explore type) — print a warning: "chunk N missing from disk — subagent may have been read-only. Re-run with general-purpose agent." Do not silently skip.
- If a subagent failed or returned invalid JSON, print a warning and skip that chunk - do not abort

If more than half the chunks failed or are missing, stop and tell the user to re-run and ensure `subagent_type="general-purpose"` is used.

Merge all chunk files into `.graphify_semantic_new.json`. **After each Agent call completes, read the real token counts from the Agent tool result's `usage` field and write them back into the chunk JSON before merging** — the chunk JSON itself always has placeholder zeros. Then run:
```bash
$(cat graphify-out/.graphify_python) -c "
import json, glob
from pathlib import Path

chunks = sorted(glob.glob('graphify-out/.graphify_chunk_*.json'))
all_nodes, all_edges, all_hyperedges = [], [], []
total_in, total_out = 0, 0
for c in chunks:
    d = json.loads(Path(c).read_text(encoding=\"utf-8\"))
    all_nodes += d.get('nodes', [])
    all_edges += d.get('edges', [])
    all_hyperedges += d.get('hyperedges', [])
    total_in += d.get('input_tokens', 0)
    total_out += d.get('output_tokens', 0)
Path('graphify-out/.graphify_semantic_new.json').write_text(json.dumps({
    'nodes': all_nodes, 'edges': all_edges, 'hyperedges': all_hyperedges,
    'input_tokens': total_in, 'output_tokens': total_out,
}, indent=2, ensure_ascii=False), encoding=\"utf-8\")
print(f'Merged {len(chunks)} chunks: {total_in:,} in / {total_out:,} out tokens')
"
```

Save new results to cache. Pass the same SPEC_PATH as Step B0 — it stamps each entry with the prompt that produced it, and a write under a different prompt than the read lands where the next run won't look (#1939):
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.cache import save_semantic_cache
from pathlib import Path

new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text(encoding=\"utf-8\")) if Path('graphify-out/.graphify_semantic_new.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}
uncached = [line for line in Path('graphify-out/.graphify_uncached.txt').read_text(encoding=\"utf-8\").splitlines() if line]
saved = save_semantic_cache(new.get('nodes', []), new.get('edges', []), new.get('hyperedges', []), root='INPUT_PATH', allowed_source_files=uncached, prompt_file='SPEC_PATH')
print(f'Cached {saved} files')
"
```

Merge cached + new results into `graphify-out/.graphify_semantic.json`:
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path

cached = json.loads(Path('graphify-out/.graphify_cached.json').read_text(encoding=\"utf-8\")) if Path('graphify-out/.graphify_cached.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}
new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text(encoding=\"utf-8\")) if Path('graphify-out/.graphify_semantic_new.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}

all_nodes = cached['nodes'] + new.get('nodes', [])
all_edges = cached['edges'] + new.get('edges', [])
all_hyperedges = cached.get('hyperedges', []) + new.get('hyperedges', [])
seen = set()
deduped = []
for n in all_nodes:
    if n['id'] not in seen:
        seen.add(n['id'])
        deduped.append(n)

merged = {
    'nodes': deduped,
    'edges': all_edges,
    'hyperedges': all_hyperedges,
    'input_tokens': new.get('input_tokens', 0),
    'output_tokens': new.get('output_tokens', 0),
}
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding=\"utf-8\")
print(f'Extraction complete - {len(deduped)} nodes, {len(all_edges)} edges ({len(cached[\"nodes\"])} from cache, {len(new.get(\"nodes\",[]))} new)')
"
```
Clean up temp files: `rm -f graphify-out/.graphify_cached.json graphify-out/.graphify_uncached.txt graphify-out/.graphify_semantic_new.json`

#### Part C - Merge AST + semantic into final extraction

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from pathlib import Path

ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text(encoding=\"utf-8\"))
sem = json.loads(Path('graphify-out/.graphify_semantic.json').read_text(encoding=\"utf-8\"))

# Merge: AST nodes first, semantic nodes deduplicated by id
seen = {n['id'] for n in ast['nodes']}
merged_nodes = list(ast['nodes'])
for n in sem['nodes']:
    if n['id'] not in seen:
        merged_nodes.append(n)
        seen.add(n['id'])

merged_edges = ast['edges'] + sem['edges']
merged_hyperedges = sem.get('hyperedges', [])
merged = {
    'nodes': merged_nodes,
    'edges': merged_edges,
    'hyperedges': merged_hyperedges,
    'input_tokens': sem.get('input_tokens', 0),
    'output_tokens': sem.get('output_tokens', 0),
}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding=\"utf-8\")
total = len(merged_nodes)
edges = len(merged_edges)
print(f'Merged: {total} nodes, {edges} edges ({len(ast[\"nodes\"])} AST + {len(sem[\"nodes\"])} semantic)')
"
```

### Step 4 - Build graph, cluster, analyze, generate outputs

**Before starting:** the code blocks below pass `directed=IS_DIRECTED` to `build_from_json()`. Replace `IS_DIRECTED` with `True` if `--directed` was given (builds a `DiGraph` preserving edge direction source→target), otherwise `False` (the default undirected `Graph`). Substitute it the same way you substitute `INPUT_PATH` — do not leave the literal `IS_DIRECTED` in the code.

```bash
mkdir -p graphify-out
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding=\"utf-8\"))
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding=\"utf-8\"))

# root= mirrors the --update runbook (#1361): relativize source_file to the same
# base so the full build and incremental --update never drift apart on re-extract.
G = build_from_json(extraction, root='INPUT_PATH', directed=IS_DIRECTED)
# Guard BEFORE any write: an empty extraction must not clobber a good graph.json /
# GRAPH_REPORT.md / analysis sidecar. Check immediately after build (#1392).
if G.number_of_nodes() == 0:
    print('ERROR: Graph is empty - extraction produced no nodes.')
    print('Possible causes: all files were skipped, binary-only corpus, or extraction failed.')
    raise SystemExit(1)
communities = cluster(G)
cohesion = score_all(G, communities)
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: 'Community ' + str(cid) for cid in communities}
# Placeholder questions - regenerated with real labels in Step 5
questions = suggest_questions(G, communities, labels)

# Export FIRST and honor the #479 shrink-guard: to_json returns False (writing
# nothing) when the new graph is smaller than the existing graph.json. Only write
# GRAPH_REPORT.md + the analysis sidecar when the graph was actually written, so
# they never describe a graph that graph.json doesn't contain (#1392).
wrote = to_json(G, communities, 'graphify-out/graph.json')
if not wrote:
    print('ERROR: refused to shrink graphify-out/graph.json (existing graph has more nodes; #479).')
    print('If this shrink is intentional (you deleted files), re-run a full build with --force.')
    raise SystemExit(1)
report = generate(G, communities, cohesion, labels, gods, surprises, detection, tokens, 'INPUT_PATH', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding=\"utf-8\")
analysis = {
    'communities': {str(k): v for k, v in communities.items()},
    'cohesion': {str(k): v for k, v in cohesion.items()},
    'gods': gods,
    'surprises': surprises,
    'questions': questions,
}
Path('graphify-out/.graphify_analysis.json').write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding=\"utf-8\")
print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities')
"
```

If this step prints `ERROR: Graph is empty`, stop and tell the user what happened - do not proceed to labeling or visualization.

Replace INPUT_PATH with the actual path.

### Step 4.5 - Graph health check (read-only integrity gate)

A non-destructive diagnostic on the extraction, before labeling. It surfaces edge collapse, dangling/missing endpoints, and self-loops — the silent-corruption modes of incremental updates and AST/LLM id mismatches. Read-only; never aborts.

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
from graphify.diagnostics import diagnose_extraction, format_diagnostic_report

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding=\"utf-8\"))
summary = diagnose_extraction(extraction, directed=IS_DIRECTED, root='INPUT_PATH')
print(format_diagnostic_report(summary))
flags = [f'{summary[k]} {label}' for k, label in (
    ('dangling_endpoint_edges', 'dangling-endpoint edges'),
    ('missing_endpoint_edges', 'missing-endpoint edges'),
    ('self_loop_edges', 'self-loop edges'),
    ('directed_same_endpoint_collapsed_edges', 'collapsed (directed) edges'),
    ('undirected_same_endpoint_collapsed_edges', 'collapsed (undirected) edges'),
) if summary.get(k, 0)]
print('GRAPH HEALTH WARNING: ' + '; '.join(flags) + ' - graph may be incomplete/corrupt.' if flags else 'Graph health: OK (no dangling/missing/collapsed edges).')
"
```

Substitute `IS_DIRECTED` and `INPUT_PATH` as in Step 4. If a `GRAPH HEALTH WARNING` prints, surface it in the final summary (do not abort — the graph is still usable, but the integrity issue must be visible, per the Honesty Rules).

### Step 5 - Label communities

Read `graphify-out/.graphify_analysis.json`. For each community key, look at its node labels and write a 2-5 word plain-language name (e.g. "Attention Mechanism", "Training Pipeline", "Data Loading").

Then regenerate the report and save the labels for the visualizer:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding=\"utf-8\"))
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding=\"utf-8\"))
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text(encoding=\"utf-8\"))

# root= as in Step 4 / the --update runbook (#1361) — same base for node-key parity.
G = build_from_json(extraction, root='INPUT_PATH', directed=IS_DIRECTED)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis['cohesion'].items()}
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}

# LABELS - replace these with the names you chose above
labels = LABELS_DICT

# Regenerate questions with real community labels (labels affect question phrasing)
questions = suggest_questions(G, communities, labels)

report = generate(G, communities, cohesion, labels, analysis['gods'], analysis['surprises'], detection, tokens, 'INPUT_PATH', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding=\"utf-8\")
Path('graphify-out/.graphify_labels.json').write_text(json.dumps({str(k): v for k, v in labels.items()}, ensure_ascii=False), encoding=\"utf-8\")
# Re-export so graph.json nodes carry the curated community_name (#2490).
# Same extraction as Step 4, so the #479 shrink-guard passes on node count;
# if it still refuses, surface the guard message - do not force past it.
wrote = to_json(G, communities, 'graphify-out/graph.json', community_labels=labels)
if not wrote:
    print('ERROR: refused to shrink graphify-out/graph.json (existing graph has more nodes; #479).')
    print('If this shrink is intentional (you deleted files), re-run a full build with --force.')
print('Report updated with community labels')
"
```

Replace `LABELS_DICT` with the actual dict you constructed (e.g. `{0: "Attention Mechanism", 1: "Training Pipeline"}`).
Replace INPUT_PATH with the actual path.

### Step 6 - Generate Obsidian vault (opt-in) + HTML

**Generate HTML always** (unless `--no-viz`). **Obsidian vault only if `--obsidian` was explicitly given** — skip it otherwise, it generates one file per node.

If `--obsidian` was given:

- If `--obsidian-dir <path>` was also given, pass it via `--dir`. Otherwise defaults to `graphify-out/obsidian`.

```bash
graphify export obsidian
# or with custom dir: graphify export obsidian --dir ~/vaults/my-project
```

Generate the HTML graph (always, unless `--no-viz`):

```bash
graphify export html  # auto-aggregates to community view if graph > 5000 nodes
# or: graphify export html --no-viz
```

### Steps 6b-8 - Wiki, Neo4j, FalkorDB, SVG, GraphML, MCP, benchmark (only on their flags)

These run only when their flag is present (`--wiki`, `--neo4j`/`--neo4j-push`, `--falkordb`/`--falkordb-push`, `--svg`, `--graphml`, `--mcp`) or, for the token-reduction benchmark, when `total_words` exceeds 5,000. A default run with no export flags skips all of them. See `references/exports.md` for each one. Run any `--wiki` export before Step 9 cleanup so `.graphify_labels.json` is still available.

---

### Step 9 - Save manifest, update cost tracker, clean up, and report

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
from datetime import datetime, timezone
from graphify.detect import save_manifest

# Save manifest for --update
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding=\"utf-8\"))
extract = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding=\"utf-8\"))
# In --update mode, 'all_files' carries the full corpus; 'files' is the changed
# subset. Full-rebuild mode populates only 'files', so the fallback handles that.
# root= relativizes the manifest keys to the scan root (same base as the build),
# so the on-disk manifest is portable across clones/machines and a later --update
# matches cached files instead of missing every one (#1417).
#
# Only stamp semantic files (docs/papers/images) that ACTUALLY produced output:
# a detected file whose chunk failed or was omitted must stay unstamped so the
# next --update re-queues it, otherwise it is marked done and its content is lost
# forever (#2015). This mirrors the library extract path exactly
# (cli._stamped_manifest_files + clear_semantic + scan_corpus); do not stamp the
# raw corpus. Code files are always stamped (AST is deterministic); only semantic
# types are gated on output.
from graphify.cli import _stamped_manifest_files
_corpus = detect.get('all_files') or detect['files']
_manifest_files = _stamped_manifest_files(_corpus, extract, Path('INPUT_PATH'))
# Files dispatched this run (the changed subset) but NOT stamped above still carry
# a stale semantic_hash from a prior run; clear it so detect_incremental re-queues
# them instead of reading them as unchanged (#1948).
_sem_types = ('document', 'paper', 'image')
_dispatched = {f for t, fl in detect['files'].items() if t in _sem_types for f in fl}
_stamped = {f for fl in _manifest_files.values() for f in fl}
_cleared = _dispatched - _stamped
# scan_corpus = the RAW full corpus (not the stamp-filtered subset) so in-root
# files newly excluded since last run are dropped rather than masquerading as
# deletions; untouched files' prior rows are still preserved (#1908).
_scan = {f for fl in _corpus.values() for f in fl}
save_manifest(_manifest_files, root='INPUT_PATH', scan_corpus=_scan, clear_semantic=_cleared or None)

# Update cumulative cost tracker
input_tok = extract.get('input_tokens', 0)
output_tok = extract.get('output_tokens', 0)

cost_path = Path('graphify-out/cost.json')
if cost_path.exists():
    cost = json.loads(cost_path.read_text(encoding=\"utf-8\"))
else:
    cost = {'runs': [], 'total_input_tokens': 0, 'total_output_tokens': 0}

cost['runs'].append({
    'date': datetime.now(timezone.utc).isoformat(),
    'input_tokens': input_tok,
    'output_tokens': output_tok,
    'files': detect.get('total_files', 0),
})
cost['total_input_tokens'] += input_tok
cost['total_output_tokens'] += output_tok
cost_path.write_text(json.dumps(cost, indent=2, ensure_ascii=False), encoding=\"utf-8\")

print(f'This run: {input_tok:,} input tokens, {output_tok:,} output tokens')
print(f'All time: {cost[\"total_input_tokens\"]:,} input, {cost[\"total_output_tokens\"]:,} output ({len(cost[\"runs\"])} runs)')
"
rm -f graphify-out/.graphify_detect.json graphify-out/.graphify_extract.json graphify-out/.graphify_ast.json graphify-out/.graphify_semantic.json graphify-out/.graphify_analysis.json
find graphify-out -maxdepth 1 -name '.graphify_chunk_*.json' -delete 2>/dev/null
rm -f graphify-out/.needs_update 2>/dev/null || true
```

Replace INPUT_PATH with the actual path (same value used in Steps 4-5) so the manifest is relativized to the scan root.

Tell the user (omit the obsidian line unless --obsidian was given):
```
Graph complete. Outputs in PATH_TO_DIR/graphify-out/

  graph.html            - interactive graph, open in browser
  GRAPH_REPORT.md       - audit report
  graph.json            - raw graph data
  obsidian/             - Obsidian vault (only if --obsidian was given)
```

If graphify saved you time, consider supporting it: https://github.com/sponsors/safishamsi

Replace PATH_TO_DIR with the actual absolute path of the directory that was processed.

Then paste these sections from GRAPH_REPORT.md directly into the chat:
- God Nodes
- Surprising Connections
- Suggested Questions

Do NOT paste the full report - just those three sections. Keep it concise.

Then immediately offer to explore. Pick the single most interesting suggested question from the report - the one that crosses the most community boundaries or has the most surprising bridge node - and ask:

> "The most interesting question this graph can answer: **[question]**. Want me to trace it?"

If the user says yes, run `/graphify query "[question]"` on the graph and walk them through the answer using the graph structure - which nodes connect, which community boundaries get crossed, what the path reveals. Keep going as long as they want to explore. Each answer should end with a natural follow-up ("this connects to X - want to go deeper?") so the session feels like navigation, not a one-shot report.

The graph is the map. Your job after the pipeline is to be the guide.

---

## Interpreter guard for subcommands

Before running any subcommand below (`--update`, `--cluster-only`, `query`, `path`, `explain`, `add`), check that `.graphify_python` exists. If it's missing (e.g. user deleted `graphify-out/`), re-resolve the interpreter first:

```bash
if [ ! -f graphify-out/.graphify_python ]; then
    GRAPHIFY_BIN=$(which graphify 2>/dev/null)
    if [ -n "$GRAPHIFY_BIN" ]; then
        PYTHON=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
        case "$PYTHON" in *[!a-zA-Z0-9/_.@-]*) PYTHON="python3" ;; esac
    else
        PYTHON="python3"
    fi
    mkdir -p graphify-out
    "$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w', encoding='utf-8').write(sys.executable)"
fi
```

## For --update and --cluster-only

Both are non-default subcommands. `--update` re-extracts only new or changed files; `--cluster-only` reruns clustering on the existing graph. See `references/update.md` for both flows.

---

## For /graphify query

When `graphify-out/graph.json` already exists and the user asks a question about the corpus, answer from the graph rather than rebuilding it:

```bash
graphify query "<question>"
```

Before traversal, expand the question against the graph's own vocabulary so a wording mismatch does not collapse the answer to noise. If the `graphify query` CLI is unavailable, fall back to an inline NetworkX traversal of `graphify-out/graph.json`. Answer using only what the graph output contains, and quote `source_location` when citing a specific fact. For that vocab-expansion step, the BFS/DFS traversal modes, the `--budget` cap, the NetworkX fallback, `save-result` feedback, and the `/graphify path` and `/graphify explain` flows, see `references/query.md`.

---

## For /graphify add and --watch

Neither is part of the default build. When the user runs `/graphify add <url>` to fetch a URL into the corpus, or passes `--watch` to auto-rebuild on file changes, see `references/add-watch.md`.

---

## For the commit hook and native CLAUDE.md integration

When the user asks to install the post-commit auto-rebuild hook or wire graphify into a project's CLAUDE.md, see `references/hooks.md`.

---

## Honesty Rules

- Never invent an edge. If unsure, use AMBIGUOUS.
- Never skip the corpus check warning.
- Always show token cost in the report.
- Never hide cohesion scores behind symbols - show the raw number.
- Never run HTML viz on a graph with more than 5,000 nodes without warning the user.
---
name: agents
description: Project identity, non-negotiables, commands, and scaffold growth instructions
last_updated: 2026-09-03
---

# GPT-Tutor-Generator

Reviewed against `.mex/ROUTER.md` and current scaffold commands on 2026-06-21.

## What This Is

A desktop tool (Python/tkinter) that converts academic PDFs into structured GitHub repositories formatted as Claude Projects knowledge bases, acting as a persistent AI tutor per subject.

## Non-Negotiables

- Read existing files before writing. Do not re-read unless the file changed.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.
- New logic goes into the correct subpackage — never into `engine.py`. `engine.py` is a facade only.
- Imports must come from focused submodules, not from `engine.py`.
- No sycophantic openers, closing fluff, emojis, or em-dashes in output.
- No obvious comments; only non-obvious WHY comments.
- No multi-paragraph docstrings.
- Skip files over 100KB unless strictly required.
- Gemini integration uses `google-genai` (NOT `google-generativeai`). Imports via `from google import genai` and must stay lazy inside method bodies — never at module top level. Anti-patterns to grep: `google.generativeai`, `genai.GenerativeModel`.
- The generated repo's code_curation.json is a generated artifact (not source). Treat it like manifest cache: prune stale entries before reads, write atomically.
- **Arquivamento de concluídos (NÃO-NEGOCIÁVEL):** quando um plano termina de executar e passa 100%
  (gate verde — golden/eval/pytest verdes, sem drift), MOVER os arquivos Markdown concluídos (plano + spec + report associados)
  para a subpasta de concluídos do diretório de origem: `docs/superpowers/plans/Feitos/`,
  `docs/superpowers/specs/Feitos/`, `docs/reports/Feitos/`, `.git/sdd/Feitos/`. Usar `git mv` quando
  trackeado (preserva histórico). A RAIZ desses diretórios só contém trabalho em andamento ou a-fazer.
- **Tracker de pendências (NÃO-NEGOCIÁVEL):** manter `docs/reports/pendencias.md` SEMPRE
  atualizado: ao concluir um item, removê-lo da lista viva e registrá-lo na seção "Concluído"; ao
  descobrir nova pendência, adicioná-la com tag [USER|CODE|DECISION].
- **Fixtures copiam contrato real (NÃO-NEGOCIÁVEL, 2026-08-06):** dado sintético de teste
  reproduz o contrato REAL da fonte (nome/tipo/formato/encoding) com proveniência declarada.
  Regra completa: `context/conventions.md` §Fixtures; dicionário campo-a-campo:
  `context/institutional.md` §Contratos.
- **Fonte única de fatos (dieta MEX 2026-08-06):** estado vivo mora no tracker de pendências
  (nunca duplicar em ROUTER/context); estrutura de código mora no graphify (`graphify update .`
  após mudar código); MEX guarda só intenção, decisões, convenções e contratos externos.

## Commands

```powershell
# Run all tests
python -m pytest tests -q

# Run a specific test file
python -m pytest tests/test_datalab_image_extraction.py -q

# Run the app
python app.py
```

## Scaffold Growth

After every task:
- If no pattern exists for this task type, create one and add it to `.mex/patterns/INDEX.md`.
- If a pattern was deviated from or a new gotcha was found, update it.
- If any context file is now outdated, update it surgically.
- Estado vivo (números, gates, pendências) vai para `docs/reports/pendencias.md` — NÃO para o
  ROUTER (que só aponta fontes; dieta 2026-08-06). Se mudou código, rodar `graphify update .`.
- **Living overview:** if the architecture, pipeline, or attribution logic changed, update
  `docs/Overview-Sistema.html` — the single living visual overview of the system (tabs 1–5
  attribution, 6 audit/debts, 7 system report). It must always reflect the current state.

## Navigation

Read `.mex/ROUTER.md` before starting any task.
---
name: router
description: Session bootstrap. Read this before any task. Points to the single source of truth for each kind of fact.
last_updated: 2026-09-08
---

# ROUTER.md - Session Bootstrap

Read this file before starting any task.

---

## Current Project State

GPT-Tutor-Generator: app desktop Python/Tkinter que converte materiais acadêmicos (PDF,
links, código, imagens) em repositórios-tutor Markdown por matéria (Claude/GPT/Gemini),
com atribuição arquivo→bloco→unidade dirigida por sinais Moodle/SARC/plano de ensino.

**Este arquivo NÃO duplica estado.** Cada tipo de fato mora em UM lugar:

| Fato | Fonte única |
|---|---|
| Estado vivo, pendências, dívidas, números de gate | `docs/reports/pendencias.md` (tracker, sempre atualizado) |
| O que a última sessão fez e a fila decidida | **`docs/reports/2026-09-08-handoff-confianca.md`** (ponto de entrada vivo) |
| O plano a revisar antes de executar | `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` |
| Estrutura do código (quem chama quem, onde vive) | `graphify explain "<símbolo>"` ou `graphify path "A" "B"`; `query` aberto só com `--budget` |
| Segunda opinião de diff (Codex) ou leitura de corpus (agy) | `patterns/delegar-codex-agy.md` |
| Por que cada escolha existe | `context/decisions.md` |
| Contratos de dados reais (Moodle/SARC/manifest/índices) | `context/institutional.md` §Contratos |
| Como escrever/verificar código e fixtures | `context/conventions.md` |
| Saída gerada (formato do repo-tutor) | `context/repo-output.md` |
| Pipeline de PDF (backends, falhas conhecidas) | `context/pdf-pipeline.md` |
| Cadeia do TEXTO (staging → Curator Studio → o que o motor pontua; descrições de imagem) | `context/text-chain.md` |
| Retrato verificado do sistema (o que existe, o que está inerte, o que não existe, código morto) | `context/audit-2026-09-07.md` (inclui os achados de 08/09: circularidade do gold, calibração da confiança, cobertura da régua) |
| Serviço externo, custo, API paga, backend de extração, descrição de imagem | `context/external-services.md` |
| Histórico de arquitetura, roadmap e changelogs (retrato de 03/09, parcialmente vencido) | `docs/Overview-Sistema.html` |
| Inventário do motor de atribuição (quem decide cada eixo, o que já existe) | `docs/reports/_harness-2026-09-04/c1-3/inventario_motor_2026-09-07.md` |
| Setup/stack/manifest | `context/setup.md`, `context/stack.md` |

Estado atual (branch, números de suite, fases, rollouts, foco da campanha): SEMPRE no
tracker `docs/reports/pendencias.md` + handoff mais recente em `docs/reports/`. Este
arquivo não carrega snapshot — snapshot aqui envelhece e mente.

---

## Routing Table

| Task type | Load |
|---|---|
| Understanding how the system works | `graphify explain` (estrutura) + `context/decisions.md` (intenção) |
| Understanding the faculty/source platforms (Moodle, SARC, Plano de Ensino) | `context/institutional.md` |
| Writing tests or fixtures with third-party data | `context/institutional.md` §Contratos + `context/conventions.md` |
| Working with a specific technology or backend | `context/stack.md` |
| Writing or reviewing code | `context/conventions.md` |
| Making a design decision | `context/decisions.md` |
| Setting up or running the project | `context/setup.md` |
| Understanding the generated repo output format | `context/repo-output.md` |
| PDF processing, backends, conversion failures | `context/pdf-pipeline.md` |
| Curadoria de markdown, aprovação, staging, descrição de imagem | `context/text-chain.md` |
| "Isso já existe no sistema?" antes de construir/refatorar | `context/audit-2026-09-07.md` (retrato verificado) — só então `docs/Overview-Sistema.html` (histórico) |
| Custo, API paga, trocar backend (Marker/MinerU/docling), provedor de descrição | `context/external-services.md` |
| Mexer no motor de atribuição (bloco/unidade/subunidade) | `docs/reports/_harness-2026-09-04/c1-3/inventario_motor_2026-09-07.md` |
| Any specific repeatable task | Check `patterns/INDEX.md` |
| Sessão passada que não está no tracker nem no handoff | `mem-search` (quarta fonte, não a primeira) |

## Harness Ownership

Uma fase, um dono. Configurado no settings.json pessoal do Claude Code, via skillOverrides.
Este arquivo roteia; o settings.json é a fonte do que está ligado.

| Fase | Dono |
|---|---|
| Critérios de aceite antes de codar | `ecc:intent-driven-development` (substituiu `superpowers:brainstorming`) |
| Capacidade que ainda não existe | `ecc:orch-add-feature` |
| Estrutura melhora, comportamento não muda | `ecc:orch-refine-code` |
| Comportamento quebrado ou errado | `ecc:orch-fix-defect` (primeira jogada: teste de regressão vermelho) |
| Medição repetida em N cursos ou N tutores | `ecc:parallel-execution-optimizer` |
| Implementação TDD dentro dos `orch-*` | agent `ecc:tdd-guide` (dono único da fase 4) |
| Review | agent `ecc:python-reviewer` + `/code-review` nativo |
| Governança dos relatórios em `docs/reports/` | `ecc:living-docs-governance` |
| Contratos e fixtures | `ecc:contract-first` |

Os `orch-*` param em Gate 1 (plano aprovado antes de escrever código) e Gate 2
(diff confirmado antes do commit). Entre os dois o pipeline corre sem parar.
Os gates são instrução dentro do SKILL.md, não hook: nada no arquivo de hooks do ECC
os impõe. O risco é pular o gate, não travar nele.

Deriva de acurácia agregada não é defeito reproduzível e não vai por
`orch-fix-defect`. Vai por harness de medição (`ecc:eval-harness`).

MCP ativo no Claude Code: `context7` e, desde 10/09, `graphify` (`.mcp.json` do
projeto, gitignored; servidor `python -m graphify.serve graph.json`). `code-review-graph`
foi removido em 08/09 por uso zero medido em 15.840 chamadas de ferramenta registradas.
No agy o mesmo servidor entrou via `agy mcp add`. No Codex está `enabled = false` no
config.toml global do Codex (pasta ~/.codex): o Alethe reescreve a entrada do projeto com um comando
que não existe; a skill `$graphify-windows` cobre. Detalhes em
`patterns/debug-graphify-mcp.md`. Estrutura de código continua no `graphify`, conforme
a tabela de fonte única acima.

Busca estrutural, ordem medida em 08/09: `Grep` para localizar o símbolo, então
`graphify explain` ou `graphify path`, e `Read` com offset só no que sobrar.
`graphify explain` custou 379 tokens contra 58.838 de ler `src/ui/dialogs.py`
inteiro. `graphify query` aberto truncou em 64 de 607 nós e avisou que a resposta
podia estar entre os 543 cortados: é indício, não resultado. O grafo indexa
`docs/` junto com o código, então pergunta de código volta com ruído de relatório.
`claude-mem:smart-explore` fica desligada: o tree-sitter dela falha em Python e
JavaScript nesta instalação, com as gramáticas presentes em disco.

---

## Behavioural Contract

Every task follows this 5-step loop:

1. **CONTEXT** - Load the relevant context file(s) from the routing table above. Check `patterns/INDEX.md` for a matching pattern. Narrate what is being loaded.
2. **BUILD** - Do the work. If a pattern exists, follow its steps. If deviating, state the deviation and why before writing code.
3. **VERIFY** - Load `context/conventions.md` and run the verify checklist item by item. State each item explicitly with pass/fail.
4. **DEBUG** - If verification fails, check `patterns/INDEX.md` for a debug pattern. Follow it. Fix and re-run VERIFY.
5. **GROW** - After completing the task, update scaffold files as described in `AGENTS.md -> Scaffold Growth`.

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
1. Conferir a régua e os deltas por material.
2. Rastrear MF, SO e o roteiro restante do ES2.
3. Reproduzir o scorer em memória, com bloqueio de rede.
4. Entregar até cinco alavancas e critério numérico de corte.

A investigação deve ultrapassar 20 chamadas locais de leitura/medição.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command "Get-Content docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md; rg -n -A 65 -B 5 'DUAS CAMADAS' docs/reports/pendencias.md; Get-Content C:/Users/Humberto/.codex/skills/graphify/references/query.md; Test-Path graphify-out/graph.json; Get-Content C:/Users/Humberto/.agents/skills/using-superpowers/references/codex-tools.md"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'git status --short; git diff -- src/builder/core/vocabulary_compile.py; Get-Content docs/reports/2026-09-08-handoff-confianca.md'[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 295ms:[0m
warning: unable to access 'C:\Users\Humberto/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\Humberto/.config/git/ignore': Permission denied
 M .claude/settings.local.json
 M .mex/context/architecture.md
 M .mex/context/audit-2026-09-07.md
 M .mex/context/decisions.md
 M .mex/context/external-services.md
 M .mex/context/institutional.md
 M .mex/context/text-chain.md
 M .mex/patterns/delegar-codex-agy.md
 M .mex/patterns/medir-alavanca-ablacao.md
 M docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md
 M docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py
 M src/builder/core/vocabulary_compile.py
 M tests/test_vocabulary_compile.py
?? docs/reports/_harness-2026-09-04/c1-3/brief_codex_astra_camada3.md
?? docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_b.log
?? docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_vocabantigo.log
?? docs/reports/_harness-2026-09-04/c1-3/codigo_determ2_puro_b.log
?? docs/reports/_harness-2026-09-04/c1-3/codigo_sem_puro_b.log
?? docs/reports/_harness-2026-09-04/c1-3/codigo_sem_puro_b2.log
?? docs/reports/_harness-2026-09-04/c1-3/compila_vocab_ES2.log
?? docs/reports/_harness-2026-09-04/c1-3/compila_vocab_IA.log
?? docs/reports/_harness-2026-09-04/c1-3/compila_vocab_SO.log
?? docs/reports/_harness-2026-09-04/c1-3/compila_vocab_TCC.log
?? docs/reports/_harness-2026-09-04/c1-3/compila_vocab_um_curso.py
?? docs/reports/_harness-2026-09-04/c1-3/errados_determ_vocabnovo.txt
?? docs/reports/_harness-2026-09-04/c1-3/mede_opcao_b_zips.log
?? docs/reports/_harness-2026-09-04/c1-3/mede_opcao_b_zips.py
?? docs/reports/_harness-2026-09-04/c1-3/mede_zips_conteudo_perdido.log
?? docs/reports/_harness-2026-09-04/c1-3/mede_zips_conteudo_perdido.py
?? docs/reports/_harness-2026-09-04/c1-3/resposta_codex_astra_camada3.md
?? scripts/monitor-agentes.ps1
diff --git a/src/builder/core/vocabulary_compile.py b/src/builder/core/vocabulary_compile.py
index 4a9bc9c..ab4e949 100644
--- a/src/builder/core/vocabulary_compile.py
+++ b/src/builder/core/vocabulary_compile.py
@@ -163,6 +163,10 @@ def _bundle(taxonomy: dict, unit: dict, labels: List[str], mats: List[dict], roo
     for e in mats:
         md = _entry_markdown_text_for_file_map(root, e) or ""
         heads = _extract_markdown_headings(md, limit=24)
+        # zip nao tem .md proprio (process_zip deixa base_markdown=None): os membros entram pelo nome-base,
+        # nao pelo caminho -- o corte de 60 chars abaixo comeria o nome da classe numa arvore Java.
+        heads = list(heads) + list(dict.fromkeys(Path(str(f.get("title") or "").replace("\\", "/")).name
+                                                 for f in (e.get("extracted_files") or []) if f.get("title")))
         ml = moodle_label_text(e)
         linhas.append(f"- TITULO: {e.get('title')} | LABEL MOODLE: {ml}\n  HEADINGS: "
                       + " | ".join(h[:60] for h in heads[:24]))
# Handoff 2026-09-08 — PONTO DE ENTRADA: revisar o plano "confiança antes de acurácia" antes de executar

Único handoff vivo. Substitui `2026-09-05b-handoff-fila-campanhas.md` (que passa a ser histórico).
**Leia nesta ordem:** (1) este arquivo; (2) `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` — o plano a
revisar; (3) `pendencias.md`, seções datadas 07 e 08/09; (4) `.mex/context/audit-2026-09-07.md`.
Rode `mem-search` para as sessões de 07 e 08/09.

> **A primeira coisa da próxima sessão é REVISAR O PLANO com o user, não executá-lo.**

---

## 1. O que aconteceu em 07 e 08/09, em uma frase

Descobrimos que **parte da acurácia do motor vinha do próprio gold**, tiramos essa contaminação, e o placar caiu. Caiu
porque a régua ficou honesta, não porque o motor piorou — no mesmo período o regime sem LLM nenhum **subiu**.

---

## 2. Estado ao terminar (08/09, tudo commitado, NADA pushed)

### Réguas no produto (Gemini bloqueado por tripwire em todas as medições)
| medida | valor |
|---|---|
| materiais 100% certos | **199/288** |
| bloco | **235/237** |
| unidade | **190/190** |
| subunidade | **161/251** |
| fila | 96 em 348 = **27,6 por 100** |
| **erros confiantes** | **64** |

### Cobertura do gold — o "100%" vale onde há régua
| eixo | gold cobre | do repositório | onde não há régua |
|---|---|---|---|
| bloco | 237 de 348 | 68% | LR inteiro; parte do CG |
| unidade | 190 de 348 | **55%** | **CG (93), LR (7) e FR (22) não têm gold de unidade** |
| subunidade | 251 de 348 | 72% | LR inteiro |

### Os três regimes (`c1-3/mede_sem_voto_llm.log`; base antiga de 233 na subunidade)
| regime | 100% certos | bloco | unidade | subunidade | fila |
|---|---|---|---|---|---|
| produto | 199/288 | 235/237 | 190/190 | 146/233 | 91 |
| sem o voto de LLM | 184/288 | 221/237 | **188/190** | 143/233 | 136 |
| zero LLM | 165/288 | 222/237 | 188/190 | 121/233 | 143 |

### Tutores (HEADs)
MF `3584f89` · SO `c0718a5` · IA `0858418` · ES2 `8cfaf2b` · TCC `73fe7b0` · LR `ae5fead` · FR `7468cd8` · CG `c56b6cb`.
Gerador: `feat/motor-atribuicao` @ `f00c443`, ~965 commits locais, suite 2337.

---

## 3. Os achados desta sessão (o que o plano precisa saber)

### 3.1 CIRCULARIDADE — o mais sério
Quatro dos seis cursos com gold (SO, IA, ES2, TCC) tinham em `course/.glossary_curation.json` um vocabulário cujo
cabeçalho dizia **"proposto-claude a partir de subunit_gt"**. Esses sinônimos viram alias da taxonomia, que é o sinal de
maior peso da subunidade — o motor era medido contra o mesmo gold que originou seu vocabulário.
**Ablação pela rota real** (`ablate_curadoria_gold.log`): subunidade **86/93 → 26/93** nesses quatro cursos
(IA 39/39 → 4/39, ES2 21/28 → 5/28, SO 15/15 → 9/15, TCC 11/11 → 8/11). Bloco e unidade não mudam.
**Feito:** os quatro arquivos foram arquivados em `.glossary_curation.gold.json` (restauráveis) e substituídos por um
gerado só de fontes do professor. Tutores SO `c0718a5` · IA `0858418` · ES2 `8cfaf2b` · TCC `73fe7b0`.

### 3.2 ES2 corrigido na causa — unidade foi a 190/190
Seis materiais da seção "Microsserviços" estavam na unidade errada por **dois** dados de curadoria derivados do gold:
1. `.timeline_curation.json` **pinava o bloco-04** na unidade 02 desde 10/08 (commit `b06b264`, "4 pinos gold-backed").
   O pino contradiz os dois golds atuais.
2. `.glossary_curation.json` punha `service discovery`, `name server`, `service registry`, `API gateway`, `gateway` sob
   2.7 ("integração e IMPLANTAÇÃO"), dando ao bloco-04 afinidade u02=3 × u01=0 no DP posicional.
**As duas correções são necessárias**: só os sinônimos não muda nada (o pino sobrepõe o DP); só o pino não basta.
Justificativa independente do gold: o rótulo do professor separa 1.5 "ARQUITETURA" de 2.7 "implantação", e o cronograma
põe discovery (10/04) e api gateway (17/04) antes da P1 (08/05). Aplicado em `ea0701f`: unidade 21/28 → **28/28**,
subunidade 21 → 27/28, zero perdas.

### 3.3 O compilador de vocabulário por LLM JÁ EXISTE e está desligado em 4 cursos
`src/builder/core/vocabulary_compile.py` (Fase 1b): **1 chamada por unidade com material**, resultado em
`course/.glossary_curation.llm.json` (arquivo separado; o loader funde os dois), com cache. O LLM **não decide
atribuição** — classifica títulos e headings dos materiais nos tópicos DO PLANO. Não é circular: não vê gold.
Já roda em **MF, CG, LR e FR** (gemini-3.5-flash). Amostra do CG: `1.1 Origens ← WHIRLWIND, SAGE, Sketchpad`.
**Não roda em SO/IA/ES2/TCC** porque `vocabulary_compile.py:222` não compila quando existe sidecar manual — e o arquivo
que ocupava esse lugar era o derivado do gold. **O sidecar do professor gerado em 07/09 ocupa o mesmo arquivo e bloqueia
igual.**
**Quanto vale** (`ablate_vocab_llm.log`, 0 chamadas): MF 51→47/58, CG 58→48/82, soma **109→95/140**. Bloco e unidade não
mudam. **Correção importante: MF e CG nunca foram "sem vocabulário". O CG sem vocabulário nenhum é 59%, não 71%.**
**Custo de ligar nos 4:** SO 6 + IA 4 + ES2 2 + TCC 4 = **16 chamadas, uma vez**, depois cache.

### 3.4 A confiança do motor por eixo — é isto que ordena o plano
`calibra_fila_como_regua.log`: "num curso novo, sem gold, quanto do que o motor entrega confiante está certo?"
| eixo | precisão do confiante | recall da fila |
|---|---|---|
| unidade | **157/157 = 100%** | não há erro |
| bloco | 177/178 = 99,4% | 1/2 |
| **subunidade** | **117/181 = 64,6%** | 26/90 = 29% |
**Para a unidade, um curso novo já dispensa gold.** Para a subunidade não: 64 materiais saem errados sem aviso.

### 3.5 A unidade fora do gold se sustenta? Parcialmente
`regua_sem_gold.py` compara o motor com o professor. Ela tem **dois caminhos e só um presta**:
- **A** — a seção nomeia a unidade: confiável.
- **B** — a seção nomeia um tópico e a régua assume a unidade dona: **erra 5 de 5 divergências**, todas no SO, e o gold
  dá razão ao motor nas cinco. (O mesmo caminho já fora refutado como regra do motor em 07/09.)
**Calibração onde as duas réguas existem (44 materiais): motor 44/44, régua 39/44.** O motor é melhor que a régua sem
gold — ela serve para confirmar, nunca para corrigir.
**Cobertura independente:** CG **16 de 93 (17%)**; FR **zero** (os 19 acordos são circulares); LR zero.
Apoio indireto do CG: o bloco bate com o assunto do cronograma em 58/59.

### 3.6 De onde a taxonomia vem × de onde deveria vir
`build_content_taxonomy` tem três fontes e só três: **tópicos** do plano; **aliases** do GLOSSARY (que vem do sidecar);
**aliases** dos headings dos materiais. **O SARC não entra na taxonomia** (alimenta só o alinhamento bloco→unidade) e
**o Moodle também não** (entra como sinal no scorer). O único canal de vocabulário concreto é o sidecar.
Teto de cada fonte em 222 materiais (`mede_fontes_do_professor.log`):
| fonte | alcança o subtópico certo |
|---|---|
| **plano de ensino (rótulo literal)** | **27 = 12%** (IA 0%, MF 7%, ES2 7%, CG 21%, SO 27%) |
| título + label do Moodle | 94 = 42% |
| SARC (label da aula) | 88 = 40% |
| headings do material | 82 = 37% |
| plano + SARC + Moodle | 138 = 62% |
| **nenhuma fonte do professor** | **48 = 22%** — o piso duro sem LLM |
**O plano é a fonte mais fraca**: nomeia a categoria, e o material nomeia o objeto.

### 3.7 O gerador de vocabulário sem gold (feito, mediu 146/233)
`gera_sidecar_professor.py`: a **seção do Moodle** que nomeia exatamente um tópico recebe o vocabulário dos materiais
dela (título, label, headings); o **label da aula do SARC** que nomeia um tópico doa os tokens restantes. Filtros:
boilerplate acadêmico, df > 15%, token que já nomeia outro tópico, e **concentração ≥ 80% das ocorrências na seção que
doa** (foi este que tirou "slides", "página", "vídeos").
Medido: **201/233 (gold) → 135/233 (sem sidecar) → 146/233 (professor)**. Por curso, limpo → professor:
ES2 5→15, SO 9→10, MF 51→52, IA 4→4, TCC 8→8, CG 58→57.
**Onde não funciona, e por quê:** IA 4/39 antes e depois. Ligar "K-Means" a "Modelos Descritivos" é conhecimento de
domínio, e esse mapa não existe no plano, nem no SARC, nem no Moodle.

### 3.8 A restrição unidade → subunidade já existe
`routing/file_map.py:184`: `auto_map_entry_subtopic` filtra o índice de tópicos por `winning_unit_slug`. É absoluta.
Consequência: **errar a unidade torna a subunidade inalcançável** — hoje 4 dos 77 erros de subunidade.

### 3.9 O Moodle NÃO dá a unidade "na maioria das vezes"
Medido em 190 materiais: a seção nomeia a unidade correta em **43 (23%)**, o label em 12 (6%), o bloco em **190 (100%)**.
Quando a seção arrisca, acerta **43/43** — precisão altíssima, cobertura baixa; por isso entra como override explícito.
**A descrição usual está invertida: o SARC dá a UNIDADE** (cronograma → blocos → DP posicional → o bloco decide) **e o
Moodle dá o QUANDO** (a data do label coloca o arquivo no bloco).

### 3.10 A unidade não é livre de LLM (ressalva que muda o placar)
**96 dos 348 materiais (28%) tiveram o BLOCO decidido por voto de LLM** (`routing/motor/llm_vote.py`, TIER 3, cache por
md5, `temporal_block_provider=llm`). O reprocess com tripwire **reusa o voto em cache** em vez de rechamar.
Mas o impacto é pequeno: sem o voto, a unidade cai só de 190 para **188**. O custo do voto está na **fila** (91 → 136) e
nos materiais sem bloco. **Sem voto o motor não erra mais, desiste mais.**

### 3.11 Anatomia da fila (96 = 74 dúvida + 22 mudou)
| motivo | n | significado |
|---|---|---|
| **conflito** | **48** | o texto aponta uma unidade e o bloco aponta outra. O bloco decide por desenho. **Metade da fila, nunca atacado** |
| sub-ambígua | 13 | 2+ subtópicos empataram acima do limiar |
| sub-empate | 10 | empate exato de score |
| flag:disamb | 9 | o bloco saiu de um desempate |
| due-straddle | 1 | entrega entre dois blocos |
| mudou | 22 | decisão confiante que se moveu na última sync (só CG). Transitório |

### 3.12 Duas correções de erro meu, para não se repetirem
- **A régua de subunidade é 251, não 233.** `subunit_gt_FR.csv` tem 18 materiais pontuáveis que nunca entraram em
  medição nenhuma desta campanha. FR faz **15/18**. Os deltas medidos continuam válidos (mesma base dos dois lados),
  mas os absolutos publicados até 08/09 estavam incompletos.
- **Material sem bloco de verdade é 1, não 7.** Contar `temporal_block_id` vazio sem olhar `manual_timeline_block_id`
  infla em 6 materiais do MF que têm pino. O único é `IA / prova-1-2024-02`, categoria `provas`, seção TDE — fora do
  eixo temporal por desenho, **não é pendência**.

### 3.13 O gargalo é o INSUMO, não a regra (medido em 07/09)
| classe | n | acerto |
|---|---|---|
| `.pdf` | 109 | **94%** |
| `.zip` (código) | 35 | 66% |
| `.html` (páginas-índice) | 37 | **62%** |
| material com link de YouTube | 28 | **57%** |
| texto próprio | 184 | 88% |
Confundimento desfeito: aprovado 93% × staging 71% **não é causal** — dentro do CG, aprovado 50% e staging 72%.
55% do erro de subunidade é material que **não tem uma subunidade única** (9 gold vazio, 12 páginas-índice).

---

## 4. NÃO FAZER — refutado por medição nesta sessão
| alavanca | resultado |
|---|---|
| Agrupar arquivos por palavras-chave para **substituir** o scorer | teto 65% com oráculo; real 85/233, pior que 114 por arquivo. Componentes conexas degeneram (IA vira 1 grupo de 39) |
| Título do vídeo no lugar do hash (91% dos 246 links são ID de 11 chars) | 183/183 títulos recuperados do oEmbed; **ganha 0, perde 2**. Mais texto do corpo PIORA: o índice fala dos filhos |
| Piso de score no resultado final | todo piso perde; melhor piso = 0 |
| Título com vocabulário completo | teto 3/38, saldo 0 |
| Página-índice decidida pelo cabeçalho | teto 6/38; melhor +2 com 17 mudanças |
| Triagem da chamada de LLM por sinal determinístico | o sinal **não prediz**: MF-01 tem 7% de sinal fraco e vale −4; MF-03 tem 50% e vale 0 |
| "A prova é fronteira de unidade" | 3 a favor, 25 contra, 8 avaliações neutras |
| Alias ambíguo entre tópicos como alavanca | 7 em 663, nenhum decide bloco |
| Automatizar o gold a partir de Moodle + SARC | erro de categoria: a régua dessas fontes acerta 39/44 onde o motor acerta 44/44 |
| **(07/09)** regra pai × filho · piso de força na 1ª passada · seção → unidade dona · zero-pad no título · número na chave | todas refutadas |

## 5. O que ENTROU nesta sessão
| mudança | onde | efeito medido |
|---|---|---|
| Descrição de imagem fora do texto que o scorer pontua | `44ed407` | +2 materiais; sub 193 → 195 |
| Pino do bloco-04 do ES2 removido + 5 sinônimos movidos de 2.7 para 1.5 | ES2 `ea0701f` | unidade 21/28 → 28/28 |
| GLOSSARY descontaminado nos 4 cursos + gerador sem gold | `baab4ac` + 4 tutores | régua honesta: 201 → 146/233 |

---

## 5b. DECISÕES JÁ TOMADAS pelo user em 08/09 — não reabrir

### Gemini LIBERADO, com protocolo de contenção
Gasto: `vocabulary_compile`, **1 chamada por unidade com material** = SO 6 + IA 4 + ES2 2 + TCC 4 = **16, uma vez**.
1. Um curso por vez, conferindo o contador logado (`vocab: <curso> — N chamada(s)`); se N passar do número de unidades
   do curso, **parar**.
2. `TUTOR_NO_VOCAB_COMPILE=1` continua em todo script de medição.
3. O voter **não** é rechamado (96 votos em cache por md5; `DEFAULT_CAP = 20` como rede).
4. `gemini_auto_summarize` continua desligado (incidente de 05/09: 60 arquivos re-resumidos).
5. Pós-check: contar chamadas do dia antes e depois e registrar no tracker.
6. O sidecar do professor sai da frente por **renomeação**, nunca apagando.

### A próxima campanha é a C5 DÍVIDAS DE DADOS, não a C3
Medido em `compara_c3_c5.log`: **C3 cobre 71 materiais (20%) e carrega 8 dos 92 erros (9%)**, com taxa de erro de 14%
contra 34% no resto — é já a parte mais saudável do repositório. A C5 tem defeito com tamanho medido (**32 dos 35 zips**
com colisão de nome de conteúdo; 99 nomes: CG 60, ES2 29, MF 10), a dívida de régua (**122 materiais sem gold de
unidade**) e o gargalo do insumo (pdf 94% × html 62% × vídeo 57%).
**Ressalva registrada:** o ganho de acurácia de corrigir esses defeitos **não foi medido**. É a aposta melhor
fundamentada, não uma certeza.
**Dois números meus corrigidos no caminho:** "43 sem texto" era **1** (42 são código com resumo); a contagem de
colisões de zip antes incluía duplicatas dentro do mesmo zip e dotfiles.

## 6. Decisões ABERTAS do user (travam trabalho)
| item | o que trava |
|---|---|
| **Qual camada LLM cortar** para ficar em duas | decisão de arquitetura aberta desde 06/09 |
| **Push/merge** dos ~965 commits locais | decisão de fronteira |
| **Posição da C7 (imagens)** na fila | ordenação |
| Revisão da fila do CG (`revisar_queue.md`) | trabalho humano |
| Correção da extração dos zips | **32 dos 35 zips** afetados; 99 nomes de conteúdo colidem entre zips do mesmo curso (CG 60, ES2 29, MF 10); `.smv` ignorado |

---

## 7. FILA DE CAMPANHAS — e qual seria a próxima

### Aberta
**C1 TRAVESSIA.** O plano de 08/09 (Fases 1 e 2.1–2.3) é o conteúdo dela. A travessia final e o item 4 dependem de LLM.

### Próxima, pela ordem registrada em 03/09
**C3 PROVAS, LISTAS E TRABALHOS.**

### Estacionadas
C7 imagens · C2 bibliografia · C4 limpa · C5 dívidas de dados · C6 web.

### DECIDIDO em 08/09: a próxima é a C5 (fundamento medido em §5b)
A ordem de 03/09 punha a C3. Os dados mostraram que a C3 é já a parte mais saudável do repositório: 20% dos materiais
e 9% dos erros. As três candidatas, com o dado que as sustenta:

1. **C5 DÍVIDAS DE DADOS, promovida.** O gargalo medido é o insumo: PDF 94%, HTML 62%, vídeo 57%. E há bugs conhecidos
   com tamanho medido: 168 colisões de nome em 14 zips do CG, `.smv` ignorado, páginas do Moodle. Além disso o gold de
   unidade do CG (93 materiais, 27% do repositório) vive aqui. **É a campanha que ataca a causa, não o sintoma.**
2. **C7 IMAGENS.** O custo real de API é o Datalab por página, não o voter. Há um caminho medido para baratear a página
   HTML (Ollama primeiro: 105 → 34 chamadas). Entra se o critério for custo.
3. **C3 provas/listas**, como registrado. Entra se o critério for cobertura de categorias.

**Decidido: C5 antes de C3.** Todo ganho de motor que sobrou é de segunda ordem (2 a 5 pontos), enquanto o insumo
responde por diferenças de 30 pontos entre classes de material — e a C3 não tem massa de erro para justificar
prioridade.

---

## 8. Leis (reafirmadas)
- **Gold só mede, nunca decide — e nunca vira insumo.** Entrou duas vezes (sidecar de sinônimos, pino de bloco) e foi
  retirado em 07 e 08/09.
- **SARC e Moodle acima do gold** quando divergirem.
- Dado antes de código: nenhuma alavanca entra sem medição prévia pela rota real.
- Gate zero-diff, teste e reprocess registrado nos 8 em toda mudança de motor.
- Ao publicar número de subunidade, dizer a base (**251**) e o regime.
- Nada é pushed sem ordem explícita.
- Tokens nunca impressos. `.claude/settings.local.json` nunca em stage.

## 9. Ferramentas desta sessão (`docs/reports/_harness-2026-09-04/c1-3/`)
`diag_gargalo.py` (38 erros por causa × evidência + anatomia da fila) · `mede_classe_material.py` ·
`mede_atribuir_vazio.py` · `mede_fontes_do_professor.py [--limpo]` · `ablate_curadoria_gold.py` ·
`gera_sidecar_professor.py` · `mede_sidecar_professor.py` · `descontamina_glossary.py --aplicar` ·
`ablate_vocab_llm.py` · `triagem_vocab_llm.py` · `mede_cluster_keywords.py` · `mede_vizinho_keywords.py` ·
`simula_propaga_similaridade.py` · `mede_moodle_da_unidade.py` · `mede_sem_voto_llm.py` · `estado_08_09.py` ·
`calibra_regua_unidade.py` · `calibra_fila_como_regua.py` · `corrige_curadoria_es2.py` · `aplica_correcao_es2.py`.
**Todos com log homônimo — e os `.log` estão no `.gitignore`, existem só nesta máquina.** Os scripts são versionados,
então tudo é reproduzível; a evidência bruta, não.

## 10. Artefatos publicados
| artefato | estado |
|---|---|
| [Placar do Motor](https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de) | **atualizado 08/09**: estado de hoje no topo, histórico de 06/09 abaixo |
| [Matriz de Atribuição](https://claude.ai/code/artifact/4ddad807-e2fe-4ede-a3ca-c175916f7ca6) | **atualizada 08/09**: coluna `produto` regenerada; `zero`/`vocab`/`auto` de snapshots de 06/09 |
| [Gold × Moodle × SARC](https://claude.ai/code/artifact/f53542b1-9061-4034-a1f3-e86ce001a81f) · [Razão dos Blocos](https://claude.ai/code/artifact/d2ef4eaa-3483-412a-9dc8-110b1f9ccacb) | aviso datado de 08/09 |
| [Raio-X](https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f) · [Anatomia do Bloco](https://claude.ai/code/artifact/ba1de7bf-a802-49fc-b88b-6be358d4b796) | **não tocados** — declaram-se leitura de 01–02/09 e linkam o Placar; a nota interna de 06/09 deles cita números superados. Têm SVG desenhado à mão: regenerar exige refazer as medições daquelas páginas |

[32m succeeded in 692ms:[0m
# Plano — confiança antes de acurácia

last_updated: 2026-09-08 (reescrito depois da atualização dos artefatos)
Entrada: `docs/reports/pendencias.md` (tracker vivo) · `.mex/context/audit-2026-09-07.md` (memória) ·
harness `docs/reports/_harness-2026-09-04/c1-3/`
Artefatos: [Placar](https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de) ·
[Matriz](https://claude.ai/code/artifact/4ddad807-e2fe-4ede-a3ca-c175916f7ca6)

---

## 1. A tese, e por que esta ordem

O gold deixou de ser insumo do motor em 07/09 (`baab4ac`, `ea0701f`); os números abaixo são pós-limpeza. Ele mede. O que o motor tem de próprio para saber se acertou é a **confiança**, que
vira a fila de revisão. Medido em 08/09 (`c1-3/calibra_fila_como_regua.log`):

| eixo | precisão do confiante | leitura |
|---|---|---|
| unidade | **157/157 = 100%** | inferência: CG 93, LR 7 e FR 22 não têm gold e ficam fora da conta; testa em 3.2 |
| bloco | 177/178 = 99,4% | idem, na prática |
| **subunidade** | **117/181 = 64,6%** | **64 materiais saem errados sem aviso** |

Subir acurácia com a confiança mentindo aumenta os acertos **e** os erros silenciosos. Produto que erra calado é pior
que produto que pergunta: o aluno não tem como saber que aquele material está no lugar errado. **Confiança primeiro.**

Isso também é o que responde ao objetivo de fundo: *a atribuição não deve depender de gold feito à mão*. Na unidade, nos cursos com gold, já
não depende. Na subunidade, o caminho não é remover o gold, é usá-lo **uma vez** para descobrir onde a confiança mente;
depois disso a confiança viaja sozinha para cursos novos.

**O que não fazer:** automatizar a criação do gold a partir do Moodle e do SARC. Medido: a régua construída dessas
fontes acerta 39/44 onde o motor acerta 44/44 — um gold automático teria introduzido 5 erros no SO. Não se mede um
instrumento com uma cópia pior dele mesmo.

---

## 2. Estado de partida (08/09, produto em disco, Gemini bloqueado)

| medida | valor |
|---|---|
| materiais 100% certos | 199/288 |
| bloco | 235/237 |
| unidade | 190/190 |
| subunidade | **161/251** |
| fila | 96 em 348 = 27,6 por 100 |
| **erros confiantes** | **64** |

**Cobertura do gold:** bloco 68% do repositório, unidade 55%, subunidade 72%. CG (93 materiais) e LR (7) não têm gold
de unidade nenhum; LR não tem gold de bloco.

**Regimes** (`c1-3/mede_sem_voto_llm.log`, base antiga de 233 na subunidade):

| regime | 100% certos | bloco | unidade | subunidade | fila |
|---|---|---|---|---|---|
| produto | 199/288 | 235/237 | 190/190 | 146/233 | 91 |
| sem o voto de LLM | 184/288 | 221/237 | 188/190 | 143/233 | 136 |
| zero LLM | 165/288 | 222/237 | 188/190 | 121/233 | 143 |

O voto de LLM vale 14 no bloco e 2 na unidade. Sem ele o motor não erra mais, **desiste mais**.

---

## FASE 1 — HONESTIDADE DA CONFIANÇA

**Objetivo:** que o motor mande para a fila o que hoje entrega calado.
**Régua:** `calibra_fila_como_regua.py`, precisão do confiante por eixo.
**Gate de saída:** precisão do confiante da subunidade **≥ 90%**, sem regressão em bloco e unidade, com o crescimento
da fila declarado e aceito pelo user.

### 1.1 Diagnosticar os 64 erros confiantes · 0 chamadas
Cruzar, para cada um: score do vencedor, margem para o segundo, origem do sinal (rótulo do plano, alias de heading,
alias compilado), tamanho do texto, classe do insumo. Só medição, sem código de motor.
Hipótese de trabalho, **não medida**: margem alta vindo de alias longo casando por acaso em texto curto.

### 1.2 Calibrar o limiar · 0 chamadas
Varrer o limiar de **confiança/margem** contra o gold, medindo os dois lados: quantos erros confiantes somem e quanto a
fila cresce. O gold entra **uma vez**, aqui.
**Ressalva registrada:** piso sobre o *score* já foi refutado em 07/09 (todo piso perde). Este item é sobre outra
grandeza. Se também não houver corte útil, o item morre e vira registro.

### 1.3 Fazer a decisão fraca cair na fila
Só se 1.2 achar ponto. Regra no motor, com gate zero-diff, teste e reprocess registrado nos 8.

---

## FASE 2 — ACURÁCIA

Começa com a Fase 1 fechada. Os três primeiros itens não gastam chamada.

### 2.1 Propagação por similaridade — **+5 medido** · 0 chamadas
Material indeciso depois da 1ª e da 2ª passada herda a subunidade do vizinho mais similar entre os que o motor decidiu
com confiança. Similaridade = Jaccard dos tokens distintivos, dentro da unidade.
`simula_propaga_similaridade.log`: regime atual 135 → 140, ganha 6 perde 1, piso 0,05–0,10.

### 2.2 Filtro mais duro no vocabulário compilado — **teto +2 por ablação; filtro não medido** · 0 chamadas
Cortar termo doado cujo núcleo aparece no vocabulário ou nos materiais de outra unidade, e recusar doação a tópico de
rótulo meta ("Áreas relacionadas", "Conceitos", "Introdução").
`triagem_vocab_llm.log` l.20 mede remover o vocabulário LLM inteiro da unidade 01 do CG (+2), não o filtro; outras 3 chamadas são neutras. Medir o filtro em si antes de executar este item.

### 2.3 `conflito` — 48 itens, metade da fila, nunca atacado · 0 chamadas
Quando o texto aponta uma unidade e o bloco aponta outra, o bloco vence por desenho e o desacordo só vira registro.
Há gold de unidade em 190 materiais para arbitrar quem acerta nesses casos. **Medir antes de mexer.**

### 2.4 Ligar o compilador de vocabulário nos 4 cursos bloqueados · 16 chamadas · **GEMINI LIBERADO (user, 08/09)**
SO 6 + IA 4 + ES2 2 + TCC 4, uma vez, cacheadas em `course/.glossary_curation.llm.json`.
Referência de 02/09 citada no próprio código: este prompt levou o IA de 5 para 37/39.

**Protocolo de contenção, não negociável nesta campanha:**
1. **Um curso por vez**, conferindo o contador que o compilador loga (`vocab: <curso> — N chamada(s)`) antes do próximo.
   Se N passar do número de unidades com material daquele curso, **parar e investigar**.
2. `TUTOR_NO_VOCAB_COMPILE=1` continua em **todo** script de medição. Medição nunca compila.
3. O voter **não** é rechamado: os 96 votos de bloco já estão em cache por md5, e `llm_vote.DEFAULT_CAP = 20` por rodada
   segue como rede.
4. `gemini_auto_summarize` continua **desligado** (incidente de 05/09: um reprocess re-resumiu 60 arquivos).
5. Pós-check obrigatório: contar chamadas do dia antes e depois, e registrar o número no tracker junto do resultado.
6. Para o sidecar do professor sair da frente (`vocabulary_compile.py:222`), **renomear**, nunca apagar.

---

## FASE 3 — COBERTURA DA RÉGUA

### 3.1 Incluir o FR no conjunto padrão · 0 chamadas
`subunit_gt_FR.csv` tem 18 materiais pontuáveis que nunca entraram em nenhuma medição desta campanha; o FR faz 15/18.
Todo script do harness que hoje usa 6 cursos passa a usar 7. **Sem isso, todo absoluto publicado continua incompleto.**

### 3.2 Gold de unidade para o CG
93 materiais, 27% do repositório, hoje sem régua nenhuma nesse eixo. A confirmação independente pelo professor cobre só
17% deles (16 de 93); no FR ela é zero, porque os 19 acordos são circulares. É o único jeito de fechar a pergunta
"a unidade se sustenta fora do gold?".

---

## 3. Decisões abertas que travam trabalho

| item | o que trava |
|---|---|
| **Qual camada LLM cortar** para ficar em duas | decisão de arquitetura aberta desde 06/09 |
| **Push/merge** dos ~965 commits locais | nada técnico; é decisão de fronteira |
| **Posição da C7 (imagens)** na fila de campanhas | ordenação |
| Revisão da fila do CG (`revisar_queue.md`) | trabalho humano |
| Correção da extração dos zips | **32 dos 35 zips** afetados; 99 nomes de conteúdo colidem entre zips do mesmo curso (CG 60, ES2 29, MF 10) |

## 4. Campanha formal e a próxima

**C1 TRAVESSIA** é a única aberta; este plano é o conteúdo dela (1.x e 2.1–2.3). Os itens 3.x continuam a C5.

**Decidido pelo user em 08/09: a próxima é a C5 DÍVIDAS DE DADOS, não a C3.** Fundamento medido
(`compara_c3_c5.log`), depois de corrigir dois números meus que estavam inflados:

| grupo | materiais | errados | % erro |
|---|---|---|---|
| **C3** (provas, listas, trabalhos, gabaritos) | 71 (20%) | **8 (9% dos erros)** | **14%** |
| resto | 277 | 84 | **34%** |

1. **C3 não tem massa de erro:** é já a parte mais saudável do repositório.
2. **A C5 tem defeito com tamanho medido:** **32 dos 35 zips** têm colisão de nome de conteúdo entre si (99 nomes:
   CG 60, ES2 29, MF 10). O código extraído e o resumo desses materiais podem estar trocados.
3. **A C5 tem a dívida de régua:** 122 materiais sem gold de unidade (CG 93, FR 22, LR 7), 35% do repositório.
4. **O gargalo é o insumo:** pdf 94% · zip 66% · html 62% · com link de YouTube 57%.

**Ressalva honesta:** os itens 2 e 4 são defeitos de dado com tamanho medido; **o ganho de acurácia que corrigi-los
traz não foi medido**. A C5 é a aposta melhor fundamentada, não uma certeza.
**Dois números meus corrigidos:** "43 materiais sem texto" era 1 (42 são código com resumo); e a contagem de colisões
de zip antes incluía duplicata dentro do mesmo zip e dotfiles.

## 5. Estado dos artefatos publicados (08/09)

| artefato | ação |
|---|---|
| **Placar do Motor** | reescrito: o estado de 08/09 vem primeiro, o histórico de 06/09 fica abaixo marcado como tal |
| **Matriz de Atribuição** | coluna `produto` regenerada do disco; nota explicando a descontaminação. As colunas `zero`, `vocab` e `auto` continuam vindo de snapshots de 06/09 |
| **Gold × Moodle × SARC** · **Razão dos Blocos** | aviso datado de 08/09 com link para o Placar |
| **Raio-X** · **Anatomia do Bloco** | **não tocados.** Já se declaram como leitura de 01–02/09 e já linkam o Placar; a nota interna de 06/09 deles cita números superados. Reescrevê-los à mão arriscaria corromper os diagramas SVG. Regenerar exige refazer as medições daquelas páginas |

## 6. Regras que valem em todos os itens

- Dado antes de código: nenhuma alavanca entra sem medição prévia pela rota real.
- Gate zero-diff, teste e reprocess registrado nos 8 tutores em toda mudança de motor.
- Gold só mede, nunca decide, e nunca vira insumo. Entrou duas vezes e foi retirado em 07 e 08/09.
- SARC e Moodle acima do gold quando divergirem.
- Ao publicar qualquer número de subunidade, dizer a base (251) e o regime.
- Nada é empurrado para `main` sem ordem explícita.
1344-empate 20 (CG 10, IA 5) · ambigua 17 · score < 1: 40 (CG 22) · propagadas 25 · subtopicos no plano 229 (CG 59, SO 36, FR 33) = 1,3 material por
1345-subtopico. **Duvida do motor x erro no gold (produto, 233):** 40 errados, 47 com sinal de duvida, 20 errados-e-com-duvida, 20 errados confiantes
1346-(CG 15 de 33), 27 alarmes falsos: o sinal aponta o CURSO (revisar/100 CG 76, FR 59) e filtra revisao; nao mede acerto.
1347-**Relatorio consolidado (artefato, pedido do user "todos os numeros, facil de entender"):** https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de
1348-
1349:## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3 (RESUMOS DE CODIGO) MEDIDA: ABLACAO E SUBSTITUTO DETERMINISTICO (06/09, sessao 6; DECISAO DO USER)
1350-**Pedido do user:** "quero o motor o mais automatico possivel, LLM para 3 camadas fica pesado, queria deixar no maximo duas"; "nao quero ficar criando
1351-novas rotas para o motor". **Peso medido no produto (8 tutores):** vocab = 1 compilacao por curso · resumos de codigo = 85 (1 por arquivo/zip, cache por
1352-hash, so re-roda se o arquivo mudar) · votos = 205 (1 por material incerto, cache). Curso novo do tamanho do CG: 1 + 17 + 42.
1353-**Ablacao da camada 3 (`c1-3/shim_codigo.py {sem|determ} {puro|holdout}`, copias, tripwire, 0 chamadas; motor puro + vocab + propagacao):**
1354-| regime | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
1355-|---|---|---|---|---|---|
1356-| COM resumos do Gemini (referencia, `b_prop_*.log`) | 186 | 183 | 53 | **87** (83 primario) | 31 |
1357-| SEM resumos (`code_curation.json` vazio, `codigo_sem_*.log`) | 186 | 183 | 53 | **71** (67) | 31 |
1358-| substituto deterministico v1: zip/ipynb crus (`codigo_determ_*.log`) | 186 | 183 | 53 | 79 (75) | 31 |
1359-| substituto deterministico v2: os `.md` que o motor JA gera para codigo/zip = o mesmo bundle que o Gemini recebe (`codigo_determ2_*.log`) | 186 | 183 | 53 | 78 (74) | 31 |
1360-**Leitura:** a camada 3 so sustenta a SUBUNIDADE (+16 sobre nada, +8 sobre o melhor substituto); bloco, unidade, cobertura e holdout nao a sentem.
1361-Os 8 que SO o resumo do Gemini acerta (listados na copia, `winner_score`/`empate`): SO threads x3 (empate exato 0,11: 'pthread' esta no vocab mas
1362-empata; o Gemini injeta 'gerenciamento de processos'/'programacao concorrente') · IA perceptron x4 + mlp-xor (na copia 'perceptron' NAO e alias de
1363-`modelos-preditivos`, so 'MultiLayer Perceptron'; o notebook tem 'Generalizacao', alias de `introducao`; o Gemini injeta 'Perceptron'/'Classificacao')
1364-· ES2 roteiro1 (zip Spring: o codigo so tem 'currency/exchange'; o Gemini injeta 'Microsservicos'). Ou seja: o resumo vale pelo VOCABULARIO DE
1365-CATEGORIA que o codigo nao contem — e um remendo da camada 2 (vocab), nao sinal proprio do codigo. Os outros 6 erros sao os mesmos com ou sem Gemini.
1366-**Decisao do user (aberta): qual camada cortar.** Recomendacao com numero: cortar a 3 (menor ganho das tres: +8 sub; vocab vale +57 sub/+10 unidade;
1367-voter vale +7 bloco/+4 holdout) e trocar o PRODUTOR de `code_curation.json` pelo deterministico v2 — mesma rota (`code_curation_signal_text` +
1368-`entry["concepts"]`), produtor diferente, 0 rotas novas; custo -8/93 na subunidade, 0 no resto. Para nao perder os 8 mantendo duas camadas: a
1369-compilacao do vocab (camada 2) passar a ver o bundle de codigo (`vocabulary_compile` le `_entry_markdown_text_for_file_map`, que para zip devolve
1370-vazio) — mesma chamada, mais insumo; exige Gemini para remedir -> decisao 3 do handoff.
1371-**"% de similaridade vocab x nome do material" (pergunta do user; `c1-3/simula_similaridade_nome.py`, 93 pontuaveis, 0 chamadas):** Jaccard de tokens
1372-do nome (title + label) x label do plano (sem LLM): limiar 0,5 -> 9 certos 0 errados 84 sem atribuicao; 0,2 -> 16/1/76. x label + aliases do vocab LLM:
1373-0,5 -> 27/0/66; 0,3 -> 46/3/44; 0,2 -> 63/6/24. `difflib` 0,3 -> 46 certos 41 errados. O scorer do motor (mesma ideia, texto inteiro + pesos): 87 com
1374-vocab, 30 sem. **Leitura:** faz sentido e JA E o que o scorer faz (sobreposicao de tokens material x vocab, por topico); um indice explicito nao
1375-acrescenta informacao — o teto e o vocabulario, nao a funcao de similaridade. Nenhuma rota nova proposta.
1376-
1377-## CONTRIBUICAO POR CAMADA (06/09, pedido do user: "os numeros obtidos sem LLM" antes de uma materia 100% nova)
1378-| camada (copias, tripwire, 0 chamadas) | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
1379-|---|---|---|---|---|---|
1380-| 100% sem LLM: motor puro SEM vocab compilado, SEM propagacao (`b_semvocab_semprop_puro.log`) | 187 conf-err 1 | 173 (ES2 18/28) | 54 | **30 (32%)** | 31 |
1381-| idem COM propagacao por headings (`b_semvocab_puro.log`) | 187 | 173 | 54 | 26 — **regride 4**: sem vocab as sementes 'confiantes' erram e a propagacao amplifica | 31 |
1382-| + vocab compilado por LLM (cache; ~1 chamada por unidade) | 186 | 183 | 53 | **87** | 31 |
1383-| + voter com cache (~35% dos materiais votados) = AUTOMATICA v2 | **193 conf-err 0** | **185** | 53 | 87 | **35** |
1384-| + curadoria (pinos, glossario manual) = produto | 198 | 191 | 55 | (IA 39/39) | 35 |
1385-**Leitura:** a propagacao PRESSUPOE o vocab compilado (com ele +5, sem ele -4): se um dia o pipeline rodar sem a camada 2, desligar a 2a passada.
1386-O vocabulario compilado e a camada que sustenta a SUBUNIDADE (30 -> 87) e boa parte da UNIDADE (173 -> 183; ES2 18 -> 28): sem ele o plano
1387-nao tem os nomes dos algoritmos. O voter sustenta o BLOCO (186 -> 193, conf-err 1 -> 0; holdout 31 -> 35). A curadoria vale 5 blocos (MF 6 pinos) e 6
1388-unidades (SO 3 + IA 3). Para uma materia nova, o custo de LLM medido no rebuild do CG (93 materiais): vocab ~9 (1/unidade) + resumos de codigo 17
1389-(1/zip ou arquivo) + voter ~40 (flagados/serie/funil) ~= 66 chamadas; travessia (opcional, medicao) +45.
1390-
1391-## SUBUNIDADE SEM LLM — PROPAGACAO DE VOCABULARIO POR HEADINGS NO MOTOR (05/09 noite, sessao 6, FEITO; gerador `4a239d9`)
1392-**Pedido do user:** arrumar as subunidades de maneira automatica, sem LLM. **Raiz:** o plano nomeia categorias e o material nomeia algoritmos; o vocab
1393-compilado por LLM nao emitiu 'perceptron'/'rede neural'/'MLP' para o IA e o remendo era o glossario MANUAL (curadoria).
1394-**Regra (`resolver_apply.propagar_vocabulario_por_headings`, 2a passada):** token EXCLUSIVO dos headings/titulo dos materiais que a 1a passada atribuiu
1395-com confianca (>= 0,7) a um subtopico vira alias desse subtopico; so materiais vazios/ambiguos/fracos sao repontuados; decisao confiante nunca e
1396-sobreposta. Salvaguardas medidas, cada uma: sem stems genericos do motor ('exemplo'/'respostas' viravam alias: CG `slab` e MF `respostas` caiam) · df
1397-<= 25% dos materiais ('sumario'/'aula' do TCC) · >= 2 confiantes · exclusivo de UM subtopico · so nos nao-confiantes (o CG perdia 8 confiantes sem isso).
1398-Limiares em `thresholds.T` (SUBUNIT_PROPAG_CONF 0,7 · MIN_ENTRIES 2 · DF_MAX 0,25; grade de 8 pontos em `c1-3/simula_propaga_grid_df025.log`).
1399-Teste `tests/test_subunit_propagacao.py` (2). Suite 2328. Reason gravada: `propagado-headings`.
1400-**Medido antes de entrar (`c1-3/simula_propaga_headings_6golds.py`, 6 golds = 233, CG/MF propostos):** 182 -> 187, **+5 -0**, 4 mudancas erro->erro;
1401-FR/LR 0 mudancas. Alias = label de sessao do SARC (`simula_alias_sessao_sub.py`): 0 efeito nos 93.
1402-**Gates (tripwire, 0 chamadas):** motor puro +vocab bloco 186/199 · unidade 183/191 · cobertura 53/57 · **sub 82 -> 87/93 (83 primario)** · automatica bloco 193/199 (97,0%, conf-err 0) · unidade 185/191 · cobertura 53/57 · **sub 87/93 (93,5%)**
1403-· holdout CG puro 31/35 · automatico 35/35 · CG sub automatico 49/82 (1 propagado) · curada bloco 198/199 · 191/191 · 55/57 · produto x 6 golds de
1404-subunidade 193/233 com extras (igual; primario 162) · sentinela 0 · censo revisar/100 57,5 (sub-empate 24 -> 20, sub-ambigua 19 -> 17) · determinismo 8/8, 0 arquivos.
1405-**Reprocess registrado dos 8 (`c1-3/reprocess_8_propagacao.py`, tripwire de produto; NAO commita quando so `updated_at` muda — caixa aplicada):**
1406-MF `7a8707a` (sub mudou 4: t1-thy, hoare, invariantes, terminacao -> verificacao-de-programas; os zips com resumo colidido) · IA `0075334` (2: lista-de-
1407-exercicios-i, p2-202401 -> busca-adversaria) · ES2 `4c8011b` (6, todos dentro dos extras do gold) · TCC `621c292` (1: aula-16 -> prova-da-indecidibilidade) ·
1408-SO/LR/FR/CG so `updated_at`, sem commit. Bloco 0 · unidade 0 · flagadas iguais · propagados 26 nos 8.
1409-**O que sobra na subunidade do motor puro (6/93):** SO fork/exec x4 (gold pela regra humana 'apoio rotula pelo card', que o IA contradiz: sem regra
1410-generica), ES2 `devops`/`kubernetes` (quase-empate). No IA o automatico agora iguala o glossario manual (39/39) — o remendo humano deixou de ser necessario.
1411-
1412-## CG UNIDADE SEM LLM E SEM PINO — RADICAL-FALLBACK NO MOTOR + 2 PINOS REMOVIDOS (05/09 tarde, sessao 6, FEITO; gerador `ff21cab`, CG `0d2020a`)
1413-**Pedido do user:** o maior numero possivel sem LLM, sem curadoria por curso. **Medido antes (`c1-3/simula_cg_unidade_generico.py`, nos 8):** radical so como
1414-fallback (RF) +1 bloco (CG 15 -> u07), 0 colateral, unidade 183 = 183 · generico por radical entre unidades (SG) 183 -> 172, SO 32 -> 21: REFUTADO · heranca
# graphify reference: query, path, explain

Load this when the user asks a question against an existing graph, or runs `/graphify path` or `/graphify explain`. The core's query stub points here for the full traversal flow. These flows use the `graphify query` CLI when it is available and fall back to an inline NetworkX traversal otherwise.

Two traversal modes - choose based on the question:

| Mode | Flag | Best for |
|------|------|----------|
| BFS (default) | _(none)_ | "What is X connected to?" - broad context, nearest neighbors first |
| DFS | `--dfs` | "How does X reach Y?" - trace a specific chain or dependency path |

First check the graph exists:
```bash
$(cat graphify-out/.graphify_python) -c "
from pathlib import Path
if not Path('graphify-out/graph.json').exists():
    print('ERROR: No graph found. Run /graphify <path> first to build the graph.')
    raise SystemExit(1)
"
```
If it fails, stop and tell the user to run `/graphify <path>` first.

### Step 0 — Constrained query expansion (REQUIRED before traversal)

graphify's `query` CLI matches nodes via case-folded substring + IDF — there is **no stemming, no synonyms, no cross-language match** inside the binary, and the inline fallback below matches the same way. If the user's question uses different language or different domain vocabulary than the graph's labels (user says "обработчик" / graph says "handler"; user says "authentication" / graph says "Guardian"), the literal matcher returns 0 hits and the answer collapses to noise.

Fix this **without inventing tokens** by expanding the query against the actual graph vocabulary first:

1. Extract the token vocabulary from node labels:
```bash
$(cat graphify-out/.graphify_python) -c "
import json, re
from pathlib import Path
data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
vocab = set()
for n in data['nodes']:
    for c in re.findall(r'[^\W\d_]+', n.get('label','') or '', re.UNICODE):
        parts = re.findall(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+', c) or [c]
        for p in parts:
            t = p.lower()
            if 3 <= len(t) <= 30:
                vocab.add(t)
Path('graphify-out/.vocab.txt').write_text('\n'.join(sorted(vocab)), encoding='utf-8')
print(f'vocab: {len(vocab)} tokens')
"
```

2. Read `graphify-out/.vocab.txt`. Then for the user's question, select **up to 12 tokens from this exact list** that semantically match the query intent. Hard constraints:
   - You MUST pick only tokens present in the vocabulary file. Do NOT invent tokens.
   - If a query concept has no plausible token in the vocab, skip it — do not substitute a near-synonym from training memory.
   - If **no** vocab tokens match the query at all, output an empty list and tell the user the corpus has no relevant vocabulary for this question. Do not fabricate a search.
   - Translate cross-language: Russian "аутентификация" → look for `auth`, `credential`, `token`, `security` IFF present in vocab.
   - Morphology: "handlers" maps to `handler` IFF present; "todos" maps to `todo` IFF present.

3. Print the selection explicitly to the user before running the query, so the expansion is auditable:
```
Query expanded to (from graph vocab, N tokens): [token1, token2, ...]
```
If the list is empty, say so plainly and stop — do not proceed to traversal.

### Step 1 — Traversal

Build the **expanded query string** by joining the selected tokens with spaces. Use this string as `QUESTION` below — NOT the original user question. (The original question is preserved only for `save-result` at the end.)

Prefer the CLI when it is installed:
```bash
graphify query "QUESTION"
# or: graphify query "QUESTION" --dfs --budget 3000
```

If the CLI is unavailable, load `graphify-out/graph.json` and run the traversal inline:

1. Find the 1-3 nodes whose label best matches the expanded tokens.
2. Run the appropriate traversal from each starting node.
3. Read the subgraph - node labels, edge relations, confidence tags, source locations.
4. Answer using **only** what the graph contains. Quote `source_location` when citing a specific fact.
5. If the graph lacks enough information, say so - do not hallucinate edges.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
G = json_graph.node_link_graph(data, edges='links')

question = 'QUESTION'
mode = 'MODE'  # 'bfs' or 'dfs'
terms = [t.lower() for t in question.split() if len(t) >= 3]  # match the vocab threshold; keeps api/jwt/ios (#1392)

# Find best-matching start nodes
scored = []
for nid, ndata in G.nodes(data=True):
    label = ndata.get('label', '').lower()
    score = sum(1 for t in terms if t in label)
    if score > 0:
        scored.append((score, nid))
scored.sort(reverse=True)
start_nodes = [nid for _, nid in scored[:3]]

if not start_nodes:
    print('No matching nodes found for query terms:', terms)
    sys.exit(0)

subgraph_nodes = set()
subgraph_edges = []

if mode == 'dfs':
    # DFS: follow one path as deep as possible before backtracking.
    # Depth-limited to 6 to avoid traversing the whole graph.
    visited = set()
    stack = [(n, 0) for n in reversed(start_nodes)]
    while stack:
        node, depth = stack.pop()
        if node in visited or depth > 6:
            continue
        visited.add(node)
        subgraph_nodes.add(node)
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                stack.append((neighbor, depth + 1))
                subgraph_edges.append((node, neighbor))
else:
    # BFS: explore all neighbors layer by layer up to depth 3.
    frontier = set(start_nodes)
    subgraph_nodes = set(start_nodes)
    for _ in range(3):
        next_frontier = set()
        for n in frontier:
            for neighbor in G.neighbors(n):
                if neighbor not in subgraph_nodes:
                    next_frontier.add(neighbor)
                    subgraph_edges.append((n, neighbor))
        subgraph_nodes.update(next_frontier)
        frontier = next_frontier

# Token-budget aware output: rank by relevance, cut at budget (~4 chars/token)
token_budget = BUDGET  # default 2000
char_budget = token_budget * 4

# Score each node by term overlap for ranked output
def relevance(nid):
    label = G.nodes[nid].get('label', '').lower()
    return sum(1 for t in terms if t in label)

ranked_nodes = sorted(subgraph_nodes, key=relevance, reverse=True)

lines = [f'Traversal: {mode.upper()} | Start: {[G.nodes[n].get(\"label\",n) for n in start_nodes]} | {len(subgraph_nodes)} nodes']
for nid in ranked_nodes:
    d = G.nodes[nid]
    lines.append(f'  NODE {d.get(\"label\", nid)} [src={d.get(\"source_file\",\"\")} loc={d.get(\"source_location\",\"\")}]')
for u, v in subgraph_edges:
    if u in subgraph_nodes and v in subgraph_nodes:
        _raw = G[u][v]; d = next(iter(_raw.values()), {}) if isinstance(G, nx.MultiGraph) else _raw
        lines.append(f'  EDGE {G.nodes[u].get(\"label\",u)} --{d.get(\"relation\",\"\")} [{d.get(\"confidence\",\"\")}]--> {G.nodes[v].get(\"label\",v)}')

output = '\n'.join(lines)
if len(output) > char_budget:
    output = output[:char_budget] + f'\n... (truncated at ~{token_budget} token budget - use --budget N for more)'
print(output)
"
```

Replace `QUESTION` with the **expanded** query string, `MODE` with `bfs` or `dfs`, and `BUDGET` with the token budget (default `2000`, or whatever `--budget N` specifies). Then answer based on the subgraph output above, using only what the graph contains.

After writing the answer, save it back into the graph so it improves future queries. Include the expanded tokens inside the `--answer` text (e.g. `"Expanded from original query via vocab: [tokens]. Then traversed..."`) so the next `--update` extracts the expansion history as a graph node:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "ORIGINAL_QUESTION" --answer "ANSWER" --type query --nodes NODE1 NODE2
```

Replace `ORIGINAL_QUESTION` with the user's verbatim question, `ANSWER` with your full answer text (containing the expanded-token trace), `NODE1 NODE2` with the list of node labels you cited. This closes the feedback loop: the next `--update` will extract this Q&A as a node in the graph.

**Work memory (self-improving loop).** Add an `--outcome` so future sessions learn from this one — append `--outcome useful|dead_end|corrected` to the `save-result` command (and `--correction "the right answer"` when correcting):

- `useful` — the cited nodes answered the question well (they become *preferred sources*).
- `dead_end` — the question/path led nowhere; don't re-derive it next time.
- `corrected` — the saved answer was wrong; `--correction` records what was right.

At the **start** of graph work, refresh and read the lessons: run `graphify reflect --if-stale` (cheap, deterministic, no LLM; `--if-stale` makes it a no-op when `LESSONS.md` is already newer than every input, e.g. when the git hook just refreshed it), then read `graphify-out/reflections/LESSONS.md`. It lists **preferred sources** (start there), **known dead ends** (skip them), and prior **corrections**. Running `reflect` yourself keeps the lessons current even without the git hook installed; if the post-commit hook *is* installed, `--if-stale` means your session-start run costs almost nothing.

---

## For /graphify path

Find the shortest path between two named concepts in the graph. Prefer the CLI when installed:

```bash
graphify path "NODE_A" "NODE_B"
```

If the CLI is unavailable, run it inline:

```bash
$(cat graphify-out/.graphify_python) -c "
import json, sys
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
G = json_graph.node_link_graph(data, edges='links')

a_term = 'NODE_A'
b_term = 'NODE_B'

def find_node(term):
    term = term.lower()
    scored = sorted(
        [(sum(1 for w in term.split() if w in G.nodes[n].get('label','').lower()), n)
         for n in G.nodes()],
        reverse=True
    )
    return scored[0][1] if scored and scored[0][0] > 0 else None

src = find_node(a_term)
tgt = find_node(b_term)

if not src or not tgt:
    print(f'Could not find nodes matching: {a_term!r} or {b_term!r}')
    sys.exit(0)

try:
    path = nx.shortest_path(G, src, tgt)
    print(f'Shortest path ({len(path)-1} hops):')
    for i, nid in enumerate(path):
        label = G.nodes[nid].get('label', nid)
        if i < len(path) - 1:
            _raw = G[nid][path[i+1]]; edge = next(iter(_raw.values()), {}) if isinstance(G, nx.MultiGraph) else _raw
            rel = edge.get('relation', '')
            conf = edge.get('confidence', '')
            print(f'  {label} --{rel}--> [{conf}]')
        else:
            print(f'  {label}')
except nx.NetworkXNoPath:
    print(f'No path found between {a_term!r} and {b_term!r}')
except nx.NodeNotFound as e:
    print(f'Node not found: {e}')
"
```

Replace `NODE_A` and `NODE_B` with the actual concept names from the user. Then explain the path in plain language - what each hop means, why it's significant.

After writing the explanation, save it back:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "Path from NODE_A to NODE_B" --answer "ANSWER" --type path_query --nodes NODE_A NODE_B
```

---

## For /graphify explain

Give a plain-language explanation of a single node - everything connected to it. Prefer the CLI when installed:

```bash
graphify explain "NODE_NAME"
```

If the CLI is unavailable, run it inline:

```bash
$(cat graphify-out/.graphify_python) -c "
import json, sys
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
G = json_graph.node_link_graph(data, edges='links')

term = 'NODE_NAME'
term_lower = term.lower()

# Find best matching node
scored = sorted(
    [(sum(1 for w in term_lower.split() if w in G.nodes[n].get('label','').lower()), n)
     for n in G.nodes()],
    reverse=True
)
if not scored or scored[0][0] == 0:
    print(f'No node matching {term!r}')
    sys.exit(0)

nid = scored[0][1]
data_n = G.nodes[nid]
print(f'NODE: {data_n.get(\"label\", nid)}')
print(f'  source: {data_n.get(\"source_file\",\"unknown\")}')
print(f'  type: {data_n.get(\"file_type\",\"unknown\")}')
print(f'  degree: {G.degree(nid)}')
print()
print('CONNECTIONS:')
for neighbor in G.neighbors(nid):
    _raw = G[nid][neighbor]; edge = next(iter(_raw.values()), {}) if isinstance(G, nx.MultiGraph) else _raw
    nlabel = G.nodes[neighbor].get('label', neighbor)
    rel = edge.get('relation', '')
    conf = edge.get('confidence', '')
    src_file = G.nodes[neighbor].get('source_file', '')
    print(f'  --{rel}--> {nlabel} [{conf}] ({src_file})')
"
```

Replace `NODE_NAME` with the concept the user asked about. Then write a 3-5 sentence explanation of what this node is, what it connects to, and why those connections are significant. Use the source locations as citations.

After writing the explanation, save it back:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "Explain NODE_NAME" --answer "ANSWER" --type explain --nodes NODE_NAME
```
True
## Subagent dispatch requires multi-agent support

Add to your Codex config (`~/.codex/config.toml`):

```toml
[features]
multi_agent = true
```

This enables the multi-agent tools that skills like
`dispatching-parallel-agents` and `subagent-driven-development` use.
Which tools you get depends on the multi-agent version your model
preset selects (current presets run V2; older ones run V1). Trust your
actual tool list over any table — including this one — when they
disagree.

- **Spawning:** give children a clean context with
  `spawn_agent {fork_turns: "none"}`; the default `"all"` copies your
  entire transcript into the child. On Codex 0.145+, role files under
  `~/.codex/agents/` attach to isolated forks via `agent_type`.
  Full-history forks accept `model` and `reasoning_effort` overrides
  (only `agent_type` is refused there) — isolated forks are the SDD
  default for context hygiene, not because overrides require them.
- **Fix rounds:** resume the implementer with `followup_task` — it
  delivers your message, triggers a turn, and transparently reloads a
  child the harness evicted. Never dispatch a fresh implementer on the
  theory that a spawned agent cannot be messaged again; on V2 it
  always can.
- **Lifecycle:** V2 has no `close_agent`. Finished children are
  evicted automatically when slots are needed; leaving them unclosed
  costs nothing. Only V1 sessions have `close_agent` — there, close
  reviewers when their review returns, and close each implementer
  after its task's review passes.
- **Model names:** never copy a model name from a skill, table, or old
  session into `spawn_agent` without checking it against your current
  spawn allowlist — V2 accepts only V2-capable presets and hard-errors
  on the rest.

## Waiting on children

`wait_agent` is an event subscription, not a poll: a long wait wakes
the moment a child produces mailbox activity, with the same latency as
a short one. Short-timeout polling buys nothing and costs a tool call —
and a context rebill — per poll. In measured sessions, roughly
two-thirds of all wait calls were short polls that timed out.

- While you still have local work, do not wait at all. A completed
  child's final answer is pushed into your mailbox and arrives with
  your next turn.
- When you are genuinely idle with children outstanding, wait in
  bounded stretches: `wait_agent` with `timeout_ms` 300000-600000
  (5-10 minutes). After each stretch — wake or timeout — post one
  status line, run `list_agents`, and chase any child that finished
  without reporting. Never stack polls shorter than five minutes; the
  event subscription wakes a bounded stretch just as fast as a short
  one.
- Completion mail cannot wake an idle controller (it is delivered
  without triggering a turn); covering that idle window is
  `wait_agent`'s only job. A stretch that times out with no activity
  is your cue to reconcile, not to shorten the next stretch.

## Model routing on spawns

Every `spawn_agent` you issue — including when you are yourself a
spawned child running a fan-out — sets `model` AND `reasoning_effort`
explicitly, per the Model Selection rules of the skill you are
executing. Setting `model` alone is a trap: the child's effort
silently resets to that model's default, not to yours.

Ask your human partner to add a machine-level backstop to
`~/.codex/config.toml` so any spawn that slips through still routes to
a deliberate tier instead of silently inheriting the session's most
expensive model:

```toml
[agents]
default_subagent_model = "<a mid-tier model from your spawn allowlist>"
default_subagent_reasoning_effort = "medium"
```

## Environment Detection

Skills that create worktrees or finish branches should detect their
environment with read-only git commands before proceeding:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree (skip creation)
- `BRANCH` empty → detached HEAD (cannot branch/push/PR from sandbox)

See `using-git-worktrees` Step 0 and `finishing-a-development-branch`
Step 1 for how each skill uses these signals.

## Codex App Finishing

When the sandbox blocks branch/push operations (detached HEAD in an
externally managed worktree), the agent commits all work and informs
the user to use the App's native controls:

- **"Create branch"** — names the branch, then commit/push/PR via App UI
- **"Hand off to local"** — transfers work to the user's local checkout

The agent can still run tests, stage files, and output suggested branch
names, commit messages, and PR descriptions for the user to copy.

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'graphify explain auto_map_entry_subtopic; graphify path auto_map_entry_subtopic score_topic_for_material; Get-Content docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py; Get-Content scripts/motor_puro.py; Get-Content scripts/ablacao_rapida.py'[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command "@'
from pathlib import Path
for f in ['codigo_sem_puro_b.log','codigo_determ2_puro_b.log','codigo_com_puro_b.log','codigo_com_puro_vocabantigo.log','errados_determ_vocabnovo.txt']:
 p=Path('docs/reports/_harness-2026-09-04/c1-3')/f
 print('\\nFILE',p)
 for i,l in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if not ('[DEBUG]' in l or 'INFO' in l): print(f'{i}: {l}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[31m exited 1 in 320ms:[0m

FILE docs\reports\_harness-2026-09-04\c1-3\codigo_sem_puro_b.log
1:   [codigo:sem] Metodos-Formais-Tutor: 0 resumos
2:   [nu] MF: 9 pinos zerados (vocab LLM mantido)
3:   [codigo:sem] Sistemas-Operacionais-Tutor: 0 resumos
4:   [nu] SO: 0 pinos zerados (vocab LLM mantido)
5:   [codigo:sem] Inteligencia-Artifical-Tutor: 0 resumos
6:   [nu] IA: 1 pinos zerados (vocab LLM mantido)
7:   [codigo:sem] Engenharia-Software-2-Tutor: 0 resumos
8:   [nu] ES2: 0 pinos zerados (vocab LLM mantido)
9:   [codigo:sem] TCC-Tutor: 0 resumos
10:   [nu] TCC: 0 pinos zerados (vocab LLM mantido)
11: [profile] Metodos-Formais-Tutor: perfil 'Metodos-Formais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
12: [ok] Metodos-Formais-Tutor: bloco 62/66 -> 62/66 (backup: manifest.json.bak)
13: [profile] Sistemas-Operacionais-Tutor: perfil 'Sistemas Operacionais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
14: [ok] Sistemas-Operacionais-Tutor: bloco 35/39 -> 35/39 (backup: manifest.json.bak)
15: [profile] Inteligencia-Artifical-Tutor: perfil 'Inteligencia Artificial' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
16: [ok] Inteligencia-Artifical-Tutor: bloco 55/59 -> 55/59 (backup: manifest.json.bak)
17: [profile] Engenharia-Software-2-Tutor: perfil 'Engenharia de Software II' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
18: [ok] Engenharia-Software-2-Tutor: bloco 34/35 -> 34/35 (backup: manifest.json.bak)
19: [profile] TCC-Tutor: perfil 'Teoria da Computabilidade e Complexidade' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
20: [ok] TCC-Tutor: bloco 26/27 -> 26/27 (backup: manifest.json.bak)
21: reprocess x5 sem voter: 327s
22: 
23: === EIXOS � motor puro (sem curadoria, sem LLM voter, COM vocab compilado) ===
24: curso      BLOCO conf-err   UNIDADE   COBERTURA    F1 pinos
25: MF      57/66           1   65/65         11/13 0.846     0
26: SO      36/38           0   30/37         19/19 1.000     0
27:        unidade errada: 0704-laminas-comunicacao-e-sincronizacao, 0904-laminas-semaforos, laminas-cs-4244-internet-programming-sockets-programming, laminas-sockets-material-alternativo-em-pt, lista-exercicios-p1, lista-exercicios-p1-gabarito, 0704-exemplo-threads-em-java
28: IA      41/42           0   39/42           1/3 0.333     0
29:        unidade errada: ia-respons�vel-7c4626, o-que-�-intelig�ncia-artificial-ia-oracle-brasil-43437f, visao-geral-introducao-e-historico
30: ES2     27/28           0   28/28         19/19 1.000     0
31: TCC     24/25           0   18/18           3/3 1.000     0
32: LR                  (sem gold � fora da regua)
33: FR                  (sem gold � fora da regua)
34: -------------------------------------------------------
35: TOTAL  bloco 185/199 (93.0%) conf-err 1 | unidade 180/190 (94.7%) | cobertura 53/57 F1 0.930 sem-pred 0 | pinos 0
36: metodos temporais: {'janela-1': 120, 'disamb': 53, 'prep-prova': 11, 'titulo-topico': 10, 'irmao-card': 8, 'ref-generica': 5, 'meta-generica': 4, 'disamb-curto': 4, 'secao-geral': 3, 'due-contain': 2, 'due-straddle': 1}
37: 
38: SUBUNIDADE motor puro (COM vocab compilado): 122/151 com-extras � 103/151 primario
39: total: 330s

FILE docs\reports\_harness-2026-09-04\c1-3\codigo_determ2_puro_b.log
1:   [codigo:determ] Metodos-Formais-Tutor: 19 resumos
2:   [nu] MF: 9 pinos zerados (vocab LLM mantido)
3:   [codigo:determ] Sistemas-Operacionais-Tutor: 8 resumos
4:   [nu] SO: 0 pinos zerados (vocab LLM mantido)
5:   [codigo:determ] Inteligencia-Artifical-Tutor: 29 resumos
6:   [nu] IA: 1 pinos zerados (vocab LLM mantido)
7:   [codigo:determ] Engenharia-Software-2-Tutor: 8 resumos
8:   [nu] ES2: 0 pinos zerados (vocab LLM mantido)
9:   [codigo:determ] TCC-Tutor: 0 resumos
10:   [nu] TCC: 0 pinos zerados (vocab LLM mantido)
11: [profile] Metodos-Formais-Tutor: perfil 'Metodos-Formais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
12: [ok] Metodos-Formais-Tutor: bloco 62/66 -> 62/66 (backup: manifest.json.bak)
13: [profile] Sistemas-Operacionais-Tutor: perfil 'Sistemas Operacionais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
14: [ok] Sistemas-Operacionais-Tutor: bloco 35/39 -> 35/39 (backup: manifest.json.bak)
15: [profile] Inteligencia-Artifical-Tutor: perfil 'Inteligencia Artificial' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
16: [ok] Inteligencia-Artifical-Tutor: bloco 55/59 -> 55/59 (backup: manifest.json.bak)
17: [profile] Engenharia-Software-2-Tutor: perfil 'Engenharia de Software II' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
18: [ok] Engenharia-Software-2-Tutor: bloco 34/35 -> 34/35 (backup: manifest.json.bak)
19: [profile] TCC-Tutor: perfil 'Teoria da Computabilidade e Complexidade' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
20: [ok] TCC-Tutor: bloco 26/27 -> 26/27 (backup: manifest.json.bak)
21: reprocess x5 sem voter: 283s
22: 
23: === EIXOS � motor puro (sem curadoria, sem LLM voter, COM vocab compilado) ===
24: curso      BLOCO conf-err   UNIDADE   COBERTURA    F1 pinos
25: MF      57/66           1   65/65         11/13 0.846     0
26: SO      36/38           0   30/37         19/19 1.000     0
27:        unidade errada: 0704-laminas-comunicacao-e-sincronizacao, 0904-laminas-semaforos, laminas-cs-4244-internet-programming-sockets-programming, laminas-sockets-material-alternativo-em-pt, lista-exercicios-p1, lista-exercicios-p1-gabarito, 0704-exemplo-threads-em-java
28: IA      41/42           0   39/42           1/3 0.333     0
29:        unidade errada: ia-respons�vel-7c4626, o-que-�-intelig�ncia-artificial-ia-oracle-brasil-43437f, visao-geral-introducao-e-historico
30: ES2     27/28           0   28/28         19/19 1.000     0
31: TCC     24/25           0   18/18           3/3 1.000     0
32: LR                  (sem gold � fora da regua)
33: FR                  (sem gold � fora da regua)
34: -------------------------------------------------------
35: TOTAL  bloco 185/199 (93.0%) conf-err 1 | unidade 180/190 (94.7%) | cobertura 53/57 F1 0.930 sem-pred 0 | pinos 0
36: metodos temporais: {'janela-1': 120, 'disamb': 53, 'prep-prova': 11, 'titulo-topico': 10, 'irmao-card': 8, 'ref-generica': 5, 'meta-generica': 4, 'disamb-curto': 4, 'secao-geral': 3, 'due-contain': 2, 'due-straddle': 1}
37: 
38: SUBUNIDADE motor puro (COM vocab compilado): 124/151 com-extras � 105/151 primario
39: total: 285s

FILE docs\reports\_harness-2026-09-04\c1-3\codigo_com_puro_b.log
1:   [codigo:com] Metodos-Formais-Tutor: resumos originais mantidos
2:   [nu] MF: 9 pinos zerados (vocab LLM mantido)
3:   [codigo:com] Sistemas-Operacionais-Tutor: resumos originais mantidos
4:   [nu] SO: 0 pinos zerados (vocab LLM mantido)
5:   [codigo:com] Inteligencia-Artifical-Tutor: resumos originais mantidos
6:   [nu] IA: 1 pinos zerados (vocab LLM mantido)
7:   [codigo:com] Engenharia-Software-2-Tutor: resumos originais mantidos
8:   [nu] ES2: 0 pinos zerados (vocab LLM mantido)
9:   [codigo:com] TCC-Tutor: resumos originais mantidos
10:   [nu] TCC: 0 pinos zerados (vocab LLM mantido)
11: [profile] Metodos-Formais-Tutor: perfil 'Metodos-Formais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
12: [ok] Metodos-Formais-Tutor: bloco 62/66 -> 62/66 (backup: manifest.json.bak)
13: [profile] Sistemas-Operacionais-Tutor: perfil 'Sistemas Operacionais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
14: [ok] Sistemas-Operacionais-Tutor: bloco 35/39 -> 35/39 (backup: manifest.json.bak)
15: [profile] Inteligencia-Artifical-Tutor: perfil 'Inteligencia Artificial' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
16: [ok] Inteligencia-Artifical-Tutor: bloco 55/59 -> 55/59 (backup: manifest.json.bak)
17: [profile] Engenharia-Software-2-Tutor: perfil 'Engenharia de Software II' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
18: [ok] Engenharia-Software-2-Tutor: bloco 34/35 -> 34/35 (backup: manifest.json.bak)
19: [profile] TCC-Tutor: perfil 'Teoria da Computabilidade e Complexidade' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
20: [ok] TCC-Tutor: bloco 26/27 -> 26/27 (backup: manifest.json.bak)
21: reprocess x5 sem voter: 318s
22: 
23: === EIXOS � motor puro (sem curadoria, sem LLM voter, COM vocab compilado) ===
24: curso      BLOCO conf-err   UNIDADE   COBERTURA    F1 pinos
25: MF      57/66           1   65/65         11/13 0.846     0
26: SO      36/38           0   30/37         19/19 1.000     0
27:        unidade errada: 0704-laminas-comunicacao-e-sincronizacao, 0904-laminas-semaforos, laminas-cs-4244-internet-programming-sockets-programming, laminas-sockets-material-alternativo-em-pt, lista-exercicios-p1, lista-exercicios-p1-gabarito, 0704-exemplo-threads-em-java
28: IA      41/42           0   39/42           1/3 0.333     0
29:        unidade errada: ia-respons�vel-7c4626, o-que-�-intelig�ncia-artificial-ia-oracle-brasil-43437f, visao-geral-introducao-e-historico
30: ES2     27/28           0   28/28         19/19 1.000     0
31: TCC     24/25           0   18/18           3/3 1.000     0
32: LR                  (sem gold � fora da regua)
33: FR                  (sem gold � fora da regua)
34: -------------------------------------------------------
35: TOTAL  bloco 185/199 (93.0%) conf-err 1 | unidade 180/190 (94.7%) | cobertura 53/57 F1 0.930 sem-pred 0 | pinos 0
36: metodos temporais: {'janela-1': 120, 'disamb': 53, 'prep-prova': 11, 'titulo-topico': 10, 'irmao-card': 8, 'ref-generica': 5, 'meta-generica': 4, 'disamb-curto': 4, 'secao-geral': 3, 'due-contain': 2, 'due-straddle': 1}
37: 
38: SUBUNIDADE motor puro (COM vocab compilado): 128/151 com-extras � 105/151 primario
39: total: 319s

FILE docs\reports\_harness-2026-09-04\c1-3\codigo_com_puro_vocabantigo.log
1:   [codigo:com] Metodos-Formais-Tutor: resumos originais mantidos
2:   [nu] MF: 9 pinos zerados (vocab LLM mantido)
3:   [vocab:antigo] Sistemas-Operacionais-Tutor: .llm.json removido da copia
4:   [codigo:com] Sistemas-Operacionais-Tutor: resumos originais mantidos
5:   [nu] SO: 0 pinos zerados (vocab LLM mantido)
6:   [vocab:antigo] Inteligencia-Artifical-Tutor: .llm.json removido da copia
7:   [codigo:com] Inteligencia-Artifical-Tutor: resumos originais mantidos
8:   [nu] IA: 1 pinos zerados (vocab LLM mantido)
9:   [vocab:antigo] Engenharia-Software-2-Tutor: .llm.json removido da copia
10:   [codigo:com] Engenharia-Software-2-Tutor: resumos originais mantidos
11:   [nu] ES2: 0 pinos zerados (vocab LLM mantido)
12:   [vocab:antigo] TCC-Tutor: .llm.json removido da copia
13:   [codigo:com] TCC-Tutor: resumos originais mantidos
14:   [nu] TCC: 0 pinos zerados (vocab LLM mantido)
15: [profile] Metodos-Formais-Tutor: perfil 'Metodos-Formais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
16: [ok] Metodos-Formais-Tutor: bloco 62/66 -> 62/66 (backup: manifest.json.bak)
17: [profile] Sistemas-Operacionais-Tutor: perfil 'Sistemas Operacionais' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
18: [ok] Sistemas-Operacionais-Tutor: bloco 35/39 -> 35/39 (backup: manifest.json.bak)
19: [profile] Inteligencia-Artifical-Tutor: perfil 'Inteligencia Artificial' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
20: [ok] Inteligencia-Artifical-Tutor: bloco 55/59 -> 55/59 (backup: manifest.json.bak)
21: [profile] Engenharia-Software-2-Tutor: perfil 'Engenharia de Software II' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
22: [ok] Engenharia-Software-2-Tutor: bloco 34/35 -> 34/35 (backup: manifest.json.bak)
23: [profile] TCC-Tutor: perfil 'Teoria da Computabilidade e Complexidade' aplicado (feature_flags={'use_anchor_engine': True, 'use_llm_voter': True, 'compile_vocabulary': True})
24: [ok] TCC-Tutor: bloco 26/27 -> 26/27 (backup: manifest.json.bak)
25: reprocess x5 sem voter: 268s
26: 
27: === EIXOS � motor puro (sem curadoria, sem LLM voter, COM vocab compilado) ===
28: curso      BLOCO conf-err   UNIDADE   COBERTURA    F1 pinos
29: MF      57/66           1   65/65         11/13 0.846     0
30: SO      36/38           0   32/37         19/19 1.000     0
31:        unidade errada: 0704-laminas-comunicacao-e-sincronizacao, 0904-laminas-semaforos, laminas-cs-4244-internet-programming-sockets-programming, laminas-sockets-material-alternativo-em-pt, 0704-exemplo-threads-em-java
32: IA      41/42           0   39/42           1/3 0.333     0
33:        unidade errada: ia-respons�vel-7c4626, o-que-�-intelig�ncia-artificial-ia-oracle-brasil-43437f, visao-geral-introducao-e-historico
34: ES2     27/28           0   25/28         19/19 1.000     0
35:        unidade errada: microsservicos4, roteiro4-circuitbreaker, roteiro4
36: TCC     24/25           0   18/18           3/3 1.000     0
37: LR                  (sem gold � fora da regua)
38: FR                  (sem gold � fora da regua)
39: -------------------------------------------------------
40: TOTAL  bloco 185/199 (93.0%) conf-err 1 | unidade 179/190 (94.2%) | cobertura 53/57 F1 0.930 sem-pred 0 | pinos 0
41: metodos temporais: {'janela-1': 118, 'disamb': 54, 'titulo-topico': 11, 'prep-prova': 11, 'irmao-card': 8, 'ref-generica': 5, 'meta-generica': 4, 'disamb-curto': 4, 'secao-geral': 3, 'due-contain': 2, 'due-straddle': 1}
42: 
43: SUBUNIDADE motor puro (COM vocab compilado): 76/151 com-extras � 56/151 primario
44: total: 271s
45: subunidade por curso, estado COM resumos, VOCAB ANTIGO (sem .llm.json em SO/IA/ES2/TCC):
46: MF    51/58  primario 34
47: SO     8/15  primario 8
48: IA     4/39  primario 4
49: ES2    5/28  primario 4
50: TCC    8/11  primario 6
51: errados (id -> pred | gold):
52:   MF   archive-of-formal-proofs-355fb8                  -> abordagens-para-verificacao-fo | provadores-de-teoremas
53:   MF   exemplos                                         -> exemplos-de-aplicacoes         | provadores-de-teoremas
54:   MF   invariantes                                      -> verificacao-de-programas       | invariante-e-variante-de-laco
55:   MF   terminacao                                       -> verificacao-de-programas       | correcao-parcial-e-total
56:   MF   tiposindutivos                                   -> verificacao-de-programas       | softwares-de-suporte-a-verific
57:   MF   exemplos-zip                                     ->                                | softwares-de-suporte-a-verific
58:   MF   classes-parte2                                   -> correcao-parcial-e-total       | verificacao-de-programas
59:   SO   definicao-e-historico                            -> chamadas-de-sistema            | evolucao-historica
60:   SO   1903-estruturas-de-controle                      -> escalonamento                  | conceitos-basicos
61:   SO   2603-algoritmos-de-escalonamento                 -> escalonamento                  | algoritmos-de-escalonamento
62:   SO   3103-threads                                     -> escalonamento                  | conceitos-basicos
63:   SO   exercicios                                       ->                                | algoritmos-de-escalonamento
64:   SO   exemplo-threads-em-c-exemplo1                    ->                                | conceitos-basicos
65:   SO   exemplo-threads-em-c-exemplo2                    -> escalonamento                  | conceitos-basicos
66:   IA   algoritmo-de-classificacao-k-nn                  -> introducao-ao-aprendizado-de-m | modelos-preditivos
67:   IA   exemplo-com-k-nn                                 -> introducao-ao-aprendizado-de-m | modelos-preditivos
68:   IA   exemplo-2-k-nn-com-iriscsv-mais-completo         -> introducao-ao-aprendizado-de-m | modelos-preditivos
69:   IA   exemplo-de-programa-com-k-nn-em-java             -> introducao-ao-aprendizado-de-m | modelos-preditivos
70:   IA   artigo-usando-k-nn-em-texto                      -> introducao-ao-aprendizado-de-m | modelos-preditivos
71:   IA   k-nn-para-classificacao-exemplo-cardio           -> introducao-ao-aprendizado-de-m | modelos-preditivos
72:   IA   k-nn-para-regressao-exemplo-imc                  -> introducao-ao-aprendizado-de-m | modelos-preditivos
73:   IA   introducao-a-redes-neurais                       -> introducao-ao-aprendizado-de-m | modelos-preditivos
74:   IA   rede-perceptron                                  -> introducao-ao-aprendizado-de-m | modelos-preditivos
75:   IA   rede-perceptron-classificacao-de-cliente         -> introducao-ao-aprendizado-de-m | modelos-preditivos
76:   IA   rede-perceptron-classificacao-planta-iris        -> introducao-ao-aprendizado-de-m | modelos-preditivos
77:   IA   rede-perceptron-exemplo-atualizado               -> introducao-ao-aprendizado-de-m | modelos-preditivos
78:   IA   rede-perceptron-or-em-python                     -> introducao-ao-aprendizado-de-m | modelos-preditivos
79:   IA   rede-perceptron-reconhecendo-letras              -> introducao-ao-aprendizado-de-m | modelos-preditivos
80:   IA   exercicio-2-solucao-com-rede-perceptron-atualiza -> introducao-ao-aprendizado-de-m | modelos-preditivos
81:   IA   mlp                                              -> introducao-ao-aprendizado-de-m | modelos-preditivos
82:   IA   mlp-xoripynb                                     -> introducao-ao-aprendizado-de-m | modelos-preditivos
83:   IA   mlp-classificacao-iris-atualizado                -> introducao-ao-aprendizado-de-m | modelos-preditivos
84:   IA   mlp-regressao-cardio                             -> introducao-ao-aprendizado-de-m | modelos-preditivos
85:   IA   rede-perceptron-e-equacao-de-reta                -> introducao-ao-aprendizado-de-m | modelos-preditivos
86:   IA   xor-backpropagation-em-python                    -> introducao-ao-aprendizado-de-m | modelos-preditivos
87:   IA   mlp-classificacao-inadimplencia-normalizacao-e-g -> introducao-ao-aprendizado-de-m | modelos-preditivos
88:   IA   como-analisar-resultados-acc-pr-re-e-f1          -> introducao-ao-aprendizado-de-m | metricas-de-avaliacao
89:   IA   arvores-de-decisao                               -> introducao-ao-aprendizado-de-m | modelos-preditivos
90:   IA   exemplo-1-arvores-de-decisao-classificacao-plant -> introducao-ao-aprendizado-de-m | modelos-preditivos
91:   IA   exemplo-2-arvores-de-decisao-regressao-diabetes  -> introducao-ao-aprendizado-de-m | modelos-preditivos
92:   IA   exemplo-complementar-classificacao-com-arvores-d -> introducao-ao-aprendizado-de-m | modelos-preditivos
93:   IA   aula-sobre-agrupamento-parte-1-particional       -> introducao-ao-aprendizado-de-m | modelos-descritivos
94:   IA   agrupamento-usando-k-means-exemplo-1-ipynb       -> introducao-ao-aprendizado-de-m | modelos-descritivos
95:   IA   agrupamento-usando-k-means-exemplo-2-ipynb       -> introducao-ao-aprendizado-de-m | modelos-descritivos
96:   IA   artigo-usando-agrupamento                        -> introducao-ao-aprendizado-de-m | modelos-descritivos
97:   IA   survey-on-clustering                             -> introducao-ao-aprendizado-de-m | modelos-descritivos
98:   IA   aula-sobre-agrupamento-parte-2-hierarquico       -> introducao-ao-aprendizado-de-m | modelos-descritivos
99:   IA   agrupamento-hierarquico-exemplo-1                -> introducao-ao-aprendizado-de-m | modelos-descritivos
100:   IA   agrupamento-hierarquico-exemplo-2-use-o-dataset- -> introducao-ao-aprendizado-de-m | modelos-descritivos
101:   ES2  microsservicos                                   -> arquitetura-serverless         | orientada-a-microsservicos
102:   ES2  roteiro1                                         -> orientada-a-servicos           | estudo-de-caso-arquitetura-ori
103:   ES2  devops                                           -> integracao-continua-ci         | conceito-de-devops
104:   ES2  kubernetes                                       -> estudo-de-caso-integracao-e-im | plataformas-de-devops
105:   ES2  microsservicos5                                  -> gerenciamento-da-configuracao  | plataformas-de-devops
106:   ES2  microsservicos2                                  -> arquitetura-serverless         | estudo-de-caso-arquitetura-ori
107:   ES2  microsservicos3                                  -> arquitetura-serverless         | estudo-de-caso-arquitetura-ori
108:   ES2  microsservicos4                                  -> arquitetura-serverless         | estudo-de-caso-integracao-e-im
109:   ES2  roteiro2-nameserver                              -> arquitetura-serverless         | estudo-de-caso-arquitetura-ori
110:   ES2  roteiro3-gateway                                 -> orientada-a-servicos           | estudo-de-caso-arquitetura-ori
111:   ES2  roteiro4-circuitbreaker                          -> orientada-a-servicos           | estudo-de-caso-integracao-e-im
112:   ES2  roteiro6-conteiners-composicao                   -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
113:   ES2  roteiro2                                         -> orientada-a-servicos           | estudo-de-caso-arquitetura-ori
114:   ES2  roteiro3                                         -> orientada-a-servicos           | estudo-de-caso-arquitetura-ori
115:   ES2  roteiro4                                         -> orientada-a-servicos           | estudo-de-caso-integracao-e-im
116:   ES2  roteiro5                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
117:   ES2  roteiro6                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
118:   ES2  microsservicos6                                  -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
119:   ES2  microsservicos7                                  -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
120:   ES2  roteiro7-filas                                   -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
121:   ES2  roteiro8-autenticacao-autorizacao                -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
122:   ES2  roteiro7                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
123:   ES2  roteiro7-history-service                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im
124:   TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hierar -> conjuntos-enumeraveis          | 
125:   TCC  aula-09-variacoes-de-maquinas-de-turing          -> maquinas-de-turing             | variacoes-de-maquinas-de-turin
Traceback (most recent call last):
  File "<stdin>", line 6, in <module>
  File "C:\Users\Humberto\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u0131' in position 39: character maps to <undefined>

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f in ['docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py','scripts/motor_puro.py','scripts/ablacao_rapida.py','docs/reports/_harness-2026-09-04/c1-3/errados_determ_vocabnovo.txt']:
 print('\\nFILE',f)
 for i,l in enumerate(Path(f).read_text(encoding='utf-8').splitlines(),1): print(f'{i}: {l}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 292ms:[0m

FILE docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py
1: """Camada 3 (resumos de codigo por Gemini) — ablacao e substituto deterministico, nas copias .ablacao, tripwire.
2: Modos: com      = resumos reais do sync (referencia, 11/09)
3:        sem      = code_curation.json vazio (nenhum texto para zips/codigo)
4:        determ   = code_curation.json SINTETICO a partir dos .md que o motor ja gera (base_markdown + extracted_files; v1 lia zip/ipynb cru),
5:                   no MESMO formato do resumo do Gemini (inferred_title / summary / concepts / language): mesma rota, produtor diferente.
6: Alvos: puro (5 cursos, --com-vocab) · auto (5, voter cacheado) · holdout / autoholdout (CG). Uso: shim_codigo.py {sem|determ} {puro|auto|holdout|autoholdout}"""
7: import io
8: import json
9: import os
10: import re
11: import runpy
12: import shutil
13: import sys
14: import zipfile
15: from collections import Counter
16: from pathlib import Path
17: 
18: GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
19: GH = GEN.parent
20: sys.path.insert(0, str(GEN))
21: sys.path.insert(0, str(GEN / "scripts"))
22: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
23: MODE, TARGET = sys.argv[1], sys.argv[2]
24: import src.builder.runtime.gemini_client as _gc  # noqa: E402
25: _gc.get_gemini_client = lambda config=None: None
26: 
27: 
28: def _bloqueado(*a, **k):
29:     raise RuntimeError("Gemini bloqueado (tripwire)")
30: 
31: 
32: _gc.GeminiClient.__init__ = _bloqueado
33: import ablacao_rapida as ab  # noqa: E402
34: import reprocess_assignments as ra  # noqa: E402
35: 
36: _CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|[_\-./\\ ]+")
37: _COMMENT = re.compile(r"^\s*(//|#|\*|/\*|--|\(\*|%|;)\s*(.*)$")
38: _WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9]{3,}")
39: _STOP = {"return", "import", "include", "public", "private", "static", "void", "int", "float", "double", "string", "const", "class",
40:          "self", "this", "true", "false", "null", "none", "print", "printf", "main", "args", "argv", "using", "namespace", "from",
41:          "while", "else", "elif", "break", "continue", "define", "ifdef", "endif", "begin", "end", "then", "with", "that", "this"}
42: 
43: 
44: def _texto_do_codigo(raw: str, nome: str) -> tuple:
45:     """(comentarios, identificadores) de um arquivo de codigo."""
46:     coments, ids = [], Counter()
47:     for line in raw.splitlines()[:600]:
48:         m = _COMMENT.match(line)
49:         if m and m.group(2).strip():
50:             coments.append(m.group(2).strip())
51:         for w in _WORD.findall(line):
52:             for part in _CAMEL.split(w):
53:                 p = part.lower()
54:                 if len(p) >= 4 and p not in _STOP and not p.isdigit():
55:                     ids[p] += 1
56:     return coments, ids
57: 
58: 
59: _FRONT = re.compile(r"^---\n.*?\n---\n", re.S)
60: _FENCE = re.compile(r"^```.*$", re.M)
61: _HEAD = re.compile(r"^#{1,6}\s+(.*)$")
62: _CELULA = re.compile(r"^C.lula \d+ . ", re.I)
63: 
64: 
65: def _bundle_md(entry: dict, repo: Path) -> list:
66:     """(titulo_do_arquivo, texto) dos .md que o motor JA gerou para o material — o mesmo bundle de `_build_bundle_text`."""
67:     out = []
68:     bm = entry.get("base_markdown")
69:     if bm and (repo / bm).is_file():
70:         out.append((str(entry.get("title") or ""), (repo / bm).read_text(encoding="utf-8", errors="replace")))
71:     for ef in entry.get("extracted_files") or []:
72:         em = ef.get("base_markdown")
73:         if em and (repo / em).is_file():
74:             out.append((Path(str(ef.get("title") or em)).name, (repo / em).read_text(encoding="utf-8", errors="replace")))
75:     return out
76: 
77: 
78: def _sintetico(entry: dict, repo: Path) -> dict:
79:     """Resumo deterministico no formato do Gemini, a partir dos .md do bundle (v2; v1 lia o zip/ipynb cru)."""
80:     ml = entry.get("moodle_label")
81:     ml = ml.get("text") if isinstance(ml, dict) else ml
82:     nomes, prosa, ids, lang = [], [], Counter(), ""
83:     for nome, md in _bundle_md(entry, repo):
84:         nomes.append(" ".join(p for p in _CAMEL.split(Path(nome).stem) if p))
85:         body = _FRONT.sub("", md, count=1)
86:         m = re.search(r"\*\*Linguagem:\*\*\s*(\w+)", body)
87:         if m and not lang:
88:             lang = m.group(1)
89:         em_codigo = False
90:         for line in body.splitlines()[:800]:
91:             if _FENCE.match(line):
92:                 em_codigo = not em_codigo
93:                 continue
94:             h = _HEAD.match(line)
95:             if h:
96:                 if not _CELULA.match(h.group(1)):
97:                     prosa.append(h.group(1).strip())
98:                 continue
99:             if em_codigo:
100:                 c = _COMMENT.match(line)
101:                 if c and c.group(2).strip():
102:                     prosa.append(c.group(2).strip())
103:                 for w in _WORD.findall(line):
104:                     for part in _CAMEL.split(w):
105:                         q = part.lower()
106:                         if len(q) >= 4 and q not in _STOP and not q.isdigit():
107:                             ids[q] += 1
108:             elif line.strip() and not line.startswith(">") and not line.startswith("|"):
109:                 prosa.append(line.strip())      # prosa de celula markdown do notebook / README
110:     title = f"{ml or entry.get('title') or ''} {' '.join(dict.fromkeys(nomes))}".strip()
111:     return {"summary": {"inferred_title": title[:200], "summary": " ".join(dict.fromkeys(prosa))[:1500],
112:                         "concepts": [w for w, _ in ids.most_common(30)], "language": lang},
113:             "content_hash": "determ", "matcher_version": 0, "model": "determ-v2", "generated_at": "determ"}
114: 
115: 
116: _ablate_orig = ab.ablate
117: 
118: 
119: def _ablate_codigo(repo, keep_llm_vocab=False):
120:     n = _ablate_orig(repo, keep_llm_vocab=True)
121:     repo = Path(repo)
122:     if repo.name in os.environ.get("VOCAB_ANTIGO", "").split(","):   # 11/09: regime "vocab antigo" sem tocar no original
123:         (repo / "course/.glossary_curation.llm.json").unlink(missing_ok=True)
124:         print(f"  [vocab:antigo] {repo.name}: .llm.json removido da copia", flush=True)
125:     src = GH / repo.name / "material_curation.json"
126:     if src.exists():
127:         shutil.copy2(src, repo / "material_curation.json")
128:     if MODE == "com":                      # 11/09: referencia com os resumos reais (code_curation.json do sync), mesma regua
129:         print(f"  [codigo:com] {repo.name}: resumos originais mantidos", flush=True)
130:         return n
131:     man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
132:     if MODE == "sem":
133:         cc = {"version": 1, "entries": {}}
134:     else:
135:         cc = {"version": 1, "entries": {e["id"]: _sintetico(e, repo) for e in man if e.get("category") == "codigo-professor" or e.get("file_type") in ("code", "zip")}}
136:     (repo / "code_curation.json").write_text(json.dumps(cc, ensure_ascii=False, indent=1), encoding="utf-8")
137:     print(f"  [codigo:{MODE}] {repo.name}: {len(cc['entries'])} resumos", flush=True)
138:     return n
139: 
140: 
141: ab.ablate = _ablate_codigo
142: _merge_orig = ra._merge_profile_flags
143: _reprocess_orig = ra.reprocess
144: 
145: 
146: def _reprocess_com_voter(repo, flags, store=None):
147:     ra._merge_profile_flags = _merge_orig
148:     return _reprocess_orig(repo, flags, store)
149: 
150: 
151: if TARGET in ("auto", "autoholdout"):
152:     ra.reprocess = _reprocess_com_voter
153: if TARGET in ("puro", "auto"):
154:     import motor_puro
155:     sys.exit(motor_puro.main(["--com-vocab"]))
156: else:
157:     sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py"), str(GEN), str(GEN / ".ablacao")]
158:     runpy.run_path(sys.argv[0], run_name="__main__")

FILE scripts/motor_puro.py
1: """MOTOR PURO — regua oficial do produto: sem curadoria manual (pinos/cards/
2: glossario) E sem voter LLM, nas copias `.ablacao` dos 5 cursos com gold.
3: READ-ONLY nos originais. Promovido do scratchpad em 02/09 (Fase 0 do plano).
4: 
5:     python scripts/motor_puro.py                # 5 cursos: nu + voter OFF + 3 eixos + subunidade
6:     python scripts/motor_puro.py --com-vocab    # 3a linha: puro + vocabulario compilado por LLM (Fase 1b)
7:                                                 # cache .glossary_curation.llm.json na copia; 1a vez chama a API
8: 
9: Mede: bloco/unidade/cobertura (eval_eixos) + subunidade (subunit_gt_*.csv, com-extras
10: e primario). Regua dupla: nada regride aqui NEM na curada (eval_eixos nos originais).
11: Baseline 01/09d: bloco 158/200 · unidade 154/191 · cobertura 51/57 · subunidade 26/93.
12: """
13: from __future__ import annotations
14: 
15: import argparse
16: import csv
17: import json
18: import os
19: import subprocess
20: import sys
21: import time
22: from pathlib import Path
23: 
24: if hasattr(sys.stdout, "reconfigure"):
25:     sys.stdout.reconfigure(encoding="utf-8", errors="replace")
26: 
27: GEN = Path(__file__).resolve().parents[1]
28: ORIG = GEN.parent
29: COPY = GEN / ".ablacao"
30: sys.path.insert(0, str(GEN))
31: sys.path.insert(0, str(GEN / "scripts"))
32: os.environ["TUTOR_REPOS_ORIG"] = str(ORIG)
33: 
34: import ablacao_rapida as ab  # noqa: E402
35: import reprocess_assignments as ra  # noqa: E402
36: 
37: _orig_merge = ra._merge_profile_flags
38: 
39: 
40: def _merge_sem_voter(options, profile):
41:     _orig_merge(options, profile)
42:     options["use_llm_voter"] = False
43: 
44: 
45: ra._merge_profile_flags = _merge_sem_voter
46: 
47: SIGS = ["MF", "SO", "IA", "ES2", "TCC"]
48: SUBUNIT_GOLD = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
49:                 "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}   # MF aprovado pelo user em 06/09 (CG no holdout_cg.py)
50: 
51: 
52: def main(argv=None) -> int:
53:     ap = argparse.ArgumentParser(description=__doc__)
54:     ap.add_argument("--com-vocab", action="store_true", help="puro + vocabulario compilado por LLM (Fase 1b)")
55:     args = ap.parse_args(argv)
56:     if args.com_vocab:
57:         os.environ.pop("TUTOR_NO_VOCAB_COMPILE", None)
58:     else:
59:         os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"   # motor puro mede SEM vocabulario por definicao
60:     t0 = time.time()
61:     for sig in SIGS:
62:         src, dst = ORIG / ab.REPO[sig], COPY / ab.REPO[sig]
63:         ab.sync(src, dst)
64:         n = ab.ablate(dst, keep_llm_vocab=args.com_vocab)
65:         print(f"  [nu] {sig}: {n} pinos zerados{' (vocab LLM mantido)' if args.com_vocab else ''}", flush=True)
66:     for sig in SIGS:
67:         ra.reprocess(COPY / ab.REPO[sig], [])
68:     print(f"reprocess x{len(SIGS)} sem voter: {time.time() - t0:.0f}s", flush=True)
69: 
70:     env = {**os.environ, "TUTOR_REPOS_DIR": str(COPY), "PYTHONIOENCODING": "utf-8"}
71:     ev = subprocess.run([sys.executable, str(GEN / "scripts/eval_eixos.py")], cwd=str(GEN), env=env,
72:                         capture_output=True, text=True, encoding="utf-8", errors="replace")
73:     modo = "COM vocab compilado" if args.com_vocab else "sem vocab"
74:     print(f"\n=== EIXOS — motor puro (sem curadoria, sem LLM voter, {modo}) ===")
75:     print(ev.stdout)
76: 
77:     tot_ok, tot_n, prim_ok = ab.score_subunit(COPY, SUBUNIT_GOLD, GEN)
78:     print(f"SUBUNIDADE motor puro ({modo}): {tot_ok}/{tot_n} com-extras · {prim_ok}/{tot_n} primario")
79:     print(f"total: {time.time() - t0:.0f}s")
80:     return 0
81: 
82: 
83: if __name__ == "__main__":
84:     raise SystemExit(main())

FILE scripts/ablacao_rapida.py
1: """Ablacao "motor nu" RAPIDA: em COPIA dos repos-tutor, em paralelo, sem tocar os originais.
2: 
3:     python scripts/ablacao_rapida.py                 # nu: zera curadoria nas copias, reprocessa os 5, mede
4:     python scripts/ablacao_rapida.py --curado        # gate: reprocessa as copias SEM ablacao e exige 0 campos vs original
5:     python scripts/ablacao_rapida.py --repos MF,TCC  # subconjunto
6:     python scripts/ablacao_rapida.py --jobs 2        # menos paralelismo (API do LLM reclamando)
7:     python scripts/ablacao_rapida.py --fresh         # apaga as copias antes (senao: sync incremental)
8: 
9: Por que copia: os derivados (.timeline_index etc.) sao ignorados pelo git; restaurar in-place exigia
10: git checkout + reprocess de novo (ciclo duplo, ~12 min). Na copia nao ha o que restaurar.
11: Por que o cache de votos da copia persiste: cada ablacao re-votaria as janelas nuas (custo + ruido).
12: Perfil da disciplina: casado pelo repo ORIGINAL (env TUTOR_REPOS_ORIG, ver reprocess_assignments).
13: """
14: from __future__ import annotations
15: 
16: import argparse
17: import json
18: import os
19: import shutil
20: import subprocess
21: import sys
22: import time
23: from pathlib import Path
24: 
25: GEN = Path(__file__).resolve().parents[1]
26: ORIG = GEN.parent
27: REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
28:         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
29: COPY_DIR = Path(os.environ.get("TUTOR_REPOS_COPY") or (GEN / ".ablacao"))
30: # raw/, staging/ e content/images ficam: sem eles image_curation muda em todos os repos e o MF perde entries (gate 2026-08-26).
31: EXCLUDE_DIRS = (".git", "build", "__pycache__", ".deeptutor")
32: KEEP_IN_COPY = ("material_curation.json",)  # cache de votos nu acumula entre rodadas
33: 
34: 
35: def sync(src: Path, dst: Path) -> None:
36:     dst.mkdir(parents=True, exist_ok=True)
37:     cmd = ["robocopy", str(src), str(dst), "/E", "/XD", *EXCLUDE_DIRS, "/XF", "*.bak", "/XJD", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1"]
38:     for f in KEEP_IN_COPY:
39:         if (dst / f).exists():
40:             cmd += ["/XF", f]
41:     rc = subprocess.run(cmd, capture_output=True, text=True).returncode
42:     if rc >= 8:
43:         raise SystemExit(f"robocopy falhou ({rc}) em {src.name}")
44: 
45: 
46: def ablate(repo: Path, keep_llm_vocab: bool = False) -> int:
47:     """Zera curadoria MANUAL na copia. keep_llm_vocab (motor_puro --com-vocab): o vocabulario
48:     compilado por LLM (`.glossary_curation.llm.json`, produto, nao curadoria) fica; senao e
49:     escondido (`.off`) para a regua "puro" medir SEM vocabulario, e restaurado no modo com."""
50:     m = json.loads((repo / "manifest.json").read_text(encoding="utf-8")); n = 0
51:     for e in m["entries"]:
52:         for k in ("manual_timeline_block_id", "manual_unit_slug", "manual_subunit_slug"):
53:             if e.get(k):
54:                 e[k] = ""; n += 1
55:     (repo / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
56:     cp = repo / "course/.timeline_curation.json"
57:     if cp.exists():
58:         cur = json.loads(cp.read_text(encoding="utf-8"))
59:         cp.write_text(json.dumps({"version": cur.get("version", 1), "blocks": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
60:     cb = repo / "course/.card_block_map.json"
61:     if cb.exists():
62:         d = json.loads(cb.read_text(encoding="utf-8"))
63:         d = {k: v for k, v in d.items() if not (isinstance(v, dict) and v.get("source") == "manual")}
64:         cb.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
65:     sc = repo / "course/.glossary_curation.json"
66:     if sc.exists():
67:         sc.unlink()
68:     llm = repo / "course/.glossary_curation.llm.json"; off = llm.with_name(llm.name + ".off")
69:     if keep_llm_vocab and off.exists():
70:         if llm.exists():
71:             off.unlink()          # sync ja trouxe o do original: o .off e orfao
72:         else:
73:             off.rename(llm)
74:     elif not keep_llm_vocab and llm.exists():
75:         if off.exists():
76:             off.unlink()
77:         llm.rename(off)
78:     return n
79: 
80: 
81: def reprocess_parallel(repos: list[Path], jobs: int) -> None:
82:     env = {**os.environ, "TUTOR_REPOS_ORIG": str(ORIG), "PYTHONIOENCODING": "utf-8", "TUTOR_NO_VOCAB_COMPILE": "1"}
83:     pending = list(repos); running: list[tuple[Path, subprocess.Popen]] = []
84:     while pending or running:
85:         while pending and len(running) < jobs:
86:             r = pending.pop(0)
87:             p = subprocess.Popen([sys.executable, str(GEN / "scripts/reprocess_assignments.py"), str(r)],
88:                                  cwd=str(GEN), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
89:             running.append((r, p))
90:         for r, p in list(running):
91:             if p.poll() is not None:
92:                 out = p.stdout.read() if p.stdout else ""
93:                 ok = [l for l in out.splitlines() if l.startswith("[ok]")]
94:                 bad = [l for l in out.splitlines() if "Traceback" in l or "Error" in l]
95:                 print(f"  {r.name}: {'; '.join(ok) or 'sem [ok]'}{'  !! ' + bad[-1] if bad else ''}", flush=True)
96:                 running.remove((r, p))
97:         time.sleep(0.5)
98: 
99: 
100: def diff_fields(a_path: Path, b_path: Path) -> list[tuple[str, str]]:
101:     a = {e["id"]: e for e in json.loads(a_path.read_text(encoding="utf-8"))["entries"]}
102:     b = {e["id"]: e for e in json.loads(b_path.read_text(encoding="utf-8"))["entries"]}
103:     out = [(k, f) for k in a for f in a[k] if f != "updated_at" and a[k].get(f) != b.get(k, {}).get(f)]
104:     out += [(k, "ENTRY_SUMIU") for k in b if k not in a] + [(k, "ENTRY_NOVA") for k in a if k not in b]
105:     return out
106: 
107: 
108: 
109: def score_subunit(copy: Path, gold: dict, gen: Path) -> tuple:
110:     """(com_extras, n, primario) da subunidade nas copias contra `docs/reports/subunit_gt_<sigla>.csv`
111:     (gold = {sigla: nome do repo}). Mesma conta do motor_puro e do holdout: scorable=yes; alvo = gold + extras."""
112:     import csv
113:     import json
114:     ok = n = prim = 0
115:     for sigla, repo in gold.items():
116:         m = json.loads((copy / repo / "manifest.json").read_text(encoding="utf-8"))
117:         pred = {str(e.get("id")): str(e.get("computed_subunit_slug") or "") for e in m["entries"]}
118:         with open(gen / "docs" / "reports" / f"subunit_gt_{sigla}.csv", encoding="utf-8-sig") as f:
119:             for r in csv.DictReader(f):
120:                 if r["scorable"] != "yes":
121:                     continue
122:                 n += 1
123:                 extras = set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
124:                 alvo = ({r["gold_subunit"]} | extras) if r["gold_subunit"] else {""}
125:                 p = pred.get(r["entry_id"], "(SUMIU)")
126:                 ok += p in alvo
127:                 prim += p == r["gold_subunit"]
128:     return ok, n, prim
129: 
130: def main(argv: list[str]) -> int:
131:     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
132:     ap.add_argument("--curado", action="store_true", help="gate: sem ablacao; copia reprocessada deve == original")
133:     ap.add_argument("--repos", default="MF,SO,IA,ES2,TCC")
134:     ap.add_argument("--jobs", type=int, default=5)
135:     ap.add_argument("--fresh", action="store_true")
136:     ap.add_argument("--no-sync", action="store_true", help="reusa as copias como estao (ex.: so re-medir)")
137:     args = ap.parse_args(argv)
138:     sigs = [s.strip() for s in args.repos.split(",") if s.strip()]
139:     if args.fresh and COPY_DIR.exists():
140:         shutil.rmtree(COPY_DIR)
141:     t0 = time.time()
142:     repos = []
143:     for sig in sigs:
144:         src, dst = ORIG / REPO[sig], COPY_DIR / REPO[sig]
145:         if not args.no_sync:
146:             sync(src, dst)
147:         if not args.curado and not args.no_sync:
148:             n = ablate(dst)
149:             print(f"  [nu] {sig}: {n} pinos zerados; curadoria, cards manuais e sidecar removidos")
150:         repos.append(dst)
151:     print(f"sync+ablacao: {time.time() - t0:.0f}s", flush=True)
152:     t1 = time.time()
153:     reprocess_parallel(repos, args.jobs)
154:     print(f"reprocess x{len(repos)} (jobs={args.jobs}): {time.time() - t1:.0f}s", flush=True)
155:     env = {**os.environ, "TUTOR_REPOS_DIR": str(COPY_DIR), "PYTHONIOENCODING": "utf-8"}
156:     if args.curado:
157:         total = 0
158:         for sig in sigs:
159:             d = diff_fields(COPY_DIR / REPO[sig] / "manifest.json", ORIG / REPO[sig] / "manifest.json")
160:             total += len(d)
161:             print(f"  gate {sig}: {len(d)} campos diferentes vs original {sorted(set(f for _, f in d))[:6]}")
162:         print("GATE:", "OK — copia == original" if total == 0 else f"FALHOU — {total} campos")
163:         return 0 if total == 0 else 1
164:     ev = subprocess.run([sys.executable, str(GEN / "scripts/eval_eixos.py")], cwd=str(GEN), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
165:     print("\n".join(l for l in ev.stdout.splitlines() if l.startswith("TOTAL") or l.startswith("curso") or l[:3].strip() in sigs))
166:     er = subprocess.run([sys.executable, str(GEN / "scripts/erros_motor_nu.py")], cwd=str(GEN), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
167:     print(er.stdout)
168:     print(f"total: {time.time() - t0:.0f}s")
169:     return 0
170: 
171: 
172: if __name__ == "__main__":
173:     raise SystemExit(main(sys.argv[1:]))

FILE docs/reports/_harness-2026-09-04/c1-3/errados_determ_vocabnovo.txt
1: errados no estado DETERM v2, vocab novo (id -> pred | gold [extras]):
2:   MF   archive-of-formal-proofs-355fb8                  -> abordagens-para-verificacao-fo | provadores-de-teoremas 
3:   MF   arvores                                          -> exemplos-de-aplicacoes         | provadores-de-teoremas ['especificacao-de-funcoes-recursivas']
4:   MF   exemplos                                         -> exemplos-de-aplicacoes         | provadores-de-teoremas ['especificacao-de-conjuntos-indutivos', 'especificacao-de-funcoes-recursivas']
5:   MF   intro                                            -> exemplos-de-aplicacoes         | provadores-de-teoremas ['especificacao-de-conjuntos-indutivos', 'especificacao-de-funcoes-recursivas']
6:   MF   listas                                           -> exemplos-de-aplicacoes         | provadores-de-teoremas ['especificacao-de-funcoes-recursivas']
7:   MF   introducao-zip                                   ->                                | softwares-de-suporte-a-verific ['verificacao-de-programas']
8:   MF   terminacao                                       ->                                | correcao-parcial-e-total ['invariante-e-variante-de-laco']
9:   MF   tiposindutivos                                   -> verificacao-de-programas       | softwares-de-suporte-a-verific 
10:   SO   exemplo-criacao-de-processos-no-unix-linux-filho -> estudo-de-casos                | chamadas-de-sistema 
11:   SO   exemplo-criacao-de-processos-no-unix-linux-teste -> estudo-de-casos                | chamadas-de-sistema 
12:   SO   exemplo-criacao-de-processos-no-unix-linux-teste -> estudo-de-casos                | chamadas-de-sistema 
13:   SO   exemplo-criacao-de-processos-no-unix-linux-teste -> estudo-de-casos                | chamadas-de-sistema 
14:   SO   exemplo-threads-em-c-exemplo1                    -> estudo-de-casos                | conceitos-basicos 
15:   SO   exemplo-threads-em-c-exemplo2                    -> estudo-de-casos                | conceitos-basicos 
16:   SO   exemplo-threads-em-c-exemplo3                    -> estudo-de-casos                | conceitos-basicos 
17:   IA   rede-perceptron-or-em-python                     -> introducao-ao-aprendizado-de-m | modelos-preditivos 
18:   IA   mlp-xoripynb                                     ->                                | modelos-preditivos 
19:   IA   aula-sobre-agrupamento-parte-2-hierarquico       -> introducao-ao-aprendizado-de-m | modelos-descritivos 
20:   ES2  kubernetes                                       -> estudo-de-caso-integracao-e-im | plataformas-de-devops 
21:   ES2  microsservicos2                                  -> orientada-a-microsservicos     | estudo-de-caso-arquitetura-ori 
22:   ES2  microsservicos3                                  -> estilos-e-padroes-arquiteturai | estudo-de-caso-arquitetura-ori 
23:   ES2  roteiro4                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im 
24:   ES2  roteiro5                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im 
25:   ES2  roteiro6                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im 
26:   ES2  roteiro7                                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im 
27:   ES2  roteiro7-history-service                         -> gerenciamento-da-configuracao  | estudo-de-caso-integracao-e-im 
28:   TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hierar -> linguagens-reconheciveis-e-dec |  

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
O §4 contém uma conclusão incorreta: **8/15 nos dois regimes não significa os mesmos sete erros**. O log antigo lista outros materiais; também mostra SO caindo de **32 para 30 acertos de unidade** com o vocabulário novo. Vou conferir as trocas por material antes de atribuir a causa.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import json
from pathlib import Path
p=Path('graphify-out/graph.json');d=json.loads(p.read_text(encoding='utf-8'));ns={n['id']:n for n in d['nodes']}
for n in ns.values():
 if n.get('label') in ['auto_map_entry_subtopic','score_topic_for_material']:
  print('NODE',n)
  for e in d.get('links',d.get('edges',[])):
   if n['id'] in [e['source'],e['target']]:print('EDGE',ns.get(e['source'],{}).get('label'),ns.get(e['target'],{}).get('label'),e.get('relation'))
print('COPIES',list(Path('.ablacao').glob('*Tutor')))
'@ | python -B -; rg -n 'DUAS CAMADAS|determ.*com|resumos' docs/reports/pendencias.md | Select-Object -First 25; rg -n '"'^def |score_topic'"' src/builder/core/content_taxonomy.py src/builder/routing/*.py"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f,ranges in {'src/builder/routing/file_map.py':[(1,290)],'src/builder/routing/resolver_apply.py':[(385,510)],'src/builder/core/vocabulary_compile.py':[(1,175)],'docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md':[(1,155)]}.items():
 ls=Path(f).read_text(encoding='utf-8').splitlines();print('\\nFILE',f)
 for a,b in ranges:
  for i in range(a-1,min(b,len(ls))): print(f'{i+1}: {ls[i]}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 242ms:[0m

FILE src/builder/routing/file_map.py
1: from __future__ import annotations
2: 
3: import json
4: import logging
5: import re
6: from dataclasses import dataclass, field
7: from datetime import date
8: from pathlib import Path
9: from typing import Callable, Dict, List, NamedTuple, Optional, Tuple
10: 
11: from src.builder.routing.dates import extract_dates
12: from src.builder.text.normalize import normalize_match_text as _normalize_text
13: from src.builder.text.normalize import split_camel_case
14: from src.builder.routing.thresholds import (
15:     DATE_STRONG_BOOST,
16:     DATE_WEAK_BOOST,
17:     T,
18:     relative_margin_confidence,
19: )
20: from src.builder.text.stopwords import UNIT_GENERIC_TOKENS
21: from src.builder.text.stopwords import FILE_MAP_TITLE_ANCHOR_STOP, FILE_MAP_TOPIC_ANCHOR_STOP
22: 
23: 
24: @dataclass
25: class UnitMatchResult:
26:     slug: str
27:     confidence: float
28:     ambiguous: bool = False
29:     reasons: List[str] = field(default_factory=list)
30: 
31: 
32: def strip_outline_prefix(text: str) -> str:
33:     text = (text or "").strip()
34:     if not text:
35:         return ""
36:     text = re.sub(
37:         r"^\s*unidade(?:\s+de\s+aprendizagem)?\s*\d+\s*[-—:.)]?\s*",
38:         "",
39:         text,
40:         flags=re.IGNORECASE,
41:     )
42:     text = re.sub(r"^\s*\d+(?:\.\d+)*\s*[-—:.)]?\s*", "", text)
43:     return text.strip()
44: 
45: 
46: def build_file_map_unit_index(
47:     units: list,
48:     *,
49:     normalize_match_text: Callable[[str], str],
50:     normalize_unit_slug: Callable[[str], str],
51:     strip_outline_prefix: Callable[[str], str],
52:     topic_text: Callable[[object], str],
53:     unit_generic_tokens: set[str],
54: ) -> list:
55:     indexed = []
56:     # Titulo normalizado de cada unidade: frase igual ao titulo de OUTRA unidade e
57:     # sinal roubado (glossario e aliases injetavam `verificacao de programas` na u01
58:     # do MF, titulo da u02 — 6 entries migravam para a unidade errada).
59:     other_unit_titles = set()
60:     for unit in units or []:
61:         raw_title = unit.get("title", "") if isinstance(unit, dict) else unit[0]
62:         title_norm = normalize_match_text(strip_outline_prefix(raw_title))
63:         if title_norm:
64:             other_unit_titles.add(title_norm)
65: 
66:     def _partes(unit):
67:         if isinstance(unit, dict):
68:             return (unit.get("title", ""), unit.get("topics", []) or [],
69:                     unit.get("extra_signals", []) or [])
70:         return (unit[0], unit[1], [])
71: 
72:     def _frases(itens):
73:         return {normalize_match_text(strip_outline_prefix(topic_text(i))) for i in itens} - {""}
74: 
75:     # Frase presente em TODAS as unidades tem poder discriminante ZERO — so infla
76:     # o score da unidade maior. Origens medidas (2026-08-18): a definicao
77:     # auto-gerada do glossario, que e a MESMA frase-modelo para todo termo, e
78:     # definicao que virou dump de sumario (ES2 injetava `camadas`, topico da u01,
79:     # nas outras duas). Descarta so onde a frase NAO e topico proprio: a unidade
80:     # dona mantem e volta a discriminar, as outras perdem.
81:     proprias = [_frases(topics) for _, topics, _ in map(_partes, units or [])]
82:     ubiquas: set = set()
83:     if len(proprias) > 1:
84:         ubiquas = set.intersection(
85:             *(proprias[i] | _frases(extras)
86:               for i, (_, _, extras) in enumerate(map(_partes, units or [])))
87:         )
88: 
89:     for unit_pos, unit in enumerate(units or []):
90:         title, topics, extra_signals = _partes(unit)
91:         # A2: conjunto de genericos POR CURSO carimbado no spec (build_file_map_unit_index_from_course);
92:         # sem carimbo cai na constante injetada (comportamento de antes).
93:         unit_generic = set((unit.get("generic_tokens") or []) if isinstance(unit, dict) else []) or set(unit_generic_tokens)
94:         descartar = ubiquas - proprias[unit_pos]
95:         clean_title = strip_outline_prefix(title)
96:         topic_phrases = []
97:         topic_tokens = []
98:         seen_topic_tokens = set()
99:         for topic in list(topics) + list(extra_signals):
100:             topic_norm = normalize_match_text(strip_outline_prefix(topic_text(topic)))
101:             if not topic_norm:
102:                 continue
103:             if topic_norm != normalize_match_text(clean_title) and topic_norm in other_unit_titles:
104:                 continue
105:             if topic_norm in descartar:
106:                 continue
107:             topic_phrases.append(topic_norm)
108:             if topic_norm not in seen_topic_tokens:
109:                 topic_tokens.append(topic_norm)
110:                 seen_topic_tokens.add(topic_norm)
111:             for token in topic_norm.split():
112:                 if len(token) >= 4 and token not in seen_topic_tokens and token not in unit_generic:
113:                     topic_tokens.append(token)
114:                     seen_topic_tokens.add(token)
115:         indexed.append({
116:             "title": title,
117:             # carimbo so quando veio calculado por curso; None -> cada consumidor usa a sua constante
118:             "generic_tokens": sorted(unit_generic) if (isinstance(unit, dict) and unit.get("generic_tokens")) else None,
119:             "slug": normalize_unit_slug(title),
120:             "normalized_title": normalize_match_text(clean_title),
121:             "topics": topics,
122:             "extra_signals": extra_signals,
123:             "topic_phrases": topic_phrases,
124:             "topic_tokens": topic_tokens,
125:             "title_anchor_tokens": [
126:                 token
127:                 for token in normalize_match_text(clean_title).split()
128:                 if len(token) >= 4 and token not in FILE_MAP_TITLE_ANCHOR_STOP
129:             ],
130:             "topic_anchor_tokens": [
131:                 token
132:                 for token in {token for text in topic_phrases for token in text.split()}
133:                 if len(token) >= 4 and token not in FILE_MAP_TOPIC_ANCHOR_STOP
134:             ],
135:             "distinctive_tokens": [],
136:         })
137: 
138:     token_frequency = {}
139:     for unit in indexed:
140:         unit_tokens = set()
141:         for text in [unit["normalized_title"]] + unit.get("topic_tokens", []):
142:             for token in text.split():
143:                 if len(token) >= 4 and not token.isdigit() and token not in unit_generic:
144:                     unit_tokens.add(token)
145:         for token in unit_tokens:
146:             token_frequency[token] = token_frequency.get(token, 0) + 1
147: 
148:     for unit in indexed:
149:         unit_tokens = set()
150:         for text in [unit["normalized_title"]] + unit.get("topic_tokens", []):
151:             for token in text.split():
152:                 if len(token) >= 4 and not token.isdigit() and token not in unit_generic:
153:                     unit_tokens.add(token)
154:         unit["token_weights"] = {
155:             token: 1.0 / token_frequency[token]
156:             for token in unit_tokens
157:             if token_frequency.get(token)
158:         }
159:         unit["distinctive_tokens"] = sorted(
160:             token
161:             for token, freq in token_frequency.items()
162:             if freq == 1 and token in unit_tokens and len(token) >= 5
163:         )
164:     return indexed
165: 
166: 
167: # "Revisão", "revisao", "revisões" no titulo ou no id (o id preserva fronteira
168: # de palavra onde o titulo usa "_", mesmo criterio do _PROVA_RE da cobertura).
169: _REVISAO_RE = re.compile(r"\brevis", re.IGNORECASE)
170: 
171: 
172: def auto_map_entry_subtopic(
173:     entry: dict,
174:     taxonomy: dict,
175:     markdown_text: str,
176:     *,
177:     winning_unit_slug: str = "",
178:     collect_entry_unit_signals: Callable[[dict, str], dict],
179:     iter_content_taxonomy_topics: Callable[[dict], List[dict]],
180:     score_entry_against_taxonomy_topic: Callable[[dict, dict], float],
181:     topic_match_result_factory,
182: ):
183:     topic_index = iter_content_taxonomy_topics(taxonomy)
184:     if winning_unit_slug:
185:         topic_index = [t for t in topic_index if str(t.get("unit_slug", "") or "") == winning_unit_slug]
186:     if not topic_index:
187:         return topic_match_result_factory(
188:             topic_slug="",
189:             topic_label="",
190:             unit_slug="",
191:             confidence=0.0,
192:             ambiguous=True,
193:             reasons=[f"sem-topicos-para-unidade:{winning_unit_slug}" if winning_unit_slug else "sem-taxonomia"],
194:         )
195: 
196:     signals = collect_entry_unit_signals(entry, markdown_text)
197:     scored = [(topic, score_entry_against_taxonomy_topic(signals, topic)) for topic in topic_index]
198:     scored.sort(key=lambda item: item[1], reverse=True)
199: 
200:     winner, winner_score = scored[0]
201:     runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
202:     margin = winner_score - runner_up_score
203:     rel_margin = margin / max(winner_score, 1e-6)
204:     # Sem sinal ou empate EXATO: nao ha vencedor real — o sort estavel elegeria
205:     # um slug arbitrario (menor indice na taxonomia) e o surfacaria com conf
206:     # 0.0 no editor (12 entries codigo-professor do repo real, 12/06). Slug
207:     # vazio e a resposta honesta; a reason preserva o diagnostico.
208:     if winner_score <= 0.0:
209:         return topic_match_result_factory(
210:             topic_slug="",
211:             topic_label="",
212:             unit_slug="",
213:             confidence=0.0,
214:             ambiguous=True,
215:             reasons=["sem-sinal (winner_score=0)"],
216:         )
217:     if len(scored) > 1 and margin == 0.0:
218:         tied = sum(1 for _, score in scored if score == winner_score)
219:         return topic_match_result_factory(
220:             topic_slug="",
221:             topic_label="",
222:             unit_slug="",
223:             confidence=0.0,
224:             ambiguous=True,
225:             reasons=[f"empate-exato {tied}x score={winner_score:.2f}"],
226:         )
227:     # Material de REVISAO sem assunto dominante revisa conteudo de fora da
228:     # taxonomia (pre-requisito, prova) — caso real: TCC aula-06 revisa a
229:     # cadeira de automatos e cairia em argumento-diagonal por vocabulario.
230:     # Escopado a titulo/id de revisao: piso global e refutado (thresholds).
231:     titulo_e_id = f"{entry.get('title') or ''} {entry.get('id') or ''}"
232:     if _REVISAO_RE.search(titulo_e_id) and winner_score < T.SUBUNIT_REVISAO_FLOOR:
233:         return topic_match_result_factory(
234:             topic_slug="",
235:             topic_label="",
236:             unit_slug="",
237:             confidence=0.0,
238:             ambiguous=True,
239:             reasons=[f"revisao-sem-assunto-dominante (winner_score={winner_score:.2f} < {T.SUBUNIT_REVISAO_FLOOR})"],
240:         )
241:     if len(scored) == 1:
242:         confidence = 0.72
243:         ambiguous = False
244:     else:
245:         confidence = max(0.0, min(1.0, rel_margin))
246:         ambiguous = rel_margin < T.SUBUNIT_AMBIG_MARGIN
247:     if ambiguous:
248:         confidence = min(confidence, 0.45)
249: 
250:     reasons = [f"winner_score={winner_score:.2f}"] + (["ambiguous"] if ambiguous else [])
251:     return topic_match_result_factory(
252:         topic_slug=str(winner.get("topic_slug", "") or ""),
253:         topic_label=str(winner.get("topic_label", "") or ""),
254:         unit_slug=str(winner.get("unit_slug", "") or ""),
255:         confidence=confidence,
256:         ambiguous=ambiguous,
257:         reasons=reasons,
258:     )
259: 
260: 
261: def score_entry_against_unit(
262:     signals: dict,
263:     unit: dict,
264:     *,
265:     score_timeline_unit_phrase: Callable[[str, set[str], str, dict], float],
266:     timeline_unit_neutral_tokens: set[str], unit_tag_boost = 0.0,
267: ) -> float:
268:     title_text = signals.get("title_text", "")
269:     markdown_headings_text = signals.get("markdown_headings_text", "")
270:     markdown_lead_text = signals.get("markdown_lead_text", "")
271:     markdown_text = signals.get("markdown_text", "")
272:     category_text = signals.get("category_text", "")
273:     manual_tags_text = signals.get("manual_tags_text", "")
274:     auto_tags_text = signals.get("auto_tags_text", "")
275:     legacy_tags_text = signals.get("legacy_tags_text", "")
276:     tags_text = signals.get("tags_text", "")
277:     raw_text = signals.get("raw_text", "")
278:     card_text = signals.get("card_text", "")
279:     # A2: genericos de unidade POR CURSO (carimbados no indice); sem carimbo, a constante.
280:     _neutral = set(unit.get("generic_tokens") or []) or set(timeline_unit_neutral_tokens)
281:     card_tokens = {tok for tok in card_text.split() if len(tok) >= 4}
282:     title_tokens = {tok for tok in title_text.split() if len(tok) >= 4}
283:     markdown_headings_tokens = {tok for tok in markdown_headings_text.split() if len(tok) >= 4}
284:     markdown_lead_tokens = {tok for tok in markdown_lead_text.split() if len(tok) >= 4}
285:     markdown_tokens = {tok for tok in markdown_text.split() if len(tok) >= 4}
286:     manual_tags_tokens = {tok for tok in manual_tags_text.split() if len(tok) >= 4}
287:     auto_tags_tokens = {tok for tok in auto_tags_text.split() if len(tok) >= 4}
288:     legacy_tags_tokens = {tok for tok in legacy_tags_text.split() if len(tok) >= 4}
289:     tags_tokens = {tok for tok in tags_text.split() if len(tok) >= 4}
290:     raw_tokens = {tok for tok in raw_text.split() if len(tok) >= 4}

FILE src/builder/routing/resolver_apply.py
385:     entry_markdown_text_for_file_map_fn,
386: ) -> list:
387:     """Fase 4 do cutover: unit/subunit no caminho do motor.
388: 
389:     Roda DEPOIS de apply_concept_resolver, sob a mesma flag: recomputa a
390:     unidade com o scorer sobrevivente e reconcilia contra o bloco que o
391:     motor acabou de gravar (fecha o gap 1.2 para os campos de unidade).
392:     Só toca entries que o motor decidiu (material + computed_block_id).
393:     """
394:     from src.builder.routing.file_map import (
395:         reconcile_unit_with_block, resolve_temporal_block, unit_of_block_or_neighbor,
396:     )
397:     from src.builder.routing.thresholds import T
398:     from src.models.tag_profile import build_learned_unit_boosts, load_tag_profile
399:     from src.utils.helpers import collapse_ws as _collapse_ws
400: 
401:     unit_index = build_file_map_unit_index_from_course_fn(course_meta, subject_profile)
402:     content_taxonomy = (
403:         course_meta.get("_content_taxonomy")
404:         or course_meta.get("_content_taxonomy_for_tests")
405:         or {}
406:     )
407:     if not content_taxonomy and course_meta.get("_repo_root"):
408:         from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
409:         content_taxonomy = load_internal_content_taxonomy(course_meta["_repo_root"])
410:     topic_index = iter_content_taxonomy_topics_fn(content_taxonomy)
411:     passe1: list = []   # (entry, texto, unidade, TopicMatchResult) da rota automatica, para a 2a passada
412: 
413:     tag_profile = None
414:     if root:
415:         try:
416:             tag_profile = load_tag_profile(Path(root) / "course")
417:         except Exception:
418:             tag_profile = None
419: 
420:     for entry in entries:
421:         if not _is_material(entry):
422:             continue
423:         block_id = str(entry.get("computed_block_id") or "").strip()
424:         if not block_id and not str(entry.get("temporal_block_id") or "").strip():
425:             # Bibliografia/referencias/cronograma sao limpas do BLOCO de proposito
426:             # (`apply_concept_resolver`): nao foram "dadas" numa aula, nao tem eixo
427:             # temporal. Mas TEM eixo de cobertura — sao material bibliografico DE
428:             # alguma unidade, e o proprio gold ja as rotula (as laminas de sockets
429:             # do SO estao em `coverage_gt_SO.csv` como u03, provenance=plano-de-
430:             # ensino). Sem bloco, `reconcile_unit_with_block` devolve a unidade do
431:             # scorer intacta (file_map.py:722), entao passar por aqui e seguro.
432:             # Medido 2026-08-19: 14 entries nesta situacao nos 5 cursos, 6 passam
433:             # a acertar e NENHUMA passa a errar (as outras 8 morrem no gate).
434:             categoria = _collapse_ws_cat(str(entry.get("category") or "")).lower()
435:             if categoria not in _NO_TIMELINE_CATEGORIES:
436:                 continue
437: 
438:         markdown_text = entry_markdown_text_for_file_map_fn(root, entry) if root is not None else ""
439: 
440:         # Zip/codigo nao tem .md: o unico sinal e o resumo do Gemini em
441:         # `code_curation.json`. O BLOCO ja recebe (`entry["concepts"]`, linha 90)
442:         # e a SUBUNIDADE tambem (`sub_md` abaixo) — a UNIDADE era a unica cega,
443:         # decidindo com texto vazio para 25 de 233 materiais dos 5 cursos (11%),
444:         # entre eles `colecoes-*` e `classes-parte1` do MF, que viviam no balde
445:         # de erro. Medido 2026-08-19: 129 -> 133 acertos, nenhum curso regride.
446:         code_rec = (code_curation.get("entries") or {}).get(str(entry.get("id") or "")) or {}
447:         texto_para_unidade = markdown_text
448:         if code_rec:
449:             from src.builder.core.code_summarization import code_curation_signal_text
450:             resumo = code_curation_signal_text(code_rec)
451:             if resumo:
452:                 texto_para_unidade = f"{markdown_text}\n\n{resumo}" if markdown_text else resumo
453: 
454:         manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
455:         if manual_unit:
456:             resolved_unit_slug, unit_confidence = manual_unit, 1.0
457:             unit_ambiguous, unit_reasons = False, ["manual"]
458:         else:
459:             learned = build_learned_unit_boosts(tag_profile, entry) if tag_profile else {}
460:             match = auto_map_entry_unit_fn(
461:                 entry, unit_index, texto_para_unidade, topic_index,
462:                 learned_unit_boosts=learned,
463:             )
464:             resolved_unit_slug = match.slug
465:             unit_confidence = match.confidence
466:             unit_ambiguous = match.ambiguous
467:             unit_reasons = list(match.reasons)
468: 
469:         gated_unit = resolved_unit_slug if (not unit_ambiguous and unit_confidence >= T.UNIT_TAG) else ""
470: 
471:         # Eixo de COBERTURA (N unidades), separado do 1:1 acima. Prova, lista,
472:         # plano de ensino e serie de laboratorio cobrem mais de uma unidade —
473:         # forcar uma so e o erro de cardinalidade que travava a medicao.
474:         from src.builder.routing.coverage_rules import META_COVERAGE_RULES, derive_coverage_units
475:         from src.builder.text.normalize import normalize_match_text as _norm_cov
476:         cobertura = derive_coverage_units(
477:             entry, unit_index, texto_para_unidade,
478:             normalize=lambda t: _norm_cov(t, keep="+-./"),
479:             fallback_unit_slug=gated_unit,
480:             topic_index=topic_index,
481:             blocks=blocks,
482:         )
483:         if cobertura:
484:             entry["coverage_units"] = cobertura
485:         else:
486:             entry.pop("coverage_units", None)
487: 
488:         # 2026-08-21: o bloco que manda na unidade e o TEMPORAL (ancora:
489:         # manual > temporal_block_id > computed), o mesmo que a regua mede —
490:         # nao o computed_block_id do scorer de conceito. Esta fase roda DEPOIS
491:         # da camada temporal (pedagogical_regeneration) justamente para ve-lo.
492:         # Bloco sem unit_slug (avaliacao/revisao/overview) herda do vizinho de
493:         # conteudo. Medido: scorer 130/188 -> bloco temporal + heranca 178/188.
494:         temporal_id = resolve_temporal_block(entry, blocks)
495:         block_unit, vizinho = unit_of_block_or_neighbor(temporal_id, blocks)
496:         blk = next((b for b in blocks
497:                     if str(b.get("id") or "") == temporal_id or str(b.get("block_uuid") or "") == temporal_id), None)
498:         block_ref = str((blk or {}).get("id") or temporal_id or block_id)
499: 
500:         # Pino manual direto do entry: computed_block_method pode ter sido
501:         # trocado p/ consensus/llm_only pelo attach ANTES deste apply — o
502:         # method nao e prova de pino (review final F4, I2).
503:         _pin = str(entry.get("manual_timeline_block_id") or "").strip()
504:         block_is_manual = bool(_pin) and _pin in {temporal_id, block_id, str((blk or {}).get("id") or ""),
505:                                                   str((blk or {}).get("block_uuid") or "")}
506: 
507:         reconciled, suffix, conflict = reconcile_unit_with_block(
508:             computed_unit_slug=gated_unit,
509:             unit_confidence=float(unit_confidence),
510:             computed_block_id=block_ref if block_unit else "",

FILE src/builder/core/vocabulary_compile.py
1: """Fase 1b (plano 02/09): vocabulario por curso SEM mao — 1 chamada de LLM por unidade
2: COM material, gravado em `course/.glossary_curation.llm.json` no formato do loader
3: (`repo.load_glossary_curation`: `{"<codigo> <Label do plano>": {"synonyms": [...]}}`, chaves
4: `_*` sao metadados). O loader funde este arquivo com o sidecar MANUAL `.glossary_curation.json`.
5: 
6: Por que o LLM: medido em 02/09 (`docs/reports/_harness-2026-09-02/compila_vocab_v2.py`) —
7: co-heading deterministico 26 -> 31/93 (refutado); este prompt IA 5 -> 37/39, FR 12 -> 17/19.
8: O LLM NAO inventa: classifica titulos/headings dos materiais da unidade nos topicos do plano.
9: 
10: Regras (decisoes C e D + o que o reprocess real de 02/09 ensinou):
11: - sidecar MANUAL existe -> o curso ja tem vocabulario: NAO chama (SO/IA/ES2/TCC intactos).
12: - `.llm.json` existe -> cache; `recompile=True` (flag `recompile_vocab`) rechama; `refilter=True`
13:   (flag `refilter_vocab`) reaplica os filtros sobre `_raw` SEM chamar (filtro muda, dado nao rola).
14: - chave = "<codigo> <label>" como o glossario escreve (R8: termo numerado casa so pelo nucleo
15:   exato — "3.1 Conceitos basicos" != "5.1 Conceitos basicos"). Sem codigo, so o label.
16: - filtros: termo == label · termo em > 1 topico (exclusividade) · termo cujo normalizado e id/
17:   titulo de um arquivo do curso · termo sem token especifico (so genericos do curso) ·
18:   **identidade**: termo igual ao nome de OUTRA unidade/topico, ou (>= 2 tokens) contido nele
19:   (CG: a aula 1 enumera as outras unidades e 48 materiais foram sugados para u01).
20: - unidades = `computed_unit_slug` do manifest (estrutura). Build do zero ainda nao tem unidade:
21:   nao grava nada e o reprocess seguinte compila.
22: Arquivo separado do manual (deviacao registrada do plano, que dizia "mesmo arquivo"): o motor
23: puro apaga a curadoria manual e mantem o compilado — sem isso a regua "puro + vocab compilado"
24: precisaria de caso especial, e recompilar nunca sobrescreve trabalho humano.
25: """
26: from __future__ import annotations
27: 
28: import collections
29: import json
30: import logging
31: import re
32: from pathlib import Path
33: from typing import Dict, List, Optional
34: 
35: from pydantic import BaseModel, Field
36: 
37: from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
38: from src.builder.extraction.content_taxonomy import _extract_markdown_headings, _topic_support_tokens
39: from src.builder.routing.resolver_apply import _is_material
40: from src.builder.text.normalize import normalize_match_text
41: from src.utils.helpers import write_text
42: from src.models.core import moodle_label_text  # leitor unico (07/09)
43: 
44: logger = logging.getLogger(__name__)
45: 
46: LLM_VOCAB_NAME = ".glossary_curation.llm.json"
47: MANUAL_VOCAB_NAME = ".glossary_curation.json"
48: # Fora do vocabulario: avaliacoes e meta-material nao descrevem UM topico.
49: OUT_CATS = frozenset({"cronograma", "provas", "trabalhos", "fotos-de-prova"})
50: MAX_BUNDLE_CHARS = 24000
51: _UNIT_PREFIX_WORDS = {"unidade", "de", "aprendizagem", "modulo", "parte", "topico", "ua"}
52: 
53: 
54: class TopicoTermos(BaseModel):
55:     topico: str = Field(description="label do topico, exatamente como dado")
56:     termos: List[str] = Field(default_factory=list,
57:                               description="termos/expressoes DOS MATERIAIS que pertencem a este topico")
58: 
59: 
60: class Vocab(BaseModel):
61:     topicos: List[TopicoTermos] = Field(default_factory=list)
62: 
63: 
64: # Prompt v2 — o unico ajuste permitido, medido (IA 34 -> 37/39). Nao mexer sem remedir.
65: SYSTEM = (
66:     "Voce recebe os TOPICOS de uma unidade do plano de ensino e os titulos e headings dos MATERIAIS "
67:     "dessa unidade. Tarefa: para cada topico, liste os termos e expressoes curtas (1-4 palavras) que "
68:     "APARECEM nos materiais e que pertencem a esse topico (nomes de algoritmos, tecnicas, siglas, "
69:     "conceitos). Inclua os termos dos TITULOS e as VARIANTES que aparecem no texto (sigla, ingles e "
70:     "portugues, singular e plural, ex.: 'clustering', 'cluster', 'agrupamento', 'EDA', 'analise "
71:     "exploratoria'). Regras: (1) so termos presentes no texto dado — nao invente; (2) cada termo em no "
72:     "maximo um topico; (3) ignore palavras genericas (introducao, exercicio, aula, exemplo, revisao) "
73:     "e o nome da disciplina; (4) se nenhum material cobre um topico, devolva lista vazia; (5) responda "
74:     "apenas o JSON do schema."
75: )
76: 
77: 
78: def _norm(text: str) -> str:
79:     return " ".join(normalize_match_text(str(text or "")).split())
80: 
81: 
82: def _strip_code(text: str) -> str:
83:     return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", " ".join(str(text or "").split()))
84: 
85: 
86: def topic_key(topic: dict) -> str:
87:     """Chave do sidecar = texto do topico como o glossario o escreve ("1.2 Modelos OSI e TCP/IP")."""
88:     code = str(topic.get("code") or "").strip()
89:     label = " ".join(str(topic.get("label") or "").split())
90:     return f"{code} {label}".strip()
91: 
92: 
93: def unit_title_core(title: str) -> str:
94:     """"Unidade de Aprendizagem 4 — Processo de Visualizacao 2D (10%)" -> "processo de visualizacao 2d"."""
95:     toks = _norm(title).split()
96:     while toks and (toks[0] in _UNIT_PREFIX_WORDS or toks[0].isdigit()):
97:         toks.pop(0)
98:     while toks and toks[-1].isdigit():
99:         toks.pop()
100:     return " ".join(toks)
101: 
102: 
103: def identities_of(taxonomy: dict) -> dict:
104:     """{"labels": {key: (unit_slug, label_norm)}, "units": {unit_slug: core_norm}} da taxonomia."""
105:     labels: Dict[str, tuple] = {}
106:     units: Dict[str, str] = {}
107:     for unit in (taxonomy or {}).get("units") or []:
108:         slug = str(unit.get("slug") or "")
109:         core = unit_title_core(str(unit.get("title") or ""))
110:         if core:
111:             units[slug] = core
112:         for topic in unit.get("topics") or []:
113:             if topic.get("label"):
114:                 labels[topic_key(topic)] = (slug, _norm(topic["label"]))
115:     return {"labels": labels, "units": units}
116: 
117: 
118: def _generic_tokens(taxonomy: dict) -> set:
119:     """Genericos do curso (A2/df), os mesmos carimbados nos topicos pelo scorer de subunidade."""
120:     try:
121:         from src.builder.timeline.index import _iter_content_taxonomy_topics
122:         topics = _iter_content_taxonomy_topics(taxonomy) or []
123:         return set((topics[0].get("generic_tokens") if topics else None) or [])
124:     except Exception:
125:         return set()
126: 
127: 
128: def filter_terms(compilado: Dict[str, List[str]], *, generic: set, file_names: set,
129:                  identities: Optional[dict] = None) -> Dict[str, List[str]]:
130:     """Pos-filtro (decisao C + identidade). `compilado` = {chave: [termos crus]} -> {chave: [termos]}."""
131:     ids = identities or {"labels": {}, "units": {}}
132:     label_norm = {key: ids["labels"].get(key, ("", _norm(_strip_code(key))))[1] for key in compilado}
133:     onde: Dict[str, set] = collections.defaultdict(set)
134:     for key, termos in compilado.items():
135:         for t in termos:
136:             tn = _norm(t)
137:             if tn:
138:                 onde[tn].add(key)
139:     out: Dict[str, List[str]] = {}
140:     for key, termos in compilado.items():
141:         own_unit = ids["labels"].get(key, ("", ""))[0]
142:         others = {v[1] for k, v in ids["labels"].items() if k != key} | \
143:                  {core for u, core in ids["units"].items() if u != own_unit}
144:         keep: List[str] = []
145:         seen: set = set()
146:         for t in termos:
147:             t = " ".join(str(t or "").split())
148:             tn = _norm(t)
149:             if not tn or tn in seen or tn == label_norm[key] or len(onde[tn]) > 1 or tn in file_names:
150:                 continue
151:             if tn in others or (len(tn.split()) >= 2 and any(tn in o for o in others)):
152:                 continue
153:             if not {x for x in _topic_support_tokens(t) if x not in generic}:
154:                 continue
155:             seen.add(tn)
156:             keep.append(t)
157:         out[key] = keep
158:     return out
159: 
160: 
161: def _bundle(taxonomy: dict, unit: dict, labels: List[str], mats: List[dict], root: Path) -> str:
162:     linhas = []
163:     for e in mats:
164:         md = _entry_markdown_text_for_file_map(root, e) or ""
165:         heads = _extract_markdown_headings(md, limit=24)
166:         # zip nao tem .md proprio (process_zip deixa base_markdown=None): os membros entram pelo nome-base,
167:         # nao pelo caminho -- o corte de 60 chars abaixo comeria o nome da classe numa arvore Java.
168:         heads = list(heads) + list(dict.fromkeys(Path(str(f.get("title") or "").replace("\\", "/")).name
169:                                                  for f in (e.get("extracted_files") or []) if f.get("title")))
170:         ml = moodle_label_text(e)
171:         linhas.append(f"- TITULO: {e.get('title')} | LABEL MOODLE: {ml}\n  HEADINGS: "
172:                       + " | ".join(h[:60] for h in heads[:24]))
173:     return (f"DISCIPLINA: {taxonomy.get('course_name') or ''}\nUNIDADE: {unit.get('title')}\nTOPICOS DO PLANO:\n"
174:             + "\n".join(f"  * {label}" for label in labels) + "\n\nMATERIAIS:\n" + "\n".join(linhas))[:MAX_BUNDLE_CHARS]
175: 

FILE docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md
1: # Plano — confiança antes de acurácia
2: 
3: last_updated: 2026-09-08 (reescrito depois da atualização dos artefatos)
4: Entrada: `docs/reports/pendencias.md` (tracker vivo) · `.mex/context/audit-2026-09-07.md` (memória) ·
5: harness `docs/reports/_harness-2026-09-04/c1-3/`
6: Artefatos: [Placar](https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de) ·
7: [Matriz](https://claude.ai/code/artifact/4ddad807-e2fe-4ede-a3ca-c175916f7ca6)
8: 
9: ---
10: 
11: ## 1. A tese, e por que esta ordem
12: 
13: O gold deixou de ser insumo do motor em 07/09 (`baab4ac`, `ea0701f`); os números abaixo são pós-limpeza. Ele mede. O que o motor tem de próprio para saber se acertou é a **confiança**, que
14: vira a fila de revisão. Medido em 08/09 (`c1-3/calibra_fila_como_regua.log`):
15: 
16: | eixo | precisão do confiante | leitura |
17: |---|---|---|
18: | unidade | **157/157 = 100%** | inferência: CG 93, LR 7 e FR 22 não têm gold e ficam fora da conta; testa em 3.2 |
19: | bloco | 177/178 = 99,4% | idem, na prática |
20: | **subunidade** | **117/181 = 64,6%** | **64 materiais saem errados sem aviso** |
21: 
22: Subir acurácia com a confiança mentindo aumenta os acertos **e** os erros silenciosos. Produto que erra calado é pior
23: que produto que pergunta: o aluno não tem como saber que aquele material está no lugar errado. **Confiança primeiro.**
24: 
25: Isso também é o que responde ao objetivo de fundo: *a atribuição não deve depender de gold feito à mão*. Na unidade, nos cursos com gold, já
26: não depende. Na subunidade, o caminho não é remover o gold, é usá-lo **uma vez** para descobrir onde a confiança mente;
27: depois disso a confiança viaja sozinha para cursos novos.
28: 
29: **O que não fazer:** automatizar a criação do gold a partir do Moodle e do SARC. Medido: a régua construída dessas
30: fontes acerta 39/44 onde o motor acerta 44/44 — um gold automático teria introduzido 5 erros no SO. Não se mede um
31: instrumento com uma cópia pior dele mesmo.
32: 
33: ---
34: 
35: ## 2. Estado de partida (08/09, produto em disco, Gemini bloqueado)
36: 
37: | medida | valor |
38: |---|---|
39: | materiais 100% certos | 199/288 |
40: | bloco | 235/237 |
41: | unidade | 190/190 |
42: | subunidade | **161/251** |
43: | fila | 96 em 348 = 27,6 por 100 |
44: | **erros confiantes** | **64** |
45: 
46: **Cobertura do gold:** bloco 68% do repositório, unidade 55%, subunidade 72%. CG (93 materiais) e LR (7) não têm gold
47: de unidade nenhum; LR não tem gold de bloco.
48: 
49: **Regimes** (`c1-3/mede_sem_voto_llm.log`, base antiga de 233 na subunidade):
50: 
51: | regime | 100% certos | bloco | unidade | subunidade | fila |
52: |---|---|---|---|---|---|
53: | produto | 199/288 | 235/237 | 190/190 | 146/233 | 91 |
54: | sem o voto de LLM | 184/288 | 221/237 | 188/190 | 143/233 | 136 |
55: | zero LLM | 165/288 | 222/237 | 188/190 | 121/233 | 143 |
56: 
57: O voto de LLM vale 14 no bloco e 2 na unidade. Sem ele o motor não erra mais, **desiste mais**.
58: 
59: ---
60: 
61: ## FASE 1 — HONESTIDADE DA CONFIANÇA
62: 
63: **Objetivo:** que o motor mande para a fila o que hoje entrega calado.
64: **Régua:** `calibra_fila_como_regua.py`, precisão do confiante por eixo.
65: **Gate de saída:** precisão do confiante da subunidade **≥ 90%**, sem regressão em bloco e unidade, com o crescimento
66: da fila declarado e aceito pelo user.
67: 
68: ### 1.1 Diagnosticar os 64 erros confiantes · 0 chamadas
69: Cruzar, para cada um: score do vencedor, margem para o segundo, origem do sinal (rótulo do plano, alias de heading,
70: alias compilado), tamanho do texto, classe do insumo. Só medição, sem código de motor.
71: Hipótese de trabalho, **não medida**: margem alta vindo de alias longo casando por acaso em texto curto.
72: 
73: ### 1.2 Calibrar o limiar · 0 chamadas
74: Varrer o limiar de **confiança/margem** contra o gold, medindo os dois lados: quantos erros confiantes somem e quanto a
75: fila cresce. O gold entra **uma vez**, aqui.
76: **Ressalva registrada:** piso sobre o *score* já foi refutado em 07/09 (todo piso perde). Este item é sobre outra
77: grandeza. Se também não houver corte útil, o item morre e vira registro.
78: 
79: ### 1.3 Fazer a decisão fraca cair na fila
80: Só se 1.2 achar ponto. Regra no motor, com gate zero-diff, teste e reprocess registrado nos 8.
81: 
82: ---
83: 
84: ## FASE 2 — ACURÁCIA
85: 
86: Começa com a Fase 1 fechada. Os três primeiros itens não gastam chamada.
87: 
88: ### 2.1 Propagação por similaridade — **+5 medido** · 0 chamadas
89: Material indeciso depois da 1ª e da 2ª passada herda a subunidade do vizinho mais similar entre os que o motor decidiu
90: com confiança. Similaridade = Jaccard dos tokens distintivos, dentro da unidade.
91: `simula_propaga_similaridade.log`: regime atual 135 → 140, ganha 6 perde 1, piso 0,05–0,10.
92: 
93: ### 2.2 Filtro mais duro no vocabulário compilado — **teto +2 por ablação; filtro não medido** · 0 chamadas
94: Cortar termo doado cujo núcleo aparece no vocabulário ou nos materiais de outra unidade, e recusar doação a tópico de
95: rótulo meta ("Áreas relacionadas", "Conceitos", "Introdução").
96: `triagem_vocab_llm.log` l.20 mede remover o vocabulário LLM inteiro da unidade 01 do CG (+2), não o filtro; outras 3 chamadas são neutras. Medir o filtro em si antes de executar este item.
97: 
98: ### 2.3 `conflito` — 48 itens, metade da fila, nunca atacado · 0 chamadas
99: Quando o texto aponta uma unidade e o bloco aponta outra, o bloco vence por desenho e o desacordo só vira registro.
100: Há gold de unidade em 190 materiais para arbitrar quem acerta nesses casos. **Medir antes de mexer.**
101: 
102: ### 2.4 Ligar o compilador de vocabulário nos 4 cursos bloqueados · 16 chamadas · **GEMINI LIBERADO (user, 08/09)**
103: SO 6 + IA 4 + ES2 2 + TCC 4, uma vez, cacheadas em `course/.glossary_curation.llm.json`.
104: Referência de 02/09 citada no próprio código: este prompt levou o IA de 5 para 37/39.
105: 
106: **Protocolo de contenção, não negociável nesta campanha:**
107: 1. **Um curso por vez**, conferindo o contador que o compilador loga (`vocab: <curso> — N chamada(s)`) antes do próximo.
108:    Se N passar do número de unidades com material daquele curso, **parar e investigar**.
109: 2. `TUTOR_NO_VOCAB_COMPILE=1` continua em **todo** script de medição. Medição nunca compila.
110: 3. O voter **não** é rechamado: os 96 votos de bloco já estão em cache por md5, e `llm_vote.DEFAULT_CAP = 20` por rodada
111:    segue como rede.
112: 4. `gemini_auto_summarize` continua **desligado** (incidente de 05/09: um reprocess re-resumiu 60 arquivos).
113: 5. Pós-check obrigatório: contar chamadas do dia antes e depois, e registrar o número no tracker junto do resultado.
114: 6. Para o sidecar do professor sair da frente (`vocabulary_compile.py:222`), **renomear**, nunca apagar.
115: 
116: ---
117: 
118: ## FASE 3 — COBERTURA DA RÉGUA
119: 
120: ### 3.1 Incluir o FR no conjunto padrão · 0 chamadas
121: `subunit_gt_FR.csv` tem 18 materiais pontuáveis que nunca entraram em nenhuma medição desta campanha; o FR faz 15/18.
122: Todo script do harness que hoje usa 6 cursos passa a usar 7. **Sem isso, todo absoluto publicado continua incompleto.**
123: 
124: ### 3.2 Gold de unidade para o CG
125: 93 materiais, 27% do repositório, hoje sem régua nenhuma nesse eixo. A confirmação independente pelo professor cobre só
126: 17% deles (16 de 93); no FR ela é zero, porque os 19 acordos são circulares. É o único jeito de fechar a pergunta
127: "a unidade se sustenta fora do gold?".
128: 
129: ---
130: 
131: ## 3. Decisões abertas que travam trabalho
132: 
133: | item | o que trava |
134: |---|---|
135: | **Qual camada LLM cortar** para ficar em duas | decisão de arquitetura aberta desde 06/09 |
136: | **Push/merge** dos ~965 commits locais | nada técnico; é decisão de fronteira |
137: | **Posição da C7 (imagens)** na fila de campanhas | ordenação |
138: | Revisão da fila do CG (`revisar_queue.md`) | trabalho humano |
139: | Correção da extração dos zips | **32 dos 35 zips** afetados; 99 nomes de conteúdo colidem entre zips do mesmo curso (CG 60, ES2 29, MF 10) |
140: 
141: ## 4. Campanha formal e a próxima
142: 
143: **C1 TRAVESSIA** é a única aberta; este plano é o conteúdo dela (1.x e 2.1–2.3). Os itens 3.x continuam a C5.
144: 
145: **Decidido pelo user em 08/09: a próxima é a C5 DÍVIDAS DE DADOS, não a C3.** Fundamento medido
146: (`compara_c3_c5.log`), depois de corrigir dois números meus que estavam inflados:
147: 
148: | grupo | materiais | errados | % erro |
149: |---|---|---|---|
150: | **C3** (provas, listas, trabalhos, gabaritos) | 71 (20%) | **8 (9% dos erros)** | **14%** |
151: | resto | 277 | 84 | **34%** |
152: 
153: 1. **C3 não tem massa de erro:** é já a parte mais saudável do repositório.
154: 2. **A C5 tem defeito com tamanho medido:** **32 dos 35 zips** têm colisão de nome de conteúdo entre si (99 nomes:
155:    CG 60, ES2 29, MF 10). O código extraído e o resumo desses materiais podem estar trocados.

[1mhook:[0m [2mPostToolUse[0m
[31m exited 1 in 388ms:[0m
COPIES [WindowsPath('.ablacao/Computacao-Grafica-Tutor'), WindowsPath('.ablacao/Engenharia-Software-2-Tutor'), WindowsPath('.ablacao/Fundamentos-de-Redes-Tutor'), WindowsPath('.ablacao/Inteligencia-Artifical-Tutor'), WindowsPath('.ablacao/Laboratorio-de-Redes-Tutor'), WindowsPath('.ablacao/Metodos-Formais-Tutor'), WindowsPath('.ablacao/Sistemas-Operacionais-Tutor'), WindowsPath('.ablacao/TCC-Tutor')]
692:`.determinismo` e `.zerodiff` (temporarios de gate, recriaveis com `--base`). **Ficam** as 8 copias `.ablacao/<Tutor>` (regime
1181:em `.ablacao/FR-rebuild/`. **Zero chamada externa** (tripwire de Gemini e de Datalab: 0 tentativas), vocab NAO compilado, sem votos, sem resumos, sem
1182:pino, sem gold. O FR atual (produto) fica como comparacao: ele tem vocab LLM (53 sinonimos), 13 votos e 4 resumos.
1349:## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3 (RESUMOS DE CODIGO) MEDIDA: ABLACAO E SUBSTITUTO DETERMINISTICO (06/09, sessao 6; DECISAO DO USER)
1351:novas rotas para o motor". **Peso medido no produto (8 tutores):** vocab = 1 compilacao por curso · resumos de codigo = 85 (1 por arquivo/zip, cache por
1356:| COM resumos do Gemini (referencia, `b_prop_*.log`) | 186 | 183 | 53 | **87** (83 primario) | 31 |
1357:| SEM resumos (`code_curation.json` vazio, `codigo_sem_*.log`) | 186 | 183 | 53 | **71** (67) | 31 |
1388:unidades (SO 3 + IA 3). Para uma materia nova, o custo de LLM medido no rebuild do CG (93 materiais): vocab ~9 (1/unidade) + resumos de codigo 17
1532:parseavel ate o fim (CG para em 7.1.2), Gemini para voter/vocab/resumos (~100-150 chamadas por curso de 90 materiais); professor sem sinal
1537:perderam o conteudo no tutor e os 5 resumos de codigo dizem 'datatype Cor'; `exemplos.zip` (5 `.smv` do NuSMV) nao gera markdown (extensao
1600:IA 8, ES2 8, CG 17; 11:45-11:54) e a 1a rodada da B mediu com resumos NOVOS — dai SO sub 81 e as 10 mudancas do CG. Referencias: cache intacto (0
1718:Sentinela 0/8 · determinismo 8/8 (0 arquivos nao deterministicos) · suite 2319. Reprocess final com a correcao do `|`: so o IA mudou (2 linhas); os outros 7 commits
1886:sentinela 0/8; **determinismo 8/8 = 0 arquivos**. Tudo igual ao gate de 03/09: nenhuma regua regrediu com S6a-S6f.
1961:curada 199/200 conf-err 0 · 191/191 · 55/57 · motor puro +vocab 183/178/53/82 · sentinela 0/8 · determinismo 8/8 (FR estava com 4
2395:**Divida achada (nao mexida):** no reprocess dos 8 com manifest IDENTICO (sentinela 0 fora de `revisar`), o `course/COURSE_MAP.md` do ES2 reordenou a lista "Tambem cobre esta unidade" (`Roteiro2_nameserver` (+12) -> `roteiro2` (+13); `Roteiro1_introducao` perdeu o (+1)) — nao-determinismo do RENDERER (ordem de empate/set), nao do motor. Entra no corte 1 do refactor: ordenar por chave estavel e cobrir com teste de determinismo.
2525:  - **Citação por página** (padrão PageIndex): resumos/artefatos do tutor citarem
rg: src/builder/core/content_taxonomy.py: O sistema não pode encontrar o arquivo especificado. (os error 2)
rg: src/builder/routing/*.py: A sintaxe do nome do arquivo, do nome do diretório ou do rótulo do volume está incorreta. (os error 123)

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
import json
p=Path('graphify-out/graph.json');d=json.loads(p.read_text(encoding='utf-8'));ns={n['id']:n for n in d['nodes']}
for n in ns.values():
 if 'auto_map_entry_subtopic' in n.get('label',''):
  print('NODE',n)
  for e in d.get('links',d.get('edges',[])):
   if n['id'] in [e['source'],e['target']]: print('EDGE',ns.get(e['source'],{}).get('label'),ns.get(e['target'],{}).get('label'),e.get('relation'))
for f,a,b in [('docs/reports/pendencias.md',1349,1384),('src/builder/routing/resolver_apply.py',482,590)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))):print(f'{i+1}: {ls[i]}')
'@ | python -B -; rg -n 'def (_?collect_entry_unit_signals|_?score_entry_against_taxonomy_topic|_?auto_map_entry_subtopic|_?iter_content_taxonomy_topics|code_curation_signal_text)|def _entry_markdown_text_for_file_map' src; rg -n 'Pthreads|pthread|Linux|Unix|Estudo|TOPICO|RAW' docs/reports/_harness-2026-09-04/c1-3/compila_vocab_SO.log"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 535ms:[0m
NODE {'label': 'auto_map_entry_subtopic()', 'file_type': 'code', 'source_file': 'src/builder/routing/file_map.py', 'source_location': 'L172', '_callable': True, '_origin': 'ast', 'community': 22, 'community_name': 'routing/file_map.py', 'norm_label': 'auto_map_entry_subtopic()', 'id': 'src_builder_routing_file_map_auto_map_entry_subtopic'}
EDGE routing/file_map.py auto_map_entry_subtopic() contains
EDGE auto_map_entry_subtopic() collect_entry_unit_signals() calls
NODE {'label': 'test_auto_map_entry_subtopic_nao_revisao_fraca_mantem_slug()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L1884', '_callable': True, '_origin': 'ast', 'community': 50, 'community_name': 'test_file_map_unit_mapping.py', 'norm_label': 'test_auto_map_entry_subtopic_nao_revisao_fraca_mantem_slug()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_nao_revisao_fraca_mantem_slug'}
EDGE test_auto_map_entry_subtopic_nao_revisao_fraca_mantem_slug() _revisao_taxonomy() calls
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_nao_revisao_fraca_mantem_slug() contains
NODE {'label': 'test_auto_map_entry_subtopic_prefers_specific_topic_and_derives_unit()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L585', '_callable': True, '_origin': 'ast', 'community': 50, 'community_name': 'test_file_map_unit_mapping.py', 'norm_label': 'test_auto_map_entry_subtopic_prefers_specific_topic_and_derives_unit()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_prefers_specific_topic_and_derives_unit'}
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_prefers_specific_topic_and_derives_unit() contains
NODE {'label': 'test_auto_map_entry_subtopic_prefers_title_and_headings_over_late_body_mentions()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L649', '_callable': True, '_origin': 'ast', 'community': 50, 'community_name': 'test_file_map_unit_mapping.py', 'norm_label': 'test_auto_map_entry_subtopic_prefers_title_and_headings_over_late_body_mentions()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_prefers_title_and_headings_over_late_body_mentions'}
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_prefers_title_and_headings_over_late_body_mentions() contains
NODE {'label': 'test_auto_map_entry_subtopic_revisao_mono_assunto_legitima_mantem_slug()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L1866', '_callable': True, '_origin': 'ast', 'community': 50, 'community_name': 'test_file_map_unit_mapping.py', 'norm_label': 'test_auto_map_entry_subtopic_revisao_mono_assunto_legitima_mantem_slug()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_revisao_mono_assunto_legitima_mantem_slug'}
EDGE test_auto_map_entry_subtopic_revisao_mono_assunto_legitima_mantem_slug() _revisao_taxonomy() calls
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_revisao_mono_assunto_legitima_mantem_slug() contains
NODE {'label': 'test_auto_map_entry_subtopic_revisao_sem_assunto_dominante_fica_vazio()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L1841', '_callable': True, '_origin': 'ast', 'community': 50, 'community_name': 'test_file_map_unit_mapping.py', 'norm_label': 'test_auto_map_entry_subtopic_revisao_sem_assunto_dominante_fica_vazio()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_revisao_sem_assunto_dominante_fica_vazio'}
EDGE test_auto_map_entry_subtopic_revisao_sem_assunto_dominante_fica_vazio() _revisao_taxonomy() calls
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_revisao_sem_assunto_dominante_fica_vazio() contains
NODE {'label': 'test_auto_map_entry_subtopic_uses_heading_enriched_alias_for_logic_propositional()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L703', '_callable': True, '_origin': 'ast', 'community': 50, 'community_name': 'test_file_map_unit_mapping.py', 'norm_label': 'test_auto_map_entry_subtopic_uses_heading_enriched_alias_for_logic_propositional()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_uses_heading_enriched_alias_for_logic_propositional'}
EDGE test_auto_map_entry_subtopic_uses_heading_enriched_alias_for_logic_propositional() _build_content_taxonomy() calls
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_uses_heading_enriched_alias_for_logic_propositional() contains
NODE {'label': 'test_auto_map_entry_subtopic_exact_tie_returns_no_slug()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L765', '_callable': True, '_origin': 'ast', 'community': 691, 'community_name': '_tie_taxonomy', 'norm_label': 'test_auto_map_entry_subtopic_exact_tie_returns_no_slug()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_exact_tie_returns_no_slug'}
EDGE test_auto_map_entry_subtopic_exact_tie_returns_no_slug() _tie_taxonomy() calls
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_exact_tie_returns_no_slug() contains
NODE {'label': 'test_auto_map_entry_subtopic_zero_score_returns_no_slug()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L785', '_callable': True, '_origin': 'ast', 'community': 691, 'community_name': '_tie_taxonomy', 'norm_label': 'test_auto_map_entry_subtopic_zero_score_returns_no_slug()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_zero_score_returns_no_slug'}
EDGE test_auto_map_entry_subtopic_zero_score_returns_no_slug() _tie_taxonomy() calls
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_zero_score_returns_no_slug() contains
NODE {'label': 'test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L1904', '_callable': True, '_origin': 'ast', 'community': 703, 'community_name': 'test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide', 'norm_label': 'test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide'}
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide() contains
EDGE Short-vocab (2026-09-01, fenomeno do holdout FR): o plano de redes so usa… test_auto_map_entry_subtopic_sigla_consagrada_pelo_plano_decide() rationale_for
NODE {'label': 'test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total()', 'file_type': 'code', 'source_file': 'tests/test_file_map_unit_mapping.py', 'source_location': 'L1954', '_callable': True, '_origin': 'ast', 'community': 704, 'community_name': 'test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total', 'norm_label': 'test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total()', 'id': 'tests_test_file_map_unit_mapping_test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total'}
EDGE test_file_map_unit_mapping.py test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total() contains
EDGE Artefato de slugify (2026-09-01, holdout FR): "TCP/IP" vira "tcpip" no slug —… test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total() rationale_for

FILE docs/reports/pendencias.md
1349: ## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3 (RESUMOS DE CODIGO) MEDIDA: ABLACAO E SUBSTITUTO DETERMINISTICO (06/09, sessao 6; DECISAO DO USER)
1350: **Pedido do user:** "quero o motor o mais automatico possivel, LLM para 3 camadas fica pesado, queria deixar no maximo duas"; "nao quero ficar criando
1351: novas rotas para o motor". **Peso medido no produto (8 tutores):** vocab = 1 compilacao por curso · resumos de codigo = 85 (1 por arquivo/zip, cache por
1352: hash, so re-roda se o arquivo mudar) · votos = 205 (1 por material incerto, cache). Curso novo do tamanho do CG: 1 + 17 + 42.
1353: **Ablacao da camada 3 (`c1-3/shim_codigo.py {sem|determ} {puro|holdout}`, copias, tripwire, 0 chamadas; motor puro + vocab + propagacao):**
1354: | regime | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
1355: |---|---|---|---|---|---|
1356: | COM resumos do Gemini (referencia, `b_prop_*.log`) | 186 | 183 | 53 | **87** (83 primario) | 31 |
1357: | SEM resumos (`code_curation.json` vazio, `codigo_sem_*.log`) | 186 | 183 | 53 | **71** (67) | 31 |
1358: | substituto deterministico v1: zip/ipynb crus (`codigo_determ_*.log`) | 186 | 183 | 53 | 79 (75) | 31 |
1359: | substituto deterministico v2: os `.md` que o motor JA gera para codigo/zip = o mesmo bundle que o Gemini recebe (`codigo_determ2_*.log`) | 186 | 183 | 53 | 78 (74) | 31 |
1360: **Leitura:** a camada 3 so sustenta a SUBUNIDADE (+16 sobre nada, +8 sobre o melhor substituto); bloco, unidade, cobertura e holdout nao a sentem.
1361: Os 8 que SO o resumo do Gemini acerta (listados na copia, `winner_score`/`empate`): SO threads x3 (empate exato 0,11: 'pthread' esta no vocab mas
1362: empata; o Gemini injeta 'gerenciamento de processos'/'programacao concorrente') · IA perceptron x4 + mlp-xor (na copia 'perceptron' NAO e alias de
1363: `modelos-preditivos`, so 'MultiLayer Perceptron'; o notebook tem 'Generalizacao', alias de `introducao`; o Gemini injeta 'Perceptron'/'Classificacao')
1364: · ES2 roteiro1 (zip Spring: o codigo so tem 'currency/exchange'; o Gemini injeta 'Microsservicos'). Ou seja: o resumo vale pelo VOCABULARIO DE
1365: CATEGORIA que o codigo nao contem — e um remendo da camada 2 (vocab), nao sinal proprio do codigo. Os outros 6 erros sao os mesmos com ou sem Gemini.
1366: **Decisao do user (aberta): qual camada cortar.** Recomendacao com numero: cortar a 3 (menor ganho das tres: +8 sub; vocab vale +57 sub/+10 unidade;
1367: voter vale +7 bloco/+4 holdout) e trocar o PRODUTOR de `code_curation.json` pelo deterministico v2 — mesma rota (`code_curation_signal_text` +
1368: `entry["concepts"]`), produtor diferente, 0 rotas novas; custo -8/93 na subunidade, 0 no resto. Para nao perder os 8 mantendo duas camadas: a
1369: compilacao do vocab (camada 2) passar a ver o bundle de codigo (`vocabulary_compile` le `_entry_markdown_text_for_file_map`, que para zip devolve
1370: vazio) — mesma chamada, mais insumo; exige Gemini para remedir -> decisao 3 do handoff.
1371: **"% de similaridade vocab x nome do material" (pergunta do user; `c1-3/simula_similaridade_nome.py`, 93 pontuaveis, 0 chamadas):** Jaccard de tokens
1372: do nome (title + label) x label do plano (sem LLM): limiar 0,5 -> 9 certos 0 errados 84 sem atribuicao; 0,2 -> 16/1/76. x label + aliases do vocab LLM:
1373: 0,5 -> 27/0/66; 0,3 -> 46/3/44; 0,2 -> 63/6/24. `difflib` 0,3 -> 46 certos 41 errados. O scorer do motor (mesma ideia, texto inteiro + pesos): 87 com
1374: vocab, 30 sem. **Leitura:** faz sentido e JA E o que o scorer faz (sobreposicao de tokens material x vocab, por topico); um indice explicito nao
1375: acrescenta informacao — o teto e o vocabulario, nao a funcao de similaridade. Nenhuma rota nova proposta.
1376: 
1377: ## CONTRIBUICAO POR CAMADA (06/09, pedido do user: "os numeros obtidos sem LLM" antes de uma materia 100% nova)
1378: | camada (copias, tripwire, 0 chamadas) | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
1379: |---|---|---|---|---|---|
1380: | 100% sem LLM: motor puro SEM vocab compilado, SEM propagacao (`b_semvocab_semprop_puro.log`) | 187 conf-err 1 | 173 (ES2 18/28) | 54 | **30 (32%)** | 31 |
1381: | idem COM propagacao por headings (`b_semvocab_puro.log`) | 187 | 173 | 54 | 26 — **regride 4**: sem vocab as sementes 'confiantes' erram e a propagacao amplifica | 31 |
1382: | + vocab compilado por LLM (cache; ~1 chamada por unidade) | 186 | 183 | 53 | **87** | 31 |
1383: | + voter com cache (~35% dos materiais votados) = AUTOMATICA v2 | **193 conf-err 0** | **185** | 53 | 87 | **35** |
1384: | + curadoria (pinos, glossario manual) = produto | 198 | 191 | 55 | (IA 39/39) | 35 |

FILE src/builder/routing/resolver_apply.py
482:         )
483:         if cobertura:
484:             entry["coverage_units"] = cobertura
485:         else:
486:             entry.pop("coverage_units", None)
487: 
488:         # 2026-08-21: o bloco que manda na unidade e o TEMPORAL (ancora:
489:         # manual > temporal_block_id > computed), o mesmo que a regua mede —
490:         # nao o computed_block_id do scorer de conceito. Esta fase roda DEPOIS
491:         # da camada temporal (pedagogical_regeneration) justamente para ve-lo.
492:         # Bloco sem unit_slug (avaliacao/revisao/overview) herda do vizinho de
493:         # conteudo. Medido: scorer 130/188 -> bloco temporal + heranca 178/188.
494:         temporal_id = resolve_temporal_block(entry, blocks)
495:         block_unit, vizinho = unit_of_block_or_neighbor(temporal_id, blocks)
496:         blk = next((b for b in blocks
497:                     if str(b.get("id") or "") == temporal_id or str(b.get("block_uuid") or "") == temporal_id), None)
498:         block_ref = str((blk or {}).get("id") or temporal_id or block_id)
499: 
500:         # Pino manual direto do entry: computed_block_method pode ter sido
501:         # trocado p/ consensus/llm_only pelo attach ANTES deste apply — o
502:         # method nao e prova de pino (review final F4, I2).
503:         _pin = str(entry.get("manual_timeline_block_id") or "").strip()
504:         block_is_manual = bool(_pin) and _pin in {temporal_id, block_id, str((blk or {}).get("id") or ""),
505:                                                   str((blk or {}).get("block_uuid") or "")}
506: 
507:         reconciled, suffix, conflict = reconcile_unit_with_block(
508:             computed_unit_slug=gated_unit,
509:             unit_confidence=float(unit_confidence),
510:             computed_block_id=block_ref if block_unit else "",
511:             block_confidence=1.0,
512:             block_unit_slug=block_unit,
513:             block_is_manual=block_is_manual,
514:             has_manual_unit=bool(manual_unit),
515:             unit_is_explicit=any(str(r).startswith("unidade-explicita=") for r in (unit_reasons or [])),
516:         )
517:         if vizinho and reconciled == block_unit and not manual_unit:
518:             suffix = list(suffix) + [f"herdada_do_vizinho={vizinho}"]
519:         if suffix:
520:             unit_reasons = list(unit_reasons) + suffix
521: 
522:         entry["computed_unit_slug"] = reconciled
523:         entry["unit_match_reasons"] = unit_reasons
524:         entry["unit_match_confidence"] = unit_confidence
525:         entry["unit_block_conflict"] = conflict
526: 
527:         tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("unit:")]
528:         if reconciled:
529:             tags.append(f"unit:{reconciled}")
530:         entry["auto_tags"] = tags
531: 
532:         # --- Subunit (rota de tópico, restrita à unidade FINAL reconciliada) ---
533:         manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
534:         regra_meta = str(cobertura[0].get("rule") or "") if cobertura else ""
535:         if manual_subunit:
536:             preferred_topic_slug = manual_subunit
537:             best_subunit_slug = manual_subunit
538:             subunit_reasons = ["manual"]
539:             subunit_confidence = 1.0
540:         elif regra_meta in META_COVERAGE_RULES:
541:             # Espelho da regra A da cobertura (2026-08-31): doc meta descreve o
542:             # curso INTEIRO — subunit vazia e a resposta honesta (SO plano/
543:             # programa caiam em evolucao-historica por vocabulario da ementa).
544:             preferred_topic_slug = ""
545:             best_subunit_slug = ""
546:             subunit_reasons = [f"meta-material:{regra_meta}"]
547:             subunit_confidence = 0.0
548:         else:
549:             # Mesmo texto enriquecido da rota de unidade — montado uma vez só.
550:             topic_match = auto_map_entry_subtopic_fn(
551:                 entry, content_taxonomy, texto_para_unidade, winning_unit_slug=reconciled,
552:             )
553:             passe1.append((entry, texto_para_unidade, reconciled, topic_match))
554:             best_subunit_slug = str(getattr(topic_match, "topic_slug", "") or "")
555:             subunit_reasons = list(getattr(topic_match, "reasons", []))
556:             subunit_confidence = float(getattr(topic_match, "confidence", 0.0))
557:             preferred_topic_slug = ""
558:             if (
559:                 topic_match.topic_slug
560:                 and not topic_match.ambiguous
561:                 and topic_match.confidence >= T.SUBUNIT_TAG
562:             ):
563:                 preferred_topic_slug = topic_match.topic_slug
564: 
565:         entry["computed_subunit_slug"] = best_subunit_slug
566:         entry["subunit_match_reasons"] = subunit_reasons
567:         entry["subunit_match_confidence"] = subunit_confidence
568: 
569:         tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
570:         if preferred_topic_slug:
571:             tags.append(f"subunit:{preferred_topic_slug}")
572:         entry["auto_tags"] = tags
573: 
574:     propagar_vocabulario_por_headings(
575:         passe1, content_taxonomy, auto_map_entry_subtopic_fn,
576:         conf_min=T.SUBUNIT_PROPAG_CONF, min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX,
577:     )
578: 
579:     # `revisar` (Fase 0, 02/09): fila de revisao, derivada do que ficou gravado,
580:     # em TODO material — inclusive os que o loop acima pulou por nao ter bloco
581:     # (justamente os "duvida"). Nao-material nao tem eixo: campo some.
582:     for entry in entries:
583:         if _is_material(entry):
584:             entry["revisar"] = revisar_de(entry)
585:         else:
586:             entry.pop("revisar", None)
587:     return entries
src\builder\core\code_summarization.py:292:def code_curation_signal_text(curation_entry: dict) -> str:
src\builder\extraction\entry_signals.py:106:def collect_entry_unit_signals(entry: dict, markdown_text: str) -> Dict[str, str]:
src\builder\artifacts\navigation.py:84:def _entry_markdown_text_for_file_map(root_dir: Optional[Path], entry: dict) -> str:
src\builder\timeline\index.py:1722:def _iter_content_taxonomy_topics(taxonomy: dict) -> List[dict]:
src\builder\timeline\index.py:1797:def _score_entry_against_taxonomy_topic(signals: dict, topic: dict, *, stem_fallback: bool = False) -> float:
src\builder\routing\file_map.py:172:def auto_map_entry_subtopic(
19:  1.3 Estudo de casos: ['Linux', 'Unix', 'Unix/Linux', 'Linux kernel map']
23:  3.4 Estudo de casos: ['Linux Threads', 'S.O. Solaris', 'Pthreads', 'pthread_create', 'pthread_exit', 'pthread_join', 'pthread_self', 'threads em C']
35:  7.6 Estudo de casos: ['Kernel UNIX']

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[31m exited 1 in 96027ms:[0m
[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command "rg -n '_auto_map_entry_subtopic|auto_map_entry_subtopic|_content_taxonomy|build_content_taxonomy' docs/reports/_harness-2026-09-04/c1-3 -g '*.py' | Select-Object -First 65; rg -n '"'^def '"' src/builder/extraction/content_taxonomy.py src/builder/routing/subunit_propagation.py; Get-ChildItem .ablacao/Sistemas-Operacionais-Tutor/course -Name; Get-Content docs/reports/_harness-2026-09-04/c1-3/compila_vocab_SO.log; Get-Content docs/reports/_harness-2026-09-04/c1-3/compila_vocab_IA.log"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f,a,b in [('src/builder/timeline/index.py',1722,1980),('src/builder/core/code_summarization.py',292,340),('src/builder/extraction/entry_signals.py',1,270),('src/builder/artifacts/navigation.py',84,157)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))): print(f'{i+1}: {ls[i]}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 256ms:[0m

FILE src/builder/timeline/index.py
1722: def _iter_content_taxonomy_topics(taxonomy: dict) -> List[dict]:
1723:     topics: List[dict] = []
1724:     seen = set()
1725:     # A2: genericos de unidade POR CURSO (df sobre as unidades da taxonomia), carimbados em cada
1726:     # topico para o scorer de subunidade; modo em UNIT_GENERIC_MODE (lista = constante de antes).
1727:     from src.builder.text.stopwords import resolve_unit_generic_tokens, short_vocab_from_topic_labels
1728:     _units = (taxonomy or {}).get("units", []) or []
1729:     # Short-vocab POR CURSO (2026-09-01): tokens curtos consagrados pelos labels
1730:     # ("Protocolo TCP" do FR consagra "tcp") — carimbado como generic_tokens.
1731:     _short_vocab = sorted(short_vocab_from_topic_labels([
1732:         _normalize_match_text(str(t.get("label") or ""))
1733:         for u in _units for t in (u.get("topics") or [])
1734:     ]))
1735:     _resolved = resolve_unit_generic_tokens(
1736:         [(str(u.get("title") or u.get("slug") or "").replace("-", " "),
1737:           [str(t.get("label") or "") for t in (u.get("topics") or [])]) for u in _units],
1738:         UNIT_GENERIC_TOKENS, course_name=str((taxonomy or {}).get("course_name") or (taxonomy or {}).get("course") or ""))
1739:     _generic = sorted(_resolved) if _resolved is not None else None
1740:     for unit in (taxonomy or {}).get("units", []) or []:
1741:         unit_slug = _normalize_unit_slug(str(unit.get("slug", "") or unit.get("title", "") or ""))
1742:         unit_title = _collapse_ws(str(unit.get("title", "") or ""))
1743:         for topic in unit.get("topics", []) or []:
1744:             topic_slug = slugify(str(topic.get("slug", "") or ""))
1745:             topic_label = _collapse_ws(str(topic.get("label", "") or ""))
1746:             if not topic_slug or not topic_label:
1747:                 continue
1748:             dedupe_key = (unit_slug, topic_slug)
1749:             if dedupe_key in seen:
1750:                 continue
1751:             seen.add(dedupe_key)
1752:             topics.append(
1753:                 {
1754:                     "unit_slug": unit_slug,
1755:                     "unit_title": unit_title,
1756:                     "topic_slug": topic_slug,
1757:                     "topic_label": topic_label,
1758:                     "topic_code": str(topic.get("code", "") or ""),
1759:                     "kind": str(topic.get("kind", "") or "topic"),
1760:                     "generic_tokens": _generic,
1761:                     "short_vocab": _short_vocab,
1762:                     "aliases": [str(alias) for alias in (topic.get("aliases", []) or []) if _collapse_ws(str(alias))],
1763:                 }
1764:             )
1765:     return topics
1766: 
1767: 
1768: _LABEL_SEP_RE = re.compile(r"\s+e\s+|\s+ou\s+|:|\(|\)|/|,|\s+-\s+", re.I)
1769: _LABEL_NUM_RE = re.compile(r"^\d+(\.\d+)*\s+")
1770: _LABEL_HEAD_RE = re.compile(r"^(\w+)\s+(de|da|do|das|dos|para|em)\s+(.+)$", re.I)
1771: from src.builder.text.stopwords import LABEL_PART_STOP as _LABEL_STOP
1772: 
1773: 
1774: def _label_parts(label: str, generic_heads: set) -> List[str]:
1775:     """Partes de um rotulo composto: 'Bezier e Algoritmo de Casteljau' -> ['Bezier', 'Algoritmo de Casteljau'];
1776:     'Algoritmos de Geometria Computacional' -> ['Geometria Computacional'] quando 'algoritmos' e cabeca de >= 2
1777:     rotulos do curso (cabeca generica). Separadores: ' e ', ' ou ', ':', parenteses, '/', ',', ' - '.
1778:     Consumidor: `resolver_apply.propagar_vocabulario_por_headings` (2a passada da subunidade, com teto de df)."""
1779:     base = _LABEL_NUM_RE.sub("", label or "").strip()
1780:     out: List[str] = []
1781:     for part in _LABEL_SEP_RE.split(base):
1782:         part = (part or "").strip(" .;")
1783:         if part and _normalize_match_text(part) != _normalize_match_text(base) and _specific_tokens(part):
1784:             out.append(part)
1785:     m = _LABEL_HEAD_RE.match(base)
1786:     if m and _normalize_match_text(m.group(1)) in generic_heads and _specific_tokens(m.group(3)):
1787:         out.append(m.group(3).strip())
1788:     return out
1789: 
1790: 
1791: def _specific_tokens(text: str) -> set:
1792:     return {tok for tok in _normalize_match_text(text or "").split() if len(tok) >= 4 and tok not in _LABEL_STOP}
1793: 
1794: 
1795: 
1796: 
1797: def _score_entry_against_taxonomy_topic(signals: dict, topic: dict, *, stem_fallback: bool = False) -> float:
1798:     title_text = signals.get("title_text", "")
1799:     markdown_headings_text = signals.get("markdown_headings_text", "")
1800:     markdown_lead_text = signals.get("markdown_lead_text", "")
1801:     markdown_text = signals.get("markdown_text", "")
1802:     category_text = signals.get("category_text", "")
1803:     manual_tags_text = signals.get("manual_tags_text", "")
1804:     auto_tags_text = signals.get("auto_tags_text", "")
1805:     legacy_tags_text = signals.get("legacy_tags_text", "")
1806:     raw_text = signals.get("raw_text", "")
1807:     label = _collapse_ws(str(topic.get("topic_label", "") or ""))
1808:     topic_slug = _collapse_ws(str(topic.get("topic_slug", "") or ""))
1809:     aliases = [str(alias) for alias in (topic.get("aliases", []) or []) if _collapse_ws(str(alias))]
1810: 
1811:     if not label and not topic_slug and not aliases:
1812:         return 0.0
1813: 
1814:     score = 0.0
1815:     exact_hits = 0
1816:     # Dedupe de frases por forma normalizada (2026-09-01): label cujo slug vira
1817:     # a MESMA frase ("Integração contínua (CI)" -> "integracao continua ci")
1818:     # contava label+slug (1.65x) por campo — inflacao estrutural a favor de
1819:     # labels "limpos" contra labels com meta-palavra ("Conceito de DevOps" so
1820:     # casa via alias 0.82x). Mesma frase conta UMA vez, no maior fator
1821:     # (label 1.0 > alias 0.82 > slug 0.65).
1822:     phrases: dict = {}
1823:     if label:
1824:         phrases[_normalize_match_text(label)] = (1.0, label)
1825:     for alias in aliases:
1826:         alias_norm = _normalize_match_text(alias)
1827:         if alias_norm and (alias_norm not in phrases or phrases[alias_norm][0] < 0.82):
1828:             phrases[alias_norm] = (0.82, alias_norm)
1829:     if topic_slug:
1830:         slug_phrase = topic_slug.replace("-", " ")
1831:         slug_norm = _normalize_match_text(slug_phrase)
1832:         if slug_norm and slug_norm not in phrases:
1833:             phrases[slug_norm] = (0.65, slug_phrase)
1834:     phrases.pop("", None)
1835:     for text, weight in [
1836:         (markdown_headings_text, 4.4),
1837:         (title_text, 3.8),
1838:         (markdown_lead_text, 2.8),
1839:         (manual_tags_text, 3.0),
1840:         (markdown_text, 1.1),
1841:         (auto_tags_text, 0.22),
1842:         (legacy_tags_text, 0.15),
1843:         (raw_text, 0.9),
1844:     ]:
1845:         for factor, phrase in phrases.values():
1846:             if _matches_normalized_phrase(text, phrase, stem_fallback):
1847:                 score += weight * factor
1848:                 exact_hits += 1
1849: 
1850:     _generic = set(topic.get("generic_tokens") or []) or UNIT_GENERIC_TOKENS  # A2: por curso
1851:     # Short-vocab (2026-09-01): sigla consagrada por LABEL do curso conta como
1852:     # token apesar de len<4 — o plano do FR so usa siglas ("Protocolo TCP") e o
1853:     # corte deixava o scorer decidir por migalhas (02-modelos conf 0.92 errado).
1854:     _short = set(topic.get("short_vocab") or [])
1855: 
1856:     def _conta(token: str) -> bool:
1857:         return len(token) >= 4 or token in _short
1858: 
1859:     topic_tokens = {
1860:         token
1861:         for token in _normalize_match_text(label).split()
1862:         if _conta(token) and token not in _generic
1863:     }
1864:     for alias in aliases:
1865:         topic_tokens.update(
1866:             token
1867:             for token in _normalize_match_text(alias).split()
1868:             if _conta(token) and token not in _generic
1869:         )
1870:     if topic_slug:
1871:         # Artefato de slugify (2026-09-01, holdout FR): "TCP/IP" -> "tcpip",
1872:         # "cliente/servidor" -> "clienteservidor". Token que o slug INVENTA
1873:         # fundindo tokens adjacentes do label/alias nunca existe no texto
1874:         # normalizado ("tcp ip") e envenenava o bonus de cobertura-total
1875:         # (02-modelos: 4/5 cobertos, o 5o era o proprio artefato — perdia
1876:         # para o label-aspirador com 2/2 migalhas). Escopo medido nos 8
1877:         # cursos: 2 topicos, ambos FR.
1878:         _seqs = [_normalize_match_text(label).split()] + [
1879:             _normalize_match_text(alias).split() for alias in aliases
1880:         ]
1881:         _proprios = {tok for seq in _seqs for tok in seq}
1882:         _fusoes = {
1883:             "".join(seq[i:i + j])
1884:             for seq in _seqs
1885:             for j in (2, 3)
1886:             for i in range(len(seq) - j + 1)
1887:         } - _proprios
1888:         topic_tokens.update(
1889:             token
1890:             for token in _normalize_match_text(topic_slug.replace("-", " ")).split()
1891:             if _conta(token) and token not in _generic and token not in _fusoes
1892:         )
1893: 
1894:     # Token curto consagrado so conta vindo de campo FORTE (heading/titulo/
1895:     # tags/nome de arquivo — onde a sigla e escolha deliberada do professor):
1896:     # sigla no heading e o caso FR; sigla solta no corpo/lead e ruido em
1897:     # qualquer texto do dominio (em doc curto o lead engole o corpo inteiro,
1898:     # e mencao tardia nao pode virar vencedor).
1899:     _campos = [
1900:         (markdown_headings_text, True),
1901:         (title_text, True),
1902:         (markdown_lead_text, False),
1903:         (manual_tags_text, True),
1904:         (markdown_text, False),
1905:         (auto_tags_text, True),
1906:         (legacy_tags_text, False),
1907:         (raw_text, True),
1908:     ]
1909:     signal_tokens = {
1910:         token
1911:         for text, forte in _campos
1912:         for token in text.split()
1913:         if len(token) >= 4 or (forte and token in _short)
1914:     }
1915:     overlap = topic_tokens & signal_tokens
1916:     if not topic_tokens:
1917:         # Topico cujo vocabulario inteiro esta em UNIT_GENERIC_TOKENS (3 no MF:
1918:         # "Linguagens de Especificacao e Logicas", os dois "Softwares de Suporte
1919:         # a Verificacao Formal de ..."). Sem este guard cai no ramo seguinte com
1920:         # `0 >= 0` e ganha +1.4 INCONDICIONAL em toda entry avaliada.
1921:         pass
1922:     elif len(topic_tokens) == 1:
1923:         if overlap:
1924:             score += 0.9
1925:     elif len(overlap) >= len(topic_tokens):
1926:         score += 1.4 + (0.22 * len(overlap))
1927:     elif len(overlap) >= 2:
1928:         score += 0.9 + (0.18 * len(overlap))
1929:     elif len(overlap) == 1:
1930:         score += 0.25
1931: 
1932:     if category_text in {"listas", "gabaritos"} and overlap:
1933:         score += 0.08
1934:     if str(topic.get("kind", "") or "") == "subtopic":
1935:         score += 0.04
1936: 
1937:     if exact_hits == 0 and score > 0.0:
1938:         score *= 0.72
1939:     if exact_hits == 0 and len(overlap) <= 1:
1940:         score *= 0.68
1941:     if auto_tags_text and exact_hits == 0 and len(overlap) <= 1:
1942:         score *= 0.88
1943:     if legacy_tags_text and exact_hits == 0:
1944:         score *= 0.9
1945:     return score
1946: 
1947: 
1948: def _build_timeline_block_topic_signals(block: Dict[str, object]) -> dict:
1949:     rows = block.get("rows", []) or []
1950:     row_texts = []
1951:     raw_texts = []
1952:     for row in rows:
1953:         text = _collapse_ws(str(row.get("content", "")))
1954:         if not text:
1955:             continue
1956:         normalized = _normalize_match_text(text)
1957:         if normalized:
1958:             row_texts.append(normalized)
1959:         raw_texts.append(text)
1960: 
1961:     topic_text = _normalize_match_text(str(block.get("topic_text", "") or ""))
1962:     alias_text = _normalize_match_text(" ".join(str(alias) for alias in (block.get("aliases", []) or [])))
1963:     combined_text = " ".join(row_texts)
1964:     return {
1965:         "title_text": topic_text,
1966:         "markdown_text": combined_text,
1967:         "category_text": "",
1968:         "tags_text": alias_text,
1969:         "raw_text": _normalize_match_text(" ".join(raw_texts)),
1970:     }
1971: 
1972: 
1973: def _score_timeline_block_against_taxonomy_topic(block: Dict[str, object], topic: dict) -> float:
1974:     signals = _build_timeline_block_topic_signals(block)
1975:     score = _score_entry_against_taxonomy_topic(signals, topic)
1976:     kind = str(topic.get("kind", "") or "topic")
1977:     if kind == "subtopic":
1978:         score += 0.18
1979:     return score
1980: 

FILE src/builder/core/code_summarization.py
292: def code_curation_signal_text(curation_entry: dict) -> str:
293:     """Texto markdown-equivalente a partir do resumo de código curado (Gemini).
294: 
295:     GERAL (qualquer cadeira): zips/códigos não têm `.md` convertido nem
296:     descrição de imagem, então o scorer de subunidade só via título + auto_tags
297:     e empatava no ruído. Este texto reaproveita o resumo que já existe em
298:     `code_curation.json` (consumido pelo matcher de BLOCO) como sinal léxico
299:     para a SUBUNIDADE. Formata o `inferred_title` como heading `#` (campo de
300:     maior peso, 4.4) e conceitos/summary/linguagem como corpo. Retorna "" se
301:     não houver resumo utilizável (no-op para entries sem curadoria de código).
302:     """
303:     summary = curation_entry.get("summary") if isinstance(curation_entry, dict) else None
304:     if not isinstance(summary, dict):
305:         return ""
306: 
307:     title = str(summary.get("inferred_title") or "").strip()
308:     prose = str(summary.get("summary") or "").strip()
309:     language = str(summary.get("language") or "").strip()
310:     concepts = [
311:         str(c).strip()
312:         for c in (summary.get("concepts") or [])
313:         if str(c).strip()
314:     ]
315: 
316:     parts: list[str] = []
317:     if title:
318:         parts.append(f"# {title}")
319:     if prose:
320:         parts.append(prose)
321:     if concepts:
322:         parts.append("Conceitos: " + ", ".join(concepts))
323:     if language:
324:         parts.append(f"Ferramenta: {language}")
325:     return "\n\n".join(parts)
326: 
327: 
328: def load_code_curation(repo_dir: Path) -> dict:
329:     path = repo_dir / "code_curation.json"
330:     if not path.exists():
331:         return {"version": 1, "entries": {}}
332:     try:
333:         return json.loads(path.read_text(encoding="utf-8"))
334:     except Exception as exc:
335:         logger.warning("Falha ao ler %s (%s: %s) — curadoria de código vazia nesta rodada", path, type(exc).__name__, exc)
336:         return {"version": 1, "entries": {}}
337: 
338: 
339: def write_code_curation(repo_dir: Path, data: dict) -> None:
340:     path = repo_dir / "code_curation.json"

FILE src/builder/extraction/entry_signals.py
1: from __future__ import annotations
2: 
3: from pathlib import Path
4: from typing import Dict, List
5: 
6: from src.builder.extraction.content_taxonomy import (
7:     _extract_markdown_headings,
8:     extract_markdown_lead_text,
9: )
10: from src.builder.extraction.image_markdown import _IMAGE_DESC_BLOCK_RE, _IMAGE_DESC_ORPHANS_RE
11: from src.builder.routing.thresholds import TOOL_EXTENSIONS
12: from src.builder.text.normalize import (  # noqa: F401  (re-export)
13:     normalize_match_text,
14:     split_camel_case,
15: )
16: 
17: 
18: def score_text_against_row(
19:     source_text: str,
20:     row_tokens: List[str],
21:     *,
22:     weight: float = 1.0,
23:     token_weights: Dict[str, float] | None = None,
24: ) -> float:
25:     # S2 (P4): token_weights (token -> peso efetivo, cf.
26:     # file_map.block_token_weights) multiplica a contribuição POR row_token —
27:     # tokens raros entre os candidatos pesam mais. None = peso 1.0 para todos
28:     # (comportamento anterior EXATO).
29:     if not source_text or not row_tokens:
30:         return 0.0
31: 
32:     source_tokens = [tok for tok in source_text.split() if len(tok) >= 4]
33:     score = 0.0
34:     for source_token in source_tokens:
35:         for row_token in row_tokens:
36:             token_weight = 1.0 if token_weights is None else float(token_weights.get(row_token, 1.0))
37:             if source_token == row_token:
38:                 score += 1.0 * weight * token_weight
39:             elif source_token in row_token or row_token in source_token:
40:                 score += 0.45 * weight * token_weight
41:             elif len(source_token) >= 5 and len(row_token) >= 5 and source_token[:5] == row_token[:5]:
42:                 score += 0.2 * weight * token_weight
43:     return score
44: 
45: 
46: def entry_image_source_dirs(root_dir: Path, entry: dict) -> List[Path]:
47:     dirs: List[Path] = []
48:     entry_id = str(entry.get("id") or "").strip()
49:     if entry_id:
50:         dirs.append(root_dir / "staging" / "assets" / "inline-images" / entry_id)
51:     images_dir = entry.get("images_dir")
52:     if images_dir:
53:         dirs.append(root_dir / images_dir)
54:     rendered_pages_dir = entry.get("rendered_pages_dir")
55:     if rendered_pages_dir:
56:         dirs.append(root_dir / rendered_pages_dir)
57:     return dirs
58: 
59: 
60: def _merge_manual_and_auto_tags(
61:     manual_tags: List[str],
62:     auto_tags: List[str],
63:     *,
64:     fallback_tags: str = "",
65:     limit: int = 6,
66: ) -> str:
67:     fallback_parts = [part.strip() for part in str(fallback_tags or "").replace(",", ";").split(";") if part.strip()]
68:     merged: List[str] = []
69:     seen = set()
70:     for tag in [*manual_tags, *auto_tags, *fallback_parts]:
71:         cleaned = str(tag or "").strip()
72:         if not cleaned or cleaned in seen:
73:             continue
74:         seen.add(cleaned)
75:         merged.append(cleaned)
76:         if len(merged) >= limit:
77:             break
78:     return "; ".join(merged)
79: 
80: 
81: # Prefixos que o PROPRIO motor escreve (`resolver_apply` espelha o que ele
82: # computou). Realimentar o scorer com eles faz o sistema re-eleger a resposta
83: # anterior: medido 2026-08-19 rodando o mesmo scorer sobre os manifests antes e
84: # depois de um reprocess — 131 -> 129 acertos, toda a perda no MF, sem ninguem
85: # ter mudado nada. `topico:`/`ferramenta:`/`tipo:` NAO entram aqui: vem do
86: # catalogo/taxonomia, nao da atribuicao.
87: _PREFIXOS_ESPELHO_DO_MOTOR = ("unit:", "subunit:", "bloco:", "block:")
88: 
89: 
90: def _sem_eco(tags: List[str]) -> List[str]:
91:     return [t for t in tags if not str(t).lower().startswith(_PREFIXOS_ESPELHO_DO_MOTOR)]
92: 
93: 
94: def texto_para_score(markdown_text: str) -> str:
95:     """Markdown sem os blocos de DESCRICAO DE IMAGEM. A descricao serve ao ALUNO (contexto da figura no tutor) e fica no
96:     arquivo; ela nao deve pontuar. Medido em 07/09: a caption generica do Datalab, em ingles ("A 4x4 grid showing the
97:     result of erosion", "Logos for GRU and PUCRS"), entra no vocabulario propagado do CURSO — os materiais confiantes doam
98:     alias — e desvia a subunidade de materiais que nem tem imagem. Ablando os blocos: +2 materiais 100% certos, subunidade
99:     193 -> 195/233, erro confiante 19 -> 18, fila 91 -> 89 (`c1-3/ablate_descricoes.log`)."""
100:     texto = str(markdown_text or "")
101:     if "IMAGE_DESCRIPTION" not in texto:
102:         return texto
103:     return _IMAGE_DESC_ORPHANS_RE.sub("\n", _IMAGE_DESC_BLOCK_RE.sub("", texto))
104: 
105: 
106: def collect_entry_unit_signals(entry: dict, markdown_text: str) -> Dict[str, str]:
107:     markdown_text = texto_para_score(markdown_text)
108:     manual_tags = [str(tag).strip() for tag in (entry.get("manual_tags") or []) if str(tag).strip()]
109:     auto_tags = [str(tag).strip() for tag in (entry.get("auto_tags") or []) if str(tag).strip()]
110:     # Lista SEM eco: so o que vira TEXTO de score. A lista crua segue inteira
111:     # para `tool_values` e para quem le auto_tags fora daqui.
112:     auto_tags_sem_eco = _sem_eco(auto_tags)
113:     # S4 (P4): valores das auto_tags `ferramenta:` em campo próprio.
114:     # ATENCAO: o comentario antigo dizia que "o scorer de bloco (file_map,
115:     # TOOL_TOKENS) filtra quais sao ferramentas de verdade". `TOOL_TOKENS` NAO
116:     # existe em `src/` (so sobrevivia num .pyc stale) — **nada filtra esta lista**.
117:     # Ver B-9 em pendencias.md; o vocabulario de `ferramenta:` e auto-inferido do
118:     # proprio corpus (B-1) e por isso vem sujo.
119:     tool_values = [
120:         tag.split(":", 1)[1].strip()
121:         for tag in auto_tags
122:         if tag.lower().startswith("ferramenta:")
123:     ]
124:     # S4b (P4): ferramenta também pela EXTENSÃO do arquivo fonte (.thy ->
125:     # isabelle, .dfy -> dafny) — os .thy do manifest real não trazem
126:     # ferramenta:isabelle nas auto_tags. União dos dois sinais, dedupada.
127:     for field in ("source_path", "raw_target"):
128:         suffix = Path(str(entry.get(field, "") or "")).suffix.lower()
129:         ext_tool = TOOL_EXTENSIONS.get(suffix)
130:         if ext_tool and ext_tool not in tool_values:
131:             tool_values.append(ext_tool)
132:     legacy_tags = [
133:         part.strip()
134:         for part in str(entry.get("tags", "") or "").replace(",", ";").split(";")
135:         if part.strip()
136:     ]
137:     merged_tags = _merge_manual_and_auto_tags(
138:         manual_tags,
139:         auto_tags_sem_eco,
140:         fallback_tags="; ".join(legacy_tags),
141:         limit=6,
142:     )
143:     image_description = str(entry.get("image_description", "") or "")
144:     extra_parts = [markdown_text or ""]
145:     notes = str(entry.get("notes", "") or "")
146:     if notes:
147:         extra_parts.append(notes)
148:     if image_description and image_description not in " ".join(extra_parts):
149:         extra_parts.append(image_description)
150:     effective_markdown = "\n".join(p for p in extra_parts if p).strip()
151:     return {
152:         # S1 (P4): split camelCase SÓ no título — "LogicaDeHoare2" vira
153:         # "logica de hoare 2" e casa com o topic do bloco. Markdown/tags intactos.
154:         "title_text": normalize_match_text(split_camel_case(entry.get("title", ""))),
155:         # limit=24 (2026-09-01): o default 8 parava no 8o heading e num
156:         # slide-deck (formato dominante das aulas) o corpo estrutural fica
157:         # invisivel — FR 02-modelos tinha "TCP/IP" no 17o heading e a subunit
158:         # certa perdia o token no campo forte. So AQUI (scorer de entry); os
159:         # strong_headings da taxonomia seguem com o default.
160:         "markdown_headings_text": normalize_match_text(" ".join(_extract_markdown_headings(markdown_text, limit=24))),
161:         "markdown_lead_text": normalize_match_text(extract_markdown_lead_text(markdown_text)),
162:         "category_text": normalize_match_text(entry.get("category", "")),
163:         "manual_tags_text": normalize_match_text("; ".join(manual_tags)),
164:         "auto_tags_text": normalize_match_text("; ".join(auto_tags_sem_eco)),
165:         "tool_tags_text": normalize_match_text(" ".join(tool_values)),
166:         "legacy_tags_text": normalize_match_text("; ".join(legacy_tags)),
167:         "tags_text": normalize_match_text(merged_tags),
168:         "raw_text": normalize_match_text(entry.get("raw_target", "")),
169:         "image_description_text": normalize_match_text(image_description),
170:         "markdown_text": normalize_match_text(effective_markdown),
171:         # alavanca 1: label do recurso Moodle (mod.name) — identidade LIMPA do
172:         # material (ex. "Exemplos (Lógica de Floyd-Hoare)"), pesa como conceito.
173:         "moodle_label_text": normalize_match_text(entry.get("moodle_label", "")),
174:         # card do Moodle (secao onde o professor postou). Sinal de COBERTURA, nao
175:         # temporal: o motor ja usa o card como janela por outra via. Consumido SO
176:         # pelo scorer de unidade — ver test_card_nao_afeta_o_scorer_de_bloco_do_motor.
177:         "card_text": normalize_match_text(entry.get("source_section", "")),
178:     }
179: 

FILE src/builder/artifacts/navigation.py
84: def _entry_markdown_text_for_file_map(root_dir: Optional[Path], entry: dict) -> str:
85:     if "_markdown_text_for_tests" in entry:
86:         return entry.get("_markdown_text_for_tests") or ""
87:     md_path = _entry_markdown_path_for_file_map(root_dir, entry)
88:     if not md_path:
89:         # Fallback: material sem .md convertido (imagem/PDF) usa descricao injetada
90:         desc = str(entry.get("image_description", "") or "").strip()
91:         return desc
92:     try:
93:         return md_path.read_text(encoding="utf-8")
94:     except Exception:
95:         return ""
96: 
97: 
98: def _infer_unit_confidence(entry: dict) -> str:
99:     if str(entry.get("manual_unit_slug") or "").strip():
100:         return "Alta"
101: 
102:     resolved_unit = (
103:         str(entry.get("_resolved_unit_slug") or "").strip()
104:         or str(entry.get("unit_slug") or "").strip()
105:         or str(entry.get("unit") or "").strip()
106:     )
107:     if not resolved_unit:
108:         return "Baixa"
109:     if resolved_unit == "curso-inteiro":
110:         return "Alta"
111: 
112:     # Prioriza o transiente do build (file_map injeta o match recem-computado);
113:     # fora do build, le o `unit_match_confidence` persistido no manifest.
114:     match_confidence = float(
115:         entry.get("_unit_match_confidence")
116:         or entry.get("unit_match_confidence")
117:         or 0.0
118:     )
119:     ambiguous = bool(entry.get("_unit_match_ambiguous"))
120:     signal_count = sum(
121:         1
122:         for flag in (
123:             entry.get("_resolved_topic_slug"),
124:             entry.get("_resolved_period"),
125:             entry.get("manual_timeline_block_id"),
126:         )
127:         if flag
128:     )
129: 
130:     if ambiguous or match_confidence < 0.45:
131:         return "Baixa"
132:     if match_confidence >= 0.85 or signal_count >= 2:
133:         return "Alta"
134:     return "Média"
135: 
136: 
137: def _file_map_markdown_cell(md_path: str) -> str:
138:     rel = (md_path or "").strip()
139:     if not rel:
140:         return "—"
141:     rel_posix = rel.replace("\\", "/")
142:     if rel_posix.startswith("staging/"):
143:         return "A revisar"
144:     return f"`{rel}`"
145: 
146: 
147: def _extract_section_headers(md_content: str) -> list[dict]:
148:     headers: list[dict] = []
149:     in_code = False
150:     in_summary = False
151: 
152:     for i, line in enumerate((md_content or "").splitlines()):
153:         stripped = line.strip()
154: 
155:         if "<!-- EXEC_SUMMARY_START -->" in stripped:
156:             in_summary = True
157:             continue

[1mhook:[0m [2mPostToolUse[0m
[32m succeeded in 1758ms:[0m
docs/reports/_harness-2026-09-04/c1-3\calibra_regua_unidade.py:27:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\calibra_regua_unidade.py:36:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\calibra_regua_unidade.py:79:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\compila_vocab_um_curso.py:11:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\compila_vocab_um_curso.py:18:tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\diag_cg_sub.py:25:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\diag_cg_sub.py:30:tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\diag_cg_sub.py:32:topics = list(eng._iter_content_taxonomy_topics(tax))
docs/reports/_harness-2026-09-04/c1-3\diag_cg_sub.py:36:sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
docs/reports/_harness-2026-09-04/c1-3\diag_cg_sub.py:37:                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
docs/reports/_harness-2026-09-04/c1-3\diag_gargalo.py:28:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\diag_gargalo.py:31:sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
docs/reports/_harness-2026-09-04/c1-3\diag_gargalo.py:32:                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
docs/reports/_harness-2026-09-04/c1-3\diag_gargalo.py:52:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\diag_gargalo.py:56:    for t in eng._iter_content_taxonomy_topics(tax):
docs/reports/_harness-2026-09-04/c1-3\docs_c1_3b.py:32:        "**IDF intra-unidade MEDIDO (05/09 tarde, `c1-3/simula_idf_sub.py`: em memoria pela rota real `auto_map_entry_subtopic`, 0 chamadas; base\n"
docs/reports/_harness-2026-09-04/c1-3\gera_sidecar_professor.py:38:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\gera_sidecar_professor.py:53:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_cluster_keywords.py:38:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_cluster_keywords.py:44:sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
docs/reports/_harness-2026-09-04/c1-3\mede_cluster_keywords.py:45:                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
docs/reports/_harness-2026-09-04/c1-3\mede_cluster_keywords.py:75:    tax = limpa(load_internal_content_taxonomy(root), curados)
docs/reports/_harness-2026-09-04/c1-3\mede_cluster_keywords.py:77:    for t in eng._iter_content_taxonomy_topics(tax):
docs/reports/_harness-2026-09-04/c1-3\mede_doacao_secao.py:28:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_doacao_secao.py:43:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_doacao_secao.py:51:    for t in eng._iter_content_taxonomy_topics(tax):
docs/reports/_harness-2026-09-04/c1-3\mede_fontes_do_professor.py:34:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_fontes_do_professor.py:64:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_fontes_do_professor.py:68:    for t in eng._iter_content_taxonomy_topics(tax):
docs/reports/_harness-2026-09-04/c1-3\mede_moodle_da_unidade.py:32:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_moodle_da_unidade.py:59:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_moodle_da_unidade.py:61:    for t in eng._iter_content_taxonomy_topics(tax):
docs/reports/_harness-2026-09-04/c1-3\mede_moodle_da_unidade.py:94:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_moodle_da_unidade.py:95:    dono = {t["topic_slug"]: t["unit_slug"] for t in eng._iter_content_taxonomy_topics(tax)}
docs/reports/_harness-2026-09-04/c1-3\mede_sarc_posicional.py:25:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_sarc_posicional.py:36:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_titulo_video.py:30:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_titulo_video.py:35:sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
docs/reports/_harness-2026-09-04/c1-3\mede_titulo_video.py:36:                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
docs/reports/_harness-2026-09-04/c1-3\mede_titulo_video.py:59:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\mede_vizinho_keywords.py:29:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\mede_vizinho_keywords.py:35:sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
docs/reports/_harness-2026-09-04/c1-3\mede_vizinho_keywords.py:36:                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
docs/reports/_harness-2026-09-04/c1-3\mede_vizinho_keywords.py:63:    tax = limpa(load_internal_content_taxonomy(root), curados)
docs/reports/_harness-2026-09-04/c1-3\simula_alias_sessao_sub.py:1:"""[SL] Higiene de alias = label de sessao do SARC no scorer de SUBTOPICO, simulado em memoria pela rota real (engine._auto_map_entry_subtopic),
docs/reports/_harness-2026-09-04/c1-3\simula_alias_sessao_sub.py:26:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\simula_alias_sessao_sub.py:31:iter_orig = eng._iter_content_taxonomy_topics
docs/reports/_harness-2026-09-04/c1-3\simula_alias_sessao_sub.py:80:        fm.auto_map_entry_subtopic,
docs/reports/_harness-2026-09-04/c1-3\simula_alias_sessao_sub.py:82:        iter_content_taxonomy_topics=make_iter(variante),
docs/reports/_harness-2026-09-04/c1-3\simula_alias_sessao_sub.py:102:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\simula_cg_sub_levers.py:2:real (`file_map.auto_map_entry_subtopic` + scorer do engine) nas copias `.ablacao` (regua automatica) contra os 6 golds (233). 0 chamadas.
docs/reports/_harness-2026-09-04/c1-3\simula_cg_sub_levers.py:28:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\simula_cg_sub_levers.py:34:iter_orig = eng._iter_content_taxonomy_topics
docs/reports/_harness-2026-09-04/c1-3\simula_cg_sub_levers.py:128:    return functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
docs/reports/_harness-2026-09-04/c1-3\simula_cg_sub_levers.py:129:                             iter_content_taxonomy_topics=make_iter(variante, root),
docs/reports/_harness-2026-09-04/c1-3\simula_cg_sub_levers.py:147:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\simula_idf_sub.py:1:"""IDF intra-unidade no scorer de SUBTOPICO, simulado em memoria pela rota real (engine._auto_map_entry_subtopic),
docs/reports/_harness-2026-09-04/c1-3\simula_idf_sub.py:24:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\simula_idf_sub.py:29:iter_orig = eng._iter_content_taxonomy_topics
docs/reports/_harness-2026-09-04/c1-3\simula_idf_sub.py:75:        fm.auto_map_entry_subtopic,
docs/reports/_harness-2026-09-04/c1-3\simula_idf_sub.py:77:        iter_content_taxonomy_topics=make_iter(variante),
docs/reports/_harness-2026-09-04/c1-3\simula_idf_sub.py:97:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\simula_indice.py:29:from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3\simula_indice.py:48:    tax = load_internal_content_taxonomy(root)
docs/reports/_harness-2026-09-04/c1-3\simula_indice.py:52:    for t in eng._iter_content_taxonomy_topics(tax):
rg: src/builder/routing/subunit_propagation.py: O sistema não pode encontrar o arquivo especificado. (os error 2)
src/builder/extraction/content_taxonomy.py:35:def _normalize_match_text(text: str) -> str:
src/builder/extraction/content_taxonomy.py:42:def _strip_outline_prefix(text: str) -> str:
src/builder/extraction/content_taxonomy.py:62:def _unit_title_core_tokens(title: str) -> set:
src/builder/extraction/content_taxonomy.py:67:def _extract_markdown_headings(raw_markdown: str, limit: int = 8) -> List[str]:
src/builder/extraction/content_taxonomy.py:82:def _strip_topic_prefix(text: str) -> str:
src/builder/extraction/content_taxonomy.py:90:def _tool_matches(tool_norm: str, normalized_text: str) -> bool:
src/builder/extraction/content_taxonomy.py:101:def _looks_like_tool_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
src/builder/extraction/content_taxonomy.py:111:def _looks_like_bibliography_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
src/builder/extraction/content_taxonomy.py:128:def _looks_like_goal_or_section_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
src/builder/extraction/content_taxonomy.py:141:def _looks_like_weak_heading_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
src/builder/extraction/content_taxonomy.py:154:def _is_valid_topic_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
src/builder/extraction/content_taxonomy.py:173:def _extract_topic_candidates(*sources: str, semantic_profile: Optional[dict] = None) -> List[str]:
src/builder/extraction/content_taxonomy.py:198:def _extract_tool_candidates(*sources: str, semantic_profile: Optional[dict] = None) -> List[str]:
src/builder/extraction/content_taxonomy.py:215:def _topic_support_tokens(text: str) -> set:
src/builder/extraction/content_taxonomy.py:224:def _select_supported_taxonomy_topic(
src/builder/extraction/content_taxonomy.py:270:def _heading_topic_has_vocab_support(
src/builder/extraction/content_taxonomy.py:303:def build_tag_catalog(
src/builder/extraction/content_taxonomy.py:364:def _extract_topic_code(text: str) -> str:
src/builder/extraction/content_taxonomy.py:369:def _strip_topic_code(text: str) -> str:
src/builder/extraction/content_taxonomy.py:383:def _parse_glossary_terms(glossary_md: str) -> List[Dict[str, object]]:
src/builder/extraction/content_taxonomy.py:431:def _glossary_aliases_for_topic(topic_label: str, unit_title: str, glossary_terms: List[Dict[str, object]]) -> List[str]:
src/builder/extraction/content_taxonomy.py:471:def _dedupe_taxonomy_topics(topics: List[dict]) -> List[dict]:
src/builder/extraction/content_taxonomy.py:504:def _infer_course_slug_from_units(units: List[tuple]) -> str:
src/builder/extraction/content_taxonomy.py:512:def build_content_taxonomy(
src/builder/extraction/content_taxonomy.py:656:def write_internal_content_taxonomy(root_dir: Path, taxonomy: dict) -> None:
src/builder/extraction/content_taxonomy.py:660:def load_internal_content_taxonomy(root_dir: Path) -> dict:
src/builder/extraction/content_taxonomy.py:673:def build_unit_tag_index(taxonomy: dict) -> dict:
src/builder/extraction/content_taxonomy.py:690:def extract_markdown_lead_text(markdown_text: str, max_chars: int = 2600) -> str:
src/builder/extraction/content_taxonomy.py:708:def _clean_heading_text(text: str) -> str:
src/builder/extraction/content_taxonomy.py:724:def collect_strong_heading_candidates(root_dir: Optional[Path], manifest_entries: Optional[List[dict]]) -> List[str]:
src/builder/extraction/content_taxonomy.py:752:def _signal_token_set(signal_text: str) -> set:
src/builder/extraction/content_taxonomy.py:758:def _matches_tag_slug(signal_text: str, tag_slug: str) -> bool:
src/builder/extraction/content_taxonomy.py:780:def _is_exam_review_signal(signal_text: str) -> bool:
src/builder/extraction/content_taxonomy.py:814:def infer_entry_auto_tags(entry: dict, markdown_text: str, vocabulary: dict) -> List[str]:
src/builder/extraction/content_taxonomy.py:869:def write_tag_catalog(
src/builder/extraction/content_taxonomy.py:942:def refresh_manifest_auto_tags(
src/builder/extraction/content_taxonomy.py:964:def _exam_code_from_text(text: str) -> str:
src/builder/extraction/content_taxonomy.py:983:def _exam_code_from_block(block: dict) -> str:
src/builder/extraction/content_taxonomy.py:992:def _entry_title_text(entry: dict) -> str:
src/builder/extraction/content_taxonomy.py:1000:def review_list_block_for_entry(entry: dict, blocks: list) -> str:
.assessment_context.json
.block_identity.json
.card_block_map.json
.content_taxonomy.json
.glossary_curation.gold.json
.semantic_profile.generated.json
.tag_catalog.json
.timeline_curation.json
.timeline_index.json
CODE_HEALTH.md
COURSE_IDENTITY.md
COURSE_MAP.md
CRONOGRAMA_DETALHADO.md
CRONOGRAMA_HEALTH.md
FILE_MAP_TRACE.md
FILE_MAP.md
GLOSSARY.md
references_curation.json
SOURCE_REGISTRY.yaml
SYLLABUS.md
SO: 38 materiais, 6 unidades com material, 6 chamadas previstas (cap)
  unidade-01-introducao-ao-estudo-de-sistemas-operacionais mats  10  zips 0  membros   0  bundle  3815 chars
  unidade-02-gerencia-do-processador mats  11  zips 0  membros   0  bundle  4582 chars
  unidade-03-programacao-concorrente mats   4  zips 0  membros   0  bundle  2762 chars
  unidade-04-deadlock              mats   3  zips 1  membros   2  bundle  1145 chars
  unidade-05-gerencia-de-memoria   mats   6  zips 0  membros   0  bundle  5011 chars
  unidade-06-gerencia-de-arquivos  mats   4  zips 0  membros   0  bundle  1797 chars
  chamada 1/6
  chamada 2/6
  chamada 3/6
  chamada 4/6
  chamada 5/6
  chamada 6/6
chamadas feitas: 6/6; modelo gemini-3.5-flash; sidecar manual devolvido: True
gravado .glossary_curation.llm.json: 20 topicos com termos, 112 termos, erros: []
  1.1 Evolu��o hist�rica: ['Hist�rico', 'Sistemas de Lotes', 'Sistemas de Tempo Compartilhado', 'Batch Multiprogramming']
  1.1 Servi�os dos sistemas operacionais: ['Process management', 'File management', 'Directory and file system management']
  1.2 Chamadas de sistema: ['SVCs', 'Chamada de Sistema', 'syscalls', 'Chamada de Sistema para Cria��o de Processos']
  1.3 Estudo de casos: ['Linux', 'Unix', 'Unix/Linux', 'Linux kernel map']
  3.1 Conceitos b�sicos: ['Processos', 'Recurso Computacional', 'Imagem do processo', 'Bloco de Controle do Processo', 'Inter-process Communication', 'Comunica��o entre Processos', 'Mem�ria Compartilhada', 'Pipes', 'Tubos', 'Multithread', 'Troca de Mensagens', 'Sincroniza��o', 'Exclus�o m�tua']
  3.2 Escalonamento: ['Escalonamento de Processos', 'Troca de Contexto', 'O Escalonador', 'Scheduler', 'Dispatcher', 'Crit�rios de Aloca��o', 'Crit�rios de Otimiza��o']
  3.3 Algoritmos de escalonamento: ['First-Come-First-Served', 'Shortest Job First', 'Prioridade', 'Round-Robin', 'M�ltiplas Filas', 'Prioridade n�o-preemptiva', 'SJF (n�o preemptivo)', 'nonpreemptive', 'preemptive']
  3.4 Estudo de casos: ['Linux Threads', 'S.O. Solaris', 'Pthreads', 'pthread_create', 'pthread_exit', 'pthread_join', 'pthread_self', 'threads em C']
  4.1 Programas multithreads: ['multithreading', 'Processo multithread', 'C�digo Java com threads']
  4.2 Comunica��o e sincroniza��o de processos: ['Sockets', 'Socket', 'Programa��o de sockets', 'Socket programming', 'exec', 'wait', 'execvp']
  4.3 Primitivas de sincroniza��o: ['sem�foros']
  4.4 Problemas cl�ssicos: ['Ponte de pista �nica']
  6.1 Pol�ticas b�sicas: ['Princ�pios B�sicos', 'Mecanismos b�sicos', 'Unidade de Gerenciamento de Mem�ria', 'Amarra��o de endere�os', 'binding', 'Endere�o l�gico', 'Endere�o f�sico', 'C�digo reloc�vel', 'C�digo absoluto', 'Carregador absoluto', 'carregador relocador']
  6.2 Mem�ria virtual: ['Espa�o de Endere�amento Virtual', 'Biblioteca Compartilhada', 'Copy-on-Write', 'Localidade']
  6.2.1 Pagina��o: ['Pagina��o sob Demanda', 'Tamanho da p�gina', 'Tabela de p�ginas', 'Translation look-aside buffers', 'TLBs', 'Registradores associativos', 'Bit V�lido-Inv�lido', 'P�gina Ausente', 'Page Fault', 'Pagina��o Excessiva', 'Thrashing', 'Substitui��o de P�ginas']
  6.2.2 Segmenta��o: ['Tabela de segmentos', 'Fragmenta��o externa', 'Segmenta��o com pagina��o']
  7.1 Arquivos: ['Ger�ncia de Arquivos', 'Tipos de Arquivos', 'Opera��es sobre Arquivos', 'Sistemas de Armazenamento em Massa', 'Unidades de Armazenamento Secund�rio']
  7.2 Diret�rios: ['Estrutura de diret�rios Hier�rquicos']
  7.3 Implementa��o de sistemas de arquivos: ['Implementa��o de Arquivos', 'Aloca��o Cont�gua', 'Esquema do Sistema de Arquivos', 'Discos Magn�ticos', 'Disco Mec�nico', 'Estrutura Interna do Disco Mec�nico', 'Escalonamento de Requisi��es', 'SSTF', 'SCAN', 'C-SCAN', 'C-LOOK']
  7.6 Estudo de casos: ['Kernel UNIX']
IA: 56 materiais, 4 unidades com material, 4 chamadas previstas (cap)
  unidade-de-aprendizagem-01-visao-geral mats   3  zips 0  membros   0  bundle  1809 chars
  unidade-de-aprendizagem-02-solucao-de-problemas mats  13  zips 3  membros  14  bundle  6897 chars
  unidade-de-aprendizagem-03-raciocinio-planejamento-e-representacao-de-conhecimento mats   1  zips 0  membros   0  bundle   891 chars
  unidade-de-aprendizagem-05-aprendizado-de-maquina mats  39  zips 1  membros   1  bundle 22991 chars
  chamada 1/4
  chamada 2/4
  chamada 3/4
  chamada 4/4
chamadas feitas: 4/4; modelo gemini-3.5-flash; sidecar manual devolvido: True
gravado .glossary_curation.llm.json: 14 topicos com termos, 76 termos, erros: []
  Conceituação: ['Inteligência Artificial', 'Inteligência Adaptativa', 'modelos de IA']
  Subáreas e disciplinas afins: ['IA generativa', 'generative', 'ChatGPT', 'Copilot']
  Introdução a agentes em ambientes determinísticos: ['Agentes e Algoritmos de Busca']
  Representação de problemas: ['Estados de mundo', 'Estado de Mundo', 'Espaço de Busca']
  Busca informada (heurística): ['Algoritmos de Busca Informada', 'Busca Informada']
  Algoritmos de Busca com Informação: ['Algoritmo Hill-Climbing', 'Hill-Climbing', 'Algoritmo Simulated Annealing', 'Simulated Annealing', 'Busca Local por Refinamentos Sucessivos', 'Dijkstra', 'Algoritmo de Dijkstra']
  Problemas de Otimização: ['Algoritmos Genéticos', 'Algoritmo Genético Simples', 'Roda da Roleta', 'Crossover e Mutação', 'Elitismo', 'Crossover de N Pontos', 'Representação Real', 'Representação Binária', 'Cálculo da Aptidão', 'Seleção', 'Operações Genéticas', 'Crossover OBX', 'Crossover PBX', 'Crossover PMX', 'Crossover CX', 'Otimização Convencional']
  Busca Adversária: ['Teoria dos Jogos', 'Árvore de Busca', 'Transposição', 'Redução por simetria', 'Algoritmo Minimax', 'Minimax']
  Agentes em Lógica: ['Ambientes', 'Agentes puramente reativos', 'Agentes Reativos', 'Agente Reativo baseado em Modelo', 'Agente Reativo baseado em Modelos']
  Introdução ao aprendizado de máquina: ['Machine Learning', 'Deep Learning', 'aprendizado indutivo', 'Exploração dos Dados', 'Análise Exploratória dos Dados', 'Caracterização dos Dados', 'Generalização']
  Paradigmas de aprendizado: ['Aprendizado Supervisionado', 'Aprendizado Não Supervisionado']
  Modelos Preditivos: ['Classificação', 'Regressão', 'Rede Neural Perceptron', 'MultiLayer Perceptron', 'Árvore de Decisão', 'k-NN', 'Classificador Linear', 'Redes Feed Forward', 'Redes Recorrentes', 'Backpropagation']
  Modelos Descritivos: ['Agrupamento', 'Agrupamento Hierárquico', 'Agrupamento Particional', 'k-Means', 'Clustering', 'Mapa auto-organizável']
  Métricas de Avaliação: ['Matriz de Confusão', 'Accuracy', 'Micro-médias', 'Macro-médias']

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
Passo 1 de 4 feito: totais dos três regimes conferidos. No SO, o empate agregado esconde regressões compensadas por ganhos. Agora verifico os aliases que vencem e o texto descartado pelo determinístico.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
import json
for f,a,b in [('src/builder/extraction/entry_signals.py',106,230),('src/builder/artifacts/navigation.py',84,110),('src/builder/extraction/content_taxonomy.py',512,558),('src/builder/extraction/content_taxonomy.py',650,673),('src/builder/routing/resolver_apply.py',590,810)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))):print(f'{i+1}: {ls[i]}')
for name in ['Sistemas-Operacionais','Metodos-Formais','Engenharia-Software-2','Inteligencia-Artifical']:
 p=Path('..')/(name+'-Tutor');tax=json.loads((p/'course/.content_taxonomy.json').read_text(encoding='utf-8'));v=json.loads((p/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'));print(name,'TAX',list(tax),'VOCAB',str(v)[:750]);print('TOPIC',tax['units'][0]['topics'][0])
'@ | python -B -; rg -n 'def propagar|def .*subtopic|TopicMatchResult|content_taxonomy import' src/builder/routing/resolver_apply.py src/builder/timeline/index.py"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 292ms:[0m

FILE src/builder/extraction/entry_signals.py
106: def collect_entry_unit_signals(entry: dict, markdown_text: str) -> Dict[str, str]:
107:     markdown_text = texto_para_score(markdown_text)
108:     manual_tags = [str(tag).strip() for tag in (entry.get("manual_tags") or []) if str(tag).strip()]
109:     auto_tags = [str(tag).strip() for tag in (entry.get("auto_tags") or []) if str(tag).strip()]
110:     # Lista SEM eco: so o que vira TEXTO de score. A lista crua segue inteira
111:     # para `tool_values` e para quem le auto_tags fora daqui.
112:     auto_tags_sem_eco = _sem_eco(auto_tags)
113:     # S4 (P4): valores das auto_tags `ferramenta:` em campo próprio.
114:     # ATENCAO: o comentario antigo dizia que "o scorer de bloco (file_map,
115:     # TOOL_TOKENS) filtra quais sao ferramentas de verdade". `TOOL_TOKENS` NAO
116:     # existe em `src/` (so sobrevivia num .pyc stale) — **nada filtra esta lista**.
117:     # Ver B-9 em pendencias.md; o vocabulario de `ferramenta:` e auto-inferido do
118:     # proprio corpus (B-1) e por isso vem sujo.
119:     tool_values = [
120:         tag.split(":", 1)[1].strip()
121:         for tag in auto_tags
122:         if tag.lower().startswith("ferramenta:")
123:     ]
124:     # S4b (P4): ferramenta também pela EXTENSÃO do arquivo fonte (.thy ->
125:     # isabelle, .dfy -> dafny) — os .thy do manifest real não trazem
126:     # ferramenta:isabelle nas auto_tags. União dos dois sinais, dedupada.
127:     for field in ("source_path", "raw_target"):
128:         suffix = Path(str(entry.get(field, "") or "")).suffix.lower()
129:         ext_tool = TOOL_EXTENSIONS.get(suffix)
130:         if ext_tool and ext_tool not in tool_values:
131:             tool_values.append(ext_tool)
132:     legacy_tags = [
133:         part.strip()
134:         for part in str(entry.get("tags", "") or "").replace(",", ";").split(";")
135:         if part.strip()
136:     ]
137:     merged_tags = _merge_manual_and_auto_tags(
138:         manual_tags,
139:         auto_tags_sem_eco,
140:         fallback_tags="; ".join(legacy_tags),
141:         limit=6,
142:     )
143:     image_description = str(entry.get("image_description", "") or "")
144:     extra_parts = [markdown_text or ""]
145:     notes = str(entry.get("notes", "") or "")
146:     if notes:
147:         extra_parts.append(notes)
148:     if image_description and image_description not in " ".join(extra_parts):
149:         extra_parts.append(image_description)
150:     effective_markdown = "\n".join(p for p in extra_parts if p).strip()
151:     return {
152:         # S1 (P4): split camelCase SÓ no título — "LogicaDeHoare2" vira
153:         # "logica de hoare 2" e casa com o topic do bloco. Markdown/tags intactos.
154:         "title_text": normalize_match_text(split_camel_case(entry.get("title", ""))),
155:         # limit=24 (2026-09-01): o default 8 parava no 8o heading e num
156:         # slide-deck (formato dominante das aulas) o corpo estrutural fica
157:         # invisivel — FR 02-modelos tinha "TCP/IP" no 17o heading e a subunit
158:         # certa perdia o token no campo forte. So AQUI (scorer de entry); os
159:         # strong_headings da taxonomia seguem com o default.
160:         "markdown_headings_text": normalize_match_text(" ".join(_extract_markdown_headings(markdown_text, limit=24))),
161:         "markdown_lead_text": normalize_match_text(extract_markdown_lead_text(markdown_text)),
162:         "category_text": normalize_match_text(entry.get("category", "")),
163:         "manual_tags_text": normalize_match_text("; ".join(manual_tags)),
164:         "auto_tags_text": normalize_match_text("; ".join(auto_tags_sem_eco)),
165:         "tool_tags_text": normalize_match_text(" ".join(tool_values)),
166:         "legacy_tags_text": normalize_match_text("; ".join(legacy_tags)),
167:         "tags_text": normalize_match_text(merged_tags),
168:         "raw_text": normalize_match_text(entry.get("raw_target", "")),
169:         "image_description_text": normalize_match_text(image_description),
170:         "markdown_text": normalize_match_text(effective_markdown),
171:         # alavanca 1: label do recurso Moodle (mod.name) — identidade LIMPA do
172:         # material (ex. "Exemplos (Lógica de Floyd-Hoare)"), pesa como conceito.
173:         "moodle_label_text": normalize_match_text(entry.get("moodle_label", "")),
174:         # card do Moodle (secao onde o professor postou). Sinal de COBERTURA, nao
175:         # temporal: o motor ja usa o card como janela por outra via. Consumido SO
176:         # pelo scorer de unidade — ver test_card_nao_afeta_o_scorer_de_bloco_do_motor.
177:         "card_text": normalize_match_text(entry.get("source_section", "")),
178:     }
179: 

FILE src/builder/artifacts/navigation.py
84: def _entry_markdown_text_for_file_map(root_dir: Optional[Path], entry: dict) -> str:
85:     if "_markdown_text_for_tests" in entry:
86:         return entry.get("_markdown_text_for_tests") or ""
87:     md_path = _entry_markdown_path_for_file_map(root_dir, entry)
88:     if not md_path:
89:         # Fallback: material sem .md convertido (imagem/PDF) usa descricao injetada
90:         desc = str(entry.get("image_description", "") or "").strip()
91:         return desc
92:     try:
93:         return md_path.read_text(encoding="utf-8")
94:     except Exception:
95:         return ""
96: 
97: 
98: def _infer_unit_confidence(entry: dict) -> str:
99:     if str(entry.get("manual_unit_slug") or "").strip():
100:         return "Alta"
101: 
102:     resolved_unit = (
103:         str(entry.get("_resolved_unit_slug") or "").strip()
104:         or str(entry.get("unit_slug") or "").strip()
105:         or str(entry.get("unit") or "").strip()
106:     )
107:     if not resolved_unit:
108:         return "Baixa"
109:     if resolved_unit == "curso-inteiro":
110:         return "Alta"

FILE src/builder/extraction/content_taxonomy.py
512: def build_content_taxonomy(
513:     teaching_plan: str,
514:     course_map_md: str,
515:     glossary_md: str,
516:     strong_headings: Optional[List[str]] = None,
517:     semantic_profile: Optional[dict] = None,
518:     *,
519:     parse_units_from_teaching_plan: Callable[[str], list],
520:     topic_text: Callable[[object], str],
521:     normalize_unit_slug: Callable[[str], str],
522: ) -> dict:
523:     units = parse_units_from_teaching_plan(teaching_plan or "")
524:     # O CONTEUDOS do plano e lista humana: nao passa pelo filtro de ruido de
525:     # heading. Medido nos 5 cursos (2026-08-20): o filtro rejeitava 27 de 127
526:     # topicos do plano, TODOS legitimos ("Logica de Hoare", "Teorema de
527:     # Cook-Levin") e zero lixo; sobreviviam so pela isencao de codigo numerico.
528:     # O plano do IA nao numera -> "Modelos Preditivos" sumia e 33 entries da u05
529:     # colapsavam no topico "introducao". O filtro segue valendo para o fallback
530:     # (COURSE_MAP e markdown gerado, onde heading de template e ruido real).
531:     topics_from_plan = bool(units)
532:     if not units and course_map_md:
533:         units = parse_units_from_teaching_plan(course_map_md)
534: 
535:     glossary_terms = _parse_glossary_terms(glossary_md or "")
536:     heading_sources = [heading for heading in (strong_headings or []) if _collapse_ws(heading)]
537: 
538:     result_units = []
539:     for unit_title, topics in units:
540:         unit_slug = normalize_unit_slug(unit_title)
541:         topic_records = []
542:         for topic in topics or []:
543:             current_topic_text = _collapse_ws(_strip_topic_code(topic_text(topic)))
544:             if not current_topic_text:
545:                 continue
546:             topic_code = _extract_topic_code(topic_text(topic))
547:             # Filtrar noise topics: sem código numérico e que não passam na validação
548:             if not topics_from_plan and not topic_code and not _is_valid_topic_candidate(
549:                 current_topic_text, semantic_profile=semantic_profile
550:             ):
551:                 continue
552:             topic_slug = slugify(current_topic_text)
553:             aliases = _glossary_aliases_for_topic(current_topic_text, unit_title, glossary_terms)
554:             topic_kind = "subtopic" if topic_code.count(".") >= 2 else "topic"
555:             topic_records.append(
556:                 {
557:                     "code": topic_code,
558:                     "slug": topic_slug,

FILE src/builder/extraction/content_taxonomy.py
650:     # como boilerplate por curso. Vem do semantic_profile (course_slug = slugify(course_name)); o
651:     # `course_slug` desta raiz e inferido das UNIDADES (outra coisa) e fica como estava.
652:     course_name = str((semantic_profile or {}).get("course_slug") or "").replace("-", " ")
653:     return {"version": 1, "course_slug": _infer_course_slug_from_units(units), "course_name": course_name, "units": result_units}
654: 
655: 
656: def write_internal_content_taxonomy(root_dir: Path, taxonomy: dict) -> None:
657:     write_text(root_dir / "course" / ".content_taxonomy.json", json.dumps(taxonomy, ensure_ascii=False, indent=2))
658: 
659: 
660: def load_internal_content_taxonomy(root_dir: Path) -> dict:
661:     """Lê course/.content_taxonomy.json de um repo. {} se ausente/ilegível.
662: 
663:     Contrapartida de write_internal_content_taxonomy. Usado como fallback quando
664:     a taxonomia não vem em memória (ex.: retag), evitando rodar o scorer de
665:     subunidade com taxonomia vazia.
666:     """
667:     try:
668:         path = Path(root_dir) / "course" / ".content_taxonomy.json"
669:         return json.loads(path.read_text(encoding="utf-8"))
670:     except Exception:
671:         return {}
672: 
673: def build_unit_tag_index(taxonomy: dict) -> dict:

FILE src/builder/routing/resolver_apply.py
Sistemas-Operacionais TAX ['version', 'course_slug', 'course_name', 'units'] VOCAB {'_provenance': 'llm', '_modelo': 'gemini-3.5-flash', '_nota': 'Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). Para curar a mao, edite/crie .glossary_curation.json (o loader funde os dois).', '_raw': {'1.1 Evolução histórica': ['Histórico', 'Sistemas de Lotes', 'Sistemas de Tempo Compartilhado', 'Batch Multiprogramming'], '1.1 Serviços dos sistemas operacionais': ['Process management', 'File management', 'Directory and file system management'], '1.2 Chamadas de sistema': ['Chamadas de Sistema', 'SVCs', 'Chamada de Sistema
TOPIC {'code': '1.1', 'slug': 'evolucao-historica', 'label': 'Evolução histórica', 'aliases': ['1.1 Evolução histórica'], 'kind': 'topic', 'unit_slug': 'unidade-01-introducao-ao-estudo-de-sistemas-operacionais'}
Metodos-Formais TAX ['version', 'course_slug', 'course_name', 'units'] VOCAB {'_provenance': 'llm', '_modelo': 'gemini-3.5-flash', '_nota': 'Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). Para curar a mao, edite/crie .glossary_curation.json (o loader funde os dois).', '_raw': {'1.1 Sistemas Formais': ['Máquina de estados', 'LINGUAGENS FORMAIS', 'Alfabeto e palavra', 'Linguagem sobre um alfabeto', 'Linguagens artificiais', 'Hierarquia de Chomsky'], '1.2 Linguagens de Especificação e Lógicas': ['Linguagem de Especificação Formal', 'Especificação Formal', 'asserções lógicas', 'LÓGICA PROPOSICIONAL', 
TOPIC {'code': '1.1', 'slug': 'sistemas-formais', 'label': 'Sistemas Formais', 'aliases': ['1.1 Sistemas Formais', 'Alfabeto e palavra', 'Archive of Formal Proofs', 'Especificação Formal', 'Hierarquia de Chomsky', 'LINGUAGENS FORMAIS', 'Linguagem sobre um alfabeto', 'Linguagens artificiais'], 'kind': 'topic', 'unit_slug': 'unidade-01-metodos-formais'}
Engenharia-Software-2 TAX ['version', 'course_slug', 'course_name', 'units'] VOCAB {'_provenance': 'llm', '_modelo': 'gemini-3.5-flash', '_nota': 'Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). Para curar a mao, edite/crie .glossary_curation.json (o loader funde os dois).', '_raw': {'1.1 Conceito de arquitetura de software': ['Arquitetura de Software', 'Sistemas de Software', 'Aplicações Corporativas', 'IEEE', 'Manutabilidade'], '1.2 Visões arquiteturais: estrutural e dinâmica': [], '1.3 Estilos e padrões arquiteturais': ['Padrões de Projeto', 'PADRÕES', 'Evolução dos modelos arquiteturais'], '1.3.1 Cam
TOPIC {'code': '1.1', 'slug': 'conceito-de-arquitetura-de-software', 'label': 'Conceito de arquitetura de software', 'aliases': ['1.1 Conceito de arquitetura de software', 'ARQUITETURA DE SOFTWARE ---', 'Sistemas de Software'], 'kind': 'topic', 'unit_slug': 'unidade-01-arquitetura-de-software'}
Inteligencia-Artifical TAX ['version', 'course_slug', 'course_name', 'units'] VOCAB {'_provenance': 'llm', '_modelo': 'gemini-3.5-flash', '_nota': 'Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). Para curar a mao, edite/crie .glossary_curation.json (o loader funde os dois).', '_raw': {'Conceituação': ['Inteligência Artificial', 'IA', 'Inteligência Adaptativa', 'modelos de IA'], 'Breve Histórico de IA': [], 'Subáreas e disciplinas afins': ['IA generativa', 'generative', 'LLM', 'ChatGPT', 'Copilot'], 'Questões filosóficas de IA': ['IA Responsável'], 'Introdução a agentes em ambientes determinísticos': ['Age
TOPIC {'code': '', 'slug': 'conceituacao', 'label': 'Conceituação', 'aliases': ['Conceituação', 'visão geral'], 'kind': 'topic', 'unit_slug': 'unidade-de-aprendizagem-01-visao-geral'}
src/builder/routing/resolver_apply.py:19:from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES
src/builder/routing/resolver_apply.py:226:def _subtopico_nomeado_no_titulo(entry: dict, unit_slug: str, vencedor: str, partes: dict, frases_topico: dict) -> str:
src/builder/routing/resolver_apply.py:239:def _secao_nomeia_subtopico(entry: dict, topicos_da_unidade: list, generic_stems) -> str:
src/builder/routing/resolver_apply.py:262:def propagar_vocabulario_por_headings(passe1: list, content_taxonomy: dict, auto_map_entry_subtopic_fn, *,
src/builder/routing/resolver_apply.py:408:        from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
src/builder/routing/resolver_apply.py:411:    passe1: list = []   # (entry, texto, unidade, TopicMatchResult) da rota automatica, para a 2a passada
src/builder/timeline/index.py:165:class TopicMatchResult:
src/builder/timeline/index.py:2040:) -> tuple[List[dict], TopicMatchResult]:
src/builder/timeline/index.py:2043:        return [], TopicMatchResult(
src/builder/timeline/index.py:2059:        return [], TopicMatchResult(
src/builder/timeline/index.py:2115:        return topic_candidates, TopicMatchResult(
src/builder/timeline/index.py:2124:    primary = TopicMatchResult(

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
import json
for f,a,b in [('src/builder/routing/resolver_apply.py',262,374),('src/builder/extraction/content_taxonomy.py',431,470),('src/builder/extraction/content_taxonomy.py',560,647)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))):print(f'{i+1}: {ls[i]}')
p=Path('../Engenharia-Software-2-Tutor');v=json.loads((p/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'));print('VOCAB_KEYS',list(v));print('VOCAB_TAIL',str(v)[-4500:])
'@ | python -B -; rg -n 'glossary_curation|sinonimos|synonyms' src/builder/knowledge -g '*.py'; rg -n 'def .*glossary|glossary_curation' src/builder -g '*.py' | Select-Object -First 35"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 330ms:[0m

FILE src/builder/routing/resolver_apply.py
262: def propagar_vocabulario_por_headings(passe1: list, content_taxonomy: dict, auto_map_entry_subtopic_fn, *,
263:                                       conf_min: float, min_entries: int, df_max: float) -> int:
264:     """2a passada da subunidade (sessao 6, 2026-09-05). Token EXCLUSIVO dos headings/titulo dos materiais
265:     que a 1a passada atribuiu com confianca a um subtopico vira alias desse subtopico; so os materiais em
266:     que a 1a passada NAO decidiu (vazio, ambiguo ou conf < conf_min) sao repontuados. O plano nomeia
267:     categorias e o material nomeia algoritmos ("Modelos Preditivos" <- perceptron, rede neural); sem isto
268:     esse vocabulario so existia por glossario manual (IA). Medido nos 6 golds (233): +5 -0, FR/LR 0.
269:     Salvaguardas, cada uma medida: sem stems genericos do motor ('exemplo'/'respostas' viravam alias e
270:     derrubavam CG slab e MF respostas), df <= df_max dos materiais ('sumario'/'aula' do TCC), >= min_entries
271:     confiantes, exclusivo de UM subtopico da unidade, e nunca sobre decisao confiante (o CG perdia 8).
272:     Devolve quantos materiais mudaram."""
273:     from src.builder.text.stopwords import MOTOR_GENERIC_STEMS as _GENERIC_STEMS
274:     from src.builder.routing.thresholds import T
275:     units = {str(u.get("slug") or ""): u for u in (content_taxonomy or {}).get("units", []) or []}
276:     if not units or not passe1:
277:         return 0
278:     toks_by_entry: dict = {}
279:     df: Counter = Counter()
280:     for entry, texto, unit_slug, match in passe1:
281:         toks = _tokens_headings(collect_entry_unit_signals(entry, texto), _GENERIC_STEMS)
282:         toks_by_entry[id(entry)] = toks
283:         df.update(toks)
284:     vocab_unit = {}
285:     for slug, u in units.items():
286:         parts = [str(u.get("title") or "")] + [f"{t.get('label', '')} {' '.join(t.get('aliases') or [])}"
287:                                                 for t in (u.get("topics") or [])]
288:         vocab_unit[slug] = {x for x in normalize_match_text(" ".join(parts)).split() if len(x) >= 4}
289:     owners: dict = defaultdict(lambda: defaultdict(set))
290:     n_conf: Counter = Counter()
291:     for entry, texto, unit_slug, match in passe1:
292:         if not match or not match.topic_slug or match.ambiguous or match.confidence < conf_min:
293:             continue
294:         for tok in toks_by_entry[id(entry)] - vocab_unit.get(unit_slug, set()):
295:             if df[tok] > df_max * len(passe1):
296:                 continue
297:             owners[unit_slug][tok].add(match.topic_slug)
298:             n_conf[(unit_slug, match.topic_slug, tok)] += 1
299:     extra: dict = defaultdict(set)
300:     for unit_slug, toks in owners.items():
301:         for tok, subs in toks.items():
302:             if len(subs) == 1 and n_conf[(unit_slug, next(iter(subs)), tok)] >= min_entries:
303:                 extra[(unit_slug, next(iter(subs)))].add(tok)
304:     partes = _partes_de_rotulo(units, passe1, df_max)   # 2a fonte (06/09): partes do rotulo composto do plano
305:     for key, ps in partes.items():
306:         extra[key] |= ps
307:     # (sem `if not extra: return 0`: a regra do titulo e a da secao, abaixo, valem mesmo sem alias novo)
308:     tax = copy.deepcopy(content_taxonomy)
309:     for u in tax.get("units", []) or []:
310:         for t in u.get("topics") or []:
311:             add = extra.get((str(u.get("slug") or ""), str(t.get("slug") or "")))
312:             if add:
313:                 t["aliases"] = list(t.get("aliases") or []) + sorted(add)
314:     mudou = 0
315:     frases_topico = {str(t.get("slug") or ""): [str(t.get("label") or "")] + list(t.get("aliases") or [])
316:                      for u in units.values() for t in (u.get("topics") or [])}
317:     decididos_na_2a: set = set()
318:     for entry, texto, unit_slug, match in passe1:
319:         if match and match.topic_slug and not match.ambiguous and match.confidence >= conf_min:
320:             # Decisao confiante da 1a passada so cai quando o TITULO do material nomeia outro subtopico da unidade por
321:             # uma parte do rotulo e NAO nomeia o vencedor (06/09, `simula_titulo_confiante.py`: +2 -0 nos 6 golds; CG
322:             # "Exercicios de geometria computacional" ia para `entidades-geometricas` por 'Vetor/Pontos/Retas' no corpo).
323:             y = _subtopico_nomeado_no_titulo(entry, unit_slug, str(match.topic_slug), partes, frases_topico)
324:             if y:
325:                 entry["computed_subunit_slug"] = y
326:                 entry["subunit_match_reasons"] = list(match.reasons) + [_TITULO_REASON]
327:                 tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
328:                 entry["auto_tags"] = tags + [f"subunit:{y}"]
329:                 mudou += 1
330:             continue  # fora isso, decisao confiante da 1a passada nunca e sobreposta
331:         novo = auto_map_entry_subtopic_fn(entry, tax, texto, winning_unit_slug=unit_slug)
332:         slug_novo = str(getattr(novo, "topic_slug", "") or "")
333:         slug_ant = str(getattr(match, "topic_slug", "") or "") if match else ""
334:         if not slug_novo or (slug_novo == slug_ant and float(novo.confidence) <= float(match.confidence)):
335:             continue
336:         entry["computed_subunit_slug"] = slug_novo
337:         texto_norm = normalize_match_text(texto or "")
338:         por_parte = any(normalize_match_text(p) in texto_norm for p in partes.get((unit_slug, slug_novo), ()))
339:         entry["subunit_match_reasons"] = list(novo.reasons) + [_DECOMP_REASON if por_parte else _PROPAG_REASON]
340:         entry["subunit_match_confidence"] = float(novo.confidence)
341:         tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
342:         if not novo.ambiguous and float(novo.confidence) >= T.SUBUNIT_TAG:
343:             tags.append(f"subunit:{slug_novo}")
344:         entry["auto_tags"] = tags
345:         decididos_na_2a.add(id(entry))
346:         mudou += 1
347:     # Ultimo recurso (06/09, S1b): onde NEM a 1a NEM a 2a passada decidiram (vazia ou empatada), a SECAO do Moodle que
348:     # nomeia exatamente um subtopico da unidade decide. Medido pela rota real nos 6 golds: +3 -0 (MF exemplos-zip, CG intro,
349:     # CG curvasparametricas). Versoes mais agressivas (sobrepor a 2a passada: +5 -3; sobrepor decisao confiante: +5 -13)
350:     # REFUTADAS: a secao do professor nomeia o pai quando o gold quer o filho (z-buffer, k-nn, escalonamento).
351:     from src.builder.timeline.index import _iter_content_taxonomy_topics
352:     por_unidade: dict = defaultdict(list)
353:     for t in _iter_content_taxonomy_topics(content_taxonomy) or []:
354:         por_unidade[str(t.get("unit_slug") or "")].append(t)
355:     for entry, texto, unit_slug, match in passe1:
356:         reasons = [str(r) for r in (entry.get("subunit_match_reasons") or [])]
357:         indecisa_2a = any(r == "ambiguous" or r.startswith("empate-exato") for r in reasons)
358:         indecisa_1a = id(entry) not in decididos_na_2a and (not match or not match.topic_slug or match.ambiguous)
359:         if entry.get("computed_subunit_slug") and not indecisa_2a and not indecisa_1a:
360:             continue
361:         y = _secao_nomeia_subtopico(entry, por_unidade.get(unit_slug, []), _GENERIC_STEMS)
362:         if not y or y == str(entry.get("computed_subunit_slug") or ""):
363:             continue
364:         entry["computed_subunit_slug"] = y
365:         entry["subunit_match_reasons"] = [r for r in reasons if r != "ambiguous" and not r.startswith("empate-exato")] + [_SECAO_REASON]
366:         entry["subunit_match_confidence"] = float(conf_min)
367:         tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
368:         entry["auto_tags"] = tags + [f"subunit:{y}"]
369:         mudou += 1
370:     return mudou
371: 
372: 
373: def apply_unit_subunit_fields(
374:     entries: list,

FILE src/builder/extraction/content_taxonomy.py
431: def _glossary_aliases_for_topic(topic_label: str, unit_title: str, glossary_terms: List[Dict[str, object]]) -> List[str]:
432:     topic_norm = _normalize_match_text(topic_label)
433:     unit_norm = _normalize_match_text(unit_title)
434:     aliases: List[str] = []
435:     seen = set()
436: 
437:     for term in glossary_terms or []:
438:         term_text = _collapse_ws(str(term.get("term", "")))
439:         if not term_text:
440:             continue
441:         term_norm = _normalize_match_text(term_text)
442:         if not term_norm:
443:             continue
444: 
445:         unit_hint = _normalize_match_text(str(term.get("unit_hint", "")))
446:         if unit_hint and unit_hint not in unit_norm and unit_norm not in unit_hint:
447:             continue
448: 
449:         # R8 (2026-08-26): termo NUMERADO do plano casa so pelo nucleo EXATO.
450:         # Por contencao, "3.3 Algoritmos de escalonamento" (e seus sinonimos
451:         # FCFS/SJF) entrava tambem em "Escalonamento" e os dois topicos
452:         # empatavam; "2.3 Variacoes de Maquinas de Turing" virava alias de
453:         # "Maquinas de Turing". Termo sem numeracao mantem a contencao.
454:         core_norm = _normalize_match_text(_strip_topic_code(term_text))
455:         if _extract_topic_code(term_text):
456:             matched = core_norm == topic_norm
457:         else:
458:             matched = term_norm == topic_norm or term_norm in topic_norm or topic_norm in term_norm
459:         if matched:
460:             for candidate in [term_text, *list(term.get("synonyms", []) or [])]:
461:                 candidate_text = _collapse_ws(candidate)
462:                 candidate_slug = slugify(candidate_text)
463:                 if not candidate_text or not candidate_slug or candidate_slug in seen:
464:                     continue
465:                 seen.add(candidate_slug)
466:                 aliases.append(candidate_text)
467: 
468:     return aliases
469: 
470: 

FILE src/builder/extraction/content_taxonomy.py
560:                     "aliases": aliases,
561:                     "kind": topic_kind,
562:                     "unit_slug": unit_slug,
563:                 }
564:             )
565: 
566:         result_units.append({"slug": unit_slug, "title": unit_title, "topics": _dedupe_taxonomy_topics(topic_records)})
567: 
568:     # (a) topico-preview cujo rotulo contem o nucleo do titulo de OUTRA unidade
569:     # migra pra unidade dona (bug MF: "1.3.1. Verificacao de Modelos" na abertura
570:     # da u01 empatava o DP 4x4 no bloco-16).
571:     title_cores = {}
572:     for unit in result_units:
573:         core = _unit_title_core_tokens(unit.get("title", ""))
574:         if len(core) >= _TITLE_CORE_MIN_TOKENS:
575:             title_cores[unit["slug"]] = core
576:     for unit in result_units:
577:         kept = []
578:         for topic in unit.get("topics", []) or []:
579:             label_toks = _topic_support_tokens(str(topic.get("label", "") or ""))
580:             owner = next(
581:                 (slug for slug, core in title_cores.items()
582:                  if slug != unit["slug"] and core <= label_toks),
583:                 None,
584:             )
585:             if owner is None:
586:                 kept.append(topic)
587:                 continue
588:             topic["unit_slug"] = owner
589:             dest = next(u for u in result_units if u["slug"] == owner)
590:             dest["topics"] = _dedupe_taxonomy_topics(list(dest.get("topics", []) or []) + [topic])
591:         unit["topics"] = kept
592: 
593:     # Heading institucional ("ENGENHARIA DE SOFTWARE II ---", "Trabalho
594:     # FinalEngenharia de Software II") aparece no cabecalho de TODO material e,
595:     # virando alias, transforma o topico dono num ima: no ES2 puxou Kubernetes e
596:     # o T1 para a unidade de arquitetura (medicao 2026-08-18). O perfil ja marca
597:     # o slug do curso como generico — aqui a checagem faltava.
598:     effective_profile = merge_semantic_profile(semantic_profile)
599:     generic_slugs = set(effective_profile.get("tag_generic_slugs") or [])
600:     course_norm = _normalize_match_text(
601:         str(effective_profile.get("course_slug") or "").replace("-", " ")
602:     )
603:     for heading in heading_sources:
604:         heading_text = _collapse_ws(_strip_topic_code(heading))
605:         heading_slug = slugify(heading_text)
606:         if not heading_text or not heading_slug:
607:             continue
608:         if heading_slug in generic_slugs:
609:             continue
610:         if course_norm and course_norm in _normalize_match_text(heading_text):
611:             continue
612:         best_unit: Optional[dict] = None
613:         best_topic: Optional[dict] = None
614:         best_score = 0.0
615:         # (b) heading que contem nucleo de titulo de unidade so enriquece a dona
616:         heading_toks = _topic_support_tokens(heading_text)
617:         owner_units = [u for u in result_units
618:                        if title_cores.get(u["slug"]) and title_cores[u["slug"]] <= heading_toks]
619:         search_units = owner_units or result_units
620:         for unit in search_units:
621:             candidate_topic = _select_supported_taxonomy_topic(
622:                 heading_text,
623:                 unit.get("topics", []) or [],
624:                 semantic_profile=semantic_profile,
625:             )
626:             if not candidate_topic:
627:                 continue
628:             topic_score = 0.0
629:             base_norm = _normalize_match_text(str(candidate_topic.get("label", "") or ""))
630:             heading_norm = _normalize_match_text(heading_text)
631:             if heading_norm == base_norm:
632:                 topic_score = 10.0
633:             elif heading_norm in base_norm or base_norm in heading_norm:
634:                 topic_score = 8.0
635:             else:
636:                 overlap = _topic_support_tokens(heading_text) & _topic_support_tokens(str(candidate_topic.get("label", "") or ""))
637:                 topic_score = 5.0 + (0.4 * len(overlap))
638:             if topic_score > best_score:
639:                 best_score = topic_score
640:                 best_unit = unit
641:                 best_topic = candidate_topic
642:         if best_topic and best_unit:
643:             aliases = list(best_topic.get("aliases", []) or [])
644:             if heading_text not in aliases and slugify(heading_text) != slugify(str(best_topic.get("label", "") or "")):
645:                 aliases.append(heading_text)
646:             best_topic["aliases"] = aliases
647:             best_unit["topics"] = _dedupe_taxonomy_topics(list(best_unit.get("topics", []) or []))
VOCAB_KEYS ['_provenance', '_modelo', '_nota', '_raw', '1.1 Conceito de arquitetura de software', '1.3 Estilos e padrões arquiteturais', '1.3.1 Camadas', '1.3.2 Cliente-Servidor', '1.3.3 Orientada a Serviços', '1.3.4 Orientada a Microsserviços', '1.4 Estratégias de Construção de Arquitetura', '1.5 Estudo de caso: arquitetura orientada a microsserviços', '2.2 Gerenciamento da Configuração', '2.3 Integração contínua (CI)', '2.6 Plataformas de DevOps', '2.7 Estudo de Caso: integração e implantação de microsserviços']
VOCAB_TAIL {'_provenance': 'llm', '_modelo': 'gemini-3.5-flash', '_nota': 'Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). Para curar a mao, edite/crie .glossary_curation.json (o loader funde os dois).', '_raw': {'1.1 Conceito de arquitetura de software': ['Arquitetura de Software', 'Sistemas de Software', 'Aplicações Corporativas', 'IEEE', 'Manutabilidade'], '1.2 Visões arquiteturais: estrutural e dinâmica': [], '1.3 Estilos e padrões arquiteturais': ['Padrões de Projeto', 'PADRÕES', 'Evolução dos modelos arquiteturais'], '1.3.1 Camadas': ['Arquitetura em camadas lógicas', 'Arquitetura em camadas físicas', 'camadas lógicas', 'camadas físicas'], '1.3.2 Cliente-Servidor': ['arquitetura cliente servidor', 'Cliente', 'Servidor', 'Client Side Rendering', 'Server Side Rendering', 'Web', 'HTTP'], '1.3.3 Orientada a Serviços': ['ARQUITETURA ORIENTADA A SERVIÇOS', 'WEB SERVICES', 'Web Services'], '1.3.4 Orientada a Microsserviços': ['MICROSSERVIÇOS', 'Microserviços', 'Monolitos', 'Escalabilidade Vertical', 'Escalabilidade Horizontal', 'Service Discovery', 'Service Registry', 'Client-Side Discovery', 'Server-Side Discovery', 'API Gateway', 'BFF', 'Backends for frontends'], '1.3.5 Arquitetura Serverless': [], '1.4 Estratégias de Construção de Arquitetura': ['Decisões Arquiteturais'], '1.5 Estudo de caso: arquitetura orientada a microsserviços': ['microsserviço de câmbio', 'microserviço de conversão', 'Discovery (Name Server)', 'Balanceamento de Carga', 'Netflix Eureka', 'CurrencyExchangeProxy', 'CurrencyExchange', 'CurrencyConversion', 'ApiGatewayApplication'], '2.1 Conceito de DevOps': ['DevOps', 'Dev', 'Ops'], '2.2 Gerenciamento da Configuração': ['Gerência de configuração', 'Gerência de versões e mudanças', 'Infraestrutura como código (IaC)', 'Gerência de pacotes'], '2.3 Integração contínua (CI)': ['Integração contínua (CI)', 'Pipeline'], '2.4 Entrega contínua (CD)': [], '2.5 Monitoramento Contínuo': [], '2.6 Plataformas de DevOps': ['Docker', 'Kubernetes', 'Azure', 'Ambientes de Desenvolvimento em Nuvem'], '2.7 Estudo de Caso: integração e implantação de microsserviços': ['microsserviço de câmbio', 'api gateway', 'Circuit Breaker', 'Composição de Containers', 'compose.yaml', 'RabbitMQ', 'Comunicação por Filas', 'Auth0', 'Autenticação e Autorização', 'Serviço em contêiner', 'Contêiner', 'Máquina Virtual', 'multi-stage build']}, '1.1 Conceito de arquitetura de software': {'synonyms': ['Arquitetura de Software', 'Sistemas de Software', 'Aplicações Corporativas', 'IEEE', 'Manutabilidade']}, '1.3 Estilos e padrões arquiteturais': {'synonyms': ['Padrões de Projeto', 'PADRÕES', 'Evolução dos modelos arquiteturais']}, '1.3.1 Camadas': {'synonyms': ['Arquitetura em camadas lógicas', 'Arquitetura em camadas físicas', 'camadas lógicas', 'camadas físicas']}, '1.3.2 Cliente-Servidor': {'synonyms': ['arquitetura cliente servidor', 'Cliente', 'Servidor', 'Client Side Rendering', 'Server Side Rendering', 'HTTP']}, '1.3.3 Orientada a Serviços': {'synonyms': ['ARQUITETURA ORIENTADA A SERVIÇOS', 'WEB SERVICES']}, '1.3.4 Orientada a Microsserviços': {'synonyms': ['Microserviços', 'Monolitos', 'Escalabilidade Vertical', 'Escalabilidade Horizontal', 'Service Discovery', 'Service Registry', 'Client-Side Discovery', 'Server-Side Discovery', 'Backends for frontends']}, '1.4 Estratégias de Construção de Arquitetura': {'synonyms': ['Decisões Arquiteturais']}, '1.5 Estudo de caso: arquitetura orientada a microsserviços': {'synonyms': ['microserviço de conversão', 'Discovery (Name Server)', 'Balanceamento de Carga', 'Netflix Eureka', 'CurrencyExchangeProxy', 'CurrencyExchange', 'CurrencyConversion', 'ApiGatewayApplication']}, '2.2 Gerenciamento da Configuração': {'synonyms': ['Gerência de configuração', 'Gerência de versões e mudanças', 'Infraestrutura como código (IaC)', 'Gerência de pacotes']}, '2.3 Integração contínua (CI)': {'synonyms': ['Pipeline']}, '2.6 Plataformas de DevOps': {'synonyms': ['Docker', 'Ambientes de Desenvolvimento em Nuvem']}, '2.7 Estudo de Caso: integração e implantação de microsserviços': {'synonyms': ['Circuit Breaker', 'Composição de Containers', 'compose.yaml', 'RabbitMQ', 'Comunicação por Filas', 'Auth0', 'Autenticação e Autorização', 'Serviço em contêiner', 'Contêiner', 'Máquina Virtual', 'multi-stage build']}}
rg: src/builder/knowledge: IO error for operation on src/builder/knowledge: O sistema não pode encontrar o arquivo especificado. (os error 2)
src/builder\artifacts\repo.py:1180:def glossary_term_core(term: str) -> str:
src/builder\artifacts\repo.py:1199:def collect_glossary_evidence(
src/builder\artifacts\repo.py:1263:def glossary_tokens(text: str) -> List[str]:
src/builder\artifacts\repo.py:1273:def trim_glossary_prefix(text: str, prefixes: List[str], *, collapse_ws: Callable[[str], str]) -> str:
src/builder\artifacts\repo.py:1288:def shorten_glossary_sentence(sentence: str, *, collapse_ws: Callable[[str], str], max_chars: int = 180) -> str:
src/builder\artifacts\repo.py:1298:def is_bad_glossary_evidence(sentence: str, *, collapse_ws: Callable[[str], str]) -> bool:
src/builder\artifacts\repo.py:1316:def normalize_glossary_sentence(
src/builder\artifacts\repo.py:1344:def best_glossary_sentence(
src/builder\artifacts\repo.py:1399:def find_glossary_evidence(
src/builder\artifacts\repo.py:1434:def refine_glossary_definition_from_evidence(
src/builder\artifacts\repo.py:1464:def seed_glossary_fields(
src/builder\artifacts\repo.py:1674:_GLOSSARY_CURATION_NAME = ".glossary_curation.json"
src/builder\artifacts\repo.py:1675:_GLOSSARY_LLM_NAME = ".glossary_curation.llm.json"
src/builder\artifacts\repo.py:1697:def _glossary_curation_key(term: str) -> str:
src/builder\artifacts\repo.py:1706:def load_glossary_curation(root_dir: Optional[Path]) -> Dict[str, List[str]]:
src/builder\artifacts\repo.py:1707:    """{termo (casefold): [sinonimos]} de `course/.glossary_curation.json`.
src/builder\artifacts\repo.py:1722:    # Manual + compilado por LLM (Fase 1b, 02/09: `.glossary_curation.llm.json`, mesmo formato,
src/builder\artifacts\repo.py:1745:            key = _glossary_curation_key(term)
src/builder\artifacts\repo.py:1755:def merge_glossary_synonyms(seed: str, curated: List[str]) -> str:
src/builder\artifacts\repo.py:1766:def glossary_md(
src/builder\artifacts\repo.py:1809:    curated_synonyms = load_glossary_curation(root_dir)
src/builder\artifacts\repo.py:1823:            synonyms = merge_glossary_synonyms(synonyms, curated_synonyms.get(_glossary_curation_key(term), []))
src/builder\core\vocabulary_compile.py:2:COM material, gravado em `course/.glossary_curation.llm.json` no formato do loader
src/builder\core\vocabulary_compile.py:3:(`repo.load_glossary_curation`: `{"<codigo> <Label do plano>": {"synonyms": [...]}}`, chaves
src/builder\core\vocabulary_compile.py:4:`_*` sao metadados). O loader funde este arquivo com o sidecar MANUAL `.glossary_curation.json`.
src/builder\core\vocabulary_compile.py:46:LLM_VOCAB_NAME = ".glossary_curation.llm.json"
src/builder\core\vocabulary_compile.py:47:MANUAL_VOCAB_NAME = ".glossary_curation.json"
src/builder\extraction\content_taxonomy.py:383:def _parse_glossary_terms(glossary_md: str) -> List[Dict[str, object]]:
src/builder\extraction\content_taxonomy.py:431:def _glossary_aliases_for_topic(topic_label: str, unit_title: str, glossary_terms: List[Dict[str, object]]) -> List[str]:
src/builder\facade\glossary.py:6:def build_glossary_aliases(
src/builder\facade\glossary.py:27:    def shorten_glossary_sentence(sentence, max_chars=180):
src/builder\facade\glossary.py:39:    def collect_glossary_evidence(root_dir, manifest_entries=None, unit_titles=None):
src/builder\facade\glossary.py:49:    def normalize_glossary_sentence(term, unit_title, sentence):
src/builder\facade\glossary.py:73:    def refine_glossary_definition_from_evidence(term, unit_hint, evidence):
src/builder\facade\glossary.py:90:    def glossary_md(course_meta, subject_profile=None, *, root_dir=None, manifest_entries=None):

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import json
from pathlib import Path
for nm in ['Sistemas-Operacionais','Metodos-Formais','Engenharia-Software-2']:
 p=Path('.ablacao')/(nm+'-Tutor');m=json.loads((p/'manifest.json').read_text(encoding='utf-8'));print(nm,'MAN_KEYS',list(m));print('meta',str(m.get('course_meta'))[:500])
 print('TAX_TOPICS',[(u['slug'],[(t['label'],t['aliases']) for t in u['topics'][:4]]) for u in json.loads((p/'course/.content_taxonomy.json').read_text(encoding='utf-8'))['units']][:2])
 for e in m['entries']:
  if e['id'] in ['roteiro1','roteiro4','arvores','invariantes','exemplo-threads-em-c-exemplo1']:print('ENTRY',e)
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 241ms:[0m
Sistemas-Operacionais MAN_KEYS ['app', 'generated_at', 'course', 'options', 'environment', 'entries', 'failed_entries', 'logs', 'updated_at', 'turma', 'schedule_url']
meta None
TAX_TOPICS [('unidade-01-introducao-ao-estudo-de-sistemas-operacionais', [('Evolução histórica', ['1.1 Evolução histórica']), ('Serviços dos sistemas operacionais', ['1.1 Serviços dos sistemas operacionais']), ('Chamadas de sistema', ['1.2 Chamadas de sistema', 'Chamada de Sistema para Criação de Processos', 'Chamada de SistemasCriação de Processos']), ('Estudo de casos', ['--- 2) Casos em que multithreading não melhora desempenho', '1.3 Estudo de casos'])]), ('unidade-02-gerencia-do-processador', [('Conceitos básicos', ['3.1 Conceitos básicos']), ('Escalonamento', ['3.2 Escalonamento', 'Escalonamento de Processos']), ('Algoritmos de escalonamento', ['3.3 Algoritmos de escalonamento']), ('Estudo de casos', ['3.4 Estudo de casos'])])]
ENTRY {'id': 'exemplo-threads-em-c-exemplo1', 'title': 'Exemplo threads em C - exemplo1', 'category': 'codigo-professor', 'file_type': 'code', 'source_path': 'C:\\Users\\Humberto\\Desktop\\Moodle\\sistemas-operacionais\\Threads\\Exemplo threads em C - exemplo1.c', 'source_section': 'Threads', 'tags': '', 'manual_tags': [], 'auto_tags': ['topico:threads', 'tipo:codigo', 'bloco:bloco-26', 'unit:unidade-02-gerencia-do-processador'], 'manual_unit_slug': '', 'manual_timeline_block_id': '', 'notes': '', 'professor_signal': '', 'include_in_bundle': True, 'relevant_for_exam': True, 'processing_mode': 'high_fidelity', 'document_profile': 'auto', 'preferred_backend': 'auto', 'datalab_mode': 'accurate', 'formula_priority': False, 'preserve_pdf_images_in_markdown': True, 'force_ocr': False, 'extract_images': True, 'extract_tables': True, 'page_range': '', 'ocr_language': 'por,eng', 'raw_target': 'raw/code/professor/exemplo-threads-em-c-exemplo1.c', 'manual_review': 'manual-review/code/exemplo-threads-em-c-exemplo1.md', 'base_markdown': 'code/professor/exemplo-threads-em-c-exemplo1.md', 'language': 'c', 'approved_markdown': 'code/professor/exemplo-threads-em-c-exemplo1.md', 'curated_markdown': 'code/professor/exemplo-threads-em-c-exemplo1.md', 'computed_unit_slug': 'unidade-02-gerencia-do-processador', 'computed_block_method': 'concept-fused', 'computed_block_id': '160eff04-bea9-4349-8a4b-992311cce6be', 'computed_block_confidence': 0.08611111111111115, 'computed_block_band': 'baixa', 'unit_match_reasons': ['winner_score=13.12', 'topic_score=12.28', 'reconciliada_do_bloco=bloco-04'], 'unit_match_confidence': 0.95, 'unit_block_conflict': {'unit': 'unidade-03-programacao-concorrente', 'block_unit': 'unidade-02-gerencia-do-processador', 'block_id': 'bloco-04'}, 'computed_subunit_slug': '', 'subunit_match_reasons': ['empate-exato 2x score=0.11'], 'subunit_match_confidence': 0.0, 'moodle_label': 'Exemplo: threads em C', 'posting_date': '2026-03-10', 'posting_date_created': '2026-03-10', 'computed_block_rationale': 'O bloco 03 aborda a gerência de processador e threads, sendo o tópico central deste exemplo que demonstra a criação e o ciclo de vida de threads.', 'computed_block_match_confidence': 0.85, 'coverage_units': [{'unit_slug': 'unidade-03-programacao-concorrente', 'topics': ['4.1 programas multithreads', 'programas multithreads'], 'confidence': 0.7, 'rule': 'card'}], 'temporal_block_id': 'e4f7e22a-e091-46f8-b70e-a65f387dbf84', 'temporal_block_method': 'janela-1', 'temporal_block_band': 'alta', 'temporal_block_flag': False, 'temporal_block_provider': 'topic', 'temporal_block_window': ['bloco-04'], 'revisar': 'duvida', 'moodle_section_index': 4, 'moodle_module_index': 4, 'moodle_week_label': '31/03 Threads'}
Metodos-Formais MAN_KEYS ['app', 'generated_at', 'course', 'options', 'environment', 'entries', 'logs', 'updated_at', 'failed_entries', 'turma', 'schedule_url']
meta None
TAX_TOPICS [('unidade-01-metodos-formais', [('Sistemas Formais', ['1.1 Sistemas Formais', 'Alfabeto e palavra', 'Archive of Formal Proofs', 'Especificação Formal', 'Hierarquia de Chomsky', 'LINGUAGENS FORMAIS', 'Linguagem sobre um alfabeto', 'Linguagens artificiais']), ('Linguagens de Especificação e Lógicas', ['1.2 Linguagens de Especificação e Lógicas', 'Composição de Proposições', 'Consequência Lógica', 'Equivalências', 'Especificação Formal', 'Fórmulas bem-formadas', 'Fórmulas mal-formadas', 'Linguagem de Especificação Formal', 'LÓGICA PROPOSICIONAL', 'Proposição', 'Semântica dos Operadores', 'Teoremas', 'asserções lógicas']), ('Fundamentos de Lógica de Primeira Ordem', ['1.2.1 Fundamentos de Lógica de Primeira Ordem', 'Assinatura', 'Avaliação de Termos', 'Fórmulas atômicas', 'LÓGICA DE PREDICADOS', 'LÓGICA PROPOCIONAL', 'LÓGICA PROPOSICIONAL ---', 'Lógica de Floyd-Hoare', 'Quantificadores']), ('Especificação de Conjuntos Indutivos', ['1.2.2 Especificação de Conjuntos Indutivos', 'Axioma', 'CONJUNTOS E FUNÇÕES', 'Conjunto das partes', 'Conjuntos Indutivos', 'Definição por indução', 'Listas polimórficas (definição indutiva)', 'Regra', 'Relação de inclusão', 'Relação de pertinência', 'Árvores de prova', 'Árvores polimórficas (definição indutiva)'])]), ('unidade-02-verificacao-de-programas', [('Lógica de Hoare', ['2.1 Lógica de Hoare', 'Atribuição', 'Composição', 'Consequência', 'Cálculo de Floyd-Hoare', 'Lógica de Floyd-Hoare', 'Lógica de Hoare – Exercícios', 'Triplas de Hoare', 'tripla de Hoare']), ('Pré e Pós Condições', ['2.1.1 Pré e Pós Condições', 'PosFraco', 'PreForte', 'precondições e pós-condições']), ('Correção Parcial e Total', ['2.1.2 Correção Parcial e Total', 'Correção', 'Correção de Algoritmos', 'Correção e Terminação', 'Correção parcial', 'Correção total', 'Ordens bem-fundamentadas']), ('Invariante e Variante de Laço', ['2.1.3 Invariante e Variante de Laço', 'Formalização de algoritmos com invariantes de laço', 'Invariantes de laço', 'Princípio da invariante', 'invariante de laço'])])]
ENTRY {'id': 'arvores', 'title': 'arvores', 'category': 'codigo-professor', 'file_type': 'code', 'source_path': 'C:\\Users\\Humberto\\Desktop\\Moodle\\metodos-formais-para-computacao\\Provas por Indução\\arvores.thy', 'tags': '', 'manual_tags': [], 'auto_tags': ['tipo:codigo', 'bloco:bloco-05', 'unit:unidade-01-metodos-formais', 'subunit:provadores-de-teoremas'], 'manual_unit_slug': '', 'manual_timeline_block_id': '', 'notes': '', 'professor_signal': '', 'include_in_bundle': True, 'relevant_for_exam': True, 'processing_mode': 'high_fidelity', 'document_profile': 'auto', 'preferred_backend': 'auto', 'datalab_mode': 'accurate', 'formula_priority': False, 'preserve_pdf_images_in_markdown': True, 'force_ocr': False, 'extract_images': True, 'extract_tables': True, 'page_range': '', 'ocr_language': 'por,eng', 'raw_target': 'raw/code/professor/arvores.thy', 'manual_review': 'manual-review/code/arvores.md', 'base_markdown': 'code/professor/arvores.md', 'language': 'isabelle', 'approved_markdown': 'code/professor/arvores.md', 'curated_markdown': 'code/professor/arvores.md', 'computed_unit_slug': 'unidade-01-metodos-formais', 'computed_block_id': '7a5e29db-f228-4e96-bd4b-272d5b74e2ae', 'computed_block_confidence': 0.12963134328358203, 'computed_block_band': 'baixa', 'unit_match_reasons': ['winner_score=15.49', 'topic_score=15.27'], 'unit_match_confidence': 0.95, 'subunit_match_reasons': ['winner_score=8.11'], 'subunit_match_confidence': 0.8365655070318283, 'computed_subunit_slug': 'provadores-de-teoremas', 'computed_block_method': 'concept-fused', 'unit_block_conflict': {}, 'source_section': 'Provas por Indução', 'moodle_label': 'Exemplos: provas sobre arvores', 'posting_date': '2026-02-18', 'posting_date_created': '2026-02-18', 'computed_block_rationale': "O material define árvores e realiza uma prova por indução, alinhando-se diretamente com o tópico 'Indução arvores'.", 'computed_block_match_confidence': 0.6, 'coverage_units': [{'unit_slug': 'unidade-01-metodos-formais', 'topics': ['provas por inducao de especificacoes equacionais recursivas', 'provas por inducao de especificacoes recursivas'], 'confidence': 0.7, 'rule': 'card'}], 'revisar': 'ok', 'moodle_section_index': 8, 'moodle_module_index': 17, 'moodle_week_label': 'Semana 30/03/2026 a 03/04/2026: (30/03/2026): Especificações recursivas e provas por indução; (atividade assíncrona): Complementar os estudos com as leituras recomendadas. (01/04/2026): Especificações recursivas e provas por indução; (atividade assíncrona): Complementar os estudos com as leituras recomendadas. || Semana 06/04/2026 a 10/04/2026: (06/04/2026): Especificações recursivas e provas por indução em Isabelle; (08/04/2026): Especificações recursivas e provas por indução em Isabelle. || Semana 13/04/2026 a 17/04/2026: (13/04/2026): Provas em Isabelle, exercícios; (15/04/2026): Exercícios de revisão para P1. || Semana 20/04/2026 a 24/04/2026: (20/04/2026): Feriado; (22/04/2026): Prova P1.', 'temporal_block_id': '7a5e29db-f228-4e96-bd4b-272d5b74e2ae', 'temporal_block_method': 'janela-1', 'temporal_block_band': 'media', 'temporal_block_flag': False, 'temporal_block_provider': 'card', 'temporal_block_window': ['bloco-05']}
ENTRY {'id': 'invariantes', 'title': 'Invariantes', 'category': 'codigo-professor', 'file_type': 'zip', 'source_path': 'C:/Users/Humberto/Desktop/Moodle/metodos-formais-para-computacao/Verificação de Programas/invariantes.zip', 'tags': '', 'manual_tags': [], 'auto_tags': ['tipo:codigo', 'bloco:bloco-11', 'unit:unidade-02-verificacao-de-programas', 'subunit:verificacao-de-programas'], 'manual_unit_slug': '', 'manual_timeline_block_id': '', 'notes': '', 'professor_signal': '', 'include_in_bundle': True, 'relevant_for_exam': True, 'processing_mode': 'high_fidelity', 'document_profile': 'math_heavy', 'preferred_backend': 'datalab', 'datalab_mode': 'balanced', 'formula_priority': False, 'preserve_pdf_images_in_markdown': False, 'force_ocr': False, 'extract_images': False, 'extract_tables': False, 'page_range': '', 'ocr_language': 'por,eng', 'raw_target': 'raw/zip/invariantes.zip', 'extracted_files': [{'manual_review': 'manual-review/code/ex1.md', 'base_markdown': 'code/professor/ex1.md', 'language': 'dafny', 'title': 'invariantes\\ex1.dfy'}, {'manual_review': 'manual-review/code/ex2.md', 'base_markdown': 'code/professor/ex2.md', 'language': 'dafny', 'title': 'invariantes\\ex2.dfy'}, {'manual_review': 'manual-review/code/ex3.md', 'base_markdown': 'code/professor/ex3.md', 'language': 'dafny', 'title': 'invariantes\\ex3.dfy'}, {'manual_review': 'manual-review/code/ex4.md', 'base_markdown': 'code/professor/ex4.md', 'language': 'dafny', 'title': 'invariantes\\ex4.dfy'}], 'base_markdown': None, 'extraction_error': None, 'file_count': 4, 'computed_unit_slug': 'unidade-02-verificacao-de-programas', 'computed_block_method': 'concept-fused', 'computed_block_id': 'c9f5f7cf-3477-4531-be7a-f7b68727009c', 'computed_block_confidence': 0.5790625, 'computed_block_band': 'alta', 'unit_match_reasons': ['winner_score=12.94', 'topic_score=0.12', 'herdada_do_vizinho=bloco-10'], 'unit_match_confidence': 0.6304636785162286, 'unit_block_conflict': {}, 'computed_subunit_slug': 'verificacao-de-programas', 'subunit_match_reasons': ['winner_score=25.46', 'propagado-headings'], 'subunit_match_confidence': 0.9950916907605281, 'moodle_label': 'Exemplos (invariantes de laco)', 'posting_date': '2026-05-11', 'posting_date_created': '2026-05-11', 'computed_block_rationale': 'O código introduz tipos indutivos (datatypes) e predicados, que são conceitos fundamentais abordados em conjuntos indutivos.', 'computed_block_match_confidence': 0.75, 'source_section': 'Verificação de Programas', 'temporal_block_id': 'c9f5f7cf-3477-4531-be7a-f7b68727009c', 'temporal_block_method': 'disamb', 'temporal_block_band': 'alta', 'temporal_block_flag': False, 'temporal_block_provider': 'labels', 'temporal_block_window': ['171a1a09-a72d-490d-b4d8-5843cfb301b4', 'c9f5f7cf-3477-4531-be7a-f7b68727009c', 'e3bc8a61-e729-4f25-9bc5-12b8a47151e3', 'de7d1b70-fb58-4a18-ad49-d1a64c6c7684', '95d7c9fb-d9e3-43cd-b1fb-5fcebddb49f0'], 'coverage_units': [{'unit_slug': 'unidade-02-verificacao-de-programas', 'topics': [], 'confidence': 0.9, 'rule': 'card'}], 'revisar': 'ok', 'moodle_section_index': 9, 'moodle_module_index': 34, 'moodle_week_label': 'Semana 27/04/2026 a 01/05/2026: (27/04/2026): lógica de Hoare; (29/04/2026): lógica de Hoare. || Semana 04/05/2026 a 08/05/2026: (04/05/2026): lógica de Hoare, exercícios; (06/05/2026): correção parcial/total, terminação; (atividade assíncrona): complementar os estudos com as leituras recomendadas e tutoriais indicados. || Semana 11/05/2026 a 15/05/2026: (11/05/2026): Introdução ao Dafny; (13/05/2026): Introdução ao Dafny. || Semana 18/05/2026 a 22/05/2026: (18/05/2026): Arrays em Dafny; (20/05/2026): Coleções auxiliares em Dafny (sequências). || Semana 25/05/2026 a 29/05/2026: (25/05/2026): Coleções auxiliares em Dafny (conjuntos); (27/05/2026): ES Day.'}
Engenharia-Software-2 MAN_KEYS ['app', 'generated_at', 'course', 'options', 'environment', 'entries', 'logs', 'updated_at', 'turma', 'schedule_url', 'failed_entries']
meta None
TAX_TOPICS [('unidade-01-arquitetura-de-software', [('Conceito de arquitetura de software', ['1.1 Conceito de arquitetura de software', 'ARQUITETURA DE SOFTWARE ---', 'Sistemas de Software']), ('Visões arquiteturais: estrutural e dinâmica', ['1.2 Visões arquiteturais: estrutural e dinâmica']), ('Estilos e padrões arquiteturais', ['1.3 Estilos e padrões arquiteturais']), ('Camadas', ['1.3.1 Camadas'])]), ('unidade-02-integracao-de-desenvolvimento-e-operacao-devops', [('Conceito de DevOps', ['2.1 Conceito de DevOps', 'DEVOPS']), ('Gerenciamento da Configuração', ['2.2 Gerenciamento da Configuração']), ('Integração contínua (CI)', ['2.3 Integração contínua (CI)']), ('Entrega contínua (CD)', ['2.4 Entrega contínua (CD)'])])]
ENTRY {'id': 'roteiro1', 'title': 'roteiro1', 'category': 'codigo-professor', 'file_type': 'zip', 'source_path': 'C:\\Users\\Humberto\\Desktop\\Moodle\\engenharia-de-software-ii\\Microsserviços\\roteiro1.zip', 'source_section': 'Microsserviços', 'tags': '', 'manual_tags': [], 'auto_tags': ['tipo:codigo', 'bloco:bloco-02', 'unit:unidade-01-arquitetura-de-software', 'subunit:orientada-a-servicos'], 'manual_unit_slug': '', 'manual_timeline_block_id': '', 'notes': '', 'professor_signal': '', 'include_in_bundle': True, 'relevant_for_exam': True, 'processing_mode': 'high_fidelity', 'document_profile': 'auto', 'preferred_backend': 'auto', 'datalab_mode': 'accurate', 'formula_priority': False, 'preserve_pdf_images_in_markdown': True, 'force_ocr': False, 'extract_images': True, 'extract_tables': True, 'page_range': '', 'ocr_language': 'por,eng', 'raw_target': 'raw/zip/roteiro1.zip', 'extracted_files': [{'manual_review': 'manual-review/code/currencyconversion.md', 'base_markdown': 'code/professor/currencyconversion.md', 'language': 'java', 'title': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java'}, {'manual_review': 'manual-review/code/currencyconversioncontroller.md', 'base_markdown': 'code/professor/currencyconversioncontroller.md', 'language': 'java', 'title': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java'}, {'manual_review': 'manual-review/code/currencyconversionserviceapplication.md', 'base_markdown': 'code/professor/currencyconversionserviceapplication.md', 'language': 'java', 'title': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java'}, {'manual_review': 'manual-review/code/currencyexchangeproxy.md', 'base_markdown': 'code/professor/currencyexchangeproxy.md', 'language': 'java', 'title': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java'}, {'manual_review': 'manual-review/code/currencyconversionserviceapplicationtests.md', 'base_markdown': 'code/professor/currencyconversionserviceapplicationtests.md', 'language': 'java', 'title': 'roteiro1\\currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java'}, {'manual_review': 'manual-review/code/currencyexchange.md', 'base_markdown': 'code/professor/currencyexchange.md', 'language': 'java', 'title': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java'}, {'manual_review': 'manual-review/code/currencyexchangecontroller.md', 'base_markdown': 'code/professor/currencyexchangecontroller.md', 'language': 'java', 'title': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java'}, {'manual_review': 'manual-review/code/currencyexchangerepository.md', 'base_markdown': 'code/professor/currencyexchangerepository.md', 'language': 'java', 'title': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java'}, {'manual_review': 'manual-review/code/currencyexchangeserviceapplication.md', 'base_markdown': 'code/professor/currencyexchangeserviceapplication.md', 'language': 'java', 'title': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java'}, {'manual_review': 'manual-review/code/resourcenotfoundexception.md', 'base_markdown': 'code/professor/resourcenotfoundexception.md', 'language': 'java', 'title': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java'}, {'manual_review': 'manual-review/code/data.md', 'base_markdown': 'code/professor/data.md', 'language': 'sql', 'title': 'roteiro1\\currency-exchange-service\\src\\main\\resources\\data.sql'}, {'manual_review': 'manual-review/code/currencyexchangeserviceapplicationtests.md', 'base_markdown': 'code/professor/currencyexchangeserviceapplicationtests.md', 'language': 'java', 'title': 'roteiro1\\currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java'}], 'base_markdown': None, 'extraction_error': None, 'file_count': 12, 'computed_unit_slug': 'unidade-01-arquitetura-de-software', 'computed_block_method': 'concept-fused', 'computed_block_id': 'b0e2cc0d-7442-4888-87f2-2a4694598b83', 'computed_block_confidence': 0.13720198915009046, 'computed_block_band': 'baixa', 'unit_match_reasons': ['winner_score=11.73', 'topic_score=0.94'], 'unit_match_confidence': 0.950910206586214, 'unit_block_conflict': {}, 'computed_subunit_slug': 'orientada-a-servicos', 'subunit_match_reasons': ['winner_score=0.94'], 'subunit_match_confidence': 0.8665107692307692, 'computed_block_rationale': 'O código implementa dois microsserviços Spring Boot que se comunicam via Feign, demonstrando a arquitetura de microsserviços e o uso do Spring para sua construção e comunicação.', 'computed_block_match_confidence': 0.6, 'moodle_label': 'Código', 'posting_date': '2026-02-18', 'posting_date_created': '2026-02-18', 'temporal_block_id': 'b0e2cc0d-7442-4888-87f2-2a4694598b83', 'temporal_block_method': 'irmao-card', 'temporal_block_band': 'media', 'temporal_block_flag': False, 'temporal_block_provider': 'irmao-card', 'temporal_block_window': ['bloco-02'], 'coverage_units': [{'unit_slug': 'unidade-01-arquitetura-de-software', 'topics': ['1.3.4 orientada a microsservicos', '1.5 estudo de caso arquitetura orientada a microsservicos', 'criando um par de microsservicos independentes', 'estudo de caso arquitetura orientada a microsservicos'], 'confidence': 0.7, 'rule': 'card'}, {'unit_slug': 'unidade-02-integracao-de-desenvolvimento-e-operacao-devops', 'topics': ['2.7 estudo de caso integracao e implantacao de microsservicos', 'estudo de caso integracao e implantacao de microsservicos'], 'confidence': 0.7, 'rule': 'card-pratica'}], 'revisar': 'ok', 'moodle_section_index': 6, 'moodle_module_index': 14, 'moodle_week_label': 'Semana 23/03/2026 a 27/03/2026: (27/03/2026): microsserviços no Spring. || Semana 30/03/2026 a 03/04/2026: (03/04/2026): feriado.'}
ENTRY {'id': 'roteiro4', 'title': 'roteiro4', 'category': 'codigo-professor', 'file_type': 'zip', 'source_path': 'C:\\Users\\Humberto\\Desktop\\Moodle\\engenharia-de-software-ii\\Microsserviços\\roteiro4.zip', 'source_section': 'Microsserviços', 'tags': '', 'manual_tags': [], 'auto_tags': ['tipo:codigo', 'bloco:bloco-04', 'unit:unidade-01-arquitetura-de-software', 'subunit:orientada-a-servicos'], 'manual_unit_slug': '', 'manual_timeline_block_id': '', 'notes': '', 'professor_signal': '', 'include_in_bundle': True, 'relevant_for_exam': True, 'processing_mode': 'high_fidelity', 'document_profile': 'auto', 'preferred_backend': 'auto', 'datalab_mode': 'accurate', 'formula_priority': False, 'preserve_pdf_images_in_markdown': True, 'force_ocr': False, 'extract_images': True, 'extract_tables': True, 'page_range': '', 'ocr_language': 'por,eng', 'raw_target': 'raw/zip/roteiro4.zip', 'extracted_files': [{'manual_review': 'manual-review/code/apigatewayapplication.md', 'base_markdown': 'code/professor/apigatewayapplication.md', 'language': 'java', 'title': 'roteiro4\\api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\ApiGatewayApplication.java'}, {'manual_review': 'manual-review/code/fallbackcontroller.md', 'base_markdown': 'code/professor/fallbackcontroller.md', 'language': 'java', 'title': 'roteiro4\\api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\FallbackController.java'}, {'manual_review': 'manual-review/code/loggingfilter.md', 'base_markdown': 'code/professor/loggingfilter.md', 'language': 'java', 'title': 'roteiro4\\api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\LoggingFilter.java'}, {'manual_review': 'manual-review/code/apigatewayapplicationtests.md', 'base_markdown': 'code/professor/apigatewayapplicationtests.md', 'language': 'java', 'title': 'roteiro4\\api-gateway\\src\\test\\java\\com\\engsoft2\\api_gateway\\ApiGatewayApplicationTests.java'}, {'manual_review': 'manual-review/code/currencyconversion.md', 'base_markdown': 'code/professor/currencyconversion.md', 'language': 'java', 'title': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java'}, {'manual_review': 'manual-review/code/currencyconversioncontroller.md', 'base_markdown': 'code/professor/currencyconversioncontroller.md', 'language': 'java', 'title': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java'}, {'manual_review': 'manual-review/code/currencyconversionserviceapplication.md', 'base_markdown': 'code/professor/currencyconversionserviceapplication.md', 'language': 'java', 'title': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java'}, {'manual_review': 'manual-review/code/currencyexchangefallback.md', 'base_markdown': 'code/professor/currencyexchangefallback.md', 'language': 'java', 'title': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeFallback.java'}, {'manual_review': 'manual-review/code/currencyexchangeproxy.md', 'base_markdown': 'code/professor/currencyexchangeproxy.md', 'language': 'java', 'title': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java'}, {'manual_review': 'manual-review/code/currencyconversionserviceapplicationtests.md', 'base_markdown': 'code/professor/currencyconversionserviceapplicationtests.md', 'language': 'java', 'title': 'roteiro4\\currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java'}, {'manual_review': 'manual-review/code/currencyexchange.md', 'base_markdown': 'code/professor/currencyexchange.md', 'language': 'java', 'title': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java'}, {'manual_review': 'manual-review/code/currencyexchangecontroller.md', 'base_markdown': 'code/professor/currencyexchangecontroller.md', 'language': 'java', 'title': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java'}, {'manual_review': 'manual-review/code/currencyexchangerepository.md', 'base_markdown': 'code/professor/currencyexchangerepository.md', 'language': 'java', 'title': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java'}, {'manual_review': 'manual-review/code/currencyexchangeserviceapplication.md', 'base_markdown': 'code/professor/currencyexchangeserviceapplication.md', 'language': 'java', 'title': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java'}, {'manual_review': 'manual-review/code/resourcenotfoundexception.md', 'base_markdown': 'code/professor/resourcenotfoundexception.md', 'language': 'java', 'title': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java'}, {'manual_review': 'manual-review/code/data.md', 'base_markdown': 'code/professor/data.md', 'language': 'sql', 'title': 'roteiro4\\currency-exchange-service\\src\\main\\resources\\data.sql'}, {'manual_review': 'manual-review/code/currencyexchangeserviceapplicationtests.md', 'base_markdown': 'code/professor/currencyexchangeserviceapplicationtests.md', 'language': 'java', 'title': 'roteiro4\\currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java'}, {'manual_review': 'manual-review/code/namingserverapplication.md', 'base_markdown': 'code/professor/namingserverapplication.md', 'language': 'java', 'title': 'roteiro4\\naming-server\\src\\main\\java\\com\\engsoft2\\naming_server\\NamingServerApplication.java'}, {'manual_review': 'manual-review/code/namingserverapplicationtests.md', 'base_markdown': 'code/professor/namingserverapplicationtests.md', 'language': 'java', 'title': 'roteiro4\\naming-server\\src\\test\\java\\com\\engsoft2\\naming_server\\NamingServerApplicationTests.java'}], 'base_markdown': None, 'extraction_error': None, 'file_count': 19, 'computed_unit_slug': 'unidade-01-arquitetura-de-software', 'computed_block_method': 'concept-fused', 'computed_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'computed_block_confidence': 0.10509109026963645, 'computed_block_band': 'baixa', 'unit_match_reasons': ['winner_score=19.24', 'topic_score=3.49'], 'unit_match_confidence': 0.95, 'unit_block_conflict': {}, 'computed_subunit_slug': 'orientada-a-servicos', 'subunit_match_reasons': ['winner_score=0.94'], 'subunit_match_confidence': 0.8665107692307692, 'computed_block_rationale': 'O código demonstra a implementação de um ecossistema de microsserviços completo com Spring Cloud, cobrindo o uso de API Gateway e Service Discovery.', 'computed_block_match_confidence': 0.6, 'temporal_block_id': 'a0d38bad-e123-4b82-b8d0-03f6724b9617', 'temporal_block_method': 'irmao-card', 'temporal_block_band': 'media', 'temporal_block_flag': False, 'temporal_block_provider': 'irmao-card', 'temporal_block_window': ['bloco-07'], 'coverage_units': [{'unit_slug': 'unidade-01-arquitetura-de-software', 'topics': ['1.3.4 orientada a microsservicos', '1.5 estudo de caso arquitetura orientada a microsservicos', 'criando um par de microsservicos independentes', 'estudo de caso arquitetura orientada a microsservicos'], 'confidence': 0.7, 'rule': 'card'}, {'unit_slug': 'unidade-02-integracao-de-desenvolvimento-e-operacao-devops', 'topics': ['2.7 estudo de caso integracao e implantacao de microsservicos', 'estudo de caso integracao e implantacao de microsservicos'], 'confidence': 0.7, 'rule': 'card-pratica'}], 'moodle_label': 'Código', 'posting_date': '2026-06-05', 'posting_date_created': '2026-06-05', 'revisar': 'ok', 'moodle_section_index': 6, 'moodle_module_index': 32, 'moodle_week_label': 'Semana 27/04/2026 a 01/05/2026: (01/05/2026): feriado. || Semana 04/05/2026 a 08/05/2026: (08/05/2026): prova P1. || Semana 11/05/2026 a 15/05/2026: (15/05/2026): microsserviços com Spring, circuit-breaker.'}

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f,a,b in [('src/builder/artifacts/repo.py',1697,1755),('src/builder/artifacts/repo.py',1804,1830),('src/builder/artifacts/navigation.py',35,84),('src/builder/extraction/entry_signals.py',79,106)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))):print(f'{i+1}: {ls[i]}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 265ms:[0m

FILE src/builder/artifacts/repo.py
1697: def _glossary_curation_key(term: str) -> str:
1698:     """Chave do sidecar = texto do topico como o glossario o escreve, COM o codigo de outline
1699:     ("1.2 Modelos OSI e TCP/IP"; R8: "3.1 Conceitos basicos" != "5.1 Conceitos basicos").
1700:     Normaliza so marcadores: `*` fora, "1.2." -> "1.2", espacos, casefold. Sem codigo, o label."""
1701:     text = " ".join(str(term or "").replace("*", "").split())
1702:     text = re.sub(r"^(\d+(?:\.\d+)*)\.(\s+)", r"\1\2", text)
1703:     return text.casefold()
1704: 
1705: 
1706: def load_glossary_curation(root_dir: Optional[Path]) -> Dict[str, List[str]]:
1707:     """{termo (casefold): [sinonimos]} de `course/.glossary_curation.json`.
1708: 
1709:     2026-08-25 (alavanca iii da subunidade): o GLOSSARY.md e artefato DERIVADO,
1710:     regravado a cada build a partir do plano + seed; a taxonomia consome o texto
1711:     gerado, nao o arquivo. Curadoria a mao no .md morre no proximo build. Este
1712:     sidecar e o lugar que sobrevive (mesmo padrao do .card_block_map): os
1713:     sinonimos entram em "Sinonimos aceitos" e viram alias do topico via
1714:     `_glossary_aliases_for_topic`. E conteudo por curso (vocabulario dos
1715:     algoritmos que o plano nao nomeia: "Modelos Preditivos" <- perceptron,
1716:     k-NN, arvore de decisao), nunca regra de motor. Medido no IA u05: 4 -> 37/39.
1717:     Formato: {"<Termo do plano>": {"synonyms": ["..."]}}."""
1718:     if not root_dir:
1719:         return {}
1720:     out: Dict[str, List[str]] = {}
1721:     secoes = _moodle_section_names(root_dir)
1722:     # Manual + compilado por LLM (Fase 1b, 02/09: `.glossary_curation.llm.json`, mesmo formato,
1723:     # chaves `_*` = metadados). Fundidos sem repetir; manual vem primeiro.
1724:     for name in (_GLOSSARY_CURATION_NAME, _GLOSSARY_LLM_NAME):
1725:         path = Path(root_dir) / "course" / name
1726:         if not path.is_file():
1727:             continue
1728:         try:
1729:             data = json.loads(path.read_text(encoding="utf-8"))
1730:         except (ValueError, OSError):
1731:             continue
1732:         for term, info in (data or {}).items():
1733:             if str(term).startswith("_"):
1734:                 continue
1735:             syn = info.get("synonyms") if isinstance(info, dict) else info
1736:             vals = [" ".join(str(s).split()) for s in (syn or []) if " ".join(str(s).split())]
1737:             if name == _GLOSSARY_LLM_NAME and secoes:
1738:                 # Higiene (CG 05/09): o compilador recebe NOMES DE SECAO do Moodle como termos e, sem
1739:                 # topico que case, pendura-os no topico generico da unidade 1 ("Morfologia Matematica"
1740:                 # virou alias de "Areas relacionadas" e puxava o bloco para u01). Secao e estrutura, nao
1741:                 # vocabulario; so o sinonimo COMPILADO e filtrado — o manual e decisao humana.
1742:                 vals = [v for v in vals if _normalize_secao(v) not in secoes]
1743:             if not vals:
1744:                 continue
1745:             key = _glossary_curation_key(term)
1746:             atual = out.setdefault(key, [])
1747:             seen = {v.casefold() for v in atual}
1748:             for v in vals:
1749:                 if v.casefold() not in seen:
1750:                     atual.append(v)
1751:                     seen.add(v.casefold())
1752:     return out
1753: 
1754: 
1755: def merge_glossary_synonyms(seed: str, curated: List[str]) -> str:

FILE src/builder/artifacts/repo.py
1804:     teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
1805:     units = parse_units_from_teaching_plan_fn(teaching_plan) if teaching_plan else []
1806:     evidence_docs = collect_glossary_evidence_fn(
1807:         root_dir, manifest_entries=manifest_entries, unit_titles=[title for title, _t in units],
1808:     ) if root_dir else []
1809:     curated_synonyms = load_glossary_curation(root_dir)
1810: 
1811:     candidates = []
1812:     for unit_title, topics in units:
1813:         for topic in topics:
1814:             candidates.append((topic_text_fn(topic), unit_title))
1815: 
1816:     if candidates:
1817:         lines.append("> Termos extraídos automaticamente do plano de ensino.")
1818:         lines.append("> Definições iniciais curtas são geradas no build para reduzir custo de contexto no tutor web.")
1819:         lines.append("")
1820:         for term, unit_title in candidates:
1821:             evidence = find_glossary_evidence_fn(term, unit_title, evidence_docs)
1822:             definition, synonyms, not_confuse = seed_glossary_fields_fn(term, unit_title, evidence=evidence)
1823:             synonyms = merge_glossary_synonyms(synonyms, curated_synonyms.get(_glossary_curation_key(term), []))
1824:             lines += [
1825:                 f"## {term}",
1826:                 f"**Definição:** {definition}",
1827:                 f"**Sinônimos aceitos:** {synonyms}",
1828:                 f"**Não confundir com:** {not_confuse}",
1829:                 f"**Aparece em:** {unit_title}",
1830:                 "",

FILE src/builder/artifacts/navigation.py
35:     for tag in entry.get("auto_tags") or []:
36:         if tag.startswith("subunit:"):
37:             return tag[len("subunit:"):]
38:     return ""
39: 
40: 
41: def _entry_priority_label(entry: dict) -> str:
42:     category = (entry.get("category") or "").strip().lower()
43:     if entry.get("relevant_for_exam") or entry.get("include_in_bundle"):
44:         return "alta"
45:     if category in EXAM_CATEGORIES or category in EXERCISE_CATEGORIES:
46:         return "alta"
47:     if category in {"material-de-aula", "codigo-professor", "quadro-branco"}:
48:         return "media"
49:     return "normal"
50: 
51: 
52: def _entry_usage_hint(entry: dict) -> str:
53:     category = (entry.get("category") or "").strip().lower()
54:     if category in {"material-de-aula", "slides", "apostila"}:
55:         return "teoria base"
56:     if category in EXAM_CATEGORIES:
57:         return "provas e revisão"
58:     if category in EXERCISE_CATEGORIES:
59:         return "exercícios"
60:     if category in ASSIGNMENT_CATEGORIES:
61:         return "trabalhos"
62:     if category in CODE_CATEGORIES:
63:         return "exemplos de código"
64:     if category in WHITEBOARD_CATEGORIES:
65:         return "explicações do professor"
66:     if category in {"cronograma", "bibliografia", "referencias"}:
67:         return "referência geral"
68:     return "consulta pontual"
69: 
70: 
71: def _entry_markdown_path_for_file_map(root_dir: Optional[Path], entry: dict) -> Optional[Path]:
72:     if not root_dir:
73:         return None
74:     for key in ["approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"]:
75:         rel_path = entry.get(key)
76:         if not rel_path or not str(rel_path).lower().endswith(".md"):
77:             continue
78:         md_path = root_dir / rel_path
79:         if md_path.exists() and md_path.is_file():
80:             return md_path
81:     return None
82: 
83: 
84: def _entry_markdown_text_for_file_map(root_dir: Optional[Path], entry: dict) -> str:

FILE src/builder/extraction/entry_signals.py
79: 
80: 
81: # Prefixos que o PROPRIO motor escreve (`resolver_apply` espelha o que ele
82: # computou). Realimentar o scorer com eles faz o sistema re-eleger a resposta
83: # anterior: medido 2026-08-19 rodando o mesmo scorer sobre os manifests antes e
84: # depois de um reprocess — 131 -> 129 acertos, toda a perda no MF, sem ninguem
85: # ter mudado nada. `topico:`/`ferramenta:`/`tipo:` NAO entram aqui: vem do
86: # catalogo/taxonomia, nao da atribuicao.
87: _PREFIXOS_ESPELHO_DO_MOTOR = ("unit:", "subunit:", "bloco:", "block:")
88: 
89: 
90: def _sem_eco(tags: List[str]) -> List[str]:
91:     return [t for t in tags if not str(t).lower().startswith(_PREFIXOS_ESPELHO_DO_MOTOR)]
92: 
93: 
94: def texto_para_score(markdown_text: str) -> str:
95:     """Markdown sem os blocos de DESCRICAO DE IMAGEM. A descricao serve ao ALUNO (contexto da figura no tutor) e fica no
96:     arquivo; ela nao deve pontuar. Medido em 07/09: a caption generica do Datalab, em ingles ("A 4x4 grid showing the
97:     result of erosion", "Logos for GRU and PUCRS"), entra no vocabulario propagado do CURSO — os materiais confiantes doam
98:     alias — e desvia a subunidade de materiais que nem tem imagem. Ablando os blocos: +2 materiais 100% certos, subunidade
99:     193 -> 195/233, erro confiante 19 -> 18, fila 91 -> 89 (`c1-3/ablate_descricoes.log`)."""
100:     texto = str(markdown_text or "")
101:     if "IMAGE_DESCRIPTION" not in texto:
102:         return texto
103:     return _IMAGE_DESC_ORPHANS_RE.sub("\n", _IMAGE_DESC_BLOCK_RE.sub("", texto))
104: 
105: 
106: def collect_entry_unit_signals(entry: dict, markdown_text: str) -> Dict[str, str]:

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries']
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

for sig in names:
 for mode in ['sem','determ','com']:
  r=evaluate(sig,mode);print(sig,mode,r[:2])
  if sig in ['MF','ES2']:
   print('ERRORS',[(k,r[3][k]) for k,v in r[2].items() if not v])

'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
import json
for nm,ids in [('Metodos-Formais',['invariantes','terminacao','arvores','intro','listas','exercicios-conjuntos','classes-parte2']),('Engenharia-Software-2',['roteiro1','roteiro2','roteiro3','roteiro4','roteiro5','roteiro6','roteiro7','roteiro7-history-service'])]:
 p=Path('..')/(nm+'-Tutor');m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))['entries'];cc=json.loads((p/'code_curation.json').read_text(encoding='utf-8'))['entries']
 for e in m:
  if e['id'] in ids:
   print(nm,e['id'],'GEMINI',cc.get(e['id'],{}).get('summary'))
   if e.get('base_markdown'):
    q=p/e['base_markdown'];print('MD_EXISTS',q.exists(),'MD_CHARS',len(q.read_text(encoding='utf-8')) if q.exists() else 0)
'@ | python -B -; rg -n 'safe_name_c|def process_zip|CODE_EXT|smv' src/builder/core/source_importers.py; Get-Content docs/reports/_harness-2026-09-04/c1-3/mede_zips_conteudo_perdido.log | Select-Object -Last 12"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 398ms:[0m
Metodos-Formais arvores GEMINI {'inferred_title': 'Definição de Árvores Binárias e Prova por Indução em Isabelle/HOL', 'language': 'isabelle', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['árvore binária', 'tipo de dado indutivo', 'recursão', 'função espelho', 'indução estrutural', 'prova de teorema', 'Isabelle/HOL'], 'summary': 'Este código demonstra a definição de um tipo de dado indutivo para árvores binárias em Isabelle/HOL, juntamente com a implementação de uma função recursiva para espelhar a árvore. Ele ilustra o processo de prova de uma propriedade sobre a função espelho (que espelhar duas vezes retorna a árvore original) utilizando indução estrutural.', 'files': [{'name': 'arvores.thy', 'role': 'definição e prova em Isabelle'}], 'suggested_block_id': 'bloco-05', 'suggested_secondary_ids': ['bloco-04', 'bloco-06'], 'match_rationale': "O material define árvores e realiza uma prova por indução, alinhando-se diretamente com o tópico 'Indução arvores'.", 'primary_block_id': 'bloco-05', 'secondary_block_ids': ['bloco-04', 'bloco-06'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
MD_EXISTS True MD_CHARS 1239
Metodos-Formais intro GEMINI {'inferred_title': 'Definição de Tipos Indutivos, Funções Recursivas e Provas por Indução em Isabelle', 'language': 'Isabelle', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Tipo Indutivo', 'Recursão Primitiva', 'Prova por Indução', 'Datatype', 'Teorema', 'Isabelle/HOL', 'Regra de Indução'], 'summary': 'Este código Isabelle demonstra a definição de tipos indutivos, como os números naturais, e a criação de funções por recursão primitiva. Ele explora as regras de indução geradas automaticamente para esses tipos e exemplifica a prova de teoremas usando indução, como a associatividade da adição. O material serve como uma introdução prática à especificação e verificação em Isabelle.', 'files': [{'name': 'intro.thy', 'role': 'exemplo de teoria'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-05', 'bloco-06'], 'match_rationale': 'O código introduz tipos indutivos e funções recursivas, demonstrando a prova por indução, elementos centrais da teoria de conjuntos indutivos e equações recursivas.', 'primary_block_id': 'bloco-04', 'secondary_block_ids': ['bloco-05', 'bloco-06'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
MD_EXISTS True MD_CHARS 1175
Metodos-Formais listas GEMINI {'inferred_title': 'Definição Recursiva de Concatenação de Listas e Prova de Associatividade em Isabelle', 'language': 'isabelle', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['lista', 'função recursiva', 'concatenação de listas', 'indução estrutural', 'associatividade', 'prova interativa', 'Isabelle/HOL'], 'summary': 'Este código Isabelle define recursivamente a operação de concatenação de listas (`cat`) e, em seguida, demonstra uma prova formal de sua propriedade de associatividade. Ele ilustra o uso de indução estrutural e a metodologia de prova interativa em Isabelle para verificar propriedades de estruturas de dados básicas.', 'files': [{'name': 'listas.thy', 'role': 'definição e prova em Isabelle'}], 'suggested_block_id': 'bloco-05', 'suggested_secondary_ids': ['bloco-06', 'bloco-04'], 'match_rationale': 'O material demonstra a aplicação de indução estrutural para provar propriedades de estruturas de dados recursivas como listas, alinhando-se bem com o tema de indução.', 'primary_block_id': 'bloco-05', 'secondary_block_ids': ['bloco-06', 'bloco-04'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
MD_EXISTS True MD_CHARS 1447
Metodos-Formais exercicios-conjuntos GEMINI {'inferred_title': 'Verificação de métodos em Dafny para manipulação de arrays e sequências', 'language': 'dafny', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['invariante de laço', 'pré-condição', 'pós-condição', 'arrays', 'sequências', 'multisets', 'predicado ghost', 'função ghost', 'verificação de programas', 'lógica de Hoare', 'algoritmos de busca', 'algoritmos de ordenação'], 'summary': 'Este bundle de exemplos em Dafny demonstra a verificação formal de diversos algoritmos fundamentais, como encontrar o máximo em um array, verificar permutação de sequências, calcular o produto de elementos e implementar busca binária e Bubble Sort. Os exemplos utilizam intensivamente pré e pós-condições, invariantes de laço, e funções/predicados ghost para provar a correção dos programas.', 'files': [{'name': 'exercicios_conjuntos\\exercicio2.dfy', 'role': 'implementação verificada'}, {'name': 'exercicios_conjuntos\\exercicio3b.dfy', 'role': 'implementação verificada'}, {'name': 'exercicios_conjuntos\\exercicio4.dfy', 'role': 'implementação verificada'}, {'name': 'exercicios_conjuntos\\exercicio5.dfy', 'role': 'implementação verificada'}, {'name': 'exercicios_conjuntos\\exercicio5b.dfy', 'role': 'implementação verificada'}], 'suggested_block_id': 'bloco-11', 'suggested_secondary_ids': ['bloco-13', 'bloco-15'], 'match_rationale': 'Os exemplos demonstram a aplicação de invariantes de laço, pré/pós-condições e o uso de funções/predicados ghost para provar a correção de algoritmos em Dafny, alinhando-se diretamente aos tópicos de correção parcial e total de programas.', 'primary_block_id': 'c9f5f7cf-3477-4531-be7a-f7b68727009c', 'secondary_block_ids': ['de7d1b70-fb58-4a18-ad49-d1a64c6c7684', '95d7c9fb-d9e3-43cd-b1fb-5fcebddb49f0'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Metodos-Formais invariantes GEMINI {'inferred_title': 'Definição e uso de tipos indutivos simples e predicados em Dafny', 'language': 'dafny', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['datatype', 'tipo indutivo', 'predicate', 'instanciação de tipo', 'verificação de propriedade'], 'summary': 'Este código demonstra a criação de tipos de dados indutivos simples (datatypes) em Dafny, mostrando como definir um tipo enumerado e como criar e usar predicados para verificar propriedades sobre instâncias desse tipo.', 'files': [{'name': 'ex1.dfy', 'role': 'exemplo de datatype e predicate'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-12'], 'match_rationale': 'O código introduz tipos indutivos (datatypes) e predicados, que são conceitos fundamentais abordados em conjuntos indutivos.', 'primary_block_id': 'bloco-04', 'secondary_block_ids': ['bloco-12'], 'block_match_confidence': 0.75, 'block_match_method': 'consensus'}
Metodos-Formais terminacao GEMINI {'inferred_title': 'Definição e Uso de Tipos Indutivos Simples (Datatypes) em Dafny', 'language': 'dafny', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['datatype', 'tipo indutivo', 'enumeração', 'predicado', 'verificação de tipos', 'programa Dafny'], 'summary': "Este código demonstra a criação e uso de tipos de dados indutivos simples (datatype) em Dafny, que permitem definir novos tipos como uniões disjuntas de construtores. Ele ilustra como definir um tipo 'Cor' e usar predicados para verificar suas propriedades em um método 'Main'.", 'files': [{'name': 'ex1.dfy', 'role': 'exemplo de datatype'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-12'], 'match_rationale': 'O arquivo exemplifica a definição de tipos indutivos (datatypes), um tópico fundamental em conjuntos e equações recursivas.', 'primary_block_id': 'bloco-04', 'secondary_block_ids': ['bloco-12'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Metodos-Formais classes-parte2 GEMINI {'inferred_title': 'Implementação Verificada de Árvore Binária de Busca com Abstração', 'language': 'dafny', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Árvore Binária de Busca (ABB)', 'Invariantes de Classe', 'Funções Abstratas (ghost variables)', 'Tripleto de Hoare Estendido', 'Encapsulamento', 'Relação de Abstração', 'Conjuntos (set)', 'Mapas (map)'], 'summary': "Este código Dafny demonstra a implementação e verificação de uma Árvore Binária de Busca. Ele foca na utilização de variáveis 'ghost' e predicados para definir a função de abstração e os invariantes de classe, garantindo a correção das operações de busca e adição.", 'files': [{'name': 'classes_parte2\\ArvoreBinariaBusca.dfy', 'role': 'implementacao_e_verificacao_abb'}], 'suggested_block_id': 'bloco-15', 'suggested_secondary_ids': ['bloco-04', 'bloco-13'], 'match_rationale': 'O material exemplifica a lógica de programas e verificação com Dafny, utilizando conceitos de orientação a objetos, variáveis ghost e abstração para uma estrutura de dados complexa.', 'primary_block_id': '95d7c9fb-d9e3-43cd-b1fb-5fcebddb49f0', 'secondary_block_ids': ['7ccdaf5e-76b8-48e5-82b5-05f80b3f054b', 'de7d1b70-fb58-4a18-ad49-d1a64c6c7684'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro1 GEMINI {'inferred_title': 'Implementação de Microsserviços de Câmbio e Conversão com Spring Boot e Feign', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Boot', 'RESTful APIs', 'Feign Client', 'Service Discovery (implícito)', 'Spring Data JPA', 'Injeção de Dependências', 'Tratamento de Exceções'], 'summary': 'Este bundle apresenta dois microsserviços Spring Boot: um de câmbio que fornece taxas de conversão e outro de conversão de moedas que consome o primeiro via Feign. Ele demonstra a comunicação entre serviços, a exposição de APIs REST e a persistência de dados para exemplificar a arquitetura de microsserviços.', 'files': [{'name': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java', 'role': 'Modelo de dados'}, {'name': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java', 'role': 'Controlador REST (Serviço de Conversão)'}, {'name': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java', 'role': 'Aplicação Spring Boot (Serviço de Conversão)'}, {'name': 'roteiro1\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java', 'role': 'Cliente Feign para serviço de câmbio'}, {'name': 'roteiro1\\currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java', 'role': 'Teste de unidade (Serviço de Conversão)'}, {'name': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java', 'role': 'Entidade JPA'}, {'name': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java', 'role': 'Controlador REST (Serviço de Câmbio)'}, {'name': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java', 'role': 'Repositório de dados'}, {'name': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java', 'role': 'Aplicação Spring Boot (Serviço de Câmbio)'}, {'name': 'roteiro1\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java', 'role': 'Exceção personalizada'}, {'name': 'roteiro1\\currency-exchange-service\\src\\main\\resources\\data.sql', 'role': 'Script de inicialização do banco de dados'}, {'name': 'roteiro1\\currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java', 'role': 'Teste de unidade (Serviço de Câmbio)'}], 'suggested_block_id': 'bloco-02', 'suggested_secondary_ids': ['bloco-10', 'bloco-04'], 'match_rationale': 'O código implementa dois microsserviços Spring Boot que se comunicam via Feign, demonstrando a arquitetura de microsserviços e o uso do Spring para sua construção e comunicação.', 'primary_block_id': 'b0e2cc0d-7442-4888-87f2-2a4694598b83', 'secondary_block_ids': ['17b8da72-b970-4db3-b49e-7cd196945b39', '8a2e86f0-fb4a-4487-86ec-07e74c73d88a'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro2 GEMINI {'inferred_title': 'Implementação de Microsserviços com Spring Cloud, Feign e Eureka para Conversão de Moedas', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Boot', 'Spring Cloud', 'Service Discovery (Eureka)', 'Feign Client', 'RESTful APIs', 'Circuit Breaker Pattern', 'Spring Data JPA'], 'summary': 'Este bundle demonstra uma arquitetura de microsserviços utilizando Spring Boot e Spring Cloud, com serviços de câmbio e conversão de moedas. Ele ilustra a descoberta de serviços com Eureka, a comunicação entre serviços via Feign, e a implementação de tolerância a falhas através de fallback.', 'files': [{'name': 'roteiro2\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java', 'role': 'Modelo de dados'}, {'name': 'roteiro2\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java', 'role': 'Controlador REST'}, {'name': 'roteiro2\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java', 'role': 'Aplicação principal'}, {'name': 'roteiro2\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java', 'role': 'Cliente Feign'}, {'name': 'roteiro2\\currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java', 'role': 'Teste unitário'}, {'name': 'roteiro2\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java', 'role': 'Entidade JPA'}, {'name': 'roteiro2\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java', 'role': 'Controlador REST'}, {'name': 'roteiro2\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java', 'role': 'Repositório JPA'}, {'name': 'roteiro2\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java', 'role': 'Aplicação principal'}, {'name': 'roteiro2\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java', 'role': 'Exceção personalizada'}, {'name': 'roteiro2\\currency-exchange-service\\src\\main\\resources\\data.sql', 'role': 'Script de dados'}, {'name': 'roteiro2\\currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java', 'role': 'Teste unitário'}, {'name': 'roteiro2\\naming-server\\src\\main\\java\\com\\engsoft2\\naming_server\\NamingServerApplication.java', 'role': 'Servidor de Nomes (Eureka)'}, {'name': 'roteiro2\\naming-server\\src\\test\\java\\com\\engsoft2\\naming_server\\NamingServerApplicationTests.java', 'role': 'Teste unitário'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-07', 'bloco-02'], 'match_rationale': 'O bundle exemplifica a implementação de Service Discovery (Eureka) e clientes declarativos (Feign), conceitos chave do bloco 04.', 'primary_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'secondary_block_ids': ['a0d38bad-e123-4b82-b8d0-03f6724b9617', 'b0e2cc0d-7442-4888-87f2-2a4694598b83'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro3 GEMINI {'inferred_title': 'Implementação de Microsserviços com Spring Cloud, Service Discovery e API Gateway', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Boot', 'Spring Cloud', 'API Gateway', 'Service Discovery (Eureka)', 'Cliente Feign', 'RESTful APIs', 'Circuit Breaker Pattern'], 'summary': 'Este bundle demonstra uma arquitetura completa de microsserviços utilizando Spring Cloud, incluindo um servidor de nomes (Eureka) para descoberta de serviços, um API Gateway para roteamento e filtros, e dois serviços interconectados de câmbio de moeda. Ele ilustra a comunicação entre os serviços usando Feign e a implementação do padrão Circuit Breaker para resiliência. O exemplo aborda a configuração de cada componente para operar em um ecossistema distribuído.', 'files': [{'name': 'api-gateway/src/main/java/com/engsoft2/api_gateway/ApiGatewayApplication.java', 'role': 'Aplicação principal do API Gateway'}, {'name': 'api-gateway/src/main/java/com/engsoft2/api_gateway/LoggingFilter.java', 'role': 'Filtro de logging global do API Gateway'}, {'name': 'api-gateway/src/test/java/com/engsoft2/api_gateway/ApiGatewayApplicationTests.java', 'role': 'Teste de contexto do API Gateway'}, {'name': 'currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyConversion.java', 'role': 'Modelo de dados para conversão de moeda'}, {'name': 'currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyConversionController.java', 'role': 'Controlador REST do serviço de conversão de moeda'}, {'name': 'currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyConversionServiceApplication.java', 'role': 'Aplicação principal do serviço de conversão de moeda'}, {'name': 'currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyExchangeProxy.java', 'role': 'Cliente Feign para o serviço de câmbio'}, {'name': 'currency-conversion-service/src/test/java/com/engsoft2/currency_conversion_service/CurrencyConversionServiceApplicationTests.java', 'role': 'Teste de contexto do serviço de conversão'}, {'name': 'currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchange.java', 'role': 'Entidade JPA para taxas de câmbio'}, {'name': 'currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchangeController.java', 'role': 'Controlador REST do serviço de câmbio'}, {'name': 'currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchangeRepository.java', 'role': 'Repositório de dados para taxas de câmbio'}, {'name': 'currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchangeServiceApplication.java', 'role': 'Aplicação principal do serviço de câmbio'}, {'name': 'currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/ResourceNotFoundException.java', 'role': 'Exceção para recurso não encontrado'}, {'name': 'currency-exchange-service/src/main/resources/data.sql', 'role': 'Script de inicialização de dados SQL para taxas de câmbio'}, {'name': 'currency-exchange-service/src/test/java/com/engsoft2/currency_exchange_service/CurrencyExchangeServiceApplicationTests.java', 'role': 'Teste de contexto do serviço de câmbio'}, {'name': 'naming-server/src/main/java/com/engsoft2/naming_server/NamingServerApplication.java', 'role': 'Aplicação principal do servidor de nomes (Eureka)'}, {'name': 'naming-server/src/test/java/com/engsoft2/naming_server/NamingServerApplicationTests.java', 'role': 'Teste de contexto do servidor de nomes'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-07', 'bloco-02'], 'match_rationale': 'O bundle demonstra a implementação de microsserviços Spring Cloud, incluindo Service Discovery com Eureka e um API Gateway, conforme os tópicos do bloco.', 'primary_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'secondary_block_ids': ['a0d38bad-e123-4b82-b8d0-03f6724b9617', 'b0e2cc0d-7442-4888-87f2-2a4694598b83'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro5 GEMINI {'inferred_title': 'Microsserviços com Spring Cloud: Gateway, Descoberta de Serviço e Circuit Breaker', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Boot', 'Spring Cloud Gateway', 'Service Discovery (Eureka)', 'Feign Client', 'Circuit Breaker', 'Mecanismos de Fallback', 'RESTful APIs'], 'summary': 'Este bundle implementa uma arquitetura de microsserviços para um sistema de câmbio de moedas, demonstrando a interação entre serviços. Inclui componentes essenciais como API Gateway para roteamento e filtros, um servidor de nomes (Eureka) para descoberta de serviços, e clientes Feign com mecanismos de fallback para resiliência e tratamento de falhas.', 'files': [{'name': 'ApiGatewayApplication.java', 'role': 'Inicializador do API Gateway'}, {'name': 'FallbackController.java', 'role': 'Controller de Fallback do Gateway'}, {'name': 'LoggingFilter.java', 'role': 'Filtro de log do Gateway'}, {'name': 'ApiGatewayApplicationTests.java', 'role': 'Testes do API Gateway'}, {'name': 'CurrencyConversion.java', 'role': 'Modelo de dados de conversão'}, {'name': 'CurrencyConversionController.java', 'role': 'Controller do serviço de conversão'}, {'name': 'CurrencyConversionServiceApplication.java', 'role': 'Inicializador do serviço de conversão'}, {'name': 'CurrencyExchangeFallback.java', 'role': 'Implementação de fallback do Feign'}, {'name': 'CurrencyExchangeProxy.java', 'role': 'Interface Feign para câmbio'}, {'name': 'CurrencyConversionServiceApplicationTests.java', 'role': 'Testes do serviço de conversão'}, {'name': 'CurrencyExchange.java', 'role': 'Modelo de dados de câmbio'}, {'name': 'CurrencyExchangeController.java', 'role': 'Controller do serviço de câmbio'}, {'name': 'CurrencyExchangeRepository.java', 'role': 'Repositório de dados de câmbio'}, {'name': 'CurrencyExchangeServiceApplication.java', 'role': 'Inicializador do serviço de câmbio'}, {'name': 'ResourceNotFoundException.java', 'role': 'Exceção de recurso não encontrado'}, {'name': 'data.sql', 'role': 'Script de inicialização de dados'}, {'name': 'CurrencyExchangeServiceApplicationTests.java', 'role': 'Testes do serviço de câmbio'}, {'name': 'NamingServerApplication.java', 'role': 'Inicializador do servidor de nomes Eureka'}, {'name': 'NamingServerApplicationTests.java', 'role': 'Testes do servidor de nomes'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-07'], 'match_rationale': 'O bundle demonstra a configuração e o uso de um API Gateway e um servidor de nomes Eureka para descoberta de serviços em uma arquitetura de microsserviços, além de implementar mecanismos de circuit breaker.', 'primary_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'secondary_block_ids': ['a0d38bad-e123-4b82-b8d0-03f6724b9617'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro6 GEMINI {'inferred_title': 'Exemplo Completo de Arquitetura de Microsserviços com Spring Cloud: Gateway, Discovery, Feign e Circuit Breaker', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Cloud', 'API Gateway', 'Service Discovery (Eureka)', 'Feign Client', 'Circuit Breaker', 'Padrões de Resiliência', 'RESTful APIs'], 'summary': 'Este bundle demonstra uma arquitetura completa de microsserviços utilizando Spring Cloud, incluindo a configuração de um API Gateway, um Naming Server para descoberta de serviços e comunicação inter-serviços via Feign. Ele exemplifica a implementação de padrões de resiliência com mecanismos de fallback (circuit breaker) e um filtro de log global no gateway.', 'files': [{'name': 'roteiro6/api-gateway/src/main/java/com/engsoft2/api_gateway/ApiGatewayApplication.java', 'role': 'Inicialização do API Gateway'}, {'name': 'roteiro6/api-gateway/src/main/java/com/engsoft2/api_gateway/FallbackController.java', 'role': 'Lógica de fallback do API Gateway'}, {'name': 'roteiro6/api-gateway/src/main/java/com/engsoft2/api_gateway/LoggingFilter.java', 'role': 'Filtro de log global do API Gateway'}, {'name': 'roteiro6/api-gateway/src/test/java/com/engsoft2/api_gateway/ApiGatewayApplicationTests.java', 'role': 'Testes do API Gateway'}, {'name': 'roteiro6/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyConversion.java', 'role': 'Modelo de dados para conversão de moedas'}, {'name': 'roteiro6/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyConversionController.java', 'role': 'Controlador REST para conversão de moedas (cliente Feign)'}, {'name': 'roteiro6/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyConversionServiceApplication.java', 'role': 'Inicialização do serviço de conversão de moedas'}, {'name': 'roteiro6/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyExchangeFallback.java', 'role': 'Lógica de fallback para chamadas de câmbio'}, {'name': 'roteiro6/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyExchangeProxy.java', 'role': 'Cliente Feign para serviço de câmbio'}, {'name': 'roteiro6/currency-conversion-service/src/test/java/com/engsoft2/currency_conversion_service/CurrencyConversionServiceApplicationTests.java', 'role': 'Testes do serviço de conversão'}, {'name': 'roteiro6/currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchange.java', 'role': 'Modelo de dados para câmbio de moedas'}, {'name': 'roteiro6/currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchangeController.java', 'role': 'Controlador REST para câmbio de moedas'}, {'name': 'roteiro6/currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchangeRepository.java', 'role': 'Repositório JPA para câmbio de moedas'}, {'name': 'roteiro6/currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/CurrencyExchangeServiceApplication.java', 'role': 'Inicialização do serviço de câmbio de moedas'}, {'name': 'roteiro6/currency-exchange-service/src/main/java/com/engsoft2/currency_exchange_service/ResourceNotFoundException.java', 'role': 'Exceção personalizada para recursos não encontrados'}, {'name': 'roteiro6/currency-exchange-service/src/main/resources/data.sql', 'role': 'Script de inicialização de dados do banco'}, {'name': 'roteiro6/currency-exchange-service/src/test/java/com/engsoft2/currency_exchange_service/CurrencyExchangeServiceApplicationTests.java', 'role': 'Testes do serviço de câmbio'}, {'name': 'roteiro6/naming-server/src/main/java/com/engsoft2/naming_server/NamingServerApplication.java', 'role': 'Inicialização do Naming Server (Eureka)'}, {'name': 'roteiro6/naming-server/src/test/java/com/engsoft2/naming_server/NamingServerApplicationTests.java', 'role': 'Testes do Naming Server'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-07'], 'match_rationale': 'O código demonstra a implementação de um ecossistema de microsserviços usando Spring Cloud, incluindo o Naming Server para descoberta de serviços e um API Gateway para roteamento e resiliência.', 'primary_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'secondary_block_ids': ['a0d38bad-e123-4b82-b8d0-03f6724b9617'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro7 GEMINI {'inferred_title': 'Implementação de Sistema de Microsserviços com Spring Cloud, Gateway, Descoberta de Serviços, Circuit Breaker e Mensageria', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Boot', 'Spring Cloud Gateway', 'Eureka Server (Descoberta de Serviços)', 'Cliente Feign', 'Circuit Breaker (Resiliência)', 'Mensageria (RabbitMQ)', 'Padrão Publish/Subscribe', 'RESTful APIs'], 'summary': 'Este conjunto de código demonstra a implementação de um sistema de microserviços em Java com Spring Boot e Spring Cloud. Ele exemplifica padrões arquitetônicos como API Gateway, descoberta de serviços com Eureka, comunicação inter-serviços via Feign Client e resiliência com Circuit Breaker. Além disso, mostra a integração de mensageria assíncrona usando RabbitMQ para registrar histórico de operações.', 'files': [{'name': 'api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\ApiGatewayApplication.java', 'role': 'Ponto de entrada do Gateway'}, {'name': 'api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\FallbackController.java', 'role': 'Controller para fallback do Gateway'}, {'name': 'api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\LoggingFilter.java', 'role': 'Filtro global de requisições'}, {'name': 'api-gateway\\src\\test\\java\\com\\engsoft2\\api_gateway\\ApiGatewayApplicationTests.java', 'role': 'Testes de unidade do Gateway'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java', 'role': 'Modelo de dados de conversão'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java', 'role': 'Controller do serviço de conversão'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java', 'role': 'Ponto de entrada do serviço de conversão'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeFallback.java', 'role': 'Implementação de fallback do Feign'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java', 'role': 'Interface Feign Client para câmbio'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\HistoryDTO.java', 'role': 'DTO para mensageria de histórico'}, {'name': 'currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\RabbitMQConfig.java', 'role': 'Configuração RabbitMQ (serviço de conversão)'}, {'name': 'currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java', 'role': 'Testes de unidade do serviço de conversão'}, {'name': 'currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java', 'role': 'Entidade de câmbio'}, {'name': 'currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java', 'role': 'Controller do serviço de câmbio'}, {'name': 'currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java', 'role': 'Repositório de dados de câmbio'}, {'name': 'currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java', 'role': 'Ponto de entrada do serviço de câmbio'}, {'name': 'currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java', 'role': 'Exceção personalizada'}, {'name': 'currency-exchange-service\\src\\main\\resources\\data.sql', 'role': 'Script de dados iniciais'}, {'name': 'currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java', 'role': 'Testes de unidade do serviço de câmbio'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\HistoryDTO.java', 'role': 'DTO para histórico (serviço de histórico)'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\HistoryServiceApplication.java', 'role': 'Ponto de entrada do serviço de histórico'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\RabbitMQConfig.java', 'role': 'Configuração RabbitMQ (serviço de histórico)'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\Receiver.java', 'role': 'Consumer de mensagens RabbitMQ'}, {'name': 'history-service\\src\\test\\java\\com\\engsoft2\\historyservice\\HistoryServiceApplicationTests.java', 'role': 'Testes de unidade do serviço de histórico'}, {'name': 'naming-server\\src\\main\\java\\com\\engsoft2\\naming_server\\NamingServerApplication.java', 'role': 'Ponto de entrada do Eureka Server'}, {'name': 'naming-server\\src\\test\\java\\com\\engsoft2\\naming_server\\NamingServerApplicationTests.java', 'role': 'Testes de unidade do Eureka Server'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-07', 'bloco-10'], 'match_rationale': 'Este bundle demonstra a implementação de um API Gateway e Descoberta de Serviços com Eureka, além de Circuit Breaker para resiliência e RabbitMQ para comunicação assíncrona.', 'primary_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'secondary_block_ids': ['a0d38bad-e123-4b82-b8d0-03f6724b9617', '17b8da72-b970-4db3-b49e-7cd196945b39'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro7-history-service GEMINI {'inferred_title': 'Serviço de Histórico de Conversões com RabbitMQ', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'Spring Boot', 'RabbitMQ', 'Mensageria assíncrona', 'Data Transfer Object (DTO)', 'Fanout Exchange', 'Filas de Mensagens (Queues)', 'Binding'], 'summary': 'Este bundle implementa um microsserviço Spring Boot para registrar histórico de conversões. Ele demonstra a configuração de comunicação assíncrona usando RabbitMQ, incluindo a definição de exchanges, queues e um listener para processar mensagens.', 'files': [{'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\HistoryDTO.java', 'role': 'DTO para histórico'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\HistoryServiceApplication.java', 'role': 'Aplicação principal'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\RabbitMQConfig.java', 'role': 'Configuração RabbitMQ'}, {'name': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\Receiver.java', 'role': 'Consumidor de mensagens'}, {'name': 'history-service\\src\\test\\java\\com\\engsoft2\\historyservice\\HistoryServiceApplicationTests.java', 'role': 'Teste de contexto'}], 'suggested_block_id': 'bloco-10', 'suggested_secondary_ids': ['bloco-02'], 'match_rationale': "O código exemplifica a comunicação assíncrona entre microsserviços utilizando RabbitMQ, que é o foco principal do bloco 'Comunicacao'.", 'primary_block_id': 'bloco-10', 'secondary_block_ids': ['bloco-02'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
Engenharia-Software-2 roteiro4 GEMINI {'inferred_title': 'Sistema de Conversão de Moedas com Microsserviços, Gateway, Discovery e Resiliência', 'language': 'java', 'pedagogical_role': 'exemplo_demonstrativo', 'concepts': ['Microsserviços', 'API Gateway (Spring Cloud Gateway)', 'Service Discovery (Eureka)', 'Cliente Declarativo (Feign)', 'Padrão Circuit Breaker', 'Tolerância a Falhas', 'RESTful APIs', 'Spring Boot'], 'summary': 'Este bundle implementa um sistema de conversão de moedas utilizando uma arquitetura de microsserviços. Ele demonstra a integração de componentes essenciais como API Gateway, serviço de descoberta (Eureka) e clientes Feign para comunicação entre serviços. O código também ilustra padrões de resiliência, como Circuit Breaker e fallbacks, para lidar com falhas de serviço em ambientes distribuídos.', 'files': [{'name': 'roteiro4\\api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\ApiGatewayApplication.java', 'role': 'Aplicação Principal do API Gateway'}, {'name': 'roteiro4\\api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\FallbackController.java', 'role': 'Controlador de Fallback do Gateway'}, {'name': 'roteiro4\\api-gateway\\src\\main\\java\\com\\engsoft2\\api_gateway\\LoggingFilter.java', 'role': 'Filtro de Logging do Gateway'}, {'name': 'roteiro4\\api-gateway\\src\\test\\java\\com\\engsoft2\\api_gateway\\ApiGatewayApplicationTests.java', 'role': 'Testes de Aplicação do Gateway'}, {'name': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java', 'role': 'Modelo de Dados de Conversão de Moedas'}, {'name': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java', 'role': 'Controlador REST de Conversão de Moedas'}, {'name': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java', 'role': 'Aplicação Principal de Conversão de Moedas'}, {'name': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeFallback.java', 'role': 'Implementação de Fallback para Feign'}, {'name': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java', 'role': 'Cliente Feign para Serviço de Câmbio'}, {'name': 'roteiro4\\currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java', 'role': 'Testes de Aplicação de Conversão de Moedas'}, {'name': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java', 'role': 'Modelo de Dados de Câmbio'}, {'name': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java', 'role': 'Controlador REST de Câmbio'}, {'name': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java', 'role': 'Repositório de Dados de Câmbio'}, {'name': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java', 'role': 'Aplicação Principal do Serviço de Câmbio'}, {'name': 'roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java', 'role': 'Exceção Customizada de Recurso Não Encontrado'}, {'name': 'roteiro4\\currency-exchange-service\\src\\main\\resources\\data.sql', 'role': 'Script de Inicialização de Dados (SQL)'}, {'name': 'roteiro4\\currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java', 'role': 'Testes de Aplicação do Serviço de Câmbio'}, {'name': 'roteiro4\\naming-server\\src\\main\\java\\com\\engsoft2\\naming_server\\NamingServerApplication.java', 'role': 'Aplicação Principal do Servidor de Nomes (Eureka)'}, {'name': 'roteiro4\\naming-server\\src\\test\\java\\com\\engsoft2\\naming_server\\NamingServerApplicationTests.java', 'role': 'Testes de Aplicação do Servidor de Nomes'}], 'suggested_block_id': 'bloco-04', 'suggested_secondary_ids': ['bloco-07'], 'match_rationale': 'O código demonstra a implementação de um ecossistema de microsserviços completo com Spring Cloud, cobrindo o uso de API Gateway e Service Discovery.', 'primary_block_id': '8a2e86f0-fb4a-4487-86ec-07e74c73d88a', 'secondary_block_ids': ['a0d38bad-e123-4b82-b8d0-03f6724b9617'], 'block_match_confidence': 0.6, 'block_match_method': 'llm_only'}
18:    CODE_EXTENSIONS,
174:    if code_path.suffix.lower() not in CODE_EXTENSIONS:
181:def process_zip(builder, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
225:        safe_name_c = f"{sub_entry.id()}{code_path.suffix.lower()}"
226:        raw_target_c = builder.root_dir / "raw" / "code" / code_subdir / safe_name_c
334:        safe_name_c = f"{sub_entry.id()}{code_path.suffix.lower()}"
335:        raw_target_c = builder.root_dir / "raw" / "code" / code_subdir / safe_name_c
curso  zips membros md distintos sobrescritos conteudo perdido zips com perda
CG      14     273           47          226               88             11
ES2      8     131           24          107                6              4
MF      13      65           30           35               35              8
IA       4      15           15            0                0              0
FR       4       8            8            0                0              0
SO       1       2            2            0                0              0
tot     44     494          126          368              129             23

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'Get-Content src/builder/__init__.py; Get-Content src/builder/timeline/__init__.py; Get-Content src/builder/artifacts/__init__.py; Get-Process python* | Select-Object Id,CPU,StartTime; Get-Content src/builder/timeline/index.py -TotalCount 90'[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 442ms:[0m
Get-Content: 
Line |
   2 |  Get-Content src/builder/__init__.py; Get-Content src/builder/timeline …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Não é possível localizar o caminho 'C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator\src\builder\__init__.py' porque ele não existe.
"""Timeline-related builder subpackage."""
"""Artifact-generation subpackage for builder modules."""

   Id   CPU StartTime
   --   --- ---------
 1224  0,02 11/09/2026 01:06:47
 8560  1,92 11/09/2026 01:00:56
15272       
15480 11,72 11/09/2026 01:05:56
20684 52,06 11/09/2026 01:11:49
22016  0,03 11/09/2026 01:05:56
23416  0,00 11/09/2026 01:06:54


import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.builder.vision.card_evidence import extract_card_evidence
from src.builder.timeline.signals import extract_timeline_session_signals
from src.builder.timeline.classifier import classify_block, row_kind_from_text
from src.builder.timeline.kinds import BlockKind
from src.builder.timeline.curation import apply_block_curation, load_boundary_dates
from src.builder.timeline.unit_matcher import assign_units_by_work_milestones, assign_units_positional
from src.builder.text.normalize import (
    normalize_match_text as _normalize_match_text,
    signal_token_set as _signal_token_set,
    stem6 as _stem6,
)
from src.builder.routing.thresholds import margin_confidence, T
from src.builder.routing.file_map import UNIT_GENERIC_TOKENS
from src.builder.extraction.teaching_plan import _normalize_unit_slug
from src.builder.text.stopwords import (
    TIMELINE_GENERIC_TOKENS as _TIMELINE_GENERIC_TOKENS,
    TIMELINE_UNIT_NEUTRAL_TOKENS as _TIMELINE_UNIT_NEUTRAL_TOKENS,
)
from src.utils.helpers import slugify, ATIVIDADE_KIND_MAP, norm_ascii_lower, collapse_ws as _collapse_ws
from src.builder.timeline.block_identity import (
    BlockIdentityError,
    load_identity_ledger,
    reattach_block_uuids,
    save_identity_ledger,
    scan_existing_block_refs,
)


TIMELINE_INDEX_VERSION = 4


def ensure_block_kind(block: dict) -> dict:
    """Lazy backfill: garante `kind` no bloco. Idempotente."""
    if not isinstance(block, dict):
        return block
    if not block.get("kind"):
        block["kind"] = classify_block(block).value
    # transiente do guard cue-x-conteudo (F2/F3): nunca persiste no JSON
    block.pop("_plan_phrases", None)
    return block


def plan_phrases_para_classificacao(unit_index) -> tuple:
    """Frases de CONTEUDO do plano (titulos + topicos das unidades), normalizadas como o
    classificador normaliza o texto do bloco. Insumo do guard cue-x-conteudo (F2/F3):
    carimbadas em `block["_plan_phrases"]` antes do finalize e removidas depois."""
    from src.builder.timeline.classifier import _norm as _cls_norm
    frases = []
    for u in unit_index or []:
        brutos = [u.get("title") if isinstance(u, dict) else ""]
        for t in (u.get("topics") or []) if isinstance(u, dict) else []:
            brutos.append(t[0] if isinstance(t, (tuple, list)) and t else t)
        for bruto in brutos:
            fr = _cls_norm(str(bruto or ""))
            if len(fr) >= 6:
                frases.append(fr)
    return tuple(dict.fromkeys(frases))


def finalize_block(block: dict) -> dict:
    """Garante `kind` e limpa unidade de blocos nao-aula.

    Provas/feriados/revisoes/etc nao tem unidade pedagogica. Override manual de
    unidade (`block_manual_unit_slug`) sempre preservado. Idempotente.
    """
    if not isinstance(block, dict):
        return block
    ensure_block_kind(block)
    if block.get("kind") != BlockKind.CLASS.value and not block.get("block_manual_unit_slug"):
        block["unit_slug"] = ""
        block["unit_confidence"] = 0.0
    return block


def _backfill_timeline_index(timeline_index: dict) -> dict:
    """Lazy upgrade v3->v4: bump version, popula `kind` em cada bloco. In-place."""
    if not isinstance(timeline_index, dict):
        return timeline_index
    for block in timeline_index.get("blocks") or []:
        finalize_block(block)


[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
Outra premissa precisa correção: **código avulso tem `.md` e o leitor o entrega ao scorer**; “entra vazio” vale para os zips sem `.md` próprio. Também encontrei resumos Gemini de `invariantes` e `terminacao` descrevendo tipos indutivos, compatíveis com a colisão de extração já registrada.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
import json,zipfile
for nm,ids in [('Metodos-Formais',['invariantes','terminacao']),('Engenharia-Software-2',['roteiro7-history-service'])]:
 p=Path('..')/(nm+'-Tutor');m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))['entries']
 for e in m:
  if e['id'] in ids:
   print('\\nENTRY',nm,e['id'])
   for ef in e.get('extracted_files',[])[:5]:
    f=p/ef['base_markdown'];print('FILE',f)
    for i,l in enumerate(f.read_text(encoding='utf-8').splitlines(),1):
     if nm=='Metodos-Formais' and i<=48 or any(w.lower() in l.lower() for w in ['rabbit','import','package','Linguagem','"'```'"']): print(f'{i}: {l}')
   if nm=='Metodos-Formais':
    z=zipfile.ZipFile(p/e['raw_target']);n=next(n for n in z.namelist() if n.endswith('ex1.dfy'));print('RAW_ZIP',n,z.read(n).decode('utf-8',errors='replace')[:900])
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 477ms:[0m

ENTRY Metodos-Formais invariantes
FILE ..\Metodos-Formais-Tutor\code\professor\ex1.md
1: ---
2: entry_id: "ex1"
3: title: "tiposindutivos\\ex1.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex1.dfy"
8: ---
9: # tiposindutivos\ex1.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Tiposindutivos
13: 
14: ```dafny
15: //tipos indutivos via datatype
16: //tipo de dados imutável
17: 
18: datatype Cor = Azul | Amarelo | Vermelho | Verde
19: 
20: predicate Gremista(c:Cor)
21: {
22:   c.Azul?
23: }
24: 
25: method Main()
26: {
27:   var c1 := Azul;
28:   var c2 := Cor.Vermelho;
29:   assert Gremista(c1);
30:   assert !Gremista(c2);
31: }
32: 
33: ```
FILE ..\Metodos-Formais-Tutor\code\professor\ex2.md
1: ---
2: entry_id: "ex2"
3: title: "tiposindutivos\\ex2.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex2.dfy"
8: ---
9: # tiposindutivos\ex2.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Tiposindutivos
13: 
14: ```dafny
15: datatype Lista<T> = Vazia | Cons(cabeca:T, cauda:Lista<T>)
16: 
17: function Tamanho<T>(lista:Lista<T>):nat
18: {
19:   //expressão condicional
20:   if lista == Vazia
21:   then 0
22:   else 1 + Tamanho(lista.cauda)
23: }
24: 
25: function Tamanhov2<T>(lista:Lista<T>):nat
26: {
27:   //casamento de padrões
28:   match lista
29:   case Vazia => 0
30:   case Cons(cabeca,cauda) => 1 + Tamanhov2(cauda)
31: }
32: 
33: function Concatenar<T>(x:Lista<T>, y:Lista<T>):Lista<T>
34:   ensures Tamanhov2(Concatenar(x,y)) == Tamanhov2(x) + Tamanhov2(y)
35: {
36:   match x
37:   case Vazia => y
38:   case Cons(cabeca,cauda) => Cons(cabeca, Concatenar(cauda,y))
39: }
40: 
41: lemma ConcatenarAssociatividade<T>(x:Lista<T>, y:Lista<T>, z:Lista<T>)
42:   ensures Concatenar(Concatenar(x,y),z) == Concatenar(x,Concatenar(y,z))
43: {}
44: 
45: method Main()
46: {
47:   var lista1:Lista<int> := Vazia;
48:   var lista2 := Cons(1,Vazia);
57: ```
FILE ..\Metodos-Formais-Tutor\code\professor\ex3.md
1: ---
2: entry_id: "ex3"
3: title: "tiposindutivos\\ex3.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex3.dfy"
8: ---
9: # tiposindutivos\ex3.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Tiposindutivos
13: 
14: ```dafny
15: datatype ArvBin<T> = Vazia | Nodo(esq:ArvBin<T>, x:T, dir:ArvBin<T>)
16: 
17: function tamanho<T>(a:ArvBin<T>):nat
18: {
19:     match a
20:     case Vazia => 0
21:     case Nodo(e,x,d) => 1 + tamanho(e) + tamanho(d)
22: }
23: 
24: function tamanhoEsquerda<T>(a:ArvBin<T>):nat
25: {
26:     match a
27:     case Vazia => 0
28:     case Nodo(e,_,_) => 1 + tamanhoEsquerda(e)
29: }
30: 
31: method Main()
32: {
33:     var arv1: ArvBin<nat> := Vazia;
34:     assert tamanho(arv1) == 0;
35:     var arv2 := Nodo(Nodo(Vazia,2,Vazia),1,Vazia);
36:     assert tamanho(arv2) == 2;
37: }
38: 
39: ```
FILE ..\Metodos-Formais-Tutor\code\professor\ex4.md
1: ---
2: entry_id: "ex4"
3: title: "terminacao\\ex4.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex4.dfy"
8: ---
9: # terminacao\ex4.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Terminacao
13: 
14: ```dafny
15: method Collatz(x: nat)
16:   decreases * //desabilita a verificação da terminação
17: {
18:   var n := x;
19:   while 1 < n
20:     decreases * //desabilita a verificação da terminação
21:   {
22:     n := if n % 2 == 0 then n / 2 else n * 3 + 1;
23:   }
24: }
25: 
26: ```
RAW_ZIP invariantes/ex1.dfy method Mult(x:nat, y:nat) returns (a:nat)
  ensures a == x * y
{
  var m:nat := x;
  var n:nat := y;
  a := 0;
  while m > 0
    invariant a + m * n == x * y
  {
    a := a + n;
    m := m - 1;
  }
}


ENTRY Metodos-Formais terminacao
FILE ..\Metodos-Formais-Tutor\code\professor\ex1.md
1: ---
2: entry_id: "ex1"
3: title: "tiposindutivos\\ex1.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex1.dfy"
8: ---
9: # tiposindutivos\ex1.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Tiposindutivos
13: 
14: ```dafny
15: //tipos indutivos via datatype
16: //tipo de dados imutável
17: 
18: datatype Cor = Azul | Amarelo | Vermelho | Verde
19: 
20: predicate Gremista(c:Cor)
21: {
22:   c.Azul?
23: }
24: 
25: method Main()
26: {
27:   var c1 := Azul;
28:   var c2 := Cor.Vermelho;
29:   assert Gremista(c1);
30:   assert !Gremista(c2);
31: }
32: 
33: ```
FILE ..\Metodos-Formais-Tutor\code\professor\ex2.md
1: ---
2: entry_id: "ex2"
3: title: "tiposindutivos\\ex2.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex2.dfy"
8: ---
9: # tiposindutivos\ex2.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Tiposindutivos
13: 
14: ```dafny
15: datatype Lista<T> = Vazia | Cons(cabeca:T, cauda:Lista<T>)
16: 
17: function Tamanho<T>(lista:Lista<T>):nat
18: {
19:   //expressão condicional
20:   if lista == Vazia
21:   then 0
22:   else 1 + Tamanho(lista.cauda)
23: }
24: 
25: function Tamanhov2<T>(lista:Lista<T>):nat
26: {
27:   //casamento de padrões
28:   match lista
29:   case Vazia => 0
30:   case Cons(cabeca,cauda) => 1 + Tamanhov2(cauda)
31: }
32: 
33: function Concatenar<T>(x:Lista<T>, y:Lista<T>):Lista<T>
34:   ensures Tamanhov2(Concatenar(x,y)) == Tamanhov2(x) + Tamanhov2(y)
35: {
36:   match x
37:   case Vazia => y
38:   case Cons(cabeca,cauda) => Cons(cabeca, Concatenar(cauda,y))
39: }
40: 
41: lemma ConcatenarAssociatividade<T>(x:Lista<T>, y:Lista<T>, z:Lista<T>)
42:   ensures Concatenar(Concatenar(x,y),z) == Concatenar(x,Concatenar(y,z))
43: {}
44: 
45: method Main()
46: {
47:   var lista1:Lista<int> := Vazia;
48:   var lista2 := Cons(1,Vazia);
57: ```
FILE ..\Metodos-Formais-Tutor\code\professor\ex3.md
1: ---
2: entry_id: "ex3"
3: title: "tiposindutivos\\ex3.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex3.dfy"
8: ---
9: # tiposindutivos\ex3.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Tiposindutivos
13: 
14: ```dafny
15: datatype ArvBin<T> = Vazia | Nodo(esq:ArvBin<T>, x:T, dir:ArvBin<T>)
16: 
17: function tamanho<T>(a:ArvBin<T>):nat
18: {
19:     match a
20:     case Vazia => 0
21:     case Nodo(e,x,d) => 1 + tamanho(e) + tamanho(d)
22: }
23: 
24: function tamanhoEsquerda<T>(a:ArvBin<T>):nat
25: {
26:     match a
27:     case Vazia => 0
28:     case Nodo(e,_,_) => 1 + tamanhoEsquerda(e)
29: }
30: 
31: method Main()
32: {
33:     var arv1: ArvBin<nat> := Vazia;
34:     assert tamanho(arv1) == 0;
35:     var arv2 := Nodo(Nodo(Vazia,2,Vazia),1,Vazia);
36:     assert tamanho(arv2) == 2;
37: }
38: 
39: ```
FILE ..\Metodos-Formais-Tutor\code\professor\ex4.md
1: ---
2: entry_id: "ex4"
3: title: "terminacao\\ex4.dfy"
4: language: "dafny"
5: category: "codigo-professor"
6: unit: ""
7: source: "raw/code/professor/ex4.dfy"
8: ---
9: # terminacao\ex4.dfy
10: 
11: > **Linguagem:** dafny
12: > Extraído de: Terminacao
13: 
14: ```dafny
15: method Collatz(x: nat)
16:   decreases * //desabilita a verificação da terminação
17: {
18:   var n := x;
19:   while 1 < n
20:     decreases * //desabilita a verificação da terminação
21:   {
22:     n := if n % 2 == 0 then n / 2 else n * 3 + 1;
23:   }
24: }
25: 
26: ```
RAW_ZIP terminacao/ex1.dfy function Somar(m:nat, n:nat):nat
  decreases m
  ensures Somar(m,n) == m+n
{
  if (m == 0)
  then n
  else Somar(m-1,n) + 1
}


ENTRY Engenharia-Software-2 roteiro7-history-service
FILE ..\Engenharia-Software-2-Tutor\code\professor\historydto.md
11: > **Linguagem:** java
14: ```java
15: package com.engsoft2.historyservice;
44: ```
FILE ..\Engenharia-Software-2-Tutor\code\professor\historyserviceapplication.md
11: > **Linguagem:** java
14: ```java
15: package com.engsoft2.historyservice;
17: import org.springframework.boot.SpringApplication;
18: import org.springframework.boot.autoconfigure.SpringBootApplication;
29: ```
FILE ..\Engenharia-Software-2-Tutor\code\professor\rabbitmqconfig.md
2: entry_id: "rabbitmqconfig"
3: title: "history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\RabbitMQConfig.java"
7: source: "raw/code/professor/rabbitmqconfig.java"
9: # history-service\src\main\java\com\engsoft2\historyservice\RabbitMQConfig.java
11: > **Linguagem:** java
14: ```java
15: package com.engsoft2.historyservice;
17: import org.springframework.amqp.core.Binding;
18: import org.springframework.amqp.core.BindingBuilder;
19: import org.springframework.amqp.core.FanoutExchange;
20: import org.springframework.amqp.core.Queue;
21: import org.springframework.amqp.rabbit.connection.ConnectionFactory;
22: import org.springframework.amqp.rabbit.core.RabbitTemplate;
23: import org.springframework.amqp.support.converter.JacksonJsonMessageConverter;
24: import org.springframework.amqp.support.converter.MessageConverter;
25: import org.springframework.context.annotation.Bean;
26: import org.springframework.context.annotation.Configuration;
29: public class RabbitMQConfig {
54:     public RabbitTemplate rabbitTemplate(ConnectionFactory factory, MessageConverter messageConverter) {
55:         final RabbitTemplate rabbitTemplate = new RabbitTemplate(factory);
56:         rabbitTemplate.setMessageConverter(messageConverter);
57:         return rabbitTemplate;
61: ```
FILE ..\Engenharia-Software-2-Tutor\code\professor\receiver.md
11: > **Linguagem:** java
14: ```java
15: package com.engsoft2.historyservice;
17: import org.apache.logging.log4j.LogManager;
18: import org.apache.logging.log4j.Logger;
19: import org.springframework.amqp.rabbit.annotation.RabbitListener;
20: import org.springframework.stereotype.Component;
27:     @RabbitListener(queues = QUEUENAME)
33: ```
FILE ..\Engenharia-Software-2-Tutor\code\professor\historyserviceapplicationtests.md
11: > **Linguagem:** java
14: ```java
15: package com.engsoft2.historyservice;
17: import org.junit.jupiter.api.Test;
18: import org.springframework.boot.test.context.SpringBootTest;
29: ```

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command "rg -n -A 24 'def _matches_normalized_phrase' src/builder/timeline/index.py; "'$env:PYTHONIOENCODING='"'utf-8'; @'
import ast,re
from pathlib import Path
from collections import Counter
p=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py');tree=ast.parse(p.read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico'] or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets)];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'))
import json
for name,ids in [('Engenharia-Software-2',['roteiro7-history-service','roteiro1']),('Metodos-Formais',['arvores','intro','listas','invariantes'])]:
 root=Path('..')/(name+'-Tutor');es=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 for e in es:
  if e['id'] in ids:print(name,e['id'],_sintetico(e,root)['summary'])
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 291ms:[0m
141:def _matches_normalized_phrase(signal_text: str, phrase: str, stem_fallback: bool = False) -> bool:
142-    """A1 (2026-08-31, medido em 3 tentativas): o fallback por RADICAL (stem6, mesma
143-    convencao do motor de bloco) e OPT-IN. Ligado globalmente derrubou subunidade
144-    87->83 e bloco 199->198; ligado so aqui com stem_fallback=True na rota de
145-    TOPICO do mapeador de UNIDADE fecha os 3 forks do SO ("chamadas de sistema" ~
146-    "chamada de sistema fork()") sem tocar a subunidade (exata)."""
147-    normalized_signal = _normalize_match_text(signal_text)
148-    normalized_phrase = _normalize_match_text(phrase)
149-    if not normalized_signal or not normalized_phrase:
150-        return False
151-    if " " not in normalized_phrase:
152-        return normalized_phrase in _signal_token_set(normalized_signal)
153-    if normalized_phrase in normalized_signal:
154-        return True
155-    if not stem_fallback:
156-        return False
157-    frase_toks = [t for t in normalized_phrase.split() if len(t) >= 4]
158-    if len(frase_toks) < 2:
159-        return False
160-    sinal_stems = {_stem6(t) for t in _signal_token_set(normalized_signal)}
161-    return all(_stem6(t) in sinal_stems for t in frase_toks)
162-
163-
164-@dataclass
165-class TopicMatchResult:
Engenharia-Software-2 roteiro1 {'inferred_title': 'Código Currency Conversion Currency Conversion Controller Currency Conversion Service Application Currency Exchange Proxy Currency Conversion Service Application Tests Currency Exchange Currency Excha', 'summary': 'roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversion.java roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionController.java roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplication.java roteiro4\\currency-conversion-service\\src\\main\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyExchangeProxy.java roteiro4\\currency-conversion-service\\src\\test\\java\\com\\engsoft2\\currency_conversion_service\\CurrencyConversionServiceApplicationTests.java roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchange.java roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeController.java roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeRepository.java roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplication.java roteiro4\\currency-exchange-service\\src\\main\\java\\com\\engsoft2\\currency_exchange_service\\ResourceNotFoundException.java roteiro4\\currency-exchange-service\\src\\main\\resources\\data.sql roteiro4\\currency-exchange-service\\src\\test\\java\\com\\engsoft2\\currency_exchange_service\\CurrencyExchangeServiceApplicationTests.java', 'concepts': ['currency', 'conversion', 'exchange', 'environment', 'multiple', 'decimal', 'springframework', 'service', 'quantity', 'boot', 'application', 'spring', 'package', 'engsoft2', 'repository', 'total', 'calculated', 'amount', 'path', 'variable', 'test', 'long', 'bind', 'annotation', 'controller', 'proxy', 'feign', 'logger', 'mapping', 'value'], 'language': 'java'}
Engenharia-Software-2 roteiro7-history-service {'inferred_title': 'Código - serviço history History DTO History Service Application Rabbit MQConfig Receiver History Service Application Tests', 'summary': 'history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\HistoryDTO.java history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\HistoryServiceApplication.java history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\RabbitMQConfig.java history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\Receiver.java history-service\\src\\test\\java\\com\\engsoft2\\historyservice\\HistoryServiceApplicationTests.java', 'concepts': ['springframework', 'rabbit', 'converter', 'history', 'amqp', 'message', 'template', 'boot', 'application', 'spring', 'bean', 'package', 'engsoft2', 'historyservice', 'core', 'binding', 'fanout', 'exchange', 'queue', 'logger', 'test', 'factory', 'context', 'final', 'queuename', 'service', 'connection', 'json', 'annotation', 'conversions'], 'language': 'java'}
Metodos-Formais arvores {'inferred_title': 'Exemplos: provas sobre arvores arvores', 'summary': 'arvores', 'concepts': ['espelho', 'nodo', 'vazia', 'simp', 'have', 'only', 'also', 'arv1', 'arv2', 'finally', 'show', 'assume', 'theory', 'arvores', 'imports', 'datatype', 'primrec', 'rightarrow', 'where', 'theorem', 'proof', 'induct', 'next'], 'language': 'isabelle'}
Metodos-Formais intro {'inferred_title': 'Exemplos - introducao intro', 'summary': 'intro definição indutiva do tipo dos naturais *) verificando termos do tipo Nat*) regra de indução para provas nos naturais, criada pelo sistema *) uma forma sintática mais elegante da regra de indução *) adição *) nat é o tipo indutivo dos naturais definidos pelo Isabelle *) verificando termos do tipo nat *)', 'concepts': ['term', 'value', 'tipo', 'induct', 'naturais', 'apply', 'verificando', 'termos', 'regra', 'indução', 'pelo', 'statement', 'rightarrow', 'simp', 'theory', 'intro', 'imports', 'definição', 'indutiva', 'datatype', 'para', 'provas', 'criada', 'sistema', 'forma', 'sintática', 'mais', 'elegante', 'adição', 'primrec'], 'language': 'isabelle'}
Metodos-Formais listas {'inferred_title': 'Exemplos: provas sobre listas listas', 'summary': 'listas', 'concepts': ['list', 'simp', 'have', 'only', 'cat2', 'forall', 'show', 'rule', 'also', 'cat1', 'proof', 'rightarrow', 'finally', 'theory', 'listas', 'imports', 'primrec', 'where', 'theorem', 'assoc', 'induction', 'next', 'assume'], 'language': 'isabelle'}
Metodos-Formais invariantes {'inferred_title': 'Exemplos (invariantes de laco) ex1 ex2 ex3 ex4', 'summary': 'tiposindutivos\\ex1.dfy tipos indutivos via datatype tipo de dados imutável tiposindutivos\\ex2.dfy expressão condicional casamento de padrões tiposindutivos\\ex3.dfy terminacao\\ex4.dfy', 'concepts': ['lista', 'vazia', 'tamanho', 'tamanhov2', 'concatenar', 'assert', 'case', 'cons', 'cauda', 'function', 'nodo', 'datatype', 'method', 'cabeca', 'match', 'azul', 'gremista', 'lista2', 'lista3', 'vermelho', 'ensures', 'lista1', 'lista4', 'esquerda', 'arv1', 'arv2', 'decreases', 'desabilita', 'verificação', 'terminação'], 'language': 'dafny'}

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries']
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

print('loaded',flush=True)
for sig in ['SO','MF','ES2','IA','TCC']:
 rs={}
 for mode in ['sem','determ','com']:
  r=evaluate(sig,mode);rs[mode]=r;print(sig,mode,r[:2],flush=True)
 if sig in ['MF','ES2']:
  for k in rs['sem'][2]:
   if len({rs[m][3][k] for m in rs})>1:
    print('DELTA',sig,k,[(m,rs[m][3][k],rs[m][2][k]) for m in rs],flush=True)
 if sig=='SO':
  old=evaluate(sig,'com',False);print('OLD',old[:2],flush=True)
  for k in old[2]:
   if old[3][k]"'!=rs['"'com'][3][k]:print('SO_CHANGE',k,old[3][k],old[2][k],rs['com'][3][k],rs['com'][2][k],flush=True)

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[31m exited 1 in 162419ms:[0m
MF sem (52, 38)
ERRORS [('archive-of-formal-proofs-355fb8', 'abordagens-para-verificacao-formal'), ('exemplos', 'exemplos-de-aplicacoes'), ('exercicios-conjuntos', 'logica-de-hoare'), ('introducao-zip', ''), ('tiposindutivos', ''), ('exemplos-zip', '')]
MF determ (50, 36)
ERRORS [('archive-of-formal-proofs-355fb8', 'abordagens-para-verificacao-formal'), ('arvores', 'exemplos-de-aplicacoes'), ('exemplos', 'exemplos-de-aplicacoes'), ('intro', 'exemplos-de-aplicacoes'), ('listas', 'exemplos-de-aplicacoes'), ('introducao-zip', ''), ('terminacao', ''), ('tiposindutivos', 'verificacao-de-programas')]
MF com (51, 34)
ERRORS [('archive-of-formal-proofs-355fb8', 'abordagens-para-verificacao-formal'), ('exemplos', 'exemplos-de-aplicacoes'), ('invariantes', 'verificacao-de-programas'), ('terminacao', 'verificacao-de-programas'), ('tiposindutivos', 'verificacao-de-programas'), ('exemplos-zip', ''), ('classes-parte2', 'correcao-parcial-e-total')]
SO sem (8, 7)
SO determ (8, 7)
SO com (8, 7)
IA sem (36, 36)
IA determ (36, 36)
IA com (38, 38)
ES2 sem (16, 14)
ERRORS [('roteiro1', ''), ('kubernetes', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos'), ('microsservicos2', 'orientada-a-microsservicos'), ('microsservicos3', 'estilos-e-padroes-arquiteturais'), ('roteiro3-gateway', 'cliente-servidor'), ('roteiro2', ''), ('roteiro3', ''), ('roteiro4', 'gerenciamento-da-configuracao'), ('roteiro5', 'gerenciamento-da-configuracao'), ('roteiro6', 'gerenciamento-da-configuracao'), ('roteiro7', 'gerenciamento-da-configuracao'), ('roteiro7-history-service', 'gerenciamento-da-configuracao')]
ES2 determ (20, 18)
ERRORS [('kubernetes', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos'), ('microsservicos2', 'orientada-a-microsservicos'), ('microsservicos3', 'estilos-e-padroes-arquiteturais'), ('roteiro4', 'gerenciamento-da-configuracao'), ('roteiro5', 'gerenciamento-da-configuracao'), ('roteiro6', 'gerenciamento-da-configuracao'), ('roteiro7', 'gerenciamento-da-configuracao'), ('roteiro7-history-service', 'gerenciamento-da-configuracao')]
ES2 com (21, 18)
ERRORS [('roteiro1', 'orientada-a-microsservicos'), ('kubernetes', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos'), ('microsservicos2', 'orientada-a-microsservicos'), ('microsservicos3', 'estilos-e-padroes-arquiteturais'), ('roteiro3-gateway', 'orientada-a-microsservicos'), ('roteiro2', 'orientada-a-microsservicos'), ('roteiro3', 'orientada-a-microsservicos')]
Traceback (most recent call last):
  File "<stdin>", line 69, in <module>
  File "<stdin>", line 48, in evaluate
  File "<stdin>", line 44, in load
  File "C:\Users\Humberto\AppData\Local\Programs\Python\Python311\Lib\pathlib.py", line 1058, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Humberto\AppData\Local\Programs\Python\Python311\Lib\pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '..\\TCC-Tutor\\code_curation.json'

[31m exited 1 in 17076ms:[0m
loaded
SO sem (8, 7)
SO determ (8, 7)
SO com (8, 7)
OLD (8, 8)
SO_CHANGE definicao-e-historico chamadas-de-sistema False evolucao-historica True
SO_CHANGE 1203-processos chamadas-de-sistema True servicos-dos-sistemas-operacionais True
SO_CHANGE exemplo-criacao-de-processos-no-unix-linux-filho chamadas-de-sistema True estudo-de-casos False
SO_CHANGE exemplo-criacao-de-processos-no-unix-linux-teste01 chamadas-de-sistema True estudo-de-casos False
SO_CHANGE exemplo-criacao-de-processos-no-unix-linux-teste02 chamadas-de-sistema True estudo-de-casos False
SO_CHANGE exemplo-criacao-de-processos-no-unix-linux-teste03 chamadas-de-sistema True estudo-de-casos False
SO_CHANGE 1903-estruturas-de-controle escalonamento False conceitos-basicos True
SO_CHANGE 2603-algoritmos-de-escalonamento escalonamento False algoritmos-de-escalonamento True
SO_CHANGE 3103-threads escalonamento False conceitos-basicos True
SO_CHANGE exercicios  False algoritmos-de-escalonamento True
SO_CHANGE exemplo-threads-em-c-exemplo1  False estudo-de-casos False
SO_CHANGE exemplo-threads-em-c-exemplo2 escalonamento False estudo-de-casos False
SO_CHANGE exemplo-threads-em-c-exemplo3 conceitos-basicos True estudo-de-casos False
MF sem (52, 38)
MF determ (50, 36)
MF com (51, 34)
DELTA MF arvores [('sem', 'provadores-de-teoremas', True), ('determ', 'exemplos-de-aplicacoes', False), ('com', 'provadores-de-teoremas', True)]
DELTA MF intro [('sem', 'especificacao-de-conjuntos-indutivos', True), ('determ', 'exemplos-de-aplicacoes', False), ('com', 'especificacao-de-funcoes-recursivas', True)]
DELTA MF listas [('sem', 'provadores-de-teoremas', True), ('determ', 'exemplos-de-aplicacoes', False), ('com', 'provadores-de-teoremas', True)]
DELTA MF exercicios-conjuntos [('sem', 'logica-de-hoare', False), ('determ', 'verificacao-de-programas', True), ('com', 'invariante-e-variante-de-laco', True)]
DELTA MF hoare [('sem', 'logica-de-hoare', True), ('determ', 'logica-de-hoare', True), ('com', 'verificacao-de-programas', True)]
DELTA MF introducao-zip [('sem', '', False), ('determ', '', False), ('com', 'verificacao-de-programas', True)]
DELTA MF invariantes [('sem', 'invariante-e-variante-de-laco', True), ('determ', 'invariante-e-variante-de-laco', True), ('com', 'verificacao-de-programas', False)]
DELTA MF terminacao [('sem', 'correcao-parcial-e-total', True), ('determ', '', False), ('com', 'verificacao-de-programas', False)]
DELTA MF tiposindutivos [('sem', '', False), ('determ', 'verificacao-de-programas', False), ('com', 'verificacao-de-programas', False)]
DELTA MF exemplos-zip [('sem', '', False), ('determ', 'softwares-de-suporte-a-verificacao-formal-de-modelos', True), ('com', '', False)]
DELTA MF classes-parte2 [('sem', 'verificacao-de-programas', True), ('determ', 'verificacao-de-programas', True), ('com', 'correcao-parcial-e-total', False)]
ES2 sem (16, 14)
ES2 determ (20, 18)
ES2 com (21, 18)
DELTA ES2 roteiro1-introducao [('sem', 'estudo-de-caso-arquitetura-orientada-a-microsservicos', True), ('determ', 'estudo-de-caso-arquitetura-orientada-a-microsservicos', True), ('com', 'orientada-a-microsservicos', True)]
DELTA ES2 roteiro1 [('sem', '', False), ('determ', 'estudo-de-caso-arquitetura-orientada-a-microsservicos', True), ('com', 'orientada-a-microsservicos', False)]
DELTA ES2 roteiro3-gateway [('sem', 'cliente-servidor', False), ('determ', 'estudo-de-caso-arquitetura-orientada-a-microsservicos', True), ('com', 'orientada-a-microsservicos', False)]
DELTA ES2 roteiro2 [('sem', '', False), ('determ', 'estudo-de-caso-arquitetura-orientada-a-microsservicos', True), ('com', 'orientada-a-microsservicos', False)]
DELTA ES2 roteiro3 [('sem', '', False), ('determ', 'estudo-de-caso-arquitetura-orientada-a-microsservicos', True), ('com', 'orientada-a-microsservicos', False)]
DELTA ES2 roteiro4 [('sem', 'gerenciamento-da-configuracao', False), ('determ', 'gerenciamento-da-configuracao', False), ('com', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos', True)]
DELTA ES2 roteiro5 [('sem', 'gerenciamento-da-configuracao', False), ('determ', 'gerenciamento-da-configuracao', False), ('com', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos', True)]
DELTA ES2 roteiro6 [('sem', 'gerenciamento-da-configuracao', False), ('determ', 'gerenciamento-da-configuracao', False), ('com', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos', True)]
DELTA ES2 roteiro7 [('sem', 'gerenciamento-da-configuracao', False), ('determ', 'gerenciamento-da-configuracao', False), ('com', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos', True)]
DELTA ES2 roteiro7-history-service [('sem', 'gerenciamento-da-configuracao', False), ('determ', 'gerenciamento-da-configuracao', False), ('com', 'estudo-de-caso-integracao-e-implantacao-de-microsservicos', True)]
IA sem (36, 36)
IA determ (36, 36)
IA com (38, 38)
Traceback (most recent call last):
  File "<stdin>", line 75, in <module>
  File "<stdin>", line 52, in evaluate
  File "<stdin>", line 48, in load
  File "C:\Users\Humberto\AppData\Local\Programs\Python\Python311\Lib\pathlib.py", line 1058, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Humberto\AppData\Local\Programs\Python\Python311\Lib\pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '..\\TCC-Tutor\\code_curation.json'

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
Passo 2 de 4 feito: o ES2 também esconde trocas. **Os quatro ganhos do determinístico são diferentes dos cinco ganhos do Gemini**; não falta apenas um roteiro. No MF, a queda de um ponto é saldo de três perdas e dois ganhos. Vou medir intervenções isoladas no scorer.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

def no_study(tax):
 for u in tax['units']:
  for t in u['topics']:
   if t['slug']=='estudo-de-casos':t['aliases']=[a for a in t['aliases'] if re.match(r'"'^'"\\d',a)]
def ownmd(e,root):
 return {} if getmd(root,e) else _sintetico(e,root)
def restored(sig):
 vocab=json.loads((Path('..')/names[sig]/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
 def change(tax):
  for u in tax['units']:
   for t in u['topics']:
    key=f\"{t.get('code','')} {t['label']}\".strip()
    for alias in vocab['_raw'].get(key,[]):
     if alias in ['Rede Perceptron','MLP','Kubernetes']:
      t['aliases'].append(alias)
 return change
def identifiers(sig):
 _,_,tax,_,_=load(sig)
 als={a for u in tax['units'] for t in u['topics'] for a in t.get('aliases',[]) if len(a)>=4}
 def synth(e,root):
  r=_sintetico(e,root)
  raw=' '.join(md for _,md in _bundle_md(e,root))
  words=set(re.findall(r'[A-Za-z][A-Za-z0-9_]*',raw))
  # Counterfactual: preserve vocabulary phrases present in raw identifiers, CamelCase boundaries.
  hits=[a for a in als if re.search(r'[A-Za-z]',a) and any(re.search(r'(?<"'![a-z])'"'+re.escape(a.replace(' ',''))+r'(?=[A-Z_0-9]|"'$)'"',w) for w in words)]
  r['summary']['concepts']+=sorted(hits)
  return r
def result(label,sig,**kwargs):
 b=evaluate(sig,'determ');r=evaluate(sig,'determ',**kwargs)
 print(label,sig,b[:2],'->',r[:2], 'gain',[k for k in b[2] if not b[2][k] and r[2][k]],'loss',[k for k in b[2] if b[2][k] and not r[2][k]],flush=True)
result('REMOVE_STUDY_ALIASES','SO',taxmod=no_study)
result('RESTORE_REJECTED','IA',taxmod=restored('IA'))
result('RESTORE_REJECTED','ES2',taxmod=restored('ES2'))
for sig in names:result('SKIP_DUPLICATE_MD',sig,synth=ownmd)
result('IDENTIFIER_ALIASES','ES2',synth=identifiers('ES2'))
for sig,ids in [('SO',['exemplo-criacao-de-processos-no-unix-linux-filho','exemplo-threads-em-c-exemplo1']),('MF',['arvores','invariantes','classes-parte2']),('ES2',['roteiro7-history-service','roteiro4'])]:
 for mode in ['sem','determ','com']:
  r=evaluate(sig,mode);by={e['id']:e for e in r[6]}
  for k in ids:
   e=by[k];ss=signals(e,r[5][k]);rank=sorted([(score(ss,t),t['topic_slug']) for t in topics(r[7]) if t['unit_slug']==e['computed_unit_slug']],reverse=True)
   print('SCORE',sig,k,mode,rank[:3],flush=True)

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 32360ms:[0m
REMOVE_STUDY_ALIASES SO (8, 7) -> (15, 14) gain ['exemplo-criacao-de-processos-no-unix-linux-filho', 'exemplo-criacao-de-processos-no-unix-linux-teste01', 'exemplo-criacao-de-processos-no-unix-linux-teste02', 'exemplo-criacao-de-processos-no-unix-linux-teste03', 'exemplo-threads-em-c-exemplo1', 'exemplo-threads-em-c-exemplo2', 'exemplo-threads-em-c-exemplo3'] loss []
RESTORE_REJECTED IA (36, 36) -> (37, 37) gain ['rede-perceptron-or-em-python'] loss []
RESTORE_REJECTED ES2 (20, 18) -> (21, 19) gain ['kubernetes'] loss []
SKIP_DUPLICATE_MD MF (50, 36) -> (53, 38) gain ['arvores', 'intro', 'listas'] loss []
SKIP_DUPLICATE_MD SO (8, 7) -> (8, 7) gain [] loss []
SKIP_DUPLICATE_MD IA (36, 36) -> (36, 36) gain [] loss []
SKIP_DUPLICATE_MD ES2 (20, 18) -> (20, 18) gain [] loss []
SKIP_DUPLICATE_MD TCC (11, 9) -> (11, 9) gain [] loss []
IDENTIFIER_ALIASES ES2 (20, 18) -> (20, 18) gain [] loss []
SCORE SO exemplo-criacao-de-processos-no-unix-linux-filho sem [(33.239999999999995, 'estudo-de-casos'), (0.9072, 'chamadas-de-sistema'), (0.0, 'servicos-dos-sistemas-operacionais')]
SCORE SO exemplo-threads-em-c-exemplo1 sem [(18.855999999999998, 'estudo-de-casos'), (0.0, 'escalonamento'), (0.0, 'conceitos-basicos')]
SCORE SO exemplo-criacao-de-processos-no-unix-linux-filho determ [(33.239999999999995, 'estudo-de-casos'), (0.9072, 'chamadas-de-sistema'), (0.0, 'servicos-dos-sistemas-operacionais')]
SCORE SO exemplo-threads-em-c-exemplo1 determ [(18.855999999999998, 'estudo-de-casos'), (0.107712, 'conceitos-basicos'), (0.0, 'escalonamento')]
SCORE SO exemplo-criacao-de-processos-no-unix-linux-filho com [(33.239999999999995, 'estudo-de-casos'), (5.699999999999999, 'chamadas-de-sistema'), (0.0, 'servicos-dos-sistemas-operacionais')]
SCORE SO exemplo-threads-em-c-exemplo1 com [(22.234, 'estudo-de-casos'), (4.458, 'conceitos-basicos'), (0.107712, 'escalonamento')]
SCORE MF arvores sem [(3.488, 'provadores-de-teoremas'), (0.9072, 'abordagens-para-verificacao-formal'), (0.12494592, 'especificacao-de-funcoes-recursivas')]
SCORE MF invariantes sem [(0.12494592, 'invariante-e-variante-de-laco'), (0.01723392, 'verificacao-de-programas'), (0.01723392, 'sistema-de-prova')]
SCORE MF classes-parte2 sem [(0.12494592, 'verificacao-de-programas'), (0.01723392, 'sistema-de-prova'), (0.01723392, 'pre-e-pos-condicoes')]
SCORE MF arvores determ [(7.056, 'exemplos-de-aplicacoes'), (3.488, 'provadores-de-teoremas'), (1.0655999999999999, 'especificacao-de-funcoes-recursivas')]
SCORE MF invariantes determ [(8.106, 'invariante-e-variante-de-laco'), (0.12494592, 'verificacao-de-programas'), (0.12494592, 'correcao-parcial-e-total')]
SCORE MF classes-parte2 determ [(0.9359999999999999, 'verificacao-de-programas'), (0.12494592, 'invariante-e-variante-de-laco'), (0.01723392, 'sistema-de-prova')]
SCORE MF arvores com [(8.106, 'provadores-de-teoremas'), (1.3247999999999998, 'especificacao-de-funcoes-recursivas'), (1.1952, 'especificacao-de-conjuntos-indutivos')]
SCORE MF invariantes com [(0.12494592, 'verificacao-de-programas'), (0.12494592, 'invariante-e-variante-de-laco'), (0.01723392, 'sistema-de-prova')]
SCORE MF classes-parte2 com [(3.488, 'correcao-parcial-e-total'), (0.9359999999999999, 'verificacao-de-programas'), (0.12494592, 'invariante-e-variante-de-laco')]
SCORE ES2 roteiro7-history-service sem [(0.107712, 'gerenciamento-da-configuracao'), (0.0, 'plataformas-de-devops'), (0.0, 'monitoramento-continuo')]
SCORE ES2 roteiro4 sem [(0.107712, 'gerenciamento-da-configuracao'), (0.0, 'plataformas-de-devops'), (0.0, 'monitoramento-continuo')]
SCORE ES2 roteiro7-history-service determ [(0.107712, 'gerenciamento-da-configuracao'), (0.107712, 'estudo-de-caso-integracao-e-implantacao-de-microsservicos'), (0.0, 'plataformas-de-devops')]
SCORE ES2 roteiro4 determ [(0.107712, 'gerenciamento-da-configuracao'), (0.0, 'plataformas-de-devops'), (0.0, 'monitoramento-continuo')]
SCORE ES2 roteiro7-history-service com [(8.426, 'estudo-de-caso-integracao-e-implantacao-de-microsservicos'), (0.9072, 'gerenciamento-da-configuracao'), (0.0, 'plataformas-de-devops')]
SCORE ES2 roteiro4 com [(4.818, 'estudo-de-caso-integracao-e-implantacao-de-microsservicos'), (0.9072, 'gerenciamento-da-configuracao'), (0.107712, 'plataformas-de-devops')]

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

root,es,tax,cc,gold=load('ES2')
for t in topics(tax):
 if 'implantacao' in t['topic_slug']:print('TOPIC',t,flush=True)
e=next(e for e in es if e['id']=='roteiro7-history-service')
md='\\n'.join(md for _,md in _bundle_md(e,root))
r=_sintetico(e,root)
for word in ['RabbitMQ','rabbitmq','Circuit Breaker','circuit breaker']:
 rec=copy.deepcopy(r);rec['summary']['concepts'].append(word)
 ss=signals(e,signaltext(rec));print(word,ss['markdown_text'][-350:],[(t['topic_slug'],score(ss,t)) for t in topics(tax) if t['unit_slug']==e['computed_unit_slug']],flush=True)

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 2228ms:[0m
TOPIC {'unit_slug': 'unidade-02-integracao-de-desenvolvimento-e-operacao-devops', 'unit_title': 'Unidade 02 — Integração de Desenvolvimento e Operação (DevOps)', 'topic_slug': 'estudo-de-caso-integracao-e-implantacao-de-microsservicos', 'topic_label': 'Estudo de Caso: integração e implantação de microsserviços', 'topic_code': '2.7', 'kind': 'topic', 'generic_tokens': ['aprendizagem', 'caso', 'conceito', 'engenharia', 'estudo', 'integracao', 'microsservicos', 'modulo', 'parte', 'software', 'topico', 'unidade'], 'short_vocab': ['cd', 'ci'], 'aliases': ['2.7 Estudo de Caso: integração e implantação de microsserviços', 'Circuit Breaker', 'Composição de Containers', 'compose.yaml', 'RabbitMQ', 'Comunicação por Filas', 'Auth0', 'Autenticação e Autorização', 'Serviço em contêiner', 'Contêiner', 'Máquina Virtual', 'multi-stage build']}
RabbitMQ a com engsoft2 historyservice historyserviceapplicationtests java conceitos springframework rabbit converter history amqp message template boot application spring bean package engsoft2 historyservice core binding fanout exchange queue logger test factory context final queuename service connection json annotation conversions rabbitmq ferramenta java [('conceito-de-devops', 0.0), ('gerenciamento-da-configuracao', 0.107712), ('integracao-continua-ci', 0.0), ('entrega-continua-cd', 0.0), ('monitoramento-continuo', 0.0), ('plataformas-de-devops', 0.0), ('estudo-de-caso-integracao-e-implantacao-de-microsservicos', 4.458)]
rabbitmq a com engsoft2 historyservice historyserviceapplicationtests java conceitos springframework rabbit converter history amqp message template boot application spring bean package engsoft2 historyservice core binding fanout exchange queue logger test factory context final queuename service connection json annotation conversions rabbitmq ferramenta java [('conceito-de-devops', 0.0), ('gerenciamento-da-configuracao', 0.107712), ('integracao-continua-ci', 0.0), ('entrega-continua-cd', 0.0), ('monitoramento-continuo', 0.0), ('plataformas-de-devops', 0.0), ('estudo-de-caso-integracao-e-implantacao-de-microsservicos', 4.458)]
Circuit Breaker ngsoft2 historyservice historyserviceapplicationtests java conceitos springframework rabbit converter history amqp message template boot application spring bean package engsoft2 historyservice core binding fanout exchange queue logger test factory context final queuename service connection json annotation conversions circuit breaker ferramenta java [('conceito-de-devops', 0.0), ('gerenciamento-da-configuracao', 0.107712), ('integracao-continua-ci', 0.0), ('entrega-continua-cd', 0.0), ('monitoramento-continuo', 0.0), ('plataformas-de-devops', 0.0), ('estudo-de-caso-integracao-e-implantacao-de-microsservicos', 4.638)]
circuit breaker ngsoft2 historyservice historyserviceapplicationtests java conceitos springframework rabbit converter history amqp message template boot application spring bean package engsoft2 historyservice core binding fanout exchange queue logger test factory context final queuename service connection json annotation conversions circuit breaker ferramenta java [('conceito-de-devops', 0.0), ('gerenciamento-da-configuracao', 0.107712), ('integracao-continua-ci', 0.0), ('entrega-continua-cd', 0.0), ('monitoramento-continuo', 0.0), ('plataformas-de-devops', 0.0), ('estudo-de-caso-integracao-e-implantacao-de-microsservicos', 4.638)]

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

root,es,tax,cc,gold=load('ES2')
e=next(e for e in es if e['id']=='roteiro7-history-service')
raw=' '.join(md for _,md in _bundle_md(e,root));words=set(re.findall(r'[A-Za-z][A-Za-z0-9_]*',raw))
als={a for u in tax['units'] for t in u['topics'] for a in t.get('aliases',[]) if len(a)>=4}
hits=[a for a in als if any(re.search(r'(?<"'![a-z])'"'+re.escape(a.replace(' ',''))+r'(?=[A-Z_0-9]|"'$)'"',w) for w in words)]
print('WORDS',[w for w in words if 'abbit' in w],'HITS',hits)
def rawsyn(e,root):
 r=_sintetico(e,root)
 if e['id']=='roteiro7-history-service':r['summary']['concepts'].append('RabbitMQ')
 return r
b=evaluate('ES2','determ');r=evaluate('ES2','determ',synth=rawsyn);print(b[:2],r[:2],r[3][e['id']])
print('taxonomy MLP',[(t['topic_slug'],t['aliases']) for t in topics(load('IA')[2]) if t['topic_slug']=='modelos-preditivos'])

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 3570ms:[0m
WORDS ['RabbitMQConfig', 'rabbitmqconfig', 'rabbit', 'rabbitTemplate', 'RabbitListener', 'RabbitTemplate'] HITS ['RabbitMQ']
(20, 18) (21, 19) estudo-de-caso-integracao-e-implantacao-de-microsservicos
taxonomy MLP [('modelos-preditivos', ['Modelos Preditivos', 'modelos supervisionados', 'Classificação', 'Regressão', 'Rede Neural Perceptron', 'MultiLayer Perceptron', 'Árvore de Decisão', 'k-NN', 'Classificador Linear', 'Redes Feed Forward', 'Redes Recorrentes', 'Backpropagation'])]

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

def no_study(tax):
 for u in tax['units']:
  for t in u['topics']:
   if t['slug']=='estudo-de-casos':t['aliases']=[a for a in t['aliases'] if re.match(r'"'^'"\\d',a)]
def ownmd(e,root):
 return {} if getmd(root,e) else _sintetico(e,root)
def restored(sig):
 vocab=json.loads((Path('..')/names[sig]/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
 def change(tax):
  for u in tax['units']:
   for t in u['topics']:
    key=f\"{t.get('code','')} {t['label']}\".strip()
    for alias in vocab['_raw'].get(key,[]):
     if alias in ['Rede Perceptron','MLP','Kubernetes']:
      t['aliases'].append(alias)
 return change
def identifiers(sig):
 _,_,tax,_,_=load(sig)
 als={a for u in tax['units'] for t in u['topics'] for a in t.get('aliases',[]) if len(a)>=4}
 def synth(e,root):
  r=_sintetico(e,root)
  raw=' '.join(md for _,md in _bundle_md(e,root))
  words=set(re.findall(r'[A-Za-z][A-Za-z0-9_]*',raw))
  # Counterfactual: preserve vocabulary phrases present in raw identifiers, CamelCase boundaries.
  hits=[a for a in als if re.search(r'[A-Za-z]',a) and any(re.search(r'(?<"'![a-z])'"'+re.escape(a.replace(' ',''))+r'(?=[A-Z_0-9]|"'$)'"',w) for w in words)]
  r['summary']['concepts']+=sorted(hits)
  return r
def result(label,sig,**kwargs):
 b=evaluate(sig,'determ');r=evaluate(sig,'determ',**kwargs)
 print(label,sig,b[:2],'->',r[:2], 'gain',[k for k in b[2] if not b[2][k] and r[2][k]],'loss',[k for k in b[2] if b[2][k] and not r[2][k]],flush=True)

s=identifiers('ES2');root,es,_,_,_=load('ES2');e=next(e for e in es if e['id']=='roteiro7-history-service')
print('ADDED',s(e,root)['summary']['concepts'][30:])
r=evaluate('ES2','determ',synth=s)
print('TOTAL',r[:2])
for k in ['roteiro4','roteiro5','roteiro6','roteiro7','roteiro7-history-service']:print(k,r[3][k],r[4][k],r[5][k][-250:])

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[31m exited 1 in 2396ms:[0m
Traceback (most recent call last):
  File "<stdin>", line 103, in <module>
TypeError: 'NoneType' object is not callable

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

def no_study(tax):
 for u in tax['units']:
  for t in u['topics']:
   if t['slug']=='estudo-de-casos':t['aliases']=[a for a in t['aliases'] if re.match(r'"'^'"\\d',a)]
def ownmd(e,root):
 return {} if getmd(root,e) else _sintetico(e,root)
def restored(sig):
 vocab=json.loads((Path('..')/names[sig]/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
 def change(tax):
  for u in tax['units']:
   for t in u['topics']:
    key=f\"{t.get('code','')} {t['label']}\".strip()
    for alias in vocab['_raw'].get(key,[]):
     if alias in ['Rede Perceptron','MLP','Kubernetes']:
      t['aliases'].append(alias)
 return change
def identifiers(sig):
 _,_,tax,_,_=load(sig)
 als={a for u in tax['units'] for t in u['topics'] for a in t.get('aliases',[]) if len(a)>=4}
 def synth(e,root):
  r=_sintetico(e,root)
  raw=' '.join(md for _,md in _bundle_md(e,root))
  words=set(re.findall(r'[A-Za-z][A-Za-z0-9_]*',raw))
  # Counterfactual: preserve vocabulary phrases present in raw identifiers, CamelCase boundaries.
  hits=[a for a in als if re.search(r'[A-Za-z]',a) and any(re.search(r'(?<"'![a-z])'"'+re.escape(a.replace(' ',''))+r'(?=[A-Z_0-9]|"'$)'"',w) for w in words)]
  r['summary']['concepts']+=sorted(hits)
  return r
 return synth
def result(label,sig,**kwargs):
 b=evaluate(sig,'determ');r=evaluate(sig,'determ',**kwargs)
 print(label,sig,b[:2],'->',r[:2], 'gain',[k for k in b[2] if not b[2][k] and r[2][k]],'loss',[k for k in b[2] if b[2][k] and not r[2][k]],flush=True)

for sig in ['ES2','MF','IA','SO']:
 result('IDENTIFIER_ALIASES',sig,synth=identifiers(sig))
for sig in ['MF','SO','IA','ES2']:
 a=evaluate(sig,'com');b=evaluate(sig,'determ')
 print('PAIRED',sig,'loss',sum(a[2][k] and not b[2][k] for k in a[2]),'gain',sum(not a[2][k] and b[2][k] for k in a[2]))

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[35m[3mcodex[0m[0m
Passo 3 de 4: intervenções em memória recuperaram **7/7 erros do SO** ao retirar aliases de “Estudo de casos”, **3 do MF** ao evitar resumo duplicado sobre `.md` existente e **2 do ES2** preservando `RabbitMQ` nos identificadores. São contrafactuais locais; ainda não demonstram um filtro geral seguro.

[32m succeeded in 22700ms:[0m
IDENTIFIER_ALIASES ES2 (20, 18) -> (22, 20) gain ['roteiro7', 'roteiro7-history-service'] loss []
IDENTIFIER_ALIASES MF (50, 36) -> (50, 36) gain [] loss []
IDENTIFIER_ALIASES IA (36, 36) -> (36, 36) gain [] loss []
IDENTIFIER_ALIASES SO (8, 7) -> (8, 7) gain [] loss []
PAIRED MF loss 4 gain 3
PAIRED SO loss 0 gain 0
PAIRED IA loss 2 gain 0
PAIRED ES2 loss 5 gain 4

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f,words in [('../Metodos-Formais-Tutor/course/.content_taxonomy.json',['Exemplos','exemplos-de-aplicacoes','Corretude']),('../Metodos-Formais-Tutor/code_curation.json',['\"invariantes\"','\"terminacao\"','\"classes-parte2\"','\"inferred_title\": \"Definição e uso','\"inferred_title\": \"Implementação Verificada']),('../Engenharia-Software-2-Tutor/code/professor/currencyconversioncontroller.md',['Circuit','Resilience']),('../Engenharia-Software-2-Tutor/code_curation.json',['\"roteiro4\"','\"roteiro5\"','\"roteiro6\"','\"roteiro7\"','\"roteiro7-history-service\"']),('../Inteligencia-Artifical-Tutor/course/.glossary_curation.llm.json',['\"Rede Perceptron\"','\"MLP\"']),('src/builder/text/normalize.py',['def signal_token_set','def split_camel_case'])]:
 print('\\nFILE',f)
 for i,l in enumerate(Path(f).read_text(encoding='utf-8').splitlines(),1):
  if any(w in l for w in words):print(f'{i}: {l[:230]}')
'@ | python -B -; rg -n -A 12 'def signal_token_set' src/builder/text/normalize.py; rg -n 'invariantes|terminacao|classes-parte2|arvores|intro,|listas|roteiro[123467]' docs/reports/subunit_gt_MF.csv docs/reports/subunit_gt_ES2.csv | Select-Object -First 24"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 185ms:[0m

FILE ../Metodos-Formais-Tutor/course/.content_taxonomy.json
145:           "slug": "exemplos-de-aplicacoes",
146:           "label": "Exemplos de Aplicações",
148:             "1.4 Exemplos de Aplicações",

FILE ../Metodos-Formais-Tutor/code_curation.json
550:     "invariantes": {
556:         "inferred_title": "Definição e uso de tipos indutivos simples e predicados em Dafny",
586:     "terminacao": {
703:     "classes-parte2": {
709:         "inferred_title": "Implementação Verificada de Árvore Binária de Busca com Abstração",

FILE ../Engenharia-Software-2-Tutor/code/professor/currencyconversioncontroller.md

FILE ../Engenharia-Software-2-Tutor/code_curation.json
287:     "roteiro5": {
398:     "roteiro6": {
509:     "roteiro7": {
651:     "roteiro7-history-service": {
706:     "roteiro4": {

FILE ../Inteligencia-Artifical-Tutor/course/.glossary_curation.llm.json
98:       "Rede Perceptron",
100:       "MLP",

FILE src/builder/text/normalize.py
45: def split_camel_case(text: str) -> str:
55: def signal_token_set(
55:def signal_token_set(
56-    signal_text: str,
57-    *,
58-    normalize: Optional[Callable[[str], str]] = None,
59-    min_token_len: int = 4,
60-) -> set:
61-    """Tokens >= min_token_len do texto normalizado. Fonte unica (P4 Fase 0).
62-
63-    Antes duplicada em content_taxonomy e timeline/index. O parametro
64-    `normalize` permite injetar variantes (content_taxonomy passa a fonte
65-    unica com keep="+-./").
66-    """
67-    normalizer = normalize or normalize_match_text
docs/reports/subunit_gt_ES2.csv:6:roteiro1-introducao,Roteiro1_introducao,material-de-aula,2026-02-18,unidade-01-arquitetura-de-software,Microsserviços,Sumário · Roteiro 1: Introdução · Criando um par de microsserviços independentes · Passo 1: criando o microsserviço de câmbio · Passo 2: criando o microserviço de conversão · **Conteúdo do arquivo de propriedades:** · Conclusões · Exercício,,estudo-de-caso-arquitetura-orientada-a-microsservicos,orientada-a-microsservicos,conteudo,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26 ('concordo com tudo'). lab: criando um par de microsservicos = estudo de caso pratico (1.5)
docs/reports/subunit_gt_ES2.csv:7:roteiro1,roteiro1,codigo-professor,2026-02-18,unidade-01-arquitetura-de-software,Microsserviços,,,estudo-de-caso-arquitetura-orientada-a-microsservicos,,card,yes,"provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26 ('concordo com tudo'). zip sem markdown; irmao numerado do roteiro1-introducao, mesmo card"
docs/reports/subunit_gt_ES2.csv:16:roteiro2-nameserver,Roteiro2_nameserver,material-de-aula,2026-02-18,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,Sumário · Roteiro 2: Discovery (Name Server) e Balanceamento de Carga · Introdução · Passo 1: criando o “name server” · Passo 2: registrando os microserviços no “name server” · Passo 3: comunicando através do “name server” · Passo 4: explorando balanceamento de carga · Exercício,,estudo-de-caso-arquitetura-orientada-a-microsservicos,,oraculo (plano AVALIACAO + SARC + label Moodle),yes,"oraculo 06/09: bloco 04 (10/04-24/04) vem antes da P1 de 08/05, que pelo plano contempla so a secao 1; label do Moodle de 24/04 = 'exercicios de revisao para P1'"
docs/reports/subunit_gt_ES2.csv:17:roteiro3-gateway,Roteiro3_gateway,material-de-aula,2026-02-18,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,Sumário · Roteiro 3: Gateway · Introdução · Passo 1: criando o “gateway” · Passo 2: configurando rotas no “gateway” · Passo 3: configurando ações globais · Exercício,,estudo-de-caso-arquitetura-orientada-a-microsservicos,,oraculo (plano AVALIACAO + SARC + label Moodle),yes,"oraculo 06/09: bloco 04 (10/04-24/04) vem antes da P1 de 08/05, que pelo plano contempla so a secao 1; label do Moodle de 24/04 = 'exercicios de revisao para P1'"
docs/reports/subunit_gt_ES2.csv:18:roteiro4-circuitbreaker,Roteiro4_circuitbreaker,material-de-aula,2026-02-18,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,Sumário · Roteiro 4: Circuit Breaker · Introdução · Passo 1: configurando as dependências no “api gateway” · Passo 2: configurando rotas no “gateway” com “circuit breaker” · Passo 3: explorando o “circuit breaker” no “api gateway” · Exercício · Passo 4: configurando as dependências no “currency conversion” · Passo 5: configurando o “circuit breaker”,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,,conteudo,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. lab circuit breaker
docs/reports/subunit_gt_ES2.csv:20:roteiro6-conteiners-composicao,Roteiro6_conteiners_composicao,material-de-aula,2026-02-18,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,Sumário · Roteiro 6: Composição de Containers · Introdução · Passo 1: configurando o serviço de câmbio no “compose.yaml” · Passo 3: configurando o serviço de name server no “compose.yaml” · Passo 4: ativando o conversor de moedas e o “gateway”,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,plataformas-de-devops,conteudo,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. lab compose
docs/reports/subunit_gt_ES2.csv:21:roteiro2,roteiro2,codigo-professor,2026-02-18,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,,,estudo-de-caso-arquitetura-orientada-a-microsservicos,,oraculo (plano AVALIACAO + SARC + label Moodle),yes,"oraculo 06/09: bloco 04 (10/04-24/04) vem antes da P1 de 08/05, que pelo plano contempla so a secao 1; label do Moodle de 24/04 = 'exercicios de revisao para P1'"
docs/reports/subunit_gt_ES2.csv:22:roteiro3,roteiro3,codigo-professor,2026-02-18,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,,,estudo-de-caso-arquitetura-orientada-a-microsservicos,,oraculo (plano AVALIACAO + SARC + label Moodle),yes,"oraculo 06/09: bloco 04 (10/04-24/04) vem antes da P1 de 08/05, que pelo plano contempla so a secao 1; label do Moodle de 24/04 = 'exercicios de revisao para P1'"
docs/reports/subunit_gt_ES2.csv:23:roteiro4,roteiro4,codigo-professor,2026-06-05,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,,card,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. zip; irmao numerado
docs/reports/subunit_gt_ES2.csv:25:roteiro6,roteiro6,codigo-professor,2026-06-05,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,,card,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. zip; irmao numerado
docs/reports/subunit_gt_ES2.csv:26:revisao-p1,revisao_p1,listas,2026-04-24,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Exercícios Revisão para Provas,Exercícios – Revisão para P1 · Imagens Curadas,,,,-,no,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. lista de revisao (conteudo de u01); avaliacao transversal
docs/reports/subunit_gt_ES2.csv:33:roteiro7-filas,Roteiro7_filas,material-de-aula,2026-06-05,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,Sumário · Roteiro 7: Comunicação por Filas · Introdução · Fanout exchange routing · Passo 1: configurando a imagem do RabbitMQ no “compose.yaml” · Passo 2: configurando o microserviço produtor · Passo 3: configurando o microserviço consumidor · Passo 4: colocando o sistema para execução · Exercícios,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,,conteudo,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. lab RabbitMQ
docs/reports/subunit_gt_ES2.csv:35:roteiro7,roteiro7,codigo-professor,2026-06-05,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,,card,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. zip; irmao numerado
docs/reports/subunit_gt_ES2.csv:36:roteiro7-history-service,roteiro7_history-service,codigo-professor,2026-06-05,unidade-02-integracao-de-desenvolvimento-e-operacao-devops,Microsserviços,,,estudo-de-caso-integracao-e-implantacao-de-microsservicos,,card,yes,provenance=proposto-claude+aprovado-user-2026-08-25; RULING USER 2026-08-26. zip; irmao numerado
docs/reports/subunit_gt_MF.csv:5:exerciciosformalizacaoalgoritmosrecursao3,Exercícios - equações recursivas parte 3,listas,2026-02-18,unidade-01-metodos-formais,Especificações Indutivas e Recursivas,Exercícios · Formalização de algoritmos como equações recursivas – Parte 3,especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,especificacao-de-conjuntos-indutivos,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); arvores binarias: definicao indutiva + equacoes recursivas
docs/reports/subunit_gt_MF.csv:6:formalizacaoalgoritmos-recursao2,Especificações recursivas - listas,material-de-aula,2026-02-18,unidade-01-metodos-formais,Especificações Indutivas e Recursivas,Sumário · Funções Recursivas sobre Listas · 1. Introdução · 2. Listas polimórficas (definição indutiva) · 3. Listas polimórficas (equações recursivas),especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,especificacao-de-conjuntos-indutivos,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); listas: definicao indutiva + equacoes recursivas
docs/reports/subunit_gt_MF.csv:7:exerciciosconjuntosindutivos,Exercícios - conjuntos indutivos,listas,2026-02-18,unidade-01-metodos-formais,Especificações Indutivas e Recursivas,Prof. Júlio Machado · Exercícios · Conjuntos Indutivos,especificacao-de-conjuntos-indutivos,especificacao-de-conjuntos-indutivos,,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user)
docs/reports/subunit_gt_MF.csv:15:provasindutivas-especificacoesrecursivas-arvores,Indução estrutural sobre árvores,material-de-aula,2026-02-18,unidade-01-metodos-formais,Provas por Indução,Indução Estrutural sobre Árvores,especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,abordagens-para-verificacao-formal,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); inducao estrutural sobre arvores
docs/reports/subunit_gt_MF.csv:16:provasindutivas-especificacoesrecursivas-listas,Indução estrutural sobre listas,material-de-aula,2026-02-18,unidade-01-metodos-formais,Provas por Indução,Indução Estrutural sobre Listas,especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,abordagens-para-verificacao-formal,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); inducao estrutural sobre listas
docs/reports/subunit_gt_MF.csv:17:exercicioscorrecaoinducaomatematica,Exercícios - provas de especificações recursivas,listas,2026-02-18,unidade-01-metodos-formais,Provas por Indução,Exercícios · Provas por Indução de Especificações Equacionais Recursivas,especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,abordagens-para-verificacao-formal,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); provas por inducao de especificacoes equacionais recursivas
docs/reports/subunit_gt_MF.csv:19:exerciciosespecificacao,Exercícios - asserções lógicas,listas,2026-02-18,unidade-01-metodos-formais,Revisão - Lógica e Especificação,Métodos Formais · Especificação Formal,linguagens-de-especificacao-e-logicas,linguagens-de-especificacao-e-logicas,,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); idem
docs/reports/subunit_gt_MF.csv:20:exerciciosformalizacaoalgoritmosrecursao2,Exercícios - equações recursivas parte 2,listas,2026-02-18,unidade-01-metodos-formais,Especificações Indutivas e Recursivas,Exercícios · Formalização de algoritmos como equações recursivas – Parte 2,especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,especificacao-de-conjuntos-indutivos,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); listas
docs/reports/subunit_gt_MF.csv:21:exerciciosisabelle2,Exercícios - provas em Isabelle (parte 2),listas,2026-02-18,unidade-01-metodos-formais,Provas por Indução,Exercícios · Formalização e prova de algoritmos como equações recursivas no Isabelle (parte 2),provadores-de-teoremas,provadores-de-teoremas,especificacao-de-funcoes-recursivas,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); provas em Isabelle
docs/reports/subunit_gt_MF.csv:25:formalizacaoalgoritmos-recursao3,Especificações recursivas - árvores binárias,material-de-aula,2026-02-18,unidade-01-metodos-formais,Especificações Indutivas e Recursivas,Sumário · Funções Recursivas sobre Árvores · 1. Árvores polimórficas (definição indutiva) · 2. Árvores polimórficas (equações recursivas),especificacao-de-funcoes-recursivas,especificacao-de-funcoes-recursivas,especificacao-de-conjuntos-indutivos,conteudo,yes,provenance=proposto-claude 2026-09-05 (aguarda aprovacao do user); arvores

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f,a,b in [('../Metodos-Formais-Tutor/course/.content_taxonomy.json',143,158),('../Metodos-Formais-Tutor/code_curation.json',703,728),('src/builder/core/source_importers.py',181,236),('docs/reports/_harness-2026-09-04/c1-3/mede_zips_conteudo_perdido.py',1,120)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))):print(f'{i+1}: {ls[i]}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 166ms:[0m

FILE ../Metodos-Formais-Tutor/course/.content_taxonomy.json
143:         {
144:           "code": "1.4",
145:           "slug": "exemplos-de-aplicacoes",
146:           "label": "Exemplos de Aplicações",
147:           "aliases": [
148:             "1.4 Exemplos de Aplicações",
149:             "Ariane 5",
150:             "Eth2.0 spec",
151:             "Gödelian Ontological Argument",
152:             "Pentium FDIV",
153:             "Therac-25",
154:             "exemplos"
155:           ],
156:           "kind": "topic",
157:           "unit_slug": "unidade-01-metodos-formais"
158:         }

FILE ../Metodos-Formais-Tutor/code_curation.json
703:     "classes-parte2": {
704:       "content_hash": "25e3f9d9d8bee2a6d2d3292ff7519cc6b1e4ea3c",
705:       "matcher_version": 2,
706:       "model": "gemini-2.5-flash",
707:       "generated_at": "2026-06-28T17:46:44",
708:       "summary": {
709:         "inferred_title": "Implementação Verificada de Árvore Binária de Busca com Abstração",
710:         "language": "dafny",
711:         "pedagogical_role": "exemplo_demonstrativo",
712:         "concepts": [
713:           "Árvore Binária de Busca (ABB)",
714:           "Invariantes de Classe",
715:           "Funções Abstratas (ghost variables)",
716:           "Tripleto de Hoare Estendido",
717:           "Encapsulamento",
718:           "Relação de Abstração",
719:           "Conjuntos (set)",
720:           "Mapas (map)"
721:         ],
722:         "summary": "Este código Dafny demonstra a implementação e verificação de uma Árvore Binária de Busca. Ele foca na utilização de variáveis 'ghost' e predicados para definir a função de abstração e os invariantes de classe, garantindo a correção das operações de busca e adição.",
723:         "files": [
724:           {
725:             "name": "classes_parte2\\ArvoreBinariaBusca.dfy",
726:             "role": "implementacao_e_verificacao_abb"
727:           }
728:         ],

FILE src/builder/core/source_importers.py
181: def process_zip(builder, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
182:     import zipfile
183: 
184:     item: Dict[str, object] = {
185:         "extracted_files": [],
186:         "base_markdown": None,
187:         "extraction_error": None,
188:     }
189:     extract_dir = builder.root_dir / "staging" / "zip-extract" / entry.id()
190:     ensure_dir(extract_dir)
191:     try:
192:         # Formato pelo CONTEUDO, nao pelo nome: o raw_target do tar.gz pode
193:         # chegar nomeado so ".gz" (safe_name usa path.suffix). filter="data"
194:         # bloqueia tar-slip/paths absolutos (backport de seguranca do 3.11.4+).
195:         if zipfile.is_zipfile(raw_target):
196:             with zipfile.ZipFile(raw_target, "r") as zf:
197:                 zf.extractall(extract_dir)
198:         else:
199:             import tarfile
200:             with tarfile.open(raw_target, "r:*") as tf:
201:                 tf.extractall(extract_dir, filter="data")
202:     except Exception as exc:
203:         item["extraction_error"] = str(exc)
204:         builder.logs.append(
205:             {"entry": entry.id(), "step": "zip_extract", "status": "error", "error": str(exc)}
206:         )
207:         return item
208: 
209:     processed = []
210:     for code_path in sorted(extract_dir.rglob("*")):
211:         if _should_skip_code_import_path(extract_dir, code_path):
212:             continue
213: 
214:         relative_name = str(code_path.relative_to(extract_dir))
215:         sub_entry = FileEntry(
216:             source_path=str(code_path),
217:             file_type="code",
218:             category=entry.category,
219:             title=relative_name,
220:             tags=entry.tags,
221:             notes=f"Extraído de: {entry.title}",
222:             include_in_bundle=entry.include_in_bundle,
223:         )
224:         code_subdir = "student" if entry.category == "codigo-aluno" else "professor"
225:         safe_name_c = f"{sub_entry.id()}{code_path.suffix.lower()}"
226:         raw_target_c = builder.root_dir / "raw" / "code" / code_subdir / safe_name_c
227:         ensure_dir(raw_target_c.parent)
228:         shutil.copy2(code_path, raw_target_c)
229: 
230:         sub_result = process_code(builder, sub_entry, raw_target_c)
231:         sub_result["title"] = relative_name
232:         processed.append(sub_result)
233: 
234:     item["extracted_files"] = processed
235:     item["file_count"] = len(processed)
236:     builder.logs.append(

FILE docs/reports/_harness-2026-09-04/c1-3/mede_zips_conteudo_perdido.py
1: """Decisao 5, 0 chamadas: quantos membros de zip mostram conteudo de OUTRO zip.
2: process_zip grava raw/code/<sub>/<id-do-membro>.<ext> so pelo nome-base, entao o ultimo zip vence.
3: Compara o original em staging/zip-extract/<zip>/<membro> com o sobrevivente em raw/. Uso: python mede_zips_conteudo_perdido.py"""
4: import hashlib, json
5: from pathlib import Path
6: REPO = Path(__file__).resolve().parents[4]
7: T = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "MF": "Metodos-Formais-Tutor",
8:      "IA": "Inteligencia-Artifical-Tutor", "FR": "Fundamentos-de-Redes-Tutor", "SO": "Sistemas-Operacionais-Tutor"}
9: def h(p): return hashlib.sha1(p.read_bytes()).hexdigest()
10: print(f"{'curso':4} {'zips':>5} {'membros':>7} {'md distintos':>12} {'sobrescritos':>12} {'conteudo perdido':>16} {'zips com perda':>14}")
11: tot = [0] * 6
12: for sig, nome in T.items():
13:     root = REPO.parent / nome
14:     man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
15:     zips = membros = perdido = 0; mds = set(); zips_perda = set()
16:     for e in man:
17:         if e.get("file_type") != "zip": continue
18:         zips += 1
19:         for f in e.get("extracted_files") or []:
20:             membros += 1; mds.add(f.get("base_markdown"))
21:             title = str(f.get("title", "")).replace("\\", "/")
22:             stg = root / "staging" / "zip-extract" / e["id"] / title
23:             bm = Path(str(f.get("base_markdown") or ""))
24:             raw = root / "raw" / "code" / bm.parent.name / (bm.stem + Path(title).suffix.lower())
25:             if stg.is_file() and raw.is_file() and h(stg) != h(raw):
26:                 perdido += 1; zips_perda.add(e["id"])
27:     row = [zips, membros, len(mds), membros - len(mds), perdido, len(zips_perda)]
28:     tot = [a + b for a, b in zip(tot, row)]
29:     print(f"{sig:4} {row[0]:5} {row[1]:7} {row[2]:12} {row[3]:12} {row[4]:16} {row[5]:14}")
30: print(f"{'tot':4} {tot[0]:5} {tot[1]:7} {tot[2]:12} {tot[3]:12} {tot[4]:16} {tot[5]:14}")
31: assert tot[4] > 0, "se deu 0, ou a colisao foi corrigida ou o staging sumiu — conferir antes de acreditar"

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command 'python -B docs/reports/_harness-2026-09-04/c1-3/mede_zips_conteudo_perdido.py; git diff --numstat -- src/builder/core/vocabulary_compile.py docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py; $env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f in ['docs/reports/_harness-2026-09-04/c1-3/compila_vocab_um_curso.py','src/builder/core/vocabulary_compile.py']:
 ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i,l in enumerate(ls,1):
  if 'get_gemini_client' in l or '_raw' in l or 'file_names' in l or 'refilter' in l or 'write' in l or 'TUTOR_NO_VOCAB' in l:print(f'{f}:{i}: {l}')
'@ | python -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 2756ms:[0m
curso  zips membros md distintos sobrescritos conteudo perdido zips com perda
CG      14     273           47          226               88             11
ES2      8     131           24          107                6              4
MF      13      65           30           35               35              8
IA       4      15           15            0                0              0
FR       4       8            8            0                0              0
SO       1       2            2            0                0              0
tot     44     494          126          368              129             23
9	1	docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py
4	0	src/builder/core/vocabulary_compile.py
docs/reports/_harness-2026-09-04/c1-3/compila_vocab_um_curso.py:41: from src.builder.runtime.gemini_client import get_gemini_client  # noqa: E402
docs/reports/_harness-2026-09-04/c1-3/compila_vocab_um_curso.py:43: client = get_gemini_client(cfg)
src/builder/core/vocabulary_compile.py:12: - `.llm.json` existe -> cache; `recompile=True` (flag `recompile_vocab`) rechama; `refilter=True`
src/builder/core/vocabulary_compile.py:13:   (flag `refilter_vocab`) reaplica os filtros sobre `_raw` SEM chamar (filtro muda, dado nao rola).
src/builder/core/vocabulary_compile.py:41: from src.utils.helpers import write_text
src/builder/core/vocabulary_compile.py:128: def filter_terms(compilado: Dict[str, List[str]], *, generic: set, file_names: set,
src/builder/core/vocabulary_compile.py:149:             if not tn or tn in seen or tn == label_norm[key] or len(onde[tn]) > 1 or tn in file_names:
src/builder/core/vocabulary_compile.py:185: def _file_names(entries: list) -> set:
src/builder/core/vocabulary_compile.py:195: def _write(out_path: Path, root: Path, raw: Dict[str, List[str]], entries: list, taxonomy: dict, *,
src/builder/core/vocabulary_compile.py:197:     filtrado = filter_terms(raw, generic=_generic_tokens(taxonomy), file_names=_file_names(entries),
src/builder/core/vocabulary_compile.py:204:                   "rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). "
src/builder/core/vocabulary_compile.py:206:         "_raw": {k: list(v) for k, v in raw.items()},
src/builder/core/vocabulary_compile.py:213:     write_text(out_path, json.dumps(out, ensure_ascii=False, indent=2))
src/builder/core/vocabulary_compile.py:221:                               refilter: bool = False) -> Optional[dict]:
src/builder/core/vocabulary_compile.py:231:         if refilter and atual and isinstance(atual.get("_raw"), dict) and taxonomy:
src/builder/core/vocabulary_compile.py:232:             return _write(out_path, root, atual["_raw"], entries, taxonomy, modelo=str(atual.get("_modelo") or ""),
src/builder/core/vocabulary_compile.py:271:     return _write(out_path, root, raw, entries, taxonomy, modelo=str(getattr(client, "model", "") or ""),

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
for f,a,b in [('src/builder/routing/resolver_apply.py',54,108),('src/builder/core/vocabulary_compile.py',185,213),('src/builder/core/vocabulary_compile.py',221,256)]:
 print('\\nFILE',f);ls=Path(f).read_text(encoding='utf-8').splitlines()
 for i in range(a-1,min(b,len(ls))):print(f'{i+1}: {ls[i]}')
'@ | python -B -; rg -n 'code_curation|concepts' src/builder/routing/motor -g '*.py' | Select-Object -First 22"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 170ms:[0m

FILE src/builder/routing/resolver_apply.py
54:     INFRA (não consumida ainda): a captação (build_lesson_topic_index no import)
55:     está ativa, mas o termo de fusão por lesson foi REVERTIDO — casar o tópico da
56:     aula contra os `concepts` ruidosos do Gemini regredia o gold (11->10). Será
57:     consumida pela alavanca 1, quando o `moodle_label` der a identidade LIMPA do
58:     material pra casar contra a lesson. Ausente/inválido -> None (degradação honesta).
59:     """
60:     if root is None:
61:         return None
62:     path = Path(root) / "course" / ".lessons_index.json"
63:     if not path.is_file():
64:         return None
65:     try:
66:         data = json.loads(path.read_text(encoding="utf-8"))
67:     except (ValueError, OSError):
68:         return None
69:     return data if isinstance(data, dict) else None
70: 
71: 
72: def assemble_resolver_inputs(
73:     root: Optional[Path],
74:     entry: dict,
75:     code_curation: dict,
76: ) -> Tuple[dict, dict, dict]:
77:     """Monta os três inputs que resolve_material_assignment precisa.
78: 
79:     Fiel ao harness compare_resolver (compare_repo:124-145): markdown cru,
80:     signals via collect_entry_unit_signals, summary da curation, e injeção
81:     de entry["concepts"] apenas quando summary.concepts existe.
82: 
83:     Retorna (entry_for_resolver, signals, summary).
84:     summary é {} quando ausente — passa como llm_curation=None ao resolver.
85:     """
86:     entry_id = str(entry.get("id") or "")
87:     rec = (code_curation.get("entries") or {}).get(entry_id) or {}
88:     summary_raw = rec.get("summary")
89:     summary: dict = summary_raw if isinstance(summary_raw, dict) else {}
90: 
91:     markdown = _entry_markdown_text_for_file_map(root, entry) if root is not None else ""
92:     signals = collect_entry_unit_signals(entry, markdown or "")
93: 
94:     entry_for_resolver = dict(entry)
95:     if summary.get("concepts"):
96:         entry_for_resolver["concepts"] = summary["concepts"]
97: 
98:     return entry_for_resolver, signals, summary
99: 
100: 
101: def apply_concept_resolver(
102:     entries: list,
103:     blocks: List[dict],
104:     units: List[dict],
105:     code_curation: dict,
106:     root: Optional[Path],
107: ) -> list:
108:     """Aplica o resolver sobre os entries materiais, sobrescrevendo APENAS campos

FILE src/builder/core/vocabulary_compile.py
185: def _file_names(entries: list) -> set:
186:     out = set()
187:     for e in entries:
188:         for k in ("id", "title"):
189:             n = _norm(str(e.get(k) or ""))
190:             if n:
191:                 out.add(n)
192:     return out
193: 
194: 
195: def _write(out_path: Path, root: Path, raw: Dict[str, List[str]], entries: list, taxonomy: dict, *,
196:            modelo: str, erros: List[str], chamadas: int) -> dict:
197:     filtrado = filter_terms(raw, generic=_generic_tokens(taxonomy), file_names=_file_names(entries),
198:                             identities=identities_of(taxonomy))
199:     out: dict = {
200:         "_provenance": "llm",
201:         "_modelo": modelo,
202:         "_nota": ("Vocabulario compilado por LLM (Fase 1b, 1 chamada por unidade com material; termos dos "
203:                   "titulos/headings dos materiais classificados nos topicos do plano). Cache: reprocess nao "
204:                   "rechama; recompilar = flag recompile_vocab; refiltrar sem chamar = refilter_vocab (usa _raw). "
205:                   f"Para curar a mao, edite/crie {MANUAL_VOCAB_NAME} (o loader funde os dois)."),
206:         "_raw": {k: list(v) for k, v in raw.items()},
207:     }
208:     if erros:
209:         out["_unidades_com_erro"] = erros
210:     for key, termos in filtrado.items():
211:         if termos:
212:             out[key] = {"synonyms": termos}
213:     write_text(out_path, json.dumps(out, ensure_ascii=False, indent=2))

FILE src/builder/core/vocabulary_compile.py
221:                               refilter: bool = False) -> Optional[dict]:
222:     """Devolve o sidecar compilado (dict no formato do loader) ou None (nao compilou)."""
223:     root = Path(root)
224:     manual = root / "course" / MANUAL_VOCAB_NAME
225:     out_path = root / "course" / LLM_VOCAB_NAME
226:     if manual.is_file():
227:         logger.info("vocab: sidecar manual presente em %s — nao compila", root.name)
228:         return None
229:     if out_path.is_file() and not recompile:
230:         atual = _load(out_path)
231:         if refilter and atual and isinstance(atual.get("_raw"), dict) and taxonomy:
232:             return _write(out_path, root, atual["_raw"], entries, taxonomy, modelo=str(atual.get("_modelo") or ""),
233:                           erros=list(atual.get("_unidades_com_erro") or []), chamadas=0)
234:         return atual
235:     if client is None or not taxonomy:
236:         return None
237: 
238:     mats = [e for e in entries if _is_material(e) and str(e.get("category") or "").strip().lower() not in OUT_CATS]
239:     por_unidade: Dict[str, List[dict]] = collections.defaultdict(list)
240:     for e in mats:
241:         u = str(e.get("computed_unit_slug") or "").strip()
242:         if u:
243:             por_unidade[u].append(e)
244:     if not por_unidade:
245:         logger.info("vocab: nenhum material com unidade em %s (build do zero?) — compila no proximo reprocess", root.name)
246:         return None
247: 
248:     raw: Dict[str, List[str]] = {}
249:     erros: List[str] = []
250:     chamadas = 0
251:     for unit in taxonomy.get("units") or []:
252:         slug = str(unit.get("slug") or "")
253:         topics = [t for t in (unit.get("topics") or []) if t.get("label")]
254:         if not topics or not por_unidade.get(slug):
255:             continue
256:         key_of = {" ".join(str(t["label"]).split()): topic_key(t) for t in topics}
src/builder/routing/motor\llm_vote.py:90:    """Sidecar de votos no repo-tutor (spec §12 item 10): raiz, como code_curation.json.

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

base=load('SO',False)[2];old={(u['slug'],t['slug']):t['aliases'] for u in base['units'] for t in u['topics']}
def remove_added(tax):
 for u in tax['units']:
  for t in u['topics']:
   if t['slug']=='estudo-de-casos':t['aliases']=old[(u['slug'],t['slug'])]
for mode in ['sem','determ','com']:
 a=evaluate('SO',mode);b=evaluate('SO',mode,taxmod=remove_added)
 print('SO_ONLY_NEW_STUDY',mode,a[:2],b[:2],flush=True)
r=evaluate('MF','com');e=next(e for e in r[6] if e['id']=='classes-parte2');ss=signals(e,r[5][e['id']])
for t in topics(r[7]):
 if t['unit_slug']==e['computed_unit_slug'] and t['topic_slug']=='correcao-parcial-e-total':
  print('MF_EXACT_ALIASES',[(field,a) for field in ['markdown_headings_text','markdown_lead_text','markdown_text'] for a in t['aliases'] if ti._matches_normalized_phrase(ss[field],a)],flush=True)

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 6804ms:[0m
SO_ONLY_NEW_STUDY sem (8, 7) (15, 14)
SO_ONLY_NEW_STUDY determ (8, 7) (15, 14)
SO_ONLY_NEW_STUDY com (8, 7) (15, 14)
MF_EXACT_ALIASES [('markdown_lead_text', 'Correção'), ('markdown_text', 'Correção')]

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
Passo 3 de 4 concluído: retirar **somente os aliases novos** de “Estudo de casos” mantém a recuperação dos sete erros do SO. Limite da reprodução: os quatro cursos investigados bateram nos totais de subunidade; TCC deu **11/11 contra 10/11 no log**. Portanto, os ganhos locais ainda precisam passar pelo harness completo.

[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
from pathlib import Path
import json,zipfile
p=Path('../Engenharia-Software-2-Tutor');es=json.loads((p/'manifest.json').read_text(encoding='utf-8'))['entries']
for e in es:
 if e['id'] in ['roteiro4','roteiro5','roteiro6']:
  z=zipfile.ZipFile(p/e['raw_target']);hits=[]
  for n in z.namelist():
   if n.endswith(('.yaml','.yml','.properties','Dockerfile','.java')):
    for i,l in enumerate(z.read(n).decode('utf-8',errors='replace').splitlines(),1):
     if any(w in l.lower() for w in ['circuitbreaker','circuit-breaker','rabbitmq','docker']):hits.append((n,i,l.strip()[:130]))
  print(e['id'],'SOURCE_HITS',hits[:8],'hits_count',len(hits))
'@ | python -B -; rg -n 'CODE_EXTENSIONS|\\.ya?ml|\\.properties|Dockerfile' src/config -g '*.py' | Select-Object -First 12"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[31m exited 1 in 326ms:[0m
roteiro5 SOURCE_HITS [('roteiro5/api-gateway/src/main/resources/application.yaml', 19, '- name: CircuitBreaker'), ('roteiro5/api-gateway/src/main/resources/application.yaml', 21, 'name: currencyConversionCircuitBreaker'), ('roteiro5/api-gateway/src/main/resources/application.yaml', 30, 'include: "health,metrics,circuitbreakers"'), ('roteiro5/api-gateway/src/main/resources/application.yaml', 39, 'circuitbreaker:'), ('roteiro5/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyExchangeFallback.java', 10, 'return new CurrencyConversion(0L,from,to,BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO,"circuit-breaker fallback");'), ('roteiro5/currency-conversion-service/src/main/resources/application.yaml', 8, 'circuitbreaker:'), ('roteiro5/currency-conversion-service/src/main/resources/application.yaml', 19, 'include: "health,metrics,circuitbreakers"'), ('roteiro5/currency-conversion-service/src/main/resources/application.yaml', 28, 'circuitbreaker:')] hits_count 8
roteiro6 SOURCE_HITS [('roteiro6/api-gateway/src/main/resources/application.yaml', 19, '- name: CircuitBreaker'), ('roteiro6/api-gateway/src/main/resources/application.yaml', 21, 'name: currencyConversionCircuitBreaker'), ('roteiro6/api-gateway/src/main/resources/application.yaml', 30, 'include: "health,metrics,circuitbreakers"'), ('roteiro6/api-gateway/src/main/resources/application.yaml', 39, 'circuitbreaker:'), ('roteiro6/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyExchangeFallback.java', 10, 'return new CurrencyConversion(0L,from,to,BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO,"circuit-breaker fallback");'), ('roteiro6/currency-conversion-service/src/main/resources/application.yaml', 8, 'circuitbreaker:'), ('roteiro6/currency-conversion-service/src/main/resources/application.yaml', 19, 'include: "health,metrics,circuitbreakers"'), ('roteiro6/currency-conversion-service/src/main/resources/application.yaml', 28, 'circuitbreaker:')] hits_count 8
roteiro4 SOURCE_HITS [('roteiro4/api-gateway/src/main/resources/application.yaml', 19, '- name: CircuitBreaker'), ('roteiro4/api-gateway/src/main/resources/application.yaml', 21, 'name: currencyConversionCircuitBreaker'), ('roteiro4/api-gateway/src/main/resources/application.yaml', 30, 'include: "health,metrics,circuitbreakers"'), ('roteiro4/api-gateway/src/main/resources/application.yaml', 39, 'circuitbreaker:'), ('roteiro4/currency-conversion-service/src/main/java/com/engsoft2/currency_conversion_service/CurrencyExchangeFallback.java', 10, 'return new CurrencyConversion(0L,from,to,BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO,"circuit-breaker fallback");'), ('roteiro4/currency-conversion-service/src/main/resources/application.yaml', 8, 'circuitbreaker:'), ('roteiro4/currency-conversion-service/src/main/resources/application.yaml', 19, 'include: "health,metrics,circuitbreakers"'), ('roteiro4/currency-conversion-service/src/main/resources/application.yaml', 28, 'circuitbreaker:')] hits_count 8
rg: src/config: IO error for operation on src/config: O sistema não pode encontrar o arquivo especificado. (os error 2)

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command '$env:PYTHONIOENCODING='"'utf-8'; @'
import sys,os,json,ast,copy,re,functools,csv,socket
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode=True
os.environ['TUTOR_NO_VOCAB_COMPILE']='1'
def denied(*a,**k): raise RuntimeError('network blocked')
socket.socket.connect=denied
socket.create_connection=denied
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy,_parse_glossary_terms,_glossary_aliases_for_topic
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd
from src.builder.artifacts.repo import _glossary_curation_key,_normalize_secao
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics,_score_entry_against_taxonomy_topic as score,TopicMatchResult
from src.builder.routing.file_map import auto_map_entry_subtopic
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings
from src.builder.routing.thresholds import T
from src.builder.core.code_summarization import code_curation_signal_text as signaltext
sf=Path('docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py')
tree=ast.parse(sf.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ['_bundle_md','_sintetico']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['_CAMEL','_COMMENT','_WORD','_STOP','_FRONT','_FENCE','_HEAD','_CELULA'] for t in n.targets))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(sf),'exec'))
import src.builder.timeline.index as ti
ti._normalize_match_text=functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set=functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase=functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)
sub=functools.partial(auto_map_entry_subtopic,collect_entry_unit_signals=signals,iter_content_taxonomy_topics=topics,score_entry_against_taxonomy_topic=score,topic_match_result_factory=TopicMatchResult)
names={'MF':'Metodos-Formais-Tutor','SO':'Sistemas-Operacionais-Tutor','IA':'Inteligencia-Artifical-Tutor','ES2':'Engenharia-Software-2-Tutor','TCC':'TCC-Tutor'}
def load(sig,new=True):
 root=Path('.ablacao')/names[sig];orig=Path('..')/names[sig]
 entries=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['entries']
 tax=load_internal_content_taxonomy(root)
 if new and sig"'!='"'MF':
  vocab=json.loads((orig/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
  terms=_parse_glossary_terms((root/'course/GLOSSARY.md').read_text(encoding='utf-8'))
  secs={_normalize_secao(e.get('source_section','')) for e in entries if e.get('source_section')}
  cv={_glossary_curation_key(k):v['synonyms'] for k,v in vocab.items() if not k.startswith('_')}
  for term in terms:
   term['synonyms']=list(term.get('synonyms',[]))+[v for v in cv.get(_glossary_curation_key(term['term']),[]) if _normalize_secao(v) not in secs]
  for u in tax['units']:
   for t in u['topics']:
    t['aliases']=list(dict.fromkeys(t.get('aliases',[])+_glossary_aliases_for_topic(t['label'],u['title'],terms)))
 # current copy is old-vocab; these three units changed in new-vocab run, per paired logs.
 if new and sig=='ES2':
  u=next(u['slug'] for u in tax['units'] if 'devops' in u['slug'])
  for e in entries:
   if e['id'] in ['microsservicos4','roteiro4-circuitbreaker','roteiro4']: e['computed_unit_slug']=u
 cc=json.loads((orig/'code_curation.json').read_text(encoding='utf-8'))['entries'] if (orig/'code_curation.json').exists() else {}
 gold={r['entry_id']:r for r in csv.DictReader(Path(f'docs/reports/subunit_gt_{sig}.csv').open(encoding='utf-8-sig')) if r['scorable']=='yes'}
 return root,entries,tax,cc,gold
def evaluate(sig,mode,new=True,taxmod=None,synth=None):
 root,entries,tax,cc,gold=load(sig,new)
 if taxmod:taxmod(tax)
 passes=[];first={};texts={}
 for e in entries:
  if e.get('category') not in ['material-de-aula','codigo-professor','listas','gabaritos','slides','apostila','provas','trabalhos','exercicios','bibliografia','referencias','quadro-branco'] and not e.get('computed_block_id'):continue
  md=getmd(root,e)
  rec=cc.get(e['id'],{}) if mode=='com' else ((synth or _sintetico)(e,root) if mode=='determ' and (e.get('category')=='codigo-professor' or e.get('file_type') in ['code','zip']) else {})
  extra=signaltext(rec)
  text=md+'\\n\\n'+extra if md and extra else md or extra
  unit=e.get('computed_unit_slug','')
  match=sub(e,tax,text,winning_unit_slug=unit)
  e['computed_subunit_slug']=match.topic_slug;e['subunit_match_reasons']=match.reasons;e['subunit_match_confidence']=match.confidence
  passes.append((e,text,unit,match));first[e['id']]=match;texts[e['id']]=text
 propagar_vocabulario_por_headings(passes,tax,sub,conf_min=T.SUBUNIT_PROPAG_CONF,min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES,df_max=T.SUBUNIT_PROPAG_DF_MAX)
 pred={e['id']:e.get('computed_subunit_slug','') for e in entries}
 ok={k:pred.get(k) in ({r['gold_subunit']}|set(filter(None,r.get('gold_subunits_extra','').split(';'))) if r['gold_subunit'] else {''}) for k,r in gold.items()}
 prim=sum(pred.get(k)==r['gold_subunit'] for k,r in gold.items())
 return sum(ok.values()),prim,ok,pred,first,texts,entries,tax

def no_study(tax):
 for u in tax['units']:
  for t in u['topics']:
   if t['slug']=='estudo-de-casos':t['aliases']=[a for a in t['aliases'] if re.match(r'"'^'"\\d',a)]
def ownmd(e,root):
 return {} if getmd(root,e) else _sintetico(e,root)
def restored(sig):
 vocab=json.loads((Path('..')/names[sig]/'course/.glossary_curation.llm.json').read_text(encoding='utf-8'))
 def change(tax):
  for u in tax['units']:
   for t in u['topics']:
    key=f\"{t.get('code','')} {t['label']}\".strip()
    for alias in vocab['_raw'].get(key,[]):
     if alias in ['Rede Perceptron','MLP','Kubernetes']:
      t['aliases'].append(alias)
 return change
def identifiers(sig):
 _,_,tax,_,_=load(sig)
 als={a for u in tax['units'] for t in u['topics'] for a in t.get('aliases',[]) if len(a)>=4}
 def synth(e,root):
  r=_sintetico(e,root)
  raw=' '.join(md for _,md in _bundle_md(e,root))
  words=set(re.findall(r'[A-Za-z][A-Za-z0-9_]*',raw))
  # Counterfactual: preserve vocabulary phrases present in raw identifiers, CamelCase boundaries.
  hits=[a for a in als if re.search(r'[A-Za-z]',a) and any(re.search(r'(?<"'![a-z])'"'+re.escape(a.replace(' ',''))+r'(?=[A-Z_0-9]|"'$)'"',w) for w in words)]
  r['summary']['concepts']+=sorted(hits)
  return r
 return synth
def result(label,sig,**kwargs):
 b=evaluate(sig,'determ');r=evaluate(sig,'determ',**kwargs)
 print(label,sig,b[:2],'->',r[:2], 'gain',[k for k in b[2] if not b[2][k] and r[2][k]],'loss',[k for k in b[2] if b[2][k] and not r[2][k]],flush=True)

def preserve(sig):
 f=identifiers(sig);als={a for t in topics(load(sig)[2]) for a in t.get('aliases',[]) if len(a)>=4}
 def synth(e,root):
  r=f(e,root)
  raw=' '.join(md for _,md in _bundle_md(e,root))
  r['summary']['concepts']+=sorted(a for a in als if ti._matches_normalized_phrase(raw,a))
  return r
 return synth
for sig in ['ES2','MF','IA','SO']:
 result('PRESERVE_PHRASES',sig,synth=preserve(sig))

'@ | python -u -B -"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 17279ms:[0m
PRESERVE_PHRASES ES2 (20, 18) -> (24, 22) gain ['roteiro4', 'roteiro5', 'roteiro6', 'roteiro7', 'roteiro7-history-service'] loss ['roteiro3-gateway']
PRESERVE_PHRASES MF (50, 36) -> (50, 36) gain [] loss []
PRESERVE_PHRASES IA (36, 36) -> (36, 36) gain [] loss []
PRESERVE_PHRASES SO (8, 7) -> (8, 7) gain [] loss []

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m
[1mhook:[0m [2mPreToolUse[0m Completed
[1mhook:[0m [2mPreToolUse[0m Completed
[35m[3mexec[0m[0m
[1m"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -Command "rg -n 'circuit.breaker' ../Engenharia-Software-2-Tutor/code/professor/currencyexchangefallback.md; rg -n 'RabbitMQConfig' ../Engenharia-Software-2-Tutor/code/professor/rabbitmqconfig.md; rg -n 'Circuit|Rabbit' ../Engenharia-Software-2-Tutor/course/.glossary_curation.llm.json; git status --short -- src/builder/routing src/builder/extraction scripts/ablacao_rapida.py scripts/motor_puro.py"[0m in C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator
[32m succeeded in 220ms:[0m
24:        return new CurrencyConversion(0L,from,to,BigDecimal.ZERO,BigDecimal.ZERO,BigDecimal.ZERO,"circuit-breaker fallback");
3:title: "history-service\\src\\main\\java\\com\\engsoft2\\historyservice\\RabbitMQConfig.java"
9:# history-service\src\main\java\com\engsoft2\historyservice\RabbitMQConfig.java
29:public class RabbitMQConfig {
94:      "Circuit Breaker",
97:      "RabbitMQ",
198:      "Circuit Breaker",
201:      "RabbitMQ",
warning: unable to access 'C:\Users\Humberto/.config/git/ignore': Permission denied
warning: unable to access 'C:\Users\Humberto/.config/git/ignore': Permission denied

[1mhook:[0m [2mPostToolUse[0m
[1mhook:[0m [2mPostToolUse[0m Completed
[35m[3mcodex[0m[0m
**A regra atual reprova o corte: 124 < 128−2 = 126 — MEDIDO.** Os totais escondem trocas importantes entre materiais. [Logs determ](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_determ2_puro_b.log:38), [com](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_b.log:38).

1. **Regressões — MEDIDO.** A refutação do SO no §4 está errada: o vocabulário novo introduz **cinco erros, corrige cinco e mantém dois**. Os aliases `Linux`, `Unix`, `Pthreads` e `threads em C` favorecem “Estudo de casos”; no exemplo `filho`, o scorer dá **33,24 contra 5,70** para “Chamadas de sistema”, mesmo com Gemini. Retirar somente os aliases novos desses tópicos, em memória, recuperou **os sete erros**. [Erros antigos:59](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_vocabantigo.log:59), [aliases:19](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/compila_vocab_SO.log:19).

   **MF — MEDIDO:** `sem→com` perde `invariantes`, `terminacao` e `classes-parte2`, recupera dois: saldo −1. Os dois primeiros recebem conteúdo trocado de `tiposindutivos`; no terceiro, “Correção” no resumo vence o tópico correto (**3,49 contra 0,94**). Já o determ desvia `arvores`, `intro` e `listas` porque promove “Exemplos” do Moodle a heading: alias de “Exemplos de Aplicações”. [Conteúdo trocado:3](C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/code/professor/ex1.md:3), [resumo:722](C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/code_curation.json:722), [alias:154](C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/course/.content_taxonomy.json:154), [heading:110](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:110).

2. **Alavancas, por ganho local observado.** Generalização dos ganhos: **HIPÓTESE**. Nenhuma intervenção abaixo foi aplicada ao produto.

| Prioridade / arquivo:função | MEDIDO contra determ | Chamadas novas | Experimento de confirmação ou descarte |
|---|---:|---:|---|
| 1. [vocabulary_compile:filter_terms](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:128): controlar doações a tópicos genéricos | SO **+7/15**, sem perdas locais | 0; reutilizar `_raw` | Formular filtro independente do gold; comparar todos os materiais, inclusive casos legítimos de “Estudo de casos”. |
| 2. [shim:_sintetico](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:99): preservar expressões e identificadores presentes no vocabulário | ES2 **+5−1 = +4/28** | 0 | Preservar frases literais e limites CamelCase; reprovar variante que continue perdendo `roteiro3-gateway`. |
| 3. [shim:_sintetico](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:78): evitar resumo duplicado quando o leitor já entrega `.md` | MF **+3/58**; demais cursos investigados sem mudança | 0 | Comparar três regimes pela rota completa, mantendo síntese para zips. |
| 4. [vocabulary_compile:filter_terms](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:149): revisar veto a termo igual ao título | Restaurar `Rede Perceptron` e `Kubernetes`: **+1 IA, +1 ES2** | 0; `_raw` | Refiltrar cache e medir perdas. Restaurar `MLP` sozinho não recuperou `mlp-xoripynb`. |
| 5. [source_importers:process_zip](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/source_importers.py:225): preservar identidade do membro | **129 conteúdos divergentes**, reproduzidos; ganho de acurácia desconhecido | 0 no experimento | Substituir conteúdo por membro original em memória; medir determ novamente. Comparação com Gemini antigo continuará assimétrica. |

3. **Critério — HIPÓTESE de aceite:** `determ≥126` serve como orçamento de perda líquida, não como equivalência. O replay encontrou **11 acertos do Gemini perdidos e sete erros recuperados**. Proponho exigir também **no máximo dois acertos perdidos individualmente**, zero novos erros de bloco/unidade e zero novos erros confiantes; repetir com voter cacheado e no holdout. Empate primário **105/151** não elimina essas trocas. [Scorer:197](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:197), [critério de confiança:65](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md:65).

4. **Desenho — MEDIDO:** 151 e 93 não sustentam comparação histórica direta. Apagar o sidecar manual mede outro produto; voter desligado não testa a arquitetura final de duas camadas. “Sem resumo” também **não significa código vazio**: código avulso possui `.md`, consumido pelo leitor. Além disso, o log antigo mostra unidade do SO **32→30** com vocabulário novo. [Ablação:65](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/scripts/ablacao_rapida.py:65), [leitor:74](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/navigation.py:74), [SO antigo:30](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_vocabantigo.log:30).

   **Limite desta análise:** replay de subunidade com unidades fixadas reproduziu os totais de MF/SO/IA/ES2; TCC divergiu, **11 contra 10**. Ganhos locais ainda não constituem validação integral nem resultado do produto reprocessado.

5. **ES2 — MEDIDO:** os quatro ganhos determ são `roteiro1/2/3` e **`roteiro3-gateway`, material de aula**; Gemini ganha outros cinco: `roteiro4/5/6/7` e `roteiro7-history-service`. Falta preservar sinal existente: `_sintetico` fragmenta `RabbitMQConfig` e dispersa `circuit-breaker fallback` na lista de tokens. Preservar `RabbitMQ` recuperou dois; preservar também frases literais recuperou os cinco, com uma regressão por propagação. **Não falta conhecimento externo nesses cinco casos.** [RabbitMQ:29](C:/Users/Humberto/Documents/GitHub/Engenharia-Software-2-Tutor/code/professor/rabbitmqconfig.md:29), [circuit-breaker:24](C:/Users/Humberto/Documents/GitHub/Engenharia-Software-2-Tutor/code/professor/currencyexchangefallback.md:24), [cortes da síntese:103](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:103).
[1mhook:[0m [2mStop[0m
[1mhook:[0m [2mStop[0m Completed
[2mtokens used[0m
179.000
**A regra atual reprova o corte: 124 < 128−2 = 126 — MEDIDO.** Os totais escondem trocas importantes entre materiais. [Logs determ](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_determ2_puro_b.log:38), [com](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_b.log:38).

1. **Regressões — MEDIDO.** A refutação do SO no §4 está errada: o vocabulário novo introduz **cinco erros, corrige cinco e mantém dois**. Os aliases `Linux`, `Unix`, `Pthreads` e `threads em C` favorecem “Estudo de casos”; no exemplo `filho`, o scorer dá **33,24 contra 5,70** para “Chamadas de sistema”, mesmo com Gemini. Retirar somente os aliases novos desses tópicos, em memória, recuperou **os sete erros**. [Erros antigos:59](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_vocabantigo.log:59), [aliases:19](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/compila_vocab_SO.log:19).

   **MF — MEDIDO:** `sem→com` perde `invariantes`, `terminacao` e `classes-parte2`, recupera dois: saldo −1. Os dois primeiros recebem conteúdo trocado de `tiposindutivos`; no terceiro, “Correção” no resumo vence o tópico correto (**3,49 contra 0,94**). Já o determ desvia `arvores`, `intro` e `listas` porque promove “Exemplos” do Moodle a heading: alias de “Exemplos de Aplicações”. [Conteúdo trocado:3](C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/code/professor/ex1.md:3), [resumo:722](C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/code_curation.json:722), [alias:154](C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/course/.content_taxonomy.json:154), [heading:110](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:110).

2. **Alavancas, por ganho local observado.** Generalização dos ganhos: **HIPÓTESE**. Nenhuma intervenção abaixo foi aplicada ao produto.

| Prioridade / arquivo:função | MEDIDO contra determ | Chamadas novas | Experimento de confirmação ou descarte |
|---|---:|---:|---|
| 1. [vocabulary_compile:filter_terms](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:128): controlar doações a tópicos genéricos | SO **+7/15**, sem perdas locais | 0; reutilizar `_raw` | Formular filtro independente do gold; comparar todos os materiais, inclusive casos legítimos de “Estudo de casos”. |
| 2. [shim:_sintetico](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:99): preservar expressões e identificadores presentes no vocabulário | ES2 **+5−1 = +4/28** | 0 | Preservar frases literais e limites CamelCase; reprovar variante que continue perdendo `roteiro3-gateway`. |
| 3. [shim:_sintetico](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:78): evitar resumo duplicado quando o leitor já entrega `.md` | MF **+3/58**; demais cursos investigados sem mudança | 0 | Comparar três regimes pela rota completa, mantendo síntese para zips. |
| 4. [vocabulary_compile:filter_terms](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:149): revisar veto a termo igual ao título | Restaurar `Rede Perceptron` e `Kubernetes`: **+1 IA, +1 ES2** | 0; `_raw` | Refiltrar cache e medir perdas. Restaurar `MLP` sozinho não recuperou `mlp-xoripynb`. |
| 5. [source_importers:process_zip](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/source_importers.py:225): preservar identidade do membro | **129 conteúdos divergentes**, reproduzidos; ganho de acurácia desconhecido | 0 no experimento | Substituir conteúdo por membro original em memória; medir determ novamente. Comparação com Gemini antigo continuará assimétrica. |

3. **Critério — HIPÓTESE de aceite:** `determ≥126` serve como orçamento de perda líquida, não como equivalência. O replay encontrou **11 acertos do Gemini perdidos e sete erros recuperados**. Proponho exigir também **no máximo dois acertos perdidos individualmente**, zero novos erros de bloco/unidade e zero novos erros confiantes; repetir com voter cacheado e no holdout. Empate primário **105/151** não elimina essas trocas. [Scorer:197](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:197), [critério de confiança:65](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md:65).

4. **Desenho — MEDIDO:** 151 e 93 não sustentam comparação histórica direta. Apagar o sidecar manual mede outro produto; voter desligado não testa a arquitetura final de duas camadas. “Sem resumo” também **não significa código vazio**: código avulso possui `.md`, consumido pelo leitor. Além disso, o log antigo mostra unidade do SO **32→30** com vocabulário novo. [Ablação:65](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/scripts/ablacao_rapida.py:65), [leitor:74](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/navigation.py:74), [SO antigo:30](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/codigo_com_puro_vocabantigo.log:30).

   **Limite desta análise:** replay de subunidade com unidades fixadas reproduziu os totais de MF/SO/IA/ES2; TCC divergiu, **11 contra 10**. Ganhos locais ainda não constituem validação integral nem resultado do produto reprocessado.

5. **ES2 — MEDIDO:** os quatro ganhos determ são `roteiro1/2/3` e **`roteiro3-gateway`, material de aula**; Gemini ganha outros cinco: `roteiro4/5/6/7` e `roteiro7-history-service`. Falta preservar sinal existente: `_sintetico` fragmenta `RabbitMQConfig` e dispersa `circuit-breaker fallback` na lista de tokens. Preservar `RabbitMQ` recuperou dois; preservar também frases literais recuperou os cinco, com uma regressão por propagação. **Não falta conhecimento externo nesses cinco casos.** [RabbitMQ:29](C:/Users/Humberto/Documents/GitHub/Engenharia-Software-2-Tutor/code/professor/rabbitmqconfig.md:29), [circuit-breaker:24](C:/Users/Humberto/Documents/GitHub/Engenharia-Software-2-Tutor/code/professor/currencyexchangefallback.md:24), [cortes da síntese:103](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py:103).
exit 0
01:22:40
