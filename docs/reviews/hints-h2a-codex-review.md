# Adaptive hints H2a: Codex review and fixes (stage `hints-h2a`)

Branch `hints/h2a` (worktree `learnanything-merge4`). The review read
`59d300e63..af1cad852` (codex-job `20261018-063502-2ApYE2`, read-only: nine
findings, one High). The fixes are in `210efe3a6`, with the references
regenerated in `03d6d0e2c`. Every finding was reproduced first by a failing
test in `tests/test_hint_h2a_review.py`: 17 of its 24 tests failed on
`af1cad852`, each for the reason the finding gives. All of them pass on the
fix. Fakes only: no model was reached, and nothing was run on a vault copy.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Polling a completed submission exposes an unrecorded worked answer | fixed | `210efe3a6` | `test_f1_a_hint_finished_before_the_submit_and_polled_after_it_is_never_shown[next_step@L3, walkthrough@L5]`, `test_f1_a_hint_written_after_the_submit_is_never_shown_into_the_committed_attempt`, `test_f1_an_open_submission_still_delivers_and_counts` |
| F2 | Medium | A smaller step toward a far waypoint cannot satisfy the contracts | fixed | `210efe3a6` | `test_f2_a_smaller_step_toward_a_far_waypoint_targets_the_adjacent_node_on_the_way`, `test_f2_the_service_serves_the_smaller_step_on_an_unchanged_draft`; `test_hint_replies::test_after_a_waypoint_more_aims_every_level_3_option_at_its_target` adjusted (see below) |
| F3 | Medium | Checkpoint validation accepts work after the first questionable point | fixed | `210efe3a6` | `test_f3_a_checkpoint_after_the_first_questionable_point_is_refused`, `test_f3_repeated_text_is_placed_at_its_first_occurrence` |
| F4 | Medium | A valid learner route may be replaced by another non-reference route | fixed | `210efe3a6` | `test_f4_an_alternative_learner_route_is_not_swapped_for_another_alternative` |
| F5 | Medium | The writer fallback raises a reply's level | fixed | `210efe3a6` | `test_f5_a_reply_to_a_level_2_hint_with_the_writer_down_is_not_served_at_level_3`, `test_f5_a_level_3_reply_falls_back_only_where_the_shortcut_allows_an_authored_hint[4 cases]` |
| F6 | Medium | EIG candidates are ranked under different rival distributions | fixed | `210efe3a6` | `test_f6_a_candidate_missing_a_rival_is_not_ranked_above_a_complete_one`, `test_f6_a_duplicate_or_unknown_prediction_is_refused` |
| F7 | Medium | Unplaceable work still gets a confident procedural hint | fixed | `210efe3a6` | `test_f7_unplaceable_work_gets_a_checked_approach_question_not_a_next_step`, `test_f7_placeable_or_valid_work_keeps_the_drawn_kind` |
| F8 | Medium | "From the book" bypasses T6 verification | fixed | `210efe3a6` | `test_f8_a_book_origin_on_an_unverified_passage_is_refused`, `test_f8_the_writer_is_told_its_passages_are_unverified` |
| F9 | Medium | The learner's successful routes never reach existing maps | fixed | `210efe3a6` | `test_f9_a_shown_hint_schedules_the_lazy_learner_route_merge`, `test_f9_the_merge_after_a_hint_obeys_the_maps_switches[2 cases]`, `test_f9_an_undelivered_hint_schedules_nothing`; `test_approach_maps::test_no_rpc_reaches_the_inline_build_or_the_merge` now also expects `schedule_merge_after_hint` |

No finding was rejected.

### What changed, per finding

