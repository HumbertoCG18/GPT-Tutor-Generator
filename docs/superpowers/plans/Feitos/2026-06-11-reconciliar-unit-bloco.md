# Reconciliar unidade × bloco (F1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o bloco autoritativo da unidade — manual de bloco vence sempre; no auto, bloco define a unidade só se `block_confidence ≥ unit_confidence`, senão mantém a unidade forte e marca conflito pra revisão.

**Architecture:** Helper puro `reconcile_unit_with_block` (em `routing/file_map.py`, irmão de `resolve_effective_block`) centraliza a regra. Ligado em `resolve_unit_block_tags` (`extraction/content_taxonomy.py`), substituindo a herança parcial já existente (:1136-1146). Conflito persiste num campo novo `unit_block_conflict` do FileEntry. Editor reflete origem/conflito e desabilita o combo de unidade quando há bloco manual; avisa subunidade órfã.

**Tech Stack:** Python (dataclass, matcher determinístico), tkinter (editor), pytest.

Spec: `docs/superpowers/specs/2026-06-11-reconciliar-unit-bloco-design.md`

---

### Task 1: Campo `unit_block_conflict` no FileEntry

**Files:**
- Modify: `src/models/core.py:101` (após `source_section`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `tests/test_core.py` (siga o estilo de construção de FileEntry já usado no arquivo; se houver um helper `_entry`/builder, reuse-o; senão construa com os campos obrigatórios `source_path/file_type/category/title`):

```python
def test_unit_block_conflict_roundtrip():
    from src.models.core import FileEntry
    e = FileEntry(source_path="C:/x/a.pdf", file_type="pdf", category="material", title="t",
                  unit_block_conflict={"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-3"})
    d = e.to_dict()
    assert d["unit_block_conflict"] == {"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-3"}
    assert FileEntry.from_dict(d).unit_block_conflict == {"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-3"}


def test_unit_block_conflict_default_not_emitted():
    from src.models.core import FileEntry
    d = FileEntry(source_path="C:/x/a.pdf", file_type="pdf", category="material", title="t").to_dict()
    assert "unit_block_conflict" not in d  # default {} não incha o manifest
    assert FileEntry.from_dict({"source_path": "C:/x/a.pdf", "file_type": "pdf",
                                "category": "material", "title": "t"}).unit_block_conflict == {}
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_core.py::test_unit_block_conflict_roundtrip tests/test_core.py::test_unit_block_conflict_default_not_emitted -v`
Expected: FAIL (`TypeError: __init__() got an unexpected keyword argument 'unit_block_conflict'`)

- [ ] **Step 3: Adicionar o campo**

Em `src/models/core.py`, após a linha 101 (`source_section: str = ""`):

```python
    # Conflito unidade×bloco detectado no auto (F1): a unidade forte (>=0.65)
    # venceu um bloco que apontava OUTRA unidade (block_confidence < unit_conf).
    # {} quando não há conflito. Sinal de revisão exibido no editor; o build
    # mantém a unidade forte. Distinto da herança silenciosa (que não é conflito).
    unit_block_conflict: dict = field(default_factory=dict)
```

(`field` já está importado no módulo — confirme o import no topo; é usado por `manual_tags`.)

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_core.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py tests/test_core.py
git commit -m "feat(model): FileEntry unit_block_conflict (sinal de revisão F1)"
```

---

### Task 2: Helper puro `reconcile_unit_with_block`

**Files:**
- Modify: `src/builder/routing/file_map.py` (após `resolve_effective_block`, ~linha 583)
- Test: `tests/test_reconcile_unit_block.py` (criar)

- [ ] **Step 1: Escrever os testes que falham**

Criar `tests/test_reconcile_unit_block.py`:

```python
from src.builder.routing.file_map import reconcile_unit_with_block


def _call(**kw):
    base = dict(
        computed_unit_slug="", unit_confidence=0.0,
        computed_block_id="", block_confidence=0.0,
        block_unit_slug="", block_is_manual=False, has_manual_unit=False,
    )
    base.update(kw)
    return reconcile_unit_with_block(**base)


def test_manual_block_wins_even_over_manual_unit():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=1.0,
        computed_block_id="bloco-2", block_confidence=1.0,
        block_unit_slug="unidade-2", block_is_manual=True, has_manual_unit=True,
    )
    assert unit == "unidade-2"
    assert reasons == ["unidade_do_bloco_manual"]
    assert conflict == {}


