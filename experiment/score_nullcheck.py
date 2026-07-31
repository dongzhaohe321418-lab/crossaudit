#!/usr/bin/env python3
"""Permutation null check for the seeded-defect pilot: chance floors for §4.3.

Why this exists
---------------
Recall under the frozen scorer rises with finding volume: an arm that emits many
findings citing many rule families collects credit for defects it never localised.
The floor answers "what would this arm have scored on a corpus whose defects were
assigned at random?" — that is, from output volume and citation habits alone.

Null model
----------
Each arm's raw outputs stay exactly where they are, so volume and citation habits
are preserved by construction. What is shuffled is the increment-to-defect map:
the thirty defect lists of the key (twenty non-empty, ten empty) are dealt back to
the thirty increments under a random permutation, and scoring then proceeds
exactly as `score.py` does. Recall is counted over the same 43 defects every time,
so observed and floor are on one scale.

Reported statistics per arm and tier: the floor (mean recall over the shuffles),
its standard deviation, the 95th percentile, a one-sided permutation p-value
(fraction of shuffles reaching the observed score), and the chance-corrected
agreement (observed - floor) / (43 - floor).

Reproduce
---------
    python3 experiment/score_nullcheck.py            # 2000 shuffles, seed 20260731
    python3 experiment/score_nullcheck.py --shuffles 10000 --seed 1

Writes experiment/results/NULLCHECK.json. Deterministic given (shuffles, seed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path

from score import FROZEN_MAP, LOC_TOKENS, RULE_MAP

ROOT = Path(__file__).parent
N_DEFECTS = 43


def load_key() -> dict:
    """Load the defect key, verifying the committed hash first (as score.py does)."""
    key_text = (ROOT / "defect_key.json").read_text()
    seal = (ROOT / "corpus/defect_key.sha256").read_text().strip()
    assert hashlib.sha256(key_text.encode()).hexdigest() == seal, "SEAL MISMATCH — abort"
    return json.loads(key_text)


def load_arms() -> dict[str, dict]:
    """arm name -> {increment: findings-blob}, precomputed once per arm."""
    arms = {}
    for arm_dir in sorted((ROOT / "results").iterdir()):
        if not arm_dir.is_dir():
            continue
        per_inc = {}
        for p in arm_dir.glob("INC-*.json"):
            reply = json.loads(p.read_text()).get("reply", {}) or {}
            findings = reply.get("findings", []) or []
            rules = [str(f.get("rule", "")).lower() for f in findings]
            per_inc[json.loads(p.read_text())["increment"]] = {
                "rules": rules,
                "blob": json.dumps(findings).lower(),
                "n": len(findings),
            }
        if per_inc:
            arms[arm_dir.name] = per_inc
    return arms


def score(assignment: dict[str, list], per_inc: dict, mapping: dict) -> tuple[int, int]:
    """Lenient and strict catches under one increment-to-defect assignment.

    Identical rule to score.py: lenient = some finding on that increment cites a
    rule family the class maps to; strict = lenient and the increment's findings
    mention one of the class's location tokens.
    """
    lenient = strict = 0
    for inc, defects in assignment.items():
        out = per_inc.get(inc)
        if not out or not defects:
            continue
        for d in defects:
            cls = d["class"]
            rule_hit = any(fam.lower() in r for r in out["rules"] for fam in mapping[cls])
            lenient += rule_hit
            strict += rule_hit and any(t in out["blob"] for t in LOC_TOKENS[cls])
    return lenient, strict


def run(shuffles: int, seed: int) -> dict:
    key = load_key()
    arms = load_arms()
    incs = list(key.keys())
    lists = [key[i] for i in incs]
    assert sum(len(v) for v in lists) == N_DEFECTS, "defect count drifted from 43"

    out: dict = {
        "null_model": ("increment-to-defect map shuffled; each arm's outputs, "
                       "output volume and rule-citation habits held fixed"),
        "shuffles": shuffles,
        "seed": seed,
        "n_defects": N_DEFECTS,
        "n_increments": len(incs),
        "arms": {},
    }
    for map_name, mapping in (("frozen", FROZEN_MAP), ("adjudicated", RULE_MAP)):
        for arm, per_inc in arms.items():
            observed = score(dict(zip(incs, lists)), per_inc, mapping)
            rng = random.Random(seed)
            draws = {"lenient": [], "strict": []}
            for _ in range(shuffles):
                shuffled = lists[:]
                rng.shuffle(shuffled)
                lo, st = score(dict(zip(incs, shuffled)), per_inc, mapping)
                draws["lenient"].append(lo)
                draws["strict"].append(st)
            entry = {"n_findings": sum(o["n"] for o in per_inc.values())}
            for tier, obs in (("lenient", observed[0]), ("strict", observed[1])):
                d = sorted(draws[tier])
                floor = statistics.fmean(d)
                entry[tier] = {
                    "observed": obs,
                    "floor": round(floor, 1),
                    "sd": round(statistics.pstdev(d), 1),
                    "p95": d[int(0.95 * (len(d) - 1))],
                    "p_value": round(sum(1 for x in d if x >= obs) / len(d), 4),
                    "chance_corrected": round((obs - floor) / (N_DEFECTS - floor), 2),
                }
            out["arms"].setdefault(map_name, {})[arm] = entry
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shuffles", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260731)
    ap.add_argument("--out", default=str(ROOT / "results/NULLCHECK.json"))
    a = ap.parse_args()

    res = run(a.shuffles, a.seed)
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    for map_name, arms in res["arms"].items():
        print(f"--- {map_name} scoring map ---")
        for arm, e in arms.items():
            for tier in ("lenient", "strict"):
                t = e[tier]
                print(f"{arm:20s} {tier:8s} n_findings={e['n_findings']:4d} "
                      f"observed={t['observed']:2d}/43  floor={t['floor']:5.1f} "
                      f"(sd {t['sd']:.1f}, p95 {t['p95']})  p={t['p_value']:.4f}  "
                      f"chance-corrected={t['chance_corrected']:.2f}")


if __name__ == "__main__":
    main()