- **F1.** `help_assists.mark_shown` refuses a row whose submission key
  already committed a `practice_attempts` row. It already refused a row with
  an `attempt_id`, and the new check also covers a hint inserted after the
  submit's attach. The check and the update run as one statement in the
  delivery transaction. `service.deliver_hint` returns `shown`,
  `submission_complete` or `not_deliverable`. The job read
  (`_job_payload`) records a refusal on the job, and from then on it answers
  `undelivered_result`: status `unavailable`, reason `submission_complete`,
  no `hintMd`, `shown: false`. Only `shown` lets the text reach the surface.
  `deliver()` keeps its old contract (the row, or None) for existing callers.
- **F2.** Rule 6's retained-waypoint check now goes through
  `contracts.toward_waypoint`. The target must be the waypoint itself, or a
  node on the route after the placement and no later than the waypoint. Once
  the work has reached or passed the waypoint, any target is accepted. The
  next-step adjacency rule is unchanged, so on `g → a → b → goal` a smaller
  step toward `b` targets `a`. The writer's `target_rule` says the same.
- **F3.** `contracts.stands_before`: what stands must end before the first
  questionable point in the draft. Positions are compared with spacing
  ignored, and each quote counts at its first occurrence. The existing
  containment check stays.
- **F4.** Rule 4 keeps the placed route, reference or not, while the work is
  valid. "I'm using a different approach" keeps it whether or not the work is
  valid. Only `book_way` moves a valid route, and only to the reference.
  Without work there is no learner route to keep.
- **F5.** `service.authored_fallback_allowed`: while the writer cannot run,
  an authored hint (level 3) answers only:
  - "More";
  - a reply to a level-3 hint with no shortcut or with "not where I'm stuck";
  - "too big a jump" when an authored hint is finer than the answered kind.

  A reply to a level-1 or level-2 hint, "the notation" and "a different
  approach" get `unavailable` with the writer's reason.
- **F6.** `discriminating.complete_predictions`: a candidate must predict
  every request rival exactly once, so a missing, duplicate or unknown rival
  id drops it. Every candidate is then scored under the same uniform prior
  over all the rivals, which are the weights the row records. The writer's
  contract asks for one prediction per rival.
- **F7.** `service.unplaced_work`: a checked route-directed answer is
  switched to an approach question when all of these hold:
  - the request is "More" at levels 1-3;
  - there is work and a map;
  - the kind is `waypoint`, `subgoal_plan`, `next_step` or
    `worked_parallel`;
  - `work_matches_a_route` and `work_valid_so_far` are both false.

  The approach question is asked and re-asked once (at most four writer
  calls). The row keeps the drawn option and its propensity. It records
  `served_kind = approach_question`, `reason = unplaced_work` and the round's
  `switched_to`, and the result carries a plain-words line.
- **F8.** A `worked_parallel` with `source_origin = "book"` fails
  `worked_parallel_book_unverified`. H2a's passages are H1's seed spans,
  retrieved with `verify=False` ("unverified: retrieval rank only"), so none
  meets §4.2's "a source quote passes T6 verification". The writer is told
  `worked_examples_verified: false` and writes an AI-written instance, which
  is labelled AI-written. A verified book label needs a T6 verification call;
  that is left for a successor stage (see open questions).
- **F9.** `map_builder.schedule_merge_after_hint` runs H1's
  `merge_learner_routes` in the background after a successful delivery. It
  goes through the sidecar's `BackgroundBuilds` registry, using H1's item
  lock, durable claim, lease, maps envelope and an admission fence; `fence`
  is a new keyword that `merge_learner_routes` passes to `_claimed`. H1's
  lifecycle code is otherwise unchanged. One map job per item is in flight
  per process. It is switched by `hints.maps.enabled` and
  `hints.maps.build_on_serve` (the config docstring now says
  `build_on_serve` covers this merge), and by
  `LEARNLOOP_APPROACH_MAP_BUILDS=off` when no client is injected. With no map
  or nothing new, no model is asked.

### Existing tests adjusted

