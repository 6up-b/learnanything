# Adaptive hints H1: Codex review

Stage `hints-h1`, branch `hints/h1`, worktree `learnanything-merge4`, reviewed
at `262d5dc26` (Codex job `20261018-023953-U3XWgU`). This round had five
Mediums and no High or Low.

## Review round 1

Each finding was reproduced first, with a pure validator call or with fakes
on a temporary vault. All 14 new tests in `tests/test_approach_maps.py`
(section "Codex review of H1") fail on `262d5dc26`. I checked the failure
reasons by restoring the three pre-fix modules from `HEAD` for that run and
then putting the fixed ones back. No `git stash` was used. On the old code:

- F1: the leaking map is valid.
- F2: the contradictory goal is valid. It is `verified_goal=True` with a
  correct declaration and unverified with an empty one.
- F4: the reference-only map is valid.
- F5: the two structure hashes are identical.
- F3: the second OS process's serve build returns `('built', 1)`, so it pays
  again.

No model calls were made, live or paid. Fakes only. No vault copy was used.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Single-digit answers bypass map leak validation | fixed | 8be57141d | `test_f1_a_single_digit_answer_marks_its_node_and_fails_a_label_that_states_it`, `test_f1_a_single_digit_vault_item_builds_with_its_leaks_marked` |
| F2 | Medium | A correct auxiliary answer verifies a contradictory goal node | fixed | 8be57141d | `test_f2_a_goal_state_that_contradicts_the_answer_is_a_mismatch[1/4]`, `[]` (empty declaration), `test_f2_the_goal_verifies_from_an_agreeing_state_or_declaration` |
| F3 | Medium | Concurrent processes can supersede a newer map with stale content | fixed | 8be57141d | `test_f3_a_stale_merge_never_supersedes_a_newer_map` (Codex's completion order), `test_f3_a_slower_initial_build_with_other_seeds_does_not_land_a_second_map`, `test_f3_the_durable_claim_keeps_a_second_worker_from_paying`, `test_f3_a_lapsed_claim_of_a_dead_process_is_taken_over_and_fences_its_commit`, `test_f3_a_second_os_process_never_pays_for_an_item_in_flight` (durability; two OS processes, spawn) |
| F4 | Medium | Initial builds can permanently discard seeded learner-route assignments | fixed | 8be57141d | `test_f4_every_seeded_solution_needs_exactly_one_route`, `test_f4_only_a_route_assignment_counts_as_mined`, `test_f4_a_seeded_but_unrouted_attempt_is_merged_later` |
| F5 | Medium | Changing an inherited rubric leaves the old map current | fixed | 8be57141d | `test_f5_an_inherited_rubric_change_is_a_new_revision` |

### What changed

- **F1** (`hints/maps.py`). `gives_away` now also matches a lone-digit exact
  key (an optional sign and one digit) as its own number token. It is never
  matched inside `14`, `3/4`, `4.5`, `x_4` or `2^4`. Node leak marking and
  the label check both go through `gives_away`, so a node whose state is `4`
  is code-marked as a leak, and a label like "The count is 4" fails
  `label_leak`. As before, a label that the answer check flags is not exempt
  just because the question states the value. The same is true for keys of
  two or more characters.
- **F2** (`hints/maps.py`). `goal_agreement` now checks two things against
  the key: the declaration, and the goal node's own conclusion (`exact_key`
  of its state, for example "Therefore P = 3/4" -> `3/4`). If either one
  decidably differs from the key, the result is `goal_mismatch`. This check
  runs before anything is verified, and the mismatch detail names its basis
  (`exact_key` or `goal_state`). An empty declaration no longer lets a wrong
  state through. A state that concludes the right value can now verify a map
  with an empty declaration.
- **F3** (`hints/map_builder.py`). Builds and merges now take a durable
  per-item claim through the shared `judgment_work_claims` machinery. This
  is the same pattern as `source_exercise_import`'s key-check claim:
  - The key is `approach_map_build:<item id>`, with a 120 s lease and a 30 s
    heartbeat. The claim is released at the end and lapses if its process
    dies.
  - The claim is taken only when a build or merge is due. A serve whose map
    is current makes no write.
  - When another process holds the claim, a serve answers `busy` at once.
    Inline builds and merges wait until their deadline, and the CLI waits
    until the claim is free. After claiming, the builder reads again and
    returns `current` when the map landed meanwhile.
  - `_store` is fenced inside its BEGIN IMMEDIATE transaction. It stores
    only while this worker's lease holds. A build stores nothing when its
    revision already has a map: another process's seeds may differ, so the
    UNIQUE seeds key alone would let both land. A merge stores only when its
    base map is still the item's newest row. Otherwise it returns `stale`
    and stores nothing. Its attempts stay unmined, so the next merge places
    them.
  - `stale` is a new `MapOutcome` status.
  - Schema unchanged: `judgment_work_claims` already exists (migration 176,
    WORKFLOW).
