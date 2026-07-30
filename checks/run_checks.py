#!/usr/bin/env python3
"""CrossAudit deterministic check runner (reference implementation).

Contract (invariant I4):
  - runs BEFORE any LLM audit;
  - exit code != 0  <=>  at least one hard failure  <=>  verdict BLOCKED,
    non-overridable by any model;
  - machine-readable output written to checks.json.

Usage:
    python checks/run_checks.py <experiment_dir> [<experiment_dir> ...]
    python checks/run_checks.py --science-root <repo_root> --changed <path> ...

Dependencies: Python 3.9+ stdlib + PyYAML.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import check_convergence
import check_schema
import check_units

CHECKS = (
    ("schema", check_schema.run),
    ("units", check_units.run),
    ("convergence", check_convergence.run),
)


def experiment_dirs_from_changed(science_root: Path, changed: list[str]) -> list[Path]:
    """Map changed file paths to experiment directories (experiments/<name>/)."""
    dirs = set()
    for rel in changed:
        parts = Path(rel).parts
        if len(parts) >= 2 and parts[0] == "experiments":
            dirs.add(science_root / parts[0] / parts[1])
    return sorted(dirs)


def run_all(experiment_dir: Path) -> dict:
    findings = []
    for name, fn in CHECKS:
        try:
            findings.extend(dict(f, check=name) for f in fn(experiment_dir))
        except Exception as exc:  # a crashing check is itself a hard failure
            findings.append({
                "check": name,
                "severity": "BLOCKER",
                "rule": "DCL-CRASH",
                "message": f"check '{name}' crashed: {exc!r} (CA-META-001: missing evidence is a finding)",
            })
    return {
        "experiment": str(experiment_dir),
        "findings": findings,
        "hard_failures": sum(1 for f in findings if f["severity"] == "BLOCKER"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dirs", nargs="*", help="experiment directories to check")
    ap.add_argument("--science-root", type=Path, default=None)
    ap.add_argument("--changed", nargs="*", default=[],
                    help="changed paths relative to science root")
    ap.add_argument("--output", type=Path, default=Path("checks.json"))
    args = ap.parse_args()

    targets = [Path(d) for d in args.dirs]
    if args.science_root and args.changed:
        targets += experiment_dirs_from_changed(args.science_root, args.changed)
    if not targets:
        print("no experiment directories to check", file=sys.stderr)
        return 2

    results = [run_all(d) for d in sorted(set(targets))]
    total_hard = sum(r["hard_failures"] for r in results)
    payload = {
        "crossaudit_dcl_version": 1,
        "verdict": "BLOCKED" if total_hard else "PASS",
        "total_hard_failures": total_hard,
        "results": results,
    }
    args.output.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    return 1 if total_hard else 0


if __name__ == "__main__":
    sys.exit(main())
