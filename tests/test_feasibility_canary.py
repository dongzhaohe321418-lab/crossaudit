from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from experiment.v4.feasibility import canary


@dataclass
class CanaryProvider:
    vendor: str
    model: str
    cli: str
    response_overrides: dict[str, Any]
    calls: int = 0

    def call(self, *, prompt: str, schema: dict[str, Any], role: str,
             timeout: int) -> dict[str, Any]:
        self.calls += 1
        response: dict[str, Any] = {
            "status": "valid", "value": {"ok": True},
            "vendor": self.vendor, "model_requested": self.model, "cli": self.cli,
            "usage": {"input_tokens": 10, "output_tokens": 2},
            "models_observed": [self.model] if self.vendor == "anthropic" else [],
            "model_identity_evidence": (
                "provider_usage_metadata" if self.vendor == "anthropic"
                else "requested_alias_only_unverified"
            ),
            "list_cost_usd": 0.01 if self.vendor == "anthropic" else None,
            "unexpected_tool_events": 0, "event_policy_violations": [],
            "allowed_startup_notices": (
                list(canary.provider_module.CODEX_EXPECTED_STARTUP_NOTICE_IDS)
                if self.vendor == "openai" else []
            ),
            "allowed_startup_notice_message_hashes": (
                list(canary.provider_module.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES)
                if self.vendor == "openai" else []
            ),
            "prompt_sha256": canary.provider_module.prompt_digest(prompt),
            "schema_sha256": canary.provider_module.digest(schema),
            "elapsed_seconds": 0.1, "exit_code": 0,
            "raw_envelope": {"safe": True}, "stderr": "", "provider_request_id": "id",
        }
        if self.vendor == "openai":
            response["allowed_startup_notice_count"] = 1
        response.update(self.response_overrides)
        return response


def _install_mocks(monkeypatch: pytest.MonkeyPatch, providers: tuple[CanaryProvider, ...]) -> None:
    monkeypatch.setattr(canary.provider_module, "providers", lambda: providers)
    monkeypatch.setattr(
        canary.provider_module, "provider_runtime_binding",
        lambda provider: {"vendor": provider.vendor, "model": provider.model, "safe": True},
    )
    monkeypatch.setattr(
        canary, "_cli_version",
        lambda provider: ({
            "exit_code": 0, "stdout": "mock 1",
            "stdout_meta": canary._opaque_text("mock 1\n"),
            "stderr_meta": canary._opaque_text(""),
        }, True),
    )


def test_canary_writes_only_after_two_valid_single_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers = (
        CanaryProvider("anthropic", "claude-sonnet-4-6", "claude", {
            "usage": {
                "input_tokens": 10, "output_tokens": 2,
                "server_tool_use": {
                    "web_search_requests": 0, "web_fetch_requests": 0,
                },
            },
        }),
        CanaryProvider("openai", "gpt-5.6-sol", "codex", {}),
    )
    _install_mocks(monkeypatch, providers)
    output = tmp_path / "receipt.json"
    success, failures = canary.run_canary(output=output, timeout=30)
    assert success is True and failures == []
    assert [provider.calls for provider in providers] == [1, 1]
    receipt = json.loads(output.read_text())
    assert receipt["format_version"] == "v4-feasibility-canary-4"
    assert [row["vendor"] for row in receipt["providers"]] == ["anthropic", "openai"]
    rendered = output.read_text()
    assert '"raw_envelope":' not in rendered
    assert '"provider_request_id":' not in rendered
    specs = [
        {"vendor": provider.vendor, "model": provider.model, "cli": provider.cli}
        for provider in providers
    ]
    bindings = {
        f"{provider.vendor}/{provider.model}": {
            "vendor": provider.vendor, "model": provider.model, "safe": True,
        }
        for provider in providers
    }
    assert canary.validate_canary_receipt(
        output, provider_specs=specs, runtime_bindings=bindings,
    ) == receipt


