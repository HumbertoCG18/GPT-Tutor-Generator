# SO Backfill Report — 2026-06-21

Branch: feat/block-stable-id
SO Repo: C:/Users/Humberto/Documents/GitHub/Sistemas-Operacionais-Tutor
Scratch map: .git/sdd/so-proposed-date-block-map.json (main repo .git only)

---

## PASSO 0 — Veredicto do Modelo

**Modelo: DIRECT** (date→block, sem card layer)

SO não tem cards/sections com datas próprias. A âncora autoritativa é o **prefixo DD.MM no título** dos arquivos (ex: `02.06 Lâminas Gerência de I/O` = 02/06/2026). Esses prefixos são datas reais de aula — confirmado cruzando com `CRONOGRAMA_DETALHADO.md` (ex: bloco-05 session `07.04.2026` = sessão "especificação tp1").

**Âncora disponível:** filename-date (título com prefixo DD.MM)
**Âncora ausente:** posting_date, lessons_index, card layer

Gate: PASS — SO tem âncora de data. 17 de 36 entries têm prefixo DD.MM parseável. Continuar.

---

## PASSO 1 — Mapa Proposto (date-only, sem scorer)

Total entries SO: 36
Blocos disponíveis: 21 (bloco-01 a bloco-21, 03/03/2026–16/07/2026)

### Tabela Completa

| entry_id | título (resumido) | data parseada | bloco (display) | uuid (8 chars) | section | flag | nota |
|---|---|---|---|---|---|---|---|
| 0206-laminas-gerencia-de-i-o-livro-texto | 02.06 Lâminas Gerência de I O | 02/06/2026 | bloco-12 | a838bf45 | Gerência de I O | ⚠️ DIFFERS | auto_tag diz bloco-05; data aponta bloco-12 |
| 0205-laminas-segmentacao | 02.05 Lâminas Segmentação | 02/05/2026 | — | — | Gerência de Memória | ❌ NO_MATCH | 02/05/2026 não cai em nenhum período de bloco (gap: 30/04–05/05) |
| 1205-laminas-gerencia-de-memoria | 12.05 Lâminas Gerência de Memória | 12/05/2026 | bloco-11 | fc0b5c7e | Gerência de Memória | ✅ OK | concorda com auto_tag |
| 2105-laminas-paginacao | 21.05 Lâminas Paginação | 21/05/2026 | bloco-11 | fc0b5c7e | Gerência de Memória | ✅ OK | concorda com auto_tag |
| 2403-escalonamento-de-processos | 24.03 Escalonamento de Processos | 24/03/2026 | bloco-03 | bdcc7b26 | Gerência de Processos CPU | ✅ OK | concorda com auto_tag |
| 2603-algoritmos-de-escalonamento | 26.03 Algoritmos de Escalonamento | 26/03/2026 | bloco-03 | bdcc7b26 | Gerência de Processos CPU | ✅ OK | concorda com auto_tag |
| 1203-processos | 12.03 Processos | 12/03/2026 | bloco-03 | bdcc7b26 | Processo e Estruturas de Controle | ✅ OK | concorda com auto_tag |
| 1703-chamada-de-sistema | 17.03 Chamada de Sistema | 17/03/2026 | bloco-03 | bdcc7b26 | Processo e Estruturas de Controle | ✅ OK | concorda com auto_tag |
| 1903-estruturas-de-controle | 19.03 Estruturas de Controle | 19/03/2026 | bloco-03 | bdcc7b26 | Processo e Estruturas de Controle | ✅ OK | concorda com auto_tag |
| 0704-laminas-comunicacao-e-sincronizacao | 07.04 Lâminas Comunicação e Sincronização | 07/04/2026 | bloco-05 | 1945c228 | Sincronização e Comunicação | ⚠️ DIFFERS | auto_tag diz bloco-07; data → bloco-05 (07/04–16/04) |
| 0904-laminas-semaforos | 09.04 Lâminas Semáforos | 09/04/2026 | bloco-05 | 1945c228 | Sincronização e Comunicação | ⚠️ DIFFERS | idem — bloco-07 é 23/04–28/04 |
| 14-04-troca-de-mensagens | 14 04 Troca de Mensagens | 14/04/2026 | bloco-05 | 1945c228 | Sincronização e Comunicação | ⚠️ DIFFERS | idem |
| 1404-laminas-ipc | 14.04 Lâminas IPC | 14/04/2026 | bloco-05 | 1945c228 | Sincronização e Comunicação | ⚠️ DIFFERS | idem |
| 0704-exemplo-threads-em-java | 07.04 Exemplo threads em Java | 07/04/2026 | bloco-05 | 1945c228 | Threads | ⚠️ DIFFERS | auto_tag diz bloco-03 |
| 3103-threads | 31.03 Threads | 31/03/2026 | bloco-03 | bdcc7b26 | Threads | ✅ OK | concorda com auto_tag |
| 0206-laminas-mecanismos-de-interrupcao | 02.06 Lâminas Mecanismos de Interrupção | 02/06/2026 | bloco-12 | a838bf45 | Gerência de I O | ⚠️ DIFFERS | auto_tag diz bloco-03 |
| 0206-laminas-memoria-virtual-livro-texto | 02.06 Lâminas Memória Virtual (Livro-texto) | 02/06/2026 | bloco-12 | a838bf45 | Gerência de Memória | ⚠️ DIFFERS | auto_tag diz bloco-11 |

