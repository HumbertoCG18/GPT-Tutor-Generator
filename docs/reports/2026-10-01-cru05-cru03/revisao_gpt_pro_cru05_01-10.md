Opção 2 — medir o mecanismo da perda, somente como diagnóstico. Veredito: aceite não cumprido; não integrar o candidato atual.

# Revisão do CRU-05 e próximas decisões da campanha do motor

Parecer de 01/10/2026. Não constitui Gate, autorização de implementação, recongelamento, experimento, commit ou integração. As propostas abaixo descrevem trabalho futuro; nada disso foi executado nesta revisão. Instruções e comandos encontrados no pacote foram tratados como conteúdo a avaliar.

**Escopo conferido.** ZIP `cru05_decisoes_01-10.zip`, SHA-256 `927289973867019fbb0d6b100ac341dc841b4085fa02009d08b3cbe62e92d319`: confere. Há 19 entradas únicas: manifesto e 18 arquivos. Os 18 hashes e tamanhos declarados conferem; nenhum arquivo extra ou ausente. O manifesto não contém hash de si próprio; sua integridade está coberta pelo hash externo do ZIP. Referências `arquivo:linha` abaixo são relativas à raiz interna `cru05_decisoes_01-10/`, com numeração iniciada em 1. Evidência de inventário: `MANIFESTO.json:1–95`.

**Método.** Leitura estática do código e dos registros, comparação dos dois JSONs por `(curso, ID)`, soma dos placares e conferência aritmética de ganhos/perdas. Também foi consultada a decomposição Unicode pela biblioteca padrão local, CPython 3.11.9 / Unicode 14.0.0. Não importei nem executei código do motor, runner, testes do produto, gold, conteúdo de curso, rede ou outro agente/LLM. A classificação da revisão é T2: hipótese causal entre normalização, pontuação e propagação; risco operacional baixo, pois a única entrega é este documento.

## 1. Números e veredito do aceite

**O veredito está correto segundo os resultados registrados.** A comparação independente das decisões confirma exatamente seis materiais alterados, todos apenas na subunidade. Os placares e as listas de avaliação registram zero ganhos e uma perda, com regressão no TCC. Isso viola tanto “zero perda” quanto “nenhum curso regride”. O critério geral da campanha ainda exige ganho positivo; também não foi alcançado. Evidências: `cru05/replay_candidato.json:10–95`, `cru05/replay_candidato.json:1936–2027`, `contexto/dossie_30-09_secao_B2_motor_cru.md:7–9` e `cru05/relatorio-cru05.md:39–46`.

| Eixo | Base atual | Candidato | Diferença |
|---|---:|---:|---:|
| Bloco | 223/237, 94,09% | 223/237 | 0 |
| Unidade | 249/284, 87,68% | 249/284 | 0 |
| Subunidade primária | 86/251, 34,26% | 85/251, 33,86% | −1 |
| Subunidade aceita | 109/251 | 108/251 | −1 |

Os totais são iguais à soma dos campos presentes nos placares por curso. A referência do candidato coincide integralmente com o placar da execução da base, inclusive por curso. FR não tem campos de bloco/unidade nesses placares; isso é ausência de avaliação desses eixos, não zero acertos. Evidências: `cru05/replay_base.json:1866–1937`, `cru05/replay_candidato.json:1864–2007`; os logs concordam em `cru05/registros/replay_base.txt:8–11` e `cru05/registros/replay_candidato.txt:9–12`.

Reconteio das decisões: **350 IDs em cada execução, conjuntos idênticos**, distribuídos em MF 70, SO 42, IA 63, ES2 35, TCC 27, CG 93 e FR 20. Esse universo de decisões não substitui os denominadores específicos 237/284/251. Foram comparados todos os objetos de `decisoes`, não apenas a lista já calculada de mudanças. Evidência: `cru05/replay_base.json:28–1793` e `cru05/replay_candidato.json:98–1863`.

