#!/usr/bin/env python3
"""Seal the defect key before any model arm runs.

What sealing does and does not do, stated plainly because v1 got this wrong.

A hash commitment proves the key did not change after the run. It does not
prove nobody saw it beforehand. Only custody by someone with no stake in the
result does that, which is why the registration asks for a third party and why
this script requires one to be named.

Three custody modes are supported, and each is recorded with what it is worth:

  collaborator   the key file goes to a repository the operator cannot rewrite
  osf            the key is attached to a timestamped OSF registration
  encrypted      an archive held by the second author, password published when
                 the arms finish

Whichever is used, the SEAL file committed here carries the digest, the mode,
the custodian, and the time. Running the arms without a committed SEAL is what
the RUNBOOK's red line forbids.

Usage:
  python3 seal_key.py --key /secure/key.json --mode collaborator \
      --custodian "name, and where it went" --out ../results/SEAL-v3.json
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

WORTH = {
 "collaborator": "custody by a party who cannot rewrite the operator's history; "
                 "integrity and prior secrecy both rest on that party's independence",
 "osf": "a timestamped third-party registration; strongest on 'the key existed and "
        "has not changed', silent on who read it before registration",
 "encrypted": "custody by the second author; adequate for a two-author paper, and "
              "readers should weigh that the custodian is a co-author",
 "hash-only": "NO third-party custody. Proves only that the key did not change after "
              "this commit. Does not support any blinding claim, and the write-up "
              "must say so in the same sentence as the results",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--mode", required=True, choices=sorted(WORTH))
    ap.add_argument("--custodian", required=True,
                    help="who holds it and where; for hash-only, say why no custodian")
    ap.add_argument("--corpus", required=True, help="corpus dir, for its CORPUS.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stamp", required=True, help="ISO timestamp; passed in, never taken from the clock")
    a = ap.parse_args()

    keyp = Path(a.key)
    if not keyp.exists(): sys.exit(f"no key at {keyp}")
    repo = Path(__file__).resolve().parents[2]
    if repo in keyp.resolve().parents:
        sys.exit("the key is inside the repository. That is the v1 failure; move it out first.")

    digest = hashlib.sha256(keyp.read_bytes()).hexdigest()
    corpus = json.loads((Path(a.corpus) / "CORPUS.json").read_text())
    if corpus.get("defect_key_sha256") != digest:
        sys.exit(f"digest mismatch: corpus records {corpus.get('defect_key_sha256')}, key hashes to {digest}")

    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=repo).stdout.strip()
    seal = {"defect_key_sha256": digest, "custody_mode": a.mode,
            "custodian": a.custodian, "what_this_is_worth": WORTH[a.mode],
            "sealed_at": a.stamp, "repo_head_at_sealing": head,
            "corpus": {k: corpus[k] for k in
                       ("seed", "n_increments", "n_defects", "channel_counts",
                        "generator_sha256", "authored_by") if k in corpus},
            "red_line": "No model arm may run before this file is committed."}
    Path(a.out).write_text(json.dumps(seal, indent=1) + "\n")
    print(json.dumps(seal, indent=1))
    if a.mode == "hash-only":
        print("\nWARNING: hash-only. No blinding claim is supported by this seal.", file=sys.stderr)

if __name__ == "__main__":
    main()
