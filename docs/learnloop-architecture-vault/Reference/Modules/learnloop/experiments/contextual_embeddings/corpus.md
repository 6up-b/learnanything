---
title: "learnloop.experiments.contextual_embeddings.corpus"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/corpus.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/corpus.py"
source_commit: "34d2068e151f70ab52d394226c810fdc208b9dee"
source_commit_timestamp: "2026-10-21T14:16:05-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.corpus module"
  - "src/learnloop/experiments/contextual_embeddings/corpus.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.corpus`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.corpus` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's corpus: copies, the read-only inventory, policy, candidate units, windows.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py) |
| Source lines | 975 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `34d2068e151f70ab52d394226c810fdc208b9dee` |
| Commit timestamp | `2026-10-21T14:16:05-04:00` |

## Public API

- `class PolicyUnavailable(RuntimeError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 82) — The material policy could not be computed: nothing is built (fail closed).
- `class CopyContainment(ValueError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 97) — A copy's root or database is not contained in the designated copy; nothing was opened (fix round 4, High 1).
- `contained_root(root: Path, *, local: bool=False) -> Path` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 102) — The copy root, resolved, refused unless it is a real directory (not a symbolic link; with ``local``, under a ``fixtures-local`` directory with no symbolic link on its path below it) with a regular ``learnloop.toml``.
- `contained_database(root: Path, config: Any) -> Path` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 126) — The copy's database path, BEFORE anything opens it: the configured ``storage.sqlite_path`` must be relative, must not escape the copy, must not pass through a symbolic link and must resolve inside the copy root (an absolute path kept by copying could name the owner's database, w…
- `prepare_copies(sources: Sequence[Path], destination_root: Path, *, label: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 177) — Back up each source vault into ``destination_root/<name>-<label>``.
- `is_wal(database: Path) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 207) — Whether a database file's header names the WAL format (read without SQLite).
- `to_rollback_journal(database: Path) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 215) — Put a fresh copy in rollback-journal mode (its companion files go): a read-only open of a WAL database creates ``-wal``/``-shm`` files and rewrites the shared-memory index, which would be a write to the copy.
- `class CopyHandle` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 231) — A vault copy opened read-only.
  - `label(self) -> str` (line 240; public)
- `open_copy(root: Path, *, load_environment: bool=False) -> CopyHandle` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 244) — The copy's vault (no settings or dotenv unless asked) and a read-only, never-migrated repository.
- `alias(kind: str, value: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 269) — A stable public alias (reports never carry private ids, titles or paths).
- `class ExtractionInfo` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 276)
  - `public(self) -> dict[str, Any]` (line 288; public)
- `extraction_infos(handle: CopyHandle) -> dict[str, ExtractionInfo]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 294)
- `class PolicySnapshot` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 317) — What a model may never read, by key, with the reason.
  - `verdict(self, extraction_id: str, span_id: str) -> str | None` (line 325; public)
  - `permitted(self, extraction_id: str, span_id: str) -> bool` (line 330; public)
  - `counts(self) -> dict[str, int]` (line 333; public)
- `policy_snapshot(handle: CopyHandle, infos: Mapping[str, ExtractionInfo]) -> PolicySnapshot` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 340) — Exam/held-out (D12) and solution/assessment-lane material, fail closed.
- `class ArtifactDependency` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 364) — What an artifact (window, vector, header, label, packet) was built from.
  - `as_dict(self) -> dict[str, Any]` (line 372; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> ArtifactDependency` (line 377; public)
- `stale_reasons(dependency: ArtifactDependency, snapshot: PolicySnapshot) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 382) — Why an artifact may no longer be used (empty: still valid).
- `invalidate(artifacts: Mapping[str, ArtifactDependency], snapshot: PolicySnapshot) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 396) — Every stale artifact id with its reasons (fresh ones are absent).
- `class Member` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 411)
- `class CandidateUnit` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 418)
  - `keys(self) -> tuple[SpanKey, ...]` (line 437; public)
  - `public(self) -> dict[str, Any]` (line 440; public)
