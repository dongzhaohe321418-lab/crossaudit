from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import select
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from experiment.v4.feasibility import providers as provider_module
from experiment.v4.feasibility import run as run_module
from experiment.v4.feasibility import score as score_module
from experiment.v4.feasibility.run import (
    ARTIFACT_SCHEMA,
    AUDIT_SCHEMA,
    CODE_SCHEMA,
    CODE_TASKS,
    LEDGER_REVIEW_SCHEMA,
    CallRunner,
    Journal,
    audit_gate,
    build_freeze_core,
    call_cost,
    evaluate_code_artifact,
    normalise_usage,
    planned_calls,
    run_study,
    validate_freeze_document,
    verify_freeze_committed_and_pushed,
)
from experiment.v4.feasibility.tasks import TASKS, clean_control, validate_artifact


@dataclass(frozen=True)
class FakeProvider:
    vendor: str
    model: str
    cli: str = "fake"

    def _task(self, prompt: str):
        return next(task for task in TASKS if task.task_id in prompt or task.brief in prompt)

    def call(self, *, prompt: str, schema: dict[str, Any], role: str,
             timeout: int = 300) -> dict[str, Any]:
        if schema == ARTIFACT_SCHEMA:
            task = self._task(prompt)
            value = clean_control(task, {})
        elif schema == AUDIT_SCHEMA:
            task = self._task(prompt)
            raw = prompt.split("Artefact:\n", 1)[1]
            artifact = ast.literal_eval(raw)
            defects = validate_artifact(task, artifact)
            findings = [
                {
                    "severity": "BLOCKER", "rule_id": f"F-{d['class'].upper()}-001",
                    "location": d["location"], "description": d["description"],
                    "confidence": 0.95,
                }
                for d in defects
            ]
            value = {
                "verdict": "BLOCK" if findings else "PASS", "confidence": 0.95,
                "checks_performed": ["deterministic recomputation"], "findings": findings,
            }
        elif schema == CODE_SCHEMA:
            if "F-CODE-01" in prompt:
                code = "def final_change(values):\n    return abs(values[-1] - values[-2])"
            else:
                code = (
                    "def exact_slope(points):\n"
                    "    return (points[-1][1] - points[0][1]) / "
                    "(points[-1][0] - points[0][0])"
                )
            value = {"code": code, "explanation": "direct formula",
                     "checks": ["visible fixture"], "limitations": []}
        elif schema == LEDGER_REVIEW_SCHEMA:
            # Structural mock only. The scoring test verifies ITT denominators,
            # not that this deliberately simple proxy is a good reviewer.
            value = {
                "accept": False, "accept_probability": 0.2,
                "tamper_detected": False, "tamper_probability": 0.1,
                "origin_round": 1, "first_defective_round": 0,
                "rule_version": "v4-feasibility-C2",
                "insufficient_evidence": "\"interface\":\"E0\"" in prompt,
            }
        else:  # pragma: no cover - a new schema must update the mock explicitly
            raise AssertionError("unexpected schema")
        response = {
            "status": "valid", "value": value,
            "vendor": self.vendor, "model_requested": self.model,
            "cli": self.cli, "role": role, "elapsed_seconds": 0.01,
            "usage": {"input_tokens": 10, "output_tokens": 5,
                      "cached_input_tokens": 0, "reasoning_tokens": 0},
            "models_observed": [self.model],
            "prompt_sha256": provider_module.prompt_digest(prompt),
            "schema_sha256": provider_module.digest(schema),
        }
        if self.vendor == "anthropic":
            response["list_cost_usd"] = 0.0001
            response["model_usage"] = {
                self.model: {"inputTokens": 10, "outputTokens": 5}
            }
        return response


def price_table(*providers: FakeProvider) -> dict[str, Any]:
    return {
        "currency": "USD",
        "prices": {
            f"{p.vendor}/{p.model}": {
                "input_per_million": 0.0,
                "cached_input_per_million": 0.0,
                "output_per_million": 0.0,
            }
            for p in providers
        },
    }


def frozen_one_task(providers: tuple[FakeProvider, FakeProvider]) -> dict[str, Any]:
    core = build_freeze_core(
        n_tasks=1, constitution_subset=1, seed=17, timeout=2,
        cost_cap_usd=10.0, per_call_reserve_usd=1.0,
        price_table=price_table(*providers), provider_list=providers,
        provider_caps_usd={p.vendor: 10.0 for p in providers},
        cli_versions={f"{p.vendor}/{p.model}": {"exit_code": 0, "stdout": "fake 1"}
                      for p in providers},
        runtime_bindings={
            f"{p.vendor}/{p.model}": {"test_runtime_binding": p.vendor}
            for p in providers
        },
    )
    # Unit-test freezes deliberately use fake providers; live ``make_freeze``
    # additionally requires the real post-hardening canary receipt.
    return {
        "freeze_sha256": provider_module.digest(core), "frozen": core,
        "created_utc": "test", "created_from_git_commit": None,
    }


def test_complete_mocked_feasibility_schedule_is_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers = (
        FakeProvider("anthropic", "fake-a"),
        FakeProvider("openai", "fake-b"),
    )
    freeze = frozen_one_task(providers)
    monkeypatch.setattr(run_module, "rebuild_live_freeze_core", lambda frozen, _: frozen)
    monkeypatch.setattr(
        run_module, "verify_freeze_committed_and_pushed",
        lambda *_: {"freeze_commit": "a" * 40, "network_remote_tip_at_start": "a" * 40},
    )
    monkeypatch.setattr(run_module, "verify_provider_runtime_binding", lambda *_: None)
    monkeypatch.setattr(run_module, "validate_canary_preflight", lambda *_: None)
    run_dir = tmp_path / "run"
    seal = run_study(
        freeze_doc=freeze, provider_list=providers, output_dir=run_dir,
    )
    assert seal["structural_semantic_integrity_valid"] is True
    assert not (run_dir / "summary.json").exists()
    monkeypatch.setattr(
        score_module, "verify_cohort_seal_committed_and_pushed",
        lambda *_: {
            "freeze_commit": "a" * 40, "seal_commit": "b" * 40,
            "network_remote_tip_at_start": "a" * 40,
            "network_remote_tip": "c" * 40,
        },
    )
    (run_dir / "summary.json").write_text("{}\n")
    with pytest.raises(ValueError, match="orphan summary"):
        score_module.score_run(run_dir)
    (run_dir / "summary.json").unlink()
    summary = score_module.score_run(run_dir)

    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    core_artifacts = [e for e in events if e.get("kind") == "artifact"
                      and e.get("module") == "core"]
    assert {e["artifact_type"] for e in core_artifacts} == {
        "natural", "clean", "seeded", "ambiguous",
    }
    assert len(core_artifacts) == 8  # four strata × two generator vendors

    c2_calls = [e for e in events if e.get("kind") == "call_complete"
                and e.get("role") == "auditor"
                and e["metadata"].get("constitution") == "C2"]
    assert len(c2_calls) == 48  # 8 artefacts × two auditors × three repeats
    assert {e["metadata"]["repeat"] for e in c2_calls} == {0, 1, 2}

    decisions = [e for e in events if e.get("kind") == "audit_decision"]
    assert {e["dcl_mode"] for e in decisions} == {
        "D0_OFF", "D1_ONLY", "D2_COMBINED_BLIND",
    }
    loops = [e for e in events if e.get("kind") == "whole_loop_end"]
    assert len(loops) == 4  # seeded output from two generators × same/cross branches
    assert {e["assignment"] for e in loops} == {"same", "cross"}
    assert all(e["final_acceptable"] == 1 for e in loops)
    assert all(e["revisions"] == 1 for e in loops)

    text_arms = [e for e in events if e.get("kind") == "defensive_loop_end"]
    assert {e["policy"] for e in text_arms} == {"P0", "P1", "P2"}
    code_arms = [e for e in events if e.get("kind") == "defensive_code_loop_end"]
    assert {e["policy"] for e in code_arms} == {"P0", "P1", "P2"}
    assert all(e["final_held_out_correct"] for e in code_arms)

    ledger = [e for e in events if e.get("kind") == "ledger_outcome"]
    assert len(ledger) == 12  # two episodes × 3 surfaces × 2 configurations
    assert all(e["review_schema_valid"] is True for e in ledger)
    assert all(set(e["review"]) == set(LEDGER_REVIEW_SCHEMA["required"]) for e in ledger)
    assert all(e["review"]["insufficient_evidence"] is True
               for e in ledger if e["interface"] == "E0")
    assert all(e["review"]["insufficient_evidence"] is False
               for e in ledger if e["interface"] in {"E1", "E2"})
    seen = Counter((e["episode_id"], e["reviewer_session"]) for e in ledger)
    assert set(seen.values()) == {1}
    for episode_id in {e["episode_id"] for e in ledger}:
        for vendor in {e["reviewer_vendor"] for e in ledger}:
            assert {e["interface"] for e in ledger
                    if e["episode_id"] == episode_id and e["reviewer_vendor"] == vendor} \
                   == {"E0", "E1", "E2"}

    assert summary["claim_status"].startswith("execution-feasibility")
    assert summary["schedule_finished"] is True
    assert summary["journal_integrity"]["hash_chain_validated"] is True
    assert summary["journal_integrity"]["final_event_sha256"]
    assert summary["whole_loop_seeded_same_cross"]["n_seeded_branches"] == 4
    assert summary["core_2x2_and_ablations"]["finding_location_match_proxy"]
    ledger_summary = summary["ledger_proxy_pilot"]["interfaces"]
    assert ledger_summary["E0"]["insufficient_evidence_rate"] == 1.0
    assert ledger_summary["E1"]["insufficient_evidence_rate"] == 0.0
    assert ledger_summary["E2"]["insufficient_evidence_rate"] == 0.0
    assert {ledger_summary[x]["n_schema_valid_review_values"] for x in ("E0", "E1", "E2")} == {4}
    assert {ledger_summary[x]["n_missing_or_invalid_review_values"]
            for x in ("E0", "E1", "E2")} == {0}
    before = (run_dir / "events.jsonl").read_bytes()
    second_seal = run_study(
        freeze_doc=freeze, provider_list=providers, output_dir=run_dir,
    )
    assert (run_dir / "events.jsonl").read_bytes() == before
    assert second_seal == seal
    second = score_module.score_run(run_dir)
    assert second["event_counts"] == summary["event_counts"]

    tampered = events
    tampered[1]["kind"] = "changed"
    (run_dir / "events.jsonl").write_text(
        "".join(json.dumps(e, sort_keys=True) + "\n" for e in tampered)
    )
    with pytest.raises(ValueError, match="invalid event hash"):
        __import__("experiment.v4.feasibility.score", fromlist=["score_run"]).score_run(run_dir)


