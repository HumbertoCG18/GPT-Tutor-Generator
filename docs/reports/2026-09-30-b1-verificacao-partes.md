# Verificação independente da seção B1 do dossiê (30/09/2026)

Nova tentativa, autorizada pelo usuário em 30/09 ~16:05, de validar a seção B1 do
`2026-09-30-dossie-decisoes-motor.md` (validação externa do regime VOCAB). Na madrugada, a B1 tinha sido escrita pelo
coordenador depois de duas falhas do worker (`job-12`, `job-17`). Desta vez a tarefa foi dividida em partes pequenas,
cada uma com as suas fontes.

Resultado:

- **63 afirmações numeradas:** 56 confirmadas, 3 divergem (D8 C2, R-VIS C5, R-CC C10) e 4 "sem evidência". Das 4, o
  coordenador resolveu duas depois (Gate 2 C4 e C7, confirmadas); ficam 2 abertas (D3 C11, D5 C8).
- **12 recomendações:**
  - 9 confirmadas;
  - 2 com divergência: D6 (menu de opções incompleto) e D8 (junta E3 e E4 numa medida só);
  - 1 "sem evidência": R-CC, porque "aprovar" era juízo do coordenador.

  O risco "sem data" da D6 também ficou sem evidência.

Nenhuma divergência inverte uma recomendação. Duas mudaram de forma (D8 e R-CC) e várias ganharam ressalvas. A B1 do
dossiê foi atualizada (§3).

**Rodada 2 (30/09 ~23:57):** as quatro partes que estouraram o tempo foram refeitas com os mesmos specs (`job-25` a
`job-28`). Todas concluíram em 165–178 s, com os mesmos vereditos e a D8–D9 completa. Ver a seção "Rodada 2" no fim.

## 1. Jobs

Uma chamada `alethe_delegate`, papel `planner-t2`, label "NOITE-3009 B1 validação externa (partes)", `run-12`, cwd na
árvore principal, somente leitura, teto de 600 s por worker. Uma tentativa por parte; nenhuma foi relançada.

| job | parte | fontes | resultado | duração | `askedToWrapUp` | saída / total de tokens |
|---|---|---|---|---:|:---:|---|
| `job-19` | D1–D3 | DP, PRE, P3, P3.1, E3 | **timeout**, texto completo entregue | 600,1 s | true | 6.352 / 373.922 |
| `job-20` | D4–D5 (+ C9 da D7) | DP, POL, PRE, E2, P3 + `git show 71dff722` | **succeeded** | 536,7 s | true | 5.654 / 370.557 |
| `job-21` | D6–D7 | DP, E2, E3, P3, P3.1 | **timeout**, texto completo entregue | 601,1 s | true | 6.486 / 296.523 |
| `job-22` | D8–D9 | DP, E2, E3, P3, P3.1 | **timeout**, texto cortado no fim da D9 (sem a seção de limitações) | 600,4 s | true | 2.460 / 390.894 |
| `job-23` | R-VIS + R-CC | ISS, REL, P3.1, PRE | **succeeded** | 548,3 s | true | 5.749 / 449.994 |
| `job-24` | Gate 2 do delta | REV, REL, ISS, `moodle.py`, `test_moodle.py` | **timeout**, texto completo entregue | 601,1 s | true | 6.723 / 381.358 |

- Modelo observado nos seis: codex `gpt-6.1-sol`, `readOnly = true`, `hasDiff = false`. `plannerId`
  `tsmq_2mmNF81XlNqqmYMe`. `threadId`: `job-19` `01a0f3b8-49f1-75b0-bf91-a633143f16f0`; `job-20`
  `01a0f3b8-49bf-7c01-a66a-32183abdb515`; `job-21` `01a0f3b8-4a0f-7e51-9e64-f69b89b292a5`; `job-22`
  `01a0f3b8-49f3-7180-9520-529de2dcb74f`; `job-23` `01a0f3b8-4a5a-7491-9913-4bc0ee13956f`; `job-24`
  `01a0f3b8-4aa8-7772-a447-3cbbe1925257`.
- **Todos os seis receberam o aviso dos 80 % e quatro estouraram mesmo assim.** A diferença para o `job-17` é que
  agora o texto escrito chegou. Em cinco dos seis, a tabela de vereditos já estava escrita antes do aviso.
- Nos dois `succeeded` (`job-20`, `job-23`), a mensagem final só dizia "a tabela já foi entregue". O texto completo
  foi recuperado do log local da sessão Codex (`~/.codex/sessions/2026/09/30/rollout-…-<threadId>.jsonl`), lendo
  apenas as mensagens do assistente.
- Nenhuma parte mirou abaixo de 70 % do teto na prática: 536–601 s. Com 4–5 fontes e 7–14 afirmações por parte, o
  tamanho ainda ficou no limite; o custo principal foi leitura (296–450 mil tokens de entrada por worker).

## 2. Resultado por decisão

Legenda: ✔ confirmado; ✎ mudou no dossiê; ○ sem validação.

| decisão | afirmações | confirma / diverge / sem evidência | recomendação | efeito na B1 |
|---|---|---|---|---|
| D1 | C1–C3 | 3 / 0 / 0 | ✔ | ✎ ressalva sobre C_novo com n = 10 |
| D2 | C4–C6 | 3 / 0 / 0 | ✔ | ✎ redação do risco |
| D3 | C7–C11 | 4 / 0 / 1 (C11, inferência) | ✔ | ✎ citação de C10 e dependência de R-CC |
| D4 | C1–C4 | 4 / 0 / 0 | ✔ | ✎ versão ausente também invalida |
| D5 | C5–C8 | 3 / 0 / 1 (C8, não medido) | ✔ | ✎ regex exata e alcance do `regexTarget` |
| D6 | C1–C5 | 5 / 0 / 0 | diverge (menu incompleto); risco sem evidência | ✎ rota combinada; risco reescrito |
| D7 | C6–C11 + C9 do `job-20` | 7 / 0 / 0 | ✔ | ✎ ressalvas de alcance |
| D8 | C1–C4 | 3 / 1 / 0 | diverge | ✎ **recomendação reformulada**: E4 e E3 são medidas diferentes |
| D9 | C5–C10 | 6 / 0 / 0 | ✔ | ✎ escopo da busca a congelar antes |
| R-VIS | C1–C7 | 6 / 1 / 0 | ✔ | ✎ C5 corrigida; contradição do REL:218 registrada |
| R-CC | C8–C14 | 6 / 1 / 0 | sem evidência | ✎ **recomendação vira "ajustar duas lacunas e aprovar"** |
| Gate 2 do delta | C1–C8 | 6 / 0 / 2 → **8 / 0 / 0** depois da conferência do coordenador (§2.12) | ✔ | ✎ opção 5 e ressalva sobre o delta local |
| **total** | **63** | **56 / 3 / 4** (58 / 3 / 2 após §2.12) | **9 ✔, 2 diverge, 1 sem evidência** | |

### 2.1 D1 — mínimo pós-gold e por curso (`job-19`)

- **Confirmado:** C1, C2, C3 e a recomendação "B com 10".
- **Ressalva nova (inferência aritmética do worker, conferida):** C_novo exige `acertos × 10 > 9 × n` (PRE:153). Com
  n = 10, isso significa 10 acertos em 10. O mínimo não cria margem estatística.
- **Nuance:** a opção B da DP limita "nenhum curso regride" aos cursos com mínimo (DP:18); a P3 e a P3.1 mantêm o veto
  de perdas também para os cursos pequenos (P3:94–96; P3.1:145–149). A recomendação é um B refinado, não literal.
- **Sugestão do planejador:** separar explicitamente mínimo para C_novo, alcance do veto e exigência de diversidade
  pós-gold (a P3.1 só exige 3 cursos antes do gold; P3.1:148–149).

### 2.2 D2 — bloco (`job-19`)

- **Confirmado:** C4, C5, C6 e a recomendação A.
- **Correção de redação:** o risco dizia que a validação "não dirá nada sobre acerto de bloco fora dos sete cursos".
  Isso sugere uma acurácia medida nos sete, que não foi conferida. A ressalva correta é "sem conclusão de acurácia de
  bloco nos cursos novos".
- **Nuance:** a redação do PRE sobre bloco está suspensa enquanto D2 estiver aberta (DP:3–4).
- **Sugestão do planejador:** registrar "A nesta validação; B num estudo temporal separado", como a P3 já descreve
  (P3:107–113).

### 2.3 D3 — unidade amostral e duplicatas (`job-19`)

- **Confirmado:** C7, C8, C9, C10 e a recomendação B.
- **C10, citação refinada:** P3:145 trata da deduplicação em E3/E4; a consistência no build está em P3:149.
- **C11 sem evidência:** reescrever o PRE §4.4 é sustentado; editar o avaliador genérico continua inferência.
- **Dependência nova:** a P3.1 acrescenta a regra de conflito contextual (R-CC), que pode excluir documentos do gold.
  Escolher B não resolve R-CC (P3.1:96–124).
- **Distinção a fixar:** documento sem entry no build conta como erro; falha de correspondência de IDs entre braços
  deixa B_novo "não avaliado" (P3:52–54; P3.1:125–133).

### 2.4 D4 — `model_version` (`job-20`)

- **Confirmado:** C1–C4 e a recomendação de implementar a verificação.
- **Sugestão do planejador:** a verificação deve tratar versão **ausente ou vazia** como inválida, não só valores
  distintos (POL:20 exige que todas as respostas tragam a versão).
- **Não conferido:** se o metadado está disponível nos registros do harness, condição para implementar só no harness.

### 2.5 D5 — âncora do gitleaks (`job-20`; regex conferida pelo coordenador)

- **Confirmado:** C5, C6, C7 e a recomendação.
- **Evidência nova:** o commit `71dff722` introduz, no `.gitleaks.toml`:
  `regexes = ['''resumo[\w.-]*\.json"\s*:\s*"[0-9a-f]{64}''']`, com `regexTarget = "match"`, `condition = "AND"`,
  `targetRules = ["sumologic-access-token"]` e `paths = ['''^docs/reports/_harness-2026-09-04/''']`. Termina no hash,
  sem `$`, com hex minúsculo.
- **Sugestão do planejador:** com `regexTarget = "match"`, ancorar a regex fecha o trecho casado pela regra, não a
  linha. "Fechar a âncora" precisa definir o formato completo admitido antes de acrescentar `$`.
- **C8 continua sem evidência:** quantas ocorrências dependem da amplitude atual não foi medido.

### 2.6 D6 — regra do lote (`job-21`)

- **Confirmado:** C1–C5.
- **Nuance de C1:** a DP fixa a regra da etapa (v2 no lote), não só um princípio (DP:54–55).
- **Diverge (menu incompleto):** exploração e confirmação podem coexistir. Faltam duas opções:
  - rota combinada: preservar o resultado v2, analisar o lote como exploratório e preparar à parte uma confirmação
    prospectiva;
  - aprovar e congelar a redação sem autorizar a aplicação imediata (P3.1:24, 181–182).
- **Sem evidência:** "o veredicto de generalização fica sem data" era inferência do coordenador. As fontes não fixam
  calendário. Reescrito como "sem calendário definido nas fontes".
- **Contradição documental nova:**
  - a P3 diz que D6 "fica fora" (P3:5) e, no §12, que D6 foi "substituído pelo §14" (P3:135);
  - a P3 exige o "pacote cego v3 aprovado" (P3:160), enquanto a P3.1 já cita as versões v5 (P3.1:64).

  A compatibilidade precisa ser explicitada antes de autorizar a aplicação.

### 2.7 D7 — links e E4 (`job-21`; C9 no `job-20`)

- **Confirmado:** C6–C11, a recomendação e, no `job-20`, a afirmação do PRE:38–41.
- **Nuances:**
  - três dos cursos também falham em E2 (E2:78–83); as causas não são exclusivas;
  - os 461 itens registrados não são automaticamente o denominador de E4;
  - manter 90 % não mantém a mesma medida, porque na P3.1 E4 conta ocorrências e E3/mínimos contam documentos
    (P3.1:71–87);
  - a identificação do HTML de página (R-PAGE) é provisória e também afeta o alvo (P3.1:57–64).
- **Sugestão do planejador:** num estudo prospectivo separado, avaliar manter destinos externos no alvo com protocolo
  próprio de captura; viabilidade não demonstrada.

### 2.8 D8 — downloads que falharam (`job-22`)

- **Confirmado:** C1, C3, C4.
- **Diverge (C2):** a lista completa de casos não cobertos e a regra "o sucesso de outra ocorrência com os mesmos
  bytes não cobre a que falhou" são da P3.1 (P3.1:65–79). A P3 enumera menos casos e fala em "unidades" (P3:58–72).
- **Diverge (recomendação):** "falhas no denominador de E3/E4" junta duas medidas diferentes. Na P3.1:
  - E4 é cobertura **por ocorrência** do alvo, com as falhas no denominador como não cobertas;
  - E3 é o **número** de documentos cobertos distintos; falha não entra como denominador, só deixa de gerar documento
    coberto (P3.1:54–56, 78–90).
- **Recomendação reformulada:** falhas no denominador de E4; E3 conta só documentos cobertos (a redação da P3.1).
- **Risco reformulado:** E4 passa a misturar disponibilidade da aquisição, proveniência e admissibilidade pelo
  cegamento.

### 2.9 D9 — alcance da busca de exposição (`job-22`)

- **Confirmado:** C5–C10 e a recomendação, como sugestão do coordenador.
- **Ressalva nova:** `git grep` em todas as branches e worktrees não cobre arquivos não versionados nem revisões
  históricas. Os próprios relatórios da validação são não versionados (E3:162–164).
