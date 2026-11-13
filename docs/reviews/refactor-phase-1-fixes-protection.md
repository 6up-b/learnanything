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
- **Siblings.** Other callers of `propose_sources` with verification (tutor tools, Reader tutor, Library ask, library exercises, source service, figures, route example, the remediation source picker) have their own scope rules and are not the MCP; none passes `withhold`. Not examined for the same defect (see below).

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
- **Open sibling, not fixed.** `record_remediation_attempt`'s schedule-refusal branch (no cold item, or one equal to the primed item) leaves the episode in `treatment` with `cold_item_id` set when it was equal to the primed item, so that item stays reserved. And an episode in `treatment` whose primed attempt is never taken reserves its cold item with no end. Neither is a retry that expired or was withdrawn, so I did not change them; whether either should end the episode is a lifecycle decision.
- **Read-only attach.** An expiry the queue's read-only attach does not write stays unreleased until a writing read runs, as the task itself stays `pending` until then.

## P7: the atomic write follows a symlinked destination (reproduced)

- **Test.** `test_a_symlinked_source_sets_file_is_written_through_and_the_link_stays`. At the tip the link was replaced by a regular file.
- **Fix.** `write_yaml_atomic` resolves the destination with `os.path.realpath` first, so the temporary sits beside the target and replaces the target.
- **Siblings.** `write_yaml_atomic` has one caller (`upsert_source_set`). `write_yaml` (every other vault file) opens the path and so already writes through a link. `evsi_calibration.artifacts.write_text_atomic` is a separate function for evidence output, not vault files; not changed.

## Rule departures

I ran `git stash` once by mistake while preparing a fail-first comparison, and popped it at once; the working tree was restored with nothing lost (checked with `git status`).
