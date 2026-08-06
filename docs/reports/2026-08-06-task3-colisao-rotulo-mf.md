# Task 3 (fio subject_profile) — colisão de rótulo MF: causa-raiz, matriz de afinidade, DP, rollback

Promovido de `.superpowers/sdd/2026-08-05-fio-subject-profile/task-3-report.md` (gitignored — este
documento é o insumo primário da próxima campanha: colisão-de-rótulo + unificação das fontes de
unidade). Branch `feat/motor-atribuicao` · MF-Tutor
`C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor`. Sign-off do user: SATISFIED (controller);
escrita real autorizada e executada no MF-Tutor. **STATUS FINAL: BLOCKED → ROLLED_BACK.**

## Resumo executivo

O reprocess real rodou sem erro, sem regressão em nada que a régua mede, e respondeu
definitivamente a pergunta em aberto da Task 2 (drift dos 3 `computed_block_id`: era artefato do
probe isolado `retag()`, não da produção — 0/67 mudou no pipeline real). Mas o objetivo central da
campanha — bloco-16 (MF) carregar `unit_slug=unidade-03-verificacao-de-modelos` — **não aconteceu**.
`content_taxonomy.json` tem as 3 unidades corretas (o fio funcionou até aí), mas o matcher
posicional (`assign_units_positional`, DP monotônico global) mantém bloco-16 em `unidade-02` com
confiança 0.4. Causa-raiz identificada e verificada por reconstrução bit-a-bit do algoritmo (não é
bug do fio — é uma característica pré-existente do DP + uma colisão de rótulo de tópico entre
Unidade 01 e Unidade 03 no `content_taxonomy`). Gate (a) — mandatório — FALHA. Por isso: BLOCKED, não
`DONE_PENDING_CONFERENCE`. Nenhum commit feito em nenhum repo.

## Causa raiz (reconstruída e verificada, não especulada)

Reconstrução de `assign_units_positional` fora do pipeline com os insumos reais do disco
pós-reprocess (`course/.timeline_index.json` + `course/.content_taxonomy.json`) bateu 100% contra o
valor persistido, incluindo os blocos não-instrucionais que o `finalize_block` limpa depois (filtro
real: `not block.get("source_kind")`, `index.py:2199`).

**Mecanismo, dois fatores compostos:**

1. **Colisão de rótulo de tópico entre Unidade 01 e Unidade 03.** O `teaching_plan` real tem, dentro
   da seção de abertura da Unidade 01 ("1.3 Abordagens para Verificação Formal"), um bullet de
   pré-visualização: *"1.3.1. Verificação de Modelos (Model Checking)"*. `build_content_taxonomy`
   cria um tópico para esse bullet sob **Unidade 01** e enriquece seus aliases com headings reais do
   material de aula (`'VERIFICAÇÃO DE MODELOS'`, `'Verificação de Modelos e Lógica Temporal'`,
   `'checagem de modelos'`) — conteudisticamente da Unidade 03, mas anexados à cópia de Unidade 01
   porque o enriquecimento casa por TEXTO do rótulo, não por unidade. Efeito: `_unit_tokens(unidade-01)`
   passa a incluir `temporal`, criando um **empate 4×4** entre unidade-01 e unidade-03 na afinidade
   de bloco-16 (tokens do bloco: `{exercicios, ferramenta, logica, modelos, temporal, verificacao}`):
   ```
   overlap com unidade-01: [logica, modelos, temporal, verificacao]   score=4
   overlap com unidade-02: [exercicios, logica, verificacao]           score=3
   overlap com unidade-03: [logica, modelos, temporal, verificacao]   score=4   <- empate com u01
   ```
   A investigação de 2026-08-05 (`2026-08-05-unit-sources-investigacao.md`, Apêndice E) tinha medido
   u01=3/u03=4 (vitória limpa, margem 1.0) — hoje é 4/4. A taxonomia mudou de estado entre a
   investigação e agora (mesmo `subject_profile`/`teaching_plan`, mas o enriquecimento de aliases por
   headings do material pode ter mudado com o rollout flag-ON `c7b7498`, entre a investigação e esta
   task). Reproduzido nos dois lados (matriz completa abaixo).

2. **DP monotônico global, não escore local.** `assign_units_positional` (`unit_matcher.py:52-118`)
   maximiza a soma de afinidade da sequência INTEIRA sob a restrição de índice de unidade
   não-decrescente. bloco-16 não é o último candidato-aula da sequência real: os filtros de produção
   (`not source_kind`, `index.py:2199`) incluem também bloco-17 ("revisão", tokens quase vazios) e
   bloco-20 ("devolução de provas", idem) depois de bloco-16. Como esses 2 blocos finais não têm
   sinal que recompense avançar até unidade-03, e bloco-16 está EMPATADO (não vence sozinho), o ótimo
   global do DP não compensa avançar de unidade numa aula só sem retorno na cauda — o tie-break
   (`empate → menor índice`, `unit_matcher.py:84-88,92-98`) prefere ficar em unidade-02 para bloco-16
   e toda a cauda.

   **Prova por reconstrução manual do DP** (17 blocos, sequência real de produção): a tabela `dp[i][u]`
   recalculada à mão a partir da matriz de afinidade abaixo reproduz o valor do disco EXATO
   (`unidade-02`, conf 0.4) em TODOS os 17 blocos, incluindo bloco-16. Não é divergência de
   implementação nem bug de leitura — é o comportamento correto e determinístico do algoritmo hoje,
   dado o empate de sinal.