- `split_offsets(text: str, max_tokens: int) -> list[tuple[int, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 461) — Deterministic ``[start, end)`` pieces of ``text`` within ``max_tokens``: cut at the last sentence or line boundary that fits, else the last space, else a hard cut.
- `permitted_titles(extraction_id: str, blocks: Sequence[BlockRow], titles: Mapping[str, str], policy: PolicySnapshot) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 517) — ``titles`` (``{extractor block id: header text}``) with every header the policy withholds, or that no current block anchors, replaced by ``WITHHELD_HEADING``: a protected heading never reaches a permitted descendant's section path (fix round 4, High 5).
- `build_units(extraction: ExtractionInfo, blocks: Sequence[BlockRow], titles: Mapping[str, str], policy: PolicySnapshot) -> list[CandidateUnit]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 543) — The common candidate map of one extraction (deterministic).
- `class Window` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 661)
- `build_windows(units: Sequence[CandidateUnit], *, window_tokens: int=pins.WINDOW_TOKENS) -> list[Window]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 674) — Section-first packing within one extraction's policy segment; no overlap; every unit in exactly one window.
- `whole_segment_windows(units: Sequence[CandidateUnit], *, limit_tokens: int) -> list[Window]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 721) — One window per permitted segment that fits ``limit_tokens`` whole (the secondary whole-source arm); a segment that does not fit gets none.
- `assert_partition(units: Sequence[CandidateUnit], windows: Sequence[Window]) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 742) — Every unit in exactly one (non-whole-segment) window.
- `dependency_map(units: Sequence[CandidateUnit], text: ExtractionText, policy: PolicySnapshot) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 759) — Each unit's numbered references resolved to the units holding them (same extraction only; a withheld target is recorded, never followed).
- `support_outside_windows(dependencies: Mapping[str, Mapping[str, Any]], windows: Sequence[Window]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 795) — How many resolved dependencies fall outside their unit's grouped window.
- `families(infos: Mapping[str, ExtractionInfo], *, vault_label: str) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 822) — ``{source_id: family_id}``: alternate editions and overlapping copies (same source bytes or the same title stem) share a family.
- `reserve_families(family_ids: Iterable[str], *, share: float, seed: int=pins.SEED) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 841) — ``{family: "development" | "reserved"}``, fixed before any question is written.
- `class CorpusSnapshot` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 855)
  - `unit(self, unit_id: str) -> CandidateUnit` (line 870; public)
  - `_units_by_id(self) -> dict[str, CandidateUnit]` (line 873; internal)
  - `unit_dependency(self, unit: CandidateUnit) -> ArtifactDependency` (line 880; public)
  - `window_dependency(self, window: Window) -> ArtifactDependency` (line 885; public)
  - `inventory(self) -> dict[str, Any]` (line 893; public) — Aggregate inventory: counts and token sizes, no text, ids aliased.
- `build_snapshot(handle: CopyHandle, *, reserve_share: float=0.0, whole_limits: Mapping[str, int] | None=None) -> CorpusSnapshot` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 944) — The frozen corpus of one copy (read-only; deterministic).

### Module constants

- `LOCAL_ROOT_NAME` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 71)
- `EXPERIMENT_DIR` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 72)
- `FORBIDDEN_SOURCE_NAMES` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 74)
- `_EQUATION_TYPES` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 75)
- `_CAPTION_TYPES` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 76)
- `_SPLIT_AT` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 77)
- `_EQ_IN` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 511)
- `WITHHELD_HEADING` ([src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 514)

## Internal implementation anchors

- `_sha(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 86)
- `_inside_local_root(path: Path) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 93)
- `_rebase_database(source: Path, target: Path) -> Path | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 149) — A source whose database lives outside its own tree (an absolute or escaping ``storage.sqlite_path``) is backed up INTO the copy and the copy's toml is rewritten to the relative path, so the copy never points at the source's database.
- `_kind(block: BlockRow) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 445)
- `_is_content(block: BlockRow) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 449)
- `_bare_equation(block: BlockRow) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 453)
- `_unit(extraction: ExtractionInfo, section: tuple[str, ...], segment: int, members: list[Member], texts: list[str], kind: str, label: str | None, lead: str | None) -> CandidateUnit` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 496)
- `_path_elements(block: BlockRow | None) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 533)
- `_chunk_tokens(unit: CandidateUnit) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 670)
- `_title_stem(title: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 816)
- `_count(values: Iterable[str]) -> dict[str, int]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py), line 937)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `prepare_copies`; statically calls `prepare_copies`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `CandidateUnit`, `CorpusSnapshot`, `alias`; statically calls `alias`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `CorpusSnapshot`, `_inside_local_root`; statically calls `_inside_local_root`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `CopyHandle`, `CorpusSnapshot`, `_inside_local_root`, `build_snapshot`, `open_copy`, `to_rollback_journal`; statically calls `_inside_local_root`, `build_snapshot`, `open_copy`, `to_rollback_journal`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `_inside_local_root`; statically calls `_inside_local_root`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `_inside_local_root`, `build_snapshot`, `open_copy`; statically calls `_inside_local_root`, `build_snapshot`, `open_copy`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `_inside_local_root`; statically calls `_inside_local_root`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/retrieval|learnloop.experiments.contextual_embeddings.retrieval]] — imports `CandidateUnit`, `CorpusSnapshot`, `Window`, `alias`; statically calls `alias`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `CopyHandle`, `CorpusSnapshot`, `_inside_local_root`, `alias`, `build_snapshot`, `open_copy`; statically calls `_inside_local_root`, `alias`, `build_snapshot`, `open_copy`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `CopyHandle`, `CorpusSnapshot`, `PolicySnapshot`, `_inside_local_root`, `contained_database`, `contained_root`; statically calls `CopyHandle`, `_inside_local_root`, `contained_database`, `contained_root`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `backup_database`, `copy_tree_with_databases`; calls `backup_database`, `copy_tree_with_databases`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `BlockRow`, `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`, `extraction_fingerprint`, `extraction_units`, `section_header_titles`; calls `extraction_blocks`, `extraction_fingerprint`, `extraction_units`, `section_header_titles`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`, `token_estimate`, `token_upper_bound`; calls `token_estimate`, `token_upper_bound`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `lead_role`, `numbered_label`, `numbered_references`; calls `lead_role`, `numbered_label`, `numbered_references`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`, `model_reader_withheld`; calls `current_extractions`, `model_reader_withheld`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `section_path`; calls `section_path`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `ExtractionText`; calls `ExtractionText`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `re`, `typing`
- Third party: `tomlkit`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_bank.py](../../../../../../../tests/test_e0_bank.py) — direct import
- [tests/test_e0_corpus.py](../../../../../../../tests/test_e0_corpus.py) — direct import
  - `test_a_later_held_out_mark_invalidates_dependent_artifacts`
  - `test_families_group_editions_and_reservation_is_fixed_before_questions`
  - `test_open_copy_is_read_only_and_never_migrates`
  - `test_policy_failure_fails_closed`
  - `test_prepare_copies_uses_the_backup_api_under_fixtures_local_only`
  - `test_re_extraction_invalidates_by_fingerprint`
  - `test_split_offsets_cover_text_exactly_and_respect_the_bound`
  - `test_wal_copies_are_converted_and_a_wal_copy_is_refused`
  - `test_whole_source_windows_only_when_the_whole_segment_fits`
  - `test_windows_partition_units_within_the_token_bound`
