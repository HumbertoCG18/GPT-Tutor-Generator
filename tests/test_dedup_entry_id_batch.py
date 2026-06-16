from src.models.core import FileEntry
from src.builder.ops.lifecycle_ops import assign_dedup_id


def _entry(source_path: str, category: str) -> FileEntry:
    return FileEntry.from_dict({
        "title": source_path,
        "source_path": source_path,
        "file_type": "pdf",
        "category": category,
    })


def test_assign_dedup_id_first_use_keeps_base_id():
    existing = set()
    e = _entry("trabalhos/introducao.pdf", "trabalhos")
    assert assign_dedup_id(e, existing) == "introducao"
    assert e.id_override == ""
    assert "introducao" in existing


def test_assign_dedup_id_collision_suffixes_category():
    existing = set()
    e1 = _entry("trabalhos/introducao.pdf", "trabalhos")
    e2 = _entry("codigo/introducao.zip", "codigo-professor")
    assert assign_dedup_id(e1, existing) == "introducao"
    assert assign_dedup_id(e2, existing) == "introducao-codigo-professor"
    assert e2.id_override == "introducao-codigo-professor"
    assert e2.id() == "introducao-codigo-professor"
