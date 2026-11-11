---
title: ADR-012 Freeze the compatibility substrate
status: compat
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-11-10
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/substrate/compat
  - docs/specs/ARCHITECTURE.md
tags:
  - learnloop/decision
  - learnloop/status/compat
  - learnloop/substrate
---

# ADR-012 Freeze the compatibility substrate

## Context

Old vaults require legacy projection/replay behavior, but extending that code would create two evolving learning systems and make current semantics harder to reason about.

## Decision

Keep `learnloop.substrate.compat` green for historical fixtures but do not add features. Any behavior change requires an explicit compatibility decision and representative old-vault fixture.

## Consequences

- Current development targets canonical packages/versioned projections.
- Compatibility fixes are narrow, fixture-backed, and separately reviewed.
- Legacy tables/modules remain discoverable as COMPAT rather than being mistaken for current policy.

## Enforcement

Compatibility fixtures, replay tests, table roles, architecture status tags, and algorithm playbook. See [[Algorithm Versions and Reproducibility#Compatibility]].

## What the freeze let go (refactor C1, 2026-11-10)

Freezing means nothing new is added, not that nothing goes. `substrate/compat/card_outcome_replay.py` (261 lines) was removed: P1's proof that card psychometrics could later be replayed from the administration and observation ledger with no schema change. No replay, rebuild or upgrade path imported it, it wrote nothing, and the deferred psychometrics model it prepared for was never built. Its tests (`test_event_sufficiency.py`, and part (c) of `test_p2_acceptance`'s replay walk) went with it. The ledger it read is unchanged, so the proof can be rebuilt from git history if the model is built. `substrate_cutover.py` and the rest of `learnloop.substrate.compat` stay; C2 decides `substrate_cutover`, which the parameter registry imports by name. Record: `docs/reviews/refactor-c1.md`.

