---
title: "learnloop.vault_lock"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault_lock.py"
source_paths:
  - "src/learnloop/vault_lock.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.vault_lock module"
  - "src/learnloop/vault_lock.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.vault_lock`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.vault_lock` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Cross-process vault mutation lock (source-ingestion §8.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py) |
| Source lines | 236 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `guard_vault_mutations(check: Callable[[Path], None])` ([source](../../../../../src/learnloop/vault_lock.py), line 40) — Install an owner's check, evaluated inside the publication lock.
- `class VaultLockError(RuntimeError)` ([source](../../../../../src/learnloop/vault_lock.py), line 80) — Base class for vault mutation lock failures.
- `class VaultLockTimeout(VaultLockError)` ([source](../../../../../src/learnloop/vault_lock.py), line 84) — Raised when the lock could not be acquired within the timeout.
- `class LockHolder` ([source](../../../../../src/learnloop/vault_lock.py), line 89)
- `vault_lock_path(root: Path) -> Path` ([source](../../../../../src/learnloop/vault_lock.py), line 94)
- `read_lock_holder(root: Path) -> LockHolder | None` ([source](../../../../../src/learnloop/vault_lock.py), line 98) — Best-effort diagnostic read of the current holder metadata.
- `vault_mutation_lock(root: Path, *, purpose: str, timeout_s: float=DEFAULT_TIMEOUT_S) -> Iterator[LockHolder]` ([source](../../../../../src/learnloop/vault_lock.py), line 125) — Acquire the exclusive vault mutation lock for the critical section.

### Module constants

- `DEFAULT_TIMEOUT_S` ([src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py), line 63)
- `_POLL_INTERVAL_S` ([src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py), line 64)

## Internal implementation anchors

- `_check_mutation_owner(root: Path) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 49)
- `_held_depths() -> dict[tuple[int, str], int]` ([source](../../../../../src/learnloop/vault_lock.py), line 73)
- `_read_lock_holder_path(path: Path) -> LockHolder | None` ([source](../../../../../src/learnloop/vault_lock.py), line 109)
- `_acquire_with_timeout(fd: int, path: Path, timeout_s: float) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 198)
- `_write_holder_fd(fd: int, holder: LockHolder) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 221)
- `_write_holder(path: Path, holder: LockHolder) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 228)
- `_clear_holder(path: Path) -> None` ([source](../../../../../src/learnloop/vault_lock.py), line 232)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `VaultLockError`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `DEFAULT_TIMEOUT_S`, `VaultLockTimeout`, `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `guard_vault_mutations`; statically calls `guard_vault_mutations`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/goals/goal_lo|learnloop.goals.goal_lo]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `DEFAULT_TIMEOUT_S`, `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/ops/content_fixes|learnloop.ops.content_fixes]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `DEFAULT_TIMEOUT_S`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `VaultLockError`, `vault_mutation_lock`; statically calls `vault_mutation_lock`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `vault_mutation_lock`; statically calls `vault_mutation_lock`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `contextvars`, `dataclasses`, `errno`, `fcntl`, `os`, `pathlib`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]], [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] and 19 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_span_support_helpers.py](../../../../../tests/facet_span_support_helpers.py) — direct import
- [tests/test_activity_families.py](../../../../../tests/test_activity_families.py) — direct import
  - `test_vault_mutation_lock_is_reentrant_per_thread_only`
- [tests/test_apply_recovery.py](../../../../../tests/test_apply_recovery.py) — direct import
  - `test_a_bind_with_nothing_pending_takes_no_apply_lock`
  - `test_the_book_cards_undo_holds_the_vault_lock_from_its_check_to_its_last_change`
- [tests/test_ingest_ownership.py](../../../../../tests/test_ingest_ownership.py) — direct import
  - `test_a_busy_vault_lock_defers_lease_work_instead_of_failing`
  - `test_stale_worker_cannot_finish_or_publish_after_replacement`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
- [tests/test_source_ingestion.py](../../../../../tests/test_source_ingestion.py) — direct import
  - `test_ingest_creates_a_new_subject_while_holding_the_vault_lock`

## Modification guidance

- Make changes here when the responsibility remains vault lock within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault_lock.py](../../../../../src/learnloop/vault_lock.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