def test_manual_unit_without_manual_block_keeps():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=1.0,
        computed_block_id="bloco-2", block_confidence=0.9,
        block_unit_slug="unidade-2", block_is_manual=False, has_manual_unit=True,
    )
    assert unit == "unidade-1"
    assert reasons == []
    assert conflict == {}


def test_auto_no_block_keeps():
    unit, reasons, conflict = _call(computed_unit_slug="unidade-1", unit_confidence=0.8)
    assert unit == "unidade-1"
    assert reasons == [] and conflict == {}


def test_auto_block_without_unit_keeps():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.8,
        computed_block_id="bloco-2", block_confidence=0.9, block_unit_slug="",
    )
    assert unit == "unidade-1"
    assert reasons == [] and conflict == {}


def test_auto_empty_unit_inherits_from_block():
    unit, reasons, conflict = _call(
        computed_unit_slug="", unit_confidence=0.0,
        computed_block_id="bloco-2", block_confidence=0.6, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == ["herdada_do_bloco=bloco-2"]
    assert conflict == {}


def test_auto_agree_keeps():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-2", unit_confidence=0.8,
        computed_block_id="bloco-2", block_confidence=0.6, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == [] and conflict == {}


def test_auto_disagree_block_stronger_reconciles():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.66,
        computed_block_id="bloco-2", block_confidence=0.80, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == ["reconciliada_do_bloco=bloco-2"]
    assert conflict == {}


def test_auto_disagree_unit_stronger_flags_conflict():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.90,
        computed_block_id="bloco-2", block_confidence=0.55, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-1"
    assert reasons == []
    assert conflict == {"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-2"}
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_reconcile_unit_block.py -v`
Expected: FAIL (`ImportError: cannot import name 'reconcile_unit_with_block'`)

- [ ] **Step 3: Implementar o helper**

Em `src/builder/routing/file_map.py`, após `resolve_effective_block` (~linha 583). Confirme que `Tuple`, `List`, `Dict` estão importados de `typing` no topo (já são usados em outras assinaturas do módulo; se faltar algum, adicione ao import existente):

```python
def reconcile_unit_with_block(
    *,
    computed_unit_slug: str,
    unit_confidence: float,
    computed_block_id: str,
    block_confidence: float,
    block_unit_slug: str,
    block_is_manual: bool,
    has_manual_unit: bool,
) -> Tuple[str, List[str], Dict[str, str]]:
    """Reconcilia a unidade efetiva com o bloco atribuído (F1, spec linhas 36-52).

    Precedência:
      1. Bloco MANUAL com unidade -> unidade do bloco (autoritativo, vence até
         manual_unit). reason "unidade_do_bloco_manual".
      2. manual_unit presente (sem bloco manual) -> mantém computed_unit_slug.
      3. Auto:
         - sem bloco / bloco sem unidade -> mantém computed_unit_slug.
         - computed_unit_slug vazio -> herda do bloco ("herdada_do_bloco=<id>").
         - concordam -> mantém.
         - discordam: block_confidence >= unit_confidence -> unidade do bloco
           ("reconciliada_do_bloco=<id>"); senão mantém a unidade forte e devolve
           conflict {unit, block_unit, block_id}.

    conflict é {} exceto no último caso (unidade forte venceu bloco discordante).
    """
    if block_is_manual and block_unit_slug:
        return block_unit_slug, ["unidade_do_bloco_manual"], {}
    if has_manual_unit:
        return computed_unit_slug, [], {}
    if not computed_block_id or not block_unit_slug:
        return computed_unit_slug, [], {}
    if not computed_unit_slug:
        return block_unit_slug, [f"herdada_do_bloco={computed_block_id}"], {}
    if block_unit_slug == computed_unit_slug:
        return computed_unit_slug, [], {}
    if block_confidence >= unit_confidence:
        return block_unit_slug, [f"reconciliada_do_bloco={computed_block_id}"], {}
    return (
        computed_unit_slug,
        [],
        {"unit": computed_unit_slug, "block_unit": block_unit_slug, "block_id": computed_block_id},
    )
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_reconcile_unit_block.py -v`
Expected: PASS (8 testes)

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/file_map.py tests/test_reconcile_unit_block.py
git commit -m "feat(routing): reconcile_unit_with_block (regra unica F1)"
```

---

### Task 3: Ligar o helper no `resolve_unit_block_tags`

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py:1136-1146` (substituir herança) e `:1167-1176` (gravar conflito); import do helper
- Test: `tests/test_content_taxonomy.py` (estender; se não existir, criar)

**Contexto:** o bloco atual a substituir é exatamente:

```python
        # Herança de unidade pelo bloco: ...
        if not computed_unit_slug and computed_block_id and not manual_unit:
            _blocks = (timeline_context.get("timeline_index") or {}).get("blocks", []) or []
            _blk = next((b for b in _blocks if str(b.get("id") or "") == computed_block_id), None)
            _blk_unit = str((_blk or {}).get("unit_slug") or "").strip()
            if _blk_unit:
                computed_unit_slug = _blk_unit
                unit_reasons = list(unit_reasons) + [f"herdada_do_bloco={computed_block_id}"]
```

`manual_block` (dict ou None) já existe em escopo (:1056); `unit_confidence`,
`block_confidence`, `unit_reasons` também.

- [ ] **Step 1: Escrever o teste de integração que falha**

Em `tests/test_content_taxonomy.py` adicionar (ajuste imports/fixtures ao padrão do arquivo; a função sob teste é `resolve_unit_block_tags` — confira a assinatura real no módulo e os `*_fn` injetados, reusando qualquer helper de fixture já presente no arquivo de teste):

```python
def test_reconcile_conflict_unit_stronger_sets_flag(<fixtures do arquivo>):
    # entry: unit matcher forte (unidade-1) + bloco auto fraco apontando unidade-2
    # Esperado: computed_unit_slug == "unidade-1", unit_block_conflict preenchido,
    # tag unit:unidade-1 presente.
    ...
    assert out_entry["computed_unit_slug"] == "unidade-1"
    assert out_entry["unit_block_conflict"] == {
        "unit": "unidade-1", "block_unit": "unidade-2", "block_id": <id-do-bloco>
    }
    assert f"unit:unidade-1" in out_entry["auto_tags"]


def test_reconcile_manual_block_overrides_unit(<fixtures>):
    # entry com manual_timeline_block_id apontando bloco de unidade-2
    # Esperado: computed_unit_slug == "unidade-2"; sem conflito.
    ...
    assert out_entry["computed_unit_slug"] == "unidade-2"
    assert out_entry.get("unit_block_conflict", {}) == {}
```

> Nota ao implementador: monte `timeline_context["timeline_index"]["blocks"]`
> com blocos contendo `id`, `unit_slug`, `administrative_only=False`. Se o arquivo
> de teste já tiver um builder de `timeline_context`/`unit_index`, reuse-o. Se for
> custoso montar o caminho completo do scorer para forçar um bloco fraco, prefira
> testar a integração via o estado pós-`resolve_unit_block_tags` com um bloco
> manual (caminho determinístico) e cobrir o caso de discordância-auto no teste de
> unidade do helper (Task 2), deixando aqui ao menos o teste de bloco manual.

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_content_taxonomy.py -k reconcile -v`
Expected: FAIL (campo `unit_block_conflict` ausente / unidade não reconciliada)

- [ ] **Step 3: Adicionar o import do helper**

No topo de `content_taxonomy.py`, no import já existente de `src.builder.routing.file_map` (ou adicionar um), incluir `reconcile_unit_with_block`. Verifique como os outros `*_fn` de file_map chegam ao módulo — se forem injetados por parâmetro, mantenha o padrão; se houver import direto, use import direto.

- [ ] **Step 4: Substituir o bloco de herança pela chamada ao helper**

Trocar o bloco :1136-1146 (mostrado no contexto acima) por:

```python
        # Reconciliação unidade×bloco (F1): bloco manual é autoritativo; no auto,
        # bloco define a unidade só se block_confidence >= unit_confidence; senão
        # mantém a unidade forte e marca conflito. Absorve a herança (unit vazio).
        _blocks = (timeline_context.get("timeline_index") or {}).get("blocks", []) or []
        _blk = next((b for b in _blocks if str(b.get("id") or "") == computed_block_id), None)
        _blk_unit = str((_blk or {}).get("unit_slug") or "").strip()
        _reconciled_unit, _unit_reason_suffix, _unit_conflict = reconcile_unit_with_block(
            computed_unit_slug=computed_unit_slug,
            unit_confidence=float(unit_confidence),
            computed_block_id=computed_block_id,
            block_confidence=float(block_confidence),
            block_unit_slug=_blk_unit,
            block_is_manual=bool(manual_block),
            has_manual_unit=bool(manual_unit),
        )
        computed_unit_slug = _reconciled_unit
        if _unit_reason_suffix:
            unit_reasons = list(unit_reasons) + _unit_reason_suffix
```

- [ ] **Step 5: Gravar o conflito no entry**

No bloco de montagem do `new_entry` (:1165-1176), após `new_entry["unit_match_confidence"] = unit_confidence`, adicionar:

```python
        new_entry["unit_block_conflict"] = _unit_conflict
```

- [ ] **Step 6: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_content_taxonomy.py -v`
Expected: PASS

- [ ] **Step 7: Rodar a suíte do builder pra garantir nenhuma regressão**

Run: `python -m pytest -q`
Expected: PASS (sem regressão; a herança antiga continua coberta — agora via o helper)

- [ ] **Step 8: Commit**

```bash
git add src/builder/extraction/content_taxonomy.py tests/test_content_taxonomy.py
git commit -m "feat(taxonomy): liga reconcile_unit_with_block (auto com guarda + manual)"
```

---

### Task 4: Editor — origem, conflito e combo de unidade

**Files:**
- Modify: `src/ui/dialogs.py:4093-4145` (`_resolve_backlog_unit_status`) e `:2322-2344` (combo "Unidade manual")

- [ ] **Step 1: Conflito + origem no `_resolve_backlog_unit_status`**

Em `_resolve_backlog_unit_status` (lê `entry_data`), antes do `return` final, derivar origem/observação dos novos sinais. Após calcular `manual_slug`/`current_unit_cell`, adicionar leitura de reasons e conflito e usá-los para enriquecer a observação no ramo automático (quando NÃO há `manual_slug`):

```python
    reasons = [str(r) for r in (entry_data.get("unit_match_reasons") or [])]
    conflict = entry_data.get("unit_block_conflict") or {}

    def _auto_source(default: str) -> str:
        if any(r == "unidade_do_bloco_manual" for r in reasons):
            return "Definida pelo bloco manual"
        if any(r.startswith("reconciliada_do_bloco=") for r in reasons):
            return "Reconciliada do bloco (auto)"
        if any(r.startswith("herdada_do_bloco=") for r in reasons):
            return "Herdada do bloco (auto)"
        return default

    def _conflict_note() -> str:
        if not conflict:
            return ""
        return (
            f" ⚠ Conflito: o bloco «{conflict.get('block_id', '')}» aponta a unidade "
            f"«{conflict.get('block_unit', '')}», mas o matcher escolheu "
            f"«{conflict.get('unit', '')}» (mais confiante). Revise."
        )
```

No ramo automático `if current_unit_cell:` (atual :4134-4139), trocar por:

```python
    if current_unit_cell:
        return {
            "assigned": current_unit_cell,
            "source": _auto_source("FILE_MAP atual"),
            "note": "Unidade atribuída automaticamente com base no FILE_MAP gerado no último processamento." + _conflict_note(),
        }
```

(Os ramos de `manual_slug` ficam como estão — override de unidade explícito não
tem conflito a sinalizar.)

- [ ] **Step 2: Desabilitar combo de unidade quando há bloco manual**

No trecho do combo "Unidade manual" (:2322-2344), após criar `unit_combo`, quando
`self._data.get("manual_timeline_block_id")` estiver preenchido, desabilitar e
anotar. Localizar o `unit_combo.grid(...)` (~:2344) e logo após o bloco
`if len(unit_labels) > 1:` adicionar:

```python
            if str(self._data.get("manual_timeline_block_id") or "").strip():
                unit_combo.configure(state="disabled")
                tk.Label(
                    tab_edit,
                    text="Unidade definida pelo bloco manual — limpe o bloco para editar a unidade.",
                    bg=p["bg"], fg=p["muted"], font=("Segoe UI", 8),
                    wraplength=520, justify="left",
                ).grid(row=row_unit + 0, column=1, sticky="sw", pady=(0, 0))
```

> Nota ao implementador: se a label extra colidir no grid com o combo (mesma
> célula row_unit/col 1), em vez da label use `add_tooltip(unit_combo, "...")`
> (helper em `dialogs.py:105`) para não mexer no layout. Escolha a opção que não
> introduz colisão (verifique no Step 3).

- [ ] **Step 3: Verificar sintaxe e ausência de colisão de grid**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py', encoding='utf-8').read())"`
Expected: sem erro.
Inspeção: nenhuma nova célula `(row, column)` duplicada na aba de edição.

- [ ] **Step 4: Suíte completa**

Run: `python -m pytest -q`
Expected: PASS (sem regressão; editor sem unit test).

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): editor mostra origem/conflito da unidade e trava combo sob bloco manual"
```

---

### Task 5: Editor — aviso de subunidade órfã

**Files:**
- Modify: `src/ui/dialogs.py` — novo loader `_load_subunit_unit_map` (perto de `_load_subunit_options`, ~:4440) e uso em `_resolve_backlog_subunit_status` (:4148-4199)
- Test: `tests/test_subunit_unit_map.py` (criar — o loader é testável de forma isolada via parsing de texto do plano)

- [ ] **Step 1: Teste do mapa subunit→unidade que falha**

Criar `tests/test_subunit_unit_map.py`. O loader recebe um `repo_dir`, mas a
lógica de parsing pode ser extraída numa função pura `_subunit_unit_map_from_plan(plan_text, unit_label_to_slug)`
testável sem disco. Estruturar assim:

```python
from src.ui.dialogs import _subunit_unit_map_from_plan


