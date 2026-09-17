# Brief para segunda opinião (Codex astra, read-only) — FR sem gold: motor puro, Datalab, LLM (2026-09-12)

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`.

## 1. A pergunta do usuário e o desenho

"Fazer FR sem gold, para ver a precisão do motor puro", depois "uma comparação entre 3 runs: totalmente crua, só Datalab, e
Datalab + LLM". FR = Fundamentos de Redes: 22 materiais no produto (20 no stash do Moodle: os 2 links de "Sugestão de Conteúdo
Online" não estão no stash), Moodle com seções explícitas "U1 - Redes de Computadores" (5) e "U2 - Camada de Aplicação" (14),
mais "Plano de Ensino" (1) e "Sugestão de Conteúdo Online" (2). Sem gold de unidade nem de bloco; gold de subunidade com 18
pontuáveis (`docs/reports/subunit_gt_FR.csv`), que só mede.

Cada run reconstrói o tutor DO ZERO a partir do stash pelo caminho da UI (`c1-3/rebuild_fr.py`, 06/09, refeito hoje):
perfil real do FR, zero curadoria, sem vocab compilado, voter desligado, tripwires que contam qualquer chamada. Réguas sem
gold de unidade: (a) unidade = a seção explícita do professor (U1/U2; 19 materiais); (b) subunidade = o gold de 18; (c) a fila
(`revisar`) como detector. `c1-3/mede_fr_sem_gold.py` mede um sandbox contra as duas e contra o produto.

- **Run 1, crua** (`rebuild_fr.py --fresh`, 807 s, 0 chamadas, 0 tentativas): pymupdf4llm nos 15 PDFs.
- **Run 2, só Datalab** (`fr_puro_datalab.py`, 0 chamadas): cópia da run 1 com o markdown do Datalab que o produto JÁ tinha nos
  15 PDFs (`advanced_markdown`, arquivos ~2× maiores) apontado como `base_markdown`, reprocessada sem voter e sem vocab.
- **Run 3, Datalab + LLM** (`fr_puro_datalab.py --llm-vivo`, 84 s): run 2 + vocab LLM do cache do produto
  (`.glossary_curation.llm.json`, compilado em 11/09, 1 chamada por unidade) + voter VOTANDO ao vivo: 10 chamadas Gemini, 11 votos gravados.
- Intermediários: run 1 + vocab (sem voter) e run 2 + vocab (sem voter); run 3 com o cache de votos do produto em vez de votar.

## 2. Resultado (MEDIDO)

| run | texto pontuado | LLM | unidade (seção U1/U2, 19) | subunidade (gold 18) | erros confiantes | fila | bloco = produto |
|---|---|---|---|---|---|---|---|
| 1 crua | pymupdf4llm | nenhum | 19/19, confiante 9/9 | **7/18**, confiante 4/9 | 5 | 10/20 | 15/20 |
| 2 só Datalab | Datalab | nenhum | 19/19, confiante 10/10 | **8/18**, confiante 5/10 | 5 | 9/20 | 15/20 |
| 1 + vocab, sem voter | pymupdf4llm | vocab (cache) | 19/19, confiante 8/8 | 18/18, confiante 8/8 | 0 | 11/20 | 10/20 |
| 2 + vocab, sem voter | Datalab | vocab (cache) | 19/19, confiante 8/8 | 18/18, confiante 8/8 | 0 | 10/20 | 10/20 |
| 3 com cache de votos | Datalab | vocab + cache de votos | 19/19, 8/8 | 18/18, 8/8 | 0 | 11/20 | 10/20 |
| **3 Datalab + LLM (viva)** | Datalab | vocab + **voter ao vivo, 10 chamadas** | 19/19, confiante 18/18 | **18/18**, confiante 17/17 | 0 | 1/20 | 19/20 |
| produto | pymupdf4llm | vocab + 13 votos | 19/19, 18/18 | 18/18, 17/17 | 0 | 1/22 | — |

"bloco = produto" = concordância do bloco temporal com o produto (não há gold de bloco no FR). "fila" = materiais com
`revisar != ok`; nas runs 1 e 2 a fila tem 0 erros de unidade dentro (só alarme falso) e pega 6 e 5 dos 11 e 10 erros de
subunidade.

## 3. Por material, run 1 (crua) e run 3 (viva) — MEDIDO
```
sandbox Fundamentos-de-Redes-Tutor: 20 materiais · produto 22 · em comum 20
material                                 secao  unid sb  unid prod sub sb                     sub prod                   gold sub               revisar sb
plano-de-ensino-20262                    -      1        1         (vazio)                    (vazio)                    -                      ok
01-protocolos-de-rede                    U1     1        1         modelos-osi-e-tcpip        conceito-de-protocolo-de-r conceito-de-protocolo- ok
02-modelos-de-referencia                 U1     1        1         modelos-osi-e-tcpip        modelos-osi-e-tcpip        modelos-osi-e-tcpip    ok
02-poster-network-protocols              U1     1        1         (vazio)                    (vazio)                    -                      duvida
03-tipos-de-redes                        U1     1        1         conceito-de-protocolo-de-r conceito-de-protocolo-de-r classificacao-e-topolo ok
unidade1-exercicios                      U1     1        1         (vazio)                    modelos-osi-e-tcpip        conceito-de-protocolo- duvida
04-camada-de-aplicacao                   U2     2        2         protocolos-de-aplicacao-pa paradigmas-clienteservidor funcoes-e-caracteristi ok
04-protocolo-http                        U2     2        2         paradigmas-clienteservidor protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
05-protocolo-dns                         U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
06-protocolo-dhcp                        U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
07-protocolos-de-e-mail                  U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
08-desenvolvimento-de-aplicacoes         U2     2        2         (vazio)                    implementacao-de-sockets   implementacao-de-socke duvida
lista-de-exercicios-1-camada-de-aplicaca U2     2        2         paradigmas-clienteservidor protocolos-de-aplicacao-pa funcoes-e-caracteristi duvida
tcp-chat-c                               U2     2        2         paradigmas-clienteservidor implementacao-de-sockets   implementacao-de-socke duvida
tcp-example                              U2     2        2         paradigmas-clienteservidor implementacao-de-sockets   implementacao-de-socke duvida
udp-example-c                            U2     2        2         paradigmas-clienteservidor implementacao-de-sockets   implementacao-de-socke duvida
udp-example-java                         U2     2        2         paradigmas-clienteservidor implementacao-de-sockets   implementacao-de-socke duvida
unidade2-exercicios-dhcp                 U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca duvida
unidade2-exercicios-dns                  U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca duvida
unidade2-exercicios-http                 U2     2        2         paradigmas-clienteservidor protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
== unidade contra a secao do professor (U1/U2), sem gold
  sandbox (motor puro, 0 chamadas)             acerto 19/19 · precisao do confiante 9/9 · erros confiantes 0 · fila 10 (pega 0 erros)
  produto (vocab LLM + votos em cache)         acerto 19/19 · precisao do confiante 18/18 · erros confiantes 0 · fila 1 (pega 0 erros)
