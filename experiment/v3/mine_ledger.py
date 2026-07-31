#!/usr/bin/env python3
"""Mine the real CrossAudit deployment ledger (perovskite-screening + -audit).

Read-only over both repos. Emits structurally-redacted records (Level-B: free
text is hashed, structural fields verbatim) suitable for public commit, plus a
human-readable summary. Label rule (FROZEN at registration):

  CONFIRMED_REAL  - finding_id appears in a later cycle's verified_closed_findings,
                    or a science-repo commit subject names it as fixed.
  UNRESOLVED      - still OPEN at the ledger freeze; excluded from precision metrics.

Usage: python3 mine_ledger.py <pv-science-dir> <pv-audit-dir> <out-dir>
"""
import json, sys, glob, os, hashlib, subprocess, re

def sha(s): return hashlib.sha256(s.encode()).hexdigest()[:16]

def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True).stdout

def main(sci, aud, out):
    os.makedirs(out, exist_ok=True)
    freeze = {"science_head": git(sci, "rev-parse", "HEAD").strip(),
              "audit_head": git(aud, "rev-parse", "HEAD").strip()}
    cycles, findings = [], {}
    for d in sorted(glob.glob(os.path.join(aud, "projects/*/cycles/CYCLE-*"))):
        cid = os.path.basename(d)
        res = json.load(open(os.path.join(d, "audit_result.json")))
        meta = json.load(open(os.path.join(d, "codex_run_metadata.json")))
        rec = {"cycle_id": cid, "audited_commit": res.get("audited_commit"),
               "decision": res.get("decision"), "model": meta.get("model"),
               "runner": meta.get("runner"), "started_at": meta.get("started_at"),
               "completed_at": meta.get("completed_at"),
               "n_findings": len(res.get("findings", [])),
               "verified_closed": [f.get("finding_id") if isinstance(f, dict) else str(f)
                                    for f in res.get("verified_closed_findings", [])],
               "findings": []}
        for f in res.get("findings", []):
            if not isinstance(f, dict): continue
            fid = f.get("finding_id")
            ev = str(f.get("evidence", ""))
            rules = sorted(set(re.findall(r"R-[A-Z]+-\d+|Gate\s*\d+", ev)))
            fr = {"finding_id": fid, "severity": f.get("severity"),
                  "status": f.get("status"), "blocked_scopes": f.get("blocked_scopes"),
                  "title_sha16": sha(str(f.get("title", ""))), "rules_cited": rules}
            rec["findings"].append(fr)
            findings.setdefault(fid, {"finding_id": fid, "severity": f.get("severity"),
                                      "first_raised": cid, "raised_in": [], "closed_confirmed_in": None,
                                      "rules_cited": rules})
            findings[fid]["raised_in"].append(cid)
        cycles.append(rec)
    for rec in cycles:                                # closure pass
        for fid in rec["verified_closed"]:
            fid = str(fid).split(":")[0].strip()
            m = re.match(r"F-\d+", fid)
            key = m.group(0) if m else fid
            if key in findings and findings[key]["closed_confirmed_in"] is None:
                findings[key]["closed_confirmed_in"] = rec["cycle_id"]
            elif key not in findings:                 # closed but never seen OPEN in ledger (raised+fixed within one leg)
                findings[key] = {"finding_id": key, "severity": None, "first_raised": None,
                                 "raised_in": [], "closed_confirmed_in": rec["cycle_id"], "rules_cited": []}
    # science-side fix commits
    log = git(sci, "log", "--format=%H\t%ad\t%s", "--date=iso-strict")
    fix_commits = [{"sha": l.split("\t")[0][:12], "date": l.split("\t")[1],
                    "fids": sorted(set(re.findall(r"F-\d+", l.split("\t")[2]))),
                    "subject_sha16": sha(l.split("\t")[2])}
                   for l in log.splitlines() if re.search(r"(?i)audit CYCLE|F-\d", l.split("\t")[2])]
    for fc in fix_commits:
        for fid in fc["fids"]:
            if fid in findings:
                findings[fid].setdefault("fix_commits", []).append(fc["sha"])
    n_conf = sum(1 for f in findings.values() if f["closed_confirmed_in"])
    summary = {"freeze": freeze, "n_cycles": len(cycles),
               "decisions": [c["decision"] for c in cycles],
               "findings_per_cycle": [c["n_findings"] for c in cycles],
               "n_distinct_findings": len(findings), "n_confirmed_real": n_conf,
               "n_unresolved": sum(1 for f in findings.values() if not f["closed_confirmed_in"]),
               "models": sorted(set(c["model"] for c in cycles if c["model"])),
               "n_science_fix_commits": len(fix_commits)}
    with open(os.path.join(out, "cycles.jsonl"), "w") as fh:
        for c in cycles: fh.write(json.dumps(c) + "\n")
    json.dump(sorted(findings.values(), key=lambda x: x["finding_id"]),
              open(os.path.join(out, "findings_lifecycle.json"), "w"), indent=1)
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
