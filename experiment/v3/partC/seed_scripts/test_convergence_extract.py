# Hand-computed example (CA-CODE-002): E = -2.0 Ha -> -54.422772491976 eV.
# Coverage is DELIBERATELY partial (realistic): the eV value and step count are
# tested; the converged flag and output schema are covered by the dry-run
# contract check, not here.
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from convergence_extract import summarise

def test_hand_computed_energy(tmp_path):
    log = tmp_path / "scf.log"
    log.write_text("STEP 1 E=-1.9 dE=1e-2\nSTEP 2 E=-2.0 dE=1e-7\n")
    out = summarise(str(log))
    assert abs(out["final_energy_ev"] - (-54.422772491976)) < 1e-9
    assert out["n_steps"] == 2