## Matriz de afinidade real (17 blocos-candidato, produção, pós-reprocess)

```
block       u01   u02   u03   tokens
bloco-01      0     0     0   apresentacao, disciplina
bloco-02      2     0     0   formais, metodos
bloco-03      2     2     1   exercicios, logica, predicados, revisao
bloco-04      6     1     0   arvores, caso, conjuntos, equacoes, estudo, exercicios, indutivos, listas, recursivas
bloco-05      5     0     0   arvores, inducao, listas, por, provas
bloco-06      3     2     0   exercicios, interativa, isabelle, prova, teoremas
bloco-07      0     1     0   exercicios, revisao
bloco-08      0     0     0   aulas, suspensao
bloco-10      2     3     1   exercicios, hoare, logica
bloco-11      2     8     1   correcao, invariantes, laco, logica, parcial, programas, terminacao, total
bloco-12      1     1     0   dafny, terminacao
bloco-13      5     2     1   arrays, colecoes, conjuntos, dafny, logica, programas, sequencias
bloco-14      0     0     0   academico, day, evento
bloco-15      3     3     1   autocontrato, dafny, exercicios, ghosts, logica, objetos, orientacao, programas
bloco-16      4     3     4   exercicios, ferramenta, logica, modelos, temporal, verificacao   <- EMPATE u01/u03
bloco-17      0     1     0   exercicios, revisao
bloco-20      1     0     0   devolucao, provas
```

Resultado do DP (recomputado com os insumos reais do disco, bate 100% com o persistido em
`course/.timeline_index.json`, os 17 blocos): todos os blocos 07/08/10-16 permanecem em unidade-02
(unidade-01 vence só até bloco-06). unidade-03 nunca é alcançada por nenhum bloco.

## Conference table — 12 blocos de aula × unidade atribuída (estado curado, pós-reprocess)

| Bloco | Unidade atribuída | Conf | Tópico (topic_text) |
|---|---|---|---|
| bloco-01 | unidade-01-metodos-formais | 0.4 | disciplina |
| bloco-02 | unidade-01-metodos-formais | 0.6 | introducao metodos formais |
| bloco-03 | unidade-01-metodos-formais | 0.4 | logica predicados |
| bloco-04 | unidade-01-metodos-formais | 0.8 | conjuntos indutivos equacoes recursivas arvores |
| bloco-05 | unidade-01-metodos-formais | 0.8 | inducao arvores |
| bloco-06 | unidade-01-metodos-formais | 0.6 | interativa teoremas isabelle |
| bloco-10 | unidade-02-verificacao-de-programas | 0.6 | logica hoare |
| bloco-11 | unidade-02-verificacao-de-programas | 0.8 | logica programas correcao parcial total terminacao invariantes |
| bloco-12 | unidade-02-verificacao-de-programas | 0.4 | terminacao introducao dafny |
| bloco-13 | unidade-02-verificacao-de-programas | 0.4 | logica programas dafny colecoes arrays sequencias conjuntos |
| bloco-15 | unidade-02-verificacao-de-programas | 0.4 | logica programas orientacao objetos dafny ghosts autocontrato |
| **bloco-16** | **unidade-02-verificacao-de-programas** ⚠️ deveria ser unidade-03 | 0.4 | verificacao modelos logica temporal ferramenta |

Contra o plano de ensino real (01 Métodos Formais / 02 Verificação de Programas / 03 Verificação de
Modelos): as primeiras 11 linhas batem com o plano. A linha 12 (bloco-16) é literalmente o conteúdo
da Unidade 03 e continua rotulada como Unidade 02 — o problema que a campanha inteira existe pra
resolver persiste.

## Gate (b)/(c) — `computed_block_id`, 67 entries — PASS (fecha a pergunta aberta da Task 2)

```
pre entries: 67   post entries: 67
key_mismatch: []
changed count: 0
```

Zero mudanças em `computed_block_id` nos 67 entries, incluindo os 3 flagados na Task 2
(`logicadehoare` bloco-10, `classes-parte1`/`classes-parte2` bloco-15 — idênticos pré/pós, IDs e
blocos de destino byte-a-byte iguais). Únicas diferenças: `auto_tags` (categoria
`topico:`/`unit:`/`subunit:`, explicitamente permitida — a fonte que os gera mudou, não o valor de
bloco/unidade).

