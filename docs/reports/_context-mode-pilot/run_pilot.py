"""Black-box MCP pilot for Context Mode. Uses stdlib only; writes no CLI config."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import secrets
import subprocess
import sys
import threading
import time


def reader(stream, out: queue.Queue[str] | list[str]) -> None:
    for line in iter(stream.readline, ""):
        if isinstance(out, queue.Queue):
            out.put(line)
        else:
            out.append(line)


class McpClient:
    def __init__(self, server: Path, sandbox: Path) -> None:
        project = sandbox / "project"
        for path in (project, sandbox / "data", sandbox / "home", sandbox / "tmp"):
            path.mkdir(parents=True, exist_ok=True)
        allowed = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE")
        env = {key: os.environ[key] for key in allowed if key in os.environ}
        env.update(
            {
                "CONTEXT_MODE_DATA_DIR": str(sandbox / "data"),
                "CONTEXT_MODE_PROJECT_DIR": str(project),
                "CLAUDE_PROJECT_DIR": str(project),
                "CLAUDE_CONFIG_DIR": str(sandbox / "home" / ".claude"),
                "CODEX_HOME": str(sandbox / "home" / ".codex"),
                "CONTEXT_MODE_PLATFORM": "codex",
                "HOME": str(sandbox / "home"),
                "USERPROFILE": str(sandbox / "home"),
                "APPDATA": str(sandbox / "home" / "AppData" / "Roaming"),
                "LOCALAPPDATA": str(sandbox / "home" / "AppData" / "Local"),
                "TEMP": str(sandbox / "tmp"),
                "TMP": str(sandbox / "tmp"),
                "CONTEXT_MODE_SEARCH_BLOCK_AFTER": "100",
                "CONTEXT_MODE_SEARCH_MAX_RESULTS_AFTER": "100"
            }
        )
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.proc = subprocess.Popen(
            ["node", str(server)],
            cwd=project,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=flags,
        )
        assert self.proc.stdin and self.proc.stdout and self.proc.stderr
        self.stdout: queue.Queue[str] = queue.Queue()
        self.stderr: list[str] = []
        self.threads = [
            threading.Thread(target=reader, args=(self.proc.stdout, self.stdout), daemon=True),
            threading.Thread(target=reader, args=(self.proc.stderr, self.stderr), daemon=True),
        ]
        for thread in self.threads:
            thread.start()
        self.request_id = 0
        self.raw_responses: list[dict] = []

    def request(self, method: str, params: dict, timeout: float = 30) -> dict:
        self.request_id += 1
        request_id = self.request_id
        wire = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        assert self.proc.stdin
        self.proc.stdin.write(json.dumps(wire, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None and self.stdout.empty():
                raise RuntimeError(f"MCP exited before response: {self.proc.returncode}")
            try:
                line = self.stdout.get(timeout=min(0.25, max(0.01, deadline - time.monotonic())))
            except queue.Empty:
                continue
            message = json.loads(line)
            self.raw_responses.append(message)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(json.dumps(message["error"], ensure_ascii=False))
                return message["result"]
        raise TimeoutError(f"MCP timeout: {method}")

    def notify(self, method: str, params: dict | None = None) -> None:
        assert self.proc.stdin
        wire = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            wire["params"] = params
        self.proc.stdin.write(json.dumps(wire, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def call(self, name: str, arguments: dict, timeout: float = 60) -> dict:
        return self.request("tools/call", {"name": name, "arguments": arguments}, timeout)

    def close(self) -> int:
        assert self.proc.stdin
        self.proc.stdin.close()
        try:
            code = self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
            code = self.proc.returncode
        for thread in self.threads:
            thread.join(timeout=2)
        return code


def text_of(result: dict) -> str:
    return "\n".join(item.get("text", "") for item in result.get("content", []) if item.get("type") == "text")


def contains_bytes(root: Path, needle: bytes, excluded: Path) -> tuple[list[str], list[str]]:
    hits = []
    errors = []
    for path in root.rglob("*"):
        if not path.is_file() or path == excluded:
            continue
        try:
            if needle in path.read_bytes():
                hits.append(str(path.relative_to(root)))
        except OSError as exc:
            errors.append(f"{path.relative_to(root)}: {exc.__class__.__name__}")
    return hits, errors


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected_config_hashes() -> dict[str, str | None]:
    home = Path.home()
    paths = [
        home / ".claude.json",
        home / ".claude" / "settings.json",
        home / ".codex" / "config.toml",
        home / ".gemini" / "config" / "mcp_config.json",
    ]
    return {str(path): sha256_file(path) for path in paths}


def sanitize(value, replacements: dict[str, str]):
    if isinstance(value, str):
        for raw, label in replacements.items():
            value = value.replace(raw, label)
        return value
    if isinstance(value, list):
        return [sanitize(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, replacements) for key, item in value.items()}
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--result-output", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name("contract.json"))
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    server = args.upstream.resolve() / contract["upstream"]["entrypoint"]
    run_dir = args.run_dir.resolve()
    result_output = args.result_output.resolve()
    sandbox = run_dir / "sandbox"
    if run_dir.exists():
        raise FileExistsError(f"run directory must be new: {run_dir}")
    if result_output.exists():
        raise FileExistsError(f"result output already exists: {result_output}")
    run_dir.mkdir(parents=True)

    protected_before = protected_config_hashes()
    bundle_hash_before = sha256_file(server)

    client = McpClient(server, sandbox)
    checks: dict[str, dict] = {}
    responses: dict[str, dict] = {}
    secret = f"SYNTHETIC_CONTEXT_MODE_{secrets.token_hex(16)}"
    secret_file = sandbox / "project" / "secret-fixture.txt"
    secret_bytes = (secret + "\n").encode("utf-8")
    secret_file.write_bytes(secret_bytes)

    try:
        init = client.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "gpt-tutor-context-mode-pilot", "version": "1"},
            },
        )
        client.notify("notifications/initialized")
        tools = client.request("tools/list", {})
        tool_names = [tool["name"] for tool in tools["tools"]]
        checks["mcp_surface"] = {
            "pass": all(name in tool_names for name in ("ctx_execute", "ctx_execute_file", "ctx_search")),
            "tool_names": tool_names,
            "server": init.get("serverInfo"),
        }

        error_result = client.call(
            "ctx_execute",
            {"language": "python", "code": "import sys\nprint('ERR_STDOUT')\nprint('ERR_STDERR', file=sys.stderr)\nraise SystemExit(7)"},
        )
        error_text = text_of(error_result)
        responses["error"] = error_result
        checks["error"] = {
            "pass": bool(error_result.get("isError")) and "Exit code: 7" in error_text and "ERR_STDOUT" in error_text and "ERR_STDERR" in error_text,
            "is_error": error_result.get("isError", False),
            "exit_code_visible": "Exit code: 7" in error_text,
        }

        unicode_expected = contract["fixtures"]["unicode"]["expected"]
        unicode_result = client.call(
            "ctx_execute",
            {"language": "python", "code": f"print({unicode_expected!r})"},
        )
        unicode_text = text_of(unicode_result)
        responses["unicode"] = unicode_result
        checks["unicode"] = {"pass": unicode_expected in unicode_text, "utf8_replacement_present": "�" in unicode_text}

        json_expected = contract["fixtures"]["json"]["expected"]
        json_payload = json.dumps(json_expected, ensure_ascii=False, separators=(",", ":"))
        json_result = client.call(
            "ctx_execute",
            {"language": "python", "code": f"print({json_payload!r})"},
        )
        json_text = text_of(json_result)
        responses["json"] = json_result
        parsed_lines = []
        for line in json_text.splitlines():
            try:
                parsed_lines.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        checks["json"] = {"pass": json_expected in parsed_lines, "parsed_payloads": parsed_lines}

        secret_result = client.call(
            "ctx_execute_file",
            {
                "path": str(secret_file),
                "language": "javascript",
                "code": "const c=require('crypto'); console.log('sha256='+c.createHash('sha256').update(FILE_CONTENT).digest('hex')); console.log('chars='+FILE_CONTENT.length);",
            },
        )
        responses["synthetic_secret"] = secret_result
        secret_response_text = text_of(secret_result)
        secret_hash = hashlib.sha256(secret_bytes).hexdigest()
        checks["synthetic_secret"] = {
            "pass": not secret_result.get("isError") and secret not in secret_response_text and secret_hash in secret_response_text,
            "response_leak": secret in secret_response_text,
            "expected_sha256": secret_hash,
            "hash_visible": secret_hash in secret_response_text,
        }

        rows = contract["fixtures"]["truncation"]["rows"]
        payload_chars = contract["fixtures"]["truncation"]["payload_chars"]
        raw_lines = [f"SECTION-{i:03d}|TOKEN-{i:03d}|" + chr(65 + i % 26) * payload_chars for i in range(rows)]
        raw_output = "\n".join(raw_lines) + "\n"
        trunc_code = (
            "import sys\n"
            f"rows=[f'SECTION-{{i:03d}}|TOKEN-{{i:03d}}|' + chr(65+i%26)*{payload_chars} for i in range({rows})]\n"
            "sys.stdout.buffer.write(('\\n'.join(rows)+'\\n').encode('ascii'))"
        )
        trunc_result = client.call(
            "ctx_execute",
            {"language": "python", "code": trunc_code, "intent": "TOKEN sections raw recovery"},
            timeout=90,
        )
        trunc_text = text_of(trunc_result)
        responses["truncation"] = trunc_result
        checks["truncation"] = {
            "pass": "Indexed " in trunc_text and raw_output not in trunc_text,
            "raw_bytes": len(raw_output.encode()),
            "response_bytes": len(trunc_text.encode()),
            "indexed": "Indexed " in trunc_text,
        }

        search_results = []
        for start in range(0, rows, 20):
            queries = [f"TOKEN-{i:03d}" for i in range(start, min(start + 20, rows))]
            search_results.append(client.call(
                "ctx_search",
                {"queries": queries, "source": "execute:python", "limit": 1},
            ))
        search_text = "\n".join(text_of(result) for result in search_results)
        responses["raw_recovery"] = search_results
        markers = ["TOKEN-000", "TOKEN-060", "TOKEN-119"]
        row_pattern = re.compile(r"SECTION-(\d{3})\|TOKEN-\d{3}\|[A-Z]{96}")
        recovered_rows = {}
        for match in row_pattern.finditer(search_text):
            recovered_rows[int(match.group(1))] = match.group(0)
        recomposed = "\n".join(recovered_rows[i] for i in sorted(recovered_rows))
        if recomposed:
            recomposed += "\n"
        exact_recovery = len(recovered_rows) == rows and recomposed.encode("ascii") == raw_output.encode("ascii")
        checks["raw_recovery"] = {
            "pass": exact_recovery,
            "exact": exact_recovery,
            "markers_recovered": {marker: marker in search_text for marker in markers},
            "utf8_replacement_present": "�" in search_text,
            "rows_expected": rows,
            "rows_recovered": len(recovered_rows),
            "recomposition_sha256": hashlib.sha256(recomposed.encode("ascii")).hexdigest(),
            "expected_sha256": hashlib.sha256(raw_output.encode("ascii")).hexdigest(),
            "note": "Only the tested ctx_search route is classified; other public routes are not inferred from tool names.",
        }
    finally:
        server_exit = client.close()

    stderr_text = "".join(client.stderr)
    persisted = json.dumps({"responses": responses, "wire": client.raw_responses}, ensure_ascii=False)
    leak_hits, scan_errors = contains_bytes(sandbox, secret.encode(), secret_file)
    protected_after = protected_config_hashes()
    bundle_hash_after = sha256_file(server)
    checks["process"] = {"pass": server_exit == 0, "server_exit_code": server_exit}
    checks["secret_scan"] = {
        "pass": secret not in persisted and secret not in stderr_text and not leak_hits and not scan_errors,
        "response_or_result_leak": secret in persisted,
        "stderr_leak": secret in stderr_text,
        "sandbox_hits_excluding_fixture": leak_hits,
        "scan_errors": scan_errors,
    }
    checks["isolation"] = {
        "pass": protected_before == protected_after and bundle_hash_before == bundle_hash_after,
        "protected_configs_unchanged": protected_before == protected_after,
        "direct_bundle_unchanged": bundle_hash_before == bundle_hash_after,
        "protected_config_count": len(protected_after),
        "child_environment": "allowlisted",
        "entrypoint": contract["upstream"]["entrypoint"],
        "network": "not_measured",
    }
    overall = all(item["pass"] for item in checks.values())
    result = {
        "schema_version": 1,
        "upstream": contract["upstream"],
        "isolation_contract": contract["isolation"],
        "checks": checks,
        "overall_pass": overall,
        "hooks_eligible_for_evaluation": overall,
        "responses": responses,
        "server_stderr": stderr_text,
        "synthetic_secret_sha256": hashlib.sha256(secret.encode()).hexdigest(),
        "provenance": {
            "bundle_sha256": bundle_hash_after,
            "python": sys.version,
            "node": subprocess.check_output(["node", "--version"], text=True).strip(),
            "command": "python run_pilot.py --upstream <pinned-clone> --run-dir <new-private-dir> --result-output <new-result.json>",
        },
    }
    (run_dir / "result.full.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    replacements = {
        str(sandbox): "<sandbox>",
        str(args.upstream.resolve()): "<upstream>",
        str(Path.home()): "<home>",
    }
    public_result = sanitize(result, replacements)
    public_result["artifact_kind"] = "sanitized-full"
    result_output.parent.mkdir(parents=True, exist_ok=True)
    result_output.write_text(json.dumps(public_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_pass": overall, "checks": {k: v["pass"] for k, v in checks.items()}}, ensure_ascii=False, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
