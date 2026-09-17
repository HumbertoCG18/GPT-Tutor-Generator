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

CATEGORIAS (lote 2):
[121] categoria: Transições de Estados (3) | termos: Running to Ready:; Processo é preemptado pelo S.O; Running to Blocked:; Blocked to Ready: | trecho: ### Transições de Estados (3) - Running to Ready:
[122] categoria: Considerações gerais | termos: Memória principal: acessada pela CPU; Memória secundária: discos; Qualquer sistema operacional tem gerência de memór; Monotarefa: gerência é simples | trecho: ## Considerações gerais - Memória principal: acessada pela CPU
[123] categoria: Memória lógica vs memória física | termos: Memória lógica; É aquela que o processo "enxerga"; Memória física; Implementada pelos circuitos integrados de memória | trecho: ### Memória lógica vs memória física - Memória lógica
[124] categoria: Endereço lógico versus endereço físico | termos: Endereço lógico: gerado pela CPU (endereço virtual; Endereço físico: endereços enviados para a memória; Programas de usuários “vêm” apenas endereços lógic | trecho: ### Endereço lógico versus endereço físico - Endereço lógico: gerado pela CPU (endereço virtual)
[125] categoria: Unidade de Gerenciamento de Memória | termos: Memory Management Unit (MMU) | trecho: ## Unidade de Gerenciamento de Memória - **Memory Management Unit (MMU)**
[126] categoria: Access | termos: Since both comparisons pass | trecho: - Access:** Since both comparisons pass, the processor is allowed to access the memory (Memória).
[127] categoria: Comparison 1 | termos: indicating an illegal address; which triggers an Interrupção (Endereço ilegal) | trecho: - Comparison 1:** The address 123 is compared with the limit (200) using a greater-than (>) operator. The result is "sim" (yes), indicating an illegal address, which triggers an **
[128] categoria: Execução de programas | termos: Alocação de um descritor de processos; Amarração de endereços (binding) | trecho: ## Execução de programas - Alocação de um descritor de processos
[129] categoria: Amarração de endereços (binding) | termos: Em tempo de compilação; Em tempo de carga; Em tempo de execução; Como traduzir endereço lógico em endereço físico | trecho: ### Amarração de endereços (*binding*) - Em tempo de compilação
[130] categoria: Carregador absoluto vs carregador relocador | termos: Endereço só é conhecido no momento da carga; ▶ e.g.; procedimento de swapping; Necessidade de traduzir endereços lógicos à endere; Relocação é a técnica que fornece essa tradução | trecho: ### Carregador absoluto vs carregador relocador - Endereço só é conhecido no momento da carga
[131] categoria: Código relocável | termos: Carregador relocador; Código relocável | trecho: #### Código relocável - Carregador relocador
[132] categoria: Código absoluto | termos: Carregador absoluto; Endereço de carga; Fixo pelo programa (programador); Qualquer | trecho: #### Código absoluto - Carregador absoluto
[133] categoria: Mecanismos básicos de gerência de memória | termos: ▶ Problema de alocação de memória; A alocação de memória depende de:; Código absoluto versus código relocável; Necessidade de gerenciamento da memória | trecho: ## Mecanismos básicos de gerência de memória - ▶ Problema de alocação de memória
[134] categoria: Definição (1) | termos: Sincronização por memória compartilhada; Solução:; ▶ Sincronização por troca de mensagens; O SO tenta usar o hardware com eficiência | trecho: ### Definição (1) - **Sincronização por memória compartilhada**
[135] categoria: Send | termos: destinatário; mensagem; destination; message\buffer | trecho: - **Send (destinatário, mensagem)**
[136] categoria: Receive | termos: remetente; mensagem; source; message\buffer | trecho: - **Receive (remetente, mensagem)**
[137] categoria: Primitivas | termos: send (destination, message\buffer); receive (source, message\buffer) | trecho: ### Primitivas - **send (destination, message\_buffer)**
[138] categoria: Endereçamento Indireto (2) | termos: Relacionamentos entre transmissor e receptor; Muitos-para-um: útil para interação cliente-servid; Outras questões: | trecho: ### Endereçamento Indireto (2) - Relacionamentos entre transmissor e receptor
[139] categoria: Mailbox ownership | termos: no caso de um port; o criador é o dono | trecho: - Mailbox ownership: no caso de um port, ele é tipicamente criado e tem como dono o processo receptor. Para um mailbox genérico, o S.O. pode oferecer um serviço do tipo create\_mai
[140] categoria: Sincronização (1) | termos: "Blocking send, blocking receive":; Mecanismo conhecido como "rendezvous" (encontro); "Nonblocking send, blocking receive": | trecho: ### Sincronização (1) - "Blocking send, blocking receive":
[141] categoria: Emissor continua processando normalmente | termos: p.ex; enviando novas mensagens | trecho: - Emissor continua processando normalmente (p.ex., enviando novas mensagens).
[142] categoria: Sincronização (2) | termos: "Nonblocking send, blocking receive" (cont.); Esquema mais usado | trecho: ### Sincronização (2) - "Nonblocking send, blocking receive" (cont.)
[143] categoria: Com "blocking receive" o processo receptor pode ficar bloqueado eternamente se a mensagem  | termos: soluções: uso de timeout; uso de mais de uma fonte | trecho: - Com "blocking receive" o processo receptor pode ficar bloqueado eternamente se a mensagem enviada se perder (soluções: uso de timeout, uso de mais de uma fonte, etc.)
[144] categoria: Sincronização (3) | termos: "Nonblocking send, nonblocking receive"; Nenhuma parte envolvida na comunicação precisa esp | trecho: ### Sincronização (3) - "Nonblocking send, nonblocking receive"
[145] categoria: Fila | termos: FIFO; Named Pipe | trecho: - Fila (FIFO, Named Pipe)
[146] categoria: Comunicação entre Processos (1) | termos: Processos executam em cápsulas autônomas; Hardware oferece proteção de memória | trecho: ### Comunicação entre Processos (1) - Processos executam em cápsulas autônomas
[147] categoria: Comunicação entre Processos (2) | termos: dividir tarefas e aumentar a velocidade de computa; aumentar da capacidade de processamento (rede);; atender a requisições simultâneas; IPC - Inter-Process Communication | trecho: ### Comunicação entre Processos (2) - dividir tarefas e aumentar a velocidade de computação;
[148] categoria: Comunicação entre Processos (4) | termos: Características desejáveis para IPC; Rápida; Simples de ser utilizada e implementada; Possuir um modelo de sincronização bem definido | trecho: ## Comunicação entre Processos (4) - Características desejáveis para IPC
[149] categoria: Mecanismos de IPC | termos: Fundamentalmente, existem duas abordagens:; Suportar alguma forma de espaço de endereçamento c; Shared memory (memória compartilhada); Pipes e Sinais (ambiente centralizado) | trecho: ### Mecanismos de IPC - Fundamentalmente, existem duas abordagens:
[150] categoria: Tubos (Pipes) (2) | termos: Um pipe tradicional caracteriza-se por ser:; A capacidade do pipe é limitada | trecho: ### Tubos (Pipes) (2) - Um *pipe* tradicional caracteriza-se por ser:
[151] categoria: Se a escrita sobre um pipe continua mesmo depois dele estar cheio, ocorre uma situação de  | termos: conseqüentemente; abra espaço no pipe | trecho: - Se a escrita sobre um *pipe* continua mesmo depois dele estar cheio, ocorre uma situação de bloqueio (que permanece até que algum outro processo leia e, conseqüentemente, abra es
[152] categoria: Uso de Pipes | termos: who | sort | lpr; + output of who is input to sort; + output of sort is input to lpr | trecho: #### Uso de Pipes - `who | sort | lpr`
[153] categoria: The diagram illustrates the flow of data through a pipeline of programs and their connecti | termos: Program1; Program2; and Program3 | trecho: The diagram illustrates the flow of data through a pipeline of programs and their connection to a Text terminal and a Display. A vertical grey bar on the left represents the 'Text 
[154] categoria: Criação de Pipes <sup>(1)</sup> | termos: Um pipe é criado pela chamada de sistema: | trecho: #### Criação de Pipes <sup>(1)</sup> - Um *pipe* é criado pela chamada de sistema:
[155] categoria: Flow of data | termos: Below the pipe component; indicating the direction of data transfer | trecho: - Flow of data:** Below the `pipe` component, the text "flow of data" is accompanied by two horizontal arrows pointing in opposite directions, indicating the direction of data tran
[156] categoria: Comunicação Pai-Filho Bi-Direcional | termos: Pai cria pipe1 e pipe2; Pai fecha descritor de leitura de pipe1; Pai fecha descritor de escrita de pipe2; Filho fecha descritor de escrita de pipe1 | trecho: #### Comunicação Pai-Filho Bi-Direcional - Pai cria pipe1 e pipe2.
[157] categoria: The diagram illustrates the data flow between three processes | termos: who; sort; and lpr | trecho: The diagram illustrates the data flow between three processes: *who*, *sort*, and *lpr*, connected by pipes (*pipe1* and *pipe2*) within the kernel space.
[158] categoria: Escrita e Leitura em Pipes (2) | termos: Regras aplicadas aos processos escritores:; Regras aplicadas aos processos leitores:; Leitura para descritor fechado retorna valor 0 | trecho: #### Escrita e Leitura em Pipes (2) - Regras aplicadas aos processos escritores:
[159] categoria: O número de bytes que podem ser temporariamente armazenados por um pipe é indicado por POS | termos: 512B | trecho: - O número de bytes que podem ser temporariamente armazenados por um *pipe* é indicado por `_POSIX_PIPE_BUF` (512B, definido em `<limits.h>`).
[160] categoria: Fila (FIFO, Named Pipe) | termos: As Filas:; persistem além da vida do processo | trecho: ### Fila (FIFO, Named Pipe) - As Filas:
[161] categoria: Criação de Filas <sup>(1)</sup> | termos: Uma fila é criada pela chamada de sistema: | trecho: #### Criação de Filas <sup>(1)</sup> - Uma fila é criada pela chamada de sistema:
[162] categoria: 2º parâmetro | termos: identifica as permissões de acesso; iguais a qualquer arquivo; determinados por OU de grupos de bits | trecho: - 2º parâmetro: identifica as permissões de acesso, iguais a qualquer arquivo, determinados por OU de grupos de bits.
[163] categoria: As permissões de acesso também podem ser indicados por 3 dígitos octais, cada um represent | termos: Read; Write; eXecute | trecho: - As permissões de acesso também podem ser indicados por 3 dígitos octais, cada um representando os valores binários de rwx (Read, Write, eXecute).
[164] categoria: Abertura de Filas (2) | termos: Regras aplicadas na abertura de filas: | trecho: #### Abertura de Filas (2) - Regras aplicadas na abertura de filas:
[165] categoria: a opção ONONBLOCK tiver sido indicada no momento da leitura | termos: nesse caso | trecho: - a opção `O_NONBLOCK` tiver sido indicada no momento da leitura (nesse caso, é devolvido o valor -1 e `errno` fica com valor `ENXIO`).
[166] categoria: a opção ONONBLOCK tiver sido indicada no momento da escrita | termos: nesse caso | trecho: - a opção `O_NONBLOCK` tiver sido indicada no momento da escrita (nesse caso, é devolvido o valor -1 e `errno` fica com valor `ENXIO`).
[167] categoria: Resumo | termos: Um processo é um programa individual em execução | trecho: ## Resumo - Um processo é um programa individual em execução
[168] categoria: Os principais estados de um processo são | termos: New; Ready; Running; Blocked e Exit | trecho: - Os principais estados de um processo são: **New, Ready, Running, Blocked e Exit**
[169] categoria: O diagrama ilustra a criação e execução de três processos | termos: Processo A; e fork C; . Enquanto isso; Processo A executa wait C | trecho: O diagrama ilustra a criação e execução de três processos: **Processo A**, **Processo B** e **Processo C**. **Processo A** executa as instruções `fork B;` e `fork C;`, criando **Pr
[170] categoria: Criação de processos no Linux | termos: exec(): carrega e executa um novo programa | trecho: ### Criação de processos no Linux - *exec()*: carrega e executa um novo programa
[171] categoria: exit | termos: termina o processo corrente. Os filhos; se existirem | trecho: - **exit:** termina o processo corrente. Os filhos, se existirem, são herdados pelo processo init e o processo pai é sinalizado.
[172] categoria: exec | termos: executa um programa; identificado pelo nome de um arquivo executável; passado como argumento | trecho: - **exec:** executa um programa, substituindo a imagem do processo corrente pela imagem de um novo processo, identificado pelo nome de um arquivo executável, passado como argumento
[173] categoria: Imagem do processo | termos: Nome dado à coleção formada por:; text: código do programa a ser executado | trecho: ### Imagem do processo - Nome dado à coleção formada por:
[174] categoria: Diagrama da imagem do processo na memória, mostrando a disposição das áreas de memória | termos: stack; heap; data e text | trecho: Diagrama da imagem do processo na memória, mostrando a disposição das áreas de memória: stack, heap, data e text.
[175] categoria: Bloco de Controle do Processo (PCB) | termos: Process Control Block | trecho: ## Bloco de Controle do Processo (PCB) - *Process Control Block.*
[176] categoria: Informações típicas do BCP | termos: Prioridade do processo; Localização na memória principal; Identificação dos arquivos abertos; Estado do processo | trecho: ### Informações típicas do BCP - Prioridade do processo.
[177] categoria: Informações de controle do processo (1) | termos: Informações de escalonamento e estado:; Prioridade; Tempo de espera na fila; Tempo de execução na última fatia de tempo | trecho: ### Informações de controle do processo (1) - Informações de escalonamento e estado:
[178] categoria: Estado do processo | termos: ready; running; suspended | trecho: - Estado do processo (ready, running, suspended, etc.)
[179] categoria: Informações de controle do processo (2) | termos: Comunicação entre processos:; Ownership e utilização de recursos:; Arquivos abertos; | trecho: ### Informações de controle do processo (2) - Comunicação entre processos:
[180] categoria: The diagram illustrates the mapping of logical pages to physical frames for Process A. On  | termos: Page 0 maps to Frame 1; Page 1 maps to Frame 3; Page 2 maps to Frame 5 | trecho: The diagram illustrates the mapping of logical pages to physical frames for Process A. On the left, a vertical stack of four boxes represents the logical pages, labeled 'Página' at
[181] categoria: Endereço lógico | termos: Endereço lógico é dividido em duas componentes:; Número da página; Deslocamento dentro de uma página | trecho: ## Endereço lógico - Endereço lógico é dividido em duas componentes:
[182] categoria: Exemplo de paginação (1) | termos: Características do sistema:; Memória física: 64 kbytes (16 bits); Paginação:; Deslocamento: 8 kbytes 13 bits 15 bits | trecho: ### Exemplo de paginação (1) - Características do sistema:
[183] categoria: Características da paginação | termos: Paginação é um tipo de relocação (via hardware); Fragmentação interna é restrita apenas a última pá; Importante:; Visão do usuário: espaço de endereçamento contíguo | trecho: ## Características da paginação - Paginação é um tipo de relocação (via hardware)
[184] categoria: Tamanho da página | termos: Páginas grandes significam; Aumento da fragmentação interna na última página; Páginas pequenas significam; Diminuição da fragmentação interna na última págin | trecho: ## Tamanho da página - Páginas grandes significam
[185] categoria: Questões relacionadas com a gerência de páginas | termos: Inclusão de mecanismos de proteção; Garantir que um processo acesse apenas endereços v; Garantir acessos autorizados a uma posição de memó; Inclusão de mecanismos de compartilhamento | trecho: ## Questões relacionadas com a gerência de páginas - Inclusão de mecanismos de proteção
[186] categoria: Proteção | termos: Proteção de acesso é garantida por definição:; Processos acessam somente suas páginas end. válido; Endereço inválido apenas na última página; ▶ Se houver fragmentação interna | trecho: ### Proteção - Proteção de acesso é garantida por definição:
[187] categoria: Compartilhamento de páginas | termos: Código compartilhado; Dados e código próprios | trecho: ## Compartilhamento de páginas - Código compartilhado
[188] categoria: Process 1 | termos: 2 (P0); and 4 (P0/P1) | trecho: **Process 1:** Valid/Shared (Válido/Compartilhado) state. Its page table (Tabela de páginas) points to physical memory frames 1 (P1), 2 (P0), and 4 (P0/P1).
[189] categoria: Process 2 | termos: 5 (P3); 6 (P3); and 7 (P2) | trecho: **Process 2:** Valid/Shared (Válido/Compartilhado) state. Its page table (Tabela de páginas) points to physical memory frames 4 (P0/P1), 5 (P3), 6 (P3), and 7 (P2).
[190] categoria: Implementação da tabela de páginas | termos: Frames livres/alocados; Registradores; Memória | trecho: ## Implementação da tabela de páginas - Frames livres/alocados
[191] categoria: Implementação da tabela de páginas via registradores | termos: Cada página um registrador; ▶ Troca de contexto: atualização dos registradores; Desvantagem é o número de registradores | trecho: ### Implementação da tabela de páginas via registradores - Cada página um registrador
[192] categoria: Implementação da tabela de páginas em memória | termos: Tabela de páginas é mantida em memória | trecho: ### Implementação da tabela de páginas em memória - Tabela de páginas é mantida em memória
[193] categoria: Número de acesso depende da largura da entrada da tabela de página e de como a memória é a | termos: byte; word | trecho: - Número de acesso depende da largura da entrada da tabela de página e de como a memória é acessada (byte, word, etc...)
[194] categoria: Page Table | termos: A table with multiple entries | trecho: - Page Table**: A table with multiple entries, each representing a page. The entry selected is the **frame da página** (page frame).
[195] categoria: Registradores associativos | termos: Pesquisa paralela | trecho: #### Registradores associativos - Pesquisa paralela
[196] categoria: TLB | termos: Translation Lookaside Buffer; a cache for recent translations | trecho: - TLB:** Translation Lookaside Buffer, a cache for recent translations.
[197] categoria: Aspectos relacionados com o uso de TLB | termos: Desvantagem é o seu custo; Tamanho limitado (de 8 a 2048 entradas); Um acesso é feito em duas partes: | trecho: #### Aspectos relacionados com o uso de TLB - Desvantagem é o seu custo
[198] categoria: Necessidade de Armazenamento | termos: Grandes quantidades de informação têm de ser armaz; Definição de estruturas (organização, hierarquia, ; ARQUIVO | trecho: ## Necessidade de Armazenamento - Grandes quantidades de informação têm de ser armazenadas
[199] categoria: Definição de estruturas | termos: organização; hierarquia; relação entre informação | trecho: - Definição de estruturas (organização, hierarquia, relação entre informação)
[200] categoria: Gerência de Arquivos | termos: Oferece a abstração de arquivos (e diretórios); criar, deletar – create(), unlink(); abrir, fechar – open(), close(); ler, escrever – read(), write() | trecho: ## Gerência de Arquivos - Oferece a abstração de arquivos (e diretórios)
[201] categoria: The diagram illustrates the internal structure of the UNIX kernel, organized into three ma | termos: User level; Kernel level; and Hardware level | trecho: The diagram illustrates the internal structure of the UNIX kernel, organized into three main levels: User level, Kernel level, and Hardware level.
[202] categoria: File Subsystem | termos: (Highlighted in green) Manages file operations; interacting with the Buffer cache; Character and block devices; and Device drivers | trecho: - File Subsystem:** (Highlighted in green) Manages file operations, interacting with the **Buffer cache**, **Character** and **block** devices, and **Device drivers**.
[203] categoria: Process control system | termos: Manages system processes; including Interprocess communication; the scheduler; and Memory management | trecho: - Process control system:** Manages system processes, including **Interprocess communication**, the **scheduler**, and **Memory management**.
[204] categoria: Permitem estruturar o armazenamento e a recuperação de dados persistentes em um ou mais di | termos: discos; fitas magnéticas | trecho: - Permitem estruturar o armazenamento e a recuperação de dados persistentes em um ou mais dispositivos de memória secundária (discos, fitas magnéticas, etc)
[205] categoria: Sistema de Arquivos | termos: Arquivo; É composto por:; Nome: identifica o arquivo perante o utilizador; Informação: dados guardados em memória secundária | trecho: ## Sistema de Arquivos - Arquivo
[206] categoria: Descritor de arquivo | termos: datas de criação; modificação e acesso; dono; autorizações de acesso) | trecho: - Descritor de arquivo: estrutura de dados em memória secundária com informação sobre o arquivo (dimensão, datas de criação, modificação e acesso, dono, autorizações de acesso)
[207] categoria: Tipos de Arquivos (1) | termos: Arquivos Regulares; Arquivos ASCII; Binários; Apresentam uma estrutura interna conhecida pelo S. | trecho: ### Tipos de Arquivos (1) - Arquivos Regulares
[208] categoria: Operações sobre Arquivos | termos: Dependem do tipo; create; delete; open | trecho: ## Operações sobre Arquivos - Dependem do tipo
[209] categoria: Diretórios <sup>(1)</sup> | termos: localização física, nome, organização e demais atr | trecho: ### Diretórios <sup>(1)</sup> - localização física, nome, organização e demais atributos
[210] categoria: Diretórios (2) | termos: Sistemas de Diretório em Nível Único; Implementação mais simples; Isso ocasionaria um conflito no acesso aos arquivo | trecho: ### Diretórios (2) - Sistemas de Diretório em Nível Único
[211] categoria: Diretórios (3) | termos: Estrutura de diretórios com dois níveis; Cada entrada aponta para o diretório pessoal | trecho: ### Diretórios (3) - Estrutura de diretórios com dois níveis
[212] categoria: Diretórios (4) | termos: Estrutura de diretórios Hierárquicos; Adotado pela maioria dos sistemas operacionais; Logicamente melhor organizado; É possível criar quantos diretórios quiser | trecho: ### Diretórios (4) - Estrutura de diretórios Hierárquicos
[213] categoria: The diagram illustrates a hierarchical directory structure. At the top is the root directo | termos: Carlos/; Ivan/ | trecho: The diagram illustrates a hierarchical directory structure. At the top is the root directory `/home/`. It branches into three main directories: `Carlos/`, `Ivan/`, and `Paulo/`. `C
[214] categoria: A definição de um SuperBloco | termos: no. de blocos | trecho: - A definição de um **SuperBloco**: contém os principais parâmetros do sistema de arquivos (tipo, no. de blocos, etc.)
[215] categoria: Esquema do Sistema de Arquivos (2) | termos: As informações sobre os blocos livres | trecho: ### Esquema do Sistema de Arquivos (2) - As informações sobre os blocos livres
[216] categoria: - Alocação Contígua | termos: O acesso é bastante simples; Pré-alocação (fragmentação interna) | trecho: #### - Alocação Contígua - O acesso é bastante simples
[217] categoria: Diagram illustrating contiguous file allocation. A table lists files | termos: 3 blocks); 8 blocks); 5 blocks). Below; blocks 10-12 in blue | trecho: Diagram illustrating contiguous file allocation. A table lists files: readme.txt (start 010, 3 blocks), prova.doc (start 002, 8 blocks), and Aula.pdf (start 017, 5 blocks). Below, 
[218] categoria: Row 2 | termos: orange (2 blocks); white (5 blocks); blue (3 blocks); orange (6 blocks) | trecho: - Row 2:** After two 'aloca' (allocate) operations. The first 'aloca' (blue arrow) places a light blue block at the start. The second 'aloca' (blue arrow) places a light purple blo
[219] categoria: Row 3 | termos: orange (2 blocks); white (5 blocks); blue (3 blocks); white (3 blocks) | trecho: - Row 3:** After two 'remove' (red arrows) operations. The first 'remove' removes the light blue block. The second 'remove' removes the light purple block. The state is: white (1 b
[220] categoria: Row 4 | termos: white (3 blocks); blue (3 blocks); yellow (3 blocks); white (2 blocks) | trecho: - Row 4:** After two more operations. The first 'remove' (red arrow) removes the first white block. The second 'aloca' (blue arrow) places a yellow block after the blue block. The 
[221] categoria: Implementação de Arquivos (4) | termos: Alocação por Lista Encadeada; É necessário que o disco seja desfragmentado perio | trecho: ### Implementação de Arquivos (4) - Alocação por Lista Encadeada
[222] categoria: Implementação de Arquivos (6) | termos: Alocação por Lista Encadeada usando Tabela na Memó; FAT (File Allocation Table); Vantagens:; Permitir o acesso direto aos blocos | trecho: ### Implementação de Arquivos (6) - Alocação por Lista Encadeada usando Tabela na Memória
[223] categoria: FAT | termos: Esquema usado pelo MS-DOS (FAT-16); Win95; Win98; Windows Millennium Edition (FAT-32) | trecho: - FAT : Esquema usado pelo MS-DOS (FAT-16), Win95, Win98, Windows Millennium Edition (FAT-32)
[224] categoria: Implementação de Arquivos (7) | termos: Desvantagem | trecho: ### Implementação de Arquivos (7) - Desvantagem
[225] categoria: Implementação de Arquivos (8) | termos: i-nodes; Ocupa menos espaço que a FAT; Usados por sistemas baseados no UNIX | trecho: ### Implementação de Arquivos (8) - i-nodes
[226] categoria: The diagram illustrates the relationship between directories, inodes, and files. It is enc | termos: directory; inode; and files | trecho: The diagram illustrates the relationship between directories, inodes, and files. It is enclosed in a dashed box and divided into three columns: **directory**, **inode**, and **file
[227] categoria: A horizontal bar representing disk layout with four sections | termos: Boot block; Super block; Inodes (with a vertical line indicating a boundary; and Data | trecho: A horizontal bar representing disk layout with four sections: **Boot block**, **Super block**, **Inodes** (with a vertical line indicating a boundary), and **Data**.
[228] categoria: Relação entre Diretórios e i-nodes (2) | termos: Passos para alcançar /usr/ast/mbox | trecho: ### Relação entre Diretórios e i-nodes (2) - Passos para alcançar /usr/ast/mbox
[229] categoria: FCFS (First-Come First Serve) | termos: Cabeçote inicia na posição 53 | trecho: ### FCFS (First-Come First Serve) - Cabeçote inicia na posição **53**
[230] categoria: SSTF (Shortest Seek Time First) | termos: O SSTF é uma forma de escalonamento SJF | trecho: ### SSTF (Shortest Seek Time First) - O SSTF é uma forma de escalonamento SJF
[231] categoria: Diagram illustrating the SSTF disk scheduling algorithm. The horizontal axis represents cy | termos: then to 53 (distance 16); then to 65 (distance 12); then to 67 (distance 2); then to 98 (distance 31) | trecho: Diagram illustrating the SSTF disk scheduling algorithm. The horizontal axis represents cylinder numbers: 0, 14, 37, 53, 65, 67, 98, 122, 124, 183, 199. The head starts at cylinder
[232] categoria: SCAN | termos: O braço inicia em uma extremidade do disco,; Às vezes chamado de algoritmo Elevator | trecho: ### SCAN - O braço inicia em uma extremidade do disco,
[233] categoria: Diagram illustrating the SCAN disk scheduling algorithm. A horizontal axis represents the  | termos: it starts at cylinder 0; moves right to 14; and 67 | trecho: Diagram illustrating the SCAN disk scheduling algorithm. A horizontal axis represents the disk cylinders, with tick marks at 0, 14, 37, 53, 65, 67, 98, 122, 124, 183, and 199. A bl
[234] categoria: C-SCAN | termos: Tempo de espera mais uniforme que o SCAN; O cabeçote move-se para a outra extremidade; atende requisições durante movimentação; ▶ Nenhuma requisição é atendida na viagem de volta | trecho: #### C-SCAN - Tempo de espera mais uniforme que o SCAN
[235] categoria: C-LOOK | termos: É uma versão do C-SCAN; depois inverte a direção imediatamente | trecho: #### C-LOOK - É uma versão do C-SCAN
[236] categoria: Diagram illustrating the C-LOOK disk scheduling algorithm. A horizontal axis represents th | termos: it starts at 14; moves right to 65; then to 98; and 183. It then jumps to 37 | trecho: Diagram illustrating the C-LOOK disk scheduling algorithm. A horizontal axis represents the disk tracks, with values 0, 14, 37, 53, 65, 67, 98, 122, 124, 183, and 199. A blue line 
[237] categoria: Selecionando um bom algoritmo | termos: e influenciado pelo método de alocação de arquivos | trecho: ### Selecionando um bom algoritmo - e influenciado pelo método de alocação de arquivos
[238] categoria: Ações na Troca de Contexto | termos: Mover o BCP para a fila apropriada; Alterar o BCP do processo selecionado; Alterar as tabelas de gerência de memória; Restaurar o contexto do processo selecionado | trecho: ### Ações na Troca de Contexto 3. Mover o BCP para a fila apropriada
[239] categoria: Definição | termos: Muda do estado executando para esperando; Muda do estado executando para pronto; Muda do estado esperando para pronto; Termina | trecho: ### Definição 1. Muda do estado executando para esperando.
[240] categoria: Dispatcher | termos: Troca de Contexto; Latência de Despacho | trecho: ### Dispatcher - **Troca de Contexto**
