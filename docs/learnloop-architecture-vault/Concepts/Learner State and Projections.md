---
title: Learner State and Projections
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/learner
  - src/learnloop/substrate/canonical_projection.py
  - src/learnloop/substrate/state_sync.py
tags:
  - learnloop/concept
  - learnloop/learner
  - learnloop/projection
---

# Learner State and Projections

Learner state is a collection of projections with distinct authority, not one mutable profile.

## LO mastery calibration

`learner.mastery` maintains a probability-space EKF over a per-learning-object latent. Item difficulty enters as the IRT observation parameter; coverage, reliability, and assistance govern observation weight. Under canonical versions the filter calibrates predicted performance only and grants no certification credit.

## Canonical facet/capability state

The canonical projection reads immutable observations and assessment contracts into Beta-like evidence state keyed by facet, capability, and optional item scope. It preserves independent evidence mass, raw coverage, last observation/error, consecutive failures, and algorithm version. This is the direct evidence substrate for learner views and certification.

Only criterion observations reach it: a failed criterion's mass goes to that criterion's own targets by the grader's attribution, and an attribution naming a facet no criterion targets changes no belief (KM spec §18, decision 3). From `mvp-0.59` (the facet-belief fixes, kill switch `facet_diagnostic.canonical_belief_fixes`; [the record](../../reviews/refactor-dfb.md)) three bookings changed: a success at or above the failure threshold ends the cell's failure streak; a transfer-tier criterion's mass is `teach_back.transfer_evidence_multiplier` of a core one's, success and failure alike (the Demonstrated timeline applies the same scale); and a total failure books independent and raw coverage on the targets its failure mass lands on. Before it a full-marks answer left the streak standing and a facet failed outright read as unmeasured.

## Facet uncertainty (diagnostic layer)

Per learning object and facet, a hypothesis posterior over the facet being solid, absent or held by a named misconception (`facet_uncertainty`, status open, resolving or resolved). Each attempt updates it from its facet outcomes; the follow-up slate's facet-EIG ranking and overlap gate, goal labels (`known_gap`, `uncertain`), the diagnostic view and the teach-back planner read it through `learner.facet_state_reader.facet_uncertainty_states_for_lo`. Canonical vaults below `mvp-0.59` neither wrote nor read it (KM2b deferred its re-key to KM4, which never shipped it), so all of those readers ran on an empty read. From `mvp-0.59` it is written per learning object on canonical facet ids and rebuilt by learner replay (the table is `DERIVED`); the key stays per LO because replay is per LO and each update's prior is the previous posterior.

## FSRS memory

Item/card state estimates difficulty, stability, retrievability, due time, and last eligible review. It answers when a particular surface should return, not whether a broad learning object is certified.

## Claims and familiarity

Learner claims seed priors and display context. Familiarity records exposure and discounts independence. Neither is direct ability evidence. The first cold observation structurally supersedes a routing prior based on reader interaction.

## Sync versus replay

State sync reconciles authored entities with current heads: create missing item/mastery rows, deactivate removed/retired items, preserve memory across content hash changes, open eligible diagnostic episodes, and run bounded maintenance. Replay reconstructs historical projections from ledgers. They solve different problems.

## Views

Capability grids, facet timelines, residual diagnostics, session diffs, familiarity views, and surfaced beliefs are read models over these projections. Renderers should consume the appropriate reader rather than reaching directly into unrelated tables.

## Modification guidance

- Decide whether a new value is raw authority, a receipt, workflow state, or a reproducible projection.
- Do not let a prediction-only lane leak into certification.
- Add a stable provenance label for displayed inferred values.
- Extend rebuild ownership/golden equivalence for new derived state.
- Use [[Rebuild and Shadow Compare]] for policy experiments.

## Tests

Mastery, capability-grid, canonical projection, facet diagnostics/timeline, familiarity, state-sync, claim, residual, rebuild, and shadow suites.

