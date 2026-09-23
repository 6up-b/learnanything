---
title: "learnloop.substrate.dataset"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/dataset.py"
source_paths:
  - "src/learnloop/substrate/dataset.py"
source_commit: "2a218baead1b47a34debd9464568936ff58f1c28"
source_commit_timestamp: "2026-09-23T15:42:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.dataset module"
  - "src/learnloop/substrate/dataset.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.dataset`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.dataset` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Reproducible local datasets from SQLite backups, never a live projection.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py) |
| Source lines | 694 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2a218baead1b47a34debd9464568936ff58f1c28` |
| Commit timestamp | `2026-09-23T15:42:12-04:00` |

## Public API

- `parse_embargo(text: str) -> timedelta` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 111) — Parse an embargo duration such as `7d`, `36h`, `90m`, `30s` or `0`.
- `split_policy_parameters(policy: str, embargo: timedelta=DEFAULT_EMBARGO) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 133) — The parameters a policy actually uses, for the manifest and quality report.
- `split_policy_description(policy: str) -> str` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 142) — The split rule and the evaluation claim it does and does not support.
- `split_assignments(attempts: list[dict[str, Any]], contracts: list[dict[str, Any]], source_links: Iterable[dict[str, Any]]=(), *, policy: str=DEFAULT_SPLIT_POLICY, embargo: timedelta=DEFAULT_EMBARGO) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 378) — Assign attempts to train, validation and test under a named policy.
- `split_counts(assignments: Iterable[dict[str, Any]], policy: str, embargo: timedelta=DEFAULT_EMBARGO) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 403) — Rows per split label, named by the policy that produced them.
- `outcome_records(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 489)
- `export_dataset(sqlite_path: Path, output: Path, *, split_policy: str=DEFAULT_SPLIT_POLICY, embargo: timedelta=DEFAULT_EMBARGO) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 644) — Back up `sqlite_path` into a new `output` directory and export from the copy.

### Module constants

- `_CAPTURED_WORKFLOW_TABLES` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 25)
- `DATASET_VERSION` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 37)
- `_SPLIT_ATTEMPT_COLUMNS` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 39)
- `_SOURCE_LINK_ENTITY_TYPES` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 40)
- `SPLIT_POLICIES` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 75)
- `DEFAULT_SPLIT_POLICY` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 76)
- `DEFAULT_EMBARGO` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 77)
- `_EMBARGO_UNITS` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 79)
- `_EMBARGO_PATTERN` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 80)
- `_SPLIT_RULES` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 82)
- `_UNVERSIONED_SPLIT_NOTE` ([src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py), line 106)

## Internal implementation anchors

