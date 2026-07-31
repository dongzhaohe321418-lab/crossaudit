"""Controller state machine: cycle identity, rounds, escalation lock, admission.

Post-hoc regression tests (finding R5); see conftest.py for why they are not the
uncommitted T1-T3.
"""
from __future__ import annotations

REPO = "owner/science-repo"
SHA_A = "a" * 40
SHA_B = "b" * 40
MAX_ROUNDS = 3


def test_new_commit_opens_a_cycle_at_round_one(state):
    c = state.open_or_advance(REPO, SHA_A, None)
    assert c["round"] == 1
    assert c["status"] == "OPEN"
    assert c["root_sha"] == c["active_sha"] == SHA_A
    assert c["cycle_id"] == state.cycle_id_for(REPO, SHA_A)


def test_same_sha_redispatch_advances_the_round_and_never_rebuilds(state):
    """Behaviour 5: a dispute or re-audit of the same commit is round n+1 of the
    same cycle, not a new cycle. Round derivation follows the commit graph, so a
    nonce file cannot reset it."""
    first = state.open_or_advance(REPO, SHA_A, None)
    again = state.open_or_advance(REPO, SHA_A, None)
    assert again["cycle_id"] == first["cycle_id"]
    assert again["round"] == 2
    assert again["status"] == "OPEN"
    third = state.open_or_advance(REPO, SHA_A, None)
    assert third["round"] == 3


def test_child_commit_advances_the_same_cycle(state):
    c = state.open_or_advance(REPO, SHA_A, None)
    state.record_verdict(c["cycle_id"], SHA_A, "BLOCKED", "r1", MAX_ROUNDS)
    revised = state.open_or_advance(REPO, SHA_B, SHA_A)
    assert revised["cycle_id"] == c["cycle_id"]
    assert revised["round"] == 2
    assert revised["active_sha"] == SHA_B


def test_blocked_at_max_rounds_escalates(state):
    c = state.open_or_advance(REPO, SHA_A, None)
    assert state.record_verdict(c["cycle_id"], SHA_A, "BLOCKED", "r1", 3) == "BLOCKED"
    state.open_or_advance(REPO, SHA_A, None)          # round 2
    state.open_or_advance(REPO, SHA_A, None)          # round 3
    assert state.record_verdict(c["cycle_id"], SHA_A, "BLOCKED", "r3", 3) == "ESCALATED"


def test_dcl_only_verdict_escalates_and_denies_admission(state):
    """Behaviour 1: an offline or model-free cycle is never admissible. DCL_ONLY
    is the verdict the audit script mints when no model audit ran (I8)."""
    c = state.open_or_advance(REPO, SHA_A, None)
    assert state.record_verdict(c["cycle_id"], SHA_A, "DCL_ONLY", "r1", MAX_ROUNDS) == "ESCALATED"
    err = state.admit(c["cycle_id"], SHA_A, "r1")
    assert err is not None and "not PASSED" in err


def test_escalated_cycle_cannot_be_routed_around(state):
    """Behaviour 6: neither a re-push of the same sha nor a child commit may
    bypass an escalated cycle (I8)."""
    c = state.open_or_advance(REPO, SHA_A, None)
    state.record_verdict(c["cycle_id"], SHA_A, "ESCALATE", "r1", MAX_ROUNDS)
    same = state.open_or_advance(REPO, SHA_A, None)
    assert same.get("blocked_by_escalation") is True
    child = state.open_or_advance(REPO, SHA_B, SHA_A)
    assert child.get("blocked_by_escalation") is True
    assert child["cycle_id"] == c["cycle_id"]
    assert child["active_sha"] == SHA_A          # the escalated sha still holds


def test_admit_requires_passed_active_and_matching_receipt(state):
    c = state.open_or_advance(REPO, SHA_A, None)
    cid = c["cycle_id"]
    assert "not PASSED" in state.admit(cid, SHA_A, "receipt-1")     # still OPEN
    state.record_verdict(cid, SHA_A, "PASS", "receipt-1", MAX_ROUNDS)
    assert "stale" in state.admit(cid, SHA_B, "receipt-1")          # wrong sha
    assert "not the cycle's recorded latest receipt" in state.admit(cid, SHA_A, "other")
    assert state.admit(cid, SHA_A, "receipt-1") is None             # admitted
    assert state.admit(cid, SHA_A, "receipt-1") is not None         # consumed


def test_admission_is_single_use(state):
    """Behaviour 3, at the state layer: a receipt admits once. The second attempt
    is refused whichever guard fires first."""
    c = state.open_or_advance(REPO, SHA_A, None)
    state.record_verdict(c["cycle_id"], SHA_A, "PASS", "receipt-1", MAX_ROUNDS)
    assert state.admit(c["cycle_id"], SHA_A, "receipt-1") is None
    replay = state.admit(c["cycle_id"], SHA_A, "receipt-1")
    assert replay is not None
    assert "consumed" in replay or "CONSUMED" in replay


def test_unknown_cycle_is_denied(state):
    assert state.admit("0" * 16, SHA_A, "receipt-1") == "unknown cycle"


def test_stale_verdict_for_superseded_sha_is_ignored(state):
    c = state.open_or_advance(REPO, SHA_A, None)
    state.record_verdict(c["cycle_id"], SHA_A, "BLOCKED", "r1", MAX_ROUNDS)
    state.open_or_advance(REPO, SHA_B, SHA_A)
    assert state.record_verdict(c["cycle_id"], SHA_A, "PASS", "late", MAX_ROUNDS) == "OPEN"
    assert state.admit(c["cycle_id"], SHA_B, "late") is not None
