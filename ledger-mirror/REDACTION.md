# Redaction rules (Level B preview)

Applied mechanically by script, reproducibly:
1. Scientific magnitudes (all floating-point numbers incl. scientific notation) → ⟨#⟩.
   Integers (finding counts, section numbers) are kept.
2. Full 40/64-hex digests truncated to 12 chars + ellipsis (identity preserved, preimage linkage broken).
3. Everything else verbatim: rule IDs, check IDs, severities, blocked scopes, file paths,
   reproduce-command shapes, timestamps, report structure.

Alternatives: Level A = verbatim (maximum credibility); Level C = structure-only skeleton
(headings, rule IDs, severities; all prose dropped).
