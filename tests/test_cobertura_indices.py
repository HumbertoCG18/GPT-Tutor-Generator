"""Watchdog (02/09): cobertura dos indices de navegacao — quantos materiais do manifest aparecem no FILE_MAP
(por raw na linha de rastreabilidade) e nos indices por tipo. O clamp de 12 KB escondia 2/3 dos materiais."""
import json

from scripts.censo_motor_llm import cobertura_indices

FILEMAP = """| 1 | A | material-de-aula | x |
|  | ↳ rastreabilidade |  | raw: `raw/pdfs/a.pdf`; tags: `x` |
| 2 | B | codigo-professor | x |
|  | ↳ rastreabilidade |  | raw: `raw/code/b.zip`; tags: `x` |

> Conteúdo truncado para manter course/FILE_MAP.md compacto e roteável.
"""


def test_cobertura_conta_presentes_ausentes_e_truncamento(tmp_path):
    (tmp_path / "course").mkdir(); (tmp_path / "code").mkdir()
    (tmp_path / "course" / "FILE_MAP.md").write_text(FILEMAP, encoding="utf-8")
    (tmp_path / "code" / "CODE_INDEX.md").write_text("| b | `raw/code/b.zip` |\n| c | c.zip |\n", encoding="utf-8")
    ents = [{"id": "a", "raw_target": "raw/pdfs/a.pdf", "category": "material-de-aula"},
            {"id": "b", "raw_target": "raw/code/b.zip", "category": "codigo-professor"},
            {"id": "c", "raw_target": "raw/code/c.zip", "category": "codigo-professor"},
            {"id": "d", "raw_target": "raw/pdfs/d.pdf", "category": "listas"}]
    r = cobertura_indices(tmp_path, ents)
    assert r["materiais"] == 4 and r["file_map"] == 2 and r["truncado"] is True
    assert r["ausentes"] == ["c", "d"] and r["code_index"] == 2 and r["sem_indice"] == ["d"]
