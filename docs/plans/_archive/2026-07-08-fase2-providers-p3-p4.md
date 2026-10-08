# FASE 2 — Providers P3 (SO data-no-nome) + P4 (TCC topic-bridge) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar janela ao SO (hoje 0% de cobertura de card-window) via data-no-nome DD.MM e ao TCC (hoje 26%, só pinos manuais) via topic-bridge do card "Semana N - Tópico", sem introduzir confiante-errado.

**Architecture:** Dois providers novos na cascata do `WindowProvider` (`P1 manual → P2 labels → P3 data → P4 topic`), ambos puros e READ-ONLY. P3 exige um gate D4 de concordância no fast-path janela-1 do `disambiguator` (data de POSTAGEM ≠ aula do conteúdo — 5 misses conhecidos no gold SO); band `alta` só com token discriminante global. Dois probes externos novos (`fase2_prova_SO/TCC.py`) medem os números do aceite spec §6.

**Tech Stack:** Python puro (stdlib `re`/`math`), pytest, artefatos gerados dos repos-tutor (`.timeline_index.json`, `.card_block_map.json`, `manifest.json`), golds `docs/reports/ground_truth_{SO,TCC}.csv`.

## Global Constraints

- Spec que governa: `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (§7 FASE 2, §6 aceite, §5 mapa).
- READ-ONLY nos repos-tutor (`~/Documents/GitHub/*-Tutor`) — probes NUNCA escrevem lá.
- Lógica nova SÓ em `src/builder/routing/motor/` e `scripts/`; NUNCA `engine.py`.
- PROIBIDO importar `block_token_weights`, `score_entry_against_timeline_block`, `select_probable_period_for_entry` no pacote do motor (guard AST `tests/test_motor_import_guard.py` — o extrator DD.MM é REIMPLEMENTADO puro, não importado do legado).
- PROIBIDO week-math ordinal-linear (F-TCC): o "N" de "Semana N - Tópico" NUNCA vira janela; só o TÓPICO.
- Invariante ANCHOR-ONLY: janela `[]` → funil-piso; material COM janela nunca escapa dela.
- `block_ref` = display id `bloco-NN`, não uuid.
- UTF-8 shim (`sys.stdout.reconfigure`) em todo script novo (console Windows cp1252).
- NÃO commitar sem pedido explícito do user (os steps de commit abaixo = pedir OK antes).
- PRÉ-GATE de medição (decisão user 2026-07-08): `python scripts/audit_gold_freshness.py` antes de qualquer medição contra ground_truth_* (já rodado hoje: 4 golds FRESCOS, 0 re-rotulagens).
- Regressão obrigatória ao fim de CADA task que toca o motor: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py` — ambos PASS exit 0 (baselines: acc 82.8%, contenção 0, confiante-errado ≤1, recall ≥0.900).
- Comandos de teste: `python -m pytest tests/test_motor_window_provider.py -q` (e afins); suite completa `python -m pytest tests -q` (1701 passed / 4 skipped hoje).

## Números pré-medidos (dry-run 2026-07-08, informam calibração)

| Medição | Valor | Implicação |
|---|---|---|
| SO: entries com DD.MM no título | 20/42 (48%) | cobertura P3 ≈ aceite ~45% ✓ |
| SO: datas de sessão → bloco | 40 datas, **0 colisões** | "data → exatamente 1 bloco" ✓ por construção |
| SO: P3 cru vs gold | **15 hit / 5 miss** | gate de concordância obrigatório |
| SO: os 5 misses | 2× `02.06`→bloco-12 (true 14), 2× `23.06`→bloco-16 (true 15), 1× `02.05`→data sem sessão (true 12) | data de POSTAGEM ≠ aula; janela-1 cega = 4 confiante-errado novos |
| TCC: P4 ingênuo (overlap ≥1 token `_toks`) nos 5 pinos | 3/5 contidos, 4/5 por interseção | "NP-completude" falha: `completude`≠`complete` → lever stem-prefix-6 |
| TCC: cobertura P4 ingênua | 20/27 (74%) | aceite >26% folgado; limiar pode apertar |
| Ano modal dos cursos | 2026 | derivar das sessions, nunca hardcode |

---

### Task 1: Extrator DD.MM puro (`extract_date_in_name`)

**Files:**
- Modify: `src/builder/routing/motor/window_provider.py`
- Test: `tests/test_motor_window_provider.py`

**Interfaces:**
- Consumes: nada novo (stdlib `re`).
- Produces: `extract_date_in_name(entry: dict) -> tuple[int, int] | None` — `(dd, mm)` do INÍCIO de `title`, `moodle_label` (dict `{"text":...}` ou str) ou basename de `source_path`; valida `1<=dd<=31`, `1<=mm<=12`. Task 2 consome.

- [ ] **Step 1: Escrever os testes que falham**

Adicionar ao FINAL de `tests/test_motor_window_provider.py`:

```python
class TestExtractDateInName:
    def test_title_com_ponto(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name({"title": "12.03 Processos"}) == (12, 3)

    def test_title_com_espaco(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name({"title": "14 04 Troca de Mensagens"}) == (14, 4)

    def test_mes_invalido_rejeitado(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        # "Integer Programming 00.01" -> dd=00 inválido; não é data
        assert extract_date_in_name({"title": "Integer Programming 00.01"}) is None
        assert extract_date_in_name({"title": "25.13 Coisa"}) is None

    def test_data_no_meio_do_titulo_nao_conta(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        # convenção SO = PREFIXO; data no meio é ruído (CS 4244 etc.)
        assert extract_date_in_name({"title": "Aula sobre 12.03 Processos"}) is None

    def test_fallback_moodle_label_e_source_path(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name(
            {"title": "Processos", "moodle_label": {"text": "21.05 Paginação"}}
        ) == (21, 5)
        assert extract_date_in_name(
            {"title": "x", "source_path": r"C:\stash\SO\02.06 Interrupção.pdf"}
        ) == (2, 6)

    def test_sem_data(self):
        from src.builder.routing.motor.window_provider import extract_date_in_name
        assert extract_date_in_name({"title": "Plano de Ensino"}) is None
        assert extract_date_in_name({}) is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_window_provider.py::TestExtractDateInName -q`
Expected: FAIL — `ImportError: cannot import name 'extract_date_in_name'`

- [ ] **Step 3: Implementar**

Em `src/builder/routing/motor/window_provider.py`, após os imports (adicionar `import re` no topo):

```python
# P3 — data-no-nome (spec §8: extrator DD.MM de title/moodle_label/source_path).
# Reimplementado PURO: o sinal DD.MM legado vive em símbolo condenado do cutover.
_DATE_PREFIX_RE = re.compile(r"^\s*(\d{1,2})[. ](\d{1,2})\b")


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def extract_date_in_name(entry: dict):
    """(dd, mm) do PREFIXO de title/moodle_label/basename(source_path); None se ausente."""
    basename = re.split(r"[\\/]", str(entry.get("source_path") or ""))[-1]
    for text in (str(entry.get("title") or ""), _moodle_label_text(entry), basename):
        m = _DATE_PREFIX_RE.match(text)
        if not m:
            continue
        dd, mm = int(m.group(1)), int(m.group(2))
        if 1 <= dd <= 31 and 1 <= mm <= 12:
            return dd, mm
    return None
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_motor_window_provider.py -q`
Expected: PASS (novos + existentes)

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add src/builder/routing/motor/window_provider.py tests/test_motor_window_provider.py
git commit -m "feat(motor): extrator DD.MM puro para o provider P3 (FASE 2)"
```

---

### Task 2: P3 `provider_date` + entrada na cascata

**Files:**
- Modify: `src/builder/routing/motor/window_provider.py`
- Modify: `src/builder/routing/motor/contracts.py` (docstring `AnchorDecision.provider`)
- Test: `tests/test_motor_window_provider.py`

**Interfaces:**
- Consumes: `extract_date_in_name` (Task 1); `MotorContext.blocks` (ordenados, com `sessions[].date` ISO).
- Produces: `provider_date(entry: dict, ctx: MotorContext) -> List[str]` — janela DISPLAY dos blocos cuja sessão cai na data (ano modal do curso); cascata `_CASCADE` ganha `(provider_date, "data")` após "labels". `resolve_window` pode agora retornar provider `"data"`.

- [ ] **Step 1: Escrever os testes que falham**

```python
def _ctx_com_datas():
    from src.builder.routing.motor.contracts import MotorContext
    blocks = [
        {"id": "bloco-01", "period_start": "2026-03-03",
         "sessions": [{"date": "2026-03-03", "label": "apresentacao"}]},
        {"id": "bloco-02", "period_start": "2026-03-10",
         "sessions": [{"date": "2026-03-10", "label": "processos"},
                      {"date": "2026-03-12", "label": "threads"}]},
    ]
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})


class TestProviderDate:
    def test_data_casa_sessao(self):
        from src.builder.routing.motor.window_provider import provider_date
        win = provider_date({"title": "10.03 Processos"}, _ctx_com_datas())
        assert win == ["bloco-02"]

    def test_data_sem_sessao_rende_vazio(self):
        from src.builder.routing.motor.window_provider import provider_date
        # 02.05: data válida mas nenhuma sessão nesse dia -> [] (funil/próximo provider)
        assert provider_date({"title": "02.05 Segmentação"}, _ctx_com_datas()) == []

    def test_sem_data_rende_vazio(self):
        from src.builder.routing.motor.window_provider import provider_date
        assert provider_date({"title": "Plano de Ensino"}, _ctx_com_datas()) == []

    def test_cascata_p3_depois_de_labels(self):
        from src.builder.routing.motor.window_provider import resolve_window
        win, provider = resolve_window({"title": "10.03 Processos"}, _ctx_com_datas())
        assert (win, provider) == (["bloco-02"], "data")

    def test_card_manual_vence_data(self):
        from src.builder.routing.motor.contracts import MotorContext
        from src.builder.routing.motor.window_provider import resolve_window
        ctx = MotorContext.from_artifacts(
            blocks=_ctx_com_datas().blocks,
            card_block_map={"Card X": {"source": "manual", "block_ids": ["bloco-01"]}},
            lessons_index={},
        )
        win, provider = resolve_window(
            {"title": "10.03 Processos", "source_section": "Card X"}, ctx)
        assert (win, provider) == (["bloco-01"], "manual")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_window_provider.py::TestProviderDate -q`
Expected: FAIL — `cannot import name 'provider_date'`

- [ ] **Step 3: Implementar**

Em `window_provider.py`, após `provider_labels`:

```python
def _modal_years(ctx: MotorContext) -> List[str]:
    """Anos das sessions, mais frequente primeiro (curso pode virar o ano)."""
    counts: dict = {}
    for b in ctx.blocks:
        for s in b.get("sessions") or []:
            y = str(s.get("date") or "")[:4]
            if y.isdigit():
                counts[y] = counts.get(y, 0) + 1
    return sorted(counts, key=lambda y: counts[y], reverse=True)


def provider_date(entry: dict, ctx: MotorContext) -> List[str]:
    """P3 — DATA-no-nome (DD.MM) -> sessão do cronograma -> bloco (janela ~1).

    0 colisão medida no corpus SO; se uma data cair em 2 blocos a janela
    carrega ambos (honesto — o disambiguator decide)."""
    dm = extract_date_in_name(entry)
    if not dm:
        return []
    dd, mm = dm
    for year in _modal_years(ctx):
        iso = f"{year}-{mm:02d}-{dd:02d}"
        refs = [
            str(b.get("id") or "")
            for b in ctx.blocks
            if any(str(s.get("date") or "") == iso for s in b.get("sessions") or [])
        ]
        refs = [r for r in refs if r]
        if refs:
            return refs
    return []
```

Atualizar `_CASCADE`:

```python
_CASCADE = (
    (provider_manual, "manual"),
    (provider_labels, "labels"),
    (provider_date, "data"),
)
```

Em `contracts.py`, docstring de `AnchorDecision`: trocar a linha
`provider = qual WindowProvider rendeu a janela ("manual"|"labels"|"").`
por
`provider = qual WindowProvider rendeu a janela ("manual"|"labels"|"data"|"topic"|"").`

- [ ] **Step 4: Rodar e ver passar + regressão MF**

Run: `python -m pytest tests/test_motor_window_provider.py tests/test_motor_import_guard.py -q`
Expected: PASS
Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: ambos `VEREDITO ... PASS` exit 0 (MF não tem DD.MM em títulos; nada muda)

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add src/builder/routing/motor/window_provider.py src/builder/routing/motor/contracts.py tests/test_motor_window_provider.py
git commit -m "feat(motor): provider P3 data-no-nome na cascata (FASE 2)"
```

---

### Task 3: Gate D4 de concordância para janela-1 vinda de P3

**Files:**
- Modify: `src/builder/routing/motor/disambiguator.py`
- Modify: `src/builder/routing/motor/anchor_engine.py:41` (passar provider)
- Modify: `src/builder/routing/motor/contracts.py` (Protocol `Disambiguator`)
- Test: `tests/test_motor_disambiguator.py`

**Interfaces:**
- Consumes: `disambiguate` atual; `_block_signature`, `entry_tokens` (internos do módulo).
- Produces: `disambiguate(entry, window, ctx, markdown="", provider="")` — kwarg novo com default `""` (comportamento FASE 0/1 intacto). Com `provider="data"` e janela-1: band `alta` SÓ se material tem token discriminante GLOBAL do bloco (df sobre TODAS as assinaturas do curso ≤ `DATE_DF_MAX`); senão ancora com band `media` + `flag=True`. Constante módulo-level `DATE_DF_MAX: int = 2` (calibrável no probe da Task 5).

**Racional (spec §3 D4):** "Sinais concordam (data-no-nome + topic) → `alta`; discordam → FLAG". Dry-run: janela-1 cega daria 4 confiante-errado novos no SO (2× `02.06`, 2× `23.06`). Concordância ingênua (∩≠∅) NÃO basta: "02.06 Gerência de I/O" ∩ bloco-12 ("enunciado **gerencia**") ≠ ∅ mas está ERRADO — o token precisa ser específico do bloco no curso (df global baixo), não boilerplate como "gerencia" no SO.

- [ ] **Step 1: Escrever os testes que falham**

Adicionar ao final de `tests/test_motor_disambiguator.py`:

```python
class TestGateConcordanciaData:
    """D4 para janela-1 vinda de P3: alta só com token discriminante global."""

    @staticmethod
    def _ctx():
        from src.builder.routing.motor.contracts import MotorContext
        # "gerencia" aparece em 3 blocos (df alto = boilerplate do curso);
        # "escalonamento" e "memoria" são específicos (df=1).
        blocks = [
            {"id": "bloco-03", "period_start": "2026-03-10",
             "topic_text": "escalonamento gerencia processador",
             "sessions": [{"date": "2026-03-10", "label": "escalonamento"}]},
            {"id": "bloco-11", "period_start": "2026-05-12",
             "topic_text": "gerencia memoria paginacao",
             "sessions": [{"date": "2026-05-12", "label": "gerencia de memoria"}]},
            {"id": "bloco-12", "period_start": "2026-06-02",
             "topic_text": "enunciado gerencia",
             "sessions": [{"date": "2026-06-02", "label": "enunciado do tp2"}]},
        ]
        return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})

    def test_concordancia_discriminante_ancora_alta(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        d = disambiguate({"title": "24.03 Escalonamento de Processos"},
                         ["bloco-03"], self._ctx(), provider="data")
        assert (d.block_ref, d.band, d.flag) == ("bloco-03", "alta", False)

    def test_token_boilerplate_nao_da_alta(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        # caso real 02.06: material de I/O postado no dia do enunciado TP2.
        # "gerencia" casa bloco-12 mas tem df=3 -> NÃO discriminante -> flag.
        d = disambiguate({"title": "02.06 Lâminas Gerência de I O"},
                         ["bloco-12"], self._ctx(), provider="data")
        assert d.block_ref == "bloco-12"       # ancora no melhor (invariante)
        assert d.flag is True
        assert d.band != "alta"

    def test_silencio_lexical_flagado(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        d = disambiguate({"title": "09.04 Lâminas Semáforos"},
                         ["bloco-12"], self._ctx(), provider="data")
        assert (d.flag, d.band != "alta") == (True, True)

    def test_provider_default_preserva_fast_path(self):
        from src.builder.routing.motor.disambiguator import disambiguate
        # P1/P2 (manual/labels ou default ""): janela-1 segue alta/1.0 (FASE 0/1)
        d = disambiguate({"title": "qualquer"}, ["bloco-12"], self._ctx())
        assert (d.band, d.conf, d.flag) == ("alta", 1.0, False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_disambiguator.py::TestGateConcordanciaData -q`
Expected: FAIL — `disambiguate() got an unexpected keyword argument 'provider'`

- [ ] **Step 3: Implementar**

Em `disambiguator.py`, adicionar constante junto de `MARGIN_TAU`:

```python
# Gate de concordância do P3 (D4, spec §3): janela-1 vinda de DATA só é
# confiante se o material carrega token ESPECÍFICO do bloco no curso —
# df global (nº de blocos cuja assinatura tem o token) <= DATE_DF_MAX.
# Data de POSTAGEM != aula do conteúdo (5 misses medidos no gold SO).
DATE_DF_MAX: int = 2
```

Adicionar helper e alterar `disambiguate`:

```python
def _global_df(ctx: MotorContext) -> dict:
    """df de cada token sobre as assinaturas de TODOS os blocos do curso."""
    df: dict = {}
    for b in ctx.blocks:
        for t in set(_block_signature(b, ctx)):
            df[t] = df.get(t, 0) + 1
    return df


def _date_window1_decision(entry: dict, block: dict, ctx: MotorContext,
                           markdown: str, win: List[str]) -> AnchorDecision:
    """Janela-1 de P3: alta exige concordância por token discriminante global."""
    ref = str(block.get("id") or block.get("block_uuid") or win[0])
    mat = entry_tokens(entry, markdown)
    sig = set(_block_signature(block, ctx))
    df = _global_df(ctx)
    discriminante = {t for t in (mat & sig) if df.get(t, 0) <= DATE_DF_MAX}
    if discriminante:
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="janela-1", window=win)
    return AnchorDecision(block_ref=ref, conf=0.0, band="media", flag=True,
                          method="janela-1", window=win)
```

Assinatura e fast-path de `disambiguate` mudam para:

```python
def disambiguate(entry: dict, window: List[str], ctx: MotorContext,
                 markdown: str = "", provider: str = "") -> AnchorDecision:
    win = list(window or [])
    blocks = [ctx.block_by_ref(r) for r in win]
    blocks = [b for b in blocks if b is not None]
    if not blocks:
        return AnchorDecision(block_ref="", method="funil", window=win)
    # Fast-path janela-1 exige que a JANELA ORIGINAL tenha 1 ref, não apenas
    # os resolvíveis (comentário FASE 1 mantido). Janela-1 vinda de DATA passa
    # pelo gate de concordância D4 — postagem != aula do conteúdo.
    if len(win) == 1 and len(blocks) == 1:
        if provider == "data":
            return _date_window1_decision(entry, blocks[0], ctx, markdown, win)
        ref = str(blocks[0].get("id") or blocks[0].get("block_uuid") or win[0])
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="janela-1", window=win)
    ...resto inalterado...
```

Em `anchor_engine.py` linha 38-44, `resolve` passa o provider:

```python
        window, provider = resolve_window(entry, ctx)
        if not window:
            return None  # sem janela -> funil (invariante ANCHOR-ONLY)
        decision = disambiguate(entry, window, ctx, markdown, provider=provider)
```

Em `contracts.py`, Protocol `Disambiguator`:

```python
class Disambiguator(Protocol):
    """Escolhe DENTRO da janela (só roda se |janela| > 1)."""
    def __call__(self, entry: dict, window: List[str], ctx: MotorContext,
                 markdown: str = "", provider: str = "") -> AnchorDecision: ...
```

- [ ] **Step 4: Rodar e ver passar + regressão MF**

Run: `python -m pytest tests/test_motor_disambiguator.py tests/test_motor_anchor_engine.py tests/test_motor_golden_mf.py -q`
Expected: PASS
Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: ambos PASS exit 0 (provider "manual"/"labels" não entra no gate novo)

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add src/builder/routing/motor/disambiguator.py src/builder/routing/motor/anchor_engine.py src/builder/routing/motor/contracts.py tests/test_motor_disambiguator.py
git commit -m "feat(motor): gate D4 de concordância para janela-1 do P3 (data != conteúdo)"
```

---

### Task 4: P4 `provider_topic` (TCC topic-bridge) + entrada na cascata

**Files:**
- Modify: `src/builder/routing/motor/window_provider.py`
- Test: `tests/test_motor_window_provider.py`

**Interfaces:**
- Consumes: `_toks` NÃO (regras próprias); `block_topic_tokens`, `block_session_tokens` de `disambiguator` (mesmo pacote, whitelist ok); `normalize_match_text` de `src.builder.text.normalize`.
- Produces: `provider_topic(entry: dict, ctx: MotorContext) -> List[str]` — janela = blocos cuja assinatura casa o TÓPICO do card por stem-prefix-6; `_CASCADE` ganha `(provider_topic, "topic")` no FIM. Constantes `TOPIC_STEM_LEN: int = 6`, `TOPIC_MIN_TOKEN: int = 2`.

**Racional (spec §3 [Δ item 9] + F-TCC):** parsear o TÓPICO de "Semana N - Tópico"; o N NUNCA vira janela. Tokens do tópico são texto CURADO (título de card), então limiar de tamanho mais baixo (>=2 segura "np", "t2") e stem-prefix-6 casa flexões (`completude`×`complexidade`/`complete` → `comple`). Dry-run: com `_toks` cru 3/5 pinos contidos; stem-prefix resgata "NP-completude".

- [ ] **Step 1: Escrever os testes que falham**

```python
class TestProviderTopic:
    @staticmethod
    def _ctx():
        from src.builder.routing.motor.contracts import MotorContext
        blocks = [
            {"id": "bloco-16", "period_start": "2026-05-06", "topic_text": "",
             "sessions": [{"date": "2026-05-06", "label": "prova p1 prova"}]},
            {"id": "bloco-21", "period_start": "2026-05-27",
             "topic_text": "reducoes polinomiais",
             "sessions": [{"date": "2026-05-27", "label": "reducoes np"}]},
            {"id": "bloco-22", "period_start": "2026-06-03",
             "topic_text": "complexidade tempo classe hard reducao problemas pspace complete",
             "sessions": [{"date": "2026-06-03", "label": "complexidade de tempo classe np hard"}]},
        ]
        return MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})

    def test_topico_com_stem_prefix(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # caso real que falhava cru: "completude" ~ "complexidade"/"complete"
        win = provider_topic({"source_section": "Semana 12 - NP-completude"}, self._ctx())
        assert "bloco-22" in win

    def test_ordinal_nunca_vira_janela(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # F-TCC: card só-ordinal (sem tópico) NÃO rende janela por week-math
        assert provider_topic({"source_section": "Semana 5 -"}, self._ctx()) == []
        assert provider_topic({"source_section": "Semana 5"}, self._ctx()) == []

    def test_section_sem_padrao_semana_rende_vazio(self):
        from src.builder.routing.motor.window_provider import provider_topic
        # provider é do padrão "Semana N - Tópico"; outros cards ficam com P1/P2
        assert provider_topic(
            {"source_section": "Verificação de Programas"}, self._ctx()) == []

    def test_token_curto_curado_casa(self):
        from src.builder.routing.motor.window_provider import provider_topic
        win = provider_topic({"source_section": "Semana 10 - Revisão para P1 e Prova P1"},
                             self._ctx())
        assert "bloco-16" in win

    def test_cascata_topic_por_ultimo(self):
        from src.builder.routing.motor.window_provider import resolve_window, _CASCADE
        assert [name for _, name in _CASCADE] == ["manual", "labels", "data", "topic"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_window_provider.py::TestProviderTopic -q`
Expected: FAIL — `cannot import name 'provider_topic'`

- [ ] **Step 3: Implementar**

Em `window_provider.py` (adicionar import no topo: `from src.builder.text.normalize import normalize_match_text` e `from src.builder.routing.motor.disambiguator import block_topic_tokens, block_session_tokens, _GENERIC_STEMS`):

```python
# P4 — topic-bridge (spec §3 [Δ item 9]; F-TCC: o N ordinal NUNCA vira janela).
_SEMANA_TOPIC_RE = re.compile(r"^\s*semana\s*\d+\s*-\s*(.+)$", re.IGNORECASE)
TOPIC_STEM_LEN: int = 6
TOPIC_MIN_TOKEN: int = 2


def _topic_tokens(topic: str) -> set:
    """Tokens do TÓPICO curado do card: >=2 chars (segura np/t2), sem genéricos."""
    out = set()
    for t in normalize_match_text(str(topic or "")).split():
        if len(t) >= TOPIC_MIN_TOKEN and not t.isdigit() and t[:8] not in _GENERIC_STEMS:
            out.add(t)
    return out


def _stems(tokens: set) -> set:
    return {t[:TOPIC_STEM_LEN] for t in tokens}


def provider_topic(entry: dict, ctx: MotorContext) -> List[str]:
    """P4 — TÓPICO do card "Semana N - Tópico" ↔ topic_text/sessions[].label."""
    m = _SEMANA_TOPIC_RE.match(str(entry.get("source_section") or ""))
    if not m:
        return []
    tstems = _stems(_topic_tokens(m.group(1)))
    if not tstems:
        return []  # card só-ordinal: week-math PROIBIDO -> sem janela
    refs = []
    for b in ctx.blocks:
        sig = block_topic_tokens(b) | block_session_tokens(b, ctx)
        if tstems & _stems(sig):
            ref = str(b.get("id") or "")
            if ref:
                refs.append(ref)
    return refs
```

Atenção ao regex: hífen OBRIGATÓRIO (`-`) separa ordinal de tópico; "Semana 7- Halteproblem" (sem espaço antes do hífen) precisa casar — `\s*\d+\s*-\s*` cobre. "Semana 5" (sem hífen) NÃO casa → sem janela ✓.

Atualizar `_CASCADE`:

```python
_CASCADE = (
    (provider_manual, "manual"),
    (provider_labels, "labels"),
    (provider_date, "data"),
    (provider_topic, "topic"),
)
```

- [ ] **Step 4: Rodar e ver passar + guard + regressão MF**

Run: `python -m pytest tests/test_motor_window_provider.py tests/test_motor_import_guard.py -q`
Expected: PASS (guard: `disambiguator` está no MESMO pacote; import permitido)
Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: ambos PASS (MF: source_sections sem "Semana N -"; P4 não dispara)

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add src/builder/routing/motor/window_provider.py tests/test_motor_window_provider.py
git commit -m "feat(motor): provider P4 topic-bridge TCC na cascata (FASE 2)"
```

---

### Task 5: Probe externo SO (`fase2_prova_SO.py`) + calibração `DATE_DF_MAX`

**Files:**
- Create: `scripts/fase2_prova_SO.py`

**Interfaces:**
- Consumes: `MotorContext.from_artifacts`, `AnchorEngine`, `is_out_of_disamb_scope` (mesmo padrão de `scripts/fase1_recall_gate_MF.py`: `build_context`, `_md_text`, colapso por `pair_key`).
- Produces: script READ-ONLY com veredito HARD exit 0/1. Métricas: cobertura P3, colisões, contenção, acurácia par-colapsada, confiante-errado, matriz do gate.

**Aceite (spec §6 P3):** data → exatamente 1 bloco (0 colisão); cobertura ~45% dos materiais SO; nenhum erro confiante escapa (D4). Baseline honesto do funil no gold SO: 47.4%.

- [ ] **Step 1: Escrever o script**

```python
#!/usr/bin/env python3
"""FASE 2 — prova do provider P3 (SO data-no-nome) vs ground_truth_SO.csv (READ-ONLY).

Números do aceite (spec §6): cobertura ~45%, data->exatamente 1 bloco (0 colisão),
confiante-errado 0 no escopo P3. Reporta tb acurácia par-colapsada vs baseline
do funil (47.4%). NÃO muta manifest/artefato. Uso:
  python scripts/fase2_prova_SO.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.contracts import MotorContext          # noqa: E402
from src.builder.routing.motor.anchor_engine import (                  # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)
from src.builder.routing.motor.window_provider import (                # noqa: E402
    provider_date, resolve_window,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Sistemas-Operacionais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_SO.csv"
PISO_COBERTURA = 0.40      # spec ~45%; medido 20/42=48% bruto
BASELINE_FUNIL = 0.474     # spec §2: SO 47.4% (18/38) — motor deve >=
MD_CAP = 6000


def _load(repo: Path, rel: str):
    p = repo / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _md_text(repo: Path, e: dict) -> str:
    for k in ("approved_markdown", "curated_markdown", "base_markdown"):
        rel = str(e.get(k) or "")
        p = repo / rel
        if rel and p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:MD_CAP]
            except OSError:
                pass
    return ""


def build_context(repo: Path) -> MotorContext:
    tl = _load(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(repo, "course/.card_block_map.json")
    m = _load(repo, "manifest.json")
    course_name = str(((m.get("course") or {}).get("course_name")) or "")
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index={}, course_name=course_name,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    args = ap.parse_args()

    ctx = build_context(args.repo)
    manifest = _load(args.repo, "manifest.json")
    entries = {str(e.get("id")): e for e in manifest.get("entries") or []}
    with args.gold.open(encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("scorable") or "") == "yes"]

    engine = AnchorEngine()
    cobertos, colisoes, contidos, fora = [], [], [], []
    results, cw, matriz = {}, [], defaultdict(int)
    for r in rows:
        e = entries.get(r["id"])
        if e is None:
            continue
        win = provider_date(e, ctx)
        if win:
            cobertos.append(r["id"])
            if len(win) > 1:
                colisoes.append((r["id"], win))
            (contidos if r["true_block_id"] in win else fora).append(r["id"])
        if is_out_of_disamb_scope(e):
            continue
        d = engine.resolve(e, ctx, _md_text(args.repo, e))
        if d is None:
            continue
        pred = str((ctx.block_by_ref(d.block_ref) or {}).get("id") or d.block_ref)
        ok = pred == r["true_block_id"]
        results[r["id"]] = ok
        matriz[("alta" if d.band == "alta" else "resto", "ok" if ok else "err")] += 1
        if d.band == "alta" and not ok and not d.flag:
            cw.append((r["id"], pred, r["true_block_id"], d.provider))

    by_pair = defaultdict(list)
    for r in rows:
        if r["id"] in results:
            by_pair[r["pair_key"] or r["id"]].append(results[r["id"]])
    total = len(by_pair)
    acc = sum(int(all(v)) for v in by_pair.values()) / max(total, 1)
    cob = len(cobertos) / max(len(rows), 1)

    print("=" * 70)
    print(f"FASE 2/P3 — SO  repo={args.repo.name}  escopo={len(rows)} rows gold")
    print(f"  cobertura P3: {len(cobertos)}/{len(rows)} = {cob:.1%} (piso {PISO_COBERTURA:.0%})")
    print(f"  colisões (data em >1 bloco): {len(colisoes)} {colisoes}")
    print(f"  contenção da janela P3: {len(contidos)} in / {len(fora)} out; out={fora}")
    print(f"  acurácia motor (par-colapsada, com-janela): {acc:.1%} de {total} pares "
          f"(baseline funil {BASELINE_FUNIL:.1%})")
    print(f"  matriz gate: {dict(matriz)}")
    print(f"  confiante-e-errado (band alta, sem flag): {len(cw)} {cw}")
    ok_cob = cob >= PISO_COBERTURA
    ok_col = not colisoes
    ok_cw = not cw
    verdict = ok_cob and ok_col and ok_cw
    print("=" * 70)
    print(f"VEREDITO FASE 2/P3: {'PASS' if verdict else 'FAIL'} "
          f"(cobertura={ok_cob} colisao0={ok_col} confErrado0={ok_cw})")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Pré-gate + rodar**

Run: `python scripts/audit_gold_freshness.py --course SO` (pré-gate de medição)
Expected: 0 hard-suspeitas
Run: `python scripts/fase2_prova_SO.py`
Expected: primeiro run reporta números REAIS. Analisar a matriz do gate:
- Se `confiante-e-errado > 0`: os tokens que "concordaram" errado têm df alto demais → DIMINUIR `DATE_DF_MAX` (2→1) em `disambiguator.py` e re-rodar.
- Se `alta,ok` ≈ 0 (tudo flagado): gate estrangulou → considerar `DATE_DF_MAX` 2→3. Escolher o ponto com `confErrado=0` que MAXIMIZA `alta,ok` (mesmo processo D4 da FASE 1). Documentar a grade testada no docstring da constante.

- [ ] **Step 3: Fixar veredito e re-rodar até PASS**

Run: `python scripts/fase2_prova_SO.py && echo PASS_CONFIRMADO`
Expected: `VEREDITO FASE 2/P3: PASS` + exit 0

- [ ] **Step 4: Regressão MF (o DATE_DF_MAX não toca MF, provar)**

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: ambos PASS exit 0

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add scripts/fase2_prova_SO.py src/builder/routing/motor/disambiguator.py
git commit -m "feat(motor): probe FASE 2 P3/SO com veredito HARD + DATE_DF_MAX calibrado"
```

---

### Task 6: Probe externo TCC (`fase2_prova_TCC.py`)

**Files:**
- Create: `scripts/fase2_prova_TCC.py`

**Interfaces:**
- Consumes: mesmos helpers-padrão (copiar `_load`/`_md_text`/`build_context` do probe SO — scripts externos são standalone por design, como fase0/fase1).
- Produces: script READ-ONLY com veredito HARD exit 0/1. Métricas: pinos reproduzidos (≥4/5), cobertura P4 (>26%), confiante-errado=0, acurácia par-colapsada vs baseline 56.0%.

**Definição de "pino reproduzido" (aceite §6):** para cada um dos 5 cards `source=manual` do `.card_block_map.json` do TCC, rodar `provider_topic` num entry sintético `{"source_section": <card>}` IGNORANDO o card map: reproduzido = `janela_P4 ∩ block_ids_manual ≠ ∅`. Reportar separadamente a contenção total (`manual ⊆ janela`) como métrica secundária. Dry-run: 4/5 por interseção cru; stem-prefix leva NP-completude a casar → alvo 5/5.

- [ ] **Step 1: Escrever o script**

```python
#!/usr/bin/env python3
"""FASE 2 — prova do provider P4 (TCC topic-bridge) vs ground_truth_TCC.csv (READ-ONLY).

Números do aceite (spec §6): >=4/5 pinos manuais reproduzidos (janela P4 acha o
bloco do pino SEM olhar o manual), cobertura >26%, resíduo cai pro TIER 3 SEM
errar confiante. F-TCC: o N de "Semana N" NUNCA vira janela. Uso:
  python scripts/fase2_prova_TCC.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.contracts import MotorContext          # noqa: E402
from src.builder.routing.motor.anchor_engine import (                  # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)
from src.builder.routing.motor.window_provider import provider_topic   # noqa: E402

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "TCC-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_TCC.csv"
PISO_PINOS = 4             # de 5 (spec §6)
PISO_COBERTURA = 0.26      # deve SUPERAR o só-manual
BASELINE_FUNIL = 0.560     # spec §2: TCC 56.0% (14/25)
MD_CAP = 6000


def _load(repo: Path, rel: str):
    p = repo / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _md_text(repo: Path, e: dict) -> str:
    for k in ("approved_markdown", "curated_markdown", "base_markdown"):
        rel = str(e.get(k) or "")
        p = repo / rel
        if rel and p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:MD_CAP]
            except OSError:
                pass
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    args = ap.parse_args()

    tl = _load(args.repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(args.repo, "course/.card_block_map.json")
    manifest = _load(args.repo, "manifest.json")
    course_name = str(((manifest.get("course") or {}).get("course_name")) or "")

    # 1) Pinos: P4 SEM o card map (senão P1 responde pelo pino).
    ctx_sem_manual = MotorContext.from_artifacts(
        blocks=blocks, card_block_map={}, lessons_index={}, course_name=course_name)
    manuais = {k: v for k, v in cbm.items() if str(v.get("source") or "") == "manual"}
    reproduzidos, contidos_total = [], []
    for card, info in sorted(manuais.items()):
        win = provider_topic({"source_section": card}, ctx_sem_manual)
        alvo = [str(b) for b in info.get("block_ids") or []]
        inter = sorted(set(win) & set(alvo))
        if inter:
            reproduzidos.append(card)
        if alvo and set(alvo) <= set(win):
            contidos_total.append(card)
        print(f"  pino {'OK ' if inter else 'ERR'} '{card}' manual={alvo} p4={win}")

    # 2) Cobertura + acurácia no gold com a cascata completa.
    ctx = MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index={}, course_name=course_name)
    entries = {str(e.get("id")): e for e in manifest.get("entries") or []}
    with args.gold.open(encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("scorable") or "") == "yes"]

    engine = AnchorEngine()
    com_janela, results, cw = [], {}, []
    for r in rows:
        e = entries.get(r["id"])
        if e is None:
            continue
        if provider_topic(e, ctx):
            com_janela.append(r["id"])
        if is_out_of_disamb_scope(e):
            continue
        d = engine.resolve(e, ctx, _md_text(args.repo, e))
        if d is None:
            continue
        pred = str((ctx.block_by_ref(d.block_ref) or {}).get("id") or d.block_ref)
        ok = pred == r["true_block_id"]
        results[r["id"]] = ok
        if d.band == "alta" and not ok and not d.flag:
            cw.append((r["id"], pred, r["true_block_id"], d.provider))

    by_pair = defaultdict(list)
    for r in rows:
        if r["id"] in results:
            by_pair[r["pair_key"] or r["id"]].append(results[r["id"]])
    total = len(by_pair)
    acc = sum(int(all(v)) for v in by_pair.values()) / max(total, 1)
    cob = len(com_janela) / max(len(rows), 1)

    print("=" * 70)
    print(f"FASE 2/P4 — TCC  repo={args.repo.name}  escopo={len(rows)} rows gold")
    print(f"  pinos reproduzidos (interseção): {len(reproduzidos)}/{len(manuais)} "
          f"(piso {PISO_PINOS}); contenção total: {len(contidos_total)}/{len(manuais)}")
    print(f"  cobertura P4: {len(com_janela)}/{len(rows)} = {cob:.1%} (piso >{PISO_COBERTURA:.0%})")
    print(f"  acurácia motor (par-colapsada, com-janela): {acc:.1%} de {total} pares "
          f"(baseline funil {BASELINE_FUNIL:.1%})")
    print(f"  confiante-e-errado: {len(cw)} {cw}")
    ok_p = len(reproduzidos) >= PISO_PINOS
    ok_c = cob > PISO_COBERTURA
    ok_w = not cw
    verdict = ok_p and ok_c and ok_w
    print("=" * 70)
    print(f"VEREDITO FASE 2/P4: {'PASS' if verdict else 'FAIL'} "
          f"(pinos={ok_p} cobertura={ok_c} confErrado0={ok_w})")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Pré-gate + rodar**

Run: `python scripts/audit_gold_freshness.py --course TCC`
Expected: 0 hard-suspeitas
Run: `python scripts/fase2_prova_TCC.py`
Expected: números reais. Se pinos <4/5: inspecionar os toks/stems do pino que falhou e calibrar `TOPIC_STEM_LEN`/`TOPIC_MIN_TOKEN` (grade 5/6/7 × 2/3) — escolher ponto com pinos máximos SEM `confiante-errado` e SEM cobertura <26%. Se confiante-errado >0 vindo de `provider="topic"` com janela grande: o disambiguator D4 já deve flagar (MARGIN_TAU); investigar antes de mexer em constante — pode ser janela P4 estreita demais (1 bloco errado): nesse caso janela-1 de "topic" também precisa do gate de concordância (estender o gate da Task 3 a `provider in {"data", "topic"}` — decisão a validar pelo número).

- [ ] **Step 3: Fixar veredito e re-rodar até PASS**

Run: `python scripts/fase2_prova_TCC.py && echo PASS_CONFIRMADO`
Expected: `VEREDITO FASE 2/P4: PASS` + exit 0

- [ ] **Step 4: Regressão MF + suite completa**

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: ambos PASS
Run: `python -m pytest tests -q`
Expected: 1701+ passed (novos testes somam), 4 skipped, 0 failed

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add scripts/fase2_prova_TCC.py src/builder/routing/motor/window_provider.py
git commit -m "feat(motor): probe FASE 2 P4/TCC com veredito HARD + calibração topic-match"
```

---

### Task 7: Report FASE 2 + tracker + ROUTER + graph

**Files:**
- Create: `docs/reports/2026-07-08-fase2-providers-report.md`
- Modify: `docs/reports/pendencias.md` (entrada FASE 2 fechada)
- Modify: `.mex/ROUTER.md` (bloco "Motor de atribuicao" — adicionar FASE 2)

**Interfaces:**
- Consumes: saídas REAIS dos probes fase2 (colar números, não inventar).
- Produces: report com: números do aceite §6 lado a lado com o medido; composição do resíduo (o que ficou flag/funil por curso); constantes calibradas (`DATE_DF_MAX`, `TOPIC_STEM_LEN`, `TOPIC_MIN_TOKEN`) com a grade testada; insumo do go/no-go FASE 3 atualizado (fila de flag SO+TCC somada à MF).

- [ ] **Step 1: Escrever o report** com esta estrutura (preencher com números REAIS dos probes):

```markdown
# FASE 2 — Providers P3 (SO) + P4 (TCC): report de fechamento

date: <data real>
branch: feat/motor-atribuicao

## Aceite (spec §6) vs medido
| Critério | Spec | Medido | PASS |
|---|---|---|---|
| P3 contenção | data → exatamente 1 bloco, 0 colisão | <colar> | <> |
| P3 cobertura | ~45% materiais SO | <colar> | <> |
| P4 pinos | ≥4/5 reproduzidos | <colar> | <> |
| P4 cobertura | >26% | <colar> | <> |
| Confiante-errado novo | 0 | <colar> | <> |
| Regressão MF | fase0+fase1 PASS | <colar> | <> |

## Constantes calibradas
<DATE_DF_MAX, TOPIC_STEM_LEN, TOPIC_MIN_TOKEN + grade testada e racional>

## Composição do resíduo (insumo go/no-go FASE 3)
<por curso: quantos flag, quantos funil, classes de erro>

## Fila humana consolidada (MF + SO + TCC)
<flags totais — o número do go/no-go>
```

- [ ] **Step 2: Atualizar `docs/reports/pendencias.md`** — nova entrada `[DERIVADO] FASE 2 FECHADA` no bloco do motor (mesmo formato das entradas FASE 0/1), com números reais e ponteiro pro report.

- [ ] **Step 3: Atualizar `.mex/ROUTER.md`** — no item "Motor de atribuicao FASE 0+1 ENTREGUES", estender para FASE 0+1+2 com uma frase por provider novo + números.

- [ ] **Step 4: Atualizar o grafo**

Run: `graphify update .`
Expected: exit 0, contagem de nodes atualizada

- [ ] **Step 5: Pedir OK do user e commitar**

```bash
git add docs/reports/2026-07-08-fase2-providers-report.md docs/reports/pendencias.md .mex/ROUTER.md
git commit -m "docs(motor): fechamento FASE 2 — report P3/P4 + tracker + ROUTER"
```

---

## Self-Review (executada na escrita do plano)

1. **Spec coverage:** §7 FASE 2 = P3+P4 (Tasks 1-4, 6) ✓; §6 aceite P3 (Task 5) ✓; §6 aceite P4 (Task 6) ✓; F-TCC week-math proibido (Task 4, teste `test_ordinal_nunca_vira_janela`) ✓; D4 concordância data+topic (Task 3) ✓; §12 "limiar do topic-match" e "SO P3 range largo" = calibração TDD nos probes (Tasks 5-6) ✓; guard imports (steps de regressão) ✓. Fora de escopo confirmado: TIER 0/1/3, janela-de-prazo, integração (fases 3-4).
2. **Placeholder scan:** os `<colar>` do report da Task 7 são intencionais (números só existem após os probes rodarem) — instrução explícita "preencher com números REAIS".
3. **Type consistency:** `provider_date`/`provider_topic` retornam `List[str]`; `disambiguate(..., provider="")` consistente entre Task 3 (definição), contracts (Protocol) e anchor_engine (call-site); nomes de cascata "manual"/"labels"/"data"/"topic" idênticos em Tasks 2/4/6 e docstring de contracts.
