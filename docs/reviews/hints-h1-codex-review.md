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

## Fix round 2 (orchestrator, after Codex job 20261018-025919-tgE3aw)

The orchestrator's Codex verify of `8fe376ba2` confirmed F4 and F5. It
reopened the stage on five Mediums (M1-M5) and one Low (L1). All six are fixed
in `257fc8899`, following the binding rulings. There is no schema change.

### How the tests were checked against the old code

The 30 new tests are in `tests/test_approach_maps.py`, in the section "Fix
round 2". They were run against `8fe376ba2`'s `src/` and `migrations/`,
exported with `git archive` into a scratch directory and put first with
`-o pythonpath=`. No file in the worktree was swapped and no `git stash` was
used. Results on the old code:

- **Every new test function fails.** That is 24 failed and 1 error (L1's
  in-flight mark left behind).
- **Six parametrized cases pass on the old code.** The old lone-digit and span
  checks already caught them, so they stay as regression cases:
  - M1, with the expected answer `4` and the state `$4$`, `\(4\)` or `+4`;
  - M1, with the expected answer `1/4` and the state `\frac{1}{4}` or
    `P = \left(\frac{1}{4}\right)`;
  - M2, with the state `So $P = 0.75$.`
- **The M4 tests fail for the reason in the ruling.** After the switch or the
  shutdown, vault A gets a judgment, a finished receipt, a checkpoint and a
  released claim.

No model calls were made, live or paid. Fakes only.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| M1 | Medium | Formatted and equivalent answers slip past leak detection | fixed | `test_m1_a_formatted_or_equivalent_answer_is_marked_and_fails_a_label[*]` (11 cases), `test_m1_a_single_symbol_answer_is_a_token_match_never_a_substring`, `test_m1_controls_and_the_questions_own_values_stay_as_ruled`, `test_m1_a_vault_item_with_a_formatted_answer_builds_with_its_leak_marked` |
| M2 | Medium | A goal state with a wrong last assignment verifies | fixed | `test_m2_a_goal_state_whose_last_assignment_differs_is_a_mismatch[*]` (4 cases), `test_m2_only_a_checked_goal_state_verifies`, `test_m2_an_unchecked_goal_is_stored_unverified` |
| M3 | Medium | Lease liveness: expiry is not checked, a lapsed lease is renewed, and the builder never learns of a lost lease | fixed | `test_m3_holds_claim_checks_expiry_and_renewal_never_revives_a_lapsed_lease`, `test_m3_an_expired_claim_writes_no_judgment_and_stores_nothing`, `test_m3_a_lost_heartbeat_stops_the_build_before_its_reask`, `test_m3_a_takeover_while_awaiting_a_response_pays_writes_and_stores_nothing_more`, `test_m3_a_lapsed_lease_is_never_renewed_by_the_heartbeat` |
| M4 | Medium | Background builds outlive a vault switch and shutdown | fixed | `test_m4_a_vault_switch_while_the_provider_is_slow_writes_nothing_to_either_vault`, `test_m4_shutdown_and_eof_drain_within_their_bound` |
| M5 | Medium | A revert to an earlier revision blocks merges forever | fixed | `test_m5_a_merge_after_a_revert_stores_a_new_version_of_that_revision`, `test_m5_a_merge_whose_revision_stopped_being_active_stores_nothing` |
| L1 | Low | A thread-start failure leaves `_INFLIGHT` set | fixed | `test_l1_a_thread_start_failure_leaves_no_in_flight_mark` |

### What changed

- **M1** (`hints/maps.py`).
  - One normalisation, `normalize_math` and `normalize_key`, is used for both
    sides. It strips `$…$`, `$$…$$`, `\(…\)`, `\[…\]`, `\left` and `\right`.
    It writes `\frac{a}{b}` (and `\dfrac`, `\tfrac`) as `(a)/(b)`. A key also
    loses its whitespace and a leading `+`.
  - `answer_candidates` lists what a text states, in that form:
    - its standalone numbers, but never the `4` in `14`, `x_4`, `2^4`, `4.5`
      or `3/4`;
    - the value after each `=`, cut at the first prose word or clause break;
    - the whole text, when it is a short expression.
  - `states_answer` compares each candidate with the key through the existing
    guarded checker (`answer_check.answers_equal`). `answer_check` is
    unchanged.
  - A single-symbol key is a word-boundary token match, never a substring:
    `x` appears in "y = x" and "Solve for x", but not in "next", "max", `x_4`
    or `\xi`.
  - `gives_away` adds `states_answer`. So a non-goal node whose state holds an
    equivalent of the answer is marked as a leak by code, and `label_leaks`
    fails such a label with `label_leak`.
  - The question's own values stay exempt for labels: the new equivalence
    check is skipped when the question itself states the answer. Node marking
    has no exemption, as before, so it leans toward marking.
  - `exact_key` now also finds a key that only parses in the shared form, for
    example `\frac{1}{4}` and a worked solution ending in `\frac{1}{4}`.
    Before, such answers had no key.
  - "Step 4" is still a label leak for the answer 4, as already ruled.
