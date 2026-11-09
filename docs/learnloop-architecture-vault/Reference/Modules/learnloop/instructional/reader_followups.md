---
title: "learnloop.instructional.reader_followups"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/reader_followups.py"
source_paths:
  - "src/learnloop/instructional/reader_followups.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.instructional.reader_followups module"
  - "src/learnloop/instructional/reader_followups.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.reader_followups`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.reader_followups` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Reader workbench RW6b part 1: cold follow-ups, the owner's "short unfamiliar problem" (spec_reader_workbench_v1 §9.3-§9.6; UX §4.8-§4.9, S15; gates G26, G27, G35, G49).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py) |
| Source lines | 1908 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FollowupError(ValueError)` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 142) — A refused follow-up request (nothing was written).
- `followups_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 154) — Follow-ups are live: the vault is at the successor (``READER_FOLLOWUPS_VERSIONS``, mvp-0.39; Codex review F4) and ``followups.enabled`` is on (default).
- `formative_questions_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 166)
- `max_wait_days(vault: Any) -> int` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 170)
- `class Question` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 179) — One open question a later independent attempt could answer.
  - `intent(self) -> str` (line 195; public)
  - `as_dict(self) -> dict[str, Any]` (line 198; public)
- `pending_cold_retry(vault: Any, repository: Repository, *, facet_id: str, attempt_ids: Sequence[str], learning_object_ids: Sequence[str], now: datetime) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 225) — mvp-0.38's interaction: a repair ``cold_retry`` still pending (or served) that owns the claim: the item it measures assesses the claim's facet, on one of the claim's attempts or on the claim's learning objects (Codex review F11: ownership is by the assessed facets, never the sou…
- `open_questions(vault: LoadedVault, repository: Repository, summary: Mapping[str, Any], *, now: datetime) -> tuple[list[Question], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 244) — The session's open questions and the notes on what was not asked (typed).
- `revealed_families(vault: Any, repository: Repository, session: RS.ReaderSession) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 386) — The families of every item whose answer the session revealed (the reveal ledger).
- `constraints_for(question: Question, *, exclude_family_ids: Sequence[str], exclude_item_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 402) — The ``PracticeConstraints`` mapping for one question (§9.3 item 2, exactly), plus ``exclude_item_ids``: the items an explicit learner choice decides (Codex review F2), never valued as an automatic check.
- `committed_items(vault: Any, connection: Any, *, own: Iterable[str]=()) -> set[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 420) — Items some commitment other than ``own`` decides (DL2 §5.3's resolution): a learner's Pause, Master, Learn, Keep, reference-only or their own "Check once", or another session's follow-up.
- `query_for(vault: Any, question: Question) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 439)
- `default_search(vault: LoadedVault, repository: Repository, *, injections: Mapping[str, Any], rerank_client: Any | None=None, clock: Clock | None=None) -> Search` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 451) — ``find_practice`` as every caller runs it (``propose_practice``: the one hypothesis-ref contract, the service's daily cap, the Reader's caller context), system-initiated.
- `followup_spend(vault: Any, repository: Repository, clock: Clock | None=None) -> Iterator[None]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 523) — ``followups.max_daily_cost_usd`` and ``source_service.max_daily_cost_usd`` together: a metered relevance call reserves in both, so whichever is reached first stops it (§9.3 item 6).
- `retention_due(vault: LoadedVault, repository: Repository, *, practice_item_id: str, attempt: Mapping[str, Any] | None, now: datetime) -> tuple[datetime | None, str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 546) — When forgetting is expected for the practiced item, from FSRS.
- `date_for(vault: LoadedVault, repository: Repository, *, purpose: str, practice_item_id: str | None, attempt: Mapping[str, Any] | None, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 593) — ``{"due_hint": YYYY-MM-DD, "basis", "capped"}``: never today, never past the time cap.
- `digest_id_for(extraction_id: str, session_key: str) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 616)
- `purpose_text(vault: Any, purpose: str, learning_object_ids: Sequence[str], novelty: str | None) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 775) — Learner-facing purpose wording (G16: never "error" or "mistake" about the learner's work).
- `why_text(purpose: str, check: Mapping[str, Any], mode: str | None) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 786)
- `plan_session(vault: LoadedVault, repository: Repository, *, extraction_id: str, session: RS.ReaderSession, search: Search | None, now: datetime, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 813) — Plan the follow-ups of one ended reader session; returns its digest row.
- `licensing_entry(question: Question) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1011) — One licensing question as a chosen line carries it (round 6): the key and everything the serve-time gate and re-valuation read, written at publication, so neither looks into the receipt's question entries.
- `sessions_to_plan(vault: LoadedVault, repository: Repository, *, now: datetime) -> list[RS.ReaderSession]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1136) — Ended reader sessions (no visit for the 30-minute gap) within the time cap with no planned digest.
- `plan_ended_sessions(vault: LoadedVault, repository: Repository, *, search: Search | None, now: datetime, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1158) — Plan every ended session waiting for its follow-ups (the background job).
- `revalue_pending(vault: LoadedVault, repository: Repository, *, now: datetime, valuer: Callable[..., Mapping[str, Any]] | None=None, clock: Clock | None=None, force: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1246) — Re-value every pending follow-up once a local day, before the plan is built, with no model call (Codex review F5).
- `exposure_refresh_waiting(repository: Repository) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1434) — Whether the last re-valuation kept a check for the exposure refresh (cheap: the digests only).
- `refresh_exposure(vault: LoadedVault, repository: Repository, *, now: datetime, clock: Clock | None=None, judge_client: Any | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1443) — The background half of re-valuation (Codex review F5): for each pending check the last re-valuation kept only because a worked example studied since was never judged against it, ask the exposure rule's judge (route ``worked_example_equivalence``) under BOTH daily envelopes (:fun…
- `answered_since(vault: Any, repository: Repository, question: Mapping[str, Any], *, since: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1493) — How the question was answered since ``since``, or None (still open).
- `default_valuer(vault: LoadedVault, repository: Repository, *, estimator: Any | None=None) -> Callable[[Mapping[str, Any], str], Mapping[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1672) — ``discriminating.value_request`` for one committed item, system-initiated, with the follow-ups' familiarity discount (G35, F12) and the question's pending repair decision (F7).
- `undo_followup(repository: Repository, *, commitment_id: str, reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1716) — Retire one follow-up the learner undid, with their optional reason.
- `undo_all(repository: Repository, *, digest_id: str, reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1753) — Retire every pending follow-up from one session ("undo all").
- `restore_followup(repository: Repository, *, commitment_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1768) — Undo a retirement (re-valuation's or the learner's own undo): the check is pending again, and re-valuation leaves it to the learner from then on.
- `coming_up(vault: LoadedVault, repository: Repository, *, extraction_id: str | None, now: datetime, retired_after: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1802) — The scheduled checks as a dated timeline (next three, then later) and the retirements since ``retired_after`` as good news.
- `now_utc(clock: Clock | None=None) -> datetime` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1871)

