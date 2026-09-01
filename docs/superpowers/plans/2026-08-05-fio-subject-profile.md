# Fio subject_profile — unidades do plano de ensino chegam ao reprocess Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Injetar o `subject_profile` (que carrega o plano de ensino) nos 3 call-sites que constroem `RepoBuilder` sem ele, restaurando a camada bloco→unidade (perda da unidade-03 do MF), com verificação nos 5 cursos e cura do repo MF.

**Architecture:** Spec-companion OBRIGATÓRIA: `docs/reports/2026-08-05-unit-sources-investigacao.md` (causa-raiz FATO: `reprocess_assignments.py` monta builder sem profile → `teaching_plan=""` em `engine.py:350` → `content_taxonomy["units"]=[]` → `assign_units_positional` early-return `m<2` → scorer legado com índice 2-unidades; matcher INOCENTADO: com as 3 unidades reais, bloco-16→unidade-03 conf 0.6). Resolução canônica de perfil por repo_root vira método de `SubjectStore` (fonte única); os 2 resolvedores existentes (`retag_manifest._resolve_subject_profile`, `reprocess_assignments._find_subject_profile`) delegam para ele; os 3 sites furados passam a usar.

**Tech Stack:** Python 3, pytest, probes `scripts/fase{0..5}_*.py`.

## Global Constraints

- Mesma disciplina do Plano B: régua completa (7 probes + `python -m pytest -q`) após cada task; números aceitos: fase0 48/58 conten0 cw1 · fase1 9/10 · fase2_SO 45.2%/0/cw0 · fase2_TCC PASS 5/5 83.3% cw0 84.2% · fase3 39 rows +3/0API · fase4 det 48/58 cw1, voter 51/58 cw0 calls0 · fase5 4/8 cw0 · pytest 1858/4/0 (+N testes novos por task). Desvio = PARAR, reportar; PROIBIDO re-tuning.
- O FIO NÃO PODE mudar atribuição de AULA (material→bloco): Tasks 1-2 exigem régua BYTE-IDÊNTICA. Mudança de UNIDADE só se materializa quando um build/reprocess RODA com perfil — em memória na Task 2, real e gated na Task 3.
- Repos-tutor READ-ONLY nas Tasks 1-2 (persist=False / json.load puro; NUNCA `_build_file_map_timeline_context_from_course` sem `persist=False` — write-trap conhecido). Task 3 escreve APENAS no Metodos-Formais-Tutor, APENAS após sign-off do user na sessão, com snapshot prévio.
- last_seen: pós-probes, `git -C <repo> status --porcelain`; `.block_identity.json` só-last_seen → `git -C <repo> checkout -- course/.block_identity.json`; outra coisa → reportar, não tocar.
- NUNCA stage `.claude/settings*.json`/`CLAUDE.md`. Commits com trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. `graphify update .` após código.
- graphify: `graphify query "<pergunta>"` antes de ler fonte desconhecida; file:line pinpointed direto tudo bem (regra vale para subagentes).

---

### Task 1: Fonte única de resolução de perfil + fio nos 3 sites

**Files:**
- Modify: `src/models/core.py` (classe `SubjectStore`, ~:333)
- Modify: `scripts/reprocess_assignments.py:115` (+ `_find_subject_profile` delega)
- Modify: `scripts/retag_manifest.py:31-42` (`_resolve_subject_profile` delega)
- Modify: `src/ui/app.py:2391` (worker do unprocess)
- Modify: `src/ui/curator_studio.py:1293-1298` e `:1303-1308` (reject)
- Test: `tests/test_subject_profile_wiring.py` (novo)

**Interfaces:**
- Produces: `SubjectStore.find_by_repo_root(repo_root) -> Optional[SubjectProfile]` — normalização de path idêntica ao `retag_manifest._resolve_subject_profile` atual (separadores, trailing slash, casefold). Consumida pelas Tasks 2-3 e pelos 5 call-sites.

- [ ] **Step 1: teste falhando (helper)**

```python
# tests/test_subject_profile_wiring.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.core import SubjectStore, SubjectProfile


def _store_with(tmp_path, repo_root: str) -> SubjectStore:
    store = SubjectStore.__new__(SubjectStore)
    sp = SubjectProfile(name="Metodos Formais")
    sp.repo_root = repo_root
    store._subjects = {"Metodos Formais": sp}
    return store


def test_find_by_repo_root_casefold_e_separadores(tmp_path):
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    store = _store_with(tmp_path, str(repo).replace("\\", "/").upper() + "/")
    found = store.find_by_repo_root(repo)
    assert found is not None and found.name == "Metodos Formais"


def test_find_by_repo_root_sem_match_devolve_none(tmp_path):
    repo = tmp_path / "Outro-Tutor"
    repo.mkdir()
    store = _store_with(tmp_path, str(tmp_path / "MF-Tutor"))
    assert store.find_by_repo_root(repo) is None
```

