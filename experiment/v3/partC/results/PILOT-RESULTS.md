# Part C — deterministic kill matrix (harness validation, expanded)

Runs key-less. Reproduce: `python3 mutate_code.py mutants && python3 code_dcl.py mutants`.
Toolchain and canary state are recorded inside `deterministic_kill_matrix.json`;
the canary asserts that no channel condemns either unmutated seed script.

Scale: **2 seed scripts, 18 mutants, 17 valid** (one discarded as
behaviour-preserving by the equivalence gate). This validates the harness and
gives a first estimate of the review-only stratum. It is **not** the registered
experiment, which needs the full seed set, predictions frozen before any run,
and the mutation log sealed with a third party.

| Channel | Kills |
|---|---|
| syntactic (pyflakes) | 2 |
| type (mypy, TypedDict) | 4 |
| test (pytest, hand-computed example) | 4 |
| toolrun (fixture dry-run vs golden contract) | 3 |
| **review-only residue** | **4** |

## The estimate, and its width

| Sample | Review-only | 95% CI (Clopper–Pearson) |
|---|---|---|
| 1 seed script, 9 mutants | 3/9 = 33.3% | [7.5%, 70.1%] |
| **2 seed scripts, 17 mutants** | **4/17 = 23.5%** | **[6.8%, 49.9%]** |

Doubling the sample moved the point estimate down and halved the interval's
width. The interval is still far too wide to carry a claim; what the data
support so far is that the stratum is **non-empty**, which is the premise the
LLM ladder arms need, and nothing sharper.

## Two predictions that failed, and why they are worth keeping

**T-REV-01** (unconverged runs silently included) was predicted review-only and
was killed by the contract dry-run, because the standard fixture happens to
contain an unconverged run, so the exclusion list changed and the output no
longer matched the golden contract. The prediction was wrong for an instructive
reason: **whether a defect is review-only is not a property of the defect. It
is a property of the defect against the deterministic layer someone actually
built, and against the fixtures they happened to choose.** A richer fixture
moves defects leftward out of the model's territory, which is the same effect
typing had on contract drift, and it argues for reporting the stratum against a
named check layer rather than in the abstract.

**T-REV-03** (per-atom means rounded to one decimal) was discarded by the
equivalence gate: on the current fixtures the rounded values are identical to
the unrounded ones, so the mutant changes no behaviour that any channel could
observe. The gate did its job. It is recorded here rather than quietly dropped,
because a discarded mutant is a fixture gap, not a nuisance.

## Standing observation from the first run

Adding TypedDict annotations relocated the output-key-rename class from the
runtime contract check to static typing, in both seed scripts (M-TOL-01 and
T-TOL-01 are both killed by `type`, though both were first predicted `toolrun`).
Cheap annotations shrink what has to be trusted to a model.
