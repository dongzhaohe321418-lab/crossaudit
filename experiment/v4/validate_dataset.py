#!/usr/bin/env python3
"""Fail-closed relational and design validation for a CrossAudit v4 export."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from typing import Any
from pathlib import Path

from schema import DataValidationError, Dataset, ID_FIELDS, load_dataset


def _index_unique(ds: Dataset, table: str) -> dict[str, dict[str, Any]]:
    field = ID_FIELDS[table]
    out: dict[str, dict[str, Any]] = {}
    for row in ds.rows(table):
        key = row[field]
        if key in out:
            raise DataValidationError(f"{table}: duplicate {field} {key!r}")
        out[key] = row
    return out


def _require_ref(table: str, row_id: str, field: str, value: str | None,
                 target: dict[str, Any], nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if value not in target:
        raise DataValidationError(
            f"{table} {row_id!r}: {field} references missing value {value!r}")


def _validate_parent_graph(artifacts: dict[str, dict[str, Any]]) -> None:
    for artifact_id in artifacts:
        seen: set[str] = set()
        current: str | None = artifact_id
        while current is not None:
            if current in seen:
                raise DataValidationError(f"artifacts: parent cycle contains {current!r}")
            seen.add(current)
            current = artifacts[current]["parent_artifact_id"]


def validate_dataset(ds: Dataset) -> dict[str, Any]:
    """Validate references, truth labels, and the registered primary factorial.

    The primary design is intention-to-audit: failed calls satisfy the scheduled
    cell but remain records with verdict ERROR.  They are never dropped here or
    by the metric layer.
    """
    idx = {name: _index_unique(ds, name) for name in ID_FIELDS}
    tasks, artifacts, defects = idx["tasks"], idx["artifacts"], idx["defects"]
    runs, findings, matches = idx["audit_runs"], idx["findings"], idx["finding_matches"]
    revisions, changes = idx["revisions"], idx["change_labels"]
    assignments, outcomes = idx["ledger_assignments"], idx["ledger_outcomes"]
    prices = {p["price_key"]: p for p in ds.price_table["prices"]}

    for aid, a in artifacts.items():
        _require_ref("artifacts", aid, "task_id", a["task_id"], tasks)
        _require_ref("artifacts", aid, "parent_artifact_id", a["parent_artifact_id"],
                     artifacts, nullable=True)
        _require_ref("artifacts", aid, "baseline_artifact_id", a["baseline_artifact_id"],
                     artifacts, nullable=True)
        _require_ref("artifacts", aid, "price_key", a["price_key"], prices, nullable=True)
        if a["parent_artifact_id"] == aid or a["baseline_artifact_id"] == aid:
            raise DataValidationError(f"artifacts {aid!r}: cannot reference itself")
        if a["parent_artifact_id"] is not None:
            parent = artifacts[a["parent_artifact_id"]]
            if parent["task_id"] != a["task_id"]:
                raise DataValidationError(f"artifacts {aid!r}: parent belongs to another task")
        if a["baseline_artifact_id"] is not None:
            base = artifacts[a["baseline_artifact_id"]]
            if base["task_id"] != a["task_id"]:
                raise DataValidationError(f"artifacts {aid!r}: baseline belongs to another task")
    _validate_parent_graph(artifacts)

    for did, d in defects.items():
        _require_ref("defects", did, "artifact_id", d["artifact_id"], artifacts)
    for aid, artifact in artifacts.items():
        blockers = [d for d in defects.values() if d["artifact_id"] == aid
                    and d["gold_status"] == "confirmed" and d["severity"] == "BLOCKER"]
        if artifact["gold_kind"] == "controlled_clean" and artifact["requires_block"]:
            raise DataValidationError(f"artifacts {aid!r}: controlled_clean cannot require block")
        if artifact["gold_kind"] == "controlled_mutant" and not artifact["requires_block"]:
            raise DataValidationError(f"artifacts {aid!r}: controlled_mutant must require block")
        if artifact["requires_block"] and not blockers:
            raise DataValidationError(f"artifacts {aid!r}: requires_block lacks confirmed BLOCKER gold")
        if not artifact["requires_block"] and blockers:
            raise DataValidationError(f"artifacts {aid!r}: pass-required artifact has BLOCKER gold")

    run_factor_keys: set[tuple[Any, ...]] = set()
    for rid, r in runs.items():
        _require_ref("audit_runs", rid, "artifact_id", r["artifact_id"], artifacts)
        _require_ref("audit_runs", rid, "price_key", r["price_key"], prices, nullable=True)
        a = artifacts[r["artifact_id"]]
        if r["generator_vendor"] != a["generator_vendor"]:
            raise DataValidationError(
                f"audit_runs {rid!r}: generator_vendor disagrees with its artifact")
        if r["provider_latency_s"] > r["end_to_end_latency_s"]:
            raise DataValidationError(
                f"audit_runs {rid!r}: provider latency exceeds end-to-end latency")
        key = (r["artifact_id"], r["auditor_vendor"], r["auditor_model"], r["audit_repeat"],
               r["dcl_level"], r["constitution_level"], r["audit_policy"])
        if key in run_factor_keys:
            raise DataValidationError(f"audit_runs {rid!r}: duplicate run-factor cell")
        run_factor_keys.add(key)
        if r["status"] == "ok":
            model, dcl, controller = (r["model_verdict"], r["dcl_verdict"],
                                      r["controller_verdict"])
            if r["dcl_level"] == "D0":
                if dcl != "NOT_RUN" or model not in {"PASS", "BLOCKED"}:
                    raise DataValidationError(
                        f"audit_runs {rid!r}: D0 requires model verdict and dcl NOT_RUN")
                expected = model
            elif r["dcl_level"] == "D1":
                if model != "NOT_RUN" or dcl not in {"PASS", "BLOCKED"}:
                    raise DataValidationError(
                        f"audit_runs {rid!r}: D1 requires dcl verdict and model NOT_RUN")
                expected = dcl
            else:
                if model not in {"PASS", "BLOCKED"} or dcl not in {"PASS", "BLOCKED"}:
                    raise DataValidationError(
                        f"audit_runs {rid!r}: {r['dcl_level']} requires both component verdicts")
                # The registered D2 controller is deterministic and auditor-blind:
                # either component may block.  D3 keeps that safe precedence while
                # changing routing, not the final admission rule.
                expected = "BLOCKED" if "BLOCKED" in {model, dcl} else "PASS"
            if controller != expected:
                raise DataValidationError(
                    f"audit_runs {rid!r}: controller verdict violates {r['dcl_level']} precedence")

    by_run_findings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fid, f in findings.items():
        _require_ref("findings", fid, "audit_run_id", f["audit_run_id"], runs)
        if runs[f["audit_run_id"]]["status"] != "ok":
            raise DataValidationError(f"findings {fid!r}: failed audit cannot emit findings")
        by_run_findings[f["audit_run_id"]].append(f)

    by_finding_match: dict[str, list[dict[str, Any]]] = defaultdict(list)
    true_per_run_defect: set[tuple[str, str]] = set()
    for mid, m in matches.items():
        _require_ref("finding_matches", mid, "finding_id", m["finding_id"], findings)
        _require_ref("finding_matches", mid, "defect_id", m["defect_id"], defects,
                     nullable=True)
        by_finding_match[m["finding_id"]].append(m)
        f = findings[m["finding_id"]]
        run = runs[f["audit_run_id"]]
        if m["defect_id"] is not None:
            d = defects[m["defect_id"]]
            if d["artifact_id"] != run["artifact_id"]:
                raise DataValidationError(
                    f"finding_matches {mid!r}: finding and defect belong to different artifacts")
            if m["label"] == "true" and d["gold_status"] != "confirmed":
                raise DataValidationError(
                    f"finding_matches {mid!r}: true match requires confirmed gold")
        if m["label"] == "true":
            pair = (f["audit_run_id"], m["defect_id"])
            if pair in true_per_run_defect:
                raise DataValidationError(
                    f"finding_matches {mid!r}: one defect was credited twice in one audit")
            true_per_run_defect.add(pair)
        if m["agreement"] and m["label"] != m["adjudicator_a_label"]:
            raise DataValidationError(
                f"finding_matches {mid!r}: agreed panel label differs from final label")

    for fid, f in findings.items():
        attached = by_finding_match[fid]
        if f["status"] == "alleged" and len(attached) != 1:
            raise DataValidationError(
                f"findings {fid!r}: every allegation needs exactly one adjudication row")
        if f["status"] != "alleged" and attached:
            raise DataValidationError(
                f"findings {fid!r}: withdrawn/referral entries cannot be scored")

    # A controller BLOCK may be caused by a deterministic DCL referral rather
    # than a model-originated allegation.  Component/controller precedence is
    # checked above; findings are therefore not incorrectly forced to reproduce
    # the controller decision.

    for rev_id, rev in revisions.items():
        _require_ref("revisions", rev_id, "parent_artifact_id", rev["parent_artifact_id"], artifacts)
        _require_ref("revisions", rev_id, "child_artifact_id", rev["child_artifact_id"], artifacts)
        _require_ref("revisions", rev_id, "trigger_audit_run_id",
                     rev["trigger_audit_run_id"], runs, nullable=True)
        _require_ref("revisions", rev_id, "price_key", rev["price_key"], prices, nullable=True)
        child = artifacts[rev["child_artifact_id"]]
        parent = artifacts[rev["parent_artifact_id"]]
        if child["parent_artifact_id"] != rev["parent_artifact_id"]:
            raise DataValidationError(
                f"revisions {rev_id!r}: child artifact does not name the registered parent")
        if child["task_id"] != parent["task_id"]:
            raise DataValidationError(f"revisions {rev_id!r}: artifacts belong to different tasks")
    for change_id, change in changes.items():
        _require_ref("change_labels", change_id, "revision_id", change["revision_id"], revisions)

    outcomes_by_assignment: Counter[str] = Counter()
    for oid, outcome in outcomes.items():
        _require_ref("ledger_outcomes", oid, "assignment_id", outcome["assignment_id"], assignments)
        outcomes_by_assignment[outcome["assignment_id"]] += 1
    for assignment_id in assignments:
        if outcomes_by_assignment[assignment_id] != 1:
            raise DataValidationError(
                f"ledger_assignments {assignment_id!r}: expected exactly one outcome")
    if assignments:
        per_reviewer: dict[str, Counter[str]] = defaultdict(Counter)
        per_episode: dict[str, Counter[str]] = defaultdict(Counter)
        seen_exposure: set[tuple[str, str]] = set()
        seen_period: set[tuple[str, str, int]] = set()
        for a in assignments.values():
            exposure = (a["reviewer_id"], a["episode_id"])
            if exposure in seen_exposure:
                raise DataValidationError(
                    "ledger_assignments: within-session episode crossover is forbidden")
            seen_exposure.add(exposure)
            period = (a["reviewer_id"], a["session_id"], a["period"])
            if period in seen_period:
                raise DataValidationError(
                    "ledger_assignments: a session period can contain only one episode")
            seen_period.add(period)
            per_reviewer[a["reviewer_id"]][a["surface"]] += 1
            per_episode[a["episode_id"]][a["surface"]] += 1
        expected_surfaces = {"E0", "E1", "E2"}
        for reviewer, counts in per_reviewer.items():
            if set(counts) != expected_surfaces or len(set(counts.values())) != 1:
                raise DataValidationError(
                    f"ledger_assignments: reviewer {reviewer!r} lacks a balanced surface set")
        for episode, counts in per_episode.items():
            if set(counts) != expected_surfaces or len(set(counts.values())) != 1:
                raise DataValidationError(
                    f"ledger_assignments: episode {episode!r} is not crossed over surfaces")
        totals = Counter(a["surface"] for a in assignments.values())
        if max(totals.values()) - min(totals.values()) > 1:
            raise DataValidationError("ledger_assignments: surfaces are globally unbalanced")

    # Registered 2x2 primary completeness.  Extra ablation and defensive records
    # may coexist, but primary records must form a complete, balanced panel.
    p = ds.manifest["primary"]
    primary_artifacts: dict[tuple[str, str, str, int], str] = {}
    target_metadata: dict[tuple[str, str], tuple[str, bool]] = {}
    for aid, a in artifacts.items():
        if a["phase"] != "initial" or a["defensive_arm"] is not None:
            continue
        if a["generator_vendor"] not in p["generator_vendors"]:
            continue
        key = (a["task_id"], a["target_id"], a["generator_vendor"],
               a["generation_repeat"])
        if key in primary_artifacts:
            raise DataValidationError(f"artifacts: duplicate primary artifact cell {key!r}")
        primary_artifacts[key] = aid
        metadata_key = (a["task_id"], a["target_id"])
        # target_id is the fixed standardisation cell shared across generator
        # vendors. base_artifact_id is deliberately not shared: each vendor
        # produces its own base and clean/mutant sibling pair.
        metadata = (a["gold_kind"], a["requires_block"])
        prior = target_metadata.setdefault(metadata_key, metadata)
        if prior[0] != metadata[0] or (metadata[0] != "natural" and prior != metadata):
            raise DataValidationError(
                f"artifacts: target {metadata_key!r} changes controlled gold across vendors")

    for task_id in tasks:
        targets = sorted(target for (task, target) in target_metadata if task == task_id)
        if not targets:
            raise DataValidationError(f"primary design has no target cells for task {task_id!r}")
        for target in targets:
            for gv in p["generator_vendors"]:
                for gr in range(p["generation_repeats"]):
                    key = (task_id, target, gv, gr)
                    if key not in primary_artifacts:
                        raise DataValidationError(f"primary design missing artifact cell {key!r}")

    primary_run_cells: Counter[tuple[str, str, int]] = Counter()
    for r in runs.values():
        if (r["dcl_level"] != p["dcl_level"]
                or r["constitution_level"] != p["constitution_level"]
                or r["audit_policy"] != p["audit_policy"]):
            continue
        if r["artifact_id"] not in set(primary_artifacts.values()):
            continue
        if r["auditor_vendor"] not in p["auditor_vendors"]:
            continue
        primary_run_cells[(r["artifact_id"], r["auditor_vendor"], r["audit_repeat"])] += 1
    for aid in primary_artifacts.values():
        for av in p["auditor_vendors"]:
            for ar in range(p["audit_repeats"]):
                key = (aid, av, ar)
                if primary_run_cells[key] != 1:
                    raise DataValidationError(
                        f"primary design expected one audit run for cell {key!r}, "
                        f"found {primary_run_cells[key]}")

    return {
        "schema_version": ds.manifest["schema_version"],
        "study_id": ds.manifest["study_id"],
        "n_tasks": len(tasks),
        "n_artifacts": len(artifacts),
        "n_audit_runs": len(runs),
        "n_failed_audit_runs": sum(r["status"] != "ok" for r in runs.values()),
        "n_findings": len(findings),
        "n_revisions": len(revisions),
        "n_ledger_assignments": len(assignments),
        "primary_cells_complete": True,
        "validation_scope": "statistical JSON/JSONL contract and registered cell balance only",
        "dispatch_freeze_validated": False,
    }


def validate_controlled_siblings(ds: Dataset) -> None:
    """Enforce the registered clean/mutant construction for dispatch."""
    controlled: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    base_owners: dict[str, tuple[str, str, int]] = {}
    confirmed_blockers: Counter[str] = Counter(
        defect["artifact_id"] for defect in ds.rows("defects")
        if defect["gold_status"] == "confirmed" and defect["severity"] == "BLOCKER"
    )
    for artifact in ds.rows("artifacts"):
        if artifact["phase"] != "initial" or artifact["gold_kind"] == "natural":
            continue
        owner = (artifact["task_id"], artifact["generator_vendor"],
                 artifact["generation_repeat"])
        prior_owner = base_owners.setdefault(artifact["base_artifact_id"], owner)
        if prior_owner != owner:
            raise DataValidationError(
                f"controlled base {artifact['base_artifact_id']!r} is reused across generators")
        controlled[(*owner, artifact["base_artifact_id"])].append(artifact)
    for key, siblings in controlled.items():
        kinds = Counter(artifact["gold_kind"] for artifact in siblings)
        if kinds != {"controlled_clean": 1, "controlled_mutant": 1}:
            raise DataValidationError(
                f"controlled base {key!r} must contain exactly one clean and one mutant sibling")
        clean = next(a for a in siblings if a["gold_kind"] == "controlled_clean")
        mutant = next(a for a in siblings if a["gold_kind"] == "controlled_mutant")
        if clean["requires_block"] or not mutant["requires_block"]:
            raise DataValidationError(
                f"controlled base {key!r} has inconsistent clean/mutant gate gold")
        if confirmed_blockers[clean["artifact_id"]] != 0 \
                or confirmed_blockers[mutant["artifact_id"]] != 1:
            raise DataValidationError(
                f"controlled base {key!r} must have zero clean and one mutant BLOCKER")


def validate_freeze_configuration(freeze_root: str | Path) -> dict[str, Any]:
    """Fail closed on unresolved confirmatory configuration before any data exist.

    This is intentionally narrower than :func:`validate_dispatch_freeze`: it
    validates the prospective study/model configuration without requiring a
    results-shaped dataset.  Passing it is necessary but never sufficient for
    dispatch; the frozen corpus, schedule, hashes, caps and cell balance still
    have to pass the full validator.
    """
    root = Path(freeze_root)

    def resolve(*relative_candidates: str) -> Path:
        for relative in relative_candidates:
            candidate = root / relative
            if candidate.is_file():
                return candidate
        return root / relative_candidates[0]

    study = resolve("config/study.yaml", "experiment/v4/config/study.yaml", "study.yaml")
    models = resolve("config/models.lock.json", "experiment/v4/config/models.lock.json",
                     "models.lock.json")
    for path in (study, models):
        if not path.is_file() or not path.read_bytes():
            raise DataValidationError(f"dispatch freeze missing non-empty {path}")

    placeholder = re.compile(r"^(?:null|~|tbd|todo|placeholder|not[_ -]?assigned|"
                             r"unfrozen(?:_blocking)?|changeme)$", re.I)

    def concrete(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip()) and not placeholder.fullmatch(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    def validate_json_required(node: Any, where: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key.endswith("_required_before_dispatch") and value is True:
                    target = key.removesuffix("_required_before_dispatch")
                    if target not in node or not concrete(node[target]):
                        raise DataValidationError(
                            f"dispatch freeze unresolved required field {where}.{target}")
            if node.get("required_before_dispatch") is True:
                for key, value in node.items():
                    if key in {"required_before_dispatch", "note"}:
                        continue
                    if not concrete(value):
                        raise DataValidationError(
                            f"dispatch freeze unresolved required field {where}.{key}")
            for key, value in node.items():
                validate_json_required(value, f"{where}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                validate_json_required(value, f"{where}[{i}]")

    try:
        model_lock = json.loads(models.read_text())
    except json.JSONDecodeError as exc:
        raise DataValidationError(f"dispatch freeze invalid JSON in {models}: {exc}") from exc
    validate_json_required(model_lock, "models.lock")
    model_status = model_lock.get("status") if isinstance(model_lock, dict) else None
    if not concrete(model_status) or "UNFROZEN" in str(model_status).upper():
        raise DataValidationError("dispatch freeze models.lock status is not frozen")

    # The study file deliberately avoids adding a YAML runtime dependency.
    # Required scalar pairs use strict mapping syntax and are compared among
    # siblings at the same indentation.
    yaml_scalars: dict[tuple[str, ...], str] = {}
    stack: list[tuple[int, str]] = []
    for line in study.read_text().splitlines():
        match = re.match(r"^(\s*)([A-Za-z0-9_]+):(?:\s*(.*?))?\s*$", line)
        if match:
            indent, key, raw = len(match.group(1)), match.group(2), match.group(3) or ""
            while stack and stack[-1][0] >= indent:
                stack.pop()
            path = tuple(name for _, name in stack) + (key,)
            value = raw.strip().strip('"\'')
            yaml_scalars[path] = value
            if not value:
                stack.append((indent, key))
    for path, raw in yaml_scalars.items():
        key = path[-1]
        if not key.endswith("_required_before_dispatch") or raw.lower() != "true":
            continue
        target = key.removesuffix("_required_before_dispatch")
        target_path = path[:-1] + (target,)
        value = yaml_scalars.get(target_path, "")
        if not concrete(None if value.lower() in {"", "null", "~"} else value):
            raise DataValidationError(
                f"dispatch freeze unresolved required field study.yaml:{'.'.join(target_path)}")

    return {
        "configuration_fields_validated": True,
        "dispatch_ready": False,
        "scope": "configuration-only; full corpus/schedule/hash validation still required",
        "study_yaml": str(study),
        "study_yaml_sha256": hashlib.sha256(study.read_bytes()).hexdigest(),
        "models_lock": str(models),
        "models_lock_sha256": hashlib.sha256(models.read_bytes()).hexdigest(),
    }


def validate_dispatch_freeze(ds: Dataset, freeze_root: str | Path) -> dict[str, Any]:
    """Validate the separate pre-dispatch freeze contract.

    This deliberately is not implied by :func:`validate_dataset`.  Dispatch
    requires the human-facing study plan and model lock, their committed hashes,
    the 120-task floor, and explicit call/cost/time caps.
    """
    root = Path(freeze_root)
    # Run the results-independent gate first.  This ordering makes unresolved
    # governance/model fields visible before any results-shaped file is needed.
    validate_freeze_configuration(root)

    def resolve(*relative_candidates: str) -> Path:
        for relative in relative_candidates:
            candidate = root / relative
            if candidate.is_file():
                return candidate
        return root / relative_candidates[0]

    study = resolve("config/study.yaml", "experiment/v4/config/study.yaml", "study.yaml")
    models = resolve("config/models.lock.json", "experiment/v4/config/models.lock.json",
                     "models.lock.json")
    for path in (study, models):
        if not path.is_file() or not path.read_bytes():
            raise DataValidationError(f"dispatch freeze missing non-empty {path}")

    placeholder = re.compile(r"^(?:null|~|tbd|todo|placeholder|not[_ -]?assigned|"
                             r"unfrozen(?:_blocking)?|changeme)$", re.I)

    def concrete(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip()) and not placeholder.fullmatch(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    def validate_json_required(node: Any, where: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key.endswith("_required_before_dispatch") and value is True:
                    target = key.removesuffix("_required_before_dispatch")
                    if target not in node or not concrete(node[target]):
                        raise DataValidationError(
                            f"dispatch freeze unresolved required field {where}.{target}")
            if node.get("required_before_dispatch") is True:
                for key, value in node.items():
                    if key in {"required_before_dispatch", "note"}:
                        continue
                    if not concrete(value):
                        raise DataValidationError(
                            f"dispatch freeze unresolved required field {where}.{key}")
            for key, value in node.items():
                validate_json_required(value, f"{where}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                validate_json_required(value, f"{where}[{i}]")

    try:
        model_lock = json.loads(models.read_text())
    except json.JSONDecodeError as exc:
        raise DataValidationError(f"dispatch freeze invalid JSON in {models}: {exc}") from exc
    validate_json_required(model_lock, "models.lock")
    model_status = model_lock.get("status") if isinstance(model_lock, dict) else None
    if not concrete(model_status) or "UNFROZEN" in str(model_status).upper():
        raise DataValidationError("dispatch freeze models.lock status is not frozen")

    # The study file is intentionally YAML, while this package has no YAML
    # dependency.  Required scalar pairs use a strict, simple mapping syntax;
    # inspect siblings at equal indentation and fail closed on null/placeholders.
    yaml_lines = study.read_text().splitlines()
    yaml_scalars: dict[tuple[str, ...], str] = {}
    stack: list[tuple[int, str]] = []
    for line in yaml_lines:
        match = re.match(r"^(\s*)([A-Za-z0-9_]+):(?:\s*(.*?))?\s*$", line)
        if match:
            indent, key, raw = len(match.group(1)), match.group(2), match.group(3) or ""
            while stack and stack[-1][0] >= indent:
                stack.pop()
            path = tuple(name for _, name in stack) + (key,)
            value = raw.strip().strip('"\'')
            yaml_scalars[path] = value
            if not value:
                stack.append((indent, key))
    for path, raw in yaml_scalars.items():
        key = path[-1]
        if not key.endswith("_required_before_dispatch") or raw.lower() != "true":
            continue
        target = key.removesuffix("_required_before_dispatch")
        target_path = path[:-1] + (target,)
        value = yaml_scalars.get(target_path, "")
        if not concrete(None if value.lower() in {"", "null", "~"} else value):
            raise DataValidationError(
                f"dispatch freeze unresolved required field study.yaml:{'.'.join(target_path)}")

    dispatch = ds.manifest.get("dispatch")
    if not isinstance(dispatch, dict):
        raise DataValidationError("study_manifest.json: dispatch caps are not frozen")
    for field in ("max_calls", "max_cost_usd", "max_wall_seconds"):
        value = dispatch.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise DataValidationError(f"study_manifest.json: dispatch.{field} must be positive")
    hashes = ds.manifest["hashes"]
    for field, path in (("study_yaml_sha256", study), ("models_lock_sha256", models)):
        expected = hashes.get(field)
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected != observed:
            raise DataValidationError(f"dispatch freeze hash mismatch for {path.name}")
    if len(ds.rows("tasks")) < 120:
        raise DataValidationError(
            f"dispatch requires at least 120 tasks, found {len(ds.rows('tasks'))}")
    domains = {task["domain"] for task in ds.rows("tasks")}
    if len(domains) < 3:
        raise DataValidationError("dispatch requires at least three represented task domains")
    gold_kinds = {artifact["gold_kind"] for artifact in ds.rows("artifacts")
                  if artifact["phase"] == "initial"}
    if not {"controlled_clean", "controlled_mutant", "natural"} <= gold_kinds:
        raise DataValidationError(
            "dispatch requires controlled clean/mutant and natural initial strata")
    if not any(task["stratum"] == "real_task_replay" for task in ds.rows("tasks")):
        raise DataValidationError("dispatch requires the registered real_task_replay stratum")

    # This is a confirmatory dispatch gate rather than a requirement for small
    # statistical fixtures.
    validate_controlled_siblings(ds)
    p = ds.manifest["primary"]
    if ds.manifest["bootstrap"]["draws"] < 5_000:
        raise DataValidationError("dispatch requires bootstrap.draws >= 5000")
    n_primary_artifacts = sum(
        a["phase"] == "initial" and a["defensive_arm"] is None
        and a["generator_vendor"] in p["generator_vendors"]
        for a in ds.rows("artifacts"))
    planned_calls = (n_primary_artifacts
                     + n_primary_artifacts * len(p["auditor_vendors"])
                     * p["audit_repeats"])
    if planned_calls > dispatch["max_calls"]:
        raise DataValidationError(
            f"planned primary calls {planned_calls} exceed cap {dispatch['max_calls']}")
    vendors = model_lock.get("vendors", {})
    for vendor in p["generator_vendors"]:
        lock = vendors.get(vendor)
        if not isinstance(lock, dict):
            raise DataValidationError(f"models.lock missing primary vendor {vendor!r}")
        generator = lock.get("generator", {})
        auditor = lock.get("auditor", {})
        if model_lock.get("core_same_vendor_generator_auditor_same_snapshot_required"):
            if (generator.get("model_id"), generator.get("snapshot_or_revision")) != (
                    auditor.get("model_id"), auditor.get("snapshot_or_revision")):
                raise DataValidationError(
                    f"models.lock vendor {vendor!r} violates same-snapshot diagonal")
        actual_generators = {a["generator_model"] for a in ds.rows("artifacts")
                             if a["phase"] == "initial"
                             and a["generator_vendor"] == vendor}
        if actual_generators != {generator.get("model_id")}:
            raise DataValidationError(
                f"dataset generator model rows disagree with models.lock vendor {vendor!r}")
        actual_auditors = {r["auditor_model"] for r in ds.rows("audit_runs")
                           if r["auditor_vendor"] == vendor}
        if actual_auditors != {auditor.get("model_id")}:
            raise DataValidationError(
                f"dataset auditor model rows disagree with models.lock vendor {vendor!r}")
    return {"dispatch_freeze_validated": True, "n_tasks": len(ds.rows("tasks")),
            "planned_primary_calls": planned_calls, "caps": dispatch,
            "study_yaml_sha256": hashes["study_yaml_sha256"],
            "models_lock_sha256": hashes["models_lock_sha256"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("--dispatch-freeze-root")
    args = ap.parse_args()
    try:
        ds = load_dataset(args.dataset)
        report = validate_dataset(ds)
        if args.dispatch_freeze_root:
            report["dispatch"] = validate_dispatch_freeze(ds, args.dispatch_freeze_root)
            report["dispatch_freeze_validated"] = True
    except DataValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
