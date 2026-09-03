"""PILOTO Curvas.htm: HTML -> markdown (conversor do pipeline, com <img>) + imagens nao-logo pelo Datalab
(convert_document_to_markdown por imagem, cache em JSON) -> refs com proveniencia inline. Read-only fora do scratchpad."""
import json, re, sys, hashlib
from pathlib import Path
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator"); sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.utils.helpers  # noqa: F401  (carrega o .env com DATALAB_API_KEY; nunca imprimir)
from src.builder.text.url_markdown import html_to_structured_markdown, truncate_markdown_blocks
from src.builder.runtime.datalab_client import convert_document_to_markdown, has_datalab_api_key
from src.builder.engine import _detect_latex_corruption
ROOT = Path(__file__).parent / "piloto-curvas"; CACHE = ROOT / "datalab_cache.json"
html_path = next((ROOT / "raw").rglob("Curvas.htm")); html = html_path.read_text(encoding="utf-8")
url = "https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm"
md = html_to_structured_markdown(html, url, "Curvas Parametricas", collapse_ws=lambda s: " ".join(str(s).split()),
                                 truncate_markdown_blocks=lambda blocks: truncate_markdown_blocks(blocks, max_chars=200000))
refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
print(f"markdown {len(md)} chars | refs de imagem no markdown: {len(refs)}")
imgs = {p.name: p for p in (ROOT / "raw").rglob("*") if p.suffix.lower() in (".gif", ".png", ".jpg", ".jpeg")}
LOGOS = {"SomenteBrasao.png", "SomentePoliAzul.png", "logo_grv_low5.png"}
cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
assert has_datalab_api_key(), "sem DATALAB_API_KEY"
todo = [n for n in sorted(set(Path(r).name for r in refs)) if n in imgs and n not in LOGOS and n not in cache]
print(f"imagens a mandar ao Datalab: {len(todo)} (cache: {len(cache)})")
for n in todo:
    p = imgs[n]
    src = p
    if p.suffix.lower() == ".gif":   # GIF -> PNG (upscale x3: os GIFs de formula tem <1 KB)
        from PIL import Image
        im = Image.open(p).convert("RGB"); im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
        src = ROOT / "png" / (p.stem + ".png"); src.parent.mkdir(exist_ok=True); im.save(src)
    try:
        r = convert_document_to_markdown(src, mode="accurate", disable_image_captions=False, max_wait_seconds=300)
        cache[n] = {"markdown": r.markdown, "pages": r.page_count, "quality": r.parse_quality_score, "cost": r.cost_breakdown}
    except Exception as exc:
        cache[n] = {"erro": f"{type(exc).__name__}: {str(exc)[:200]}"}
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  {n:22} -> {str(cache[n].get('markdown', cache[n].get('erro')))[:110]!r}")
# composicao com proveniencia inline
def repl(m):
    alt, src = m.group(1), m.group(2); n = Path(src).name
    if n in LOGOS: return ""
    c = cache.get(n)
    if not c or "markdown" not in c: return f"![{n} — não capturada]({src})"
    txt = " ".join(c["markdown"].split())[:400]
    return f"![{n} — {txt}](images/{n})"
out = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, md)
(ROOT / "Curvas.piloto.md").write_text(out, encoding="utf-8")
corr = sum(1 for n, c in cache.items() if "markdown" in c and _detect_latex_corruption(c["markdown"]))
print(f"\nescrito {ROOT / 'Curvas.piloto.md'} ({len(out)} chars) | imagens com LaTeX corrompido (watchdog): {corr}/{len(cache)}")
