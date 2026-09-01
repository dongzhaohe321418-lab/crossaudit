from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiment.v4.feasibility import providers as provider_module
from experiment.v4.feasibility import run as run_module
from experiment.v4.feasibility.semantics import validate_semantics
from tests.test_feasibility_pilot import FakeProvider, frozen_one_task


def _rewrite(events: list[dict], event_id: str, field: str, value) -> list[dict]:
    changed = copy.deepcopy(events)
    row = next(item for item in changed if item.get("event_id") == event_id)
    row[field] = value
    return changed


def test_semantic_replay_accepts_reloaded_journal_and_rejects_mutations(
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
    output = tmp_path / "semantic-run"
    run_module.run_study(
        freeze_doc=freeze, provider_list=providers, output_dir=output,
    )

    # Reload the sorted JSONL bytes.  Validating only the runner's transient
    # in-memory dictionaries would miss prompt-rendering order dependencies.
    events = [
        json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()
    ]
    core = freeze["frozen"]
    assert validate_semantics(events, core) == []

    # The formal replay independently derives the exact local Codex notice
    # from raw events; the adapter's named summary is not trusted on its own.
    codex_core = copy.deepcopy(core)
    next(row for row in codex_core["providers"] if row["vendor"] == "openai")[
        "cli"
    ] = "codex"
    codex_events = copy.deepcopy(events)
    for row in codex_events:
        if row.get("kind") != "call_complete" or row.get("provider") != "openai" \
                or row.get("provider_invoked") is not True:
            continue
        response = row.get("response")
        if not isinstance(response, dict):
            continue
        response["cli"] = "codex"
        if response.get("status") != "valid":
            continue
        response["allowed_startup_notices"] = list(
            provider_module.CODEX_EXPECTED_STARTUP_NOTICE_IDS
        )
        response["allowed_startup_notice_count"] = 1
        response["allowed_startup_notice_message_hashes"] = list(
            provider_module.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES
        )
        response["raw_envelope"] = [
            {"type": "thread.started", "thread_id": f"t-{row['call_id']}"},
            {"type": "item.completed", "item": {
                "id": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE_ITEM_ID,
                "type": "error",
                "message": provider_module.CODEX_CODE_MODE_FAIL_CLOSED_NOTICE,
            }},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {
                "id": "answer", "type": "agent_message",
                "text": json.dumps(response["value"], sort_keys=True),
            }},
            {"type": "turn.completed", "usage": {
                "input_tokens": 1, "output_tokens": 1,
            }},
        ]
    assert validate_semantics(codex_events, codex_core) == []
    tampered_notice = copy.deepcopy(codex_events)
    target_response = next(
        row["response"] for row in tampered_notice
        if row.get("kind") == "call_complete" and row.get("provider") == "openai"
        and row.get("status") == "valid"
    )
    target_response["allowed_startup_notice_message_hashes"] = ["0" * 64]
    assert any(
        "startup notice summary is not reproducible" in error
        for error in validate_semantics(tampered_notice, codex_core)
    )
    tampered_count = copy.deepcopy(codex_events)
    next(
        row["response"] for row in tampered_count
        if row.get("kind") == "call_complete" and row.get("provider") == "openai"
        and row.get("status") == "valid"
    )["allowed_startup_notice_count"] = 0
    assert any(
        "startup notice summary is not reproducible" in error
        for error in validate_semantics(tampered_count, codex_core)
    )

    natural = next(
        row for row in events
        if row.get("kind") == "artifact" and row.get("module") == "core"
        and row.get("artifact_type") == "natural"
    )
    mutated = copy.deepcopy(events)
    target = next(row for row in mutated if row.get("event_id") == natural["event_id"])
    target["value"]["result"] += 1
    assert any("field 'value'" in error for error in validate_semantics(mutated, core))

    decision = next(row for row in events if row.get("kind") == "audit_decision")
    wrong_gate = "PASS" if decision["gate"] != "PASS" else "BLOCK"
    assert any(
        "field 'gate'" in error
        for error in validate_semantics(
            _rewrite(events, decision["event_id"], "gate", wrong_gate), core,
        )
    )

    ledger = next(row for row in events if row.get("kind") == "ledger_outcome")
    assert any(
        "field 'correct_accept'" in error
        for error in validate_semantics(
            _rewrite(
                events, ledger["event_id"], "correct_accept",
                1 - ledger["correct_accept"],
            ),
            core,
        )
    )

    schedule = next(row for row in events if row.get("kind") == "call_scheduled")
    assert any(
        "prompt_sha256" in error
        for error in validate_semantics(
            _rewrite(events, schedule["event_id"], "prompt_sha256", "0" * 64), core,
        )
    )

    completion = next(
        row for row in events
        if row.get("kind") == "call_complete" and row.get("provider_invoked") is True
        and row.get("status") == "valid"
    )
    mutated = copy.deepcopy(events)
    target = next(row for row in mutated if row.get("event_id") == completion["event_id"])
    target["usage"]["input_tokens"] += 1
    assert any(
        "usage is not derivable" in error for error in validate_semantics(mutated, core)
    )

    mutated = _rewrite(
        events, completion["event_id"], "cost_source", "self_reported_unfrozen_price",
    )
    assert any(
        "cost/source is not derivable" in error
        for error in validate_semantics(mutated, core)
    )

    schedule_positions = [
        index for index, row in enumerate(events) if row.get("kind") == "call_scheduled"
    ]
    reordered = copy.deepcopy(events)
    first, second = schedule_positions[0], schedule_positions[1]
    reordered[first], reordered[second] = reordered[second], reordered[first]
    order_errors = validate_semantics(reordered, core)
    assert "call_scheduled sequence differs from the frozen seeded order" in order_errors
    assert any("synchronously completed" in error for error in order_errors)

    extra = copy.deepcopy(events)
    extra.insert(-1, {
        "event_id": "schedule:foreign", "kind": "call_scheduled",
        "call_id": "foreign", "role": "foreign_role",
        "provider": "anthropic", "model": "fake-a",
        "prompt_sha256": "0" * 64, "schema_sha256": "0" * 64,
        "metadata": {"module": "foreign"},
    })
    extra_errors = validate_semantics(extra, core)
    assert any("unregistered event IDs" in error for error in extra_errors)
    assert any("unregistered call roles" in error for error in extra_errors)
    assert any("unregistered call modules" in error for error in extra_errors)

    bad_core = copy.deepcopy(core)
    bad_core["planned_calls"]["maximum_total"] += 1
    assert any(
        "planned_calls is not derivable" in error
        for error in validate_semantics(events, bad_core)
    )