Nota: se `SubjectStore` não tiver atributo interno `_subjects` com esse nome, LER a classe primeiro e ajustar o fake ao shape real (o teste trava comportamento, não representação interna — usar a API pública de escrita se existir).

- [ ] **Step 2:** `python -m pytest tests/test_subject_profile_wiring.py -v` → FAIL (`find_by_repo_root` inexistente).
- [ ] **Step 3: implementar o método** (transcrever a normalização do `retag_manifest._resolve_subject_profile:36-41` — é a mais tolerante das duas existentes):

```python
    def find_by_repo_root(self, repo_root) -> "Optional[SubjectProfile]":
        """Resolve o perfil da materia dono de um repo-tutor gerado (match por repo_root)."""
        target = str(repo_root).replace("\\", "/").rstrip("/").casefold()
        for name in self.names():
            sp = self.get(name)
            rr = str(getattr(sp, "repo_root", "") or "").replace("\\", "/").rstrip("/").casefold()
            if rr and rr == target:
                return sp
        return None
```

- [ ] **Step 4:** testes do helper verdes.
- [ ] **Step 5: teste falhando (fio do reprocess)** — adicionar ao mesmo arquivo:

```python
def test_reprocess_passa_subject_profile_ao_builder(tmp_path, monkeypatch):
    import scripts.reprocess_assignments as ra
    repo = tmp_path / "MF-Tutor"
    repo.mkdir()
    (repo / "manifest.json").write_text(json.dumps({"course": {}, "options": {}, "entries": []}), encoding="utf-8")
    sp = SubjectProfile(name="Metodos Formais")
    sp.repo_root = str(repo)
    store = SubjectStore.__new__(SubjectStore)
    store._subjects = {"Metodos Formais": sp}
    captured = {}

    class FakeBuilder:
        def __init__(self, **kw):
            captured.update(kw)
        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", FakeBuilder)
    ra.reprocess(repo, flags=[], store=store)
    assert captured.get("subject_profile") is sp


def test_reprocess_sem_perfil_builder_recebe_none(tmp_path, monkeypatch):
    import scripts.reprocess_assignments as ra
    repo = tmp_path / "Solto-Tutor"
    repo.mkdir()
    (repo / "manifest.json").write_text(json.dumps({"course": {}, "options": {}, "entries": []}), encoding="utf-8")
    store = SubjectStore.__new__(SubjectStore)
    store._subjects = {}
    captured = {}

    class FakeBuilder:
        def __init__(self, **kw):
            captured.update(kw)
        def incremental_build(self):
            pass

    monkeypatch.setattr(ra, "RepoBuilder", FakeBuilder)
    ra.reprocess(repo, flags=[], store=store)
    assert captured.get("subject_profile") is None
```

- [ ] **Step 6:** rodar → FAIL (`subject_profile` não é passado).
- [ ] **Step 7: os 5 edits**

(a) `scripts/reprocess_assignments.py:115`:

```python
    builder = RepoBuilder(root_dir=repo, course_meta=course_meta, entries=[], options=options,
                          subject_profile=profile)
```

(b) `scripts/reprocess_assignments.py` `_find_subject_profile` vira delegação (manter a função — probes/testes citam):

```python
def _find_subject_profile(repo: Path, store):
    return store.find_by_repo_root(repo)
```

(c) `scripts/retag_manifest.py:31-42` `_resolve_subject_profile` delega preservando `--subject`:

```python
def _resolve_subject_profile(repo_root: Path, subject_name: str):
    from src.models.core import SubjectStore
    store = SubjectStore()
    if subject_name:
        return store.get(subject_name)
    return store.find_by_repo_root(repo_root)
```

(d) `src/ui/app.py:2391` (worker do unprocess) — resolver perfil antes do builder; `SubjectStore` já é importado no módulo (verificar import; se ausente, importar no topo):

```python
                profile = SubjectStore().find_by_repo_root(repo_dir)
                builder = RepoBuilder(repo_dir, meta, [], {}, subject_profile=profile)
```

(e) `src/ui/curator_studio.py:1293-1298` e o bloco de compat `:1303-1308` — mesmo padrão nos DOIS construtores:

```python
            profile = SubjectStore().find_by_repo_root(self.repo_dir)
            builder = RepoBuilder(
                root_dir=self.repo_dir,
                course_meta=self._repo_course_meta(),
                entries=[],
                options={},
                subject_profile=profile,
            )
```

