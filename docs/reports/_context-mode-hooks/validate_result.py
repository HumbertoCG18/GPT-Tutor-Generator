"""Validate the published hook-pilot result without rerunning hooks."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
data = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
report = (ROOT / "docs/reports/2026-09-18-piloto-hooks-context-mode.md").read_text(encoding="utf-8")

expected_failures = {"no_persisted_secret", "no_hook_stderr", "malformed_input_fail_open"}
assert data["passed"] == 7 and data["total"] == 10
assert {name for name, passed in data["checks"].items() if not passed} == expected_failures
assert data["activation_recommendation"]["overall"] == "reject full hook activation"
assert data["platforms"]["claude-code"]["storage"]["synthetic_secret_file_count"] == 1
assert data["platforms"]["codex"]["storage"]["synthetic_secret_file_count"] == 1
assert data["platforms"]["antigravity-cli"]["storage"]["synthetic_secret_file_count"] == 0
assert all(p["storage"]["duplicate_groups"] == 0 for p in data["platforms"].values())
assert {row["source_hook"] for row in data["platforms"]["claude-code"]["storage"]["synthetic_secret_events"]} == {"SessionStart", "Stop", "UserPromptSubmit"}
assert {row["source_hook"] for row in data["platforms"]["codex"]["storage"]["synthetic_secret_events"]} == {"PostToolUse", "Stop", "UserPromptSubmit"}
assert data["platforms"]["antigravity-cli"]["storage"]["synthetic_secret_events"] == []
assert "**7/10**" in report and "não ativar" in report

home = Path.home()
paths = {
    "claude_settings": home / ".claude/settings.json",
    "codex_config": home / ".codex/config.toml",
    "codex_hooks": home / ".codex/hooks.json",
    "gemini_settings": home / ".gemini/settings.json",
    "agy_hooks": home / ".gemini/config/hooks.json",
    "agy_mcp": home / ".gemini/config/mcp_config.json",
}
current = {
    name: hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    for name, path in paths.items()
}
assert current == data["config_hashes_after"] == data["config_hashes_before"]
print("PASS: expected findings, report, duplicates, recommendation and global config hashes")
