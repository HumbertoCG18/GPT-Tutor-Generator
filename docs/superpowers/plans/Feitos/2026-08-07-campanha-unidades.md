# Campanha 2/3 — Unidades: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recuperar as unidades perdidas nos índices dos repos-tutor (MF u03 · SO u04 · ES2 u03 · IA u04/u05, este condicionado a ruling) matando a colisão de rótulo na fonte + desempate do DP, com gold de unidade como régua e curas gated por curso.

**Architecture:** Fix na taxonomia (`build_content_taxonomy`: exclusividade de núcleo de título por TOKENS + higiene de heading) → desempate por sinal concentrado no DP (`assign_units_positional`) → sonda canônica = caminho de produção (padrão `rebuild_diff`) → gold 82 blocos rotulado pelo user → curas por curso com snapshot+sha256 e gates. Spec: `docs/superpowers/specs/2026-08-07-campanha-unidades-design.md` (v2, 2 rodadas de revisão com dados reais). Evidência: `docs/reports/2026-08-07-spec-review-unidades.md`.

**Tech Stack:** Python 3.13 stdlib + pytest. Sem dependência nova.

## Global Constraints

- **Zero escrita em repo-tutor fora das curas (Tasks 8-11).** Cura sempre com snapshot tracked+gitignored, eco por arquivo + sha256, rollback testado (protocolo provado 3×; glob silencioso = rede furada).
- **Suite baseline: 1881 passed / 4 skipped / 1 failed** — o 1 failed é `test_caracterizacao_blocos_atual[IA]` (golden stale, item próprio no tracker). 2º fail = regressão SUA. Rodar: `python -m pytest -q`.
- **Não reprocessar NENHUM curso via GUI durante a campanha** até a cura do curso (Tasks 1-3 mudam algoritmo globalmente; repos só podem mudar pelas curas gated — mesma disciplina da campanha 1).
- Fixtures derivadas de DADOS REAIS com proveniência registrada em comentário (regra `context/conventions.md` / MEX).
- Número de sonda que não passe pelo caminho de produção NÃO vale como gate (regra dura, spec §5).
- Réguas vivas da campanha 1 (comandos na Task 8) byte-idênticas, exceto mudança INTENCIONAL de unidade justificada por gold.
- Encoding: scripts novos com `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` (padrão `reprocess_assignments.py:29-31`); nunca assumir slug ASCII (ids reais: `ia-responsável-7c4626`, dotless-i U+0131 no TCC).
- Commits em Conventional Commits, um por task no mínimo.
- IA: NENHUMA mudança no repo IA antes do ruling da Task 11 (violação da premissa monotônica, spec §2).

---

### Task 1: U1(a)+(b) — Exclusividade de núcleo de título na taxonomia

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py` (fn `build_content_taxonomy`, ~linhas 455-539; helpers novos no módulo)
- Create: `tests/test_content_taxonomy_exclusividade.py`
- Create: `tests/fixtures/taxonomy/mf_teaching_plan.txt` (extraído do vivo, passo 1)

**Interfaces:**
- Consumes: `_topic_support_tokens`, `_strip_topic_code`, `_dedupe_taxonomy_topics`, `_normalize_match_text` (já existem no módulo).
- Produces: `_unit_title_core_tokens(title: str) -> set[str]` (usada também na Task 2); `build_content_taxonomy` passa a devolver tópicos-preview sob a unidade DONA do título.

- [ ] **Step 1: Extrair fixture real do teaching_plan do MF**

```bash
python -c "
import sys; sys.path.insert(0, '.')
from src.models.core import SubjectStore
from pathlib import Path
sp = SubjectStore().find_by_repo_root(r'C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor')
Path('tests/fixtures/taxonomy/mf_teaching_plan.txt').parent.mkdir(parents=True, exist_ok=True)
Path('tests/fixtures/taxonomy/mf_teaching_plan.txt').write_text(sp.teaching_plan, encoding='utf-8')
print('ok', len(sp.teaching_plan))
"
```

Adicionar na 1ª linha do teste (comentário): proveniência = `%APPDATA%/GPTTutorGenerator/subjects.json`, perfil MF, extraído 2026-08-07 (mtime da fonte 2026-08-04). NÃO editar o conteúdo.

- [ ] **Step 2: Escrever os testes RED**

```python
# tests/test_content_taxonomy_exclusividade.py
# Fixture: teaching_plan REAL do MF (subjects.json vivo, extraido 2026-08-07).
# Headings REAIS coletados do repo MF (audit 2026-08-07, spec-review §F3).
# Caso: bullets-preview "1.3.1. Verificacao de Modelos" / "1.3.2. Verificacao de
# Programas" na abertura da u01 contaminavam a assinatura da u01 (empate 4x4 no
# bloco-16 — docs/reports/2026-08-06-task3-colisao-rotulo-mf.md).
from pathlib import Path

from src.builder.extraction.content_taxonomy import (
    build_content_taxonomy,
    _unit_title_core_tokens,
)
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan
from src.builder.timeline.unit_matcher import _unit_tokens
from src.utils.helpers import slugify

MF_PLAN = Path("tests/fixtures/taxonomy/mf_teaching_plan.txt").read_text(encoding="utf-8")
MF_HEADINGS = [
    "VERIFICAÇÃO DE MODELOS",
    "Verificação de Modelos e Lógica Temporal",
    "checagem de modelos",
    "Verificação de Modelos NuSMV/NuXMV + Fasten",
    "Programação e Verificação com Dafny",
]


def _mk(plan, headings):
    return build_content_taxonomy(
        teaching_plan=plan,
        course_map_md="",
        glossary_md="",
        strong_headings=headings,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=lambda t: str(t),
        normalize_unit_slug=lambda title: slugify(title),
    )


