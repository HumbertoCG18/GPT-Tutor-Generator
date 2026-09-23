# W-Y (#52) — tipo de bloco decidido por linha (prototipo)

HEAD 493119e; decisoes sha256 `b9b21711ec5d8fce3c931d5ef247a5de33ceb523c02e1a47e86e455fc87e0c77`; resultado sha256 `d590f17bed1f0d8590cd7cac86b3c196c917cd87fd291e65063fe182a9a8b0ca`.
Script `wy_kind_por_linha_22-09.py` (patch so em memoria). P0 = regras do brief; P1 = P0 + ajustes:

- P1a: Atividade 'prova de substituicao' = makeup (senao 'prova' do ATIVIDADE_KIND_MAP vira assessment)
- P1b: marcador suspension/event e metadado de periodo; rotulo nao-class decide ('Feriado {kind=suspension}' = holiday)
- P1c: g2/ps com rotulo vazio = o marcador decide (assessment/makeup, como hoje)
- P1d: adjacencia de duvidas/plantao pula outra linha de duvidas/plantao (cadeia antes da prova)

## A. Totais (8 cursos vivos)

| contagem | academic_event | assessment | class | deliverable | event | g2 | holiday | makeup | office_hours | overview | ps | reserved | results | review | suspended | suspension | workshop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linha_atual | 0 | 16 | 184 | 29 | 8 | 11 | 1 | 0 | 0 | 0 | 6 | 2 | 2 | 0 | 0 | 16 | 0 |
| linha_P0 | 8 | 28 | 166 | 29 | 0 | 0 | 2 | 0 | 4 | 6 | 0 | 2 | 1 | 13 | 15 | 0 | 1 |
| linha_P1 | 8 | 25 | 162 | 29 | 0 | 0 | 13 | 7 | 3 | 6 | 0 | 2 | 1 | 14 | 4 | 0 | 1 |
| bloco_vivo | 8 | 27 | 91 | 29 | 0 | 0 | 13 | 6 | 9 | 4 | 0 | 2 | 2 | 4 | 4 | 0 | 1 |
| bloco_controle | 8 | 27 | 91 | 29 | 0 | 0 | 13 | 6 | 9 | 4 | 0 | 2 | 2 | 4 | 4 | 0 | 1 |
| bloco_P0 | 8 | 28 | 93 | 29 | 0 | 0 | 2 | 0 | 4 | 6 | 0 | 2 | 1 | 11 | 15 | 0 | 1 |
| bloco_P1 | 8 | 25 | 89 | 29 | 0 | 0 | 13 | 7 | 3 | 6 | 0 | 2 | 1 | 12 | 4 | 0 | 1 |

Por curso (blocos controle -> P0 -> P1):

