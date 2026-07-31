# CLAUDE.md — operating instructions for Claude Code sessions in this repo

You are continuing an established project. Orient from this file first, then
`HANDOFF.md` (session history), then `paper/QUALITY-BACKLOG.md` (open work).

## What this repo is

CrossAudit: a git-native, cross-vendor audit protocol for agentic science.
Position paper (`paper/crossaudit.tex`, 15 pp), reference implementation
(`checks/`, `controller/`, `examples/minimal/`), a registered ablation
programme (`experiment/`), bilingual design docs (`improvements/`), and
workshop submission scaffolds (`paper/submissions/`).

## Standing rules — non-negotiable 长期铁律

1. **Science repos are read-only.** `perovskite-screening` and
   `perovskite-screening-audit` may be cloned and read; never modify them,
   never comment on or alter their scientific content. Process metadata only.
   （科学仓库只读；不得对其中科学内容做任何评论或改动。）
2. **Paper style is frozen.** British spelling; no reintroduction of
   em-dash prose rhythm (file-wide ` --- ` count stays exactly 9: the eight
   invariant labels in §3.2 plus one bibliography title — raised from 8 on
   2026-07-31 when B4 repaired I2's mangled label; CI asserts the number); no
   AI-tell flourishes or new aphorisms; honesty framing everywhere: the
   reference implementation "targets I1–I8, implements a subset". Verify after
   edits: `grep -c ' --- ' paper/crossaudit.tex`.
3. **Experiment red lines** (`experiment/v3/RUNBOOK.md` §8): scoring maps and
   label rules never change after outputs exist (amend via dated AMENDMENT
   sections only); no reading arm outputs before all arms finish; API keys
   never enter the repo; the defect key is sealed before model arms run.
4. **Document precedence.** `experiment/v3-ABLATION-REGISTRATION.md` (+
   amendments) beats `improvements/`; `docs/architecture.md` beats READMEs.
5. **Bilingual parity.** CONTRIBUTING requires zh/en README parity; the zh
   README currently lags (known debt, `ROADMAP-R2.md`).

## Commands

- Paper: `cd paper && pdflatex -interaction=nonstopmode crossaudit.tex` (×2);
  check `grep -cE "^!"` = 0, then page count and ` --- ` count.
- Part C pilot: `cd experiment/v3/partC && python3 -m pytest seed_scripts -q
  && python3 mutate_code.py mutants && python3 code_dcl.py mutants`.
- Ledger mining: `python3 experiment/v3/mine_ledger.py <pv-science> <pv-audit>
  experiment/v3/real-ledger`.
- Workshop skeletons: `cd paper/submissions/neurips2026 && pdflatex
  academia-long.tex` (official `neurips_2026.sty` auto-detected if present).

## Current queue (details in paper/QUALITY-BACKLOG.md)

New lane 2026-08-01 (operator): **installer/packaging**, isolated in
`installer-design/` (operator directive; never mixes with the research
record). Design v1 = 05 + Amendment 1 + 05a there: seven testable
constraints, audit-only 0.2 (one auditor key), wizard 0.3 (gh hard prereq,
plan/--apply, three-state admission honesty), Generator adapter 0.5 (then
the two-key full-loop promise switches on), enforced admission only via
user-owned GitHub App + persistent atomic controller. No PyPI account yet:
distribution is GitHub-direct (tag-pinned git+https, release wheels +
hashes); PyPI deferred. UI and agent-dialog surfaces kept open under the
console iron rule (front-end writes nothing of its own). requires-python
moved to >=3.10.

Lane change 2026-07-31 (operator): **arXiv first; NeurIPS formatting (D2–D5)
deferred**, scaffolds under paper/submissions/ untouched. arXiv materials are
ready in paper/ARXIV.md (single-file source verified, form metadata, condensed
abstract); the upload itself is operator-only (D6), after which Claude back-fills
CITATION.cff and both READMEs with the id. B5/C3/A2+B7/B4/B6 all done
2026-07-31; the paper is 15 pp with Table 2 invariants card and Figure 2
termination walk, ` --- ` count 9. Key-gated: A1/A5 ablation arms (RUNBOOK
stages 0–2), then A3 reframe + C2. Operator-only: arXiv upload (D6), key escrow
choice, blinded adjudication, comma-splice read-through (C1), A4 decision.

Sixth-audit hygiene items (improvements/04): R1–R11 all closed as of
2026-07-31; CI (.github/workflows/ci.yml) now guards the paper build, the
style freeze, the test suite, and the Part C verdicts on every push.

## Credentials

Keys live in `~/.crossaudit-keys.env` (gitignored pattern), or CI secrets.
Any token that has ever appeared in a chat transcript is burned: revoke and
rotate before running model arms. Git push uses the operator's own auth.
