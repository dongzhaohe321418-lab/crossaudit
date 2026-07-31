# Minimal example: fork-and-run CrossAudit in ~15 minutes

Two repositories, one loop. `science-repo/` is where a Generator pushes
experiment increments; `audit-repo/` holds the Constitution, the deterministic
checks, the Auditor runner, and the report ledger.

## Setup

1. **Create the repos.** Copy `science-repo/` → `you/demo-science` and
   `audit-repo/` → `you/demo-audit` (both with default branch `main`).
   Copy the top-level `checks/` AND `controller/` directories of the main CrossAudit
   repository into the root of `you/demo-audit` (without `controller/` you get
   `cycle_id="no-controller"`, rounds stuck at 1, and no dead-letter source).
2. **Point them at each other.** In `demo-science/crossaudit.yml`, set
   `audit.repo: you/demo-audit`.
3. **Cross-repo token.** Create a fine-grained PAT with `contents: read/write`
   and `actions: write` on both repos; add it as secret
   `CROSSAUDIT_DISPATCH_TOKEN` in **both** repos.
4. **Auditor credentials (optional).** In `demo-audit`, add secret
   `AUDITOR_API_KEY` and repo variable `AUDITOR_MODEL` (any OpenAI-compatible
   endpoint; override `AUDITOR_ENDPOINT` env in the workflow for non-default
   providers). Skip this to run in offline stub mode — deterministic checks
   only, no LLM.

## Run it

**Happy path.** Edit anything under `experiments/2026-07-30-demo/` in
`demo-science` and push. Watch: the science repo dispatches → the audit repo
checks out the exact SHA, runs the deterministic layer, then the Auditor →
a report lands in `demo-audit/reports/` → a `PASS` verdict dispatches back →
the science repo's summary shows the Generator hook point.

**Force a BLOCKER.** In `results.json`, change `"unit": "kcal/mol"` to
`"unit": "banana"` (unknown unit) or delete a `source` field, and push.
The deterministic layer fails, the verdict comes back `BLOCKED`, and the
summary tells the Generator to revise with the trailer
`CrossAudit-Round: 2` on its next commit.

**Force an escalation.** Push a third `BLOCKED` revision (rounds exhaust at
`max_rounds: 3`) — or make `metadata.yml` contradict `results.json` in a way
scripts cannot see but the LLM can, then dispute twice. A GitHub Issue
labelled `crossaudit-escalation` appears in `demo-science`, and the loop
halts for that increment only.

## What to look at afterwards

- `demo-audit/reports/<sha>-round<k>.md` — findings cite rule IDs and the
  Constitution commit hash (invariant I3).
- `git log` in both repos — the entire supervision history as commits
  (invariant I2).
- The workflow summaries — where a real deployment would invoke the
  Generator agent (Claude Code action, queue message, cron pickup…).
  The demo deliberately leaves that hook as a comment: CrossAudit specifies
  the *loop*, not your agent runtime.

## Notes

- The demo experiment data are illustrative, not scientific claims.
- Compute decoupling (I6) is structural: nothing in these workflows touches
  your HPC jobs; verdicts only gate the *next* increment.
- Real deployments should protect `main` on the audit repo (the Generator
  must have no write path to reports or rules) and pin actions by SHA per
  your organisation's policy.