- `_json(value: Any) -> str` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 43)
- `_hash_file(path: Path) -> str` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 47)
- `_fsync_file(path: Path) -> None` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 52)
- `_fsync_directory(path: Path) -> None` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 57)
- `_timestamp(value: str) -> datetime` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 65)
- `_check_split_policy(policy: str, embargo: timedelta) -> None` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 126)
- `_contract_lineage(contract: dict[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 148) — Content-lineage keys an assessment contract records.
- `_source_link_lineage(link: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 168) — A cited source span, qualified by its source so locators cannot collide.
- `class _LineageGroups` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 176) — Union-find whose component root is the lexicographically smallest key.
- `_chronological_cutoffs(times: list[datetime]) -> tuple[datetime | None, datetime | None]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 200) — The 70% and 85% timestamps.
- `_temporal_cutoffs(times: list[datetime]) -> tuple[datetime | None, datetime | None]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 210) — The 70% and 85% timestamps of one learning object's distinct times.
- `_utc_timestamp(value: str) -> datetime` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 224) — A timestamp in UTC, reading a value without an offset as UTC rather than as the host's local time, so assignments do not depend on the host zone.
- `_chronological_bucket(when: datetime, first: datetime | None, second: datetime | None) -> str` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 233)
- `_content_lineage_by_attempt(attempts: list[dict[str, Any]], contracts: list[dict[str, Any]], source_links: Iterable[dict[str, Any]]) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 241) — Each attempt's content-lineage keys from its item and learning object.
- `_is_eligible(attempt: dict[str, Any], lineage: set[str]) -> bool` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 265) — Only human attempts whose content can be traced define cutoffs and buckets.
- `_ineligible_label(attempt: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 270)
- `_chronological_order(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 276)
- `_assignment_row(attempt: dict[str, Any], group_hash: str, chronological: str, lineage: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 280)
- `_content_family_splits(attempts: list[dict[str, Any]], lineage_by_attempt: dict[str, set[str]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 290) — Whole content families per global chronological bucket.
- `_temporal_splits(attempts: list[dict[str, Any]], lineage_by_attempt: dict[str, set[str]], embargo: timedelta) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 330) — Chronological splits within each learning object, with an embargo.
- `_index_by(values: Iterable[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 420)
- `_cold_receipt_status(derived: dict[str, Any], observed: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 427) — Label status of one final coldness receipt.
- `_r_next(source: dict[str, Any], future: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 449)
- `_f_label(adjudication: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 477)
- `_write_jsonl(target: Path, values: Iterable[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 567) — Write, hash and fsync one artifact in a single pass.
- `_write_manifest(output: Path, manifest: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 582) — Publish the manifest atomically, after every artifact is durable.
- `_ordered_table_rows(connection: sqlite3.Connection, table: str) -> Iterable[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 597) — Stream a table in a stable order rather than loading it whole.
- `_split_source_links(connection: sqlite3.Connection, tables: set[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 605)
- `_export_snapshot(snapshot: Path, output: Path, *, split_policy: str, embargo: timedelta) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 613)
- `_export_into(sqlite_path: Path, output: Path, *, split_policy: str, embargo: timedelta) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/dataset.py), line 667)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `DEFAULT_SPLIT_POLICY`, `export_dataset`, `parse_embargo`; statically calls `export_dataset`, `parse_embargo`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] — imports `TABLE_ROLES`, `TableRole`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `COLLECTION_VERSION`, `LABEL_VERSION`, `retention_exclusions`; calls `retention_exclusions`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `inspect_collection`, `rows`, `table_names`; calls `inspect_collection`, `rows`, `table_names`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `hashlib`, `json`, `os`, `pathlib`, `re`, `shutil`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_cold_receipt_status_keeps_unscorable_and_dispositions_distinct`
  - `test_content_policy_quarantines_learning_objects_revisited_across_cutoffs`
  - `test_content_split_on_a_copy_of_the_linear_algebra_fixture_finds_real_families`
  - `test_dataset_export_cli_reports_sqlite_errors_and_removes_partial_output`
  - `test_exact_offer_survives_refresh_recovery_and_dataset_export`
  - `test_export_preserves_censored_repair_disposition_as_distinct_from_failure`
  - `test_failed_export_leaves_no_manifest_and_no_partial_directory`
  - `test_independent_content_families_both_land_in_splits`
  - `test_manifest_is_published_by_atomic_rename`
  - `test_non_human_attempts_do_not_move_a_learning_objects_temporal_cutoffs`
  - `test_non_human_attempts_do_not_quarantine_a_human_family`
  - `test_parse_embargo_reads_durations`
  - `test_parse_embargo_refuses_other_text`
  - `test_production_lane_and_live_backup_preserve_committed_state`
  - `test_scored_item_text_is_snapshotted_once_per_revision_and_exported`
  - `test_source_spans_join_learning_objects_into_one_family`
  - `test_split_assignments_are_independent_of_input_order`
  - `test_split_assignments_never_join_families_through_a_surface_format_label`
  - `test_split_assignments_quarantine_content_families_across_time_boundaries`
  - `test_split_assignments_refuse_an_unknown_policy_or_negative_embargo`
  - `test_temporal_cutoffs_use_exact_integer_percentiles`
  - `test_temporal_embargo_boundary`
  - `test_temporal_policy_default_embargo_quarantines_holdouts_near_training`
  - `test_temporal_policy_keeps_equal_timestamps_in_one_bucket`
  - `test_temporal_policy_splits_each_learning_objects_own_history`
  - `test_temporal_split_on_a_copy_of_the_linear_algebra_fixture_has_holdouts`
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_head_163_database_upgrades_to_snapshots_and_fk_free_adjudications`

## Modification guidance

- Change dataset policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/dataset.py](../../../../../../src/learnloop/substrate/dataset.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
