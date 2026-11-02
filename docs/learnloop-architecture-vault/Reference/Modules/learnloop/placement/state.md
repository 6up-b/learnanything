---
title: "learnloop.placement.state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/state.py"
source_paths:
  - "src/learnloop/placement/state.py"
source_commit: "0005dbcf6f675a98a3d3b0a58a1af1fa137931e3"
source_commit_timestamp: "2026-11-01T02:20:07-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.state module"
  - "src/learnloop/placement/state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.state` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: Placement state (learner field §5.2): what is assumed known, and what happened.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py) |
| Source lines | 1552 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0005dbcf6f675a98a3d3b0a58a1af1fa137931e3` |
| Commit timestamp | `2026-11-01T02:20:07-05:00` |

## Public API

- `placement_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 130) — F2 serves only at a placement version with the kill switch on.
- `diagnosis_can_arrive(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 139) — Whether a queued live diagnosis can land now (``split_grading_active``).
- `initial_probes_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 159) — Whether state sync opens an opening diagnostic episode per new LO.
- `gap_commitments_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 170) — Created prerequisites' light commitments are read (their creation switch on).
- `gap_sooner_checks_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 182) — ``mvp-0.16``: sooner checks are read (kill switch ``sooner_check_enabled``).
- `opening_probes_ignored(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 197) — Whether unanswered opening episodes are ignored (owner decision 2026-10-12).
- `unanswered_opening_episode_ids(connection: Any, episode_ids: Iterable[str] | None=None) -> frozenset[str]` ([source](../../../../../../src/learnloop/placement/state.py), line 213) — Open opening episodes exactly as state sync left them: nothing answered, nothing adopted.
- `ignored_opening_episode_ids(vault: LoadedVault, repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/placement/state.py), line 246) — The opening episodes placement ignores right now (empty when it does not).
- `episode_ignored(vault: LoadedVault, repository: Repository, episode: Any) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 255) — Whether this open episode is an unanswered opening episode placement ignores.
- `servable_open_episodes(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/state.py), line 266) — ``repository.open_probe_episodes()`` without the ignored opening episodes.
- `servable_open_episode(vault: LoadedVault, repository: Repository, learning_object_id: str) -> Any` ([source](../../../../../../src/learnloop/placement/state.py), line 281) — ``repository.open_probe_episode(lo)``, or None when placement ignores it.
- `placement_tables_present(connection: Any) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 290)
- `class Assumption` ([source](../../../../../../src/learnloop/placement/state.py), line 298)
  - `is_open(self) -> bool` (line 337; public)
  - `as_dict(self) -> dict[str, Any]` (line 340; public)
- `class LearningObjectIntent` ([source](../../../../../../src/learnloop/placement/state.py), line 345) — An LO's current placement routing, derived in time order (never stored).
  - `as_dict(self) -> dict[str, Any]` (line 367; public)
- `class PlacementState` ([source](../../../../../../src/learnloop/placement/state.py), line 372)
  - `due_gap_check_learning_object_ids(self, now_iso: str) -> frozenset[str]` (line 382; public) — Maintenance LOs whose brought-forward check is due now.
  - `advanced_learning_object_ids(self) -> frozenset[str]` (line 392; public) — Open assumptions whose first review a learner-text gap brought forward.
  - `committed_learning_object_ids(self) -> frozenset[str]` (line 398; public) — Open light commitments: prerequisites created from a learner's text.
  - `open_by_lo(self) -> dict[str, Assumption]` (line 406; public)
  - `latest_by_lo(self) -> dict[str, Assumption]` (line 410; public)
  - `decided_learning_object_ids(self) -> frozenset[str]` (line 417; public)
  - `_with_intent(self, intent: str) -> frozenset[str]` (line 420; internal)
  - `back_to_learning_learning_object_ids(self) -> frozenset[str]` (line 424; public) — LOs back to learning: a missed check, a miss in maintenance, or "I don't know this" (with or without an assumption).
  - `maintained_learning_object_ids(self) -> frozenset[str]` (line 432; public) — LOs whose check passed: in maintenance, remaining learning items withheld.
  - `due_learning_object_ids(self, now_iso: str) -> frozenset[str]` (line 437; public)
  - `awaiting_diagnosis_learning_object_ids(self) -> frozenset[str]` (line 441; public) — LOs whose assumption or maintenance waits on a miss's diagnosis: they stay as they are, and no further check item is served meanwhile.
- `pfc_unverified_attempt_ids(connection: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/placement/state.py), line 539) — Attempts whose current grade placement reads as PF-c *unassessed*.
- `load_answers(connection: Any, learning_object_ids: Iterable[str] | None=None) -> dict[str, tuple[AnswerFacts, ...]]` ([source](../../../../../../src/learnloop/placement/state.py), line 650) — Every recorded answer per LO, in (created_at, id) order.
- `diagnosis_waits_run_out(connection: Any, now_iso: str) -> int` ([source](../../../../../../src/learnloop/placement/state.py), line 736) — How many misses' diagnosis waits have run out at ``now_iso``, by the rule :func:`load_miss_verdicts` applies (live diagnose jobs only, a payload naming no mode being live; the deadline ``DIAGNOSIS_WAIT_DAYS`` after the first; run out strictly after it).
- `load_miss_verdicts(connection: Any, answers: Iterable[AnswerFacts], *, diagnosis_live: bool, now_iso: str) -> dict[str, MissVerdict]` ([source](../../../../../../src/learnloop/placement/state.py), line 754) — How the diagnosis decides each graded miss (owner decision 2026-10-12).
- `evaluate_independence(connection: Any, answers: Iterable[AnswerFacts], *, since_floor: str | None=None) -> tuple[AnswerFacts, ...]` ([source](../../../../../../src/learnloop/placement/state.py), line 1013) — Each answer with its independence facts from the existing rules.
- `load_placement_state_from_connection(connection: Any, *, active: bool, diagnosis_live: bool, now_iso: str, gap_commitments: bool=False, gap_checks: bool=False) -> PlacementState` ([source](../../../../../../src/learnloop/placement/state.py), line 1366) — Placement state over one connection.
- `load_placement_state(vault: LoadedVault, repository: Repository, *, now_iso: str | None=None) -> PlacementState` ([source](../../../../../../src/learnloop/placement/state.py), line 1441) — Placement state for a vault; ``now_iso`` defaults to the wall clock.
- `prerequisite_learning_objects(vault: LoadedVault, learning_object_id: str) -> set[str]` ([source](../../../../../../src/learnloop/placement/state.py), line 1457) — LOs on the concepts this LO declares as prerequisites (field §5.2 order).
- `order_new_material(vault: LoadedVault, predictor: LearnerPredictor, items: Sequence[tuple[str, str]], *, taught_first: Iterable[str]=()) -> list[tuple[str, dict[str, float]]]` ([source](../../../../../../src/learnloop/placement/state.py), line 1478) — Order (practice_item_id, learning_object_id) pairs of new material.
- `choose_check_items(predictor: LearnerPredictor, candidates: Mapping[str, Sequence[str]], *, attempted_item_ids: Iterable[str]=()) -> dict[str, str]` ([source](../../../../../../src/learnloop/placement/state.py), line 1518) — One first-review item per due assumed LO: a normal cold item.
- `assumption_summary(state: PlacementState) -> dict[str, Any]` ([source](../../../../../../src/learnloop/placement/state.py), line 1544)

