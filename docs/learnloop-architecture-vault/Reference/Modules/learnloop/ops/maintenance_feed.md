---
title: "learnloop.ops.maintenance_feed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/maintenance_feed.py"
source_paths:
  - "src/learnloop/ops/maintenance_feed.py"
source_commit: "93df11dc9fc1f412f0ee3d84a893ccfa89288cf2"
source_commit_timestamp: "2026-10-25T17:27:01-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.maintenance_feed module"
  - "src/learnloop/ops/maintenance_feed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.maintenance_feed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.maintenance_feed` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Maintenance feed (source-ingestion §11).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py) |
| Source lines | 514 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `93df11dc9fc1f412f0ee3d84a893ccfa89288cf2` |
| Commit timestamp | `2026-10-25T17:27:01-04:00` |

## Public API

- `class NoticeType` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 35)
- `generate_maintenance_feed(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 89) — Regenerate the feed deterministically; return the live notices (§11).
- `report_transcription_mismatch(vault: LoadedVault, repository: Repository, practice_item_id: str, *, origin: Any, note: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 356) — File the learner's report that an imported exercise's transcription doesn't match the page (ux_reader_compare_ask_v1 §8.2).
- `dismiss_notice(repository: Repository, notice_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 487)
- `snooze_notice(repository: Repository, notice_id: str, *, until: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 491) — Snooze a notice; escalation-policy notices raise severity after N snoozes.

### Module constants

- `ESCALATION_SNOOZE_THRESHOLD` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 31)
- `NOTICE_TYPES` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 42)
- `TRANSCRIPTION_MISMATCH` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 74)
- `_COLLECTORS` ([src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py), line 472)

## Internal implementation anchors

- `class _Notice` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 78)
- `_collect(vault: LoadedVault, repository: Repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 156)
- `_stale_link_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 163)
- `_open_conflict_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 188)
- `_partial_append_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 204)
- `_lo_without_practice_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 218)
- `_taught_blueprint_without_assessment_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 240) — A taught blueprint with no assessment_alignment provenance (§11).
- `_source_outcome_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 259) — Provenance-outcome associations as additive suggestions (§11, ING M8).
- `_graph_edit_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 287) — Graph-editor notices (§8/§12): ambiguous edge direction + queued restructure requests.
- `_probe_pool_empty_notices(vault, repository) -> list[_Notice]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 317) — Empty diagnostic-probe pools, surfaced as a maintenance need rather than skipped.
- `_prompt_sha256(prompt: str) -> str` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 350)
- `_transcription_title(label: str | None, practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 440)
- `_transcription_action(practice_item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 444)
- `_resolve_reworded_transcription_reports(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/ops/maintenance_feed.py), line 448) — Resolve every live report whose item no longer has the wording reported (a reword, a re-import or the item gone).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`; statically calls `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `report_transcription_mismatch`; statically calls `report_transcription_mismatch`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`; statically calls `dismiss_notice`, `generate_maintenance_feed`, `snooze_notice`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/source_outcome_analytics|learnloop.content.sources.source_outcome_analytics]] — imports `analyze_source_outcomes`, `source_outcome_notices`; calls `analyze_source_outcomes`, `source_outcome_notices`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `ambiguous_edge_direction_notices`, `restructure_request_notices`; calls `ambiguous_edge_direction_notices`, `restructure_request_notices`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `PROBE_POOL_EMPTY_NOTICE_TYPE`, `held_probe_pool_notice_keys`, `probe_pool_empty_conditions`, `probe_pool_empty_notice_payload`; calls `held_probe_pool_notice_keys`, `probe_pool_empty_conditions`, `probe_pool_empty_notice_payload`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_ambiguous_edge_direction_notice_carries_evidence`
  - `test_ambiguous_edge_direction_omits_sparse_evidence`
  - `test_queue_restructure_request_records_and_surfaces_in_feed`
  - `test_resolve_edge_direction_flip_files_proposal_and_resolves_notice`
  - `test_resolve_edge_direction_keep_resolves_without_filing`
  - `test_resolve_edge_direction_retire_removes_and_can_restore`
- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — direct import
  - `test_dismiss_and_snooze_do_not_change_curriculum`
  - `test_maintenance_notice_aging_policies`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_a_notice_raised_before_placement_is_held_not_resolved`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_maintenance_feed_sustains_and_auto_resolves_the_notice`
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_the_report_is_one_notice_that_counts_keeps_the_text_and_reopens`
  - `test_the_report_resolves_when_the_wording_changes_and_holds_until_then`
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_feed_refresh_reading_before_a_report_never_overwrites_it`
  - `test_a_reworded_card_resolves_but_a_report_on_the_new_wording_meanwhile_is_kept`
  - `test_the_feed_upsert_of_other_notices_is_unchanged`
  - `test_two_reports_on_two_connections_both_count`
- [tests/test_source_outcome_analytics.py](../../../../../../tests/test_source_outcome_analytics.py) — direct import
  - `test_actionable_associations_flow_into_maintenance_feed`

## Modification guidance

- Make changes here when the responsibility remains maintenance feed within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/maintenance_feed.py](../../../../../../src/learnloop/ops/maintenance_feed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
