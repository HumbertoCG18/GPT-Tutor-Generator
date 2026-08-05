# Plano B — investigação do motor de atribuição

Data: 2026-08-05 · branch `feat/motor-atribuicao` · **READ-ONLY estrito** (nenhum arquivo do
projeto modificado, nenhum commit, nenhum reprocess com `--write`; todos os experimentos
rodaram em memória a partir de scripts no scratchpad).

Repos medidos: `TCC-Tutor`, `Metodos-Formais-Tutor`, `Sistemas-Operacionais-Tutor`.

**Veredito de topo:** os dois casos NÃO são a mesma família. 2a é um confiante-errado por
sinal-fantasma (stopword PT tratada como token discriminante) somado a uma falha de recall
estrutural. 2b não é instabilidade nenhuma — o funil é determinístico e idempotente; o
manifest em disco é que está velho em relação ao índice.

---

## CASO 2a — confident-wrong do TCC (`aula-01` → bloco-02, provider=topic)

### Repro (confirmado hoje)

```
python scripts/fase2_prova_TCC.py
  confiante-e-errado: 1 [('aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-
                          conjuntos-e-enumerabilidade', 'bloco-02', 'bloco-01', 'topic')]
  VEREDITO FASE 2/P4: FAIL (pinos=True cobertura=True confErrado0=False)
```

### Dados do caso (medidos)

```
source_section : 'Semana 1 - Enumerabilidade e Argumento da Diagonalização de Cantor'
title          : 'Aula 01 - Apresentação da Disciplina, Revisão de Teoria de Conjuntos e
                  Enumerabilidade'
course_name    : 'Teoria da Computabilidade e Complexidade'
janela P4      : ['bloco-02', 'bloco-06', 'bloco-17', 'bloco-31']   <-- bloco-01 AUSENTE
decisão        : block_ref=bloco-02 conf=0.6168 band='alta' flag=False method='disamb'
```

Ranking dentro da janela:

| # | bloco | score | hits (material ∩ assinatura) | df_global |
|---|-------|-------|------------------------------|-----------|
| 0 | bloco-02 | 1.0030 | `conjuntos`, **`nao`** | 4, **1** |
| 1 | bloco-17 | 0.3843 | `conjuntos`, `funcoes` | 4, 4 |
| 2 | bloco-06 | 0.2996 | `funcoes` | 4 |
| 3 | bloco-31 | 0.2935 | `conjuntos`, `funcoes` | 4, 4 |

```
discriminante (hits_best - hits_runner) = {'nao'}
rel_margin = (1.0030 - 0.3843) / 1.0030 = 0.6168  >=  MARGIN_TAU (0.55)
```

### Causa-raiz — são DUAS falhas independentes

**Falha A — recall: o bloco correto nunca entra na janela.**

`_block_signature` (`src/builder/routing/motor/disambiguator.py:96-108`) remove os tokens do
nome do curso (`drop = _toks(ctx.course_name)`) e `_toks`
(`disambiguator.py:29-38`) remove os `_GENERIC_STEMS`. Aplicado ao bloco-01:

- `topic_text = 'sobre teoria conjuntos'` → `sobre` cai (stem genérico), `teoria` cai
  (está em "**Teoria** da Computabilidade e Complexidade") → sobra `conjuntos`
- única sessão: `label = 'apresentacao'` → `apresent` ∈ `_GENERIC_STEMS` → cai

**Assinatura final do bloco-01 = `{'conjuntos'}`.** O tópico do card
("Enumerabilidade e Argumento da Diagonalização de Cantor") tem stems
`{argume, cantor, diagon, enumer}` — interseção vazia — então `provider_topic`
(`src/builder/routing/motor/window_provider.py:119-125`) nunca o inclui. **O motor não tem
como acertar este caso**; só pode errar em silêncio ou errar alto.

**Falha B — confiança: o guard D4 é satisfeito por uma stopword.**

`disambiguator.py:184`:

```python
confident = s1 > 0 and s2 > 0 and rel_margin >= MARGIN_TAU and bool(discriminante)
```

