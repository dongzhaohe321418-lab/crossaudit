#!/usr/bin/env python3
"""Deterministic self-consistency check on the corpus, before any model is called.

Every defect this catches is one a model arm would otherwise report against a
clean increment, where it would be scored as a false alarm and would inflate the
false-block rate of every arm equally -- measuring the corpus, not the auditors.
v1 lost a rung to exactly that. The rule this file enforces is the protocol's own
I4: if a check is decidable by script, no model should be spending a round on it.

Three families:

  paths    every path the increment names -- declared inputs, declared outputs,
           the lockfile, the rerun command, the source of each reported quantity
           -- resolves to a file that is actually shipped.
  numbers  the domain-tool checks in tool_checks.py draw nothing on a clean
           increment.
  digits   each reported value agrees with its evidence to the precision it is
           printed at, not merely to a tolerance the checker chose. A record
           printed to four decimals that is right to three invites a finding.

Increments carrying seeded defects are exempted from precisely the claim their
defect breaks and checked on everything else; the exemption map is explicit
below, so a new defect class that breaks a path claim fails this script until
someone adds it deliberately.

Exit 0 only when every increment passes. Anything else is a corpus to fix.

Usage: python3 check_corpus.py --corpus <dir> --key <path> [--json out.json]
"""
from __future__ import annotations
import argparse, json, re, sys
from hashlib import sha256
from pathlib import Path

import yaml

from tool_checks import HARTREE_EV, check_increment, parse_log

# Which claim each defect class deliberately breaks. A class absent from this map
# is expected to leave every claim below intact; if it does not, this script says
# so rather than letting a model arm discover it after the key is sealed.
EXEMPT = {
    "D1": {"source"},   # removes a quantity's source outright
    "L4": {"source"},   # points a source at a script that was never declared
    "D2": {"digits"},   # mislabels a unit, so the printed-precision test is moot
    "T1": {"numbers", "digits"},
    "T2": {"numbers"},
    "T3": {"numbers"},
    "D3": {"numbers"},
}

REV = re.compile(r"@[0-9a-f]{5,}$")           # source strings carry @<code_version>
RERUN = re.compile(r"([\w./-]+\.py)")


def declared_paths(meta: dict, res: dict) -> list[tuple[str, str]]:
    """(claim-kind, relative path) for every file the increment says exists."""
    out = []
    for p in meta.get("inputs") or []:
        out.append(("inputs", str(p)))
    for p in meta.get("outputs") or []:
        out.append(("outputs", str(p)))
    lock = (meta.get("environment") or {}).get("lockfile")
    if lock:
        out.append(("lockfile", str(lock)))
    m = RERUN.search(str(meta.get("rerun") or ""))
    if m:
        out.append(("rerun", m.group(1)))
    for q in res.get("quantities") or []:
        if isinstance(q, dict) and q.get("source"):
            out.append(("source", REV.sub("", str(q["source"]))))
    return out


def printed_precision(text: str, value_repr: str) -> float | None:
    """Half a unit in the last printed place of a decimal literal."""
    if "." not in value_repr:
        return None
    return 0.5 * 10 ** -len(value_repr.split(".")[1])


def check_digits(d: Path, res: dict) -> list[dict]:
    """Reported eV must equal the log's hartree to the precision both are printed at."""
    q = {x["name"]: x for x in res.get("quantities", []) if isinstance(x, dict)}
    tot = q.get("total_energy")
    if not tot or tot.get("unit") != "eV":
        return []
    raw = re.search(r"# final energy (-?\d+\.\d+) hartree", (d / "scf.log").read_text())
    if not raw:
        return [{"check": "digits", "detail": "no '# final energy' line to compare against"}]
    ha_txt = raw.group(1)
    ev_txt = json.dumps(tot["value"])
    tol_ev = printed_precision(ev_txt, ev_txt) or 5e-5
    # The hartree line's own rounding propagates into eV and must be allowed for.
    tol_ha = (printed_precision(ha_txt, ha_txt) or 5e-7) * HARTREE_EV
    got, want = float(ev_txt), float(ha_txt) * HARTREE_EV
    if abs(got - want) > tol_ev + tol_ha:
        return [{"check": "digits",
                 "detail": f"results.json prints {ev_txt} eV; scf.log prints {ha_txt} Ha "
                           f"= {want:.6f} eV. Gap {abs(got-want):.6f} eV exceeds the "
                           f"{tol_ev + tol_ha:.6f} eV the two printed precisions allow."}]
    return []


def corpus_digest(root: Path) -> str:
    """One digest over every increment file, so a committed report cannot be
    presented as evidence about a corpus it was not run against."""
    h = sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "CORPUS-CHECK.json"):
        h.update(str(f.relative_to(root)).encode()); h.update(b"\0")
        h.update(sha256(f.read_bytes()).digest())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()

    key = json.loads(Path(a.key).read_text())["key"]
    incs = sorted(Path(a.corpus).glob("INC-*"))
    if not incs:
        sys.exit("no increments found")

    problems, checked = {}, 0
    for d in incs:
        exempt = set()
        for defect in key.get(d.name, []):
            exempt |= EXEMPT.get(defect["class"], set())
        meta = yaml.safe_load((d / "metadata.yml").read_text())
        res = json.loads((d / "results.json").read_text())
        found = []

        for kind, rel in declared_paths(meta, res):
            if kind in exempt:
                continue
            if not (d / rel).is_file():
                found.append({"check": f"path:{kind}",
                              "detail": f"{kind} names {rel!r}, which is not shipped in this increment"})

        if "numbers" not in exempt:
            fs, ran = check_increment(d)
            if not ran:
                found.append({"check": "numbers", "detail": "the domain checks could not run"})
            found += [{"check": f"tool:{f['check']}", "detail": f["detail"]} for f in fs]

        if "digits" not in exempt:
            found += check_digits(d, res)

        checked += 1
        if found:
            problems[d.name] = found

    report = {"increments_checked": checked, "increments_with_problems": len(problems),
              "corpus_sha256": corpus_digest(Path(a.corpus)),
              "checker_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "problems": problems}
    print(json.dumps(report, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1) + "\n")
    if problems:
        print(f"\n{len(problems)} increment(s) contradict themselves before any model has "
              f"read them. Fix the generator, not the rulebook.", file=sys.stderr)
        sys.exit(1)
    print("\nthe corpus is self-consistent on paths, numbers and printed digits.")


if __name__ == "__main__":
    main()
