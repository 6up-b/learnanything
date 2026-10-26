# Reader CA2: one Ask panel

Stage `reader-ca2-one-ask`, branch `reader/ca2-one-ask` in `learnanything-dl2`, base `eae00d58a` (main with RW7b
`mvp-0.32`, mobile PR-1, the owner-capture 1025 fixes = CA0, the Reader Compare/Ask and curriculum specs). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §7 (CA2), §11 K5-K11, §13 (the successor ruling and the kill switches) and §15
Q1-Q6 (owner decisions 2026-10-25). Fakes only: no live model call, no paid call, no vault touched.

## 1. The successor ruling (§13, K10): yes, `mvp-0.34`

The task's rule: if the unified rule changes an attempt's classification beyond today's `hints_used` meaning, stop and
make it a successor. Two of CA2's rules do, so they ship as one successor with one kill switch; everything else is
presentation or keeps the existing meaning and ships behind the panel's own switch with no tag.

| Rule | Today (`mvp-0.32`) | CA2 | Classification change? |
|---|---|---|---|
| **K10, the Reader's cold Ask** (`tutor_qa.py`'s bound row, `reader_dialogue`'s cold link row) | every cold question is hint-equivalent (L6), whatever its `question_type` | only a substantive one (`HINT_EQUIVALENT_TYPES`), as practice already does | **yes**: a cold check with a Reader clarification question stays *on your own* instead of becoming practice with help |
| **Q4, help on a cold follow-up** (`cold_retry`, `certification_cold_probe`) | submit refuses a hinted attempt (`COLD_CHECK_ASSISTED`), so the simple shell withholds hints ("No hints on this one") | the take step; submit admits the attempt as practice with help | **yes**: an attempt the predecessor refused is now recorded (assisted), and what submit admits changes |
| K6, *earlier on this question* opened before Submit | (no such door) | one hint-equivalent, said first | no: `hints_used` += 1 with its existing meaning (the book-left-open rule, spec §5.4) |
| Practice Ask's own rule (§7.7) | substantive questions count | the same | no |

So: `ONE_ASK_ALGORITHM_VERSION = "mvp-0.34"` (one constant, after RW7b's `mvp-0.32`; the LP claim fixes hold `mvp-0.33`
on their branch), `ONE_ASK_VERSIONS`, `learnloop upgrade --to mvp-0.34` (`learnloop/one_ask_upgrade.py`, RW7b's chained
pattern: the predecessor, or `mvp-0.9` onwards through the chain; anything older refused), the defaults snapshot, and
the kill switch **`ask.cold_help_converts`** (default true). Below the tag, or switched off, both rules are the
predecessor's exactly (`serve_eligibility.help_converts_active`).

**Persisted meaning.** Nothing recorded is rewritten or re-read under the new rule: replay reads the stored
`question_events.hint_equivalent` and `practice_attempts.hints_used`, never the rule. The one place an assisted attempt
could now meet a cold measurement (the repair cold retry's and the certification probe's consumers) skips it
unconditionally (`remediation.assisted_attempt`); before the successor submit refused such an attempt, so no recorded
attempt reaches that branch and replay is unchanged. The projection, scoring weights and FSRS are untouched: an
assisted attempt is dampened by its `hints_used` as any hinted attempt is.

## 2. What changed

### Backend

* **Q4, help converts a cold follow-up** (`serve_eligibility._decide_submit`, `attempts.submit_decision`): under the
  rule, a hinted submit on a due cold follow-up is `SERVE` with reason `COLD_CHECK_HELP_TAKEN`, claims no task (the cold
  measurement is not answered by an assisted attempt), primed or not (the help may have shown the answer). With no help
  taken, every predecessor refusal stands (a primed or auto-primed unassisted draft is still refused). The consumers
  (`remediation.record_remediation_attempt`, `certification_cold_probe._record_probe_outcome`) leave the task open for
  an assisted attempt; the next serve withdraws it with the existing typed disposition
  (`COLD_CHECK_PRACTISED_SINCE_SCHEDULED`, causal outcome `unmeasurable_no_held_out_surface`).
* **The take step on a cold follow-up** (`intent.checks`): `served_check` no longer serves a "Check once" on a cold
  follow-up item in the measured view (no help offered) under the rule, and `cold_followup_view` gives a due cold
  follow-up with no "Check once" the cold view (the banner, the ladder header, locators hidden until feedback, D46).
  The practice serve attaches it as `intentCheck` (`handlers/practice.py`).
* **K10** (`reader_modes.BoundAsk.cold_counts_every_question`, set by `handlers/reader_tutor.bound_ask`;
  `reader_dialogue.ask` and `_record_cold_hint_equivalent`): under the rule a cold Ask counts only when substantive; the
  cold link row stores the tutor's `question_type` instead of `other`. Leak overlap still writes its reveal row whatever
  the type (unchanged code).
