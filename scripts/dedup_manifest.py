"""Remove entries DUPLICADAS do manifest (mesmo conteudo, vindas de re-import).

Contexto: quando um repo e re-processado de uma fonte nova (ex.: stash atual em
Desktop/Moodle) sem purgar as entries antigas (ex.: source_path em Downloads), cada
arquivo vira DUAS entries — a antiga + a nova do stash. Os nomes diferem por espaco
sobrando / 'Aula07' vs 'Aula 07 -' / diacritico combinante ('Reconhecı́veis'), entao
o dedup por basename exato (filter_already_processed / incremental_build por
source_path) nao pega, e ambas coexistem -> "arquivos mal espalhados".

Esta tool agrupa as entries por CHAVE NORMALIZADA do basename (NFKD, sem combining,
sem nao-alfanumerico). Em cada grupo com >1 entry, se houver pelo menos uma cujo
arquivo EXISTE no stash (a re-processada) E pelo menos uma que NAO existe (stale),
mantem as do stash e marca as stale pra remocao. Grupos sem twin no stash, ou com
todas no stash, sao AMBIGUOS -> preservados e so logados (nunca deleta as cegas).

So mexe no manifest.json (remove entries). NAO apaga artefatos derivados das entries
removidas (content/curated/<id>.md etc.) -- esses viram orfaos; rodar a aba
"Manutenizacao" do app (sweep) depois pra limpar. Os ids removidos sao logados.

Uso:
    python -m scripts.dedup_manifest <repo_root> --stash <stash_root>            # dry-run
    python -m scripts.dedup_manifest <repo_root> --stash <stash_root> --write    # grava (.bak)
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

_EXT_RE = re.compile(
    r"\.(pdf|zip|thy|ipynb|md|pptx?|docx?|png|jpe?g|webp|txt|smv|dfy|lean|v|hs)$",
    re.IGNORECASE,
)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def norm_key(name: str) -> str:
    """Chave canonica de um basename: sem extensao, NFKD sem combining, so [a-z0-9].

    'Aula07 X.pdf', 'Aula 07 - X.pdf' e 'Aula 07 - X .pdf' colapsam na MESMA chave;
    'Reconhecı́veis' (i + combining acute) == 'Reconhecíveis' (precomposto).
    """
    s = _EXT_RE.sub("", str(name or "").strip().casefold())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return _NON_ALNUM_RE.sub("", s)


def plan_dedup(entries: list, stash_basenames: set) -> tuple[list, list]:
    """Planeja a remocao de duplicatas stale.

    entries: lista de dicts do manifest. stash_basenames: set de basenames
    (casefold) presentes no stash. Retorna (removals, ambiguous):
    - removals: lista de (index, entry) das entries stale a remover.
    - ambiguous: lista de (key, members) de grupos preservados (sem twin no stash
      ou todas no stash) -- so pra log, nada removido.
    """
    known = {str(b).strip().casefold() for b in (stash_basenames or set())}
    groups: dict = defaultdict(list)
    for i, e in enumerate(entries or []):
        base = os.path.basename(str(e.get("source_path") or ""))
        in_stash = base.casefold() in known
        groups[norm_key(base)].append((i, e, in_stash))

    removals: list = []
    ambiguous: list = []
    for key, members in groups.items():
        if not key or len(members) < 2:
            continue
        in_stash = [m for m in members if m[2]]
        stale = [m for m in members if not m[2]]
        if in_stash and stale:
            for (idx, e, _) in stale:
                removals.append((idx, e))
        else:
            ambiguous.append((key, members))
    return removals, ambiguous


def _stash_basenames(stash_root: Path) -> set:
    out: set = set()
    if not stash_root.is_dir():
        return out
    for root, _dirs, files in os.walk(stash_root):
        for f in files:
            if f == "_ARQUIVOS_DO_CARD.txt":
                continue
            out.add(f.casefold())
    return out


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    write = "--write" in argv
    stash = ""
    if "--stash" in argv:
        i = argv.index("--stash")
        stash = argv[i + 1] if i + 1 < len(argv) else ""
    pos = [a for a in argv if not a.startswith("-") and a != stash]
    if not pos or not stash:
        print("uso: python -m scripts.dedup_manifest <repo_root> --stash <stash_root> [--write]")
        return 2
    repo = Path(pos[0])
    mpath = repo / "manifest.json"
    if not mpath.is_file():
        print(f"manifest.json nao encontrado em {repo}")
        return 2
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    stash_bn = _stash_basenames(Path(stash))

    removals, ambiguous = plan_dedup(entries, stash_bn)

    print(f"repo={repo}  entries={len(entries)}  stash_arquivos={len(stash_bn)}")
    print(f"duplicatas stale a remover: {len(removals)}  | grupos ambiguos preservados: {len(ambiguous)}")
    for idx, e in removals:
        print(f"  REMOVE id={e.get('id')!r} sec={e.get('source_section')!r} "
              f"src={os.path.basename(str(e.get('source_path') or ''))!r}")
    for key, members in ambiguous:
        tags = ", ".join(f"{os.path.basename(str(e.get('source_path') or ''))}"
                         f"({'stash' if ins else 'stale'})" for _i, e, ins in members)
        print(f"  AMBIGUO key={key!r}: {tags}")

    if not write:
        print("Dry-run. Use --write para gravar (faz .bak antes).")
        return 0
    if not removals:
        print("Nada a remover.")
        return 0

    mpath.with_suffix(".json.bak").write_text(
        mpath.read_text(encoding="utf-8"), encoding="utf-8")
    remove_idx = {idx for idx, _e in removals}
    manifest["entries"] = [e for i, e in enumerate(entries) if i not in remove_idx]
    mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    removed_ids = [e.get("id") for _i, e in removals if e.get("id")]
    print(f"Gravado (.bak feito). Removidas {len(remove_idx)} entries.")
    print("Artefatos orfaos das removidas (limpar via aba Manutencao/sweep):")
    for rid in removed_ids:
        print(f"  content/curated/{rid}.md  (e sidecars correlatos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
