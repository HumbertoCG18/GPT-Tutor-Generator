# Pacote completo de fontes locais — medição 15/09

Reconstrução concluída nos sete cursos, sem chamadas LLM/rede registradas.
Documentos originais + captura Moodle local + perfil salvo (plano/SARC), sem
transplantar manifest, pinos, mapas de cards ou decisões do produto.
Destino novo: `.frzero/pacote_fontes_15-09`, um diretório por tutor.

## Resultado medido

Referência: reconstrução crua anterior, não a cópia herdada do produto.
Mesmos 316 materiais da régua: 303 comuns, 13 ausentes mantidos no denominador.

| Eixo | Cru anterior | Pacote completo | Ganhos | Perdas | Denominador comum |
|---|---:|---:|---:|---:|---:|
| Bloco | 169/237 | 210/237 | 47 | 6 | 231 |
| Unidade | 234/284 | 239/284 | 9 | 4 | 271 |
| Subtema aceito | 99/251 | 108/251 | 9 | 0 | 243 |
| Subtema primário | 76/251 | 84/251 | 8 | 0 | 243 |

Na população comum, os numeradores são os mesmos; usar os denominadores da última
coluna. Não há crédito atribuído a material ausente. Gold indisponível não é zero.

| Curso | Bloco antes→depois | Unidade antes→depois | Aceito antes→depois | Primário antes→depois |
|---|---|---|---|---|
| MF | 45→50/66 | 59→61/66 | 29→29/58 | 25→25/58 |
| SO | 29→36/39 | 23→27/37 | 5→8/15 | 4→7/15 |
| IA | 25→38/42 | 39→39/42 | 5→5/39 | 4→4/39 |
| ES2 | 11→27/28 | 26→25/28 | 2→8/28 | 2→7/28 |
| TCC | 26→26/27 | 17→17/18 | 9→9/11 | 7→7/11 |
| CG | 33→33/35 | 70→70/93 | 42→42/82 | 28→28/82 |
| FR | sem gold | sem gold | 7→7/18 | 6→6/18 |

Contagem herdada anterior: 222/253/142/100, não reexecutada nesta etapa.
Pacote completo recupera 41 dos 53 acertos de bloco perdidos no saldo anterior,
mas ainda fica 12 abaixo da contagem herdada. Saldo não identifica os mesmos
materiais recuperados e não equivale a uma aprovação sem regressões.

## Gates e proveniência

- 338 entradas/fontes: MF67, SO42, IA61, ES2 35, TCC27, CG86, FR20. Conjuntos de
  origens iguais à referência, sem ambiguidades; hashes dos documentos e dos
  metadados de entrada verificados. Sete capturas conferidas contra o hash do
  diagnóstico anterior e novamente no destino; nenhuma recaptura remota.
- Sete perfis de entrada iguais à referência. IDs, períodos, linhas de origem e
  sessões do cronograma iguais antes de aplicar gold ordinal. Nenhum pino manual
  de bloco/unidade/subunidade preenchido nos manifests reconstruídos.
- 75 textos divergiram em bytes, exclusivamente pelo caminho do novo repositório
  nas referências a imagens: MF17, SO6, IA20, ES2 11, TCC7, CG10, FR4. Normalizar
  somente esse prefixo torna todos os 338 textos idênticos à referência.
- Sete builds completed=true, failed_entries=[], calls={}. Bloqueios locais de
  socket/API e voter/compilação desligados; não é bloqueio global de rede do SO.
- Extração local mantida, sem nova conversão Datalab. A preferência por metadados
  Datalab não foi testada nem revertida; este contraste trata fontes de plataforma.
  O perfil salvo ainda é entrada herdada declarada: não prova autonomia a partir
  de PDFs puros nem atualização/fidelidade da captura frente ao Moodle remoto.

O driver copia somente contents.json bruto, executa o build existente, deriva
sinais com backfills Moodle existentes e executa incremental_build. Mapas de
datas são produzidos pelo parser, não copiados. A opção de semestre usada no
backfill fornece o ano do cronograma; o perfil de semestre não foi alterado.
O contraste mede o pacote completo e seu reprocessamento, não efeitos isolados
de cada campo. Não somar os braços de ablação anteriores a este resultado.

