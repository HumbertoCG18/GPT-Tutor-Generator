# Briefing para segunda opinião — motor de atribuição do GPT-Tutor-Generator

Data: 2026-09-10. Este documento é autocontido: quem o lê não conhece o projeto. Tudo que está aqui foi medido, com o
número ao lado; onde é hipótese, está escrito "hipótese". Ao final está a pergunta que estamos fazendo.

**O que esperamos de você:** não implementar. Queremos análise e plano: o que poderia melhorar, o que tiraria o gargalo,
o que resolveria o problema de vez, e o que você faria diferente do que fizemos. Se discordar de alguma conclusão
nossa, diga qual e por quê.

---

## 1. O que é o projeto

O **GPT-Tutor-Generator** gera, para cada disciplina de graduação, um "tutor": um repositório organizado com todos os
materiais que o professor publicou (slides, listas, código, vídeos, provas), cada material classificado em três eixos
para que um aluno (ou um assistente de IA) consiga navegar o curso pela estrutura do plano de ensino.

Os três eixos, do mais grosso ao mais fino:

| eixo | o que é | de onde vem a estrutura |
|---|---|---|
| **bloco** | um trecho contíguo do cronograma: uma ou mais aulas datadas sobre o mesmo tema | SARC (sistema institucional de cronograma) |
| **unidade** | uma unidade do plano de ensino ("Unidade 02 — Gerência de Memória") | plano de ensino |
| **subunidade** | um tópico numerado dentro da unidade ("2.3 Paginação", "1.3.4 Orientada a Microsserviços") | plano de ensino |

O material chega pelo **Moodle** (LMS), organizado em **seções** (o professor chama de cards), com **label** por
material (ex.: "21/05 Lâminas: Paginação") e às vezes datas no label ou no nome.

**O usuário-alvo é um aluno que só faz login.** Ele não vai anotar nada, não vai criar referência, não vai curar. Tudo
que o motor precisa tem de vir do que o professor já publicou: plano de ensino, cronograma do SARC, e o Moodle.

**Regime de custo:** o projeto quer o mínimo possível de chamadas a LLM. LLM é aceito como camada opcional e
barata (poucas chamadas por curso, cacheadas), nunca como decisor por arquivo.

Oito cursos estão gerados (siglas usadas no texto): Métodos Formais (MF), Sistemas Operacionais (SO), Inteligência
Artificial (IA), Engenharia de Software 2 (ES2), TCC, Computação Gráfica (CG), Laboratório de Redes (LR), Fundamentos
de Redes (FR). **348 materiais** ao todo. Stack: Python, determinístico, com um cliente Gemini opcional.

---

## 2. Como o motor decide cada eixo

### 2.1 Bloco
Uma cascata de "providers" tenta reduzir os ~20–30 blocos do cronograma a uma **janela** de candidatos para cada
arquivo, usando sinais estruturais: data no label do Moodle, data no nome do arquivo, ordinal ("Aula 17"), tópico do
card casando com o rótulo de uma aula, prazo de entrega. Janela de 1 bloco decide direto. Janela maior passa por um
**desempate léxico** (tokens do arquivo × rótulos das aulas do bloco). Se o desempate fica sem margem, o arquivo é
**flagado** e, se o voter estiver ligado, um **LLM vota dentro da janela** (uma chamada por arquivo flagado, cacheada
por hash do conteúdo, teto de 20 chamadas por rodada).

Distribuição real de quem colocou cada arquivo no bloco (348 materiais):

| provider | n | % |
|---|---|---|
| **voto de LLM** | **96** | **28%** |
| tópico do card | 80 | 23% |
| labels datados do card | 58 | 17% |
| ordinal "Aula N" | 26 | 8% |
| data no nome | 23 | 7% |
| LLM sem janela (funil) | 16 | 5% |
| outros (prep-prova, irmão no card, referência genérica, prazo, manual) | 49 | 14% |

### 2.2 Unidade
**A unidade é herdada do bloco.** O cronograma vira blocos; um alinhamento posicional (programação dinâmica monotônica
na ordem do plano) liga cada bloco-aula a uma unidade por afinidade de tokens entre os rótulos das aulas e o
título+tópicos da unidade. O arquivo herda a unidade do bloco onde caiu. Existe um scorer de texto para unidade, mas
**ele não decide**: se discorda do bloco, o bloco vence e o desacordo é gravado como `unit_block_conflict` para
auditoria. Exceção: se a seção do Moodle nomeia explicitamente uma unidade ("U2 - ..."), isso vence o bloco.