### Module constants

- `FOLLOWUPS_VERSION` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 95)
- `VIA` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 96)
- `ENVELOPE` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 98)
- `OWNER_KIND` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 99)
- `UNDO_TASK` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 101)
- `UNDO_REASON_CHARS` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 103)
- `NEXT_SHOWN` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 105)
- `PURPOSE_DISCRIMINATING` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 107)
- `PURPOSE_RETENTION` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 108)
- `INTENT_BY_PURPOSE` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 109)
- `NOVELTY_SAME_SURFACE` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 111)
- `NOVELTY_NEW_PROBLEM` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 112)
- `NOVELTY_LABELS` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 113)
- `RETIRE_ANSWERED` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 117)
- `RETIRE_BELOW_STOP` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 118)
- `RETIRE_UNDONE` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 119)
- `RETIRE_EXPOSED` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 122)
- `RETIRE_REPAIR_OWNS` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 124)
- `RETIRE_UNREADABLE` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 129)
- `KEPT_REFRESH` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 132)
- `ANSWERED_SOLVED` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 135)
- `ANSWERED_RIVALS` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 136)
- `CHECK_VERDICTS` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 139)
- `REVALUATION_ATTEMPTS` ([src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py), line 1306)

### Explicit exports

`__all__` declares:

- `ENVELOPE`
- `FOLLOWUPS_VERSION`
- `FollowupError`
- `NOVELTY_LABELS`
- `PURPOSE_DISCRIMINATING`
- `PURPOSE_RETENTION`
- `Question`
- `UNDO_TASK`
- `VIA`
- `coming_up`
- `committed_items`
- `constraints_for`
- `date_for`
- `default_search`
- `default_valuer`
- `digest_id_for`
- `exposure_refresh_waiting`
- `followup_spend`
- `followups_enabled`
- `open_questions`
- `pending_cold_retry`
- `plan_ended_sessions`
- `plan_session`
- `purpose_text`
- `refresh_exposure`
- `restore_followup`
- `retention_due`
- `revalue_pending`
- `revealed_families`
- `sessions_to_plan`
- `undo_all`
- `undo_followup`