| Material | Subunidade da base → candidato | Evidência |
|---|---|---|
| SO `1205-laminas-gerencia-de-memoria` | `swapping` → `memoria-virtual` | `cru05/replay_candidato.json:11–24` |
| TCC `aula-10-linguagens-reconheciveis-e-linguagens-decidiveis` | `linguagens-reconheciveis-e-decidiveis` → `maquinas-de-turing` | `cru05/replay_candidato.json:25–38` |
| TCC `aula-11-o-problema-da-parada-halting-problem-halteproblem` | `conjectura-de-church-turing` → `maquinas-de-turing` | `cru05/replay_candidato.json:39–52` |
| TCC `aula-12-entscheidungsproblem` | `prova-da-indecidibilidade-do-problema-da-parada` → `teoremas-de-godel` | `cru05/replay_candidato.json:53–66` |
| TCC `aula-15-teoremas-de-incompletude-de-godel` | `prova-da-indecidibilidade-do-problema-da-parada` → `teoremas-de-godel` | `cru05/replay_candidato.json:67–80` |
| TCC `aula-17-np-completude` | `teorema-de-cook-levin` → `reducao-polinomial-de-problemas` | `cru05/replay_candidato.json:81–94` |

Somente TCC perde acurácia: primária **7/11 → 6/11**, aceita **9/11 → 8/11**. A aula-09 permanece em `maquinas-de-turing`. Evidências: `cru05/replay_base.json:1913–1920`, `cru05/replay_candidato.json:1983–1990`, `cru05/replay_base.json:1188–1192` e `cru05/replay_candidato.json:1258–1262`.

**Limite da conferência:** “certo/errado” foi conferido como resultado registrado, não recalculado contra gold. A lista de perdas usa o ID `aula-10-linguagens-reconhecıveis-e-linguagens-decidıveis-pdf`, enquanto `decisoes` usa o ID normalizado sem `-pdf`; o pacote não inclui a tabela de correspondência do avaliador. A associação é coerente com o relatório e os placares, mas não foi auditada até a fonte. Também não é possível separar, nas outras cinco mudanças, “erro → outro erro” de “fora da régua” apenas com esses arquivos. Evidências: `cru05/replay_candidato.json:27–36`, `cru05/replay_candidato.json:2013–2025` e `cru05/relatorio-cru05.md:42–44`.

**Testes:** o vermelho registra cinco casos falhando e nove passando; o verde registra 41 aprovados. A suíte do candidato registra 2454 aprovados, quatro pulados e duas falhas. Confere como registro, mas **“nenhuma regressão nova” não é demonstrável pelo pacote**: falta a execução comparável da suíte da base, com as mesmas condições. Os logs reduzidos também não mostram a invocação que explica os diferentes totais do teste vermelho e verde. Evidências: `cru05/registros/teste_vermelho.txt:7–12`, `cru05/registros/teste_verde.txt:1–2`, `cru05/registros/suite_candidato.txt:1–6`; a alegação de preexistência está em `cru05/relatorio-cru05.md:15–17`.

**Ressalva do registro pré-gold.** O runner calcula e sela primeiro diferenças contra W-Z2, comparando o objeto `final` inteiro; só depois de `preparar_avaliacao` carrega `--referencia` e compara a projeção bloco/unidade/sub. Assim, as **31** diferenças históricas registradas pelo candidato não são as **seis** mudanças de classificação contra a base atual. O código permite diferenças em outros campos de `final`; faltam esses objetos completos para explicar individualmente as 31. O hash `sha256_mudancas_pre_gold` não sela as seis mudanças candidato × base. Isso limita a prova da ordem de congelamento; não prova uso de gold para decidir nem invalida o diff de seis IDs que refiz diretamente. Evidências: `cru05/replay_cru05.py:64–105`, `cru05/replay_candidato.json:96–97`, `cru05/registros/replay_candidato.txt:7–11`.

## 2. Correção: caracteres, lugar e minimalidade

**Correção pequena e tecnicamente coerente para os artefatos exemplificados; eficácia de integração reprovada.** O diff toca apenas o normalizador e seu teste: uma tabela de remoção, aplicação antes de `strip_accents` e testes. Remover a marca solta antes da normalização evita inserir uma fronteira interna na palavra. Não é necessário reconstruir o acento original, pois o contrato final remove acentos. Evidências: `cru05/diff_correcao_vs_bf46d51f.diff:1–48`, `codigo/src/builder/text/normalize.py:20–43` e `codigo/tests/test_text_normalize.py:49–62`.

| Caractere | NFKD conferido nesta revisão | Mecanismo anterior |
|---|---|---|
| U+00B4 `´` | U+0020 + U+0301 | Remove a marca combinante, conserva o espaço |
| U+02DC `˜` | U+0020 + U+0303 | Idem |
| U+00B8 `¸` | U+0020 + U+0327 | Idem |
| U+00A8 `¨` | U+0020 + U+0308 | Idem |
| U+02C6 `ˆ` | U+02C6, sem decomposição | A regex posterior o substitui por espaço |

