from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
V5 = ROOT / "experiment" / "v5"


def _module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, V5 / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_v5_structure_is_valid_but_dispatch_is_blocked():
    preflight = _module("crossaudit_v5_preflight", "preflight.py")
    config = preflight.load_config(V5 / "config" / "study.yaml")
    report = preflight.validate_structure(config)
    assert report == {"structurally_valid": True, "planned_calls": 24930}
    blockers = preflight.freeze_blockers(config)
    assert "cost_caps.maximum_money" in blockers
    assert "model_identity.resolved_models_lock_sha256" in blockers
    with pytest.raises(preflight.PreflightError, match="dispatch blocked"):
        preflight.preflight(V5 / "config" / "study.yaml")


def test_v5_power_is_reproducible_and_uses_task_as_unit():
    power = _module("crossaudit_v5_power", "power_simulation.py")
    config = power.PowerConfig(n_tasks=30, simulations=12, seed=17,
                               cross_correct_gate_effect=0.20)
    first = power.simulate_power(config)
    second = power.simulate_power(config)
    assert first == second
    assert first["config"]["n_tasks"] == 30
    assert first["claim_scope"] == "included_configurations_only"
    assert first["observed_outcomes_used"] is False


def test_v5_large_effect_has_more_power_on_fixed_random_stream():
    power = _module("crossaudit_v5_power_effect", "power_simulation.py")
    shared = dict(n_tasks=45, simulations=30, seed=31,
                  repeat_correlation=0.20)
    weak = power.simulate_power(power.PowerConfig(
        **shared, cross_correct_gate_effect=0.0))
    strong = power.simulate_power(power.PowerConfig(
        **shared, cross_correct_gate_effect=0.30))
    assert strong["superiority_power"] > weak["superiority_power"]


def test_v5_scenarios_cover_registered_stresses():
    power = _module("crossaudit_v5_power_scenarios", "power_simulation.py")
    assert {"central", "high_dependence", "high_repeat_correlation",
            "direction_reversal", "auditor_heterogeneity", "technical_missingness",
            "low_baseline_accuracy", "high_false_block", "n180"} == set(
                power.SCENARIO_OVERRIDES)
    assert power.scenario_config("n180", simulations=2).n_tasks == 180


def test_v5_central_10000_result_passes_only_the_central_design_gates():
    report = json.loads((V5 / "power-central-10000.json").read_text())
    assert report["config"]["simulations"] == 10_000
    assert report["confirmatory_simulation_count"] is True
    assert report["observed_outcomes_used"] is False
    assert report["conjunctive_power"] >= 0.80
    assert 0.93 <= report["correct_effect_coverage95"] <= 0.97
    assert 0.015 <= report["superiority_type1_at_zero"] <= 0.035
    assert 0.04 <= report["noninferiority_type1_at_margin_boundary"] <= 0.06
    assert report["bootstrap_t_calibration_required_before_freeze"] is True
