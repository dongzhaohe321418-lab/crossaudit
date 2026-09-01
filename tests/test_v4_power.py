from __future__ import annotations

from tests.test_v4_helpers import V4  # noqa: F401  (installs v4 on sys.path)

from power_simulation import (REGISTERED_GRID_AXES, PowerConfig,
                              registered_scenario_configs, simulate_power)


def test_power_simulation_is_seed_reproducible():
    config = PowerConfig(n_tasks=30, simulations=20, seed=41,
                         cross_correct_gate_effect=0.20, false_block_margin=0.10,
                         analysis_bootstrap_draws=100)
    assert simulate_power(config) == simulate_power(config)


def test_larger_effect_increases_correct_gate_power_on_fixed_random_stream():
    base = dict(n_tasks=50, simulations=60, seed=12, false_block_margin=0.10,
                analysis_bootstrap_draws=100)
    weak = simulate_power(PowerConfig(**base, cross_correct_gate_effect=0.0))
    strong = simulate_power(PowerConfig(**base, cross_correct_gate_effect=0.30))
    assert strong["correct_gate_superiority_power"] > weak["correct_gate_superiority_power"]
    assert weak["correct_gate_type1_at_zero"] <= 0.15


def test_more_tasks_narrows_expected_interval():
    small = simulate_power(PowerConfig(n_tasks=20, simulations=30, seed=4,
                                       cross_correct_gate_effect=0.2,
                                       analysis_bootstrap_draws=100))
    large = simulate_power(PowerConfig(n_tasks=80, simulations=30, seed=4,
                                       cross_correct_gate_effect=0.2,
                                       analysis_bootstrap_draws=100))
    assert large["mean_correct_gate_ci95_width"] < small["mean_correct_gate_ci95_width"]


def test_registered_power_grid_covers_every_frozen_stress_axis_and_is_shardable():
    required = {
        "baseline_correct_gate", "cross_correct_gate_effect", "baseline_false_block",
        "task_base_icc", "repeat_correlation", "cross_direction_heterogeneity",
        "generator_main_effect", "auditor_main_effect", "domain_imbalance",
        "technical_missingness", "differential_missingness",
        "nominal_clean_contamination",
    }
    assert required <= set(REGISTERED_GRID_AXES)
    base = PowerConfig(simulations=2, analysis_bootstrap_draws=10)
    oat = registered_scenario_configs(base, "oat")
    assert len(oat) > len(required)
    assert registered_scenario_configs(base, "oat", scenario_index=1) == [oat[1]]
