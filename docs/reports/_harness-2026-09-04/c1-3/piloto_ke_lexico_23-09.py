"""Piloto KE (23/09): léxico ConceptNet 5.7.0 (en/pt, IsA + Synonym) e tabela de aliases por tópico do plano.

Regras em piloto_ke_declaracao_23-09.md (pré-registradas antes da aquisição). Entradas: o dump baixado e as taxonomias do
plano de ensino das raízes da base v2 (`load_internal_content_taxonomy`, a mesma que o replay usa). NÃO lê gold, régua,
previsões, IDs ou texto de materiais. Saídas (em .frzero/ke_piloto_23-09/, fora do git):
  lexico_conceptnet_5.7.0_en_pt.json  arestas filtradas com proveniência
  aliases_ke_23-09.json               aliases KE por (curso, unidade, tópico) com a aresta de origem
e o resumo sem gold em c1-3/piloto_ke_lexico_23-09.json (hashes e contagens).
"""
import collections
import csv
import gzip
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
DIR = DATA / ".frzero/ke_piloto_23-09"
DUMP = DIR / "conceptnet-assertions-5.7.0.csv.gz"
LEX = DIR / "lexico_conceptnet_5.7.0_en_pt.json"
ALI = DIR / "aliases_ke_23-09.json"
sys.path.insert(0, str(DATA))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10 ** 8)

RELS = {"/r/IsA": "isa", "/r/Synonym": "syn"}
LANGS = ("/c/en/", "/c/pt/")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def chave(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().replace("_", " ").split())


def termo(uri):
    partes = uri.split("/")          # ['', 'c', 'en', 'neural_network', 'n', ...]
    return partes[2], partes[3].replace("_", " ")


def singular_pt(k):
    out = []
    for w in k.split():
        for suf, rep in (("oes", "ao"), ("aes", "ao"), ("ais", "al"), ("eis", "el"), ("ois", "ol"), ("ns", "m")):
            if w.endswith(suf) and len(w) > len(suf) + 1:
                w = w[: -len(suf)] + rep
                break
        else:
            if re.search(r"[aeiou]s$", w) and len(w) > 3:
                w = w[:-1]
        out.append(w)
    return " ".join(out)


def construir_lexico():
    arestas = []
    with gzip.open(DUMP, "rt", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            rel = RELS.get(row[1])
            if not rel or not row[2].startswith(LANGS) or not row[3].startswith(LANGS):
                continue
            info = json.loads(row[4])
            (la, ta), (lb, tb) = termo(row[2]), termo(row[3])
            arestas.append([rel, la, ta, lb, tb, row[0], info.get("dataset", ""), info.get("license", "")])
    arestas.sort()
    LEX.write_text(json.dumps({"fonte": "ConceptNet 5.7.0", "arquivo_sha256": sha_file(DUMP),
                               "regra": "rel em {IsA, Synonym}; ambas as pontas em /c/en ou /c/pt; sem outro filtro",
                               "campos": ["rel", "lingua_a", "termo_a", "lingua_b", "termo_b", "uri", "dataset", "licenca"],
                               "arestas": arestas}, ensure_ascii=False), encoding="utf-8")
    return arestas


def construir_aliases(arestas):
    from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
    from src.builder.text.stopwords import MOTOR_GENERIC_STEMS
    from src.builder.timeline.index import _label_parts
    syn, hipo = collections.defaultdict(list), collections.defaultdict(list)
    conceitos = set()
    for rel, la, ta, lb, tb, uri, ds, lic in arestas:
        ka, kb = chave(ta), chave(tb)
        conceitos.update((ka, kb))
        if rel == "syn":
            syn[ka].append((kb, tb, lb, uri, ds))
            syn[kb].append((ka, ta, la, uri, ds))
        else:                                   # IsA(a, b): a é-um b -> a é hipônimo de b
            hipo[kb].append((ka, ta, la, uri, ds))
    raizes = json.loads((HERE / "wz2_diagnostico_causal_23-09.json").read_text(encoding="utf-8"))["raizes"]

    def higiene(texto):
        k = chave(texto)
        if len(k) < 4 or k.replace(" ", "").isdigit():
            return False
        return not (" " not in k and any(k.startswith(g) for g in MOTOR_GENERIC_STEMS))

    tabela, resumo = {}, {}
    for sig, rel_root in raizes.items():
        tax = load_internal_content_taxonomy(DATA / rel_root)
        tabela[sig], n_top, n_com, n_al = {}, 0, 0, 0
        for u in tax.get("units", []) or []:
            for t in u.get("topics") or []:
                n_top += 1
                label = str(t.get("label") or "")
                frases = [label] + [str(a) for a in t.get("aliases") or []] + list(_label_parts(label, set()))
                ja = {chave(f) for f in frases}
                casados = {}
                for fr in frases:
                    for k in {chave(fr), singular_pt(chave(fr))}:
                        if k and k in conceitos:
                            casados.setdefault(k, fr)
                S = {k: {"via": "casamento", "frase_do_plano": fr} for k, fr in casados.items()}
                for k in list(casados):
                    for k2, t2, l2, uri, ds in syn.get(k, []):
                        S.setdefault(k2, {"via": "syn", "de": k, "termo": t2, "lingua": l2, "uri": uri, "dataset": ds})
                H = {}
                for k in S:
                    for k2, t2, l2, uri, ds in hipo.get(k, []):
                        H.setdefault(k2, {"via": "isa", "de": k, "termo": t2, "lingua": l2, "uri": uri, "dataset": ds})
                novos = []
                for k, prov in sorted({**H, **S}.items()):
                    txt = prov.get("termo") or k
                    if k in ja or not higiene(txt):
                        continue
                    novos.append({"alias": txt, **prov})
                if novos:
                    tabela[sig][f"{u.get('slug')}|{t.get('slug')}"] = novos
                    n_com += 1
                    n_al += len(novos)
        resumo[sig] = {"topicos": n_top, "topicos_com_alias_ke": n_com, "aliases_ke": n_al}
        print(sig, resumo[sig], flush=True)
    ALI.write_text(json.dumps(tabela, ensure_ascii=False, sort_keys=True, indent=0), encoding="utf-8")
    return resumo


def main():
    assert DUMP.exists(), DUMP
    arestas = construir_lexico()
    cont = collections.Counter((a[0], a[1], a[3]) for a in arestas)
    print("arestas", len(arestas), dict(cont), flush=True)
    resumo = construir_aliases(arestas)
    out = {"dump_sha256": sha_file(DUMP), "lexico_sha256": sha_file(LEX), "aliases_sha256": sha_file(ALI),
           "script_sha256": sha_file(Path(__file__)), "arestas": len(arestas),
           "arestas_por_tipo": {f"{r}:{a}->{b}": n for (r, a, b), n in sorted(cont.items())}, "por_curso": resumo}
    (HERE / "piloto_ke_lexico_23-09.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
