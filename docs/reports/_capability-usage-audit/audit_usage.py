"""Inventory configured capabilities and count structured tool calls without printing secrets."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


HOME = Path.home()
TOOL_IN_JS = re.compile(r"tools\.([A-Za-z0-9_]+)\s*\(")
SKILL_PATH = re.compile(r"[/\\]([^/\\]+)[/\\]SKILL\.md", re.IGNORECASE)
EXPLICIT_SKILL = re.compile(r"(?<![\w$])\$([A-Za-z0-9][A-Za-z0-9:._-]*)")
GH_COMMAND = re.compile(r"(?i)(?<![\w.-])gh(?:\.exe)?\s+[a-z]")
READ_VERB = re.compile(r"(?i)\b(?:Get-Content|cat|type|head|tail)\b|\bsed\s+-n\b")
DIRECT_READ_TOOLS = {"Read", "read_file", "view_file"}
SHELL_TOOLS = {"Bash", "bash", "PowerShell", "exec", "exec_command", "run_command", "shell_command"}
KNOWN_SKILLS = {
    path.parent.name
    for root in (HOME / ".agents/skills", HOME / ".codex/skills", HOME / ".gemini")
    if root.exists()
    for path in root.rglob("SKILL.md")
}


@dataclass
class Stats:
    files: int = 0
    bytes: int = 0
    parsed_lines: int = 0
    invalid_lines: int = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    tool_calls: collections.Counter[str] = field(default_factory=collections.Counter)
    mcp_calls: collections.Counter[str] = field(default_factory=collections.Counter)
    nested_tool_references: collections.Counter[str] = field(default_factory=collections.Counter)
    skill_reads: collections.Counter[str] = field(default_factory=collections.Counter)
    skill_invocations: collections.Counter[str] = field(default_factory=collections.Counter)
    explicit_skills: collections.Counter[str] = field(default_factory=collections.Counter)
    gh_command_matches: int = 0

    def observe_timestamp(self, value: str | None) -> None:
        if not value:
            return
        value = value[:30]
        if self.first_timestamp is None or value < self.first_timestamp:
            self.first_timestamp = value
        if self.last_timestamp is None or value > self.last_timestamp:
            self.last_timestamp = value

    def observe_call(self, name: str | None, payload: Any) -> None:
        if not name:
            return
        name = name.split("<", 1)[0]
        self.tool_calls[name] += 1
        if name.startswith("mcp__"):
            self.mcp_calls[name] += 1
        text = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
        for skill in set(skill_read_names(name, payload)):
            self.skill_reads[skill] += 1
        if name == "Skill" and isinstance(payload, dict):
            skill = payload.get("skill") or payload.get("name")
            if skill:
                self.skill_invocations[str(skill)] += 1
        if name in SHELL_TOOLS:
            self.gh_command_matches += sum(len(GH_COMMAND.findall(command)) for command in command_texts(payload))
        if name == "exec":
            for nested in TOOL_IN_JS.findall(text):
                self.nested_tool_references[nested] += 1
        if name == "call_mcp_tool" and isinstance(payload, dict):
            server = payload.get("ServerName") or payload.get("server_name")
            tool = payload.get("ToolName") or payload.get("tool_name")
            if server and tool:
                server = str(server).strip("\"'")
                tool = str(tool).strip("\"'")
                self.mcp_calls[f"mcp:{server}:{tool}"] += 1

    def observe_user_text(self, text: str) -> None:
        for skill in EXPLICIT_SKILL.findall(text):
            if skill in KNOWN_SKILLS:
                self.explicit_skills[skill] += 1

    def serialise(self) -> dict[str, Any]:
        return {
            "files": self.files,
            "bytes": self.bytes,
            "parsed_lines": self.parsed_lines,
            "invalid_lines": self.invalid_lines,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "tool_calls_total": sum(self.tool_calls.values()),
            "tool_calls": dict(self.tool_calls.most_common()),
            "mcp_calls": dict(sorted(self.mcp_calls.items())),
            "nested_tool_references_not_calls": dict(self.nested_tool_references.most_common()),
            "skill_file_reads": dict(self.skill_reads.most_common()),
            "skill_tool_invocations": dict(self.skill_invocations.most_common()),
            "explicit_skill_mentions": dict(self.explicit_skills.most_common()),
            "gh_command_matches": self.gh_command_matches,
        }


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def command_texts(payload: Any) -> Iterable[str]:
    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            yield payload
        else:
            if decoded == payload:
                yield payload
            else:
                yield from command_texts(decoded)
    elif isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in {"cmd", "command", "script"} and isinstance(value, str):
                yield value
    elif isinstance(payload, list):
        for item in payload:
            yield from command_texts(item)


def skill_read_names(tool: str, payload: Any) -> Iterable[str]:
    if tool in DIRECT_READ_TOOLS:
        candidates = strings(payload)
    elif tool in SHELL_TOOLS:
        candidates = (
            segment
            for command in command_texts(payload)
            for segment in re.split(r"[;&|\n]", command)
            if READ_VERB.search(segment)
        )
    else:
        return
    for candidate in candidates:
        for skill in SKILL_PATH.findall(candidate):
            if skill in KNOWN_SKILLS:
                yield skill
def parse_claude(obj: dict[str, Any], stats: Stats) -> None:
    stats.observe_timestamp(obj.get("timestamp"))
    message = obj.get("message") or {}
    if obj.get("type") == "user":
        for text in strings(message.get("content", [])):
            stats.observe_user_text(text)
    for block in message.get("content", []) if isinstance(message, dict) else []:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            stats.observe_call(block.get("name"), block.get("input", {}))


def parse_codex(obj: dict[str, Any], stats: Stats) -> None:
    stats.observe_timestamp(obj.get("timestamp"))
    if obj.get("type") != "response_item":
        return
    payload = obj.get("payload") or {}
    kind = payload.get("type")
    if kind in {"function_call", "custom_tool_call", "mcp_tool_call"}:
        stats.observe_call(payload.get("name"), payload.get("arguments", payload.get("input", {})))
    if kind == "message" and payload.get("role") == "user":
        for text in strings(payload.get("content", [])):
            stats.observe_user_text(text)


def parse_agy(obj: dict[str, Any], stats: Stats) -> None:
    stats.observe_timestamp(obj.get("created_at"))
    if obj.get("type") == "USER_INPUT":
        stats.observe_user_text(str(obj.get("content", "")))
    for call in obj.get("tool_calls", []) or []:
        if isinstance(call, dict):
            stats.observe_call(call.get("name"), call.get("args", {}))


def scan(root: Path, parser, include=None) -> Stats:
    stats = Stats()
    for path in root.rglob("*.jsonl") if root.exists() else []:
        if include and not include(path):
            continue
        stats.files += 1
        stats.bytes += path.stat().st_size
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    stats.invalid_lines += 1
                    continue
                stats.parsed_lines += 1
                if isinstance(obj, dict):
                    parser(obj, stats)
    return stats


def safe_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def safe_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def config_hash(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def inventory() -> dict[str, Any]:
    claude_settings_path = HOME / ".claude/settings.json"
    claude_config_path = HOME / ".claude.json"
    codex_config_path = HOME / ".codex/config.toml"
    agy_mcp_path = HOME / ".gemini/config/mcp_config.json"
    agy_settings_path = HOME / ".gemini/settings.json"
    claude_settings = safe_json(claude_settings_path)
    claude_config = safe_json(claude_config_path)
    codex = safe_toml(codex_config_path)
    agy_mcp = safe_json(agy_mcp_path)
    overrides = claude_settings.get("skillOverrides", {})
    codex_skills = (codex.get("skills") or {}).get("config", [])
    def mcp_states(servers: dict[str, Any]) -> dict[str, bool]:
        return {
            name: not bool(value.get("disabled", False)) and bool(value.get("enabled", True))
            for name, value in sorted(servers.items())
            if isinstance(value, dict)
        }

    claude_mcps = claude_config.get("mcpServers") or {}
    codex_mcps = codex.get("mcp_servers") or {}
    agy_mcps = agy_mcp.get("mcpServers") or agy_mcp.get("mcp_servers") or {}
    return {
        "config_sha256": {
            "claude_settings": config_hash(claude_settings_path),
            "claude_config": config_hash(claude_config_path),
            "codex_config": config_hash(codex_config_path),
            "agy_mcp": config_hash(agy_mcp_path),
            "agy_settings": config_hash(agy_settings_path),
        },
        "claude": {
            "mcp_servers": mcp_states(claude_mcps),
            "enabled_plugins": sorted(name for name, enabled in (claude_settings.get("enabledPlugins") or {}).items() if enabled),
            "skill_override_modes": dict(collections.Counter(str(value) for value in overrides.values())),
        },
        "codex": {
            "mcp_servers": mcp_states(codex_mcps),
            "plugins": {name: bool(value.get("enabled", True)) for name, value in sorted((codex.get("plugins") or {}).items()) if isinstance(value, dict)},
            "skill_entries": len(codex_skills),
            "skill_enabled": sum(entry.get("enabled") is True for entry in codex_skills),
            "skill_disabled": sum(entry.get("enabled") is False for entry in codex_skills),
        },
        "agy": {
            "mcp_servers": mcp_states(agy_mcps),
            "builtin_skill_files": len(list((HOME / ".gemini/antigravity-cli/builtin/skills").rglob("SKILL.md"))),
        },
    }


def self_test() -> None:
    claude = Stats()
    parse_claude({"type": "system", "message": {"content": [{"type": "text", "text": '"type":"tool_use"'}]}}, claude)
    parse_claude({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "mcp__github__get", "input": {}}]}}, claude)
    assert claude.tool_calls == {"mcp__github__get": 1}

    reads = Stats()
    reads.observe_call("Read", {"file_path": "/skills/graphify/SKILL.md"})
    reads.observe_call("Read", {"file_path": "/skills/graphify/SKILL.md", "note": "/skills/graphify/SKILL.md"})
    reads.observe_call("Write", {"content": "See /skills/graphify/SKILL.md"})
    reads.observe_call("Bash", {"command": "echo /skills/graphify/SKILL.md"})
    reads.observe_call("Bash", {"command": "echo /skills/graphify/SKILL.md; cat notes.md"})
    assert reads.skill_reads == {"graphify": 2}

    commands = Stats()
    commands.observe_call("Bash", {"command": "gh issue list"})
    commands.observe_call("Bash", {"command": "pwd; gh pr list"})
    commands.observe_call("exec_command", json.dumps({"cmd": "gh repo view"}))
    assert commands.gh_command_matches == 3

    codex = Stats()
    parse_codex({"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "input": "await tools.mcp__x__y({});"}}, codex)
    assert codex.tool_calls == {"exec": 1}
    assert codex.nested_tool_references == {"mcp__x__y": 1}

    agy = Stats()
    parse_agy({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "query-docs", "args": {}}]}, agy)
    assert agy.tool_calls == {"query-docs": 1}
    print("PASS: structured calls counted; textual definitions ignored")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    result = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "method": "structured tool calls only; Codex nested orchestrator names retained separately as non-call references",
        "inventory": inventory(),
        "usage": {
            "claude": scan(HOME / ".claude/projects", parse_claude).serialise(),
            "codex_sessions": scan(HOME / ".codex/sessions", parse_codex).serialise(),
            "codex_archived": scan(HOME / ".codex/archived_sessions", parse_codex).serialise(),
            "agy": scan(
                HOME / ".gemini/antigravity-cli/brain",
                parse_agy,
                include=lambda path: path.name == "transcript_full.jsonl",
            ).serialise(),
        },
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)


if __name__ == "__main__":
    sys.exit(main())
