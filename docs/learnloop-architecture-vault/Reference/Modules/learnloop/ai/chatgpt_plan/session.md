---
title: "learnloop.ai.chatgpt_plan.session"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/chatgpt_plan/session.py"
source_paths:
  - "src/learnloop/ai/chatgpt_plan/session.py"
source_commit: "42ab0bc90d513d76d7b0eea692d52330b51a8385"
source_commit_timestamp: "2026-10-23T10:49:09-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai.chatgpt_plan"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.chatgpt_plan.session module"
  - "src/learnloop/ai/chatgpt_plan/session.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-chatgpt-plan"
---

# `learnloop.ai.chatgpt_plan.session`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.chatgpt_plan.session` exists within [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] to own the behavior summarized by its module contract: The ChatGPT-plan session: sign-in, the access token for a call, status, sign-out.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py) |
| Source lines | 737 |
| Owning package | [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `42ab0bc90d513d76d7b0eea692d52330b51a8385` |
| Commit timestamp | `2026-10-23T10:49:09-04:00` |

## Public API

- `class ChatGPTSignInRequired(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 83) — No usable ChatGPT sign-in on this machine.
- `class ChatGPTPlanNotEnabled(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 87) — Signed in, but the grant does not include ChatGPT plan usage.
- `class ChatGPTPlanUsageExhausted(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 91) — A usage limit was reached; plan requests are paused.
- `class ChatGPTPlanNotEligible(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 95) — ChatGPT plan usage is unavailable for this user, workspace or policy.
- `class TokenWaitAborted(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 99) — The caller stopped waiting for the credential step (interrupt or deadline); nothing was sent.
- `class PlanStatus` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 117) — What this machine's ChatGPT sign-in can do, from local files only.
  - `paused_until(self, pause_minutes: int) -> float | None` (line 135; public)
  - `readiness(self, *, pause_minutes: int=DEFAULT_PAUSE_MINUTES, now: float | None=None) -> tuple[str, str]` (line 141; public) — ``(state, message)``: ``ready``, ``signed_out``, ``plan_usage_disabled``, ``not_eligible``, ``usage_exhausted`` or ``store_error``.
  - `as_dict(self, *, pause_minutes: int=DEFAULT_PAUSE_MINUTES) -> dict[str, Any]` (line 171; public)
- `class SignInResult` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 197)
  - `as_dict(self) -> dict[str, Any]` (line 207; public)
- `class PendingSignIn` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 215) — One authorization attempt: its listener, PKCE verifier, state and nonce.
  - `__init__(self, session: 'PlanSession', *, discovery: Discovery, client_id: str, new_registration: bool, expected_subject: str | None, login_hint: str | None, consent: bool, port: int | None) -> None` (line 218; internal)
  - `wait(self, timeout: float=SIGN_IN_TIMEOUT_SECONDS) -> SignInResult` (line 243; public) — Wait for the browser to return, then finish; the listener always closes.
  - `cancel(self) -> None` (line 256; public) — End the wait; a callback already being finished is refused at commit.
  - `close(self) -> None` (line 262; public)
  - `finish(self, params: dict[str, str]) -> SignInResult` (line 265; public)
- `class PlanSession` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 269) — The machine's ChatGPT sign-in, read from (and written to) a :class:`PlanStore`.
  - `__init__(self, store: PlanStore | None=None, *, http: HttpCall=urllib_call, clock: Callable[[], float]=time.time) -> None` (line 272; internal)
  - `status(self) -> PlanStatus` (line 279; public)
  - `begin_sign_in(self, *, issuer: str=AUTH_ISSUER, new_account: bool=False, consent: bool=False, port: int | None=None) -> PendingSignIn` (line 309; public) — Start one attempt: discovery, a fresh state/nonce/PKCE, the loopback listener.
  - `_complete(self, pending: PendingSignIn, params: dict[str, str]) -> SignInResult` (line 331; internal)
  - `acknowledge_welcome(self) -> None` (line 424; public) — The first-sign-in confirmation was shown; never show it again.
  - `access_token(self, *, timeout: float=HTTP_TIMEOUT_SECONDS, cancelled: Callable[[], bool] | None=None) -> str` (line 430; public) — A current access token, refreshed (with rotation) when near expiry.
  - `_access_token_locked(self, *, started: float, timeout: float, cancelled: Callable[[], bool] | None) -> str` (line 458; internal)
  - `_reconciled(self, account: Account, tokens: Tokens) -> tuple[Account, Tokens]` (line 513; internal) — Finish a commit that stopped between the token snapshot and the account (caller holds the lock).
  - `_usable(self, account: Account, tokens: Tokens) -> str` (line 528; internal) — The token, only under a grant that includes ChatGPT plan usage.
  - `_fresh(self, tokens: Tokens) -> bool` (line 536; internal)
  - `_still_valid_or_raise(self, tokens: Tokens, message: str) -> Tokens` (line 539; internal)
  - `_signed_in(self) -> tuple[Account, Tokens]` (line 544; internal)
  - `_sign_out_locally(self, account: Account, reason: str) -> str` (line 559; internal) — Clear the tokens after a terminal refresh error (the caller holds ``refresh.lock``).
  - `_signout_epoch(self) -> int` (line 571; internal)
  - `check_usable(self, *, pause_minutes: int) -> dict[str, Any] | None` (line 576; public) — Refuse before any request when readiness says the plan cannot serve it.
  - `note_unauthorized(self) -> None` (line 595; public) — A 401: refresh before the next request.
  - `note_usage_limit(self, *, code: str, request_id: str | None) -> None` (line 600; public)
  - `note_not_eligible(self, *, code: str, request_id: str | None) -> None` (line 605; public)
  - `note_listed_models(self, slugs: list[str]) -> None` (line 608; public) — Remember the account's model list (``learnloop ai models chatgpt``) for `learnloop doctor`.
  - `listed_models(self) -> dict[str, Any] | None` (line 616; public) — The last model list of the signed-in account, or ``None`` (never listed, or another account).
  - `resume(self) -> None` (line 627; public) — Clear the usage-limit pause so the next request tries the plan again.
  - `note_success(self, observed_pause: dict[str, Any] | None) -> None` (line 632; public) — A completed response: the expired pause it was sent under is no longer news.
  - `sign_out(self) -> dict[str, Any]` (line 643; public) — Clear the tokens, then revoke the renewable session; keep the registration and host id.
  - `_revoke_quietly(self, endpoint: str | None, client_id: str, refresh_token: str | None) -> None` (line 695; internal) — One best-effort revocation of tokens that were never saved.

### Module constants

- `MANAGE_USAGE_URL` ([src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 75)
- `SIGN_IN_COMMAND` ([src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 76)
- `REFRESH_MARGIN_SECONDS` ([src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 78)
- `DEFAULT_PAUSE_MINUTES` ([src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 79)
- `SIGN_IN_TIMEOUT_SECONDS` ([src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 80)

### Explicit exports

`__all__` declares:

- `ChatGPTPlanNotEligible`
- `ChatGPTPlanNotEnabled`
- `ChatGPTPlanUsageExhausted`
- `ChatGPTSignInRequired`
- `MANAGE_USAGE_URL`
- `PendingSignIn`
- `PlanSession`
- `PlanStatus`
- `SIGN_IN_COMMAND`
- `SignInResult`
- `TokenWaitAborted`

## Internal implementation anchors

- `_now_iso(now: float | None=None) -> str` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 103)
- `_parse_iso(value: Any) -> float | None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 107)
- `_tokens_from(payload: dict[str, Any], *, now: float, previous: Tokens | None, scopes: list[str] | None) -> Tokens` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py), line 706)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `ChatGPTPlanNotEligible`, `ChatGPTPlanNotEnabled`, `ChatGPTPlanUsageExhausted`, `ChatGPTSignInRequired`, `MANAGE_USAGE_URL`, `PlanSession`; statically calls `ChatGPTPlanNotEligible`, `ChatGPTPlanUsageExhausted`, `PlanSession`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `PlanSession`; statically calls `PlanSession`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `PlanSession`; statically calls `PlanSession`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `MANAGE_USAGE_URL`, `PlanSession`; statically calls `PlanSession`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `PlanSession`; statically calls `PlanSession`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `PendingSignIn`, `PlanSession`, `SIGN_IN_TIMEOUT_SECONDS`; statically calls `PlanSession`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `PlanSession`; statically calls `PlanSession`

