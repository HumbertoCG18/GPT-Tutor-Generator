"""Registro (06/09, sessao 6): unidade explicita da secao vence o bloco (1b41003) — FR do zero run A2 (19/19 pela secao), gates, reprocess
registrado dos 8; run B do FR (Gemini liberado so para o FR). Args: 1 = resumo do reprocess, 2 = resumo da run B, 3 = fila/100, 4 = determinismo."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
REP, RUNB, FILA, DET = (sys.argv + ["?", "?", "?", "?"])[1:5]


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
edit(T, "**Run B (Gemini so para o FR, ~20 chamadas) aguarda liberacao.** Sandbox fica em `.ablacao/FR-rebuild/` (nao apagado o FR original).\n",
        "**Alavanca ENTROU (`1b41003`, `file_map.reconcile_unit_with_block(unit_is_explicit=...)`):** o motor JA detectava a unidade explicita da secao\n"
        "(`unidade-explicita=u2`, conf 0,95, `explicit_unit_number`) e a reconciliacao a sobrepunha pelo bloco — inclusive bloco FLAGADO ou herdado do\n"
        "vizinho. Agora a explicita vence e o conflito fica registrado (`explicita-vence-bloco=<id>`). So o FR tem secoes 'U<n>'; nos outros 7 a secao\n"
        "nomeia a unidade por titulo em 60 materiais (MF 29, CG 23, SO 6, ES2 2) e em todos a unidade final ja era a da secao (0 diferem): a regra por\n"
        "titulo seria no-op hoje, fica como candidata. Teste `test_unidade_explicita_da_secao_vence_bloco_discordante`. Suite 2335.\n"
        "**Run A2 do FR (`rebuild_fr.py --fresh`, 888 s, 0 chamadas):** unidade x secao do professor **10/19 -> 19/19** · concordancia com o produto\n"
        "bloco 11/20, unidade 11 -> 17/20, subunidade 7 -> 10/20 · fila 11/20 (conflito 9 — agora 'explicita-vence-bloco' — flag disamb 8, sem bloco 2,\n"
        "sub-empate 2). **Gates (copias, tripwire):** 5 cursos e holdout CG identicos (186/183/53/138 · 193/185/53/138 · 31/35 · 35/35 · CG sub 58/82).\n"
        f"**Reprocess registrado dos 8 (`c1-3/reprocess_8_explicita.py`):** {REP}. Fila {FILA}/100. Determinismo {DET}.\n"
        f"**Run B do FR (`rebuild_fr_b.py --fresh`, Gemini liberado pelo user so para o FR, contado; Datalab bloqueado):** {RUNB}\n"
        "Sandboxes: `.ablacao/FR-rebuild/` (A2) e `.ablacao/FR-rebuild-B/` (B); o FR original nao foi apagado.\n")

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Regra da secao S1b (`4d649c4`, +3 -0 simulado, +2 no motor):",
        f"Unidade explicita da secao vence bloco (`1b41003`): FR do zero unidade x secao 10/19 -> 19/19; 7 cursos iguais. FR run A2 fila 11/20; run B (Gemini, so FR): {RUNB[:120]}.\n"
        "Regra da secao S1b (`4d649c4`, +3 -0 simulado, +2 no motor):")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Unidade explicita da secao do Moodle ("U2 - ...") vence bloco discordante; FR reconstruido do zero como cenario do aluno (sem gold)

**Date:** 2026-09-06
**Status:** Active
**Decision:** `reconcile_unit_with_block` recebe `unit_is_explicit`; quando a unidade veio de `unidade-explicita=u<n>` (secao 'U<n>' do Moodle), ela vence o bloco discordante e o conflito fica registrado (`1b41003`). FR reconstruido do zero em sandbox (`.ablacao/FR-rebuild/`, run A, 0 chamadas) e com Gemini (`FR-rebuild-B/`, run B); o FR original nao foi apagado.
**Reasoning:** Pedido do user: FR do zero, numeros sem gold, maximo sem LLM. A unica regua sem gold no FR e a secao do professor ('U1', 'U2'); na run A o motor acertava 10/19 e os 9 erros eram todos a unidade explicita (conf 0,95) sobreposta por bloco flagado ou herdado do vizinho. Com a regra: 19/19; 5 cursos e CG identicos (a secao 'U<n>' so existe no FR; onde a secao nomeia a unidade por titulo, 60 materiais, a unidade final ja coincidia).
**Consequences:** Reprocess registrado: {REP}. Run B: {RUNB[:300]}. Fila do FR do zero segue 11/20: blocos flagados e conflitos (estrutura do Moodle sem datas) — territorio do voter ou de dado.
"""
assert "Unidade explicita da secao do Moodle" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `rebuild_fr_b.py --fresh` (run B, Gemini contado, Datalab bloqueado) · `reprocess_8_explicita.py`. Logs `rebuild_fr_a2.log`, `rebuild_fr_b.log`, `explicita_*.log`, `reprocess_8_explicita.log`.\n", encoding="utf-8")
print("docs ok")