def test_title_core_tokens_por_tokens_sem_regex_de_prefixo():
    assert _unit_title_core_tokens("Unidade 01 — Métodos Formais") == {"metodos", "formais"}
    assert _unit_title_core_tokens("Unidade de Aprendizagem 5 — Aprendizado de máquina") == {"aprendizado", "maquina"}
    assert _unit_title_core_tokens("UNIDADE 02 — Turing-Computabilidade\u200b") == {"turing", "computabilidade"}
    # sem prefixo padrao -> titulo inteiro e o nucleo (degradacao graciosa)
    assert _unit_title_core_tokens("Verificação de Modelos") == {"verificacao", "modelos"}


def test_preview_migra_para_unidade_dona():
    tax = _mk(MF_PLAN, MF_HEADINGS)
    units = tax["units"]
    assert len(units) == 3
    u01, u02, u03 = units
    labels_u01 = [t["label"] for t in u01["topics"]]
    assert all("Modelos (Model Checking)" not in l for l in labels_u01)
    assert all(l != "Verificação de Programas" for l in labels_u01)
    # aliases ricos foram junto pro dono
    labels_u03 = [t["label"] for t in u03["topics"]]
    assert any("Verificação de Modelos" in l for l in labels_u03)


def test_assinatura_u01_sem_tokens_da_u03():
    tax = _mk(MF_PLAN, MF_HEADINGS)
    u01, u02, u03 = tax["units"]
    assert "temporal" not in _unit_tokens(u01)
    assert "temporal" in _unit_tokens(u03)


def test_heading_com_nucleo_de_titulo_so_enriquece_a_dona():
    tax = _mk(MF_PLAN, ["Verificação de Modelos e Lógica Temporal"])
    u01, u02, u03 = tax["units"]
    aliases_u01 = [a for t in u01["topics"] for a in t.get("aliases", [])]
    assert "Verificação de Modelos e Lógica Temporal" not in aliases_u01


def test_titulo_de_um_token_nao_participa_da_exclusividade():
    # guard anti-falso-positivo: nucleo com < 2 tokens (ex.: "Deadlock" SO u04)
    assert _unit_title_core_tokens("Unidade 04 — _Deadlock_") == {"deadlock"}
    # a exclusividade exige >= 2 tokens; taxonomia com titulo curto nao move nada
    # (coberto indiretamente: MF nao tem titulo de 1 token; asserção documental)
```

- [ ] **Step 3: Rodar e confirmar RED**

Run: `python -m pytest tests/test_content_taxonomy_exclusividade.py -v`
Expected: FAIL — `_unit_title_core_tokens` não existe; depois do helper, `test_preview_migra_para_unidade_dona` falha (preview segue sob u01).

- [ ] **Step 4: Implementar em `content_taxonomy.py`**

Helpers no módulo (perto de `_strip_outline_prefix`):

```python
# Exclusividade de nucleo de titulo (campanha 2 §4-U1): nucleo por TOKENS,
# nunca regex de prefixo — titulos reais variam ("Unidade NN —", "Unidade de
# Aprendizagem N —", "UNIDADE NN —") e nada garante padrao em curso futuro.
_UNIT_TITLE_GENERIC = {"unidade", "aprendizagem", "modulo", "parte", "topico"}
_TITLE_CORE_MIN_TOKENS = 2  # nucleo de 1 token ("Deadlock") nao move nada: falso-positivo > beneficio


def _unit_title_core_tokens(title: str) -> set:
    toks = _topic_support_tokens(_strip_topic_code(str(title or "")))
    return {t for t in toks if t not in _UNIT_TITLE_GENERIC and not t.isdigit()}
```

Em `build_content_taxonomy`, DEPOIS do loop que monta `result_units` (linha ~500) e ANTES do loop de headings (linha ~502):

```python
    # (a) topico-preview cujo rotulo contem o nucleo do titulo de OUTRA unidade
    # migra pra unidade dona (bug MF: "1.3.1. Verificacao de Modelos" na abertura
    # da u01 empatava o DP 4x4 no bloco-16).
    title_cores = {}
    for unit in result_units:
        core = _unit_title_core_tokens(unit.get("title", ""))
        if len(core) >= _TITLE_CORE_MIN_TOKENS:
            title_cores[unit["slug"]] = core
    for unit in result_units:
        kept = []
        for topic in unit.get("topics", []) or []:
            label_toks = _topic_support_tokens(str(topic.get("label", "") or ""))
            owner = next(
                (slug for slug, core in title_cores.items()
                 if slug != unit["slug"] and core <= label_toks),
                None,
            )
            if owner is None:
                kept.append(topic)
                continue
            topic["unit_slug"] = owner
            dest = next(u for u in result_units if u["slug"] == owner)
            dest["topics"] = _dedupe_taxonomy_topics(list(dest.get("topics", []) or []) + [topic])
        unit["topics"] = kept
```

No loop de headings (502-536), antes de iterar `result_units`:

```python
        # (b) heading que contem nucleo de titulo de unidade so enriquece a dona
        heading_toks = _topic_support_tokens(heading_text)
        owner_units = [u for u in result_units
                       if title_cores.get(u["slug"]) and title_cores[u["slug"]] <= heading_toks]
        search_units = owner_units or result_units
