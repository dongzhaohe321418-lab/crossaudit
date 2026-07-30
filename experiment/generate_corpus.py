#!/usr/bin/env python3
"""Deterministic seeded-defect corpus generator (pilot). Seed fixed; no LLM involved.

Outputs:
  corpus/INC-###/{metadata.yml,results.json,SUMMARY.md}
  defect_key.json        (LOCAL ONLY until reveal — do not commit before both arms run)
  corpus/defect_key.sha256  (commit this: the seal)
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

SEED = 20260730
N_CLEAN, N_DEFECTIVE = 10, 20
ROOT = Path(__file__).parent
FUNCTIONALS = ["PBE0", "B3LYP", "PBE", "wB97X-D"]
BASES = ["def2-SVP", "def2-TZVP", "cc-pVDZ"]
SYSTEMS = ["water dimer", "ammonia dimer", "methane--water complex", "HF dimer",
           "formic acid dimer", "benzene--water complex"]

DCL_CLASSES = ["D1", "D2", "D3", "D4"]
LLM_CLASSES = ["L1", "L2", "L3", "L4", "L5", "L6"]


def base_increment(rng: random.Random, idx: int) -> dict:
    func, basis = rng.choice(FUNCTIONALS), rng.choice(BASES)
    system = rng.choice(SYSTEMS)
    be = round(-rng.uniform(2.5, 7.5), 2)
    dist = round(rng.uniform(2.6, 3.3), 2)
    thr = 1e-6
    ach = round(rng.uniform(0.05, 0.9) * thr, 10)
    script = f"run_{idx:03d}.py"
    return {
        "system": system, "func": func, "basis": basis, "be": be, "dist": dist,
        "thr": thr, "ach": ach, "script": script,
        "metadata": {
            "objective": f"Pilot increment: counterpoise-corrected binding energy of the {system} at {func}/{basis}. Synthetic corpus item.",
            "inputs": [f"geometries/{idx:03d}.xyz", f"scripts/{script}"],
            "method": {"functional": func, "basis_set": basis,
                       "corrections": ["counterpoise"], "thresholds": {"scf": thr}},
            "code_version": f"c{idx:03d}beef",
            "environment": "container:demo/psi4:1.9",
            "exclusions": [],
            "rerun": f"python {script}",
        },
        "results": {
            "quantities": [
                {"name": "binding_energy", "value": be, "unit": "kcal/mol",
                 "source": f"{script}@c{idx:03d}beef"},
                {"name": "intermolecular_distance", "value": dist, "unit": "angstrom",
                 "source": f"{script}@c{idx:03d}beef"},
            ],
            "convergence": {"converged": True, "threshold": thr, "achieved": ach,
                            "unit": "hartree"},
        },
        "summary": (f"We compute the counterpoise-corrected binding energy of the {system} "
                    f"at {func}/{basis}, obtaining {be} kcal/mol at an intermolecular "
                    f"distance of {dist} angstrom. SCF convergence reached "
                    f"{ach:.2e} Ha against a {thr:.0e} Ha threshold. All runs are "
                    f"reported; none were excluded."),
    }


def inject(rng: random.Random, inc: dict, cls: str) -> dict:
    m, r = inc["metadata"], inc["results"]
    if cls == "D1":
        r["quantities"][0].pop("source")
        return {"class": cls, "location": "results.json quantities[0].source",
                "description": "provenance removed from binding_energy"}
    if cls == "D2":
        r["quantities"][1]["unit"] = "kcal/mol"
        return {"class": cls, "location": "results.json quantities[1].unit",
                "description": "distance carries an energy unit"}
    if cls == "D3":
        r["convergence"]["achieved"] = r["convergence"]["threshold"] * 5
        return {"class": cls, "location": "results.json convergence",
                "description": "achieved exceeds threshold"}
    if cls == "D4":
        m.pop("code_version")
        return {"class": cls, "location": "metadata.yml code_version",
                "description": "required field removed"}
    if cls == "L1":
        wrong = rng.choice([f for f in FUNCTIONALS if f != m["method"]["functional"]])
        inc["summary"] = inc["summary"].replace(m["method"]["functional"], wrong, 1)
        return {"class": cls, "location": "SUMMARY vs metadata.method.functional",
                "description": f"summary claims {wrong}, metadata says {m['method']['functional']}"}
    if cls == "L2":
        inc["summary"] = inc["summary"].replace(
            "All runs are reported; none were excluded.",
            "Two outlier runs were dropped from the average as unstable.")
        return {"class": cls, "location": "SUMMARY vs metadata.exclusions",
                "description": "summary admits dropped runs; exclusions list empty"}
    if cls == "L3":
        other = rng.choice([b for b in BASES if b != m["method"]["basis_set"]])
        inc["summary"] += (f" This is {abs(round(rng.uniform(0.3, 1.4), 2))} kcal/mol stronger than our "
                           f"earlier {other} value, confirming the trend.")
        return {"class": cls, "location": "SUMMARY final sentence",
                "description": f"cross-basis comparison ({other} vs {m['method']['basis_set']}) stated without caveat"}
    if cls == "L4":
        r["quantities"][0]["source"] = f"legacy_fit.py@{rng.randrange(16**7):07x}"
        return {"class": cls, "location": "results.json quantities[0].source",
                "description": "source script not among declared inputs"}
    if cls == "L5":
        inc["summary"] = inc["summary"].replace(
            f"obtaining {inc['be']}", f"obtaining a repulsive {abs(inc['be'])}")
        return {"class": cls, "location": "SUMMARY vs results binding_energy sign",
                "description": "prose claims repulsive; JSON value is negative (attractive)"}
    if cls == "L6":
        r["convergence"]["converged"] = False
        inc["summary"] += " The binding energy is converged and final."
        return {"class": cls, "location": "SUMMARY vs convergence.converged",
                "description": "prose claims converged/final; convergence block says false"}
    raise ValueError(cls)


def yaml_dump(d: dict) -> str:  # minimal, dependency-free
    import io
    out = io.StringIO()

    def w(obj, ind=0):
        for k, v in obj.items():
            pad = "  " * ind
            if isinstance(v, dict):
                out.write(f"{pad}{k}:\n"); w(v, ind + 1)
            elif isinstance(v, list):
                out.write(f"{pad}{k}:{' []' if not v else ''}\n")
                for item in v:
                    out.write(f"{pad}  - {json.dumps(item) if not isinstance(item, str) else item}\n")
            else:
                out.write(f"{pad}{k}: {json.dumps(v) if not isinstance(v, (int, float)) or isinstance(v, bool) else v}\n")
    w(d)
    return out.getvalue()


def main() -> None:
    rng = random.Random(SEED)
    corpus = ROOT / "corpus"
    corpus.mkdir(exist_ok=True)
    key = {}
    plan = ["clean"] * N_CLEAN + ["defective"] * N_DEFECTIVE
    rng.shuffle(plan)
    for i, kind in enumerate(plan, 1):
        inc = base_increment(rng, i)
        defects = []
        if kind == "defective":
            n = rng.choice([1, 2, 3])
            classes = rng.sample(DCL_CLASSES, k=min(1, n)) if rng.random() < 0.45 else []
            classes += rng.sample(LLM_CLASSES, k=n - len(classes))
            if "D1" in classes and "L4" in classes:  # both target quantities[0].source
                classes.remove("L4")
                classes.append(rng.choice(
                    [c for c in LLM_CLASSES if c != "L4" and c not in classes]))
            for cls in classes:
                defects.append(inject(rng, inc, cls))
        d = corpus / f"INC-{i:03d}"
        d.mkdir(exist_ok=True)
        (d / "metadata.yml").write_text(yaml_dump(inc["metadata"]))
        (d / "results.json").write_text(json.dumps(inc["results"], indent=2) + "\n")
        (d / "SUMMARY.md").write_text(inc["summary"] + "\n")
        key[f"INC-{i:03d}"] = defects
    key_text = json.dumps(key, indent=2, sort_keys=True)
    (ROOT / "defect_key.json").write_text(key_text)
    seal = hashlib.sha256(key_text.encode()).hexdigest()
    (corpus / "defect_key.sha256").write_text(seal + "\n")
    n_def = sum(len(v) for v in key.values())
    print(f"corpus: {len(plan)} increments ({N_CLEAN} clean); defects: {n_def}; seal: {seal}")


if __name__ == "__main__":
    main()
