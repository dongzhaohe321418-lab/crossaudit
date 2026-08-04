#!/usr/bin/env python3
"""Score the isolation ladder. Frozen at registration; do not edit after arms run.

Two things this does that the v1 scorer did not.

**Per-defect binding.** A defect counts as caught when one finding names its
location. One finding cannot discharge two defects, and a pile of findings
cannot discharge one; v1's strict tier assembled evidence across findings and
overstated localisation, which the fourth audit caught.

**Chance correction and a trend, not a league table.** Recall rises with volume,
so raw comparison is meaningless. Every rung gets a permutation floor, and the
headline is Cochran's Q across the ladder with exact McNemar between adjacent
rungs under Holm, because the registered question is whether isolation buys
anything monotonically, not which single arm wins.

The co-primary is the false-block rate on clean increments, reported beside
recall always. An arm that finds everything and blocks everything has found
nothing.
"""
from __future__ import annotations
import argparse, json, math, random, re
from collections import defaultdict
from pathlib import Path

from reply_schema import partition, referrals

LADDER = ["L1", "L2", "L3", "L4", "L4b", "L5"]

def norm(s: str) -> set:
    """Tokens that identify a location, insensitive to how it was phrased."""
    s = (s or "").lower()
    return {t for t in re.findall(r"[a-z_][a-z0-9_]{2,}", s)
            if t not in {"json", "the", "and", "for", "results", "file", "field", "value"}}

def matched(defect: dict, finding: dict) -> bool:
    want = norm(defect["location"]) | norm(defect.get("description", ""))
    got = norm(finding.get("location", "")) | norm(finding.get("description", ""))
    return len(want & got) >= 2

def score_arm(key: dict, arm: dict):
    """Bind at most one finding to each defect. Returns per-defect hits and extras."""
    hits, extras = {}, defaultdict(list)
    for inc, defects in key.items():
        found = list((arm.get(inc) or {}).get("findings", []))
        used = set()
        for d in defects:
            j = next((i for i, f in enumerate(found)
                      if i not in used and matched(d, f)), None)
            hits[(inc, d["class"], d["location"])] = j is not None
            if j is not None: used.add(j)
        extras[inc] = [f for i, f in enumerate(found) if i not in used]
    return hits, extras

def permutation_floor(key, arm, shuffles, seed):
    """Shuffle which increment holds which defects; the arm's outputs never move."""
    rng = random.Random(seed)
    incs = sorted(key)
    bags = [key[i] for i in incs]
    floors = []
    for _ in range(shuffles):
        perm = bags[:]; rng.shuffle(perm)
        shuffled = dict(zip(incs, perm))
        h, _ = score_arm(shuffled, arm)
        floors.append(sum(h.values()))
    floors.sort()
    return {"mean": round(sum(floors) / len(floors), 1),
            "p95": floors[int(0.95 * len(floors))],
            "sd": round((sum((x - sum(floors)/len(floors))**2 for x in floors)/len(floors))**0.5, 1)}

def mcnemar_exact(a, b):
    """Two-sided exact McNemar on paired per-defect outcomes."""
    n01 = sum(1 for k in a if not a[k] and b.get(k))
    n10 = sum(1 for k in a if a[k] and not b.get(k))
    n = n01 + n10
    if n == 0: return {"b": n01, "c": n10, "p": 1.0}
    k = min(n01, n10)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)
    return {"b": n01, "c": n10, "p": round(p, 5)}

def cochran_q(arms):
    """Q over k arms on the shared per-defect matrix."""
    keys = sorted(set.intersection(*(set(a) for a in arms.values()))) if arms else []
    if not keys: return None
    k = len(arms); names = sorted(arms)
    rows = [[1 if arms[n][key] else 0 for n in names] for key in keys]
    G = [sum(r[j] for r in rows) for j in range(k)]
    L = [sum(r) for r in rows]
    num = (k - 1) * (k * sum(g*g for g in G) - sum(G)**2)
    den = k * sum(L) - sum(l*l for l in L)
    if den == 0: return {"Q": None, "df": k - 1, "note": "no discordant defects"}
    return {"Q": round(num / den, 3), "df": k - 1, "n_defects": len(keys)}

