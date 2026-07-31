#!/usr/bin/env python3
"""Deterministic channels for Part C. Order = cost order:
lint (pyflakes) -> type (mypy) -> tests (pytest w/ mutant substituted)
-> toolrun (standard fixture + golden contract). First killing channel is
recorded; equivalence verification (extended fixtures) runs first and
discards behaviour-preserving mutants. Exit data: kill matrix JSON.

Fail-closed (finding R2, sixth audit). A channel whose tool is absent used to
score silently and wrongly: `python -m mypy` on a machine without mypy exits
non-zero, which the old type channel read as "mutant killed", so every mutant
died in the type channel and the review-only residue, the quantity Part C
exists to measure, collapsed to zero without a warning. Missing pyflakes failed
the other way, contributing zero kills. Three guards now stand in the way:

  1. preflight  - every channel tool is resolved and version-stamped before any
                  mutant runs; a missing tool aborts with exit 2, naming it.
  2. typed exit - each channel distinguishes "tool ran and condemned the mutant"
                  from "tool failed to run"; the latter raises ToolError and
                  aborts rather than counting as a kill.
  3. canary     - the four channels run against the unmutated seed script first
                  and must all stay silent; a channel that kills the seed is
                  misconfigured, whatever it would have said about a mutant.

The resolved toolchain is written into the kill matrix, so a residue figure can
always be read back against the tools that produced it.
"""
import json, os, platform, subprocess, sys, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = json.load(open(os.path.join(HERE, "fixtures/golden_summary.json")))
SEED = os.path.join(HERE, "seed_scripts/convergence_extract.py")
CHANNEL_TOOLS = {"syntactic": "pyflakes", "type": "mypy", "test": "pytest"}


class ToolError(RuntimeError):
    """A channel's tool did not run; its verdict is unusable."""


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)


def preflight():
    """Resolve every channel tool, or abort. Returns the version stamp."""
    stamp = {"python": platform.python_version(), "platform": platform.platform()}
    missing = []
    for channel, mod in CHANNEL_TOOLS.items():
        r = run([sys.executable, "-m", mod, "--version"])
        if r.returncode != 0:
            missing.append(f"  {channel:9s} channel needs `{sys.executable} -m {mod}`")
        else:
            stamp[mod] = ((r.stdout or r.stderr).strip().splitlines() or [""])[0]
    if missing:
        print("PREFLIGHT FAILED — deterministic channels cannot be scored:",
              *missing, "Install the missing tools (pip install -e '.[partC]')",
              sep="\n", file=sys.stderr)
        sys.exit(2)
    return stamp


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
    for fx, tol in [("fixtures/scf.log", None), ("fixtures/scf_edge_tol.log", None),
                    ("fixtures/scf_mid_tol.log", None), ("fixtures/scf_nonmono.log", None),
                    ("fixtures/scf_broken.log", None)]:
        fxp = os.path.join(HERE, fx)
        if behaviour(mpath, fxp, tol) != behaviour(SEED, fxp, tol):
            return True
    return False


def ch_lint(mpath):
    r = run([sys.executable, "-m", "pyflakes", mpath])
    if r.returncode not in (0, 1):          # 0 clean, 1 messages, else tool trouble
        raise ToolError(f"pyflakes exit {r.returncode}: {r.stderr.strip()[:200]}")
    return "undefined name" in r.stdout


def ch_type(mpath):
    r = run([sys.executable, "-m", "mypy", "--ignore-missing-imports",
             "--no-error-summary", mpath])
    if r.returncode not in (0, 1):          # 2 = usage/crash, 127 = absent
        raise ToolError(f"mypy exit {r.returncode}: {(r.stderr or r.stdout).strip()[:200]}")
    return "error:" in r.stdout


def ch_test(mpath):
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(mpath, os.path.join(td, "convergence_extract.py"))
        shutil.copy(os.path.join(HERE, "seed_scripts/test_convergence_extract.py"), td)
        r = run([sys.executable, "-m", "pytest", td, "-q", "-x"])
        if r.returncode not in (0, 1):      # 2 interrupted, 3 internal, 4 usage, 5 no tests
            raise ToolError(f"pytest exit {r.returncode}: {(r.stdout or r.stderr)[-200:]}")
        return r.returncode == 1


def ch_toolrun(mpath):
    st, out = behaviour(mpath, os.path.join(HERE, "fixtures/scf.log"))
    if st != "ok": return True
    return out != GOLD          # full-schema contract comparison


CHANNELS = [("syntactic", ch_lint), ("type", ch_type),
            ("test", ch_test), ("toolrun", ch_toolrun)]


def canary():
    """No channel may kill the unmutated seed. One that does is misconfigured."""
    fired = [name for name, fn in CHANNELS if fn(SEED)]
    if fired:
        print(f"CANARY FAILED — channel(s) {fired} condemn the unmutated seed "
              f"script; their verdicts on mutants cannot be trusted.", file=sys.stderr)
        sys.exit(3)
    return {"seed_script": os.path.relpath(SEED, HERE), "channels_fired": []}


def main(mutdir):
    toolchain = preflight()
    canary_result = canary()
    results = []
    for m in json.load(open(os.path.join(mutdir, "MUTATION_LOG.json"))):
        mpath = os.path.join(mutdir, m["id"] + ".py")
        if not equivalence_check(mpath):
            results.append({**m, "valid": False, "killed_by": None}); continue
        killed = None
        for name, fn in CHANNELS:
            if fn(mpath): killed = name; break
        results.append({**m, "valid": True, "killed_by": killed})
    out = {"toolchain": toolchain,
           "canary": canary_result,
           "results": results,
           "review_only_residue": [r["id"] for r in results if r["valid"] and r["killed_by"] is None],
           "kills": {c: sum(1 for r in results if r["killed_by"] == c)
                     for c, _ in CHANNELS}}
    json.dump(out, open(os.path.join(HERE, "results/deterministic_kill_matrix.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mutants"))
