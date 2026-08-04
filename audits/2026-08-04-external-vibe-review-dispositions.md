# Seventh audit — external vibe-paper screen: dispositions

**Reviewer** external, cross-vendor, working from the PDF and the public
repository state. **Verdict** Borderline Reject, leaning Weak Reject; LLM-writing
risk assessed high **with direct evidence**, that evidence being our own
committed self-screen.

We accept the review in full. Nothing below is a defence. Two of its findings
are defects we introduced and then failed to catch in our own audit of the same
artefact, days apart, which is the more useful result of the exercise.

## Accepted and fixed in this commit

| # | Finding | What we did |
|---|---|---|
| 1 | **Bibliographic contamination.** Entry [7] carried both `arXiv:2606.19544` and `arXiv:2306.05685`, the latter belonging to MT-Bench at [6]. | Verified. The stray line was ours: inserting the new entry after [6] split [6]'s trailing arXiv line onto the new item. Removed from [7], restored to [6]. |
| 2 | **"Public and replayable" is false while the repositories are private.** | Verified: both repositories return 403 anonymously. Figure 1's caption and §4.5 now say replayable *by anyone the operator grants access to*, and §4.5 states plainly that the repositories are private at the time of writing, that the claim is about the artefact's form and not its availability, and that a reader who cannot reach them should discount accordingly. |
| 3 | **I2 conflates three different guarantees.** | Rewritten as three named tiers: parsed-record inspectability (held), raw-exchange preservation (not captured), full process replay (unachievable while the calls are stochastic). The invariant now says which tier the reference holds and points at the deployment's two further gaps. |
| 4 | **Protocol, reference, deployment and product line are used interchangeably.** | New Table 3 binds each object to what it is claimed to do, what it is not, and what evidence exists for it. The product line's row reads "Evidence here: none". |
| 5 | **Counterfactual without a control.** "Absent the loop, all twelve would have proceeded downstream unchallenged." | Replaced in both places with the observable: they were detected and closed before the gated downstream action, and this deployment ran no control condition so it cannot say what would have happened otherwise. |
| 6 | **[19] overreads.** Sharma et al. study user-prompted sycophancy, which does not license "closing" an agent-to-agent anchoring channel. | Rewritten. Contextual isolation is now stated as a design precaution, with the citation explicitly labelled as nearest-available rather than supporting evidence. |
| 7 | **Trial framed causally.** "The vendor split is the result"; "vendor heterogeneity produced observably decorrelated readings". | Heading changed to "The two arms read the rulebook differently". The claim now says two *configurations*, run once, cannot separate a vendor effect from prompt, temperature or sampling, and that disagreement is weaker than decorrelation. |
| 8 | **No LLM contribution statement.** | Added before the acknowledgements. It states what the assistant drafted, what the authors verified, that the same assistant ran our internal screen, and that the screen missed the citation defect the external reviewer caught. |
| 9 | **§5 bulleted grid.** | Ten bullets converted to run-in paragraphs. The document now contains no `itemize` at all. |
| 10 | **Semicolons and `therefore`.** | Prose semicolons 73 to 50, `therefore` 9 to 6, and the reviewer-voice self-emphasis ("deserves weight", "worth reporting", "sharpest version") removed. |

## Accepted, done after a challenge

The first version of this file listed four items as outstanding. The operator
asked why they could not be finished, and the answer was that only two of them
were actually blocked.

- **§4.3 shortened**, 852 words to 550, and retitled *What a second
  implementation taught the specification*. All product surface is gone: no
  interface, no CLI, no console. What remains is the three places where a
  second implementation exposed something the specification had left
  underdetermined. The section states in its second sentence that the package
  is measured nowhere in this paper. This was never blocked; it was deferred
  because the section had been added at the operator's request and cutting it
  felt like overreach. Deferring silently was the wrong call: the choice should
  have been surfaced rather than half-made.
- **Figure 1 split.** A new Figure 1 draws separation of powers alone, four
  boxes and the write and read edges between them, and the loop figure keeps
  the cycle. The loop's caption drops the invariant-by-invariant walk and
  points at the body instead. Also not blocked, just unfinished.
- **Artefacts pinned to a commit.** §4.5 now names the commit every statement
  refers to, rather than a moving default branch, which was the second half of
  the reviewer's finding 2 and had been missed.

## Still open, and genuinely blocked

- **Repository visibility and a DOI.** Changing visibility needs administrative
  rights this session does not hold, and the sandbox's GitHub API access is
  scoped to the configured repositories. Operator action. Until it happens, the
  disclosure added under finding 2 stands in place of the claim.
- **The experiment redo.** It needs API credentials from two vendors and a
  third-party escrow decision, neither of which an assistant can produce. The
  design is frozen in `experiment/v3-ABLATION-REGISTRATION.md`; execution is
  what waits.

## What this exercise demonstrated

Our own screen of this manuscript, run three days earlier by the assistant that
wrote it, reported low risk and no hallucinated citations, and specifically
recorded that all twenty references had been verified. It missed a contaminated
entry that the same assistant had introduced in the same session. A
cross-vendor reader found it on first pass.

That is the paper's thesis, demonstrated against the paper. It belongs in the
record whichever way the submission goes.
