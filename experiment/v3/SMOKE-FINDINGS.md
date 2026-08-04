# What a few cents of live calls found

Three smoke runs against a live Anthropic endpoint, twelve increments in all,
before any registered arm exists. Recorded because each round found something
that would have wasted the real run.

## The credentials

Two keys arrived as a screenshot and both failed. The Anthropic endpoint
answered `"API key is invalid."`; the difference from the working key was one
character, a capital `I` read as a lowercase `l`, in each. A 108-character
random string transcribed by eye or by OCR is a coin flip. Keys belong in
repository secrets by copy and paste, with nothing in between.

`api.openai.com` is unreachable from this sandbox at all, so the cross-vendor
rung cannot run here whatever the credential says. CI was already the intended
path for provenance reasons; it is now the only path that works.

## Round one: the runner works, the corpus does not

Three increments, all parsed, rule identifiers cited, `sections_applied`
populated. The runner is sound.

The corpus was not. A clean increment drew three findings, all false, and two
had a common cause: the increment disagreed with its own evidence at the fifth
decimal place, because `results.json` carried a float and `scf.log` printed a
rounded string. An auditor that reports a 2.1e-05 eV discrepancy is not wrong
to notice it. Fixed by deriving the reported value from the printed one.

## Round two: three defects nobody seeded

Four increments. The strongest finding was chemistry we never encoded: the
structure record gave an HF dimer eleven atoms, because the generator drew the
count at random. An auditor that knows an HF dimer has four said so. Also
found: declared input paths that shipped no files, and a threshold declared
without its unit.

None of these were in the defect key. All would have been reported by every
arm, on every clean increment, in the registered run.

## Round three: the runner was hiding the evidence

The clean-set validator found the corpus declaring `geometries/`, `scripts/`
and `envs/` while the auditor received only the files beside `metadata.yml`.
The runner walked one level. The auditor's complaint that declared inputs were
missing was correct, and the fix was in the runner rather than the corpus.

## Where this stops being patchable

After three rounds the clean set still draws findings, and the remaining ones
divide into two kinds that no fourth round closes.

**A synthetic corpus cannot satisfy a rulebook written for real work.** The
geometry files are placeholder atoms, because generating real ones needs real
chemistry. An auditor that reads them says so, correctly. The same is true of
the geometry-provenance rule: the corpus does not model an optimisation
history, so it cannot document one.

**Some findings are auditor calibration, not corpus defects.** The most
persistent is a reported energy in eV beside a log in hartree, flagged as a
mismatch without the conversion being done; the values agree exactly. Another
reads a formatting difference between `4.072310e-07` and `4.07231e-07` as a
numerical discrepancy.

Both kinds are worth measuring. Neither can be measured while they are mixed
together, and a clean increment that draws findings for real reasons makes the
false-block rate a measure of the corpus.

## The decision this leaves, which is the operator's

Two ways out, and the registration has to name one before a corpus is sealed.

1. **Scope the rulebook to the corpus.** Run the study against a named subset
   of rules the synthetic corpus can satisfy, and say so beside every number.
   This is what a decidable acceptance criterion means: a rule the corpus
   cannot satisfy is not decidable against it. Cheap, honest, and narrows what
   the study can claim.
2. **Use real increments.** Draw the corpus from the live deployment's own
   history and mutate those. Expensive, and it entangles the study with the
   science repository the standing rules keep read-only.

Option 1 is what v1 did implicitly and did not say. Saying it is the
improvement. Either way, `validate_clean.py` runs to zero before sealing, and
that gate is now in the pipeline rather than in someone's memory.

---

# Round four, 2026-08-04: the clean set driven to two, and both are the harness

Written after the scoped rulebook was proposed, against the same live endpoint.
Fifty-eight calls in all. The clean set went 15 → 14 → 6 → 2 findings, and the
interesting part is that almost none of the reduction came from the auditor
getting better.

## Four corpus defects, all found by script before a model saw them

The first was already open: `results.json` declared `total_energy`'s source as
`logs/scf.log` while the log shipped at `scf.log`. Three more surfaced once it
was fixed.

- **Bare source paths.** Quantities cited `run_019.py` while the declared input
  was `scripts/run_019.py`. Defect class L4 is *"source script not among
  declared inputs"* — with the clean form also arguably not among them, L4 was
  not distinguishable from clean, and the class would have measured nothing.
  Sources are now `scripts/…` on both sides.
- **`exclusions:` rendered as a bare key**, which parses to null rather than to
  an empty list. An auditor calling the field unset would have been right, on
  clean increments, and class L2's whole signal is a summary admitting dropped
  runs while exclusions is empty.
- **Prose rounded what the record did not.** `SUMMARY.md` printed convergence at
  three significant figures (`3.34e-07`) against a recorded `3.33941e-07`. The
  summary now quotes the record's own digits.
- **The geometry files were chemically fake.** Ten atoms labelled `X` at 0.7 Å
  intervals, under a metadata objective naming a formic acid dimer. The auditor
  reported the contradiction on two clean increments and was entirely right: a
  formic acid dimer contains carbon and oxygen. This is the worst of the four,
  because it is not a formatting nit — it is exactly the class of substantive
  contradiction the study wants measured, sitting on increments labelled clean,
  where it would have scored as a false alarm and inverted the measurement. The
  files now carry the system's real composition, and line 2 states that the
  coordinates are placeholders, so there is nothing left to contradict.

