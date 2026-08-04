# Rollout flag-ON Trilha 1 (MF → SO → TCC · audit IA/ES2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ligar `use_anchor_engine`+`use_llm_voter` no MF (com seed do cache F3), validar com gate HARD-drift 0 + régua completa, expandir para SO e TCC com medição por curso, auditar IA/ES2 (report-only, sem flip).

**Architecture:** Flags vivem em `SubjectProfile.feature_flags` (`%APPDATA%\GPTTutorGenerator\subjects.json`) e são injetadas FLAT em `builder.options` por `_build_options_from_config` (src/ui/app.py:83). O reprocess headless (`scripts/reprocess_assignments.py`) lê options do `manifest.json` do repo-tutor — flags NÃO chegam lá; Task 1 adiciona injeção `--flags`. Motor lê `options.get("use_anchor_engine")` (pedagogical_regeneration.py:446) e `options.get("use_llm_voter")` (idem :53).

**Tech Stack:** Python 3, pytest, PowerShell, git (repos-tutor como rede de segurança).

## Global Constraints

- Flag-OFF byte-idêntico; régua completa (7 probes + suite) antes/depois de qualquer mudança do motor.
- FAIL = resultado honesto; PROIBIDO re-tuning pra passar régua. Pisos em fração exata (48/58, 51/58, 4/8).
- Medição só com `python scripts/audit_gold_freshness.py` exit 0 e hard=0 (ZERO_OVERLAP = soft informativo).
- D-E: provider nunca chuta. Gold muda SÓ com evidência + autorização do user.
- Lógica nova SÓ em motor/scripts, NUNCA `engine.py` (guard AST `test_motor_import_guard`).
- READ-ONLY nos repos-tutor EXCETO o reprocess autorizado do rollout; snapshot git ANTES de cada reprocess.
- UTF-8 shim (`sys.stdout.reconfigure`) em scripts tocados; NUNCA commitar `.claude/settings*.json`/`CLAUDE.md`.
- Cutover EXCLUÍDO desta campanha (decisão user 2026-08-03). Merge → main só no fim da refatoração.
- Após mudanças de código: `graphify update .`.
- Commits terminam com `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

**Números de referência (régua, valores aceitos):**
fase0 48/58 (82.8%) · contencioso 0 · cw 1 | fase1 recall 9/10 | fase2_SO 45.2% / 0 colisão / cw 0 | fase2_TCC pinos 5/5 + 83.3% / cw 0 | fase3 lift +3 / 0 chamadas API | fase4 det 48/58 cw1 + voter 51/58 (87.9%) cw0 calls=0 | fase5 target 4/8 cw0 (t1→bloco-11 alta · t1-thy→bloco-11 alta · t2→bloco-16 media+FLAG · revisao-p1-gabarito→bloco-07 funil) | suite 1816 passed / 4 skipped (Task 1 adiciona testes: passa a 1816+N).

**Piloto MF (referência do gate, dry-run 2026-07-22, PRÉ-F5b):** 67 entries → 51 temporal (15 alta/36 media; providers 9 manual/6 labels/36 llm) + 11 pinos (motor respeita e limpa temporal) + 5 TIER-2 fora-de-escopo. Voter: 36 hits cache, 0 chamadas API, fila humana 0. PÓS-F5b esperado: t1-2026-1/t1-2026-1-thy/t2-2026-1 GANHAM temporal via tier2 (blocos 11/11/16) → **54 temporal**; `revisao-p1-gabarito` fica no funil (bloco-07, correto por gold); `plano` = funil DELIBERADO (sem temporal).

**Paths:**
- Projeto: `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator`
- MF: `C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor` (índice em `course/.timeline_index.json`)
- SO: `C:/Users/Humberto/Documents/GitHub/Sistemas-Operacionais-Tutor` (JÁ tem `material_curation.json` na raiz)
- TCC: `C:/Users/Humberto/Documents/GitHub/TCC-Tutor` (SEM curation na raiz → voter pode pagar até 20 votos, cap built-in)
- Subjects: `%APPDATA%\GPTTutorGenerator\subjects.json` (chaves: `Metodos-Formais`, `Sistemas Operacionais`, `Teoria da Computabilidade e Complexidade`)
- Scratchpad da sessão: usar o diretório de scratchpad indicado pelo harness para scripts one-off e backups.

---

### Task 1: Injeção `--flags` no reprocess headless

**Files:**
- Modify: `scripts/reprocess_assignments.py`
- Test: `tests/test_reprocess_flags.py` (novo)

**Interfaces:**
- Produces: CLI `python scripts/reprocess_assignments.py --flags use_anchor_engine,use_llm_voter <repo>...` — merge `{flag: True}` nas options lidas do manifest ANTES de construir o RepoBuilder. Funções novas: `_apply_flags(options: dict, flag_names: list) -> None` e `_parse_argv(argv: list) -> tuple[list, list]` (flags, patterns). `reprocess(repo: Path, flags: list) -> None` ganha o parâmetro.

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_reprocess_flags.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reprocess_assignments as ra  # noqa: E402


def test_apply_flags_marca_true_e_preserva_options():
    opts = {"image_format": "png"}
    ra._apply_flags(opts, ["use_anchor_engine", "use_llm_voter"])
    assert opts["use_anchor_engine"] is True
    assert opts["use_llm_voter"] is True
    assert opts["image_format"] == "png"


def test_apply_flags_vazio_nao_muda_nada():
    opts = {"a": 1}
    ra._apply_flags(opts, [])
    assert opts == {"a": 1}


def test_parse_argv_com_flags():
    flags, pats = ra._parse_argv(["--flags", "use_anchor_engine,use_llm_voter", "C:/x"])
    assert flags == ["use_anchor_engine", "use_llm_voter"]
    assert pats == ["C:/x"]


def test_parse_argv_sem_flags_e_retrocompativel():
    flags, pats = ra._parse_argv(["C:/x", "C:/y"])
    assert flags == []
    assert pats == ["C:/x", "C:/y"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_reprocess_flags.py -v`
