"""HTML salvo no stash como MATERIAL (SYNC S6b, 2026-09-03).

Pagina do professor / do Moodle -> markdown pelo conversor de URL (sem teto) e cada imagem da pagina
pelo Datalab CRU (GIF direto, sem PNG/upscale; piloto Curvas 03/09), com cache por md5 em
`course/.image_transcriptions.json` e cap por build. Formula -> bloco `$$` + fonte + item em
`manual-review/formulas/`; legenda do Datalab -> Gemini PT-BR -> `![Figura: ...]`; imagem que volta
vazia -> Gemini descreve; falha/externa/ausente -> `![x — não capturada]`. Imagens copiadas para
`content/images/<id>-<arquivo>` (o unprocess limpa por prefixo). Clientes chegam injetados
(`datalab_image_fn`, `gemini_text_fn`): os testes passam os falsos com o gold do piloto."""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import shutil
from pathlib import Path
from typing import Callable, Dict, Optional
from urllib.parse import unquote

from src.builder.text.url_markdown import html_to_structured_markdown, truncate_markdown_blocks
from src.utils.helpers import ensure_dir, safe_rel, write_text

logger = logging.getLogger(__name__)

HTML_IMAGE_DATALAB_CAP = 400
CACHE_REL = Path("course") / ".image_transcriptions.json"
PROMPT_LEGENDA = ("Traduza para portugues brasileiro esta legenda de figura de material de aula, "
                  "respondendo so com a legenda traduzida: ")
PROMPT_DESCRICAO = ("Descreva em uma frase, em portugues brasileiro, o conteudo desta figura de material "
                    "de aula (diagrama, grafico, formula ou animacao). Responda so com a descricao.")

_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_DATA_URI_RE = re.compile(r"^data:image/([A-Za-z0-9.+-]+);base64,(.+)$", re.S)
_CAPTION_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
# Bloco $$...$$ = formula (12/12 do gold Curvas); legenda tem so math inline ("$C_1$") na prosa.
_FORMULA_RE = re.compile(r"\$\$.+?\$\$", re.S)
_CHARSET_RE = re.compile(rb"""charset=["']?([\w-]+)""", re.I)


def datalab_image_markdown(path: Path) -> str:
    from src.builder.runtime.datalab_client import convert_document_to_markdown

    result = convert_document_to_markdown(path, mode="accurate", disable_image_captions=False,
                                          max_wait_seconds=300)
    return result.markdown or ""


def _read_html(path: Path) -> str:
    raw = path.read_bytes()
    declared = _CHARSET_RE.search(raw[:4096])
    for enc in ((declared.group(1).decode("ascii", "ignore") if declared else ""), "utf-8", "cp1252"):
        if not enc:
            continue
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _collapse(text) -> str:
    return " ".join(str(text).split())


