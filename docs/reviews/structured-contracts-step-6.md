# Structured contracts, step 6: blank live dialogue

Status: **teacher adopted with baseline consecutive-failure outcomes preserved; teach-back and tutor remain unadopted pending owner decision SC-1**.
The latter two production paths are unchanged, including their blank-reply bugs. No allowance was invented.
No commit or index update was made. The untracked design reference was read, not modified.

## Baseline and bounded admission

Before any production edit, `test_live_dialogue_contract_baseline.py` ran the real services, common transport and
OpenAI chat completion/schema-repair code, with only the SDK replaced by `tests/openai_fakes.py`.
Result: **32 passed in 2.53s**. Initial fixture mistakes (a missing required tool facet list and modeling a terminal
timeout as a retryable SDK timeout) were corrected before that capture. Physical counts below count SDK requests,
not calls to `complete`. No real model or network was used.

`RecordingChat` records the active gate at the real service/transport boundary. Teach-back's `next_question` and
tutor's `ask_question` arrive with **no request gate**. Their sidecar handlers likewise install no spend/recovery
envelope around these calls. The follow-up cap and Q&A caps count delivered learner questions; output-token limits,
provider timeout and general model-use permission do not authorize another physical request. A provider's existing
schema repair is not evidence of a caller-owned contract retry slot. All ten tutor selectors reach this boundary.
Both surfaces remain unadopted under the task's bounded-admission rule; their baseline tests remain characterization of today's behavior.

The teacher's real `_lesson_spend` installs a `LessonSpendGate`. The recorder proves both contract attempts use
that same gate; each actual metered request, including schema repairs, has a committed `spend_reserved` and a
settled `spend` row. A depleted real gate refuses the correction before the SDK sees it and closes with `budget`.
No synthetic recovery funds, count cap or gate were added.

## Orchestrator rulings

1. Teach-back and tutor stay unadopted. Open owner question: **may the tutor and teach-back send one extra request
   for a blank reply, counted as part of the learner's own question, given that neither call has a spend envelope
   today?** Ledger [SC-1](refactor-bug-ledger.md) is open. The defects remain: a blank teach-back question is appended
   and consumes a follow-up; a blank tutor reply can be recorded and shown.
2. Teacher preservation wins over the design reference's proposed two-send exhaustion policy and the earlier
   worker's implementation. The shared re-ask is the first recovery of a blank; another blank returns to the
   existing consecutive-failure loop. Each rejected blank consumes one existing failure slot, so the shared re-ask
   replaces a loop retry instead of adding one. This preserves the old three-turn ceiling, including mixed failures.
   Only the deliberate whitespace fix changes the baseline rows below.

## Teach-back question — stopped

Intended contract: `question_md` is non-blank after the existing ANSI/control-character sanitizing and whitespace
check. Proposed fixed requirement, **not installed or sent**:

> Provide a non-blank student question in the question_md field.

Only `TeachBackQuestion` belongs to this adoption. `TeachBackAuthoring` is the separate generated-content family.
There is no existing recovery admission, caller-wide deadline or cancellation callback to map here. The current
provider failure propagates as `CodexUnavailable`/timeout: the sidecar sets `question = None` and finishes/grades
the partial transcript. The question is not appended and `asked_count` does not advance in that failure path.

| Case | Before physical requests / learner outcome | After physical requests / learner outcome |
|---|---|---|
| Valid first | 1 / question shown, asked count +1 | same |
| Blank then valid queued | 1 / blank shown, asked count +1; valid unused | same (stopped) |
| Blank twice queued | 1 / blank shown, asked count +1 | same (stopped) |
| Whitespace | 1 / whitespace shown, asked count +1 | same (stopped) |
| Malformed then valid | 2 / repaired question shown, asked count +1 | same |
| Terminal deadline after first send | 1 / provider failure, asked count unchanged | same |
| Terminal interruption after first send | 1 / provider failure, asked count unchanged | same |
| Tool-only intermediate | N/A: this schema has no tools | N/A |

An additional stopped-path test captures an ANSI/control-only question becoming exactly empty while still advancing
the count. Production is still unadopted on this surface. No checkpoint, receipt or question persistence changed.

