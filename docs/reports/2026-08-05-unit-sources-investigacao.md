# Dual unit sources + MF's lost unidade-03 — READ-ONLY investigation

Data: 2026-08-05 · branch `feat/motor-atribuicao` · Repo alvo: `Metodos-Formais-Tutor`
Status: **investigação completa / fix NÃO iniciado — próxima campanha** (campanha u3/subject_profile,
ver `docs/reports/pendencias.md`).

**Safety receipt.** `git -C Metodos-Formais-Tutor status --porcelain` → EMPTY before, EMPTY after. No tutor repo
was written. Everything below is `json.load` + pure functions (`_parse_units_from_teaching_plan`,
`build_content_taxonomy`, `assign_units_positional`, `_derive_unit_specs_from_repo`). The persist=True write
trap (`_build_file_map_timeline_context_from_course`, `retag()`) was never called.
Note: the generator repo shows `M src/builder/extraction/content_taxonomy.py` — that is the **other agent**
committing concurrently, not me (line numbers in that file shifted between two of my own greps mid-session:
`build_content_taxonomy` moved L440 → L454). I edited nothing.

---

## TL;DR

The u3 loss is **not** a matcher bug and **not** primarily the repo-derived fallback. It is a
**subject_profile delivery hole**: four call sites construct `RepoBuilder` without `subject_profile`, so
`teaching_plan == ""`, so `content_taxonomy["units"] == []`, so `assign_units_positional` **returns `[]`
without ever scoring** (it hard-refuses `m < 2`), so the flow drops to the legacy scorer fed by the
COURSE_MAP-derived 2-unit index — which the same run then re-writes to disk, closing a self-perpetuating
loop. Fed the real 3-unit specs, the matcher puts bloco-16 in **unidade-03 with argmax 4 vs 3 vs 2**.

---

## §Q1 — Map of the two unit sources

### The two producers

| | `unit_index` | `content_taxonomy["units"]` |
|---|---|---|
| Producer | `build_file_map_unit_index_from_course` — `src/builder/routing/file_map.py:1609` | `build_file_map_content_taxonomy_from_course` — `src/builder/routing/file_map.py:1483` → `_build_content_taxonomy` — `src/builder/engine.py:314` → `build_content_taxonomy` — `src/builder/extraction/content_taxonomy.py:454` |
| Primary input | `subject_profile.teaching_plan` (live string from `SubjectStore`, **not** a file read) — `file_map.py:1626` | same `subject_profile.teaching_plan` — `file_map.py:1499` |
| Secondary inputs | GLOSSARY terms → `extra_signals` (`file_map.py:1637-1669`) | synthesized `course_map_md` (rebuilt in memory from the parsed units, `file_map.py:1506-1518`), GLOSSARY text, strong headings, semantic profile |
| Test escape hatch | `course_meta["_unit_index_for_tests"]` (`file_map.py:1622`) | `course_meta["_content_taxonomy"]` / `_content_taxonomy_for_tests` (`file_map.py:1495`) |
| **Behaviour when `teaching_plan == ""`** | **falls back to `_derive_unit_specs_from_repo`** (`file_map.py:1628`) — reads the GENERATED repo's `course/COURSE_MAP.md` + `course/.timeline_index.json` | **returns `{"version":1,"course_slug":"","units":[]}`** and stops (`file_map.py:1500-1501`) |
| Shape | `[{slug, title, topics, extra_signals, …}]` after `build_file_map_unit_index` | `{version, course_slug, units:[{slug, title, topics:[{label, aliases, …}]}]}` |
| Persisted? | no (in-memory only) | yes → `course/.content_taxonomy.json` (`content_taxonomy.py:542`) |

**Asymmetry is the whole bug.** Same input, opposite failure modes: one silently substitutes a
repo-derived surrogate, the other silently yields nothing. Neither logs.

Extra irony: `build_content_taxonomy` itself already has a COURSE_MAP fallback —
`content_taxonomy.py:465-467`, `if not units and course_map_md: units = parse_units_from_teaching_plan(course_map_md)`
— but the wrapper at `file_map.py:1500` short-circuits *before* it can ever fire.

