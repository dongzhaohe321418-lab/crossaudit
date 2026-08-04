#!/usr/bin/env python3
"""Put the two vendors' clean-set rates beside each other and say what follows.

AMENDMENT 3 registers this as a limitation to report rather than a threshold to
pass. So this script never exits non-zero on a number. It states both rates with
exact intervals, says whether they are distinguishable, and writes the sentence
the paper owes its reader either way -- before the arms run, so that neither
outcome can be chosen after the fact.

The comparison is Fisher's exact test on the 2x2 of (entry filed, no entry) by
vendor. Two twenty-increment samples cannot resolve a small difference, and the
report says so rather than reading a large p as agreement.

Usage:
  python3 preflight_report.py --anthropic a.json --openai o.json \
      --corpus-check c.json --seed 20260804 --models <id-a> <id-o> --out PREFLIGHT.json
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

from score_v3 import clopper


def load(p: str) -> dict | None:
    """validate_clean prints JSON then a note on stderr; tolerate a missing run."""
    try:
        text = Path(p).read_text()
    except OSError:
        return None
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(text[i:j + 1])
    except json.JSONDecodeError:
        return None


def arm(d: dict | None) -> dict | None:
    if not d:
        return None
    n = d.get("clean_increments_sampled") or 0
    blocked = sum(1 for v in (d.get("detail") or {}).values() if v)
    lo, hi = clopper(blocked, n) if n else (None, None)
    return {"clean_increments": n, "increments_with_an_entry": blocked,
            "rate": round(blocked / n, 4) if n else None, "ci95": [lo, hi],
            "findings": d.get("findings"),
            "withdrawn_by_author": d.get("withdrawn_by_author"),
            "referred_to_tools": d.get("referred_to_tools")}


def fisher(a1, n1, a2, n2) -> float:
    """Two-sided Fisher exact on [[a1, n1-a1], [a2, n2-a2]]."""
    b1, b2 = n1 - a1, n2 - a2
    tot, row1, col1 = n1 + n2, n1, a1 + a2
    def p(k):
        return (math.comb(row1, k) * math.comb(tot - row1, col1 - k)) / math.comb(tot, col1)
    obs = p(a1)
    lo = max(0, col1 - (tot - row1))
    hi = min(row1, col1)
    return round(min(1.0, sum(p(k) for k in range(lo, hi + 1) if p(k) <= obs * (1 + 1e-9))), 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anthropic", required=True)
    ap.add_argument("--openai", required=True)
    ap.add_argument("--corpus-check")
    ap.add_argument("--seed")
    ap.add_argument("--models", nargs=2, default=["", ""])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    arms = {"anthropic": arm(load(a.anthropic)), "openai": arm(load(a.openai))}
    check = load(a.corpus_check) if a.corpus_check else None

    verdict, p = None, None
    A, O = arms["anthropic"], arms["openai"]
    if A and O and A["clean_increments"] and O["clean_increments"]:
        p = fisher(A["increments_with_an_entry"], A["clean_increments"],
                   O["increments_with_an_entry"], O["clean_increments"])
        overlap = not (A["ci95"][1] < O["ci95"][0] or O["ci95"][1] < A["ci95"][0])
        if p < 0.05:
            verdict = ("The two vendors file entries against clean material at different rates. "
                       "L5's false-block rate therefore carries a component that is not audit "
                       "quality, and the arm results must report this preflight beside them and "
                       "decline any cross-vendor false-block comparison that does not account "
                       "for it.")
        elif overlap:
            verdict = ("The rates are not distinguishable at this sample size, which is not the "
                       "same as equal: twenty increments per vendor cannot resolve a difference "
                       "smaller than roughly twenty points. The comparison proceeds, and the "
                       "paper states the resolution rather than implying agreement.")
        else:
            verdict = ("Intervals are disjoint but the exact test is not significant; treat as "
                       "unresolved and report both.")
    else:
        verdict = ("One vendor did not produce a usable result. The preflight is incomplete, and "
                   "AMENDMENT 3's confound stands unmeasured; say so wherever L5 is reported.")

    report = {"registered_under": "AMENDMENT 3 (2026-08-04)",
              "purpose": "per-vendor rate of entries filed against increments with nothing wrong",
              "not_a_gate": "This is reported, never passed or failed. See AMENDMENT 3.",
              "calibration_seed": a.seed,
              "models": {"anthropic": a.models[0], "openai": a.models[1]},
              "corpus_self_check": (check or {}).get("increments_with_problems"),
              "corpus_sha256": (check or {}).get("corpus_sha256"),
              "arms": arms, "fisher_exact_p": p, "reading": verdict}
    Path(a.out).write_text(json.dumps(report, indent=1) + "\n")

    print("## v3 preflight\n")
    for name, r in arms.items():
        if not r:
            print(f"- **{name}**: no usable result"); continue
        lo, hi = r["ci95"]
        print(f"- **{name}** (`{report['models'][name]}`): "
              f"{r['increments_with_an_entry']}/{r['clean_increments']} increments drew an entry "
              f"= {r['rate']:.1%}, CI95 [{lo:.1%}, {hi:.1%}]; "
              f"{r['withdrawn_by_author']} withdrawn, {r['referred_to_tools']} referred to tools")
    if p is not None:
        print(f"\nFisher exact p = {p}")
    print(f"\n{verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
