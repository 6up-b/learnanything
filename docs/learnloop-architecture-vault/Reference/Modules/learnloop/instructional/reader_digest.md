---
title: "learnloop.instructional.reader_digest"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/reader_digest.py"
source_paths:
  - "src/learnloop/instructional/reader_digest.py"
source_commit: "15b8ad274b95519454101107517ec05d907f179a"
source_commit_timestamp: "2026-11-01T14:45:15-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.instructional.reader_digest module"
  - "src/learnloop/instructional/reader_digest.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.reader_digest`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.reader_digest` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Reader workbench RW6b part 2: the session narrative (spec_reader_workbench_v1 §9.2, §9.5, §9.6; UX §4.8, W14).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py) |
| Source lines | 906 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `15b8ad274b95519454101107517ec05d907f179a` |
| Commit timestamp | `2026-11-01T14:45:15-05:00` |

## Public API

- `class ReaderDigestNarrativeV1(WireModel)` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 135) — The narrative and the summary ids it cites (strict).
- `class NarrativeResult` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 143) — What one narration did.
  - `as_dict(self) -> dict[str, Any]` (line 155; public)
- `class NarrativeUnavailable(Exception)` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 159) — Refused before any call (the reason lasts only while it holds).
  - `__init__(self, reason: str, message: str) -> None` (line 162; internal)
- `digest_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 176) — RW6b part 2 as a whole (``digest.enabled``): the narrative and the router card's reader section.
- `narrative_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 183) — ``digest.enabled`` and ``digest.narrative_enabled``: off, no route call and no narrative anywhere.
- `quotes_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 190) — ``digest.narrative_quotes_inquiry`` (learner-blindness relax; default on).
- `prompt_version(vault: Any) -> str` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 196) — The narrative prompt's version: the quotes' while their switch is on.
- `models_off() -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 202)
- `citable_ids(summary: Mapping[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 214) — Every event id the typed summary carries (``ReaderSessionSummaryV1``): the inquiries' root exchanges and question events, every Ask exchange of the session, the workbench sessions and their attempts, the formative records' source events (and their inquiry roots), the gaps named…
- `count_words(text: str) -> int` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 241)
- `validate_narrative(answer: ReaderDigestNarrativeV1, summary: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 245) — Why the narrative cannot stand, or [] (code's check, spec §9.2 / G25): the text is non-empty, at most :data:`MAX_WORDS` words and free of the well's evidence markers, and it cites at least one id, every one of them in the summary.
- `inquiry_quotes(repository: Repository, summary: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 299) — The learner's own words of each inquiry root question the summary names (opened, resolved, still open; at most :data:`QUOTE_COUNT`, each at most :data:`QUOTE_CHARS` characters), keyed by the root exchange the narrative cites.
- `build_prompt(vault: Any, repository: Repository, summary: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 328)
- `exam_withheld(vault: Any, repository: Repository, summary: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 358) — Whether the session touched a passage the one exam predicate withholds (unreadable predicate: withheld, fail closed).
- `daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None=None) -> Any` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 377)
- `capped_message(vault: Any) -> str` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 386)
- `request_timeout_seconds(vault: Any, route: PaidRoute) -> float` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 391) — The route's configured per-request timeout: its provider profile's ``timeout_seconds``, else ``ai.timeout_seconds`` (``ai.client``'s own resolution).
- `narration_lease_seconds(timeout_seconds: float) -> int` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 403) — The session claim's lease (final verify F3): it outlives the route's request, so a successor can take the claim over only once the holder has stopped renewing it for longer than its request can last, which in practice means the holder died or froze.
- `class NarrativeRoute` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 426) — The narrative's pinned route for one session.
  - `__init__(self, vault: Any, repository: Repository, *, client: Any | None, envelope: Any, live: Callable[[], None] | None=None) -> None` (line 429; internal)
  - `subscription(self) -> bool` (line 446; public)
  - `price(self) -> float | None` (line 450; public)
  - `problem(self) -> NarrativeUnavailable | None` (line 453; public) — Checked before any call: the env switch, the route, the price and today's cap.
  - `ask(self, prompt: str, *, owner_id: str) -> ReaderDigestNarrativeV1` (line 467; public)
  - `model(self) -> str` (line 489; public)
- `claim_key(digest_id: str) -> str` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 499)
- `admission_problem(vault: Any, repository: Repository, *, client: Any | None=None, clock: Clock | None=None) -> NarrativeUnavailable | None` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 507) — Whether a narration would be refused now, before any call.
- `narrate_digest(vault: Any, repository: Repository, digest_id: str, *, client: Any | None=None, now: datetime, clock: Clock | None=None) -> NarrativeResult` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 579) — Write one session's narrative (§9.2), once.
- `sessions_to_summarize(vault: Any, repository: Repository, *, now: datetime) -> list[RS.ReaderSession]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 722) — Ended reader sessions within follow-ups' time cap with no digest row, while narration is on and follow-ups are not live (switched off, or the vault below their successor): the narrative's own sessions (Codex review F2; ``digest.narrative_enabled`` and ``followups.enabled`` are s…
- `summarize_ended_sessions(vault: Any, repository: Repository, *, now: datetime, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 750) — Persist the typed summary of each session :func:`sessions_to_summarize` names and had activity, as a summary-only digest row (``incomplete``, ``valuation_json.not_planned``; no commitment, no valuation, no model call), so it can be narrated (Codex review F2).
- `digests_waiting(vault: Any, repository: Repository, *, now: datetime, client: Any | None=None, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 788) — Digest rows whose ended session has no narrative yet, oldest first, or [] when narration is switched off or would be refused before any call now (so a Today build starts no job that can do nothing).
- `narrate_waiting(vault: Any, repository: Repository, *, now: datetime, client: Any | None=None, clock: Clock | None=None) -> list[NarrativeResult]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 807) — Narrate every waiting session (the background job).
- `narrative_view(vault: Any, repository: Repository, *, extraction_id: str, session_key: str | None, now: datetime, client: Any | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 831) — The session's narrative for "Last time here" and Wrap up, or None (switched off, no digest row for the session yet, or the session still running).

### Module constants

- `ROUTE_TASK` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 81)
- `PURPOSE` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 82)
- `OWNER_KIND` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 83)
- `PROMPT_VERSION` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 84)
- `QUOTES_PROMPT_VERSION` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 89)
- `QUOTE_COUNT` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 92)
- `QUOTE_CHARS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 93)
- `LEDGER_TASK` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 95)
- `LEDGER_LEFT` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 96)
- `ENVELOPE` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 97)
- `MODELS_ENV` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 98)
- `NARRATIVE_VERSION` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 99)
- `MAX_WORDS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 101)
- `LABEL` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 104)
- `AUTHORITY` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 105)
- `_CAPS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 108)
- `_INSTRUCTIONS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 110)
- `_QUOTES_INSTRUCTIONS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 122)
- `EVIDENCE_MARKERS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 129)
- `STATES` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 132)
- `CLAIM_TASK` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 496)
- `ADMISSION_REASONS` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 504)
- `_TRANSIENT` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 522)
- `_TRANSIENT_GUARD` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 523)
- `NOT_PLANNED_KEY` ([src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py), line 712)

