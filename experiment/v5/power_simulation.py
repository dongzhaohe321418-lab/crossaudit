#!/usr/bin/env python3
"""Prospective power simulator for the three-vendor CrossAudit v5 design.

The simulator mirrors the independent units and allocation of the registered
draft: three principal generators, natural/clean/mutant artefacts, a complete
3 x 3 principal-auditor matrix, an alternate same-vendor auditor, and three
fresh-context repeats.  It is a design tool and never reads observed v4 or v5
outcomes.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import NormalDist
from typing import Any


@dataclass(frozen=True)
class PowerConfig:
    n_tasks: int = 150
    vendors: tuple[str, ...] = ("A", "B", "C")
    domains: int = 3
    audit_repeats: int = 3
    natural_defect_prevalence: float = 0.50
    baseline_defect_correct_gate: float = 0.68
    baseline_false_block: float = 0.08
    cross_correct_gate_effect: float = 0.08
    cross_false_block_effect: float = 0.00
    same_vendor_alt_correct_gate_effect: float = 0.02
    same_vendor_alt_false_block_effect: float = 0.00
    noninferiority_margin: float = 0.05
    task_icc: float = 0.15
    base_artifact_icc: float = 0.10
    repeat_correlation: float = 0.50
    direction_heterogeneity: float = 0.00
    auditor_effect_spread: float = 0.00
    technical_missingness: float = 0.00
    differential_cross_missingness: float = 0.00
    simulations: int = 10_000
    alpha: float = 0.05
    seed: int = 20260901


SCENARIO_OVERRIDES: dict[str, dict[str, Any]] = {
    "central": {},
    "high_dependence": {"task_icc": 0.30, "base_artifact_icc": 0.20},
    "high_repeat_correlation": {"repeat_correlation": 0.80},
    "direction_reversal": {"direction_heterogeneity": 0.12},
    "auditor_heterogeneity": {"auditor_effect_spread": 0.05},
    "technical_missingness": {
        "technical_missingness": 0.05,
        "differential_cross_missingness": 0.01,
    },
    "low_baseline_accuracy": {"baseline_defect_correct_gate": 0.58},
    "high_false_block": {"baseline_false_block": 0.20},
    "n180": {"n_tasks": 180},
}


def scenario_config(name: str, *, simulations: int | None = None,
                    seed: int | None = None) -> PowerConfig:
    if name not in SCENARIO_OVERRIDES:
        raise ValueError(f"unknown scenario {name!r}")
    config = replace(PowerConfig(), **SCENARIO_OVERRIDES[name])
    if simulations is not None:
        config = replace(config, simulations=simulations)
    if seed is not None:
        config = replace(config, seed=seed)
    _check(config)
    return config


def _check(config: PowerConfig) -> None:
    if config.n_tasks < 30:
        raise ValueError("n_tasks must be >=30 for this task-level design")
    if len(config.vendors) != 3 or len(set(config.vendors)) != 3:
        raise ValueError("the v5 design requires exactly three distinct vendors")
    if config.domains != 3:
        raise ValueError("the v5 design requires three domains")
    if config.audit_repeats != 3:
        raise ValueError("the v5 design requires three audit repeats")
    for name in ("natural_defect_prevalence", "baseline_defect_correct_gate",
                 "baseline_false_block", "repeat_correlation", "alpha"):
        value = getattr(config, name)
        if not 0 < value < 1:
            raise ValueError(f"{name} must be strictly between zero and one")
    if config.task_icc < 0 or config.base_artifact_icc < 0:
        raise ValueError("ICC values must be non-negative")
    if config.task_icc + config.base_artifact_icc >= 0.80:
        raise ValueError("task and base-artifact ICC sum must be below 0.80")
    for name in ("technical_missingness", "differential_cross_missingness"):
        if not 0 <= getattr(config, name) < 1:
            raise ValueError(f"{name} must lie in [0, 1)")
    if config.simulations < 1:
        raise ValueError("simulations must be positive")


def _clamp(value: float) -> float:
    return min(1 - 1e-8, max(1e-8, value))


def _make_room_for_risk_difference(baseline: float, effect: float) -> float:
    """Keep both probabilities in [0,1] without attenuating the risk difference."""
    lower = max(1e-8, -effect + 1e-8)
    upper = min(1 - 1e-8, 1 - effect - 1e-8)
    return min(upper, max(lower, baseline))


def _logit(probability: float) -> float:
    probability = _clamp(probability)
    return math.log(probability / (1 - probability))


def _logistic(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def _latent_sds(config: PowerConfig) -> tuple[float, float]:
    residual = math.pi ** 2 / 3
    denominator = 1 - config.task_icc - config.base_artifact_icc
    return (
        math.sqrt(config.task_icc * residual / denominator),
        math.sqrt(config.base_artifact_icc * residual / denominator),
    )


def _repeat_probability(rng: random.Random, probability: float,
                        correlation: float) -> float:
    if correlation <= 0:
        return probability
    concentration = 1 / correlation - 1
    return rng.betavariate(
        max(1e-7, probability * concentration),
        max(1e-7, (1 - probability) * concentration),
    )


def _collapsed_cell(rng: random.Random, *, probability: float,
                    repeats: int, missingness: float, clean: bool) -> tuple[float, float | None]:
    """Return service-level correct-gate and clean-burden repeat means."""
    probability = _repeat_probability(rng, _clamp(probability), 0.0)
    correct: list[float] = []
    burden: list[float] = []
    for _ in range(repeats):
        if rng.random() < missingness:
            correct.append(0.0)
            if clean:
                burden.append(1.0)
            continue
        event = float(rng.random() < probability)
        if clean:
            burden.append(event)
            correct.append(1.0 - event)
        else:
            correct.append(event)
    return statistics.fmean(correct), statistics.fmean(burden) if clean else None


def _cell_with_repeat_correlation(rng: random.Random, *, probability: float,
                                  config: PowerConfig, missingness: float,
                                  clean: bool) -> tuple[float, float | None]:
    cell_probability = _repeat_probability(
        rng, _clamp(probability), config.repeat_correlation)
    return _collapsed_cell(
        rng, probability=cell_probability, repeats=config.audit_repeats,
        missingness=missingness, clean=clean)


def simulate_task_contrasts(config: PowerConfig, *, seed: int,
                            correct_effect: float | None = None,
                            false_block_effect: float | None = None,
                            include_alternate: bool = True) -> dict[str, list[float]]:
    """Simulate one complete dataset and return one contrast per task."""
    _check(config)
    rng = random.Random(seed)
    correct_effect = (config.cross_correct_gate_effect if correct_effect is None
                      else correct_effect)
    false_block_effect = (config.cross_false_block_effect
                          if false_block_effect is None else false_block_effect)
    task_sd, base_sd = _latent_sds(config)
    vendors = config.vendors
    centered = {vendor: index - (len(vendors) - 1) / 2
                for index, vendor in enumerate(vendors)}
    # Expected fraction clean: the controlled clean third plus the clean share
    # of the natural third.  The controlled mutant third is always defective.
    clean_fraction = (1 + (1 - config.natural_defect_prevalence)) / 3
    defect_cross_effect = (
        correct_effect + clean_fraction * false_block_effect
    ) / (1 - clean_fraction)

    output = {"correct_cross_minus_same": [], "burden_cross_minus_same": [],
              "alt_minus_same_correct": [], "alt_minus_same_burden": []}
    for task_index in range(config.n_tasks):
        domain = task_index % config.domains
        domain_shift = (domain - 1) * 0.08
        task_latent = rng.gauss(0.0, task_sd)
        same_correct: list[float] = []
        cross_correct: list[float] = []
        alt_correct: list[float] = []
        same_burden: list[float] = []
        cross_burden: list[float] = []
        alt_burden: list[float] = []

        for generator in vendors:
            natural_defective = rng.random() < config.natural_defect_prevalence
            artefacts = (("natural", not natural_defective),
                         ("verified_clean", True), ("mutant", False))
            generator_direction = centered[generator] * config.direction_heterogeneity
            for _stratum, clean in artefacts:
                base_latent = rng.gauss(0.0, base_sd)
                if clean:
                    same_probability = _logistic(
                        _logit(config.baseline_false_block)
                        + task_latent + base_latent + domain_shift)
                else:
                    same_probability = _logistic(
                        _logit(config.baseline_defect_correct_gate)
                        + task_latent + base_latent + domain_shift)

                # In the central design, ``cross_correct_gate_effect`` is the
                # marginal risk-difference target, not an uncalibrated latent
                # coefficient.  Bound the shared reference probability before
                # applying the shift so ceiling/floor clipping cannot silently
                # shrink that target.  Heterogeneity scenarios intentionally
                # relax exact calibration and report the realised estimand.
                if config.direction_heterogeneity == 0 and config.auditor_effect_spread == 0:
                    shift = false_block_effect if clean else defect_cross_effect
                    same_probability = _make_room_for_risk_difference(
                        same_probability, shift)

                for auditor in vendors:
                    cross = auditor != generator
                    auditor_shift = centered[auditor] * config.auditor_effect_spread
                    if cross:
                        effect = ((false_block_effect - generator_direction)
                                  if clean else
                                  (defect_cross_effect + generator_direction))
                        probability = _clamp(same_probability + effect + auditor_shift)
                    else:
                        probability = _clamp(same_probability + auditor_shift)
                    missingness = min(0.99, config.technical_missingness
                                      + (config.differential_cross_missingness
                                         if cross else 0.0))
                    correct, burden = _cell_with_repeat_correlation(
                        rng, probability=probability, config=config,
                        missingness=missingness, clean=clean)
                    if cross:
                        cross_correct.append(correct)
                        if burden is not None:
                            cross_burden.append(burden)
                    else:
                        same_correct.append(correct)
                        if burden is not None:
                            same_burden.append(burden)

                if include_alternate:
                    alt_effect = (config.same_vendor_alt_false_block_effect if clean
                                  else config.same_vendor_alt_correct_gate_effect)
                    alt_probability = _clamp(same_probability + alt_effect)
                    correct, burden = _cell_with_repeat_correlation(
                        rng, probability=alt_probability, config=config,
                        missingness=config.technical_missingness, clean=clean)
                    alt_correct.append(correct)
                    if burden is not None:
                        alt_burden.append(burden)

        output["correct_cross_minus_same"].append(
            statistics.fmean(cross_correct) - statistics.fmean(same_correct))
        output["burden_cross_minus_same"].append(
            statistics.fmean(cross_burden) - statistics.fmean(same_burden))
        if include_alternate:
            output["alt_minus_same_correct"].append(
                statistics.fmean(alt_correct) - statistics.fmean(same_correct))
            output["alt_minus_same_burden"].append(
                statistics.fmean(alt_burden) - statistics.fmean(same_burden))
    return output


def _normal_summary(values: list[float], *, alpha: float,
                    one_sided: bool = False) -> dict[str, float | list[float]]:
    estimate = statistics.fmean(values)
    se = statistics.stdev(values) / math.sqrt(len(values))
    critical = NormalDist().inv_cdf(1 - alpha if one_sided else 1 - alpha / 2)
    return {"estimate": estimate, "se": se,
            "interval": [estimate - critical * se, estimate + critical * se]}


def estimate_dataset(contrasts: dict[str, list[float]], *, alpha: float) -> dict[str, Any]:
    return {
        "correct": _normal_summary(
            contrasts["correct_cross_minus_same"], alpha=alpha),
        "burden": _normal_summary(
            contrasts["burden_cross_minus_same"], alpha=alpha, one_sided=True),
        "alt_correct": _normal_summary(
            contrasts["alt_minus_same_correct"], alpha=alpha)
        if contrasts["alt_minus_same_correct"] else None,
    }


def simulate_power(config: PowerConfig) -> dict[str, Any]:
    """Estimate power, boundary type-I error, bias, and interval coverage."""
    _check(config)
    superiority = noninferiority = conjunctive = 0
    superiority_type1 = noninferiority_type1 = 0
    estimates: list[float] = []
    widths: list[float] = []
    intervals: list[list[float]] = []
    alt_estimates: list[float] = []
    for simulation in range(config.simulations):
        base_seed = config.seed + simulation * 10_007
        target = estimate_dataset(simulate_task_contrasts(
            config, seed=base_seed), alpha=config.alpha)
        null_superiority = estimate_dataset(simulate_task_contrasts(
            config, seed=base_seed + 1, correct_effect=0.0,
            include_alternate=False), alpha=config.alpha)
        boundary_noninferiority = estimate_dataset(simulate_task_contrasts(
            config, seed=base_seed + 2, false_block_effect=config.noninferiority_margin,
            include_alternate=False), alpha=config.alpha)

        correct_interval = target["correct"]["interval"]
        burden_interval = target["burden"]["interval"]
        passed_superiority = correct_interval[0] > 0
        passed_noninferiority = burden_interval[1] < config.noninferiority_margin
        superiority += int(passed_superiority)
        noninferiority += int(passed_noninferiority)
        conjunctive += int(passed_superiority and passed_noninferiority)
        superiority_type1 += int(null_superiority["correct"]["interval"][0] > 0)
        noninferiority_type1 += int(
            boundary_noninferiority["burden"]["interval"][1]
            < config.noninferiority_margin)
        estimates.append(target["correct"]["estimate"])
        intervals.append(correct_interval)
        widths.append(correct_interval[1] - correct_interval[0])
        if target["alt_correct"] is not None:
            alt_estimates.append(target["alt_correct"]["estimate"])

    denominator = config.simulations
    monte_carlo_estimand = statistics.fmean(estimates)
    calibrated_coverage = statistics.fmean(
        float(interval[0] <= monte_carlo_estimand <= interval[1])
        for interval in intervals)
    nominal_coverage = statistics.fmean(
        float(interval[0] <= config.cross_correct_gate_effect <= interval[1])
        for interval in intervals)
    report = {
        "schema_version": "crossaudit-v5-power-1",
        "config": asdict(config),
        "analysis_method": "task_level_normal_interval_for_design_iteration",
        "superiority_power": superiority / denominator,
        "clean_noninferiority_power": noninferiority / denominator,
        "conjunctive_power": conjunctive / denominator,
        "superiority_type1_at_zero": superiority_type1 / denominator,
        "noninferiority_type1_at_margin_boundary": noninferiority_type1 / denominator,
        "correct_effect_monte_carlo_estimand": monte_carlo_estimand,
        "nominal_effect_parameter": config.cross_correct_gate_effect,
        "nominal_to_marginal_effect_difference": (
            monte_carlo_estimand - config.cross_correct_gate_effect),
        "correct_effect_coverage95": calibrated_coverage,
        "nominal_parameter_coverage95": nominal_coverage,
        "mean_correct_interval_width": statistics.fmean(widths),
        "same_vendor_alt_minus_same_mean": statistics.fmean(alt_estimates),
        "confirmatory_simulation_count": denominator >= 10_000,
        "bootstrap_t_calibration_required_before_freeze": True,
        "claim_scope": "included_configurations_only",
        "observed_outcomes_used": False,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIO_OVERRIDES),
                        default="central")
    parser.add_argument("--simulations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = scenario_config(
        args.scenario, simulations=args.simulations, seed=args.seed)
    report = simulate_power(config)
    report["scenario"] = args.scenario
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
