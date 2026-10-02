# Workflow comum: Claude Code, Codex, AGY

Implantação aprovada em 15/09/2026. Fonte versionada com remoto privado `HumbertoCG18/agent-workflow-lab` (desde 23/09, cópia contra perda de disco); `private/` segue só local.
Fonte das seis skills pessoais em `skills/`; destinos e hashes em `deployed-skills.json`.
Papéis ECC para execução inline em `agents/`. Plugins ECC/ponytail/claude-mem continuam
sob seus gerenciadores nativos. Não copiar seus bundles para este repositório.

## Operação

Roteamento corrente: [workflow.md](workflow.md). Contrato do pesquisador:
[agents/agy-researcher.md](agents/agy-researcher.md), usado inline no AGY.
Não modificar bundles ECC para adaptar um único projeto.

1. Rodar `python verify.py` antes/depois de atualizar plugins ou abrir novas sessões no Alethe.
2. Para revisar catálogo Codex sem inferência, rodar `python catalog.py`.
3. Para testar CBM nas três configurações sem indexação/inferência, rodar `python probe_mcp.py`.
4. Para pytest, usar `rtk pytest <args>` no ambiente do projeto; recuperar detalhes
   com `rtk recall <hash> --full`. Outros comandos continuam brutos.

`private/` contém backups e logs locais, inclusive configurações: nunca versionar.
`phase1.py` registra a migração histórica e recusa repetição após a implantação.
Os comandos de validação não removem skills, não atualizam índices e não chamam modelos.
`benchmark_rtk.py` é um experimento isolado e deixa os logs completos em private/.

## Responsabilidades

| Componente | Dono / regra |
|---|---|
| Sessões e terminais | Alethe; não importar novamente os mesmos destinos |
| Processo | ECC; papéis nativos quando disponíveis, inline quando não |
| Skills pessoais | Fontes deste diretório; distribuição manual revisada, hashes conferidos |
| MCPs | Configuração nativa de cada CLI; CBM fallback, sem watcher/indexação automática |
| Saída pytest | RTK 0.49.0, executável local, sem hooks automáticos |
| Estado do projeto | Tracker/handoff do próprio projeto |

## Pilotos e limites

- Skillfile 1.9.1 está somente em bin/ para reprodução. `Skillfile.pilot` não é
  manifesto de produção. Segunda instalação foi idempotente, mas atualização de
  fonte local não substituiu destino AGY existente. `diff` não suporta entrada local.
  Portanto, lock/patch/conflito remoto não foram promovidos como solução para estas fontes.
- RTK foi adotado somente para pytest: dois cenários sintéticos, três repetições
  por braço, exit codes e sentinelas preservados, recall da falha recuperado.
  Não extrapolar para todos os testes/projetos, qualidade de diagnóstico autônomo ou quota.
- `rtk grep` falhou por ausência de grep; `rtk rg` existe, mas não foi promovido.
- AGY reconhece seis skills pessoais uma vez cada. MCP está habilitado e o transporte
  respondeu; uso headless pelo agente exige permissão normal para MCP. Nenhuma
  permissão global foi ampliada por esta implantação.
- Codex: núcleo pessoal de 24 entradas; GPT Tutor declara sete extras. Arrays de
  configuração são substituídos: o projeto contém a seleção completa, não só acréscimos.
- Catálogo de apps/conectores da aplicação pode diferir do CLI. Reabertura pelo
  Alethe ainda precisa da confirmação do usuário; sessões diretas passaram 3/3.

## Atualização e rollback

Antes de modificar uma fonte, comparar destino com o hash registrado. Havendo drift,
revisar/mesclar primeiro; nunca sobrescrever automaticamente. Copiar apenas o arquivo
revisado aos destinos enumerados e atualizar seus hashes no manifesto. Rodar verify.py.
Atualizações de plugins exigem nova leitura do catálogo: caminhos de cache contêm versão.

Backups por execução ficam em private/<timestamp>/, com changes.json quando escritos
pelo helper. As antigas entradas learned/medir-uso foram movidas para archived/ no
backup correspondente. Restaurar só os arquivos da fase em ordem inversa, revisando
mudanças posteriores; nunca restaurar .claude.json inteiro às cegas, pois guarda
estado mutável de sessões. Não executar reset do GPT Tutor.

Projetos futuros começam com núcleo global. Adicionar apenas skills de domínio
necessárias e validar na CLI real; não copiar a configuração GPT Tutor inteira,
que referencia o grafo e os caminhos locais deste projeto.

## Delegação e continuidade

[workflow.md](workflow.md) contém a autorização de uma escalada automática por tarefa.
[task-state.template.md](task-state.template.md) define o estado persistente por worktree.
[personal-instructions.md](personal-instructions.md) é a cópia versionada das instruções
pessoais instaladas, sem credenciais. [agents/README.md](agents/README.md) explica a
portabilidade inline. No GPT Tutor, distribuir o snapshot .workflow/ entre branches.
Comparação Fable/Astra e aceite Alethe continuam pendentes; não são checks de verify.py.