### Explicit exports

`__all__` declares:

- `ADMISSION_REASONS`
- `AUTHORITY`
- `LABEL`
- `LEDGER_TASK`
- `MAX_WORDS`
- `NarrativeResult`
- `NarrativeRoute`
- `PROMPT_VERSION`
- `QUOTES_PROMPT_VERSION`
- `ROUTE_TASK`
- `ReaderDigestNarrativeV1`
- `admission_problem`
- `build_prompt`
- `inquiry_quotes`
- `prompt_version`
- `quotes_enabled`
- `citable_ids`
- `count_words`
- `digest_enabled`
- `digests_waiting`
- `narrate_digest`
- `narrate_waiting`
- `narration_lease_seconds`
- `narrative_enabled`
- `narrative_view`
- `request_timeout_seconds`
- `sessions_to_summarize`
- `summarize_ended_sessions`
- `validate_narrative`

## Internal implementation anchors

- `_config(vault: Any) -> Any` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 172)
- `_ids(values: Iterable[Any]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 210)
- `_dedupe(values: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 271)
- `_titles(vault: Any, repository: Repository, summary: Mapping[str, Any]) -> dict[str, dict[str, str]]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 284)
- `_anchor_keys(summary: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 345)
- `_vault_key(vault: Any) -> str` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 526)
- `_note(vault: Any, digest_id: str, status: str | None, reason: str | None=None) -> None` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 530)
- `_transient(vault: Any, digest_id: str) -> tuple[str, str | None] | None` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 538)
- `_session_ended(row: Mapping[str, Any], now: datetime) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 543)
- `_record(repository: Repository, row: Mapping[str, Any], *, narrative: str | None, cited: Sequence[str], model: str, prompt: str, reasons: Sequence[str], words: int | None, clock: Clock | None, claim: Any | None=None, version: str=PROMPT_VERSION) -> bool` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 548) — The narrative (or the drop) and its verdict, in one transaction.
- `_narrate_claimed(vault: Any, repository: Repository, row: Mapping[str, Any], summary: Mapping[str, Any], result: NarrativeResult, claim: Any, route: NarrativeRoute, *, clock: Clock | None) -> NarrativeResult` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 650) — The narration itself, under the session's claim (Codex re-review F3).
- `_not_planned_reason(vault: Any) -> str` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 715)
- `_landed(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/reader_digest.py), line 825)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `module`; statically calls `admission_problem`, `digests_waiting`, `narrate_waiting`, `narrative_enabled`, `sessions_to_summarize`, `summarize_ended_sessions`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `module`; statically calls `narrative_enabled`, `narrative_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `enforced_total_seconds`; calls `enforced_total_seconds`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `READER_FOLLOWUPS_VERSIONS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_withheld`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/reader_digests|learnloop.db.stores.reader_digests]] — imports `module`; calls `digest`, `digest_for_session`, `digests`, `insert_digest`, `set_narrative`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `module`; calls `_LeaseLost`, `_claimed`, `_holds`, `_renew_live`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; calls `digest_id_for`, `followups_enabled`, `max_wait_days`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/reader/reader_sessions|learnloop.reader.reader_sessions]] — imports `module`; calls `all_sessions`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; calls `_sections`, `session_summary`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `math`, `os`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]], [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chat_total_transport_deadline.py](../../../../../../tests/test_chat_total_transport_deadline.py) — direct import
  - `test_rw6b2_f3_a_dribbling_narration_request_ends_inside_its_lease_and_publishes_nothing`
  - `test_rw6b2_f3_the_narration_lease_is_the_enforced_bound_plus_the_claim_margin`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_switched_off_the_narrative_prompt_is_todays_exactly`
  - `test_the_narrative_may_quote_the_learners_inquiry_words_under_the_same_checks`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_a_citation_outside_the_summary_or_none_at_all_is_refused`
  - `test_a_holder_that_stops_renewing_is_taken_over_only_after_its_request_timed_out`
  - `test_a_lease_lost_before_the_request_sends_nothing_and_writes_nothing`
  - `test_a_lease_lost_during_the_call_never_publishes_and_the_answer_is_not_paid_twice`
  - `test_a_metered_route_past_todays_cap_is_capped_and_sends_nothing`
  - `test_a_narrative_written_meanwhile_never_supersedes_part_1s_plan`
  - `test_a_provider_failure_is_retried_later_and_then_lands`
  - `test_a_session_on_exam_material_is_never_sent`
  - `test_a_spend_stop_inside_the_call_is_capped`
  - `test_a_successor_never_sends_while_the_holder_renews_past_its_original_lease`
  - `test_a_waiting_session_reads_pending_and_a_running_one_reads_nothing`
  - `test_an_invalid_citation_drops_the_narrative_records_why_and_is_never_paid_again`
  - `test_an_overlong_narrative_is_dropped`
  - `test_an_unpriced_metered_route_is_refused_before_sending`
  - `test_below_the_follow_ups_successor_the_summary_row_says_so`
  - `test_citable_ids_are_the_summarys_event_ids`
  - `test_no_summary_row_with_narration_off_or_follow_ups_live`
  - `test_overlapping_narrations_from_two_repositories_pay_once`
  - `test_rebuild_shadow_is_zero_with_a_narrative_present`
  - `test_switched_off_there_is_no_route_call_and_no_narrative_anywhere`
  - `test_the_card_and_wrap_up_carry_the_landed_narrative`
  - `test_the_narration_lease_outlives_the_routes_request_timeout`
  - `test_the_narrative_is_written_once_even_when_two_writers_race`
  - `test_the_narrative_is_written_once_from_the_typed_summary_with_valid_citations`
  - `test_the_plan_down_means_no_narrative_and_no_other_provider`
  - `test_the_prompt_carries_the_typed_summary_and_never_the_learners_words`
  - `test_the_wells_evidence_markers_never_appear_in_a_narrative`
  - `test_the_word_bound_is_120_words`
  - `test_with_follow_ups_off_an_ended_session_is_summarized_and_narrated`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
  - `test_i_a_narrative_write_invalidates_c1s_memo_once_and_the_choice_is_the_same`
  - `test_ii_digest_off_is_the_predecessor_card_byte_for_byte_on_a_c1_plan`
  - `test_iii_the_narration_claim_and_the_reading_path_claims_are_distinct_and_independent`
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_a_narrative_written_after_the_cutoff_is_not_shown_at_it`
  - `test_narration_switched_off_after_a_narrative_was_saved_shows_it_nowhere`

## Modification guidance

- Make changes here when the responsibility remains reader digest within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/reader_digest.py](../../../../../../src/learnloop/instructional/reader_digest.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