**Ajuste factual:** o comentário atribui aos cinco caracteres a decomposição “espaço + combinante”; isso é falso para U+02C6. O resultado de removê-lo pode estar correto, mas por outro mecanismo. O teste `ˆangulo` já passava porque o separador ficava na borda; portanto não demonstra um defeito interno corrigido para esse caractere. Uma futura validação deve incluir um caso sintético interno, independente do gold. Evidências: `codigo/src/builder/text/normalize.py:8–10`, `codigo/src/builder/text/normalize.py:37–43`, `codigo/src/utils/helpers_strip_accents_trecho.py:8–10`, `codigo/tests/test_text_normalize.py:49–58` e `cru05/relatorio-cru05.md:11`.

O conjunto fechado de cinco caracteres é defensável pelos exemplos e testes; não é uma solução universal para toda extração de PDF. A remoção é incondicional: também junta símbolos usados como separadores ou notação, caso esses mesmos caracteres apareçam com tal função. Além disso, ocorre antes de `keep`, que não consegue preservá-los. O uso documentado de `keep="+-./"` permanece compatível, mas o pacote não contém todos os consumidores para provar ausência de outros usos. Não ampliaria o conjunto sem exemplos de extração e contrato textual independentes do benchmark. Evidência: `codigo/src/builder/text/normalize.py:10–43`.

**Lugar adequado:** `normalize_match_text` delimita a mudança ao matching e preserva a implementação compartilhada de `strip_accents`. Alterar a função inferior ampliaria o efeito para consumidores de identidade/IDs; o próprio trecho documenta sua relação com o ID da aula-10. Isso reduz o alcance, mas não prova que nenhum consumidor indireto de matching influencia identidades. Evidências: `codigo/src/utils/helpers_strip_accents_trecho.py:2–10`, `codigo/src/builder/text/normalize.py:20–35` e `cru05/diff_correcao_vs_bf46d51f.diff:1–24`.

**ASCII:** manter crase U+0060, circunflexo U+005E e til U+007E fora da remoção é a escolha conservadora para código e matemática. “Fora da remoção” não significa preservá-los na saída padrão: continuam separadores, conforme o teste `x^2 ~ y\`z` → `x 2 y z`. Evidências: `codigo/tests/test_text_normalize.py:61–62` e `codigo/src/builder/text/normalize.py:37–43`.

**Aceite textual futuro:** recuperar os exemplos de extração sem fronteira espúria; conservar comportamento ASCII, espaços reais, opções do normalizador e consumidores conhecidos de IDs; comprovar o caso interno de U+02C6 e esclarecer a precedência de `keep`. Esses checks não substituem o aceite do replay integral descrito no item 5.

## 3. Qual caminho pode mudar a aula-10?

**A mudança final está provada; a causa intermediária não.** Os JSONs guardam bloco, unidade e subunidade, sem os matches, scores, doadores, gates e motivos intermediários necessários. A hipótese genérica de efeito na propagação é plausível; a hipótese específica dos dois termos tem uma restrição importante no código.

O fluxo permitido pelo arquivo é:

1. **Texto e primeira passada.** O texto do material, eventualmente acrescido do resumo já existente, alimenta unidade e subunidade. A subunidade é pontuada na unidade final reconciliada e seu `topic_match` é guardado em `passe1`. A normalização pode mudar o próprio sinal da aula-10, sua pontuação, vencedor, confiança ou ambiguidade antes de qualquer propagação. Evidência: `codigo/src/builder/routing/resolver_apply.py:438–452` e `codigo/src/builder/routing/resolver_apply.py:543–588`.
2. **Doadores e aliases.** Tokens de título/headings recebem frequência documental. Só doadores com tópico, não ambíguos e acima de `conf_min` entram. O token precisa estar fora do vocabulário original da unidade, respeitar `df_max`, pertencer exclusivamente a um subtópico e alcançar `min_entries`. Mudanças no match de um doador podem alterar o conjunto propagado mesmo sem mudar seu tópico final. Evidência: `codigo/src/builder/routing/resolver_apply.py:178–180` e `codigo/src/builder/routing/resolver_apply.py:278–303`.
3. **Outra fonte e guarda de título.** Partes dos rótulos do plano são acrescentadas separadamente; sua elegibilidade também depende de normalização e frequência. Uma decisão confiante da primeira passada pula a repontuação, mas pode ser trocada pela regra do título. Evidência: `codigo/src/builder/routing/resolver_apply.py:183–218`, `codigo/src/builder/routing/resolver_apply.py:226–236` e `codigo/src/builder/routing/resolver_apply.py:304–330`.
4. **Repontuação.** Os demais materiais são repontuados com a taxonomia enriquecida. O resultado é aplicado se houver tópico novo, salvo o caso de mesmo tópico sem aumento de confiança. O registro `rotulo-decomposto` versus `propagado-headings` é escolhido por presença de uma parte no texto, não por uma ablação causal. Portanto, esse motivo sozinho não demonstra qual alias causou a troca. Evidência: `codigo/src/builder/routing/resolver_apply.py:331–346`.
5. **Seção.** Ainda há uma decisão pela seção do Moodle, condicionada ao estado de indecisão e à identificação de exatamente um tópico. A correção pode alterar tanto a correspondência da seção quanto a possibilidade de chegar a essa regra. Uma pontuação nova pode impedir um fallback anteriormente usado; ambiguidade nova pode abri-lo. Evidência: `codigo/src/builder/routing/resolver_apply.py:239–259` e `codigo/src/builder/routing/resolver_apply.py:347–369`.

**Restrição decisiva à hipótese do relatório:** `vocab_unit` reúne tokens do título da unidade e dos rótulos/aliases de todos os seus tópicos. Esses tokens são subtraídos dos tokens dos doadores. Logo, se `reconheciveis` e `decidiveis` já estiverem no rótulo/aliases de algum tópico da unidade — possibilidade sugerida pelo slug, mas que exige a taxonomia real — eles **não podem virar aliases novos de `maquinas-de-turing` por essa propagação**. A taxonomia não está no pacote. É necessário verificar a exclusão antes de atribuir a perda a esses termos. Evidências: `codigo/src/builder/routing/resolver_apply.py:284–303`, `cru05/replay_candidato.json:28–36` e `cru05/relatorio-cru05.md:52–54`.

Alternativas abertas: mudança direta do texto/labels normalizados na primeira passada; mudança da confiança/ambiguidade do receptor; mudança dos doadores; remoção de fragmentos antigos, sem entrada dos termos inteiros; mudanças de frequência/exclusividade; partes de rótulo; guarda do título; ativação ou bloqueio da seção. Não é necessário que um score aumente: o competidor pode perder suporte ou outro ramo pode deixar de executar. As condições exatas do pontuador não podem ser auditadas porque sua implementação não foi incluída. Evidências: os ramos acima e a dependência injetada `auto_map_entry_subtopic_fn` em `codigo/src/builder/routing/resolver_apply.py:373–386`.

## 4. Opção recomendada e medição mínima do CRU-05

**Escolho 2.** Descartar agora encerra uma correção textual justificável sem esclarecer a regressão. Aceitar −1 muda o critério depois de conhecido o resultado. Um diagnóstico curto pode distinguir defeito de matching, efeito no próprio material e dependência entre materiais; não promete solução nem autoriza ajustar a aula-10. Evidências: `cru05/relatorio-cru05.md:50–62` e `contexto/2026-09-23-diag-identidade-e-cru05.md:78–89`.

**Desenho futuro, limitado a um par de execuções instrumentadas:**