- `test_hint_replies::test_after_a_waypoint_more_aims_every_level_3_option_at_its_target`:
  its deliberately wrong first answer aimed at the goal from the waypoint
  itself. Under F2's semantics that is correct, because the waypoint has been
  reached. The wrong answer now aims past the waypoint from the givens, which
  still fails `rule6_not_the_waypoint_target`.
- `test_approach_maps::test_no_rpc_reaches_the_inline_build_or_the_merge`:
  H1's guard expected H2 to wire the merge. The sidecar now imports
  `schedule_merge_after_hint` as well, and still never reaches
  `merge_learner_routes` or `build_map_inline` directly.

### Scope kept

- No migration (head 211). No `apps/` change. No change to H0's attach or
  report logic, or to H1's validator, leases or lifecycle; `fence` is the one
  added keyword on the merge entry.
- No evidence, grading, scheduling or replay rule change.
- The writer prompt changed (F2, F6, F8 wording). `hint_writer.v1` is kept
  because nothing of H2a has landed.

### Open questions

1. **Verified "from the book".** H2a never labels a hint "from the book".
   Restoring the label needs T6 verification of the quoted passage, which is
   a model call (`find_sources(verify=True)` or a verify of the seeds), with
   its source and span stored on the row.
2. **Replies on unplaceable work.** A "doesn't connect" reply keeps the
   answered level (D15), so F7's switch applies to "More" only. Should H2b
   carry the previous placement into the chooser's state so the approach
   question can be offered there too?
3. **The writer-down path's propensity.** The review's §6.2 note: when the
   writer cannot run, the row records no propensity rather than §4.5's
   fallback propensity 1. This was not a numbered finding and is unchanged.

### Gate (this step)

The full suite, the whole durability lane and vitest run once, in the
landing gate. `TMPDIR` was the worktree's `fixtures-local/tmp`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **26 kept, 0 broken**.
- `uv run pytest -n auto` on 25 files: **681 passed**. The files:
  - new and changed: `test_hint_h2a_review`, `test_hint_replies`,
    `test_approach_maps`;
  - affected: `test_approach_map_boundaries`, `test_approach_map_replay`,
    `test_help_assists_schema`, `test_hint_blind`, `test_hint_contracts`,
    `test_hint_discriminating`, `test_hint_evidence`,
    `test_hint_kill_switch`, `test_hint_service`, `test_hint_telemetry`,
    `test_library_asks_migration`, `test_judge_routes`;
  - contract: `test_architecture`, `test_mobile_allowlist`,
    `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`,
    `test_desktop_rpc_contract`, `test_coordinated_migrations`,
    `test_registry_audit`, `test_table_roles`,
    `test_tracked_fixture_databases`, `test_config_refactor`.
- Before that, all hint and approach-map files
  (`tests/test_hint_*.py tests/test_approach_map*.py`): **356 passed**.
- `test_hint_h2a_review` and `test_hint_evidence`, run three more times for
  the job and merge threads: **39 passed** each time.
- Durability:
  - `-m durability` on `test_help_assists_schema`, `test_hint_telemetry`,
    `test_hint_evidence`, `test_approach_maps`, `test_hint_h2a_review`:
    **2 passed**;
  - `--durable-sqlite` on `test_hint_h2a_review` and `test_hint_evidence`
    (WAL; the delivery transaction and the job and merge threads'
    connections): **39 passed**.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 211). Committed in `03d6d0e2c` (commit labels and line
  citations only).
- No frontend or Tauri change, so no npm, vitest or cargo step. No migration,
  so no head fixture.
- Model calls: **0**. No paid or live call, and no run on any vault copy.

## Fix round 2 (after Codex job 20261018-070736-i218fT)

