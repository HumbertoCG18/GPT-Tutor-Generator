# Guard de conflito: override manual vs auto-atribuição (cronograma)

> Design doc. Aprovado em 2026-06-06.

## Goal

Sinalizar (e facilitar reverter) quando um **override manual** de bloco do
cronograma contradiz um sinal de **auto-atribuição forte** — para que overrides
errados parem de persistir silenciosamente e contaminar as tags das materials.

Motivador real (TCC): `.timeline_curation.json` tinha
`bloco-02 → manual_unit_slug: unidade-02-turing`, mas o auto atribui
`unidade-01-conjuntos-enumeraveis` com confiança 1.0. Override manual sempre
vence (por design), então o bloco "Conjuntos Enumeráveis" ficava marcado unidade
2, e a material assignada a ele herdava a tag errada. Nada no sistema avisava do
conflito.

## Contexto (estado atual)

- Overrides de bloco vivem em `course/.timeline_curation.json`
  (`manual_unit_slug`, `manual_kind_override`, `manual_topic_label`), escritos só
  pelo tab Cronograma (`timeline_dashboard.py` → `set_block_override`).
- `_apply_curation_overrides` (em `src/builder/timeline/index.py`) injeta
  `manual_unit_slug` como `block_manual_unit_slug` no bloco (rename p/ não colidir
  com o `FileEntry.manual_unit_slug` entry-level do manifest).
- Serialização (`.timeline_index.json`) carrega por bloco: `block_manual_unit_slug`,
  `manual_kind_override`, `source_kind` (Atividade/cor do SARC),
  `primary_topic_confidence`, `topic_ambiguous`, `topic_candidates[]`
  (cada um com `unit_slug`/`score`). Confirmado nos dados do TCC.
- Auto-atribuição de unidade no build (`index.py`): topic-derive roda quando
  `primary_topic.confidence >= 0.65 and not ambiguous`. Esse é o gate que define
  "o auto teria decidido".
- Auto-classificação de kind: `classify_block` honra `manual_kind_override` >
  `source_kind` (SARC) > texto/sessão.
- Health report do cronograma: `scripts/validate_timeline.py`
  (`health_report`/`gate_failures`) + artefato `CRONOGRAMA_HEALTH.md`
  (`src/builder/artifacts/cronograma_health.py`).

## Decisões (do brainstorming)

- **Limiar unidade:** sinaliza quando o auto **teria decidido** (topic
  `confidence >= 0.65`, não-ambíguo) e diverge do override. Pega o bloco-02
  (conf 1.0); NÃO pega overrides legítimos (bloco-10/11/12, onde o auto abstém).
- **Limiar kind:** sinaliza só quando `manual_kind_override` diverge do
  `source_kind` (SARC autoritativo). Auto-kind por texto é fraco e seu override é
  legítimo (ex.: class→review) → não sinaliza. Baixo ruído.
- **Superfície:** health-check (CRONOGRAMA_HEALTH.md + warning no report) **e**
  aviso no tab Cronograma com sugestão do auto + botão "reverter p/ auto".
- **Comportamento:** só **warning** + revert manual. Override segue vencendo
  funcionalmente; nada é auto-revertido. Conflito **não** é falha dura de gate.
- **Decomposição:** 2 planos — backend (detecção + health-check) e UI (tab).

## Arquitetura

Uma camada de **detecção pura** opera sobre blocos serializados (campos já no
`.timeline_index.json`), sem recomputar taxonomia. Dois consumidores read-only:
o health report e o tab Cronograma. A função do guard é **tornar conflitos
visíveis e reversíveis**, não mudar a precedência.

---

## PARTE A — Backend (Plano 1)

### A1. Módulo de detecção `src/builder/timeline/conflicts.py` (novo)

Constante: `UNIT_AUTO_MIN_CONFIDENCE = 0.65` (espelha o gate de topic-derive).

```python
def auto_suggested_unit(block: Mapping) -> tuple[str, float]:
    """(unit_slug, confidence) que o auto atribuiria, ignorando override.

    Espelha o gate de topic-derive do build: so sugere quando o topico primario
    e confiante o bastante e nao-ambiguo. Senao ("", 0.0).
    """
    if block.get("topic_ambiguous"):
        return ("", 0.0)
    conf = float(block.get("primary_topic_confidence") or 0.0)
    if conf < UNIT_AUTO_MIN_CONFIDENCE:
        return ("", 0.0)
    candidates = block.get("topic_candidates") or []
    if not candidates:
        return ("", 0.0)
    unit = str((candidates[0] or {}).get("unit_slug") or "")
    return (unit, conf) if unit else ("", 0.0)
```

```python
def detect_block_conflicts(block: Mapping) -> list[dict]:
    """Lista de conflitos override-vs-auto de UM bloco (unit e kind)."""
    out = []
    manual_unit = str(block.get("block_manual_unit_slug") or "").strip()
    if manual_unit:
        auto_unit, conf = auto_suggested_unit(block)
        if auto_unit and _norm_unit(auto_unit) != _norm_unit(manual_unit):
            out.append({
                "block_id": str(block.get("id") or ""),
                "field": "unit",
                "manual": manual_unit,
                "auto": auto_unit,
                "confidence": conf,
            })
    manual_kind = str(block.get("manual_kind_override") or "").strip()
    source_kind = str(block.get("source_kind") or "").strip()
    if manual_kind and source_kind and manual_kind != source_kind:
        out.append({
            "block_id": str(block.get("id") or ""),
            "field": "kind",
            "manual": manual_kind,
            "auto": source_kind,
            "confidence": 1.0,
        })
    return out
```

