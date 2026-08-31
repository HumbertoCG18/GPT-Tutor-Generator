"""Tests for the GitHub clone branch-detection + Windows long-path fix.

Bug: `process_github_repo` hardcoded the `main` branch fallback (repos whose
default is `master`/other fail) and never enabled `core.longpaths`, so big
repos broke on Windows checkout (`Filename too long`).

These tests mock `subprocess.run` so no network/git is touched: the clone mock
creates an empty clone dir, so the rglob over extracted files yields nothing and
`process_code` is never invoked. We assert on the *commands* git is asked to run.
"""

import types
from pathlib import Path
from unittest.mock import patch

import pytest

from src.builder.core import source_importers as si
from src.models.core import FileEntry


class _Builder:
    def __init__(self, root):
        self.root_dir = Path(root)
        self.logs = []

    # process_github_repo busca o texto da pagina via a rota de URL do builder
    def _process_url(self, entry):
        return {
            "base_markdown": f"staging/markdown-auto/url_fetcher/{entry.id()}.md",
            "base_backend": "url_fetcher",
            "manual_review": None,
        }


def _proc(returncode=0, stdout="", stderr=""):
    p = types.SimpleNamespace()
    p.returncode = returncode
    p.stdout = stdout
    p.stderr = stderr
    return p


def _is(cmd, token):
    return token in cmd


# --- _detect_default_branch -------------------------------------------------


def test_detect_default_branch_parses_symref():
    out = "ref: refs/heads/develop\tHEAD\nabc123\tHEAD\n"
    with patch.object(si.subprocess, "run", return_value=_proc(0, out)):
        assert si._detect_default_branch("https://github.com/o/r") == "develop"


def test_detect_default_branch_fallback_on_nonzero():
    with patch.object(si.subprocess, "run", return_value=_proc(128, "", "boom")):
        assert si._detect_default_branch("https://github.com/o/r") == "main"


def test_detect_default_branch_fallback_on_missing_git():
    with patch.object(si.subprocess, "run", side_effect=FileNotFoundError()):
        assert si._detect_default_branch("https://github.com/o/r") == "main"


# --- process_github_repo: branch detection + longpaths ----------------------


def _github_entry(tags=""):
    return FileEntry(
        source_path="https://github.com/o/r",
        file_type="github-repo",
        category="codigo-professor",
        title="r",
        tags=tags,
    )


def test_clone_detects_default_branch_when_tags_empty(tmp_path):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if _is(cmd, "ls-remote"):
            return _proc(0, "ref: refs/heads/trunk\tHEAD\n")
        Path(cmd[-1]).mkdir(parents=True, exist_ok=True)  # fake clone target
        return _proc(0)

    with patch.object(si.subprocess, "run", side_effect=fake_run):
        si.process_github_repo(_Builder(tmp_path), _github_entry(tags=""))

    clone_cmd = next(c for c in calls if _is(c, "clone"))
    assert _is(clone_cmd, "trunk"), "detected default branch must be used"


def test_clone_command_enables_longpaths(tmp_path):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if _is(cmd, "ls-remote"):
            return _proc(0, "ref: refs/heads/main\tHEAD\n")
        Path(cmd[-1]).mkdir(parents=True, exist_ok=True)
        return _proc(0)

    with patch.object(si.subprocess, "run", side_effect=fake_run):
        si.process_github_repo(_Builder(tmp_path), _github_entry(tags=""))

    clone_cmd = next(c for c in calls if _is(c, "clone"))
    assert _is(clone_cmd, "-c") and _is(clone_cmd, "core.longpaths=true")


def test_page_text_becomes_base_markdown_even_when_clone_fails(tmp_path):
    """github-repo sem rota de texto deixava o scorer com 0 chars (eth2/aws no
    MF): o texto da pagina (via _process_url) vira base_markdown SEMPRE, clone
    falho incluso."""

    def fake_run(cmd, **kw):
        if _is(cmd, "ls-remote"):
            return _proc(0, "ref: refs/heads/main\tHEAD\n")
        return _proc(128, "", "fatal: Remote branch main not found")

    with patch.object(si.subprocess, "run", side_effect=fake_run):
        item = si.process_github_repo(_Builder(tmp_path), _github_entry(tags="main"))

    assert item["clone_error"]
    eid = _github_entry(tags="main").id()
    assert item["base_markdown"] == f"staging/markdown-auto/url_fetcher/{eid}.md"
    assert item["base_backend"] == "url_fetcher"


def test_clone_uses_explicit_branch_override_without_detection(tmp_path):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if _is(cmd, "ls-remote"):
            raise AssertionError("ls-remote must not run when tags pin a branch")
        Path(cmd[-1]).mkdir(parents=True, exist_ok=True)
        return _proc(0)

    with patch.object(si.subprocess, "run", side_effect=fake_run):
        si.process_github_repo(_Builder(tmp_path), _github_entry(tags="master"))

    clone_cmd = next(c for c in calls if _is(c, "clone"))
    assert _is(clone_cmd, "master")
