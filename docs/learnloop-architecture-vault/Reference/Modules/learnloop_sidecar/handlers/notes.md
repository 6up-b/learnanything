---
title: "learnloop_sidecar.handlers.notes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/notes.py"
source_paths:
  - "src/learnloop_sidecar/handlers/notes.py"
source_commit: "47f2ffc037e55db12ce419711e1d4920cae4fad7"
source_commit_timestamp: "2026-11-02T04:33:30-05:00"
source_worktree_state: "clean"
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
  - "learnloop_sidecar.handlers.notes module"
  - "src/learnloop_sidecar/handlers/notes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.notes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.notes` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Deliverable curriculum C2 RPCs: the learner's notes, linked (spec_deliverable_curriculum_v1 §10, §12 C2; C2b: the vault's own notes, in every vault).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/notes.py](../../../../../../src/learnloop_sidecar/handlers/notes.py) |
| Source lines | 410 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `47f2ffc037e55db12ce419711e1d4920cae4fad7` |
| Commit timestamp | `2026-11-02T04:33:30-05:00` |

## Public API

- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 75) — What the Reader's prompt contract adds for C2 (absent while ``notes.enabled`` is off).
- `queue_note_gaps(ctx: SidecarContext, vault: Any, repository: Any) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 91) — Curriculum C5: queue the linked notes' current snapshots for the gap pipeline and wake its worker (no model call here); follow-ups Nov 2: first set aside the gaps read from a note no longer linked (``jobs.retract_unlinked_notes``).
- `class GoalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 242)
- `notes_path(ctx: SidecarContext, params: GoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 250) — The notes on a deliverable's path lines, by topic (no model call in the request).
- `class ExtractionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 267)
- `notes_marks(ctx: SidecarContext, params: ExtractionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 272) — The ``›`` marks of one reading: per passage, the notes linked beside it.
- `class PassageRef(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 280)
- `class PassagesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 285)
- `notes_passages(ctx: SidecarContext, params: PassagesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 290) — Compare's *your take* band: the notes linked to the compared passages.
- `class SearchInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 302)
- `notes_search(ctx: SidecarContext, params: SearchInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 311) — *link one of your notes*: the vault's own notes for the passage (or the learner's words), by exact words or (embeddings on) by meaning.
- `class NoteRef(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 325)
- `class LinkInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 330)
- `notes_link(ctx: SidecarContext, params: LinkInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 337) — The learner links a note to a passage by hand (theirs: kept, never re-judged).
- `class DecideInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 351)
- `notes_decide(ctx: SidecarContext, params: DecideInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 358) — One tap: hide a note link (hidden across re-judgments), or keep it after all.
- `class HiddenInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 372)
- `notes_hidden(ctx: SidecarContext, params: HiddenInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 377) — The note links the learner hid, newest first (Settings; *show again* is ``notes.decide`` ``keep``).
- `class GapsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 385)
- `notes_set_gaps(ctx: SidecarContext, params: GapsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 390) — Curriculum C5's opt-in from Settings (owner Q9: off by default): writes ``notes.gaps_enabled``.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/notes.py](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 54)
- `NOTES_RPCS` ([src/learnloop_sidecar/handlers/notes.py](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 59)
- `GAPS_LINE` ([src/learnloop_sidecar/handlers/notes.py](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 71)
- `_REGISTRY_LOCK` ([src/learnloop_sidecar/handlers/notes.py](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 145)

### Explicit exports

`__all__` declares:

- `GAPS_LINE`
- `NOTES_RPCS`
- `prompt_contract_fields`
- `queue_note_gaps`

## Internal implementation anchors

- `_require(ctx: SidecarContext) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 112)
- `_error(exc: NL.NotesError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 119)
- `_extraction(repository: Any, extraction_id: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 123)
- `class _Work` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 135) — One vault's background note linking, in memory: per deliverable, the (day, path) it last started for, and that run's state.
- `_work(ctx: SidecarContext) -> _Work` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 148)
- `_spawn(ctx: SidecarContext, name: str, run: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 159)
- `_link(ctx: SidecarContext, vault: Any, repository: Any, goal_id: str, targets: list[NL.Target], *, retry: bool) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/notes.py), line 167) — Start the deliverable's note linking in the background: once a local day per path (its topics and their passages), again after a run that waited for its model, once ``NL.WAITING_RETRY_SECONDS`` have passed since it stopped (Codex re-review F14: the reads polling a waiting run ne…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `record_model_calls`; calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `local_date`; calls `local_date`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_learner_notes`; calls `enqueue_learner_notes`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `apply_config_updates`; calls `apply_config_updates`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `enabled`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `MAX_TAKE_CHARS`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; calls `available`, `decide`, `enabled`, `for_goal`, `for_passages`, `hidden`, `link_by_hand`, `link_goal`, `marks`, `notes_settings`, `path_targets`, `search`, `take_text`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `pathlib`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_c2_rpcs_are_all_of_them`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_settings_opt_in_writes_the_switch_queues_the_linked_notes_and_off_reads_none`
- [tests/test_notes_linked.py](../../../../../../tests/test_notes_linked.py) — direct import
  - `test_re_f14_a_waiting_run_is_not_restarted_by_every_read`
  - `test_the_rpcs_are_registered_and_desktop_only`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/notes.py](../../../../../../src/learnloop_sidecar/handlers/notes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
