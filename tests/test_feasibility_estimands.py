from __future__ import annotations

from copy import deepcopy

import pytest

from experiment.v4.feasibility.estimands import fixed_weight_2x2
from experiment.v4.feasibility.schema import validate_json_schema
from experiment.v4.feasibility.tasks import ARTIFACT_SCHEMA, AUDIT_SCHEMA


def _row(task: str, generator: str, auditor: str, stratum: str, value: float) -> dict:
    return {
        "task_id": task, "generator_vendor": generator,
        "auditor_vendor": auditor, "artifact_type": stratum,
        "correct_gate": value,
    }


def test_fixed_2x2_collapses_unbalanced_repeats_before_fixed_stratum_weighting() -> None:
    rows = []
    values = {("A", "A"): 0.2, ("A", "B"): 0.8, ("B", "A"): 0.4, ("B", "B"): 0.6}
    for stratum in ("clean", "seeded", "ambiguous"):
        for (generator, auditor), value in values.items():
            rows.append(_row("T1", generator, auditor, stratum, value))
            if generator == "A" and auditor == "A":
                # Extra repeats in one cell must not give that cell more weight
                # than any other direction in the 2x2 contrast.
                rows.extend([_row("T1", generator, auditor, stratum, value)] * 4)
    result = fixed_weight_2x2(
        rows, task_ids=["T1"], vendors=["A", "B"],
        strata=("clean", "seeded", "ambiguous"), outcome="correct_gate", seed=1,
    )
    assert result["incomplete_tasks"] == {}
    assert result["task_cells"]["T1"] == pytest.approx({
        "A->A": 0.2, "A->B": 0.8, "B->A": 0.4, "B->B": 0.6,
    })
    assert result["contrasts"]["cross_minus_same"]["estimate"] == pytest.approx(0.2)
    assert result["contrasts"]["A->B_minus_A->A"]["estimate"] == pytest.approx(0.6)
    assert result["contrasts"]["B->A_minus_B->B"]["estimate"] == pytest.approx(-0.2)


def test_fixed_2x2_marks_missing_stratum_without_realised_row_reweighting() -> None:
    rows = [
        _row("T1", generator, auditor, stratum, 1.0)
        for generator in ("A", "B") for auditor in ("A", "B")
        for stratum in ("clean", "seeded", "ambiguous")
    ]
    rows.pop()
    result = fixed_weight_2x2(
        rows, task_ids=["T1"], vendors=["A", "B"],
        strata=("clean", "seeded", "ambiguous"), outcome="correct_gate", seed=1,
    )
    assert result["complete_task_ids"] == []
    assert result["incomplete_tasks"] == {"T1": ["B->B/ambiguous"]}
    assert result["contrasts"]["cross_minus_same"]["estimate"] is None


def test_local_schema_validator_rejects_extra_wrong_nonfinite_and_out_of_range() -> None:
    valid = {
        "result": 1.0, "unit": "mg", "method": "mean",
        "evidence": ["M-A"], "checks": [], "limitations": [],
    }
    assert validate_json_schema(valid, ARTIFACT_SCHEMA) == []
    extra = {**valid, "unexpected": True}
    assert any("additional properties" in error for error in validate_json_schema(extra, ARTIFACT_SCHEMA))
    wrong_item = {**valid, "evidence": [123]}
    assert any("evidence[0]" in error for error in validate_json_schema(wrong_item, ARTIFACT_SCHEMA))
    nonfinite = {**valid, "result": float("nan")}
    assert any("result" in error for error in validate_json_schema(nonfinite, ARTIFACT_SCHEMA))

    audit = {
        "verdict": "PASS", "confidence": 1.1,
        "checks_performed": [], "findings": [],
    }
    assert any("maximum" in error for error in validate_json_schema(audit, AUDIT_SCHEMA))
    bool_number = deepcopy(valid)
    bool_number["result"] = True
    assert any("result" in error for error in validate_json_schema(bool_number, ARTIFACT_SCHEMA))
