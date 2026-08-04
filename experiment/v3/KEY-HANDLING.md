# Where the keys live, and why not here

The v3 model arms need credentials from two vendors. Twice now those
credentials have arrived in a chat transcript, and both times they were burned
on arrival. The rule that makes them burned is the project's own: a credential
that reaches the ledger is a public credential, and a transcript is a ledger
that neither of us controls.

Rotating and re-sending has an obvious failure mode, which is that it invites
the same path again. So the arms should not run against a key any assistant
has ever seen.

## The intended path

Keys become **GitHub Actions secrets**, and the arms run in CI on the
operator's own account.

1. Revoke the exposed keys at each vendor's console.
2. Mint replacements. Scope them to the minimum the arms need, and set a spend
   cap; the registered run is roughly 420 calls at temperature 0.
3. Add them as repository secrets under Settings, Secrets and variables,
   Actions: `EXP_ANTHROPIC_KEY` and `EXP_OPENAI_KEY`. Pin the model
   identifiers as repository *variables* rather than secrets, since a model ID
   is not a secret and pinning it in the open is part of the provenance:
   `EXP_MODEL_ANTHROPIC`, `EXP_MODEL_OPENAI`.
4. Dispatch the workflow. Nothing is typed anywhere an assistant can read it.

## Why this is better than a sandbox run, not merely safer

The arms produce evidence for a registered study, so where they ran is part of
the record. A CI run on the operator's account leaves a workflow log with
timestamps, a runner identity, the exact commit, and the resolved model IDs,
all attributable and none of it reconstructed after the fact. A run inside an
assistant's ephemeral sandbox leaves the assistant's word for it. For a study
whose whole subject is supervision that a third party can replay, the second
option is the wrong one on its own terms, quite apart from the credentials.

This is the third time this project has found that an operational shortcut
would have quietly violated the property the paper argues for. The first was
the defect key committed in the open. The second was the T1--T3 test runs that
existed only in a session. This is the third, and it is recorded here for the
same reason as the other two.

## What is still outstanding

The credentials are one of two blockers. The other is the **defect-key
escrow** decision, which costs nothing and has not been made:

- a collaborator's private repository, or
- an OSF registration, or
- an encrypted archive held by the second author, password published when the
  arms finish.

Whichever is chosen, the corpus is generated, its key sealed with that third
party, and only then do the arms run. Sealing after a run is not sealing.
