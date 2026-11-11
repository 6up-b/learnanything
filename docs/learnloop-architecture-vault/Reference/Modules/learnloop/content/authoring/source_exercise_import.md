---
title: "learnloop.content.authoring.source_exercise_import"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/source_exercise_import.py"
source_paths:
  - "src/learnloop/content/authoring/source_exercise_import.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.source_exercise_import module"
  - "src/learnloop/content/authoring/source_exercise_import.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.source_exercise_import`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.source_exercise_import` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Importing textbook exercises with checked answer keys (spec_source_practice_and_probes_v1 §7.2-§7.4).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py) |
| Source lines | 1718 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SolutionJudgment(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 169)
- `class SolutionMatch(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 175)
- `selection_for_region(repository: Repository, extraction_id: str, span_ids: Sequence[str], *, vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 189) — A Reader-style selection over whole blocks: ``start = 0``, ``end = len(text)``.
- `solution_regions(connection, extraction_id: str) -> list[tuple[tuple[str, ...], str, int | None]]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 212) — ``(span ids, text, page)`` of every solution region of one extraction.
- `find_book_solution(vault: LoadedVault, repository: Repository, *, extraction_id: str, label: str, statement: str, client: Any | None=None, owner_id: str='', deadline: float | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 244) — The passage of the exercise's own source that solves it, or a typed absence.
- `class LadderResult` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 316)
  - `verified(self) -> bool` (line 325; public)
- `import_caps(vault: LoadedVault) -> SpendCaps` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 342) — One import's bound: the money cap is the owner's (None, the default: none; the daily guard still bounds it); the call and token counts only keep a runaway loop bounded (never a learning decision).
- `daily_cap_reason(vault: LoadedVault, repository: Repository, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 385) — ``source_service.max_daily_cost_usd``: the service's metered spend today (UTC).
- `authoring_admission(vault: LoadedVault, repository: Repository, client: Any, *, owner_id: str) -> Callable[[str, type], Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 413) — Admit the authoring request under the import's caps before it is sent.
- `plan_import_cost(vault: LoadedVault, *, statement_chars: int, imports: int=1) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 482) — A numerical upper-bound estimate of ``imports`` imports, for dry runs.
- `run_key_ladder(vault: LoadedVault, repository: Repository, *, subject_id: str, stem: str, reference: str, solution: Mapping[str, Any] | None, cited_quote: str='', clients: Mapping[str, Any] | None=None, run_id: str | None=None) -> LadderResult` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 538) — Check one key and label it honestly (the table in §7.3).
- `record_key_check(repository: Repository, *, item: PracticeItem, result: LadderResult, trigger: str, started_at: str, import_id: str | None=None, content_hash: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 666) — One append-only check row bound to the content that was checked.
- `draft_content_hash(draft: AuthoredDraft, extra_payload: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 688) — ``reference_content_hash`` of a draft as it will be written: the content the ladder checks before anything reaches the vault (Codex re-review F1).
- `class CheckClaim` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 736) — A lease on one import's key check: its key, this worker and its epoch.
- `check_claim_key(import_id: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 744)
- `claim_check(repository: Repository, import_id: str, content_hash: str | None) -> tuple[str, CheckClaim | None]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 748) — Atomically claim an import's check: (``claimed``, claim), (``held``, None) while another worker's lease is live, or (``done``, None) once completed.
- `release_check(repository: Repository, claim: CheckClaim | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 768) — Give an unfinished claim back (the check ended without a row to fence).
- `attach_to_matching_family(vault: LoadedVault, repository: Repository, item_id: str, *, clients: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 855) — Join a family on the LO whose every member PF's family judge calls the same target.
- `screen_profiles(draft: AuthoredDraft, screen: Mapping[str, Any], repository: Repository) -> tuple[AuthoredDraft, dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 953) — Write a screened exercise's persisted screen onto its draft (spec §8.4).
- `import_source_exercise(root: Path, repository: Repository, *, extraction_id: str, span_ids: Sequence[str], caller: str, proposal_id: str | None=None, clients: Mapping[str, Any] | None=None, time_box_seconds: float | None=None, validate: Callable[[AuthoredDraft], Mapping[str, Any]] | None=None, need_id: str | None=None, learning_object_hint: str | None=None, label: str | None=None, import_id: str | None=None, clock: Clock | None=None, screen: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1094) — Import one textbook exercise region as a practice item, its key checked.
- `resume_import(root: Path, repository: Repository, import_id: str, *, clients: Mapping[str, Any] | None=None, clock: Clock | None=None, run_pending: bool=True) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1432) — Complete what a dead process left of one import, from durable state (F5).
- `pending_import_checks(repository: Repository, *, include_held: bool=False) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1507) — Imports whose verification is incomplete (cheap SQL).
- `recover_import_checks(root: Path, repository: Repository, *, clients: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1554) — Startup recovery: resume every import a dead process left incomplete.
- `verify_item_key(root: Path, repository: Repository, item_id: str, *, trigger: str, clients: Mapping[str, Any] | None=None, clock: Clock | None=None, import_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1578) — Run the ladder over an existing exercise import's CURRENT content (§7.3a).
- `record_reader_import(root: Path, repository: Repository, result: Mapping[str, Any], *, extraction_id: str, span_ids: Sequence[str], source_id: str | None, revision_id: str | None, clock: Clock | None=None, pending_check: bool=False) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1660) — The Reader's import gets a ``source_exercise_imports`` row per written item (``caller = reader``, ``key_status = model_answer``); the item is unchanged (G5).

