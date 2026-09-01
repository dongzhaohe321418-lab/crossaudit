#!/usr/bin/env python3
"""Task-clustered inference primitives shared by real and simulated studies."""
from __future__ import annotations

import itertools
import math
import random
import statistics
from collections import defaultdict
from statistics import NormalDist
from typing import Any, Iterable


def _mean(values: Iterable[float]) -> float:
    xs = list(values)
    if not xs:
        raise ValueError("mean of an empty estimand")
    return statistics.fmean(xs)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    """Holm family-wise adjustment with the required monotonic step-down."""
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for i, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (total - i) * p))
        adjusted[name] = running
    return adjusted


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("quantile of an empty sample")
    if len(sorted_values) == 1:
        return sorted_values[0]
    x = (len(sorted_values) - 1) * q
    lo, hi = math.floor(x), math.ceil(x)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] * (hi - x) + sorted_values[hi] * (x - lo)


def _signflip_p(values: list[float], seed: int, draws: int = 20_000) -> float:
    """Two-sided sign-flip sensitivity test over independent task contrasts."""
    observed = abs(_mean(values))
    n = len(values)
    if n <= 20:
        total = 1 << n
        extreme = 0
        for mask in range(total):
            value = abs(sum(x if mask & (1 << i) else -x for i, x in enumerate(values)) / n)
            extreme += value >= observed - 1e-15
        return extreme / total
    rng = random.Random(seed)
    extreme = 0
    for _ in range(draws):
        value = abs(sum(x if rng.random() < 0.5 else -x for x in values) / n)
        extreme += value >= observed - 1e-15
    return (extreme + 1) / (draws + 1)


def infer_task_contrasts(values: dict[str, float], *, draws: int, seed: int,
                         compute_signflip: bool = True) -> dict[str, Any]:
    """Inference for one already-collapsed contrast per independent task."""
    if not values:
        return {"n_tasks": 0, "estimate": None, "se": None, "ci95_bootstrap": None,
                "one_sided95_lower_bootstrap": None,
                "one_sided95_upper_bootstrap": None,
                "ci95_normal": None, "ci90_normal": None, "signflip_p": None}
    task_ids = sorted(values)
    xs = [float(values[t]) for t in task_ids]
    estimate = _mean(xs)
    se = statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
    z95, z90 = NormalDist().inv_cdf(0.975), NormalDist().inv_cdf(0.95)
    normal95 = [estimate - z95 * se, estimate + z95 * se]
    normal90 = [estimate - z90 * se, estimate + z90 * se]
    boot_ci = None
    one_sided_lower = None
    one_sided_upper = None
    if draws:
        rng = random.Random(seed)
        boot = []
        for _ in range(draws):
            boot.append(_mean(values[task_ids[rng.randrange(len(task_ids))]]
                              for _ in task_ids))
        boot.sort()
        boot_ci = [_quantile(boot, 0.025), _quantile(boot, 0.975)]
        one_sided_lower = _quantile(boot, 0.05)
        one_sided_upper = _quantile(boot, 0.95)
    return {
        "n_tasks": len(xs),
        "estimate": estimate,
        "se": se,
        "ci95_bootstrap": boot_ci,
        "one_sided95_lower_bootstrap": one_sided_lower,
        "one_sided95_upper_bootstrap": one_sided_upper,
        "ci95_normal": normal95,
        "ci90_normal": normal90,
        "signflip_p": _signflip_p(xs, seed + 1) if draws and compute_signflip else None,
        "task_contrasts": values,
    }


def factorial_2x2_contrast(rows: list[dict[str, Any]], outcome: str,
                           generator_vendors: list[str], auditor_vendors: list[str],
                           *, draws: int, seed: int, allow_incomplete: bool = False,
                           compute_signflip: bool = True) -> dict[str, Any]:
    """Cross-vendor minus same-vendor contrast after collapsing within task.

    ``rows`` must contain one value per task and 2x2 cell.  Repeated model calls
    must be averaged before entering this function; treating them as rows would
    be pseudoreplication, so duplicate cells are rejected.
    """
    if set(generator_vendors) != set(auditor_vendors) or len(generator_vendors) != 2:
        raise ValueError("2x2 cross-vendor contrast requires the same two vendor labels")
    cells: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    scheduled: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        task = row["task_id"]
        key = (row["generator_vendor"], row["auditor_vendor"])
        if key in scheduled[task]:
            raise ValueError(f"duplicate task-cell row for {task!r}, {key!r}")
        scheduled[task].add(key)
        value = row.get(outcome)
        if value is None:
            continue
        cells[task][key] = float(value)
    expected = set(itertools.product(generator_vendors, auditor_vendors))
    contrasts: dict[str, float] = {}
    incomplete: list[str] = []
    for task, planned in sorted(scheduled.items()):
        if planned != expected:
            raise ValueError(
                f"outcome {outcome!r} has incomplete 2x2 scheduled task {task!r}")
        got = cells[task]
        if set(got) != expected:
            incomplete.append(task)
            continue
        cross = _mean(v for (g, a), v in got.items() if g != a)
        same = _mean(v for (g, a), v in got.items() if g == a)
        contrasts[task] = cross - same
    # A task with any non-null cell must be complete for this estimand.  Tasks
    # with all-null outcomes (e.g. recall on clean controls) never enter cells.
    if incomplete and not allow_incomplete:
        raise ValueError(f"outcome {outcome!r} has incomplete 2x2 tasks: {incomplete}")
    report = infer_task_contrasts(
        contrasts, draws=draws, seed=seed, compute_signflip=compute_signflip)
    report.update({"outcome": outcome, "estimand": "cross_vendor_minus_same_vendor",
                   "n_scheduled_tasks": len(scheduled),
                   "n_incomplete_tasks": len(incomplete),
                   "incomplete_task_ids": incomplete})
    return report


