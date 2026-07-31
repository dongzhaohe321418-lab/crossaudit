# Sixth audit (first internal cross-instance) — dispositions

The five previous audits were run by a foreign vendor or by a human relay. This
one was run by a same-vendor instance with no shared context: a fresh clone of
`8389ebd` on a second machine, reading only the repository. It found defects the
authoring sessions could not see, which is the isolation argument of section 4.3
demonstrated on the repository rather than on a corpus. Findings:
`improvements/04-repo-hygiene-and-reproducibility.md`.

Eleven findings, all ACCEPTED. Two are self-inflicted I2 violations by the
authoring session, recorded as such.

## Phase 1 — closed

**R1 — the paper cited `experiment/score_nullcheck.py`, which existed in no
commit.** Cause chain: the fourth audit computed the permutation floors, the
implementation lived only on the machine that ran it and was never pushed, and
the authoring session then wrote it into the paper as a ledger artefact. The
floors were therefore unreproducible in a paper arguing that claims must be
checkable against a committed ledger. Reimplemented from the published null-model
description and rerun: **floors 4.8 / 22.4 / 31.8 of 43** lenient (4.2 / 16.3 /
24.4 strict), κ **.813** same-family vs **.677** cross-vendor at the strict tier,
2000 shuffles, seed 20260731, frozen map. The lost implementation is recovered to
within Monte Carlo noise — 22.4 and both κ land on the previously reported
values; 4.7 and 31.9 move by 0.1 — and the floors are stable across seeds 1, 7
and 20260731 and at 20000 shuffles. Per the standing policy the recomputation
wins and the prose follows: paper, graphical abstract, and QUALITY-BACKLOG now
carry the recomputed values and name the seed; the fourth-audit dispositions
carry an appended supersession note and are otherwise left unedited.
**Sweep: six citation sites, not five** — `paper/crossaudit-abstract-figure.tex`
also encodes the floors as bar rules and was regenerated (`.pdf`, `.png`).
`HANDOFF.md` and `experiment/v3/RUNBOOK.md` name the script without numbers and
are now simply true. The v3 registration is clean; no amendment needed.
Commit `89db3f3`.

**R2 — the Part C channels mis-scored silently when a tool was absent.** The type
channel read a non-zero exit from `python -m mypy` as a kill, so on a machine
without mypy every mutant died there and the review-only residue went to zero
unannounced; the lint channel failed the other way, contributing no kills without
pyflakes. Fixed to the specification set by the cloud session: preflight resolves
and version-stamps every channel tool and aborts with exit 2 naming what is
missing; each channel separates "tool condemned the mutant" from "tool did not
run" (ToolError, and mypy is read by its `error:` output rather than exit
status); a canary runs the four channels against the unmutated seed and aborts if
any fires. The toolchain is written into the kill matrix. Rerun under the pinned
set: kills 1/2/2/1, residue M-REV-01/02/03, **byte-identical to the committed
verdicts** — the pilot result stands, and the harness that produced it can now
say when it cannot. Commit `07fd1cd`.

**R3 — no dependency manifest.** `pyproject.toml` with a `partC` extra, plus
`constraints.txt` pinning the set of record (pyflakes 3.4.0, mypy 2.3.0, pytest
9.1.1, PyYAML 6.0.3 on CPython 3.12.13). Landed before R2 in commit order
because R2's rerun needed the pinned toolchain to exist. Commit `ce55dec`.

**R7 — tracked bytecode, no ignore file.** Commit `1428601`.

## Phase 2 — closed

**R5 — one test file for 2026 LOC.** Forty regression tests under
`controller/tests/`, covering the five behaviours of the ROADMAP-R2 status line
plus the escalation lock and the reply-validator negatives: state machine (cycle
identity, same-sha re-dispatch advancing the round, child-commit advance,
max-rounds escalation, DCL_ONLY refusing admission, escalation lock against both
re-push and child commit, admission requiring PASSED and active and matching
receipt, single use, stale-verdict handling); receipt verifier end to end
against real git trees (PASS admits and consumes, dry run does not consume,
replay denied, and denial for tampered artefact, tampered report, weakened
constitution, altered check layer, ABSENT-but-present manifest entry, non-PASS
verdict, failed integrity, unversioned constitution, missing field, foreign sha,
receipt outside its cycle directory); validator (fabricated rule ids in coverage
and in findings, empty or malformed coverage, PASS with a BLOCKER, BLOCKED
without one, verdicts outside the vocabulary, invalid severities) and the I8
floor, an offline run minting DCL_ONLY rather than a conforming PASS.

Per the operator's three conditions: they live in `controller/tests/`, every file
header states they are post-hoc work written from the current behaviour of the
code, and they are never called T1–T3. The originals ran only inside the session
that wrote them and are unrecoverable — the **third I2 self-violation** this
audit recorded. `ROADMAP-R2.md` and `HANDOFF.md` carry appended supersession
notes pointing at `75f4d6f`; neither claim was edited. Tests run against a copy
of `controller/` in a tmp dir, because `state.py` resolves its store relative to
its own file; one test asserts the repository's state file was never written.
Commits `75f4d6f`, `3e9e2fe`.

**R4 — CI never ran the reference implementation.** `ci.yml`, three jobs, no
secrets, no vendor calls: paper compiles twice with zero error lines and the
style freeze asserted mechanically (` --- ` count must be 8); suite runs under
the pinned toolchain; Part C regenerates the mutants, checks them byte-identical
to the committed set, reruns the four channels and compares the matrix with the
toolchain and canary blocks stripped, per the operator's specification. The
comparison logic was exercised locally against both the identical case and a
seeded drift. Commit `280b90a`.

**R6+R11 — the v1 workflow was still armed.** Moved to
`.github/workflows-archive/` (GitHub runs only `.github/workflows/`, so it is
inert by construction) rather than deleted, since it is the runner that produced
`experiment/results/`. `RUN_TRIGGER` deleted; `experiment/DESIGN.md` carries an
appended note; the archive README records what must be re-pinned before any
rerun, its model defaults being stale against the v3 registration. Commit
`527dd4b`.

## Cross-instance replication (cloud side, 2026-07-31)

The cloud instance re-derived phase 1 independently: `NULLCHECK.json` rewritten
on its machine came out **byte-identical**, and the Part C channels were rerun on
**CPython 3.11.15** against the same pinned tool versions, giving kills 1/2/2/1,
the same three-mutant residue, and a silent canary. The Part C verdicts are
therefore stable across a Python minor version; the only difference falls in the
toolchain block, which is visible rather than silent, and that is what the R2 fix
was for. Recorded here as a data point for Part C's environment sensitivity: it
bounds drift for the interpreter, not for the analysers, whose versions remain
the ones to watch.

## Phase 3 — open

R8 (duplicate and superseded figure exports), R9 (accepted as "do not move";
`experiment/README.md` maps the generations instead), R10 (two missing zh README
sections).

R8 gained one item during phase 2: `e49d801` added `paper/crossaudit.pdf`
alongside `paper/crossaudit-paper.pdf`, byte-for-byte the same build under two
names. Phase 3 should keep one and say in `paper/FIGURES.md` which command
produces it.

## Notes carried forward

- B5 is gated on R1 and the gate is written into `paper/QUALITY-BACKLOG.md`:
  the chance-floor column takes its numbers from
  `experiment/results/NULLCHECK.json`, never from the superseded values.
- For the paper: this audit is usable as a worked instance of contextual
  isolation at the ladder's same-vendor rung — same vendor, no shared context,
  and it caught what the authoring sessions could not. The commits are citable.
