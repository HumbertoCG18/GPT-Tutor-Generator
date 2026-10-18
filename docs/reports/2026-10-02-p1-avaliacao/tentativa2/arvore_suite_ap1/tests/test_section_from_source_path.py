"""idea 3: import direto deriva source_section da pasta-pai (casa o card_block_map)."""
from src.builder.ops.entry_processing import _section_from_source_path


class _E:
    def __init__(self, **k):
        self.__dict__.update(k)


def test_deriva_pasta_pai_como_secao():
    e = _E(file_type="zip", source_path="C:/x/Verificação de Programas/hoare.zip")
    assert _section_from_source_path(e) == "Verificação de Programas"


def test_lida_com_backslash():
    e = _E(file_type="code", source_path=r"C:\x\Provas por Inducao\arvores.thy")
    assert _section_from_source_path(e) == "Provas por Inducao"


def test_url_e_repo_vazios():
    assert _section_from_source_path(_E(file_type="url", source_path="https://x.com/p")) == ""
    assert _section_from_source_path(_E(file_type="github-repo", source_path="https://github.com/a/b")) == ""


def test_sem_source_vazio():
    assert _section_from_source_path(_E(file_type="pdf", source_path="")) == ""
