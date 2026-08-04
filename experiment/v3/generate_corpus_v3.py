#!/usr/bin/env python3
"""Corpus generator for the v3 ablation. Deterministic; no model is called.

Differences from the v1 generator, each required by the registration:

* **Channel tags.** Every defect carries the cheapest channel expected to catch
  it -- ``script``, ``tool`` or ``model`` -- so Part A's channel decomposition
  has a denominator per channel rather than one lump.
* **Tool-verifiable artefacts.** Increments ship a parseable SCF log and a
  structure record, so the domain-tool arm has something to recompute against.
  Without them the tool channel cannot exist and its contribution cannot be
  separated from the model's.
* **Transcript slots.** Each increment gets an empty ``transcript.md`` for the
  L1/L2 ladder rungs. The generating model writes it later, blind to the key;
  the generator only reserves the slot so the corpus layout is fixed before any
  model runs.
* **Provenance of the clean set.** ``--authored-by`` records which vendor's
  model wrote the clean increments this corpus mutates, so the per-vendor
  corpora the registration asks for are distinguishable after the fact.

Sealing.  The key is written outside the corpus tree and its SHA-256 beside the
corpus.  ``seal_key.py`` is the only supported way to place the key with its
escrow; this script refuses to write the key into the repository.

Usage:
  python3 generate_corpus_v3.py --out corpus3 --key /secure/path/key.json \
      --seed 20260805 --n-clean 20 --n-defective 40 --authored-by deterministic
"""
from __future__ import annotations

import argparse, hashlib, json, random, sys
from pathlib import Path

FUNCTIONALS = ["PBE0", "B3LYP", "PBE", "wB97X-D", "M06-2X"]
BASES = ["def2-SVP", "def2-TZVP", "cc-pVDZ", "aug-cc-pVTZ"]
SYSTEMS = ["water dimer", "ammonia dimer", "methane--water complex", "HF dimer",
           "formic acid dimer", "benzene--water complex", "methanol dimer"]
HARTREE_EV = 27.211386245988

# class -> (cheapest expected channel, one-line rationale kept with the key)
CHANNELS = {
    "D1": ("script", "a required provenance field is absent"),
    "D2": ("script", "a length carries an energy unit"),
    "D3": ("script", "achieved convergence exceeds its own threshold"),
    "D4": ("script", "a required metadata field is absent"),
    "T1": ("tool", "the SCF log's final energy disagrees with the reported value"),
    "T2": ("tool", "the log's last step is not below the stated threshold"),
    "T3": ("tool", "the structure record's distance disagrees with the reported one"),
    "L1": ("model", "prose names a different functional than the metadata"),
    "L2": ("model", "prose admits exclusions the metadata denies"),
    "L3": ("model", "an unlike-for-unlike comparison is stated without caveat"),
    "L4": ("model", "the cited source script is not a declared input"),
    "L5": ("model", "prose reverses the sign's physical meaning"),
    "L6": ("model", "prose claims convergence the record denies"),
}
SCRIPT_C, TOOL_C, MODEL_C = ([k for k, v in CHANNELS.items() if v[0] == c]
                             for c in ("script", "tool", "model"))
# pairs that would overwrite each other's evidence
# Pairs that would overwrite or mask each other's evidence. T2 and L6 both touch
# the convergence record: L6 sets converged=False, which suppresses the very claim
# T2 contradicts, so a tool check keyed on "claims convergence" can never fire.
# Found by validating the tool channel against the key before sealing, which is
# what that validation is for.
EXCLUSIVE = [{"D1", "L4"}, {"D3", "T2"}, {"D3", "L6"}, {"T1", "L5"}, {"T2", "L6"}]


