---
title: "learnloop.content.authoring.persona_gate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/persona_gate.py"
source_paths:
  - "src/learnloop/content/authoring/persona_gate.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.persona_gate module"
  - "src/learnloop/content/authoring/persona_gate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.persona_gate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.persona_gate` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: §3.0's shared planted-persona gate, wired into the live authoring path.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py) |
| Source lines | 1629 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RealismLicenseStatus(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 120) — Why a row's pass is (or is not) B2-licensed -- persisted in the audit.
- `class InstrumentClass(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 152) — The closed vocabulary of authored instrument classes §3.0 governs.
- `class GateTier(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 193) — Hard ship/no-ship vs advisory flag-for-review vs out of scope.
- `tier_for(instrument_class: InstrumentClass) -> GateTier` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 228)
- `contrast_pair_key(payload: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 262) — The pair id two contrast-pair members share, if the payload declares one.
- `classify_instrument(payload: Mapping[str, Any]) -> InstrumentClass` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 293) — The instrument class of one proposal-row payload (§3.0 tiering input).
- `class PersonaKind(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 336) — Who is answering.
- `class Persona` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 346) — One planted student, and the answer it would write.
  - `as_dict(self) -> dict[str, Any]` (line 368; public)
- `class PersonaTrial` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 379) — One persona graded in memory against one item.
  - `passes(self) -> bool` (line 387; public)
  - `as_dict(self) -> dict[str, Any]` (line 390; public)
- `class GateDecision(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 399) — The four outcomes, and the four different things they mean.
- `class PersonaGateReason(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 423) — Closed vocabulary of *why*.
- `class SeparationVerdict` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 508) — Whether one item's personas separate, with the trials that decided it.
  - `as_dict(self) -> dict[str, Any]` (line 516; public)