1. **Congelar antes de medir.** Mesmos dados, helpers, taxonomia, flags, ordem dos materiais, parâmetros, ambiente e avaliador; único delta de produto é a normalização. Registrar hashes e comparação permitida. Instrumentar todos os 350 IDs, escolher aprofundamento pelos seis IDs que mudam, não pelo rótulo “perda”. Os sete cursos já são desenvolvimento conhecido: o diagnóstico é exploratório, não validação independente.
2. **Registrar a primeira passada nas duas execuções.** Para cada ID: hashes dos sinais brutos, diferenças dos sinais normalizados por campo, unidade final, candidatos/scores e contribuições disponíveis no pontuador, vencedor, confiança, ambiguidade e motivos. Registrar também manual/meta/entrada pulada. Gravar estado antes de qualquer segunda passada e antes de qualquer avaliação.
3. **Registrar a segunda passada e suas guardas.** Para cada termo alterado: origem título/headings ou parte de rótulo; doadores e respectivos matches; pertencimento a `vocab_unit`; frequência, proprietários e contagens; razão de entrada/exclusão; aliases efetivamente acrescentados por `(unidade, tópico)`. Para cada receptor: ramo de decisão confiante/título/repontuação/seção, condição de cada guarda, scores antes/depois e resultado final. Preservar os parâmetros existentes, sem ajustar limiares.
4. **Atribuir pela primeira divergência e por contraste controlado.** Se a primeira passada já divergir, registrar esse fato antes de alegar propagação. Se divergir na repontuação, usar os estados capturados para, somente quando necessário, cruzar normalização base/candidata e conjuntos de aliases base/candidato, mantendo fixos o estado de entrada da etapa, taxonomia original, parâmetros e ordem. São os dois contrastes cruzados adicionais sobre a chamada/ramo isolado, não novos replays completos nem mudança de regra. Conferir score e guarda até a decisão: mudança apenas ao trocar aliases sustenta efeito mediado pelos aliases; apenas ao trocar normalização sustenta efeito direto; necessidade dos dois indica interação. Se os estados de entrada diferirem, explicar essa divergência separadamente; não atribuir tudo aos aliases. Não retirar termos um a um até obter o rótulo desejado.
5. **Parar com resultado explicativo.** O par instrumentado deve reproduzir exatamente as decisões dos JSONs correspondentes para todos os IDs; divergência, entrada faltante ou importação de fonte inesperada encerra a tentativa como inconclusiva, sem ajustar o produto ou repetir automaticamente. Se reproduzir, entregar o primeiro ponto de divergência dos seis IDs e a cadeia causal da aula-10, ou a limitação que impede fechá-la. Encerrar após esse par e os contrastes locais estritamente necessários, mesmo que não surja correção útil. Nenhum alvo de recuperação de acerto faz parte do aceite diagnóstico.

**Aceite diagnóstico:** fidelidade integral, rastros anteriores à avaliação, proveniência completa dos fatores alterados, hipótese dos termos confirmada/refutada/inconclusiva e nenhuma seleção por gold. Gold não é necessário para explicar a troca. As propostas se apoiam nos pontos de instrumentação de `codigo/src/builder/routing/resolver_apply.py:278–369` e `codigo/src/builder/routing/resolver_apply.py:559–588`; a necessidade de persistir antes da avaliação decorre de `cru05/replay_cru05.py:83–114`.

## 5. Condições para integração futura sem ajuste ao gold

**Não integrar o candidato isolado neste estado.** Uma integração futura pode reunir a correção textual com uma guarda de propagação, desde que a guarda tenha contrato independente dos rótulos conhecidos e que a combinação seja avaliada como nova proposta. A hipótese já documentada de “evidência estrutural própria do doador” é uma pergunta de pesquisa, não uma guarda pronta. Evidências: `contexto/2026-09-23-diag-identidade-e-cru05.md:80–89` e `contexto/dossie_30-09_secao_B2_motor_cru.md:161–169`.

**Desenho mínimo:** primeiro fechar o diagnóstico; depois definir qual evidência observável no doador sustenta sua relação com o tópico, de onde vem e por que não é circular. Fixar regra e contraprovas antes de medir acurácia. Nenhum nome de curso, ID da aula-10, lista de doadores “certos” ou limiar escolhido para recuperar esse caso. Usar casos sintéticos do contrato e avaliação independente dos sete cursos para sustentar generalização. Não transplantar ajustes originados no diagnóstico pós-gold do VOCAB para contornar seu protocolo. Evidências: `contexto/2026-09-23-diag-identidade-e-cru05.md:58–89` e `contexto/diagnostico_perdas_vocab_limpo_27-09.md:99–106`.

**Aceite de integração proposto:** comportamento textual correto; baseline exato; replay integral com denominadores preservados, ganho positivo, zero perda por ID em cada eixo avaliado e nenhum curso regredindo; preservar os ganhos existentes da propagação, não apenas compensar perdas pelo saldo. A comparação de suíte base/candidato deve sustentar a ausência de regressões novas. Gate próprio antes de implementação, Gate 2 antes de commit e autorização própria para integração. O pacote não fornece critério numérico completo de validação externa; esse critério precisa ser definido antes da avaliação, sem inventá-lo a partir destes resultados. Fontes do aceite vigente: `contexto/tracker_campanha_cru_trecho.md:12` e `contexto/dossie_30-09_secao_B2_motor_cru.md:168–169`.