```

e trocar `for unit in result_units:` por `for unit in search_units:` (SÓ nesse loop).

- [ ] **Step 5: Rodar os testes até GREEN**

Run: `python -m pytest tests/test_content_taxonomy_exclusividade.py -v`
Expected: PASS (5/5).

- [ ] **Step 6: Suite + não-regressão TCC**

Run: `python -m pytest -q` → 1881+5 passed / 4 skipped / 1 failed (o golden IA conhecido).
Sanity read-only TCC (0 colisões → no-op): `python scripts/rebuild_diff.py` → TCC com `0 blocos mudaram`. MF PODE mostrar mudança de unit no bloco-16? NÃO ainda — sem a Task 3 o DP mantém empate; esperado TAMBÉM `0 mudaram` no MF (assinatura muda, atribuição não — provado na simulação da revisão).

- [ ] **Step 7: Commit**

```bash
git add src/builder/extraction/content_taxonomy.py tests/test_content_taxonomy_exclusividade.py tests/fixtures/taxonomy/mf_teaching_plan.txt
git commit -m "feat(taxonomia): exclusividade de nucleo de titulo — preview migra pra unidade dona (U1, campanha 2)"
```

---

### Task 2: U1(c) — Higiene de heading (decoração markdown + administrativo)

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py` (`collect_strong_heading_candidates`, linhas 587-610)
- Test: `tests/test_content_taxonomy_exclusividade.py` (append)

**Interfaces:**
- Consumes: `_normalize_match_text`, `_collapse_ws` (módulo).
- Produces: `_clean_heading_text(text: str) -> str` (retorna `""` = descartar).

- [ ] **Step 1: Testes RED (casos REAIS da auditoria 2026-08-07)**

```python
# append em tests/test_content_taxonomy_exclusividade.py
from src.builder.extraction.content_taxonomy import _clean_heading_text


def test_clean_heading_strips_decoracao_markdown():
    assert _clean_heading_text("**Exercícios**") == "Exercícios"
    assert (
        _clean_heading_text("[Formal Verification of Axiom-Free Proof](./entries/x.html)")
        == "Formal Verification of Axiom-Free Proof"
    )


def test_clean_heading_descarta_administrativo_e_tabela():
    # casos reais: TCC plano-de-ensino.md e geradas "Sumário"/"Conteúdo Extraído"
    assert _clean_heading_text("| NOME | E-MAIL | |---| Anderson |") == ""
    assert _clean_heading_text("PLANO DE ENSINO") == ""
    assert _clean_heading_text("PROFESSOR (ES)") == ""
    assert _clean_heading_text("Sumário") == ""
    assert _clean_heading_text("Conteúdo Extraído") == ""
    assert _clean_heading_text("Imagens Curadas") == ""


def test_clean_heading_preserva_conteudo_legitimo():
    assert _clean_heading_text("Verificação de Modelos e Lógica Temporal") == "Verificação de Modelos e Lógica Temporal"
```

Run: `python -m pytest tests/test_content_taxonomy_exclusividade.py -k clean_heading -v` → FAIL (fn não existe).

- [ ] **Step 2: Implementar**

```python
_ADMIN_HEADING_NORMS = {
    "plano de ensino", "professor", "professor es", "professores",
    "sumario", "conteudo extraido", "imagens curadas", "referencias", "bibliografia",
}
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def _clean_heading_text(text: str) -> str:
    t = _MD_LINK_RE.sub(r"\1", str(text or ""))
    t = t.replace("**", "").replace("__", "")
    if "|" in t:  # linha de tabela nunca e heading legitimo
        return ""
    t = _collapse_ws(t)
    norm = _normalize_match_text(t)
    norm_alpha = " ".join(w for w in norm.split() if w.isalpha())
    if norm_alpha in _ADMIN_HEADING_NORMS:
        return ""
    return t
```

Em `collect_strong_heading_candidates`, dentro do loop de headings (linha ~604):

```python
            for heading in file_headings[:4]:
                heading = _clean_heading_text(heading)
                heading_slug = slugify(heading)
                if heading_slug and heading_slug not in seen:
```

- [ ] **Step 3: GREEN + suite**

Run: `python -m pytest tests/test_content_taxonomy_exclusividade.py -v` → PASS.
Run: `python -m pytest -q` → sem fail novo.

- [ ] **Step 4: Commit**

```bash
git add src/builder/extraction/content_taxonomy.py tests/test_content_taxonomy_exclusividade.py
git commit -m "feat(taxonomia): higiene de heading — decoracao markdown e administrativo fora do alias-enrichment (U1c)"
```

---

### Task 3: U1b — Desempate por sinal concentrado no DP

**Files:**
- Modify: `src/builder/timeline/unit_matcher.py:75-102` (miolo do DP em `assign_units_positional`)
- Create: `tests/test_unit_matcher_desempate.py`

**Interfaces:**
- Consumes/Produces: assinatura de `assign_units_positional(class_blocks, units) -> List[Tuple[str, float]]` INALTERADA (mudança só no tie-break interno).

- [ ] **Step 1: Testes RED**

```python
# tests/test_unit_matcher_desempate.py
# Fixture destilada do caso REAL bloco-15/16/17/20 do MF pos-U1
# (docs/reports/2026-08-07-spec-review-unidades.md §A2/A3: empate de CAMINHO
# 4+0+0 vs 3+1+0; matriz real em 2026-08-06-task3-colisao-rotulo-mf.md).
from src.builder.timeline.unit_matcher import assign_units_positional


def _unit(slug, *labels):
    return {"slug": slug, "title": "", "topics": [{"label": l, "aliases": []} for l in labels]}


def _block(bid, topic_text):
    return {"id": bid, "topic_text": topic_text, "sessions": []}


UNITS = [
    _unit("unidade-01", "logica predicados verificacao formal"),
    _unit("unidade-02", "exercicios logica verificacao programas hoare"),
    _unit("unidade-03", "logica temporal modelos verificacao"),
]
BLOCKS = [
    _block("b15", "hoare programas logica"),                                  # aff [1,3,1]
    _block("b16", "exercicios ferramenta logica modelos temporal verificacao"),  # aff [2,3,4]
    _block("b17", "exercicios revisao"),                                      # aff [0,1,0]
    _block("b20", "devolucao provas"),                                        # aff [0,0,0]
]


def test_empate_de_caminho_vence_sinal_concentrado():
    # caminho "ficar": 3+1+0 == caminho "avancar": 4+0+0 -> soma empata;
    # soma de quadrados 9+1 < 16 -> avancar vence
    out = dict(zip([b["id"] for b in BLOCKS], assign_units_positional(BLOCKS, UNITS)))
    assert out["b16"] == ("unidade-03", 0.6)
    assert out["b15"] == ("unidade-02", 0.6)


def test_sem_empate_nada_muda():
    # b17 com 2 tokens de u02 -> ficar (3+2) > avancar (4+0): sem empate,
    # comportamento identico ao atual
    blocks = [
        _block("b15", "hoare programas logica"),
        _block("b16", "exercicios ferramenta logica modelos temporal verificacao"),
        _block("b17", "exercicios hoare revisao"),
    ]
    out = dict(zip([b["id"] for b in blocks], assign_units_positional(blocks, UNITS)))
    assert out["b16"] == ("unidade-02", 0.4)


def test_sem_sinal_nenhum_continua_fallback():
    blocks = [_block("b1", "xyzabc qwerty")]
    assert assign_units_positional(blocks, UNITS) == []
```

