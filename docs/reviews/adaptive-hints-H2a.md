# Adaptive hints H2a: the hint service core and `practice.request_hint` (stage `hints-h2a`)

Branch `hints/h2a` (worktree `learnanything-merge4`), base `main` at
`59d300e63` (H1 landed; migration head 211). Spec:
`docs/specs/spec_adaptive_hints_v1.md` §2, §3, §4.1, §4.2, §4.4-§4.7, §4.8
(label wording only), §5, §6.2, §7.1-§7.4, §9, §10 (H2 row, §10.1), §11
(G-H1..G-H8, G-H10..G-H16), §12 (D3-D5, D8-D10, D15-D17); friction notes of
`docs/reviews/adaptive-hints-H0.md` §9 and `docs/reviews/adaptive-hints-H1.md` §8.

The orchestrator split the spec's H2 (size L): **H2a** is the service and its
RPCs with no UI; **H2b** adds the practice-screen panel, outcome placement,
the per-kind report rows and the `hint_feedback` adapter with its widening
migration.

## 0. Plan (written before the code)

**Scope.** Backend only: no `apps/` change, no `hint_outcome`, no report rows
beyond H0/H1's, no learner-text adapter and no `source_kind` widening, no
workbench, guided redo or tutor change, no migration (H0's `help_assists`
already has every column), no evidence, grading, scheduling or replay rule
change beyond §5's existing-meaning fold.

**Package `learnloop.hints`** (still under `hints-never-write-evidence`):
- `kinds.py`: the twelve kinds with their levels (§4.2), the plain-words
  labels and the *worked help ◌* mark (§4.8), the four shortcuts, the request
  values, and the fallback order per level.
