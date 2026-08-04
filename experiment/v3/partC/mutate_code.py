#!/usr/bin/env python3
"""Deterministic mutator for the Part C seed script.

Each mutant: (id, class, predicted cheapest channel, textual substitution).
The mutation log written here IS the defect key; on the real run it is sealed
before any model arm executes. Equivalence rule: a mutant must change
behaviour on the EXTENDED fixture set (fixtures/*.log incl. edge inputs);
the deterministic toolrun channel later sees only the STANDARD fixture
(scf.log) -- the gap is what makes a review-only stratum possible, mirroring
reality: no auditor runs exhaustive inputs.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = {"conv": "seed_scripts/convergence_extract.py",
         "tab": "seed_scripts/tabulate_results.py"}
SRC = {k: open(os.path.join(HERE, v)).read() for k, v in SEEDS.items()}
SEED = SRC["conv"]  # legacy alias for the first registry below

MUTANTS = [
  # -- syntactic (lint-catchable: undefined name in the error branch) --
  ("M-SYN-01", "undefined_name_in_error_branch", "syntactic",
   'raise ValueError("no SCF steps found")',
   'raise ValueError("no SCF steps found: " + log_pathh)'),
  # -- type-level (mypy-catchable: energy becomes str) --
  ("M-TYP-01", "float_return_becomes_str", "type",
   '"final_energy_ev": final_e_ha * HARTREE_TO_EV,',
   '"final_energy_ev": str(final_e_ha * HARTREE_TO_EV),'),
  # -- test-killable (the hand-computed example dies) --
  ("M-TST-01", "unit_conversion_dropped", "test",
   "HARTREE_TO_EV = 27.211386245988", "HARTREE_TO_EV = 1.0"),
  ("M-TST-02", "off_by_one_step_count", "test",
   '"converged": converged, "n_steps": n}', '"converged": converged, "n_steps": n - 1}'),
  # -- tool-verifiable (schema/contract drift; tests don't cover schema) --
  # NOTE: originally predicted toolrun; adding TypedDict annotations moved
  # this whole class left, to the type channel -- "typing shifts contract
  # drift from runtime to static analysis", itself a reportable observation.
  ("M-TOL-01", "output_key_renamed", "type",
   '"converged": converged,', '"is_converged": converged,'),
  ("M-TOL-02", "converged_flag_inverted", "toolrun",
   "converged = last_de <= tol_hartree", "converged = last_de > tol_hartree"),
  # -- review-only (behaviour changes only off the standard fixture) --
  ("M-REV-01", "boundary_flip_at_tolerance", "review-only",
   "converged = last_de <= tol_hartree", "converged = last_de < tol_hartree"),
  ("M-REV-02", "tolerance_loosened_1000x", "review-only",
   "float(sys.argv[2]) if len(sys.argv) > 2 else 1e-6",
   "float(sys.argv[2]) if len(sys.argv) > 2 else 1e-3"),
  ("M-REV-03", "last_step_vs_min_energy", "review-only",
   "final_e_ha = steps[-1][1]", "final_e_ha = min(s[1] for s in steps)"),
]

MUTANTS = [(mid, mclass, ch, old, new, "conv") for (mid, mclass, ch, old, new) in MUTANTS] + [
  # ---- tabulate_results.py ----
  ("T-SYN-01", "undefined_name_in_error_branch", "syntactic",
   'raise ValueError("no runs")', 'raise ValueError("no runs in " + pathh)', "tab"),
  ("T-TYP-01", "count_becomes_str", "type",
   '"n_included": len(included),', '"n_included": str(len(included)),', "tab"),
  ("T-TST-01", "per_atom_division_dropped", "test",
   'included.append(r["energy_ev"] / r["n_atoms"])', 'included.append(r["energy_ev"])', "tab"),
  ("T-TST-02", "mean_becomes_sum", "test",
   '"mean_energy_per_atom_ev": sum(included) / len(included),',
   '"mean_energy_per_atom_ev": sum(included),', "tab"),
  ("T-TOL-01", "output_key_renamed", "type",
   '"excluded": excluded}', '"skipped": excluded}', "tab"),
  ("T-TOL-02", "exclusions_not_recorded", "toolrun",
   'excluded.append(r["id"]); continue', 'continue', "tab"),
  # ---- review-only: type-safe, test-surviving, semantically wrong ----
  ("T-REV-01", "unconverged_runs_included", "review-only",
   'if not r.get("converged"):', 'if False:', "tab"),
  ("T-REV-02", "zero_atom_guard_inverted", "review-only",
   'if r.get("n_atoms", 0) <= 0:', 'if r.get("n_atoms", 0) < 0:', "tab"),
  ("T-REV-03", "mean_of_means_not_pooled", "review-only",
   'included.append(r["energy_ev"] / r["n_atoms"])',
   'included.append(round(r["energy_ev"] / r["n_atoms"], 1))', "tab"),
]

def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    log = []
    for mid, mclass, channel, old, new, seed in MUTANTS:
        base = SRC[seed]
        assert base.count(old) >= 1, (mid, old)
        src = base.replace(old, new, 1)
        open(os.path.join(outdir, f"{mid}.py"), "w").write(src)
        log.append({"id": mid, "class": mclass, "predicted_channel": channel, "seed": seed})
    json.dump(log, open(os.path.join(outdir, "MUTATION_LOG.json"), "w"), indent=1)
    print(f"{len(log)} mutants written")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mutants")