Expected: FAIL — `AttributeError: module 'reprocess_assignments' has no attribute '_apply_flags'`

- [ ] **Step 3: Implementação mínima**

Em `scripts/reprocess_assignments.py`: adicionar UTF-8 shim após os imports (regra da casa), as duas funções, e usar em `reprocess`/`main`:

```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _apply_flags(options: dict, flag_names: list) -> None:
    """Merge {flag: True} nas options (flags ficam FLAT, como _build_options_from_config)."""
    for name in flag_names:
        options[str(name)] = True


def _parse_argv(argv: list) -> tuple[list, list]:
    """['--flags', 'a,b', pat...] -> (['a','b'], [pat...]); sem --flags -> ([], argv)."""
    pats = list(argv)
    flags: list = []
    if pats and pats[0] == "--flags":
        if len(pats) < 2:
            return [], []
        flags = [f for f in pats[1].split(",") if f]
        pats = pats[2:]
    return flags, pats
```

Em `reprocess(repo, flags)`: após `options = manifest.get("options", {}) or {}`, chamar `_apply_flags(options, flags)` e, se flags, imprimir `[flags] {repo.name}: {', '.join(flags)}`. Em `main`: `flags, argv = _parse_argv(argv)` no topo; `reprocess(repo, flags)` no loop.

- [ ] **Step 4: Rodar testes — verde + retrocompatibilidade**

Run: `python -m pytest tests/test_reprocess_flags.py -v` → 4 PASS.
Run: `python -m pytest -q` → suite completa verde (1816+4 passed / 4 skipped).

- [ ] **Step 5: Commit + graphify**

```bash
git add scripts/reprocess_assignments.py tests/test_reprocess_flags.py
git commit -m "feat(rollout): --flags no reprocess headless (injecao use_anchor_engine/use_llm_voter)"
graphify update .
```

---

### Task 2: Snapshot git MF + seed cache F3 + flip flags MF

**Files:**
- Create: `C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/material_curation.json` (cópia do seed)
- Modify: `%APPDATA%\GPTTutorGenerator\subjects.json` (fora do repo; backup antes)

**Interfaces:**
- Consumes: seed `docs/reports/material_curation_MF.json` (existe, verificado).
- Produces: MF com cache F3 na raiz + `feature_flags = {"use_anchor_engine": true, "use_llm_voter": true}` em `Metodos-Formais`. Repo MF com working tree LIMPO (snapshot commitado).

- [ ] **Step 1: Snapshot git do MF (rede de segurança — repo está sujo, ~35 arquivos do sync headless F5b)**

```powershell
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" add -A
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" commit -m "snapshot pre-rollout flag-ON (estado flag-OFF + sync headless F5b)"
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" log --oneline -1
```

