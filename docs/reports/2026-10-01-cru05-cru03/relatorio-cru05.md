# CRU-05 (#89): acentos espaçadores em `normalize_match_text`

**Resultado: o aceite não foi cumprido.** A correção perde 1 acerto na subunidade primária. Sem commit e sem Gate 2.
Escopo: Gate 1 de 01/10, ~11:45.

## O que foi feito

- Worktree `GPT-Tutor-Generator-cru05`, branch local `fix/cru05-acentos-espacadores` (a partir de `bf46d51f`).
- **Teste vermelho** (`tests/test_text_normalize.py`): 5 de 6 casos falhavam antes da correção (`registros/teste_vermelho.txt`).
  - Exemplos: "Comput´aveis" → "comput aveis"; "Defini¸c˜ao" → "defini c ao".
  - "ˆangulo" já passava, porque o acento fica no início da palavra.
- **Correção** (`src/builder/text/normalize.py`): `translate` remove U+00B4, U+02DC, U+00B8, U+02C6 e U+00A8 antes do
  `strip_accents`. Os ASCII `` ` `` `^` `~` ficam de fora. Diff de 2 arquivos, +21/−1.
  - Ressalva da revisão: o comentário no código diz que o NFKD decompõe os cinco em espaço + combinante. Isso é falso
    para U+02C6, que não se decompõe e vira espaço pelo filtro `[^a-z0-9]`.
  - O caso de teste "ˆangulo" não demonstra o defeito interno para U+02C6, porque o acento fica na borda da palavra.
- **Testes de normalização:** 41 verdes (`registros/teste_verde.txt`).
- **Suíte completa** (CPython 3.11.9): 2454 aprovados, 4 pulados e 2 falhas (`registros/suite_candidato.txt`).
  - **Base comparável**, acrescentada depois da revisão: `bf46d51f` sem a correção, na worktree da noite de 30/09, com
    `src`/`tests` idênticos ao HEAD (`registros/suite_base.txt`). Resultado: 2447 aprovados, 4 pulados e as mesmas 2
    falhas (`caracterizacao_blocos[Fundamentos-de-Redes-Tutor]` e `pdf_markdown actualtext`).
  - Os +7 aprovados do candidato são exatamente os testes novos, e as falhas são idênticas por ID. **Nenhuma regressão
    nova.**

## Replay integral (offline, 7 cursos)

Runner: `replay_cru05.py`. Ele segue esta ordem:

1. fixa `src.__path__` na worktree;
2. carrega os módulos de replay da principal, só para leitura;
3. compara as decisões por ID sem gold;
4. só depois usa o gold para avaliar.

Cada execução levou cerca de 140 s. Ao final, conferi que nenhum módulo `src` foi carregado de fora da worktree.

| execução | bloco | unidade | subunidade primária | subunidade aceita |
|---|---|---|---|---|
| captura congelada do W-Z2 (23/09, `f941ac33`) | 223/237 | 248/284 | 86/251 | 109 |
| **base**: `src` atual sem a correção (`replay_base.json`) | 223/237 | **249/284** | 86/251 | 109 |
| **candidato**: com a correção (`replay_candidato.json`, `--referencia replay_base.json`) | 223/237 | 249/284 | **85/251** | 108 |

- **Base × captura congelada:** 1 material diferente, em dois campos. `CG exercicios-sobre-curvas-html` muda de unidade,
  de `unidade-02` para `unidade-07`, e passa a acertar a unidade. Também muda de subunidade, de vazia para `hermite`,
  sem efeito no placar da primária nem da aceita. Isso foi omitido na versão revisada e apontado pela revisão do GPT.
  A atribuição ao `eebc698c` (24/09, W-AB), posterior à captura, é inferida pela data, não provada. A referência do
  aceite é, portanto, a base atual: 223/249/86, a mesma do CRU_LIMPO de 26/09 (`replay_base.json`, sha256 `e024d396…`).
- **"31 × 6":** o runner sela, antes do gold, as diferenças contra a captura W-Z2, comparando o objeto `final` inteiro
  (31 no candidato). As 6 mudanças contra a base vêm depois, com `--referencia`, sem selo próprio. O diff dos 6 IDs foi
  refeito pela revisão diretamente sobre `decisoes`.
- **Candidato × base:** 6 decisões de subunidade mudam; bloco e unidade não mudam.
  - SO, 1 material: `1205-laminas-gerencia-de-memoria`, de `swapping` para `memoria-virtual`.
  - TCC, 5 materiais: aula-10, aula-11, aula-12, aula-15 e aula-17.
  - Resultado: **0 ganhos e 1 perda**. A perda é `TCC aula-10-linguagens-reconhecíveis-e-linguagens-decidíveis`, de
    `linguagens-reconheciveis-e-decidiveis` (certo) para `maquinas-de-turing`.
  - As outras 5 mudanças ficam fora da régua ou trocam um erro por outro.
- **A perda do diagnóstico de 23/09** (TCC `aula-09`, atribuída ao fragmento `aveis`) não mudou: o material está em
  `maquinas-de-turing` na base e no candidato.

## Leitura

- A correção é tecnicamente certa: as palavras deixam de ser partidas.
- Ela muda o vocabulário que a 2ª passada propaga entre materiais, e o saldo nos 7 cursos é −1.
- **Hipótese, não medida:** com "reconheciveis" e "decidiveis" inteiras, os termos propagados para
  `maquinas-de-turing` pelos doadores do TCC ficam mais fortes e puxam a aula-10. Isso apontaria de novo para a
  propagação sem suporte, que é o núcleo do CRU-05, e não para a normalização.
- Ajustar a correção para recuperar a aula-10 seria regra encaixada no gold. Não foi feito.

## Decisão pendente

1. **Descartar a correção.** Manter o defeito documentado; o CRU-05 fica com resultado negativo registrado.
2. **Medir o mecanismo da perda**, só como diagnóstico, instrumentando a 2ª passada nas duas execuções e sem mudar
   regra. Serve para confirmar ou refutar a hipótese da propagação.
3. **Aceitar a correção mesmo com −1**, como correção de texto, contra o critério de integração vigente. Não recomendado.

## Revisão do ChatGPT Pro (01/10)

Parecer integral em `revisao_gpt_pro_cru05_01-10.md` (sha256 `16c92d06…`), sobre o pacote
`cru05_decisoes_01-10.zip` (`92728997…`).

**Veredito:** opção 2 (medir o mecanismo da perda, só como diagnóstico); aceite não cumprido; não integrar o candidato.

**Pontos factuais, corrigidos acima:**

- comentário do U+02C6;
- campo de subunidade do CG contra W-Z2;
- "31 × 6";
- suíte da base, que faltava.

**Restrição à hipótese da propagação:** `vocab_unit` subtrai do vocabulário dos doadores os tokens dos rótulos e aliases
da unidade. Se "reconheciveis"/"decidiveis" já estiverem num tópico da unidade, eles não podem virar aliases novos de
`maquinas-de-turing`. A causa pode estar na 1ª passada, na confiança/ambiguidade do receptor, nos doadores, nas partes de
rótulo, na guarda do título ou na regra de seção.

**Decisões propostas pela revisão, todas dependentes de Gate do usuário:**

1. fixar a referência atual por conteúdo (`replay_base.json`, `e024d396…`), mantendo a W-Z2 como histórica;
2. CRU-02 (b) como posição documental;
3. diagnóstico curto do CRU-05:
   - par instrumentado com fidelidade integral;
   - atribuição pela primeira divergência e por contraste controlado;
   - parada após o par;
4. medição do CRU-03 com universo e definições congelados antes, tabela lateral e gold só para pontuar proposta
   congelada;
5. VOCAB à parte.
