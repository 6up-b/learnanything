---
title: "learnloop_sidecar.handlers.figures"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/figures.py"
source_paths:
  - "src/learnloop_sidecar/handlers/figures.py"
source_commit: "0f1d1abf38dcb9d4401a6c7a4cd80bbd0f6c871f"
source_commit_timestamp: "2026-11-02T07:49:16-05:00"
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
  - "learnloop_sidecar.handlers.figures module"
  - "src/learnloop_sidecar/handlers/figures.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.figures`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.figures` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW5a RPCs: explorable figures (spec_reader_workbench_v1 §8; UX §4.7, W11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py) |
| Source lines | 1454 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0f1d1abf38dcb9d4401a6c7a4cd80bbd0f6c871f` |
| Commit timestamp | `2026-11-02T07:49:16-05:00` |

## Public API

- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 98) — What the Reader's prompt contract adds for RW5a (absent while off).
- `manim_opt_in_state(vault: Any) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 130)
- `deliver_figure(ctx: SidecarContext, result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 171) — A finished build as it may go out NOW: with the switch off since, or its passage held out since, nothing of it is delivered.
- `class RegionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 271)
- `class FigureRequestInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 276)
- `offered_spans(vault: Any, repository: Any, origin: str, offer_ref: str | None) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 290) — The ``(extraction_id, span_id)`` blocks the judgment ``offer_ref`` said were explorable: the library organizer's notes (RW4a) or the Reader tutor's answer (RW1c), as stored, each confirmed by the verdict's own ``judgment_ledger`` row (Codex review F3: the append-only ledger, not…
- `tutor_figure_goal(repository: Any, offer_ref: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 340) — RW5d: the ``figure_goal`` the Reader tutor's stored answer ``offer_ref`` wrote (its text and the cited spans it grounds in), read from the stored output only (as :func:`offered_spans` reads its explorable blocks): the press makes no model call, and a goal the answer did not writ…
- `reader_figure_request(ctx: SidecarContext, params: FigureRequestInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 507) — "Make this explorable": refused at once for held-out material or a switch that is off; otherwise a build job (read it with reader.figure_job).
- `class AnchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 519)
- `class ReadingAtInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 528)
- `class HostRefInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 533) — References only, each verified on the server (spec §7.1).
- `class FigureRequestV1Input(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 549) — ``FigureRequestV1`` (spec §7.1).
- `figure_request(ctx: SidecarContext, params: FigureRequestV1Input) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 566) — RW5d P1 "show me": one request for every host (module docstring); a build job.
- `class FigureReviseInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 583)
- `reader_figure_revise(ctx: SidecarContext, params: FigureReviseInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 597) — "Not right?": a new version with the learner's note (a build job).
- `class FigureJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 648)
- `reader_figure_job(ctx: SidecarContext, params: FigureJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 653) — A figure build's state, at once (never a wait on the request path).
- `reader_figure_job_cancel(ctx: SidecarContext, params: FigureJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 666)
- `class FiguresInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 676)
- `reader_figures(ctx: SidecarContext, params: FiguresInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 681) — The open source's figures as the Reader shows them (no model call).
- `class RichCancelInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 721)
- `figure_rich_cancel(ctx: SidecarContext, params: RichCancelInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 726) — RW5d P2b: cancel a rich build (the fuller animation, or a rich-only figure's pending line).
- `class RichRetryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 747)
- `figure_rich_retry(ctx: SidecarContext, params: RichRetryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 752) — RW5d P2b (Codex review F9): try a rich build again that ended with no row (interrupted when LearnLoop stopped, or stopped with code's reason).
- `class ManimOptInInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 793)
- `figure_manim_opt_in(ctx: SidecarContext, params: ManimOptInInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 798) — RW5d P2b (spec §9b.3, Q17): the standing opt-in for Manim figures, asked once inline on a press: "allow" writes ``figures.manim_opt_in = "standing"`` with the date; "not now" writes ``"declined"`` (Manim stays off the menu and is not asked again; settings can change it, and revo…
- `class FigurePredictInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 827)
- `reader_figure_predict(ctx: SidecarContext, params: FigurePredictInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 834) — The learner's prediction: stored, the observed before/after readout returned, matched decided by code.
- `class FigureExplainInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 865)
- `reader_figure_explain(ctx: SidecarContext, params: FigureExplainInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 871) — "What changed, and why?" (optional, once).
- `class AttemptHost` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 895) — An attempt host's verified references (§7.1: each resolved on the server, never the client's word): ``practice`` (the answer box: its submission key and practice session), ``workbench`` (a problem bound to the item) or ``feedback`` (a committed attempt, or a submission that has…
  - `counts(self) -> bool` (line 913; public) — An open attempt: a figure here is one hint-equivalent.
  - `ref(self) -> dict[str, Any]` (line 918; public) — The verified references as the request row keeps them.
  - `record(self) -> dict[str, Any]` (line 926; public)
  - `cost_line(self) -> str` (line 931; public)
- `attempt_view(view: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 947) — A figure's view as an attempt host shows it (ruling R1): never its fuller (Manim) version, which stays Reader-side.
- `attempt_aliases(repository: Any, item_id: str, submission_id: str | None, workbench_session_id: str | None) -> tuple[frozenset[str], frozenset[str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 976) — Codex review F3: every identity of the one attempt in progress (Reader CA2's aliases, ``reader.workbench.attempt_identities``): the answer box's draft keys handed into Work in Steps and the workbenches they were handed into, so a figure is counted once across every host of the a…
- `take_step_available(vault: Any, repository: Any, item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1012) — Whether a check on your own on ``item_id`` takes help (the ladder's take step, as the hint panel's): a "Check once" served cold with the help header, or a due cold follow-up under Reader CA2's conversion rule (``ask.cold_help_converts``, mvp-0.34).
- `record_attempt_figure(ctx: SidecarContext, attempt: dict[str, Any], figure_id: str, *, chooser_row: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1231) — §11.2: a figure going out on an attempt host.
- `class TakeStepInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1350)
- `figure_take_step(ctx: SidecarContext, params: TakeStepInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1358) — §11.3, G-SM16: *show me* on a check on your own.
- `class FigureOpenInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1407)
- `figure_open(ctx: SidecarContext, params: FigureOpenInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1414) — §11.4: open a stored figure on an attempt host (the chooser's ``explore_figure`` line lands as one line that opens it).

### Module constants

- `FIGURE_RPCS` ([src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 81)
- `_LATER_HOST_REFS` ([src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 368)
- `TAKE_STEP_REQUIRED` ([src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 891)
- `HELP_OFF_MESSAGE` ([src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 939)
- `RICH_READER_ONLY` ([src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 943)

### Explicit exports

`__all__` declares:

- `FIGURE_RPCS`
- `AttemptHost`
- `deliver_figure`
- `prompt_contract_fields`
- `record_attempt_figure`
- `take_step_available`

## Internal implementation anchors

- `_require(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 140)
- `_refused(exc: FS.FigureRefused) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 147)
- `_event(repository: Any, event: str, payload: dict[str, Any], *, extraction_id: str | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 151)
- `_jobs(ctx: SidecarContext) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 161)
- `_wake_gap_worker(ctx: SidecarContext) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 207) — A queued learner-text job wakes the post-attempt worker's ``gaps`` slot, which starts lazily (Codex review F6).
- `_rich_spawner(ctx: SidecarContext, vault: Any, *, granted: bool=True) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 214) — RW5d P2b (spec §8.6, SM9): how a build starts its rich job on the durable queue.
- `_start(ctx: SidecarContext, request: FS.FigureRequest, *, attempt: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 237)
- `_same_goal(left: str | None, right: str | None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 363)
- `_host_caller(vault: Any, repository: Any, *, origin: str, host_ref: dict[str, Any], offer_ref: str | None) -> Any | None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 371) — The caller a request's question-event reference determines, or None when it names none (Codex review F2).
- `_request_figure(ctx: SidecarContext, *, origin: str, extraction_id: str | None, span_ids: list[str], region: dict[str, Any] | None, goal_text: str | None, reading_at: dict[str, Any] | None, offer_ref: str | None, host_ref: dict[str, Any], cold_active: bool, span_keys: list[str] | None=None, take_step: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 405) — One figure request, from either RPC: validated, its caller derived and its held-out material refused here, on the request path, before any job or model call; then a build job.
- `_retry_plan_waits(ctx: SidecarContext, lines: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 706)
- `_prediction_assist(vault: Any, repository: Any, figure_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 851) — RW5d P3 (Codex review F7): the open attempt's figure row a prediction is made under (:func:`learnloop.figures.help.open_assist_for`), while figures in attempts are on; else None (formative only, as before).
- `_refuse_rich(row: dict[str, Any] | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 956) — Ruling R1: a rich figure is never opened or revised on an attempt host.
- `_help_required(vault: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 963)
- `_help_off_line(attempt: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 968) — Codex review F5: what a delivery answers when figures in attempts were switched off between the request and the delivery (nothing shown, nothing recorded).
- `_token_row_matches(row: dict[str, Any] | None, *, item_id: str, session_id: str | None, kind: str, submissions: frozenset[str], workbenches: frozenset[str]) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 990) — Whether a take step's row is this attempt's (Codex review F1): the same item, unattached, under one of the attempt's identities (its aliases included), and, for an answer-box row, in the same practice session as the request.
- `_item_cold(vault: Any, repository: Any, item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1006)
- `_committed_attempt(repository: Any, item_id: str, submission_id: str | None, *, session_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1037) — The attempt ``submission_id`` committed, or None (Codex re-review F1).
- `_sole_open_session(repository: Any, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1062) — Codex re-review F1: the answer box's session is the one open session.
- `_attempt_host(ctx: SidecarContext, vault: Any, repository: Any, host_ref: dict[str, Any], *, take_step: str | None=None, for_take_step: bool=False) -> AttemptHost` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1080) — Resolve an attempt host's references on the server (§7.1, §7.2).
- `_attempt_caller(vault: Any, repository: Any, host: AttemptHost) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1154) — The caller an attempt host determines (§7.2): an open attempt retrieves under ``assisted_practice`` for its item (a converted check too: its take step made it practice with help), feedback under the item's post-attempt policy; caller kind ``learner`` (origin ``ask``).
- `_request_attempt_figure(ctx: SidecarContext, vault: Any, repository: Any, *, goal: str | None, host_ref: dict[str, Any], take_step: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1180) — The Ask panel's *show me* on an attempt host (§6.4): verified, the caller derived, a check on your own refused without its take step, then a build job whose delivery records the figure on the attempt.
- `_figure_overlap(item: Any, row: dict[str, Any]) -> float` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1212)
- `_reveal_written(connection: Any, item_id: str, basis: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1220) — Whether this figure's reveal was already written for the item since its last attempt (a delivery read again writes it once).
- `_refuse_own_blocks(vault: Any, repository: Any, item_id: str, row: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1322) — A figure placed at or built from the item's own blocks (its exercise, solution or worked answer) is never opened or revised on its attempt.
- `_workbench_snapshot(repository: Any, workbench_session_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/figures.py), line 1334) — The problem's live steps as a workbench help row keeps them (ids, numbers and content hashes: ``hints.report_workbench``'s work at delivery), or None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `_item_cold`; statically calls `_item_cold`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `unit_origin`, `unit_token`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal_strict`, `reveal_episode_id`; calls `record_reveal_strict`, `reveal_episode_id`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_reserved`; calls `exam_reserved`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure`, `has_tables`, `superseding`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `bind_figure`, `insert_assist`, `open_figure_rows`, `submission_committed`, `submission_session_conflict`, `take_step`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `manim_opt_in`, `offerable_blocks`, `tutor_explorable_yes`, `tutor_figure_goal_offered`; calls `manim_opt_in`, `offerable_blocks`, `tutor_explorable_yes`, `tutor_figure_goal_offered`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `COST_LINES`, `FIGURE_LEVEL`, `TAKE_STEP_BANNER`, `chain_root`, `figure_keys`, `open_assist_for`, `reveal_text`; calls `chain_root`, `figure_keys`, `open_assist_for`, `reveal_text`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; calls `attempt_hosted_job`, `due_for_plan_retry`, `manim_opt_in_needed`, `manim_runtime_state`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `FigureRequest`, `anchored`, `attempt_hosted`, `build_figure`, `check_request`, `enabled`, `figure_offers_enabled`, `figure_view`, `figure_withheld`, `help_enabled`, `list_figures`, `predictions_enabled`, `record_explanation`, `record_prediction`, `redelivered_view`, `region_enabled`, `resume_rich_intents`, `retry_rich_job`, `revision_request`, `revisions_enabled`, `rich_enabled`, `rich_pending`, `rich_revision_retry`, `rich_row`, `show_me_enabled`, `shown_figure`, `sketch_enabled`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `module`; calls `reveal_amount`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`, `caller_for_question_event`; calls `caller_for`, `caller_for_question_event`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `cold_followup_view`, `served_check`; calls `cold_followup_view`, `served_check`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `apply_config_updates`; calls `apply_config_updates`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `attempt_identities`, `session_row`, `submission_id_for`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `item_exclusions`; calls `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; calls `ask_row`, `ledger_explorable`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`, `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `live_workbench_steps`; calls `live_workbench_steps`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `LibraryJobs`, `_job_payload`, `reader_caller`; calls `LibraryJobs`, `_job_payload`, `reader_caller`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `require_owned_session`; calls `require_owned_session`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `_item_cold`; calls `_item_cold`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `require_identity`; calls `require_identity`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — direct import
  - `test_f1_a_context_neighbour_held_out_after_authoring_withholds_the_figure`
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_a_check_that_takes_no_help_refuses_the_take_step`
  - `test_take_step_availability_follows_the_hint_ladders_take_step`
  - `test_the_sidecar_never_offers_a_figure_cold_or_switched_off`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f1_a_take_step_token_from_another_session_is_not_this_attempts`
  - `test_f3_the_same_figure_opened_on_the_answer_box_and_in_work_in_steps_counts_once`
  - `test_f5_switched_off_between_the_build_and_the_delivery_nothing_is_shown_or_counted`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_retrieved_passage_held_out_later_withholds_the_figure`
- [tests/test_figures_show_me_codex_review.py](../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
  - `test_f4_a_home_held_out_after_construction_withholds_the_figure`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_kept_build_results_fuller_line_is_read_again_from_the_current_rows`
  - `test_a_kept_result_naming_a_ready_fuller_version_is_not_delivered_once_its_inputs_are_protected`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw5a_rpcs_are_all_of_them`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/figures.py](../../../../../../src/learnloop_sidecar/handlers/figures.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
