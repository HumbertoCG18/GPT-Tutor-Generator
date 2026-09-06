"""Camada 3 (resumos de codigo por Gemini) — ablacao e substituto deterministico, nas copias .ablacao, tripwire.
Modos: sem      = code_curation.json vazio (nenhum texto para zips/codigo)
       determ   = code_curation.json SINTETICO a partir dos .md que o motor ja gera (base_markdown + extracted_files; v1 lia zip/ipynb cru),
                  no MESMO formato do resumo do Gemini (inferred_title / summary / concepts / language): mesma rota, produtor diferente.
Alvos: puro (5 cursos, --com-vocab) · auto (5, voter cacheado) · holdout / autoholdout (CG). Uso: shim_codigo.py {sem|determ} {puro|auto|holdout|autoholdout}"""
import io
import json
import re
import runpy
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MODE, TARGET = sys.argv[1], sys.argv[2]
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (tripwire)")


_gc.GeminiClient.__init__ = _bloqueado
import ablacao_rapida as ab  # noqa: E402
import reprocess_assignments as ra  # noqa: E402

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|[_\-./\\ ]+")
_COMMENT = re.compile(r"^\s*(//|#|\*|/\*|--|\(\*|%|;)\s*(.*)$")
_WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9]{3,}")
_STOP = {"return", "import", "include", "public", "private", "static", "void", "int", "float", "double", "string", "const", "class",
         "self", "this", "true", "false", "null", "none", "print", "printf", "main", "args", "argv", "using", "namespace", "from",
         "while", "else", "elif", "break", "continue", "define", "ifdef", "endif", "begin", "end", "then", "with", "that", "this"}


def _texto_do_codigo(raw: str, nome: str) -> tuple:
    """(comentarios, identificadores) de um arquivo de codigo."""
    coments, ids = [], Counter()
    for line in raw.splitlines()[:600]:
        m = _COMMENT.match(line)
        if m and m.group(2).strip():
            coments.append(m.group(2).strip())
        for w in _WORD.findall(line):
            for part in _CAMEL.split(w):
                p = part.lower()
                if len(p) >= 4 and p not in _STOP and not p.isdigit():
                    ids[p] += 1
    return coments, ids


_FRONT = re.compile(r"^---\n.*?\n---\n", re.S)
_FENCE = re.compile(r"^```.*$", re.M)
_HEAD = re.compile(r"^#{1,6}\s+(.*)$")
_CELULA = re.compile(r"^C.lula \d+ . ", re.I)


def _bundle_md(entry: dict, repo: Path) -> list:
    """(titulo_do_arquivo, texto) dos .md que o motor JA gerou para o material — o mesmo bundle de `_build_bundle_text`."""
    out = []
    bm = entry.get("base_markdown")
    if bm and (repo / bm).is_file():
        out.append((str(entry.get("title") or ""), (repo / bm).read_text(encoding="utf-8", errors="replace")))
    for ef in entry.get("extracted_files") or []:
        em = ef.get("base_markdown")
        if em and (repo / em).is_file():
            out.append((Path(str(ef.get("title") or em)).name, (repo / em).read_text(encoding="utf-8", errors="replace")))
    return out


def _sintetico(entry: dict, repo: Path) -> dict:
    """Resumo deterministico no formato do Gemini, a partir dos .md do bundle (v2; v1 lia o zip/ipynb cru)."""
    ml = entry.get("moodle_label")
    ml = ml.get("text") if isinstance(ml, dict) else ml
    nomes, prosa, ids, lang = [], [], Counter(), ""
    for nome, md in _bundle_md(entry, repo):
        nomes.append(" ".join(p for p in _CAMEL.split(Path(nome).stem) if p))
        body = _FRONT.sub("", md, count=1)
        m = re.search(r"\*\*Linguagem:\*\*\s*(\w+)", body)
        if m and not lang:
            lang = m.group(1)
        em_codigo = False
        for line in body.splitlines()[:800]:
            if _FENCE.match(line):
                em_codigo = not em_codigo
                continue
            h = _HEAD.match(line)
            if h:
                if not _CELULA.match(h.group(1)):
                    prosa.append(h.group(1).strip())
                continue
            if em_codigo:
                c = _COMMENT.match(line)
                if c and c.group(2).strip():
                    prosa.append(c.group(2).strip())
                for w in _WORD.findall(line):
                    for part in _CAMEL.split(w):
                        q = part.lower()
                        if len(q) >= 4 and q not in _STOP and not q.isdigit():
                            ids[q] += 1
            elif line.strip() and not line.startswith(">") and not line.startswith("|"):
                prosa.append(line.strip())      # prosa de celula markdown do notebook / README
    title = f"{ml or entry.get('title') or ''} {' '.join(dict.fromkeys(nomes))}".strip()
    return {"summary": {"inferred_title": title[:200], "summary": " ".join(dict.fromkeys(prosa))[:1500],
                        "concepts": [w for w, _ in ids.most_common(30)], "language": lang},
            "content_hash": "determ", "matcher_version": 0, "model": "determ-v2", "generated_at": "determ"}


_ablate_orig = ab.ablate


def _ablate_codigo(repo, keep_llm_vocab=False):
    n = _ablate_orig(repo, keep_llm_vocab=True)
    repo = Path(repo)
    src = GH / repo.name / "material_curation.json"
    if src.exists():
        shutil.copy2(src, repo / "material_curation.json")
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    if MODE == "sem":
        cc = {"version": 1, "entries": {}}
    else:
        cc = {"version": 1, "entries": {e["id"]: _sintetico(e, repo) for e in man if e.get("category") == "codigo-professor" or e.get("file_type") in ("code", "zip")}}
    (repo / "code_curation.json").write_text(json.dumps(cc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [codigo:{MODE}] {repo.name}: {len(cc['entries'])} resumos", flush=True)
    return n


ab.ablate = _ablate_codigo
_merge_orig = ra._merge_profile_flags
_reprocess_orig = ra.reprocess


def _reprocess_com_voter(repo, flags, store=None):
    ra._merge_profile_flags = _merge_orig
    return _reprocess_orig(repo, flags, store)


if TARGET in ("auto", "autoholdout"):
    ra.reprocess = _reprocess_com_voter
if TARGET in ("puro", "auto"):
    import motor_puro
    sys.exit(motor_puro.main(["--com-vocab"]))
else:
    sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py"), str(GEN), str(GEN / ".ablacao")]
    runpy.run_path(sys.argv[0], run_name="__main__")