- `state.py`: `HintState`, assembled from local reads only (§4.5's list): LO
  placement intent and mastery, the live predictor's P(success) and variance,
  facet evidence (unaided credit vs assisted-only mass), prior attempts on the
  item and its LO, open rivals, this attempt's earlier hints (kinds, levels,
  feedback), route preference (from the map's learner routes), the work
  (the checkpoint's draft when the request carries none), time since shown,
  help style. Pure reads from `learnloop.placement` are named
  `ignore_imports` lines with their reasons (H0 friction note 3).
- `options.py`: the (kind, level) options and their preconditions:
  `discriminating` only with two or more open rivals and not after one was
  answered at this placement; `waypoint` / `subgoal_plan` only with a map;
  `worked_parallel` only with a usable source example (the map's `source:`
  seeds or another instance in the family); `localize` / `error_specific`
  only with work; a Hint press serves levels 1-3 only and levels 4-5 only for
  a taken level (D17); shortcut and pick exclusions (§4.2).
- `chooser.py`: the Decider task `hint_chooser` (added to `DECIDER_TASKS`:
  never a chat fallback, never `LEARNLOOP_AI_PROVIDER`), one request with two
  questions (`kind_level` choice; `horizon` score only when a waypoint is
  offered); sampling from the Decider's probabilities with a seeded RNG
  (`random.Random(seed)`, seed logged), propensity = the probability of what
  was drawn (joint kind_level x horizon; conditional on a taken level, asked
  over that level's options alone; 1 where one option); `choice_policy =
  "argmax"` logs 1; the 3 s time box (`chooser_timeout_seconds`) passed to
  the client and checked on the wall clock; fallback (§4.5, practice surface):
  authored hints in order while they last, then `next_step`; after a reply,
  the next kind of a fixed list that satisfies the shortcut, at the same
  level; propensity 1, `chooser = 'fallback'`. `book_way` / `smaller_step`
  are `learner_pick` with no propensity. One `judgment_ledger` row (task
  `hint_choice`, judge `decider`) per Decider request; receipts labelled with
  `judge`, `question_set_version` and `state_hash`.
- `writer.py`: route `hint_writer`, one structured chat call through
  `PaidCalls` (receipts, checkpoints, `estimated_only` on the ChatGPT plan);
  the placement (§4.4) is part of its output; the seven shared rules and every
  kind contract (§4.2, §4.6) are checked in code; a failure is re-asked once
  naming it, then downgraded to a level-3 `next_step` from the last valid
  checkpoint without its unverified claims (one more call); leak control on
  every hint at level <= 3: `answer_leaks_expected` plus H1's `gives_away`
  (short numeric answers) plus the map's leak-node states (H1 friction notes 4
  and 7: binding here, whatever the map's marks say); a leaking hint is
  re-asked once, then withheld with the spec's wording. **D9:** the writer
  never resolves to a Codex profile; when routing would give Codex (today's
  active provider), the service falls back to authored hints and says why.
- `discriminating.py`: rivals from the diagnoser overlay (open hypotheses and
  durable misconceptions on the item's LO), `unresolved_cause_factors`'
  candidate causes of the item's latest diagnosed attempt, and this
  attempt's named gaps (`learner_text_gaps` of kind misconception on the item
  since its last attempt); the writer proposes candidates with each rival's
  predicted answer; each is compiled as a `CompiledInstrument` (one one-hot
  row per rival over the distinct predicted answers) and ranked by the
  existing `instrument_expected_information_gain` under uniform weights
  (labelled `uniform`; an `ignore_imports` line for the pure function); zero
  EIG dropped; no positive EIG -> §4.2's downgrade with its why line.
- `service.py`: `HintRequestV1` / `HintResultV1` (typed, versioned), the spend
  envelope, the decision flow, and the `help_assists` row (written prepared,
  `shown = 0`, and marked shown when the result is delivered; see the RPCs).

**Spend.** `hints.max_daily_cost_usd` ($1.00) as RW4a/H1's
`SharedDailyEnvelope` under its own envelope name, owner kinds
`hint_chooser` and `hint_writer`, at `hints.price_per_million` (the shared
`[hints]` price, H1 friction note 5); a metered writer with no price is
refused before sending; the ChatGPT plan is `estimated_only`; a capped day
falls back to authored hints and says so.

**Sidecar RPCs** (new module `learnloop_sidecar/handlers/hints.py`, desktop
only, pinned in `tests/test_mobile_allowlist.py`; no Tauri passthrough: no
frontend calls them until H2b):
- `practice.request_hint`: the sidecar is serial and a writer call takes
  seconds, so (as RW4a's library jobs, Codex review F6 there) the request
  answers at once with a job; immediate outcomes (adaptive off, a diagnostic
  block, a refusal) answer `done` with no job thread.
- `practice.hint_job`: reads the job at once. **The read that returns the
  done result delivers it:** the prepared row becomes `shown = 1` with
  `shown_at`, and a key overlap writes the `reveal_events` `tutor_answer` row
  (basis `hint:<kind>:L<level>`), in the sidecar (the reveal writer lives in
  `learnloop.attempts`). A crash before the read leaves `shown = 0`.
- `practice.cancel_hint`: before delivery, the row stays `shown = 0` and
  counts nothing (G-H3: "an authored fallback cancels the pending adaptive
  request").
- `practice.answer_discriminating` (chosen over a request field: an answer is
  fire-and-forget-safe and need not ask for a new hint): one `help_assists`
  row, `assist_kind = 'discriminate_answer'`, `counted_by` NULL; no posterior,
  no probe observation; the next hint's state carries it.
- Refused, with no model call, during a diagnostic block (G-H14).

**The fold** (sidecar submit path, not `learnloop.hints`): at
`submit_attempt` and `submit_dont_know`, the shown server rows of this
submission (still unattached) at levels 1-3 add to `hints_used` beside the
tutor-question fold, clamped by `max_useful_hints`; any shown level 4-5 sets
`primed`. Authored reveals stay client-counted (`counted_by = 'client'`); an
authored hint the service itself serves is a server row the client does not
count (H0 friction note 2).

**Config** `[hints]`: `adaptive_enabled` (default true, the spec's live
default behind its kill switch), `chooser_enabled`, `choice_policy`
(`sample` | `argmax`), `chooser_timeout_seconds` (3), `help_style`
(`let_me_struggle` | `balanced` | `guide_me`, read here; the editor is H2b),
`max_daily_cost_usd` (1.00); routes `ai.routing.hint_chooser` (decider) and
`ai.routing.hint_writer` (chat). Every new numeric leaf classified in
`params/parameter_registry.py`; every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry
recomputed with the "no scoring, scheduling, projection or serving change"
note. Adaptive hints need `hints.telemetry_enabled` too (the rows are the
count); with either off `practice.request_hint` answers `disabled` and the
practice RPCs are byte-identical to the base (G-H1).

**Tests** (fakes only): `test_hint_service.py`, `test_hint_contracts.py`,
`test_hint_replies.py`, `test_hint_discriminating.py`, `test_hint_evidence.py`,
`test_hint_blind.py`, `test_hint_kill_switch.py`, with helpers in
`tests/hint_fakes.py`; G-H10 extended in `test_approach_map_replay.py`; the
mobile allowlist pin; the judge-route disclosures; the defaults snapshot.

## 1. What was built

### 1.1 The service (`learnloop.hints`, still under `hints-never-write-evidence`)

- `kinds.py`: §4.2's twelve kinds with their levels, the Reader's plain-word
  labels (§4.8) and the level-3 label of `discriminating`, the horizon rubric
  and its labels, *worked help ◌*, the two worked-help picks with their
  consequence stated before they are taken, the four shortcuts, the four
  request values, the fallback order per level, the withheld wording and the
  why lines of §4.2's no-positive-EIG downgrade, and the wording lint's three
  phrases.
- `state.py`: `HintState`, assembled from local reads only; each read is
  independent and best-effort (a failed one is named in `unread`, never
  guessed). The Decider's slice (`decider_state`) is typed and short and never
  carries the draft's text, the reference answer or the map's states (§7.4).
- `options.py`: the options and their preconditions, and every reply's and
  pick's constraint (the module docstring has the list); excluded options are
  recorded on the row with their reason.
- `chooser.py`: one Decider request with `kind_level` (choice) and `horizon`
  (score, asked only when a waypoint is offered and a horizon is allowed);
  `random.Random` seeded from a logged seed; the propensity is the drawn
  option's probability (times the horizon's, renormalized over the allowed
  horizons, when a waypoint is drawn); a taken level asks over that level's
  options alone (conditional); one option left: no request, propensity 1,
  `chooser = 'learner_pick'`; `argmax` logs 1; the 3 s time box is passed to
  the client and checked on the wall clock; a failure, time-out, refusal or
  unavailable Decider falls back (§4.5); one `hint_choice` ledger row per
  request (judge `decider`, verdict the drawn option or the failure, the full
  vectors, seed, policy, propensity and state hash in its rationale); receipts
  labelled `judge = decider`, `question_set_version = hint-chooser-qs-v1` and
  the state hash (`decider_judgments.ask_decider` gained optional
  `question_set_version` and `timeout_seconds`, defaulting to today's).
- `writer.py`: route `hint_writer` through `PaidCalls` (receipts under owner
  kind `hint_writer`, labelled `judge = llm`, `question_set_version =
  hint_writer.v1` and the state hash); `HintWriterOutputV1` (strict: every
  field required) carries the placement, the hint, its route and target, a
  strategy slug and every kind's contract fields; D9's Codex refusal and the
  other reasons a hint cannot be written (`unrouted`, `unpriced`, `capped`,
  `models_off`) are checked **before** the chooser is asked, so a refused
  writer spends nothing.
- `contracts.py`: the seven shared rules and every kind's contract in code,
  and leak control on every level-1-3 text (`answer_leaks_expected`, H1's
  `gives_away` for short and equivalent answers, and the map's leak-node
  expressions less what the question itself states).
- `discriminating.py`: the rivals, the candidates compiled as
  `CompiledInstrument`s and ranked by `instrument_expected_information_gain`
  under uniform weights (labelled `uniform`; reliability 1, since the answer
  is compared with the predictions by code), zero EIG dropped, and the check
  that a question states no rival.
- `service.py`: `HintRequestV1` / `HintResultV1` (versioned), the flow (§0),
  the daily envelope `hints.max_daily_cost_usd` (owner kinds `hint_chooser`
  and `hint_writer`, at `hints.price_per_million`), the prepared row, the
  `hint_fit` verdict of a reply, `deliver`, `reveal_amount`/`reveal_basis`,
  and `record_discriminate_answer`.

### 1.2 The decision flow, as built

1. Disabled (`adaptive_enabled` or `telemetry_enabled` off): `disabled`, no
   read beyond the config, no row, no call.
2. Validated: a reply or pick names a shown hint of this submission;
   `smaller_step` answers a waypoint; a taken level is 4 or 5 and its own
   request; a shortcut belongs to a reply.
3. A reply appends its `learner_card` verdict `different` on `hint_fit` first.
4. State, options, the writer's route check.
5. The choice: the learner's pick; one option; the Decider; or the fallback.
6. Authored (fallback or the writer's verbatim pick): the item's text, leak
   checked; otherwise the writer: ask, check, re-ask once naming the failures
   and leaks, then the level-3 `next_step` downgrade (one more call). A leak
   on the re-ask or the downgrade withholds; a downgrade that fails is
   `unavailable` (`contract_failed`).
7. The row is written prepared; the result says what was served and why.

### 1.3 Sidecar (`learnloop_sidecar/handlers/hints.py`)

`practice.request_hint`, `practice.hint_job`, `practice.cancel_hint`,
`practice.answer_discriminating` (desktop only; pinned). The job registry
lives on the context (in memory, the last 32 jobs), binds each job to its
vault (a read after a vault switch is `not_found` and delivers nothing), and
runs inline under `ctx.hints_inline` (tests). Test seams: `ctx.hint_writer_client`,
`ctx.hint_chooser_client`, `ctx.hint_seed`. No Tauri passthrough (no frontend
calls them until H2b).

### 1.4 The fold (`learnloop_sidecar/handlers/practice.py`)

`_server_hint_fold` reads `help_assists.server_fold`: shown, server-counted,
still-unattached hint rows of the session and item under the submission's
key (a client with no key: the session's rows since the item's last
attempt). `submit_attempt`: `hints_used = client + tutor questions + server
(levels 1-3)`, clamped by `max_useful_hints`; `primed |= any level 4-5`.
`submit_dont_know`: the server rows join the total (clamped when they do;
the tutor-question fold's absence there is left as it was, §14 Q5); `primed`
for worked help. Authored reveals stay the client's count. H0's attach binds
the server rows to the attempt with the authored ones.

### 1.5 Config, routes, registry, snapshots, boundaries

- `[hints]` `adaptive_enabled = true`, `chooser_enabled = true`,
  `choice_policy = "sample"`, `chooser_timeout_seconds = 3.0`, `help_style =
  "balanced"`, `max_daily_cost_usd = 1.00` (modelled defaults, not in the
  decision-only template); routes `ai.routing.hint_chooser` (decider-only,
  in `DECIDER_TASKS`) and `ai.routing.hint_writer` (`AITask`,
  `ROUTE_FOR_OPERATION`, `AIRoutingConfig`); disclosure rows for both
  (`get_settings` lists them).
- `params/parameter_registry.py`: `hints.max_daily_cost_usd` and
  `hints.chooser_timeout_seconds` (structural, operational).
- Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry (19) recomputed with the "no
  scoring, scheduling, projection or serving change" note.
- `pyproject.toml`: three `ignore_imports` lines with their reasons
  (`hints.state -> placement.state`, `hints.state -> placement.predictor`,
  `hints.discriminating -> diagnosis.probe_families`).
  `graders-never-read-approach-maps` holds unchanged.
- `tests/conftest.py`: `LEARNLOOP_HINT_MODELS=off` (no hint route resolves a
  real client unless a test injects a fake).

## 2. Deviations (each recorded, none a rule change)

1. **A hint is a job, shown when delivered.** The spec's `practice.request_hint`
   is one call; the sidecar is serial and a written hint takes seconds, so (as
   RW4a's library asks) it answers with a job and `practice.hint_job` reads it.
   "Written to `help_assists` when shown" is implemented as: the row is
   written prepared (`shown = 0`) and the job read that returns it marks it
   shown and writes its reveal. This is what makes G-H3's cancel exact: a
   hint cancelled (or never read) is never shown and counts nothing.
2. **The discriminating answer is its own RPC**
   (`practice.answer_discriminating`, the task's choice): fire-and-forget
   safe, and an answer need not ask for a new hint. Its row is placed at the
   question's work (the question row's `work_hash`), so "one at a time at a
   placement" holds without the screen sending its draft.
3. **Adaptive hints need `hints.telemetry_enabled`.** The rows are the count;
   with telemetry off the service answers `disabled` (the spec does not name
   the interaction).
4. **The reveal amount.** `answer_leak_overlap` alone scores a worked answer
   written in symbols as 0 (it is lexical); the delivered hint's amount is
   `max(span_answer_overlap, 1.0 if gives_away)`: the tutor's measure as the
   source spans use it, and a full reveal when the exact key is stated. Below
   level 4 leak control already keeps such text out.
5. **Each request is its own paid call.** The prompt carries the request's
   id, so asking again on the same work never returns an earlier request's
   checkpointed answer (found in testing: a withheld hint would otherwise be
   "recovered" on every retry).
6. **Leak expressions exclude the question's givens** (H1's rule for labels,
   applied to hint text): "1/2" in "P(X ≤ 1/2)" is never a leak.
7. **A waypoint at "the goal itself"** may target the goal node (the rubric
   offers that horizon) while leak control keeps the goal's state out of the
   text; any other leak node is refused as a target.
8. **`authored` is never a chooser option.** The fallback serves authored
   hints, and the writer may serve one verbatim at level 3 (`authored_index`),
   leak-checked; the Decider chooses among the written kinds.
9. **Fallback scope when the writer cannot run** (Codex, unpriced, capped,
   failing): the next authored hint serves for "More" and replies; worked
   help, `book_way` and `smaller_step` get `unavailable` with the reason (an
   authored hint is not what they asked for).
10. **No inline map build on a hint** (§4.3.1 row 2; the learner-route merge
    of row 3 is wired by the Codex review's F9: a shown hint schedules
    `merge_learner_routes` in the background, see `hints-h2a-codex-review.md`). The approach-map route resolves to Codex on the owner's vaults
    (29-37 s), so an inline build cannot fit a hint; H2a serves without the
    map kinds when there is no map (§4.4 "No map"), and build on serve already
    covers new items. Both are H2b/H4 friction notes below.
11. **The `hint_fit` verdict is written for "doesn't connect" replies only**
    (§5's table), not for `book_way`, `smaller_step` or "More".
12. **The answered-hint level for a reply on an authored hint is 3** (H0's
    `AUTHORED_LEVEL`).
13. **Writer receipts are labelled too** (`judge = llm`), beside the chooser's.

## 3. §10.1 confirmation (the reviewer's check of §5)

Checked on this base against `resolve_attempt_activity_policy`
(`diagnosis/causal_activity_policy.py:231`, via `classify_attempt_activity`
`:145` and `contamination_class_for_attempt` `:121`) and both certification
projections, `substrate/canonical_projection.py:791` and
`learner/facet_evidence_timeline.py:851`, which call it with the attempt's
`attempt_type`, `hints_used` and `primed`:

| Shown | Recorded | Policy (existing) |
|---|---|---|
| levels 1-3 | `hints_used += 1` | `counts_as_assisted`, no certification, FSRS unchanged (class `verification`) |
| levels 4-5 | `primed = true`, no count | `repair_activity`: no FSRS, no certification, assisted |
| key overlap | `reveal_events` `tutor_answer`, basis `hint:<kind>:L<level>` | admissibility, reveal-aware lanes, auto-prime's 0.35 sum |
| discriminating answer | `help_assists` row only | none |

A primed attempt with no hint count resolves to exactly the policy of a
primed attempt that also counted hints (asserted for both attempt types:
`test_a_primed_attempt_with_no_hint_count_is_classified_as_a_counted_one_is`),
as a guided redo's does. The learner field's arms are offline
(`FieldConfig.enabled = False`). **No mapping needs a new rule; no successor.**
One observation, not a rule change: a hint's key overlap joins auto-prime's
sum, so several partly overlapping hints can prime an attempt by the existing
rule (`test_levels_one_to_three_add_one_each_and_attach_to_the_attempt`).

§3's citations re-verified on `59d300e63` (substance holds; lines moved):
the fold `handlers/practice.py:1004-1009`, `submit_dont_know_on` `:1148`;
`hint_equivalents_for_submission` `tutor/tutor_qa.py:900`,
`answer_leaks_expected` `:975`; `instrument_expected_information_gain`
`diagnosis/probe_families.py:467`; `certification_credit`
`learner/capability_mapping.py:246`; `REVEAL_SOURCE_KINDS`
`attempts/reveal_ledger.py:49`; `AUTO_PRIME_REVEAL_THRESHOLD`
`attempts/attempts.py:160`; `DECIDER_TASKS` `ai/routing.py:113`;
`ChoiceQuestion` `ai/decisions.py:74`; `HintPolicy` `vault/models.py:396`,
`hints` `:783`; `error_events_for_attempt` `db/repositories.py:2147`,
`fetch_session_checkpoint` `:10429`, `causal_hypotheses_for_learning_object`
`:15304`, `unresolved_cause_factors_for_attempt` `:17156`;
`load_placement_state` `placement/state.py:1405`; `active_predictor`
`placement/predictor.py:164`.

## 4. Gates covered

G-H1 (`test_hint_kill_switch.py`: adaptive and telemetry off answer
`disabled`, write nothing, ask nobody; H0's practice scenario is
byte-identical in responses and every table with adaptive hints on or off;
a disabled request leaves the database file byte-identical; the served item
is identical), G-H2 and G-H3 (`test_hint_evidence.py`), G-H4
(`test_hint_blind.py`: the blind prompt of a hinted, primed attempt with a
marked map, hint, strategy, rival, question and answer equals the prompt the
same answer gets on a vault that never served a hint), G-H5 and G-H6
(`test_hint_contracts.py`), G-H7 and G-H8 (`test_hint_service.py`; the
decider route's no-fallback rule by `test_judge_routes.py`'s
`DECIDER_TASKS` parametrization, which now includes `hint_chooser`), G-H10
(`test_approach_map_replay.py` extended: two server hints folded into an
attempt, the hint routes forbidden during rebuild and shadow replay), G-H11
(`test_hint_service.py`: a capped day and an unpriced metered writer fall back
before any call; the ChatGPT plan is `estimated_only` and writes on a capped
day), G-H12 (labels and the wording lint, `test_hint_service.py`), G-H13 (the
contract and its three new lines, `test_approach_map_boundaries.py`; the RPC
pins, `test_mobile_allowlist.py`), G-H14 (`test_hint_kill_switch.py`: no
model call during a diagnostic block; the cold-check banner is frontend and
untouched), G-H15 (`test_hint_replies.py`), G-H16 (`test_hint_discriminating.py`).
Not in H2a: G-H9 (H1's), G-H17 (H0's schema; the widening is H2b's).

## 5. Tests

New (fakes only: `StructuredClientFake`, a decision-client fake, H1's
`MapFake` for stored maps; vaults from `tests/helpers.py` through H1's
builders): `tests/hint_fakes.py` (helpers), `tests/test_hint_service.py`
(31), `tests/test_hint_contracts.py` (23), `tests/test_hint_replies.py` (11),
`tests/test_hint_discriminating.py` (10), `tests/test_hint_evidence.py` (15),
`tests/test_hint_blind.py` (2), `tests/test_hint_kill_switch.py` (5): 97.
Changed: `tests/test_approach_map_replay.py` (G-H10 extended, 3),
`tests/test_mobile_allowlist.py` (the H2a pins), `tests/test_judge_routes.py`
(the two disclosures), `tests/test_hint_telemetry.py` (the report shows the
new keys), `tests/test_approach_map_boundaries.py` (the contract's three new
lines), `tests/conftest.py` (`LEARNLOOP_HINT_MODELS=off`).

## 6. Files

- Python: `src/learnloop/hints/{kinds,state,options,chooser,writer,contracts,discriminating,service}.py`
  (new), `src/learnloop/hints/__init__.py`, `src/learnloop_sidecar/handlers/hints.py`
  (new), `src/learnloop_sidecar/handlers/{__init__,practice}.py`,
  `src/learnloop/db/stores/help_assists.py`, `src/learnloop/decider_judgments.py`,
  `src/learnloop/ai/{routing,disclosures}.py`, `src/learnloop/config/{schema,template}.py`,
  `src/learnloop/params/parameter_registry.py`, `pyproject.toml`.
- Docs: this file; `docs/specs/spec_adaptive_hints_v1.md` §15 (the H2a note);
  the regenerated references (`Config - hints.md` and the other configuration
  notes' line citations and commit labels; the prose leaf counts in
  `Configuration.md` and `Database.md`: 894 leaves).
- No migration, no frontend, no Tauri change.

## 6a. Gate (this step; the full suite, the whole durability lane and vitest run once in the landing gate)

Run on the final tree (`8650441a7`), `TMPDIR` = the worktree's `fixtures-local/tmp`:
- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **26 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n auto` (template `.pyc` cleared first):
  **2028 passed** over the new hint tests (97), the H0/H1 hint tests
  (`test_hint_telemetry`, `test_help_assists_schema`, `test_approach_maps`,
  `test_approach_map_replay`, `test_approach_maps_schema`,
  `test_approach_map_boundaries`), the contract pins
  (`test_mobile_allowlist`, `test_judge_routes`,
  `test_provider_resolution_parity`, `test_architecture`, `test_table_roles`,
  `test_coordinated_migrations`, `test_tracked_fixture_databases`,
  `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`,
  `test_desktop_rpc_contract`, `test_vault_template`, `test_config_refactor`,
  `test_registry_audit`, `test_grading_cli`, `test_p0_cutover_mvp08`,
  `test_field_config`, `test_sensitivity_certificates`,
  `test_constraint_engine`, the `test_mvp0*_upgrade` snapshot files,
  `test_plan_determinism`, `test_open_world_gate`, `test_kinship_feature`,
  `test_chatgpt_plan_workspace`, `test_openai_embedding_client`,
  `test_project_cli`, `test_reading_step_switch`, `test_recurrence_commands`,
  `test_regrade_contract_successor`, `test_regrade_contract_upgrade`,
  `test_serve_eligibility_review`, `test_diagnosis_input_provenance`), the
  Decider callers (`test_decider_agreement`, `test_decider_landing`,
  `test_facet_reword_confirm`, `test_facet_span_support`,
  `test_method_explicit_landing`, `test_method_explicit_upgrade`,
  `test_tier1_decider`, `test_reader_intent`, `test_reader_rw1b_review`,
  `test_reader_rw1b_rereview`), every test file that drives the practice
  handler's submits (`test_causal_repair_sidecar_rpcs`,
  `test_daily_plan_composition`, `test_daily_plan_review_regressions`,
  `test_daily_plan_rpc`, `test_diagnosis_async_router`, `test_diagnosis_card`,
  `test_field_signal_production_paths`, `test_placement_opening_probes`,
  `test_reader_rw3a_landing`, `test_reader_workbench_rw2a`,
  `test_router_r1_composition`, `test_router_r2a_serving`,
  `test_router_r2bc_landing`, `test_sidecar_contract`,
  `test_sidecar_item_authoring`, `test_sidecar_trace_and_clarification`,
  `test_sidecar_tutor_qa`, `test_stuck_prompt`, `test_ux_phase4_feedback`)
  and the policy and grader contracts (`test_blind_grading_contract`,
  `test_causal_activity_policy`). The hint files reran twice more: 97 passed
  each time.
- Durability: `-m durability` on `test_help_assists_schema`,
  `test_hint_telemetry`, `test_approach_maps_schema`: **2 passed**; the new
  evidence, service and discriminating tests under `--durable-sqlite` (WAL,
  the job threads' concurrent connections): **56 passed**. No migration.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 211; 894 effective leaves).
- No frontend or Tauri change, so no npm, vitest or cargo step.
- A no-model smoke on a backup-API copy of `fixtures/linear_algebra` under
  `fixtures-local/h2a-smoke/` (every API-key variable unset, empty `HOME`,
  `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `LEARNLOOP_HINT_MODELS`,
  `LEARNLOOP_APPROACH_MAP_BUILDS` and `LEARNLOOP_ROUTER_MODELS` off): the
  vault's active provider is Codex and `ai.routing.hint_writer` is unset, so
  `practice.request_hint` answered `unavailable` / `codex_refused` with the
  spec's reason (that item has no authored hint), one unshown request row, and
  **0 model calls, 0 receipts, $0**. No paid or live call was made in this stage.

## 7. Owner-run commands

```bash
# Turn adaptive hints off (the kill switch; the practice RPCs are then exactly as before):
#   [hints]
#   adaptive_enabled = false
# Keep hints but stop asking the Decider (the fallback serves: authored hints, then the next step):
#   chooser_enabled = false
# Serve the Decider's top option instead of sampling (no off-policy evaluation then):
#   choice_policy = "argmax"

# The writer route. Unset, it is the active provider, and on Codex no hint is
# written (D9): the item's own hints serve and the result says why. Sign in to
# the ChatGPT plan once (the sign-in is saved outside every vault), add a
# chatgpt_plan profile to the vault and route the writer to it:
uv run learnloop ai signin chatgpt
uv run learnloop ai status chatgpt --vault <path>
#   [ai.providers.chatgpt]
#   type = "chatgpt_plan"
#   model = "<a model `learnloop ai models chatgpt --vault <path> --profile chatgpt` lists>"
#   [ai.routing]
#   hint_writer = "chatgpt"
uv run learnloop ai latency --vault <path> --provider chatgpt --provider codex_low --runs 3
# A metered (OpenRouter) writer instead needs a price, and is held to the daily cap:
#   [hints]
#   price_per_million = <USD per million tokens>
#   max_daily_cost_usd = 1.00
# The chooser is the Decider (ai.routing.hint_chooser; unset: openrouter_decider), which
# needs OPENROUTER_API_KEY in settings.env; without it the fallback serves.
uv run learnloop config effective --vault <path>         # check the [hints] section
uv run learnloop hints report --vault <path> --json       # H0/H1's report (per-kind rows are H2b)
```

The sign-in, status, models and latency commands are the merged provider's
(`docs/reviews/chatgpt-plan-provider.md`, "CLI").

## 8. Open questions (with the default taken)

1. **adaptive_enabled defaults on** (live behind its kill switch, the owner's
   rule). Until H2b no UI calls the RPC, so nothing changes for the learner;
   on the owner's vaults (Codex active) a request would serve authored hints
   and say why. Default: on.
2. **The ChatGPT-plan sign-in** is still pending, so no hint is written on the
   owner's vaults until `ai.routing.hint_writer` names a signed-in plan
   profile or a priced OpenRouter profile. Default: unset (authored fallback).
3. **Rival weights are uniform.** An open probe episode's posterior is over
   its own hypothesis set and a facet's `hypothesis_marginal` is not tied to
   these rivals; mapping either to the rivals is left for when a surface
   supplies both (the workbench's check). Default: uniform, labelled.
4. **Auto-prime from hint reveals.** Several partly overlapping hints can sum
   past 0.35 and prime an attempt by the existing rule (§3). Default: as the
   rule says; the owner may prefer hints not to join the sum (a successor).
5. **`submit_dont_know`'s tutor-question asymmetry** (§14 Q5) is left as it
   was; only the server rows join there.
6. **The "doesn't connect" verdict for picks.** `book_way` and `smaller_step`
   write no `hint_fit` verdict (§5 names only the replies). Default: replies only.
7. **The answer text of a discriminating question** stays on its row
   (`feedback_text`) until H2b's `hint_feedback` adapter reads it.

## 9. Friction notes for H2b, RW2b/H3 and H4

**H2b (the panel and the rest of H2).**
1. *The RPC contract.* `practice.request_hint {sessionId, practiceItemId,
   submissionId, answerMd?, request, answeredAssistId?, feedbackShortcut?,
   feedbackText?, feedbackSelection?, takenLevel?, secondsOnItem?}` answers
   `{jobId, state: pending|done|cancelled, result}`; poll `practice.hint_job
   {jobId}` (it answers at once; pace the polls); the read that returns
   `state = done` with `result.status = ready` shows the hint (`result.shown =
   true`): render exactly that result. Statuses: `ready`, `withheld`
   (`message` is the spec's wording), `unavailable` (`reason`, `message`),
   `disabled` (keep today's authored path), `refused` (diagnostic block),
   `cancelled`. Flush the draft first or send `answerMd`. Add the Tauri
   passthroughs (`practice_request_hint`, `practice_hint_job`,
   `practice_cancel_hint`, `practice_answer_discriminating`).
2. *Labels.* `result.labels = {origin, kind, worked_help, horizon}`; show the
   picks from `result.picks` (each with `worked_help` and `consequence`) before
   they are taken; `result.replies` lists the quiet lines (`smaller_step` only
   under a waypoint).
3. *Cancel and the authored offer.* After `hints.authored_offer_after_seconds`
   (4; add the key in H2b) offer the item's hint: call `practice.cancel_hint`
   first, then reveal it with `practice.record_hint_reveal` (client-counted);
   a cancel after delivery answers `already_shown` and the hint stays.
4. *The discriminating answer box.* `result.discriminating` (`rivals` as ids
   and statuses only, `predictedAnswers`, `eigNats`, `answerBox`); send the
   one-line answer to `practice.answer_discriminating {sessionId,
   practiceItemId, submissionId, questionAssistId, answerMd}` and show its
   `message`; never put it in the answer draft.
5. *The help-style editor* writes `hints.help_style` (Settings and the "⋯"
   menu); the service reads it per request.
6. *Outcome placement* (`hint_outcome`, `hints.outcome_placement_enabled`)
   joins the maps' envelope (`hints.maps.max_daily_cost_usd`), per §7.3.
7. *The `hint_feedback` adapter and migration 212's widening* of both
   `source_kind` CHECKs: the texts are `help_assists.feedback_text` on rows
   with `request = 'feedback'` (role `hint_feedback`) and on
   `assist_kind = 'discriminate_answer'` rows (role `discriminate_answer`).
8. *Per-kind report rows* read `help_assists` (`hint_kind`, `level`,
   `chooser`, `propensity`, `drawn_option_json`, `contract_failures_json`'s
   `outcome`, `shown`) and `judgment_ledger` (`hint_choice`, `hint_fit`).
9. *The inline map build* on a hint (§4.3.1 row 2) is not wired:
   `map_builder.build_map_inline` needs a route that fits a hint's time (not
   Codex). The lazy learner-route merge (row 3) runs in the background after
   delivery (`schedule_merge_after_hint`, review F9).
10. *Unplaceable work.* A route-directed hint on work the writer placed on no
    route and found not clearly valid becomes a checked approach question on
    "More" (review F7); a reply keeps its level, so H2b may want the chooser's
    state to carry the previous placement and offer the approach question
    there too.

**RW2b / H3.** Call `learnloop.hints.service.request_hint` with the workbench
surface once the service accepts it (H2a validates `surface = 'practice'`);
the workbench's level is a rung the learner takes (`taken_level` 1-5 there,
and its fallback is the Reader's rung progression, §4.5), its placement is
the check's `continue_from` node, and its rows add the workbench columns. The
job pattern and the delivery-marks-shown rule carry over.

**H4.** Guided redo and the tutor call the same service with their surface;
the redo's preserved prefix is the work, and its diagnosis's rivals join the
state.
