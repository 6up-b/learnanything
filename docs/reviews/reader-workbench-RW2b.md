# Reader workbench RW2b + adaptive hints H3: checks and adaptive help in the workbench (stage `reader-rw2b-h3`)

Branch `reader/rw2b` in `learnanything-merge4`, base `7d4c5f4ce` (the H2b landing, migration head 212).
Specs: `spec_reader_workbench_v1.md` §5.2-5.5, §5.6, §5.8, §5.9, §14 (G5, G7, G8, G9, G12, G33, G36,
G37, G38, G60, G62, G63, G64), §20.11; `ux_reader_workbench_v1.md` §4.0, §4.10, §5.2-5.11, W5-W7,
moments 5-6; `spec_adaptive_hints_v1.md` §10 H3, §16 (incl. §16.4), G-H3, G-H5..G-H8, G-H15, G-H16.
Friction notes read: RW2a §5 and its open questions, H2a §9, H2b §9 and its landing.

## 0. Plan (written before the code)

**One hint service (G64).** Every workbench hint, its kind and the suggested rung come from
`learnloop.hints`. The service gains the workbench surface through one new module,
`learnloop/hints/workbench.py` (the H3 extension), and small surface-gated branches in
`service.py` (the request's `surface` instead of the `practice` constant; the workbench's options,
choice, step rules and row columns when `surface = 'workbench'`). With `surface = 'practice'` every
path, prompt, row and result is byte-identical to H2b (pinned). H2a's fold, fence and delivery,
H2b's answer-box hand-off (`ServerHintFold.window_fold`) and H1's map lifecycle are not touched.
The Reader side (`learnloop/reader/workbench_help.py`, `workbench_check.py`) defines no writer,
chooser or map builder: an import-linter contract keeps `learnloop.reader` and the workbench
handler off `learnloop.hints.writer`, `.chooser`, `.map_builder`, `.options` and `.contracts`, and a
test greps the Reader for the hint routes.

**The ladder (§5.2, §5.5).** `workbench.suggest_help` asks the service for the suggested rung
(one Decider request over the five rungs' (kind, level) options and the horizon, sampled, the
propensity logged in the `hint_choice` ledger row; 3 s time box). With the chooser off, timed out
or unavailable the suggestion is the Reader's progression: rung 1, then one above the last rung
offered or taken on that step (offers are salience-only `workbench_help_offered` events). Taking
is `workbench.request_help {takenLevel 1-5, suggestionId?}`: the suggested rung serves the drawn
option (joint propensity, `level_source = offered`); another rung draws its kind from the same
Decider vector renormalized over that level (conditional propensity, `learner_pick`), 1 where the
level has one option; under the fallback each rung has its fixed kind (L1 approach question, or
the discriminating question with rivals open; L2 localize; L3 the item's next authored hint,
then `next_step`; L4 continuation; L5 walkthrough; propensity 1). With two or more rivals open on
the about-step, level 1's only option is `discriminating` (G37); `workbench.discriminate_enabled`
off removes it. After a waypoint on the step, levels 3+ aim at its target and `next_step` toward
it is among them; "a smaller step toward this goal" and "show me the book's way" are H2a's picks.

**Steps in the contract (rules 1-3, 7).** The request carries the steps with ids, the last check's
verdicts and graph, the about-step and `continue_from` (computed by the Reader from the check:
the last standing step before the about-step that does not depend on the first questionable step;
"that's not where I'm stuck" moves the about-step to the picked step). The writer receives them as
a `workbench` block in its prompt (absent on the practice screen, so its prompt is unchanged). The
service checks, in code, beyond H2a's shared rules: a quote lies inside one existing step; at
level 2+ the about-step is quoted; what stands lies in standing steps only; with a map the
placement starts from the node the `continue_from` step reached. A failure is re-asked once, then
H2a's level-3 `next_step` downgrade.