Run: `python -m pytest tests/test_unit_matcher_desempate.py -v` → `test_empate_de_caminho_vence_sinal_concentrado` FAIL (hoje b16 fica em unidade-02@0.4); os outros 2 PASS (pinam o comportamento atual).

- [ ] **Step 2: Implementar — DP com score lexicográfico `(Σaff, Σaff²)`**

Substituir `unit_matcher.py:75-102` por:

```python
    # Tie-break secundario por sinal concentrado (campanha 2 U1b): empate na
    # soma -> vence o caminho com maior soma de quadrados (sinal forte num
    # bloco > migalhas espalhadas; caso real bloco-16 MF). Empate duplo
    # mantem menor indice (nao avancar atoa).
    NEG = (float("-inf"), float("-inf"))
    dp = [[NEG] * m for _ in range(n)]
    par = [[-1] * m for _ in range(n)]
    for u in range(m):
        dp[0][u] = (aff[0][u], aff[0][u] ** 2)
    for i in range(1, n):
        for u in range(m):
            best = NEG
            bu = -1
            # melhor unidade anterior pu <= u; empate (soma E soma^2) -> menor pu
            for pu in range(u + 1):
                if dp[i - 1][pu] > best:
                    best = dp[i - 1][pu]
                    bu = pu
            dp[i][u] = (aff[i][u] + best[0], aff[i][u] ** 2 + best[1])
            par[i][u] = bu

    # unidade final: maior (soma, soma^2); empate -> menor indice
    last = 0
    best = NEG
    for u in range(m):
        if dp[n - 1][u] > best:
            best = dp[n - 1][u]
            last = u
```

(Resto da função — reconstrução `assign` e confs — INALTERADO.)

- [ ] **Step 3: GREEN + suite + preview read-only**

Run: `python -m pytest tests/test_unit_matcher_desempate.py -v` → 3/3 PASS.
Run: `python -m pytest -q` → sem fail novo.
Run: `python scripts/rebuild_diff.py` → esperado: **MF bloco-16 `unidade-02 -> unidade-03`** (único diff de unidade em MF); SO/ES2/TCC 0 mudanças de unidade; **IA: registrar o que aparecer, NÃO agir** (repo IA só muda na Task 11). Colar a saída no commit message body.

- [ ] **Step 4: Commit**

```bash
git add src/builder/timeline/unit_matcher.py tests/test_unit_matcher_desempate.py
git commit -m "feat(matcher): desempate do DP por sinal concentrado (U1b) — bloco-16 MF destravado"
```

---

### Task 4: U5 — W1 canônico + 3 warnings de degradação muda

**Files:**
- Modify: `src/builder/ops/taxonomy_inputs.py:16-32` (param `entries=None` + warning)
- Modify: `src/builder/ops/pedagogical_regeneration.py:394-404` (W1 adota fn canônica)
- Modify: `src/builder/engine.py:2124` (injeção)
- Modify: `src/builder/routing/file_map.py:1500-1501` e `:1629-1634` (warnings)
- Modify: `src/builder/extraction/content_taxonomy.py:598` (warning skip de path)
- Create: `tests/test_degradacao_avisada.py`

**Interfaces:**
- Produces: `build_rich_content_taxonomy(repo_root, course_meta, subject_profile, *, taxonomy_fn, filter_live_fn, entries=None)` — `entries=None` lê manifest do disco (comportamento atual); entries passadas = usa direto (caminho W1, sem re-read).

- [ ] **Step 1: Testes RED (caplog)**

```python
# tests/test_degradacao_avisada.py
import json
import logging

from src.builder.ops.taxonomy_inputs import build_rich_content_taxonomy
from src.builder.extraction.content_taxonomy import collect_strong_heading_candidates


def test_manifest_ausente_avisa(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        out = build_rich_content_taxonomy(
            tmp_path, {"_repo_root": tmp_path}, None,
            taxonomy_fn=lambda cm, sp, live: {"units": [], "n": len(live)},
            filter_live_fn=lambda root, entries: entries,
        )
    assert out["n"] == 0
    assert any("manifest" in r.message.lower() for r in caplog.records)


def test_entries_em_memoria_nao_le_disco(tmp_path):
    # manifest.json NAO existe; entries explicitas passam direto (caminho W1)
    out = build_rich_content_taxonomy(
        tmp_path, {"_repo_root": tmp_path}, None,
        taxonomy_fn=lambda cm, sp, live: {"units": [], "n": len(live)},
        filter_live_fn=lambda root, entries: entries,
        entries=[{"id": "x"}],
    )
    assert out["n"] == 1


def test_heading_md_inexistente_avisa(tmp_path, caplog):
    # caso real vivo: IA artigo-usando-agrupamento -> content/curated/*.md ausente
    entries = [{"id": "quebrado", "approved_markdown": "content/curated/nao-existe.md"}]
    with caplog.at_level(logging.WARNING):
        out = collect_strong_heading_candidates(tmp_path, entries)
    assert out == []
    assert any("nao-existe.md" in r.message for r in caplog.records)
```

