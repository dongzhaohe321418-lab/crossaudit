#!/usr/bin/env python3
"""Pure metric construction for CrossAudit v4.

No inferential procedure lives here.  This module turns validated relational
records into run-, task-, and condition-level numerators and denominators; the
cluster module then resamples tasks rather than defects or repeated calls.
"""
from __future__ import annotations

import itertools
import statistics
from collections import Counter, defaultdict
from typing import Any

from schema import Dataset


def mean_or_none(values: list[float | int | None]) -> float | None:
    xs = [float(x) for x in values if x is not None]
    return statistics.fmean(xs) if xs else None


def median_or_none(values: list[float | int | None]) -> float | None:
    xs = [float(x) for x in values if x is not None]
    return statistics.median(xs) if xs else None


def token_cost(row: dict[str, Any], prices: dict[str, dict[str, Any]]) -> float | None:
    key = row.get("price_key")
    if key is None:
        return None
    p = prices[key]
    return (
        row["input_tokens"] * p["input_per_million"]
        + row["output_tokens"] * p["output_per_million"]
        + row["cached_tokens"] * p["cached_per_million"]
        + row["reasoning_tokens"] * p["reasoning_per_million"]
    ) / 1_000_000


def _indices(ds: Dataset) -> dict[str, Any]:
    tables = ds.tables
    artifacts = {x["artifact_id"]: x for x in tables["artifacts"]}
    tasks = {x["task_id"]: x for x in tables["tasks"]}
    defects_by_artifact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in tables["defects"]:
        defects_by_artifact[d["artifact_id"]].append(d)
    findings_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    findings = {x["finding_id"]: x for x in tables["findings"]}
    for f in tables["findings"]:
        findings_by_run[f["audit_run_id"]].append(f)
    matches_by_finding: dict[str, dict[str, Any]] = {}
    for m in tables["finding_matches"]:
        matches_by_finding[m["finding_id"]] = m
    prices = {p["price_key"]: p for p in ds.price_table["prices"]}
    return {"artifacts": artifacts, "tasks": tasks, "defects_by_artifact": defects_by_artifact,
            "findings_by_run": findings_by_run, "findings": findings,
            "matches_by_finding": matches_by_finding, "prices": prices}


