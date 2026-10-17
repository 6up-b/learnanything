# Reader workbench RW1b: the intent box and active reading (stage `reader-rw1b`)

Branch `reader/rw1b` (worktree `learnanything-merge4`), base `main` at
`09acb51fd` (RW6a landed; migration head 207). Spec:
`docs/specs/spec_reader_workbench_v1.md` §13 row RW1b and what it cites (§4.2
in full, §4.3 Data, §4.4, §4.5; §3.4 items 13 and 16; §14 G3, G4, G36, G51,
G57; §16 D2, D3, D41, D43; §18; §20.9 S3-S5). Presentation:
`docs/specs/ux_reader_workbench_v1.md` §1 (the five intentions), §2 moments 2,
4 and 5, §3 (selection never switches the rail tab), §4.0, §4.1, §4.3, §4.10,
W2, §10 S3-S5. RW6a's friction note 1 (the `ReaderObservationV1` read for
missed next-step, why-step and assumption answers).

## 0. Plan (written before the code)

**Scope.** RW1b only: the intent box and its Decider routing, the palette by
intention, the active-reading questions (next step with the fold, why step,
assumptions, reconstruct later, another way to see this), the three-way
self-check, missed answers as `reader_formative` learner text and
`ReaderObservationV1` records, and migration 208. No RW4a library ask, no
grading, regrade, replay, eligibility, workbench-recording or recap change
beyond wiring the formative answers into the read RW6a left ready.

**Migration 208** (`208_learner_text_source_kinds.sql`): temp-then-rename of
`learner_text_gaps` and `learner_text_gap_jobs` under `PRAGMA foreign_keys =
OFF`, each `source_kind` CHECK widened with `workbench_text` and
`reader_formative` (one migration, both kinds), every row and id copied,
indexes and append-only triggers recreated; the runner's `foreign_key_check`
runs before commit (three tables reference `learner_text_gaps`). It also adds
two things RW1b's rows need: `reader_authored_questions.answer_basis`
(`source` | `model`, NULL for section and inquiry rows) so the expected
answer is labelled honestly, and a partial UNIQUE index on the selection
reuse key (extraction, anchor spans, style, prompt version), as RW1a's
inquiry index does. Roles in `table_roles` unchanged (checked by its test).
`fixtures/migration_head_207` → `migration_head_208` (backup-API copy, only
208 applied, rollback journal) and every hard-coded path.

**Config** (modelled defaults, left out of the decision-only template;
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` recomputed for every version with a "no
scoring, scheduling, projection or serving change" note):
- `[reader_intent]` `enabled = true`, `speculative_enabled = true`,
  `speculate_after_ms = 600`, `timeout_seconds = 4`, `max_calls_per_day = 200`;
- `[reader_active_reading]` `enabled = true`;
- `[reader_formative]` `enabled = true`;
- `ai.routing.reader_intent` (a decider-only route in `DECIDER_TASKS`; unset is
  the code-default Decider profile, never a chat fallback, never
  `LEARNLOOP_AI_PROVIDER`), with a privacy disclosure row (the selection and
  the typed text, including unsubmitted text after a pause while speculation
  is on).

**Routing** (`learnloop/reader/reader_intent.py`): the action catalogue (one
table: id, intention, palette label, the Decider's option description, the
effect the Reader runs: the same RPC and payload as today's palette); the
options are the actions that exist when the call is made (switches and
landed phases). One typed `ChoiceQuestion` to the Decider, argmax, ≤ 4 s;
unavailable, timed out, spent out, tied or failed → Ask. Empty text → Ask, no
call. A daily count of the route's receipts caps calls (200); speculation
stops at 80% of it. Every routing appends one `judgment_ledger` row (task
`reader_intent`, judge `decider`); a speculative routing's fate (`used` or
`discarded`) is appended as a superseding row on the same question; a
"change" appends the learner's correction (judge `learner_card`). Events:
`reader_action_invoked` with `intent_routed` / `intent_corrected`,
`reader_job_queued` / `reader_job_completed` with `speculative`, all
`salience_only`. The sidecar runs a routing on a small worker thread (the
sidecar is serial, so a Decider call never blocks the Reader's other RPCs):
`reader.route_intent` starts it and `reader.intent_routing` reads it, so ↵
picks up the speculative routing already in flight.

**Active reading** (the quick-check producer, W13): selection-scoped
`reader_authored_questions` rows (`scope_kind = 'selection'`,
`question_style` next_step / why_step / assumptions / reconstruct) written by
the existing `reader_quick_check` job type (a new `selection` path), admitted
like RW1a's passage check (`[reader_inquiry]` caps, isolated turn, durable
claim on the reuse key, held-out material refused). The next step's expected
answer is the book's following block, verbatim (source voice); why-step and
assumption answers are the book's words only when the quote is found in the
passage (else the model's, labelled). Answering, the self-check (matches ·
partly · no; a `learner_card` verdict) and dismiss write no attempt.
"Reconstruct this later" escalates through the existing escalation and adds
one `test_me_later` commitment on the new item (`due_hint`), both undoable.
"Another way to see this" is the sources service's existing `find_sources`
RPC with `intent = "alternative"` and the open passage excluded.

**Formative text** (`reader_formative`): a partly / no self-check on a next
step, why step or assumption answer queues one learner-text gap job (the
dispatcher reads the answer, the selection and the expected answer; read by
the gap reader with its own task text); a match writes nothing new.
`ReaderObservationV1`'s formative records gain the gaps named from them.

**Successor and kill switches.** None (§4.5: content and display). A missed
answer reaches learner-text gaps as a reader question already does; whatever
the pipeline then does is its own mvp-0.16 rule under its own switch.
`reader_intent.enabled` (off: the palette and the rail flip to Notes on
selection, as today; also off while `reader_inquiry` is off),
`reader_intent.speculative_enabled`, `reader_active_reading.enabled`,
`reader_formative.enabled`. Off, the prompt contract and the Reader are
byte-identical to the base (snapshots written on the base frontend first).

**Frontend** (new files under `screens/reader/`): `IntentBox.tsx` (unfocused
box under the selection, type-to-focus, ↵ ask · tab actions · esc, the routed
line with *change*, the seven states), `useIntentBox.ts` (speculation timer
and reuse on ↵), `intentPalette.ts` (the grouped palette from the contract),
`ActiveReadingCard.tsx` / `useActiveReading.ts` (the question in the rail, the
answer box, the self-check, the fold), and the fold in the text view (dotted
rule, *show*) with a cover on the original-page view.

**Tests.** Fail-first for G3, G4, G36, G51, G57; `test_reader_intent.py`,
`test_reader_intentions.py`, `test_reader_active_reading.py`,
`test_reader_reconstruct.py`, `test_reader_formative_texts.py`,
`test_learner_text_source_widening.py` (durability lane); vitest
`IntentBox.test.tsx`, `nextStepFold.test.tsx`, `intentSwitchOff.test.tsx`.
Fakes only (`StructuredClientFake`, `FakeDecider`).