def test_maps_each_topic_to_its_unit():
    plan = (
        "## Unidade 1 — Limites\n"
        "- 1.1 Noção de limite\n"
        "- 1.2 Continuidade\n"
        "## Unidade 2 — Derivadas\n"
        "- 2.1 Regra da cadeia\n"
    )
    unit_label_to_slug = {"Unidade 1 — Limites": "unidade-1", "Unidade 2 — Derivadas": "unidade-2"}
    out = _subunit_unit_map_from_plan(plan, unit_label_to_slug)
    assert out.get("nocao-de-limite") == "unidade-1"
    assert out.get("continuidade") == "unidade-1"
    assert out.get("regra-da-cadeia") == "unidade-2"
```

> Nota: ajuste o texto do plano ao formato que `_parse_units_from_teaching_plan`
> realmente reconhece (leia a função antes de escrever o teste; use um exemplo que
> ela parseia). O ponto do teste é: cada subunit_slug mapeia para o unit_slug da
> sua unidade.

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_subunit_unit_map.py -v`
Expected: FAIL (`ImportError: cannot import name '_subunit_unit_map_from_plan'`)

- [ ] **Step 3: Implementar o parser puro + loader**

Perto de `_load_subunit_options` (`dialogs.py:4440`), adicionar a função pura e o
loader que a alimenta com as fontes (COURSE_MAP / teaching_plan), reusando
`_parse_units_from_teaching_plan` e `slugify` (já importados):

