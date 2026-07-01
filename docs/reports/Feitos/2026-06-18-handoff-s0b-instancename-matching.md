# Handoff — S0b: moodle_label por instancename + matching robusto + re-sync por fonte

date: 2026-06-18
branch: `feat/reconciliar-unit-bloco`
estado: **spec do S0b escrito, commitado e aprovado em design** (`7d1f5e9`, `93cbcff`). Próximo passo = `writing-plans` → implementação TDD. Suíte base **1483 verde**; golden PDF **5/5, cw 0**; resolver de bloco ainda atrás da flag `use_concept_resolver` (OFF = produção funil).

## Como retomar (ler nesta ordem, NÃO reler a conversa antiga)
1. `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis). `.mex/context/institutional.md` (seção **Moodle × M365** atualizada nesta sessão).
2. **Este handoff.**
3. **Spec do S0b:** `docs/superpowers/specs/2026-06-18-moodle-label-instancename-automatico-design.md` (design completo + posição na fila + testes + eval-gate).
4. Handoff anterior (S0→A1): `docs/reports/2026-06-18-handoff-s0-feito-rumo-a1.md` (mapa de precedência, recursos Moodle/SARC, A1).
5. Direção geral: `docs/reports/2026-06-17-handoff-signal-registry.md` (fila A1–A7).
6. **Prefixar TODA resposta com `[Humberto]`** (CLAUDE.md). Commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. **Caveman mode** ativo (terse; código/commits/spec normais).

## Posição na fila
`S0 (feito) → **S0b (este, design pronto)** → A1 → A2 → A3 → A5 → A4 (cutover) → A6 → A7`. S0 capturou sinais aditivos; S0b torna a captura **correta+completa** e re-sincroniza; destrava a rotulagem de gold cross-curso e o A1.

## O que é o S0b (escopo aprovado)
Tornar `moodle_label` (instancename) e `posting_date` colarem **automático** no import, robusto à colisão de filename, + re-sync dos 5 repos por fonte. Reproduz sem trabalho manual o que o usuário fez à mão no TCC.

- **Fix A (código), `src/builder/sources/moodle.py`:** `backfill_moodle_label_from_api` e `backfill_posting_date_from_api` passam a indexar por **savename (`sf.disk_name`) sanitizado** + fallback no `sf.filename`. Unicidade por-key. Resolve colisão `main.pdf` (TCC) / `slides.pdf` (SO). **Aditivo — não muda atribuição.**
- **Fix 1b (data), `sanitize_folder_name`:** zero-padding de `DD/MM`→`DD.MM` (2 dígitos) **só quando o separador é `/`** (datas; versão/seção com `.` ficam intactas). Ex.: `24/4`→`24.04`, `06/12/2026`→`06.12.2026`, `12/2025`→`12.2025` (preservado). Cosmético pro sinal (`extract_dates` já tolera `\d{1,2}`); eval-gate = `rebuild_diff` idêntico.
- **Re-sync por fonte:** Moodle (TCC/IA/SO) = `import_moodle_courses(download=True)` (salva em `<seção>/<instancename>` → source_section pela pasta + savename automático + backfill cola label/posting). M365 (MF/ES2) = arquivos ficam; backfill aditivo pega posting_date (+label onde filename casa).
- **FORA de escopo:** matching de `source_section` (consumed/eval-gated); concept resolver; rotulagem de gold.

## Mapa de fonte por curso (confirmado pelo usuário)
UM canal por curso, sem duplicação por arquivo:
- **Moodle:** TCC (`93728`), IA (`93156`), SO (`92854`).
- **M365 / OneDrive (nome com data):** MF (`92717`), ES2 (`92714`) — mesmo professor (Julio).
Repos em `C:\Users\Humberto\Documents\GitHub\*-Tutor`.

## Verificação via Moodle API (read-only, feita nesta sessão)
API live (userid=289064, 22 cursos). Cobertura de sinal por repo (`manifest.json`):

| Curso | entries | moodle_label | posting_date | arquivos Moodle | diagnóstico |
|---|---|---|---|---|---|
| MF | 60 | 57 | 57 | 36 | ok (M365, filename casa) |
| IA | 16 | 12 | 12 | 68 | **import incompleto** (faltam ~50) |
| SO | 25 | 7 | 7 | 36 | M365 date-name vs Moodle `slides.pdf` |
| ES2 | 39 | 8 | 8 | 30 | M365 (Microsserviços=24 num card) |
| TCC | 24 | **1** | 1 | 25 | savename manual ok, label não colou (colisão `main.pdf`) |

Causa raiz TCC (confirmada): `source_path` já é o instancename ("Aula 17 - NP-Completude…"), `source_section` veio da pasta, mas `moodle_label` vazio porque o backfill casa por `sf.filename`="main.pdf". `iter_section_files` JÁ traz `label=mod.name` e `savename` — só o matching estava na key errada.

## Próximos passos (ordem)
1. **`writing-plans`** a partir do spec → plano de implementação TDD.
2. Implementar Fix A + Fix 1b (RED→GREEN; fixtures novas em `tests/test_moodle_labels.py` p/ colisão `main.pdf` e em `tests/test_moodle.py` p/ date-padding). Commit.
3. **Re-sync por fonte** (com `.apibak`/dry-run; NÃO auto-commitar repos — revisar `rebuild_diff` antes): IA puxa faltantes, SO/TCC label limpo, MF/ES2 posting aditivo.
4. Regenerar `gold_by_card` nos 5 repos (label/seção limpos) → rotular → `expand_card_gold` → travar baseline (gate).
5. Gates: `rebuild_diff` idêntico + golden 5/5 + `pytest -q` verde.

## Pendência do usuário (depois do S0b)
Rotular `docs/reports/gold_templates/gold_by_card_<curso>.csv` (1 linha/card, confirmar `true_block_id`) → `expand_card_gold` → baseline cross-curso (destrava eval-gate do A1). **MF já feito nesta sessão**: `tests/fixtures/eval/ground_truth_MF.csv` (58 arq, 57 rotulados; funil 82,5%, cw 4). Os outros 4 ficam mais limpos após o re-sync do S0b.

## Eval-gates / comandos
- Suíte: `python -m pytest tests -q` (1483 base).
- Golden PDF: `python scripts/eval_assignments.py` (5/5, cw 0).
- Rebuild-diff 5 cursos: `python scripts/rebuild_diff.py` (drift pré-existente ES2 7/IA 20/SO 13/MF 1 = dívida A7, NÃO regressão).
- Probe Moodle (read-only): `python -m scripts.moodle_probe --course <id>` (seções/cards). `--dump <id>` = JSON cru.
- Gold cross-curso: `python -m scripts.gold_by_card "<repo>" "<out.csv>"` → rotular → `python -m scripts.expand_card_gold "<repo>" "<by_card.csv>" "<ground_truth.csv>"` → `python scripts/eval_ground_truth.py "<repo>" "<ground_truth.csv>"`.

## Gotchas
- Token Moodle mobile em `moddle/.env` (`MOODLE_URL`/`MOODLE_TOKEN`). `moodle_probe`/`migrate_signals` são read-only/aditivos.
- Console Windows cp1252: imprimir UTF-8 cru quebra (`UnicodeEncodeError`); usar `PYTHONIOENCODING=utf-8` ou `sys.stdout.reconfigure`. O `??` em saída é display, não corrupção do dado.
- Hook `code-review-graph` PostCommit cospe traceback cp1252 no commit — inofensivo, commit passa.
- `sanitize_folder_name` preserva acentos (só `< > : " / \ | ? *` viram espaço); `/` entre dígitos vira `.` (datas). Casar SEMPRE pelo savename sanitizado, nunca pelo instancename cru.
- Limite conhecido S0b: colisão de savename idêntico (sufixo ` (2)` no disco via `download_course`) é ponto cego do índice — raro.
- Re-import pode trazer arquivos novos (IA) que mudam cards → revisar `rebuild_diff` antes de aceitar; `download_course` valida magic bytes (redirect M365/HTML cai em `failed`).

