# P1 — avaliação congelada concluída em 02/10/2026

**P1 e A+P1 passaram, separadamente, os critérios congelados contra a base.** Subunidade primária: **86/251 → 87/251 (+1, zero perda por ID)**; bloco **223/237** e unidade **249/284** invariantes. Nenhum curso regrediu. **Integração e commit não autorizados; P1 continua desligado por padrão no produto.**

Contrato v2 §5, SHA256 d30980a3347c9866bbe2a11860310e33497d6b26a2330b408294a6600fa2e3d3, preservado. A execução técnica2 foi autorizada explicitamente após a interrupção da tentativa1. Mesma Thread/worktree isolada job-31, run-16, Claude Opus5.5/high observado; nenhuma nova revisão. Revisor job-30 e contador1 preservados. Nenhum ajuste de regra, divisor, limiar, propagação ou escopo.

## Resultado dos quatro braços

| braço | bloco | unidade | subunidade primária | subunidade aceita | resultado contra base |
|---|---:|---:|---:|---:|---|
| base |223/237|249/284|86/251|109/251|controle anterior, e024d396…|
| A: só acentos |223/237|249/284|85/251|108/251|reprovação anterior, −1|
| P1 |223/237|249/284|87/251|110/251|+1 ganho,0 perdas: passa|
| A+P1 |223/237|249/284|87/251|110/251|+1 ganho,0 perdas: passa|

Controles base/A reutilizados por hash, não reexecutados. Cada braço preserva350IDs; denominadores de pontuação continuam237/284/251. Novos replays P1,A+P1 e A+P1-desligado concluídos em aproximadamente279–280s, em processos independentes. A+P1 desligado reproduziu o controle A em **350/350**, nos três eixos.

O ganho comum contra a base é **TCC `aula-09-variacoes-de-maquinas-de-turing`**. P1 muda2IDs de subunidade (o ganho e SO `2306-laminas-gerencia-de-arquivos`, neutro). A+P1 muda7IDs de subunidade contra base; seis mudanças são neutras no placar. Zero diferenças de bloco/unidade porID contra o respectivo braço semP1, e zero perdas nos eixos pontuados. Nenhum curso regrediu.

Contraste adicional **A+P1 vs A: +2/−0 na primária e aceita**, conferido porID a partir dos ganhos/perdas registrados contra a mesma base: aula-09 e TCC `aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis-pdf`. O combinado restaura a perda antiga de A na aula-10. Esse resultado contraria a expectativa descritiva anterior do contrato; o desenho não foi alterado para produzi-lo. O aceite do combinado decorre de **+1 contra a base**, não de melhorar só sobre A.

## Grupos e limites

| grupo | base primária | A primária | P1 primária | A+P1 primária |
|---|---:|---:|---:|---:|
| desenvolvimento:MF/SO/IA/ES2/TCC|50/151|49/151|51/151|51/151|
| CG/FR:descritivos,expostos|36/100|36/100|36/100|36/100|
| independente|nenhum curso|nenhum curso|nenhum curso|nenhum curso|

Por curso, primária nos candidatos:MF25/58,SO7/15,IA4/39,ES2 7/28,TCC8/11,CG30/82,FR6/18. Só TCC ganha contra base (7/11→8/11). Desenvolvimento:bloco190/202 e unidade175/191, inalterados; CG/FR:bloco33/35 e unidade74/93, inalterados. FR não tem denominador de bloco/unidade nesse placar; não interpretar ausência como zero acertos.

O efeito observado é **um material, num único curso de desenvolvimento**. CG/FR já influenciaram desenvolvimento e são somente descritivos. Os sete cursos não demonstram generalização independente; não há resultado em curso novo.

## Identidade, congelamento e suíte

- Três manifests completos anteriores ao scoring,zeroABORT,350IDs em cada um,`src_fora` vazio e hashes dos módulos carregados iguais aos esperados. Paths+SHA256 foram gravados pelo próprio processo; o coordenador conferiu os arquivos, as decisões e seus hashes. Decisões anteriores ao gold iguais aos JSONs finais; asserts pós-gold passaram. Gold usado apenas pelo scoring.
- P1: index28894d0a…,file_map6ad4f70b…,normalize base d0ce2309…; combinado: mesmo index/file_map,normalize A f5b9581a…. Produto/testeoriginais preservados; teste P1 90746e83….
- Evidências anteriores mantidas sem repetição:P1 desligado350/350,mutação detectada,suíte P1 **2461 aprovados,4 pulados,2 falhas preexistentes**.
- Suíte combinada final,Python3.11.9: **2469 aprovados,4 pulados,1 falha preexistente**,62,73s. Falha: `tests/test_caracterizacao_blocos_atual.py::test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor]`, já presente na baseline. **Nenhuma falha nova.** A outra falha antiga de ActualText não reapareceu; não atribuir isso a correção do produto.
- Coleta comparável demonstrada:todos os **2467 IDs de teste** anteriores presentes,mais7testes de acentos, total **2474**. Os14testes P1 também passaram dentro da suíte combinada. Nenhum teste novo foi escrito nesta retomada.

