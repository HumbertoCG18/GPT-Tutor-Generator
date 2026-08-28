"""PDF -> markdown via pymupdf4llm, com duas correcoes de raiz (2026-08-28).

1. `pymupdf4llm >= 1.27` monta o layout com `TEXT_IGNORE_ACTUALTEXT`: PDFs que codificam
   caracteres via `/ActualText` (Google Docs + fonte Inter: `( + ) :`) saem como glifos
   privados (U+E081 `(`, U+E09D `+`, U+E082 `)`, U+E092 `:`). Medido no plano do TCC:
   `G1 = (P1+P2+T)/3` virava `G1 = \ue081P1\ue09dP2\ue09dT\ue082/3`; sem a flag, 0 PUA e
   texto identico ao extraido pela versao anterior (ratio 1,000 em TCC/SO/ES2).
2. `use_ocr=True` (default) OCR-iza e DESCARTA o texto nativo de paginas com logo + texto
   (`needs_ocr: img_text`): SO/Lab SO/Fund. Redes perdiam ~400 chars e acentos. OCR so
   quando a pagina nao tem texto nativo.
3. Fracao EMPILHADA (numerador / barra vetorial / denominador — equacao do Word/LaTeX):
   o texto sai sem a divisao ("G1 = P1 + P2 + TP" e, noutra linha, "3"). Medido em SO, MF
   e ES2 (a media do G1). Deteccao GEOMETRICA, sem lexico: regua horizontal curta e
   isolada (sem borda vertical nas pontas, sem regua vizinha — tabela tem as duas), texto
   cobrindo-a por cima e texto centrado por baixo -> a linha vira `lhs = (num) / den`.
"""
from __future__ import annotations

import re
import unicodedata
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def respect_actualtext():
    """Tira TEXT_IGNORE_ACTUALTEXT das FLAGS do layout do pymupdf4llm durante a chamada."""
    try:
        import pymupdf
        import pymupdf4llm.helpers.document_layout as layout
    except ImportError:  # pymupdf4llm ausente ou versao sem o modulo: nada a corrigir
        yield
        return
    flags = getattr(layout, "FLAGS", None)
    if flags is None:
        yield
        return
    layout.FLAGS = flags & ~pymupdf.TEXT_IGNORE_ACTUALTEXT
    try:
        yield
    finally:
        layout.FLAGS = flags


def pdf_has_native_text(pdf_path: str | Path) -> bool:
    import pymupdf
    with pymupdf.open(str(pdf_path)) as doc:
        return any(page.get_text().strip() for page in doc)


def pdf_to_markdown(pdf_path: str | Path, **kwargs) -> str:
    """`pymupdf4llm.to_markdown` com ActualText respeitado e OCR so sem texto nativo
    (a menos que o chamador passe `use_ocr`/`force_ocr` explicitamente)."""
    import pymupdf4llm
    if "use_ocr" not in kwargs and not kwargs.get("force_ocr"):
        kwargs["use_ocr"] = not pdf_has_native_text(pdf_path)
    with respect_actualtext():
        md = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)
    if isinstance(md, str):
        try:
            fracoes = stacked_fractions(pdf_path)
        except Exception:  # detector e bonus: nunca derruba a extracao
            fracoes = []
        if fracoes:
            md = splice_fractions(md, fracoes)
    return md


# ---------------------------------------------------------------- fracoes empilhadas
_SUBSCRIPT_RATIO = 0.85   # span menor que 85% do corpo principal = subscrito ("P" + "1")


def _texto_dos_spans(spans: list) -> str:
    """Concatena spans em ordem de x; subscrito cola no anterior (P + 1 -> P1)."""
    spans = sorted(spans, key=lambda s: s["bbox"][0])
    corpo = max(s["size"] for s in spans)
    out = ""
    for s in spans:
        t = s["text"]
        if out and s["size"] < _SUBSCRIPT_RATIO * corpo:
            out = out.rstrip() + t.strip()
        else:
            out += ("" if not out or out.endswith(" ") or t.startswith(" ") else " ") + t
    return " ".join(out.split())


