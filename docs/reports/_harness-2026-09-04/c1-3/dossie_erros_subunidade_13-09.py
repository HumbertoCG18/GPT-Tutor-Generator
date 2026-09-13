"""DOSSIE dos erros de subunidade do cru HONESTO: para cada erro, exatamente o que o adquiridor veria.

Motivo (13/09): antes de gastar orcamento construindo aquisicao de vocabulario, medir o TETO dela. O astra pos a
pergunta em 4 classes por material, e nenhuma delas se decide com a lista de erros sozinha:

  A  EXPRESSAO AUSENTE      o material nao contem nenhuma expressao que um especialista ligaria ao topico do gold
                            -> aquisicao NAO resolve (nao ha o que adquirir)
  B  EXPRESSAO PRESENTE,    a expressao esta la, falta a RELACAO termo->topico
     RELACAO AUSENTE        -> aquisicao RESOLVE. E o teto dela.
  C  COMPETICAO             a evidencia esta la e ja pontua, mas perde para outro candidato
                            -> problema de ordenacao/scorer, nao de aquisicao
  D  AUSENCIA VALIDA /      gold vazio, ou assunto sem subtopico correspondente na unidade exigida
     CONTEUDO INSUFICIENTE  -> sai do alvo

Este script NAO classifica: monta o dossie por curso com (a) o bundle que o compilador de vocabulario receberia para
aquele material — titulo, label do Moodle e ate 24 headings, exatamente `vocabulary_compile._bundle` —, (b) o
catalogo COMPLETO de topicos do curso, (c) o que o cru decidiu e o que o gold cobra, e (d) os sinais determinísticos
que ja separam C de A/B (score do topico do gold, se ele e argmax, exact_hits/overlap quando ha).

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/dossie_erros_subunidade_13-09.py
Saida: dossie_erros_subunidade_13-09/<CURSO>.md (um por curso) + .../_indice.md
"""
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
ORIG = GEN.parent
COPIA = GEN / ".motor3eixos"
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.core.vocabulary_compile import _extract_markdown_headings, moodle_label_text  # noqa: E402
from src.builder.core.vocabulary_compile import _entry_markdown_text_for_file_map  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
OUT = Path(__file__).with_suffix("")


def topicos_do_curso(root):
    """Catalogo completo de (unidade, codigo, rotulo) da taxonomia do curso — o destino possivel de qualquer termo."""
    p = root / "course/.content_taxonomy.json"
    if not p.exists():
        return []
    tax = json.loads(p.read_text(encoding="utf-8"))
    linhas = []
    for u in tax.get("units") or []:
        for t in u.get("topics") or []:
            linhas.append((str(u.get("title") or ""), str(t.get("code") or ""), str(t.get("label") or ""), "topic"))
            for s in t.get("subtopics") or []:
                linhas.append((str(u.get("title") or ""), str(s.get("code") or ""), str(s.get("label") or ""), "subtopic"))
    return linhas


def main():
    OUT.mkdir(exist_ok=True)
    erros = list(csv.DictReader((Path(__file__).parent / "erros_subunidade_cru_honesto_13-09.csv")
                                .open(encoding="utf-8-sig", newline="")))
    por_curso = {}
    for r in erros:
        por_curso.setdefault(r["curso"], []).append(r)

    indice = ["# Dossiê dos erros de subunidade — cru honesto (142/251), 13/09", "",
              "Um arquivo por curso. Cada erro traz **o bundle que o adquiridor de vocabulário receberia** "
              "(título, label do Moodle, até 24 headings — igual a `vocabulary_compile._bundle`) e o **catálogo "
              "completo de tópicos do curso**.", ""]
    for sig, rs in sorted(por_curso.items(), key=lambda kv: -len(kv[1])):
        root = COPIA / NOMES[sig]
        man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        cat = topicos_do_curso(root)
        L = [f"# {sig} — {len(rs)} erros de subunidade no cru honesto", "",
             f"## Catálogo COMPLETO de tópicos de {sig} ({len(cat)} entradas)",
             "Qualquer termo pode pertencer a qualquer um destes. O destino não está restrito à unidade do material.", "",
             "| unidade | código | rótulo | tipo |", "|---|---|---|---|"]
        for u, c, lab, kind in cat:
            L.append(f"| {u} | {c} | {lab} | {kind} |")
        L += ["", "---", "", f"## Os {len(rs)} erros", ""]
        for i, r in enumerate(rs, 1):
            e = man.get(r["entry_id"]) or {}
            md = _entry_markdown_text_for_file_map(root, e) or "" if e else ""
            heads = list(_extract_markdown_headings(md, limit=24)) if md else []
            heads += list(dict.fromkeys(Path(str(f.get("title") or "").replace("\\", "/")).name
                                        for f in (e.get("extracted_files") or []) if f.get("title")))
            L += [f"### {i}. `{r['entry_id']}`", "",
                  f"- **gold (primário):** `{r['gold'] or '(vazio)'}`" + (f" · extras: `{r['extras']}`" if r["extras"] else ""),
                  f"- **o cru decidiu:** `{r['cru'] or '(vazio)'}` · **o produto decide:** `{r['produto'] or '(vazio)'}`"
                  f" (produto acerta: {'sim' if r['produto_acerta'] == '1' else 'não'})",
                  f"- rota: `{r['rota']}` · na fila: {'sim' if r['na_fila'] == '1' else 'não'} · confiança: {r['conf']}",
                  f"- unidade atribuída: `{r['unidade']}` (a unidade está certa: {'sim' if r['unidade_certa'] == '1' else 'não'})",
                  f"- categoria/tipo: `{r['categoria']}` / `{r['tipo']}`", "",
                  "**BUNDLE que o adquiridor veria:**", "```",
                  f"TITULO: {e.get('title')}",
                  f"LABEL MOODLE: {moodle_label_text(e) if e else ''}",
                  "HEADINGS: " + (" | ".join(h[:80] for h in heads[:24]) if heads else "(nenhum)"),
                  "```", ""]
        (OUT / f"{sig}.md").write_text("\n".join(L), encoding="utf-8")
        indice.append(f"- `{sig}.md` — **{len(rs)} erros**, {len(cat)} tópicos no catálogo")
        print(f"  {sig}: {len(rs)} erros, {len(cat)} topicos, {len((OUT / f'{sig}.md').read_text(encoding='utf-8'))} chars")
    (OUT / "_indice.md").write_text("\n".join(indice) + "\n", encoding="utf-8")
    print(f"\nDossie em {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