```python
def detect_timeline_conflicts(blocks: Iterable[Mapping]) -> list[dict]:
    """Achata detect_block_conflicts sobre todos os blocos."""
    result = []
    for block in blocks or []:
        if isinstance(block, Mapping):
            result.extend(detect_block_conflicts(block))
    return result
```

`_norm_unit` reusa a normalização de slug de unidade já existente
(`_normalize_unit_slug` de `extraction/teaching_plan.py` ou equivalente) para
comparar `unidade-02-turing-computabilidade` vs variações. Importar a função
canônica em vez de reimplementar (DRY).

### A2. Integração no health report (`scripts/validate_timeline.py`)

- `health_report(blocks)` ganha a chave `override_conflicts`: lista de
  `detect_timeline_conflicts(blocks)`.
- `gate_failures(report)` **não** vira falha dura por conflito (override é
  legítimo). Em vez disso, expor a contagem para o report textual. (Se já houver
  uma noção de "warnings" separada de "gate failures", adicionar lá; senão,
  apenas a chave `override_conflicts` no report, consumida pelo artefato A3.)

### A3. Render em `CRONOGRAMA_HEALTH.md` (`src/builder/artifacts/cronograma_health.py`)

- Nova seção "Conflitos de curadoria" quando houver conflitos. Para cada
  conflito: `block_id` + `period_label` (lookup pelo id) + campo (unidade/kind) +
  `manual` vs `auto` + confiança. Ex.:
  `⚠️ bloco-02 (04/03/2026) unidade: manual unidade-02-turing ≠ auto unidade-01-conjuntos (100%)`.
- Sem conflitos: linha curta "_Nenhum conflito de curadoria._" (consistente com
  os estados vazios já adotados nos MDs do tutor).

### A4. Testes (TDD, `tests/test_curation_conflicts.py` novo)

- `auto_suggested_unit`: bloco com `topic_ambiguous=True` → `("",0)`; conf<0.65 →
  `("",0)`; conf 1.0 não-ambíguo com candidato unidade-01 → `("unidade-01...",1.0)`.
- `detect_block_conflicts` unidade: bloco estilo TCC bloco-02 (manual unidade-02,
  candidato unidade-01 conf 1.0) → 1 conflito unit; bloco com manual unidade-03 e
  `topic_ambiguous=True` (estilo bloco-10) → 0 conflitos.
- `detect_block_conflicts` kind: `manual_kind_override="holiday"` +
  `source_kind="assessment"` → 1 conflito kind; `manual_kind_override="review"`
  sem `source_kind` (estilo bloco-05) → 0 conflitos; manual==source_kind → 0.
- `detect_timeline_conflicts`: lista de blocos mistos → só os conflitos.
- health report: `health_report` inclui `override_conflicts` com o conflito.
- CRONOGRAMA_HEALTH render: contém a seção e a linha do conflito quando há; frase
  de vazio quando não há.

---

## PARTE B — UI (Plano 2)

### B1. Aviso por linha no tab Cronograma (`src/ui/timeline_dashboard.py`)

- Helper puro `block_conflict_label(block) -> Optional[str]`: usa
  `detect_block_conflicts(block)`; retorna texto curto p/ exibir
  (ex.: `auto: unidade-01-conjuntos (100%)`) ou `None`. Testável sem Tk.
- Na renderização do bloco: se houver conflito, marcador 🔴 + a nota do auto ao
  lado do dropdown do campo em conflito.

### B2. Ação "reverter p/ auto"

- Botão por override em conflito. Ao clicar:
  - unidade: `save_block_unit_override(course_dir, block_id, None)` (limpa).
  - kind: `save_block_kind_override(course_dir, block_id, None)` (limpa).
  - Em seguida `enqueue_reprocess_fn()` (já injetado no dashboard) p/ o auto
    re-derivar no próximo build.
- Confirmação leve (messagebox) antes de limpar, já que altera curadoria.

### B3. Testes UI

- `block_conflict_label`: mesmos casos de A4 reduzidos ao texto; sem conflito →
  `None`. (O `grid`/widget Tk não é testado por automação.)

---

## Fora de escopo

- Auto-reverter overrides (só warning + revert manual).
- Detectar auto-atribuição errada **sem** override (sem ground-truth não dá).
- Conflito de override **entry-level** de material (`FileEntry.manual_unit_slug`
  no manifest) — o guard de bloco já cobre a fonte da propagação das tags.
- Recomputar taxonomia no health-check (a detecção usa só campos já gravados).

## Riscos

- Índices stale sem `source_kind` (gerados antes do backend SARC) não disparam
  conflito de kind — degrada em silêncio até regenerar. Aceitável (o conflito de
  unidade, que motivou tudo, independe de `source_kind`).
- `topic_candidates[0]` assume ordenação por score desc (garantida pelo build);
  se vazio, `auto_suggested_unit` abstém (sem falso positivo).
