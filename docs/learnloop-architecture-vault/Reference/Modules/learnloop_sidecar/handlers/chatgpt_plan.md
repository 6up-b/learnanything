---
title: "learnloop_sidecar.handlers.chatgpt_plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/chatgpt_plan.py"
source_paths:
  - "src/learnloop_sidecar/handlers/chatgpt_plan.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.chatgpt_plan module"
  - "src/learnloop_sidecar/handlers/chatgpt_plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.chatgpt_plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.chatgpt_plan` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Desktop "Continue with ChatGPT": sign-in, status and plan-usage actions.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/chatgpt_plan.py](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py) |
| Source lines | 223 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class SignInAttempts` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 55) — The process's one sign-in attempt, run on a background thread.
  - `__init__(self) -> None` (line 58; internal)
  - `start(self, session: PlanSession, *, new_account: bool, consent: bool, timeout: float=SIGN_IN_TIMEOUT_SECONDS) -> _Attempt` (line 62; public)
  - `cancel(self, *, wait: float=CANCEL_WAIT_SECONDS) -> bool` (line 90; public)
  - `snapshot(self) -> dict[str, Any] | None` (line 101; public)
- `chatgpt_plan_payload(ctx: SidecarContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 109) — Status (local files only), the current attempt, and the open vault's plan profiles.
- `chatgpt_plan_status(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 134)
- `class SignInStartParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 138)
- `chatgpt_plan_signin_start(ctx: SidecarContext, params: SignInStartParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 144)
- `chatgpt_plan_signin_cancel(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 153)
- `chatgpt_plan_signout(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 159)
- `chatgpt_plan_acknowledge_welcome(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 166)
- `chatgpt_plan_resume(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 172)
- `class UseFallbackParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 177)
- `ai_use_fallback(ctx: SidecarContext, params: UseFallbackParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 187) — The learner chose "Use OpenRouter instead" on one offer (plan-first transport T1, redesign D).

### Module constants

- `CANCEL_WAIT_SECONDS` ([src/learnloop_sidecar/handlers/chatgpt_plan.py](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 34)
- `ATTEMPTS` ([src/learnloop_sidecar/handlers/chatgpt_plan.py](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 106)

### Explicit exports

`__all__` declares:

- `ATTEMPTS`
- `SignInAttempts`
- `chatgpt_plan_payload`

## Internal implementation anchors

- `class _Attempt` ([source](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py), line 38)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `chatgpt_plan_payload`; statically calls `chatgpt_plan_payload`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/oauth|learnloop.ai.chatgpt_plan.oauth]] — imports `SignInError`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]] — imports `plan_profiles`; calls `plan_profiles`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `PendingSignIn`, `PlanSession`, `SIGN_IN_TIMEOUT_SECONDS`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/store|learnloop.ai.chatgpt_plan.store]] — imports `StoreError`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `answer_offer`, `granted_origins`, `granted_tasks`, `offer_profile`, `revoke`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_sidecar.py](../../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
  - `test_cancel_and_failure_are_reported`
  - `test_resume_clears_a_pause`
  - `test_sign_in_from_the_desktop_without_a_vault`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse`
  - `test_fix_l2_a_quiet_status_read_never_points_at_an_offer_it_did_not_make`
  - `test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build`
  - `test_rr_f3_the_plan_status_lists_the_sessions_grants_for_a_lasting_stop`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/chatgpt_plan.py](../../../../../../src/learnloop_sidecar/handlers/chatgpt_plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
