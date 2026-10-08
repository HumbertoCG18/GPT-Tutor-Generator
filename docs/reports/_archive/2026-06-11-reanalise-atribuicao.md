# Re-análise independente — sistema de atribuição de bloco

date: 2026-06-11
motivação: suspeita de viés/alucinação no diagnóstico anterior
(`2026-06-11-diagnostico-atribuicao.md`). Tudo aqui foi re-verificado do zero:
números recomputados por script direto no manifest real, mecanismos lidos no
código-fonte, e o gabarito re-derivado do stash Moodle físico.

## Método

1. Recomputei estatísticas direto de `Metodos-Formais-Tutor/manifest.json` (56 entries).
2. Cruzei cada entry com a localização física real do arquivo no stash
   (`Desktop/Moodle/metodos-formais-para-computacao`, basename matching).
3. Comparei `computed_block_id` contra o gabarito `course/.card_block_map.json`.
4. Li as listas `_ARQUIVOS_DO_CARD.txt` de cada seção (arquivos que o card Moodle espera).
5. Dois agentes verificaram 12 afirmações do diagnóstico no código (eu re-verifiquei
   manualmente as refutações suspeitas — um agente errou em A5).
6. Rodei o harness `scripts/eval_assignments.py` com a fixture sintética E com o
   índice de timeline real para reproduzir o bug B3.

## Números reais (recomputados, 56 entries — diagnóstico anterior usava 49/54)

| Fato | Valor |
|---|---|
| Entries totais | 56 (49 material + código avaliado antes era subconjunto) |
| Sem `source_section` | 32/56 (57%) |
| `computed_block_confidence` = 1.0 | 46/56 |
| `computed_block_method` preenchido | 18/56 (só código: 9 llm_only, 9 consensus) |
| Bloco manual | 7 |
| Ids duplicados no manifest | 2 pares reais: `introducao` ×2, `t1-2026-1` ×2 |
| Entries cujo bloco computado está FORA do gabarito da sua seção física | 8 |
| Entries em seção SEM entrada no gabarito | 18 |
| Cobertura do card_block_map | 5 de 9 seções do stash |

Os "8 erros" do diagnóstico anterior correspondem às 8 entries fora do gabarito —
número bate. Todas têm `source_section` vazio — isso também bate.

## Veredito das afirmações do diagnóstico anterior

| # | Afirmação | Veredito | Evidência |
|---|---|---|---|
| A1 | Sem `source_section`, gabarito desliga em silêncio | **CONFIRMADO** | `file_map.py:854-855` — `_card_scoped_block` retorna `("", 0.0)` sem log/flag/penalidade |
| A2 | `margin_confidence` satura em 1.0 | **CONFIRMADO** | `thresholds.py:6-12` — `(winner−runner)+0.18·winner` clampado em [0,1]; scores típicos 4-8 ⇒ sempre 1.0 |
| A3 | `computed_block_method` só para código | **CONFIRMADO** | `pedagogical_regeneration.py:115-148`; fonte só no caminho Gemini (`code_summarization.py:383`) |
| A4 | Scorer sem IDF | **PARCIAL** | Scorer de UNIDADE TEM IDF (`file_map.py:136-140`, `token_weights = 1/freq`). Scorer de BLOCO/temporal (`entry_signals.py:12-26`) NÃO tem — pesos fixos 1.0/0.45. Diagnóstico generalizou errado, mas a falha vale para o scorer que decide bloco |
| A5 | CamelCase vira 1 token | **CONFIRMADO** | `normalize.py:7-17` — `lower()` ANTES do regex ⇒ "LogicaDeHoare" → "logicadehoare" (1 token, não casa o topic "logica de hoare"). Nota: agente verificador refutou errado; re-verifiquei manualmente |
| A6 | Backfill de seção é script manual nunca chamado pelo pipeline | **CONFIRMADO** | `scripts/backfill_source_section.py` standalone, sem import em pipeline algum |
| B1 | `references` (EN) fura `_NO_TIMELINE_CATEGORIES` | **CONFIRMADO** | `content_taxonomy.py:961` só PT; `navigation.py:607` tem a versão com "references" — sets divergentes. Entry real `archive-of-formal-proofs-355fb8` (references) recebeu bloco-06 conf 1.0 |
| B2 | Card bonus somado 2× | **REFUTADO** | `file_map.py:795` e `:874` são caminhos mutuamente exclusivos — não há dupla soma no mesmo entry→bloco |
| B3 | `eval_assignments.py` colapsa com índice persistido | **CONFIRMADO (comportamental)** | Fixture sintética usa blocos com chave `rows` → 5/5 OK. Blocos do índice REAL (`sessions`/`source_rows`, sem `rows`) → TODA entry prevê bloco-01, band baixa. Degenera em silêncio, não crasha |
| B4 | Entry com unit u02 + bloco u01 | **TRATADO POR F1** | `reconcile_unit_with_block` (`file_map.py:586-628`, commit d6ef048) cobre; falta re-rodar retag no repo real |
| B5 | Ids duplicados no manifest | **CONFIRMADO** | 2 pares reais. Dedup do import é por `source_path`, não por id (`lifecycle_ops.py:58-62`); diretórios de assets usam `entry.id()` ⇒ risco real de sobrescrita |