`check_corpus.py` was written after the first of these and would have caught it
and two of the others without a single call: every declared path resolves to a
shipped file, the domain checks draw nothing, and each reported value agrees
with its evidence to the precision both are printed at. It runs green on all
sixty increments, and it fails when deliberately broken, which was tested. This
is I4 turned on the study's own materials — a question a script settles is not
a question to spend a round on.

## The auditor cannot multiply, and this is measurable

`CA-NUM-001` was drafted on 2026-08-04 requiring the Auditor to convert units
and state a tolerance before alleging a numeric disagreement. It complied. The
conversions were then checked against the corpus:

| increment | log (Ha) | record (eV) | auditor's product | auditor's error | true gap |
|---|---|---|---|---|---|
| INC-004 | −133.138803 | −3622.8914 | −3622.8917 | 3.4e-4 | 4.0e-5 |
| INC-005 | −229.629970 | −6248.5498 | −6248.5497 | 5.1e-5 | 4.9e-5 |
| INC-008 | −226.566975 | −6165.2015 | −6165.1996 | **1.8e-3** | 8.8e-5 |
| INC-009 | −218.935907 | −5957.5495 | −5957.5490 | 4.8e-4 | 2.5e-5 |
| INC-019 | −76.524733 | −2082.3441 | −2082.3440 | 4.8e-5 | 5.2e-5 |

Every record agrees with its own log to inside the precision both are printed
at. The Auditor quoted the right constant and read the right inputs, and its
multiplication was wrong by up to twenty times the discrepancy it was weighing.
Its verdicts followed its own error exactly: the two increments it called
contradictory (INC-004, INC-008) are the two where it multiplied worst; the
three it cleared are the three where it happened to multiply well.

So the rule was aimed at the wrong defect. It required disclosure, and the
failure was never omission — the Auditor disclosed a calculation and the
calculation was wrong. `CA-NUM-001` now says arithmetic belongs to the
deterministic channel: state a tolerance, and where establishing a disagreement
takes a conversion, refer the pair for a tool check instead of raising a
BLOCKER on your own sum. After the rewrite the Auditor referred the eV/hartree
pair on 20 of 20 clean increments and alleged nothing — which is the behaviour
asked for, and which also says the tool channel is load-bearing rather than
decorative.

## Nine verdicts of compliance, filed as defects

With `findings` the only array in the reply schema, an auditor told to show its
working wrote the working there. One six-increment run produced nine entries
whose descriptions ended *"these match exactly"*, *"No contradiction found upon
unit conversion"*, *"No finding under CA-DATA-002"*. One contained the words
*"Wait — structure.json IS listed."* Each would have counted as a false alarm
against a clean increment.

Two repairs, and the order matters. `run_rung.py` now offers
`checks_performed` and `referred_to_tools` beside `findings`, worded identically
on every rung — a hygiene instruction present on one rung and absent on another
would make the ladder measure prompt quality rather than isolation. That cut the
rate but did not end it.

The obvious second repair is to read the descriptions and drop the ones that
sound like compliance. That repair is worse than the defect: a prose classifier
nobody validated, firing at different rates on different vendors' phrasing,
would put the filter inside the very comparison the study exists to make. So
each finding now carries a `violated` boolean and `reply_schema.py` partitions
on the boolean alone — false is withdrawn and reported, true or absent is
scored. Absent counts as scored on purpose: a model that omits the field has
withdrawn nothing, and inferring withdrawal from silence is what `CA-META-001`
forbids.

Tested on synthetic arms carrying one withdrawn entry and one referral per
increment: false-block rate 0/20, where the old reader would have returned
20/20. The counts are published per arm rather than discarded — how often an
auditor files an allegation and retracts it in the same breath is a property of
that auditor.

## Where the clean set stands, and what is left

All twenty clean increments, one call each: **eighteen draw nothing**. Two draw
a single entry, and both are the same residual — a `violated: true` finding
whose prose concludes *"This is consistent, not contradictory."* Neither
alleges anything about the corpus.

So the residual clean-set rate is 2/20, 10%, Clopper–Pearson 95% CI [1.2%,
31.7%], and it is attributable to reply discipline rather than to any judgement
about the science. It is a floor under every arm's false-block rate. Because the
contract is worded identically on every rung it should bias the rungs equally
and leave the ladder comparison intact — *should*, and that word is doing work,
because it has been measured on one vendor only.

**This is the open confound and it belongs to the operator.** If reply
discipline differs between vendors, the cross-vendor rung's false-block rate
will differ for reasons that have nothing to do with audit quality, and L5 is
precisely the rung the paper's thesis rests on. `api.openai.com` is unreachable
from this sandbox, so `validate_clean.py` must be run against the OpenAI vendor
in CI before the arms, and the two residual rates reported side by side. If they
differ materially, the false-block comparison across the vendor boundary needs a
stated correction or a stated limitation; it does not need a silent one.

## Status of the changes above

All of it is pre-registration work: no arm outputs exist, so the scorer and the
label rules were still free to move under the red lines in `RUNBOOK.md` §8. They
are not free to move after this. What changed on 2026-08-04, in one list, for
whoever enacts the amendment: the corpus generator (four defects), the reply
schema (`checks_performed`, `referred_to_tools`, `violated`), the reply reader
(`reply_schema.py`, new), the deterministic corpus gate (`check_corpus.py`,
new), and `CA-NUM-001`'s criterion. The scoped rulebook remains a proposal.

The corpus these numbers were measured against has digest
`f97635563ad5410194e5b1026cf5f02f3dedda3bba05fcdde0f4b9489f775b8d` under
`check_corpus.py`'s tree hash, seed 20260804.
