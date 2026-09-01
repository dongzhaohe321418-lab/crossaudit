"""Frozen task-level estimands for the v4 feasibility 2x2 design."""
from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from typing import Any, Iterable


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def _cluster_report(task_values: dict[str, float], seed: int, draws: int = 5000) -> dict[str, Any]:
    ids = sorted(task_values)
    estimate = statistics.fmean(task_values.values()) if ids else None
    interval = None
    if len(ids) > 1 and draws:
        rng = random.Random(seed)
        sampled = [
            statistics.fmean(task_values[ids[rng.randrange(len(ids))]] for _ in ids)
            for _ in range(draws)
        ]
        interval = [_quantile(sampled, 0.025), _quantile(sampled, 0.975)]
    return {
        "n_tasks": len(ids),
        "estimate": estimate,
        "ci95_task_bootstrap": interval,
        "task_values": {key: task_values[key] for key in ids},
        "warning": "descriptive feasibility interval; convenience tasks" if ids else None,
    }


def fixed_weight_2x2(
    rows: Iterable[dict[str, Any]], *, task_ids: list[str], vendors: list[str],
    strata: tuple[str, ...], outcome: str, seed: int,
) -> dict[str, Any]:
    """Collapse repeats, weight strata equally, then estimate the four 2x2 cells.

    Missing directions or strata make the affected task incomplete.  We never
    substitute a realised-row average for a prospectively fixed-weight cell.
    """
    if len(vendors) != 2 or len(set(vendors)) != 2:
        raise ValueError("fixed_weight_2x2 requires exactly two distinct vendors")
    if not strata or len(set(strata)) != len(strata):
        raise ValueError("strata must be a non-empty unique tuple")
    vendor_a, vendor_b = vendors
    grouped: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("task_id")), str(row.get("generator_vendor")),
            str(row.get("auditor_vendor")), str(row.get("artifact_type")),
        )
        value = row.get(outcome)
        if key[0] not in task_ids or key[1] not in vendors or key[2] not in vendors \
                or key[3] not in strata:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) \
                and math.isfinite(float(value)):
            grouped[key].append(float(value))

    cell_task_values: dict[str, dict[str, float]] = {
        f"{generator}->{auditor}": {}
        for generator in vendors for auditor in vendors
    }
    incomplete: dict[str, list[str]] = {}
    task_cells: dict[str, dict[str, float]] = {}
    for task_id in task_ids:
        missing: list[str] = []
        cells: dict[str, float] = {}
        for generator in vendors:
            for auditor in vendors:
                stratum_means: list[float] = []
                label = f"{generator}->{auditor}"
                for stratum in strata:
                    values = grouped.get((task_id, generator, auditor, stratum), [])
                    if not values:
                        missing.append(f"{label}/{stratum}")
                    else:
                        # Repeats are collapsed within artefact/auditor first.
                        stratum_means.append(statistics.fmean(values))
                if len(stratum_means) == len(strata):
                    cells[label] = statistics.fmean(stratum_means)
        if missing:
            incomplete[task_id] = sorted(missing)
            continue
        task_cells[task_id] = cells
        for label, value in cells.items():
            cell_task_values[label][task_id] = value

    aa = f"{vendor_a}->{vendor_a}"
    ab = f"{vendor_a}->{vendor_b}"
    ba = f"{vendor_b}->{vendor_a}"
    bb = f"{vendor_b}->{vendor_b}"
    contrasts: dict[str, dict[str, float]] = {
        "cross_minus_same": {},
        f"{ab}_minus_{aa}": {},
        f"{ba}_minus_{bb}": {},
        f"generator_main_{vendor_b}_minus_{vendor_a}": {},
        f"auditor_main_{vendor_b}_minus_{vendor_a}": {},
        "generator_by_auditor_interaction": {},
    }
    for task_id, cells in task_cells.items():
        contrasts["cross_minus_same"][task_id] = (
            0.5 * (cells[ab] + cells[ba]) - 0.5 * (cells[aa] + cells[bb])
        )
        contrasts[f"{ab}_minus_{aa}"][task_id] = cells[ab] - cells[aa]
        contrasts[f"{ba}_minus_{bb}"][task_id] = cells[ba] - cells[bb]
        contrasts[f"generator_main_{vendor_b}_minus_{vendor_a}"][task_id] = (
            0.5 * (cells[ba] + cells[bb]) - 0.5 * (cells[aa] + cells[ab])
        )
        contrasts[f"auditor_main_{vendor_b}_minus_{vendor_a}"][task_id] = (
            0.5 * (cells[ab] + cells[bb]) - 0.5 * (cells[aa] + cells[ba])
        )
        contrasts["generator_by_auditor_interaction"][task_id] = (
            cells[bb] - cells[ba] - cells[ab] + cells[aa]
        )

    return {
        "outcome": outcome,
        "vendors": vendors,
        "strata": list(strata),
        "weighting": "equal across frozen strata after within-artifact/auditor repeat collapse",
        "complete_task_ids": sorted(task_cells),
        "incomplete_tasks": dict(sorted(incomplete.items())),
        "task_cells": {task: task_cells[task] for task in sorted(task_cells)},
        "four_cells": {
            label: _cluster_report(values, seed + index)
            for index, (label, values) in enumerate(sorted(cell_task_values.items()))
        },
        "contrasts": {
            label: _cluster_report(values, seed + 100 + index)
            for index, (label, values) in enumerate(contrasts.items())
        },
    }


def natural_available_gold_2x2(
    rows: Iterable[dict[str, Any]], *, task_ids: list[str], vendors: list[str],
    outcome: str, seed: int,
) -> dict[str, Any]:
    """Report the natural stratum separately, with no missing-cell reweighting."""
    result = fixed_weight_2x2(
        rows, task_ids=task_ids, vendors=vendors, strata=("natural",),
        outcome=outcome, seed=seed,
    )
    result["availability_note"] = (
        "Only tasks with all four natural-output cells and deterministic gold are included; "
        "missing cells are reported, never reweighted."
    )
    return result