- CG: {'academic_event': 2, 'assessment': 4, 'class': 15, 'deliverable': 2, 'holiday': 1, 'office_hours': 5} -> {'academic_event': 2, 'assessment': 4, 'class': 15, 'deliverable': 2, 'holiday': 1, 'office_hours': 2, 'review': 3} -> {'academic_event': 2, 'assessment': 3, 'class': 15, 'deliverable': 2, 'holiday': 1, 'makeup': 1, 'office_hours': 2, 'review': 3}
- ES2: {'assessment': 3, 'class': 8, 'holiday': 2, 'makeup': 1, 'suspended': 1} -> {'assessment': 4, 'class': 8, 'suspended': 3} -> {'assessment': 3, 'class': 8, 'holiday': 2, 'makeup': 1, 'suspended': 1}
- FR: {'academic_event': 3, 'assessment': 4, 'class': 16, 'deliverable': 3, 'holiday': 1, 'makeup': 1, 'office_hours': 1, 'reserved': 1} -> {'academic_event': 3, 'assessment': 4, 'class': 16, 'deliverable': 3, 'overview': 1, 'reserved': 1, 'review': 1, 'suspended': 1} -> {'academic_event': 3, 'assessment': 4, 'class': 15, 'deliverable': 3, 'holiday': 1, 'makeup': 1, 'overview': 1, 'reserved': 1, 'review': 1}
- IA: {'academic_event': 1, 'assessment': 4, 'class': 9, 'deliverable': 3, 'holiday': 1, 'makeup': 1, 'office_hours': 1, 'overview': 2, 'results': 1, 'suspended': 1} -> {'academic_event': 1, 'assessment': 4, 'class': 11, 'deliverable': 3, 'holiday': 1, 'office_hours': 1, 'overview': 1, 'review': 1, 'suspended': 1} -> {'academic_event': 1, 'assessment': 4, 'class': 10, 'deliverable': 3, 'holiday': 1, 'makeup': 1, 'office_hours': 1, 'overview': 1, 'review': 1, 'suspended': 1}
- LR: {'assessment': 1, 'class': 5, 'deliverable': 8, 'holiday': 3} -> {'class': 5, 'deliverable': 8, 'overview': 1, 'suspended': 3} -> {'assessment': 1, 'class': 4, 'deliverable': 8, 'holiday': 3, 'overview': 1}
- MF: {'academic_event': 1, 'assessment': 3, 'class': 12, 'deliverable': 1, 'makeup': 1, 'results': 1, 'review': 2, 'suspended': 2} -> {'academic_event': 1, 'assessment': 4, 'class': 11, 'deliverable': 1, 'overview': 1, 'results': 1, 'review': 2, 'suspended': 2} -> {'academic_event': 1, 'assessment': 3, 'class': 11, 'deliverable': 1, 'makeup': 1, 'overview': 1, 'results': 1, 'review': 2, 'suspended': 2}
- SO: {'assessment': 4, 'class': 10, 'deliverable': 4, 'holiday': 3, 'makeup': 1, 'office_hours': 2, 'overview': 2, 'reserved': 1} -> {'assessment': 4, 'class': 11, 'deliverable': 4, 'office_hours': 1, 'overview': 2, 'reserved': 1, 'review': 1, 'suspended': 3} -> {'assessment': 4, 'class': 10, 'deliverable': 4, 'holiday': 3, 'makeup': 1, 'overview': 2, 'reserved': 1, 'review': 2}
- TCC: {'academic_event': 1, 'assessment': 4, 'class': 16, 'deliverable': 8, 'holiday': 2, 'makeup': 1, 'review': 2, 'workshop': 1} -> {'academic_event': 1, 'assessment': 4, 'class': 16, 'deliverable': 8, 'review': 3, 'suspended': 2, 'workshop': 1} -> {'academic_event': 1, 'assessment': 3, 'class': 16, 'deliverable': 8, 'holiday': 2, 'makeup': 1, 'review': 3, 'workshop': 1}

### Casos-alvo e legitimos (tipo do bloco vivo -> P0 | P1, por linha)

- alvo:FR-introducao-ao-roteamento: {'class->class|class': 1}
- alvo:IA-ml-introducao: {'overview->class|class': 1}
- alvo:TCC-atendimento-g2: {'assessment->review|review': 1}
- alvo:TCC-oficina: {'deliverable->deliverable|deliverable': 5, 'workshop->workshop|workshop': 1}
- alvo:duvidas-office_hours: {'office_hours->office_hours|office_hours': 3, 'office_hours->office_hours|review': 1, 'office_hours->review|review': 5}
- legitimo:feriado/suspensao: {'holiday->holiday|holiday': 2, 'holiday->suspended|holiday': 11, 'suspended->suspended|suspended': 4}
- legitimo:overview: {'overview->overview|overview': 3}
- legitimo:revisao: {'review->review|review': 4}

### Linhas cujo tipo muda (linha P0, bloco P0 ou bloco P1) + alvos

