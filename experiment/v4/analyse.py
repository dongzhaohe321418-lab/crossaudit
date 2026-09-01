#!/usr/bin/env python3
"""Run every registered CrossAudit v4 endpoint from one validated export."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from cluster_inference import (clustered_ratio_difference, factorial_2x2_contrast,
                               holm_adjust, paired_interaction_contrast,
                               paired_level_contrast)
from metrics import (audit_run_rows, calibration_metrics, condition_summaries,
                     cost_latency_metrics, defensive_rows, ledger_metrics,
                     mean_or_none, primary_task_cells, revision_rows,
                     stability_metrics, whole_loop_rows)
from schema import DataValidationError, Dataset, load_dataset
from validate_dataset import validate_dataset


def _ratio_contrast(cells: list[dict[str, Any]], numerator: str, denominator: str,
                    *, draws: int, seed: int, label: str) -> dict[str, Any]:
    same: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    cross: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for row in cells:
        target = cross if row["cross_vendor"] else same
        target[row["task_id"]][0] += row[numerator]
        target[row["task_id"]][1] += row[denominator]
    return clustered_ratio_difference(
        {k: tuple(v) for k, v in same.items()}, {k: tuple(v) for k, v in cross.items()},
        draws=draws, seed=seed, label=label)


def _revision_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "mean_net_correction": None, "total_corrected": 0,
                "total_introduced": 0, "escalation_rate": None}
    return {
        "n": len(rows),
        "mean_net_correction": statistics.fmean(r["net_correction"] for r in rows),
        "mean_net_correction_rate": statistics.fmean(r["net_correction_rate"] for r in rows),
        "total_corrected": sum(r["corrected"] for r in rows),
        "total_introduced": sum(r["introduced"] for r in rows),
        "escalation_rate": statistics.fmean(r["escalated"] for r in rows),
        "mean_cost_usd": mean_or_none([r["cost_usd"] for r in rows]),
        "mean_latency_s": statistics.fmean(r["latency_s"] for r in rows),
        "rows": rows,
    }


def _whole_loop_summary(rows: list[dict[str, Any]],
                        revision_events: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n_episodes": 0, "rows": [], "revision_event_rows": revision_events}
    return {
        "n_episodes": len(rows),
        "mean_resolved_fraction": mean_or_none([r["resolved_fraction"] for r in rows]),
        "final_acceptability_rate": mean_or_none(
            [r["final_acceptable_blind"] for r in rows]),
        "mean_new_defects": statistics.fmean(r["introduced"] for r in rows),
        "mean_unnecessary_changes": statistics.fmean(
            r["unnecessary_change_count"] for r in rows),
        "mean_net_correction": statistics.fmean(r["net_correction"] for r in rows),
        "mean_revisions": statistics.fmean(r["n_revisions"] for r in rows),
        "escalation_rate": statistics.fmean(r["escalated"] for r in rows),
        "mean_cost_usd": mean_or_none([r["cost_usd"] for r in rows]),
        "mean_latency_s": statistics.fmean(r["latency_s"] for r in rows),
        "mean_human_minutes": statistics.fmean(r["human_minutes"] for r in rows),
        "unit": "one initial-to-final loop episode",
        "rows": rows,
        "revision_event_rows": revision_events,
    }


def _ablation_report(run_rows: list[dict[str, Any]], *, draws: int, seed: int,
                     generator_vendors: list[str] | None = None,
                     auditor_vendors: list[str] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"dcl": {}, "constitution": {}, "c_by_d_interaction": {}}
    confirmatory = ("correct_gate", "false_block", "recall_script", "recall_tool",
                    "recall_model")
    descriptive = ("cost_usd", "latency_s")

    # Reconstruct the registered cross-minus-same contrast inside every
    # task×Constitution×DCL arm before contrasting factor levels.  This prevents
    # a vendor main effect from being mistaken for an ablation effect.
    if generator_vendors is not None and auditor_vendors is not None:
        expected = {(g, a) for g in generator_vendors for a in auditor_vendors}
        grouped: dict[tuple[str, str, str], dict[tuple[str, str], list[dict[str, Any]]]] = (
            defaultdict(lambda: defaultdict(list)))
        for row in run_rows:
            if (row["generator_vendor"] in generator_vendors
                    and row["auditor_vendor"] in auditor_vendors):
                grouped[(row["task_id"], row["dcl_level"], row["constitution_level"])][
                    (row["generator_vendor"], row["auditor_vendor"])].append(row)
        standardized = []
        for (task_id, dcl, constitution), cells in sorted(grouped.items()):
            if set(cells) != expected:
                continue
            arm = {"task_id": task_id, "dcl_level": dcl,
                   "constitution_level": constitution}
            for outcome in confirmatory + descriptive:
                values = {}
                for direction, rows in cells.items():
                    observed = [r[outcome] for r in rows if r.get(outcome) is not None]
                    if observed:
                        values[direction] = statistics.fmean(observed)
                if set(values) == expected:
                    cross = statistics.fmean(
                        value for (g, a), value in values.items() if g != a)
                    same = statistics.fmean(
                        value for (g, a), value in values.items() if g == a)
                    arm[outcome] = cross - same
                else:
                    arm[outcome] = None
            standardized.append(arm)
        run_rows = standardized
        out["estimand"] = "factor-level difference in task-standardised cross-minus-same"
    else:
        out["estimand"] = "paired task arm mean (test helper / non-vendor subset)"

    def annotate_holm(family: dict[str, dict[str, dict[str, Any]]], family_name: str) -> None:
        raw = {}
        for contrast, endpoints in family.items():
            for outcome, report in endpoints.items():
                if outcome in confirmatory and report.get("signflip_p") is not None:
                    raw[f"{contrast}|{outcome}"] = report["signflip_p"]
        adjusted = holm_adjust(raw)
        for contrast, endpoints in family.items():
            for outcome, report in endpoints.items():
                key = f"{contrast}|{outcome}"
                report["multiplicity_family"] = family_name if outcome in confirmatory else None
                report["p_holm"] = adjusted.get(key)
                report["confirmatory"] = outcome in confirmatory

    # Registered contrasts.  D0->D1 and D2->D3 are not silently promoted to
    # confirmatory analyses; they may be added later under an explicit amendment.
    for i, (low, high) in enumerate((("D0", "D2"), ("D1", "D2"))):
        if not any(r["dcl_level"] == low for r in run_rows) or not any(
                r["dcl_level"] == high for r in run_rows):
            continue
        out["dcl"][f"{high}_minus_{low}"] = {
            outcome: paired_level_contrast(
                run_rows, task_field="task_id", factor="dcl_level", low=low, high=high,
                outcome=outcome, draws=draws, seed=seed + i * 20 + j)
            for j, outcome in enumerate(confirmatory + descriptive)
        }
    for i, (low, high) in enumerate((("C0", "C1"), ("C1", "C2"), ("C0", "C2"))):
        if not any(r["constitution_level"] == low for r in run_rows) or not any(
                r["constitution_level"] == high for r in run_rows):
            continue
        out["constitution"][f"{high}_minus_{low}"] = {
            outcome: paired_level_contrast(
                run_rows, task_field="task_id", factor="constitution_level",
                low=low, high=high, outcome=outcome, draws=draws,
                seed=seed + 100 + i * 20 + j)
            for j, outcome in enumerate(confirmatory + descriptive)
        }
    interaction_possible = all(any(r["dcl_level"] == d and r["constitution_level"] == c
                                   for r in run_rows)
                               for d in ("D0", "D2") for c in ("C0", "C2"))
    if interaction_possible:
        out["c_by_d_interaction"]["D2-D0_by_C2-C0"] = {
            outcome: paired_interaction_contrast(
                run_rows, task_field="task_id", factor_a="dcl_level", a_low="D0",
                a_high="D2", factor_b="constitution_level", b_low="C0", b_high="C2",
                outcome=outcome, draws=draws, seed=seed + 500 + j)
            for j, outcome in enumerate(confirmatory + descriptive)
        }
    annotate_holm(out["dcl"], "ablation_dcl_confirmatory")
    annotate_holm(out["constitution"], "ablation_constitution_confirmatory")
    annotate_holm(out["c_by_d_interaction"], "ablation_c_by_d_confirmatory")
    return out


def _defensive_report(rows: list[dict[str, Any]], *, draws: int, seed: int
                      ) -> dict[str, Any]:
    rows = [{**row, "session_task_cluster":
             f"{row['generator_session_id']}::{row['task_id']}"} for row in rows]
    summaries = {}
    for arm in ("P0", "P1", "P2"):
        subset = [r for r in rows if r["defensive_arm"] == arm]
        if subset:
            summaries[arm] = {
                "n": len(subset),
                **{k: mean_or_none([r[k] for r in subset]) for k in (
                    "word_delta", "loc_delta", "file_delta", "docs_word_delta",
                    "assertion_delta", "disclaimer_delta", "wrapper_delta", "retry_delta",
                    "exception_handler_delta", "dependency_delta", "complexity_delta",
                    "audit_overhead_ratio",
                    "quality_score", "novelty_score", "heldout_score",
                    "blind_final_acceptable")},
            }
    contrasts = {}
    outcomes = ("word_delta", "loc_delta", "disclaimer_delta", "wrapper_delta",
                "retry_delta", "exception_handler_delta", "dependency_delta",
                "complexity_delta", "audit_overhead_ratio", "quality_score", "novelty_score",
                "heldout_score", "blind_final_acceptable")
    for i, (low, high) in enumerate((("P0", "P1"), ("P1", "P2"), ("P0", "P2"))):
        if low not in summaries or high not in summaries:
            continue
        contrasts[f"{high}_minus_{low}"] = {
            outcome: paired_level_contrast(
                rows, task_field="session_task_cluster", factor="defensive_arm",
                low=low, high=high,
                outcome=outcome, draws=draws, seed=seed + i * 20 + j)
            for j, outcome in enumerate(outcomes)
        }
    primary_outcomes = {"audit_overhead_ratio", "quality_score", "heldout_score"}
    raw = {}
    for contrast in ("P1_minus_P0", "P2_minus_P0"):
        for outcome, report in contrasts.get(contrast, {}).items():
            if outcome in primary_outcomes and report.get("signflip_p") is not None:
                raw[f"{contrast}|{outcome}"] = report["signflip_p"]
    adjusted = holm_adjust(raw)
    for contrast, endpoints in contrasts.items():
        for outcome, report in endpoints.items():
            key = f"{contrast}|{outcome}"
            report["confirmatory"] = contrast in {"P1_minus_P0", "P2_minus_P0"} \
                and outcome in primary_outcomes
            report["multiplicity_family"] = (
                "defensive_primary_policy_endpoints" if report["confirmatory"] else None)
            report["p_holm"] = adjusted.get(key)
    return {
        "summaries": summaries, "contrasts": contrasts, "rows": rows,
        "primary_interpretation_rule": (
            "defensive production requires increased compliance/defensive share without "
            "commensurate blinded quality or held-out improvement"),
        "cluster_unit": "generator_session_id crossed with task_id",
    }


def _ledger_inference(ds: Dataset, *, draws: int, seed: int) -> dict[str, Any]:
    assignments = {a["assignment_id"]: a for a in ds.rows("ledger_assignments")}
    rows = []
    for o in ds.rows("ledger_outcomes"):
        a = assignments[o["assignment_id"]]
        rows.append({
            "reviewer_id": a["reviewer_id"], "episode_id": a["episode_id"],
            "surface": a["surface"], "accuracy": float(o["decision_correct"]),
            "restricted_time_to_correct_s": (
                o["time_to_decision_s"] if o["decision_correct"]
                else o["registered_time_cap_s"]),
            "provenance_score": o["provenance_score"],
            "tamper_detection": float(o["tamper_flag"] == o["tamper_truth"]),
            "first_defective_commit_accuracy": (
                float(o["first_defective_commit_correct"])
                if o["first_defective_commit_correct"] is not None else None),
            "rule_version_accuracy": (float(o["rule_version_correct"])
                                      if o["rule_version_correct"] is not None else None),
            "review_burden_score": o["review_burden_score"],
        })
    reviewer_contrasts = {}
    episode_sensitivity = {}
    outcomes = ("accuracy", "restricted_time_to_correct_s", "provenance_score",
                "tamper_detection", "first_defective_commit_accuracy",
                "rule_version_accuracy", "review_burden_score")
    for i, (low, high) in enumerate((("E0", "E1"), ("E0", "E2"), ("E1", "E2"))):
        if not rows:
            continue
        key = f"{high}_minus_{low}"
        reviewer_contrasts[key] = {
            outcome: paired_level_contrast(
                rows, task_field="reviewer_id", factor="surface", low=low, high=high,
                outcome=outcome, draws=draws, seed=seed + i * 20 + j)
            for j, outcome in enumerate(outcomes)
        }
        episode_sensitivity[key] = {
            outcome: paired_level_contrast(
                rows, task_field="episode_id", factor="surface", low=low, high=high,
                outcome=outcome, draws=draws, seed=seed + 500 + i * 20 + j)
            for j, outcome in enumerate(outcomes)
        }
    primary_key = "E2_minus_E0"
    if primary_key in reviewer_contrasts:
        family = reviewer_contrasts[primary_key]
        primary_endpoints = {"accuracy", "restricted_time_to_correct_s"}
        raw = {name: report["signflip_p"] for name, report in family.items()
               if name in primary_endpoints and report.get("signflip_p") is not None}
        adjusted = holm_adjust(raw)
        for name, report in family.items():
            report["multiplicity_family"] = (
                "ledger_primary_endpoints" if name in primary_endpoints else None)
            report["p_holm"] = adjusted.get(name)
            report["confirmatory"] = name in primary_endpoints
    secondary_raw = {}
    for key in ("E1_minus_E0", "E2_minus_E1"):
        for name, report in reviewer_contrasts.get(key, {}).items():
            if name in {"accuracy", "restricted_time_to_correct_s"} \
                    and report.get("signflip_p") is not None:
                secondary_raw[f"{key}|{name}"] = report["signflip_p"]
    secondary_adjusted = holm_adjust(secondary_raw)
    for key, family in reviewer_contrasts.items():
        if key == primary_key:
            continue
        for name, report in family.items():
            family_key = f"{key}|{name}"
            report["multiplicity_family"] = (
                "ledger_secondary_contrasts" if family_key in secondary_raw else None)
            report["p_holm"] = secondary_adjusted.get(family_key)
            report["confirmatory"] = False
    return {
        "descriptive": ledger_metrics(ds),
        "reviewer_clustered_contrasts": reviewer_contrasts,
        "episode_cluster_sensitivity": episode_sensitivity,
        "primary_contrast": primary_key,
        "survival_estimand": (
            "restricted mean time to correct decision; incorrect/unresolved censored at cap"),
    }


def _primary_inference(cells: list[dict[str, Any]], primary_plan: dict[str, Any],
                       *, draws: int, seed: int) -> dict[str, Any]:
    reports = {}
    outcomes = ("correct_gate", "false_block", "recall", "operational_nonadmission",
                "cost_usd", "latency_s", "failure_rate")
    for i, outcome in enumerate(outcomes):
        subset = cells
        if outcome == "false_block":
            subset = [row for row in cells if row["eligible_false_block"]]
        elif outcome == "recall":
            subset = [row for row in cells if row["eligible_recall"]]
        reports[outcome] = factorial_2x2_contrast(
            subset, outcome, primary_plan["generator_vendors"],
            primary_plan["auditor_vendors"], draws=draws, seed=seed + i,
            allow_incomplete=True)
    reports["precision"] = _ratio_contrast(
        cells, "n_true_findings", "n_adjudicated_findings", draws=draws,
        seed=seed + 20, label="cross_minus_same_precision")
    reports["micro_recall"] = _ratio_contrast(
        cells, "n_caught", "n_gold", draws=draws,
        seed=seed + 21, label="cross_minus_same_micro_recall")
    return reports


def _missingness_sensitivity(ds: Dataset, run_rows: list[dict[str, Any]], *,
                             draws: int, seed: int) -> dict[str, Any]:
    """Registered extreme-case treatment of technical failures.

    Observed semantic outcomes stay missing in the primary estimator.  These
    deterministic imputations reveal how conclusions move under the two
    directionally adverse assignments and under all-failures-incorrect.
    """
    scenarios = {
        "cross_failures_incorrect_same_failures_correct": (0.0, 1.0),
        "cross_failures_correct_same_failures_incorrect": (1.0, 0.0),
        "all_failures_incorrect": (0.0, 0.0),
    }
    out = {}
    for i, (name, (cross_correct, same_correct)) in enumerate(scenarios.items()):
        imputed = [dict(row) for row in run_rows]
        for row in imputed:
            if row["status"] == "ok":
                continue
            assigned_correct = cross_correct if row["cross_vendor"] else same_correct
            row["correct_gate"] = assigned_correct
            if not row["requires_block"]:
                row["false_block"] = 1.0 - assigned_correct
        cells = primary_task_cells(ds, imputed)
        reports = _primary_inference(cells, ds.manifest["primary"],
                                     draws=draws, seed=seed + i * 100)
        out[name] = {"correct_gate": reports["correct_gate"],
                     "false_block": reports["false_block"]}
    return {
        "n_failed_calls": sum(row["status"] != "ok" for row in run_rows),
        "extreme_case_scenarios": out,
        "inverse_probability_weighting": {
            "implemented": False,
            "reason": "requires a separately frozen pre-treatment missingness model",
        },
    }


def build_report(ds: Dataset, *, draws: int | None = None, seed: int | None = None
                 ) -> dict[str, Any]:
    validation = validate_dataset(ds)
    draws = ds.manifest["bootstrap"]["draws"] if draws is None else draws
    seed = ds.manifest["bootstrap"]["seed"] if seed is None else seed
    if draws < 0:
        raise ValueError("bootstrap draws must be non-negative")
    runs = audit_run_rows(ds)
    cells = primary_task_cells(ds, runs)
    p = ds.manifest["primary"]

    primary = _primary_inference(cells, p, draws=draws, seed=seed)
    margin = p["false_block_noninferiority_margin"]
    correct_gate_pass = (primary["correct_gate"]["ci95_bootstrap"] is not None
                         and primary["correct_gate"]["ci95_bootstrap"][0] > 0)
    fbr_pass = (primary["false_block"]["one_sided95_upper_bootstrap"] is not None
                and primary["false_block"]["one_sided95_upper_bootstrap"] < margin)
    primary_decision = {
        "correct_gate_superiority": {
            "method": "lower bound of two-sided 95% whole-task bootstrap CI > 0",
            "passed": correct_gate_pass,
            "lower_bound": primary["correct_gate"]["ci95_bootstrap"][0]
            if primary["correct_gate"]["ci95_bootstrap"] else None,
        },
        "clean_false_block_noninferiority": {
            "method": "upper one-sided 95% whole-task bootstrap bound < margin",
            "passed": fbr_pass, "margin": margin,
            "upper_bound": primary["false_block"]["one_sided95_upper_bootstrap"],
        },
        "joint_intersection_union_passed": correct_gate_pass and fbr_pass,
        "multiplicity": "intersection-union: both co-primary criteria must pass",
    }

    rev_rows = revision_rows(ds)
    loop_rows = whole_loop_rows(ds)
    def_rows = defensive_rows(ds)
    report = {
        "schema_version": ds.manifest["schema_version"],
        "study_id": ds.manifest["study_id"],
        "provenance": {"hashes": ds.manifest["hashes"], "bootstrap": {
            "seed": seed, "draws": draws}, "price_table_currency": ds.price_table["currency"]},
        "validation": validation,
        "primary_2x2": primary,
        "primary_decision": primary_decision,
        "primary_task_cells": cells,
        "conditions": condition_summaries(runs),
        "ablations": _ablation_report(
            runs, draws=draws, seed=seed + 1000,
            generator_vendors=p["generator_vendors"],
            auditor_vendors=p["auditor_vendors"]),
        "revision_loop": _whole_loop_summary(loop_rows, rev_rows),
        "defensive_programming": _defensive_report(def_rows, draws=draws, seed=seed + 2000),
        "stability": stability_metrics(ds, runs),
        "calibration": calibration_metrics(ds),
        "ledger_utility": _ledger_inference(ds, draws=draws, seed=seed + 3000),
        "cost_latency": cost_latency_metrics(ds, runs),
        "technical_missingness": _missingness_sensitivity(
            ds, runs, draws=draws, seed=seed + 4000),
        "claim_gate": {
            "statistical_joint_pass": primary_decision["joint_intersection_union_passed"],
            "estimator": ("registered task-standardised cross-minus-same estimator with "
                          "whole-task percentile bootstrap"),
            "primary_estimator_implemented": True,
            "glmm_sensitivity_implemented": False,
            "bootstrap_draws_sufficient": draws >= 5_000,
            "dispatch_freeze_validated": False,
            "confirmatory_dispatch_ready": False,
            "confirmatory_analysis_ready": (
                draws >= 5_000
                and primary["correct_gate"]["n_incomplete_tasks"] == 0
                and primary["false_block"]["n_incomplete_tasks"] == 0),
            "reason": ("Primary estimator is implemented. Dispatch readiness is separate: "
                       "run validate_dataset.py --dispatch-freeze-root and use at least 5000 "
                       "bootstrap draws. GLMM/g-computation is a non-blocking sensitivity."),
        },
    }
    return report


def canonical_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("--out", required=True)
    ap.add_argument("--draws", type=int)
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()
    try:
        ds = load_dataset(args.dataset)
        report = build_report(ds, draws=args.draws, seed=args.seed)
    except (DataValidationError, ValueError) as exc:
        print(f"ANALYSIS REFUSED: {exc}", file=sys.stderr)
        return 2
    Path(args.out).write_text(canonical_json(report))
    print(canonical_json({"study_id": report["study_id"],
                          "validation": report["validation"],
                          "primary_2x2": report["primary_2x2"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