def test_invalid_ledger_review_is_persisted_as_null(tmp_path: Path) -> None:
    invalid_value = {
        "accept": False, "accept_probability": 0.2,
        "tamper_detected": False, "tamper_probability": 0.1,
        "origin_round": 1, "first_defective_round": 0,
        "rule_version": "v4-feasibility-C2", "insufficient_evidence": True,
        "operator_note": "must never enter the derived outcome",
    }
    assert run_module.validated_ledger_review(invalid_value) is None
    assert run_module.validated_ledger_review({
        key: (True if key == "origin_round" else value)
        for key, value in invalid_value.items() if key != "operator_note"
    }) is None
    valid_value = {key: value for key, value in invalid_value.items()
                   if key != "operator_note"}
    assert run_module.validated_ledger_review(valid_value) == valid_value
    for field in ("accept_probability", "tamper_probability"):
        for bad_probability in (-0.01, 1.01, float("inf"), float("nan"), True):
            candidate = dict(valid_value)
            candidate[field] = bad_probability
            assert run_module.validated_ledger_review(candidate) is None
    bad_first_round = dict(valid_value)
    bad_first_round["first_defective_round"] = False
    assert run_module.validated_ledger_review(bad_first_round) is None

    class InvalidLedgerCalls:
        def call(self, **_kwargs):
            return {
                "status": "valid", "response": {"value": invalid_value},
                "elapsed_seconds": 0.01,
            }

    providers = (
        FakeProvider("anthropic", "fake-a"),
        FakeProvider("openai", "fake-b"),
    )
    journal = Journal(tmp_path / "events.jsonl", "c" * 64)
    run_module.run_ledger(journal, InvalidLedgerCalls(), (TASKS[0],), providers, seed=17)
    outcomes = [e for e in journal.events if e.get("kind") == "ledger_outcome"]
    assert len(outcomes) == 12
    assert all(e["status"] == "invalid_review_schema" for e in outcomes)
    assert all(e["review_schema_valid"] is False for e in outcomes)
    assert all(e["review"] is None for e in outcomes)
    assert "operator_note" not in json.dumps(outcomes)
    score_module = __import__("experiment.v4.feasibility.score", fromlist=["_ledger_summary"])
    invalid_cell = score_module._ledger_summary(journal.events)[
        "by_attack_and_interface_ITT"
    ]["none"]["E0"]
    assert invalid_cell["accept_probability_brier_ITT"] == 1.0
    assert invalid_cell["decision_time_capped_seconds"]["mean"] == 300.0
    assert invalid_cell["raw_latency_seconds"]["mean"] == 0.01


def test_seven_ledger_attacks_and_attack_interface_itt_scoring(tmp_path: Path) -> None:
    class FixedLedgerCalls:
        def call(self, **kwargs):
            return {
                "status": "valid",
                "response": {"value": {
                    "accept": False, "accept_probability": 0.25,
                    "tamper_detected": True, "tamper_probability": 0.75,
                    "origin_round": 1, "first_defective_round": 0,
                    "rule_version": "v4-feasibility-C2",
                    "insufficient_evidence": "\"interface\":\"E0\"" in kwargs["prompt"],
                }},
                "elapsed_seconds": 2.5,
            }

    providers = (
        FakeProvider("anthropic", "fake-a"),
        FakeProvider("openai", "fake-b"),
    )
    journal = Journal(tmp_path / "seven.jsonl", "d" * 64)
    run_module.run_ledger(journal, FixedLedgerCalls(), TASKS, providers, seed=17)
    truths = [e for e in journal.events if e.get("kind") == "ledger_truth"]
    outcomes = [e for e in journal.events if e.get("kind") == "ledger_outcome"]
    expected_attacks = {
        "none", "stale_receipt", "wrong_commit", "changed_constitution",
        "missing_round", "altered_report", "unsupported_identity",
    }
    assert len(truths) == 7
    assert {e["truth"]["attack"] for e in truths} == expected_attacks
    assert len(outcomes) == 42  # seven episodes × three interfaces × two configurations
    assert all(e["correct_first_defective"] == 1 for e in outcomes)
    assert all(e["correct_rounds"] == 1 for e in outcomes)

    score_module = __import__("experiment.v4.feasibility.score", fromlist=["_ledger_summary"])
    summary = score_module._ledger_summary(journal.events)
    assert summary["attack_counts"] == {attack: 1 for attack in sorted(expected_attacks)}
    ledger_contrast = summary["episode_clustered_proxy_contrasts"]["correct_accept"][
        "E2_minus_E0"
    ]
    assert ledger_contrast["cluster_field"] == "episode_id"
    assert ledger_contrast["n_clusters"] == 7
    matrix = summary["by_attack_and_interface_ITT"]
    none_e0 = matrix["none"]["E0"]
    stale_e0 = matrix["stale_receipt"]["E0"]
    assert none_e0["n_proxy_reviews_ITT"] == 2
    assert none_e0["accept_accuracy_ITT"] == 0.0
    assert none_e0["tamper_accuracy_ITT"] == 0.0
    assert none_e0["origin_round_accuracy_ITT"] == 1.0
    assert none_e0["first_defective_round_accuracy_ITT"] == 1.0
    assert none_e0["round_pair_accuracy_ITT"] == 1.0
    assert none_e0["rule_accuracy_ITT"] == 1.0
    assert none_e0["insufficient_evidence_rate_ITT"] == 1.0
    assert none_e0["accept_probability_brier_ITT"] == pytest.approx(0.5625)
    assert none_e0["tamper_probability_brier_ITT"] == pytest.approx(0.5625)
    assert none_e0["raw_latency_seconds"]["mean"] == 2.5
    assert none_e0["decision_time_capped_seconds"]["mean"] == 300.0
    assert stale_e0["accept_accuracy_ITT"] == 1.0
    assert stale_e0["tamper_accuracy_ITT"] == 1.0
    assert stale_e0["accept_probability_brier_ITT"] == pytest.approx(0.0625)
    assert stale_e0["tamper_probability_brier_ITT"] == pytest.approx(0.0625)
    assert stale_e0["decision_time_capped_seconds"]["mean"] == 2.5
    assert matrix["stale_receipt"]["E1"]["insufficient_evidence_rate_ITT"] == 0.0

    altered, _ = run_module._ledger_episode(TASKS[0], 5)
    for report_event in (altered["E1"]["messages"][1], altered["E2"]["events"][1]):
        assert run_module.digest(report_event["audit_report"]) != report_event["report_sha256"]
    unsupported, _ = run_module._ledger_episode(TASKS[0], 6)
    for identity_event in (unsupported["E1"]["messages"][2],
                           unsupported["E2"]["events"][2]):
        attestation = identity_event["identity_attestation"]
        assert identity_event["presented_provider_identity"] \
               != attestation["attested_provider_identity"]
        assert attestation["claim_sha256"] == run_module.digest({
            "provider_identity": attestation["attested_provider_identity"],
            "artifact_sha256": attestation["artifact_sha256"],
        })