## Caminho de dependência (gold cross-curso) — gravado 2026-06-18
**Regra-chave:** A1–A7 DEPENDEM do gold baseline, NÃO o contrário. O gold baseline cross-curso é o pré-requisito que **destrava** o eval-gate do A1. Logo o gold vem ANTES de A1. NÃO é preciso terminar A1–A7 para rotular gold.

Faltam **4 CSVs**: IA, SO, ES2, TCC (MF já feito). O que trava os 4 é o **S0b** (este refactor), especificamente o re-sync (Task 4): TCC/IA/SO puxam do Moodle e hoje têm label/seção sujos (TCC 1/24, IA 16/68, SO colisão `slides.pdf`) — rotular antes do re-sync = rotular lixo. MF pôde ir antes por ser M365 com filename casando direto; ES2 também é M365 mas o re-sync ainda lhe traz posting/seção → rotular junto.

**Caminho mínimo (executar até terminar esta rodada de refatoração):**
1. S0b Tasks 1–3 (código): matching por savename + date zero-padding + eval-gate (`rebuild_diff` idêntico, golden 5/5, suíte verde).
2. S0b Task 4 (re-sync manual, com o usuário): Moodle `import_moodle_courses(download=True)` p/ TCC/IA/SO; backfill aditivo p/ MF/ES2.
3. Regenerar `gold_by_card` nos 4 → rotular `true_block_id` → `expand_card_gold` → travar baseline → destrava A1.

Modo de execução escolhido: **subagent-driven** (subagent fresco por task, melhor contra regressão).
