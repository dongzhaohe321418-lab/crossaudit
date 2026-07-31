# 04 — Repository hygiene and reproducibility | 仓库卫生与可复现性

**EN** — A full-repository audit run on 2026-07-31 from a fresh clone of
`8389ebd` on a second machine (macOS, Python 3.12, TeX Live 2025). Unlike
01–03, which propose new evidence, this document records defects in the
repository *as it stands*: two of them change numbers the paper reports or
will report. Precedence unchanged: where this disagrees with
`experiment/v3-ABLATION-REGISTRATION.md`, the registration wins.

**中文** — 2026-07-31 在第二台机器（macOS / Python 3.12 / TeX Live 2025）
上从 `8389ebd` 全新克隆做的全仓审计。01–03 提出新证据，本文档记录的是
**现有仓库自身的缺陷**：其中两条会改变论文已报告或即将报告的数字。优先级
不变：与注册文档冲突时以注册文档为准。

## Verified healthy 已验证正常

| Check 检查 | Result 结果 |
|---|---|
| `pdflatex crossaudit.tex` ×2 | 0 errors, 14 pp, 0 Overfull/Underfull |
| Style freeze `grep -c ' --- '` | 8 — within the frozen band |
| Secret scan, tree + all 53 commits | clean |
| `checks/run_checks.py` on the demo increment | `PASS`, exit 0 |
| `pytest experiment/v3/partC/seed_scripts` | 1 passed |
| SCORECARD arithmetic (class tables vs headline recalls) | consistent, both maps |

## Findings 发现

Severity: **C** blocks a claim / **H** blocks mechanisation / **M** hygiene.

### R1 (C) — the paper cites a script that has never existed

§4.3 attributes the permutation floors (4.7 / 22.4 / 31.9 of 43) to
`experiment/score_nullcheck.py`. That path is absent from the working tree
**and from every commit**: `git log --all --diff-filter=A -- '*nullcheck*'`
returns nothing. The floors are therefore unreproducible, in a paper whose
thesis is that claims must be checkable against a committed ledger.
This is an I2 violation by the repository against itself.

*Fix*: implement the test to the description already published (2000 shuffles
of the increment→defect map, preserving each arm's output volume and citation
habits), regenerate the three floors, commit script **and** its output JSON.
If the regenerated numbers differ from 4.7 / 22.4 / 31.9, the prose changes —
not the script. **B5 must not run before this**: promoting the floors into
the §4.3 table would harden an unreproducible number into a headline column.

（论文 §4.3 把置换检验地板值归给一个从未在任何 commit 中存在过的脚本；
这些数字目前不可复现。先补脚本、重算、以重算值为准，然后才做 B5。）

### R2 (C) — Part C channels mis-score silently when a tool is missing

`code_dcl.py:44` defines the type channel as `returncode != 0` of
`python3 -m mypy`. With mypy absent the interpreter exits non-zero, so
**every mutant is recorded as "killed by type"**. The lint channel fails the
other way: `"undefined name" in stdout` is simply `False` when pyflakes is
missing, so the channel silently contributes zero kills.

Observed on this machine: the committed matrix (kills 1/2/2/1, **review-only
residue = 3**) reproduces as kills 0/9/0/0, **residue = 0**. The residue is
the measurement target of Part C and the mutation log is its defect key —
an environment difference currently rewrites ground truth without a warning.

*Fix*: a preflight that imports each channel's tool and aborts if any is
missing; record resolved tool versions and interpreter inside
`deterministic_kill_matrix.json`; treat "tool error" as a distinct outcome
from "mutant killed". **Must land before A5 runs**, or the sealed run burns
keys on a harness that cannot be trusted to have measured anything.

（缺少 mypy 时"类型通道"把全部变异体判为击杀，缺少 pyflakes 时静默零击杀；
本机复现得到 9/9 击杀、残差 0，而提交的结果是 6/9、残差 3。上钥匙跑 A5 前
必须先加工具预检与版本记录。）

### R3 (H) — no dependency manifest anywhere

No `requirements.txt`, `pyproject.toml`, `setup.py`, or lockfile. The checks
layer needs PyYAML; Part C needs pyflakes, mypy, pytest; the arms need two
vendor SDKs — all unpinned. R2 is a symptom of this. Also the prerequisite
for the pip-packaging roadmap in §5.

*Fix*: `pyproject.toml` with extras (`checks`, `experiment`, `partC`), plus a
pinned constraints file whose hash is recorded in every result artifact.

### R4 (H) — CI never runs the reference implementation

`.github/workflows/experiment.yml` is the only workflow, and it runs the v1
arms. Nothing in CI executes `checks/`, `controller/`, or the Part C harness.
The repository argues for mechanised precedence and does not mechanise its own.