def test_generated_code_is_never_run_in_parent_and_fails_closed() -> None:
    spec = CODE_TASKS[0]
    valid = {"code": "def final_change(values):\n    return abs(values[-1] - values[-2])",
             "explanation": "formula", "checks": [], "limitations": []}
    assert evaluate_code_artifact(spec, valid)["held_out_correct"] is True

    started = time.monotonic()
    hanging = {"code": "def final_change(values):\n    while True:\n        pass",
               "explanation": "", "checks": [], "limitations": []}
    report = evaluate_code_artifact(spec, hanging)
    assert time.monotonic() - started < 1.0
    assert report["static_ok"] is False
    assert any("While" in error for error in report["errors"])

    importing = {"code": "import os\ndef final_change(values):\n    return 0",
                 "explanation": "", "checks": [], "limitations": []}
    assert any("Import" in error for error in evaluate_code_artifact(spec, importing)["errors"])


def test_usage_sums_every_model_entry_and_claude_list_cost_wins() -> None:
    response = {
        "usage": {
            "input_tokens": 10, "output_tokens": 4,
            "cache_creation_input_tokens": 99,
        },
        "model_usage": {
            "main": {
                "inputTokens": 10, "outputTokens": 4,
                "cacheReadInputTokens": 2, "cacheCreationInputTokens": 5,
                "reasoningTokens": 1,
            },
            "helper": {
                "inputTokens": 3, "outputTokens": 2,
                "cachedInputTokens": 1, "cache_write_input_tokens": 2,
                "reasoning_output_tokens": 3,
            },
        },
        "list_cost_usd": 0.123,
    }
    usage = normalise_usage(response)
    assert usage == {
        "available": True,
        "billable_fields_complete": True,
        "invalid_nonfinite": False,
        "invalid_token_fields": False,
        "provenance": "sum_of_model_usage_entries",
        "source_entry_count": 2,
        "input_tokens": 13,
        "output_tokens": 6,
        "cached_input_tokens": 3,
        "cache_creation_input_tokens": 5,
        "cache_write_input_tokens": 2,
        "reasoning_tokens": 4,
    }
    provider = FakeProvider("anthropic", "fake-a")
    cost, source = call_cost(provider, response, usage, price_table(provider))
    assert cost == 0.123
    assert source == "provider_list_cost_usd"


def test_anthropic_usage_without_provider_total_makes_cost_unknown_and_stops(
    tmp_path: Path,
) -> None:
    class MissingTotalWithHelper(FakeProvider):
        def call(self, **kwargs):
            response = super().call(**kwargs)
            response.pop("list_cost_usd", None)
            response["model_usage"] = {
                self.model: {"inputTokens": 10, "outputTokens": 5},
                "claude-haiku-helper": {"inputTokens": 2, "outputTokens": 1},
            }
            return response

    provider = MissingTotalWithHelper("anthropic", "claude-sonnet-4-6")
    other = FakeProvider("openai", "b")
    journal = Journal(tmp_path / "helper-cost.jsonl", "7" * 64)
    calls = CallRunner(
        journal, price_table(provider, other), cap=5, reserve=0.1, timeout=1,
        provider_caps={"anthropic": 5, "openai": 5},
    )
    first = calls.call(
        call_id="helper", provider=provider, prompt='"interface":"E0"',
        schema=LEDGER_REVIEW_SCHEMA, role="ledger_proxy_reviewer", metadata={},
    )
    assert first["cost_usd"] is None
    assert first["cost_source"] == "unavailable_anthropic_provider_total"
    blocked = calls.call(
        call_id="later", provider=other, prompt='"interface":"E0"',
        schema=LEDGER_REVIEW_SCHEMA, role="ledger_proxy_reviewer", metadata={},
    )
    assert blocked["status"] == "budget_unverifiable"
    assert blocked["provider_invoked"] is False


def test_codex_usage_aliases_do_not_double_charge_reasoning_or_cache_write() -> None:
    provider = FakeProvider("openai", "fake-b")
    response = {
        "usage": {
            "input_tokens": 100, "output_tokens": 10,
            "cached_input_tokens": 20, "cache_write_input_tokens": 7,
            "reasoning_output_tokens": 40,
        },
    }
    usage = normalise_usage(response)
    assert usage["cached_input_tokens"] == 20
    assert usage["cache_write_input_tokens"] == 7
    assert usage["cache_creation_input_tokens"] == 0
    assert usage["reasoning_tokens"] == 40
    prices = {
        "currency": "USD",
        "prices": {
            "openai/fake-b": {
                "input_per_million": 2.0,
                "cached_input_per_million": 1.0,
                "output_per_million": 4.0,
            },
        },
    }
    cost, source = call_cost(provider, response, usage, prices)
    assert cost == 0.00022  # 80 input + 20 cached input + 10 output; no add-ons.
    assert source == "frozen_token_price_table"


@pytest.mark.parametrize(
    "usage_payload",
    [
        {"input_tokens": -1, "output_tokens": 2},
        {"input_tokens": 1.5, "output_tokens": 2},
        {"input_tokens": 3, "inputTokens": 4, "output_tokens": 2},
        {"input_tokens": float("nan"), "output_tokens": 2},
    ],
    ids=("negative", "fractional", "conflicting-alias", "nonfinite"),
)
def test_invalid_usage_telemetry_never_produces_a_cost(
    usage_payload: dict[str, Any],
) -> None:
    provider = FakeProvider("openai", "fake-b")
    response = {"usage": usage_payload}
    usage = normalise_usage(response)
    assert usage["available"] is False
    cost, source = call_cost(provider, response, usage, price_table(provider))
    assert cost is None
    assert source == "invalid_usage_telemetry"


def test_summary_aggregates_every_normalised_usage_field() -> None:
    usage = normalise_usage({
        "usage": {
            "input_tokens": 11, "output_tokens": 5,
            "cache_read_input_tokens": 3,
            "cache_creation_input_tokens": 2,
            "cache_write_input_tokens": 1,
            "reasoning_output_tokens": 4,
        },
    })
    expected_tokens = {
        "input_tokens": 11, "output_tokens": 5,
        "cached_input_tokens": 3,
        "cache_creation_input_tokens": 2,
        "cache_write_input_tokens": 1,
        "reasoning_tokens": 4,
    }
    events = [
        {"kind": "call_scheduled", "call_id": "one"},
        {
            "kind": "call_complete", "call_id": "one",
            "provider": "openai", "role": "generator", "status": "valid",
            "provider_invoked": True, "usage": usage, "cost_usd": 0.01,
            "cost_source": "frozen_token_price_table", "identity_verified": None,
            "elapsed_seconds": 0.2,
            "metadata": {"module": "defensive_text", "policy": "P0"},
        },
    ]
    execution = score_module._execution_summary(events)
    assert execution["token_totals"] == expected_tokens
    assert execution["usage_available_provider_invocations"] == 1
    assert execution["usage_unavailable_provider_invocations"] == 0
    assert execution["usage_provenance"] == {"top_level_usage": 1}
    cell = execution["by_provider_and_role"]["openai/generator"]
    assert {field: cell[field] for field in expected_tokens} == expected_tokens
    assert cell["usage_available_provider_invocations"] == 1
    assert cell["usage_unavailable_provider_invocations"] == 0
    assert cell["usage_provenance"] == {"top_level_usage": 1}
    policy = score_module._policy_resources(events, "defensive_text")["P0"]
    assert {field: policy[field] for field in expected_tokens} == expected_tokens