### Consumers

| Consumer | Reads | Site |
|---|---|---|
| `_build_timeline_index` — **positional matcher feed** | `content_taxonomy["units"]` | `src/builder/timeline/index.py:2198` → `assign_units_positional(class_candidates, units_ordered)` at `:2200` |
| `_build_timeline_index` — **legacy fallback scorer** | `unit_index` | `index.py:2209` `_assign_timeline_block_to_unit(b, unit_index)`; `:2211` `_vote_unit_from_topic_candidates(b, unit_index)` |
| `_build_timeline_index` — topic index | `content_taxonomy` | `index.py:2139` `_iter_content_taxonomy_topics`; `:2174` `_assign_timeline_block_to_topic` |
| `_build_file_map_timeline_context_from_course` | **builds BOTH**, passes both down | `index.py:1362` (unit_index), `:1363` (taxonomy), `:1380-1382` (both into `_build_timeline_index`) |
| `resolve_unit_block_tags` (manifest file→unit/block tagging) | **builds its own** `unit_index` + reads taxonomy | `content_taxonomy.py:1023` (unit_index), `:1028-1036` (taxonomy, w/ disk fallback `load_internal_content_taxonomy`) |
| `_card_scoped_block` / `lookup_card_blocks` | `unit_index` | `content_taxonomy.py:893, 909, 1219` |
| `_auto_map_entry_unit` / subtopic scorers | `unit_index` | `content_taxonomy.py:1109`, `file_map.py:486-494` |
| `build_course_unit_topic_index` (student state) | `content_taxonomy` | `src/builder/artifacts/student_state.py:148` |
| `detect_block_conflicts` | `content_taxonomy` | `src/builder/timeline/conflicts.py:55` |
| UI unit/subunit pickers | `content_taxonomy`-shaped plan units | `src/ui/dialogs.py:4362, 4418, 4450` |
| `course_map_md` → writes `COURSE_MAP.md` | taxonomy/timeline via `runtime_course_meta` | `src/builder/artifacts/navigation.py:823`; write at `ops/pedagogical_regeneration.py:402` |

Note `resolve_unit_block_tags` has a **third** derivation moment: it calls
`build_file_map_unit_index_from_course` again itself (`content_taxonomy.py:1023`), so a single
`regenerate_pedagogical_files` derives units at least twice, independently.

### Where the two can disagree (code paths)

1. **`teaching_plan` empty** → taxonomy `[]` **and** unit_index = repo-derived. Maximum divergence.
   `file_map.py:1500-1501` vs `file_map.py:1628`. ← *this is the MF bug*
2. **`_content_taxonomy` injected but `_unit_index_for_tests` not** (or vice-versa) — the two escape
   hatches at `file_map.py:1495` and `:1622` are independent, so tests can pin one and let the other derive.
3. **`retag` path** — `resolve_unit_block_tags` falls back to `load_internal_content_taxonomy` (disk,
   possibly stale) for the taxonomy while re-deriving `unit_index` live. Documented as "Dívida #5" at
   `content_taxonomy.py:1032-1036`.
4. **Glossary divergence** — unit_index enriches with glossary terms (`file_map.py:1641-1669`), the
   taxonomy consumes glossary through a different path (`_glossary_aliases_for_topic`). The two can end up
   with different alias sets for the same unit even on the happy path.
5. **Titles** — repo-derived titles are `slug.replace("-", " ").title()` (`file_map.py:1592`), i.e.
   accent-stripped and Title-Cased, so they never string-match plan titles.

### BUILD vs REPROCESS

Both funnel through the *same* `_regenerate_pedagogical_files` (`engine.py:2116` →
`ops/pedagogical_regeneration.py`). The difference is **not** the code path — it's whether
`builder.subject_profile` is populated:

