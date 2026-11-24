---
title: "learnloop.intent.inline_administration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/intent/inline_administration.py"
source_paths:
  - "src/learnloop/intent/inline_administration.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.intent"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.intent.inline_administration module"
  - "src/learnloop/intent/inline_administration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-intent"
---

# `learnloop.intent.inline_administration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.intent.inline_administration` exists within [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] to own the behavior summarized by its module contract: Inline cold checks in the Reader (spec §12.6; mvp-0.69): the administration protocol of a due "Check once" where the learner reads, beside Today's (decision D2: the Reader adds a place, not a rule).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py) |
| Source lines | 953 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InlineCheckError(Exception)` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 61)
  - `__init__(self, code: str, message: str, details: Mapping[str, Any] | None=None) -> None` (line 62; internal)
- `class Opened` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 70) — A check's commitment and what begin found about it.
- `host_places(repository: Any, learning_object_ids: Iterable[str]) -> tuple[set[tuple[str, str]], set[str]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 108) — Where each LO is taught as the desks place it: its primary passage's section and every goal path's section for it (the host a check's marker sits before).
- `protection(vault: Any, repository: Any, opened: Opened, visible: Mapping[str, Any], covered: Covered) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 132) — What is veiled of ``visible`` while this check is open, and how it was decided.
- `narrow(veiled: list[dict[str, Any]], judgment: Any | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 217) — The Decider's seam (spec §12.6.3): once the reveal adjudication judgment exists it may un-veil what it judges states nothing of the answer.
- `being_answered(repository: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 260) — The commitments an open inline administration holds (the lock Today honours).
- `union(veil_sets: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 267) — Everything veiled by an administration's veil sets (deduplicated, in order) and what was opened by the last.
- `find(repository: Any, token: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 280)
- `cold_presentation(served: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 307) — The learner-facing cold presentation of a served item (an allowlist): what the card shows, and nothing it could read the answer from.
- `eligibility_of(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 332) — The serve-time Check once reason the item is not cold now (``ELIGIBILITY_WORDS``), or None when it is.
- `refuse_open_elsewhere(repository: Any, commitment_id: str) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 349) — Another commitment's administration is open: refused, naming it.
- `preflight(vault: Any, repository: Any, *, request_id: str, commitment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 365) — The answers ``begin`` gives before it reads the serving view, for a caller that would otherwise do work first (start a practice session for a check that cannot open).
- `begin(vault: Any, repository: Any, *, request_id: str, commitment_id: str, session_id: str, visible: Mapping[str, Any], serve: Callable[[str], Mapping[str, Any]], covered: Covered, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 418) — Open an inline administration: the item, the frozen contract (``serve``: Today's own session serve of the item, which freezes it), every candidate with its key, the cold presentation, the protection and its first veil set, all before the prompt is returned.
- `veils(repository: Any, token: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 453) — The administration's veils: everything veiled, what was opened, the standing set (veiled and not opened) and the revision (the last veil set's sequence number).
- `protect_more(vault: Any, repository: Any, *, token: str, visible: Mapping[str, Any], covered: Covered, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 496) — Veil what came into view (navigation, a new window, a search): a veil set of the additions only.
- `measured(repository: Any, ref: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 523) — Whether what opening this ref shows can be measured against the answer keys: a source passage's text, text pad blocks, tutor exchanges and search rows naming one of those.
- `with_measured(repository: Any, refs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 551)
- `expose(vault: Any, repository: Any, *, token: str, ref: Mapping[str, Any], kind: str, exposure_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 606) — Record what the learner did that is exposure, at once, with its reveals, in one transaction (all of it or none: a refusal or failure records nothing, and the veil must stay).
- `revealed(text: str, key: str) -> float` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 717) — How much of an answer key an opened text shows: the tutor's overlap rule (inherited until the Decider judges reveals), and the whole key stated as whole words counts in full whatever its length (the overlap rule scores a short key such as "osmosis" zero when a passage states exa…
- `cold_now(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 731) — Whether the check's item could still be answered cold now: the Check once decision over the reveal ledger, where every opening (measured, or unmeasured at the priming threshold) is.
- `prepare_submit(vault: Any, repository: Any, *, token: str, submission_id: str, veils_revision: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 741) — Before the attempt: reserve the submission on the administration (a crash after the attempt is found by it), with whether the check was pending then.
- `notes_opened(admin: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 775) — Whether the learner opened a note's veil during this administration (an exposure event with unmeasured notes).
- `attempt_submission_key(submission_id: str) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 783) — The attempt service's own idempotency key for an inline submission.
- `finish_submit(vault: Any, repository: Any, *, token: str, attempt_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 789) — After the attempt: settle as for any qualifying attempt (the check is answered only if this attempt is its first on-your-own, cold one), then close the administration with the attempt and the outcome it promises, in one transaction.
- `outcome(vault: Any, repository: Any, *, admin: Mapping[str, Any], clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 814) — Whether the administration's attempt answered its check, and why not when it did not: the reason, and the Check once decision's own reason at the attempt (``eligibility``: a hold, the answer shown).
- `release(repository: Any, *, token: str, submission_id: str, attempt_for: Callable[[str, str], str | None]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 861) — A reservation no attempt was accepted for is undone (the attempt service refused: grading unavailable, the item gone, the session elsewhere), so the card can be answered again or set aside.
- `abandon(vault: Any, repository: Any, *, token: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 875) — "Not now": closed with no attempt; the duty stays pending and what was opened stays in the reveal ledger.
- `reopen(vault: Any, repository: Any, *, attempt_for: Callable[[str, str], str | None], clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 911) — The restart read: the open administration, or None.

### Module constants

- `SURFACE` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 43)
- `METHOD` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 46)
- `PRIMED_BY_NOTE` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 48)
- `METHOD_WHOLE_SOURCES` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 50)
- `PLACED_KINDS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 53)
- `OPENED_BASIS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 55)
- `DUE_ONLY` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 57)
- `BELOW_TAG` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 58)
- `_DISPLAY_KEYS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 94)
- `ELIGIBILITY_WORDS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 290)
- `UNMEASURED_BASIS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 296)
- `MEASURED_BLOCK_KINDS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 299)
- `PRESENTATION_KEYS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 303)
- `INTENT_CHECK_KEYS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 304)

