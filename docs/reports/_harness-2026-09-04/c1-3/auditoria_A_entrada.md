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
[1] curso MF | TOPICO 1.3 Abordagens para Verificação Formal | CATEGORIA: Abordagens para Verificação Formal | TERMO: Verificação de Modelos (Model Checking):
[2] curso MF | TOPICO 1.3 Abordagens para Verificação Formal | CATEGORIA: Abordagens para Verificação Formal | TERMO: É baseado em modelos
[3] curso MF | TOPICO 1.3 Abordagens para Verificação Formal | CATEGORIA: Abordagens para Verificação Formal | TERMO: Verificação Dedutiva:
[4] curso MF | TOPICO 1.3 Abordagens para Verificação Formal | CATEGORIA: Abordagens para Verificação Formal | TERMO: Verificação baseada em inferência (portanto, em provas)
[5] curso MF | TOPICO 2.1 Lógica de Hoare | CATEGORIA: Lógica de Floyd-Hoare | TERMO: Abordagem que usaremos:
[6] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Aspectos de proteção e compartilhamento | TERMO: Problema associado:
[7] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (1) | TERMO: Constituídos de 2 partes:
[8] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (1) | TERMO: Mecânica
[9] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (1) | TERMO: Eletrônica – Controladora ou Adaptadora
[10] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (1) | TERMO: Controladora
[11] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Controladora (cont.)
[12] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Também tratar o acesso do dispositivo ao barramento
[13] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Tarefas típicas
[14] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Correção de erros
[15] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Possui registradores usados para comunicar com o SO
[16] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Tipicamente tem memória interna (buffer)
[17] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: Dispositivos de Entrada e Saída (2) | TERMO: Compatibilizar velocidades
[18] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Orientado a caractere | TERMO: stream
[19] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Orientado a caractere | TERMO: character device
[20] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Orientado a caractere | TERMO: unbuffered
[21] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diagrama de árvore de diretórios mostrando a estrutura de nomes de dispositivos em UNIX. O | TERMO: llyS0
[22] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diagrama de árvore de diretórios mostrando a estrutura de nomes de dispositivos em UNIX. O | TERMO: llyS1
[23] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diagrama de árvore de diretórios mostrando a estrutura de nomes de dispositivos em UNIX. O | TERMO: llyS2 e llyS3
[24] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: O diagrama ilustra a arquitetura de software para o subsistema de entrada e saída. No topo | TERMO: "Driver IDE"
[25] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: O diagrama ilustra a arquitetura de software para o subsistema de entrada e saída. No topo | TERMO: há ícones representando um disco rígido
[26] curso SO | TOPICO 2.1 Dispositivos de entrada e saída | CATEGORIA: O diagrama ilustra a arquitetura de software para o subsistema de entrada e saída. No topo | TERMO: uma disquete e um CD-ROM. À direita
[27] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Fundamentos
[28] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Paginação sob Demanda
[29] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Criação de Processos
[30] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Substituição de Páginas
[31] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Alocação de Blocos (frames)
[32] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Paginação Excessiva (Thrashing)
[33] curso SO | TOPICO 6.2 Memória virtual | CATEGORIA: Capítulo 9: Memória Virtual | TERMO: Segmentação sob Demanda
[34] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Características da paginação | TERMO: Paginação é um tipo de relocação (via hardware)
[35] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Características da paginação | TERMO: Fragmentação interna é restrita apenas a última página
[36] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Características da paginação | TERMO: Importante:
[37] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Características da paginação | TERMO: Visão do usuário: espaço de endereçamento contíguo
[38] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Características da paginação | TERMO: Tabela de páginas
[39] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Características da paginação | TERMO: Facilita implementação de proteção e compartilhamento
[40] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Proteção | TERMO: Proteção de acesso é garantida por definição:
[41] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Proteção | TERMO: Processos acessam somente suas páginas end. válidos
[42] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Proteção | TERMO: Endereço inválido apenas na última página
[43] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Proteção | TERMO: ▶ Se houver fragmentação interna
[44] curso SO | TOPICO 7.4 Proteção | CATEGORIA: Proteção | TERMO: Bit de validade:
[45] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Gerência de Arquivos | TERMO: Oferece a abstração de arquivos (e diretórios)
[46] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Gerência de Arquivos | TERMO: criar, deletar – create(), unlink()
[47] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Gerência de Arquivos | TERMO: abrir, fechar – open(), close()
[48] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Gerência de Arquivos | TERMO: ler, escrever – read(), write()
[49] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Gerência de Arquivos | TERMO: posicionar – lseek()
[50] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Sistema de Arquivos | TERMO: Arquivo
[51] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Sistema de Arquivos | TERMO: É composto por:
[52] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Sistema de Arquivos | TERMO: Nome: identifica o arquivo perante o utilizador
[53] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Descritor de arquivo | TERMO: datas de criação
[54] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Descritor de arquivo | TERMO: modificação e acesso
[55] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Descritor de arquivo | TERMO: dono
[56] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Descritor de arquivo | TERMO: autorizações de acesso)
[57] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Sistema de Arquivos | TERMO: Informação: dados guardados em memória secundária
[58] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Arquivos Regulares
[59] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Arquivos ASCII
[60] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Binários
[61] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Apresentam uma estrutura interna conhecida pelo S.O
[62] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Diretórios
[63] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Arquivos do sistema
[64] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Tipos de Arquivos (1) | TERMO: Mantêm a estrutura do Sistemas de Arquivos
[65] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: Dependem do tipo
[66] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: create
[67] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: delete
[68] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: open
[69] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: close
[70] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: read
[71] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: write
[72] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: append
[73] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: seek
[74] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: get attributes
[75] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: set attributes
[76] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Operações sobre Arquivos | TERMO: rename
[77] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios <sup>(1)</sup> | TERMO: localização física, nome, organização e demais atributos
[78] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (2) | TERMO: Sistemas de Diretório em Nível Único
[79] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (2) | TERMO: Implementação mais simples
[80] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (2) | TERMO: Isso ocasionaria um conflito no acesso aos arquivos
[81] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (3) | TERMO: Estrutura de diretórios com dois níveis
[82] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (3) | TERMO: Cada entrada aponta para o diretório pessoal
[83] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (4) | TERMO: Estrutura de diretórios Hierárquicos
[84] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (4) | TERMO: Adotado pela maioria dos sistemas operacionais
[85] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (4) | TERMO: Logicamente melhor organizado
[86] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Diretórios (4) | TERMO: É possível criar quantos diretórios quiser
[87] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Esquema do Sistema de Arquivos (2) | TERMO: As informações sobre os blocos livres
[88] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (4) | TERMO: Alocação por Lista Encadeada
[89] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (4) | TERMO: É necessário que o disco seja desfragmentado periodicamente
[90] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (6) | TERMO: Alocação por Lista Encadeada usando Tabela na Memória
[91] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (6) | TERMO: FAT (File Allocation Table)
[92] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (6) | TERMO: Vantagens:
[93] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (6) | TERMO: Permitir o acesso direto aos blocos
[94] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (7) | TERMO: Desvantagem
[95] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (8) | TERMO: i-nodes
[96] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (8) | TERMO: Ocupa menos espaço que a FAT
[97] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Implementação de Arquivos (8) | TERMO: Usados por sistemas baseados no UNIX
[98] curso SO | TOPICO 7.2 Diretórios | CATEGORIA: Relação entre Diretórios e i-nodes (2) | TERMO: Passos para alcançar /usr/ast/mbox
[99] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Exemplo de Programa Multithread (1) | TERMO: Editor de Texto
[100] curso SO | TOPICO 4.1 Programas multithreads | CATEGORIA: Exemplo de Programa Multithread (1) | TERMO: Processamento assíncrono (salvamento periódico)
[101] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Útil para aplicações que requerem características avançadas de sistemas operacionais | TERMO: ex: multimídia
[102] curso SO | TOPICO 5.2 Caracterização | CATEGORIA: Útil para aplicações que requerem características avançadas de sistemas operacionais | TERMO: realidade virtual
[103] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Unidade 06 — Gerência de arquivos | TERMO: [ ] 7.1 Arquivos
[104] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Unidade 06 — Gerência de arquivos | TERMO: [ ] 7.2 Diretórios
[105] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Unidade 06 — Gerência de arquivos | TERMO: [ ] 7.3 Implementação de sistemas de arquivos
[106] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Unidade 06 — Gerência de arquivos | TERMO: [ ] 7.4 Proteção
[107] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Unidade 06 — Gerência de arquivos | TERMO: [ ] 7.5 Segurança
[108] curso SO | TOPICO 7.1 Arquivos | CATEGORIA: Unidade 06 — Gerência de arquivos | TERMO: [ ] 7.6 Estudo de casos
[109] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Gerência de configuração | TERMO: Gerência de versões e mudanças
[110] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Gerência de configuração | TERMO: Git
[111] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Gerência de configuração | TERMO: Gerência de dependências internas e automação de construção
[112] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Gerência de configuração | TERMO: Maven, Gradle, Npm, Yarn
[113] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Gerência de configuração | TERMO: Gerência de pacotes
[114] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Gerência de configuração | TERMO: Apt, Homebrew, Windows package manager
[115] curso ES2 | TOPICO 2.3 Integração contínua (CI) | CATEGORIA: Integração contínua (CI) | TERMO: [GitHub actions](#), [Jenkins](#), [Travis CI](#)
[116] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Princípios e padrões de arquitetura de sistemas. Descrição estrutural e comportamental de  | TERMO: integração
[117] curso ES2 | TOPICO 2.2 Gerenciamento da Configuração | CATEGORIA: Princípios e padrões de arquitetura de sistemas. Descrição estrutural e comportamental de  | TERMO: de sistema
[118] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Uma função é efetivamente computável se e somente se é computável por uma Máquina de Turin | TERMO: ou equivalentemente
[119] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Uma função é efetivamente computável se e somente se é computável por uma Máquina de Turin | TERMO: é uma função recursiva
[120] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Componentes de uma Máquina de Turing | TERMO: 1 Fita: memória infinita dividida em células
[121] curso TCC | TOPICO 2.1 Máquinas de Turing | CATEGORIA: Componentes de uma Máquina de Turing | TERMO: 3 Controle: estados que determinam o comportamento
[122] curso TCC | TOPICO 4.5 Classe NP | CATEGORIA: Classe NP | TERMO: Linguagens decidíveis por MTN em tempo polinomial
[123] curso TCC | TOPICO 4.7 Intratabilidade | CATEGORIA: Evidências de Intratabilidade | TERMO: 2 Problema é PSPACE-hard
[124] curso TCC | TOPICO 4.7 Intratabilidade | CATEGORIA: Evidências de Intratabilidade | TERMO: 3 Problema é EXPTIME-complete
[125] curso TCC | TOPICO 4.7 Intratabilidade | CATEGORIA: Evidências de Intratabilidade | TERMO: 4 Problema requer tempo/espço super-polinomial (provado)
[126] curso TCC | TOPICO 1.1 Conjuntos Enumeráveis | CATEGORIA: Estudo dos conjuntos enumeráveis e provas por diagonalização. Estudo da teoria das funções | TERMO: classe P
[127] curso TCC | TOPICO 1.1 Conjuntos Enumeráveis | CATEGORIA: UNIDADE 01: Conjuntos Enumeráveis e Funções Recursivas | TERMO: 1.1. Conjuntos Enumeráveis
[128] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.1. Tipos de Problemas Computacionais
[129] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.2. Complexidade de Tempo e de Espaço
[130] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.5. Classe NP
[131] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.5.1. Definição da Classe
[132] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.5.3 Teorema de Cook-Levin
[133] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.5.4 Redução Polinomial de Problemas
[134] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.5.5 Provas de NP-Completeness
[135] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.6 Classe PSPACE
[136] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.6.1 Definição da Classe
[137] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.6.3 Provas de PSPACE-Completeness
[138] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: 4.7 Intratabilidade
[139] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: Unidade 04 — Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: [ ] 4.5.5 Provas de NP-Completude
[140] curso TCC | TOPICO 4.3 Hierarquia de Classes de Complexidade de Problemas | CATEGORIA: Unidade 04 — Hierarquia de Classes de Complexidade de Problemas Computacionais | TERMO: [ ] 4.6.3 Provas de PSPACE-Completude
[141] curso CG | TOPICO 6.3 Projeções | CATEGORIA: Tipos mais comuns de projeções ortográficas são | TERMO: FRONTAL
[142] curso CG | TOPICO 6.3 Projeções | CATEGORIA: Tipos mais comuns de projeções ortográficas são | TERMO: LATERAL e SUPERIOR
[143] curso CG | TOPICO 6.3 Projeções | CATEGORIA: Tipos mais comuns de projeções ortográficas são | TERMO: z):
[144] curso CG | TOPICO 1.4 Aplicações | CATEGORIA: n Depende da aplicação | TERMO: complexidade da cena
[145] curso CG | TOPICO 1.4 Aplicações | CATEGORIA: n Depende da aplicação | TERMO: tipos de objetos
[146] curso CG | TOPICO 1.4 Aplicações | CATEGORIA: n Depende da aplicação | TERMO: equipamento disponível
[147] curso CG | TOPICO 1.4 Aplicações | CATEGORIA: Em uma aplicação, muitas vezes, temos objetos que são derivados de um mesmo modelo, por ex | TERMO: "numa planta baixa temos várias mesas
[148] curso CG | TOPICO 1.4 Aplicações | CATEGORIA: Em uma aplicação, muitas vezes, temos objetos que são derivados de um mesmo modelo, por ex | TERMO: com a mesma estrutura básica
[149] curso CG | TOPICO 1.4 Aplicações | CATEGORIA: Em uma aplicação, muitas vezes, temos objetos que são derivados de um mesmo modelo, por ex | TERMO: na cor e no posicionamento dentro da casa"
[150] curso CG | TOPICO 3.5 Segmentação | CATEGORIA: O desenho desses dois segmentos é feito com a primitiva GLLINES , com a qual o OpenGL inte | TERMO: os dois primeiros vértices formam o eixo X
[151] curso CG | TOPICO 3.5 Segmentação | CATEGORIA: O desenho desses dois segmentos é feito com a primitiva GLLINES , com a qual o OpenGL inte | TERMO: e os dois seguintes formam o eixo Y
[152] curso CG | TOPICO 1.3 Áreas relacionadas | CATEGORIA: 1.3. Áreas relacionadas | TERMO: 1.4. Aplicações
[153] curso CG | TOPICO 5.1 Transformações Geométricas e coordenadas homogêneas 2D | CATEGORIA: 5.1. Transformações Geométricas e coordenadas homogêneas 2D | TERMO: 5.2. Mapeamento Window e Viewport
[154] curso CG | TOPICO 5.1 Transformações Geométricas e coordenadas homogêneas 2D | CATEGORIA: 5.1. Transformações Geométricas e coordenadas homogêneas 2D | TERMO: 5.3. Pipeline de visualização 2D
[155] curso CG | TOPICO 5.1 Transformações Geométricas e coordenadas homogêneas 2D | CATEGORIA: 5.1. Transformações Geométricas e coordenadas homogêneas 2D | TERMO: 5.4. Composição de transformações 2D
[156] curso CG | TOPICO 5.1 Transformações Geométricas e coordenadas homogêneas 2D | CATEGORIA: 5.1. Transformações Geométricas e coordenadas homogêneas 2D | TERMO: 5.5. Representação matricial das transformações 3D
[157] curso CG | TOPICO 5.1 Transformações Geométricas e coordenadas homogêneas 2D | CATEGORIA: 5.1. Transformações Geométricas e coordenadas homogêneas 2D | TERMO: 5.6. Composição de transformações 3D
[158] curso CG | TOPICO 3.5 Segmentação | CATEGORIA: Tomando o segmento de reta | TERMO: yf)
[159] curso CG | TOPICO 1.2 Conceitos | CATEGORIA: Da definição acima devem ser bem entendidos e diferenciados dois conceitos | TERMO: normalmente
[160] curso CG | TOPICO 1.2 Conceitos | CATEGORIA: Da definição acima devem ser bem entendidos e diferenciados dois conceitos | TERMO: um possível modelo
[161] curso CG | TOPICO 1.2 Conceitos | CATEGORIA: Da definição acima devem ser bem entendidos e diferenciados dois conceitos | TERMO: é o seguinte:
[162] curso FR | TOPICO 3.2 Protocolo TCP | CATEGORIA: FOROUZAN, B.; FEGAN, S. Protocolo TCP/IP. 3ª ed. Porto Alegre | TERMO: Bookman
[163] curso FR | TOPICO 3.2 Protocolo TCP | CATEGORIA: FOROUZAN, B.; FEGAN, S. Protocolo TCP/IP. 3ª ed. Porto Alegre | TERMO: 2010 (recurso online)
