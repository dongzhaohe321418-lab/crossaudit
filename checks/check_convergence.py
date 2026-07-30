"""Convergence assertion (backs CA-METH-002).

Mechanisable half of the convergence rule: the flag, the threshold, and the
achieved value must be present, and achieved must actually beat the threshold.
Whether the *threshold itself* is appropriate is judgement — that half lives
in the Constitution (CA-METH-003, ADVISORY), not here.
"""
from __future__ import annotations

import json
from pathlib import Path


def _blocker(message: str) -> dict:
    return {"severity": "BLOCKER", "rule": "CA-METH-002", "message": message}


def run(experiment_dir: Path) -> list[dict]:
    results_path = experiment_dir / "results.json"
    if not results_path.is_file():
        return []
    try:
        results = json.loads(results_path.read_text())
    except json.JSONDecodeError:
        return []

    conv = results.get("convergence")
    if conv is None:
        return [_blocker("results.json has no 'convergence' block")]
    if not isinstance(conv, dict):
        return [_blocker("'convergence' must be an object")]

    findings: list[dict] = []
    if conv.get("converged") is not True:
        findings.append(_blocker("convergence.converged is not true — unconverged "
                                 "numbers are not results"))
    threshold, achieved = conv.get("threshold"), conv.get("achieved")
    if threshold is None or achieved is None:
        findings.append(_blocker("convergence must state both 'threshold' and 'achieved'"))
    else:
        try:
            if abs(float(achieved)) > abs(float(threshold)):
                findings.append(_blocker(
                    f"achieved ({achieved}) does not meet threshold ({threshold})"))
        except (TypeError, ValueError):
            findings.append(_blocker("convergence threshold/achieved are not numeric"))
    return findings
