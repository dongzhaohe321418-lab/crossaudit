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
