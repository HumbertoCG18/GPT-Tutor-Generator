# W-Y v2 (#52, MOTOR-08) — tipo de bloco por linha na base vigente

src: `C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator-ap1-base` @ f404c6de; pre-registro sha256 `8b8a24dd86825784f01545524b50c91e13d3c4867276630d65dd5415c8841400`; resultado sha256 `0c2c2b8810502ec9b69211f0cfb8b36632d67e8a66d739ff25f48d1345bd05c9`; 593 s. Repos intocados: True.

Bracos: base (indice gravado = referencia 87), controle (indice reconstruido com o codigo atual), P1adj (prototipo P1 do W-Y + adjudicacoes 2 e 4 de 05/10), P1adjH (P1adj + H-duvidas no prep-prova). Aceite contra controle.

## C. Placar (cadeia da referencia 87)

| braco | bloco | unidade | sub prim | sub aceita |
|---|---|---|---|---|
| base | 223/237 | 249/284 | 87/251 | 110/251 |
| controle | 223/237 | 249/284 | 87/251 | 110/251 |
| P1adj | 215/237 | 252/284 | 88/251 | 111/251 |
| P1adjH | 217/237 | 253/284 | 88/251 | 111/251 |

Aceite (contra controle): {"P1adj": {"perdas": 9, "ganhos": 6, "cursos_que_regridem": [["SO", "bloco"], ["SO", "unidade"], ["TCC", "bloco"]], "passa": false}, "P1adjH": {"perdas": 6, "ganhos": 6, "cursos_que_regridem": [["TCC", "bloco"]], "passa": false}}

Diferencas por ID (gold):

- base->controle: nenhuma
- controle->P1adj: ganho CG unidade exercicios; ganho CG sub_aceita openglbasico; ganho CG sub_primaria openglbasico; ganho CG unidade openglbasico; ganho CG unidade video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758; ganho MF unidade eth2; perda SO bloco lista-exercicios-p1; perda SO unidade lista-exercicios-p1; perda SO bloco lista-exercicios-p1-gabarito; perda TCC bloco 3d-matching; perda TCC bloco 3dm-caetano-gabriel-e-gustavo; perda TCC bloco cubic-3-edge-coloring; perda TCC bloco integer-programming-0001; perda TCC bloco programacao-inteira-01-20260617-154423-0000; perda TCC bloco trabalho-t2-enunciado
- controle->P1adjH: ganho CG unidade exercicios; ganho CG sub_aceita openglbasico; ganho CG sub_primaria openglbasico; ganho CG unidade openglbasico; ganho CG unidade video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758; ganho MF unidade eth2; perda TCC bloco 3d-matching; perda TCC bloco 3dm-caetano-gabriel-e-gustavo; perda TCC bloco cubic-3-edge-coloring; perda TCC bloco integer-programming-0001; perda TCC bloco programacao-inteira-01-20260617-154423-0000; perda TCC bloco trabalho-t2-enunciado
- P1adj->P1adjH: ganho SO bloco lista-exercicios-p1; ganho SO unidade lista-exercicios-p1; ganho SO bloco lista-exercicios-p1-gabarito

Por curso (bloco/unidade/sub prim/sub aceita):

- MF: base 60/63/25/29; controle 60/63/25/29; P1adj 60/64/25/29; P1adjH 60/64/25/29
- SO: base 36/30/7/8; controle 36/30/7/8; P1adj 34/29/7/8; P1adjH 36/30/7/8
- IA: base 41/39/4/5; controle 41/39/4/5; P1adj 41/39/4/5; P1adjH 41/39/4/5
- ES2: base 27/26/7/8; controle 27/26/7/8; P1adj 27/26/7/8; P1adjH 27/26/7/8
- TCC: base 26/17/8/10; controle 26/17/8/10; P1adj 20/17/8/10; P1adjH 20/17/8/10
- CG: base 33/74/30/43; controle 33/74/30/43; P1adj 33/77/31/44; P1adjH 33/77/31/44
- FR: base None/None/6/7; controle None/None/6/7; P1adj None/None/6/7; P1adjH None/None/6/7

