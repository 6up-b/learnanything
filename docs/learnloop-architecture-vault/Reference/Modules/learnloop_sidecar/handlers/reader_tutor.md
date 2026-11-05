---
title: "learnloop_sidecar.handlers.reader_tutor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reader_tutor.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reader_tutor.py"
source_commit: "workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb"
source_commit_timestamp: "2026-11-04T19:32:38-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop_sidecar.handlers.reader_tutor module"
  - "src/learnloop_sidecar/handlers/reader_tutor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.reader_tutor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.reader_tutor` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW1c's composition for ``reader.ask`` (spec_reader_workbench_v1 §4.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/reader_tutor.py](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py) |
| Source lines | 471 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb` |
| Commit timestamp | `2026-11-04T19:32:38-05:00` |

## Public API

- `retrieval_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 39)
- `offers_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 44)
- `learner_state_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 49) — Learner-blindness relax's kill switch, ``reader_tutor.learner_state_enabled``.
- `learner_state(vault: Any, repository: Any, params: Any, restricted: 'ReaderRestriction', *, now_iso: str | None=None) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 57) — The learner state one ``reader.ask`` hands the tutor, or None while the switch is off.
- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 111) — What RW1c adds to the Reader's prompt contract (nothing while both switches are off).
- `class ReaderRestriction` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 151) — What one ``reader.ask`` is restricted to, derived on the server whatever the retrieval switch says (Codex re-review F2).
  - `cold(self) -> bool` (line 169; public)
  - `stored(self) -> dict[str, Any] | None` (line 172; public) — The restriction persisted on the question (``source_context.reader_caller``), so a caller rebuilt from it later is never wider; None when unrestricted.
- `restriction(vault: Any, repository: Any, params: Any) -> ReaderRestriction` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 182) — The question's restriction (see :class:`ReaderRestriction`).
- `bound_ask(vault: Any, repository: Any, params: Any, restricted: ReaderRestriction) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 199) — The question's :class:`reader_modes.BoundAsk`, or None when no workbench session binds an item.
- `class ReaderInputs` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 249) — The model-written inputs one lookup builds from, AS READ (fix round 7, R1).
- `reader_inputs(vault: Any, repository: Any, *, lo_ids: list[str], personalized: bool, intent: str, target_hypotheses: list[dict[str, str]], binding: Any) -> ReaderInputs` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 269) — The :class:`ReaderInputs` of one lookup.
- `build_request(ctx: Any, vault: Any, repository: Any, params: Any, restricted: ReaderRestriction, binding: Any=None) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 286) — The ``ReaderTutorRequest`` for one ``reader.ask``, or None while retrieval is off.
- `tools_refused(restricted: ReaderRestriction) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 372) — No tool, practice request or offer lookup may run for this question (G48, Codex review F2, re-review F2): during a cold administration, whether the client says so (``coldActive``) or the server derives it from the bound item, and inside a bound session, where a tool's own caller…
- `offers(vault: Any, repository: Any, result: dict[str, Any], *, extraction_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 383) — The Reader's own buttons under an answer (None while ``offers_enabled`` is off): RW1c's "try the next step first" and RW5b's "make this explorable".
- `fallback_practice_request(vault: Any, question: str, event_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 425) — Without the sources service, "Practice this" is a plain ``find_practice`` on the learner's question (§4.6; the same RPC S0 later fills).
- `record_excerpt_exposure(vault: Any, repository: Any, result: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 438) — The "From your books" excerpt's text is shown: one exposure row (best effort).

### Module constants

- `FALLBACK_PRACTICE_VERSION` ([src/learnloop_sidecar/handlers/reader_tutor.py](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 36)

### Explicit exports

`__all__` declares:

- `FALLBACK_PRACTICE_VERSION`
- `bound_ask`
- `build_request`
- `ReaderRestriction`
- `fallback_practice_request`
- `learner_state`
- `learner_state_enabled`
- `offers`
- `offers_enabled`
- `prompt_contract_fields`
- `record_excerpt_exposure`
- `restriction`
- `retrieval_enabled`
- `tools_refused`

## Internal implementation anchors

- `_ancestors(exchanges: list[dict[str, Any]], parent_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py), line 138)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `learner_state_enabled`, `module`, `prompt_contract_fields`; statically calls `bound_ask`, `build_request`, `fallback_practice_request`, `learner_state`, `learner_state_enabled`, `offers`, `offers_enabled`, `prompt_contract_fields`, `record_excerpt_exposure`, `restriction`, `retrieval_enabled`, `tools_refused`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `offers_enabled`, `show_me_enabled`; calls `offers_enabled`, `show_me_enabled`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_shown_spans`; calls `record_shown_spans`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_sources`, `resolve_misconceptions`; calls `propose_sources`, `resolve_misconceptions`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `ask_history`, `inquiry_enabled`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `session_row`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `module`; calls `build`, `enabled`, `omitted`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; calls `fields`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `help_converts_active`; calls `help_converts_active`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `find_sources_for_caller`; calls `find_sources_for_caller`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `open_questions`; calls `open_questions`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `module`; calls `ItemBoundGuard`, `ReaderLookup`, `explorable_buttons`, `inquiry_exchanges`, `learner_work`, `named_gap_hypotheses`, `next_step_buttons`, `offer_shown_span_keys`, `passage_learning_objects`, `shown_source_ids`, `shown_span_keys`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `PRACTICE_QUESTION_CHARS`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `BoundAsk`, `ReaderTutorRequest`; calls `BoundAsk`, `ReaderTutorRequest`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `reader_caller`; calls `reader_caller`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_the_tutor_buttons_are_make_explorable_on_this_books_equation_and_figure_blocks`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reader_tutor.py](../../../../../../src/learnloop_sidecar/handlers/reader_tutor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
