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
* **The submit's fold still counts by the window.** A question asked under one serve's key, the item skipped and served
  again with a new key, folds into the next attempt on the item (B3's window, unchanged evidence semantics), though the
  new serve's thread starts empty. Folding by key would change classification again (another successor); left as is.
* **The help record** lists the questions answered in this visit; a thread restored from the transcript after a
  remount is shown in the panel but not re-listed in the record line.
* **The successor's number.** `fix/rebuild-equivalence` (`c8a138009`) also names its bounded-replay successor
  `mvp-0.34`. Both are one constant; whichever lands second renumbers (and moves its predecessor).
* **Q4's measurement.** An assisted cold follow-up leaves its measurement to be withdrawn at the next serve (the repair
  ends unmeasurable, honestly). Whether a fresh cold retry should be scheduled instead is a scheduling decision for the
  owner.

## 4. Gate (targeted; the full suite runs once in the landing gate)

Every command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`; pytest at `-n 6` or
fewer, vitest at `--maxWorkers=4`, one test run at a time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| pytest, the new file `tests/test_reader_ca2_one_ask.py` | 30 passed |
| pytest batch 1 (35 files: the successor's chain pins and the contracts, below) | 1,258 passed, 14 skipped, 5 failed (chain-tail pins and the CLI help snapshot this stage moves); fixed, then the 5 files plus `test_ad_guard.py`, `test_ad_protected_tables.py`, `test_architecture.py`, `test_reader_ca2_one_ask.py`, `test_sidecar_tutor_qa.py`, `test_capture_route_recovery.py`: 217 passed, 3 skipped |
| pytest batch 2 (151 files that exercise a changed module, below) | 8,948 passed, 3 skipped, 2 xfailed, 6 failed; fixed (B3's budget assertion is K5's now; two tests of other things pin the panel off; the recovered capture answer carries its mode; RW1c's golden strips the new receipt), then the 6 files: 119 passed, and `test_reader_tutor_switch_off.py` 2 passed |
| `npm install`, `npm run typecheck`, `npm run frontend:build` (apps/learnloop-tauri) | clean, clean, built |
| vitest, new: `src/components/AskOverlay.panel.test.tsx`, `src/screens/PracticeScreen.ca2OneAsk.test.tsx` | 12 passed, 7 passed |
| vitest, touched (148 files: `src/components/AskOverlay*`, `src/screens/PracticeScreen*`, `src/screens/workbench`, `src/screens/practice`, `src/screens/reader`, `src/screens/ReaderScreen.workbench`, `.inquiry`, `.inquiryOff`, `src/screens/FeedbackScreen*`, `src/app`) | 1,341 passed, 5 failed: all in `src/app/App.fixRound4.test.tsx`, 5 s timeouts under the parallel load; alone 9 passed |
| cargo check | not run: nothing under `src-tauri` changed (no new RPC; `ask_tutor_question` and `get_tutor_transcript` are passthroughs) |
| durability lane, DB reference scripts | not run: no migration, no DB or connection code, no schema change (`source_context_json` and `answer_mode` already exist) |

**Batch 1:** `test_ad23_successor.py test_field_workbench_signals.py test_intent_codex_rereview.py
test_method_explicit_upgrade.py test_mvp09_upgrade.py test_mvp010_upgrade.py test_mvp011_upgrade.py
test_mvp013_upgrade.py`-`test_mvp018_upgrade.py test_mvp020_upgrade.py`-`test_mvp024_upgrade.py
test_reading_step_switch.py test_recurrence_commands.py test_regrade_contract_successor.py
test_required_method_grading.py test_route_rules_in_grader.py test_serve_eligibility_review.py
test_serve_eligibility.py test_plan_follows_path.py test_config_refactor.py test_cli_help_snapshot.py
test_sidecar_serializer_snapshot.py test_sidecar_contract.py test_desktop_rpc_contract.py test_mobile_allowlist.py
test_architecture.py test_table_roles.py test_constraint_engine.py`.

**Batch 2** (every test file naming `tutor_qa`, `reader_modes`, `reader_dialogue`, `reader.ask`, `served_check`,
`intent.checks`, `config_dto`, `tutor_qa_prompt`, `certification_cold_probe`, `remediation`, `ask_tutor_question`,
`get_tutor_transcript`, `BoundAsk` or `reader_tutor`, less those in batch 1): test_ad1_attempt_columns.py test_ad1_codex_review_fixes.py test_ad1_fix_round4.py test_ad1_reading_opportunities.py test_ad23_contract.py test_ad3_dose_arm.py test_adaptive_difficulty_ad1.py test_ai_config.py test_assumed_known.py test_authoring_contract.py test_capture_desktop.py test_capture_route_recovery.py test_causal_attribution_p0.py test_causal_attribution_p2.py test_causal_cold_outcomes.py test_causal_factor_deferral.py test_causal_orchestrator.py test_causal_p2_acceptance.py test_causal_repair_sidecar_rpcs.py test_certification_cold_probe.py test_chatgpt_plan_provider.py test_chatgpt_plan_workspace.py test_codex_lockdown_round2.py test_codex_lockdown_round3.py test_codex_output_schema.py test_codex_tool_lockdown.py test_coldness_receipt.py test_collection_dataset.py test_common_repair_delivery.py test_compare_sources_keep.py test_daily_loop_reader_authored_practice.py test_daily_loop_reader_retire.py test_daily_loop_reference_adoption.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_diagnostic_probe_freshness.py test_dialogue_causal_join.py test_dl2_rw4b_keyed_pick_check.py test_e0_delivery.py test_embedding_route_isolation.py test_exam_protection.py test_exam_protection_review.py test_field_signal_production_paths.py test_figure_offers.py test_figures_rw5b_fix_round2.py test_figures_rw5b_review.py test_followup_diagnostic_selection.py test_forecast_receipts.py test_goal_certification_any_of.py test_goal_series.py test_guided_redo.py test_held_grade_evidence.py test_hint_kill_switch.py test_hypothesis_surface_wiring.py test_instrument_servability_journeys.py test_instrument_serving.py test_integration_daily_loop_field.py test_intent_checks.py test_intent_codex_review.py test_intent_fix_round4.py test_intent_fix_round5.py test_intent_orchestrator_rulings.py test_intent_plan.py test_judge_routes.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_review.py test_library_ask.py test_library_ask_review.py test_mcp_c1a_landing.py test_migrations.py test_misconception_transitions_intake.py test_model_usage_report.py test_output_budget.py test_owner_capture_1025.py test_p2_leakage_suite.py test_p3_journeys.py test_pfc_unassessed_readers.py test_pf_generation.py test_pinned_span_bridge.py test_placement_opening_probes.py test_placement_signals.py test_plan_first_transport_grant_scope.py test_plan_first_transport_offer_grants.py test_plan_first_transport.py test_post_attempt_pipeline.py test_prescription_passages.py test_primed_attempts.py test_probe_remint.py test_question_context.py test_question_promotions.py test_question_queue.py test_question_signal.py test_quick_check.py test_reader_activity.py test_reader_branches.py test_reader_dialogue.py test_reader_guidance.py test_reader_inquiry_kill_switch.py test_reader_inquiry_status.py test_reader_intent.py test_reader_observation_records.py test_reader_passage_check.py test_reader_recap.py test_reader_recap_review.py test_reader_recap_review_r2.py test_reader_reconnect.py test_reader_report.py test_reader_rw1b_review.py test_reader_rw1c_review.py test_reader_tutor_offers.py test_reader_tutor_retrieval.py test_reader_tutor_switch_off.py test_reader_wrap_up.py test_remediation_cold_retry.py test_retrieval_interventions_write_points.py test_reveal_ledger.py test_rw2c_switch_off.py test_rw4_kill_switches.py test_salience_firewall.py test_scheduler.py test_scoreboard.py test_sidecar_measurement.py test_sidecar_reader_p3.py test_sidecar_reader.py test_sidecar_remediation_surfaces.py test_sidecar_source_retrieval.py test_sidecar_teach_back.py test_sidecar_tutor_qa.py test_source_retrieval_followup.py test_source_retrieval_guards.py test_source_retrieval_rereview_cost.py test_source_retrieval_rereview.py test_source_retrieval_search.py test_source_retrieval_tutor.py test_source_space_resolver.py test_structured_transport_parity.py test_stuck_prompt.py test_teacher_te0_confidence_events.py test_tutor_citations.py test_tutor_delivery_fixes.py test_tutor_practice_request.py test_tutor_promotion_w2.py test_tutor_qa.py test_tutor_tool_requests.py test_ux_phase1_connect_ai.py test_ux_phase1_landing.py test_ux_phase1_usability_round1.py test_ux_phase2_shell.py test_ux_phase4_feedback.py

No paid or live call was made: every model is a fake, no vault was opened, no provider was routed.

## Landing onto main (batch 3: Reader CA2 + Reader RW5d P1 + local retrieval P2, 2026-10-26)

The three stages land together (owner-approved batch landing) on `merge/batch3-onto-main` in `learnanything-merge2`,
cut from `main` at `1335df0c0` (latest `mvp-0.34`, migrations through 222, head fixture `migration_head_222`, Reader
CA1 just landed). Main was neither fast-forwarded nor pushed. The same section is appended to all three stages'
records; the stage-specific owner notes and open items are at the end.

### Commits and conflicts

| Commit | What |
|---|---|
| `043463103` | `--no-ff` merge of `reader/ca2-one-ask` (`ebfbfe7e5`, base `eae00d58a`). Conflicts composed keeping both sides: `algorithm_versions.py` (the chain gains `ONE_ASK_ALGORITHM_VERSION` after `REPLAY_LEDGER_ALGORITHM_VERSION`), `cli/app.py` (help text, `--to` dispatch, refusal text name 0.33, 0.34 and 0.35), `config/schema.py` (`ReplayConfig` and `AskConfig`), `template.py` (23 snapshot hunks: main's notes kept, CA2's note added, renumbered "inert below mvp-0.35"), `parameter_registry.py` (C0a's and CA2's rules), `sidecar/context.py`, `handlers/practice.py`, `handlers/sessions.py` (CA1's `pageSeen` and CA2's `earlierOpened` draft flags side by side: `_with_keyed_flag` and `_with_earlier_opened`, `draft_page_seen` and the earlier-marker helpers), `api/client.ts`, `PracticeScreen.tsx` (CA1's as-printed imports and `OpenInSource` modal beside CA2's `DockedAsk`; the book component stays `bookCarried \|\| pageSeen`, CA2's `earlierCounted` beside it; both draft flags in the checkpoint and its deps), 45 test files (main's absolute chain indices and head paths kept; the version pins moved below), the reference notes (main's side, then regenerated). CA2's `migrations/221_workbench_earlier_opened.sql` renamed **223**; its `fixtures/migration_head_221` dropped (main's 222 kept for the rebuild). CA2's `one_ask_upgrade.py` rewritten to the journalled activation (below). The stale practice-cap wording fixed (below). |
| `bdd511fa6` | `--no-ff` merge of `reader/rw5d-p1-show-me` (`33b9aa5d8`, base `eaf9859ad`). Conflicts: `template.py` (24 hunks, RW5d's `[figures] show_me_enabled` note on every tag), `AskRail.tsx` (CA2's Enter-sends branch and RW5d's `alt+Enter` *show me ▸* branch both kept, CA2's `enterSends` label kept on the ask button, RW5d's show-me row and thread lines after it), `tests/test_mobile_allowlist.py` (the desktop-only list names both `READER_CA1_RPCS` and `READER_RW5D_RPCS`; CA2 adds no RPC). Migration 224 keeps its number. |
| `54aef20c7` | `fixtures/migration_head_224` **rebuilt** from main's tracked, sanitized `migration_head_222/state.sqlite`: a backup-API copy, 223 then 224 applied under `UPGRADE_SCRATCH_COPY`, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1), integrity ok, `foreign_key_check` empty, copied into place with the backup API, no companion files. Every table's rows equal main's 222 except `schema_migrations` (+223, +224); against RW5d's own head only `workbench_sessions` differs. Git records it as the rename `migration_head_222 -> migration_head_224`; README updated. |
| `de25dd4fa` | Earlier migrations' schema-diff tests through 223 + 224 (`[..., 222, 223, 224]`, `CA2_ALTERED_TABLES = {"workbench_sessions"}` beside RW5d's sets); CA2's migration test renumbered `test_223_adds_only_the_earlier_opening_column` (from 222, applies [223, 224], head 224); chain pins at mvp-0.35; all 26 defaults fingerprints recomputed (template `.pyc` cleared). |
| `88ac84275` | `--no-ff` merge of `retrieval/lr-p2-query-student` (`3d3755578`, base `eaf9859ad`). Conflicts: `parameter_registry.py` (RW5d's `figure_admission` and LR P2's four module owners), `template.py` (24 hunks, LR P2's `[embedding.local]` student keys and route note on every tag). Fingerprints recomputed again (26, from the composed defaults). |
| `930abc06e` | References and CLI help (below). |
| `867f7934a` | `tests/test_batch3_landing.py`: the chain and journal tests and interactions (i)-(iv); the activation journal's docstring names `one_ask_upgrade`. |
| `9a3dbdeba` | The last tests pinning mvp-0.34 as the latest (LP claim fixes' version set, rebuild equivalence's bare upgrade, mvp-0.18's default target); version comments. |
| `8ef8338e8` | The landing records. |
| `bfea40a29` | Gate fix: the query student's start wait without a caller deadline is bounded by `SOCKET_TIMEOUT_S` (fail-first test); references regenerated (0 errors). |
| `fe7143aa2` | Gate fix: RW2c's two switch-off pins drop CA2's additive workbench keys at their unused values; landing test (iv)'s data root per test. |

`main` and all three stage tips (`ebfbfe7e5`, `33b9aa5d8`, `3d3755578`) are ancestors of the tip. Against main the diff
adds **no tracked database or binary apart from the head fixture rename** (`git diff --numstat -M main` lists only
`fixtures/{migration_head_222 => migration_head_224}/state.sqlite` as binary); the root `.gitignore` is unchanged.

### Renumbering and the chain

- `ONE_ASK_ALGORITHM_VERSION = "mvp-0.35"`, after `REPLAY_LEDGER_ALGORITHM_VERSION` (`mvp-0.34`, rebuild equivalence;
  `mvp-0.33` is the LP claim fixes). `LATEST_ALGORITHM_VERSION` is `mvp-0.35`; `ONE_ASK_VERSIONS == {"mvp-0.35"}`; the
  snapshot `mvp-0.35` is recorded; the earlier `*_VERSIONS` sets each gain `mvp-0.35`.
- `one_ask_upgrade.py` now follows `replay_ledger_upgrade.py`: `PREDECESSOR = mvp-0.34`, the chained predecessors
  `mvp-0.9 .. mvp-0.33` go through `upgrade_to_replay_ledger` first; the activation is ONE `BEGIN IMMEDIATE`
  transaction under the vault mutation lock (the predecessor's manifest, `activate_p0_projection`, the registry
  refresh, the journal (`predecessor`, `target`) at the shared `<db>.claim-fixes-activation` path, the durable
  publication last); the completion marker is the `p0_projection_activation` receipt under the tag. Its
  `complete_interrupted_activation` completes a journal naming mvp-0.35 and hands any other to rebuild equivalence's
  (which hands an mvp-0.33 journal on). The CLI (`cli/runtime.py`) and the desktop sidecar (`sidecar/context.py`) now
  install `one_ask_upgrade.complete_interrupted_activation`, the chain's latest.
- `learnloop upgrade --to mvp-0.35` works from mvp-0.9, 0.27, 0.29, 0.30, 0.31, 0.32, 0.33 and 0.34
  (`test_upgrade_to_mvp035_works_from_every_supported_version`, 8 cases); the bare `upgrade` targets mvp-0.35. The
  upgrade's help and refusal text name every tag; `tests/cli_help_snapshot.json` changed only for `upgrade`.
- New keys move no unrelated version hash: `test_eval_harness.py`, `test_success_head*.py` and the field arm tests pass
  as merged (the arm hashes read `[mastery]` only).

### The practice Ask cap (fixed at landing; owner decisions 2026-10-26)

`config/template.py`'s `[tutor_qa]` comment and `TutorQAConfig`'s description said practice was "per item+session".
They now say: **per attempt; enforced on metered routes; unlimited on the subscription (ChatGPT plan) route while
`[ask] panel_enabled`** (off, the cap applies on every route). The cap stays `max_questions_practice = 3` in
`<vault>/learnloop.toml` `[tutor_qa]`, beside `max_questions_feedback` (per attempt), `max_questions_library` (per note
per UTC day) and `max_questions_reader` (per span per UTC day). The code (`tutor_qa.question_usage(metered=...)`) was
already CA2's final rule; no behaviour changed.

### Interactions (`tests/test_batch3_landing.py`; no break found, so no fix)

- **(i) CA2's cap vs RW5d's *show me*.** RW5d's spec §6.2 sends the Ask rail's text "as a figure goal instead of a
  question"; CA2's K5 cap counts question events. A tutor `figure_goal` press and an Ask-rail *show me* each build a
  figure, write no `question_events` row and leave the practice and library budgets as they were, at mvp-0.35 with the
  panel on (`test_i_...`). P3's Ask-panel *show me* (a figure as a hint-equivalent) is not built yet.
- **(ii) CA2's `earlier_opened_at` vs CA1 and rebuild equivalence.** The column is LIFECYCLE state on a WORKFLOW table;
  replay never reads it. A workbench submit with an earlier opening carried into steps rebuilds exactly as the same
  submit without it: mastery 0, facets 0 (`test_ii_...`). **Finding (pre-existing on main, not the batch):** on that
  real-clock sidecar path the shadow rebuild moves the submitted item's `due_at` by 1 s (live 1 s later): reproduced
  3/3 on `git archive main` at mvp-0.34 with a plain workbench submit. The owner parity below (frozen clocks) is 0/0/0.
  CA1's as-printed page reads and writes no learner state (its parity stands).
- **(iii) T1's offer keying vs CA2's routes.** A grant given on `figure.request` (even naming `tutor_qa`) never routes
  CA2's Ask (`ask_tutor_question`) to OpenRouter; a grant given on the Ask itself routes it to OpenRouter, which is
  metered (`is_subscription_transport` false), so the per-attempt cap applies there; the plan route stays unlimited
  with the panel on (`test_iii_...`; fake OpenAI client, nothing sent).
- **(iv) LR P2's resolver vs RW5d's grounding.** RW5d grounds a goal through `find_sources_for_caller`. With an adopted
  (fake) student behind `spaces.LOCAL_QUERY_ENCODER` and `default = "local:grouped"`, the hook is live (it tries to start
  the query process); with `embedding.local.student = false` it starts nothing and the grounding retrieval's status and
  hits equal P1's empty hook exactly (`test_iv_...`).

### Regeneration

- `db_generate_reference.py` then `db_validate_reference.py`: **errors []** after the prose counts were updated by hand
  (Configuration.md and Database.md: **1,064 leaves in 74 sections, 353 table notes**). No new `CONFIG_SECTION_FUNCTIONS`
  entry was needed (CA2 brought `ask`; `figures` and `embedding.local` existed). ~425 other note changes are
  `source_commit` stamps.
- `validate_vault.py`: passed (1,161 notes).
- `tests/cli_help_snapshot.json`: `upgrade` only. RPC contract, serializer snapshot and mobile allowlist pass as merged.

### Gate (at `9a3dbdeba`, the fixes at `bfea40a29` and `fe7143aa2`; `env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`; logs in `fixtures-local/landing-batch3/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` (+ `uv pip install pypdfium2`), 5G scopes; `lint-imports --no-cache` | **36 kept**, 0 broken |
| targeted run (104 files: every stage's tests, the chain/migration/pin files, contracts), `-n 6`, 5G | 2,188 passed, 3 failed (stale latest-version pins, fixed in `9a3dbdeba`, 42 passed on rerun), 25 skipped, 3 xfailed, 26 min |
| `tests/test_batch3_landing.py` | 24 passed |
| full suite, run 1 (at `9a3dbdeba`, `flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50`) | **hung.** Started 20:18:49 after the thread-leak stage's lock; reached 99% by 21:06:40, then no line. One worker held ~737 leaked threads at ~1,100% CPU; it was SIGKILLed at 21:36 as a worker of this run, xdist never replaced it, and the other 7 workers sat in `futex_wait` (load ~0.6). The kill of the rest of the tree was refused by the permission layer; the owner stopped the scope at 22:03 (`rc=143`). |
| durability (`-m durability`, at `8ef8338e8`; the later commits touch only the student's start wait and tests) | **138 passed**, 1 skipped (46 s) |
| full suite, run 2 (at `8ef8338e8`, with `-o faulthandler_timeout=600 --junitxml`) | **hung again at 99%** and was stopped at 00:09 (`systemctl --user stop` of its own scope, `rc=143`). Five 10-minute dumps: four are a leaked-thread worker whose dump is cut at faulthandler's 100 threads (64-69 `post_attempt_worker._loop` threads, 14-29 `_run_reading_sweep` threads, the 4th inside `sweep_reading_requests` / `pending_reading_requests`), so their main thread (the test) is not shown; the reading-request sweep frames place them in the leak class (`test_reader_rw1c_review.py` leaks the sweep and post-attempt threads into `test_reading_request_sweep.py`). The fifth names **`test_query_student.py::test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start`**, main thread in `student_encoder.py:352 encode -> _await_ready(deadline=None)` from `search.py:558 _resolved_meaning`: an unbounded wait for a starting student. It passes alone (3/3, 2.5 s), but a stalled student process would hang production retrieval the same way, so it was **fixed** (`bfea40a29`: without a caller deadline the start wait is bounded by `SOCKET_TIMEOUT_S`, the registered `keep` guardrail, and a student that never becomes ready is a `TimeoutError`, i.e. the resolver's `encoder_late`; fail-first test `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`, which hung >20 s before). `test_query_student.py` 51 passed + torch lane re-run (51 passed, 1 skipped) after the fix. |
| the two leak-class files alone | `test_reading_request_sweep.py`: **14 passed** (58 s). `test_reader_rw1c_review.py`: does not finish alone in 25 min (sys-CPU-bound leaked threads, no single test over 10 min); in 300 s it makes the same progress on `git archive main` as on the merge (282 vs 283 results), so it is the known leak (the fix/test-thread-leak stage), not this batch |
| full suite, run 3 (at `bfea40a29`, the two leak-class files `--ignore`d, `faulthandler_timeout=600`, `--junitxml`, `-rfE`) | **41 min 11 s; 21,563 passed, 18 failed, 89 skipped, 41 xfailed.** Failures: the **10 Codex CLI 0.164.0** tests (same set as main's tree); **2 real, fixed** (below); **6 load/leak**, each passing alone: `test_plan_first_transport_offer_grants::test_p1_…` and `test_reading_hardening_2_fixes::test_f1_…` (known flakes, 3/3 alone, 47 s), and four `test_query_student.py` tests (`…starts_lazily_serves…`, `…kill_switches_take_the_student…`, `…resolver_serves_the_adopted_student…`, `…resident_gpu_student_yields…`) whose thread-served fake student did not start within the now-bounded 30 s on the leaked-thread worker (`encoder_late` instead of the earlier hang); the file passes alone and 3× under `-n 4` with the landing tests. One 10-minute dump (cut at 100 threads, leak class) during `test_f1_…` (1,408 s). **Top 10 durations:** `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep` 1,407.9 s; `test_evsi_multisim::test_cli_multisim_quick_fits_every_family_and_reports_claims` 275.3 s; `test_ad23_successor::test_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest` 183.6 s; `test_batch3_landing::test_upgrade_to_mvp035_works_from_every_supported_version[mvp-0.9]` 153.7 s; `test_recurrence_commands::test_the_upgrade_command_defaults_to_the_latest` 123.9 s; `test_mvp011_upgrade::test_existing_vaults_keep_their_version_until_the_owner_upgrades` 119.2 s; `test_mvp016_upgrade::test_upgrade_command_defaults_to_the_latest` 116.0 s; `test_mvp015_upgrade::test_upgrade_command_defaults_to_the_latest` 114.2 s; `test_mvp020_upgrade::test_upgrade_through_the_chain_from_mvp013_to_mvp018` 109.1 s; `test_recurrence_commands::test_the_upgrade_command_prints_the_advisory_guard_status` 96.5 s (all 50 in `fixtures-local/landing-batch3/logs/full3.log`) |
| the 2 real failures, fixed (`fe7143aa2`) | `test_rw2c_switch_off::test_with_all_four_switches_off_the_sequence_equals_the_base_codes` and `test_rw2c_fix_round2::test_fr2_3_…restores_the_base_payload` failed deterministically: RW2c's byte-identity pins against `7e7bdff1b` met CA2's additive workbench keys (`earlierHints` 0, `earlierOpened` False), which sit outside RW2c's switches. The pins now drop exactly those keys at exactly those unused values before comparing (`tests/rw2c_base_sequence.LATER_STAGE_KEYS`); 18 passed. `test_iv` now keeps the student's data root per test (`XDG_DATA_HOME`). |
| Codex lockdown on main's tree (`git archive main`, alone) | the same 10 fail on codex-cli 0.164.0: `test_codex_isolation_mcp_check` ×3, `test_codex_lockdown_round2` ×3, `test_codex_lockdown_round3` ×3, `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled` |
| torch lane (`uv sync ... --extra pdf`; `tests/test_query_student.py` + `_gpu.py`; then the standard extras re-synced, torch gone) | 50 passed, 1 skipped (the GPU smoke) |
| owner lane (`-m owner_vaults`, backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-batch3/`) | 83 passed, **6 failed: exactly the 6 known** (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests, `test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`); 0 `model_call_receipts` |
| `npm install` (esbuild's postinstall blocked as before), `npm run typecheck` | clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **221 files, 1,917 tests passed** (61 s) |
| `npm run frontend:build`; `cargo check` | built (the usual chunk-size warning); finished |
| empty dirs | `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` stayed empty; `HOME` gained `.nv/ComputeCache` (the torch lane's CUDA cache) and `.local/share/learnloop` (landing test (iv) wrote the student's data root there before it set `XDG_DATA_HOME`; fixed in `fe7143aa2`, removed) |

### Parity (backup-API copies of the mvp030 backups; `fixtures-local/landing-batch3/`, scripts in `scripts/`)

Setup: `orig/` = backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`;
`u34/` = `orig` brought to **mvp-0.34 with main's code** (routes to the `127.0.0.1:9` blackhole, 64 tasks on main and 65
on the merge (LR P2's `retrieval_query_generator`), none outside it; `upgrade --to mvp-0.34`, `rebuild-derived-state` ×2).
`code_main` = `git archive 1335df0c0`, `code_merge` = `git archive 867f7934a` (src and migrations unchanged since). Every
run through `env -i` with empty dirs; `run.py`'s audit hook refuses Codex process starts and non-loopback sockets.

- **(a) main vs merge at mvp-0.34** (after the primary sidecar load; a second main copy as the noise control): every
  row of all 357 common tables identical (18,806 rows LA, 8,195 probability); the merge adds only 224's objects
  (`figure_requests` empty, its indexes and triggers) and the new columns (`interactive_figures` ×12,
  `workbench_sessions.earlier_opened_at`), all NULL; `schema_migrations` +223, +224, common rows identical; integrity
  ok, foreign keys 0, `model_call_receipts` 0. Certification, Today and the plan **byte-identical** main vs merge (and
  main vs main). `rebuild --shadow` **0/0/0** both sides; `doctor` identical (57/1 LA, 101/48 probability, pre-existing).
- **(b) `upgrade --to mvp-0.35`** (the merge's code, on copies of u34): "mvp-0.34 -> mvp-0.35", no journal left. **Rows:
  every row kept; mastery and every schedule unchanged (0 LOs, 0 items moved).** What changes, exactly: the
  `algorithm_version` stamp (0.34 -> 0.35) and `updated_at`/`created_at` of `facet_recall_state` (76 / 2 rows) and
  `facet_capability_evidence` (36 / 1) (DERIVED, the projection activation), `parameter_registry.updated_at` (352, the
  refresh), plus one `derived_state_rebuilds` (`p0_projection_activation`), one `parameter_registry_manifests` row.
  Shadow right after the upgrade: facet 0, **mastery 21 / 18 = the `mastery_state` version stamp only** (no value moves),
  schedule 0, as at RW7b's projection-only activation; after `rebuild-derived-state` ×2: **0/0/0**; doctor unchanged.
  After a primary load + 12 live attempts (frozen clock): **0/0/0**. Bare `upgrade` -> mvp-0.35. From the mvp-0.30
  backup straight `--to mvp-0.35` (chains through 0.31-0.34) and the owner's two steps (`--to mvp-0.34`, then
  `--to mvp-0.35`), rebuilt: **0/0/0**, doctor unchanged. **Nothing changes until CA2 is used.**
- **(c) the kill switches** (`[ask] panel_enabled`, `cold_help_converts`, `[figures] show_me_enabled`,
  `[embedding.local] student` all false): set before the upgrade (k35), or after an on upgrade then rebuilt (kr35),
  versus the merge's mvp-0.34 copy: certification, Today, mastery and every schedule identical after the version
  stamp; the plan identical except 7 hashes over the versioned card (`card_hash`, `snapshot_hash`), exactly as the
  rbeq landing recorded for its tag; the switches-on copy (on35) the same. (a) shows the merge at mvp-0.34 equals main.
- **(d) an interrupted mvp-0.35 activation** (the upgrade dies with `os._exit(17)` after the config publication):
  label mvp-0.35, journal present, the predecessor's mastery untouched. `upgrade --to mvp-0.35` completes it ("completed
  the interrupted activation of mvp-0.35"; again: "vault is already mvp-0.35"); the desktop start completes it; both
  equal the clean upgrade (0 LOs moved). Every attach that may not complete it refuses with "The upgrade to mvp-0.35
  did not finish ... run `learnloop upgrade --to mvp-0.35`" (`Repository`, `open_vault_repository` without a
  completer, the secondary attach, and the remote schema check as `SchemaMismatch`), leaving the vault as it was. Plain
  `doctor --json` is a read-only attach and refuses too (the journal stays), as recorded at the LP and rbeq landings.
- **Receipts and calls.** The 42 parity databases with a receipts table and the 3 owner-lane copies hold **0
  `model_call_receipts`** (the other 21 files are the probability backup's empty `.learnloop/state.sqlite` stubs); no
  audit-log line (no process start, no socket). **Spend: $0.** Nothing under `~/learnloop-vaults`, `~/learnloop-retired`
  or `~/learnloop-books` was opened or listed.

### Owner notes

- **Before upgrading:** back up the vaults; close the desktop app, the MCP server and the phone page. Then
  `learnloop upgrade --to mvp-0.35 --vault <vault>` (or the bare `learnloop upgrade`); from mvp-0.30 it chains through
  0.31-0.34 (mvp-0.34's step is the whole-vault rebuild). Migrations 223 and 224 apply on the first open.
- **Kill switches (`<vault>/learnloop.toml`):** `[ask] panel_enabled = false` (the overlay and per-source answer mode
  as before), `[ask] cold_help_converts = false` (the predecessor's cold rules, no downgrade), `[figures]
  show_me_enabled = false` (RW5b's figures exactly), `[embedding.local] student = false` (the query student never
  serves; P1's retrieval).
- **The practice Ask cap:** `[tutor_qa] max_questions_practice` (default 3) per attempt on metered routes; unlimited on
  the ChatGPT plan route while the panel is on.
- **Local retrieval P2 stays off until you run its setup** (`docs/reviews/retrieval-local-p2-query-student.md`,
  "Commands for the owner"): `embeddings local setup` (adopting the cached 9B), `embeddings local index`,
  `embeddings local student setup` (adopting the two 0.6B bases), then `student plan`, `generate`, `targets`, `train`,
  `evaluate`, `adopt` / `reject`, `status`, each with `--dry-run` first.

### Open items

- **The leaked-thread class still hangs a full run at 99%** (`test_reader_rw1c_review.py` and the reading-request sweep). Run 3 excluded those two files; they are the fix/test-thread-leak stage's. Rerun the whole suite once that lands.
- **Fixed at landing:** the query student's unbounded start wait (`bfea40a29`) and RW2c's two switch-off pins vs CA2's keys (`fe7143aa2`).
- **Low (pre-existing, main):** a real-clock workbench submit leaves `practice_item_state.due_at` 1 s later than a
  rebuild computes (interaction (ii)); frozen-clock parity is 0/0/0.
- **Low (recorded since LP):** `doctor --json` refuses an interrupted activation rather than completing it.

### Open items for Reader CA2

- **F2 (Low, on the record):** strategy questions are not routed to the hint service; that routing is H4's (Codex
  review F2's rejected part). Leak control and the take step apply to every practice Ask answer meanwhile.
- The successor renumbered **mvp-0.35** (this record's §1 and the spec's as-built note say mvp-0.34, the branch's
  number); migration renumbered **223** (221 on the branch).
- Carried from §3: K9's "just show me" recognition, H4's strategy answers, the earlier-attempt count across a restart,
  the window fold, Q4's measurement.
