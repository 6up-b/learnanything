---
title: "learnloop.pads.submission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/submission.py"
source_paths:
  - "src/learnloop/pads/submission.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.submission module"
  - "src/learnloop/pads/submission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.submission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.submission` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Submitting a pad block (spec §10.9): the only way a pad's words become evidence, and an explicit act.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/submission.py](../../../../../../src/learnloop/pads/submission.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SubmissionRefused(Exception)` ([source](../../../../../../src/learnloop/pads/submission.py), line 48)
  - `__init__(self, code: str, message: str, details: dict[str, Any] | None=None) -> None` (line 49; internal)
- `class Prepared` ([source](../../../../../../src/learnloop/pads/submission.py), line 55) — A block version cleared for hand-off, or the row of a submission already made (``existing``).
- `request_hash(*, block_id: str, version_id: str, submitted_as: str, practice_item_id: str, session_id: str) -> str` ([source](../../../../../../src/learnloop/pads/submission.py), line 70)
- `prepare(repository: Any, *, submission_id: str, block_id: str, version_id: str, submitted_as: str, practice_item_id: str, session_id: str) -> Prepared` ([source](../../../../../../src/learnloop/pads/submission.py), line 105) — Check one submission and freeze its text (raises :class:`SubmissionRefused`).
- `record(repository: Any, prepared: Prepared, *, attempt_id: str | None, teach_back_id: str | None, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/submission.py), line 148) — Write the submission's row once (a concurrent retry that wrote it first wins); returns the row.
- `tags(connection: Any, heads: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/pads/submission.py), line 167) — Each block's submissions for ``pad.get`` (the "submitted · …" tag), each saying whether it froze the block's current words or an earlier version.

### Module constants

- `SUBMITTABLE` ([src/learnloop/pads/submission.py](../../../../../../src/learnloop/pads/submission.py), line 37)
- `ENTRY_SURFACE` ([src/learnloop/pads/submission.py](../../../../../../src/learnloop/pads/submission.py), line 44)
- `QUOTED_MESSAGE` ([src/learnloop/pads/submission.py](../../../../../../src/learnloop/pads/submission.py), line 45)

### Explicit exports

`__all__` declares:

- `ATTEMPT`
- `ENTRY_SURFACE`
- `Prepared`
- `QUOTED_MESSAGE`
- `SUBMITTABLE`
- `SubmissionRefused`
- `TEACH_BACK`
- `prepare`
- `record`
- `request_hash`
- `tags`

## Internal implementation anchors

- `_answered_item(connection: Any, pad: dict[str, Any], version: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/pads/submission.py), line 76) — The item this block may be "my answer to": its check cell's, else its problem pad's.
- `_quotes(connection: Any, repository: Any, pad_id: str, block: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/pads/submission.py), line 88)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `tags`; statically calls `tags`
- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `module`; statically calls `prepare`, `record`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/pad_ledgers|learnloop.db.stores.pad_ledgers]] — imports `module`; calls `insert_submission`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`, `heads`, `pad`, `standing_anchors_for_blocks`, `submission`, `submissions_for_blocks`, `version`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `QUOTE_KINDS`, `lineage`, `words_version`; calls `lineage`, `words_version`
- [[Reference/Modules/learnloop/pads/quoting|learnloop.pads.quoting]] — imports `includes_quote`; calls `includes_quote`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd4_submission.py](../../../../../../tests/test_reader_rd4_submission.py) — direct import
  - `test_a_problem_pads_block_becomes_an_attempt_through_the_ordinary_submit`

## Modification guidance

- Make changes here when the responsibility remains submission within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/submission.py](../../../../../../src/learnloop/pads/submission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