- **M2** (`hints/maps.py`).
  - `assignment_conclusion` reads the goal state's last `=` after the same
    normalisation. "Therefore y = x^3" gives `x^3`, and "P = \frac{3}{4}"
    gives `(3)/(4)`. It never reads `<=`, `>=`, `!=` or `==` as an
    assignment.
  - That value is compared with the guarded checker, and a decidable
    difference is `goal_mismatch` (basis `goal_state`). A declaration that
    differs is still `goal_mismatch` (basis `exact_key`).
  - Only the goal state verifies. Either its conclusion equals the key, or it
    assigns nothing and states the key ("There are 4 socks").
  - A declaration that agrees with a state the checker cannot read is
    `unverified` (basis `goal_state_unchecked`). It never becomes verified
    through the declaration alone. Such a map is still stored, with
    `verified_goal = 0`, when everything else validates. The spec allows this
    in §4.3: "otherwise the builder's declaration, stored as unverified".
  - One case of the F2 test (`"1/4"` with "The probability at the point")
    expected `verified`. Under this ruling it is now `unverified`, and it
    moved to `test_m2_*`.
- **M3** (`db/stores/judgment_claims.py`, `hints/map_builder.py`).
  - `holds_claim(..., now=...)` also requires the lease to be unexpired.
    Without `now` it behaves as before for its other callers: the judge,
    reader quick checks and source-exercise import.
  - `renew_claim` refuses an expired lease, for every caller. A lapsed lease
    is never revived, because another worker may already have judged it free.
  - The heartbeat sets `claim.lost` when a renewal is refused, or when its
    vault's generation has ended.
  - The builder checks liveness (lost signal, fence, owner, epoch and expiry,
    read in the database) at three points:
    - before assembling seeds;
    - before each ask, the re-ask included. Each physical request, provider
      and truncation retries included, also goes through `PaidCalls.admit`;
    - inside each `judgment_ledger` write's transaction.
  - On a lost lease the builder raises `_LeaseLost`. `_paid` maps it to
    `stale`, with no further paid work.
  - `_store` re-checks owner, epoch and expiry inside BEGIN IMMEDIATE.
- **M4** (`hints/map_builder.py`, `learnloop_sidecar/context.py`,
  `handlers/app.py`, `handlers/practice.py`, `server.py`).
  - **The registry.** `BackgroundBuilds` is a registry keyed to the loaded
    vault (its sqlite path) with a generation token. `SidecarContext` owns one
    (`map_builds`). `load` closes it when the vault changes and binds it to
    the new one. The `shutdown` RPC and the end of `serve()` (shutdown or EOF)
    call `close_background_builds()`.
  - **Closing.** `close()` stops admitting builds and bumps the generation,
    which cancels every admitted `BuildFence`. It then joins running builds
    for at most `drain_seconds` (default `DRAIN_SECONDS` = 3 s). It never
    hangs on a provider call.
  - **Fenced writes.** Every late write of a background build is fenced by the
    generation and the lease. That covers receipts and checkpoints (through
    `_FencedRepository`, the repository its `PaidCalls` writes through),
    judgments, the map row, the claim's renewal and release, and a new claim.
    Each write holds the registry's gate. A switch waits for a write already
    under way, then fences every later one.
  - **Provider calls.** These are not interrupted. Their results are fenced.
  - **Admission.** `schedule_build_on_serve(builds=...)` admits a build only
    for the registry's vault and only while it is open. The module's default
    registry is unbound: it is for tests and callers without a sidecar.
    `wait_for_background_builds` still joins the builds of every registry.
- **M5** (`hints/map_builder.py`). A merge is now fenced against the newest
  row of its own revision: `current_map` for the base's `practice_item_hash`
  and `structure_hash`. That revision must still be the item's active one:
  `item_revision` is recomputed inside the transaction, so a new PF skeleton
  that arrives mid-merge fences it out. A merge's `supersedes_id` is its base.
  So A -> B -> revert to A -> merge stores version 3 of A, superseding A's
  version 1.
