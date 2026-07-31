#!/usr/bin/env python3
"""CrossAudit controller state machine (R2 §1).

State lives in the AUDIT repository (`controller/state.json`) — the Generator has no
write path to it. Full generator/auditor/controller triple-separation would need a
third repository or external store; that residual is documented, not hidden.

One record per logical increment (cycle):
  cycle_id        stable id: sha256(science_repo + root_sha)[:16]
  root_sha        first audited commit of this logical increment
  active_sha      the commit currently under audit / most recently admitted
  parent_receipt  sha256 of the previous round's receipt ("" for round 1)
  round           controller-managed, monotonic per cycle
  status          OPEN | BLOCKED | PASSED | ESCALATED | CONSUMED
  consumed        list of receipt hashes already used for admission (replay guard)

API (all mutations append to history[] for the ledger):
  open_or_advance(repo, sha, parent_sha) -> cycle dict (round assigned here)
  record_verdict(cycle_id, sha, verdict, receipt_hash, max_rounds) -> new status
  admit(cycle_id, receipt_hash) -> None | error  (freshness + replay guard)
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

STATE = Path(__file__).parent / "state.json"


def _load() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"cycles": {}, "history": []}


def _save(s: dict) -> None:
    STATE.write_text(json.dumps(s, indent=2, sort_keys=True))


def _log(s: dict, event: str, **kw) -> None:
    s["history"].append({"t": int(time.time()), "event": event, **kw})


def cycle_id_for(repo: str, root_sha: str) -> str:
    return hashlib.sha256(f"{repo}\n{root_sha}".encode()).hexdigest()[:16]


def open_or_advance(repo: str, sha: str, parent_sha: str | None) -> dict:
    """New root commit -> new cycle at round 1. A commit whose parent is an existing
    cycle's active_sha -> same cycle, next round (a revision). Nonce-file tricks no
    longer reset rounds: identity follows the commit graph, not changed paths."""
    s = _load()
    for cid, c in s["cycles"].items():
        if c["active_sha"] == sha and c["status"] in ("OPEN", "BLOCKED"):
            # Same-sha re-dispatch (dispute/re-audit): ADVANCE, never rebuild.
            c["round"] += 1
            c["status"] = "OPEN"
            _log(s, "readvance_same_sha", cycle=cid, sha=sha, round=c["round"])
            _save(s)
            return c | {"cycle_id": cid}
        if c["active_sha"] == sha and c["status"] == "ESCALATED":
            _log(s, "blocked_by_escalation", cycle=cid, sha=sha)
            _save(s)
            return c | {"cycle_id": cid, "blocked_by_escalation": True}
    for cid, c in s["cycles"].items():
        if parent_sha and c["active_sha"] == parent_sha and c["status"] == "ESCALATED":
            # A child commit cannot route around an escalated cycle (I8).
            _log(s, "blocked_by_escalation", cycle=cid, sha=sha, parent=parent_sha)
            _save(s)
            return c | {"cycle_id": cid, "blocked_by_escalation": True}
        if parent_sha and c["active_sha"] == parent_sha and c["status"] in ("BLOCKED", "OPEN"):
            c["round"] += 1
            c["active_sha"] = sha
            c["status"] = "OPEN"
            _log(s, "advance", cycle=cid, sha=sha, round=c["round"])
            _save(s)
            return c | {"cycle_id": cid}
    cid = cycle_id_for(repo, sha)
    c = {"root_sha": sha, "active_sha": sha, "parent_receipt": "", "round": 1,
         "status": "OPEN", "consumed": [], "repo": repo}
    s["cycles"][cid] = c
    _log(s, "open", cycle=cid, sha=sha)
    _save(s)
    return c | {"cycle_id": cid}


def record_verdict(cycle_id: str, sha: str, verdict: str,
                   receipt_hash: str, max_rounds: int) -> str:
    s = _load()
    c = s["cycles"][cycle_id]
    if c["active_sha"] != sha:
        status = c["status"]  # stale result for a superseded sha: ignore, keep state
        _log(s, "stale_verdict_ignored", cycle=cycle_id, sha=sha, verdict=verdict)
        _save(s)
        return status
    if verdict == "PASS":
        c["status"] = "PASSED"
    elif verdict in ("ESCALATE", "DCL_ONLY"):
        c["status"] = "ESCALATED"
    else:  # BLOCKED
        c["status"] = "ESCALATED" if c["round"] >= max_rounds else "BLOCKED"
    c["parent_receipt"] = receipt_hash
    _log(s, "verdict", cycle=cycle_id, sha=sha, verdict=verdict,
         round=c["round"], status=c["status"], receipt=receipt_hash[:16])
    _save(s)
    return c["status"]


def admit(cycle_id: str, sha: str, receipt_hash: str) -> str | None:
    """Freshness + single-use: a receipt admits only the cycle's CURRENT sha, once."""
    s = _load()
    c = s["cycles"].get(cycle_id)
    if c is None:
        return "unknown cycle"
    if c["status"] != "PASSED":
        return f"cycle status is {c['status']}, not PASSED"
    if c["active_sha"] != sha:
        return f"stale: receipt sha {sha[:12]} != active {c['active_sha'][:12]}"
    if receipt_hash in c["consumed"]:
        return "receipt already consumed (replay)"
    if c["parent_receipt"] != receipt_hash:
        return "receipt is not the cycle's recorded latest receipt"
    c["consumed"].append(receipt_hash)
    c["status"] = "CONSUMED"
    _log(s, "admit", cycle=cycle_id, sha=sha, receipt=receipt_hash[:16])
    _save(s)
    return None


def mark_deadlettered(cycle_id: str, issue_ref: str) -> None:
    s = _load()
    if cycle_id in s["cycles"]:
        s["cycles"][cycle_id]["deadlettered"] = issue_ref
        _log(s, "deadletter", cycle=cycle_id, issue=issue_ref)
        _save(s)


def stuck_cycles(max_age_s: int) -> list[dict]:
    """Cycles OPEN/BLOCKED with no state change for max_age_s — dead-letter feed."""
    s = _load()
    last: dict[str, int] = {}
    for h in s["history"]:
        if "cycle" in h:
            last[h["cycle"]] = h["t"]
    now = int(time.time())
    return [{"cycle_id": cid, **c} for cid, c in s["cycles"].items()
            if c["status"] in ("OPEN", "BLOCKED") and not c.get("deadlettered")
            and now - last.get(cid, now) > max_age_s]


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1]
    if cmd == "open":
        print(json.dumps(open_or_advance(sys.argv[2], sys.argv[3],
                                         sys.argv[4] if len(sys.argv) > 4 else None)))
    elif cmd == "verdict":
        print(record_verdict(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
                             int(sys.argv[6])))
    elif cmd == "admit":
        err = admit(sys.argv[2], sys.argv[3], sys.argv[4])
        print(err or "ADMITTED")
        sys.exit(1 if err else 0)
    elif cmd == "stuck":
        print(json.dumps(stuck_cycles(int(sys.argv[2]))))