def stacked_fractions(pdf_path: str | Path) -> list[dict]:
    """[{page, lhs, numerator, denominator}] das fracoes desenhadas como barra vetorial.

    Criterios (todos geometricos): regua horizontal fina (h <= 1.5) e curta (8..250 pt);
    isolada — nenhuma outra regua horizontal a menos de 20 pt cobrindo o mesmo x, nenhuma
    regua vertical tocando as pontas (grade de tabela); texto imediatamente acima cobrindo
    >= 60% da barra e terminando dentro dela; texto imediatamente abaixo, mais estreito que
    a barra e centrado nela. O que sobra a esquerda da barra na linha do numerador e o `lhs`
    ("G1 =") — pode estar no mesmo span do numerador (SO) ou em span proprio (MF/ES2)."""
    import pymupdf
    out = []
    with pymupdf.open(str(pdf_path)) as doc:
        for pno, page in enumerate(doc):
            spans = [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", [])
                     for s in l.get("spans", []) if s["text"].strip()]
            rects = [d["rect"] for d in page.get_drawings()]
            horiz = [r for r in rects if r.height <= 1.5 and 8 <= r.width <= 250]
            vert = [r for r in rects if r.width <= 1.5 and r.height >= 8]
            for r in horiz:
                if any(o is not r and abs(o.y0 - r.y0) <= 20 and abs(o.y0 - r.y0) > 0.5
                       and min(o.x1, r.x1) - max(o.x0, r.x0) > 0 for o in horiz):
                    continue
                if any((abs(v.x0 - r.x0) <= 3 or abs(v.x0 - r.x1) <= 3) and v.y0 - 3 <= r.y0 <= v.y1 + 3 for v in vert):
                    continue

                def overl(s):
                    return min(s["bbox"][2], r.x1) - max(s["bbox"][0], r.x0)
                above = [s for s in spans if -3 <= r.y0 - s["bbox"][3] <= 6 and overl(s) > 0]
                below = [s for s in spans if -1 <= s["bbox"][1] - r.y1 <= 6 and overl(s) > 0]
                if not above or not below:
                    continue
                cobre = max(s["bbox"][2] for s in above) - min(max(s["bbox"][0], r.x0) for s in above)
                if cobre < 0.6 * r.width or max(s["bbox"][2] for s in above) > r.x1 + 8:
                    continue
                bx0, bx1 = min(s["bbox"][0] for s in below), max(s["bbox"][2] for s in below)
                if abs((bx0 + bx1) / 2 - (r.x0 + r.x1) / 2) > 0.25 * r.width or (bx1 - bx0) > 0.9 * r.width:
                    continue
                y_top = min(s["bbox"][1] for s in above)
                left = [s for s in spans if s not in above and s["bbox"][2] <= r.x0 + 2
                        and abs(s["bbox"][1] - y_top) < 8 and r.x0 - s["bbox"][2] < 30]
                num = _texto_dos_spans(above)
                lhs = _texto_dos_spans(left) if left else ""
                if "=" in num and not lhs:          # "G1 = P1 + P2 + TP" num span so (SO)
                    lhs, num = num.split("=", 1)
                    lhs = lhs.strip() + " ="
                out.append({"page": pno, "lhs": lhs.strip(), "numerator": num.strip(),
                            "denominator": _texto_dos_spans(below)})
    return out


def _chave(texto: str) -> str:
    return re.sub(r"[^0-9a-z]", "", unicodedata.normalize("NFKC", texto).lower())


def _canonico(fr: dict) -> str:
    num = unicodedata.normalize("NFKC", fr["numerator"]).strip()
    den = unicodedata.normalize("NFKC", fr["denominator"]).strip()
    if re.search(r"[+\-]", num) and not (num.startswith("(") and num.endswith(")")):
        num = f"({num})"
    lhs = unicodedata.normalize("NFKC", fr["lhs"]).strip()
    return f"{lhs} {num} / {den}".strip()


def splice_fractions(md: str, fractions: list[dict]) -> str:
    """Reescreve no markdown a linha do numerador como `lhs (num) / den` e remove o
    denominador (fim da mesma linha ou linha seguinte). Numerador nao achado -> deixa como esta."""
    lines = md.splitlines()
    for fr in fractions:
        k_num, k_den = _chave(fr["numerator"]), _chave(fr["denominator"])
        if not k_num or not k_den:
            continue
        for i, line in enumerate(lines):
            k_line = _chave(line)
            if k_num not in k_line:
                continue
            j = next((j for j in range(i + 1, min(i + 3, len(lines))) if lines[j].strip()), None)
            mesma = k_line.endswith(k_num + k_den)
            proxima = j is not None and _chave(lines[j]) == k_den
            # A fracao ja foi PROVADA pela geometria: reescreve a linha do numerador mesmo
            # que o denominador nao tenha chegado ao texto (o layout pode te-lo tratado como
            # figura); a linha do denominador so e removida se existir.
            m = re.match(r"^(\W*)(.*?)(\**\s*)$", line)
            prefixo, sufixo = m.group(1), m.group(3).strip()
            lines[i] = f"{prefixo}{_canonico(fr)}{sufixo}"
            if proxima:
                del lines[j]
            break
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")
