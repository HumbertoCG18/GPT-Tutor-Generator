# Brief para segunda opinião (Codex astra, read-only) — 17 contradições de UNIDADE: gold por bloco × gold por material, 2026-09-12

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`. Suas revisões de 11 e 12/09 (estado da C1, gold do CG, regressão de unidade) já
estão incorporadas.

## 1. A pergunta

C5 (dívidas de dados) abriu hoje; item 1 é adjudicar 17 materiais em que duas fontes de gold de UNIDADE discordam. O usuário
disse: **"material_gt faz mais sentido, delega o astra para verificar"**. Você verifica: a inclinação dele se sustenta? O que
muda na régua e no motor se ela valer?

As duas fontes:
- **Gold por bloco** (o que a régua lê hoje): `tests/fixtures/eval/gold_units_<sig>.csv` dá a unidade verdadeira de cada BLOCO
  temporal (aula datada do SARC/Moodle); `docs/reports/ground_truth_<sig>.csv` dá o bloco verdadeiro de cada material; a
  unidade do material = unidade do seu bloco (`scripts/eval_entry_unit.py::_load_truth`, l. 63; `scripts/eval_eixos.py:64`
  diz literalmente "UNIDADE (gravada vs verdade = unidade do bloco verdadeiro)"). Semântica: **quando o professor deu a aula.**
- **Gold por material** (`docs/reports/material_gt_<sig>.csv`, coluna `gold_units`, rulings do usuário de 18-31/08): a unidade
  a que o CONTEÚDO pertence pelo plano de ensino ou por ruling explícito. Semântica: **onde o plano põe o assunto.**
- Desde 12/09 `_load_truth` cai para `material_gt` só em curso SEM gold por bloco (CG). Nos 5 cursos com os dois, o bloco manda
  e o `material_gt` é ignorado; medido: discordam em 16 materiais (+1 do MF que só tem `material_gt`).
- **O gold de unidade do CG, aprovado ontem (93 materiais), foi rotulado pela SEÇÃO do Moodle e pelo plano de ensino**, isto é,
  pelo conteúdo/estrutura do professor, não pela data do bloco. Se a régua do CG é "conteúdo" e a dos 5 cursos é "data", a
  régua de unidade tem duas semânticas hoje.

Lei do projeto (handoff §8): "SARC e Moodle acima do gold". Aqui as duas fontes são do professor: o plano (conteúdo) e o
cronograma (data). O motor decide unidade pelo bloco por desenho ("bloco vence"; o texto discordante fica gravado em
`unit_block_conflict` para auditoria).

## 2. As 17 linhas (MEDIDO, `docs/reports/contradicoes_unidade_material_gt_vs_bloco.csv`; o produto segue o bloco em todas)
```
curso material                                    secao Moodle                              bloco     u_bloco (gold)   u_material (gold)  nota do material_gt
MF  eth2                                         (bibliografia, sem secao)                 bloco-01  u01 metodos      u02 verificacao    propagado de coverage_gt_MF; CONFIRMADO ruling user 2026-08-31: u02
MF  aws-encryption-sdk                           (bibliografia, sem secao)                 bloco-01  u01 metodos      u02 verificacao    idem
MF  t1-2026-1                                    TDE Trabalho Discente Efetivo             bloco-11  u02 verificacao  u01 metodos        proposto-claude 19/08: enunciado 'Provas por Inducao de Especificacoes Equacionais Recursivas' = u01
MF  t1-2026-1-thy                                TDE Trabalho Discente Efetivo             bloco-11  u02 verificacao  u01 metodos        idem
MF  t2-2026-1                                    TDE Trabalho Discente Efetivo             bloco-20  (sem gold)       u02 verificacao    proposto-claude 19/08: enunciado cita 'dafny' e 'invariante' = u02 (produto: u03)
SO  0704-laminas-comunicacao-e-sincronizacao     Sincronizacao e Comunicacao de Processos  bloco-06  u04 deadlock     u03 concorrente    plano-de-ensino 18/08: topico 4.2 Comunicacao e sincronizacao na u03
SO  0904-laminas-semaforos                       Sincronizacao e Comunicacao de Processos  bloco-06  u04 deadlock     u03 concorrente    idem
SO  0704-exemplo-threads-em-java                 Threads                                   bloco-06  u04 deadlock     u03 concorrente    plano-de-ensino 18/08: topico 4.1 Programas multithreads na u03
SO  3103-threads                                 Threads                                   bloco-04  u02 processador  u03 concorrente    idem
SO  biblioteca-em-c-pthread                      Threads                                   bloco-04  u02 processador  u03 concorrente    idem
SO  exemplo-threads-em-c-exemplo1                Threads                                   bloco-04  u02 processador  u03 concorrente    idem
SO  exemplo-threads-em-c-exemplo2                Threads                                   bloco-04  u02 processador  u03 concorrente    idem
SO  exemplo-threads-em-c-exemplo3                Threads                                   bloco-04  u02 processador  u03 concorrente    idem
ES2 microsservicos5                              Microsservicos                            bloco-08  u02 integracao   u01 arquitetura    ruling-user 19/08: a serie de microsservicos cobre a unidade que fala de microsservicos (u01)
ES2 microsservicos7                              Microsservicos                            bloco-09  u02 integracao   u01 arquitetura    idem
ES2 azure                                        Microsservicos                            bloco-09  u02 integracao   u01 arquitetura    idem
ES2 microsservicos4                              Microsservicos                            bloco-07  u02 integracao   u01 arquitetura    idem
```
Blocos envolvidos (índice do produto): MF bloco-01 02/03 "disciplina" (u01, conf 0,4) · bloco-11 06/05 "lógica programas correção
parcial total terminação invariantes laço" (unidade vazia no índice) · bloco-20 06/07 "entrega" (vazia) · SO bloco-04 19 a 31/03
"gerência processador processos chamadas sistema escalonamento threads" (u02, conf 0,8) · bloco-06 07 a 09/04 "gerência processador
sincronização deadlock" (u04, conf 1,0) · ES2 bloco-07 15/05 "microserviços spring circuit breaker" (u02, conf 1,0) · bloco-08 22 a
29/05 "implantação microserviços contêineres" (u02, 0,6) · bloco-09 05/06 "comunicação" (u02, 1,0).

Plano de ensino (tópicos citados): SO u02 gerência do processador = 3.1 Conceitos básicos · 3.3 Algoritmos de escalonamento; **u03
programação concorrente = 4.1 Programas multithreads · 4.2 Comunicação e sincronização de processos**; u04 deadlock = 5.1 a 5.4.
ES2 u01 arquitetura de software = 1.1 a 1.5 (1.3.4 Orientada a Microsserviços; 1.5 Estudo de caso: arquitetura orientada a
microsserviços); u02 integração de desenvolvimento = 2.1 DevOps · 2.2 Configuração · 2.3 CI · 2.4 CD · 2.5 Monitoramento · 2.6
Plataformas · 2.7 Estudo de Caso: implantação. MF u01 métodos formais = 1.1 a 1.3 (1.2.3 Especificação de Funções Recursivas;
1.3.3 Provadores de Teoremas); u02 verificação de programas = 2.1 Lógica de Hoare (2.1.3 Invariante e Variante de Laço) · 2.2
Softwares de Suporte; u03 verificação de modelos.

## 3. O que o motor já diz (MEDIDO, `unit_block_conflict` no manifest)

Em **11 das 17** o produto registrou conflito texto × bloco, e o texto queria exatamente a unidade do `material_gt`: MF t1 ×2 e
t2; SO lâminas-comunicação, exemplo-threads-java, 3103-threads, biblioteca-pthread, exemplo-threads-c ×2; ES2 microsservicos7 e
microsservicos4. Nas outras 6 (MF eth2/aws, SO semáforos e exemplo3, ES2 microsservicos5 e azure) não há conflito gravado.

Item 2.3 do plano (medido 11/09 e 12/09 contra o gold POR BLOCO): "bloco vence" acerta 34/35 dos conflitos com gold; texto 1.
**Se `material_gt` vencer nas 17, esses 11 viram "texto certo": bloco 23/35, texto 12/35.** As alavancas "texto vence o bloco por
confiança" (gate 0,6 a 0,95: −17 a −2) e "texto vence se bloco conf ≤ 0,4" (+1/−1), refutadas em 05/09, foram medidas contra o
mesmo gold por bloco: a refutação é parcialmente circular.

Régua de unidade nos 5 cursos hoje: 190/190 com o gold por bloco; **com `material_gt` vencendo nas 16 que têm gold por bloco:
174/190 (91,6%)**, porque o produto segue o bloco em todas. Régua total com o CG: 274/278 → 258/278.

## 4. Perguntas, em ordem

1. **Semântica.** Para o produto (um tutor que navega pelas unidades do plano), a unidade do material é "onde o plano põe o
   assunto" ou "quando o professor deu a aula"? Há terceira leitura (as duas valem, gold com `|`)? O CG já está rotulado por
   conteúdo; os 5 cursos por data: qual das duas a régua deve adotar para os 8, e o que fazer com a outra?
2. **As 17, família a família.** SO threads/sincronização (8): o plano é explícito (4.1, 4.2 em u03), o professor deu nas aulas
   de u02/u04. ES2 microsserviços (4): ruling do usuário de 19/08, seção do Moodle "Microsserviços", blocos de u02 (DevOps). MF
   eth2/aws (2): bibliografia sem seção, bloco-01 "disciplina", ruling do usuário de 31/08 = u02. MF t1 ×2 e t2 (3): entregas
   (TDE) em blocos sem unidade; enunciado aponta u01/u02. Em cada família, qual lado a evidência sustenta, e qual é fraco?
3. **Se `material_gt` vence: o que muda no motor.** "Bloco vence" deixa de ser 34/35. Que regra medível teria chance (texto vence
   quando a seção do Moodle nomeia um tópico cujo plano está noutra unidade; ou quando o material é código/lista e o bloco é de
   outra unidade), e qual é o risco de repetir a refutação circular de 05/09? Sequência: adjudicar → régua → medir regra no
   replay → só então código?
4. **Se o bloco vence: o que fazer com `material_gt`.** Os rulings de 18-31/08 viram nota histórica? Como evitar que a mesma
   contradição volte em curso novo?
5. **Régua.** `_load_truth` hoje: bloco manda, `material_gt` só sem bloco. Que precedência é honesta depois da adjudicação
   (material_gt manda onde existe; bloco preenche o resto)? O que isso faz com os 16 materiais e com a comparabilidade com 08/09?
6. **Risco.** O que nesta análise pode estar errado: o "texto queria" do motor como evidência (é o próprio motor), a nota
   "proposto-claude" como fonte, a contagem 11/17, a leitura do plano de ensino.
