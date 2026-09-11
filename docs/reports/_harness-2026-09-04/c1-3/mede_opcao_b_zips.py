"""Opcao b, 0 chamadas: quanto insumo os zips acrescentariam a compilacao de vocabulario.
Hoje _bundle le _entry_markdown_text_for_file_map (zip -> vazio). Com b leria _build_bundle_text (membros)."""
import json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
ROOT = Path(__file__).resolve()
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from src.builder.core.vocabulary_compile import _is_material, OUT_CATS, _extract_markdown_headings  # noqa
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa
from src.builder.core.code_summarization import _build_bundle_text  # noqa

TUTORES = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "FR": "Fundamentos-de-Redes-Tutor",
           "IA": "Inteligencia-Artifical-Tutor", "LR": "Laboratorio-de-Redes-Tutor", "MF": "Metodos-Formais-Tutor",
           "SO": "Sistemas-Operacionais-Tutor", "TCC": "TCC-Tutor"}
PAT = re.compile(r"thread|perceptron|mlp|xor|roteiro", re.I)
print(f"{'curso':4} {'mats':>4} {'unid':>4} {'zips':>4} {'zip-md-vazio':>12} {'heads-hoje':>10} {'heads-b':>8} {'chars-b':>8} {'outros-vazios':>13}")
tot = Counter()
casos = []
for sig, nome in TUTORES.items():
    root = REPO.parent / nome
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    mats = [e for e in man if _is_material(e) and str(e.get("category") or "").strip().lower() not in OUT_CATS]
    unid = {str(e.get("computed_unit_slug") or "").strip() for e in mats} - {""}
    zips = [e for e in mats if e.get("file_type") == "zip"]
    b = SimpleNamespace(root_dir=root)
    zvazio = hhoje = hb = cb = 0
    for e in zips:
        md = _entry_markdown_text_for_file_map(root, e) or ""
        hh = len(_extract_markdown_headings(md, limit=24))
        bt = _build_bundle_text(b, e)
        hbb = len(_extract_markdown_headings(bt, limit=24))
        zvazio += (not md.strip()); hhoje += hh; hb += hbb; cb += len(bt)
        if PAT.search(str(e.get("title", "")) + " " + str(e.get("id", ""))):
            casos.append((sig, e.get("id"), [str(f.get("title")) for f in (e.get("extracted_files") or [])][:6]))
    outros = sum(1 for e in mats if e.get("file_type") != "zip" and not (_entry_markdown_text_for_file_map(root, e) or "").strip())
    print(f"{sig:4} {len(mats):4} {len(unid):4} {len(zips):4} {zvazio:12} {hhoje:10} {hb:8} {cb:8} {outros:13}")
    tot.update(mats=len(mats), unid=len(unid), zips=len(zips), zvazio=zvazio, hb=hb, outros=outros)
print(f"{'tot':4} {tot['mats']:4} {tot['unid']:4} {tot['zips']:4} {tot['zvazio']:12} {'':10} {tot['hb']:8} {'':8} {tot['outros']:13}")
print("\nzips que casam thread|perceptron|mlp|xor|roteiro (o que b entregaria ao compilador = nomes dos membros):")
for sig, i, membros in casos:
    print(f"  {sig} {i}: {membros}")
print("\narquivos ocultos em course/ (MF), para achar a taxonomia:", sorted(p.name for p in (REPO.parent / TUTORES['MF'] / 'course').glob('.*.json')))
