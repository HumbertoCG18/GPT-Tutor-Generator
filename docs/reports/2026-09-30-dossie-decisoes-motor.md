# Dossiê de decisões do motor (30/09/2026)

Relatório único das decisões que dependem do usuário. Para cada uma: opções, evidência já medida (arquivo e número), o
que cada escolha destrava e a recomendação. **Recomendação não é aprovação**; nada aqui foi aplicado.

Produzido no trabalho noturno de 30/09 (Frente B), só com relatórios, issues e o tracker. Sem gold, sem conteúdo de
pacote cego, sem `.frzero/`, sem rede, LLM, build ou replay.

## 0. Como este dossiê foi montado

| seção | autor | estado |
|---|---|---|
| **B1. Validação externa do regime VOCAB** (D1–D9, R-VIS, R-CC, Gate 2 do delta Moodle) | **coordenador** (Claude Code, `claude-opus-5-5`), **verificada por 6 workers `planner-t2`** (`job-19` a `job-24`, `run-12`, 30/09 ~16:08) | Escrita de madrugada, depois de duas falhas do worker (`job-12` interrompido às 02:29, `job-17` timeout sem texto). Verificada à tarde em partes: 56 de 63 afirmações confirmadas, 3 divergências, 4 sem evidência (2 resolvidas depois). Cada decisão traz uma linha **Verificação**; o detalhe está em `2026-09-30-b1-verificacao-partes.md` |
| **B2. Motor CRU** (#49, CRU-02, CRU-03, CRU-05) | worker `planner-t2`, `job-18` / `run-11`, codex `gpt-6.1-sol`, 494,9 s | texto do worker reproduzido; números conferidos pelo coordenador contra a fonte (§B2.6); uma correção de fato acrescentada (Gate 2 da #49) |

Abreviações das fontes (todas sob `docs/reports/`; `c1-3` = `_harness-2026-09-04/c1-3`):

| sigla | arquivo |
|---|---|
| PRE | `2026-09-29-regime-vocab-validacao-externa-preregistro.md` |
| DP | `c1-3/validacao_externa_etapa2_29-09/decisoes_pendentes.md` |
| E2 | `c1-3/validacao_externa_etapa2_29-09/relatorio_etapa2.md` |
| E3 | `c1-3/validacao_externa_etapa3_29-09/relatorio_etapa3.md` |
| P3 | `c1-3/validacao_externa_etapa3_29-09/proposta_normativa_populacao.md` |
| P3.1 | `c1-3/validacao_externa_etapa3_correcoes_29-09/proposta_normativa_populacao_p3_1.md` |
| ISS | `c1-3/validacao_externa_etapa3_correcoes_29-09/issue_correcoes_etapa3.md` |
| REL | `c1-3/validacao_externa_etapa3_correcoes_29-09/relatorio_correcoes_etapa3.md` |
| POL | `c1-3/validacao_externa_29-09/politicas.md` |
| REV | `2026-09-30-revisao-delta-rmeta-rpage.md` (worktree da noite) |
| TRK | `pendencias.md` |
| HO | `2026-09-23-handoff-motor-wz-waa-claude.md` |
| DIAG | `2026-09-23-diag-identidade-e-cru05.md` |

## 1. Quadro das decisões, na ordem sugerida

| # | decisão | recomendação em uma linha | destrava |
|---:|---|---|---|
| 1 | **Gate 2 do delta Moodle** (R-META/R-PAGE) | **não commitar como está**: a revisão desta noite deu NÃO APROVAR (2 MAJOR, reproduzidos). Autorizar a correção e uma nova revisão. Alternativa: abandonar o delta e retirá-lo da árvore. "Não commitar" não tira o delta de execução local | commit técnico de `moodle.py` + `test_moodle.py` |
| 2 | **Gate 2 da #49** | Gate 2 **registrado como aprovado** em 22/09 ~12:23 (estado antigo da tarefa). O commit `410592d8` é ancestral do HEAD e de `origin/feat/motor-atribuicao` **local, sem fetch**. Reconciliar o tracker; estado remoto e integração na `main` não conferidos | fechar a pendência falsa do CRU-04 |
| 3 | **P3.1 como pacote** (resolve D1, D2, D3, D7, D8 e redefine D6) | aprovar a redação, aceitando a marca [C] e que o lote de 29/09 fica exploratório. Antes, explicitar a compatibilidade entre P3 §14 (pacote v3) e P3.1 (v5). D8 na forma da P3.1: falhas no denominador de E4; E3 conta documentos cobertos | regra de população; reescrita do pré-registro |
| 4 | **R-CC** (conflito contextual no gold) | ajustar duas lacunas e aprovar: dar encaminhamento à unidade indeterminável sem ocorrências em unidades diferentes; citar na P3.1 a sensibilidade do `?` | `gold-externo-2` e instruções v2 |
| 5 | **R-VIS** (binários e pixels no pacote cego) | recusar OLE e MP4 soltos; aceitar imagens com leitura dos metadados e aceitação expressa do risco dos pixels; varrer XMP e base64 | liberação do pacote cego para uso real |
| 6 | **D4** (`model_version`) | implementar a verificação na sanidade pós-geração | coerência entre política e código |
| 7 | **D5** (âncora do gitleaks) | fechar a âncora | exceção mais estreita |
| 8 | **D9** (alcance da busca de exposição) | estender a busca às branches e worktrees locais; declarar memória e conversas como limite | significado de "N0" no pré-registro |
| 9 | **Regime do CRU-02** | publicar o teto do cru como posição documental (meta não cumprida); conhecimento externo segue na frente VOCAB | fecha a direção da subunidade no cru |
| 10 | **Origem do bloco no CRU-03** | proposta delimitada para afinidade zero em fronteiras e janelas; cabeçalho e bloco de duas unidades como adjudicação | Gate 1 de medição do CRU-03 |
| 11 | **CRU-05** | priorizar a normalização dos acentos espaçadores; doador estrutural só depois de medição | Gate 1 de correção delimitada |

As decisões 1 e 2 podem ser **decididas** separadamente das outras. Mas o estado de `src/` que resultar da decisão 1
não é independente do congelamento da validação VOCAB: POL:9 fixa o hash de toda a árvore `src/`, e POL:18–19 e
PRE:122–125 mandam interromper diante de qualquer diferença, sem atualizar o esperado. Ver "B1 — Dependências e
pré-condições". As 3 a 8 são pré-condição da assinatura do pré-registro: ele
"não será assinado enquanto qualquer item abaixo estiver aberto" (DP:3–4). As 9 a 11 são da frente CRU e não dependem
da validação externa.

---

## B1. Validação externa do regime VOCAB

**Estado de partida (conferido nas fontes):**

- O pré-registro não está assinado (PRE:3). As afirmações de regra em D1, D2 e D3 estão suspensas (DP:4).
- População em 29/09: generalização = nenhum curso; piloto externo = nenhum; o mínimo não foi atingido (PRE:35–36).
- Lote adquirido em 29/09: 8 cursos N0, 461 itens da API = 267 ok + 171 links externos + 23 `tipo_inesperado` em um
  curso (E2:66–68). Pela regra v2, os 8 são inelegíveis: 7 falham em E4 e 1 em E3 (E2:76–87; DP:59).
- **Aviso de contaminação** (DP:6–8): as contagens do universo local e do lote já são conhecidas por quem decide.
  Nenhuma escolha abaixo pode ser justificada por fazer um curso específico entrar ou sair.
- A P3 (E3, §5) e a sua emenda P3.1 já propõem resposta para D1, D2, D3, D7 e D8. **Nenhuma das duas foi aprovada nem
  aplicada**, e nenhuma contagem foi calculada com elas (P3:3–5; P3.1:5–6). D4, D5 e D9 ficaram fora (P3:133–136).

### D1. Mínimo pós-gold e mínimo por curso

**Opções** (DP:15–19):

- A. manter só os mínimos totais;
- B. somar um mínimo por curso (exemplo: ≥ 10 na subunidade primária pós-gold; abaixo disso o curso é descritivo);
- C. mínimo derivado da precisão desejada (largura de intervalo).

**Evidência medida:**

- mínimos hoje: 3 cursos N0 e 100 adjudicáveis pré-gold; 80 materiais pós-gold; nenhum mínimo por curso (PRE:31–33;
  DP:12–13);
- a P3 (§8) e a P3.1 (§5.3) escolhem **B com 10**: curso com menos de 10 documentos na população da subunidade
  primária é descritivo quanto a C_novo, continua no agregado e no veto de perdas (P3:94–96; P3.1:145–149). O número
  10 é o mesmo de E3 (P3:96);
- para C não há cálculo feito (DP:19). Efeito de B no lote: não aplicável antes do gold (P3:148).

**O que destrava:** fecha um item que impede a assinatura. Define quando "nenhum curso regride" e C_novo valem por
curso. A opção C exigiria fixar métrica e método agora, trabalho novo e não medido.

**Recomendação: B com 10**, como está na P3.1. É o menor acréscimo que impede um curso de 5 materiais de virar "curso
avaliado" (risco que a própria DP aponta em A, DP:17). Risco residual: o número é convenção operacional, sem garantia
estatística (P3.1:19), e foi escolhido conhecendo as contagens (marca [C]). Com n = 10, C_novo
(`acertos × 10 > 9 × n`, PRE:153) exige 10 acertos em 10.

**Verificação (`job-19`): confirmada** (C1–C3 e recomendação). Acrescentado:

- a P3/P3.1 mantêm o veto de perdas também nos cursos pequenos, o que refina a opção B da DP (DP:18);
- a exigência de 10/10;
- sugestão do planejador: separar mínimo para C_novo, alcance do veto e diversidade pós-gold (hoje "3 cursos" só vale
  antes do gold; P3.1:148–149).

### D2. Bloco: medir com gold ou limitar a dois eixos

**Opções** (DP:27–29):

- A. dois eixos (unidade, subunidade primária) + estabilidade de bloco;
- B. bloco com gold por data/sessão da aula, com regra data → bloco fixada antes;
- C. bloco com gold sobre a lista de blocos do motor de timeline (quebra o cegamento).

**Evidência medida:**

- o pré-registro já descreve A: bloco não rotulado, invariância de bloco por ID entre CRU e candidato (PRE:50–52,
  149–151);
- a P3 (§10) e a P3.1 (§4.4–4.5) mantêm A e fixam a linguagem: "estabilidade de bloco", nunca "acerto" ou "acurácia"
  (P3:107–113; P3.1:128–136). A P3.1 acrescenta: sanidade dos IDs **antes** de comparar; se falhar, B_novo fica "não
  avaliado" (P3.1:131–133);
- acurácia de bloco em cursos novos: **não medida**; só com gold temporal independente e protocolo próprio
  (P3.1:135–136).

**O que destrava:** fecha D2 sem trabalho novo de adjudicação. A opção B exigiria pré-registro e Gate próprios; a C
está descartada pela própria DP.

**Recomendação: A**, com a redação da P3.1. Risco residual: não haverá conclusão sobre acurácia de bloco nos cursos
novos; dois braços podem concordar num bloco errado (P3.1:134).

**Verificação (`job-19`): confirmada** (C4–C6 e recomendação). **Mudou** a redação do risco: a versão anterior
("nada sobre acerto fora dos sete cursos") sugeria uma acurácia medida nos sete, que não foi conferida. Acrescentado:
a redação atual do PRE sobre bloco está suspensa enquanto D2 estiver aberta (DP:3–4). Sugestão do planejador:
registrar "A nesta validação; B num estudo temporal separado" (P3:107–113).

### D3. Unidade amostral e duplicatas

**Opções** (DP:39–42):

- A. material (bytes), avaliando só a entry de menor id;
- B. material, exigindo consistência (acerto só se todas as entries do material acertam);
- C. entry, com replicação da linha do gold (código atual);
- D. excluir os materiais duplicados.

**Evidência medida:**

- o código de 29/09 faz C e isso **infla o denominador** quando o build duplica entries, demonstrado pela revisão
  (DP:33–35); o pré-registro descreve essa replicação no §4.4 (PRE:66–68);
- no lote há 9 pares de duplicatas em 3 cursos (E3:96; P3:14);
- a P3 (§3–4) e a P3.1 (§3.1, §4.1, §4.3) escolhem **B**: documento = (curso, sha256), uma linha de gold por
  documento com todas as ocorrências visíveis, acerto só se todas as entries vinculadas satisfazem a régua do eixo,
  entry ausente conta como erro (P3:40–54; P3.1:83–84, 94–95, 125–127). Isso também responde à pergunta em aberto
  "o mesmo arquivo em duas seções vale uma linha" (DP:44–45; P3:50–51);
- efeito no lote: não calculado (deduplicação em E3/E4, P3:145; consistência no build, P3:149).

**O que destrava:** fecha D3. Trabalho novo: o §4.4 do pré-registro teria de ser reescrito (sustentado). Que o
avaliador genérico precise passar da replicação para a consistência é inferência do coordenador, não verificada.

**Recomendação: B.** É a única que não escolhe uma entry representante depois do build nem conta o mesmo julgamento
várias vezes. Risco residual: é mais severa (um erro de duplicata vira erro do material).

**Verificação (`job-19`): confirmada** (C7–C10 e recomendação; C11 continua inferência). Acrescentado:

- escolher B **não resolve** o conflito contextual, que depende de R-CC (P3.1:96–124);
- é preciso distinguir documento sem entry no build (conta como erro) de falha de correspondência de IDs entre
  braços (deixa B_novo "não avaliado"; P3:52–54; P3.1:125–133).

### D4. `model_version`

**Opções** (DP:49–51): implementar a verificação na sanidade pós-geração (sem nova geração) **ou** retirar a regra.

**Evidência medida:**

- a política diz que todas as respostas têm de trazer o mesmo `model_version` e que valores mistos invalidam a geração
  (POL:20–21; PRE:123–125);
- o código de 29/09 **não aborta** com `model_version` misto nem ausente (demonstrado, DP:49–50);
- o modelo é um alias sem versão imutável (POL:14; PRE:173);
- fora da P3 e da P3.1 (P3:133).

**O que destrava:** alinha política e código. Implementar é mudança de harness (não de `src/`), com teste; retirar é
só documento.

**Recomendação: implementar a verificação.** A regra é barata e é a única defesa contra o alias mudar no meio da
rodada. Risco residual: ela garante homogeneidade dentro da rodada, não que o modelo seja o mesmo da VOCAB_LIMPO (a
política já diz que o valor é relatado, não comparado, POL:21).

**Verificação (`job-20`): confirmada** (C1–C4 e recomendação). Acrescentado:

- a verificação deve recusar também versão **ausente ou vazia**, não só valores distintos (POL:20);
- não conferido: se o metadado está nos registros do harness, condição para implementar só lá.

### D5. Âncora da exceção do gitleaks

**Opções** (DP:52–53): fechar a âncora final da regex **ou** deixar como está.

**Evidência medida:** a regex aceita 64 hex seguidos de espaço e sufixo, sem âncora final; não foi alterada porque não
estava na lista autorizada (DP:52–53; E2:34–35). Fora da P3 (P3:134). A exceção vem do commit local `71dff722` (um
dos 6 commits à frente de `origin`). Quantas linhas hoje dependem do sufixo: **não medido**.

**O que destrava:** item independente do protocolo; fecha uma das pendências que seguram a assinatura.

**Recomendação: fechar a âncora.** Exceção de scanner de segredos deve ser a mais estreita possível. Risco residual:
alguma linha legítima com sufixo pode passar a falhar no check `secrets`; precisa de uma execução do gitleaks depois
da mudança, e é commit novo (os 6 locais não são reescritos).

**Verificação (`job-20`; regex conferida pelo coordenador com `git show 71dff722`): confirmada** (C5–C7 e
recomendação; C8 continua não medida). Evidência nova: a exceção é
`regexes = ['''resumo[\w.-]*\.json"\s*:\s*"[0-9a-f]{64}''']`, com `regexTarget = "match"`, `condition = "AND"`,
`targetRules = ["sumologic-access-token"]` e `paths = ['''^docs/reports/_harness-2026-09-04/''']`. Termina no hash,
sem `$`.

Sugestão do planejador: com `regexTarget = "match"`, a âncora fecha o trecho casado pela regra, não a linha. Definir o
formato completo admitido antes de acrescentar `$`.

### D6. Regra do lote adquirido

**Opções.** A DP só fixa o princípio: o lote usa a mesma regra da v2, e qualquer ajuste de limiar exige decisão
explícita, sabendo das contagens (DP:54–55). A P3 substitui D6 pela "entrada em vigor" (P3:135, 155–161) e a P3.1
endurece (P3.1:21–23). As opções reais são:

- (i) manter a v2 para o lote: a seleção continua vazia (E2:87);
- (ii) aprovar a P3.1 e aplicá-la **uma única vez** ao lote congelado, com o resultado relatado seja qual for
  (P3:158–159), tratado como **exploratório/descritivo** (P3.1:21–23);
- (iii) aprovar a P3.1 só para aquisição prospectiva;
- (iv) *(acrescentada na verificação, sugestão do planejador)* rota combinada: preservar o resultado v2, analisar o
  lote como exploratório **e** preparar à parte uma confirmação prospectiva;
- (v) *(idem)* aprovar e congelar a redação sem autorizar a aplicação imediata (P3.1:24, 181–182).

**Evidência medida:**

- resultado do lote pela v2: nenhum curso (E2:76–87);
- resultado do lote pela P3/P3.1: **não calculado**, de propósito (P3:152–153; P3.1:6);
- o catálogo da conta tem 28 cursos: 8 N0 (todos já baixados), 8 N1, 8 conhecidos excluídos, 1 excluído por
  correspondência parcial e 3 que não são disciplina (E2:53–62). **Não sobra curso N0 nessa conta** para uma
  aquisição prospectiva; a P3 já aponta "outra conta, outros semestres" (P3:102–103).

**O que destrava:** (ii) permite gerar pacotes cegos reais e exercitar a cadeia de ponta a ponta, mas sem veredicto
confirmatório. (iii) preserva o caráter confirmatório e depende de uma fonte nova de cursos.

**Recomendação: (iv), a rota combinada**, com o enquadramento da P3.1 §0. O lote já foi inspecionado; tratá-lo
como confirmatório depois de mudar a regra seria indefensável. O lote congelado oferece uma oportunidade já disponível
de exercitar a cadeia, sob autorização própria e com relato exploratório; as fontes não demonstram exclusividade nem
prazo (PRE:174–175; P3:102–103) *(corrigido em 01/10, revisão do GPT B1-N2)*. A evidência confirmatória só vem da via
prospectiva, com o protocolo congelado **antes** de examinar elegibilidade ou resultados da aquisição nova
(P3.1:21–23). Risco residual: as fontes não definem calendário para
a confirmação, que depende de cursos N0 fora do catálogo atual da conta.

**Verificação (`job-21`):** C1–C5 confirmadas. **Mudou:**

- o menu estava incompleto: foram acrescentadas (iv) e (v), e a recomendação passou de (ii) para (iv), que contém (ii);
- "o veredicto fica sem data" era inferência do coordenador; foi reescrito.

Nuance de C1: a DP fixa a regra da etapa, não só um princípio. Contradições novas em "B1 — Contradições encontradas":
P3:5 × P3:135 e P3:160 × P3.1:64.

### D7. E4 em cursos com links do Moodle

**Opções** (DP:59–63): manter E4 como está; tirar os links do denominador de E4; outro limiar.

**Evidência medida:**

- os 8 cursos N0 falham em E3 (1) ou E4 (7); E4 é o único critério que barra os 4 cursos que passam em E2 e E3
  (DP:59–60; E2:76–85);
- 171 dos 461 itens são links externos (E2:66–68);
- a P3.1 (§1) tira os módulos `url` do **alvo** (não só do denominador), com justificativa operacional: o protocolo não
  captura destinos externos sob a mesma cadeia de proveniência; vale para qualquer curso e não muda com a utilidade de
  um link (P3.1:36–50, 189);
- é a mudança mais sensível: "os links reprovam E4 em 7 de 8 cursos" (E3:128–129; P3:144). Efeito no lote: **não
  calculado**. O limiar de 90 % não muda (P3:84–85; P3.1:18).

**O que destrava:** preservada **integralmente** a regra v2, mantém-se o resultado vazio registrado e a validação não
começa (E2:74–87; PRE:38–41). O efeito de qualquer combinação com P3/P3.1 não foi calculado, e tirar os links do alvo
não garante elegibilidade *(corrigido em 01/10, revisão do GPT B1-N3)*.

**Recomendação: tirar os links do alvo, na redação da P3.1.** A justificativa (recorte de aquisição) independe das
contagens e é mais defensável que a da P3 (que se apoiava no schema do gold, P3.1:189). Risco residual: a decisão é
tomada conhecendo o efeito qualitativo; por isso o lote de 29/09 só pode ser exploratório (D6). As conclusões deixam
de valer para conteúdo acessado por link (P3:124–125).

**Verificação (`job-21`; PRE:38–41 no `job-20`): confirmada** (C6–C11, PRE:38–41 e recomendação). Ressalvas
acrescentadas:

- três dos cursos também falham em E2 (E2:78–83);
- os 461 itens não são automaticamente o denominador de E4;
- manter 90 % não mantém a mesma medida: na P3.1, E4 conta ocorrências e E3/mínimos contam documentos
  (P3.1:71–87);
- a R-PAGE provisória também mexe no alvo (P3.1:57–64).

Sugestão do planejador: capturar destinos externos num estudo prospectivo separado, com protocolo próprio
(viabilidade não demonstrada).

### D8. Downloads que falharam e a contagem estrutural

**Opções** (DP:64–66): falhas entram ou não no denominador de E3/E4.

**Evidência medida:**

- 23 arquivos com `tipo_inesperado` em um curso; hoje estão só no inventário (DP:64–65; E2:66–68);
- a P3.1 (§2.4) põe falha, parcial, recusa, ausência de vínculo, ambiguidade, conteúdo vazio e formato fora da
  allowlist **no denominador de E4, como ocorrências não cobertas**; o sucesso de outra ocorrência com os mesmos bytes
  não cobre a que falhou (P3.1:65–79). A P3 (§5) enumera menos casos e fala em "unidades" (P3:58–72);
- na P3.1, **E3 é outra medida**: o número de documentos cobertos distintos. Uma falha não entra como denominador de
  E3; só deixa de gerar documento coberto (P3.1:54–56, 78–90);
- a P3 classifica a mudança como "mais severa"; efeito não calculado (P3:146–147).

**O que destrava:** fecha D8 e torna E4 uma medida de cobertura do alvo, não do que por acaso chegou.

**Recomendação: falhas no denominador de E4; E3 conta só documentos cobertos** (a redação da P3.1). É a opção que não
premia falha de aquisição. Risco residual: E4 passa a misturar disponibilidade da aquisição, proveniência e
admissibilidade pelo cegamento; formatos de código fora da allowlist (`.go` 33, `.asm` 9, P3:14) também pesam contra
o curso.

**Verificação (`job-22`):** C1, C3, C4 confirmadas. **Mudou:**

- C2 atribuía à P3 a lista completa, que é da P3.1;
- a recomendação "falhas no denominador de E3/E4" juntava duas medidas diferentes e foi reformulada.

Sugestão do planejador: decidir separadamente a unidade de E4 e a contagem de E3, inclusive para ocorrências
repetidas.

**Rodada 2 (`job-27`, 30/09 ~23:59, concluída em 167 s): confirma a rodada 1** (C2 diverge pelo mesmo motivo; a
recomendação reformulada é confirmada com a separação E3/E4). Acrescentado:

- formatos fora da allowlist reduzem a cobertura (E4) e não contam para E3; não são penalidade na acurácia do motor;
- resolver D8 não autoriza aplicar a regra, nem gold, build ou motor (P3.1:21–24, 181–182).

### D9. Alcance da busca de exposição

**Opções** (DP:67–70): estender a busca a outras branches, worktrees, memória de sessões e conversas antes do Gate 1,
**ou** manter o alcance e declarar o limite.

**Evidência medida:**

- a busca olha só o commit `bf46d51f` e os nomes das pastas de download (DP:67–68; E2:91–92);
- verificação local da etapa 3: 21 candidatos, todos com busca ok; 11 sem ocorrência; 10 com ocorrências descritas;
  nenhum N1 virou N0 (E3:103–112);
- a P3.1 (§7) define quando "sem ocorrência" vale e distingue zero matches de fonte ausente e de erro (P3.1:168–177);
- outras branches, worktrees, memória e conversas: **não buscadas** (E2:91–92).

**O que destrava:** define o que "N0" significa no pré-registro: "nenhuma evidência nas fontes pesquisadas", não
independência comprovada (P3:127–128).

**Recomendação (sugestão do coordenador, não está nas fontes como opção fechada): estender a busca ao que é local e
determinístico** (todas as branches e worktrees locais, por `git grep`, sem rede nem LLM) e **declarar memória de
sessões e conversas como limite**. Risco residual: exposição por conversa ou memória continua invisível; o usuário
cursou as disciplinas e conhece o conteúdo (E2:93–94).

**Verificação (`job-22`): confirmada** (C5–C10 e recomendação, como sugestão do coordenador). Ressalva acrescentada:

- `git grep` em branches e worktrees não cobre arquivos não versionados nem revisões históricas, e os próprios
  relatórios da validação são não versionados (E3:162–164);
- é preciso congelar **antes** da busca quais branches, revisões, worktrees e arquivos locais entram;
- fonte requisitada que não puder ser examinada não vira "zero matches" (P3.1:168–177).

O texto do worker foi cortado no fim, antes das limitações.

**Rodada 2 (`job-27`, concluída em 167 s, com as limitações): confirma C5–C10.** A recomendação aparece como "sem
evidência" nas fontes, porque é sugestão do coordenador (já marcada assim acima). Acrescentado:

- "git grep em todas as branches" não é, sozinho, um contrato de cobertura: o escopo precisa ser verificável, com
  ausência, erro e omissão separados de zero matches;
- ampliar a busca não converte automaticamente ocorrência em exposição nem muda N1/N0; a categoria do arquivo não
  determina uso nem nível (E3:103–112; P3.1:176–180);
- familiaridade do adjudicador e exposição do motor são limitações distintas e não devem ser fundidas (E2:91–94;
  P3:127–128);
- resolver D9 fecha só esse ponto, não o Gate 1 (DP:3–4).

### R-VIS. Cegamento e binários

**Opções** (ISS:171–175): a) recusar o que não é examinável; b) aceitar expressamente o risco residual dos pixels,
examinando todas as estruturas textuais; c) outra política. O relatório detalha (REL:209–221): (a) OLE legado solto:
recusar; (b) imagens: **b1** recusar ou **b2** aceitar com leitura dos metadados textuais e aceitação explícita dos
pixels; (c) MP4 solto: recusar; (d) XMP do PDF e base64 de `ipynb`: varrer ou aceitar como limitação.