- `separation_verdict(*, expected_answer: str, personas: Sequence[Persona], require_keyed_detector: bool, has_keyed_detector: bool, grading_client: Any=None, fire_context: Mapping[str, Any] | None=None) -> SeparationVerdict` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 558) — §3.0's single question, asked over one item's personas.
- `declares_error_count(prompt: str) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 636) — Does this prompt tell the learner how many errors to look for?
- `error_hunt_verdict(payload: Mapping[str, Any], *, personas: Sequence[Persona], vault: LoadedVault, repository: Repository | None=None, grading_client: Any=None) -> SeparationVerdict` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 711) — §3.0's separation question, asked the way an A3 item answers it.
- `build_personas(payload: Mapping[str, Any], *, vault: LoadedVault, repository: Repository | None=None) -> tuple[Persona, ...]` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 833) — Plant the personas §3.0 needs from whatever the payload/registry supplies.
- `class PersonaGateOutcome` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 955) — One row's typed gate outcome — the thing persisted into ``audit_json``.
  - `gated(self) -> bool` (line 971; public) — Did the gate make a prediction about this item?
  - `as_dict(self) -> dict[str, Any]` (line 980; public)
- `class PersonaGate` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 1001) — §3.0 as a ``row_transform`` over persisted proposal rows (plan item 5.3).
  - `__init__(self, vault: LoadedVault, repository: Repository | None=None, *, grading_client: Any=None) -> None` (line 1011; internal)
  - `blocked(self) -> list[PersonaGateOutcome]` (line 1025; public)
  - `flagged(self) -> list[PersonaGateOutcome]` (line 1029; public)
  - `violations(self) -> list[str]` (line 1033; public) — Hard-tier failures, in ``_RungGate``'s ``"<ref>: <message>"`` shape.
  - `warnings(self) -> list[str]` (line 1042; public)
  - `summary(self) -> dict[str, Any]` (line 1048; public)
  - `__call__(self, rows: list[dict[str, Any]]) -> None` (line 1065; internal)
  - `_is_authored_item(row: Mapping[str, Any]) -> bool` (line 1099; internal)
  - `_apply(self, row: dict[str, Any], outcome: PersonaGateOutcome) -> None` (line 1106; internal)
  - `persona_generator_family(self) -> str | None` (line 1111; public) — B3 family identity of whatever authored the personas being gated.
  - `_licenses_this_gate(self, row: Mapping[str, Any]) -> bool` (line 1131; internal) — Is this B2 run a license for the material THIS gate is judging?
  - `_authored_signature_runs(self, outcome: PersonaGateOutcome) -> tuple[list[Mapping[str, Any]], PersonaGateOutcome | None]` (line 1159; internal) — Read the B2 ledger.
  - `_apply_realism_license(self, outcome: PersonaGateOutcome) -> PersonaGateOutcome` (line 1189; internal) — B2 licenses a pass, or invalidates it when personas are separable.
  - `_judge_contrast_pair(self, key: str, members: Sequence[Mapping[str, Any]]) -> list[PersonaGateOutcome]` (line 1265; internal) — §3.0's A4 clause: the belief-holder must fail EXACTLY one member.
  - `_pair_outcome(row: Mapping[str, Any], decision: GateDecision, verdict: SeparationVerdict) -> PersonaGateOutcome` (line 1347; internal)
  - `judge(self, payload: Mapping[str, Any], *, client_item_id: str='item') -> PersonaGateOutcome` (line 1362; public) — Judge one payload.
  - `_decide(instrument_class: InstrumentClass, tier: GateTier, verdict: SeparationVerdict) -> GateDecision` (line 1421; internal) — Map a separation verdict onto a route decision, given the tier.
  - `_record(row: dict[str, Any], outcome: PersonaGateOutcome) -> None` (line 1438; internal) — Persist the typed outcome onto the row (audit + route), never log-only.
- `class GatePrecisionRow` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 1470) — One persisted gate outcome, joined to the reviewer's later decision.
  - `gated(self) -> bool` (line 1484; public)
- `gate_precision(repository: Repository, *, blinded_labels: Mapping[str, bool] | None=None, since: str | None=None) -> Metric` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 1488) — ``persona_gate_precision``: of the items the gate blocked or flagged, how many were genuinely bad.
- `persona_gate_rows(repository: Repository, *, since: str | None=None) -> list[GatePrecisionRow]` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 1611) — Every persisted persona-gate outcome, joined to its reviewer decision.

### Module constants

- `PERSONA_GATE_VERSION` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 114)
- `PERSONA_GATE_REALISM_SOURCE` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 117)
- `UNPLANTABLE_IS_FATAL` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 204)
- `DIAGNOSTIC_INSTRUMENT_CLASSES` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 214)
- `_A_CLASS_TOKENS` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 221)
- `CONTRAST_PAIR_TAG_PREFIX` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 259)
- `_REGISTRY_PLANT_SOURCES` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 620)
- `_ERROR_COUNT_PATTERNS` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 628)
- `GATE_PRECISION_METRIC` ([src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 1466)

## Internal implementation anchors

- `_rubric_of(payload: Mapping[str, Any]) -> Mapping[str, Any] | None` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 236)
- `_fatal_errors_of(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 241)
- `_keyed_misconception_ids(payload: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 248)
- `_fires(answer: str, *, expected: str, grading_client: Any=None, fire_context: Mapping[str, Any] | None=None) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 525) — Grade one persona answer in memory.
- `_plant_holder(plant: Mapping[str, Any], *, vault: LoadedVault, repository: Repository | None, personas: Sequence[Persona]) -> Persona | None` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 652) — The persona who holds the belief THIS plant was drawn from, or ``None``.
- `_facet_error_signatures(vault: LoadedVault, facet_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 826)
- `_expected_text(payload: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 937)
- `_ref(row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 944)
- `_tally(values: Iterable[str]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/authoring/persona_gate.py), line 1604)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `gate_precision`; statically calls `gate_precision`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `GateDecision`, `PersonaGate`, `_keyed_misconception_ids`; statically calls `PersonaGate`, `_keyed_misconception_ids`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `GateDecision`, `PersonaGate`; statically calls `PersonaGate`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `declares_error_count`; statically calls `declares_error_count`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `gate_precision`; statically calls `gate_precision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/content/authoring/persona_realism|learnloop.content.authoring.persona_realism]] — imports `PERSONA_REALISM_MATCHER_VERSION`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `model_family`; calls `model_family`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`, `request_diagnostic_fire`; calls `normalize_answer`, `request_diagnostic_fire`
- [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] — imports `payload_profiles`; calls `payload_profiles`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `Metric`; calls `Metric`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `logging`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contrast_pairs.py](../../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_a_pair_key_is_derived_not_authored`
  - `test_a_pair_must_satisfy_both_the_persona_gate_and_the_pair_gate`
  - `test_a_pair_the_persona_gate_cannot_plant_does_not_ship`
  - `test_carrying_the_pair_fields_is_what_makes_it_a_contrast_pair`
- [tests/test_discrimination_profiles.py](../../../../../../../tests/test_discrimination_profiles.py) — direct import
  - `test_a_discriminating_profile_passes_and_plants_every_profile`
  - `test_authoring_a_profile_promotes_the_item_to_the_hard_tier_structurally`
  - `test_profile_whose_signature_equals_the_answer_key_is_blocked`
- [tests/test_error_hunt_items.py](../../../../../../../tests/test_error_hunt_items.py) — direct import
  - `test_a_facet_error_signature_corroborates_a_plant_with_no_registry_belief`
  - `test_a_plant_identical_to_its_own_repair_is_rejected`
  - `test_a_plant_invisible_to_the_belief_holder_passes`
  - `test_a_plant_the_belief_holder_would_catch_is_rejected`
  - `test_a_plant_the_registry_cannot_corroborate_is_rejected`
  - `test_a_plant_with_no_required_repair_is_rejected`
  - `test_a_prompt_that_states_the_error_count_is_rejected`
  - `test_carrying_an_error_hunt_contract_is_what_makes_it_an_error_hunt`
  - `test_the_clean_rotation_passes_with_its_own_typed_reason`
- [tests/test_persona_gate.py](../../../../../../../tests/test_persona_gate.py) — direct import
  - `test_b2_license_from_another_generator_family_stays_advisory`
  - `test_b2_license_promotes_plain_practice_advisory_failure_to_hard`
  - `test_b2_lookup_fault_is_not_reported_as_an_unvalidated_pass`
  - `test_b2_never_run_is_recorded_as_no_run`
  - `test_b2_separable_corpus_invalidates_an_otherwise_passing_hard_gate`
  - `test_contrast_pair_must_fail_exactly_one_member`
  - `test_every_typed_reason_is_reachable_is_asserted_by_this_module`
  - `test_gate_precision_becomes_available_once_labels_are_supplied`
  - `test_gate_precision_reports_no_data_before_any_prediction`
  - `test_gate_precision_reports_no_producer_without_blinded_ground_truth`
  - `test_live_generate_diagnostics_blocks_an_undiscriminating_diagnostic`
  - `test_live_generate_diagnostics_ships_a_discriminating_diagnostic`
  - `test_live_plain_practice_item_is_flagged_but_shipped`
  - `test_live_route_abstains_when_there_is_nothing_to_plant`
  - `test_reason_facet_holder_fails_via_semantic_grader`
  - `test_reason_insufficient_persona_payload_blocks_an_unplantable_error_hunt`
  - `test_reason_no_keyed_detector`
  - `test_reason_not_an_instrument_abstains`
  - `test_tier_is_read_off_the_payload_not_the_route`

## Modification guidance

- Change persona gate policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/persona_gate.py](../../../../../../../src/learnloop/content/authoring/persona_gate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
