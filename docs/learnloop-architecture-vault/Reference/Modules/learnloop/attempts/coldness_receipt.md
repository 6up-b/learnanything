---
title: "learnloop.attempts.coldness_receipt"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/coldness_receipt.py"
source_paths:
  - "src/learnloop/attempts/coldness_receipt.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.coldness_receipt module"
  - "src/learnloop/attempts/coldness_receipt.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.coldness_receipt`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.coldness_receipt` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Explicit coldness administration receipts for delayed retrieval lanes.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py) |
| Source lines | 2035 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ColdnessEvaluation` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1433) — One computed set of dimensions, ready to store or to gate on.
- `evaluate_final_coldness(vault: LoadedVault, repository: Repository, *, task: Mapping[str, Any], cold_attempt_id: str | None, clock: Clock | None=None) -> ColdnessEvaluation` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1692) — Compute the final-stage dimensions.
- `record_administration_snapshot(vault: LoadedVault, repository: Repository, *, task: Mapping[str, Any], clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1789) — Stage 1: the serving-time snapshot, idempotent per follow-up task.
- `record_certification_administration_snapshot(vault: LoadedVault, repository: Repository, *, task: Mapping[str, Any], clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1867) — Named certification-lane adapter for callers that require lane clarity.
- `record_final_receipt(repository: Repository, *, task: Mapping[str, Any], evaluation: ColdnessEvaluation, outcome: str, cold_attempt_id: str | None=None, cold_verification_id: str | None=None, lane: str=LANE_REPAIR_COLD_RETRY, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1883) — Stage 2: the terminal receipt — measured verifications AND refusals.
- `record_schedule_refusal_receipt(repository: Repository, *, opportunity: Mapping[str, Any], decision: str, reason: str, candidate_summary: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1944) — Record a terminal receipt when no task could be scheduled.

### Module constants

- `COLDNESS_RECEIPT_VERSION` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 133)
- `TELEMETRY_COVERAGE_VERSION` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 134)
- `LANE_REPAIR_COLD_RETRY` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 138)
- `LANE_CERTIFICATION_COLD_PROBE` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 139)
- `MIN_COLD_DELAY` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 147)
- `WINDOW_SUBMIT_GRACE` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 151)
- `WINDOW_RULE` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 152)
- `DIMENSION_NAMES` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 154)
- `SCANNED_LEDGERS` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 167)
- `KNOWN_UNOBSERVED_CHANNELS` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 234)
- `ABSENCE_CLEAR` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 263)
- `ABSENCE_CONTAMINATED` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 264)
- `ABSENCE_INDETERMINATE` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 265)
- `SELECTION_POLICY` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 267)
- `SELECTION_POLICY_NOTE` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 268)
- `COLD_ITEM_REVEAL_REASONS` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1049)
- `SAME_SURFACE_REASONS` ([src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1066)

### Explicit exports

`__all__` declares:

- `COLDNESS_RECEIPT_VERSION`
- `TELEMETRY_COVERAGE_VERSION`
- `LANE_REPAIR_COLD_RETRY`
- `LANE_CERTIFICATION_COLD_PROBE`
- `KNOWN_UNOBSERVED_CHANNELS`
- `MIN_COLD_DELAY`
- `SCANNED_LEDGERS`
- `WINDOW_SUBMIT_GRACE`
- `ColdnessEvaluation`
- `evaluate_final_coldness`
- `record_administration_snapshot`
- `record_certification_administration_snapshot`
- `record_final_receipt`
- `record_schedule_refusal_receipt`

## Internal implementation anchors

- `_content_id(prefix: str, value: Any) -> str` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 277)
- `_iso(value: datetime) -> str` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 284)
- `_dimension(status: str, evidence: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 288)
- `_canonical_facets(vault: LoadedVault, facets: Any) -> set[str]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 292)
- `_telemetry_coverage(interval: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 296)
- `_indeterminate_dimensions(reason: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 305)
- `_case_scope(vault: LoadedVault, repository: Repository, *, case_kind: str | None, case_ref: str | None) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 315) — Resolve a case to the LO/facets whose study can refresh this target.
- `_episode_is_relevant(vault: LoadedVault, repository: Repository, episode: Mapping[str, Any] | None, *, relevant_los: set[str], relevant_facets: set[str], relevant_case_refs: set[str]) -> bool` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 375)
- `_scan_exposures(vault: LoadedVault, repository: Repository, *, interval_start: str, interval_end: str, source_attempt: Mapping[str, Any] | None, cold_item_id: str | None, cold_attempt_id: str | None=None, case_ref: str | None, exclude_attempt_ids: set[str], additional_relevant_los: set[str] | None=None, additional_relevant_facets: set[str] | None=None, additional_relevant_case_refs: set[str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 400) — Typed intervening-exposure scan over the enumerated ledgers.
- `_item_source_spans(item: Any) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 803) — The (extraction, span) pairs an item was authored from, if any.
- `_retrieval_delay(*, source_at: str | None, measured_to: str | None, scan: Mapping[str, Any], minimum_delay: timedelta=MIN_COLD_DELAY, anchor_kind: str='primed_attempt') -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 828)
- `_exposure_isolation(scan: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 883)
- `_surface_novelty(vault: LoadedVault, repository: Repository, *, cold_item_id: str | None, source_attempt: Mapping[str, Any] | None, interval_end: str, exclude_attempt_ids: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 903) — Positive administered-exclusion evidence, time-bounded.
- `_selection_basis(task: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 985)
- `_cold_item_reveal_rows(scan: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1073) — Ledger rows (migration 154) that exposed the COLD item's own answer.
- `_answer_leakage(scan: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1084)
- `_window_integrity(*, task: Mapping[str, Any], open_at: str | None, submit_at: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1115)
- `_grading_identity(repository: Repository, attempt_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1155) — Who graded one attempt: channel, tiers, and the agent run behind it.
- `_run_separation(source: Mapping[str, Any] | None, cold: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1211) — Half one: did a DIFFERENT run grade the cold attempt?
- `_context_blinding(repository: Repository, *, source_attempt_id: str | None, cold_attempt_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1244) — Half two: was the cold grading call given repair/diagnosis context?
- `_verification_blinding(repository: Repository, *, source_attempt_id: str | None, cold_attempt_id: str | None, cold_attempt: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1308) — Two independent halves, recorded separately and reported separately.
- `_unassisted(cold_attempt: Mapping[str, Any] | None, scan: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1387) — Was the cold attempt taken without assistance — flags AND ledger.
- `_derive(dimensions: Mapping[str, Any], scan: Mapping[str, Any] | None, *, stage: str, lane: str=LANE_REPAIR_COLD_RETRY) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1446)
- `_hard_contamination(scan: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1502)
- `_evaluate(vault: LoadedVault, repository: Repository, *, task: Mapping[str, Any], stage: str, cold_attempt_id: str | None, open_at: str | None, now_iso: str) -> ColdnessEvaluation` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1518)
- `_apply_episode_reveal_budget(derived: dict[str, Any], task: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/attempts/coldness_receipt.py), line 1742) — Downgrade the repair-effect CLAIM when the episode overspent its reveals.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `evaluate_final_coldness`, `record_final_receipt`; statically calls `evaluate_final_coldness`, `record_final_receipt`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `LANE_REPAIR_COLD_RETRY`, `record_schedule_refusal_receipt`; statically calls `record_schedule_refusal_receipt`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `LANE_CERTIFICATION_COLD_PROBE`, `evaluate_final_coldness`, `record_final_receipt`, `record_schedule_refusal_receipt`; statically calls `evaluate_final_coldness`, `record_final_receipt`, `record_schedule_refusal_receipt`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `record_administration_snapshot`, `record_certification_administration_snapshot`; statically calls `record_administration_snapshot`, `record_certification_administration_snapshot`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `REMEDIATION_DELIVERY_CONTEXT`, `REMEDIATION_DELIVERY_ENTITY_TYPE`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]], [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_probe_records_a_durable_versioned_label`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_coldness_receipts_are_append_only`
  - `test_delivered_passages_in_interval_are_typed_exposure_not_indeterminate`
  - `test_feedback_reopen_on_the_source_attempt_is_a_soft_exposure`
  - `test_happy_path_snapshot_verification_and_final_receipt`
  - `test_min_cold_delay_mirrors_the_lane_scheduling_constant`
  - `test_over_budget_episode_downgrades_the_repair_effect_claim`
  - `test_prescription_without_a_delivery_record_is_unknown_not_pass`
  - `test_retrieval_cointervention_demotes_attribution_not_the_verification`
  - `test_reveal_on_the_cold_item_fails_leakage_and_unassisted`
  - `test_verification_blinding_is_unknown_without_a_grading_context_receipt`
  - `test_within_budget_episode_records_the_spend_without_downgrading`

## Modification guidance

- Change coldness receipt policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/coldness_receipt.py](../../../../../../src/learnloop/attempts/coldness_receipt.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