O único token que separa o vencedor do runner-up é **`nao`**, vindo do label da sessão do
bloco-02 (`'conjuntos enumeraveis e nao enumeraveis'`). `_toks` só filtra por
`len(t) >= 3`, `not t.isdigit()` e `t[:8] not in _GENERIC_STEMS` — e `_GENERIC_STEMS`
(`disambiguator.py:22-26`) é uma lista de 20 stems de domínio, **sem nenhuma stopword
gramatical do português**. Pior: `df_global['nao'] = 1`, ou seja, a métrica de raridade
classifica a negação como *o token mais discriminante do curso inteiro*.

Confirmado que o projeto NÃO tem essa palavra em lugar nenhum do filtro compartilhado:
`grep 'nao' src/builder/text/stopwords.py` → sem resultado. O motor
(`window_provider._topic_tokens:93-103` e `disambiguator._toks:29-38`) usa filtro próprio,
que não herda `TIMELINE_GENERIC_TOKENS`/`UNIT_GENERIC_TOKENS`.

### (i) Que diferença do índice reconstruído produziu isso

A decisão inteira pendura em **um token de uma string de label de sessão**. O rebuild de
2026-08-04 reescreveu `topic_text`/`sessions[].label` dos blocos; basta o label do bloco-02
passar a conter `nao` (ou o df de `nao` cair para 1) para o `discriminante` deixar de ser
vazio e a decisão saltar de `media+flag` para `alta`. Não houve mudança de lógica: o índice
antigo simplesmente não sorteava esse token. **A regressão cw 0→1 não é uma regressão de
código — é a exposição de um design sem guard**, e ela voltaria sozinha a qualquer nova
edição de cronograma.

### (ii) Sinal ordinal — não existe no motor

O motor não tem nenhum sinal ordinal. `annotate_class_ordinals` /`score_sequence_match`
(`src/builder/routing/sequence.py:33` e `:49`, `SEQUENCE_BOOST=0.20` em
`thresholds.py:163`) existem, mas alimentam **só o funil legado**
(`concept_resolver.py:346`, `file_map`). No motor não há chamada.

Importante separar duas coisas que a spec confundiu: a proibição F-TCC
("o N de `Semana N` NUNCA vira janela", `window_provider.py:87` e `:117`) é sobre o ordinal
**do card** e está correta. O ordinal **do próprio material** (`"Aula 01"` no título)
é outro sinal, legítimo, e está simplesmente ausente. Adicioná-lo é feature nova, não
correção — e não é necessário para zerar o cw.

### (iii) Onde a confiança é atribuída

| Local | Papel |
|---|---|
| `disambiguator.py:184` | `confident = ... and bool(discriminante)` — o gate |
| `disambiguator.py:187-194` | `band='alta'` se confident; senão `confidence_band(rel_margin)` com demoção forçada alta→media |
| `disambiguator.py:140` / `:142` | gate de janela-1 P3/P4 (`_gated_window1_decision`) — mesmo conceito de "discriminante", mesmo furo |
| `thresholds.py:118-131` | `confidence_band` (BAND_HIGH=0.50 / BAND_LOW=0.20) |

### Menor fix honesto — VALIDADO EMPIRICAMENTE

**Fix: lista de stopwords gramaticais PT no filtro compartilhado do motor.** É exatamente
o minor já catalogado como "stopwords PT P4" — ele não é cosmético, é a causa-raiz do cw.
Um único ponto (`_GENERIC_STEMS`, `disambiguator.py:22-26`) cobre os dois consumidores,
porque `window_provider.py:14` importa `_GENERIC_STEMS` de lá. Zero re-tuning de número
(`MARGIN_TAU`, `DATE_DF_MAX`, `BAND_*` intactos).

Medições (simulação em memória, `fase2_prova_TCC.py` completo):

| Conjunto adicionado a `_GENERIC_STEMS` | acc par-colapsada | acc topic | conf-errado | veredito |
|---|---|---|---|---|
| — (hoje) | 84.2% | 16/20 = 80.0% | **1** | FAIL |
| `{nao}` | **84.2%** | **16/20 = 80.0%** | **0** | **PASS** |
| `{nao,sim,com,sem,por,dos,das,nos,nas,uma,que}` | **84.2%** | **16/20 = 80.0%** | **0** | **PASS** |
| + demonstrativos/comparativos (`este,esta,esse,essa,aquele,mais,menos,seus,suas,como,pelo,pela,entre`) | 78.9% ⚠ | 14/20 = 70.0% | 0 | PASS |