(import de `SubjectStore` no topo do módulo se ausente). Sites GUI (d)/(e) não têm teste headless viável (Tkinter) — cobertura = testes do helper + do reprocess + review de diff; declarar isso no report.

- [ ] **Step 8:** testes novos verdes + suite completa (`python -m pytest -q`, esperar 1858/4/0 + novos).
- [ ] **Step 9: régua completa BYTE-IDÊNTICA** (o fio sem reprocess não muda nada) + restaurar last_seen.
- [ ] **Step 10:** commit único: `fix(wiring): subject_profile chega ao RepoBuilder nos 3 sites furados via SubjectStore.find_by_repo_root (fio u3)` + trailer. `graphify update .`.

---

### Task 2: Verificação — 5 cursos, parser vs índice + recompute MF em memória

**Files:**
- Create (scratchpad, NÃO no repo): `<scratchpad>/verify_units_5cursos.py` e `<scratchpad>/recompute_mf_units.py`
- Test: nenhum novo no repo (task de medição; resultados vão no report e em pendencias.md)
- Modify: `docs/reports/pendencias.md` (tabela de resultado)

**Interfaces:**
- Consumes: `SubjectStore.find_by_repo_root` (Task 1); `_parse_units_from_teaching_plan` (`src/builder/extraction/teaching_plan.py:30`); índices via `json.load` puro.

- [ ] **Step 1: tabela parser-vs-índice dos 5 cursos.** Para cada repo-tutor em `~/Documents/GitHub` (`TCC-Tutor`, `Metodos-Formais-Tutor`, `Sistemas-Operacionais-Tutor`, `Engenharia-Software-2-Tutor`, `Inteligencia-Artificial-Tutor`): unidades do PARSER (fonte: `subjects.json` → `find_by_repo_root(...).teaching_plan`; fallback `content/curated/plano.md` do repo se o perfil não tiver plano) vs unit-slugs distintos nos `blocks[]` de `course/.timeline_index.json` (`json.load` puro; IA sem índice = registrar e seguir). Saída: tabela curso × (unidades-parser, unidades-índice, delta). ES2: repo tem sujeira pré-existente conhecida (45 arquivos) — SÓ LEITURA, nada de checkout/restore lá.
- [ ] **Step 2: recompute MF em memória com o fio consertado.** Reproduzir o caminho REAL do reprocess (mesmas funções, `persist=False`, profile via `find_by_repo_root`) e extrair a atribuição bloco→unidade resultante. Aceite: 3 unidades presentes; bloco-16 → `unidade-03-verificacao-de-modelos` (slug conforme normalização real); blocos 01-06 → unidade-01 e 10-15 → unidade-02 INALTERADOS; atribuição de AULA (computed_block_id) dos 67 entries byte-idêntica ao disco. Desvio = PARAR e reportar (não ajustar).
- [ ] **Step 3:** régua completa byte-idêntica + suite + restaurar last_seen (MF/SO/TCC).
- [ ] **Step 4:** registrar tabela + resultado do recompute em pendencias.md (item `[DERIVADO]` da campanha do fio) e commit `docs(planob-fio): verificacao unidades 5 cursos + recompute MF em memoria (task 2)` + trailer.

---

### Task 3: Cura do MF — reprocess real (GATED: sign-off do user)

**Files:**
- Nenhum arquivo novo no repo do projeto; escrita REAL no `Metodos-Formais-Tutor` (autorizada no gate).
- Modify: `docs/reports/pendencias.md` + handoff curto `docs/reports/2026-08-05-fio-u3-cura-mf.md`

**Interfaces:**
- Consumes: script consertado (Task 1), números esperados (Task 2).

- [ ] **Step 0 (CONTROLLER, não o subagente): sign-off explícito do user na sessão para escrever no MF-Tutor.** Sem sign-off = task não roda.
- [ ] **Step 1: snapshot de segurança no MF-Tutor** — commit `snapshot pre-cura-u3` incluindo os artefatos GITIGNORED relevantes copiados para fora do repo (lição TCC: `course/.timeline_index.json`, sidecars — copiar para o scratchpad com hash registrado; o commit cobre só os tracked).
- [ ] **Step 2: reprocess real**: `python -m scripts.reprocess_assignments <path-do-MF-Tutor>` SEM `--flags` (T18+fio: flags E perfil vêm vivos do subjects.json — este é o teste de fogo da armadilha morta).
- [ ] **Step 3: gates pós-cura** (TODOS obrigatórios):
  - `COURSE_MAP.md` passa a listar `### Unidade 03 Verificacao De Modelos` (3 unidades no total);
  - unit-slugs do índice = 3; bloco-16 → unidade-03; blocos 01-06/10-15 mantêm u1/u2;
  - atribuição de AULA: `computed_block_id` dos 67 entries IDÊNTICO ao pré-cura (diff programático manifest antes/depois — mudanças permitidas SÓ em campos de unidade/auto_tags `unit:`/`subunit:` e derivados);
  - régua completa nos números aceitos (fase0/fase1/fase4 rodam contra MF real — se a cura mudar algum número da régua, PARAR: é sinal de vazamento aula←unidade, reverter pelo snapshot e reportar);
  - suite completa verde.