Expected: commit criado; `git status --porcelain` vazio.

- [ ] **Step 2: Seed do cache F3 + validação**

```powershell
Copy-Item "C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/material_curation_MF.json" "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/material_curation.json"
python -c "import json; d=json.load(open('C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor/material_curation.json', encoding='utf-8')); print(type(d).__name__, len(d))"
```

Expected: JSON parseia; imprime tipo e contagem (>0). Sem cache o voter re-paga até 20 votos — seed é PRÉ-REQUISITO do flip (pendencias 2026-07-22).

- [ ] **Step 3: Backup + flip flags no subjects.json**

```powershell
Copy-Item "$env:APPDATA\GPTTutorGenerator\subjects.json" "<scratchpad>\subjects.json.bak"
python - <<'EOF'
import json, os
from pathlib import Path
p = Path(os.environ["APPDATA"]) / "GPTTutorGenerator" / "subjects.json"
data = json.loads(p.read_text(encoding="utf-8"))
data["Metodos-Formais"]["feature_flags"] = {"use_anchor_engine": True, "use_llm_voter": True}
p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("flags MF:", data["Metodos-Formais"]["feature_flags"])
EOF
```

(No PowerShell, salvar o trecho python como `<scratchpad>\flip_mf.py` e rodar `python <scratchpad>\flip_mf.py`.)
Expected: `flags MF: {'use_anchor_engine': True, 'use_llm_voter': True}`. Formato preservado (indent=2, ensure_ascii=False — mesmo do `SubjectStore.save`).

- [ ] **Step 4: Verificar round-trip**

```powershell
python -c "import json,os;from pathlib import Path;d=json.loads((Path(os.environ['APPDATA'])/'GPTTutorGenerator'/'subjects.json').read_text(encoding='utf-8'));print(sorted(d.keys()));print(d['Metodos-Formais']['feature_flags'])"
```

Expected: as 5 matérias presentes; flags do MF = ambas true. (Sem commit — subjects.json é AppData, fora de git.)

---

### Task 3: Reprocess MF flag-ON + gate HARD-drift

**Files:**
- Create: `<scratchpad>/gate_mf.py` (gate one-off, não entra no repo)
- Modify (efeito): `Metodos-Formais-Tutor/manifest.json` + índices regenerados

**Interfaces:**
- Consumes: Task 1 (`--flags`), Task 2 (seed + snapshot).
- Produces: MF com `temporal_*` reais gravados; log do reprocess em `<scratchpad>/reprocess_mf.log`; veredito do gate (PASS/FAIL) com contagens.

- [ ] **Step 1: Rodar reprocess flag-ON (log capturado)**

```powershell
python scripts/reprocess_assignments.py --flags use_anchor_engine,use_llm_voter "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" *>&1 | Tee-Object "<scratchpad>\reprocess_mf.log"
```

Expected: `[flags] Metodos-Formais-Tutor: use_anchor_engine, use_llm_voter`, depois `[ok] Metodos-Formais-Tutor: bloco X/Y -> X'/Y'` sem traceback. Backup `manifest.json.bak` criado pelo script.

- [ ] **Step 2: Gate — escrever e rodar `<scratchpad>/gate_mf.py`**