def holm(pvals: dict):
    order = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, run = len(order), {}, 0.0
    for i, (k, p) in enumerate(order):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = round(run, 5)
    return out

def clopper(k, n, alpha=0.05):
    def le(p): return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k+1))
    def ge(p): return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))
    lo, hi = 0.0, 1.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(160):
            m = (a+b)/2
            a, b = (m, b) if ge(m) < alpha/2 else (a, m)
        lo = (a+b)/2
    if k < n:
        a, b = 0.0, 1.0
        for _ in range(160):
            m = (a+b)/2
            a, b = (m, b) if le(m) > alpha/2 else (a, m)
        hi = (a+b)/2
    return round(lo, 3), round(hi, 3)

def load_arm(d: Path):
    """Normalise every arm's replies through one partition, so no arm is read
    on terms another was not. `findings` after this call means "entries the
    auditor still stood behind"; entries it withdrew, and pairs it referred to a
    deterministic check, are kept beside them and reported, never scored."""
    out = {}
    for p in sorted(d.glob("INC-*.json")):
        rec = json.loads(p.read_text())
        parsed = rec.get("parsed")
        found, withdrawn = partition(parsed)
        out[rec["increment"]] = {**(parsed or {}), "findings": found,
                                 "_withdrawn": withdrawn,
                                 "_referred": referrals(parsed)}
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--results", required=True, help="dir holding one subdir per rung")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--shuffles", type=int, default=2000)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    blob = json.loads(Path(a.key).read_text())
    key, meta = blob["key"], blob["meta"]
    clean = [d.name for d in sorted(Path(a.corpus).glob("INC-*")) if d.name not in key]
    total = sum(len(v) for v in key.values())

    arms, per_arm = {}, {}
    for rung in LADDER:
        d = Path(a.results) / rung
        if not d.exists(): continue
        arm = load_arm(d)
        hits, extras = score_arm(key, arm)
        arms[rung] = hits
        n_find = sum(len((arm.get(i) or {}).get("findings", [])) for i in arm)
        blocked = [i for i in clean if (arm.get(i) or {}).get("findings")]
        lo, hi = clopper(len(blocked), len(clean)) if clean else (None, None)
        by_ch = defaultdict(lambda: [0, 0])
        for inc, ds in key.items():
            for d_ in ds:
                cell = by_ch[d_["channel"]]
                cell[1] += 1
                cell[0] += 1 if hits[(inc, d_["class"], d_["location"])] else 0
        per_arm[rung] = {
            "recall": sum(hits.values()), "of": total,
            "findings_emitted": n_find,
            "withdrawn_by_author": sum(len((arm.get(i) or {}).get("_withdrawn", [])) for i in arm),
            "referred_to_tools": sum(len((arm.get(i) or {}).get("_referred", [])) for i in arm),
            "chance_floor": permutation_floor(key, arm, a.shuffles, a.seed),
            "false_block_rate": {"blocked": len(blocked), "clean": len(clean),
                                 "ci95": [lo, hi]},
            "recall_by_channel": {k: {"caught": v[0], "of": v[1]} for k, v in by_ch.items()},
        }

    adjacent = [(x, y) for x, y in zip(LADDER, LADDER[1:]) if x in arms and y in arms]
    raw = {f"{x}->{y}": mcnemar_exact(arms[x], arms[y]) for x, y in adjacent}
    adj = holm({k: v["p"] for k, v in raw.items()}) if raw else {}
    report = {
        "frozen_scorer_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest(),
        "corpus": meta, "n_defects": total, "n_clean": len(clean),
        "shuffles": a.shuffles, "seed": a.seed,
        "arms": per_arm,
        "trend": cochran_q(arms),
        "adjacent_mcnemar": {k: {**v, "p_holm": adj.get(k)} for k, v in raw.items()},
        "reading": "Recall is meaningless beside its chance floor and its false-block rate. "
                   "The registered headline is the trend across rungs, not any single arm.",
    }
    Path(a.out).write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "corpus"}, indent=1)[:2600])

if __name__ == "__main__":
    main()