## Tutor final reply — stopped

Intended contract: a final reply has content that actually survives the existing display processing. A tool-only
intermediate answer remains legal; an allowed/verified Reader excerpt or bridge can also be displayed content, so
an unconditional `answer_md.strip()` would be wrong. Proposed fixed requirement, **not installed or sent**:

> Provide non-blank learner-visible content for a final reply, or request an allowed tool for an intermediate reply.

No new transcript, rejected output, hidden record or authority would be carried by this line. Its final predicate
must still use the caller's actual display rules when an admission envelope is supplied.

| Case | Before physical requests / learner outcome | After physical requests / learner outcome |
|---|---|---|
| Valid first | 1 / answer recorded and shown | same |
| Blank then valid queued | 1 / blank recorded as answered; valid unused | same (stopped) |
| Blank twice queued | 1 / blank recorded as answered | same (stopped) |
| Whitespace | 1 / whitespace recorded as answered | same (stopped) |
| Malformed then valid | 2 / repaired answer recorded and shown | same |
| Tool-only intermediate | 1 / typed request returned, empty prose allowed; no re-ask | same |
| Terminal deadline after first send | 1 / failed question row, `answer_md = None` | same |
| Terminal interruption after first send | 1 / failed question row, `answer_md = None` | same |

The bounded tool-only fixture was built and passed **before adoption work**, through the real provider parser and
`request_tutor_answer`, with all five tool-bearing selectors. It is not re-asked. The five corresponding no-tool
selectors are valid-first controls. Covered selectors are `TutorAnswer`, `ReaderTutorAnswer`,
`ReaderTutorExplorableAnswer`, `ReaderTutorShowMeAnswer`, `ReaderTutorExplorableShowMeAnswer`, and each `WithTools`
variant. All are excluded from production adoption for the same missing admission, not because blank final prose
is valid. Verified excerpt/bridge-only display behavior has not been newly tested here; it remains required for
that adoption. The preview opening also uses the same unadopted request function.

The current failure path finishes the agent run as failed and leaves the learner's question recorded with no answer.
The sidecar retains its existing `provider_unavailable` wording: “<provider> is unavailable for tutor Q&A.”
No answer checkpoint was introduced or changed. The blind grader was untouched.

## Teacher turn — adopted

`TEACHER_MESSAGE_CONTRACT` requires `bool(turn.message.strip())`, before transcript recording, display or actions.
All eight combinations of base/visuals, episodes, and TE2 use it. A check, prediction, visual, plan or close request
with no message is rejected too, as required by this step's message contract. Tool-only tutor permissiveness does
not apply to teacher actions.

The predicate name is `blank_message`; the exact fixed requirement is:

> Provide a non-blank learner-visible message in the message field.

The shared correction format appends this requirement to the original prompt. No rejected turn, transcript excerpt
or new hidden context is interpolated. The first prompt builder, selected schema, purpose and initial request's
`timeout_seconds=None` are unchanged. Tests compare the sent first request with the original builder output and
the correction with `correction_prompt`; existing identity pins remain unchanged.

Admission checks the live lesson's existing gate and remaining consecutive-failure room. The physical provider
request then reserves against that gate, exactly as before. The first request's configured foreground provider
timeout bounds the correction through a monotonic remaining-time callback; the correction receives the remainder.
Closing the lesson prevents recovery; the existing provider interruption and physical gate still refuse sends.
The plan provider's existing shared deadline hook remains in force. Protection is reread before a correction, as
it was before the loop's retries. Provider schema repairs retain their own existing rule, independently of the
one contract credit. The adapter explicitly admits those repairs too.

A rejected answer is retained only on its failed operation receipt, with `ContractRejected`; its physical receipt
still honestly records a completed send. For each rejected blank, including a rejected shared correction, the
transcript stores only an invalid marker
with the existing fixed `the turn is empty` detail, never the rejected turn. Each marker consumes one existing
consecutive-failure slot. A second blank returns `None` to the existing loop; with two failures it may request
the third turn. At three failures recovery admission refuses another correction and the loop closes normally.
This also preserves accounting when blank replies mix with other failures. Successful corrections become ordinary
accepted turns. There is no reusable
model-answer checkpoint or corrected-receipt replay path for this ephemeral service; no cache was added. The shared
correction provenance has predicate/ordinal and a null request key, since this service has no existing logical
checkpoint key. Rejected receipts are not read as answers.

