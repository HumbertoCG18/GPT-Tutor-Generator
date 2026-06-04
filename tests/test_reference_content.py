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
