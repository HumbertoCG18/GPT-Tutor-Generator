# Brief para segunda opinião (Codex, perfil astra, read-only) — camada 3 do motor de atribuição, 2026-09-11

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator (gerador). Tutores gerados ficam ao lado, em
C:/Users/Humberto/Documents/GitHub/<Nome>-Tutor. Você está em sandbox read-only: não edite, não rode nada que chame
Gemini, não proponha commit. Responda em português, no máximo 1 página mais tabelas, cada achado com evidência
(arquivo:linha ou log:linha) e marcado como MEDIDO ou HIPÓTESE.
Abreviação usada abaixo: `c1-3/` = `docs/reports/_harness-2026-09-04/c1-3/`.

## 1. O problema

O motor atribui cada material de um curso a bloco (semana), unidade e subunidade. Três camadas usam LLM: (1) voter de
bloco, (2) vocabulário compilado por LLM (1 chamada por unidade, `src/builder/core/vocabulary_compile.py`), (3) resumos
de código por Gemini (`src/builder/core/code_summarization.py`, 1 por arquivo/zip, gravados em `code_curation.json`).
O usuário quer no máximo duas camadas. A candidata a cortar é a 3, trocando o produtor de `code_curation.json` pelo
substituto determinístico v2 (sintetizado dos `.md` que o motor já gera para cada membro do zip).

Fato estrutural (MEDIDO, `src/builder/routing/resolver_apply.py:439-450`): material zip ou código não tem `.md`
próprio; o único texto que chega à decisão de unidade e subunidade é o resumo em `code_curation.json`. Sem resumo
nenhum, o zip entra vazio.

## 2. O que foi feito hoje (11/09)

1. `vocabulary_compile._bundle` passou a incluir os nomes-base dos membros do zip no bundle da compilação (antes o zip
   contribuía vazio). Diff: `git diff src/builder/core/vocabulary_compile.py`. Teste:
   `tests/test_vocabulary_compile.py::test_bundle_zip_leva_nomes_base_dos_membros`.
2. Compilação do vocabulário LLM nos 4 cursos que estavam bloqueados por sidecar manual: SO 6, IA 4, ES2 2, TCC 4
   chamadas (gemini-3.5-flash). Script e logs: `docs/reports/_harness-2026-09-04/c1-3/compila_vocab_um_curso.py`,
   `compila_vocab_{SO,IA,ES2,TCC}.log`. Arquivos gravados: `<Tutor>/course/.glossary_curation.llm.json`.
   Achado (MEDIDO, IA): o LLM propôs `Rede Perceptron` e `MLP` para "Modelos Preditivos" e `filter_terms`
   (`vocabulary_compile.py`, regra `tn in file_names`) derrubou os dois porque coincidem com títulos de materiais.
3. Medições em cópias (`.ablacao/`), tripwire de Gemini, 0 chamadas, regime "motor puro" (sem curadoria manual, sem
   voter, com vocabulário LLM; `scripts/motor_puro.py`, `scripts/ablacao_rapida.py`,
   `docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py`). Régua: `docs/reports/subunit_gt_<SIGLA>.csv`, linhas
   `scorable=yes`, 151 materiais em MF, SO, IA, ES2, TCC. Acerto "com-extras" = predição no gold ou nos extras aceitos;
   "primário" = igual ao gold.

## 3. Resultados (MEDIDO), subunidade, vocabulário NOVO nos 4 cursos

| curso | sem resumos | determ v2 | com resumos (Gemini) | n |
|---|---|---|---|---|
| MF | 52 | 50 | 51 | 58 |
| SO | 8 | 8 | 8 | 15 |
| IA | 36 | 36 | 38 | 39 |
| ES2 | 16 | 20 | 21 | 28 |
| TCC | 10 | 10 | 10 | 11 |
| total | 122 | 124 | 128 | 151 |
| primário | 103 | 105 | 105 | |

Bloco 185/199 e unidade 180/190 idênticos nos três regimes. Logs: `c1-3/codigo_sem_puro_b.log`,
`c1-3/codigo_sem_puro_b2.log` (repetição, mesmo 122), `c1-3/codigo_determ2_puro_b.log`, `c1-3/codigo_com_puro_b.log`.
Referência de 06/09 na régua antiga de 93 (não comparável): com 87, determ 78, sem 71 (`c1-3/b_prop_puro.log`,
`c1-3/codigo_determ2_puro.log`, `c1-3/codigo_sem_puro.log`).

Regra de decisão combinada com o usuário, traduzida: cortar a camada 3 se `determ >= com - 2`. Deu 124 contra 128.

Errados no estado DETERM: `c1-3/errados_determ_vocabnovo.txt`. Errados no estado SEM (id -> predito | gold):