| Entry point | passes `subject_profile`? | Site |
|---|---|---|
| Full/incremental build (UI) | YES | `src/ui/app.py:2025-2035`, `:2155`, `:2306`, `:2445` |
| "Reprocessar Repositorio" (UI) | YES | `src/ui/app.py:2207-2215` (`active_subj`) |
| Maintenance sweep (UI) | YES | `src/ui/app.py:910-917` |
| `scripts/retag_manifest.py` | YES (`_resolve_subject_profile` by `repo_root`) | `scripts/retag_manifest.py:30-41`, used at `:83` |
| **`scripts/reprocess_assignments.py`** | **NO** | `scripts/reprocess_assignments.py:81` |
| **UI "remover processamento" (`unprocess`)** | **NO** | `src/ui/app.py:2391` `RepoBuilder(repo_dir, meta, [], {})` → regenerates at `ops/lifecycle_ops.py:248` |
| **Curator Studio "reprovar arquivo" (`reject`)** | **NO** | `src/ui/curator_studio.py:1293-1297` and `:1303` → regenerates at `ops/lifecycle_ops.py:367` |

`retag_manifest.py` already solved this correctly. `reprocess_assignments.py` did not — and it is the one
the August rollout docs tell you to run.

---

## §Q2 — Root cause of MF's lost unidade-03

### The chain (FACT)

```
scripts/reprocess_assignments.py:81   RepoBuilder(root_dir, course_meta, entries=[], options)   # no subject_profile
  → engine.py:1726                    subject_profile: Optional[SubjectProfile] = None
  → ops/pedagogical_regeneration.py:319-323   build_file_map_content_taxonomy_from_course(meta, None, entries)
  → file_map.py:1499-1501             teaching_plan = "" → return {"version":1,"course_slug":"","units":[]}
  → ops/pedagogical_regeneration.py:325      WRITES course/.content_taxonomy.json  ← poison persisted
  → index.py:2198                     units_ordered = []            (m = 0)
  → unit_matcher.py:66-67             if m < 2: return []           ← MATCHER NEVER SCORES ANYTHING
  → index.py:2207-2215                ELSE branch: legacy _assign_timeline_block_to_unit(b, unit_index)
  → file_map.py:1628                  unit_index = _derive_unit_specs_from_repo(course_meta)
  → file_map.py:1574-1587             reads course/COURSE_MAP.md → only 2 "### " headings exist
  → file_map.py:1602-1604             extra_signals for u2 = topic_text of blocks ALREADY tagged u2
                                       (bloco-16's own words become u2's evidence) ← self-confirming
  → bloco-16 → unidade-02, conf 1.0
  → ops/pedagogical_regeneration.py:402  RE-WRITES COURSE_MAP.md with 2 units → loop closed, next run repeats
```

### On-disk proof that this ran (FACT)

`Metodos-Formais-Tutor/course/.content_taxonomy.json` (58 bytes, mtime **Aug 4 17:58**, same as every other
regenerated artifact):

```json
{ "version": 1, "course_slug": "", "units": [] }
```

That file can *only* be produced by the `teaching_plan == ""` early return at `file_map.py:1500-1501`.
`.assessment_context.json` is empty for the same reason. Corroborating:

- `COURSE_MAP.md:9,17` — `### Unidade 01 Metodos Formais` / `### Unidade 02 Verificacao De Programas`:
  accent-stripped, Title-Cased, "De" capitalized → exactly `slug.replace("-"," ").title()` (`file_map.py:1592`).
  The plan's real titles are `Unidade 01 — Métodos Formais` etc. **The COURSE_MAP is a render of the
  timeline index, not of the plan.**
- `COURSE_MAP.md:23` lists `Verificacao modelos logica temporal ferramenta` *under Unidade 02*.
- `.timeline_curation.json` = `{"version":1,"blocks":{}}` → **no manual override**. RULES OUT curation
  (`index.py:101-104`, which is the only place `unit_confidence = 1.0` is set by hand).
- bloco-16: `primary_topic_slug=""`, `topic_candidates=[]`, `topic_source="topic_text_fallback"` — the
  signature of an empty taxonomy (nothing to match topics against).
- bloco-03 carries `conf = 0.51` — the soft-continuation inheritance constant at `index.py:2225`, reachable
  only when a block came out of the assignment step with an **empty** `unit_slug`. The positional matcher
  never leaves a block empty. Independent proof the ELSE branch ran.