```python
def _subunit_unit_map_from_plan(plan_text: str, unit_label_to_slug: Dict[str, str]) -> Dict[str, str]:
    """subunit_slug -> unit_slug, a partir do texto do plano. O unit_slug vem de
    unit_label_to_slug (título da unidade -> slug canônico); títulos sem slug
    conhecido caem para slugify(título)."""
    out: Dict[str, str] = {}
    for unit_title, topics in _parse_units_from_teaching_plan(plan_text):
        unit_slug = unit_label_to_slug.get(unit_title) or slugify(unit_title)
        if not unit_slug:
            continue
        for topic_item in topics or []:
            raw = topic_item[0] if isinstance(topic_item, (list, tuple)) else str(topic_item)
            label = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", (raw or "").strip()).strip()
            slug = slugify(label)
            if slug and slug not in out:
                out[slug] = unit_slug
    return out


def _load_subunit_unit_map(repo_dir: Optional[Path]) -> Dict[str, str]:
    """Carrega subunit_slug -> unit_slug das mesmas fontes de _load_subunit_options."""
    if not repo_dir:
        return {}
    unit_label_to_slug = {label: slug for label, slug in _load_file_map_unit_options(repo_dir)}
    course_map_path = repo_dir / "course" / "COURSE_MAP.md"
    if course_map_path.exists():
        try:
            return _subunit_unit_map_from_plan(course_map_path.read_text(encoding="utf-8"), unit_label_to_slug)
        except Exception:
            return {}
    return {}
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_subunit_unit_map.py -v`
Expected: PASS

