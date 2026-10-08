# Reconciliar unidade × bloco — Design (F1)

date: 2026-06-11
origem: análise do subsistema de atribuição do editor de backlog (F1)
status: aprovado para plano

## Objetivo

Hoje a unidade (`computed_unit_slug`, gate 0.65) e o bloco temporal
(`computed_block_id`, gate 0.50) são computados **independentes** em
`resolve_unit_block_tags`. Quando discordam (bloco aponta uma unidade ≠ da que o
matcher de unidade escolheu), as tags `unit:` e `bloco:` se contradizem — e nada
reconcilia. Como um bloco ∈ uma unidade, o bloco é o sinal mais específico.

Intenção do projeto: **auto é o caminho principal e deve ser preciso**; o manual
é rede de correção pra quando o aluno revê o backlog e acha erro. Esta mudança
torna a atribuição auto coerente (unidade derivada do bloco quando faz sentido) e
faz o override manual de bloco ser autoritativo da unidade.

## Decisões (do brainstorming)

- **Manual**: bloco manual escolhido ⇒ unidade vem dele. Autoritativo, sem
  guarda (escolha humana explícita), vence inclusive `manual_unit_slug`.
- **Auto, com guarda**: havendo bloco auto, a unidade deriva do bloco **só se**
  `computed_block_confidence ≥ unit_match_confidence`; senão mantém a unidade
  forte e **marca conflito** pra revisão.
- Unit-sem-bloco continua possível (raro): `manual_unit_slug` permanece no modelo
  e vale quando não há bloco.
- Subunidade órfã (de outra unidade que a do bloco): **só avisa** no editor, não
  mexe em dado.
- Auto path do **bloco** em si (`resolve_effective_block`, scorer) **não muda**.

## Contexto verificado (file:line)

