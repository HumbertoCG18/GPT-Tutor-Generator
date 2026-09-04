"""Snapshot do site de um professor -> camada raw + PDFs no stash + cronograma em Markdown.

    python scripts/site_snapshot.py --root <dir> [--pdf] [--depth 1] [--syllabus URL] URL@card [URL@card ...]

Saida (tudo debaixo de --root):
    raw/site/<host>/<caminho>            bytes originais (.orig) + copia normalizada UTF-8 (.html) + imagens relativas
    raw/site/site_links.json             pagina -> {url, local, titulo, encoding, card, kind, links, images}
    stash/<card>/<nome>.pdf              (--pdf) pagina impressa pelo Edge/Chrome headless a partir da copia normalizada
    cronograma.md                        (--syllabus) tabela SARC do cronograma, para SubjectProfile.syllabus

Decisoes (handoff 2026-08-26): PDF e desbloqueio para o holdout (pipeline de sempre, Datalab extrai as figuras);
o cronograma NUNCA passa por PDF (ja sai limpo do conversor HTML); site_links.json preserva a camada de links
que o PDF perde. Encoding: BOM -> <meta charset> -> header HTTP -> cp1252 (o process_url atual usa utf-8 fixo e
quebra UTF-16/latin-1 — defeito conhecido, fora do escopo aqui).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PAGE_EXT = (".htm", ".html")
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp")
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
_META_CHARSET_RE = re.compile(rb"<meta[^>]+charset\s*=\s*[\"']?\s*([\w-]+)", re.I)
_META_TAG_RE = re.compile(r"<meta[^>]+charset[^>]*>", re.I)


def fetch(url: str, timeout: int = 30) -> tuple[bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.info().get_content_charset()


def detect_encoding(raw: bytes, header_charset: str | None) -> str:
    """BOM -> <meta charset> -> header HTTP -> cp1252. 'unicode' (Word) = UTF-16."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    m = _META_CHARSET_RE.search(raw[:8000])
    enc = (m.group(1).decode("ascii", "ignore") if m else "") or (header_charset or "") or "cp1252"
    if enc.lower() in ("unicode", "utf-16le", "utf-16be"):
        enc = "utf-16"
    try:
        "".encode(enc)
    except LookupError:
        enc = "cp1252"
    return enc


def normalize_html(text: str) -> str:
    """Copia UTF-8 com <meta charset="utf-8"> unico: e a que o navegador imprime (cp1252 sem header ele erra)."""
    text = _META_TAG_RE.sub("", text)
    if re.search(r"<head[^>]*>", text, re.I):
        return re.sub(r"(<head[^>]*>)", r'\1<meta charset="utf-8">', text, count=1, flags=re.I)
    return '<meta charset="utf-8">' + text


def local_path(root: Path, url: str) -> Path:
    u = urlparse(url)
    path = unquote(u.path)
    if path.endswith("/") or not path:
        path = path + "index.html"
    return root / u.netloc / path.lstrip("/")


def same_site(url: str, base: str) -> bool:
    a, b = urlparse(url), urlparse(base)
    return a.netloc == b.netloc


def in_subtree(url: str, base: str) -> bool:
    """Mesmo host E caminho sob o DIRETORIO da pagina-base (S6d): `same_site` seguia links para
    `Aulas/` inteiro, `CGII/`, `~manssour/` — entra so o que o card do Moodle aponta e o que vive abaixo dele."""
    a, b = urlparse(url), urlparse(base)
    if a.netloc != b.netloc:
        return False
    base_path = unquote(b.path)
    base_dir = base_path if base_path.endswith("/") else base_path.rsplit("/", 1)[0] + "/"
    return unquote(a.path).startswith(base_dir)


def slug(text: str) -> str:
    from src.utils.helpers import slugify
    return slugify(text) or "pagina"


def find_browser() -> str | None:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    return None