Base x referencia 87: 0 mudancas por ID. Congelado: {"arquivo": "wy2_kind_por_linha_05-10_congelado.json", "sha256_decisoes": "455b9cee82d120c95429dd79b879883d634112c96637fceb8055cb7e94233acd", "sha256_arquivo": "b3890b43a66049f1d32b890d3d77691e937f997c8d6cc79a4a0ba9885d05be73"}

Mudancas de decisao sem gold:

- base->controle: 0
- controle->P1adj: 18
  - CG exercicios: {'bloco': 'bloco-02', 'unidade': 'unidade-02-fundamentos-matematicos', 'sub': ''} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-ao-processamento-grafico', 'sub': ''}
  - CG listadeexercicios2026-1: {'bloco': 'bloco-21', 'unidade': 'unidade-08-sintese-de-imagens-realisticas', 'sub': 'modelos-de-reflexao-ambiente-difusa-especular'} -> {'bloco': 'bloco-22', 'unidade': 'unidade-08-sintese-de-imagens-realisticas', 'sub': 'modelos-de-reflexao-ambiente-difusa-especular'}
  - CG openglbasico: {'bloco': 'bloco-02', 'unidade': 'unidade-03-processamento-de-imagens-e-visao-computacional', 'sub': 'introducao-e-exemplos-de-aplicacoes'} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-ao-processamento-grafico', 'sub': 'aplicacoes'}
  - CG video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758: {'bloco': 'bloco-02', 'unidade': 'unidade-02-fundamentos-matematicos', 'sub': ''} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-ao-processamento-grafico', 'sub': ''}
  - FR 01-protocolos-de-rede: {'bloco': 'bloco-01', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'modelos-osi-e-tcpip'} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'modelos-osi-e-tcpip'}
  - FR 03-tipos-de-redes: {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia'} -> {'bloco': 'bloco-03', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia'}
  - FR 06-protocolo-dhcp: {'bloco': 'bloco-03', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': 'protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat'} -> {'bloco': 'bloco-05', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': 'protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat'}
  - FR 08-desenvolvimento-de-aplicacoes: {'bloco': 'bloco-05', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': ''} -> {'bloco': 'bloco-06', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': ''}
  - MF archive-of-formal-proofs-355fb8: {'bloco': 'bloco-01', 'unidade': 'unidade-01-metodos-formais', 'sub': 'abordagens-para-verificacao-formal'} -> {'bloco': 'bloco-01', 'unidade': 'unidade-01-metodos-formais', 'sub': 'sistemas-formais'}
  - MF eth2: {'bloco': 'bloco-01', 'unidade': 'unidade-01-metodos-formais', 'sub': 'abordagens-para-verificacao-formal'} -> {'bloco': 'bloco-01', 'unidade': 'unidade-02-verificacao-de-programas', 'sub': 'correcao-parcial-e-total'}
  - SO lista-exercicios-p1: {'bloco': 'bloco-09', 'unidade': 'unidade-03-programacao-concorrente', 'sub': ''} -> {'bloco': 'bloco-11', 'unidade': 'unidade-01-introducao-ao-estudo-de-sistemas-operacionais', 'sub': 'chamadas-de-sistema'}
  - SO lista-exercicios-p1-gabarito: {'bloco': 'bloco-09', 'unidade': 'unidade-03-programacao-concorrente', 'sub': 'programas-multithreads'} -> {'bloco': 'bloco-11', 'unidade': 'unidade-03-programacao-concorrente', 'sub': 'programas-multithreads'}
  - TCC 3d-matching: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC 3dm-caetano-gabriel-e-gustavo: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC cubic-3-edge-coloring: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': ''} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': ''}
  - TCC integer-programming-0001: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC programacao-inteira-01-20260617-154423-0000: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC trabalho-t2-enunciado: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