**Evidência medida:**

- R-VIS **não foi aprovada** e nada foi implementado; o pacote cego não está liberado para uso real (ISS:139, 170;
  REL:281);
- "sem OCR" (Gate 1) proibiu acrescentar OCR, não autorizou entregar pixels não examinados (ISS:141–142);
- proveniência confirmada não diz nada sobre o conteúdo que o professor publicou (ISS:153–154, 163);
- a v4 aceita sem inspeção suficiente: imagens embutidas e soltas, OLE legado e MP4 (só pela assinatura), pixels e
  XMP de PDF (o dicionário Info é lido) e base64 de notebook (há varredura textual, mas a base64 não é decodificada)
  (REL:194–205);
- impacto no lote de qualquer opção: **não calculado** (REL:224–226); a recusa conservadora já vigente também não teve
  impacto calculado (REL:172–173);
- critérios de aceite da implementação já listados (ISS:329–339); arquivos afetados: gerador v5 e testes (ISS:322).

**O que destrava:** é a decisão que libera (ou não) o pacote cego para uso real. Sem ela não há entrega ao
adjudicador. Exige implementação nova no gerador, com teste vermelho por caso.

**Recomendação: a do próprio relatório (REL:221): recusar OLE e MP4 soltos, b2 para imagens, varrer XMP e base64.**
Risco residual, que precisa de aceitação **expressa**: pixels e vetores não examinados; uma figura com texto proibido
passaria. O argumento de que a b1 "derruba quase todos os slides e documentos com figura" (REL:214–215) é apreciação
qualitativa, não medida. A escolha deve se apoiar no alcance de inspeção que se aceita.

