"""Auditoria de entries DUPLICADAS nos repos-tutor, em 3 niveis de certeza.

    python scripts/detecta_duplicatas.py                    # 6 cursos
    python scripts/detecta_duplicatas.py --repos SO,MF      # subconjunto
    python scripts/detecta_duplicatas.py --quase 0.85       # limiar do nivel 3

Niveis (do certo para o provavel):
  BYTES      sha256 do arquivo raw identico -> 100% o MESMO arquivo (dedup do
             motor ja agrupa esses no voto via content_key/md5, sem reportar).
  PDF-TEXTO  sha256 do texto POR PAGINA (pymupdf, mesmo extrator no mesmo
             momento) identico -> 100% o mesmo documento; os bytes diferem so
             em metadados (caso real CG: pares com 4-6 bytes de diferenca =
             /Title com id do Moodle + /CreationDate + /ModDate).
  TEXTO      sha256 do markdown extraido NORMALIZADO identico -> mesmo documento
             em extracoes de builds diferentes (caso real: SO plano-de-ensino vs
             programa; formatacao ****x**** vs **x**, descricoes de imagem).
  QUASE      difflib ratio >= limiar entre textos normalizados -> triagem humana.

Read-only: nao muda manifest nem motor. Saida = relatorio por curso.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from eval_entry_unit import COURSES as _COURSES, GITHUB_DIR  # noqa: E402

COURSES = dict(_COURSES)
COURSES.setdefault("CG", "Computacao-Grafica-Tutor")

_MD_KEYS = ("approved_markdown", "curated_markdown", "base_markdown")


def _raw_path(repo: Path, entry: dict) -> Path | None:
    """Arquivo fisico da entry: raw_target do repo; fallback source_path local."""
    rel = str(entry.get("raw_target") or "")
    if rel and (repo / rel).is_file():
        return repo / rel
    sp = str(entry.get("source_path") or "")
    if sp and not sp.startswith(("http://", "https://")) and Path(sp).is_file():
        return Path(sp)
    return None


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _texto_normalizado(repo: Path, entry: dict) -> str:
    """Markdown da entry sem os artefatos que variam entre extracoes do mesmo
    documento: comentarios/blocos gerados, descricoes de imagem, formatacao
    (* _ # > -), digitos de ancora {N}---, whitespace. Casefold no fim."""
    rel = next((entry.get(k) for k in _MD_KEYS if entry.get(k)), None)
    if not rel or not str(rel).endswith(".md") or not (repo / str(rel)).is_file():
        return ""
    txt = (repo / str(rel)).read_text(encoding="utf-8", errors="replace")
    txt = re.split(r"<!--\s*IMAGE_DESCRIPTION_ORPHANS", txt)[0]
    txt = re.sub(r"<!--.*?-->", " ", txt, flags=re.S)
    txt = re.sub(r"^>.*\[Descri[cç][aã]o de imagem\].*$", " ", txt, flags=re.M)
    txt = re.sub(r"\{\d+\}-{2,}", " ", txt)
    txt = re.sub(r"[*_#>`|-]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip().casefold()


def rodar(siglas: list[str], quase: float) -> int:
    total = 0
    for sigla in siglas:
        repo = GITHUB_DIR / COURSES[sigla]
        manp = repo / "manifest.json"
        if not manp.exists():
            continue
        entries = json.loads(manp.read_text(encoding="utf-8")).get("entries") or []
        por_bytes: dict[str, list] = {}
        textos: dict[str, str] = {}
        rotulo: dict[str, str] = {}
        for e in entries:
            eid = str(e.get("id") or "")
            if not eid:
                continue
            rotulo[eid] = f"{eid}  ({str(e.get('source_section') or '')[:30]})"
            p = _raw_path(repo, e)
            if p is not None:
                por_bytes.setdefault(_sha256_file(p), []).append(eid)
            t = _texto_normalizado(repo, e)
            if len(t) >= 200:  # texto curto demais colide por pobreza, nao por duplicata
                textos[eid] = t

        achados = []
        byte_dups = {h: ids for h, ids in por_bytes.items() if len(ids) > 1}
        pareados = set()
        for ids in byte_dups.values():
            achados.append(("BYTES", ids))
            pareados.update(ids)

        # PDF-TEXTO: texto por pagina via pymupdf (mesmo extrator, agora) —
        # independe do markdown de builds antigos e ignora metadados do arquivo.
        try:
            import pymupdf
        except ImportError:
            pymupdf = None
        if pymupdf is not None:
            por_pdf: dict[str, list] = {}
            for e in entries:
                eid = str(e.get("id") or "")
                if not eid or eid in pareados:
                    continue
                p = _raw_path(repo, e)
                if p is None or p.suffix.lower() != ".pdf":
                    continue
                try:
                    with pymupdf.open(p) as doc:
                        h = hashlib.sha256(str(doc.page_count).encode())
                        for pg in doc:
                            h.update(pg.get_text().encode())
                except Exception:
                    continue
                por_pdf.setdefault(h.hexdigest(), []).append(eid)
            for ids in (v for v in por_pdf.values() if len(v) > 1):
                achados.append(("PDF-TEXTO", ids))
                pareados.update(ids)

        por_texto: dict[str, list] = {}
        for eid, t in textos.items():
            if eid in pareados:
                continue
            por_texto.setdefault(hashlib.sha256(t.encode()).hexdigest(), []).append(eid)
        for ids in (v for v in por_texto.values() if len(v) > 1):
            achados.append(("TEXTO", ids))
            pareados.update(ids)

        # Par enunciado<->gabarito (X vs X_respostas) NAO e duplicata: o gabarito
        # embute o enunciado e passa do limiar (ES2 revisao-p2 0.940). Mesmo
        # pareador da FASE 4.
        from src.builder.artifacts.repo import _exercise_answer_stem
        titulo = {str(e.get("id") or ""): str(e.get("title") or "") for e in entries}
        livres = [eid for eid in textos if eid not in pareados]
        for i, a in enumerate(livres):
            for b in livres[i + 1:]:
                sa, ga = _exercise_answer_stem(titulo.get(a, a))
                sb, gb = _exercise_answer_stem(titulo.get(b, b))
                if sa == sb and ga != gb:
                    continue
                sm = difflib.SequenceMatcher(None, textos[a], textos[b])
                # quick_ratio e cota superior barata: poda o ratio() caro
                if sm.quick_ratio() >= quase and sm.ratio() >= quase:
                    achados.append((f"QUASE {sm.ratio():.3f}", [a, b]))

        print(f"== {sigla}: {len(achados)} grupo(s) duplicado(s)")
        for nivel, ids in achados:
            total += 1
            print(f"   [{nivel}]")
            for eid in ids:
                print(f"      {rotulo.get(eid, eid)}")
    return total


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", default=",".join(COURSES))
    ap.add_argument("--quase", type=float, default=0.90)
    args = ap.parse_args(argv[1:])
    siglas = [s.strip().upper() for s in args.repos.split(",") if s.strip()]
    rodar(siglas, args.quase)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