The verify read `2153658bc`. It confirmed F2, F3, F4, F6, F8 and F9, and the
original F1, F5 and F7 scenarios. It reopened four items (one High). The
orchestrator's binding rulings are applied in `c7eb3bd49`, and the references
are regenerated in `b083da1ed`. The tests are in
`tests/test_hint_h2a_review_round2.py`. Its 19 tests were run against
`2153658bc`'s source (`git archive 2153658bc`, with
`pytest -o pythonpath=<tmp>/src`): 14 failed. Twelve failed for the reason the
item gives. Two are new-API guards that fail on the import: the fold rule's
unit test and the strict reveal's guard. All 19 pass on the fix. Fakes only:
no model was reached.

| id | severity | title | fix | tests (fail on `2153658bc`) |
|---|---|---|---|---|
| V1 | High | Delivery races the submission's evidence snapshot | taken again inside the attempt's write transaction | `test_v1_a_hint_delivered_after_the_fold_and_before_the_commit_is_counted[attempt-next_step@L3, dont_know-next_step@L3, dont_know-worked_chunk@L4]`; guards: `[attempt-walkthrough@L5]` (passes on the old tree, because the L5 reveal auto-primes it there), `test_v1_a_delivery_inside_the_commit_waits_and_is_refused[attempt, dont_know]`, `test_v1_the_fold_rule_is_the_submits_own` |
| V2 | Medium | Contract fallback raises a reply's level | `downgrade_allowed` | `test_v2_a_reply_or_pick_at_level_2_that_fails_twice_is_not_served_at_level_3[feedback, book_way]`; guards: `test_v2_a_fixed_level_3_reply_keeps_the_level_3_downgrade`, `test_v2_more_keeps_the_section_4_6_downgrade` |
| V3 | Medium | F7 excludes replies and picks | `unplaced_work` for every request; from the givens for `book_way` and worked help | `test_v3_a_reply_on_unplaceable_work_gets_the_approach_question[None, learner_route]`, `test_v3_a_smaller_step_on_unplaceable_work_gets_the_approach_question`, `test_v3_more_never_serves_a_check_this_part_on_unplaceable_work`, `test_v3_the_books_way_on_unplaceable_work_starts_from_the_givens`, `test_v3_worked_help_taken_on_unplaceable_work_starts_from_the_givens` |
| V4 | Medium | Delivery succeeds without its reveal | shown mark and reveal in one transaction | `test_v4_a_failed_reveal_write_shows_nothing_and_the_job_retries`; guard: `test_v4_record_reveal_keeps_swallowing_for_its_existing_callers` |

### What changed, per item

- **V1.** The invariant: the attempt commits the fold over the rows shown
  when it commits, and no row becomes shown after that.
  - **The fold travels with the draft.** The submit's fold and the rule it
    applied go on the draft as
    `AttemptDraft.server_hint_fold`, a
    `learnloop.attempts.hint_fold.ServerHintFold`. The rule covers:
    - the base hints (the client's plus the tutor questions');
    - the base priming (the client's, or a trace changed after a
      self-grade disclosure);
    - the item's `max_useful_hints`, with `submit_dont_know`'s "clamp only
      when the fold adds";
    - for an empty stuck answer, the `stuck_attempt_type` inputs.

    Both submit handlers compute their values through it. So the pre-commit
    value and the in-transaction value come from one rule.
  - **The count is taken again under the write lock.** `apply_attempt` reads
    the fold again inside its own `BEGIN IMMEDIATE` transaction, before
    anything is computed (`_refold_server_hints`). While the transaction
    holds the write lock, no delivery can commit, and once the attempt
    exists `mark_shown` refuses the row. So this count is final.
  - **On a change, the draft is rebuilt by the same rule.** The rebuild
    covers `hints_used`, `primed` and a stuck answer's type. Everything
    computed from the draft later in the same transaction then reads the
    final count:
    - the auto-prime;
    - the eligibility decision (`_resolve_attempt_target`, re-run by
      `compute_attempt_application`);
    - the activity classification;
    - dampening and the FSRS cap;
    - the completion saved with the attempt.

    The blind grade is reused. The one grade field derived from
    `hints_used` is a self-graded "I don't know"'s deterministic error type,
    and it is recomputed.
  - **No rollback path was needed.** The recompute is done inside the
    transaction, so the ruling's "roll back and redo once" fallback was not
    used.
  - **Delivery loses inside the commit.** `mark_shown` still refuses under
    `BEGIN IMMEDIATE` once the submission has an attempt.
  - **The tests use two sidecars on one vault.**
    - Sidecar B prepares the hint. Sidecar A submits.
    - In the first order, B delivers after A's fold read and before A's
      commit. A's attempt equals a serial twin's (delivered, then
      submitted): the count, priming, the attempt type and the activity
      classes.
    - In the second order, B tries to deliver while A's attempt
      transaction is open. B waits on the lock, then is refused
      (`submission_complete`). The row stays unshown, no reveal is written,
      and the attempt counted nothing.
