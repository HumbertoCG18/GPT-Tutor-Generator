# Declaracao do professor — SO

Para cada CATEGORIA que voce usou nos materiais, escreva o codigo do topico do plano a que os termos listados pertencem, ou SEM. Nao corrija arquivos individuais. Tempo sugerido: ate 30 minutos.

## Topicos do plano
- `1.1` Evolução histórica
- `1.1` Serviços dos sistemas operacionais
- `1.2` Chamadas de sistema
- `1.3` Estudo de casos
- `3.1` Conceitos básicos
- `3.2` Escalonamento
- `3.3` Algoritmos de escalonamento
- `3.4` Estudo de casos
- `4.1` Programas multithreads
- `4.2` Comunicação e sincronização de processos
- `4.3` Primitivas de sincronização
- `4.4` Problemas clássicos
- `4.5` Construções concorrentes de alto nível
- `5.1` Conceitos básicos
- `5.2` Caracterização
- `5.3` Prevenção
- `5.4` Detecção e recuperação
- `6.1` Políticas básicas
- `6.2` Memória virtual
- `6.3` Estudo de casos
- `7.1` Arquivos
- `7.2` Diretórios
- `7.3` Implementação de sistemas de arquivos
- `7.4` Proteção
- `7.5` Segurança
- `7.6` Estudo de casos
- `2.1` Dispositivos de entrada e saída
- `2.2` Controladores dos dispositivos
- `2.3` Drivers dos dispositivos
- `2.4` Estudo de casos

## Categorias