### Module constants

- `LADDER_VERSION` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 124)
- `SOLUTION_MATCH_PROMPT_VERSION` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 125)
- `SOLUTION_CANDIDATES` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 127)
- `SOLUTION_PASSAGE_CHARS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 128)
- `MIN_QUOTE_WORDS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 131)
- `OWNER_KIND` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 132)
- `CALLERS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 133)
- `TRIGGERS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 134)
- `PROCESS_TOKEN` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 137)
- `CHECK_CLAIM_TASK` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 144)
- `CHECK_LEASE_SECONDS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 145)
- `CHECK_HEARTBEAT_SECONDS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 146)
- `PRICE_SETTING` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 147)
- `_SOLUTION_INSTRUCTIONS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 154)
- `_BOOK_SOLUTION_INSTRUCTIONS` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 162)
- `SOLUTION_MATCH_TASK` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 180)
- `SCREEN_FATAL_MAX_GRADE` ([src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 946)

### Explicit exports

`__all__` declares:

- `CALLERS`
- `LADDER_VERSION`
- `LadderResult`
- `SOLUTION_MATCH_PROMPT_VERSION`
- `SOLUTION_MATCH_TASK`
- `SolutionMatch`
- `attach_to_matching_family`
- `authoring_admission`
- `screen_profiles`
- `CHECK_CLAIM_TASK`
- `CheckClaim`
- `check_claim_key`
- `claim_check`
- `draft_content_hash`
- `release_check`
- `find_book_solution`
- `import_caps`
- `import_source_exercise`
- `plan_import_cost`
- `pending_import_checks`
- `record_key_check`
- `record_reader_import`
- `recover_import_checks`
- `resume_import`
- `run_key_ladder`
- `selection_for_region`
- `solution_regions`
- `verify_item_key`

## Internal implementation anchors

- `class _RecordingCaller(PFCaller)` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 329) — A ``PFCaller`` that remembers every ledger id it appends.
- `_quote_in(quote: str, text: str) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 352)
- `_normalized_answer(value: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 359)
- `_roles(vault: LoadedVault, clients: Mapping[str, Any]) -> Callable[[str], list[RoleClient]]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 363)
- `_metered_without_price(vault: LoadedVault, role: Callable[[str], list[RoleClient]], names: Sequence[str]) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 374)
- `_method_judge(vault: LoadedVault, clients: Mapping[str, Any]) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 399) — The one-time statement judge (``learnloop.content.proposals.
- `_insert_check(connection: Any, *, item_id: str, content_hash: str, result: LadderResult, trigger: str, started_at: str, import_id: str | None, clock: Clock | None, legacy_identity: bool=False) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 653)
- `_ladder_record(result: LadderResult, started_at: str, content_hash: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 677) — A ladder's result as the import row keeps it (durable before the write, F5), bound to the hash of the draft it verified (Codex re-review F1).
- `_ladder_from_record(record: Mapping[str, Any]) -> LadderResult` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 697)
- `_without_pending(verification: Mapping[str, Any], **extra: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 702)
- `_complete_check(connection: Any, *, import_id: str | None, item_id: str, content_hash: str, result: LadderResult, trigger: str, started_at: str, clock: Clock | None, edited: bool=False, legacy_identity: bool=False) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 706) — The check row and the import's completion, in the caller's ONE transaction (F5).
- `_lease_now() -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 729) — Wall-clock time for leases: process liveness, never the vault's clock.
- `_heartbeat(repository: Repository, claim: CheckClaim | None) -> Iterator[None]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 782) — Renew the claim's lease while the ladder runs (stops when it is lost).
- `_fenced_complete(repository: Repository, claim: CheckClaim | None, *, import_id: str | None, item_id: str, content_hash: str, result: LadderResult, trigger: str, started_at: str, clock: Clock | None, edited: bool=False) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 809) — The check row and the import's completion, only while the claim holds.
- `_clear_pending(repository: Repository, import_id: str, claim: CheckClaim | None, *, clock: Clock | None, **fields: Any) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 832) — Clear an import's pending marker (with ``fields``), only while the claim holds.
- `_plain_text(value: Any) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 949)
- `class _Pending` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1026) — A ladder still running when the time box closed (D1): it records its check against the content it was given once both it and the write finish.
- `_finish_pending(repository: Repository, pending: _Pending, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1041)
- `_run_time_boxed(function: Callable[[], LadderResult], seconds: float | None, pending: _Pending, on_done: Callable[[], None]) -> LadderResult | None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1062)
- `_import_source_exercise(root: Path, repository: Repository, *, vault: LoadedVault, extraction_id: str, span_ids: Sequence[str], caller: str, proposal_id: str | None, clients: Mapping[str, Any] | None, time_box_seconds: float | None, validate: Callable[[AuthoredDraft], Mapping[str, Any]] | None, need_id: str | None, learning_object_hint: str | None, label: str | None, import_id: str | None, clock: Clock | None, screen: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1144)
- `_commit_written(repository: Repository, import_id: str, item: PracticeItem, *, clock: Clock | None) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1387) — The written status and, when the ladder finished, its check row: one transaction, so neither exists without the other (F5).
- `_resume_pending(root: Path, repository: Repository, vault: LoadedVault, row: Mapping[str, Any], pending: Mapping[str, Any], *, clients: Mapping[str, Any] | None, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1471)
- `_lease_wait_seconds(repository: Repository, import_ids: Sequence[str]) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1537) — Seconds until the earliest live lease among ``import_ids`` lapses, or None.
- `_ladder_for_item(vault: LoadedVault, repository: Repository, item: PracticeItem, *, clients: Mapping[str, Any] | None, clock: Clock | None) -> tuple[LadderResult, str]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1597)
- `_verify_item_key(root: Path, repository: Repository, vault: LoadedVault, item_id: str, *, trigger: str, clients: Mapping[str, Any] | None, clock: Clock | None, import_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1613)
- `_cited_quote(expected: str, solution: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py), line 1647) — For an existing key, the part of the solution passage that repeats it, if any.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `PRICE_SETTING`, `module`; statically calls `import_source_exercise`, `record_reader_import`, `verify_item_key`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `import_source_exercise`, `plan_import_cost`, `verify_item_key`; statically calls `import_source_exercise`, `plan_import_cost`, `verify_item_key`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `import_source_exercise`; statically calls `import_source_exercise`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `CHECK_LEASE_SECONDS`, `pending_import_checks`, `recover_import_checks`; statically calls `pending_import_checks`, `recover_import_checks`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `verify_item_key`; statically calls `verify_item_key`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `selection_for_region`; statically calls `selection_for_region`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `PRICE_SETTING`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `record_model_calls`, `requested_reasoning_effort`, `single_request`; calls `content_key`, `generation_limit`, `observe_model_calls`, `record_model_calls`, `requested_reasoning_effort`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`; calls `TruncationRetry`, `output_budget`, `output_ceiling`, `reasoning_effort`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `job_grant`, `priced_by`, `unit_origin`, `unit_token`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `AuthoredDraft`, `ExerciseAuthoringError`, `author_exercises`, `write_draft`; calls `AuthoredDraft`, `ExerciseAuthoringError`, `author_exercises`, `write_draft`
- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `SandboxLimits`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_held_out_inventory`, `screen_practice_payload`; calls `build_held_out_inventory`, `screen_practice_payload`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `LazyStatementJudge`, `resolve_statement_judge`; calls `LazyStatementJudge`, `resolve_statement_judge`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `SCOPE_ONLY_REFUSAL`, `exam_material`, `reference_keys`, `scope_only_among`; calls `exam_material`, `reference_keys`, `scope_only_among`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `read_exercise_statement`, `selection_nodes`; calls `read_exercise_statement`, `selection_nodes`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `CLAIMED`, `DONE`, `HELD`, `claim_work`, `complete_claim`, `holds_claim`, `live_lease`, `release_claim`, `renew_claim`; calls `claim_work`, `complete_claim`, `holds_claim`, `live_lease`, `release_claim`, `renew_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `MAX_REGION_BLOCKS`, `REGION_BODY_HINTS`, `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`; calls `blocks_by_key`, `extraction_hint_rows`, `section_header_titles`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `KEY_IDENTITY`, `KEY_IDENTITY_FIELD`, `VERIFIED_STATUSES`, `import_row`, `insert_import`, `insert_key_check`, `update_import`; calls `import_row`, `insert_import`, `insert_key_check`, `update_import`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `FamilyVerdict`, `pair_passes`; calls `pair_passes`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `PFCaller`, `PFUnavailable`, `ROLE_TASKS`, `RoleClient`, `planned_role_clients`, `resolve_role_clients`; calls `PFCaller`, `planned_role_clients`, `resolve_role_clients`
- [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]] — imports `module`; calls `VerifierEnv`, `span_support`, `verify_reference`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`; calls `ListwiseTask`, `judge_listwise`, `listwise_caps`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `FRAMING_TOKENS`, `estimated_call_tokens`, `plan_route`; calls `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `effective_hint`, `extraction_scope`; calls `effective_hint`, `extraction_scope`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `POOL_HYBRID_RRF`, `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`, `service_spend_today`; calls `service_spend`, `service_spend_today`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `attach_to_family`, `family_item_input`; calls `attach_to_family`, `family_item_input`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `final_answer_text`; calls `final_answer_text`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `reference_content_hash`; calls `reference_content_hash`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `json`, `pathlib`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]], [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reference_gate_imports_helpers.py](../../../../../../../tests/reference_gate_imports_helpers.py) — direct import
- [tests/source_exercise_import_helpers.py](../../../../../../../tests/source_exercise_import_helpers.py) — direct import
- [tests/source_service_fakes.py](../../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_attach_to_family.py](../../../../../../../tests/test_attach_to_family.py) — direct import
  - `test_a_matching_family_is_joined_and_undone`
  - `test_attach_switch_off_skips_the_judge`
  - `test_no_matching_family_leaves_the_item_unfamilied`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_a_syllabus_exercise_is_refused_before_any_model_call`
  - `test_a_syllabus_made_during_the_import_writes_nothing`
  - `test_a_unit_override_leaves_the_rest_of_the_book_practice`
  - `test_the_one_write_refuses_a_syllabus_draft`
  - `test_the_reader_s_own_import_refuses_a_syllabus_before_any_model_call`