== subunidade contra subunit_gt_FR (18)
  sandbox (motor puro, 0 chamadas)             acerto 7/18 · precisao do confiante 4/9 · erros confiantes 5 · fila 9 (pega 6 erros)
  produto (vocab LLM + votos em cache)         acerto 18/18 · precisao do confiante 17/17 · erros confiantes 0 · fila 1 (pega 0 erros)
```
```
sandbox Fundamentos-de-Redes-Tutor: 20 materiais · produto 22 · em comum 20
material                                 secao  unid sb  unid prod sub sb                     sub prod                   gold sub               revisar sb
plano-de-ensino-20262                    -      1        1         (vazio)                    (vazio)                    -                      ok
01-protocolos-de-rede                    U1     1        1         conceito-de-protocolo-de-r conceito-de-protocolo-de-r conceito-de-protocolo- ok
02-modelos-de-referencia                 U1     1        1         modelos-osi-e-tcpip        modelos-osi-e-tcpip        modelos-osi-e-tcpip    ok
02-poster-network-protocols              U1     1        1         (vazio)                    (vazio)                    -                      ok
03-tipos-de-redes                        U1     1        1         conceito-de-protocolo-de-r conceito-de-protocolo-de-r classificacao-e-topolo ok
unidade1-exercicios                      U1     1        1         modelos-osi-e-tcpip        modelos-osi-e-tcpip        conceito-de-protocolo- ok
04-camada-de-aplicacao                   U2     2        2         funcoes-e-caracteristicas- paradigmas-clienteservidor funcoes-e-caracteristi duvida
04-protocolo-http                        U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
05-protocolo-dns                         U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
06-protocolo-dhcp                        U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
07-protocolos-de-e-mail                  U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
08-desenvolvimento-de-aplicacoes         U2     2        2         implementacao-de-sockets   implementacao-de-sockets   implementacao-de-socke ok
lista-de-exercicios-1-camada-de-aplicaca U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa funcoes-e-caracteristi ok
tcp-chat-c                               U2     2        2         implementacao-de-sockets   implementacao-de-sockets   implementacao-de-socke ok
tcp-example                              U2     2        2         implementacao-de-sockets   implementacao-de-sockets   implementacao-de-socke ok
udp-example-c                            U2     2        2         implementacao-de-sockets   implementacao-de-sockets   implementacao-de-socke ok
udp-example-java                         U2     2        2         implementacao-de-sockets   implementacao-de-sockets   implementacao-de-socke ok
unidade2-exercicios-dhcp                 U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
unidade2-exercicios-dns                  U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
unidade2-exercicios-http                 U2     2        2         protocolos-de-aplicacao-pa protocolos-de-aplicacao-pa protocolos-de-aplicaca ok
== unidade contra a secao do professor (U1/U2), sem gold
  sandbox (motor puro, 0 chamadas)             acerto 19/19 · precisao do confiante 18/18 · erros confiantes 0 · fila 1 (pega 0 erros)
  produto (vocab LLM + votos em cache)         acerto 19/19 · precisao do confiante 18/18 · erros confiantes 0 · fila 1 (pega 0 erros)