- controle->P1adjH: 15
  - CG exercicios: {'bloco': 'bloco-02', 'unidade': 'unidade-02-fundamentos-matematicos', 'sub': ''} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-ao-processamento-grafico', 'sub': ''}
  - CG openglbasico: {'bloco': 'bloco-02', 'unidade': 'unidade-03-processamento-de-imagens-e-visao-computacional', 'sub': 'introducao-e-exemplos-de-aplicacoes'} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-ao-processamento-grafico', 'sub': 'aplicacoes'}
  - CG video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758: {'bloco': 'bloco-02', 'unidade': 'unidade-02-fundamentos-matematicos', 'sub': ''} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-ao-processamento-grafico', 'sub': ''}
  - FR 01-protocolos-de-rede: {'bloco': 'bloco-01', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'modelos-osi-e-tcpip'} -> {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'modelos-osi-e-tcpip'}
  - FR 03-tipos-de-redes: {'bloco': 'bloco-02', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia'} -> {'bloco': 'bloco-03', 'unidade': 'unidade-01-introducao-a-redes-de-computadores', 'sub': 'conceito-de-protocolo-de-redes-pessoais-locais-metropolitanas-e-de-longa-distancia'}
  - FR 06-protocolo-dhcp: {'bloco': 'bloco-03', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': 'protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat'} -> {'bloco': 'bloco-05', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': 'protocolos-de-aplicacao-para-infraestrutura-dns-dhcp-snmp-nat'}
  - FR 08-desenvolvimento-de-aplicacoes: {'bloco': 'bloco-05', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': ''} -> {'bloco': 'bloco-06', 'unidade': 'unidade-02-nivel-de-aplicacao', 'sub': ''}
  - MF archive-of-formal-proofs-355fb8: {'bloco': 'bloco-01', 'unidade': 'unidade-01-metodos-formais', 'sub': 'abordagens-para-verificacao-formal'} -> {'bloco': 'bloco-01', 'unidade': 'unidade-01-metodos-formais', 'sub': 'sistemas-formais'}
  - MF eth2: {'bloco': 'bloco-01', 'unidade': 'unidade-01-metodos-formais', 'sub': 'abordagens-para-verificacao-formal'} -> {'bloco': 'bloco-01', 'unidade': 'unidade-02-verificacao-de-programas', 'sub': 'correcao-parcial-e-total'}
  - TCC 3d-matching: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC 3dm-caetano-gabriel-e-gustavo: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC cubic-3-edge-coloring: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': ''} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': ''}
  - TCC integer-programming-0001: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC programacao-inteira-01-20260617-154423-0000: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
  - TCC trabalho-t2-enunciado: {'bloco': 'bloco-25', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-04-hierarquia-de-classes-de-complexidade-de-problemas-computacionais', 'sub': 'reducao-polinomial-de-problemas'}
- P1adj->P1adjH: 3
  - CG listadeexercicios2026-1: {'bloco': 'bloco-22', 'unidade': 'unidade-08-sintese-de-imagens-realisticas', 'sub': 'modelos-de-reflexao-ambiente-difusa-especular'} -> {'bloco': 'bloco-21', 'unidade': 'unidade-08-sintese-de-imagens-realisticas', 'sub': 'modelos-de-reflexao-ambiente-difusa-especular'}
  - SO lista-exercicios-p1: {'bloco': 'bloco-11', 'unidade': 'unidade-01-introducao-ao-estudo-de-sistemas-operacionais', 'sub': 'chamadas-de-sistema'} -> {'bloco': 'bloco-09', 'unidade': 'unidade-03-programacao-concorrente', 'sub': ''}
  - SO lista-exercicios-p1-gabarito: {'bloco': 'bloco-11', 'unidade': 'unidade-03-programacao-concorrente', 'sub': 'programas-multithreads'} -> {'bloco': 'bloco-09', 'unidade': 'unidade-03-programacao-concorrente', 'sub': 'programas-multithreads'}

Raizes do placar: demovidos no DP = {"MF": ["bloco-03"], "SO": [], "IA": [], "ES2": [], "TCC": ["bloco-05"], "CG": [], "FR": []}; skip H = {"MF": [], "SO": ["bloco-10", "bloco-11"], "IA": ["bloco-22"], "ES2": [], "TCC": ["bloco-34"], "CG": ["bloco-09", "bloco-22", "bloco-27"], "FR": ["bloco-10"]}

## A. Tipos nos 8 cursos vivos (controle -> P1adj)

| contagem | academic_event | assessment | class | deliverable | event | g2 | holiday | makeup | office_hours | overview | ps | reserved | results | review | suspended | suspension | workshop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linha_atual | 0 | 16 | 184 | 29 | 8 | 11 | 1 | 0 | 0 | 0 | 6 | 2 | 2 | 0 | 0 | 16 | 0 |
| linha_P1adj | 8 | 25 | 164 | 30 | 0 | 0 | 13 | 7 | 3 | 6 | 0 | 2 | 1 | 12 | 4 | 0 | 0 |
| bloco_vivo | 8 | 26 | 91 | 29 | 0 | 0 | 13 | 6 | 8 | 4 | 0 | 3 | 2 | 5 | 4 | 0 | 1 |
| bloco_controle | 8 | 26 | 91 | 29 | 0 | 0 | 13 | 6 | 8 | 4 | 0 | 3 | 2 | 5 | 4 | 0 | 1 |
| bloco_P1adj | 8 | 24 | 89 | 30 | 0 | 0 | 13 | 7 | 3 | 6 | 0 | 3 | 1 | 12 | 4 | 0 | 0 |

Demovidos que voltam ao DP: {"MF": [{"bloco": "bloco-03", "linhas": [2], "unit_f1": "unidade-01-metodos-formais", "kind_f2": "class", "unit_f2": "unidade-01-metodos-formais"}], "TCC": [{"bloco": "bloco-05", "linhas": [6], "unit_f1": "unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas", "kind_f2": "class", "unit_f2": "unidade-02-turing-computabilidade"}]}

Skip H (review de duvidas, nao alvo do prep-prova): {"CG": ["bloco-09", "bloco-22", "bloco-27"], "ES2": [], "FR": ["bloco-10"], "IA": ["bloco-22"], "LR": [], "MF": [], "SO": ["bloco-10", "bloco-11"], "TCC": ["bloco-34"]}

Linhas class com cauda 'entrega' (regra (2) NAO aplicada a elas): []

### Linhas cujo tipo (linha ou bloco) ou unidade do bloco muda, + alvos

| curso | L | data | rotulo | Atividade | marc | linha atual | bloco vivo | bloco controle | linha P1adj | regra P1adj | bloco P1adj | unidade ctrl -> P1adj | caso |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CG | 14 | 22/09/2026 | Aula de dúvidas | Aula |  | class | bloco-09=office_hours | bloco-09=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-09=review |  ->  | alvo:duvidas-office_hours |
| CG | 16 | 29/09/2026 | Aula de dúvidas | Aula |  | class | bloco-11=office_hours | bloco-11=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-11=office_hours |  ->  | alvo:duvidas-office_hours |
| CG | 22 | 20/10/2026 | Semana Acadêmica | Evento Acadêmico |  | event | bloco-16=academic_event | bloco-16=academic_event | academic_event | 2:atividade=evento | bloco-16=academic_event |  ->  |  |
| CG | 23 | 22/10/2026 | Semana Acadêmica | Evento Acadêmico |  | event | bloco-17=academic_event | bloco-17=academic_event | academic_event | 2:atividade=evento | bloco-17=academic_event |  ->  |  |
| CG | 30 | 17/11/2026 | Aula de dúvidas | Aula |  | class | bloco-22=office_hours | bloco-22=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-22=review |  ->  | alvo:duvidas-office_hours |
| CG | 32 | 24/11/2026 | Prova PS | Prova de Substituição |  | assessment | bloco-24=assessment | bloco-24=assessment | makeup | 2:atividade=substituicao(P1a) | bloco-24=makeup |  ->  |  |
| CG | 33 | 26/11/2026 | Aula de dúvidas | Aula |  | class | bloco-25=office_hours | bloco-25=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-25=office_hours |  ->  | alvo:duvidas-office_hours |
| CG | 35 | 03/12/2026 | Aula de dúvidas | Aula |  | class | bloco-27=office_hours | bloco-27=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-27=review |  ->  | alvo:duvidas-office_hours |
| ES2 | 4 | 03/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-03=holiday | bloco-03=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-03=holiday |  ->  | legitimo:feriado/suspensao |
| ES2 | 8 | 01/05/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-05=holiday | bloco-05=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-05=holiday |  ->  | legitimo:feriado/suspensao |
| ES2 | 15 | 19/06/2026 | Suspensão: jogo Copa do Mundo {kind=suspension} | Aula | suspension | suspension | bloco-11=suspended | bloco-11=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-11=suspended |  ->  | legitimo:feriado/suspensao |
| ES2 | 18 | 10/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-14=makeup | bloco-14=makeup | makeup | 2:atividade=substituicao(P1a) | bloco-14=makeup |  ->  |  |
| ES2 | 19 | 17/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-15=assessment | bloco-15=assessment | assessment | 2:atividade=prova | bloco-15=assessment |  ->  |  |
| FR | 0 | 04/08/2026 | Apresentação da Disciplina | Aula |  | class | bloco-01=class | bloco-01=class | overview | 4:overview | bloco-01=overview | unidade-01-introducao-a-redes-de-computadores ->  |  |
| FR | 6 | 25/08/2026 | Aula Magna da Escola Politécnica {kind=event} | Evento Acadêmico | event | event | bloco-04=academic_event | bloco-04=academic_event | academic_event | 2:atividade=evento | bloco-04=academic_event |  ->  |  |
| FR | 14 | 22/09/2026 | Dúvidas da P1 | Aula |  | class | bloco-10=review (override) | bloco-10=review | review | 4:office_hours>review(proxima=assessment) | bloco-10=review |  ->  | legitimo:revisao |
| FR | 17 | 01/10/2026 | Introdução ao roteamento IP | Aula |  | class | bloco-13=class (override) | bloco-13=class | class | 4:class | bloco-13=class | unidade-04-nivel-de-rede -> unidade-04-nivel-de-rede | alvo:FR-introducao-ao-roteamento |
| FR | 20 | 13/10/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-16=holiday | bloco-16=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-16=holiday |  ->  | legitimo:feriado/suspensao |
| FR | 22 | 20/10/2026 | Semana Acadêmica da PUCRS {kind=event} | Evento Acadêmico | event | event | bloco-18=academic_event | bloco-18=academic_event | academic_event | 2:atividade=evento | bloco-18=academic_event |  ->  |  |
| FR | 23 | 22/10/2026 | Semana Acadêmica da PUCRS {kind=event} | Evento Acadêmico | event | event | bloco-19=academic_event | bloco-19=academic_event | academic_event | 2:atividade=evento | bloco-19=academic_event |  ->  |  |
| FR | 34 | 01/12/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-27=makeup | bloco-27=makeup | makeup | 2:atividade=substituicao(P1a) | bloco-27=makeup |  ->  |  |
| FR | 36 | 08/12/2026 | {kind=g2} | Aula | g2 | g2 | bloco-29=reserved (override) | bloco-29=reserved | assessment | 3:g2+rotulo_vazio(P1c) | bloco-29=reserved |  ->  |  |
| FR | 37 | 10/12/2026 | Prova G2 {kind=g2} | Aula | g2 | g2 | bloco-30=assessment | bloco-30=assessment | assessment | 3:g2+rotulo_prova | bloco-30=assessment |  ->  |  |
| IA | 0 | 02/03/2026 | Plano de ensino (conteúdo programático, cronograma, forma e  | Aula |  | class | bloco-01=overview | bloco-01=overview | overview | 4:overview | bloco-01=overview |  ->  | legitimo:overview |
| IA | 2 | 09/03/2026 | ML - Introdução à ML | Aula |  | class | bloco-03=overview | bloco-03=overview | class | 4:class | bloco-03=class | unidade-de-aprendizagem-05-aprendizado-de-maquina -> unidade-de-aprendizagem-05-aprendizado-de-maquina | alvo:IA-ml-introducao |
| IA | 14 | 20/04/2026 | Suspensão de aulas {kind=suspension} | Aula | suspension | suspension | bloco-06=suspended | bloco-06=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-06=suspended |  ->  | legitimo:feriado/suspensao |
| IA | 17 | 29/04/2026 | Dúvidas para T1 | Aula |  | class | bloco-08=office_hours | bloco-08=office_hours | office_hours | 4:office_hours(proxima=deliverable) | bloco-08=office_hours |  ->  | alvo:duvidas-office_hours |
| IA | 25 | 27/05/2026 | ES Day {kind=event} | Evento Acadêmico | event | event | bloco-14=academic_event | bloco-14=academic_event | academic_event | 2:atividade=evento | bloco-14=academic_event |  ->  |  |
| IA | 33 | 24/06/2026 | Suspensao de atividades {kind=suspension} | Feriado | suspension | suspension | bloco-18=holiday | bloco-18=holiday | holiday | 2:atividade=feriado | bloco-18=holiday |  ->  | legitimo:feriado/suspensao |
| IA | 36 | 06/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-21=makeup | bloco-21=makeup | makeup | 2:atividade=substituicao(P1a) | bloco-21=makeup |  ->  |  |
| IA | 37 | 08/07/2026 | Atendimento. Divulgação dos resultados da G1 até 09/07 | Aula |  | results | bloco-22=results | bloco-22=results | review | 4:office_hours>review(proxima=assessment) | bloco-22=review |  ->  |  |
| IA | 38 | 13/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-23=assessment | bloco-23=assessment | assessment | 2:atividade=prova | bloco-23=assessment |  ->  |  |
| IA | 39 | 15/07/2026 | {kind=g2} | Aula | g2 | g2 | bloco-24=assessment | bloco-24=assessment | assessment | 3:g2+rotulo_vazio(P1c) | bloco-24=assessment |  ->  |  |
| LR | 0 | 03/08/2026 | Apresentação da disciplina | Aula |  | class | bloco-01=class | bloco-01=class | overview | 4:overview | bloco-01=overview | unidade-01-nivel-de-aplicacao-configuracao-e-analise-de-protocolos ->  |  |
| LR | 5 | 07/09/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-06=holiday | bloco-06=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-06=holiday |  ->  | legitimo:feriado/suspensao |
| LR | 10 | 12/10/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-10=holiday | bloco-10=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-10=holiday |  ->  | legitimo:feriado/suspensao |
| LR | 13 | 02/11/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-13=holiday | bloco-13=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-13=holiday |  ->  | legitimo:feriado/suspensao |
| LR | 18 | 07/12/2026 | {kind=g2} | Aula | g2 | g2 | bloco-17=assessment | bloco-17=assessment | assessment | 3:g2+rotulo_vazio(P1c) | bloco-17=assessment |  ->  |  |
| MF | 0 | 02/03/2026 | Apresentação da disciplina | Aula |  | class | bloco-01=class | bloco-01=class | overview | 4:overview | bloco-01=overview | unidade-01-metodos-formais ->  |  |
| MF | 13 | 15/04/2026 | Exercícios de revisão | Aula |  | class | bloco-07=review | bloco-07=review | review | 4:review | bloco-07=review |  ->  | legitimo:revisao |
| MF | 14 | 20/04/2026 | Suspensão de aulas {kind=suspension} | Aula | suspension | suspension | bloco-08=suspended | bloco-08=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-08=suspended |  ->  | legitimo:feriado/suspensao |
| MF | 25 | 27/05/2026 | SE Day {kind=event} | Evento Acadêmico | event | event | bloco-14=academic_event | bloco-14=academic_event | academic_event | 2:atividade=evento | bloco-14=academic_event |  ->  |  |
| MF | 33 | 24/06/2026 | Suspensão: jogo Copa do Mundo {kind=suspension} | Aula | suspension | suspension | bloco-17=suspended | bloco-17=suspended | suspended | 3:suspension_metadado>4:suspended(P1b) | bloco-17=suspended |  ->  | legitimo:feriado/suspensao |
| MF | 35 | 01/07/2026 | Exercícios de revisão | Aula |  | class | bloco-19=review | bloco-19=review | review | 4:review | bloco-19=review |  ->  | legitimo:revisao |
| MF | 37 | 08/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-21=makeup | bloco-21=makeup | makeup | 2:atividade=substituicao(P1a) | bloco-21=makeup |  ->  |  |
| MF | 39 | 15/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-23=assessment | bloco-23=assessment | assessment | 2:atividade=prova | bloco-23=assessment |  ->  |  |
| SO | 0 | 03/03/2026 | Apresentação da disciplina e Introdução | Aula |  | class | bloco-01=overview | bloco-01=overview | overview | 4:overview | bloco-01=overview |  ->  | legitimo:overview |
| SO | 1 | 05/03/2026 | Introdução | Aula |  | class | bloco-02=overview | bloco-02=overview | overview | 4:overview | bloco-02=overview |  ->  | legitimo:overview |
| SO | 9 | 02/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-05=holiday | bloco-05=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-05=holiday |  ->  | legitimo:feriado/suspensao |
| SO | 14 | 21/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-08=holiday | bloco-08=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-08=holiday |  ->  | legitimo:feriado/suspensao |
| SO | 17 | 30/04/2026 | Duvidas Prova | Aula |  | class | bloco-10=office_hours | bloco-10=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-10=review |  ->  | alvo:duvidas-office_hours |
| SO | 18 | 05/05/2026 | Duvidas TP1, duvidas p1 | Aula |  | class | bloco-11=office_hours | bloco-11=office_hours | review | 4:office_hours>review(proxima=assessment) | bloco-11=review |  ->  | alvo:duvidas-office_hours |
| SO | 27 | 04/06/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-17=holiday | bloco-17=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-17=holiday |  ->  | legitimo:feriado/suspensao |
| SO | 34 | 30/06/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-22=makeup | bloco-22=makeup | makeup | 2:atividade=substituicao(P1a) | bloco-22=makeup |  ->  |  |
| SO | 38 | 14/07/2026 | Prova G2 {kind=g2} | Aula | g2 | g2 | bloco-26=assessment | bloco-26=assessment | assessment | 3:g2+rotulo_prova | bloco-26=assessment |  ->  |  |
| SO | 39 | 16/07/2026 | {kind=g2} | Aula | g2 | g2 | bloco-27=assessment | bloco-27=assessment | assessment | 3:g2+rotulo_vazio(P1c) | bloco-27=assessment |  ->  |  |
| TCC | 9 | 03/04/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-07=holiday | bloco-07=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-07=holiday |  ->  | legitimo:feriado/suspensao |
| TCC | 17 | 01/05/2026 | Feriado {kind=suspension} | Aula | suspension | suspension | bloco-15=holiday | bloco-15=holiday | holiday | 3:suspension_metadado>4:holiday(P1b) | bloco-15=holiday |  ->  | legitimo:feriado/suspensao |
| TCC | 18 | 06/05/2026 | Revisão para prova P1 | Aula |  | class | bloco-16=review | bloco-16=review | review | 4:review | bloco-16=review |  ->  | legitimo:revisao |
| TCC | 24 | 27/05/2026 | SE DAY {kind=event} | Evento Acadêmico | event | event | bloco-20=academic_event | bloco-20=academic_event | academic_event | 2:atividade=evento | bloco-20=academic_event |  ->  |  |
| TCC | 25 | 29/05/2026 | Oficina de problemas - Entrega T2 | Aula |  | class | bloco-21=workshop | bloco-21=workshop | deliverable | 4:workshop>deliverable(cauda-entrega) | bloco-21=deliverable |  ->  | alvo:TCC-oficina |
| TCC | 29 | 12/06/2026 | Oficina de problemas - Entrega T2 {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-25=deliverable | bloco-25=deliverable | deliverable | 2:atividade=trabalho | bloco-25=deliverable |  ->  | alvo:TCC-oficina |
| TCC | 30 | 17/06/2026 | Oficina de problemas {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-26=deliverable | bloco-26=deliverable | deliverable | 2:atividade=trabalho | bloco-26=deliverable |  ->  | alvo:TCC-oficina |
| TCC | 31 | 19/06/2026 | Oficina de problemas {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-27=deliverable | bloco-27=deliverable | deliverable | 2:atividade=trabalho | bloco-27=deliverable |  ->  | alvo:TCC-oficina |
| TCC | 32 | 24/06/2026 | Oficina de problemas {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-28=deliverable | bloco-28=deliverable | deliverable | 2:atividade=trabalho | bloco-28=deliverable |  ->  | alvo:TCC-oficina |
| TCC | 33 | 26/06/2026 | Oficina de problemas - Apresentação {kind=deliverable} | Trabalho | deliverable | deliverable | bloco-29=deliverable | bloco-29=deliverable | deliverable | 2:atividade=trabalho | bloco-29=deliverable |  ->  | alvo:TCC-oficina |
| TCC | 34 | 01/07/2026 | Revisão para Prova P2 | Aula |  | class | bloco-30=review | bloco-30=review | review | 4:review | bloco-30=review |  ->  | legitimo:revisao |
| TCC | 36 | 08/07/2026 | Prova PS {kind=ps} | Prova de Substituição | ps | ps | bloco-32=makeup | bloco-32=makeup | makeup | 2:atividade=substituicao(P1a) | bloco-32=makeup |  ->  |  |
| TCC | 38 | 15/07/2026 | Atendimento a dúvidas {kind=g2} | Aula | g2 | g2 | bloco-34=assessment | bloco-34=assessment | review | 3:g2_metadado>4:office_hours>review(proxima=assessment) | bloco-34=review |  ->  | alvo:TCC-atendimento-g2 |
| TCC | 39 | 17/07/2026 | Prova G2 {kind=g2} | Prova de G2 | g2 | g2 | bloco-35=assessment | bloco-35=assessment | assessment | 2:atividade=prova | bloco-35=assessment |  ->  |  |

## B. Segmentacao (8 cursos vivos)

- CG: vivo x controle 0 grupos; controle x P1adj 29 -> 29, 0 grupos
- ES2: vivo x controle 0 grupos; controle x P1adj 15 -> 15, 0 grupos
- FR: vivo x controle 0 grupos; controle x P1adj 30 -> 30, 0 grupos
- IA: vivo x controle 0 grupos; controle x P1adj 24 -> 24, 0 grupos
- LR: vivo x controle 0 grupos; controle x P1adj 17 -> 17, 0 grupos
- MF: vivo x controle 0 grupos; controle x P1adj 23 -> 23, 0 grupos
- SO: vivo x controle 0 grupos; controle x P1adj 27 -> 27, 0 grupos
- TCC: vivo x controle 0 grupos; controle x P1adj 35 -> 35, 0 grupos

## D. Obsoletos no src da dev

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
- src/builder/timeline/index.py:1268 `def _promote_preexam_reviews` — heuristica de label de sessao 'revisao' (pos-classificacao)
