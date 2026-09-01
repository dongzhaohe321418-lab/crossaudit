#!/usr/bin/env python3
"""Outcome-free preflight for the prospective CrossAudit v5 design."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


class PreflightError(ValueError):
    """Raised when the design is structurally invalid or not freeze-ready."""


def _get(config: dict[str, Any], dotted: str) -> Any:
    value: Any = config
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


REQUIRED_FREEZE_FIELDS = (
    "human_panels.gold_panel_manifest_sha256",
    "human_panels.matching_panel_manifest_sha256",
    "human_panels.calibration_report_sha256",
    "model_identity.resolved_models_lock_sha256",
    "power.power_report_sha256",
    "freeze.prompt_bundle_sha256",
    "freeze.task_manifest_sha256",
    "freeze.mutation_key_external_commitment",
    "freeze.randomisation_seed_commitment",
    "freeze.opaque_arm_mapping_custodian",
    "freeze.analysis_code_sha256",
    "freeze.table_shells_sha256",
    "freeze.external_timestamp_uri",
    "cost_caps.currency",
    "cost_caps.maximum_money",
    "cost_caps.maximum_input_tokens",
    "cost_caps.maximum_output_tokens",
    "cost_caps.maximum_human_review_hours",
    "cost_caps.maximum_wall_clock_hours",
    "privacy.provider_egress_approval_sha256",
    "privacy.real_task_replay_approval_sha256",
    "dry_run.receipt_sha256",
)


def load_config(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    value = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PreflightError("study configuration must be a mapping")
    return value


def validate_structure(config: dict[str, Any]) -> dict[str, Any]:
    design = config.get("design")
    if not isinstance(design, dict):
        raise PreflightError("missing design mapping")
    generators = design.get("generator_vendor_codes")
    auditors = design.get("auditor_vendor_codes")
    if not isinstance(generators, list) or len(generators) != 3:
        raise PreflightError("exactly three generator vendor codes are required")
    if len(set(generators)) != 3 or auditors != generators:
        raise PreflightError("generator and auditor vendor codes must be identical and unique")
    if design.get("total_pinned_snapshots") != 6:
        raise PreflightError("six pinned snapshots are required")
    if design.get("initial_task_briefs") != 150:
        raise PreflightError("the prospective initial design requires 150 tasks")
    if design.get("maximum_task_briefs_after_blinded_reestimation") != 180:
        raise PreflightError("the blinded expansion ceiling must be 180 tasks")
    if design.get("audit_repeats_per_required_cell") != 3:
        raise PreflightError("every required audit cell must have three repeats")
    if design.get("constitution_repeats") != {"C0": 3, "C1": 3, "C2": 3}:
        raise PreflightError("C0, C1, and C2 must each have three repeats")
    calls = config.get("planned_call_ceiling", {})
    parts = ["principal_generation", "primary_c2_d2_matrix",
             "same_vendor_different_model", "constitution_c0_c1_additions",
             "whole_loop"]
    if any(type(calls.get(name)) is not int or calls[name] < 0 for name in parts):
        raise PreflightError("planned call ceiling has a missing or invalid module")
    if sum(calls[name] for name in parts) != calls.get(
            "total_before_authorised_technical_retries"):
        raise PreflightError("planned call ceiling does not sum to the declared total")
    if config.get("claim_scope") != "included_configurations_only":
        raise PreflightError("population-vendor wording is prohibited")
    return {"structurally_valid": True, "planned_calls": calls["total_before_authorised_technical_retries"]}


def freeze_blockers(config: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_FREEZE_FIELDS
            if _get(config, field) in (None, "", [], {})]


def preflight(path: str | Path) -> dict[str, Any]:
    config = load_config(path)
    report = validate_structure(config)
    blockers = freeze_blockers(config)
    report.update({
        "study_id": config.get("study_id"),
        "status": config.get("status"),
        "freeze_ready": not blockers,
        "blocking_fields": blockers,
    })
    if blockers:
        raise PreflightError(
            "dispatch blocked; unresolved freeze fields: " + ", ".join(blockers))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_config")
    parser.add_argument("--json", action="store_true", help="emit a JSON refusal report")
    args = parser.parse_args()
    try:
        report = preflight(args.study_config)
    except PreflightError as exc:
        if args.json:
            print(json.dumps({"freeze_ready": False, "error": str(exc)}, indent=2))
        else:
            print(f"BLOCKED: {exc}")
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