- **V2.** `service.downgrade_allowed`: §4.6's level-3 `next_step` downgrade
  answers "More" and any request at level 3 or higher.
  - A `feedback` reply, `smaller_step` or `book_way` fixed at level 1 or 2
    stops after the re-ask. It answers `unavailable` (`contract_failed`):
    "I couldn't write a hint that fits here; press Hint again or use the
    item's hint". The prepared row is not deliverable.
  - A fixed level 3 keeps the downgrade. Fixed levels 4-5 are lowered by
    it.
- **V3.** `service.unplaced_work` now applies to every request. The
  route-directed kinds are the ruling's (`next_step`, `waypoint`,
  `subgoal_plan`, `error_specific`, `continuation`), plus F7's
  `worked_parallel`. When both placement flags are false:
  - **`book_way` and worked help** (levels 4-5, which the learner took)
    keep their option and are re-asked from the givens on the reference
    route. `Target.from_givens` is told to the writer and checked in code:
    - the placement must be at the givens (`at_givens`);
    - nothing of the work may be claimed as standing;
    - rules 1 and 3 are not required.

    An answer already at the givens on the reference route is kept as it
    is.
  - **Every other request** gets the checked `approach_question` at level 1.
    That lowers the level, and never raises it.

  The row records the drawn option, the served kind and
  `reason = unplaced_work`. The round records `switched_to`
  (`approach_question` or `from_givens`). The writer is asked at most four
  times, as in F7.
- **V4.** The sidecar's `_deliver` shows the row (`deliver_hint`) and writes
  its positive-overlap `tutor_answer` reveal in one transaction.
  - The reveal goes through `reveal_ledger.record_reveal_strict` and
    `reveal_episode_id(strict=True)`, which raise instead of swallowing.
  - A failed reveal write rolls the shown mark back. The read answers
    `unavailable` with reason `reveal_not_recorded`, no text and
    `shown: false`. The job is neither delivered nor refused, so a later
    read retries it.
  - The learner-route merge is scheduled only after the transaction
    commits.
  - `record_reveal` keeps its swallowing behaviour (it now wraps the strict
    writer), so its existing callers are unchanged.

### Scope kept

- No migration (head 211), and no `apps/` change.
- H0's attach logic and H1's lifecycle are unchanged.
- `apply_attempt` changes only for a draft that carries a fold. Only the two
  submit handlers set one. Replay never refolds.
- `hint_writer.v1` is kept. The prompt gains a `from_givens` line, used only
  when that target is asked, and nothing of H2a has landed.
- Model calls: **0**.

### Gate (fix round 2)

The full suite, the whole durability lane and vitest run once, in the
landing gate. `TMPDIR` was the worktree's `fixtures-local/tmp`.

