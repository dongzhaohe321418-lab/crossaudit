from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from experiment.v4.feasibility import canary
from experiment.v4.feasibility import providers as provider_module
from experiment.v4.feasibility import score as score_module
from experiment.v4.feasibility import run as run_module
from experiment.v4.feasibility.run import call_cost


@pytest.mark.parametrize(
    "observed",
    [
        ["claude-sonnet-4-6"],
        ["Claude Sonnet 4.6"],
        ["claude-sonnet-4-6-20260805"],
    ],
    ids=("exact", "normalised-exact", "delimited-suffix"),
)
def test_model_alias_observed_accepts_only_exact_or_delimited_suffix(
    observed: list[str],
) -> None:
    assert provider_module.model_alias_observed("claude-sonnet-4-6", observed)


@pytest.mark.parametrize(
    "observed",
    [
        ["evil-claude-sonnet-4-6"],
        ["claude-sonnet-4-60"],
        ["claude-sonnet-4-6evil"],
        ["claude-sonnet-4"],
    ],
    ids=("prefixed-spoof", "numeric-suffix-spoof", "joined-suffix-spoof", "prefix"),
)
def test_model_alias_observed_rejects_prefix_and_suffix_spoofs(
    observed: list[str],
) -> None:
    assert not provider_module.model_alias_observed("claude-sonnet-4-6", observed)


@pytest.mark.parametrize(
    "listed,expected_source",
    [
        (None, "unavailable_anthropic_provider_total"),
        (0.0, "invalid_anthropic_zero_provider_total"),
        (float("nan"), "unavailable_anthropic_provider_total"),
        (float("inf"), "unavailable_anthropic_provider_total"),
        (-0.01, "unavailable_anthropic_provider_total"),
    ],
    ids=("missing", "zero", "nonfinite-nan", "nonfinite-inf", "negative"),
)
def test_anthropic_positive_usage_requires_a_positive_finite_provider_total(
    listed: float | None, expected_source: str,
) -> None:
    provider = SimpleNamespace(vendor="anthropic", model="claude-sonnet-4-6")
    usage = {
        "available": True,
        "invalid_nonfinite": False,
        "invalid_token_fields": False,
        "input_tokens": 10,
        "output_tokens": 2,
    }
    cost, source = call_cost(
        provider, {"list_cost_usd": listed}, usage, {"prices": {}},
    )
    assert cost is None
    assert source == expected_source


def test_valid_response_with_zero_output_usage_has_unverifiable_cost() -> None:
    provider = SimpleNamespace(vendor="openai", model="gpt-5.6-sol")
    usage = {
        "available": True,
        "invalid_nonfinite": False,
        "invalid_token_fields": False,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
    }
    cost, source = call_cost(
        provider, {"status": "valid"}, usage,
        {"prices": {"openai/gpt-5.6-sol": {
            "input_per_million": 4.0,
            "cached_input_per_million": 0.4,
            "output_per_million": 20.0,
        }}},
    )
    assert cost is None
    assert source == "invalid_zero_output_usage_for_valid_response"


@dataclass
class _CanaryProvider:
    vendor: str
    model: str
    cli: str
    calls: int = 0

    def call(
        self, *, prompt: str, schema: dict[str, Any], role: str, timeout: int,
    ) -> dict[str, Any]:
        self.calls += 1
        response: dict[str, Any] = {
            "status": "valid",
            "value": {"ok": True},
            "vendor": self.vendor,
            "model_requested": self.model,
            "cli": self.cli,
            "usage": {"input_tokens": 10, "output_tokens": 2},
            "models_observed": [self.model] if self.vendor == "anthropic" else [],
            "model_identity_evidence": (
                "provider_usage_metadata"
                if self.vendor == "anthropic"
                else "requested_alias_only_unverified"
            ),
            "list_cost_usd": 0.01 if self.vendor == "anthropic" else None,
            "unexpected_tool_events": 0,
            "event_policy_violations": [],
            "allowed_startup_notices": (
                list(provider_module.CODEX_EXPECTED_STARTUP_NOTICE_IDS)
                if self.vendor == "openai" else []
            ),
            "allowed_startup_notice_message_hashes": (
                list(provider_module.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES)
                if self.vendor == "openai" else []
            ),
            "prompt_sha256": provider_module.prompt_digest(prompt),
            "schema_sha256": provider_module.digest(schema),
            "elapsed_seconds": 0.1,
            "exit_code": 0,
            "raw_envelope": {"safe": True},
            "stderr": "",
            "provider_request_id": "test-id",
        }
        if self.vendor == "openai":
            response["allowed_startup_notice_count"] = 1
        return response