- `resolve_unit_block_tags` (`src/builder/extraction/content_taxonomy.py:996-1178`):
  - `manual_unit` lido em :1029-1034 → `resolved_unit_slug`, `unit_confidence=1.0`.
  - `manual_block = resolve_entry_manual_timeline_block_fn(...)` em :1056 (dict do
    bloco ou None); auto block resolvido em :1060-1122; `block_confidence` em :1134.
  - `computed_unit_slug = resolved_unit_slug if (not unit_ambiguous and unit_confidence >= 0.65) else ""` (:1132).
  - **Reconciliação parcial JÁ EXISTE** em :1136-1146 ("Herança de unidade pelo
    bloco"): quando `computed_unit_slug` vazio + há bloco com unidade + sem
    `manual_unit` → herda `block.unit_slug`. **Não trata o caso de discordância**
    (unidade decidiu ≥0.65 e bloco aponta outra). Este é o gap.
  - Campos gravados em :1167-1175 (`computed_unit_slug`, `unit_match_reasons`,
    `unit_match_confidence`, etc.).
- `resolve_effective_block` / `resolve_entry_manual_timeline_block` /
  `resolve_entry_manual_unit_slug` em `src/builder/routing/file_map.py:476-583`
  (onde vive a precedência de bloco; lugar natural do helper novo).
- Editor: `_resolve_backlog_unit_status` (`dialogs.py:4093-4145`),
  `_resolve_backlog_subunit_status` (:4148-4199),
  `_resolve_backlog_timeline_status` (:4202-4359). Combo "Unidade manual" e painel
  em :2322-2408.
- `_load_subunit_options` (`dialogs.py:4440-4486`) achata tópicos e **descarta** o
  vínculo unidade↔tópico — `_parse_units_from_teaching_plan` devolve
  `(unit_title, topics)`, mas o loader joga `unit_title` fora. Pro aviso órfão é
  preciso um mapa novo subunit→unidade.

## Mudanças

### 1. Helper puro `reconcile_unit_with_block` (`src/builder/routing/file_map.py`)

Irmão de `resolve_effective_block`. Centraliza a regra (absorve a herança
existente + os casos novos). Retorna `(unit_slug, reason_suffix, conflict)`:

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
    """Reconcilia a unidade efetiva com o bloco atribuído (F1).

    Precedência:
      1. Bloco MANUAL com unidade -> unidade do bloco (autoritativo, vence até
         manual_unit). reason "unidade_do_bloco_manual".
      2. manual_unit presente -> mantém computed_unit_slug (já é o manual).
      3. Auto:
         - sem bloco / bloco sem unidade -> mantém computed_unit_slug.
         - computed_unit_slug vazio -> herda do bloco (caso já existente).
           reason "herdada_do_bloco=<id>".
         - concordam -> mantém.
         - discordam: se block_confidence >= unit_confidence -> unidade do bloco
           (reason "reconciliada_do_bloco=<id>"); senão mantém a unidade forte e
           devolve conflict {unit, block_unit, block_id} pra revisão.

    conflict é {} exceto no último caso (unidade forte venceu um bloco discordante).
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

### 2. Ligação no `resolve_unit_block_tags` (`content_taxonomy.py`)

Substituir o bloco de herança :1136-1146 por uma chamada ao helper, **depois** de
`computed_unit_slug`/`computed_block_id`/`computed_block_confidence` definidos
(:1132-1134). Lookup do `block_unit_slug` reusa a busca já existente (`_blk`):

```python
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
    if _reconciled_unit != computed_unit_slug:
        computed_unit_slug = _reconciled_unit
    if _unit_reason_suffix:
        unit_reasons = list(unit_reasons) + _unit_reason_suffix
```

`computed_block_band` continua derivado depois (intocado). Gravar o conflito no
entry (:1165-1176), espelhando o padrão de `latex_corruption` (dict, omitido
quando vazio via `to_dict`):

```python
    new_entry["unit_block_conflict"] = _unit_conflict
```

### 3. Campo novo no FileEntry (`src/models/core.py`)

Após os campos de match (após :101 `source_section`):

```python
    # Conflito unidade×bloco detectado no auto (F1): a unidade forte (>=0.65)
    # venceu um bloco que apontava OUTRA unidade (block_confidence < unit_conf).
    # {} quando não há conflito. Sinal de revisão exibido no editor; o build
    # mantém a unidade forte. Distinto da herança silenciosa (que não é conflito).
    unit_block_conflict: dict = field(default_factory=dict)
```

`to_dict` omite `{}`; `from_dict` filtra. Round-trip livre.

### 4. Editor — refletir reconciliação + conflito (`src/ui/dialogs.py`)

`_resolve_backlog_unit_status` passa a derivar de uma única fonte coerente com o
manifest reconciliado:
- **Unidade atribuída**: a unidade efetiva (já reconciliada no manifest —
  `computed_unit_slug` / tag `unit:`).
- **Origem**: "manual" (override de unidade), "definida pelo bloco manual",
  "reconciliada do bloco", "herdada do bloco", ou "matcher de unidade".
- **Observação**: se `unit_block_conflict` não vazio → aviso
  "Auto: bloco «{block_id}» aponta unidade «{block_unit}», mas o matcher de
  unidade escolheu «{unit}» (mais confiante). Revise.".

Combo "Unidade manual" (:2322-2344): quando há `manual_timeline_block_id`
resolvido, **desabilitar** (`state="disabled"`) com nota muted "Unidade definida
pelo bloco manual — limpe o bloco para editar a unidade.". Sem bloco manual:
funciona como hoje.

### 5. Editor — aviso de subunidade órfã (`src/ui/dialogs.py`)

Loader novo `_load_subunit_unit_map(repo_dir) -> dict[str, str]` (subunit_slug →
unit_slug), derivado de `_parse_units_from_teaching_plan` (que já dá
`(unit_title, topics)`) + mapa unit_title→unit_slug das opções de unidade
(`_load_file_map_unit_options`, cujo label é o título da unidade). Em
`_resolve_backlog_subunit_status`, quando há bloco efetivo e `manual_subunit_slug`
mapeia pra uma unidade ≠ da unidade do bloco → acrescenta à observação:
"Subunidade «{sub}» pertence à unidade «{sub_unit}», diferente da unidade «{blk_unit}»
do bloco. Revise.". Só texto; nenhum dado é alterado.

## Não-objetivos

- Não alterar `resolve_effective_block` nem o scorer de bloco.
- Não limpar subunidade automaticamente.
- Não mexer no subunit matching nem nos gates (unit 0.65 / block 0.50 / subunit 0.60).
- Não remover `manual_unit_slug` (caso raro unit-sem-bloco).
- Limpeza visual da aba (esconder campos vazios, compactar dump do bloco,
  deduplicar painéis) é a fase seguinte (F2/F4), não esta.

## Testes

`tests/test_reconcile_unit_block.py` (novo) — helper puro:
- bloco manual com unidade → vence inclusive `has_manual_unit=True`.
- `has_manual_unit` sem bloco manual → mantém.
- auto sem bloco / bloco sem unidade → mantém.
- auto, `computed_unit_slug` vazio → herda do bloco (reason herdada).
- auto, concordam → mantém, sem conflito.
- auto, discordam, `block_conf ≥ unit_conf` → unidade do bloco (reason reconciliada).
- auto, discordam, `block_conf < unit_conf` → mantém unidade forte + conflict
  preenchido com os 3 slugs.

`tests/test_content_taxonomy.py` (ou equivalente existente) — integração:
- entry auto com unit forte + bloco discordante fraco → manifest mantém unit,
  grava `unit_block_conflict`, tag `unit:` = unidade forte.
- entry com bloco manual de outra unidade → `computed_unit_slug` = unidade do
  bloco; sem conflito.

`tests/test_core.py` — round-trip de `unit_block_conflict` (default `{}` não
emitido; preenchido preserva).

Editor (dialogs): sem unit test (widgets); validação por revisão de código.
