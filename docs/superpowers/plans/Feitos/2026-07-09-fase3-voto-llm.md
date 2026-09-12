# FASE 3 — Voto LLM (TIER 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o TIER 3 do motor de atribuição — voto Gemini nos materiais flagged ∪ same-theme, cacheado por identidade de conteúdo, bounded à janela — e provar lift ≥ +4 no gold MF sem novo confiante-errado.

**Architecture:** Novo módulo `llm_vote.py` no pacote do motor (cache `material_curation`, série same-theme, prompt, `LlmVoter`); `AnchorEngine` ganha hook opcional TIER 3 (`voter=None` ⇒ saída byte-idêntica às FASES 0-2); régua HARD nova `scripts/fase3_prova_LLM_MF.py` mede o lift contra `ground_truth_MF.csv`. Integração no reprocess é FASE 4 — aqui tudo é READ-ONLY nos repos-tutor.

**Tech Stack:** Python, pydantic (schema do voto), google-genai via `GeminiClient.summarize_bundle` (lazy), pytest.

**Contexto de decisão (GO do user, 09/07):** spec `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` §3 TIER 3 + Regras do voto (§12 da revisão), §7 FASE 3, §9 itens 10/12; handoff `docs/reports/2026-07-09-handoff-fase3.md`.

## Global Constraints

- Branch `feat/motor-atribuicao`. **NÃO commitar sem autorização de sessão** — re-perguntar ao user ANTES do Task 1 (na FASE 2 ele autorizou commit-por-task; autorização não transfere).
- **READ-ONLY nos repos-tutor**: nenhuma escrita fora de `GPT-Tutor-Generator`. O cache do probe vive em `docs/reports/material_curation_MF.json` (o sidecar `material_curation.json` NO repo-tutor é FASE 4, escrito pelo reprocess = ação do user na GUI).
- Lógica nova SÓ em `src/builder/routing/motor/` e `scripts/`; NUNCA `engine.py`.
- LLM = `google-genai` **lazy dentro do método**; PROIBIDO `google.generativeai` / `genai.GenerativeModel`. Modelo: `gemini-2.5-flash` via `get_gemini_client(config)` (chave: config UI > env `GEMINI_API_KEY`).
- Guard AST vigente: pacote do motor NÃO importa `block_token_weights`, `score_entry_against_timeline_block`, `select_probable_period_for_entry` (teste existente deve continuar verde).
- **Autoconfiança do LLM é IGNORADA** como sinal (MARCO 1: "alta" 18/18, acertou 8) — gravada no cache só para auditoria; nenhum gate a lê.
- **Voto BOUNDED à janela**: voto fora da janela = inválido → mantém FLAG. **Sem-janela NÃO vota** (classe plano.pdf perdida — regra final §12; o funil-piso responde).
- **Aceitação cega no escopo** (flagged ∪ same-theme): voto válido SUBSTITUI a escolha determinística; band `media`, `flag=False`, `provider="llm"`, `method="llm"`.
- **Cache por identidade de conteúdo** (md5 dos bytes de `source_path`; fallback `id`) — gêmeos compartilham 1 voto (coerente com TIER 0); write atômico (tmp + `os.replace`); seed = `docs/reports/marco1_votes_MF.json` re-chaveado. MARCO 0/1 NÃO se re-rodam.
- **Cap=20 chamadas API por rodada** (cache hit não conta). Escopo maior que o cap ⇒ probe INCOMPLETO (exit 1), re-rodar acumula.
- **Número do aceite (spec §7):** lift ≥ **+4** acertos no escopo do voto no MF, **0** confiante-errado (band alta + errado, global). FAIL é resultado honesto — reportar e devolver ao user; NÃO prompt-engineer o grão-de-semana (spec §12 regra 4).
- **PRÉ-GATE:** `python scripts/audit_gold_freshness.py` antes de qualquer medição contra gold.
- **Regressão obrigatória** ao fim: `fase0_prova_motor_MF.py` && `fase1_recall_gate_MF.py` && `fase2_prova_SO.py` && `fase2_prova_TCC.py` + suite pytest completa (1724 passed / 0 failed é o piso).
- UTF-8 shim (`sys.stdout.reconfigure`) em script novo; docs em PT-BR.
- `AnchorEngine()` sem voter = comportamento FASE 2 **byte-idêntico** (flag-OFF do TIER 3).
- Pre-commit hook pode imprimir UnicodeEncodeError não-fatal — confirmar commit com `git log -1`.
- Após mudanças de código: `graphify update .`.

## File Structure

| Arquivo | Papel |
|---|---|
| Create `src/builder/routing/motor/llm_vote.py` | TIER 3 completo: cache IO, `content_key`, seed import, série same-theme, prompt, `match_window_ref`, `LlmVoter` |
| Modify `src/builder/routing/motor/contracts.py` | `LlmVoterProtocol` (shape do voter, sem lógica) |
| Modify `src/builder/routing/motor/anchor_engine.py` | `AnchorEngine.__init__(voter, series_ids)` + hook TIER 3 no `resolve` |
| Create `scripts/fase3_prova_LLM_MF.py` | Régua HARD FASE 3 (exit 0/1/2), `--dry-run`, seed, cap |
| Create `tests/test_motor_llm_vote.py` | Unidade do módulo (cache, chave, série, voto bounded, cap) |
| Modify `tests/test_motor_anchor_engine.py` | Wiring TIER 3 (voter=None byte-idêntico; aceitação; escopo) |
| Create `docs/reports/2026-07-09-fase3-llm-report.md` | Report de fechamento (Task 6) |

Dependências entre módulos (sem ciclo): `llm_vote` importa `contracts` + `anchor_engine.is_out_of_disamb_scope` (lazy, dentro da função) + `text/normalize`; `anchor_engine` NÃO importa `llm_vote` (recebe o voter pronto). `gemini_client` só via import lazy dentro de método.

---

### Task 1: Cache material_curation + identidade de conteúdo + seed MARCO 1

**Files:**
- Create: `src/builder/routing/motor/llm_vote.py`
- Test: `tests/test_motor_llm_vote.py`