def _install_canary_mocks(
    monkeypatch: pytest.MonkeyPatch, providers: tuple[_CanaryProvider, ...],
) -> None:
    monkeypatch.setattr(canary.provider_module, "providers", lambda: providers)
    monkeypatch.setattr(
        canary.provider_module,
        "provider_runtime_binding",
        lambda provider: {
            "vendor": provider.vendor,
            "model": provider.model,
            "safe": True,
        },
    )
    monkeypatch.setattr(
        canary,
        "_cli_version",
        lambda provider: ({
            "exit_code": 0,
            "stdout": "mock 1",
            "stdout_meta": canary._opaque_text("mock 1\n"),
            "stderr_meta": canary._opaque_text(""),
        }, True),
    )


def _valid_canary_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, tuple[_CanaryProvider, ...]]:
    providers = (
        _CanaryProvider("anthropic", "claude-sonnet-4-6", "claude"),
        _CanaryProvider("openai", "gpt-5.6-sol", "codex"),
    )
    _install_canary_mocks(monkeypatch, providers)
    output = tmp_path / "receipt.json"
    assert canary.run_canary(output=output, timeout=30) == (True, [])
    return output, providers


def _validate_canary_receipt(
    output: Path, providers: tuple[_CanaryProvider, ...],
) -> dict[str, Any]:
    specs = [
        {"vendor": provider.vendor, "model": provider.model, "cli": provider.cli}
        for provider in providers
    ]
    bindings = {
        f"{provider.vendor}/{provider.model}": {
            "vendor": provider.vendor,
            "model": provider.model,
            "safe": True,
        }
        for provider in providers
    }
    return canary.validate_canary_receipt(
        output, provider_specs=specs, runtime_bindings=bindings,
    )


def test_canary_source_change_since_import_fails_before_provider_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers = (
        _CanaryProvider("anthropic", "claude-sonnet-4-6", "claude"),
        _CanaryProvider("openai", "gpt-5.6-sol", "codex"),
    )
    _install_canary_mocks(monkeypatch, providers)
    monkeypatch.setattr(
        canary,
        "expected_source_hashes",
        lambda: {"experiment/v4/feasibility/canary.py": "0" * 64},
    )
    output = tmp_path / "receipt.json"
    output.write_text("preserve me\n")

    assert canary.run_canary(output=output, timeout=30) == (
        False, ["source_changed_since_import"],
    )
    assert [provider.calls for provider in providers] == [0, 0]
    assert output.read_text() == "preserve me\n"


