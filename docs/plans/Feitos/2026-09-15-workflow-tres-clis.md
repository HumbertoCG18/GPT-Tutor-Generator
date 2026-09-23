# Plano de implementação: workflow comum para Claude Code, Codex e AGY

**Estado:** aprovado e implantado nas três CLIs; aceite final pelo Alethe pendente. Execução e desvios medidos em `docs/reports/workflow-implantacao_15-09.md`; estado vivo no tracker.
**Objetivo:** reduzir contexto inicial e conflitos, tornar a seleção de skills reproduzível e testar economia de saída sem acrescentar API paga.
**Arquitetura:** Alethe cuida das sessões; ECC do processo; um conjunto pequeno de skills comuns e pacotes por projeto. Um único gestor escreve cada destino. Instalação de skills não implica portabilidade de hooks, agentes ou autenticação.
**Execução:** seguir os donos definidos no AGENTS.md do usuário. A aprovação deste plano autoriza apenas as fases selecionadas; nenhum commit, publicação ou remoção destrutiva implícita.
**Plataforma medida:** Windows/PowerShell; Codex CLI 0.154.0; Claude Code 2.1.273; AGY é Antigravity CLI, não Gemini CLI.

## 1. Diagnóstico e evidências

Auditoria em 15/09/2026, horário de São Paulo. Fontes externas fixadas por SHA em
`docs/reports/_workflow-audit-2026-09-15/candidate-sources.json`.
Downloads apenas de documentação; nenhum instalador remoto executado.

| Superfície | Medição | Interpretação / limite |
|---|---|---|
| Codex local, skills/list | 78 entradas, 74 enabled, 4 disabled; nenhum erro | Catálogo retornado pelo app-server; não inclui necessariamente todas as skills injetadas pela aplicação/conectores |
| Descrições dessas 74 | 18.366 caracteres | Não são tokens nem uma medição do orçamento completo da sessão |
| ECC no catálogo Codex | 24: 20 skills + 4 comandos migrados | O pacote já foi reduzido; não recomendar remover 600 supostas skills ativas |
| Skills pessoais | 23 em .agents/skills, 12 em .codex/skills, 8 em .claude/skills | Arquivos descobertos, incluindo sistema e cópias desabilitadas; não somar como invocações |
| ECC Claude | 286 skills no diretório principal; 261 user-invocable-only e 25 sem override | Entre as 25, cinco de pesquisa científica fora do núcleo de programação |
| ECC AGY | 20 skills no diretório principal | Os 632 SKILL.md dentro do bundle incluem traduções e arquivos de outras plataformas |
| AGY | Importações ponytail, ecc, claude-mem; três plugins habilitados no config local | Instalado/importado não prova que todo hook executa no AGY |
| Repositórios | 12 repositórios irmãos sob Documents/GitHub | Quatro skills de projeto encontradas em T-ES2; GPT Tutor usa skills globais e hooks próprios |
| Memória nativa Codex | 42 arquivos, 82.059 bytes; memory_summary.md 2.563 bytes | Não há evidência de grande volume que justifique limpeza automática |
| Instruções pessoais | CLAUDE.md, AGENTS.md e GEMINI.md: 7.914 bytes e mesmo SHA256 | Preservar esse contrato, não criar três cópias divergentes |

Inventário completo: `skills-inventory.csv`; configurações filtradas: `inventory-summary.json`.
A varredura física registrou 2.342 ocorrências de SKILL.md, incluindo traduções,
caches e subdiretórios que não entram no catálogo. Não são 2.342 skills ativas.
Escopo: diretórios pessoais conhecidos, registro Claude, caches Codex, plugins AGY
em .gemini/config e 12 repositórios irmãos. Não é uma busca no disco inteiro.