- **Sugestão do planejador:**
  - congelar antes da busca quais branches, revisões, worktrees e arquivos locais entram;
  - uma fonte requisitada que não puder ser examinada não vira "zero matches" (P3.1:168–177).
- **Corte:** o texto parou no fim da D9, antes das limitações. A tabela e o aprofundamento das duas decisões chegaram
  completos.

### 2.10 R-VIS (`job-23`)

- **Confirmado:** C1, C2, C3, C4, C6, C7 e a recomendação do REL:221.
- **Diverge (C5):** "aceita só pela assinatura" generaliza demais. O PDF tem o dicionário Info lido e o notebook tem
  varredura textual; o que continua sem inspeção suficiente são as estruturas listadas: pixels, XMP e base64
  (REL:194–205).
- **Contradição documental nova:** REL:218 diz que os pixels seriam aceitos "como já foi aceito para o texto de PDF em
  imagem". O mesmo relatório (REL:169–171) e o issue (ISS:141–142) corrigem isso: essa aceitação está pendente.
- **Sugestões do planejador:**
  - explicitar o tratamento de vetores e o significado de "inspeção suficiente";
  - alinhar EXIF, que aparece nos testes de aceite (ISS:332) mas não na enumeração da b2 (REL:216–218);
  - esclarecer que os "mesmos arquivos limpos" dos controles não incluem OLE/MP4.
- **Ressalva de justificativa:** "b1 derruba quase todos os slides" (REL:214–215) é apreciação qualitativa, não
  medida. A escolha deve se apoiar no alcance da inspeção aceito, não nesse número.

### 2.11 R-CC (`job-23`)

- **Confirmado:** C8, C9, C11, C12, C13, C14.
- **Diverge (C10):** a exclusão por conflito exige as **duas** condições: o conteúdo não decide a unidade **e** as
  ocorrências estão em seções de unidades diferentes (ISS:292–293). O dossiê tinha omitido a segunda.
- **Lacuna que decorre disso:** unidade indeterminável sem ocorrências em unidades diferentes não tem encaminhamento
  na regra.
- **C11 complementada:** a conta de sensibilidade vale para A_novo e C_novo, não para B_novo (ISS:310–311).
- **Recomendação "sem evidência":** "aprovar" é juízo do coordenador, não recomendação das fontes. O worker concorda
  com a direção, mas recomenda ajustar antes de aprovar:
  - dar encaminhamento ao caso descoberto;
  - fazer a P3.1 mencionar a sensibilidade do marcador `?`.

  **O coordenador adota essa posição:** a lacuna é real.
- **Inferência do worker:** acrescentar os mesmos conflitos como erro em todos os braços preserva a ordenação de
  A_novo; a pressão da sensibilidade recai sobre o limiar de C_novo.

### 2.12 Gate 2 do delta Moodle (`job-24`; C4 e C7 resolvidos pelo coordenador)

- **Confirmado:** C1, C2, C3, C5, C6, C8 (como inferência) e a recomendação.
- **Causalidade no código** (worker, conferida): o truncamento nasce em `r.read(pedir)` (MOO:451) e o tratamento soma
  só `exc.partial` (MOO:452–455). O Content-Length é lido sem distinguir chunked (MOO:440–441). Sem limite, a
  comparação de MOO:461–462 levanta `IncompleteRead`. Com limite, a leitura para no saldo (MOO:447–449), a recusa
  conservadora de MOO:463–464 não dispara porque há `esperado`, e o fragmento é decodificado em MOO:475.
- **C4, resolvido pelo coordenador (medido, `grep` somente leitura):** `MoodleClient` aparece só em
  `tests/test_moodle.py`. As ocorrências de "chunked" na suíte (`test_core.py`, `test_datalab_image_extraction.py`) são
  do backend Datalab, não de HTTP. **Nenhum teste da suíte exercita o `MoodleClient` com resposta chunked.**
- **C7, resolvido pelo coordenador:** "nova aquisição exige manifesto novo e Gate de rede" está em E3:89–90 e
  REL:187. Os trechos de REL e ISS dados ao worker não traziam essa linha.
- **Mudou no dossiê:**
  - **opção 5 (sugestão do planejador): abandonar formalmente o delta e retirá-lo da árvore.** Exige reconciliar o
    `adquire` v5, que depende do contador e do limite do cliente (REL:305–309);
  - **ressalva:** "não commitar por enquanto" **não tira o delta de execução**. A árvore principal roda com o
    `_call` modificado (MOO:475), inclusive pela UI (`dialogs.py:1719`);
  - **escolha de contrato na correção:** recusar cabeçalhos conflitantes não restaura o comportamento anterior do
    caso 2a. Se for essa a escolha, o aceite precisa dizer isso, em vez de manter a promessa de compatibilidade
    (ISS:344–345).

## 3. O que mudou no dossiê

`2026-09-30-dossie-decisoes-motor.md` foi atualizado:

- cada decisão da B1 ganhou uma linha **Verificação** com o job, o resultado e o que mudou;
- as frases que divergiam foram corrigidas no lugar: D2 (risco), D3 (C10), D6 (opções e risco), D8 (recomendação),
  R-VIS (C5), R-CC (C10 e recomendação) e Gate 2 (opção 5 e ressalva);
- o quadro de decisões (§1) e o §0 registram a verificação;
- as contradições novas entraram em "B1 — Contradições encontradas".

## 4. O que ficou sem validação

- **Afirmações "sem evidência" que continuam abertas:** D3 C11 (editar o avaliador genérico, inferência); D5 C8
  (ocorrências dependentes da amplitude da regex, não medido); D6 risco de calendário (reescrito); R-CC "aprovar"
  (substituído).
- **Não conferido por nenhum worker nem pelo coordenador:**
  - o código do harness genérico (D3, D4);
  - a configuração atual do gitleaks e o seu comportamento (D5);
  - o efeito de qualquer regra no lote (nenhum cálculo, por desenho);
  - a frequência real de respostas chunked com Content-Length conflitante na instância (Gate 2);
  - o cronograma de uma aquisição prospectiva (D6).
- **Texto cortado:** a seção de limitações do `job-22` (D8–D9) não chegou. A tabela e o aprofundamento chegaram.
- **Números:** os workers confirmaram contra os documentos; nenhum número foi recalculado a partir dos dados.

## Anexo — textos dos workers

Mensagens do assistente, na ordem, recuperadas do log local de cada sessão Codex. Para o `job-22`, o texto parcial
entregue pelo Alethe no timeout (o log local só guardou as mensagens iniciais). As tabelas repetidas pelos workers
foram mantidas.

### job-19 — D1–D3

````text
[2026-09-30T19:10:01.614Z]
Vou conferir C1–C11 apenas nos cinco arquivos permitidos, por intervalos de linhas, e apresentar a tabela antes do aprofundamento. Sem executar testes ou alterar arquivos.

---MSG---

[2026-09-30T19:11:26.011Z]
Os cinco arquivos estão disponíveis. A conferência usará os textos do disco; afirmações sobre código, cálculos ou revisão externa serão avaliadas apenas pelo que esses documentos registram.

---MSG---

[2026-09-30T19:13:54.565Z]
As fontes sustentam o núcleo das recomendações, com duas ressalvas: D1 mantém o veto de perdas também nos cursos abaixo do mínimo, refinando a opção B de DP; D3 inclui uma regra de conflito contextual ainda proposta, que pode excluir documentos do gold. P3.1 também limita qualquer análise deste lote conhecido a exploratória/descritiva.

---MSG---

[2026-09-30T19:18:01.665Z]
| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D1 | C1 — mínimos totais, sem mínimo por curso | confirma | PRE:31–33; DP:12–13 | Ausência de mínimo **pós-gold** por curso; E3 já exige mínimo pré-gold (PRE:28). |
| D1 | C2 — P3/P3.1 propõem B com 10, preservando agregado e veto | confirma | P3:94–96; P3.1:145–149 | Curso pequeno fica descritivo quanto a C_novo, mas suas perdas continuam vetando. P3 associa 10 a E3. |
| D1 | C3 — precisão não calculada; efeito pós-gold ainda inaplicável | confirma | DP:19; P3:148 | Ambas as ressalvas são explícitas. |
| D1 | **Síntese — recomendação B com 10 e risco convencional** | confirma | P3.1:14–19,145–149 | É proposta, não decisão vigente; [C] indica conhecimento prévio, não prova calibração deliberada. |
| D2 | C4 — PRE descreve dois eixos e invariância de bloco por ID | confirma | PRE:48–52,149–151 | Essa redação consta do PRE, mas está suspensa enquanto D2 permanecer aberto (DP:3–4). |
| D2 | C5 — estabilidade, sanidade prévia e B_novo “não avaliado” se falhar | confirma | P3:107–113; P3.1:128–134 | Comparação por entry/ID; ausência, duplicação ou vínculo não resolvido impedem o veredicto. |
| D2 | C6 — acurácia exige gold temporal independente e protocolo próprio | confirma | P3:111–113; P3.1:135–136 | Acurácia fica fora desta validação. |
| D2 | **Síntese — recomendação A e alcance limitado** | confirma | P3:107–113; P3.1:128–136 | A ressalva correta é “sem conclusão de acurácia nos cursos novos”; acurácia nos sete anteriores não foi conferida. |
| D3 | C7 — replicação `material@eid` e inflação do denominador | confirma | DP:33–35; PRE:66–68 | Confirmação documental: código e demonstração da revisão não foram inspecionados. |
| D3 | C8 — nove pares de duplicatas em três cursos | confirma | E3:94–97; P3:14 | E3 registra os pares; P3 acrescenta a distribuição por cursos. |
| D3 | C9 — documento por curso/hash, uma linha, todas as entries e ausência como erro | confirma | P3:40–54; P3.1:83–84,94–95,125–127 | Consistência é exigida **por eixo**; ocorrências permitidas ficam visíveis. |
| D3 | C10 — efeito no lote não calculado | confirma | P3:3–4,145,149 | A linha 145 trata da deduplicação em E3/E4; a consistência no build aparece separadamente na linha 149. |
| D3 | C11 — exige editar avaliador genérico e reescrever PRE §4.4 | sem evidência | PRE:66–68,134–135; P3.1:125–127 | Reescrever PRE é sustentado; editar especificamente o avaliador é inferência plausível, sem demonstração de implementação. |
| D3 | **Síntese — recomendação B e maior severidade** | confirma | DP:40; P3:52–54; P3.1:125–127 | Uma entry errada reprova o documento naquele eixo; a regra contextual também precisa ser resolvida. |

**D1.** O menu cobre as principais alternativas, mas não fecha a política inteira. DP limita “nenhum curso regride” aos cursos com mínimo; P3/P3.1 preservam o veto de perdas também nos cursos pequenos — portanto, a recomendação é uma versão refinada de B, não sua adoção literal (DP:18; P3:94–96; P3.1:145–149). **Sugestão do planejador:** separar explicitamente mínimo para C_novo, alcance do veto e exigência de diversidade pós-gold. P3.1 atualmente exige quantidade de cursos apenas antes do gold e depois manda relatar quantos atingiram o mínimo (P3.1:148–149).

Isso destrava a redação metodológica necessária ao Gate 1 e a classificação pós-gold usada na avaliação; os denominadores são congelados na etapa de ligação ao build, antes do Gate de avaliação (PRE:102–108,115). **Concordo com B com 10 como convenção operacional**, preservando todas as perdas no veto; não como garantia de precisão ou justificativa confirmatória para o lote conhecido (P3.1:19,21–23).

Risco residual: pode haver concentração da amostra em poucos cursos. Além disso, **inferência aritmética**, não experimento: com dez documentos, C_novo exige dez acertos, porque a desigualdade é estrita; o mínimo não cria margem estatística de segurança (PRE:153; P3.1:145–146).

**D2.** As alternativas distinguem estabilidade, gold temporal independente e rótulos produzidos pelo motor, mas não precisam ser mutuamente excludentes entre estudos. **Sugestão do planejador:** explicitar “A nesta validação; B em estudo temporal separado”, combinação já descrita pela P3; C conserva o problema de cegamento apontado em DP (DP:27–29; P3:107–113).

A escolha A fecha eixos, linguagem dos relatórios e condição de B_novo, permitindo especificar sanidade e comparação antes da avaliação (PRE:48–52,113–115; P3.1:128–136). **Concordo com A para a pergunta atual:** verifica se o vocabulário altera blocos sem fornecer ao adjudicador rótulos derivados do motor.

Risco residual: dois braços podem concordar em um bloco errado. Entries distintas do mesmo documento também podem ter blocos diferentes entre si; a exigência é preservar cada entry entre braços, não uniformizar o documento (P3.1:129–134). As fontes não sustentam uma conclusão sobre acurácia nos cursos anteriores.

**D3.** O menu cobre as políticas principais de duplicação, mas não fecha conflitos contextuais. P3.1 acrescenta rótulos múltiplos, ambiguidade somente de subunidade e exclusão por conflito, com análise de sensibilidade; essa regra continua proposta e exige nova versão do contrato do gold (P3.1:96–124). **Sugestão do planejador:** tratar aprovação dessa regra como decisão explícita, em vez de pressupor que escolher B já a resolve.

D3 destrava a identidade documental e o pacote de adjudicação antes do gold, além da ligação, pontuação e denominadores posteriores ao build (PRE:103–108; P3.1:83–95,125–127). **Concordo com B se o alvo for a confiabilidade do documento em todas as suas aparições:** evita contar repetidamente o mesmo julgamento e impede que uma representante esconda erros das demais.

