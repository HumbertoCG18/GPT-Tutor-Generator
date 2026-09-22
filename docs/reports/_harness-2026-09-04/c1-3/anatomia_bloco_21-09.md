# W-L — anatomia dos 24 erros de BLOCO por entrada (21/09)

Fonte: manifests já gravados dos builds de 15/17-09. **Nenhum build, rede, LLM ou alteração em `src/`.**
Script: `anatomia_bloco_21-09.py` · JSON: `anatomia_bloco_21-09.json`
sha256(JSON) = `a36cc90a975039110d5074b89686191312c51aa756359c70cdc550ad06a5c746`
HEAD: 9220a57 · branch feat/motor-atribuicao

Gold (`mede.golds(sig)[0]`) usado **só** para rotular certo/errado, nunca como entrada de sinal.
Ausentes permanecem no denominador. Placar reproduzido: **bloco 213/237**, MF 53/66 (asserts no JSON, todos verdes).

## Agregados

| curso | certo/n | ausentes | erros com âncora | vazios |
|---|---|---|---|---|
| MF | 53/66 (80,3%) | 4 | 8 | 1 |
| SO | 36/39 (92,3%) | 0 | 2 | 1 |
| IA | 38/42 (90,5%) | 2 | 2 | 0 |
| ES2 | 27/28 (96,4%) | 0 | 1 | 0 |
| TCC | 26/27 (96,3%) | 0 | 0 | 1 |
| CG | 33/35 (94,3%) | 0 | 2 | 0 |
| **total** | **213/237 (89,9%)** | **6** | **15** | **3** |

Classes confirmadas (não recontadas do zero — reproduzidas): 6 ausentes, 8 vizinho ±1, 7 distantes, 3 vazios.

**Corte mais informativo que a distância — o gold estava na janela gravada?**

| | erros | métodos |
|---|---|---|
| gold **dentro** da janela → erro de **desempate** | 8 | `disamb` (8/8) |
| gold **fora** da janela → erro de **janela** | 7 | `janela-1` (4), `disamb` (3) |
| sem janela (vazio/ausente) | 9 | — |

Erros por método/banda (só os 15 com âncora): `disamb/baixa` 6, `janela-1/media` 4, `disamb/alta` 3, `disamb/media` 2.

Sentido: em 11 dos 15 há distância medível; **8 têm o gold posterior ao previsto** (motor ancora cedo), 3 anterior.

## (4) Risco por método+banda — quantas entradas estão CERTAS hoje com o mesmo par

| método/banda | erros | certas hoje (total) | MF | SO | IA | ES2 | TCC | CG |
|---|---|---|---|---|---|---|---|---|
| disamb/alta | 3 | 21 | 17 | 0 | 2 | 0 | 0 | 2 |
| disamb/baixa | 6 | 13 | 2 | 4 | 2 | 0 | 0 | 5 |
| disamb/media | 2 | 15 | 11 | 1 | 0 | 0 | 0 | 3 |
| janela-1/media | 4 | 38 | 11 | 8 | 0 | 11 | 5 | 3 |

Qualquer regra escrita "por método" toca esse volume de acertos. Nenhuma das certas em risco tem pino manual,
isto é, nenhuma está protegida pelo degrau `apply.py:78-80`.

## Tabela por entrada (24)

Colunas: cls = classe; dist = índice(previsto) − índice(gold); "na janela" = gold estava entre os candidatos gravados;
"conc." = `computed_block_id` (scorer de conceito) coincidiria com o gold; "un.err" = unidade também errada na régua.

