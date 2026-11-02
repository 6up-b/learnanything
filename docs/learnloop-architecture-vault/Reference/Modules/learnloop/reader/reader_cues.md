---
title: "learnloop.reader.reader_cues"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_cues.py"
source_paths:
  - "src/learnloop/reader/reader_cues.py"
source_commit: "758fec8241d0befbc095f69220952611b05e419b"
source_commit_timestamp: "2026-10-20T15:05:02-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_cues module"
  - "src/learnloop/reader/reader_cues.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_cues`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_cues` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW3a: margin cues from the Guide (spec_reader_workbench_v1 §6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py) |
| Source lines | 620 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `758fec8241d0befbc095f69220952611b05e419b` |
| Commit timestamp | `2026-10-20T15:05:02-04:00` |

## Public API

- `class CueError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 102) — A refused cue request (nothing was written).
- `cues_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 110) — RW3a's kill switch (``cues.enabled``, default on).
- `cue_density(vault: Any) -> str` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 117)
- `density_budget(density: str) -> int` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 123)
- `step_down(density: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 129) — "Fewer marks like this": one notch down (more -> normal -> fewer -> off).
- `off_sources(vault: Any) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 136)
- `one_per_viewport(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 141)
- `cue_id_for(extraction_id: str, span_id: str, learning_object_id: str, target_id: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 154)
- `render_note(topic: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 170)
- `render_because(day: str | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 174)
- `earlier_work(vault: Any, repository: Repository, *, attempt_id: str | None, fallback_at: str | None=None, statement: str | None=None, pending: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 233) — "Open · what you worked on" for one cited attempt: the question as it was answered, the answer in the learner's words, and ``statement`` in LearnLoop's model's voice (RW3a's Guide cues; RW3b's discovered cues name their target's own statement, Codex review F12).
- `cue_candidates(vault: Any, repository: Repository, *, extraction_id: str, plan: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 283) — Every cue the plan's sections would carry, in the rail's order per section, before the learner's choices (density, not relevant, cues off).
- `guide_cues(vault: Any, repository: Repository, *, extraction_id: str, plan: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 349) — The plan's margin cues within the learner's choices (spec §6.1-6.2).
- `find_cue(vault: Any, repository: Repository, *, extraction_id: str, cue_id: str, plan: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 397) — A cue of this plan by id, whatever the learner's choices (a "not relevant" can be undone, a cue from a book switched off still answers); held-out material is never a cue.
- `record_cue_tap(repository: Repository, *, extraction_id: str, cue: Mapping[str, Any], action: str, text: str | None=None, clock: Clock | None=None, actions: Mapping[str, tuple[str, str]]=CUE_TAP_ACTIONS, right_kind: str=CUE_RIGHT_KIND) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 414) — Record a tap on a cue: one salience-only event and, when it changes the learner's verdict, one ``learner_card`` row on ``passage_cue`` (the question is (span, target)); a repeated verdict appends nothing and an undo with nothing to undo appends nothing.
- `preference_changes(vault: Any, *, density: str | None=None, source_id: str | None=None, source_off: bool | None=None, via: str='footer') -> tuple[dict[tuple[str, ...], Any], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 499) — The ``[cues]`` config updates a preference change makes, and the events it logs.
- `log_preference_events(repository: Repository, events: Iterable[Mapping[str, Any]], *, extraction_id: str | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 528) — Record preference changes (salience only; no learner text).
- `preferences(vault: Any, *, source_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 549) — The learner's cue preferences, as the Reader and Settings show them.
- `check_me_request(vault: Any, cue: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 563) — What "Check me" asks ``find_practice`` for (spec §6.1): one short item on the cue's Learning Object, as an ordinary attempt on your own.

### Module constants

- `CUES_VERSION` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 51)
- `CUE_TASK` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 53)
- `CUE_LEFT_KIND` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 54)
- `CUE_RIGHT_KIND` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 55)
- `CUE_KIND_REVISIT` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 58)
- `DENSITIES` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 60)
- `DENSITY_BUDGET` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 62)
- `CUE_TAP_ACTIONS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 65)
- `DISCOVERED_TAP_ACTIONS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 73)
- `CUE_PREFERENCE_EVENTS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 78)
- `SERVER_CUE_EVENTS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 80)
- `RW3B_SERVER_CUE_EVENTS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 82)
- `PREFERENCE_VIA` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 84)
- `NOTE_TEMPLATE` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 88)
- `BECAUSE_TEMPLATE` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 90)
- `BECAUSE_UNDATED` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 91)
- `LABEL_TEMPLATE` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 93)
- `CUE_TEMPLATES` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 94)
- `MAX_PROMPT_CHARS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 96)
- `MAX_ANSWER_CHARS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 98)
- `MAX_NOT_RELEVANT_CHARS` ([src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py), line 99)