**Verificação (`job-23`): confirmada** (C1–C4, C6, C7 e recomendação). **Mudou:** C5 dizia "só pela assinatura" para
todos os casos; PDF e notebook têm inspeção parcial (corrigido acima). Sugestões do planejador, antes da decisão:

- explicitar o tratamento de vetores e o significado de "inspeção suficiente";
- alinhar EXIF, que está nos testes de aceite (ISS:332) mas não na enumeração da b2 (REL:216–218);
- esclarecer que os "mesmos arquivos limpos" dos controles não incluem OLE/MP4.

Contradição nova em "B1 — Contradições encontradas": REL:218.

### R-CC. Conflito contextual no gold

**Opções:** aprovar a regra proposta (ISS:277–316; P3.1:96–124), alterá-la ou recusá-la. Recusar deixa o caso sem
regra: não existe regra de status aprovada para conflito (ISS:264–275; P3.1:96–98).

**Evidência medida:**

- é só proposta documental; sem gold nem adjudicação (ISS:369);
- a regra: rótulo pelo conteúdo; vários ids quando o conteúdo sustenta mais de uma unidade ou tópico; marcador `?`
  quando só a subunidade é ambígua; `excluido` com `conflito_contextual:` quando o conteúdo não decide a unidade
  **e** as ocorrências estão em seções de unidades diferentes (ISS:279–293);
