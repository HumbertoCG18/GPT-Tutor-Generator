# Raiz da cadeia de metadados, 15/09

Diagnóstico autorizado: captura → metadados → janela → unidade, incluindo acertos.
Sem correção, sem novo placar, sem reextração, sem chamadas LLM externas. Scripts
leem cópias e operam em memória. MD Datalab continua preferido; não foi substituído.

## Correção de premissa anterior

Existem payloads raw/moodle/contents.json nos SETE tutores da cópia herdada
.frzero/implementacao_taxonomia_15-09. Seus SHA256 são iguais aos arquivos dos
respectivos tutores-produto locais. Isso não certifica atualidade remota, mas
prova disponibilidade de captura local para repetir parsing sem rede.

Nas reconstruções, só CG/FR carregaram contents.json. O driver cru_fontes_15-09.py
buscou esse arquivo apenas em stash.parent/raw/moodle; ele não consultou a
captura guardada no tutor. Logo parte da chamada "herança do produto" era
captura bruta omitida do pacote de entrada, não decisão ou curadoria do produto.
Minha recomendação de recapturar Moodle antes de continuar foi prematura.

## Medição de recuperabilidade

| Curso | Entradas de origem comum | Estrutura rederivada exata | Captura na reconstrução |
|---|---:|---:|---|
| MF | 62 | 61 | não |
| SO | 39 | 37 | não |
| IA | 57 | 55 | não |
| ES2 | 35 | 35 | não |
| TCC | 27 | 25 | não |
| CG | 86 | 70 | sim |
| FR | 20 | 20 | sim |

Total 303/326: os três campos de estrutura, nos 303 casamentos, coincidem
exatamente com o histórico. As 23 entradas restantes não casam; preencher
moodle_label via casador existente não acrescentou casamentos. Este universo
inclui entradas fora da régua: não confundir com os 303 materiais gold comuns
da medição anterior. Campo semanal vazio também participa da igualdade; igualdade
de estrutura não significa que exista data resolvível para todo material.

Datas/formato de 23/24 cards históricos são reproduzidos. A exceção é TDE do ES2:
histórico 03/07/2026, captura parseada 06/07/2026; esta última não gera bloco
na timeline usada. Não copiar o derivado antigo como se fosse captura atual.
A origem dessa diferença histórica não foi determinada nesta etapa.

## Transformações que mudam o significado da evidência

1. Captura e ingestão não são a mesma operação. moodle_pull.py:178 persiste o
   payload no tutor; stash_import.py:126 cria entradas a partir dos arquivos e
   do sidecar de nomes. backfill_moodle_structure_repo (moodle.py:330) só consulta
   o payload no destino; sem ele retorna sem alterar campos. Não houve falha de
   parser que explique a ausência geral dos cinco cursos: a entrada não chegou.
2. backfill_moodle_structure_from_api (moodle.py:298) transforma posição em
   associação: módulo herda o label datado anterior; labels consecutivos viram
   um run. card_stream.py:80 alinha esse run às semanas, usando título/rótulo e
   categoria, com desempate cronológico. Isso é inferência por arquivo, não
   declaração explícita do professor sobre cada arquivo.
3. parse_card_dates (moodle_labels.py:318) agrega por SEÇÃO; derive_card_block_map
   (:152) transforma suas datas em união de blocos. provider_labels
   (window_provider.py:50) aplica essa mesma janela aos arquivos daquela seção.
   A fonte pode ser correta e a janela insuficiente para distinguir os arquivos.
4. _build_timeline_index (index.py:2236) calcula unidade de bloco por marcos ou
   alinhamento posicional. Isso não é uma unidade curricular extraída como
   declaração direta do SARC. resolver_apply.py:494-518 usa essa unidade na
   reconciliação do arquivo; file_map.py:782-813 faz a herança/sobreposição,
   excetuando unidade manual ou explicitamente numerada. Não transporta a
   incerteza do matcher do bloco para essa decisão.

IA ilustra consumidores incompatíveis: o payload real contém seção
"Semana 3 - 16/03 a 20/03 - Machine Learning e Dados" e label com
"16/03: ML e Dados (continuação)" / "18/03: Aprendizado Supervisionado".
parse_card_dates reconhece formato B sem ano; o backfill de week_label procura
dd/mm/aaaa em labels. Por isso ordem ficou sem janelas, enquanto datas_cards
teve efeito. Não era ausência de toda informação temporal no original.

## Controles: a estrutura também ajuda

No braço ordem, as janelas dos 5 ganhos MF, 5 dos 8 ganhos SO com janela card,
e 16 ganhos ES2 contêm o bloco gold. As três perdas MF/SO excluem o bloco gold.
Dos 43 acertos mantidos MF, 39 têm janela card e 37 incluem o gold: dois acertos
resistem apesar de janela card inadequada. Logo janela errada não implica
necessariamente perda: importa se a cascata a promove.

No braço datas_cards do IA, todas as 40 entradas comuns com gold têm o bloco
correto na janela, incluindo 14 ganhos, 24 acertos mantidos, uma perda e um
erro mantido. No ES2, todas as 26 janelas datadas também contêm o bloco correto,
incluindo a perda. Nesses casos, ampliar a competição e escolher dentro dela,
não perder o gold na captura, é o mecanismo observado.

## Unidade: inferência usada como autoridade

Fornecendo o bloco GOLD, a unidade efetiva desse bloco (incluindo vizinho quando
necessário) é compatível com o gold curricular em 203/220 materiais comuns com
ambos os eixos e unidade de bloco disponível. Diverge em 17: MF2, SO8, IA1,
ES2 3, TCC1, CG2. FR não possui gold de bloco/unidade. Isso não mede 17 perdas
atuais: mede incompatibilidade entre duas classificações, inclusive sob bloco certo.

Replay puro do matcher posicional ES2 reproduz bloco08→unidade02/conf0.6 e
bloco09→unidade02/conf0.4; marcos não se aplicam. Um probe do contrato de
reconcile_unit_with_block, com unidade lexical distinta e sem pinos/explicitude,
retorna unidade do bloco igualmente para block_confidence 0, 0.4 e 1.
Confiança lexical .99 nesse probe é valor controlado, não medição de um arquivo.

Portanto, a hipótese estrutural é sustentada em dois pontos: contexto coletivo
vira restrição individual; classificação temporal inferida vira autoridade
curricular. Não é defeito de tamanho de glossário nem prova de que Datalab
resolveria. Também não autoriza remover essas fontes: os controles mostram
ganhos e 203 compatibilidades que precisam ser preservados.

## Evidência e limites

Comando, na raiz:

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/rastreia_cadeia_metadados_15-09.py
ruff check docs/reports/_harness-2026-09-04/c1-3/rastreia_cadeia_metadados_15-09.py
```

Saída nova no mesmo diretório: cadeia_metadados_verificada_15-09.json, com hashes,
casamentos, controles, discordâncias e probes. cadeia_metadados_15-09.json é
prévia preservada, antes dos probes. Primeira execução parou por presumir mapa
de cards no CG; leitor foi ajustado à ausência legítima e executado novamente.
Ruff passou; asserts dos probes passaram; zero tentativas de rede registradas.
Nenhuma cópia, src ou tutor-produto foi escrita; nenhum commit/push.

Próximo passo proposto, não executado: montar entrada experimental com documentos
originais + payload Moodle local identificado por hash + plano/SARC, gerando
metadados pelos parsers, sem transplantar campos do manifest. Só então avaliar
o fluxo completo e desenhar tratamento de granularidade/incerteza, preservando
os acertos. As 23 entradas sem vínculo e o TDE divergente permanecem explícitos.
