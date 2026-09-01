from src.builder.core.reference_content import parse_github_repo


def test_parses_plain_repo_url():
    assert parse_github_repo("https://github.com/Netflix/eureka") == ("Netflix", "eureka")


def test_parses_with_git_suffix():
    assert parse_github_repo("https://github.com/OpenFeign/feign.git") == ("OpenFeign", "feign")


def test_parses_with_extra_path():
    assert parse_github_repo("https://github.com/spring-projects/spring-security-samples/tree/main/servlet") == ("spring-projects", "spring-security-samples")


def test_parses_without_scheme():
    assert parse_github_repo("github.com/aws/aws-encryption-sdk") == ("aws", "aws-encryption-sdk")


def test_non_github_returns_none():
    assert parse_github_repo("https://docs.python.org/3/library/asyncio.html") is None


def test_garbage_returns_none():
    assert parse_github_repo("") is None
    assert parse_github_repo("https://github.com/onlyowner") is None


from unittest.mock import patch, MagicMock
from src.builder.core.reference_content import fetch_github_readme


def _resp(status, text=""):
    r = MagicMock()
    r.status_code = status
    r.text = text
    return r


def test_fetch_readme_returns_body_on_200():
    with patch("src.builder.core.reference_content.requests.get", return_value=_resp(200, "# Eureka\nservice registry")) as g:
        out = fetch_github_readme("Netflix", "eureka")
    assert "service registry" in out
    assert "api.github.com/repos/Netflix/eureka/readme" in g.call_args[0][0]


def test_fetch_readme_empty_on_404():
    with patch("src.builder.core.reference_content.requests.get", return_value=_resp(404)):
        assert fetch_github_readme("x", "y") == ""


def test_fetch_readme_empty_on_exception():
    with patch("src.builder.core.reference_content.requests.get", side_effect=Exception("network")):
        assert fetch_github_readme("x", "y") == ""


from src.builder.core.reference_content import fetch_reference_text


def test_github_entry_uses_readme():
    entry = {"file_type": "github-repo", "source_path": "https://github.com/Netflix/eureka"}
    with patch("src.builder.core.reference_content.fetch_github_readme", return_value="readme body"):
        assert fetch_reference_text(entry) == "readme body"


def test_doc_url_uses_html_extractor():
    entry = {"file_type": "link", "source_path": "https://docs.example.com/guide"}
    html = "<html><body><nav>menu</nav><main><h1>Guia</h1><p>conteudo util</p></main><footer>rodape</footer></body></html>"
    with patch("src.builder.core.reference_content.requests.get", return_value=_resp(200, html)):
        out = fetch_reference_text(entry)
    assert "conteudo util" in out
    assert "menu" not in out and "rodape" not in out


def test_empty_source_returns_empty():
    assert fetch_reference_text({"file_type": "link", "source_path": ""}) == ""


def test_truncates_to_max_chars():
    entry = {"file_type": "github-repo", "source_path": "https://github.com/a/b"}
    with patch("src.builder.core.reference_content.fetch_github_readme", return_value="x" * 50000):
        out = fetch_reference_text(entry, max_chars=1000)
    assert len(out) <= 1000


# --- texto LOCAL antes da rede (2026-08-18) ---------------------------------
# Causa raiz medida: 1 de 15 refs mapeadas nos 5 repos. As referencias sao PDFs
# do Moodle ja convertidos em markdown no proprio repo, mas o fetch so buscava
# GitHub README / pagina HTML — texto vazio, zero conceito, zero mapeamento.

def test_le_markdown_local_do_repo_antes_de_ir_na_rede(tmp_path):
    from src.builder.core.reference_content import fetch_reference_text

    md = tmp_path / "content" / "curated"
    md.mkdir(parents=True)
    (md / "pthread.md").write_text(
        "<!-- EXEC_SUMMARY_START -->\n> boilerplate\n<!-- EXEC_SUMMARY_END -->\n"
        "# Biblioteca em C - pthread\n\nNo Linux as threads sao referenciadas como tasks.\n",
        encoding="utf-8")
    entry = {"category": "bibliografia", "source_path": r"C:\Users\x\Desktop\pthread.pdf",
             "approved_markdown": "content/curated/pthread.md"}

    out = fetch_reference_text(entry, repo_root=tmp_path)

    assert "threads" in out
    assert "boilerplate" not in out          # sumario executivo injetado nao entra
    assert "EXEC_SUMMARY" not in out


def test_sem_markdown_local_continua_indo_na_rede(monkeypatch, tmp_path):
    from src.builder.core import reference_content as rc

    monkeypatch.setattr(rc, "fetch_github_readme", lambda *a, **k: "readme body")
    entry = {"file_type": "github-repo", "source_path": "https://github.com/a/b"}
    assert rc.fetch_reference_text(entry, repo_root=tmp_path) == "readme body"


def test_markdown_local_ausente_no_disco_nao_quebra(tmp_path):
    from src.builder.core.reference_content import fetch_reference_text

    entry = {"category": "bibliografia", "source_path": "",
             "approved_markdown": "content/curated/nao-existe.md"}
    assert fetch_reference_text(entry, repo_root=tmp_path) == ""