- `uv run lint-imports --no-cache`: **26 kept, 0 broken**.
- `uv run pytest -n 8` on 47 files: **1266 passed**. The files:
  - every `tests/test_hint_*.py` and `tests/test_approach_map*.py`
    (including the new round-2 file);
  - the contract files: `test_mobile_allowlist`,
    `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`,
    `test_registry_audit`, `test_architecture`, `test_cli_help_snapshot`,
    `test_coordinated_migrations`, `test_table_roles`,
    `test_tracked_fixture_databases`, `test_config_refactor`;
  - `test_reveal_ledger`, `test_help_assists_schema`, `test_judge_routes`,
    `test_library_asks_migration`;
  - every practice-handler file that submits through `submit_attempt` or
    `submit_dont_know` (21 files: daily plan, diagnosis, router, reader,
    sidecar contract, stuck prompt, UX phase 4 and others).
- `tests/test_hint_h2a_review_round2.py` run three more times for the
  threads: **19 passed** each time.
- Durability:
  - `-m durability` on `test_help_assists_schema`, `test_hint_telemetry`,
    `test_hint_evidence`, `test_approach_maps`, `test_hint_h2a_review`,
    `test_hint_h2a_review_round2` and `test_reveal_ledger`: **2 passed**;
  - `--durable-sqlite` (WAL) on `test_hint_h2a_review_round2` (the
    two-connection interleavings), `test_hint_h2a_review` and
    `test_hint_evidence`: **58 passed**.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 211). Committed in `b083da1ed` (commit labels and line
  citations only).

## Fix round 3 (after Codex job 20261018-073851-h8jddN)

The verify read `1f23ee970`. It confirmed three things:

- V1 for a matching submission key, in both orders;
- that every value derived from the count is recomputed from the final
  count;
- no regression for hint-free stored evidence against `59d300e63`.

It reopened five items (one High). The orchestrator's binding rulings are
applied in `3d189580e`, and the references are regenerated in `ff1ec0df6`.
The tests are in `tests/test_hint_h2a_review_round3.py`. Its 10 tests were run
against `1f23ee970`'s source (`git archive 1f23ee970`, with
`pytest -o pythonpath=<tmp>/src`): 7 failed, each for the reason the item
gives. The 3 that pass there are guards. All 10 pass on the fix. Fakes only.

| id | severity | title | fix | tests (fail on `1f23ee970`) |
|---|---|---|---|---|
| W1 | High | A keyless submit lets a waiting delivery succeed | the fence closes the session's window | `test_w1_a_delivery_waiting_on_a_keyless_commit_is_refused`, `test_w1_the_fence_and_the_keyless_fold_share_one_window`; guards: `test_w1_a_delivery_before_a_keyless_commit_is_counted`, `test_w1_a_hint_free_keyless_submit_records_what_it_did` |
| W2 | Medium | Option fallback raises a fixed-level pick | options at the answered level only | `test_w2_the_books_way_after_a_level_2_hint_with_the_draft_cleared_is_not_level_3` |
| W3 | Medium | The AT_GIVENS shortcut bypasses from_givens | the shortcut passes the whole from-givens contract | `test_w3_a_walkthrough_at_the_givens_that_claims_work_stands_is_re_asked` |
| W4 | Medium | A kind change drops placement constraints | `dataclasses.replace` on every Target change | `test_w4_a_second_zero_eig_answer_from_the_givens_keeps_the_from_givens_contract` |
| W5 | Medium | Delivery when the item is gone or changed | fail closed before marking shown | `test_w5_a_hint_for_a_removed_or_changed_item_is_never_shown[removed, edited]`; guard: `test_w5_an_unchanged_item_still_delivers` |

### What changed, per item