Risco residual: maior multiplicidade cria mais oportunidades de reprovar um documento. Também é necessário distinguir **documento sem entry no build**, que conta como erro, de **falha de correspondência de IDs entre braços**, que deixa B_novo não avaliado (P3:52–54; P3.1:125–133). C11 sustenta a necessidade de adaptar a avaliação à nova semântica, mas não demonstra qual arquivo precisa ser editado.

**Limitações.** Conferi somente os textos permitidos: não confirmei código, revisão original, contagens por inspeção dos materiais, cálculos ou estado git. DP suspende as regras anteriores, e P3.1 permanece não aprovada; resolver D1–D3 não fecha os demais pontos nem autoriza aquisição, gold, build ou motor (DP:3–4,47–69; P3.1:5–8,24,181–182). Qualquer análise deste lote conhecido permanece exploratória/descritiva; avaliação confirmatória exige aquisição prospectiva sob protocolo previamente congelado (P3.1:21–23).

---MSG---

[2026-09-30T19:18:46.974Z]
A tabela de vereditos e o aprofundamento já foram entregues. Nada ficou pendente no escopo documental.

Não conferidos, pelas restrições: código do avaliador, demonstração original da revisão, contagens nos materiais e estado git. C11 ficou parcialmente sustentada: PRE §4.4 precisa ser reescrito; editar especificamente o avaliador genérico permanece inferência plausível.
````

### job-20 — D4–D5 (+ C9 da D7)

````text
[2026-09-30T19:09:58.132Z]
Vou conferir as nove afirmações nas cinco fontes e no commit permitido. Entregarei primeiro a tabela; depois, minha leitura das opções e recomendações, sem alterar arquivos.


---MSG---

[2026-09-30T19:13:16.400Z]
D4 e D5 constam como pendências no dossiê. O commit confirma a regex sem âncora final; a falha de `model_version` tem confirmação documental, mas o código está fora do escopo. Falta fechar os trechos da P3 e a ressalva normativa da D7.


---MSG---

[2026-09-30T19:17:19.424Z]
| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D4 | C1 — mesmo `model_version` em todas as respostas; mistura invalida | confirma | POL:20–21; PRE:123–125 | Homogeneidade dentro da rodada; sem comparação com VOCAB_LIMPO. |
| D4 | C2 — código não aborta com versão mista ou ausente | confirma | DP:49–50; E2:40 | Confirmação documental do defeito declarado “demonstrado”; código não inspecionado. |
| D4 | C3 — modelo é alias sem versão imutável | confirma | POL:14; PRE:173 | Limitação explicitamente registrada. |
| D4 | C4 — ficou fora da P3 | confirma | P3:133 | Continua aberto. |
| D4 | **Resumo — regra e implementação divergem; decisão pendente** | confirma | DP:49–51; P3:133 | A sanidade proposta resolve a lacuna, se verificar presença e homogeneidade. |
| D5 | C5 — regex permite hash seguido de espaço/sufixo; alteração fora da autorização | confirma | DP:52–53; E2:34–35; `.gitleaks.toml@71dff722:20` | São hex **minúsculos**; a regex termina no hash, sem `$`. |
| D5 | C6 — fora da P3, sem allowlist nova | confirma | P3:134 | Afirmação limitada à proposta. |
| D5 | C7 — exceção introduzida pelo commit indicado | confirma | `git show --stat 71dff722`; `.gitleaks.toml@71dff722:15–21` | O diff adiciona a exceção específica do harness. |
| D5 | C8 — quantidade de linhas atuais dependentes do sufixo não medida | sem evidência | DP:52–53; E2:34–35; P3:134 | Nenhuma contagem apresentada; isso não prova que nunca houve medição. |
| D5 | **Resumo — ausência de âncora comprovada; impacto atual desconhecido** | confirma | `.gitleaks.toml@71dff722:20`; DP:52–53 | Falta medir consumidores e conferir o scanner. |
| D7 | C9 — mínimo insuficiente impede início; limiares não acomodam cursos disponíveis | confirma | PRE:38–41 | É a regra normativa expressa. |
| D7 | **Resumo — afirmação fiel ao pré-registro** | confirma | PRE:38–41 | Não equivale a uma verificação operacional atual. |

Fontes: [DP], [POL], [PRE], [E2], [P3].

**D4 — minha leitura**

As opções são completas quanto à decisão normativa: manter a exigência e implementá-la, ou retirá-la. Falta fechar o contrato da verificação.

- **Sugestão do planejador:** explicitar que versão ausente ou vazia também impede validar a geração. Conferir apenas quantidade de valores distintos pode aceitar respostas sem metadado; POL:20 exige que todas tragam a versão.
- **Implementar:** permite verificar a integridade da geração antes das etapas seguintes; mistura ou ausência interrompem, preservando os registros, sem regenerar. O fechamento da D4 remove uma pendência do pré-registro, mas não libera os demais Gates ou resolve a população insuficiente (DP:3–4; PRE:35–41,113–118).
- **Retirar:** elimina esse veto, após revisão normativa explícita, permitindo prosseguir sem garantia de homogeneidade. Retirar a regra não corrige o metadado ausente.

**Concordo com implementar na sanidade, sem nova geração:** torna verificável uma exigência já escrita. A possibilidade de fazê-lo exclusivamente no harness depende de o metadado estar disponível nos registros; isso não foi conferido neste escopo.

**Risco residual:** versões iguais dentro da rodada não demonstram igualdade com VOCAB_LIMPO, como POL:21 expressamente ressalva. Alias mutável e parâmetros default continuam sendo limitações (POL:14–15; PRE:173).

**D5 — minha leitura**

Regex exata introduzida pelo commit, em `.gitleaks.toml@71dff722:20`:

```toml
regexes = ['''resumo[\w.-]*\.json"\s*:\s*"[0-9a-f]{64}''']
```

A exceção usa `regexTarget = "match"` e condição `AND`, limitada à regra `sumologic-access-token` e ao caminho do harness (`.gitleaks.toml@71dff722:17–21`). Como o padrão termina no hash sem âncora, texto posterior não impede esse casamento — sustenta C5.

As opções abrangem fechar ou manter o comportamento atual, mas “fechar” precisa definir exatamente qual trecho deve terminar ali.

- **Sugestão do planejador:** definir o formato completo admitido e conferir o trecho submetido a `regexTarget = "match"` antes de acrescentar `$`. Ancorar o match não significa necessariamente ancorar a linha inteira.
- **Fechar:** restringe a exceção e remove a pendência documental após alteração e validação. Não demonstra, sozinho, ausência de segredos.
- **Manter:** permite encerrar a decisão mediante aceitação explícita da amplitude atual; não reduz a amplitude da exceção.

**Concordo com restringir a exceção:** o comentário do commit promete “formato exato”, mas a regex admite continuação. Concordo com conferir o gitleaks antes de considerar a mudança validada; nenhum efeito sobre linhas legítimas foi medido aqui.

**Risco residual:** um sufixo hoje tolerado pode deixar de ser dispensado, se pertencer ao trecho avaliado pelo scanner. O diff comprova a origem da exceção, mas não comprova sua configuração atual nem quantas ocorrências dependem dela.

**D7 — conferência avulsa**

C9 reproduz corretamente PRE:38–41: aguardar candidatos, recalcular pela mesma regra e script congelado, sem ajustar limiares à disponibilidade. Não avaliei outras opções ou recomendações da D7, conforme o recorte solicitado.

**Limitações**

Conferi documentos e o commit permitido. Não revalidei o defeito no código, a regex atual, seus consumidores ou o comportamento do gitleaks; “demonstrado” permanece atribuído ao dossiê. Branch/HEAD foram tratados como contexto fornecido, sem comandos adicionais; nenhum teste, alteração ou execução experimental foi realizado.

---MSG---

[2026-09-30T19:17:45.302Z]
A tabela de vereditos e o aprofundamento já foram entregues. Conferência documental concluída, sem alterações.

Ficaram sem verificação independente: código do harness, regex atual, quantidade de linhas dependentes do sufixo e comportamento do gitleaks — fora do escopo autorizado. C8 permanece **sem evidência**; C2 confirma o relato documental, não uma nova demonstração.
````

### job-21 — D6–D7

````text
[2026-09-30T19:09:59.971Z]
Vou conferir as cinco fontes por linhas, registrar primeiro os vereditos e depois avaliar as opções. Somente leitura; sem aplicar regras ao lote.

---MSG---

[2026-09-30T19:11:49.100Z]
Branch e HEAD conferem. Há alterações locais em outros arquivos; não vou lê-las. A regra v2 registra seleção vazia, e as fontes já avisam que a proposta foi formulada com as contagens conhecidas.

---MSG---

[2026-09-30T19:15:05.196Z]
| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D6 | C1 — v2 no lote; ajuste de limiar exige decisão explícita | confirma | DP:54–55 | É regra da etapa, não apenas orientação; decisão deve reconhecer as contagens. |
| D6 | C2 — §14 substitui D6; aplicação única; lote exploratório, confirmação prospectiva | confirma | P3:135,157–161; P3.1:21–24 | Vigência proposta, ainda não autorizada. |
| D6 | C3 — nenhum curso pela v2 | confirma | E2:76–87 | Resultado documental da regra vigente. |
| D6 | C4 — resultado P3/P3.1 deliberadamente não calculado | confirma | P3:152–153; P3.1:5–6 | Não permite prever elegibilidade pela emenda. |
| D6 | C5 — catálogo esgotado quanto aos N0; nova aquisição em outra conta/semestre | confirma | E2:53–62,66; P3:102–103 | Inferência restrita ao catálogo e à classificação registrados. |
| D6 | Resumo — alternativas e recomendação do coordenador | diverge | P3.1:21–24,181–182; P3:157–161 | Menu incompleto: exploração e confirmação podem coexistir; aprovação não autoriza execução. |
| D7 | C6 — reprovação em E3/E4; E4 é a única barreira para os cursos que passam E2/E3 | confirma | DP:59–60; E2:78–85 | Nos demais, também pode falhar E2; não são causas exclusivas. |
| D7 | C7 — links externos no total de itens registrados | confirma | E2:66–68 | 171 de 461 registros; esse total não é automaticamente o denominador de E4. |
| D7 | C8 — módulos `url` fora do alvo; razão operacional; regra universal | confirma | P3.1:36–50,189 | Não afirma impossibilidade de congelar ou adjudicar links. |
| D7 | C9 — mudança mais sensível; efeito não calculado; percentual mantido | confirma | E3:128–130; P3:144; P3.1:18,78–79 | Atribuição aos links é relatada; efeito líquido não foi isolado aqui. |
| D7 | C10 — conclusões excluem conteúdo acessado por link | confirma | P3:124–125; P3.1:36–43,163–164 | Restrição substantiva do alcance. |
| D7 | C11 — mantendo v2, seleção vazia | confirma | E2:87; P3:152–153 | Resultado preservado; não é resultado da P3.1. |
| D7 | Resumo — excluir links do alvo com enquadramento exploratório | confirma | P3.1:14–23,42–50 | Sustentação documental; concordância metodológica condicionada ao alvo pretendido. |

Vou aprofundar duas ressalvas: exploração não substitui confirmação prospectiva, e a P3.1 altera mais que a presença de links no denominador.

---MSG---

[2026-09-30T19:18:42.125Z]
| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D6 | C1 — lote segue v2; ajuste de limiar exige decisão explícita | confirma | DP:54–55 | Ressalva ao “só princípio”: DP fixa a regra da etapa, reconhecendo as contagens conhecidas. |
| D6 | C2 — entrada em vigor substitui D6; aplicação única; exploração retrospectiva e confirmação prospectiva | confirma | P3:135,155–161; P3.1:21–24 | São condições propostas, ainda não autorização. P3:5 diz que D6 fica fora, em tensão com P3:135. |
| D6 | C3 — nenhum curso elegível pela v2 | confirma | E2:76–87 | Resultado registrado para o lote. |
| D6 | C4 — resultado P3/P3.1 deliberadamente não calculado | confirma | P3:152–153; P3.1:5–6 | Não há resultado de seleção pela emenda. |
| D6 | C5 — catálogo com 28 cursos: 8 N0 adquiridos, 8 N1, 8 conhecidos excluídos, 1 correspondência parcial e 3 não disciplinas; N0 esgotados | confirma | E2:53–62,66; P3:102–103 | Os N1 estão divididos em duas classes. Esgotamento vale para aquele catálogo e classificação; P3 indica outra conta/outros semestres. |
| D6 | Risco — “veredicto de generalização fica sem data” | sem evidência | P3:98–103; P3.1:21–23 | As fontes não fixam calendário. A demora é risco de planejamento, não consequência necessária da opção exploratória. |
| D6 | Resumo — opções e recomendação do coordenador | diverge | P3.1:21–24,181–182; P3:157–161 | Enquadramento correto, mas menu incompleto: exploração e confirmação podem coexistir; aprovar o texto não autoriza executar. |
| D7 | C6 — 8 N0 falham em E3 (1) ou E4 (7); E4 sozinho barra os 4 que passam E2/E3 | confirma | DP:59–60; E2:78–85 | Nos demais, também pode falhar E2; a frase não enumera todas as reprovações. |
| D7 | C7 — 171 links externos entre 461 itens | confirma | E2:66–68 | Total de registros da aquisição; não equivale automaticamente ao denominador de E4. |
| D7 | C8 — `url` fora do alvo, com fundamento operacional de proveniência e aplicação universal | confirma | P3.1:36–50,189 | Exclui também das conclusões; não afirma impossibilidade de congelar ou adjudicar links. |
| D7 | C9 — mudança mais sensível; links associados à reprovação em 7 de 8; efeito não calculado; limiar de 90% preservado | confirma | E3:128–130; P3:144; P3.1:18,78–79 | Confirmação documental da atribuição aos links; efeito líquido da emenda continua desconhecido. |
| D7 | C10 — conclusões não abrangem conteúdo acessado por link | confirma | P3:124–125; P3.1:36–43,163–164 | É redução substantiva do alcance. |
| D7 | C11 — mantendo v2, seleção continua vazia | confirma | E2:87; P3:152–153 | Não é resultado da P3.1. |
| D7 | Resumo — excluir links do alvo; decisão informada pelas contagens exige enquadramento exploratório | confirma | P3.1:14–23,42–50,189 | A justificativa é coerente com o recorte de aquisição; concordância depende do alvo pretendido. |

