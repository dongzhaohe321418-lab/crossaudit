#!/usr/bin/env python3
"""Score both arms against the revealed defect key. Run only after both arms' raw
outputs are committed and defect_key.json is revealed (seal must verify)."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent

# Which rule families count as catching which defect class (lenient tier).
RULE_MAP = {
    "D1": ("CA-DATA-001",), "D2": ("CA-DATA-001", "CA-DOM"), "D3": ("CA-METH-002",),
    "D4": ("CA-REPRO-001",),
    "L1": ("CA-DATA-002",), "L2": ("CA-DATA-002", "CA-DATA-003"), "L3": ("CA-DOM", "CA-DATA-002"),
    "L4": ("CA-DATA-001", "CA-DATA-002"), "L5": ("CA-DATA-002",), "L6": ("CA-METH-002", "CA-DATA-002"),
}
LOC_TOKENS = {  # strict tier: finding must also mention one of these tokens
    "D1": ("source", "provenance", "binding_energy"), "D2": ("unit", "distance"),
    "D3": ("converg", "threshold"), "D4": ("code_version",),
    "L1": ("functional", "method"), "L2": ("exclu", "dropped"),
    "L3": ("basis", "level", "compar"), "L4": ("source", "input", "legacy"),
    "L5": ("sign", "repulsive", "attractive", "contradict"), "L6": ("converg",),
}


def main() -> None:
    key_text = (ROOT / "defect_key.json").read_text()
    seal = (ROOT / "corpus/defect_key.sha256").read_text().strip()
    assert hashlib.sha256(key_text.encode()).hexdigest() == seal, "SEAL MISMATCH — abort"
    key = json.loads(key_text)

    lines = ["# Seeded-Defect Pilot — Scorecard", "",
             f"Seal verified: `{seal[:16]}…`", ""]
    for arm_dir in sorted((ROOT / "results").iterdir()):
        if not arm_dir.is_dir():
            continue
        outs = {json.loads(p.read_text())["increment"]: json.loads(p.read_text())
                for p in arm_dir.glob("INC-*.json")}
        model = next(iter(outs.values()))["model"] if outs else "?"
        caught_l, caught_s, per_class = 0, 0, defaultdict(lambda: [0, 0, 0])
        total = 0
        fp = 0
        verdict_ok = 0
        for inc, defects in key.items():
            reply = outs.get(inc, {}).get("reply", {})
            findings = reply.get("findings", []) or []
            blob = json.dumps(findings).lower()
            if not defects:
                fp += sum(1 for f in findings if f.get("severity") == "BLOCKER")
                verdict_ok += reply.get("verdict") == "PASS"
                continue
            has_blocker_defect = True  # all seeded classes map to BLOCKER-family rules
            verdict_ok += (reply.get("verdict") == "BLOCKED") == has_blocker_defect
            for d in defects:
                total += 1
                cls = d["class"]
                per_class[cls][2] += 1
                rule_hit = any(any(fam.lower() in str(f.get("rule", "")).lower()
                                   for fam in RULE_MAP[cls]) for f in findings)
                loc_hit = rule_hit and any(t in blob for t in LOC_TOKENS[cls])
                caught_l += rule_hit
                caught_s += loc_hit
                per_class[cls][0] += rule_hit
                per_class[cls][1] += loc_hit
        lines += [f"## Arm `{arm_dir.name}` — model `{model}`", "",
                  f"- Lenient recall: **{caught_l}/{total}**; strict: **{caught_s}/{total}**",
                  f"- False-positive BLOCKERs on clean increments: **{fp}**",
                  f"- Verdict accuracy: **{verdict_ok}/{len(key)}**", "",
                  "| class | lenient | strict | n |", "|---|---|---|---|"]
        lines += [f"| {c} | {v[0]} | {v[1]} | {v[2]} |"
                  for c, v in sorted(per_class.items())]
        lines.append("")
    (ROOT / "results/SCORECARD.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