### Explicit exports

`__all__` declares:

- `BECAUSE_TEMPLATE`
- `BECAUSE_UNDATED`
- `CUES_VERSION`
- `CUE_KIND_REVISIT`
- `CUE_PREFERENCE_EVENTS`
- `CUE_TAP_ACTIONS`
- `DISCOVERED_TAP_ACTIONS`
- `RW3B_SERVER_CUE_EVENTS`
- `current_verdicts`
- `earlier_work`
- `CUE_TASK`
- `CUE_TEMPLATES`
- `CueError`
- `DENSITIES`
- `DENSITY_BUDGET`
- `LABEL_TEMPLATE`
- `MAX_ANSWER_CHARS`
- `NOTE_TEMPLATE`
- `PREFERENCE_VIA`
- `SERVER_CUE_EVENTS`
- `check_me_request`
- `cue_candidates`
- `cue_density`
- `cue_id_for`
- `cues_enabled`
- `density_budget`
- `find_cue`
- `guide_cues`
- `log_preference_events`
- `preference_changes`
- `preferences`
- `record_cue_tap`
- `render_because`
- `render_note`
- `step_down`

## Internal implementation anchors

- `_digest(parts: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 150)
- `_day(created_at: str | None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 158) — "2 Oct" for a timestamp (UTC), or None when it does not parse.
- `_clip(text: str | None, limit: int) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 178)
- `_clip_question(statement: str | None, method: Any) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 185) — The answered question for the popover: the statement clipped as before, and a required method's instruction after it, whole.
- `_clip_answer(text: str | None, limit: int=MAX_ANSWER_CHARS) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 197) — The learner's own words, verbatim but for surrounding blank space and a clip at ``limit`` (line breaks kept: an answer's shape is part of it).
- `_strongest_error(repository: Repository, learning_object_id: str) -> Any | None` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 207) — The error the Guide's reason names: the same choice ``_learner_signal`` makes over the diagnoser's overlay (highest severity, then newest).
- `_earlier_work(vault: Any, repository: Repository, error: Any, pending: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 217) — What "Open" shows (spec §6.1, "the cited attempt, its diagnosis"): when the learner answered, on which question, the answer itself in their own words, and LearnLoop's model's reading of that answer once it has one.
- `_current_verdicts(repository: Repository, extraction_id: str) -> dict[tuple[str, str], str]` ([source](../../../../../../src/learnloop/reader/reader_cues.py), line 261) — The learner's current verdict per (span, target) on this extraction's cues.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `module`; statically calls `cue_candidates`, `cue_density`, `cues_enabled`, `current_verdicts`, `earlier_work`, `off_sources`, `one_per_viewport`, `render_note`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `check_me_request`, `cues_enabled`, `find_cue`, `guide_cues`, `log_preference_events`, `preference_changes`, `preferences`, `record_cue_tap`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`; statically calls `cue_density`, `find_cue`, `record_cue_tap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/answered_contracts|learnloop.db.stores.answered_contracts]] — imports `answered_contracts`; calls `answered_contracts`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `held_out_sections`; calls `held_out_sections`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `answered_question`, `fit_presented_prompt`; calls `answered_question`, `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_open_shows_the_answered_question_with_its_frozen_method_whole`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_a_cue_on_held_out_material_cannot_be_tapped`
  - `test_a_long_answer_is_clipped_and_an_error_without_an_attempt_has_none`
  - `test_a_new_error_on_the_learning_object_is_a_new_cue`
  - `test_a_transcript_passage_carries_a_cue_like_any_source`
  - `test_check_me_never_offers_the_question_the_learner_answered`
  - `test_cue_copy_is_fixed_templates_that_never_judge_the_learner`
  - `test_cues_and_their_taps_write_no_evidence_mastery_fsrs_or_plan_row`
  - `test_every_server_cue_event_is_salience_only`
  - `test_not_relevant_withholds_the_cue_until_the_learner_undoes_it`
  - `test_step_down_walks_more_normal_fewer_off`
  - `test_taps_are_salience_only_events_and_learner_card_verdicts`
  - `test_the_client_records_cue_impressions_and_cannot_forge_a_tap`
  - `test_the_report_counts_marks_shown_taps_and_choices_against_marks_shown`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_margin_cue_marks_only_a_passage_whose_cited_words_are_there`
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method`
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_rw3b_cue_events_are_salience_only_server_events_the_client_cannot_record`

## Modification guidance

- Change reader cues policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_cues.py](../../../../../../src/learnloop/reader/reader_cues.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
