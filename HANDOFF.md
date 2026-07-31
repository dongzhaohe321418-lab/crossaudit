# HANDOFF — cloud-session digest for continuation (2026-07-31)

Written by the Cowork cloud session that built most of this repo, as the
migration document for local Claude Code sessions. Read `CLAUDE.md` first;
this file is history + first-15-minutes.

## What has been done (chronological, with commits)

1. Protocol + repo bootstrapped: 8 invariants, two-repo reference impl,
   Constitution templates, checks, minimal example, docs, diagrams.
2. Position paper written and hardened through **five external cross-vendor
   audits** (claims → implementation honesty → wiring 6/6 fixed → statistics
   → style); dispositions committed under `audits/`. R2 architecture built:
   controller state machine, full receipt verifier, fail-closed admission,
   locally tested (T1–T3).
3. Seeded-defect trial v1 run three-arm; seal failure caught by audit,
   corrected dual-tier reporting adopted; permutation floors via
   `experiment/score_nullcheck.py`.
4. Figure 1 redesigned twice to the final dense clockwise-ring form
   (`33f91ab`, overlaps eliminated `2a9e4d7`); Table 1 related-work
   comparison (`cd7a0b4`); graphical abstract at paper standard (`baebe35`);
   standalone figure exports (`5a8fd2d`).
5. Discussion gained the packaging (pip) + supervision-console roadmap
   (`4226afd`); WeChat article replaced with operator's rewrite (`df4c65f`).
6. Workshop targets verified (both deadline 2026-08-29): AI-Native Academia
   (Atlanta, 9pp) and Agentic Systems for Molecular Sciences (Paris, 5pp,
   double-blind). Scaffolds + plan: `paper/submissions/` (`36f84ac`).
7. v3 ablation registered and frozen (`98c2f59` + amendments `7a231c2`
   isolation ladder, `2226cc4` Part C code audit): see
   `improvements/` for bilingual expositions (`978f1a1`).
8. Real deployment ledger mined and frozen (`experiment/v3/real-ledger/`):
   7 cycles, decisions BLOCK×5→PASS_WITH_CAVEATS→PASS, findings decay
   7-4-3-2-1-1-0, 12/14 behaviourally confirmed. RUNBOOK: `fb4d0a7`.
9. Part C pilot run key-less end-to-end (`c40ed12`): 9 mutants, deterministic
   channels kill 6, **review-only residue = 3** — the ambiguous stratum is
   real and awaits the LLM ladder.

## Operator actions pending (in the operator's hands only)

1. **Revoke every credential that has appeared in chat** (GitHub PAT, old
   OpenAI key) and mint fresh keys for both vendors into
   `~/.crossaudit-keys.env`.
2. Choose the defect-key escrow route (RUNBOOK stage 0, three options).
3. Download official `neurips_2026.sty` into `paper/submissions/neurips2026/`.
4. Later: 1–2 h blinded adjudication (Part B), comma-splice read-through
   (`paper/reviews/STYLE_DEAI_2026-07-31.md`).

## First 15 minutes in Claude Code

```bash
git clone https://github.com/dongzhaohe321418-lab/crossaudit && cd crossaudit
claude   # reads CLAUDE.md automatically
```
Then say, e.g.: "读 CLAUDE.md 和 HANDOFF.md，按 QUALITY-BACKLOG 推荐顺序
继续：先做 B5 和 C3。" For key-bearing experiment runs, verify
`~/.crossaudit-keys.env` exists first and follow RUNBOOK stages 0–2.

Suggested division of labour: local Claude Code owns key-bearing arm runs and
anything touching your local clones of the perovskite repos; any cloud
session owns paper prose, figures, and submission docs. Both converge through
commits — the ledger, as ever, is the shared memory.
