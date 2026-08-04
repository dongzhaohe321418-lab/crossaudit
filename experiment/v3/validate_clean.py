#!/usr/bin/env python3
"""Audit the clean increments before sealing, and refuse to seal until they pass.

A corpus is clean with respect to its key. It is not automatically clean with
respect to the rulebook, and those are different properties. If a clean
increment violates a rule nobody seeded, every arm will report it, the
false-block rate will measure the corpus rather than the auditor, and the study
will conclude that auditors are miscalibrated when the truth is that the corpus
was broken. v1 hit exactly this: a rule requiring a source on every numeric
entry, against convergence blocks that carried none.

Reading the clean set with a model is blinding-safe, because clean increments
contain no key material. Reading the defective set is not, and this script
refuses to touch it.

Exit 0 only when the clean set draws no findings. Anything else is work to do.

Usage:
  python3 validate_clean.py --corpus <dir> --key <path> --vendor anthropic \
      --model <id> [--sample 6]
"""
from __future__ import annotations
import argparse, json, os, random, subprocess, sys
from pathlib import Path

from reply_schema import partition, referrals

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True); ap.add_argument("--key", required=True)
    ap.add_argument("--vendor", default="anthropic"); ap.add_argument("--model", required=True)
    ap.add_argument("--sample", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    key = json.loads(Path(a.key).read_text())["key"]
    clean = [d for d in sorted(Path(a.corpus).glob("INC-*")) if d.name not in key]
    if not clean: sys.exit("no clean increments")
    rng = random.Random(a.seed)
    pick = clean if a.sample >= len(clean) else rng.sample(clean, a.sample)

    stage = Path("/tmp/_validate_clean"); subprocess.run(["rm", "-rf", str(stage)])
    stage.mkdir(parents=True)
    for d in pick: subprocess.run(["cp", "-r", str(d), str(stage)])

    out = Path("/tmp/_validate_out"); subprocess.run(["rm", "-rf", str(out)])
    here = Path(__file__).parent
    r = subprocess.run([sys.executable, str(here / "run_rung.py"), "--rung", "validate",
                        "--vendor", a.vendor, "--model", a.model, "--constitution", "full",
                        "--corpus", str(stage), "--out", str(out)],
                       capture_output=True, text=True)
    if r.returncode: sys.exit(f"the audit call failed: {r.stdout}\n{r.stderr}")

    total, n_withdrawn, n_referred, report = 0, 0, 0, {}
    for p in sorted(out.glob("INC-*.json")):
        rec = json.loads(p.read_text())
        fs, withdrawn = partition(rec.get("parsed"))
        total += len(fs); n_withdrawn += len(withdrawn)
        n_referred += len(referrals(rec.get("parsed")))
        report[rec["increment"]] = [{"rule": f.get("rule"), "why": f.get("description")} for f in fs]
    print(json.dumps({"clean_increments_sampled": len(pick), "findings": total,
                      "withdrawn_by_author": n_withdrawn, "referred_to_tools": n_referred,
                      "detail": report}, indent=1))
    if total:
        print(f"\n{total} finding(s) on increments nobody seeded. Each is either a corpus "
              f"defect to fix or an auditor false positive to record before sealing; "
              f"deciding which is the operator's, and the decision belongs in the "
              f"registration.", file=sys.stderr)
        sys.exit(1)
    print("\nclean set draws nothing. Safe to seal.")

if __name__ == "__main__":
    main()