- [ ] **Step 4: conferência humana** — apresentar ao user a tabela dos 12 blocos de aula × unidade atribuída × tópico, pedir confirmação (minutos). Registrar veredito.
- [ ] **Step 5:** commit no MF-Tutor (`chore: cura u3 — reprocess com perfil vivo (3 unidades restauradas)` + trailer) SÓ com aprovação do Step 4; pendencias.md atualizado (cura concluída; SO/TCC/ES2 conforme tabela da Task 2 — se algum tiver perda análoga, vira item próprio); handoff curto com números.
- [ ] **Step 6:** régua final + `graphify update .`.

### Task 4: Prevenção — a perda de unidades nunca mais passa em silêncio (EXECUTAR ANTES DA TASK 3 — decisão user 2026-08-06)

**Files:**
- Create: `scripts/verify_units.py` (promoção do `verify_units_5cursos.py` do scratchpad da Task 2)
- Create: `tests/fixtures/eval/units_baseline.json` (estado conhecido por curso — inclui as perdas atuais como FATO registrado)
- Modify: ponto de build/reprocess onde o índice é gravado (derivar o local exato do menor diff lendo o fluxo — candidato: onde `content_taxonomy["units"]` alimenta a gravação do índice; NÃO no `engine.py` além de wiring trivial)
- Modify: `src/builder/routing/file_map.py` (`_derive_unit_specs_from_repo:1550` — aviso alto quando usado)
- Test: `tests/test_units_guard.py` (novo)

**Interfaces:**
- Produces: (1) guard "unidade nunca encolhe em silêncio": build/reprocess que computa 0 unidades do plano ENQUANTO o índice existente no repo tem ≥2 unit-slugs → `RuntimeError` com mensagem clara (nome do curso, contagens, dica: perfil ausente?) ANTES de persistir; (2) `scripts/verify_units.py <repos...>` — compara parser-vs-índice por curso e FALHA (exit≠0) em perda NOVA vs `units_baseline.json` (perdas já conhecidas registradas no baseline = WARN, não FAIL; a cura ATUALIZA o baseline); vira 8º item da régua; (3) `_derive_unit_specs_from_repo` loga `logger.warning` ("unidades derivadas do repo gerado, nao do plano de ensino — fallback") quando alcançado.

- [ ] **Step 1: testes falhando** — `tests/test_units_guard.py` com fixtures sintéticas (SEM repos reais): (a) guard dispara: índice existente com 2 unit-slugs + parser devolvendo [] → RuntimeError com nome do curso na mensagem; (b) guard NÃO dispara: repo novo sem índice + parser []; (c) guard NÃO dispara: parser devolve 3 unidades; (d) verify: perda nova vs baseline → exit≠0; perda já no baseline → exit 0 com WARN; (e) fallback loga warning (caplog).
- [ ] **Step 2:** RED confirmado com output.
- [ ] **Step 3:** implementar guard + script + warning (menor diff; local exato do guard derivado e documentado no report com file:line).
- [ ] **Step 4:** GREEN + suite completa.
- [ ] **Step 5:** `python scripts/verify_units.py` nos 5 repos reais → saída esperada HOJE: TCC OK · MF/SO/ES2/IA WARN (perdas conhecidas no baseline, registradas como fato com números da Task 2). Régua 7 probes byte-idêntica (guard não pode disparar em fluxo legítimo) + restaurar last_seen (nunca ES2/IA).
- [ ] **Step 6:** commit `feat(guard): unidades nunca encolhem em silencio + verify_units na regua + fallback barulhento (fio task 4)` + trailer. `graphify update .`.

---

## Self-Review

- Cobertura da spec (investigação §Recommendation): fonte única de resolução (Task 1 helper), 3 sites furados (Task 1 edits a/d/e), delegação dos 2 resolvedores existentes (b/c), verificação 5 cursos (Task 2), cura MF (Task 3). Merge unit_index↔content_taxonomy: FORA deste plano por decisão da investigação (churn de slugs; campanha própria).
- Sem placeholder: edits transcritos; testes com código real; fake de `SubjectStore` com nota de ajuste ao shape real (decisão de leitura, não TBD).
- Tipos consistentes: `find_by_repo_root` devolve `Optional[SubjectProfile]`; call-sites usam kwarg `subject_profile=` (assinatura `engine.py:1726`).
