from __future__ import annotations

import hashlib
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v3_runner_loads_amendment_3_rulebook() -> None:
    module = runpy.run_path(str(ROOT / "experiment" / "v3" / "run_rung.py"))
    rules, recorded = module["load_registered_rules"]("full")
    frozen = (ROOT / "experiment" / "v3" / "AUDIT_RULES_scoped.md").read_text()

    assert rules == frozen
    assert recorded == hashlib.sha256(frozen.encode()).hexdigest()
    assert rules != (ROOT / "templates" / "AUDIT_RULES.md").read_text()


def test_v3_bare_rung_has_no_rulebook() -> None:
    module = runpy.run_path(str(ROOT / "experiment" / "v3" / "run_rung.py"))
    assert module["load_registered_rules"]("none") == ("", None)
