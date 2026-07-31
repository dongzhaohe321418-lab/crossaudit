#!/usr/bin/env python3
"""Full receipt verification (R2 §2). Exit 0 = ADMIT-eligible; nonzero = DENY, reason on stdout.

Verifies, against a fetched audit-ledger commit and a science checkout:
  schema and required fields · science repo identity · resolved sha + tree hash ·
  per-file manifest against the science tree · constitution / DCL-source / prompt
  hashes against the audit tree · report blob hash · verdict · controller freshness
  (state machine PASSED + active + unconsumed, via state.py admit).

Usage:
  python3 verify_receipt.py --receipt <receipt.json> --science-root <dir> \
      --audit-root <dir> --expect-repo <owner/sci> --expect-sha <full-sha> \
      [--admit]   # perform the state-machine admission (single-use)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REQUIRED = ("science_repo", "sha", "tree", "round", "cycle_id", "manifest",
            "constitution_hash", "dcl_source_sha256", "prompt_sha256",
            "report_sha256", "auditor_model", "verdict", "audit_integrity")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()


def fail(msg: str) -> None:
    print(f"DENY: {msg}")
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--science-root", type=Path, required=True)
    ap.add_argument("--audit-root", type=Path, required=True)
    ap.add_argument("--expect-repo", required=True)
    ap.add_argument("--expect-sha", required=True)
    ap.add_argument("--admit", action="store_true")
    a = ap.parse_args()

    try:
        r = json.loads(a.receipt.read_text())
    except Exception as exc:  # noqa: BLE001
        fail(f"receipt unparsable: {exc}")
    missing = [k for k in REQUIRED if k not in r]
    if missing:
        fail(f"receipt missing fields: {missing}")
    if r["science_repo"] != a.expect_repo:
        fail(f"science_repo {r['science_repo']} != expected {a.expect_repo}")
    if r["sha"] != a.expect_sha:
        fail(f"sha {r['sha']} != expected {a.expect_sha}")
    head = sh("git", "-C", str(a.science_root), "rev-parse", "HEAD")
    tree = sh("git", "-C", str(a.science_root), "rev-parse", "HEAD^{tree}")
    if head != r["sha"]:
        fail(f"science checkout HEAD {head[:12]} != receipt sha")
    if tree != r["tree"]:
        fail(f"science tree {tree[:12]} != receipt tree")
    for rel, digest in r["manifest"].items():
        p = a.science_root / rel
        if digest == "ABSENT":
            if p.exists():
                fail(f"manifest says ABSENT but {rel} exists")
        elif not p.is_file() or sha256_file(p) != digest:
            fail(f"manifest mismatch for {rel}")
    const = a.audit_root / "AUDIT_RULES.md"
    if not const.is_file():
        fail("constitution missing in audit tree")
    const_commit = sh("git", "-C", str(a.audit_root), "log", "-1", "--format=%H",
                      "--", "AUDIT_RULES.md")
    if r["constitution_hash"] == "unversioned":
        fail("receipt declares constitution unversioned — the ledger must version AUDIT_RULES.md")
    if not const_commit:
        fail("cannot resolve constitution commit in audit tree (HEAD unborn?) — fail closed")
    if r["constitution_hash"] != const_commit:
        fail(f"constitution commit {const_commit[:12]} != receipt {str(r['constitution_hash'])[:12]}")
    dcl_files = sorted((a.audit_root / "checks").glob("*.py"))
    dcl_digest = hashlib.sha256(b"".join(p.read_bytes() for p in dcl_files)).hexdigest()
    if dcl_digest != r["dcl_source_sha256"]:
        fail("DCL source hash mismatch — check layer changed since audit")
    if not a.receipt.parent.name.startswith(r["sha"]):
        fail(f"receipt lives in {a.receipt.parent.name}, not a cycle dir for {r['sha'][:12]}")
    report = a.receipt.parent / "report.md"
    if not report.is_file() or sha256_file(report) != r["report_sha256"]:
        fail("report blob hash mismatch or report missing")
    if r["verdict"] != "PASS":
        fail(f"verdict is {r['verdict']}, not PASS — nothing to admit")
    if r["audit_integrity"] != "OK":
        fail(f"audit integrity: {r['audit_integrity']} — escalation required")
    receipt_hash = hashlib.sha256(a.receipt.read_bytes()).hexdigest()
    if a.admit:
        sys.path.insert(0, str(Path(__file__).parent))
        import state  # noqa: PLC0415
        err = state.admit(r["cycle_id"], r["sha"], receipt_hash)
        if err:
            fail(f"controller: {err}")
    print(f"ADMIT: receipt {receipt_hash[:16]} verified"
          f"{' and consumed' if a.admit else ' (dry-run, not consumed)'}")


if __name__ == "__main__":
    main()
