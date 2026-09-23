# Contrato de qualidade da primeira fatia web C6

Issue #14. Escopo aprovado: documentação; ativação acompanha a primeira fatia vertical
web em issue própria. Nenhum gate web está implementado por este documento.

## Fronteiras e contrato

O motor Python mantém regras de atribuição, persistência e geração. A interface web
consome transporte versionado; não importa Tkinter nem reimplementa regras do motor.
Adaptadores ficam na borda Python. Transporte, framework, runtime e gerenciador serão
escolhidos no Gate 1 da fatia; a primeira superfície é um painel local de leitura.

DTOs e eventos devem ter uma fonte única: modelos Python de fronteira com exportação
JSON Schema (Pydantic é candidato, não dependência aprovada). Tipos do cliente derivam
do schema; evitar duas definições manuais. O contrato versiona campos, nulabilidade,
erros sanitizados, identificador da operação e estados terminais. Total desconhecido
não vira percentual. Eventos incluem ordenação para rejeitar atualização obsoleta.

Verificar produtor e consumidor com a mesma fixture revisada: resposta válida, vazio,
erro, versão incompatível e campos opcionais. Teste de arquitetura deve falhar se UI
importar Tkinter, acessar persistência diretamente ou duplicar entrada do motor. O
formato efetivo e a compatibilidade retroativa serão aceitos junto do primeiro schema.

## Decisões de ferramentas

| Capacidade | Decisão | Condição verificável para ativar |
|---|---|---|
| Lint/formato web | Biome preferido; versão por definir | pacote web e arquivos suportados presentes; configuração e comando no CI |
| Fronteiras TS | ArchContract candidato | camadas TS concretas; violação deliberada precisa falhar |
| Código sem uso | Knip consultivo primeiro | rotas/build estáveis; confirmar usos dinâmicos antes de bloquear/remover |
| Commits | Conventional Commits; commitlint adiado | estratégia de merge exigir validação de cada commit, não apenas título do PR |
| Mutação | Stryker adiado | regra crítica e suíte rápida; piloto medido antes de limite obrigatório |
| Cobertura | relatório local + baseline/ratchet | runner escolhido; nenhuma regressão do limite no mesmo PR |
| Upload de cobertura | Codecov opcional | aprovação de destino, dados, permissões e política de upload |
| E2E | Playwright planejado | aplicação executável; jornada real no browser, não apenas mocks |

Sem Node ou ferramentas web adicionados ao runtime Python para satisfazer esta lista.
O check Python `core` continua independente e obrigatório.

## Aceite da primeira fatia

1. Fixar stack, versões, lockfile, comandos de desenvolvimento/build/teste e contrato
   versionado. Testes de integração exercitam o adaptador com motor Python e dados
   sintéticos/revisados; sem LLM ou serviços pagos na validação padrão.
2. Cobrir idle, loading, empty, success e error; simular lentidão, falha e retorno
   obsoleto. Operações longas futuras também cobrem cancelamento e repetição sem
   submissão duplicada. E2E verifica teclado, foco, nomes acessíveis e movimento
   reduzido. Skeleton só para conteúdo assíncrono previsível; lazy loading só para
   recurso pesado não essencial ao primeiro uso.
3. Medir inicialização, tamanho transferido, tempo até conteúdo útil e resposta da
   interação principal numa fixture e máquina identificadas. Registrar ao menos
   cinco execuções, mediana e máximo, cache frio/quente separados. Antes de merge,
   aprovar limites numéricos a partir do baseline e automatizar o orçamento; nenhum
   número de desempenho está medido ou aprovado neste documento.
4. CI com permissões mínimas, build reproduzível, unitários, integração, arquitetura,
   lint, cobertura e E2E aplicáveis. Um controle negativo deve provar que cada gate
   obrigatório bloqueia o PR. Check ausente, pulado ou infraestrutura falha não é verde.
5. Artefato associado ao SHA e PR; smoke de inicialização, leitura e erro sanitizado.
   Documentar e ensaiar rollback para o artefato anterior. Mudança de dados exige
   compatibilidade/backup. Merge, release e deploy mantêm autorizações próprias.

## Observabilidade e evidências

Responder localmente: qual operação falhou, quanto demorou e qual resultado terminou.
Propagar o ID da operação pelo transporte; não enviar material acadêmico, prompts,
credenciais ou caminhos privados nos logs do browser. Exportação externa continua
dependente de destino e aprovação. Indisponibilidade do coletor não bloqueia uso.

O PR da fatia anexa comandos, resultados, cobertura, baseline de desempenho,
capturas normal/reduced-motion e resultado do rollback. Referências de ferramentas
e requisitos gerais ficam em `.mex/patterns/engenharia-produto.md`; esta especificação
define aceite, não comprova adoção ou funcionamento das ferramentas candidatas.

## Fechamento

#14 entrega o contrato documental. A issue de ativação [#41](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/41) permanece aberta até os gates
executarem na primeira fatia. Não fechar a ativação apenas por adicionar arquivos de
configuração. Rollback desta entrega: revert do PR documental.
