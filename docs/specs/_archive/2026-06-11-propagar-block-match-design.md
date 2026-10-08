# Propagar method/confiança do match de código — Design

date: 2026-06-11
origem: auditoria "info gerada mas não propagada" (gap real verificado)
status: aprovado para plano

## Objetivo

`block_match_confidence` e `block_match_method` são computados pelo code
summarizer (Gemini + matcher local) em `code_summarization.py:382-383` e gravados
em `code_curation.json`, mas **nada os consome** downstream (grep confirma: só
escrita; `codes_panel.py` só *seta* "manual", nunca lê). Propagar para o manifest
e exibir no editor de backlog — espelhando o #4 (match_rationale).

## Contexto verificado (file:line)

- Produtor: `src/builder/core/code_summarization.py:382-383`
  (`summary_dict["block_match_confidence"] = round(conf, 3)`,
  `summary_dict["block_match_method"] = method`). `method` ∈
  {consensus, llm_only, auto_concept, orphan} (de `_consolidate_assignment`).
- Ponto único de propagação (já existe): `attach_block_rationale`
  (`src/builder/ops/pedagogical_regeneration.py:115-127`) — lê
  `summary.match_rationale` e grava `computed_block_rationale`, com `pop` quando
  ausente (anti-stale). Chamado em `regenerate_pedagogical_files` (ponto de
  convergência dos dois caminhos de build).
- FileEntry: `src/models/core.py:90` tem `computed_block_rationale`. Já existe
  `computed_block_confidence` (linha 83) com semântica DIFERENTE (confiança do
  routing/`resolve_unit_block_tags`), por isso o campo novo usa nome distinto.
- Editor: `src/ui/dialogs.py:2268-2280` tem o campo read-only "Por que este
  bloco?" (lê `computed_block_rationale`, fallback "—", tooltip). `add_tooltip`
  em `dialogs.py:105`. Linhas encadeiam relativamente (`row_rationale`,
  `row_unit = row_rationale + 1`).

## Mudanças

### 1. FileEntry (`src/models/core.py`)

Após `computed_block_rationale` (linha 90), adicionar:

```python
    # Método e confiança do match code->bloco, do code summarizer (Gemini +
    # matcher local). Copiados de code_curation.json (summary.block_match_method
    # / block_match_confidence) na regeneração pedagógica; default vazio/0.0 para
    # entries sem summary (não-código). Distinto de computed_block_confidence
    # (acima), que é a confiança do routing determinístico.
    computed_block_method: str = ""
    computed_block_match_confidence: float = 0.0
```

`to_dict` emite só não-default (string vazia / 0.0 não poluem o manifest);
`from_dict` filtra para campos conhecidos — round-trip livre.

### 2. Propagação (`src/builder/ops/pedagogical_regeneration.py`)

Renomear `attach_block_rationale` → `attach_block_summary_fields` (passa a
carregar 3 campos) e estender para copiar os 3, com o mesmo padrão anti-stale
(`pop` quando ausente). Atualizar o call site em `regenerate_pedagogical_files`.

```python
def attach_block_summary_fields(entries: list, code_curation: dict) -> list:
    """Sincroniza campos do code_curation (summary.*) com o entry dict:
    match_rationale -> computed_block_rationale,
    block_match_method -> computed_block_method,
    block_match_confidence -> computed_block_match_confidence.
    Sem valor na curation, remove o campo — evita dado stale após
    prune/reatribuição."""
    curation_entries = (code_curation or {}).get("entries", {})
    for e in entries:
        rec = curation_entries.get(str(e.get("id") or "")) or {}
        summary = rec.get("summary") or {}

        rationale = str(summary.get("match_rationale") or "").strip()
        if rationale:
            e["computed_block_rationale"] = rationale
        else:
            e.pop("computed_block_rationale", None)

        method = str(summary.get("block_match_method") or "").strip()
        if method:
            e["computed_block_method"] = method
        else:
            e.pop("computed_block_method", None)

        conf = summary.get("block_match_confidence")
        if conf is not None:
            try:
                e["computed_block_match_confidence"] = float(conf)
            except (TypeError, ValueError):
                e.pop("computed_block_match_confidence", None)
        else:
            e.pop("computed_block_match_confidence", None)

    return entries
```

Call site: trocar `attach_block_rationale(...)` por
`attach_block_summary_fields(...)` (mesma assinatura/args).

### 3. Editor de backlog (`src/ui/dialogs.py`)

Após o bloco "Por que este bloco?" (`row_rationale`, ~2268-2280) e antes de
`row_unit`, inserir um campo read-only "Match do bloco":

- `row_match = row_rationale + 1`
- valor: monta string a partir de `computed_block_method` e
  `computed_block_match_confidence`:
  - método vazio → "—"
  - senão → `f"método: {metodo} · confiança: {conf:.2f}"` (conf de
    `self._data.get("computed_block_match_confidence") or 0.0`).
- label "Match do bloco", valor muted, `wraplength=520`, mesmo estilo do campo de
  rationale.
- tooltip: "Como o bloco do cronograma foi escolhido para este código:\n"
  "consensus = Gemini e matcher local concordam; llm_only = só o Gemini;\n"
  "auto_concept = fallback por conceito; orphan = sem bloco.\n"
  "'—' quando não há summary (arquivo não-código)."
- ajustar a linha seguinte: `row_unit = row_match + 1` (encadeia relativo).

## Escopo (espelha o #4)

Manifest + editor apenas. **Não** propaga para tutor / FILE_MAP / CODE_INDEX
(orçamento de token do tutor; é sinal de curadoria, não de ensino).

## Não-objetivos

- Não tocar o produtor (`code_summarization.py`) — já grava corretamente.
- Não expor ao tutor nem em artefatos gerados para o tutor.
- Não unificar com `computed_block_confidence` (routing) — semânticas distintas.

## Testes (`tests/test_block_rationale.py`)

Estender o arquivo existente:
- `attach_block_summary_fields` copia os 3 campos quando presentes no summary.
- Remoção stale: entry com valores antigos + curation sem esses campos → todos
  os 3 removidos (`pop`).
- Confiança não-numérica no summary → campo removido (não quebra).
- Entry sem summary (não-código) → nenhum dos 3 campos presente.
- Atualizar referências ao nome antigo `attach_block_rationale` no teste.
