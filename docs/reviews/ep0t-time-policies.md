# EP0t: named evidence-time policies, the cutoff value and the prediction target's identity

Evidence packets spec (`docs/specs/spec_evidence_packets_v1.md`) §7.1-7.2, §7.6, §7.7.4, §8 EP0t, §10. A structure
step: no read result, ordering, exception, cache key, seed, prompt or stored value changes; no migration, table,
config key, algorithm tag, kill switch, status-history writer or replayer.

- **Base:** `52b9edc050` (origin/main). **Head:** the commit that adds this record, on `46663124be` (branch `ep/ep0t-time-policies`).
- **New modules:** `src/learnloop/db/evidence_cutoff.py` (the `Cutoff` value, its presets, the comparison kernels
  and the mutable-field inventory) and `src/learnloop/db/prediction_target.py` (`PredictionTarget`,
  `target_hash`). Both import only the standard library (and `learnloop.clock`), checked by
  `tests/test_evidence_cutoff.py::test_the_module_imports_nothing_of_learnloop_but_the_clock`. They sit in
  `learnloop.db` beside `db/attempt_availability.py`, the existing evidence-time predicate, which attempts,
  diagnosis, the router, adaptive difficulty and the field already import under every contract: no new
  import-contract exception, and no new first-level module (the structure ratchet's `first_level_root_modules`
  stays 36).
- **Census:** `tests/fixtures/evidence_cutoff_census.toml`, held to the tree by `tests/test_evidence_cutoff_census.py`.

## 1. The value

