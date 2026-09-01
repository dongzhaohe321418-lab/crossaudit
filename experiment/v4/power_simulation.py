#!/usr/bin/env python3
"""Task-clustered power simulation for the v4 co-primary endpoints.

This is a design tool, not an observed-data effect-size oracle.  It explores a
grid of plausible correct-gate and false-block effects and calls the same 2x2 contrast
function used by ``analyse.py``.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from cluster_inference import factorial_2x2_contrast


@dataclass(frozen=True)
class PowerConfig:
    n_tasks: int = 120
    clean_fraction: float = 0.33
    generation_repeats: int = 2
    audit_repeats: int = 3
    baseline_correct_gate: float = 0.70
    cross_correct_gate_effect: float = 0.08
    baseline_false_block: float = 0.10
    cross_false_block_effect: float = 0.00
    false_block_margin: float = 0.05
    task_base_icc: float = 0.20
    repeat_correlation: float = 0.50
    cross_direction_heterogeneity: float = 0.0
    generator_main_effect: float = 0.0
    auditor_main_effect: float = 0.0
    domain_imbalance: float = 0.0
    technical_missingness: float = 0.0
    differential_missingness: float = 0.0
    nominal_clean_contamination: float = 0.0
    simulations: int = 10_000
    analysis_bootstrap_draws: int = 5_000
    alpha: float = 0.05
    seed: int = 20260831


REGISTERED_GRID_AXES: dict[str, tuple[float | int, ...]] = {
    "n_tasks": (120, 180),
    "baseline_correct_gate": (0.60, 0.70, 0.80),
    "cross_correct_gate_effect": (0.0, 0.05, 0.08, 0.10),
    "baseline_false_block": (0.02, 0.05, 0.10, 0.20),
    "task_base_icc": (0.10, 0.20, 0.30),
    "repeat_correlation": (0.20, 0.50, 0.80),
    "cross_direction_heterogeneity": (0.0, 0.04),
    "generator_main_effect": (0.0, 0.04),
    "auditor_main_effect": (0.0, 0.04),
    "domain_imbalance": (0.0, 0.20),
    "technical_missingness": (0.0, 0.02, 0.05),
    "differential_missingness": (0.0, 0.02),
    "nominal_clean_contamination": (0.0, 0.05),
}


def registered_scenario_configs(base: PowerConfig, mode: str = "oat",
                                scenario_index: int | None = None) -> list[PowerConfig]:
    """Materialise the frozen axes as OAT stress tests or a full Cartesian grid."""
    if mode not in {"oat", "full"}:
        raise ValueError("registered grid mode must be 'oat' or 'full'")
    if mode == "full":
        names = tuple(REGISTERED_GRID_AXES)
        total = math.prod(len(REGISTERED_GRID_AXES[name]) for name in names)
        if scenario_index is None:
            raise ValueError(
                f"full grid has {total} scenarios; pass --scenario-index to shard it")
        if not 0 <= scenario_index < total:
            raise ValueError(f"scenario_index must be in [0, {total})")
        products = itertools.product(*(REGISTERED_GRID_AXES[name] for name in names))
        values = next(itertools.islice(products, scenario_index, scenario_index + 1))
        return [replace(base, **dict(zip(names, values)))]
    scenarios = [base]
    for name, values in REGISTERED_GRID_AXES.items():
        for value in values:
            if value != getattr(base, name):
                scenarios.append(replace(base, **{name: value}))
    # Keep deterministic order but remove a central value duplicated through
    # numerically equal float/int representations.
    unique: dict[str, PowerConfig] = {}
    for scenario in scenarios:
        key = json.dumps(asdict(scenario), sort_keys=True)
        unique[key] = scenario
    result = list(unique.values())
    if scenario_index is not None:
        if not 0 <= scenario_index < len(result):
            raise ValueError(f"scenario_index must be in [0, {len(result)})")
        return [result[scenario_index]]
    return result


def _check(c: PowerConfig) -> None:
    if c.n_tasks < 4:
        raise ValueError("n_tasks must be >=4")
    if c.generation_repeats < 1 or c.audit_repeats < 1 or c.simulations < 1:
        raise ValueError("repeat and simulation counts must be positive")
    for name in ("clean_fraction", "baseline_correct_gate", "baseline_false_block", "alpha",
                 "task_base_icc", "repeat_correlation"):
        value = getattr(c, name)
        if not 0 < value < 1:
            raise ValueError(f"{name} must lie strictly between 0 and 1")
    if c.false_block_margin <= 0:
        raise ValueError("false_block_margin must be positive")
    for name in ("domain_imbalance", "technical_missingness", "differential_missingness",
                 "nominal_clean_contamination"):
        if not 0 <= getattr(c, name) < 1:
            raise ValueError(f"{name} must lie in [0, 1)")
    if c.analysis_bootstrap_draws < 1:
        raise ValueError("analysis_bootstrap_draws must be positive")


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def _logistic(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _clamp(p: float) -> float:
    return min(1 - 1e-9, max(1e-9, p))


def _observed_correlated_mean(rng: random.Random, p: float, n: int, rho: float,
                              missingness: float) -> float | None:
    """Beta-binomial repeat correlation plus explicit technical missingness."""
    if rho > 0:
        concentration = 1 / rho - 1
        p = rng.betavariate(max(1e-9, p * concentration),
                            max(1e-9, (1 - p) * concentration))
    observed = [float(rng.random() < p) for _ in range(n)
                if rng.random() >= missingness]
    return statistics.fmean(observed) if observed else None


def simulate_task_cells(config: PowerConfig, *, seed: int,
                        correct_gate_effect: float | None = None,
                        false_block_effect: float | None = None) -> list[dict[str, Any]]:
    """Generate already-collapsed task cells with realistic within-task repeats."""
    _check(config)
    correct_gate_effect = (config.cross_correct_gate_effect if correct_gate_effect is None
                           else correct_gate_effect)
    false_block_effect = (config.cross_false_block_effect if false_block_effect is None
                          else false_block_effect)
    rng = random.Random(seed)
    n_clean = max(1, min(config.n_tasks - 1, round(config.n_tasks * config.clean_fraction)))
    rows = []
    vendors = ("A", "B")
    repeats = config.generation_repeats * config.audit_repeats
    latent_sd = math.sqrt(config.task_base_icc * math.pi ** 2
                          / (3 * (1 - config.task_base_icc)))
    clean_correct_same = 1 - config.baseline_false_block
    defect_correct_same = ((config.baseline_correct_gate
                            - config.clean_fraction * clean_correct_same)
                           / (1 - config.clean_fraction))
    defect_cross_effect = ((correct_gate_effect
                            + config.clean_fraction * false_block_effect)
                           / (1 - config.clean_fraction))
    for i in range(config.n_tasks):
        nominal_clean = i < n_clean
        contaminated = nominal_clean and rng.random() < config.nominal_clean_contamination
        clean = nominal_clean and not contaminated
        if rng.random() < 1 / 3 + 2 * config.domain_imbalance / 3:
            domain = 0
        else:
            domain = 1 + int(rng.random() >= 0.5)
        # One latent difficulty per task induces correlation across all four cells.
        u_gate = rng.gauss(0, latent_sd) + (domain - 1) * 0.03
        u_false = rng.gauss(0, latent_sd) + (domain - 1) * 0.03
        p_gate_same = _logistic(_logit(_clamp(defect_correct_same)) + u_gate)
        p_false_same = _logistic(_logit(config.baseline_false_block) + u_false)
        for gv in vendors:
            for av in vendors:
                cross = gv != av
                direction = (config.cross_direction_heterogeneity / 2
                             if (gv, av) == ("A", "B") else
                             -config.cross_direction_heterogeneity / 2
                             if (gv, av) == ("B", "A") else 0.0)
                mains = ((config.generator_main_effect / 2 if gv == "B" else
                          -config.generator_main_effect / 2)
                         + (config.auditor_main_effect / 2 if av == "B" else
                            -config.auditor_main_effect / 2))
                p_gate = _clamp(p_gate_same + mains
                                + (defect_cross_effect + direction if cross else 0.0))
                p_false = _clamp(p_false_same + mains
                                 + (false_block_effect - direction if cross else 0.0))
                missingness = min(0.999, max(
                    0.0, config.technical_missingness
                    + (config.differential_missingness if cross else 0.0)))
                if clean:
                    false_block = _observed_correlated_mean(
                        rng, p_false, repeats, config.repeat_correlation, missingness)
                    correct_gate = None if false_block is None else 1.0 - false_block
                else:
                    false_block = None
                    correct_gate = _observed_correlated_mean(
                        rng, p_gate, repeats,
                        config.repeat_correlation, missingness)
                rows.append({
                    "task_id": f"T-{i:04d}", "generator_vendor": gv,
                    "auditor_vendor": av,
                    "correct_gate": correct_gate, "false_block": false_block,
                    "eligible_false_block": clean, "domain": domain,
                })
    return rows


def _success(report: dict[str, Any], direction: str, threshold: float,
             interval_name: str) -> bool:
    interval = report[interval_name]
    if not interval:
        return False
    if direction == "greater":
        return interval[0] > threshold
    if direction == "less":
        return interval[1] < threshold
    raise ValueError(direction)


def estimate_one(config: PowerConfig, *, seed: int, correct_gate_effect: float | None = None,
                 false_block_effect: float | None = None) -> dict[str, Any]:
    rows = simulate_task_cells(config, seed=seed, correct_gate_effect=correct_gate_effect,
                               false_block_effect=false_block_effect)
    correct_gate = factorial_2x2_contrast(
        rows, "correct_gate", ["A", "B"], ["A", "B"],
        draws=config.analysis_bootstrap_draws, seed=seed + 1,
        allow_incomplete=True, compute_signflip=False)
    false_block = factorial_2x2_contrast(
        [row for row in rows if row["eligible_false_block"]],
        "false_block", ["A", "B"], ["A", "B"],
        draws=config.analysis_bootstrap_draws, seed=seed + 2,
        allow_incomplete=True, compute_signflip=False)
    return {"correct_gate": correct_gate, "false_block": false_block}


def simulate_power(config: PowerConfig) -> dict[str, Any]:
    _check(config)
    alt_gate, alt_fb, joint = 0, 0, 0
    null_gate_reject, boundary_fb_reject = 0, 0
    gate_widths, fb_widths = [], []
    gate_coverage, fb_coverage = 0, 0
    analysis_failures = 0
    normal_gate_reject, normal_fb_reject = 0, 0
    for i in range(config.simulations):
        seed = config.seed + i * 10_007
        alt = estimate_one(config, seed=seed)
        r_ok = _success(alt["correct_gate"], "greater", 0.0, "ci95_bootstrap")
        f_upper = alt["false_block"]["one_sided95_upper_bootstrap"]
        f_ok = f_upper is not None and f_upper < config.false_block_margin
        analysis_failures += (alt["correct_gate"]["estimate"] is None
                              or alt["false_block"]["estimate"] is None)
        alt_gate += r_ok
        alt_fb += f_ok
        joint += r_ok and f_ok
        r_ci = alt["correct_gate"]["ci95_bootstrap"]
        f_ci = alt["false_block"]["ci95_bootstrap"]
        if r_ci:
            gate_widths.append(r_ci[1] - r_ci[0])
            gate_coverage += r_ci[0] <= config.cross_correct_gate_effect <= r_ci[1]
        if f_ci:
            fb_widths.append(f_ci[1] - f_ci[0])
            fb_coverage += f_ci[0] <= config.cross_false_block_effect <= f_ci[1]
        normal_gate_reject += _success(
            alt["correct_gate"], "greater", 0.0, "ci95_normal")
        normal_fb_reject += _success(
            alt["false_block"], "less", config.false_block_margin, "ci90_normal")

        # Superiority type-I is assessed at zero.  Non-inferiority type-I is
        # assessed at the margin boundary, not at zero (which is the alternative).
        null_r = estimate_one(config, seed=seed + 1, correct_gate_effect=0.0,
                              false_block_effect=config.cross_false_block_effect)
        boundary_f = estimate_one(config, seed=seed + 2,
                                  correct_gate_effect=config.cross_correct_gate_effect,
                                  false_block_effect=config.false_block_margin)
        null_gate_reject += _success(null_r["correct_gate"], "greater", 0.0,
                                     "ci95_bootstrap")
        boundary_upper = boundary_f["false_block"]["one_sided95_upper_bootstrap"]
        boundary_fb_reject += (boundary_upper is not None
                               and boundary_upper < config.false_block_margin)

    n = config.simulations
    return {
        "config": asdict(config),
        "analysis": ("task-level 2x2 cross-minus-same with whole-task percentile bootstrap; "
                     "correct-gate superiority uses two-sided 95%, clean-FBR "
                     "non-inferiority uses upper one-sided 95%"),
        "correct_gate_superiority_power": alt_gate / n,
        "false_block_noninferiority_power": alt_fb / n,
        "joint_power": joint / n,
        "correct_gate_type1_at_zero": null_gate_reject / n,
        "false_block_type1_at_margin": boundary_fb_reject / n,
        "correct_gate_ci95_coverage": gate_coverage / n,
        "false_block_ci95_coverage": fb_coverage / n,
        "mean_correct_gate_ci95_width": statistics.fmean(gate_widths) if gate_widths else None,
        "mean_false_block_ci95_width": statistics.fmean(fb_widths) if fb_widths else None,
        "analysis_failure_rate": analysis_failures / n,
        "normal_vs_bootstrap": {
            "correct_gate_normal_rejection_rate": normal_gate_reject / n,
            "false_block_normal_rejection_rate": normal_fb_reject / n,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-tasks", default="120",
                    help="comma-separated task counts for the power grid")
    ap.add_argument("--simulations", type=int, default=10_000)
    ap.add_argument("--analysis-bootstrap-draws", type=int, default=5_000)
    ap.add_argument("--correct-gate-effect", type=float, default=0.08)
    ap.add_argument("--false-block-effect", type=float, default=0.0)
    ap.add_argument("--false-block-margin", type=float, default=0.05)
    ap.add_argument("--registered-grid", choices=("oat", "full"),
                    help="run every frozen axis one-at-a-time or its full Cartesian product")
    ap.add_argument("--scenario-index", type=int,
                    help="run one zero-based registered-grid scenario (required for full)")
    ap.add_argument("--allow-small-simulations", action="store_true",
                    help="unit-test/debug escape hatch; output is not confirmatory")
    ap.add_argument("--seed", type=int, default=20260831)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        if args.simulations < 10_000 and not args.allow_small_simulations:
            raise ValueError(
                "confirmatory power requires >=10000 simulations per scenario; "
                "use --allow-small-simulations only for tests")
        sizes = [int(x) for x in args.n_tasks.split(",") if x.strip()]
        base_configs = [PowerConfig(
            n_tasks=n, simulations=args.simulations,
            analysis_bootstrap_draws=args.analysis_bootstrap_draws,
            cross_correct_gate_effect=args.correct_gate_effect,
            cross_false_block_effect=args.false_block_effect,
            false_block_margin=args.false_block_margin, seed=args.seed + i * 1_000_003)
                        for i, n in enumerate(sizes)]
        configs = ([scenario for base in base_configs
                    for scenario in registered_scenario_configs(
                        base, args.registered_grid, args.scenario_index)]
                   if args.registered_grid else base_configs)
        reports = [simulate_power(replace(config, seed=config.seed + i * 1_000_003))
                   for i, config in enumerate(configs)]
    except ValueError as exc:
        print(f"POWER SIMULATION REFUSED: {exc}", file=sys.stderr)
        return 2
    payload = {
        "schema_version": "4.0",
        "confirmatory_minimum_simulations_per_scenario": 10_000,
        "confirmatory": args.simulations >= 10_000,
        "scenario_grid_metadata": {
            "registered_axes": {k: list(v) for k, v in REGISTERED_GRID_AXES.items()},
            "construction": args.registered_grid or "explicit_n_tasks_only",
            "scenario_index": args.scenario_index,
            "n_scenarios": len(reports),
            "full_cartesian_scenario_count": math.prod(
                len(values) for values in REGISTERED_GRID_AXES.values()),
            "covers_direction_heterogeneity_vendor_auditor_effects_domain_imbalance_"
            "missingness_and_nominal_clean_contamination": bool(args.registered_grid),
        },
        "grid": reports,
    }
    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    Path(args.out).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