Minhas recomendações também são formuladas conhecendo as contagens. Os fundamentos abaixo são finalidade do estudo, proveniência e separação entre exploração e confirmação.

**D6 — regra do lote adquirido**

As opções são úteis, mas não formam alternativas mutuamente exclusivas. **Sugestão do planejador:** acrescentar uma via combinada — preservar o resultado v2, analisar o lote como exploratório e preparar separadamente uma confirmação prospectiva. Também cabe aprovar e congelar a redação sem autorizar sua aplicação imediata, distinção expressa na P3.1:24,181–182.

O que cada escolha destrava:

- **Manter v2:** encerra a seleção deste lote sob a regra vigente; não produz avaliação do motor nem veredicto de generalização com essa seleção vazia (E2:87; P3:100–103).
- **Aplicar P3.1 ao lote:** após autorização própria, permite conhecer elegibilidade e cobertura sob o novo recorte. Qualquer avaliação posterior desse lote permanece exploratória; aprovação textual não libera gold, build ou motor (P3.1:21–24).
- **Reservar P3.1 à aquisição prospectiva:** oferece a via confirmatória, desde que o protocolo seja congelado antes de examinar elegibilidade ou resultados da nova aquisição. Não garante atingir os mínimos (P3.1:21–23,150–152).

**Concordância:** concordo com a recomendação exploratória se a finalidade for compreender o comportamento da regra no material adquirido. Para obter evidência confirmatória de generalização, ela precisa ser acompanhada da via prospectiva; não a substitui.

**Risco residual:** congelar a emenda agora impede novas escolhas retrospectivas, mas não elimina o conhecimento que informou sua elaboração. Há ainda uma lacuna documental de vigência: aplicação única e pacote aprovado aparecem na P3:157–161, enquanto a P3.1 exige autorizações próprias e referencia versões posteriores do gerador/pacote (P3.1:64,181–182,191,195). **Sugestão do planejador:** explicitar essa compatibilidade antes de autorizar aplicação; o calendário da confirmação permanece não especificado nas fontes.

**D7 — links, alvo e cobertura**

O menu original da DP distingue manter E4, retirar links do denominador ou alterar o limiar (DP:61–63). A recomendação posterior acrescenta uma escolha substantivamente diferente: **retirar links do alvo e das conclusões**, não apenas da conta de cobertura (P3.1:36–50).

O que cada escolha destrava:

- **Manter v2:** preserva o critério e o resultado registrados, sem destravar seleção neste lote (E2:87).
- **Excluir somente do denominador:** permite outro cálculo de cobertura, mas deixa pendente como representar links que continuariam no alvo. Exige esclarecer o alcance das conclusões.
- **Excluir do alvo conforme P3.1:** alinha a cobertura ao que o protocolo captura sob sua cadeia de proveniência; permite avaliar esse recorte, sem antecipar elegibilidade (P3.1:42–50,78–79).
- **Mudar o limiar:** altera a exigência de cobertura, mas não resolve a ausência de captura dos destinos externos. Exige decisão explícita, com contagens conhecidas (DP:55,61–63; P3.1:42–43).

**Sugestão do planejador:** acrescentar, para estudo prospectivo separado, a possibilidade de manter destinos externos no alvo mediante protocolo próprio de captura e proveniência. A P3.1 não os declara impossíveis de congelar; registra que o protocolo atual não os captura nessa cadeia (P3.1:42–43). A viabilidade dessa alternativa não foi demonstrada pelas fontes.

**Concordância:** concordo com excluir links do alvo se o objeto pretendido for precisamente o recorte operacional descrito na P3.1. A justificativa de proveniência sustenta essa escolha sem depender da quantidade de cursos elegíveis; ela não sustenta conclusões sobre a disciplina inteira.

**Risco residual:** manter o percentual não mantém a mesma medida. Na P3.1, E4 mede ocorrências, enquanto E3 e os mínimos usam documentos distintos; falhas e recusas continuam no denominador de cobertura (P3.1:71–87). Portanto, retirar links não permite inferir o resultado líquido; também permanece provisória a regra de identificação do HTML de páginas, informada inclusive pelo lote conhecido (P3.1:57–64).

**Limitações**

Conferi a sustentação documental nas cinco fontes, sem recalcular contagens nem verificar artefatos subjacentes. Não confirmei causalmente o efeito isolado dos links, o resultado líquido da P3.1, a implementação dos contratos mencionados, aprovações posteriores ou um calendário de aquisição; esses pontos não ficam demonstrados pela leitura autorizada.
````

### job-22 — D8–D9

````text
[texto parcial entregue pelo Alethe no timeout; o log local do Codex só guardou as mensagens iniciais]

Vou conferir somente os cinco documentos, por intervalos de linhas. A resposta começa pela tabela de vereditos; depois apresento minha leitura de D8 e D9, sem decidir por você.DP, E2 e E3 sustentam as contagens citadas e o alcance limitado da busca. D8 e D9 continuam abertas; vou conferir nas propostas como falhas entram na cobertura e quando “sem ocorrência” pode ser declarado.P3.1 separa os critérios: E4 usa ocorrências do alvo, incluindo falhas como não cobertas; E3 exige documentos cobertos distintos. A descrição do coordenador precisa dessa ressalva. Também há uma diferença entre os textos: P3.1 explicita parcial, ambiguidade e conteúdo vazio; P3 não enumera todos esses casos.| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D8 | C1 — 23 arquivos `tipo_inesperado`, num curso, apenas no inventário | confirma | DP:64–66; E2:66–69 | Tratamento relatado para a regra v2; não entram em adjudicáveis nem em fonte local. |
| D8 | C2 — P3 e P3.1 estabelecem toda a lista de não cobertos e a regra dos mesmos bytes | diverge | P3:58–72; P3.1:65–79 | P3.1 confirma integralmente. P3 enumera menos casos e usa unidades; a regra explícita por ocorrência é da P3.1. |
| D8 | C3 — mudança mais severa, efeito não calculado | confirma | P3:146–147 | Avaliação qualitativa da proposta; não é resultado medido no lote. |
| D8 | C4 — `.go` 33 e `.asm` 9 também pesam contra o curso | confirma | P3:14–15, 137–138, 147; P3.1:71–79 | Como não cobertos na cobertura proposta; não há impacto por curso calculado. |
| D8 | **Resumo — falhas no denominador de E3/E4; E4 mais difícil** | diverge | P3.1:78–90; P3:144–147 | Apoio para E4. E3 é mínimo de documentos cobertos, não proporção com denominador de falhas. |
| D9 | C5 — busca limitada ao commit `bf46d51f` e nomes das pastas de download | confirma | DP:67–70; E2:91–92; E3:103–105 | E3 explicita `git grep/log` no commit e leitura dos nomes das pastas. |
| D9 | C6 — 21 candidatos, busca ok; 11 sem ocorrência, 10 com ocorrências; nenhum N1 virou N0 | confirma | E3:105–112 | Confirma o resultado relatado nessa etapa. |
| D9 | C7 — P3.1 define “sem ocorrência” e distingue ausência de fonte e erros | confirma | P3.1:168–177 | Também distingue erro de interpretação e trecho omitido; é norma proposta. |
| D9 | C8 — outras branches, worktrees, memória e conversas não foram buscadas | confirma | E2:91–92; DP:67–68 | Limitação expressamente registrada. |
| D9 | C9 — N0 não comprova independência | confirma | P3:127–129; DP:68–69 | Significa ausência de evidência nas fontes pesquisadas. |
| D9 | C10 — usuário cursou as disciplinas e conhece o conteúdo | confirma | E2:93–94; P3:127–128 | Conhecimento do adjudicador; não equivale, por si, à exposição do motor. |
| D9 | **Resumo — ampliar branches/worktrees e declarar memória/conversas como limite** | confirma | DP:67–70; P3:136; P3.1:168–182 | Diagnóstico confirmado. A ampliação seletiva é sugestão do coordenador, não decisão aprovada nas fontes. |

**D8**

As opções “entram ou não no denominador de E3/E4” precisam ser reformuladas. P3.1 separa dois objetos: **E4 mede cobertura por ocorrência do alvo**, enquanto **E3 exige documentos cobertos distintos**, agrupados por curso e hash. Falhas permanecem no cadastro de cobertura, mas não produzem documentos cobertos para E3; uma aquisição bem-sucedida não apaga outra ocorrência que falhou. (P3.1:54–56, 71–90.)

**Sugestão do planejador:** decidir separadamente a unidade de E4 e a contagem de E3, incluindo a política para ocorrências repetidas. A alternativa já documentada é a separação da P3.1; manter o tratamento v2 é outra escolha, mas preserva a exclusão das falhas da contagem descrita em DP. (DP:64–66; P3.1:78–90.)

O que cada escolha destrava:

- **Manter v2:** fecha a posição sobre D8 preservando o tratamento e o resultado histórico; não cria população elegível. (E2:3–5; DP:64–66.)
- **Adotar a redação P3.1:** define como registrar cobertura e contar documentos numa aplicação futura autorizada. A aprovação do texto, isoladamente, não autoriza aquisição, gold, build nem motor. (P3.1:24, 78–90.)
- **Deixar unidade ou tratamento pendentes:** mantém D8 aberta; DP impede assinar o pré-registro enquanto houver item aberto. (DP:3–4.)

**Concordo com incluir falhas de ocorrências do alvo em E4**, porque o universo deve ser definido antes de conhecer o sucesso do download, preservando o que a cobertura pretende medir. **Discordo da formulação conjunta “denominador de E3/E4”**, pois ela apaga a distinção estabelecida pela P3.1. (P3.1:33–34, 78–90.)

O risco residual não é apenas “E4 fica mais difícil”: o resultado mistura disponibilidade da aquisição, proveniência e admissibilidade pelo cegamento. Além disso, o efeito líquido da proposta permanece desconhecido, porque outras mudanças também alteram o alvo e a unidade; não cabe inferir quais cursos passariam. (P3.1:65–79; P3:144–147.)

**D9**

As alternativas principais estão presentes — ampliar a busca ou manter seu alcance com limitação explícita —, mas falta especificar operacionalmente a ampliação. A solução intermediária do coordenador é possível; entretanto, “todas as branches e worktrees por `git grep`” não demonstra, nessas fontes, cobertura de arquivos não versionados ou de revisões históricas. O próprio relatório declara sua pasta nova e não versionada. (DP:67–70; E3:162–164.)

**Sugestão do planejador:** congelar antes da busca quais branches, revisões, worktrees e arquivos locais integram o escopo, incluindo o tratamento dos não versionados. Memória e conversas podem permanecer explicitamente fora; uma fonte **requisitada**, porém ausente ou com saída incompleta, não pode ser convertida em “zero matches”. (P3.1:168–177.)

O que cada escolha destrava:

- **Manter o alcance atual:** permite fechar D9 com uma conclusão restrita às fontes efetivamente pesquisadas; não comprova independência. (DP:68–70; E2:91–92.)
- **Ampliar fontes locais:** permite produzir evidência adicional antes do Gate e reexaminar possíveis exposições. Encontrar uma menção não determina automaticamente uso ou nível; a categoria do arquivo também não determina isso. (P3.1:176–180.)
- **Requisitar memória/conversas sem conseguir examiná-las:** impede declarar “sem ocorrência” para esse escopo ampliado. A alternativa é reduzir explicitamente o alcance da conclusão. (P3.1:168–175.)

