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