def audit_run_rows(ds: Dataset) -> list[dict[str, Any]]:
    """One scored row per scheduled audit call, including failed calls."""
    ix = _indices(ds)
    out = []
    for run in ds.rows("audit_runs"):
        artifact = ix["artifacts"][run["artifact_id"]]
        task = ix["tasks"][artifact["task_id"]]
        gold = [d for d in ix["defects_by_artifact"][artifact["artifact_id"]]
                if d["gold_status"] == "confirmed"]
        active = [f for f in ix["findings_by_run"][run["audit_run_id"]]
                  if f["status"] == "alleged"]
        labelled = [(f, ix["matches_by_finding"][f["finding_id"]]) for f in active]
        true_matches = [(f, m) for f, m in labelled if m["label"] == "true"]
        false_matches = [(f, m) for f, m in labelled
                         if m["label"] in {"false", "duplicate"}]
        unresolved = [(f, m) for f, m in labelled if m["label"] == "unresolved"]
        caught = len({m["defect_id"] for _, m in true_matches})
        adjudicated = len(true_matches) + len(false_matches)
        blocker_pairs = [(f, m) for f, m in labelled
                         if f["severity"] == "BLOCKER" and f["blocked_scope"]]
        blocker_true = sum(m["label"] == "true" for _, m in blocker_pairs)
        blocker_adjudicated = sum(m["label"] in {"true", "false", "duplicate"}
                                  for _, m in blocker_pairs)
        ok = run["status"] == "ok"
        recall_itt = None
        if gold:
            recall_itt = caught / len(gold) if ok else None
        precision = len(true_matches) / adjudicated if adjudicated else None
        blocker_precision = blocker_true / blocker_adjudicated if blocker_adjudicated else None
        gate_blocked = not ok or run["controller_verdict"] == "BLOCKED"
        # Technical failure is missing for the semantic primary estimands, not
        # silently relabelled PASS or BLOCK.  Operational non-admission remains
        # fail-closed and is co-reported below.
        correct_gate = (float((run["controller_verdict"] == "BLOCKED")
                              == artifact["requires_block"]) if ok else None)
        false_block = None
        if not artifact["requires_block"] and ok and run["model_verdict"] != "NOT_RUN":
            # Registered clean-FBR is an effective model-originated BLOCK.  A
            # deterministic DCL-only block and a transport failure are separate
            # operational endpoints, not false model allegations.
            false_block = float(run["model_verdict"] == "BLOCKED")
        operational_nonadmission = 1.0 if gate_blocked else 0.0
        caught_ids = {m["defect_id"] for _, m in true_matches}
        channel_metrics = {}
        for channel in ("script", "tool", "model", "human"):
            channel_gold = [d for d in gold if d["channel"] == channel]
            channel_metrics[f"recall_{channel}"] = (
                sum(d["defect_id"] in caught_ids for d in channel_gold) / len(channel_gold)
                if channel_gold else None)
        out.append({
            "task_id": task["task_id"], "requires_block": artifact["requires_block"],
            "gold_kind": artifact["gold_kind"],
            "base_artifact_id": artifact["base_artifact_id"],
            "target_id": artifact["target_id"],
            "artifact_id": artifact["artifact_id"],
            "generation_repeat": artifact["generation_repeat"],
            "generator_vendor": run["generator_vendor"],
            "auditor_vendor": run["auditor_vendor"],
            "cross_vendor": run["generator_vendor"] != run["auditor_vendor"],
            "audit_run_id": run["audit_run_id"], "audit_repeat": run["audit_repeat"],
            "dcl_level": run["dcl_level"],
            "constitution_level": run["constitution_level"],
            "audit_policy": run["audit_policy"], "status": run["status"],
            "model_verdict": run["model_verdict"], "dcl_verdict": run["dcl_verdict"],
            "controller_verdict": run["controller_verdict"],
            "verdict": run["controller_verdict"], "n_gold": len(gold), "n_caught": caught,
            "caught_defect_ids": sorted(caught_ids),
            "recall": recall_itt, "n_true_findings": len(true_matches),
            "n_false_findings": len(false_matches), "n_unresolved_findings": len(unresolved),
            "n_adjudicated_findings": adjudicated, "precision": precision,
            "blocker_precision": blocker_precision, "false_block": false_block,
            "correct_gate": correct_gate,
            "operational_nonadmission": operational_nonadmission,
            "cost_usd": token_cost(run, ix["prices"]),
            "provider_latency_s": run["provider_latency_s"],
            "latency_s": run["end_to_end_latency_s"],
            "p_any_blocker": run["p_any_blocker"],
            **channel_metrics,
        })
    return out