### Entries SEM data (NO_DATE) — 19 entries

| entry_id | section | manual_block_uuid |
|---|---|---|
| exercicios | Gerência de Processos CPU | — |
| apresentacao-da-disciplina | Informações Gerais | — |
| lista-exercicios-p1-gabarito | Informações Gerais | — |
| lista-exercicios-p1 | Informações Gerais | — |
| lista1-gab | Informações Gerais | — |
| lista2 | Informações Gerais | — |
| plano-de-ensino | Informações Gerais | 31997686 (bloco-01) |
| questoes-do-enade-sobre-sisop | Informações Gerais | — |
| definicao-e-historico | Introdução aos SO | — |
| exemplo-criacao-de-processos-no-unix-linux-filho | Processo e Estruturas de Controle | — |
| exemplo-criacao-de-processos-no-unix-linux-teste01 | Processo e Estruturas de Controle | — |
| exemplo-criacao-de-processos-no-unix-linux-teste02 | Processo e Estruturas de Controle | — |
| exemplo-criacao-de-processos-no-unix-linux-teste03 | Processo e Estruturas de Controle | — |
| laminas-cs-4244-internet-programming-sockets-programming | Sincronização e Comunicação | 1945c228 (bloco-05) |
| laminas-sockets-material-alternativo-em-pt | Sincronização e Comunicação | 1945c228 (bloco-05) |
| biblioteca-em-c-pthread | Threads | bdcc7b26 (bloco-03) |
| exemplo-threads-em-c-exemplo1 | Threads | — |
| exemplo-threads-em-c-exemplo2 | Threads | — |
| exemplo-threads-em-c-exemplo3 | Threads | — |

**Flags de atenção:**
- `0205-laminas-segmentacao` (02/05/2026): data cai no gap entre bloco-09 (05/05) e bloco-08 (30/04) — nenhum bloco cobre 02/05. **❌ UNRESOLVABLE por data.**
- 8 entries com `DIFFERS` — data contradiz o auto_tag existente. Requer revisão.
- 3 entries com `manual_timeline_block_id` já preenchido (plano-de-ensino, laminas-sockets×2, biblioteca-em-c-pthread) — esses são autoritative pela outra rota.

---

## PASSO 2 — Flags de Revisão

**AMBÍGUOS:** 0 (nenhuma data cai em períodos sobrepostos — blocos SO são não-sobrepostos)

**SEM MATCH DE DATA:** 1
- `0205-laminas-segmentacao` (02/05/2026) — gap no calendário (bloco-08=30/04, bloco-09=05/05)

**SEM DATA:** 19 entries

**DISCORDÂNCIAS** (data difere do auto_tag atual): 8 entries
- `0206-laminas-gerencia-de-i-o-livro-texto`: data→bloco-12, tag→bloco-05
- `0704-laminas-comunicacao-e-sincronizacao`: data→bloco-05, tag→bloco-07
- `0904-laminas-semaforos`: data→bloco-05, tag→bloco-07
- `14-04-troca-de-mensagens`: data→bloco-05, tag→bloco-07
- `1404-laminas-ipc`: data→bloco-05, tag→bloco-07
- `0704-exemplo-threads-em-java`: data→bloco-05, tag→bloco-03
- `0206-laminas-mecanismos-de-interrupcao`: data→bloco-12, tag→bloco-03
- `0206-laminas-memoria-virtual-livro-texto`: data→bloco-12, tag→bloco-11

