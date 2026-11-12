---
title: "learnloop.cli.mcp"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/mcp.py"
source_paths:
  - "src/learnloop/cli/mcp.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.mcp module"
  - "src/learnloop/cli/mcp.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.mcp`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.mcp` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop mcp`: the chat frontend over MCP (spec_mcp_frontend_c1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/mcp.py](../../../../../../src/learnloop/cli/mcp.py) |
| Source lines | 184 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `serve(vault: VaultOption=None, transport: Annotated[str, typer.Option('--transport', help='http (default) or stdio.')]='http', port: Annotated[int, typer.Option('--port', help='Loopback port for http.', min=1, max=65535)]=DEFAULT_PORT, host: Annotated[str, typer.Option('--host', help='Bind address; only 127.0.0.1 is permitted.')]='127.0.0.1', public_host: Annotated[list[str] | None, typer.Option('--public-host', help='Exact public Host header the tunnel forwards (repeatable).')]=None, public_origin: Annotated[list[str] | None, typer.Option('--public-origin', help='Extra exact browser Origin to accept (repeatable).')]=None, log_level: Annotated[str, typer.Option('--log-level', help='Server log level.')]='warning') -> None` ([source](../../../../../../src/learnloop/cli/mcp.py), line 49) — Serve the vault to chat hosts (secondary attach: never migrates or runs startup work).
- `token_show(vault: VaultOption=None, port: Annotated[int, typer.Option('--port', min=1, max=65535)]=DEFAULT_PORT, public_host: Annotated[list[str] | None, typer.Option('--public-host')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/mcp.py), line 103) — Print the endpoint path and URLs (the token is made on first use).
- `token_rotate(vault: VaultOption=None, port: Annotated[int, typer.Option('--port', min=1, max=65535)]=DEFAULT_PORT, public_host: Annotated[list[str] | None, typer.Option('--public-host')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/mcp.py), line 131) — Replace the token; the old URL stops working (a running server rereads it).
- `activity(vault: VaultOption=None, days: Annotated[int, typer.Option('--days', min=0, max=3650, help='Look back this many days.')]=7, limit: Annotated[int, typer.Option('--limit', min=0, max=500, help='Recent calls to list.')]=20, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/mcp.py), line 152) — What chat hosts did with this vault: calls by tool and host, passages shown (read-only).

### Module constants

- `DEFAULT_PORT` ([src/learnloop/cli/mcp.py](../../../../../../src/learnloop/cli/mcp.py), line 29)

### Explicit exports

`__all__` declares:

- `mcp_app`

## Internal implementation anchors

- `_root(vault: Path | None) -> Path` ([source](../../../../../../src/learnloop/cli/mcp.py), line 33)
- `_dump(payload: object) -> str` ([source](../../../../../../src/learnloop/cli/mcp.py), line 44)
- `_token_payload(root: Path, token: str, port: int, public_hosts: list[str]) -> dict[str, object]` ([source](../../../../../../src/learnloop/cli/mcp.py), line 89)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `mcp_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/app_launch|learnloop.app_launch]] — imports `serve_mcp`; calls `serve_mcp`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_vault`; calls `bind_command_vault`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/remote/endpoint_token|learnloop.remote.endpoint_token]] — imports `TokenError`, `endpoint_path`, `ensure_token`, `rotate_token`, `token_path`; calls `endpoint_path`, `ensure_token`, `rotate_token`, `token_path`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `SchemaMismatch`, `vault_sqlite_path`; calls `vault_sqlite_path`
- [[Reference/Modules/learnloop/remote/telemetry|learnloop.remote.telemetry]] — imports `chat_activity`; calls `chat_activity`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `find_vault_root`; calls `find_vault_root`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_append_units.py](../../../../../../tests/test_cli_append_units.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/mcp.py](../../../../../../src/learnloop/cli/mcp.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
