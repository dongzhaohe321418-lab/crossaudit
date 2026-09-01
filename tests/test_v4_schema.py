from __future__ import annotations

import json

import pytest

from tests.test_v4_helpers import copy_fixture, read_jsonl, write_jsonl

from metrics import audit_run_rows
from schema import DataValidationError, load_dataset
from validate_dataset import (validate_controlled_siblings, validate_dataset,
                              validate_dispatch_freeze,
                              validate_freeze_configuration)


def test_minimal_fixture_is_complete_and_failed_call_stays_in_itt():
    ds = load_dataset(__import__("tests.test_v4_helpers", fromlist=["FIXTURE"]).FIXTURE)
    report = validate_dataset(ds)
    assert report["primary_cells_complete"] is True
    assert report["n_audit_runs"] == 16
    assert report["n_failed_audit_runs"] == 1
    rows = audit_run_rows(ds)
    failed = next(r for r in rows if r["status"] == "parse_error")
    assert failed["recall"] is None
    assert failed["operational_nonadmission"] == 1.0


def test_duplicate_id_is_rejected(tmp_path):
    root = copy_fixture(tmp_path)
    rows = read_jsonl(root / "tasks.jsonl")
    rows.append(dict(rows[0]))
    write_jsonl(root / "tasks.jsonl", rows)
    with pytest.raises(DataValidationError, match="duplicate task_id"):
        validate_dataset(load_dataset(root))


def test_missing_primary_cell_is_rejected(tmp_path):
    root = copy_fixture(tmp_path)
    rows = read_jsonl(root / "audit_runs.jsonl")
    rows = [r for r in rows if r["audit_run_id"] != "R-C-A-A-0"]
    write_jsonl(root / "audit_runs.jsonl", rows)
    with pytest.raises(DataValidationError, match="expected one audit run"):
        validate_dataset(load_dataset(root))


def test_dangling_reference_is_rejected(tmp_path):
    root = copy_fixture(tmp_path)
    rows = read_jsonl(root / "defects.jsonl")
    rows[0]["artifact_id"] = "MISSING"
    write_jsonl(root / "defects.jsonl", rows)
    with pytest.raises(DataValidationError, match="references missing"):
        validate_dataset(load_dataset(root))


def test_one_defect_cannot_receive_two_true_credits_in_one_run(tmp_path):
    root = copy_fixture(tmp_path)
    findings = read_jsonl(root / "findings.jsonl")
    findings.append({
        "schema_version": "4.0", "finding_id": "F-DUP", "audit_run_id": "R-D-A-B-0",
        "severity": "BLOCKER", "origin": "model", "rule": "CA-X-001",
        "location": "report:1",
        "status": "alleged", "confidence": 0.8, "blocked_scope": True,
    })
    matches = read_jsonl(root / "finding_matches.jsonl")
    matches.append({
        "schema_version": "4.0", "match_id": "M-DUP", "finding_id": "F-DUP",
        "defect_id": "D-A", "label": "true", "adjudicator_a": "J1",
        "adjudicator_b": "J2", "adjudicator_a_label": "true",
        "adjudicator_b_label": "true", "agreement": True,
    })
    write_jsonl(root / "findings.jsonl", findings)
    write_jsonl(root / "finding_matches.jsonl", matches)
    with pytest.raises(DataValidationError, match="credited twice"):
        validate_dataset(load_dataset(root))


def test_old_factor_vocabulary_is_rejected(tmp_path):
    root = copy_fixture(tmp_path)
    manifest = json.loads((root / "study_manifest.json").read_text())
    manifest["primary"]["dcl_level"] = "on"
    (root / "study_manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(DataValidationError, match="dcl_level"):
        load_dataset(root)


def test_extra_vendor_records_do_not_break_registered_two_vendor_primary(tmp_path):
    root = copy_fixture(tmp_path)
    artifacts = read_jsonl(root / "artifacts.jsonl")
    extra = dict(artifacts[0])
    extra.update({"artifact_id": "A-C-C", "generator_vendor": "C",
                  "generator_model": "gen-c"})
    artifacts.append(extra)
    write_jsonl(root / "artifacts.jsonl", artifacts)
    report = validate_dataset(load_dataset(root))
    assert report["primary_cells_complete"] is True


def test_artifact_level_gold_allows_vendor_specific_natural_siblings(tmp_path):
    root = copy_fixture(tmp_path)
    artifacts = read_jsonl(root / "artifacts.jsonl")
    targets = [a for a in artifacts if a["artifact_id"] in {"A-C-A", "A-C-B"}]
    for target in targets:
        target["gold_kind"] = "natural"
    next(a for a in targets if a["artifact_id"] == "A-C-B")["requires_block"] = True
    defects = read_jsonl(root / "defects.jsonl")
    defects.append({
        "schema_version": "4.0", "defect_id": "D-NAT", "defect_key": "NAT-1",
        "artifact_id": "A-C-B", "class": "natural", "channel": "human",
        "severity": "BLOCKER", "location": "report:2", "gold_status": "confirmed",
    })
    write_jsonl(root / "artifacts.jsonl", artifacts)
    write_jsonl(root / "defects.jsonl", defects)
    assert validate_dataset(load_dataset(root))["primary_cells_complete"] is True


def test_statistical_validation_does_not_claim_dispatch_freeze(tmp_path):
    root = copy_fixture(tmp_path)
    ds = load_dataset(root)
    assert validate_dataset(ds)["dispatch_freeze_validated"] is False
    with pytest.raises(DataValidationError, match="study.yaml"):
        validate_dispatch_freeze(ds, root)


def test_confirmatory_dispatch_requires_clean_mutant_siblings():
    ds = load_dataset(__import__("tests.test_v4_helpers", fromlist=["FIXTURE"]).FIXTURE)
    with pytest.raises(DataValidationError, match="one clean and one mutant sibling"):
        validate_controlled_siblings(ds)


def test_configuration_preflight_blocks_before_results_are_loaded():
    root = __import__("tests.test_v4_helpers", fromlist=["FIXTURE"]).FIXTURE.parents[1]
    with pytest.raises(DataValidationError, match="vendor_code_mapping.status"):
        validate_freeze_configuration(root)
