# Dispositions: annotated external review of 2026-08-05 (Weak Reject, 39 annotations)

Reviewed against the final submitted version (the annotated PDF contains
`twenty-two references` and `paper-v1.0.0`, so every finding is live against
the current text). The reviewer reported 28 factual checks with 4 refuted and
1 inconclusive; each of its checkable claims was re-verified here against the
source, the ledger data, or the arithmetic before any edit was made.

## Verification of the review's claims

Confirmed and fixed in this commit (annotation numbers from the extraction):

| # | Finding | Verified how | Fix |
|---|---|---|---|
| 1 | Title dated July 2026, content runs to 3 Aug | source | date → August 2026 |
| 5 | **Norman citation mischaracterised**: reliability–bias coexistence holds for *two production-deployed judges* of 21, not "across twenty-one judge models" | fetched the source abstract; reviewer right | sentence now states the two-of-21 finding |
| 7 | `machinery;\footnote{…} Our position` — semicolon before a new sentence | source | full stop |
| 9 | "increments, commits under" missing conjunction | source | "and commits them" |
| 10 | DCL sentence strands its verb | source | list parenthesised |
| 11 | Figure 2 strip claims "replayable" against I2's own tiering | source | "parsed supervision record is re-inspectable" |
| 12 | "permissive" mislabels credential isolation | source | "credential" |
| 13 | "is invalid and treated … and escalates" broken coordination | source | serial predicates |
| 15 | Comma splice after "in both directions" | source; our own splice detector missed this shape (long-subject appositive) | colon |
| 16 | **§3.4 self-contradiction on dispute rights** | source: "the Generator … disputes" vs "the Generator may not dispute at all" | disputes are lodged with grounds supplied by the principal; the Generator originates none |
| 17 | "as untrusted hint" + splice | source | article + semicolon |
| 18 | "grades against I3 Second" missing full stop | source; **introduced by our own Major-Revision edit the day before** | full stop |
| 20 | "Since that first cycle … seven cycles" implies eight; ledger has seven including the first | `summary.json`: 7 cycles, decisions list length 7 | "Including that first cycle" |
| 21 | Falling series confounded by backlog→fresh boundary | design fact | confound stated at the series, not only for the second stretch |
| 22 | "Twelve of them cite a single provenance gate" — **a first-freeze (14-finding) sentence stranded in the second-freeze (23-finding) paragraph**, supported by neither snapshot as written | ANALYSIS-B gate table | replaced with the supported statement: 25 of 39 occurrences cite one rule across 16 of 21 cycles |
| 23 | First catch + "fourteen findings that followed" = 15 > 14 distinct | `summary.json`: 14 distinct including the first | "thirteen" |
| 24 | Vendor confounded with harness/sampling, stated late | design fact | confound now stated at the design sentence |
| 25 | Exploratory status not on the results table itself | — | footnote now opens "All figures exploratory: blinding voided…" |
| 27 | Column mixes BLOCKER-finding counts (26) with verdict counts (10/10) | table + footnote | header now "BLOCKER findings on 10 clean" |
| 29 | Chance-corrected agreement unnamed | `score_nullcheck.py` defines it | formula stated inline: (observed−floor)/(43−floor); it is not Cohen's κ, and the review's suggestion to call it κ would itself have been wrong |
| 30 | **"26 to 31" not derivable** | arithmetic: 38−12=26, 41−12=29; 21/24 beyond all 17 | "26 to 29 beyond the registered twelve (21 to 24 beyond the seventeen)" |
| 36 | Training-signal claim ignores its own Goodhart risk | §5's own content | hedged: candidate signal, with the risk named |
| 37 | O(escalations) economics presented as content, unmeasured | text already conceded partly | "hypothesised", with the missing measurement named |
| 39 | "in itself" | source | "in it" |
| 2, 3 | Abstract omits the variant caveat; self-audit not labelled uncontrolled | fair | "closely related variant"; "committed, uncontrolled record" |

Also fixed while in the file: one stray pre-revision arm label
("cross-vendor arm's 10/10") missed by the previous renaming pass.

## Where the reviewer was wrong or partly wrong

Two of its "refuted" checks survive scrutiny in our favour, and one suggestion
would have introduced an error:

1. **[22]'s diagnosis was right but its suggested replacement was wrong**: it
   proposed attaching 33/12 to the scope sentence, which the final text
   already did; the actual defect was the stranded first-freeze sentence
   beside it, which the annotation's anchor brushed but its suggestion did not
   repair. Fixed at the real defect.
2. **[29] suggested "Cohen's κ = 0.81"**. The statistic is not Cohen's kappa;
   it is agreement corrected against each arm's own permutation floor.
   Adopting the suggestion verbatim would have mislabelled a statistic in the
   act of naming it. The fix states the actual formula.
3. **[8]** claims the protocol "cannot be graded above the guarantee it
   defines" — accepted in substance, implemented as a caption-level tier note
   rather than demoting the cell, because I2's parsed-record tier is the
   guarantee the column now names.

## Deferred to the venue version, with reasons

- **[6] positioning against in-toto/SLSA/sigstore/W3C PROV and multi-agent
  debate**: real gap, both external reviews raised it; requires verified
  citations and a paragraph of honest differentiation, queued as the first
  writing task of the venue revision rather than a same-day insertion.
- **[14] soundness/independence/completeness argument for I1–I8**: the right
  ask and a section's worth of work.
- **[33] injection red-team suite, [34] collusion detection procedure**:
  join the registered follow-up study's backlog; the paper already labels
  both as untested defences, which is the honest interim state.
- **[4] anonymisation**: arXiv is not blind; applies to the venue copy.
- **[31] rescoping contributions to "proposal + existence proof"**: the
  revision already moved the abstract and §4.4 most of the way; the
  contributions list itself is venue-version work.
- **[32] enumerate reader-unverifiable claims**: Table 3's evidence column
  and §4.5's discount instruction carry this today; a per-claim audit table
  is venue work.

## Referred to the operator (not ours to decide)

- **[19]/[35]**: whether naming the HPC provider and the perovskite domain
  discloses collaborators' unpublished work, and whether to add a
  venue-style ethics/broader-impacts statement. Both need the human
  principal and the collaborator, not this loop.

## The uncomfortable part, recorded on purpose

Three of the defects fixed here were introduced or missed by this loop in the
last 48 hours: the missing full stop ([18]) came from our own Major-Revision
edit; the stranded first-freeze sentence ([22]) survived our §4.2 units pass;
and the Norman mischaracterisation ([5]) survived a references check that the
contributions statement described in the same breath. Two different external
reviewers have now each caught a citation-accuracy defect that our own
same-source screens missed. That is the paper's thesis, operating on the
paper, for the third time.