@pytest.mark.parametrize(
    "mutation",
    (
        "non-object-provider",
        "extra-receipt-field",
        "extra-provider-field",
        "extra-usage-field",
    ),
)
def test_canary_preflight_rejects_malformed_or_extended_provider_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    output, providers = _valid_canary_receipt(tmp_path, monkeypatch)
    receipt = json.loads(output.read_text())
    if mutation == "non-object-provider":
        receipt["providers"][0] = "not-an-object"
    elif mutation == "extra-receipt-field":
        receipt["unregistered_evidence"] = True
    elif mutation == "extra-provider-field":
        receipt["providers"][0]["unregistered_evidence"] = True
    else:
        receipt["providers"][0]["usage"]["unregistered_tokens"] = 1
    receipt["receipt_sha256"] = provider_module.digest({
        key: value for key, value in receipt.items() if key != "receipt_sha256"
    })
    output.write_text(json.dumps(receipt))

    with pytest.raises(RuntimeError, match="canary preflight failed"):
        _validate_canary_receipt(output, providers)


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1/org/repo.git",
        "https://127.1/org/repo.git",
        "https://2130706433/org/repo.git",
        "https://0x7f000001/org/repo.git",
        "https://10.1/org/repo.git",
        "git://github.com/example/crossaudit.git",
        "ssh://git@127.42.1.2/org/repo.git",
        "https://10.0.0.1/org/repo.git",
        "https://172.16.0.1/org/repo.git",
        "https://192.168.1.1/org/repo.git",
        "https://169.254.10.2/org/repo.git",
        "ssh://git@[::1]/org/repo.git",
        "https://[fe80::1]/org/repo.git",
        "https://[fc00::1]/org/repo.git",
    ],
)
def test_network_anchor_rejects_loopback_private_and_link_local_remotes(url: str) -> None:
    assert not score_module._non_file_remote_url(url)
    assert not run_module._non_file_remote_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/example/crossaudit.git",
        "ssh://git@github.com/example/crossaudit.git",
        "git@github.com:example/crossaudit.git",
    ],
)
def test_network_anchor_accepts_github_remotes(url: str) -> None:
    assert score_module._non_file_remote_url(url)
    assert run_module._non_file_remote_url(url)


def _analysis_receipt(
    *, seal_commit: str, first_analysis_tip: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    static = {
        "format_version": "v4-feasibility-analysis-receipt-1",
        "freeze_sha256": "f" * 64,
        "cohort_seal_bytes_sha256": "c" * 64,
        "summary_bytes_sha256": "d" * 64,
        "pre_analysis_freeze_commit": "a" * 40,
        "pre_dispatch_network_tip": "b" * 40,
        "pre_analysis_seal_commit": seal_commit,
        "schedule_finished": True,
        "scientific_outputs_withheld": False,
        "claim_boundary": "non-confirmatory feasibility evidence",
    }
    receipt = {
        **static,
        "network_remote_tip_at_analysis": first_analysis_tip,
        "created_utc": "2026-09-01T00:00:00+00:00",
        "note": "test",
    }
    receipt["receipt_sha256"] = score_module._digest(receipt)
    return receipt, static


def test_analysis_receipt_rejects_first_analysis_tip_without_seal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seal_commit = "1" * 40
    first_tip = "2" * 40
    current_tip = "3" * 40
    receipt, static = _analysis_receipt(
        seal_commit=seal_commit, first_analysis_tip=first_tip,
    )

    def fake_git(*args: str, check: bool = True) -> SimpleNamespace:
        returncode = int(args == (
            "merge-base", "--is-ancestor", seal_commit, first_tip,
        ))
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(score_module, "_git", fake_git)
    with pytest.raises(ValueError, match="does not contain the cohort seal"):
        score_module._validate_analysis_receipt(receipt, static, current_tip)


def test_analysis_receipt_accepts_advanced_remote_descendant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seal_commit = "1" * 40
    first_tip = "2" * 40
    current_tip = "3" * 40
    receipt, static = _analysis_receipt(
        seal_commit=seal_commit, first_analysis_tip=first_tip,
    )
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str, check: bool = True) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(score_module, "_git", fake_git)
    score_module._validate_analysis_receipt(receipt, static, current_tip)
    assert (
        "merge-base", "--is-ancestor", seal_commit, first_tip,
    ) in calls
    assert (
        "merge-base", "--is-ancestor", first_tip, current_tip,
    ) in calls


def _ledger_review() -> dict[str, Any]:
    return {
        "accept": True,
        "accept_probability": 0.9,
        "tamper_detected": False,
        "tamper_probability": 0.1,
        "origin_round": 0,
        "first_defective_round": None,
        "rule_version": "v4-feasibility-C2",
        "insufficient_evidence": False,
    }


