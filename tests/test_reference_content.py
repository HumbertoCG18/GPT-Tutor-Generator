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
