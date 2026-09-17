# Declaracao do professor — FR

Para cada CATEGORIA que voce usou nos materiais, escreva o codigo do topico do plano a que os termos listados pertencem, ou SEM. Nao corrija arquivos individuais. Tempo sugerido: ate 30 minutos.

## Topicos do plano
- `1.1` Conceitos de redes de computadores e Internet
- `1.2` Modelos OSI e TCP/IP
- `1.3` Conceito de protocolo de redes pessoais, locais, metropolitanas e de longa distância
- `2.1` Funções e características do nível de aplicação
- `2.2` Paradigmas cliente/servidor e P2P
- `2.3` Protocolos de aplicação para infraestrutura (DNS, DHCP, SNMP, NAT)
- `2.4` Protocolos de aplicação para o usuário (HTTP, HTTPS, SMTP, POP3, IMAP)
- `3.1` Funções e características do nível de transporte
- `3.2` Protocolo TCP
- `3.21` Controle de congestionamento TCP
- `3.3` Protocolo UDP
- `4.1` Tipos de serviços
- `4.2` Protocolo IPv4
- `4.3` Protocolo IPv6
- `4.4` Protocolo ICMPv6
- `4.5` Roteamento estático e dinâmico
- `5.1` Funções e características do nível de enlace
- `5.2` Protocolos de enlace para redes locais cabeadas (Ethernet)
- `5.3` Protocolos de enlace para redes locais sem fio (IEEE 802.11 e Bluetooth)
- `6.1` Classificação e topologias de redes de computadores
- `6.2` Fundamentos de comunicação de dados
- `6.3` Equipamentos de interconexão

## Categorias