- June backups `course/.timeline_index.json.bak` (Jun 2) and `.prebuild.bak` (Jun 7) both contain
  `bloco-15 | unidade-03-verificacao-de-modelos | 1.0 | "verificacao modelos logica temporal ferramenta"`
  — same block, renumbered to bloco-16 since. Confirms regression, not a never-worked feature.

### The matcher experiment (FACT — script: `exp_matcher.py`, same scratchpad)

Real `assign_units_positional`, real MF blocks from `.timeline_index.json`, real taxonomy built from the
real `plano.md` via the real `_build_content_taxonomy`:

**Step 1 — parser on the real plano.md:** 3 units (01 Métodos Formais/10, 02 Verificação de Programas/6,
03 Verificação de Modelos/7). **Step 2 — real taxonomy:** 3 units, slugs
`unidade-01-metodos-formais` / `unidade-02-verificacao-de-programas` / `unidade-03-verificacao-de-modelos`.

**Step 5 — result with the real 3 units (17 class candidates of 21 blocks):**

```
bloco-16  -> unidade-03-verificacao-de-modelos   conf=0.6   *** CHANGED (was unidade-02-verificacao-de-programas)
bloco-17  -> unidade-03-verificacao-de-modelos   conf=0.4   *** CHANGED (was <empty>)
bloco-20  -> unidade-03-verificacao-de-modelos   conf=0.4   *** CHANGED (was <empty>)
bloco-07  -> unidade-01-metodos-formais          conf=0.4   *** CHANGED (was <empty>)
bloco-08  -> unidade-01-metodos-formais          conf=0.4   *** CHANGED (was <empty>)
bloco-14  -> unidade-02-verificacao-de-programas conf=0.4   *** CHANGED (was <empty>)
total changed: 6/17   (blocos 01-06, 10-13, 15 unchanged)
```

**Step 6 — affinity dump for bloco-16** (`|block_tokens ∩ unit_tokens|`):

```
topic_text : 'verificacao modelos logica temporal ferramenta'
sessions   : ['verificacao de modelos logica temporal aula' x2, 'exercicios aula' x2,
              'verificacao de modelos ferramenta aula']
block tokens (6): exercicios, ferramenta, logica, modelos, temporal, verificacao

vs unidade-01-metodos-formais            score=3   overlap=[logica, modelos, verificacao]
vs unidade-02-verificacao-de-programas   score=2   overlap=[logica, verificacao]
vs unidade-03-verificacao-de-modelos     score=4   overlap=[logica, modelos, temporal, verificacao]   ← argmax
```

argmax on u3, margin 4−3 = 1.0 ≥ `ANCHOR_MIN_MARGIN` → `CONF_ANCHOR` 0.6. Full matrix (17×3) in the
appendix; u3's column is zero everywhere except bloco-16 (4), 11 (1), 13 (1), 15 (1), 10 (1), 03 (1) —
the DP correctly refuses to advance to u3 before bloco-16.

**Step 7 — same blocks, POISONED 2-unit specs** (`_derive_unit_specs_from_repo` output, slugified):

```
bloco-16  -> unidade-02-verificacao-de-programas  conf=0.6     ← production bug reproduced exactly
```

### Verdicts

- **MATCHER: RULED OUT (FACT).** Given correct specs it produces the correct answer with a clear margin.
  Candidate (ii) MATCHER COLLAPSE is dead.
- **SPEC DELIVERY: GUILTY (FACT).** The specs never reached the matcher — the matcher was never invoked
  (`m < 2` guard, `unit_matcher.py:66-67`). `content_taxonomy["units"]` was `[]`, proven on disk.
- **POISONED FALLBACK: REAL BUT SECONDARY (FACT).** `_derive_unit_specs_from_repo` is genuinely
  self-perpetuating — it harvests `extra_signals` from blocks already carrying the wrong slug
  (`file_map.py:1602-1604`) and the same run re-writes the 2-unit COURSE_MAP it just read from
  (`pedagogical_regeneration.py:402`). It is what *locks in* the loss across runs and what made "reprocess
  again" never fix it. But it is downstream: with `subject_profile` present it is never reached at all.
  Fixing only the fallback would not have restored u3 (the taxonomy would still be `[]` and the matcher
  still skipped).