* **K5, the attempt's thread** (`tutor_qa.practice_thread_events(submission_id=)`, `ask_question(submission_id=,
  workbench_session_id=, about_step=)`): a practice question stores `source_context.attempt_key` when it is asked (no
  migration: `source_context_json`); the thread, the turns the tutor is given and the transcript are the submission's.
  A question recorded before CA2 has no key and keeps B3's window rule. **The budget** is a money bound per item per UTC
  day while the panel is on (K5: "its window doesn't reset per serve"; B3 had made it per attempt).
* **K7** (`handlers/tutor_qa._ask_panel_inputs`): `ask_tutor_question` takes `submissionId`, `workbenchSessionId`
  (refused unless that workbench session is bound to the question's item), `aboutStep` (said to the tutor with the
  steps) and a one-question `answerMode`. Policy and counts stay the server's.
* **§7.4, the help style is the answer mode** (`tutor_qa.HELP_STYLE_ANSWER_MODES`): *let me struggle* → ask me first,
  *balanced* → help me reason, *guide me* → answer directly. The adapter resolves the mode from `hints.help_style` (a
  workbench session's per-problem style wins, D31) for practice and feedback, and the Reader's `reader.ask` uses it when
  the client sends none (Q5). The practice prompt gains `_TUTOR_QA_PRACTICE_MODE_TASKS` (every mode inside the practice
  context's leak control) and the version suffix `+answer-mode-v1`; with no mode the prompt and version are today's.
  The answer's mode is stored on the row (`question_events.answer_mode`; AD's reading sweep reads only reader and
  library rows, so nothing reads practice rows' mode) and returned.
* **The receipt** (§7.5): every Ask answer's `source_context.receipt` names the model, prompt version and agent run its
  `question_type` came from (the question event lacked them).
* **K6, earlier on this question** (`tutor_qa.earlier_threads`, `handlers/tutor_qa._earlier`): the practice and feedback
  transcripts carry the item's earlier attempts' help, newest first (each attempt with a date, how it ended in the
  evidence vocabulary, its questions and its hints), `earlierCountsAsHint` (practice: true; feedback: false) and
  `cold` (server-derived: a cold "Check once" or a due cold follow-up; then the list is empty). Nothing earlier enters
  any model context (C6).
* **Config**: `[ask] panel_enabled` (the presentation's switch, no tag) and `cold_help_converts` (the successor's),
  both classified in `parameter_registry` (structural kill switches: the model's typed `question_type` decides, no new
  weight, margin or threshold). The app snapshot sends `ask` only while the panel is on. One guardrail constant,
  `tutor_qa.EARLIER_THREADS_LIMIT = 20`, labelled `keep` (a display bound on how much history one panel loads).

### Frontend (`apps/learnloop-tauri/src`)

* **One component, three hosts** (`components/AskOverlay.tsx`, `variant`): `modal` (the library, capture and Reader
  overlay contexts keep it), `docked` (practice and feedback: `components/DockedAsk.tsx`, a 360 px column, resizable
  and remembered, a sheet over the lower half below 1,040 px) and `inline` (under the focused workbench step). The panel
  parts: the context line with chips (`about › Exercise 6.1.12 · your draft ×`, `step 3 · your steps 1–4`, *ⓘ what's
  sent*), the stored help style (`components/askPanel.tsx`, `StoredHelpStyle`), the thread with one voice label per
  answer (`◇ model · about step 3 · helping you reason · counts as a hint` / `a clarification · free` / on a cold check
  `counts as help` / `a clarification · still on your own`), book first (`§ from your books` chips, else *Your books
  don't cover this directly — this is LearnLoop's model's explanation*), the box with the cost said before sending, *change*
  for one question's mode, and *earlier on this question ▸ · opening one counts as a hint*. Esc closes the panel, never
  the screen; ↵ in the box never reaches the screen's ^↵.
* **The practice screen** docks the panel instead of App's overlay, and in Work in Steps `?` (and the palette, and
  "ask about this step · ?") opens it inline under the focused step (`Workbench.renderAsk`, `askSignal`); a question
  about the whole problem sits at the foot of the steps. The live draft (or the steps) is read when the question goes.
  The help record line (`helpRecordLine`, K8) lists hints, the book left open, an earlier attempt's help and each
  question with its cost; in steps the questions join the workbench's footer. An earlier attempt opened before Submit
  adds one to the submitted `hintsUsed` (as the book does), once per submission key, and never to `authoredHints`.
* **Cold** (§7.7): the banner changes to *Practice with help ◌ — you asked about the maths* only after a substantive
  answer; a cold follow-up served with the take step (Q4) offers Hint through the ladder's header instead of "No hints on
  this one" (without it, the predecessor's copy and behaviour stand).
* **The Reader** (Q5): the rail's mode select is replaced by the help style (one stored preference); the Reader's
  working posture asks inline under a step when the problem is bound to an item in a practice session, instead of
  *"Ask the tutor is beside the book. Leave for now…"*. Feedback's Ask docks beside feedback (and no longer counts as an
  overlay covering the answer).
* **The hint panel** shows *help style: …* beside its `⋯` menu (C7).

## 3. Not built in this stage (open questions)

* **K9, a request for the answer through the take step.** Recognizing "just show me" before answering needs a model's
  typed judgment logged in `judgment_ledger` (§7.5) or H4's strategy routing; neither exists yet. The practice context's
  Socratic prompt and leak overlap accounting apply to every Ask answer as before.
* **Strategy questions answered by the hint service (H4)** and the workbench's *help so far ▸* thread in the help
  column: not built (H4 waits on its own checkpoint). Inline panels show their own exchanges; the docked panel shows the
  attempt's whole thread.
* **The diagnostic block's one line** (*Ask opens after this short set · your question is kept*): Ask stays hidden and
  refused during a diagnostic block, as today.
* **The earlier-attempt count across a restart.** It is client-counted (like the book left open, with no new ledger
  kind: `interaction_events.kind` and `help_assists.assist_kind` are CHECK-constrained, so a durable row needs a
  migration). A restart mid-attempt forgets that it was opened; opening it again counts it again (the link says so).
* **Q4's measurement.** An assisted cold follow-up leaves its measurement to be withdrawn at the next serve (the repair
  ends unmeasurable, honestly). Whether a fresh cold retry should be scheduled instead is a scheduling decision for the
  owner.

## 4. Gate

See the stage's structured result (the exact commands and counts are recorded there and below once run).