Uso observado, amostra limitada: 30 JSONL mais recentemente modificados por CLI.
Claude: 62 chamadas reais; Codex: 167 chamadas externas, principalmente exec/wait.
Não foram encontradas invocações explícitas de Skill nessa amostra; isso NÃO prova
desuso: leitura direta de arquivos, chamadas dentro de exec e uso implícito ficam
fora dessa contagem. Histórico AGY não foi decodificado. Não excluir recursos com
base em ausência nesta amostra. Evidência: `usage-sample.json`.

### Problemas concretos

- As quatro desativações anteriores funcionaram: skills/list confirma quatro disabled.
  O aviso persiste porque elas retiraram só parte do catálogo. Ele diz respeito às
  descrições de skills, não ao banco de memória nem à saída de comandos.
- Graphify e graphify-windows continuam simultâneos. Consolidar preservando as
  adaptações Windows e o intérprete Python311; não deduplicar só pelo nome.
- Há duas medir-uso-antes-de-remover. A cópia Codex contém duas correções úteis:
  caminho Claude correto e nome claude-mem. Incorporar essas correções à fonte
  comum antes de desativar a outra. A cópia .agents contém erros nesses dois pontos.
- using-superpowers impõe acionamento amplo e brainstorming antes de planejamento,
  enquanto o usuário escolheu ECC como dono dessas fases. Testes, planejamento,
  revisão e encerramento também têm múltiplos donos potenciais.
- O Codex Companion contém helpers explicitamente destinados a chamar Codex a
  partir do Claude. No Codex, consome catálogo e adiciona hooks; no Claude tem
  finalidade concreta. Testar desativação apenas no Codex, mantendo a integração Claude.
- O Claude já tem statusline Python com modelo/diretório/Git; o próprio arquivo
  diz que contexto e quotas ficam na barra do app. ClaudeHUD não é uma lacuna automática.
- Alethe já gerencia skills/MCP. A configuração de projeto do Graphify ainda contém
  a forma inválida graphify <repo> --mcp relatada anteriormente. Não acrescentar um
  segundo sincronizador sobre os mesmos destinos antes de resolver quem escreve.
- Existem tdd-guide.md e python-reviewer.md nos bundles Claude/AGY; nenhuma função
  equivalente aparece em [agents] do Codex pessoal. Um arquivo distribuído não
  comprova que o subagente é chamável nas três CLIs.

## 2. Avaliação de todas as propostas

“Sem API paga adicional” não significa inferência ilimitada ou ausência de consumo
da assinatura. Ferramentas locais podem economizar contexto; o modelo principal
continua sujeito às quotas existentes. Não acrescentar roteamento automático para
APIs pagas como fallback.

