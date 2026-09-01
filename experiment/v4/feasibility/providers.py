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
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CODEX_SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")

# Every name below was checked against ``codex features list`` for the frozen
# CLI before registration.  ``skip_host_skill_discovery`` is an opt-out feature
# and must therefore be enabled.  ``unified_exec`` is requested off but Codex
# 0.151.0 reports it as an always-on stable feature; the frozen effective state
# exposes that residual risk while the outer sandbox still denies child exec.
CODEX_ENABLED_FEATURES = ("skip_host_skill_discovery",)
CODEX_DISABLED_FEATURES = (
    "apps",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "code_mode",
    "code_mode_host",
    "computer_use",
    "enable_mcp_apps",
    "hooks",
    "image_generation",
    "in_app_browser",
    "multi_agent",
    "multi_agent_v2",
    "plugins",
    "plugin_sharing",
    "remote_plugin",
    "shell_snapshot",
    "shell_snapshot_v2",
    "shell_tool",
    "skill_mcp_dependency_install",
    "skill_search",
    "standalone_web_search",
    "tool_call_mcp_elicitation",
    "tool_suggest",
    "unified_exec",
    "view_image",
    "workspace_dependencies",
)
CODEX_ALLOWED_RESIDUAL_ENABLED_FEATURES = frozenset({"unified_exec"})
CODEX_ALLOWED_EVENT_TYPES = frozenset({
    "thread.started", "turn.started", "turn.completed",
    "item.started", "item.updated", "item.completed",
})
CODEX_ALLOWED_EVENT_FIELDS = {
    "thread.started": frozenset({"type", "thread_id"}),
    "turn.started": frozenset({"type"}),
    "turn.completed": frozenset({"type", "usage"}),
    "item.started": frozenset({"type", "item"}),
    "item.updated": frozenset({"type", "item"}),
    "item.completed": frozenset({"type", "item"}),
}
CODEX_ALLOWED_ITEM_TYPES = frozenset({"agent_message", "reasoning"})
CODEX_ALLOWED_ITEM_FIELDS = frozenset({"id", "type", "text"})
CODEX_ALLOWED_STARTUP_NOTICE_FIELDS = frozenset({"id", "type", "message"})
CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID = "item_0"
CODEX_CODE_MODE_FAIL_CLOSED_NOTICE = (
    "Code Mode is unavailable because code-mode host is disabled. Code mode will "
    "fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`."
)
CODEX_EXPECTED_STARTUP_NOTICE_IDS = ("code_mode_host_disabled_fail_closed",)
CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES = (
    hashlib.sha256(CODEX_CODE_MODE_FAIL_CLOSED_NOTICE.encode("utf-8")).hexdigest(),
)
NEUTRAL_SYSTEM_INSTRUCTION = (
    "Follow the user task. Do not use tools. Return only the object required by the "
    "supplied output schema."
)
NETWORK_GIT_ANCHOR_HOSTS = frozenset({"github.com"})


def network_git_remote_allowed(url: str) -> bool:
    """Accept only the study's named external Git host, never path/IP aliases."""
    if not url or url.startswith(("file://", "/", "./", "../", "~")):
        return False
    host: str | None = None
    if re.match(r"^(?:https|ssh)://[^/\s]+/", url):
        try:
            host = urlparse(url).hostname
        except ValueError:
            return False
    else:
        match = re.fullmatch(r"(?:[^/@\s]+@)?(\[[^\]]+\]|[^/:\s]+):[^\s]+", url)
        if match:
            host = match.group(1).strip("[]")
    return bool(host) and host.rstrip(".").lower() in NETWORK_GIT_ANCHOR_HOSTS


def identity_requirement(vendor: str) -> str:
    return (
        "required_observed_alias" if vendor == "anthropic"
        else "unavailable_allowed"
    )


def model_alias_observed(requested: str, observed_models: Any) -> bool:
    """Match an exact alias token sequence, allowing only a delimited suffix."""
    def normalise(value: str) -> str:
        return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))

    wanted = normalise(requested)
    if len(wanted) < 4 or not isinstance(observed_models, list):
        return False
    candidates = [
        normalise(model)
        for model in observed_models if isinstance(model, str)
    ]
    return bool(candidates) and all(candidates) and any(
        model == wanted or model.startswith(wanted + "-") for model in candidates
    )


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