| id | categoria | termos listados sob ela | codigo do topico ou SEM |
|---|---|---|---|
| 1 | Introdução | Um programa é uma coleção de segmentos, ; Código; Dados alocados estaticamente; Dados alocados dinamicamente |  |
| 2 | e.g | procedimentos (funções); bibliotecas; páginas read-only; read-write |  |
| 3 | Diagrama do Espaço de usuário | Um oval contendo quatro retângulos numer; 3 e 4 |  |
| 4 | Endereço lógico em segmentação | Endereço lógico é composto por duas part; Número de segmento; Deslocamento dentro do segmento; Segmentação é similar a alocação partici |  |
| 5 | Tradução de endereço lógico em endereço físico | Tabela de segmentos; Hardware (comparador); Entrada na tabela de segmento:; base: endereço inicial (físico) do segme |  |
| 6 | Implementação da tabela de segmentos | Construção de uma tabela de segmentos; Cada segmento corresponde a uma entrada ; Cada segmento necessita armazenar dois v; Limite e base |  |
| 7 | Implementação da tabela de segmentos via registradores | Cada segmento dois registradores (base e; ▶ Troca de contexto: atualização dos reg |  |
| 8 | Implementação da tabela de segmentos em memória | Tabela de segmentos armazenada em memóri |  |
| 9 | Problemas com implementação da tabela em memória | Problemas similares ao da paginação:; Solução:; Empregar uma TLB; Observação (válida também para a paginaç |  |
| 10 | Physical Address | If the comparison is successful |  |
| 11 | Aspectos de proteção e compartilhamento | Problema associado: |  |
| 12 | Desvantagem da segmentação | Concatenação de segmentos adjacentes; Compactação da memória |  |
| 13 | Solução para fragmentação externa | Analisar o problema sob dois pontos extr; Um processo é um único segmento; Cada byte é um segmento; ▶ Similar a página de 1 byte |  |
| 14 | Segmentação com paginação | Solução se traduz em paginar segmentos |  |
| 15 | The diagram illustrates the mapping from logical to physical addresses | 'p'; and 'd'; with a bracket under 'p d' |  |
| 16 | Chapter 13: I/O Systems | I/O Hardware; Application I/O Interface; Kernel I/O Subsystem; Transforming I/O Requests to Hardware Op |  |
| 17 | I/O Hardware | Incredible variety of I/O devices; Common concepts; Port; Bus (daisy chain or shared direct access |  |
| 18 | Polling | Determines state of device; command-ready; busy; Error |  |
| 19 | Interrupts | Interrupt handler receives interrupts; Maskable to ignore or delay some interru; Interrupt vector to dispatch interrupt t; Based on priority |  |
| 20 | Direct Memory Access | Requires DMA controller |  |
| 21 | CPU memory bus | cache |  |
| 22 | Application I/O Interface | Devices vary in many dimensions; Character-stream or block; Sequential or random-access; Sharable or dedicated |  |
| 23 | Device Drivers | A row of drivers including SCSI device d; keyboard device driver; mouse device driver; PCI bus device driver |  |
| 24 | Device Controllers | A row of controllers including SCSI devi; keyboard device controller; mouse device controller; PCI bus device controller |  |
| 25 | Physical Devices | A row of hardware devices including SCSI; keyboard; mouse; PCI bus |  |
| 26 | Block and Character Devices | Block devices include disk drives; Commands include read, write, seek; Raw I/O or file-system access; Memory-mapped file access possible |  |
| 27 | Network Devices | Separates network protocol from network ; Includes select functionality; Approaches vary widely (pipes, FIFOs, st |  |
| 28 | Approaches vary widely | pipes; FIFOs; streams; queues |  |
| 29 | Clocks and Timers | Provide current time, elapsed time, time; Programmable interval timer used for tim |  |
| 30 | Blocking and Nonblocking I/O | Blocking - process suspended until I/O c; Easy to use and understand; Insufficient for some needs; User interface, data copy (buffered I/O) |  |
| 31 | The diagram illustrates two I/O methods | device driver; interrupt handler; kernel (interrupt handler and hardware); and user (requesting process) |  |
| 32 | Diagram comparing Synchronous and Asynchronous I/O methods across four | requesting process; device driver; interrupt handler; and hardware |  |
| 33 | Kernel I/O Subsystem | Scheduling; To cope with device speed mismatch; To cope with device transfer size mismat; Caching - fast memory holding copy of da |  |
| 34 | device | keyboard; status: idle; laser printer; status: busy |  |
| 35 | request for laser printer | address: 38546; length: 1372 |  |
| 36 | request for disk unit 2 | file: xxx; operation: read; address: 43046; length: 20000 |  |
| 37 | Error Handling | ❑ System error logs hold problem reports |  |
| 38 | I/O Protection | All I/O instructions defined to be privi; I/O must be performed via system calls |  |
| 39 | 2 perform I/O | Inside the kernel |  |
| 40 | 3 return to user | After the I/O is complete; where the user program resumes execution |  |
| 41 | Each record contains pointers to various functions | inode pointer; pointer to read and write functions; pointer to select function; pointer to ioctl function |  |
| 42 | I/O Requests to Hardware Operations | Determine device holding file; Translate name to device representation; Physically read data from disk into buff; Make data available to requesting proces |  |
| 43 | interrupt handler | Responds to interrupts from the device c |  |
| 44 | STREAMS | A STREAM consists of:; STREAM head interfaces with the user pro; driver end interfaces with the device; zero or more STREAM modules between them |  |
| 45 | Performance | I/O a major factor in system performance; Context switches due to interrupts; Data copying; Network traffic especially stressful |  |
| 46 | Character Typing | leading to 'interrupt generated' (rectan |  |
| 47 | State Saving | which then leads to 'interrupt handled' ; which then leads to 'device driver' (rec |  |
| 48 | System Call | which then leads to 'interrupt handled'  |  |
| 49 | Interrupt Handling | which then leads to 'interrupt generated |  |
| 50 | Network Packet Received | leading to 'network adapter' (rectangle) |  |
| 51 | Improving Performance | Reduce number of context switches; Reduce data copying; Use DMA |  |
| 52 | The diagram shows four concentric circles representing protection ring | green; yellow; orange; and red |  |
| 53 | Diagram of protection rings. Four concentric circles represent Ring 0, | green; yellow; orange; and red |  |
| 54 | Dispositivos de Entrada e Saída (1) | Constituídos de 2 partes:; Mecânica; Eletrônica – Controladora ou Adaptadora; Controladora |  |
| 55 | O diagrama ilustra a conexão de dispositivos de entrada e saída a um s | CPU; Memory; Video controller; Keyboard controller |  |
| 56 | Dispositivos de Entrada e Saída (2) | Controladora (cont.); Também tratar o acesso do dispositivo ao; Tarefas típicas; Correção de erros |  |
| 57 | Tipos de interfaces (dados) | Barramentos:; Porta Serial, Porta Paralela, USB, PS/2; PCI, AGP, PCI-E, SCSI, IDE, SATA |  |
| 58 | Mapeamento de Endereços | Mapeamento em espaço de entrada e saída; Instruções especiais da CPU para E/S; Opcodes separados (IN reg, [end16], OUT ; Mapeamento em espaço de memória |  |
| 59 | Opcodes separados | IN reg; [end16]; OUT [end16]; reg |  |
| 60 | Técnicas para realização de E/S <sup>(1)</sup> | Três técnicas usadas:; E/S Programada; Interrupção; Acesso Direto à Memória |  |
| 61 | Técnicas para realização de E/S (2) | E/S Programada; Interação com o dispositivo é responsabi; Ciclo de funcionamento; Envio do comando ao dispositivo |  |
| 62 | Técnicas para realização de E/S <sup>(3)</sup> | E/S Orientada a Interrupção; Requer hardware especial:; Controlador de interrupções:; Identifica o dispositivo que gerou a int |  |
| 63 | Técnicas para realização de E/S (4) | E/S Orientada a Interrupção (cont.) |  |
| 64 | Técnicas para realização de E/S (5) | Acesso direto à memória (DMA); Controlador de DMA:; O processador é liberado para outras tar; Terminando a transferência, o controlado |  |
| 65 | Controlador de DMA | Representado por um retângulo no centro-; contendo subcomponentes: Endereço; Contador e Controle |  |
| 66 | Controlador de disco | Representado por um retângulo no centro-; contendo um subcomponente Buffer |  |
| 67 | Dispositivo | Representado por um cilindro no topo; conectado ao Controlador de disco |  |
| 68 | 3. Dados transferidos | através do Buffer do Controlador de disc; para a Memória principal |  |
| 69 | Subsistema (Software) de Entrada e Saída (1) | Uniformizar o tratamento dos dispositivo; “Esconder” detalhes de mais “baixo nível; Permitir a inclusão de novos dispositivo; Facilitar a correção de erros gerados pe |  |
| 70 | Memória virtual, Sistema de arquivos, and Biblioteca de E/S | Three intermediate layers that handle me; file system operations; and I/O library functions; respectively |  |
| 71 | Subsistema de E/S | The core I/O subsystem layer; which coordinates the data flow |  |
| 72 | Hardware | The bottom layer; representing the physical hardware compo |  |
| 73 | Software | Indicated by a bracket on the right; "E/S independente do dispositivo"; and the "API" layer |  |
| 74 | Subsistema (Software) de Entrada e Saída (4) | Software de E/S de usuário:; Wrappers para chamadas de sistema |  |
| 75 | Subsistema (Software) de Entrada e Saída (5) | E/S independente de dispositivo (a segui; Interface do subsistema de E/S (API); dispositivos “abstratos” de E/S; Dispositivos “abstratos” |  |
| 76 | Orientado a bloco | block device; buffered; random access |  |
| 77 | Orientado a caractere | stream; character device; unbuffered |  |
| 78 | Subsistema (Software) de Entrada e Saída (6) | Interface do subsistema de E/S (cont.); Dispositivos Orientado a bloco; Organiza dados em blocos de tamanho fixo; Acessa diretamente um bloco de dados |  |
| 79 | Subsistema (Software) de Entrada e Saída (7) | Interface do subsistema de E/S (cont.); Dispositivos Orientado a caractere; Operações típicas:; put( ) e get( ) |  |
| 80 | ex | teclado; vídeo; mouse; impressora |  |
| 81 | Subsistema (Software) de Entrada e Saída (8) | Interface do subsistema de E/S (cont.); Dispositivos Orientado a rede; Necessário estabelecimento de conexões; Operações típicas: |  |
| 82 | orientado a conexão | connect( ); accept( ); read( ); write( ) |  |
| 83 | Subsistema (Software) de Entrada e Saída (9) | Software de E/S independente de disposit; Implementa funções gerais comuns a todos; Atribuição uniforme do nome independente; Nome do dispositivo é um string |  |
| 84 | Diagrama de árvore de diretórios mostrando a estrutura de nomes de dis | llyS0; llyS1; llyS2 e llyS3 |  |
| 85 | E/S independente do dispositivo | middle layer; separated by a dashed line |  |
| 86 | Dentro da camada de drivers, há cinco boxes rotulados | driver SCSI; driver EIDE; driver floppy; driver rede e driver teclado |  |
| 87 | Subsistema (Software) de Entrada e Saída (17) | Drivers de dispositivo |  |
| 88 | O diagrama ilustra a arquitetura de software para o subsistema de entr | "Driver IDE"; há ícones representando um disco rígido; uma disquete e um CD-ROM. À direita |  |
| 89 | Subsistema (Software) de Entrada e Saída (18) | Drivers de dispositivo (cont.); Desenvolvidos pelo fabricante do disposi; Vantagens; Facilidade de adicionar novos drivers |  |
| 90 | Capítulo 9: Memória Virtual | Fundamentos; Paginação sob Demanda; Criação de Processos; Substituição de Páginas |  |
| 91 | Fundamentos | Paginação sob demanda; Segmentação sob demanda |  |
| 92 | The diagram illustrates the virtual address space layout. It is a vert | a grey 'stack' segment at the top; a grey 'heap' segment below the blue reg; a grey 'data' segment below the heap |  |
| 93 | The diagram illustrates the memory layout of two processes sharing a c | stack; shared library; heap; data |  |
| 94 | Paginação sob Demanda | Necessita de menos E/S; Ocupa menos memória; Resposta mais rápida; Página é necessária  $\Rightarrow$  refe |  |
| 95 | The diagram illustrates the transfer of a paged memory to contiguous d | indicating they are not used |  |
| 96 | página ausente | SO verifica uma outra tabela para decidi; Referência inválida  $\Rightarrow$  abor; Obtém bloco livre na memória; Traz página do disco para o bloco alocad |  |
| 97 | Criação de Processos | Copy-on-Write (Cópia na Escrita); Arquivos Mapeados na Memória (depois) |  |
| 98 | logical memory for user 1 | 1 (load M); 2 (J) |  |
| 99 | logical memory for user 2 | 1 (B); 2 (D); and 3 (E). Page 1 (B) is highlighted |  |
| 100 | monitor | 1 ($\downarrow$); 2 (D); 3 (H); 4 (load M) |  |
| 101 | physical memory | A large cylinder representing physical m; containing pages B and M |  |
| 102 | Paginação Excessiva (Thrashing) | Baixa utilização da CPU |  |
| 103 | Process A Virtual Memory | Pages 1; with page 1 highlighted in grey) |  |
| 104 | Process B Virtual Memory | Pages 1; with page 1 highlighted in grey) |  |
| 105 | map | mode; position; size |  |
| 106 | Outras Questões – Tamanho da Página | fragmentação; tamanho da tabela; sobrecarga de E/S; localidade |  |
| 107 | ■ Estrutura de programa | Int[128,128] data;; Cade linha é armazenada em uma página; Programa 1 |  |
| 108 | Programação Concorrente (2) | Vantagens:; Desvantagens:; Mais complexa; A aplicação precisa ser reescrita |  |
| 109 | Condição de Corrida (1) | Solução: |  |
| 110 | Quando um processo entra na sua seção crítica, os outros devem esperar | ou seja |  |
| 111 | Soluções para o problema Condição de Corrida | Soluções de Hardware; Inibição de Interrupções; Instrução TSL (apresenta busy wait); Soluções de Software com busy wait |  |
| 112 | OBS | para atualizar uma estrutura de controle |  |
| 113 | Busy Wait | O que essas soluções fazem é:; Consequência: desperdício de tempo de CP; Problema da inversão de prioridade: |  |
| 114 | Definição (2) | A operação P também é comumente referenc; down ou wait; V também é comumente referenciada; up ou signal |  |
| 115 | Exemplo | agora zero |  |
| 116 | Overhead | Ocorre na execução do escalonamento; Tarefa de alternar a CPU entre dois proc; O tempo depende muito do hardware; 1 a 1000 microseg |  |
| 117 | The diagram illustrates a 5-state process model. The states are repres | New; Ready; Running; Blocked |  |
| 118 | Figure 3.6 | Ready (5-35); Running (12-15); Running (22-28); Running (28-31) |  |
| 119 | Transições de Estados (1) | Null to New:; ▶ Novo batch job; ▶ Logon interativo (usuário se conecta a; New to Ready: |  |
| 120 | Transições de Estados (2) | Ready to Running:; Running to Exit:; ▶ Término normal;; ▶ Término do processo pai (em alguns sis |  |
| 121 | Transições de Estados (3) | Running to Ready:; Processo é preemptado pelo S.O; Running to Blocked:; Blocked to Ready: |  |
| 122 | Considerações gerais | Memória principal: acessada pela CPU; Memória secundária: discos; Qualquer sistema operacional tem gerênci; Monotarefa: gerência é simples |  |
| 123 | Memória lógica vs memória física | Memória lógica; É aquela que o processo "enxerga"; Memória física; Implementada pelos circuitos integrados  |  |
| 124 | Endereço lógico versus endereço físico | Endereço lógico: gerado pela CPU (endere; Endereço físico: endereços enviados para; Programas de usuários “vêm” apenas ender |  |
| 125 | Unidade de Gerenciamento de Memória | Memory Management Unit (MMU) |  |
| 126 | Access | Since both comparisons pass |  |
| 127 | Comparison 1 | indicating an illegal address; which triggers an Interrupção (Endereço  |  |
| 128 | Execução de programas | Alocação de um descritor de processos; Amarração de endereços (binding) |  |
| 129 | Amarração de endereços (binding) | Em tempo de compilação; Em tempo de carga; Em tempo de execução; Como traduzir endereço lógico em endereç |  |
| 130 | Carregador absoluto vs carregador relocador | Endereço só é conhecido no momento da ca; ▶ e.g.; procedimento de swapping; Necessidade de traduzir endereços lógico; Relocação é a técnica que fornece essa t |  |
| 131 | Código relocável | Carregador relocador; Código relocável |  |
| 132 | Código absoluto | Carregador absoluto; Endereço de carga; Fixo pelo programa (programador); Qualquer |  |
| 133 | Mecanismos básicos de gerência de memória | ▶ Problema de alocação de memória; A alocação de memória depende de:; Código absoluto versus código relocável; Necessidade de gerenciamento da memória |  |
| 134 | Definição (1) | Sincronização por memória compartilhada; Solução:; ▶ Sincronização por troca de mensagens; O SO tenta usar o hardware com eficiênci |  |
| 135 | Send | destinatário; mensagem; destination; message\buffer |  |
| 136 | Receive | remetente; mensagem; source; message\buffer |  |
| 137 | Primitivas | send (destination, message\buffer); receive (source, message\buffer) |  |
| 138 | Endereçamento Indireto (2) | Relacionamentos entre transmissor e rece; Muitos-para-um: útil para interação clie; Outras questões: |  |
| 139 | Mailbox ownership | no caso de um port; o criador é o dono |  |
| 140 | Sincronização (1) | "Blocking send, blocking receive":; Mecanismo conhecido como "rendezvous" (e; "Nonblocking send, blocking receive": |  |
| 141 | Emissor continua processando normalmente | p.ex; enviando novas mensagens |  |
| 142 | Sincronização (2) | "Nonblocking send, blocking receive" (co; Esquema mais usado |  |
| 143 | Com "blocking receive" o processo receptor pode ficar bloqueado eterna | soluções: uso de timeout; uso de mais de uma fonte |  |
| 144 | Sincronização (3) | "Nonblocking send, nonblocking receive"; Nenhuma parte envolvida na comunicação p |  |
| 145 | Fila | FIFO; Named Pipe |  |
| 146 | Comunicação entre Processos (1) | Processos executam em cápsulas autônomas; Hardware oferece proteção de memória |  |
| 147 | Comunicação entre Processos (2) | dividir tarefas e aumentar a velocidade ; aumentar da capacidade de processamento ; atender a requisições simultâneas; IPC - Inter-Process Communication |  |
| 148 | Comunicação entre Processos (4) | Características desejáveis para IPC; Rápida; Simples de ser utilizada e implementada; Possuir um modelo de sincronização bem d |  |
| 149 | Mecanismos de IPC | Fundamentalmente, existem duas abordagen; Suportar alguma forma de espaço de ender; Shared memory (memória compartilhada); Pipes e Sinais (ambiente centralizado) |  |
| 150 | Tubos (Pipes) (2) | Um pipe tradicional caracteriza-se por s; A capacidade do pipe é limitada |  |
| 151 | Se a escrita sobre um pipe continua mesmo depois dele estar cheio, oco | conseqüentemente; abra espaço no pipe |  |
| 152 | Uso de Pipes | who | sort | lpr; + output of who is input to sort; + output of sort is input to lpr |  |
| 153 | The diagram illustrates the flow of data through a pipeline of program | Program1; Program2; and Program3 |  |
| 154 | Criação de Pipes <sup>(1)</sup> | Um pipe é criado pela chamada de sistema |  |
| 155 | Flow of data | Below the pipe component; indicating the direction of data transfe |  |
| 156 | Comunicação Pai-Filho Bi-Direcional | Pai cria pipe1 e pipe2; Pai fecha descritor de leitura de pipe1; Pai fecha descritor de escrita de pipe2; Filho fecha descritor de escrita de pipe |  |
| 157 | The diagram illustrates the data flow between three processes | who; sort; and lpr |  |
| 158 | Escrita e Leitura em Pipes (2) | Regras aplicadas aos processos escritore; Regras aplicadas aos processos leitores:; Leitura para descritor fechado retorna v |  |
| 159 | O número de bytes que podem ser temporariamente armazenados por um pip | 512B |  |
| 160 | Fila (FIFO, Named Pipe) | As Filas:; persistem além da vida do processo |  |
| 161 | Criação de Filas <sup>(1)</sup> | Uma fila é criada pela chamada de sistem |  |
| 162 | 2º parâmetro | identifica as permissões de acesso; iguais a qualquer arquivo; determinados por OU de grupos de bits |  |
| 163 | As permissões de acesso também podem ser indicados por 3 dígitos octai | Read; Write; eXecute |  |
| 164 | Abertura de Filas (2) | Regras aplicadas na abertura de filas: |  |
| 165 | a opção ONONBLOCK tiver sido indicada no momento da leitura | nesse caso |  |
| 166 | a opção ONONBLOCK tiver sido indicada no momento da escrita | nesse caso |  |
| 167 | Resumo | Um processo é um programa individual em  |  |
| 168 | Os principais estados de um processo são | New; Ready; Running; Blocked e Exit |  |
| 169 | O diagrama ilustra a criação e execução de três processos | Processo A; e fork C; . Enquanto isso; Processo A executa wait C |  |
| 170 | Criação de processos no Linux | exec(): carrega e executa um novo progra |  |
| 171 | exit | termina o processo corrente. Os filhos; se existirem |  |
| 172 | exec | executa um programa; identificado pelo nome de um arquivo exe; passado como argumento |  |
| 173 | Imagem do processo | Nome dado à coleção formada por:; text: código do programa a ser executado |  |
| 174 | Diagrama da imagem do processo na memória, mostrando a disposição das  | stack; heap; data e text |  |
| 175 | Bloco de Controle do Processo (PCB) | Process Control Block |  |
| 176 | Informações típicas do BCP | Prioridade do processo; Localização na memória principal; Identificação dos arquivos abertos; Estado do processo |  |
| 177 | Informações de controle do processo (1) | Informações de escalonamento e estado:; Prioridade; Tempo de espera na fila; Tempo de execução na última fatia de tem |  |
| 178 | Estado do processo | ready; running; suspended |  |
| 179 | Informações de controle do processo (2) | Comunicação entre processos:; Ownership e utilização de recursos:; Arquivos abertos; |  |
| 180 | The diagram illustrates the mapping of logical pages to physical frame | Page 0 maps to Frame 1; Page 1 maps to Frame 3; Page 2 maps to Frame 5 |  |
| 181 | Endereço lógico | Endereço lógico é dividido em duas compo; Número da página; Deslocamento dentro de uma página |  |
| 182 | Exemplo de paginação (1) | Características do sistema:; Memória física: 64 kbytes (16 bits); Paginação:; Deslocamento: 8 kbytes 13 bits 15 bits |  |
| 183 | Características da paginação | Paginação é um tipo de relocação (via ha; Fragmentação interna é restrita apenas a; Importante:; Visão do usuário: espaço de endereçament |  |
| 184 | Tamanho da página | Páginas grandes significam; Aumento da fragmentação interna na últim; Páginas pequenas significam; Diminuição da fragmentação interna na úl |  |
| 185 | Questões relacionadas com a gerência de páginas | Inclusão de mecanismos de proteção; Garantir que um processo acesse apenas e; Garantir acessos autorizados a uma posiç; Inclusão de mecanismos de compartilhamen |  |
| 186 | Proteção | Proteção de acesso é garantida por defin; Processos acessam somente suas páginas e; Endereço inválido apenas na última págin; ▶ Se houver fragmentação interna |  |
| 187 | Compartilhamento de páginas | Código compartilhado; Dados e código próprios |  |
| 188 | Process 1 | 2 (P0); and 4 (P0/P1) |  |
| 189 | Process 2 | 5 (P3); 6 (P3); and 7 (P2) |  |
| 190 | Implementação da tabela de páginas | Frames livres/alocados; Registradores; Memória |  |
| 191 | Implementação da tabela de páginas via registradores | Cada página um registrador; ▶ Troca de contexto: atualização dos reg; Desvantagem é o número de registradores |  |
| 192 | Implementação da tabela de páginas em memória | Tabela de páginas é mantida em memória |  |
| 193 | Número de acesso depende da largura da entrada da tabela de página e d | byte; word |  |
| 194 | Page Table | A table with multiple entries |  |
| 195 | Registradores associativos | Pesquisa paralela |  |
| 196 | TLB | Translation Lookaside Buffer; a cache for recent translations |  |
| 197 | Aspectos relacionados com o uso de TLB | Desvantagem é o seu custo; Tamanho limitado (de 8 a 2048 entradas); Um acesso é feito em duas partes: |  |
| 198 | Necessidade de Armazenamento | Grandes quantidades de informação têm de; Definição de estruturas (organização, hi; ARQUIVO |  |
| 199 | Definição de estruturas | organização; hierarquia; relação entre informação |  |
| 200 | Gerência de Arquivos | Oferece a abstração de arquivos (e diret; criar, deletar – create(), unlink(); abrir, fechar – open(), close(); ler, escrever – read(), write() |  |
| 201 | The diagram illustrates the internal structure of the UNIX kernel, org | User level; Kernel level; and Hardware level |  |
| 202 | File Subsystem | (Highlighted in green) Manages file oper; interacting with the Buffer cache; Character and block devices; and Device drivers |  |
| 203 | Process control system | Manages system processes; including Interprocess communication; the scheduler; and Memory management |  |
| 204 | Permitem estruturar o armazenamento e a recuperação de dados persisten | discos; fitas magnéticas |  |
| 205 | Sistema de Arquivos | Arquivo; É composto por:; Nome: identifica o arquivo perante o uti; Informação: dados guardados em memória s |  |
| 206 | Descritor de arquivo | datas de criação; modificação e acesso; dono; autorizações de acesso) |  |
| 207 | Tipos de Arquivos (1) | Arquivos Regulares; Arquivos ASCII; Binários; Apresentam uma estrutura interna conheci |  |
| 208 | Operações sobre Arquivos | Dependem do tipo; create; delete; open |  |
| 209 | Diretórios <sup>(1)</sup> | localização física, nome, organização e  |  |
| 210 | Diretórios (2) | Sistemas de Diretório em Nível Único; Implementação mais simples; Isso ocasionaria um conflito no acesso a |  |
| 211 | Diretórios (3) | Estrutura de diretórios com dois níveis; Cada entrada aponta para o diretório pes |  |
| 212 | Diretórios (4) | Estrutura de diretórios Hierárquicos; Adotado pela maioria dos sistemas operac; Logicamente melhor organizado; É possível criar quantos diretórios quis |  |
| 213 | The diagram illustrates a hierarchical directory structure. At the top | Carlos/; Ivan/ |  |
| 214 | A definição de um SuperBloco | no. de blocos |  |
| 215 | Esquema do Sistema de Arquivos (2) | As informações sobre os blocos livres |  |
| 216 | - Alocação Contígua | O acesso é bastante simples; Pré-alocação (fragmentação interna) |  |
| 217 | Diagram illustrating contiguous file allocation. A table lists files | 3 blocks); 8 blocks); 5 blocks). Below; blocks 10-12 in blue |  |
| 218 | Row 2 | orange (2 blocks); white (5 blocks); blue (3 blocks); orange (6 blocks) |  |
| 219 | Row 3 | orange (2 blocks); white (5 blocks); blue (3 blocks); white (3 blocks) |  |
| 220 | Row 4 | white (3 blocks); blue (3 blocks); yellow (3 blocks); white (2 blocks) |  |
| 221 | Implementação de Arquivos (4) | Alocação por Lista Encadeada; É necessário que o disco seja desfragmen |  |
| 222 | Implementação de Arquivos (6) | Alocação por Lista Encadeada usando Tabe; FAT (File Allocation Table); Vantagens:; Permitir o acesso direto aos blocos |  |
| 223 | FAT | Esquema usado pelo MS-DOS (FAT-16); Win95; Win98; Windows Millennium Edition (FAT-32) |  |
| 224 | Implementação de Arquivos (7) | Desvantagem |  |
| 225 | Implementação de Arquivos (8) | i-nodes; Ocupa menos espaço que a FAT; Usados por sistemas baseados no UNIX |  |
| 226 | The diagram illustrates the relationship between directories, inodes,  | directory; inode; and files |  |
| 227 | A horizontal bar representing disk layout with four sections | Boot block; Super block; Inodes (with a vertical line indicating ; and Data |  |
| 228 | Relação entre Diretórios e i-nodes (2) | Passos para alcançar /usr/ast/mbox |  |
| 229 | FCFS (First-Come First Serve) | Cabeçote inicia na posição 53 |  |
| 230 | SSTF (Shortest Seek Time First) | O SSTF é uma forma de escalonamento SJF |  |
| 231 | Diagram illustrating the SSTF disk scheduling algorithm. The horizonta | then to 53 (distance 16); then to 65 (distance 12); then to 67 (distance 2); then to 98 (distance 31) |  |
| 232 | SCAN | O braço inicia em uma extremidade do dis; Às vezes chamado de algoritmo Elevator |  |
| 233 | Diagram illustrating the SCAN disk scheduling algorithm. A horizontal  | it starts at cylinder 0; moves right to 14; and 67 |  |
| 234 | C-SCAN | Tempo de espera mais uniforme que o SCAN; O cabeçote move-se para a outra extremid; atende requisições durante movimentação; ▶ Nenhuma requisição é atendida na viage |  |
| 235 | C-LOOK | É uma versão do C-SCAN; depois inverte a direção imediatamente |  |
| 236 | Diagram illustrating the C-LOOK disk scheduling algorithm. A horizonta | it starts at 14; moves right to 65; then to 98; and 183. It then jumps to 37 |  |
| 237 | Selecionando um bom algoritmo | e influenciado pelo método de alocação d |  |
| 238 | Ações na Troca de Contexto | Mover o BCP para a fila apropriada; Alterar o BCP do processo selecionado; Alterar as tabelas de gerência de memóri; Restaurar o contexto do processo selecio |  |
| 239 | Definição | Muda do estado executando para esperando; Muda do estado executando para pronto; Muda do estado esperando para pronto; Termina |  |
| 240 | Dispatcher | Troca de Contexto; Latência de Despacho |  |
| 241 | Critérios de Otimização | Maximizar utilização da CPU; Maximizar produtividade; Minimizar o tempo de processamento; Minimizar o tempo de espera |  |
| 242 | UCP | Executes from 0 to 12 (orange); 12 to 20 (green); 20 to 35 (cyan); and 35 to 40 (yellow) |  |
| 243 | Gantt chart illustrating FCFS scheduling for four processes | UCP; Processo A; Processo B; and 40 |  |
| 244 | Gantt chart illustrating SJF scheduling for four processes | UCP; Processo A; Processo B; divided into yellow (0-5) |  |
| 245 | Gantt chart illustrating priority scheduling for processes UCP, Proces | yellow (0-5); cyan (5-20); orange (20-32) |  |
| 246 | Considere que | para o algoritmo de prioridade |  |
| 247 | Exemplo de Programa Multithread (1) | Editor de Texto; Processamento assíncrono (salvamento per |  |
| 248 | Definição (3) | Cada thread tem a si associada:; Thread ID; Estado dos registradores, incluindo o PC; Endereços da pilha |  |
| 249 | Estado de execução | ready; blocked; running |  |
| 250 | Bottom-left | Two separate boxes; each containing one wavy line. Label: mu |  |
| 251 | Bottom-right | Two separate boxes; each containing three wavy lines. Label: |  |
| 252 | Diagram illustrating four process/thread configurations | 1. one process; one thread; 2. one process; multiple threads |  |
| 253 | Threads vs Processos (1) | Propriedade de recursos (“resource owner; Escalonamento (“scheduling / dispatching; Propriedade de recursos:; Escalonamento: |  |
| 254 | Threads vs Processos (2) | Tradicionalmente o processo está associa; um programa em execução; um conjunto de recursos; Em um S.O. que suporta múltiplas threads |  |
| 255 | Threads estão associadas às atividades de execução | ou seja |  |
| 256 | Apresentação | Prof. Dr. Miguel Gomes Xavier; miguel.xavier@pucrs.br; Áreas de interesse/pesquisa |  |
| 257 | Ementa | Estudo dos diversos mecanismos para comu |  |
| 258 | UNIDADE 3: Programação concorrente | 3.1 Programas multithreads; 3.2 Comunicação e sincronização de proce; 3.3 Primitivas de sincronização; 3.4 Problemas clássicos |  |
| 259 | functionalities layers | The top layer; encompassing all kernel functionalities |  |
| 260 | electronics | The bottom layer; representing the physical hardware |  |
| 261 | system | Includes interfaces core; Device Model; system run; generic HW access |  |
| 262 | processing | Includes processes; threads; synchronization; Scheduler |  |
| 263 | memory | Includes memory access; virtual memory; memory mapping; logical memory |  |
| 264 | storage | Includes files & directories access; Virtual File System; page cache; swap |  |
| 265 | networking | Includes sockets access; protocol families; networking storage; socket splice |  |
| 266 | Footer | 2010 Constantine Shulyupin www.MakeLinux |  |
| 267 | Sistema de Avaliação | Onde: |  |
| 268 | Avisos | Chamada; Frequência mínima para aprovação: 75%; máximo de faltas: 7 faltas (14 h/a); Notebooks e tablets: utilizar com modera |  |
| 269 | Moodle | material; trabalhos; provas |  |
| 270 | Linux Threads | Implementa o modelo de mapeamento um-par |  |
| 271 | Exemplos | Solaris 2; Tru64 UNIX's; Windows NT/2000 com o ThreadFiber packag |  |
| 272 | O diagrama ilustra o Modelo M | n de threads. No topo; há três círculos rotulados com a letra ' |  |
| 273 | The diagram illustrates the Solaris multithreading model across three  | User; Kernel; and Hardware |  |
| 274 | Bibliotecas de Threads (2) | Uma biblioteca de threads contém código ; criação e sincronização de threads; troca de mensagens e dados entre threads; escalonamento de threads |  |
| 275 | Bibliotecas de Threads <sup>(1)</sup> | libpthread (padrão POSIX/IEEE 1003.1c); libthread (Solaris) |  |
| 276 | POSIX Threads ou pthreads provê uma interface padrão para manipulação  | Unix; Windows |  |
| 277 | Esperando pelo Término da Thread: pthreadjoin() (2) | Valores de retorno:; EDEADLK – tid especifica a thread chamad; EINVAL – o valor de tid é inválido |  |
| 278 | Sistema de Computação | Hardware; Programas de aplicação; Usuários |  |
| 279 | Provê os recursos básicos de computação | UCP; memória; dispositivos de E/S |  |
| 280 | Definem as maneiras pelas quais os recursos do sistema são usados para | compiladores; sistemas de banco de dados; video games; programas financeiros |  |
| 281 | A diagram showing the layers of computer software and hardware. It con | Banking system; Airline reservation; Web browser; Compilers |  |
| 282 | ... possibilita o uso eficiente e controlado dos diversos componentes  | unidade central de processamento; memória; dispositivos de entrada e saída |  |
| 283 | Organização Típica | Núcleo (kernel); Gerente de Memória; Sistema de E/S; Sistema de Arquivos |  |
| 284 | The diagram shows a single vertical stack of components. At the top is | 'VFS; System call'; 'IPC; File System' |  |
| 285 | The diagram shows a green 'Application' box at the top. Below it is a  | 'Application IPC' (orange); 'UNIX Server' (green); 'Device Driver' (grey); Virtual Memory |  |
| 286 | The diagram shows a green 'Application' box at the top. Below it is a  | 'File Server' (blue); 'UNIX Server' (green); Virtual Memory; 'UNIX Server' |  |
| 287 | Histórico (1) | No início ... (inexistência de S.O.) |  |
| 288 | Tipos de Sistemas Operacionais | Sistemas de Lotes (Batch); Sistemas de Tempo Compartilhado (Time Sh; Sistemas de Tempo Real (Real-Time); Sistemas Mainframes |  |
| 289 | Sistemas de Lotes (1) | Inexistência de computação interativa |  |
| 290 | The first block contains the text | $JOB; MARVIN TANENBAUM |  |
| 291 | Diagram of a batch system showing a sequence of job steps | \$JOB; \$FORTRAN; \$LOAD; \$RUN |  |
| 292 | Sistemas de Tempo Compartilhado | Tempo de resposta é baixo; Número de tarefas processadas/tempo é ba; Arquitetura mais complexa e de propósito |  |
| 293 | - Soft Real-Time | Utilização limitada em controle industri |  |
| 294 | Útil para aplicações que requerem características avançadas de sistema | ex: multimídia; realidade virtual |  |
| 295 | Sistemas Mainframes | Arquitetura de hardware complexa; Trabalham em multimodo (usualmente “batc |  |
| 296 | Sistemas Desktop | Caracterizado pelo uso de computadores p |  |
| 297 | Dispositivos típicos de E/S | teclado; mouse; terminal de vídeo; pequenas impressoras |  |
| 298 | Pode rodar diferentes tipos de S.O | Windows; MacOS; UNIX; Linux |  |
| 299 | Sistemas Distribuídos (1) | Vantagens:; Compartilhamento de recursos;; Balanceamento de carga;; Aumento da velocidade de computação; |  |
| 300 | Sistemas Distribuídos (2) | Sistema fracamente acoplado (Loosely cou; Arquitetura Cliente-Servidor: |  |
| 301 | Servidores são configurados para satisfazer as consultas dos sistemas  | servidor de arquivos; servidor de mail; servidor de ftp |  |
| 302 | Sistemas Paralelos(1) | Principais vantagens:; Aumento da vazão (“throughput”); Economia de escala;; Aumento da confiabilidade |  |
| 303 | Sistemas Paralelos(2) | Symmetric multiprocessing (SMP) |  |
| 304 | A maioria dos sistemas operacionais modernos suporta SMP, através do c | Windows NT; Solaris; OS/2; Linux |  |
| 305 | Classificação | Quanto ao número de usuários:; Monousuário:; Projetados para suportar um único usuári; Ex: MS-DOS, Windows 3x, Windows 9x |  |
| 306 | A UCP fica ociosa durante muito tempo enquanto o programa aguarda por  | digitação de um dado; leitura do disco |  |
| 307 | Monoprogramação | A complexidade de implementação é relati |  |
| 308 | Multiprogramação | Vários programas competem pelos recursos |  |
| 309 | Program A | Run; Wait |  |
| 310 | Program B | Wait; Run |  |
| 311 | Program C | Wait; Run |  |
| 312 | Multiprogramação (cont.) | Maximização do uso do processador e da m; Suporte de hardware:; Proteção de memória; Mecanismo de interrupção (sinalização de |  |
| 313 | Cover of the book 'Computer Networking | A Top-Down Approach Featuring the Intern |  |
| 314 | Sockets | process sends/receives messages to/from ; socket analogous to door; ❖ sending process shoves message out doo |  |
| 315 | API | (1) choice of transport protocol |  |
| 316 | Socket API | introduced in BSD4.1 UNIX, 1981; explicitly created, used, released by ap; client/server paradigm; two types of transport service via socke |  |
| 317 | process | The top component; which is controlled by application devel |  |
| 318 | TCP with buffers, variables | The transport layer component; which is controlled by operating system |  |
| 319 | Client must contact server | ▮ server process must first be running |  |
| 320 | Client contacts server by: | ▮ creating client-local TCP socket; ▮ specifying IP address, port number of ; ❖ allows server to talk with multiple cl; ❖ source port numbers used to distinguis |  |
| 321 | Example client-server app: | 2) server reads line from socket |  |
| 322 | TCP connection setup | connect to hostid |  |
| 323 | Example | Java client (TCP); cont; Java server (TCP) |  |
| 324 | Diagram mapping Java code to actions | 'Create output stream; attached to socket' points to DataOutput; labeled 'End of while loop; loop back and wait for another client co |  |
| 325 | TCP/IP Sockets in Java: Practical Guide for Programmers | Kenneth L. Calvert; Michael J. Donahoo |  |
| 326 | Client | Create a TCP socket; Communicate; Close the connection; Establish connection |  |
| 327 | Server | Create a TCP socket; Repeatedly:; a. Accept new connection; b. Communicate |  |
| 328 | TCP Tidbits | Client knows server address and port; No correlation between send() and recv() |  |
| 329 | Closing a Connection | close() used to delimit communication; Analogous to EOF |  |
| 330 | Cliente contata o servidor | Criando um socket TCP local |  |
| 331 | Exemplo de aplicação cliente-servidor: | 2) Servidor lê linha do socket |  |
| 332 | Internal Streams | Inside the process circle; there are two vertical boxes: "inFromUse |  |
| 333 | External Streams | Outside the process circle; there are two vertical boxes: "inFromSer |  |
| 334 | Cria datagrama para enviar ao cliente | sendData.length; IPAddress; port) |  |
| 335 | Tutorial sobre Java | “Socket Programming in Java: a tutorial |  |
| 336 | OBJETIVOS | O cumprimento da disciplina busca dar ao; ao final do semestre; condições de: |  |
| 337 | PROCEDIMENTOS E RECURSOS: | Uso de projetor multimídia; Uso de laboratório para elaboração de tr |  |
| 338 | P1 | Prova 1; 03 e 04 |  |
| 339 | P2 | Prova 2; 06 e 07 |  |
| 340 | SILBERSCHATZ, Abraham, GALVIN, Peter B, GAGNE, Greg. Sistemas Operacio | Elsevier; 2008. 673p |  |
| 341 | DEITEL, Harvey M. Sistemas operacionais. 3.ed. São Paulo | Pearson Prentice Hall; 2005. 760 p. (Acervo Digital) |  |
| 342 | LEWIS, Bil ; Berg, Daniel J. Threads Primer | 1996. 319p |  |
| 343 | SHAY, William A. Sistemas Operacionais. São Paulo | Makron Books do Brasil Ed. Ltda; 1996. 758p |  |
| 344 | STALLINGS, W. Operating systems – Internals and Design Principles. 3.e | Prentice-Hall; 1998. 779p |  |
| 345 | - SOFTWARE DE APOIO: | Sistema Operacional Linux e suas ferrame |  |
| 346 | Unidade 01 — Introdução ao estudo de sistemas operacionais | [ ] 1.1 Evolução histórica; [ ] 1.1 Serviços dos sistemas operaciona; [ ] 1.2 Chamadas de sistema; [ ] 1.3 Estudo de casos |  |
| 347 | Unidade 02 — Gerência do Processador | [ ] 3.2 Escalonamento; [ ] 3.3 Algoritmos de escalonamento; [ ] 3.4 Estudo de casos |  |
| 348 | 🧪 Tambem cobre esta unidade | Apresentação da Disciplina; Programa (+1) |  |
| 349 | Unidade 03 — Programação concorrente | [ ] 4.1 Programas multithreads; [ ] 4.2 Comunicação e sincronização de p; [ ] 4.3 Primitivas de sincronização; [ ] 4.4 Problemas clássicos |  |
| 350 | Unidade 04 — Deadlock | [ ] 5.2 Caracterização; [ ] 5.3 Prevenção; [ ] 5.4 Detecção e recuperação |  |
| 351 | Unidade 05 — Gerência de Memória | [ ] 6.1 Políticas básicas; [ ] 6.1.1 Sistemas monoprogramados; [ ] 6.1.2 Partições fixas; [ ] 6.1.3 Partições variáveis |  |
| 352 | Unidade 06 — Gerência de arquivos | [ ] 7.1 Arquivos; [ ] 7.2 Diretórios; [ ] 7.3 Implementação de sistemas de arq; [ ] 7.4 Proteção |  |
| 353 | Unidade 07 — Gerência de entrada e saída | [ ] 2.1 Dispositivos de entrada e saída; [ ] 2.2 Controladores dos dispositivos; [ ] 2.3 Drivers dos dispositivos; [ ] 2.4 Estudo de casos |  |
| 354 | Instruções para a realização da prova: | Escreva de maneira legível e organizada |  |
| 355 | Exercise 5.12 | Consider the following set of processes |  |
| 356 | Draw four Gantt charts that illustrate the execution of these processe | FCFS; SJF |  |
| 357 | Pronto | processo está apto a executar; aguardando CPU |  |
| 358 | Bloqueado/Esperando | processo aguarda E/S; evento ou recurso |  |
| 359 | Executando → Pronto | preempção; fim do quantum ou interrupção |  |
| 360 | Enunciado | crie um algoritmo que impeça o deadlock; exclusão mútua; condição de corrida; deadlock e starvation |  |
| 361 | Text | contém o código do programa; como main() e soma() |  |
| 362 | Resposta: | Data: contém variáveis globais ou estáti; Heap: memória alocada dinamicamente com  |  |
| 363 | Stack | contém variáveis locais; parâmetros e endereços de retorno |  |
| 364 | Alocação: | Código de main() e soma() → text; str → ponteiro local na stack; s1, s2, ret → stack; parâmetros a e b de soma() → stack |  |
| 365 | Compartilhados entre as threads: | code/text; data; heap; arquivos abertos |  |
| 366 | Exclusivos de cada thread: | registradores; stack; contador de programa |  |
| 367 | Linha 4 | executada pelo processo pai original; após fork; existem pai e filho |  |
| 368 | Observação | tecnicamente; NULL) está incorreto |  |
| 369 | Linha 9 | normalmente apenas o pai executa; porque o filho é substituído pelo progra |  |
| 370 | Solução | usar aging |  |
| 371 | Quantum = 10, quando aplicável. Ordem de chegada | P1; P2; P3 |  |
| 372 | Tempo médio de espera | 67 unidades; 33 unidades |  |
| 373 | Exercícios preparatórios para P2 | setor de índice: 9; setor de dados: 20, 22, 10 e 5 |  |
| 374 | setor de dados | 10 e 5 |  |
| 375 | TANENBAUM, A. D. Sistemas operacionais modernos. 3. ed. São Paulo | Pearson Prentice Hall; 2010 (adaptado) |  |
