# Exam protection: Codex review and fixes

**Branch:** `sources/exam-protection` (worktree `learnanything-merge3`), base main `e8d261405`.
**Reviewed:** the stage as committed through `883b8da11` (`docs/reviews/exam-protection.md`); Codex job `20261013-172155-Gd6N4S` (read-only, no paid calls, memory-only probes reproduced F2-F4).
**Fix commits:** `1c7b70f25` (code and tests), `9554ff588` (regenerated DB and config references), `dcc1b02bb` (the Reader drain's source sets without a vault, found by the first gate run), `f97724e29` (references again), and this record.
**Migration:** none (no schema change). **Algorithm successor:** none (F6). **New config key:** `goals.held_out_selection` (default `true`). **Paid calls:** none. **Frontend / `src-tauri`:** unchanged.

Every finding reproduced. Five are fixed outright. F6 is fixed in part (a kill switch, its parity checks and the shadow-rebuild validation) and rejected in part (the algorithm successor), under the owner's standing ruling.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Already-imported held-out items remain eligible for routine practice | **fixed** | `1c7b70f25` | `test_an_item_marked_held_out_after_its_import_leaves_routine_practice` (Today's queue and the shared exclusions), `test_a_pick_of_an_item_marked_held_out_since_its_proposal_is_refused`, `test_a_session_serve_of_an_item_marked_held_out_is_refused` |
| F2 | High | Held-out restrictions fail to propagate across revisions | **fixed** | `1c7b70f25` | `test_held_out_marks_in_two_extractions_each_reach_the_other`, `test_an_unresolvable_mark_withholds_every_extraction_of_its_source`, `test_the_same_unit_marked_in_two_extractions_withholds_only_that_unit`, `test_the_same_occurrence_with_other_content_is_not_the_same_unit` |
| F3 | High | Reader protection uses a narrower held-out partition than the leakage gate | **fixed** | `1c7b70f25` | `test_a_held_out_assessment_signal_is_held_out_for_the_reader_and_the_gate_alike` (the partition, `ExamMaterial.is_held_out`, Reader Ask, `held_out_material`), `test_a_reader_import_of_a_held_out_signal_is_refused` |
| F4 | High | PF forwards held-out quotes identified through locators | **fixed** | `1c7b70f25` | `test_pf_never_forwards_a_held_out_parent_quote[locator / namespaced / unlocated]` |
| F5 | High | Exposure after reservation does not invalidate an exam item | **fixed** | `1c7b70f25` | `test_an_exam_item_exposed_after_its_reservation_is_withdrawn_before_the_exam_starts` (reserve, expose, start the exam), `test_a_pool_every_item_of_which_was_exposed_is_reserved_afresh` |
| F6 | Medium | Serving changes are unconditional under existing algorithm versions | **fixed in part** (kill switch, parity, shadow rebuilds); **rejected in part** (algorithm successor) | `1c7b70f25` | `test_with_the_switch_off_routine_practice_serves_held_out_material_as_before`, `..._picks_and_session_serves_are_not_refused`, `..._shown_material_is_selected_as_before` (exam pool, certification cold probe), `..._the_cold_retry_is_the_predecessor_s`, `..._an_exposed_exam_item_is_administered_as_before`, `test_the_switch_never_reaches_what_a_model_is_shown`, `test_replay_never_reads_the_switch`; shadow rebuilds below. Successor: the owner's ruling (live changes behind kill switches, not successors, for serving changes replay never reads) |

**Fail-first evidence.** All 21 tests in `tests/test_exam_protection_review.py` were run against a `git archive` of `883b8da11`'s `src/` and `migrations/` (`-o pythonpath=fixtures-local/tmp/base883/src`; a probe confirmed `learnloop.content.sources.exam_material` was imported from the archive): **21 failed**. The F1-F5 tests fail on the reported defects (the item stays in Today's queue; the pick and the serve go through; `t5` of the other extraction is not held out; the re-extraction is unprotected; `is_held_out` is false on the signal; the Reader import is not refused; the held-out quote is in PF's passages; the exposed items are in the exam's `item_order`). The F6 tests fail because the switch does not exist there.

## F1: held-out material out of routine practice