- [tests/test_discriminating_search.py](../../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_an_unverified_import_is_excluded_from_value_intents_but_not_practice`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_import_of_held_out_material_is_refused_before_any_model_call`
  - `test_an_import_rechecks_a_stale_proposal_before_any_paid_call`
- [tests/test_import_split_parity.py](../../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_author_then_write_writes_what_import_exercises_writes`
  - `test_selection_for_region_spans_whole_blocks`
  - `test_the_reader_job_records_an_import_row_and_leaves_the_item_unchanged`
- [tests/test_key_ladder_labels.py](../../../../../../../tests/test_key_ladder_labels.py) — direct import
  - `test_the_daily_cap_skips_the_ladder`
- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
  - `test_r2_the_shared_reader_lives_where_s1_and_the_reader_import_it`
- [tests/test_method_explicit_landing.py](../../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_a_check_recorded_on_main_still_verifies_and_the_fresh_check_label_needs_a_change`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_fix_l1_an_exercise_imports_own_authoring_route_is_held_to_its_price`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_startup_recovery_of_import_key_checks_never_uses_the_grant`
  - `test_the_edit_recheck_never_uses_the_grant`
  - `test_the_imports_time_boxed_key_check_carries_its_requests_grant`
  - `test_the_reader_imports_background_key_check_never_uses_the_grant`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
  - `test_a_named_solution_block_holding_part_of_the_statement_withholds_the_whole_crop`
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_a_block_on_the_imports_book_solution_spans_is_never_cropped`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_split_written_before_ownership_was_kept_withholds_the_free_crop`
  - `test_an_import_written_before_ownership_was_kept_shows_only_the_page`
- [tests/test_reference_check_binding.py](../../../../../../../tests/test_reference_check_binding.py) — direct import
  - `test_a_late_background_check_never_verifies_an_edit`
  - `test_an_edited_prompt_or_key_is_unverified_until_rechecked`
  - `test_the_edit_rpc_queues_a_recheck`
- [tests/test_reference_gate_imports.py](../../../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_a_later_verification_never_rewrites_earlier_attempts`
  - `test_a_regrade_never_raises_an_attempts_status`
  - `test_a_shadow_rebuild_at_the_tag_shows_zero_deltas`
  - `test_attempts_record_the_key_status_and_unverified_ones_never_certify`
  - `test_below_the_tag_the_gate_never_runs`
  - `test_the_projection_reads_the_recorded_status_on_replay`
- [tests/test_required_method_round3_rereview.py](../../../../../../../tests/test_required_method_round3_rereview.py) — direct import
  - `test_f1_a_ladder_result_committed_later_keeps_the_identity_it_was_computed_under`
- [tests/test_source_exercise_import.py](../../../../../../../tests/test_source_exercise_import.py) — direct import
  - `test_a_background_check_lost_with_its_process_is_resumed_at_startup`
  - `test_a_late_check_whose_lease_was_taken_over_records_nothing`
  - `test_a_live_check_in_another_process_is_never_taken_over`
  - `test_a_process_death_around_the_written_commit_never_loses_the_check`
  - `test_a_reader_imports_background_check_is_durable_too`
  - `test_a_resumed_check_never_verifies_content_edited_since`
  - `test_a_retried_written_import_restores_a_missing_check`
  - `test_overlapping_recoveries_run_one_check`
  - `test_recovery_never_binds_a_verdict_to_content_edited_before_the_commit`
  - `test_the_sidecar_resumes_pending_checks_at_startup`
  - `test_the_time_box_writes_checking_and_the_check_lands_later`
- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_an_imported_exercise_is_rechecked_for_independence_when_served`
  - `test_an_interactive_import_bounds_the_authored_drafts_own_duration`
- [tests/test_source_service_spend_envelopes.py](../../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
- [tests/test_sources_merge_composition.py](../../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_authoring_runs_at_the_policy_budget_and_retries_a_truncation_once_at_double`

## Modification guidance

- Change source exercise import policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/source_exercise_import.py](../../../../../../../src/learnloop/content/authoring/source_exercise_import.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
