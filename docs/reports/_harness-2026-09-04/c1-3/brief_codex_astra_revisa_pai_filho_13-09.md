# Brief 10 para o astra (read-only, esforco LOW): REVISE e CORRIJA a contagem pai x filho feita pelo AGY — 2026-09-13

Ordem do usuario: *"Delegue o AGY para fazer isso, e depois, para o astra revisar e corrigir alguma coisa caso precise"*.
"Isso" = o passo que voce mesmo recomendou no brief 9: medir nos 7 cursos quantos erros de subunidade sao **o pai vencendo
o proprio filho**, antes de decidir se vale flag em `src/`. **Resposta curta.** MEDIDO x HIPOTESE, `arquivo:linha`.

## 1. O que o AGY fez

Dois modelos, independentes, mesmo brief (`c1-3/brief_agy_pai_filho_13-09.md` — leia, sao as definicoes exatas):

- `c1-3/resposta_agy_pai_filho_gemini-3.1-pro-high.json`
- `c1-3/resposta_agy_pai_filho_claude-opus-4-6-thinking.json`

Formato: o JSON de fora e o envelope do AGY; a resposta esta no campo `response` (string com o JSON do schema
`c1-3/pai_filho_schema_13-09.json`). Se algum dos dois estiver vazio, truncado ou fora do schema, diga isso — nao
complete por ele.

**Historico que muda a leitura:** a PRIMEIRA rodada dos dois modelos falhou igual — os dois tentaram rodar um script
("vou processar com um script Python para garantir precisao") e o modo headless do AGY nega `command`; sairam sem JSON
(arquivados como `*.FALHOU-command.json`). As saidas que voce revisa sao a SEGUNDA rodada: brief + os dois CSV **inline pelo
stdin, com instrucao de nao usar nenhuma ferramenta**. Ou seja, **e classificacao de 109 linhas por leitura, sem codigo** —
os proprios modelos sinalizaram que isso e fragil. Espere erro de contagem e trate a sua reproducao deterministica como a
referencia.

**Entradas que o AGY leu** (as mesmas que voce deve usar):
- `c1-3/erros_subunidade_cru_honesto_13-09.csv` — os 109 erros de ACEITO do cru honesto (braco C, 142/251)
- `c1-3/pai_filho_topicos_13-09.csv` — 217 topicos dos 7 cursos (`curso, unit_slug, slug, code, kind, label`), extraidos
  de `.motor3eixos/<curso>/course/.content_taxonomy.json`

**O que eu ja sei da estrutura, verificado:** as 7 taxonomias sao listas PLANAS (0 subtopicos aninhados); parentesco so
existe pelo `code`. **O IA nao tem nenhum `code` e todos os 20 topicos sao `kind=topic`** — nao ha pai x filho la por
construcao. O FR tem `3.21` com `kind=topic` (parece `3.2.1` digitado sem ponto).

## 2. O que eu quero de voce

1. **Reproduza a classificacao deterministicamente** (voce pode rodar Python read-only e imprimir; nao escreva arquivo)
   com as definicoes exatas do brief do AGY. Mostre os `totais` e o `pai_vence_filho` por curso.
2. **Compare com cada saida do AGY:** totais batem? Liste as linhas em que cada modelo errou, com a classe correta.
3. **Critique as definicoes, nao so a execucao.** O parentesco por prefixo de `code` e suficiente? O `3.21` do FR deveria
   contar como filho de `3.2`? No IA, ha outro parentesco recuperavel **sem inventar** (ex.: estrutura do plano)? Se nao,
   diga que o IA fica fora desta medicao.
4. **O tamanho:** quantos dos 109 erros sao pai vencendo filho (primario, e via `extras`)? Em quantos cursos? Isso
   justifica a flag em `src/` que voce mencionou, ou e um padrao de 1 curso (os 4 zips do FR sao o mesmo professor e a
   mesma aula — *"quatro arquivos nao sao quatro validacoes"*)?
5. **O que NAO concluir** desta contagem (ela conta relacao estrutural entre o que o motor escolheu e o gold; nao prova
   que o pai venceu por tokens genericos — isso so o score mostra).