**Recomendado: a lista conservadora de 11 palavras-função.** Zera o confiante-errado
mantendo a acurácia byte-idêntica. A lista larga custa 2 casos — **não estender além de
palavras-função**; demonstrativos e comparativos carregam sinal acidental que hoje acerta.

Efeito no caso: sem `nao`, `hits_best = {conjuntos}` ⊆ `hits_runner = {conjuntos, funcoes}`
→ `discriminante = {}` → `confident=False` → band demovida para `media` + `flag=True` →
cai para TIER 3 / funil. **Esse é o comportamento correto**: a Falha A (recall) continua
existindo e o motor honestamente não sabe.

Sobre a Falha A: não tem fix de guard, é recall. Deixar cair em `media+flag` é a
degradação honesta. Um fix de verdade exigiria ou o sinal ordinal do material (item (ii))
ou parar de dropar `teoria` da assinatura quando ela é o *único* token restante do bloco —
ambos maiores que o escopo do cw e a serem decididos por número, não aqui.

---

## CASO 2b — "idempotência do funil-base"

### Veredito: NÃO é não-determinismo. É determinístico E idempotente.

**Evidência 1 — determinismo real (PYTHONHASHSEED).** Recompute completo de
`resolve_unit_block_tags` sobre TCC, 2 execuções por processo, 3 processos com seeds
diferentes:

```
PYTHONHASHSEED=0      run1 == run2: True   FINGERPRINT = 3b57b1644c8847e036ebde2b7151ad1c
PYTHONHASHSEED=1      run1 == run2: True   FINGERPRINT = 3b57b1644c8847e036ebde2b7151ad1c
PYTHONHASHSEED=12345  run1 == run2: True   FINGERPRINT = 3b57b1644c8847e036ebde2b7151ad1c
```

Idêntico. A hipótese "ordenação de `set()`" está **descartada** para este caminho.
Varredura confirmatória: o único `set`→saída ordenada em `src/` é
`sanitization.py:273` (`sorted(set(...))`, já correto). Não há `list(set(...))` em `src/`.

**Evidência 2 — idempotência (recompute do recompute):**

| repo | disk → pass1 | pass1 → pass2 | pass2 → pass3 |
|---|---|---|---|
| TCC-Tutor (27) | **4** mudanças | **0** | **0** |
| Metodos-Formais-Tutor (67) | **3** mudanças | **0** | **0** |
| Sistemas-Operacionais-Tutor (42) | **0** | **0** | **0** |

As 4 do TCC são exatamente as reportadas (`3dm-caetano-gabriel-e-gustavo`,
`cubic-3-edge-coloring`, `integer-programming-0001`,
`programacao-inteira-01-20260617-154423-0000`). As 3 do MF são `logicadehoare`,
`classes-parte1`, `classes-parte2`. SO já convergiu (o flip de ontem foi gravado).

**Conclusão:** o `manifest.json` em disco está STALE em relação ao índice atual. O primeiro
reprocess converge; todos os seguintes são no-op. Não há oscilação. É
**determinístico-e-sensível-ao-input**, não não-determinismo — e a "instabilidade" é
one-shot, não recorrente. Flags ON/OFF não mudam nada aqui: nenhuma delas toca este ramo.

### Causa-raiz — flag de ambiguidade lida e jogada fora

`src/builder/extraction/content_taxonomy.py:1208`:

```python
_period, p_conf, _p_ambig, _ = select_probable_period_for_entry_fn(...)
```

`content_taxonomy.py:1224-1234`:

```python
if _period:                                   # <-- gate SÓ na string
    for block in instructional_blocks:
        if str(block.get("period_label") or "") == _period:
            period_block_id = ...
            block_confidence = float(p_conf)  # <-- aceita 0.0
            block_method = "scorer_only"
            break
```

**`_p_ambig` é atribuída e nunca lida.** `grep -n "_p_ambig" src/` retorna **uma única
linha** em toda a árvore (a 1208). A função já devolve a informação de que não sabe
(`file_map.py:1394`: `ambiguous = best_score < 1.0 or abs(best_score - runner_up_score) < 0.35`,
retornada em `file_map.py:1413`) e o chamador a descarta.