| curso | L | data | rotulo | Atividade | marc | linha atual | bloco vivo | bloco controle | linha P0 | regra P0 | bloco P0 | linha P1 | regra P1 | bloco P1 | caso |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CG | 14 | 22/09/2026 | Aula de dúvidas | Aula |  | class | bloco-09=office_hours | bloco-09=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-09=review | review | 4:office_hours>review(proxima=assessment) | bloco-09=review | alvo:duvidas-office_hours |
| CG | 16 | 29/09/2026 | Aula de dúvidas | Aula |  | class | bloco-11=office_hours | bloco-11=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-11=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-11=office_hours | alvo:duvidas-office_hours |
| CG | 22 | 20/10/2026 | Semana Acadêmica | Evento Acadêmico |  | event | bloco-16=academic_event | bloco-16=academic_event | academic_event | 2:atividade=evento | bloco-16=academic_event | academic_event | 2:atividade=evento | bloco-16=academic_event |  |
| CG | 23 | 22/10/2026 | Semana Acadêmica | Evento Acadêmico |  | event | bloco-17=academic_event | bloco-17=academic_event | academic_event | 2:atividade=evento | bloco-17=academic_event | academic_event | 2:atividade=evento | bloco-17=academic_event |  |
| CG | 30 | 17/11/2026 | Aula de dúvidas | Aula |  | class | bloco-22=office_hours | bloco-22=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-22=review | review | 4:office_hours>review(proxima=assessment) | bloco-22=review | alvo:duvidas-office_hours |
| CG | 32 | 24/11/2026 | Prova PS | Prova de Substituição |  | assessment | bloco-24=assessment | bloco-24=assessment | assessment | 2:atividade=prova | bloco-24=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-24=makeup |  |
| CG | 33 | 26/11/2026 | Aula de dúvidas | Aula |  | class | bloco-25=office_hours | bloco-25=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-25=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-25=office_hours | alvo:duvidas-office_hours |
| CG | 35 | 03/12/2026 | Aula de dúvidas | Aula |  | class | bloco-27=office_hours | bloco-27=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-27=review | review | 4:office_hours>review(proxima=assessment) | bloco-27=review | alvo:duvidas-office_hours |
| ES2 | 4 | 03/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-03=holiday | bloco-03=holiday | suspended | 3:suspension | bloco-03=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-03=holiday | legitimo:feriado/suspensao |
| ES2 | 8 | 01/05/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-05=holiday | bloco-05=holiday | suspended | 3:suspension | bloco-05=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-05=holiday | legitimo:feriado/suspensao |
| ES2 | 15 | 19/06/2026 | Suspensão: jogo Copa do Mundo {kind=suspension} | Aula | suspension | suspension | bloco-11=suspended | bloco-11=suspended | suspended | 3:suspension | bloco-11=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-11=suspended | legitimo:feriado/suspensao |
| ES2 | 18 | 10/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-14=makeup | bloco-14=makeup | assessment | 2:atividade=prova | bloco-14=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-14=makeup |  |
| ES2 | 19 | 17/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-15=assessment | bloco-15=assessment | assessment | 2:atividade=prova | bloco-15=assessment | assessment | 2:atividade=prova | bloco-15=assessment |  |
| FR | 0 | 04/08/2026 | Apresentação da Disciplina | Aula |  | class | bloco-01=class | bloco-01=class | overview | 4:overview | bloco-01=overview | overview | 4:overview | bloco-01=overview |  |
| FR | 6 | 25/08/2026 | Aula Magna da Escola Politécnica {kind=event} | Evento Acadêmico | event | event | bloco-04=academic_event | bloco-04=academic_event | academic_event | 2:atividade=evento | bloco-04=academic_event | academic_event | 2:atividade=evento | bloco-04=academic_event |  |
| FR | 14 | 22/09/2026 | Dúvidas da P1 | Aula |  | class | bloco-10=office_hours | bloco-10=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-10=review | review | 4:office_hours>review(proxima=assessment) | bloco-10=review | alvo:duvidas-office_hours |
| FR | 17 | 01/10/2026 | Introdução ao roteamento IP | Aula |  | class | bloco-13=class (override) | bloco-13=class | class | 4:class | bloco-13=class | class | 4:class | bloco-13=class | alvo:FR-introducao-ao-roteamento |
| FR | 20 | 13/10/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-16=holiday | bloco-16=holiday | suspended | 3:suspension | bloco-16=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-16=holiday | legitimo:feriado/suspensao |
| FR | 22 | 20/10/2026 | Semana Acadêmica da PUCRS {kind=event} | Evento Acadêmico | event | event | bloco-18=academic_event | bloco-18=academic_event | academic_event | 2:atividade=evento | bloco-18=academic_event | academic_event | 2:atividade=evento | bloco-18=academic_event |  |
| FR | 23 | 22/10/2026 | Semana Acadêmica da PUCRS {kind=event} | Evento Acadêmico | event | event | bloco-19=academic_event | bloco-19=academic_event | academic_event | 2:atividade=evento | bloco-19=academic_event | academic_event | 2:atividade=evento | bloco-19=academic_event |  |
| FR | 34 | 01/12/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-27=makeup | bloco-27=makeup | assessment | 2:atividade=prova | bloco-27=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-27=makeup |  |
| FR | 36 | 08/12/2026 | {kind=g2} | Aula | g2 | g2 | bloco-29=assessment | bloco-29=assessment | class | 3:g2_metadado>4:class | bloco-29=class | assessment | 3:g2+rotulo_vazio(P1c) | bloco-29=assessment |  |
| FR | 37 | 10/12/2026 | Prova G2 {kind=g2} | Aula | g2 | g2 | bloco-30=assessment | bloco-30=assessment | assessment | 3:g2+rotulo_prova | bloco-30=assessment | assessment | 3:g2+rotulo_prova | bloco-30=assessment |  |
| IA | 0 | 02/03/2026 | Plano de ensino (conteúdo programático, cronograma, forma e  | Aula |  | class | bloco-01=overview | bloco-01=overview | overview | 4:overview | bloco-01=overview | overview | 4:overview | bloco-01=overview | legitimo:overview |
| IA | 2 | 09/03/2026 | ML - Introdução à ML | Aula |  | class | bloco-03=overview | bloco-03=overview | class | 4:class | bloco-03=class | class | 4:class | bloco-03=class | alvo:IA-ml-introducao |
| IA | 14 | 20/04/2026 | Suspensão de aulas {kind=suspension} | Aula | suspension | suspension | bloco-06=suspended | bloco-06=suspended | suspended | 3:suspension | bloco-06=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-06=suspended | legitimo:feriado/suspensao |
| IA | 17 | 29/04/2026 | Dúvidas para T1 | Aula |  | class | bloco-08=office_hours | bloco-08=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-08=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-08=office_hours | alvo:duvidas-office_hours |
| IA | 25 | 27/05/2026 | ES Day {kind=event} | Evento Acadêmico | event | event | bloco-14=academic_event | bloco-14=academic_event | academic_event | 2:atividade=evento | bloco-14=academic_event | academic_event | 2:atividade=evento | bloco-14=academic_event |  |
| IA | 33 | 24/06/2026 | Suspensao de atividades {kind=suspension} | Feriado | suspension | suspension | bloco-18=holiday | bloco-18=holiday | holiday | 2:atividade=feriado | bloco-18=holiday | holiday | 2:atividade=feriado | bloco-18=holiday | legitimo:feriado/suspensao |
| IA | 36 | 06/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-21=makeup | bloco-21=makeup | assessment | 2:atividade=prova | bloco-21=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-21=makeup |  |
| IA | 37 | 08/07/2026 | Atendimento. Divulgação dos resultados da G1 até 09/07 | Aula |  | results | bloco-22=results | bloco-22=results | review | 4:office_hours>review(proxima=assessment) | bloco-22=review | review | 4:office_hours>review(proxima=assessment) | bloco-22=review |  |
| IA | 38 | 13/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-23=assessment | bloco-23=assessment | assessment | 2:atividade=prova | bloco-23=assessment | assessment | 2:atividade=prova | bloco-23=assessment |  |
| IA | 39 | 15/07/2026 | {kind=g2} | Aula | g2 | g2 | bloco-24=assessment | bloco-24=assessment | class | 3:g2_metadado>4:class | bloco-24=class | assessment | 3:g2+rotulo_vazio(P1c) | bloco-24=assessment |  |
| LR | 0 | 03/08/2026 | Apresentação da disciplina | Aula |  | class | bloco-01=class | bloco-01=class | overview | 4:overview | bloco-01=overview | overview | 4:overview | bloco-01=overview |  |
| LR | 5 | 07/09/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-06=holiday | bloco-06=holiday | suspended | 3:suspension | bloco-06=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-06=holiday | legitimo:feriado/suspensao |
| LR | 10 | 12/10/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-10=holiday | bloco-10=holiday | suspended | 3:suspension | bloco-10=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-10=holiday | legitimo:feriado/suspensao |
| LR | 13 | 02/11/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-13=holiday | bloco-13=holiday | suspended | 3:suspension | bloco-13=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-13=holiday | legitimo:feriado/suspensao |
| LR | 18 | 07/12/2026 | {kind=g2} | Aula | g2 | g2 | bloco-17=assessment | bloco-17=assessment | class | 3:g2_metadado>4:class | bloco-17=class | assessment | 3:g2+rotulo_vazio(P1c) | bloco-17=assessment |  |
| MF | 0 | 02/03/2026 | Apresentação da disciplina | Aula |  | class | bloco-01=class | bloco-01=class | overview | 4:overview | bloco-01=overview | overview | 4:overview | bloco-01=overview |  |
| MF | 2 | 09/03/2026 | Revisão de lógica de predicados, Exercícios | Aula |  | class | bloco-03=class | bloco-03=class | review | 4:review | bloco-03=class | review | 4:review | bloco-03=class |  |
| MF | 13 | 15/04/2026 | Exercícios de revisão | Aula |  | class | bloco-07=review | bloco-07=review | review | 4:review | bloco-07=review | review | 4:review | bloco-07=review | legitimo:revisao |
| MF | 14 | 20/04/2026 | Suspensão de aulas {kind=suspension} | Aula | suspension | suspension | bloco-08=suspended | bloco-08=suspended | suspended | 3:suspension | bloco-08=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-08=suspended | legitimo:feriado/suspensao |
| MF | 25 | 27/05/2026 | SE Day {kind=event} | Evento Acadêmico | event | event | bloco-14=academic_event | bloco-14=academic_event | academic_event | 2:atividade=evento | bloco-14=academic_event | academic_event | 2:atividade=evento | bloco-14=academic_event |  |
| MF | 33 | 24/06/2026 | Suspensão: jogo Copa do Mundo {kind=suspension} | Aula | suspension | suspension | bloco-17=suspended | bloco-17=suspended | suspended | 3:suspension | bloco-17=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-17=suspended | legitimo:feriado/suspensao |
| MF | 35 | 01/07/2026 | Exercícios de revisão | Aula |  | class | bloco-19=review | bloco-19=review | review | 4:review | bloco-19=review | review | 4:review | bloco-19=review | legitimo:revisao |
| MF | 37 | 08/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-21=makeup | bloco-21=makeup | assessment | 2:atividade=prova | bloco-21=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-21=makeup |  |
| MF | 39 | 15/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-23=assessment | bloco-23=assessment | assessment | 2:atividade=prova | bloco-23=assessment | assessment | 2:atividade=prova | bloco-23=assessment |  |
| SO | 0 | 03/03/2026 | Apresentação da disciplina e Introdução | Aula |  | class | bloco-01=overview | bloco-01=overview | overview | 4:overview | bloco-01=overview | overview | 4:overview | bloco-01=overview | legitimo:overview |
| SO | 1 | 05/03/2026 | Introdução | Aula |  | class | bloco-02=overview | bloco-02=overview | overview | 4:overview | bloco-02=overview | overview | 4:overview | bloco-02=overview | legitimo:overview |
| SO | 9 | 02/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-05=holiday | bloco-05=holiday | suspended | 3:suspension | bloco-05=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-05=holiday | legitimo:feriado/suspensao |
| SO | 14 | 21/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-08=holiday | bloco-08=holiday | suspended | 3:suspension | bloco-08=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-08=holiday | legitimo:feriado/suspensao |
| SO | 17 | 30/04/2026 | Duvidas Prova | Aula |  | class | bloco-10=office_hours | bloco-10=office_hours | office_hours | 4:office_hours(proxima=office_hours) | bloco-10=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-10=review | alvo:duvidas-office_hours |
| SO | 18 | 05/05/2026 | Duvidas TP1, duvidas p1 | Aula |  | class | bloco-11=office_hours | bloco-11=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-11=review | review | 4:office_hours>review(proxima=assessment) | bloco-11=review | alvo:duvidas-office_hours |
| SO | 27 | 04/06/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-17=holiday | bloco-17=holiday | suspended | 3:suspension | bloco-17=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-17=holiday | legitimo:feriado/suspensao |
| SO | 34 | 30/06/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-22=makeup | bloco-22=makeup | assessment | 2:atividade=prova | bloco-22=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-22=makeup |  |
| SO | 38 | 14/07/2026 | Prova G2 {kind=g2} | Aula | g2 | g2 | bloco-26=assessment | bloco-26=assessment | assessment | 3:g2+rotulo_prova | bloco-26=assessment | assessment | 3:g2+rotulo_prova | bloco-26=assessment |  |
| SO | 39 | 16/07/2026 | {kind=g2} | Aula | g2 | g2 | bloco-27=assessment | bloco-27=assessment | class | 3:g2_metadado>4:class | bloco-27=class | assessment | 3:g2+rotulo_vazio(P1c) | bloco-27=assessment |  |
| TCC | 6 | 25/03/2026 | Revisão: Alfabeto, Cadeia, Linguagem, Hierarquia de Chomsky, | Aula |  | class | bloco-05=class | bloco-05=class | review | 4:review | bloco-05=class | review | 4:review | bloco-05=class |  |
| TCC | 9 | 03/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-07=holiday | bloco-07=holiday | suspended | 3:suspension | bloco-07=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-07=holiday | legitimo:feriado/suspensao |
| TCC | 17 | 01/05/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-15=holiday | bloco-15=holiday | suspended | 3:suspension | bloco-15=suspended | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-15=holiday | legitimo:feriado/suspensao |
| TCC | 18 | 06/05/2026 | Revisão para prova P1 | Aula |  | class | bloco-16=review | bloco-16=review | review | 4:review | bloco-16=review | review | 4:review | bloco-16=review | legitimo:revisao |
| TCC | 24 | 27/05/2026 | SE DAY {kind=event} | Evento Acadêmico | event | event | bloco-20=academic_event | bloco-20=academic_event | academic_event | 2:atividade=evento | bloco-20=academic_event | academic_event | 2:atividade=evento | bloco-20=academic_event |  |
| TCC | 25 | 29/05/2026 | Oficina de problemas - Entrega T2 | Aula |  | class | bloco-21=workshop | bloco-21=workshop | workshop | 4:workshop | bloco-21=workshop | workshop | 4:workshop | bloco-21=workshop | alvo:TCC-oficina |
| TCC | 29 | 12/06/2026 | Oficina de problemas - Entrega T2 {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-25=deliverable | bloco-25=deliverable | deliverable | 2:atividade=trabalho | bloco-25=deliverable | deliverable | 2:atividade=trabalho | bloco-25=deliverable | alvo:TCC-oficina |
| TCC | 30 | 17/06/2026 | Oficina de problemas {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-26=deliverable | bloco-26=deliverable | deliverable | 2:atividade=trabalho | bloco-26=deliverable | deliverable | 2:atividade=trabalho | bloco-26=deliverable | alvo:TCC-oficina |
| TCC | 31 | 19/06/2026 | Oficina de problemas {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-27=deliverable | bloco-27=deliverable | deliverable | 2:atividade=trabalho | bloco-27=deliverable | deliverable | 2:atividade=trabalho | bloco-27=deliverable | alvo:TCC-oficina |
| TCC | 32 | 24/06/2026 | Oficina de problemas {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-28=deliverable | bloco-28=deliverable | deliverable | 2:atividade=trabalho | bloco-28=deliverable | deliverable | 2:atividade=trabalho | bloco-28=deliverable | alvo:TCC-oficina |
| TCC | 33 | 26/06/2026 | Oficina de problemas - Apresentação {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-29=deliverable | bloco-29=deliverable | deliverable | 2:atividade=trabalho | bloco-29=deliverable | deliverable | 2:atividade=trabalho | bloco-29=deliverable | alvo:TCC-oficina |
| TCC | 34 | 01/07/2026 | Revisão para Prova P2 | Aula |  | class | bloco-30=review | bloco-30=review | review | 4:review | bloco-30=review | review | 4:review | bloco-30=review | legitimo:revisao |
| TCC | 36 | 08/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-32=makeup | bloco-32=makeup | assessment | 2:atividade=prova | bloco-32=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-32=makeup |  |
| TCC | 38 | 15/07/2026 | Atendimento a dúvidas {kind=g2} | Aula | g2 | g2 | bloco-34=assessment | bloco-34=assessment | review | 3:g2_metadado>4:office_hours>review(proxima=assessment) | bloco-34=review | review | 3:g2_metadado>4:office_hours>review(proxima=assessment) | bloco-34=review | alvo:TCC-atendimento-g2 |
| TCC | 39 | 17/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-35=assessment | bloco-35=assessment | assessment | 2:atividade=prova | bloco-35=assessment | assessment | 2:atividade=prova | bloco-35=assessment |  |

Tabela completa (todas as linhas) em `A.linhas` do JSON.

## B. Segmentacao (indice reconstruido em memoria; controle x P0/P1, mesmo insumo)

- CG: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 29 -> 29 blocos, 29 identicos
  - controle_x_P1: 29 -> 29 blocos, 29 identicos
- ES2: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 15 -> 15 blocos, 15 identicos
  - controle_x_P1: 15 -> 15 blocos, 15 identicos
- FR: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 30 -> 30 blocos, 30 identicos
  - controle_x_P1: 30 -> 30 blocos, 30 identicos
- IA: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 24 -> 24 blocos, 24 identicos
  - controle_x_P1: 24 -> 24 blocos, 24 identicos
- LR: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 17 -> 17 blocos, 17 identicos
  - controle_x_P1: 17 -> 17 blocos, 17 identicos
- MF: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 23 -> 23 blocos, 23 identicos
  - controle_x_P1: 23 -> 23 blocos, 23 identicos
- SO: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 27 -> 27 blocos, 27 identicos
  - controle_x_P1: 27 -> 27 blocos, 27 identicos
- TCC: vivo x controle = 0 grupos de segmentacao, 0 blocos com kind divergente
  - controle_x_P0: 35 -> 35 blocos, 35 identicos
  - controle_x_P1: 35 -> 35 blocos, 35 identicos

## C. Placar 3 eixos (builds-base)

| braco | bloco (estrito) | bloco leniente | unidade | sub prim | sub aceita |
|---|---|---|---|---|---|
| base | 217/237 | 217 | 246/284 | 84/251 | 107/251 |
| controle | 217/237 | 217 | 246/284 | 84/251 | 107/251 |
| P0 | 215/237 | 215 | 247/284 | 85/251 | 108/251 |
| P1 | 215/237 | 215 | 247/284 | 85/251 | 108/251 |

Por curso (bloco, unidade, sub prim, sub aceita):

- MF: base 56/61/25/29; controle 56/61/25/29; P0 56/61/25/29; P1 56/61/25/29
- SO: base 36/30/7/8; controle 36/30/7/8; P0 34/29/7/8; P1 34/29/7/8
- IA: base 39/39/4/5; controle 39/39/4/5; P0 39/39/4/5; P1 39/39/4/5
- ES2: base 27/25/7/8; controle 27/25/7/8; P0 27/25/7/8; P1 27/25/7/8
- TCC: base 26/17/7/9; controle 26/17/7/9; P0 26/17/7/9; P1 26/17/7/9
- CG: base 33/74/28/41; controle 33/74/28/41; P0 33/76/29/42; P1 33/76/29/42
- FR: base None/None/6/7; controle None/None/6/7; P0 None/None/6/7; P1 None/None/6/7

Diferencas por ID (de -> para):

- controle->P0 ganho CG sub_aceita openglbasico (gold openglbasico)
- controle->P0 ganho CG sub_primaria openglbasico (gold openglbasico)
- controle->P0 ganho CG unidade exercicios (gold exercicios)
- controle->P0 ganho CG unidade openglbasico (gold openglbasico)
- controle->P0 perda SO bloco lista-exercicios-p1 (gold lista-exercicios-p1)
- controle->P0 perda SO bloco lista-exercicios-p1-gabarito (gold lista-exercicios-p1-gabarito)
- controle->P0 perda SO bloco_leniente lista-exercicios-p1 (gold lista-exercicios-p1)
- controle->P0 perda SO bloco_leniente lista-exercicios-p1-gabarito (gold lista-exercicios-p1-gabarito)
- controle->P0 perda SO unidade lista-exercicios-p1 (gold lista-exercicios-p1)
- controle->P1 ganho CG sub_aceita openglbasico (gold openglbasico)
- controle->P1 ganho CG sub_primaria openglbasico (gold openglbasico)
- controle->P1 ganho CG unidade exercicios (gold exercicios)
- controle->P1 ganho CG unidade openglbasico (gold openglbasico)
- controle->P1 perda SO bloco lista-exercicios-p1 (gold lista-exercicios-p1)
- controle->P1 perda SO bloco lista-exercicios-p1-gabarito (gold lista-exercicios-p1-gabarito)
- controle->P1 perda SO bloco_leniente lista-exercicios-p1 (gold lista-exercicios-p1)
- controle->P1 perda SO bloco_leniente lista-exercicios-p1-gabarito (gold lista-exercicios-p1-gabarito)
- controle->P1 perda SO unidade lista-exercicios-p1 (gold lista-exercicios-p1)

Gold de bloco remapeado (bloco base sem bloco de linhas identicas no braco):


Segmentacao nos builds-base:

- MF base_x_controle: 23 -> 23, 23 identicos, 0 grupos
- MF controle_x_P0: 23 -> 23, 23 identicos, 0 grupos
- MF controle_x_P1: 23 -> 23, 23 identicos, 0 grupos
- SO base_x_controle: 27 -> 27, 27 identicos, 0 grupos
- SO controle_x_P0: 27 -> 27, 27 identicos, 0 grupos
- SO controle_x_P1: 27 -> 27, 27 identicos, 0 grupos
- IA base_x_controle: 24 -> 24, 24 identicos, 0 grupos
- IA controle_x_P0: 24 -> 24, 24 identicos, 0 grupos
- IA controle_x_P1: 24 -> 24, 24 identicos, 0 grupos
- ES2 base_x_controle: 15 -> 15, 15 identicos, 0 grupos
- ES2 controle_x_P0: 15 -> 15, 15 identicos, 0 grupos
- ES2 controle_x_P1: 15 -> 15, 15 identicos, 0 grupos
- TCC base_x_controle: 35 -> 35, 35 identicos, 0 grupos
- TCC controle_x_P0: 35 -> 35, 35 identicos, 0 grupos
- TCC controle_x_P1: 35 -> 35, 35 identicos, 0 grupos
- CG base_x_controle: 29 -> 29, 29 identicos, 0 grupos
- CG controle_x_P0: 29 -> 29, 29 identicos, 0 grupos
- CG controle_x_P1: 29 -> 29, 29 identicos, 0 grupos
- FR base_x_controle: 30 -> 30, 30 identicos, 0 grupos
- FR controle_x_P0: 30 -> 30, 30 identicos, 0 grupos
- FR controle_x_P1: 30 -> 30, 30 identicos, 0 grupos

## D. Obsoletos com o prototipo

- src/builder/timeline/classifier.py:29 `CLASS_INTRO_TERMS` — regra 1 OVERVIEW por substring no conteudo agregado
- src/builder/timeline/classifier.py:53 `KIND_KEYWORDS` — regra 3 keywords sobre conteudo agregado + period_label
- src/builder/timeline/classifier.py:102 `def _content_text` — insumo das heuristicas de conteudo
- src/builder/timeline/classifier.py:115 `def _session_text` — insumo de _session_exam_or_review
- src/builder/timeline/classifier.py:140 `def _session_exam_or_review` — regras 2/3b (sessao revela prova/revisao)
- src/builder/timeline/classifier.py:155 `def _office_hours_session_majority` — guard maioria de sessoes (SO bloco-18)
- src/builder/timeline/classifier.py:176 `def _text_of` — conteudo+period_label para keywords
- src/builder/timeline/classifier.py:184 `def _has_unit_evidence` — guard planning/trabalho por evidencia de unidade
- src/builder/timeline/classifier.py:192 `def _cue_e_conteudo_do_plano` — guard cue x conteudo do plano (F2/F3)
- src/builder/timeline/classifier.py:137 `WEAK_EXAM_TOKENS` — guard 'prova'/'teste' nus (motor window_provider tambem importa)
- src/builder/timeline/classifier.py:321 `def row_kind_from_text` — linha classificada via classify_block sintetico
- src/builder/timeline/classifier.py:336 `ROW_TEXT_KINDS` — subconjunto de kinds por texto de linha
- src/builder/timeline/index.py:53 `def plan_phrases_para_classificacao` — so alimenta _cue_e_conteudo_do_plano
- src/builder/timeline/index.py:308 `_IGNORED_KIND_AS_SOURCE` — g2/ps viram assessment/makeup sem olhar o rotulo
- src/builder/timeline/index.py:1252 `def _promote_preexam_reviews` — heuristica de label de sessao 'revisao' (pos-classificacao)

Testes que referenciam esses simbolos: {"test_atividade_kind.py": ["classify_block", "_aggregate_source_kind"], "test_classifier_guard_prova_plano.py": ["classify_block"], "test_classifier_office_hours_guard.py": ["classify_block"], "test_core.py": ["classify_block", "_promote_preexam_reviews"], "test_cue_conteudo_do_plano.py": ["classify_block"], "test_sarc_kind_flow.py": ["_aggregate_source_kind"], "test_timeline_kinds.py": ["classify_block"]}

