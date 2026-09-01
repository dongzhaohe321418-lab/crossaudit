#!/usr/bin/env python3
"""Versioned, dependency-free data contract for the CrossAudit v4 studies.

The contract is deliberately relational.  Raw model replies remain immutable
artefacts; these JSONL tables contain only the fields needed to reconstruct the
registered estimands.  Every row carries a schema version so that concatenating
incompatible study exports fails loudly instead of silently changing a metric.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "4.0"

# Registered factor vocabulary.  Human-readable meanings belong in the study
# registration; these stable codes are what analysis files join on.
DCL_LEVELS = {"D0", "D1", "D2", "D3"}
CONSTITUTION_LEVELS = {"C0", "C1", "C2"}
AUDIT_POLICIES = {"P0", "P1", "P2"}
COMPONENT_VERDICTS = {"PASS", "BLOCKED", "ERROR", "NOT_RUN"}
CONTROLLER_VERDICTS = {"PASS", "BLOCKED", "ERROR"}
LEDGER_SURFACES = {"E0", "E1", "E2"}

TABLE_FILES = {
    "tasks": "tasks.jsonl",
    "artifacts": "artifacts.jsonl",
    "defects": "defects.jsonl",
    "audit_runs": "audit_runs.jsonl",
    "findings": "findings.jsonl",
    "finding_matches": "finding_matches.jsonl",
    "revisions": "revisions.jsonl",
    "change_labels": "change_labels.jsonl",
    "ledger_assignments": "ledger_assignments.jsonl",
    "ledger_outcomes": "ledger_outcomes.jsonl",
}

ID_FIELDS = {
    "tasks": "task_id",
    "artifacts": "artifact_id",
    "defects": "defect_id",
    "audit_runs": "audit_run_id",
    "findings": "finding_id",
    "finding_matches": "match_id",
    "revisions": "revision_id",
    "change_labels": "change_id",
    "ledger_assignments": "assignment_id",
    "ledger_outcomes": "outcome_id",
}

SHA256 = re.compile(r"^[0-9a-f]{64}$")


class DataValidationError(ValueError):
    """Raised when a v4 dataset cannot support the registered analysis."""


@dataclass(frozen=True)
class Dataset:
    root: Path
    manifest: dict[str, Any]
    tables: dict[str, list[dict[str, Any]]]
    price_table: dict[str, Any]

    def rows(self, name: str) -> list[dict[str, Any]]:
        return self.tables[name]


def _fail(source: str, message: str) -> None:
    raise DataValidationError(f"{source}: {message}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _require(record: dict[str, Any], fields: dict[str, Any], source: str) -> None:
    missing = sorted(set(fields) - set(record))
    if missing:
        _fail(source, f"missing required fields: {', '.join(missing)}")
    for name, expected in fields.items():
        value = record[name]
        accepted = expected if isinstance(expected, tuple) else (expected,)
        if value is None and type(None) in accepted:
            continue
        non_null = tuple(t for t in accepted if t is not type(None))
        if bool in non_null:
            good = type(value) is bool
        elif int in non_null and float not in non_null:
            good = type(value) is int
        elif float in non_null:
            good = _is_number(value)
        else:
            good = isinstance(value, non_null)
        if not good:
            names = "/".join(t.__name__ for t in accepted)
            _fail(source, f"field {name!r} must be {names}, got {type(value).__name__}")


def _enum(record: dict[str, Any], field: str, allowed: set[Any], source: str) -> None:
    if record[field] not in allowed:
        _fail(source, f"field {field!r} must be one of {sorted(str(x) for x in allowed)}")


def _nonnegative(record: dict[str, Any], fields: tuple[str, ...], source: str) -> None:
    for field in fields:
        if record[field] < 0:
            _fail(source, f"field {field!r} must be non-negative")


def _probability(value: Any, source: str, field: str) -> None:
    if value is not None and (not _is_number(value) or not 0 <= value <= 1):
        _fail(source, f"field {field!r} must be null or in [0, 1]")


def validate_manifest_shape(manifest: dict[str, Any], source: str = "study_manifest.json") -> None:
    _require(manifest, {
        "schema_version": str,
        "study_id": str,
        "hashes": dict,
        "primary": dict,
        "bootstrap": dict,
    }, source)
    if manifest["schema_version"] != SCHEMA_VERSION:
        _fail(source, f"schema_version must be {SCHEMA_VERSION!r}")
    for name in ("corpus_sha256", "analysis_plan_sha256", "code_sha256"):
        value = manifest["hashes"].get(name)
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            _fail(source, f"hashes.{name} must be a lowercase SHA-256")
    primary = manifest["primary"]
    _require(primary, {
        "generator_vendors": list,
        "auditor_vendors": list,
        "generation_repeats": int,
        "audit_repeats": int,
        "dcl_level": str,
        "constitution_level": str,
        "audit_policy": str,
        "alpha": float,
        "false_block_noninferiority_margin": float,
    }, f"{source}.primary")
    if len(primary["generator_vendors"]) != 2 or len(set(primary["generator_vendors"])) != 2:
        _fail(source, "primary.generator_vendors must contain exactly two distinct values")
    if len(primary["auditor_vendors"]) != 2 or len(set(primary["auditor_vendors"])) != 2:
        _fail(source, "primary.auditor_vendors must contain exactly two distinct values")
    if set(primary["generator_vendors"]) != set(primary["auditor_vendors"]):
        _fail(source, "primary generator and auditor vendor sets must be identical")
    if primary["generation_repeats"] < 1 or primary["audit_repeats"] < 1:
        _fail(source, "primary repeat counts must be positive")
    _enum(primary, "dcl_level", DCL_LEVELS, f"{source}.primary")
    _enum(primary, "constitution_level", CONSTITUTION_LEVELS, f"{source}.primary")
    _enum(primary, "audit_policy", AUDIT_POLICIES, f"{source}.primary")
    if primary["alpha"] != 0.05:
        _fail(source, "v4 confirmatory analysis currently registers alpha=0.05")
    if primary["false_block_noninferiority_margin"] != 0.05:
        _fail(source, "v4 registers the clean false-block non-inferiority margin at 0.05")
    _require(manifest["bootstrap"], {"seed": int, "draws": int}, f"{source}.bootstrap")
    if manifest["bootstrap"]["draws"] < 0:
        _fail(source, "bootstrap.draws must be non-negative")


def validate_record_shape(table: str, r: dict[str, Any], source: str) -> None:
    _require(r, {"schema_version": str}, source)
    if r["schema_version"] != SCHEMA_VERSION:
        _fail(source, f"schema_version must be {SCHEMA_VERSION!r}")

    if table == "tasks":
        _require(r, {"task_id": str, "domain": str, "stratum": str}, source)
    elif table == "artifacts":
        _require(r, {
            "artifact_id": str, "task_id": str, "phase": str,
            # base_artifact_id is the clean/mutant sibling cluster.  target_id
            # is the fixed standardisation cell shared across vendors; unlike
            # artifact_id neither is a foreign key into this table.
            "base_artifact_id": str, "target_id": str,
            "parent_artifact_id": (str, type(None)), "baseline_artifact_id": (str, type(None)),
            "defensive_arm": (str, type(None)), "generator_vendor": str,
            "generator_model": str, "generator_session_id": str,
            "generation_repeat": int,
            "gold_kind": str, "requires_block": bool,
            "file_count": int, "bytes": int, "loc": int, "words": int,
            "docs_words": int, "assertion_count": int, "disclaimer_count": int,
            "wrapper_count": int, "retry_count": int,
            "exception_handler_count": int, "dependency_count": int,
            "complexity": (float, type(None)),
            "quality_score": (float, type(None)), "novelty_score": (float, type(None)),
            "heldout_score": (float, type(None)),
            "blind_final_acceptable": (bool, type(None)),
            "input_tokens": int, "output_tokens": int, "cached_tokens": int,
            "reasoning_tokens": int, "latency_s": float, "price_key": (str, type(None)),
        }, source)
        _enum(r, "phase", {"initial", "revision", "final"}, source)
        _enum(r, "gold_kind", {"controlled_clean", "controlled_mutant", "natural"}, source)
        if r["defensive_arm"] is not None:
            _enum(r, "defensive_arm", AUDIT_POLICIES, source)
        _nonnegative(r, ("generation_repeat", "file_count", "bytes", "loc", "words",
                         "docs_words", "assertion_count", "disclaimer_count", "input_tokens",
                         "wrapper_count", "retry_count", "exception_handler_count",
                         "dependency_count", "input_tokens", "output_tokens", "cached_tokens",
                         "reasoning_tokens", "latency_s"), source)
        if r["complexity"] is not None and r["complexity"] < 0:
            _fail(source, "field 'complexity' must be null or non-negative")
        _probability(r["quality_score"], source, "quality_score")
        _probability(r["novelty_score"], source, "novelty_score")
        _probability(r["heldout_score"], source, "heldout_score")
        for field in ("base_artifact_id", "target_id", "generator_session_id"):
            if not r[field].strip():
                _fail(source, f"field {field!r} must be non-empty")
    elif table == "defects":
        _require(r, {
            "defect_id": str, "defect_key": str, "artifact_id": str, "class": str,
            "channel": str, "severity": str, "location": str, "gold_status": str,
        }, source)
        _enum(r, "channel", {"script", "tool", "model", "human"}, source)
        _enum(r, "severity", {"BLOCKER", "ADVISORY"}, source)
        _enum(r, "gold_status", {"confirmed", "absent", "unresolved"}, source)
    elif table == "audit_runs":
        _require(r, {
            "audit_run_id": str, "artifact_id": str, "generator_vendor": str,
            "auditor_vendor": str, "auditor_model": str, "audit_repeat": int,
            "dcl_level": str, "constitution_level": str, "audit_policy": str,
            "status": str, "model_verdict": str, "dcl_verdict": str,
            "controller_verdict": str, "p_any_blocker": (float, type(None)),
            "input_tokens": int, "output_tokens": int, "cached_tokens": int,
            "reasoning_tokens": int, "provider_latency_s": float,
            "end_to_end_latency_s": float, "price_key": (str, type(None)),
        }, source)
        _enum(r, "dcl_level", DCL_LEVELS, source)
        _enum(r, "constitution_level", CONSTITUTION_LEVELS, source)
        _enum(r, "audit_policy", AUDIT_POLICIES, source)
        _enum(r, "status", {"ok", "provider_error", "parse_error", "timeout"}, source)
        _enum(r, "model_verdict", COMPONENT_VERDICTS, source)
        _enum(r, "dcl_verdict", COMPONENT_VERDICTS, source)
        _enum(r, "controller_verdict", CONTROLLER_VERDICTS, source)
        _nonnegative(r, ("audit_repeat", "input_tokens", "output_tokens", "cached_tokens",
                         "reasoning_tokens", "provider_latency_s", "end_to_end_latency_s"), source)
        _probability(r["p_any_blocker"], source, "p_any_blocker")
        if r["status"] == "ok" and r["controller_verdict"] == "ERROR":
            _fail(source, "a successful audit cannot have controller_verdict ERROR")
        if r["status"] != "ok" and r["controller_verdict"] != "ERROR":
            _fail(source, "a failed audit must have controller_verdict ERROR")
    elif table == "findings":
        _require(r, {
            "finding_id": str, "audit_run_id": str, "severity": str,
            "origin": str,
            "rule": (str, type(None)), "location": str, "status": str,
            "confidence": (float, type(None)), "blocked_scope": bool,
        }, source)
        _enum(r, "severity", {"BLOCKER", "ADVISORY"}, source)
        _enum(r, "origin", {"dcl", "model", "controller", "human"}, source)
        _enum(r, "status", {"alleged", "withdrawn", "referral"}, source)
        _probability(r["confidence"], source, "confidence")
    elif table == "finding_matches":
        _require(r, {
            "match_id": str, "finding_id": str, "defect_id": (str, type(None)),
            "label": str, "adjudicator_a": str, "adjudicator_b": str,
            "adjudicator_a_label": str, "adjudicator_b_label": str,
            "agreement": bool,
        }, source)
        _enum(r, "label", {"true", "false", "duplicate", "unresolved"}, source)
        _enum(r, "adjudicator_a_label", {"true", "false", "duplicate", "unresolved"}, source)
        _enum(r, "adjudicator_b_label", {"true", "false", "duplicate", "unresolved"}, source)
        if r["agreement"] != (r["adjudicator_a_label"] == r["adjudicator_b_label"]):
            _fail(source, "agreement must equal adjudicator label equality")
        if r["label"] == "true" and r["defect_id"] is None:
            _fail(source, "a true match must name a defect_id")
        if r["label"] == "false" and r["defect_id"] is not None:
            _fail(source, "a false match must have defect_id=null")
    elif table == "revisions":
        _require(r, {
            "revision_id": str, "parent_artifact_id": str, "child_artifact_id": str,
            "trigger_audit_run_id": (str, type(None)), "audit_policy": str,
            "revision_session_id": str,
            "round": int, "status": str, "escalated": bool,
            "input_tokens": int, "output_tokens": int, "cached_tokens": int,
            "reasoning_tokens": int, "latency_s": float, "human_minutes": float,
            "price_key": (str, type(None)),
        }, source)
        _enum(r, "audit_policy", AUDIT_POLICIES, source)
        _enum(r, "status", {"ok", "error"}, source)
        _nonnegative(r, ("round", "input_tokens", "output_tokens", "cached_tokens",
                         "reasoning_tokens", "latency_s", "human_minutes"), source)
    elif table == "change_labels":
        _require(r, {
            "change_id": str, "revision_id": str, "label": str,
            "added_words": int, "deleted_words": int, "added_loc": int,
            "deleted_loc": int, "files_touched": int,
        }, source)
        _enum(r, "label", {"functional_improvement", "necessary_evidence",
                            "compliance_only", "defensive_disclaimer", "neutral",
                            "harmful"}, source)
        _nonnegative(r, ("added_words", "deleted_words", "added_loc", "deleted_loc",
                         "files_touched"), source)
    elif table == "ledger_assignments":
        _require(r, {
            "assignment_id": str, "reviewer_id": str, "session_id": str,
            "episode_id": str, "surface": str, "attack_class": (str, type(None)),
            "period": int, "order_seed": int,
        }, source)
        _enum(r, "surface", LEDGER_SURFACES, source)
        _nonnegative(r, ("period",), source)
    elif table == "ledger_outcomes":
        _require(r, {
            "outcome_id": str, "assignment_id": str, "decision_correct": bool,
            "decision_resolved": bool, "decision_censored": bool,
            "time_to_decision_s": float,
            "registered_time_cap_s": float,
            "provenance_score": float, "tamper_truth": bool, "tamper_flag": bool,
            "first_defective_commit_correct": (bool, type(None)),
            "rule_version_correct": (bool, type(None)), "confidence": float,
            "review_burden_score": float,
        }, source)
        _probability(r["provenance_score"], source, "provenance_score")
        _probability(r["confidence"], source, "confidence")
        _probability(r["review_burden_score"], source, "review_burden_score")
        _nonnegative(r, ("time_to_decision_s", "registered_time_cap_s"), source)
        if r["registered_time_cap_s"] <= 0:
            _fail(source, "registered_time_cap_s must be positive")
        if r["time_to_decision_s"] > r["registered_time_cap_s"]:
            _fail(source, "time_to_decision_s cannot exceed registered_time_cap_s")
        if r["decision_correct"] and not r["decision_resolved"]:
            _fail(source, "a correct decision must be resolved")
        if r["decision_censored"] == r["decision_correct"]:
            _fail(source, "decision_censored must be the complement of decision_correct")
    else:
        _fail(source, f"unknown table {table!r}")

    ident = r.get(ID_FIELDS[table])
    if not isinstance(ident, str) or not ident.strip():
        _fail(source, f"{ID_FIELDS[table]} must be a non-empty string")


def validate_price_table_shape(table: dict[str, Any], source: str = "price_table.json") -> None:
    _require(table, {"schema_version": str, "currency": str, "prices": list}, source)
    if table["schema_version"] != SCHEMA_VERSION:
        _fail(source, f"schema_version must be {SCHEMA_VERSION!r}")
    if table["currency"] != "USD":
        _fail(source, "v4 reports monetary costs in USD")
    seen: set[str] = set()
    for i, p in enumerate(table["prices"], 1):
        src = f"{source}:prices[{i}]"
        _require(p, {
            "price_key": str, "provider": str, "model": str,
            "input_per_million": float, "output_per_million": float,
            "cached_per_million": float, "reasoning_per_million": float,
            "effective_date": str,
        }, src)
        _nonnegative(p, ("input_per_million", "output_per_million",
                         "cached_per_million", "reasoning_per_million"), src)
        if p["price_key"] in seen:
            _fail(src, f"duplicate price_key {p['price_key']!r}")
        seen.add(p["price_key"])


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise DataValidationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataValidationError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise DataValidationError(f"{path}: top level must be an object")
    return value


def _read_jsonl(path: Path, table: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError as exc:
        raise DataValidationError(f"missing required file: {path}") from exc
    rows: list[dict[str, Any]] = []
    for line_no, text in enumerate(lines, 1):
        if not text.strip():
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DataValidationError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise DataValidationError(f"{path}:{line_no}: each line must be an object")
        validate_record_shape(table, value, f"{path}:{line_no}")
        rows.append(value)
    return rows


def load_dataset(root: str | Path) -> Dataset:
    root = Path(root)
    manifest = _read_json(root / "study_manifest.json")
    validate_manifest_shape(manifest, str(root / "study_manifest.json"))
    price_table = _read_json(root / "price_table.json")
    validate_price_table_shape(price_table, str(root / "price_table.json"))
    tables = {name: _read_jsonl(root / filename, name)
              for name, filename in TABLE_FILES.items()}
    return Dataset(root=root, manifest=manifest, tables=tables, price_table=price_table)