Consequência: um palpite ambíguo de confiança ZERO é aceito como atribuição dura, e o
`_best_instructional_block_fallback` (`content_taxonomy.py:811-871`, o "pega o melhor" da
spec, que ranqueia TODOS os blocos com o scorer real e devolve uma
`relative_margin_confidence` honesta) **nunca é alcançado**, porque `_period` é truthy.

**Traço medido (TCC, as 4 entries — idênticas):**

```
[select_period] cands=27 -> period='1 dia · 06/05/2026' conf=0.0 ambig=True
[select_period] blocos com esse period_label (ordem): ['bloco-16']
=> bloco:bloco-16  conf=0.0  method=scorer_only
```

Enquanto o scorer "pega o melhor", nos MESMOS inputs, tem resposta com margem real:

```
3dm-caetano-gabriel-e-gustavo : bloco-22 (29.39) vs bloco-19 (22.87)   [disco tinha bloco-22]
cubic-3-edge-coloring         : bloco-22 (55.30) vs bloco-19 (41.42)
integer-programming-0001      : bloco-16 (20.5456) == bloco-26 (20.5456)  <-- empate exato
programacao-inteira-01-...    : bloco-16 (20.5456) == bloco-26 (20.5456)  <-- empate exato
```

**Traço SO (`exercicios-p2`, bloco-03 → bloco-16):**

```
[select_period] cands=17 -> period='1 dia · 23/06/2026' conf=0.0539 ambig=False
=> bloco:bloco-16  conf=0.0539  method=scorer_only
```

Note que aqui `ambig=False`. **Um guard só-de-ambiguidade NÃO pega o SO** — só o piso de
confiança pega. O fix precisa dos dois.

### Por que o vencedor muda quando o índice muda

`select_probable_period_for_entry` decide pelo caminho *session-first*
(`file_map.py:1360`: `if session_score >= 1.0`). Qual bloco cruza esse portão primeiro
depende dos labels/datas das sessões do índice. Como a confiança resultante é ~0, a decisão
é uma navalha: qualquer reescrita de label/data no rebuild troca o bloco vencedor sem que
nada no código mude. Determinístico, mas pendurado em ruído.

### Segunda falha, latente (o "empate resolvido por ordem de chegada")

A função devolve um **period_label (string)**, não um bloco. `content_taxonomy.py:1225-1234`
resolve label→bloco pegando o **primeiro** bloco de `instructional_blocks` com aquele label
(`break`). Quando 2+ blocos compartilham `period_label`, a escolha é arbitrária e depende
da ordem de entrada da lista. Nos casos medidos cada label tinha 1 bloco, então **não é o
gatilho ativo** — mas é exatamente o mecanismo descrito no briefing, e está a um
re-bucketing de índice de disparar. (O empate exato `bloco-16 == bloco-26` no scorer bruto
das 2 entries acima mostra que empates reais acontecem neste corpus.)

Ordenação em si está correta: `list.sort` é estável (`content_taxonomy.py:867`,
`concept_resolver.py:375`, `file_map.py:1364`), então o desempate é reprodutível dada a
mesma entrada — o problema não é aleatoriedade, é que o critério de desempate é
"ordem da lista" em vez de algo com significado.

### Sintoma irmão (MF, contagem de linhas dos .md)

Mesma causa, não `set()`. MF move 3 entries no primeiro recompute
(`logicadehoare`, `classes-parte1`, `classes-parte2`); entry que troca de bloco troca de
seção nos índices gerados → contagem de linhas diferente. Não provei end-to-end (regenerar
.md exige escrita, fora do escopo read-only), mas o determinismo por seed já elimina a
hipótese de ordenação de `set` e a idempotência (`pass1→pass2 = 0`) prevê corretamente que
a variação some depois da primeira rodada.

### Menor fix

**Fix principal (uma linha, raiz, cobre todos os chamadores) —
`content_taxonomy.py:1224`:**

```python
if _period and not _p_ambig and p_conf > 0:
```

Ou seja: **ler a flag que a função já devolve** e aplicar um piso de confiança. Cai no
`_best_instructional_block_fallback`, que é o "pega o melhor" que a spec manda e já produz
confiança honesta. Mata as 4 do TCC e o drift do SO num edit só. Não inventa número novo:
`p_conf > 0` é o piso trivial (hoje aceita-se literalmente zero).