- **F4** (`hints/maps.py`, `hints/map_builder.py`). There is a new
  validation reason, `unplaced_attempt`: every seeded learner solution must
  be on exactly one route. Missing and duplicated placements are both
  rejected, as merges already required. Initial builds are re-asked once and
  then not stored. `_known_attempts` now counts only route assignments, not
  `seeds.attempts`. So an attempt that was seeded but never routed (the
  shape F4 found accepted) is placed by the next merge. Its seeds record is
  de-duplicated.
- **F5** (`hints/map_seeds.py`). A new `rubric_seed(vault, item)` returns the
  rubric the builder reads: the item's own, or else its practice mode's
  default. `structure_hash(item, skeletons, rubric)` now covers it, through
  both `item_revision` (the cheap serve-side key) and `MapSeeds`, so
  `seeds_hash` covers it too. When an inherited rubric changes, the item has
  a new revision: no current map, and a new row with `supersedes_id`.

### Limits and notes

- **F1.** The lone-digit match leans toward marking. A given node that
  restates the digit is marked as a leak. That only restricts what H2 may
  reveal. A label holding the digit for another reason (for example "Step
  4") fails and is re-asked. Labels are meant to carry no values anyway.
- **F2.** The state's conclusion is read the way `reference_final_answer`
  reads a reference: only a numeric last-sentence conclusion or an equal
  numeric chain. A state that does not end in such a conclusion stays
  undecidable and is judged by the declaration, as before.
- **F3 cross-process wait.** A CLI build waiting on another process can wait
  as long as that process's build takes. A dead holder's lease lapses within
  120 s.
- **Docs.** `docs/reviews/adaptive-hints-H1.md` §1.1 and §1.3 now describe
  the fixed behaviour. The comment in `migrations/211_approach_maps.sql`
  about what `structure_hash` covers was left as written, because the
  migration and its head fixture are fixed. This document and the H1 doc
  record the rubric addition.
- **Claims that don't hold.** The review's "Claims that don't hold" list is
  answered by F1, F2, F3 and F5 above.
- **G-H11 duplicate paid work** across processes is closed by the claim
  (F3).

### Gate (this step; targeted, per the owner rule of 2026-10-17)

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`. Both
  ran with `TMPDIR` set to the worktree's `fixtures-local/tmp`.
- `uv run lint-imports --no-cache`: 26 kept, 0 broken.
- `uv run pytest -n auto` over the following 16 files: **268 passed**.
  - `tests/test_approach_maps.py`
  - `tests/test_approach_map_boundaries.py`
  - `tests/test_approach_map_replay.py`
  - `tests/test_approach_maps_schema.py`
  - `tests/test_architecture.py`
  - `tests/test_help_assists_schema.py`
  - `tests/test_judge_routes.py`
  - `tests/test_library_asks_migration.py`
  - `tests/test_reader_active_reading.py`
  - `tests/test_reader_formative_texts.py`
  - `tests/test_reader_passage_check.py`
  - `tests/test_recurrence_merge_composition.py`
  - `tests/test_hint_telemetry.py`
  - `tests/test_table_roles.py`
  - `tests/test_coordinated_migrations.py`
  - `tests/test_tracked_fixture_databases.py`
- `uv run pytest -m durability` over the four approach-map test files: **2
  passed**. These are the schema durability test and the new two-process F3
  test.
- `uv run pytest -n auto --durable-sqlite tests/test_approach_maps.py`: **65
  passed**. The claim, its heartbeat and the fenced commits all ran under
  production WAL and `synchronous=FULL`.
- The 14 new tests were rerun 3 times with `-n 4`: 14 passed each time. The
  threaded tests order their workers with gates. The only waits are the
  0.3 s merge deadline and the OS-process test's 1 s polling pause.
- Not run, because nothing they cover changed:
  - schema, migration, head fixture and DB references (no schema change);
  - config defaults, CLI help, serializer and RPC pins;
  - the frontend and cargo (no `apps/` change).
- The full suite, the whole durability lane and the whole vitest run are
  left for the landing gate.