## Internal implementation anchors

- `_config(vault: Any) -> Any` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 150)
- `_item_lo(vault: Any, item_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 202)
- `_attempt_rows(repository: Repository, attempt_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 207)
- `_facet_los(vault: Any, facet_id: str) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 217)
- `_followups_envelope(vault: Any, repository: Repository, clock: Clock | None) -> Any` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 514)
- `_local_day(moment: datetime) -> date` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 538)
- `_iso(moment: datetime) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 542)
- `_workbench_spans(repository: Repository, session_ids: Sequence[str]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 620)
- `_section_spans(repository: Repository, extraction_id: str, sections: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 638) — The first span of the last section the session read (the studied passage).
- `_session_spans(vault: Any, repository: Repository, summary: Mapping[str, Any], learning_object_ids: Sequence[str], extraction_id: str) -> tuple[list[str], list[str]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 654) — The way back (§9.3 item 9; Codex review F10): the session's inquiry roots and anchor spans on these learning objects; the spans of the workbench sessions that worked an item of them and of the formative records that touched them; with none of those, the workbench and formative s…
- `_novelty(vault: Any, item_id: str, worked_item_ids: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 708) — Exact facts only (row 79): a candidate in the family of an item the session worked is ``same_surface`` and never transfer; anything else is "a new problem" until the relevance step returns ``new_application``.
- `_chosen_checks(result: Mapping[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 721) — Each section's checks that may be dated: a check verdict, a licensing regime.
- `_marginal(section: Mapping[str, Any], check: Mapping[str, Any]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 735) — P(E) under the problem's prior for a later pick, whose receipt values it conditionally (S5 records P(E) for every chosen check, §11.4 item 1): the sum the valuation's own ``_predicted`` takes, over the persisted point table.
- `_question_outcome(result: Mapping[str, Any], chosen: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 750)
- `_incomplete(result: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 770)
- `_exposure_scope(vault: Any, repository: Repository, learning_object_ids: Sequence[str], extraction_id: str) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 798) — The extractions the exposure rule's worked-example shortlist is drawn from for these learning objects (``teaching_scope``), plus the session's: the serve-time gate reads studied examples in this scope (F1).
- `_licensing_entries(line: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1025)
- `_licensing(line: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1030) — The keys of the questions that license a chosen check (its ``licensing`` list; a line without one is malformed and licenses nothing: round 7, F20).
- `_live_lines(repository: Repository, chosen: Sequence[Mapping[str, Any]]) -> dict[str, int]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1038) — ``ref -> index`` of each chosen line whose check is live (pending).
- `_undone_refs(repository: Repository, chosen: Sequence[Mapping[str, Any]]) -> set[str]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1054) — The items whose check from this digest the learner undid (and did not restore): never scheduled again by a later search of the same session.
- `_publish(vault: Any, repository: Repository, *, digest_id: str, existing: Mapping[str, Any] | None, extraction_id: str, session: RS.ReaderSession, summary: Mapping[str, Any], notes: Sequence[Mapping[str, Any]], families: Sequence[str], receipt_questions: list[dict[str, Any]], chosen: list[dict[str, Any]], commitment_ids: list[str], planned: Sequence[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]], incomplete: bool, intent_excluded: set[str], now: datetime, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1069) — F3: the commitments, the digest receipt and the queue revision in one transaction.
- `_first_version(repository: Repository, commitment_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1175)
- `_provenance(repository: Repository, commitment_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1180)
- `_events(repository: Repository, commitment_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1187)
- `_learner_kept(repository: Repository, commitment_id: str) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1191) — The learner undid a retirement (or restored an undo): re-valuation leaves it alone.
- `_solved_attempt(vault: Any, repository: Repository, *, learning_object_ids: Sequence[str], facet_ids: Sequence[str], since: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1205) — The unaided success that answered a retention question (the good news's date).
- `_today(now: datetime) -> str` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1230)
- `_gate_verdict(vault: Any, repository: Repository, *, item_id: str, provenance: Mapping[str, Any], valued_at: str, now: datetime, questions: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1234) — The serve-time gate's verdict now (exposure since valuation, repair ownership; ``scheduling.intent.followup_gate``), with no model call, by the strictest rule across the open licensing ``questions`` (F16).
- `_revaluation_decisions(vault: Any, repository: Repository, snapshot: Mapping[str, Any], *, valuer: Callable[..., Mapping[str, Any]] | None, switched_off: str | None, now: datetime, clock: Clock | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1309) — Every pending check's decision from one digest snapshot; writes nothing.
- `_commit_revaluation(repository: Repository, snapshot: Mapping[str, Any], lines: list[dict[str, Any]], *, now: datetime, today: str, clock: Clock | None) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1355) — Commit one digest's decisions, or None (nothing written) when the row is no longer the snapshot they were computed from (round 8).
- `_targets(repository: Repository, commitment_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1485)
- `_own_question(provenance: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1523) — The check's own question, from its provenance, as re-valuation reads a licensing question.
- `_revaluation_licensing(provenance: Mapping[str, Any], line: Mapping[str, Any] | None, item_id: str, receipt_keys: set[str]) -> tuple[list[dict[str, Any]], list[str], bool]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1531) — ``(licensing, pruned, unreadable)`` for one check (round 6).
- `_revaluation_line(vault: Any, repository: Repository, *, commitment_id: str, item_id: str, provenance: Mapping[str, Any], valuer: Callable[..., Mapping[str, Any]], extraction_id: str, now: datetime, clock: Clock | None, licensing: Sequence[Mapping[str, Any]]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1563) — One pending check's re-valuation.
- `_applied_exposure(*_args: Any, **_kwargs: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1665) — Re-valuation's exposure verdict inside ``value_request``: the rule was applied by :func:`_gate_verdict` with no model call (F5).
- `_require_followup(repository: Repository, commitment_id: str) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1704)
- `_retirement(repository: Repository, commitment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1788)
- `_due_hint(repository: Repository, commitment_id: str) -> str | None` ([source](../../../../../../src/learnloop/instructional/reader_followups.py), line 1866)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; statically calls `digest_id_for`, `followups_enabled`, `max_wait_days`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `module`; statically calls `coming_up`, `default_search`, `default_valuer`, `exposure_refresh_waiting`, `followups_enabled`, `plan_ended_sessions`, `refresh_exposure`, `restore_followup`, `revalue_pending`, `sessions_to_plan`, `undo_all`, `undo_followup`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `module`; statically calls `coming_up`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`, `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `READER_FOLLOWUPS_VERSIONS`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `fsrs_rating_for_attempt`; calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`, `resolve_disposition`, `retire`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/db/stores/reader_digests|learnloop.db.stores.reader_digests]] — imports `module`; calls `digest`, `digest_for_commitment`, `digest_for_session`, `digests`, `insert_digest`, `update_digest`, `without_narrative`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `extraction_units`; calls `extraction_units`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `resolve_episode_channel`
- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `module`; calls `value_request`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `module`; calls `independent_check_eligibility`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `module`; calls `pending_causal_decision`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `PolicyRefused`, `caller_for`; calls `caller_for`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `continuation_cursor`, `propose_practice`; calls `continuation_cursor`, `propose_practice`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `SCALE_LABEL`, `VALUATION_VERSION`, `recent_assisted_success`; calls `recent_assisted_success`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `disabled_reason`; calls `disabled_reason`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `item_facets`; calls `item_facets`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `ContinuationMismatch`, `PracticeConstraints`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_sessions|learnloop.reader.reader_sessions]] — imports `module`; calls `all_sessions`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; calls `_source_id`, `session_summary`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `module`; calls `initial_stability`, `interval_for_retention`
- [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]] — imports `REPAIR_RETRY_OWNS`, `followup_gate`, `open_cold_retries`, `owning_retry`; calls `followup_gate`, `open_cold_retries`, `owning_retry`
- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `STORED_RETENTION`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `Resolution`, `load_snapshots`; calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `teaching_scope`; calls `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `daily_envelope`, `midnight`; calls `SharedDailyEnvelope`, `daily_envelope`, `midnight`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `SUCCESS_CORRECTNESS`, `is_assisted`; calls `is_assisted`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]], [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]], [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c1_landing.py](../../../../../../tests/test_curriculum_c1_landing.py) — direct import
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_a_side_by_side_read_holds_a_follow_up_on_a_shown_span_and_only_there`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_with_follow_ups_off_an_ended_session_is_summarized_and_narrated`
- [tests/test_reader_followup_valuation.py](../../../../../../tests/test_reader_followup_valuation.py) — direct import
  - `test_the_default_search_is_find_practice_with_the_exact_filters_system_initiated`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_a_claim_needing_an_independent_check_is_a_retention_question`
  - `test_a_closed_probe_episode_answers_a_discriminating_question`
  - `test_a_discriminating_check_is_dated_for_the_next_days_plan`
  - `test_a_retention_check_is_dated_at_the_effective_due_within_the_cap`
  - `test_an_abstention_an_exclusion_or_an_unknown_keeps_the_check`
  - `test_coming_up_is_a_dated_timeline_next_three_then_later`
  - `test_each_follow_up_is_a_test_me_later_commitment_with_its_provenance`
  - `test_formative_records_add_questions_only_with_their_switch`
  - `test_only_ended_sessions_wait_for_planning`
  - `test_only_reader_follow_ups_can_be_undone_here`
  - `test_rebuild_shadow_is_zero_with_follow_ups_present`
  - `test_revaluation_retires_a_check_that_no_longer_clears_the_stop`
  - `test_revaluation_retires_a_follow_up_answered_since_with_its_reason`
  - `test_revealed_families_are_the_sessions_reveals_only`
  - `test_the_cards_good_news_names_how_the_question_was_answered_and_drops_a_restored_check`
  - `test_the_exact_filters_reach_find_practice_admission`
  - `test_the_kill_switch_creates_nothing_and_runs_no_revaluation`
  - `test_the_provenance_carries_the_way_back_and_dl2_renders_it`
  - `test_the_search_is_asked_with_the_exact_filters`
  - `test_the_spend_envelopes_are_the_followups_and_the_services`
  - `test_the_valuation_is_the_sources_specs_machinery`
  - `test_undo_all_retires_every_pending_follow_up_from_the_session`
  - `test_undo_leaves_an_answered_check_answered`
  - `test_undo_takes_an_optional_reason_on_a_learner_card_verdict`
  - `test_without_fsrs_state_the_date_is_the_schedulers_first_interval`