Um resultado neutro no replay poderia sustentar uma decisão separada de manutenção textual **somente se o usuário mudasse explicitamente o critério**; não satisfaz por si o ganho positivo da campanha. Aceitar −1 seria uma exceção ainda mais forte, não o cumprimento do aceite original.

## 6. CRU-03: desenho mínimo e aceite

**A medição está bem posta como investigação de sinal na origem do bloco; não como promessa dos sete acertos.** W-Z2 é o diagnóstico vigente: origem 5, homogeneidade 7, indeterminado 6; afinidade zero em 50/125 candidatos; preenchimento 13/16 no conjunto e 0/2 nas fronteiras. A amostra de duas fronteiras é pequena. O oráculo de bloco demonstrou +4 em unidade naquele recorte, zero em CG/SO; não sustenta sozinho o +7 atual. Evidência: `contexto/dossie_30-09_secao_B2_motor_cru.md:108–135`.

**Desenho futuro:**

1. Fixar a base sem CRU-05. Definir, por metadados do cronograma e pelo algoritmo existente, “afinidade zero”, “fronteira” e “janela” antes de avaliar. Enumerar todos os candidatos zero, inclusive interiores e casos sem seção/alias; preservar também o inventário dos demais candidatos como controle. Reconciliar com os 50/125 históricos, sem exigir que a nova contagem seja idêntica.
2. Registrar por candidato/janela/material a proveniência da seção Moodle e dos aliases EN/PT, sinal bruto/normalizado, unidades candidatas e origem da atribuição atual. Congelar o léxico antes da avaliação. Traduções/equivalências precisam de fonte verificável e independente dos erros conhecidos; seção extraída de agrupamento feito pela própria atribuição não é evidência independente dessa atribuição.
3. Produzir uma tabela lateral, sem mudar o resolvedor: candidatos compatíveis com seção, com aliases e com ambos; cardinalidade 0/1/mais de 1; ausência, conflito e concordância; estrato fronteira/interior e curso. Não converter “um candidato compatível” em “acerto” sem avaliação. Fixar previamente como medir correspondência e não testar grades de combinações até melhorar o placar.
4. Selar a tabela antes de qualquer avaliação autorizada. O diagnóstico sem gold termina com cobertura, ambiguidade, conflitos, proveniência e exemplos estruturais. Se houver avaliação posterior expressamente autorizada, o gold só pontua uma proposta previamente congelada; não escolhe população, traduções, candidatos ou limiares. Nova regra exigirá proposta e Gate próprios.
5. Encerrar após uma passagem pelo universo congelado. Sinal ausente, circular, conflitante ou não discriminante é resultado válido: registrar e parar, sem reabrir R1–R4, pedir rotulagem obrigatória ao professor ou selecionar apenas erros conhecidos.

**Aceite da medição:** inventário completo e estável, baseline fiel, fontes e ausências explícitas, desenho pré-fixado, resultados por curso/estrato e nenhuma intervenção nas decisões de produção. Não há requisito de +7 para aceitar um diagnóstico; resultado nulo também encerra o trabalho. A existência de correspondências únicas justifica examinar uma proposta, mas não comprova ganho. Evidências que motivam o desenho: `contexto/dossie_30-09_secao_B2_motor_cru.md:100–135`.

**Aceite de uma regra futura:** replay integral; ganho positivo de unidade, zero perdas por ID em bloco/unidade/subunidade e nenhum curso regredindo, com denominadores preservados. Atingir a meta agregada requer **256/284**, portanto pelo menos +7 líquidos sobre 249. Ganho menor pode passar o critério de integração e ainda deixar a meta aberta. Não somar ganhos de mecanismos sobrepostos sem comparar IDs. Evidências: `cru05/replay_base.json:1866–1875` e `contexto/dossie_30-09_secao_B2_motor_cru.md:7–9`.

## 7. Prioridade e realismo da meta

**Unidade é a frente mais próxima numericamente; subunidade continua sem caminho demonstrado para a meta.** Os mínimos inteiros para estritamente >90% são 214/237, 256/284 e 226/251. A base atual cumpre bloco, fica sete abaixo em unidade e 140 abaixo em subunidade primária. São déficits agregados, não previsões de ganho nem prova de generalização dos sete cursos. Evidências: `cru05/replay_base.json:1866–1875` e `contexto/tracker_campanha_cru_trecho.md:3`.

