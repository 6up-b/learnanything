---
title: "learnloop.router_objective.exposure"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/exposure.py"
source_paths:
  - "src/learnloop/router_objective/exposure.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.exposure module"
  - "src/learnloop/router_objective/exposure.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.exposure`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.exposure` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 row 4: who initiated a source exposure.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py) |
| Source lines | 129 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `initiator_for(context: str | None, stated: str | None=None) -> str` ([source](../../../../../../src/learnloop/router_objective/exposure.py), line 43) — A client's word when it is one of ours, else what the context says, else the learner.
- `session_at(repository: Any, at: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/router_objective/exposure.py), line 55) — The one session in force at ``at``: started by then and not ended before it.
- `plan_block_at(repository: Any, extraction_id: str | None, at: str) -> str | None` ([source](../../../../../../src/learnloop/router_objective/exposure.py), line 73) — The one plan reading block on this reading in force at ``at``: created by then and not ended before it.
- `fields(config: Any, repository: Any, *, context: str | None, initiator: str | None=None, block_id: str | None=None, session_id: str | None=None, visit_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/exposure.py), line 92) — The event's RO0 fields, ``{}`` when the receipts are off (the writer then writes what it always did).
- `visit_fields(config: Any, repository: Any, payload: Mapping[str, Any], *, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/exposure.py), line 106) — What a Reader visit's event adds: its initiator, and its session and (a plan-sent visit's) block, each as the client captured it at the opening, else as of ``at``, the visit's own time; else the link is unknown.

### Module constants

- `LEARNER` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 23)
- `PLAN` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 24)
- `TUTOR_CITATION` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 25)
- `DOSE_OFFER` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 26)
- `LESSON` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 27)
- `INITIATORS` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 28)
- `_BY_CONTEXT` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 30)
- `COLUMNS` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 36)
- `LINK_CLIENT` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 38)
- `LINK_AS_OF_EVENT` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 39)
- `LINK_UNKNOWN` ([src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py), line 40)

### Explicit exports

`__all__` declares:

- `COLUMNS`
- `DOSE_OFFER`
- `INITIATORS`
- `LEARNER`
- `LESSON`
- `LINK_AS_OF_EVENT`
- `LINK_CLIENT`
- `LINK_UNKNOWN`
- `PLAN`
- `TUTOR_CITATION`
- `fields`
- `initiator_for`
- `plan_block_at`
- `session_at`
- `visit_fields`

## Internal implementation anchors

- `_only(rows: list[Any]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/exposure.py), line 51)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]] — imports `module`; statically calls `visit_fields`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `module`; statically calls `fields`, `get`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `module`; statically calls `fields`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`; calls `objective_receipts_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]], [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]], [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_codex_verify.py](../../../../../../tests/test_ro0_codex_verify.py) — direct import
  - `test_r2_an_opening_with_two_sessions_open_names_neither`
- [tests/test_ro0_row4_exposure_initiator.py](../../../../../../tests/test_ro0_row4_exposure_initiator.py) — direct import
  - `test_off_the_writer_writes_what_it_always_did`
  - `test_one_exposure_is_one_row_with_its_fields`
  - `test_the_initiator_is_the_clients_word_else_the_contexts_else_the_learner`

## Modification guidance

- Make changes here when the responsibility remains exposure within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/exposure.py](../../../../../../src/learnloop/router_objective/exposure.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
