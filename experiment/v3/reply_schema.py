#!/usr/bin/env python3
"""One place where a reply is turned into findings, so every arm is read alike.

Smoke testing on 2026-08-04 found auditors filing verdicts of compliance as
findings -- "these match exactly", "No contradiction found - this is a passed
check, not a finding" -- inside the `findings` array. Adding `checks_performed`
to the prompt cut the rate but did not end it: the instruction is advice, and the
model follows it most of the time.

The obvious repair is to read the prose and drop entries that sound like
compliance. That repair is worse than the defect. A prose filter is a classifier
nobody validated, it fires at different rates on different vendors' phrasing, and
the ladder would then be measuring the filter. So the reply carries a boolean
instead, and this module partitions on the boolean alone:

    violated: true    -> a finding, scored
    violated: false   -> withdrawn by its own author, counted and reported
    absent            -> a finding, scored

The last line is the fail-closed one. A model that omits the field has not
withdrawn anything, and inferring withdrawal from silence is the move `CA-META-001`
exists to forbid. The withdrawn count is reported rather than discarded: how often
an auditor files an allegation and retracts it in the same breath is a property of
that auditor, and the study should publish it, not launder it.
"""
from __future__ import annotations


def partition(parsed: dict | None) -> tuple[list, list]:
    """Return (findings, withdrawn) for one increment's parsed reply."""
    if not parsed:
        return [], []
    out, withdrawn = [], []
    for f in parsed.get("findings") or []:
        if isinstance(f, dict) and f.get("violated") is False:
            withdrawn.append(f)
        else:
            out.append(f)
    return out, withdrawn


def referrals(parsed: dict | None) -> list:
    """Pairs the auditor routed to a deterministic check rather than adjudicating.

    A referral is not an allegation and must never count towards a false-block
    rate; it is the behaviour `CA-NUM-001` asks for.
    """
    if not parsed:
        return []
    r = parsed.get("referred_to_tools") or []
    return list(r) if isinstance(r, list) else [r]
