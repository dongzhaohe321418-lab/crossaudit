#!/usr/bin/env python3
"""Direct paired test of the two model arms. Computed post hoc; labelled as such.

The permutation floors in NULLCHECK.json calibrate each arm against its own
citation volume. They say nothing about the gap BETWEEN arms, and an earlier
draft of the paper said the lenient-tier comparison was "within noise" with no
statistic behind the phrase. The external review of 2026-08-05 called this out,
correctly. This script computes the statement's missing support, or its
refutation, from the committed outputs and the frozen scoring map.

Design: the 43 seeded defects are the pairing unit. For each defect and each
model arm, the frozen-map rule test (lenient) and the location-token test
(strict) give a caught/missed boolean, reproduced digit-for-digit from
score.py's logic; the script asserts the arm totals match the published
38/43, 41/43, 38, 37 before computing anything else, so it cannot silently
diverge from the scorecard. Then:

  * exact two-sided McNemar on the discordant pairs (b = GPT-only catches,
    c = Claude-only catches);
  * a 10,000-draw paired bootstrap over defects for a 95% CI on the recall
    difference.

Post hoc means post hoc: this was not pre-registered, the trial remains
exploratory, and the number's job is to stop a sentence from carrying a claim
no computation ever supported.

Usage: python3 arm_contrast.py   (writes results/ARM-CONTRAST.json)
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from score import FROZEN_MAP, LOC_TOKENS

ROOT = Path(__file__).parent
ARMS = ("anthropic-subagent", "openai")
PUBLISHED = {"anthropic-subagent": {"lenient": 38, "strict": 38},
             "openai": {"lenient": 41, "strict": 37}}


def per_defect(arm_dir: Path, key: dict) -> dict:
    outs = {json.loads(p.read_text())["increment"]: json.loads(p.read_text())
            for p in arm_dir.glob("INC-*.json")}
    vec = {}
    for inc, defects in sorted(key.items()):
        reply = outs.get(inc, {}).get("reply", {})
        findings = reply.get("findings", []) or []
        blob = json.dumps(findings).lower()
        for j, d in enumerate(defects or []):
            cls = d["class"]
            rule_hit = any(any(fam.lower() in str(f.get("rule", "")).lower()
                               for fam in FROZEN_MAP[cls]) for f in findings)
            loc_hit = rule_hit and any(t in blob for t in LOC_TOKENS[cls])
            vec[(inc, j, cls)] = {"lenient": rule_hit, "strict": loc_hit}
    return vec


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def main() -> None:
    key_text = (ROOT / "defect_key.json").read_text()
    seal = (ROOT / "corpus/defect_key.sha256").read_text().strip()
    assert hashlib.sha256(key_text.encode()).hexdigest() == seal, "SEAL MISMATCH — abort"
    key = json.loads(key_text)

    vecs = {arm: per_defect(ROOT / "results" / arm, key) for arm in ARMS}
    idx = sorted(vecs[ARMS[0]])
    assert idx == sorted(vecs[ARMS[1]]) and len(idx) == 43, "defect universes differ"

    report = {"pairing_unit": "seeded defect (n=43)", "map": "FROZEN",
              "provenance": "post hoc, 2026-08-05, in response to external review; "
                            "not pre-registered", "arms": {}, "tiers": {}}
    for arm in ARMS:
        got = {t: sum(vecs[arm][i][t] for i in idx) for t in ("lenient", "strict")}
        assert got == PUBLISHED[arm], f"{arm}: {got} != published {PUBLISHED[arm]}"
        report["arms"][arm] = got

    rng = random.Random(20260805)
    for tier in ("lenient", "strict"):
        a = [vecs["anthropic-subagent"][i][tier] for i in idx]
        o = [vecs["openai"][i][tier] for i in idx]
        b = sum(1 for x, y in zip(a, o) if y and not x)   # GPT only
        c = sum(1 for x, y in zip(a, o) if x and not y)   # Claude only
        diffs = []
        for _ in range(10_000):
            picks = [rng.randrange(43) for _ in range(43)]
            diffs.append(sum(o[k] for k in picks) - sum(a[k] for k in picks))
        diffs.sort()
        report["tiers"][tier] = {
            "difference_openai_minus_claude": sum(o) - sum(a),
            "both_caught": sum(1 for x, y in zip(a, o) if x and y),
            "both_missed": sum(1 for x, y in zip(a, o) if not x and not y),
            "gpt_only_b": b, "claude_only_c": c,
            "mcnemar_exact_p": round(mcnemar(b, c), 4),
            "bootstrap": {"draws": 10_000, "seed": 20260805,
                          "ci95_defects": [diffs[249], diffs[9749]],
                          "ci95_recall_points": [round(100 * diffs[249] / 43, 1),
                                                 round(100 * diffs[9749] / 43, 1)]},
        }
    out = ROOT / "results" / "ARM-CONTRAST.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
