---
title: "learnloop.desks.protocol"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/desks/protocol.py"
source_paths:
  - "src/learnloop/desks/protocol.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.desks"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.desks.protocol module"
  - "src/learnloop/desks/protocol.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-desks"
---

# `learnloop.desks.protocol`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.desks.protocol` exists within [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] to own the behavior summarized by its module contract: The workbench's write protocol (spec §3.4), shared by ``desk.apply`` and ``pad.apply``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/desks/protocol.py](../../../../../../src/learnloop/desks/protocol.py) |
| Source lines | 134 |
| Owning package | [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProtocolError(Exception)` ([source](../../../../../../src/learnloop/desks/protocol.py), line 31) — A batch the server will not take (nothing applied, nothing stored).
  - `__init__(self, code: str, message: str, details: Mapping[str, Any] | None=None) -> None` (line 34; internal)
- `class OpRefused(Exception)` ([source](../../../../../../src/learnloop/desks/protocol.py), line 40) — One op that cannot apply; the batch goes on (its result is ``refused``).
  - `__init__(self, code: str, message: str) -> None` (line 43; internal)
- `class OpConflict(Exception)` ([source](../../../../../../src/learnloop/desks/protocol.py), line 48) — One op whose expected head is stale; the batch goes on (its result is ``conflict``).
  - `__init__(self, current: Mapping[str, Any]) -> None` (line 51; internal)
- `ok(**extra: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/protocol.py), line 56)
- `run_op(connection: Any, apply: Callable[[], Mapping[str, Any] | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/protocol.py), line 60) — One op's result.
- `request_hash(channel: str, request: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/desks/protocol.py), line 74)
- `apply_batch(repository: Any, *, channel: str, client_id: str, seq: int, request: Mapping[str, Any], apply_ops: Callable[[Any, str], dict[str, Any]], pad_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/protocol.py), line 80) — Apply one batch exactly once, in order, with its receipt; return its reply.
- `client_seq_heads(repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/desks/protocol.py), line 126)

### Module constants

- `OK` ([src/learnloop/desks/protocol.py](../../../../../../src/learnloop/desks/protocol.py), line 26)
- `CONFLICT` ([src/learnloop/desks/protocol.py](../../../../../../src/learnloop/desks/protocol.py), line 27)
- `REFUSED` ([src/learnloop/desks/protocol.py](../../../../../../src/learnloop/desks/protocol.py), line 28)

### Explicit exports

`__all__` declares:

- `CONFLICT`
- `OK`
- `REFUSED`
- `OpConflict`
- `OpRefused`
- `ProtocolError`
- `apply_batch`
- `client_seq_heads`
- `ok`
- `request_hash`
- `run_op`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `OpConflict`, `OpRefused`, `apply_batch`, `client_seq_heads`, `run_op`; statically calls `OpConflict`, `OpRefused`, `apply_batch`, `client_seq_heads`, `run_op`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `OpConflict`, `OpRefused`, `apply_batch`, `run_op`; statically calls `OpConflict`, `OpRefused`, `apply_batch`, `run_op`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `OpRefused`, `apply_batch`, `run_op`; statically calls `OpRefused`, `apply_batch`, `run_op`
- [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]] — imports `ProtocolError`
- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `ProtocolError`
- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `ProtocolError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/workspace_batches|learnloop.db.stores.workspace_batches]] — imports `module`; calls `client_heads`, `find_receipt`, `insert_receipt`, `last_seq`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]], [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]], [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd0_protocol.py](../../../../../../tests/test_reader_rd0_protocol.py) — direct import
  - `test_a_batch_number_used_with_other_ops_is_refused`
  - `test_a_batch_out_of_seq_order_is_refused_and_applies_nothing`
  - `test_batches_replayed_out_of_order_converge_to_the_in_order_state`
  - `test_desk_and_pad_batches_share_one_sequence_per_client`
- [tests/test_reader_rd8a_ink.py](../../../../../../tests/test_reader_rd8a_ink.py) — direct import
  - `test_a_retried_batch_returns_its_receipt_and_a_resent_ink_id_is_a_no_op`
  - `test_ink_shares_the_clients_one_sequence_with_pad_batches`

## Modification guidance

- Make changes here when the responsibility remains protocol within learnloop.desks; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/desks/protocol.py](../../../../../../src/learnloop/desks/protocol.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