### Explicit exports

`__all__` declares:

- `host_places`
- `BELOW_TAG`
- `Covered`
- `InlineCheckError`
- `METHOD`
- `METHOD_WHOLE_SOURCES`
- `OPENED_BASIS`
- `Opened`
- `PLACED_KINDS`
- `SURFACE`
- `UNMEASURED_BASIS`
- `abandon`
- `attempt_submission_key`
- `begin`
- `being_answered`
- `cold_now`
- `cold_presentation`
- `eligibility_of`
- `expose`
- `find`
- `finish_submit`
- `measured`
- `narrow`
- `outcome`
- `preflight`
- `prepare_submit`
- `protect_more`
- `protection`
- `release`
- `reopen`
- `revealed`
- `union`
- `veils`
- `with_measured`

## Internal implementation anchors

- `_now(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 81)
- `_require_tag(vault: Any) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 85)
- `_ref_key(ref: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 97)
- `_window_group(kind: str) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 207)
- `_check(vault: Any, repository: Any, commitment_id: str, *, clock: Clock | None) -> Any` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 227)
- `_learning_objects(vault: Any, repository: Any, commitment_id: str, candidates: Iterable[str]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 234)
- `_open_in_today(repository: Any, candidates: Iterable[str]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 245) — Today shows one of the check's items now: the current practice session's checkpoint names it (written when the item is shown, whether or not an answer is typed yet).
- `_frozen_candidates(vault: Any, candidates: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 318) — Every item that can settle the check (the serving view's candidates, ``build_checks``'s one expansion), each with its LO and its answer key as they are now: what an opening is charged to and measured against.
- `_terminal(admin: Mapping[str, Any]) -> InlineCheckError` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 360)
- `_record_gap(vault: Any, repository: Any, admin: Mapping[str, Any], request_id: str) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 396)
- `_servable_now(vault: Any, repository: Any, commitment_id: str, *, clock: Clock | None) -> Any` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 405) — The check as begin would serve it, or the refusal: not due, nothing servable, or Today showing it.
- `_require_open(admin: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 467)
- `_require_unreserved(admin: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 472)
- `_opened_for(admin: Mapping[str, Any], repository: Any) -> Opened` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 477) — The administration as begin froze it: its candidates are the ones begin resolved, never rebuilt later.
- `_text_of(repository: Any, ref: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 555) — What an opened (measured) veil shows, as the texts measured against the answer keys.
- `_unmeasured(ref: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 588) — The notes an opened veil showed (their ids only; C2: a note is never evidence).
- `_exposure_result(vault: Any, repository: Any, admin: Mapping[str, Any], event: Mapping[str, Any] | None, *, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 599)
- `_replayed_exposure(vault: Any, repository: Any, admin: Mapping[str, Any], exposure_id: str, kind: str, ref: Mapping[str, Any], *, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 686) — A retried opening returns the first result; the same id for another opening is refused (it would be recorded as nothing).
- `_charged_keys(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 697) — Every item an opening is charged to, with the key it is measured against: the candidates begin froze (their keys as they were then), and any candidate the check has gained since (an item made for its LO after begin, with its key now), so an opening that states a newer item's ans…
- `_close_veils(connection: Any, token: str, now: str) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 854)
- `_attempted_elsewhere(repository: Any, admin: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 898) — An attempt on one of the check's candidates since the administration opened, made on another surface (an assisted Today answer moves the check's date; any answer there changes what this card would decide).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]] — imports `module`; statically calls `InlineCheckError`, `abandon`, `attempt_submission_key`, `begin`, `cold_now`, `eligibility_of`, `expose`, `find`, `finish_submit`, `notes_opened`, `preflight`, `prepare_submit`, `protect_more`, `release`, `reopen`, `veils`, `with_measured`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `inline_checks_on`; calls `inline_checks_on`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `reveal_episode_id`; calls `reveal_episode_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`
- [[Reference/Modules/learnloop/db/stores/check_administrations|learnloop.db.stores.check_administrations]] — imports `module`; calls `by_request`, `by_token`, `close`, `insert_administration`, `insert_veil_set`, `open_administration`, `open_commitments`, `release_submission`, `set_exposure`, `set_submission`, `veil_sets`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `settle_answered_checks`; calls `settle_answered_checks`
- [[Reference/Modules/learnloop/intent/inline_checks|learnloop.intent.inline_checks]] — imports `_Sections`, `_primary_passage`; calls `_Sections`, `_primary_passage`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `load_snapshots`; calls `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`, `module`; calls `check_once_at_attempt`, `decide`, `gather`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_answer_overlap`; calls `span_answer_overlap`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd7a_inline_checks.py](../../../../../../tests/test_reader_rd7a_inline_checks.py) — direct import
  - `test_a_crash_after_the_attempt_and_before_the_close_is_recovered_with_that_attempt`
  - `test_begin_serves_todays_item_with_its_frozen_contract_and_records_the_veils_before_the_prompt`
  - `test_below_the_tag_every_check_rpc_refuses_and_today_ignores_the_lock`
  - `test_one_administration_at_a_time_and_today_honours_it`
  - `test_opening_a_notes_veil_reads_no_note_and_says_so_in_the_receipt`
  - `test_opening_a_veil_that_states_the_answer_primes_the_item_and_the_answer_is_practice`
  - `test_rd7_11_while_a_submission_is_reserved_not_now_and_openings_are_refused`
  - `test_rd7_12_the_outcome_is_saved_with_the_close_and_every_retry_returns_it`
  - `test_rd7_15_a_card_moved_by_an_answer_elsewhere_is_superseded_on_recovery`
  - `test_rd7_3_leaving_for_an_unveiled_surface_is_an_unmeasured_opening`
  - `test_rd7_4_every_candidate_of_an_lo_check_is_charged_from_the_set_begin_froze`
  - `test_rd7_5_an_opening_and_its_reveals_commit_together_and_a_retry_charges_nothing_again`
  - `test_rd7_61_a_passage_the_section_map_does_not_place_is_held`
  - `test_rd7_62_another_request_adopting_the_open_check_records_the_gap_and_the_same_request_does_not`
  - `test_rd7_64_an_opening_that_states_a_short_key_exactly_is_a_reveal`
  - `test_rd7_65_an_opening_is_charged_to_a_candidate_made_after_begin`
  - `test_rd7_66_a_revision_never_sent_is_refused_and_nothing_is_veiled_after_a_reservation`
  - `test_rd7_68_an_answer_the_attempt_service_refuses_reserves_nothing`
  - `test_rd7_71_a_row_with_no_frozen_presentation_is_superseded_on_recovery`
  - `test_rd7_73_the_restored_card_says_what_was_opened_and_a_crashed_answer_returns_its_outcome`
  - `test_rd7_74_a_check_not_due_yet_is_refused_before_a_session_starts`
  - `test_rd7_7_an_opening_nothing_can_measure_is_charged_and_says_so_before`
  - `test_rd7_8_the_host_passage_is_protected_and_missing_coverage_fails_closed_for_its_source`
  - `test_rd7_9_recovery_shows_the_frozen_card_without_serving_again_and_names_the_reserved_submission`
  - `test_submit_records_one_attempt_on_the_reader_surface_settles_and_is_idempotent`
  - `test_the_protection_set_veils_covered_passages_and_every_note_bearing_surface`
- [tests/test_reader_rd7b_cold_followup_parity.py](../../../../../../tests/test_reader_rd7b_cold_followup_parity.py) — direct import
  - `test_rw6bs_gate_holds_the_follow_up_on_both_surfaces`

## Modification guidance

- Make changes here when the responsibility remains inline administration within learnloop.intent; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
