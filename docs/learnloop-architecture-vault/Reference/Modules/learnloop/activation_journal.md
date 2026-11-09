---
title: "learnloop.activation_journal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/activation_journal.py"
source_paths:
  - "src/learnloop/activation_journal.py"
source_commit: "a121b50fc6d7aa4b4d4d5756c0da8d0de9d2d2a7"
source_commit_timestamp: "2026-11-09T15:45:04-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.activation_journal module"
  - "src/learnloop/activation_journal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.activation_journal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.activation_journal` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: An activation that did not commit: its journal, and what may open the vault meanwhile.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py) |
| Source lines | 164 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a121b50fc6d7aa4b4d4d5756c0da8d0de9d2d2a7` |
| Commit timestamp | `2026-11-09T15:45:04-05:00` |

## Public API

- `class InterruptedActivation(RuntimeError)` ([source](../../../../../src/learnloop/activation_journal.py), line 72) — The vault's activation did not commit; it is not served until it completes.
- `journal_path(sqlite_path: Path) -> Path` ([source](../../../../../src/learnloop/activation_journal.py), line 76) — The activation journal beside ``sqlite_path``.
- `pending(sqlite_path: Path) -> bool` ([source](../../../../../src/learnloop/activation_journal.py), line 83) — Whether an activation journal stands beside ``sqlite_path``.
- `completing() -> bool` ([source](../../../../../src/learnloop/activation_journal.py), line 89) — Whether this context is completing (or running) the activation itself.
- `completing_activation() -> Iterator[None]` ([source](../../../../../src/learnloop/activation_journal.py), line 96) — Mark this context as the activation's own writer, so its opens are not refused.
- `message(sqlite_path: Path) -> str` ([source](../../../../../src/learnloop/activation_journal.py), line 106) — What to tell the learner: which upgrade did not finish, and the command that completes it.
- `install_completer(completer: Callable[[Path], object] | None) -> None` ([source](../../../../../src/learnloop/activation_journal.py), line 122) — Install the process's completion (an entry point does, at import); None removes it.
- `complete(vault_root: Path, sqlite_path: Path) -> None` ([source](../../../../../src/learnloop/activation_journal.py), line 129) — Complete a journalled activation before an opener attaches, or raise :class:`InterruptedActivation`.
- `refuse_if_interrupted(sqlite_path: Path) -> None` ([source](../../../../../src/learnloop/activation_journal.py), line 146) — Raise :class:`InterruptedActivation` while a journal stands (unless this context completes it).

### Module constants

- `JOURNAL_SUFFIX` ([src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py), line 63)
- `_COMPLETING` ([src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py), line 66)
- `_COMPLETER` ([src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py), line 69)

### Explicit exports

`__all__` declares:

- `JOURNAL_SUFFIX`
- `InterruptedActivation`
- `complete`
- `completing`
- `completing_activation`
- `install_completer`
- `journal_path`
- `message`
- `pending`
- `refuse_if_interrupted`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`; statically calls `install_completer`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `refuse_if_interrupted`; statically calls `refuse_if_interrupted`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/failure_share_upgrade|learnloop.failure_share_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/interval_factor_upgrade|learnloop.interval_factor_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/lesson_offers_upgrade|learnloop.lesson_offers_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/lesson_opportunity_upgrade|learnloop.lesson_opportunity_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/phone_probes_upgrade|learnloop.phone_probes_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `module`; statically calls `message`, `pending`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/router_calibration_upgrade|learnloop.router_calibration_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/router_followups_upgrade|learnloop.router_followups_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/router_learned_tail_upgrade|learnloop.router_learned_tail_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/router_objective_upgrade|learnloop.router_objective_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/teacher_probes_upgrade|learnloop.teacher_probes_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/unevidenced_return_upgrade|learnloop.unevidenced_return_upgrade]] — imports `module`; statically calls `completing_activation`, `journal_path`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `module`; statically calls `complete`, `completing`, `pending`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `module`; statically calls `install_completer`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `json`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]], [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] and 24 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_denial_log.py](../../../../../tests/test_ad_denial_log.py) — direct import
- [tests/test_attempt_content_state_successor.py](../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_landing_ii_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_it`
- [tests/test_batch3_landing.py](../../../../../tests/test_batch3_landing.py) — direct import
  - `test_without_a_completion_every_attach_refuses_with_the_mvp035_upgrade_message`
- [tests/test_cold_retry_reschedule.py](../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp037_journal`
- [tests/test_curriculum_c1_landing.py](../../../../../tests/test_curriculum_c1_landing.py) — direct import
  - `test_ii_an_interrupted_mvp039_activation_is_handed_down_by_c1s_completion`
  - `test_ii_an_interrupted_mvp040_activation_is_refused_without_the_completion_and_upgrade_completes_it`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp039_journal`
- [tests/test_help_fold_attach_successor.py](../../../../../tests/test_help_fold_attach_successor.py) — direct import
- [tests/test_learner_report_superseded.py](../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_without_a_completion_every_attach_refuses_with_the_mvp036_upgrade_message`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f2_an_activation_that_cannot_complete_stops_the_opener`
  - `test_f2_an_opener_in_a_process_that_cannot_complete_refuses`
  - `test_f2_attaches_that_never_write_refuse_while_the_journal_stands`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
- [tests/test_rbeq_pr2_landing.py](../../../../../tests/test_rbeq_pr2_landing.py) — direct import
  - `test_without_a_completion_the_opener_and_every_attach_refuse_with_the_upgrade_message`
- [tests/test_reader_followups_successor.py](../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp038_journal`
- [tests/test_teacher_te1_successor.py](../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_a_bare_upgrade_goes_through_mvp041_along_the_chain`

## Modification guidance

- Make changes here when the responsibility remains activation journal within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/activation_journal.py](../../../../../src/learnloop/activation_journal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
