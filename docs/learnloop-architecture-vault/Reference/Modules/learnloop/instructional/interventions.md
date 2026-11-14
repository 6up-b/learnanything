---
title: "learnloop.instructional.interventions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/interventions.py"
source_paths:
  - "src/learnloop/instructional/interventions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.interventions module"
  - "src/learnloop/instructional/interventions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.interventions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.interventions` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Retrieval in the evidence loop: the intervention records (spec_source_practice_and_probes_v1 §11; S5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/interventions.py](../../../../../../src/learnloop/instructional/interventions.py) |
| Source lines | 513 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `interventions_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 61)
- `record_intervention(vault: LoadedVault, repository: Repository, *, kind: str, clock: Clock | None=None, existing: Callable[[Any], str | None] | None=None, **fields: Any) -> str | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 66) — Append one intervention row; None (nothing written) when the switch is off.
- `seconds_since_related_exposure(verdicts: Sequence[Mapping[str, Any] | None], *, now: str) -> float | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 178) — Seconds from the most recent related exposure any verdict records to ``now`` (the delivery), or None when none records one (Codex third pass F13).
- `record_pick(vault: LoadedVault, repository: Repository, *, proposal_id: str, practice_item_id: str | None=None, exercise: Mapping[str, Any] | None=None, serve_verdict: Mapping[str, Any] | None=None, session_id: str | None=None, router_decision_id: str | None=None, import_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 189) — A picked proposal delivered: an item (``practice_pick``) or an imported textbook exercise (``source_exercise``, with the item it became).
- `record_tutor_citations(vault: LoadedVault, repository: Repository, event_id: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 254) — A tutor answer citing retrieved or pinned spans (``source_passage``).
- `record_shown_spans(repository: Repository, keys: Sequence[str], *, context: str, entity_type: str, entity_id: str, source_versions: Mapping[str, Any] | None=None, clock: Clock | None=None, exposure_fields: Mapping[str, Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 280) — One ``source_exposure_events`` row per span whose text became visible.
- `record_offer_shown(vault: LoadedVault, repository: Repository, tool_call_id: str, *, span_keys: Sequence[str]=(), session_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 321) — A tool's passage offer opened (``source_passage``) or comparison shown (``comparison``).
- `offer_shown(vault: LoadedVault, repository: Repository, tool_call_id: str, *, span_keys: Sequence[str]=(), session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 330) — The passages that became visible are recorded as exposure first, always; the intervention (when ``interventions`` is on) links those rows.
- `record_remediation_delivery(vault: LoadedVault, repository: Repository, episode: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 371) — Ranked remediation passages delivered (``remediation_passage``); the fallback prescription is not retrieval.
- `record_need_served(vault: LoadedVault, repository: Repository, need: Mapping[str, Any], *, practice_item_id: str, proposal_id: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 391) — A need fulfilled from the sources and then served (``source_exercise``).
- `outcomes_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 432) — ``learnloop sources outcomes``: associations by intent, kind, caller and source.

### Module constants

- `ASSOCIATIONS_LABEL` ([src/learnloop/instructional/interventions.py](../../../../../../src/learnloop/instructional/interventions.py), line 57)

### Explicit exports

`__all__` declares:

- `ASSOCIATIONS_LABEL`
- `interventions_active`
- `offer_shown`
- `outcomes_report`
- `record_intervention`
- `record_need_served`
- `record_offer_shown`
- `record_pick`
- `record_remediation_delivery`
- `record_shown_spans`
- `record_tutor_citations`
- `seconds_since_related_exposure`

## Internal implementation anchors

- `_pick_delivery(proposal_id: str, practice_item_id: str | None, import_id: str | None) -> Callable[[Any], str | None]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 88) — One delivery per picked proposal candidate (Codex re-review F10).
- `_revision_ids(repository: Repository, extraction_ids: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 105)
- `_check_entry(valuation: Mapping[str, Any] | None, ref: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 113) — The valued check (or valued candidate) for ``ref`` in a proposal's valuation receipt: the calibration fields (§11.4).
- `_state_ref(valuation: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 149)
- `_exposure_moments(verdict: Mapping[str, Any]) -> list[datetime]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 159) — When the verdict's related exposures happened: the persisted stamps, else (a verdict recorded before them) its check time less the age it measured then.
- `_wilson(successes: int, n: int, z: float=1.96) -> list[float] | None` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 408)
- `_rates(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/interventions.py), line 417)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `outcomes_report`; statically calls `outcomes_report`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `record_pick`; statically calls `record_pick`
- [[Reference/Modules/learnloop/remote/telemetry|learnloop.remote.telemetry]] — imports `record_shown_spans`; statically calls `record_shown_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `record_need_served`; statically calls `record_need_served`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `record_shown_spans`; statically calls `record_shown_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `record_shown_spans`; statically calls `record_shown_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `record_shown_spans`; statically calls `record_shown_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `record_remediation_delivery`; statically calls `record_remediation_delivery`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `offer_shown`; statically calls `offer_shown`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `record_tutor_citations`; statically calls `record_tutor_citations`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `proposal`; calls `proposal`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `KEY_STATUS_LABELS`, `effective_key_status`, `exercise_import_ids`, `impressions_for_proposal`, `insert_intervention`, `interventions`, `outcomes`, `tool_call`, `tool_call_runs`; calls `effective_key_status`, `exercise_import_ids`, `impressions_for_proposal`, `insert_intervention`, `interventions`, `outcomes`, `tool_call`, `tool_call_runs`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for_question_event`; calls `caller_for_question_event`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; calls `fields`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `COLD_STATES`, `MEASURED_COLD_STATES`, `SUCCESS_CORRECTNESS`, `rebuild_intervention_outcomes`; calls `rebuild_intervention_outcomes`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]], [[Reference/Modules/learnloop/remote/telemetry|learnloop.remote.telemetry]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intervention_outcomes_replayer.py](../../../../../../tests/test_intervention_outcomes_replayer.py) — direct import
  - `test_the_replayer_is_registered_deterministic_and_calls_nothing`
  - `test_the_replayer_reads_persisted_exposure`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_fallback_pick_is_not_exposed_by_its_own_listing_and_its_request_reaches_the_import_unchanged`
  - `test_a_seen_page_or_solution_is_labelled_and_offered_as_practice_never_as_a_check`
  - `test_exposure_since_the_card_was_shown_is_read_again_at_the_pick`
  - `test_exposure_since_the_pick_is_read_again_at_admission_and_shown`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
  - `test_an_exercise_pick_and_a_need_served_are_source_exercise_rows`
  - `test_an_opened_offer_records_exposure_that_independence_reads`
  - `test_passages_and_comparisons_are_recorded_when_shown`
  - `test_the_switch_off_writes_nothing`
  - `test_tutor_citations_and_remediation_delivery`
- [tests/test_sources_outcomes_report.py](../../../../../../tests/test_sources_outcomes_report.py) — direct import
  - `test_the_report_groups_and_labels_associations`
  - `test_the_report_says_when_recording_is_off`
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_studied_worked_example_records_the_seconds_since_exposure`
  - `test_decision_fields_reach_the_record_and_the_outcome_derives_the_action_change`
  - `test_exposure_age_is_measured_at_delivery_not_at_valuation`

## Modification guidance

- Make changes here when the responsibility remains interventions within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/interventions.py](../../../../../../src/learnloop/instructional/interventions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
