---
title: "learnloop.content.synthesis.proposal_match"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/proposal_match.py"
source_paths:
  - "src/learnloop/content/synthesis/proposal_match.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.proposal_match module"
  - "src/learnloop/content/synthesis/proposal_match.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.proposal_match`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.proposal_match` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: What a synthesis run's result is when an earlier run already proposed the same rows.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/proposal_match.py](../../../../../../../src/learnloop/content/synthesis/proposal_match.py) |
| Source lines | 158 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProposalMatch` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 58)
- `proposed_content(rows: list[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 79) — The compared content of a run's rows, before they are persisted.
- `stored_content(repository: Repository, items: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 93) — The compared content of a persisted proposal's items.
- `match_proposal(repository: Repository, *, source_set_id: str, purpose: str, rows: list[Mapping[str, Any]]) -> ProposalMatch | None` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 113) — The earlier proposal of ``source_set_id`` under ``purpose`` whose items equal ``rows`` (module docstring).
- `class RejectedProposalMatch(Exception)` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 143) — A run's rows equal a proposal the learner wholly rejected: its answers are dropped and it pays again.
  - `__init__(self, proposal_id: str) -> None` (line 146; internal)

### Module constants

- `_COMPARED_FIELDS` ([src/learnloop/content/synthesis/proposal_match.py](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 42)
- `_PREFERENCE` ([src/learnloop/content/synthesis/proposal_match.py](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 54)

### Explicit exports

`__all__` declares:

- `MatchKind`
- `ProposalMatch`
- `RejectedProposalMatch`
- `match_proposal`
- `proposed_content`
- `stored_content`

## Internal implementation anchors

- `_stored(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 63)
- `_content(rows: Iterable[Mapping[str, Any]], dependencies: Mapping[str, list[str]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 69)
- `_kind(items: list[dict[str, Any]]) -> MatchKind` ([source](../../../../../../../src/learnloop/content/synthesis/proposal_match.py), line 106)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `ProposalMatch`, `RejectedProposalMatch`, `match_proposal`; statically calls `RejectedProposalMatch`, `match_proposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rerun_proposals.py](../../../../../../../tests/test_rerun_proposals.py) — direct import
  - `test_a_changed_payload_is_not_a_match`
  - `test_two_runs_of_the_same_answers_store_equal_content_whatever_their_ids_and_clocks`

## Modification guidance

- Change proposal match policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/proposal_match.py](../../../../../../../src/learnloop/content/synthesis/proposal_match.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
