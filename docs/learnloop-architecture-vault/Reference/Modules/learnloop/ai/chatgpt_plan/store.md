---
title: "learnloop.ai.chatgpt_plan.store"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/chatgpt_plan/store.py"
source_paths:
  - "src/learnloop/ai/chatgpt_plan/store.py"
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
  - "learnloop.ai.chatgpt_plan.store module"
  - "src/learnloop/ai/chatgpt_plan/store.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-chatgpt-plan"
---

# `learnloop.ai.chatgpt_plan.store`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.chatgpt_plan.store` exists within [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] to own the behavior summarized by its module contract: Machine-local sign-in state for the ChatGPT-plan provider.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py) |
| Source lines | 517 |
| Owning package | [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class StoreError(RuntimeError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 72) — The machine-local store cannot be read or written.
- `class LockTimeout(StoreError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 76) — A lock was not acquired within its timeout.
- `class LockCancelled(StoreError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 80) — The caller gave up waiting for a lock (an interrupt or its deadline).
- `default_store_root() -> Path` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 84)
- `class Account` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 89) — One registration and its validated identity.
  - `from_dict(cls, data: dict[str, Any]) -> 'Account'` (line 114; public)
- `class Tokens` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 120)
  - `from_dict(cls, data: dict[str, Any]) -> 'Tokens'` (line 135; public)
- `class SecretBackend(Protocol)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 140)
  - `load(self, client_id: str) -> dict[str, Any] | None` (line 143; public)
  - `save(self, client_id: str, payload: dict[str, Any]) -> None` (line 145; public)
  - `clear(self, client_id: str) -> None` (line 147; public)
- `class FileSecrets` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 150) — Tokens in ``tokens.json`` (0600), keyed by client id.
  - `__init__(self, root: Path) -> None` (line 155; internal)
  - `load(self, client_id: str) -> dict[str, Any] | None` (line 158; public)
  - `save(self, client_id: str, payload: dict[str, Any]) -> None` (line 165; public)
  - `clear(self, client_id: str) -> None` (line 168; public)
- `class KeyringSecrets` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 179) — Tokens in the OS keyring (service ``learnloop-chatgpt-plan``).
  - `__init__(self, module: Any) -> None` (line 184; internal)
  - `load(self, client_id: str) -> dict[str, Any] | None` (line 187; public)
  - `save(self, client_id: str, payload: dict[str, Any]) -> None` (line 200; public)
  - `clear(self, client_id: str) -> None` (line 206; public)
- `usable_keyring() -> Any | None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 213) — The ``keyring`` module when it has a real backend, else None.
- `class PlanStore` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 236) — The ChatGPT-plan store under one root (default: the LearnLoop config dir).
  - `__init__(self, root: Path | None=None) -> None` (line 239; internal)
  - `account_path(self) -> Path` (line 244; public)
  - `state_path(self) -> Path` (line 248; public)
  - `host_path(self) -> Path` (line 252; public)
  - `ensure_root(self) -> None` (line 255; public)
  - `host_id(self) -> str` (line 263; public) — This host's ``ext_agent_host_id``, created once and then reused.
  - `load_account(self) -> Account | None` (line 280; public)
  - `save_account(self, account: Account) -> None` (line 289; public)
  - `secrets_for(self, account: Account) -> SecretBackend` (line 294; public)
  - `preferred_secrets(self) -> SecretBackend` (line 305; public)
  - `load_tokens(self, account: Account) -> Tokens | None` (line 312; public)
  - `save_tokens(self, account: Account, tokens: Tokens) -> None` (line 321; public)
  - `clear_tokens(self, account: Account) -> None` (line 325; public)
  - `save_sign_in(self, account: Account, tokens: Tokens) -> Account` (line 333; public) — Persist a validated sign-in: tokens first, then the account that points at them.
  - `load_state(self) -> dict[str, Any]` (line 358; public)
  - `update_state(self, **changes: Any) -> dict[str, Any]` (line 362; public) — Merge ``changes`` into ``state.json`` (a None value removes the key).
  - `clear_state_if(self, key: str, expected: Any) -> bool` (line 376; public) — Remove ``key`` only while it still holds ``expected`` (compare and clear, under the lock).
  - `lock(self, name: str='store.lock', timeout: float=LOCK_TIMEOUT_SECONDS, cancelled: Callable[[], bool] | None=None) -> Iterator[None]` (line 390; public) — An exclusive lock across threads and processes.

### Module constants

- `STORE_DIRNAME` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 60)
- `SECRET_STORE_ENV` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 64)
- `KEYRING_SERVICE` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 65)
- `LOCK_TIMEOUT_SECONDS` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 66)
- `_LOCK_POLL_SECONDS` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 67)
- `_THREAD_LOCKS` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 68)
- `_THREAD_LOCKS_GUARD` ([src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 69)

### Explicit exports

`__all__` declares:

- `Account`
- `FileSecrets`
- `KEYRING_SERVICE`
- `KeyringSecrets`
- `LockCancelled`
- `LockTimeout`
- `PlanStore`
- `SECRET_STORE_ENV`
- `StoreError`
- `Tokens`
- `default_store_root`
- `usable_keyring`

## Internal implementation anchors

- `_thread_lock(key: str) -> threading.Lock` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 439)
- `_read_json(path: Path) -> Any` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 447)
- `_write_json(path: Path, data: Any) -> None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 460) — Atomic 0600 write: a reader sees the old file or the new one, never a mix.
- `_fsync_directory(directory: Path) -> None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 485) — Make a rename or deletion in ``directory`` durable (POSIX; a no-op where unsupported).
- `_utc_now() -> str` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py), line 500)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `Account`, `LOCK_TIMEOUT_SECONDS`, `LockCancelled`, `PlanStore`, `StoreError`, `Tokens`; statically calls `Account`, `PlanStore`, `Tokens`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `StoreError`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `StoreError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `global_settings_path`; calls `global_settings_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `json`, `os`, `pathlib`, `tempfile`, `threading`, `time`, `typing`, `uuid`
- Third party: `keyring`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]], [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_signin.py](../../../../../../../tests/test_chatgpt_plan_signin.py) — direct import
  - `test_a_reader_never_sees_new_tokens_with_the_old_grant`
  - `test_a_refresh_that_drops_plan_usage_never_serves_a_restricted_token`
  - `test_credential_files_are_durable_after_replace_and_delete`
  - `test_keyring_backend_keeps_tokens_out_of_files`
  - `test_store_root_follows_the_config_dir`
  - `test_the_store_lock_gives_up_on_timeout_or_cancellation_but_not_when_free`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/chatgpt_plan/store.py](../../../../../../../src/learnloop/ai/chatgpt_plan/store.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