- **W1.** `help_assists.mark_shown` still runs under `BEGIN IMMEDIATE`.
  - **Two things now close a row's count** (`_CLOSED`):
    - its submission committed an attempt (F1);
    - any attempt of the row's `practice_session_id` and `practice_item_id`
      committed at or after the row's `requested_at`, whatever that
      attempt's submission key, NULL included.

    `deliver_hint` reports either case as `submission_complete`
    (`help_assists.count_closed`).
  - **The keyless window is now session-scoped.** The fold uses the same
    window. A keyless submit's `since` is now the item's last attempt *in
    this session* (`help_assists.keyless_window_start`). Before, it was the
    item's last attempt in any session.
  - **`since` is read again at commit.** `hint_fold.read_fold` reads it
    again inside the attempt's write transaction with the count. So the
    refold counts exactly the rows requested after the last attempt in the
    session and shown when the attempt commits. Once the attempt commits,
    the fence stops every row requested at or before it.
  - **The upper bound needs no clause.** A row is requested before it is
    inserted, and it is inserted under the write lock. So every row visible
    to the refold was requested before the attempt's `created_at`, which is
    stamped inside the same transaction.
  - **Ties.** Timestamps have one-second precision. A row requested in the
    same second as an attempt is closed (`>=`), and the next window does not
    count it (`>`). It is never shown and never counted.
  - **Hint-free keyless submits.** These fold nothing, before and after the
    fix. Their records are unchanged.
- **W2.** `build_options` for `book_way` answering a level-1 or level-2 hint
  keeps that level.
  - If neither the answered kind nor the level's plain form applies (e.g.
    `localize` with the draft cleared), no option is offered. The request
    answers V2's unavailable message ("I couldn't write a hint that fits
    here; press Hint again or use the item's hint"), and no writer call is
    made.
  - `feedback` already offered the answered level only. `smaller_step`
    answers a level-3 waypoint.
  - `downgrade_allowed` now compares the answered hint's level, never the
    chosen target's.
- **W3.** An answer `unplaced_work` finds already at the givens is checked
  again under the from-givens target (`replace(current, from_givens=True,
  reference_route=True, downgrade=False)`).
  - It is accepted only when that check passes. Otherwise it is re-asked
    from the givens, as FROM_GIVENS is.
  - The round records `from_givens_failures`.
- **W4.** Every Target change in `_check_round` and `_write` now goes
  through `dataclasses.replace`, so `from_givens` and every route constraint
  are kept. The audit table is below.
- **W5.** The sidecar's `_deliver` passes the item as loaded now to
  `deliver_hint(..., item=...)`.
  - **When it refuses:** before `mark_shown`, a missing item, or one whose
    `practice_item_hash` differs from the row's, is refused.
  - **What the read returns:** status `unavailable`, reason `item_changed`,
    no text, `shown: false`.
  - **The job:** it is marked refused (not retryable), so nothing is counted
    and no reveal is written.
  - **Other callers:** `deliver()` keeps its old contract (the item is not
    checked unless passed).

### Target audit (W4)

| site | before | now |
|---|---|---|
| `_check_round`: no-positive-EIG fallback | `Target(served_kind, level, target_node_id, reference_route, request, shortcut, answered)`, which dropped `horizon_index`, `downgrade` and `from_givens` | `replace(target, kind=served_kind)`: everything kept |
| `_write`: round-3 §4.6 downgrade | `Target("next_step", 3, ...)`, which dropped `horizon_index` (deliberate: a next step has none) and `from_givens` (False there, since the downgrade runs only before any unplaced switch) | `replace(target, kind="next_step", level=3, horizon_index=None, target_node_id=<kept at L3>, downgrade=True)`: keeps `from_givens`, `reference_route`, `request`, `shortcut` and `answered` |
| `_write`: approach-question switch | `Target("approach_question", 1, request, shortcut, answered)`, which dropped `target_node_id` and `horizon_index` (deliberate), `reference_route` (True only for `book_way`, which never takes this switch), `downgrade`, and `from_givens` (False there) | `replace(target, kind="approach_question", level=1, horizon_index=None, target_node_id=None, downgrade=False)`: keeps `reference_route` and `from_givens` |
| `_write`: FROM_GIVENS re-ask and the AT_GIVENS check | `replace(current, from_givens=True, reference_route=True, downgrade=False)` | unchanged: everything else kept; `downgrade` is cleared on purpose, since starting from the givens is not a checkpoint downgrade |
| `request_hint`: the chosen option | `Target(kind, level, horizon_index, target_node_id=<at L3>, reference_route, request, shortcut, answered)` | unchanged. `OptionSet.max_horizon` was never a Target field: `too_big` applies it in the options, as before |
| `_writer_down`, `_authored` | no Target | unchanged |

