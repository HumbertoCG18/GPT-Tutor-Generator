# Metadados e regressão de blocos: medição concluída

Autorizado pelo usuário após a reconstrução dos sete cursos. Zero chamadas LLM;
src, tutores-produto, .ablacao e .motor3eixos não são destinos de escrita.

1. Inventariar as 50 perdas de bloco entre materiais presentes, com diferenças
   de metadados, pinos e disponibilidade de Markdown Datalab comprovada em disco.
2. Controle: reprocessar uma cópia nova da reconstrução sem alterar entradas.
   Exigir mesmas previsões e taxonomia; parar se houver drift.
3. Braços separados: datas (`posting_date`, `posting_date_created`), rótulos
   (`moodle_label`, `source_section`), ordem (`moodle_section_index`,
   `moodle_module_index`, `moodle_week_label`) e união desses campos.
   Sem pinos, categorias, títulos ou previsões do produto. Restaurar campos em
   TODAS as origens únicas comuns, nunca selecionar só os erros.
4. Avaliar os quatro eixos contra a reconstrução, conservando o denominador
   completo. Texto consumido e taxonomia devem permanecer invariantes.

Piloto ES2/IA; candidato com efeito positivo segue para os sete cursos. Valores
históricos do manifest servem ao contraste causal, não provam recuperabilidade
offline. Se só existirem no produto, registrar essa dependência explicitamente.

Preferência do usuário: Markdown Datalab existente primeiro. Validar arquivo,
registro da extração e vínculo com a fonte; chunks são candidatos quando o
consolidado não existe. Não confundir frontmatter gerado pelo app com metadado
extraído do PDF, nem data de publicação Moodle com data escrita no documento.
Não trocar o corpo Markdown no braço de metadados: isso seria outro fator.

## Execução e gates

Controle inicial ES2 inválido: cópia só textual omitiu oito ZIPs, removidos pelo
reprocessamento. Preservado. Rodada `integral` copia todos os arquivos; ES2/IA
passaram com mesmas entradas, texto, taxonomia e previsões.
No piloto ES2, ordem/semana recuperou 16 blocos mas perdeu saldo de uma unidade.
O braço mínimo `ordem` segue para caracterização nos sete cursos, não para deploy.

| Faixa | Destinos exclusivos | Gate |
|---|---|---|
| IA | curso IA por braço | concluir os quatro fatores |
| MF/SO | cada curso por braço | controle antes de ordem |
| TCC/CG/FR | cada curso por braço | controle antes de ordem |

Reprocessamentos locais em paralelo, sem agentes/LLM. Cada rodada exige texto,
taxonomia e entradas invariantes; controles também exigem previsões idênticas.

## Contraste adicional justificado pelo consumidor

`provider_labels` lê `.card_block_map.json`, não `posting_date`; o mapa não existe
na reconstrução de ES2/IA. `card_entry_block_ids` rederiva blocos pelas datas dos
rótulos. Braço `datas_cards`: somente registros históricos `source=labels` com
datas ISO e formato, `block_ids=[]`; nenhum UUID, pino ou mapeamento manual do
produto é devolvido. Essas datas históricas não estão nos downloads locais de
ES2/IA; o resultado mede dependência, não recuperabilidade sem recaptura Moodle.

## Resultados medidos

Referência desta rodada: reconstrução desde fontes locais, não o braço C.
Denominadores completos preservados; material ausente não recebe acerto.
Estrutura/semana inclui texto e datas do rótulo semanal, não só ordem numérica.

| Eixo, sete cursos | Reconstrução | Estrutura/semana | Ganhos | Perdas |
|---|---:|---:|---:|---:|
| Bloco | 169/237 | 195/237 | 29 | 3 |
| Unidade | 234/284 | 239/284 | 9 | 4 |
| Subunidade aceita | 99/251 | 105/251 | 6 | 0 |
| Subunidade primária | 76/251 | 81/251 | 5 | 0 |

| Curso | Bloco antes → depois | Ganhos/perdas de bloco | Unidade antes → depois |
|---|---|---|---|
| MF | 45 → 48/66 | +5/-2 | 59 → 61/66 |
| SO | 29 → 36/39 | +8/-1 | 23 → 27/37 |
| IA | 25 → 25/42 | 0/0 | 39 → 39/42 |
| ES2 | 11 → 27/28 | +16/0 | 26 → 25/28 |
| TCC | 26 → 26/27 | 0/0 | 17 → 17/18 |
| CG | 33 → 33/35 | 0/0 | 70 → 70/93 |
| FR | sem gold de bloco | não aplicável | sem gold de unidade |