| curso | entry_id | cls | método | banda | flag | provider | janela gravada | previsto | gold | dist | sentido | na janela | conc. | un.err | sinais presentes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CG | `basico3d-cpp` | distante | disamb | baixa | sim | topic | bloco-05, 13, 15 | bloco-05 | bloco-15 | −10 | gold posterior | **sim** | sim | sim | posting 2026-07-28; card "14 - Exercícios sobre Modelagem Geométrica" |
| CG | `basico3d-py-zip` | distante | disamb | baixa | sim | topic | bloco-05, 13, 15 | bloco-05 | bloco-15 | −10 | gold posterior | **sim** | sim | sim | card "14 - Exercícios sobre Modelagem Geométrica" (sem posting_date) |
| ES2 | `azure` | vizinho±1 | janela-1 | media | sim | card | bloco-08 | bloco-08 | bloco-09 | −1 | gold posterior | não | não | sim | posting 2026-02-18; card "Microsserviços" |
| IA | `algoritmo-de-classificacao-k-nn` | vizinho±1 | disamb | media | sim | labels | bloco-04, 05 | bloco-04 | bloco-05 | −1 | gold posterior | **sim** | não | não | seção com data e "Semana 3 - 16.03 a 20.03"; posting 2026-02-24 |
| IA | `analise-exploratoria-de-dados-exemplo-1` | vizinho±1 | disamb | baixa | sim | labels | bloco-04, 05 | bloco-05 | bloco-04 | +1 | gold anterior | **sim** | sim | não | mesma seção "Semana 3 - 16.03 a 20.03"; posting 2026-02-24 |
| IA | `ia-responsável-7c4626` | ausente | — | — | — | — | — | vazio | bloco-01 | — | — | — | — | n/a | url (microsoft.com), category references |
| IA | `o-que-é-inteligência-artificial-ia-oracle-brasil-43437f` | ausente | — | — | — | — | — | vazio | bloco-01 | — | — | — | — | n/a | url (oracle.com), category references |
| MF | `archive-of-formal-proofs-355fb8` | ausente | — | — | — | — | — | vazio | bloco-01 | — | — | — | — | n/a | url (isa-afp.org), category references |
| MF | `aws-encryption-sdk` | ausente | — | — | — | — | — | vazio | bloco-01 | — | — | — | — | n/a | github-repo, category bibliografia |
| MF | `eth2` | ausente | — | — | — | — | — | vazio | bloco-01 | — | — | — | — | n/a | github-repo, category bibliografia |
| MF | `exerciciosdafny2` | distante | disamb | alta | não | labels | bloco-10, 11, 12, 13, 15 | bloco-11 | bloco-13 | −2 | gold posterior | **sim** | não | não | ordinal 2 no id; posting 2026-02-18; card "Verificação de Programas" |
| MF | `exerciciosnusmv` | distante | disamb | alta | não | labels | bloco-16, 18, 19, 21 | bloco-18 | bloco-16 | +2 | gold anterior | **sim** | não | não | posting 2026-02-18; card "Especificação e Verificação de Modelos" |
| MF | `intro` | vizinho±1 | janela-1 | media | não | card | bloco-05 | bloco-05 | bloco-06 | −1 | gold posterior | não | não | não | posting 2026-02-18; card "Provas por Indução" |
| MF | `introducao` | vizinho±1 | disamb | baixa | sim | labels | bloco-01, 02 | bloco-01 | bloco-02 | −1 | gold posterior | **sim** | não | não | posting 2026-02-18; card "Introdução a Métodos Formais" |
| MF | `introducao-zip` | distante | janela-1 | media | sim | card | bloco-10 | bloco-10 | bloco-12 | −2 | gold posterior | não | sim | não | posting 2026-05-11; card "Verificação de Programas" |
| MF | `provas` | vizinho±1 | janela-1 | media | sim | card | bloco-05 | bloco-05 | bloco-06 | −1 | gold posterior | não | sim | não | posting 2026-02-18; card "Provas por Indução" |
| MF | `revisao` | vizinho±1 | disamb | alta | não | labels | bloco-03, 04 | bloco-04 | bloco-03 | +1 | gold anterior | **sim** | não | não | posting 2026-02-18; card "Revisão - Lógica e Especificação" |
| MF | `t1-2026-1` | ausente | — | — | — | — | — | vazio | bloco-11 | — | — | — | — | n/a | pdf; card "TDE Trabalho Discente Efetivo"; posting 2026-04-15; fora-de-escopo-disamb |
| MF | `t2-2026-1` | vazio | — | — | — | — | — | vazio | bloco-20 | — | — | — | não | não | card "TDE Trabalho Discente Efetivo"; posting 2026-06-14; fora-de-escopo-disamb |
| MF | `terminacao` | vizinho±1 | disamb | media | sim | card | bloco-10, 11 | bloco-11 | bloco-12 | −1 | gold posterior | não | não | não | posting 2026-05-11; card "Verificação de Programas" |
| SO | `definicao-e-historico` | vazio | — | — | — | — | — | vazio | bloco-03 | — | — | — | **sim** | não | posting 2026-03-10; card "Introdução aos Sistemas Operacionais" |
| SO | `laminas-cs-4244-internet-programming-sockets-programming` | distante | disamb | baixa | sim | card | bloco-06, 07 | bloco-06 | bloco-09 | −3 | gold posterior | não | sim | sim | posting 2026-03-10; card "Sincronização e Comunicação de Processos" |
| SO | `laminas-sockets-material-alternativo-em-pt` | distante | disamb | baixa | sim | card | bloco-06, 07 | bloco-06 | bloco-09 | −3 | gold posterior | não | não | sim | posting 2026-03-10; card "Sincronização e Comunicação de Processos" |
| TCC | `t1-enunciado` | vazio | — | — | — | — | — | vazio | bloco-04 | — | — | — | não | n/a | escopo-prazo; card "Semana 3 - ... e Trabalho 1"; posting 2026-03-18 |