## Regressões e raiz reproduzida

Perdas de bloco: MF quatro (três ProvasIndutivas sem bloco e terminacao→11),
SO uma (laminas-sockets-material-alternativo-em-pt→06), IA uma
(analise-exploratoria-de-dados-exemplo-1→05). Perdas de unidade: o mesmo material
de SO e microsservicos5, microsservicos7, azure de ES2. Ganhos/perdas individuais
e previsões estão no JSON completo, não apenas os saldos acima.

Replay adicional de MF reproduziu todos os campos temporais em 134 entradas
(67 em cada cópia). Com nomes e frases do plano reais, auto_detect_category
classifica os três arquivos ProvasIndutivas_EspecificaçõesRecursivas*.pdf como
provas. Regra: src/utils/helpers.py:682; importador: stash_import.py:104.
A categoria já estava errada antes: prova matemática foi tratada como avaliação.

Comprovação da cadeia: categoria provas → tier2_due_scope
(src/builder/routing/motor/due_window.py:41) → lexical=False
(apply.py:91). Antes, janela temática [05] permitia decisão. Depois, janela de
labels [05,06,07] com voter ausente retorna None (anchor_engine.py:253), apagando
os campos temporais. Assim, o acerto antigo escondia um erro de categoria.

Dois controles em memória, sem regravar tutor nem somar ao placar:
1. Retirar apenas datas de cards: janela temática [05,06], continua None nos três.
2. Habilitar lexical=True somente na chamada de diagnóstico: bloco05 nos três.

Isso reproduz o mecanismo, não valida habilitar lexical para provas acadêmicas
reais. A distinção prova matemática/avaliação deve preceder qualquer alteração
global de prioridade. Conflitos bloco/unidade e cards incertos continuam questões
separadas, conforme diagnósticos anteriores.

## Comandos e arquivos

Diretório dos scripts/logs/JSON: docs/reports/_harness-2026-09-04/c1-3.
Comandos registrados abaixo já foram executados; os drivers recusam destinos
ou resultados existentes. Não reexecutar sobrescrevendo os arquivos desta rodada.

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/pacote_fontes_15-09.py --curso MF
```

Mesmo comando por SO, IA, ES2, TCC, CG e FR. Saída capturada com Tee-Object em
pacote_fontes_MF_15-09.log e respectivos nomes por curso. Três filas locais,
sem agentes: MF/SO, ES2/IA, TCC/CG/FR; cada curso escreve em destino independente.
Cada destino contém _inputs_15-09.json, _capture_inputs_15-09.json e
_build_result_15-09.json. Tempos em segundos: MF3980.57, SO533.06, IA3502.43,
ES2 2281.0, TCC2549.28, CG979.96, FR273.21.

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/verifica_pacote_fontes_15-09.py --saida verificacao_pacote_7cursos_15-09.json
python -B docs/reports/_harness-2026-09-04/c1-3/replay_abstencoes_pacote_15-09.py
```

Segundo comando grava replay_abstencoes_pacote_raiz_15-09.json. Resultados
parciais e dois replays preliminares preservados. Ruff inicialmente apontou B023
no novo reprodutor; parâmetro da lambda vinculado explicitamente e replay/Ruff
reexecutados com sucesso. Skills de avaliação e verificação orientaram gates,
denominadores e separação entre teste em memória e placar; python-patterns
orientou o reprodutor sem alteração do motor.

Não houve edição de src, .ablacao, tutores-produto ou .motor3eixos nesta etapa;
alterações preexistentes do worktree preservadas. Configuração da régua continua
regua (veto=texto, SEM curadoria do benchmark=puro), cursos MF,SO,IA,ES2,TCC,CG,FR.
Sete builds encerrados, sem processos desta reconstrução pendentes. Sem commit/push.

## Decisão proposta, não implementada

Manter o pacote completo como referência experimental: recuperar a captura omitida
melhora os quatro saldos, mas não elimina regressões. Próximo teste focal:
classificação de prova matemática versus avaliação, com controle de provas reais,
antes de mexer na precedência temporal. Promoção ao produto e correção em src
continuam dependendo de autorização.
