#!/usr/bin/env python3
"""Dead-letter sweep (R2 §7): open an escalation issue for every stuck cycle."""
import json
import subprocess
import sys

import state

for c in state.stuck_cycles(int(sys.argv[1]) if len(sys.argv) > 1 else 21600):
    title = f"CrossAudit dead-letter: cycle {c['cycle_id']} stuck in {c['status']}"
    body = (f"Cycle {c['cycle_id']} (repo {c['repo']}, active {c['active_sha'][:12]}, "
            f"round {c['round']}) has had no state change beyond the threshold. "
            f"Human attention required.")
    subprocess.run(["gh", "issue", "create", "--repo", c["repo"], "--title", title,
                    "--label", "crossaudit-escalation", "--body", body], check=False)
    print("escalated", c["cycle_id"])
