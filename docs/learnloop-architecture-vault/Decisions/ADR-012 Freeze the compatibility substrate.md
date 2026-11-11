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

## What the freeze let go (refactor C1 and C2, 2026-11-10 and 11)

Freezing means nothing new is added, not that nothing goes. `substrate/compat/card_outcome_replay.py` (261 lines) was removed: P1's proof that card psychometrics could later be replayed from the administration and observation ledger with no schema change. No replay, rebuild or upgrade path imported it, it wrote nothing, and the deferred psychometrics model it prepared for was never built. Its tests (`test_event_sufficiency.py`, and part (c) of `test_p2_acceptance`'s replay walk) went with it. The ledger it read is unchanged, so the proof can be rebuilt from git history if the model is built. Record: `docs/reviews/refactor-c1.md`.

Refactor C2 (2026-11-11) removed `substrate/compat/substrate_cutover.py` (720 lines): P1 step 9's dual-write cutover, with its fail-safe lineage writer, deferred-projection rebuild and six ordered gates. Nothing imported it except the parameter registry's module table, which named it for two structural version pins; the live attempt path decides the purpose-adapter cutover in `substrate/administration_adapters.py` (`hot_path_applies_practice_review`), which stays. Its two registry entries and its tests (`test_substrate_cutover.py`, `test_journey6.py`) went with it. `learnloop.substrate.compat` now holds `activity_backfill.py`, and the freeze still applies to it. Record: `docs/reviews/refactor-c2.md`.