@pytest.mark.parametrize(
    "vendor,overrides,expected",
    [
        ("openai", {"usage": {}}, "billable_usage_unavailable"),
        ("openai", {"allowed_startup_notice_count": 0},
         "allowed_startup_notice_count_mismatch"),
        ("openai", {"usage": {"input_tokens": 0, "output_tokens": 0}},
         "zero_output_usage_for_valid_response"),
        ("anthropic", {"list_cost_usd": None}, "anthropic_list_cost_unavailable"),
        ("anthropic", {
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "list_cost_usd": 0.0,
        }, "zero_anthropic_provider_total"),
        ("anthropic", {"models_observed": ["wrong-model"]}, "requested_model_not_observed"),
        ("openai", {"vendor": "wrong"}, "vendor_mismatch"),
    ],
)
def test_canary_cost_identity_and_usage_failures_do_not_replace_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    vendor: str, overrides: dict[str, Any], expected: str,
) -> None:
    providers = (
        CanaryProvider(
            "anthropic", "claude-sonnet-4-6", "claude",
            overrides if vendor == "anthropic" else {},
        ),
        CanaryProvider(
            "openai", "gpt-5.6-sol", "codex",
            overrides if vendor == "openai" else {},
        ),
    )
    _install_mocks(monkeypatch, providers)
    output = tmp_path / "receipt.json"
    output.write_text("old receipt\n")
    success, failures = canary.run_canary(output=output, timeout=30)
    assert success is False
    assert any(failure.endswith(expected) for failure in failures)
    assert output.read_text() == "old receipt\n"


def test_canary_secret_in_raw_response_never_reaches_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-ant-abcdefghijklmnopqrstuvwxyz"
    providers = (
        CanaryProvider(
            "anthropic", "claude-sonnet-4-6", "claude",
            {"raw_envelope": {"secret": secret}},
        ),
        CanaryProvider("openai", "gpt-5.6-sol", "codex", {}),
    )
    _install_mocks(monkeypatch, providers)
    output = tmp_path / "receipt.json"
    output.write_text("preserved\n")
    success, failures = canary.run_canary(output=output, timeout=30)
    assert success is False
    assert any(failure.endswith("secret_in_provider_response") for failure in failures)
    assert output.read_text() == "preserved\n"
    assert secret not in output.read_text()


@pytest.mark.parametrize(
    "mutation",
    ("old-format", "stale-source", "missing-provider", "tool-use-hidden-by-count"),
)
def test_canary_preflight_rejects_old_stale_incomplete_or_action_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    providers = (
        CanaryProvider("anthropic", "claude-sonnet-4-6", "claude", {}),
        CanaryProvider("openai", "gpt-5.6-sol", "codex", {}),
    )
    _install_mocks(monkeypatch, providers)
    output = tmp_path / "receipt.json"
    assert canary.run_canary(output=output, timeout=30)[0] is True
    receipt = json.loads(output.read_text())
    if mutation == "old-format":
        receipt["format_version"] = "v4-feasibility-canary-2"
    elif mutation == "stale-source":
        receipt["source_hashes"]["experiment/v4/feasibility/canary.py"] = "0" * 64
    elif mutation == "missing-provider":
        receipt["providers"].pop()
    else:
        # The dict is the primary evidence; a forged aggregate of zero must not
        # hide an observed server-side action.
        receipt["providers"][0]["server_tool_use"] = {"web_search_requests": 1}
        receipt["providers"][0]["server_tool_use_count"] = 0
    receipt["receipt_sha256"] = canary.provider_module.digest({
        key: value for key, value in receipt.items() if key != "receipt_sha256"
    })
    output.write_text(json.dumps(receipt))
    specs = [
        {"vendor": provider.vendor, "model": provider.model, "cli": provider.cli}
        for provider in providers
    ]
    bindings = {
        f"{provider.vendor}/{provider.model}": {
            "vendor": provider.vendor, "model": provider.model, "safe": True,
        }
        for provider in providers
    }
    with pytest.raises(RuntimeError, match="canary preflight failed"):
        canary.validate_canary_receipt(
            output, provider_specs=specs, runtime_bindings=bindings,
        )
