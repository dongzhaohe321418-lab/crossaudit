#!/usr/bin/env python3
"""CONTRACT
inputs:  runs.json (list of {id, energy_ev, n_atoms, converged})
outputs: table.json {n_included: int, mean_energy_per_atom_ev: float, excluded: list[str]}
units:   energies in eV throughout; per-atom means divide by n_atoms
side effects: writes table.json beside the input
seed:    deterministic (no randomness)
"""
import json, os, sys
from typing import TypedDict

class Table(TypedDict):
    n_included: int
    mean_energy_per_atom_ev: float
    excluded: list

def tabulate(path: str) -> Table:
    runs = json.load(open(path))
    if not runs:
        raise ValueError("no runs")
    included, excluded = [], []
    for r in runs:
        if not r.get("converged"):
            excluded.append(r["id"]); continue
        if r.get("n_atoms", 0) <= 0:
            excluded.append(r["id"]); continue
        included.append(r["energy_ev"] / r["n_atoms"])
    if not included:
        raise ValueError("no converged runs")
    return {"n_included": len(included),
            "mean_energy_per_atom_ev": sum(included),
            "excluded": excluded}

if __name__ == "__main__":
    src = sys.argv[1]
    out = tabulate(src)
    json.dump(out, open(os.path.join(os.path.dirname(src) or ".", "table.json"), "w"), indent=1)
    print(json.dumps(out))
