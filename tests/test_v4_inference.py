from __future__ import annotations

import copy
import random

import pytest

from tests.test_v4_helpers import V4  # noqa: F401  (installs v4 on sys.path)

from cluster_inference import (clustered_ratio_difference, factorial_2x2_contrast,
                               factorial_v_by_v_contrast, infer_task_contrasts)


def rows_fixture():
    rows = []
    values = {
        "T1": {("A", "A"): 0.0, ("A", "B"): 1.0,
               ("B", "A"): 1.0, ("B", "B"): 0.0},
        "T2": {("A", "A"): 0.5, ("A", "B"): 0.5,
               ("B", "A"): 0.5, ("B", "B"): 0.5},
    }
    for task, cells in values.items():
        for (g, a), value in cells.items():
            rows.append({"task_id": task, "generator_vendor": g,
                         "auditor_vendor": a, "y": value})
    return rows


def test_known_2x2_task_contrast():
    report = factorial_2x2_contrast(
        rows_fixture(), "y", ["A", "B"], ["A", "B"], draws=100, seed=3)
    assert report["estimate"] == pytest.approx(0.5)
    assert report["n_tasks"] == 2
    assert report["task_contrasts"] == {"T1": 1.0, "T2": 0.0}


def test_vendor_relabelling_and_row_order_do_not_change_estimate():
    rows = rows_fixture()
    renamed = copy.deepcopy(rows)
    for row in renamed:
        row["generator_vendor"] = {"A": "B", "B": "A"}[row["generator_vendor"]]
        row["auditor_vendor"] = {"A": "B", "B": "A"}[row["auditor_vendor"]]
    random.Random(1).shuffle(renamed)
    a = factorial_2x2_contrast(rows, "y", ["A", "B"], ["A", "B"], draws=20, seed=2)
    b = factorial_2x2_contrast(renamed, "y", ["A", "B"], ["A", "B"], draws=20, seed=2)
    assert a["estimate"] == b["estimate"]
    assert a["ci95_bootstrap"] == b["ci95_bootstrap"]


def test_known_three_vendor_task_standardised_contrast():
    rows = []
    for task, shift in (("T1", 0.0), ("T2", 0.2)):
        for generator in "ABC":
            for auditor in "ABC":
                value = shift + (1.0 if generator != auditor else 0.0)
                rows.append({"task_id": task, "generator_vendor": generator,
                             "auditor_vendor": auditor, "y": value})
    report = factorial_v_by_v_contrast(
        rows, "y", list("ABC"), list("ABC"), draws=100, seed=9)
    assert report["estimate"] == pytest.approx(1.0)
    assert report["vendor_count"] == 3
    assert report["claim_scope"] == "included_vendors_only"
    assert report["direction_contrasts"]["T1"] == pytest.approx(
        {"A": 1.0, "B": 1.0, "C": 1.0})


def test_three_vendor_contrast_rejects_incomplete_panel():
    rows = [{"task_id": "T1", "generator_vendor": g,
             "auditor_vendor": a, "y": 1.0}
            for g in "ABC" for a in "ABC"][:-1]
    with pytest.raises(ValueError, match="incomplete VxV"):
        factorial_v_by_v_contrast(
            rows, "y", list("ABC"), list("ABC"), draws=0, seed=1)


def test_duplicate_repeat_rows_are_rejected_as_pseudoreplication():
    rows = rows_fixture()
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError, match="duplicate task-cell"):
        factorial_2x2_contrast(rows, "y", ["A", "B"], ["A", "B"], draws=0, seed=1)


def test_incomplete_task_cell_is_rejected():
    rows = rows_fixture()[:-1]
    with pytest.raises(ValueError, match="incomplete 2x2"):
        factorial_2x2_contrast(rows, "y", ["A", "B"], ["A", "B"], draws=0, seed=1)


def test_bootstrap_is_task_clustered_and_seed_reproducible():
    values = {"large": 10.0, "small": 0.0}
    a = infer_task_contrasts(values, draws=100, seed=19)
    b = infer_task_contrasts(values, draws=100, seed=19)
    assert a["ci95_bootstrap"] == b["ci95_bootstrap"]
    assert a["estimate"] == 5.0
    assert a["n_tasks"] == 2


def test_clustered_ratio_difference_recomputes_denominators():
    same = {"T1": (1, 10), "T2": (9, 10)}
    cross = {"T1": (5, 10), "T2": (10, 10)}
    report = clustered_ratio_difference(same, cross, draws=100, seed=5)
    assert report["left"] == pytest.approx(0.5)
    assert report["right"] == pytest.approx(0.75)
    assert report["estimate"] == pytest.approx(0.25)
