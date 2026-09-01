from __future__ import annotations

import copy

import pytest

from tests.test_v4_helpers import FIXTURE

from analyse import build_report, canonical_json
from metrics import (audit_run_rows, cost_latency_metrics, defensive_rows,
                     ledger_metrics, primary_task_cells, revision_rows)
from schema import Dataset, load_dataset


def test_primary_endpoints_have_registered_direction_and_denominators():
    report = build_report(load_dataset(FIXTURE), draws=100, seed=7)
    assert report["primary_2x2"]["recall"]["estimate"] == pytest.approx(0.5)
    assert report["primary_2x2"]["correct_gate"]["estimate"] == pytest.approx(0.125)
    assert report["primary_2x2"]["micro_recall"]["estimate"] == pytest.approx(0.5)
    assert report["primary_2x2"]["false_block"]["estimate"] == pytest.approx(0.25)
    assert report["primary_2x2"]["precision"]["estimate"] == pytest.approx(-0.25)
    assert report["primary_2x2"]["precision"]["left"] == pytest.approx(1.0)
    assert report["primary_2x2"]["precision"]["right"] == pytest.approx(0.75)


def test_repeats_are_collapsed_before_task_cell_inference():
    ds = load_dataset(FIXTURE)
    cells = primary_task_cells(ds)
    assert len(cells) == 8  # two tasks x four cells, not sixteen calls
    cell = next(c for c in cells if c["task_id"] == "T-DEF"
                and c["generator_vendor"] == "B" and c["auditor_vendor"] == "A")
    assert cell["n_runs"] == 2
    assert cell["recall"] == pytest.approx(0.5)


def test_revision_loop_counts_corrections_and_defensive_overhead_separately():
    ds = load_dataset(FIXTURE)
    revisions = {r["revision_id"]: r for r in revision_rows(ds)}
    assert revisions["REV-P0"]["net_correction"] == 0
    assert revisions["REV-P2"]["corrected"] == 1
    assert revisions["REV-P2"]["introduced"] == 0
    defensive = {r["defensive_arm"]: r for r in defensive_rows(ds)}
    assert defensive["P1"]["audit_overhead_ratio"] == pytest.approx(1.0)
    assert defensive["P2"]["audit_overhead_ratio"] == pytest.approx(0.25)
    assert defensive["P2"]["wrapper_delta"] == 3
    assert defensive["P2"]["retry_delta"] == 2
    assert defensive["P2"]["exception_handler_delta"] == 3
    assert defensive["P2"]["dependency_delta"] == 1
    assert defensive["P2"]["complexity_delta"] == pytest.approx(2.0)
    assert defensive["P2"]["quality_score"] > defensive["P1"]["quality_score"]


def test_ledger_utility_and_calibration_are_real_endpoints():
    report = build_report(load_dataset(FIXTURE), draws=20, seed=4)
    ledger = report["ledger_utility"]["descriptive"]
    assert ledger["E2"]["accuracy"] == 1.0
    assert ledger["E2"]["mean_seconds"] < ledger["E0"]["mean_seconds"]
    assert report["calibration"]["finding"]["n"] == 5
    assert 0 <= report["calibration"]["finding"]["brier"] <= 1


def test_missing_price_is_unavailable_not_zero():
    original = load_dataset(FIXTURE)
    tables = copy.deepcopy(original.tables)
    tables["audit_runs"][0]["price_key"] = None
    ds = Dataset(original.root, original.manifest, tables, original.price_table)
    costs = cost_latency_metrics(ds, audit_run_rows(ds))["audit"]
    assert costs["n_missing_cost"] == 1
    assert costs["mean_cost_usd"] is not None


def test_all_missing_prices_never_report_zero_total():
    original = load_dataset(FIXTURE)
    tables = copy.deepcopy(original.tables)
    for run in tables["audit_runs"]:
        run["price_key"] = None
    ds = Dataset(original.root, original.manifest, tables, original.price_table)
    costs = cost_latency_metrics(ds, audit_run_rows(ds))["audit"]
    assert costs["n_missing_cost"] == costs["n"]
    assert costs["total_cost_usd"] is None
    assert costs["mean_cost_usd"] is None


def test_all_block_strategy_exposes_false_block_and_low_precision():
    original = load_dataset(FIXTURE)
    tables = copy.deepcopy(original.tables)
    defects_by_artifact = {}
    for defect in tables["defects"]:
        if defect["gold_status"] == "confirmed":
            defects_by_artifact.setdefault(defect["artifact_id"], defect["defect_id"])
    finding_n = len(tables["findings"])
    matched_runs = {f["audit_run_id"] for f in tables["findings"]}
    for run in tables["audit_runs"]:
        if run["status"] != "ok" or run["audit_run_id"] in matched_runs:
            continue
        run["model_verdict"] = "BLOCKED"
        run["controller_verdict"] = "BLOCKED"
        finding_n += 1
        fid = f"F-ALL-{finding_n}"
        tables["findings"].append({
            "schema_version": "4.0", "finding_id": fid,
            "audit_run_id": run["audit_run_id"], "severity": "BLOCKER",
            "origin": "model",
            "rule": "CA-X-001", "location": "any:1", "status": "alleged",
            "confidence": 0.99, "blocked_scope": True,
        })
        did = defects_by_artifact.get(run["artifact_id"])
        tables["finding_matches"].append({
            "schema_version": "4.0", "match_id": f"M-ALL-{finding_n}",
            "finding_id": fid, "defect_id": did, "label": "true" if did else "false",
            "adjudicator_a": "J1", "adjudicator_b": "J2",
            "adjudicator_a_label": "true" if did else "false",
            "adjudicator_b_label": "true" if did else "false", "agreement": True,
        })
    ds = Dataset(original.root, original.manifest, tables, original.price_table)
    rows = audit_run_rows(ds)
    clean = [r for r in rows if not r["requires_block"]]
    true_n = sum(r["n_true_findings"] for r in rows)
    adj_n = sum(r["n_adjudicated_findings"] for r in rows)
    assert sum(r["false_block"] for r in clean) / len(clean) == 1.0
    assert true_n / adj_n < 0.5
    assert sum(r["n_caught"] for r in rows) / sum(r["n_gold"] for r in rows) > 0.8


def test_report_is_byte_reproducible_for_fixed_seed():
    ds = load_dataset(FIXTURE)
    a = canonical_json(build_report(ds, draws=50, seed=99))
    b = canonical_json(build_report(ds, draws=50, seed=99))
    assert a == b


def test_machine_claim_gate_cannot_overstate_current_stdlib_analysis():
    report = build_report(load_dataset(FIXTURE), draws=20, seed=3)
    assert report["claim_gate"]["primary_estimator_implemented"] is True
    assert report["claim_gate"]["glmm_sensitivity_implemented"] is False
    assert report["claim_gate"]["bootstrap_draws_sufficient"] is False
    assert report["claim_gate"]["dispatch_freeze_validated"] is False
    assert report["claim_gate"]["confirmatory_dispatch_ready"] is False
    assert report["primary_decision"]["joint_intersection_union_passed"] is False
