CURSO: SO

TOPICOS DO PLANO (use somente estes codigos):
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

CATEGORIAS (lote 1):
[1] categoria: Introdução | termos: Um programa é uma coleção de segmentos, tipicament; Código; Dados alocados estaticamente; Dados alocados dinamicamente | trecho: ## Introdução - Um programa é uma coleção de segmentos, tipicamente:
[2] categoria: e.g | termos: procedimentos (funções); bibliotecas; páginas read-only; read-write | trecho: - e.g.: procedimentos (funções), bibliotecas
[3] categoria: Diagrama do Espaço de usuário | termos: Um oval contendo quatro retângulos numerados 1; 3 e 4 | trecho: Diagrama do Espaço de usuário: Um oval contendo quatro retângulos numerados 1, 2, 3 e 4.
[4] categoria: Endereço lógico em segmentação | termos: Endereço lógico é composto por duas partes:; Número de segmento; Deslocamento dentro do segmento; Segmentação é similar a alocação particionada dinâ | trecho: ### Endereço lógico em segmentação - Endereço lógico é composto por duas partes:
[5] categoria: Tradução de endereço lógico em endereço físico | termos: Tabela de segmentos; Hardware (comparador); Entrada na tabela de segmento:; base: endereço inicial (físico) do segmento na mem | trecho: ### Tradução de endereço lógico em endereço físico - Tabela de segmentos
[6] categoria: Implementação da tabela de segmentos | termos: Construção de uma tabela de segmentos; Cada segmento corresponde a uma entrada na tabela; Cada segmento necessita armazenar dois valores:; Limite e base | trecho: ### Implementação da tabela de segmentos - Construção de uma tabela de segmentos
[7] categoria: Implementação da tabela de segmentos via registradores | termos: Cada segmento dois registradores (base e limite); ▶ Troca de contexto: atualização dos registradores | trecho: ### Implementação da tabela de segmentos via registradores - Cada segmento dois registradores (base e limite)
[8] categoria: Implementação da tabela de segmentos em memória | termos: Tabela de segmentos armazenada em memória | trecho: ### Implementação da tabela de segmentos em memória - Tabela de segmentos armazenada em memória
[9] categoria: Problemas com implementação da tabela em memória | termos: Problemas similares ao da paginação:; Solução:; Empregar uma TLB; Observação (válida também para a paginação) | trecho: ### Problemas com implementação da tabela em memória - Problemas similares ao da paginação:
[10] categoria: Physical Address | termos: If the comparison is successful | trecho: - Physical Address:** If the comparison is successful, the final **End. Físico** (Physical Address) is formed by combining the base address and the displacement (**d**).
[11] categoria: Aspectos de proteção e compartilhamento | termos: Problema associado: | trecho: ## Aspectos de proteção e compartilhamento - Problema associado:
[12] categoria: Desvantagem da segmentação | termos: Concatenação de segmentos adjacentes; Compactação da memória | trecho: ### Desvantagem da segmentação - Concatenação de segmentos adjacentes
[13] categoria: Solução para fragmentação externa | termos: Analisar o problema sob dois pontos extremos:; Um processo é um único segmento; Cada byte é um segmento; ▶ Similar a página de 1 byte | trecho: ### Solução para fragmentação externa - Analisar o problema sob dois pontos extremos:
[14] categoria: Segmentação com paginação | termos: Solução se traduz em paginar segmentos | trecho: ### Segmentação com paginação - Solução se traduz em paginar segmentos
[15] categoria: The diagram illustrates the mapping from logical to physical addresses. At the top, a box  | termos: 'p'; and 'd'; with a bracket under 'p d' | trecho: The diagram illustrates the mapping from logical to physical addresses. At the top, a box labeled 'End. lógico' contains two parts: 's' and 'd'. A bracket under 'd' has an arrow po
[16] categoria: Chapter 13: I/O Systems | termos: I/O Hardware; Application I/O Interface; Kernel I/O Subsystem; Transforming I/O Requests to Hardware Operations | trecho: # Chapter 13: I/O Systems - I/O Hardware
[17] categoria: I/O Hardware | termos: Incredible variety of I/O devices; Common concepts; Port; Bus (daisy chain or shared direct access) | trecho: ## I/O Hardware - Incredible variety of I/O devices
[18] categoria: Polling | termos: Determines state of device; command-ready; busy; Error | trecho: ### Polling - Determines state of device
[19] categoria: Interrupts | termos: Interrupt handler receives interrupts; Maskable to ignore or delay some interrupts; Interrupt vector to dispatch interrupt to correct ; Based on priority | trecho: ### Interrupts - **Interrupt handler** receives interrupts
[20] categoria: Direct Memory Access | termos: Requires DMA controller | trecho: ### Direct Memory Access - Requires **DMA** controller
[21] categoria: CPU memory bus | termos: cache | trecho: - CPU memory bus**: A blue cylinder connecting the **DMA/bus/interrupt controller**, **cache**, and **memory<sup>x</sup> buffer**.
[22] categoria: Application I/O Interface | termos: Devices vary in many dimensions; Character-stream or block; Sequential or random-access; Sharable or dedicated | trecho: ### Application I/O Interface - Devices vary in many dimensions
[23] categoria: Device Drivers | termos: A row of drivers including SCSI device driver; keyboard device driver; mouse device driver; PCI bus device driver | trecho: - Device Drivers**: A row of drivers including SCSI device driver, keyboard device driver, mouse device driver, ..., PCI bus device driver, floppy device driver, and ATAPI device d
[24] categoria: Device Controllers | termos: A row of controllers including SCSI device control; keyboard device controller; mouse device controller; PCI bus device controller | trecho: - Device Controllers**: A row of controllers including SCSI device controller, keyboard device controller, mouse device controller, ..., PCI bus device controller, floppy device co
[25] categoria: Physical Devices | termos: A row of hardware devices including SCSI devices; keyboard; mouse; PCI bus | trecho: - Physical Devices**: A row of hardware devices including SCSI devices, keyboard, mouse, ..., PCI bus, floppy-disk drives, and ATAPI devices (disks, tapes, drives).
[26] categoria: Block and Character Devices | termos: Block devices include disk drives; Commands include read, write, seek; Raw I/O or file-system access; Memory-mapped file access possible | trecho: #### Block and Character Devices - Block devices include disk drives
[27] categoria: Network Devices | termos: Separates network protocol from network operation; Includes select functionality; Approaches vary widely (pipes, FIFOs, streams, que | trecho: #### Network Devices - Separates network protocol from network operation
[28] categoria: Approaches vary widely | termos: pipes; FIFOs; streams; queues | trecho: - Approaches vary widely (pipes, FIFOs, streams, queues, mailboxes)
[29] categoria: Clocks and Timers | termos: Provide current time, elapsed time, timer; Programmable interval timer used for timings, peri | trecho: #### Clocks and Timers - Provide current time, elapsed time, timer
[30] categoria: Blocking and Nonblocking I/O | termos: Blocking - process suspended until I/O completed; Easy to use and understand; Insufficient for some needs; User interface, data copy (buffered I/O) | trecho: ### Blocking and Nonblocking I/O - **Blocking** - process suspended until I/O completed
[31] categoria: The diagram illustrates two I/O methods | termos: device driver; interrupt handler; kernel (interrupt handler and hardware); and user (requesting process) | trecho: The diagram illustrates two I/O methods: Synchronous (a) and Asynchronous (b). Both methods are shown across four layers: requesting process, device driver, interrupt handler, and 
[32] categoria: Diagram comparing Synchronous and Asynchronous I/O methods across four layers | termos: requesting process; device driver; interrupt handler; and hardware | trecho: Diagram comparing Synchronous and Asynchronous I/O methods across four layers: requesting process, device driver, interrupt handler, and hardware.
[33] categoria: Kernel I/O Subsystem | termos: Scheduling; To cope with device speed mismatch; To cope with device transfer size mismatch; Caching - fast memory holding copy of data | trecho: ### Kernel I/O Subsystem - Scheduling
[34] categoria: device | termos: keyboard; status: idle; laser printer; status: busy | trecho: - device: keyboard, status: idle
[35] categoria: request for laser printer | termos: address: 38546; length: 1372 | trecho: - request for laser printer (address: 38546, length: 1372)
[36] categoria: request for disk unit 2 | termos: file: xxx; operation: read; address: 43046; length: 20000 | trecho: - request for disk unit 2 (file: xxx, operation: read, address: 43046, length: 20000)
[37] categoria: Error Handling | termos: ❑ System error logs hold problem reports | trecho: ### Error Handling - ❑ System error logs hold problem reports
[38] categoria: I/O Protection | termos: All I/O instructions defined to be privileged; I/O must be performed via system calls | trecho: ### I/O Protection - All I/O instructions defined to be privileged
[39] categoria: 2 perform I/O | termos: Inside the kernel | trecho: - 2 perform I/O:** Inside the kernel, the trap is handled by a dispatcher (labeled `case $n$` ). The dispatcher calls a kernel routine (labeled `read`) to perform the I/O operation
[40] categoria: 3 return to user | termos: After the I/O is complete; where the user program resumes execution | trecho: - 3 return to user:** After the I/O is complete, control returns from the kernel to the user space, where the user program resumes execution.
[41] categoria: Each record contains pointers to various functions | termos: inode pointer; pointer to read and write functions; pointer to select function; pointer to ioctl function | trecho: - Each record contains pointers to various functions: **inode pointer**, **pointer to read and write functions**, **pointer to select function**, **pointer to ioctl function**, and
[42] categoria: I/O Requests to Hardware Operations | termos: Determine device holding file; Translate name to device representation; Physically read data from disk into buffer; Make data available to requesting process | trecho: ### I/O Requests to Hardware Operations - Determine device holding file
[43] categoria: interrupt handler | termos: Responds to interrupts from the device controller | trecho: - interrupt handler**: Responds to interrupts from the device controller, storing data in buffers and signaling the device driver.
[44] categoria: STREAMS | termos: A STREAM consists of:; STREAM head interfaces with the user process; driver end interfaces with the device; zero or more STREAM modules between them | trecho: ### STREAMS - A STREAM consists of:
[45] categoria: Performance | termos: I/O a major factor in system performance:; Context switches due to interrupts; Data copying; Network traffic especially stressful | trecho: ## Performance - I/O a major factor in system performance:
[46] categoria: Character Typing | termos: leading to 'interrupt generated' (rectangle) | trecho: - Character Typing:** A 'character typed' event (circle) triggers a 'hardware' interrupt, leading to 'interrupt generated' (rectangle).
[47] categoria: State Saving | termos: which then leads to 'interrupt handled' (rectangle; which then leads to 'device driver' (rectangle) | trecho: - State Saving:** The 'interrupt generated' event leads to 'state save' (rectangle), which then leads to 'interrupt handled' (rectangle).
[48] categoria: System Call | termos: which then leads to 'interrupt handled' (rectangle | trecho: - System Call:** A 'system call completes' event (rectangle) triggers a 'context switch' (rectangle), which then leads to 'interrupt handled' (rectangle).
[49] categoria: Interrupt Handling | termos: which then leads to 'interrupt generated' (rectang | trecho: - Interrupt Handling:** The 'interrupt handled' event leads to 'state save' (rectangle), which then leads to 'interrupt generated' (rectangle).
[50] categoria: Network Packet Received | termos: leading to 'network adapter' (rectangle) | trecho: - Network Packet Received:** A 'network packet received' event (circle) triggers a 'hardware' interrupt, leading to 'network adapter' (rectangle).
[51] categoria: Improving Performance | termos: Reduce number of context switches; Reduce data copying; Use DMA | trecho: ### Improving Performance - Reduce number of context switches
[52] categoria: The diagram shows four concentric circles representing protection rings. The innermost cir | termos: green; yellow; orange; and red | trecho: The diagram shows four concentric circles representing protection rings. The innermost circle is labeled "Kernel". The next ring is labeled "Device drivers". The third ring is labe
[53] categoria: Diagram of protection rings. Four concentric circles represent Ring 0, Ring 1, Ring 2, and | termos: green; yellow; orange; and red | trecho: Diagram of protection rings. Four concentric circles represent Ring 0, Ring 1, Ring 2, and Ring 3. The innermost circle is labeled 'Kernel'. The next ring is labeled 'Device driver
[54] categoria: Dispositivos de Entrada e Saída (1) | termos: Constituídos de 2 partes:; Mecânica; Eletrônica – Controladora ou Adaptadora; Controladora | trecho: ### Dispositivos de Entrada e Saída (1) - Constituídos de 2 partes:
[55] categoria: O diagrama ilustra a conexão de dispositivos de entrada e saída a um sistema centralizado. | termos: CPU; Memory; Video controller; Keyboard controller | trecho: O diagrama ilustra a conexão de dispositivos de entrada e saída a um sistema centralizado. No topo, há uma barra horizontal que representa o barramento do sistema. Abaixo dela, há 
[56] categoria: Dispositivos de Entrada e Saída (2) | termos: Controladora (cont.); Também tratar o acesso do dispositivo ao barrament; Tarefas típicas; Correção de erros | trecho: ### Dispositivos de Entrada e Saída (2) - Controladora (cont.)
[57] categoria: Tipos de interfaces (dados) | termos: Barramentos:; Porta Serial, Porta Paralela, USB, PS/2; PCI, AGP, PCI-E, SCSI, IDE, SATA | trecho: ### Tipos de interfaces (dados) - Barramentos:
[58] categoria: Mapeamento de Endereços | termos: Mapeamento em espaço de entrada e saída; Instruções especiais da CPU para E/S; Opcodes separados (IN reg, [end16], OUT [end16], r; Mapeamento em espaço de memória | trecho: ### Mapeamento de Endereços - Mapeamento em espaço de entrada e saída
[59] categoria: Opcodes separados | termos: IN reg; [end16]; OUT [end16]; reg | trecho: - Opcodes separados (IN reg, [end16], OUT [end16], reg)
[60] categoria: Técnicas para realização de E/S <sup>(1)</sup> | termos: Três técnicas usadas:; E/S Programada; Interrupção; Acesso Direto à Memória | trecho: ### Técnicas para realização de E/S <sup>(1)</sup> - Três técnicas usadas:
[61] categoria: Técnicas para realização de E/S (2) | termos: E/S Programada; Interação com o dispositivo é responsabilidade do ; Ciclo de funcionamento; Envio do comando ao dispositivo | trecho: ### Técnicas para realização de E/S (2) - E/S Programada
[62] categoria: Técnicas para realização de E/S <sup>(3)</sup> | termos: E/S Orientada a Interrupção; Requer hardware especial:; Controlador de interrupções:; Identifica o dispositivo que gerou a interrupção | trecho: ### Técnicas para realização de E/S <sup>(3)</sup> - E/S Orientada a Interrupção
[63] categoria: Técnicas para realização de E/S (4) | termos: E/S Orientada a Interrupção (cont.) | trecho: ### Técnicas para realização de E/S (4) - E/S Orientada a Interrupção (cont.)
[64] categoria: Técnicas para realização de E/S (5) | termos: Acesso direto à memória (DMA); Controlador de DMA:; O processador é liberado para outras tarefas; Terminando a transferência, o controlador gera uma | trecho: ### Técnicas para realização de E/S (5) - Acesso direto à memória (DMA)
[65] categoria: Controlador de DMA | termos: Representado por um retângulo no centro-esquerda; contendo subcomponentes: Endereço; Contador e Controle | trecho: - Controlador de DMA:** Representado por um retângulo no centro-esquerda, contendo subcomponentes: Endereço, Contador e Controle.
[66] categoria: Controlador de disco | termos: Representado por um retângulo no centro-direita; contendo um subcomponente Buffer | trecho: - Controlador de disco:** Representado por um retângulo no centro-direita, contendo um subcomponente Buffer.
[67] categoria: Dispositivo | termos: Representado por um cilindro no topo; conectado ao Controlador de disco | trecho: - Dispositivo:** Representado por um cilindro no topo, conectado ao Controlador de disco.
[68] categoria: 3. Dados transferidos | termos: através do Buffer do Controlador de disco; para a Memória principal | trecho: - 3. Dados transferidos:** Uma seta curva indica a transferência de dados do Dispositivo, através do Buffer do Controlador de disco, para a Memória principal.
[69] categoria: Subsistema (Software) de Entrada e Saída (1) | termos: Uniformizar o tratamento dos dispositivos; “Esconder” detalhes de mais “baixo nível”; Permitir a inclusão de novos dispositivos; Facilitar a correção de erros gerados pelo disposi | trecho: ### Subsistema (Software) de Entrada e Saída (1) - Uniformizar o tratamento dos dispositivos
[70] categoria: Memória virtual, Sistema de arquivos, and Biblioteca de E/S | termos: Three intermediate layers that handle memory manag; file system operations; and I/O library functions; respectively | trecho: - Memória virtual**, **Sistema de arquivos**, and **Biblioteca de E/S**: Three intermediate layers that handle memory management, file system operations, and I/O library functions,
[71] categoria: Subsistema de E/S | termos: The core I/O subsystem layer; which coordinates the data flow | trecho: - Subsistema de E/S**: The core I/O subsystem layer, which coordinates the data flow.
[72] categoria: Hardware | termos: The bottom layer; representing the physical hardware components | trecho: - Hardware**: The bottom layer, representing the physical hardware components.
[73] categoria: Software | termos: Indicated by a bracket on the right; "E/S independente do dispositivo"; and the "API" layer | trecho: - Software**: Indicated by a bracket on the right, it encompasses the top three layers: "E/S nível de usuário", "E/S independente do dispositivo", and the "API" layer.
[74] categoria: Subsistema (Software) de Entrada e Saída (4) | termos: Software de E/S de usuário:; Wrappers para chamadas de sistema | trecho: ### Subsistema (Software) de Entrada e Saída (4) - Software de E/S de usuário:
[75] categoria: Subsistema (Software) de Entrada e Saída (5) | termos: E/S independente de dispositivo (a seguir..); Interface do subsistema de E/S (API); dispositivos “abstratos” de E/S; Dispositivos “abstratos” | trecho: ### Subsistema (Software) de Entrada e Saída (5) - E/S independente de dispositivo (a seguir..)
[76] categoria: Orientado a bloco | termos: block device; buffered; random access | trecho: - Orientado a bloco (block device, buffered, random access)
[77] categoria: Orientado a caractere | termos: stream; character device; unbuffered | trecho: - Orientado a caractere (stream, character device, unbuffered)
[78] categoria: Subsistema (Software) de Entrada e Saída (6) | termos: Interface do subsistema de E/S (cont.); Dispositivos Orientado a bloco; Organiza dados em blocos de tamanho fixo; Acessa diretamente um bloco de dados | trecho: ### Subsistema (Software) de Entrada e Saída (6) - Interface do subsistema de E/S (cont.)
[79] categoria: Subsistema (Software) de Entrada e Saída (7) | termos: Interface do subsistema de E/S (cont.); Dispositivos Orientado a caractere; Operações típicas:; put( ) e get( ) | trecho: ### Subsistema (Software) de Entrada e Saída (7) - Interface do subsistema de E/S (cont.)
[80] categoria: ex | termos: teclado; vídeo; mouse; impressora | trecho: - ex: teclado, vídeo, mouse, impressora, etc...
[81] categoria: Subsistema (Software) de Entrada e Saída (8) | termos: Interface do subsistema de E/S (cont.); Dispositivos Orientado a rede; Necessário estabelecimento de conexões; Operações típicas: | trecho: ### Subsistema (Software) de Entrada e Saída (8) - Interface do subsistema de E/S (cont.)
[82] categoria: orientado a conexão | termos: connect( ); accept( ); read( ); write( ) | trecho: - orientado a conexão: `connect( )`, `accept( )`, `read( )`, `write( )`
[83] categoria: Subsistema (Software) de Entrada e Saída (9) | termos: Software de E/S independente de dispositivo; Implementa funções gerais comuns a todos os dispos; Atribuição uniforme do nome independente do dispos; Nome do dispositivo é um string | trecho: ### Subsistema (Software) de Entrada e Saída (9) - Software de E/S independente de dispositivo
[84] categoria: Diagrama de árvore de diretórios mostrando a estrutura de nomes de dispositivos em UNIX. O | termos: llyS0; llyS1; llyS2 e llyS3 | trecho: Diagrama de árvore de diretórios mostrando a estrutura de nomes de dispositivos em UNIX. O nó raiz é `/dev`, que aponta para quatro nós filhos: `llyS0`, `llyS1`, `llyS2` e `llyS3`.
[85] categoria: E/S independente do dispositivo | termos: middle layer; separated by a dashed line | trecho: - E/S independente do dispositivo** (middle layer, separated by a dashed line)
[86] categoria: Dentro da camada de drivers, há cinco boxes rotulados | termos: driver SCSI; driver EIDE; driver floppy; driver rede e driver teclado | trecho: Dentro da camada de drivers, há cinco boxes rotulados: **driver SCSI**, **driver EIDE**, **driver floppy**, **driver rede** e **driver teclado**.
[87] categoria: Subsistema (Software) de Entrada e Saída (17) | termos: Drivers de dispositivo | trecho: ### Subsistema (Software) de Entrada e Saída (17) - Drivers de dispositivo
[88] categoria: O diagrama ilustra a arquitetura de software para o subsistema de entrada e saída. No topo | termos: "Driver IDE"; há ícones representando um disco rígido; uma disquete e um CD-ROM. À direita | trecho: O diagrama ilustra a arquitetura de software para o subsistema de entrada e saída. No topo, um bloco retangular rotulado "Independente do dispositivo" envia setas para três blocos 
[89] categoria: Subsistema (Software) de Entrada e Saída (18) | termos: Drivers de dispositivo (cont.); Desenvolvidos pelo fabricante do dispositivo; Vantagens; Facilidade de adicionar novos drivers | trecho: ### Subsistema (Software) de Entrada e Saída (18) - Drivers de dispositivo (cont.)
[90] categoria: Capítulo 9: Memória Virtual | termos: Fundamentos; Paginação sob Demanda; Criação de Processos; Substituição de Páginas | trecho: # Capítulo 9: Memória Virtual - Fundamentos
[91] categoria: Fundamentos | termos: Paginação sob demanda; Segmentação sob demanda | trecho: ## Fundamentos - Paginação sob demanda
[92] categoria: The diagram illustrates the virtual address space layout. It is a vertical rectangle with  | termos: a grey 'stack' segment at the top; a grey 'heap' segment below the blue region; a grey 'data' segment below the heap | trecho: The diagram illustrates the virtual address space layout. It is a vertical rectangle with a vertical axis on the left. The top of the axis is labeled 'Max' and the bottom is labele
[93] categoria: The diagram illustrates the memory layout of two processes sharing a common library. Each  | termos: stack; shared library; heap; data | trecho: The diagram illustrates the memory layout of two processes sharing a common library. Each process has its own memory space, represented by a vertical stack of segments: stack, shar
[94] categoria: Paginação sob Demanda | termos: Necessita de menos E/S; Ocupa menos memória; Resposta mais rápida; Página é necessária  $\Rightarrow$  referencia ela | trecho: ### Paginação sob Demanda - Necessita de menos E/S
[95] categoria: The diagram illustrates the transfer of a paged memory to contiguous disk space. It shows  | termos: indicating they are not used | trecho: The diagram illustrates the transfer of a paged memory to contiguous disk space. It shows a vertical stack of memory pages labeled 'main memory' at the bottom. The stack is divided
[96] categoria: página ausente | termos: SO verifica uma outra tabela para decidir:; Referência inválida  $\Rightarrow$  aborta; Obtém bloco livre na memória; Traz página do disco para o bloco alocado | trecho: #### página ausente - SO verifica uma outra tabela para decidir:
[97] categoria: Criação de Processos | termos: Copy-on-Write (Cópia na Escrita); Arquivos Mapeados na Memória (depois) | trecho: ### Criação de Processos - Copy-on-Write (Cópia na Escrita)
[98] categoria: logical memory for user 1 | termos: 1 (load M); 2 (J) | trecho: - logical memory for user 1:** A 4-page memory space with pages 0 (H), 1 (load M), 2 (J), and 3 (M). A PC points to page 1.
[99] categoria: logical memory for user 2 | termos: 1 (B); 2 (D); and 3 (E). Page 1 (B) is highlighted | trecho: - logical memory for user 2:** A 4-page memory space with pages 0 (A), 1 (B), 2 (D), and 3 (E). Page 1 (B) is highlighted.
[100] categoria: monitor | termos: 1 ($\downarrow$); 2 (D); 3 (H); 4 (load M) | trecho: - monitor:** A 8-page memory space with pages 0 (monitor), 1 ($\downarrow$), 2 (D), 3 (H), 4 (load M), 5 (J), 6 (A), and 7 (E). An arrow points from page 1 to page 4.
[101] categoria: physical memory | termos: A large cylinder representing physical memory; containing pages B and M | trecho: - physical memory:** A large cylinder representing physical memory, containing pages B and M.
[102] categoria: Paginação Excessiva (Thrashing) | termos: Baixa utilização da CPU | trecho: ### Paginação Excessiva (*Thrashing*) - Baixa utilização da CPU.
[103] categoria: Process A Virtual Memory | termos: Pages 1; with page 1 highlighted in grey) | trecho: **Process A Virtual Memory:** Pages 1, 2, 3, 4, 5, 6 (from top to bottom, with page 1 highlighted in grey).
[104] categoria: Process B Virtual Memory | termos: Pages 1; with page 1 highlighted in grey) | trecho: **Process B Virtual Memory:** Pages 1, 2, 3, 4, 5, 6 (from top to bottom, with page 1 highlighted in grey).
[105] categoria: map | termos: mode; position; size | trecho: map(mode, position, size)
[106] categoria: Outras Questões – Tamanho da Página | termos: fragmentação; tamanho da tabela; sobrecarga de E/S; localidade | trecho: ### Outras Questões – Tamanho da Página - fragmentação
[107] categoria: ■ Estrutura de programa | termos: Int[128,128] data;; Cade linha é armazenada em uma página; Programa 1 | trecho: #### ■ Estrutura de programa - `Int[128,128] data;`
[108] categoria: Programação Concorrente (2) | termos: Vantagens:; Desvantagens:; Mais complexa; A aplicação precisa ser reescrita | trecho: ## Programação Concorrente (2) - Vantagens:
[109] categoria: Condição de Corrida (1) | termos: Solução: | trecho: ### Condição de Corrida (1) - Solução:
[110] categoria: Quando um processo entra na sua seção crítica, os outros devem esperar para entrar nas sua | termos: ou seja | trecho: - Quando um processo entra na sua seção crítica, os outros devem esperar para entrar nas suas seções críticas (ou seja, devem bloquear)
[111] categoria: Soluções para o problema Condição de Corrida | termos: Soluções de Hardware; Inibição de Interrupções; Instrução TSL (apresenta busy wait); Soluções de Software com busy wait | trecho: ##### Soluções para o problema Condição de Corrida - Soluções de Hardware
[112] categoria: OBS | termos: para atualizar uma estrutura de controle) | trecho: - OBS: Interrupções pelo tempo de algumas poucas instruções pode ser conveniente para o kernel (p.ex., para atualizar uma estrutura de controle).
[113] categoria: Busy Wait | termos: O que essas soluções fazem é:; Consequência: desperdício de tempo de CPU; Problema da inversão de prioridade: | trecho: ### Busy Wait - O que essas soluções fazem é:
[114] categoria: Definição (2) | termos: A operação P também é comumente referenciada como:; down ou wait; V também é comumente referenciada; up ou signal | trecho: ### Definição (2) - A operação P também é comumente referenciada como:
[115] categoria: Exemplo | termos: agora zero | trecho: - Exemplo: suponha que os dois down do código do produtor estivessem invertidos. Neste caso, mutex seria diminuído antes de empty. Se o buffer estivesse completamente cheio, o prod
[116] categoria: Overhead | termos: Ocorre na execução do escalonamento; Tarefa de alternar a CPU entre dois processos; O tempo depende muito do hardware; 1 a 1000 microseg | trecho: ## Overhead - Ocorre na execução do escalonamento
[117] categoria: The diagram illustrates a 5-state process model. The states are represented by ovals | termos: New; Ready; Running; Blocked | trecho: The diagram illustrates a 5-state process model. The states are represented by ovals: New, Ready, Running, Blocked, and Exit. The transitions between these states are as follows:
[118] categoria: Figure 3.6 | termos: Ready (5-35); Running (12-15); Running (22-28); Running (28-31) | trecho: Figure 3.6: Process States for Trace of Figure 3.3. A Gantt chart showing the execution of three processes (A, B, C) and a Dispatcher over a 50-unit time scale. Process A has three
[119] categoria: Transições de Estados (1) | termos: Null to New:; ▶ Novo batch job; ▶ Logon interativo (usuário se conecta ao sistema); New to Ready: | trecho: ### Transições de Estados (1) - Null to New:
[120] categoria: Transições de Estados (2) | termos: Ready to Running:; Running to Exit:; ▶ Término normal;; ▶ Término do processo pai (em alguns sistemas) | trecho: ### Transições de Estados (2) - Ready to Running:
