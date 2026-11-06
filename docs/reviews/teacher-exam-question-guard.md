# Teacher exam-question guard (`teacher/exam-question-guard`, base `23182034c6`)

A protection fix found at TE2's landing smoke (`docs/reviews/teacher-te2.md`, "Landing onto main"). On the
linear_algebra copy, a teacher turn that quoted an exam-reserved question's prompt was accepted into the lesson's
turn log and shown. The teacher's output guards (`teacher/guards.py`: `key_guard`, `identifier_guard`, `check_all`)
covered answer keys, not the reserved questions themselves. The owner's rule (Nov 4, exam rigor) is that only
reserved questions are protected, and they are never shown before their exam.

**No migration, no successor, no config key, no model request** (0 paid calls; none made by this stage). It is a
guard tightening that refuses only leaking text. No reader or writer of the old item difficulty scalar is added.

## Commits

| Commit | What |
|---|---|
| `830923138d` | The guard (`teacher/guards.py`), its call sites (`teacher/service.py`, `teacher/probes.py`), and the reproduce-first tests (`tests/test_teacher_exam_question_guard.py`) |
| (this commit) | spec_teacher_v1 §9.3 "As built", this file, the regenerated module references |

## What changed

**The protection source.** `guards.reserved_book(vault, repository)` reads the questions once per teacher turn,
through the authority the rest of LearnLoop uses: `learner_protection.withheld_items`, then
`content.authoring.practice_leakage.reserved_questions`. That is the same pair TE2's typed goals
(`teacher/topics.protected`) and FG1's and TE2's probes (`followup_run.authoring.reserved_view`) use. It covers:

- items in an exam pool;
- items made from held-out units, and the held-out spans themselves;
- live assessment reservations;
- each such item's stem, key and rubric.

If `withheld_items` is unavailable, or the read raises, the book is `unreadable`.

**The matcher and its rule.** `guards.quotes_reserved` calls `practice_leakage.reserved_findings` unchanged. That
covers contiguous 6-word shingles (less what ordinary items and readable source text show) and whole stems. It
counts a finding when two conditions hold:

- **Span kinds only.** A finding counts if it is `wording` or `stem`. The matcher's lone `numeric` findings do not
  count: a lesson's arithmetic ("0.5", "1/2", "16.0") would trip them, and a number alone shows no question.
