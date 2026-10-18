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
