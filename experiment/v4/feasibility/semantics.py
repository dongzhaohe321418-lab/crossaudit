"""Outcome-blind semantic replay for v4 feasibility journals.

Structural counts are not enough to establish that a journal represents the
frozen experiment: a rewritten derived result can preserve every count and
foreign-key relationship.  This module therefore rebuilds the complete event
and call registry from the hash-verified ``frozen_core`` and the deterministic
functions in :mod:`run`.  Only provider completions are treated as observations;
all artefacts, gates, labels, prompts, lineages, and loop transitions are
recomputed from those observations.

The import of ``run`` is deliberately lazy.  ``score`` imports ``structure``,
and ``structure`` may in turn call this validator without creating an import
cycle during module initialisation.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Callable


_GENERIC_EVENT_FIELDS = {
    "event_id", "kind", "time_utc", "freeze_sha256",
    "previous_event_sha256", "event_sha256",
}


def _same(left: Any, right: Any) -> bool:
    """JSON-domain equality that does not equate booleans with integers."""
    try:
        return json.dumps(
            left, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ) == json.dumps(
            right, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError):
        return type(left) is type(right) and left == right


def validate_semantics(events: list[dict[str, Any]], frozen_core: dict[str, Any]) -> list[str]:
    """Return semantic-integrity errors for one otherwise parsed journal.

    This function is intentionally outcome blind: it never evaluates whether a
    model answer is scientifically favourable.  It checks only whether every
    persisted consequence is the deterministic consequence of the frozen
    design and the provider completion that precedes it.
    """
    errors: list[str] = []
    try:
        from . import run as run_api
        from . import providers as provider_api
    except ImportError:  # pragma: no cover - documented direct-script mode
        import run as run_api  # type: ignore
        import providers as provider_api  # type: ignore

    if not isinstance(events, list) or not all(isinstance(row, dict) for row in events):
        return ["semantic validation requires a list of event objects"]
    if not isinstance(frozen_core, dict):
        return ["semantic validation requires a hash-verified frozen_core object"]

    rows_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(events):
        event_id = row.get("event_id")
        if not isinstance(event_id, str):
            errors.append(f"event at index {index} has no string event_id")
            continue
        rows_by_id[event_id].append(row)
    for event_id, rows in sorted(rows_by_id.items()):
        if len(rows) != 1:
            errors.append(f"event_id {event_id!r} occurs {len(rows)} times")

    observed_by_id = {key: value[0] for key, value in rows_by_id.items() if value}
    expected_event_ids: set[str] = set()
    expected_call_ids: set[str] = set()
    expected_call_specs: dict[str, dict[str, Any]] = {}
    expected_kinds: dict[str, str] = {}

    def expect_event(event_id: str, kind: str, fields: dict[str, Any], *,
                     exact_fields: bool = True) -> dict[str, Any] | None:
        expected_event_ids.add(event_id)
        prior_kind = expected_kinds.setdefault(event_id, kind)
        if prior_kind != kind:
            errors.append(
                f"internal semantic registry collision for {event_id!r}: "
                f"{prior_kind!r} versus {kind!r}"
            )
        row = observed_by_id.get(event_id)
        if row is None:
            errors.append(f"missing expected {kind} event {event_id!r}")
            return None
        if row.get("kind") != kind:
            errors.append(
                f"event {event_id!r} has kind {row.get('kind')!r}; expected {kind!r}"
            )
        for field, expected in fields.items():
            if field not in row or not _same(row.get(field), expected):
                errors.append(
                    f"event {event_id!r} field {field!r} is not derivable from frozen inputs"
                )
        if exact_fields and kind not in {"call_complete"}:
            allowed = _GENERIC_EVENT_FIELDS | set(fields)
            extras = sorted(set(row) - allowed)
            if extras:
                errors.append(
                    f"event {event_id!r} contains unregistered fields: {extras!r}"
                )
        return row

    design = frozen_core.get("design")
    provider_rows = frozen_core.get("providers")
    task_rows = frozen_core.get("tasks")
    code_specs = frozen_core.get("code_tasks")
    schemas = frozen_core.get("schemas")
    if not isinstance(design, dict):
        return errors + ["frozen_core.design is not an object"]
    if not isinstance(provider_rows, list) or not all(isinstance(x, dict) for x in provider_rows):
        return errors + ["frozen_core.providers is not a list of objects"]
    if not isinstance(task_rows, list) or not all(isinstance(x, dict) for x in task_rows):
        return errors + ["frozen_core.tasks is not a list of objects"]
    if not isinstance(code_specs, (list, tuple)) or not all(isinstance(x, dict) for x in code_specs):
        return errors + ["frozen_core.code_tasks is not a list of objects"]
    if not isinstance(schemas, dict):
        return errors + ["frozen_core.schemas is not an object"]

    try:
        providers = {
            str(row["vendor"]): {
                "vendor": str(row["vendor"]), "model": str(row["model"]),
                "cli": str(row["cli"]),
                "identity_requirement": str(row["identity_requirement"]),
            }
            for row in provider_rows
        }
        if len(providers) != len(provider_rows):
            raise ValueError("duplicate provider vendor")
        tasks = {
            str(row["task_id"]): run_api.Task(
                task_id=str(row["task_id"]), domain=str(row["domain"]),
                brief=str(row["brief"]), result=row["result"], unit=str(row["unit"]),
                evidence=tuple(str(x) for x in row["evidence"]),
                tolerance=row["tolerance"], alternate_unit=str(row["alternate_unit"]),
                alternate_result=row["alternate_result"],
            )
            for row in task_rows
        }
        task_ids = [str(x) for x in design["task_ids"]]
        vendors = [str(x) for x in design["generator_vendors"]]
        auditor_vendors = [str(x) for x in design["auditor_vendors"]]
        policies = [str(x) for x in design["defensive_policies"]]
        artifact_types = [str(x) for x in design["artifact_types"]]
        subset_ids = {str(x) for x in design["constitution_subset_task_ids"]}
        repeats = int(design["primary_audit_repeats"])
        max_revisions = int(design["max_revision_rounds"])
        interfaces = [str(x) for x in design["ledger_interfaces"]]
        episode_count = int(design["ledger_episode_count"])
        attack_sequence = [str(x) for x in design["ledger_attack_sequence"]]
        code_task_ids = [str(x) for x in design["code_task_ids"]]
        schema_values = {
            name: row["value"] for name, row in schemas.items()
            if isinstance(row, dict) and "value" in row
        }
        artifact_schema = schema_values["artifact"]
        audit_schema = schema_values["audit"]
        code_schema = schema_values["code"]
        ledger_schema = schema_values["ledger_review"]
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return errors + [f"frozen design cannot be reconstructed: {type(exc).__name__}: {exc}"]

    if task_ids != [str(row.get("task_id")) for row in task_rows]:
        errors.append("frozen design task_ids do not exactly match frozen_core.tasks order")
    if set(task_ids) != set(tasks):
        errors.append("frozen design task_ids do not exactly match frozen_core.tasks")
    if vendors != auditor_vendors or len(vendors) != 2 or set(vendors) != set(providers):
        errors.append("frozen provider/auditor grids are not the same two provider vendors")
    if artifact_types != list(run_api.ARTIFACT_TYPES):
        errors.append("frozen artifact_types differ from the bound runner contract")
    if policies != list(run_api.POLICIES):
        errors.append("frozen defensive policies differ from the bound runner contract")
    if interfaces != list(run_api.INTERFACES):
        errors.append("frozen ledger interfaces differ from the bound runner contract")
    if attack_sequence != list(run_api.LEDGER_ATTACKS[:episode_count]):
        errors.append("frozen ledger attack sequence differs from the bound runner contract")
    if repeats != run_api.PRIMARY_REPEATS or max_revisions != run_api.MAX_REVISIONS:
        errors.append("frozen repeat/revision constants differ from the bound runner contract")
    if set(code_task_ids) != {str(row.get("task_id")) for row in code_specs}:
        errors.append("frozen code task IDs do not exactly match frozen_core.code_tasks")
    try:
        derived_plan = run_api.planned_calls(
            len(task_ids), int(design["constitution_subset_n_tasks"]),
        )
        if not _same(frozen_core.get("planned_calls"), derived_plan):
            errors.append("frozen planned_calls is not derivable from the frozen design")
        frozen_budget = frozen_core["budget"]
        if frozen_budget.get("currency") != "USD":
            errors.append("frozen budget currency is not USD")
        if type(frozen_budget.get("maximum_model_calls")) is not int \
                or frozen_budget.get("maximum_model_calls") != run_api.MAXIMUM_MODEL_CALLS:
            errors.append("frozen maximum_model_calls differs from the bound runner")
        if derived_plan["maximum_total"] > frozen_budget.get("maximum_model_calls", -1):
            errors.append("frozen prospective call plan exceeds the hard model-call cap")
        cap = frozen_budget.get("hard_cost_cap_usd")
        reserve_value = frozen_budget.get("per_call_reserve_usd")
        caps = frozen_budget.get("provider_caps_usd")
        if not run_api.finite_number(cap, non_negative=True) or not 0 < cap <= 40:
            errors.append("frozen global cost cap is outside the registered range")
        if not run_api.finite_number(reserve_value, non_negative=True) \
                or not 1 <= reserve_value <= cap:
            errors.append("frozen per-call reserve is outside the registered range")
        if not isinstance(caps, dict) or set(caps) != set(vendors):
            errors.append("frozen provider caps do not match the two vendors")
        elif any(
            not run_api.finite_number(value, non_negative=True) or not 0 < value <= cap
            for value in caps.values()
        ):
            errors.append("a frozen provider cap is outside the registered range")
        elif "anthropic" in caps and caps["anthropic"] > 25:
            errors.append("frozen Anthropic cap exceeds the registered USD 25 stop")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        errors.append(f"frozen call/budget plan cannot be derived: {type(exc).__name__}: {exc}")

    # Study bookends are part of the exact event registry.
    observed_start = observed_by_id.get("study:start") or {}
    start_anchor = observed_start.get("pre_dispatch_freeze_anchor")
    if not isinstance(start_anchor, dict) or set(start_anchor) != {
        "freeze_commit", "network_remote_tip_at_start",
    } or any(
        not isinstance(start_anchor.get(field), str) or len(start_anchor[field]) < 40
        for field in ("freeze_commit", "network_remote_tip_at_start")
    ):
        errors.append("study_start pre-dispatch freeze anchor is malformed")
        start_anchor = None
    expect_event("study:start", "study_start", {
        "claim_status": frozen_core.get("claim_status"),
        "design": design,
        "planned_calls": frozen_core.get("planned_calls"),
        "budget": frozen_core.get("budget"),
        "pre_dispatch_freeze_anchor": start_anchor,
    })
    expected_event_ids.add("study:end")  # fields are reconstructed after every call is known
    expected_kinds["study:end"] = "study_end"

    def completion_for(call_id: str) -> dict[str, Any]:
        row = observed_by_id.get(f"complete:{call_id}")
        if isinstance(row, dict):
            return row
        return {
            "call_id": call_id, "status": "missing", "response": None,
            "elapsed_seconds": 0.0,
        }

    def register_call(call_id: str, vendor: str, prompt: str, schema: dict[str, Any],
                      role: str, metadata: dict[str, Any], *,
                      upstream_ok: bool = True) -> dict[str, Any]:
        expected_call_ids.add(call_id)
        call_spec = {
            "vendor": vendor, "role": role, "metadata": metadata,
            "upstream_ok": upstream_ok, "schema": schema,
        }
        prior_spec = expected_call_specs.setdefault(call_id, call_spec)
        if not _same(prior_spec, call_spec):
            errors.append(f"semantic call registry collision for {call_id!r}")
        provider = providers.get(vendor, {"vendor": vendor, "model": None})
        common = {
            "call_id": call_id, "role": role, "provider": vendor,
            "model": provider.get("model"), "metadata": metadata,
        }
        expect_event(f"schedule:{call_id}", "call_scheduled", {
            **common,
            "prompt_sha256": run_api.prompt_digest(prompt),
            "schema_sha256": run_api.digest(schema),
        })
        completion = expect_event(
            f"complete:{call_id}", "call_complete", common, exact_fields=False,
        )
        if completion is not None:
            response = completion.get("response")
            if isinstance(response, dict) and completion.get("status") not in {
                "secret_output_quarantined", "interrupted",
            }:
                if response.get("prompt_sha256") != run_api.prompt_digest(prompt):
                    errors.append(f"completion {call_id!r} response has a wrong prompt hash")
                if response.get("schema_sha256") != run_api.digest(schema):
                    errors.append(f"completion {call_id!r} response has a wrong schema hash")
        return completion_for(call_id)

    def artifact_fields(*, artifact_id: str, module: str, task: Any,
                        generator_vendor: str, artifact_type: str,
                        policy: str | None, round_no: int,
                        completion: dict[str, Any] | None, value: Any,
                        intended_gold: str | None = None,
                        parent_artifact_id: str | None = None,
                        base_artifact_id: str | None = None) -> dict[str, Any]:
        defects = run_api.validate_artifact(task, value) if isinstance(value, dict) else []
        if intended_gold == "clean":
            gold = ("clean" if not defects else "mislabeled_clean") \
                if isinstance(value, dict) else "intended_clean_upstream_failure"
        elif intended_gold == "defective":
            gold = ("defective" if defects else "mutation_failure") \
                if isinstance(value, dict) else "intended_defective_upstream_failure"
        elif isinstance(value, dict):
            gold = "defective" if defects else "clean"
        else:
            gold = "unresolved"
        fields = {
            "artifact_id": artifact_id, "module": module, "task_id": task.task_id,
            "generator_vendor": generator_vendor,
            "generator_model": providers[generator_vendor]["model"],
            "artifact_type": artifact_type, "policy": policy, "round": round_no,
            "parent_artifact_id": parent_artifact_id,
            "base_artifact_id": base_artifact_id,
            "status": completion.get("status") if completion is not None else "derived",
            "source_call_id": completion.get("call_id") if completion is not None else None,
            "value": value,
            "content_sha256": run_api.digest(value) if value is not None else None,
            "defects": defects, "gold_status": gold,
            "requires_block": (
                False if gold == "intended_clean_upstream_failure"
                else True if gold == "intended_defective_upstream_failure"
                else bool(defects) if gold not in {
                    "unresolved", "mislabeled_clean", "mutation_failure",
                } else None
            ),
            "metrics": run_api.metric_text(value),
        }
        expect_event(f"artifact:{artifact_id}", "artifact", fields)
        return fields

    def correct_gate(gate: str, artifact: dict[str, Any]) -> int | None:
        truth = artifact.get("requires_block")
        if truth is None:
            return None
        return int(gate == ("BLOCK" if truth else "PASS"))

    # Core generation and all deterministic siblings.
    core_artifacts: dict[tuple[str, str, str], dict[str, Any]] = {}
    try:
        for task_id in task_ids:
            task = tasks[task_id]
            for vendor in vendors:
                call_id = f"core-gen-{run_api.stable_id(task_id, vendor)}"
                completion = register_call(
                    call_id, vendor, run_api.generator_prompt(task, "P0"),
                    artifact_schema, "generator",
                    {"module": "core", "task_id": task_id, "policy": "P0"},
                )
                natural_id = f"A-{run_api.stable_id('core', task_id, vendor, 'natural')}"
                natural = artifact_fields(
                    artifact_id=natural_id, module="core", task=task,
                    generator_vendor=vendor, artifact_type="natural", policy=None,
                    round_no=0, completion=completion,
                    value=run_api.response_value(completion), base_artifact_id=natural_id,
                )
                core_artifacts[(task_id, vendor, "natural")] = natural
                source = natural["value"]
                if isinstance(source, dict):
                    clean_value = run_api.clean_control(task, source)
                    seeded_value = run_api.seeded_variant(task, clean_value)
                    ambiguous_value = run_api.ambiguous_clean_control(task, clean_value)
                else:
                    clean_value = seeded_value = ambiguous_value = None
                clean_id = f"A-{run_api.stable_id('core', task_id, vendor, 'clean')}"
                clean = artifact_fields(
                    artifact_id=clean_id, module="core", task=task,
                    generator_vendor=vendor, artifact_type="clean", policy=None,
                    round_no=0, completion=None, value=clean_value,
                    intended_gold="clean", parent_artifact_id=natural_id,
                    base_artifact_id=natural_id,
                )
                core_artifacts[(task_id, vendor, "clean")] = clean
                for kind, value, intended in (
                    ("seeded", seeded_value, "defective"),
                    ("ambiguous", ambiguous_value, "clean"),
                ):
                    artifact_id = f"A-{run_api.stable_id('core', task_id, vendor, kind)}"
                    core_artifacts[(task_id, vendor, kind)] = artifact_fields(
                        artifact_id=artifact_id, module="core", task=task,
                        generator_vendor=vendor, artifact_type=kind, policy=None,
                        round_no=0, completion=None, value=value,
                        intended_gold=intended, parent_artifact_id=clean_id,
                        base_artifact_id=natural_id,
                    )
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        errors.append(f"core artefact replay failed: {type(exc).__name__}: {exc}")

    # DCL events and D1 decisions exist once per core artefact, regardless of
    # how many model-audit repeats refer to it.
    for artifact in core_artifacts.values():
        dcl_gate, dcl_findings = run_api._run_dcl(artifact)
        expect_event(f"dcl:{artifact['artifact_id']}", "dcl_result", {
            "artifact_id": artifact["artifact_id"], "task_id": artifact["task_id"],
            "gate": dcl_gate, "findings": dcl_findings,
            "note": (
                "same frozen micro-task checker also supplies feasibility gold; "
                "not an effectiveness estimate"
            ),
        })
        expect_event(
            f"decision:{artifact['artifact_id']}:D1_ONLY", "audit_decision", {
                "call_id": None, "artifact_id": artifact["artifact_id"],
                "task_id": artifact["task_id"],
                "generator_vendor": artifact["generator_vendor"],
                "auditor_vendor": None, "artifact_type": artifact["artifact_type"],
                "constitution": "NA", "repeat": 0, "dcl_mode": "D1_ONLY",
                "gate": dcl_gate, "correct_gate": correct_gate(dcl_gate, artifact),
                "false_block": (
                    int(dcl_gate == "BLOCK")
                    if artifact.get("requires_block") is False else None
                ),
                "escalation": int(dcl_gate == "ERROR"), "call_status": "offline",
            },
        )

    core_audit_completions: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for task_id in task_ids:
        task = tasks.get(task_id)
        if task is None:
            continue
        for generator_vendor in vendors:
            for kind in artifact_types:
                artifact = core_artifacts.get((task_id, generator_vendor, kind))
                if artifact is None:
                    continue
                cells: list[tuple[str, int]] = [("C2", repeat) for repeat in range(repeats)]
                if task_id in subset_ids and kind in {"clean", "seeded"}:
                    cells += [("C0", 0), ("C1", 0)]
                for auditor_vendor in auditor_vendors:
                    for constitution, repeat in cells:
                        call_id = "core-audit-" + run_api.stable_id(
                            artifact["artifact_id"], auditor_vendor, constitution, repeat,
                        )
                        metadata = {
                            "module": "core", "task_id": task_id,
                            "artifact_id": artifact["artifact_id"],
                            "generator_vendor": generator_vendor,
                            "artifact_type": kind, "constitution": constitution,
                            "repeat": repeat,
                        }
                        completion = register_call(
                            call_id, auditor_vendor,
                            run_api.audit_prompt(task, artifact.get("value"), constitution),
                            audit_schema, "auditor", metadata,
                            upstream_ok=isinstance(artifact.get("value"), dict),
                        )
                        core_audit_completions[
                            (artifact["artifact_id"], auditor_vendor, constitution, repeat)
                        ] = completion
                        model_gate, _ = run_api.audit_gate(completion)
                        dcl_gate, _ = run_api._run_dcl(artifact)
                        effective = (
                            "ERROR" if model_gate == "ERROR" or dcl_gate == "ERROR"
                            else "BLOCK" if dcl_gate == "BLOCK" or model_gate == "BLOCK"
                            else "PASS"
                        )
                        for mode, gate in (
                            ("D0_OFF", model_gate), ("D2_COMBINED_BLIND", effective),
                        ):
                            expect_event(
                                f"decision:{call_id}:{mode}", "audit_decision", {
                                    "call_id": call_id,
                                    "artifact_id": artifact["artifact_id"],
                                    "task_id": task_id,
                                    "generator_vendor": generator_vendor,
                                    "auditor_vendor": auditor_vendor,
                                    "artifact_type": kind,
                                    "constitution": constitution, "repeat": repeat,
                                    "dcl_mode": mode, "gate": gate,
                                    "correct_gate": correct_gate(gate, artifact),
                                    "false_block": (
                                        int(gate == "BLOCK")
                                        if artifact.get("requires_block") is False else None
                                    ),
                                    "escalation": int(gate == "ERROR"),
                                    "call_status": completion.get("status"),
                                },
                            )

    # Seeded same/cross whole-loop replay.  The gate recomputed from the
    # completion—not a persisted gate or revision count—controls each branch.
    for task_id in task_ids:
        task = tasks.get(task_id)
        if task is None:
            continue
        for generator_vendor in vendors:
            initial = core_artifacts.get((task_id, generator_vendor, "seeded"))
            if initial is None:
                continue
            initial_defects = run_api._defect_keys(initial.get("defects", []))
            for auditor_vendor in auditor_vendors:
                branch_id = f"WL-{run_api.stable_id(initial['artifact_id'], auditor_vendor)}"
                assignment = "same" if generator_vendor == auditor_vendor else "cross"
                initial_call_id = "core-audit-" + run_api.stable_id(
                    initial["artifact_id"], auditor_vendor, "C2", 0,
                )
                initial_completion = core_audit_completions.get(
                    (initial["artifact_id"], auditor_vendor, "C2", 0),
                    completion_for(initial_call_id),
                )
                gate, findings, model_gate, dcl_gate = run_api.combined_blind_gate(
                    initial, initial_completion,
                )
                expect_event(f"whole-loop-audit:{branch_id}:0", "whole_loop_audit", {
                    "branch_id": branch_id, "task_id": task_id,
                    "artifact_id": initial["artifact_id"],
                    "generator_vendor": generator_vendor,
                    "auditor_vendor": auditor_vendor, "assignment": assignment,
                    "round": 0, "gate": gate, "findings": findings,
                    "reused_core_call_id": initial_call_id,
                    "call_status": initial_completion.get("status"),
                    "model_gate": model_gate, "dcl_gate": dcl_gate,
                    "dcl_mode": "D2_COMBINED_BLIND",
                })
                current = initial
                rounds = 0
                while gate == "BLOCK" and rounds < max_revisions:
                    rounds += 1
                    revision_call_id = "whole-loop-revise-" + run_api.stable_id(
                        branch_id, rounds,
                    )
                    revision_metadata = {
                        "module": "whole_loop", "branch_id": branch_id,
                        "task_id": task_id, "assignment": assignment,
                        "auditor_vendor": auditor_vendor, "round": rounds,
                        "parent_artifact_id": current["artifact_id"],
                    }
                    revision = register_call(
                        revision_call_id, generator_vendor,
                        run_api.revision_prompt(task, current.get("value"), findings, rounds),
                        artifact_schema, "whole_loop_reviser", revision_metadata,
                        upstream_ok=isinstance(current.get("value"), dict),
                    )
                    artifact_id = f"{branch_id}-R{rounds}"
                    revised = artifact_fields(
                        artifact_id=artifact_id, module="whole_loop", task=task,
                        generator_vendor=generator_vendor,
                        artifact_type="seeded_revision", policy=None,
                        round_no=rounds, completion=revision,
                        value=run_api.response_value(revision),
                        parent_artifact_id=current["artifact_id"],
                    )
                    audit_call_id = "whole-loop-audit-" + run_api.stable_id(
                        branch_id, rounds,
                    )
                    audit_metadata = {
                        "module": "whole_loop", "branch_id": branch_id,
                        "task_id": task_id, "artifact_id": artifact_id,
                        "generator_vendor": generator_vendor,
                        "auditor_vendor": auditor_vendor, "assignment": assignment,
                        "round": rounds,
                    }
                    audit_completion = register_call(
                        audit_call_id, auditor_vendor,
                        run_api.audit_prompt(task, revised.get("value"), "C2"),
                        audit_schema, "whole_loop_auditor", audit_metadata,
                        upstream_ok=isinstance(revised.get("value"), dict),
                    )
                    gate, findings, model_gate, dcl_gate = run_api.combined_blind_gate(
                        revised, audit_completion,
                    )
                    expect_event(
                        f"whole-loop-audit:{branch_id}:{rounds}", "whole_loop_audit", {
                            "branch_id": branch_id, "task_id": task_id,
                            "artifact_id": artifact_id,
                            "generator_vendor": generator_vendor,
                            "auditor_vendor": auditor_vendor, "assignment": assignment,
                            "round": rounds, "gate": gate, "findings": findings,
                            "reused_core_call_id": None,
                            "call_status": audit_completion.get("status"),
                            "model_gate": model_gate, "dcl_gate": dcl_gate,
                            "dcl_mode": "D2_COMBINED_BLIND",
                        },
                    )
                    current = revised

                initial_available = isinstance(initial.get("value"), dict)
                final_available = isinstance(current.get("value"), dict)
                comparison_available = initial_available and final_available
                final_defects = (
                    run_api._defect_keys(current.get("defects", []))
                    if final_available else set()
                )
                initial_value = initial.get("value") \
                    if isinstance(initial.get("value"), dict) else {}
                final_value = current.get("value") if final_available else {}
                changed_fields = sorted(
                    field for field in set(initial_value) | set(final_value)
                    if run_api.canonical(initial_value.get(field))
                    != run_api.canonical(final_value.get(field))
                ) if comparison_available else None
                necessary_fields = {location for _, location in initial_defects}
                resolved_count = (
                    len(initial_defects - final_defects) if comparison_available else None
                )
                expect_event(f"whole-loop-end:{branch_id}", "whole_loop_end", {
                    "branch_id": branch_id, "task_id": task_id,
                    "generator_vendor": generator_vendor,
                    "auditor_vendor": auditor_vendor, "assignment": assignment,
                    "initial_artifact_id": initial["artifact_id"],
                    "final_artifact_id": current["artifact_id"],
                    "revisions": rounds,
                    "initial_gate": run_api.combined_blind_gate(
                        initial, initial_completion,
                    )[0],
                    "final_gate": gate,
                    "initial_defect_count": len(initial_defects),
                    "initial_artifact_available": initial_available,
                    "final_artifact_available": final_available,
                    "comparison_available": comparison_available,
                    "fraction_initial_resolved_ITT": (
                        resolved_count / len(initial_defects)
                        if comparison_available and initial_defects else 0.0
                    ),
                    "resolved_defect_count": resolved_count,
                    "remaining_initial_defect_count": (
                        len(initial_defects & final_defects)
                        if comparison_available else None
                    ),
                    "new_defect_count": (
                        len(final_defects - initial_defects)
                        if comparison_available else None
                    ),
                    "changed_fields": changed_fields,
                    "unnecessary_changed_fields": (
                        [field for field in changed_fields if field not in necessary_fields]
                        if changed_fields is not None else None
                    ),
                    "final_acceptable": int(not final_defects and final_available),
                    "note": "deterministic feasibility labels; no human change adjudication",
                })

    # Defensive-text generation, metrics, cross-vendor audits and P2 replay.
    defensive_initial: dict[tuple[str, str, str], dict[str, Any]] = {}
    for task_id in task_ids:
        task = tasks.get(task_id)
        if task is None:
            continue
        for vendor in vendors:
            for policy in policies:
                call_id = f"def-gen-{run_api.stable_id(task_id, vendor, policy)}"
                completion = register_call(
                    call_id, vendor, run_api.generator_prompt(task, policy),
                    artifact_schema, "defensive_generator",
                    {"module": "defensive_text", "task_id": task_id,
                     "policy": policy, "round": 0},
                )
                artifact_id = f"DP-{run_api.stable_id(task_id, vendor, policy, 0)}"
                defensive_initial[(task_id, vendor, policy)] = artifact_fields(
                    artifact_id=artifact_id, module="defensive_text", task=task,
                    generator_vendor=vendor, artifact_type="policy_output",
                    policy=policy, round_no=0, completion=completion,
                    value=run_api.response_value(completion),
                )

    def expect_defensive_metrics(artifact: dict[str, Any], baseline: dict[str, Any],
                                 *, initial: bool) -> None:
        expect_event(
            f"def-metrics:{artifact['artifact_id']}", "defensive_metrics", {
                "artifact_id": artifact["artifact_id"], "task_id": artifact["task_id"],
                "generator_vendor": artifact["generator_vendor"],
                "policy": artifact["policy"], "round": artifact["round"],
                "metrics": {
                    **artifact["metrics"],
                    "objective_correct": int(artifact.get("requires_block") is False),
                    "held_out_correct": None,
                    "method_novelty_vs_P0": run_api._method_novelty(
                        artifact.get("value"), baseline.get("value"),
                    ),
                },
                "change_label_vs_P0": run_api._defensive_change_label(artifact, baseline),
                "note": (
                    "text tasks have independent deterministic correctness but no separate "
                    "held-out generation; held_out_correct is null"
                    if initial else
                    "text tasks have no separate held-out generation; see scientific-Python fixtures"
                ),
            },
        )

    for (task_id, vendor, policy), artifact in defensive_initial.items():
        baseline = defensive_initial.get((task_id, vendor, "P0"))
        if baseline is not None:
            expect_defensive_metrics(artifact, baseline, initial=True)

    def defensive_audit(task: Any, artifact: dict[str, Any], auditor_vendor: str,
                        policy: str, round_no: int) -> tuple[str, list[dict[str, Any]]]:
        call_id = "def-audit-" + run_api.stable_id(
            artifact["artifact_id"], auditor_vendor, round_no,
        )
        completion = register_call(
            call_id, auditor_vendor,
            run_api.audit_prompt(task, artifact.get("value"), "C2"), audit_schema,
            "defensive_auditor",
            {"module": "defensive_text", "task_id": task.task_id,
             "artifact_id": artifact["artifact_id"], "policy": policy,
             "round": round_no,
             "audit_mode": "hard_gate" if policy == "P2" else "shadow"},
            upstream_ok=isinstance(artifact.get("value"), dict),
        )
        gate, findings, model_gate, dcl_gate = run_api.combined_blind_gate(
            artifact, completion,
        )
        expect_event(f"def-audit-result:{call_id}", "defensive_audit", {
            "call_id": call_id, "artifact_id": artifact["artifact_id"],
            "task_id": task.task_id,
            "generator_vendor": artifact["generator_vendor"],
            "auditor_vendor": auditor_vendor, "policy": policy,
            "round": round_no, "gate": gate, "findings": findings,
            "objective_correct": correct_gate(gate, artifact),
            "call_status": completion.get("status"),
            "model_gate": model_gate, "dcl_gate": dcl_gate,
            "dcl_mode": "D2_COMBINED_BLIND",
        })
        return gate, findings

    for task_id in task_ids:
        task = tasks.get(task_id)
        if task is None:
            continue
        for vendor in vendors:
            other_vendors = [candidate for candidate in vendors if candidate != vendor]
            if len(other_vendors) != 1:
                errors.append(f"cannot derive cross-vendor defensive auditor for {vendor!r}")
                continue
            auditor_vendor = other_vendors[0]
            for policy in policies:
                first = defensive_initial.get((task_id, vendor, policy))
                baseline = defensive_initial.get((task_id, vendor, "P0"))
                if first is None or baseline is None:
                    continue
                gate, findings = defensive_audit(task, first, auditor_vendor, policy, 0)
                current = first
                rounds = 0
                while policy == "P2" and gate == "BLOCK" and rounds < max_revisions:
                    rounds += 1
                    call_id = "def-revise-" + run_api.stable_id(
                        task_id, vendor, policy, rounds,
                    )
                    completion = register_call(
                        call_id, vendor,
                        run_api.revision_prompt(task, current.get("value"), findings, rounds),
                        artifact_schema, "reviser",
                        {"module": "defensive_text", "task_id": task_id,
                         "policy": policy, "round": rounds,
                         "parent_artifact_id": current["artifact_id"]},
                        upstream_ok=isinstance(current.get("value"), dict),
                    )
                    artifact_id = f"DP-{run_api.stable_id(task_id, vendor, policy, rounds)}"
                    revised = artifact_fields(
                        artifact_id=artifact_id, module="defensive_text", task=task,
                        generator_vendor=vendor, artifact_type="policy_output",
                        policy=policy, round_no=rounds, completion=completion,
                        value=run_api.response_value(completion),
                        parent_artifact_id=current["artifact_id"],
                    )
                    expect_defensive_metrics(revised, baseline, initial=False)
                    current = revised
                    gate, findings = defensive_audit(
                        task, current, auditor_vendor, policy, rounds,
                    )
                expect_event(f"def-loop:{task_id}:{vendor}:{policy}",
                             "defensive_loop_end", {
                    "task_id": task_id, "generator_vendor": vendor,
                    "policy": policy, "initial_artifact_id": first["artifact_id"],
                    "final_artifact_id": current["artifact_id"],
                    "revisions": rounds, "final_gate": gate,
                    "initial_objective_correct": int(first.get("requires_block") is False),
                    "final_objective_correct": int(current.get("requires_block") is False),
                })

    # Defensive code is replayed with the same isolated evaluator used by the
    # runner.  Cache evaluations because identical journals may be scored twice.
    evaluation_cache: dict[str, dict[str, Any]] = {}

    def evaluate(spec: dict[str, Any], value: Any) -> dict[str, Any]:
        key = run_api.digest({"task_id": spec.get("task_id"), "value": value})
        if key not in evaluation_cache:
            evaluation_cache[key] = run_api.evaluate_code_artifact(spec, value)
        return evaluation_cache[key]

    code_by_id = {str(spec.get("task_id")): spec for spec in code_specs}
    for task_id in code_task_ids:
        spec = code_by_id.get(task_id)
        if spec is None:
            continue
        for vendor in vendors:
            for policy in policies:
                round_no = 0
                call_id = "code-gen-" + run_api.stable_id(task_id, vendor, policy, 0)
                completion = register_call(
                    call_id, vendor, run_api.code_prompt(spec, policy), code_schema,
                    "defensive_code_generator",
                    {"module": "defensive_code", "task_id": task_id,
                     "policy": policy, "round": 0},
                )
                value = run_api.response_value(completion)
                report = evaluate(spec, value)
                initial_report = report
                artifact_id = f"DC-{run_api.stable_id(task_id, vendor, policy, 0)}"
                current = {
                    "artifact_id": artifact_id, "value": value, "evaluation": report,
                }
                expect_event(f"code-artifact:{artifact_id}", "defensive_code_artifact", {
                    "artifact_id": artifact_id, "task_id": task_id,
                    "generator_vendor": vendor,
                    "generator_model": providers[vendor]["model"],
                    "policy": policy, "round": 0, "parent_artifact_id": None,
                    "source_call_id": call_id, "value": value,
                    "content_sha256": run_api.digest(value) if value is not None else None,
                    "evaluation": report,
                })
                while (
                    policy == "P2"
                    and not all(bool(report.get(name)) for name in (
                        "static_ok", "visible_correct", "held_out_correct",
                    ))
                    and round_no < max_revisions
                ):
                    round_no += 1
                    call_id = "code-revise-" + run_api.stable_id(
                        task_id, vendor, policy, round_no,
                    )
                    completion = register_call(
                        call_id, vendor,
                        run_api.code_revision_prompt(
                            spec, current["value"], report, round_no,
                        ),
                        code_schema, "defensive_code_reviser",
                        {"module": "defensive_code", "task_id": task_id,
                         "policy": policy, "round": round_no,
                         "parent_artifact_id": current["artifact_id"]},
                        upstream_ok=isinstance(current.get("value"), dict),
                    )
                    value = run_api.response_value(completion)
                    report = evaluate(spec, value)
                    next_id = f"DC-{run_api.stable_id(task_id, vendor, policy, round_no)}"
                    expect_event(f"code-artifact:{next_id}",
                                 "defensive_code_artifact", {
                        "artifact_id": next_id, "task_id": task_id,
                        "generator_vendor": vendor,
                        "generator_model": providers[vendor]["model"],
                        "policy": policy, "round": round_no,
                        "parent_artifact_id": current["artifact_id"],
                        "source_call_id": call_id, "value": value,
                        "content_sha256": (
                            run_api.digest(value) if value is not None else None
                        ),
                        "evaluation": report,
                    })
                    current = {
                        "artifact_id": next_id, "value": value, "evaluation": report,
                    }
                expect_event(f"code-loop:{task_id}:{vendor}:{policy}",
                             "defensive_code_loop_end", {
                    "task_id": task_id, "generator_vendor": vendor, "policy": policy,
                    "final_artifact_id": current["artifact_id"],
                    "revisions": round_no,
                    "initial_static_ok": initial_report["static_ok"],
                    "initial_visible_correct": initial_report["visible_correct"],
                    "initial_held_out_correct": initial_report["held_out_correct"],
                    "initial_objective_correct": int(all(
                        bool(initial_report[name]) for name in (
                            "static_ok", "visible_correct", "held_out_correct",
                        )
                    )),
                    "final_static_ok": report["static_ok"],
                    "final_visible_correct": report["visible_correct"],
                    "final_held_out_correct": report["held_out_correct"],
                    "final_objective_correct": int(all(
                        bool(report[name]) for name in (
                            "static_ok", "visible_correct", "held_out_correct",
                        )
                    )),
                })

    # Provenance surfaces are never trusted from the journal: reconstruct each
    # from the frozen task and episode number, then hash the exact review prompt.
    for episode_no in range(episode_count):
        if not task_ids:
            break
        task_id = task_ids[episode_no % len(task_ids)]
        task = tasks.get(task_id)
        if task is None:
            continue
        surfaces, truth = run_api._ledger_episode(task, episode_no)
        episode_id = f"LE-{episode_no:02d}"
        if episode_no < len(attack_sequence) and truth.get("attack") != attack_sequence[episode_no]:
            errors.append(f"ledger episode {episode_id!r} attack differs from frozen sequence")
        expect_event(f"ledger-truth:{episode_id}", "ledger_truth", {
            "episode_id": episode_id, "task_id": task_id, "truth": truth,
            "note": (
                "deterministic seeded proxy episode; attack key is not sent in "
                "E0/E1/E2 prompt metadata"
            ),
        })
        for reviewer_vendor in vendors:
            for block in range(3):
                interface = interfaces[(episode_no + block) % len(interfaces)]
                session_id = f"{reviewer_vendor}-proxy-block-{block}"
                surface = {"interface": interface, **surfaces[interface]}
                call_id = "ledger-review-" + run_api.stable_id(
                    episode_id, interface, reviewer_vendor, session_id,
                )
                completion = register_call(
                    call_id, reviewer_vendor, run_api.ledger_review_prompt(surface),
                    ledger_schema, "ledger_proxy_reviewer",
                    {"module": "ledger", "episode_id": episode_id,
                     "task_id": task_id, "interface": interface,
                     "reviewer_session": session_id},
                )
                review = run_api.validated_ledger_review(
                    run_api.response_value(completion),
                )
                valid = review is not None
                expect_event(f"ledger-outcome:{call_id}", "ledger_outcome", {
                    "call_id": call_id, "episode_id": episode_id,
                    "task_id": task_id, "interface": interface,
                    "reviewer_vendor": reviewer_vendor,
                    "reviewer_model": providers[reviewer_vendor]["model"],
                    "reviewer_session": session_id, "attack": truth["attack"],
                    "status": (
                        completion.get("status") if valid
                        else "invalid_review_schema"
                        if completion.get("status") == "valid"
                        else completion.get("status")
                    ),
                    "review_schema_valid": valid, "review": review,
                    "correct_accept": (
                        int(review["accept"] == truth["accept"]) if valid else 0
                    ),
                    "correct_tamper": (
                        int(review["tamper_detected"] == truth["tamper_truth"])
                        if valid else 0
                    ),
                    "correct_origin": (
                        int(review["origin_round"] == truth["origin_round"])
                        if valid else 0
                    ),
                    "correct_first_defective": (
                        int(review["first_defective_round"] == truth["first_defective_round"])
                        if valid else 0
                    ),
                    "correct_rounds": (
                        int(
                            review["origin_round"] == truth["origin_round"]
                            and review["first_defective_round"]
                            == truth["first_defective_round"]
                        ) if valid else 0
                    ),
                    "correct_rule": (
                        int(review["rule_version"] == truth["rule_version"])
                        if valid else 0
                    ),
                    "elapsed_seconds": completion.get("elapsed_seconds", 0.0),
                })

    # Replay resource accounting and every deterministic pre-dispatch stop in
    # append order.  This keeps a rewritten status, token ledger, or cost from
    # changing which later model calls appear to have been eligible.
    price_table = frozen_core.get("price_table")
    budget = frozen_core.get("budget")
    provider_objects: dict[str, Any] = {}
    if isinstance(price_table, dict) and isinstance(budget, dict):
        for row in provider_rows:
            try:
                provider_objects[str(row["vendor"])] = run_api.Provider(
                    str(row["vendor"]), str(row["model"]), str(row["cli"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(
                    f"provider accounting identity is invalid: {type(exc).__name__}: {exc}"
                )
    else:
        errors.append("frozen price_table/budget cannot be replayed")

    token_fields = (
        "input_tokens", "output_tokens", "cached_input_tokens",
        "cache_creation_input_tokens", "cache_write_input_tokens",
        "reasoning_tokens", "source_entry_count",
    )

    def valid_usage_shape(call_id: str, usage: Any) -> bool:
        if not isinstance(usage, dict):
            errors.append(f"completion {call_id!r} usage is not an object")
            return False
        valid = True
        for field in token_fields:
            value = usage.get(field)
            if type(value) is not int or value < 0:
                errors.append(
                    f"completion {call_id!r} usage.{field} is not a non-negative integer"
                )
                valid = False
        for field in (
            "available", "billable_fields_complete", "invalid_nonfinite",
            "invalid_token_fields",
        ):
            if type(usage.get(field)) is not bool:
                errors.append(f"completion {call_id!r} usage.{field} is not boolean")
                valid = False
        if usage.get("provenance") not in {
            "unavailable", "sum_of_model_usage_entries", "top_level_usage", "model_usage",
        }:
            errors.append(f"completion {call_id!r} usage provenance is unregistered")
            valid = False
        expected_keys = set(token_fields) | {
            "available", "billable_fields_complete", "invalid_nonfinite",
            "invalid_token_fields", "provenance",
        }
        if set(usage) != expected_keys:
            errors.append(f"completion {call_id!r} usage fields differ from the frozen ledger")
            valid = False
        return valid

    invoked_statuses = {
        "valid", "invalid_schema", "provider_error", "parse_error", "timeout",
        "provider_event_policy_violation", "secret_output_quarantined",
        "model_identity_drift", "interrupted",
    }
    safety_statuses = {
        "provider_event_policy_violation", "secret_output_quarantined",
        "model_identity_drift",
    }
    safety_seen = False
    unknown_cost_seen = False
    prior_invocations = 0
    replay_elapsed = 0.0
    replay_accrued = 0.0
    replay_provider_accrued = {vendor: 0.0 for vendor in vendors}
    unknown_cost_providers: set[str] = set()
    try:
        global_cap = float(budget["hard_cost_cap_usd"])
        reserve = float(budget["per_call_reserve_usd"])
        maximum_calls = int(budget["maximum_model_calls"])
        provider_caps = {
            str(key): float(value) for key, value in budget["provider_caps_usd"].items()
        }
        elapsed_cap = int(design["cumulative_provider_elapsed_cap_seconds"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        errors.append(f"frozen stop policy cannot be replayed: {type(exc).__name__}: {exc}")
        global_cap = reserve = float("inf")
        maximum_calls = 2**63 - 1
        provider_caps = {vendor: float("inf") for vendor in vendors}
        elapsed_cap = 2**63 - 1

    completion_rows = [row for row in events if row.get("kind") == "call_complete"]
    for completion in completion_rows:
        call_id = completion.get("call_id")
        if not isinstance(call_id, str) or call_id not in expected_call_specs:
            # The exact registry reports this independently; never let an
            # unregistered row influence replay state.
            continue
        spec = expected_call_specs[call_id]
        vendor = spec["vendor"]
        status = completion.get("status")
        invoked = completion.get("provider_invoked")
        elapsed = completion.get("elapsed_seconds")
        completion_base_fields = _GENERIC_EVENT_FIELDS | {
            "call_id", "role", "provider", "model", "status", "provider_invoked",
            "response", "usage", "cost_usd", "elapsed_seconds", "metadata",
        }
        regular_invocation_fields = completion_base_fields | {
            "cost_source", "global_cap_overshoot", "provider_cap_overshoot",
            "identity_verified",
        }
        if status == "interrupted":
            expected_completion_fields = completion_base_fields
        elif status == "safety_stop_blocked":
            expected_completion_fields = completion_base_fields | {
                "cost_unverifiable", "blocking_unknown_cost_providers",
            }
        elif status == "budget_unverifiable":
            expected_completion_fields = completion_base_fields | {
                "cost_unverifiable", "budget_scope", "blocking_unknown_cost_providers",
            }
        elif invoked is True:
            expected_completion_fields = regular_invocation_fields
        else:
            expected_completion_fields = completion_base_fields
        missing_completion_fields = sorted(expected_completion_fields - set(completion))
        extra_completion_fields = sorted(set(completion) - expected_completion_fields)
        if missing_completion_fields:
            errors.append(
                f"completion {call_id!r} lacks required operational fields: "
                f"{missing_completion_fields!r}"
            )
        if extra_completion_fields:
            errors.append(
                f"completion {call_id!r} contains unregistered operational fields: "
                f"{extra_completion_fields!r}"
            )
        if not run_api.finite_number(elapsed, non_negative=True):
            errors.append(f"completion {call_id!r} elapsed_seconds is not finite/non-negative")

        usage = completion.get("usage")
        valid_usage_shape(call_id, usage)
        response = completion.get("response")
        quarantined = status == "secret_output_quarantined"
        if invoked is False and response is not None:
            errors.append(f"blocked completion {call_id!r} retains a response envelope")
        if invoked is True and status not in {"interrupted", "secret_output_quarantined"} \
                and not isinstance(response, dict):
            errors.append(f"invoked completion {call_id!r} lacks a response envelope")
        if quarantined:
            expected_quarantine_keys = {
                "status", "discarded_raw_sha256", "secret_pattern_labels", "note",
            }
            if not isinstance(response, dict) or set(response) != expected_quarantine_keys:
                errors.append(f"quarantined completion {call_id!r} has a malformed tombstone")
            elif (
                response.get("status") != "secret_output_quarantined"
                or not isinstance(response.get("discarded_raw_sha256"), str)
                or len(response["discarded_raw_sha256"]) != 64
                or not isinstance(response.get("secret_pattern_labels"), list)
                or not response["secret_pattern_labels"]
                or response.get("note")
                != "raw response discarded before append-only journal persistence"
            ):
                errors.append(f"quarantined completion {call_id!r} tombstone is not reproducible")
        if isinstance(response, dict) and invoked is True and status not in {
            "interrupted", "secret_output_quarantined",
        }:
            expected_adapter_fields = {
                "vendor": vendor,
                "model_requested": providers[vendor]["model"],
                "cli": providers[vendor]["cli"],
                "role": spec["role"],
            }
            for field, expected_value in expected_adapter_fields.items():
                if response.get(field) != expected_value:
                    errors.append(
                        f"completion {call_id!r} response {field} disagrees with the frozen adapter"
                    )
            if not run_api.finite_number(
                response.get("elapsed_seconds"), non_negative=True,
            ):
                errors.append(
                    f"completion {call_id!r} response elapsed_seconds is invalid"
                )
            response_status = str(response.get("status", "parse_error"))
            if response_status not in {
                "valid", "provider_error", "parse_error", "timeout",
                "provider_event_policy_violation",
            }:
                response_status = "parse_error"
            derived_status = response_status
            if response_status == "valid":
                schema_errors = run_api.validate_json_schema(
                    response.get("value"), spec["schema"],
                )
                expected_local = {
                    "valid": not schema_errors, "errors": schema_errors[:100],
                }
                if not _same(response.get("local_schema_validation"), expected_local):
                    errors.append(
                        f"completion {call_id!r} local schema validation is not reproducible"
                    )
                if schema_errors:
                    derived_status = "invalid_schema"
                if vendor == "openai" and providers[vendor].get("cli") == "codex":
                    raw_events = response.get("raw_envelope")
                    expected_notice_ids = list(
                        provider_api.CODEX_EXPECTED_STARTUP_NOTICE_IDS
                    )
                    expected_notice_hashes = list(
                        provider_api.CODEX_EXPECTED_STARTUP_NOTICE_MESSAGE_HASHES
                    )
                    if not isinstance(raw_events, list) or not all(
                        isinstance(event, dict) for event in raw_events
                    ):
                        errors.append(
                            f"completion {call_id!r} lacks replayable Codex raw events"
                        )
                    else:
                        try:
                            raw_jsonl = "\n".join(
                                json.dumps(
                                    event, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False,
                                )
                                for event in raw_events
                            )
                        except (TypeError, ValueError, OverflowError):
                            raw_jsonl = ""
                            errors.append(
                                f"completion {call_id!r} Codex raw events are not strict JSON"
                            )
                        replayed_events, policy_violations = (
                            provider_api.parse_codex_event_stream(raw_jsonl)
                            if raw_jsonl else ([], [{"reason": "not_strict_json"}])
                        )
                        notice_ids, notice_hashes = (
                            provider_api.codex_startup_notice_evidence(replayed_events)
                        )
                        if policy_violations:
                            errors.append(
                                f"completion {call_id!r} Codex raw events fail policy replay"
                            )
                        if notice_ids != expected_notice_ids \
                                or notice_hashes != expected_notice_hashes:
                            errors.append(
                                f"completion {call_id!r} Codex startup notice evidence "
                                "differs from the frozen contract"
                            )
                    if response.get("allowed_startup_notices") != expected_notice_ids \
                            or response.get("allowed_startup_notice_count") \
                            != len(expected_notice_ids) \
                            or response.get(
                                "allowed_startup_notice_message_hashes"
                            ) != expected_notice_hashes:
                        errors.append(
                            f"completion {call_id!r} Codex startup notice summary "
                            "is not reproducible"
                        )
            if derived_status not in {
                "provider_error", "parse_error", "timeout",
                "provider_event_policy_violation",
            }:
                observed_models = response.get("models_observed")
                expected_identity: bool | None = None
                missing_identity = observed_models is None or observed_models == []
                requirement = providers[vendor].get("identity_requirement")
                if missing_identity and requirement == "unavailable_allowed":
                    expected_identity = None
                else:
                    expected_identity = run_api.model_alias_observed(
                        str(providers[vendor]["model"]), observed_models,
                    )
                    if not expected_identity:
                        derived_status = "model_identity_drift"
                if completion.get("identity_verified") is not expected_identity:
                    errors.append(
                        f"completion {call_id!r} identity verification is not reproducible"
                    )
            elif completion.get("identity_verified") is not None:
                errors.append(
                    f"completion {call_id!r} has identity evidence for an ineligible response"
                )
            if status != derived_status:
                errors.append(
                    f"completion {call_id!r} status is not derivable from its response"
                )
        if not quarantined:
            expected_usage = run_api.normalise_usage(response if isinstance(response, dict) else {})
            if not _same(usage, expected_usage):
                errors.append(f"completion {call_id!r} usage is not derivable from its response")

        expected_block: str | None = None
        # A resume-generated interrupted completion is created before all stop
        # checks.  The journal does not carry execution-session boundaries, so
        # its special precedence is validated through its fixed payload below.
        is_interrupted = status == "interrupted"
        if not is_interrupted:
            if safety_seen:
                expected_block = "safety_stop_blocked"
            elif unknown_cost_seen:
                expected_block = "budget_unverifiable"
            elif not spec["upstream_ok"]:
                expected_block = "upstream_failure"
            elif prior_invocations >= maximum_calls:
                expected_block = "call_cap_blocked"
            elif replay_elapsed >= elapsed_cap:
                expected_block = "elapsed_cap_blocked"
            elif replay_accrued + reserve > global_cap + 1e-12:
                expected_block = "budget_blocked"
            elif replay_provider_accrued.get(vendor, 0.0) + reserve \
                    > provider_caps.get(vendor, global_cap) + 1e-12:
                expected_block = "provider_budget_blocked"

        if expected_block is not None:
            if status != expected_block or invoked is not False:
                errors.append(
                    f"completion {call_id!r} violates pre-dispatch stop replay; "
                    f"expected {expected_block!r}"
                )
        elif status not in invoked_statuses or invoked is not True:
            errors.append(
                f"completion {call_id!r} is blocked/invoked inconsistently with stop replay"
            )
        expected_unknown_providers = sorted(unknown_cost_providers)
        if status == "safety_stop_blocked":
            if completion.get("cost_unverifiable") is not bool(unknown_cost_providers) \
                    or completion.get("blocking_unknown_cost_providers") \
                    != expected_unknown_providers:
                errors.append(f"completion {call_id!r} has wrong safety-stop evidence")
        if status == "budget_unverifiable":
            if completion.get("cost_unverifiable") is not True \
                    or completion.get("budget_scope") != "combined_cohort" \
                    or completion.get("blocking_unknown_cost_providers") \
                    != expected_unknown_providers:
                errors.append(f"completion {call_id!r} has wrong unknown-cost stop evidence")

        cost = completion.get("cost_usd")
        cost_source = completion.get("cost_source")
        if invoked is False:
            if not _same(cost, 0.0):
                errors.append(f"blocked completion {call_id!r} does not have zero cost")
            if "cost_source" in completion:
                errors.append(f"blocked completion {call_id!r} has an unexpected cost source")
        elif is_interrupted:
            if cost is not None or "cost_source" in completion:
                errors.append(f"interrupted completion {call_id!r} has invented cost evidence")
        elif quarantined:
            if cost is not None or cost_source != "quarantined_unverifiable" \
                    or not _same(usage, run_api.normalise_usage({})) \
                    or completion.get("identity_verified") is not None:
                errors.append(
                    f"quarantined completion {call_id!r} must use the fixed unverifiable ledger"
                )
        elif invoked is True:
            provider = provider_objects.get(vendor)
            if provider is None or not isinstance(price_table, dict):
                errors.append(f"completion {call_id!r} lacks a frozen provider price identity")
            else:
                expected_cost, expected_source = run_api.call_cost(
                    provider, response if isinstance(response, dict) else {},
                    usage if isinstance(usage, dict) else {}, price_table,
                )
                if not _same(cost, expected_cost) or cost_source != expected_source:
                    errors.append(
                        f"completion {call_id!r} cost/source is not derivable from frozen prices"
                    )

        if invoked is True and not is_interrupted:
            numeric_cost = (
                float(cost) if run_api.finite_number(cost, non_negative=True) else None
            )
            expected_global_overshoot = (
                numeric_cost is not None
                and replay_accrued + numeric_cost > global_cap + 1e-12
            )
            expected_provider_overshoot = (
                numeric_cost is not None
                and replay_provider_accrued.get(vendor, 0.0) + numeric_cost
                > provider_caps.get(vendor, global_cap) + 1e-12
            )
            if completion.get("global_cap_overshoot") is not expected_global_overshoot:
                errors.append(f"completion {call_id!r} has a wrong global-cap overshoot flag")
            if completion.get("provider_cap_overshoot") is not expected_provider_overshoot:
                errors.append(f"completion {call_id!r} has a wrong provider-cap overshoot flag")

        if invoked is True:
            prior_invocations += 1
            if run_api.finite_number(elapsed, non_negative=True):
                replay_elapsed += float(elapsed)
        if run_api.finite_number(cost, non_negative=True):
            replay_accrued += float(cost)
            replay_provider_accrued[vendor] = (
                replay_provider_accrued.get(vendor, 0.0) + float(cost)
            )
        if status in safety_statuses:
            safety_seen = True
        if invoked is True and cost is None:
            unknown_cost_seen = True
            unknown_cost_providers.add(vendor)

    # The terminal budget summary is a deterministic aggregation of observed
    # call completions.  It is not allowed to self-report a more favourable cap
    # or cost state.
    # Preserve append order: IEEE-754 addition is not associative and the
    # runner accrues costs in journal order.
    completions = [
        row for row in events
        if row.get("kind") == "call_complete" and row.get("call_id") in expected_call_ids
    ]
    accrued = sum(
        float(row["cost_usd"]) for row in completions
        if isinstance(row.get("cost_usd"), (int, float))
    )
    provider_accrued = {
        vendor: sum(
            float(row["cost_usd"]) for row in completions
            if row.get("provider") == vendor
            and isinstance(row.get("cost_usd"), (int, float))
        )
        for vendor in vendors
    }
    expect_event("study:end", "study_end", {
        "accrued_cost_usd": accrued,
        "provider_accrued_cost_usd": provider_accrued,
        "cost_cap_overshoot_seen": any(
            row.get("global_cap_overshoot") or row.get("provider_cap_overshoot")
            for row in completions
        ),
        "unknown_cost_seen": any(
            row.get("provider_invoked") and row.get("cost_usd") is None
            for row in completions
        ),
        "note": (
            "completion means the feasibility schedule was attempted, not that "
            "every provider call succeeded"
        ),
    })

    # Rebuild the exact seeded call order.  Order is part of the estimand:
    # safety and unknown-cost stops censor every later cell, while provider caps
    # censor later calls for only one configuration.  Merely checking the ID
    # union would therefore permit a materially different ITT exposure.
    seed = int(design.get("randomisation_seed", 0))
    expected_schedule_sequence: list[str] = []
    core_generation_cells = run_api._shuffled(
        [(task_id, vendor) for task_id in task_ids for vendor in vendors], seed + 101,
    )
    expected_schedule_sequence.extend(
        f"core-gen-{run_api.stable_id(task_id, vendor)}"
        for task_id, vendor in core_generation_cells
    )
    core_audit_cells: list[tuple[dict[str, Any], str, str, int]] = []
    for task_id in task_ids:
        for generator_vendor in vendors:
            for kind in artifact_types:
                artifact = core_artifacts.get((task_id, generator_vendor, kind))
                if artifact is None:
                    continue
                for auditor_vendor in auditor_vendors:
                    for repeat in range(repeats):
                        core_audit_cells.append((artifact, auditor_vendor, "C2", repeat))
                    if task_id in subset_ids and kind in {"clean", "seeded"}:
                        core_audit_cells.extend(
                            (artifact, auditor_vendor, constitution, 0)
                            for constitution in ("C0", "C1")
                        )
    expected_schedule_sequence.extend(
        "core-audit-" + run_api.stable_id(
            artifact["artifact_id"], auditor_vendor, constitution, repeat,
        )
        for artifact, auditor_vendor, constitution, repeat
        in run_api._shuffled(core_audit_cells, seed + 202)
    )
    seeded_artifacts = sorted(
        (artifact for (task_id, vendor, kind), artifact in core_artifacts.items()
         if kind == "seeded"),
        key=lambda artifact: artifact["artifact_id"],
    )
    for initial in seeded_artifacts:
        branch_seed = seed + int(
            run_api.stable_id("whole-loop-order", initial["artifact_id"]), 16,
        )
        for auditor_vendor in run_api._shuffled(auditor_vendors, branch_seed):
            branch_id = f"WL-{run_api.stable_id(initial['artifact_id'], auditor_vendor)}"
            for round_no in range(1, max_revisions + 1):
                revision_id = "whole-loop-revise-" + run_api.stable_id(
                    branch_id, round_no,
                )
                audit_id = "whole-loop-audit-" + run_api.stable_id(
                    branch_id, round_no,
                )
                if revision_id not in expected_call_specs:
                    break
                expected_schedule_sequence.append(revision_id)
                if audit_id in expected_call_specs:
                    expected_schedule_sequence.append(audit_id)

    defensive_generation_cells = run_api._shuffled(
        [(task_id, vendor, policy) for task_id in task_ids
         for vendor in vendors for policy in policies],
        seed + 303,
    )
    expected_schedule_sequence.extend(
        f"def-gen-{run_api.stable_id(task_id, vendor, policy)}"
        for task_id, vendor, policy in defensive_generation_cells
    )
    for task_id, vendor, policy in run_api._shuffled(
        defensive_generation_cells, seed + 304,
    ):
        auditor_vendor = next(candidate for candidate in vendors if candidate != vendor)
        for round_no in range(max_revisions + 1):
            artifact_id = f"DP-{run_api.stable_id(task_id, vendor, policy, round_no)}"
            audit_id = "def-audit-" + run_api.stable_id(
                artifact_id, auditor_vendor, round_no,
            )
            if audit_id not in expected_call_specs:
                break
            if round_no > 0:
                revision_id = "def-revise-" + run_api.stable_id(
                    task_id, vendor, policy, round_no,
                )
                if revision_id in expected_call_specs:
                    expected_schedule_sequence.append(revision_id)
            expected_schedule_sequence.append(audit_id)

    code_cells = run_api._shuffled(
        [(task_id, vendor, policy) for task_id in code_task_ids
         for vendor in vendors for policy in policies],
        seed + 404,
    )
    for task_id, vendor, policy in code_cells:
        expected_schedule_sequence.append(
            "code-gen-" + run_api.stable_id(task_id, vendor, policy, 0)
        )
        for round_no in range(1, max_revisions + 1):
            revision_id = "code-revise-" + run_api.stable_id(
                task_id, vendor, policy, round_no,
            )
            if revision_id not in expected_call_specs:
                break
            expected_schedule_sequence.append(revision_id)

    ledger_cells: list[tuple[str, str, str, str]] = []
    for episode_no in range(episode_count):
        episode_id = f"LE-{episode_no:02d}"
        for reviewer_vendor in vendors:
            for block in range(3):
                interface = interfaces[(episode_no + block) % len(interfaces)]
                session_id = f"{reviewer_vendor}-proxy-block-{block}"
                ledger_cells.append(
                    (episode_id, interface, reviewer_vendor, session_id)
                )
    expected_schedule_sequence.extend(
        "ledger-review-" + run_api.stable_id(
            episode_id, interface, reviewer_vendor, session_id,
        )
        for episode_id, interface, reviewer_vendor, session_id
        in run_api._shuffled(ledger_cells, seed + 505)
    )
    if len(expected_schedule_sequence) != len(set(expected_schedule_sequence)) \
            or set(expected_schedule_sequence) != expected_call_ids:
        errors.append("seeded semantic call-order registry does not match expected call union")
    observed_schedule_sequence = [
        str(row.get("call_id")) for row in events if row.get("kind") == "call_scheduled"
    ]
    if observed_schedule_sequence != expected_schedule_sequence:
        errors.append("call_scheduled sequence differs from the frozen seeded order")
    positions_for_dispatch = {
        row.get("event_id"): index for index, row in enumerate(events)
        if isinstance(row.get("event_id"), str)
    }
    for index, call_id in enumerate(expected_schedule_sequence):
        schedule_position = positions_for_dispatch.get(f"schedule:{call_id}")
        complete_position = positions_for_dispatch.get(f"complete:{call_id}")
        if schedule_position is None or complete_position is None:
            continue
        if index + 1 < len(expected_schedule_sequence):
            next_schedule = positions_for_dispatch.get(
                f"schedule:{expected_schedule_sequence[index + 1]}"
            )
            if next_schedule is not None and not (
                schedule_position < complete_position < next_schedule
            ):
                errors.append(
                    f"call {call_id!r} was not synchronously completed before the next dispatch"
                )

    observed_event_ids = set(rows_by_id)
    missing_ids = sorted(expected_event_ids - observed_event_ids)
    extra_ids = sorted(observed_event_ids - expected_event_ids)
    # Individual missing-event messages above are useful locally; the set-level
    # report proves that the expected union itself was checked.
    if missing_ids:
        errors.append(f"expected event-ID union is missing IDs: {missing_ids!r}")
    if extra_ids:
        errors.append(f"journal contains unregistered event IDs: {extra_ids!r}")

    scheduled_call_ids = {
        str(row.get("call_id")) for row in events if row.get("kind") == "call_scheduled"
    }
    completed_call_ids = {
        str(row.get("call_id")) for row in events if row.get("kind") == "call_complete"
    }
    if scheduled_call_ids != expected_call_ids:
        errors.append(
            "scheduled call-ID registry differs from semantic replay: "
            f"missing={sorted(expected_call_ids - scheduled_call_ids)!r}, "
            f"extra={sorted(scheduled_call_ids - expected_call_ids)!r}"
        )
    if completed_call_ids != expected_call_ids:
        errors.append(
            "completed call-ID registry differs from semantic replay: "
            f"missing={sorted(expected_call_ids - completed_call_ids)!r}, "
            f"extra={sorted(completed_call_ids - expected_call_ids)!r}"
        )

    # Explicitly reject unexpected module/role values even when an attacker
    # reuses an otherwise plausible ID.
    registered_roles = {
        row.get("role") for row in events
        if row.get("kind") in {"call_scheduled", "call_complete"}
    }
    allowed_roles = {
        "generator", "auditor", "whole_loop_reviser", "whole_loop_auditor",
        "defensive_generator", "defensive_auditor", "reviser",
        "defensive_code_generator", "defensive_code_reviser",
        "ledger_proxy_reviewer",
    }
    unknown_roles = sorted(str(x) for x in registered_roles - allowed_roles)
    if unknown_roles:
        errors.append(f"journal contains unregistered call roles: {unknown_roles!r}")
    observed_modules = {
        (row.get("metadata") or {}).get("module")
        for row in events if row.get("kind") in {"call_scheduled", "call_complete"}
        and isinstance(row.get("metadata"), dict)
    }
    allowed_modules = {"core", "whole_loop", "defensive_text", "defensive_code", "ledger"}
    unknown_modules = sorted(str(x) for x in observed_modules - allowed_modules)
    if unknown_modules:
        errors.append(f"journal contains unregistered call modules: {unknown_modules!r}")

    # Validate causal ordering without assuming a particular randomised cell
    # order.  Every local edge must point backwards in the append-only journal.
    positions = {
        row.get("event_id"): index for index, row in enumerate(events)
        if isinstance(row.get("event_id"), str)
    }

    def precedes(parent_id: str, child_id: str, label: str) -> None:
        parent_pos, child_pos = positions.get(parent_id), positions.get(child_id)
        if parent_pos is not None and child_pos is not None and parent_pos >= child_pos:
            errors.append(
                f"causal order violation: {parent_id!r} does not precede "
                f"{child_id!r} ({label})"
            )

    for call_id in expected_call_ids:
        precedes(f"schedule:{call_id}", f"complete:{call_id}", "dispatch")
    for row in events:
        event_id = row.get("event_id")
        if not isinstance(event_id, str):
            continue
        kind = row.get("kind")
        source_call = row.get("source_call_id")
        if isinstance(source_call, str):
            precedes(f"complete:{source_call}", event_id, "artefact source")
        parent_artifact = row.get("parent_artifact_id")
        if isinstance(parent_artifact, str):
            parent_prefix = "code-artifact:" if kind == "defensive_code_artifact" \
                else "artifact:"
            precedes(f"{parent_prefix}{parent_artifact}", event_id, "artefact lineage")
        metadata = row.get("metadata")
        if kind == "call_scheduled" and isinstance(metadata, dict):
            artifact_id = metadata.get("artifact_id")
            if isinstance(artifact_id, str):
                prefix = "code-artifact:" if metadata.get("module") == "defensive_code" \
                    else "artifact:"
                precedes(f"{prefix}{artifact_id}", event_id, "audit input")
            parent_id = metadata.get("parent_artifact_id")
            if isinstance(parent_id, str):
                prefix = "code-artifact:" if metadata.get("module") == "defensive_code" \
                    else "artifact:"
                precedes(f"{prefix}{parent_id}", event_id, "revision input")
            module, round_no = metadata.get("module"), metadata.get("round")
            if module == "whole_loop" and row.get("role") == "whole_loop_reviser" \
                    and isinstance(metadata.get("branch_id"), str) \
                    and type(round_no) is int and round_no > 0:
                precedes(
                    f"whole-loop-audit:{metadata['branch_id']}:{round_no - 1}",
                    event_id, "whole-loop gate before revision",
                )
            if module == "defensive_text" and row.get("role") == "reviser" \
                    and isinstance(parent_id, str) and type(round_no) is int \
                    and round_no > 0:
                other = [candidate for candidate in vendors if candidate != row.get("provider")]
                if len(other) == 1:
                    prior_audit_call = "def-audit-" + run_api.stable_id(
                        parent_id, other[0], round_no - 1,
                    )
                    precedes(
                        f"def-audit-result:{prior_audit_call}", event_id,
                        "defensive gate before revision",
                    )
            if module == "ledger" and isinstance(metadata.get("episode_id"), str):
                precedes(
                    f"ledger-truth:{metadata['episode_id']}", event_id,
                    "ledger truth before reviewer allocation",
                )
        call_id = row.get("call_id")
        if kind in {"audit_decision", "defensive_audit", "ledger_outcome"} \
                and isinstance(call_id, str):
            precedes(f"complete:{call_id}", event_id, "derived call outcome")
        artifact_id = row.get("artifact_id")
        if kind in {"dcl_result", "audit_decision"} and isinstance(artifact_id, str):
            precedes(f"artifact:{artifact_id}", event_id, "offline artefact decision")
        if kind == "ledger_outcome" and isinstance(row.get("episode_id"), str):
            precedes(
                f"ledger-truth:{row['episode_id']}", event_id,
                "ledger truth allocation",
            )
        if kind == "defensive_metrics" and isinstance(artifact_id, str):
            precedes(f"artifact:{artifact_id}", event_id, "defensive metric input")
        if kind == "whole_loop_audit" and isinstance(artifact_id, str):
            precedes(f"artifact:{artifact_id}", event_id, "whole-loop audit artefact")
            reused = row.get("reused_core_call_id")
            if isinstance(reused, str):
                precedes(f"complete:{reused}", event_id, "reused core audit")
            elif type(row.get("round")) is int and row.get("round") > 0 \
                    and isinstance(row.get("branch_id"), str):
                audit_call = "whole-loop-audit-" + run_api.stable_id(
                    row["branch_id"], row["round"],
                )
                precedes(f"complete:{audit_call}", event_id, "whole-loop audit outcome")
        if kind == "whole_loop_end" and isinstance(row.get("branch_id"), str) \
                and type(row.get("revisions")) is int:
            precedes(
                f"whole-loop-audit:{row['branch_id']}:{row['revisions']}",
                event_id, "whole-loop terminal gate",
            )
            if isinstance(row.get("final_artifact_id"), str):
                precedes(
                    f"artifact:{row['final_artifact_id']}", event_id,
                    "whole-loop final artefact",
                )
        if kind == "defensive_loop_end" and isinstance(row.get("final_artifact_id"), str):
            precedes(
                f"artifact:{row['final_artifact_id']}", event_id,
                "defensive final artefact",
            )
            if type(row.get("revisions")) is int and isinstance(row.get("generator_vendor"), str):
                other = [candidate for candidate in vendors
                         if candidate != row["generator_vendor"]]
                if len(other) == 1:
                    audit_call = "def-audit-" + run_api.stable_id(
                        row["final_artifact_id"], other[0], row["revisions"],
                    )
                    precedes(
                        f"def-audit-result:{audit_call}", event_id,
                        "defensive terminal audit",
                    )
        if kind == "defensive_code_loop_end" \
                and isinstance(row.get("final_artifact_id"), str):
            precedes(
                f"code-artifact:{row['final_artifact_id']}", event_id,
                "defensive-code final artefact",
            )

    # Stable order and de-duplication make repeated scoring byte-identical.
    return sorted(set(errors))