### 2.3 Subunidade
Só disputa **entre os tópicos da unidade atribuída** (restrição absoluta). Um scorer léxico casa o texto do material
contra o rótulo e os **aliases** de cada tópico. Depois, uma segunda passada propaga vocabulário: tokens exclusivos dos
headings dos materiais que a primeira passada já decidiu com confiança viram aliases do tópico, e os materiais
indecisos são repontuados. Há ainda regras de desempate: decomposição de rótulos compostos ("Bézier e Algoritmo de
Casteljau" → "Bézier"), o título do material nomeando outro subtópico, e a seção do Moodle nomeando exatamente um
subtópico (só onde nada decidiu).

### 2.4 A taxonomia (o vocabulário de cada tópico)
É o coração do eixo de subunidade. Tem exatamente três fontes:

| o que | de onde |
|---|---|
| tópicos (código, rótulo, slug) | parser do plano de ensino |
| aliases 1 | um GLOSSARY.md por curso, cujos sinônimos vêm de um arquivo sidecar `course/.glossary_curation.json` (manual) e/ou `course/.glossary_curation.llm.json` (compilado por LLM); o loader funde os dois |
| aliases 2 | headings dos próprios materiais |

**O SARC não entra na taxonomia** (alimenta só o alinhamento bloco→unidade). **O Moodle também não** (entra como sinal
no scorer e nas regras). O único canal de vocabulário concreto é o sidecar.

O compilador por LLM (`vocabulary_compile.py`) faz **uma chamada por unidade que tem material**, pede ao modelo que
classifique títulos e headings dos materiais nos tópicos do plano, filtra (exclusividade entre tópicos, identidade com
nome de outra unidade, boilerplate) e grava em cache. Ele **não compila quando existe o sidecar manual** — regra para
nunca sobrescrever trabalho humano.

### 2.5 A fila de revisão
Campo `revisar` por material, recalculado a cada reprocessamento. `duvida` quando: texto e bloco discordam de unidade
(`conflito`); subunidade ambígua ou empatada; bloco veio de desempate flagado; prazo entre dois blocos. `mudou` quando
uma decisão confiante se moveu na última sincronização com o Moodle. É o único sinal de dúvida que o motor emite.

---

## 3. Como medimos

### 3.1 Gold
Referência anotada à mão, por eixo, em CSV. **Regra da casa: o gold só mede, nunca decide, e nunca vira insumo do
motor.** Outra regra: se gold e professor (SARC/Moodle) divergirem, é mais provável que o gold esteja errado.

Cobertura do gold (o "100%" só vale onde há gold):

| eixo | gold cobre | % do repositório | onde não há régua |
|---|---|---|---|
| bloco | 237 de 348 | 68% | LR inteiro; parte do CG |
| unidade | 190 de 348 | **55%** | **CG (93 materiais), LR (7) e FR (22) não têm gold de unidade** |
| subunidade | 251 de 348 | 72% | LR inteiro |

### 3.2 Regimes de medição
Todas as medições rodam com o cliente Gemini bloqueado por um tripwire (qualquer chamada explode), em cópias dos
repositórios. Três regimes:

- **produto**: o que está em disco, com votos de LLM em cache e vocabulário compilado.
- **sem voto**: o voter desligado de verdade, então o cache nunca é lido.
- **zero LLM**: sem voto e sem nenhum sidecar de vocabulário.

### 3.3 Régua sem gold
Compara o motor com o que o professor escreveu: posição datada no Moodle, assunto da seção × assunto do cronograma,
e seção nomeando unidade ou tópico. Foi calibrada contra o gold (ver 5.8).

---

## 4. Estado atual (2026-09-08, produto em disco, 0 chamadas de LLM na medição)

| medida | valor |
|---|---|
| materiais 100% certos (todos os eixos com gold) | **199 / 288** |
| bloco | **235 / 237** |
| unidade | **190 / 190** |
| subunidade | **161 / 251** |
| fila de revisão | 96 em 348 = **27,6 por 100** |
| **erros entregues como confiantes (fora da fila)** | **64** |

Os três regimes (base de 233 na subunidade, medida antes de incluir o FR):

| regime | 100% certos | bloco | unidade | subunidade | fila |
|---|---|---|---|---|---|
| produto | 199/288 | 235/237 | 190/190 | 146/233 | 91 |
| sem o voto de LLM | 184/288 | 221/237 | **188/190** | 143/233 | 136 |
| zero LLM | 165/288 | 222/237 | 188/190 | 121/233 | 143 |

**O voto de LLM vale 14 no bloco e apenas 2 na unidade.** Sem ele o motor não erra mais, desiste mais: a fila vai de 91
a 136.

Anatomia da fila (96 itens):

| motivo | n |
|---|---|
| conflito texto × bloco na unidade | **48** |
| subunidade ambígua | 13 |
| subunidade em empate exato | 10 |
| bloco veio de desempate flagado | 9 |
| prazo entre dois blocos | 1 |
| mudou na última sincronização (transitório, só CG) | 22 |

---

## 5. Os achados, com os dados

### 5.1 Parte da acurácia vinha do próprio gold (circularidade)
Quatro dos seis cursos com gold (SO, IA, ES2, TCC) tinham em `course/.glossary_curation.json` um vocabulário cujo
cabeçalho dizia literalmente "proposto-claude a partir de subunit_gt" — ou seja, sinônimos derivados do CSV de gold
contra o qual o motor era medido. Esses sinônimos viram alias da taxonomia, o sinal de maior peso da subunidade.

Ablação pela rota real (remover o arquivo e reprocessar):

| curso | subunidade com o sidecar | sem |
|---|---|---|
| SO | 15/15 | 9/15 |
| IA | 39/39 | **4/39** |
| ES2 | 21/28 | 5/28 |
| TCC | 11/11 | 8/11 |
| soma | **86/93** | **26/93** |

Bloco e unidade não mudam. O sidecar foi arquivado e substituído por um gerado só de fontes do professor (ver 5.7).
O produto caiu de 253/288 para 199/288 **porque a régua ficou honesta**; no mesmo período o regime zero-LLM subiu
de 155 para 165 por engenharia determinística.

### 5.2 A confiança do motor por eixo
A pergunta "num curso novo, sem gold, se eu aceitar tudo que o motor NÃO põe na fila, quanto está certo?":

| eixo | precisão do confiante | recall da fila |
|---|---|---|
| unidade | **157/157 = 100%** | não há erro |
| bloco | 177/178 = 99,4% | 1/2 |
| **subunidade** | **117/181 = 64,6%** | 26/90 = 29% |

**Para a unidade, um curso novo já dispensa gold.** Para a subunidade, o motor não sabe que não sabe: 64 materiais
saem errados sem aviso.

### 5.3 O vocabulário é o jogo inteiro da subunidade
Três medições independentes convergem:

| regime | subunidade |
|---|---|
| sem vocabulário nenhum (1ª passada) | 114/233 = 49% |
| produto atual (sidecar do professor) | 135/233 = 58% |
| MF + CG, que têm vocabulário compilado por LLM | 109/140 = 78% |
| com o sidecar derivado do gold (contaminado) | 201/233 = 86% |

E a relação já registrada antes desta campanha: 87/93 com vocabulário, 30/93 sem.

### 5.4 O plano de ensino é a fonte MAIS FRACA de vocabulário
Para 222 materiais com gold, "o subtópico certo é nomeável por esta fonte?" (critério determinístico de nomeação):

| fonte | alcança o subtópico certo |
|---|---|
| **plano de ensino, rótulo literal** | **27 = 12%** (IA 0%, MF 7%, ES2 7%, CG 21%, SO 27%) |
| título + label do Moodle | 94 = 42% |
| SARC, label da aula | 88 = 40% |
| headings do material | 82 = 37% |
| plano + SARC + Moodle | 138 = 62% |
| **nenhuma fonte do professor** | **48 = 22%** |

**O plano nomeia a categoria e o material nomeia o objeto.** O plano da IA diz "Modelos Descritivos"; o material diz
"K-Means". O plano do ES2 diz "Estudo de caso: arquitetura orientada a microsserviços"; o material se chama
`roteiro2-nameserver`. Esse mapa objeto→categoria é conhecimento de domínio e **não existe em fonte nenhuma do
professor**. Os 22% que nenhuma fonte alcança são o piso duro sem LLM.

Ressalva medida: as colunas SARC e Moodle acima usam a taxonomia com aliases. **Com a taxonomia limpa**, SARC cai de
40% para 21% e no IA de 95% para 0%. A nomeação é circular: o texto do professor só "nomeia" o tópico quando o
vocabulário concreto já está na taxonomia.

### 5.5 O gargalo é o INSUMO, não a regra
Acerto de subunidade por classe de material (233 com gold):

| classe | n | acerto |
|---|---|---|
| `.pdf` | 109 | **94%** |
| `.zip` (código) | 35 | 66% |
| `.html` (páginas-índice de vídeos) | 37 | **62%** |
| material com link de YouTube | 28 | **57%** |
| texto próprio | 184 | 88% |
| texto entre 3.000 e 8.000 chars | 37 | 97% · texto < 500 chars: 62% |

55% do erro de subunidade é material que **não tem uma subunidade única**: 9 casos onde o gold quer "nenhuma" e o
motor preencheu (prática de OpenGL, setup de ferramenta), 12 páginas-índice que enumeram N vídeos filhos e o motor
escolhe o filho mais citado quando o certo é o assunto da página. O modelo de dados grava um escalar; o gold já admite
vazio e alternativas.

Confundimento desfeito: materiais aprovados na interface de curadoria acertam 93% e os não aprovados 71%, mas dentro
de um mesmo curso (CG) aprovado dá 50% e não aprovado 72%. Não é causal.

### 5.6 O compilador de vocabulário por LLM já existe e estava desligado onde mais importava
`vocabulary_compile.py`: uma chamada por unidade com material, cache, arquivo separado. Já roda em MF, CG, LR e FR.
Amostra do que produz no CG: `1.1 Origens ← WHIRLWIND, SAGE, Sketchpad, Invenção do mouse`. Não é circular: não vê gold.

Quanto vale, medido por ablação (remover o arquivo e reprocessar):

| curso | com | sem |
|---|---|---|
| MF | 51/58 | 47/58 |
| CG | 58/82 | **48/82** |

Bloco e unidade não mudam. Por unidade, das 9 chamadas que produziram vocabulário: 5 rendem 16 pontos, 3 não mudam
nada, **1 custa 2 pontos** (a unidade 01 do CG, "Áreas relacionadas", recebeu "Morfologia Matemática" e "Manipulação
de Imagens", que são assuntos da unidade 03 — correto como prosa, veneno como vocabulário de matcher).

Nunca rodou em SO/IA/ES2/TCC porque existia o sidecar manual — o derivado do gold. Custo de ligar: 16 chamadas, uma
vez. Referência registrada no código, de uma medição anterior: esse prompt levou o IA de 5 para 37/39.

### 5.7 Gerador de vocabulário sem gold, só de fontes do professor
Construído e medido: a seção do Moodle que nomeia exatamente um tópico recebe o vocabulário dos materiais dela
(título, label, headings); o label da aula do SARC que nomeia um tópico doa os tokens restantes. Filtros: boilerplate
acadêmico, frequência > 15% dos materiais, token que já nomeia outro tópico, e concentração ≥ 80% das ocorrências na
seção que doa.

| regime | subunidade |
|---|---|
| sidecar derivado do gold | 201/233 |
| sem sidecar | 135/233 |
| **sidecar do professor** | **146/233** |

Recupera 11 dos 66 pontos. Por curso, limpo → professor: ES2 5→15, SO 9→10, MF 51→52, IA 4→4, TCC 8→8, CG 58→57.
**No IA não recupera nada**, pelo motivo de 5.4.

### 5.8 A unidade fora do gold: parcialmente sustentada
A régua sem gold tem dois caminhos. **A**: a seção nomeia a unidade — confiável. **B**: a seção nomeia um tópico e a
régua assume a unidade dona — **erra 5 de 5 divergências**, e o gold dá razão ao motor nas cinco.

Calibração onde as duas réguas existem (44 materiais): **motor 44/44, régua 39/44**. O motor é melhor que a régua sem
gold; ela serve para confirmar, nunca para corrigir.

Cobertura independente nos cursos sem gold de unidade: CG **16 de 93 (17%)**; FR **zero** (os 19 acordos são
circulares — o motor decidiu lendo a mesma seção); LR zero. Apoio indireto do CG: o bloco bate com o assunto do
cronograma em 58/59.

### 5.9 A unidade não é livre de LLM, mas quase
28% dos blocos foram decididos por voto de LLM em cache. Sem o voto a unidade cai só de 190 para 188. O custo do voto
está na fila, não na precisão.

### 5.10 O Moodle não dá a unidade "na maioria das vezes"
Em 190 materiais com gold, a seção do Moodle nomeia a unidade correta em **43 (23%)**, o label em 12 (6%), o bloco em
190 (100%). Quando a seção arrisca, acerta 43/43 — precisão altíssima, cobertura baixa. **O SARC dá a unidade; o
Moodle dá o quando** (a data do label coloca o arquivo no bloco).

### 5.11 Um caso resolvido na causa: ES2
Seis materiais estavam na unidade errada por dois dados de curadoria derivados do gold: um pino manual de bloco
("gold-backed", de uma versão antiga do gold) e cinco sinônimos de arquitetura (`service discovery`, `name server`,
`API gateway`...) colocados sob o tópico de "implantação". As duas correções eram necessárias. Justificadas pelo
professor, não pelo gold: o rótulo do plano separa "arquitetura" de "implantação", e o cronograma põe essas aulas antes
da P1. Unidade 21/28 → 28/28, subunidade 21 → 27/28, zero perdas.

---

## 6. Tudo que foi tentado e refutado por medição (não repetir)

| alavanca | resultado |
|---|---|
| Piso de score no resultado final (não atribuir se fraco) | todo piso perde; melhor piso = 0 |
| Piso de força na 1ª passada para bloquear a 2ª | sem efeito em 5 valores |
| Regra pai × filho (texto cobre vários filhos → sobe para o pai) | 8 configurações, nenhuma com saldo positivo; curso-dependente |
| Seção nomeia um tópico → unidade dona do tópico decide | erra 5 de 5 onde há gold |
| Título com vocabulário completo | teto 3 em 38 erros; saldo 0 |
| Página-índice decidida pelo cabeçalho (H1/seção) | teto 6 em 38; melhor +2 com 17 mudanças |
| Título real do vídeo do YouTube no lugar do hash de 11 chars (91% dos 246 links) | 183/183 títulos recuperados; **ganha 0, perde 2** — mais texto do corpo piora, o índice fala dos filhos |
| IDF intra-unidade no scorer | 0 · +1/−5 · 0 |
| Similaridade nome do material × vocabulário (Jaccard, difflib) | refutada em 4 variantes |
| Agrupar arquivos por palavras-chave para SUBSTITUIR o scorer | teto 65% com oráculo; real pior que por arquivo (componentes conexas degeneram: IA vira 1 grupo de 39) |
| Triagem da chamada de LLM por sinal determinístico de fraqueza | o sinal não prediz o valor da chamada |
| "A prova é fronteira de unidade" no cronograma | 3 a favor, 25 contra |
| Automatizar o gold a partir de Moodle + SARC | erro de categoria: a régua dessas fontes acerta 39/44 onde o motor acerta 44/44 |
| Zero-pad no número da unidade; número na chave do slug | quebram glossário e slugs |
| Texto vence o bloco por confiança | −17 a −2 |
| Card como origem da subunidade de código | 0/−23 |
| Vocabulário determinístico por co-heading (em vez de LLM) | 26 → 31/93, contra LLM 5 → 37/39 no IA |

**Medido e positivo, ainda não implementado:**

| alavanca | ganho |
|---|---|
| Propagação por similaridade: indeciso herda do vizinho mais similar entre os confiantes (Jaccard, dentro da unidade) | **+5** (ganha 6, perde 1); vizinho mais similar compartilha a subunidade em 76% dos casos |
| Filtro mais duro no vocabulário compilado (termo que nomeia outra unidade; tópico de rótulo meta) | **+2** |

---

## 7. O diagnóstico, como o entendemos hoje

1. **Bloco e unidade estão resolvidos onde há régua** (99,2% e 100%), com confiança honesta (99,4% e 100% de
   precisão no confiante). O que resta lá é cobertura de gold, não motor.
2. **A subunidade é o problema**, e ele tem duas faces:
   - a confiança mente (64,6% de precisão no confiante; 64 erros silenciosos);
   - o vocabulário que separa acerto de erro é conhecimento de domínio que **não está em nenhuma fonte do professor**
     (12% no plano, 22% em fonte nenhuma), e o único jeito medido de obtê-lo sem gold é uma chamada de LLM por unidade.
3. Todo ganho determinístico que sobrou no motor é de segunda ordem (+2 a +5), enquanto o insumo responde por
   diferenças de 30 pontos entre classes de material (PDF 94% × HTML 62% × vídeo 57%).
4. **Nosso plano atual:** primeiro tornar a confiança honesta (calibrar o limiar de confiança da subunidade contra o
   gold uma única vez, fazer a decisão fraca cair na fila; gate: ≥ 90% de precisão no confiante), depois acurácia
   (as duas alavancas medidas + ligar o compilador nos 4 cursos com 16 chamadas), depois cobertura de régua (gold de
   unidade para o CG). Em seguida, a campanha de dívidas de dados: 32 dos 35 zips do repositório têm colisão de nome
   de arquivo entre si (99 nomes de conteúdo), então o código extraído e o resumo desses materiais podem estar
   trocados.

---

## 8. Estrutura de código relevante (para quem quiser raciocinar sobre arquitetura)

```
src/builder/
  extraction/content_taxonomy.py      build_content_taxonomy: plano -> topicos; GLOSSARY + headings -> aliases
  extraction/teaching_plan.py         parser do plano (numeracao X.Y / X.Y.Z, teto de 2 digitos por nivel)
  extraction/entry_signals.py         texto que o scorer pontua (descricoes de imagem ja saem daqui)
  core/vocabulary_compile.py          compilador de vocabulario por LLM: 1 chamada por unidade com material, cache
  timeline/index.py                   cronograma do SARC -> blocos
  timeline/unit_matcher.py            assign_units_positional: DP monotonico bloco -> unidade por afinidade de tokens
  routing/motor/window_provider.py    providers de janela (labels, data, ordinal, topic, card...)
  routing/motor/anchor_engine.py      cascata + voter opcional (TIER 3)
  routing/motor/llm_vote.py           voto de LLM na janela, cache por md5, cap 20 por rodada
  routing/file_map.py                 auto_map_entry_subtopic (restrito a unidade) + reconcile_unit_with_block (bloco decide)
  routing/resolver_apply.py           2a passada (propagar_vocabulario_por_headings), regras de titulo e secao, fila
  routing/revisar.py                  a fila: duvida / mudou / ok
docs/reports/_harness-2026-09-04/c1-3/   ~80 scripts de medicao, cada um com log homonimo
docs/reports/pendencias.md               tracker vivo de tudo que foi medido
```

Dados por curso (repositório do tutor): `manifest.json` (um registro por material com bloco/unidade/subunidade
computados, razões, confiança, fila), `course/.content_taxonomy.json`, `course/.timeline_index.json`,
`course/.glossary_curation[.llm].json`, `course/.timeline_curation.json` (pinos manuais), `code_curation.json`
(resumos de código por LLM, cache por hash).

---

## 9. A pergunta

Dado tudo acima, o que você faria? Especificamente:

1. **Há um caminho para a subunidade que não passe por vocabulário de domínio vindo de LLM?** Medimos que plano, SARC
   e Moodle juntos nomeiam o subtópico certo em 62% dos materiais, e 22% não são nomeados por fonte nenhuma. Você vê
   uma fonte ou um mecanismo que não consideramos?
2. **Como tornar a confiança da subunidade honesta** (hoje 64,6% de precisão no confiante) sem gold por curso? Nossa
   hipótese é calibrar um limiar uma vez; você vê algo melhor?
3. **O modelo de dados obriga uma subunidade escalar por material**, mas 55% do erro é material que não tem uma
   subunidade única (páginas-índice, prática de ferramenta). Vale mudar o contrato? Como?
4. **A dependência do bloco:** a unidade é herdada do bloco, e 28% dos blocos vieram de voto de LLM. Isso é um risco
   estrutural ou um preço aceitável?
5. **Estamos gastando esforço no lugar certo?** O plano atual é confiança → acurácia → dados. Você inverteria?
6. **O que você mediria antes de qualquer coisa** que nós ainda não medimos?

Não implemente. Não gere código. Queremos o raciocínio, o plano, e as discordâncias.