**Interfaces:**
- Consumes: nada do motor (só stdlib + pydantic).
- Produces: `content_key(entry: dict, repo_dir: Path) -> str`; `load_material_curation(path: Path) -> dict` (shape `{"version": 1, "votes": {}}`); `save_material_curation(path: Path, data: dict) -> None` (atômico); `import_marco1_seed(seed_votes: dict, entries_by_id: dict, repo_dir: Path) -> dict` (votos re-chaveados por conteúdo); constantes `MD_PROMPT_CAP = 3500`, `DEFAULT_CAP = 20`; `class Voto(BaseModel)` com `block_id: str`, `confianca: str`, `justificativa_curta: str`.

- [ ] **Step 1: Escrever os testes que falham**

```python
"""Testes do TIER 3 (llm_vote): cache, chave de conteudo, seed, serie, voto bounded."""
from __future__ import annotations

import json
from pathlib import Path

from src.builder.routing.motor.llm_vote import (
    content_key,
    import_marco1_seed,
    load_material_curation,
    save_material_curation,
)


def _entry(rid: str, source_path: str = "", title: str = "", section: str = "",
           category: str = "material") -> dict:
    return {"id": rid, "source_path": source_path, "title": title or rid,
            "source_section": section, "category": category}


def test_content_key_gemeos_compartilham_chave(tmp_path: Path):
    (tmp_path / "a.pdf").write_bytes(b"mesmo conteudo")
    (tmp_path / "b.pdf").write_bytes(b"mesmo conteudo")
    k1 = content_key(_entry("e1", "a.pdf"), tmp_path)
    k2 = content_key(_entry("e2", "b.pdf"), tmp_path)
    assert k1 == k2 and len(k1) == 32  # md5 hex


def test_content_key_fallback_id_sem_arquivo(tmp_path: Path):
    assert content_key(_entry("orfao", "nao/existe.pdf"), tmp_path) == "orfao"
    assert content_key(_entry("semsrc"), tmp_path) == "semsrc"


def test_cache_roundtrip_e_corrompido(tmp_path: Path):
    path = tmp_path / "material_curation.json"
    assert load_material_curation(path) == {"version": 1, "votes": {}}
    data = {"version": 1, "votes": {"k": {"block_id": "bloco-01"}}}
    save_material_curation(path, data)
    assert load_material_curation(path) == data
    assert not path.with_suffix(".json.tmp").exists()  # write atomico limpa tmp
    path.write_text("{ nao e json", encoding="utf-8")
    assert load_material_curation(path) == {"version": 1, "votes": {}}


def test_import_marco1_seed_rechaveia_por_conteudo(tmp_path: Path):
    (tmp_path / "x.pdf").write_bytes(b"conteudo X")
    entries = {"rid1": _entry("rid1", "x.pdf"), "rid3": _entry("rid3")}
    seed = {
        "rid1": {"block_id": "bloco-05", "confianca": "alta",
                 "justificativa": "j", "model": "gemini-2.5-flash"},
        "rid2": {"block_id": "bloco-01"},                # entry sumiu: pula
        "rid3": {"block_id": "", "erro": "timeout"},     # voto com erro: pula
    }
    votes = import_marco1_seed(seed, entries, tmp_path)
    key = content_key(entries["rid1"], tmp_path)
    assert set(votes) == {key}
    assert votes[key]["block_id"] == "bloco-05"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.routing.motor.llm_vote'`

- [ ] **Step 3: Implementar o módulo (parte 1)**

```python
"""TIER 3 (FASE 3): voto LLM nos flagged ∪ same-theme (spec §3 TIER 3 + §12).

Regras (sign-off condicional 03/07 + GO do user 09/07):
- Autoconfianca do LLM e IGNORADA (gravada so p/ auditoria; nenhum gate le).
- Voto BOUNDED a janela: fora da janela = invalido -> mantem FLAG.
- Sem-janela NAO vota (funil-piso responde).
- Cache por IDENTIDADE DE CONTEUDO (md5 do arquivo; fallback id) — gemeos
  compartilham 1 voto (coerente com TIER 0); write atomico; seed MARCO 1.
- Cap de chamadas API por rodada (cache hit nao conta).
- google-genai LAZY dentro do metodo (invariante spec §4).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel

from src.builder.routing.motor.contracts import MotorContext
from src.builder.text.normalize import normalize_match_text

MD_PROMPT_CAP = 3500   # protocolo MARCO 1
DEFAULT_CAP = 20       # orcamento D8 por rodada/reprocess

SYSTEM_TEMPLATE = (
    "Voce e o desambiguador de atribuicao material->bloco de um tutor de curso "
    "universitario ({course}). Dado um material didatico e os blocos candidatos "
    "da timeline do curso (com datas e topicos do roteiro do professor), escolha "
    "o bloco em que esse material foi usado em aula. Responda APENAS com um dos "
    "block_id candidatos, exatamente como escrito (ex.: bloco-13)."
)


class Voto(BaseModel):
    block_id: str
    confianca: str            # alta|media|baixa — auditoria; NUNCA lida por gate
    justificativa_curta: str


def content_key(entry: dict, repo_dir: Path) -> str:
    """Identidade de conteudo: md5 dos bytes de source_path; fallback = id."""
    rel = str(entry.get("source_path") or "")
    p = Path(repo_dir) / rel
    if rel and p.is_file():
        try:
            h = hashlib.md5()
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            pass
    return str(entry.get("id") or "")


def load_material_curation(path: Path) -> dict:
    if not Path(path).is_file():
        return {"version": 1, "votes": {}}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "votes": {}}
    if not isinstance(data, dict) or not isinstance(data.get("votes"), dict):
        return {"version": 1, "votes": {}}
    return data


def save_material_curation(path: Path, data: dict) -> None:
    """Write atomico: tmp + os.replace (spec §12 regra 5)."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def import_marco1_seed(seed_votes: dict, entries_by_id: dict, repo_dir: Path) -> dict:
    """Re-chaveia votos do MARCO 1 (por entry-id) para identidade de conteudo.

    Voto com erro/block_id vazio NAO entra (deve re-chamar a API);
    entry que sumiu do manifest NAO entra.
    """
    votes: dict = {}
    for rid, vote in (seed_votes or {}).items():
        if not str((vote or {}).get("block_id") or "").strip():
            continue
        e = entries_by_id.get(str(rid))
        if not e:
            continue
        votes[content_key(e, repo_dir)] = dict(vote)
    return votes
```

