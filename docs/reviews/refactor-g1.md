# G1. Facts, not a second decider

Base `2e3de890ff`. Structure track: no served or persisted value changes, except the one log field the step exists to
correct (FG1's `observational.decide_probe`, §3). [Strategy §2.10](../specs/refactor_strategy_v3.md#210-arc-g-one-decider-one-record-of-each-fact-one-belief-one-protection)

## 0. Step 0: what `decide_probe` reads, decides and feeds (at the base, before editing)

### 0.1 Inputs and where each comes from

`decide_probe` (`diagnosis/causal_probe_coherence.py:406-518`) reads only its arguments, plus the fitted store when it
is given no `parameters`. It reads no clock. In production its only deciding caller is
`causal_orchestrator._status_for_factor` (`:944-957`), which gathers every argument before the call:

| Argument | Unit | Gathered by (`diagnosis/`, base line) | Source |
|---|---|---|---|
| `repair_class_ids` | ids | `probe_targeting.classify_cause_set` over the factor's candidate causes (`causal_orchestrator.py:670`) | repository (factor, hypotheses) |
| `common_repair_covers` | flag | `repair_class_need_for_factor` (the diagnosis receipt's cover, read from the attempt's debug payload) or `not targeting.probe_worthy` (`:828-829`) | repository |
| `expected_information_gain` | share of locked-hypothesis pairs the instrument's blind bundles separate, 0 to 1 (not nats) | `causal_reads._discrimination_inputs` over the chosen candidate's recorded `discrimination` (`:879-880`) | repository (candidates), then deterministic |
| `probability_information_changes_repair` | share of separable pairs in different repair classes, 0 to 1 | the same (`:881`) | as above |
| `probe_burden_minutes` | minutes | `causal_reads._probe_burden_minutes`: the instrument card's `expected_seconds` / 60, else the orchestrator default 1.5 (`:917-921`) | repository (family links, card), fitted store `causal_orchestrator_policy` (nothing writes it: the default serves) |
| `avoided_overteaching_minutes` | minutes | `causal_reads._avoided_overteaching_minutes`: sum minus mean of the repair classes' `expected_minutes`, default 8.0 each (`:922-927`) | repository (diagnosis receipt), fitted store as above |
| `pending_machine_checks` | ids | `machine_checks.pending_machine_checks_for_factor`, only when the cause set is probe-worthy (`:843-852`) | repository |
| `session_budget_minutes` | minutes or None | `causal_repair_status`'s argument | argument; **no caller in `src` passes it, so it is always None in production** |
| `learner_preference` | one of `probe_hard_stops.LEARNER_PREFERENCES` | `probe_hard_stops.learner_preference` (`:928-933`) | repository (preference events, session-scoped) |
| `recent_diagnostic_burden` | count | `causal_reads._recent_diagnostic_burden`: diagnostic-probe attempts among the last 10 on the learning object (`:934-942`) | repository, fitted store (window) |
| `repository`, `parameters` | | `resolve_causal_probe_parameters(repository)` (`:668`), passed in | fitted store `causal_probe_policy` (nothing writes it: the defaults serve, `lifecycle` `heuristic_default`) |

### 0.2 Each line of `decide_probe`, classified

| Base lines | What | Class |
|---|---|---|
| 430 | resolve the parameters (repository read when none are given) | bookkeeping |
| 431-432 | distinct non-empty repair classes, sorted; more than one? | fact |
| 433-437 | expected avoided minutes = max(0, avoided) × clip(change) × clip(gain) | fact |
| 438-450 | the decision's carried fields: classes, `high_priority_need` = `blocks_branch_specific_repair` = different and not covered, expected avoided, burden floored at 0, machine-check ids; the parameter manifest | fact; manifest bookkeeping |
| 451-456 | common cover → `skip_common_repair` | verdict (on a fact) |
| 457-462 | one class → `skip_action_equivalent` | verdict (on a fact) |
| 463-468 | pending machine checks → `defer_machine_checks` | hard stop |
| 469-474 | preference in decline / teach_now / no_more_diagnostics → `defer_learner_preference` | hard stop |
| 475-481 | recent burden ≥ `recent_diagnostic_limit` (2; negative disables) → `defer_recent_burden` | verdict (a hand-set count rule, which goes with the verdict at G2: strategy §2.10, G2 review "Scope") |
| 482-490 | budget given and below the burden **as given** (not floored) → `defer_session_budget` | hard stop (the probe does not fit) |
| 491-496 | gain ≤ `minimum_expected_information_gain` (0.0) → `skip_no_discrimination` | verdict |
| 497-505 | change ≤ `minimum_action_change_probability` (0.0) → `skip_no_action_change` | verdict |
| 506-513 | expected avoided ≤ floored burden + `probe_value_margin_minutes` (0.0) → `skip_burden_exceeds_value` | verdict |
| 514-518 | otherwise `probe_now` | verdict |

### 0.3 Outputs and their readers

`ProbeDecision`: `decision`, `reason`, `repair_class_ids`, `high_priority_need`, `blocks_branch_specific_repair`,
`expected_avoided_overteaching_minutes`, `probe_burden_minutes`, `machine_checks_first`, `parameters` (manifest),
`decision_policy_version`.

- `_status_for_factor` reads `decision` (the verb its eight arms map onto five repair statuses, `:1004-1134`),
  `reason` (the receipt's `reason` and `RepairStatus.probe_decision_reason`) and
  `expected_avoided_overteaching_minutes` (the receipt's `inputs`, `:986-988`). It reads no other field: the receipt's
  `parameters` come from its own `probe_parameters.manifest()` and the classes from `targeting`.
- Every arm writes one `causal_probe_decision_receipts` row through `finish` (`:698-721`). Readers of that table:
  `causal_health` (`:230`), `followups` (`:1053`, `:1134`, the common-repair attach), `scoreboard` (`:1343-1348`),
  `instructional/needs` (`:283`), `router_objective/picks` (`:89-91`).
- FG1's `followup_run/router._observe` reads only `decision` (§0.4).
- Tests: `test_causal_attribution_p2` calls it directly; the rest reach it through the orchestrator.

### 0.4 FG1's call with zeros, and the readers of its log field

`followup_run/router._observe` (`:128-153`) calls `repair_class_need_for_factor`, then `decide_probe` with the gain,
the change probability, the burden and the avoided minutes all 0.0, no machine checks, preference, burden or budget,
and the repository (so the parameters are resolved again). It writes
`{"decide_probe": verb, "repair_class_ids", "repair_class_divergence", "common_repair_covers"}` as the decision's
`observational`, or `{}` and the exception. With those inputs the verb is `skip_common_repair` or
`skip_action_equivalent` when the classes settle it (both decided by real facts: those two arms come before anything
the zeros feed), and otherwise `skip_no_discrimination` (with the default parameters; `defer_recent_burden` under a
fitted limit of 0 or less), a verdict on a gain that was never computed: no instrument exists before FG1 authors one.

Readers of the field:
1. `router/plan_log.py:777` copies it into `router_decisions.detail_json.observational` (outside `snapshot_hash`'s
   inputs, so no hash reads it).
2. `followup_run/decision_view.py:103` passes the stored dict through as `details.observational` (desktop
   `FollowupPanel.tsx` and phone `RouterLine.tsx` read `details` but not this key; `git grep` finds no frontend reader).
3. `refusal_records.followup_gate_record` (`:353`, `:380`) writes `facts.value_check` = the verb (or `failed`) on
   the `followup_gate` decision record.
4. `router._card_facts` (`:156-165`) reads `repair_class_divergence` into the router card's facts (a prompt input).
5. Tests: `test_followup_router.test_the_value_checks_are_on_the_record_and_decide_nothing`,
   `test_refusal_records.test_a_value_check_that_fails_is_named_on_the_gates_record` (patches
   `causal_probe_coherence.decide_probe`), `test_followup_codex_review` (asserts `details.observational` is None when
   held), `ih2_lessons_compete_helpers` (patches `router.observational`, which `decide` does not call).

### 0.5 The two resolvers side by side

`resolve_causal_probe_parameters` (`causal_probe_coherence.py:151-186`) and `resolve_cold_probe_parameters`
(`goals/certification_cold_probe.py:248-282`), line by line: copy the defaults; no repository → the defaults; no
active fitted set for the scope → the defaults; `params = record.get("params") or {}`; for each default key present in
`params`: a bool or a non-number is invalid, a non-finite or out-of-bounds float is invalid, otherwise it replaces the
default; return `lifecycle="fitted"`, `fitted_set_id=str(record["id"])`, `invalid_keys` sorted, even when every key was
invalid. The only textual difference in the algorithm is the unused loop variable's name (`default` / `_default`). They
differ in data (scope, defaults, bounds) and in the dataclass they return (`CausalProbeParameters` with
`recent_diagnostic_limit`; `ColdProbeParameters` with `horizon_days`, `window_days`, `success_correctness`; the same
`manifest()` shape). `causal_orchestrator.resolve_orchestrator_parameters` (`:266-297`) is the same algorithm a third
time. Behaviour: identical. So they merge (§4).

## 1. What moved

| What | From (base) | To (tip) |
|---|---|---|
| The facts and hard stops of `decide_probe` | `causal_probe_coherence.py:431-450`, `:463`, `:469`, `:482-485` | `diagnosis/probe_facts.py`: `ProbeFacts` (`:27`), `probe_facts` (`:76`) |
| The verdict ladder | `causal_probe_coherence.py:451-518` | `probe_facts.py`: `settled_by_repair_classes` (`:129`, the first two arms), `probe_verdict` (`:141`) |
| `decide_probe` | `causal_probe_coherence.py:406-518` | the same name and signature at `:388`; its body resolves the parameters (`:416`), calls `probe_facts` (`:417`) and `probe_verdict` (`:429`), and builds the same `ProbeDecision` (`:430`) |
| The fitted-knob resolution | three copies: `causal_probe_coherence.py:160-186`, `goals/certification_cold_probe.py:256-282`, `causal_orchestrator.py:269-297` | `params/fitted_params.py:81` `resolve_bounded_knobs`; each named resolver keeps its signature and dataclass and passes its scope, defaults and bounds |
| FG1's logged value checks | `followup_run/router.py:128-153` (a `decide_probe` call with zeros) | the same function: `repair_class_need_for_factor`, then `settled_by_repair_classes`; `VERDICT_ABSENT_NO_INSTRUMENT` (§3) |

`probe_facts.py` imports nothing of LearnLoop (`dataclasses`, `typing` only), so G2's router can import the facts
without the 1,900-line coherence module. `ProbeDecision`, `CausalProbeParameters` and the defaults stay where they
were.

**P1, definitions.** Top-level definitions compared by AST against the base (scratch `defs_diff.py`): every definition
of the seven changed modules is identical except the ones this step meant to change: `decide_probe`,
`resolve_causal_probe_parameters` (`causal_probe_coherence`), `resolve_orchestrator_parameters` (`causal_orchestrator`),
`resolve_cold_probe_parameters` (`certification_cold_probe`), `_observe` (`followup_run/router`),
`followup_gate_record` (`refusal_records`, one added fact), and each module's imports; added:
`resolve_bounded_knobs`, `VERDICT_ABSENT_NO_INSTRUMENT` and `probe_facts.py`'s names. No definition moved unchanged,
so there is no moved body to prove identical; the split is proved by P2.

**The split, old lines to new homes.**

| Base `decide_probe` lines | New home | Body change and why |
|---|---|---|
| 430 `resolved = parameters or resolve(...)` | `decide_probe:416` | none |
| 431-432 classes, `different_repairs` | `probe_facts:92-93` | none |
| 433-437 expected avoided | `probe_facts:94-98` | none |
| 438-450 `base` fields | `ProbeFacts` fields; `decide_probe:430-440` copies them onto `ProbeDecision` | `high_priority_need` and `blocks_branch_specific_repair` were the same expression twice; now one fact, `action_relevant`, copied to both. The manifest is built after the verdict instead of before it (`manifest()` is pure) |
| 451-462 cover, one class | `settled_by_repair_classes:134-137` | none |
| 463 `if pending_machine_checks` | fact `machine_checks_pending = bool(...)` (`:110`); verdict `:156` | the truth test computed once, as a named flag |
| 469 preference in the three refusing values | fact `learner_preference_refuses` (`:111`, `REFUSING_PREFERENCES`); verdict `:158` | the set literal is a named frozenset |
| 475-476 recent burden vs limit | verdict `:160-161` | `facts.recent_diagnostic_burden`; the limit is still read only when the ladder reaches it |
| 482-485 budget below the burden as given | fact `session_budget_short` (`:114`); verdict `:163` | computed eagerly from the raw burden, as before (the floor applies only to the value comparison) |
| 491, 497-498, 506-507 the value thresholds | verdict `:165`, `:167`, `:169-171` | reads `facts.*`; thresholds read through `Thresholds.__getitem__` at the same points (a test pins that an unreached threshold is never read) |
| 514-518 `probe_now` | verdict `:173` | none |

The facts are computed eagerly where the old code reached some only after earlier arms returned. Every such
computation is a comparison or arithmetic on the declared types (`float`, `float | None`, `int`, a sequence of ids,
a preference string) and cannot raise or read anything on them; the thresholds, which could (a `values` mapping
missing a key), stay lazy.

## 2. The verdict as a function of the facts

`probe_verdict(facts, thresholds)`, first arm that applies:

1. one repair covers the plausible cause set → `skip_common_repair`;
2. one repair class (or none) → `skip_action_equivalent`;
3. hard stop: pending machine checks → `defer_machine_checks`;
4. hard stop: the learner said "not now", "teach me now" or "no more diagnostics" → `defer_learner_preference`;
5. recent diagnostic probes ≥ `recent_diagnostic_limit` (2; a negative limit disables it) → `defer_recent_burden`;
6. hard stop: the session budget, when given, is below the probe's burden → `defer_session_budget`;
7. gain ≤ `minimum_expected_information_gain` (0.0) → `skip_no_discrimination`;
8. change probability ≤ `minimum_action_change_probability` (0.0) → `skip_no_action_change`;
9. expected avoided minutes ≤ burden + `probe_value_margin_minutes` (0.0) → `skip_burden_exceeds_value`;
10. otherwise `probe_now`.

Every threshold is `CAUSAL_PROBE_POLICY_DEFAULTS` (`causal_probe_coherence.py:95-107`) through
`resolve_causal_probe_parameters`, which reads fitted scope `causal_probe_policy`; nothing writes that scope
(`cli/fit.py` writes only `fsrs_weights` and `followup_gate`, `:35`, `:129`), so the defaults always serve. The
orchestrator's input defaults (burden 1.5 minutes, 8.0 minutes per repair class, a window of 10 attempts) are the same
kind of unwritten scope (`causal_orchestrator_policy`). The session budget is never passed by any caller in `src`, so arm
6 is reachable only from tests.

## 3. FG1's log field: what it is now, and its readers

`_observe` still reads `repair_class_need_for_factor` and writes `repair_class_ids`, `repair_class_divergence` and
`common_repair_covers` as before. Of the verdict:
- where the repair classes settle the question (a common cover, or at most one class), `decide_probe` is
  `skip_common_repair` or `skip_action_equivalent`, the same bytes as before: those arms read only facts that exist
  at this point;
- otherwise `decide_probe` is absent and `decide_probe_absent` is `no_instrument_before_authoring`: the remaining arms
  read the instrument's gain, change probability and burden, and FG1 authors its probe after this decision. The old
  value there, `skip_no_discrimination`, was a verdict on a gain no one computed.

It no longer calls `decide_probe` or resolves the probe-policy parameters. Readers, on old and new rows:
1. `router/plan_log.py:777` copies the dict into `router_decisions.detail_json.observational`: old rows keep their
   `decide_probe`; new divergent rows carry `decide_probe_absent` instead. No hash covers the field.
2. `followup_run/decision_view.py:103` passes the stored dict through unchanged; no frontend reads the key.
3. `refusal_records.followup_gate_record`: `facts.value_check` is still the verdict when there is one (or `failed`);
   the new `facts.value_check_absent` carries the reason. Old records are stored rows and are not rebuilt.
4. `router._card_facts` reads `repair_class_divergence`, which did not change, so the card's bytes do not move.

On the recorded journeys (§6, P2) FG1 observed 135 times: 131 divergent observations change from
`skip_no_discrimination` to the absence, 2 `skip_action_equivalent` and 2 failures (`ValueError`, `LookupError`) are
unchanged.

## 4. The two resolvers

They do not differ in behaviour (§0.5), and neither does `resolve_orchestrator_parameters`: the algorithm is now
`params/fitted_params.resolve_bounded_knobs`, which returns the dataclass's keyword arguments. The three named
functions stay, each one call, because ten callers use their typed results (`ColdProbeParameters.horizon_days`,
`CausalProbeParameters.recent_diagnostic_limit`, ...). Proof: 342 synthetic fitted records (no repository, no
active set, empty and `None` params, an integer id, an unknown key, and each knob and all knobs at once set to each of
24 values: bools, ints, floats at and past every bound, NaN, ±inf, a string, a list, a mapping) through all three
resolvers, every manifest, property and value type dumped: 1,026 cases, byte-equal at base and tip (sha256
`7baf3c1978e5...`).

## 5. Measurements

**`probe_facts` per candidate:** 1.7 µs (median over the 49 distinct recorded inputs, 2,000 calls each; maximum
1.73 µs). The P-draw harness's synthetic journeys make no probe decision (no miss with rival causes; their tables
name the probe tables only in the catalog), so the inputs are those the diagnosis journeys and causal suites made
(§6, P2).

**The probe rollout per branch** (E5's replay loader, scratch `p_time.py`; six `evaluate` calls recorded on the P-draw
`both` journey at the base, 6 or 7 topics each, at the recorded 8 draws; one `_Model` per call, timed after a warm-up,
median of 5; the times at 16 draws are 3-8% higher):

| Rollout piece | Median (range over the six calls) |
|---|---|
| a probe action's whole value (`_Model.value`: the probe segment, a choice per result, then the none and repair branches on the true path) | 227 ms (58-294) |
| one result branch (`_probe_choice`: the post-probe belief world, the none and repair branches with their tails) | 77 ms (19-98) |
| one true-path branch (a repair action's value: the repair and the tail) | 38 ms (10-49) |
| building the belief world (once per model) | 1.3 ms |

A probe's value is about six tails today: two result branches (success, miss) of two tails each, and two true-path
tails. **Branching per hypothesis** (G2's `π_Q` per hypothesis; not built) replaces the two results with one branch
per locked hypothesis. Locked sets on the recorded journeys: 3 hypotheses in 337 of 385, 4 in 40, 5 in 2, 6 in 5, 2 in 1
(the open arm included). Two bounds per candidate per batch, at the median call:
- if each hypothesis needs a whole probe rollout of its own (its own result distribution and its own repair): H × 227
  ms, so 0.68 s at H = 3 and 1.36 s at H = 6;
- if the result choices stay shared (the choice depends on the result alone, as today) and each hypothesis adds only
  its own true-path none and repair branches: 227 + (H − 1) × 2 × 38 ms, so 0.38 s at H = 3 and 0.61 s at H = 6.
The numeric policy evaluates every candidate in each batch, so a probe candidate adds this to each batch it is in.

## 6. Proofs

Scratch: the recording plugin `g1_record.py`, `p2_probe.py`, `p2_resolve.py`, `cmp_rec.py`, `cmp_orch.py`,
`pdraw.py` (E5's, work path changed and `value` → `rollouts` in its record option), `p_time.py`, `defs_diff.py`,
`cycle_measure.py`. **P2's synthetic equality is this step's proof; the fresh-copy rebuild (P-shadow) is the
orchestrator's.** No owner vault or copy was opened.

**P2. Equality on recorded inputs.** At the base, a pytest plugin wrapped `decide_probe` (in the coherence module, the
orchestrator's import and any test module's), `Repository.insert_causal_probe_decision_receipt`,
`insert_hypothesis_set` and FG1's `_observe`, and ran 42 files: the diagnosis journey golden, every `test_causal*`,
every test naming `decide_probe`, `causal_probe_decision`, `resolve_cold_probe_parameters` or
`resolve_causal_probe_parameters`, and every test reaching `causal_repair_status`, remediation or `miss_with_rivals`
(799 passed, 1 xfailed). Recorded: 230 `decide_probe` calls (133 of them FG1's zero calls), 49 distinct inputs, 109
receipt rows in 76 tests, 385 hypothesis sets, 135 FG1 observations.
- `decide_probe` on the 49 distinct inputs (with their resolved parameters), on a synthetic grid of 40,320 inputs
  (five threshold sets × every ladder input at its boundaries; then the value terms over gains, change probabilities,
  burdens, avoided minutes and budgets including negatives, values above 1 and NaN), and 200 with no parameters (the
  resolver path): base `src` (a `git archive` of `2e3de890ff`) and tip **byte-equal**, 40,569 results, sha256
  `1ebf13c7af32...`. Verdicts on the recorded inputs: `skip_common_repair` 34, `probe_now` 5, `skip_no_discrimination`
  4, `skip_action_equivalent` 3, `defer_learner_preference` 2, `defer_machine_checks` 1 (6 of the 10 arms); the grid
  reaches all ten (`skip_common_repair` 14,400, `skip_action_equivalent` 9,600, `defer_session_budget` 3,216,
  `defer_recent_burden` 2,832, `skip_no_discrimination` 2,484, `defer_machine_checks` 2,400, `skip_no_action_change`
  2,112, `defer_learner_preference` 1,440, `skip_burden_exceeds_value` 939, `probe_now` 897).
- The same 42 files rerun at the tip with the plugin: the 109 receipt rows are **equal test by test** after
  normalizing ids (ULIDs and content ids, by order of first appearance in each test) and wall stamps; the 97
  orchestrator `decide_probe` calls (230 minus FG1's 133) are equal test by test in inputs, resolved parameters and
  result; hypothesis sets equal (385). Control: a second base run compared with the first under the same
  normalization is equal in every one of these, and differs, as the tip does, only in 12 tests' wall-clock
  `created_at` when stamps are not normalized.
- The resolvers: §4.

**P3.** `tests/test_diagnosis_journey_golden.py` and the causal suites pass. The golden moves in one line, the
`fg1_ask_now` case's `followup_gate` record: `"value_check": "skip_no_discrimination"` becomes
`"value_check_absent": "no_instrument_before_authoring"`, the field §3 replaces (rewritten with the golden's own
write switch; nothing else in the file changed). **P-draw** on the ten scenarios (`both`, `coin`, `llm_fails`,
`llm_fails_ih5_off`, `no_models`, `guard`, `evidence`, `offers`, `contest`, `early`; 31 runs): every table, prompt,
Decider call and `why --json` **byte-equal** at base and tip, with the decision path's connection opens and
statements equal (`both` 57 / 436, `no_models` 74 / 552, `early` 34 / 264, as E5 recorded). Recording `evaluate`'s
inputs for §5 left `both`'s output byte-equal.

**P4.** `tests/test_identity_pins.py` and `tests/pinned_draws.py` are not in the diff, and the pins pass with nothing
written (§8).

**P5.** Largest import component 84 → 84, modules in a cycle 220 → 220, the same members (untracked files included).
`probe_facts` is in no cycle. No file with a ceiling changed; `causal_probe_coherence.py` 2,004 → 1,926 lines,
`causal_orchestrator.py` 1,149 → 1,128, `certification_cold_probe.py` 1,958 → 1,937.

**P6.** `tests/test_probe_facts.py` (new; fails at the base, where the module does not exist): each fact on a case
worked by hand (classes `["r:b", None, "r:a", "r:a", ""]` → `("r:a", "r:b")`; 10 avoided minutes × 0.8 × 0.5 = 4.0),
the clips and floors, action relevance, each hard stop (machine checks, each refusing preference and two that do not
refuse, the budget against the raw burden including negatives), the stops' order, the two arms the classes settle,
the ladder's order on facts, and that a threshold the ladder does not reach is never read.

## 7. Tests added, changed and ported

- Added: `tests/test_probe_facts.py` (P6).
- `test_followup_router.test_the_value_checks_are_on_the_record_and_decide_nothing`: asserted that FG1's record
  carried *a* verdict (`seen["decide_probe"]`) on a divergent factor, which was the zero-input verdict. Now asserts
  that it carries none and names the absence (`decide_probe_absent == VERDICT_ABSENT_NO_INSTRUMENT`): stronger, and
  the behaviour this step changes. Its `repair_class_divergence` assertion is unchanged.
- `test_refusal_records.test_a_hard_refusal_and_no_plan_each_leave_the_gates_record`: one assertion added (the
  gate's record names `value_check_absent` and has no `value_check` on the divergent no-plan journey).
- `test_refusal_records.test_a_value_check_that_fails_is_named_on_the_gates_record` (ported): it made the value checks
  fail by patching `causal_probe_coherence.decide_probe`, which FG1 no longer calls. It now patches
  `repair_class_need_for_factor`, the checks' one remaining read, and fails it only when the router calls it:
  commissioning reads the same function in the same journey, and failing it there changed the journey (two fewer
  hypothesis sets than at the base, seen in P2's tip run before this fix). Its assertions are unchanged.
- No other test changed; `ih2_lessons_compete_helpers` still patches `router.observational`, which `decide` never
  called before or after.

## 8. Gate

Targeted tests at the tip of the source commits: 988 files (the 984 `scripts/affected_tests.py --files` selects from
the changed files, every test naming `decide_probe`, `probe_facts`, `causal_probe_decision`,
`resolve_cold_probe_parameters` or `resolve_causal_probe_parameters`, P2's 42 files, `test_identity_pins`,
`test_retired_config_identities`, `test_effective_defaults_golden`, `test_cli_help_snapshot`,
`test_structure_ratchets`, `test_diagnosis_journey_golden`), in 17 chunks of at most 60 at `-n 2`,
`-m "not arc_close"`, each in a 5 GB scope: 24,891 passed, 0 failed. Alone at `-n 1`: `test_architecture` 18
passed, `test_test_layout` 3 passed. `lint-imports --no-cache` 43 kept, 0 broken; `ruff check` clean;
`check_gate_partition` 31,196 + 65 = 31,261; the vault validators pass (the desktop catalog reported `_generated.md`
stale before the regeneration, which is what the regeneration is for). Identity pins pass with nothing written; the
structure golden is not raised (no ratcheted number rose). No run was killed for memory.

## 9. What G2 should know

- **The candidate's facts.** `ProbeFacts` is what the diagnostic layer can hand the router for a probe on the repair
  lane: classes, action relevance, the gain and change probability (shares, not nats), expected avoided minutes,
  burden minutes, recent probe count, and the hard stops. For the router's own value it still needs what the
  strategy lists and `ProbeFacts` does not hold: the locked set, P(result | h) per hypothesis (the blind bundles'
  predictions; today only their pairwise separability reaches the facts), and the repair per hypothesis
  (`_repair_class_by_hypothesis` in the orchestrator). Those are reads, not new computations.
- **What stays a hard stop:** pending machine checks, the learner's preference, the session budget (unused in
  production today), the episode conflict (in the orchestrator and in `hard_refusal`, not in `probe_facts`), and an
  unavailable or unreviewed instrument (the orchestrator's `blocked_pending_review` arms). What goes with the verdict:
  the recent-burden count rule (2), the three value thresholds (all 0.0 and never fitted), and the class arms as
  verdicts (the class facts stay; `followup_run/lanes.py`'s rival count stays the rule for which lane exists).
- **The two stop orders** still differ: `decide_probe` checks machine checks before preference, `hard_refusal`
  preference first (`probe_hard_stops`' docstring). `ProbeFacts.hard_stops` lists them in the verdict's order; a
  single order is G2's choice. Ledger row K9-9 (the empty learning-object id in the two conflict checks) is due "with
  G1 ... or by the close of the K9 package"; this brief did not include it and it is untouched here (§11).
- **The card.** FG1's card carries no probe facts: its decision comes before an instrument exists, so there are none
  to carry, and adding any line would move the card's bytes (E7's check). The repair lane has no router card today.
  G2 adds the facts to the probe candidate's card under its successor.
- **The branching cost** (§5): 0.4 to 0.7 s per probe candidate per batch at three hypotheses, 0.6 to 1.4 s at six.

## 10. Where an "answer was exposed" fact attaches (ledger G3-1, not fixed here)

The exposure that matters for G3-1 happens after the probe is chosen and before or while it is answered, so it is
not a fact `probe_facts` can see: its inputs end at the decision. The fix attaches at the evidence step:
`probe_evidence._presentation_contamination` (`diagnosis/probe_evidence.py:181-193`) takes `attempt_type`,
`hints_used` and `tutor_contaminated`; an `answer_exposed` input there, computed by the same checks the
discriminating observation already runs (`causal_discrimination.py:161-181` for pre-answer workflow exposure,
`:249-280` for the reveal ledger), makes the observation contaminated, so its weight drops to
`contaminated_evidence_weight` and it cannot qualify for completion (`:613-640`). That is one argument and one
contamination key, under an algorithm tag. A second, smaller use belongs to G2: when the router's WAIT arm releases
feedback before the probe (the strategy's G2 review, "Timing"), the exposure is known before the decision, and
G2 can add it to `ProbeFacts` as a hard stop.

## 11. Open items

- K9-9 (open, due with G1 or at the K9 close): not in this brief; left for the orchestrator to schedule.
- P-shadow on a fresh private copy at base and tip: the orchestrator's.

Implementer: one Opus session, no subagents; token use not available to the implementer.