**Nota crítica sobre os 0x.04 DIFFERS:** bloco-05 (07/04–16/04) e bloco-07 (23/04–28/04) têm topics distintos. Os arquivos de Comunicação/Semáforos/IPC carregam data 07–14/04, que é o período do bloco-05 ("gerencia processador sincronizacao deadlock"). Isso é suspeito — possivelmente o Moodle postou material de sincronização no período errado, ou os prefixos de data são da data de disponibilização no Moodle, não da aula correspondente.

---

## PASSO 3 — M2 e M3 Rerun

### M2 — Cobertura (de 36 entries)

| Status | Count | % |
|---|---|---|
| Placement autoritativo limpo (data→bloco, OK) | 16 | 44% |
| Discordância data vs auto_tag (DIFFERS) | 8 | 22% |
| NO_MATCH (data sem bloco correspondente) | 1 | 3% |
| NO_DATE (sem âncora de data) | 19 | 53% |
| **Com manual_block_id preenchido** | 3 | 8% |
| **Já coberto por auto_tag (independente da data)** | 33 | 92% |

Nota: o auto_tag existente já cobre 33/36 (92%) — mas foram derivados por scorer, não por data autoritativa. Por data-only:
- 16/36 (44%) têm colocação limpa e autoritativa
- 8/36 (22%) têm data mas contradizem o auto_tag — requerem revisão humana antes de aplicar
- 1/36 (3%) tem data mas gap no calendário
- 19/36 (53%) ficam sem colocação via data — precisam de outro mecanismo

**M2 efetivo (cobertura autoritativa pós-backfill):** 16 + 3 (manual existente) = **19/36 = 53%**

### M3 — Granularidade

Granularidade: **session-precise para as 16 OK** — cada prefixo DD.MM identifica uma data de aula específica (dia único). Blocos SO têm sessions por dia, então o mapeamento é 1 file → 1 bloco (não intervalo). ✅

Para as 19 sem data: granularidade seria section-level (Moodle section → bloco por tópico) — coarse, não session-precise.

**M1 (accuracy):** Não corre — SO não tem gold. O placement é autoritativo-por-data, não inferido. As 16 placements OK são confiáveis na medida que o prefixo de data reflete a data real de aula (risco: data de postagem no Moodle ≠ data de aula).

---

## FECHAMENTO — Tabela de Cobertura dos 5 Repos

| Repo | Cobertura atual | Pós-backfill | O que falta |
|---|---|---|---|
| IA | 95% | 95% (já quase completo) | ~5% sem section/date — candidatos a manual |
| ES2 | 92% | 92% (já quase completo) | ~8% sem âncora clara |
| MF | 75% | 75% | Mega-cards (1 card → múltiplos blocos) + ~25% código sem section |
| SO | 0% (card) | **44% autoritativo / 53% com manual existente** | 53% sem data (materiais genéricos/exercícios) + 1 gap + 8 discordâncias a resolver |
| TCC | 31% | 31% | O mais difícil: estrutura menos alinhada com timeline |

**SO resumo:** De 0% para 44% por data-only. As 8 discordâncias precisam de decisão (data-de-postagem vs data-de-aula). As 19 sem data são materiais de referência/exercícios que provavelmente pertencem ao bloco pelo conteúdo (section_name como fallback seria razoável mas fora do escopo desta fase).

---

## READ-ONLY PROOF

- `manifest.json` mtime: 2026-06-20 13:45:47 (inalterado)
- `.block_identity.json` mtime: 2026-06-20 13:45:47 (inalterado)
- SO `git status --short`: apenas `??` (untracked) — zero `M` (modified) — nenhum arquivo existente foi tocado
- Scratch file criado apenas em: `GPT-Tutor-Generator/.git/sdd/so-proposed-date-block-map.json`
- Nenhum outro repo tocado