Nota: `tmp.write_text`/`os.replace` — `Path.with_suffix(".json.tmp")` exige o nome exato usado no teste (`path.suffix + ".tmp"` produz `.json.tmp`). `re`, `defaultdict`, `normalize_match_text`, `Dict/List/Optional/Set`, `MotorContext` ficam usados nas partes 2-3 (Tasks 2-3) — se o linter reclamar de unused no commit desta task, mover os imports para a task que os usa.

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: 4 passed

- [ ] **Step 5: Guard de imports do motor continua verde**

Run: `python -m pytest tests/test_motor_contracts.py -v -k import`
Expected: PASS (se o guard vive em outro arquivo de teste, rodar `python -m pytest tests/ -q -k "guard or import_guard"`)

- [ ] **Step 6: Commit (se autorizado)**

```bash
git add src/builder/routing/motor/llm_vote.py tests/test_motor_llm_vote.py
git commit -m "feat(motor): cache material_curation por identidade de conteudo + seed MARCO 1 (FASE 3 T1)"
```

---

### Task 2: Série same-theme (escopo do voto)

**Files:**
- Modify: `src/builder/routing/motor/llm_vote.py`
- Test: `tests/test_motor_llm_vote.py`

**Interfaces:**
- Consumes: `is_out_of_disamb_scope(entry)` de `anchor_engine` (import LAZY dentro da função — evita ciclo), `normalize_match_text(s) -> str` de `src/builder/text/normalize.py`.
- Produces: `detect_same_theme_series(entries: List[dict]) -> Set[str]` — ids que são MEMBROS de série (mesmo card + mesmo stem sem dígitos, ≥2 ordinais distintos; porta `detect_series` do marco0, validada no MARCO 1).

- [ ] **Step 1: Testes que falham**

```python
from src.builder.routing.motor.llm_vote import detect_same_theme_series


def test_serie_same_theme_detecta_membros():
    entries = [
        _entry("d1", title="Exercicios Dafny 1", section="Verificacao"),
        _entry("d2", title="Exercicios Dafny 2", section="Verificacao"),
        _entry("solo", title="Prova Especial 9", section="Outra"),
    ]
    assert detect_same_theme_series(entries) == {"d1", "d2"}


def test_serie_exige_ordinais_distintos_e_card():
    entries = [
        _entry("a1", title="Lista 1", section="Card A"),
        _entry("a2", title="Lista 1", section="Card A"),      # mesmo ordinal: nao
        _entry("b1", title="Lista 1", section=""),            # sem card: nao
        _entry("b2", title="Lista 2", section=""),
    ]
    assert detect_same_theme_series(entries) == set()


def test_serie_exclui_fora_de_escopo_d6():
    entries = [
        _entry("t1", title="TDE 1", section="Verificacao", category="trabalhos"),
        _entry("t2", title="TDE 2", section="Verificacao", category="trabalhos"),
    ]
    assert detect_same_theme_series(entries) == set()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_llm_vote.py -v -k serie`
Expected: FAIL — `ImportError: cannot import name 'detect_same_theme_series'`

- [ ] **Step 3: Implementar**

```python
_DIGITS = re.compile(r"\d+")


def detect_same_theme_series(entries: List[dict]) -> Set[str]:
    """Membros de serie same-theme: mesmo card + mesmo stem, >=2 ordinais distintos.

    Porta detect_series do marco0 (metodologia validada no MARCO 1).
    Import lazy de is_out_of_disamb_scope: anchor_engine nao importa llm_vote,
    entao o lazy quebra o ciclo so por higiene de dependencia.
    """
    from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope

    groups: Dict[tuple, list] = defaultdict(list)
    for e in entries or []:
        if is_out_of_disamb_scope(e):
            continue
        rid = str(e.get("id") or "")
        name = str(e.get("title") or rid)
        nums = _DIGITS.findall(name)
        stem = _DIGITS.sub("", normalize_match_text(name)).strip()
        sec = str(e.get("source_section") or "").strip()
        if rid and nums and stem and sec:
            groups[(sec, stem)].append((rid, int(nums[-1])))
    members: Set[str] = set()
    for ms in groups.values():
        if len(ms) >= 2 and len({o for _, o in ms}) >= 2:
            members.update(rid for rid, _o in ms)
    return members
```

Atenção: conferir a assinatura real de `normalize_match_text` (`src/builder/text/normalize.py:8`) antes de usar — precisa devolver string case/acento-folded; se o nome/shape diferir, usar o fold equivalente do módulo `text/normalize` (whitelist do guard permite `text/*`). O marco0 usava `_fold` = NFKD + lower + sem acento.

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit (se autorizado)**

```bash
git add src/builder/routing/motor/llm_vote.py tests/test_motor_llm_vote.py
git commit -m "feat(motor): detect_same_theme_series — escopo do voto TIER 3 (FASE 3 T2)"
```

---

### Task 3: Prompt + LlmVoter (voto bounded, cache, cap)

**Files:**
- Modify: `src/builder/routing/motor/llm_vote.py`
- Test: `tests/test_motor_llm_vote.py`

**Interfaces:**
- Consumes: `MotorContext` (`.block_by_ref(ref)`, `.lessons_index`, `.course_name`), `GeminiClient.summarize_bundle(bundle_text, schema, system_instruction) -> BaseModel`, `get_gemini_client(config) -> Optional[GeminiClient]` (lazy).
- Produces:
  - `build_vote_prompt(entry: dict, window: List[str], ctx: MotorContext, markdown: str = "") -> str`
  - `match_window_ref(block_id_vote: str, window: List[str], ctx: MotorContext) -> Optional[str]`
  - `class LlmVoter` com `__init__(config: Optional[dict], cache_path: Path, repo_dir: Path, cap: int = DEFAULT_CAP, client=None)` (client injetável nos testes), `vote(entry, window, ctx, markdown="") -> Optional[str]` (ref DA JANELA ou None), `has_vote(entry) -> bool`, contadores `calls`, `skipped_cap`, `errors`.