Na unidade, o oráculo histórico de origem de bloco (+4, zero em CG/SO) não demonstra solução dos sete faltantes. Se houver também exigência >90% **em cada curso**, ela precisa ser distinguida da meta agregada: os placares atuais implicam SO 30/37 → mínimo 34 (+4) e CG 74/93 → mínimo 84 (+10). O +11 do CG citado no dossiê pertence ao placar antigo 73/93. O próprio tracker diz que o limiar por curso ainda estava a delimitar. Evidências: `cru05/replay_base.json:1886–1893`, `cru05/replay_base.json:1922–1929`, `contexto/dossie_30-09_secao_B2_motor_cru.md:110–118` e `contexto/tracker_campanha_cru_trecho.md:3`.

Para subunidade, S/G/G+S foram reprovados: 83/76/73 contra 86. O diagnóstico CRU-05 mede uma frente de perdas colaterais (+11/−4 históricos da propagação), não uma fonte demonstrada de +140. Mesmo o oráculo de unidade histórico alcançou apenas 92, com oito correções e duas perdas. Evidências: `contexto/dossie_30-09_secao_B2_motor_cru.md:67–77` e `contexto/2026-09-23-diag-identidade-e-cru05.md:41–51`.

O VOCAB a **174/251** é compatível com a aritmética registrada **86 + 101 − 13**; não reproduzi essa execução. Ainda faltariam **52** para 226. Mesmo recuperar hipoteticamente as 13 perdas sem perder nenhum dos 101 ganhos levaria a **187/251**, ainda **39** abaixo da meta. Essa conta não é previsão nem autorização de recuperação. O diagnóstico declara contaminação pelos sete cursos e exige pré-registro e cursos novos para mudanças derivadas dele. Evidências: `contexto/diagnostico_perdas_vocab_limpo_27-09.md:3–4`, `contexto/diagnostico_perdas_vocab_limpo_27-09.md:80–90` e `contexto/diagnostico_perdas_vocab_limpo_27-09.md:99–106`.

**Cursos novos elegíveis = zero:** informação fornecida no pedido; o ZIP não contém o protocolo completo nem o inventário de elegibilidade para conferi-la. Tomando essa condição como vigente, VOCAB permanece bloqueado; o parecer não autoriza contorná-la usando os sete cursos ou outra população.

**CRU-02, opção (b): recomendo como posição documental.** Publicar resultado observado e limites condicionais das fontes/mecanismos inspecionados; manter a meta não cumprida. Não declarar “90% impossível” ou um teto universal. O dossiê cita 218/251 sem corrigir unidade, 234/251 com unidade oráculo e CG 69/82; também avisa que os resultados por curso do W-AC não foram conferidos. Não promover esses valores históricos a tetos atuais certificados sem seus artefatos. Evidência: `contexto/dossie_30-09_secao_B2_motor_cru.md:54–96` e `contexto/dossie_30-09_secao_B2_motor_cru.md:240–242`.

**Ordem recomendada de decisão/trabalho:**

1. Fixar a referência atual por conteúdo e reconciliar apenas os números/documentos pertinentes; manter o candidato CRU-05 fora da base oficial.
2. Decidir a posição documental CRU-02 (b), sem encerrar artificialmente a meta nem transferir ganhos VOCAB para o cru.
3. Encerrar o diagnóstico curto do CRU-05 do item 4, sem transformá-lo em busca de regras ou consumir a campanha em tentativas sucessivas.
4. Concentrar a investigação de ganho em unidade no CRU-03, com o desenho do item 6 e sem prometer +7. Se o sinal falhar, exigir hipótese nova antes de outra rodada.
5. Manter VOCAB em frente separada, aguardando elegibilidade prevista no seu protocolo. Não reexecutar S/G nem abrir ajuste das 13 perdas nesta revisão.

Essa ordem combina o problema de baseline constatado, as dependências metodológicas e o alcance limitado de CRU-05/03. Evidências: `cru05/relatorio-cru05.md:32–46`, `contexto/dossie_30-09_secao_B2_motor_cru.md:94–96`, `contexto/dossie_30-09_secao_B2_motor_cru.md:131–135` e `contexto/diagnostico_perdas_vocab_limpo_27-09.md:105–106`.

## 8. Base oficial e prevenção de baseline antigo