Run: `python -m pytest tests/test_degradacao_avisada.py -v` → FAIL (kwarg `entries` não existe; warnings não emitidos).

- [ ] **Step 2: Implementar `taxonomy_inputs.py`**

```python
logger = logging.getLogger(__name__)


def build_rich_content_taxonomy(
    repo_root,
    course_meta: dict,
    subject_profile,
    *,
    taxonomy_fn: Callable[..., dict],
    filter_live_fn: Callable[..., list],
    entries: Optional[list] = None,
) -> dict:
    if entries is None:
        manifest_path = Path(repo_root) / "manifest.json"
        entries = []
        if manifest_path.is_file():
            try:
                entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", []) or []
            except (json.JSONDecodeError, OSError):
                logger.warning("manifest.json ilegivel em %s — taxonomia degrada pra pobre (0 entries)", repo_root)
                entries = []
        else:
            logger.warning("manifest.json ausente em %s — taxonomia degrada pra pobre (0 entries)", repo_root)
    live = filter_live_fn(repo_root, entries)
    return taxonomy_fn(course_meta, subject_profile, live)
```

- [ ] **Step 3: W1 adota a fn canônica**

Em `engine.py:2124` trocar a injeção `build_file_map_content_taxonomy_from_course_fn=_build_file_map_content_taxonomy_from_course` por `build_rich_content_taxonomy_fn=_build_rich_content_taxonomy` (e o nome do parâmetro em `regenerate_pedagogical_files`). Em `pedagogical_regeneration.py:398-402`:

```python
    content_taxonomy = build_rich_content_taxonomy_fn(
        builder.root_dir,
        runtime_course_meta,
        builder.subject_profile,
        entries=live_manifest_entries,
    )
```

(`live_manifest_entries` da linha 394 continua alimentando `manifest["entries"]` na 395 — sem mudança. Nota: `engine._build_rich_content_taxonomy` (engine.py:2280) precisa repassar `entries=` pro ops — adicionar o kwarg pass-through.)

- [ ] **Step 4: Warnings nos early-returns de `file_map.py` e no coletor**

`file_map.py:1500-1501` (taxonomia): antes do return vazio, `logger.warning("sem teaching_plan no perfil — content_taxonomy vazia (curso perde estrutura de unidades)")`. `file_map.py:1629-1634` (unit index): no ramo `not teaching_plan`, `logger.warning("sem teaching_plan — unit_index cai pro fallback repo-derived (%d specs)", len(unit_specs))`. `content_taxonomy.py:598`: no `continue` de path inexistente, `logger.warning("heading skip: %s aponta md inexistente (%s)", entry.get("id"), rel_path)` — atenção: só quando `rel_path` EXISTE no manifest mas o arquivo não resolve (entry sem campo md continua silencioso, é o caso esperado código/professor).

- [ ] **Step 5: GREEN + suite + commit**

Run: `python -m pytest tests/test_degradacao_avisada.py -v` → PASS. `python -m pytest -q` → sem fail novo.

```bash
git add src/builder/ops/taxonomy_inputs.py src/builder/ops/pedagogical_regeneration.py src/builder/engine.py src/builder/routing/file_map.py src/builder/extraction/content_taxonomy.py tests/test_degradacao_avisada.py
git commit -m "refactor(taxonomia): W1 usa build_rich_content_taxonomy canonica + warnings nas degradacoes mudas (U5)"
```

---

### Task 5: U2 — Sonda canônica = caminho de produção

**Files:**
- Create: `scripts/course_probe.py`
- Modify: `scripts/rebuild_diff.py` (consome a sonda)
- Modify: `scripts/verify_units.py` (consome a sonda; contagem parser-vs-índice)
- Create: `tests/test_course_probe.py`

**Interfaces:**
- Produces: `compute_production_index(sp) -> dict` (índice enriquecido idêntico ao que W1/W2 escreveriam, `persist=False`) e `compute_production_taxonomy(sp) -> dict`. TODA sonda de unidade da campanha passa por aqui.

- [ ] **Step 1: Teste RED**

```python
# tests/test_course_probe.py
import scripts.course_probe as cp


class _FakeSP:
    def __init__(self, root):
        self.repo_root = str(root)
        self.teaching_plan = ""


def test_probe_chama_pipeline_completo_na_ordem(tmp_path, monkeypatch):
    (tmp_path / "manifest.json").write_text('{"course": {}, "entries": []}', encoding="utf-8")
    calls = []
    monkeypatch.setattr(cp.engine, "_build_rich_content_taxonomy",
                        lambda *a, **k: calls.append("tax") or {"units": []})

    def _ctx(cm, sp, content_taxonomy=None, persist=True):
        calls.append(("ctx", persist))
        return {"timeline_index": {"version": 4, "blocks": []}}

    monkeypatch.setattr(cp.engine, "_build_file_map_timeline_context_from_course", _ctx)
    monkeypatch.setattr(cp.engine, "_persist_enriched_timeline_index",
                        lambda idx: calls.append("persist") or {"version": 4, "blocks": []})
    out = cp.compute_production_index(_FakeSP(tmp_path))
    assert calls == ["tax", ("ctx", False), "persist"]
    assert out["blocks"] == []
```

Run: `python -m pytest tests/test_course_probe.py -v` → FAIL (módulo não existe).

- [ ] **Step 2: Implementar `scripts/course_probe.py`**