`Cutoff(preset, admission, corrections, anchor_kind, anchor_id, times, boundaries, tie_order, availability,
corrections_then, approximate, schema="evidence_cutoff/1")`, frozen. Each `Boundary` is
`(subject, time, op, anchor, comparison, missing, malformed)`: `op` is `<` or `<=`, `comparison` is `instant`
(parsed UTC), `text` (stored string), `text_key` (`(created_at, id)` as text) or `days` (AD's float days), and
`missing`/`malformed` say whether a row without a time, or with an unreadable one, is `excluded`, `admitted`,
`ignored` or `raises`. `to_json()` is canonical (sorted keys, compact, UTF-8 kept); `from_json(to_json(c)) == c` for
every preset (times are held sorted so the round trip is exact). `identity_scalar()` returns the scalar each reader
keyed by before the type existed (an `as_of`, a closure's date or stamp, an attempt id, None for current): no
existing key, seed, hash or prompt receives the dataclass or its JSON (checked by the unchanged identity pins,
section 6).

`Cutoff.admits(occurred, received=None, attempt_id=None)` applies the preset's attempt rule exactly as its reader
does; `history_v1` adds `written_before` (records) and `mark_before` (learner marks).

## 2. Presets: strictness, ties, availability

| Preset | Admission | Boundaries (op, comparison) | Ties | Availability | Missing / malformed | Corrections |
|---|---|---|---|---|---|---|
| `current` | all | none | — | — | admitted | now |
| `corrected_before(attempt, occurred_at)` | occurred before | `(created_at, id) < (occurred_at, attempt)`, text key | by id | created_at | admitted (text `"None"`, `""`) | now |
| `as_known_at(known_at, fields=)` | known by | `received or created <= known_at`, instant | `(created_at, id)` | received if non-empty, else created (loaded-row form) | excluded (fails closed) | **then**; each asked field the inventory cannot reconstruct is listed in `approximate`. No reader uses it yet |
| `closure_through(local_date)` | occurred and received by | occurred `<` limit, received `<` limit, instant; limit = next local midnight computed in the machine's zone and stored as an instant; `9999-12-31` (or an unreadable date) is the far future, `<=` | — | both times tested | occurred missing excluded; received missing ignored; unreadable raises | now (grades, holds, quarantine, epoch) |
| `closure_at(stamp)` | same | both `<=` the stamp, instant | — | both | same | now |
| `history_v1(attempt, completed_at, known_at=, available_at_reads=)` | attempts by order and known time; records by write time | attempts: `(created_at, id) < target`, text key, and with the switch on a non-empty readable `received_at` `<=` the target's known time (its receipt, else its completion), instant; records: written `<` the target's completion, instant; learner marks: `created_at` `<` the target's completion, text | by id | received (non-empty) with the switch on, else created_at | attempt: admitted; record: excluded | now, except a causal hypothesis's version: its latest written before the cutoff (`corrections_then`) |
| `ad_replay(as_of)` | occurred by | attempts, reading opportunities, claims: `days(t) <= days(as_of)` | `(created_at, id)` | created_at | unreadable skipped; an unreadable `as_of` raises; no `as_of`: every readable time | now (grades, quarantine, holds, claims' supersession), protection now through the material view |
| `completed_by(as_of)` | occurred by | `created_at <= as_of`, **text** | `(created_at, id)` | created_at | `None` raises `TypeError`, `""` admitted; no `as_of`: all | now (latest surviving epoch, the field's revision policy) |

Characterized, not changed (tests in `tests/test_evidence_cutoff.py`): the field's text comparison admits
`…09:00:00.5Z` (a later instant whose text sorts first) and excludes `…10:00:00+02:00` (an earlier instant); AD
does the opposite; `history_v1`'s attempt order is text too. The attempt writer stamps `utc_now_iso` (whole
seconds, `Z`), where text and instant order agree; other writers' formats were not surveyed (question 3).

## 3. Caller -> preset matrix

Statuses: **adapted** (the reader's comparison is now the preset's kernel, moved verbatim, or the reader states
its preset), **named** (follows an adapted reader), **no_preset** (no preset reproduces it without a changed
result: not adapted, how it differs is given), **not_a_cutoff**. Lines at the head of this branch.

| Caller | Preset | Status | Evidence / how it differs |
|---|---|---|---|
| `router_objective/checks.py:485` `Closure.through` | closure (through) | adapted | every event a check's completion, rate or score counts, to the end of a local date: exclusive at the next local midnight (the far future inclusive); both an answer's occurrence and received time; grades, holds, quarantine and the current epoch now |
| `router_objective/checks.py:493` `Closure.at` | closure (at) | adapted | the same events to a stamp (a window's closing moment), inclusive |
| `router_objective/checks.py:500` `Closure.admits` | closure (through, at) | adapted | the one test every counted event passes (assignment rows, sessions, administrations, skips, displacements, help shown, answers) |
| `router_objective/checks.py:507` `_closure` | closure (through) | named | resolve and completion with through= a local date |
| `router_objective/checks.py:705` `r_for` | closure (through) | named | a day's r_L, closed at the end of that day unless a closure is passed |
| `router_objective/checks.py:714` `support_at` | closure (at) | named | the latest drawn day's r_L as of a stamp (the stop coin's support) |
| `daily_plan/objective_inputs.py:380` `_combiner_read` | closure (at) | named | the memory model's combiner fit on resolved randomized checks as of the decision's now_iso |
| `router_objective/scores.py:512` `_context.as_of` | closure (at) | named | a closed window's score reads (resolved checks, completion, r_L, prices, exam results) as of its closing moment |
| `router_objective/tail_data.py:609` `_exam_result_known` | closure (at) | named | an imported exam result as known at a stamp (the learned tail's dated reward) |
| `router_objective/tail_data.py:625` `transitions` | closure (at) | named | the learned tail's transition rewards: the checks as they stood at the read's stamp |
| `router_objective/tail_data.py:646` `transitions.as_of_end` | closure (at) | named | each transition's end as of its own stamp |
| `daily_plan/objective_inputs.py:330` `decision_reads` | — | not_a_cutoff | a cache scope, not a cutoff: one decision's builds share a read while the database's commit version (PRAGMA data_version) is unchanged; any commit invalidates it; the reads inside are closure(at now_iso) (_combiner_read). No historical snapshot API |
| `diagnosis/split/history.py:767` `VaultHistoryStore._load` | history_v1 | named | the loader: received_at is selected (and a non-empty, readable one becomes the known time) only with available_at_reads on; grading evidence current (superseded_at IS NULL), holds now, factor, misconception and candidate status now, every causal hypothesis version kept |
| `diagnosis/split/history.py:1260` `VaultHistoryStore.cutoff` | history_v1 | adapted | the preset the store states for a target |
| `diagnosis/split/history.py:1254` `VaultHistoryStore._known_by` | history_v1 | adapted | attempts: known (a non-empty received_at) by the target's known time, else its completion, inclusive, parsed instants |
| `diagnosis/split/history.py:1063` `VaultHistoryStore._written_before` | history_v1 | adapted | records (hypotheses, factors, registry rows, cold verifications): written strictly before the target's completion instant; an unknown time is never before |
| `diagnosis/split/history.py:1271` `VaultHistoryStore.attempts_before` | history_v1 | named | prior attempts: (created_at, id) text order strictly before the target's, and known by its known time; learner marks by created_at text strictly before the target's completion text (_marks_as_of) |
| `diagnosis/split/history.py:1324` `VaultHistoryStore.lagged_attempts` | history_v1 | named | the receipt's count of attempts the cutoff does not show (later, or earlier but not yet known): grows with later attempts, so a delayed diagnosis's receipt differs from a live one's |
| `diagnosis/split/history.py:1077` `VaultHistoryStore._hypotheses_as_of` | history_v1 | named | hypotheses as of the target: source attempt before it and written before it; a causal hypothesis in its latest version written before the cutoff (corrections then); a mutable row's last_updated falls back to its creation when the update postdates the cutoff, its status now |
| `diagnosis/split/history.py:1106` `VaultHistoryStore._observed_before` | history_v1 | named | cold verifications: written before the target and, when the cold attempt is known to the store, ordered before it (no known-time gate on that attempt) |
| `diagnosis/split/history.py:1416` `StaticHistoryStore.cutoff` | corrected_before | adapted | a planted learner's constructed past: attempts and records by (created_at, id) of the attempt or source attempt, strictly before the target, no known-time gate |
| `diagnosis/split/context.py:680` `assemble_diagnosis_context` | history_v1 | named | the diagnoser's context: prior attempts, hypotheses, registry, repairs and the receipt's lagged count at the diagnosed attempt |
| `diagnosis/split/context.py:624` `_registry_shortlist` | history_v1 | named | the registry universe a retriever shortlists |
| `diagnosis/split/snapshot.py:240` `export_snapshot` | history_v1 | named | the snapshot history mode's export of everything before the target |
| `diagnosis/split/jobs.py:788` `_diagnose` | history_v1 | named | hybrid retrieval's earlier non-passes |
| `diagnosis/split/jobs.py:1343` `_estimated_retrieval` | history_v1 | named | the retrieval estimate's registry and failures |
| `diagnosis/offline_review/runner.py:1178` `ReviewRun.stage_grades` | history_v1 | named | an offline review's prior attempts per staged attempt |
| `field/probability_states.py:452` `StateRenderer._card` | history_v1 | named | a prediction point's prior attempts (AttemptRef at the observation) |
| `field/probability_states.py:587` `StateRenderer._hypotheses` | history_v1 | named | a prediction point's hypotheses and repairs |
| `adaptive_difficulty/replay.py:332` `load_events` | ad_replay | adapted | attempts, reading opportunities and claims at or before as_of in float days (unreadable times skipped; no as_of: every readable one); through the material view, whose protection is today's; grades, quarantine, holds and claims' supersession (superseded_by IS NULL) now; exposures for warmth unbounded by as_of but read strictly before each serve |
| `adaptive_difficulty/replay.py:871` `snapshot` | ad_replay | named | the cached state; every production caller passes no as_of (ad_replay(None)); the cache key keeps the scalar as_of (Cutoff.identity_scalar), the loaded events are fingerprinted separately |
| `field/outcomes.py:429` `_load` | completed_by | adapted | attempt rows whose created_at text is at or before as_of text (None raises, empty is admitted); the latest surviving grading epoch and the field's revision policy now |
| `field/outcomes.py:698` `load_attempt_rows` | completed_by | named | the field's immutable attempt rows |
| `field/outcomes.py:770` `load_facet_rows` | completed_by | named | the field's facet rows |
| `adaptive_difficulty/forecasters.py:93` `_challenger` | completed_by | named | the challenger forecaster's field rows as of the serve (as_of=served_at), through the material view |
| `adaptive_difficulty/history_card.py:195` `_Reads.attempts` | — | no_preset | text: created_at <= ? AND {known} <= ? AND {available} <= ? (served_at), inclusive; nearest closure(at), which parses |
| `adaptive_difficulty/outside.py:192` `history_card` | — | no_preset | parsed instants, strict: occurred < served and known < served, a missing time excluded; closure(at) is inclusive |
| `confidence_events.py:232` `taps_before` | — | no_preset | text: {known} < ?, strict, no occurrence test |
| `confidence_events.py:260` `learner_events` | — | no_preset | text: {known} < ?, strict |
| `daily_plan/check_inputs.py:60` `_evidence_as_of` | — | no_preset | text: {known} <= ?, inclusive |
| `daily_plan/objective_inputs.py:410` `_combiner_with_traces` | — | no_preset | see router_objective/combiner_data.py::rows |
| `daily_plan/router_card.py:187` `CardGatherer.inputs` | — | no_preset | text: {known} < ?, strict, ordered by {known} |
| `daily_plan/router_card.py:444` `CardGatherer._attempts` | — | no_preset | text: {known} < ?, strict |
| `daily_plan/router_card.py:576` `CardGatherer._interaction` | — | no_preset | text: {known} < ?, strict |
| `db/stores/lessons.py:174` `pending_delayed_checks` | — | no_preset | text: created_at > lesson close AND {known} <= ?, inclusive |
| `learner_context.py:1321` `_traces` | — | no_preset | text: {known} <= ?, inclusive |
| `reader_learner_state.py:195` `_build` | — | no_preset | text: {known} < ?, strict |
| `router_objective/combiner_data.py:131` `rows` | — | no_preset | loaded-row known time parsed, inclusive against now; a missing known excluded, an unreadable one raises |
| `router_objective/miss_cause.py:159` `latest_misses` | — | no_preset | text: created_at <= ? AND {known} <= ?, inclusive |
| `router_objective/miss_cause.py:462` `surprise_reference` | — | no_preset | text: {known} <= ?, inclusive |
| `router_objective/miss_cause.py:522` `_between` | — | no_preset | text key order like history_v1's, but the known time is SQL text against now_iso, not a parsed instant against the target's |
| `router_objective/miss_cause.py:547` `beta_rows` | — | no_preset | text: created_at <= ? AND {known} <= ?, inclusive |
| `router_objective/miss_cause.py:671` `_offer_rows` | — | no_preset | SQL {known} read back, then text: str(known) > now_iso excluded |
| `router_objective/preferences.py:149` `features_at` | — | no_preset | text: {known} <= ?, inclusive |
| `router_objective/scores.py:206` `exam_result_known` | — | no_preset | text: substr(created_at, 1, 10) = date AND {known} <= ? |
| `router_objective/tail_data.py:366` `_receipt` | — | no_preset | text: known > at excluded, inclusive |
| `router_objective/tail_data.py:540` `logged` | — | no_preset | text: known > at excluded, inclusive |
| `teacher/check_delivery.py:377` `classify` | — | no_preset | text: {known} <= ?, inclusive |
| `teacher/diagnosed_sources.py:226` `_miss` | — | no_preset | text: created_at <= ? AND {known} <= ?, inclusive |
| `teacher/diagnosed_sources.py:359` `_asked_miss` | — | no_preset | text: created_at <= ? AND {known} <= ?, inclusive |

### Readers that fit no preset (stopped, not adapted)

The 25 `no_preset` rows above are the availability predicate's readers (`attempt_time_sql` in SQL, `known_at` over
loaded rows) outside the diagnoser's history. Each compares `COALESCE(received_at, created_at)` (switch on) or
`created_at` (off) with a caller's stamp, as **text** in SQL, strict (`<`) at six SQL sites and inclusive (`<=`)
elsewhere, some also bounding `created_at`; `adaptive_difficulty/outside.py::history_card` and
`router_objective/combiner_data.py::rows` parse instants (strict on both times, and inclusive on the known time,
respectively). The nearest preset, `closure`, parses instants and tests occurrence and receipt separately;
`history_v1` orders by `(created_at, id)` and parses its known time. Mapping any of them onto a preset would change
which rows they admit on non-canonical stamps or empty receipts, so none was adapted. The SQL form keeps an empty
receipt as `''`, which sorts before every time, while `known_at` falls back to `created_at`
(`tests/test_evidence_cutoff_readers.py::test_the_sql_form_reads_an_empty_receipt_as_text`); the attempt writer
stores a blank receipt as NULL, so no written row has one. Question 1 below.

## 4. Mutable-field inventory

`MUTABLE_FIELDS` in `db/evidence_cutoff.py` (the spec's §7.1 table re-located at this tip, plus the help ledger's
set-once updates). `tests/test_evidence_cutoff.py::test_the_inventory_names_real_columns` checks every stored
table and column exists in a fresh schema. `as_known_at(fields=...)` lists every asked field below `exact` /
`by_timestamp` in `approximate`, never silently current.

| Field(s) | Recoverable | How |
|---|---|---|
| `grading_evidence.superseded_at`, `.superseded_by_evidence_id` | by timestamp | the epoch in force at a time is the rows not yet superseded |
| `practice_attempts.rubric_score`, `.correctness`, `.confidence` | partial | from grading evidence where criterion rows exist |
| `(held_for_review).held` | partial | blind records and current evidence by their times, except the review reason replay writes |
| `misconceptions.status` | exact | `misconception_transition_events` (since migration 056) |
| `misconceptions.statement`, `.facet_ids_json`, `.severity`, `.source_error_event_ids_json` | none | overwritten |
| `misconception_candidates.status`, `.occurrence_count`, `.source_error_event_ids_json`, `.statement`, `.statement_normalized` | none | no history |
| `unresolved_cause_factors.status` | partial | a resolution's observation ids date it |
| `unresolved_cause_factors.candidate_causes_json` | none | overwritten |
| `probe_presentations.status`, `.submitted_at`, `.ended_at` | by timestamp | each status change stamps a time |
| `probe_episodes.status`, `.completed_at` | by timestamp | completion dated |
| `probe_episodes.completion_posterior_json`, `.completion_detail_json` | none | the posterior before completion is not kept |
| `remediation_episodes.state`, `.primed_attempt_id`, `.cold_attempt_id` | none | overwritten |
| `error_events.status`, `.misconception_id` | none | overwritten |
| `learner_claims.superseded_by` | by timestamp | the superseding claim's creation |
| `learner_claims.applied_after_attempts` | none | a running count |
| `followup_tasks.consumed_attempt_id` | partial | the consuming attempt's time |
| `followup_tasks.status`, `.not_before` | none | overwritten |
| `fitted_parameters.active`, `.deactivated_at` | by timestamp | history rows kept |
| `help_assists.shown`, `.shown_at` | by timestamp | set once with `shown_at` |
| `help_assists.attempt_id` | partial | the attach writes no time of its own |
| `help_assists.submitted_at`, `.submit_latency_seconds` | partial | an attach may fill a submit time it did not observe |
| `help_assists.practice_session_id` | none | a workbench row's session filled later |
| `(protection).material_view` | none | exam reservations and held-out spans applied as of now |

Settled by test (the sheet's open row on historical help visibility):
`tests/test_evidence_cutoff_readers.py::test_a_hint_shown_then_attached_after_the_cutoff_is_partly_reconstructable`
writes an assist, shows it, and attaches it after a cutoff through the store's own functions: the attach changes
only `attempt_id` and `submitted_at` and records no time of its own, so `shown`/`shown_at` are exact as of the cutoff
and `attempt_id`/`submitted_at` are reported approximate.

## 5. The prediction target and its pin

`PredictionTarget(kind, members, unit, event_version, resolver_version, action_kind, action_id, horizon_kind,
horizon, anchor_kind, anchor_id, schema="prediction_target/1")`; `TargetMember(kind, id, revision, source)` with
kinds `item`, `learning_object`, `facet`, `surface_group`. Members are held sorted by every field (construction
order never reaches the bytes); a repeated member is refused, not collapsed; every value is a string or null (no
float formatting); no display text is accepted. `target_hash()` is `sha256:` + the sha256 of `canonical_json()`.

New identity site **EP0t** in `tests/identity_pins_helpers.py` (sources `PredictionTarget.canonical_json`,
`PredictionTarget.target_hash`), two pins at fixed inputs:

- `EP0t.full` = `f0cbcc2b50d110c6eff2bfe7306820316ad50145a80269634524a92a1d6be261` (digest of the pinned canonical
  JSON and `target_hash` = `sha256:4a82c035fa03dc2fc212055c1344881bb0f51aefcc13efb8a3a0093a885c70a7`)
- `EP0t.minimal` = `3453bfb6acbeed24d8a8168e2e1c3950ba20af22411da1eaa70bde1ed89d10a2` (`target_hash` =
  `sha256:195d03a81cb43794254b36c92c889c6e8e88b8e185fa35772efff7d48a004e63`)

The cutoff's serialization is not a compared identity (EPp stores it beside a receipt); its exact bytes for one
preset are held by `test_the_serialized_form_names_preset_policies_anchor_boundaries_and_approximation`.

## 6. Old identities unchanged

- `uv run python tests/test_identity_pins.py --write` recomputed every pin at its fixed input; the only change to
  `tests/goldens/identities.toml` is the two added `EP0t.*` lines (`git diff` shows `2 insertions(+)`, no deletion),
  and `tests/goldens/identity_shapes.toml` is untouched. `tests/test_identity_pins.py`: all pins, shapes and the
  AST coverage check pass (no new dump reaches a hash: the target hashes an explicit field list, not `asdict`).
- No existing key receives the new types: the AD snapshot cache key still carries the scalar `as_of`
  (`replay.snapshot`, unchanged), `Closure`'s new `cutoff` field is `compare=False` so closure equality and hashing
  are the predecessor's, and no prompt, seed or manifest builder was touched.
- The diagnosis journey golden, the due-queue goldens and the RO5/RO6 suites pass unchanged (section 8).

## 7. Tests: fail-first and characterization

- **Characterization (passing before any reader was adapted):** `tests/test_evidence_cutoff_readers.py` was
  written and run against the unadapted readers first: 18 passed (the presets reproduced the base readers on real
  vaults), then again after the adaptation.
- **Fail-first (Closure stating its preset):** `tests/test_evidence_cutoff.py` before `Closure` was adapted: 9 failed
  (`AttributeError: 'Closure' object has no attribute 'cutoff'`), 30 passed (the kernels' literal matrices against
  the verbatim predecessor expressions); after: all pass.
- **Fail-first (target and census):** with `db/prediction_target.py` and the census fixture absent,
  `tests/test_prediction_target.py` fails to import (`ModuleNotFoundError`) and the census test fails
  (`FileNotFoundError`).
- The kernels are the readers' expressions moved verbatim; the literal matrices compare the moved kernel, the
  adapted reader and the preset with a verbatim copy of the base expression on the same inputs, exceptions included
  (`_base_*` in `tests/test_evidence_cutoff.py`).
- The type was drafted before its tests were written; the type-level tests' fail-first evidence is the import
  failure above, not a red run against an earlier API.

## 8. Commands and results

All through the scratch wrapper, each pytest run in a 3G memory scope at `-n 1` with explicit targets.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui`; `uv pip install --offline pypdfium2==5.14.0` | installed |
| `pytest tests/test_evidence_cutoff_readers.py` against the unadapted readers (before the store's `cutoff` assertions and the help test were added) | `18 passed` |
| `pytest tests/test_evidence_cutoff.py` before `Closure` was adapted | 9 failed (`AttributeError: 'Closure' object has no attribute 'cutoff'`), 30 passed |
| `pytest tests/test_evidence_cutoff.py tests/test_evidence_cutoff_readers.py` after the adaptation | `57 passed in 4.93s` |
| `pytest tests/test_prediction_target.py tests/test_evidence_cutoff_census.py` with the target module and the census fixture moved aside | collection error `ModuleNotFoundError: No module named 'learnloop.db.prediction_target'`; `FileNotFoundError` on the census |
| `python tests/test_identity_pins.py --write` | `tests/goldens/identities.toml`: `2 insertions(+)` (`EP0t.full`, `EP0t.minimal`), nothing else changed; shapes file unchanged |
| `pytest tests/test_evidence_cutoff.py tests/test_evidence_cutoff_readers.py tests/test_evidence_cutoff_census.py tests/test_prediction_target.py tests/test_identity_pins.py` | `429 passed in 21.32s` |
| `pytest -m "not arc_close"` chunk 1 (21 files: `test_ad2_model`, `test_ad2_serving`, `test_approach_map_replay`, `test_daily_plan_replay`, `test_diagnosis_history_modes`, `test_diagnosis_journey_golden`, `test_diagnosis_replay`, `test_due_queue_golden`, `test_due_queue_read_builds`, `test_field_signal_production_paths`, `test_field_split_outcomes`, `test_field_workbench_signals`, `test_intervention_outcomes_replayer`, `test_mvp017_route_check_replay`, `test_probability_prep`, `test_rebuild_history_appends`, `test_regrade_contract_replay`, `test_ro0_row3_ask_availability`, `test_ro1_availability_reads`, `test_ro2_history_forecaster`, `test_ro2_history_protection`) | `252 passed, 3 skipped in 87.29s` |
| `pytest -m "not arc_close"` chunk 2 (20 files: `test_ro2_history_resolve`, `test_ro5_calibration`, `test_ro5_checks`, `test_ro5_codex_rereview`, `test_ro5_codex_review`, `test_ro5_landing`, `test_ro5_stop_coin`, `test_ro5_successor`, `test_ro6_codex_rereview`, `test_ro6_codex_review`, `test_ro6_landing`, `test_ro6_serving`, `test_ro6_successor`, `test_ro6_tail_data`, `test_rospeed2_connections`, `test_rospeed2_section_map`, `test_rospeed_join`, `test_rospeed_watcher`, `test_router_outcomes`, `test_stuck_prompt_replay`) | `286 passed in 267.80s` |
| `pytest -m "not arc_close"` the four new files, `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_ro1_availability`, `test_practice_availability` | `503 passed in 81.62s` |
| `pytest tests/test_test_layout.py` (alone) | `3 passed in 19.51s` |
| `pytest tests/test_architecture.py` (alone) | `18 passed in 30.42s` |
| `python scripts/check_gate_partition.py` | `collected 32204: landing 32139 + arc_close 65` |
| `ruff check` | `All checks passed!` |
| `lint-imports --no-cache` | `Contracts: 44 kept, 0 broken.` |
| `git diff --check` | clean |

## 9. Not checked

- The landing gate, the arc-close gate, the durability lane and the P-shadow/P-draw lanes (the orchestrator's).
- The full affected set: `scripts/affected_tests.py` lists 486 files for the changed modules; the run used the name
  filter `ro5|ro6|history|replay|field_|outcomes|closure|availability|due_queue|diagnosis_journey|ad2_|rospeed|probability`
  over that list (41 files) plus the brief's named availability files.
- The no_preset readers' behaviour on owner data (whether any stored row has a non-canonical stamp or an empty
  receipt): no owner vault was opened.
- The spec's recoverability claims beyond the help ledger's: the inventory test checks that each column exists,
  not that its history is (or is not) recoverable.
- Vault references were not regenerated (the landing does).

## 10. Questions

1. **The availability SQL family (25 readers).** No preset reproduces them. Should EP name an eighth preset for
   "known by a stamp, text comparison of `COALESCE(received_at, created_at)`, strict or inclusive per site", or should
   EP4 move them onto `closure`/`as_known_at` as a behaviour change under the playbook?
2. **Empty receipts.** The SQL form admits a row whose `received_at` is `''` at any cutoff; the loaded-row form reads
   its `created_at`. No writer stores `''` today. Leave as is, or make the migration-free writer guarantee a tested
   invariant?
3. **Text comparisons.** `completed_by` and `history_v1`'s attempt order compare stored text, which agrees with
   instant order only for one-width `Z` stamps. Is that an invariant of every attempt writer (worth a guard),
   or a latent difference for EP4?
4. **`lagged_attempts`.** A delayed diagnosis's receipt counts more lagged attempts than a live one's at the same
   target (the history itself is equal at fixed corrections). Is the receipt count meant to be part of "a live and a
   delayed diagnosis read the same history" (EP §10)?
5. **`as_known_at`.** It exists as a value only (no reader applies historical corrections). EP4 decides which
   reader moves onto it.