**Concordo com uma ampliação local delimitada**, pela maior abrangência documental, sem justificá-la por reclassificar qualquer curso. **Concordo apenas parcialmente com o mecanismo sugerido:** ele precisa demonstrar cobertura do escopo declarado, inclusive dos arquivos não versionados escolhidos, antes de sustentar “sem ocorrência”. (E3:162–164; P3

[corte do timeout]
````

### job-23 — R-VIS + R-CC

````text
[2026-09-30T19:09:56.739Z]
Vou conferir as afirmações somente nos quatro arquivos permitidos, com referências de linha. A tabela virá antes do aprofundamento; não executarei testes nem alterarei arquivos.

---MSG---

[2026-09-30T19:11:26.955Z]
Cwd, branch e HEAD conferem com o brief: `GPT-Tutor-Generator`, `feat/motor-atribuicao`, `bf46d51f`. A leitura dos trechos está em andamento.

---MSG---

[2026-09-30T19:13:35.871Z]
As fontes confirmam que R-VIS continua pendente e R-CC é só proposta. Há ressalvas na síntese: “só pela assinatura” simplifica os casos de PDF e notebook; a exclusão por conflito exige ocorrências em unidades diferentes; a sensibilidade cobre A_novo e C_novo, mas não B_novo.

---MSG---

[2026-09-30T19:17:25.456Z]
| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| R-VIS | C1 — opções gerais e detalhamento por formato | confirma | ISS:171–177; REL:209–221 | Opções reproduzidas corretamente; “outra política” permanece aberta. |
| R-VIS | C2 — não aprovada, não implementada, pacote não liberado | confirma | ISS:139,170; REL:279–282 | Refere-se a R-VIS; outras correções foram implementadas. |
| R-VIS | C3 — “sem OCR” não autorizou pixels não examinados | confirma | ISS:141–142; REL:169–171 | Aceitação do risco continua pendente. |
| R-VIS | C4 — proveniência não garante conteúdo permitido | confirma | ISS:153–164 | Integridade, proveniência e inspeção são dimensões distintas. |
| R-VIS | C5 — todos os casos listados aceitos “só pela assinatura” | diverge | REL:194–205 | Lista confirmada, generalização excessiva: PDF tem leitura de Info; notebook tem varredura textual. As estruturas apontadas permanecem sem inspeção suficiente. |
| R-VIS | C6 — impactos das opções e da recusa vigente não calculados | confirma | REL:172–173,224–226 | Não há estimativa quantitativa autorizada do efeito no lote. |
| R-VIS | C7 — arquivos afetados e critérios de aceite listados | confirma | ISS:322,329–339 | Existem; a redação dos controles aceitos precisa esclarecimento. |
| R-VIS | Recomendação — OLE/MP4 recusados, b2, varrer XMP/base64; risco visual expresso | confirma | REL:214–223; ISS:168–169 | É a recomendação do REL. “Quase todos” é apreciação qualitativa, sem impacto calculado. O risco inclui vetores. |
| **R-VIS** | **Resumo documental** | **confirma** | ISS:139–175; REL:281,353 | **Decisão pendente; recomendação disponível, sem liberação operacional.** |
| R-CC | C8 — não existe regra de status aprovada para conflito | confirma | ISS:264–275; P3.1:96–98 | Hash registrado não equivale a aprovação. |
| R-CC | C9 — proposta documental, sem gold nem adjudicação | confirma | ISS:369; REL:282 | Estado declarado expressamente. |
| R-CC | C10 — conteúdo, múltiplos ids, `?`, exclusão por unidade indeterminável | diverge | ISS:279–293 | Síntese incompleta: exclusão exige também ocorrências em seções de unidades diferentes. |
| R-CC | C11 — aprovação nas duas contas, sem mudar limiar | confirma | ISS:304–311 | Sensibilidade de A_novo e C_novo; B_novo não recebe essa conta. Inclui `?` nos eixos de subunidade. |
| R-CC | C12 — versões novas, sem editar gold-externo-1; documentos somente | confirma | ISS:315–316,325 | Arquivos novos ainda propostos; nenhum gold produzido. |
| R-CC | C13 — quantidade de documentos em conflito não medida | confirma | P3.1:5–6,123–124 | Confirmação documental: nenhuma contagem calculada sob a proposta. |
| R-CC | C14 — adjudicador único | confirma | PRE:86,170 | É o usuário; concordância entre avaliadores não é medida. |
| R-CC | Recomendação — aprovar; riscos de adjudicador único e redução dos denominadores por `?` | sem evidência | PRE:86; ISS:285–288; REL:354 | Riscos confirmados; “aprovar” é juízo do coordenador, não recomendação expressa dessas fontes. |
| **R-CC** | **Resumo documental** | **confirma** | ISS:277–316; P3.1:96–124 | **Proposta coerente em seus casos definidos, com exclusões e sensibilidade explícitas; aprovação pendente.** |

**R-VIS**

As opções estão completas como menu geral, mas ainda não como contrato operacional inequívoco. Há uma inconsistência documental: REL:218 fala em pixels “como já foi aceito” para PDF em imagem, enquanto ISS:141–142 e REL:169–171 corrigem precisamente essa alegação e mantêm a aceitação pendente.

**Sugestão do planejador:** antes da decisão, explicitar o tratamento dos vetores e o significado de “inspeção suficiente” — a recusa conservadora não implica necessariamente recusar qualquer PDF (ISS:155–168). Alinhar também EXIF, previsto nos testes mas ausente da enumeração da b2, e esclarecer que os “mesmos arquivos limpos” aceitos não incluem OLE/MP4 recusados pelo formato (REL:216–218; ISS:332,336–339).

O que cada escolha destrava:

- **Recusa conservadora:** permite especificar uma implementação que recuse conteúdo insuficientemente examinável. As recusas continuam no denominador de cobertura; podem impedir elegibilidade, inclusive quando atingem o plano, sem impacto atualmente calculado (P3.1:65–79,140–142).
- **b2 com varredura de XMP/base64:** permite especificar a admissão de conteúdo visual com inspeção textual e aceitação expressa do risco restante. Exige mudança do contrato, implementação e verificação; a decisão isolada não libera o pacote (ISS:168–174,322,329–339,354–359).
- **Outra política ou aceitação de XMP/base64 como limitação:** exige definir previamente o alcance da inspeção e os riscos aceitos; não é uma exceção automática para recuperar cobertura (REL:220; ISS:136–137,175).

**Minha leitura:** concordo com a recomendação do REL como proposta, condicionada aos esclarecimentos acima e à aceitação expressa de pixels **e vetores**. A justificativa deve ser a escolha consciente do alcance da inspeção, não a alegação não medida de que b1 inviabilizaria quase todo o lote.

**Risco residual:** estruturas textuais examinadas permitem verificar assinaturas conhecidas, não demonstrar ausência de conteúdo proibido em pixels, vetores ou outras estruturas. Proveniência confirmada não elimina esse risco (ISS:153–169).

**R-CC**

A proposta distingue corretamente conteúdo que sustenta vários rótulos de conteúdo que não permite determinar um rótulo. O marcador `?` não deve substituir vários tópicos sustentados pelo conteúdo; a exclusão contextual tem a condição adicional omitida pelo coordenador (ISS:279–293).

**Sugestão do planejador:** além de aprovar a redação, explicitar as alternativas de devolver para ajuste ou adiar mantendo o bloqueio. Para ajuste, esclarecer o encaminhamento da unidade indeterminável sem ocorrências em unidades diferentes e fazer P3.1 mencionar expressamente a sensibilidade de `?`, já detalhada em ISS:305–306; não estender automaticamente `conflito_contextual:` a casos que a regra não cobre.

O que cada escolha destrava:

- **Aprovar a proposta:** resolve essa pendência normativa e permite encaminhar os novos documentos de schema/instruções. Não autoriza adjudicação, produção de gold ou execução; essas fases têm autorização própria (ISS:315–325,358–359; P3.1:24,181–182).
- **Ajustar antes de aprovar:** fecha os casos e harmoniza os documentos antes do congelamento, preservando o gold-externo-1.
- **Adiar:** mantém R-CC pendente; não torna válida a antiga expressão “regra já congelada” (ISS:264–275).

**Minha leitura:** concordo com a direção da proposta, mas recomendo ajustar essas lacunas antes da aprovação documental. O congelamento anterior às predições e a consequência previamente fixada da sensibilidade reduzem graus de liberdade; não resolvem a incerteza do julgamento por um único adjudicador (ISS:304–316; PRE:86).

**Risco residual:** `?` reduz os denominadores de subunidade; `excluido` sai também dos mínimos pós-gold, mas permanece na cobertura e na estabilidade de bloco (ISS:285–301). B_novo continua sem sensibilidade para perdas em documentos sem rótulo determinável (ISS:310–311).

**Inferência:** se os mesmos conflitos forem acrescentados como erros a todos os braços, a ordenação comparativa de A_novo permanece; a pressão dessa sensibilidade recai sobre o limiar de C_novo. Portanto, exigir ambas as contas não substitui uma verificação de perdas que depende de gold (ISS:305–311; PRE:146–153).

**Limitações**

Cwd, branch e HEAD conferidos. A análise usou somente os quatro arquivos autorizados, incluindo ISS:369, explicitamente citado no brief. Não conferi código, implementação efetiva, artefatos, contagens do lote ou julgamentos reais; os estados e impactos são declarações documentais. Nenhum teste ou experimento foi executado.

---MSG---

[2026-09-30T19:17:51.741Z]
Conferência documental concluída; tabela de vereditos e aprofundamento já entregues.

Ficou sem conferir: implementação real, artefatos e impacto quantitativo das escolhas no lote — fora do escopo autorizado. Nenhuma leitura adicional, alteração, teste ou experimento foi feito.
````

### job-24 — Gate 2 do delta

````text
[2026-09-30T19:09:56.336Z]
Vou conferir apenas as cinco fontes e os diffs permitidos, sem executar testes. Publicarei primeiro a tabela de vereditos; depois, a leitura das opções e dos limites da decisão.

---MSG---

[2026-09-30T19:11:31.386Z]
O diff está restrito a MOO e TST. O transporte dos testes novos não inclui `Transfer-Encoding`; vou confrontar essa lacuna com os achados e os limites documentados do Gate 2.

---MSG---

[2026-09-30T19:14:22.939Z]
| afirmação | veredito | arquivo:linha | nota curta |
|---|---|---|---|
| C1 | confirma | REV:3,12–13,42–67 | `job-16`, papel reviewer: NÃO APROVAR, dois MAJOR. |
| C2 | confirma | REV:132–144; MOO:440–465,475 | Reproduções registradas: subcontagem dos parciais e uso indevido de Content-Length em chunked. |
| C3 | confirma | REV:151–154 | A condição dos cenários reproduzidos é cabeçalho conflitante; frequência real não medida. A qualificação HTTP consta do relatório. |
| C4 | confirma, com ressalva | TST:556–567,621–628,653–678; REL:331,335–339; REV:155–156 | Testes novos não geram chunked; resultados históricos conferem documentalmente. Ausência de cobertura na suíte inteira não foi inspecionada. |
| C5 | confirma | REL:292,299–300; REV:139–142,157–159 | Compatibilidade sem limite e contagem de resposta incompleta têm contraexemplos registrados. |
| C6 | confirma | REL:443–453 | Proposta inclui apenas MOO e TST; tracker excluído expressamente. |
| C7 | sem evidência integral | REL:281,466–468; ISS:352–359 | R-VIS e aprovações separadas estão documentadas; “Gate de rede” e ausência de qualquer dependência imediata não estão demonstrados nos trechos permitidos. |
| C8 | confirma como inferência | MOO:436–465; REV:52–53,66–67 | Lógica concentrada em `_le_resposta`; tamanho e suficiência da correção ainda não medidos. |
| Decisão | confirma a recomendação técnica | REV:163–166; ISS:340–345,356–359 | Corrigir antes de reconsiderar Gate 2 é sustentado pelas fontes; a decisão permanece com o usuário. |

Vou aprofundar a causalidade no MOO e distinguir o que cada opção permite fazer do que continua dependendo de aprovação.

---MSG---

[2026-09-30T19:18:17.922Z]
| afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|
| C1 — parecer independente | confirma | REV:3,12–13,42–67 | `job-16`, papel reviewer: **NÃO APROVAR**, com dois MAJOR. |
| C2 — reproduções do coordenador | confirma | REV:132–144; MOO:440–465,475 | Registrados os parciais **0/3 e 2/5**, a exceção sem limite e a aceitação de `[]` extraído de `[]xxx`. |
| C3 — condição e frequência do segundo achado | confirma | REV:151–154 | Os cenários reproduzidos combinam chunked e Content-Length. Frequência real não medida; a qualificação “fora do protocolo” consta da fonte, sem conferência normativa externa nesta tarefa. |
| C4 — testes e ausência de cobertura | sem evidência | TST:556–567,621–628,653–678; REL:331,335–339; REV:155–156 | **Confirma parcialmente:** testes novos não geram chunked; constam 54/54 e suíte com 2458 passando, uma falha preexistente e quatro pulados. A ausência de cobertura na **suíte inteira** não foi demonstrada pelas fontes permitidas. |
| C5 — relatório promete além do comportamento | confirma | REL:292,299–300; REV:139–142,157–159 | Há contraexemplos documentados à compatibilidade sem limite e à contagem de respostas incompletas. |
| C6 — escopo do commit | confirma | REL:443–453 | Somente MOO e TST; tracker expressamente excluído. |
| C7 — nenhuma dependência imediata; Gate de rede e R-VIS | sem evidência | REL:281,466–468; ISS:352–359 | **Confirma parcialmente:** R-VIS pendente, pacote não liberado e aprovações distintas. Os trechos não explicitam o Gate de rede nem demonstram ausência de qualquer dependência imediata do commit. |
| C8 — correção pequena e localizada | confirma | MOO:436–465; REV:52–53,66–67 | Sustenta-se **como inferência** sobre a lógica em `_le_resposta`; tamanho e suficiência da correção ainda não foram medidos. |
| Resumo da decisão — recomendação de corrigir antes | confirma | REV:163–166; ISS:340–345,356–359 | Recomendação tecnicamente sustentada. O parecer é desfavorável ao delta atual; a decisão de Gate 2 continua com o usuário. |

**A causalidade de C2 está identificada no MOO.** No truncamento, `r.read(pedir)` pode levantar a exceção em MOO:451. O tratamento preserva e soma apenas `exc.partial` e reconstrói a exceção em MOO:452–455; não incorpora o parcial interno descrito em REV:46–50. Isso explica tanto a subcontagem quanto a perda em `ultimo_corpo` e na exceção devolvida.

No conflito de cabeçalhos, MOO:440–441 considera Content-Length sem distinguir chunked. Sem limite, a comparação em MOO:461–462 produz `IncompleteRead` mesmo depois do término válido do transporte registrado em REV:141. Com limite, MOO:447–449 encerra a leitura no saldo; como `esperado` está definido, a recusa conservadora de MOO:463–464 não ocorre. O fragmento retorna em MOO:465 e é decodificado como JSON em MOO:475 — daí a aceitação documentada de `[]` em REV:142.

**C8 sustenta localização, não uma estimativa de esforço.** A correção precisaria tocar o tratamento do parcial em MOO:452–455, preservando payload sem duplicação nem framing, e a interpretação do comprimento/completude em MOO:440–464. Também exigiria regressões em TST com transporte chunked, incluindo os casos registrados em REV:139–144, e renovação das evidências documentais.

Existe uma escolha de contrato: seguir a interpretação chunked sem usar Content-Length como prova de término ou recusar explicitamente cabeçalhos conflitantes, alternativas propostas em REV:66–67. **Recusar o conflito não restaura o comportamento anterior daquele caso**; essa escolha precisaria aparecer no aceite, em vez de manter irrestrita a promessa de compatibilidade de ISS:344–345.

As opções cobrem os caminhos principais, mas falta distinguir **adiar** de **abandonar**:

1. **Commitar como está:** registra o delta atual, mediante decisão explícita de Gate 2. Mantém os achados e o parecer desfavorável; não libera aquisição ou uso real (REV:163–164; ISS:356–359; REL:281).

2. **Corrigir antes:** permite produzir novas evidências, obter a revisão autorizada do delta corrigido e então reconsiderar Gate 2. É o caminho que busca satisfazer o contrato de contagem e compatibilidade; requer Gate 1 próprio e nova autorização de revisão (REV:165–166; ISS:190–200,340–345).

3. **Commitar com limitações e issue:** registra o delta e torna o desvio explícito. Documentar os achados não corrige a subcontagem nem satisfaz, por si, os aceites; seria aceitação consciente dessas limitações (MOO:452–455; ISS:340–345).

4. **Não commitar por enquanto:** mantém a decisão pendente. **Não retira o delta da execução local:** `_call` continua passando pela implementação modificada em MOO:475.

5. **Sugestão do planejador — abandonar formalmente o delta e autorizar sua retirada:** encerra esta proposta de alteração do produto, em vez de apenas adiá-la. Exige reconciliar o uso do `adquire` v5, que depende do contador e do limite do cliente, além das afirmações documentais; não libera uso real (REL:305–309,281).

**Concordo com a recomendação de corrigir antes:** a subcontagem contradiz diretamente o contrato documentado, e registrar uma limitação não recupera os bytes perdidos. A condição de cabeçalhos conflitantes delimita o segundo achado, mas não elimina o primeiro nem fornece revisão favorável ao delta atual.

O risco residual é precisar de nova rodada caso a correção não preserve corretamente parciais, orçamento e completude; seu esforço ainda não foi medido. Mesmo com o delta corrigido e posteriormente commitado, permanecem as decisões separadas sobre R-VIS, aprovação metodológica e R-PAGE provisória (REL:466–468).

**Limitações:** conferi documentos, intervalos de código e os diffs permitidos; não executei testes nem novas reproduções. Os resultados históricos e a reprodução do coordenador foram confirmados como registros das fontes, não como medições próprias; não inspecionei a suíte inteira, não medi frequência real, não consultei norma HTTP nem o dossiê completo, e não revalidei HEAD ou SHA-256 — o diff corresponde aos arquivos e blobs documentados em REL:447–450.
````

## Rodada 2 (30/09 ~23:57 → 01/10 ~00:00)

O usuário passou a coordenação para esta sessão e autorizou uma nova rodada das quatro partes que tinham estourado o
tempo. Uma chamada `alethe_delegate`, papel `planner-t2`, label "NOITE-3009 B1 partes (rodada 2)", `run-13`. Os specs
são **idênticos** aos da rodada 1 (sha256 conferido no `orchestrator-jobs.json` do Alethe).

Build novo do Alethe, conferido no log de cada sessão Codex:

- o orçamento entra antes do spec: "[Alethe] Time budget: 600 s from now. Write your answer by 420 s; anything not
  written when the budget ends is lost." (ausente na rodada 1);
- `effort = medium`, `sandbox = read-only`, `gpt-6.1-sol`;
- menções a plugins no log caíram: ponytail 17 → 2, claude-mem 14 → 6, `ecc:` 62 → 14 (job-19 × job-25). As que restam
  vêm provavelmente das instruções do projeto. É indício, não prova, de que os plugins saíram.

### Tempos e resultados

| parte | rodada 1 | rodada 2 | antes dos 600 s? | tokens totais (r1 → r2) | saída (r1 → r2) |
|---|---|---|:---:|---|---|
| D1–D3 | `job-19`: timeout, 600,1 s | **`job-25`: succeeded, 177,6 s** | sim (30 %) | 373.922 → 150.038 | 6.352 → 3.699 |
| D6–D7 | `job-21`: timeout, 601,1 s | **`job-26`: succeeded, 165,4 s** | sim (28 %) | 296.523 → 271.739 | 6.486 → 3.180 |
| D8–D9 | `job-22`: timeout, 600,4 s, cortado | **`job-27`: succeeded, 167,1 s** | sim (28 %) | 390.894 → 193.495 | 2.460 → 3.335 |
| Gate 2 do delta | `job-24`: timeout, 601,1 s | **`job-28`: succeeded, 168,5 s** | sim (28 %) | 381.358 → 239.546 | 6.723 → 3.174 |

- `plannerId` `7jEdcaIHSHoGGPv_soJta`. `threadId`: `job-25` `01a0f564-8e69-7961-811a-2fff46dfb841`; `job-26`
  `01a0f564-8e69-7740-b76e-236740295415`; `job-27` `01a0f564-8e69-7343-b72b-f93aba0f3841`; `job-28`
  `01a0f564-8e69-7801-b804-15b46fd30022`.
- `askedToWrapUp` não aparece no status da rodada 2. Os quatro terminaram com 28–30 % do teto, antes do aviso dos
  80 %.
- Leitura: com o mesmo spec, o tempo caiu de ~600 s para ~170 s, e a saída ficou com cerca de metade do tamanho
  (menos repetição de tabela). A mudança simultânea de effort (padrão → medium), do prefixo de orçamento e dos plugins
  não permite atribuir o ganho a um fator só.

### Comparação dos vereditos

| parte | rodada 1 | rodada 2 | diferença |
|---|---|---|---|
| D1–D3 | C1–C10 confirmam; C11 sem evidência; recomendações confirmadas | igual | só nuances novas (abaixo) |
| D6–D7 | C1–C11 confirmam; risco "sem data" sem evidência; menu da D6 "diverge" (incompleto); P3:5 × P3:135 | igual na substância; o menu da D6 aparece como "confirma, mas as opções podem ser combinadas" | rótulo diferente, mesma conclusão (rota combinada) |
| D8–D9 | C2 diverge; recomendação da D8 diverge (E3/E4); D9 confirmada; **limitações perdidas** | C2 diverge; recomendação da D8 confirma **com** a separação E3/E4; recomendação da D9 "sem evidência" (é sugestão do coordenador); **limitações entregues** | mesma conclusão; texto completo |
| Gate 2 do delta | C4 e C7 sem evidência (depois resolvidas pelo coordenador); demais confirmam; recomendação confirmada | igual | sugestão nova: corrigir por etapas |

**Nenhum veredito se inverteu.** Itens novos:

- **D1 (`job-25`):** explicitar o que significa o C_novo global quando parte dos cursos só é descritiva. A P3.1 manda
  informar quantos atingiram o mínimo, mas não reescreve PRE:153.
- **D3 (`job-25`):** se o objetivo fosse a colocação contextual por ocorrência, seria outro desenho (gold por
  ocorrência), não a replicação da opção C. Sugestão do planejador, fora do escopo atual.
- **D8 (`job-27`):** formatos fora da allowlist pesam na cobertura (E4) e em E3, não na acurácia do motor. Resolver D8
  não autoriza aplicação. **Incorporado à B1.**
- **D9 (`job-27`):** o nome da ferramenta não é contrato de cobertura. Ampliar a busca não converte ocorrência em
  exposição nem muda N1/N0. Familiaridade do adjudicador ≠ exposição do motor. Resolver D9 fecha só a D9.
  **Incorporado à B1.**
- **Gate 2 (`job-28`):** sugestão do planejador de fazer a correção por etapas: primeiro a subcontagem, depois a
  política para cabeçalhos conflitantes, mantendo o commit pendente. Um commit parcial exigiria escopo e aceite
  próprios. Registrado aqui; a B1 não mudou nesse ponto.

### O que mudou na B1

Só na D8 e na D9 (linhas "Rodada 2" no dossiê), conforme pedido. As demais partes confirmaram a rodada 1, e as
nuances novas ficam registradas aqui.

### Anexo da rodada 2 — textos dos workers

Mensagens do assistente, recuperadas do log local de cada sessão Codex.

#### job-25 — D1–D3

````text
Vou conferir C1–C11 nas cinco fontes e escrever a tabela antes do aprofundamento. A classificação da rota exige uma leitura adicional por instrução superior; a análise documental ficará restrita aos arquivos permitidos.


Rota: verificação documental pelo agente ativo, sem delegação. DP suspende D1–D3, e PRE continua não assinado; portanto, vou distinguir regra proposta de regra aprovada.


C1–C9 têm apoio documental, com ressalvas de status e escopo. C10 cita o efeito da deduplicação em E3/E4; não calcula o efeito da consistência no build. P3.1 também restringe a análise do lote conhecido a exploratória/descritiva e acrescenta uma regra ainda não aprovada para conflito contextual.


| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D1 | C1 — mínimos totais, sem mínimo por curso | confirma | PRE:31–33; DP:12–13; DP:3–4 | Descreve o texto proposto; não uma regra aprovada. D1 está suspensa. |
| D1 | C2 — propostas escolhem B com 10; curso pequeno permanece no agregado e no veto | confirma | P3:94–96; P3.1:145–149 | P3.1 restringe o caráter descritivo a C_novo e explicita que os 3 cursos são exigência apenas pré-gold. |
| D1 | C3 — precisão sem cálculo; efeito do mínimo por curso indisponível antes do gold | confirma | DP:19; P3:148 | Nenhuma justificativa estatística calculada foi apresentada. |
| D1 | **Resumo — recomendar B com 10, reconhecendo convenção e contaminação** | confirma | P3.1:14–23; P3.1:145–149 | Há apoio documental para essa leitura, sem garantia de precisão nem autorização para aplicá-la. |
| D2 | C4 — PRE já descreve dois eixos e invariância de bloco por ID | confirma | PRE:48–52; PRE:149–151 | Corresponde à opção A de DP. |
| D2 | C5 — propostas mantêm A; sanidade anterior à comparação; falha deixa B_novo não avaliado | confirma | P3:107–113; P3.1:128–134 | P3.1 exige correspondência dos IDs e proíbe resolver o vínculo depois de ver predições. |
| D2 | C6 — acurácia nos cursos novos não medida; exige gold temporal independente | confirma | P3.1:135–136; P3:111–113 | Estabilidade entre braços não demonstra acerto. |
| D2 | **Resumo — recomendar A; limitar afirmações sobre acurácia** | confirma | P3.1:128–136; PRE:177 | Confirma a limitação nos cursos novos. As fontes não permitem afirmar que a acurácia foi demonstrada nos cursos de desenvolvimento. |
| D3 | C7 — replicação `material@eid` infla o denominador, segundo a revisão | confirma | DP:33–35; PRE:66–68 | Confirma como registro documental; código e demonstração original não foram examinados. |
| D3 | C8 — duplicatas: 9 pares em 3 cursos | confirma | P3:14–15; E3:94–97 | P3 informa ambos os números; E3 confirma os pares e registra ausência de duplicata entre cursos. |
| D3 | C9 — documento por `(curso, sha256)`; uma linha; todas as entries; ausência é erro | confirma | P3:40–54; P3.1:83–95; P3.1:125–127 | Em P3.1, documento reúne ocorrências **cobertas**; o acerto é exigido por eixo. Conflito contextual tem tratamento adicional. |
| D3 | C10 — efeito no lote não calculado | confirma | P3:3–4; P3:145; P3:149 | A linha 145 trata da unidade de E3/E4. Para consistência no build, a linha 149 registra ausência de build; não quantifica efeito no placar. |
| D3 | C11 — implementar B exige mudar o avaliador genérico e reescrever PRE §4.4 | sem evidência | PRE:66–68; PRE:134–135; P3:52–54 | Reescrever §4.4 decorre da incompatibilidade textual. É necessário adequar a avaliação, mas as fontes não provam qual componente precisa ser alterado. |
| D3 | **Resumo — recomendar B; um erro de duplicata compromete o material** | confirma | DP:40; P3.1:125–127 | A severidade é intencional e, em P3.1, vale por eixo. A recomendação depende de fechar também conflito contextual e vínculos. |

1. **D1 — concordo com B como convenção operacional, condicionalmente.** O valor 10 reaproveita E3, mas isso não demonstra precisão suficiente para C_novo; a própria P3.1 declara ausência dessa garantia (P3:96; P3.1:19).

   As opções de DP cobrem três orientações úteis, mas não são exaustivas: mínimo agregado, mínimo por curso e precisão são dimensões combináveis. **Sugestão do planejador:** explicitar o significado do C_novo global quando parte dos cursos recebe apenas descrição, identificando quais cursos sustentam o veredicto; P3.1 exige informar quantos atingiram o mínimo, mas não reescreve integralmente a regra global de PRE (P3.1:145–149; PRE:153).

   **Destrava:** o fechamento dos critérios de PRE §2 e §11 para revisão/Gate 1, depois o congelamento dos denominadores e a avaliação em §7. Não libera isoladamente adjudicação ou execução (PRE:102–115; P3.1:24).

   **Risco residual:** um corte operacional continua separando cursos com tamanhos próximos sem garantia estatística. Além disso, o lote conhecido só admite análise exploratória/descritiva sob a emenda; avaliação confirmatória exige aquisição prospectiva com protocolo previamente congelado (P3.1:19–23).

2. **D2 — concordo com A para esta validação.** Ela responde se o vocabulário preserva o bloco entre braços, enquanto acurácia temporal exige outro gold e protocolo; juntar essas perguntas agora ampliaria o estudo (P3:107–113; P3.1:128–136).

   DP oferece alternativas pertinentes, mas C apresenta um problema explícito de cegamento, e B exige uma regra temporal previamente fixada (DP:28–29). **Sugestão do planejador:** manter estabilidade nesta validação e reservar acurácia temporal para estudo independente, podendo exigir ambas em uma decisão futura; essa combinação não precisa modificar o protocolo atual.

   **Destrava:** definir o conteúdo do pacote de adjudicação sem rótulos de bloco e fechar a sanidade/comparação necessárias a B_novo na sequência de captura e avaliação (PRE:50–52; PRE:103–115; P3.1:128–136).

   **Risco residual:** CRU e VOCAB podem preservar o mesmo bloco errado. A falha de IDs produz “não avaliado”, e a estabilidade não autoriza extrapolar acurácia dos cursos novos nem pressupor comprovação nos cursos anteriores (P3.1:131–136; PRE:177).

3. **D3 — concordo com B para avaliar consistência por documento.** Ela evita escolher uma entry conveniente ou contar repetidamente o mesmo julgamento; sua severidade é coerente com exigir que todas as entries vinculadas satisfaçam a régua de cada eixo (P3:50–54; P3.1:125–127).

   As opções não esgotam objetivos possíveis. **Sugestão do planejador:** se o objetivo fosse avaliar colocação contextual por ocorrência, considerar gold independente por ocorrência, com dependência entre ocorrências explicitada; isso seria outro desenho, não a replicação de uma única linha prevista em C.

   A lacuna mais importante já aparece na própria P3.1: bytes iguais em seções diferentes podem gerar conflito contextual. Ela propõe regras de múltiplos rótulos, subunidade indeterminada ou exclusão, com análise de sensibilidade para A_novo/C_novo; exige `gold-externo-2` e instruções novas, ainda não aprovadas (P3.1:96–124).

   **Destrava:** primeiro fechar cadastro, schema e instruções antes da entrega ao adjudicador; depois substituir a replicação de PRE §4.4 pela ligação e avaliação por documento no congelamento da rodada (PRE:103–108; P3.1:83–95; P3.1:120–127).

   **Risco residual:** o julgamento único precisa representar adequadamente contextos legítimos diferentes. Exclusões por conflito reduzem os denominadores pós-gold e não têm análise de sensibilidade em B_novo; além disso, a comparação depende de vínculos e IDs íntegros (P3.1:110–118; P3.1:131–133).

**Limitações:** conferência documental, sem testes ou reprodução. Não examinei código, demonstração original da revisão, avaliador, schema real ou artefatos do lote; portanto, C7 é confirmação do relato e C11 permanece parcialmente sustentada. Cwd/branch/HEAD foram recebidos do brief, não verificados. Além da leitura obrigatória de roteamento, nenhuma fonte externa às cinco permitidas foi usada na análise.

Resolver D1–D3 não fecha sozinho o Gate 1: DP mantém outras decisões abertas, e aprovar P3.1 não autoriza aquisição, gold, build ou motor (DP:49–70; P3.1:24).
````

#### job-26 — D6–D7

````text
Vou conferir as afirmações por linhas nas cinco fontes e entregar primeiro a tabela, depois minha leitura de D6 e D7. Há uma exigência superior de consultar a rota antes de agir; essa será a única leitura fora da lista e não servirá de evidência documental.


As fontes sustentam os números e o enquadramento exploratório. Duas ressalvas: P3 se contradiz sobre D6 entre a abertura e §12; P3.1 distingue excluir links do alvo de apenas retirá-los do denominador e diz que sua aprovação não autoriza execução.


| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D6 | C1 — DP mantém a regra v2 e exige decisão explícita para ajustar limiares | confirma | DP:54–55 | A decisão deve registrar conhecimento das contagens. |
| D6 | C2 — P3 substitui D6 pela vigência; aplicação única; P3.1 restringe o lote conhecido a análise exploratória | confirma | P3:135,155–161; P3.1:21–24 | Há contradição editorial: P3:5 ainda diz que D6 fica fora. Aprovação normativa não autoriza execução. |
| D6 | C3 — Nenhum curso elegível pela v2 | confirma | E2:76–87 | Resultado registrado, sem recálculo nesta verificação. |
| D6 | C4 — Resultado sob P3/P3.1 deliberadamente não calculado | confirma | P3:152–153; P3.1:5–6 | Ausência de cálculo não demonstra população suficiente. |
| D6 | C5 — Catálogo esgotou N0; nova aquisição pode buscar outra conta/semestres | confirma | E2:53–68; P3:100–103 | Os 28 são 8 N0 + 6 N1 + 2 N1 de piloto + 8 conhecidos + 1 correspondência parcial + 3 não disciplinas. “Não sobra N0” vale para esse catálogo e essa classificação. |
| D6 | Opções — v2; P3.1 exploratória no lote; P3.1 prospectiva | confirma | DP:54–55; P3:157–161; P3.1:20–24 | São caminhos compatíveis com os textos, mas podem ser combinados e exigem autorizações distintas. |
| D6 | Risco — recomendação deixa a generalização “sem data” | sem evidência | P3.1:21–24; P3:100–103 | As fontes exigem aquisição prospectiva; não apresentam calendário. Não sustentam que a opção exploratória, por si, cause o atraso. |
| D6 | **Síntese — recomendação exploratória é documentalmente admissível** | confirma | P3.1:21–24,181–182 | Admissível como caminho condicionado; não produz avaliação confirmatória nem libera fases seguintes. |
| D7 | C6 — Lote falha em E3 ou E4; E4 sozinho barra quem passa E2/E3 | confirma | DP:59–60; E2:78–85 | Há 1 falha em E3 e 7 em E4; entre estas últimas, 4 passam E2/E3. Alguns cursos também falham E2. |
| D7 | C7 — 171 dos 461 itens são links externos | confirma | E2:66–68 | Contagem do inventário relatada em E2. |
| D7 | C8 — P3.1 exclui `url` do alvo por proveniência, universalmente | confirma | P3.1:36–50,189 | Não afirma impossibilidade de congelar/adjudicar links; delimita o protocolo de aquisição. |
| D7 | C9 — Exclusão dos links é a mudança mais sensível; efeito não calculado; E4 permanece 90% | confirma | E3:128–130; P3:144; P3.1:18,78–79 | A atribuição aos links é afirmada pelos documentos; não foi isolada experimentalmente nesta tarefa. |
| D7 | C10 — Conclusões excluem conteúdo acessado por link | confirma | P3:124–125; P3.1:36–43,154–164 | Restrição explícita do alcance. |
| D7 | C11 — Mantida a v2, seleção continua vazia | confirma | E2:87; P3:152–153 | Resultado pertence à v2; não deve ser substituído pelo resultado de outra regra. |
| D7 | **Síntese — excluir links na redação P3.1; lote conhecido exploratório** | confirma | P3.1:14–24,36–50 | A fundamentação operacional é coerente; permanece uma escolha feita conhecendo as contagens. |

**D6 — minha leitura**

As opções cobrem os destinos principais do lote, mas misturam duas decisões: qual regra aplicar e qual força de conclusão admitir. P3.1 resolve a segunda expressamente: qualquer análise sob a emenda no lote já inspecionado é exploratória/descritiva; a avaliação confirmatória exige aquisição prospectiva com protocolo congelado previamente (P3.1:21–23).

- **v2 no lote:** preserva o resultado vazio e documenta o não atingimento; não destrava avaliação de generalização nesse lote (E2:87).
- **P3.1 exploratória no lote:** após aprovação, congelamento e autorização própria, destrava a descrição da elegibilidade sob a nova regra. Não garante população suficiente nem autoriza gold, build ou motor (P3.1:24,150–152,181–182).
- **P3.1 prospectiva:** prepara um protocolo para aquisição futura e avaliação confirmatória, condicionada às autorizações e ao atendimento dos mínimos; a aquisição futura pode também terminar insuficiente (P3.1:21–24,150–152).
- **Sugestão do planejador — combinar exploração e preparação prospectiva:** tratar o lote conhecido como análise descritiva separada e preparar o protocolo futuro sem condicionar sua redação ao resultado exploratório. É uma opção organizacional feita conhecendo as contagens; sua justificativa é separar os objetivos, não conseguir cursos elegíveis.

**Concordo condicionalmente com a recomendação (ii):** ela permite documentar o lote sob um recorte operacional mais explícito, preservando o resultado v2 e o caráter exploratório. Para o objetivo de generalização confirmatória, ela precisa ser acompanhada pelo caminho prospectivo, sem esperar que o lote conhecido legitime o protocolo.

**Risco residual:** aprovação de P3.1 não equivale a protocolo inteiramente resolvido: a regra de página continua provisória, há regra de conflito contextual ainda proposta e cada fase exige autorização própria (P3.1:57–64,96–98,123–124,181–182). Nenhuma das fontes fixa uma data de generalização.

**D7 — minha leitura**

As opções da DP são suficientes para discutir E4 numericamente, mas incompletas para decidir o objeto do estudo. **Retirar links apenas do denominador e excluí-los do alvo são decisões diferentes:** P3.1 faz a segunda e também os exclui de E3 e das conclusões (DP:61–63; P3.1:36–50).

- **Manter v2/E4:** preserva a comparação com a regra original; neste lote, mantém a seleção vazia (E2:87).
- **Excluir links do alvo pela P3.1:** destrava uma definição coerente de cobertura das ocorrências capturadas pelo protocolo. O efeito líquido permanece desconhecido: falhas, recusas e formatos não admitidos continuam no denominador, enquanto E3 exige documentos distintos (P3.1:71–87).
- **Outro limiar:** abre revisão normativa de tolerância à cobertura; não há nas fontes fundamento para recomendar um valor alternativo. Escolhê-lo após conhecer as contagens deve ser declarado e não pode ser justificado por elegibilidade de cursos (DP:6–8,61–63).
- **Sugestão do planejador — protocolo futuro com captura de destinos externos:** ampliar prospectivamente o alvo mediante cadeia de proveniência própria. A possibilidade decorre de P3.1 não declarar os links impossíveis de congelar; destravaria avaliação desse conteúdo apenas após definir e autorizar outro protocolo (P3.1:42–43).

**Concordo com excluir links conforme P3.1:** o recorte acompanha o que o protocolo captura com proveniência verificável e delimita corretamente as conclusões. Esta concordância é feita conhecendo as contagens e não se fundamenta em remover a barreira de elegibilidade.

**Risco residual:** o estudo passa a responder sobre o subconjunto operacional, não sobre a disciplina inteira ou seu conteúdo pedagógico (P3.1:163–164). Manter o valor de E4 não preserva o significado anterior da medida: P3.1 usa ocorrências do alvo em E4 e documentos distintos em E3 (P3.1:78–87).

**Limitações:** conferi os relatos e propostas do disco, sem validar inventários, fontes congeladas, código ou efeitos quantitativos. Branch/HEAD não foram verificados; a rota obrigatória foi consultada apenas para classificação da tarefa, sem uso como evidência sobre D6/D7.
````

#### job-27 — D8–D9

````text
Vou conferir as afirmações nas cinco fontes, com referências de linha, e entregar a tabela antes do aprofundamento. A recomendação será avaliada pelo contrato metodológico, sem usar a entrada ou saída de cursos como justificativa.

Classificação: verificação documental delimitada, somente leitura, no agente ativo; sem nova delegação. Vou distinguir o que as fontes confirmam do que é proposta normativa ainda pendente de aprovação.

A principal divergência está em D8: P3.1 separa E4 por ocorrências de aquisição e E3 por documentos cobertos distintos. As falhas permanecem no denominador de E4, mas não contam para atingir E3; a lista completa de falhas e a regra sobre outra ocorrência com os mesmos bytes estão explícitas em P3.1.

Em D9, as afirmações factuais conferem. Ampliar a busca é sugestão do coordenador: as fontes mantêm D9 aberto e não definem essa ampliação.

| decisão | afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|---|
| D8 | C1 — 23 arquivos `tipo_inesperado`, num curso, hoje só no inventário | confirma | DP:64–66; E2:66–69 | DP explicita que não entram nas contagens de adjudicáveis nem de fonte local. |
| D8 | C2 — P3 e P3.1 estabelecem toda a lista de não cobertura e impedem cobertura por outra ocorrência bem-sucedida | diverge | P3:64–72; P3.1:65–85 | P3 contém parte da lista; P3.1 explicita parcial, ambiguidade, vazio e a regra entre ocorrências. O denominador é de **E4**; E3 conta documentos cobertos distintos. |
| D8 | C3 — P3 chama a mudança de mais severa; efeito não calculado | confirma | P3:146–153 | Classificação expressa da proposta; não é efeito medido no lote. |
| D8 | C4 — `.go` 33 e `.asm` 9 também pesam contra o curso | confirma | P3:14–15, 137–138, 147; P3.1:71–85 | Na proposta, ficam não cobertos em E4 e não contribuem para atingir E3. Não é penalidade de acurácia do motor. |
| D8 | **Resumo — falhas no denominador; E4 mais difícil** | confirma | P3:146; P3.1:71–90 | Há respaldo normativo proposto para E4. A recomendação precisa distinguir E3/E4; o efeito líquido das mudanças não foi calculado. |
| D9 | C5 — busca limitada ao commit `bf46d51f` e nomes das pastas de download | confirma | DP:67–70; E3:103–106 | E3 especifica Git grep/log no commit e leitura dos nomes das pastas. |
| D9 | C6 — 21 candidatos, buscas ok; 11 sem ocorrência, 10 com ocorrências; nenhum N1 virou N0 | confirma | E3:105–112 | Resultado relatado; ocorrências descritas não produziram reclassificação. |
| D9 | C7 — P3.1 define validade de “sem ocorrência” e distingue ausência/erro | confirma | P3.1:168–177 | Também distingue erro de interpretação e trecho omitido; exige disponibilidade e interpretação integral das fontes requisitadas. |
| D9 | C8 — outras branches, worktrees, memória e conversas não foram buscadas | confirma | E2:91–92; DP:67–68 | Limite declarado expressamente. |
| D9 | C9 — N0 é ausência de evidência nas fontes pesquisadas, não independência comprovada | confirma | P3:127–128; DP:68–69 | A conclusão permanece relativa ao escopo da busca. |
| D9 | C10 — usuário cursou as disciplinas e conhece o conteúdo | confirma | E2:93–94 | Familiaridade afeta o cegamento do adjudicador; o relatório distingue isso de exposição do motor. |
| D9 | **Resumo — ampliar branches/worktrees e declarar memória/conversas como limite** | sem evidência | DP:67–70; P3:136; P3.1:168–182 | As fontes abrem a decisão, mas não prescrevem essa combinação. É sugestão do coordenador, documentalmente compatível com o problema. |

**D8 — minha leitura**

As opções “entram ou não entram” cobrem a decisão binária, mas são insuficientes como contrato operacional. P3 usa unidades por bytes adquiridos e unidades próprias para falhas; P3.1 separa **ocorrências de aquisição para E4** de **documentos cobertos distintos para E3**, substituindo a redação ambígua anterior. Portanto, não cabe falar genericamente em “denominador de E3/E4” (P3:40–46, 83–85; P3.1:5–8, 54–90).

**Sugestão do planejador:** formular a escolha em termos dessa separação: manter a contagem vigente ou adotar cobertura por ocorrências do alvo congelado, com falhas preservadas em E4 e somente documentos cobertos contribuindo para E3. A distinção já está proposta em P3.1; minha sugestão é incorporá-la explicitamente à decisão D8.

O que cada escolha destrava:

- **Manter a regra vigente:** resolve D8 pela manutenção da exclusão das falhas das contagens estruturais. A cobertura continua sem representar essas perdas, que ficam no inventário (DP:64–66).
- **Adotar a redação de P3.1:** define o denominador independentemente do sucesso da aquisição, impede que deduplicação ou outra ocorrência bem-sucedida apague uma falha e separa cobertura de disponibilidade de documentos para avaliação (P3.1:54–90).

**Concordo com a recomendação, com a correção para E4:** fixar o denominador antes de conhecer disponibilidade evita que falhas reduzam artificialmente o universo cuja cobertura se pretende medir. A justificativa é essa propriedade do protocolo, não o efeito sobre cursos específicos.

**Risco residual:** E4 passa a refletir também aquisição, proveniência e política de cegamento, não apenas capacidade do motor; formatos recusados reduzem cobertura mesmo quando seriam pedagogicamente úteis. Não se pode afirmar o efeito líquido sobre elegibilidade: há mudanças simultâneas de alvo e unidade, e a proposta deliberadamente não as aplicou ao lote (P3:144–153; P3.1:65–79, 156–164).

Resolver D8 não autoriza aplicação, gold, build ou motor. P3.1 mantém essas autorizações separadas e classifica análises deste lote conhecido como exploratórias/descritivas (P3.1:21–24, 181–182).

**D9 — minha leitura**

As opções “ampliar” ou “manter e declarar o limite” cobrem a direção da decisão, mas não definem a abrangência da ampliação. Falta especificar quais fontes serão requisitadas, quais estados serão examinados, como registrar ocorrências e o que fazer quando uma fonte estiver ausente ou sua leitura incompleta (P3.1:168–177).

**Sugestão do planejador:** admitir uma ampliação delimitada a branches/worktrees locais, com escopo congelado e memória/conversas explicitamente fora da busca. Essa é uma terceira configuração operacional entre manter tudo como está e ampliar a todas as categorias mencionadas; o nome da ferramenta, sozinho, não estabelece um contrato de cobertura.

O que cada escolha destrava:

- **Manter o alcance:** permite encerrar D9 com N0 estritamente relativo ao commit e às pastas pesquisadas, preservando a limitação declarada (DP:67–70; E2:91–92).
- **Ampliar de forma delimitada:** permite verificar exposição nas fontes adicionais escolhidas e registrar os limites restantes. Não autoriza converter automaticamente ocorrências em exposição efetiva nem N1 em N0: o verificador relatado não altera níveis, e a categoria do arquivo não determina uso ou nível (E3:103–112; P3.1:176–180).

**Concordo com a ampliação delimitada sugerida**, desde que “todas as branches/worktrees” seja convertido em escopo verificável, com ausências, erros e omissões separados de zero matches. Ela reduz uma lacuna documental conhecida, mas não comprova independência.

**Risco residual:** exposição por memória ou conversa continua não examinada; familiaridade do adjudicador permanece mesmo com uma busca ampliada. São limitações distintas, que não devem ser fundidas numa única classificação de exposição do motor (E2:91–94; P3:127–128).

Resolver D9 fecha apenas esse ponto pendente: não equivale ao Gate 1 nem elimina as demais decisões abertas (DP:3–4; E3:11–12).

**Limitações**

Conferi as afirmações contra as cinco fontes permitidas, por intervalos de linhas. Confirmei o que os documentos **relatam ou propõem**; não verifiquei inventários, scripts, capturas ou resultados subjacentes.

Cwd, branch e HEAD foram tomados do contexto fornecido, sem inspeção Git. Não executei testes, buscas de exposição, cálculos, rede ou experimentos; nenhuma decisão metodológica foi aplicada.
````

#### job-28 — Gate 2 do delta

````text
Vou conferir C1–C8 nas fontes permitidas e entregar a tabela antes do aprofundamento. Há conflito de escopo: a instrução de roteamento exige uma leitura adicional; farei só essa leitura obrigatória, sem usá-la como evidência dos vereditos.


REV registra os dois achados e a reprodução pelo coordenador; MOO mostra os caminhos responsáveis. Duas ressalvas: a falta de cobertura da suíte inteira não pode ser provada só pelos testes novos, e “Gate de rede” ainda precisa aparecer nos trechos autorizados.


| afirmação | veredito (confirma/diverge/sem evidência) | arquivo:linha | nota curta |
|---|---|---|---|
| C1 — NÃO APROVAR, 2 MAJOR, job-16/reviewer | **confirma** | REV:3, 12–13, 44–67 | O relatório registra exatamente esse parecer e essa identificação. |
| C2 — reproduções pelo coordenador | **confirma** | REV:132–144; MOO:440–465, 475 | Registra 0/3 e 2/5 bytes; erro sem limite e aceitação de `[]` com limite. Correspondência com o código detalhada abaixo. |
| C3 — MAJOR 2 exige chunked + Content-Length; frequência não medida | **confirma**, nos cenários documentados | REV:151–154; MOO:440–444, 461–464 | A combinação está nos dois reprodutores. “Fora do protocolo HTTP” é afirmação de REV; não foi conferida contra norma externa. |
| C4 — testes novos sem chunked; resultados verdes não cobrem os achados | **sem evidência**, para a afirmação sobre toda a suíte | TST:556–567, 584–678; REV:85–87, 155–156; REL:331, 335–339 | Confirmo ausência de chunked nos testes novos e os resultados **registrados**: 54/54; 2458 passam, mesma falha preexistente, 4 pulados. Os arquivos permitidos não provam ausência de cobertura em toda a suíte. |
| C5 — REL promete mais do que cumpre em chunked | **confirma** | REL:292, 299–300; REV:139–142; MOO:452–455, 461–464 | Há contraexemplos documentados tanto para compatibilidade sem limite quanto para contagem de resposta incompleta. |
| C6 — commit proposto só MOO/TST; tracker fora | **confirma** | REL:443–453 | O escopo proposto exclui expressamente o tracker. O `git diff --stat` atual também mostra o tracker modificado; isso não o inclui na proposta. |
| C7 — commit não destrava nada imediato; aquisição exige Gate de rede e R-VIS | **sem evidência**, para a formulação integral | REL:281, 466–468; ISS:352–359 | Confirmo R-VIS pendente, pacote sem liberação real e aprovações distintas. Esses trechos não explicitam “Gate de rede” nem demonstram ausência de qualquer dependência imediata. |
| C8 — correção pequena e localizada em `_le_resposta` | **confirma como inferência**, com ressalva | MOO:436–465; REV:52–53, 66–67 | Os caminhos defeituosos são locais. A entrega também precisa tocar testes e corrigir afirmações documentais; esforço e suficiência ainda não foram demonstrados. |
| Decisão — recomendar corrigir antes de decidir Gate 2 | **confirma como recomendação sustentada**, sem decidir pelo usuário | REV:163–166; ISS:356–359 | O delta atual tem parecer desfavorável. Corrigir exige Gate 1 próprio e nova autorização de revisão; esta conferência não substitui nenhum deles. |

Referências: **REV** = relatório independente de 30/09; **REL** = relatório de correções; **ISS** = issue de correções; **MOO** = `src/builder/sources/moodle.py`; **TST** = `tests/test_moodle.py`.

**C2 e C8: correspondência e alcance da correção.**

- **Subcontagem:** MOO:452–455 preserva e soma somente `exc.partial`, ignorando o payload em `exc.__cause__.partial` descrito em REV:139–140. A exceção reconstruída também recebe esse corpo incompleto. A correção precisa preservar os parciais úteis, sem duplicar chunks nem contar framing, mantendo contador, `ultimo_corpo` e exceção coerentes.
- **Erro sem limite:** MOO:440–441 transforma Content-Length em `esperado`, sem considerar chunked. Após ler o corpo completo, MOO:461–462 exige o comprimento conflitante e lança `IncompleteRead`.
- **Aceitação do prefixo:** MOO:447–449 interrompe a leitura quando acaba o saldo; MOO:461–464 não recusa quando o comprimento declarado já foi alcançado. MOO:465 devolve o prefixo, e MOO:475 aceita seu JSON. É preciso impedir que Content-Length conflitante sirva como prova de término do transporte.

Isso sustenta **localização da lógica**, não uma correção já comprovadamente pequena. Também seriam necessários transporte chunked nos testes novos (TST:556–567) e ajuste das promessas em REL:292, 299–300. Recusar cabeçalhos conflitantes, alternativa de REV:66–67, elimina a aceitação indevida, mas mantém diferença diante da leitura anterior no caso sem limite; essa escolha precisa ficar explícita no aceite.

**Opções e o que destravam.**

| opção | o que destrava |
|---|---|
| (1) Commitar como está | Versionamento do delta atual, mediante decisão explícita sobre o parecer desfavorável; não libera uso real. |
| (2) Corrigir ambos, testar e revisar novamente | Base corrigida e novas evidências para decidir Gate 2; não substitui as aprovações metodológicas. |
| (3) Commitar com limitações e issue | Versionamento e acompanhamento dos defeitos conhecidos; registrar limitações não satisfaz as promessas atuais. |
| (4) Não commitar por enquanto | Preserva a decisão pendente; não destrava implementação nem uso real. |
| **Sugestão do planejador:** dividir a correção em etapas, mantendo o commit pendente | Permite resolver a subcontagem enquanto se define a política para cabeçalhos conflitantes. Commit parcial exigiria escopo e aceite próprios. |

As opções cobrem os destinos principais do delta; faltou explicitar essa possibilidade de execução por etapas e a escolha entre desconsiderar Content-Length em chunked ou recusar a resposta conflitante.

**Concordo com (2):** os contraexemplos atingem compromissos expressos de R-META, e a restrição protocolar de MAJOR 2 não elimina MAJOR 1. A rodada adicional tem custo, mas produz evidência pertinente ao Gate 2; autorização continua sendo do usuário.

**Risco residual:** regressão na contagem ou no término exatamente no limite; frequência real dos cabeçalhos conflitantes desconhecida (REV:151–154); reentrância não validada (REV:113). R-VIS e aprovação metodológica permanecem pendentes independentemente dessa correção (REL:466–468).

**Limitações:** conferência documental e inspeção delimitada; não executei pytest nem reproduções. Não confirmei resultados históricos por execução, cobertura da suíte inteira, frequência na instância, norma HTTP, Gate de rede específico ou ausência universal de dependências imediatas; branch, HEAD e hashes completos ficaram atestados por REV:19–25, sem nova medição. A única leitura adicional foi o roteamento obrigatório, sem uso como evidência dos vereditos.
````
