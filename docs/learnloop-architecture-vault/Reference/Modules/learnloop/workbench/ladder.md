---
title: "learnloop.workbench.ladder"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/ladder.py"
source_paths:
  - "src/learnloop/workbench/ladder.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.ladder module"
  - "src/learnloop/workbench/ladder.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.ladder`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.ladder` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2b: the help ladder's Reader side (spec_reader_workbench_v1 §5.2, §5.5, §5.6, G60, G62).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py) |
| Source lines | 417 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `help_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 53)
- `live_workbench_steps(repository: Repository, session_id: str) -> list[hint_workbench.WorkbenchStep]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 58)
- `last_shown_check(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 74)
- `hint_context(vault: Any, repository: Repository, session: Mapping[str, Any], *, focused_step: str | None=None, feedback_step: str | None=None, answered: Mapping[str, Any] | None=None, offered_level: int | None=None, suggestion_id: str | None=None, steps: Sequence[hint_workbench.WorkbenchStep] | None=None, symbolic_now: Any=None) -> hint_workbench.WorkbenchHintContext` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 96) — What the hint service is given for one workbench request (module docstring).
- `help_outcome_lines(vault: Any, repository: Repository, session: Mapping[str, Any]) -> tuple[dict[str, Any], ...]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 150) — RW2c (§5.10): the typed help-outcome lines for the problem's item's facets, read now, while ``workbench.help_outcomes_enabled`` is on; ``()`` otherwise or without history (so the writer's and the chooser's inputs are exactly as before).
- `fallback_level(repository: Repository, session_id: str, about_step: str | None) -> int` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 172) — The Reader's progression (§5.5, G62): rung 1 the first time on a step, then one rung above the last rung offered or taken there, up to 5.
- `offered_events(repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 192) — The ``workbench_help_offered`` events of a problem, oldest first.
- `hint_views(vault: Any, repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 211) — The problem's shown hints, discriminating answers and bridges, in order, as the workbench restores them under their steps (resume keeps the assistance history).
- `standalone_examples(vault: Any, repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 274) — RW2c: the shown "Show me a similar example" results (not under a hint), the latest per step, oldest first.
- `row_claims(row: Mapping[str, Any], *, symbolic_enabled: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 292) — A hint row's own claims as checked (Reader §5.3; fix round 1, F14); with symbolic checks off a stored checked claim is the model's reading (fix round 10).
- `served_claims(repository: Repository, assist_id: str | None, *, symbolic_enabled: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 302) — The claims of the hint ``assist_id`` (``[]`` when it has none).
- `passage_draw_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 324) — ``workbench.passage_draw_enabled`` NOW: RW2c's bridge fields (the draw, "another passage", the book a drawn or picked passage is in) are serialized only while it is on (fix round 2, 3).
- `bridge_view(row: Mapping[str, Any], *, passage_draw: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 337) — A shown bridge as the workbench restores it.
- `unavailable_message(reason: str | None, *, authored_left: bool) -> str` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 356)
- `stuck_texts(repository: Repository, session_id: str) -> list[str]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 372) — The newest version of every non-empty stuck step (its row id).
- `queue_stuck_texts(vault: Any, repository: Repository, session_id: str) -> list[str]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 381) — Queue each stuck step's newest text (``workbench_text``, role ``stuck``); idempotent per version, so a step queued once and unchanged is not queued again.

### Module constants

- `LOG` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 40)
- `TAILORED_UNAVAILABLE` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 43)
- `NO_AUTHORED_LEFT` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 44)
- `WRITER_DOWN_REASONS` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 46)
- `SETTLED_LINE` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 49)
- `UNSETTLED_LINE` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 50)
- `RW2C_BRIDGE_FIELDS` ([src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py), line 334)

### Explicit exports

`__all__` declares:

- `NO_AUTHORED_LEFT`
- `SETTLED_LINE`
- `UNSETTLED_LINE`
- `WRITER_DOWN_REASONS`
- `TAILORED_UNAVAILABLE`
- `RW2C_BRIDGE_FIELDS`
- `bridge_view`
- `passage_draw_enabled`
- `row_claims`
- `served_claims`
- `fallback_level`
- `help_enabled`
- `hint_context`
- `hint_views`
- `last_shown_check`
- `live_workbench_steps`
- `offered_events`
- `queue_stuck_texts`
- `stuck_texts`
- `unavailable_message`

## Internal implementation anchors

- `_rows(repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 69)
- `_verdicts(check: Mapping[str, Any] | None, steps: Sequence[hint_workbench.WorkbenchStep], *, symbolic_enabled: bool=False) -> list[hint_workbench.StepVerdict]` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 79) — The check's verdicts that still describe the steps (same text).
- `_step_line(about: int | None, continue_from: int | None) -> str` ([source](../../../../../../src/learnloop/workbench/ladder.py), line 318)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `live_workbench_steps`; statically calls `live_workbench_steps`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `help_enabled`, `queue_stuck_texts`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`; statically calls `fallback_level`, `help_enabled`, `hint_context`, `hint_views`, `last_shown_check`, `live_workbench_steps`, `passage_draw_enabled`, `queue_stuck_texts`, `served_claims`, `standalone_examples`, `unavailable_message`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `bridge_view`, `help_enabled`, `hint_context`, `live_workbench_steps`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `assist`, `module`; calls `assist`, `workbench_rows`
- [[Reference/Modules/learnloop/db/stores/workbench|learnloop.db.stores.workbench]] — imports `module`; calls `steps_for_session`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_workbench_text`; calls `enqueue_workbench_text`
- [[Reference/Modules/learnloop/hints/kinds|learnloop.hints.kinds]] — imports `module`; calls `labels_for`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; calls `WorkbenchHintContext`, `WorkbenchStep`, `checkpoint_for`, `standing_steps`, `symbolic_enabled`, `verdict_from_record`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `live_steps`, `workbench_enabled`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `stored_claims`, `verdict_records`; calls `stored_claims`, `verdict_records`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `lines_for_item`; calls `lines_for_item`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `alternatives_view`; calls `alternatives_view`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `module`; calls `example_view`, `examples_enabled`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]]
- [tests/test_hint_h2b_fix3.py](../../../../../../tests/test_hint_h2b_fix3.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]]
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]]
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]]
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]]

## Modification guidance

- Make changes here when the responsibility remains ladder within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/ladder.py](../../../../../../src/learnloop/workbench/ladder.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
