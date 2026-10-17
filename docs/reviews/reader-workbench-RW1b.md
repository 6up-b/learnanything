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

## 1. What was built

### 1.1 Migration 208 (`migrations/208_learner_text_source_kinds.sql`)

- `learner_text_gaps` and `learner_text_gap_jobs` rebuilt temp-then-rename under `PRAGMA foreign_keys = OFF` (the runner turns it off before `BEGIN` and runs `foreign_key_check` before the commit), each `source_kind` CHECK widened with **both** `workbench_text` and `reader_formative` in one migration. Every row and id is copied; the indexes and the two append-only triggers are recreated; the three tables whose foreign keys name `learner_text_gaps` (`learner_text_gap_reversals`, `learner_gap_check_advances`, `learner_gap_commitments`) resolve to the rebuilt one.
- Also in 208 (see §3 item 1): `reader_authored_questions.answer_basis` (`source` | `model`, NULL on section and inquiry rows) and the partial UNIQUE index `idx_reader_authored_questions_selection` on the selection reuse key (extraction, anchor spans, style, prompt version) `WHERE scope_kind = 'selection'`.
- `table_roles`: unchanged (both tables keep their roles; pinned by `test_208_keeps_the_table_roles`). No new table.
- Head fixture `fixtures/migration_head_207` → `fixtures/migration_head_208`: a backup-API copy of the base's 207 database (read from git `09acb51fd`), only 208 applied under `upgrade_allowance(UPGRADE_TEST_HELPER)`, `wal_checkpoint(TRUNCATE)` → `(0, 0, 0)`, `journal_mode=DELETE` (header bytes 18-19 are 1/1), `integrity_check` ok, `foreign_key_check` empty, copied into place with the backup API, no companion files. The README gains the 208 paragraph. 29 files named the old path (tests, both reference scripts, `docs/decider-tier1-migration.md`, the Database Catalog); all now name `migration_head_208`; `SCHEMA_HEAD = 208` in both scripts; `test_route_rules_in_grader.py`'s max-migration assertion is 208.

### 1.2 Config (modelled defaults; not in the decision-only template)

`[reader_intent]` `enabled`, `speculative_enabled`, `speculate_after_ms` (600), `timeout_seconds` (4), `max_calls_per_day` (200); `[reader_active_reading]` `enabled`; `[reader_formative]` `enabled`; `ai.routing.reader_intent` (added to `DECIDER_TASKS`: a decider-only route, never a chat fallback, never `LEARNLOOP_AI_PROVIDER`). All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed (`defaults_fingerprint_for_version`) with a "no scoring, scheduling, projection or serving change" note. The privacy disclosure (`ai/disclosures.py`) gains the `reader_intent` row: the box's words, a short excerpt of the selection and the action names go to the Decider on Enter, and after a pause while speculation is on; switching speculation off sends nothing until Enter.

### 1.3 The intent box's router (`src/learnloop/reader/reader_intent.py`)