def test_unknown_cost_blocks_entire_cohort_and_keeps_itt_records(tmp_path: Path) -> None:
    class UnknownCost(FakeProvider):
        def call(self, **kwargs):
            return {
                "status": "valid", "value": {},
                "vendor": self.vendor, "model_requested": self.model,
                "cli": self.cli, "role": kwargs["role"], "elapsed_seconds": 0.01,
                "usage": {"input_tokens": 10, "output_tokens": 5},
                "models_observed": [self.model],
                "model_usage": {self.model: {"inputTokens": 10, "outputTokens": 5}},
                "prompt_sha256": provider_module.prompt_digest(kwargs["prompt"]),
                "schema_sha256": provider_module.digest(kwargs["schema"]),
            }

    other_dispatches: list[dict[str, Any]] = []

    class MustNotDispatch(FakeProvider):
        def call(self, **kwargs):
            other_dispatches.append(kwargs)
            return super().call(**kwargs)

    a = UnknownCost("anthropic", "fake-a")
    b = MustNotDispatch("openai", "fake-b")
    prices = price_table(a, b)
    journal = Journal(tmp_path / "events.jsonl", "f" * 64)
    calls = CallRunner(journal, prices, cap=5, reserve=0.1, timeout=1,
                       provider_caps={"anthropic": 5, "openai": 5})
    first = calls.call(call_id="a1", provider=a, prompt="x", schema={}, role="x", metadata={})
    assert first["cost_usd"] is None
    same_vendor = calls.call(
        call_id="a2", provider=a, prompt="x", schema={}, role="x", metadata={},
    )
    other_vendor = calls.call(
        call_id="b1", provider=b, prompt="x", schema=LEDGER_REVIEW_SCHEMA,
        role="ledger_proxy_reviewer", metadata={},
    )

    for blocked in (same_vendor, other_vendor):
        assert blocked["status"] == "budget_unverifiable"
        assert blocked["provider_invoked"] is False
        assert blocked["cost_unverifiable"] is True
        assert blocked["budget_scope"] == "combined_cohort"
        assert blocked["blocking_unknown_cost_providers"] == ["anthropic"]
    assert other_dispatches == []
    assert journal.get("schedule:b1") is not None
    assert journal.get("complete:b1") == other_vendor


@pytest.mark.parametrize(
    "unsafe_number", [float("nan"), float("inf"), 10 ** 5000],
    ids=("nan", "infinity", "oversized-integer"),
)
def test_nonfinite_or_unserialisable_provider_numbers_fail_closed_without_breaking_journal(
    tmp_path: Path, unsafe_number: Any,
) -> None:
    class UnsafeNumberProvider(FakeProvider):
        def call(self, **kwargs):
            return {
                "status": "valid",
                "value": {
                    "result": unsafe_number, "unit": "percentage_points",
                    "method": "unsafe", "evidence": ["csv:revenue", "csv:cost"],
                    "checks": [], "limitations": [],
                },
                "usage": {"input_tokens": float("nan"), "output_tokens": 1},
                "models_observed": [self.model],
                "prompt_sha256": provider_module.prompt_digest("x"),
                "schema_sha256": provider_module.digest(ARTIFACT_SCHEMA),
            }

    provider = UnsafeNumberProvider("openai", "unsafe")
    journal_path = tmp_path / "unsafe-number.jsonl"
    journal = Journal(journal_path, "9" * 64)
    calls = CallRunner(
        journal, price_table(provider), cap=5, reserve=0.1, timeout=1,
        provider_caps={"openai": 5},
    )
    completion = calls.call(
        call_id="unsafe-number", provider=provider, prompt="x",
        schema=ARTIFACT_SCHEMA, role="generator", metadata={"module": "test"},
    )
    assert completion["status"] == "invalid_schema"
    assert completion["cost_usd"] is None
    assert completion["usage"]["available"] is False
    assert completion["usage"]["invalid_nonfinite"] is True
    assert completion["response"]["nonfinite_values_redacted"] is True
    assert completion["response"]["local_schema_validation"]["valid"] is False
    assert len([event for event in journal.events if event["kind"] == "call_complete"]) == 1

    # The persisted JSON and chain remain readable even when Python itself
    # refuses to render the original integer as a decimal string.
    reloaded = Journal(journal_path, "9" * 64)
    assert reloaded.get("complete:unsafe-number") == completion
    later = calls.call(
        call_id="later", provider=provider, prompt="x",
        schema=ARTIFACT_SCHEMA, role="generator", metadata={"module": "test"},
    )
    assert later["status"] == "budget_unverifiable"
    assert later["provider_invoked"] is False


def test_adapter_timeout_completion_retains_frozen_prompt_and_schema_hashes(
    tmp_path: Path,
) -> None:
    class RaisingTimeout(FakeProvider):
        def call(self, **kwargs):
            raise subprocess.TimeoutExpired(cmd="fake", timeout=1)

    provider = RaisingTimeout("openai", "timeout")
    journal = Journal(tmp_path / "timeout.jsonl", "8" * 64)
    calls = CallRunner(
        journal, price_table(provider), cap=5, reserve=0.1, timeout=1,
        provider_caps={"openai": 5},
    )
    completion = calls.call(
        call_id="timeout", provider=provider, prompt="exact prompt",
        schema=ARTIFACT_SCHEMA, role="generator", metadata={"module": "test"},
    )
    schedule = journal.get("schedule:timeout")
    assert schedule is not None
    assert completion["status"] == "timeout"
    assert completion["response"]["prompt_sha256"] == schedule["prompt_sha256"]
    assert completion["response"]["schema_sha256"] == schedule["schema_sha256"]


def test_nonfinite_and_oversized_numeric_freeze_inputs_are_rejected() -> None:
    providers = (FakeProvider("anthropic", "a"), FakeProvider("openai", "b"))
    base = dict(
        n_tasks=1, constitution_subset=1, seed=17, timeout=2,
        cost_cap_usd=10.0, per_call_reserve_usd=1.0,
        price_table=price_table(*providers), provider_list=providers,
        provider_caps_usd={p.vendor: 10.0 for p in providers},
        cli_versions={f"{p.vendor}/{p.model}": {"exit_code": 0} for p in providers},
        runtime_bindings={f"{p.vendor}/{p.model}": {"test": p.vendor} for p in providers},
    )
    for unsafe in (float("nan"), float("inf"), 10 ** 5000):
        with pytest.raises(ValueError):
            build_freeze_core(**{**base, "cost_cap_usd": unsafe})
        prices = json.loads(json.dumps(base["price_table"]))
        prices["prices"]["openai/b"]["input_per_million"] = unsafe
        with pytest.raises(ValueError):
            build_freeze_core(**{**base, "price_table": prices})