- **The matcher's own span length.** A finding counts only if it is at least the matcher's shingle order
  (`inventory.shingle_n`, `DEFAULT_SHINGLE_N` = 6). This excludes a whole stem shorter than that, such as
  "Define a basis.", and a short text equal to a whole short held-out block. The task asked that a short common
  phrase must not trip the guard. Both limits are structural (the matcher's own kinds and span length), so no new
  constant was invented.

**Where it runs.** `guards.reserved_guard` is a fourth guard in `check_all`. The order is:

1. keys;
2. for a logged field, the identifier guard (moved inside `check_all` through `vault_keys`, so an existing key hit
   keeps its `answer_key` reason);
3. reserved questions;
4. the open check's solution;
5. citations.

So it covers every field the guards checked before:

- the displayed fields: message, choices, prediction prompt and choices, check question and choices, plan
  statements, the close's recap, and visual goals;
- the identifier guard's logged fields: plan ids and `lo_id`s, check, prediction and forecast nodes, a forecast's
  LO, a detour's hypothesis, a probe's readings and node, a gap's words and ref.

Two posing-path gaps were also closed:

- **The posed check's solution and rubric.** `service._check_solution_fields` covers `check.committed_solution`
  and `check.rubric[i].fact`. They are shown by no field, but they become the check's vault item, which the
  grader reads, and the grader's feedback can quote them. They pass only the reserved-question guard, because the
  solution answers its own check by design. Before this fix they passed no guard.
- **A built figure's words** (`service._visual`): the reserved guard runs between the key guard and the open-check
  guard. A hit records the figure `withheld` (code `reserved_question`) with its own line for the teacher.

**On a hit.** The turn is withheld by location, as an answer-key hit is:

- `validation = 'withheld'`, reason `reserved_question` (`protection_unreadable` when the book could not be read);
- the detail is `<location>: <fixed line>`, naming no words, because it enters the transcript the teacher reads
  next;
- the model is re-prompted, under the existing consecutive-failure rule.

The refused turn's raw payload is recorded exactly as TE1 records any withheld turn (`payload.turn`). Nothing reads
it, and it is unchanged.

**The inline grader.** The blind grader sees only the check item and the learner's answer. Now that the check's
solution and rubric are guarded, it has no reserved text to quote, except the learner's own words. Its feedback is
still filtered at both places it is shown:

- `service._answer_check` (`check_result.grader_feedback`);
- `probes.record_answer` (`probe_result.grader_feedback`; the reserved book is read before the write lock).

`guards.shown_feedback` returns None when the feedback quotes a reserved question or the book is unreadable. The
grade, the attempt and its stored completion are unchanged, and the view and the transcript then carry no feedback.

**The prediction path** needed nothing new: its prompt and choices were already displayed fields, and it runs
from the guarded, accepted turn.

**Not changed:**

- `topics.protected` (already the matcher, whole);
- `lesson_probe` (FG1's checks);
- the brief's protection state;
- TE1's withheld-turn recording.

The diff stays in `guards.py` and its call sites. `service.py`'s hunks are at `_answer_check`'s result,
`_call_teacher`'s guard loops, a new `_check_solution_fields`, and `_visual`'s guard loop. It does not touch
TE3a's reveal/show write or receipt exposure.

## Tests (reproduce-first)

`tests/test_teacher_exam_question_guard.py`, 19 tests. On the base source (the `src` diff reverted, the tests in
place): **17 failed, 2 passed**. The 2 that passed are the ordinary-sentence lesson and the grader's ordinary
feedback, which must pass on both. With the fix: **19 passed**.

The vault is `build_teacher_vault` plus three items:

- an exam-pool item whose stem shares no words with its key (the smoke's shape: the key guard cannot see it);
- an exam-pool item with a short stem ("Define a basis.");
- a held-out item made from the held-out unit `lay_held` (not in any exam pool).

| Test | What it pins |
|---|---|
| `test_the_matcher_reads_both_items_as_withheld_questions` | both items are `WITHHELD_EXAM`; a stem, and part of one at the matcher's span, match; an ordinary sentence, a 4-word shared phrase, a lone decimal and the short stem do not (the raw matcher does find the last two) |
| `test_a_turn_quoting_an_exam_reserved_stem_is_withheld_and_shown_nowhere[message, choice, plan, prediction, check, check.committed_solution, check.rubric, recap]` | withheld `reserved_question`, named by location; the detail carries no words; the raw payload recorded; the re-prompt told; then the stem is in no view, displayed text, receipt, teacher or grader prompt, or transcript |
| `test_a_logged_field_quoting_a_reserved_stem_is_withheld_by_location` | a plan node id (`requests[0].plan[0].id`) and a TE2 probe reading (`requests[1].readings[0]`): withheld; no generation job |
| `test_a_held_out_items_stem_is_withheld_likewise` | the held-out (not exam) item's stem: withheld, shown nowhere |
| `test_an_ordinary_sentence_sharing_a_few_words_with_a_reserved_stem_is_not_withheld` | a lesson message sharing words with both long stems and the short one: accepted and shown |
| `test_unreadable_protection_fails_closed` | `reserved_questions` raising: every turn withheld `protection_unreadable`, nothing shown, the lesson closes `teacher_contract_failure` |
| `test_reserved_book_is_unreadable_when_withheld_items_is` | `withheld_items` unavailable: unreadable; the guard refuses; feedback is dropped |
| `test_the_inline_graders_feedback_quoting_a_reserved_stem_is_not_shown[True, False]` | the check's feedback quoting a stem: `None`, grade `right`, shown nowhere; ordinary feedback: kept and shown |
| `test_a_lesson_probes_grader_feedback_quoting_a_reserved_stem_is_not_shown` | the same for a TE2 lesson probe's `probe_result` |
| `test_a_figure_quoting_a_reserved_stem_is_not_shown` | a figure whose words quote the stem: `withheld`, code `reserved_question`, no `shown_text` |
| `test_a_lesson_with_no_reserved_text_is_byte_identical_with_the_guard_off` | a full lesson (plan, check, answer with grader feedback, re-plan, stop): every `lesson_turns` row and payload, the receipt, every view and every model prompt are identical, ids aside, to the same lesson with `reserved_book` replaced by one that never fires (main's guards) |

Four existing tests in `test_teacher_te2log_episodes.py` first failed when the reserved guard ran before the
identifier guard. Their fields carry a reserved item's key, which is also its stem, so `answer_key` became
`reserved_question`. The identifier guard now runs inside `check_all` before the reserved guard, and they pass
unchanged.

## Gate (this step; targeted, per the owner's rule of 2026-10-17)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` (isolated env) | 43 kept, 0 broken |
| `pytest -n 6 tests/test_teacher_exam_question_guard.py` on the base source | 17 failed, 2 passed (reproduction) |
| `pytest -n 6` new file plus every file exercising `teacher.guards`, `teacher.service` or `teacher.probes` (list below) | **662 passed** |
| `pytest -n 6` contract set (list below) | **959 passed, 6 skipped** |
| `module_generate.py`, `module_validate.py` (isolated env) | 1244 module notes; PASS |
| `validate_vault.py` | passed (2235 notes) |

Every pytest ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`. Every other Python
command ran under `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

**Behaviour files (662):**

- `tests/test_teacher_*.py` (every teacher test file, the new one included);
- `test_reader_rw5d_p4b_teacher_visuals`;
- `test_data_capture_a6_delayed_pick`, `test_data_capture_successor`;
- `test_figures_prefetch`, `test_figures_prefetch_review_fixes`;
- `test_followup_single_use`, `test_followup_successor`, `test_followup_reserved_only`;
- `test_followups_batch5_lesson`, `test_followups_batch5_recap_dependencies`, `test_followups_batch5_recap_protection`;
- `test_followups_batch6_review_fixes`, `test_followups_batch6_router_report`;
- `test_followups_batch7_prefetch_capped_resume`, `test_followups_nov2_figure_provenance`;
- `test_ro1_successor`, `test_ro4_successor`, `test_ro5_successor`, `test_ro6_successor`, `test_rofu_successor`;
- `test_practice_leakage`.

**Contract set (959 + 6 skipped):**

- architecture and registries: `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`,
  `test_module_catalog_inventory`, `test_ad_protected_tables`;
- `test_cli_help_snapshot`;
- the display-label audit: `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`,
  `test_rw5c_labels`;
- the process-launch allowlist: `test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`,
  `test_codex_lockdown_round3`;
- storage and the public tip: `test_sqlite_file_copies`, `test_public_tip_guards`, `test_config_refactor`;
- the desktop and sidecar contracts: `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`,
  `test_sidecar_contract`, `test_sidecar_registry`, `test_desktop_activation_audit`;
- `test_mobile_allowlist`;
- `test_coordinated_migrations`, `test_tracked_fixture_databases`;
- `test_notes_never_read`.

Not run, because nothing they cover changed:

- no migration, DB or connection code: durability lane, DB reference scripts;
- no frontend or Rust: npm, vitest, cargo, desktop reference;
- no config key: defaults snapshot.

The full suite runs once, in the landing gate.

## Open items

- **Smoke on the copy.** The landing smoke can replay the original case on the linear_algebra copy (a teacher turn
  quoting `pi_axiom_commutative_recall_02`'s prompt) and check that it is now `withheld` with `reserved_question`.
  This stage ran no manual run on any vault copy.
- **For the owner: two judgments made under "a short common phrase must not trip it".**
  - Lone distinctive numbers from a reserved question are not withheld from teaching text. The keys guard still
    covers answers.
  - A reserved question whose whole stem is shorter than the matcher's 6-word span is not withheld when a lesson
    repeats it. (Narrowed by the Codex review's F1 and re-review F1, `teacher-examguard-codex-review.md`: such a
    stem is withheld when it carries a distinctive number, or when the text poses it as its own sentence or clause
    or asks it; only a word-only stem inside a teaching sentence still passes.)

  To protect either, drop the corresponding condition in `guards.quotes_reserved`, a one-line change. The cost is
  a false refusal whenever a lesson uses that number or phrase.
- **A book exercise that is also exam-reserved.** If such a question's text appears verbatim in a delivered
  passage, a teacher turn quoting it is still withheld. The whole-stem finding is not relieved by the source
  showing it, as on FG1's path. The teacher is re-prompted to paraphrase.
- **Already-recorded rows are not rewritten.** Grader feedback that a pre-fix lesson stored and turns it accepted
  stay as recorded. A lesson whose protection state changed already ends before its next teacher call (ruling R1).