- **The fix is available today (FACT).** The live `SubjectStore`
  (`%APPDATA%/GPTTutorGenerator/subjects.json`) holds MF's `teaching_plan` at 5191 chars, and feeding it to
  `_parse_units_from_teaching_plan` yields the 3 units. All five subjects have non-empty teaching plans
  (MF 5191, IA 3569, TCC 5801, SO 10944, ES2 4693) — so every repo reprocessed headlessly since the script
  was written has been running with an empty taxonomy.

### Candidate (iii): what else the evidence forces

- **`plano.md` is never read by any flow.** `Metodos-Formais-Tutor/content/curated/plano.md` is a curated
  *artifact*; the live plan text lives only in `SubjectStore`. So "is the plano.md even read during
  reprocess?" — no, and it isn't read during build either. The `teaching_plan` string is the only source.
- **Two more silent leaks in the GUI**, not just the script: `unprocess` (`app.py:2391`) and Curator Studio
  `reject` (`curator_studio.py:1293`, `:1303`) both construct `RepoBuilder` without `subject_profile` and
  both call `_regenerate_pedagogical_files` (`lifecycle_ops.py:248`, `:367`). Removing or rejecting a single
  file from the GUI wipes `.content_taxonomy.json` and re-poisons COURSE_MAP for the whole course. This is
  almost certainly how repos got poisoned *between* rollout runs. STATUS: FACT for the code path;
  HYPOTHESIS for whether it specifically caused MF's Aug 4 state (the Aug 4 17:58 timestamps are equally
  consistent with a rollout `reprocess_assignments.py` run).
- **The August rollout docs already half-knew.** `docs/reports/2026-08-04-handoff-rollout-trilha1.md:83`
  ("`reprocess_assignments.py` NÃO lê subjects.json") and
  `docs/reports/2026-08-05-planob-investigacao.md:324` (task T18) flag the same missing wiring — but frame
  it purely as a **feature-flags** durability problem. Nobody connected it to unit derivation. T18's scope
  is too narrow: merging `feature_flags` alone would leave `subject_profile=None` and the u3 loss intact.
- **No warning anywhere.** Neither `file_map.py:1500` nor `:1628` logs. A course silently losing a third of
  its structure produced zero output. The rollout reported "bloco X/Y coverage improved" while the unit
  layer was collapsing underneath it.

---

## §Recommendation

### The u3 fix (minimal, one place)

