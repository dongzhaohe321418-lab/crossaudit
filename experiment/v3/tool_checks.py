#!/usr/bin/env python3
"""Domain-tool channel for Part A: recompute, do not read.

Each check re-derives a quantity from a committed artefact and compares it with
what the increment reports.  That is the whole difference between this channel
and the script channel: the scripts ask whether a field is present and
well-formed, these ask whether the number is the number the evidence supports.

Fail-closed, as in Part C: a missing or unparseable artefact is a finding, not
a skip, and the runner exits non-zero if any check cannot run at all.

Usage: python3 tool_checks.py <corpus-dir> [--json out.json]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HARTREE_EV = 27.211386245988
STEP = re.compile(r"STEP\s+(\d+)\s+E=(-?\d+\.\d+)\s+dE=([\d.eE+-]+)")

def parse_log(p: Path):
    steps = [(int(m[1]), float(m[2]), float(m[3])) for m in (STEP.match(l) for l in p.read_text().splitlines()) if m]
    if not steps:
        raise ValueError("no SCF steps in log")
    return steps

def check_increment(d: Path):
    """Return (findings, ran) for one increment."""
    f = []
    try:
        res = json.loads((d / "results.json").read_text())
        log = parse_log(d / "scf.log")
        struct = json.loads((d / "structure.json").read_text())
    except Exception as e:
        return [{"check": "artefacts", "detail": f"cannot read the evidence: {e}"}], False

    q = {x["name"]: x for x in res.get("quantities", []) if isinstance(x, dict)}
    conv = res.get("convergence", {})

    # T1: reported total energy must match the log's final step
    if "total_energy" in q and q["total_energy"].get("unit") == "eV":
        want = log[-1][1] * HARTREE_EV
        got = q["total_energy"]["value"]
        if abs(got - want) > max(1e-3, abs(want) * 1e-5):
            f.append({"check": "energy_matches_log",
                      "detail": f"results.json reports {got} eV; the log's final step gives {want:.4f} eV"})

    # T2: a claim of convergence must be supported by the log's last step
    if conv.get("converged") is True:
        thr, last = conv.get("threshold"), log[-1][2]
        if thr is not None and last > thr:
            f.append({"check": "log_supports_convergence",
                      "detail": f"convergence claimed at threshold {thr:g}, but the log's last step is {last:.3e}"})

    # T3: the structure record and the reported distance must agree
    if "intermolecular_distance" in q and "pair_distance_angstrom" in struct:
        got, want = q["intermolecular_distance"]["value"], struct["pair_distance_angstrom"]
        if abs(got - want) > 0.01:
            f.append({"check": "distance_matches_structure",
                      "detail": f"results.json reports {got} A; structure.json records {want} A"})
    return f, True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus"); ap.add_argument("--json")
    a = ap.parse_args()
    incs = sorted(Path(a.corpus).glob("INC-*"))
    if not incs:
        sys.exit(f"no increments under {a.corpus}")
    out, unran = {}, 0
    for d in incs:
        f, ran = check_increment(d)
        if not ran: unran += 1
        out[d.name] = f
    flagged = {k: v for k, v in out.items() if v}
    summary = {"n_increments": len(incs), "n_flagged": len(flagged),
               "n_findings": sum(len(v) for v in out.values()),
               "n_unreadable": unran, "findings": out}
    if a.json: Path(a.json).write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "findings"}, indent=1))
    if unran:
        print(f"{unran} increment(s) could not be checked at all", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