*Fix*: `ci.yml` on push/PR — pytest, `run_checks.py` over
`examples/minimal/…/2026-07-30-demo`, `verify_receipt.py` over
`ledger-mirror/CYCLE-000001`, and the R2 channel preflight.

### R5 (H) — 2026 LOC of Python, one test file

The only test is `experiment/v3/partC/seed_scripts/test_convergence_extract.py`
(14 lines), which exists as experimental material rather than as coverage.
`checks/` (the I4 precedence layer) and `controller/` (state machine, receipt
verifier, fail-closed admission) have **zero** automated tests, while HANDOFF
records them as "locally tested (T1–T3)" — tests that are not in the repo,
so the claim is exactly the kind that I2 says cannot be recovered afterwards.

*Fix*: land T1–T3 as `tests/`, add one negative test per check failure mode
and per receipt-verifier rejection path.

### R6 (M) — the v1 experiment workflow is still armed

`experiment.yml` triggers on `push` to `main` touching
`experiment/RUN_TRIGGER`, with `secrets.ANTHROPIC_API_KEY` /
`secrets.OPENAI_API_KEY`, `contents: write`, and an auto-commit of raw
outputs. v1 is finished and its results are frozen; an accidental touch spends
keys and appends to a frozen set. Default model pins
(`claude-sonnet-4-5`, `gpt-5.1`) are also stale relative to v3.

*Fix*: `workflow_dispatch` only, with a typed confirmation input; move model
IDs to variables the registration names.

### R7 (M) — bytecode was tracked, no ignore file *(fixed 2026-07-31, uncommitted)*

15 `.pyc` files were tracked and no `.gitignore` existed; `run_checks.py`
writes `checks.json` into whatever directory it is invoked from, including the
repo root. `.gitignore` added (LaTeX rules scoped to `paper/` so that the
`*.log` fixtures under `experiment/v3/partC/fixtures/` stay tracked), bytecode
untracked.

### R8 (M) — duplicate and superseded binaries

`articles/wechat/crossaudit-architecture.png` and `diagrams/architecture.png`
are byte-identical (`md5 c5e0c8c7…`, 438 KB each). Three generations of the
graphical abstract coexist (`crossaudit-graphical-abstract.png`,
`-v2.png` + `-v2.pdf`, `crossaudit-abstract-figure.png` + `.pdf`, ≈1.8 MB).
No `.tex` in the repo uses `\includegraphics` — every figure is TikZ — so none
of these are build inputs; they are exports. Pack size 6.44 MiB.

*Fix*: one current export per figure, delete superseded generations, point the
WeChat article at `diagrams/architecture.png`, and add a short
`paper/FIGURES.md` mapping each `.tex` source to its export.

### R9 (M) — `experiment/` mixes generations

v1 sits at the top level (`corpus/`, `results/`, `score.py`, `run_arm.py`,
`generate_corpus.py`, `defect_key.json`) while v2 and v3 are foldered.
Moving v1 into `experiment/v1/` would rewrite paths the frozen paper cites
(including the R1 path). *Recommendation*: do **not** move; add
`experiment/README.md` mapping generation → directory → status → registration
document. Revisit only if the paper is reworked wholesale.

### R10 (M) — bilingual parity debt, now specific

`README.zh-CN.md` is missing two sections present in `README.md`:
*Repository layout* and *Deployment note: making admission binding*.
CONTRIBUTING requires parity; ROADMAP-R2 already records the debt in general
terms — this pins it to two sections.

### R11 (low) — `experiment/RUN_TRIGGER` becomes dead under R6

A file containing one timestamp, whose only function is the push trigger R6
removes. Delete with R6, or keep with a one-line comment in the workflow.

## Execution plan 执行计划

Ordered by what unblocks what, not by size.

| Phase | Items | Effort | Gate 说明 |
|---|---|---|---|
| 0 *(done)* | R7 | — | `.gitignore` + untrack bytecode, uncommitted |
| 1 — integrity | **R1**, **R2**, R3 | ~4 h | R1 gates B5; R2+R3 gate A5/A1. Nothing else should jump this queue |
| 2 — mechanise | R4, R5, R6 (+R11) | ~5 h | Needs R3's manifest to pin CI |
| 3 — tidy | R8, R9, R10 | ~1.5 h | Independent; safe to batch into one commit each |
| 4 — resume | QUALITY-BACKLOG B5 → C3 → A2+B7 → B4 → B6 → D2 | as scoped | B5 now legitimate because R1 produced the floors |

Commit discipline: one commit per finding, message naming the finding id, so
that the fix ledger for this audit is itself replayable. Phase 1 commits
should carry the regenerated artifacts (floors JSON, kill matrix with tool
versions) rather than prose claims about them.

（执行顺序按"解锁关系"而非工作量排列：R1 解锁 B5，R2+R3 解锁 A5/A1，
第 2 阶段依赖 R3 的依赖清单。每条发现一次提交，提交里带重算产物而非
对产物的文字描述。）
