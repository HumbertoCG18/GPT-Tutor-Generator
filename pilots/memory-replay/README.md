# Piloto: replay offline de seleção de memória (issue #45)

Mede, sem chamar nenhum modelo, o que aconteceria com um conjunto de memórias
candidatas se decisões de descarte **simuladas** fossem aplicadas sobre o baseline.
A pergunta que o piloto responde é só esta: *dado este rótulo manual do que era
necessário, o descarte simulado perderia algo, e quanto texto sairia?*

```
python pilots/memory-replay/replay.py pilots/memory-replay/example.json
python -m unittest discover -s pilots/memory-replay -p "test_*.py"
```

Só stdlib (Python 3.11 usado na medição). O relatório sai em JSON (ASCII) no stdout;
erro de entrada sai no stderr com código 2 e stdout vazio. O script não grava arquivo,
não abre rede nem banco e faz zero chamadas LLM.

## Entrada

JSON local **redigido manualmente**. Chaves desconhecidas são recusadas (typo em
`required_ids` viraria "sem rótulos" em silêncio).

| Campo | Tipo | Observação |
|---|---|---|
| `version` | inteiro `1` | `true` e `1.0` são recusados |
| `task`, `project` | string não vazia | `project` define o baseline |
| `candidates[]` | `id`, `project`, `text` (strings não vazias), `protected` (booleano estrito) | IDs únicos no arquivo inteiro |
| `required_ids` | lista de IDs, **opcional** | rótulo manual; só avaliação |
| `simulated_decisions[]` | `id` + `decision` opcional | no máximo uma entrada por ID |

Também são recusados: JSON malformado, chave JSON duplicada, `NaN`/`Infinity`, ID
repetido ou desconhecido em `required_ids`/`simulated_decisions`, texto não
codificável em UTF-8. BOM UTF-8 é aceito.

## Regras

1. **Baseline**: candidatos cujo `project` é igual ao `project` da entrada, na ordem do
   arquivo. Os de outro projeto saem e são listados em `excluded_other_project`.
   Candidato `protected` de outro projeto é **erro**: não some em silêncio.
2. **Deduplicação exata**: mesmo `text`, caractere a caractere (sem trim, caixa ou
   normalização Unicode). Fica o primeiro ID; `provenance` guarda todos os IDs do
   grupo. Se qualquer membro é protegido, o grupo é protegido.
3. **Ramo simulado**: recebe exatamente o conjunto elegível do baseline. Um item só sai
   com decisão explícita e válida `drop`, no ID canônico, e se não for protegido.
   Todo o resto preserva, com o motivo em `simulated.preserved`:
   `keep`, `uncertain`, `error`, `missing` (sem decisão), `invalid` (valor fora do
   vocabulário, tipo errado ou campo `decision` ausente), `protected` (drop ignorado).
   Decisão apontando para alias de duplicata ou para outro projeto não exclui nada e
   aparece em `not_applicable_decisions`.
4. **Rótulos não selecionam**: as funções de seleção não recebem `required_ids`; eles
   entram só depois, na avaliação. Um `required_id` conta como retido se qualquer ID do
   grupo (canônico ou alias) foi selecionado. `required_id` de outro projeto aparece
   como perdido nos dois ramos.

Estrutura/IDs errados em `simulated_decisions` derrubam o arquivo (erro de autoria). Já
o *valor* de `decision` simula saída de modelo, que pode vir torta: por isso é
fail-open e reportado, nunca exclusão.

## Métricas e o que NÃO é medido

- `selected_ids`, `provenance`, `protected_ids`, `dropped_ids`, `preserved`.
- `chars` (code points) e `utf8_bytes` dos textos selecionados; duplicata conta uma
  vez. **Caracteres não são tokens** e o relatório não os converte.
- `tokens`: sempre `null`, com `measurement.tokens = "not_measured"`. O piloto **não
  mede tokens** e não os estima a partir de caracteres ou bytes. Não há flag nem
  tokenizer opcional: a CLI aceita só o caminho do JSON, os imports são apenas stdlib
  (`argparse`, `json`, `sys`) e qualquer outra opção é recusada pelo parser (código 2).
- `evaluation`: `lost_ids` e `recall` por ramo. Sem `required_ids` →
  `undefined_no_labels` (`recall` e `lost_ids` nulos); lista vazia →
  `undefined_no_required`. Nunca 100% fictício.
- `measurement.cost = "not_measured"`, `llm_calls = 0` (do replay; nada diz sobre o
  custo de produzir decisões reais).

## Limites deste recorte

- O replay **não decide** nada: as decisões vêm escritas no JSON. Ele não prova que um
  modelo decidiria assim, nem ganho real de qualidade, custo, latência ou de qualquer
  seletor tipado/TypeSafe. Prova apenas a contabilidade sobre o caso fornecido.
- `example.json` é **100% sintético**. Nenhum dado de histórico, sessão ou banco real
  foi lido para construir o piloto.
- Sem exportador de banco: não há leitura de claude-mem nem de outra base. Um caso real
  exige redação manual (remover nomes, caminhos, segredos e conteúdo de terceiros)
  antes de virar JSON, e não deve ser versionado sem essa revisão.
- Baseline = "tudo do projeto". Não modela ranking, orçamento de contexto, recência
  nem dedup aproximada.
- `required_ids` é julgamento manual de uma pessoa sobre uma tarefa; recall aqui é
  relativo a esse rótulo, sem concordância entre anotadores.

## Amostragem futura (fora deste recorte)

Antes de qualquer conclusão agregada: definir a população (tarefas por projeto e
período), sortear os casos em vez de escolher os memoráveis, fixar o tamanho da amostra
e o critério de rótulo **antes** de ver as decisões simuladas, rotular `required_ids`
às cegas em relação ao ramo simulado e reportar casos sem rótulo como indefinidos, não
como acerto. Exportador e decisões vindas de modelo real pedem issue e Gate 1 próprios.
