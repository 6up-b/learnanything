# UX-40: a finished section's questions apply, and held for review is not failed

Branch `fix/ux40-section-questions-apply`, from main `746335c4a0`.

## The measurement

A rerun of a walk's vault on the real model route (numbers and field values only; this step read no vault and made no model call). After a book's build, a finished section's questions were written topic by topic (UX-37): each topic one authoring call of about 130 s and 6,400 output tokens giving 3 practice items, then six persona-gate judge calls. Every item, 9 of 9 over three topics, came back with `review_route = "review_required"`. Each row was valid (no validation error), its audit status was `passed`, the persona gate's decision was `pass`, and it cited one source reference of `ref_type` `canonical_source` (the Reader's citation of the section's passages, with span ids and a quote). Nothing applied: the three part proposals stayed `pending`; the job recorded for each topic the error "Questions need review before applying" and ended failed; its message stayed "Writing questions: 0 of 7 topics finished"; the learner had no practice. The house doubles answer `auto_apply`, so no test saw it.

## Step 0 (written before any code change)

The rule the brief calls `effective_review_route` is `evaluate_review_policy` in `src/learnloop/content/proposals/proposals.py` (no function of the brief's name exists). The row flag is `proposal_item_row`'s `"_auto_apply": validation_status == "valid" and review_policy == "auto_apply"`; gates can only turn it off.

### a. Who sends this prompt, and what happens to a row the model marks `review_required`

The line is in `_practice_expansion_instructions` (`content/authoring/practice_generation.py`). It is built in two places: `generate_post_probe_practice_proposal` (per topic for a section, once for the whole plan otherwise) and `generate_goal_practice_proposal`. The prompt carrying it is `authoring_prompt` (`content/proposals/ai_contracts.py`): the instructions ride in `context.instructions`. `_cross_source_instructions` (the cross-source route) does not carry the line.

Where a held row goes, for every caller: it is persisted as a `pending` row of a `proposed_patches` batch (`proposed_patch_items`, `decision = 'pending'`); it is never written to the vault, so it is not practisable. It is shown in the desktop's Library (the proposals list in the tree, opened with its payload in the editor) and the Proposals screen (`ProposalsScreen.tsx`, `PayloadPreview`): both show the whole payload, `prompt`, `expected_answer` and `grading_rubric` included, so **a learner who looks at it sees the expected answer before having tried the question**. To get it, the learner must accept it there (or edit, or reject). The phone and Today have no review surface (Today says "“…” needs a look in your Library."). The Proposals screen's route pill reads `auto_apply` for every valid practice-item creation (the sidecar's `_review_route` ignores the model's flag, grounding, the audit and collisions), so a held row shows a green `auto_apply` pill while pending, and "accept all auto_apply" takes it (ledger UX-40b). The model's per-item `rationale` is not stored on the row (`proposed_patch_items` has no such column; `_item_dto` shows the batch summary as every row's rationale), so a reviewer never sees why the model held it.

| Caller | How it reaches the line | Supplied `context.source_refs` | A `review_required` row |
|---|---|---|---|
| A finished section (desktop "Done with this section" or its quick check; the phone's; a section waiting for its build, `jobs.start_waiting_sections`; the sidecar's drain of owed sections, `section_questions.py`) | `practice_expansion` job, reason `reader_section_completed:<section>` → `handle_practice_expansion` → `generate_post_probe_practice_proposal(..., checkpoint_scope=…)` → one part per topic → `_apply_authoring_parts` | the section's passages, `canonical_source` (or a note), merged into the proposal | pending; **before this fix the topic got the error "Questions need review before applying", the job ended failed (`ValueError`, not retried), Today said "Couldn't write the questions…" with a Try again that asks nothing** |
| Starter practice for empty topics (`generate_starter_practice`, goals.py; reason `learner_requested_starter_practice`) | `practice_expansion` job, whole plan in one call | none (payload `source_refs` empty) | pending in the batch; job completes |
| Maintain's commissioning gaps (`generate_commissioning_practice`, measurement.py) | `practice_expansion` job, whole plan | none | pending; job completes. The screen promises review: "authored items land in Proposals for review as the batch completes" (MaintenanceScreen.tsx), and the handler's docstring says "never applied silently" |
| An adaptive-difficulty commission (`daily_plan._commission_enqueue` → `enqueue_practice_expansion(ad_commission_id=…)`) | `_handle_ad_commission` → `generate_post_probe_practice_proposal`, one item | none | pending; the commission stays open until an item lands |
| "More questions" on a missed attempt's primed retry (`start_primed_retry`, feedback.py) | `generate_post_probe_practice_proposal(max_new_per_lo=1)` then `accept_items(root, patch_id)` with no ids | none | **accepted anyway**: `accept_items` with no ids takes every pending valid row, so the route does not matter |
| CLI `learnloop generate-practice` | `generate_post_probe_practice_proposal` | none | pending; printed for `proposals` review |
| Goal population (`goal_population` job from the goal wizard; CLI `populate-goal`) | `generate_goal_practice_proposal` | none | the job and the CLI without `--review` call `accept_items(root, patch_id)` with no ids: **accepted anyway**; with `--review`, pending |