```python
# gate_mf.py — HARD-drift gate do rollout MF (compara com piloto 2026-07-22 ajustado pós-F5b)
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor")
m = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
idx = json.loads((REPO / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
uuid2disp = {}
for b in idx.get("blocks", []):
    for key in ("uuid", "block_uuid"):
        if b.get(key):
            uuid2disp[b[key]] = b.get("id") or b.get("display_id") or ""

entries = m.get("entries", [])
temporal = [e for e in entries if e.get("temporal_block_id")]
pinos = [e for e in entries if e.get("manual_timeline_block_id")]
tkeys = Counter(k for e in entries for k in e if str(k).startswith("temporal"))
print("total entries:", len(entries))
print("com temporal_block_id:", len(temporal))
print("com pino manual:", len(pinos))
print("campos temporal_*:", dict(tkeys))

def disp(e):
    t = str(e.get("temporal_block_id") or "")
    return uuid2disp.get(t, t)

alvo = {"t1-2026-1": "bloco-11", "t1-2026-1-thy": "bloco-11", "t2-2026-1": "bloco-16"}
fails = []
byid = {e.get("id"): e for e in entries}
for eid, want in alvo.items():
    e = byid.get(eid)
    got = disp(e) if e else None
    print(f"tier2 {eid}: {got} (esperado {want})")
    if not e or got != want:
        fails.append(f"{eid}: {got} != {want}")
for eid in ("plano", "revisao-p1-gabarito"):
    e = byid.get(eid)
    if e and e.get("temporal_block_id"):
        fails.append(f"{eid}: ganhou temporal ({disp(e)}) — devia ficar no funil")
    print(f"funil {eid}: temporal={bool(e.get('temporal_block_id')) if e else 'ENTRY AUSENTE'}")

# pinos: motor respeita e LIMPA temporal
suja = [e.get("id") for e in pinos if e.get("temporal_block_id")]
if suja:
    fails.append(f"pinos com temporal nao-limpo: {suja}")

print()
if len(temporal) != 54:
    fails.append(f"temporal count {len(temporal)} != 54 (51 piloto + 3 tier2)")
if len(pinos) != 11:
    fails.append(f"pinos {len(pinos)} != 11")
print("GATE:", "PASS" if not fails else "FAIL")
for f in fails:
    print(" -", f)
sys.exit(0 if not fails else 1)
```

Run: `python <scratchpad>/gate_mf.py`
Expected: GATE PASS. Nota honesta: nomes de campo (`temporal_band`/provider) e ids exatos podem divergir do chute do gate — se o script quebrar por NOME de campo, corrigir o GATE (é one-off de leitura), NUNCA o motor. Se quebrar por VALOR (contagem/bloco errado), é FAIL real → Step 5.

- [ ] **Step 3: Voter — 0 chamadas API**

Inspecionar `<scratchpad>\reprocess_mf.log`: nenhuma linha de chamada Gemini nova (cache F3: 36 hits esperados); fila humana 0. `Select-String -Path "<scratchpad>\reprocess_mf.log" -Pattern "gemini|voter|vote" -CaseSensitive:$false` e ler as linhas.
Expected: só hits de cache / SKIPPED; zero requisições de rede do voter.

- [ ] **Step 4: Review do git diff no MF**

```powershell
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" status --porcelain
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" diff --stat
```

Expected: mudanças em `manifest.json` + artefatos regenerados (índices, SYLLABUS/KB se regenerados). NENHUM arquivo de conteúdo/markdown deletado. Diff de `manifest.json` (amostra): adições `temporal_*`, funil `auto_tags bloco:` INTACTO nos 42 confirmados.

- [ ] **Step 5 (SÓ SE GATE FAIL): rollback + registro honesto**

```powershell
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" checkout -- .
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" clean -fd
```

Reverter flags no subjects.json (restaurar backup do scratchpad). Registrar FAIL em pendencias.md com números. PROIBIDO re-tuning. PARAR a campanha e reportar ao user.

- [ ] **Step 6: Commit do rollout no repo MF**

```powershell
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" add -A
git -C "C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor" commit -m "rollout flag-ON: use_anchor_engine + use_llm_voter (temporal_* reais; gate HARD-drift PASS)"
```

---

### Task 4: Régua completa pós-flip MF + suite

**Files:** nenhum modificado — medição pura. Log em `<scratchpad>/regua_posflip_mf.log`.

**Interfaces:**
- Consumes: Task 3 concluída (MF flag-ON reprocessado).
- Produces: veredito da régua (números idênticos aos aceitos) — gate de prosseguimento para SO/TCC.

- [ ] **Step 1: Pré-gate de gold**

Run: `python scripts/audit_gold_freshness.py`
Expected: exit 0, hard=0 (ZERO_OVERLAP soft ok — 47 rows esperadas na condição PDF-de-trabalho).

- [ ] **Step 2: Rodar os 7 probes (capturar tudo)**

```powershell
foreach ($s in "fase0_prova_motor_MF","fase1_recall_gate_MF","fase2_prova_SO","fase2_prova_TCC","fase3_prova_LLM_MF","fase4_prova_D9","fase5_prova_tier2") { "=== $s ==="; python "scripts/$s.py" } *>&1 | Tee-Object "<scratchpad>\regua_posflip_mf.log"
```