```python
"""Sonda canonica de indice/unidade: EXATAMENTE o caminho de producao
(W1/W2), persist=False. Regra da campanha 2 (U2): numero de sonda que nao
passe por aqui nao vale como gate. Padrao extraido de rebuild_diff.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.builder.engine as engine  # noqa: E402


def _course_meta(repo: Path) -> dict:
    mp = repo / "manifest.json"
    cm = json.loads(mp.read_text(encoding="utf-8")).get("course", {}) if mp.exists() else {}
    return {**cm, "_repo_root": repo}


def compute_production_taxonomy(sp) -> dict:
    repo = Path(getattr(sp, "repo_root", "") or "")
    return engine._build_rich_content_taxonomy(repo, _course_meta(repo), sp)


def compute_production_index(sp) -> dict:
    repo = Path(getattr(sp, "repo_root", "") or "")
    cm = _course_meta(repo)
    rich = engine._build_rich_content_taxonomy(repo, cm, sp)
    ctx = engine._build_file_map_timeline_context_from_course(
        cm, sp, content_taxonomy=rich, persist=False
    )
    return engine._persist_enriched_timeline_index(
        ctx.get("timeline_index") or {"version": 4, "blocks": []}
    )
```

- [ ] **Step 3: Refatorar `rebuild_diff.py` e `verify_units.py`**

`rebuild_diff.diff_course` substitui as linhas 35-39 por `new = course_probe.compute_production_index(sp)` (import no topo). `verify_units.py`: trocar qualquer recompute próprio pela sonda + imprimir por curso `parser=N indice_disco=N indice_sonda=N` (parser via `_parse_units_from_teaching_plan(sp.teaching_plan)`; disco via `course/.timeline_index.json`; sonda via `compute_production_index`). Ler o arquivo atual ANTES de editar e preservar o que ele já reporta.

- [ ] **Step 4: GREEN + prova nos 5 cursos**

Run: `python -m pytest tests/test_course_probe.py -v` → PASS. `python -m pytest -q` → sem fail novo.
Run: `python scripts/verify_units.py` → tabela 5 cursos. Esperado AGORA (pós Tasks 1-3, pré-cura): sonda MF = 3 unidades com bloco-16 u03; disco MF = 2 (diverge DE PROPÓSITO até a cura — anotar no output do commit).

- [ ] **Step 5: Commit**

```bash
git add scripts/course_probe.py scripts/rebuild_diff.py scripts/verify_units.py tests/test_course_probe.py
git commit -m "feat(sonda): course_probe canonica no caminho de producao; rebuild_diff/verify_units consomem (U2)"
```

---

### Task 6: U3 — Template de gold + eval_units

**Files:**
- Create: `scripts/gold_units_template.py`
- Create: `scripts/eval_units.py`
- Create: `tests/test_eval_units.py`

**Interfaces:**
- Produces: `docs/reports/gold_templates/gold_units_<CURSO>.csv` (colunas: `block_uuid,block_id,date_start,date_end,kind,topic_text,unit_slug_atual,true_unit,notes`); `scripts/eval_units.py [--course CURSO]` lê `tests/fixtures/eval/gold_units_<CURSO>.csv` e imprime acc por curso + mismatches; exit 1 se regressão vs `--baseline <json>`.

- [ ] **Step 1: Teste RED do eval (fixture sintética mínima, 3 linhas)**

```python
# tests/test_eval_units.py
import json

from scripts.eval_units import score_course


def test_score_course_compara_por_block_uuid(tmp_path):
    gold_csv = tmp_path / "gold_units_X.csv"
    gold_csv.write_text(
        "block_uuid,block_id,true_unit\n"
        "uuid-1,bloco-01,unidade-01\n"
        "uuid-2,bloco-02,unidade-02\n"
        "uuid-3,bloco-03,\n",  # sem rotulo -> fora do denominador
        encoding="utf-8",
    )
    index = {"blocks": [
        {"block_uuid": "uuid-1", "id": "bloco-01", "unit_slug": "unidade-01"},
        {"block_uuid": "uuid-2", "id": "bloco-02", "unit_slug": "unidade-99"},
        {"block_uuid": "uuid-3", "id": "bloco-03", "unit_slug": "unidade-03"},
    ]}
    r = score_course(gold_csv, index)
    assert (r["ok"], r["total"]) == (1, 2)
    assert r["mismatches"] == [{"block_uuid": "uuid-2", "block_id": "bloco-02",
                               "true": "unidade-02", "got": "unidade-99"}]
```

Run: `python -m pytest tests/test_eval_units.py -v` → FAIL.

- [ ] **Step 2: Implementar os 2 scripts**

`scripts/eval_units.py` (núcleo):

```python
"""Regua de unidade: gold block_uuid->true_unit vs indice EM DISCO (producao).
Uso: python scripts/eval_units.py [--course MF] [--baseline caminho.json]
Gold: tests/fixtures/eval/gold_units_<CURSO>.csv (keyed block_uuid — NUNCA
bloco-NN posicional; licao do drift do gold MF, tracker 2026-07-08)."""
import csv


def score_course(gold_csv, index) -> dict:
    by_uuid = {b.get("block_uuid"): b for b in index.get("blocks", [])}
    ok, total, mismatches = 0, 0, []
    with open(gold_csv, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            true = (row.get("true_unit") or "").strip()
            if not true:
                continue
            total += 1
            blk = by_uuid.get((row.get("block_uuid") or "").strip()) or {}
            got = str(blk.get("unit_slug") or "")
            if got == true:
                ok += 1
            else:
                mismatches.append({"block_uuid": row.get("block_uuid"),
                                   "block_id": row.get("block_id"),
                                   "true": true, "got": got})
    return {"ok": ok, "total": total, "mismatches": mismatches}
```

`main()`: itera `SubjectStore().names()`, mapeia curso→`gold_units_<CURSO>.csv` (curso = sigla do nome do repo: Metodos-Formais→MF, Sistemas-Operacionais→SO, Engenharia-Software-2→ES2, Inteligencia-Artifical→IA, TCC→TCC), carrega `course/.timeline_index.json`, imprime `CURSO ok/total (pct) + mismatches`, grava json com `--out`. `--baseline x.json` → exit 1 se `ok` de algum curso cair.

