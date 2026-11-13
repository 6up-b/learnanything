# Phase 1 fixes: group FR-C (protection), rows P1-P7

Branch `refactor/p1-fixes-protection`, based on main `e231d7fb59`. One commit per row, test and fix together. Every test was shown failing at the tip before its fix. All seven reproduced.

## P1: the gate judges the snapshot, not only the file (reproduced)

- **Test.** `tests/test_k1_source_sets_gate.py::test_a_snapshot_loaded_from_an_empty_file_stays_unreadable_after_the_file_is_restored`: load while the file is empty, restore the file, call `exam_material` with the old vault. At the tip it did not raise.
- **Choice.** Carry the load's verdict on the loaded vault. `load_vault` appends a `yaml:empty` issue when the source sets file is empty at load; `protection_issues` already refuses any issue naming that path, and it still re-reads the file for an empty file now. Comparing the snapshot with the file would need a fingerprint or a re-parse on every gate call and would still leave the instant between the compare and the use; the issue lives exactly as long as the snapshot, so there is no window. A parse or schema failure already left a loader issue (`yaml:invalid`); the empty file was the only silent case.
- **Callers and siblings.** Every reader of the snapshot goes through `protection_issues` (`exam_material`, `role_material`, `held_out_partition` via `_require_readable`; `withheld_items`, `learner_context`, `remote/views.py`, `section_coverage`, `doctor`). The change is in the loader, so all are covered. The settled load (`load_vault_settled`) retries an empty file and keeps the last load only after its attempts, which now also carries the issue. Doctor reports the empty file twice (the loader's `yaml:empty`, and `source_sets:unreadable`); both are errors, the duplicate is cosmetic.
- **Not verified.** The desktop reload journey.

## P2: a root with no vault config is refused (reproduced)

- **Test.** `tests/test_exam_protection.py::test_a_reader_preset_fails_before_any_model_call_when_the_vault_config_disappears`: a book whose exam scope in `source_sets.yaml` holds its reading out, a queued preset, `learnloop.toml` removed, drain with a recording client. At the tip the request reached the model path (the list branch returned no source sets).
- **Fix.** `jobs._reader_source_sets` raises `SourceSetsUnreadable` when `learnloop.toml` is missing.
- **Callers.** `_refuse_held_out_reader_material` (quick check, inquiry passage check) and the drain's `source_sets=lambda` in `_drain_reader_requests`. Both now fail the request or job, as an unloadable vault already did.
- **Assertions changed.** `tests/test_ingest_jobs.py::test_kick_reader_drain_runs_model_synthesis_foreground` and `::test_background_reader_drain_records_model_call_receipts` bound the jobs object to a bare `tmp_path`, which relied on the empty-list branch. They now bind to `create_basic_vault(tmp_path / "vault").root`. Their subject is the drain, not the gate.
- **Siblings.** Searched `src` for other bare-list or `None` source-set arguments to the gate (`exam_material(`, `held_out_material(`, `exam_source_sets=`): none besides the test calls with `()`, which are bare lists by design.

## P3: source set saves serialize on the vault mutation lock (reproduced)

- **Test.** `test_two_source_set_saves_that_read_the_same_file_do_not_lose_one_another`: two threads, the first pauses after its read until the second has started; the first adds a set, the second adds another. At the tip the second overwrote the first.
- **Fix.** The read-modify-write in `vault/writer.upsert_source_set` runs inside `vault_mutation_lock(root, purpose="source_set_write")` (re-entrant, so the proposal accept and family operations that already hold it nest).
- **Writers of `source_sets.yaml`.** One: `upsert_source_set`. Its callers: `cli/source_set.py` (three commands), `sidecar handlers/ingest.py`, `content/pipeline/add_source.py`, `quick_add.py`, `revision_refresh.py`, `content/sources/source_deletion.py`. All reach the lock through the writer. `migration_coordinator` only reads the file. Hand edits and other processes that do not use the writer are outside any lock.
- **Not verified.** Two real processes (the test uses threads; `flock` excludes separate open file descriptions, which is what two threads in one process hold).

## P4: MCP find_sources withholds before verification (reproduced)

- **Test.** `tests/test_k1_mcp_find_sources.py::test_a_reserved_probe_passage_never_reaches_the_verification_model`: a probe item's own passage, `find_passages(verify=True)`, a recorder in place of `find_sources._verify`. At the tip the passage was in the pool handed to verification.
- **Fix.** `find_sources` takes `withhold`, a caller's rule from pool hits to a reason; the hits named leave the pool after the exam filter and before the verification page, only when a verification will run. The reasons are counted on the manifest (`withheld_before_verification`). `remote/sources.py` builds one classifier (`_classifier`: exam, assessment lane, solution, reserved or probe passages) and uses it both as that rule and in `_shown`, so the two cannot disagree; `_shown` adds the early counts, so the response's counts keep their keys.
- **Counts.** A dropped passage is now counted when it was in the verified pool, where before it was counted only when the model picked it (or, unverified, when it was in the top `limit`). With no verification nothing changes. The counts are therefore at least what they were.
- **Siblings.** See "P4 siblings" below.

## P5: the routine due queue honours the reservation (reproduced)

- **Test.** `test_the_routine_due_queue_does_not_serve_a_reserved_cold_item_before_its_check`: the basic vault's due item leaves `build_due_queue` once a treatment episode reserves it, and returns when the episode completes. At the tip it stayed.
- **Fix.** `routine_serving_exclusions` carries `open_remediation_cold_item_ids()` in `cold_check_reserved_item_ids` (the out-of-timing builder overwrote the field with tasks plus the same set); `routine_withhold_reason` gives `cold_check_reserved` (a routine gate, in `ROUTINE_GATES` and the plan's `POOL_CODES`). The cold retry task itself reaches the queue by the follow-up insertion, which does not ask this gate.
- **Selectors, before and after.**
  - Due queue (`build_due_queue`): before no; after yes.
  - Plan engine (`build_eligible`, `daily_plan/objective_inputs` `routine_serving_exclusions(...).out_of_timing_item_ids`): before no for the episode set (the routine object's field was empty); after yes.
  - `find_practice`/quick check/practice-index admission (`out_of_timing_serving_exclusions`): yes before and after.
  - Session serve door (`refuse_held_out_item`): checks exam reservation and held-out only. It is the door the cold check itself uses, so it is unchanged.
  - Phone and desktop queues: both call `build_due_queue`; yes after.
  - `explain_practice_item` and the intent feasibility builds: use the routine exclusions through `_BuildAdmission`; yes after.
  - AD slot check 0 (`ad_slot`): reads `cold_check_reserved_item_ids` of its own exclusions; yes before.
  - MCP practice: no practice-serving tool found in `remote/` or `learnloop_mcp` that selects an item (learning context and sources only).

## P6: the reservation ends with the retry (reproduced)

- **Tests.** `test_a_cold_retry_that_expires_unanswered_releases_its_reservation` (a real `cold_scheduled` episode with a `cold_retry` task, the queue's own expiry run past `expires_at`; asserts the item is back in `build_due_queue`) and `test_a_withdrawn_cold_retry_with_no_replacement_releases_its_reservation`. Both failed at the tip.
- **Fix.** The episode ends (`abandoned`, an existing state nothing wrote) where the task reaches its terminal state: in `Repository.due_followup_tasks`, in the same transaction as the expiry update, for the episodes of the cold retries it just expired; and in `remediation.withdraw_cold_measurement`. Both go through `Repository._release_cold_reservation`, which ends only a `cold_scheduled` episode with no open cold retry left. `open_remediation_cold_item_ids` is unchanged.
- **Reschedule.** `reschedule_assisted_cold_retry` withdraws a retry and then needs the episode still `cold_scheduled`; it passes `release_reservation=False` and releases through its wrapper only when no fresh retry was scheduled (the one-per-chain bound, no independent surface, a refusal).
- **Paths checked.** Answered: already `completed` (`consume_followup_task` caller). Expired: above. Withdrawn by the queue's cold lane (`apply_cold_decision`): through `withdraw_cold_measurement`. Withdrawn by the assisted reschedule: above. Certification cold probes are another kind and untouched.
- **Open sibling, decided afterwards.** See "P6 follow-up" below; the original note was: `record_remediation_attempt`'s schedule-refusal branch (no cold item, or one equal to the primed item) leaves the episode in `treatment` with `cold_item_id` set when it was equal to the primed item, so that item stays reserved. And an episode in `treatment` whose primed attempt is never taken reserves its cold item with no end. Neither is a retry that expired or was withdrawn, so I did not change them; whether either should end the episode is a lifecycle decision.
- **Read-only attach.** An expiry the queue's read-only attach does not write stays unreleased until a writing read runs, as the task itself stays `pending` until then.

## P7: the atomic write follows a symlinked destination (reproduced)

- **Test.** `test_a_symlinked_source_sets_file_is_written_through_and_the_link_stays`. At the tip the link was replaced by a regular file.
- **Fix.** `write_yaml_atomic` resolves the destination with `os.path.realpath` first, so the temporary sits beside the target and replaces the target.
- **Siblings.** `write_yaml_atomic` has one caller (`upsert_source_set`). `write_yaml` (every other vault file) opens the path and so already writes through a link. `evsi_calibration.artifacts.write_text_atomic` is a separate function for evidence output, not vault files; not changed.

## P4 siblings: every caller that sends retrieved passages to a model

`find_sources` already applies the one exam predicate (`exam_withheld`, all exam) to the pool before any verification, for every caller. So a surface whose own predicate is exam or held-out material is protected before the model on every path. The question is a surface that applies a wider predicate (`model_reader_withheld`: solutions and the assessment lane) or a different one after the passages return. I did not change any surface's set.

| Surface (file:line) | Scope / policy | Its predicate | Before or after the model | Action |
|---|---|---|---|---|
| MCP `remote/sources.py` `find_passages` | library, `verify` | all exam, assessment lane, solutions, reserved/probe passages | was after | fixed in P4 |
| Tutor tool `find_sources` (`instructional/tools.py` `execute_tool`, `_sources_view`) | library (default), `verify=True` | `model_reader_withheld` (solution, assessment lane), bound item's answer overlap | lane was after; answer overlap is before for assisted practice (`find_sources`' own filter) | fixed: `withhold=_lane_rule(...)` |
| Tutor tool `compare_sources` (`execute_tool`, `_comparison_view`) | library | the same lane rule | was after (pins, anchor, retrieved passages, all read by the verification and comparison models) | fixed: `compare_sources(withhold=...)`, applied to pins and anchor in `admitted` and to the candidates before verification |
| Reader lookup (`source_retrieval/reader_tutor.py:213`, `_admitted` :250) | library; assisted practice becomes the item-bound teaching scope | held-out only (K1 D2), plus the item-bound guard | before: `find_sources`' exam filter is wider than held-out, and the item-bound scope and answer filter precede verification | none |
| Reader pinned spans (`source_retrieval/tutor.py:508`) | no model verification | exam, scope, answer overlap | before any grounding | none |
| Library ask (`source_retrieval/library_ask.py:613`, `:637`; sidecar `handlers/library_ask.py:483`) | library, `verify=False` | held-out check on the anchor before retrieval; exam filter in `find_sources` | no verification model. The later `organize` judgment reads passages the exam filter already passed | none |
| Library ask comparison (`library_ask.py:1090-1097`, `:1432`; `handlers/library_ask.py:646`) | caller's scope | exam check on the anchor, held-out check on pins | before the call | none |
| Figures grounding (`figures/service.py:977`, `keys_withheld` :1000) | library, `verify=True` | `spans_withheld`, the same exam set as `exam_withheld` | before (the post check is the same set `find_sources` applied) | none |
| Workbench example (`workbench/route_example.py:119`, `keep` :143) | derived policy, `worked_example` verification | exam set; exercise/solution roles; answer overlap | before for the exam set and answer overlap (assisted practice scope also excludes exercise/solution); the roles check here is a selection filter | none |
| Sidecar `find_sources` RPC (`handlers/source_service.py:222`) and `compare_sources` RPC (:250) | caller's scope | the learner's own screen, exam filter in `find_sources` | the result goes to the learner, not a model | none |
| Library exercises (`handlers/library_exercises.py:406`) | teaching, `verify=False` | teaching scope applies before | no verification | none |
| Remediation source picker (`instructional/sources.py:104`) | teaching scope | teaching-wider exclusions in the scope | before | none |

Fail-first tests (`tests/test_p4_tutor_tool_withhold.py`, a recording `_verify` in place of the model): the tool's `find_sources` and `compare_sources` sent a problem-set passage to verification at the tip (`('ext_ps', 's2')` in the pool); both pass with the fix. The tool's `withheld_from_model` counts are still filled (the rule counts on the same `_Withhold`).

## P6 follow-up: a reservation lasts only while there is something left to do

Decision applied in the one query, `Repository.open_remediation_cold_item_ids`: a live episode reserves its cold item when its primed attempt is still to be taken, or when a cold retry stands open (`pending` or `served`). The episode state machine is unchanged.

- **(a) schedule-refusal branch.** Test `test_an_episode_whose_cold_retry_was_never_scheduled_reserves_nothing_after_its_primed_attempt` runs the real path (a legacy episode whose cold item is its primed item, then a primed attempt through `complete_self_graded_attempt`): the episode stays `treatment` with `primed_attempt_id` set and no task. At the tip the item stayed reserved; now it is not, before the primed attempt it still is.
- **(b) a `treatment` episode whose primed attempt is never taken: not fixed, and the rows cannot say.** No row has a terminal state or an expiry for it: `treatment` creates no follow-up task (the primed attempt is an ordinary practice attempt, and the `cold_retry` task is made only after it), the episode has `created_at`/`updated_at` but no `expires_at`, and nothing writes `abandoned` for a stale episode. What is missing is a lifetime for the episode itself (an `expires_at`, or a rule that an episode idle for N days ends), which is a product decision about how long a prescribed repair stays open. I did not invent one. Until it exists such an episode holds its cold item out of routine practice indefinitely; `why item:<id>` names it (below), so it is not silent.
- **What the learner sees.** `cold_check_reserved` is a routine gate, so `build_due_queue` records it like any other withheld reason: `why item:<id>` reports it as `excluded_now` (`exclusion_now`), and the slate record's exclusions by rule carry it with its count (`by_rule`). Test `test_a_reserved_cold_item_is_named_and_counted_by_the_slate_and_why`. There is no plain-language sentence for the code beyond the code itself; the other routine codes have none either.

## Rule departures

I ran `git stash` once by mistake while preparing a fail-first comparison, and popped it at once; the working tree was restored with nothing lost (checked with `git status`).