**Reproduction.** An item gets a canonical exercise in a problems unit and is due. Marking the unit `held_out_evaluation` after the import left it in `build_due_queue`, and a stale proposal's pick and a session `get_practice_item` served it. `item_exam_status` had no production caller.

**Fix.**
- `exam_material.held_out_items(vault, repository)`: the items whose own source (`item_source_keys`: canonical exercise, block-level provenance refs, an extraction named whole) lies in the held-out partition (F3's one partition). An extraction a ref names without a block counts only when it is held out whole. Serving is precise here, unlike PF's quotes (F4): an unlocated ref is not evidence that the item came from the held-out part.
- `scheduling.serving_exclusions`: a fourth routine exclusion, `held_out_item_ids`, in `item_ids` and `out_of_timing_item_ids`. It reaches Today's queue (`withheld("held_out_material")`), placement's first-review check, the quick check and `find_practice` admission (new reason `held_out_material`).
- Existing picks and serves are rechecked:
  - `instructional.practice.refuse_exam_reserved_pick` becomes `refuse_protected_pick`. With the vault it also refuses a held-out item. It is called by `record_proposal_selection` and `imported_exercise_selection`, so `plan_learner_pick` and the open list's serve inherit it.
  - `learnloop_sidecar.serving.refuse_held_out_item` is the session-serve door, with code `held_out_material` and the reason. It is called from `get_practice_item` (session serves only; read-only opens still render), `open_queue_item` and `start_teach_back`.
- The certification cold probe and the remediation cold retry also skip held-out items. The probe scheduler must not create a task the serving door refuses, and a cold check would put the exam's question in front of the learner.
- The exam pool still reserves held-out items: the held-out exam is where they belong.

## F2: marks reach every extraction of the source

**Reproduction.** Two extractions of the textbook, `ext_text` marking "Exercises" and a re-extraction `ext_text_2` marking "Worked examples". Each extraction took only its own marks, so `ext_text`'s worked example (`t5`) was not held out. An unresolvable mark in the only marking extraction returned before the other extraction was considered, leaving it open.

**Fix** (`exam_material._held_out_units`). A mark is a restriction on the source:
- Each extraction carries its own marks by unit id, and every other extraction's marks by label: every unit with that label, since labels repeat ("Exercises" under each chapter).
- The one exception is a unit the extraction itself marks that is provably the same unit: the n-th with that label **and** the same content hash (`semantic_hash`, now carried on `UnitRow`). This is the common re-mark after a re-extraction, and it is not widened to every same-labelled unit. When the content differs, or the marks disagree on which occurrence, every unit with the label is withheld.
- A label that does not resolve withholds the whole extraction, as before. A mark that resolves nowhere (its unit, and so its label, is unknown) now withholds **every** extraction of the source.

## F3: one held-out partition

**Reproduction.** An exam unit's inventory carries an assessment signal with `held_out: true` and no unit mark. `held_out_partition` covered its span; `held_out_material(repository)` and `ExamMaterial.is_held_out` did not. So Reader Ask, presets, checks and the Reader import accepted it.

**Fix.**
- The signals are added in one place (`_add_signals`) and read by `exam_material` too. `ExamMaterial.held_out` is the full partition, which `is_held_out`, the Reader import's guard, the import recheck and `item_exam_status` read.
- `held_out_material(vault_or_sets, repository)` is the partition across every subject. The repository-only signature is gone, so no caller can narrow it silently. Each caller now passes the source-set context:
  - `tutor_qa.ask_question` (and its manifest filter) and `reader_dialogue.ask` pass the vault.
  - `reader_requests.model_synthesis(client, *, source_sets=...)` takes the sets, or a callable, read when each request is sent. The ingest runner's drain reads them through `jobs._reader_source_sets(vault_root)`: the vault's source sets; none for a root with no `learnloop.toml` (a runner bound to a bare directory, as two ingest-job tests do); a vault that fails to load raises, so the request fails before any call. The unit tests pass `()`.
  - The quick and passage checks' `_refuse_held_out_reader_material` reads the same helper.

## F4: PF's parent quotes

**Reproduction.** A parent `SourceRef` with `extraction_id`, a `block_span_v1` locator into a held-out exercise, a quote and empty `span_ids` passed the guard, so the quote was a generation passage. Namespaced span ids (`ext:span`) and an extraction-only ref passed too.

**Fix.**
- `exam_material.source_ref_keys(ref)` is the shared parser: the locator, plain span ids, and namespaced ones (`ext/span`, `ext:span`; block span ids never carry a separator). `item_source_keys` now uses it.
- `source_ref_protected(material, ref, repository)` drops a quote, conservatively, when:
  - any located block is exam or held-out material;
  - the ref names an extraction without a block and any of that extraction is material;
  - a located block id is not a block of a partly protected extraction (the text cannot be placed);
  - the ref has no location, but its source or revision has material in it.
- PF's `_passages` asks it before forwarding any quote.

## F5: exposure after reservation

**Reproduction.** Reserve a pool, read one item's exercise in the Reader, reveal another's answer through the tutor, start the exam: both were in `item_order`. The `own_reserved_ids` exemption kept them, and `start_exam` checked servability only.

**Fix** (`goals.exam_pool.withdraw_exposed_reservations`).
- **What is withdrawn.** A reserved item the learner has been shown is withdrawn. "Shown" uses the same rule as reservation (`exposed_items`, reading `shown_items`): a reveal outside its own feedback, its exercise or book solution read, or its prompt in a proposal.
- **History.** The row is released (`released_at`), never deleted, so the reservation history stays, and the item rejoins practice as a finished exam's items do (new `Repository.release_exam_pool_items`). Nothing is withdrawn while the goal's exam is in progress (its order is frozen).
- **When it runs.** At the start of `reserve_exam_pool` (so `get_exam_status` and the pool count are honest, and a pool emptied this way is reserved afresh, under the usual deferral rule) and in `start_exam` before anything is frozen. If every item is withdrawn at start, the error says why.
- **Reporting.** The report (`ExamPoolReport.withdrawn`, `as_dict()["withdrawn_note"]`), `start_exam`'s view (`withdrawn_items`, `withdrawn_note`), and the sidecar's `get_exam_status` and `start_exam` snapshots (`withdrawnItems`, `withdrawnNote`) carry the items, their reasons and one learner-facing line. The note reads: "N exam item(s) were set aside because you've already seen them since they were held out (an answer revealed, its exercise or solution read), so they would no longer be a fair test."
- **Not displayed yet.** The desktop UI does not render the note (no frontend change in this step; open question 1). The pool count it shows is already correct.

## F6: a kill switch, and no algorithm successor

**Reproduction.** As reported: the shown-material filters (exam pool, certification probe, cold retry) applied at every version with no switch, so no setting restored the predecessor's selection. F1 and F5 add two more serving rules of the same kind. This is a process requirement, not a behaviour defect. What can be tested is the switch and its parity, and what can be run is the rebuild validation; both follow.

**Fixed: the kill switch.**
- `goals.held_out_selection` (default `true`; `exam_material.held_out_selection_active`) governs every serving rule of the stage and this fix:
  - shown material never becomes an exam item, a certification cold probe or a cold retry;
  - an exposed exam item is withdrawn before the exam starts;
  - an item made from held-out material stays out of routine practice, picks and session serves, and is never a cold probe or retry.
- Off, each selection is the predecessor's. The tests compare against the predecessor's behaviour: the shown and held-out items are selected, served and administered again.
- The switch is read through one function (`exposed_items` for the shown/held-out item rules; `held_out_selection_active` for the routine exclusion and the doors). It never reaches what a model is shown, which is a privacy rule, not a serving change (`test_the_switch_never_reaches_what_a_model_is_shown`).
- The reservation check of gap (c) (a pick of an exam-reserved item) stays unswitched. It enforces the existing quarantine (`serving_exclusions` already never offered a reserved item) at a door that bypassed it.

**Rejected: the algorithm successor.**
- Handoff §0 rule 5 reads "a change to what is served is an algorithm successor with a kill switch". The owner's standing ruling, applied at UX Phase 1's landing on main (`c50dd0bcb`, `docs/reviews/ux-phase1.md`, "Versioning: the reading step is a live change, not a successor"), is narrower: serving changes that replay never reads are live changes behind kill switches, not successors. The facet-locks F6 ruling (`facet-reword-confirm-codex-review.md`) cites the same decision.
- These rules are such a change. They decide which item a selector offers or reserves (`exam_pool_items` and `remediation_episodes` are WORKFLOW, `followup_tasks` WORKFLOW). No replayer or projection calls `select_held_out_probe_item`, `start_remediation_treatment`, `reserve_exam_pool`, `start_exam` or the serving exclusions. Every attempt is still judged by its own coldness receipt when it is made.
- `SUCCESSOR_CHAIN` is unchanged (latest `mvp-0.19` on this base).

**The shadow-rebuild validation (run).**
- **Copies.** Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the worktree's three tracked fixtures, under `fixtures-local/exam-f6/`. Each was migrated to head 197 with `db.migrate.apply_migrations`: 155 → 197 for `linear_algebra` and `probability`, 152 → 197 for `arxiv_v2`.
- **Runs.** `learnloop rebuild --shadow --json` ran four times on each copy:
  1. HEAD (`1c7b70f25`) with the copy's own config;
  2. HEAD with `--set goals.held_out_selection=false`;
  3. HEAD with `--set goals.held_out_selection=true`;
  4. the predecessor `883b8da11` (a `git archive` on `PYTHONPATH`; probe: modules from the archive, `GoalsConfig` without the key).

| Copy | Version | Replayed attempts | Rebuilt LOs | Live vs replay rows (facet / mastery / schedule) | Four runs identical | Live DB sha256, before = after the runs |
|---|---|---|---|---|---|---|
| `linear_algebra` | `mvp-0.8` | 70 | 8 | 22 / 6 / 47 | yes | `b3c42510735ff1d9…` |
| `probability` | `mvp-0.8` | 2 | 1 | 2 / 1 / 1 | yes | `868475ae50dc8926…` |
| `arxiv_v2` | `mvp-0.8` | 3 | 3 | 2 / 34 / 3 | yes | `2066ad88474cbf42…` |

- **What differs between runs.** "Identical" means equal once the surrogate ULIDs the replay mints (the shadow marker id, the replayed family ids, which playbook step 6 ignores) and the echoed `applied_overrides` are set aside.
- **The diff rows are the baseline gap, not this change.** They compare each fixture's stored projections with a replay today. The predecessor reports the same rows with the same values, so the switch adds zero mastery, facet and schedule delta. Every run reported `live_database.unchanged: true`.
- **The head fixture too.** `test_replay_never_reads_the_switch` shows the same on `fixtures/migration_head_197` at the latest tag: every DERIVED table is identical after rebuilds with the switch on and off.

**Served-set probe on the same copies** (switch on against off, `build_due_queue(persist_explanations=False)` and the exam pool's candidates):
- **None of the three vaults is affected today.** No unit selection marks anything held out, `exposed_items` finds no shown item (`reveal_events` 0; `source_exposure_events` 4 in `probability`, none on an item's own exercise; no impressions), and no item is made from held-out material.
- **Results.** Today's queue is identical (41, 67 and 32 items). The linear-algebra goal's pool candidates are identical (33), and its 15 standing reservations are not withdrawn.
- **File state.** The probe's first pass changed the bytes of the `linear_algebra` copy's database file (the copies are disposable WAL databases; a second pass changed nothing), so that copy's hash in `fixtures-local/` no longer matches the table. The rebuild runs above were each before = after.

## Files touched

- `src/learnloop/content/sources/exam_material.py`:
  - F2's projection (`_label_occurrences`, `_held_out_units`);
  - F3's one partition (`_add_signals`, `held_out_material(vault_or_sets, repository)`);
  - F4's parser and check (`source_ref_keys`, `source_ref_protected`);
  - F1's items (`held_out_item_ids`, `held_out_items`, `HELD_OUT_ITEM_REFUSAL`);
  - F5/F6's `exposed_items` and `held_out_selection_active`;
  - `Material.touched` / `empty`.
- `src/learnloop/db/stores/source_block_fts.py`: `UnitRow.semantic_hash`.
- `src/learnloop/db/repositories.py`: `release_exam_pool_items`.
- `src/learnloop/scheduling/serving_exclusions.py`, `scheduling/scheduler.py`, `practice_index/admission.py`: the held-out routine exclusion.
- `src/learnloop/instructional/practice.py`: `refuse_protected_pick`.
- `src/learnloop_sidecar/serving.py`, `handlers/practice.py`, `handlers/queue.py`, `handlers/teach_back.py`: the session-serve door.
- `src/learnloop/goals/exam_pool.py`, `goals/exam_session.py`, `learnloop_sidecar/handlers/exams.py`: F5's withdrawal and its report.
- `src/learnloop/goals/certification_cold_probe.py`, `diagnosis/remediation.py`: through `exposed_items(with_held_out=True)`.
- `src/learnloop/ops/pf_generation.py`: F4.
- `src/learnloop/tutor/tutor_qa.py`, `reader/reader_dialogue.py`, `reader/reader_requests.py`, `content/pipeline/jobs.py` (`_reader_source_sets`): F3's source-set context.
- `src/learnloop/config/schema.py` (`GoalsConfig.held_out_selection`) and `config/template.py`: all eleven defaults snapshots recomputed with `defaults_fingerprint_for_version`; each moves only because the effective config gains the key.
- Tests: `tests/test_exam_protection_review.py` (new, 21 tests); `tests/test_reader_requests.py` and `tests/test_exam_protection.py` pass the source sets to `model_synthesis`.
- Docs:
  - the regenerated DB and config references (one more effective leaf: 788 → 789 in the two prose counts);
  - `docs/reviews/exam-protection.md` (§2.3's renamed function, §6 and §8 Q4/Q5 marked as settled here);
  - this record.

## Gate

Run on `f97724e29` (the code as committed; this record is the only later change), with `TMPDIR` set to the worktree's `fixtures-local/tmp`:

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9999 passed**, 0 failed, 0 skipped (6 min 42 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 9900 deselected |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (no schema change; one new effective config leaf); validate: no errors. `validate_vault.py`: passed (1097 notes) |
| frontend (`npm ...`), `cargo check` | not run: nothing under `apps/learnloop-tauri` changed |

- **First run.** The first full run (on `9554ff588`) failed two tests: `test_ingest_jobs.py::test_kick_reader_drain_runs_model_synthesis_foreground` and `::test_background_reader_drain_records_model_call_receipts`, 9997 passed. Their runner is bound to a bare directory, and the drain's new vault load raised, so the request failed. `dcc1b02bb` reads the source sets only where a vault exists, and the rerun above is clean.
- **Targeted runs before the gate:**
  - `tests/test_exam_protection_review.py`: 21 passed;
  - with `tests/test_exam_protection.py`: 45 passed;
  - 104 related test files (exam, reader, tutor, PF, leakage, serving, admission, picks, remediation, certification, scheduler, config and template, quick check, synthesis, corpus, find_sources, facet authority, source import, generation, teach-back, queue, daily plan, architecture, instructional, source service, placement): 1235 passed;
  - a further set of exam, goal, contamination, PF and source-block files: 411 passed.

## Open questions for the owner

1. **Showing the withdrawal note in the exam UI.** The note and the withdrawn items are in `get_exam_status` and the `start_exam` snapshot, but `ExamStatusSnapshot` / `ExamSessionSnapshot` (`apps/learnloop-tauri/src/api/dto.ts`) do not declare them, so the desktop does not show them yet. Recommended default: render the note on the goal banner and the exam's first screen in a frontend follow-up.
2. **Label projection across revisions (F2).** A mark in one extraction withholds *every* same-labelled unit in the others, unless the other extraction marks the same unit (same occurrence and content). With repeated labels ("Exercises" in every chapter) this withholds more than the owner marked, and with F1 it keeps those units' imported items out of practice too. Recommended default: keep (fail closed); a structural mapping (label path plus content hash) could narrow it later.
3. **A protection behind a switch (F6).** The serving rules can now be turned off. The model-context protections cannot. Recommended default: keep as built.
4. **Exam-reserved items as cold probes or cold retries** (seen while fixing, not a review finding, not changed). `select_held_out_probe_item` and the cold retry do not exclude an item reserved for a goal's exam. The routine queue never serves a reserved item, so the likely outcome is a probe task that waits rather than a leak; this was not traced end to end. Recommended default: exclude exam-reserved items from both in a follow-up.
