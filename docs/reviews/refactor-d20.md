# D-20: the approach-map replay test compared two wall-clock stamps

Ledger row D-20. Test: `tests/test_approach_map_replay.py::test_rebuild_and_replay_call_no_model_and_never_read_approach_maps`.

## What differed

The test rebuilds a vault and a copy (with `approach_maps` and `help_assists` dropped) and compares every DERIVED table. When the two
rebuilds straddled a wall-clock second boundary, these columns differed by exactly one second and nothing else did (2 of 30 reproductions
with a per-cell diff, e.g. `2026-11-13T01:46:07Z` vs `2026-11-13T01:46:08Z`):

| table | columns |
|---|---|
| `facet_recall_state` | `updated_at` (both rows) |
| `facet_capability_evidence` | `created_at`, `updated_at` |
| `subject_identifiability_watermarks` | `checked_at` |

No learner-state column (counts, probabilities, stability, evidence values) differed.

## Why

The replayers stamp these columns from `utc_now_iso(clock)` (`clock.py`: `SystemClock` when `clock` is None, second granularity), for
example `Repository.upsert_identifiability_watermark` (`src/learnloop/db/repositories.py:6559`). `rebuild_all_derived_state` already takes
a `clock` and passes it to the replayers (`rebuild_orchestrator.py:685-713`); the test left it None, so each rebuild read the system
clock, and the two usually share a second.

## Fix

The test passes one `FrozenClock` to both rebuilds. No table or row is dropped from the comparison. With the clock fixed the full
per-cell diff is empty, which also shows every writer of the three tables honours the injected clock (no production change).

## Counts (this worktree, test alone, 60 runs each)

Before the change: 10 of 60 failed. After: 0 of 60 failed.
