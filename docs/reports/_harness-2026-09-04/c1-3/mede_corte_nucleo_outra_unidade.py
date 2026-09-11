"""§2.2 do plano 08/09, regra 2 (nunca medida): cortar termo DOADO pelo LLM cujo nucleo aparece no vocabulario ou nos
materiais de OUTRA unidade. A regra 1 (rotulo meta) entrou em 11/09; esta ficou sem medida. 0 chamadas.
Termo doado = synonym do `course/.glossary_curation.llm.json`; nucleo = termo normalizado; "aparece" = casador de frase do motor.
  V1 vocab : em alias/label de topico de outra unidade, ou no titulo dela
  V2 heads : em titulo/label moodle/headings/membros de zip de material de outra unidade (o que o LLM viu)
  V3 texto : no .md inteiro de material de outra unidade
  V12      : V1 ou V2
Regua: 7 cursos com gold (251), regime determ com o produtor do produto (como replay_exp_cg.py).
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/mede_corte_nucleo_outra_unidade.py"""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
import src.builder.timeline.index as ti  # noqa: E402
from src.builder.core import code_summarization as cs  # noqa: E402
from src.builder.core.vocabulary_compile import _norm, topic_key, unit_title_core  # noqa: E402
from src.builder.extraction.content_taxonomy import _extract_markdown_headings as heads  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
casa = ti._matches_normalized_phrase


def synth_produto(sig):
    als = set(cs.course_aliases(Path(".ablacao") / rp.NAMES[sig]))

    def synth(e, root):
        s = cs.synthesize_code_entry(e, root, als)
        return {"summary": s} if s else {}
    return synth


def contexto(sig):
    """{unidade: termos doados (norm)} e, por unidade, o vocab / heads / texto dos materiais DELA (as outras = resto)."""
    root, entries, tax, _, _ = rp.load(sig)
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    llm = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    doado, vocab, hd, tx = {}, {}, {}, {}
    for u in tax["units"]:
        doado[u["slug"]] = {_norm(v) for t in u["topics"] for v in llm.get(topic_key(t), {}).get("synonyms", [])}
        vocab[u["slug"]] = [unit_title_core(u["title"])] + [a for t in u["topics"] for a in [t["label"]] + t.get("aliases", [])]
    for e in entries:
        un = e.get("computed_unit_slug") or ""
        if not un or (e.get("category") not in rp.CATEGORIAS and not e.get("computed_block_id")):
            continue
        md = rp.getmd(root, e) or ""
        h = [str(e.get("title") or ""), moodle_label_text(e)] + list(heads(md, limit=24)) + [
            Path(str(f.get("title") or "").replace("\\", "/")).name for f in (e.get("extracted_files") or []) if f.get("title")]
        hd.setdefault(un, []).append(" | ".join(h))
        tx.setdefault(un, []).append(md)
    return doado, {"V1": vocab, "V2": hd, "V3": tx}


def veta(doado, fonte):
    out = {}
    for u, termos in doado.items():
        outras = [s for v, ss in fonte.items() if v != u for s in ss]
        out[u] = {t for t in termos if any(casa(s, t) for s in outras)}
    return out


def corte(vet):
    def change(tax):
        for u in tax["units"]:
            v = vet.get(u["slug"], set())
            for t in u["topics"]:
                t["aliases"] = [a for a in t["aliases"] if _norm(a) not in v]
    return change


tot = {}
for sig in CURSOS:
    doado, fontes = contexto(sig)
    synth = synth_produto(sig)
    base = rp.evaluate(sig, "determ", synth=synth)
    n = len(base[2])
    linha = f"{sig:4} base {base[0]:3}/{n:<3} doados {sum(map(len, doado.values())):3}"
    tot.setdefault("base", [0, 0]); tot["base"][0] += base[0]; tot["base"][1] += n
    vets = {m: veta(doado, f) for m, f in fontes.items()}
    vets["V12"] = {u: vets["V1"][u] | vets["V2"][u] for u in doado}
    for m, vet in vets.items():
        r = rp.evaluate(sig, "determ", synth=synth, taxmod=corte(vet))
        g = [k for k in base[2] if not base[2][k] and r[2][k]]
        l = [k for k in base[2] if base[2][k] and not r[2][k]]
        nc = sum(map(len, vet.values()))
        linha += f" | {m} corta {nc:3} -> {r[0]:3} (+{len(g)} -{len(l)})"
        tot.setdefault(m, [0, 0]); tot[m][0] += r[0]; tot[m][1] += n
        if g or l:
            print(f"    {sig} {m}: gain {g} loss {l}", flush=True)
        ex = sorted(t for s in vet.values() for t in s)
        print(f"    {sig} {m} cortados ({nc}): {ex[:15]}{' ...' if nc > 15 else ''}", flush=True)
    print(linha, flush=True)
print("TOTAL 7 cursos (com-extras) /251:", {m: f"{v[0]}/{v[1]}" for m, v in tot.items()})