⚠ **Isto MUDA atribuições** (TCC: 4 entries saem de bloco-16 para bloco-22/etc.). É mudança
de comportamento, não refactor. Tem que ser medido nos golds antes do rollout.

**Fix opcional (empate latente) — `content_taxonomy.py:1225-1234`:** quando >1 bloco
compartilha o `period_label`, desempatar pelo score do scorer em vez de pegar o primeiro
da lista. Só vale a pena se o fix principal não tornar o ramo inalcançável na prática.

---

## Mapa das tasks mecânicas (19)

| # | Task | file:line | Fix em uma frase |
|---|---|---|---|
| 1 | T1b migração combo em `AppConfig._load` | `src/ui/theme.py:121-122` | A migração é um `if` inline hard-coded (`vision_backend=='ollama'` × 3 modelos); virar tabela `{(backend, modelo_velho): modelo_novo}` para novas migrações não exigirem outra condicional. |
| 2 | T2b `logger.debug` em `load_repo_artifact` | `src/builder/routing/motor/context.py:18-21` | `except Exception: return {}` engole JSON corrompido em silêncio; adicionar `logger.debug("artefato %s ilegível: %s", rel, exc)` (o módulo ainda não tem `logger`). |
| 3 | T3 filtro janela-1 no `fase3_prova` | `scripts/fase3_prova_LLM_MF.py:93` | `if d.flag or r["id"] in series:` não filtra `len(d.window) > 1`, que `AnchorEngine.resolve` (`anchor_engine.py:57`) exige — a sonda superestima o escopo do voto; adicionar a condição. |
| 4 | T4b lock voter cross-processo | `src/builder/routing/motor/llm_vote.py:203` (`threading.Lock`), `:220-225` (`_persist`), `:227-239` (`prune`) | O lock é só in-process; `_persist` faz read-merge-write sem exclusão entre processos — dois reprocess simultâneos se clobberam. Trocar por lock de arquivo (sentinela `O_EXCL`) em volta de `_persist`/`prune`. |
| 5 | T7a double-md5 | `llm_vote.py:49-62` (`content_key`), chamado em `:218` (`has_vote`) e `:250` (`vote`) | O md5 do arquivo inteiro é recalculado por chamada; memoizar por `entry["id"]` num dict de instância. |
| 6 | T7b e2e gate via `regenerate_pedagogical_files` | `src/builder/ops/pedagogical_regeneration.py:419-421`; testes em `tests/test_pedagogical_regeneration_order.py` e `tests/test_tag_catalog.py:325` | Falta um teste e2e que trave a ORDEM `refresh_manifest_auto_tags` → `resolve_unit_block_tags` → `attach_block_summary_fields` (a precedência de método depende dela; ver comentário `content_taxonomy.py:1321-1329`). |
| 7 | T9a ref `"None"` no health | `src/builder/routing/motor/apply.py:50` (origem), `src/builder/artifacts/cronograma_health.py:178` (sintoma) | `[str(r) for r in (decision.window or [])]` transforma `None` na string `"None"`, que passa o filtro `if str(r)` do health e vira candidato fantasma; filtrar na origem: `... if r`. |
| 8 | F3 parent-dir `save_material_curation` | `llm_vote.py:77-82` | `tmp.write_text` estoura se o diretório-pai não existe; `path.parent.mkdir(parents=True, exist_ok=True)` antes. |
| 9 | F3 fold de acento em `source_section` | `llm_vote.py:131` (`detect_same_theme_series`) | `sec = str(...).strip()` cru, sem fold — diverge de `due_window._card_entry:40` e `window_provider._card_entry:23`, que usam `norm_ascii_lower`; usar o mesmo helper. |
| 10 | F3 `match_window_ref` strip/casefold | `llm_vote.py:173-183` | Comparação sensível a caixa (`v in (str(ref), b['id'], b['block_uuid'])`); um voto `"Bloco-13"` cai fora da janela. Casefold nos dois lados. |
| 11 | F3 truncamento do dry-run | `scripts/fase3_prova_LLM_MF.py:104` | `build_vote_prompt(...)[:900]` corta o prompt no dry-run, que existe justamente para auditar o prompt inteiro; remover o slice ou parametrizar. |
| 12 | F3 stopwords PT P4 | `disambiguator.py:22-26` (`_GENERIC_STEMS`), consumido por `window_provider.py:14,101` e `disambiguator.py:36` | **NÃO é cosmético — é a causa-raiz do 2a.** Ver seção 2a: lista conservadora de 11 palavras-função zera o confiante-errado sem custo de acurácia. |
| 13 | F5b filtro `fileurl` em `extract_file_dues` | `src/builder/sources/moodle_labels.py:297-298` | `f.get("type") == "file"` aceita qualquer conteúdo tipo file; falta descartar entradas sem `fileurl` válido (placeholders do Moodle) antes de contar/indexar. |
| 14 | F5b gate de due vazio | `src/builder/routing/motor/due_window.py:58` e `:61-62` | Já há `str(hit.get("due") or "")` no caminho posicional e no filtro de `assign_dues`, mas `resolve_due_window:82` reaceita `due=""` do retorno stem; gate único no `_match_due` de saída. |
| 15 | F5b imports locais | `content_taxonomy.py:832,834,839,1039,1051,1156,1172,1189`; `concept_resolver.py:326,329` | Imports tardios espalhados dentro de funções; consolidar no topo onde não há ciclo real (os de `entry_signals`/`file_map` em `content_taxonomy` têm ciclo declarado — esses ficam, com comentário). |
| 16 | F5b hoist `_stems` | `window_provider.py:120-121` | `_stems(sig)` é recomputado para cada bloco a cada entry; a assinatura por bloco é invariante — cachear em `ctx` (mesmo padrão de `ctx._global_df_cache`, `disambiguator.py:119-128`). |
| 17 | `topics` → `kind` no filtro D-H | `due_window.py:85` | `if not (b.get("topics") or []): continue` exclui bloco de conteúdo cujo `topics` veio vazio; usar `kind` (o campo semântico, já usado em `content_taxonomy.py:966,973`) para separar conteúdo de admin/prova. |
| 18 | `reprocess_assignments` ler `subjects.json` | `scripts/reprocess_assignments.py:71` | `course_meta = manifest["course"]` congela a meta do manifest; ler o `SubjectStore` (`src/models/core.py:333`, `get_app_data_dir()/subjects.json`) para o reprocess usar o perfil vivo. |
| 19 | `manifest.json.bak` tracked no MF | `scripts/reprocess_assignments.py:78-79` | `git ls-files "*.bak"` no MF retorna 5 arquivos versionados (`manifest.json.bak`, `manifest.json.retag.bak`, `code_curation.json.bak`, `course/.timeline_index.json.bak`, `.prebuild.bak`); adicionar `*.bak` ao `.gitignore` do repo gerado (`engine._generated_repo_gitignore_text`) e destrackear. |