def print_pdf(browser: str, html_file: Path, out_pdf: Path) -> bool:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:  # Edge deixa Crashpad/ aberto
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={prof}", "--no-pdf-header-footer", "--virtual-time-budget=8000",
               f"--print-to-pdf={out_pdf}", html_file.resolve().as_uri()]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return False
        # O Edge headless retorna antes de fechar o arquivo: espera existir e estabilizar (ate 30 s).
        last = -1
        for _ in range(60):
            if out_pdf.exists():
                size = out_pdf.stat().st_size
                if size > 0 and size == last:
                    break
                last = size
            time.sleep(0.5)
        if not (out_pdf.exists() and out_pdf.stat().st_size > 0):
            err = (res.stderr or res.stdout or "").strip().splitlines()
            print(f"      edge: {err[-1][:160] if err else 'sem saida'}")
            return False
    return True


def pdf_stats(pdf: Path) -> tuple[int, int]:
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf))
        return doc.page_count, sum(len(p.get_images(full=True)) for p in doc)
    except Exception:
        return -1, -1


def syllabus_table(html_text: str, url: str) -> str:
    from src.builder.text.url_markdown import html_to_structured_markdown, truncate_markdown_blocks
    from src.utils.helpers import collapse_ws
    md = html_to_structured_markdown(html_text, url, "Cronograma", collapse_ws=collapse_ws,
                                     truncate_markdown_blocks=lambda b: truncate_markdown_blocks(b, max_chars=2_000_000))
    rows = [l for l in md.splitlines() if l.startswith("|")]
    return "\n".join(rows) + "\n"


