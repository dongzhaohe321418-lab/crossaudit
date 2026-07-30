#!/usr/bin/env python3
"""v2 scorer: per-defect single-finding binding (R2 §9 / audit §3.1).

A finding may credit AT MOST ONE defect, and must alone satisfy BOTH the rule-family
and the location tokens for that defect (no cross-finding assembly). Greedy one-to-one
matching, defects ordered by specificity. Clean-increment reporting separates
false-block VERDICT rate from blocker-finding counts, and reports advisory burden.

Corpus v2 key format: {inc: {"defects": [{id, class, rules, loc_tokens, severity_expected}],
                             "type": "clean"|"defective"|"l3_only"|"out_of_scope"}}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def finding_matches(f: dict, d: dict) -> bool:
    rule = str(f.get("rule", "")).lower()
    blob = json.dumps(f).lower()
    return (any(fam.lower() in rule for fam in d["rules"])
            and any(t.lower() in blob for t in d["loc_tokens"]))


def score(results_dir: Path, key: dict) -> dict:
    out = {"per_defect": [], "clean": {"n": 0, "false_block_verdicts": 0,
                                       "blocker_findings": 0, "advisory_findings": 0},
           "l3_only": {"n": 0, "wrongly_blocked": 0},
           "out_of_scope": {"n": 0, "wrongly_blocked": 0}}
    for inc, meta in sorted(key.items()):
        p = results_dir / f"{inc}.json"
        reply = json.loads(p.read_text())["reply"] if p.exists() else {"verdict": "MISSING", "findings": []}
        findings = list(reply.get("findings", []))
        verdict = reply.get("verdict")
        t = meta["type"]
        if t == "clean":
            c = out["clean"]; c["n"] += 1
            c["false_block_verdicts"] += verdict == "BLOCKED"
            c["blocker_findings"] += sum(1 for f in findings if f.get("severity") == "BLOCKER")
            c["advisory_findings"] += sum(1 for f in findings if f.get("severity") == "ADVISORY")
            continue
        if t in ("l3_only", "out_of_scope"):
            out[t]["n"] += 1
            out[t]["wrongly_blocked"] += verdict == "BLOCKED"
        used: set[int] = set()
        for d in sorted(meta.get("defects", []), key=lambda d: -len(d["loc_tokens"])):
            hit_idx = next((i for i, f in enumerate(findings)
                            if i not in used and finding_matches(f, d)), None)
            sev_ok = (hit_idx is not None and
                      findings[hit_idx].get("severity") == d.get("severity_expected",
                                                                 findings[hit_idx].get("severity")))
            if hit_idx is not None:
                used.add(hit_idx)
            out["per_defect"].append({"inc": inc, "id": d["id"], "class": d["class"],
                                      "caught": hit_idx is not None, "severity_ok": sev_ok})
    n = len(out["per_defect"])
    out["recall"] = f"{sum(1 for d in out['per_defect'] if d['caught'])}/{n}"
    return out


if __name__ == "__main__":
    results, keyfile = Path(sys.argv[1]), Path(sys.argv[2])
    print(json.dumps(score(results, json.loads(keyfile.read_text())), indent=2))