Expected (números ACEITOS, seção Global Constraints): fase0 48/58 conten0 cw1 · fase1 9/10 · fase2_SO 45.2%/0/0 · fase2_TCC 5/5+83.3%/cw0 · fase3 +3/0API · fase4 48/58 cw1 + 51/58 cw0 calls0 · fase5 target 4/8 cw0. Probes são motor-in-memory (flag-independent); os artefatos MF regenerados na Task 3 são o ÚNICO input que mudou — qualquer delta = investigar ANTES de prosseguir; se legítimo-inexplicável, tratar como FAIL honesto (rollback Task 3 Step 5 + registro).

- [ ] **Step 3: Suite completa**

Run: `python -m pytest -q`
Expected: 1816+N passed / 4 skipped / 0 failed (N = testes da Task 1).

- [ ] **Step 4: Badges/health (validação leve, GUI fica pro user)**

Checar que `BUILD_REPORT.md` do MF regenerou sem seção de erro nova e que entries com `temporal_*` têm badge/band coerente no manifest (spot-check 3 entries: 1 alta, 1 media, 1 pino). Registrar no log.

---

### Task 5: Registro do rollout MF (pendencias + commit)

**Files:**
- Modify: `docs/reports/pendencias.md` (entrada nova 2026-08-03)

**Interfaces:**
- Consumes: números reais das Tasks 3–4.
- Produces: entrada `[DERIVADO/DECISION] Rollout flag-ON MF EXECUTADO` com: contagens do gate (54/11/…), voter 0 calls, régua byte-idêntica, commits dos dois repos, decisão user (cutover fora, push antes).

- [ ] **Step 1: Escrever a entrada** (números REAIS medidos, não os esperados; formato das entradas vizinhas).
- [ ] **Step 2: Commit**

```bash
git add docs/reports/pendencias.md
git commit -m "docs(rollout): flag-ON MF executado — gate HARD-drift PASS, regua byte-identica, voter 0 calls"
```

---

### Task 6: Pre-flight + flip SO

**Files:**
- Create: `<scratchpad>/gate_so.py` (adaptação do gate_mf.py)
- Modify: subjects.json (`Sistemas Operacionais`), repo SO (reprocess)

**Interfaces:**
- Consumes: Task 4 verde (gate de prosseguimento). SO JÁ tem `material_curation.json` na raiz (verificado 2026-08-03) e topics 19/21 blocos (2 sem topics = admin, esperado).
- Produces: SO flag-ON com gate próprio + medição pré/pós.

- [ ] **Step 1: Pré-flight**

Run: `python scripts/audit_gold_freshness.py --course SO`
Expected: exit 0, hard=0. Se hard>0 → PARAR SO, registrar, seguir para Task 7 (TCC) — cursos são independentes.

- [ ] **Step 2: Baseline pré-flip** — `python scripts/fase2_prova_SO.py` (deve bater 45.2%/0/0 — já rodado na Task 4, confirmar).

- [ ] **Step 3: Snapshot git SO** — mesmo padrão da Task 2 Step 1 (commit `snapshot pre-rollout flag-ON`).

- [ ] **Step 4: Flip SO no subjects.json** — mesmo padrão da Task 2 Step 3, chave `"Sistemas Operacionais"`, backup antes.

- [ ] **Step 5: Reprocess flag-ON**

```powershell
python scripts/reprocess_assignments.py --flags use_anchor_engine,use_llm_voter "C:/Users/Humberto/Documents/GitHub/Sistemas-Operacionais-Tutor" *>&1 | Tee-Object "<scratchpad>\reprocess_so.log"
```

Expected: `[ok]` sem traceback. Voter: contar chamadas API no log (cache SO existente deve cobrir; cap 20 built-in). Registrar: nº chamadas, nº hits, fila humana.

- [ ] **Step 6: Gate SO (adaptar gate_mf.py)** — SEM piloto SO, o gate é estrutural: (a) pinos preservados e com temporal limpo; (b) funil `auto_tags bloco:` intacto (diff manifest); (c) temporal só em entries de escopo (nenhum TIER-2/out-category com temporal); (d) re-run `python scripts/fase2_prova_SO.py` → 45.2%/0/0 IDÊNTICO (probe é in-memory; artefatos regenerados não podem deslocá-lo); (e) `audit_gold_freshness --course SO` hard=0 PÓS-reprocess (detecta drift posicional). Delta report: contar entries cujo `temporal_block_id` diverge do funil e cruzar com gold rotulado — regressão em banda ALTA = 0 (aceite; espírito cw=0). FAIL → rollback padrão (Task 3 Step 5, adaptado) + registro; não bloqueia TCC.