`scripts/reprocess_assignments.py:81` — resolve the profile the way `retag_manifest.py` already does and
pass it in. `scripts/retag_manifest.py:30-41` has a working `_resolve_subject_profile(repo_root, subject_name)`
that matches by `repo_root`; import it rather than writing a second copy, and hand the result to
`RepoBuilder(..., subject_profile=sp)`. One import + one kwarg. This restores the teaching plan, so the
taxonomy comes back with 3 units, so `assign_units_positional` actually runs, so bloco-16 lands in
unidade-03 (proven above) — and `_derive_unit_specs_from_repo` is never reached, so the loop cannot re-arm.
It also subsumes T18: with a real `SubjectProfile` in hand, merging its `feature_flags` into `options` is
the same two lines. Then re-run reprocess on MF once to rebuild `.content_taxonomy.json` and COURSE_MAP
from the plan. **Do the same for `app.py:2391` and `curator_studio.py:1293/:1303`** — those already have a
resolved profile in scope (`self._resolve_subject_profile(repo_dir)` / the panel's subject) and are one
kwarg each; leaving them means the next "reprovar arquivo" click re-poisons the repo.

### Guardrail (cheap, catches the class not the instance)

`src/builder/routing/file_map.py:1500` — before returning the empty taxonomy, `logger.warning` that the
course is being regenerated with no teaching plan. Same at `:1628` for the repo-derived fallback. Two lines.
A run that silently discards the entire unit structure must not be indistinguishable from a healthy one.
(Optional, stronger: since `build_content_taxonomy` already accepts a COURSE_MAP fallback at
`content_taxonomy.py:465-467`, `file_map.py:1500` could pass the repo's COURSE_MAP text instead of
returning `[]` — but that would inherit the same poisoned 2-unit map, so it degrades gracefully rather
than correctly. The warning is the honest fix; the profile wiring is the real one.)

### Should the two sources merge?

**Merge — but not now, and not by deleting either function.** The right shape is one derivation:
`content_taxonomy` becomes the single unit truth, and `unit_index` becomes a *projection* of it
(`build_file_map_unit_index(taxonomy["units"])` plus the glossary `extra_signals` enrichment) instead of a
parallel parse of the same `teaching_plan`. `_derive_unit_specs_from_repo` then survives only as an
explicit, logged, opt-in disaster-recovery path — never as an implicit default.

Migration risk is real and argues for sequencing:
- `unit_index` entries carry `extra_signals` that taxonomy units don't; the glossary enrichment at
  `file_map.py:1641-1669` would have to be re-hung on the projection or the file→unit scorers
  (`file_map.py:486-494`, `content_taxonomy.py:1109`) get quietly weaker.
- Titles differ by construction today (accented plan titles vs Title-Cased slug titles). Unifying them
  changes `_normalize_unit_slug` outputs for any repo currently on the fallback → **slug churn → every
  `unidade-*` auto_tag and `block_identity` reference in the poisoned repos re-keys at once.**
- `resolve_unit_block_tags` derives its own `unit_index` (`content_taxonomy.py:1023`) and has its own
  stale-disk taxonomy fallback ("Dívida #5", `:1032-1036`). Merging without also collapsing that third
  derivation just moves the divergence.
- Three tests pin the current fallback contract directly (`tests/test_unit_fallback.py:12, 64, 91, 111, 117`).

So: **ship the profile wiring + the warnings first** (small, reversible, fixes production today), let the
repos re-derive cleanly from their real plans, *then* do the merge against repos that are already correct.
Merging while MF/IA/TCC/SO/ES2 still hold fallback-derived slugs would migrate the poison into the new
single source.

---

## §Evidence appendix

### A. Safety receipts

```
$ git -C C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor status --porcelain   # BEFORE
(empty)
$ git -C C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor status --porcelain   # AFTER
(empty)
```

### B. MF on-disk state

```
$ cat course/.content_taxonomy.json          # 58 bytes, mtime Aug 4 17:58
{ "version": 1, "course_slug": "", "units": [] }

$ cat course/.timeline_curation.json         # 37 bytes
{ "version": 1, "blocks": {} }

$ cat course/.assessment_context.json
{ "version": 1, "assessments": [], "conflicts": [] }
```

`course/COURSE_MAP.md` (837 bytes, Aug 4 17:58) — 2 unit headings only:

```
 9: ### Unidade 01 Metodos Formais
17: ### Unidade 02 Verificacao De Programas
23: - [ ] Verificacao modelos logica temporal ferramenta      ← bloco-16 content, filed under u2
```

`content/curated/plano.md` — 3 units (`Nº. DA UNIDADE: 01` @46, `02` @64, `03` @75).

### C. bloco-16 as persisted (`course/.timeline_index.json`)

```
id                     = 'bloco-16'
period_start/end       = '2026-06-15' / '2026-06-29'
unit_slug              = 'unidade-02-verificacao-de-programas'
unit_confidence        = 1.0
auto_unit_slug         = 'unidade-02-verificacao-de-programas'
primary_topic_slug     = ''            topic_candidates = []
primary_topic_label    = 'Verificacao modelos logica temporal ferramenta'
topic_source           = 'topic_text_fallback'
topic_text             = 'verificacao modelos logica temporal ferramenta'
topics                 = ['verificacao modelos logica temporal', 'verificacao modelos ferramenta']
sessions               = 5
block_uuid             = 'a6ac04f2-7611-4bef-b74a-54390cef4084'
```

`.timeline_index.json` has no top-level `units` key (`d["units"] is None`) — units are not persisted there,
only per-block slugs. That is why `_derive_unit_specs_from_repo` has to scrape `COURSE_MAP.md` headings.

### D. June backups (regression proof)

```
course/.timeline_index.json.bak           (Jun 2 22:23)
  bloco-15  unidade-03-verificacao-de-modelos  1.0  'verificacao modelos logica temporal ferramenta'
course/.timeline_index.json.prebuild.bak  (Jun 7 01:12)
  bloco-15  unidade-03-verificacao-de-modelos  1.0  'verificacao modelos logica temporal ferramenta'
```

### E. Full affinity matrix, real 3 units (Step 6)

```
  block        u01-metodos-formais   u02-verificacao-progr   u03-verificacao-model
  bloco-01                       0                       0                       0
  bloco-02                       2                       0                       0
  bloco-03                       1                       1                       1
  bloco-04                       3                       0                       0
  bloco-05                       0                       0                       0
  bloco-06                       1                       1                       0
  bloco-07                       0                       0                       0
  bloco-08                       0                       0                       0
  bloco-10                       1                       2                       1
  bloco-11                       2                       6                       1
  bloco-12                       0                       0                       0
  bloco-13                       3                       2                       1
  bloco-14                       0                       0                       0
  bloco-15                       2                       2                       1
  bloco-16                       3                       2                       4    ← argmax u3
  bloco-17                       0                       0                       0
  bloco-20                       0                       0                       0
```

(bloco-09/18/19/21 excluded: `source_kind='assessment'` → not class candidates, `index.py:2199`.)

### F. Repo-derived (poisoned) specs, Step 3

```
title='Unidade 01 Metodos Formais'          topics=0  extra_signals=24
title='Unidade 02 Verificacao De Programas' topics=0  extra_signals=39
```

`topics=0` always (hardcoded `[]` at `file_map.py:1605`) — so the fallback index has **no topic labels or
aliases at all**, only bag-of-words scraped from blocks already assigned. Under `_unit_tokens`
(`unit_matcher.py:43-49`, which reads only `title` + `topics[].label/aliases`) these specs contribute
*nothing but the title tokens* to the positional matcher — which is why Step 7's 2-unit run is so flat.

### G. Live SubjectStore (`%APPDATA%/GPTTutorGenerator/subjects.json`)

```
Metodos-Formais                            teaching_plan_len=5191   → parses to 3 units
Inteligencia Artificial                    teaching_plan_len=3569
Teoria da Computabilidade e Complexidade   teaching_plan_len=5801
Sistemas Operacionais                      teaching_plan_len=10944
Engenharia de Software II                  teaching_plan_len=4693
```

### H. Key file:line index

| What | Where |
|---|---|
| taxonomy empty-return | `src/builder/routing/file_map.py:1500-1501` |
| unit_index repo fallback | `src/builder/routing/file_map.py:1628` |
| fallback reads COURSE_MAP | `src/builder/routing/file_map.py:1574-1587` |
| fallback Title-Cases slug | `src/builder/routing/file_map.py:1592` |
| fallback self-feeds extra_signals | `src/builder/routing/file_map.py:1602-1605` |
| taxonomy's unused COURSE_MAP fallback | `src/builder/extraction/content_taxonomy.py:465-467` |
| matcher fed from taxonomy | `src/builder/timeline/index.py:2198-2200` |
| matcher `m<2` hard refusal | `src/builder/timeline/unit_matcher.py:66-67` |
| legacy ELSE branch | `src/builder/timeline/index.py:2207-2215` |
| soft-continuation 0.51 | `src/builder/timeline/index.py:2225` |
| curation-only conf=1.0 | `src/builder/timeline/index.py:101-104` |
| taxonomy written to disk | `src/builder/ops/pedagogical_regeneration.py:325` |
| COURSE_MAP rewritten | `src/builder/ops/pedagogical_regeneration.py:402` |
| **missing subject_profile (script)** | `scripts/reprocess_assignments.py:81` |
| **missing subject_profile (unprocess)** | `src/ui/app.py:2391` |
| **missing subject_profile (reject)** | `src/ui/curator_studio.py:1293, 1303` |
| correct precedent | `scripts/retag_manifest.py:30-41, 83` |
| RepoBuilder default | `src/builder/engine.py:1726` |
