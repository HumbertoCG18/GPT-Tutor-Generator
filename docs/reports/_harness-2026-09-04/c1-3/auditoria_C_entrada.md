Voce e um professor universitario de computacao auditando uma lista de RELACOES extraidas automaticamente.
Cada relacao diz: "o TERMO pertence ao TOPICO do plano de ensino". O termo foi achado no material do professor, listado sob uma
CATEGORIA (um titulo ou um rotulo com dois-pontos), e o topico foi escolhido por uma regra automatica.

Para CADA relacao, classifique:
  CORRETA      o termo e um conceito, tecnica, ferramenta ou assunto que um aluno estudaria dentro daquele topico
  INCORRETA    o termo pertence a outro assunto; a ligacao com o topico e errada
  RUIDO        o termo nao e um conceito: e frase de prosa, referencia bibliografica, link, descricao de imagem, instrucao
  INDETERMINADA  nao da para decidir so com o que esta aqui

Regras: julgue so com o que esta escrito; nao use ferramentas; nao explique; responda apenas o JSON do schema, uma entrada por id.


RELACOES:
[1] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Base | TERMO: listar alguns elementos específicos de I
[2] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Axioma: | TERMO: o Definição de um conjunto base {/ $\in$ }
[3] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Regra: | TERMO: o Representação gráfica: 1$\ldots$ $\in$ $\in$ [ ]
[4] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Indução | TERMO: se\ h1\in I
[5] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: &= 15 \quad | TERMO: [x \rightarrow 0
[6] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Lógicas de Segunda Ordem | TERMO: HOL
[7] curso MF | TOPICO 2.1 Lógica de Hoare | CATEGORIA: Lógica de Floyd-Hoare | TERMO: Abordagem que usaremos:
[8] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Assinatura | TERMO: Dividida em duas partes:
[9] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Termos | TERMO: Toda constante $\in$ é um termo
[10] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: $$\frac{t1 | TERMO: tn):T{\Sigma}(X)} f \in F
[11] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: LÓGICA DE PREDICADOS | TERMO: L(j)
[12] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Classificação de Conjunto de Fórmulas | TERMO: Seja  $\{A1, \dots, An\}$  um conjunto de fórmulas
[13] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Classificação de Conjunto de Fórmulas | TERMO: $mod(\{p, p \rightarrow q, q\})$
[14] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Proposição | TERMO: O numero 712 é ímpar (F)
[15] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Caso Indutivo | TERMO: R \rangle)$
[16] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Caso base | TERMO: $P(m)$
[17] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Relações | TERMO: Seja uma relação binária R:A$\leftrightarrow$B
[18] curso MF | TOPICO 1.2 Linguagens de Especificação e Lógicas | CATEGORIA: Transitiva | TERMO: yA
[19] curso MF | TOPICO 3.3 Especificação de Propriedades para Sistemas Sequenciais e Concorrentes | CATEGORIA: Propriedades | TERMO: Terminação é uma propriedade de vivacidade
[20] curso MF | TOPICO 3.3 Especificação de Propriedades para Sistemas Sequenciais e Concorrentes | CATEGORIA: Propriedades | TERMO: Um programa termina
[21] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: $F\varphi$  é uma fórmula | TERMO: “future”
[22] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: Observação | TERMO: $\diamond$  e  $\square$
[23] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: eventually  $\diamond a$ | TERMO: The first three states are labeled  $\neg a$
[24] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: CTL - Sintaxe | TERMO: $AX\varphi$  é uma fórmula
[25] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: CTL - Sintaxe | TERMO: $A[\varphi U\psi]$  é uma fórmula
[26] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: A tree diagram illustrating the semantics of the CTL formula EG f. The root node is labele | TERMO: a left child
[27] curso MF | TOPICO 3.2 Fundamentos de Lógicas Temporais | CATEGORIA: LTL versus CTL | TERMO: $FX p$  é válido em ambos modelos
[28] curso MF | TOPICO 2.2 Softwares de Suporte à Verificação Formal de Programas | CATEGORIA: Programação e Verificação com Dafny (Arrays) | TERMO: Quantifiers
[29] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Introdução | TERMO: Dados alocados dinamicamente
[30] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Endereço lógico em segmentação | TERMO: Deslocamento dentro do segmento
[31] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Endereço lógico em segmentação | TERMO: Segmentação é similar a alocação particionada dinâmica
[32] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Tradução de endereço lógico em endereço físico | TERMO: limite: tamanho do segmento
[33] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Implementação da tabela de segmentos | TERMO: Construção de uma tabela de segmentos
[34] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Problemas com implementação da tabela em memória | TERMO: Solução:
[35] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Solução para fragmentação externa | TERMO: Analisar o problema sob dois pontos extremos:
[36] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Solução para fragmentação externa | TERMO: ▶ Similar a página de 1 byte
[37] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: I/O Hardware | TERMO: Common concepts
[38] curso SO | TOPICO 2.2 Controladores dos dispositivos | CATEGORIA: Direct Memory Access | TERMO: Requires DMA controller
[39] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Device Drivers | TERMO: A row of drivers including SCSI device driver
[40] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Network Devices | TERMO: Separates network protocol from network operation
[41] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Network Devices | TERMO: Includes select functionality
[42] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Clocks and Timers | TERMO: Provide current time, elapsed time, timer
[43] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Clocks and Timers | TERMO: Programmable interval timer used for timings, periodic interrupts
[44] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: The diagram illustrates two I/O methods | TERMO: kernel (interrupt handler and hardware)
[45] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Kernel I/O Subsystem | TERMO: To cope with device transfer size mismatch
[46] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: device | TERMO: keyboard
[47] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: device | TERMO: status: idle
[48] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: device | TERMO: status: busy
[49] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: request for disk unit 2 | TERMO: file: xxx
[50] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: request for disk unit 2 | TERMO: file: yyy
[51] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Each record contains pointers to various functions | TERMO: pointer to ioctl function
[52] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: I/O Requests to Hardware Operations | TERMO: Translate name to device representation
[53] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Interrupt Handling | TERMO: which then leads to 'interrupt generated' (rectangle)
[54] curso SO | TOPICO 7.4 Proteção | CATEGORIA: The diagram shows four concentric circles representing protection rings. The innermost cir | TERMO: green
[55] curso SO | TOPICO 2.2 Controladores dos dispositivos | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Compatibilizar velocidades
[56] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Tipos de interfaces (dados) | TERMO: Barramentos:
[57] curso SO | TOPICO 2.2 Controladores dos dispositivos | CATEGORIA: Opcodes separados | TERMO: reg
[58] curso SO | TOPICO 2.2 Controladores dos dispositivos | CATEGORIA: Técnicas para realização de E/S <sup>(1)</sup> | TERMO: Acesso Direto à Memória
[59] curso SO | TOPICO 2.2 Controladores dos dispositivos | CATEGORIA: Técnicas para realização de E/S <sup>(3)</sup> | TERMO: Define a prioridade das interrupções
[60] curso SO | TOPICO 2.2 Controladores dos dispositivos | CATEGORIA: Controlador de DMA | TERMO: Contador e Controle
[61] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivo | TERMO: Representado por um cilindro no topo
[62] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Subsistema (Software) de Entrada e Saída (1) | TERMO: Facilitar a correção de erros gerados pelo dispositivo
[63] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Subsistema (Software) de Entrada e Saída (1) | TERMO: Desempenho
[64] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Software | TERMO: "E/S independente do dispositivo"
[65] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Orientado a caractere | TERMO: stream
[66] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Subsistema (Software) de Entrada e Saída (6) | TERMO: Organiza dados em blocos de tamanho fixo
[67] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Diagrama de árvore de diretórios mostrando a estrutura de nomes de dispositivos em UNIX. O | TERMO: llyS0
[68] curso SO | TOPICO 2.3 Drivers dos dispositivos | CATEGORIA: Dentro da camada de drivers, há cinco boxes rotulados | TERMO: driver floppy
[69] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Segmentação sob Demanda
[70] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Paginação sob Demanda | TERMO: Ocupa menos memória
[71] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: logical memory for user 1 | TERMO: 2 (J)
[72] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: logical memory for user 2 | TERMO: 2 (D)
[73] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: map | TERMO: position
[74] curso SO | TOPICO 3.2 Escalonamento | CATEGORIA: Overhead | TERMO: O tempo depende muito do hardware
[75] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: Figure 3.6 | TERMO: a trace of system events is shown
[76] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: Figure 3.6 | TERMO: and I/O requests
[77] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: Transições de Estados (3) | TERMO: Running to Ready:
[78] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Considerações gerais | TERMO: Memória principal: acessada pela CPU
[79] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Endereço lógico versus endereço físico | TERMO: Endereço físico: endereços enviados para a memória RAM
[80] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Comparison 1 | TERMO: which triggers an Interrupção (Endereço ilegal)
[81] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: send | TERMO: destination
[82] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Endereçamento Indireto (2) | TERMO: Muitos-para-um: útil para interação cliente-servidor
[83] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Comunicação entre Processos (4) | TERMO: Rápida
[84] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Comunicação entre Processos (4) | TERMO: Funcione igualmente em ambientes distribuídos
[85] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Uso de Pipes | TERMO: who | sort | lpr
[86] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: The diagram illustrates the flow of data through a pipeline of programs and their connecti | TERMO: and Program3
[87] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Comunicação Pai-Filho Bi-Direcional | TERMO: Pai fecha descritor de escrita de pipe2
[88] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Escrita e Leitura em Pipes (2) | TERMO: Leitura para descritor fechado retorna valor 0
[89] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: As permissões de acesso também podem ser indicados por 3 dígitos octais, cada um represent | TERMO: Read
[90] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: As permissões de acesso também podem ser indicados por 3 dígitos octais, cada um represent | TERMO: eXecute
[91] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: O diagrama ilustra a criação e execução de três processos | TERMO: Processo A
[92] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: Bloco de Controle do Processo (PCB) | TERMO: Process Control Block
[93] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: Informações de controle do processo (2) | TERMO: Comunicação entre processos:
[94] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Exemplo de paginação (1) | TERMO: Características do sistema:
[95] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Proteção | TERMO: Processos acessam somente suas páginas end. válidos
[96] curso SO | TOPICO 6.1 Políticas básicas | CATEGORIA: Process 2 | TERMO: 5 (P3)
[97] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Necessidade de Armazenamento | TERMO: Grandes quantidades de informação têm de ser armazenadas
[98] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Necessidade de Armazenamento | TERMO: Definição de estruturas (organização, hierarquia, relação entre informação)
[99] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Gerência de Arquivos | TERMO: abrir, fechar – open(), close()
[100] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Permitem estruturar o armazenamento e a recuperação de dados persistentes em um ou mais di | TERMO: discos
[101] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: read
[102] curso SO | TOPICO 7.3 Implementação de sistemas de arquivos | CATEGORIA: - Alocação Contígua | TERMO: Pré-alocação (fragmentação interna)
[103] curso SO | TOPICO 7.3 Implementação de sistemas de arquivos | CATEGORIA: Diagram illustrating contiguous file allocation. A table lists files | TERMO: 3 blocks)
[104] curso SO | TOPICO 7.3 Implementação de sistemas de arquivos | CATEGORIA: Diagram illustrating contiguous file allocation. A table lists files | TERMO: 5 blocks). Below
[105] curso SO | TOPICO 7.3 Implementação de sistemas de arquivos | CATEGORIA: Relação entre Diretórios e i-nodes (2) | TERMO: Passos para alcançar /usr/ast/mbox
[106] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Definição (1) | TERMO: O SO tenta usar o hardware com eficiência
[107] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Diagram illustrating the SSTF disk scheduling algorithm. The horizontal axis represents cy | TERMO: then to 65 (distance 12)
[108] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Diagram illustrating the SSTF disk scheduling algorithm. The horizontal axis represents cy | TERMO: then to 67 (distance 2)
[109] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Diagram illustrating the SSTF disk scheduling algorithm. The horizontal axis represents cy | TERMO: then to 98 (distance 31)
[110] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Diagram illustrating the SSTF disk scheduling algorithm. The horizontal axis represents cy | TERMO: illustrating the shortest seek time at each step
[111] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: SCAN | TERMO: Às vezes chamado de algoritmo Elevator
[112] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: C-SCAN | TERMO: atende requisições durante movimentação
[113] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: C-SCAN | TERMO: ▶ Nenhuma requisição é atendida na viagem de volta
[114] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Diagram illustrating the C-LOOK disk scheduling algorithm. A horizontal axis represents th | TERMO: moves right to 65
[115] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Diagram illustrating the C-LOOK disk scheduling algorithm. A horizontal axis represents th | TERMO: moves left to 14
[116] curso SO | TOPICO 3.2 Escalonamento | CATEGORIA: Definição | TERMO: Muda do estado esperando para pronto
[117] curso SO | TOPICO 3.2 Escalonamento | CATEGORIA: Dispatcher | TERMO: Latência de Despacho
[118] curso SO | TOPICO 3.2 Escalonamento | CATEGORIA: Critérios de Otimização | TERMO: Minimizar o tempo de processamento
[119] curso SO | TOPICO 3.2 Escalonamento | CATEGORIA: Critérios de Otimização | TERMO: Minimizar o tempo de espera
[120] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Gantt chart illustrating FCFS scheduling for four processes | TERMO: UCP
[121] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Gantt chart illustrating FCFS scheduling for four processes | TERMO: Processo A
[122] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Gantt chart illustrating SJF scheduling for four processes | TERMO: 25 for A
[123] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Exemplo de Programa Multithread (1) | TERMO: Processamento assíncrono (salvamento periódico)
[124] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Estado de execução | TERMO: ready
[125] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Diagram illustrating four process/thread configurations | TERMO: 1. one process
[126] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Diagram illustrating four process/thread configurations | TERMO: 3. multiple processes
[127] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Threads vs Processos (1) | TERMO: Propriedade de recursos:
[128] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Threads vs Processos (2) | TERMO: Tradicionalmente o processo está associado a:
[129] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Bibliotecas de Threads (2) | TERMO: Incluir o arquivo pthreads.h
[130] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Bibliotecas de Threads (2) | TERMO: “Linkar” a biblioteca lpthread
[131] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Bibliotecas de Threads <sup>(1)</sup> | TERMO: libpthread (padrão POSIX/IEEE 1003.1c)
[132] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Sistema de Computação | TERMO: Programas de aplicação
[133] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Sistema de Computação | TERMO: Usuários
[134] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Definição (1) | TERMO: Gerenciamento de recursos
[135] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Organização Típica | TERMO: Sistema de Arquivos
[136] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: The diagram shows a single vertical stack of components. At the top is a green box labeled | TERMO: 'VFS
[137] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: The diagram shows a single vertical stack of components. At the top is a green box labeled | TERMO: 'IPC
[138] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: The diagram shows a single vertical stack of components. At the top is a green box labeled | TERMO: File System'
[139] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: The diagram shows a single vertical stack of components. At the top is a green box labeled | TERMO: Virtual Memory'
[140] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: The diagram shows a single vertical stack of components. At the top is a green box labeled | TERMO: Dispatcher
[141] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Sistemas Mainframes | TERMO: Arquitetura de hardware complexa
[142] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Sistemas Mainframes | TERMO: Trabalham em multimodo (usualmente “batch” e “time- sharing”)
[143] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Pode rodar diferentes tipos de S.O | TERMO: UNIX
[144] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Sistemas Paralelos(1) | TERMO: Principais vantagens:
[145] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Multiprogramação (cont.) | TERMO: Maximização do uso do processador e da memória
[146] curso SO | TOPICO 1.1 Serviços dos sistemas operacionais | CATEGORIA: Multiprogramação (cont.) | TERMO: Mecanismo de interrupção (sinalização de eventos)
[147] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Socket API | TERMO: ❖ unreliable datagram
[148] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Client | TERMO: Create a TCP socket
[149] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Server | TERMO: c. Close the connection
[150] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Closing a Connection | TERMO: close() used to delimit communication
[151] curso SO | TOPICO 4.2 Comunicação e sincronização de processos | CATEGORIA: Cria datagrama para enviar ao cliente | TERMO: sendData.length
[152] curso SO | TOPICO 3.1 Conceitos básicos | CATEGORIA: Pronto | TERMO: processo está apto a executar
[153] curso SO | TOPICO 3.3 Algoritmos de escalonamento | CATEGORIA: Quantum = 10, quando aplicável. Ordem de chegada | TERMO: P1
[154] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Algoritmo k-NN | TERMO: Etapa de Generalização:
[155] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Características | TERMO: partem de soluções propostas e tentam melhorá-las
[156] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Passo 3 | TERMO: Logo após a geração de uma população
[157] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Genético: Crossover | TERMO: O operador genético crossover é responsável por
[158] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Genético: Crossover | TERMO: Há vários tipos de cruzamento:
[159] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Indução Top-Down | TERMO: Determinar quando parar de particionar
[160] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Como filtrar os dados com base em um atributo? | TERMO: Múltipla
[161] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Atributos Contínuos: Calculando o Índice GINI | TERMO: Para a eficiência computacional: para cada atributo,
[162] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Vantagens e Desvantagens de Árvores de Decisão | TERMO: Sujeitas a overfitting (super-ajuste aos dados)
[163] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Espaço de Hipóteses | TERMO: Intersecção de hiper-retângulos é vazia
[164] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Espaço de Hipóteses | TERMO: União é o espaço total
[165] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Árvores de Decisão para Problemas de Regressão | TERMO: Árvores de Modelos
[166] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Exemplos de Algoritmos | TERMO: Divisões sempre binárias (agrega categorias)
[167] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: Grupos | TERMO: diferentes níveis de refinamento)
[168] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: - Etapas: | TERMO: validação e
[169] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: - Proximidade: Medidas para Atributos Quantitativos: | TERMO: Medidas de Similaridade:
[170] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: interpretação | TERMO: indicando a natureza do grupo
[171] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates two types of clustering. On the left, a vertical line separates tw | TERMO: a group of four blue dots
[172] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates the agglomerative clustering process. It shows a hierarchy of clus | TERMO: one containing points 1 and 2
[173] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: Diagrama de agrupamento hierárquico aglomerativo. O diagrama mostra a formação de clusters | TERMO: o cluster '1
[174] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: A dendrogram illustrating the hierarchical clustering of elements 1 through 6. The x-axis  | TERMO: the cluster {1
[175] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: Podem corresponder a taxonomias úteis. Exemplos em ciências biológicas | TERMO: e.g
[176] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: Podem corresponder a taxonomias úteis. Exemplos em ciências biológicas | TERMO: reconstrução filogenética
[177] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates a hierarchical clustering process. At the top, two clusters are sh | TERMO: C4
[178] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates a hierarchical clustering process. At the top, two clusters are sh | TERMO: C6
[179] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates a hierarchical clustering process. At the top level, three cluster | TERMO: 4). Below these clusters
[180] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates a hierarchical clustering process. At the bottom, seven individual | TERMO: 3). Above these
[181] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The diagram illustrates a hierarchical clustering process. At the bottom, seven individual | TERMO: 4). At the top
[182] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: A dendrogram illustrating hierarchical clustering. The x-axis represents 7 data points, la | TERMO: 3} and two singletons)
[183] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: A seleção pode ser feita pelo seguinte procedimento prático | TERMO: \text{SOMATOTAL}]$
[184] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Fenótipo | TERMO: representa o objeto
[185] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: É interessante notar que o cromossomo pode ser interpretado como um anel formado pela uniã | TERMO: Beasley
[186] curso IA | TOPICO introducao-ao-aprendizado-de-maquina Introdução ao aprendizado de máquina | CATEGORIA: A line graph showing three time series | TERMO: 'Série aleatória (esquerda)' (red line)
[187] curso IA | TOPICO introducao-ao-aprendizado-de-maquina Introdução ao aprendizado de máquina | CATEGORIA: Line graph showing three data series | TERMO: and 'Série sazonal (temporada)'
[188] curso IA | TOPICO introducao-ao-aprendizado-de-maquina Introdução ao aprendizado de máquina | CATEGORIA: Caracterização dos Dados | TERMO: Intervalares e racionais: para os quantitativos;
[189] curso IA | TOPICO introducao-ao-aprendizado-de-maquina Introdução ao aprendizado de máquina | CATEGORIA: Bar chart showing the frequency of height categories | TERMO: and Medio (2)
[190] curso IA | TOPICO metricas-de-avaliacao Métricas de Avaliação | CATEGORIA: É sempre uma matriz quadrada | TERMO: os resultados gerados pelo preditor
[191] curso IA | TOPICO metricas-de-avaliacao Métricas de Avaliação | CATEGORIA: Classificação: Accuracy | TERMO: FP (Falso-Positivo): 2
[192] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Precisa de uma função sucessor que gera uma solução próxima à atual | TERMO: introduz uma “perturbação” (modificação) na solução atual
[193] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Hill-Climbing | TERMO: Vizinhos ao estado atual
[194] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Hill-Climbing | TERMO: Boa estratégia, quando há muitos sucessores (ex: milhares)
[195] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Simulated Annealing | TERMO: $\Delta E$ : é chamado de variação de energia
[196] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Simulated Annealing | TERMO: O método termina quando
[197] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Algoritmo Simulated Annealing | TERMO: ausência de melhora
[198] curso IA | TOPICO introducao-a-agentes-em-ambientes-deterministicos Introdução a agentes em ambientes determinísticos | CATEGORIA: | <b>Atuadores | TERMO: escrita em arquivo
[199] curso IA | TOPICO introducao-a-agentes-em-ambientes-deterministicos Introdução a agentes em ambientes determinísticos | CATEGORIA: Agente baseado em objetivos | TERMO: Características
[200] curso IA | TOPICO introducao-a-agentes-em-ambientes-deterministicos Introdução a agentes em ambientes determinísticos | CATEGORIA: Agente baseado em utilidade | TERMO: Compara diferentes alternativas
[201] curso IA | TOPICO introducao-a-agentes-em-ambientes-deterministicos Introdução a agentes em ambientes determinísticos | CATEGORIA: Agente baseado em utilidade | TERMO: Escolhe a opção que maximiza a utilidade esperada
[202] curso IA | TOPICO introducao-a-agentes-em-ambientes-deterministicos Introdução a agentes em ambientes determinísticos | CATEGORIA: - Vantagens | TERMO: É adequado para ambientes dinâmicos e complexos
[203] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: Agentes e Algoritmos de Busca | TERMO: ▶ Aspirar sujeira ou
[204] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: Estados de mundo | TERMO: ▶ [B,Suja,Suja]
[205] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: Estados de mundo | TERMO: ▶ [B,Limpa,Suja]
[206] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: ![A search tree diagram for a vacuum cleaner problem. The root node is [A,Suja,Suja]. It h | TERMO: Suja
[207] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: ![A search tree diagram for a vacuum cleaner problem. The root node is [A,Suja,Suja]. It h | TERMO: Limpa] (labeled 'aspirar')
[208] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: ![A search tree diagram for a vacuum cleaner problem. The root node is [A,Suja,Suja]. It h | TERMO: [B
[209] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: ![A search tree diagram for a vacuum cleaner problem. The root node is [A,Suja,Suja]. It h | TERMO: Suja] (labeled 'direita')
[210] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: ▶ custo do caminho | TERMO: cada passo custa 1
[211] curso IA | TOPICO representacao-de-problemas Representação de problemas | CATEGORIA: ▶ Se o problema fosse estendido para mais salas, da seguinte forma | TERMO: 2 salas no térreo
[212] curso IA | TOPICO introducao-ao-aprendizado-de-maquina Introdução ao aprendizado de máquina | CATEGORIA: Deep Learning | TERMO: Capacidade de trabalhar com grandes volumes de dados
[213] curso IA | TOPICO paradigmas-de-aprendizado Paradigmas de aprendizado | CATEGORIA: A pile of mixed-colored potatoes | TERMO: and purple
[214] curso IA | TOPICO paradigmas-de-aprendizado Paradigmas de aprendizado | CATEGORIA: Three separate groups of potatoes | TERMO: illustrating the result of clustering
[215] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: X | TERMO: \dots
[216] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: W | TERMO: wp$
[217] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Diagrama de dois neurônios biológicos conectados por uma sinapse. O neurônio à esquerda po | TERMO: 'Corpo celular' (o corpo central do neurônio)
[218] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: The diagram illustrates the internal structure of an artificial neuron j. On the left, a v | TERMO: followed by three vertical dots
[219] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: The diagram illustrates the internal structure of an artificial neuron j. On the left, a v | TERMO: $w{3j}$
[220] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: The diagram illustrates the internal structure of an artificial neuron j. On the left, a v | TERMO: representing the final output of the neuron
[221] curso IA | TOPICO busca-adversaria Busca Adversária | CATEGORIA: Teoria dos Jogos: Algoritmos por turnos | TERMO: “Informações perfeitas”
[222] curso IA | TOPICO busca-adversaria Busca Adversária | CATEGORIA: Função sucessor | TERMO: estado)
[223] curso IA | TOPICO busca-adversaria Busca Adversária | CATEGORIA: The diagram shows a minimax search tree with four levels. The levels are labeled MAX, MIN, | TERMO: going to the left MIN node
[224] curso IA | TOPICO busca-adversaria Busca Adversária | CATEGORIA: Diagram illustrating a minimax search tree for a 3x3 tic-tac-toe game. The tree has four l | TERMO: Level 2 (oponente (MIN))
[225] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: From hidden nodes 1, 2, 3 to hidden nodes 4, 5 | TERMO: $W{51}$  to node 5
[226] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: From hidden nodes 1, 2, 3 to hidden nodes 4, 5 | TERMO: $W{42}$  to node 4
[227] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: From hidden nodes 4, 5 to output nodes 6, 7 | TERMO: $W{75}$  to node 7
[228] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: From hidden nodes 4, 5 to output nodes 6, 7 | TERMO: $W{40}$  to node 4
[229] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Como definir a topologia de uma rede MLP? | TERMO: A topologia mais simples possui 3 camadas:
[230] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Diagrama de uma rede MLP com 3 camadas | TERMO: oculta e saída
[231] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Output Layer | TERMO: labeled  $y1
[232] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Diagram of an Iris flower with labels for its parts | TERMO: and Cálice (conjunto de sépalas)
[233] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Below the layers, the dimensions are labeled | TERMO: $n$  for the input layer
[234] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Below the layers, the dimensions are labeled | TERMO: $p$  for the hidden layer
[235] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: X é o conjunto de entrada | TERMO: xZ\}$
[236] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: D é o conjunto de saídas desejadas | TERMO: dM\}$
[237] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Camada Oculta | TERMO: Gradiente Neurônio 3: 0.03803417896970686
[238] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Operações Genéticas | TERMO: Operadores baseados em permutações
[239] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: Crossover PBX | TERMO: Da mesma forma, selecione aleatoriamente  $n$  posições
[240] curso IA | TOPICO problemas-de-otimizacao Problemas de Otimização | CATEGORIA: - Da mesma forma, copia G pois está na mesma posição de C (cromossomo 2) | TERMO: Filho 1.....: A           C                   G
[241] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Inclinação e Pesos | TERMO: Quando se tem duas entradas
[242] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: 3 classes | TERMO: Iris-versicolor
[243] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: A scatter plot showing the distribution of three Iris species based on four attributes | TERMO: petal\length
[244] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Diagram illustrating a neural network structure for Iris plant classification. The input l | TERMO: $x1$  (Comprimento da sépala)
[245] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Grid 3 | TERMO: The first column is green
[246] curso IA | TOPICO modelos-preditivos Modelos Preditivos | CATEGORIA: Diagram of a single-layer perceptron simulation. A blue circle node contains the value '1' | TERMO: a horizontal arrow points to the right
[247] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: | Clustering algorithm based on ensemble              | Methods for generating the set of  | TERMO: sMCLA
[248] curso IA | TOPICO modelos-descritivos Modelos Descritivos | CATEGORIA: The basic idea of this kind of clustering algorithms is to simulate the changing process o | TERMO: the typical algorithm of the ACO\based
[249] curso IA | TOPICO conceituacao Conceituação | CATEGORIA: Cloudpainter | TERMO: robô criado por Pindar VanArman
[250] curso IA | TOPICO conceituacao Conceituação | CATEGORIA: O estudo de computações que tornam possível perceber, raciocinar e agir | TERMO: Winston
[251] curso IA | TOPICO conceituacao Conceituação | CATEGORIA: Estrutural | TERMO: entre objetos
[252] curso IA | TOPICO subareas-e-disciplinas-afins Subáreas e disciplinas afins | CATEGORIA: A woman wearing glasses and a white sweater is speaking into a microphone, likely recordin | TERMO: 'trophy
[253] curso IA | TOPICO subareas-e-disciplinas-afins Subáreas e disciplinas afins | CATEGORIA: A woman wearing glasses and a white sweater is speaking into a microphone, likely recordin | TERMO: and'
[254] curso IA | TOPICO metricas-de-avaliacao Métricas de Avaliação | CATEGORIA: Como analisar resultados | TERMO: Re e F1
[255] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Service Discovery | TERMO: Serviços necessitam realizar comunicação entre si
[256] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Associated with the arrow are the actions | TERMO: heartbeat()
[257] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: The diagram illustrates the Netflix Eureka architecture across three availability zones | TERMO: us-east-1c
[258] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: The diagram illustrates a system architecture where different frontend applications intera | TERMO: 'Mobile app'
[259] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: State transition diagram for a three-state failure handling protocol | TERMO: Closed
[260] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: State transition diagram for a three-state failure handling protocol | TERMO: Half-Open
[261] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Data patterns | TERMO: 'Aggregate'
[262] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: The diagram illustrates the Docker architecture, divided into three main sections | TERMO: Docker Host
[263] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Client | TERMO: and docker pull
[264] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Registry | TERMO: and Plugins
[265] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: The diagram illustrates the Auth0 authentication flow involving three main components | TERMO: the API Consumer Application
[266] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: 3. Request with JWT | TERMO: including the JWT
[267] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Spring Security | TERMO: Ataques de “Cross Site Request Forgery” (CSRF)
[268] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Autenticação | TERMO: Java Authentication and Authorization Service (JAAS)
[269] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Arquitetura Orientada a Mensagens | TERMO: Arquitetura para aplicações distribuídas
[270] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Arquitetura Publish/Subscribe | TERMO: (2) assinar eventos
[271] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Implementação | TERMO: Cenário de comunicação:
[272] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Implementação | TERMO: Assíncrona
[273] curso ES2 | TOPICO 1.1 Conceito de arquitetura de software | CATEGORIA: Aplicações Corporativas | TERMO: Aplicações de serviços
[274] curso ES2 | TOPICO 1.1 Conceito de arquitetura de software | CATEGORIA: Arquitetura de Software | TERMO: Descrição dos subsistemas mais críticos
[275] curso ES2 | TOPICO 1.1 Conceito de arquitetura de software | CATEGORIA: Arquitetura de Software | TERMO: Aplicação “stand alone” (executa em um PC)
[276] curso ES2 | TOPICO 1.1 Conceito de arquitetura de software | CATEGORIA: Arquitetura de Software | TERMO: Log de eventos
[277] curso ES2 | TOPICO 1.4 Estratégias de Construção de Arquitetura | CATEGORIA: Component 1 | TERMO: S2
[278] curso ES2 | TOPICO 1.4 Estratégias de Construção de Arquitetura | CATEGORIA: Component 1 | TERMO: and S3
[279] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Onion Architecture diagram showing concentric layers | TERMO: Object Services
[280] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Onion Architecture diagram showing concentric layers | TERMO: UserSession
[281] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Diagram of Hexagonal Architecture showing the Business Model at the center, surrounded by  | TERMO: SOAP Server
[282] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: The diagram illustrates the user journey for Pedro, a user interacting with a system. The  | TERMO: Serviços
[283] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: System Status | TERMO: 'default'
[284] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Instances currently registered with Eureka | TERMO: and 'Status'. It shows 'No instances available'
[285] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Route | TERMO: é composto por um id
[286] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Diagrama de arquitetura mostrando o fluxo de dados entre componentes | TERMO: Cliente
[287] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: Topic | TERMO: ideal para comunicação multicast
[288] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Arquitetura orientada a serviços | TERMO: Arquiteturas SOA compreendem 5 elementos:
[289] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Arquitetura orientada a serviços | TERMO: Prover conectividade
[290] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Arquitetura orientada a serviços | TERMO: Lidar com segurança
[291] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Arquitetura orientada a serviços | TERMO: Gerenciamento de serviços
[292] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Arquitetura orientada a serviços | TERMO: Monitoramento e logging
[293] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Web Services | TERMO: Trabalham sobre o modelo de requisição/resposta
[294] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: HTTP | TERMO: 2 (RFC [7540](#))
[295] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: REST | TERMO: Identificação dos recursos através de URIs;
[296] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: REST | TERMO: DELETE: remove a coleção inteira
[297] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: REST | TERMO: DELETE: remove o elemento da coleção
[298] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: - Dois padrões de web services/APIs | TERMO: Usam REST ou qualquer outra coisa
[299] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: - Dois padrões de web services/APIs | TERMO: Usam JSON para transferência de dados
[300] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Arquitetura em camadas lógicas | TERMO: Negócio
[301] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: - Vantagens | TERMO: Simples de implementar se comparada com outras abordagens
[302] curso ES2 | TOPICO 1.3 Estilos e padrões arquiteturais | CATEGORIA: Camada Física Média | TERMO: que contém a LogicaSistFuncionarios (ícone de documento)
[303] curso ES2 | TOPICO 1.5 Estudo de caso: arquitetura orientada a microsserviços | CATEGORIA: O diagrama ilustra a arquitetura de um aplicativo de comércio eletrônico monolítico. No to | TERMO: 'Payment'
[304] curso TCC | TOPICO 4.7 Intratabilidade | CATEGORIA: Diagram illustrating a perfect matching between three groups | TERMO: Y (enfermeiros)
[305] curso TCC | TOPICO 4.7 Intratabilidade | CATEGORIA: The diagram shows three columns of circles representing the sets X, Y, and Z. Column X is  | TERMO: x1 to y1 to z1
[306] curso TCC | TOPICO 1.2 Argumento Diagonal de Cantor e Conjuntos Incontáveis | CATEGORIA: Significado | TERMO: $\mathbb{R}$  é “maior” que  $\mathbb{N}$
[307] curso TCC | TOPICO 1.2 Argumento Diagonal de Cantor e Conjuntos Incontáveis | CATEGORIA: Consequência Fundamental | TERMO: Existem apenas  $\aleph0$  programas (strings finitas)
[308] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Trabalharemos com funções  $f | TERMO: onde:
[309] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Notação | TERMO: $\vec{x}$  denota  $(x1, x2, \dots, xk)$
[310] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Axiomas de Peano (simplificado) | TERMO: 1 0 é um número natural
[311] curso TCC | TOPICO 1.2 Argumento Diagonal de Cantor e Conjuntos Incontáveis | CATEGORIA: “Prova” | TERMO: Composição de funções totais é total
[312] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Ideia | TERMO: incrementa o resto
[313] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Aritmética básica | TERMO: $\times$
[314] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Aritmética básica | TERMO: $\dot{-}$
[315] curso TCC | TOPICO 1.3 Funções Recursivas Primitivas e Funções Recursivas Parciais | CATEGORIA: Isto é | TERMO: então  $a \circ b \in S$
[316] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: “Se está em  $q1$  lendo  $a$ | TERMO: move à direita
[317] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Convenções | TERMO: Estado de aceitação: círculo duplo
[318] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Convenções | TERMO: Transições: setas rotuladas  $a \rightarrow b, D$
[319] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Transições | TERMO: setas rotuladas  $a \rightarrow b
[320] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Transições | TERMO: D$
[321] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: q<sub>acc</sub> | TERMO: Estado de aceitação
[322] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: De q<sub>1</sub> para q<sub>acc</sub> | TERMO: L$
[323] curso TCC | TOPICO 2.2 Linguagens Reconhecíveis e Decidíveis | CATEGORIA: Interseção | TERMO: então  $L1 \cap L2$  é r.e
[324] curso TCC | TOPICO 2.5 Máquinas de Turing Universais | CATEGORIA: Finitos estados | TERMO: qn$
[325] curso TCC | TOPICO 2.5 Máquinas de Turing Universais | CATEGORIA: 4 Atualize | TERMO: posição
[326] curso TCC | TOPICO 2.5 Máquinas de Turing Universais | CATEGORIA: 4 Atualize | TERMO: estado na Fita 3
[327] curso TCC | TOPICO 2.4 Conjectura de Church-Turing | CATEGORIA: Evidências | TERMO: Máquinas de Post
[328] curso TCC | TOPICO 3.1 Prova da Indecidibilidade do Problema da Parada | CATEGORIA: Função de Parada | TERMO: 0 caso contrário
[329] curso TCC | TOPICO 2.3 Variações de Máquinas de Turing | CATEGORIA: Consequência para Complexidade | TERMO: Para computabilidade:  $\text{MTN} \equiv \text{MTD}$
[330] curso TCC | TOPICO 2.3 Variações de Máquinas de Turing | CATEGORIA: Demonstração de Equivalência | TERMO: Utilize duas fitas
[331] curso TCC | TOPICO 3.2 Entscheidungsproblem e Introdução à Reducibilidade de Problemas | CATEGORIA: Construa redução  $f$ | TERMO: dado  $\langle M
[332] curso TCC | TOPICO 2.2 Linguagens Reconhecíveis e Decidíveis | CATEGORIA: Decidíveis | TERMO: $E{DFA}$
[333] curso TCC | TOPICO 2.4 Conjectura de Church-Turing | CATEGORIA: Alonzo Church (1903–1995) | TERMO: Sua prova foi publicada meses antes de Turing
[334] curso TCC | TOPICO 3.2 Entscheidungsproblem e Introdução à Reducibilidade de Problemas | CATEGORIA: Predicados de estado | TERMO: $Qi(t)$  — “no tempo  $t$
[335] curso TCC | TOPICO 3.3 Decidibilidade de Teorias Lógicas | CATEGORIA: Exemplos Decidíveis | TERMO: Lógica Proposicional: tabelas-verdade, DPLL, SAT solvers
[336] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Alfabeto | TERMO: \sqcup\}$
[337] curso TCC | TOPICO 3.4 Teoremas de Gödel | CATEGORIA: Caso 1: Suponha $S \vdash G$ | TERMO: Isso significa que  $S$  prova uma falsidade
[338] curso TCC | TOPICO 3.4 Teoremas de Gödel | CATEGORIA: Exemplos de Sentenças Indecidíveis | TERMO: A própria sentença de Gödel  $G$
[339] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: Hierarquias Estritas Estabelecidas | TERMO: $P \subsetneq \text{EXPTIME}$  (tempo: gaps hierárquicos)
[340] curso TCC | TOPICO 4.7 Intratabilidade | CATEGORIA: Evidências de Intratabilidade | TERMO: 2 Problema é PSPACE-hard
[341] curso TCC | TOPICO 4.5 Classe NP | CATEGORIA: NP-complete | TERMO: SAT
[342] curso TCC | TOPICO 1.2 Argumento Diagonal de Cantor e Conjuntos Incontáveis | CATEGORIA: Prova | TERMO: Compute-se  $f(w)$  em tempo polinomial e
[343] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: ![Figura | TERMO: C e D
[344] curso CG | TOPICO 5.1 Transformações Geométricas e coordenadas homogêneas 2D | CATEGORIA: Translação X | TERMO: Translação Y: 0
[345] curso CG | TOPICO 2.2 Operações com vetores | CATEGORIA: o produto vetorial ![Figura | TERMO: z2) onde z2 é negativo
[346] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: ![Figura | TERMO: um cubo azul com um bule de chá
[347] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: ![Figura | TERMO: um segmento vertical íngreme
[348] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: ![Figura | TERMO: Desenha()
[349] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: ![Figura | TERMO: no frame 50
[350] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: ![Figura | TERMO: C (inferior esquerdo)
[351] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: Curvas Paramétricas | TERMO: t: tempo decorrido
[352] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: Curvas Paramétricas | TERMO: Chamadas de Interpolação, aproximação ou composição ponderada
[353] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: Curvas Paramétricas | TERMO: Ponto Inicial + Vetor colocado no ponto
[354] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: Curva Bèzier | TERMO: Formas alternativas de traçado
[355] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: Curvas Bèzier | TERMO: A derivada é igual nas duas curvas
[356] curso CG | TOPICO 7.1 Formas de Representação | CATEGORIA: Curva Hermite | TERMO: Dois pontos de controle, P0 e P3
[357] curso CG | TOPICO 6.4 Algoritmos de Remoção de Elementos Ocultos | CATEGORIA: Algoritmo do Pintor | TERMO: n Solução para o problema da ambiguidade
[358] curso CG | TOPICO 2.2 Operações com vetores | CATEGORIA: Vetores | TERMO: Definem uma direção
[359] curso CG | TOPICO 2.2 Operações com vetores | CATEGORIA: • Operações | TERMO: Produto Vetorial
[360] curso CG | TOPICO 2.1 Entidades geométricas | CATEGORIA: Retas | TERMO: Equação paramétrica da reta
[361] curso CG | TOPICO 2.3 Algoritmos de detecção e cálculo de intersecção | CATEGORIA: int intersec2d | TERMO: Ponto k
[362] curso CG | TOPICO 2.3 Algoritmos de detecção e cálculo de intersecção | CATEGORIA: int intersec2d | TERMO: Ponto n
[363] curso FR | TOPICO 1.3 Conceito de protocolo de redes pessoais, locais, metropolitanas e de longa distância | CATEGORIA: Protocolos de Comunicação | TERMO: Para um protocolo funcionar é necessário que:
[364] curso FR | TOPICO 1.2 Modelos OSI e TCP/IP | CATEGORIA: OSI - Camada de Transporte | TERMO: erros que entrega mensagens ou bytes ordem enviada
[365] curso FR | TOPICO 1.2 Modelos OSI e TCP/IP | CATEGORIA: ● Define um formato de pacote oficial e um protocolo chamado IP (Internet Protocol) | TERMO: Importante função de roteamento
[366] curso FR | TOPICO 6.1 Classificação e topologias de redes de computadores | CATEGORIA: Redes de difusão | TERMO: Formas de endereçamento:
[367] curso FR | TOPICO 6.1 Classificação e topologias de redes de computadores | CATEGORIA: Redes de difusão | TERMO: Unicast
[368] curso FR | TOPICO 1.3 Conceito de protocolo de redes pessoais, locais, metropolitanas e de longa distância | CATEGORIA: Redes Locais (LAN) | TERMO: Local Area Network (LAN)
[369] curso FR | TOPICO 1.3 Conceito de protocolo de redes pessoais, locais, metropolitanas e de longa distância | CATEGORIA: Redes Locais (LAN) | TERMO: Rede de um laboratório de informática
[370] curso FR | TOPICO 1.3 Conceito de protocolo de redes pessoais, locais, metropolitanas e de longa distância | CATEGORIA: Redes Geograficamente Distribuídas (WAN) | TERMO: Maiores taxas de erros
[371] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Cliente | TERMO: browser que solicita
[372] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: 3xx – Redirecionamento | TERMO: • 301 Moved Permanently
[373] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: 3xx – Redirecionamento | TERMO: 303 See Other
[374] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: 3xx – Redirecionamento | TERMO: • 417 Expectation Failed
[375] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: 3xx – Redirecionamento | TERMO: 201 Created
[376] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Persistência de Conexões | TERMO: HTTP 1.1 é persistente por padrão
[377] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Cookies | TERMO: 4 componentes
[378] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Cookies | TERMO: Rastreamento cross-site
[379] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: • ISPs: universidades, empresas, provedores | TERMO: Desnecessário aumentar largura de banda da instituição
[380] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Age | TERMO: tempo
[381] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Age | TERMO: em segundos
[382] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: HTTPS | TERMO: Hyper Text Transfer Protocol Secure
[383] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: • Máquinas são endereçadas por endereços IP | TERMO: www.pucrs.br
[384] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Tradução de nomes | TERMO: Problema:
[385] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Servidores Autoritativos | TERMO: Implementar seu próprio DNS (ex: BIND)
[386] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Pode ter subdomínios | TERMO: mail.google.com
[387] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Pode ter subdomínios | TERMO: aluno.pucrs.br
[388] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Tipos de Registros | TERMO: (foo.com, relay1.bar.foo.com, CNAME)
[389] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Contém um cabeçalho com informações de controle | TERMO: flags
[390] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Registro de Domínio | TERMO: ICANN (Internet Corporation for Assigned Names and Numbers):
[391] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Funcionamento do DHCP | TERMO: distribuição
[392] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Cada endereço concedido tem um lease time | TERMO: vida útil
[393] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Funcionamento do DHCP | TERMO: vencimento (T1/T2)
[394] curso FR | TOPICO 2.3 Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT) | CATEGORIA: Obtenção de nova configuração | TERMO: Todos servidores respondem com OFFER
[395] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Agentes de Usuário | TERMO: Apple Mail
[396] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Comandos SMTP | TERMO: RCPT TO: – Informa o endereço do destinatário
[397] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: 4xx – Erro temporário | TERMO: 451 – Erro de processamento
[398] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: IMAP – Internet Message Access Protocol | TERMO: Funcionamento:
[399] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: IMAP – Internet Message Access Protocol | TERMO: Vantagem: ideal para quem usa vários dispositivos
[400] curso FR | TOPICO 2.4 Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP) | CATEGORIA: Comparação entre IMAP e POP3 | TERMO: Acesso no mesmo local
