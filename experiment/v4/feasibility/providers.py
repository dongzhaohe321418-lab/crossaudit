"""Fresh-context CLI adapters used by the v4 feasibility cohort.

The adapters preserve each CLI's full envelope, including usage and latency.
They do not claim identical hidden system prompts.  Consequently the cohort
estimates configuration-level effects for these two agent products, not a
vendor-population effect or a pure weights-only effect.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# OAuth/keychain-backed CLIs need the user's home and executable path, but the
# model subprocess must not inherit arbitrary API keys or project secrets.  A
# provider that needs another variable must add it here deliberately and record
# the change in the feasibility freeze.
SAFE_ENV_NAMES = {
    "HOME", "PATH", "TMPDIR", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL",
    "LC_CTYPE", "TERM", "COLORTERM", "XDG_CONFIG_HOME", "CODEX_HOME",
    "CLAUDE_CONFIG_DIR", "OPENAI_CONFIG_HOME", "OPENAI_PROFILE",
    "ANTHROPIC_PROFILE", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "NODE_EXTRA_CA_CERTS",
    # The desktop host routes outbound provider traffic through these values.
    # They are available to the CLI process but any model tool use makes the
    # record invalid below, so the model cannot inspect them and still pass.
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "all_proxy", "no_proxy",
}

# These variables select the network route, trust roots, or on-disk auth
# profile used by the provider CLIs.  Their values are never written to the
# freeze: only presence and a one-way digest are retained.  HOME is included
# because it is the implicit auth-profile root when a CLI-specific override is
# absent.
SECURITY_ROUTE_ENV_NAMES = (
    "HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR", "OPENAI_CONFIG_HOME",
    "OPENAI_PROFILE", "ANTHROPIC_PROFILE", "XDG_CONFIG_HOME",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE", "NODE_EXTRA_CA_CERTS",
)


def safe_subprocess_env() -> dict[str, str]:
    env = {name: value for name, value in os.environ.items() if name in SAFE_ENV_NAMES}
    env.update({"CI": "1", "NO_COLOR": "1"})
    return env


def security_route_environment_binding() -> dict[str, Any]:
    """Return a secret-free binding for routing, trust and auth-profile state."""
    safe = safe_subprocess_env()
    variables: dict[str, dict[str, Any]] = {}
    for name in SECURITY_ROUTE_ENV_NAMES:
        value = safe.get(name)
        variables[name] = {
            "present": value is not None,
            "value_sha256": (
                hashlib.sha256(value.encode()).hexdigest() if value is not None else None
            ),
        }
    return {
        "variables": variables,
        "binding_sha256": hashlib.sha256(
            json.dumps(
                variables, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ).encode()
        ).hexdigest(),
    }


def resolved_cli_path(cli: str) -> Path:
    """Resolve one CLI through only the PATH that its child process receives."""
    located = shutil.which(cli, path=safe_subprocess_env().get("PATH"))
    if located is None:
        raise FileNotFoundError(f"provider CLI not found: {cli}")
    resolved = Path(located).resolve(strict=True)
    if not resolved.is_file():
        raise RuntimeError(f"provider CLI is not a regular file: {resolved}")
    return resolved


def _binary_identity(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise RuntimeError(f"provider executable is not a regular file: {resolved}")
    return {
        "resolved_path": str(resolved),
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        "size_bytes": resolved.stat().st_size,
    }


def codex_native_binary(cli: str) -> Path:
    """Resolve the packaged native Codex binary without starting a shell.

    The npm entry point is a JavaScript launcher.  Running that launcher under
    ``sandbox-exec`` would require allowing Node to spawn the native binary,
    which would also make model-requested subprocesses possible.  Calling the
    native binary directly lets the OS profile allow exactly one initial exec
    and deny every later exec before it occurs.
    """
    entry = resolved_cli_path(cli)
    if entry.is_file() and entry.read_bytes()[:4] in {b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"}:
        return entry
    package_root = entry.parent.parent
    candidates = sorted(package_root.glob("node_modules/@openai/codex-*/vendor/*/bin/codex"))
    if len(candidates) != 1:
        raise RuntimeError(
            "Could not resolve one packaged native Codex binary; refusing an "
            f"unisolated call (found {len(candidates)})"
        )
    return candidates[0].resolve()


def provider_runtime_binding(provider: "Provider") -> dict[str, Any]:
    """Freeze the exact CLI/native code and secret-free security route."""
    cli_path = resolved_cli_path(provider.cli)
    executables: dict[str, Any] = {
        "cli": {"requested": provider.cli, **_binary_identity(cli_path)},
    }
    if provider.vendor == "openai":
        executables["native"] = _binary_identity(codex_native_binary(provider.cli))
    return {
        "vendor": provider.vendor,
        "model": provider.model,
        "executables": executables,
        "security_route_environment": security_route_environment_binding(),
    }


def verify_provider_runtime_binding(provider: "Provider", expected: dict[str, Any]) -> None:
    """Fail before dispatch if executable bytes, paths or routing state drift."""
    observed = provider_runtime_binding(provider)
    if canonical(observed) != canonical(expected):
        raise RuntimeError(
            f"runtime binding drift for {provider.vendor}/{provider.model}; "
            "refusing provider dispatch"
        )


def no_subprocess_profile(initial_binary: Path) -> str:
    """Return a macOS profile that denies every exec except the initial one."""
    raw = str(initial_binary)
    if '"' in raw or "\n" in raw:
        raise ValueError("unsafe executable path for sandbox profile")
    return (
        '(version 1)(allow default)(deny process-exec)'
        f'(allow process-exec (literal "{raw}"))'
    )


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Provider:
    vendor: str
    model: str
    cli: str

    def call(self, *, prompt: str, schema: dict[str, Any], role: str, timeout: int = 300) -> dict[str, Any]:
        started = time.time()
        try:
            with tempfile.TemporaryDirectory(prefix="crossaudit-v4-") as td:
                work = Path(td)
                if self.vendor == "anthropic":
                    rec = self._anthropic(work, prompt, schema, role, timeout)
                elif self.vendor == "openai":
                    rec = self._openai(work, prompt, schema, role, timeout)
                else:
                    raise ValueError(f"unsupported provider {self.vendor}")
        except subprocess.TimeoutExpired as exc:
            rec = {
                "status": "timeout",
                "exit_code": None,
                "timeout_seconds": timeout,
                "raw_envelope": "",
                "stderr": str(exc),
            }
        rec.update({
            "vendor": self.vendor,
            "model_requested": self.model,
            "cli": self.cli,
            "role": role,
            "prompt_sha256": digest(prompt.encode()),
            "schema_sha256": digest(schema),
            "elapsed_seconds": round(time.time() - started, 3),
        })
        return rec

    def _anthropic(self, work: Path, prompt: str, schema: dict[str, Any], role: str, timeout: int) -> dict[str, Any]:
        cmd = [
            str(resolved_cli_path(self.cli)),
            "--safe-mode",
            "--restricted",
            "--tools", "",
            "--strict-mcp-config",
            "--mcp-config", '{"mcpServers":{}}',
            "--print",
            "--no-session-persistence",
            "--max-budget-usd", "1.0",
            "--effort", "low",
            "--model", self.model,
            "--output-format", "json",
            "--json-schema", canonical(schema),
            "--system-prompt", (
                f"You are the {role} in a blinded research evaluation. Do not use tools. "
                "Return only the object required by the supplied JSON schema."
            ),
        ]
        proc = subprocess.run(cmd, cwd=work, input=prompt, capture_output=True, text=True,
                              timeout=timeout, env=safe_subprocess_env())
        if proc.returncode:
            return {"status": "provider_error", "exit_code": proc.returncode,
                    "stderr": proc.stderr[-4000:], "raw_envelope": proc.stdout[-4000:]}
        try:
            outer = json.loads(proc.stdout)
            value = outer.get("structured_output")
            if value is None:
                value = json.loads(outer.get("result", ""))
            server_tools = outer.get("usage", {}).get("server_tool_use", {})
            used_external_tool = any(v for v in server_tools.values()) if isinstance(server_tools, dict) else False
            status = "parse_error" if used_external_tool else "valid"
            return {"status": status, "exit_code": 0, "value": value,
                    "usage": outer.get("usage"), "model_usage": outer.get("modelUsage"),
                    "list_cost_usd": outer.get("total_cost_usd"),
                    "models_observed": sorted((outer.get("modelUsage") or {}).keys()),
                    "model_identity_evidence": "provider_usage_metadata",
                    "provider_request_id": outer.get("uuid"), "raw_envelope": outer,
                    "stderr": proc.stderr[-4000:]}
        except Exception as exc:
            return {"status": "parse_error", "exit_code": 0, "parse_error": str(exc),
                    "raw_envelope": proc.stdout[-12000:], "stderr": proc.stderr[-4000:]}

    def _openai(self, work: Path, prompt: str, schema: dict[str, Any], role: str, timeout: int) -> dict[str, Any]:
        schema_path = work / "output.schema.json"
        schema_path.write_text(json.dumps(schema, indent=2) + "\n")
        full_prompt = (
            f"You are the {role} in a blinded research evaluation. Do not use tools. "
            "Return only the object required by the output schema.\n\n" + prompt
        )
        sandbox_exec = Path("/usr/bin/sandbox-exec")
        if not sandbox_exec.is_file():
            raise RuntimeError("sandbox-exec unavailable; refusing an unisolated Codex call")
        native = codex_native_binary(self.cli)
        cmd = [
            str(sandbox_exec), "-p", no_subprocess_profile(native), str(native),
            "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox", "read-only", "--model", self.model,
            "-c", "model_reasoning_effort=low", "--output-schema", str(schema_path),
            "--json", "-",
        ]
        proc = subprocess.run(cmd, cwd=work, input=full_prompt, capture_output=True, text=True,
                              timeout=timeout, env=safe_subprocess_env())
        events: list[dict[str, Any]] = []
        for line in proc.stdout.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        messages = [e["item"]["text"] for e in events
                    if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
        usage = next((e.get("usage") for e in reversed(events) if e.get("type") == "turn.completed"), None)
        thread_id = next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), None)
        tool_events = [e for e in events if "tool" in str(e.get("type", "")).lower()
                       or "tool" in str(e.get("item", {}).get("type", "")).lower()]
        if proc.returncode:
            return {"status": "provider_error", "exit_code": proc.returncode,
                    "stderr": proc.stderr[-4000:], "raw_envelope": events[-20:]}
        try:
            value = json.loads(messages[-1])
            status = "parse_error" if tool_events else "valid"
            return {"status": status, "exit_code": 0, "value": value, "usage": usage,
                    "list_cost_usd": None, "models_observed": [],
                    "model_identity_evidence": "requested_alias_only_unverified",
                    "unexpected_tool_events": len(tool_events),
                    "provider_request_id": thread_id, "raw_envelope": events,
                    "stderr": proc.stderr[-4000:]}
        except Exception as exc:
            return {"status": "parse_error", "exit_code": 0, "parse_error": str(exc),
                    "raw_envelope": events[-20:], "stderr": proc.stderr[-4000:]}


def providers() -> tuple[Provider, Provider]:
    return (
        Provider("anthropic", "claude-sonnet-4-6", "claude"),
        Provider("openai", "gpt-5.6-sol", "codex"),
    )
