# Part C — code-audit pilot harness

Mutation-testing pipeline per registration Amendment 2. Contents:
`seed_scripts/` typed+partially-tested reference script and its test;
`fixtures/` standard + extended inputs and the golden contract;
`mutate_code.py` deterministic mutant registry (the log is the defect key —
sealed before model arms on the real run); `code_dcl.py` the four
deterministic channels in cost order (pyflakes → mypy → pytest → fixture
dry-run vs golden) with behaviour-change equivalence gating on the extended
fixture set; `results/` the kill matrix and pilot notes. The review-only
residue it isolates is the input set for the LLM isolation-ladder arms.
