# Plano B — dívidas do motor + fixes 2a/2b Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar o confident-wrong do TCC (2a), o gate furado do funil-base (2b) e as 19 dívidas mecânicas mapeadas, com medição gold a cada mudança de comportamento.

**Architecture:** Spec-companion OBRIGATÓRIA: `docs/reports/2026-08-05-planob-investigacao.md` (evidência file:line, medições empíricas, riscos §Riscos, ordem §Ordem). Cada task abaixo cita a seção correspondente. Motor = `src/builder/routing/motor/`; funil = `src/builder/extraction/content_taxonomy.py`.

**Tech Stack:** Python 3, pytest, probes `scripts/fase{0..5}_*.py`, `audit_gold_freshness.py`.

## Global Constraints

- Régua completa (7 probes + suite) após CADA task que toca motor/funil; números aceitos: fase0 48/58 conten0 cw1 · fase1 9/10 · fase2_SO 45.2%/0/cw0 · fase2_TCC pinos 5/5 + 83.3% (fase2_TCC HOJE dá cw=1 — a Task 1 zera; a partir dela, cw=0 vira gate de novo) · fase3 +3/0API · fase4 det 48/58 cw1, voter 51/58 cw0 calls0 · fase5 target 4/8 cw0 · pytest 1823/4/0 (+N de testes novos por task).
- FAIL = resultado honesto; PROIBIDO re-tuning (MARGIN_TAU, BAND_*, DATE_DF_MAX intocados). Pisos em fração exata.
- Mudança de COMPORTAMENTO (Tasks 1, 4, 5) = medição gold pré/pós com delta row-a-row registrado em pendencias.md. Mudança de atribuição só aceita se: cw não sobe em NENHUM curso E acurácia não cai.
- TDD por task. Lógica nova SÓ em motor/scripts/extraction — `engine.py` intocado (guard AST).
- NUNCA commitar `.claude/settings*.json`/`CLAUDE.md`. Commits com `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Repos-tutor READ-ONLY neste plano (nenhum reprocess/flip — MF e SO ficam ON como estão; TCC/ES2 OFF).
- Probes que montam contexto do funil ESCREVEM `last_seen` em `.block_identity.json` dos repos-tutor (achado §extra) — ao final de qualquer task que rode probes, `git -C <repo> checkout -- course/.block_identity.json` nos repos afetados se só `last_seen` mudou.
- Após código: `graphify update .`.

---

### Task 1: T12 — stopwords PT no motor (fecha o caso 2a)

Spec-companion §2a. Causa: token `nao` (df_global=1) satisfaz `bool(discriminante)` em `disambiguator.py:184` → band alta indevida. Fix VALIDADO empiricamente: lista conservadora de 11 palavras-função → fase2_TCC cw 1→0, acc 84.2% intacta. NÃO estender a lista (versão larga custa 2 casos, 84.2%→78.9%).

**Files:**
- Modify: `src/builder/routing/motor/disambiguator.py:22-26`
- Test: `tests/test_motor_stopwords_pt.py` (novo)

**Interfaces:**
- Produces: `_GENERIC_STEMS` ampliado — consumido por `disambiguator._toks:36` e `window_provider.py:14,101` (cobre também o gate de janela-1 `disambiguator.py:140`, mesmo furo — §Riscos item 5: UM patch, não dois).

- [ ] **Step 1: teste falhando**

```python
# tests/test_motor_stopwords_pt.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.disambiguator import _toks


def test_palavras_funcao_pt_nao_sao_tokens():
    # 'nao' era o unico discriminante do cw aula-01 (investigacao 2026-08-05 §2a)
    toks = _toks("conjuntos enumeraveis e nao enumeraveis")
    assert "nao" not in toks
    assert "conjuntos" in toks and "enumeraveis" in toks


def test_lista_conservadora_completa():
    for w in ("nao", "sim", "com", "sem", "por", "dos", "das", "nos", "nas", "uma", "que"):
        assert w not in _toks(f"conteudo {w} conteudo"), w


def test_tokens_de_dominio_preservados():
    toks = _toks("verificacao de modelos logica temporal")
    assert {"verificacao", "modelos", "logica", "temporal"} <= toks
