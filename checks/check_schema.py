"""Schema/self-description check (backs CA-DATA-001, CA-REPRO-001).

Verifies that an experiment increment is structurally self-describing:
metadata.yml and results.json exist, parse, and carry the required fields.
Pure structure — no scientific judgement lives here.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REQUIRED_METADATA = ("objective", "inputs", "method", "code_version", "environment")
REQUIRED_QUANTITY_FIELDS = ("name", "value", "unit", "source")


def _blocker(rule: str, message: str) -> dict:
    return {"severity": "BLOCKER", "rule": rule, "message": message}


def _advisory(rule: str, message: str) -> dict:
    return {"severity": "ADVISORY", "rule": rule, "message": message}


def run(experiment_dir: Path) -> list[dict]:
    findings: list[dict] = []
    meta_path = experiment_dir / "metadata.yml"
    results_path = experiment_dir / "results.json"

    meta = None
    if not meta_path.is_file():
        findings.append(_blocker("CA-REPRO-001", f"missing {meta_path.name}"))
    else:
        try:
            meta = yaml.safe_load(meta_path.read_text())
        except yaml.YAMLError as exc:
            findings.append(_blocker("CA-REPRO-001", f"metadata.yml does not parse: {exc}"))
    if isinstance(meta, dict):
        for field in REQUIRED_METADATA:
            if not meta.get(field):
                findings.append(_blocker(
                    "CA-REPRO-001", f"metadata.yml missing required field '{field}'"))
        if "rerun" not in meta:
            findings.append(_advisory("CA-REPRO-002", "no 'rerun' entry in metadata.yml"))

    results = None
    if not results_path.is_file():
        findings.append(_blocker("CA-DATA-001", f"missing {results_path.name}"))
    else:
        try:
            results = json.loads(results_path.read_text())
        except json.JSONDecodeError as exc:
            findings.append(_blocker("CA-DATA-001", f"results.json does not parse: {exc}"))
    if isinstance(results, dict):
        quantities = results.get("quantities")
        if not isinstance(quantities, list) or not quantities:
            findings.append(_blocker("CA-DATA-001", "results.json has no 'quantities' list"))
        else:
            for i, q in enumerate(quantities):
                for field in REQUIRED_QUANTITY_FIELDS:
                    if not isinstance(q, dict) or q.get(field) in (None, ""):
                        findings.append(_blocker(
                            "CA-DATA-001",
                            f"quantities[{i}] missing '{field}' (units+provenance are mandatory)"))
    return findings
