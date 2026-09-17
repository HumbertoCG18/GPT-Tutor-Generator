"""A evidencia do topico certo existe no arquivo e NAO chega ao bundle? DETERMINISTICO (13/09).

Por que: o diagnostico dos 109 erros (`teto_aquisicao_13-09.csv`) disse que em 23 deles a evidencia decisiva mora
fora do bundle que o adquiridor de vocabulario recebe — frontmatter `language: "isabelle"`, identificadores dentro
dos `.java`, o corte em 24 headings. **Aquilo foi JULGAMENTO de agente.** Este script mede a mesma coisa sem
julgamento nenhum, com a normalizacao do proprio motor, e serve para confirmar ou derrubar aquele numero.

Para cada erro de subunidade do cru honesto, procura o rotulo do topico do GOLD (frase inteira, e tambem cada token
especifico dele) em 4 CAMADAS, da mais pobre para a mais rica:

  1 BUNDLE        titulo + label do Moodle + ate 24 headings + nome dos membros de zip
                  = exatamente `vocabulary_compile._bundle`, o que o adquiridor ve
  2 FRONTMATTER   o cabecalho YAML do markdown do material (onde vive `language: "isabelle"`)
  3 CORPO         o markdown inteiro do material
  4 MEMBROS       o markdown de CADA arquivo extraido (os `code/professor/*.md` dos zips), corpo e frontmatter

A conta que decide: **em quantos materiais a evidencia esta ausente na camada 1 e presente em 2, 3 ou 4?**
Esse e o tamanho da alavanca "engenharia de bundle", medido em vez de julgado.

Nao mede ganho: um token presente nao vira acerto sozinho (medido em 12/09: dos 32 alcancados por alguma fonte, so
10 teriam o gold como argmax). E teto de ALCANCE, e o log diz isso em toda saida.

0 chamadas. Le a copia `.motor3eixos/` (braco C, o cru honesto). Nao escreve em curso nenhum.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/evidencia_fora_do_bundle_13-09.py
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
COPIA = GEN / ".motor3eixos"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.core.vocabulary_compile import _extract_markdown_headings, moodle_label_text  # noqa: E402
from src.builder.core.vocabulary_compile import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
import src.builder.timeline.index as ti  # noqa: E402

N = ti._normalize_match_text
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
CAMADAS = ("bundle", "frontmatter", "corpo", "membros")


def frase_no(texto_norm, frase):
    n = N(frase or "")
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


def tokens_especificos(label):
    """Tokens do rotulo que nao sao genericos do motor e tem >= 4 chars — os que carregam sinal."""
    return {t for t in N(label or "").split() if len(t) >= 4 and t not in MOTOR_GENERIC_STEMS}


def rotulo_do_topico(root, slug):
    """O label humano do subtopico, a partir do slug do gold. Sem ele nao ha o que procurar."""
    p = root / "course/.content_taxonomy.json"
    if not p.exists() or not slug:
        return ""
    tax = json.loads(p.read_text(encoding="utf-8"))
    for u in tax.get("units") or []:
        for t in u.get("topics") or []:
            for no in [t] + list(t.get("subtopics") or []):
                if str(no.get("slug") or "") == slug:
                    return str(no.get("label") or "")
    return ""


def camadas_do_material(root, e):
    """Devolve {camada: texto normalizado}. As camadas sao cumulativas em riqueza, nao em conteudo."""
    md = _entry_markdown_text_for_file_map(root, e) or ""
    fm = ""
    if md.startswith("---"):
        fim = md.find("\n---", 3)
        fm = md[:fim] if fim > 0 else md[:2000]
    heads = list(_extract_markdown_headings(md, limit=24))
    membros = [f for f in (e.get("extracted_files") or []) if f.get("title")]
    heads += list(dict.fromkeys(Path(str(f.get("title") or "").replace("\\", "/")).name for f in membros))
    bundle = " ".join([str(e.get("title") or ""), moodle_label_text(e) or "", " ".join(h[:60] for h in heads[:24])])

    txt_membros = []
    for f in membros:
        bm = f.get("base_markdown") or ""
        if not bm:
            continue
        fp = root / "course" / bm if not (root / bm).exists() else root / bm
        for cand in (root / bm, root / "course" / bm, root / "acervo" / bm):
            if cand.exists():
                fp = cand
                break
        try:
            txt_membros.append(fp.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
        txt_membros.append(str(f.get("language") or ""))
    return {"bundle": N(bundle), "frontmatter": N(fm), "corpo": N(md), "membros": N(" ".join(txt_membros))}


def main():
    erros = list(csv.DictReader((HERE / "erros_subunidade_cru_honesto_13-09.csv").open(encoding="utf-8-sig", newline="")))
    juizo = {}
    p = HERE / "teto_aquisicao_13-09.csv"
    if p.exists():
        for r in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
            juizo[r["entry_id"]] = r

    linhas, mans = [], {}
    for r in erros:
        sig = r["curso"]
        root = COPIA / NOMES[sig]
        if sig not in mans:
            mans[sig] = {x["id"]: x for x in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        e = mans[sig].get(r["entry_id"])
        if not e or not r["gold"]:
            continue
        label = rotulo_do_topico(root, r["gold"])
        toks = tokens_especificos(label)
        cam = camadas_do_material(root, e)
        achou = {}
        for c in CAMADAS:
            t = cam[c]
            achou[c] = ("frase" if frase_no(t, label) else
                        ("token" if toks and any(re.search(r"(^|\s)" + re.escape(tk) + r"(\s|$)", t) for tk in toks)
                         else "nada"))
        fora = achou["bundle"] == "nada" and any(achou[c] != "nada" for c in CAMADAS[1:])
        linhas.append(dict(curso=sig, entry_id=r["entry_id"], gold=r["gold"], label_do_gold=label,
                           tokens=";".join(sorted(toks)), **{f"em_{c}": achou[c] for c in CAMADAS},
                           evidencia_fora_do_bundle=int(fora),
                           classe_do_diagnostico=(juizo.get(r["entry_id"]) or {}).get("classe_final", ""),
                           juizo_disse_fora=(juizo.get(r["entry_id"]) or {}).get("fora_do_bundle", "")))

    out = HERE / "evidencia_fora_do_bundle_13-09.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    print(f"MEDIDO em {len(linhas)} erros com gold nao vazio (dos 109; os de gold vazio nao tem rotulo a procurar).")
    print("TETO DE ALCANCE, NAO GANHO: token presente nao vira acerto sozinho — em 12/09, dos 32 alcancados por")
    print("alguma fonte, so 10 teriam o gold como argmax.\n")

    print(f"{'camada':14} {'frase':>7} {'token':>7} {'nada':>7}   (acumulado: onde o rotulo do gold e alcancavel)")
    for c in CAMADAS:
        k = collections.Counter(l[f"em_{c}"] for l in linhas)
        print(f"{c:14} {k['frase']:>7} {k['token']:>7} {k['nada']:>7}")

    fora = [l for l in linhas if l["evidencia_fora_do_bundle"]]
    print(f"\n>>> EVIDENCIA AUSENTE NO BUNDLE E PRESENTE EM ALGUMA CAMADA MAIS RICA: {len(fora)} de {len(linhas)}")
    print(f"    por curso: {dict(collections.Counter(l['curso'] for l in fora))}")
    print(f"    por camada que a contem: frontmatter {sum(1 for l in fora if l['em_frontmatter'] != 'nada')} · "
          f"corpo {sum(1 for l in fora if l['em_corpo'] != 'nada')} · "
          f"membros {sum(1 for l in fora if l['em_membros'] != 'nada')}")

    print(f"\n>>> CONFRONTO COM O JULGAMENTO DOS AGENTES (a razao deste script existir)")
    j_sim = {l["entry_id"] for l in linhas if l["juizo_disse_fora"] == "1"}
    m_sim = {l["entry_id"] for l in fora}
    print(f"    o agente disse 'fora do bundle' em {len(j_sim)} · a medicao diz {len(m_sim)}")
    print(f"    concordam: {len(j_sim & m_sim)} · so o agente: {len(j_sim - m_sim)} · so a medicao: {len(m_sim - j_sim)}")

    print(f"\n>>> POR CLASSE DO DIAGNOSTICO (a evidencia fora do bundle atravessa as classes?)")
    for cl in ("A", "B", "C", "D", ""):
        rs = [l for l in linhas if l["classe_do_diagnostico"] == cl]
        if rs:
            print(f"    classe {cl or '(sem)'}: {len(rs):>3} erros · {sum(l['evidencia_fora_do_bundle'] for l in rs):>3} com evidencia fora do bundle")

    print(f"\nDetalhe em {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