```

- [ ] **Step 2:** `python -m pytest tests/test_motor_stopwords_pt.py -v` → FAIL (`nao` presente).
- [ ] **Step 3: fix**

```python
# Espelha marco0._GEN: stems (prefixo 8) que NÃO discriminam bloco.
# Palavras-função PT: medição 2026-08-05 (docs/reports/2026-08-05-planob-investigacao.md
# §2a) — lista conservadora zera confident-wrong com acurácia intacta (84.2%);
# NÃO estender com demonstrativos/comparativos: a versão larga custou 2 casos (78.9%).
_GENERIC_STEMS = frozenset({
    "introduc", "continua", "exercici", "revisao", "conteudo", "material",
    "aplicac", "apresent", "sobre", "parte", "exemplo", "usando", "aula",
    "para", "resposta", "solucao", "lista",
    "nao", "sim", "com", "sem", "por", "dos", "das", "nos", "nas", "uma", "que",
})
```

- [ ] **Step 4:** testes verdes + `python scripts/fase2_prova_TCC.py` → **PASS, cw=0, acc 84.2%, pinos 5/5** (números da medição empírica — desvio = PARAR, reportar).
- [ ] **Step 5: régua completa** (7 probes + `python -m pytest -q`) — números aceitos; fase2_TCC agora PASS. Restaurar `last_seen` dos repos-tutor tocados pelos probes.
- [ ] **Step 6: registro + commit** — entrada pendencias `[DERIVADO] T12 stopwords PT: causa-raiz do cw TCC fechada (cw 1→0, acc intacta)`; `git add` dos 3 arquivos; msg `fix(motor): stopwords PT em _GENERIC_STEMS — zera confident-wrong aula-01/TCC (T12, causa-raiz 2a)`.

---

### Task 2: Batch higiene sem mudança de comportamento (T9a·T2b·T8·T9·T10·T7a·T16·T13·T14·T11)

Spec-companion §Mapa itens 2,5,7,8,9,10,11,13,14,16. Todos sem efeito observável na régua (gate: flag-OFF byte-idêntico). Um commit por área: (a) motor/apply+context, (b) llm_vote, (c) window_provider/due_window/moodle_labels, (d) probe fase3.

**Files:**
- Modify: `src/builder/routing/motor/apply.py:50` · `src/builder/routing/motor/context.py:18-21` · `src/builder/routing/motor/llm_vote.py` (:49-62 memoize, :77-82 mkdir, :131 fold, :173-183 casefold) · `src/builder/routing/motor/window_provider.py:120-121` (hoist `_stems` cacheado em ctx, padrão `_global_df_cache` de `disambiguator.py:119-128`) · `src/builder/routing/motor/due_window.py` (gate due-vazio na saída de `_match_due`) · `src/builder/sources/moodle_labels.py:297-298` (exigir `fileurl`) · `scripts/fase3_prova_LLM_MF.py:104` (remover slice `[:900]` do dry-run)
- Test: `tests/test_motor_higiene_batch.py` (novo — 1 teste por item com efeito testável: `apply.py` window sem `"None"`; fold/casefold de `llm_vote`; `fileurl` ausente descartado; due vazio não casa; memoize md5 chamado 1× via monkeypatch contador)

Edits exatos (transcrever):
- `apply.py:50`: `[str(r) for r in (decision.window or [])]` → `[str(r) for r in (decision.window or []) if r]`
- `context.py`: adicionar `logger = logging.getLogger(__name__)` no topo (+`import logging`) e no `except Exception as exc: logger.debug("artefato %s ilegivel: %s", rel, exc); return {}`
- `llm_vote.py:77-82` (`save_material_curation`): `path.parent.mkdir(parents=True, exist_ok=True)` antes do write
- `llm_vote.py:131`: `sec = str(...).strip()` → usar `norm_ascii_lower(...)` (mesmo helper de `due_window._card_entry:40`)
- `llm_vote.py:173-183` (`match_window_ref`): comparar com `.strip().casefold()` nos dois lados
- `llm_vote.py` memoize: dict `self._key_cache: dict = {}` em `__init__`; `content_key` consulta por `entry["id"]` antes de hashear
- `window_provider.py:120-121`: cachear `_stems(sig)` por bloco em `ctx` (invariante por índice)
- `due_window.py`: no retorno de `_match_due`, `if not due: return None` (gate único; caminho stem pode devolver due vazio — spec-companion item 14)
- `moodle_labels.py:297-298`: `f.get("type") == "file"` → `f.get("type") == "file" and f.get("fileurl")`

- [ ] **Step 1:** testes novos falhando (onde aplicável) → **Step 2:** edits → **Step 3:** testes verdes + suite completa → **Step 4: régua completa byte-idêntica** (nenhum número pode mudar — este batch é higiene; qualquer delta = bug introduzido, reverter o item culpado) + restaurar `last_seen`.
- [ ] **Step 5:** 4 commits por área (`refactor(motor): ...`, `refactor(voter): ...`, `refactor(providers): ...`, `fix(probe): dry-run fase3 sem truncamento`) + `graphify update .`.

---

### Task 3: T3 — sonda fase3 filtra janela-1 (instrumentação ANTES das medições 2b)

Spec-companion §Mapa item 3. `scripts/fase3_prova_LLM_MF.py:93`: `if d.flag or r["id"] in series:` não exige `len(d.window) > 1` que `anchor_engine.py:57` exige → sonda superestima escopo do voto.

- [ ] **Step 1:** teste/verificação: rodar `python scripts/fase3_prova_LLM_MF.py` ANTES (baseline +3/0API) e registrar as rows contadas.
- [ ] **Step 2:** edit: `if (d.flag and len(d.window) > 1) or r["id"] in series:` (alinhar ao gate real do engine).
- [ ] **Step 3:** re-rodar fase3 → esperado: lift +3 / 0 API MANTIDO (o filtro remove rows que nunca votariam; se o número MUDAR, registrar a diferença honestamente — o número antigo era viés da sonda; decisão de piso novo = registrar em pendencias, NÃO ajustar código pra manter o velho).
- [ ] **Step 4:** suite + commit `fix(probe): fase3 conta so rows elegiveis ao voto (janela>1) — T3`.

---

### Task 4: Fix 2b — funil lê `_p_ambig` + piso de confiança (MUDA ATRIBUIÇÕES — medição gold obrigatória)

Spec-companion §2b. `content_taxonomy.py:1224` aceita palpite `conf=0.0, ambig=True` como atribuição dura; fallback honesto nunca alcançado. Fix de 1 linha + tie-break opcional (§2b "Segunda falha latente").

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py:1224` (+ :1225-1234 tie-break se ramo continuar alcançável)
- Test: `tests/test_funil_gate_ambiguidade.py` (novo)

