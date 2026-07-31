# Part C pilot — deterministic kill matrix (harness validation)

Run 2026-07-31, key-less. Scale: ONE seed script (`convergence_extract.py`,
typed, partially tested by design), 9 deterministic mutants. This validates
the harness and demonstrates the review-only stratum exists; it is NOT the
registered experiment (that needs the full seed set, predictions frozen
before any run, and the mutation log sealed).

| Channel | Kills | Mutants |
|---|---|---|
| syntactic (pyflakes) | 1 | M-SYN-01 undefined name in error branch |
| type (mypy, TypedDict) | 2 | M-TYP-01 float→str; M-TOL-01 output key renamed |
| test (pytest, hand-computed example) | 2 | M-TST-01 unit factor dropped; M-TST-02 step off-by-one |
| toolrun (fixture dry-run + golden contract) | 1 | M-TOL-02 converged flag inverted |
| **review-only residue** | **3** | M-REV-01 boundary `<=`→`<` at tolerance; M-REV-02 default tolerance ×1000; M-REV-03 min-energy instead of last-step |

Pilot readings (to re-test at scale):
1. **The ambiguous stratum is real and constructible**: 3/9 behaviour-changing
   semantic bugs pass lint, types, the test suite, and the output contract.
   These three are precisely what the LLM ladder arms (L1–L5) will face.
2. **Typing moves contract drift left**: adding TypedDict relocated the
   key-rename class from runtime (toolrun) to static analysis (type) —
   protocol-relevant: cheap annotations shrink what models must be trusted with.
3. **Two harness lessons** hit during the pilot and fixed before any model
   arm exists: sandboxed execution (a mutant run must never touch fixtures)
   and dead-code mutation (mutating an unused default proves nothing —
   equivalence checking caught it, which is what it is for).

Reproduce, from a clone with the pinned channel tools installed
(`pip install -c constraints.txt -e '.[partC]'`):
`python3 mutate_code.py mutants && python3 code_dcl.py mutants`.
Without them `code_dcl.py` now aborts at preflight instead of scoring; the
toolchain that produced the matrix above is stamped inside
`deterministic_kill_matrix.json` (finding R2, sixth audit). The table is
unchanged by that fix: under pyflakes 3.4.0 / mypy 2.3.0 / pytest 9.1.1 the
channels kill the same six mutants and leave the same three.