def test_secret_output_is_discarded_and_identity_drift_stops_dispatch(tmp_path: Path) -> None:
    class SecretProvider(FakeProvider):
        def call(self, **kwargs):
            return {
                "status": "valid", "value": {"leak": "sk-ant-abcdefghijklmnopqrstuvwxyz"},
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "list_cost_usd": 0.01, "models_observed": [self.model],
            }

    secret = SecretProvider("anthropic", "a")
    other = FakeProvider("openai", "b")
    journal = Journal(tmp_path / "secret.jsonl", "a" * 64)
    calls = CallRunner(journal, price_table(secret, other), cap=5, reserve=0.1, timeout=1,
                       provider_caps={"anthropic": 5, "openai": 5})
    leaked = calls.call(call_id="leak", provider=secret, prompt="x", schema={}, role="x",
                        metadata={})
    assert leaked["status"] == "secret_output_quarantined"
    persisted = (tmp_path / "secret.jsonl").read_text()
    assert "sk-ant-abcdefghijklmnopqrstuvwxyz" not in persisted
    assert leaked["response"]["secret_pattern_labels"] == ["anthropic_key"]
    stopped = calls.call(call_id="later", provider=other, prompt="x", schema={}, role="x",
                         metadata={})
    assert stopped["status"] == "safety_stop_blocked"

    class DriftProvider(FakeProvider):
        def call(self, **kwargs):
            return {"status": "valid", "value": {},
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                    "models_observed": ["unexpected-model"]}

    drift = DriftProvider("openai", "wanted-model")
    journal2 = Journal(tmp_path / "drift.jsonl", "b" * 64)
    calls2 = CallRunner(journal2, price_table(drift), cap=5, reserve=0.1, timeout=1,
                        provider_caps={"openai": 5})
    event = calls2.call(call_id="drift", provider=drift, prompt="x", schema={}, role="x",
                        metadata={})
    assert event["status"] == "model_identity_drift"
    assert event["identity_verified"] is False


def test_provider_event_violation_stops_every_later_dispatch(tmp_path: Path) -> None:
    dispatches: list[str] = []

    class PolicyViolationProvider(FakeProvider):
        def call(self, **kwargs):
            dispatches.append(self.vendor)
            return {
                "status": "provider_event_policy_violation", "value": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "models_observed": [],
                "event_policy_violations": [{"reason": "unsafe test event"}],
            }

    class MustNotDispatch(FakeProvider):
        def call(self, **kwargs):  # pragma: no cover - safety gate must win
            dispatches.append(self.vendor)
            return super().call(**kwargs)

    unsafe = PolicyViolationProvider("openai", "unsafe")
    other = MustNotDispatch("anthropic", "other")
    journal = Journal(tmp_path / "event-policy.jsonl", "d" * 64)
    calls = CallRunner(
        journal, price_table(unsafe, other), cap=5, reserve=0.1, timeout=1,
        provider_caps={"openai": 5, "anthropic": 5},
    )
    first = calls.call(
        call_id="unsafe", provider=unsafe, prompt="x", schema={}, role="x", metadata={},
    )
    assert first["status"] == "provider_event_policy_violation"
    assert first["provider_invoked"] is True
    for call_id, provider in (("same-later", unsafe), ("other-later", other)):
        stopped = calls.call(
            call_id=call_id, provider=provider, prompt="x", schema={}, role="x", metadata={},
        )
        assert stopped["status"] == "safety_stop_blocked"
        assert stopped["provider_invoked"] is False
    assert dispatches == ["openai"]


def test_anthropic_server_tool_use_is_quarantined_and_stops_other_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    outer = {
        "structured_output": {"raw": "danger-marker"},
        "usage": {
            "input_tokens": 1, "output_tokens": 1,
            "server_tool_use": {"web_search_requests": 1},
        },
        "modelUsage": {"a": {"inputTokens": 1, "outputTokens": 1}},
        "total_cost_usd": 0.01,
        "uuid": "request-1",
    }
    monkeypatch.setattr(
        provider_module.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=json.dumps(outer), stderr="",
        ),
    )
    fake_cli = tmp_path / "claude"
    fake_cli.write_bytes(b"")
    monkeypatch.setattr(provider_module, "resolved_cli_path", lambda _: fake_cli)
    anthropic = provider_module.Provider("anthropic", "a", "claude")

    other_dispatches: list[bool] = []

    class MustNotDispatch(FakeProvider):
        def call(self, **kwargs):  # pragma: no cover - safety gate must win
            other_dispatches.append(True)
            return super().call(**kwargs)

    other = MustNotDispatch("openai", "b")
    journal = Journal(tmp_path / "anthropic-tool.jsonl", "e" * 64)
    calls = CallRunner(
        journal, price_table(anthropic, other), cap=5, reserve=0.1, timeout=1,
        provider_caps={"anthropic": 5, "openai": 5},
    )
    violation = calls.call(
        call_id="tool", provider=anthropic, prompt="x", schema={}, role="x", metadata={},
    )
    assert violation["status"] == "provider_event_policy_violation"
    assert violation["response"]["raw_envelope"]["discarded"] is True
    assert violation["response"]["event_policy_violations"] == [{
        "reason": "anthropic_server_tool_use_nonzero",
        "server_tool_names": ["web_search_requests"],
    }]
    assert "danger-marker" not in (tmp_path / "anthropic-tool.jsonl").read_text()
    stopped = calls.call(
        call_id="other", provider=other, prompt="x", schema={}, role="x", metadata={},
    )
    assert stopped["status"] == "safety_stop_blocked"
    assert stopped["provider_invoked"] is False
    assert other_dispatches == []


def test_freeze_and_call_plan_are_fail_closed() -> None:
    providers = (FakeProvider("anthropic", "a"), FakeProvider("openai", "b"))
    freeze = frozen_one_task(providers)
    assert validate_freeze_document(freeze, freeze["frozen"]) == freeze["freeze_sha256"]
    changed = json.loads(json.dumps(freeze["frozen"]))
    changed["design"]["primary_audit_repeats"] = 2
    with pytest.raises(RuntimeError, match="differ"):
        validate_freeze_document(freeze, changed)
    assert planned_calls(6, 2)["maximum_total"] == 610
    assert freeze["frozen"]["budget"]["maximum_model_calls"] == 610
    assert freeze["frozen"]["design"]["ledger_decision_time_cap_seconds"] == 300
    assert freeze["frozen"]["claim_status"].startswith("execution-feasibility")
    assert set(freeze["frozen"]["protocol_document_hashes"]) == {
        "experiment/v4/FEASIBILITY-REGISTRATION.md",
        "experiment/v4/FEASIBILITY-AMENDMENT-1.md",
        "experiment/v4/feasibility/CANARY-RECEIPT.json",
    }
    assert set(freeze["frozen"]["provider_runtime_bindings"]) == {
        "anthropic/a", "openai/b",
    }
    assert "enforce_git_freeze" not in inspect.signature(run_study).parameters


def test_prompt_hash_is_raw_utf8_across_freeze_schedule_and_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = replace(
        TASKS[0],
        brief="第一行：原始提示🙂\nsecond line\r\n第三行",
    )
    monkeypatch.setattr(run_module, "TASKS", (task,))
    anthropic = provider_module.Provider("anthropic", "a", "fake-claude")
    openai = provider_module.Provider("openai", "b", "fake-codex")
    provider_list = (anthropic, openai)
    bindings = {
        f"{provider.vendor}/{provider.model}": {"test_binding": provider.vendor}
        for provider in provider_list
    }
    versions = {
        f"{provider.vendor}/{provider.model}": {"exit_code": 0, "stdout": "fake 1"}
        for provider in provider_list
    }
    core = build_freeze_core(
        n_tasks=1, constitution_subset=1, seed=17, timeout=2,
        cost_cap_usd=10.0, per_call_reserve_usd=1.0,
        price_table=price_table(*provider_list), provider_list=provider_list,
        provider_caps_usd={"anthropic": 10.0, "openai": 10.0},
        cli_versions=versions, runtime_bindings=bindings,
    )
    prompt = run_module.generator_prompt(task, "P0")

    def fake_anthropic(self, work, sent_prompt, schema, role, timeout):
        assert sent_prompt == prompt
        return {
            "status": "valid", "value": {},
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "list_cost_usd": 0.01, "models_observed": [self.model],
        }

    monkeypatch.setattr(provider_module.Provider, "_anthropic", fake_anthropic)
    journal = Journal(tmp_path / "events.jsonl", "c" * 64)
    calls = CallRunner(
        journal, price_table(*provider_list), cap=5, reserve=0.1, timeout=1,
        provider_caps={"anthropic": 5, "openai": 5},
    )
    completion = calls.call(
        call_id="unicode", provider=anthropic, prompt=prompt,
        schema=ARTIFACT_SCHEMA, role="generator", metadata={},
    )
    scheduled = journal.get("schedule:unicode")
    assert scheduled is not None

    expected_prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    assert "第一行" in prompt and "\n" in prompt and "🙂" in prompt
    assert core["prompt_hashes"]["rendered_prompt_hash_definition"] == (
        "sha256(raw UTF-8 prompt string); no JSON encoding or newline normalisation"
    )
    assert core["prompt_hashes"]["rendered_generators"][f"{task.task_id}/P0"] \
           == scheduled["prompt_sha256"] \
           == completion["response"]["prompt_sha256"] \
           == expected_prompt_hash
    assert provider_module.digest(prompt) != expected_prompt_hash

    expected_schema_hash = provider_module.digest(ARTIFACT_SCHEMA)
    assert core["schemas"]["artifact"]["sha256"] \
           == scheduled["schema_sha256"] \
           == completion["response"]["schema_sha256"] \
           == expected_schema_hash