O primeiro comando da suíte combinada falhou na coleta por fixtures ausentes; o executor sobrescreveu seu log e transcreveu a causa/comando no relatório parcial. Após montagem, a suíte2442/4skip não era suficiente:ausência de descoberta dos tutores substituía32casos por4NOTSET. O coordenador confirmou os IDs e executou a suíte comparável com `TUTOR_REPOS` explícito, preservando o log2442 e registrando a nova saída separadamente. Não houve rebuild nem alteração dos tutores/golden snapshots.

Limitação preservada do runner: a barreira pode contar arquivoABORT como manifest e não checar ABORT após o while. Os processos já estavam iniciados; nenhum foi relançado nem alterado em voo. **Nesta execução havia exatamente3manifests válidos e zeroABORT**, conferidos, portanto o defeito não foi exercido. Corrigir a guarda antes de reutilizar o runner em outra automação; essa limitação não autoriza repetição desta avaliação.

## Arquivos e evidência

Artefatos na worktree isolada:
`C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-p1/.alethe/worktrees/job-31/docs/reports/2026-10-02-p1-avaliacao/tentativa2/`

| arquivo/superfície | conteúdo |
|---|---|
| `replay_t2.py`, `consolida2.py` | adaptação operacional do replay e comparação dos braços;nenhuma regra nova |
| `esperado_p1.json`, `esperado_ap1.json` | hashes esperados dos três módulos |
| `barreira/p1.json`, `ap1.json`, `ap1_desligado.json` | decisões congeladas e identidade no próprio processo |
| `replay_p1.json`, `replay_ap1.json`, `replay_ap1_desligado.json` | três resultados integrais novos |
| `consolidado2.json`, `verificacao-coordenador.json` | placares,flags,contrasteporID,grupos,asserts e hashes |
| `log_p1.txt`, `log_ap1.txt`, `log_ap1_desligado.txt` | logs integrais da execução2 |
| `suite_ap1.txt`, `suite_ap1_comparavel.txt`, `coleta_*.txt` | execução preliminar2442 e finalcomparável2469;manifests de coleta |
| `arvore_suite_ap1/` | montagem descartável da suíte,sem alterar testes de produto;test_text_normalize da cru05 e teste P1 existentes |
| `relatorio-tentativa2.md` | relatório do executor,com complementação do coordenador |

Na worktree P1 original:este relatório,plano de retomada e estados; nenhuma alteração nova de produto. Na principal:somente registro/estado e trecho da campanha no tracker. Tentativa1 e seus logs/telemetria preservados. Nenhuma integração,commit,push,merge,nova revisão,#42/scheduler,suspensão,rebuild ou chamadaLLMdo motor.

## Posição da campanha e próximo Gate

**MOTOR permanece2/10 concluídas(20%).** A fase de avaliação de MOTOR-01 está concluída tecnicamente; a tarefa aguarda Gate próprio de escolha/integração e não foi contada como entrega integrada. MOTOR-02(acento sozinho,reprovado) e MOTOR-03(sinalnulo) seguem encerradas; demais tarefas preservadas.

Se um candidato for integrado, o placar observado será223/237 bloco(94,1%),249/284 unidade(87,7%) e87/251primária(34,7%):faltam **+7 em unidade** e **+139 em primária** para superar90% com esses denominadores. **A referência vigente continua223/249/86** até integração e decisão própria; não atualizar baseline com o candidato silenciosamente.

Escolha posterior do usuário: **A+P1**, pela correção textual incorporada; sem superioridade de acurácia demonstrada sobre P1. Próximo Gate: autorizar o [plano de integração/ativação conjunta](plano-integracao-acentos-p1.md), com reversão conjunta e preservação das referências 86/87. Escolha não concede o Gate. Commit continua condicionado a autorização própria. Não abrir variante,redesenho ou nova avaliação nesta tentativa.
