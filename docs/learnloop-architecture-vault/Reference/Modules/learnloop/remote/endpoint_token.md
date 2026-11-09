---
title: "learnloop.remote.endpoint_token"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/remote/endpoint_token.py"
source_paths:
  - "src/learnloop/remote/endpoint_token.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.remote"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.remote.endpoint_token module"
  - "src/learnloop/remote/endpoint_token.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-remote"
---

# `learnloop.remote.endpoint_token`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.remote.endpoint_token` exists within [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] to own the behavior summarized by its module contract: The MCP endpoint's persistent secret path (spec_mcp_frontend_c1 §3.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py) |
| Source lines | 238 |
| Owning package | [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class TokenError(RuntimeError)` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 38) — The token file is unreadable or malformed (fail closed: nothing is served).
- `token_directory(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 42)
- `token_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 46)
- `read_token(vault_root: Path) -> str | None` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 75) — The current token, None when none was made yet; :class:`TokenError` if malformed.
- `ensure_token(vault_root: Path) -> str` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 90) — The token, made on first use.
- `rotate_token(vault_root: Path) -> str` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 101) — A new token; the old URL stops working (a running server rereads the file).
- `endpoint_path(token: str) -> str` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 109)
- `alias_key_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 129)
- `read_alias_key(vault_root: Path) -> bytes | None` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 133) — The vault's alias key, None when none was made (or it cannot be read: the caller then keys aliases for its own process).
- `ensure_alias_key(vault_root: Path) -> bytes` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 160) — The vault's alias key, made on first use (0600, beside the token).
- `class TokenStore` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 190) — The current token for a running server, reread when the file changes.
  - `__init__(self, vault_root: Path) -> None` (line 193; internal)
  - `current(self) -> str | None` (line 200; public)
  - `matches_path(self, path: str) -> bool` (line 216; public) — Whether ``path`` is exactly ``/<token>/mcp`` (constant-time compare).

### Module constants

- `TOKEN_DIRECTORY` ([src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py), line 33)
- `TOKEN_FILE` ([src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py), line 34)
- `_TOKEN_RE` ([src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py), line 35)
- `ALIAS_KEY_FILE` ([src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py), line 124)
- `ALIAS_KEY_LOCK` ([src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py), line 125)
- `_ALIAS_KEY_RE` ([src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py), line 126)

### Explicit exports

`__all__` declares:

- `ALIAS_KEY_FILE`
- `TOKEN_FILE`
- `TokenError`
- `TokenStore`
- `alias_key_path`
- `endpoint_path`
- `ensure_alias_key`
- `ensure_token`
- `read_alias_key`
- `read_token`
- `rotate_token`
- `token_path`

## Internal implementation anchors

- `_prepare_directory(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 50)
- `_write(vault_root: Path, token: str) -> None` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 60)
- `_alias_key_lock(directory: Path) -> Iterator[None]` ([source](../../../../../../src/learnloop/remote/endpoint_token.py), line 145) — One maker of the alias key at a time, across processes: an advisory lock beside it, released when its holder exits or dies.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]] — imports `TokenError`, `endpoint_path`, `ensure_token`, `rotate_token`, `token_path`; statically calls `endpoint_path`, `ensure_token`, `rotate_token`, `token_path`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `read_alias_key`; statically calls `read_alias_key`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `fcntl`, `hmac`, `os`, `pathlib`, `re`, `secrets`, `threading`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]], [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mcp_c1a_narrow.py](../../../../../../tests/test_mcp_c1a_narrow.py) — direct import
  - `test_a_second_first_start_keeps_the_alias_key_already_installed`
  - `test_simultaneous_first_starts_agree_on_one_alias_key`
  - `test_the_server_keeps_its_alias_key_beside_the_endpoint_token`
- [tests/test_mcp_cli.py](../../../../../../tests/test_mcp_cli.py) — direct import
  - `test_token_show_makes_a_private_stable_token_and_rotate_replaces_it`
- [tests/test_mcp_http.py](../../../../../../tests/test_mcp_http.py) — direct import
  - `test_a_rotated_token_takes_effect_without_a_restart`
  - `test_only_the_secret_path_with_allowed_host_and_origin_answers`
  - `test_the_sdk_client_works_over_http_and_the_call_is_labelled_by_host`
  - `test_the_token_never_reaches_a_log_record`

## Modification guidance

- Make changes here when the responsibility remains endpoint token within learnloop.remote; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/remote/endpoint_token.py](../../../../../../src/learnloop/remote/endpoint_token.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