def test_audit_prompt_is_stable_across_journal_json_key_reordering() -> None:
    task = TASKS[0]
    artifact = {
        "limitations": [], "checks": ["recomputed"], "evidence": list(task.evidence),
        "method": "mean", "unit": task.unit, "result": task.result,
    }
    journal_roundtrip = json.loads(json.dumps(artifact, sort_keys=True))
    assert list(artifact) != list(journal_roundtrip)
    assert run_module.audit_prompt(task, artifact, "C2") \
           == run_module.audit_prompt(task, journal_roundtrip, "C2")


def test_run_rebuilds_complete_live_core_before_git_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers = (FakeProvider("anthropic", "a"), FakeProvider("openai", "b"))
    freeze = frozen_one_task(providers)
    changed = json.loads(json.dumps(freeze["frozen"]))
    changed["providers"][0]["model"] = "drifted"
    git_checks: list[bool] = []
    monkeypatch.setattr(run_module, "rebuild_live_freeze_core", lambda *_: changed)
    monkeypatch.setattr(
        run_module, "verify_freeze_committed_and_pushed", lambda *_: git_checks.append(True),
    )
    with pytest.raises(RuntimeError, match="differ"):
        run_study(
            freeze_doc=freeze, provider_list=providers, output_dir=tmp_path / "never-created",
        )
    assert git_checks == []
    assert not (tmp_path / "never-created").exists()


def test_cli_version_uses_restricted_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = tmp_path / "cli"
    cli.write_bytes(b"binary")
    captured: dict[str, Any] = {}

    def fake_run(cmd, **kwargs):
        captured.update({"cmd": cmd, **kwargs})
        return SimpleNamespace(returncode=0, stdout="v1\n", stderr="")

    monkeypatch.setattr(run_module, "resolved_cli_path", lambda _: cli)
    monkeypatch.setattr(run_module, "safe_subprocess_env", lambda: {"PATH": "/bound"})
    monkeypatch.setattr(run_module.subprocess, "run", fake_run)
    assert run_module._cli_version(FakeProvider("anthropic", "a"))["stdout"] == "v1"
    assert captured["cmd"] == [str(cli), "--version"]
    assert captured["env"] == {"PATH": "/bound"}


def test_runtime_binding_hashes_paths_bytes_and_route_without_plaintext(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = tmp_path / "codex.js"
    native = tmp_path / "codex-native"
    sandbox_exec = tmp_path / "sandbox-exec"
    cli.write_bytes(b"launcher-v1")
    native.write_bytes(b"native-v1")
    sandbox_exec.write_bytes(b"sandbox-v1")
    monkeypatch.setattr(provider_module, "resolved_cli_path", lambda _: cli)
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module, "CODEX_SANDBOX_EXEC", sandbox_exec)
    effective_features = {
        **{name: True for name in provider_module.CODEX_ENABLED_FEATURES},
        **{name: False for name in provider_module.CODEX_DISABLED_FEATURES},
        "unified_exec": True,
    }
    monkeypatch.setattr(
        provider_module, "codex_effective_feature_state",
        lambda _: dict(sorted(effective_features.items())),
    )
    monkeypatch.setenv("HTTPS_PROXY", "https://private-route.invalid:8443")
    provider = provider_module.Provider("openai", "m", "codex")
    binding = provider_module.provider_runtime_binding(provider)
    rendered = json.dumps(binding, sort_keys=True)
    assert "private-route.invalid" not in rendered
    assert binding["executables"]["cli"]["resolved_path"] == str(cli)
    assert binding["executables"]["cli"]["sha256"] == hashlib.sha256(b"launcher-v1").hexdigest()
    assert binding["executables"]["native"]["sha256"] == hashlib.sha256(b"native-v1").hexdigest()
    assert binding["executables"]["sandbox_exec"]["resolved_path"] == str(sandbox_exec)
    policy = binding["invocation_policy"]
    assert policy["effective_selected_features"] == dict(sorted(effective_features.items()))
    assert policy["residual_enabled_requested_disabled"] == ["unified_exec"]
    assert policy["web_search_cli_flag_present"] is False
    route = binding["security_route_environment"]["variables"]["HTTPS_PROXY"]
    assert route == {
        "present": True,
        "value_sha256": hashlib.sha256(b"https://private-route.invalid:8443").hexdigest(),
    }
    cli.write_bytes(b"launcher-v2")
    with pytest.raises(RuntimeError, match="runtime binding drift"):
        provider_module.verify_provider_runtime_binding(provider, binding)


def test_every_actual_dispatch_rechecks_runtime_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider("openai", "fake-b")
    checks: list[tuple[Any, Any]] = []
    monkeypatch.setattr(
        run_module, "verify_provider_runtime_binding",
        lambda observed, expected: checks.append((observed, expected)),
    )
    journal = Journal(tmp_path / "events.jsonl", "e" * 64)
    calls = CallRunner(
        journal, price_table(provider), cap=5, reserve=0.1, timeout=1,
        provider_caps={"openai": 5},
        provider_runtime_bindings={"openai/fake-b": {"frozen": True}},
    )
    for call_id in ("one", "two"):
        result = calls.call(
            call_id=call_id, provider=provider, prompt='"interface":"E0"',
            schema=LEDGER_REVIEW_SCHEMA, role="ledger_proxy_reviewer", metadata={},
        )
        assert result["provider_invoked"] is True
    assert checks == [(provider, {"frozen": True}), (provider, {"frozen": True})]


def test_codex_feature_probe_freezes_effective_state_and_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = tmp_path / "codex-native"
    native.write_bytes(b"not executed by the mock")
    enabled = set(provider_module.CODEX_ENABLED_FEATURES)
    residual = set(provider_module.CODEX_ALLOWED_RESIDUAL_ENABLED_FEATURES)
    selected = enabled | set(provider_module.CODEX_DISABLED_FEATURES)
    observed = {
        name: name in enabled or name in residual
        for name in selected
    }
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append([str(x) for x in cmd])
        stdout = "\n".join(
            f"{name} stable {'true' if state else 'false'}"
            for name, state in sorted(observed.items())
        )
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(provider_module.subprocess, "run", fake_run)
    assert provider_module.codex_effective_feature_state(native) == dict(sorted(observed.items()))
    assert calls[-1] == [
        str(native), "features", "list", *provider_module.codex_feature_override_args(),
    ]

    observed["shell_tool"] = True
    with pytest.raises(RuntimeError, match="overrides were not effective"):
        provider_module.codex_effective_feature_state(native)