---

## Riscos e dependências entre os fixes

1. **2a-fix e 2b-fix são independentes** — caminhos disjuntos (motor `disambiguator` vs
   funil `content_taxonomy`). Podem ir em paralelo.
2. **2b-fix muda atribuições reais.** TCC sai de bloco-16 (conf 0.0) para bloco-22/etc.
   Precisa de medição nos golds TCC/MF/SO antes de qualquer rollout. Não tratar como
   refactor seguro.
3. **2b-fix pode reordenar T17 (D-H `topics`→`kind`)**: os dois mexem em quais blocos são
   candidatos elegíveis. Medir separadamente, não empilhar num commit só.
4. **Não estender a lista de stopwords além das palavras-função** — medido: a versão larga
   custa 2 casos (84.2%→78.9%). Se alguém "melhorar" a lista depois, a acurácia cai em
   silêncio. Vale um comentário no código citando a medição.
5. **T12 (stopwords) é pré-requisito conceitual do gate de janela-1** (`disambiguator.py:140`,
   `_gated_window1_decision`): o mesmo conceito de "discriminante" com o mesmo furo. O fix
   em `_GENERIC_STEMS` conserta os dois de uma vez — não fazer dois patches.
6. **T4b (lock) e T5/T7a (double-md5) tocam o mesmo arquivo** (`llm_vote.py`), junto com
   T8/T9/T10. Cinco tasks num arquivo de 283 linhas: agrupar num commit de higiene do
   `llm_vote`, com o lock separado (é o único com risco de comportamento).
