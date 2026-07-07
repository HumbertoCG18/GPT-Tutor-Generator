# Handoff — Roteiro como base de atribuição

date: 2026-06-28
contexto: continua de `2026-06-26-handoff-arquitetura-cascata.md`. Branch `feat/block-stable-id`.
status: mem-off gap recuperado, shims aplicados, probe baseline rodd. Próximo = prototipar roteiro-como-base no IA.

---

## 0. TL;DR pro chat novo

- **Sessão de recuperação de gap**: `claude-mem` estava off 21–28/jun (issues abertas no repo). Contexto recuperado manualmente via handoff anterior + releitura de scripts.
- **3 ações concluídas**: (1) UTF-8 shim em 4 scripts, (2) baseline compare_resolver.py rodado nos 5 cursos, (3) confirmado que `lessons_index` (roteiro) existe em 3/5 cursos e é o sinal correto — não `posting_date`.
- **Decisão firme do user**: roteiro como BASE, não tempero. `posting_date` = lixo (ignorar). A sessão anterior havia regredido para medir datas; o user corrigiu.
- **Próximo passo (não disparado)**: protótipo roteiro-as-base no IA — `material → match-de-conteúdo → entrada-do-roteiro → data → bloco`. Medir contra gold IA. Read-only.

---

## 1. Disciplina (não negociável — persiste)

- **NÃO commita.** User separa à mão (trabalho pré-sessão misturado no working-tree).
- **Mutação do vivo = ação do USER na GUI** (deletar pin, reprocessar). CC prepara/valida arquivos mortos.
- **GUI lê o disco** — ordem blindada: fecha-GUI → rename → gate-vivo → reabre → reprocessa.
- **Aviso GUI "sem bloco atribuído" = sem PIN, não sem placement** — NÃO preencher à mão.

---

## 2. Estado dos scripts IA (todos com UTF-8 shim aplicado)

| Script | Status | Nota |
|--------|--------|------|
| `scripts/compare_resolver.py` | ✅ shim | Read-only probe. Roda nos 5 cursos. |
| `scripts/build_ground_truth_IA.py` | ✅ shim | Gera `docs/reports/ground_truth_IA.csv` |
| `scripts/classify_discriminant_IA.py` | ✅ shim | Classifica scorable em DISC/TRIVIAL |
| `scripts/diff_pinfix_IA.py` | ✅ shim | Detecta cascateamento de pin |

