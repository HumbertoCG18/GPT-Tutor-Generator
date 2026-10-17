# CRU-05 (#89): diagnóstico do mecanismo da perda

**Opção 2 da revisão do GPT Pro, autorizada pelo usuário em 01/10.**

Desenho seguido:

- um par instrumentado;
- fidelidade integral;
- atribuição pela primeira divergência;
- parada depois do par;
- sem gold. O gold não foi lido.

**Resultado:**

- **Refutada:** a hipótese **específica** do relatório, de que "reconheciveis"/"decidiveis" teriam sido propagados para
  `maquinas-de-turing`.
- Nos 6 materiais que mudam, a **primeira divergência** está no texto do próprio material (1ª passada).
- A 2ª passada, com aliases alterados, decide 4 dos 6, inclusive a aula-10.
- A participação relativa das duas passadas não foi quantificada: não houve contrastes cruzados.

*Texto revisado em 01/10 com as precisões do usuário: o que foi refutado é só a hipótese específica, e a fragilidade
do pontuador é hipótese, não causa demonstrada.*

## Execução

- **Runner** `diag_cru05_mecanismo.py`, rodado uma vez para cada lado:
  - **base:** `src` da worktree da noite (`bf46d51f`, `normalize` `d0ce2309…`), contra `replay_base.json`;
  - **candidato:** `src` da `cru05` (`normalize` `f5b9581a…`), contra `replay_candidato.json`.
- **Fidelidade:** integral nos dois lados. As decisões são idênticas às referências em todos os 350 IDs, nenhum módulo
  `src` foi carregado de fora da worktree, e cada execução levou cerca de 1160 s.
  - Registros: `registros/diag_rastro_*.txt`.
  - Rastros: `diag_rastro_base.json` e `diag_rastro_candidato.json`.
- **O que foi instrumentado:**
  - unidade bruta;
  - 1ª passada com as pontuações de todos os tópicos;
  - tokens de headings;
  - `vocab_unit`;
  - aliases acrescentados, com origem e doadores;
  - guarda do título;
  - repontuação da 2ª passada;
  - regra da seção;
  - final.
- **Comparação:** `compara_mecanismo.py` → `compara_mecanismo.json` e `registros/compara_mecanismo*.txt`.

## Primeira divergência

- **46 materiais** têm alguma diferença intermediária:
  - em 31, a primeira divergência é nos **tokens do próprio material**;
  - em 15, só mudam os aliases da unidade; os tokens do material ficam iguais.
- **6 mudam a decisão final**, os mesmos do replay. Em todos os 6 a primeira divergência é no **texto do próprio
  material**.

| material | 1ª passada: base → candidato | quem decide no candidato |
|---|---|---|
| SO `1205-laminas-gerencia-de-memoria` | `swapping` 0,35 → `memoria-virtual` 0,31 | a própria 1ª passada (a 2ª repete) |
| TCC `aula-10` (**a perda**) | `linguagens-reconheciveis-e-decidiveis` 0,60 → `maquinas-de-turing-universais`, **ambíguo** (5,96 × 5,74 de `maquinas-de-turing`; o certo fica em 2,28) | 2ª passada → `maquinas-de-turing` (propagado-headings) |
| TCC `aula-11` | `conjectura-de-church-turing` 0,88 (confiante) → `maquinas-de-turing` 0,85 (confiante) | a 1ª passada; a guarda do título não age |
| TCC `aula-12` | `prova-da-indecidibilidade…` 0,93 (confiante) → o mesmo tópico, 0,19 (**deixa de ser confiante**) | 2ª passada → `teoremas-de-godel` |
| TCC `aula-15` | `prova-da-indecidibilidade…` 0,39 → `teoremas-de-godel` 0,43 | 2ª passada confirma `teoremas-de-godel` |
| TCC `aula-17` | `teorema-de-cook-levin` 0,7075 (confiante por pouco; `conf_min` 0,70) → 0,577 | 2ª passada → `reducao-polinomial-de-problemas` |

## Cadeia da aula-10

1. **Texto.** A correção junta as palavras do próprio material:
   - "maquina", que antes virava "m" + "aquina";
   - "decidivel"/"indecidiveis", que antes viravam "decid" + "iveis";
   - "analise", "decisao", "reducao" e outras.
