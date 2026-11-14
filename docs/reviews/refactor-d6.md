# Refactor D6: constant gates in the rest of the code, and the version sets

Step D6 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d6-constant-gates-rest`, based on main `a4bd9f2b77` (D4, D5 and D5 part 2 landed; the floor `OLDEST_SUPPORTED = mvp-0.58` is enforced at every door, the head is `mvp-0.59`). Structure track: no served or persisted value changes for a vault at or above the floor. The method is D4's, D5's and D5 part 2's (`docs/reviews/refactor-d4.md`, `refactor-d5.md`, `refactor-d5b.md`).

## 1. Step 0, before any deletion

### (a) The count

`scripts/refactor_measures.py` at the base, floor `mvp-0.58`: **61 gate sites** (`x in *_VERSIONS` / `not in`) in the four packages, **54 constant at the floor, 7 varying**. The 7 varying sites all test `FACET_BELIEF_FIX_VERSIONS` or its alias `FACET_BELIEF_CORRECTION_VERSIONS` (`mvp-0.59` only, the facet-belief successor): `learner/facet_state_reader.py:56`, `:82`, `:155`, `:442`, `:504`, `ops/doctor.py:1612`, `router_objective_switches.py:490`. They vary because the set starts above the floor: a vault at `mvp-0.58` takes the predecessor branch, one at `mvp-0.59` the successor's. They are live branches and stay.

The classifier sees only `in` tests whose right side is a name ending `_VERSIONS`. A read of every use of a version set and of every tag constant outside `algorithm_versions.py` (names, function-local imports included; there is no `importlib` or string dispatch of either) finds three more sites it does not count: `field/outcomes.py:290` and `:579` (`version in (P0_ALGORITHM_VERSION, *P0_SUCCESSOR_VERSIONS)`, a tuple), and `placement/report.py:212-214` (an SQL `IN` over `PLACEMENT_VERSIONS`). No other code compares a tag: `attempts/measurement_corrections.py:243` compares the vault's tag with an argument (D4 §1(c)), `ops/upgrades.py:245`, `:273` compare it with the upgrade's own target, and nothing orders tags by `SUCCESSOR_CHAIN.index` outside `ops/upgrades.py`.

### (b) The replay question

Every site below except G4, G34 and R1 reads **the vault's current tag** (`vault.config.algorithms.algorithm_version`, or the same through `getattr` on a duck-typed config): below the floor it is dead whatever tag a replayed row was written under. Where a vault's tag can come from is unchanged since D4 §1(b), D5 §1(b) and D5 part 2 §1(b), re-read at this base: `load_vault` refuses a vault below the floor and one whose `learnloop.toml` names no tag (ADR-019); doctor, the MCP server's and phone host's attach, and journals below the floor are refused the same way; a shadow rebuild's forced tag is refused below the floor (`shadow_rebuild.build_candidate_config`); `learnloop upgrade` sets the tag to the table's links, which start at the floor; the harnesses that build their own vault below the floor (`learnloop goldenpath bootstrap`, `learnloop recall-calibration`) are refused by it (D-24). Configs built in code (`LearnLoopConfig()`, tag `mvp-0.6`): in production only `substrate/activities._algorithm_version(None)` (a stamp, D-23) and `params/parameter_registry` (numeric leaves) build one; none reaches a gate here. The doctor, the shadow rebuild and replay read every site below through the loaded vault's config, never a row's tag.

**A config an owner vault could hold.** Every class (b) site keeps its kill switch, so a vault that sets one keeps that switch's off-branch; the tag half is all that goes. No site reads a config key that only an old tag's vault could hold.

**A tag this code does not know** (D-31): before this step every gate here reads it as below its tag. §5 refuses it at the door.

**The three row readers (class (c))**: G4 compares a stored router decision's own `algorithm_version` (a lesson offer drawn before `mvp-0.55` keeps its old reading: no `offer_shown` event existed), G34 the tag stored in a same-cause judgment's `rationale` (strategy §2.6 names it), R1 the stored `derived_state_rebuilds.algorithm_version` of each rebuild (the placement report's "placement began" instant is the first rebuild at a placement tag). Each set they compare against stays.

### (c) Every site

Classes as D4: **(a)** a pure tag gate: the gate and its dead branch go. **(b)** tag and kill switch: only the tag half goes; the switch and its off-branch stay for D7. **(c)** a reader of stored rows by shape, a marker or a row's own stored tag: kept. **(d)** kept, with the reason.

Line numbers are the base's (`a4bd9f2b77`). "Constant" is at `mvp-0.58` (every set at a constant site holds both `mvp-0.58` and `mvp-0.59`, checked by importing them).

| # | site | set | constant | dead branch (below the tag) | class |
|---|---|---|---|---|---|
| G1 | `daily_plan/engine.py:157` `plan_active` | `DAILY_PLAN_VERSIONS` | yes | Today without the finite plan | (b): `plan.enabled` |
| G2 | `daily_plan/engine.py:225` `reading_path_plan_active` | `READING_PATH_PLAN_VERSIONS` | yes | the plan's reading block in the predecessor's order | (b): `reading_paths.plan_uses_path` (and `reading_paths.enabled`) |
| G3 | `daily_plan/engine.py:246` `deliverable_plan_active` | `DELIVERABLE_PLAN_VERSIONS` | yes | RW7b's per-book reading | (b): `curriculum.plan_uses_path`, `curriculum.enabled` |
| G4 | `daily_plan/lesson_offer.py:251` `never_on_screen` | `FAILURE_SHARE_VERSIONS` on the **decision row's stored** `algorithm_version` | not a vault tag | an offer drawn before `mvp-0.55` reads drawn-as-shown | (c) |
| G5 | `daily_plan/lesson_suggestion.py:111` `suggestions_enabled` | `LESSON_SUGGESTIONS_VERSIONS` | yes | Today never suggests a lesson | (b): `router.lesson_suggestions.enabled` |
| G6 | `daily_plan/lesson_suggestion.py:117` same | `TEACHER_VERSIONS` | yes | lessons cannot open, so no suggestion | (b): `teacher.enabled` |
| G7 | `daily_plan/lesson_suggestion.py:495` `_target` | `ROUTER_MIXTURE_VERSIONS` | yes | `router.mode = "mixture"` draws the card by the staged tie-break | (b): `router.mode` |
| G8 | `daily_plan/policy.py:43` `router_active` | `ROUTER_STAGED_FRAME_VERSIONS` | yes | Today as `mvp-0.22` (no router) | (b): `router.enabled` |
| G9 | `daily_plan/policy.py:57` `mixture_active` | `ROUTER_MIXTURE_VERSIONS` | yes | `mixture` serves as `staged` | (b): `router.mode` |
| G10 | `diagnosis/probe_robust.py:60` `use_robust_probe` | `P0_PROJECTION_VERSIONS` | yes | the legacy point probe path: no calibration channel pinned at an episode's open, instruments valued as ordinary items (`below_robust_cutover`), no coarse-schema mapping of a probe outcome | (a) |
| G11 | `diagnosis/remediation.py:1131` `cold_retry_reschedule_active` | `COLD_RETRY_RESCHEDULE_VERSIONS` | yes | no fresh cold retry after help | (b): `practice.reschedule_cold_after_assist` |
| G12 | `diagnosis/text_gaps/actions.py:481` `sooner_check_active` | `LEARNER_TEXT_GAP_VERSIONS` | yes | no sooner check | (b): `learner_text_gaps.enabled`, `.sooner_check_enabled` |
| G13 | `diagnosis/voi_stopping.py:243` `voi_stopping_active` | `VOI_STOPPING_VERSIONS` | yes | the four count caps | (b): `voi_stopping.enabled` and the site's sub-switch |
| G14 | `diagnosis/voi_stopping.py:262` `probe_lane_reads_diagnosis` | `VOI_STOPPING_VERSIONS` | yes | the probe lane reads raw events | (b): `diagnosis.probe_lane_reads_diagnosis` |
| G15 | `placement/report.py:89` `placement_report` | `PLACEMENT_VERSIONS` | yes | the manifest's `placement_version` is false | (a): the field keeps its value, `True` |
| R1 | `placement/report.py:212` same (SQL) | `PLACEMENT_VERSIONS` over **stored** `derived_state_rebuilds.algorithm_version` | not a vault tag | — | (c) |
| G16 | `placement/state.py:139` `placement_active` | `PLACEMENT_VERSIONS` | yes | no placement | (b): `placement.enabled` |
| G17 | `placement/state.py:159` `diagnosis_can_arrive` | `DIAGNOSIS_SPLIT_VERSIONS` | yes | no live diagnosis can land, placement decides by today's rule | (b): `diagnosis.split_enabled` |
| G18 | `placement/state.py:193` `gap_sooner_checks_active` | `LEARNER_TEXT_GAP_VERSIONS` | yes | sooner checks not read | (b): `learner_text_gaps.enabled`, `.sooner_check_enabled` |
| G19 | `placement/state.py:227` `unevidenced_return_active` | `UNEVIDENCED_RETURN_VERSIONS` | yes | the placement hole | (b): `placement.unevidenced_return` |
| G20 | `field/signals.py:474` | `LEARNER_TEXT_GAP_VERSIONS` | yes | the F11 grounded rule as at `mvp-0.15` | (b): `learner_text_gaps.enabled`, `.sooner_check_enabled` |
| G21 | `field/workbench_signals.py:99` `workbench_field_signals_live` | `WORKBENCH_FIELD_SIGNALS_VERSIONS` | yes | no workbench signals | (b): `workbench.field_signals_enabled` |
| G22 | `field/outcomes.py:290` (not counted: a tuple) | `P0_ALGORITHM_VERSION`, `P0_SUCCESSOR_VERSIONS` | yes | an attempt with no interpretation keeps its raw attempt-type mass | (a) |
| G23 | `field/outcomes.py:579` (not counted) | same | yes | the same, in the outcome ledger's rows | (a): the tag half of the `or`; `interpretation is not None` is a shape and its branch is the kept one |
| G24 | `goals/certification_cold_probe.py:584` `_unverified_imports` | `SOURCE_REFERENCE_GATE_VERSIONS` | yes | unverified imports are not left out | (a) |
| G25 | `goals/exam_pool.py:314` same | `SOURCE_REFERENCE_GATE_VERSIONS` | yes | same | (a) |
| G26 | `instructional/needs.py:63` `source_first_active` | `SOURCE_FIRST_NEEDS_VERSIONS` | yes | generation first | (b): `source_service.enabled`, `.source_first_needs` |
| G27 | `instructional/reader_digest.py:719` `_not_planned_reason` | `READER_FOLLOWUPS_VERSIONS` | yes | the reason written is `below_followups_successor` | (a): always `followups_off`; nothing in `src/` or the desktop reads the stored reason back |
| G28 | `instructional/reader_followups.py:164` `followups_enabled` | `READER_FOLLOWUPS_VERSIONS` | yes | nothing planned | (b): `followups.enabled` |
| G29 | `content/proposals/patches.py:648` `_refuse_learnable_on_legacy` | `CANONICAL_STATE_VERSIONS` | yes | a learnable map's apply is refused | (a) |
| G30 | `content/proposals/patches.py:1111` `_reject_unregistered_facets` | `CANONICAL_STATE_VERSIONS` | yes | an unregistered facet is accepted | (a) |
| G31 | `serve_eligibility.py:971` `help_converts_active` | `ONE_ASK_VERSIONS` | yes | the predecessor's help rules | (b): `ask.cold_help_converts` |
| G32 | `serve_eligibility.py:989` `decision_active` | `ELIGIBILITY_DECISION_VERSIONS` | yes | every serve path as `mvp-0.26` | (b): `eligibility.enabled` |
| G33 | `decider_judgments.py:113` `decider_active` | `DECIDER_TIER1_VERSIONS` | yes | every serving judgment on its LLM path | (b): `decider_routes.<task>` |
| G34 | `substrate/recurrence_groups.py:442` `_source_judgments` | `DECIDER_TIER1_VERSIONS` on the **judgment's stored** tag | not a vault tag | — | (c) |
| G35 | `adaptive_difficulty/successor.py:48` `successor_active` | `ADAPTIVE_DIFFICULTY_VERSIONS` | yes | AD off | (b): `adaptive_difficulty.enabled` |
| G36 | `adaptive_difficulty/successor.py:97` `lesson_opportunities_on` | `LESSON_OPPORTUNITY_VERSIONS` | yes | no lesson opportunities | (b): `adaptive_difficulty.lesson_opportunities` |
| G37 | `data_capture/gates.py:28` `serving_on` | `DATA_CAPTURE_VERSIONS` | yes | `mvp-0.43`'s serving, `router_outcomes_v2` | (b): `data_capture.serving` |
| G38 | `figures/prefetch_ledger.py:71` `pressed_waits_on` | `FIGURE_WAIT_VERSIONS` | yes (the set starts at the floor) | `prefetch_decision_v1` | (d): `figures/` is a parallel lane's (the brief: stay out) |
| G39 | `followup_serve/gates.py:34` `generate_and_serve_on` | `FOLLOWUP_SERVE_VERSIONS` | yes | FG1 off | (b): `followup.generate_and_serve` |
| G40-G47 | `router_objective_switches.py:72` `_at_tag`, `:161` `objective_tag`, `:191` `calibration_tag`, `:250` `learned_tail_tag`, `:266` `followups_tag`, `:353` `lesson_offers_tag`, `:377` `failure_share_tag`, `:460` `slip_gap_tag` | `INTERVAL_FACTOR_`, `ROUTER_OBJECTIVE_`, `ROUTER_CALIBRATION_`, `ROUTER_LEARNED_TAIL_`, `ROUTER_FOLLOWUPS_`, `LESSON_OFFERS_`, `FAILURE_SHARE_`, `SLIP_GAP_VERSIONS` | yes | each successor's predecessor | see §1(d) |
| G48 | `scheduling/intent/serving.py:126` `intent_enabled` | `INTENT_VERSIONS` | yes | no intent | (b): `intent.enabled` |
| G49 | `scheduling/scheduler.py:1171` `probe_ties_admitted` | `PROBE_TIE_VERSIONS` | yes | probe ties excluded | (b): `router.probe_tie_admission` |
| G50 | `scheduling/scheduler.py:1327` (the trace's config snapshot) | `VOI_STOPPING_VERSIONS` | yes | the snapshot leaves out `voi_stopping` | (a) |
| G51 | `teacher/service.py:108` `lessons_active` | `TEACHER_VERSIONS` | yes | no lesson opens | (b): `teacher.enabled` |
| G52 | `teacher/service.py:113` `require_active` | `TEACHER_VERSIONS` | yes | `teacher_unavailable` ("needs this vault upgraded") | (a) |
| G53 | `teacher/te2.py:60` `on` | `TEACHER_PROBES_VERSIONS` | yes | TE1's lessons | (b): `teacher.enabled`, `teacher.probes` |
| G54 | `learnloop_sidecar/handlers/serializers.py:358` | `CANONICAL_STATE_VERSIONS` | yes | no assessment contract snapshotted at serve | (a) |
| G55 | `learnloop_sidecar/handlers/workbench.py:156` | `CANONICAL_STATE_VERSIONS` | yes | same, for a bound workbench session | (a) |
| G56 | `learnloop_sidecar/request_origin.py:87` `phone_probes_on` | `PHONE_PROBES_VERSIONS` | yes | the phone is V2's | (b): the host's `phone_probes` (on the request origin) |

By the strategy's packages: `daily_plan/` 9 (the strategy said 8; G4 is a row reader), `diagnosis/` 5 (G10-G14; the strategy's 4 left out G14 or G10), `placement/` 5 plus R1 (the strategy's 4 left out G15), `field/` 2 counted plus G22, G23, `goals/` 2, `instructional/` 3, `content/proposals/` 2, `serve_eligibility.py` 2, `decider_judgments.py` 1, `substrate/recurrence_groups.py` 1 (G34, kept). The other 22 counted sites are in packages the strategy did not list (`adaptive_difficulty/`, `data_capture/`, `figures/`, `followup_serve/`, `router_objective_switches.py`, `scheduling/`, `teacher/`, the sidecar).

### (d) The router objective's tag predicates (G40-G47) and the identity pins

The eight `*_tag` predicates of `router_objective_switches.py` are not only gates: `daily_plan/objective_chooser.objective_settings` and `generator_now`, and `router_objective_switches.followup_switch_snapshot` / `followup_generator_switches`, put a key into the prefetch boundary identity, the numeric policy's seed and RO6's generator key only at the tag ("below the tag the key keeps its predecessor's bytes"). `tests/test_identity_pins.py` pins those identities for two configs: a new vault's (`init`, the head) and `legacy` (a config whose file names no tag, so the in-code default `mvp-0.6`). Deleting a tag half changes nothing at `init`, but moves the `legacy` pins.

Measured, not argued: each version set in turn was widened to hold `mvp-0.6`, `mvp-0.7` and `mvp-0.8` (every gate on it then takes its successor branch for the `legacy` config, as it would with the tag half gone) and the pins were run; the base code otherwise. All sets widened at once move four pins: `C3.boundary.legacy`, `C4.objective_settings.legacy`, `C4.switches.legacy`, `C5.legacy`. One set at a time (every set alphabetically up to `P0_PROJECTION_VERSIONS`, then the router, teacher, lesson and data-capture sets with `-k legacy`), exactly three sets move any:

| set | pins that move | through |
|---|---|---|
| `FAILURE_SHARE_VERSIONS` | `C3.boundary.legacy`, `C4.objective_settings.legacy` | `failure_share_tag` in `objective_settings` (IH5's, IH2's and IH4's keys) |
| `ROUTER_FOLLOWUPS_VERSIONS` | `C3.boundary.legacy`, `C4.switches.legacy`, `C4.objective_settings.legacy`, `C5.legacy` | `followups_tag` in `followup_switch_snapshot` and `followup_generator_switches` |
| `SLIP_GAP_VERSIONS` | `C3.boundary.legacy`, `C4.objective_settings.legacy` | `slip_gap_tag` in `objective_settings` and the generator switches |

So **G44 (`followups_tag`), G46 (`failure_share_tag`) and G47 (`slip_gap_tag`) are class (d)**: deleting their tag half moves an identity pin, and the brief's rule is to stop that deletion. What the pins hold there is the bytes of a key built from a config no vault can open with (a `learnloop.toml` without a tag is refused at every door), so nothing served depends on them; whether to drop the `legacy` arm of C3-C5 (a deliberate pin change) or keep the three predicates until D7 removes the switches they guard is the orchestrator's call (§9). **G40 (`_at_tag`), G41 (`objective_tag`), G42 (`calibration_tag`), G43 (`learned_tail_tag`) and G45 (`lesson_offers_tag`) are class (b)**: each pairs with its successor's switches (`scheduler.surprise.remove_interval_factor`, `router_objective.available_at_reads`, `.self_report_not_validated`; `router_objective.enabled`; RO5's rates and `fitted_models`; `learned_tail`; `router.lesson_suggestions.in_objective` with TE1b's switches), and no pin moves.

### (e) Totals

Of the 54 constant sites: **(a) 11** (G10, G15, G24, G25, G27, G29, G30, G50, G52, G54, G55), **(b) 37** (G1-G3, G5-G9, G11-G14, G16-G21, G26, G28, G31-G33, G35-G37, G39-G43, G45, G48, G49, G51, G53, G56), **(c) 2** (G4, G34), **(d) 4** (G38 the figures lane, G44, G46, G47 the identity pins). Outside the classifier's count: G22 and G23 (a), R1 (c). The 7 varying sites stay.

## 2. The version sets and tag constants

`algorithm_versions.py` at the base: 1,287 lines, **51 version sets** (`*_VERSIONS`; the classifier counts 52 with `facet_state_reader`'s alias `FACET_BELIEF_CORRECTION_VERSIONS`), 53 tag constants (50 chain members, `LEGACY_ALGORITHM_VERSION`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`), `SUCCESSOR_CHAIN`, `successors_from`, `OLDEST_SUPPORTED`, `LATEST_ALGORITHM_VERSION`. Who reads each after the gates of §1 go (searched as names over `src/`, `tests/`, `scripts/`, the vault's `_scripts/` and `apps/`; no string dispatch names any):

**Sets kept (7):**

| set | read by | why it stays |
|---|---|---|
| `DECIDER_TIER1_VERSIONS` | G34 | a stored judgment's tag is compared against it (class (c)) |
| `PLACEMENT_VERSIONS` | R1 | stored `derived_state_rebuilds.algorithm_version` rows (class (c)) |
| `FAILURE_SHARE_VERSIONS` | G4 (c), G46 (d) | a stored decision's tag; the identity pins |
| `ROUTER_FOLLOWUPS_VERSIONS` | G44 (d) | the identity pins |
| `SLIP_GAP_VERSIONS` | G47 (d) | the identity pins |
| `FACET_BELIEF_FIX_VERSIONS` | the 7 varying gates (and stored uncertainty rows' tags, D5 part 2 §1(b)) | varies at the floor |
| `FIGURE_WAIT_VERSIONS` | G38 (d) | `figures/` is a parallel lane's |

**Sets deleted (44):** nine already read by no gate at the base (D4/D5 removed their sites): `STUCK_PROMPT_`, `RECURRENCE_GROUP_`, `ROUTE_RULES_`, `METHOD_EXPLICIT_`, `REGRADE_CONTRACT_`, `CLAIM_FIXES_`, `REPLAY_LEDGER_`, `SUPERSEDED_CLAIMS_`, `HELP_FOLD_ATTACH_VERSIONS` (tests only); and 35 whose last gate goes in §1: `DIAGNOSIS_SPLIT_`, `P0_SUCCESSOR_`, `P0_PROJECTION_`, `CANONICAL_STATE_` (with `learner/assessment_contracts`' re-exports of the last three), `DAILY_PLAN_`, `PROBE_TIE_`, `LEARNER_TEXT_GAP_`, `SOURCE_REFERENCE_GATE_`, `SOURCE_FIRST_NEEDS_`, `VOI_STOPPING_`, `ROUTER_STAGED_FRAME_`, `ROUTER_MIXTURE_`, `ELIGIBILITY_DECISION_`, `INTENT_`, `ADAPTIVE_DIFFICULTY_`, `WORKBENCH_FIELD_SIGNALS_`, `READING_PATH_PLAN_`, `ONE_ASK_`, `ATTEMPT_CONTENT_STATE_` (a docstring mention only), `COLD_RETRY_RESCHEDULE_`, `READER_FOLLOWUPS_`, `DELIVERABLE_PLAN_`, `TEACHER_`, `LESSON_SUGGESTIONS_`, `DATA_CAPTURE_`, `FOLLOWUP_SERVE_`, `INTERVAL_FACTOR_`, `ROUTER_OBJECTIVE_`, `ROUTER_CALIBRATION_`, `ROUTER_LEARNED_TAIL_`, `TEACHER_PROBES_`, `LESSON_OPPORTUNITY_`, `LESSON_OFFERS_`, `PHONE_PROBES_`, `UNEVIDENCED_RETURN_VERSIONS`. No stored row is compared against any of them (the three row readers are G4, G34, R1), and none is in the upgrade table. Their test readers are each successor test's frozen-set assertion (`X_VERSIONS == frozenset({...})`, whose only subject is the set) and tests that pick a tag below a set to reach a deleted branch (§3).

**Tag constants: all 53 kept.** The 50 chain members are `SUCCESSOR_CHAIN` itself (the brief keeps the chain; the upgrade table's rows name them by it), and their comments are the record of what each tag means. `LEGACY_ALGORITHM_VERSION` is read by `learner/recall_calibration` (D-24's harness); `KM_ALGORITHM_VERSION` and `P0_ALGORITHM_VERSION` are stamps written on stored rows (`facet_state_reader`, `canonical_projection`, `p0_projection`, `probe_robust`, `grade_resolution`), so stored data names them. `successors_from`, `OLDEST_SUPPORTED` and `LATEST_ALGORITHM_VERSION` stay.
