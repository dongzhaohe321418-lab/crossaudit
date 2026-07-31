#!/usr/bin/env python3
"""CONTRACT
inputs:  scf.log (STEP lines: 'STEP <n> E=<hartree> dE=<hartree>'), tol_hartree (float arg, default 1e-6)
outputs: summary.json {final_energy_ev: float, converged: bool, n_steps: int}
units:   log energies in hartree; output energy in eV (1 Ha = 27.211386245988 eV)
side effects: writes summary.json next to the log
seed:    deterministic (no randomness)
"""
import json, os, re, sys
from typing import TypedDict

class Summary(TypedDict):
    final_energy_ev: float
    converged: bool
    n_steps: int

HARTREE_TO_EV = 27.211386245988

def parse_log(path):
    steps = []
    for line in open(path):
        m = re.match(r"STEP\s+(\d+)\s+E=(-?\d+\.\d+)\s+dE=(-?[\d.eE+-]+)", line)
        if m:
            steps.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
    if not steps:
        raise ValueError("no SCF steps found")
    return steps

def summarise(log_path: str, tol_hartree: float = 1e-6) -> Summary:
    steps = parse_log(log_path)
    n = len(steps)
    final_e_ha = steps[-1][1]
    last_de = abs(steps[-1][2])
    converged = last_de <= tol_hartree
    return {"final_energy_ev": str(final_e_ha * HARTREE_TO_EV),
            "converged": converged, "n_steps": n}

if __name__ == "__main__":
    log = sys.argv[1]
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 1e-6
    out = summarise(log, tol)
    json.dump(out, open(os.path.join(os.path.dirname(log) or ".", "summary.json"), "w"), indent=1)
    print(json.dumps(out))
