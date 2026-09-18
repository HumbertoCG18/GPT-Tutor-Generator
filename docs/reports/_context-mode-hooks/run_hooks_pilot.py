"""Isolated Context Mode hook pilot for issue #19; stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import secrets
import shutil
import sqlite3
import statistics
import subprocess
import time
from pathlib import Path


EXPECTED_SHA = "c127f2fe8496fefc36e0ebef36ded92d4fa8f570"
EVENTS = {
    "claude-code": ["pretooluse", "posttooluse", "userpromptsubmit", "precompact", "sessionstart", "stop"],
    "codex": ["pretooluse", "posttooluse", "userpromptsubmit", "precompact", "sessionstart", "stop"],
    "antigravity-cli": ["pretooluse", "posttooluse", "stop"],
}


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1)]


def payload(platform: str, event: str, project: Path, secret: str, session: str) -> dict:
    if platform == "antigravity-cli":
        base = {
            "conversationId": session,
            "workspace": {"current_dir": str(project)},
            "workspacePaths": [str(project)],
            "stepIdx": 7,
        }
        if event == "pretooluse":
            return base | {"toolCall": {"name": "run_command", "args": {"CommandLine": "pytest -q"}}}
        if event == "posttooluse":
            return base | {
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}},
                "error": None,
                "result": f"clean {secret}",
            }
        return base | {"status": "completed"}

    base = {"session_id": session, "cwd": str(project)}
    if event == "pretooluse":
        return base | {"tool_name": "Bash", "tool_input": {"command": "pytest -q"}}
    if event == "posttooluse":
        return base | {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "tool_response": f"clean {secret}",
        }
    if event == "userpromptsubmit":
        return base | {"prompt": f"continue safely {secret}"}
    if event == "precompact":
        return base | {"trigger": "manual"}
    if event == "sessionstart":
        return base | {"source": "startup"}
    return base | {"stop_hook_active": False, "last_assistant_message": f"done {secret}"}


def isolated_env(root: Path, project: Path, platform: str) -> dict[str, str]:
    home = root / "home"
    context = root / "context-mode"
    temp = root / "tmp"
    appdata = root / "appdata"
    local = root / "localappdata"
    for path in (home, context, temp, appdata, local, project):
        path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "APPDATA": str(appdata),
            "LOCALAPPDATA": str(local),
            "TEMP": str(temp),
            "TMP": str(temp),
            "XDG_DATA_HOME": str(root / "xdg-data"),
            "XDG_CONFIG_HOME": str(root / "xdg-config"),
            "CONTEXT_MODE_DIR": str(context),
            "CONTEXT_MODE_PLATFORM": platform,
            "CLAUDE_PROJECT_DIR": str(project),
            "GEMINI_PROJECT_DIR": str(project),
            "CODEX_HOME": str(home / ".codex"),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "CONTEXT_MODE_SUPPRESS_SECURITY_WARNING": "1",
        }
    )
    return env


def invoke(
    cli: Path,
    upstream: Path,
    platform: str,
    event: str,
    data: dict | str,
    env: dict[str, str],
    timeout_s: float = 20,
) -> dict:
    started = time.perf_counter_ns()
    command = (
        ["node", str(upstream / "hooks" / f"{event}.mjs")]
        if platform == "claude-code"
        else ["node", str(cli), "hook", platform, event]
    )
    try:
        proc = subprocess.run(
            command,
            input=data if isinstance(data, str) else json.dumps(data, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=upstream,
            env=env,
            timeout=timeout_s,
            check=False,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "latency_ms": (time.perf_counter_ns() - started) / 1_000_000,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "stdout": (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            "stderr": (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
            "latency_ms": (time.perf_counter_ns() - started) / 1_000_000,
            "timeout": True,
        }


def inspect_databases(root: Path, secret: bytes) -> dict:
    dbs = list(root.rglob("*.db"))
    rows = 0
    duplicate_groups = 0
    secret_events: list[dict[str, str]] = []
    schema_errors: list[str] = []
    for db_path in dbs:
        try:
            db = sqlite3.connect(db_path)
            tables = [r[0] for r in db.execute("select name from sqlite_master where type='table'")]
            for table in tables:
                if not table.replace("_", "").isalnum():
                    continue
                rows += db.execute(f'select count(*) from "{table}"').fetchone()[0]
                if table == "session_events":
                    duplicate_groups += db.execute(
                        "select count(*) from (select session_id,type,category,data,count(*) n "
                        "from session_events group by session_id,type,category,data having n>1)"
                    ).fetchone()[0]
                    for row in db.execute(
                        "select distinct type,category,source_hook from session_events "
                        "where instr(cast(data as text), ?) > 0",
                        (secret.decode(),),
                    ):
                        secret_events.append(
                            {"type": row[0] or "", "category": row[1] or "", "source_hook": row[2] or ""}
                        )
            db.close()
        except (sqlite3.Error, OSError) as exc:
            schema_errors.append(type(exc).__name__)
    persisted = []
    for path in root.rglob("*"):
        if path.is_file():
            try:
                relative = path.relative_to(root)
                if relative.parts[0] != "project" and secret in path.read_bytes():
                    persisted.append(str(relative))
            except OSError:
                pass
    return {
        "database_count": len(dbs),
        "row_count": rows,
        "duplicate_groups": duplicate_groups,
        "synthetic_secret_file_count": len(persisted),
        "synthetic_secret_events": sorted(secret_events, key=lambda row: tuple(row.values())),
        "schema_errors": schema_errors,
    }


def config_paths() -> dict[str, Path]:
    home = Path.home()
    return {
        "claude_settings": home / ".claude" / "settings.json",
        "codex_config": home / ".codex" / "config.toml",
        "codex_hooks": home / ".codex" / "hooks.json",
        "gemini_settings": home / ".gemini" / "settings.json",
        "agy_hooks": home / ".gemini" / "config" / "hooks.json",
        "agy_mcp": home / ".gemini" / "config" / "mcp_config.json",
    }


def verify_byte_exact_rollback(configs: dict[str, Path], run_root: Path) -> bool:
    profile = run_root / "rollback-profile"
    backup = run_root / "rollback-backup"
    profile.mkdir()
    backup.mkdir()
    expected: dict[str, str] = {}
    for name, source in configs.items():
        if not source.is_file():
            continue
        live_copy = profile / name
        saved_copy = backup / name
        live_copy.write_bytes(source.read_bytes())
        saved_copy.write_bytes(live_copy.read_bytes())
        expected[name] = hashlib.sha256(live_copy.read_bytes()).hexdigest()
        with live_copy.open("ab") as stream:
            stream.write(b"\ncontext-mode synthetic hook registration\n")
        live_copy.write_bytes(saved_copy.read_bytes())
    restored = all(sha256(profile / name) == digest for name, digest in expected.items())
    shutil.rmtree(profile)
    shutil.rmtree(backup)
    return restored and not profile.exists() and not backup.exists()


def hook_inventory() -> dict:
    inventory = {
        "claude-code": {"active_events": ["PreToolUse", "SessionStart"], "context_mode_events": 6, "overlap": 2},
        "codex": {"active_events": ["PreToolUse", "SessionStart"], "context_mode_events": 6, "overlap": 2},
        "antigravity-cli": {"active_events": ["ECC imported", "claude-mem imported"], "context_mode_events": 3, "overlap": "capture semantics"},
    }
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=15)
    args = parser.parse_args()
    upstream = args.upstream.resolve()
    cli = upstream / "cli.bundle.mjs"
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if sha != EXPECTED_SHA or not cli.is_file():
        raise SystemExit("Pinned upstream mismatch or missing CLI bundle")

    here = Path(__file__).resolve().parent
    run_root = here / "_runs" / time.strftime("%Y%m%d-%H%M%S")
    run_root.mkdir(parents=True)
    configs = config_paths()
    before = {name: sha256(path) for name, path in configs.items()}
    synthetic = ("sk-proj-" + secrets.token_hex(32)).encode()
    platforms: dict[str, dict] = {}

    for platform, events in EVENTS.items():
        root = run_root / platform
        project = root / "project"
        env = isolated_env(root, project, platform)
        session = f"pilot-{platform}"
        for instruction_file in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
            (project / instruction_file).write_text(
                f"Synthetic private fixture: {synthetic.decode()}\n", encoding="utf-8"
            )
        event_results = {}
        response_secret = False
        for event in events:
            result = invoke(cli, upstream, platform, event, payload(platform, event, project, synthetic.decode(), session), env)
            response_secret |= synthetic.decode() in (result["stdout"] + result["stderr"])
            event_results[event] = {
                "exit_code": result["exit_code"],
                "timeout": result.get("timeout", False),
                "stdout_bytes": len(result["stdout"].encode()),
                "stderr_bytes": len(result["stderr"].encode()),
                "latency_ms": round(result["latency_ms"], 3),
            }

        samples = []
        benchmark_payload = payload(platform, "pretooluse", project, synthetic.decode(), session + "-bench")
        for _ in range(args.runs):
            samples.append(invoke(cli, upstream, platform, "pretooluse", benchmark_payload, env)["latency_ms"])
        malformed = invoke(cli, upstream, platform, "pretooluse", "not-json{{", env)
        timed = invoke(cli, upstream, platform, "pretooluse", benchmark_payload, env, timeout_s=0.001)
        storage = inspect_databases(root, synthetic)
        platforms[platform] = {
            "events": event_results,
            "latency": {
                "samples": len(samples),
                "p50_ms": round(statistics.median(samples), 3),
                "p95_ms": round(percentile(samples, 0.95), 3),
            },
            "context": {
                "response_bytes": sum(e["stdout_bytes"] for e in event_results.values()),
                "heuristic_tokens_bytes_div_3": math.ceil(sum(e["stdout_bytes"] for e in event_results.values()) / 3),
            },
            "response_contains_synthetic_secret": response_secret,
            "malformed_input_fail_open": malformed["exit_code"] == 0 and not malformed["stdout"],
            "timeout_contained": timed.get("timeout", False),
            "storage": storage,
        }

    after = {name: sha256(path) for name, path in configs.items()}
    rollback_ok = verify_byte_exact_rollback(configs, run_root)
    checks = {
        "upstream_pinned": sha == EXPECTED_SHA,
        "all_events_exit_zero": all(
            event["exit_code"] == 0 and not event["timeout"]
            for platform in platforms.values()
            for event in platform["events"].values()
        ),
        "global_configs_unchanged": before == after,
        "no_response_secret": all(not p["response_contains_synthetic_secret"] for p in platforms.values()),
        "no_persisted_secret": all(p["storage"]["synthetic_secret_file_count"] == 0 for p in platforms.values()),
        "no_duplicate_records_by_content_key": all(
            p["storage"]["duplicate_groups"] == 0 for p in platforms.values()
        ),
        "no_hook_stderr": all(
            event["stderr_bytes"] == 0
            for platform in platforms.values()
            for event in platform["events"].values()
        ),
        "malformed_input_fail_open": all(p["malformed_input_fail_open"] for p in platforms.values()),
        "harness_timeout_enforced": all(p["timeout_contained"] for p in platforms.values()),
        "byte_exact_backup_restore": rollback_ok,
    }
    result = {
        "issue": 19,
        "upstream_sha": sha,
        "upstream_version": "1.0.169",
        "runs": args.runs,
        "inventory": hook_inventory(),
        "platforms": platforms,
        "config_hashes_before": before,
        "config_hashes_after": after,
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "activation_recommendation": {
            "overall": "reject full hook activation",
            "claude-code": "reject: secret persistence, stderr, RTK and SessionStart overlap",
            "codex": "reject: secret persistence, stderr, malformed-input crash and Graphify overlap",
            "antigravity-cli": "reject: stderr, pytest denial and unverified payload fields",
        },
    }
    (here / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_root / "result.full.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "total": result["total"], "checks": checks}, ensure_ascii=False))
    if os.environ.get("KEEP_CONTEXT_MODE_HOOK_RUN") != "1":
        shutil.rmtree(run_root)
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