== subunidade contra subunit_gt_FR (18)
  sandbox (motor puro, 0 chamadas)             acerto 18/18 · precisao do confiante 17/17 · erros confiantes 0 · fila 1 (pega 0 erros)
  produto (vocab LLM + votos em cache)         acerto 18/18 · precisao do confiante 17/17 · erros confiantes 0 · fila 1 (pega 0 erros)
```

## 4. Achados de caminho (MEDIDO)

a. **O motor pontua `base_markdown`; `advanced_markdown` é a última opção** (`src/builder/artifacts/navigation.py::_entry_markdown_path_for_file_map`:
   approved > curated > base > advanced). O FR do produto tem Datalab nos 15 PDFs (`advanced_backend: datalab`, `advanced_markdown`
   presente 15/15) e o motor nunca leu esse texto. Uma run com Datalab ao vivo (`rebuild_fr_c2.py`, `preferred_backend=datalab`) foi
   parada em 2/20 porque o engine escolhe base = pymupdf4llm e advanced = datalab (`engine.py:1650-1656`), e o scorer leria a base.
   A run 2 contornou apontando `base_markdown` para o .md do Datalab existente.
b. **O vocab compilado mexe no bloco**: com vocab e sem voter, bloco = produto cai de 15/20 para 10/20 (aliases do vocab entram no
   casamento tópico × bloco); o voter recompõe (19/20). Ou seja, vocab sem voter piora o bloco e melhora a subunidade.
c. **O cache de votos do produto não serve a um tutor do zero**: `material_curation.json` (13 votos) tem chave por conteúdo (11 dos
   20 materiais batem), mas o voto só é reaproveitado se a JANELA de blocos for a mesma (`llm_vote.py:359-400`); blocos novos têm
   outros uuids → todos miss → sem cliente, o voter cala. Daí a linha "3 com cache" = "só vocab".
d. Sandbox fora do `subjects.json`: sem perfil, o plano parseia 0 unidades e o guard "unidade nunca encolhe" aborta o reprocess;
   os scripts forçam o perfil do FR (`store.find_by_repo_root`), como o `rebuild_fr.py` passa `subject_profile` ao builder.

Contexto de 06/09 (Placar): "FR do zero, run A: unidade 19/19 pela seção do professor, 11 avisos; run B (Gemini ~22 chamadas)
19/19, 6 avisos; os 19 acordos de unidade são circulares: o motor decidiu lendo a mesma seção".

## 5. Perguntas, em ordem

1. **A leitura se sustenta?** "Extração vale +1; vocabulário vale +11 e zera os erros confiantes; voter vale a fila (10 → 1) e o
   bloco (10 → 19); unidade não depende de nada." Onde ela extrapola o que 20 materiais de um curso com seções "U<n>" permitem?
2. **Unidade 19/19 sem gold é medida ou tautologia?** O motor lê a seção "U2 - …" e a régua é a mesma seção. O que sobra de
   evidência independente (o produto concorda 20/20; bloco temporal; o plano)? O que um curso sem "U<n>" nas seções (CG, SO) faria?
3. **Achado b, vocab piora o bloco sem voter.** Defeito a corrigir (o vocab não devia entrar no casamento de bloco) ou desenho
   aceitável porque o voter existe? Como medir nos 8 tutores (bloco gold nos 5 + CG) a 0 chamadas?
4. **Achado a, base × advanced.** Para o item 4 da C5 (insumo html/vídeo 62%/57%): o scorer deveria preferir o advanced quando
   existe? No FR a diferença é +1 na subunidade. Que medição a 0 chamadas decide isso nos 8 (o produto tem `advanced_markdown`
   em 163 materiais)?
5. **Achado c, cache de votos.** Chave por conteúdo + janela: correto por desenho ou defeito para o cenário "tutor novo do mesmo
   curso"? Vale mudar a chave, ou o voto de um tutor não deve mesmo migrar?
6. **Risco.** 20 × 22 materiais; sandbox com perfil forçado; o gold de subunidade do FR nasceu com o produto (vocab LLM); a run 3
   viva votou 10 e o produto tem 13; o que mais pode estar errado nas tabelas?