**Check my work (§5.2, §5.3).** `workbench.check` (a job): route `workbench_check` (chat,
structured output: per step `valid | questionable | unchecked`, the reason quoted, `depends_on`,
`assumption`, the map node and route reached, a declared symbolic transformation; the first
questionable step; the error-kind guess with its alternatives). **Never on Codex** (the request
path; spec §5.8 sets a 10 s p50 and recommends a ChatGPT-plan or fast OpenRouter profile, and does
not allow Codex): refused before any call, saying why, like `hint_writer` (D9). Symbolic checks
run FIXED sympy code per declared kind (equivalence, differentiation, integration incl. definite,
substitution, solving, limits, sums, inequalities (numeric sampling labelled "checked
numerically"), boundary and normalization) inside the PF-b sandbox, each with a negative control
(a perturbed result must be rejected, else the check confirms nothing); no model-written code
runs. No bubblewrap: every verdict is "model's reading". Map nodes are validated against the
current map through `learnloop.hints.workbench.place_steps` (an unknown node is dropped; a valid
step on no route is `new_route`); `hints.maps.enabled` off names none. A check row is a
`help_assists` row (`assist_kind = 'check'`, counted by the server), prepared then shown on
delivery through H2a's `deliver_hint` (its fence), inside a workbench guard (below). Caps:
`workbench.max_calls_per_session` (24) and `workbench.max_daily_cost_usd` ($1.00 metered, at
`workbench.price_per_million`); hint calls stay on the hint service's money caps.

**Evidence (§5.4, G5, G-H3).** The workbench sends no client count. `submission_plan` folds the
session's shown, server-counted, unattached workbench rows (one per check and per level 1-3 hint,
`primed` for 4-5) with the same store function the record line reads (`help_assists.workbench_fold`),
beside the book and the carried hints; the answer box's hints still come by H2b's window fold
(workbench rows carry no practice session until Submit, so the window never sees them). No count
is lost to a race: `workbench.submit` first stamps the submission's admission time on its rows
(H0's own stamp, now made before the plan is read), and a workbench row is delivered only while
its row has no submit stamp, checked in the delivery's own transaction; so every row is either
shown before the plan reads the fold or never shown. `held_hints` (RW2a) counts an open problem's
workbench rows, so a submit from the answer box records them too. Reveal basis
`workbench_hint:<kind>:L<n>` (the authored kind exempt, H2b's ruling). A hint-free workbench
submit is byte-identical to main (pinned).

**Learner text (§5.6), in-session.** Adapter `workbench_text` (migration 208 already admits it):
roles `stuck` (a stuck step's newest version, queued when Help, Check, Leave or Submit sends it),
`hint_feedback` and `discriminate_answer` (the workbench's `help_assists` rows, queued when
written). A named gap joins the next request's rivals (H2b's `open_rivals` reads the item's gaps).

**Bridging, trace, report.** After a hint is delivered in the Reader, a background bridge
(`TutorSpanProvider`, practice context, unchanged) writes a `bridge` row (never counted) with the
verified passage; the hint shows "finding the matching step in the book…" meanwhile and never
waits. The split diagnoser's context gains the step trace (assists in order with kind and level,
the step graph, the error-kind guesses labelled as guesses, discriminating questions with
answers; never a map) under `+workbench-v1`, only when a trace exists. `learnloop hints report`
gains a `workbench` block: checks (latency, verdict methods, kinds), rung taken vs suggested by
facet and week, recovery after a check, "doesn't connect" by shortcut and kind, goals after a
waypoint, discriminating asked/answered/skipped against the diagnoses.

**Config.** `[workbench]` `help_enabled`, `symbolic_checks_enabled`, `discriminate_enabled`,
`error_kind_enabled`, `bridge_enabled` (all on), `max_calls_per_session = 24`,
`max_daily_cost_usd = 1.00`, `price_per_million` (unset); route `ai.routing.workbench_check`;
every key classified in `params/parameter_registry.py`. Off, `workbench.help_enabled` restores RW2a
byte for byte (pinned).

**Frontend.** `ReaderScreen.tsx`'s working posture moves to `reader/ReaderWorkingPosture.tsx`
first. New in `screens/workbench/`: `HelpLadder.tsx` (choose and take separate), `CheckColumn.tsx`,
`StepHints.tsx` (hint cards under their about-step, the feedback box with four shortcuts and the
step picker, the discriminating answer box, the picks, the bridge line), `HelpStyleControl.tsx`
(the header's per-problem override), `whereThisGoes.ts`, `useWorkbenchHelp.ts`; the record line
and footer name every assist; the answer-confidence row (RW2a open question 3). The practice
screen's "Work in steps" gets the same ladder (no bridge: no book there).

**No migration.** `help_assists` already has every workbench column and CHECK value (H0), and 208
admits `workbench_text`.

## 1. What was built

| Part | What | Commits |
|---|---|---|
| Plan | §0 above | `cf8d06d45` |
| Backend | the hint service's workbench surface (`learnloop/hints/workbench.py` + surface-gated branches), the new package `learnloop/workbench/` (check, symbolic, ladder, bridge), the store's fold, the submit's stamp-then-fold, `workbench_text`, the diagnoser trace, config, route, registry | `ac1caec92` |
| Frontend + report | the ladder, the check column, hints under their steps, the help style, the working posture split out, eight passthroughs, the report rows | `1e38affc9` |
| Tests, snapshots, references | fourteen backend test files, `HelpLadder.test.tsx`, the recomputed config snapshots, the regenerated references, the two learner-text pins | `ade492eb1`, `7c00d4329`, `024081749`, `e5de819c2` |
| Record | this file | (last commit) |

**Paid calls: none ($0.00).** Every model is a fake in the tests; the one manual run (below, §6) was on a backup-API copy of `fixtures/probability` under `fixtures-local/smoke-rw2b/` with every key unset and empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`: 0 receipts, 0 `hint_choice` rows.

### 1.1 The one hint service, on the workbench (H3; G64)

* `learnloop/hints/workbench.py` is the surface's extension: `WorkbenchHintContext` (the live steps numbered, the last check's verdicts and step graph, the first questionable step, the about-step, `continue_from`, the standing steps, the check's error-kind guess and rival readings, the offered rung, the suggestion's judgment id, the header's help style, the picked step); the step graph (`standing_steps`, `checkpoint_for`, `dependents`); the ladder's options (`ladder_options`, `taken_options` = H2a's `build_options` plus the workbench's constraints: the discriminating switch, rung 1 is the discriminating question only on the check's first questionable step with two or more rivals (G37), a goal's target kept on the step through a smaller step and later Help); `suggest` (H2a's chooser over the five rungs, `where` = the Reader workbench, the check's typed summary and map placement, never a step's text); `taken_choice` (the suggested rung serves the drawn option with its joint propensity; another rung draws from the same vector renormalized over that rung, seeded `seed:L<n>`, the conditional propensity logged; one option at the rung: 1; argmax: 1; no judgment: the rung's fixed kind, propensity 1); `check_steps` (the exact rules 1-3 and 7); `row_columns`; `deliver_workbench`; `place_steps` and `current_map_for` (the Reader reads maps only through the service); `text_leaks`.
* `service.py`: `HintRequestV1.workbench` (required with `surface = 'workbench'`, refused otherwise); `_validate_workbench` (a "More" request takes a rung 1-5; a reply or a pick has no taken level); the row's `surface` is the request's; the workbench's options, choice (`_choose_workbench`: the suggestion's draw, else one conditional Decider request over the taken rung's options while the chooser is on, else the fixed kind), rules (`check_steps` after H2a's `check_output` in each round) and columns; a taken rung 1 or 2 is never downgraded to a level-3 hint (it would raise help the learner did not take); the item's own hints serve rung 3 while the writer cannot run. `chooser.ask` gained `where` and `extra_state`, `writer.build_prompt` a `workbench` block, `record_discriminate_answer` a `surface`: each absent on the practice screen, whose prompt, state, rows and results are unchanged (the H2a/H2b suites pass).

### 1.2 Check my work (§5.2, §5.3; G9, G12, G38)

`learnloop/workbench/check.py`: route `workbench_check` through `PaidCalls`, strict output `WorkbenchCheckOutputV1` (per step: verdict, reason, quote, `depends_on`, assumption, map claim, declared transformation; the first questionable step; the error-kind guess, its reason and two or three rival readings; assumptions). Validated in code: unknown steps, later dependencies and foreign quotes dropped and recorded in `contract_failures_json`; a reason that would give the answer away replaced; the first questionable step recomputed from the verdicts; map claims validated by the service (`new_route` kept; an unknown node dropped; only valid steps placed). Refused before any call on Codex (`codex_refused`), with `LEARNLOOP_WORKBENCH_MODELS=off`, unrouted, unpriced on a metered route, at `workbench.max_calls_per_session` (receipts of the problem plus its bridges) and at `workbench.max_daily_cost_usd` (`SharedDailyEnvelope`, owner kind `workbench_check`). The same steps checked again answer with the last check and count nothing. The view the learner sees has no node or route (the map contains the solution).

`learnloop/workbench/symbolic.py`: the model declares the kind and its inputs (sympy syntax, as data); a FIXED harness checks them in the PF-b sandbox (`run_sandboxed_python`): equivalence, differentiation, integration (an antiderivative up to a constant, or a definite integral), substitution, solving, limits, sums, boundary values, normalization and inequalities (sampled, `checked_numerically`). A verdict is trusted only when its controls behave: sympy's true result must be accepted and a perturbed one rejected (for an antiderivative, plus the variable). A passing claim is `✓ checked`, a failing one `≠` (the step becomes questionable); otherwise, or without bubblewrap (`sandbox_unavailable`), the model's reading. `workbench.symbolic_checks_enabled` off runs nothing.

### 1.3 Evidence (§5.4; G5, G-H2, G-H3)

* `help_assists.workbench_fold`: one per shown check and per shown level 1-3 hint, `primed` for a shown level 4-5 hint, over the problem's `surface = 'workbench'`, shown, server-counted, unattached rows. `submission_plan` reads it (`SubmissionPlan.help`, `hints_used` = book + carried + help, `primed`), and so does the record line (`record_line(help_fold=…)`: *2 hints (a check, a level-3 hint) → practice with help ◌*, the footer *help used: a check, a level-3 hint*; the keys are RW2a's exactly when the problem has no help).
* `workbench.submit` stamps the submission's admission time on the problem's rows (H0's `stamp_submitted`, under the key `workbench:<session>`) BEFORE it reads the plan; `deliver_workbench` refuses, inside H2a's own delivery transaction, any row with that stamp. So a row is shown before the fold is read (and counted) or never shown; H2a's fold, fence and delivery are unchanged.
* The window fold (H2b's ruling R1) never sees workbench rows: they carry no practice session until Submit, when `bind_workbench_rows` sets it and the attempt (by key).
* `held_hints` counts an open problem's fold and the new `held_primed` primes every submit of the item, so the answer box's submit records the help an open problem holds (RW2a's held rule extended to RW2b's rows).
* Reveal basis `workbench_hint:<kind>:L<n>`; the item's own hints exempt (H2b's ruling).

### 1.4 The ladder's Reader side and the RPCs

`learnloop/workbench/ladder.py`: `hint_context` (module docstring), `fallback_level` (rung 1, then one above the last rung offered or taken on the step, up to 5: the hint rows' `offered_level`/`level` and the salience-only `workbench_help_offered` events), `hint_views` (resume restores the hints, their answers and bridges), `queue_stuck_texts`, the unavailable lines (UX §5.6). `learnloop_sidecar/handlers/workbench_help.py`: `workbench.check`, `.suggest_help`, `.request_help`, `.help_job`, `.cancel_help`, `.answer_discriminating`, `.set_help_style`, `.help_state` (jobs, as H2a's; the read that returns a ready check or hint delivers it; a delivered hint in the Reader starts the bridge job). Every one refuses `help_disabled` before reading or writing; `not_bound` before setup; a diagnostic block refuses before any model. The RW2a handler: the stamp-then-plan, `primed=plan.primed`, the bind after commit, Leave and Submit queue stuck texts, a bind schedules H1's background map build. The config DTO carries `workbench.help {enabled, bridge}` only while on.

### 1.5 Learner text, trace, bridge, report

* `workbench_text` (`diagnosis/text_gaps/sources.py`): roles `stuck` (a stuck step's version, by SQL on `workbench_steps`), `hint_feedback` and `discriminate_answer` (the workbench's `help_assists` rows); readable and non-serving; queued by `enqueue_workbench_text` (pipeline and help both on); the practice screen's `hint_feedback` adapter never takes a workbench row. Provenance: H2b's `hint_feedback_record` (the item's solution an input).
* The split diagnoser's `CurrentAttempt.workbench_trace` (`diagnosis/split/workbench_trace.py`, by SQL on `help_assists` of the attempt's submission): the assists in order with the work before each, the step graph, the guesses labelled as the check's guesses, discriminating questions with answers; no node or route; prompt version `diagnosis-v1-split+workbench-v1` only when a trace exists. The blind grader sees the composed steps only (tested).
* `learnloop/workbench/bridge.py`: T6's `TutorSpanProvider` in the practice context (item-bound scope, verified spans) after a hint is shown in the Reader; a `bridge` row counted by neither, shown on its read; never on the practice screen.
* `learnloop hints report` gains `workbench` (`hints/report_workbench.py`, `workbench-help-report-v1`): checks, rung taken against suggested by facet and ISO week, kinds by rung, recovery after a check, "doesn't connect" by shortcut and kind and its rate, goals after a waypoint and smaller steps, discriminating asked/answered/skipped and diagnosed after, latency p50/p95 of both routes. Present only when the vault has workbench rows; `build_hints_report` is unchanged.

### 1.6 Frontend

`ReaderScreen.tsx`'s working posture moved to `reader/ReaderWorkingPosture.tsx` (RW2a friction note 5; 3,144 → 3,080 lines). In `screens/workbench/`: `helpModel.ts` (every fixed line, the shortcuts, the help styles, *where this goes* with the source kind each box routes to, the rungs, the choose/take reducer, the labels), `useWorkbenchHelp.ts` (jobs paced 350 ms rising to 1.5 s; exactly what the delivering read returns is rendered; resume restores), `HelpLadder.tsx` (five rungs at once, digits/arrows choose, ↵ takes, ▸ *suggested (why?)* with the form and a split judgment), `CheckColumn.tsx` (the 120 px verdict column, the first questionable step's quoted reason and *(model's guess)*, assumptions, stale line, the sandbox's absence), `StepHints.tsx` (hints in the model's voice under their about-step, the item's own hints in a neutral voice; *a smaller step toward this goal*, *this doesn't connect…* with the four shortcuts, the step picker and *say more*, *show me the book's way*, the discriminating answer box, the bridge line that peeks the passage, showing the book first when it is hidden), `HelpStyleControl.tsx` (the header's per-problem style), `WhereThisGoes.tsx`. `Workbench.tsx`: *check my work · counts as a hint · ctrl+k*, *help · ctrl+h*, Ctrl+Shift+H, the optional confidence row (RW2a open question 3), the dependency outline on focus. With `workbench.help` absent every element is absent and the RW2a markup is unchanged (`switchOff.test.tsx`, `Workbench.test.tsx` unchanged and green). The practice screen's *Work in steps* is the same component, so the same ladder (no bridge there).

## 2. Deviations (each recorded)

1. **A package of its own, `learnloop/workbench/`**, for the check, the symbolic harness, the ladder's Reader side and the bridge, not modules under `learnloop/reader/`: the hint service and the source-retrieval envelope already import the Reader, so a Reader module importing them made a package cycle (`frozen-cross-package-cycles`). The RW2a scratchpad stays `learnloop.reader.workbench`. The new package is added to `evidence-never-reads-the-workbench`, and `workbench-calls-the-one-hint-service` keeps it and `learnloop.reader` off the writer, chooser, options, contracts, discriminating, maps and map builder (G64).
2. **The service's extension points are additive surface branches** (§1.1): no H2a fold, fence, delivery or contract function was reworked; `HintRequestV1` gained one optional field, `chooser.ask`, `writer.build_prompt` and `record_discriminate_answer` optional keywords, `downgrade_allowed` one clause (a taken rung 1-2), `authored_fallback_allowed` one clause (rung 3).
3. **No count is lost to a race without touching H2a's fold**: the submit stamps first and delivery refuses a stamped row (§1.3), instead of extending `ServerHintFold`. A refused submit (a cold check with the book, grading unavailable) leaves its stamps: a row still pending then is never shown (the job answers *not shown*; ask again); rows already shown are counted at the next submit.
4. **Symbolic checks run fixed code per declared kind** (the model supplies only the kind and expressions), not a model-written sympy check: no model-written code runs, and the controls are sympy's own result and its perturbation.
5. **The check never runs on Codex.** It is on the request path; §5.8 sets a 10 s p50 and recommends a ChatGPT-plan or fast OpenRouter profile and nowhere allows Codex, so D9's rule for `hint_writer` applies (orchestrator note 3).
6. **The same steps checked again count nothing** (the last check stands): a check names what it found, and the same finding again tells nothing new.
7. **A workbench row's `work_hash` is its placement**: the about-step's id and text (the whole work without one), so "two hints on the same step" (rule 5) and "one at a time" per step (G37) are exact; the work's length stays in `work_chars`.
8. **A question that tells explanations apart is offered only on the check's first questionable step** (UX §5.8 "when"; spec §5.2), with two or more rivals: elsewhere rung 1 is an approach question (`excluded = no_questionable_step`).
9. **The suggestion is the `hint_choice` ledger row** (its id is the `suggestionId` a take sends); its `left_id` is a reserved assist id that names no row. The take's row carries the offered rung, the drawn option and the propensity.
10. **Offers are salience-only events** (`workbench_help_offered`, and `help_style_changed`), RW2b's `HELP_WORKBENCH_EVENTS`, kept out of RW2a's pinned tuple.
11. **Stuck text is queued when it is sent** (Help, Check, Leave, Submit), by version, never on every saved keystroke.
12. **The config DTO nests the switch**: `workbench.help` (the RW2a `workbench` key is unchanged with it off).
13. **Not built in this stage** (§8): the separate verification of a hint's own checkable claims (§5.3 "hints are verified separately"), *a short problem instead* (§5.2, optional on the sources spec), the rail's tabs in the header's `⋯` (RW2a open question 5).

## 3. Gates covered

| Gate | Where |
|---|---|
| G5 (all rows) | `test_workbench_assistance.py`: no help; a check; each level 1-3; levels 4-5 primed; book + check + three hints with one record line; the reveal basis; the authored exemption; cancelled and unread; the admission fence; the window with an answer-box hint (counted once each); the answer box's submit holds an open problem's help; a discriminating answer changes nothing; abandoned and rebuild; a hint-free submit identical with help off |
| G7 | `test_workbench_hints.py`: no step cited, a quote across steps, continuing from the questionable step, the about-step not quoted, the map start node, a taken rung 2 never raised; kind contracts and rule 6 through H2a's suites |
| G8 | withheld leak (`test_workbench_hints.py`); a check's reason never states the answer (`test_workbench_check.py`); bridging through T6's item-bound practice context, never delaying the hint |
| G9 | `test_workbench_check.py` (checked only when the sandbox ran with its controls, no bubblewrap, switch off, undeclared kinds), `test_workbench_check_kinds.py` (every declared kind, true and wrong, real sandbox) |
| G12 | Codex refusal, per-problem cap, unpriced and daily cap (`test_workbench_check.py`); chooser time box and fallback (`test_workbench_chooser.py`); hint calls on the service's caps (H2a) |
| G33 | `test_workbench_hints.py`: not where I'm stuck (moves, keeps the level, `hint_fit`), the strategy change, the notation, a different approach, the text reaching the next hint |
| G36 | `test_workbench_text_gaps.py` (reading writes only gap tables), `test_workbench_step_graph.py` (the guess writes no diagnosis or error event), `test_workbench_discriminate.py` (no posterior or probe observation) |
| G37 | `test_workbench_discriminate.py` (ten tests) |
| G38 | `test_workbench_step_graph.py`, `test_workbench_check_map.py`, `test_workbench_trace.py` |
| G60 | `test_workbench_hints.py::test_a_hint_sits_under_its_about_step…`, `HelpLadder.test.tsx` |
| G62 | `HelpLadder.test.tsx` (the footer and record line name the check), `test_workbench_chooser.py` (one rung higher per press), `test_workbench_text_gaps.py::test_each_boxs_where_this_goes…` |
| G63 | `test_workbench_chooser.py` (kinds of their rung, no goal without a map, the goal kept and the smaller step, joint and conditional propensities, the seed, argmax, fallback, the learner's picks) |
| G64 | `test_workbench_hint_service.py` (monkeypatched `request_hint` and `suggest`, the contract, the routes, the rows) |
| G-H5..G-H8, G-H15, G-H16 | the H2a/H2b suites (unchanged, green) plus the workbench tests above |
| Switch-off pins | `test_workbench_help_kill_switch.py`; `test_workbench_check.py` (every RPC refuses); `switchOff.test.tsx`, `HelpLadder.test.tsx` (frontend) |
| Mobile | `test_mobile_allowlist.py` (eight RW2b RPCs pinned desktop-only, four RW2a RPCs it extends) |

## 4. Tests

New backend files (121 tests, all passing): `test_workbench_assistance.py` (16), `test_workbench_check.py` (17), `test_workbench_check_kinds.py` (6, real sandbox), `test_workbench_check_map.py` (3), `test_workbench_chooser.py` (13), `test_workbench_discriminate.py` (9), `test_workbench_help_kill_switch.py` (1), `test_workbench_hint_service.py` (5), `test_workbench_hints.py` (16), `test_workbench_in_session_gaps.py` (2), `test_workbench_report.py` (1), `test_workbench_step_graph.py` (6), `test_workbench_text_gaps.py` (6), `test_workbench_trace.py` (3); builders `tests/workbench_help_fakes.py` (`CheckFake`, `wb_answer`). Frontend: `HelpLadder.test.tsx` (14). Changed pins, each moved by RW2b on purpose: `test_judge_routes.py` (the route `workbench_check` disclosed), `test_reader_formative_texts.py` and `test_learner_text_gaps_flow.py` (`workbench_text` is readable now and swept), `test_mobile_allowlist.py`, `tests/conftest.py` (`LEARNLOOP_WORKBENCH_MODELS=off`).

## 5. Files

Backend: `src/learnloop/hints/{workbench,report_workbench}.py` (new), `hints/{service,chooser,writer}.py`, `src/learnloop/workbench/{__init__,check,symbolic,ladder,bridge}.py` (new), `reader/workbench.py`, `db/stores/help_assists.py`, `diagnosis/split/{workbench_trace}.py` (new) and `{context,contract,diagnoser,jobs,live}.py`, `diagnosis/text_gaps/{sources,jobs,contract,pipeline,provenance}.py`, `config/{schema,template}.py`, `ai/{routing,disclosures}.py`, `params/parameter_registry.py`, `cli/hints.py`, `learnloop_sidecar/handlers/{workbench_help}.py` (new), `handlers/{workbench,practice,__init__}.py`, `learnloop_sidecar/context.py`, `pyproject.toml`. Frontend: `apps/learnloop-tauri/src/screens/workbench/{helpModel.ts,useWorkbenchHelp.ts,HelpLadder.tsx,CheckColumn.tsx,StepHints.tsx,HelpStyleControl.tsx,WhereThisGoes.tsx,HelpLadder.test.tsx}` (new), `Workbench.tsx`, `stepModel.ts`, `useWorkbenchSession.ts`, `screens/reader/ReaderWorkingPosture.tsx` (new), `ReaderScreen.tsx`, `api/{client,dto}.ts`, `app/algoConfig.ts`, `src-tauri/src/{commands,main}.rs`. Docs: this file; the regenerated configuration and database references (906 leaves).

## 6. Gate (this step; the full suite, the whole durability lane and the whole vitest run happen once, in the landing gate)

All with `TMPDIR=fixtures-local/tmp`; `/tmp/learnloop-fullsuite.lock` was free (`flock -n`) before each pytest run.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** (25 before RW2a's base plus `workbench-calls-the-one-hint-service` new; `evidence-never-reads-the-workbench` widened to `learnloop.workbench`) |
| `uv run pytest -n auto` over the 152 files below (every new test file, every file exercising a changed module found by `git grep` for `learnloop.hints`, `hint_service`, `learnloop.reader.workbench`, `help_assists`, `diagnosis.split`, `text_gaps`, `submit_attempt`, `workbench.`, the hints report, `app_snapshot`/`config_dto`, disclosures, and the contract tests: config defaults snapshot, CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table roles, registry audit, judge routes, tracked fixture databases, coordinated migrations, the PF sandbox) | **3029 passed, 2 xfailed** (284 s) |
| `uv run pytest -n 8 -m durability` over the hint, RW2a and workbench files (the store's new functions) | **2 passed** |
| `uv run pytest --durable-sqlite tests/test_workbench_assistance.py tests/test_workbench_check.py` (WAL, production pragmas) | **36 passed** |
| `npm install` (up to date), `npm run typecheck` | ok |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.workbench.test.tsx src/screens/attentionBudget.test.tsx src/app src/screens/reader/voices.test.tsx src/screens/reader/modelActionStates.test.tsx src/screens/practice` | **30 files, 260 passed** |
| `npm run frontend:build` | ok (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` (no schema change; the configuration reference gains 9 leaves: 897 → 906, the prose counts in `Database.md` and `Configuration.md` moved with it) | **0 errors**, schema head 212 |

No migration (help_assists has every workbench column and CHECK value since H0's 210, and 208 admits `workbench_text`), so no head fixture, table role or coordinated-migration change.

Test files run: approach_map_fakes.py daily_plan_fakes.py hint_fakes.py mcp_world.py recap_fixtures.py recurrence_fakes.py split_live_helpers.py test_active_errors_overlay.py test_ai_compare.py test_approach_map_boundaries.py test_approach_map_replay.py test_approach_maps.py test_architecture.py test_blind_grading_contract.py test_chatgpt_plan_landing.py test_chatgpt_plan_provider.py test_chatgpt_plan_sidecar.py test_chatgpt_plan_workspace.py test_cli_help_snapshot.py test_config_refactor.py test_coordinated_migrations.py test_daily_loop_start_minutes.py test_daily_plan_composition.py test_daily_plan_owner_decisions.py test_daily_plan_replay.py test_daily_plan_review_regressions.py test_decider_landing.py test_desktop_rpc_contract.py test_diagnose_review.py test_diagnosis_async_router.py test_diagnosis_card.py test_diagnosis_context.py test_diagnosis_contract.py test_diagnosis_embeddings.py test_diagnosis_history_modes.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_diagnosis_isolation.py test_diagnosis_pipeline.py test_diagnosis_replay.py test_diagnosis_reports.py test_embedding_backfill.py test_embedding_recipe_hash_pins.py test_embedding_route_isolation.py test_field_signal_production_paths.py test_forecast_receipts_landing.py test_forecast_receipts.py test_glm_ocr.py test_grading_support.py test_held_grade_composition.py test_held_grade_evidence.py test_help_assists_schema.py test_hint_authored_reveal_ruling.py test_hint_blind.py test_hint_contracts.py test_hint_discriminating.py test_hint_evidence.py test_hint_feedback_texts.py test_hint_feedback_widening.py test_hint_h2a_review.py test_hint_h2a_review_round2.py test_hint_h2a_review_round3.py test_hint_h2a_review_round4.py test_hint_h2b_fix3.py test_hint_h2b_fix4.py test_hint_h2b_rereview.py test_hint_h2b_review.py test_hint_kill_switch.py test_hint_outcome.py test_hint_replies.py test_hint_report.py test_hint_service.py test_hint_telemetry.py test_hypothesis_reference_contract.py test_judge_routes.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_rereview.py test_learner_text_gaps_review.py test_learner_text_source_widening.py test_library_asks_migration.py test_mcp_c1a_landing.py test_mcp_c1a_narrow.py test_mcp_c1a_review.py test_mcp_tools.py test_method_explicit_landing.py test_mobile_allowlist.py test_mvp011_upgrade.py test_mvp016_upgrade.py test_openai_embedding_client.py test_pfc_unassessed_readers.py test_pfc_unverified_unassessed.py test_pf_sandbox.py test_placement_diagnosis_decides.py test_placement_opening_probes.py test_placement_split_grades.py test_post_attempt_worker.py test_probability_cli.py test_probability_prep.py test_reader_active_reading.py test_reader_cues.py test_reader_find_sources_callers.py test_reader_formative_texts.py test_reader_guidance.py test_reader_intent.py test_reader_recap.py test_reader_recap_review.py test_reader_recap_review_r2.py test_reader_rw1b_review.py test_reader_rw3a_landing.py test_reader_workbench_rw2a.py test_reader_wrap_up.py test_recurrence_groups.py test_recurrence_key.py test_recurrence_live.py test_recurrence_merge_composition.py test_registry_audit.py test_required_method_grading.py test_required_method_round3_review.py test_router_r2a_serving.py test_router_r2bc_landing.py test_route_rules_in_grader.py test_settings_sidecar.py test_sidecar_contract.py test_sidecar_serializer_snapshot.py test_sidecar_trace_and_clarification.py test_sidecar_tutor_qa.py test_stuck_prompt.py test_stuck_prompt_replay.py test_t6_followup_composition.py test_table_roles.py test_tier1_decider.py test_tracked_fixture_databases.py test_ux_phase4_feedback.py test_ux_phase4_landing.py test_workbench_assistance.py test_workbench_check_kinds.py test_workbench_check_map.py test_workbench_check.py test_workbench_chooser.py test_workbench_discriminate.py test_workbench_help_kill_switch.py test_workbench_hint_service.py test_workbench_hints.py test_workbench_in_session_gaps.py test_workbench_report.py test_workbench_step_graph.py test_workbench_text_gaps.py test_workbench_trace.py text_gap_fakes.py workbench_help_fakes.py 

**The manual run (no model):** a backup-API copy of `fixtures/probability` (`learnloop.db.copies.copy_tree_with_databases`) at `fixtures-local/smoke-rw2b/probability`, with `[hints] outcome_placement_enabled = false`, `[hints.maps] build_on_serve = false`, `[learner_text_gaps] enabled = false`, every API key unset, empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `LEARNLOOP_APPROACH_MAP_BUILDS=off`: the DTO carried `workbench.help`; a check answered `codex_refused` (the vault's active provider is Codex) before any call; Help suggested rung 1 by the fallback (no Decider key: `unavailable`); rung 3 served the item's own hint (`authored`, reason `codex_refused`, *from the item*) and rungs 1 and 4 said *Tailored hints are unavailable right now (hints aren't written on Codex). The item's own hints are still here ▸*; the record line read *1 hint (a level-3 hint) → practice with help ◌*; `help_state` restored the hint. **0 receipts and 0 `hint_choice` rows** were written.

## 7. Owner-run commands

```toml
# Checks and the help ladder are on by default (the kill switch and its parts):
#   [workbench]
#   help_enabled = false              # RW2a's workbench exactly as before
#   symbolic_checks_enabled = false   # every verdict the model's reading
#   discriminate_enabled = false      # rung 1 always an ordinary question
#   error_kind_enabled = false        # no error-kind guess shown or traced
#   bridge_enabled = false            # no "compare with the book"
#   max_calls_per_session = 24        # the workbench's own calls per problem
#   max_daily_cost_usd = 1.00         # metered checks a UTC day
#   price_per_million = <USD>         # needed for a metered check route
# The check never runs on Codex. Sign in to the ChatGPT plan once (outside
# every vault), then route the check and the hint writer to it:
#   [ai.providers.chatgpt]
#   type = "chatgpt_plan"
#   model = "<a model `learnloop ai models chatgpt --vault <path> --profile chatgpt` lists>"
#   [ai.routing]
#   workbench_check = "chatgpt"
#   hint_writer = "chatgpt"
# The ladder's suggestion is the Decider (ai.routing.hint_chooser, OPENROUTER_API_KEY);
# without it the Reader's progression suggests (rung 1, then one up per press).
```

```bash
uv run learnloop hints report --surface workbench --vault <path> --json   # the RW2b checkpoint's rows (read-only)
uv run learnloop gaps run --backlog --vault <path>                         # sweeps workbench replies and answers too
```

## 8. Open questions (with the default taken)

1. **The check on Codex** (deviation 5). Default: refused, saying how to route it; the owner's vaults need the ChatGPT-plan sign-in (or a fast OpenRouter profile with `workbench.price_per_million`) before checks run.
2. **Hints' own checkable claims** (§5.3 "hints are verified separately from how they are written") are not checked symbolically yet: it needs a claim field in the shared writer's output, a schema the adaptive-hints spec owns. Default: deferred to H4 or a small H-successor; the writer's contracts and leak control still hold.
3. **"A short problem instead"** (§5.2, optional on the sources spec; `find_practice` already has `intent = "discriminate"`). Default: not built here; it opens a second session with `entry = discriminating_problem` and `parent_session_id`, both already in RW2a's schema.
4. **The same steps checked again count nothing** (deviation 6). Default: as built.
5. **An open problem's help is held by an answer-box submit, and again by the problem's own later submit** (two attempts, each assisted by it), RW2a's rule for the book. Default: as built.
6. **A refused submit's stamp** makes a hint still pending at that moment undeliverable (deviation 3). Default: accepted; the learner asks again.
7. **The rail's tabs in the header's `⋯`** (RW2a open question 5). Default: not yet; the ladder took the room.
8. **The suggestion's ledger row names a reserved assist id** (deviation 9). Default: as built; H5 links a take to its suggestion by the `seed` the take's row keeps (the ledger row's seed).
9. **Rung 1 off the questionable step** (deviation 8). Default: an approach question.

## 9. Friction notes for RW2c, RW2d, H4 and H5

**RW2c (what helps this learner).** `help_outcomes` can read the workbench's rows directly: checks (`step_verdicts_json` with `map_node_id`/`route_id` per valid step, `first_questionable_step_id`, `error_kind_guess`, `alternatives_json`), hints (`about_step_id`, `continue_from_step_id`, `offered_level`, `level_source`), bridges (`cited_span_ids_json`, `retrieval_manifest_json`, `placement_json.hint_assist_id`). `hints/report_workbench.py`'s "recovery after a check" is the immediate-continuation measure (next check's first questionable step moved, gone or the same, with or without help between). The bridge takes T6's first verified span: RW2c's logged passage draw goes in `workbench/bridge.py` (the row's `propensity`/`seed` are free). "Compare methods" can reuse `workbench/check.py`'s `CheckRoute` (route `workbench_check`, its caps, never Codex).

**RW2d (workbench signals).** Mid-work stuck steps are queued as `workbench_text` by version (`workbench/ladder.py:stuck_texts`); "help before work" is a hint row whose `step_snapshot_json` is empty (or `work_chars = 0`). Both are read without the workbench's modules by SQL (the contract forbids `learnloop.workbench` in the field).

**H4 (guided redo and the tutor).** `service.SURFACES` is the one place to add a surface; `hints/workbench.py` is the pattern for a surface's context, options, rules and row columns. A surface whose submit can race its own deliveries can reuse the stamp-then-fold rule (`deliver_workbench`). A taken level 1-2 is never downgraded (`downgrade_allowed`). The writer's `build_prompt(workbench=…)` block is per surface.

**H5 (off-policy report).** On workbench rows: the suggested rung's take logs the joint propensity (`level_source = offered`, `chooser = decider`); another rung the conditional (`learner_pick`, `chooser = decider`); a one-option rung `learner_pick` with 1; the fallback `fallback` with 1; `argmax` 1; the book's way and a smaller step `learner_pick` with none. The suggestion itself is a `hint_choice` ledger row (vectors, seed, draw) whose `left_id` names no row; the take that followed keeps `offered_level` and the drawn option.

## 10. Fix round 1 (Codex review)

`docs/reviews/reader-rw2b-h3-codex-review.md`: 15 findings (3 High), all fixed in `7ce123267`. That round supersedes
deviation 5 and open question 1 (the check now runs on Codex, `estimated_only`, F12) and the first item of deviation
13, which is open question 2 (a hint's own checkable claims are now verified before it is shown, F14).

**Fix round 3 (orchestrator ruling on F3).** The symbolic check (`learnloop/workbench/symbolic.py`, described above) no longer checks the model's declared
expressions. It parses the learner's own LaTeX step (sympy, lark backend) and checks that relation. The
declaration only picks the kind, and inequality and boundary are no longer checked. See the review file's "Fix
round 3".

**Fix round 9 (orchestrator decision).** `workbench.symbolic_checks_enabled` now defaults to **false**. RW2b ships
with every symbolic verdict labelled "model's reading, not checked", and the sandbox is never invoked. The checker
stays behind the switch until a renderer-equivalent (MathML) checker lands. The review file's "Fix round 9" records
the limits and the test corpus for that stage.

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw2b-onto-main`, cut from main at `29a49b5e6` (the AD1
landing, migration head 213). The stage tip is `1754d0d3d`, unchanged; its base was `7d4c5f4ce` (the H2b landing),
so AD1 came in with the merge. The orchestrator's final whole-stage verify (Codex job `20261019-002911-DDMlXt`) is
clean: no High, one Medium accepted as non-blocking (below). Main was neither fast-forwarded nor pushed here.

**Commits:**
- `892078de4`: a `--no-ff` merge of `reader/rw2b` onto `29a49b5e6`, with the conflicts composed and every defaults
  snapshot from `mvp-0.9` to `mvp-0.27` recomputed.
- `9db0938d1`: the references regenerated on the merged tree.
- `89878cfe9`: one gate fix (the copy-site audit, below).
- This record.

### Merge

- **Code conflicts** (seven files). Every one was resolved by keeping both sides:
  - `ai/routing.py`: the AD routes (`ad_forecast_llm`, `ad_forecast_decider`, `ad_feature_audit`) and their task
    map entries, next to `workbench_check`;
  - `ai/disclosures.py`, `config/schema.py` (`AIRoutingConfig`): the three AD routes next to `workbench_check`;
  - `tests/test_judge_routes.py`: the pinned judge set now holds both stages' routes;
  - `tests/conftest.py`: `LEARNLOOP_AD_MODELS=off` next to `LEARNLOOP_WORKBENCH_MODELS=off`;
  - `apps/learnloop-tauri/src/app/algoConfig.ts`: AD1's `ratingTap` and `firstHintProgress` next to RW2b's
    `workbenchHelp` (type, defaults and `setAlgoConfig`);
  - `config/template.py`: both stages' history comments are kept. A per-version line for RW2b was added to
    `mvp-0.10`..`mvp-0.27`, and all 19 entries from `mvp-0.9` to `mvp-0.27` were recomputed from the composed
    defaults (`defaults_fingerprint_for_version`, after clearing the config `.pyc`). The entries before `mvp-0.9`
    were already equal.
- **Merged without conflict, checked by hand.** Both sides changed `handlers/practice.py`, `api/dto.ts`,
  `api/client.ts`, `PracticeScreen.tsx`, `attempts/attempts.py`, `params/parameter_registry.py`,
  `learnloop_sidecar/context.py`, `tests/test_architecture.py` and `pyproject.toml`. Both stages' fields and call
  sites survive:
  - `SubmitAttemptInput` and `DontKnowInput` carry AD1's `difficulty_rating` and `first_hint_progress` and RW2b's
    `authored_hints` and `book_counted`;
  - the queued resubmit passes all four;
  - the draft envelope keeps AD1's `first_hint_progress` and `hint_seen`;
  - the two submit payloads in `PracticeScreen.tsx` send `authoredHints`/`bookCounted` and the tap and marker.
- **Generated references** (395 notes under `Reference/`, all `source_commit` lines): main's side was taken, then
  the references were regenerated.
- **`uv.lock`**: `uv lock` on the merged `pyproject.toml` resolved 179 packages with no change beyond the stage's
  `lark 1.3.1`.
- **No migration**, so no head fixture, table role or coordinated-migration change. `migration_head_213` is main's.
  `src-tauri` changed (17 lines, the eight passthroughs), so `cargo check` ran.

### Regenerated

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 213, 333
  table notes, 397 notes changed. The configuration catalog went from 908 to **917** leaves (RW2b's 9 on AD1's 908).
  The two hand-written prose counts (`Reference/Configuration/Configuration.md`, `Reference/Database/Database.md`)
  were moved to 917; the validator failed on them until then.
- **Defaults snapshots.** Recomputed in the merge (above). Afterwards **0 mismatches** over every
  `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry, and none of the old hashes is named anywhere in `src/` or `tests/`.
- **CLI help snapshot.** `python tests/test_cli_help_snapshot.py --write`: no change.
- **RPC pins and the parameter registry.** The serializer snapshot, desktop RPC contract, mobile allowlist (the
  eight RW2b RPCs and the new submit fields desktop-only), CLI help, registry audit, `test_grading_cli.py`,
  `test_p0_cutover_mvp08.py`, `test_config_refactor.py` and `test_judge_routes.py`: **315 passed**, no file
  rewritten.
- **`validate_vault.py`**: passes (1,129 notes; 1,127 of 1,127 reachable).
- **Known failures, from before this stage, not fixed:**
  - `desktop_validate.py` stops on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts`, as
    at the AD1 landing;
  - `module_validate.py` reports **900** issues, up from 879 at the AD1 landing. The rise is RW2b's new modules
    without module notes (`learnloop/workbench/*`, `hints/workbench.py`, `hints/report_workbench.py`,
    `symbolic_view.py`).

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`, and every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`. The AD2+AD3 worktree and its
processes were not touched. Every test uses fakes. **This is the first full run over the stage's code**: every
stage step and the 15 fix rounds ran targeted tests only (owner rule 2026-10-17).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (`lark 1.3.1` installed by the sync) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` on `9db0938d1` | **14,032 passed, 2 xfailed, 1 failed** (21 min 38 s; `fixtures-local/rw2b-landing-fullsuite.log`). The AD1 landing ran 13,738 |
| the one failure | `test_sqlite_file_copies.py::test_every_file_copy_site_is_an_audited_sqlite_copier`: real, from the stage, fixed in `89878cfe9` (below); the file then passes |
| `pytest -m durability` on `89878cfe9` | **113 passed**, 13,922 deselected (3 min 58 s; `fixtures-local/rw2b-landing-durability.log`) |
| `npm install`, `npm run typecheck` | up to date; clean |
| `npm test` (the whole vitest run) | **138 files, 1,098 tests passed** on the first run. The `FeedbackScreen` flake did not fire |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok |
| thread, lock and timing tests | all passed on the first run, so none was rerun. The `"8841"` MCP flake did not fire |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run, apart from this record; no `-wal` beside a fixture |

**The gate fix (`89878cfe9`).** Fix rounds 10 and 11 added `tests/test_reader_rw2b_fix10.py` and `_fix11.py`. Each
`shutil.copy`s a Python helper script (`rw2b_fix10_base_sequence.py`, `rw2b_fix11_base_sequence.py`) into an
archived base-code tree. Neither copies a database, but the copy-site audit fails on any unlisted copy call, and no
targeted run included it. Both sites are now in `AUDITED_COPIERS` with that reason. The test failed first (in the
full run) and passes after the fix. No code changed.

### Parity (backup-API copies; no model call completed)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (probability with its
  `.learnloop/state.sqlite`) were copied once with `copy_tree_with_databases` from the main checkout into
  `fixtures-local/landing-rw2b/orig/`. Every other copy came from `orig/`, or from its upgraded copy `u27/`,
  through the same helper. `arxiv_v2` was not opened. Both vaults start at schema 165, label `mvp-0.8`, with 0
  `model_call_receipts`.
- **Code.** Main's code is `git archive 29a49b5e6` and the merge's is `git archive 9db0938d1` (`src`, `migrations`,
  `pyproject.toml`; `src` is the same at the tip), each first on `sys.path`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG`. `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` were empty directories and still are. No key
  or provider variable was set.
- **Model routes, set before anything ran.** H2b's `neutralize3.py`, run under each code (54 routes on main, 55 on
  the merge), sent every field of that code's `AIRoutingConfig` to `127.0.0.1:9`:
  - chat routes to `blackhole` (`openai_chat` at `http://127.0.0.1:9/v1`): `hint_writer`, `approach_map`,
    `hint_outcome`, `workbench_check`, `ad_forecast_llm`, `ad_feature_audit` and the rest;
  - decider-only routes to `blackhole_decider`: `hint_chooser`, `ad_forecast_decider`, `tier1_decider` (the
    Decider) and the rest;
  - `ai.active_provider` to `blackhole`, the fallback cleared;
  - `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense` and `[embedding]` off;
  - `[learner_text_gaps] enabled = false`;
  - `[hints.maps] build_on_serve = false` and `[hints] outcome_placement_enabled = false` on every copy.
  - A copy upgraded by main's code got `workbench_check = "blackhole"` before the merge's code opened it.
  - A resolver check over every `AITask` (57 on main, 58 on the merge) found nothing outside those two profiles
    except `embedding` (disabled, keyless).
- **The profiles' key variable** (`LL_LANDING_NO_KEY`) was unset, except in the two (e) runs that say so.

**(a) Schema and rows, and (b) nothing served changes**

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 213 (48) / the same | the same |
| schema, main@213 vs merge@213 | **identical**: 1,414 objects each, none on one side only, no SQL differs | **identical** (1,413) |
| rows of every table (338), all columns | **identical** (16,539 rows); `schema_migrations` differs only in `applied_at` (the open's time) | **identical** (7,637 rows; the same) |
| `foreign_key_check` / `integrity_check`, both sides | 0 / ok | 0 / ok |
| `rebuild --shadow --json` | **0 differences** after normalisation (raw: the marker id and database hashes); facet 0, mastery 2, schedule 8; live database unchanged on both | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json` | **0 differences** (raw: the copy paths); 57 issues, 1 error | **0 differences**; 101 issues, 48 errors |
| **(b)** at `mvp-0.8`: certification, recipe gaps and curves; the Today queue at a frozen clock (2026-10-19 09:00 UTC; no session, a session, greedy); the daily plan | **byte-identical** (39 facets, 84 points; queue 41; the plan is off below `mvp-0.14`) | **byte-identical** (29 facets; queue 67) |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice), then opened by each code | certification and curves **byte-identical** (82 points, 7 corrections); Today queue **byte-identical** (43) | **byte-identical** (queue 67) |
| the daily plan at `mvp-0.27` (the sidecar's handlers in process, frozen clock: read, serve, serve again, read; the plan tables, `plan_presentations`, the `plan_block` decisions) | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash in `detail_json`, which hash a card carrying the plan's ULID. **A second run of main's code differs from the first in exactly these three**, and the merge differs in nothing else | the same |

**(c) Practice through the real sidecar** (stdio), on copies of probability at `mvp-0.27` (`u27/`), so the daily
plan serves. The sequence:
- `initialize`, `get_config`, `set_grading_provider manual`, `start_session`;
- one daily-plan serve (`get_daily_plan`, `next_plan_item` with `serve` true: `pi_three_independent_birthd`), then
  a 12 s wait for AD's background jobs;
- on `pi_prob_derive_complement`: `get_practice_item`, `get_probe_contract`, `practice.record_hint_reveal`
  (authored hint 0), `save_practice_draft`, `submit_attempt` with self-grade, the `submissionId` and
  `difficultyRating: "hard"`, then `acknowledge_practice_submission`;
- `submit_dont_know` on `pi_incl_derive_intersections` (another LO), acknowledged;
- a hint-free workbench `open`, `get` and `submit` on `pi_story_binomial_translation` (a third LO);
- `get_session`, `shutdown`.

The runs: (i) main (`ci`, plus `ci2`, main again as the baseline); (ii) the merge with
`[workbench] help_enabled = false` (`cii`); (iii) the merge at the defaults (`ciii`).

| Check | Result |
|---|---|
| every response (21 calls), (i) vs (ii) vs (iii) | **identical** after AD1's normalisation (ULIDs, timestamps, the copy path, `initialize`'s schema-head fields) **except two keys**. First, `initialize`'s method list gains the eight RPCs in (ii) and (iii): `workbench.check`, `.suggest_help`, `.request_help`, `.help_job`, `.cancel_help`, `.answer_discriminating`, `.set_help_style`, `.help_state`. Second, in (iii) only, `get_config` carries `workbench.help: {enabled: true, bridge: true, symbolic: false}`. In (ii), `get_config` is raw-identical to main's |
| the database delta | (ii) and (iii) differ from (i) only in tables where `ci2` (main again) also differs from `ci`: wall-clock floats in `attempt_debug_payloads`, `scheduler_explanations` and `scheduler_slate_candidates`; the router card hash in `attention_block_events`; and AD's background rows (`judgment_ledger` uuids, `item_forecast_payloads` request hashes). No merge-only table or column was written |
| the attempts, all four runs | **identical** evidence fields: the `open_text` attempt has `hints_used` 1, `primed` 0, correctness 1.0, `difficulty_rating` **hard**, `first_hint_progress` NULL (not sent); the `dont_know` is recorded as stuck (`declared_stuck` 1, scored 0), `hints_used` 0; the workbench attempt (`desktop_practice_workbench`) has `hints_used` 0, `primed` 0. The activity classes are the same, there are 0 `reveal_events` rows, and one `help_assists` row (the client-counted authored reveal, level 3, attached to the first attempt) |

**(d) Counting** (merge at the defaults vs main, on `pi_prob_derive_complement`)

| Run | Sequence | Attempt |
|---|---|---|
| `d1` main / merge | an authored reveal on the answer box, the draft (`hintsUsed` 1), *Work in steps* (`workbench.open` with `carriedHints` 1; the record line reads *1 hint (1 shown on the answer box) → practice with help ◌*), no help taken, `workbench.submit` | **identical**: `desktop_practice_workbench`, `hints_used` **1**, `primed` 0, `declared_stuck` 1, scored 0, assisted, not certifying |
| `d2` main / merge | the reveal, then an old-client `submit_attempt` (`hintsUsed` 1, no `authoredHints` or `bookCounted`) | **identical**: `desktop_practice`, `hints_used` **1**, `primed` 0, correctness 1.0; the reveal's row attached to it |
| `d3` merge | the same with the new client's `authoredHints: 1, bookCounted: false` | the same as `d2` |

**(e) Check my work at the default** (on `pi_story_binomial_translation`, one step, `workbench.check` once, then
`workbench.help_job` until done):
- **Key unset, and the dummy key set** (`emerge`, `ekmerge`). The request started as a job (`pending`) and ended
  `unavailable`, reason `unpriced`: *"A metered check route needs workbench.price_per_million."* It was refused
  before sending, with no receipt and no `help_assists` row.
- **The dummy key and `workbench.price_per_million = 1.0`** (`epmerge`, so the request reaches the loopback). The
  job ended `unavailable`, reason `check_failed`: *"Couldn't check your steps just now. They're saved — try again
  ↵"*. It wrote 6 `model_call_receipts` rows (3 requests, each a parent and a `chat_request` child), all
  **`failed`**, and no `help_assists` row.
- In all three runs, `help_state` returned `check: null` and no hints, and the record line read *your own attempt*.
  No workbench response contains "checked", `✓` or `≠`.

**(f) Help switched off** (`[workbench] help_enabled = false`). All eight RPCs refused **`help_disabled`**:
`workbench.check`, `.suggest_help`, `.request_help` (rung 1), `.help_job`, `.cancel_help`,
`.answer_discriminating`, `.set_help_style` and `.help_state`. The workbench itself still opened, saved a step and
read its record.

**`model_call_receipts` across all 44 databases** under `landing-rw2b/` (copies and their base backups): 6 rows,
**all `failed`**, all in (e)'s `epmerge` at `127.0.0.1:9`. There are **0** `completed` rows.

### New findings

- **Fixed: a gate gap from targeted runs.** The copy-site audit was outside every targeted run, so fix rounds 10 and
  11's helper copies reached the landing unaudited (`89878cfe9`).
- **Behaviour to know, not a defect.** A metered `workbench_check` route without `workbench.price_per_million` is
  refused before sending (`unpriced`). With a price set and the route down, one press of *Check my work* made 3
  requests before answering *Couldn't check your steps just now*. Nothing is counted or shown either way.

### For the owner

- **No migration and no `--to` command.** Nothing served changes (parity (a)-(c)).
- **New dependency: `lark` 1.3.1** (the parser behind the symbolic checker). `uv sync` pulls it in.
- **What appears in the workbench** (Reader *Work in steps*, and the practice screen's *Work in steps*):
  - *check my work · counts as a hint · ctrl+k*: a verdict column beside the steps, with the first questionable
    step's quoted reason and the check's guess, labelled *(model's guess)*;
  - *help · ctrl+h*: the help ladder, five rungs at once with a ▸ *suggested* one. The hints sit under the step
    they are about, with *this doesn't connect…* and its four shortcuts, *a smaller step toward this goal*, *show
    me the book's way*, and, in the Reader, a line that finds the matching step in the book;
  - the header's help style for this problem;
  - the record line and footer naming every check and hint;
  - an optional answer-confidence row.

  A shown check counts as one hint, as does each level 1-3 hint; a level 4-5 hint primes the attempt.
- **Check my work runs on the active provider, which is Codex in the owner's vaults.** That is allowed, but slow
  (about 30 s). For speed, route `ai.routing.workbench_check` to the ChatGPT plan or a fast OpenRouter profile. A
  metered profile also needs `[workbench] price_per_million`, or every check is refused before sending.
- **Hints still need the ChatGPT sign-in or a priced OpenRouter route for `hint_writer`.** Without it, rung 3 serves
  the item's own hints, and the other rungs say tailored hints are unavailable.
- **Symbolic checks are off by default.** Every verdict reads *model's reading, not checked*, and the sandbox never
  runs. The follow-up stage is **renderer-equivalent symbolic checks** (codex review, "Fix round 9"). To turn the
  current checker on, set `[workbench] symbolic_checks_enabled = true`, knowing the limits recorded there.
- **Turning help off:** `[workbench] help_enabled = false`. RW2a's workbench then returns exactly, and the eight RPCs
  refuse (parity (c)(ii) and (f)).
- **Open questions (defaults taken), from §8 and the codex review:**
  - 1: the check on Codex. Superseded in fix round 1: it is allowed (`estimated_only`);
  - 2: a hint's checkable claims. Superseded in fix round 1: they are verified before showing (F14), and with
    symbolic checks off they are the model's reading;
  - 3: *a short problem instead*: not built;
  - 4: the same steps checked again count nothing;
  - 5: an open problem's help is held by an answer-box submit and again by the problem's own submit. Superseded in
    fix round 13 for RW2b's server assists, which follow H2b's R1 window, so whichever attempt commits first takes
    them;
  - 6: a refused submit's stamp makes a hint still pending then undeliverable (the learner asks again);
  - 7: the rail's tabs in the header's `⋯`: not yet;
  - 8: the suggestion's ledger row names a reserved assist id;
  - 9: rung 1 off the questionable step is an approach question;
  - binding (codex review): textual and strict, so it yields fewer checked verdicts and never a wrong one. This is
    moot at the default (symbolic off).
- **Open items:**
  - the last verify's accepted **Medium** (job `20261019-002911-DDMlXt`): an in-flight toggle of
    `workbench.symbolic_checks_enabled` during diagnosis provenance and admission;
  - the follow-up stage **renderer-equivalent symbolic checks** (MathML; the corpus is in the codex review's "Fix
    round 9");
  - **RW2a's pre-existing undercount.** When there is no RW2b assist, a book counted on another surface plus an
    authored reveal is undercounted. The count there is RW2a's base path, byte-identical to `7d4c5f4ce` by design.
    This is a follow-up;
  - `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (900 issues), both from before this stage.
