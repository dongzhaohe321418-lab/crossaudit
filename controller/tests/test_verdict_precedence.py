"""Verdict-synthesis precedence, pinned after two external reviews found the gap.

The combined case is the one that matters: a DCL hard failure AND an invalid
auditor reply used to synthesise BLOCKED, absorbing the integrity failure into
an ordinary scientific verdict. I3 says an invalid audit escalates, full stop;
the reviews of 2026-08-05 both flagged that the implementation and Table 2
disagreed with the invariant. The precedence now lives in one pure function,
and this file is the regression test the fix ships with.
"""
from __future__ import annotations

import importlib.util
import sys

import pytest

from conftest import REPO as REPO_ROOT

AUDIT_SCRIPT = REPO_ROOT / "examples/minimal/audit-repo/scripts/run_llm_audit.py"


@pytest.fixture(scope="module")
def audit_mod():
    spec = importlib.util.spec_from_file_location("run_llm_audit_vp", AUDIT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def v(mod, **kw):
    args = dict(escalation_lock=False, llm_invalid=None, dcl_hard_failures=0,
                bounds_exceeded=0, llm_reply=None)
    args.update(kw)
    return mod.synthesise_verdict(**args)


def test_the_combined_case_escalates(audit_mod):
    """DCL hard failure + invalid reply -> ESCALATE, never BLOCKED (I3 over I4)."""
    got = v(audit_mod, llm_invalid="no sections_applied", dcl_hard_failures=3)
    assert got == "ESCALATE"


def test_invalid_reply_alone_escalates(audit_mod):
    assert v(audit_mod, llm_invalid="fabricated rule id") == "ESCALATE"


def test_i4_is_untouched_by_the_swap(audit_mod):
    """A VALID model PASS still cannot waive a DCL hard failure."""
    got = v(audit_mod, dcl_hard_failures=1, llm_reply={"verdict": "PASS"})
    assert got == "BLOCKED"


def test_escalation_lock_outranks_everything(audit_mod):
    got = v(audit_mod, escalation_lock=True, llm_invalid="x", dcl_hard_failures=9)
    assert got == "ESCALATE"


def test_truncated_inputs_cannot_mint_pass(audit_mod):
    got = v(audit_mod, bounds_exceeded=2, llm_reply={"verdict": "PASS"})
    assert got == "ESCALATE"


def test_offline_floor_is_dcl_only(audit_mod):
    assert v(audit_mod) == "DCL_ONLY"


def test_clean_valid_reply_passes_through(audit_mod):
    assert v(audit_mod, llm_reply={"verdict": "PASS"}) == "PASS"
    assert v(audit_mod, llm_reply={"verdict": "BLOCKED"}) == "BLOCKED"