class Snapshot:
    def __init__(self, root: Path, depth: int, pdf: bool):
        self.root = root
        self.raw = root / "raw" / "site"
        self.stash = root / "stash"
        self.depth = depth
        self.pdf = pdf
        self.browser = find_browser() if pdf else None
        self.pages: dict[str, dict] = {}
        self.images: set[str] = set()

    def save_page(self, url: str, card: str, kind: str, level: int, follow: bool = True) -> dict | None:
        if url in self.pages:
            rec = self.pages[url]
            if follow and level < self.depth and not rec.get("_followed"):
                rec["_followed"] = True
                for child in rec["links"]:
                    self.save_page(child, rec["card"], "folha", level + 1)
            return rec
        try:
            raw, hc = fetch(url)
        except Exception as exc:
            print(f"  !! {url}: {exc}")
            return None
        enc = detect_encoding(raw, hc)
        text = raw.decode(enc, errors="replace")
        lp = local_path(self.raw, url)
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.with_suffix(lp.suffix + ".orig").write_bytes(raw)
        norm = normalize_html(text)
        lp.write_text(norm, encoding="utf-8")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        title = (soup.title.get_text(" ", strip=True) if soup.title else "") or lp.stem
        links, imgs = [], []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("mailto:", "javascript:", "#")):
                continue
            full = urljoin(url, href)
            if in_subtree(full, url) and full.lower().split("?")[0].endswith(PAGE_EXT):
                links.append(full)
        for im in soup.find_all("img", src=True):
            full = urljoin(url, im["src"].strip())
            imgs.append(full)
            if same_site(full, url):
                self.save_image(full)
        rec = {"url": url, "local": str(lp.relative_to(self.root)).replace("\\", "/"), "title": title, "encoding": enc,
               "card": card, "kind": kind, "level": level, "links": sorted(set(links)), "images": sorted(set(imgs)),
               "words": len(soup.get_text(" ").split())}
        self.pages[url] = rec
        print(f"  [{kind}] {url}  enc={enc} palavras={rec['words']} links={len(rec['links'])} img={len(rec['images'])}")
        if follow and level < self.depth:
            rec["_followed"] = True
            for child in rec["links"]:
                self.save_page(child, card, "folha", level + 1)
        return rec

    def save_image(self, url: str) -> None:
        if url in self.images:
            return
        self.images.add(url)
        lp = local_path(self.raw, url)
        if lp.exists():
            return
        try:
            raw, _ = fetch(url)
            lp.parent.mkdir(parents=True, exist_ok=True)
            lp.write_bytes(raw)
        except Exception as exc:
            print(f"  !! imagem {url}: {exc}")

    def save_material(self, rec: dict, stash: Path) -> Path:
        """S6d: a pagina vira MATERIAL no stash como bundle `stash/<card>/<Stem>/` = copia normalizada + imagens do
        mesmo host (as do dir da pagina no caminho relativo; as de fora pelo basename — ExercicioDuasCores escreve as
        proprias imagens como URL absoluta `~pinho/...`). Nunca `.orig`; imagem de outro host fica de fora (o build
        marca "nao capturada"). O bundle e 1 item html no scan; as imagens sao dele, nao entries."""
        page_url = rec["url"]
        page_local = self.root / rec["local"]
        bundle = stash / (rec["card"] or "sem-card") / page_local.stem
        bundle.mkdir(parents=True, exist_ok=True)
        dest = bundle / page_local.name
        dest.write_bytes(page_local.read_bytes())
        page_dir = unquote(urlparse(page_url).path).rsplit("/", 1)[0] + "/"
        for img in rec.get("images") or []:
            if not same_site(img, page_url):
                continue
            src = local_path(self.raw, img)
            if not src.is_file():
                continue
            img_path = unquote(urlparse(img).path)
            rel = img_path[len(page_dir):] if img_path.startswith(page_dir) else Path(img_path).name
            out = bundle / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(src.read_bytes())
        return dest

    def print_all(self) -> None:
        if not self.browser:
            print("  !! nenhum Edge/Chrome encontrado; --pdf ignorado")
            return
        for rec in self.pages.values():
            if rec.get("no_pdf"):
                continue
            out = self.stash / (rec["card"] or "sem-card") / f"{slug(rec['title'])}.pdf"
            ok = print_pdf(self.browser, self.root / rec["local"], out)
            pages, imgs = pdf_stats(out) if ok else (-1, -1)
            rec["pdf"] = str(out.relative_to(self.root)).replace("\\", "/") if ok else ""
            rec["pdf_pages"], rec["pdf_images"] = pages, imgs
            print(f"  [pdf] {out.name}: {'ok' if ok else 'FALHOU'} paginas={pages} imagens={imgs}")

    def write_links(self) -> None:
        self.raw.mkdir(parents=True, exist_ok=True)
        recs = [{k: v for k, v in r.items() if not k.startswith("_")} for r in self.pages.values()]
        (self.raw / "site_links.json").write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", help="URL@card (card = secao do Moodle que a pagina pertence)")
    ap.add_argument("--root", required=True)
    ap.add_argument("--depth", type=int, default=1, help="niveis de links relativos a seguir (hub -> folhas = 1)")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--syllabus", help="URL do cronograma (tabela SARC) -> cronograma.md; nunca vira PDF")
    args = ap.parse_args(argv)
    root = Path(args.root)
    t0 = time.time()
    snap = Snapshot(root, args.depth, args.pdf)
    targets = [(t.partition("@")[0], t.partition("@")[2].strip()) for t in args.targets]
    for url, card in targets:          # alvos explicitos primeiro (card deles manda), links depois
        snap.save_page(url, card, "hub", 0, follow=False)
    for url, card in targets:
        snap.save_page(url, card, "hub", 0, follow=True)
    if args.syllabus and args.syllabus in snap.pages:
        snap.pages[args.syllabus]["no_pdf"] = True   # cronograma nunca vira PDF
    if args.pdf:
        snap.print_all()
    snap.write_links()
    if args.syllabus:
        raw, hc = fetch(args.syllabus)
        enc = detect_encoding(raw, hc)
        text = raw.decode(enc, errors="replace")
        lp = local_path(snap.raw, args.syllabus)
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.with_suffix(lp.suffix + ".orig").write_bytes(raw)
        table = syllabus_table(text, args.syllabus)
        (root / "cronograma.md").write_text(table, encoding="utf-8")
        n = max(0, len(table.splitlines()) - 2)
        print(f"  [cronograma] enc={enc} -> cronograma.md: {n} linhas de dados")
    print(f"paginas={len(snap.pages)} imagens={len(snap.images)} em {time.time() - t0:.0f}s -> {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
