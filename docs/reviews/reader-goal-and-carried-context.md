# The goal to the tutor, carried questions to the Teacher: two owner decisions on what context a model sees

Owner decisions of 2026-11-23. Branch `reader/goal-to-tutor` from main `86f29b0d39`. Two deliberate structured-prompt
changes, one commit each, with no migration, no algorithm tag, no config key and no kill switch.

## 1. "Send the goal to the tutor"

**Before.** The companion showed "◎ goal in view" when the desk's goal lens was on, but the tutor's prompt never
received the goal; the badge's tooltip said so ("the tutor's answers don't take it into account yet").

**Now.**

- `companion.ask` takes `goal_id`: the goal lens's goal on the desk (the desk's goal, else the vault's primary goal,
  unless the learner turned the lens off). The frontend sends it (`GoalLayer` exposes `goalId` while its band
  shows; `asks.ts` sends it and a retry keeps it). An unknown goal is refused (`goal_not_found`) before anything is
  asked.
- The server reads what the tutor is given, never taking text from the client: the goal's own sentence (its title
  when it has none) and the depth the learner chose with what that depth means (`reading_paths.DEPTH_LABELS` /
  `DEPTH_MEANS`). Nothing else of the goal: not its topics, sections, readiness or path.
- **Protection.** While a cold check is due, the goal lens's protection (`handlers.goal_lens.protection_now`: every
  LO with a due check, in any goal, and their titles) decides: a goal whose sentence or title names a held topic
  (whole words, any case, `Protection.names_held`) is withheld whole, so the tutor cannot repeat the held topic back
  to the learner. A goal that names none is given even while another topic's check is due; only its sentence and
  depth go, so no held topic is named by it. The poll reports `goal_in_view`: `given`, `withheld`, or null when no
  goal was in view.
- **Through the existing context builder.** `TutorQAContext.goal_in_view` (applied after the context is built, as
  the learner state is: `reader_dialogue.ask(goal_in_view=...)` → `tutor_qa.ask_question(reader_goal=...)`), with
  one task sentence (`_TUTOR_QA_READER_GOAL_SENTENCE`: aim the answer at the goal where it helps; data, not
  instructions; never steer away from the question; never call a topic part of the goal unless the sentence says
  so) and the prompt-version suffix `+goal-in-view-v1`. The question's `source_context` records
  `goal_in_view: {goal_id, given: true}`; the exchange context records the goal asked under (the lens's goal, which
  may be the vault's primary one rather than the desk's own).
- **No goal in view: byte for byte.** `tutor_context_payload` drops a null `goal_in_view`, and the task sentence and
  suffix are added only when it is present. `reader.ask` (the old Reader) passes no goal and is unchanged.