- [ ] **Step 5: Avisar órfão em `_resolve_backlog_subunit_status`**

A função precisa da unidade efetiva do bloco. Passar dois novos parâmetros
opcionais (`subunit_unit_map`, `block_unit_slug`) e, no ramo `manual_slug`,
acrescentar à nota quando a subunidade manual pertencer a outra unidade:

Assinatura (:4148):
```python
def _resolve_backlog_subunit_status(
    entry_data: dict,
    repo_dir: Optional[Path],
    label_by_slug: Optional[Dict[str, str]] = None,
    subunit_unit_map: Optional[Dict[str, str]] = None,
    block_unit_slug: str = "",
) -> Dict[str, str]:
```

No ramo `if manual_slug:` (após montar `note`), antes do `return`:
```python
        sub_unit = (subunit_unit_map or {}).get(manual_slug, "")
        if block_unit_slug and sub_unit and sub_unit != block_unit_slug:
            note += (
                f" ⚠ A subunidade pertence à unidade «{sub_unit}», diferente da "
                f"unidade «{block_unit_slug}» do bloco. Revise."
            )
```

No call site de `_resolve_backlog_subunit_status` (dentro de `_build_ui`, onde
`subunit_status = _resolve_backlog_subunit_status(...)` é chamado, ~:2445),
passar os novos argumentos. A unidade efetiva do bloco vem do timeline status já
calculado / do `manual_timeline_block_id` resolvido; reusar
`self._manual_timeline_label_by_id`/options para obter o `unit_slug` do bloco
efetivo, ou derivar de `_resolve_backlog_timeline_status`. Carregar o mapa uma vez:
```python
        self._subunit_unit_map = _load_subunit_unit_map(self._repo_dir)
```
e passar `subunit_unit_map=self._subunit_unit_map, block_unit_slug=<unit do bloco efetivo>`.