- **lacuna:** unidade indeterminável **sem** ocorrências em unidades diferentes não tem encaminhamento na regra;
- sensibilidade com consequência fixada antes dos resultados, para A_novo e C_novo (não para B_novo): o veredicto só
  é "aprovado" se aprovar nas duas contas; o limiar não muda (ISS:304–311);
- exige `gold-externo-2` e instruções v2, arquivos novos; o `gold-externo-1` não é editado (ISS:315–316);
- quantos documentos do lote cairiam em conflito: **não medido** (não há gold).

**O que destrava:** fecha o §4.2 da P3.1 e permite redigir o `gold-externo-2`. É só documento (ISS:325).

**Recomendação: ajustar duas lacunas e aprovar.** Ajustes:

1. dar encaminhamento ao caso de unidade indeterminável sem ocorrências em unidades diferentes. Isso exige uma
   **escolha explícita do usuário** de status/encaminhamento antes do gold; a revisão do GPT (01/10) não propõe uma;
2. fazer a P3.1 mencionar a sensibilidade do `?`, já detalhada em ISS:305–306. Redação mínima proposta pela revisão
   do GPT: "A_novo e C_novo são calculados no principal e na sensibilidade: documentos excluídos por conflito contam
   como erro nos eixos afetados; documentos com `?` contam como erro nos eixos de subunidade. Aprovação exige as duas
   contas, sem mudar limiar. B_novo não possui conta de sensibilidade."

A regra é fixada antes de qualquer gold e já traz a conta de sensibilidade, que é o que impede a exclusão por conflito
de virar grau de liberdade. Risco residual:

- o adjudicador é único e aplica a regra sozinho (PRE:86);
- o marcador `?` reduz os denominadores de subunidade;
- B_novo fica sem conta de sensibilidade;
- se os mesmos conflitos contam como erro em todos os braços, a ordenação de A_novo se mantém e a pressão recai sobre o
  limiar de C_novo (inferência do planejador).

**Verificação (`job-23`):** C8, C9, C11–C14 confirmadas. **Mudou:**