def base_increment(rng, idx):
    func, basis, system = rng.choice(FUNCTIONALS), rng.choice(BASES), rng.choice(SYSTEMS)
    be = round(-rng.uniform(2.5, 7.5), 2)
    dist = round(rng.uniform(2.6, 3.3), 2)
    thr = 1e-6
    ach = round(rng.uniform(0.05, 0.9) * thr, 12)
    e_final_ha = round(-rng.uniform(76.0, 232.0), 6)
    script = f"run_{idx:03d}.py"
    steps = []
    e = e_final_ha - rng.uniform(0.02, 0.2)
    for k in range(1, rng.randrange(5, 9)):
        de = (e_final_ha - e) * rng.uniform(0.45, 0.8)
        e += de
        steps.append((k, round(e, 8), abs(round(de, 10))))
    steps.append((len(steps) + 1, e_final_ha, ach))
    return {
        "idx": idx, "system": system, "func": func, "basis": basis, "be": be,
        "dist": dist, "thr": thr, "ach": ach, "script": script,
        "e_final_ha": e_final_ha, "steps": steps,
        "metadata": {
            "objective": f"Counterpoise-corrected binding energy of the {system} at {func}/{basis}. Synthetic corpus item.",
            "inputs": [f"geometries/{idx:03d}.xyz", f"scripts/{script}", "logs/scf.log"],
            "method": {"functional": func, "basis_set": basis,
                       "corrections": ["counterpoise"], "thresholds": {"scf": thr}},
            "code_version": f"c{idx:03d}beef", "environment": "container:demo/psi4:1.9",
            "exclusions": [], "rerun": f"python {script}",
        },
        "results": {
            "quantities": [
                {"name": "binding_energy", "value": be, "unit": "kcal/mol",
                 "source": f"{script}@c{idx:03d}beef"},
                {"name": "intermolecular_distance", "value": dist, "unit": "angstrom",
                 "source": f"{script}@c{idx:03d}beef"},
                {"name": "total_energy", "value": round(e_final_ha * HARTREE_EV, 4),
                 "unit": "eV", "source": "logs/scf.log"},
            ],
            "convergence": {"converged": True, "threshold": thr, "achieved": ach,
                            "unit": "hartree"},
        },
        "structure": {"pair_distance_angstrom": dist, "n_atoms": rng.randrange(6, 24)},
        "summary": (f"We compute the counterpoise-corrected binding energy of the {system} "
                    f"at {func}/{basis}, obtaining {be} kcal/mol at an intermolecular "
                    f"distance of {dist} angstrom. SCF convergence reached {ach:.2e} Ha "
                    f"against a {thr:.0e} Ha threshold. All runs are reported; none were excluded."),
    }


def inject(rng, inc, cls):
    m, r = inc["metadata"], inc["results"]
    if cls == "D1":
        r["quantities"][0].pop("source", None)
        loc, desc = "results.json quantities[0].source", "provenance removed from binding_energy"
    elif cls == "D2":
        r["quantities"][1]["unit"] = "kcal/mol"
        loc, desc = "results.json quantities[1].unit", "distance carries an energy unit"
    elif cls == "D3":
        r["convergence"]["achieved"] = r["convergence"]["threshold"] * 5
        loc, desc = "results.json convergence", "achieved exceeds threshold"
    elif cls == "D4":
        m.pop("code_version", None)
        loc, desc = "metadata.yml code_version", "required field removed"
    elif cls == "T1":
        r["quantities"][2]["value"] = round(r["quantities"][2]["value"] * 1.004, 4)
        loc = "results.json quantities[2].value vs logs/scf.log"
        desc = "reported total energy does not match the log's final step"
    elif cls == "T2":
        s = inc["steps"]
        s[-1] = (s[-1][0], s[-1][1], inc["thr"] * 8)
        loc, desc = "logs/scf.log final dE vs convergence.threshold", "log's last step is above the stated threshold while the record claims convergence"
    elif cls == "T3":
        inc["structure"]["pair_distance_angstrom"] = round(inc["dist"] + rng.uniform(0.15, 0.4), 2)
        loc, desc = "structure.json vs results quantities[1]", "structure record and reported distance disagree"
    elif cls == "L1":
        wrong = rng.choice([f for f in FUNCTIONALS if f != m["method"]["functional"]])
        inc["summary"] = inc["summary"].replace(m["method"]["functional"], wrong, 1)
        loc, desc = "SUMMARY vs metadata.method.functional", f"summary claims {wrong}"
    elif cls == "L2":
        inc["summary"] = inc["summary"].replace(
            "All runs are reported; none were excluded.",
            "Two outlier runs were dropped from the average as unstable.")
        loc, desc = "SUMMARY vs metadata.exclusions", "summary admits dropped runs; exclusions empty"
    elif cls == "L3":
        other = rng.choice([b for b in BASES if b != m["method"]["basis_set"]])
        inc["summary"] += (f" This is {abs(round(rng.uniform(0.3,1.4),2))} kcal/mol stronger than our "
                           f"earlier {other} value, confirming the trend.")
        loc, desc = "SUMMARY final sentence", f"cross-basis comparison ({other}) without caveat"
    elif cls == "L4":
        r["quantities"][0]["source"] = f"legacy_fit.py@{rng.randrange(16**7):07x}"
        loc, desc = "results.json quantities[0].source", "source script not among declared inputs"
    elif cls == "L5":
        inc["summary"] = inc["summary"].replace(f"obtaining {inc['be']}",
                                                f"obtaining a repulsive {abs(inc['be'])}")
        loc, desc = "SUMMARY vs binding_energy sign", "prose claims repulsive; value is attractive"
    elif cls == "L6":
        r["convergence"]["converged"] = False
        inc["summary"] += " The binding energy is converged and final."
        loc, desc = "SUMMARY vs convergence.converged", "prose claims converged; record says false"
    else:
        raise ValueError(cls)
    return {"class": cls, "channel": CHANNELS[cls][0], "location": loc,
            "description": desc, "rationale": CHANNELS[cls][1]}