- **L1** (`hints/map_builder.py`). `schedule_build_on_serve` clears the
  in-flight mark in a `finally` for any failure before the thread starts.
  This includes a `Thread()` that raises and a `start()` that raises.

### Limits, defaults taken, and notes

- **Receipts of a fenced call are dropped (M4 ruling).** A paid call that
  returns after its vault was switched away, or its lease lost, keeps its
  "start" receipt, but its "finish" receipt and its checkpoint are not
  written. The drop is logged (WARNING, with the call's id, tokens and cost).
  The daily spend ledger (`source_service_spend`) is deliberately not fenced:
  the reservation still settles with the actual amount, so money already
  spent always counts against `hints.maps.max_daily_cost_usd`. This also
  departs from `save_model_checkpoint`'s general "saved even after the job
  lost ownership" rule, for map builds only, as the ruling asks.
- **`renew_claim` change is store-wide.** The ruling names `renew_claim`, so
  the expiry refusal applies to its other caller too: source-exercise import's
  key-check heartbeat. That heartbeat now stops at a lapsed lease, so
  recovery can take it over. Its tests pass (`test_source_exercise_import`,
  `test_source_exercise_rpcs`). `holds_claim`'s expiry check stays opt-in
  (`now=`).
- **Retrieval while assembling seeds.** Seeds are assembled after a liveness
  check, through the real repository. A retrieval that is slow across a switch
  is not fenced inside `find_sources_for_caller`, which is outside H1's scope.
- **M1 leans toward marking**, as F1 did. A lone letter key, for example a
  multiple-choice answer `B` or a rare `a`, is a token match in prose too.
  Node marking only restricts what H2 may reveal, and a flagged label is
  re-asked.
- **Migration comment.** The comment in `migrations/211_approach_maps.sql`
  about what `structure_hash` covers is unchanged (it does not mention the
  resolved rubric). This round needed no schema change, so the fixture was not
  rebuilt, and the orchestrator's instruction was to make that edit only with
  a rebuild.

### Gate (targeted, per the owner rule of 2026-10-17; `TMPDIR` = the worktree's `fixtures-local/tmp`)

- `uv run lint-imports --no-cache`: 26 kept, 0 broken.
- `uv run pytest -n 8` over 25 files: **464 passed**. The files are:
  - the 16 files of round 1;
  - the sidecar lifecycle, initialize and shutdown files:
    `test_sidecar_transport`, `test_sidecar_registry`,
    `test_sidecar_contract`, `test_ux_phase1_first_run`,
    `test_settings_sidecar`, `test_sidecar_golden_path`;
  - the other `renew_claim` caller's files and the post-attempt worker:
    `test_source_exercise_import`, `test_source_exercise_rpcs`,
    `test_post_attempt_worker`.
- `uv run pytest -m durability` over the four approach-map files: **2
  passed**. These include the two-process F3 test.
- `uv run pytest -n 8 --durable-sqlite tests/test_approach_maps.py`: **95
  passed**.
- The new timing and thread tests (`m3_`, `m4_`, `m5_`, `l1_` and the F3
  tests) were rerun 3 times with `-n 4`: 15 passed each time. The `--durable-sqlite`
  run was also repeated 3 times: 10 passed each time.
- Not run, because nothing they cover changed: the schema, migration, head
  fixture and DB references; `answer_check` and its callers (unmodified); the
  CLI, config and serializer pins; the frontend and cargo.
- The full suite, the whole durability lane and the whole vitest run are left
  for the landing gate.

## Fix round 3 (after Codex job 20261018-032508-6kTAc9)

The Codex verify of `50fbf3fc3` confirmed M3, M5, L1 and the spend
accounting. It reopened the stage on four Mediums and three Lows. Prose parsing
for goals and leaks was not converging, so the orchestrator's rulings R1-R4
change the design. Everything is fixed in `07b0dcdec`. There is no schema
change: the new fields live inside `map_json`, so migration 211, its head
fixture and the references are untouched.

### How the tests were checked against the old code

The 30 new tests are in `tests/test_approach_maps.py`, in the section "Fix
round 3". They were run against `50fbf3fc3`'s `src/` and `migrations/`,
exported with `git archive` and put first with `-o pythonpath=`. No worktree
file was swapped and nothing was stashed.

The fixtures write the new node fields only when the model declares them
(`approach_map_fakes._structured_fields`). So on the old tree each test fails
on its behaviour, not on `extra_forbidden`.

- **Every new test function fails.** That is 26 failed.
- **Four parametrized cases pass on the old code**, and stay as controls:
  - R3 `ledger` and `store`: both already re-checked the fence inside their
    transaction through `_holds`;
  - R2, with the expected answer `1/4` and the span `$P(X \le 1/2) = \frac{1}{4}$`;
  - R2, with the expected answer `4` and the state "a share of 3/4".
- **The R3 failures are Codex's reproduction.** On the old code, with the
  write lock held and the registry closed while the write waits, the claim,
  release, checkpoint and receipt writes all land in the closed vault.
- **The R4 failures are Codex's.** On the old code:
  - close returns `True` while a build is alive;
  - the second drain takes another 0.4 s;
  - the log line names `call_id: null`.

No model calls were made, live or paid.

| Codex item | ruling | severity | verdict | tests |
|---|---|---|---|---|
| 2, 3 | R1 | Medium | fixed | `test_r1_prose_or_a_mentioned_answer_never_verifies_the_goal[*]` (4), `test_r1_only_the_structured_conclusion_verifies_or_contradicts`, `test_r1_a_quantity_carries_its_unit_in_its_own_field`, `test_r1_an_unparsed_conclusion_or_no_key_is_stored_unverified`, `test_r1_the_builders_output_schema_requires_the_structured_fields` |
| 1 | R2 | Medium | fixed (best effort; see below) | `test_r2_an_answer_inside_a_math_span_or_with_a_unicode_sign_is_marked[*]` (5), `test_r2_a_sign_stays_attached_and_a_fraction_is_never_split[*]` (7), `test_r2_a_structured_value_equal_to_the_answer_marks_its_node` |
| 4 | R3 | Medium | fixed | `test_r3_a_close_while_a_write_waits_for_the_lock_lands_nothing[claim, release, checkpoint, receipt, ledger, store]` |
| 5, 6, 7 | R4 | Low | fixed | `test_r4_launch_and_close_are_atomic`, `test_r4_a_generation_is_drained_once`, `test_r4_a_dropped_receipt_logs_its_call_id` |

### What changed

- **R1** (`hints/maps.py`; the builder's prompt).
  - `MapNode` gains `conclusion` (the goal's final answer as a bare
    expression, with no prose and no units, or `""` for a proof) and `unit`.
    Both are required by the builder's strict output schema. The pydantic
    default `""` lets older fixtures and other nodes omit them.
  - `goal_agreement(conclusion, expected, unit)` decides from the conclusion
    alone:
    - `verified` only when it parses and `answers_equal` holds against the
      exact key;
    - `goal_mismatch` (basis `conclusion`) only when it parses and
      `answers_differ` holds;
    - otherwise `unverified`, stored with `verified_goal = 0` and the basis
      `no_exact_key`, `no_conclusion`, `conclusion_unparsed` or `undecidable`.
      It is never rejected.
  - "Parses" means `answer_check.parse_answer` or `safe_math_text`, after the
    shared normalisation (`structured_expression`). A declared unit written
    after the expression is dropped. An expression is "unparsed" when it is
    any of:
    - a quantity with its unit still attached ("4 m");
    - an equation, an inequality or `!=`;
    - prose.
  - The prose goal check, `assignment_conclusion` and the token-presence path
    are removed. "Distance = 4 m" is now just prose: the conclusion is `4`
    with unit `m`.
  - `goal_answer` stays as the builder's informational restatement, and a
    label still must not contain it. It no longer decides anything.
  - The F2 tests and round 2's M2 tests, which pinned prose-based verdicts,
    are replaced by the R1 tests.
- **R2** (`hints/maps.py`).
  - Each node may carry `value`, the bare expression its state establishes.
    A non-goal node whose `value` equals the answer under `answers_equal` is
    marked as a leak by code (`value_states_answer`). A leak node's `value`
    and `conclusion` join the expressions a label must not contain.
  - Prose extraction, improved once:
    - every math span (`$…$`, `$$…$$`, `\(…\)`, `\[…\]`) is taken whole as a
      candidate before its delimiters are stripped;
    - Unicode signs (−, ‐, ‑, ‒, –, —, ﹣, －, ＋) are written as ASCII;
    - a sign stays attached, so `-4`, `−4` and `x-4` never state `4`;
    - a fraction is never split, so the numerator and denominator of `3/4`,
      `\frac{3}{4}` and `(3)/(4)` are not candidates. This applies to the
      lone-digit matcher too.
  - Candidates are compared with `answers_equal`. Codex's cases are now
    caught: `$\frac{2}{8}$` for `0.25`, `$x*x$` for `x^2`, and `−4` for `-4`.
- **R3** (`hints/map_builder.py`; `db/stores/model_calls.py`).
  - **The fenced transaction.** `_fenced_txn` is the one write fence. It
    acquires BEGIN IMMEDIATE first. Only then does it take the registry gate
    and re-check the generation token and the lease (owner, epoch and expiry,
    or the generation only when taking a new claim). It holds the gate until
    the commit.
  - **The writes it covers.** Every late write goes through it: the claim,
    renew, release, the receipt start and finish, the checkpoint save and
    discard, judgments and map rows. The pre-acquired `open_` boolean
    (`_write_gate`) is removed.
  - **Closing.** `close()` takes the gate only to change the generation. A
    writer still waiting on the database lock holds nothing that close waits
    on. When it gets the lock it sees the new generation and rolls back,
    however long busy_timeout kept it waiting.
  - **Receipts and checkpoints.** These are written transactionally on the
    fence's connection. The receipt start goes through the pinned connection,
    and when fenced out it raises, so no request is sent. The finish and the
    checkpoint SQL are shared from the store (`finish_receipt`,
    `insert_checkpoint`, `delete_checkpoint`), so the SQL-owner rule holds.
    The store's own methods are unchanged in behaviour.
- **R4** (`hints/map_builder.py`).
  - **(5)** `BackgroundBuilds.launch` admits, registers and starts a build
    under the registry lock, and refuses once the registry is closed. So a
    close either refuses the build or joins it.
  - **(6)** A generation is drained once. Closing an already-closed registry
    joins nothing more, so a vault switch (close, then bind) and shutdown
    (the handler, then `serve()`'s `finally`) each spend one deadline.
  - **(7)** A dropped receipt logs `event["id"]`.

### Limits and notes

- **Prose leak detection is best-effort defence in depth.** The binding leak
  gate is H2's leak control on the written hint text (spec §4.6), which H2
  must run on every hint. This is recorded as H2 friction note 7 in
  `docs/reviews/adaptive-hints-H1.md` §8. Structured `value` and
  `conclusion` are what code relies on.
- **Known Low.** Prose that needs algebraic rewriting to show the answer, for
  example "x times x" written in words for `x^2`, is not detected.
- **Unverified maps (H2 friction note 8).** An unverified map is stored and
  usable. H2 must not treat unverified as invalid.
- **Close waits for one commit.** Close waits on the gate only for a commit
  already holding the database lock. In rollback-journal mode, that commit
  can itself wait for readers, up to busy_timeout. Close never waits on a
  writer that is still queued for the lock.
- **Version labels unchanged.** `PROMPT_VERSION` and `MAP_SCHEMA_VERSION`
  were not bumped, because no map has been stored outside tests (migration
  211 is unlanded). The prompt text changed, and so does its hash and
  checkpoint key.

### Gate (targeted; `TMPDIR` = the worktree's `fixtures-local/tmp`)

- `uv run lint-imports --no-cache`: 26 kept, 0 broken.
- `uv run pytest -n 8` over round 2's 25 files plus
  `test_model_call_receipt_owners.py` (the store refactor): **489 passed**.
  The first run had one failure: `test_architecture`'s SQL-owner rule caught
  a raw `DELETE` in `map_builder`. That SQL was moved into the store, and the
  rerun is green.
- `uv run pytest -m durability` over the four approach-map files: **2
  passed**. These include the two-process F3 test.
- `uv run pytest -n 8 --durable-sqlite tests/test_approach_maps.py`: **116
  passed**.
- The thread and timing tests were rerun 3 times with `-n 4`:
  - `r3_`, `r4_`, `m3_`, `m4_`, `m5_`, `l1_` and `f3_`: 24 passed each time;
  - the same set without `f3_`, under `--durable-sqlite`: 19 passed each
    time.
- Not run: references (no schema change), and the frontend and cargo (no
  `apps/` change). The full suite, the whole durability lane and vitest are
  left for the landing gate.

## Fix round 4 (after Codex job 20261018-035041-4Y7U0m)

The Codex verify of `8d10955d8` confirmed:

- R1's design;
- R3's queued-writer fix, with no lock inversion;
- R4;
- the store helpers;
- every earlier boundary.

It reopened the stage on two Mediums and two Lows. All four are fixed in
`da60b180d`, following the orchestrator's rulings U1-U4. There is no schema
change.

### How the tests were checked against the old code

The 18 new tests are in `tests/test_approach_maps.py`, in the section "Fix
round 4". They were run against `8d10955d8`'s `src/` and `migrations/` (`git
archive`, `-o pythonpath=`). Results:

- **Every new test function fails on the old code**: 15 failed.
- **Three U1 cases already pass on the old code** and stay as controls:
  - `4m` against `4m`;
  - `4` against `4` with unit `m`;
  - `4 m` against `5` with unit `m`.
- **The failures match Codex's descriptions.** On the old code:
  - **U1:** `4 m` against `4`/`m` is `goal_mismatch`, and a value of `4`/`m`
    marks no leak.
  - **U2:** `close(0.02)` stays blocked behind a commit held by a reader.
  - **U3:** an expired lease is changed to `released`.
  - **U4:** `- 4` states `4`, and "Use the ratio 3 / 4" fails `label_leak`.

The U2 test doesn't need the new `committing` counter to exist. On the old
code it waits a fixed half-second instead, so it fails on the bound, not on an
`AttributeError`.

| Codex item | ruling | severity | verdict | tests |
|---|---|---|---|---|
| 1 | U1 | Medium | fixed | `test_u1_a_reference_with_a_unit_is_read_by_the_same_quantity_helper[*]` (12), `test_u1_a_structured_value_with_its_unit_marks_its_node` |
| 2 | U2 | Medium | fixed | `test_u2_close_never_waits_past_its_bound_on_a_commit_held_by_a_reader` |
| 3 | U3 | Low | fixed | `test_u3_an_expired_lease_is_never_released` |
| 4 | U4 | Low | fixed | `test_u4_a_spaced_fraction_is_one_token[3, 4]`, `test_u4_a_spaced_sign_stays_attached` |

### What changed

- **U1** (`hints/maps.py`).
  - One helper, `read_quantity(text, unit)`, reads the reference, the goal's
    `conclusion` and a node's `value`. It produces a `Quantity` with these
    parts:
    - `number`;
    - normalised `unit`;
    - `whole`, the algebraic reading;
    - `ambiguous`.
  - It recognises three shapes:
    - "4 m", a number, a space and a unit token (letters, µ, Ω, °, % and then
      `^ / * · .`), which is split into a number and a unit;
    - "4m", a number with letters attached, which is **ambiguous** (4 metres
      or 4·m);
    - anything else, which is an expression with the declared unit, if any.
  - `\text{…}`, `\mathrm{…}`, `\,` and `~` are read as plain text, and a
    declared unit written after the expression is dropped.
  - Units are compared as normalised strings (`normalize_unit`): markup and
    whitespace removed, `²`/`^{2}` written `^2`, case kept.
  - `compare_quantities(reference, given)` decides as follows:
    - Equal units, no unit on either side, or a unit on one side only against
      an unambiguous reference: the numbers decide with
      `answers_equal`/`answers_differ`. Equal means verified (or a leak);
      a clear difference means mismatch.
    - Units that differ: unverified, with the basis `unit_differs`.
    - An ambiguous "4m" on either side decides only when its algebraic and
      quantity readings agree. A unit on one side only against an ambiguous
      reference decides nothing. Otherwise it is unverified, with the basis
      `unit_ambiguous`. Never a mismatch.
  - `exact_key` keeps a quantity-shaped reference whole ("4 m", "$4\,\text{m}$")
    instead of squashing it to `4m`.
  - `value_states_answer` uses the same rule for the node value leak check.
  - The R1 test case "conclusion `4 m`, no unit field, reference `4`" is now
    verified, a unit on one side against an unambiguous reference. Round 3
    had it as `conclusion_unparsed`.
- **U2** (`hints/map_builder.py`). The linearisation changes, and there is no
  commit gate any more.
  - **The writer's side.** The generation lives under a small
    `_generation_lock`. Inside its transaction, after BEGIN IMMEDIATE, a
    writer:
    1. checks its lease, which cannot change under the write lock;
    2. takes the small lock to check the generation and register as
       committing (`_committing += 1`);
    3. releases the small lock;
    4. commits, and deregisters in a `finally`.
  - **The close side.** `close()` takes the small lock only to bump the
    generation, so no writer can pass its check after that. It then waits on
    the condition `_committing == 0`, up to the remaining deadline. If a
    commit is still finishing at the deadline, it logs a WARNING and returns
    `False`. It never blocks past its bound.
  - **Semantics, recorded as the ruling asks.** A commit that registered
    before the bump is linearised before close. It may finish after close
    returns, into the vault file its connection already holds. That is a
    pre-close write to its own vault, and it is acceptable. No writer that
    checks after the bump commits.
- **U3** (`hints/map_builder.py`). `_release` goes through the normal
  lease-checked `_fenced_txn`. A lost or expired lease is never changed to
  `released`; it lapses or is taken over.
- **U4** (`hints/maps.py`).
  - `number_tokens` is one tokenizer for answer candidates and the lone-digit
    shortcut (`_states_short_key`).
  - A signed number keeps a sign separated by whitespace ("- 4", "−  4"), and
    a fraction is one token across whitespace ("3 / 4", "( 3 ) / ( 4 )"). A
    number is never the numerator or denominator of a fraction it is not part
    of ("x / 4", "4 / x").
  - `_clean` joins a spaced leading sign to its number before the checker
    sees it. The checker would otherwise read "- 4" as a markdown list bullet
    holding `4`.
  - "Use the ratio 3 / 4" is no longer a `label_leak` for 3 or 4, whether or
    not the question states the ratio. "- 4" does not state `4`.

### Limits and notes

- **Monomials verify less often.** An attached-letter answer like `2x` is
  ambiguous by shape. It verifies when written the same way on both sides
  (`2x` against `2x`), but `x*2` against `2x` is now unverified, not
  verified. This is a loss of verification, never a rejection.
- **`x - 4` is `-4`.** A binary minus written with spaces ("x - 4") now reads
  as the signed token `-4`, so it does not state `4`. This leans away from
  marking. Prose detection remains best-effort defence in depth, and H2's
  §4.6 text gate is binding (friction note 7).
- **U2 test in WAL mode.** Under `--durable-sqlite` (WAL), a reader does not
  hold a commit. There the U2 test checks only the bound and the
  after-the-bump fence; the `False` return is asserted in rollback-journal
  mode.

### Gate (targeted; `TMPDIR` = the worktree's `fixtures-local/tmp`)

- `uv run lint-imports --no-cache`: 26 kept, 0 broken.
- `uv run pytest -n 8` over the same 26 files as round 3: **507 passed**.
- `uv run pytest -m durability` over the four approach-map files: **2
  passed**.
- `uv run pytest -n 8 --durable-sqlite tests/test_approach_maps.py`: **134
  passed**.
- The thread and timing tests were rerun 3 times with `-n 4`:
  - `u2_`, `u3_`, `r3_`, `r4_`, `m3_`, `m4_`, `m5_`, `l1_` and `f3_`: 26
    passed each time;
  - the same set without `f3_`, under `--durable-sqlite`: 21 passed each
    time.
- Not run: references (no schema change), and the frontend and cargo. The
  full suite, the whole durability lane and vitest are left for the landing
  gate.

## Fix round 5 (after Codex job 20261018-040555-09Q38u)

The Codex verify of `003fc9863` confirmed U2, U3, the lifecycle and every
boundary. It reopened the stage on three Mediums and one Low, all in reading
quantities and units:

1. "2 x" was read as a unit: `2*x` became a mismatch and `2` became verified.
2. 4 cm verified against 4 m, because the "m" was stripped from the end of
   "cm".
3. 4 m² gave a mismatch.
4. (Low) "x /   4", with extra spaces, still split the fraction.

The orchestrator ruled that unit reasoning was not converging and replaced
it with a simpler rule set that never reasons about units at all. It is
implemented in `7333da6d8`, with no schema change.

### The rules (now in `hints/maps.py`)

- **`norm(s)`.** It does five things:
  - strips the math delimiters, `\text{}`, `\mathrm{}`, `\,` and `~`;
  - writes Unicode superscripts as `^n`;
  - writes Unicode signs as ASCII;
  - collapses whitespace to single spaces;
  - trims the result.
- **Quantity-shaped.** A reference is quantity-shaped when `norm(reference)`
  is a number (an integer, a decimal or a/b), then whitespace, then a token
  starting with a non-digit. Examples: "4 m", "4 m^2", "2 x", "3 cm",
  "4 °C". `exact_key` keeps such a reference whole.
- **Goal rules (`structured_verdict`, used by `goal_agreement`).**
  1. A quantity-shaped reference is verified only when
     `norm(conclusion + " " + unit)` equals `norm(reference)` as a string. When
     the unit is empty, `norm(conclusion)` is compared, so a conclusion of
     "4 m" also matches. Otherwise it is unverified, with the basis
     `quantity_reference`. It is never a mismatch.
  2. For any other reference, when the structured unit is not empty, the same
     string equality decides. Otherwise it is unverified, with the basis
     `unit_on_conclusion`. It is never a mismatch.
  3. For any other reference with no unit, `answers_equal` gives verified and
     `answers_differ` gives `goal_mismatch`. Anything else is unverified
     (`conclusion_unparsed`, `undecidable`). So `x^2` against `x^3` and `1/4`
     against `3/4` stay mismatches.
- **Removed.** `read_quantity`, `compare_quantities`, `Quantity`,
  `normalize_unit` and every suffix stripping, including in
  `structured_expression`.
- **The node value leak check (`value_states_answer`).** A node's value is a
  leak when rules 1–3 would verify it as the goal, or when
  `norm(value) == norm(reference)`. This is conservative.
- **U4.** `number_tokens` now uses a scan, `_standalone`, in place of the
  fixed-width lookbehinds. The scan skips any amount of whitespace when it
  checks the slash and parenthesis context on both sides. So "x /   4",
  "x /  (4)", "x / ( 4 )" and "x/\t4" are denominators. The adjacency rules
  are unchanged: `x_4`, `2^4`, `4.5`, `x-4`, a signed `- 4`, and whole
  fractions.

### Tests

- **New tests.** These are in the section "Fix round 5" of
  `tests/test_approach_maps.py`:
  - `test_r5_quantities_compare_as_strings_and_never_mismatch[*]`, 13 cases.
    They cover Codex's cases:
    - `2 x` against `2*x`, `2` and `2 x`;
    - `4 m` against `4 cm` with unit `m`, and `3 cm` against `3` with unit
      `m`;
    - `4 m²`, `4 m³`, `4 °C` and `(4) m`;
    - the rule-3 controls: `x^2` against `x^3`, `1/4` against `3/4`, and
      `1/4` against `0.25`.
  - `test_r5_a_value_is_a_leak_when_the_goal_rules_verify_it_or_it_equals_the_reference`.
  - `test_r5_a_denominator_after_any_whitespace_is_not_the_answer[*]`, 4
    labels, each checked for the answer 4.
- **Earlier tests re-pinned to these rules.**
  - `test_u1_a_reference_with_a_unit_is_read_by_the_same_quantity_helper[*]`
    (round 4's table). These cases changed:
    - `4 m` against `5`/`m` was a mismatch; it is now unverified
      (`quantity_reference`).
    - `4 m` against `4` with no unit was verified; it is now unverified
      (`quantity_reference`).
    - `4` against `4`/`m` was verified; it is now unverified
      (`unit_on_conclusion`).
    - The `cm` cases were `unit_differs`; they are now `quantity_reference`.
    - `4m` against `4`/`m` was `unit_ambiguous`; it is now
      `unit_on_conclusion`.
    - `4` against `4m` was unverified; it is now `goal_mismatch`, because by
      rule 3 `4m` is algebra.
  - `test_r1_a_quantity_carries_its_unit_in_its_own_field`: the reference
    `4 m` verifies `4`/`m` and `4 m`. The bare reference `4` with `4`/`m` is
    now unverified (`unit_on_conclusion`), and with `4 m` and no unit it is
    `conclusion_unparsed`.
- **Against `003fc9863`.** The tests were run against `003fc9863`'s `src/`
  and `migrations/` (`git archive`, `-o pythonpath=`). Every Codex case
  fails there, and so does every new test function: 19 failed. 12 passed:
  - the rule-3 and string-identity controls;
  - two labels the old fixed-width lookbehinds already handled.

### Notes

- **For H2.** H2 friction note 8 in `docs/reviews/adaptive-hints-H1.md` now
  records these rules. Unverified is common for quantity answers: an
  equivalent but differently spelled unit, `2*x` for "2 x", or a unit on one
  side only. H2 must not treat unverified as invalid.
- **Literal reading of "quantity-shaped".** The definition is applied
  literally: a token starting with any non-digit. So an algebraic reference
  written with spaces around an operator ("1 - x", "4 + x") is
  quantity-shaped. It verifies only by string identity and is never a
  mismatch. That is conservative: verification is lost, but nothing is ever
  rejected.
- **No unit means algebra.** A conclusion with letters attached and no unit
  ("4m") against a bare reference ("4") is algebra under rule 3, so it is a
  mismatch.

### Gate (targeted; `TMPDIR` = the worktree's `fixtures-local/tmp`)

- `uv run lint-imports --no-cache`: 26 kept, 0 broken.
- `uv run pytest -n 8` over the same 26 files as round 4: **525 passed**.
- `uv run pytest -m durability` over the four approach-map files: **2
  passed**.
- `uv run pytest -n 8 --durable-sqlite tests/test_approach_maps.py`: **152
  passed**.
- The thread tests were run once, because the lifecycle is untouched: `u2_`,
  `u3_`, `r3_`, `r4_`, `m3_`, `m4_`, `m5_`, `l1_` and `f3_`, 26 passed.
- Not run: references (no schema change), and the frontend and cargo. The
  full suite, the whole durability lane and vitest are left for the landing
  gate.