- [ ] **Step 1: Testes que falham**

```python
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.llm_vote import (
    MD_PROMPT_CAP, LlmVoter, build_vote_prompt, match_window_ref,
)


def _ctx() -> MotorContext:
    blocks = [
        {"id": "bloco-01", "block_uuid": "uuid-1", "period_start": "2026-03-01",
         "period_end": "2026-03-07", "topic_text": "inducao",
         "sessions": [{"date": "2026-03-02"}]},
        {"id": "bloco-02", "block_uuid": "uuid-2", "period_start": "2026-03-08",
         "period_end": "2026-03-14", "topic_text": "hoare", "sessions": []},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map={},
        lessons_index={"2026-03-02": "inducao em listas"},
        course_name="Metodos Formais")


class FakeVotoResp:
    def __init__(self, block_id, confianca="alta", justificativa_curta="j"):
        self.block_id = block_id
        self.confianca = confianca
        self.justificativa_curta = justificativa_curta


class FakeClient:
    model = "fake-model"

    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []

    def summarize_bundle(self, bundle_text, schema, system_instruction):
        self.prompts.append((bundle_text, system_instruction))
        a = self.answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a


def test_build_vote_prompt_conteudo_e_cap():
    ctx = _ctx()
    e = _entry("e1", title="Lista Inducao", section="Card X")
    prompt = build_vote_prompt(e, ["bloco-01", "bloco-02"], ctx, "M" * 9999)
    assert "Lista Inducao" in prompt
    assert "bloco-01" in prompt and "bloco-02" in prompt
    assert "inducao em listas" in prompt          # roteiro via ctx.lessons_index
    assert prompt.count("M") == MD_PROMPT_CAP     # trecho capado (protocolo MARCO 1)


def test_match_window_ref_bounded():
    ctx = _ctx()
    win = ["bloco-01", "bloco-02"]
    assert match_window_ref("bloco-02", win, ctx) == "bloco-02"
    assert match_window_ref("uuid-1", win, ctx) == "bloco-01"   # casa por uuid
    assert match_window_ref("bloco-99", win, ctx) is None       # fora da janela
    assert match_window_ref("", win, ctx) is None


def test_voter_cache_hit_nao_chama_api(tmp_path: Path):
    ctx = _ctx()
    (tmp_path / "m.pdf").write_bytes(b"conteudo")
    e = _entry("e1", "m.pdf")
    cache = tmp_path / "cur.json"
    key = content_key(e, tmp_path)
    save_material_curation(cache, {"version": 1, "votes": {
        key: {"block_id": "bloco-02", "confianca": "alta"}}})
    client = FakeClient([])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01", "bloco-02"], ctx) == "bloco-02"
    assert voter.calls == 0 and client.prompts == []
    assert voter.has_vote(e)


def test_voter_chama_api_e_persiste(tmp_path: Path):
    ctx = _ctx()
    e = _entry("e1", title="Lista 1")
    cache = tmp_path / "cur.json"
    client = FakeClient([FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01", "bloco-02"], ctx) == "bloco-01"
    assert voter.calls == 1
    saved = load_material_curation(cache)
    assert saved["votes"]["e1"]["block_id"] == "bloco-01"
    assert saved["votes"]["e1"]["model"] == "fake-model"


def test_voter_voto_fora_da_janela_cacheia_mas_nao_ancora(tmp_path: Path):
    ctx = _ctx()
    e = _entry("e1")
    cache = tmp_path / "cur.json"
    client = FakeClient([FakeVotoResp("bloco-99")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01"], ctx) is None       # bounded: mantem FLAG
    assert load_material_curation(cache)["votes"]["e1"]["block_id"] == "bloco-99"
    # re-rodada: cache hit, sem nova chamada
    voter2 = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([]))
    assert voter2.vote(e, ["bloco-01"], ctx) is None
    assert voter2.calls == 0


def test_voter_cap_e_erro(tmp_path: Path):
    ctx = _ctx()
    cache = tmp_path / "cur.json"
    client = FakeClient([FakeVotoResp("bloco-01"), FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, cap=1, client=client)
    assert voter.vote(_entry("e1"), ["bloco-01"], ctx) == "bloco-01"
    assert voter.vote(_entry("e2"), ["bloco-01"], ctx) is None    # cap estourou
    assert voter.skipped_cap == 1
    # erro de API: nao persiste (proxima rodada re-tenta), errors conta
    client2 = FakeClient([RuntimeError("boom")])
    voter2 = LlmVoter({}, cache_path=tmp_path / "c2.json", repo_dir=tmp_path, client=client2)
    assert voter2.vote(_entry("e3"), ["bloco-01"], ctx) is None
    assert voter2.errors == 1
    assert load_material_curation(tmp_path / "c2.json")["votes"] == {}


def test_voter_sem_janela_nao_vota(tmp_path: Path):
    ctx = _ctx()
    client = FakeClient([FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=tmp_path / "c.json", repo_dir=tmp_path, client=client)
    assert voter.vote(_entry("e1"), [], ctx) is None
    assert voter.calls == 0 and client.prompts == []
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: FAIL — `ImportError: cannot import name 'LlmVoter'`

- [ ] **Step 3: Implementar**

```python
def _block_lines(window: List[str], ctx: MotorContext) -> str:
    out = []
    for ref in window:
        b = ctx.block_by_ref(ref) or {}
        did = str(b.get("id") or ref)
        datas = (f"{str(b.get('period_start') or '')[:10]}.."
                 f"{str(b.get('period_end') or '')[:10]}")
        top = str(b.get("topic_text") or b.get("primary_topic_label") or "").strip()
        rot = " ; ".join(
            ctx.lessons_index.get(str(s.get("date") or "")[:10], "")
            for s in (b.get("sessions") or [])
            if ctx.lessons_index.get(str(s.get("date") or "")[:10])
        )
        out.append(f"- {did} [{datas}] topico: {top[:90]}  roteiro: {rot[:120]}")
    return "\n".join(out)