## (1) Os 18 não-ausentes — leitura

- **Nenhum** dos 15 com âncora tem `data_no_nome` (regex `window_provider.py:346-363` não casa em nenhum deles).
  O sinal de data por prefixo simplesmente não existia nessas entradas; não é caso de "sinal ignorado".
- `posting_date` existe em 14 dos 15 (só `basico3d-py-zip` não tem) — é o sinal presente e não decisivo mais comum.
  Fato adicional: MF concentra `posting_date = 2026-02-18` em 5 erros, que é data de postagem em massa, não data de aula.
- `computed_block_id` (scorer de conceito, que a régua **não** mede) coincidiria com o gold em **7 dos 18**
  (CG ×2, MF `introducao-zip`, MF `provas`, IA `analise-exploratoria`, SO `laminas-cs-4244`, SO `definicao-e-historico`)
  e **erraria nos outros 11**. Não é um substituto; é um segundo voto que discorda do temporal em metade dos casos.
- Unidade também errada a montante em **5** entradas (CG ×2, SO ×2, ES2 `azure`) — bate com o dado já publicado.

## (2) Os 3 vazios — degrau da cascata (hipótese, não confirmável sem reexecutar)

| entrada | predicados avaliados agora | degrau provável |
|---|---|---|
| MF `t2-2026-1` | `tier2_due_scope`=False, `is_out_of_disamb_scope`=**True** | `apply.py:97-104` — temporal limpo antes de qualquer janela |
| TCC `t1-enunciado` | `tier2_due_scope`=**True**, `is_out_of_disamb_scope`=True | `apply.py:92-94` — due-window não casou e `resolve_unscoped` devolveu None |
| SO `definicao-e-historico` | ambos False | `apply.py:117-119` — `engine.resolve` None (funil-piso) |

Corroboração indireta (fato): entradas irmãs com `tier2_due_scope`=True **resolvem** por `prep-prova`/`due-contain`
(MF `revisao-p1`, `t1-2026-1-thy`, SO `lista-exercicios-p1/p2`, ES2 `revisao-p1/p2`, IA `p2-2024*`).
O degrau de prazo funciona; o que falha é a entrada que não entra nele.

**Achado relevante sobre `t1-2026-1`:** é o único "ausente" que **não é link**. Ele existe no pacote com o mesmo id —
o que mudou foi o `source_path` (Downloads → Desktop/Moodle), e por isso a régua de origem não o casa. Mas no pacote
ele sai **vazio** (`temporal_block_method` = None): sua `category` caiu de `trabalhos` (baseline) para `outros`
(pacote 17-09), `tier2_due_scope` virou False e ele cai no mesmo degrau de `t2-2026-1`. Casar a origem **não** o
converteria em acerto. Os dois formam um par com o mesmo mecanismo.

## (3) Sinais presentes e não decisivos — censo sobre os 18