def primary_task_cells(ds: Dataset, run_rows: list[dict[str, Any]] | None = None
                       ) -> list[dict[str, Any]]:
    """Collapse repeats/targets to one equally-standardised task × 2x2 cell.

    The nesting order is material: first audit repeats within an exact target,
    then generation repeats/registered targets within task.  An eligible target
    with no observed semantic outcome makes that task-cell missing rather than
    allowing the remaining targets to acquire accidental extra weight.
    """
    run_rows = run_rows if run_rows is not None else audit_run_rows(ds)
    p = ds.manifest["primary"]
    exact_groups: dict[tuple[str, str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    primary_artifacts = {
        a["artifact_id"] for a in ds.rows("artifacts")
        if a["phase"] == "initial" and a["defensive_arm"] is None
        and a["generator_vendor"] in p["generator_vendors"]
        and a["generation_repeat"] < p["generation_repeats"]
    }
    for row in run_rows:
        if row["artifact_id"] not in primary_artifacts:
            continue
        if (row["auditor_vendor"] not in p["auditor_vendors"]
                or row["dcl_level"] != p["dcl_level"]
                or row["constitution_level"] != p["constitution_level"]
                or row["audit_policy"] != p["audit_policy"]):
            continue
        exact_groups[(row["task_id"], row["target_id"], row["generator_vendor"],
                      row["auditor_vendor"], row["generation_repeat"])].append(row)

    exact_rows: list[dict[str, Any]] = []
    for (task_id, target_id, gv, av, generation_repeat), rows in sorted(exact_groups.items()):
        costs = [r["cost_usd"] for r in rows]
        true_n = sum(r["n_true_findings"] for r in rows)
        adj_n = sum(r["n_adjudicated_findings"] for r in rows)
        exact_rows.append({
            "task_id": task_id, "target_id": target_id,
            "generator_vendor": gv, "auditor_vendor": av,
            "generation_repeat": generation_repeat, "n_runs": len(rows),
            "requires_block": rows[0]["requires_block"],
            "has_gold": any(r["n_gold"] > 0 for r in rows),
            "recall": mean_or_none([r["recall"] for r in rows]),
            "correct_gate": mean_or_none([r["correct_gate"] for r in rows]),
            "false_block": mean_or_none([r["false_block"] for r in rows]),
            "operational_nonadmission": mean_or_none(
                [r["operational_nonadmission"] for r in rows]),
            "n_true_findings": true_n, "n_adjudicated_findings": adj_n,
            "n_caught": sum(r["n_caught"] for r in rows),
            "n_gold": sum(r["n_gold"] for r in rows),
            "cost_usd": (statistics.fmean(float(x) for x in costs)
                         if all(x is not None for x in costs) else None),
            "latency_s": mean_or_none([r["latency_s"] for r in rows]),
            "failure_rate": statistics.fmean(r["status"] != "ok" for r in rows),
            **{f"recall_{channel}": mean_or_none(
                [r[f"recall_{channel}"] for r in rows])
               for channel in ("script", "tool", "model", "human")},
        })

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in exact_rows:
        groups[(row["task_id"], row["generator_vendor"], row["auditor_vendor"])].append(row)

    def complete_mean(rows: list[dict[str, Any]], outcome: str,
                      eligible: Any = None) -> float | None:
        selected = [r for r in rows if eligible is None or eligible(r)]
        if not selected:
            return None
        values = [r[outcome] for r in selected]
        return statistics.fmean(float(v) for v in values) if all(
            v is not None for v in values) else None

    cells = []
    for (task_id, gv, av), rows in sorted(groups.items()):
        true_n = sum(r["n_true_findings"] for r in rows)
        adj_n = sum(r["n_adjudicated_findings"] for r in rows)
        cells.append({
            "task_id": task_id, "generator_vendor": gv, "auditor_vendor": av,
            "cross_vendor": gv != av,
            "n_exact_target_cells": len(rows),
            "n_runs": sum(r["n_runs"] for r in rows),
            "eligible_recall": any(r["has_gold"] for r in rows),
            "eligible_false_block": any(not r["requires_block"] for r in rows),
            "recall": complete_mean(rows, "recall", lambda r: r["has_gold"]),
            "correct_gate": complete_mean(rows, "correct_gate"),
            "false_block": complete_mean(
                rows, "false_block", lambda r: not r["requires_block"]),
            "operational_nonadmission": complete_mean(rows, "operational_nonadmission"),
            "precision": true_n / adj_n if adj_n else None,
            "n_true_findings": true_n, "n_adjudicated_findings": adj_n,
            "n_caught": sum(r["n_caught"] for r in rows),
            "n_gold": sum(r["n_gold"] for r in rows),
            "cost_usd": complete_mean(rows, "cost_usd"),
            "latency_s": complete_mean(rows, "latency_s"),
            "failure_rate": statistics.fmean(r["failure_rate"] for r in rows),
            **{f"recall_{channel}": complete_mean(rows, f"recall_{channel}")
               for channel in ("script", "tool", "model", "human")},
        })
    return cells


def condition_summaries(run_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Descriptive endpoints for every DCL/Constitution/audit/vendor condition."""
    keys = ("generator_vendor", "auditor_vendor", "dcl_level",
            "constitution_level", "audit_policy")
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in run_rows:
        groups[tuple(row[k] for k in keys)].append(row)
    out = []
    for key, rows in sorted(groups.items()):
        true_n = sum(r["n_true_findings"] for r in rows)
        adj_n = sum(r["n_adjudicated_findings"] for r in rows)
        gold_n = sum(r["n_gold"] for r in rows)
        caught_n = sum(r["n_caught"] for r in rows)
        costs = [r["cost_usd"] for r in rows]
        clean = [r for r in rows if not r["requires_block"]]
        out.append({
            **dict(zip(keys, key)), "n_runs": len(rows),
            "n_tasks": len({r["task_id"] for r in rows}),
            "macro_recall": mean_or_none([r["recall"] for r in rows]),
            "correct_gate": mean_or_none([r["correct_gate"] for r in rows]),
            "micro_recall": caught_n / gold_n if gold_n else None,
            "precision": true_n / adj_n if adj_n else None,
            "false_block_rate": mean_or_none([r["false_block"] for r in clean]),
            "operational_nonadmission_rate": mean_or_none(
                [r["operational_nonadmission"] for r in clean]),
            "failure_rate": statistics.fmean(r["status"] != "ok" for r in rows),
            "mean_cost_usd": mean_or_none(costs),
            "mean_latency_s": mean_or_none([r["latency_s"] for r in rows]),
            **{f"recall_{channel}": mean_or_none([r[f"recall_{channel}"] for r in rows])
               for channel in ("script", "tool", "model", "human")},
        })
    return out


def revision_rows(ds: Dataset) -> list[dict[str, Any]]:
    ix = _indices(ds)
    defects = ix["defects_by_artifact"]
    changes_by_revision: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in ds.rows("change_labels"):
        changes_by_revision[c["revision_id"]].append(c)
    out = []
    for revision in ds.rows("revisions"):
        parent = ix["artifacts"][revision["parent_artifact_id"]]
        child = ix["artifacts"][revision["child_artifact_id"]]
        before = {d["defect_key"] for d in defects[parent["artifact_id"]]
                  if d["gold_status"] == "confirmed"}
        after = {d["defect_key"] for d in defects[child["artifact_id"]]
                 if d["gold_status"] == "confirmed"}
        corrected, introduced = before - after, after - before
        labels = Counter(c["label"] for c in changes_by_revision[revision["revision_id"]])
        compliance_words = sum(c["added_words"] for c in changes_by_revision[revision["revision_id"]]
                               if c["label"] in {"compliance_only", "defensive_disclaimer"})
        out.append({
            "revision_id": revision["revision_id"], "task_id": parent["task_id"],
            "audit_policy": revision["audit_policy"], "status": revision["status"],
            "round": revision["round"], "escalated": revision["escalated"],
            "n_before": len(before), "n_after": len(after),
            "corrected": len(corrected), "introduced": len(introduced),
            "net_correction": len(corrected) - len(introduced),
            "net_correction_rate": (len(corrected) - len(introduced)) / max(1, len(before)),
            "change_labels": dict(labels), "compliance_added_words": compliance_words,
            "cost_usd": token_cost(revision, ix["prices"]),
            "latency_s": revision["latency_s"], "human_minutes": revision["human_minutes"],
            "revision_session_id": revision["revision_session_id"],
        })
    return out


def whole_loop_rows(ds: Dataset) -> list[dict[str, Any]]:
    """One initial-to-final row per loop episode, never one row per revision."""
    ix = _indices(ds)
    artifacts = ix["artifacts"]
    defects = ix["defects_by_artifact"]
    revisions = {r["revision_id"]: r for r in ds.rows("revisions")}
    revision_by_child = {r["child_artifact_id"]: r for r in revisions.values()}
    changes_by_revision: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for change in ds.rows("change_labels"):
        changes_by_revision[change["revision_id"]].append(change)
    out = []
    for final in ds.rows("artifacts"):
        if final["phase"] != "final" or final["baseline_artifact_id"] is None:
            continue
        initial = artifacts[final["baseline_artifact_id"]]
        chain: list[dict[str, Any]] = []
        cursor = final["artifact_id"]
        seen: set[str] = set()
        while cursor in revision_by_child:
            if cursor in seen:
                raise ValueError(f"revision chain cycle at {cursor!r}")
            seen.add(cursor)
            revision = revision_by_child[cursor]
            chain.append(revision)
            cursor = revision["parent_artifact_id"]
        if cursor != initial["artifact_id"] and chain:
            raise ValueError(
                f"final artifact {final['artifact_id']!r} does not trace to baseline")
        before = {d["defect_key"] for d in defects[initial["artifact_id"]]
                  if d["gold_status"] == "confirmed"}
        after = {d["defect_key"] for d in defects[final["artifact_id"]]
                 if d["gold_status"] == "confirmed"}
        corrected, introduced = before - after, after - before
        chain_changes = [c for revision in chain
                         for c in changes_by_revision[revision["revision_id"]]]
        labels = Counter(c["label"] for c in chain_changes)
        costs = [token_cost(r, ix["prices"]) for r in chain]
        out.append({
            "task_id": final["task_id"], "initial_artifact_id": initial["artifact_id"],
            "final_artifact_id": final["artifact_id"],
            "generator_session_id": final["generator_session_id"],
            "audit_policy": final["defensive_arm"], "n_revisions": len(chain),
            "resolved_fraction": len(corrected) / len(before) if before else None,
            "final_acceptable_blind": final["blind_final_acceptable"],
            "corrected": len(corrected), "introduced": len(introduced),
            "net_correction": len(corrected) - len(introduced),
            "unnecessary_change_count": sum(
                labels[name] for name in ("compliance_only", "defensive_disclaimer",
                                          "neutral", "harmful")),
            "compliance_only_count": labels["compliance_only"],
            "harmful_change_count": labels["harmful"],
            "change_count": len(chain_changes), "change_labels": dict(labels),
            "escalated": any(r["escalated"] for r in chain),
            "cost_usd": sum(float(c) for c in costs)
            if costs and all(c is not None for c in costs) else (0.0 if not costs else None),
            "latency_s": sum(r["latency_s"] for r in chain),
            "human_minutes": sum(r["human_minutes"] for r in chain),
        })
    return out


def defensive_rows(ds: Dataset) -> list[dict[str, Any]]:
    ix = _indices(ds)
    revisions_by_child = {r["child_artifact_id"]: r["revision_id"] for r in ds.rows("revisions")}
    changes_by_revision: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in ds.rows("change_labels"):
        changes_by_revision[c["revision_id"]].append(c)
    out = []
    for a in ds.rows("artifacts"):
        if a["phase"] != "final" or a["defensive_arm"] is None or a["baseline_artifact_id"] is None:
            continue
        base = ix["artifacts"][a["baseline_artifact_id"]]
        changes = changes_by_revision.get(revisions_by_child.get(a["artifact_id"], ""), [])
        compliance = sum(c["added_words"] for c in changes
                         if c["label"] in {"compliance_only", "defensive_disclaimer"})
        added = max(0, a["words"] - base["words"])
        out.append({
            "task_id": a["task_id"], "artifact_id": a["artifact_id"],
            "generator_session_id": a["generator_session_id"],
            "defensive_arm": a["defensive_arm"],
            "word_delta": a["words"] - base["words"],
            "loc_delta": a["loc"] - base["loc"],
            "file_delta": a["file_count"] - base["file_count"],
            "docs_word_delta": a["docs_words"] - base["docs_words"],
            "assertion_delta": a["assertion_count"] - base["assertion_count"],
            "disclaimer_delta": a["disclaimer_count"] - base["disclaimer_count"],
            "wrapper_delta": a["wrapper_count"] - base["wrapper_count"],
            "retry_delta": a["retry_count"] - base["retry_count"],
            "exception_handler_delta": (
                a["exception_handler_count"] - base["exception_handler_count"]),
            "dependency_delta": a["dependency_count"] - base["dependency_count"],
            "complexity_delta": (a["complexity"] - base["complexity"]
                                 if a["complexity"] is not None
                                 and base["complexity"] is not None else None),
            "compliance_added_words": compliance,
            "audit_overhead_ratio": compliance / max(1, added),
            "quality_score": a["quality_score"], "novelty_score": a["novelty_score"],
            "heldout_score": a["heldout_score"],
            "blind_final_acceptable": a["blind_final_acceptable"],
        })
    return out


def _finding_signature(run_id: str, by_run: dict[str, list[dict[str, Any]]],
                       matches: dict[str, dict[str, Any]]) -> set[str]:
    sig = set()
    for f in by_run[run_id]:
        if f["status"] != "alleged":
            continue
        m = matches[f["finding_id"]]
        if m["label"] == "true":
            sig.add(f"D:{m['defect_id']}")
        else:
            sig.add(f"F:{f['rule']}:{f['location']}:{m['label']}")
    return sig


def stability_metrics(ds: Dataset, run_rows: list[dict[str, Any]] | None = None
                      ) -> dict[str, Any]:
    run_rows = run_rows if run_rows is not None else audit_run_rows(ds)
    by_id = {r["audit_run_id"]: r for r in run_rows}
    raw_by_id = {r["audit_run_id"]: r for r in ds.rows("audit_runs")}
    by_run_findings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in ds.rows("findings"):
        by_run_findings[f["audit_run_id"]].append(f)
    matches = {m["finding_id"]: m for m in ds.rows("finding_matches")}
    groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for rid, raw in raw_by_id.items():
        key = (raw["artifact_id"], raw["auditor_vendor"], raw["auditor_model"],
               raw["dcl_level"], raw["constitution_level"], raw["audit_policy"])
        groups[key].append(rid)
    rows = []
    verdict_pairs: list[tuple[str, str]] = []
    catch_pairs: list[tuple[str, str]] = []

    def chance_kappa(pairs: list[tuple[str, str]]) -> float | None:
        if not pairs:
            return None
        observed = statistics.fmean(a == b for a, b in pairs)
        counts = Counter(label for pair in pairs for label in pair)
        total = 2 * len(pairs)
        expected = sum((n / total) ** 2 for n in counts.values())
        return (observed - expected) / (1 - expected) if expected < 1 else None
    for key, ids in sorted(groups.items()):
        if len(ids) < 2:
            continue
        pairs = list(itertools.combinations(sorted(ids), 2))
        local_verdict_pairs = [(raw_by_id[a]["controller_verdict"],
                                raw_by_id[b]["controller_verdict"]) for a, b in pairs]
        verdict_pairs.extend(local_verdict_pairs)
        verdict_disagreement = statistics.fmean(a != b for a, b in local_verdict_pairs)
        jaccards = []
        for left, right in pairs:
            a = _finding_signature(left, by_run_findings, matches)
            b = _finding_signature(right, by_run_findings, matches)
            jaccards.append(1.0 if not a and not b else len(a & b) / len(a | b))
        recalls = [by_id[r]["recall"] for r in ids if by_id[r]["recall"] is not None]
        gold_ids = {d["defect_id"] for d in ds.rows("defects")
                    if d["artifact_id"] == key[0] and d["gold_status"] == "confirmed"}
        local_catch_pairs: list[tuple[str, str]] = []
        all_repeat_catches = []
        for defect_id in sorted(gold_ids):
            states = [defect_id in by_id[r]["caught_defect_ids"] for r in sorted(ids)]
            all_repeat_catches.append(all(states))
            local_catch_pairs.extend((str(a), str(b)) for a, b in itertools.combinations(states, 2))
        catch_pairs.extend(local_catch_pairs)
        rows.append({
            "artifact_id": key[0], "auditor_vendor": key[1], "auditor_model": key[2],
            "dcl_level": key[3], "constitution_level": key[4], "audit_policy": key[5],
            "n_repeats": len(ids), "verdict_pair_disagreement": verdict_disagreement,
            "finding_jaccard": statistics.fmean(jaccards),
            "recall_sd": statistics.pstdev(recalls) if len(recalls) > 1 else 0.0,
            "verdict_chance_corrected_kappa": chance_kappa(local_verdict_pairs),
            "catch_pair_agreement": mean_or_none([a == b for a, b in local_catch_pairs]),
            "all_repeat_stable_catch_rate": mean_or_none(all_repeat_catches),
        })
    adjudicator_pairs = [(m["adjudicator_a_label"], m["adjudicator_b_label"])
                         for m in ds.rows("finding_matches")]
    return {
        "groups": rows,
        "mean_verdict_pair_disagreement": mean_or_none(
            [r["verdict_pair_disagreement"] for r in rows]),
        "mean_finding_jaccard": mean_or_none([r["finding_jaccard"] for r in rows]),
        "mean_recall_sd": mean_or_none([r["recall_sd"] for r in rows]),
        "verdict_chance_corrected_kappa": chance_kappa(verdict_pairs),
        "catch_chance_corrected_kappa": chance_kappa(catch_pairs),
        "adjudication_raw_agreement": mean_or_none(
            [a == b for a, b in adjudicator_pairs]),
        "adjudication_krippendorff_alpha_nominal": chance_kappa(adjudicator_pairs),
        "mean_all_repeat_stable_catch_rate": mean_or_none(
            [r["all_repeat_stable_catch_rate"] for r in rows]),
    }


def _calibration(records: list[tuple[float, int]], bins: int = 5) -> dict[str, Any]:
    if not records:
        return {"n": 0, "brier": None, "ece": None, "bins": []}
    brier = statistics.fmean((p - y) ** 2 for p, y in records)
    bucketed: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for p, y in records:
        bucketed[min(bins - 1, int(p * bins))].append((p, y))
    out, ece = [], 0.0
    for i, bucket in enumerate(bucketed):
        if not bucket:
            out.append({"lo": i / bins, "hi": (i + 1) / bins, "n": 0,
                        "mean_probability": None, "observed_rate": None})
            continue
        mp = statistics.fmean(p for p, _ in bucket)
        obs = statistics.fmean(y for _, y in bucket)
        ece += len(bucket) / len(records) * abs(mp - obs)
        out.append({"lo": i / bins, "hi": (i + 1) / bins, "n": len(bucket),
                    "mean_probability": mp, "observed_rate": obs})
    return {"n": len(records), "brier": brier, "ece": ece, "bins": out}


def calibration_metrics(ds: Dataset) -> dict[str, Any]:
    ix = _indices(ds)
    finding_records = []
    for f in ds.rows("findings"):
        if f["status"] != "alleged" or f["confidence"] is None:
            continue
        label = ix["matches_by_finding"][f["finding_id"]]["label"]
        if label in {"true", "false", "duplicate"}:
            finding_records.append((float(f["confidence"]), 1 if label == "true" else 0))
    verdict_records = []
    for run in ds.rows("audit_runs"):
        if run["status"] != "ok" or run["p_any_blocker"] is None:
            continue
        gold = any(d["gold_status"] == "confirmed" and d["severity"] == "BLOCKER"
                   for d in ix["defects_by_artifact"][run["artifact_id"]])
        verdict_records.append((float(run["p_any_blocker"]), int(gold)))
    return {"finding": _calibration(finding_records), "verdict": _calibration(verdict_records)}


def ledger_metrics(ds: Dataset) -> dict[str, Any]:
    assignments = {a["assignment_id"]: a for a in ds.rows("ledger_assignments")}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for o in ds.rows("ledger_outcomes"):
        groups[assignments[o["assignment_id"]]["surface"]].append(o)
    out = {}
    for surface, rows in sorted(groups.items()):
        tampered = [r for r in rows if r["tamper_truth"]]
        clean = [r for r in rows if not r["tamper_truth"]]
        out[surface] = {
            "n": len(rows),
            "accuracy": statistics.fmean(r["decision_correct"] for r in rows),
            "mean_provenance_score": statistics.fmean(r["provenance_score"] for r in rows),
            "tamper_recall": mean_or_none([r["tamper_flag"] for r in tampered]),
            "tamper_false_alarm": mean_or_none([r["tamper_flag"] for r in clean]),
            "mean_seconds": statistics.fmean(r["time_to_decision_s"] for r in rows),
            "median_seconds": statistics.median(r["time_to_decision_s"] for r in rows),
            "restricted_mean_time_to_correct_s": statistics.fmean(
                r["time_to_decision_s"] if r["decision_correct"]
                else r["registered_time_cap_s"] for r in rows),
            "censor_rate": statistics.fmean(r["decision_censored"] for r in rows),
            "first_defective_commit_accuracy": mean_or_none(
                [r["first_defective_commit_correct"] for r in rows]),
            "rule_version_accuracy": mean_or_none([r["rule_version_correct"] for r in rows]),
            "mean_review_burden": statistics.fmean(r["review_burden_score"] for r in rows),
            "confidence_brier": statistics.fmean(
                (r["confidence"] - int(r["decision_correct"])) ** 2 for r in rows),
        }
    return out


def cost_latency_metrics(ds: Dataset, run_rows: list[dict[str, Any]] | None = None
                         ) -> dict[str, Any]:
    run_rows = run_rows if run_rows is not None else audit_run_rows(ds)
    ix = _indices(ds)
    generation_costs = [token_cost(a, ix["prices"]) for a in ds.rows("artifacts")]
    audit_costs = [r["cost_usd"] for r in run_rows]
    revision_costs = [token_cost(r, ix["prices"]) for r in ds.rows("revisions")]

    def summarise(costs: list[float | None], latencies: list[float]) -> dict[str, Any]:
        known = [c for c in costs if c is not None]
        return {
            "n": len(costs), "n_missing_cost": len(costs) - len(known),
            "total_cost_usd": sum(known) if known else (0.0 if not costs else None),
            "mean_cost_usd": mean_or_none(known),
            "mean_latency_s": mean_or_none(latencies),
            "median_latency_s": median_or_none(latencies),
        }

    return {
        "generation": summarise(generation_costs, [a["latency_s"] for a in ds.rows("artifacts")]),
        "audit": summarise(audit_costs, [r["latency_s"] for r in run_rows]),
        "revision": summarise(revision_costs, [r["latency_s"] for r in ds.rows("revisions")]),
    }
