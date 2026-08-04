#!/usr/bin/env python3
"""Second-snapshot analysis of the live deployment ledger.

Read-only over both science repositories. Emits analysis.json plus the
integrity checks that decide which statements the data can carry. Every
derived quantity here is process metadata: cycle identities, decisions,
severities, self-labelled finding sources, rule citations, timestamps.
No scientific content is read, quoted, or judged.

Usage: python3 analyse_ledger.py <pv-science> <pv-audit> <out-dir>
"""
import json, glob, os, re, sys, subprocess, statistics as st
from collections import Counter, defaultdict
from datetime import datetime

def git(r,*a): return subprocess.run(["git","-C",r]+list(a),capture_output=True,text=True).stdout.strip()
def T(s):
    try: return datetime.fromisoformat(str(s).replace("Z","+00:00"))
    except Exception: return None

def main(sci, aud, out):
    os.makedirs(out, exist_ok=True)
    cycles=[]
    for d in sorted(glob.glob(os.path.join(aud,"projects/*/cycles/CYCLE-*"))):
        res=json.load(open(d+"/audit_result.json"))
        meta=json.load(open(d+"/codex_run_metadata.json"))
        fs=[f for f in res.get("findings",[]) if isinstance(f,dict)]
        recs=[]
        for f in fs:
            ev=" | ".join(str(x) for x in (f.get("evidence") or []))
            recs.append(dict(fid=f.get("finding_id"), sev=f.get("severity"),
                scopes=list(f.get("blocked_scopes") or []),
                source=(re.search(r"source:\s*([A-Z_]+)",ev) or [None,None])[1],
                fclass=(re.search(r"finding_class:\s*([A-Z_]+)",ev) or [None,None])[1],
                rules=sorted(set(re.findall(r"R-[A-Z]+-\d+|Gate\s*\d+|CA-[A-Z]+-\d+", ev)))))
        cycles.append(dict(cid=os.path.basename(d), decision=res["decision"],
            started=meta.get("started_at"), completed=meta.get("completed_at"),
            model=meta.get("model"), findings=recs,
            closed=[m.group(0) for v in res.get("verified_closed_findings",[])
                    for m in [re.search(r"F-\d+", v.get("finding_id","") if isinstance(v,dict) else str(v))]
                    if m]))
    idx={c["cid"]:i for i,c in enumerate(cycles)}
    allf=[f for c in cycles for f in c["findings"]]

    # --- integrity check: is the decision definitional given blocked_scopes? ---
    determ=Counter()
    for c in cycles:
        determ[(c["decision"], any(f["scopes"] for f in c["findings"]))]+=1
    decision_is_definitional = all(
        (dec=="BLOCK") == blocking for (dec,blocking),_ in determ.items() if dec!="PASS")

    # --- lifecycle ---
    raised=defaultdict(list); closed={}
    for c in cycles:
        for f in c["findings"]: raised[f["fid"]].append(c["cid"])
        for k in c["closed"]:
            if k not in closed: closed[k]=c["cid"]
    lags={k: idx[closed[k]]-idx[raised[k][0]] for k in raised if k in closed}
    survived={k:len(v) for k,v in raised.items() if len(v)>1}

    # --- cadence ---
    durs=[(T(c["completed"])-T(c["started"])).total_seconds()/60
          for c in cycles if T(c["started"]) and T(c["completed"])]
    gaps=[]; prev=None
    for c in cycles:
        a=T(c["started"])
        if prev and a: gaps.append((a-prev).total_seconds()/60)
        if T(c["completed"]): prev=T(c["completed"])

    an=dict(
      freeze=dict(science=git(sci,"rev-parse","HEAD"), audit=git(aud,"rev-parse","HEAD")),
      n_cycles=len(cycles), n_findings=len(allf), n_distinct=len(raised),
      n_closed=len(closed), n_open=len(raised)-len(closed),
      decisions=Counter(c["decision"] for c in cycles),
      findings_per_cycle=[len(c["findings"]) for c in cycles],
      severity=Counter(f["sev"] for f in allf),
      source=Counter(f["source"] for f in allf),
      fclass=Counter(f["fclass"] for f in allf),
      source_x_severity=Counter(f"{f['source']}|{f['sev']}" for f in allf),
      scopes=Counter(s for f in allf for s in f["scopes"]),
      rules=Counter(r for f in allf for r in f["rules"]),
      rule_cycle_spread={r: len({c["cid"] for c in cycles for f in c["findings"] if r in f["rules"]})
                         for r in {r for f in allf for r in f["rules"]}},
      decision_vs_blocking={f"{k[0]}|any_blocking={k[1]}":v for k,v in determ.items()},
      decision_is_definitional=decision_is_definitional,
      closure_lag=dict(median=st.median(lags.values()), mean=round(st.mean(lags.values()),2),
                       max=max(lags.values()), per_finding=lags),
      survived_multiple_audits=survived,
      audit_minutes=dict(median=round(st.median(durs),1), min=round(min(durs),1), max=round(max(durs),1)),
      gap_minutes=dict(median=round(st.median(gaps)), q1=round(sorted(gaps)[len(gaps)//4]),
                       q3=round(sorted(gaps)[3*len(gaps)//4]), max=round(max(gaps))),
      models=sorted({c["model"] for c in cycles if c["model"]}),
    )
    an={k:(dict(v) if isinstance(v,Counter) else v) for k,v in an.items()}
    json.dump(an, open(os.path.join(out,"analysis.json"),"w"), indent=1, default=str)
    json.dump(cycles, open(os.path.join(out,"cycles-b.json"),"w"), indent=1)
    print(json.dumps({k:v for k,v in an.items() if k not in ("closure_lag","rule_cycle_spread")}, indent=1, default=str))

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