7. **T19 (.bak) é destrutivo em repo do usuário** (`git rm --cached`) — confirmar antes.
8. **Nenhum destes fixes remove a Falha A do 2a (recall).** Depois do 2a-fix o TCC passa com
   cw=0, mas `aula-01` continua atribuído ao bloco errado, agora flagado. Se a métrica de
   aceite mudar de "confiante-errado=0" para "acurácia", este caso reaparece.

---

## Ordem sugerida de execução

1. **T12 — stopwords PT** (lista conservadora de 11). Zera o `FAIL` do
   `fase2_prova_TCC.py` sem custo medido de acurácia. Maior retorno, menor diff, já
   validado empiricamente. Fecha o 2a.
2. **T7/T9a (`ref "None"`) + T2b (logger) + T8/T9/T10 (higiene `llm_vote`) + T11 + T16 + T13**
   — mecânicos, sem mudança de comportamento observável. Um commit por área.
3. **T3 (filtro janela-1 na sonda)** — corrige a instrumentação; fazer ANTES de medir
   qualquer coisa com o `fase3_prova`, senão os números da medição saem enviesados.
4. **2b-fix (`content_taxonomy.py:1224`)** — com medição nos 3 golds no mesmo passo.
   Depois do passo 3 para que a régua já esteja correta.
5. **T17 (D-H `topics`→`kind`)** — medir isolado, depois do 2b-fix, para não confundir as
   duas mudanças de elegibilidade de bloco.
6. **T4b (lock cross-processo)** — sozinho, é o único com risco de deadlock/regressão de
   concorrência.
7. **T14, T15, T1b, T18, T6 (T7b e2e), T19** — limpeza e infraestrutura, sem pressa.

---

## ⚠ Achado extra + quebra involuntária do read-only

**`_build_file_map_timeline_context_from_course` ESCREVE no repo.** Meus diagnósticos —
que só leem e recomputam em memória — deixaram os 3 repos-tutor sujos:

```
TCC-Tutor                  M course/.block_identity.json   (03:20:26)
Metodos-Formais-Tutor      M course/.block_identity.json   (03:20:35)
Sistemas-Operacionais-Tutor M course/.block_identity.json  (03:20:56)
```

Diff em todos: **apenas `last_seen: "..." → "2026-08-05"`**, N linhas (31/21/21). Nenhum
uuid, nenhum `display_id`, nenhuma identidade alterada. Cosmético, mas **é uma escrita que
eu não deveria ter causado** — reporto em vez de reverter em silêncio (reverter também é
escrita não autorizada). Restauração, se desejada:
`git -C <repo> checkout -- course/.block_identity.json`.

As demais sujeiras dos repos são **anteriores** e não são minhas:
`TCC-Tutor manifest.json` (04/08 20:11), `course/.timeline_index.json.bak` (04/08),
`material_curation.json` untracked (04/08 19:31).

**Isto é um achado de verdade, não só um acidente meu:** qualquer sonda "read-only" que
chame `_build_file_map_timeline_context_from_course` (ou seja, todo probe que monte o
contexto do funil) suja o repo-tutor. Vale um `read_only=True` no caminho de leitura, ou
mover o bump de `last_seen` para o caminho de build explícito. Adjacente ao 2b: é mais um
lugar onde "só olhar" muda estado.

---

## Apêndice — scripts de diagnóstico (scratchpad, read-only)

| arquivo | o que faz |
|---|---|
| `diag_2a.py` | Dump completo da decisão de `aula-01`: janela, assinaturas, hits, df, rel_margin, discriminante |
| `diag_2a_fix.py` | Injeta stopwords PT em memória e re-roda `fase2_prova_TCC.py` inteiro |
| `diag_2b.py` | Recompute in-memory de `resolve_unit_block_tags` + fingerprint (usado com PYTHONHASHSEED) |
| `diag_2b2.py` | Distribuição de scores do scorer bruto por bloco (detecção de empates) |
| `diag_2b3.py` | Traça qual ramo de `resolve_unit_block_tags` decide (instrumenta `select_probable_period_for_entry` e o fallback) |
| `diag_2b4.py` | Teste de idempotência: `recompute(recompute(x)) == recompute(x)` nos 3 repos |
