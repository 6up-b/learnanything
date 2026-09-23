---
title: "Rebuild Ownership"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
schema_head: 165
source_commit: "e1153c01d0c6e29e6c4f97f1f4fa1e5214914f73"
source_commit_timestamp: "2026-09-23T18:50:00-04:00"
last_verified: "2026-09-23"
aliases:
  - "Derived state rebuild"
  - "DERIVED_STATE_REPLAYERS"
source_paths:
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/substrate/replay.py"
  - "src/learnloop/substrate/canonical_projection.py"
  - "src/learnloop/substrate/shadow_rebuild.py"
  - "src/learnloop/db/scopes.py"
  - "src/learnloop/db/connection.py"
  - "src/learnloop/db/checkpoint.py"
  - "src/learnloop/goals/exam_seeding.py"
  - "tests/test_rebuild_orchestrator.py"
  - "tests/test_shadow_rebuild.py"
tags:
  - "learnloop/database/rebuild"
  - "learnloop/database/derived"
  - "learnloop/status/active"
---

# Rebuild Ownership

The rebuild umbrella provides one ordered, lossless route from preserved history to every table marked `DERIVED`. Registry validation runs before the first write, every raw attempt must be accounted for, and a successful live rebuild appends exactly one [[Reference/Database/Tables/derived_state_rebuilds|derived_state_rebuilds]] receipt. ^rebuild-contract

```mermaid
flowchart LR
    Raw[(RAW ledgers)] --> AS[activity_substrate prerequisite]
    AS --> LS[learning_state]
    LS --> CP[canonical_projection]
    CP --> ID[identifiability]
    LS --> R[(one rebuild receipt)]
    CP --> R
    ID --> R
```

This order is difficult to infer from table names: activity backfill creates authoritative replay input but owns no derived table; canonical facet projection consumes the complete replayed learning state; identifiability consumes the canonical projection.

## Owner registry

### `activity_substrate` prerequisite

Owns no `DERIVED` table. It backfills missing authoritative activity observations before replay so all raw attempts can be accounted for.

### `learning_state`

- [[Reference/Database/Tables/ability_transition_events|ability_transition_events]]
- [[Reference/Database/Tables/attempt_surprise|attempt_surprise]]
- [[Reference/Database/Tables/item_parameter_state|item_parameter_state]]
- [[Reference/Database/Tables/learning_object_mastery|learning_object_mastery]]
- [[Reference/Database/Tables/learning_outcome_labels|learning_outcome_labels]]
- [[Reference/Database/Tables/practice_item_quality_state|practice_item_quality_state]]

It clears the whole family for a whole-vault rebuild, replays persisted attempts, and recreates cold mastery rows for authored learning objects with no attempt history.

### `canonical_projection`

- [[Reference/Database/Tables/capability_residual_state|capability_residual_state]]
- [[Reference/Database/Tables/facet_capability_evidence|facet_capability_evidence]]
- [[Reference/Database/Tables/facet_recall_state|facet_recall_state]]

It projects canonical facet/capability state after learning-state replay is complete.

### `identifiability`

- [[Reference/Database/Tables/subject_identifiability_watermarks|subject_identifiability_watermarks]]

It recomputes subject-level identifiability findings from the canonical projection.

## Correctness oracles

`tests/test_rebuild_orchestrator.py` pins four properties:

1. every `DERIVED` table has exactly one owner and no non-derived table is claimed;
2. every scoped raw attempt is reported as accounted for;
3. a same-version rebuild reproduces every column exactly, including IDs and timestamps;
4. one planted stale row in each derived table disappears, while preserved roles remain unchanged and exactly one receipt is appended.

> [!important] Rebuild does not call AI providers
> Provider outputs needed for replay are retained in raw grading/source ledgers. Rebuild changes computation over stored evidence; it does not regenerate history. Provider design details live in [[AI Architecture]].

## Live rebuild

```bash
learnloop rebuild-derived-state --vault /path/to/vault --json
```

This command synchronizes authored vault state, mutates the ten live projections, validates attempt coverage, and writes one receipt. `--learning-object` may scope learning-object work, but callers should understand the projection dependencies before using a partial rebuild.

`rebuild_all_derived_state` is an `@atomic_repository_call`: every replayer's writes and the receipt run inside one `BEGIN IMMEDIATE` transaction (nested repository writes join it as savepoints), so a replay or completeness failure rolls back and leaves the published projections untouched. The transaction holds the database write lock for the whole rebuild, which serializes it with every other writer.

> [!note] Readers keep reading during a live rebuild
> The database runs in WAL mode (see [[ADR-015 SQLite runs in WAL mode with synchronous FULL]]). Readers keep the last committed snapshot for the whole rebuild transaction and see the new projections once it commits. On a copy of `fixtures/linear_algebra` (a 46 MB database, production connection settings, a reader polling every 1 ms, three consecutive rebuilds of about 0.78 s each), the longest gap between successful reads was 0.011–0.013 s. That gap is the reader thread waiting for Python's interpreter lock in the same process, not a database lock. Under the rollback journal the same measurement blacked readers out for 0.20–0.47 s per rebuild. A second writer still waits for the rebuild's write lock, and gives up with `database is locked` after the 5 s `busy_timeout`.

`learnloop rebuild-derived-state` calls `rebuild_live_derived_state`, which runs the umbrella and then a best-effort `TRUNCATE` checkpoint. The three rebuilds above grew the `-wal` to 7.2 MB, and the checkpoint emptied it in 17 ms.

Other replay entry points:

- `replay.record_content_recalibration` (content apply inside an ingest job) replays the affected learning objects inside `repository.atomic()`, so the ingest lease cannot change hands between clearing an LO's derived rows and re-folding them, and a failure publishes nothing.
- `goals.exam_seeding.seed_exam_attempts` calls `replay.rebuild_derived_state` directly for the learning objects it seeded, without its own transaction scope, so that replay commits per repository call.

## Shadow rebuild

```bash
learnloop rebuild --shadow \
  --set algorithms.algorithm_version=mvp-0.9 \
  --set mastery.base_observation_variance=2.0 \
  --vault /path/to/vault \
  --json
```

Shadow mode:

- attaches the live database read-only;
- records a SHA-256 of the database file followed by its `-wal` before work, because committed pages can still be in the `-wal`;
- copies it with SQLite's backup API into a temporary database;
- validates dotted config overrides against the typed configuration;
- runs the ordinary umbrella on the scratch copy;
- reports semantic mastery/facet/schedule deltas;
- verifies the live database hash again and writes no live receipt.

> [!tip] Preferred algorithm-change workflow
> Use shadow rebuild to inspect consequences before changing `learnloop.toml` or running the live rebuild. See [[Learning System]] for algorithm intent and `docs/algorithm-change-playbook.md` for the repository playbook.

## Extension guidance

A new projection family must declare its owned tables, dependencies, runner, row accounting, and deterministic test oracle in `rebuild_orchestrator.py`. Do not classify captured calibration artifacts or mixed authoritative rows as `DERIVED` merely to simplify cleanup.
