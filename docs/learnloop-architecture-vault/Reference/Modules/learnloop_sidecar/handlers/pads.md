---
title: "learnloop_sidecar.handlers.pads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/pads.py"
source_paths:
  - "src/learnloop_sidecar/handlers/pads.py"
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
  - "learnloop_sidecar.handlers.pads module"
  - "src/learnloop_sidecar/handlers/pads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.pads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.pads` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPCs: scratchpads (spec §3.4, §10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py) |
| Source lines | 376 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class PadGetInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 43)
- `class PadListInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 47)
- `class PadApplyInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 54)
- `pad_get_handler(ctx: SidecarContext, params: PadGetInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 62) — One pad: its metadata, its standing blocks in order (each with its head version and its submissions) and their links.
- `pad_list_handler(ctx: SidecarContext, params: PadListInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 80) — Pads, most recently changed first, a page at a time: for the library, search and the drain.
- `pad_apply_handler(ctx: SidecarContext, params: PadApplyInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 106) — One batch of ops on one pad: ``{applied_seq, results, heads, pads}``.
- `class SubmitTarget(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 122) — Where the block's text goes: the practice session and item the existing entry point records it on (the item a problem pad or check cell answers, or a teach-back item for the block's LO from ``request_teach_back``).
- `class PadSubmitBlockInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 134)
- `pad_submit_block_handler(ctx: SidecarContext, params: PadSubmitBlockInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 217) — Submit one block version as an attempt or a teach-back (an explicit act): ``{submission_id, block_id, version_id, as, attempt_id?, teach_back_id?, duplicate, entry?}``.
- `class PadProposalsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 247)
- `pad_proposals_handler(ctx: SidecarContext, params: PadProposalsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 252) — The pad's gutter proposals: one per standing block's current words at most, with its labels.
- `class ProposalLabelInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 265)
- `proposal_label_handler(ctx: SidecarContext, params: ProposalLabelInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 273) — What the learner did with a proposal ("not this" means wrong, "dismiss" means not now), once per id.
- `class PadDrainInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 288)
- `pad_drain_handler(ctx: SidecarContext, params: PadDrainInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 295) — Closing a desk: the pads it worked on that day, what each holds, and a carry offer when the last line asks.
- `class CarriedAnchor(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 302)
- `class CarryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 308)
- `carried_carry_handler(ctx: SidecarContext, params: CarryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 324) — Carry a question (idempotent by ``carried_id``): ``{carried: {...}, created}``.
- `class CarriedListInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 339)
- `carried_list_handler(ctx: SidecarContext, params: CarriedListInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 346) — Carried questions, longest carried first, a page at a time, with the shelf's display limit.
- `class CarriedMarkInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 355)
- `carried_mark_handler(ctx: SidecarContext, params: CarriedMarkInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 366) — A label or a notice on a carried question (idempotent by ``event_id``): ``{carried, applied, conflict}``.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 32)
- `PAD_RPCS` ([src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 35)
- `PAD_RD4_RPCS` ([src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 37)

## Internal implementation anchors

- `_after_batch(ctx: SidecarContext, vault: Any, repository: Any, block_ids: list[str]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 88) — The committed blocks' words to learner text, and their proposals.
- `_submission_reply(row: dict[str, Any], *, duplicate: bool, entry: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 142)
- `_hand_to_attempt(ctx: SidecarContext, vault: Any, prepared: submission_core.Prepared, target: SubmitTarget) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 152)
- `_started_teach_back(repository: Any, prepared: submission_core.Prepared) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 178) — The conversation this submission already opened (a retry after a lost reply), else None; refuses when another teach-back of the item is under way in the session (its next turn would take the block as an answer).
- `_hand_to_teach_back(ctx: SidecarContext, repository: Any, prepared: submission_core.Prepared, target: SubmitTarget) -> tuple[dict[str, Any] | None, str | None, str | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 199)
- `_carried_wire(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/pads.py), line 317)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_attempt_type`; calls `stuck_attempt_type`
- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `ProtocolError`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `PadNotFound`, `PadOp`, `apply_pad_ops`, `pad_list`, `pad_view`; calls `apply_pad_ops`, `pad_list`, `pad_view`
- [[Reference/Modules/learnloop/pads/carried|learnloop.pads.carried]] — imports `module`; calls `carry`, `listing`, `mark`
- [[Reference/Modules/learnloop/pads/drain|learnloop.pads.drain]] — imports `desk_drain`; calls `desk_drain`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `module`; calls `settle_blocks`
- [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]] — imports `module`; calls `label`, `pad_proposals`, `propose_for_blocks`
- [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]] — imports `module`; calls `prepare`, `record`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TeachBackState`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `teach_back_envelope`; calls `teach_back_envelope`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `Verbatim`, `versioned`; calls `Verbatim`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]] — imports `protocol_error`; calls `protocol_error`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SubmitAttemptInput`, `submit_attempt_on`; calls `SubmitAttemptInput`, `submit_attempt_on`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SubmitTeachBackTurnInput`, `submit_teach_back_turn`; calls `SubmitTeachBackTurnInput`, `submit_teach_back_turn`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd0_rpcs_are_all_of_them`
  - `test_the_pinned_rd4a_rpcs_are_all_of_them`
- [tests/test_reader_rd0_rpcs.py](../../../../../../tests/test_reader_rd0_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_reader_rd4_rpcs.py](../../../../../../tests/test_reader_rd4_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/pads.py](../../../../../../src/learnloop_sidecar/handlers/pads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
