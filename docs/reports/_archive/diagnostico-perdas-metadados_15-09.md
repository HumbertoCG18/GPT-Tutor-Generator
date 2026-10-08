# Diagnóstico das perdas de metadados, 15/09

Escopo: perdas dos braços ordem (sete cursos) e datas_cards (ES2/IA).
Nove pares material/braço, oito materiais únicos. Não é novo placar nem correção.
Zero chamadas LLM/rede registradas. Sem escrita nas cópias, src ou tutores-produto.

## Reprodução

Comando executado na raiz:

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/diagnostica_perdas_metadados_15-09.py
ruff check docs/reports/_harness-2026-09-04/c1-3/diagnostica_perdas_metadados_15-09.py
```

Evidência: no mesmo diretório, diagnostico_perdas_metadados_verificado_15-09.json.
Replay de apply_anchor_engine em memória: 445 entradas de nove raízes reproduzem
todos os campos temporal_* armazenados. Contexto e texto vêm dos artefatos reais;
voter=None; socket bloqueado. Gold seleciona casos para diagnóstico, nunca entra
na decisão. Campos de unidade são os resultados já medidos: não houve replay do
pipeline completo de unidade nesta etapa.

Remoção do sinal em contexto novo: nove decisões voltam ao bloco anterior,
assertadas por material. Isso confirma dependência local, não autoriza desligar
o sinal globalmente: os ganhos da medição anterior também dependem dele.

## 1. Card inferido exclui o acerto e substitui outra decisão incerta

| Caso, braço ordem | Antes → depois | Evidência causal |
|---|---|---|
| MF exerciciosdafny1 | bloco-12 → bloco-11 | Alinhamento sem sinal lexical próprio escolhe semana anterior; janela [10,11] exclui 12 |
| MF terminacao | bloco-12 → bloco-11 | Duas semanas casam um token; preferência pela mais cedo escolhe [10,11] |
| SO laminas-sockets-material-alternativo-em-pt | bloco-09 → bloco-06 | Faixa de âncoras [06,07] exclui 09; ambos têm score 0 |

MF: card_stream._align usa título+rótulo, não o corpo. Execução de _toks mostrou
ExerciciosDafny1 → ['dafny1'], mas Introducao ao Dafny → ['dafny']. Os cinco
scores daquele material nas semanas são 0, -0.001, -0.002, -0.003, -0.004.
A ordem monotônica o mantém na semana escolhida pelos predecessores. Para
terminacao, as semanas concorrentes têm 0.999 e 0.998: o desconto cronológico
decide, não evidência que separe os dois assuntos.

SO: week_label é "14/04 Lâminas: IPC"; material sem data própria recebe a faixa
das âncoras da seção. A janela original tinha bloco-09, score 1.239939, mas
decisão flagada. A alternativa fica entre 06 e 07, ambos score zero: empate
escolhe 06, continua flagado e ainda assim é adotado.

Causa de promoção: anchor_engine.py:278-291 aceita alternativa quando muda o
bloco OU remove a flag; não exige que a alternativa deixe de ser incerta.
Formação da janela: card_stream.py:80-108 (alinhamento), :126-153 (âncoras).
O caso SO reproduz especificamente substituição por candidato sem evidência
lexical. Não prova que todas as decisões flagadas devam ser preservadas.

## 2. Datas de seção ampliam a competição e o léxico troca o vencedor

| Caso, braço datas_cards | Antes → depois | Competição observada |
|---|---|---|
| ES2 microsservicos3 | bloco-04 → bloco-10 | Janela passa de cinco para sete blocos; 10 entra e supera 04 |
| IA analise-exploratoria-de-dados-exemplo-1 | bloco-04 → bloco-05 | Janela de um vira dois blocos; 05 ganha por margem pequena |

ES2: treze datas do card Microsserviços produzem uma janela de seção ampla.
O bloco correto 04 permanece candidato: score 2.398342, tokens api/gateway/spring.
O bloco 10 entra: 2.940774, autenticacao/autorizacao; vence, flagado. Não houve
perda do bloco correto no parsing de datas; houve nova competição lexical.

IA: datas 16/03 e 18/03 produzem blocos 04 e 05. Antes, topic fornecia só 04,
com decisão sem flag. Depois, labels tem precedência e o léxico decide:
04 = 0.634284 (dados); 05 = 0.662488 (analise/resultados), margem 0.042573.
O resultado passa a flagado. A proteção do fallback card para decisões
confiantes NÃO protege esta troca: labels atua antes, na cascata principal.

Fontes: window_provider.py:326, card_block.py:174, moodle_labels.py:152,
disambiguator.py:217. O JSON contém janelas e scores completos.

## 3. Unidade curricular herda a classificação temporal do bloco

ES2 microsservicos5 e microsservicos7 passam a acertar seus blocos 08/09 no
braço ordem, mas esses blocos carregam unidade-02 (DevOps), enquanto a régua
curricular desses materiais aceita unidade-01 (Arquitetura de Software).

microsservicos7: o scorer já escolhe unidade-01; unit_block_conflict registra
essa escolha. reconcile_unit_with_block a substitui por unidade-02. O mesmo
acontece com microsservicos3 no braço datas_cards. Não é aquisição de alias.

microsservicos5 e azure: unidade lexical ambígua é esvaziada pelo gate; depois
herda a unidade do bloco. Azure continua com bloco errado (01→08, gold09),
mas perde o acerto de unidade que herdava de 01. No SO, sockets também passa
a herdar a unidade do bloco errado. Assim ficam explicadas as quatro perdas
de unidade de ordem e as duas de datas_cards, sem somar materiais repetidos.

Fontes: resolver_apply.py:467 e :494-528; file_map.py:782-813. A regra compara
precedência, não uma comprovação curricular por material. Em microsservicos7,
o conflito já observado basta para localizar a sobreposição. Nos casos ambíguos,
não há vencedor lexical confiável para preservar automaticamente.

## Limites e próximo teste

Não há uma causa única nem prova de que trocar a precedência global resolva.
Hipóteses para avaliação posterior: preservar ambiguidade na janela inferida;
avaliar força e granularidade do sinal antes de substituir uma decisão; separar
localização temporal de unidade curricular. Nenhuma implementada ou pontuada.
As experiências anteriores de precedência continuam válidas; não reabrir regra
global já negativa só porque estes casos perderam.

Preferência Datalab mantida. Nenhum MD foi trocado: os mecanismos reproduzidos
operam com texto fixo. Recuperar captura original Moodle continua pendente;
este diagnóstico usa os metadados históricos já declarados no contraste.

Artefatos preliminares preservados: diagnostico_perdas_metadados_15-09.json e
versão detalhado tinham contrafactual nulo com contexto copiado. Não usar esse
campo para concluir causa. A versão final usou contexto novo; verificado adiciona
bindings explícitos aos wrappers após cinco avisos B023 do Ruff. Replay e os nove
asserts passaram novamente; Ruff passou. Esses ajustes são do diagnóstico,
não mudanças no motor. O grafo foi usado read-only; avisou skill0.9.42/pacote0.9.5.

Próximo passo proposto: teste mínimo do caso SO (alternativa com zero evidência
substitui acerto), antes de desenhar qualquer correção; depois medir seu alcance
nos sete cursos. Corrigir a unidade exige tratar o contrato curricular separadamente.
