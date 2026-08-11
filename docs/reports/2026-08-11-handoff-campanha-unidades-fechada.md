# Handoff — sessão 2026-08-11: campanha 2 (Unidades) FECHADA 13/13; fila = campanha 3

**Branch:** `feat/motor-atribuicao`. Sucede `docs/reports/2026-08-11-handoff-campanha-unidades-meio.md`
(campanha a ~80%). Ledger SDD: `.superpowers/sdd/2026-08-07-campanha-unidades/progress.md`
(gitignored). Spec/plano movidos pra `Feitos/` neste fechamento.

## §1 Placar final

**eval_units 5/5 (gold do user congelado 5/5):** MF 12/14=85.7 · SO 9/11=81.8 · ES2 7/7=100 ·
TCC 13/13=100 · **IA 9/10=90** (T11 executada). Misses restantes = 100% POLÍTICA
(overview/véspera/entrega-embutida não carregam unidade) — zero erro de matcher.
**Suite 1920 passed / 0 failed / 4 skipped — golden IA crônico FECHADO.**
**12 pinos gold-backed em produção:** 3 SO + 4 ES2 + 5 IA (4× u05-ML + bloco-16 u03).
Índices em disco: MF 3/3 · SO 7/7 · ES2 3/3 · TCC 4/4 · IA 4/5 (u04 sem aula própria no
SARC vivo; WARN-baseline permanente).

## §2 O que esta sessão fechou

1. **Review T10** (Approved; golden ES2 editado à mão verificado BYTE A BYTE vs índice vivo;
   `pytest -k ES2` é NO-OP — filtro certo `-k "Engenharia-Software-2"`, no tracker).
2. **T11 — ruling IA (user: opção B, pinos gold-backed)**: relatório
   `2026-08-11-t11-ruling-ia-opcoes.md`; refresh gated (25→23 blocos) + 4 pinos u05 nos
   blocos ML + bloco-16 `manual_kind_override=class`+pino u03 (falso positivo 'planejamento'
   no TEMA). IA-Tutor `dd9967d`+`458f744`; projeto `96dfb3e` (gold IA 23 blocos/régua 10,
   goldens re-baselined). Snapshot 13 sidecars sha256 em
   `.superpowers/sdd/2026-08-07-campanha-unidades/snapshots/`.
3. **Fix slug (pergunta do user mid-sessão, ruling: corrigir pré-freeze)**: percentual de
   carga no título ("Visão Geral (5%)") vazava pro slug ("visao-geral-5"). Fix TDD em
   `_normalize_unit_slug` (`8683a39`); matching já era imune (tokenizador só-letras/isdigit);
   slugs IA u01/u02 migrados no índice ANTES do freeze do gold.
4. **T12 — sandbox aula-13 TCC**: resíduo VIVO (sem pino → bloco-13 via card, band alta
   0.85, winner=48.76/topic=8.83). Guard C6-equivalente = item [CODE] com RED pronto;
   pino segura produção. Report `2026-08-11-t12-sandbox-aula13-tcc.md` (`e7b6f09`).
5. **T13 — fechamento**: tracker `pendencias.md` atualizado (entrada Concluído campanha 2 +
   2 seções de dívida nova); spec/plano → `Feitos/`; este handoff.

## §3 Achado técnico novo (RED pronto, tracker)

`manual_kind_override`→class NÃO re-deriva unidade: `_serialize_timeline_index`
(index.py:835) zera unit_slug de não-class ANTES de `_apply_curation_overrides`;
`auto_unit_slug` preserva o que o DP deu. Workaround institucional: kind override + pino
juntos (precedentes bloco-18 SO, bloco-16 IA).

## §4 Fila da próxima sessão

1. **Campanha 3/3 (fila original da unificação): SO providers → reprocess-all → cutover.**
   PRÉ-REQUISITO: item classifier posicional (tracker, RED pronto) — prior de revisão do
   SO depende de kind confiável. PRÉ-REQUISITO 2: remendo golds antigos (~60 linhas;
   SO hard=13 · IA hard=1 pós-refresh; re-auditoria ground_truth_MF).
2. Dívidas [DECISION] prontas pra ruling: covered_units (fonte candidata mapeada) ·
   PS/G2 estrutural · subunidades.
3. Guard C6 aula-13 (RED = sandbox T12) — só com aval do user.

## §4b Estado do freshness gate no fechamento (review final)

`check_sarc_freshness` = **5/5, 0 diffs (fix aprovado e aplicado pós-fechamento, mesmo
dia)**. Os 6 falsos-stale eram artefato do COMPARADOR: espaço duplo preservado pelo
import vs colapsado pelo parse vivo, e sessão REAL agendada sem descrição (IA 15/07 =
bloco-23, SO 16/07; confirmadas no HTML vivo — NÃO eram fantasma de import) descartada
só do lado vivo. Fix: `_norm_desc` nos dois lados + testes; parser de produção intocado.
Gold IA congelado SEGURO.
Reviews finais: T11 "With fixes" → fix round completo (2c99e75/15d4d94); whole-branch
"With fixes" → os 2 fixes de registro fechados neste commit.

## §5 Armadilhas (persistem)

- NÃO reprocessar cursos pela GUI; reprocess headless gated com `[profile]` no stdout.
- xlsx: `python scripts/gold_units_xlsx.py fix-dropdowns` após QUALQUER gravação openpyxl;
  `gold_units_rotular.xlsx` está M no working tree (rotulagem do user em andamento — não
  sobrescrever sem conferir).
- `sha256sum *` não pega dotfiles — usar `.[!.]* *`.
- Suite agora DEVE dar 0 failed; QUALQUER fail = regressão real (o golden IA fechou).
- mem-search fora do ar; contexto = este handoff + ledger SDD + reports 2026-08-*.