def git_verification_env() -> dict[str, str]:
    """Return the restricted environment with Git replace objects disabled."""
    env = safe_subprocess_env()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
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


def codex_feature_override_args() -> list[str]:
    args: list[str] = []
    for name in CODEX_ENABLED_FEATURES:
        args.extend(("--enable", name))
    for name in CODEX_DISABLED_FEATURES:
        args.extend(("--disable", name))
    return args


def codex_exec_fixed_args() -> list[str]:
    """Return the fixed, locally help-validated Codex exec arguments."""
    return [
        "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
        "--strict-config", "-c", "suppress_unstable_features_warning=true",
        *codex_feature_override_args(),
        "--skip-git-repo-check", "--sandbox", "read-only",
    ]


def codex_effective_feature_state(native: Path) -> dict[str, bool]:
    """Read and validate selected effective features without a model request."""
    proc = subprocess.run(
        [str(native), "features", "list", *codex_feature_override_args()],
        capture_output=True, text=True, timeout=20, env=safe_subprocess_env(),
    )
    if proc.returncode:
        raise RuntimeError(
            "could not verify frozen Codex feature state: "
            + (proc.stderr.strip() or f"exit {proc.returncode}")
        )
    observed: dict[str, bool] = {}
    selected = set(CODEX_ENABLED_FEATURES) | set(CODEX_DISABLED_FEATURES)
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] in selected and parts[-1] in {"true", "false"}:
            observed[parts[0]] = parts[-1] == "true"
    missing = selected - set(observed)
    if missing:
        raise RuntimeError(
            "Codex feature probe omitted registered names: " + ", ".join(sorted(missing))
        )
    wrong_enabled = [name for name in CODEX_ENABLED_FEATURES if not observed[name]]
    unsafe_enabled = [
        name for name in CODEX_DISABLED_FEATURES
        if observed[name] and name not in CODEX_ALLOWED_RESIDUAL_ENABLED_FEATURES
    ]
    if wrong_enabled or unsafe_enabled:
        raise RuntimeError(
            "Codex safety feature overrides were not effective: "
            f"required_true={wrong_enabled}, required_false={unsafe_enabled}"
        )
    return dict(sorted(observed.items()))


def codex_invocation_policy(native: Path, model: str) -> dict[str, Any]:
    """Return the exact command/tool/event policy bound into the freeze."""
    effective = codex_effective_feature_state(native)
    profile = no_subprocess_profile(native)
    return {
        "fixed_exec_args": codex_exec_fixed_args(),
        "dynamic_exec_args": [
            "--model", model, "-c", "model_reasoning_effort=low",
            "--output-schema", "<ephemeral-output-schema-path>", "--json", "-",
        ],
        "feature_overrides": {
            "enabled": list(CODEX_ENABLED_FEATURES),
            "disabled": list(CODEX_DISABLED_FEATURES),
        },
        "effective_selected_features": effective,
        "residual_enabled_requested_disabled": sorted(
            name for name in CODEX_DISABLED_FEATURES if effective[name]
        ),
        "web_search_cli_flag_present": False,
        "config_sources": {
            "user_config": "ignored",
            "project_rules": "ignored; fresh temporary cwd",
            "host_skill_discovery": "skipped by enabled opt-out feature",
        },
        "outer_sandbox": {
            "executable": str(CODEX_SANDBOX_EXEC),
            "profile": profile,
            "profile_sha256": hashlib.sha256(profile.encode("utf-8")).hexdigest(),
        },
        "event_allowlist": {
            "event_types": sorted(CODEX_ALLOWED_EVENT_TYPES),
            "event_fields": {
                name: sorted(fields)
                for name, fields in sorted(CODEX_ALLOWED_EVENT_FIELDS.items())
            },
            "item_types": sorted(CODEX_ALLOWED_ITEM_TYPES),
            "item_fields": sorted(CODEX_ALLOWED_ITEM_FIELDS),
            "allowed_local_startup_notices": [{
                "id": CODEX_EXPECTED_STARTUP_NOTICE_IDS[0],
                "event_type": "item.completed",
                "item_type": "error",
                "item_fields": sorted(CODEX_ALLOWED_STARTUP_NOTICE_FIELDS),
                "item_id": CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
                "message_sha256": hashlib.sha256(
                    CODEX_CODE_MODE_FAIL_CLOSED_NOTICE.encode("utf-8")
                ).hexdigest(),
                "required_count": 1,
                "required_position": (
                    "second_nonempty_event_after_thread.started_before_turn.started"
                ),
                "meaning": "disabled code-mode host is confirmed fail-closed",
            }],
            "unknown_or_other_error_event": "provider_event_policy_violation",
        },
    }