def test_network_upstream_is_required_and_ls_remote_is_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze_path = tmp_path / "FREEZE.json"
    freeze_path.write_text("{}\n")
    monkeypatch.setattr(run_module, "REPO_ROOT", tmp_path)
    freeze_commit = "a" * 40
    remote_tip = "b" * 40
    calls: list[list[str]] = []
    remote_url = {"value": "file:///tmp/not-a-network-remote"}
    committed_freeze = {"value": freeze_path.read_bytes()}

    def completed(cmd, returncode=0, stdout="", stderr=""):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    def fake_run(cmd, **kwargs):
        argv = [str(x) for x in cmd]
        calls.append(argv)
        args = argv[1:]
        if args[:2] == ["replace", "-l"]:
            return completed(argv)
        if args[:2] == ["rev-parse", "--git-common-dir"]:
            return completed(argv, stdout=".git\n")
        if args[:1] == ["ls-files"]:
            return completed(argv)
        if args[:2] == ["status", "--porcelain"]:
            return completed(argv)
        if args[:2] == ["log", "-1"]:
            return completed(argv, stdout=freeze_commit + "\n")
        if args[:1] == ["show"]:
            return completed(argv, stdout=committed_freeze["value"])
        if args[:2] == ["rev-parse", "--verify"]:
            return completed(argv, stdout=remote_tip + "\n")
        if args[:1] == ["merge-base"] or args[:1] == ["cat-file"]:
            return completed(argv)
        if args[:2] == ["symbolic-ref", "--quiet"]:
            return completed(argv, stdout="main\n")
        if args[:3] == ["config", "--get", "branch.main.remote"]:
            return completed(argv, stdout="origin\n")
        if args[:3] == ["config", "--get", "branch.main.merge"]:
            return completed(argv, stdout="refs/heads/main\n")
        if args[:3] == ["remote", "get-url", "origin"]:
            return completed(argv, stdout=remote_url["value"] + "\n")
        if args[:2] == ["ls-remote", "--exit-code"]:
            return completed(argv, stdout=f"{remote_tip}\trefs/heads/main\n")
        raise AssertionError(f"unexpected subprocess: {argv}")

    monkeypatch.setattr(run_module.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="registered GitHub network host"):
        verify_freeze_committed_and_pushed(freeze_path)
    assert not any(cmd[1:3] == ["ls-remote", "--exit-code"] for cmd in calls)

    calls.clear()
    remote_url["value"] = "https://github.com/example/crossaudit.git"
    verify_freeze_committed_and_pushed(freeze_path)
    network_calls = [cmd for cmd in calls if cmd[1:3] == ["ls-remote", "--exit-code"]]
    assert network_calls == [[
        "git", "ls-remote", "--exit-code", remote_url["value"], "refs/heads/main",
    ]]

    calls.clear()
    committed_freeze["value"] = b'{"different":true}\n'
    with pytest.raises(RuntimeError, match="bytes differ from the containing Git commit"):
        verify_freeze_committed_and_pushed(freeze_path)
    assert not any(cmd[1:3] == ["ls-remote", "--exit-code"] for cmd in calls)


def test_provider_commands_enforce_empty_tools_and_no_subprocess(monkeypatch, tmp_path: Path) -> None:
    captured: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(cmd, **kwargs):
        captured.append(([str(x) for x in cmd], kwargs))
        if "claude" in str(cmd[0]):
            stdout = json.dumps({"structured_output": {}, "usage": {}, "modelUsage": {}})
        else:
            stdout = "\n".join([
                json.dumps({"type": "thread.started", "thread_id": "t"}),
                json.dumps({"type": "item.completed", "item": {
                    "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
                    "type": "error",
                    "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
                }}),
                json.dumps({"type": "turn.started"}),
                json.dumps({"type": "item.completed",
                            "item": {"type": "agent_message", "text": "{}"}}),
                json.dumps({"type": "turn.completed",
                            "usage": {"input_tokens": 1, "output_tokens": 1}}),
            ])
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(provider_module.subprocess, "run", fake_run)
    fake_claude = tmp_path / "claude"
    fake_claude.write_bytes(b"mock")
    monkeypatch.setattr(provider_module, "resolved_cli_path", lambda _: fake_claude)
    anthropic = provider_module.Provider("anthropic", "m", "claude")
    anthropic._anthropic(tmp_path, "p", {}, "r", 1)
    anthropic_cmd, anthropic_kwargs = captured[-1]
    assert anthropic_cmd[anthropic_cmd.index("--tools") + 1] == ""
    assert anthropic_cmd[anthropic_cmd.index("--max-budget-usd") + 1] == "1.0"
    assert "--strict-mcp-config" in anthropic_cmd
    assert anthropic_cmd[anthropic_cmd.index("--mcp-config") + 1] == '{"mcpServers":{}}'
    anthropic_system = anthropic_cmd[anthropic_cmd.index("--system-prompt") + 1]
    assert anthropic_system == provider_module.NEUTRAL_SYSTEM_INSTRUCTION
    assert anthropic_kwargs["input"] == "p"

    native = tmp_path / "codex-native"
    native.write_text("")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    openai = provider_module.Provider("openai", "m", "codex")
    openai_response = openai._openai(tmp_path, "p", {}, "r", 1)
    openai_cmd, openai_kwargs = captured[-1]
    assert openai_response["status"] == "valid"
    assert openai_cmd[0] == "/usr/bin/sandbox-exec"
    profile = openai_cmd[openai_cmd.index("-p") + 1]
    assert "(deny process-exec)" in profile
    assert f'(allow process-exec (literal "{native}"))' in profile
    assert openai_cmd[openai_cmd.index("--sandbox") + 1] == "read-only"
    assert "--ephemeral" in openai_cmd
    assert "--ignore-user-config" in openai_cmd
    assert "--ignore-rules" in openai_cmd
    assert "--strict-config" in openai_cmd
    assert "suppress_unstable_features_warning=true" in openai_cmd
    assert "--search" not in openai_cmd
    enabled = {
        openai_cmd[i + 1] for i, value in enumerate(openai_cmd[:-1])
        if value == "--enable"
    }
    disabled = {
        openai_cmd[i + 1] for i, value in enumerate(openai_cmd[:-1])
        if value == "--disable"
    }
    assert enabled == set(provider_module.CODEX_ENABLED_FEATURES)
    assert disabled == set(provider_module.CODEX_DISABLED_FEATURES)
    codex_system, codex_user_prompt = openai_kwargs["input"].split("\n\n", 1)
    assert codex_system == anthropic_system == provider_module.NEUTRAL_SYSTEM_INSTRUCTION
    assert codex_user_prompt == "p"
    for internal_role_word in ("generator", "auditor", "blinded", "evaluation", "defensive"):
        assert internal_role_word not in codex_system.lower()


@pytest.mark.parametrize(
    "unsafe_event",
    [
        {"type": "item.completed", "item": {
            "type": "command_execution", "text": "danger-marker",
        }},
        {"type": "item.completed", "item": {
            "type": "file_change", "text": "danger-marker",
        }},
        {"type": "item.completed", "item": {
            "type": "web_search", "text": "danger-marker",
        }},
        {"type": "item.completed", "item": {
            "type": "mcp_tool_call", "text": "danger-marker",
        }},
        {"type": "item.completed", "item": {
            "type": "error", "text": "danger-marker",
        }},
        {"type": "item.completed", "item": {
            "type": "future_unknown_item", "text": "danger-marker",
        }},
        {"type": "error", "error": {"message": "danger-marker"}},
        {"type": "item.completed", "item": {
            "type": "reasoning", "text": "safe prose", "command": "danger-marker",
        }},
    ],
    ids=(
        "command-execution", "file-change", "web-search", "mcp", "error-item",
        "unknown-item", "top-level-error", "reasoning-with-action-field",
    ),
)
def test_codex_event_allowlist_rejects_actions_errors_and_unknowns(
    unsafe_event: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = "\n".join(json.dumps(event) for event in (
        {"type": "thread.started", "thread_id": "t"},
        {"type": "item.completed", "item": {
            "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
            "type": "error",
            "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
        }},
        {"type": "turn.started"},
        unsafe_event,
        {"type": "item.completed", "item": {
            "type": "agent_message", "text": "{}",
        }},
        {"type": "turn.completed", "usage": {
            "input_tokens": 1, "output_tokens": 1,
        }},
    ))
    monkeypatch.setattr(
        provider_module.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
        ),
    )
    native = tmp_path / "codex-native"
    native.write_bytes(b"")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    response = provider_module.Provider("openai", "m", "codex")._openai(
        tmp_path, "p", {}, "r", 1,
    )
    assert response["status"] == "provider_event_policy_violation"
    assert response["value"] is None
    assert response["event_policy_violations"]
    assert not any(
        row["reason"] == "required_startup_notice_set_mismatch"
        for row in response["event_policy_violations"]
    )
    assert response["raw_envelope"]["discarded"] is True
    assert "danger-marker" not in json.dumps(response, sort_keys=True)


