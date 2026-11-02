---
title: "learnloop.source_retrieval.role_labeller"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/role_labeller.py"
source_paths:
  - "src/learnloop/source_retrieval/role_labeller.py"
source_commit: "e5d1ab4ddf9c8aaaaaeed2d6586089e960260ff1"
source_commit_timestamp: "2026-10-20T22:56:44-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.role_labeller module"
  - "src/learnloop/source_retrieval/role_labeller.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.role_labeller`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.role_labeller` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The owner-run batch role labeller (reader workbench RW4e; spec_reader_workbench_v1 §7.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py) |
| Source lines | 560 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e5d1ab4ddf9c8aaaaaeed2d6586089e960260ff1` |
| Commit timestamp | `2026-10-20T22:56:44-04:00` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 95)
- `class PassageRoles(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 99)
  - `_tolerate_roles(cls, data: Any) -> Any` (line 110; internal)
- `class RoleLabellerResult(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 114)
- `labeller_prompt(source_title: str | None, candidates: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 144)
- `agreed_verdicts(value: Any) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 240) — ``value`` with each judgment's verdict agreeing with its cleaned roles (fix round 5): ``roles`` when they are non-empty, else ``none``.
- `first_judgments(judgments: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 291) — Each ref's first judgment (the rule the ledger's insertion keeps).
- `eligible_passages(vault: LoadedVault, repository: Repository, extraction_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 323) — The source's passages a model may read, in reading order, with what was left out and why (counts) and which were already labelled.
- `run_budget(vault: LoadedVault, batches: int, passages: int, *, subscription: bool) -> SpendBudget` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 378) — One run's caps: every batch once and one retry each; the dollar cap (metered) ``roles.batch_max_cost_usd``.
- `label_roles(vault: LoadedVault, repository: Repository, extraction_id: str, *, dry_run: bool=False, client: Any | None=None, clock: Clock | None=None, cancelled: Callable[[], bool]=lambda: False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 388) — Label the reading's passages with instructional roles (see the module docstring).

### Module constants

- `PROMPT_VERSION` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 80)
- `LEDGER_TASK` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 81)
- `LEFT_KIND` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 82)
- `RIGHT_KIND` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 83)
- `BATCH_SIZE` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 85)
- `PASSAGE_CHARS` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 86)
- `SKIPPED_BLOCK_TYPES` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 88)
- `MODELS_ENV` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 91)
- `CAP_SETTING` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 92)
- `ROLE_LABELLER_TASK` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 120)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 129)

### Explicit exports

`__all__` declares:

- `BATCH_SIZE`
- `LEDGER_TASK`
- `MODELS_ENV`
- `PROMPT_VERSION`
- `ROLE_LABELLER_TASK`
- `PassageRoles`
- `RoleLabellerResult`
- `eligible_passages`
- `label_roles`
- `labeller_prompt`
- `run_budget`

## Internal implementation anchors

- `_labelled(repository: Repository, extraction_id: str) -> set[Key]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 150) — Passages this labeller already judged on this reading (any verdict).
- `_unapplied(repository: Repository, extraction_id: str) -> dict[Key, dict[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 165) — Passages this labeller judged ``roles`` on this reading whose proposals were never written (Codex review F2): ``key -> {input hash: ledger id}``.
- `_receipt_batches(connection, extraction_id: str) -> Iterator[tuple[str, dict[str, Key], dict[str, Any], Any]]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 202) — This reading's accepted batch answers from their receipts (newest first): ``(input hash, ref -> passage, ref -> first judgment, receipt)``, each answer parsing and judging every passage of its batch.
- `_answers_with_roles(connection, extraction_id: str) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 228) — ``(extraction/span, input hash)`` of every passage a saved answer gave a non-empty (cleaned) roles list, whatever verdict it stated.
- `_apply_pending(vault: LoadedVault, repository: Repository, extraction_id: str, pending: Mapping[Key, Mapping[str, str]], *, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 256) — Apply judged, unapplied passages from their paid answers' receipts (newest first), with no model call: a receipt counts when it declared this reading's batch map and prompt version, and its answer parses and judges every passage of that batch (what the run accepted).
- `_usage(outcomes: Sequence[Mapping[str, Any]], budget: SpendBudget, route: Any, *, subscription: bool, price: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 300) — The run's usage (Codex review F4): tokens and dollars estimated from each call's reported usage (``estimated_only`` on a subscription; dollars unknown with no price), and apart, what the budget was charged.
- `_batches(passages: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 359)
- `_batch_prompt(title: str | None, batch: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Key], str]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 363)
- `_title(repository: Repository, extraction_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/role_labeller.py), line 370)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `label_roles`; statically calls `label_roles`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `extraction_blocks`, `extraction_source_ids`; calls `extraction_blocks`, `extraction_source_ids`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`; calls `ListwiseTask`, `judge_listwise`, `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`, `receipt_answers`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`, `receipt_answers`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `module`; calls `batch_max_cost_usd`, `claims_from_judgments`, `clean_roles`, `propose_roles`, `tolerate_roles`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `block_roles`, `model_reader_withheld`; calls `block_roles`, `model_reader_withheld`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `protection`; calls `protection`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `os`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_label_roles_cli.py](../../../../../../tests/test_label_roles_cli.py) — direct import
  - `test_a_judged_passage_whose_answer_is_gone_is_reported_incomplete_never_done`
  - `test_a_metered_run_reports_its_charge_and_the_same_estimate`
  - `test_a_missing_roles_field_never_fails_a_batch`
  - `test_a_none_verdict_beside_roles_is_recorded_as_roles_and_recovered_after_the_last_batch`
  - `test_a_request_with_no_reported_usage_counts_its_estimate_beside_reported_ones`
  - `test_a_rerun_resumes_after_the_passages_already_labelled`
  - `test_a_retried_request_that_reported_nothing_counts_its_estimate`
  - `test_a_run_labels_every_batch_in_reading_order_as_proposals`
  - `test_a_subscription_route_is_estimated_only_and_never_refused_for_money`
  - `test_a_subscription_run_reports_the_estimate_from_reported_tokens`
  - `test_a_subscription_run_with_no_price_keeps_its_estimate_unknown`
  - `test_a_zero_cap_sends_nothing`
  - `test_an_answer_judging_a_passage_twice_is_the_batchs_failed_attempt_retried_within_the_caps`
  - `test_an_answer_that_always_judges_a_passage_twice_commits_nothing_and_never_reports_done`
  - `test_an_interruption_after_the_last_judgment_resumes_with_zero_calls`
  - `test_an_interruption_before_the_first_proposal_is_applied_on_resume_without_a_call`
  - `test_an_interruption_midway_through_a_batch_leaves_nothing_half_written_and_resumes`
  - `test_an_older_none_row_whose_saved_answer_has_roles_is_recovered`
  - `test_held_out_and_exam_material_never_reach_the_labeller`
  - `test_recovery_takes_a_refs_first_judgment_as_the_live_path_did`
  - `test_the_cap_is_checked_before_each_batch_call`
  - `test_the_dry_run_names_the_batches_the_cap_would_stop`

## Modification guidance

- Make changes here when the responsibility remains role labeller within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/role_labeller.py](../../../../../../src/learnloop/source_retrieval/role_labeller.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