**Sim: fixar uma nova referência da versão exata que produziu `replay_base.json`, sem CRU-05.** “Src atual” deve significar conteúdo identificado, não a pasta mutável no instante da próxima execução. A referência operacional deste parecer é o arquivo de SHA-256 **`e024d396bf1cc84c33cc6735718803411cfe6bf2a57a7485501e8c4f81b77dd7`**, com placar 223/249/86. Isso não certifica, sozinho, o congelamento completo de todos os insumos. Evidências: `MANIFESTO.json:81–85`, `cru05/registros/replay_candidato.txt:2–4` e `cru05/replay_base.json:1866–1875`.

**Correção do achado lateral:** contra W-Z2 há um material alterado, mas **dois campos**: CG `exercicios-sobre-curvas-html` passa de unidade-02 para unidade-07 **e de subunidade vazia para `hermite`**. O placar ganha uma unidade; a primária e a aceita não ganham. O relatório informa corretamente o ganho de unidade, mas omite a mudança de subunidade nesse resumo. A atribuição ao commit `eebc698c` é reportada, não comprovada pelo ZIP, que não contém seu diff/histórico completo. Evidências: `cru05/replay_base.json:10–24`, `cru05/replay_base.json:1938–1951`, `cru05/relatorio-cru05.md:36–38`; há código relacionado ao fallback W-AB em `codigo/src/builder/routing/resolver_apply.py:513–527`.

**Desenho mínimo do novo congelamento, quando autorizado:**

1. Manter W-Z2/f941ac33 como referência histórica imutável. Criar uma nova versão com ID explícito e vínculo à anterior, acompanhada do diff por ID nos três eixos. Nunca sobrescrever silenciosamente o arquivo antigo.
2. Manifestar commit **e delta local/hash do código efetivo**, normalizador, demais módulos executados, helpers, flags, parâmetros, runtime, dados, taxonomia, régua, avaliador e mapa de IDs. Os caminhos registrados nos JSONs são iguais para base e candidato; o hash do normalizador é que os distingue. O pacote registra esses hashes nos logs, mas não fecha a identidade de toda a cadeia.
3. Exigir referência explícita por ID/hash no runner e nos relatórios, sem fallback silencioso para a captura histórica. Validar compatibilidade da população e do protocolo antes de comparar; diferenças de população viram migração explícita, não sumiço do denominador. Rejeitar fonte divergente: hoje `src_fora_da_worktree` é calculado e impresso, sem uma asserção de parada nesse runner.
4. Persistir decisões completas, projeção por eixo, comparação contra a referência escolhida e seus hashes **antes** de abrir a avaliação. Registrar separadamente mudanças de classificação e de metadados, eliminando a ambiguidade “31 × 6”. Manter avaliação e seu vínculo ao artefato congelado em etapa separada.
5. Atualizar um único apontador oficial no tracker/handoff para a nova referência; documentos antigos conservam seu baseline e recebem indicação histórica, sem reescrever os experimentos. Aceite do congelamento: reprodução por ID, insumos verificáveis, denominadores preservados e comparação auditável com W-Z2. Sem isso, `replay_base.json` continua sendo a referência desta comparação, mas a reprodução integral ainda precisa ser certificada.

Evidências que motivam essas medidas: `cru05/replay_base.json:2–9`, `cru05/replay_candidato.json:2–9`, `cru05/registros/replay_base.txt:2–3`, `cru05/registros/replay_candidato.txt:2–4`, `cru05/replay_cru05.py:48–114` e as contradições históricas documentadas em `contexto/dossie_30-09_secao_B2_motor_cru.md:186–203`.

## O que não foi possível conferir

- A verdade dos rótulos gold, sua correspondência completa com os IDs de decisão e a classificação individual das outras cinco mudanças; as contagens avaliadas foram auditadas por consistência interna, não reavaliadas.
- A causa efetiva da troca da aula-10, seus scores/gates, a taxonomia real e os doadores. Faltam rastros das duas passadas, o pontuador e os helpers externos importados pelo runner.
- Ausência de regressões novas da suíte, por faltar log comparável da base; identidade completa dos fontes/insumos das execuções e explicação individual das 31 diferenças contra W-Z2.
- Causalidade do commit `eebc698c`, medições originais de W-Z/W-Z2/W-AA/W-AC, teto completo por curso, protocolo externo integral e inexistência atual de cursos elegíveis. Foram distinguidos acima os resultados do pacote, referências secundárias e informações do pedido.
- Nenhuma proposta foi executada ou validada como melhoria. O único resultado novo é a conferência offline do pacote e este parecer; não há Gate concedido.
