# v3: everything that does not need a credential is built

Status 2026-08-04. Four pieces, each exercised end to end against a throwaway
corpus. Nothing here has seen a real key, and none of it has run a model.

| Piece | File | State |
|---|---|---|
| Corpus generator | `generate_corpus_v3.py` | 60 increments, 68 defects, channels 23 script / 22 tool / 23 model. Refuses to write the key inside the repository. |
| Domain-tool channel | `tool_checks.py` | 22 of 22 tool-channel defects caught, no false alarms, on the throwaway corpus. |
| Ladder runner | `run_rung.py` | Parses; fails closed with no credential. Temperature 0, one call per increment, per-input digests, resumable. |
| Frozen scorer | `score_v3.py` | Dry-run on three synthetic arms of known quality recovers the built-in ordering: Cochran Q 24.52 on 2 df, adjacent McNemar under Holm, chance floors, per-channel recall, and a 14/20 false-block rate reported with its exact interval. |
| Sealing | `seal_key.py` | Four custody modes, each recorded with what it is worth. `hash-only` warns that it supports no blinding claim. |
| Dispatch | `.github/workflows/v3-arms.yml` | Manual dispatch only. Refuses to start unless a committed seal exists and the operator can name its digest. |

## The generator found a collision before any model ran

Validating `tool_checks.py` against the throwaway key showed one seeded defect
the tool channel could never catch. T2 makes the SCF log contradict a claim of
convergence; L6 sets that claim to false. Together, L6 removes the very
assertion T2 contradicts, so a check keyed on "claims convergence" cannot fire.
The exclusion list now covers the pair.

This is the same shape as the D1/L4 collision in v1, and it is why the tool
channel is validated against a key before a real corpus is sealed. A collision
found afterwards is a corpus that has to be thrown away.

## Two disciplines that follow from how this was built

**The throwaway corpus is throwaway.** Validation required running checks
against a key, so that key has been seen and its corpus cannot be used. The
real corpus is generated with a different seed and sealed without anyone
reading it. What validation establishes is a property of the generator, which
carries across seeds; what it cannot establish is the blindness of the corpus
it validated on.

**Sealing precedes the arms, and the workflow enforces it.** The dispatch form
asks for the seal's digest and refuses to run if the committed seal disagrees.
This is the RUNBOOK red line moved out of a document and into the machine, for
the same reason \invariant{4} exists: a rule a person has to remember is a rule
that will be forgotten on the day it matters.

## What is left, and who has to do it

1. **Revoke the two keys sent in chat.** They are burned.
2. **Mint replacements, add as repository secrets** `EXP_ANTHROPIC_KEY` and
   `EXP_OPENAI_KEY`. Pin model ids as repository *variables*:
   `EXP_MODEL_ANTHROPIC`, `EXP_MODEL_ANTHROPIC_ALT`, `EXP_MODEL_OPENAI`.
3. **Choose a custody mode** for the defect key: `collaborator`, `osf`, or
   `encrypted`. The fourth, `hash-only`, is available and honest, but it buys
   no blinding claim and the write-up would have to say so beside every number.
4. Then: generate the real corpus, seal it, dispatch the rungs. Steps 1 to 3
   are the only ones an assistant cannot do.

The L1 and L2 rungs need the generating session's transcript, which the corpus
reserves but does not fill. They are driven separately once the fresh-context
rungs are in.