## Descoberta nova — a premissa central do P1 está errada

O diagnóstico anterior afirmou: *"a informação de seção existe no stash e se perde
no caminho; backfill por basename resolve e os PDFs caem nos blocos do gabarito"*.
**Três fatos novos derrubam isso:**

### 1. Os arquivos dos erros estão fisicamente no card ERRADO do stash

`LogicaDeHoare.pdf`, `LogicaDeHoare2.pdf`, `CorrecaoTerminacao.pdf`,
`ExerciciosCorrecaoTerminacao.pdf`, `FormalizacaoAlgoritmos_InvariantesLaco.pdf`,
`ExerciciosFormalizacaoAlgoritmosInvariantes.pdf` estão na pasta
**"Revisão - Lógica e Especificação"** — mas a lista `_ARQUIVOS_DO_CARD.txt` desse
card só espera lógica proposicional/predicados (material de março). Quem espera
"Lógica de Hoare (parte 1/2)", "Invariantes de laço", "Correção e Terminação" é o
card **"Verificação de Programas"**. Os nomes de download do Moodle
(`LogicaDeHoare.pdf`) diferem dos nomes de exibição do card ("Lógica de Hoare
(parte 1).pdf"), e os arquivos foram colocados na pasta errada.

Consequência: backfill por pasta daria seção "Revisão - Lógica e Especificação"
→ gabarito {bloco-02, bloco-03} (março) → **erro confiante**, pois o conteúdo é
Hoare/terminação (abril-maio, blocos 10-12). P1 como especificado converteria os
8 erros atuais em 6+ erros novos com prior "forte".

### 2. O card_block_map cobre só 5 das 9 seções

`course/.card_block_map.json` (source: "manual", criado 07/06) não tem entrada para
"Verificação de Programas" — justamente a maior seção (15 arquivos, blocos 10-15).
Mesmo com seção correta preenchida, o prior não dispara para ela. Também não há
entrada para "Introdução a Métodos Formais" nem "TDE".

### 3. Há dois fluxos de import com comportamentos opostos

- Entries vindas de `Downloads/Metodos-Formais/` TÊM `source_section` preenchida.
- Entries cujo `source_path` está DENTRO do stash (a seção é literalmente o nome da
  pasta-pai no caminho!) têm `source_section` vazio.

Ou seja: o fluxo que mais facilmente derivaria a seção é o que a descarta.

## Cadeia causal revisada

```
[elo 1] Import direto de arquivo do stash não preenche source_section
        (mesmo com a seção no próprio caminho)               — CONFIRMADO
   ↓
[elo 2] Sem seção, _card_scoped_block retorna vazio EM SILÊNCIO
        → prior nunca consultado, sem aviso                  — CONFIRMADO
   ↓
[elo 3] Decide o scorer de bloco, que é fraco:
        sem IDF (peso fixo), CamelCase = 1 token,
        sem sinal de ferramenta (.thy vs Dafny)              — CONFIRMADO
   ↓
[elo 4] margin_confidence satura em 1.0 → erro sai "confiante"
        e a triagem humana não prioriza                      — CONFIRMADO
   +
[elo 0 — NOVO] Mesmo consertando 1-2, o prior falharia:
        gabarito cobre 5/9 seções, mapeamento da seção
        "Revisão" é questionável, e os arquivos dos erros
        estão no card físico errado                          — NOVO
```

**Causa raiz sistêmica:** nenhum elo valida a integridade do sinal de seção.
O import não o preenche quando disponível; o stash não é validado contra as listas
`_ARQUIVOS_DO_CARD.txt` (que já existem e detectariam a colocação errada); o
gabarito não exige cobertura; e a confiança não reflete qual estágio decidiu nem
se o prior estava ausente. Não é um bug único — é ausência de contrato entre os
estágios do funil.

## Implicações para o plano-mestre

- **P0 (medição)** — mantém, B3 confirmado com mecanismo exato (`rows` vs
  `sessions`/`source_rows`; degenera para bloco-01 em silêncio). Golden set precisa
  de rótulos re-julgados: os "expected" do diagnóstico anterior eram julgamento de
  LLM e pelo menos os casos da seção "Revisão" são ambíguos (conteúdo Hoare vs
  pasta Revisão).
- **P1 (seção automática)** — **precisa de redesenho**. Backfill por pasta do stash
  é insuficiente e perigoso: tem que (a) validar arquivo contra a lista
  `_ARQUIVOS_DO_CARD.txt` do card (match fuzzy nome-download ↔ nome-exibição),
  (b) sinalizar arquivo em pasta inconsistente em vez de confiar nela, e
  (c) garantir cobertura do card_block_map para TODAS as seções (hoje manual, 5/9).
- **P2 (confiança/method)** — mantém, A2/A3 confirmados na íntegra.
- **P3 (higiene)** — B2 sai da lista (refutado); B1 e B5 confirmados; B5 é mais
  sério que o descrito (sobrescrita de assets por id colidido).
- **P4 (scorer)** — IDF já existe no scorer de unidade (`token_weights`); reusar o
  mesmo mecanismo no scorer de bloco é caminho mais curto que o descrito. CamelCase
  confirmado (fix na tokenização do título, não no normalize global — o normalize é
  fonte única e mudá-lo afeta 6+ módulos).

## ADDENDUM (mesma noite) — causa raiz da contaminação do stash encontrada

O usuário confirmou: o stash do Desktop saiu assim do download automático (não foi
colocação manual). Investigação na fonte, com a API Moodle real chamada ao vivo:

### Fatos provados

1. **A API Moodle está correta HOJE**: `core_course_get_contents` (curso 92717)
   coloca `LogicaDeHoare.pdf`, `CorrecaoTerminacao.pdf` etc. na seção
   "Verificação de Programas". As listas `_ARQUIVOS_DO_CARD.txt` (geradas em
   08/06 15:31) também — a API nunca esteve errada.
2. **Os bytes do Desktop foram escritos pelo app** (mtime 08/06 15:32-15:34 =
   hora do run; cópia manual preservaria mtime de origem 13/05). Hash idêntico
   ao material original do Moodle.
3. **Os nomes em disco são os originais** (`LogicaDeHoare.pdf`), não os
   nomes-de-módulo que `download_course` atual gravaria
   ("Lógica de Hoare (parte 1).pdf") — o run usou código carregado antes do
   commit `3f73ef2` (13:47). Irrelevante para a seção, mas data o run.
4. **O caminho que escreveu os arquivos não foi `download_course`** (que herda a
   seção correta da API) e sim o fluxo M365: o Moodle PUCRS serve arquivos via
   SharePoint/OneDrive; `download_course` marca como `failed` (redirect HTML) e
   o app cai em `download_subject_m365` (src/builder/sources/m365.py:222).
5. **O fluxo M365 ADIVINHA o card por léxico** (`match_card`, m365.py:84):
   afinidade de tokens entre o nome da subpasta do OneDrive do professor e os
   nomes das seções Moodle, threshold 0.34. O professor organiza o OneDrive por
   TÓPICO; o Moodle, por card. Reproduzido com as funções reais:
   - pasta `lógica*`/`especificacao` → "Revisão - Lógica e Especificação" (score 1.0)
   - pasta `logica-hoare` → "Revisão - Lógica e Especificação" (0.5) — e
     "Verificação de Programas" pontua **0.0** (nenhum token em comum)
   - pasta `dafny`/`isabelle` → sem match → vira pasta literal no stash
6. **Prova do item 5 nos logs do manifest**: entries `ExerciciosDafny*` com
   `source_path` quebrado apontando para `...\metodos-formais-para-computacao\dafny\`
   — a pasta literal `dafny` existiu no stash, layout que só o fluxo M365 produz.
7. **O chute vira "verdade" no manifest**: `apply_source_section` (m365.py:284,
   chamado em dialogs.py:1971) grava o card adivinhado em `source_section`.

### Cadeia causal completa (final)

```
OneDrive do professor organizado por TÓPICO (pasta "lógica..." contém
lógica básica + Hoare + terminação)
   ↓
match_card adivinha card por token: "lógica*" → "Revisão - Lógica e
Especificação" (1.0); "Verificação de Programas" nem pontua
   ↓
~15 arquivos despejados no card errado do stash + source_section
gravado com o chute (apply_source_section)
   ↓
[a partir daqui, a cadeia já documentada acima: prior ausente/errado →
scorer fraco decide → confiança 1.0 mente]
```

**Ironia central:** a verdade sempre esteve disponível de graça —
`section_file_index` (moodle.py:132) já mapeia basename→seção real a partir da
MESMA resposta da API usada para gerar as listas esperadas. O fluxo M365 ignora
esse índice e re-adivinha por léxico. O mesmo padrão do scorer de bloco: sinal
forte disponível, descartado em favor de matching fraco apresentado com
confiança máxima.

### Correções de curso no stash (estado em 11/06 ~22h)

- Usuário já moveu: `LogicaDeHoare.pdf`, `LogicaDeHoare2.pdf`,
  `LogicaDeHoare_exercicios_respostas.pdf`, `FormalizacaoAlgoritmos_InvariantesLaco.pdf`
  → "Verificação de Programas".
- Faltam mover (ainda em "Revisão - Lógica e Especificação"):
  `CorrecaoTerminacao.pdf`, `ExerciciosCorrecaoTerminacao.pdf`,
  `ExerciciosFormalizacaoAlgoritmosInvariantes.pdf`.
- Stash também está INCOMPLETO vs API de hoje: faltam `classes_parte2.zip`,
  `exercicios_introducao.zip`, `exercicios_arrays.zip`, `exercicios_sequences.zip`,
  `p58-ben-ari.pdf`, `ExerciciosConjuntosIndutivos_respostas.pdf` e outros
  "Respostas" — e `revisao_p1.pdf`/gabarito não constam mais... (verificar
  seção "Exercícios de Revisão para Provas", que a API hoje lista com 2 arquivos).
- `manifest.json` tem `source_path` quebrados (pasta `dafny\` extinta + arquivos
  movidos hoje) — reprocessar exige reconciliação de caminhos.

### Verificação do fluxo M365 "compartilhados comigo" (pedido do usuário)

Contexto confirmado: o professor hospeda os arquivos em pasta PRIVADA do OneDrive;
o app descobre via Graph `/me/insights/shared` ("compartilhados comigo") filtrando
por substring da matéria/professor na URL. Simulação com as funções reais
(`subfolder_for` + `match_card`) sobre URLs no formato SharePoint PUCRS:

| Filtro | URL …/Documents/MetodosFormais/logica/LogicaDeHoare.pdf | …/dafny/… | arquivo na raiz | share-link curto |
|---|---|---|---|---|
| `metodos` | **"Revisão - Lógica e Especificação"** (errado) | pasta literal `dafny` | `_geral` | `_geral` |
| `metodos formais` (c/ espaço) | `_geral` | `_geral` | `_geral` | `_geral` |
| `machado` (professor) | pasta literal `Documents` | `Documents` | `Documents` | `_geral` |

A simulação reproduz TODA a evidência física: a pasta `dafny\` extinta (logs do
manifest), a pasta `_geral\plano.pdf` no Desktop, e os arquivos de Hoare no card
"Revisão". Confirma que o filtro usado continha "metodos" casando um segmento do
caminho, e que a pasta do professor `logica` (organização por TÓPICO) foi mapeada
lexicalmente para o card "Revisão - Lógica e Especificação" — score 1.0, enquanto
"Verificação de Programas" pontua 0.0.

Falhas adicionais encontradas neste fluxo:

- **`m365_filter` nunca foi persistido** no SubjectProfile (está `''`):
  `dialogs.py:1966-1969` salva via `store.get(info0["name"])` com o nome vindo do
  Moodle ("Métodos Formais para Computação"), que não bate com o nome da matéria
  no store ("Metodos-Formais") — o save é pulado em silêncio.
- **Sensibilidade catastrófica ao filtro**: filtro com espaço ou nome do professor
  degrada TUDO para `_geral`/`Documents` sem aviso — o usuário não tem como saber
  que a grafia exata do filtro decide o layout inteiro do stash.
- **`/me/insights/shared` é heurística de atividade do Graph**, não uma listagem
  da pasta compartilhada — pode omitir arquivos (stash incompleto observado) e
  não fornece a árvore real de pastas; o webUrl de share-link curto nem contém
  o caminho (cai em `_geral`).
- **Aliases default acertam só ferramentas** (`dafny`/`isabelle` →
  m365.py:35-38); tópicos como `logica` não têm alias e caem no match léxico cru.

### Implicação adicional para o plano-mestre

P1 ganha um item a montante: **o fluxo M365 deve usar `section_file_index` da
API Moodle (basename→seção real) como fonte primária do card**, com `match_card`
léxico só como fallback sinalizado (matched=False ⇒ pasta literal + aviso, nunca
seção inventada). Isso conserta o problema na ORIGEM; o backfill de seção do P1
original vira a segunda linha de defesa.

## Limitações desta re-análise

- O "bloco esperado" continua sendo julgamento (meu, por topic/data) para as seções
  sem gabarito; não há ground truth absoluto sem o professor.
- Não dá pra afirmar QUEM colocou os arquivos na pasta errada (usuário vs export);
  a evidência da lista esperada do card é forte mas indireta.
- `card_block_map.json` tem `source: "manual"` e não está no git do repo tutor —
  origem exata (sessão anterior? UI?) não rastreável.
