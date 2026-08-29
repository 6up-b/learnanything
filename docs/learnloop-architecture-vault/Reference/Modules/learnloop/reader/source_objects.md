---
title: "learnloop.reader.source_objects"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_objects.py"
source_paths:
  - "src/learnloop/reader/source_objects.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.source_objects module"
  - "src/learnloop/reader/source_objects.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_objects`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_objects` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Source-object layer + relations + canonical mapping proposals (spec §7, design B step 7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py) |
| Source lines | 169 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SourceObjectError(ValueError)` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 34) — Domain error for the source-object service.
- `author_source_object(repository: Repository, *, source_id: str, revision_id: str, object_type: str, exact_text: str='', content: Mapping[str, Any] | None=None, citations: list[Mapping[str, Any]] | None=None, authorship: str='ai', status: str='proposed', authorial_role: str | None=None, salience_proposal: float | None=None, model_provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 38) — Author a new source object (version 1).
- `review_source_object(repository: Repository, *, source_object_id: str, status: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 79) — Append a review status successor (``reviewed`` / ``rejected`` / ``superseded``).
- `link_relation(repository: Repository, *, source_object_id: str, related_object_id: str | None=None, relation_type: str=CONNECT_IT_RELATION, learner_text: str | None=None, authorship: str='learner', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 95) — Create a versioned relation between source objects.
- `propose_mapping(repository: Repository, *, target_kind: str, source_object_id: str | None=None, annotation_id: str | None=None, target_ref: str | None=None, confidence: float | None=None, rationale: str | None=None, provenance: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 118) — Append a canonical mapping proposal (§7.3).
- `accept_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 143)
- `reject_mapping(repository: Repository, *, proposal_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 150) — Rejecting a mapping never deletes the annotation or suppresses alternatives (§7.3).
- `source_objects_for_source(repository: Repository, *, source_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 159)
- `proposal_inbox(repository: Repository, *, status: str='proposed', source_object_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_objects.py), line 163) — Non-modal review inbox (§6.4): accumulated proposals reviewed without losing reading position.

### Module constants

- `OBJECT_TYPES` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 19)
- `RELATION_TYPES` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 23)
- `MAPPING_TARGET_KINDS` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 27)
- `CONNECT_IT_RELATION` ([src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py), line 31)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; statically calls `author_source_object`, `propose_mapping`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `accept_mapping`, `link_relation`, `proposal_inbox`, `reject_mapping`, `review_source_object`, `source_objects_for_source`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_objects.py](../../../../../../tests/test_source_objects.py) — direct import
  - `test_author_begins_proposed_and_review_is_append_only`
  - `test_connect_it_relation_defaults_to_learner_connects_proposal`
  - `test_mapping_proposal_accept_and_reject_are_non_destructive`

## Modification guidance

- Change source objects policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_objects.py](../../../../../../src/learnloop/reader/source_objects.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