2. **1ª passada.** Com "maquina" inteira, os rótulos "Máquinas de Turing…" passam a casar. Os dois tópicos de máquinas
   superam o tópico certo, e a decisão fica ambígua e vai para a 2ª passada. Na base, a decisão também ia para a 2ª
   passada (0,60 < 0,70), mas com o tópico certo à frente.
3. **2ª passada, aliases** (`compara_mecanismo.json`, cursos/TCC):
   - **o tópico certo perde a parte de rótulo "Decidíveis".** Provável causa, inferida de `_partes_de_rotulo`
     (`resolver_apply.py:183–218`): a parte só entra se aparecer em ≤ 25 % dos textos (`df_max` 0,25, busca por
     substring). Com a palavra inteira, "decidiveis" (inclusive dentro de "indecidiveis") passa a aparecer em mais
     textos do TCC. O rastro não guardou essa frequência no texto completo, só nos headings: **não medido**;
   - **`maquinas-de-turing` ganha** "maquina", "codificacao", "contexto" e "historico" por propagação, e **perde** o
     fragmento "aveis", que era a perda do diagnóstico de 23/09.
4. **Repontuação.** Na base, o certo vencia com 16,74 (rotulo-decomposto). No candidato vence `maquinas-de-turing`, com
   14,31 (propagado-headings).

**A hipótese específica do relatório está refutada.** "reconheciveis" e "decidiveis" **não** foram propagados para
`maquinas-de-turing`; a ressalva da revisão sobre o `vocab_unit` se confirma.

O que muda de forma visível é "maquina", que a correção torna inteira:

- no rastro do candidato, aparece nos headings de 5 dos 26 materiais do TCC (na base, como o fragmento "aquina");
- está nos rótulos de dois tópicos da unidade 02;
- vira alias propagado de `maquinas-de-turing`.

## Leitura

- **O acerto da aula-10 na base coexistia com o defeito, e não se sustenta sem ele.** O único delta entre as execuções
  é a normalização. Logo, 1 dos 86 acertos atuais da subunidade primária depende do texto fragmentado. O mecanismo
  exato dentro do pontuador é descrito acima, não isolado.
- **A correção é textual e certa, e tira do motor uma "ajuda" acidental.** A **hipótese** que o diagnóstico justifica
  para a próxima proposta é uma fragilidade do pontuador: termos pouco discriminantes entre tópicos e entre materiais
  do curso passam a decidir. Seria da mesma família dos mecanismos A e B do diagnóstico das perdas do VOCAB (migalha de
  token; aliases acumulados e diluição).
  - Isso **não** está demonstrado como causa exclusiva.
- **A propagação não fica descartada como contribuinte.** A primeira divergência na 1ª passada não demonstra, sozinha,
  que uma guarda de propagação seria inútil.
  - Na aula-10, a 2ª passada muda os aliases da unidade: o tópico certo perde "Decidíveis" e `maquinas-de-turing` ganha
    "maquina", "codificacao", "contexto" e "historico". É ela que decide o resultado final.
- **Contrastes cruzados** (normalização base × aliases candidatos, e o inverso) **não foram executados**. Por isso, a
  participação relativa da 1ª e da 2ª passadas na aula-10 e nos outros 3 casos decididos na 2ª passada fica **não
  quantificada**.

## O que isso diz sobre a decisão

1. **Não integrar a correção isolada** (confirmado). Ela troca um acerto que dependia do texto fragmentado por um erro.
2. **Hipótese para a próxima proposta:** o peso de termos pouco discriminantes no pontuador da subunidade, separando a
   frequência entre tópicos da frequência entre materiais.
   - É uma proposta nova, com Gate próprio, sem regra encaixada no gold e com o aceite de integração vigente.
   - A correção dos acentos pode acompanhar o candidato, com os efeitos avaliados separadamente.
   - A contribuição da propagação continua em aberto.
3. **Limites:**
   - diagnóstico pós-gold sobre cursos já vistos (só explica; não é evidência para ajuste);
   - a causa do descarte de "Decidíveis" é inferida, não medida;
   - "certo" e "errado" vêm do replay; o gold não foi lido aqui.
