"""Puxa um curso do Moodle pela API e monta o stash: arquivos, paginas internas e links CLASSIFICADOS.

    python scripts/moodle_pull.py --course 95106 --root <dir> --dry-run      # so classifica: links.json + resumo
    python scripts/moodle_pull.py --course 95106 --root <dir> --pdf          # baixa/imprime tudo

Saida (debaixo de --root):
    stash/<secao>/<arquivo>          resources baixados + paginas (site/Moodle) impressas em PDF (--pdf)
    raw/moodle/contents.json         core_course_get_contents cru
    raw/moodle/pages/<cmid>.html     HTML das paginas internas (mod_page)
    raw/moodle/labels.json           labels (sub-cards) na ordem em que aparecem
    raw/moodle/sections.json         summary + labels COMPLETOS por secao (F1: a formula do G1 do
                                     Lab SO vive no summary da secao 0, fora de qualquer card)
    raw/sarc/cronograma-*.html       export do SARC descoberto no proprio Moodle (F12), so quando a
                                     TURMA do export bate com a do shortname (330 != 310 -> review)
    stash/.moodle_nomes.json         F10: "card/arquivo" -> NOME DO MODULO no Moodle. O stash salva o
                                     filename ("03 - Tipos de Redes.pdf"), mas a categoria certa muitas
                                     vezes so existe no nome do modulo ("Tipos de Redes (Slides)") — ou
                                     vice-versa ("Livro-texto: Buildroot" vs "aula03 - buildroot.pdf").
                                     scan_stash_cards le o sidecar e detecta sobre OS DOIS nomes.
    raw/site/...                     snapshot das paginas do site do professor (site_snapshot)
    links.json                       cada url/page com {secao, nome, url, tipo, acao, destino, sinal}
    manual-review/links.md           o que ficou ambiguo (nunca chute silencioso)

Classificacao (handoff 2026-08-26, passo 2) — deterministica, SEM nada por curso, em ordem de confianca:
  1. card: secao com bibliografia/referencia/links uteis/leitura/complementar -> referencia
  2. dominio/caminho: PDF -> material (download); pagina no MESMO host das outras paginas do professor -> material
     (snapshot+PDF); youtube/vimeo -> video (referencia); github/gitlab/doi/acm/ieee/springer/sciencedirect/
     scholar/books.google/amazon/wikipedia -> referencia/repositorio
  3. nome do link: livro/artigo/paper/repositorio/documentacao/tutorial/manual -> referencia
  4. pagina interna do Moodle: NOME primeiro (exercic/resolucao/atividade/lista -> material; 'videos' -> indice),
     conteudo como desempate (>= 3 links de video e < 300 palavras -> indice); material -> PDF
  Resto -> review.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.migrate_signals import load_moodle_token  # noqa: E402
from scripts.site_snapshot import Snapshot, detect_encoding, find_browser, normalize_html, print_pdf, pdf_stats, slug  # noqa: E402
from src.builder.sources.moodle import MoodleClient, sanitize_folder_name  # noqa: E402

VIDEO_HOSTS = ("youtube.com", "youtu.be", "vimeo.com")
REFERENCE_HOSTS = ("github.com", "gitlab.com", "doi.org", "dl.acm.org", "ieeexplore.ieee.org", "link.springer.com",
                   "sciencedirect.com", "scholar.google", "books.google", "amazon.com", "amazon.com.br", "wikipedia.org",
                   "medium.com", "stackoverflow.com")
REFERENCE_CARD_RE = re.compile(r"bibliograf|refer[eê]ncia|links?\s*[úu]teis|leitura|complementar", re.I)
REFERENCE_NAME_RE = re.compile(r"\b(livro|artigo|paper|reposit[óo]rio|documenta[çc][ãa]o|tutorial|manual|cap[íi]tulo)\b", re.I)
YT_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([\w-]{6,})")


def host_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


SARC_EXPORT_RE = re.compile(r"sarc\.pucrs\.br/.*export\.aspx", re.I)
# Turma no shortname do Moodle: "4646I-04310262" = codigo-CC TTT SSS (TTT = turma 310).
# Medido nos 9 cursos do user (MF 031, SO 032, ..., CG 310, FR 320, Lab Redes 340, Lab SO 310).
_SHORTNAME_TURMA_RE = re.compile(r"-\d{2}(\d{3})\d{3}$")
# Turma no cabecalho do export: "4646I-4 Laboratorio de Sistemas Operacionais (330) - 32/410".
_EXPORT_TURMA_RE = re.compile(r"\((\d{3})\)")


def turma_do_shortname(shortname: str) -> str:
    m = _SHORTNAME_TURMA_RE.search(str(shortname or "").strip())
    return m.group(1) if m else ""


def turma_do_export(html: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", str(html or "")[:4000])
    m = _EXPORT_TURMA_RE.search(texto)
    return m.group(1) if m else ""


def classify_url(name: str, section: str, url: str, professor_hosts: set[str]) -> tuple[str, str, str]:
    """-> (tipo, acao, sinal). tipo: cronograma | material-pagina | material-pdf | video | referencia | review."""
    h = host_of(url)
    path = urlparse(url).path.lower()
    # F12: o export do SARC esta postado como link nos 3 cursos novos ("Cronograma") — e o
    # cronograma da disciplina, nao material nem referencia, mesmo dentro de card de plano.
    if SARC_EXPORT_RE.search(url):
        return "cronograma", "cronograma", "sarc"
    if REFERENCE_CARD_RE.search(section):
        return "referencia", "referencia", "card"
    if any(h.endswith(v) for v in VIDEO_HOSTS):
        return "video", "referencia", "dominio"
    if any(h.endswith(r) for r in REFERENCE_HOSTS):
        return "referencia", "referencia", "dominio"
    if h in professor_hosts:
        if path.endswith(".pdf"):
            return "material-pdf", "download", "dominio+pdf"
        if path.endswith((".htm", ".html", "/")) or "." not in path.rsplit("/", 1)[-1]:
            return "material-pagina", "snapshot", "dominio+pagina"
    if REFERENCE_NAME_RE.search(name):
        return "referencia", "referencia", "nome"
    if path.endswith(".pdf"):
        return "material-pdf", "download", "pdf"
    return "review", "review", "nenhum"


PAGE_VIDEO_NAME_RE = re.compile(r"v[íi]deos?", re.I)
PAGE_MATERIAL_NAME_RE = re.compile(r"exerc[íi]c|resolu[çc][ãa]o|atividade|lista|enunciado|roteiro", re.I)


def classify_page(html: str, name: str = "") -> tuple[str, str, str]:
    """Nome primeiro (o professor nomeia a pagina pelo que ela e), conteudo como desempate."""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    words = len(text.split())
    videos = len(set(YT_RE.findall(html)))
    stats = f"{videos} videos, {words} palavras"
    if PAGE_MATERIAL_NAME_RE.search(name):
        return "material-pagina-moodle", "print", "nome+" + stats
    if PAGE_VIDEO_NAME_RE.search(name) and (videos >= 1 or words < 300):
        return "indice-videos", "referencia", "nome+" + stats
    if videos >= 3 and words < 300:
        return "indice-videos", "referencia", stats
    return "material-pagina-moodle", "print", stats


class Pull:
    def __init__(self, client: MoodleClient, token: str, root: Path, pdf: bool, dry: bool):
        self.c, self.tok, self.root, self.pdf, self.dry = client, token, root, pdf, dry
        self.stash = root / "stash"
        self.rawm = root / "raw" / "moodle"
        self.links: list[dict] = []
        self.labels: list[dict] = []
        self.sections: list[dict] = []
        self.nomes: dict[str, str] = {}  # F10: "card/arquivo-no-disco" -> nome do modulo
        self.turma_moodle = ""
        self.browser = find_browser() if pdf else None
        self.snap = Snapshot(root, depth=1, pdf=pdf)

    def get(self, fileurl: str) -> bytes:
        sep = "&" if "?" in fileurl else "?"
        req = urllib.request.Request(fileurl + f"{sep}token={self.tok}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()

    def run(self, course: int) -> None:
        contents = self.c.get_course_contents(course)
        try:
            info = self.c._call("core_course_get_courses_by_field", field="id", value=course)
            shortname = str((info.get("courses") or [{}])[0].get("shortname") or "")
        except Exception:
            shortname = ""
        self.turma_moodle = turma_do_shortname(shortname)
        print(f"turma do Moodle ({shortname or '?'}): {self.turma_moodle or '?'}")
        self.rawm.mkdir(parents=True, exist_ok=True)
        (self.rawm / "contents.json").write_text(json.dumps(contents, ensure_ascii=False, indent=1), encoding="utf-8")
        urls = [(m.get("contents") or [{}])[0].get("fileurl", "") for s in contents for m in s.get("modules", []) if m["modname"] == "url"]
        hosts = Counter(host_of(u) for u in urls if u and not any(host_of(u).endswith(v) for v in VIDEO_HOSTS + REFERENCE_HOSTS))
        professor_hosts = {h for h, n in hosts.items() if n >= 2}  # host que o professor usa repetidamente = site dele
        print(f"hosts do professor (>=2 links): {sorted(professor_hosts)}")
        for sec in contents:
            card = sanitize_folder_name(sec.get("name") or "") or f"secao-{sec.get('section')}"
            # F1: summary da secao (fora de card) + labels completos — e onde mora a formula
            # do G1 do Lab SO ("Avaliacao: G1 = (TP1+TP2+TP3+TP4)/4 ... media 5.0, sem G2").
            _summary = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sec.get("summary") or "")).strip()
            _sec_rec = {"secao": sec.get("name"), "section": sec.get("section"), "summary": _summary, "labels": []}
            self.sections.append(_sec_rec)
            for m in sec.get("modules", []):
                mn = m["modname"]
                if mn == "label":
                    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.get("description") or "")).strip()
                    self.labels.append({"secao": sec.get("name"), "cmid": m["id"], "texto": txt[:500]})
                    _sec_rec["labels"].append(txt)
                elif mn == "resource":
                    for f in m.get("contents") or []:
                        fname = f.get("filename", "arquivo")
                        # Resource .htm(l) (roteiros dos labs 2026/2) segue o MESMO caminho das
                        # paginas: raw + print em PDF -> Datalab no build -> descricoes de imagem
                        # posicionadas (IMAGE_DESCRIPTION), igual a CG. Cru no stash ele virava
                        # `codigo-professor` sem texto nem descricao (pedido do user 2026-08-30).
                        if fname.lower().endswith((".htm", ".html")):
                            dest = self.stash / card / f"{Path(fname).stem}.pdf"
                            self.nomes[f"{card}/{dest.name}"] = str(m.get("name") or "")
                            rec = {"secao": sec.get("name"), "nome": m.get("name"), "url": f.get("fileurl", ""),
                                   "tipo": "material-pagina-arquivo", "acao": "print", "destino": "", "sinal": "resource-html"}
                            self.links.append(rec)
                            if self.dry:
                                continue
                            raw = self.get(f["fileurl"])
                            html = raw.decode(detect_encoding(raw, "utf-8"), errors="replace")
                            pages_dir = self.rawm / "pages"; pages_dir.mkdir(parents=True, exist_ok=True)
                            hp = pages_dir / f"{m['id']}-{slug(Path(fname).stem)}.html"
                            hp.write_text(normalize_html(html), encoding="utf-8")
                            rec["raw"] = str(hp.relative_to(self.root))
                            if self.browser:
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                if not dest.exists() and print_pdf(self.browser, hp, dest):
                                    rec["destino"] = str(dest.relative_to(self.root))
                                    rec["pdf_pages"], rec["pdf_images"] = pdf_stats(dest)
                                elif dest.exists():
                                    rec["destino"] = str(dest.relative_to(self.root))
                            continue
                        dest = self.stash / card / fname
                        self.nomes[f"{card}/{dest.name}"] = str(m.get("name") or "")
                        rec = {"secao": sec.get("name"), "nome": m.get("name"), "url": f.get("fileurl", ""), "tipo": "arquivo",
                               "acao": "download", "destino": str(dest.relative_to(self.root)), "sinal": "resource"}
                        self.links.append(rec)
                        if not self.dry:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if not dest.exists():
                                dest.write_bytes(self.get(f["fileurl"]))
                elif mn == "url":
                    ext = (m.get("contents") or [{}])[0].get("fileurl", "")
                    tipo, acao, sinal = classify_url(m.get("name", ""), sec.get("name", ""), ext, professor_hosts)
                    rec = {"secao": sec.get("name"), "nome": m.get("name"), "url": ext, "tipo": tipo, "acao": acao, "destino": "", "sinal": sinal}
                    self.links.append(rec)
                    if tipo == "cronograma":
                        # F12: valida a TURMA antes de confiar — o professor do Lab SO postou o
                        # export da 330 no Moodle da 310 (achado do user, 2026-08-30).
                        try:
                            html = self.get_plain(ext).decode("utf-8", errors="replace")
                        except Exception as exc:
                            rec["acao"], rec["sinal"], rec["erro"] = "review", "sarc-inacessivel", str(exc)[:120]
                            continue
                        rec["turma_export"] = turma_do_export(html)
                        rec["turma_moodle"] = self.turma_moodle
                        if self.turma_moodle and rec["turma_export"] and rec["turma_export"] != self.turma_moodle:
                            rec["acao"], rec["sinal"] = "review", "turma-divergente"
                            print(f"!! cronograma do SARC e da turma {rec['turma_export']}, Moodle e {self.turma_moodle} -> review")
                        elif not self.dry:
                            sarc_dir = self.root / "raw" / "sarc"; sarc_dir.mkdir(parents=True, exist_ok=True)
                            out = sarc_dir / f"cronograma-{slug(m.get('name', 'sarc'))}.html"
                            out.write_text(html, encoding="utf-8")
                            rec["destino"] = str(out.relative_to(self.root))
                        continue
                    if self.dry:
                        continue
                    if acao == "download":
                        dest = self.stash / card / (Path(urlparse(ext).path).name or "arquivo.pdf")
                        self.nomes[f"{card}/{dest.name}"] = str(m.get("name") or "")
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        if not dest.exists():
                            try:
                                dest.write_bytes(self.get_plain(ext))
                            except Exception as exc:
                                rec["erro"] = str(exc)[:120]
                        rec["destino"] = str(dest.relative_to(self.root))
                    elif acao == "snapshot":
                        self.snap.stash = self.stash
                        page = self.snap.save_page(ext, card, "hub", 0, follow=True)
                        rec["destino"] = page["local"] if page else ""
                elif mn == "page":
                    fu = (m.get("contents") or [{}])[0].get("fileurl", "")
                    raw = self.get(fu) if fu else b""
                    html = raw.decode(detect_encoding(raw, "utf-8"), errors="replace") if raw else ""
                    tipo, acao, sinal = classify_page(html, m.get("name", ""))
                    rec = {"secao": sec.get("name"), "nome": m.get("name"), "url": m.get("url", ""), "tipo": tipo, "acao": acao,
                           "destino": "", "sinal": sinal, "videos": sorted(set(YT_RE.findall(html)))}
                    self.links.append(rec)
                    if self.dry:
                        continue
                    pages_dir = self.rawm / "pages"; pages_dir.mkdir(parents=True, exist_ok=True)
                    hp = pages_dir / f"{m['id']}-{slug(m.get('name', 'pagina'))}.html"
                    hp.write_text(normalize_html(html), encoding="utf-8")
                    rec["raw"] = str(hp.relative_to(self.root))
                    if acao == "print" and self.browser:
                        out = self.stash / card / f"{slug(m.get('name', 'pagina'))}.pdf"
                        self.nomes[f"{card}/{out.name}"] = str(m.get("name") or "")
                        if print_pdf(self.browser, hp, out):
                            rec["destino"] = str(out.relative_to(self.root)); rec["pdf_pages"], rec["pdf_images"] = pdf_stats(out)
        if not self.dry and self.pdf:
            self.snap.print_all()
            for p in self.snap.pages.values():
                for rec in self.links:
                    if rec.get("url") == p["url"]:
                        rec["destino"] = p.get("pdf", "") or rec["destino"]; rec["pdf_pages"] = p.get("pdf_pages"); rec["pdf_images"] = p.get("pdf_images")
        self.snap.write_links()
        (self.rawm / "labels.json").write_text(json.dumps(self.labels, ensure_ascii=False, indent=1), encoding="utf-8")
        (self.rawm / "sections.json").write_text(json.dumps(self.sections, ensure_ascii=False, indent=1), encoding="utf-8")
        if self.nomes and not self.dry:
            self.stash.mkdir(parents=True, exist_ok=True)
            (self.stash / ".moodle_nomes.json").write_text(json.dumps(self.nomes, ensure_ascii=False, indent=1), encoding="utf-8")
        (self.root / "links.json").write_text(json.dumps(self.links, ensure_ascii=False, indent=1), encoding="utf-8")
        review = [r for r in self.links if r["acao"] == "review"]
        (self.root / "manual-review").mkdir(exist_ok=True)
        (self.root / "manual-review" / "links.md").write_text(
            "# Links sem classificacao (decidir: material / referencia / ignorar)\n\n" + "\n".join(f"- [{r['secao']}] {r['nome']} -> {r['url']}" for r in review) + "\n", encoding="utf-8")

    def get_plain(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--course", type=int, required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    url, tok = load_moodle_token()
    if not tok:
        print("Faltando MOODLE_TOKEN"); return 2
    pull = Pull(MoodleClient(url, tok), tok, Path(args.root), args.pdf, args.dry_run)
    pull.run(args.course)
    by = Counter((r["tipo"], r["acao"]) for r in pull.links)
    print("\n== classificacao (tipo, acao): contagem")
    for (t, a), n in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"   {n:3}  {t:24} -> {a}")
    print(f"labels: {len(pull.labels)} | links.json: {len(pull.links)} itens | review: {sum(1 for r in pull.links if r['acao'] == 'review')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
