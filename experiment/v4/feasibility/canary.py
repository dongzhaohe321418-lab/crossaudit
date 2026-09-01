#!/usr/bin/env python3
"""Run the content-free, post-hardening provider isolation canary.

This command calls each configuration returned by ``providers.providers()``
exactly once.  It never persists provider envelopes: only a validated,
secret-scanned receipt containing safe summaries and one-way hashes can replace
the formal receipt.  Use ``--execute`` explicitly; importing this module or
asking for help performs no provider call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.version_info < (3, 10):  # pragma: no cover - project floor is Python 3.10
    raise RuntimeError("CrossAudit v4 feasibility requires Python 3.10 or newer")

try:  # Module execution and direct-script execution are both supported.
    from . import providers as provider_module
    from .run import SECRET_PATTERNS, normalise_usage
    from .schema import validate_json_schema, validate_schema_definition
except ImportError:  # pragma: no cover - exercised by direct CLI execution
    import providers as provider_module
    from run import SECRET_PATTERNS, normalise_usage
    from schema import validate_json_schema, validate_schema_definition


FORMAT_VERSION = "v4-feasibility-canary-4"
PROMPT = 'Return exactly {"ok":true}.'
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"ok": {"type": "boolean", "enum": [True]}},
    "required": ["ok"],
    "additionalProperties": False,
}
ROLE = "content-free canary"
PURPOSE = (
    "content-free post-hardening connectivity, schema, runtime-binding, "
    "event-allowlist and no-tool isolation canary"
)
CLAIM_BOUNDARY = "not cohort data and not evidence about audit efficacy"
DEFAULT_RECEIPT = Path(__file__).with_name("CANARY-RECEIPT.json")
SOURCE_FILES = {
    "experiment/v4/feasibility/canary.py": Path(__file__).resolve(),
    "experiment/v4/feasibility/providers.py": Path(provider_module.__file__).resolve(),
    "experiment/v4/feasibility/run.py": Path(__file__).with_name("run.py").resolve(),
    "experiment/v4/feasibility/schema.py": Path(__file__).with_name("schema.py").resolve(),
}
RECEIPT_FIELDS = frozenset({
    "format_version", "executed_utc", "purpose", "claim_boundary",
    "source_hashes", "call_contract", "prompt_sha256", "schema",
    "schema_sha256", "providers", "secret_scan", "receipt_sha256",
})
PROVIDER_ROW_FIELDS = frozenset({
    "vendor", "requested_model", "cli", "cli_version", "runtime_binding",
    "runtime_binding_before_sha256", "runtime_binding_after_sha256",
    "runtime_binding_stable_during_call", "status", "value",
    "local_schema_validation", "usage", "list_cost_usd", "models_observed",
    "model_identity_evidence", "exit_code", "elapsed_seconds",
    "prompt_sha256", "schema_sha256", "event_policy_violation_count",
    "event_policy_violations", "unexpected_tool_event_count", "server_tool_use",
    "server_tool_use_count", "raw_envelope_meta", "stderr_meta",
    "provider_request_id_meta", "response_secret_scan_hits",
    "allowed_startup_notice_count", "allowed_startup_notices",
    "allowed_startup_notice_message_hashes",
})
USAGE_FIELDS = frozenset({
    "available", "billable_fields_complete", "invalid_nonfinite",
    "invalid_token_fields", "input_tokens", "output_tokens",
    "cached_input_tokens", "cache_creation_input_tokens",
    "cache_write_input_tokens", "reasoning_tokens", "provenance",
    "source_entry_count",
})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256(path.read_bytes())


def _canonical(value: Any, *, strict: bool = False) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=not strict,
        default=repr,
    )


def _opaque_text(value: Any) -> dict[str, Any]:
    if value is None:
        return {"present": False, "utf8_bytes": 0, "sha256": None}
    raw = str(value).encode("utf-8")
    return {"present": True, "utf8_bytes": len(raw), "sha256": _sha256(raw)}


def _opaque_json(value: Any) -> dict[str, Any]:
    if value is None:
        return {"present": False, "canonical_json_bytes": 0, "sha256": None}
    raw = _canonical(value).encode("utf-8")
    return {
        "present": True,
        "canonical_json_bytes": len(raw),
        "sha256": _sha256(raw),
    }


def _secret_hits(value: Any) -> list[str]:
    rendered = _canonical(value)
    return sorted(name for name, pattern in SECRET_PATTERNS if pattern.search(rendered))


def _safe_number(value: Any, *, nonnegative: bool = False) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    if not math.isfinite(number) or (nonnegative and number < 0):
        return None
    return value


def _cli_version(provider: provider_module.Provider) -> tuple[dict[str, Any], bool]:
    try:
        proc = subprocess.run(
            [str(provider_module.resolved_cli_path(provider.cli)), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            env=provider_module.safe_subprocess_env(),
        )
    except Exception as exc:
        return {
            "exit_code": None,
            "stdout": None,
            "stdout_meta": _opaque_text(None),
            "stderr_meta": _opaque_text(None),
            "error_type": type(exc).__name__,
        }, False
    stdout = proc.stdout.strip()
    return {
        "exit_code": proc.returncode,
        "stdout": stdout[:1000],
        "stdout_meta": _opaque_text(proc.stdout),
        "stderr_meta": _opaque_text(proc.stderr),
    }, proc.returncode == 0 and bool(stdout)


def _server_tool_summary(response: dict[str, Any]) -> tuple[dict[str, int], int, bool]:
    usage = response.get("usage")
    raw = usage.get("server_tool_use") if isinstance(usage, dict) else None
    if raw is None:
        return {}, 0, True
    if not isinstance(raw, dict):
        return {}, 0, False
    summary: dict[str, int] = {}
    valid = True
    for name, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or value < 0 or int(value) != value:
            valid = False
            continue
        if int(value) > 0:
            summary[str(name)] = int(value)
    return dict(sorted(summary.items())), sum(summary.values()), valid


def _event_violation_summary(response: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    raw = response.get("event_policy_violations", [])
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        return [], False
    summary: list[dict[str, Any]] = []
    valid = True
    for item in raw:
        if not isinstance(item, dict):
            valid = False
            continue
        summary.append({
            "reason": str(item.get("reason", "missing"))[:200],
            "event_type": (
                None if item.get("event_type") is None
                else str(item.get("event_type"))[:100]
            ),
            "item_type": (
                None if item.get("item_type") is None
                else str(item.get("item_type"))[:100]
            ),
        })
    return summary, valid


def _summarise_response(
    response: dict[str, Any], provider: provider_module.Provider,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    status = response.get("status")
    value = response.get("value")
    schema_errors = validate_json_schema(value, SCHEMA)
    if status != "valid":
        failures.append("non_valid_status")
    if value != {"ok": True}:
        failures.append("value_not_exact_ok_true")
    if schema_errors:
        failures.append("local_schema_error")
    for field, expected in (
        ("vendor", provider.vendor),
        ("model_requested", provider.model),
        ("cli", provider.cli),
    ):
        if response.get(field) != expected:
            failures.append(f"{field}_mismatch")

    event_violations, event_shape_valid = _event_violation_summary(response)
    if not event_shape_valid or event_violations:
        failures.append("event_policy_violation")

    raw_notices = response.get("allowed_startup_notices", [])
    if not isinstance(raw_notices, list) or not all(
        isinstance(item, str) for item in raw_notices
    ):
        startup_notices: list[str] = []
        failures.append("invalid_allowed_startup_notices")
    else:
        startup_notices = list(raw_notices)
    expected_notices = (
        list(provider_module.CODEX_EXPECTED_STARTUP_NOTICE_IDS)
        if provider.vendor == "openai" else []
    )
    if startup_notices != expected_notices:
        failures.append("allowed_startup_notice_mismatch")
    raw_notice_count = response.get(
        "allowed_startup_notice_count", 0 if provider.vendor != "openai" else None,
    )
    if type(raw_notice_count) is not int or raw_notice_count != len(startup_notices) \
            or raw_notice_count != len(expected_notices):
        failures.append("allowed_startup_notice_count_mismatch")
    raw_notice_hashes = response.get("allowed_startup_notice_message_hashes", [])
    if not isinstance(raw_notice_hashes, list) or not all(
        isinstance(item, str) and re.fullmatch(r"[0-9a-f]{64}", item)
        for item in raw_notice_hashes
    ):
        startup_notice_hashes: list[str] = []
        failures.append("invalid_allowed_startup_notice_message_hashes")
    else:
        startup_notice_hashes = list(raw_notice_hashes)
    expected_notice_hashes = (
        list(provider_module.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES)
        if provider.vendor == "openai" else []
    )
    if startup_notice_hashes != expected_notice_hashes:
        failures.append("allowed_startup_notice_message_hash_mismatch")

    unexpected = response.get("unexpected_tool_events", 0)
    if isinstance(unexpected, bool) or not isinstance(unexpected, (int, float)) \
            or not math.isfinite(float(unexpected)) or unexpected < 0 \
            or int(unexpected) != unexpected:
        unexpected_count = 0
        failures.append("invalid_unexpected_tool_count")
    else:
        unexpected_count = int(unexpected)
        if unexpected_count:
            failures.append("unexpected_tool_event")

    server_tools, server_tool_count, server_tool_shape_valid = _server_tool_summary(response)
    if not server_tool_shape_valid:
        failures.append("invalid_server_tool_summary")
    if server_tool_count:
        failures.append("server_tool_use")

    models = response.get("models_observed", [])
    if not isinstance(models, list) or not all(isinstance(model, str) for model in models):
        models = []
        failures.append("invalid_models_observed")
    if models:
        if not provider_module.model_alias_observed(provider.model, models):
            failures.append("requested_model_not_observed")
    elif provider.vendor == "anthropic":
        failures.append("requested_model_not_observed")

    list_cost = response.get("list_cost_usd")
    if list_cost is not None and _safe_number(list_cost, nonnegative=True) is None:
        failures.append("invalid_list_cost")
        list_cost = None
    if provider.vendor == "anthropic" and list_cost is None:
        failures.append("anthropic_list_cost_unavailable")
    elapsed = _safe_number(response.get("elapsed_seconds"), nonnegative=True)
    if response.get("elapsed_seconds") is not None and elapsed is None:
        failures.append("invalid_elapsed_seconds")

    if response.get("prompt_sha256") != provider_module.prompt_digest(PROMPT):
        failures.append("prompt_hash_mismatch")
    if response.get("schema_sha256") != provider_module.digest(SCHEMA):
        failures.append("schema_hash_mismatch")

    response_secret_hits = _secret_hits(response)
    if response_secret_hits:
        failures.append("secret_in_provider_response")

    usage = normalise_usage(response)
    if usage.get("available") is not True or usage.get("billable_fields_complete") is not True:
        failures.append("billable_usage_unavailable")
    if usage.get("invalid_nonfinite") is True:
        failures.append("invalid_nonfinite_usage")
    if int(usage.get("output_tokens", 0) or 0) <= 0:
        failures.append("zero_output_usage_for_valid_response")
    if provider.vendor == "anthropic" and list_cost is not None \
            and float(list_cost) == 0.0:
        failures.append("zero_anthropic_provider_total")

    return {
        "status": status if isinstance(status, str) else None,
        "value": value if value == {"ok": True} else None,
        "local_schema_validation": {
            "valid": not schema_errors,
            "errors": schema_errors[:20],
        },
        "usage": usage,
        "list_cost_usd": list_cost,
        "models_observed": sorted(models),
        "model_identity_evidence": (
            str(response.get("model_identity_evidence"))[:200]
            if response.get("model_identity_evidence") is not None else None
        ),
        "exit_code": response.get("exit_code")
            if type(response.get("exit_code")) is int else None,
        "elapsed_seconds": elapsed,
        "prompt_sha256": response.get("prompt_sha256"),
        "schema_sha256": response.get("schema_sha256"),
        "event_policy_violation_count": len(event_violations),
        "event_policy_violations": event_violations,
        "allowed_startup_notice_count": (
            raw_notice_count if type(raw_notice_count) is int else None
        ),
        "allowed_startup_notices": startup_notices,
        "allowed_startup_notice_message_hashes": startup_notice_hashes,
        "unexpected_tool_event_count": unexpected_count,
        "server_tool_use": server_tools,
        "server_tool_use_count": server_tool_count,
        "raw_envelope_meta": _opaque_json(response.get("raw_envelope")),
        "stderr_meta": _opaque_text(response.get("stderr")),
        "provider_request_id_meta": _opaque_text(response.get("provider_request_id")),
        "response_secret_scan_hits": response_secret_hits,
    }, sorted(set(failures))


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(
        value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False,
    ) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def expected_source_hashes() -> dict[str, str]:
    return {name: _file_sha256(path) for name, path in sorted(SOURCE_FILES.items())}


IMPORTED_SOURCE_HASHES = expected_source_hashes()


def validate_canary_receipt(
    path: Path, *, provider_specs: list[dict[str, Any]],
    runtime_bindings: dict[str, Any],
) -> dict[str, Any]:
    """Fail closed unless ``path`` proves the current post-hardening canary passed."""
    try:
        receipt = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError("post-hardening canary receipt is unreadable") from exc
    errors: list[str] = []
    if not isinstance(receipt, dict):
        raise RuntimeError("post-hardening canary receipt is not an object")
    if set(receipt) != RECEIPT_FIELDS:
        errors.append("unexpected or missing receipt fields")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if receipt.get("receipt_sha256") != provider_module.digest(unsigned):
        errors.append("invalid receipt self-hash")
    if receipt.get("format_version") != FORMAT_VERSION:
        errors.append("wrong format version")
    if receipt.get("purpose") != PURPOSE or receipt.get("claim_boundary") != CLAIM_BOUNDARY:
        errors.append("wrong canary purpose or claim boundary")
    executed = receipt.get("executed_utc")
    try:
        executed_time = datetime.fromisoformat(executed) if isinstance(executed, str) else None
    except ValueError:
        executed_time = None
    if executed_time is None or executed_time.tzinfo is None:
        errors.append("invalid canary execution time")
    if receipt.get("source_hashes") != expected_source_hashes():
        errors.append("stale canary dependency hashes")
    if receipt.get("prompt_sha256") != provider_module.prompt_digest(PROMPT):
        errors.append("wrong canary prompt hash")
    if receipt.get("schema") != SCHEMA or receipt.get("schema_sha256") != provider_module.digest(SCHEMA):
        errors.append("wrong canary schema")
    contract = receipt.get("call_contract")
    if not isinstance(contract, dict) or set(contract) != {
        "provider_factory", "calls_per_returned_provider", "provider_count",
        "role_metadata", "timeout_seconds",
    } or contract.get("provider_factory") != "providers.providers" \
            or contract.get("calls_per_returned_provider") != 1 \
            or contract.get("provider_count") != len(provider_specs) \
            or contract.get("role_metadata") != ROLE \
            or type(contract.get("timeout_seconds")) is not int \
            or not 1 <= contract["timeout_seconds"] <= 600:
        errors.append("wrong canary call contract")
    expected = {
        f"{row.get('vendor')}/{row.get('model')}": row for row in provider_specs
        if isinstance(row, dict)
    }
    provider_rows = receipt.get("providers")
    observed: dict[str, dict[str, Any]] = {}
    if isinstance(provider_rows, list):
        for row in provider_rows:
            if not isinstance(row, dict):
                errors.append("canary provider evidence row is not an object")
                continue
            key = f"{row.get('vendor')}/{row.get('requested_model')}"
            if key in observed:
                errors.append("duplicate canary provider")
            observed[key] = row
    else:
        errors.append("canary providers is not a list")
    if not isinstance(provider_rows, list) or len(provider_rows) != len(expected):
        errors.append("canary provider evidence row count is wrong")
    if set(observed) != set(expected) or len(expected) != len(provider_specs):
        errors.append("canary providers differ from frozen providers")
    for key, spec in expected.items():
        row = observed.get(key)
        if not isinstance(row, dict):
            continue
        if set(row) != PROVIDER_ROW_FIELDS:
            errors.append(f"{key}: unexpected or missing provider evidence fields")
        if row.get("cli") != spec.get("cli"):
            errors.append(f"{key}: wrong cli")
        if row.get("status") != "valid" or row.get("value") != {"ok": True}:
            errors.append(f"{key}: canary did not return valid ok=true")
        local = row.get("local_schema_validation")
        if not isinstance(local, dict) or local.get("valid") is not True or local.get("errors") != []:
            errors.append(f"{key}: local schema validation failed")
        if row.get("prompt_sha256") != receipt.get("prompt_sha256") \
                or row.get("schema_sha256") != receipt.get("schema_sha256"):
            errors.append(f"{key}: provider hash mismatch")
        binding = runtime_bindings.get(key)
        if row.get("runtime_binding") != binding \
                or row.get("runtime_binding_stable_during_call") is not True \
                or row.get("runtime_binding_before_sha256") != provider_module.digest(binding) \
                or row.get("runtime_binding_after_sha256") != provider_module.digest(binding):
            errors.append(f"{key}: runtime binding mismatch")
        cli_version = row.get("cli_version")
        if not isinstance(cli_version, dict) or set(cli_version) != {
            "exit_code", "stdout", "stdout_meta", "stderr_meta",
        } or cli_version.get("exit_code") != 0 or not cli_version.get("stdout"):
            errors.append(f"{key}: cli version unavailable")
        usage = row.get("usage")
        token_fields = USAGE_FIELDS - {
            "available", "billable_fields_complete", "invalid_nonfinite",
            "invalid_token_fields", "provenance",
        }
        if not isinstance(usage, dict) or set(usage) != USAGE_FIELDS \
                or any(type(usage.get(field)) is not int or usage[field] < 0
                       for field in token_fields) \
                or usage.get("provenance") not in {
                    "top_level_usage", "model_usage", "sum_of_model_usage_entries",
                } or usage.get("available") is not True \
                or usage.get("billable_fields_complete") is not True \
                or usage.get("invalid_nonfinite") is not False \
                or usage.get("invalid_token_fields") is not False \
                or int(usage.get("output_tokens", 0) or 0) <= 0:
            errors.append(f"{key}: billable usage unavailable")
        if row.get("exit_code") != 0:
            errors.append(f"{key}: provider process did not exit successfully")
        if _safe_number(row.get("elapsed_seconds"), nonnegative=True) is None:
            errors.append(f"{key}: elapsed time is invalid")
        if row.get("event_policy_violation_count") != 0 \
                or row.get("event_policy_violations") != [] \
                or row.get("unexpected_tool_event_count") != 0 \
                or row.get("server_tool_use") != {} \
                or row.get("server_tool_use_count") != 0 \
                or row.get("response_secret_scan_hits") != []:
            errors.append(f"{key}: action or secret isolation failed")
        expected_notices = (
            list(provider_module.CODEX_EXPECTED_STARTUP_NOTICE_IDS)
            if spec.get("vendor") == "openai" else []
        )
        if row.get("allowed_startup_notices") != expected_notices \
                or row.get("allowed_startup_notice_count") != len(expected_notices):
            errors.append(f"{key}: allowed local startup notices differ from contract")
        expected_notice_hashes = (
            list(provider_module.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES)
            if spec.get("vendor") == "openai" else []
        )
        if row.get("allowed_startup_notice_message_hashes") != expected_notice_hashes:
            errors.append(f"{key}: allowed local startup notice hashes differ from contract")
        models = row.get("models_observed")
        if not isinstance(models, list) or not all(isinstance(model, str) for model in models):
            errors.append(f"{key}: model observations are malformed")
            models = []
        if spec.get("vendor") == "anthropic":
            observed_cost = _safe_number(row.get("list_cost_usd"), nonnegative=True)
            if observed_cost is None or float(observed_cost) <= 0.0:
                errors.append(f"{key}: provider total cost unavailable")
            if not provider_module.model_alias_observed(
                str(spec.get("model", "")), models,
            ):
                errors.append(f"{key}: requested model not observed")
    secret = receipt.get("secret_scan")
    if not isinstance(secret, dict) or set(secret) != {"patterns", "hits"} \
            or secret.get("hits") != [] \
            or secret.get("patterns") != [name for name, _ in SECRET_PATTERNS]:
        errors.append("receipt secret scan is invalid")
    if _secret_hits(receipt):
        errors.append("receipt contains a secret pattern")
    if errors:
        raise RuntimeError("post-hardening canary preflight failed: " + "; ".join(errors))
    return receipt


def run_canary(*, output: Path, timeout: int) -> tuple[bool, list[str]]:
    schema_definition_errors = validate_schema_definition(SCHEMA)
    if schema_definition_errors:
        return False, ["invalid_canary_schema_definition"]

    source_hashes_before = expected_source_hashes()
    if source_hashes_before != IMPORTED_SOURCE_HASHES:
        return False, ["source_changed_since_import"]
    prompt_sha = provider_module.prompt_digest(PROMPT)
    schema_sha = provider_module.digest(SCHEMA)
    provider_receipts: list[dict[str, Any]] = []
    failures: list[str] = []
    provider_list = provider_module.providers()
    if len(provider_list) != 2 or len({provider.vendor for provider in provider_list}) != 2:
        return False, ["provider_factory_did_not_return_two_distinct_vendors"]

    for provider in provider_list:
        label = f"{provider.vendor}/{provider.model}"
        cli_version, cli_version_valid = _cli_version(provider)
        if not cli_version_valid:
            failures.append(f"{label}:cli_version_unavailable")

        try:
            binding_before = provider_module.provider_runtime_binding(provider)
        except Exception:
            failures.append(f"{label}:runtime_binding_before_failed")
            continue

        response: dict[str, Any] | None = None
        try:
            candidate = provider.call(
                prompt=PROMPT,
                schema=SCHEMA,
                role=ROLE,
                timeout=timeout,
            )
            if isinstance(candidate, dict):
                response = candidate
            else:
                failures.append(f"{label}:provider_response_not_object")
        except Exception:
            failures.append(f"{label}:provider_call_failed")

        try:
            binding_after = provider_module.provider_runtime_binding(provider)
        except Exception:
            failures.append(f"{label}:runtime_binding_after_failed")
            binding_after = None

        binding_stable = (
            binding_after is not None
            and provider_module.canonical(binding_before)
            == provider_module.canonical(binding_after)
        )
        if not binding_stable:
            failures.append(f"{label}:runtime_binding_drift")
        if response is None:
            continue

        safe_response, response_failures = _summarise_response(response, provider)
        failures.extend(f"{label}:{failure}" for failure in response_failures)
        provider_receipts.append({
            "vendor": provider.vendor,
            "requested_model": provider.model,
            "cli": provider.cli,
            "cli_version": cli_version,
            "runtime_binding": binding_before,
            "runtime_binding_before_sha256": provider_module.digest(binding_before),
            "runtime_binding_after_sha256": (
                provider_module.digest(binding_after)
                if binding_after is not None else None
            ),
            "runtime_binding_stable_during_call": binding_stable,
            **safe_response,
        })

    if len(provider_receipts) != len(provider_list):
        failures.append("missing_provider_receipt_summary")

    receipt: dict[str, Any] = {
        "format_version": FORMAT_VERSION,
        "executed_utc": _utc_now(),
        "purpose": PURPOSE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_hashes": source_hashes_before,
        "call_contract": {
            "provider_factory": "providers.providers",
            "calls_per_returned_provider": 1,
            "provider_count": len(provider_list),
            "role_metadata": ROLE,
            "timeout_seconds": timeout,
        },
        "prompt_sha256": prompt_sha,
        "schema": SCHEMA,
        "schema_sha256": schema_sha,
        "providers": provider_receipts,
        "secret_scan": {
            "patterns": [name for name, _ in SECRET_PATTERNS],
            "hits": [],
        },
    }

    if expected_source_hashes() != source_hashes_before:
        failures.append("source_changed_during_canary")
    persisted_secret_hits = _secret_hits(receipt)
    if persisted_secret_hits:
        failures.extend(f"receipt_secret:{name}" for name in persisted_secret_hits)
    try:
        _canonical(receipt, strict=True)
    except (TypeError, ValueError):
        failures.append("receipt_not_strict_json")

    failures = sorted(set(failures))
    if failures:
        return False, failures
    receipt["receipt_sha256"] = provider_module.digest(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    provider_specs = [
        {"vendor": provider.vendor, "model": provider.model, "cli": provider.cli}
        for provider in provider_list
    ]
    runtime_bindings = {
        f"{row['vendor']}/{row['requested_model']}": row["runtime_binding"]
        for row in provider_receipts
    }
    try:
        with tempfile.TemporaryDirectory(prefix="crossaudit-canary-", dir=output.parent) as td:
            candidate = Path(td) / "candidate.json"
            _atomic_write_json(candidate, receipt)
            validate_canary_receipt(
                candidate, provider_specs=provider_specs,
                runtime_bindings=runtime_bindings,
            )
            os.replace(candidate, output)
    except Exception:
        return False, ["candidate_receipt_self_validation_failed"]
    return True, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform exactly one content-free call to each frozen provider",
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--output", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("refusing provider calls without explicit --execute")
    if not 1 <= args.timeout <= 600:
        parser.error("--timeout must be between 1 and 600 seconds")

    success, failures = run_canary(output=args.output, timeout=args.timeout)
    if not success:
        # Failure codes are fixed labels and never include provider output.
        print("canary failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    receipt_hash = _file_sha256(args.output)
    print(f"wrote validated canary receipt: {args.output} sha256={receipt_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
