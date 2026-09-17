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

CATEGORIAS (lote 4):
[361] categoria: Text | termos: contém o código do programa; como main() e soma() | trecho: - **Text:** contém o código do programa, como `main()` e `soma()`.
[362] categoria: Resposta: | termos: Data: contém variáveis globais ou estáticas inicia; Heap: memória alocada dinamicamente com malloc | trecho: ## Resposta: - **Data:** contém variáveis globais ou estáticas inicializadas.
[363] categoria: Stack | termos: contém variáveis locais; parâmetros e endereços de retorno | trecho: - **Stack:** contém variáveis locais, parâmetros e endereços de retorno.
[364] categoria: Alocação: | termos: Código de main() e soma() → text; str → ponteiro local na stack; s1, s2, ret → stack; parâmetros a e b de soma() → stack | trecho: ## Alocação: - Código de `main()` e `soma()` → **text**
[365] categoria: Compartilhados entre as threads: | termos: code/text; data; heap; arquivos abertos | trecho: ## Compartilhados entre as threads: - code/text
[366] categoria: Exclusivos de cada thread: | termos: registradores; stack; contador de programa | trecho: ## Exclusivos de cada thread: - registradores
[367] categoria: Linha 4 | termos: executada pelo processo pai original; após fork; existem pai e filho | trecho: - **Linha 4:** executada pelo processo pai original; após `fork`, existem pai e filho.
[368] categoria: Observação | termos: tecnicamente; NULL) está incorreto | trecho: Observação: tecnicamente, `execvp("ls", NULL)` está incorreto; o segundo argumento deveria ser um vetor de argumentos, por exemplo:
[369] categoria: Linha 9 | termos: normalmente apenas o pai executa; porque o filho é substituído pelo programa true | trecho: - **Linha 9:** normalmente apenas o pai executa, porque o filho é substituído pelo programa `true`.
[370] categoria: Solução | termos: usar aging | trecho: Solução: usar **aging**, aumentando gradualmente a prioridade de processos que esperam muito.
[371] categoria: Quantum = 10, quando aplicável. Ordem de chegada | termos: P1; P2; P3 | trecho: Quantum = 10, quando aplicável. Ordem de chegada: P1, P2, P3.
[372] categoria: Tempo médio de espera | termos: 67 unidades; 33 unidades | trecho: **Tempo médio de espera: 48,67 unidades**
[373] categoria: Exercícios preparatórios para P2 | termos: setor de índice: 9; setor de dados: 20, 22, 10 e 5 | trecho: ## Exercícios preparatórios para P2. - setor de índice: 9
[374] categoria: setor de dados | termos: 10 e 5 | trecho: - setor de dados: 20, 22, 10 e 5
[375] categoria: TANENBAUM, A. D. Sistemas operacionais modernos. 3. ed. São Paulo | termos: Pearson Prentice Hall; 2010 (adaptado) | trecho: TANENBAUM, A. D. Sistemas operacionais modernos. 3. ed. São Paulo: Pearson Prentice Hall, 2010 (adaptado).
