"""Camada 3 (resumos de codigo por Gemini) — ablacao e substituto deterministico, nas copias .ablacao, tripwire.
Modos: com      = resumos reais do sync (referencia, 11/09)
       sem      = code_curation.json vazio (nenhum texto para zips/codigo)
       determ   = code_curation.json SINTETICO a partir dos .md que o motor ja gera (base_markdown + extracted_files; v1 lia zip/ipynb cru),
                  no MESMO formato do resumo do Gemini (inferred_title / summary / concepts / language): mesma rota, produtor diferente.
Alvos: puro (5 cursos, --com-vocab) · auto (5, voter cacheado) · holdout / autoholdout (CG). Uso: shim_codigo.py {sem|determ} {puro|auto|holdout|autoholdout}"""
import io
import json
import os
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


_ALS: set = set()   # aliases do curso; _ablate_codigo preenche antes de sintetizar (11/09)


def _aliases_do_curso(repo: Path) -> set:
    """Aliases dos topicos + sinonimos do vocabulario LLM da copia. Vocabulario de categoria que o codigo bruto so tem
    dentro de identificador (RabbitMQConfig) ou de frase (circuit breaker fallback). 11/09, experimentos do astra."""
    from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
    tax = load_internal_content_taxonomy(repo)
    als = {a for u in tax.get("units", []) for t in u.get("topics", []) for a in t.get("aliases", [])}
    llm = repo / "course/.glossary_curation.llm.json"
    if llm.is_file():
        als |= {a for k, v in json.loads(llm.read_text(encoding="utf-8")).items()
                if not k.startswith("_") and isinstance(v, dict) for a in v.get("synonyms", [])}
    return {a for a in als if len(a) >= 4}


def _sintetico(entry: dict, repo: Path) -> dict:
    """Resumo deterministico no formato do Gemini, a partir dos .md do bundle (v3, 11/09; v2 = tokens soltos; v1 lia o zip cru).
    v3: (a) material com .md proprio nao ganha resumo (o leitor ja entrega o texto; duplicar promovia o label Moodle a heading);
    (b) alias do curso presente em identificador CamelCase ou como frase literal no codigo entra em concepts na forma do alias."""
    if entry.get("base_markdown"):
        return {}
    ml = entry.get("moodle_label")
    ml = ml.get("text") if isinstance(ml, dict) else ml
    nomes, prosa, ids, lang = [], [], Counter(), ""
    bruto = []
    for nome, md in _bundle_md(entry, repo):
        bruto.append(md)
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
    raw = " ".join(bruto)
    words = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", raw))
    hits = {a for a in _ALS if re.search(r"[A-Za-z]", a) and any(
        re.search(r"(?<![a-z])" + re.escape(a.replace(" ", "")) + r"(?=[A-Z_0-9]|$)", w) for w in words)}
    hits |= {a for a in _ALS if _frase(raw, a)}
    title = f"{ml or entry.get('title') or ''} {' '.join(dict.fromkeys(nomes))}".strip()
    return {"summary": {"inferred_title": title[:200], "summary": " ".join(dict.fromkeys(prosa))[:1500],
                        "concepts": [w for w, _ in ids.most_common(30)] + sorted(hits), "language": lang},
            "content_hash": "determ", "matcher_version": 0, "model": "determ-v3", "generated_at": "determ"}


import functools
import src.builder.timeline.index as _ti
_frase = functools.lru_cache(maxsize=200000)(_ti._matches_normalized_phrase)
def _reimporta_zips(repo: Path) -> None:
    """11/09 (REIMPORTA_ZIPS=1): re-extrai cada zip da copia com o process_zip corrigido (membro leva o id do zip) e
    atualiza extracted_files no manifest. 0 chamadas: process_code nao chama LLM; code_curation.json segue por id do zip."""
    from types import SimpleNamespace
    from src.builder.core import source_importers as si
    from src.models.core import FileEntry
    mp = repo / "manifest.json"; man = json.loads(mp.read_text(encoding="utf-8"))
    b = SimpleNamespace(root_dir=repo, logs=[]); n = m = 0
    for e in man["entries"]:
        raw = repo / str(e.get("raw_target") or "")
        if e.get("file_type") != "zip" or not e.get("raw_target") or not raw.is_file():
            continue
        fe = FileEntry(source_path=str(raw), file_type="zip", category=e.get("category") or "codigo-professor",
                       title=e.get("title") or e["id"], id_override=e["id"])
        item = si.process_zip(b, fe, raw)
        if item.get("extraction_error"):
            print(f"  [zip] {repo.name}/{e['id']}: {item['extraction_error']}", flush=True); continue
        e["extracted_files"] = item["extracted_files"]; e["file_count"] = item["file_count"]; n += 1; m += item["file_count"]
    mp.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    mds = [f.get("base_markdown") for e in man["entries"] if e.get("file_type") == "zip" for f in (e.get("extracted_files") or [])]
    print(f"  [zip] {repo.name}: {n} zips re-extraidos, {m} membros, md distintos {len(set(mds))}", flush=True)


_ablate_orig = ab.ablate


def _ablate_codigo(repo, keep_llm_vocab=False):
    n = _ablate_orig(repo, keep_llm_vocab=True)
    repo = Path(repo)
    if repo.name in os.environ.get("VOCAB_ANTIGO", "").split(","):   # 11/09: regime "vocab antigo" sem tocar no original
        (repo / "course/.glossary_curation.llm.json").unlink(missing_ok=True)
        print(f"  [vocab:antigo] {repo.name}: .llm.json removido da copia", flush=True)
    if os.environ.get("REIMPORTA_ZIPS"):
        _reimporta_zips(repo)
    src = GH / repo.name / "material_curation.json"
    if src.exists():
        shutil.copy2(src, repo / "material_curation.json")
    if MODE == "com":                      # 11/09: referencia com os resumos reais (code_curation.json do sync), mesma regua
        print(f"  [codigo:com] {repo.name}: resumos originais mantidos", flush=True)
        return n
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    global _ALS
    _ALS = _aliases_do_curso(repo)
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