- [ ] **Step 1: medição PRÉ (obrigatória):** rodar fase0 (MF), fase2_SO, fase2_TCC + gold-check das 7 entries conhecidas (4 TCC: 3dm/cubic/integer/programacao → hoje bloco-16 conf 0.0; 3 MF: logicadehoare/classes-parte1/classes-parte2; SO exercicios-p2). Registrar tabela id→bloco-atual→gold-true.
- [ ] **Step 2: teste falhando** — unit com `select_probable_period_for_entry_fn` fake devolvendo `("1 dia · x", 0.0, True, None)`: gate deve RECUSAR e cair no fallback (`block_method != "scorer_only"`); e com `(label, 0.4, False, None)`: aceitar.
- [ ] **Step 3: fix**

```python
                    if _period and not _p_ambig and p_conf > 0:
```

(comentário de 1 linha: `# le a flag de ambiguidade + piso trivial — palpite conf=0/ambig nunca vira atribuicao dura (investigacao 2026-08-05 §2b)`)

- [ ] **Step 4: medição PÓS** — mesma tabela; aceite: (a) cw não sobe em NENHUM probe; (b) acurácia fase0/fase2_* não cai; (c) as 7 entries movem para blocos ≥ iguais ao gold (esperado: 3dm/cubic → bloco-22 [gold bloco-24 — registrar: erro persiste mas com confiança honesta do fallback]; empates integer/programacao → ver Step 5). Delta row-a-row em pendencias. Se (a) ou (b) falhar: REVERTER + FAIL honesto registrado + PARAR task.
- [ ] **Step 5: tie-break (só se necessário):** se as entries de empate exato (bloco-16 == bloco-26, 20.5456) continuarem decididas por ordem-da-lista no caminho novo, aplicar desempate por score do scorer em `content_taxonomy.py:1225-1234`; senão registrar "ramo inalcançável, tie-break dispensado".
- [ ] **Step 6:** régua completa + suite + restaurar `last_seen` + commit `fix(funil): gate de periodo le _p_ambig + piso de confianca — palpite cego nunca vira atribuicao (2b)` + registro pendencias com as duas tabelas.

---

### Task 5: T17 — filtro D-H `topics` → `kind` (isolado, re-medição)

Spec-companion §Mapa item 17 + §Riscos item 3 (NUNCA no mesmo commit do 2b). `due_window.py:85`: `if not (b.get("topics") or []): continue` → usar `kind` (campo required, semântico — separa conteúdo de admin/prova como em `content_taxonomy.py:966,973`). Mata o pré-requisito "topics populado" do rollout de curso novo.

