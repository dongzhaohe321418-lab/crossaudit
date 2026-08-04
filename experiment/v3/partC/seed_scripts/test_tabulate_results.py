# Hand-computed example (CA-CODE-002): two runs, -8.0/4 = -2.0 and -6.0/2 = -3.0,
# mean -2.5 eV/atom. Coverage is deliberately partial: exclusion bookkeeping and
# the output schema are left to the contract dry-run, as in a real project.
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from tabulate_results import tabulate

def test_hand_computed_mean(tmp_path):
    p = tmp_path / "runs.json"
    p.write_text(json.dumps([
        {"id": "a", "energy_ev": -8.0, "n_atoms": 4, "converged": True},
        {"id": "b", "energy_ev": -6.0, "n_atoms": 2, "converged": True}]))
    out = tabulate(str(p))
    assert abs(out["mean_energy_per_atom_ev"] - (-2.5)) < 1e-12
    assert out["n_included"] == 2