`grep "Target(" src/learnloop/hints` finds no other construction. The
writer prompt only reads the Target.

### Gate (fix round 3)

The full suite, the whole durability lane and vitest run once, in the
landing gate.

- `uv run lint-imports --no-cache`: **26 kept, 0 broken**.
- `uv run pytest -n 8` on 48 files: **1276 passed**. These are round 2's 47
  files plus the round-3 file.
- `tests/test_hint_h2a_review_round3.py` run three more times: **10 passed**
  each time.
- Durability:
  - `-m durability` on the touched files (round 2's set plus round 3's
    file): **2 passed**;
  - `--durable-sqlite` (WAL) on the round-3, round-2 and review files and
    `test_hint_evidence`: **68 passed**.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 211). Committed in `ff1ec0df6`: commit labels, line
  citations, and the `help_assists` note's test list (it now lists the
  round-3 file).
- Model calls: **0**. No migration and no `apps/` change.

## Fix round 3b (closes round 3's keyless double count)

The orchestrator ruled the gap round 3 recorded as High-class, because a hint
could be counted twice. The fix is `fe69c0410`, and the references are
regenerated in `0fa750cfe`.

- **The attempt that counts a server hint row attaches it.**
  - Inside the attempt's write transaction, after the attempt row exists,
    `apply_attempt` calls `hint_fold.attach_keyless`. That sets
    `attempt_id` on every row a keyless fold counted.
  - It is the same NULL-to-value write that H0's attach makes, and H0's
    identity trigger allows it.
  - The rows are defined once, in `help_assists._fold_rows`, for both the
    count and the attach: unattached, shown, server-counted hint rows of the
    session and item, requested after the window start.
  - The window start is the one `refolded_draft` reads under the same lock.
    The draft carries it even when the count is unchanged.
- **Every fold counts unattached rows only**, keyed or keyless (it already
  did: `attempt_id IS NULL`). So a row a keyless attempt took is never
  counted again, whatever its key.
- **H0's keyed attach is unchanged.** It only attaches rows whose
  `attempt_id` is NULL. So it never moves a row a keyless attempt took.
- **Telemetry rows are untouched.** Client-counted authored rows are not
  attached or folded here.
- **Replay never attaches** (`replace_existing`).

Tests are in `tests/test_hint_h2a_review_round3.py`, round-3b section. Run
against `git archive 664a5ad1e`, 2 of its 4 tests fail:

- `test_3b_a_keyless_submit_attaches_the_hint_it_counted` fails because the
  row's `attempt_id` stayed NULL.
- `test_3b_a_hint_counted_by_a_keyless_submit_is_never_counted_again` fails
  because the k1 submit counted the hint a second time (1, not 0).

The guards pass there:

- `test_3b_keyed_flows_are_unchanged`;
- `test_3b_authored_reveal_telemetry_is_not_taken_by_a_keyless_submit`;
- round 3's `test_w1_a_hint_free_keyless_submit_records_what_it_did`.

This closes round 3's open question, which is removed above.

### Gate (fix round 3b)

- `uv run lint-imports --no-cache`: **26 kept, 0 broken**.
- `uv run pytest -n 8` on round 3's 48 files: **1280 passed**.
- Durability:
  - `-m durability` on the touched files: **2 passed**;
  - `--durable-sqlite` (WAL) on the round-3, round-2 and review files,
    `test_hint_evidence` and `test_hint_telemetry`: **136 passed**.
- References: **0 errors** (head 211).
- Model calls: **0**. No migration and no `apps/` change.