- C10 omitia a segunda condição da exclusão (ISS:292–293), corrigida acima; daí vem a lacuna 1;
- "aprovar" era juízo do coordenador, sem evidência nas fontes; a recomendação passou a "ajustar e aprovar".

### Gate 2 do delta Moodle

**Opções:**

1. commitar os dois arquivos como estão;
2. corrigir os dois achados antes (Gate 1 próprio para `src/`, teste vermelho primeiro, nova revisão autorizada) e
   só então decidir o Gate 2;
3. commitar como está, registrando os dois achados como limitação conhecida e abrindo issue (sugestão do coordenador,
   listada só para completar o quadro);
4. não commitar o delta no produto por enquanto (**isso não o tira de execução**: a árvore principal roda com o
   `_call` modificado, `moodle.py:475`, inclusive pela UI, `dialogs.py:1719`);
5. *(acrescentada na verificação, sugestão do planejador)* abandonar formalmente o delta e retirá-lo da árvore. Exige
   reconciliar o `adquire` v5, que depende do contador e do limite do cliente (REL:305–309).

**Evidência medida:**

- revisão independente desta noite (`job-16`, papel `reviewer`, codex `gpt-6.1-sol`): **NÃO APROVAR**, 2 MAJOR (REV,
  §3);
- os dois achados foram **reproduzidos pelo coordenador** em memória, sem escrita (REV, §6):
  - chunk truncado: `bytes_recebidos` registra 0 de 3 bytes e 2 de 5;
  - resposta chunked com Content-Length conflitante: sem limite, o delta levanta `IncompleteRead` onde a leitura
    anterior devolvia `[]`; com limite, aceita `[]` de um corpo `[]xxx`;
- o segundo achado só aparece com `Transfer-Encoding: chunked` e `Content-Length` juntos (resposta fora do protocolo);
  a frequência disso na instância real **não foi medida**;
- os testes do delta não geram resposta chunked: `tests/test_moodle.py` 54/54 e a suíte (2458 passam, 1 falha
  preexistente e alheia, 4 pulados; REL:331, 335–339) não cobrem nenhum dos dois casos;
- o relatório de 29/09 afirma que os bytes são contados "quando a resposta vem incompleta" e que `None` é o
  comportamento anterior (REL:292, 299–300): as duas frases precisam de ressalva;
- o commit proposto tem só os dois arquivos; `pendencias.md` fica fora (REL:443–453).

**O que destrava:** o commit técnico do `MoodleClient`. Ele não é pré-condição de nada imediato: a aquisição real
depende de Gate de rede e de R-VIS, e a assinatura do pré-registro depende de D1–D9.

**Recomendação: opção 2.** O defeito de contagem atinge justamente o que o R-META promete (o orçamento de bytes), e
não há pressa que justifique commitar com revisão desfavorável. A correção é localizada em `_le_resposta`: o tratamento do parcial em
`moodle.py:452–455` e a leitura do comprimento em `moodle.py:440–464`. O esforço não foi medido. Risco residual:
mais uma rodada (Gate 1, testes com transporte chunked, nova revisão que exige autorização explícita). Na correção há
uma escolha de contrato: recusar cabeçalhos conflitantes não restaura o comportamento anterior do caso 2a. Se for
essa a escolha, o aceite precisa dizer isso, em vez de manter a promessa de compatibilidade (ISS:344–345).

**Revisão do GPT (01/10): NÃO APROVAR confirmado; "corrigir antes" mantido** (29 casos HTTP offline). Acrescentado:

- o MAJOR 2 continua MAJOR mesmo com cabeçalhos fora do protocolo, porque o prefixo é aceito em silêncio;
- caso M2c: com chunked + Content-Length 999 e limite 3, o delta recusa sem ler, quando o payload real (2 bytes)
  cabia;
- armadilha da correção do MAJOR 1: no caso C16 (`2\r\n[]\r`) a causa interna contém `\r`, que é framing. Somar
  `__cause__.partial` às cegas conta 3 em vez de 2;
- reentrância na mesma instância reproduzida (contador 4 > limite 3), com uso concorrente real não demonstrado:
  MINOR condicional. O encaminhamento mínimo é declarar uso sequencial por instância, sem ampliar o escopo;
- corrigir por etapas organiza a execução, mas o Gate 2 fica pendente até o conjunto inteiro;
- redação recomendada: "Corrigir ambos os defeitos sob escopo autorizado, começando pelos testes de payload/framing e
  fixando a política para cabeçalhos conflitantes antes do aceite. Gate 2 pendente até os testes do conjunto e a
  revisão autorizada. Adiar o commit não desativa o delta local. Antes da validação externa, reconciliar o baseline
  de `src/` com POL §1/PRE §8."

Plano da correção: `2026-09-30-noite-resumo.md`, §12.

**2ª revisão do GPT (01/10):** o esboço de correção corrige os sete contraexemplos anteriores, mas **não** basta para
o contrato:

- P-01: `TimeoutError` ou `LineTooLong` depois do payload perde a contagem;
- P-02: tamanho de chunk `-1` leva a `read(-1)` além do teto.

Os dois são MAJOR. A recomendação "corrigir antes" continua, e o escopo passa a incluir P-01 e P-02. A direção do
usuário (01/10) está no resumo, §12.1 e §12.3:

- V1 inicial, sem troca automática para a V2;
- CL ignorado em chunked e Transfer-Encoding não suportado recusado antes do corpo;
- matriz Python antes de implementar;
- worktree isolada;
- Gate 2 sobre o conjunto.

Escolher recusar cabeçalhos conflitantes não resolveria o chunk negativo sem CL.

**3ª revisão do GPT (01/10):** nenhum CRITICAL nem MAJOR novo; cinco MINOR incorporados ao resumo, §12.1 e §12.3.
O A35 deixou de ter alternativa: o candidato ignora o CL e recusa o tamanho negativo antes do payload. A V1 é
plausível, não validada. Decisões novas apresentadas antes do Gate 1: versões concretas da matriz e contrato do R5.

**Verificação (`job-24`; C4 e C7 resolvidas pelo coordenador): confirmada** (C1–C8 e recomendação).

- O worker apontou a causalidade linha a linha (`moodle.py:440–465, 475`).
- C4 foi medida pelo coordenador com `grep`, somente leitura: `MoodleClient` só aparece em `tests/test_moodle.py`, e
  "chunked" na suíte só aparece no backend Datalab. Nenhum teste exercita o cliente com resposta chunked.
- C7: "nova aquisição exige manifesto novo e Gate de rede" está em E3:89–90 e REL:187.
- **Mudou:** entraram a opção 5 e a ressalva da opção 4.

### B1 — Ordem sugerida de decisão

1. **Gate 2 do delta Moodle** (independente; decidir já, porque há revisão desfavorável).
2. **P3.1 como pacote**: D7, D8, D3, D1 e D2 estão escritas juntas e se apoiam (alvo → ocorrências → documento →
   mínimos → bloco). Decidir **D6** no mesmo ato, porque a aprovação define o que se pode concluir do lote.
3. **R-CC** (é o §4.2 da P3.1).
4. **R-VIS** (libera o pacote cego).
5. **D4, D5, D9** (independentes e pequenas).
6. Só então: reescrever o pré-registro com as regras aprovadas, congelar por hash e ir ao Gate 1 (PRE:102).

### B1 — Dependências e pré-condições de execução (acrescentadas em 01/10, revisão do GPT)

Nenhuma delas autoriza editar política, adquirir, produzir gold, rodar o motor ou decidir Gate.

1. **Baseline de `src/` (B1-N1, MAJOR documental).**
   - **Conflito:** POL:9 congela o hash de toda a árvore `src/`, e POL:18–19 e PRE:122–125 mandam interromper diante
     de qualquer diferença, sem atualizar o esperado. O delta do `MoodleClient` altera `src/` (REL:290; ISS:365–367).
   - **Possibilidades a deliberar:**
     - uma árvore de aquisição corrigida e outra de compilação exatamente congelada, com identidades e passagem de
       artefatos explícitas;
     - ou emendar o baseline por decisão metodológica própria e rastreável.
   - **Proibido:** atualizar o hash esperado automaticamente.
   - **Não medidos:** o hash atual de `src/` e se o harness suporta a separação.