def test_codex_text_only_reasoning_and_agent_message_are_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = "\n".join(json.dumps(event) for event in (
        {"type": "thread.started", "thread_id": "t"},
        {"type": "item.completed", "item": {
            "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
            "type": "error",
            "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
        }},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {
            "id": "reasoning-1", "type": "reasoning", "text": "schema only",
        }},
        {"type": "item.completed", "item": {
            "id": "message-1", "type": "agent_message", "text": '{"ok":true}',
        }},
        {"type": "turn.completed", "usage": {
            "input_tokens": 1, "output_tokens": 1,
        }},
    ))
    monkeypatch.setattr(
        provider_module.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
        ),
    )
    native = tmp_path / "codex-native"
    native.write_bytes(b"")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    response = provider_module.Provider("openai", "m", "codex")._openai(
        tmp_path, "p", {}, "r", 1,
    )
    assert response["status"] == "valid"
    assert response["value"] == {"ok": True}
    assert response["event_policy_violations"] == []
    assert response["allowed_startup_notices"] == [
        "code_mode_host_disabled_fail_closed",
    ]
    assert response["allowed_startup_notice_count"] == 1
    assert response["allowed_startup_notice_message_hashes"] == list(
        provider_module.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES
    )


def test_codex_exact_fail_closed_notice_is_rejected_after_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = "\n".join(json.dumps(event) for event in (
        {"type": "thread.started", "thread_id": "t"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {
            "id": "message-1", "type": "agent_message", "text": '{"ok":true}',
        }},
        {"type": "item.completed", "item": {
            "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
            "type": "error",
            "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
        }},
        {"type": "turn.completed", "usage": {
            "input_tokens": 1, "output_tokens": 1,
        }},
    ))
    monkeypatch.setattr(
        provider_module.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
        ),
    )
    native = tmp_path / "codex-native"
    native.write_bytes(b"")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    response = provider_module.Provider("openai", "m", "codex")._openai(
        tmp_path, "p", {}, "r", 1,
    )
    assert response["status"] == "provider_event_policy_violation"
    assert any(
        row["reason"] == "allowed_startup_notice_wrong_position"
        for row in response["event_policy_violations"]
    )


@pytest.mark.parametrize(
    "mutation,expected_reason",
    (
        ("missing", "required_startup_notice_set_mismatch"),
        ("duplicate", "allowed_startup_notice_wrong_position"),
        ("mutated", "item_type_not_allowlisted"),
        ("mutated-id", "item_type_not_allowlisted"),
        ("extra-field", "item_type_not_allowlisted"),
        ("before-thread", "allowed_startup_notice_wrong_position"),
        ("turn-before-notice", "allowed_startup_notice_wrong_position"),
        ("after-content", "allowed_startup_notice_wrong_position"),
        ("after-turn", "allowed_startup_notice_wrong_position"),
        ("notice-not-followed-by-turn", "required_startup_event_prefix_mismatch"),
    ),
)
def test_codex_startup_notice_contract_is_exact_and_positional(
    mutation: str, expected_reason: str,
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread = {"type": "thread.started", "thread_id": "t"}
    turn = {"type": "turn.started"}
    notice = {"type": "item.completed", "item": {
        "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
        "type": "error",
        "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
    }}
    answer = {"type": "item.completed", "item": {
        "id": "answer", "type": "agent_message", "text": '{"ok":true}',
    }}
    completed = {"type": "turn.completed", "usage": {
        "input_tokens": 1, "output_tokens": 1,
    }}
    cases: dict[str, list[dict[str, Any]]] = {
        "missing": [thread, turn, answer, completed],
        "duplicate": [thread, notice, notice, turn, answer, completed],
        "mutated": [thread, {
            **notice, "item": {**notice["item"], "message": "mutated"},
        }, turn, answer, completed],
        "mutated-id": [thread, {
            **notice, "item": {**notice["item"], "id": "not-item-0"},
        }, turn, answer, completed],
        "extra-field": [thread, {
            **notice, "item": {**notice["item"], "extra": False},
        }, turn, answer, completed],
        "before-thread": [notice, thread, turn, answer, completed],
        "turn-before-notice": [thread, turn, notice, answer, completed],
        "after-content": [thread, turn, answer, notice, completed],
        "after-turn": [thread, turn, completed, notice, answer],
        "notice-not-followed-by-turn": [thread, notice, answer, completed],
    }
    stdout = "\n".join(json.dumps(event) for event in cases[mutation])
    monkeypatch.setattr(
        provider_module.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
        ),
    )
    native = tmp_path / "codex-native"
    native.write_bytes(b"")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    response = provider_module.Provider("openai", "m", "codex")._openai(
        tmp_path, "p", {}, "r", 1,
    )
    assert response["status"] == "provider_event_policy_violation"
    assert any(
        row["reason"] == expected_reason
        for row in response["event_policy_violations"]
    )


@pytest.mark.parametrize(
    "malformed_item",
    (
        [],
        {"id": "missing-text", "type": "agent_message"},
    ),
)
def test_malformed_codex_item_is_policy_violation_and_stops_cohort(
    malformed_item: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = "\n".join(json.dumps(event) for event in (
        {"type": "thread.started", "thread_id": "t"},
        {"type": "item.completed", "item": {
            "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
            "type": "error",
            "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
        }},
        {"type": "turn.started"},
        {"type": "item.completed", "item": malformed_item},
        {"type": "turn.completed", "usage": {
            "input_tokens": 1, "output_tokens": 1,
        }},
    ))
    monkeypatch.setattr(
        provider_module.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
        ),
    )
    native = tmp_path / "codex-native"
    native.write_bytes(b"")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    provider = provider_module.Provider("openai", "m", "codex")
    journal = Journal(tmp_path / "malformed.jsonl", "f" * 64)
    calls = CallRunner(
        journal, price_table(provider), cap=5, reserve=0.1, timeout=1,
        provider_caps={"openai": 5},
    )
    completion = calls.call(
        call_id="malformed", provider=provider, prompt="p", schema={},
        role="generator", metadata={},
    )
    assert completion["status"] == "provider_event_policy_violation"
    assert calls.safety_stop_seen is True


def test_second_process_cannot_open_or_dispatch_same_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A process holding the output flock excludes a complete second runner."""
    run_dir = tmp_path / "locked-run"
    repo = Path(__file__).resolve().parents[1]
    holder = (
        "import sys\n"
        "from pathlib import Path\n"
        "from experiment.v4.feasibility.run import exclusive_output_lock\n"
        "with exclusive_output_lock(Path(sys.argv[1])):\n"
        "    print('LOCKED', flush=True)\n"
        "    sys.stdin.readline()\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo), str(repo / "src"), env.get("PYTHONPATH", "")]
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", holder, str(run_dir)], cwd=repo, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    try:
        ready, _, _ = select.select([proc.stdout], [], [], 5)
        assert ready, proc.stderr.read()
        assert proc.stdout.readline().strip() == "LOCKED"

        @dataclass(frozen=True)
        class NoDispatchProvider(FakeProvider):
            def call(self, **kwargs):  # pragma: no cover - lock must prevent this
                raise AssertionError("provider dispatch occurred while output was locked")

        providers = (
            NoDispatchProvider("anthropic", "fake-a"),
            NoDispatchProvider("openai", "fake-b"),
        )
        freeze = frozen_one_task(providers)
        monkeypatch.setattr(run_module, "rebuild_live_freeze_core", lambda frozen, _: frozen)
        monkeypatch.setattr(
            run_module, "verify_freeze_committed_and_pushed",
            lambda *_: {"freeze_commit": "a" * 40, "network_remote_tip_at_start": "a" * 40},
        )
        monkeypatch.setattr(run_module, "validate_canary_preflight", lambda *_: None)
        with pytest.raises(RuntimeError, match="locked by another feasibility process"):
            run_study(
                freeze_doc=freeze, provider_list=providers, output_dir=run_dir,
            )
        assert not (run_dir / "run_manifest.json").exists()
        assert not (run_dir / "events.jsonl").exists()
    finally:
        if proc.stdin:
            proc.stdin.write("\n")
            proc.stdin.flush()
        proc.communicate(timeout=5)
    assert proc.returncode == 0
