"""Migra ids de entry colididos para o esquema fix c v2 (sufixo por extensão).

Repos gerados com o código antigo podem ter ids de entry duplicados
(`introducao` ×2) ou sufixados por categoria (`exemplos-codigo-professor`). Este
tool re-deduplica os ids exatamente como um build fresco com fix c v2 faria
(reusa `_dedup_entry_id`/`_entry_dedup_tokens`), renomeia os assets em disco,
atualiza o `manifest.json` e re-chaveia o `code_curation.json`.

Determinístico e IDEMPOTENTE: rodar de novo quando já está canônico = no-op.
NÃO toca `source_path` (arquivo original do usuário) nem re-extrai zips
(`extracted_files` segue como está — repopular exige reimport; não é necessário
quando o resumo Gemini já existe).

Uso:
  python scripts/migrate_collided_ids.py <repo>           # dry-run (mostra o plano)
  python scripts/migrate_collided_ids.py <repo> --apply   # aplica (backup .bak)

Depois de aplicar: regenerar artefatos da matéria (regenerate/retag — barato,
sem re-extrair) para FILE_MAP/CODE_INDEX/etc. refletirem os ids novos.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.builder.ops.lifecycle_ops import _dedup_entry_id, _entry_dedup_tokens  # noqa: E402
from src.models.core import FileEntry  # noqa: E402

# Campos do entry que guardam paths de asset relativos ao repo (renomeáveis).
# source_path fica de fora de propósito (é o original do usuário, fora do repo).
PATH_KEYS = (
    "base_markdown", "approved_markdown", "curated_markdown",
    "advanced_markdown", "raw_target", "manual_review", "md_path",
)


def _base_id(entry: dict) -> str:
    """Id base (sem override), como FileEntry.id() computaria do source_path."""
    return FileEntry(
        source_path=str(entry.get("source_path") or ""),
        file_type=str(entry.get("file_type") or ""),
        category="",
        title=str(entry.get("title") or ""),
    ).id()


def _tokens(entry: dict) -> tuple[str, str]:
    class _O:
        pass
    o = _O()
    o.source_path = str(entry.get("source_path") or "")
    return _entry_dedup_tokens(o)


def canonical_ids(entries: list[dict]) -> list[str]:
    """Replay do dedup fix c v2 na ordem do manifest → id canônico por entry."""
    existing: set[str] = set()
    out: list[str] = []
    for e in entries:
        base = _base_id(e)
        canonical = base if base not in existing else _dedup_entry_id(
            base, existing, ext=_tokens(e)[0], folder=_tokens(e)[1]
        )
        existing.add(canonical)
        out.append(canonical)
    return out


def _stem(value: str) -> str:
    return PurePosixPath(str(value).replace("\\", "/")).stem


def _renamed_path(value: str, new_id: str) -> str:
    p = PurePosixPath(str(value).replace("\\", "/"))
    return str(p.with_name(new_id + p.suffix))


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python scripts/migrate_collided_ids.py <repo> [--apply]")
        return 2
    repo = Path(sys.argv[1])
    do_apply = "--apply" in sys.argv[2:]

    man_path = repo / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    cur_path = repo / "code_curation.json"
    curation = json.loads(cur_path.read_text(encoding="utf-8")) if cur_path.exists() else None

    plan = [
        (str(e.get("id")), new, e)
        for e, new in zip(entries, canonical_ids(entries))
        if new != str(e.get("id"))
    ]

    if not plan:
        print("Nada a migrar — todos os ids já são canônicos (fix c v2).")
        return 0

    tag = "[APPLY]" if do_apply else "[DRY-RUN]"
    print(f"{tag} {len(plan)} entries a migrar:\n")
    # (old_abs, new_abs, entry, field, new_relpath)
    renames: list[tuple[Path, Path, dict, str, str]] = []
    for old, new, e in plan:
        print(f"  {old}  ->  {new}  (ft={e.get('file_type')}, cat={e.get('category')})")
        for k in PATH_KEYS:
            v = e.get(k)
            if v and _stem(v) == old:
                newv = _renamed_path(v, new)
                print(f"     {k}: {v} -> {newv}")
                renames.append((repo / v, repo / newv, e, k, newv))
        if curation and old in curation.get("entries", {}):
            print(f"     code_curation[{old}] -> [{new}]")

    if not do_apply:
        print("\n(dry-run) Rode com --apply para executar (faz backup .bak).")
        return 0

    shutil.copy2(man_path, str(man_path) + ".bak")
    if cur_path.exists():
        shutil.copy2(cur_path, str(cur_path) + ".bak")

    # 1) renomeia cada arquivo físico uma vez; atualiza todos os campos que apontam pra ele
    moved: set[str] = set()
    for old_abs, new_abs, e, k, newv in renames:
        key = str(old_abs)
        if key not in moved:
            if old_abs.exists():
                new_abs.parent.mkdir(parents=True, exist_ok=True)
                old_abs.replace(new_abs)
            moved.add(key)
        e[k] = newv

    # 2) ids do manifest + rekey do code_curation
    for old, new, e in plan:
        e["id"] = new
        e["id_override"] = new
        if curation is not None:
            ce = curation.get("entries", {})
            if old in ce:
                ce[new] = ce.pop(old)

    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if curation is not None:
        cur_path.write_text(json.dumps(curation, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nAplicado. Backups: {man_path.name}.bak"
          + (f" + {cur_path.name}.bak" if cur_path.exists() else ""))
    print("Próximo: regenerar artefatos da matéria (regenerate/retag) p/ FILE_MAP/CODE_INDEX usarem os ids novos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
