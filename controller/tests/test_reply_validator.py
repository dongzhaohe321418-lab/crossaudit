"""Auditor-reply validation and the offline verdict floor.

The negatives the 2026-07-30 audit hardened I3 against (fabricated rule ID, no
cited coverage, PASS carrying a BLOCKER), plus the I8 floor: with no model audit
the pipeline mints DCL_ONLY, never a conforming PASS. Post-hoc regression tests
(finding R5); see conftest.py.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO as REPO_ROOT, git, init_repo

AUDIT_SCRIPT = REPO_ROOT / "examples/minimal/audit-repo/scripts/run_llm_audit.py"
CONSTITUTION = REPO_ROOT / "examples/minimal/audit-repo/AUDIT_RULES.md"
KNOWN = {"CA-DATA-001", "CA-DATA-002", "CA-METH-002"}


@pytest.fixture(scope="module")
def audit_mod():
    spec = importlib.util.spec_from_file_location("run_llm_audit", AUDIT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def valid_reply(**changes) -> dict:
    return {"verdict": "PASS", "sections_applied": ["CA-DATA-001"],
            "findings": []} | changes


def test_a_conforming_reply_validates(audit_mod):
    assert audit_mod.validate_reply(valid_reply(), KNOWN) is None


def test_unknown_rule_id_in_coverage_is_invalid(audit_mod):
    why = audit_mod.validate_reply(valid_reply(sections_applied=["CA-NOPE-999"]), KNOWN)
    assert why and "not in the Constitution" in why


def test_unknown_rule_id_in_a_finding_is_invalid(audit_mod):
    reply = valid_reply(verdict="BLOCKED", findings=[
        {"severity": "BLOCKER", "rule": "CA-INVENTED-001", "observation": "x"}])
    why = audit_mod.validate_reply(reply, KNOWN)
    assert why and "not in the Constitution" in why


@pytest.mark.parametrize("applied", [[], None, "CA-DATA-001"])
def test_empty_or_malformed_coverage_is_invalid(audit_mod, applied):
    why = audit_mod.validate_reply(valid_reply(sections_applied=applied), KNOWN)
    assert why and "no sections_applied" in why


def test_pass_carrying_a_blocker_is_invalid(audit_mod):
    reply = valid_reply(findings=[
        {"severity": "BLOCKER", "rule": "CA-DATA-001", "observation": "unit missing"}])
    why = audit_mod.validate_reply(reply, KNOWN)
    assert why == "verdict PASS while carrying a BLOCKER finding"


def test_blocked_without_a_blocker_finding_is_invalid(audit_mod):
    reply = valid_reply(verdict="BLOCKED", findings=[
        {"severity": "ADVISORY", "rule": "CA-DATA-001", "observation": "nit"}])
    why = audit_mod.validate_reply(reply, KNOWN)
    assert why == "verdict BLOCKED without any BLOCKER finding"


@pytest.mark.parametrize("verdict", ["APPROVED", "", None, "pass"])
def test_verdicts_outside_the_vocabulary_are_invalid(audit_mod, verdict):
    why = audit_mod.validate_reply(valid_reply(verdict=verdict), KNOWN)
    assert why == "missing/invalid verdict"


def test_invalid_severity_is_rejected(audit_mod):
    reply = valid_reply(findings=[
        {"severity": "CRITICAL", "rule": "CA-DATA-001", "observation": "x"}])
    why = audit_mod.validate_reply(reply, KNOWN)
    assert why and "invalid severity" in why


def test_constitution_rule_ids_parse_out_of_the_shipped_example():
    """The validator's `known_rules` comes from this regex over the Constitution;
    if the heading style drifts, every rule id silently becomes unknown."""
    rules = set(re.findall(r"^### (CA-[A-Z]+-\d+)", CONSTITUTION.read_text(), re.M))
    assert len(rules) >= 3, rules


def test_offline_run_mints_dcl_only_not_pass(tmp_path: Path):
    """I8 floor, end to end: no model audit ran, so the pipeline may report the
    deterministic layer's result and nothing stronger."""
    sci = tmp_path / "science"
    init_repo(sci)
    (sci / "results.json").write_text('{"binding_energy": -3.65}\n')
    git("add", "-A", cwd=sci)
    git("commit", "-qm", "increment", cwd=sci)

    aud = tmp_path / "audit"
    (aud / "scripts").mkdir(parents=True)
    (aud / "scripts" / "run_llm_audit.py").write_bytes(AUDIT_SCRIPT.read_bytes())
    (aud / "AUDIT_RULES.md").write_bytes(CONSTITUTION.read_bytes())
    checks_json = aud / "checks.json"
    checks_json.write_text(json.dumps({"crossaudit_dcl_version": 1, "verdict": "PASS",
                                       "total_hard_failures": 0, "results": []}))
    changed = aud / "changed.txt"
    changed.write_text("results.json\n")

    r = subprocess.run(
        [sys.executable, str(aud / "scripts/run_llm_audit.py"),
         "--science-root", str(sci), "--science-repo", "owner/science-repo",
         "--constitution", str(aud / "AUDIT_RULES.md"), "--checks", str(checks_json),
         "--changed", str(changed), "--out", "receipt.json", "--offline"],
        cwd=aud, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

    receipt = json.loads(next(aud.glob("cycles/*/receipt.json")).read_text())
    assert receipt["verdict"] == "DCL_ONLY"
    assert receipt["verdict"] != "PASS"