def yaml_dump(d, ind=0):
    out = []
    pad = "  " * ind
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(f"{pad}{k}:"); out.append(yaml_dump(v, ind + 1))
        elif isinstance(v, list):
            out.append(f"{pad}{k}:")
            for it in v:
                out.append(f"{pad}  - {json.dumps(it) if isinstance(it,(dict,list)) else it}")
        else:
            out.append(f"{pad}{k}: {json.dumps(v) if isinstance(v,str) else v}")
    return "\n".join(x for x in out if x)


def scf_log(inc):
    lines = [f"# SCF log for {inc['script']} ({inc['func']}/{inc['basis']})"]
    for k, e, de in inc["steps"]:
        lines.append(f"STEP {k} E={e:.8f} dE={de:.3e}")
    lines.append(f"# final energy {inc['e_final_ha']:.6f} hartree")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--key", required=True, help="path OUTSIDE the repository")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n-clean", type=int, default=20)
    ap.add_argument("--n-defective", type=int, default=40)
    ap.add_argument("--authored-by", default="deterministic",
                    help="which vendor's model wrote the clean increments this mutates")
    a = ap.parse_args()

    keyp = Path(a.key).resolve()
    repo = Path(__file__).resolve().parents[2]
    if repo in keyp.parents:
        sys.exit(f"refusing to write the defect key inside the repository ({keyp}). "
                 "Give --key a path outside it; seal_key.py places it with the escrow.")

    rng = random.Random(a.seed)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    key = {}
    n = a.n_clean + a.n_defective
    for i in range(1, n + 1):
        inc = base_increment(rng, i)
        defects = []
        if i > a.n_clean:
            k = rng.choice([1, 1, 2, 2, 3])
            pool = (rng.sample(SCRIPT_C, k=min(len(SCRIPT_C), k)) if rng.random() < 0.35 else [])
            pool += rng.sample(TOOL_C, k=1) if rng.random() < 0.45 else []
            pool += rng.sample(MODEL_C, k=max(0, k - len(pool)))
            chosen = []
            for c in pool:
                if any({c, d} in EXCLUSIVE for d in chosen):
                    continue
                chosen.append(c)
            for c in chosen:
                defects.append(inject(rng, inc, c))
        d = out / f"INC-{i:03d}"; d.mkdir(exist_ok=True)
        (d / "metadata.yml").write_text(yaml_dump(inc["metadata"]) + "\n")
        (d / "results.json").write_text(json.dumps(inc["results"], indent=1) + "\n")
        (d / "structure.json").write_text(json.dumps(inc["structure"], indent=1) + "\n")
        (d / "scf.log").write_text(scf_log(inc))
        (d / "SUMMARY.md").write_text(f"# {inc['system']}\n\n{inc['summary']}\n")
        (d / "transcript.md").write_text(
            "<!-- Reserved for the L1/L2 ladder rungs. The generating model writes its\n"
            "     rationale here, blind to the defect key. Empty in the corpus as sealed. -->\n")
        if defects:
            key[f"INC-{i:03d}"] = defects

    ndef = sum(len(v) for v in key.values())
    meta = {"seed": a.seed, "n_increments": n, "n_clean": a.n_clean,
            "n_defective": a.n_defective, "n_defects": ndef,
            "authored_by": a.authored_by,
            "channel_counts": {c: sum(1 for v in key.values() for d in v if d["channel"] == c)
                               for c in ("script", "tool", "model")},
            "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    keyp.parent.mkdir(parents=True, exist_ok=True)
    keyp.write_text(json.dumps({"meta": meta, "key": key}, indent=1) + "\n")
    digest = hashlib.sha256(keyp.read_bytes()).hexdigest()
    (out / "CORPUS.json").write_text(json.dumps(
        {**meta, "defect_key_sha256": digest, "key_path_note": "held outside the repository"},
        indent=1) + "\n")
    print(json.dumps({**meta, "defect_key_sha256": digest, "key_written_to": str(keyp)}, indent=1))


if __name__ == "__main__":
    main()