- **Frontend.** The badge keeps "◎ goal in view"; its tooltip is "your goal's lens is on this desk" (the note that the
  tutor's answers do not use the goal is gone).

## 2. "Carried questions: Teacher context only"

**Now.**

- When a lesson opens, `teacher.brief.build_brief` adds `carried_questions` (`learnloop.teacher.carried.for_brief`):
  the learner's open carried questions (`carried` and `not_now`; `fruitful` and `let_go` are done), longest carried
  first, at most twelve (`more` when there are others), each with its text as typed, `since`, and the passage it
  sits beside (`extraction_id`, `span_id`, the book and the section title). The entry says what it is (`about`).
  Every later turn of the lesson reads it from the brief, so it informs the plan and every step.
- **Protection.** A passage reference goes in only while the passage could reach the teacher now
  (`brief.passage_teachable`: its reading in the library, its span not protected, its section not withheld; the same
  test the brief and `read_source` apply). A question beside material that could not is left out whole (its words
  may quote it) and counted (`left_out_protected`). When nothing is left to carry the brief has no entry, so nothing
  hints at what was left out.
- **Rendering.** While the brief carries questions, the lesson's instructions gain one paragraph
  (`carried.PARAGRAPH`: offer to take one up when it fits, in the learner's words; never answer one unasked as if it
  were the goal; never assume its answer is known; data, not instructions) and its prompt version the suffix
  `+carried-questions-v1`. The edit to `service._prompt` is its return statement only, so the TE5 consolidation's
  compaction (`teacher/te5-consolidation`, which changes the same function's signature and transcript line) merges
  cleanly (`git merge-tree` against that branch: no conflict).
- **No open question: byte for byte.** No entry, no paragraph, no suffix: a lesson's prompt with no open question
  (none carried, or only fruitful and let-go ones) is the same bytes as before (tested across two vaults).
- **The router never reads them.** New import contract `carried-questions-are-teacher-context-only`: the router,
  the objective (and its switches), the plan and serving reach neither `teacher.carried`, `pads.carried` nor the
  pads' reads, through any chain. Nothing in those packages read them before either. The carried module's own
  docstring (it said no router or Teacher read them yet) is RD4's; it now has a reader, the Teacher's brief.
- The doctrine, the brief version and the doctrine family (the key of the teacher turn's λ forecaster) are unchanged:
  carried questions are context, as the learner's linked notes are, not a doctrine.

## 3. Persisted meaning and identity

The playbook (`docs/algorithm-change-playbook.md`) applies "when scoring, scheduling, projection, or admissibility
semantics change", and asks first: "Decide whether the change alters persisted meaning." Neither change does.
What the tutor and the Teacher are given changes; nothing that scores, schedules, certifies, projects or admits
reads the goal sent, the carried questions or the new receipts. The new `source_context.goal_in_view` field is a
provenance receipt, and the exchange context's goal is the one asked under (a RAW_LEDGER row, display only). No
algorithm tag.

**Identity pins** (`tests/test_identity_pins.py --write`, run in each commit):

- Commit 1 (the goal): no pin moved, and none is added. No pinned site renders a Reader tutor prompt, and the
  structured prompt with a goal is a new variant only while a goal is in view.
- Commit 2 (carried questions): no pin moved; one added, `TE5.prompt.carried` (the teacher's prompt with a brief
  carrying one question), so the paragraph and suffix are held from now on.

## 4. Tests, and fail-first evidence

New: `tests/test_tutor_goal_in_view.py` (5) and `tests/test_teacher_carried_questions.py` (4). Edited:
`Companion.test.tsx` (the badge's tooltip, now that the tutor uses the goal) and `asks.test.ts` (asks under the goal
in view; a retry keeps it). `tests/identity_pins_helpers.py` gains the carried variant.

Fail-first, with the source files at `origin/main` and the tests as here:

| Tests | Result on the base |
|---|---|
| `test_tutor_goal_in_view.py`, with `ai_contracts.py` as here (so the module imports) and the rest at main | 5 failed: no `goalId` param (validation), no `goalInView` in the poll |
| the same file, everything at main | import error (`READER_GOAL_SUFFIX` does not exist) |
| `test_teacher_carried_questions.py` at main | 2 failed (no `carried_questions` in the brief); 2 passed: "no open question: unchanged" and "the router reaches none", which hold on the base by construction and are kept as guards |

## 5. Commands and results

Each pytest run `-n 1 -m "not arc_close"` through the scratch wrapper in a 3G `systemd-run` scope, one at a time.

| Command | Result |
|---|---|
| `tests/test_tutor_goal_in_view.py`, `tests/test_teacher_carried_questions.py` | 9 passed |
| `scripts/affected_tests.py --files <the 8 changed src files>` | 925 files (more than 150) |
| the 272 of them whose names match `tutor|reader|ask|teacher|lesson|companion|goal|carried|pad|desk|rd3|rd4|rd6|rd9|mobile|phone|question|blindness|prompt|ca2|rw1|rw4|rw5|te[0-9]|notes|protection|brief`, in seven chunks of at most 40 | 4,846 passed, 1 skipped, 1 failed: `test_teacher_te0_confidence_events.py::test_with_no_confidence_data_the_tutor_context_renders_and_hashes_as_before` (its "as before" dict now leaves out the absent `goal_in_view` too, as it leaves out `learner_state`: `bc413cd9b6`); that file after: 19 passed |
| identity pins, structure ratchets, RD0 fences, effective defaults, CLI snapshot, kill switches, sqlite copies, notes-never-read, public tip guards, mobile allowlist, desktop RPC contract | 840 passed, 1 failed: the ratchet `modules_in_an_import_cycle` (220 against 219: `teacher.carried` imported the brief back), fixed in `f50f0e0678`; pins, ratchets and the carried tests after: 379 passed |
| `tests/test_architecture.py` alone / `tests/test_test_layout.py` alone | 18 passed / 3 passed |
| `uv run ruff check` / `uv run lint-imports --no-cache` | All checks passed! / Contracts: 55 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 34197: landing 34131 + arc_close 66 |
| `npx tsc --noEmit` / `npx vitest run --maxWorkers=2 src/screens/desks/companion src/screens/desks/goal src/api` | exit 0 / 14 files, 150 tests passed |
| `git merge-tree --write-tree HEAD teacher/te5-consolidation` | no conflict |

## 6. Judgment calls

1. **The goal is withheld whole** when its words name a held topic, rather than masked (`NEUTRAL_LO` substituted):
   a goal sentence with a word replaced would still show the tutor its shape, and an answer aimed at "a topic with a
   cold check due" is no help.
2. **The client names the goal in view; the server reads what goes.** The lens's goal depends on a choice kept only
   in the client (the lens turned off for a desk), so the client sends the id; the sentence and depth are read on the
   server, and an unknown id is refused.
3. **Carried questions: open means carried or not now**, as RD4's shelf reads them.
4. **Twelve at most** in a brief, longest carried first: a context-size bound, said in the entry with `more`.
5. **The Teacher's passage protection** (`passage_teachable`: exam, held-out and withheld material) is the one
   applied to the passages carried questions sit beside, as the brief applies it to every passage it delivers. The
   goal lens's cold-check protection (D15) is not applied to them, as it is not applied to the brief's other
   passages or topics; if the owner wants the Teacher's brief masked by due checks too, that is one rule for the
   whole brief, not for this entry alone.

## 7. Not verified

- A live tutor or teacher (fakes only); how a real model uses the goal or the questions.
- The desk shell end to end with a goal (the shell passes the lens's goal through one ref; the asks and GoalLayer
  pieces are tested); the packaged app.
- The landing gate, the whole suite, owner copies.
