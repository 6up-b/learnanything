# Refactor K1 fixes: the six protection bugs K1 found

Step "K1's protection fixes" (strategy §2.17: "Fix before G6"), branch `refactor/k1-protection-fixes`, based on main `ff8b42530b`. Rows K1-1, K1-3, K1-4, K1-5, K1-6, K1-7 of `docs/reviews/refactor-bug-ledger.md`. K1-2 (the Reader import and exam material) is the owner's call and is untouched. None of these changes scoring, scheduling policy or projections; K1-3 and K1-6 change which item the learner is *served* in the cases K1's record named (R1, D6). Each row has a fail-first test, shown failing at the base tip (the fix reverted) and passing with it.

## K1-1: exam material fails closed when the source sets did not load (`885f875096`)

- **Tests** (`tests/test_k1_source_sets_gate.py`, 24 cases; each corruption is unparseable, schema-invalid, empty and truncated mid-key): `test_every_shared_reader_refuses_unloaded_source_sets` (`exam_material`, `held_out_partition`, `held_out_material`, `role_material`, `exam_withheld`, `spans_withheld`), `test_the_tutor_figures_and_phone_withhold_when_source_sets_did_not_load` (`teaching_exclusions`, `exam_exclusions`, `teaching_scope`, figures' `withheld_message`, `phone_withheld` returning the whole reading), `test_the_exercise_import_and_the_facet_resolver_refuse`, `test_the_source_sets_write_never_leaves_a_truncated_file`. At the base tip every shared reader returned "no exam material" for all four corruptions (18 of 24 cases failed; the other six are the valid-file and premise cases, which pass before and after). A valid file behaves as before (`test_a_valid_file_still_reads_the_exam_member_as_exam_material`).
- **Fix.** `protection_issues` and `SNAPSHOT_UNSETTLED` move from `learner_protection` into `content/sources/exam_material.py` (a leaf, so the check can sit in the shared read); `learner_protection` re-imports both, so its four readers (`withheld_items`, `learner_context`, `remote/views.py`, section coverage) are unchanged and read the same function. `exam_material`, `role_material` and `held_out_partition` call `_require_readable` first and raise `SourceSetsUnreadable` (callers already treat an exception as "withhold"). `source_marks` (the book card's bookkeeping, K1 §5) is not gated. The check applies only to an object that has a `root` and `source_sets` (a vault): bare source-set lists carry no file to check.
  The callers that passed bare lists now pass the vault: `source_set_synthesis` (`exam_material(vault, ...)`), the facet resolver's `exam_source_sets` (it takes the vault; `for_vault` passes it), and the Reader's `_reader_source_sets` (returns the loaded vault). The exercise import turns the exception into a `rejected` import with a reason (`fail(...)`) instead of leaving its row open.
  `source_sets.yaml` is written by `write_yaml_atomic` (`vault/yaml_io.py`: temp file in the same directory, fsync, rename, directory fsync). It is a small copy of `evsi_calibration.artifacts.write_text_atomic`, because importing that module from `vault/` breaks the "no cycles" import contract; `write_yaml` stays as it was for every other file.
- **Not asking twice.** `withheld_items` still stops at its own `protection_issues` check and never reaches the shared read (`test_the_readers_that_already_asked_still_refuse_and_ask_once` counts one call).
- **Checked.** 3,031 related tests pass (every test file that mentions exam material, source sets, learner protection, the resolver or `upsert_source_set`). A hand-edited file cut at a member boundary parses as fewer members and cannot be told from the owner's intent: ledger row K1-8.

## K1-3: the session serve door refuses an exam-reserved item (`be926eca26`)

- **Test** (`tests/test_k1_serve_door_reservation.py`): a reserved item at `refuse_held_out_item` raised nothing at the base tip; it now raises `SidecarError` with code `exam_reserved`, with the same sentence a reserved pick gets (`EXAM_RESERVED_PICK`). A second test pins that the refusal does not follow the `goals.held_out_selection` switch (as `refuse_protected_pick`, and as K1 D7 says reservations are not switched), and an unreserved item is served.
- **Fix.** `refuse_held_out_item` checks `exam_reserved` before the switch. The exam's own screens do not go through this door (`handlers/exams.py` has its own sitting and answers), and the 2,192 tests that touch the exam pool, `get_practice_item` or the serve doors pass.

## K1-4: MCP `find_sources` (`d660d565c2`)

- **Tests** (`tests/test_k1_mcp_find_sources.py`): a probe item's own passage, and a problem-set (assessment-lane) passage, were both returned at the base tip; now each is dropped and counted (`held_for_a_check`, `exam_material`).
- **Fix.** `_PROTECTING` names the four withheld reasons through `learner_protection`'s constants (the literal strings had no probe). `_shown` also asks `corpus.model_reader_withheld` (the rule the tutor's library scope uses): `assessment_lane` counts under `exam_material`, an effective-role `solution` under `solutions`.

## K1-5: the inspector hides the hints of the question being answered (`7cd48b12c0`)

- **Test** (`InspectorOverlay.phase4.test.tsx`): the hints of the item open on the practice screen showed in simple and classic mode; now neither shows them; an item that is not open still shows them.
- **Judgment call.** The design choice was hide or count as a reveal; I chose hiding, while the item is being answered, in both modes (classic still shows the key and rubric "as before", a recorded UX decision). I did not hide hints of an item never answered but not open, nor did I touch the server: `inspect_entity` still sends them (K1 R4 and R9's server-side variant are the UX stage's payload split).
- **Checked.** `npm run typecheck`, the inspector tests and the two tests that read the overlay.

## K1-6: a remediation's cold item is reserved when chosen (`742308f515`)

- **Tests** (`tests/test_k1_remediation_cold_reservation.py`): with an episode in `treatment` and no `cold_retry` task yet, `cold_administration_open` was False and `out_of_timing_serving_exclusions` left the item out of `cold_check_reserved_item_ids`; both now hold it. A completed or abandoned episode reserves nothing. `COLD_TASK_KINDS` is `serve_eligibility.COLD_FOLLOWUP_TASK_KINDS` itself (one definition; `learner_protection` iterates it sorted).
- **Fix.** `Repository.open_remediation_cold_item_ids()` is the one query (`state NOT IN ('completed','abandoned')`, what `learner_protection` already read inline); `cold_administration_open`, the out-of-timing exclusions and `withheld_items` use it. This is the change in what is served K1 D6 named: Today's queue no longer offers the cold item as ordinary practice between the episode choosing it and its check.

## K1-7: docstrings (`8e2dfad2d4`)

Rule 4 in `exam_material.py` no longer says "no search hit" (the library search applies no protection filter: the snippet reaches the learner's screen, the query is all a model reads). The module's closing paragraph and `figures.service.withheld_message` now say figures refuse all exam material, wider than the Reader's held-out-only Ask. No code changed.

## Not verified

Whether the desktop sidecar's callers of `exam_material` all surface a `SourceSetsUnreadable` as a refusal rather than a generic error (each already treated an exception as "withhold"; the new tests assert the raise, and the related suites pass, not each handler's message).