- [tests/test_e0_delivery.py](../../../../../../../tests/test_e0_delivery.py) — direct import
  - `test_a_source_that_does_not_fit_runs_the_named_fallback_never_a_truncation`
  - `test_d0_and_d1_reproduce_the_production_reader_delivery`
  - `test_d2_is_the_whole_permitted_section_and_d3_the_whole_permitted_source`
  - `test_retrieved_d0_and_d1_deliver_the_same_initial_evidence`
- [tests/test_e0_dry_run.py](../../../../../../../tests/test_e0_dry_run.py) — direct import
  - `test_split_strata_is_deterministic_and_complete`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_r0_runs_find_sources_on_a_service_copy_and_the_frozen_copy_is_untouched`
  - `test_resume_pays_only_for_what_is_missing`
  - `test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_a_permitted_block_containing_a_withheld_blocks_text_is_embedded`
  - `test_an_unredacted_service_copy_is_refused_before_any_request`
  - `test_the_earlier_ledgers_admissions_stay_visible_so_a_known_truncation_is_not_resent`
  - `test_the_guard_still_refuses_withheld_text_even_past_its_first_characters`
  - `test_the_two_passes_stay_independent_requests_in_different_orders`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f15_provider_limits_use_a_guaranteed_upper_bound`
  - `test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy`
  - `test_f3_a_resolved_client_that_differs_from_its_pin_is_refused_before_any_request`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h1_a_frozen_copy_naming_an_outside_or_linked_database_is_refused`
  - `test_h1_a_service_copy_naming_an_outside_database_is_refused_before_any_open`
  - `test_h1_prepare_rebases_a_relocated_database_into_the_copy`
  - `test_h2_an_overcharged_hosted_response_stops_the_paid_run_at_once`
  - `test_h5_a_heading_marked_later_invalidates_the_units_built_under_it`
  - `test_h5_a_withheld_heading_never_reaches_a_permitted_descendant`
  - `test_h6_the_production_protection_rejects_an_unknown_item_question`
  - `test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli`
  - `test_m11_a_charged_but_unrecorded_request_is_blocked_never_resent`
  - `test_m11_a_settled_response_is_recovered_from_the_receipts`
  - `test_m11_concurrent_workers_send_one_request_and_a_known_failure_may_retry`
  - `test_m12_a_provider_failure_records_incomplete_work_instead_of_aborting`
  - `test_m13_an_arm_that_fails_every_logged_question_stops_verdicts`
  - `test_m9_the_qwen_route_is_canaried_before_its_service_backfill`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_a_role_call_goes_through_the_messages_api_transport`
  - `test_each_model_id_is_canaried_before_bulk_work_and_a_wrong_model_stops_the_run`
- [tests/test_e0_review_round6.py](../../../../../../../tests/test_e0_review_round6.py) — direct import
  - `test_m1_no_e0_vault_load_reads_settings_env_or_a_copy_dotenv`
- [tests/test_e0_review_round7.py](../../../../../../../tests/test_e0_review_round7.py) — direct import
  - `test_a_canary_failure_reaches_the_contracts_result_with_its_reason`
  - `test_the_three_perplexity_canaries_pass_against_the_documented_contract`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_a_non_item_failure_still_stops_the_labels`
  - `test_a_refused_backfill_batch_is_reported_safely_and_sent_once_more`
  - `test_a_single_ref_that_still_truncates_is_counted_missing_not_a_stop`
  - `test_a_truncated_window_is_split_until_every_unit_has_its_context`
  - `test_one_questions_unusable_labels_skip_that_question_only`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends`
- [tests/test_e1_supplement.py](../../../../../../../tests/test_e1_supplement.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains corpus within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/corpus.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/corpus.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
