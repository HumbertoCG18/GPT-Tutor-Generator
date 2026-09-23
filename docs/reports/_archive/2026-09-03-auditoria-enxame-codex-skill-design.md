# Auditoria-enxame como skill nativa do Codex

**Data:** 2026-09-03
**Status:** aprovado para plano
**Fonte funcional:** `.claude/workflows/auditoria-enxame.js`

## Objetivo

Portar para o Codex o comportamento observável da auditoria-enxame usada no Claude
Code: uma auditoria profunda, somente leitura, dividida em sete dimensões independentes,
com verificação adversarial de cada achado sério e síntese final priorizada.

O port é uma skill específica deste repositório. Ele não depende do runtime de workflows
do Claude, não chama modelos Claude e não congela no texto números de testes, estado de
campanha, caminhos absolutos ou nomes de modelos.

## Entregáveis previstos

```text
.agents/skills/auditoria-enxame/
├── SKILL.md
└── references/
    ├── dimensions.md
    └── report-contract.md
```

- `SKILL.md`: gatilhos, invariantes e orquestração.
- `references/dimensions.md`: contrato das sete varreduras e critérios de evidência.
- `references/report-contract.md`: formato dos achados, vereditos e relatório final.

Não haverá script de implementação. A orquestração usará as ferramentas nativas de
colaboração do Codex, e os comandos de inspeção continuarão determinados pelo contexto
do projeto.

## Gatilhos e limites

A skill será carregada quando o usuário pedir explicitamente uma auditoria-enxame,
varredura profunda do repositório ou auditoria combinada de código morto, duplicação,
performance, campos não consumidos, legado, testes e robustez.

Ela não será acionada para uma revisão comum de um diff, diagnóstico de um bug isolado
ou pedido de implementação. A execução pode consumir muitos agentes e tempo, portanto
o disparo precisa ser explícito.

## Contexto fresco

Antes de distribuir trabalho, o coordenador:

1. lê as instruções vigentes em `.mex/ROUTER.md` e `.mex/AGENTS.md`;
2. consulta `graphify-out/graph.json` por `graphify query` quando disponível;
3. lê o tracker e o handoff vivo apontados pelo ROUTER somente quando uma dimensão
   depender do estado atual de campanha;
4. registra branch, commit e estado do worktree com comandos Git somente leitura;
5. descobre testes, módulos e caminhos no filesystem atual.

Assim, a skill não repete a contagem antiga de testes nem descreve como atuais sistemas
que já foram removidos. O diretório de trabalho, e não um caminho de usuário embutido,
define a raiz auditada.

## Orquestração

### Fase 1: varrer

O coordenador cria sete trabalhos logicamente paralelos:

1. código morto;
2. duplicação e reinvenção;
3. performance em caminhos quentes;
4. campos produzidos mas não consumidos;
5. mapa de legado e risco de cutover;
6. saúde, cobertura e duração dos testes;
7. robustez e falhas silenciosas.

Cada trabalho recebe contexto isolado, escopo de somente leitura e o mesmo contrato de
saída. Os sete trabalhos são independentes, mas o scheduler respeita o limite de agentes
do runtime. Com quatro slots totais, por exemplo, o coordenador executa até três filhos
simultâneos e alimenta novas dimensões conforme slots liberam. “Sete agentes” significa
sete responsabilidades independentes, não a promessa de sete processos simultâneos.

Os agentes de varredura usam um modelo de trabalho permitido pelo `spawn_agent` atual,
com modelo e esforço definidos explicitamente na chamada. A skill escolhe em runtime e
registra a escolha, sem persistir nomes de modelos que possam ficar obsoletos.

### Fase 2: verificar adversarialmente

Para cada achado de severidade alta ou média, limitado aos seis mais fortes por dimensão,
o coordenador cria uma verificação independente. O verificador tenta refutar o achado,
procura consumidores ou proteções ignorados, confere as linhas citadas e devolve um dos
vereditos:

- `confirmado`;
- `refutado`;
- `não verificável`, com a evidência que faltou.

Cada achado recebe seu próprio veredito. As verificações também rodam em ondas limitadas
pelos slots disponíveis. Falha ou timeout de um verificador não transforma o achado em
confirmado.

### Fase 3: sintetizar

O agente raiz, no modelo ativo da sessão, combina:

- achados altos e médios confirmados;
- achados baixos, claramente marcados como não submetidos à segunda fase;
- achados refutados;
- dimensões ou verificações incompletas.

A síntese não é delegada a um modelo Claude equivalente ao Fable. A qualidade vem do
contrato de evidência, da verificação adversarial e do modelo Codex ativo.

## Contrato de evidência

Todo achado da primeira fase contém:

| Campo | Regra |
|---|---|
| `dimensão` | uma das sete dimensões fechadas |
| `título` | afirmação curta e falsificável |
| `local` | caminho relativo e linha ou símbolo atual |
| `evidência` | chamadas, medições ou busca que sustentam a afirmação |
| `severidade` | `alta`, `media` ou `baixa` |
| `ação` | correção ou decisão concreta sugerida |

O veredito acrescenta `status` e `razão`. Evidência sem localização atual, inferência
apresentada como fato ou achado duplicado entre dimensões não entra como confirmado.

## Contrato do relatório

O resultado padrão é devolvido na conversa, sem gravar arquivos. Ele contém, nesta ordem:

1. escopo auditado, commit e eventuais lacunas;
2. placar por severidade e status;
3. achados confirmados ordenados por severidade e impacto;
4. quick wins;
5. mudanças estruturais;
6. riscos de cutover que devem apenas ser registrados;
7. achados refutados;
8. dimensões ou verificações incompletas;
9. ordem de ação sugerida.

Persistir o relatório em `docs/reports/` exige pedido explícito do usuário, pois é uma
mutação fora do modo padrão somente leitura.

## Invariante de somente leitura

Durante a auditoria, nenhum agente pode:

- editar código, documentação, configuração ou artefatos;
- reprocessar ou reconstruir repositórios-tutor;
- executar comandos Git que alterem índice, branch, commits ou remotes;
- instalar ou atualizar dependências;
- tratar uma sugestão como autorização para corrigir.

São permitidos leitura, `rg`, consultas Graphify, inspeção Git e Python de diagnóstico.
Quando a dimensão de testes executar pytest, ela usa `python -B`, desabilita o cache do
pytest e mantém temporários fora da árvore auditada. Testes conhecidos por alterar dados
reais ou serviços externos são apenas descritos, a menos que o usuário os autorize.

O coordenador compara o estado do worktree antes e depois. Mudança inesperada encerra a
auditoria com o incidente visível e sem alegação de conclusão limpa.

## Falhas parciais

- Um finder pode ser repetido uma vez após erro transitório.
- Uma dimensão que continuar falhando aparece como `incompleta`, com o motivo.
- Uma verificação ausente deixa o achado como `não verificável`.
- O relatório nunca converte ausência de evidência em “nenhum problema encontrado”.
- Se colaboração multiagente não estiver disponível, a skill para e informa o requisito;
  ela não simula silenciosamente uma auditoria-enxame sequencial do agente raiz.

## Estratégia de validação da skill

A implementação seguirá TDD para skills:

### RED

Executar cenários de pressão sem a nova skill e registrar falhas observadas, cobrindo pelo
menos:

1. pedido de auditoria com pressão para corrigir imediatamente;
2. finder que falha no meio da execução;
3. achado sério plausível, mas refutável por um consumidor indireto;
4. worktree já sujo antes da auditoria.

O baseline precisa demonstrar pelo menos uma falha real antes de `SKILL.md` ser criado.

### GREEN

Criar a menor skill que faça os mesmos cenários respeitarem:

- sete dimensões presentes;
- zero edição durante a auditoria;
- veredito independente para todo achado alto ou médio selecionado;
- falhas parciais explicitadas;
- relatório no formato definido.

### REFACTOR e gates

1. fechar racionalizações descobertas nos testes e repetir os cenários;
2. validar a estrutura com `quick_validate.py`;
3. confirmar descoberta pelos gatilhos da descrição;
4. comparar hashes e `git status --short` antes/depois de uma execução controlada;
5. conferir manualmente que todos os achados sérios do fixture têm veredito;
6. testar com os modelos Codex que serão usados como finder e verificador.

## Critérios de aceite

- A skill é descoberta por pedidos explícitos de auditoria-enxame.
- As sete dimensões do workflow Claude continuam representadas.
- O limite de concorrência do Codex é respeitado sem omitir dimensões.
- Até seis achados altos/médios por dimensão recebem verificação individual.
- Nenhum achado não verificado é apresentado como confirmado.
- O relatório diferencia confirmado, refutado, não verificável e incompleto.
- Uma execução padrão não altera o worktree nem dados externos.
- Não há caminho absoluto, contagem de testes, campanha ou modelo Claude congelado.
- A skill e suas referências passam na validação estrutural e nos cenários RED/GREEN.

## Fora de escopo

- Corrigir os achados da auditoria.
- Substituir ou remover `.claude/workflows/auditoria-enxame.js`.
- Importar conversas do Claude Code.
- Criar o protocolo de revisão do trabalho do Codex pelo Claude após o reset do limite.
  Esse handoff é uma segunda capacidade e terá desenho próprio depois deste port.
