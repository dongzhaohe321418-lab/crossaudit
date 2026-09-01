# CrossAudit v4 — Stopping, Pause, and Cohort Rules

**Registered:** 2026-09-01
**Status:** prospective; applies before any v4 outcome is inspected.

## 1. No outcome-dependent early stopping

There is no efficacy, harm-direction, or futility stopping based on same/cross
outcomes. No operator may inspect cell results and stop because a hypothesis is
already significant, null, embarrassing, expensive, or “clear enough”. The
only allowed sample-size change is the blinded nuisance-parameter procedure in
`POWER.md`.

## 2. Immediate integrity stop

Stop the affected cohort immediately if any of the following occurs:

1. the defect key, clean/natural gold labels, arm mapping, or attack key becomes
   available to an assigned generator, auditor, adjudicator, or unblinded
   analyst before its authorised reveal;
2. a confirmatory output exists before the registration/freeze manifest is
   externally committed;
3. the task, corpus, prompt, scrubber, Constitution, DCL, tool layer, reply
   schema, matcher, scorer, or analysis code differs from its frozen hash;
4. substantive artefact content is rewritten by the blinding scrubber;
5. a supposedly fresh audit has access to another arm, generation transcript,
   defect-count information, or prior finding;
6. an API credential or protected real-task payload is exposed; or
7. a live science/production repository is modified by a replay or study arm.

Preserve all completed data, label the cohort integrity-stopped, and publish the
cause. Do not repair it in place. A restart is a new cohort with a new freeze.

## 3. Model and provider drift

Pause if the exact model snapshot cannot be verified, an endpoint silently
changes version/behaviour, a provider deprecates the pinned model, or tool access
changes. Do not substitute a “closest” model. Completed outputs remain in their
original cohort; a replacement model begins a separately registered cohort and
cannot fill missing cells of the old one.

Provider identity is the configured endpoint's declared identity unless a
provider-signed attestation exists. Hash-bound receipts must not be described as
cryptographic proof of provider identity.

## 4. Technical failure thresholds

A transport failure may receive at most two byte-identical retries with the
same model snapshot, payload, parameters, and assigned cell. Once any response
bytes have been received, a retry is a new registered repeat, not a technical
retry.

Pause an affected cell when either condition is met:

- more than 5% of its scheduled calls remain technically missing after retries;
  or
- the endpoint is unavailable for 72 consecutive hours during its execution
  window.

Resume only if the original frozen configuration returns. If it does not return
within the pre-frozen study deadline, close the cohort incomplete. Missing cells
cannot be hand-filled or borrowed from a new model.

Invalid, empty, refused, or unparseable model replies are study outcomes, not
transport failures. They remain as escalations under intention-to-audit and do
not trigger a free retry.

## 5. Human adjudication reliability

Before production adjudication, the Gold and Matching Panels complete a blinded
calibration set. Pause that adjudication stream if Krippendorff's alpha is below
0.67 or raw agreement is below 80%. The manual may be clarified without arm
information and a second independent calibration set run.

If the threshold fails twice:

- retain and report all disagreement;
- downgrade exhaustive natural/real defect-recall claims to exploratory;
- continue precision/gate analyses only where a defensible consensus label
  exists; and
- do not reveal arm identities to obtain agreement.

The numerical reliability thresholds themselves do not certify scientific
correctness; they are minimum operability rules.

## 6. Corpus-quality pause

Before auditor dispatch, pause if deterministic preflight or the Gold Panel
finds any purported clean control non-clean. Rebuild/relabel while fully blind
and issue a new corpus commitment.

After dispatch, a newly discovered genuine defect does not justify removal. Use
the nominal-label and corrected-label analyses in `SAP.md`. If more than 5% of
nominal clean controls contain independently confirmed blockers, classify the
clean-validation process as failed and stop confirmatory false-block claims for
that cohort.

## 7. Cost, call, time, and privacy caps

The exact numerical caps are required fields to freeze before dispatch:

- money and currency;
- calls overall and by module;
- input/output tokens;
- wall-clock deadline;
- human-review hours; and
- protected-data exposure policy.

At a cap, finish no new call; preserve the current block boundary where safe,
and close the cohort incomplete. Power, favourable preliminary results, or sunk
cost do not authorise an overrun. A cap may be increased only before any v4
output exists; after that, additional resources require a new cohort.

Stop immediately on protected-data egress outside the frozen provider/privacy
policy. Notify the responsible operator under the applicable incident process;
do not commit exposed payloads to the public ledger.

## 8. Randomisation and balance checks

The randomiser validates complete required cells before execution. Pause before
calls if counts are unequal outside pre-specified blocks, any task lacks both
same and cross assignments, a vendor direction is missing, or the ablation
subset is not prospectively selected.

Realised imbalance caused by technical missingness is reported and handled by
the SAP. It is not repaired after outcomes by deleting observations from larger
cells.

## 9. Stop records

Every pause/stop record must include:

```yaml
event_id: STOP-...
timestamp_utc: ...
cohort_id: ...
trigger_rule: ...
detected_by: ...
affected_cells: [...]
outputs_existed: true|false
arm_outcomes_visible_to_decider: true|false
action: pause|integrity_stop|close_incomplete|new_cohort
evidence_sha256: ...
resolution: ...
```

The record is committed before any resume or replacement cohort. A stopped
study reports stopped; it does not disappear.