Piloto ES2/IA: datas de publicação isoladas não alteraram nenhum eixo.
Rótulos isolados: ES2 +1 unidade e +1 aceita, sem perdas; IA inalterado.
União dos campos teve o mesmo placar de estrutura/semana nos dois cursos.
Datas dos cards, contraste separado: ES2 bloco 11→19/28 (+9/-1), unidade
26→26/28 (+2/-2), aceita 2→4/28, primária 2→4/28; IA bloco 25→38/42
(+14/-1), demais eixos inalterados. Não somar resultados dos dois braços:
a combinação não foi medida.

No ES2, estrutura/semana perde unidade em microsservicos5, microsservicos7 e
azure. Os dois primeiros passam a acertar o bloco enquanto erram a unidade.
Isso localiza uma interação entre eixos; não prova sozinho qual regra corrigir.

## Causa sustentada e limites

Reposição isolada de metadados altera atribuições com texto e taxonomia iguais:
a ausência desses sinais explica parte da regressão. Há dois caminhos distintos:
card_windows (card_stream.py:110) consome estrutura/semana; provider_labels
(window_provider.py:50) consome o mapa de cards. card_entry_block_ids
(card_block.py:174) rederiva blocos pelas datas. posting_date não substitui isso.

Preferência Datalab aplicada no inventário: entre 50 perdas comuns, quatro têm
MD/chunks existentes com evidência direta de extração Datalab (ES2 1, IA 3).
Nos outros 46, a busca nos caminhos registrados e nos originais não comprovou
esse artefato; isso não prova que nunca houve extração Datalab. Os candidatos
Datalab examinados não forneceram frontmatter com os campos Moodle necessários.
Corpo Markdown não foi substituído: esta rodada NÃO mede superioridade nem ganho
de placar do Datalab. Metadados da plataforma devem vir da captura Moodle;
MD Datalab tem preferência para conteúdo/metadados documentais comprovados.

Os campos históricos vieram da cópia herdada. ES2/IA não têm os rótulos originais
nos downloads locais verificados. Portanto, ganho causal não equivale a fluxo
autônomo reproduzível desde fonte. Não promover nenhum braço: existem regressões.

## Comandos e arquivos

Diretório dos scripts e placares: docs/reports/_harness-2026-09-04/c1-3.
Comandos abaixo executados com esse prefixo nos nomes dos scripts; nomes de saída
são resolvidos pelo próprio script nesse diretório.

```powershell
python -B inventario_metadados_15-09.py --originais --saida inventario_metadados_originais_15-09.json
python -B metadados_blocos_15-09.py --curso CURSO --braco BRACO
python -B pontua_metadados_15-09.py --cursos MF,SO,IA,ES2,TCC,CG,FR --bracos controle,ordem --saida placar_metadados_7cursos_15-09.json
python -B pontua_metadados_15-09.py --cursos ES2,IA --bracos datas_cards --saida placar_datas_cards_piloto_15-09.json
```

Matriz executada: controle/ordem nos sete cursos; datas/rotulos/conjunto/datas_cards
em ES2 e IA. Logs: metadados_BRACO_integral_CURSO_15-09.log. Destinos exclusivos:
.frzero/metadados_BRACO_integral_15-09/TUTOR. Cada destino contém
_metadados_result_15-09.json com alterações e invariantes. Placar dos cinco braços
iniciais ES2/IA: placar_metadados_piloto_15-09.json. Esses arquivos incluem os flips
por material; os logs do motor mostram cobertura de atribuição, não acurácia gold.

Auditoria final: 22 rodadas válidas, sete controles com previsões idênticas,
zero tentativas registradas de rede/LLM, entradas/textos/taxonomia invariantes.
Comparação por ID de todos os campos manual/pinned: zero mudanças. A consulta
inicial dos flips de unidade tentou indexar valores nulos; refeita com guarda
de nulidade, sem alterar placares. Ruff dos três scripts passou; git diff --check
sem erros (avisos LF/CRLF). Todos os processos da medição terminaram.
.motor3eixos não foi reprocessada nesta etapa; configuração conferida: regua,
veto=texto, sem curadoria do benchmark, MF/SO/IA/ES2/TCC/CG/FR.
Nenhuma alteração em src nesta medição, nenhum commit/push.

Próximo passo proposto, não executado: obter captura original dos metadados Moodle
faltantes e reproduzir sua ingestão; depois isolar as regressões por material sem
introduzir exceções por curso ou decisões derivadas do gold. Troca para corpo
Datalab exige outro contraste, separado dos metadados de plataforma.