| Projeto | Função e custo | Compatibilidade / sobreposição | Decisão |
|---|---|---|---|
| [RTK](https://github.com/rtk-ai/rtk) | Filtra saídas de comandos localmente; sem inferência remota necessária | Windows; hooks Claude/Codex documentados. Antigravity via regra de projeto; não confundir com hook Gemini CLI | Primeiro piloto funcional, inicialmente chamadas explícitas |
| [Skillfile](https://github.com/eljulians/skillfile) | Gerencia skills/agentes com lock e patches; sem API de LLM | Claude/Codex e destino Antigravity; install-path permite destino explícito. Não transporta semântica de hooks | Candidato preferido a gestor único, somente se passar piloto isolado |
| [Kasetto](https://github.com/pivoshenko/kasetto) | Gerencia skills, MCP, comandos e instruções; lock, Windows, dry-run | Escopo maior colide com o gerenciamento Alethe. Destino Antigravity documentado não é automaticamente AGY CLI | Alternativa ao Skillfile, nunca os dois; reservar para substituir gestão de configuração inteira |
| [ClaudeHUD](https://github.com/jarrodwatts/claude-hud) | Statusline local; versão consultada usa stdin/transcript, sem chamadas de rede próprias | Só Claude; substituiria a statusline atual e repetiria parte do Alethe | Opcional, não fase obrigatória; adotar apenas se faltar informação útil fora do Alethe |
| [CodexMemoryTrim](https://github.com/Yu-Xiao-Sheng/codex-memory-trim) | Audita/edita memória nativa Codex, incluindo banco/rollouts; execução usa o agente | Só Codex. Não limpa descrições de skills e não corrige claude-mem | Adiar limpeza; considerar apenas auditoria read-only se houver problema comprovado de memória |
| [One Skill to Rule Them All](https://github.com/rebelytics/one-skill-to-rule-them-all) | task-observer propõe melhorias; usa contexto/inferência do agente | Markdown adaptável, mas sobrepõe ECC learn/skill-create e captura do claude-mem | Aproveitar revisão manual de correções no fluxo existente; não instalar observador permanente |
| [Hermes Agent](https://hermes-agent.nousresearch.com/docs/integrations/providers) | Outro runtime, com memória, skills, cron e canais; aceita modelos locais e ChatGPT OAuth segundo documentação | Não é uma skill das três CLIs; cria outro dono para execução/memória | Fora da stack de desenvolvimento por enquanto; reavaliar para automações pessoais/canais |
| [Hermes Brasil](https://github.com/Hermes-brasil/hermes-brasil) | Coleção de guias/skills PT-BR | anti-ai-slop repete instruções de escrita; outras skills focam Hermes/negócios | Fonte de consulta; importar somente uma skill específica quando houver demanda |
| [Hermes HUD](https://github.com/joeynyc/hermes-hud) | TUI para dados do Hermes | Depende de Hermes; README declara macOS/Linux, não comprova Windows nativo | Não adicionar |
| [Doberman Core](https://github.com/DobermanCore/Doberman-Core) | Políticas locais em hooks/proxy MCP | Alpha; hook Codex experimental; não comprova interceptação total do AGY. Soma autorizações às nativas/guards do projeto | Adiar; somente piloto de segurança separado se surgir requisito concreto |
| [TruthProbe](https://github.com/miso-choi/TruthProbe) | Pesquisa sobre intervenções em modelos; exige acesso aos pesos e ambiente de avaliação | Não é verificador genérico de respostas nem skill aplicável aos modelos fechados das três CLIs | Fora deste plano; não resolve verificação factual do workflow |
| [OmniRoute](https://github.com/diegosouzapw/OmniRoute) | Gateway com OAuth/API, fallback e compressão; software gratuito, provedor determina custo | Acrescenta servidor, tradução de protocolos, credenciais e políticas de roteamento | Não adicionar ao caminho padrão das CLIs autenticadas nativamente |
| [DeerFlow](https://github.com/bytedance/deer-flow) | Outro harness com sandbox, memória e subagentes; opções locais e providers CLI/OAuth documentadas | Pode evitar API paga em certas configurações, mas repete orquestração; infraestrutura maior | Reservar para produto de pesquisa/automações longas, não para melhorar estas três CLIs |
| [Headroom](https://github.com/headroomlabs-ai/headroom) | Biblioteca/proxy/MCP de compressão, também memória e aprendizagem | wrap pode instalar Serena globalmente; sobrepõe Graphify/CBM, troglodita e RTK | Não instalar junto com RTK; alternativa futura apenas se RTK deixar gargalo medido |

Não atribuir ganhos publicitários de tokens ao nosso fluxo: nenhum candidato foi
executado nesta auditoria. Licença aberta e suporte declarado não equivalem a
compatibilidade validada. Alguns projetos evoluem rapidamente: usar os SHAs
auditados para revisão e uma release verificada para instalação, nunca update cego.

## 3. Stack desejada: uma responsabilidade por componente

| Responsabilidade | Dono | Limite |
|---|---|---|
| Terminais, sessões, layout, retomada | Alethe | Não reescrever destinos de skills/MCP administrados por outro dono |
| Login e modelos | Cada CLI nativa | Sem gateway novo, sem conversão de login AGY em chave Gemini |
| Escopo e processo | ponytail + ECC orch-* | Preservar Gates 1/2 e usar a variante proporcional à tarefa |
| Comunicação | troglodita + instruções pessoais | Um formato, sem outro compressor de estilo |
| Navegação estrutural | Graphify | CBM explicitamente atualizado apenas quando fallback for necessário |
| Estado do projeto | MEX/tracker/handoff | Memória automática não substitui artefatos revisáveis |
| Memória histórica | claude-mem para consulta, captura conforme provedor disponível | Worker sem reinício; erro de allowance não é corrigido por instalar skills |
| Skills versionadas | Fonte comum; possível Skillfile após piloto | Nunca Skillfile + Kasetto + Alethe escrevendo o mesmo destino |
| Saída de comandos | RTK, se aprovado pelo teste | Saída bruta preservada; não comprimir resultados consumidos por scripts |
| Guardas de código | Hooks existentes + permissões nativas | Adaptadores explícitos por CLI, sem empilhar guardrails |

## 4. Sequência de implantação

Resultado da execução: curadoria aplicada; seis skills pessoais distribuídas nas
três CLIs; CBM registrado nas três; RTK promovido somente para pytest. Skillfile
não promovido após falha de atualização de fonte local; adotada a alternativa
manual com fonte comum e hashes prevista no plano. ClaudeHUD/MemoryTrim não
adicionados. As listas abaixo preservam o plano original; não representam um
checklist integralmente aprovado por testes, sobretudo Alethe e hooks automáticos.

### Fase 1 — resolver contexto e donos antes de instalar

Arquivos: ~/.codex/config.toml; ~/.claude/settings.json; ~/.agents/skills;
~/.gemini/config/config.json; instruções pessoais nos três caminhos já existentes;
política do projeto em .mex/ROUTER.md. Destinos AGY adicionais somente depois da
verificação da descoberta real descrita na fase 2.

- [ ] Fazer backup das configurações e hashes dos diretórios geridos; preservar
  permissões, autenticação, hooks e MCPs não relacionados. Não copiar segredos para Git.
- [ ] Consolidar Graphify Windows e medir-uso; revisar diff completo e referências
  relativas antes de escolher o único diretório descoberto por CLI. Não apagar originais.
- [ ] Retirar using-superpowers do acionamento global. Deixar ECC responsável pelo
  processo e pôr helpers sobrepostos de planejamento/TDD/review/branch sob demanda.
- [ ] Avaliar desativação do plugin codex@openai-codex SOMENTE dentro do Codex;
  preservar no Claude. Confirmar transferência/segunda opinião no Claude após isso.
  Não manter patch manual eterno no hooks.json de cache como solução principal.
- [ ] Curar seleção global e de projeto. Proposta auditável por entrada em
  `proposed-codex-profiles.json`: núcleo projetado de 24 entradas locais, incluindo
  seis de sistema, com 7.425 caracteres de descrição. GPT Tutor acrescenta
  python-patterns, python-testing, error-handling, regex-vs-llm-structured-text e pdf.
  Projeção, não medição após implantação; conectores/apps podem adicionar skills.
- [ ] No Claude, manter overrides seletivos e revisar as cinco skills científicas
  sem override: pubmed-database, uspto-database, gget, literature-review e
  scholar-evaluation. Destiná-las a projetos de pesquisa, sem declarar que nunca são usadas.
- [ ] Pacotes especializados ficam por projeto: Python/PDF no GPT Tutor; Docker,
  frontend, shadcn e web-design no T-ES2; documentos/planilhas/slides/segurança quando
  necessários. Não desabilitar capacidades de apps administradas pela plataforma
  sem confirmar o controle correspondente. Não copiar skills oficiais inteiras para reescrevê-las.
- [ ] Validar três inicializações novas, no terminal direto e dentro do Alethe.
  Ausência do aviso, catálogo esperado e capacidade de acionar os fluxos essenciais.
  Se persistir: atribuir descrições remanescentes por origem e reduzir só a seleção
  dessa origem. Não aumentar artificialmente a janela do modelo, nem cortar todas
  as descrições indiscriminadamente para esconder o problema.

**Aceite:** warning ausente no cenário de uso real; zero skill essencial perdida;
zero dono duplicado por fase; manter os 4 disabled já confirmados.
Perfis aqui são conjuntos propostos, NÃO uma promessa de flags nativas idênticas.
Evitar alternar configuração global em paralelo: núcleo pessoal estável e extras
locais por projeto. No Codex, verificar precedência dos overrides de projeto antes
de usá-los; no Claude, user-invocable-only é diferente de disabled.

### Fase 2 — confirmar portabilidade; piloto Skillfile

Nova pasta de laboratório proposta: C:/Users/Humberto/Documents/GitHub/agent-workflow-lab.
Fontes versionadas propostas: skills/, Skillfile, Skillfile.lock e matriz de destinos.
Não transferir o bundle ECC inteiro para esse diretório.

- [ ] Confirmar raízes descobertas por cada CLI com uma skill sentinela que apenas
  imprime um identificador. Para Codex, usar skills/list. Claude/AGY: /skills e uma
  invocação explícita. Não usar inferência paga adicional; as invocações consomem a
  quota normal das CLIs. Limpar a sentinela ao concluir o teste.
- [ ] Resolver divergência AGY: documentação atual aponta
  ~/.gemini/antigravity-cli/skills; esta instalação importou plugins em
  ~/.gemini/config/plugins. O target antigravity do Kasetto aponta para
  ~/.gemini/antigravity/skills. Nenhum desses caminhos pode ser escolhido por suposição.
- [ ] Verificar a versão Windows do Skillfile e fixar versão/hash. Pilotar apenas
  duas skills portáveis já existentes: troglodita e a medir-uso corrigida.
  Usar install-path se o target embutido não corresponder à descoberta AGY comprovada.
- [ ] Revisar `skillfile validate`, `skillfile status` e `skillfile diff` em destinos
  descartáveis. Instalar duas vezes: segunda aplicação deve produzir zero diferença.
  Testar patch local e atualização upstream conflitante sem perda silenciosa.
- [ ] Conferir arquivos e dependências, não só SKILL.md. Se um destino for link,
  testar antes: Skillfile documenta recusa de componentes de caminho com symlink.
- [ ] Abrir/fechar Alethe e reler hashes. Se reescrever o mesmo destino, não promover
  o gestor: primeiro corrigir/desativar esse escritor. Não construir um loop de
  sincronização para disputar a configuração.
- [ ] Traduzir agentes/hooks por capacidade real. Claude usa os agentes nativos
  do ECC; Codex precisa de papel suportado ou execução inline equivalente; AGY
  precisa confirmar agente importado. Não prometer /ecc:* ou tdd-guide pelo simples
  transporte de Markdown. Manter adaptadores de hook do GPT Tutor específicos.

**Aceite:** duas skills descobertas uma vez em cada CLI; referências funcionando;
idempotência; rollback completo; Alethe não causa drift; nada fora dos destinos
declarados alterado. Se falhar, manter fonte comum/manual e não instalar Kasetto
automaticamente. Kasetto é alternativa de desenho, não fallback de instalador.

### Fase 3 — piloto RTK, sem proxy de modelos

- [ ] Instalar binário Windows de release fixada/verificada somente no laboratório.
  Não executar rtk init global inicialmente, pois ele escreve hooks/instruções.
- [ ] Medir os mesmos comandos com e sem RTK: git status, git diff --stat,
  rg em símbolos reais, pytest passando e pytest falhando. Usar cópia descartável
  para o teste vermelho; não alterar testes vivos do GPT Tutor.
- [ ] Registrar bytes, tempo mediano de três repetições e exit code. Se houver
  tokenizer disponível, medir tokens; rtk gain é estimativa própria, não faturamento
  nem prova de economia de quota. Acrescentar custo das releituras do log bruto.
- [ ] Critérios propostos: preservar 100% dos exit codes e fatos necessários ao
  diagnóstico; reduzir ao menos 30% da saída nas tarefas verbosas escolhidas;
  acesso verificável à saída integral; nenhuma regressão na correção do agente.
- [ ] Claude/Codex: testar hook nativo numa configuração isolada somente depois
  do modo explícito. Confirmar payload real e ordem com os guards existentes;
  ferramentas nativas Read/Grep/Glob não passam pelo hook Bash do RTK.
- [ ] AGY: começar com rtk explícito via run_command. A regra Antigravity anunciada
  pelo RTK não prova interceptação transparente no AGY CLI. Não instalar o hook
  BeforeTool do Gemini CLI como se fosse AGY.

**Aceite:** promover apenas os comandos aprovados. Manter scripts/JSON, grep que
alimenta pipeline e avaliações de conteúdo exato no caminho bruto. Não combinar
RTK com Headroom/OmniRoute ou filtros paralelos. Em erro/omissão, desligar o wrapper
e recuperar saída bruta; não trocar o modelo para compensar.

### Fase 4 — aprendizagem e observabilidade, sem daemon novo

- [ ] Manter tracker/handoff como fallback enquanto claude-mem não grava por quota.
  Não reiniciar o worker nem adicionar outro observador automático para repetir a mesma captura.
- [ ] Ao encerrar trabalho relevante, usar o dono ECC existente para propor até três
  correções de skills com evidência, destino e revisão humana. Nenhuma edição
  automática de instruções globais. Reaproveita a ideia do task-observer sem adicionar
  mais uma skill permanente ou prometer memória infalível.
- [ ] ClaudeHUD só entra como teste de substituição da statusline atual. Comparar
  ganho de informação e latência dentro/fora do Alethe. Um statusLine ativo, rollback
  para ~/.claude/hooks/statusline.py. Não há equivalente a instalar nas outras duas CLIs.
- [ ] CodexMemoryTrim fica sem cron e sem limpeza até auditoria específica demonstrar
  memória obsoleta. Backup consistente do banco e compatibilidade da versão seriam
  pré-requisitos de qualquer futura exclusão; não usar contra o warning de skills.

### Fase 5 — adoção em projetos futuros

- [ ] Versionar seleção, versões fixadas, patches e destinos no repositório de
  workflow; autenticação e sessões permanecem pessoais e fora de Git.
- [ ] Novo projeto começa apenas com núcleo comum + instruções locais mínimas.
  Importar pacote de domínio somente quando a tarefa exigir, sem replicar todo o MEX
  do GPT Tutor nem instalar todas as skills do ECC.
- [ ] Atualização de qualquer bundle roda os mesmos gates: catálogo sem warning,
  diff de configuração revisado, descoberta por CLI, hooks únicos e rollback.
  Atualização manual deliberada; nenhum sincronizador altera cache vivo por trás.

## 5. Rollback e critério de parada

Antes de cada fase, backup próprio dos arquivos tocados e registro da versão.
Rollback restaura somente esses arquivos; não faz reset da árvore suja nem reinstala
todos os plugins. Remover apenas o hook/entrada introduzido na fase; preservar
os dados de memória e os bancos Graphify/CBM existentes.

Parar promoção se houver duplicata carregada, drift após abrir Alethe, mudança de
credenciais/modelo não pedida, perda de saída necessária, cobrança adicional
inesperada ou falha de restauração. Nenhuma stack garante ausência de erros futuros;
versionamento, um dono por destino e testes de atualização reduzem esse risco.

## Fontes e reprodução

- Alethe: https://github.com/Kc1t/alethe-agents e https://alethe-agents.kc1t.com/
- Skills Codex: https://learn.chatgpt.com/docs/build-skills
- AGY CLI: https://www.antigravity.google/docs/cli/plugins
- Fontes dos candidatos: links da tabela e SHAs em candidate-sources.json.
- Reproduzir inventário: Python311 em docs/reports/_workflow-audit-2026-09-15/audit.py.
- Reproduzir catálogo sem inferência: Python311 em list_codex_skills.py.
- Inventário não é auditoria de segurança dos projetos externos. Suporte documental
  ainda precisa dos testes Windows/AGY antes de adoção.
