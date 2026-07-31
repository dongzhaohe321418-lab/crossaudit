#!/usr/bin/env python3
"""Deterministic channels for Part C. Order = cost order:
lint (pyflakes) -> type (mypy) -> tests (pytest w/ mutant substituted)
-> toolrun (standard fixture + golden contract). First killing channel is
recorded; equivalence verification (extended fixtures) runs first and
discards behaviour-preserving mutants. Exit data: kill matrix JSON."""
import json, os, subprocess, sys, tempfile, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = json.load(open(os.path.join(HERE, "fixtures/golden_summary.json")))

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)

def behaviour(src_path, log_path, tol=None):
    """Run a mutant on one input inside a scratch dir (never touches fixtures)."""
    with tempfile.TemporaryDirectory() as td:
        lp = os.path.join(td, "scf.log")
        shutil.copy(log_path, lp)
        cmd = [sys.executable, os.path.abspath(src_path), lp] + ([str(tol)] if tol else [])
        r = run(cmd)
    if r.returncode != 0:
        return ("error", r.stderr.strip().splitlines()[-1][:80] if r.stderr else "err")
    try:
        return ("ok", json.loads(r.stdout))
    except Exception:
        return ("badout", r.stdout[:80])

def equivalence_check(mpath):
    """Behaviour must differ from seed on >=1 extended fixture."""
    seed = os.path.join(HERE, "seed_scripts/convergence_extract.py")
    for fx, tol in [("fixtures/scf.log", None), ("fixtures/scf_edge_tol.log", None),
                    ("fixtures/scf_mid_tol.log", None), ("fixtures/scf_nonmono.log", None),
                    ("fixtures/scf_broken.log", None)]:
        fxp = os.path.join(HERE, fx)
        if behaviour(mpath, fxp, tol) != behaviour(seed, fxp, tol):
            return True
    return False

def ch_lint(mpath):
    r = run([sys.executable, "-m", "pyflakes", mpath])
    return "undefined name" in r.stdout

def ch_type(mpath):
    r = run([sys.executable, "-m", "mypy", "--ignore-missing-imports", "--no-error-summary", mpath])
    return r.returncode != 0

def ch_test(mpath):
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(mpath, os.path.join(td, "convergence_extract.py"))
        shutil.copy(os.path.join(HERE, "seed_scripts/test_convergence_extract.py"), td)
        r = run([sys.executable, "-m", "pytest", td, "-q", "-x"])
        return r.returncode != 0

def ch_toolrun(mpath):
    st, out = behaviour(mpath, os.path.join(HERE, "fixtures/scf.log"))
    if st != "ok": return True
    return out != GOLD          # full-schema contract comparison

def main(mutdir):
    results = []
    for m in json.load(open(os.path.join(mutdir, "MUTATION_LOG.json"))):
        mpath = os.path.join(mutdir, m["id"] + ".py")
        if not equivalence_check(mpath):
            results.append({**m, "valid": False, "killed_by": None}); continue
        killed = None
        for name, fn in [("syntactic", ch_lint), ("type", ch_type),
                         ("test", ch_test), ("toolrun", ch_toolrun)]:
            if fn(mpath): killed = name; break
        results.append({**m, "valid": True, "killed_by": killed})
    out = {"results": results,
           "review_only_residue": [r["id"] for r in results if r["valid"] and r["killed_by"] is None],
           "kills": {c: sum(1 for r in results if r["killed_by"] == c)
                     for c in ["syntactic", "type", "test", "toolrun"]}}
    json.dump(out, open(os.path.join(HERE, "results/deterministic_kill_matrix.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mutants"))
