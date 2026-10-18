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