No "more questions" action other than these reaches the line (`generate_starter_practice` is the only learner-facing "write questions for this topic" press; the Reader's per-section questions are this practice route).

**Is applying a grounded, audited, gate-passed question without review wrong anywhere?** For the finished section, no: the learner asked for practice on what they just read, the items cite the passages they read, every gate ran, and the review surface shows the answer first. For primed retry and goal population the route is already moot (they accept every valid row). **Maintain's commissioning is the one caller whose screen promises review.** The new wording therefore applies only where references are supplied in `context.source_refs`, which only the finished-section route supplies; on every other caller `context.source_refs` is empty and the line leaves its items `review_required` (the code also routes an item without a direct, resolvable, supplied-or-declared reference to review). The old line's "a direct note … in the supplied context" could be read to include the context's notes; the measured model did not, so in practice nothing changes there. (Whether Maintain's items should apply is not this task's; its docstring and screen already disagree with the code for any row a model marks `auto_apply` on its own.)

### b. Other authoring prompts that tell the model when to choose a review route

Searched every prompt-building module (`grep review_route|auto_apply|review_required` in `src/`, then each hit that is prompt text). Two lines exist:

1. `content/authoring/practice_generation.py`, `_practice_expansion_instructions` (this task's): "Use review_route='review_required' unless a direct note or canonical source reference in the supplied context supports auto_apply."
2. `content/authoring/practice_generation.py`, `_diagnostic_practice_instructions`: "Use review_route='review_required'; generated diagnostic probes must be reviewed before writing vault content."

Line 2 does not have the wording problem: it is an unconditional rule that matches the code (`evaluate_review_policy` with a diagnostic context never auto-applies; `_diagnostic_proposal_item_row` forces `_auto_apply = False`). Not changed. No other prompt names the route: `authoring_prompt`'s task text, `EXERCISE_AUTHORING_PROMPT`, the probe, teach-back, tutor-promotion and synthesis prompts say nothing about it (their routes are set in code: `graph_edit_proposals.py` writes `"review_route": "review_required"` itself; tutor promotions, rung variants and synthesis decide in code). So only line 1 had the problem.

### c. What `evaluate_review_policy` requires for `auto_apply`, and what the measured rows met

In order (ordinary authoring, `context=None`):

1. The model's route is not `reject` — met.
2. Every cited `source_ref_id` resolves (`_unresolved_source_ref_ids`) — met (valid rows; an unresolved ref is also a validation error).
3. `operation == "create"` and `item_type` in learning_object / practice_item / concept_edge — met (practice_item creates).
4. At least one `source_ref_id` — met (one each).
5. Direct grounding: every cited ref that is in the proposal's refs is `note` or `canonical_source` (`_has_direct_grounding`) — met (`canonical_source`).
6. No id collision with the vault (`_has_id_collision`) — met (valid; a collision is also a validation error).
7. The generated-practice audit: present, not `failed`, and a `not_applicable_with_trace` audit carries its trace (`_generated_practice_audit_error`) — met (`passed`).
8. **Last: the model's own `review_route == "auto_apply"`** — **not met**: the only condition the rows failed.

Then the row flag needs `validation_status == "valid"` (met), and the gates must leave it on (persona decision `pass`; nothing refused). Every condition the code checks held except the model's flag.

## Commits

| Commit | What |
|---|---|
| `361c0175e7` | This record's step 0, before any code |
| `9524e5252f` | Held for review is not failed (`_apply_authoring_parts`), the realistic doubles and their tests |
| `aa78518d17` | The prompt line, its test, and the one-topic section's request pin |

This record's remainder and the ledger rows are the last commit.

## Judgment calls to read first

1. **The new wording names `context.source_refs`, not "the context".** Step 0 (a) found one caller whose screen promises review: Maintain's commissioning ("authored items land in Proposals for review"). Only the finished-section route supplies references in `context.source_refs`; on every other caller it is empty, so the line leaves their items `review_required`. The old line's "a direct note … in the supplied context" could be read to include the context's notes; the measured model did not use that reading, so nothing changes there in practice.
2. **"Audit passed" is said as the code checks it.** `_generated_practice_audit_error` accepts an audit of status `passed`, and one of `not_applicable_with_trace` with its trace (the base prompt tells the model to use that status for conceptual items without a deterministic check). The line says "its audit is passed (or not_applicable_with_trace with a trace)"; "passed" alone would send every conceptual item back to review.
3. **No version constant bumped.** The instruction block has no version of its own. The prompt carrying it is `authoring_prompt`, whose `AUTHORING_PROMPT_VERSION` is rendered into every authoring prompt (whole-call authoring, the section pin's fixed-instruction key, and others): bumping it would move pins this line does not move, which the brief makes a stop. `PRACTICE_GENERATION_PROMPT_VERSION` is recorded only by the cross-source route, which does not carry this line. Reuse is still safe: each authoring answer's checkpoint key hashes the rendered prompt, which now differs. One consequence: a section job started before this change keeps its frozen `:requests` snapshot (UX-33), so its Try again sends the old line; its saved part proposals are reused as before (a held part is now finished on resume, so such a job completes).
4. **"Held for review" is any pending row that is not `invalid`.** Gates refuse by setting `validation_status = "invalid"` (surface gate, rung gate hard tier, persona gate block, pair gate, duplicate prompts); an advisory persona flag or a gate's remediation sets `warning` and sends the row to review. A `warning` row is written, acceptable and waiting for a look, so it counts as held, not failed. A part with any invalid pending row (or no rows at all) keeps today's error, failed state and Try again; its error text is unchanged (all pending rows' reasons).
5. **The model's rationale is not shown to a reviewer.** The line asks the model to say in its rationale what is unchecked, as the brief requires, but `proposed_patch_items` has no rationale column and the Library shows the batch summary as every row's rationale. Surfacing it needs a stored field (a schema change), so it is named here and in ledger UX-40b, not done.

## The prompt line

`src/learnloop/content/authoring/practice_generation.py`, `_practice_expansion_instructions`, the fifth line; no other line changed:

- Old: "Use review_route='review_required' unless a direct note or canonical source reference in the supplied context supports auto_apply."
- New: "Set review_route='auto_apply' on an item when every one of its source_ref_ids is a note or canonical_source reference supplied in context.source_refs and its audit is passed (or not_applicable_with_trace with a trace); use review_route='review_required' only for an item you could not fully check against the passages it cites, or that relies on something outside them, and say in its rationale what is unchecked."

No schema field, config field, gate or `evaluate_review_policy` condition changed. No migration. **No algorithm tag**: no persisted meaning of scoring, scheduling or projections changes. The line changes what the model is asked; the stored rows' meaning, the review policy and every gate are as before, and an applied question is the same kind of row the policy already applied (`docs/algorithm-change-playbook.md` covers changes to persisted meaning).

## Pins that moved

- **The one-topic section's request bytes** (`tests/test_section_question_parts.py::test_one_topic_request_bytes_and_checkpoint_reuse`, UX-33): `37a5f8e07262bc797fe344c59601ad0387b65a895e24cb10e92678d4a0208c4b` → `3ee763d8f71b89d1638787d9d5fa1328cfcd14aff21ba29f8b20c752fed72897`. Checked that the line is the whole difference: the two recorded requests (old and new source, the same synthetic one-topic section) differ only in `prompt`, the old prompt contains the old line exactly once, and replacing it with the new line gives the new prompt byte for byte. Schema, purpose, timeout, budgets, workspace, isolation, effort and images are equal.
- **Identity pins (`tests/test_identity_pins.py`): none moved.** The registered section-authoring answer key renders `authoring_prompt` with fixed instructions ("Write three questions for lo_pin_svd."), not `_practice_expansion_instructions`; no other registered identity renders this line. The suite passed (345, then 347 with the two prompt tests) on the new line, and `python tests/test_identity_pins.py --write` through the wrapper rewrote nothing (`git status` clean afterwards).

## Held for review versus failed, before and after

`_apply_authoring_parts`'s `describe` decides a saved part's state after its rows were persisted and its auto-apply rows applied.

| A topic's rows after apply | Before | After |
|---|---|---|
| All applied | finished | finished (unchanged) |
| Some applied, the rest pending and valid (or `warning`): held for review | error "Questions need review before applying" (or the warnings joined); not counted done; job ends failed (`ValueError: Questions need review for …`); `questions.failed` names the topic; Try again reuses the saved proposal and asks nothing | finished: no error, counted in the progress amount, not in `questions.failed`; the job completes; its pending rows count in `questions.to_look_at` as before |
| None applied, all pending and valid: held for review (the measured case) | as above, and Today showed "Couldn't write the questions…" | as above: finished, waiting for a look |
| Any pending row `invalid` (refused by a gate, a duplicate prompt, a validation error) | error with the rows' reasons; job failed | unchanged |
| No rows | error | unchanged |
| A model failure (timeout, invalid JSON) | the topic's error; curable; automatic retry | unchanged |

The section's completed checkpoint is saved as for any completed section, so a later identical rebuild returns it without a call; the held rows stay in the review queue.

## Today after the change

From `apps/learnloop-tauri/src/app/todayCause.ts` (unchanged; the facts it reads changed). "Questions ready" means some of the book's applied questions are on today's list (desktop); the phone reads no list and uses the written count.

| Facts after the section's writing ended | Today state, before | Today state, after |
|---|---|---|
| Applied questions on today's list, and some questions to look at (`count > 0`, `to_look_at > 0`, no failed topic) | `questions_ready_with_section_work` with "Not every topic's questions could be written." and a Try again that asks nothing | `questions_ready`: "N questions from “Section”, the part you read. More come as you finish sections." with Begin; the questions to look at are not mentioned |
| Same, none on today's list | `section_failed` ("Couldn't write the questions from “Section”…", Try again) | `none_up` ("Nothing from “…” is up today…"), or `finish_section` if another book has none finished; nothing about the questions to look at |
| Only questions to look at (`count = 0`, `to_look_at > 0`, nothing failed: the measured case) | `section_failed` with Try again (asks nothing) | `needs_look`: "“…” needs a look in your Library." with Open Library (only after every ranked cause and list offer; the phone says the same sentence) |
| Questions to look at and another topic failed (a refused row, or a model failure), nothing on today's list | `section_failed`, naming both topics | `section_failed`, naming only the failed topic; Try again resumes it; the questions to look at are not said |
| Questions to look at and a failed topic, some applied ones on today's list | `questions_ready_with_section_work` + "Not every topic's questions could be written." | the same state and line, for the failed topic only |
| While still writing, a topic held for review, nothing yet on today's list | `section_failed` ("Couldn't write the questions from “Section: Topic”…", ranked above the writing line, with a Try again that requeues nothing while the job runs) | `section_writing`: "Writing questions from “Section”, the part you read · 1 of 3 topics done" |
| While still writing, a topic held for review, some applied ones on today's list | `questions_ready_with_section_work` + "Not every topic's questions could be written." (no Try again while writing) | `questions_ready_with_section_work` without the failed line: "… are ready. More are being written (1 of 3 topics done)." |

**Missing for the frontend (no frontend file changed):**

1. No sentence says that a section's questions wait for a look when some of them are offered (`questions_ready`), none are up (`none_up`), or a topic also failed (`section_failed`): `toLookAt` is read only where nothing was written (`count === 0`). A line such as "N more wait for a look in your Library." beside the offer is missing.
2. `needs_look`'s sentence ("“…” needs a look in your Library.") does not say that it is questions written from the section, nor that looking at them shows their answers (step 0 a): a learner who wants to practise them should accept them unseen, which no screen offers. A state such as `questions_to_look_at` with words like "N questions from “Section” wait for your OK in your Library" and an accept-without-showing action is missing.
3. The Proposals screen's `auto_apply` pill on held rows (ledger UX-40b).

## Tests (fail first)

Every test ran first against the unchanged production code (the base `746335c4a0` sources for the first six; the old prompt line, restored from `HEAD` into the working tree and put back after, for the prompt test). One run, `-vv`: **6 failed, 1 passed** (the passing one was the request pin, a preservation guard).

| Test | Failure on the unchanged code |
|---|---|
| `test_section_question_parts.py::test_grounded_questions_the_model_holds_for_review_wait_for_a_look_and_the_section_completes` (3 topics, the double marks all 9 grounded, audited questions `review_required`) | `{'code': 'ValueError', 'message': 'Questions need review for lo_topic_f, lo_topic_b, lo_topic_e'}`, `'failed' == 'completed'` |
| `…::test_one_question_of_three_held_for_review_leaves_two_applied_and_the_topic_finished` (one topic, its third question held) | `{'code': 'ValueError', 'message': 'Questions need review for lo_topic_f'}`, `'failed' == 'completed'` |
| `…::test_a_held_question_beside_a_refused_one_still_fails_its_topic` (topic 1: one applied, one held; topic 2: one refused duplicate, one held) | `'error' not in {'error': 'Questions need review before applying', …, 'topic_id': 'lo_topic_f'}`: the first topic failed. After the fix only topic 2 fails (the guard that refusal keeps today's treatment) |
| `test_first_questions_today.py::test_a_topic_whose_questions_wait_for_a_look_is_finished_not_failed` (a built book, a finished section, the real section job with the all-held double; facts read during the second and third calls and after) | progress while writing `{'done': 0, 'total': 3}` where `{'done': 1, …}` was expected |
| `test_first_questions_today.py::test_two_questions_applied_and_one_to_look_at` | job `'failed' == 'completed'` |
| `test_section_question_parts.py::test_the_request_states_when_a_grounded_question_applies_without_review` (the built request's review line, asserted on its meaning-bearing phrases) | `assert "review_route='auto_apply' on an item when every one of its source_ref_ids" in "Use review_route='review_required' unless a direct note or canonical source reference in the supplied context supports auto_apply."` |
| `test_section_question_parts.py::test_one_topic_request_bytes_and_checkpoint_reuse` (the existing pin) | passes on the old line; on the new line before the pin was updated: `'3ee763d8f71b…0c752fed72897' == '37a5f8e07262…678d4a0208c4b'` |

The doubles (`tests/section_question_parts_helpers.py`): `answer`/`Writer` gain `per_topic` (questions per topic), `held` (positions the model marks `review_required`, with a rationale saying they are grounded and audited), `repeated` (positions whose prompt repeats across topics) and `facet`; `held_writer()` is the live route's answer (three per topic, all held); `topics_in()` puts the section's topics and note into a built book's library. Each held row is valid, cites the section's note (`ref_type` `note`, direct grounding; the measured rows cited `canonical_source`, which the same condition accepts), carries a `passed` audit, and passes every gate. In the built book's library the facet is taken from its registry (with the basic vault's `recall` every row was `unknown_evidence_facet` and the test would have failed for the wrong reason; seen once while building the test, not counted).

No existing assertion changed except the request pin's value, moved by the line.

## What I ran

Every Python run through the scratch wrapper (`env -i`, empty `HOME`, `CODEX_HOME` and config dir), every pytest run as `uv run --no-sync pytest -q -n 1 -p no:cacheprovider <explicit files>` from a script that refuses an empty target list, in `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=1G`, one at a time. No run was killed. All on the final code (`aa78518d17`; the record and ledger change no code).

- Fail-first, as above: **6 failed, 1 passed**; the prompt test on the old line: **1 failed, 1 passed** (with the request pin).
- After the held-for-review commit: the new tests, **6 passed, 1 failed** (the prompt test, still on the old line); `test_section_question_parts.py`, `test_first_questions_today.py`, `test_first_questions_arrive.py`, `test_contrast_pairs.py` with `-m "not arc_close"`: **91 passed, 1 failed** (the same prompt test); `test_identity_pins.py`: **345 passed**.
- After the prompt commit: the prompt test, the request pin and `test_identity_pins.py`: **347 passed**; `python tests/test_identity_pins.py --write`: no file changed.
- `scripts/affected_tests.py --files` the two changed source files listed **261** files (over 150), so I ran the brief's name filter instead: every `tests/test_*.py` whose name contains `practice_expansion`, `practice_generation`, `authoring`, `proposal`, `review` or `section` (130 files, `test_section_question_parts.py` among them), in four chunks with `-m "not arc_close"`: **609 passed**; **645 passed**; **771 passed, 1 xfailed**; **405 passed**. Then the files outside that filter that read this prompt or route (`test_ad23_fix_r5`–`r8`, `test_practice_leakage`, `test_required_method_items`, `test_teach_back_generation`, `test_persona_gate`, `test_sidecar_measurement`) with `test_first_questions_today.py`, `test_first_questions_arrive.py` and `test_contrast_pairs.py`: **274 passed**.
- `test_identity_pins.py`, `test_retired_config_identities.py`, `test_diagnosis_journey_golden.py`, `test_structure_ratchets.py`, `test_mobile_allowlist.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`: **759 passed** (no pin, golden or ratchet moved).
- `test_test_layout.py` alone: **3 passed**. `test_architecture.py` alone: **18 passed**.
- `ruff check`: **All checks passed!** `lint-imports --no-cache`: **Contracts: 43 kept, 0 broken.** `scripts/check_gate_partition.py`: **collected 31929: landing 31864 + arc_close 65**. `git diff --check`: exit 0.

## Not verified

- **Whether the real model follows the new line.** No live or paid call was made; the orchestrator checks it on the real route.
- No app, browser, server or Today screen ran: the Today table is read from `todayCause.ts` against the facts the tests produce.
- A section job started before this change resumes with its frozen request snapshot (the old line) on Try again; read from the code, not run.
