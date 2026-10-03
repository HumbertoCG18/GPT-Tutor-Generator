# Instruções ao adjudicador — validação externa do regime VOCAB (versão 1, 29/09/2026)

**Situação: preparação. Nenhum pacote foi entregue; nenhum material deve ser rotulado antes do Gate 1.**

Você vai dizer, para cada material de um curso, a que unidade e a que tópico do plano de ensino ele pertence. Sua
resposta é o gold contra o qual o motor será medido depois. Ela precisa vir só do conteúdo do material e do plano.

## 1. O que você recebe (um pacote por curso)

- `plano/`: o plano de ensino original e o texto dele.
- `rotulos.json`: unidades (`U01`, `U02`, …) e tópicos (`U01.T01`, …) extraídos do plano. São os únicos rótulos válidos.
- `materiais/` e `materiais.json`: os materiais do curso, como o professor publicou, com o nome original, a seção e o
  módulo do Moodle em que estavam.
- `moodle_estrutura.json`: nomes e resumos das seções e os rótulos de texto que o professor pôs no Moodle.
- `gold_modelo.csv`: uma linha por material a rotular. Você preenche e devolve como `gold_<SIGLA>.csv`.
- `declaracao_cegamento.md`: você preenche e assina ao terminar.

Links externos aparecem em `materiais.json` com `adjudicavel = false` e não entram no gold: o conteúdo deles não pode
ser congelado.

## 2. O que você NÃO pode consultar, do início ao congelamento do gold

1. Qualquer tutor, build, manifest, `FILE_MAP`, relatório ou tela do GPT-Tutor-Generator deste curso.
2. Qualquer saída do motor (bloco, unidade, subunidade, score, confiança, motivo, tag, placar) de qualquer curso.
3. **Qualquer LLM ou assistente** (ChatGPT, Claude, Gemini, Copilot etc.) para ler, resumir ou classificar material.
   O experimento mede um vocabulário gerado por LLM; um gold com ajuda de LLM ficaria correlacionado com ele.
4. Conversa com o executor (Claude Code) ou com o revisor sobre materiais específicos. Perguntas só sobre o formato
   do arquivo (schema), nunca sobre conteúdo.
5. Colegas ou monitores para decidir rótulos.

Pode: abrir os arquivos do pacote, ler o plano, usar seu conhecimento da disciplina, buscar num livro-texto o sentido
de um termo.

## 3. Como rotular cada material

1. Abra o material e leia o suficiente para saber do que ele trata. O nome do arquivo e a seção do Moodle são pistas,
   não decisão.
2. **`status`:**
   - `avaliado`: material de ensino, exercício, prática, trabalho ou prova;
   - `meta`: documento sobre o curso inteiro (plano, cronograma, regras de avaliação, apresentação da disciplina);
   - `excluido`: arquivo ilegível, vazio, corrompido ou que não pertence ao curso. Explique em `observacao`.
3. **`unidade`** (para `avaliado` e `meta`): a unidade do plano cujo conteúdo o material ensina ou exercita. Use mais de
   uma (`U01|U02`) só se o material cobre as duas de forma substancial ou se, depois de ler, você não consegue decidir
   entre elas. Use `-` quando nenhuma unidade é a resposta certa (comum em `meta`).
4. **`sub_primaria`** (só `avaliado`): o tópico, ou os tópicos, de que o material trata principalmente. Prefira um.
   Use mais de um só quando são igualmente centrais. Use `-` quando nenhum tópico do plano é a resposta certa.
5. **`sub_aceita`** (só `avaliado`): os tópicos de `sub_primaria` mais os que também seriam respostas defensáveis.
   Não acrescente tópico só porque um termo dele aparece de passagem.
6. Dúvida entre dois tópicos: o de maior parte do conteúdo vai em `sub_primaria`, o outro em `sub_aceita`.

## 4. Procedimento

1. Uma passada completa, na ordem do `gold_modelo.csv`. Anote início e fim na declaração.
2. Pode corrigir linhas até entregar. Depois da entrega, o arquivo é validado e congelado por hash e nada muda.
3. Se a validação automática reprovar por forma (id desconhecido, célula obrigatória vazia), você corrige só a forma
   apontada, sem rever outras linhas.

## 5. Declaração de cegamento (preencher e assinar)

Arquivo `declaracao_cegamento.md` do pacote:

```text
Curso: <SIGLA>    Pacote: <sha256 do pacote_manifesto.json>
Início: <data e hora>    Fim: <data e hora>
Declaro que, até entregar o gold deste curso:
[ ] não abri tutor, build, manifest, relatório ou tela do GPT-Tutor-Generator deste curso;
[ ] não vi nenhuma saída do motor para este curso;
[ ] não usei LLM ou assistente para ler, resumir ou classificar materiais;
[ ] não discuti materiais específicos com o executor, o revisor ou terceiros.
Observações: <texto livre>
Assinatura: <nome>
```

Uma caixa não marcada torna o gold daquele curso inválido para a validação (pré-registro, §7.4).