- [tests/test_reader_followups_rereview.py](../../../../../../tests/test_reader_followups_rereview.py) — direct import
  - `test_f13_a_failure_after_the_exposure_retirement_loses_neither_the_check_nor_the_re_ask`
  - `test_f14_a_resumed_search_conditions_on_the_live_check_and_retires_nothing`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f10_a_formative_record_and_the_studied_passage_are_the_fallbacks`
  - `test_f11_a_repair_retry_scheduled_after_the_follow_up_takes_its_place`
  - `test_f11_a_retry_owns_only_the_facets_its_item_assesses`
  - `test_f12_the_production_valuer_composes_the_attempt_familiarity_discount`
  - `test_f1_an_impression_since_valuation_holds_the_check_and_revaluation_retires_and_re_asks`
  - `test_f3_a_session_another_process_planned_meanwhile_is_not_published_twice`
  - `test_f5_an_unjudged_worked_example_is_refreshed_in_the_background_under_both_envelopes`
  - `test_f5_revaluation_never_reaches_the_exposure_judge`
  - `test_f5_with_the_source_switches_off_revaluation_values_nothing_and_keeps_the_check`
  - `test_f7_an_open_causal_factor_with_competing_repairs_is_a_decision_question`
  - `test_f7_revaluation_passes_the_stored_pending_decision`
  - `test_f9_a_formative_only_retention_question_reaches_a_valuation_problem`
- [tests/test_reader_followups_round3.py](../../../../../../tests/test_reader_followups_round3.py) — direct import
  - `test_an_item_the_learner_undid_is_never_scheduled_again_by_the_same_session`
  - `test_an_item_whose_check_was_retired_is_scheduled_again_as_a_fresh_generation`
  - `test_f14_the_exact_three_search_sequence_ends_with_exactly_one_live_check`
  - `test_f15_resuming_one_question_never_abandons_the_check_another_question_shares`
  - `test_f15_revaluation_keeps_a_shared_check_while_any_licensing_question_needs_it`
  - `test_round_2s_reconciliation_reason_is_gone`
- [tests/test_reader_followups_round4.py](../../../../../../tests/test_reader_followups_round4.py) — direct import
  - `test_f16_a_shared_check_is_held_and_retired_by_retentions_rule`
- [tests/test_reader_followups_round5.py](../../../../../../tests/test_reader_followups_round5.py) — direct import
  - `test_f17_a_retention_question_reopened_since_the_revaluation_still_tightens_the_gate`
  - `test_f17_revaluation_retires_an_unreadable_check_and_re_asks_what_it_can_name`
- [tests/test_reader_followups_round6.py](../../../../../../tests/test_reader_followups_round6.py) — direct import
  - `test_f17_no_answer_state_change_can_relax_the_gate_on_a_shared_check`
  - `test_f18_re_planning_that_drops_a_question_keeps_the_shared_check_live_and_served`
- [tests/test_reader_followups_round7.py](../../../../../../tests/test_reader_followups_round7.py) — direct import
  - `test_f19_a_publication_between_the_read_and_the_write_keeps_the_restored_license`
  - `test_f19_a_question_still_absent_from_the_fresh_receipt_is_pruned`
  - `test_f20_a_line_without_a_licensing_list_is_held_and_retired_as_unreadable`
- [tests/test_reader_followups_round8.py](../../../../../../tests/test_reader_followups_round8.py) — direct import
  - `test_round8_a_changed_row_is_recomputed_and_the_second_pass_commits`
  - `test_round8_a_row_that_keeps_changing_is_left_for_the_next_pass`
  - `test_round8_a_scalar_licensing_is_unreadable_not_a_crash`
  - `test_round8_sols_interleaving_keeps_the_shared_check_live`
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_planning_and_revaluation_are_gated_by_the_tag_and_the_switch`
- [tests/test_reader_rw6b_landing.py](../../../../../../tests/test_reader_rw6b_landing.py) — direct import
  - `test_i_check_once_commitments_and_follow_ups_coexist_and_the_gate_touches_only_follow_ups`
  - `test_ii_a_rescheduled_fresh_cold_retry_holds_and_retires_an_existing_follow_up`
  - `test_ii_a_rescheduled_fresh_cold_retry_owns_the_claim_at_planning`
  - `test_iii_a_ca5a_peek_of_the_items_source_span_holds_the_follow_up`
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_historical_cutoff_reads_the_same_after_a_later_undo`

## Modification guidance

- Make changes here when the responsibility remains reader followups within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/reader_followups.py](../../../../../../src/learnloop/instructional/reader_followups.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