- [ ] **Step 7: Commit no repo SO** (`rollout flag-ON: ...`) + entrada pendencias.md + commit docs no projeto.

---

### Task 7: Pre-flight + flip TCC

Mesmo formato da Task 6, com diferenças:

- Chave subjects.json: `"Teoria da Computabilidade e Complexidade"`. Repo: `TCC-Tutor`.
- Pré-flight: `python scripts/audit_gold_freshness.py --course TCC` (hard=0) + baseline `python scripts/fase2_prova_TCC.py` (5/5 pinos + 83.3%/cw0).
- **TCC NÃO tem `material_curation.json` na raiz** → voter SEM cache: até 20 votos pagos (Gemini, cap built-in) + possível fila humana. Registrar chamadas/custo/fila no log. Fila humana > 0 = ITEM PRO USER (curadoria na GUI), não FAIL.
- Gate estrutural idêntico (pinos 5/5 preservados é linha dura; `fase2_prova_TCC` idêntico pós-flip; freshness hard=0 pós).
- Commits nos dois repos + pendencias.

- [ ] **Step 1: Pré-flight TCC** (gold + baseline)
- [ ] **Step 2: Snapshot git TCC**
- [ ] **Step 3: Flip TCC no subjects.json** (backup antes)
- [ ] **Step 4: Reprocess flag-ON + log** (`reprocess_tcc.log`)
- [ ] **Step 5: Gate TCC + registro de custo do voter**
- [ ] **Step 6: Commits + pendencias**

---

### Task 8: Audit IA/ES2 — report-only (SEM flip)

**Files:** nenhum modificado nos repos IA/ES2 (READ-ONLY estrito).

**Interfaces:**
- Produces: seção no relatório final + pendencias: o que bloqueia o flip de cada um.

- [ ] **Step 1:** `python scripts/audit_gold_freshness.py --course IA` e `--course ES2` — registrar hard/soft por classe.
- [ ] **Step 2:** Registrar bloqueios conhecidos + achados: gold IA user-side (trilha 4: placements, straddle SARC); stash IA parcial (~45 arquivos); timeline IA com janela 24–29/06 trocada (snapshot SARC antigo); **IA tem flag legado `use_anchor_placement: true`** — precedência já é `use_anchor_engine > use_anchor_placement` (pedagogical_regeneration.py:444), mas o flip futuro do IA deve DESLIGAR o legado no mesmo ato (registrar como pré-requisito).
- [ ] **Step 3:** Entrada pendencias `[DERIVADO] Audit pré-rollout IA/ES2` + commit docs.

---

### Task 9: Housekeeping final da campanha

- [ ] **Step 1:** Handoff novo `docs/reports/2026-08-03-handoff-rollout-trilha1.md` (ou data do dia): estado por curso (MF/SO/TCC ON, IA/ES2 bloqueios), números dos gates, o que resta da trilha 1 (dívidas → Plano B; cutover adiado por decisão user; rollout IA/ES2 bloqueado em gold user-side).
- [ ] **Step 2:** `graphify update .`
- [ ] **Step 3:** Commit + push (`git push origin feat/motor-atribuicao` — autorizado pelo user nesta campanha).

---

## Fora deste plano (mesma campanha, plano próprio)

**Plano B — dívidas do motor** (defer-F5: T1b/T2b/T3/T4b/T7a/T7b/T9a + herdados F3; minors-batch F5b: filtro fileurl, gate due-vazio, imports locais, hoist stems; topics→kind SÓ com re-medição): exige investigação site-a-site antes de escrever código no plano — será escrito após o rollout, com a régua desta campanha como baseline.

## Self-Review (executado na escrita)

- Cobertura: itens 1–3 da trilha 1 cobertos (rollout MF, push já feito, SO/TCC + audit IA/ES2); item 4 (cutover) excluído por decisão user; item 5 (dívidas) → Plano B declarado.
- Placeholders: gate scripts completos; única incerteza declarada honestamente (nomes de campo `temporal_*` no manifest — regra de correção: gate sim, motor nunca).
- Consistência: `_apply_flags`/`_parse_argv` usados com as mesmas assinaturas nas Tasks 1 e 3; chaves do subjects.json copiadas da inspeção real.