- **The catalogue** (`ACTIONS`): one table with id (the ledger verdict), group, palette words, the Decider's option description and the effect the Reader runs. Understand: ask (three answer modes: answer directly, help me reason, ask me first), explain differently, worked example, research this, why does this step work?, what does this assume?, another way to see this. Apply: work through this, let me try the next step, add this exercise to practice. Consolidate: revisit once (test me later), help me remember, reconstruct this later. Transfer: connect it, why this matters. Mark: highlight, note, confusing, not worth remembering. Orient is empty (absent) until RW4a / RW7a land.
- **Availability**: active reading only with `reader_active_reading.enabled`; work through this only with `workbench.enabled`; another way only with `source_service.enabled`; a held-out passage keeps only the Mark actions that show nothing to a model; the learner's own notes (a `textfile` source) keep only the anchor-free actions (ask ×3, test me later, help me remember, connect it).
- **`route()`**: one typed `ChoiceQuestion` (options = the available actions), argmax. Empty text → Ask, no call, nothing written. Unavailable, timed out, spend-refused, tied, failing, or the day at `max_calls_per_day` (root receipts of owner kind `reader_intent` since UTC midnight) → Ask (`status = fallback`, `reason` named). Speculative routings are not made with the switch off or once 80% of the day's calls are used; Enter still routes until the cap. The admission is the Decider's own (`decider_judgments.ask_decider`, a public wrapper of the existing `_ask`: one admitted request at the listed input price, receipts written before the request).
- **The ledger** (task `reader_intent`, left = the input hash, right = the selection key): one `decider` row per routing (verdict = the action or the fallback reason; probabilities, speculative, latency in the rationale; never the learner's words). A speculative routing's fate is a superseding `decider` row with `fate: used | discarded` (`record_fate`, idempotent; none for an Enter routing). "change" is a `learner_card` row superseding the head, verdict = the action picked instead or `cancelled` (`record_correction`).

### 1.4 Active reading (`reader_quick_check.py`, `active_reading.py`)

- **Selection-scoped questions** in the quick-check producer (W13): `author_selection_question` writes `scope_kind = 'selection'` rows in style `next_step`, `why_step`, `assumptions` or `reconstruct` (`question_style` values RW1a's migration created), admitted under `[reader_inquiry]`'s caps and receipts (the quick-check producer's existing route, `canonical_ingest`), sent as an isolated turn, under a durable claim on the reuse key (`judgment_work_claims`), the database refusing a second row. Prompt `rw1b-reading-active-v1`.
- **The expected answer is honest by code**: the next step's is the book's following block(s) verbatim (the model only names which of the next three blocks make up the step; a prefix, else the first); a reconstruction's is the selected derivation verbatim; a why-step or assumption answer is the book's (`answer_basis = 'source'`) only when the model's `source_quote` is found in the passage (whitespace-normalised, case-insensitive), else it is the model's answer, labelled so (`'model'`).
- **The job path**: the existing `reader_quick_check` job type gains a `selection` scope (`_handle_reader_selection_check`), with held-out material refused before any call (code `exam_material`) and the inquiry check's refusal codes (`capped`, `spend_refused`, `provider_unavailable`, `held`), plus `no_passage` / `no_question`. One live batch per reuse key (`enqueue_reader_selection_check`).
- **Actions** (`record_selection_action`): `answered` (an empty answer is "show me"), `self_checked` (matches · partly · no, stored in `self_check` and appended to `judgment_ledger` as a `learner_card` verdict, as RW1a's quick check does), `dismissed`. Formative only.
- **Reconstruct this later** (`reconstruct_commit` / `reconstruct_undo`): the quick check's own escalation into one practice item, plus one `test_me_later` commitment on it (target `legacy_practice_item`, `due_hint` three days ahead, idempotent on `reader_reconstruct:<question>`); undo retires the commitment and the item (`retire_item`, reason `no_longer_relevant`).

### 1.5 Missed answers as learner text (`diagnosis/text_gaps/`)

- `SOURCE_KINDS` gains `reader_formative` and `workbench_text`; the dispatcher `learner_text()` reads `reader_formative` (`reader_formative_text`: the learner's answer, with the question, the selected passage, the expected answer and whose it is, and the self-check as context; the passage's provenance-linked LOs and their single subject) and returns nothing for `workbench_text` until RW2b builds its adapter (the job is skipped).
- The stuck-text reader reads it with its own task text (`READER_FORMATIVE_TASK`, prompt version `learner-gap-reader-formative-v1`); the stuck answer's prompt is unchanged. The Decider's kind state names the surface.
- `enqueue_reader_formative`: only with `learner_text_gaps.enabled` and `reader_formative.enabled` on, only for a missed (partly / no) next-step, why-step or assumption answer the learner wrote; idempotent. A match, a "show me" with no answer, or a question added to practice since, queues nothing. The sidecar's self-check RPC queues it and wakes the post-attempt worker's `gaps` slot.
- Write provenance: the gap row's learner words carry a record (`formative_record`: the topics and the passage's spans as a canonical-source ref), so the chat guard can release them by its rule (c) and withholds them otherwise.
- **`ReaderObservationV1`** (RW6a's read, the wiring only): the missed records' `hypotheses` are the gap ids learner-text gaps named from them (`named_gaps(..., source_kind="reader_formative")`), and `observed` gains `answer_basis`, so the recap and Wrap up say "differed from the book's" or "from LearnLoop's model's answer" (recapCopy).

### 1.6 The sidecar (`src/learnloop_sidecar/handlers/reader_intent.py`)

Eight desktop-only RPCs (pinned off the phone): `reader.route_intent` (starts a routing on a worker thread with its own repository connection, answers at once; an empty text, a held-out passage or a speculation not made answer without a thread), `reader.intent_routing` (reads it, waiting at most a second), `reader.intent_outcome` (used / discarded / corrected), `reader.active_question`, `reader.active_question_status`, `reader.active_question_action`, `reader.reconstruct`, `reader.reconstruct_undo`; and `reader.prompt_contract` carries `intent` (the palette, the notes palette, the speculation settings) and `activeReading` (`foldBlocks`) only while their switches (and `reader_inquiry`) are on. Events, all `salience_only` and server-owned (the UI cannot record them): `intent_routed`, `intent_corrected`, `active_question_requested`, `active_question_answered`, `reconstruct_committed`, `reconstruct_undone` on `reader_action_invoked`, and `reader_job_queued` / `reader_job_completed` with `job_kind = intent_routing` and `speculative`. Eight Tauri passthroughs.

### 1.7 The report (`reader_report.py`)

`intent`: routings, speculative, used, used speculatively, discarded, fallbacks by reason, corrections counted on used routings only, actions by intention (from the funnel's `action_invoked` with `entry`). `active_reading`: questions by style, answered, self-checks by style, formative texts queued.

### 1.8 The Reader (frontend, `apps/learnloop-tauri`)

- `screens/reader/useIntentBox.ts` + `IntentBox.tsx` + `intentPalette.ts`: the box appears 150 ms after a learner's selection on the reading surface (the text view, the original page, the marquee union), **unfocused**; PgDn, arrows, Space and Ctrl+C keep their meaning; the first printable key focuses it and is typed into it; Enter and Tab work without typing; `?` focuses it; while it shows, the Reader's single-key shortcuts (`w`, `[`, `]`, `\`) are off; keys on the rail keep their meaning; in skim mode it opens only on `?` or Tab; Esc or a click elsewhere closes it, recording nothing. Typing that pauses for `speculateAfterMs` starts a speculative routing; Enter takes it when the text is unchanged (fate `used`), and a changed text discards it and routes again. The routed action runs at once through the palette's own handler and shows as `→ <Intention> · <action> · change`; "change" cancels a pending Ask or question and opens the palette with the text kept; the pick is the correction. Tab opens the palette by intention (arrow keys move, Enter presses). Pending is `◐ choosing…` with cancel; a broken routing asks (and says so).
- **Selection never switches the rail tab** while the box is on (the three `setRailTab(... "notes")` flips are gone behind it); a routed Ask opens Ask (D41); an empty Enter opens Ask on the selection with no call and puts the cursor in the composer.
- `useActiveReading.ts` + `ActiveReadingCard.tsx`: the card at the head of Notes (opened by the learner's act): the question (model voice), the answer box with *ⓘ where this goes*, *compare with the book* / *show me*, then the learner's line beside the book's (source voice) or the model's (model voice, "model's justification"), the self-check, *don't bring this back*; reconstruct's receipt with *undo*; another way to see this (the sources service's `find_sources`, intent `alternative`, the open passage excluded, labelled *from a different book* / *a worked example instead* / *elsewhere in this book*; *nothing in your books treats this differently yet*). Seven states through `ModelActionState`.
- **The fold**: "let me try the next step" folds the book's next blocks at once (computed in the Reader, then the sidecar's `foldedSpanIds`) under a dotted rule — *the next line is folded while you try · show* — with *◐ writing the question — the lines stay folded* while it is written; the fold opens on an answer, "show me", "show" or dismiss. On the original-page view the folded blocks get an opaque cover (`PdfReaderPane.coveredSpans`).
- `invokePreset` / `captureHighlight` take the box's words as the learner text and its intention and entry for the funnel; `submitAsk` takes a routed answer mode; `NotesRail` takes an optional header. Off, every new prop is absent.

## 2. Gates and where they are tested

| Gate | Backend | Frontend |
|---|---|---|
| **G3** routing = the palette's call; empty Enter no call; failures ask; change is a `learner_card` verdict; off = today's | `test_reader_intent.py` (the Decider picks, ledger row; empty Enter; four failure kinds; a tie; an unready route is never a chat fallback; the day's cap; change and cancel; options are only what exists; RPC refusals off; contract byte-identical off); `test_reader_intentions.py::test_grouping_changes_no_presets_effect`, `test_nothing_in_todays_notes_palette_is_missing` | `IntentBox.test.tsx`: empty Enter, routed Ask in its mode, unavailable Decider asks, change records the pick, a palette pick makes exactly the Notes palette's call; `intentSwitchOff.test.tsx` |
| **G4** scoped questions formative and keyed; no shadowing; section rows byte-identical | `test_reader_active_reading.py` (expected answers by basis, reuse key, the database's unique key, no shadowing, section payload unchanged, no attempt or evidence, show me, the job once, held-out refused); `test_reader_reconstruct.py` (an item only after escalation, an ordinary `test_me_later`) | `nextStepFold.test.tsx` (no attempt in any call) |
| **G36** W1's tiers; widening keeps rows and passes `foreign_key_check` (durability lane) | `test_reader_formative_texts.py` (queued only when missed; switches; dispatcher; reading writes only gap rows, every evidence table unchanged; the observation's hypothesis); `test_learner_text_source_widening.py` (every row, column, index and trigger kept; both kinds admitted, others refused; append-only; FKs resolve; a durability-lane case); the firewall case per new event (`test_every_rw1b_event_is_salience_only_refused_as_evidence_and_never_client_recorded`) | — |
| **G51** intentions change no effect; another way excludes the open passage; reconstruct one item + one commitment, undoable; every source kind; notes anchor-free | `test_reader_intentions.py` (grouping, absent phases, switches, notes, transcript and notes routing, active reading on a transcript, the frontend fixture equals the sidecar's palette); `test_reader_reconstruct.py` | `IntentBox.test.tsx` (palette groups); `nextStepFold.test.tsx` (off: absent, no ghost); another way's exclusion is the request (`excludeSpanKeys` of the selection) |
| **G57** selection never changes the rail tab; the box never takes focus until a printable key; keys | — | `IntentBox.test.tsx`: unfocused and no tab change, scroll/copy keys untouched, type-to-focus, `?`, Tab, Esc, arrows and Enter in the palette, rail keys keep their meaning, skim, never inside the rail; `intentSwitchOff.test.tsx` (off: today's flip) |

**Fail-first evidence.** Frontend (`fb5b2f876`, committed before any RW1b frontend code): 15 of 16 tests failed on the base (the 16th, "never inside the rail", holds trivially). The switched-off snapshots (`fbc8b11e6`, 7 snapshots) were written on the base frontend and pass unchanged. Backend: written beside the code; run against the base's source (`git archive 09acb51fd src migrations`, `PYTHONPATH` to it, `-o pythonpath=.`): all five RW1b test files fail at collection (no `reader_intent`, no `READER_FORMATIVE_PROMPT_VERSION`, …) and 3 of the 4 migration tests fail (no 208; the table-roles check holds on the base too).

## 3. Decisions and deviations

1. **Migration 208 carries two more things than the widening**: `answer_basis` (whose words an expected answer is, so W2's labels are persisted, not re-derived) and the selection reuse key as a UNIQUE index (as RW1a's inquiry key is). Both are on `reader_authored_questions` (no rebuild); section and inquiry rows are untouched.
2. **"Quick check on this passage"** (§4.2's Consolidate row) is not offered on a plain selection: UX §4.1 omits it and RW1a's passage check belongs to an inquiry (the reconnect line). **Default: absent.**
3. **Two of today's presets** — *worked example* and *research this* (the `ask` preset) — are not in §4.2's table; they sit under Understand so nothing in today's palette needs more than Tab plus one choice (U13).
4. **Phases not built**: Orient's *what matters here* (RW7a) and *what do I need first* (RW4a's graph expansion), Transfer's *where else is this explained?* and *where is this used?* (RW4a's library ask), *practice this in a new setting* / *practice this question* (needs DL3's / RW4a's practice RPC and the learner-pick UI), *find an exercise in my sources* (RW4b), *compare sources* (RW4a/RW4d), *make this explorable* (RW5a): **absent** (not disabled), and not among the Decider's options. *Another way to see this* uses `find_sources` with intent `alternative` (it exists), not §4.2's fallback.
5. **"change" after an action that already ran**: a pending Ask or a pending question is cancelled; a local capture (a preset, a highlight) already made stays, with its own undo in Notes, and the pick runs as well. Spec: "change cancels it".
6. **Reconstruct's receipt**: "Added to your practice: later you'll be asked to rebuild this derivation without the book · undo", not "In a few days…": until DL2 reads `due_hint`, the escalated item is an ordinary new item the scheduler may serve sooner (W2: no surface promises what nothing schedules). The commitment carries `due_hint` (+3 days) for DL2.
7. **Routing off the request path**: the sidecar is serial, so a routing runs on a small worker thread and is read back by `reader.intent_routing` (polled every 250 ms); the speculative routing "in flight" is that thread. Not in the spec; nothing else changes.
8. **The fate of a speculative routing** is a superseding `decider` row with the fate in its rationale (the ledger is append-only); the report reads the chain's head.
9. **The intent box needs RW1a's switch** (`reader_inquiry.enabled`), like RW6a's recap: its states, voices and Ask are RW1a's. Off, the contract has no `intent` key and the Reader is the base's.
10. **Event names**: `active_question_requested` (with `style`) for every active-reading request instead of §4.3's `next_step_requested`; `active_question_answered` for the self-check.
11. **A held-out passage** is never routed (the sidecar refuses `exam_material` before any call; the box says so and offers Mark only).
12. **The fold's one-key unfold** is the *show* button (focusable, Enter); no dedicated key (open question 4).
13. **`workbench_text`** is admitted by the schema and the dispatcher (skipped) only; RW2b builds its adapter.
14. **Write provenance for formative words**: recorded (topics and the passage as a source ref), so the chat frontend's guard can release them; tutor questions' words were already recorded.

## 4. Successor (§4.5)

**None.** Routing, the palette, the questions, the fold and the self-check are content and display (W1 tiers 1-2). A missed answer reaches learner-text gaps exactly as a reader question already does (§4.2, W1: "Tier-2 inputs to content … follow the learner-text-gaps precedent and take no successor"); whatever the pipeline then does — a named gap, a created prerequisite, and, at mvp-0.16 or later with `learner_text_gaps.sooner_check_enabled`, a sooner check and a weak prerequisite signal for placement — is the existing mvp-0.16 successor's rule under its own switch, unchanged. No new rule reads the new rows. `reader_formative.enabled = false` stops every such text. Replay reads nothing new (no `reader_formative` rows exist in any history before this stage). Recorded as open question 1 in case the owner wants missed answers kept out of the field signals.

## 5. Friction audit (G52) for the workflows RW1b touched

| Workflow | Before | After |
|---|---|---|
| Ask about a selection and get back to reading | select → the rail flips to Notes → open Ask → type → ask | select → type in the box (it focuses on the first key) → ↵ (routed in the pause) → the Ask tab opens with the answer; the source keeps its place and focus |
| Capture "test me later" | select → Notes (flipped) → click | select → type *quiz me later* ↵, or Tab → *revisit once* (the same call) |
| Try the next step of a derivation | not possible (the next lines are right there) | select → Tab → *let me try the next step* → the next lines fold at once → write → see the book's step → matches · partly · no |
| Remember to rebuild a derivation | write your own question | select → *reconstruct this later* → one practice item, *undo* |
| Find another treatment | Library search by hand | select → *another way to see this* → one or two passages, labelled |

Keyboard: every new action is reachable from a selection with printable keys + ↵, or Tab + arrows + ↵; Esc peels the box. Waits on a model: the routing (`◐ choosing…`, usually under the 4 s timeout, usually instant with speculation), the question (`◐ writing the question`, the fold already shown). Focus moves only on the learner's key. Context: the selection stays; the rail does not move on its own.

## 6. Tests and counts

New backend files (all pass): `test_reader_intent.py` 27, `test_reader_intentions.py` 10, `test_reader_active_reading.py` 14, `test_reader_reconstruct.py` 5, `test_reader_formative_texts.py` 8, `test_learner_text_source_widening.py` 4 (one on the durability lane); `test_mobile_allowlist.py` +9 pins and one registry check. New vitest files: `IntentBox.test.tsx` 15, `nextStepFold.test.tsx` 4, `intentSwitchOff.test.tsx` 3 (7 snapshots written on the base), `recapCopyBasis.test.ts` 1; `voices.test.tsx`'s model-voice lint admits the book-voice branch of an expected answer (`answer_basis = source`) and nothing else.

## 7. Files

- Migration and fixture: `migrations/208_learner_text_source_kinds.sql`; `fixtures/migration_head_208/` (renamed from `_207`, rebuilt, README).
- Backend: `src/learnloop/reader/reader_intent.py` (new), `src/learnloop/reader/active_reading.py` (new), `src/learnloop/reader/reader_quick_check.py`, `src/learnloop/reader/ai_contracts.py`, `src/learnloop/reader/reader_observations.py`, `src/learnloop/reader/reader_inquiry.py`, `src/learnloop/reader/reader_report.py`, `src/learnloop/diagnosis/text_gaps/{contract,sources,jobs,judges,pipeline,provenance}.py`, `src/learnloop/db/repositories.py` (the selection insert and lookups), `src/learnloop/content/pipeline/jobs.py` (the selection job path and its enqueue), `src/learnloop/decider_judgments.py` (`ask_decider`), `src/learnloop/ai/routing.py`, `src/learnloop/ai/disclosures.py`, `src/learnloop/config/schema.py`, `src/learnloop/config/template.py`; sidecar `src/learnloop_sidecar/handlers/reader_intent.py` (new), `handlers/reader.py` (the contract fields), `handlers/__init__.py`.
- Frontend: `screens/reader/{IntentBox.tsx, useIntentBox.ts, intentPalette.ts, ActiveReadingCard.tsx, useActiveReading.ts}` (new), `screens/ReaderScreen.tsx` (+135 lines, now 3,014), `screens/reader/{NotesRail.tsx, useReaderInquiry.ts, recapCopy.ts, RecapCard.tsx, WrapUpPanel.tsx}`, `components/PdfReaderPane.tsx` (`coveredSpans`), `api/{client.ts, dto.ts}`, `fixtures/readerIntentContract.ts` (new), `src-tauri/src/{commands.rs, main.rs}` (eight passthroughs).
- Tests: the six new backend files and four new vitest files above; `tests/test_mobile_allowlist.py`; `screens/reader/voices.test.tsx`; 29 files' head-fixture paths.
- References: the Configuration and Database references regenerated (head 208, 873 leaves in 58 sections), `_scripts/db_generate_reference.py` (three section descriptions), `Maps/LearnLoop Pipeline Map.md` (the RW1b bullet).

## 8. Open questions (with the default taken)

1. Should a missed formative answer's named prerequisite reach the learner field's weak prerequisite signals (placement's fast track) and the sooner check, as a reader question's does through the mvp-0.16 rule? **Default: yes, as for reader questions (no successor)**; the alternative is a filter on `source_kind = 'reader_formative'` in `field/signals.learner_gap_targets` and the check advance, which would itself be a serving change to decide.
2. Offer "quick check on this passage" (§4.2's Consolidate) on a plain selection, as a `recall`-style selection row? **Default: no** (UX §4.1 omits it; the inquiry's check stays on the reconnect line).
3. Delay a reconstruct item's first serve to its `due_hint` before DL2 lands? **Default: no** — that is a scheduling change (a successor); the receipt says "later", and DL2 reads the date.
4. A dedicated key for the fold's "show" (UX §4.3's "one-key unfold")? **Default: none beyond the focusable *show* button**; candidates are `u` or Alt+↓, which RW3a uses for marks.
5. When "change" follows a capture that already ran, undo it automatically? **Default: no** — the capture keeps its own undo; the pick runs too.
6. After undoing "reconstruct this later", may the same selection be reconstructed again? **Default: no** (the row stays escalated; its key is used). A second try needs a new selection.
7. The recap's Wrap up should count an answered next-step question as activity (RW6a reads `answered_at`) even after "show me" with no answer? **Default: yes**, as RW6a reads it.

## 9. Friction notes for RW4a, RW1c, RW2b and RW3b

1. **RW4a**: add Orient's *what do I need first?* and Transfer's *where else is this explained?* / *where is this used?* as rows in `reader_intent.ACTIONS` (with `needs=("library",)` and an `Availability.library` flag from its switch); the palette, the Decider's options, the contract and `readerIntentContract.ts` follow (the fixture test pins the copy). *Practice this question* is the same `find_practice` call as DL3's; add it once that RPC exists. *Another way* already uses `find_sources(intent="alternative")`; RW4a's library answer can replace its card with the comparing posture.
2. **RW1c**: the tutor's *another way* under an answer is the same `find_sources` call `useActiveReading.anotherWay` makes (with every passage shown in the inquiry excluded); reuse it. The routed Ask goes through `submitAsk` with `answerMode`; RW1c's three answer modes per answer are the tutor's, not the router's.
3. **RW2b**: `workbench_text` is admitted by migration 208 and the dispatcher returns nothing for it: add `workbench_text_text(...)` in `text_gaps/sources.py`, a READER task for it beside `READER_FORMATIVE_TASK`, and its kind-state surface (already named). No further widening is needed (if the adaptive-hints spec's `hint_feedback` kind is wanted, it needs one; RW1b did not add it, as nothing reads it yet).
4. **RW3b**: the *try the next step first* cue (`▹┆`) should start `activeCtl.start("next_step", [span], localFold([span]))` — the same RPC, fold and card; a cue tap is the learner's act, so the card may open Notes. Named gaps from `reader_formative` texts (now with `answer_basis`) are cue targets as reader questions' are.
5. **All**: `ReaderScreen.tsx` is 3,014 lines; RW1b's behaviour lives in `screens/reader/`; the Reader's single-key shortcuts must check `intentBox.open` if a new one is added outside the box's capture handler (the box swallows printable keys while it shows).

## 10. Owner-run commands

None needed: no paid call was made (fakes only), and nothing here runs in a batch. To look at it on a copy: make a backup-API copy into `fixtures-local/` (`learnloop.db.copies.copy_tree_with_databases`), `uv run learnloop doctor --fix-state --vault <copy>` (applies migration 208 under the coordinator), then `LEARNLOOP_VAULT=<abs path to the copy> npm run dev` from `apps/learnloop-tauri`. Select a line of a worked example: the box appears without taking focus; type *quiz me later* and pause, then ↵; or Tab → *let me try the next step*. The Decider routing needs the OpenRouter key (`openrouter_decider`, about $0.0004 a call, at most 200 a day); without it every routing asks. Switches in the copy's `learnloop.toml`: `[reader_intent] enabled = false` (today's selection), `speculative_enabled = false` (route on Enter only), `[reader_active_reading] enabled = false`, `[reader_formative] enabled = false`. `uv run learnloop reader report --json --vault <copy>` shows the `intent` and `active_reading` rows.

## 11. Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, `uv run --no-sync` after the install; both suite lanes under `flock /tmp/learnloop-fullsuite.lock`. No paid or live model call: every test uses fakes (`StructuredClientFake`, the router's `FakeDecider` priced at the listed input price, the gap fakes).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken |
| `pytest -n auto -q -p no:cacheprovider` (full suite), on `266a9a271` | **13,022 passed, 2 xfailed**, 0 failed (21 min 18 s, while another stage held the machine). Base 12,941: +81 (the six RW1b files 68, the mobile pins +9 and a registry check, the firewall case, the report and fixture-drift tests). The first run (on `c89c84851`) had 10 failures, all fixed in `266a9a271`: the parameter registry did not classify the three new numeric leaves (7 tests), the judge-route disclosure test's route set (1), the widening test's `shutil.copy2` of migration text tripping the file-copy audit (1), and the mvp-0.8 cutover's registry audit (1) |
| `pytest -m durability` | **107 passed**, 12,917 deselected (1 min 58 s); base 106 + the widening test's durability case |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **119 files, 959 tests passed** (base 936; +23: IntentBox 15, nextStepFold 4, intentSwitchOff 3, recapCopyBasis 1). One run while the full suite held the machine timed out 6 unrelated tests (vault switching, the detour strip, 5 s timeouts); the next run passed 959 of 959 |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, exit 0 (eight passthroughs) |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py`, `module_validate.py` | regenerated (schema head 208, 327 table notes, 873 configuration leaves in 58 sections); errors []; passed (1,119 notes, all reachable); passed |
| `test_config_refactor.py` (19 snapshots recomputed, the template `.pyc` cleared), `test_coordinated_migrations.py`, `test_migrations.py`, `test_table_roles.py`, `test_architecture.py`, CLI help and RPC pins | pass (in the full suite); CLI help unchanged |

**Pre-existing, not RW1b:** `desktop_validate.py` stops on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts` ("unclassified desktop source"), as recorded at RW6a. **Not done:** no adversarial (Codex) review in this stage; no real-UI look (the screens are exercised through the real `ReaderScreen` in jsdom, where ranges have no geometry, so the box's placement under the selection is exercised only by its fallbacks). No vault was opened: no manual run, no copy under `fixtures-local/`; the tracked fixture vaults are untouched.