def build_vote_prompt(entry: dict, window: List[str], ctx: MotorContext,
                      markdown: str = "") -> str:
    """Prompt do MARCO 1 generalizado (roteiro via ctx.lessons_index)."""
    md = (markdown or "")[:MD_PROMPT_CAP]
    return (
        f"MATERIAL:\n"
        f"  titulo: {entry.get('title')}\n"
        f"  categoria: {entry.get('category')}\n"
        f"  secao/card do Moodle: {entry.get('source_section') or '(sem secao)'}\n"
        f"  trecho do conteudo:\n---\n{md or '(sem markdown extraido)'}\n---\n\n"
        f"BLOCOS CANDIDATOS:\n{_block_lines(window, ctx)}\n\n"
        f"Qual bloco? Responda no schema."
    )


def match_window_ref(block_id_vote: str, window: List[str],
                     ctx: MotorContext) -> Optional[str]:
    """Voto -> ref da janela (bounded). Fora da janela = None (mantem FLAG)."""
    v = str(block_id_vote or "").strip()
    if not v:
        return None
    for ref in window:
        b = ctx.block_by_ref(ref) or {}
        if v in (str(ref), str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            return ref
    return None


class LlmVoter:
    """Voto Gemini cacheado com cap por rodada. vote() -> ref da janela ou None.

    client injetavel (testes); em producao lazy via get_gemini_client (spec §4).
    Erro de API NAO e cacheado (rodada seguinte re-tenta); voto fora da janela
    E cacheado (voto real, so nao ancora).
    """

    def __init__(self, config: Optional[dict], cache_path: Path, repo_dir: Path,
                 cap: int = DEFAULT_CAP, client=None):
        self._config = config or {}
        self._cache_path = Path(cache_path)
        self._repo_dir = Path(repo_dir)
        self._cap = int(cap)
        self._client = client
        self._client_loaded = client is not None
        self._data = load_material_curation(self._cache_path)
        self.calls = 0          # chamadas API na rodada (cache hit nao conta)
        self.skipped_cap = 0    # escopo sem voto por cap estourado
        self.errors = 0

    def _get_client(self):
        if not self._client_loaded:
            from src.builder.runtime.gemini_client import get_gemini_client  # lazy
            self._client = get_gemini_client(self._config)
            self._client_loaded = True
        return self._client

    def has_vote(self, entry: dict) -> bool:
        return content_key(entry, self._repo_dir) in self._data["votes"]

    def vote(self, entry: dict, window: List[str], ctx: MotorContext,
             markdown: str = "") -> Optional[str]:
        if not window:
            return None                      # sem-janela NAO vota (spec §12)
        key = content_key(entry, self._repo_dir)
        cached = self._data["votes"].get(key)
        if cached is None:
            if self.calls >= self._cap:
                self.skipped_cap += 1
                return None
            client = self._get_client()
            if client is None:
                return None                  # sem chave -> mantem FLAG
            prompt = build_vote_prompt(entry, window, ctx, markdown)
            system = SYSTEM_TEMPLATE.format(course=ctx.course_name or "curso")
            self.calls += 1
            try:
                voto = client.summarize_bundle(prompt, Voto, system)
            except Exception:  # noqa: BLE001 — voto falhou: FLAG fica, sem cache
                self.errors += 1
                return None
            cached = {
                "block_id": str(voto.block_id).strip(),
                "confianca": str(voto.confianca).strip(),  # auditoria; nunca gate
                "justificativa": str(voto.justificativa_curta)[:200],
                "model": getattr(client, "model", ""),
            }
            self._data["votes"][key] = cached
            save_material_curation(self._cache_path, self._data)
        return match_window_ref(str(cached.get("block_id") or ""), window, ctx)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: 14 passed

- [ ] **Step 5: Suite do motor inteira verde**

Run: `python -m pytest tests/ -q -k motor`
Expected: todos PASS, 0 failed

- [ ] **Step 6: Commit (se autorizado)**

```bash
git add src/builder/routing/motor/llm_vote.py tests/test_motor_llm_vote.py
git commit -m "feat(motor): LlmVoter — voto Gemini bounded a janela, cache, cap (FASE 3 T3)"
```

---

### Task 4: Wiring TIER 3 no AnchorEngine (aceitação cega no escopo)

**Files:**
- Modify: `src/builder/routing/motor/contracts.py` (adicionar Protocol ao fim)
- Modify: `src/builder/routing/motor/anchor_engine.py`
- Test: `tests/test_motor_anchor_engine.py` (acrescentar classe de testes)

**Interfaces:**
- Consumes: `LlmVoterProtocol.vote(entry, window, ctx, markdown="") -> Optional[str]` (Task 3 satisfaz).
- Produces: `AnchorEngine.__init__(voter: Optional[LlmVoterProtocol] = None, series_ids: Optional[Set[str]] = None)`; `resolve` inalterado na assinatura. Com voter: decisão FLAGADA ou entry∈series_ids ⇒ voto; voto válido ⇒ `block_ref=voto`, `band="media"`, `flag=False`, `provider="llm"`, `method="llm"`. `voter=None` ⇒ **byte-idêntico** à FASE 2.

- [ ] **Step 1: Testes que falham** (acrescentar em `tests/test_motor_anchor_engine.py`; usar os fixtures/estilo já existentes no arquivo — os stubs abaixo monkeypatcham `resolve_window`/`disambiguate` do módulo para isolar o hook)

```python
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor import anchor_engine as ae


class _FakeVoter:
    def __init__(self, answer):
        self.answer = answer
        self.seen = []

    def vote(self, entry, window, ctx, markdown=""):
        self.seen.append(str(entry.get("id")))
        return self.answer


def _tier3_ctx():
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01"}, {"id": "bloco-02"}],
        card_block_map={}, lessons_index={})


def _stub_cascade(monkeypatch, *, flag: bool, band: str = "baixa"):
    monkeypatch.setattr(ae, "resolve_window",
                        lambda e, c: (["bloco-01", "bloco-02"], "topic"))
    monkeypatch.setattr(
        ae, "disambiguate",
        lambda e, w, c, m, provider="": AnchorDecision(
            block_ref="bloco-01", conf=0.9 if band == "alta" else 0.2,
            band=band, flag=flag, window=list(w)))


def test_tier3_flagged_voto_valido_ancora_media(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert d.block_ref == "bloco-02"
    assert d.band == "media" and d.flag is False
    assert d.provider == "llm" and d.method == "llm"
    assert voter.seen == ["e1"]


def test_tier3_voto_none_mantem_flag(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    d = ae.AnchorEngine(voter=_FakeVoter(None)).resolve(
        {"id": "e1", "category": "m"}, _tier3_ctx())
    assert d.block_ref == "bloco-01" and d.flag is True and d.provider == "topic"


def test_tier3_sem_voter_byte_identico(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    d0 = ae.AnchorEngine().resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert d0.block_ref == "bloco-01" and d0.flag is True and d0.band == "baixa"


def test_tier3_nao_flagado_fora_de_serie_nao_vota(monkeypatch):
    _stub_cascade(monkeypatch, flag=False, band="alta")
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert voter.seen == [] and d.block_ref == "bloco-01" and d.band == "alta"


def test_tier3_membro_de_serie_vota_mesmo_sem_flag(monkeypatch):
    _stub_cascade(monkeypatch, flag=False, band="alta")
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter, series_ids={"e1"}).resolve(
        {"id": "e1", "category": "m"}, _tier3_ctx())
    assert voter.seen == ["e1"]
    assert d.block_ref == "bloco-02" and d.band == "media" and d.provider == "llm"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_anchor_engine.py -v -k tier3`
Expected: FAIL — `TypeError: AnchorEngine.__init__() got an unexpected keyword argument 'voter'`

- [ ] **Step 3: Implementar**

Em `contracts.py`, ao fim (padrão dos Protocols existentes):

```python
class LlmVoterProtocol(Protocol):
    """TIER 3: voto LLM bounded a janela; None = sem voto -> mantem decisao/FLAG."""
    def vote(self, entry: dict, window: List[str], ctx: MotorContext,
             markdown: str = "") -> Optional[str]: ...
```

Em `anchor_engine.py` (substituir a classe; imports: acrescentar `Set` ao `typing` e `LlmVoterProtocol` ao import de contracts):

```python
class AnchorEngine:
    """resolve(entry, ctx) -> AnchorDecision | None (None = funil-piso).

    TIER 3 (FASE 3): voter opcional — voter=None => saida byte-identica as
    FASES 0-2. Escopo do voto = decisao FLAGADA ∪ membro de serie same-theme
    (spec §3 TIER 3); aceitacao cega: band "media", flag=False, provider="llm"
    (spec §12 regra 3). Sem-janela nunca chega ao voto (funil antes).
    """

    def __init__(self, voter: Optional["LlmVoterProtocol"] = None,
                 series_ids: Optional[Set[str]] = None):
        self._voter = voter
        self._series_ids = frozenset(series_ids or ())

    def resolve(self, entry: dict, ctx: MotorContext, markdown: str = "") -> Optional[AnchorDecision]:
        if is_out_of_disamb_scope(entry):
            return None
        window, provider = resolve_window(entry, ctx)
        if not window:
            return None  # sem janela -> funil (invariante ANCHOR-ONLY)
        decision = disambiguate(entry, window, ctx, markdown, provider=provider)
        if not decision.block_ref:
            return None  # nenhum ref da janela resolve -> funil honesto
        decision.provider = provider
        if self._voter is not None and (
                decision.flag or str(entry.get("id") or "") in self._series_ids):
            voted = self._voter.vote(entry, window, ctx, markdown)
            if voted:
                decision.block_ref = voted
                decision.band = "media"
                decision.flag = False
                decision.provider = "llm"
                decision.method = "llm"
        return decision
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_motor_anchor_engine.py tests/test_motor_llm_vote.py tests/test_motor_contracts.py -v`
Expected: todos PASS (novos + antigos — os antigos provam o byte-idêntico com voter=None)

- [ ] **Step 5: Regressão determinística (4 probes, sem API)**

Run (cada um exit 0):
```bash
python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py
```
Expected: 4× PASS — o hook TIER 3 sem voter não muda NENHUM número.

- [ ] **Step 6: Commit (se autorizado)**

```bash
git add src/builder/routing/motor/contracts.py src/builder/routing/motor/anchor_engine.py tests/test_motor_anchor_engine.py
git commit -m "feat(motor): hook TIER 3 no AnchorEngine — aceitacao cega no escopo flagged∪same-theme (FASE 3 T4)"
```

---

### Task 5: Régua HARD `scripts/fase3_prova_LLM_MF.py` (dry-run primeiro)

**Files:**
- Create: `scripts/fase3_prova_LLM_MF.py`

**Interfaces:**
- Consumes: `build_context`, `_md_text`, `display_of`, `collapse` de `scripts/fase0_prova_motor_MF.py` (DRY — mesmo padrão do marco1 que importava do marco0); `AnchorEngine`, `is_out_of_disamb_scope`; tudo do `llm_vote`.
- Produces: régua exit 0 (PASS) / 1 (FAIL ou INCOMPLETO) / 2 (repo/chave ausente); flags `--repo --gold --cap --dry-run`.

- [ ] **Step 1: Escrever o script completo**

```python
#!/usr/bin/env python3
"""FASE 3 — prova do TIER 3 (voto LLM) vs ground_truth_MF.csv (READ-ONLY no repo-tutor).

Numero do aceite (spec §7 FASE 3): lift >= +4 acertos no escopo do voto
(flagged ∪ same-theme, com janela e decisao) SEM novo confiante-errado
(band alta + errado, medido GLOBAL) — era +5 no MARCO 1 cru; regras finais:
sem-janela NAO vota. Autoconfianca do LLM ignorada (nunca lida por gate).

Cache: docs/reports/material_curation_MF.json (identidade de conteudo md5;
seed = docs/reports/marco1_votes_MF.json re-chaveado na primeira rodada).
O repo-tutor NAO recebe escrita (disciplina READ-ONLY; sidecar = FASE 4).
Cap=20 chamadas/rodada: escopo maior que o cap -> INCOMPLETO exit 1;
re-rodar acumula cache ate completar.

PRE-GATE: rode scripts/audit_gold_freshness.py antes de medir.

Uso: python scripts/fase3_prova_LLM_MF.py [--repo PATH] [--gold CSV] [--cap N] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.builder.routing.motor.anchor_engine import (                   # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)
from src.builder.routing.motor.llm_vote import (                        # noqa: E402
    LlmVoter, build_vote_prompt, detect_same_theme_series,
    import_marco1_seed, save_material_curation,
)
from fase0_prova_motor_MF import (                                      # noqa: E402
    _md_text, build_context, collapse, display_of,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
CACHE = ROOT / "docs" / "reports" / "material_curation_MF.json"
SEED = ROOT / "docs" / "reports" / "marco1_votes_MF.json"
LIFT_MIN = 4          # spec §7 FASE 3 (era +5 no MARCO 1 cru; sem-janela nao vota)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    ap.add_argument("--cap", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true", help="monta prompts, nao chama API")
    args = ap.parse_args()
    repo, gold_path = Path(args.repo), Path(args.gold)

    if not repo.is_dir():
        print(f"ERRO: repo MF nao encontrado: {repo}", file=sys.stderr)
        return 2

    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    course_name = str((man.get("course") or {}).get("course_name") or "")
    entries = man.get("entries") or []
    byid = {str(e.get("id")): e for e in entries}
    ctx = build_context(repo, course_name)

    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    scope_rows = [r for r in rows
                  if byid.get(r["id"]) and not is_out_of_disamb_scope(byid[r["id"]])]

    # 1) baseline deterministico + escopo do voto
    eng0 = AnchorEngine()
    series = detect_same_theme_series(entries)
    base = {}                    # rid -> (decision, markdown)
    vote_rows = []
    for r in scope_rows:
        e = byid[r["id"]]
        md = _md_text(repo, e)
        d = eng0.resolve(e, ctx, markdown=md)
        if d is None:
            continue             # sem janela/decisao -> funil; NAO vota (spec §12)
        base[r["id"]] = (d, md)
        if d.flag or r["id"] in series:
            vote_rows.append(r)

    n_flag = sum(1 for r in vote_rows if base[r["id"]][0].flag)
    print(f"FASE 3 — escopo do voto: {len(vote_rows)} rows "
          f"({n_flag} flagged; serie same-theme total={len(series)})")

    if args.dry_run:
        for r in vote_rows[:5]:
            d, md = base[r["id"]]
            print(f"\n===== {r['id']} =====")
            print(build_vote_prompt(byid[r["id"]], d.window, ctx, md)[:900])
        print(f"\n(dry-run: {len(vote_rows)} prompts montaveis; nada chamado)")
        return 0

    # 2) seed do MARCO 1 (so na primeira rodada, cache ainda nao existe)
    if not CACHE.is_file() and SEED.is_file():
        seed = import_marco1_seed(
            json.loads(SEED.read_text(encoding="utf-8")), byid, repo)
        save_material_curation(CACHE, {"version": 1, "votes": seed})
        print(f"  seed MARCO 1 importado: {len(seed)} votos -> {CACHE.name}")

    # 3) rodada com voto (cache acumula entre rodadas)
    cfg_path = Path.home() / ".gpt_tutor_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    voter = LlmVoter(cfg, cache_path=CACHE, repo_dir=repo, cap=args.cap)
    eng1 = AnchorEngine(voter=voter, series_ids=series)

    d_ok = l_ok = 0
    res_det, res_llm = {}, {}
    cw = []
    for r in scope_rows:
        got = base.get(r["id"])
        if got is None:
            continue
        d0, md = got
        e = byid[r["id"]]
        d1 = eng1.resolve(e, ctx, markdown=md)
        pred0 = display_of(ctx, d0.block_ref)
        pred1 = display_of(ctx, d1.block_ref) if d1 else pred0
        ok0, ok1 = pred0 == r["true_block_id"], pred1 == r["true_block_id"]
        res_det[r["id"]], res_llm[r["id"]] = ok0, ok1
        if d1 and d1.band == "alta" and not d1.flag and not ok1:
            cw.append((r["id"], pred1, r["true_block_id"]))
        if r in vote_rows:
            d_ok += ok0
            l_ok += ok1
            mark0, mark1 = ("ok" if ok0 else "X "), ("ok" if ok1 else "X ")
            print(f"  {r['id'][:46]:46} det={pred0:9}{mark0} "
                  f"llm={pred1:9}{mark1} true={r['true_block_id']:9} "
                  f"[{d1.method if d1 else '-'}]")

    pend = [r["id"] for r in vote_rows if not voter.has_vote(byid[r["id"]])]
    lift = l_ok - d_ok
    ok_g, tot_g = collapse(res_llm, scope_rows)

    print("=" * 70)
    print(f"FASE 3/TIER 3 — MF  chamadas API nesta rodada: {voter.calls}  "
          f"erros: {voter.errors}  sem-voto (cap): {voter.skipped_cap}")
    print(f"  escopo do voto: deterministico {d_ok}/{len(vote_rows)} -> "
          f"LLM {l_ok}/{len(vote_rows)}  lift={lift:+d} (piso +{LIFT_MIN})")
    print(f"  global escopo-disamb par-colapsado c/ voto: {ok_g}/{tot_g}")
    print(f"  confiante-e-errado (band alta, global): {len(cw)} {cw}")
    if pend:
        print(f"  INCOMPLETO: {len(pend)} sem voto (cap/erro) — re-rode p/ acumular: {pend}")
    print("=" * 70)

    ok_lift = lift >= LIFT_MIN
    ok_cw = not cw
    ok_full = not pend
    verdict = ok_lift and ok_cw and ok_full
    print(f"VEREDITO FASE 3: {'PASS' if verdict else 'FAIL'} "
          f"(lift={ok_lift} confErrado0={ok_cw} completo={ok_full})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Validar o dry-run (sem API, sem chave)**

Run: `python scripts/fase3_prova_LLM_MF.py --dry-run`
Expected: exit 0; imprime `escopo do voto: N rows` com N > 0 (fila MF tem 37 flags; escopo com decisão deve ficar próximo disso) e até 5 prompts contendo `MATERIAL:` e `BLOCOS CANDIDATOS:`.
Se N == 0: BUG (provável no escopo/série) — investigar antes de seguir.

- [ ] **Step 3: Suite completa verde**

Run: `python -m pytest -q`
Expected: ≥1724 passed, 0 failed (novos testes somam ao total)

- [ ] **Step 4: Commit (se autorizado)**

```bash
git add scripts/fase3_prova_LLM_MF.py
git commit -m "feat(motor): regua HARD fase3_prova_LLM_MF — lift do voto TIER 3 vs gold MF (FASE 3 T5)"
```

---

### Task 6: Rodada real (API), regressão total e report de fechamento

Esta task GASTA API (~escopo − seed ≈ 20-40 chamadas, ≤ US$1) e depende de `GEMINI_API_KEY`/config. **Confirmar com o user antes da primeira rodada real.**

**Files:**
- Create: `docs/reports/2026-07-09-fase3-llm-report.md`
- Modify: `docs/reports/pendencias.md` (tracker — entrada FASE 3)
- (gerado) `docs/reports/material_curation_MF.json` — cache commitável (votos são insumo de medição, como `marco1_votes_MF.json`)

**Interfaces:**
- Consumes: Task 5 (régua) + chave Gemini.
- Produces: número oficial da FASE 3 + veredito go-forward.

- [ ] **Step 1: Pré-gate de frescor do gold**

Run: `python scripts/audit_gold_freshness.py`
Expected: golds FRESCOS (falso-alarme conhecido: SO `lista2` ADMIN_TRUE). Se HARD drift no MF: PARAR e reportar ao user — não medir contra gold stale.

- [ ] **Step 2: Rodada 1 do voto (seed + até 20 chamadas)**

Run: `python scripts/fase3_prova_LLM_MF.py`
Expected: imprime `seed MARCO 1 importado: ~15-18 votos`, chamadas ≤ 20. Se `INCOMPLETO` → Step 3; se completo → Step 4.

- [ ] **Step 3: Rodadas adicionais até completar (cache acumula)**

Run: `python scripts/fase3_prova_LLM_MF.py` (repetir enquanto `INCOMPLETO`; cada rodada ≤ 20 chamadas novas)
Expected: em 1-2 re-rodadas, `completo=True` e veredito final PASS ou FAIL.

- [ ] **Step 4: Interpretar o veredito**
  - **PASS** (lift ≥ +4, confErrado 0): FASE 3 provada; seguir Step 5.
  - **FAIL honesto** (lift < +4): NÃO iterar prompt para grão-de-semana (spec §12 regra 4 — classe provada não-conversível). Reportar números reais ao user com a decisão: aceitar lift menor (revisar piso com sign-off) OU reverter GO (flags → fila humana + dívida #1 band). O report do Step 5 é escrito do mesmo jeito, com o veredito honesto.

- [ ] **Step 5: Regressão total (4 probes + suite + novo probe)**

Run:
```bash
python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py && python scripts/fase3_prova_LLM_MF.py && python -m pytest -q
```
Expected: 5× PASS + suite 0 failed. (fase0-2 rodam SEM voter — números FASE 2 intactos por construção.)

- [ ] **Step 6: Report de fechamento** — criar `docs/reports/2026-07-09-fase3-llm-report.md` com: números finais (lift, chamadas totais, custo estimado, confiante-errado, acc global par-colapsada antes/depois), tabela det vs llm por row do escopo, decisões de calibração tomadas na fase (o que ficou do §12: sem-janela não vota — classe plano.pdf documentada como perdida), riscos residuais com dono (ex.: prompt generalizado vs MARCO 1; série same-theme votando sobre band alta — medido nesta fase), e o que fica para FASE 4 (sidecar `material_curation.json` no repo-tutor via reprocess, background-thread na GUI, prune stale por chave órfã, cap/opt-in por flag de curso via `SubjectProfile.feature_flags`).

- [ ] **Step 7: Tracker + grafo**

Run: `graphify update .`
Atualizar `docs/reports/pendencias.md`: FASE 3 com número final; dívida #1 (band no ramo flagado) fica N/A-se-PASS (TIER 3 consome flag, não band) — registrar o desfecho.

- [ ] **Step 8: Commit final (se autorizado)**

```bash
git add docs/reports/2026-07-09-fase3-llm-report.md docs/reports/material_curation_MF.json docs/reports/pendencias.md
git commit -m "docs(motor): fechamento FASE 3 — voto TIER 3 medido no gold MF"
```

- [ ] **Step 9: Gate de arquivamento** — SÓ se plano 100% executado e gate verde: `git mv docs/superpowers/plans/2026-07-09-fase3-voto-llm.md docs/superpowers/plans/Feitos/` + tracker. Se FAIL no Step 4, NÃO arquivar — o plano fica aberto até a decisão do user.

---

## Self-Review (executado na escrita)

1. **Cobertura do spec:** §12 regra 1 (autoconfiança ignorada) → Task 3 (`confianca` gravada, nunca lida); regra 2 (bounded) → `match_window_ref` + teste; regra 3 (aceitar cego, band media, provider=llm) → Task 4; regra 4 (não iterar grão-de-semana) → Task 6 Step 4; regra 5 (cache md5/pair_key, atomic, seed) → Task 1 (prune stale de chaves órfãs adiado p/ FASE 4 — documentado no report Task 6, quando o sidecar entra no repo); regra 6 (cap=20, opt-in por curso) → cap na Task 3 (opt-in por flag = FASE 4, integração); §7 número (+4 sem novo conf-errado) → Task 5/6; sem-janela não vota → engine retorna None antes do hook + teste `test_voter_sem_janela_nao_vota`.
2. **Placeholders:** nenhum TBD; todo step de código tem o código; comandos com expected.
3. **Consistência de tipos:** `LlmVoter.vote` ↔ `LlmVoterProtocol.vote` ↔ `_FakeVoter.vote` mesmas assinaturas; `AnchorEngine(voter=, series_ids=)` usado idêntico em Task 4 testes e Task 5 script; `content_key(entry, repo_dir)` mesma ordem em todos os call-sites.
4. **Riscos sinalizados ao executor:** (a) assinatura real de `normalize_match_text` — conferir na Task 2; (b) nome exato do teste de guard de imports — Task 1 Step 5 tem fallback de busca; (c) contagem `14 passed`/`7 passed` é indicativa — o que importa é 0 failed.