| Case | Before physical requests / learner outcome | After physical requests / learner outcome |
|---|---|---|
| Valid first | 1 / message shown | 1 / same |
| Empty then valid | 2 / valid message shown by outer retry | 2 / valid message shown by shared correction |
| Two empty, third valid queued | 3 / third message shown | 3 / same; shared correction then outer retry |
| Empty throughout | 3 / `teacher_contract_failure` close | 3 / same close |
| Whitespace then valid queued | 1 / whitespace shown; valid unused | 2 / valid message shown |
| Two whitespace, third valid queued | 1 / whitespace shown; later answers unused | 3 / valid message shown |
| Whitespace throughout | 1 / whitespace shown | 3 / `teacher_contract_failure` close |
| Malformed then valid | 2 / repaired message shown | 2 / same |
| Tool-only intermediate | N/A to tutor fixture; teacher requires message | N/A |
| Terminal deadline after first send | 1 / saved lesson, existing unavailable error | 1 / same |
| Terminal interruption after first send | 1 / saved lesson, existing unavailable error | 1 / same |

The **three-empty-request** policy is preserved: two empty turns followed by a valid one still deliver that
message in three requests; empty throughout still closes after three. No non-whitespace row sends more requests
than its baseline. Whitespace is the explicit exception: it was shown immediately and now consumes the same
existing failure slots as an empty turn, with at most three turn attempts. Provider schema repairs retain their
existing separate allowance; the shared re-ask does not add a fourth turn attempt.

Additional preservation/bound tests:

- Malformed → empty → valid and empty → malformed → valid: three physical requests, success.
- Malformed → empty → malformed → valid: four, success. Malformed → empty → malformed → empty → valid:
  five, success. Three malformed → empty pairs: six, existing consecutive-failure close (baseline counts).
- Two malformed outputs then valid: three, success through the old outer schema retry. Six malformed outputs:
  six, existing consecutive-failure close. Other contract failures still close after three.
- A blank at each of the three positions among other contract failures never grows the old three-request total.
- Deadline elapsed after rejection, or persistent provider interruption before correction: one physical send,
  existing `plan_unavailable` error. Exhausted funds: one rejected send for the action, then `budget` close.
- Three blanks close durably; `resume` on the closed lesson sends nothing further. Two failed turns (both blank
  or mixed with another contract failure) still leave the third slot for a valid message. Both blank receipts fail;
  their transcript markers contain no rejected answer; the outer retry is an ordinary request, not a second suffix.
- An otherwise valid close action with blank message never executes and cannot claim `goal_reached`.
- All eight models accept the correction, record two metered admissions and keep raw rejected output only on the
  failed receipt. Both empty and whitespace are tested for every model.

Two existing leak/exposure tests used blank-message fixtures with meaningful plan/recap fields. Their fixture
messages now contain ordinary prose so those tests continue exercising their original guards. No assertion was
weakened. The shared teacher fake decodes the original JSON before the appended correction suffix.

## Verification and limits

Only explicit pytest file/node selections ran, with `-n 2` and name-filtered chunks of at most 30 files, excluding
arc-close. In the earlier round, one exploratory run discovered four socket tests behind imported helpers; all failed at socket creation
with `PermissionError`, and were then deselected and listed below. A second exploratory chunk overlapped a separate
pytest invocation; the per-run scratch cleanup in separate PID namespaces removed its active fixtures. Its 148
failures were discarded and the chunk rerun sequentially. This was test-runner interference, not a code change.

The prospective structure scan includes the untracked new Python files without touching the index. It passes:
**465 private production patch sites, 23 source-text assertions**, unchanged. Largest import component 84;
modules in cycles 220. No first prompt, wire schema, config key, algorithm tag, migration, kill switch, identity
pin or golden changed. No prohibited configuration, owner vault or local fixture was read.