| sinal | entradas | comentário |
|---|---|---|
| `posting_date` | 14 | presente quase sempre; em MF é data de postagem em lote |
| card/`source_section` com data ou semana | 3 (IA ×2, TCC `t1-enunciado`) | "Semana 3 - 16.03 a 20.03" |
| ordinal no id/título | 1 (`exerciciosdafny2`) | |
| data no prefixo de título/label/card/basename | **0** | regex de `window_provider.py` não casa em nenhum erro |
| categoria de prova/trabalho em escopo de prazo | 2 (TCC `t1-enunciado`, MF `t1-2026-1` no baseline) | |

## (5) MF: o que separa 53 de 60/66

13 entradas erradas. Nenhuma alavanca isolada cobre as 7 necessárias — o melhor grupo cobre 4.

| entrada | alavanca hipotética | certas hoje que a chave também atinge (MF / total) |
|---|---|---|
| `archive-of-formal-proofs-355fb8`, `aws-encryption-sdk`, `eth2` | ingestão de link (entrar no pacote) | 0 / 0 |
| `t1-2026-1`, `t2-2026-1` | TDE `outros` fora-de-escopo → devolver ao escopo de prazo | 3 / 8 |
| `exerciciosdafny2`, `exerciciosnusmv`, `introducao`, `revisao` | **desempate** dentro da janela `disamb` (gold já é candidato) | 30 / 49 |
| `intro`, `provas`, `introducao-zip` | janela `janela-1` de 1 bloco que não contém o gold | 11 / 38 |
| `terminacao` | janela `disamb` [10,11] que não contém o gold (12) | 11 / 15 (banda media) |

3+2+4+3+1 = 13. Para 60/66 seria preciso acertar 7 de 13, isto é, **pelo menos duas famílias distintas**.
Isto é contagem de cobertura, **não** ganho medido: nenhuma dessas alavancas foi executada.

## Alavancas — tocadas ÷ em risco (hipóteses, sem medição)

| alavanca | tocadas | em risco | razão | entradas |
|---|---|---|---|---|
| ingestão de link | 5 | 0 | — (sem risco) | MF ×3, IA ×2 |
| fora-de-escopo (TDE `outros`) | 2 | 8 | 0,25 | MF `t1-2026-1`, `t2-2026-1` |
| desempate `disamb` (gold na janela) | 6* | 34 | 0,18 | MF ×2, SO ×2, CG ×2 |
| fronteira `janela-1` (±1) | 3 | 38 | 0,08 | MF ×2, ES2 ×1 |
| fronteira `disamb` (±1) | 3 | 49 | 0,06 | MF ×3 |
| seção datada vence | 2 | 63 | 0,03 | IA ×2 |
| funil-piso (`engine` None) | 1 | 0 | — | SO `definicao-e-historico` |
| prazo sem due casado | 1 | 8 | 0,12 | TCC `t1-enunciado` |

\* a agregação do JSON usa `revisar-disamb` (distantes) e `fronteira-disamb` (±1) separadamente; somando o critério
"gold estava na janela" são 8 entradas em 4 cursos.

**A alavanca "seção datada vence" se auto-refuta como regra única (fato):** as duas entradas do IA estão no MESMO card
("Semana 3 - 16.03 a 20.03"), com janela idêntica [bloco-04, bloco-05], e erram em **direções opostas** — uma quer 05,
a outra quer 04. A seção não desempata o que está dentro dela; o problema é intra-card.

## Limitações e separação fato/hipótese

**Fatos** (lidos dos manifests): método, banda, flag, provider, janela, previsto, gold, distância, `computed_block_id`,
categoria, `source_section`, `posting_date`, `tier2_due_scope`/`is_out_of_disamb_scope` avaliados agora sobre a entry gravada,
e o pertencimento do gold à janela gravada.

**Hipóteses** (não medidas, não implementáveis a partir daqui):
1. O degrau exato da cascata em que cada vazio saiu — o motor não persiste o caminho percorrido.
2. Toda coluna "alavanca" e toda contagem "em risco": cobertura, não ganho. Nada foi reexecutado.
3. `computed_acertaria` é contrafactual de **campo**, não de execução: trocar o vencedor mudaria a cascata inteira.
4. Os 6 ausentes não têm `temporal_*` porque não há entry (5 links) ou porque a régua não casa a origem (1 PDF);
   em ambos os casos, **nenhuma regra de bloco os alcança hoje** — para os links, porque não existem no pacote.
