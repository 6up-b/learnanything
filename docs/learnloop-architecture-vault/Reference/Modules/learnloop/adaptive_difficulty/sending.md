---
title: "learnloop.adaptive_difficulty.sending"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/sending.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/sending.py"
source_commit: "108fc925aca83dcc3776405f9810cff86c4be3ef"
source_commit_timestamp: "2026-10-21T10:39:25-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.sending module"
  - "src/learnloop/adaptive_difficulty/sending.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.sending`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.sending` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD's one paid-call path, and the held-out check before each request it sends (spec A8; Codex re-review F11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/sending.py](../../../../../../src/learnloop/adaptive_difficulty/sending.py) |
| Source lines | 396 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `108fc925aca83dcc3776405f9810cff86c4be3ef` |
| Commit timestamp | `2026-10-21T10:39:25-04:00` |

## Public API

- `class ProtectedContent(AIInterrupted)` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 63) — A request refused before it was sent: something it quotes is protected now.
- `class StaleSnapshot(ProtectedContent)` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 76) — Refused because the loaded vault changed under the check (a reload, a switch, retries exhausted), not because the content is held out.
- `class SendGuard` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 84) — One job's held-out check, consulted before each request it sends.
  - `__init__(self, vault: Any, repository: Any, *, items: Iterable[Any]=(), item_ids: Iterable[str]=(), identities: Iterable[Mapping[str, Any]]=(), protected: Any=None, live_vault: Callable[[], Any] | None=None, epoch: str | None=None) -> None` (line 102; internal)
  - `stale(self) -> bool` (line 125; public) — The job was refused for a changed snapshot (retryable), not held-out content.
  - `check(self, purpose: str='request') -> Any` (line 130; public) — Raise :class:`ProtectedContent` when the job may send (or record) nothing more.
  - `confirm(self, generation: Any, purpose: str='record') -> None` (line 159; public) — Admit, or refuse when the vault was reloaded since ``generation`` was checked.
  - `_raise_refused(self) -> None` (line 182; internal)
  - `_refuse_if(self, reason: str | None, purpose: str, kind: type[ProtectedContent]=None) -> None` (line 187; internal)
  - `_snapshot(self) -> tuple[Any, Any]` (line 195; internal) — ``(the vault loaded now, its reload generation)``, read as one snapshot.
  - `_protected_now(self) -> tuple[str | None, Any, type[ProtectedContent]]` (line 210; internal) — ``(why it is refused or None, the reload generation judged, the refusal's kind)``.
  - `_judged(self, vault: Any) -> str | None` (line 242; internal)
- `before_dispatch() -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 293) — The last confirmation before a request is dispatched (fix round 6, V1-b).
- `ask_llm(guard: SendGuard, route: Any, client: Any, *, price: float | None, repository: Any, caps: Mapping[str, Any], owner_kind: str, owner_id: str, purpose: str, prompt: str, result_model: Any, metadata: Mapping[str, Any], envelope: Any) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 349) — One logical LLM call on ``route`` (its retries included), each attempt checked first.
- `ask_decider(guard: SendGuard, client: Any, *, config: Any, repository: Any, task: str, state: Any, questions: Mapping[str, Any], owner_id: str, route: str, question_set_version: str, envelope: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 375) — One Decider request (no retry path), checked before it is admitted and before it is sent.
- `refusal_status(exc: BaseException) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 393) — The outcome status of a refusal: ``stale`` (retryable) or ``protected`` (terminal).

### Module constants

- `RELOAD_RETRIES` ([src/learnloop/adaptive_difficulty/sending.py](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 60)
- `_DISPATCH` ([src/learnloop/adaptive_difficulty/sending.py](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 281)

### Explicit exports

`__all__` declares:

- `ProtectedContent`
- `SendGuard`
- `StaleSnapshot`
- `ask_decider`
- `ask_llm`
- `before_dispatch`
- `refusal_status`

## Internal implementation anchors

- `_root(vault: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 271)
- `_checked(guard: SendGuard, purpose: str) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 284)
- `class _GuardGate` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 308) — The guard as the context's request gate, behind the gate already installed.
- `_sending(guard: SendGuard, envelope: Any) -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/sending.py), line 336)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `ProtectedContent`, `before_dispatch`; statically calls `before_dispatch`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `ProtectedContent`, `SendGuard`, `StaleSnapshot`, `module`, `refusal_status`; statically calls `SendGuard`, `ask_decider`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `ProtectedContent`, `SendGuard`, `refusal_status`; statically calls `SendGuard`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `ProtectedContent`, `SendGuard`, `module`, `refusal_status`; statically calls `SendGuard`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `ProtectedContent`, `SendGuard`, `module`, `refusal_status`; statically calls `SendGuard`, `ask_decider`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `ProtectedContent`, `SendGuard`, `ask_llm`, `refusal_status`; statically calls `SendGuard`, `ask_llm`, `refusal_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `MaterialView`; calls `MaterialView`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `suspended`; calls `suspended`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `Protection`, `protection`; calls `Protection`, `protection`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `gate_model_requests`; calls `active_request_gate`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ask_decider`; calls `ask_decider`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`; calls `PaidCalls`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_another_vault_or_none_loaded_refuses`
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — direct import
  - `test_a_reload_while_protection_is_built_is_never_judged_by_the_vault_it_replaced`
  - `test_an_admission_after_a_reload_since_its_check_is_refused`
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_a_harmless_reload_between_the_audits_check_and_its_record_is_retried`
  - `test_a_publication_paused_between_assignment_and_bump_is_never_admitted`
  - `test_the_last_confirmation_runs_after_the_outer_gate_and_the_receipt`
- [tests/test_ad1_fix_round7.py](../../../../../../tests/test_ad1_fix_round7.py) — direct import
  - `test_a_refused_decider_record_labels_the_decider_status`
- [tests/test_ad23_fix_r9.py](../../../../../../tests/test_ad23_fix_r9.py) — direct import
  - `test_send_guard_refuses_an_unavailable_predicate_whatever_the_job_quotes`

## Modification guidance

- Make changes here when the responsibility remains sending within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/sending.py](../../../../../../src/learnloop/adaptive_difficulty/sending.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