class _PageImages:
    def __init__(self, builder, entry_id: str, html_dir: Path,
                 datalab_image_fn: Callable[[Path], str],
                 gemini_text_fn: Callable[..., str]):
        self.builder = builder
        self.root = builder.root_dir
        self.entry_id = entry_id
        self.html_dir = html_dir
        self.datalab = datalab_image_fn
        self.gemini = gemini_text_fn
        self.images_dir = ensure_dir(self.root / "content" / "images")
        self.cache_path = self.root / CACHE_REL
        self.cache: Dict[str, dict] = {}
        if self.cache_path.is_file():
            try:
                self.cache = json.loads(self.cache_path.read_text(encoding="utf-8")) or {}
            except Exception:
                self.cache = {}
        self.dirty = False
        self.stats = {"total": 0, "formulas": 0, "figuras": 0, "descritas": 0,
                      "nao_capturadas": 0, "datalab_calls": 0}

    def replace(self, match: re.Match) -> str:
        src = match.group(2).strip()
        self.stats["total"] += 1
        data = _DATA_URI_RE.match(src)
        if data:
            raw = base64.b64decode(data.group(2))
            ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(data.group(1).lower(), data.group(1).lower())
            name = f"data-{hashlib.md5(raw).hexdigest()[:8]}.{ext}"
            copy = self.images_dir / f"{self.entry_id}-{name}"
            copy.write_bytes(raw)
            to_datalab = copy
        elif src.startswith(("http://", "https://")):
            # URL absoluta: o bundle do snapshot (S6d) copia a imagem do mesmo host pelo basename para o dir da
            # pagina (ExercicioDuasCores escreve as proprias imagens como `https://.../~pinho/.../x.gif`).
            local = self.html_dir / Path(unquote(src.split("?", 1)[0])).name
            name = local.name
            if not local.is_file():
                return self._nao_capturada(name, src)
            raw = local.read_bytes()
            copy = self.images_dir / f"{self.entry_id}-{name}"
            shutil.copyfile(local, copy)
            to_datalab = local
        else:
            local = self.html_dir / unquote(src).replace("\\", "/")
            name = local.name
            if not local.is_file():
                return self._nao_capturada(name, src)
            raw = local.read_bytes()
            copy = self.images_dir / f"{self.entry_id}-{name}"
            shutil.copyfile(local, copy)
            to_datalab = local
        rel = safe_rel(copy, self.root).replace("\\", "/")
        key = hashlib.md5(raw).hexdigest()
        rec = self.cache.get(key)
        if rec is None:
            calls = getattr(self.builder, "_html_datalab_calls", 0)
            if calls >= HTML_IMAGE_DATALAB_CAP:
                return self._nao_capturada(name, rel, f" (cap {HTML_IMAGE_DATALAB_CAP})")
            self.builder._html_datalab_calls = calls + 1
            self.stats["datalab_calls"] += 1
            try:
                rec = {"markdown": self.datalab(to_datalab) or ""}
            except Exception as exc:
                logger.warning("Datalab falhou em %s (%s): %s", name, self.entry_id, exc)
                return self._nao_capturada(name, rel)
            self.cache[key] = rec
            self.dirty = True
        return self._render(name, rel, copy, rec)

    def _render(self, name: str, rel: str, copy: Path, rec: dict) -> str:
        md = str(rec.get("markdown") or "").strip()
        captions = _CAPTION_RE.findall(md)
        rest = _CAPTION_RE.sub("", md).strip()
        if _FORMULA_RE.search(rest):
            self.stats["formulas"] += 1
            self._write_formula_review(name, rel, md)
            return f"\n\n{md}\n<sub>fonte: [{name}]({rel})</sub>\n\n"
        # Datalab devolve caption + paragrafo descrevendo a MESMA figura: a caption basta.
        english = _collapse(" ".join(captions)) if captions else _collapse(rest)
        if english:
            pt = self._gemini_cached(rec, PROMPT_LEGENDA + english)
            self.stats["figuras"] += 1
            return f"![Figura: {pt or english}]({rel})"
        pt = self._gemini_cached(rec, PROMPT_DESCRICAO, copy)
        if pt:
            self.stats["descritas"] += 1
            return f"![Figura: {pt}]({rel})"
        return self._nao_capturada(name, rel)

    def _gemini_cached(self, rec: dict, prompt: str, image_path: Optional[Path] = None) -> str:
        pt = rec.get("pt")
        if pt is None:
            try:
                pt = _collapse(self.gemini(prompt, image_path) if image_path else self.gemini(prompt))
            except Exception as exc:
                logger.warning("Gemini falhou (%s): %s", self.entry_id, exc)
                pt = ""
            if pt:
                rec["pt"] = pt
                self.dirty = True
        return pt or ""

    def _nao_capturada(self, name: str, target: str, extra: str = "") -> str:
        self.stats["nao_capturadas"] += 1
        return f"![{name} — não capturada{extra}]({target})"

    def _write_formula_review(self, name: str, rel: str, latex: str) -> None:
        path = self.root / "manual-review" / "formulas" / f"{self.entry_id}-{Path(name).stem}.md"
        write_text(path, (
            "---\n"
            f"id: {self.entry_id}\n"
            "type: manual_formula_review\n"
            f"source_image: {rel}\n"
            "---\n\n"
            f"# Fórmula transcrita — {name}\n\n"
            f"![{name}]({rel})\n\n"
            f"{latex}\n\n"
            "- [ ] conferir com o professor (transcrição fiel da imagem; erros da fonte NÃO foram corrigidos)\n"
        ))

    def save_cache(self) -> None:
        if self.dirty:
            write_text(self.cache_path, json.dumps(self.cache, ensure_ascii=False, indent=1, sort_keys=True))


def process_html(builder, entry, raw_target: Path, *, datalab_image_fn, gemini_text_fn) -> Dict[str, object]:
    item: Dict[str, object] = {
        "document_report": None,
        "pipeline_decision": None,
        "base_markdown": None,
        "advanced_markdown": None,
        "advanced_backend": None,
        "base_backend": "html_converter",
        "manual_review": None,
    }
    markdown = html_to_structured_markdown(
        _read_html(raw_target), "", entry.title, collapse_ws=_collapse,
        truncate_markdown_blocks=lambda blocks: truncate_markdown_blocks(blocks, max_chars=None),
    )
    images = _PageImages(builder, entry.id(), Path(entry.source_path).parent, datalab_image_fn, gemini_text_fn)
    markdown = re.sub(r"\n{3,}", "\n\n", _IMG_RE.sub(images.replace, markdown))
    images.save_cache()
    md_file = builder.root_dir / "staging" / "markdown-auto" / "html" / f"{entry.id()}.md"
    write_text(md_file, markdown)
    item["base_markdown"] = safe_rel(md_file, builder.root_dir)
    item["html_images"] = dict(images.stats)
    builder.logs.append({"entry": entry.id(), "step": "html_import", "status": "ok", **images.stats})
    return item
