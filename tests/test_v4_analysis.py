from __future__ import annotations

from tests.test_v4_helpers import FIXTURE

from analyse import _ablation_report, build_report
from cluster_inference import holm_adjust
from schema import load_dataset


def test_holm_adjustment_is_monotone_and_machine_readable():
    adjusted = holm_adjust({"a": 0.01, "b": 0.03, "c": 0.20})
    assert adjusted == {"a": 0.03, "b": 0.06, "c": 0.20}


def test_registered_ablation_contrasts_interaction_and_holm_exist():
    rows = []
    for task_no in range(3):
        for dcl in ("D0", "D1", "D2"):
            for constitution in ("C0", "C1", "C2"):
                base = 0.2 + 0.1 * task_no
                d = {"D0": 0.0, "D1": 0.1, "D2": 0.3}[dcl]
                c = {"C0": 0.0, "C1": 0.1, "C2": 0.2}[constitution]
                interaction = 0.2 if dcl == "D2" and constitution == "C2" else 0.0
                rows.append({
                    "task_id": f"T{task_no}", "dcl_level": dcl,
                    "constitution_level": constitution,
                    "correct_gate": base + d + c + interaction,
                    "false_block": max(0.0, 0.2 - d / 2),
                    "recall_script": d, "recall_tool": d / 2,
                    "recall_model": c, "cost_usd": d + c, "latency_s": 1 + d + c,
                })
    report = _ablation_report(rows, draws=20, seed=9)
    assert set(report["dcl"]) == {"D2_minus_D0", "D2_minus_D1"}
    assert set(report["constitution"]) == {
        "C1_minus_C0", "C2_minus_C1", "C2_minus_C0"}
    assert "D2-D0_by_C2-C0" in report["c_by_d_interaction"]
    endpoint = report["constitution"]["C2_minus_C0"]["correct_gate"]
    assert endpoint["confirmatory"] is True
    assert endpoint["multiplicity_family"] == "ablation_constitution_confirmatory"
    assert endpoint["p_holm"] is not None
    assert report["dcl"]["D2_minus_D0"]["recall_tool"]["p_holm"] is not None


def test_co_primary_decision_and_ledger_multiplicity_are_explicit():
    report = build_report(load_dataset(FIXTURE), draws=20, seed=5)
    decision = report["primary_decision"]
    assert "two-sided 95%" in decision["correct_gate_superiority"]["method"]
    assert "one-sided 95%" in decision["clean_false_block_noninferiority"]["method"]
    assert decision["clean_false_block_noninferiority"]["margin"] == 0.05
    assert decision["joint_intersection_union_passed"] is False
    ledger = report["ledger_utility"]["reviewer_clustered_contrasts"]
    primary = ledger["E2_minus_E0"]
    for name in ("accuracy", "restricted_time_to_correct_s"):
        assert primary[name]["multiplicity_family"] == "ledger_primary_endpoints"
        assert primary[name]["p_holm"] is not None
