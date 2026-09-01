#!/usr/bin/env python3
"""Generate publication figures from the sealed v4 feasibility summary.

All plotted values are read from the frozen analysis summary. No demo data,
row sampling, or post-hoc uncertainty calculation is used here. Intervals are
the descriptive task-bootstrap intervals already produced by the frozen scorer.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


FIG_WIDTH_MM = 183.0
FIG_HEIGHT_MM = 126.0
FIG_WIDTH_IN = 7.2047
FIG_HEIGHT_IN = 4.9606
RASTER_DPI = 600

BLUE = "#0F4D92"
BLUE_LIGHT = "#79A9D1"
BLUE_PALE = "#DDEAF4"
GOLD = "#B87503"
GOLD_LIGHT = "#E4B75D"
INK = "#20262E"
GRAY = "#6D7785"
GRAY_LIGHT = "#C7CDD4"
GRID = "#D9DEE5"
WHITE = "#FFFFFF"

EXPECTED_FREEZE = "d4102a553395dad82b5e4147cb8a5e1e3f22d1fa2eea37b584a522bd8668830c"
EXPECTED_CLAIM_STATUS = "execution-feasibility; non-confirmatory; no vendor-population claim"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
SUMMARY_PATH = (
    REPO_ROOT
    / "experiment/v4/feasibility/results/2026-09-01-six-task-amendment-2/summary.json"
)
OUTPUT_DIR = REPO_ROOT / "paper/figures"
QA_DIR = SCRIPT_DIR / "qa"
SOURCE_DATA_PATH = SCRIPT_DIR / "source-data.csv"

SOURCE_FIELDS = [
    "figure",
    "panel",
    "record_type",
    "module",
    "metric",
    "estimand",
    "condition",
    "cluster_id",
    "cluster_unit",
    "estimate",
    "ci_low",
    "ci_high",
    "ci_method",
    "unit",
    "raw_value",
    "raw_unit",
    "n_observations",
    "n_clusters",
    "numerator",
    "denominator",
    "transformation",
    "weighting",
    "source_json_path",
    "warning",
]


def load_alignment_gate() -> Any:
    """Load the mandatory nature-figure Matplotlib alignment gate."""

    candidates: list[Path] = []
    configured = os.environ.get("NATURE_FIGURE_SKILL_ROOT")
    if configured:
        candidates.append(Path(configured).expanduser() / "scripts")
    candidates.append(Path.home() / ".codex/skills/nature-figure/scripts")
    for scripts_dir in candidates:
        if (scripts_dir / "audit_panel_alignment.py").is_file():
            sys.path.insert(0, str(scripts_dir))
            from audit_panel_alignment import require_matplotlib_panel_alignment

            return require_matplotlib_panel_alignment
    searched = ", ".join(str(path) for path in candidates)
    raise RuntimeError(
        "nature-figure alignment helper not found. Install nature-figure or set "
        f"NATURE_FIGURE_SKILL_ROOT. Searched: {searched}"
    )


require_matplotlib_panel_alignment = load_alignment_gate()


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7.0,
        "axes.titlesize": 8.0,
        "axes.labelsize": 7.0,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.3,
        "axes.linewidth": 0.7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": WHITE,
        "figure.facecolor": WHITE,
    }
)


def read_summary() -> dict[str, Any]:
    with SUMMARY_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert data["freeze_sha256"] == EXPECTED_FREEZE
    assert data["claim_status"] == EXPECTED_CLAIM_STATUS
    assert data["schedule_finished"] is True
    assert data["structural_completion"]["valid"] is True
    assert data["structural_completion"]["observed"]["events"] == 2235
    assert data["execution"]["n_scheduled"] == 542
    assert data["execution"]["n_completed"] == 542
    assert data["execution"]["provider_invocations"] == 542
    assert data["execution"]["status_counts"] == {"valid": 542}
    assert np.isclose(data["execution"]["known_cost_usd"], 12.1504115)
    return data


def add_row(rows: list[dict[str, Any]], **values: Any) -> None:
    row = {field: "" for field in SOURCE_FIELDS}
    for key, value in values.items():
        if key not in row:
            raise KeyError(f"unknown source-data field: {key}")
        row[key] = value
    rows.append(row)


def add_effect_rows(
    rows: list[dict[str, Any]],
    *,
    figure: str,
    panel: str,
    module: str,
    metric: str,
    estimand: str,
    condition: str,
    result: dict[str, Any],
    source_json_path: str,
    sign: float = 1.0,
    transformation: str = "none",
) -> dict[str, Any]:
    interval = result["ci95_task_bootstrap"]
    estimate = sign * result["estimate"]
    ci_low, ci_high = sorted((sign * interval[0], sign * interval[1]))
    warning = result.get("warning") or ""
    add_row(
        rows,
        figure=figure,
        panel=panel,
        record_type="estimate",
        module=module,
        metric=metric,
        estimand=estimand,
        condition=condition,
        cluster_unit=result.get("cluster_field", "task_id"),
        estimate=estimate,
        ci_low=ci_low,
        ci_high=ci_high,
        ci_method="descriptive 95% task bootstrap",
        unit="proportion",
        n_clusters=result.get("n_clusters", result.get("n_tasks", "")),
        transformation=transformation,
        weighting="equal-weight frozen clusters",
        source_json_path=source_json_path,
        warning=warning,
    )
    cluster_values = result.get("cluster_values", result.get("task_values", {}))
    for cluster_id, value in sorted(cluster_values.items()):
        add_row(
            rows,
            figure=figure,
            panel=panel,
            record_type="cluster_value",
            module=module,
            metric=metric,
            estimand=estimand,
            condition=condition,
            cluster_id=cluster_id,
            cluster_unit=result.get("cluster_field", "task_id"),
            estimate=sign * value,
            unit="proportion",
            n_observations=1,
            transformation=transformation,
            source_json_path=f"{source_json_path}.cluster_values.{cluster_id}",
            warning=warning,
        )
    return {"estimate": estimate, "ci_low": ci_low, "ci_high": ci_high}


def add_panel_label(ax: mpl.axes.Axes, label: str) -> None:
    ax.text(
        -0.20,
        1.14,
        label,
        transform=ax.transAxes,
        fontsize=8.5,
        fontweight="bold",
        ha="left",
        va="top",
        color=INK,
    )


def panel_title(ax: mpl.axes.Axes, title: str) -> None:
    ax.set_title(title, loc="left", pad=7.0, fontweight="bold", color=INK)


def clean_axis(ax: mpl.axes.Axes) -> None:
    ax.tick_params(length=2.5, width=0.6, color=GRAY, pad=2.0)
    ax.spines["left"].set_color(GRAY)
    ax.spines["bottom"].set_color(GRAY)


def normalise_generated_text(path: Path) -> None:
    """Use repository-friendly LF endings and remove generator whitespace."""

    content = path.read_text(encoding="utf-8")
    path.write_text(
        "\n".join(line.rstrip() for line in content.splitlines()) + "\n",
        encoding="utf-8",
    )


def forest_plot(
    ax: mpl.axes.Axes,
    labels: list[str],
    effects: list[dict[str, Any]],
    colors: list[str],
    markers: list[str],
    xlim: tuple[float, float],
) -> None:
    y_positions = np.arange(len(labels))[::-1]
    ax.axvline(0.0, color=GRAY, linewidth=0.8, linestyle=(0, (2, 2)), zorder=0)
    for y_pos, effect, color, marker in zip(y_positions, effects, colors, markers):
        estimate = effect["estimate"] * 100.0
        low = effect["ci_low"] * 100.0
        high = effect["ci_high"] * 100.0
        ax.errorbar(
            estimate,
            y_pos,
            xerr=np.array([[estimate - low], [high - estimate]]),
            fmt=marker,
            markersize=4.8,
            markerfacecolor=WHITE if marker == "s" else color,
            markeredgecolor=color,
            markeredgewidth=0.9,
            color=color,
            ecolor=color,
            elinewidth=1.2,
            capsize=2.2,
            capthick=0.8,
            zorder=3,
        )
    ax.set_yticks(y_positions, labels)
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.65, len(labels) - 0.35)
    ax.set_xlabel("Effect (percentage points; + = better)")
    ax.grid(axis="x", color=GRID, linewidth=0.5, zorder=-2)
    clean_axis(ax)


def make_figure5(data: dict[str, Any], rows: list[dict[str, Any]]) -> Path:
    core = data["core_2x2_and_ablations"]
    d0 = core["primary_pairing"]["D0_OFF"]
    controlled = d0["controlled_correct_gate_fixed_2x2"]
    false_block = d0["negative_control_false_block_fixed_2x2"]
    dcl = core["dcl_ablation"]["paired_contrasts"]

    cell_order = [
        "anthropic->anthropic",
        "anthropic->openai",
        "openai->anthropic",
        "openai->openai",
    ]
    cell_values: list[float] = []
    for cell in cell_order:
        result = controlled["four_cells"][cell]
        cell_values.append(result["estimate"])
        add_row(
            rows,
            figure="Figure 5",
            panel="a",
            record_type="estimate",
            module="Generator x Auditor",
            metric="correct_gate",
            estimand="absolute controlled C2/D0 cell rate",
            condition=cell,
            cluster_unit="task_id",
            estimate=result["estimate"],
            ci_low=result["ci95_task_bootstrap"][0],
            ci_high=result["ci95_task_bootstrap"][1],
            ci_method="descriptive 95% task bootstrap",
            unit="proportion",
            n_clusters=result["n_tasks"],
            weighting=controlled["weighting"],
            source_json_path=(
                ".core_2x2_and_ablations.primary_pairing.D0_OFF."
                f"controlled_correct_gate_fixed_2x2.four_cells.{cell}"
            ),
            warning=result["warning"],
        )
        for task_id, value in sorted(result["task_values"].items()):
            add_row(
                rows,
                figure="Figure 5",
                panel="a",
                record_type="cluster_value",
                module="Generator x Auditor",
                metric="correct_gate",
                estimand="absolute controlled C2/D0 cell rate",
                condition=cell,
                cluster_id=task_id,
                cluster_unit="task_id",
                estimate=value,
                unit="proportion",
                n_observations=1,
                source_json_path=(
                    ".core_2x2_and_ablations.primary_pairing.D0_OFF."
                    f"controlled_correct_gate_fixed_2x2.four_cells.{cell}.task_values.{task_id}"
                ),
                warning=result["warning"],
            )

    pairing_specs = [
        (
            "Anthropic author\ncross - same",
            controlled["contrasts"]["anthropic->openai_minus_anthropic->anthropic"],
            "correct_gate",
            "Anthropic-authored: OpenAI auditor minus Anthropic auditor",
            1.0,
            "none",
        ),
        (
            "OpenAI author\ncross - same",
            controlled["contrasts"]["openai->anthropic_minus_openai->openai"],
            "correct_gate",
            "OpenAI-authored: Anthropic auditor minus OpenAI auditor",
            1.0,
            "none",
        ),
        (
            "All authors\ncorrect gate",
            controlled["contrasts"]["cross_minus_same"],
            "correct_gate",
            "cross minus same",
            1.0,
            "none",
        ),
        (
            "All authors\nfalse-block reduction",
            false_block["contrasts"]["cross_minus_same"],
            "false_block",
            "same minus cross",
            -1.0,
            "sign reversed from raw cross-minus-same false-block contrast",
        ),
    ]
    pairing_effects: list[dict[str, Any]] = []
    for label, result, metric, estimand, sign, transformation in pairing_specs:
        del label
        raw_key = {
            "Anthropic-authored: OpenAI auditor minus Anthropic auditor": "anthropic->openai_minus_anthropic->anthropic",
            "OpenAI-authored: Anthropic auditor minus OpenAI auditor": "openai->anthropic_minus_openai->openai",
            "cross minus same": "cross_minus_same",
            "same minus cross": "cross_minus_same",
        }[estimand]
        source_block = (
            "controlled_correct_gate_fixed_2x2" if metric == "correct_gate" else
            "negative_control_false_block_fixed_2x2"
        )
        pairing_effects.append(
            add_effect_rows(
                rows,
                figure="Figure 5",
                panel="b",
                module="Generator x Auditor",
                metric=metric,
                estimand=estimand,
                condition="C2/D0 controlled strata",
                result=result,
                source_json_path=(
                    ".core_2x2_and_ablations.primary_pairing.D0_OFF."
                    f"{source_block}.contrasts.{raw_key}"
                ),
                sign=sign,
                transformation=transformation,
            )
        )

    dcl_specs = [
        ("D2 - D0\ncorrect gate", dcl["correct_gate"]["D2_minus_D0"], "correct_gate", "D2 minus D0", 1.0, "none"),
        ("D2 - D0\nfalse-block reduction", dcl["false_block"]["D2_minus_D0"], "false_block", "D0 minus D2", -1.0, "sign reversed so positive means fewer false blocks"),
        ("D2 - D1\ncorrect gate", dcl["correct_gate"]["D2_minus_D1"], "correct_gate", "D2 minus D1", 1.0, "none"),
        ("D2 - D1\nfalse-block reduction", dcl["false_block"]["D2_minus_D1"], "false_block", "D1 minus D2", -1.0, "sign reversed so positive means fewer false blocks"),
    ]
    dcl_effects: list[dict[str, Any]] = []
    for label, result, metric, estimand, sign, transformation in dcl_specs:
        del label
        raw_key = "D2_minus_D0" if "D0" in estimand else "D2_minus_D1"
        dcl_effects.append(
            add_effect_rows(
                rows,
                figure="Figure 5",
                panel="c",
                module="DCL ablation",
                metric=metric,
                estimand=estimand,
                condition="C2 all frozen artefacts",
                result=result,
                source_json_path=(
                    f".core_2x2_and_ablations.dcl_ablation.paired_contrasts.{metric}.{raw_key}"
                ),
                sign=sign,
                transformation=transformation,
            )
        )

    rates_d0 = d0["rates_by_assignment_and_artifact_type"]
    rates_d2 = core["primary_pairing"]["D2_COMBINED_BLIND"][
        "rates_by_assignment_and_artifact_type"
    ]
    controlled_keys = [
        f"{assignment}/{artifact_type}"
        for assignment in ("cross", "same")
        for artifact_type in ("ambiguous", "clean", "seeded")
    ]
    strata_values = {
        "Natural": {
            "D0": np.mean([rates_d0["cross/natural"]["mean"], rates_d0["same/natural"]["mean"]]),
            "D2": np.mean([rates_d2["cross/natural"]["mean"], rates_d2["same/natural"]["mean"]]),
            "n": 72,
        },
        "Controlled\n(3 strata)": {
            "D0": np.mean([rates_d0[key]["mean"] for key in controlled_keys]),
            "D2": np.mean([rates_d2[key]["mean"] for key in controlled_keys]),
            "n": 216,
        },
    }
    assert np.isclose(strata_values["Natural"]["D0"], 0.25)
    assert np.isclose(strata_values["Natural"]["D2"], 1.0)
    assert np.isclose(strata_values["Controlled\n(3 strata)"]["D0"], 0.8981481481481481)
    assert np.isclose(
        strata_values["Controlled\n(3 strata)"]["D0"],
        strata_values["Controlled\n(3 strata)"]["D2"],
    )
    for stratum, values in strata_values.items():
        for mode in ("D0", "D2"):
            add_row(
                rows,
                figure="Figure 5",
                panel="d",
                record_type="derived_estimate",
                module="DCL ablation",
                metric="correct_gate",
                estimand="assignment-balanced stratum rate",
                condition=f"{stratum}; {mode}",
                cluster_unit="task_id",
                estimate=values[mode],
                unit="proportion",
                n_observations=values["n"],
                n_clusters=6,
                transformation="equal mean across same/cross and listed artifact strata",
                weighting="equal-weight cells; all contributing cells have 36 rows",
                source_json_path=(
                    ".core_2x2_and_ablations.primary_pairing."
                    f"{'D0_OFF' if mode == 'D0' else 'D2_COMBINED_BLIND'}."
                    "rates_by_assignment_and_artifact_type"
                ),
                warning="descriptive feasibility decomposition",
            )
    add_row(
        rows,
        figure="Figure 5",
        panel="d",
        record_type="reference",
        module="DCL ablation",
        metric="correct_gate",
        estimand="D1 checker-defined ceiling",
        condition="all artifact types",
        estimate=1.0,
        unit="proportion",
        n_observations=48,
        n_clusters=6,
        transformation="none",
        source_json_path=".core_2x2_and_ablations.dcl_ablation.D1_ONLY_accuracy_by_artifact_type",
        warning="D1 shares the deterministic checker that defines feasibility gold",
    )

    fig, axes = plt.subplots(2, 2, figsize=(7.2047, 4.9606))
    fig.subplots_adjust(left=0.13, right=0.985, bottom=0.105, top=0.94, wspace=0.48, hspace=0.58)

    ax = axes[0, 0]
    matrix = np.array(cell_values).reshape(2, 2) * 100.0
    cmap = LinearSegmentedColormap.from_list("crossaudit_blue", ["#F5F7FA", BLUE_PALE, BLUE])
    ax.imshow(matrix, vmin=0.0, vmax=100.0, cmap=cmap, aspect="auto", interpolation="nearest")
    ax.set_xticks([0, 1], ["Anthropic", "OpenAI"])
    ax.set_yticks([0, 1], ["Anthropic", "OpenAI"])
    ax.set_xlabel("Auditor configuration")
    ax.set_ylabel("Generator configuration")
    for row_index in range(2):
        for column_index in range(2):
            ax.text(
                column_index,
                row_index,
                f"{matrix[row_index, column_index]:.1f}%",
                ha="center",
                va="center",
                fontsize=7.2,
                fontweight="bold",
                color=WHITE if matrix[row_index, column_index] >= 55 else INK,
            )
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(WHITE)
        spine.set_linewidth(1.0)
    panel_title(ax, "Absolute correct gate (C2/D0)")
    add_panel_label(ax, "a")

    ax = axes[0, 1]
    forest_plot(
        ax,
        [spec[0] for spec in pairing_specs],
        pairing_effects,
        [BLUE, BLUE, BLUE_LIGHT, GOLD],
        ["o", "o", "o", "s"],
        (-10.0, 32.0),
    )
    ax.axhline(1.5, color=GRID, linewidth=0.6)
    panel_title(ax, "Pairing effects (C2/D0)")
    add_panel_label(ax, "b")

    ax = axes[1, 0]
    forest_plot(
        ax,
        [spec[0] for spec in dcl_specs],
        dcl_effects,
        [BLUE, GOLD, BLUE, GOLD],
        ["o", "s", "o", "s"],
        (-24.0, 26.0),
    )
    ax.axhline(1.5, color=GRID, linewidth=0.6)
    panel_title(ax, "Component ablations (C2)")
    add_panel_label(ax, "c")

    ax = axes[1, 1]
    categories = list(strata_values)
    x_positions = np.arange(len(categories))
    bar_width = 0.32
    d0_values = [strata_values[name]["D0"] * 100.0 for name in categories]
    d2_values = [strata_values[name]["D2"] * 100.0 for name in categories]
    bars_d0 = ax.bar(
        x_positions - bar_width / 2,
        d0_values,
        bar_width,
        color=GRAY_LIGHT,
        edgecolor="none",
        linewidth=0.0,
    )
    bars_d2 = ax.bar(
        x_positions + bar_width / 2,
        d2_values,
        bar_width,
        color=BLUE,
        edgecolor="none",
        linewidth=0.0,
    )
    ax.axhline(
        100.0,
        color=GOLD,
        linewidth=1.0,
        linestyle=(0, (3, 2)),
    )
    for bar, value in zip(bars_d0, d0_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value - 3.0,
            f"{value:.1f}",
            ha="center",
            va="top",
            fontsize=6.0,
            color=INK,
        )
    for bar, value in zip(bars_d2, d2_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value - 3.0,
            f"{value:.1f}",
            ha="center",
            va="top",
            fontsize=6.0,
            color=WHITE,
        )
    ax.set_xticks(x_positions, categories)
    ax.set_ylabel("Correct gate (%)")
    ax.set_ylim(0.0, 114.0)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", color=GRID, linewidth=0.5, zorder=-2)
    ax.text(
        0.02,
        0.98,
        "Bar order: D0 / D2; dashed: D1 checker ceiling",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.0,
        color=INK,
    )
    clean_axis(ax)
    panel_title(ax, "D2 gain is localized to natural output")
    add_panel_label(ax, "d")

    return export_figure(fig, axes.ravel(), "figure5-v4-configuration-effects")


def make_figure6(data: dict[str, Any], rows: list[dict[str, Any]]) -> Path:
    defensive = data["defensive_production"]["research_artefact_policy_arms"]
    initial = defensive["initial_anticipatory"]["arm_descriptives"]["objective_correct"]
    final = defensive["bounded_loop_by_policy"]
    resources = defensive["resource_use_by_policy"]
    loop = data["whole_loop_seeded_same_cross"]["by_assignment"]
    ledger = data["ledger_proxy_pilot"]

    policies = ["P0", "P1", "P2"]
    initial_values = [initial[policy]["mean"] for policy in policies]
    final_values = [final[policy]["final_objective_correct_rate_ITT"] for policy in policies]
    for stage, values in (("initial", initial_values), ("final", final_values)):
        for policy, value in zip(policies, values):
            numerator = round(value * 12)
            source_path = (
                ".defensive_production.research_artefact_policy_arms."
                f"initial_anticipatory.arm_descriptives.objective_correct.{policy}.mean"
                if stage == "initial"
                else ".defensive_production.research_artefact_policy_arms."
                f"bounded_loop_by_policy.{policy}.final_objective_correct_rate_ITT"
            )
            add_row(
                rows,
                figure="Figure 6",
                panel="a",
                record_type="arm_rate",
                module="Defensive production",
                metric="objective_correct",
                estimand=f"{stage} ITT correctness",
                condition=policy,
                cluster_unit="task_id",
                estimate=value,
                unit="proportion",
                n_observations=12,
                n_clusters=6,
                numerator=numerator,
                denominator=12,
                weighting="session rate; six convenience-task clusters",
                source_json_path=source_path,
                warning="descriptive feasibility rate",
            )
    repair = final["P2"]["repair_among_initial_wrong"]
    regression = final["P2"]["regression_among_initial_correct"]
    for metric, result in (("repair", repair), ("regression", regression)):
        add_row(
            rows,
            figure="Figure 6",
            panel="a",
            record_type="conditional_rate",
            module="Defensive production",
            metric=metric,
            estimand=f"P2 {metric} conditional rate",
            condition="P2",
            estimate=result["rate"],
            unit="proportion",
            numerator=result["numerator"],
            denominator=result["denominator"],
            source_json_path=(
                ".defensive_production.research_artefact_policy_arms."
                f"bounded_loop_by_policy.P2.{metric}_among_initial_"
                f"{'wrong' if metric == 'repair' else 'correct'}"
            ),
            warning="conditional descriptive rate",
        )

    resource_specs = [
        ("Calls", "provider_invocations", "calls"),
        ("Cost", "known_cost_usd", "USD"),
        ("Provider\ntime", "latency_seconds_sum", "seconds"),
    ]
    resource_ratios: dict[str, list[float]] = {policy: [] for policy in policies}
    for label, key, raw_unit in resource_specs:
        baseline = resources["P0"][key]
        for policy in policies:
            raw_value = resources[policy][key]
            ratio = raw_value / baseline
            resource_ratios[policy].append(ratio)
            add_row(
                rows,
                figure="Figure 6",
                panel="b",
                record_type="relative_resource",
                module="Defensive production",
                metric=key,
                estimand=f"{policy} relative to P0",
                condition=policy,
                estimate=ratio,
                unit="ratio",
                raw_value=raw_value,
                raw_unit=raw_unit,
                n_observations=12,
                n_clusters=6,
                transformation=f"{policy} value divided by P0 value",
                source_json_path=(
                    ".defensive_production.research_artefact_policy_arms."
                    f"resource_use_by_policy.{policy}.{key}"
                ),
                warning="cumulative cohort resource use; no uncertainty interval",
            )

    loop_specs = [
        ("Initial defect\nresolved", "fraction_initial_resolved_ITT"),
        ("Final\nacceptable", "final_acceptable"),
        ("New defect", "new_defect_any"),
        ("Unnecessary\nchange", "unnecessary_change_any"),
    ]
    loop_values: dict[str, list[float]] = {assignment: [] for assignment in ("same", "cross")}
    for label, key in loop_specs:
        del label
        for assignment in ("same", "cross"):
            value = loop[assignment][key]["mean"]
            loop_values[assignment].append(value)
            add_row(
                rows,
                figure="Figure 6",
                panel="c",
                record_type="assignment_rate",
                module="Whole loop",
                metric=key,
                estimand="assignment-specific ITT rate",
                condition=assignment,
                cluster_unit="task_id",
                estimate=value,
                unit="proportion",
                n_observations=loop[assignment]["n_branches"],
                n_clusters=6,
                numerator=round(value * loop[assignment]["n_branches"]),
                denominator=loop[assignment]["n_branches"],
                source_json_path=(
                    f".whole_loop_seeded_same_cross.by_assignment.{assignment}.{key}.mean"
                ),
                warning="descriptive feasibility rate; endpoints are not compositional",
            )

    ledger_specs = [
        ("Accept\ndecision", "accept_accuracy_ITT"),
        ("Tamper\ndetection", "tamper_accuracy_ITT"),
        ("First defective\nround", "first_defective_round_accuracy_ITT"),
    ]
    ledger_values: dict[str, list[float]] = {interface: [] for interface in ("E0", "E1", "E2")}
    for label, key in ledger_specs:
        del label
        for interface in ("E0", "E1", "E2"):
            result = ledger["interfaces"][interface]
            value = result[key]
            ledger_values[interface].append(value)
            add_row(
                rows,
                figure="Figure 6",
                panel="d",
                record_type="interface_rate",
                module="Ledger proxy",
                metric=key,
                estimand="interface-specific proxy accuracy",
                condition=interface,
                cluster_unit="episode_id",
                estimate=value,
                unit="proportion",
                n_observations=result["n_proxy_reviews_ITT"],
                n_clusters=7,
                numerator=round(value * result["n_proxy_reviews_ITT"]),
                denominator=result["n_proxy_reviews_ITT"],
                source_json_path=f".ledger_proxy_pilot.interfaces.{interface}.{key}",
                warning="fresh model proxies, not human participants; clustered by seven episodes",
            )
    add_effect_rows(
        rows,
        figure="Figure 6",
        panel="d",
        module="Ledger proxy",
        metric="first_defective_round_accuracy",
        estimand="E2 minus E1",
        condition="structured ledger versus ordinary log",
        result=ledger["episode_clustered_proxy_contrasts"]["correct_first_defective"]["E2_minus_E1"],
        source_json_path=(
            ".ledger_proxy_pilot.episode_clustered_proxy_contrasts."
            "correct_first_defective.E2_minus_E1"
        ),
    )
    stability = data["core_2x2_and_ablations"]["C2_three_repeat_stability"]
    add_row(
        rows,
        figure="Figure 6",
        panel="caption",
        record_type="diagnostic_rate",
        module="Repetition stability",
        metric="valid_verdict_flip_rate",
        estimand="any gate flip among three valid replies",
        condition="C2 artefact-auditor cells",
        cluster_unit="artifact_id x auditor_vendor",
        estimate=stability["valid_verdict_flip_rate_among_all_three_valid"],
        unit="proportion",
        n_observations=stability["n_all_three_valid_cells"],
        numerator=5,
        denominator=96,
        source_json_path=(
            ".core_2x2_and_ablations.C2_three_repeat_stability."
            "valid_verdict_flip_rate_among_all_three_valid"
        ),
        warning=stability["note"],
    )

    fig, axes = plt.subplots(2, 2, figsize=(7.2047, 4.9606))
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.105, top=0.94, wspace=0.48, hspace=0.58)

    ax = axes[0, 0]
    colors = [GRAY, GOLD, BLUE]
    markers = ["o", "s", "D"]
    offsets = [-0.055, 0.0, 0.055]
    for policy, color, marker, offset, start, end in zip(
        policies, colors, markers, offsets, initial_values, final_values
    ):
        x_values = np.array([0.0, 1.0]) + offset
        y_values = np.array([start, end]) * 100.0
        ax.plot(
            x_values,
            y_values,
            color=color,
            marker=marker,
            markersize=5.0,
            markerfacecolor=WHITE if policy == "P1" else color,
            markeredgecolor=color,
            linewidth=1.2,
            label=policy,
        )
    ax.set_xticks([0, 1], ["Initial", "After bounded loop"])
    ax.set_xlim(-0.25, 1.25)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Objective correct (%)")
    ax.grid(axis="y", color=GRID, linewidth=0.5, zorder=-2)
    ax.legend(loc="upper left", ncol=3, handlelength=1.8, columnspacing=0.9)
    ax.text(
        0.98,
        0.92,
        "P2: 2/9 repairs; 0/3 regressions",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.3,
        color=INK,
    )
    clean_axis(ax)
    panel_title(ax, "Hard gate repaired 2 initial errors")
    add_panel_label(ax, "a")

    ax = axes[0, 1]
    group_positions = np.arange(len(resource_specs)) * 1.0
    bar_width = 0.28
    p1_positions = group_positions - bar_width / 2
    p2_positions = group_positions + bar_width / 2
    bars_p1 = ax.bar(
        p1_positions,
        resource_ratios["P1"],
        bar_width,
        color=GOLD_LIGHT,
        edgecolor="none",
        linewidth=0.0,
    )
    bars_p2 = ax.bar(
        p2_positions,
        resource_ratios["P2"],
        bar_width,
        color=BLUE,
        edgecolor="none",
        linewidth=0.0,
    )
    ax.axhline(1.0, color=GRAY, linewidth=0.9, linestyle=(0, (2, 2)))
    for bar, value in zip(bars_p1, resource_ratios["P1"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value * 0.60,
            f"{value:.2f}x",
            ha="center",
            va="center",
            fontsize=6.0,
            color=INK,
        )
    for bar, value in zip(bars_p2, resource_ratios["P2"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value * 0.60,
            f"{value:.2f}x",
            ha="center",
            va="center",
            fontsize=6.0,
            color=WHITE,
        )
    tick_positions = np.ravel(np.column_stack((p1_positions, p2_positions)))
    ax.set_xticks(group_positions, ["Calls", "Cost", "Time"])
    ax.set_xticks(tick_positions, ["P1", "P2"] * 3, minor=True)
    ax.set_ylabel("Relative to P0")
    ax.set_ylim(0.0, 2.82)
    ax.set_yticks([0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
    ax.text(
        0.98,
        0.98,
        "Dashed reference: P0 = 1.0",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.0,
        color=INK,
    )
    clean_axis(ax)
    ax.tick_params(axis="x", which="major", length=0.0, pad=15.0)
    ax.tick_params(axis="x", which="minor", length=2.0, pad=2.0)
    panel_title(ax, "P2 used more resources")
    add_panel_label(ax, "b")

    ax = axes[1, 0]
    x_positions = np.arange(len(loop_specs))
    same_values = np.array(loop_values["same"]) * 100.0
    cross_values = np.array(loop_values["cross"]) * 100.0
    for x_pos, same_value, cross_value in zip(x_positions, same_values, cross_values):
        ax.plot([x_pos - 0.08, x_pos + 0.08], [same_value, cross_value], color=GRAY_LIGHT, linewidth=1.0)
    ax.scatter(
        x_positions - 0.08,
        same_values,
        s=28,
        facecolors=WHITE,
        edgecolors=GRAY,
        linewidths=1.0,
        marker="o",
        label="Same",
        zorder=3,
    )
    ax.scatter(
        x_positions + 0.08,
        cross_values,
        s=30,
        color=BLUE,
        linewidths=1.0,
        marker="x",
        label="Cross",
        zorder=4,
    )
    ax.set_xticks(x_positions, [spec[0] for spec in loop_specs])
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Branches (%)")
    ax.grid(axis="y", color=GRID, linewidth=0.5, zorder=-2)
    ax.text(
        0.98,
        0.98,
        "Same: open circle; Cross: x",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.0,
        color=INK,
    )
    clean_axis(ax)
    panel_title(ax, "Same and cross endpoints matched")
    add_panel_label(ax, "c")

    ax = axes[1, 1]
    x_positions = np.arange(len(ledger_specs))
    bar_width = 0.24
    interface_styles = [
        ("E0", GRAY_LIGHT, GRAY),
        ("E1", GOLD_LIGHT, GOLD),
        ("E2", BLUE, BLUE),
    ]
    for offset_index, (interface, fill, edge) in enumerate(interface_styles):
        offset = (offset_index - 1) * bar_width
        values = np.array(ledger_values[interface]) * 100.0
        bars = ax.bar(
            x_positions + offset,
            values,
            bar_width,
            color=fill,
            edgecolor="none",
            linewidth=0.0,
        )
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                3.0 if value == 0 else value * 0.60,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=6.2,
                color=INK if interface == "E0" or value == 0 else WHITE,
            )
    ax.set_xticks(x_positions, [spec[0] for spec in ledger_specs])
    ax.set_ylabel("Proxy accuracy (%)")
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", color=GRID, linewidth=0.5, zorder=-2)
    ax.text(
        0.02,
        0.98,
        "Bar order: E0 / E1 / E2",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.0,
        color=INK,
    )
    clean_axis(ax)
    panel_title(ax, "Ledger matched log on primary decisions")
    add_panel_label(ax, "d")

    return export_figure(fig, axes.ravel(), "figure6-v4-operational-tradeoffs")


def export_figure(
    fig: mpl.figure.Figure,
    axes: Iterable[mpl.axes.Axes],
    stem: str,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    axes_list = list(axes)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        axes=axes_list,
        panel_ids=list("abcd"),
        json_out=QA_DIR / f"{stem}.alignment.json",
        overlay_svg=QA_DIR / f"{stem}.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=True,
        strict=True,
    )
    normalise_generated_text(QA_DIR / f"{stem}.alignment.svg")
    pdf_path = OUTPUT_DIR / f"{stem}.pdf"
    fig.savefig(pdf_path, format="pdf", facecolor=WHITE)
    svg_path = OUTPUT_DIR / f"{stem}.svg"
    fig.savefig(svg_path, format="svg", facecolor=WHITE)
    normalise_generated_text(svg_path)
    fig.savefig(OUTPUT_DIR / f"{stem}.png", format="png", dpi=600, facecolor=WHITE)
    fig.savefig(
        OUTPUT_DIR / f"{stem}.tiff",
        format="tiff",
        dpi=600,
        facecolor=WHITE,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    return pdf_path


def write_source_data(rows: list[dict[str, Any]]) -> None:
    SOURCE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SOURCE_DATA_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    data = read_summary()
    rows: list[dict[str, Any]] = []
    figure5 = make_figure5(data, rows)
    figure6 = make_figure6(data, rows)
    write_source_data(rows)
    print(f"wrote {figure5.relative_to(REPO_ROOT)}")
    print(f"wrote {figure6.relative_to(REPO_ROOT)}")
    print(f"wrote {SOURCE_DATA_PATH.relative_to(REPO_ROOT)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