```
MF   archive-of-formal-proofs-355fb8 -> abordagens-para-verificacao-formal | provadores-de-teoremas
MF   exemplos -> exemplos-de-aplicacoes | provadores-de-teoremas
MF   exercicios-conjuntos -> logica-de-hoare | softwares-de-suporte-a-verificacao
MF   introducao-zip -> (vazio) | softwares-de-suporte-a-verificacao
MF   tiposindutivos -> (vazio) | softwares-de-suporte-a-verificacao
MF   exemplos-zip -> (vazio) | softwares-de-suporte-a-verificacao
SO   exemplo-criacao-de-processos-no-unix-linux-{filho,teste x3} -> estudo-de-casos | chamadas-de-sistema
SO   exemplo-threads-em-c-exemplo{1,2,3} -> estudo-de-casos | conceitos-basicos
IA   rede-perceptron-or-em-python -> introducao-ao-aprendizado-de-maquina | modelos-preditivos
IA   mlp-xoripynb -> (vazio) | modelos-preditivos
IA   aula-sobre-agrupamento-parte-2-hierarquico -> introducao-ao-aprendizado-de-maquina | modelos-descritivos
ES2  roteiro1, roteiro2, roteiro3 -> (vazio) | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  roteiro3-gateway -> cliente-servidor | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  microsservicos2 -> orientada-a-microsservicos | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  microsservicos3 -> estilos-e-padroes-arquiteturais | estudo-de-caso-arquitetura-orientada-a-microsservicos
ES2  kubernetes -> estudo-de-caso-integracao-e-implantacao | plataformas-de-devops
ES2  roteiro4, roteiro5, roteiro6, roteiro7, roteiro7-history-service -> gerenciamento-da-configuracao | estudo-de-caso-integracao-e-implantacao
TCC  aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia -> linguagens-reconheciveis-e-decidiveis | (vazio)
```

## 4. Regime "com resumos, vocabulário ANTIGO" (MEDIDO), mesma régua de 151, `c1-3/codigo_com_puro_vocabantigo.log`

Nesta régua "puro", `ablate` apaga o sidecar manual; logo "vocabulário antigo" para SO, IA, ES2 e TCC significa
NENHUM vocabulário (nem o sidecar do professor), que é exatamente o estado da baseline de 06/09.

| curso | com resumos, vocab antigo | com resumos, vocab novo | delta |
|---|---|---|---|
| MF | 51/58 | 51/58 | 0 |
| SO | 8/15 | 8/15 | 0 |
| IA | 4/39 | 38/39 | +34 |
| ES2 | 5/28 | 21/28 | +16 |
| TCC | 8/11 | 10/11 | +2 |
| total | 76/151 (primário 56) | 128/151 (primário 105) | +52 |

Leitura: nenhum curso regrediu com o vocabulário novo. Os 7 erros do SO existem nos dois regimes, então a hipótese da
pergunta 1(b) está REFUTADA por esta medição: o vocabulário novo não os causou; a pergunta que fica é por que o SO erra
esses 7 em qualquer regime. A lista de errados deste regime está no fim do log.

## 5. Outros fatos medidos hoje que pesam

- Colisão de nomes na extração de zip (`src/builder/core/source_importers.py`, `process_zip`, `safe_name_c` usa só o
  nome-base do membro): 129 arquivos de código mostram o conteúdo de OUTRO zip, em 23 dos 44 zips (CG 88 em 11 zips,
  MF 35 em 8, ES2 6 em 4). Script e log: `c1-3/mede_zips_conteudo_perdido.{py,log}`. Ainda não corrigido: decisão do
  usuário é corrigir depois da decisão sobre a camada 3, porque o reprocesso re-resume zips se a camada 3 ficar.
- 42 dos 44 zips entravam vazios na compilação do vocabulário antes da mudança 1 (`c1-3/mede_opcao_b_zips.{py,log}`).
- `_bundle` corta cada heading em 60 caracteres (`vocabulary_compile.py`, função `_bundle`).
- Os tutores SO, IA, ES2, TCC ainda NÃO foram reprocessados com o vocabulário novo; só as cópias de medição foram.

## 6. O que NÃO repropor (refutado por medição, `docs/reports/2026-09-08-handoff-confianca.md` §4)

Agrupar por palavras-chave no lugar do scorer; título do vídeo no lugar do hash; piso de score; título com vocabulário
completo; página-índice pelo cabeçalho; triagem da chamada de LLM por sinal determinístico (o sinal não prediz);
"prova é fronteira de unidade"; alias ambíguo como alavanca; automatizar o gold a partir de Moodle e SARC; regra
pai × filho; piso de força na 1ª passada; seção → unidade dona; zero-pad; número na chave.

## 7. Perguntas, em ordem

1. Regressões. (a) MF: sem 52 > com 51 > determ 50. (b) SO 8/15, os 7 errados todos preditos como `estudo-de-casos`;
   HIPÓTESE minha: o vocabulário novo do SO pôs `Pthreads`, `pthread_create`, `Linux`, `Unix` em "3.4 Estudo de
   casos" e "1.3 Estudo de casos" (ver `compila_vocab_SO.log`), puxando os exemplos para lá. O §4 já refuta a hipótese
   para o SO; explique então por que os 7 do SO e o 1 do MF erram, pelos arquivos, e como medir com 0 chamadas.
2. Onde melhorar: no máximo 5 alavancas, ordenadas por ganho esperado na régua de 151, cada uma com arquivo:função,
   custo em chamadas e o experimento de 0 chamadas que a confirma ou mata antes de tocar produto.
3. A regra `determ >= com - 2` é sã para decidir cortar a camada 3? Se não, qual usar, com número.
4. Falhas no desenho da medição: régua 151 contra a antiga 93, `ablate` apagando o sidecar manual, produto não
   reprocessado, `sem` como regime. O que invalidaria uma conclusão tirada daqui.
5. Os 8 roteiros do ES2: o determ recupera 4 dos 5 que o Gemini recupera. O que falta ao determinístico, no texto que
   ele produz (`shim_codigo.py`, função `_sintetico`), para pegar o resto sem LLM.

Arquivos para ler primeiro: `docs/reports/2026-09-08-handoff-confianca.md`,
`docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` (§1, §2.2, §2.4), `docs/reports/pendencias.md` (seção
"NO MAXIMO DUAS CAMADAS LLM", 06/09), e os scripts e logs citados acima.