### Repository tooling consumers

- [scripts/benchmark_chatgpt_plan_latency.py](../../../../../../../scripts/benchmark_chatgpt_plan_latency.py); calls `PlanSession`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/oauth|learnloop.ai.chatgpt_plan.oauth]] — imports `AGENT_NAME`, `AUTH_ISSUER`, `CallbackListener`, `DYNAMIC_CLIENT_ID`, `Discovery`, `EndpointUnreachable`, `HTTP_TIMEOUT_SECONDS`, `HttpCall`, `PLAN_SCOPE`, `SignInError`, `TERMINAL_REFRESH_ERRORS`, `TokenEndpointError`, `authorization_url`, `discover`, `exchange_code`, `fetch_jwks`, `granted_scopes`, `new_pkce_pair`, `refresh_grant`, `revoke_refresh_token`, `states_match`, `urllib_call`, `validate_id_token`; calls `CallbackListener`, `SignInError`, `authorization_url`, `discover`, `exchange_code`, `fetch_jwks`, `granted_scopes`, `new_pkce_pair`, `refresh_grant`, `revoke_refresh_token`, `states_match`, `validate_id_token`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/store|learnloop.ai.chatgpt_plan.store]] — imports `Account`, `LOCK_TIMEOUT_SECONDS`, `LockCancelled`, `PlanStore`, `StoreError`, `Tokens`; calls `Account`, `PlanStore`, `Tokens`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `secrets`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]], [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_t1_routes.py](../../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_inside_an_ad_operation_no_route_asks_and_no_grant_serves`
- [tests/test_ai_compare.py](../../../../../../../tests/test_ai_compare.py) — direct import
- [tests/test_chatgpt_plan_cli.py](../../../../../../../tests/test_chatgpt_plan_cli.py) — direct import
  - `test_doctor_warns_when_a_route_uses_a_plan_this_machine_cannot_serve`
  - `test_latency_dry_run_then_a_timed_run`
  - `test_signin_json_and_no_browser_prints_the_url_to_stderr`
  - `test_status_models_resume_and_signout`
- [tests/test_chatgpt_plan_landing.py](../../../../../../../tests/test_chatgpt_plan_landing.py) — direct import
- [tests/test_chatgpt_plan_provider.py](../../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_a_success_clears_the_expired_pause_it_saw`
  - `test_a_success_that_overlaps_a_usage_limit_keeps_the_pause`
  - `test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing`
  - `test_readiness_reads_local_state_only`
  - `test_signed_out_is_refused_before_any_request`
  - `test_usage_limit_before_the_stream_and_not_eligible`
  - `test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back`
- [tests/test_chatgpt_plan_sidecar.py](../../../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
  - `test_resume_clears_a_pause`
- [tests/test_chatgpt_plan_signin.py](../../../../../../../tests/test_chatgpt_plan_signin.py) — direct import
  - `test_a_grant_without_plan_usage_signs_in_but_is_not_usable`
  - `test_a_pause_ends_by_itself_after_the_profile_window`
  - `test_a_reader_never_sees_new_tokens_with_the_old_grant`
  - `test_a_refresh_that_drops_plan_usage_never_serves_a_restricted_token`
  - `test_cancel_after_the_browser_returned_saves_nothing`
  - `test_concurrent_refreshes_send_one_request`
  - `test_declined_consent_saves_nothing`
  - `test_first_sign_in_registers_validates_and_stores_machine_locally`
  - `test_invalid_grant_clears_tokens_and_requires_sign_in`
  - `test_keyring_backend_keeps_tokens_out_of_files`
  - `test_reauthorization_rejects_a_callback_naming_another_client`
  - `test_refresh_rotates_tokens_and_never_sends_scope`
  - `test_registration_without_issued_client_id_is_incomplete`
  - `test_returning_sign_in_reuses_the_issued_client_and_host`
  - `test_returning_sign_in_with_another_account_keeps_the_saved_one`
  - `test_sign_in_timeout_and_cancel_end_the_attempt`
  - `test_sign_out_during_an_in_flight_refresh_stays_signed_out`
  - `test_sign_out_invalidates_a_sign_in_that_was_already_pending`
  - `test_sign_out_revokes_then_clears_tokens_but_keeps_the_registration`
  - `test_state_mismatch_is_refused_before_any_exchange`
  - `test_transient_refresh_failure_keeps_credentials`
  - `test_wrong_nonce_is_refused_and_nothing_replaced`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_a_paused_plan_never_falls_back_to_codex`
  - `test_a_usage_limit_mid_turn_pauses_the_plan`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_plan_call_that_fails_for_availability_offers_openrouter_for_that_route`
  - `test_admission_equals_wire_and_every_body_keeps_the_grammar`
  - `test_doctor_names_a_configured_slug_the_account_does_not_list`
  - `test_f2_openrouter_is_offered_only_when_the_feature_could_use_it`
  - `test_f7_an_explicit_inline_never_sends_tools_and_a_tools_turn_caps_its_resent_input`
  - `test_the_stage_changes_transport_selection_only`
  - `test_unavailable_offers_openrouter_only_when_configured_and_sends_nothing_unasked`
- [tests/test_plan_first_transport_paid_roles.py](../../../../../../../tests/test_plan_first_transport_paid_roles.py) — direct import
  - `test_a_grant_routes_a_paid_role_to_openrouter_priced_as_metered_and_a_ready_plan_comes_first`
  - `test_every_paid_role_resolves_to_the_plan_and_asks_before_openrouter`
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/chatgpt_plan/session.py](../../../../../../../src/learnloop/ai/chatgpt_plan/session.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