> Nota ao implementador: se obter o `unit_slug` do bloco efetivo no editor for
> custoso (exige resolver o bloco), use a unidade já exibida no painel de unidade
> (a unidade efetiva reconciliada) como `block_unit_slug` — o objetivo do aviso é
> só detectar incoerência subunidade↔unidade efetiva. Garanta que nenhum dado é
> alterado; é só texto na observação.

- [ ] **Step 6: Verificar sintaxe + suíte**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py', encoding='utf-8').read())"` e `python -m pytest -q`
Expected: sem erro; PASS.

- [ ] **Step 7: Commit**

```bash
git add src/ui/dialogs.py tests/test_subunit_unit_map.py
git commit -m "feat(ui): aviso de subunidade orfa (unidade != unidade do bloco)"
```

---

## Self-Review

- **Spec coverage:** Task 1 = §3 (campo); Task 2 = §1 (helper) + §Testes(helper);
  Task 3 = §2 (ligação) + §Testes(integração); Task 4 = §4 (editor unidade/combo);
  Task 5 = §5 (aviso órfão) + loader subunit→unidade. Não-objetivos respeitados
  (não toca `resolve_effective_block`/scorer/gates; não limpa subunidade; mantém
  `manual_unit_slug`).
- **Placeholder scan:** os pontos marcados "Nota ao implementador" são decisões de
  layout/fixture com caminho concreto + fallback explícito, não TODOs vagos. Código
  do helper, do campo e da ligação está completo e literal.
- **Type consistency:** `reconcile_unit_with_block(...)` mesma assinatura nas Tasks
  2 e 3; retorno `(str, List[str], Dict[str,str])` consistente; `unit_block_conflict`
  é `dict` (default `{}`) na Task 1 e gravado como dict na Task 3; chaves do conflito
  (`unit`/`block_unit`/`block_id`) idênticas em helper, gravação e display.
- **Ordem de execução:** Task 2 antes da 3 (helper existe antes da ligação); Task 1
  antes da 3 (campo existe antes de gravar). 4 e 5 só dependem de 1-3.
