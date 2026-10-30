# Ferramentas locais e portabilidade

Fonte das skills pessoais compartilhadas: `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/skills`.
Claude, Codex e AGY têm destinos próprios; validar com `verify.py` nesse laboratório.
Alethe cuida das sessões. Não reimportar bundles inteiros nem deixar dois gestores
reescreverem os mesmos destinos. Skillfile permanece apenas piloto, sem sincronização automática.

Graphify é o único grafo de código nas três CLIs. CBM removido na FERR-01 (#64) por falta de uso
(Claude 0/4.622 sessões, Codex 20 chamadas em 3 sessões, AGY 1, medido em 15/10).
GPT Tutor: fallback CBM removido do `.mex` na REC-06.
Graphify roda pela CLI local nas três (graphify query/explain/path no projeto atual);
o MCP saiu porque servia um graph.json fixo do GPT Tutor em qualquer projeto.

## MCPs por CLI (paridade medida em 30/09/2026)

Movido para [tooling-details.md › MCPs por CLI](tooling-details.md#mcps-por-cli-paridade-medida-em-30092026): contagens de uso, MCPs removidos, como readicionar e backups. Iguais nas três: context7, claude-mem (mcp-search); GitHub e Graphify pelas CLIs gh e graphify.

## Codex Companion (plugin codex@openai-codex)

Medido em 17/10/2026 com count_tool_use.py (Claude/Codex/AGY: 4.979/649/237 sessões):
codex-rescue como tool 0/0/0, Skill codex:* 1/0/0, astra-review 123/0/0. Caminho oficial de
leitura no Codex: codex_read/astra_review (no Alethe, alethe_delegate readOnly).
Invariante: o Codex não carrega o Companion (Codex chamando Codex é circular); verify.py falha
se ele estiver ligado, e o conserto é desligar (#110), não remover a regra para deixar verde.
No Claude Code o plugin fica: zero uso sem cobertura total dos transcripts é lacuna, não prova.
Remedir com `--until` em 17/11 antes de desligar, seguindo references/capabilities.md.
Controle do revisor só leitura (ACH-0006, medido em 18/10 com `codex exec --profile astra --sandbox
read-only` e `windows.sandbox = "elevated"`): escrita em arquivo, `git commit` e rede (`WinError 10013`)
falham; push e `gh` de escrita dependem de rede. A regra no brief (#114) é só instrução; o sandbox é o controle.

Codex medido: 0.165.0 (28/10/2026, #479; sondas repetidas na 0.165.0, #62). No Windows o Codex roda cada hook pelo `pwsh -Command`, que
troca exit 2 por 1, e com 1 a chamada passa (openai/codex#54072); os guardas do lab no modo `codex` negam
com exit 0 + JSON deny, que saiu `Blocked` no `codex exec`. Versão nova do Codex: o verify.py avisa até
alguém repetir as sondas da CODEX-03 (chave falsa e `git -c … commit` num repo descartável) e trocar esta linha.

RTK rtk-oss 1.0.1 (Apache-2.0; o binário padrão da 1.0 inclui motor BUSL-1.1) está em
`C:/Users/Humberto/.local/bin/rtk.exe`. Piloto da fase 1 (CUSTO-02, #128, medir em 24/10):
o hook `hooks/rtk-pytest-only.py` do lab (#470) aceita a reescrita do `rtk hook claude` só
quando os operadores `&&`/`;` ficam iguais e cada trecho fica como digitado ou igual à
reescrita que o próprio hook calcula: `rtk ` antes de `pytest|cargo|ls|gh|wc`, ou
`python -m pytest` → `rtk pytest`, com os mesmos argumentos. Caractere fora do ASCII
imprimível (exceto espaço e tab, p. ex. NBSP), quebra de linha, pipe, `&`,
subshell, `$`, crase, aspas, `\`, `#` ou redirecionamento (exceto `2>&1`) no original ou na
reescrita, e falha ou timeout do rtk, deixam o comando nativo. `vitest` e `npm test` ficam fora. Rollback: `~/.claude/hooks/rtk-pytest-only.py.bak-custo02`
(hook) e `rtk-0.49.0.exe.bak` (binário). `%APPDATA%/rtk/config.toml` só cala o aviso do
hook global (`suppress_hook_warning`); telemetria desligada. Se o pytest do projeto não
estiver no PATH, preservar o ambiente nativo e executar o comando original.
Recuperar detalhes omitidos com `rtk recall <hash> --full` quando houver indicação.
Para comparação exata, JSON ou pipelines, usar saída original. Não aplicar RTK a
rg/grep, git ou todos os comandos via hook sem medição específica. Não confundir
redução de bytes com economia comprovada de quota.

Aprendizagem: ao fechar trabalho relevante, usar ECC para propor correções com
 evidência; não editar skills globais automaticamente. Tracker/handoff preservam
continuidade quando claude-mem não grava. Não reiniciar o worker por erro de quota.

Portabilidade ECC: dentro do Alethe, seguir o caminho de Orquestração ([tooling-alethe.md](tooling-alethe.md)).
Fora dele, usar subagente nativo quando disponível. Se a CLI não expuser
o papel, executar a etapa inline seguindo a definição em
`C:/Users/Humberto/Documents/GitHub/agent-workflow-lab/agents/`
(tdd-guide.md ou python-reviewer.md), preservando Gates 1/2. Nunca inventar
uma chamada de subagente. Ausência do papel ECC não é gatilho para escalar ao revisor.

## `/goal`: encerrar só com a suíte verde
Sem hook novo no Stop além do `tamanho.py` (#374, aprovado em 24/10); em 21/10 os 10 hooks Stop da sessão, plugins incluídos, somavam 2,3 s por turno (#244). `/goal` é um hook Stop de prompt, por sessão; custo do avaliador não medido.
Usar em trabalho com fim verificável. Exemplo: `/goal pytest -q bin hooks claude plugins githooks sai com código 0, ou parar após 20 turnos`.
O avaliador (modelo pequeno) não roda comandos: só lê o que o agente mostrou. Pedir o comando e a saída final.
Limite da condição: 4.000 caracteres. `/goal clear` remove. Indisponível com `disableAllHooks`.
Fonte: https://code.claude.com/docs/en/goal

## Leitura que cabe no contexto (#339)

Medido em 23/10 na sessão 9d476570: depois da compactação, 218 saídas de ferramenta somaram 269.563 caracteres, e 3 leituras inteiras ocuparam 75.303 deles. Para evitar:
- Arquivo ou artefato grande: localizar com `grep -n` ou com a ferramenta Grep, e ler só o trecho (`Read` com `offset`/`limit`). O `Artifact read` salva o HTML num arquivo local, que também se lê por trecho. O painel lido inteiro custou 49.999 caracteres.
- Busca no lab exclui `graphify-out/` (`--exclude-dir=graphify-out`, ou `glob` na Grep). Sem isso, um `grep -rln` deu 15.394 caracteres, a maior parte de `graph.json` diários.
- `bin/show-config.py`: primeiro `--keys`, depois o caminho mais estreito que responde, nunca o bloco `hooks` inteiro. `hooks.PreToolUse` deu 9.910 caracteres, quase tudo `node -e` dos hooks ECC.

## Número medido

Movido para [tooling-details.md › Número medido](tooling-details.md#número-medido): N, faixa e limitador de todo número citado, e o checklist antes de citar.

## Donos por fase

Saíram das instruções pessoais na #180. Uma fase, um dono.
- Escopo mínimo: ponytail; reutilizar antes de construir.
- Estrutura: Graphify explain/path antes de query com budget; confirmar projeto e fonte atual.
- Nomes do ECC sem prefixo no Claude Code; no Codex e no AGY, `ecc:<nome>`.
- Nova capacidade: orch-add-feature. Refatoração: orch-refine-code. Defeito: orch-fix-defect, com o teste vermelho primeiro.
- Implementação no papel tdd-guide. Revisão pelo contrato do revisor (review.md), com o checklist python-reviewer/code-review e sem criar outro revisor pago.
- Medição repetida: parallel-execution-optimizer. Git e PR: git-workflow e pr. Aprendizado: skill-create quando disponível.
- Escada de aprendizado: erro que se repete vira primeiro check mecânico (hook, `verify.py` ou teste) e só depois texto. O check só vale se falhar (vermelho) com o caso real passado e passar após a correção; registrar o caso na issue ou no teste.
- Skills: carregar só na fase correspondente e conforme as regras da CLI. Leitura com objetivo: `rg` localiza, depois só o trecho necessário.
- Fontes: o mapa de fontes do projeto localiza (tabela tarefa → estado e fontes): `.mex/ROUTER.md` quando existir; sem `.mex`, uma seção nesse formato no AGENTS.md. A memória é a quarta fonte, depois de tracker e handoff; não buscar sessão anterior já documentada.
- Salvar na memória só o que surpreenderia uma sessão futura e não se deriva de código, git ou docs. Cada lição leva a fonte e o gatilho de invalidação.

## Glossário e ADR leve

Movido para [tooling-details.md › Glossário e ADR leve](tooling-details.md#glossário-e-adr-leve): quando criar glossário/ADR, formato mínimo e como medir consultas.

## Alethe

Movido para [tooling-alethe.md › Alethe como Orquestração principal](tooling-alethe.md#alethe-como-orquestração-principal): nomes nativos, dispatch único e limites do Alethe.

Movido para [tooling-alethe.md › Build do Alethe (pastas de saída do cargo)](tooling-alethe.md#build-do-alethe-pastas-de-saída-do-cargo): `CARGO_TARGET_DIR`, verificação enxuta, atualizar o Alethe Dev e `cargo check`.