2. **R-VIS** precede qualquer aplicação. Ela muda a cobertura de E4 e os documentos de E3 (P3.1:65–85), e também E2,
   porque plano recusado impede elegibilidade (P3.1:140–142). A política de cegamento precisa estar aprovada,
   implementada, verificada e congelada antes de aplicar a regra de população.
3. **R-PAGE** continua provisória e informada pelo lote (P3.1:57–64). Falta decidir entre confirmar o contrato da
   versão da instância (consulta externa, com Gate próprio) e assumir a regra provisória de forma justificada no
   protocolo.
4. **R-CC:** resolver D1/D3 não resolve R-CC nem congela `gold-externo-2` e as instruções v2 (ISS:315–316). A unidade
   indeterminável sem ocorrências em unidades diferentes precisa de encaminhamento concreto.
5. **D9** exige um universo de busca congelado (revisões, branches, worktrees, arquivos locais), com tratamento de
   indisponibilidade, erro e omissão. **D4** depende de confirmar que o metadado existe nos registros do harness.
   **D5** depende de definir o trecho exato permitido e testar o scanner.
6. **Precedência v3/v5:** P3:160 exige o "pacote cego v3 aprovado" e P3.1:64 cita a v5. Isso é desatualização
   contratual, não defeito funcional demonstrado. Falta redação de precedência que identifique a versão aplicável da
   política e os scripts aprovados. "Implementado na v5" não significa "aprovado para uso real" (REL:281).

### B1 — Contradições encontradas

- **Pré-registro × P3.1.** O pré-registro ainda descreve a população pela regra v2 (PRE:27–29), a replicação da linha
  do gold (PRE:66–68) e a versão `pacote-cego-1` (PRE:88); a P3.1 propõe o contrário nos dois primeiros pontos
  (P3.1:83–84, 125–127) e o gerador já está na v5 (REL:316). Não é erro: o pré-registro está congelado à espera das
  decisões. Mas ele precisa ser reescrito, não só assinado.
- **Issue × código.** O A2 descreve `OrcamentoExcedido` com `bytes_lidos` (ISS:202); o código usa `parcial`. O
  revisor considerou a divergência nominal, sem efeito nos consumidores (REV, §4, resposta 3).
- **Relatório × revisão.** As linhas REL:292 e REL:299–300 afirmam mais do que o código cumpre nos cenários chunked
  (REV, §6).
- **Cabeçalho do Adendo 2.** Diz "AGUARDANDO DECISÃO" e "nada implementado neste adendo" (ISS:128–134), enquanto A2 e
  A3 já trazem "IMPLEMENTADO" no título (ISS:179, 228). O Adendo 3 esclarece (ISS:363–371).
- **Errata da preparação.** Em 29/09 eram três N0 (CALC1, FP, MC), não cinco (E2:10).
- **P3 sobre D6 (achada na verificação).** O cabeçalho da P3 diz que D6 "fica fora" (P3:5); o §12 diz que D6 foi
  "substituído pelo §14" (P3:135).
- **Versão do pacote cego na entrada em vigor (achada na verificação).** A P3 exige o "pacote cego v3 aprovado"
  (P3:160); a P3.1 já cita o `adquire` e o gerador v5 (P3.1:64). A compatibilidade precisa ser explicitada antes de
  autorizar a aplicação.
- **REL × issue sobre pixels de PDF (achada na verificação).** REL:218 diz "como já foi aceito para o texto de PDF em
  imagem"; o próprio relatório (REL:169–171) e o issue (ISS:141–142) corrigem isso: a aceitação está pendente.

### B1 — Limitações

- Seção escrita pelo coordenador e verificada depois por seis workers `planner-t2` (`job-19` a `job-24`), cada um
  só com as fontes da sua parte. Quatro estouraram os 600 s mas entregaram o texto escrito; o do `job-22` (D8–D9)
  perdeu só as limitações. Essas quatro partes foram refeitas com os mesmos specs na rodada 2 (`job-25` a `job-28`,
  `run-13`, 30/09 ~23:57), todas concluídas em 165–178 s, com os mesmos vereditos. A D8–D9 chegou completa. Continuam
  sem evidência: D3 C11 (inferência) e D5 C8 (não medido).
- Não foram lidos: `relatorio_preparacao.md`, `errata_relatorio_preparacao_29-09.md`, `sugestoes_redacao_p3.md`, os
  JSON de inventário, conferência e triagem, o `.gitleaks.toml` e o código do harness genérico. O que depende deles
  está marcado como "não medido" ou "inferência".
- Todos os números vêm dos relatórios citados; nenhum foi recalculado nesta noite, exceto a reprodução dos achados da
  revisão (REV, §6).
- Nenhum efeito das regras propostas no lote foi calculado, por desenho (P3:152–153).

---

## B2. Motor CRU

Texto do worker `planner-t2` (`job-18`), com as referências originais relativas a `docs/reports/`. As notas do
coordenador estão marcadas.

Recomendações não equivalem a aprovação. Mantêm-se a meta estritamente **> 90 % por eixo**, ausentes no denominador e
o aceite de integração: ganho positivo, zero perda, nenhum curso regride, replay integral (`pendencias.md:10`;
`2026-09-23-handoff-motor-wz-waa-claude.md:13–18`).

### Gate 2 da #49