- [ ] **Step 1:** teste: bloco com `topics=[]` mas `kind="class"` DEVE ancorar; bloco `kind="assessment"` NUNCA ancora (t2→bloco-16 pulando 17/18 preservado).
- [ ] **Step 2:** edit: `if str(b.get("kind") or "") in NON_CONTENT_KINDS: continue` com `NON_CONTENT_KINDS = frozenset({"assessment", "review", "event", "holiday", "suspension", "admin", "office_hours", "overview", "results", "academic_event", "planning", "reserved", "deliverable", "workshop", "suspended", "holiday"})`? NÃO — decisão de conjunto é DESIGN: derivar a lista dos kinds REAIS dos 5 índices (dry-run rebuild lista os kinds) e classificar conteúdo vs não-conteúdo com base no comportamento atual (blocos hoje SEM topics = não-conteúdo esperado); documentar a tabela kind→classe no teste. Gate: fase5 target 4/8 cw0 byte-idêntico (D-H não pode mudar resultado no MF atual).
- [ ] **Step 3:** régua completa (fase5 em foco) + suite + commit `feat(motor): filtro D-H por kind (required) no lugar de topics (opcional) — T17, re-medido`.

---

### Task 6: T4b — lock cross-processo do voter (sozinho)

Spec-companion §Mapa item 4. `llm_vote.py:203` lock in-process; `_persist:220-225` read-merge-write sem exclusão entre processos.

- [ ] **Step 1:** teste: dois "processos" simulados (subprocess real com script mínimo OU teste do sentinela: segundo acquire falha/espera) — travar o comportamento: merge não perde votos.
- [ ] **Step 2:** implementar lock de arquivo com sentinela `O_EXCL` + retry/timeout curto em volta de `_persist`/`prune` (marcar `# ponytail: lock por sentinela O_EXCL; trocar por portalocker se contenção real aparecer`).
- [ ] **Step 3:** suite + régua flag-OFF byte-idêntica + commit `fix(voter): lock cross-processo em _persist/prune (T4b)`.

---

### Task 7: Infra final (T15·T1b·T18·T7b·T19·read_only probe)

Spec-companion §Mapa itens 15, 1, 18, 6, 19 + §extra. Cada item = 1 commit.

- [ ] **T15 imports:** consolidar imports tardios no topo em `content_taxonomy.py:832,834,839,1039,1051,1156,1172,1189` e `concept_resolver.py:326,329` ONDE não há ciclo; os com ciclo declarado (entry_signals/file_map) ficam com comentário `# import local: ciclo com X`. Suite verde.
- [ ] **T1b:** `src/ui/theme.py:121-122` — migração vira tabela `_MODEL_MIGRATIONS = {("ollama", "modelo_velho"): "modelo_novo", ...}` (valores atuais do if inline, transcritos ao ler o arquivo). Teste de migração por tabela.
- [ ] **T18:** `scripts/reprocess_assignments.py` — ler `SubjectStore` (match por `repo_root` resolvido) e mesclar `feature_flags` do perfil vivo nas options (CLI `--flags` continua vencendo; sem perfil → comportamento atual). Testes: com perfil ON injeta; `--flags` sobrepõe; sem subjects.json → igual hoje. MATA a armadilha operacional do handoff (reprocess MF sem `--flags`).
- [ ] **T7b:** teste e2e da ORDEM `refresh_manifest_auto_tags` → `resolve_unit_block_tags` → `attach_block_summary_fields` via `regenerate_pedagogical_files` (fixture mínima; trava a precedência de `content_taxonomy.py:1321-1329`).
- [ ] **T19 (.bak, DESTRUTIVO em repo user — CONFIRMAR COM USER ANTES):** `engine._generated_repo_gitignore_text` ganha `*.bak`; nos repos-tutor `git rm --cached` dos 5 .bak versionados do MF + commit lá. SÓ com sign-off explícito do user na sessão.
- [ ] **read_only probe:** mover o bump de `last_seen` do caminho de leitura (`_build_file_map_timeline_context_from_course`) para o caminho de build explícito OU param `read_only=True` usado pelos probes — decidir pelo menor diff; régua byte-idêntica; fecha o achado §extra.
- [ ] Régua completa final + `graphify update .` + handoff de fechamento do Plano B + push (autorizado padrão da campanha).

---

## Self-Review

- Cobertura: 2a (T1), 2b (T4), 19 mecânicas (T2: 10 itens · T3 · T5 · T6 · T7: 5 itens + read_only) — 19/19 mapeadas. Ordem = §Ordem da investigação.
- Sem placeholder: edits exatos transcritos onde a investigação cravou linha; T17 Step 2 e T1b deixam decisão de VALOR explícita como passo de derivação (ler estado real), não TBD.
- Riscos herdados: §Riscos 1-8 da investigação embutidos nas tasks (2b≠T17 em commits separados; stopwords não estendem; T19 com confirmação; lock isolado).