def provider_runtime_binding(provider: "Provider") -> dict[str, Any]:
    """Freeze the exact CLI/native code and secret-free security route."""
    cli_path = resolved_cli_path(provider.cli)
    executables: dict[str, Any] = {
        "cli": {"requested": provider.cli, **_binary_identity(cli_path)},
    }
    invocation_policy = None
    if provider.vendor == "openai":
        native = codex_native_binary(provider.cli)
        executables["native"] = _binary_identity(native)
        executables["sandbox_exec"] = _binary_identity(CODEX_SANDBOX_EXEC)
        invocation_policy = codex_invocation_policy(native, provider.model)
    binding = {
        "vendor": provider.vendor,
        "model": provider.model,
        "executables": executables,
        "security_route_environment": security_route_environment_binding(),
        "system_instruction": {
            "value": NEUTRAL_SYSTEM_INSTRUCTION,
            "sha256": hashlib.sha256(
                NEUTRAL_SYSTEM_INSTRUCTION.encode("utf-8")
            ).hexdigest(),
        },
    }
    if invocation_policy is not None:
        binding["invocation_policy"] = invocation_policy
    return binding


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
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode()
    return hashlib.sha256(raw).hexdigest()


def prompt_digest(prompt: str) -> str:
    """Hash the exact evaluation-prompt string as raw UTF-8 bytes."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _codex_violation(line_number: int, reason: str, *, raw: str,
                     event: dict[str, Any] | None = None) -> dict[str, Any]:
    item = event.get("item") if isinstance(event, dict) else None
    return {
        "line_number": line_number,
        "reason": reason,
        "event_type": event.get("type") if isinstance(event, dict) else None,
        "item_type": item.get("type") if isinstance(item, dict) else None,
        "raw_line_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    }


def _codex_allowed_startup_notice_id(event: dict[str, Any]) -> str | None:
    """Recognise one exact local fail-closed notice, never arbitrary errors."""
    if event.get("type") != "item.completed" or set(event) != {"type", "item"}:
        return None
    item = event.get("item")
    if not isinstance(item, dict) or set(item) != CODEX_ALLOWED_STARTUP_NOTICE_FIELDS:
        return None
    if item.get("type") != "error" \
            or item.get("id") != CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID:
        return None
    if item.get("message") != CODEX_CODE_MODE_FAIL_CLOSED_NOTICE:
        return None
    return CODEX_EXPECTED_STARTUP_NOTICE_IDS[0]


def codex_startup_notice_evidence(
    events: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """Derive named notice IDs and message hashes from exact raw events."""
    ids: list[str] = []
    hashes: list[str] = []
    for event in events:
        notice_id = _codex_allowed_startup_notice_id(event)
        if notice_id is None:
            continue
        ids.append(notice_id)
        message = event["item"]["message"]
        hashes.append(hashlib.sha256(message.encode("utf-8")).hexdigest())
    return ids, hashes


def parse_codex_event_stream(stdout: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse Codex JSONL and reject every event/item outside a safe allowlist."""
    events: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for line_number, raw in enumerate(stdout.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            violations.append(_codex_violation(
                line_number, "non_json_event_line", raw=raw,
            ))
            continue
        if not isinstance(event, dict):
            violations.append(_codex_violation(
                line_number, "event_is_not_an_object", raw=raw,
            ))
            continue
        events.append(event)
        event_type = event.get("type")
        if event_type not in CODEX_ALLOWED_EVENT_TYPES:
            violations.append(_codex_violation(
                line_number, "event_type_not_allowlisted", raw=raw, event=event,
            ))
            continue
        error_value = event.get("error")
        if error_value is not None and error_value != "":
            violations.append(_codex_violation(
                line_number, "event_contains_error", raw=raw, event=event,
            ))
        unknown_event_fields = sorted(
            set(event) - CODEX_ALLOWED_EVENT_FIELDS[str(event_type)]
        )
        if unknown_event_fields:
            violations.append(_codex_violation(
                line_number,
                "allowlisted_event_has_unknown_fields:" + ",".join(unknown_event_fields),
                raw=raw, event=event,
            ))
            continue
        if isinstance(event_type, str) and event_type.startswith("item."):
            item = event.get("item")
            if not isinstance(item, dict):
                violations.append(_codex_violation(
                    line_number, "item_event_missing_object", raw=raw, event=event,
                ))
                continue
            item_type = item.get("type")
            if item_type == "error" and _codex_allowed_startup_notice_id(event):
                fixed_startup_prefix = (
                    len(events) == 2
                    and events[0].get("type") == "thread.started"
                )
                if not fixed_startup_prefix:
                    violations.append(_codex_violation(
                        line_number, "allowed_startup_notice_wrong_position",
                        raw=raw, event=event,
                    ))
                continue
            if item_type not in CODEX_ALLOWED_ITEM_TYPES:
                violations.append(_codex_violation(
                    line_number, "item_type_not_allowlisted", raw=raw, event=event,
                ))
                continue
            unknown_fields = sorted(set(item) - CODEX_ALLOWED_ITEM_FIELDS)
            if unknown_fields:
                violations.append(_codex_violation(
                    line_number, "allowlisted_item_has_unknown_fields:" + ",".join(unknown_fields),
                    raw=raw, event=event,
                ))
                continue
            text = item.get("text")
            if event_type == "item.completed" and not isinstance(text, str):
                violations.append(_codex_violation(
                    line_number, "completed_item_missing_text", raw=raw, event=event,
                ))
    notice_ids, notice_hashes = codex_startup_notice_evidence(events)
    if notice_ids != list(CODEX_EXPECTED_STARTUP_NOTICE_IDS) \
            or notice_hashes != list(CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES):
        violations.append({
            "line_number": None,
            "reason": "required_startup_notice_set_mismatch",
            "event_type": "item.completed",
            "item_type": "error",
            "raw_line_sha256": None,
        })
    elif len(events) < 3 or [event.get("type") for event in events[:3]] != [
        "thread.started", "item.completed", "turn.started",
    ] or _codex_allowed_startup_notice_id(events[1]) is None:
        violations.append({
            "line_number": None,
            "reason": "required_startup_event_prefix_mismatch",
            "event_type": "item.completed",
            "item_type": "error",
            "raw_line_sha256": None,
        })
    return events, violations


@dataclass(frozen=True)
class Provider:
    vendor: str
    model: str
    cli: str

    def call(self, *, prompt: str, schema: dict[str, Any], role: str, timeout: int = 300) -> dict[str, Any]:
        started = time.monotonic()
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
            "prompt_sha256": prompt_digest(prompt),
            "schema_sha256": digest(schema),
            "elapsed_seconds": round(time.monotonic() - started, 3),
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
            "--system-prompt", NEUTRAL_SYSTEM_INSTRUCTION,
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
            usage_payload = outer.get("usage")
            server_tools = (
                usage_payload.get("server_tool_use", {})
                if isinstance(usage_payload, dict) else {}
            )
            used_external_tool = (
                any(server_tools.values())
                if isinstance(server_tools, dict) else bool(server_tools)
            )
            if used_external_tool:
                tool_names = (
                    sorted(str(name) for name, count in server_tools.items() if count)
                    if isinstance(server_tools, dict)
                    else ["unrecognised_server_tool_use_shape"]
                )
                return {
                    "status": "provider_event_policy_violation",
                    "exit_code": 0,
                    "value": None,
                    "usage": outer.get("usage"),
                    "model_usage": outer.get("modelUsage"),
                    "list_cost_usd": outer.get("total_cost_usd"),
                    "models_observed": sorted((outer.get("modelUsage") or {}).keys()),
                    "model_identity_evidence": "provider_usage_metadata",
                    "provider_request_id": outer.get("uuid"),
                    "event_policy_violations": [{
                        "reason": "anthropic_server_tool_use_nonzero",
                        "server_tool_names": tool_names,
                    }],
                    "discarded_raw_envelope_sha256": hashlib.sha256(
                        proc.stdout.encode("utf-8")
                    ).hexdigest(),
                    "raw_envelope": {
                        "discarded": True,
                        "reason": "server tool use violates no-tool policy",
                        "server_tool_names": tool_names,
                    },
                    "stderr": proc.stderr[-4000:],
                }
            return {"status": "valid", "exit_code": 0, "value": value,
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
        schema_path.write_text(json.dumps(schema, indent=2, allow_nan=False) + "\n")
        full_prompt = NEUTRAL_SYSTEM_INSTRUCTION + "\n\n" + prompt
        sandbox_exec = CODEX_SANDBOX_EXEC
        if not sandbox_exec.is_file():
            raise RuntimeError("sandbox-exec unavailable; refusing an unisolated Codex call")
        native = codex_native_binary(self.cli)
        cmd = [
            str(sandbox_exec), "-p", no_subprocess_profile(native), str(native),
            *codex_exec_fixed_args(), "--model", self.model,
            "-c", "model_reasoning_effort=low", "--output-schema", str(schema_path),
            "--json", "-",
        ]
        proc = subprocess.run(cmd, cwd=work, input=full_prompt, capture_output=True, text=True,
                              timeout=timeout, env=safe_subprocess_env())
        events, event_policy_violations = parse_codex_event_stream(proc.stdout)
        startup_notice_ids, startup_notice_hashes = codex_startup_notice_evidence(events)
        usage = next(
            (event.get("usage") for event in reversed(events)
             if event.get("type") == "turn.completed"),
            None,
        )
        thread_id = next(
            (event.get("thread_id") for event in events
             if event.get("type") == "thread.started"),
            None,
        )
        if event_policy_violations:
            return {
                "status": "provider_event_policy_violation",
                "exit_code": proc.returncode,
                "value": None,
                "usage": usage,
                "list_cost_usd": None,
                "models_observed": [],
                "model_identity_evidence": "requested_alias_only_unverified",
                "event_policy_violations": event_policy_violations,
                "allowed_startup_notices": startup_notice_ids,
                "allowed_startup_notice_count": len(startup_notice_ids),
                "allowed_startup_notice_message_hashes": startup_notice_hashes,
                "discarded_raw_envelope_sha256": hashlib.sha256(
                    proc.stdout.encode("utf-8")
                ).hexdigest(),
                "provider_request_id": thread_id,
                "raw_envelope": {
                    "discarded": True,
                    "event_count": len(events),
                    "reason": "event allowlist violation",
                },
                "stderr": proc.stderr[-4000:],
            }
        messages = [
            item["text"]
            for event in events
            if event.get("type") == "item.completed"
            and isinstance((item := event.get("item")), dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ]
        if proc.returncode:
            return {"status": "provider_error", "exit_code": proc.returncode,
                    "stderr": proc.stderr[-4000:], "raw_envelope": events[-20:]}
        try:
            value = json.loads(messages[-1])
            return {"status": "valid", "exit_code": 0, "value": value, "usage": usage,
                    "list_cost_usd": None, "models_observed": [],
                    "model_identity_evidence": "requested_alias_only_unverified",
                    "unexpected_tool_events": 0,
                    "event_policy_violations": [],
                    "allowed_startup_notices": startup_notice_ids,
                    "allowed_startup_notice_count": len(startup_notice_ids),
                    "allowed_startup_notice_message_hashes": startup_notice_hashes,
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
