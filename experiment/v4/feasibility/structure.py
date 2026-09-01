"""Fail-closed structural validation for a v4 feasibility journal.

This module deliberately checks the frozen schedule independently of outcome
values.  A terminal ``study_end`` event is necessary but never sufficient for
claiming that the schedule finished.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any, Iterable


def _rows(events: Iterable[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [event for event in events if event.get("kind") == kind]


def _counter_diff(expected: Counter[Any], observed: Counter[Any]) -> dict[str, Any]:
    missing = expected - observed
    extra = observed - expected
    return {
        "missing": {repr(key): count for key, count in sorted(missing.items(), key=lambda x: repr(x[0]))},
        "extra": {repr(key): count for key, count in sorted(extra.items(), key=lambda x: repr(x[0]))},
    }


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode()).hexdigest()


def _stable_id(*parts: Any) -> str:
    return hashlib.sha256("\x1f".join(str(part) for part in parts).encode()).hexdigest()[:20]


def _mismatch(errors: list[str], label: str, row: dict[str, Any], expected: dict[str, Any]) -> None:
    for field, value in expected.items():
        if row.get(field) != value:
            errors.append(f"{label} field {field!r} is not derivable from frozen inputs")


def validate_structure(events: list[dict[str, Any]], frozen_core: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate schedule topology and return a JSON-serialisable audit report."""
    errors: list[str] = []
    semantic_core = frozen_core if isinstance(frozen_core, dict) else None
    starts = _rows(events, "study_start")
    ends = _rows(events, "study_end")
    if len(starts) != 1:
        errors.append(f"expected exactly one study_start; observed {len(starts)}")
    if len(ends) != 1:
        errors.append(f"expected exactly one study_end; observed {len(ends)}")
    if not events or events[0].get("kind") != "study_start":
        errors.append("study_start is not the first event")
    if not events or events[-1].get("kind") != "study_end":
        errors.append("study_end is not the last event")

    if not isinstance(frozen_core, dict):
        errors.append("manifest lacks a hash-verified frozen_core")
        frozen_core = {}
    design = frozen_core.get("design")
    if len(starts) == 1:
        for field in ("claim_status", "design", "planned_calls", "budget"):
            if starts[0].get(field) != frozen_core.get(field):
                errors.append(f"study_start.{field} differs from frozen_core")
        anchor = starts[0].get("pre_dispatch_freeze_anchor")
        if not isinstance(anchor, dict) or set(anchor) != {
            "freeze_commit", "network_remote_tip_at_start",
        }:
            errors.append("study_start lacks the exact pre-dispatch freeze anchor fields")
    if not isinstance(design, dict):
        errors.append("study_start.design is missing or not an object")
        design = {}
    task_ids = design.get("task_ids")
    subset_ids = design.get("constitution_subset_task_ids")
    code_task_ids = design.get("code_task_ids")
    vendors = design.get("generator_vendors")
    auditor_vendors = design.get("auditor_vendors")
    artifact_types = design.get("artifact_types")
    policies = design.get("defensive_policies")
    interfaces = design.get("ledger_interfaces")
    attacks = design.get("ledger_attack_sequence")
    episode_count = design.get("ledger_episode_count")
    repeats = design.get("primary_audit_repeats")
    max_revisions = design.get("max_revision_rounds")
    required_lists = {
        "task_ids": task_ids,
        "constitution_subset_task_ids": subset_ids,
        "code_task_ids": code_task_ids,
        "generator_vendors": vendors,
        "auditor_vendors": auditor_vendors,
        "artifact_types": artifact_types,
        "defensive_policies": policies,
        "ledger_interfaces": interfaces,
        "ledger_attack_sequence": attacks,
    }
    for name, value in required_lists.items():
        if not isinstance(value, list) or not value or len(value) != len(set(value)):
            errors.append(f"study_start.design.{name} must be a non-empty unique list")
    if errors and not all(isinstance(v, list) for v in required_lists.values()):
        # Keep later checks deterministic without guessing a missing design.
        task_ids, subset_ids, code_task_ids = [], [], []
        vendors, auditor_vendors, artifact_types, policies, interfaces, attacks = [], [], [], [], [], []
    if vendors != auditor_vendors or len(vendors) != 2:
        errors.append("the structural contract requires the same two generator/auditor vendors")
    if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats <= 0:
        errors.append("primary_audit_repeats must be a positive integer")
        repeats = 0
    if not isinstance(max_revisions, int) or isinstance(max_revisions, bool) or max_revisions < 0:
        errors.append("max_revision_rounds must be a non-negative integer")
        max_revisions = 0
    if not isinstance(episode_count, int) or isinstance(episode_count, bool) \
            or episode_count != len(attacks):
        errors.append("ledger_episode_count must equal the attack-sequence length")
        episode_count = len(attacks)

    scheduled = _rows(events, "call_scheduled")
    completed = _rows(events, "call_complete")
    schedules_by_call: dict[str, list[dict[str, Any]]] = defaultdict(list)
    completes_by_call: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scheduled:
        schedules_by_call[str(row.get("call_id"))].append(row)
    for row in completed:
        completes_by_call[str(row.get("call_id"))].append(row)
    for call_id in sorted(set(schedules_by_call) | set(completes_by_call)):
        ss, cc = schedules_by_call.get(call_id, []), completes_by_call.get(call_id, [])
        if len(ss) != 1 or len(cc) != 1:
            errors.append(
                f"call {call_id!r} must have one schedule and one completion; "
                f"observed {len(ss)}/{len(cc)}"
            )
            continue
        schedule, completion = ss[0], cc[0]
        for field in ("role", "provider", "model", "metadata"):
            if schedule.get(field) != completion.get(field):
                errors.append(f"call {call_id!r} {field} differs between schedule and completion")
        response = completion.get("response")
        status = completion.get("status")
        invoked_statuses = {
            "valid", "invalid_schema", "provider_error", "parse_error",
            "timeout", "provider_event_policy_violation", "secret_output_quarantined",
            "model_identity_drift", "interrupted",
        }
        blocked_statuses = {
            "safety_stop_blocked", "budget_unverifiable", "upstream_failure",
            "call_cap_blocked", "elapsed_cap_blocked", "budget_blocked",
            "provider_budget_blocked",
        }
        if status not in invoked_statuses | blocked_statuses:
            errors.append(f"call {call_id!r} has unknown completion status {status!r}")
        if status in invoked_statuses and completion.get("provider_invoked") is not True:
            errors.append(f"call {call_id!r} invoked-status is not marked provider_invoked")
        if status in blocked_statuses and completion.get("provider_invoked") is not False:
            errors.append(f"call {call_id!r} blocked-status is marked provider_invoked")
        if status in blocked_statuses and (response is not None or completion.get("cost_usd") != 0.0):
            errors.append(f"call {call_id!r} blocked completion has response or nonzero cost")
        envelope_optional = {"secret_output_quarantined", "interrupted"}
        if status in invoked_statuses - envelope_optional:
            if not isinstance(response, dict):
                errors.append(f"call {call_id!r} lacks its provider response envelope")
            else:
                for field in ("prompt_sha256", "schema_sha256"):
                    if response.get(field) != schedule.get(field):
                        errors.append(f"call {call_id!r} response {field} differs from schedule")
        if status == "valid":
            local = response.get("local_schema_validation") if isinstance(response, dict) else None
            if (not isinstance(local, dict) or local.get("valid") is not True
                    or local.get("errors") != []):
                errors.append(f"call {call_id!r} valid status lacks successful local schema validation")
        if status == "invalid_schema":
            local = response.get("local_schema_validation") if isinstance(response, dict) else None
            if not isinstance(local, dict) or local.get("valid") is not False or not local.get("errors"):
                errors.append(f"call {call_id!r} invalid_schema lacks local validation errors")

    stop_seen = False
    unknown_cost_seen = False
    for event in events:
        if event.get("kind") != "call_complete":
            continue
        if (stop_seen or unknown_cost_seen) and event.get("provider_invoked"):
            errors.append(f"call {event.get('call_id')!r} was invoked after a global stop condition")
        if event.get("status") in {
            "provider_event_policy_violation", "secret_output_quarantined", "model_identity_drift",
        }:
            stop_seen = True
        if event.get("provider_invoked") and event.get("cost_usd") is None:
            unknown_cost_seen = True

    def schedules(module: str, role: str | None = None) -> list[dict[str, Any]]:
        return [
            row for row in scheduled
            if (row.get("metadata") or {}).get("module") == module
            and (role is None or row.get("role") == role)
        ]

    # Core generation and audit cells.
    core_gen_observed = Counter(
        ((row.get("metadata") or {}).get("task_id"), row.get("provider"))
        for row in schedules("core", "generator")
    )
    core_gen_expected = Counter((task, vendor) for task in task_ids for vendor in vendors)
    if core_gen_observed != core_gen_expected:
        errors.append("core generation cells differ from the frozen task×generator grid")

    core_artifacts = [
        row for row in _rows(events, "artifact") if row.get("module") == "core"
    ]
    artifact_observed = Counter(
        (row.get("task_id"), row.get("generator_vendor"), row.get("artifact_type"))
        for row in core_artifacts
    )
    artifact_expected = Counter(
        (task, vendor, artifact_type)
        for task in task_ids for vendor in vendors for artifact_type in artifact_types
    )
    if artifact_observed != artifact_expected:
        errors.append("core artefacts differ from the frozen task×generator×stratum grid")
    artifacts_by_cell = {
        (row.get("task_id"), row.get("generator_vendor"), row.get("artifact_type")): row
        for row in core_artifacts
    }
    for task in task_ids:
        for vendor in vendors:
            natural = artifacts_by_cell.get((task, vendor, "natural"))
            clean = artifacts_by_cell.get((task, vendor, "clean"))
            seeded = artifacts_by_cell.get((task, vendor, "seeded"))
            ambiguous = artifacts_by_cell.get((task, vendor, "ambiguous"))
            if not all((natural, clean, seeded, ambiguous)):
                continue
            base_id = natural.get("artifact_id")
            clean_id = clean.get("artifact_id")
            if natural.get("parent_artifact_id") is not None:
                errors.append(f"natural artefact {(task, vendor)!r} unexpectedly has a parent")
            if clean.get("parent_artifact_id") != base_id:
                errors.append(f"clean artefact {(task, vendor)!r} does not descend from natural")
            for derived in (seeded, ambiguous):
                if derived.get("parent_artifact_id") != clean_id:
                    errors.append(
                        f"{derived.get('artifact_type')} artefact {(task, vendor)!r} "
                        "does not descend directly from clean"
                    )
            for derived in (clean, seeded, ambiguous):
                if derived.get("base_artifact_id") != base_id:
                    errors.append(
                        f"{derived.get('artifact_type')} artefact {(task, vendor)!r} lacks natural base"
                    )
                value = derived.get("value")
                expected_hash = _digest(value) if value is not None else None
                if derived.get("content_sha256") != expected_hash:
                    errors.append(f"core artefact {derived.get('artifact_id')!r} has a wrong content hash")

    c2_expected = Counter(
        (task, generator, artifact_type, auditor, "C2", repeat)
        for task in task_ids for generator in vendors for artifact_type in artifact_types
        for auditor in auditor_vendors for repeat in range(repeats)
    )
    ablation_expected = Counter(
        (task, generator, artifact_type, auditor, constitution, 0)
        for task in subset_ids for generator in vendors for artifact_type in ("clean", "seeded")
        for auditor in auditor_vendors for constitution in ("C0", "C1")
    )
    core_audit_observed = Counter(
        (
            (row.get("metadata") or {}).get("task_id"),
            (row.get("metadata") or {}).get("generator_vendor"),
            (row.get("metadata") or {}).get("artifact_type"),
            row.get("provider"),
            (row.get("metadata") or {}).get("constitution"),
            (row.get("metadata") or {}).get("repeat"),
        )
        for row in schedules("core", "auditor")
    )
    core_audit_expected = c2_expected + ablation_expected
    if core_audit_observed != core_audit_expected:
        errors.append("core audit cells differ from frozen C2 repeats/C0-C1 subset")

    # Each core audit produces D0 and D2; D1 is exactly once per artefact.
    decisions = _rows(events, "audit_decision")
    d0d2_observed = Counter(
        (row.get("call_id"), row.get("dcl_mode"))
        for row in decisions if row.get("dcl_mode") in {"D0_OFF", "D2_COMBINED_BLIND"}
    )
    d0d2_expected = Counter(
        (row.get("call_id"), mode)
        for row in schedules("core", "auditor") for mode in ("D0_OFF", "D2_COMBINED_BLIND")
    )
    if d0d2_observed != d0d2_expected:
        errors.append("D0/D2 decisions do not map one-to-one to core audits")
    d1_observed = Counter(
        row.get("artifact_id") for row in decisions if row.get("dcl_mode") == "D1_ONLY"
    )
    d1_expected = Counter(row.get("artifact_id") for row in core_artifacts)
    if d1_observed != d1_expected:
        errors.append("D1 decisions are not exactly once per core artefact")
    dcl_observed = Counter(row.get("artifact_id") for row in _rows(events, "dcl_result"))
    if dcl_observed != d1_expected:
        errors.append("DCL results are not exactly once per core artefact")
    core_artifacts_by_id = {row.get("artifact_id"): row for row in core_artifacts}
    core_schedules_by_call = {
        row.get("call_id"): row for row in schedules("core", "auditor")
    }
    for row in decisions:
        artifact = core_artifacts_by_id.get(row.get("artifact_id"))
        if row.get("dcl_mode") == "D1_ONLY":
            if not artifact or any(row.get(field) != artifact.get(field) for field in (
                "task_id", "generator_vendor", "artifact_type",
            )):
                errors.append(f"D1 decision {row.get('event_id')!r} disagrees with its artefact")
            continue
        schedule = core_schedules_by_call.get(row.get("call_id"))
        metadata = schedule.get("metadata") if schedule else {}
        expected_fields = {
            "task_id": metadata.get("task_id"),
            "generator_vendor": metadata.get("generator_vendor"),
            "auditor_vendor": schedule.get("provider") if schedule else None,
            "artifact_type": metadata.get("artifact_type"),
            "constitution": metadata.get("constitution"),
            "repeat": metadata.get("repeat"),
        }
        if not schedule or not artifact or any(row.get(field) != value for field, value in expected_fields.items()):
            errors.append(f"audit decision {row.get('event_id')!r} disagrees with schedule/artefact")

    # Whole-loop topology: every seeded sibling has both auditors; revisions are conditional.
    branch_expected = Counter(
        (task, generator, auditor)
        for task in task_ids for generator in vendors for auditor in auditor_vendors
    )
    loop_ends = _rows(events, "whole_loop_end")
    branch_observed = Counter(
        (row.get("task_id"), row.get("generator_vendor"), row.get("auditor_vendor"))
        for row in loop_ends
    )
    if branch_observed != branch_expected:
        errors.append("whole-loop endings do not cover every seeded task×generator×auditor branch")
    audits_by_branch: dict[str, list[int]] = defaultdict(list)
    for row in _rows(events, "whole_loop_audit"):
        audits_by_branch[str(row.get("branch_id"))].append(row.get("round"))
    for end in loop_ends:
        branch = str(end.get("branch_id"))
        revisions = end.get("revisions")
        if not isinstance(revisions, int) or isinstance(revisions, bool) or not 0 <= revisions <= max_revisions:
            errors.append(f"whole-loop branch {branch!r} has invalid revision count")
            continue
        if sorted(audits_by_branch.get(branch, [])) != list(range(revisions + 1)):
            errors.append(f"whole-loop branch {branch!r} has non-contiguous audit rounds")
        branch_audits = sorted(
            (row for row in _rows(events, "whole_loop_audit") if str(row.get("branch_id")) == branch),
            key=lambda row: row.get("round", -1),
        )
        if any(row.get("gate") != "BLOCK" for row in branch_audits[:revisions]):
            errors.append(f"whole-loop branch {branch!r} revised after a non-BLOCK gate")
        if revisions < max_revisions and branch_audits and branch_audits[-1].get("gate") == "BLOCK":
            errors.append(f"whole-loop branch {branch!r} stopped early while still BLOCK")
        assignment = "same" if end.get("generator_vendor") == end.get("auditor_vendor") else "cross"
        if end.get("assignment") != assignment:
            errors.append(f"whole-loop branch {branch!r} has the wrong same/cross assignment")
        branch_calls = schedules("whole_loop")
        revision_rounds = sorted(
            (row.get("metadata") or {}).get("round") for row in branch_calls
            if (row.get("metadata") or {}).get("branch_id") == branch
            and row.get("role") == "whole_loop_reviser"
        )
        audit_rounds = sorted(
            (row.get("metadata") or {}).get("round") for row in branch_calls
            if (row.get("metadata") or {}).get("branch_id") == branch
            and row.get("role") == "whole_loop_auditor"
        )
        wanted = list(range(1, revisions + 1))
        if revision_rounds != wanted or audit_rounds != wanted:
            errors.append(f"whole-loop branch {branch!r} revision calls are incomplete/non-contiguous")

    # Defensive text and code schedules/endpoints.
    text_initial_expected = Counter(
        (task, vendor, policy) for task in task_ids for vendor in vendors for policy in policies
    )
    text_initial_observed = Counter(
        ((row.get("metadata") or {}).get("task_id"), row.get("provider"),
         (row.get("metadata") or {}).get("policy"))
        for row in schedules("defensive_text", "defensive_generator")
    )
    if text_initial_observed != text_initial_expected:
        errors.append("defensive-text initial generation grid is incomplete")
    all_artifacts_by_id = {
        row.get("artifact_id"): row for row in _rows(events, "artifact")
    }
    text_audit_observed = Counter(
        ((row.get("metadata") or {}).get("task_id"),
         (all_artifacts_by_id.get((row.get("metadata") or {}).get("artifact_id")) or {}).get("generator_vendor"),
         row.get("provider"), (row.get("metadata") or {}).get("policy"),
         (row.get("metadata") or {}).get("round"))
        for row in schedules("defensive_text", "defensive_auditor")
        if (row.get("metadata") or {}).get("round") == 0
    )
    text_audit_expected = Counter(
        (task, generator, next(v for v in vendors if v != generator), policy, 0)
        for task in task_ids for generator in vendors for policy in policies
    )
    if text_audit_observed != text_audit_expected:
        errors.append("defensive-text round-0 audit grid is incomplete")
    text_end_observed = Counter(
        (row.get("task_id"), row.get("generator_vendor"), row.get("policy"))
        for row in _rows(events, "defensive_loop_end")
    )
    if text_end_observed != text_initial_expected:
        errors.append("defensive-text loop endings are incomplete")

    code_initial_expected = Counter(
        (task, vendor, policy) for task in code_task_ids for vendor in vendors for policy in policies
    )
    code_initial_observed = Counter(
        ((row.get("metadata") or {}).get("task_id"), row.get("provider"),
         (row.get("metadata") or {}).get("policy"))
        for row in schedules("defensive_code", "defensive_code_generator")
    )
    if code_initial_observed != code_initial_expected:
        errors.append("defensive-code initial generation grid is incomplete")
    code_end_observed = Counter(
        (row.get("task_id"), row.get("generator_vendor"), row.get("policy"))
        for row in _rows(events, "defensive_code_loop_end")
    )
    if code_end_observed != code_initial_expected:
        errors.append("defensive-code loop endings are incomplete")

    for module, end_kind, initial_role, revision_role in (
        ("defensive_text", "defensive_loop_end", "defensive_generator", "reviser"),
        ("defensive_code", "defensive_code_loop_end", "defensive_code_generator", "defensive_code_reviser"),
    ):
        for end in _rows(events, end_kind):
            revisions = end.get("revisions")
            task, vendor, policy = end.get("task_id"), end.get("generator_vendor"), end.get("policy")
            if not isinstance(revisions, int) or isinstance(revisions, bool) or not 0 <= revisions <= max_revisions:
                errors.append(f"{module} session {(task, vendor, policy)!r} has invalid revision count")
                continue
            revision_rounds = sorted(
                (row.get("metadata") or {}).get("round") for row in schedules(module, revision_role)
                if (row.get("metadata") or {}).get("task_id") == task
                and row.get("provider") == vendor
                and (row.get("metadata") or {}).get("policy") == policy
            )
            wanted = list(range(1, revisions + 1))
            if revision_rounds != wanted:
                errors.append(f"{module} session {(task, vendor, policy)!r} has non-contiguous revisions")
            if policy != "P2" and revisions != 0:
                errors.append(f"{module} non-P2 session {(task, vendor, policy)!r} revised")
            if module == "defensive_text":
                audit_rounds = sorted(
                    (row.get("metadata") or {}).get("round") for row in schedules(module, "defensive_auditor")
                    if (row.get("metadata") or {}).get("task_id") == task
                    and (row.get("metadata") or {}).get("policy") == policy
                    and (all_artifacts_by_id.get((row.get("metadata") or {}).get("artifact_id")) or {}).get("generator_vendor") == vendor
                )
                if audit_rounds != list(range(revisions + 1)):
                    errors.append(f"{module} session {(task, vendor, policy)!r} has non-contiguous audits")
                audit_events = sorted(
                    (row for row in _rows(events, "defensive_audit")
                     if row.get("task_id") == task and row.get("generator_vendor") == vendor
                     and row.get("policy") == policy),
                    key=lambda row: row.get("round", -1),
                )
                if len(audit_events) != revisions + 1:
                    errors.append(f"{module} session {(task, vendor, policy)!r} lacks audit outcomes")
                if policy == "P2":
                    if any(row.get("gate") != "BLOCK" for row in audit_events[:revisions]):
                        errors.append(f"{module} session {(task, vendor, policy)!r} revised after non-BLOCK")
                    if revisions < max_revisions and audit_events and audit_events[-1].get("gate") == "BLOCK":
                        errors.append(f"{module} session {(task, vendor, policy)!r} stopped early while BLOCK")
            else:
                artifacts = sorted(
                    (row for row in _rows(events, "defensive_code_artifact")
                     if row.get("task_id") == task and row.get("generator_vendor") == vendor
                     and row.get("policy") == policy),
                    key=lambda row: row.get("round", -1),
                )
                if [row.get("round") for row in artifacts] != list(range(revisions + 1)):
                    errors.append(f"{module} session {(task, vendor, policy)!r} has non-contiguous artefacts")
                def failed(row: dict[str, Any]) -> bool:
                    report = row.get("evaluation") or {}
                    return not all(bool(report.get(name)) for name in (
                        "static_ok", "visible_correct", "held_out_correct",
                    ))
                if policy == "P2":
                    if any(not failed(row) for row in artifacts[:revisions]):
                        errors.append(f"{module} session {(task, vendor, policy)!r} revised a passing artefact")
                    if revisions < max_revisions and artifacts and failed(artifacts[-1]):
                        errors.append(f"{module} session {(task, vendor, policy)!r} stopped early while failing")

    # Ledger: seven deterministic attacks, six fresh proxy reviews each.
    truths = _rows(events, "ledger_truth")
    truth_attacks = Counter((row.get("truth") or {}).get("attack") for row in truths)
    if truth_attacks != Counter(attacks):
        errors.append("ledger truth episodes do not cover the frozen attack sequence exactly once")
    outcomes = _rows(events, "ledger_outcome")
    episode_ids = [row.get("episode_id") for row in truths]
    ledger_expected = Counter(
        (episode, vendor, block)
        for episode in episode_ids for vendor in vendors for block in range(3)
    )
    ledger_observed = Counter(
        (row.get("episode_id"), row.get("reviewer_vendor"),
         str(row.get("reviewer_session", "")).rsplit("-", 1)[-1])
        for row in outcomes
    )
    ledger_expected_rendered = Counter(
        (episode, vendor, str(block)) for episode, vendor, block in ledger_expected.elements()
    )
    if ledger_observed != ledger_expected_rendered:
        errors.append("ledger outcomes do not contain six proxy reviews per episode")
    ledger_truth_by_id = {row.get("episode_id"): row for row in truths}
    ledger_schedules_by_call = {
        row.get("call_id"): row for row in schedules("ledger", "ledger_proxy_reviewer")
    }
    per_episode_vendor_interfaces: Counter[tuple[Any, Any, Any]] = Counter()
    for row in outcomes:
        schedule = ledger_schedules_by_call.get(row.get("call_id"))
        metadata = schedule.get("metadata") if schedule else {}
        truth_row = ledger_truth_by_id.get(row.get("episode_id"))
        expected_fields = {
            "episode_id": metadata.get("episode_id"),
            "task_id": metadata.get("task_id"),
            "interface": metadata.get("interface"),
            "reviewer_session": metadata.get("reviewer_session"),
            "reviewer_vendor": schedule.get("provider") if schedule else None,
            "reviewer_model": schedule.get("model") if schedule else None,
        }
        if not schedule or not truth_row or any(row.get(field) != value for field, value in expected_fields.items()):
            errors.append(f"ledger outcome {row.get('event_id')!r} disagrees with schedule/truth")
        per_episode_vendor_interfaces[(
            row.get("episode_id"), row.get("reviewer_vendor"), row.get("interface"),
        )] += 1
    expected_episode_vendor_interfaces = Counter(
        (episode, vendor, interface)
        for episode in episode_ids for vendor in vendors for interface in interfaces
    )
    if per_episode_vendor_interfaces != expected_episode_vendor_interfaces:
        errors.append("each ledger episode×configuration does not contain E0/E1/E2 exactly once")
    ledger_scheduled_ids = {
        row.get("call_id") for row in schedules("ledger", "ledger_proxy_reviewer")
    }
    if ledger_scheduled_ids != {row.get("call_id") for row in outcomes}:
        errors.append("ledger schedules and outcomes are not one-to-one")
    allocation = Counter((row.get("reviewer_session"), row.get("episode_id")) for row in outcomes)
    if any(count != 1 for count in allocation.values()):
        errors.append("a ledger proxy block saw multiple surfaces for one episode")
    if len(outcomes) != episode_count * len(vendors) * 3:
        errors.append("ledger proxy-review count differs from frozen episode×configuration×block total")
    if Counter(row.get("interface") for row in outcomes) != Counter({name: episode_count * len(vendors) for name in interfaces}):
        errors.append("ledger interface allocation is not balanced")

    planned = starts[0].get("planned_calls") if len(starts) == 1 else {}
    maximum = planned.get("maximum_total") if isinstance(planned, dict) else None
    budget = starts[0].get("budget") if len(starts) == 1 else {}
    cap = budget.get("maximum_model_calls") if isinstance(budget, dict) else None
    if not isinstance(maximum, int) or len(scheduled) > maximum:
        errors.append("scheduled-call count exceeds or lacks the frozen planned maximum")
    if not isinstance(cap, int) or len(scheduled) > cap:
        errors.append("scheduled-call count exceeds or lacks the hard model-call cap")

    observed = {
        "events": len(events),
        "scheduled_calls": len(scheduled),
        "completed_calls": len(completed),
        "core_generation_cells": sum(core_gen_observed.values()),
        "core_audit_cells": sum(core_audit_observed.values()),
        "whole_loop_branches": len(loop_ends),
        "defensive_text_sessions": len(_rows(events, "defensive_loop_end")),
        "defensive_code_sessions": len(_rows(events, "defensive_code_loop_end")),
        "ledger_episodes": len(truths),
        "ledger_proxy_reviews": len(outcomes),
    }
    expected = {
        "core_generation_cells": sum(core_gen_expected.values()),
        "core_audit_cells": sum(core_audit_expected.values()),
        "whole_loop_branches": sum(branch_expected.values()),
        "defensive_text_sessions": sum(text_initial_expected.values()),
        "defensive_code_sessions": sum(code_initial_expected.values()),
        "ledger_episodes": episode_count,
        "ledger_proxy_reviews": episode_count * len(vendors) * 3,
        "maximum_scheduled_calls": maximum,
        "hard_model_call_cap": cap,
    }
    if semantic_core is not None:
        # Semantic replay is part of the sole fail-closed scoring path.  Keep
        # the import lazy because the replay module imports runner helpers to
        # reconstruct prompts, costs, and deterministic outcomes.
        try:
            from .semantics import validate_semantics

            errors.extend(
                f"semantic: {message}"
                for message in validate_semantics(events, semantic_core)
            )
        except Exception as exc:
            errors.append(
                "semantic validator failed closed: "
                f"{type(exc).__name__}: {exc}"
            )
    return {
        "valid": not errors,
        "errors": errors,
        "expected": expected,
        "observed": observed,
        "call_pairing": {
            "schedule_call_ids": len(schedules_by_call),
            "completion_call_ids": len(completes_by_call),
            **_counter_diff(
                Counter({key: len(value) for key, value in schedules_by_call.items()}),
                Counter({key: len(value) for key, value in completes_by_call.items()}),
            ),
        },
    }