`scripts/gold_units_template.py`: para cada curso, `compute_production_index`? **NÃO — disco** (gold rotula o estado ATUAL de produção; sonda ainda não curada): ler `course/.timeline_index.json`, filtrar blocos com `not b.get("source_kind")` (82 no total, contado na revisão), escrever CSV `utf-8-sig` com as colunas da interface (`true_unit`/`notes` vazias). Imprimir contagem por curso.

- [ ] **Step 3: GREEN + gerar templates**

Run: `python -m pytest tests/test_eval_units.py -v` → PASS.
Run: `python scripts/gold_units_template.py` → 5 CSVs em `docs/reports/gold_templates/`, total 82 linhas.

- [ ] **Step 4: Commit + HALT**

```bash
git add scripts/gold_units_template.py scripts/eval_units.py tests/test_eval_units.py docs/reports/gold_templates/gold_units_*.csv
git commit -m "feat(gold): template gold_units (82 blocos, block_uuid) + regua eval_units (U3)"
```

**HALT — entregar os 5 CSVs ao user para rotulagem (Task 7). Não prosseguir para curas sem gold.**

---

### Task 7: [USER] Rotulagem do gold + baseline pré-cura

**Files:**
- Create: `tests/fixtures/eval/gold_units_<CURSO>.csv` ×5 (cópia dos templates rotulados)
- Create: `docs/reports/2026-08-07-eval-units-baseline-precura.json`

