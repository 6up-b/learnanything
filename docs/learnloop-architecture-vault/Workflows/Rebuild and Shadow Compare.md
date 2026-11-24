---
title: Rebuild and Shadow Compare
aliases:
  - Derived State Rebuild Workflow
  - Shadow Rebuild Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/substrate/shadow_rebuild.py
  - src/learnloop/db/table_roles.py
  - src/learnloop/cli/app.py
  - tests/test_rebuild_orchestrator.py
  - tests/test_shadow_rebuild.py
tags:
  - learnloop/workflow
  - learnloop/rebuild
  - learnloop/persistence
  - learnloop/operations
---

# Rebuild and Shadow Compare

Replay reconstructs projections from stored attempts, contracts and other retained inputs. It never asks a model or deletes evidence. [[State and Persistence]] explains table roles and write authority. [[Database Catalog#DERIVED tables|Database Catalog]] lists the clearable tables.

## Compare in a scratch copy

```bash
learnloop rebuild --shadow --json --vault "$VAULT"
learnloop rebuild --shadow --set mastery.irt.eb_difficulty_enabled=true --json --vault "$VAULT"
```

The live database is attached read-only and copied with SQLite backup. The candidate runs on the copy. Repeat `--set` for additional overrides. The report gives the applied overrides, per-replayer accounting, and mastery, facet and schedule differences. Check `live_database.unchanged` and review the individual deltas. Shadow mode never promotes its copy or runs live migrations or state sync.

^shadow-first

## Understand what replay reads

The [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|replayer registry]] gives ownership and dependency order. The activity prerequisite can materialize missing authoritative observations before learner replay. Recurrence groups are rebuilt ahead of the learner fold, canonical facet and capability projections read the completed fold, and identifiability reads the canonical projection. The registry also owns the other clearable families, including router outcomes, adaptive-difficulty state and the source text index.

Replay reads the bounded history prefix for the attempt being applied. Three later activations record inputs the old ledgers could not always recover:

| From | Input replay uses | Older history |
|---|---|---|
| `mvp-0.65` | [[Reference/Database/Tables/attempt_application_order|Application order]] breaks ties between grades stamped in the same second by recorded application sequence. | Keeps the predecessor order with an unknown-order label. |
| `mvp-0.66` | [[Reference/Database/Tables/attempt_lifecycle_inputs|Lifecycle inputs]] give the facet set used at application, so later retirement does not change that application. | Uses a labelled reconstruction from the predecessor's replay. |
| `mvp-0.67` | [[Reference/Database/Tables/mastery_seed_inputs|Mastery seed inputs]] preserve the claims that seeded the first persisted mastery state. | Uses a labelled reconstruction. A starting-level change affects topics created afterwards. |

From `mvp-0.60`, a rebuild uses the newest activity observation for the answer. It adds a raw grade event when the grade changed and a new interpretation when it differs from the current head. An adjudicated, reviewed or quarantined head survives unless a changed grade supersedes it. Earlier supported tags can append a new history chain during rebuild. See [[Algorithm Versions and Reproducibility]] for upgrade and history boundaries.

## Run a live rebuild only when justified

Close vault writers and back up the vault before repairing live derived state. Run [[Doctor Migrations and Recovery|doctor]] before and after.

```bash
learnloop doctor --json --vault "$VAULT"
learnloop rebuild-derived-state --json --vault "$VAULT"
learnloop doctor --json --vault "$VAULT"
```

Repeat `--learning-object` to scope learner replay to selected topics. Shared dependent projections may still need a broader refresh. The result gives the algorithm version, rebuilt topics, replayed attempt count and marker when written. The orchestrator validates replay ownership and attempt coverage and writes the rebuild receipt in the transaction. Unaccounted attempts fail that rebuild.

Inspect a topic with `learnloop show` and use [[Inspect Persistent State]] for its evidence and receipts. Run [[Debug a decision]] first when the only symptom is a surprising choice. Use [[Import Canonical Sources#Resume, cancel, and retry]] for a failed build and [[Process Model Output#Failure handling]] for failed grading.

## Worked drill

[[Recovery and Rebuild Drill]] walks through shadow comparison and the live-repair boundary. Use it alongside [[State and Persistence#Copying and backing up a vault]].
