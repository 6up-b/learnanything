---
title: Algorithm Versions and Reproducibility
aliases:
  - Algorithm Versioning
  - Reproducibility
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/algorithm_versions.py
  - docs/algorithm-change-playbook.md
  - src/learnloop/ops/vault_upgrade.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/substrate/shadow_rebuild.py
tags:
  - learnloop/concept
  - learnloop/algorithm
  - learnloop/reproducibility
---

# Algorithm Versions and Reproducibility

Algorithm versions identify persisted meaning, not package releases.

## Current vocabulary

| Version | Meaning |
|---|---|
| `mvp-0.7` | canonical knowledge-model state and assessment contracts |
| `mvp-0.8` | authority-propagation projection with robust composition/reliability discounting |
| `mvp-0.9` | successor retaining mvp-0.8 projection semantics and adding cross-channel reveal accounting |

Successor sets are explicit so a new version does not accidentally fall back to a legacy projection through an equality check.

## Defaults fingerprint

Omitted configuration defaults are frozen per algorithm version by a CI fingerprint. A minimal vault therefore remains reproducible without writing every default into `learnloop.toml`. Changing a behavior-bearing default requires an explicit version/fingerprint decision.

## Change protocol

1. Decide whether persisted meaning changes; if yes, add an immediate-successor algorithm version.
2. Keep raw ledgers and receipts immutable; append correction/reinterpretation events.
3. Implement an explicit upgrade that prepares candidate projection before atomic config replacement.
4. Update the effective-default fingerprint.
5. Classify new tables and assign derived rebuild ownership.
6. Extend replay-completeness and exact golden rebuild tests.
7. Run a shadow rebuild and inspect mastery/facet/schedule deltas while proving the live hash unchanged.
8. Exercise predecessor-to-successor fixture upgrade, FK checks, doctor, and idempotent second rebuild.

^change-protocol

## Schema versus algorithm version

Migration schema version describes storage shape; algorithm version describes interpretation. A migration may prepare tables for a future algorithm without activating it. An algorithm upgrade may reuse the same schema but rebuild projections under new semantics.

## Compatibility

`learnloop.substrate.compat` is frozen old-vault machinery. A behavior change there requires a separate compatibility decision and historical fixture; it is never incidental cleanup inside an algorithm bump.

## Evaluation

Rebuild equality proves reproducibility, not benefit. Candidate policy needs simulation/prequential metrics, shadow diffs, and explicit owner review. See [[Testing and Invariants#When changing algorithms]].

## Tests

- `tests/test_mvp09_upgrade.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_shadow_rebuild.py`
- default/config fingerprint tests
- historical fixture migration/replay suites

