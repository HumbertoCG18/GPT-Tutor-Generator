"""Por que a subunidade erra no FR CONSTRUIDO DO ZERO? Diagnostico DETERMINISTICO, erro a erro (13/09).

Pergunta do usuario: "como podemos aumentar a % da subunidade em um curso construido do 0?". O FR do zero (stash do
Moodle pelo caminho da UI, tripwire, 0 chamadas) acerta 6/18 no primario. Antes de propor alavanca, ver o score.

Para cada erro, com as funcoes REAIS do motor (sem reimplementar nada):
  - o texto que o resolver entrega ao scorer: markdown + resumo DETERMINISTICO de codigo (`code_curation_signal_text`),
    exatamente como `resolver_apply.apply_unit_subunit_fields` monta `texto_para_unidade`
  - a 1a passada (`engine._auto_map_entry_subtopic`, restrita a unidade final) e o que a 2a passada deixou no manifest
  - o top-3 de score na unidade e a posicao/score do topico do GOLD (o gold so mede, nao entra no motor)
  - CONTRAFACTUAL EM MEMORIA (marcado como tal, nao e o motor inteiro): o mesmo scorer lendo o `moodle_label` com o peso
    do titulo. Serve para decidir se o braco vale o reprocess; nao e ganho.

0 chamadas. Le a copia `.frzero/base` (nunca `.ablacao/`).
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/diagnostico_frzero_13-09.py [<sandbox>]
"""
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.utils.helpers  # noqa: F401,E402  (.env)
from src.builder import engine as eng  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.extraction.entry_signals import collect_entry_unit_signals  # noqa: E402
from src.builder.timeline.index import _iter_content_taxonomy_topics, _score_entry_against_taxonomy_topic  # noqa: E402

SB = Path(sys.argv[1]) if len(sys.argv) > 1 else GEN / ".frzero/base"


def main():
    gold = {r["entry_id"]: r for r in csv.DictReader((GEN / "docs/reports/subunit_gt_FR.csv").open(encoding="utf-8-sig", newline=""))
            if r["scorable"] == "yes"}
    man = json.loads((SB / "manifest.json").read_text(encoding="utf-8"))["entries"]
    cc = (json.loads((SB / "code_curation.json").read_text(encoding="utf-8")).get("entries") or {}) if (SB / "code_curation.json").exists() else {}
    tax = load_internal_content_taxonomy(SB)
    idx = _iter_content_taxonomy_topics(tax)
    rotulo = {str(t.get("topic_slug") or ""): str(t.get("topic_label") or "") for t in idx}

    n_err = n_label_resolve = n_label_quebra = 0
    for e in man:
        g = gold.get(e["id"])
        if not g:
            continue
        final = str(e.get("computed_subunit_slug") or "")
        md = _entry_markdown_text_for_file_map(SB, e) or ""
        resumo = code_curation_signal_text(cc.get(e["id"]) or {}) if e["id"] in cc else ""
        texto = f"{md}\n\n{resumo}" if (md and resumo) else (md or resumo)
        unidade = str(e.get("computed_unit_slug") or "")
        tops = [t for t in idx if str(t.get("unit_slug") or "") == unidade]
        sig = collect_entry_unit_signals(e, texto)
        scored = sorted(((str(t.get("topic_slug") or ""), _score_entry_against_taxonomy_topic(sig, t)) for t in tops),
                        key=lambda x: -x[1])
        p1 = eng._auto_map_entry_subtopic(e, tax, texto, winning_unit_slug=unidade)

        sig_l = dict(sig)
        sig_l["title_text"] = f"{sig.get('title_text', '')} {sig.get('moodle_label_text', '')}".strip()
        scored_l = sorted(((str(t.get("topic_slug") or ""), _score_entry_against_taxonomy_topic(sig_l, t)) for t in tops),
                          key=lambda x: -x[1])
        vence_l = scored_l[0][0] if scored_l and scored_l[0][1] > 0 and (len(scored_l) < 2 or scored_l[0][1] > scored_l[1][1]) else ""

        certo = final == g["gold_subunit"]
        if not certo:
            n_err += 1
        if vence_l == g["gold_subunit"] and not certo:
            n_label_resolve += 1
        if certo and vence_l and vence_l != g["gold_subunit"]:
            n_label_quebra += 1
        if certo:
            continue

        pos = next((i for i, (s, _) in enumerate(scored, 1) if s == g["gold_subunit"]), None)
        sc_gold = next((v for s, v in scored if s == g["gold_subunit"]), None)
        print(f"=== {e['id']}  ({e.get('file_type')}, {len(texto)} chars de texto ao scorer, resumo de codigo: {'sim' if resumo else 'nao'})")
        print(f"    titulo: {e.get('title')!r} · moodle_label: {e.get('moodle_label')!r}")
        print(f"    GOLD  {g['gold_subunit']}  = {rotulo.get(g['gold_subunit'], '?')!r}")
        print(f"    gold na unidade final? {'sim' if pos else 'NAO (unidade errada ou topico fora)'} · posicao {pos} · score {sc_gold}")
        print(f"    1a passada: {p1.topic_slug or '(vazio)'} conf={p1.confidence:.3f} {list(p1.reasons)}")
        print(f"    final     : {final or '(vazio)'} {e.get('subunit_match_reasons')}")
        print("    top-3: " + " · ".join(f"{s[:34]}={v:.2f}" for s, v in scored[:3]))
        print(f"    [contrafactual em memoria] com moodle_label no titulo, a 1a passada venceria: {vence_l or '(empate/vazio)'}"
              + ("  <-- o gold" if vence_l == g["gold_subunit"] else ""))
        print()

    print(f"ERROS: {n_err} de {len(gold)}")
    print(f"[contrafactual em memoria, so 1a passada, NAO e o motor] moodle_label resolveria {n_label_resolve} erros "
          f"e quebraria {n_label_quebra} acertos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