### Module constants

- `INTENT_ASSUMED` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 123)
- `INTENT_MAINTENANCE` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 124)
- `INTENT_LEARNING` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 125)
- `PLACEMENT_TABLES` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 127)
- `LEARNER_TEXT_GAP_SOURCE` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 167)
- `OPENING_EPISODE_TRIGGER` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 194)
- `_COLD_DIMENSIONS` ([src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py), line 985)

## Internal implementation anchors

- `_rows(connection: Any, sql: str, params: Sequence[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/placement/state.py), line 450)
- `_contamination_classes(connection: Any, attempt_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/placement/state.py), line 456) — Latest recorded contamination class per attempt (most contaminated wins).
- `_criterion_maxima(connection: Any, contract_ids: Iterable[str]) -> dict[tuple[str, str], float]` ([source](../../../../../../src/learnloop/placement/state.py), line 489) — ``(contract id, criterion id) -> max_points`` from the content-addressed assessment contracts the evidence rows were graded against.
- `_latest_grading_supports(connection: Any, attempt_ids: Iterable[str]) -> dict[str, Mapping[str, Any]]` ([source](../../../../../../src/learnloop/placement/state.py), line 509) — Each attempt's latest blind grade record's ``grading_support``.
- `_table_present(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 694)
- `_json(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/placement/state.py), line 700)
- `_wait_deadline(first_job_at: str | None) -> str | None` ([source](../../../../../../src/learnloop/placement/state.py), line 709) — The instant a miss stops waiting on its diagnosis (rules.DIAGNOSIS_WAIT_DAYS).
- `_live_diagnose_job(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 718) — A diagnose job of the live diagnosis (a payload naming no mode is live).
- `_diagnosis_wait_deadline(live_jobs: Iterable[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/placement/state.py), line 724) — A miss's wait deadline: ``DIAGNOSIS_WAIT_DAYS`` after its first live diagnose job.
- `_wait_over(deadline: str | None, now_iso: str) -> bool` ([source](../../../../../../src/learnloop/placement/state.py), line 730) — Whether a miss's diagnosis wait has run out at ``now_iso`` (strictly after it).
- `class _BorrowedRepository(Repository)` ([source](../../../../../../src/learnloop/placement/state.py), line 975) — Repository reads inside the caller's connection and snapshot; never commits.
- `_final_receipt_veto(connection: Any, attempt_id: str) -> str | None` ([source](../../../../../../src/learnloop/placement/state.py), line 988) — Why a final coldness receipt makes the attempt non-independent, if it does.
- `_order(created_at: Any, row_id: Any) -> tuple[str, str]` ([source](../../../../../../src/learnloop/placement/state.py), line 1063) — The durable order of a decision, return or answer (module docstring).
- `_landed(verdict: MissVerdict, answer: AnswerFacts) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/placement/state.py), line 1069) — When a miss's decision became known, in the durable order: None while it is pending; the answer itself when it was known at once (learner-side help, an unassessed or joint grade, no diagnosis queued).
- `_learner_side_before(answers: Sequence[AnswerFacts], *, after: int, landed: tuple[str, str] | None, stop: tuple[str, str] | None=None) -> AnswerFacts | None` ([source](../../../../../../src/learnloop/placement/state.py), line 1081) — The first answer after ``answers[after]`` with learner-side help that was recorded before the earlier miss's decision ``landed`` (and before ``stop``, a return).
- `_resolve(decision: Mapping[str, Any], returns: Sequence[Mapping[str, Any]], answers: Sequence[AnswerFacts], independence: IndependenceCheck, graded: Mapping[str, MissVerdict]) -> Assumption` ([source](../../../../../../src/learnloop/placement/state.py), line 1103)
- `_intent(learning_object_id: str, decision: Assumption | None, latest_return: Mapping[str, Any] | None, answers: Sequence[AnswerFacts], graded: Mapping[str, MissVerdict]) -> LearningObjectIntent | None` ([source](../../../../../../src/learnloop/placement/state.py), line 1220) — The LO's current routing from its latest decision and latest return.
- `_commitment_decisions(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/placement/state.py), line 1298) — Created prerequisites' light commitments as decision rows (source ``learner_text_gap``): one delayed check, no predictor.
- `_advance_decisions(connection: Any, decisions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/placement/state.py), line 1316) — mvp-0.16: bring each assumption's first review forward to its earliest learner-text-gap advance; returns (decisions, maintenance advances).
- `_pending_maintenance_checks(advances: Sequence[Mapping[str, Any]], intents: Mapping[str, LearningObjectIntent], answers: Mapping[str, Sequence[AnswerFacts]]) -> dict[str, Mapping[str, Any]]` ([source](../../../../../../src/learnloop/placement/state.py), line 1343) — Per maintenance LO, its earliest advance written in this maintenance spell that no answer has taken since it fell due.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `servable_open_episode`; statically calls `servable_open_episode`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `servable_open_episode`; statically calls `servable_open_episode`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `servable_open_episodes`; statically calls `servable_open_episodes`
- [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]] — imports `assumption_summary`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`; statically calls `assumption_summary`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `placement_active`; statically calls `placement_active`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `diagnosis_waits_run_out`; statically calls `diagnosis_waits_run_out`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `load_placement_state`, `placement_active`; statically calls `load_placement_state`, `placement_active`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `ignored_opening_episode_ids`; statically calls `ignored_opening_episode_ids`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `servable_open_episode`, `servable_open_episodes`; statically calls `servable_open_episode`, `servable_open_episodes`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `ignored_opening_episode_ids`, `servable_open_episodes`; statically calls `ignored_opening_episode_ids`, `servable_open_episodes`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `episode_ignored`; statically calls `episode_ignored`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `episode_ignored`; statically calls `episode_ignored`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `diagnosis_can_arrive`, `load_answers`, `load_placement_state_from_connection`, `placement_active`; statically calls `diagnosis_can_arrive`, `load_answers`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `load_placement_state`, `placement_active`, `prerequisite_learning_objects`; statically calls `load_placement_state`, `placement_active`, `prerequisite_learning_objects`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `prerequisite_learning_objects`; statically calls `prerequisite_learning_objects`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `LEARNER_TEXT_GAP_SOURCE`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`; statically calls `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `prerequisite_learning_objects`; statically calls `prerequisite_learning_objects`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `pfc_unverified_attempt_ids`; statically calls `pfc_unverified_attempt_ids`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `load_placement_state`; statically calls `load_placement_state`
- [[Reference/Modules/learnloop/placement/claim_check|learnloop.placement.claim_check]] — imports `load_placement_state`, `placement_active`; statically calls `load_placement_state`, `placement_active`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `INTENT_MAINTENANCE`, `PlacementState`, `diagnosis_can_arrive`, `evaluate_independence`, `load_answers`, `load_placement_state_from_connection`, `placement_active`; statically calls `diagnosis_can_arrive`, `evaluate_independence`, `load_answers`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/placement/report|learnloop.placement.report]] — imports `INTENT_ASSUMED`, `INTENT_MAINTENANCE`, `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_tables_present`; statically calls `diagnosis_can_arrive`, `load_placement_state_from_connection`, `placement_tables_present`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `load_answers`; statically calls `load_answers`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `ignored_opening_episode_ids`; statically calls `ignored_opening_episode_ids`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `choose_check_items`, `diagnosis_can_arrive`, `load_placement_state`, `order_new_material`, `placement_active`, `servable_open_episodes`; statically calls `choose_check_items`, `diagnosis_can_arrive`, `load_placement_state`, `order_new_material`, `placement_active`, `servable_open_episodes`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `load_placement_state`; statically calls `load_placement_state`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `initial_probes_enabled`; statically calls `initial_probes_enabled`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `episode_ignored`; statically calls `episode_ignored`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `servable_open_episode`; statically calls `servable_open_episode`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `LEARNER_TEXT_GAP_SOURCE`, `load_placement_state`, `placement_active`; statically calls `load_placement_state`, `placement_active`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `LEARNER_TEXT_GAP_SOURCE`, `load_placement_state`, `placement_active`; statically calls `load_placement_state`, `placement_active`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `episode_ignored`, `servable_open_episode`; statically calls `episode_ignored`, `servable_open_episode`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `placement_active`; statically calls `placement_active`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DIAGNOSIS_SPLIT_VERSIONS`, `LEARNER_TEXT_GAP_VERSIONS`, `PLACEMENT_VERSIONS`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `production_admissibility`; calls `production_admissibility`
- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `CONTAMINATION_PRECEDENCE`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `FrozenClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `check_advances`, `commitments`; calls `check_advances`, `commitments`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `LearnerPredictor`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/placement/rules|learnloop.placement.rules]] — imports `AnswerFacts`, `CHECK_PASS`, `DIAGNOSIS_WAIT_DAYS`, `FALLBACK_BUDGET_SKIPPED`, `FALLBACK_DIAGNOSIS_FAILED`, `FALLBACK_DIAGNOSIS_UNAVAILABLE`, `FALLBACK_NOT_BLIND_GRADED`, `FALLBACK_NOT_DIAGNOSED`, `FALLBACK_NOT_NEEDED`, `FALLBACK_REJECTED`, `FALLBACK_SPLIT_DISABLED`, `KEPT_REASONS`, `MISS_KEPT`, `MISS_PENDING`, `MISS_TO_LEARNING`, `MissVerdict`, `PFC_UNASSESSED_INTERPRETATION`, `PFC_UNASSESSED_INTERPRETATION_KEY`, `PFC_UNVERIFIED_BLOCK`, `REASON_DIAGNOSIS_PENDING`, `REASON_LEARNER_SIDE`, `REASON_NO_DIAGNOSIS`, `answer_facts`, `check_verdict`, `decide_miss`, `diagnosis_reason`, `new_material_key`, `prerequisite_layers`; calls `MissVerdict`, `answer_facts`, `check_verdict`, `decide_miss`, `diagnosis_reason`, `new_material_key`, `prerequisite_layers`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] and 28 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_a_final_receipt_that_does_not_qualify_as_cold_retrieval_cannot_pass_the_check`
  - `test_a_passed_check_keeps_the_remaining_learning_items_withheld`
  - `test_a_post_reveal_answer_cannot_pass_the_check`
  - `test_a_qualified_final_receipt_still_lets_the_check_pass`
  - `test_a_return_in_the_same_second_as_i_know_this_still_returns_the_lo`
  - `test_an_early_miss_still_returns_the_lo_to_learning`
  - `test_answers_in_the_same_second_as_a_decision_or_return_keep_their_order`
  - `test_failed_first_review_quietly_returns_the_lo_to_learning`
  - `test_fast_track_check_waits_for_its_review_interval`
  - `test_i_dont_know_this_returns_an_assumed_lo_to_learning_immediately`
  - `test_i_know_this_in_the_same_second_as_a_return_supersedes_it`
  - `test_initial_probes_switch_restores_opening_episodes_only`
  - `test_kill_switch_restores_initial_probes_serving_and_ordering_exactly`
  - `test_new_vaults_start_with_placement_on`
  - `test_no_initial_episodes_for_new_los_and_new_material_is_served_in_order`
  - `test_passed_first_review_keeps_the_lo_in_maintenance`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
  - `test_m1_the_deadline_input_moves_strictly_after_the_deadline`
  - `test_m2_the_count_is_placements_rule_for_the_same_rows`
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_placement_and_the_field_read_a_held_attempt_as_unassessed`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_missing_prerequisite_is_drafted_created_live_seeded_and_committed`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_gap_brings_an_assumed_los_check_forward_and_the_switch_restores_the_predecessor`
  - `test_a_gap_on_a_maintenance_lo_brings_its_next_review_forward_until_answered`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f10_switching_edges_off_removes_their_effect_and_keeps_them_in_the_file`
  - `test_f13_a_created_los_check_failed_goes_to_learning`
  - `test_f13_a_created_los_check_passed_goes_to_maintenance`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline`
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
  - `test_f6_the_resolving_review_carries_one_quiet_claim_line_and_no_other_does`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_latest_version`
  - `test_split_and_placement_activate_at_the_right_versions`
  - `test_upgrade_from_mvp010_flips_rebuilds_and_preserves_history_and_open_episodes`
  - `test_upgrade_from_mvp09_chains_through_the_split`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_kill_switch_keeps_the_version_and_every_predecessor`
  - `test_only_mvp013_offers_the_stuck_control`
  - `test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_the_plan_serves_only_at_the_successor_with_the_switch_on`
  - `test_upgrade_from_mvp013_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_upgrade_from_mvp014_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_with_sooner_checks`
  - `test_upgrade_from_mvp015_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_upgrade_from_mvp016_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_each_version_keeps_its_predecessors_and_grades_as_mvp016`
  - `test_upgrade_from_mvp017_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_with_the_route_rules`
  - `test_upgrade_from_mvp019_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_a_diagnosis_that_never_lands_stops_holding_the_check`
  - `test_i_dont_know_this_does_not_wait_on_a_pending_diagnosis`
  - `test_the_decision_waits_while_the_diagnosis_is_pending`
  - `test_the_kill_switch_ignores_diagnosis_decided_outcomes`
  - `test_the_state_loader_requires_the_split_reading_and_the_time`
  - `test_turning_the_split_back_on_does_not_reopen_held_misses`
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
  - `test_placement_ignores_unanswered_opening_episodes_on_fixture_copies`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_a_named_calibration_adopts_an_ignored_episode`
  - `test_an_answer_on_an_ignored_episode_is_not_held_back_for_it`
  - `test_an_answered_opening_episode_is_not_ignored`
  - `test_an_error_driven_reprobe_adopts_an_ignored_episode`
  - `test_an_ignored_episode_feeds_no_reader_that_scores_it`
  - `test_an_in_progress_opening_episode_serves_no_probe_and_is_not_parked`
  - `test_the_causal_quick_check_stops_the_episode_being_ignored`
  - `test_the_overconfidence_list_adopts_an_ignored_episode`
  - `test_the_switches_serve_the_opening_episodes_again_exactly`
  - `test_unanswered_opening_episodes_are_ignored_and_their_los_start_as_learning`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
  - `test_a_located_error_is_decided_by_its_diagnosis`
  - `test_a_pfc_grade_whose_review_was_cleared_is_still_unassessed`
  - `test_a_pfc_grade_with_another_review_reason_is_still_unassessed`
  - `test_a_record_written_before_the_rule_keeps_m2s_reading`
  - `test_a_regrade_to_unverified_keeps_the_topic_in_maintenance`
  - `test_an_assessed_shortfall_beside_an_unverified_criterion_is_a_miss_the_diagnosis_decides`
  - `test_an_unverified_answer_in_maintenance_is_not_a_lapse`
  - `test_an_unverified_pfc_grade_on_the_check_keeps_the_topic_in_maintenance`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_f1_a_learner_gap_commitment_is_never_assumed_known`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_upgrade_chains_from_each_predecessor`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_a_confused_stuck_answer_keeps_its_topic_out_of_fast_track`

## Modification guidance

- Make changes here when the responsibility remains state within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/state.py](../../../../../../src/learnloop/placement/state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
