"""Receipt verification and admission, end to end against real git trees.

Behaviours 2, 3 and 4 of the ROADMAP-R2 status line: PASS admits and consumes,
a replayed receipt is denied, a tampered artefact is denied. Post-hoc regression
tests (finding R5); see conftest.py.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import CONTROLLER, REPO as REPO_ROOT, git, init_repo

SCIENCE_REPO = "owner/science-repo"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Env:
    def __init__(self, sci: Path, aud: Path, controller: Path, receipt: Path,
                 sha: str, cycle_id: str, receipt_hash: str, state):
        self.sci, self.aud, self.controller = sci, aud, controller
        self.receipt, self.sha = receipt, sha
        self.cycle_id, self.receipt_hash, self.state = cycle_id, receipt_hash, state

    def verify(self, admit: bool = True) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(self.controller / "verify_receipt.py"),
               "--receipt", str(self.receipt), "--science-root", str(self.sci),
               "--audit-root", str(self.aud), "--expect-repo", SCIENCE_REPO,
               "--expect-sha", self.sha]
        if admit:
            cmd.append("--admit")
        return subprocess.run(cmd, capture_output=True, text=True)

    def rewrite_receipt(self, **changes) -> None:
        """Rewrite the receipt and re-bind the state to its new hash."""
        r = json.loads(self.receipt.read_text()) | changes
        self.receipt.write_text(json.dumps(r, indent=2, sort_keys=True))
        self.receipt_hash = sha256_bytes(self.receipt.read_bytes())
        self.state.record_verdict(self.cycle_id, self.sha, "PASS",
                                  self.receipt_hash, 3)


@pytest.fixture()
def env(tmp_path: Path, controller_copy: Path, state) -> Env:
    sci = tmp_path / "science"
    init_repo(sci)
    (sci / "results.json").write_text('{"binding_energy": -3.65}\n')
    (sci / "metadata.yml").write_text("code_version: c001beef\n")
    git("add", "-A", cwd=sci)
    git("commit", "-qm", "increment", cwd=sci)
    sha = git("rev-parse", "HEAD", cwd=sci)
    tree = git("rev-parse", "HEAD^{tree}", cwd=sci)

    aud = tmp_path / "audit"
    init_repo(aud)
    (aud / "AUDIT_RULES.md").write_text("### CA-DATA-001\nEvery numeric entry carries unit and source.\n")
    (aud / "checks").mkdir()
    for f in sorted((REPO_ROOT / "checks").glob("*.py")):
        (aud / "checks" / f.name).write_bytes(f.read_bytes())
    git("add", "-A", cwd=aud)
    git("commit", "-qm", "constitution and checks", cwd=aud)
    const_commit = git("log", "-1", "--format=%H", "--", "AUDIT_RULES.md", cwd=aud)
    dcl_digest = sha256_bytes(b"".join(p.read_bytes()
                                       for p in sorted((aud / "checks").glob("*.py"))))

    cycle_dir = aud / "cycles" / sha
    cycle_dir.mkdir(parents=True)
    report = cycle_dir / "report.md"
    report.write_text("# Audit Report\n\nNo blockers.\n")

    receipt = cycle_dir / "receipt.json"
    receipt.write_text(json.dumps({
        "science_repo": SCIENCE_REPO, "sha": sha, "tree": tree, "round": 1,
        "cycle_id": state.cycle_id_for(SCIENCE_REPO, sha),
        "manifest": {"results.json": sha256_bytes((sci / "results.json").read_bytes()),
                     "notes.md": "ABSENT"},
        "constitution_hash": const_commit,
        "dcl_source_sha256": dcl_digest,
        "prompt_sha256": sha256_bytes(b"prompt"),
        "report_sha256": sha256_bytes(report.read_bytes()),
        "auditor_model": "test-auditor", "verdict": "PASS",
        "audit_integrity": "OK",
    }, indent=2, sort_keys=True))
    receipt_hash = sha256_bytes(receipt.read_bytes())

    cycle = state.open_or_advance(SCIENCE_REPO, sha, None)
    state.record_verdict(cycle["cycle_id"], sha, "PASS", receipt_hash, 3)
    return Env(sci, aud, controller_copy, receipt, sha, cycle["cycle_id"],
               receipt_hash, state)


def test_pass_receipt_admits_and_consumes(env: Env):
    r = env.verify()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ADMIT" in r.stdout and "consumed" in r.stdout
    assert env.state._load()["cycles"][env.cycle_id]["status"] == "CONSUMED"


def test_dry_run_verifies_without_consuming(env: Env):
    r = env.verify(admit=False)
    assert r.returncode == 0 and "not consumed" in r.stdout
    assert env.state._load()["cycles"][env.cycle_id]["status"] == "PASSED"


def test_replayed_receipt_is_denied(env: Env):
    assert env.verify().returncode == 0
    replay = env.verify()
    assert replay.returncode != 0
    assert replay.stdout.startswith("DENY")


def test_tampered_science_artifact_is_denied(env: Env):
    (env.sci / "results.json").write_text('{"binding_energy": 3.65}\n')
    r = env.verify()
    assert r.returncode != 0 and "manifest mismatch" in r.stdout
    assert env.state._load()["cycles"][env.cycle_id]["status"] == "PASSED"


def test_tampered_report_is_denied(env: Env):
    (env.receipt.parent / "report.md").write_text("# Audit Report\n\nAll fine, promise.\n")
    r = env.verify()
    assert r.returncode != 0 and "report blob hash mismatch" in r.stdout


def test_tampered_constitution_is_denied(env: Env):
    (env.aud / "AUDIT_RULES.md").write_text("### CA-DATA-001\nAnything goes.\n")
    git("add", "-A", cwd=env.aud)
    git("commit", "-qm", "weaken the constitution", cwd=env.aud)
    r = env.verify()
    assert r.returncode != 0 and "constitution commit" in r.stdout


def test_tampered_check_layer_is_denied(env: Env):
    (env.aud / "checks" / "run_checks.py").write_text("# neutered\n")
    r = env.verify()
    assert r.returncode != 0 and "DCL source hash mismatch" in r.stdout


def test_manifest_absent_entry_that_exists_is_denied(env: Env):
    (env.sci / "notes.md").write_text("smuggled in after the audit\n")
    r = env.verify()
    assert r.returncode != 0 and "ABSENT" in r.stdout


def test_non_pass_verdict_is_not_admissible(env: Env):
    env.rewrite_receipt(verdict="BLOCKED")
    r = env.verify()
    assert r.returncode != 0 and "not PASS" in r.stdout


def test_failed_audit_integrity_is_not_admissible(env: Env):
    env.rewrite_receipt(audit_integrity="TRUNCATED_INPUT")
    r = env.verify()
    assert r.returncode != 0 and "audit integrity" in r.stdout


def test_unversioned_constitution_is_denied(env: Env):
    env.rewrite_receipt(constitution_hash="unversioned")
    r = env.verify()
    assert r.returncode != 0 and "unversioned" in r.stdout


def test_missing_required_field_is_denied(env: Env):
    r = json.loads(env.receipt.read_text())
    del r["auditor_model"]
    env.receipt.write_text(json.dumps(r, indent=2, sort_keys=True))
    out = env.verify()
    assert out.returncode != 0 and "missing fields" in out.stdout


def test_receipt_for_another_sha_is_denied(env: Env):
    env.rewrite_receipt(sha="c" * 40)
    r = env.verify()
    assert r.returncode != 0 and "sha" in r.stdout


def test_receipt_outside_its_cycle_directory_is_denied(env: Env, tmp_path: Path):
    stray = tmp_path / "elsewhere"
    stray.mkdir()
    (stray / "report.md").write_bytes((env.receipt.parent / "report.md").read_bytes())
    (stray / "receipt.json").write_bytes(env.receipt.read_bytes())
    env.receipt = stray / "receipt.json"
    r = env.verify()
    assert r.returncode != 0 and "cycle dir" in r.stdout


def test_suite_does_not_write_repository_state(env: Env):
    """state.py resolves its store relative to its own file, so a test that ran
    the real module rather than the copy would deposit cycle state in the
    repository. Catch that here rather than in a diff."""
    env.verify()
    assert not (CONTROLLER / "state.json").exists(), (
        "a test wrote controller/state.json into the repository")
