# Vibe-paper screen — same-source, and declared as such

**Date** 2026-08-03. **Screen** the operator's LLM-authorship checklist
(S1–S4, F1–F3, T1–T2, L1–L3, plus the four high-risk regions).
**Target** `paper/crossaudit.tex` @ commit `92d841b`.

**Conflict of interest, stated first.** Most of this paper's prose was written
by the same assistant that ran this screen. Under the argument the paper makes,
that is the configuration a supervisor should not be in: the reviewer shares the
author's blind spots by construction. The measurements below are mechanical and
reproducible, which limits the damage; the judgement calls are not, and should
be read as self-assessment. A screen worth trusting would come from a different
vendor, run against the same checklist, with its report committed here.

## Triggered

**S3 — bullets carrying paragraph-weight material.** Three list environments.
§1's contributions (4 items, ~35 words each) is conventional and fine. The other
two are not: §3.2's eight invariants (8 items, ~62 words each) and §5's threat
model (10 items, ~62 words each). Each item is a full paragraph of reasoning
wearing a bullet. The §5 items in particular are causal arguments — threat,
mechanism, residual — laid out in parallel, which is exactly the failure mode the
checklist names.
*Mitigating:* both are reference structures a reader consults rather than reads
through, and §3.2 is duplicated as Table 2 for that reason. But the checklist is
right that the prose has been flattened into a grid.

**T2 — bold on 18 run-in heads.** Eight of them label the roles and are
definitional; ten are §5's threat labels. Combined with 23 `\paragraph` heads,
the document's later sections are a dense sequence of bold run-ins with no
vertical rhythm. Visually the emphasis has stopped emphasising.

**L1 (partial) — `therefore` ×9, semicolons at 8 per 1,000 words.** The
template phrases the checklist names are absent (`it is worth noting` 0,
`this ensures that` 0, `furthermore` 0, `crucially/importantly/notably` 0,
`the fact that` 0, `leverage` 0, `delve` 0). What remains is a real
semicolon habit and a `therefore` reflex, both of which read as machine
connective tissue when they cluster.

## Not triggered, with evidence

**S1.** Intro is 650 words over five substantive paragraphs, opening with two
distinct motivations (agentic systems; the reproducibility record) before the
problem statement. Not one-or-two paragraphs, and the motivation is not abrupt.

**S2.** No mid-paper switch to unmotivated detail. §4.3, added late at the
operator's request, is the one place where that risk was live; it is scoped to
three protocol-level claims and states explicitly that the product line is
evaluated nowhere in the paper.

**S4.** Baseline comparison (Table 1) sits at the end of §2 at char 11,742,
before the protocol at 12,706. Comparison precedes method, which is the correct
order for a position paper; there is no baseline material inside §3 or §4.

**F1.** Every symbol is denoted at first use: vendor $A$ and $B$ in §3.1's first
sentence, round $k$ and report $R_k$ in §3.4's first sentence, $n{=}43$ inside
its own clause. Five symbols total.

**F2.** Zero display equations, 12 inline maths spans, most of them a single
letter or an order term. The fragmentation pattern the checklist describes
requires formulas to fragment; there are none.

**F3.** Zero algorithm environments and zero pseudocode blocks.

**T1.** Naming is stable. `DCL` appears 19 times and is expanded once, 28
characters earlier, at first use. `Constitution` 29, `Generator` 19,
`Auditor` 26 — no abbreviation drift, no competing names for one component.

**L2.** Zero occurrences of `elegant`, `seamless`, `theoretically`,
`effortless`, `cutting-edge`, `paradigm`, `holistic`, `synergy`. `naturally`
does not appear as a flourish.

**L3 — overclaim.** Every capability verb checked in context. `eliminate`
appears twice, both negated ("does not eliminate correlated error"; "reduced,
not eliminated"). `prevent` appears in four places, three of which immediately
bound themselves ("detects a rewrite rather than preventing one"; "miscitation
is caught by the dispute channel, not prevented"). `prove` in the threat model
is a denial ("proves that an exchange occurred; it does not prove the identity").
`guarantee` is used six times, five of them about a guarantee *thinning*,
*dissolving*, or being *out of scope*. The paper's habit runs the other way.

**Related work — hallucinated citations.** All 20 entries were verified against
their source pages the same day; the record is `paper/REFERENCES-AUDIT.md`.
Twenty defined, twenty cited, no orphans in either direction. Three author lists
were corrected, one preprint relabelled. No fabricated entry.

**Appendix.** There is none.

**Figures.** Three, all hand-authored TikZ with 27 bespoke node styles, no
`\includegraphics`, no tool output. This is the opposite of the failure the
checklist screens for.

**Experiment section.** §4.4 uses no bullets. Its motivation is not distorted
in the paper's favour; it opens by stating that the intended experiment failed
and that a cross-vendor audit voided its blinding.

## Verdict

**Risk: low.** Three items trigger, none from the compound the checklist flags
as decisive: S1 clean, F1 clean, F2 not applicable, L1 only partial. No
hallucinated citation. Method detail is legible.

The honest weakness is presentational, not evidential: too much of §3.2 and §5
is laid out as bulleted grids of bold-headed paragraphs. That is a real
readability defect and the checklist is right to catch it.

## Dispositions

1. **§5 threat model → prose.** Convert the ten bulleted items to run-in
   paragraphs. The bullets impose parallel structure on arguments that are not
   parallel. *Accepted, to do.*
2. **§3.2 invariants → keep as a list.** It is a definitional enumeration with a
   companion table, and prose would make it harder to consult, not easier. The
   items should be shortened so each states its guarantee and rationale in two
   or three sentences rather than five. *Partially accepted.*
3. **Semicolons and `therefore`.** Reduce both by roughly half, converting
   semicolon joins to full stops where the two halves stand alone.
   *Accepted, to do.*
4. **Bold.** Leave the eight role definitions; the threat labels lose their bold
   when item 1 converts them to run-in heads. *Follows from 1.*
5. **The screen itself.** Commission the same checklist from a different vendor
   and commit its report beside this one. Until then this file is what the
   paper calls a same-source audit, and it should be read at that discount.
   *Open, operator's call.*