> **Correção de fato (coordenador, medida nesta noite).** O **Gate 2 da #49 já foi aprovado** pelo usuário em 22/09
> ~12:23 ("Commitar código + artefatos"), com escopo de 2 arquivos de `src/tests` + 15 artefatos de `c1-3`; push, PR
> e merge não foram autorizados naquele ato. O registro está no estado antigo da tarefa, campo `gate_2_49`
> (`.workflow/local/active-task-ate-20260930.md`). O commit é o `410592d8` (22/09 12:23:26, "fix(motor): _score do
> desempate deixa de dividir por sqrt(len(sig))", Refs #49; código: `disambiguator.py` e `test_motor_disambiguator.py`,
> +67/−12). Ele é ancestral do HEAD `bf46d51f` e da referência local `origin/feat/motor-atribuicao`. O tracker nunca
> cita esse hash: o bloco da #49 ainda diz "SEM COMMIT" (`pendencias.md:999`) e o CRU-04 diz "Gate 2 pendente"
> (`pendencias.md:45`). **A decisão que resta não é o Gate 2; é corrigir o tracker** (e, à parte, a integração na
> `main` pela PR #9). O worker não tinha acesso ao estado local e por isso tratou a aprovação como não comprovada.

**Opções**

- **Reconhecer a entrega existente e reconciliar o encerramento documental/Gate 2** (sugestão do planejador). A
  escolha de V1 já foi aprovada no Gate 1; não cabe reabrir a comparação de fórmulas (`pendencias.md:997–1003`).
- **Manter o aceite formal pendente**, especificando qual comprovação falta (sugestão do planejador). A existência do
  commit não demonstra, sozinha, autorização do Gate 2. *[Nota do coordenador: a autorização existe; ver a correção
  acima.]*
- A integração na `main` permanece decisão própria da frente MOTOR-9/PR #9 (`pendencias.md:76–78`).

**Evidência medida**

- O git confirmou `410592d8` no histórico da branch atual e na referência local `origin/feat/motor-atribuicao`.
  Portanto, "SEM COMMIT" está desatualizado.
- Foi commitada a remoção do divisor de `_score`, mantendo assinatura e gate D4. O diff de código e teste é de 2
  arquivos, +67/−12; o commit também contém artefatos das medições (`pendencias.md:1000–1003, 1016–1017`).
- O aceite com código real passou 11/11: bloco 214 → **217/237 (91,6 %)**, unidade 246/284, zero perda e nenhum curso
  regredindo. Mudaram exatamente os blocos de MF `exerciciosnusmv`, MF `provas` e IA `k-nn`; houve 16 mudanças de
  banda/flag sem troca de bloco. A influência do comprimento caiu de 18/97 para 0/97 janelas
  (`pendencias.md:969, 1002–1009`).
- A revisão Astra única já foi consumida: "APROVAR COM AJUSTES", nenhum achado CRITICAL/HIGH/MEDIUM e 2 LOW tratados.
  Testes: 28/28 no disambiguator; suíte com 2410 aprovados, 4 pulados e 1 falha preexistente. O W-T depois reproduziu
  217/237 e 246/284 pela cadeia real, com congelamento e JSON idênticos (`pendencias.md:1010–1017, 1113–1114`).

**O que destrava.** Reconciliar o estado permite reconhecer a entrega da #49 no CRU-04 e retirar a pendência
documental incorreta. Não exige reimplementação nem repetir a revisão consumida. A integração via MOTOR-9 continua
separada (`pendencias.md:45, 76–78`).

**Recomendação.** Reconhecer o commit existente e corrigir o tracker. Risco residual: a situação atual da issue #49
no GitHub e a integração na `main` não foram verificadas (sem rede); os testes históricos não certificam
automaticamente o HEAD atual.

### Regime do CRU-02

**Opções** (exatamente as das fontes; `2026-09-23-handoff-motor-wz-waa-claude.md:78–80`):

- **(a)** regime separado de conhecimento externo, relação termo → tópico, com guarda contra ajuste ao benchmark;
- **(b)** aceitar e publicar o teto do cru por curso;
- **(c)** outro mecanismo sobre o pacote, somente com fonte de sinal nova.

A opção (a) já tem frente própria em andamento (regime VOCAB, seção B1). Isso não é autorização para inserir LLM ou
embedding no cru.

**Evidência medida**

- Na base v2, a subunidade primária está em **86/251**; o mínimo agregado é 226, faltando **+140**. Por curso: MF
  25/58, SO 7/15, IA 4/39, ES2 7/28, TCC 7/11, CG 30/82, FR 6/18 (`handoff:32–41`).
- O W-Z2 separou 165 erros em não geração 76, seleção 67, unidade 17 e identidade 5. O oráculo de unidade levou 86 →
  92, com 8 correções e 2 perdas: corrigir a unidade não resolve o déficit principal (`handoff:56–58`).
- O W-AA reprovou os mecanismos examinados: S 83 (+1/−4), G 76 (+19/−29) e G+S 73 (+20/−33), contra a base 86. Os
  ganhos do IA por G eram colisões de radical, não demonstração da relação categoria → algoritmo
  (`pendencias.md:671–678`).
- Para (b): teto estrutural ideal de 234/251 com unidade oráculo, mas o CG fica em 69/82 (84,1 %); sem corrigir a
  unidade, 218/251. A fonte ressalva que é teto das intervenções sobre as fontes inspecionadas e a régua atual, não
  limite universal de informação. Tetos completos por curso: não encontrados nas fontes permitidas
  (`pendencias.md:700–704, 740`).
- Para (a) e (c), ganho integrado demonstrado nesta base: não medido / não encontrado.

> **Nota do coordenador.** Existe um commit posterior, `3c8f26d9` "docs(motor): teto do regime cru por curso e
> varredura final da subunidade (W-AC)", no histórico do branch. Ele não estava na lista de fontes do worker e não
> foi lido nesta noite: os tetos por curso podem já estar medidos lá. **Não conferido.**

**O que destrava**

- (a): prosseguimento da frente separada; não encerra o CRU-02 nem cumpre a meta do cru por transferência de
  resultado;
- (b): publicação honesta do placar, da cobertura e dos limites medidos. Exige distinguir resultado observado de teto
  condicional; não autoriza declarar a meta cumprida;
- (c): nova proposta de Gate 1, identificando sinal, proveniência e hipótese discriminante antes de medir. Não
  destrava a reutilização de S/G/G+S nem a rotulagem obrigatória pelo professor (`pendencias.md:679–681`;
  `handoff:17–18, 78–80`).

**Recomendação.** Adotar **(b) como posição documental do cru**, preservando a meta como não cumprida, e manter (a)
na frente própria. Só escolher (c) quando houver sinal novo identificável. Risco residual: as medições refutam
mecanismos específicos; não provam a impossibilidade geral do cru.

### Origem do bloco no CRU-03

**Opções.** As hipóteses do W-Z, ainda não implementadas (`pendencias.md:779–782`):

- **afinidade zero:** usar a seção do Moodle dos materiais ou aliases EN/PT antes do preenchimento pela ordem;
- **rótulo-cabeçalho:** distinguir cabeçalho da unidade anterior de conteúdo da seguinte;
- **bloco de duas unidades:** escopo por linha (W-Y) ou decisão por material.

São frentes possíveis, não alternativas de precedência bloco × texto. R1–R4 permanecem fechadas (`handoff:17–18`).

**Evidência medida**

- A unidade v2 está em **248/284**; o mínimo agregado é 256: faltam +8 no total, e as metas por curso exigem CG +11 e
  SO +4 (`handoff:33, 37, 39–41`).
- No W-Z, a melhor R1 deu 241 (+3/−10); R3/R4 ficaram em 237 (+1/−12). Todas reprovaram e reduziram a subunidade
  (`pendencias.md:763–765`).
- O W-Z classificou os 18 casos como origem 9, homogeneidade 6 e empate 3. Identificou o SO bloco-04 com 4 materiais
  u02 e 5 u03, além dos casos de afinidade zero e de rótulo-cabeçalho (`pendencias.md:770–778`).
- O W-Z2 refinou: **origem 5, homogeneidade 7, indeterminado 6**. O SO bloco-04 passou a homogeneidade; o SO bloco-06
  tinha gold de bloco u04, o que derruba a hipótese de +2 no SO. O oráculo ideal de bloco deu +4 em unidade e zero no
  CG e no SO. Isso mede potencial ideal, não o ganho de uma regra implementável (`pendencias.md:724–734`).
- Afinidade zero ocorre em 50/125 candidatos (40 %); o preenchimento sem sinal acertou 13/16, mas 0/2 nas fronteiras.
  Há sinal para investigar fronteiras, sem justificativa para eliminar o preenchimento indiscriminadamente
  (`pendencias.md:725–726`).

**O que destrava**

- afinidade zero: proposta delimitada de Gate 1 para origem em fronteiras e janelas, com sinais independentes do
  gold;
- rótulo-cabeçalho: esclarecer o contrato e a evidência de origem; não autoriza recuperar o antigo potencial de +2 no
  SO;
- duas unidades: definir escopo por linha/material e resolver as adjudicações pertinentes antes de desenhar mudança.

Nenhuma dessas escolhas demonstra, hoje, caminho para os déficits de CG e SO (`pendencias.md:44, 733, 779–782`).

**Recomendação.** Priorizar a proposta delimitada para **afinidade zero em fronteiras e janelas**, com o W-Z2 como
diagnóstico vigente; tratar cabeçalho e duas unidades primeiro como questões de contrato e adjudicação. Risco
residual: mesmo o oráculo ideal não atende CG e SO; o mecanismo real ainda precisa demonstrar ganho sem perdas.

### CRU-05

**Opções.** Os candidatos documentados (`2026-09-23-diag-identidade-e-cru05.md:83–89`):

- **normalização de acentos espaçadores:** compor ou remover os diacríticos sem inserir separador;
- **doador com evidência estrutural própria:** hipótese C2 do W-Z2; exige proposta e medição antes de qualquer regra.

Manter a propagação atual até existir candidato aprovado é sugestão do planejador. Desligá-la não foi autorizado nem
apresentado como solução nas fontes (`pendencias.md:46`).

**Evidência medida**

- A instrumentação reproduziu a base v2 por ID: 223/237, 248/284 e 86/251. A propagação produziu **+11/−4**, além de
  23 movimentos de erro para outro erro. Nos ganhos com termo acrescentado visível, 8/8 tinham doadores certos. Essa
  avaliação não pode virar seleção de doadores pelo gold (`diag:7–8, 45, 58–64, 78–81`).
- As 4 perdas têm causas diferentes (`diag:66–76`):
  - FR (2 materiais): `server`, propagado por 2 doadores, ambos errados;
  - TCC: `aveis`, fragmento produzido por acento espaçador; 3 dos 137 termos propagados são fragmentos desse tipo;
  - CG: `janela`, com doadores mistos; a classificação como perda depende da adjudicação da régua do CG.
- A normalização está ligada diretamente a 1 perda, mas a correção e os efeitos globais não foram medidos. O filtro
  estrutural também não foi medido e teria de preservar os 11 ganhos (`diag:83–89`).
- O defeito separado de identidade de `frases_topico` teve 0 decisões alteradas em 170 chamadas; não oferece ganho
  atual demonstrado (`diag:27–37`).

**O que destrava**

- normalização: Gate 1 de correção delimitada, teste vermelho e replay integral; toca a normalização compartilhada,
  além da 2ª passada;
- doador estrutural: primeiro a medição de discriminabilidade sem gold; só depois o desenho de regra;
- manter: preserva a base enquanto se decide; não encerra o CRU-05 nem remove as perdas registradas.

Qualquer integração continua sujeita a ganho positivo, zero perda, nenhum curso regredindo e replay integral
(`pendencias.md:46`).

**Recomendação.** Priorizar os **acentos espaçadores**, por haver causa concreta; deixar o doador estrutural como
investigação posterior, sem prometer filtro eficaz. Risco residual: a normalização pode afetar todo o motor;
recuperar a perda do TCC preservando os ganhos ainda precisa ser medido.

### B2 — Ordem sugerida de decisão

1. **#49:** reconhecer o commit e corrigir o tracker.
2. **CRU-02:** fixar a posição do regime e impedir que resultados VOCAB sejam contabilizados como cru.
3. **CRU-03:** escolher a frente de origem com o W-Z2 como referência, sem reabrir precedência.
4. **CRU-05:** selecionar o próximo passo delimitado.

O CRU-03 pode ajudar a unidade e algumas subunidades, mas o oráculo de bloco mostrou apenas +4/+2, sem ganho no CG e
no SO. O CRU-05 é independente da escolha VOCAB e não é caminho para o déficit de 140 subunidades. A adjudicação da
régua do CG condiciona a leitura de parte dos dois diagnósticos (`pendencias.md:733, 746`; `diag:50–51, 74–76`).

### B2 — Contradições encontradas

- **"SEM COMMIT" × git.** `pendencias.md:45, 995–999` mantém o estado anterior à entrega; o git confirma `410592d8`
  no branch e na referência local de `origin`. *[Coordenador: e o estado local registra o Gate 2 aprovado.]*
- **217/237 × 223/237; 246/284 × 248/284; 84/251 × 86/251.** O primeiro conjunto é o estado #47 + #48 + #49 sobre a
  base histórica; o segundo é a base v2, com a régua final e os materiais antes ausentes presentes. São bases
  diferentes. A contribuição isolada da importação e da régua para cada diferença não foi encontrada
  (`pendencias.md:1018–1019`; `handoff:28–39`).
- **Evolução histórica.** Unidade 239 → 244 (#47) → 246 (#48); bloco 213 → 214 (#48) → 217 (#49). Não atribuir o
  placar v2 inteiro à #49 (`pendencias.md:12, 44–45, 1018–1019`).
- **"Importar ausentes chega a 259".** O W-T apresentou 246 + 13 = 259 como cenário prospectivo; o tracker ainda repete
  essa direção no CRU-03, enquanto o handoff já registra os materiais presentes e o resultado 248/284. O cenário não
  é ganho realizado nem ação ainda disponível (`pendencias.md:44, 1131–1133`; `handoff:28, 39`).
- **W-AA "planejado" × "medido".** O bloco de desenho preserva pendências anteriores; execução, reprovação e Gate 2
  documental foram registrados depois. Não reabrir a execução já concluída (`pendencias.md:690–712, 665–681`;
  `handoff:20–21, 73–74`).
- **Origem 9 × origem 5.** O W-Z2 refinou a classificação pela evidência de bloco e retirou o potencial de +2 no SO;
  prevalece sobre a hipótese do W-Z (`pendencias.md:772–782, 727–734`).

### B2 — Limitações (do worker)

- Só os intervalos e relatórios autorizados foram consultados, além do git de leitura. Nenhum arquivo foi alterado;
  nenhum experimento ou replay foi executado.
- Os números são medições reportadas, não revalidadas. Não foram conferidos código, capturas, gold, estado remoto da
  issue ou da PR, nem integração na `main`. A referência de `origin` é local.
- O W-R excluiu entradas cacheadas das suas janelas e reexecutou a unidade só nos cursos cujo bloco mudou; esses
  limites permanecem (`pendencias.md:992–993`). Ganhos das propostas de origem, normalização e seleção estrutural
  continuam não medidos.

### B2.6 Conferência dos números pelo coordenador

Cada número da seção B2 foi conferido lendo a linha citada na fonte (árvore principal, somente leitura).

| item | fonte lida | resultado |
|---|---|---|
| meta > 90 % por eixo; histórico 213/237, 239/284, 84/251 | TRK:10, 12 | confere |
| CRU-02, CRU-03, CRU-04, CRU-05 no bloco `fila-campanhas` | TRK:43–46 | confere |
| MOTOR-9 / PR #9 | TRK:76–78 | confere |
| W-AA: S 83 (+1/−4), G 76 (+19/−29), G+S 73 (+20/−33), base 86 | TRK:671 | confere |
| teto 218/251 sem corrigir a unidade; 234/251 e CG 69/82 (84,1 %) com unidade oráculo | TRK:700, 740 | confere |
| W-Z2: 51/56 blocos; 50 de 125 sem sinal (40 %); preenchimento 13/16, fronteira 0/2; origem 5 / homogeneidade 7 / indeterminado 6; oráculo de bloco +4, 0 no CG e SO | TRK:724–734 | confere |
| W-Z: R1 241 (+3/−10); R3/R4 237 (+1/−12); 18 = origem 9 / homogeneidade 6 / empate 3; SO bloco-04 com 4 u02 + 5 u03 | TRK:763–765, 772–776 | confere |
| hipóteses (a), (b), (c) de origem do bloco | TRK:779–782 | confere |
| W-R: V0 214/237 e 246/284; V1 217/237, 3/0, imune 0/97; V0 18/97 | TRK:969–978 | confere |
| #49: aceite 11/11; 217/237 (91,6 %); 246/284; MF 54 → 56, IA 38 → 39; 16 mudanças de banda/flag; revisão Astra com 2 LOW; disambiguator 28/28; suíte 2410 / 4 / 1; diff 2 arquivos +67/−12 | TRK:997–1019 | confere |
| W-T: estado #49 reproduzido 217/237, 246/284; 246 + 13 = 259 | TRK:1114, 1131–1133 | confere |
| placar v2 por curso e total (223/237, 248/284, 86/251; mínimos 214/256/226; +8, CG +11, SO +4; +140) | HO:30–41 | confere |
| W-Z2 no handoff: 165 = 76 + 67 + 17 + 5; oráculo de unidade 86 → 92 (8 correções, 2 perdas) | HO:56–58 | confere |
| opções (a), (b), (c) da subunidade | HO:78–80 | confere |
| CRU-05: propagação +11/−4; 23 erro → outro erro; 8 ganhos com doadores todos certos; 137 termos propagados, 3 fragmentos; `server`, `aveis`, `janela` | DIAG:41–76 | confere |
| identidade `frases_topico`: 170 chamadas, 0 decisões mudariam | DIAG:27–37 | confere |
| commit `410592d8`: ancestral do HEAD e de `origin/feat/motor-atribuicao` (referência local); código +67/−12 em 2 arquivos | `git merge-base --is-ancestor`, `git show --stat` | **medido** pelo coordenador |
| Gate 2 da #49 aprovado em 22/09 ~12:23 | `.workflow/local/active-task-ate-20260930.md`, campo `gate_2_49` | **medido** (lido) pelo coordenador; o worker não tinha essa fonte |

**Não conferido:** estado da issue #49 e da PR #9 no GitHub (sem rede); se `origin` remoto ainda coincide com a
referência local (sem `fetch`); o conteúdo do commit `3c8f26d9` (W-AC, teto do cru por curso); os JSON e scripts por
trás de cada número (só os relatórios foram lidos).