def test_ledger_contrast_marks_episode_incomplete_when_one_vendor_surface_is_missing() -> None:
    events: list[dict[str, Any]] = [{
        "kind": "ledger_truth",
        "episode_id": "L1",
        "truth": {"accept": True, "tamper_truth": False, "attack": "none"},
    }]
    for interface, vendors in (("E0", ("A", "B")), ("E1", ("A",)), ("E2", ("A", "B"))):
        for vendor in vendors:
            events.append({
                "kind": "ledger_outcome",
                "episode_id": "L1",
                "interface": interface,
                "reviewer_vendor": vendor,
                "reviewer_session": f"{vendor}-session",
                "call_id": f"L1-{interface}-{vendor}",
                "status": "valid",
                "review_schema_valid": True,
                "review": _ledger_review(),
                "correct_accept": 1,
                "correct_tamper": 1,
                "correct_origin": 1,
                "correct_first_defective": 1,
                "correct_rounds": 1,
                "correct_rule": 1,
                "elapsed_seconds": 1.0,
            })

    contrast = score_module._ledger_summary(events)[
        "episode_clustered_proxy_contrasts"
    ]["correct_accept"]["E1_minus_E0"]
    assert contrast["required_rows_per_level"] == 2
    assert contrast["incomplete_clusters"] == ["L1"]
    assert contrast["n_clusters"] == 0
    assert contrast["estimate"] is None


def test_whole_loop_unavailable_harm_is_missing_but_itt_acceptability_is_zero() -> None:
    rows: list[dict[str, Any]] = []
    for generator in ("A", "B"):
        for assignment in ("same", "cross"):
            unavailable = generator == "B" and assignment == "cross"
            rows.append({
                "kind": "whole_loop_end",
                "task_id": "T1",
                "branch_id": f"T1-{generator}-{assignment}",
                "generator_vendor": generator,
                "assignment": assignment,
                "fraction_initial_resolved_ITT": 0.0 if unavailable else 1.0,
                "final_acceptable": 0 if unavailable else 1,
                "new_defect_count": None if unavailable else 0,
                "unnecessary_changed_fields": None if unavailable else [],
                "revisions": 0,
            })
    summary = score_module._whole_loop_summary(rows, {
        "task_ids": ["T1"],
        "generator_vendors": ["A", "B"],
        "auditor_vendors": ["A", "B"],
    })

    assert summary["by_assignment"]["cross"]["final_acceptable"]["mean"] == 0.5
    assert summary["by_assignment"]["cross"]["new_defect_any"]["n_missing"] == 1
    acceptability = summary["cross_minus_same_task_clustered"]["final_acceptable"]
    assert acceptability["incomplete_clusters"] == []
    assert acceptability["estimate"] == -0.5
    harm = summary["cross_minus_same_task_clustered"]["new_defect_any"]
    assert harm["incomplete_clusters"] == ["T1"]
    assert harm["estimate"] is None


def test_code_quality_tradeoff_is_never_labelled_compliance_only() -> None:
    def row(
        policy: str, *, static: bool, visible: bool, held: bool, checks: int,
    ) -> dict[str, Any]:
        return {
            "kind": "defensive_code_artifact",
            "artifact_id": f"A-{policy}",
            "task_id": "F-CODE-01",
            "generator_vendor": "openai",
            "policy": policy,
            "round": 0,
            "value": {"checks": ["check"] * checks, "limitations": []},
            "evaluation": {
                "static_ok": static,
                "visible_correct": visible,
                "held_out_correct": held,
                "metrics": {
                    "loc": 1, "wrapper_count": 0, "assertion_count": 0,
                    "exception_count": 0, "retry_count": 0,
                    "disclaimer_count": 0, "words": 1, "bytes": 1,
                },
            },
        }

    summary = score_module._defensive_summary([
        row("P0", static=False, visible=True, held=False, checks=0),
        row("P1", static=True, visible=False, held=False, checks=1),
    ])
    labels = summary["scientific_python_policy_arms"][
        "initial_change_labels_vs_P0"
    ]["P1"]["label_counts"]
    assert labels == {"quality_changed": 1}
