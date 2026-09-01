# CrossAudit v5: top-conference confirmatory package

This directory is a **prospective, pre-results design package**.  It does not
amend the registered v4 study or combine with the sealed six-task v4
feasibility cohort.  The separation is intentional: v4 established that the
measurement and evidence-sealing machinery can execute; v5 is designed to test
whether heterogeneous audit assignment improves outcomes.

## Scientific question

> Under fixed information, budget, and controller rules, when does a more
> heterogeneous auditor improve final gate correctness without an unacceptable
> increase in clean-artifact burden?

`vendor` is an assignment factor, not a synonym for independence.  The design
separates same-model, same-vendor/different-model, and cross-vendor review and
restricts inference to the included, pinned configurations.

## Minimum design

- 150 independent task briefs, with one blinded expansion to at most 180;
- three domains and at least 60 real-task or repository replays;
- three vendors in a complete 3 x 3 primary Generator x Auditor matrix;
- six pinned model snapshots, including one same-vendor/different-model auditor
  baseline per vendor;
- natural output plus verified-clean/exactly-one-mutant controlled siblings;
- three fresh-context audit repeats in every required cell;
- two independent domain reviewers and a third adjudicator;
- C0/C1/C2 Constitution cells all run with three repeats; and
- paired whole-loop branches on a prospectively sampled 60-task subset.

The planned ceiling is 24,930 model calls before any separately authorised
technical retries.  This is a design ceiling, not permission to spend.  The
preflight remains blocked until model identities, monetary and token caps,
human-review capacity, provider-egress approval, randomisation commitments, and
panel manifests are filled and hash-locked.

## Files

- `REGISTRATION-DRAFT.md`: claims, design, stopping rules, and go/no-go gates.
- `SAP-DRAFT.md`: estimands, inference, multiplicity, and missingness.
- `POWER.md`: exact-allocation simulation requirements.
- `config/study.yaml`: machine-readable design and unresolved freeze fields.
- `power_simulation.py`: task/base-artifact/repeat clustered power simulator.
- `preflight.py`: outcome-free refusal checks for the design freeze.

## Safe workflow

```bash
python experiment/v5/preflight.py experiment/v5/config/study.yaml
python experiment/v5/power_simulation.py --scenario central --simulations 10000 \
  --output experiment/v5/power-central.json
```

The first command is expected to return `BLOCKED` until the operational fields
are deliberately completed.  No provider dispatch code is included here.