**Shim padrão** (logo após os imports, antes de tudo):
```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

---

## 3. Baseline IA (denominador MUDOU desde handoff anterior)

O arquivo `gold_IA_rotular.xlsx` foi modificado em 28/06 (antes da sessão). Denominador live:

- **74 linhas** no gold xlsx
- **58 joined** ao manifest
- **30 scorable** (era 33 no handoff de 26/06 — STALE)
- **1 discriminante** = `IA-aula-29` (era 13 no handoff anterior — STALE)
- **24 straddle-flag** (clean, sem data_real por-material)

**FAILs restantes**: 1 (`IA-aula-29`: true bloco-06, temporal bloco-05).

> ⚠ Os números 87%/91%/13 discriminantes do handoff anterior são obsoletos. Não usar como referência.

---

## 4. Roteiro (`lessons_index`) — disponibilidade por curso

| Curso | `course/.lessons_index.json` | Sinal de base |
|-------|------------------------------|---------------|
| **IA** (Inteligencia-Artifical-Tutor) | ✅ presente | roteiro |
| **MF** (Metodos-Formais-Tutor) | ✅ presente | roteiro |
| **ES2** (Engenharia-Software-2-Tutor) | ✅ presente | roteiro |
| SO (Sistemas-Operacionais-Tutor) | ❌ ausente | filename-date (45% cobertura, 84% consistente por card) |
| TCC (TCC-Tutor) | ❌ ausente | a confirmar (posting_date tem 21 valores distintos = possivelmente real) |

**Formato do lessons_index**:
```json
{"version": 1, "by_date": {"2026-03-02": "Apresentação do plano de ensino, Histórico", "2026-03-04": "Visão Geral", ...}}
```

**Grão importante**: roteiro é por-SESSÃO (cada data = tópico distinto). Usar como base = grão 1:1 com blocos-sessão → **elimina straddle** (o straddle veio do gold agrupar 2 sessões num subtópico; o roteiro cru as distingue).

---

## 5. Cascata de precedência (INVERTIDA no código atual)

Contexto do handoff 26/06 (ainda válido):

```
temporal_block_id  (âncora)    ← maior precedência
manual_timeline_block_id (pin) ← média
computed_block_id  (concept_resolver) ← menor
```

O resolver-fino (`concept_resolver`) escreve em `computed` = fundo da pilha. Ligar `use_concept_resolver=True` sem reordenar não ajuda. O teste de flag-swap do handoff anterior **ainda não foi disparado**.

---

## 6. compare_resolver.py — resultado da rodada baseline (28/06)

Rodou nos 5 cursos. Resultado qualitativo (não log completo):
- Resolver-fino causa **churn massivo (50–74%)** com **degradação de confiança** (alta→baixa) nos cursos onde o funil já está correto.
- Isso corresponde ao "probe-2 net -24" reportado pela sessão Claude Web paralela.
- "probe-1 net 0" (lesson-ON vs lesson-OFF diff) **não foi re-derivado** formalmente — só atestado por memória.
- O probe é **motor-vs-motor** (resolver-fino vs funil), não acurácia vs gold. Não confundir.

**Caveat crítico** do script: `resolver-COM-concepts-do-LLM vs funil-SEM`. Não é like-for-like.

---

## 7. Pendências abertas (priorizadas)

### P1 — Protótipo roteiro-as-base no IA (PRÓXIMO PASSO)

Implementar `material → match-de-conteúdo → entrada-do-roteiro → data → bloco` para IA.
Medir contra `ground_truth_IA.csv`. **Read-only** (não altera manifest).

Isso é diferente do `score_lesson_match` atual: o scorer atual é peso 0.5 em fusão (tempero). A proposta é usar como BASE — o tópico do roteiro é o oráculo, não um voto.

### P2 — SO e TCC sem roteiro

Verificar se os cards de SO/TCC têm texto de roteiro extraível (`build_lesson_topic_index`). Se sim, extrai e iguala ao IA/MF/ES2. Se não, SO fica com filename-date, TCC a confirmar.

### P3 — flag-swap test da cascata

Teste do handoff 26/06 ainda pendente: `use_anchor_placement=False` + `use_concept_resolver=True` → reprocessa → re-mede. **Depende de P1 estar estável primeiro** (precisamos de baseline sólido antes de mexer no vivo).

### P4 — TCC NFD normalization (latente)

Filename `aula-10-linguagens-reconhecíveis` tem `ı` (U+0131, dotless-i, NFD do macOS). Pode quebrar joins silenciosamente. Fix = normalizar NFC no import. Não urgente.

### P5 — Gold-discriminante SO

Pendente. Depende da refatoração de atribuição.

---

## 8. Discrepâncias/gotchas pra próxima sessão

- `docs/reports/gold_templates/` está no `.gitignore` → `ground_truth_IA.csv` lá dentro não commita. O arquivo correto está em `docs/reports/ground_truth_IA.csv` (fora do gitignore).
- `docs/reports/gold_templates/gold_IA_rotular.predropdown-20260628-021507.bak.xlsx` = backup da versão pré-modificação do xlsx. Denominator do backup = 33 scorable (obsoleto).
- Branch atual: `feat/block-stable-id`. Não criou commit novo nesta sessão (só shims em scripts não-commitados).
- `M docs/reports/pendencias.md` e `M docs/reports/gold_templates/gold_IA_rotular.xlsx` no git status = modificados por sessão anterior ao gap, ainda não commitados pelo user.
- Arquivos novos desta sessão (`2026-06-28-probe-resolver-recuperado.md`, `ground_truth_IA.csv`, `build_ground_truth_IA.py`, `classify_discriminant_IA.py`, `diff_pinfix_IA.py`) são `??` (untracked) — user vai separar à mão.