A live-route walk must check a valid first teacher turn's request/receipt identity; parsed-empty → useful correction;
two blanks → third valid message or third blank → existing close; same lesson envelope reservations and settled usage; safe suffix;
remaining deadline and actual cancellation; both schema/contract orders; real plan and authorized non-plan routes;
protection changing between attempts; restart after close; and the learner feed never containing the rejected blank.
Teach-back and tutor need an owner-supplied existing recovery envelope before any live recovery walk is meaningful.
Then check teach-back's unchanged count on failure, all tutor variants' final displayed content, verified Reader
excerpts and tool-only turns, and their existing failure wording.

Not verified: real model output, billing, streaming/socket deadline enforcement, real process kills, desktop/phone
rendering, the full suite, arc-close or the landing gate. Physical count measurements here use the real OpenAI chat
adapter over a fake SDK; no new real-plan stream experiment was performed. OpenAI's existing per-request/repair
timeout mechanics were not changed. Deadline tests prove refusal before a correction, not real transport interruption.
No durable recovery checkpoint/crash protocol was added to the teacher's ephemeral call.

Open owner question **SC-1** is stated above and filed in the bug ledger; neither question-count budget currently
supplies a recovery admission.

## Commands and final result lines

`t.sh` and `py.sh` are the supplied isolated wrappers. Continuation runs are sequential pytest invocations,
explicit files only, at most 30 files per selection and `-n 2`. All 33 test filenames containing `teacher`,
`structured_contracts` or `live_dialogue` are included. No socket tests are in these selections.

- `t.sh tests/test_teacher_structured_contracts.py tests/test_live_dialogue_contract_baseline.py tests/test_teacher_te1_review_fixes.py -q -n 2` — `102 passed in 7.80s`.
  The first continuation run had two test-assertion failures: the new mixed-failure test incorrectly required unrelated
  domain failures to omit their existing payload. The assertion now checks only rejected blanks; production was unchanged.
- `py.sh ruff check` — `All checks passed!`.
- `py.sh lint-imports --no-cache` — `Contracts: 45 kept, 0 broken.`
- `py.sh python` (prospective structure scan, explicit three new Python files included without index changes) —
  `Prospective ratchets passed, including all new Python files: private_patch_sites=465, source_text_assertions=23, largest_import_component=84, modules_in_an_import_cycle=220`.
- `git diff --check` — exit 0, no output.

### Continuation selection 1

```sh
t.sh \
  tests/test_live_dialogue_contract_baseline.py \
  tests/test_reader_rw5d_p4b_teacher_visuals.py \
  tests/test_structured_contracts.py \
  tests/test_teacher_exam_question_guard.py \
  tests/test_teacher_from_check.py \
  tests/test_teacher_structured_contracts.py \
  tests/test_teacher_te0_confidence_events.py \
  tests/test_teacher_te0_fix_round2.py \
  tests/test_teacher_te0_review_fixes.py \
  tests/test_teacher_te1_curriculum_c4.py \
  tests/test_teacher_te1_lesson.py \
  tests/test_teacher_te1_migration.py \
  tests/test_teacher_te1_review_fixes.py \
  tests/test_teacher_te1_successor.py \
  tests/test_teacher_te1_weight.py \
  tests/test_teacher_te1b_landing_r2.py \
  tests/test_teacher_te1b_migration.py \
  tests/test_teacher_te1b_rereview_fixes.py \
  tests/test_teacher_te1b_review_fixes.py \
  tests/test_teacher_te1b_suggestions.py \
  tests/test_teacher_te2_landing_r1.py \
  tests/test_teacher_te2_lessons.py \
  tests/test_teacher_te2_migration.py \
  tests/test_teacher_te2_probes.py \
  tests/test_teacher_te2_review_fixes.py \
  tests/test_teacher_te2_sidecar.py \
  tests/test_teacher_te2_successor.py \
  tests/test_teacher_te2log_activity.py \
  tests/test_teacher_te2log_episodes.py \
  tests/test_teacher_te2log_migration.py \
  -q -n 2 -m "not arc_close"
```

