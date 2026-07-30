# Redaction rules (Level B preview)

Applied mechanically by script, reproducibly:
1. Scientific magnitudes (all floating-point numbers incl. scientific notation) → ⟨#⟩.
   Integers (finding counts, section numbers) are kept.
2. Full 40/64-hex digests truncated to 12 chars + ellipsis (identity preserved, preimage linkage broken).
3. Everything else verbatim: rule IDs, check IDs, severities, blocked scopes, file paths,
   reproduce-command shapes, timestamps, report structure.

Alternatives: Level A = verbatim (maximum credibility); Level C = structure-only skeleton
(headings, rule IDs, severities; all prose dropped).

## Status note (v6 re-audit, accepted)

The `report_manifest.json` hashes in this mirror are the PRIVATE originals' digests,
truncated by rule 2 — they intentionally match no public blob. This mirror is a
**structural transparency preview** (report structure, rule citations, severities,
blocked scopes, reproduce-command shapes), NOT a hash-verifiable, replayable I2 ledger.
The mechanical redaction script is committed at `tools/redact_mirror.py`; verifiable
public cycles require either publishing originals or committing to redacted-blob hashes
at redaction time (ROADMAP-R2).
