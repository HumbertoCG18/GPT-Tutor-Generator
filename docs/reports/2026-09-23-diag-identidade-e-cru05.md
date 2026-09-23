# Diagnóstico delimitado — identidade de `frases_topico` e CRU-05 (proveniência da 2ª passada), 23/09/2026

Só medição. Nada em `src/`, na régua ou nos critérios foi alterado. A 2ª passada não foi desligada, nenhuma grade de
confiança foi criada e nenhum doador foi escolhido pelo gold: o gold só avaliou, depois do registro congelado.
Dados: `c1-3/diag_identidade_propagacao_23-09.{py,json}`.
Execução: uma passada de base instrumentada em memória (harness do W-Z2, 7 cursos, 309 s).
- **Fidelidade:** decisões idênticas por ID à captura congelada da base v2 (`f941ac33…`).
- **Placar recalculado:** bloco 223/237, unidade 248/284, subunidade primária 86/251.

## 1. Identidade: `frases_topico` sem `unit_slug`

**Mecanismo.** `propagar_vocabulario_por_headings` (`resolver_apply.py:315-316`) monta
`frases_topico = {topic_slug: [rótulo] + aliases}` percorrendo todas as unidades. Com slug repetido em duas unidades, a
última sobrescreve. `_subtopico_nomeado_no_titulo` (`:226-236`) usa `frases_topico[vencedor]` na guarda "o título não
nomeia o vencedor" e, com isso, pode consultar frases de outra unidade.

**Teste mínimo (função real, taxonomia sintética).** Unidade u1 com `introducao` ("Introducao ao pipeline grafico") e
`bezier` ("Bezier e Algoritmo de Casteljau"); o título do material nomeia os dois.
- Com u2 também tendo um tópico `introducao`, a decisão confiante é trocada para `bezier`: a guarda leu as frases de u2.
- No controle, sem slug repetido, a guarda bloqueia e nada muda.
Confirmado.

**Alcance e efeito na base v2.**

| medida | valor |
|---|---|
| chamadas da regra do título | 170 |
| slugs repetidos na taxonomia | só SO: `estudo-de-casos` (5 unidades), `conceitos-basicos` (2) |
| chamadas com vencedor de slug repetido | 1 (SO), com frases diferentes das do par (unidade, tópico) |
| decisões que mudariam com a chave (unidade, tópico) | **0** |

O defeito é real e alcançável, mas não afeta nenhuma decisão atual. Nenhum ganho de acurácia é atribuído a ele.

**Proposta separada (não implementada).** Indexar `frases_topico` pelo par: `{(unit_slug, topic_slug): …}` e
`frases_topico.get((unit_slug, vencedor), [])`. O critério de classificação pelo título não muda. O teste é o teste
mínimo acima: com slug repetido, nada deve mudar. A instrumentação já calculou o resultado com o par nas 170 chamadas
(0 mudanças); mesmo assim, a implementação exige Gate 1 e replay integral.

## 2. CRU-05: proveniência da 2ª passada

**Efeito direto por fonte**, por material (sem contagem dupla). Coincide com o W-Z2 (+26/−4, líquido +22):

| razão da mudança | ganho | perda | erro → outro erro | certo mantido | sem gold |
|---|---:|---:|---:|---:|---:|
| propagação de vocabulário (`propagado-headings`) | 11 | 4 | 23 | 2 | 17 |
| partes do rótulo do plano (`rotulo-decomposto`) | 10 | 0 | 8 | 7 | 5 |
| seção do Moodle nomeia o tópico | 5 | 0 | 0 | 0 | 8 |
| título nomeia o tópico | 0 | 0 | 0 | 0 | 1 |

O alcance diretamente medido da propagação é **+11/−4**. Esta tarefa não é caminho para os 140 acertos que faltam na
subunidade.

**Termos acrescentados:**
- 137 propagados de headings e títulos de doadores confiantes;
- 127 partes de rótulo do plano;
- por curso (propagados / partes): IA 62/6, TCC 30/17, CG 19/41, MF 11/17, SO 6/5, ES2 5/12, FR 4/29.

**Qualidade dos doadores dos termos presentes em cada material mudado** (avaliação pelo gold, 1ª passada do doador):

| efeito | n | doadores do termo |
|---|---:|---|
| ganho | 11 | todos certos 8 (MF `recursao` 3/3 e `especificacoes` 2/2, SO `fork`, CG `grafica` 2/2); sem termo acrescentado visível no título/texto 3 (MF) |
| perda | 4 | todos errados 2; mistos 2 |
| erro → outro erro | 23 | todos errados 10; mistos 10; todos certos 1; sem gold 2 (IA 10, CG 6, ES2 4, MF 2, FR 1) |

**As 4 perdas, por proveniência:**
1. FR `04-protocolo-http` e `unidade2-exercicios-http`: o termo `server` foi propagado para "paradigmas
   cliente-servidor" por 2 doadores, ambos errados na 1ª passada. Propagação sem suporte.
2. TCC `aula-09-variacoes-de-maquinas-de-turing`: o termo `aveis` é **artefato de extração**. Os PDFs do TCC trazem
   acentos espaçadores do LaTeX ("Comput´aveis", "Func¸˜oes", com U+00B4, U+00B8 e U+02DC). O `normalize_match_text`
   separa a palavra nesses caracteres ("comput aveis"), e o fragmento virou alias de `maquinas-de-turing`. Na base, 3 dos
   137 termos propagados são fragmentos desse tipo: `defini` (SO), `aveis` e `alise` (TCC). Eles aparecem em 2 materiais
   mudados: esta perda e um material sem gold.
3. CG `transformacoesgeometricas`: `janela`, com doadores mistos. É um dos 5 casos da régua CG com gold vazio; a
   classificação como perda depende daquela adjudicação e não deve ser contada como efeito do algoritmo (ver
   `2026-09-23-regua-cg-adjudicacao-proposta.md`).

**Leitura.** A dependência entre materiais não é defeito em si: todos os ganhos com termo visível vêm de doadores
certos. As perdas e a maior parte dos movimentos sem ganho vêm de doadores errados ou mistos (IA concentra 10 dos 23),
e uma perda vem de artefato de texto. O gold avalia os doadores, mas não pode selecioná-los; separar dependência
legítima de propagação sem suporte exige um sinal sem gold, e esta medição não demonstra qual.

**Candidatos para decisão (nenhum implementado; cada um com Gate 1 e replay integral):**
- **Identidade de texto (acentos espaçadores):** compor ou remover os diacríticos espaçadores (U+00B4, U+02DC, U+00B8,
  U+02C6, U+00A8 …) sem inserir separador. Toca a normalização usada em todo o motor, então o efeito pode ir além da
  2ª passada e só o replay integral o mede. Diretamente ligado a 1 perda, sem ganho prometido.
- **Doador com evidência estrutural própria** (C2 do W-Z2): hipótese sem medição aqui. Para passar no aceite teria de
  preservar os 11 ganhos, cujos doadores eram certos, sem usar o gold para escolher doadores. Precisa de proposta e de
  medição antes de qualquer desenho de regra.