- [ ] **Step 1: User rotula `true_unit` nos 5 CSVs** (slugs válidos = os do índice/plano do curso; deixar vazio = bloco fora do denominador; `notes` livre). Dúvida de rótulo → resolver com o user ANTES de congelar, nunca chutar.
- [ ] **Step 2: Congelar**: copiar os 5 rotulados para `tests/fixtures/eval/` (mesmo nome). Validar: `python scripts/eval_units.py` roda 5/5 sem erro de parse e sem `block_uuid` desconhecido.
- [ ] **Step 3: Baseline pré-cura**: `python scripts/eval_units.py --out docs/reports/2026-08-07-eval-units-baseline-precura.json` — anotar acc por curso (MF esperado: bloco-16 mismatch = a doença medida).
- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/eval/gold_units_*.csv docs/reports/2026-08-07-eval-units-baseline-precura.json
git commit -m "chore(gold): gold_units 5/5 rotulado (sign-off user) + baseline pre-cura (U3)"
```

---

### Task 8: U4-MF — Cura gated do Metodos-Formais-Tutor

**Files:** nenhum do projeto — runbook sobre `C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor` (escrita AUTORIZADA por esta task, única exceção à constraint global).

- [ ] **Step 1: Snapshot**: no MF-Tutor, `git add -A && git commit --allow-empty -m "snapshot pre-cura-unidades"` + copiar os 5 sidecars gitignored (`course/.content_taxonomy.json`, `.timeline_index.json`, `.assessment_context.json`, `.tag_catalog.json`, `.semantic_profile.generated.json`) pro scratchpad com `sha256sum > SHA256SUMS.txt`, ecoando ARQUIVO POR ARQUIVO (nunca glob mudo).
- [ ] **Step 2: Preview read-only**: `python scripts/rebuild_diff.py` → MF: esperado SÓ bloco-16 `unidade-02 -> unidade-03` (+kind 0). Qualquer outro diff de unidade → PARAR, investigar antes de escrever.
- [ ] **Step 3: Reprocess real**: `python scripts/reprocess_assignments.py "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor"` — confirmar linha `[profile]` no stdout (flags vivas, T18).
- [ ] **Step 4: Gates (TODOS, na ordem)**:
  1. `python scripts/verify_units.py` → MF `parser=3 indice_disco=3` e bloco-16 `unidade-03-verificacao-de-modelos`.
  2. `python scripts/eval_units.py --baseline docs/reports/2026-08-07-eval-units-baseline-precura.json` → MF sobe (bloco-16 sai dos mismatches), NENHUM curso cai.
  3. `computed_block_id`: diff manifest pré (backup `.bak` do reprocess) vs pós → 0 mudanças (ou cada mudança justificada por escrito).
  4. Réguas vivas: `python scripts/eval_ground_truth.py` (MF 64/66=97.0) · `python scripts/fase2_prova_TCC.py` (84.2/cw0) · `python scripts/fase4_prova_D9.py` (det 53/58, voter 58/58) · `python scripts/fase5_prova_tier2.py` (6/8 cw0) · `python scripts/audit_gold_freshness.py` (hard=0 5/5) · `python scripts/rebuild_diff.py` (MF agora 0 — disco == código).
  5. `python -m pytest -q` → sem fail novo.
- [ ] **Step 5: FAIL em qualquer gate → rollback** (restaurar sidecars do snapshot + `git checkout`, verificar sha256 byte-a-byte, `git status --porcelain -uall` vazio) + report em `docs/reports/` + HALT ruling.
- [ ] **Step 6: PASS → commit no MF-Tutor** (`cura unidades: bloco-16 -> unidade-03 (campanha 2 U4-MF)`) + registrar números no tracker (Task 13 consolida).

---

### Task 9: U4-SO — Diagnóstico + cura do Sistemas-Operacionais-Tutor

- [ ] **Step 1: Diagnóstico READ-ONLY (antes de qualquer escrita)**: com `course_probe.compute_production_index`, responder por escrito: (a) u04-deadlock aparece na sonda pós-fixes? (b) o conteúdo de deadlock segue absorvido no `topic_text` do bloco-05 (confirmado na revisão) — de onde vem essa agregação (sessões SARC do bloco? material mal-janelado?) — inspecionar `blocks[].sessions[].label` dos blocos 04-06 no índice + linhas SARC correspondentes; (c) a não-monotonicidade 10-12 (u07→u05→u07) some no recompute (camada stale) ou persiste?
- [ ] **Step 2: DECISÃO**: se a recuperação da u04 exigir re-segmentação de blocos (mexer em composição de bloco, não em atribuição de unidade) → **HALT ruling com o user** (opções + custo). Se for atribuição (assinatura/matcher), especificar o fix, TDD igual Tasks 1-3, commit no projeto.
- [ ] **Step 3: Cura**: mesmo runbook da Task 8 (snapshot+sha256 → preview → reprocess → gates 1-5 → rollback-ou-commit). Gate extra SO: sequência de unidades no índice pós-cura é monotônica; bloco-12 conforme gold (recompute muda u07→u05 — o gold do user decide o certo, não assumir).

---

### Task 10: U4-ES2 — Diagnóstico + cura do Engenharia-Software-2-Tutor

- [ ] **Step 1: Diagnóstico READ-ONLY**: por que u03-testes-de-software nunca vence? Medir com a sonda: assinatura `_unit_tokens(u03)` vs tokens dos blocos finais. Pista da auditoria (spec §2): 8/35 entries (roteiro1-7 + history-service) não têm campo md → zero headings. Verificar: os materiais de TESTES do curso estão nesses roteiros? Se sim, a assinatura da u03 depende só do plano (sem enriquecimento) — quantificar o gap.
- [ ] **Step 2: DECISÃO**: fix candidato barato (ex.: tokens do plano bastam mas há colisão/migalha — reaproveitar U1/U1b) → TDD + commit. Fix caro (gerar md pros roteiros / mudar coletor) → HALT ruling.
- [ ] **Step 3: Cura**: runbook da Task 8 (gates 1-5).

---

### Task 11: U4-IA — HALT-primeiro: diagnóstico de viabilidade + ruling

- [ ] **Step 1: Diagnóstico READ-ONLY** (nenhuma escrita no IA-Tutor): mapear cronologia real vs ordem do plano — pra cada bloco, datas + conteúdo vs unidade "ideal" do gold do user (Task 7 dá o mapa). Confirmar a violação monotônica (ML/u05 semanas 2-9; agentes/u03 semana 16) com os dados, não com a narrativa.
- [ ] **Step 2: Relatório de opções pro user** (`docs/reports/`): (a) aceitar limitação documentada (índice IA fica com 3 unidades, gold registra o teto); (b) modo não-monotônico por curso no matcher (custo/risco estimados); (c) outra via achada no diagnóstico. **HALT — ruling do user.**
- [ ] **Step 3: Executar o ruling** (se (b): TDD igual Tasks 1-3 + flag/gating por curso; se (a): registrar no tracker e NO gold). Cura (se houver) = runbook Task 8.

---

### Task 12: U6 — Resíduo do scorer (aula-13 TCC, sandbox)

- [ ] **Step 1**: `git -C C:/Users/Humberto/Documents/GitHub/TCC-Tutor show 91c1d2a --stat` → identificar ONDE vive o pino da aula-13 (arquivo+campo exatos).
- [ ] **Step 2**: copiar TCC-Tutor pro scratchpad (cópia INTEIRA), remover o pino na CÓPIA, rodar a sonda (`course_probe` com um `sp` fake apontando `repo_root` pra cópia; `teaching_plan` real do perfil TCC) → onde cai `aula-13-teorema-de-rice` sem pino?
- [ ] **Step 3**: bloco-12 (correto) → **óbito**: U1 matou o resíduo; registrar veredito no tracker. bloco-13 (atraído pelo rótulo rico) → especificar guard C6-equivalente no caminho do scorer como item [CODE] com caso de teste pronto (o sandbox É o RED) — implementar SÓ com aprovação do user (pode ser follow-up, pino segura produção).
- [ ] **Step 4**: commit do veredito (report curto em `docs/reports/`).

---

### Task 13: Fechamento da campanha

- [ ] **Step 1**: régua integral: `python -m pytest -q` + as 6 réguas da Task 8 gate 4 + `python scripts/eval_units.py --baseline ...` → colar números.
- [ ] **Step 2**: tracker `docs/reports/pendencias.md`: entrada Concluído da campanha 2 (placar por curso, rulings, achados novos com `as-of`); mover itens fechados; registrar U6/IA conforme veredito; `last_updated`.
- [ ] **Step 3**: spec + plano → `Feitos/` (`git mv`); handoff novo em `docs/reports/` com a fila (campanha 3/3 SO providers → reprocess-all → cutover).
- [ ] **Step 4**: commit `docs(campanha-unidades): fechamento`.

---

## Self-review (feito na escrita)

1. **Cobertura do spec**: U1(a,b)=Task 1 · U1(c)=Task 2 · U1b=Task 3 · U5=Task 4 · U2=Task 5 · U3=Tasks 6-7 · U4=Tasks 8-11 (MF/SO/ES2/IA, TCC sem cura ✓) · U6=Task 12 · aceites §7=Tasks 8-13. Não-objetivos respeitados (nada de merge de fontes, deleção, reprocess-all).
2. **Placeholders**: nenhum TBD; Tasks 9-11 são investigação por natureza — os passos dizem O QUE medir e ONDE, com HALT explícito nas bifurcações que são do user.
3. **Consistência de tipos**: `assign_units_positional` assinatura inalterada (Task 3); `build_rich_content_taxonomy` ganha kwarg opcional `entries` (Task 4) e o wrapper `engine._build_rich_content_taxonomy` repassa; `compute_production_index(sp)->dict` usado nas Tasks 5, 6 (nota: template usa DISCO de propósito), 9, 11, 12; `score_course(gold_csv, index)->dict` consistente entre teste e script.