| id | categoria | termos listados sob ela | codigo do topico ou SEM |
|---|---|---|---|
| 1 | 📖 Apoio | Neutralidade da Rede; Governança da Internet → content/BIBLIOG |  |
| 2 | Unidade 01 — Introdução a redes de computadores | [ ] 1.2 Modelos OSI e TCP/IP |  |
| 3 | Unidade 02 — Nível de aplicação | [ ] 2.2 Paradigmas cliente/servidor e P2; [ ] 2.2.1 Implementação de sockets |  |
| 4 | [ ] 2.3 Protocolos de aplicação para infraestrutura | DNS; DHCP; SNMP; NAT |  |
| 5 | [ ] 2.4 Protocolos de aplicação para o usuário | HTTP; HTTPS; SMTP; POP3 |  |
| 6 | Unidade 03 — Nível de transporte | [ ] 3.2 Protocolo TCP; [ ] 3.21 Controle de congestionamento TC; [ ] 3.3 Protocolo UDP |  |
| 7 | Unidade 04 — Nível de rede | [ ] 4.1 Tipos de serviços; [ ] 4.2 Protocolo IPv4; [ ] 4.2.1 Funções; [ ] 4.2.2 Endereçamento |  |
| 8 | Unidade 06 — Nível físico | [ ] 6.2 Fundamentos de comunicação de da; [ ] 6.2.1 Cálculo da capacidade do canal; [ ] 6.2.2 Hierarquias digitais; [ ] 6.3 Equipamentos de interconexão |  |
| 9 | Protocolos de Comunicação | Para um protocolo funcionar é necessário |  |
| 10 | • O projeto de redes de comunicação é organizado em camadas | Cada camada suporta diferentes protocolo; Pilha de protocolos ( protocol stack ); Interface bem definida entre as camadas |  |
| 11 | Hierarquias de protocolos | Entre camadas existem interfaces; Diferentes sistemas operacionais possuem; Linux vs Windows vs macOS; Windows 98 x Windows 8 |  |
| 12 | • Redes | Estabelecer uma conexão |  |
| 13 | Serviços orientados a conexão | Essencialmente funciona como um tubo; o Normalmente a ordem de chegada é prese; Tamanho máximo de mensagem; Qualidade de serviço (QoS) |  |
| 14 | Problema | Cada fabricante desenvolvia sua arquitet; Demorado e inviável em redes grandes; Alterações na rede exigem reconfiguração; Solução com DHCP: |  |
| 15 | ● Solução: utilização de modelos de referências | Estudaremos dois modelos de referência:; OSI; TCP/IP |  |
| 16 | Modelo OSI | Proposta pelo ISO (International Standar; Possui 7 camadas |  |
| 17 | OSI - Camada Física | Trata da transmissão de bits brutos por ; meio físico |  |
| 18 | OSI - Camada de Redes | Determinadas a cada nova conexão; Dinâmicas, sendo determinadas para cada ; Responsável pelo controle de congestiona |  |
| 19 | OSI - Camada de Transporte | Repassa os fragmentos a camada de redes; erros que entrega mensagens ou bytes ord |  |
| 20 | OSI - Camada de Sessão | Sessões oferecem serviços |  |
| 21 | OSI - Camada de Apresentação | Responsável pela sintaxe e semântica das |  |
| 22 | ● Protocolo utilizados para o desenvolvimento de aplicações | o SMTP (Simple Mail Transfer Protocol) |  |
| 23 | TCP/IP | Necessidade de conectar redes heterogeni; o Transmissão de voz |  |
| 24 | TCP/IP - Camada Inter-redes | Esta camada é análoga ao sistema de corr |  |
| 25 | ● Define um formato de pacote oficial e um protocolo chamado IP (Inter | Importante função de roteamento; Diferença: faz a fragmentação de pacotes |  |
| 26 | TCP/IP - Camada de Transporte | o UDP (User Datagram Protocol) |  |
| 27 | TCP/IP - Camada de Aplicação | Protocolos de interesse do usuário |  |
| 28 | Problemas com o modelo TCP/IP | Ex: Bluetooth |  |
| 29 | Modelo de referência híbrido | Modelo de referência híbrido: |  |
| 30 | • Em quais camadas cada equipamento opera? | Hub; Brigde; Switch; Roteador |  |
| 31 | • Classificação em duas dimensões: | Tecnologias de transmissão; Área de operação (escala) |  |
| 32 | Tipos de Rede | Classificação por tecnologias de transmi; Redes de difusão (broadcast); Redes ponto a ponto; Redes Pessoais (PAN) |  |
| 33 | Redes de difusão | Cada mensagem é recebida por todos os pa; Formas de endereçamento:; Unicast; Broadcast |  |
| 34 | Redes ponto a ponto | Conexões entre pares; Necessidade de determinar a melhor rota |  |
| 35 | Difusão x ponto a ponto | Redes menores e próximas tendem a usar d |  |
| 36 | Redes Pessoais (PAN) | Personal Area Network (PAN); Dispositivos comunicantes próximos do in |  |
| 37 | Redes Locais (LAN) | Local Area Network (LAN); Redes privadas – tamanho restrito; Pertence a um único domínio administrati; Tempo de atraso conhecido |  |
| 38 | Redes Metropolitanas (MAN) | Metropolitan area network (MAN); Versão ampliada das LANs; Abrange uma área maior (ex: cidade); Sistema de TV a cabo |  |
| 39 | Redes Geograficamente Distribuídas (WAN) | Abrangência desde um país até distâncias; Maiores taxas de erros; Tempo de atraso de pacotes variável |  |
| 40 | ● Interconexão de sistemas (WPAN) o Bluetooth | Rede Celular - WiMAX, LTE |  |
| 41 | Histórico (anos 60) | ARPANET (1a. Versão em 1969); 4 nós: UCLA, UCSB, SRI, UTAH; Software de comunicação: NCP (Network Co |  |
| 42 | 4 nós | UCLA; UCSB; SRI; UTAH |  |
| 43 | Histórico (anos 70) | Internetting Project – Vint Cerf e Bob K |  |
| 44 | Internet hoje | Formas de acesso à Internet; Rede telefônica: serviço de dial-up ou D; Rede cabeada usada para transmissão de T; Conexão direta com um backbone ou ISP |  |
| 45 | Exemplos | Web (HTTP); e-mail (SMTP); transferência de arquivos (FTP); DNS |  |
| 46 | Conceitos Básicos | Processo : programa em execução em um ho |  |
| 47 | Arquiteturas de Aplicação | Cliente-servidor : |  |
| 48 | Arquitetura Cliente-Servidor | O cliente inicia a comunicação com o ser; Comunicação é centralizada: servidor for |  |
| 49 | Exemplo | HTTP; SMTP; DNS |  |
| 50 | Cada processo é endereçado por um par | IP; porta |  |
| 51 | |Telefonia IP|SIP, RTP|UDP ou TCP|SIP | RTP: dinâmico| |  |
| 52 | Web e o HTTP | HTTP; HyperText Transfer Protocol; Protocolo de aplicação da Web; Arquitetura cliente-servidor |  |
| 53 | Cliente | browser que solicita; recebe e apresenta os objetos na Web |  |
| 54 | Um objeto é um arquivo qualquer | HTML; JPEG; GIF; CSS |  |
| 55 | Versões do HTTP | o Compactação de cabeçalhos e priorizaçã |  |
| 56 | Protocolo HTTP | Orientado a requisição e resposta: |  |
| 57 | Também é possível usar portas alternativas | ex: 8080 |  |
| 58 | Requisição HTTP | Formato da requisição; Cabeçalho em modo texto (formato ASCII); Principais métodos de HTTP:; POST – Envia dados para criar um novo re |  |
| 59 | Resposta HTTP | 302 Found – Redirecionamento temporário ; 401 Unauthorized – Requer autenticação p; 500 Internal Server Error – Erro genéric; Principais campos de cabeçalhos de uma r |  |
| 60 | 1xx – Informacional | 100 Continue; 101 Switching Protocols; 102 Processing; • 103 Early Hints |  |
| 61 | 3xx – Redirecionamento | 300 Multiple Choices; • 301 Moved Permanently; 302 Found; 303 See Other |  |
| 62 | 418 I'm a teapot | Easter egg; april's fool 1998 |  |
| 63 | 4xx – Erro do cliente | 400 Bad Request; 401 Unauthorized; 402 Payment Required (reservado); 403 Forbidden |  |
| 64 | 5xx – Erro do servidor | 500 Internal Server Error; 501 Not Implemented; 502 Bad Gateway; 503 Service Unavailable |  |
| 65 | Date | 12 Aug 2025 20:15:19 GMT ) |  |
| 66 | Connection | close ) |  |
| 67 | Last-Modified | 11 Aug 2025 18:00:00 GMT ) |  |
| 68 | Persistência de Conexões | Apenas um troca de mensagens por conexão; Connection: close; Conexões persistentes (HTTP keep-alive); Reuso de conexões, várias trocas de mens |  |
| 69 | Cookies | Existe desde 1997 (RFC 2109); Armazenar informações entre requisições; 4 componentes; Linha de cabeçalho na msg HTTP de respos |  |
| 70 | Manter sessões ativas | login; carrinho de compras; “1-click purchase” |  |
| 71 | Banners de rede de anúncios - remarketing | ex.: Google Ads; Meta Ads |  |
| 72 | Cache na Web | Reduz latência e tráfego de rede |  |
| 73 | • ISPs | universidades; empresas; provedores |  |
| 74 | • ISPs: universidades, empresas, provedores | Reduz o tempo de resposta das requisiçõe; Diminuição do trafego no enlace até o se; Desnecessário aumentar largura de banda ; Mais barato cache do que Banda |  |
| 75 | Consequências | Frequentemente é um upgrade caro |  |
| 76 | Caches Web (servidor proxy) | Campos enviados na resposta (servidor → ; Campos enviados na requisição (cliente → |  |
| 77 | Cache-Control | no-cache; public; private ) |  |
| 78 | Age | tempo; em segundos |  |
| 79 | • Arquivo desatualizado no Cache? | Get condicional:; Comando GET; Linha de cabeçalho If-Modified-Since: |  |
| 80 | HTTP/1.1   200   OK Date | Mon |  |
| 81 | GET /fruit/kiwi.gif HTTP/1.1 Host | www.exotiquecuisine.com If-modified-sinc; 30 Oct 2014 19:04:24 |  |
| 82 | HTTP/1.1   304   Not Modified Date | Mon |  |
| 83 | HTTP/2.0 | Multiplexação de mensagens em uma única ; Faz compressão de dados e cabeçalhos HTT; Multiplexa várias solicitações em uma ún |  |
| 84 | HTTP/3 | Versão mais atual do HTTP; Encapsulado sobre UDP, em vez de TCP; Melhora a velocidade de carregamento dos; Reduz latência e melhora desempenho em r |  |
| 85 | HTTPS | Hyper Text Transfer Protocol Secure; SSL (Secure Socket Layer); TLS (Transport Layer Security); HTTPS é o padrão da Web |  |
| 86 | REST APIs | Transferência de Estado Representacional; É um estilo arquitetural de software; Popularização da computação em nuvem; Software-as-a-Service (SaaS) |  |
| 87 | • Máquinas são endereçadas por endereços IP | Utilização de nomes para hosts ( hostnam; google.com; gaia.cs.umass.edu; www.pucrs.br |  |
| 88 | Tradução de nomes | Inicialmente; Problema:; Dificuldade em manter atualizado; Solução: DNS (Domain Name Service) |  |
| 89 | DNS | Serviço de diretório da Internet (Domain; Composto de:; Banco de Dados Distribuído implementado  |  |
| 90 | Exemplos de usuários | HTTP; IMAP; FTP |  |
| 91 | Distribuição de Carga | Mesmo nome para vários endereços IP (hos; Utilizado em servidores distribuídos; Cada servidor tem um IP distinto; Sob consulta, encontra os vários endereç |  |
| 92 | Protocolo DNS | RFC 1034 e RFC 1035; DNS é uma caixa preta para demais aplica; Completamente distribuído; Volume de tráfego (superlotação do enlac |  |
| 93 | • root servers Servidores de nomes raiz ( ) | 13 ao total (A a M) |  |
| 94 | Servidores Autoritativos | Servidores de nomes com autoridade; Terceiro nível na hierarquia IP; Endereços acessíveis publicamente; Implementar seu próprio DNS (ex: BIND) |  |
| 95 | Pagar para manter os registros de IPs em um servidor DNS | ex: Amazon AWS; Cloudflare; Google |  |
| 96 | Servidor Local | Servidor DNS Local; Cada ISP (ISP residencial, companhia, un; Também chamado de “servidor de nomes def |  |
| 97 | • Armazenamento temporário de respostas DNS já resolvidas | Reduz consultas externas repetidas aos s; Reduz latência e melhora o tempo de resp; Diminui carga e tráfego na rede |  |
| 98 | • Domínio: | pucrs.br (domínio da PUCRS) |  |
| 99 | Pode ter subdomínios | mail.google.com; aluno.pucrs.br |  |
| 100 | Geralmente é um FQDN | ex.: sparta.pucrs.br; mail.google.com |  |
| 101 | Nome Totalmente Qualificado | .com → domínio de topo (TLD) |  |
| 102 | FQDN | domínios intermediários e o domínio raiz |  |
| 103 | Tipos de Registros | (foo.com, relay1.bar.foo.com, CNAME); (foo.com, mail.bar.foo.com, MX) |  |
| 104 | Mensagem DNS | Baseada no formato definido pela RFC 103; Uma mensagem pe organizada em quatro seç; Answer: RRs que respondem diretamente à  |  |
| 105 | Contém um cabeçalho com informações de controle | ID; flags; contagem de RRs |  |
| 106 | Registro de Domínio | Como registrar um de domínio no DNS:; Empresa nova chamada Network Utopia; ICANN (Internet Corporation for Assigned; 967 entidades registradoras |  |
| 107 | Configuração na entidade registradora | dns1.networkutopia.com; dns2.networkutopia.com; A) |  |
| 108 | DDoS em TLDs | .org); mais difícil de filtrar; mas reduzido pelo cache |  |
| 109 | Reflexão e Amplificação | uso do DNS para sobrecarregar um alvo; explorando respostas maiores que as cons |  |
| 110 | • dig | dig +trace google.com |  |
| 111 | Cada dispositivo precisa ser configurado manualmente | como IP; máscara; gateway; DNS |  |
| 112 | • Objetivo: atribuir automaticamente configurações de rede a dispositi | RFC: 2131 (1997); Portas: UDP 67 (servidor) e UDP 68 (clie |  |
| 113 | Vantagem | elimina configuração manual; facilita mobilidade e administração da r; simples; rápido e consome pouco espaço no servido |  |
| 114 | Funcionamento do DHCP | (domínio de broadcast) ou acessíveis via; distribuição; vencimento (T1/T2) |  |
| 115 | Cada endereço concedido tem um lease time | validade temporária; vida útil |  |
| 116 | Opções de configuração via DHCP | Principais parâmetros (opções) de config; Também é possível criar opções customiza |  |
| 117 | Obtenção de nova configuração | Cliente envia DISCOVERY em broadcast; Todos servidores respondem com OFFER |  |
| 118 | Renovação de configuração | Processo de renovação automática: |  |
| 119 | Exemplo prático | Liberar o endereço de IP em uso (RELEASE |  |
| 120 | o dhclient -r | Obter um novo endereço IP (DORA): |  |
| 121 | DHCP RELEASE: | Libera a configuração atual; • Cliente envia para o servidor |  |
| 122 | DHCP DISCOVERY: | Procura por um servidor disponível; • Cliente envia por broadcast |  |
| 123 | DHCP REQUEST: | Cliente solicita a configuração oferecid; • Cliente envia por broadcast |  |
| 124 | DHCP Relay | que |  |
| 125 | Vulnerabilidades do DHCP | Rogue DHCP Server:; Declines forjados: endereços marcados co |  |
| 126 | Servidor falso oferece parâmetros maliciosos | ex.: gateway errado; DNS malicioso |  |
| 127 | o Tráfego pode ser interceptado ou redirecionado | phishing; MITM; vazamento de dados |  |
| 128 | Inundação de requisições | servidor sobrecarregado; atraso ou falha nas respostas |  |
| 129 | Primeiro e-mail enviado na história | Enviado via ARPANET, percursora da Inter; Mainframe DEC PDP-10:; Processador KA10 a ~1 MHz; RAM de 512 KB |  |
| 130 | Sistema operacional TENEX | com suporte a time-sharing; acesso via terminais |  |
| 131 | Sistemas de E-mail Atuais | do destinatário; A mensagem é enviada a caixa postal; Baseiam-se nos seguintes protocolos:; SMTP – Simple Mail Transfer Protocol (RF |  |
| 132 | SMTP – Simple Mail Transfer Protocol | RFC 821; Funciona sobre TCP :; Formato do endereço: |  |
| 133 | o POP – Post Office Protocol | RFC 918 |  |
| 134 | o IMAP – Internet Message Access Protocol | RFC 3501 |  |
| 135 | Agentes de Usuário | Apple Mail; Gmail) |  |
| 136 | Servidores de Correio | Infraestrutura que armazena |  |
| 137 | Formato das Mensagens | Mensagem de e-mail (RFC 5322): |  |
| 138 | From | confirmo nossa reunião de amanhã. Alice |  |
| 139 | EHLO – Versão estendida do HELO | suporta recursos extras como AUTH; STARTTLS |  |
| 140 | Comandos SMTP | MAIL FROM: – Informa o endereço do remet; RCPT TO: – Informa o endereço do destina; DATA – Inicia a transmissão da mensagem ; VRFY – Verifica se uma conta existe no s |  |
| 141 | NOOP – Comando “no operation” | servidor responde OK; usado para teste |  |
| 142 | 2xx – Sucesso | 220 – Serviço pronto; 221 – Fechando conexão; 250 – Comando aceito com sucesso |  |
| 143 | 4xx – Erro temporário | 421 – Serviço indisponível, fechando con; 450 – Caixa postal indisponível; 451 – Erro de processamento |  |
| 144 | 5xx – Erro permanente | 500 – Sintaxe inválida; 501 – Parâmetro inválido; 552 – Caixa postal cheia / tamanho exced; 553 – Endereço de remetente inválido |  |
| 145 | C | confirmo nossa reunião de amanhã. C: Ali |  |
| 146 | Hoje, usa-se arquitetura cliente-servidor | PC; laptop; smartphone |  |
| 147 | Recuperação de e-mails | (webmail) |  |
| 148 | POP – Post Office Protocol | Versão atual: POP3 ( RFC 1939 , 1996); Funcionamento básico:; Cliente autentica no servidor |  |
| 149 | o Download-and-delete | Menor uso de espaço no servidor |  |
| 150 | o Download-and-keep | Maior uso de espaço no servidor |  |
| 151 | POP3 – Comandos e Respostas | Autenticação |  |
| 152 | IMAP – Internet Message Access Protocol | Versão atual: IMAP4rev1 ( RFC 3501 , 200; Funcionamento:; Mensagens permanecem no servidor; Cliente acessa e manipula pastas e mensa |  |
| 153 | Flags de estado | lida; respondida; excluída |  |
| 154 | Busca de mensagens por critérios | assunto; remetente; data |  |
| 155 | Comparação entre IMAP e POP3 | POP3; Acesso no mesmo local; o Offline |  |
| 156 | E-mail pela Web (Webmail) | O navegador Web atua como agente de usuá |  |
| 157 | Comunicação entre Processos | Dentro do mesmo host:; Em diferentes hosts:; ▫Ex: sockets; ▫número de porta |  |
| 158 | Socket | Essa interface é chamada de Socket |  |
| 159 | Socket TCP | Implementa um canal confiável; Serviço de conexão:; o Garante ordem de entrega; Stream |  |
| 160 | GET /cs453/index.html HTTP/1.1 <cr><lf> Host | Windows NT 5.1; en-US; application/xml; application/xhtml+xml |  |
| 161 | FOROUZAN, B. A.; MOSHARRAF, F. Redes de computadores | uma abordagem top-down. McGraw-Hill: Boo; 2013 (recurso online) |  |
| 162 | KUROSE, J. F.; ROSS, K. W.; ZUCCHI, W. L. Redes de Computadores e a In | uma abordagem top-down. 6ª ed. Pearson; 2013 (recurso online) |  |
| 163 | TANENBAUM, A. Redes de Computadores. 5ª ed. São Paulo | Pearson; 2011 (recurso online) |  |
| 164 | FOROUZAN, B.; FEGAN, S. Protocolo TCP/IP. 3ª ed. Porto Alegre | Bookman; 2010 (recurso online) |  |
| 165 | PETERSON, L. L.; DAVIE, B. S. Computer networks | a systems approach. Elsevier; 2012. 5. GORALSKI; 2ª ed. 2017 |  |
| 166 | Parte 1 — Requisições e Respostas HTTP | (Fonte: P1 — 2024/2) |  |