def paired_level_contrast(rows: list[dict[str, Any]], *, task_field: str,
                          factor: str, low: str, high: str, outcome: str,
                          draws: int, seed: int) -> dict[str, Any]:
    """High-minus-low paired contrast, averaging repeats inside task and level."""
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get(factor) not in {low, high} or row.get(outcome) is None:
            continue
        grouped[row[task_field]][row[factor]].append(float(row[outcome]))
    contrasts = {}
    for task, levels in grouped.items():
        if low in levels and high in levels:
            contrasts[task] = _mean(levels[high]) - _mean(levels[low])
    report = infer_task_contrasts(contrasts, draws=draws, seed=seed)
    report.update({"outcome": outcome, "factor": factor,
                   "contrast": f"{high}_minus_{low}"})
    return report


def paired_interaction_contrast(rows: list[dict[str, Any]], *, task_field: str,
                                factor_a: str, a_low: str, a_high: str,
                                factor_b: str, b_low: str, b_high: str,
                                outcome: str, draws: int, seed: int) -> dict[str, Any]:
    """Difference-in-differences, with one interaction value per task."""
    grouped: dict[str, dict[tuple[str, str], list[float]]] = defaultdict(
        lambda: defaultdict(list))
    allowed_a, allowed_b = {a_low, a_high}, {b_low, b_high}
    for row in rows:
        if row.get(factor_a) not in allowed_a or row.get(factor_b) not in allowed_b:
            continue
        if row.get(outcome) is None:
            continue
        grouped[row[task_field]][(row[factor_a], row[factor_b])].append(float(row[outcome]))
    expected = set(itertools.product(allowed_a, allowed_b))
    contrasts = {}
    for task, cells in grouped.items():
        if set(cells) != expected:
            continue
        values = {key: _mean(xs) for key, xs in cells.items()}
        at_high_b = values[(a_high, b_high)] - values[(a_low, b_high)]
        at_low_b = values[(a_high, b_low)] - values[(a_low, b_low)]
        contrasts[task] = at_high_b - at_low_b
    report = infer_task_contrasts(contrasts, draws=draws, seed=seed)
    report.update({"outcome": outcome, "factor_a": factor_a, "factor_b": factor_b,
                   "contrast": (f"({a_high}-{a_low})@{b_high}_minus_"
                                f"({a_high}-{a_low})@{b_low}")})
    return report


def clustered_ratio(task_counts: dict[str, tuple[float, float]], *, draws: int,
                    seed: int) -> dict[str, Any]:
    """Ratio-of-sums with a task-cluster percentile bootstrap."""
    usable = {k: v for k, v in task_counts.items() if v[1] >= 0}
    denominator = sum(v[1] for v in usable.values())
    estimate = sum(v[0] for v in usable.values()) / denominator if denominator else None
    ci = None
    if draws and usable and denominator:
        ids = sorted(usable)
        rng = random.Random(seed)
        boot = []
        for _ in range(draws):
            picks = [ids[rng.randrange(len(ids))] for _ in ids]
            den = sum(usable[t][1] for t in picks)
            if den:
                boot.append(sum(usable[t][0] for t in picks) / den)
        if boot:
            boot.sort()
            ci = [_quantile(boot, 0.025), _quantile(boot, 0.975)]
    return {"n_tasks": len(usable), "numerator": sum(v[0] for v in usable.values()),
            "denominator": denominator, "estimate": estimate, "ci95_bootstrap": ci}


def clustered_ratio_difference(left: dict[str, tuple[float, float]],
                               right: dict[str, tuple[float, float]], *, draws: int,
                               seed: int, label: str = "right_minus_left") -> dict[str, Any]:
    """Difference between two ratio-of-sums estimands, resampling whole tasks."""
    ids = sorted(set(left) | set(right))

    def ratio(which: dict[str, tuple[float, float]], picks: list[str]) -> float | None:
        den = sum(which.get(t, (0.0, 0.0))[1] for t in picks)
        return (sum(which.get(t, (0.0, 0.0))[0] for t in picks) / den) if den else None

    l0, r0 = ratio(left, ids), ratio(right, ids)
    estimate = r0 - l0 if l0 is not None and r0 is not None else None
    ci = None
    if draws and estimate is not None:
        rng = random.Random(seed)
        boot = []
        for _ in range(draws):
            picks = [ids[rng.randrange(len(ids))] for _ in ids]
            lv, rv = ratio(left, picks), ratio(right, picks)
            if lv is not None and rv is not None:
                boot.append(rv - lv)
        if boot:
            boot.sort()
            ci = [_quantile(boot, 0.025), _quantile(boot, 0.975)]
    return {"n_tasks": len(ids), "estimate": estimate, "ci95_bootstrap": ci,
            "estimand": label, "left": l0, "right": r0}