Last result: `456 passed in 39.43s`.

### Continuation selection 2

```sh
t.sh \
  tests/test_teacher_te2log_node_held.py \
  tests/test_teacher_te2log_receipt.py \
  tests/test_teacher_te2log_report.py \
  -q -n 2 -m "not arc_close"
```

Last result: `12 passed in 3.78s`.

### Continuation selection 3

```sh
t.sh tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_public_tip_guards.py tests/test_test_layout.py tests/test_architecture.py -q -n 2 -m "not arc_close"
```

Last result: `389 passed in 42.06s`.

Earlier round's broader teach-back/tutor selections passed with 395 and 215 tests respectively, and its guard
selection passed with 389 tests. Those are historical results; the socket exclusions below still need running.

## Socket tests for the orchestrator

The following 28 nodes need loopback access (including three unreachable-provider probes). They were deselected
from final selections; four initially undiscovered helper-backed nodes failed before opening a socket. Run these
with the supplied wrapper and no more than `-n 2`, or rerun their four complete files outside this sandbox:
`tests/test_sidecar_teach_back.py`, `tests/test_sidecar_tutor_qa.py`, `tests/test_teach_back_generation.py`, and
`tests/test_tutor_delivery_fixes.py`.

```text
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_conversation_checkpoints_and_grades
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_finish_early_grades_only_asked_criteria
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_requires_ready_provider
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_rejects_non_teach_back_items
tests/test_sidecar_teach_back.py::test_sidecar_queue_excludes_teach_back_items_when_provider_unready
tests/test_sidecar_teach_back.py::test_sidecar_queue_excludes_teach_back_items_under_manual_grading
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_finish_under_manual_grading_is_typed_and_preserves_checkpoint
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_finish_survives_post_step_failure
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_finish_retry_returns_same_attempt
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_from_a_queue_offer_links_the_graded_attempt
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_rejects_an_offer_of_another_item_or_session
tests/test_sidecar_teach_back.py::test_sidecar_teach_back_resume_merges_pending_learner_answer
tests/test_sidecar_teach_back.py::test_sidecar_request_teach_back_finds_existing_card
tests/test_sidecar_teach_back.py::test_sidecar_request_teach_back_uses_llm_authoring_and_quest
tests/test_sidecar_tutor_qa.py::test_sidecar_ask_rate_transcript_and_limit
tests/test_sidecar_tutor_qa.py::test_sidecar_submit_attempt_counts_question_hint_equivalents
tests/test_sidecar_tutor_qa.py::test_sidecar_save_tutor_answer_note_and_facet_question_counts
tests/test_sidecar_tutor_qa.py::test_sidecar_ask_is_rejected_during_teach_back
tests/test_sidecar_tutor_qa.py::test_sidecar_ask_requires_ready_provider
tests/test_sidecar_tutor_qa.py::test_preview_tutor_opening_after_stop_diagnosing
tests/test_sidecar_tutor_qa.py::test_preview_tutor_opening_without_decision_degrades_silently
tests/test_sidecar_tutor_qa.py::test_sidecar_promote_tutor_question_dedup_route_is_idempotent
tests/test_sidecar_tutor_qa.py::test_sidecar_promote_tutor_question_gap_rejected_in_library_context
tests/test_sidecar_tutor_qa.py::test_sidecar_promote_tutor_question_requires_ready_provider
tests/test_teach_back_generation.py::test_generate_practice_mode_mix_adds_hard_constraint_and_teach_back_guidance
tests/test_teach_back_generation.py::test_generate_practice_mode_mix_teach_back_count_violation_is_hard
tests/test_teach_back_generation.py::test_generate_practice_mode_mix_other_mode_mismatch_soft_warns
tests/test_tutor_delivery_fixes.py::test_the_sidecar_injects_the_linked_reference_rules
```

## The socket tests, run by the orchestrator (2026-11-21)

Every test file whose name contains teach_back, tutor, teacher, structured_contracts or live_dialogue, with the
identity pins, the structure ratchets and the test layout, outside the sandbox: `1104 passed in 90.98s`.