**Veredito:** a hipótese "disco estava stale, o recompute fresco é que está certo" é FALSA — o
pipeline de produção real e completo (`RepoBuilder.incremental_build()` →
`regenerate_pedagogical_files`, com `_apply_curation_overrides` + `_apply_timeline_post_transforms` +
`attach_block_summary_fields` na ordem certa) reproduz exatamente o valor gravado em disco. O drift
que a Task 2 observou era um artefato do probe isolado (`scripts.retag_manifest.retag(persist=False)`,
que pula `attach_block_summary_fields` e outras etapas do fluxo completo) — não algo que acontece na
produção real.

## Achados extra

- **`unit_confidence=1.0` pré-cura em bloco-16 era stale.** O DP real nunca produz 1.0 (valores
  possíveis: 0.4/0.6/0.8). Pós-cura caiu para 0.4. O `1.0` do disco pré-cura era resíduo de rodada
  muito anterior (provavelmente Junho, com curation ou algoritmo diferente), carregado adiante por
  reprocessos sucessivos sem nunca ser recalculado.
- **Corrupção `U+FFFD` pré-existente no `teaching_plan`.** `sp.teaching_plan` (fonte:
  `%APPDATA%/GPTTutorGenerator/subjects.json`, live `SubjectStore`) contém literalmente
  `'\ufffd\ufffd'` no trecho `"1.3.1. Verifica\ufffd\ufffdo de Modelos"` — dado já corrompido na
  fonte, não introduzido pelo reprocess. Só ficou visível porque `content_taxonomy` deixou de ser
  `{units:[]}` e passou a carregar o texto real do plano. Fora de escopo desta task (editar
  `subjects.json` não era uma escrita autorizada); **consertar antes da próxima cura**.

## Rollback executado (2026-08-06, decisão do user via controller) — STATUS FINAL: ROLLED_BACK

Snapshot pré-cura: commit `f83adc9fe8509bc49d68eba11f2e327afda0800e` (2026-08-06 13:10:49 -0300,
commit vazio — confirma repo tracked já limpo antes de começar) + 5 sidecars gitignored copiados
para o scratchpad com `SHA256SUMS.txt`.

```
$ git -C Metodos-Formais-Tutor checkout -- .
$ rm -f Metodos-Formais-Tutor/manifest.json.bak
$ cp <scratchpad>/mf-snapshot-pre/content_taxonomy.json           Metodos-Formais-Tutor/course/.content_taxonomy.json
$ cp <scratchpad>/mf-snapshot-pre/timeline_index.json              Metodos-Formais-Tutor/course/.timeline_index.json
$ cp <scratchpad>/mf-snapshot-pre/assessment_context.json          Metodos-Formais-Tutor/course/.assessment_context.json
$ cp <scratchpad>/mf-snapshot-pre/tag_catalog.json                 Metodos-Formais-Tutor/course/.tag_catalog.json
$ cp <scratchpad>/mf-snapshot-pre/semantic_profile.generated.json  Metodos-Formais-Tutor/course/.semantic_profile.generated.json
```

Verificação sha256 dos 5 sidecars restaurados vs `SHA256SUMS.txt` gravado no snapshot pré-cura — os 5
batem byte-a-byte. Estado final:

```
$ git -C Metodos-Formais-Tutor status --porcelain -uall
(vazio — 0 linhas, tracked E untracked)
$ git -C Metodos-Formais-Tutor rev-parse HEAD
f83adc9fe8509bc49d68eba11f2e327afda0800e   (= snapshot pre-cura-u3, inalterado)
```

Sanity checks pós-rollback (`verify_units.py` e `fase4_prova_D9.py`) idênticos ao estado pré-cura —
MF continua WARN (`parser=3 indice=2`), motor não vê diferença nenhuma (flag-OFF byte-idêntico,
det 48/58=82.8% cw1, voter 51/58=87.9% cw0 calls0). Nenhum commit de Task 3 em nenhum repo; repo do
projeto sem alterações além dos reports (`.superpowers/` é gitignored).

## Concerns para a próxima campanha

1. **O objetivo central não foi alcançado.** O fio funciona — a taxonomia tem as 3 unidades reais —
   mas isso não se propaga até `unit_slug` por bloco por causa do empate de sinal + comportamento do
   DP monotônico na cauda. Consertar exige trabalho novo: (a) desfazer a colisão de rótulo entre a
   menção-prévia de "Verificação de Modelos" na Unidade 01 e o tópico real da Unidade 03 no
   `build_content_taxonomy` (bug genérico — provavelmente afeta qualquer plano cujo texto de abertura
   de unidade cite o título de uma unidade futura), OU (b) curadoria manual pontual via
   `.timeline_curation.json` para bloco-16 (mecanismo já existe, `_apply_curation_overrides`, mas é
   ação humana por bloco, não automatizável).
2. Investigar se os outros 4 cursos (SO/ES2/IA/TCC) têm o mesmo padrão de colisão de rótulo — sinal
   genérico, não peculiaridade do MF.
3. Corrigir o `U+FFFD` em `subjects.json` (teaching_plan do MF) antes da próxima cura.
4. Working tree do MF-Tutor está limpo pós-rollback — nenhuma ação pendente ali.
