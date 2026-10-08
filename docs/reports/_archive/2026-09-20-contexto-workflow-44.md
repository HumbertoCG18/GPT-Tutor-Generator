# Consolidação do contexto e papéis das CLIs — #44

Issue: https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/44
Estado: consolidação distribuída; hooks configurados e testados diretamente. Confiança nativa
do Codex e delegação em sessão nova pendentes. Sem commit, merge ou execução noturna.

## Medição

Tokenizer: tiktoken 0.14.0, o200k_base, ambiente uv --no-project --with tiktoken.
É uma régua reproduzível de texto, não tokenizer atestado dos três modelos nem cobrança de assinatura.
Nenhuma chamada adicional de modelo via CLI nesta entrega.

| Conjunto | Tokens |
|---|---:|
| Mesmas sete superfícies antes | 11.648 |
| Bootstrap consolidado | 3.450 |
| Handoff do workflow | 191 |
| orch-add-feature + orch-pipeline | 2.026 |
| Roteamento carregado uma vez | 243 |
| Lembrete Claude/Codex por UserPromptSubmit | 72 |
| Cenário de planejamento acima | 5.982 |

Sete superfícies: personal-instructions.md, workflow.md, AGENTS.md do projeto,
.mex/AGENTS.md, .mex/ROUTER.md, .workflow/README.md e engenharia-produto.md.
Redução comparável do bootstrap: aproximadamente 70,4%. Não comparar 5.982 com 13.990 como
experimento controlado: o lote antigo incluía outros documentos/releituras.
O cenário não inclui estado ativo adicional, fontes de código, outras skills, catálogo de ferramentas,
instruções da plataforma, mensagens de plugins ou conversa. Tarefas que exigirem isso podem exceder 6k.
AGY: lembrete de 88 tokens por PreInvocation; pode ocorrer após ferramentas, não só por mensagem.
Quota/cache/latência e delegação E2E não foram medidos.

## Fontes e distribuição

Fonte compartilhada: agent-workflow-lab; edição isolada em agent-workflow-lab-context-44,
branch refactor/44-context. Integração GPT em GPT-Tutor-Generator-context-44,
branch refactor/44-workflow-context. Alterações anteriores foram preservadas nos arquivos usados
como baseline; worktrees não representam só commits limpos do novo escopo.
As instruções pessoais foram distribuídas para ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md e
~/.gemini/GEMINI.md. Fonte e três destinos comparados byte a byte.
O GPT Tutor corrente recebeu mapa/identidade/engenharia curtos e snapshot .workflow revisado.
Outras branches/worktrees existentes não foram sobrescritos. Fonte canônica tem precedência;
snapshots antigos servem como fallback e precisam de atualização revisada ao integrar suas branches.

As sete seções do workflow anterior foram movidas para references/; detalhe de ferramentas
pessoais foi preservado em tooling.md. Routing é curto; configuração fica em routing-details.md.
Histórico do mapa/identidade preservado em .mex/context/*-history.md; engenharia detalhada
em engenharia-produto-details.md. Não carregar esses históricos no bootstrap.

## Papéis e hooks

Claude Code: terminal principal, Fable implementa e testa.
Codex: planeja/orquestra tarefas complexas; Astra faz revisão independente delimitada.
AGY: auditoria/pesquisa e achados/documentação em arquivos autorizados.
Contratos inline novos: agents/codex-planner.md e agents/agy-auditor.md. Não são registro
de agentes nativos nem instalam outro executor.

Hooks nativos adicionados preservando os existentes: UserPromptSubmit no Claude/Codex,
PreInvocation no AGY. Fonte em agent-workflow-lab/hooks/registration.json e routing-*.json.
Cada comando imprime JSON estático; não lança LLM, não executa fila nem escreve estado.
A decisão semântica por dificuldade/escopo cabe ao agente ativo orientado pelo contrato.
Isto é automação de instrução, não enforcement técnico de delegação/Gates/contadores.

Verificações locais: 3/3 comandos com exit 0 e envelope correto; configurações sem o fragmento
novo idênticas aos backups. Links dos núcleos conferidos; manifests/hashes revalidados.
verify.py mantém erro preexistente: Codex Companion reenabled inside Codex. Não foi desabilitado
sem auditar uso/dependências. Arquivos gerenciados e instruções pessoais não divergiram.

## Próxima validação e rollback

Abrir nova sessão; no Codex, revisar/confiar a nova definição UserPromptSubmit em /hooks.
No Claude/AGY, inspecionar /hooks e validar uma tarefa real, preservando contadores anteriores.
Configuração presente + comando isolado verde não provam carregamento nativo ou delegação E2E.
O runtime noturno #42 continua bloqueado; fila/catalogação #43 não foram reimplementadas.
Hook diurno não implica herança em subprocesso safe-mode do supervisor noturno.

Rollback: remover somente handlers desta tarefa; conferir alterações posteriores antes de restaurar
documentos. Baselines privados: agent-workflow-lab/private/context-consolidation-20260920/before/.
Não publicar esses backups: incluem configurações pessoais. Código de produto e credenciais intactos.

Fontes de interface: [Claude](https://code.claude.com/docs/en/hooks),
[Codex](https://learn.chatgpt.com/docs/hooks),
[Antigravity](https://antigravity.google/docs/hooks?tab=ide).
