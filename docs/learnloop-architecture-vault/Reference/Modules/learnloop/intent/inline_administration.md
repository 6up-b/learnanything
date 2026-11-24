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
| Source lines | 602 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InlineCheckError(Exception)` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 60)
  - `__init__(self, code: str, message: str, details: Mapping[str, Any] | None=None) -> None` (line 61; internal)
- `class Opened` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 69) — A check's commitment and what begin found about it.
- `protection(vault: Any, repository: Any, opened: Opened, visible: Mapping[str, Any], covered: Covered) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 101) — What is veiled of ``visible`` while this check is open, and how it was decided.
- `narrow(veiled: list[dict[str, Any]], judgment: Any | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 176) — The Decider's seam (spec §12.6.3): once the reveal adjudication judgment exists it may un-veil what it judges states nothing of the answer.
- `being_answered(repository: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 215) — The commitments an open inline administration holds (the lock Today honours).
- `union(veil_sets: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 222) — Everything veiled by an administration's veil sets (deduplicated, in order) and what was opened by the last.
- `find(repository: Any, token: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 235)
- `preflight(vault: Any, repository: Any, *, request_id: str, commitment_id: str) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 243) — The refusals ``begin`` gives before it reads the serving view (the tag, another open check, a duty no longer pending), for a caller that would otherwise do work first (start a practice session for a check that cannot open).
- `begin(vault: Any, repository: Any, *, request_id: str, commitment_id: str, session_id: str, visible: Mapping[str, Any], serve: Callable[[str], Mapping[str, Any]], covered: Covered, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 262) — Open an inline administration: the item, the frozen contract (``serve``: Today's own session serve of the item, which freezes it), the protection and its first veil set, all before the prompt is returned.
- `veils(repository: Any, token: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 314)
- `protect_more(vault: Any, repository: Any, *, token: str, visible: Mapping[str, Any], covered: Covered, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 343) — Veil what came into view (navigation, a new window, a search): a veil set of the additions only.
- `expose(vault: Any, repository: Any, *, token: str, ref: Mapping[str, Any], kind: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 414) — Record what the learner did that is exposure, at once.
- `cold_now(vault: Any, repository: Any, admin: Mapping[str, Any], *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 460) — Whether the check's item could still be answered cold now (the Check once decision over the reveal ledger).
- `prepare_submit(vault: Any, repository: Any, *, token: str, submission_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 470) — Before the attempt: name the submission on the administration (a crash after the attempt is found by it).
- `notes_opened(admin: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 489) — Whether the learner opened a note's veil during this administration (an exposure event with unmeasured notes).
- `attempt_submission_key(submission_id: str) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 498) — The attempt service's own idempotency key for an inline submission.
- `finish_submit(vault: Any, repository: Any, *, token: str, attempt_id: str, pending_before: bool, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 504) — After the attempt: close the administration with it, then settle as for any qualifying attempt (the check is answered only if this attempt is its first on-your-own, cold one).
- `outcome(vault: Any, repository: Any, *, token: str, pending_before: bool | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 520) — Whether the administration's attempt answered its check, and why not when it did not.
- `abandon(vault: Any, repository: Any, *, token: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 552) — "Not now": closed with no attempt; the duty stays pending and what was opened stays in the reveal ledger.
- `reopen(vault: Any, repository: Any, *, attempt_for: Callable[[str, str], str | None], clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 567) — The restart read: the open administration, or None.

### Module constants

- `SURFACE` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 42)
- `METHOD` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 45)
- `PRIMED_BY_NOTE` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 47)
- `METHOD_WHOLE_SOURCES` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 49)
- `PLACED_KINDS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 52)
- `OPENED_BASIS` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 54)
- `DUE_ONLY` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 56)
- `BELOW_TAG` ([src/learnloop/intent/inline_administration.py](../../../../../../src/learnloop/intent/inline_administration.py), line 57)

### Explicit exports

`__all__` declares:

- `BELOW_TAG`
- `InlineCheckError`
- `METHOD`
- `METHOD_WHOLE_SOURCES`
- `OPENED_BASIS`
- `Opened`
- `PLACED_KINDS`
- `Covered`
- `SURFACE`
- `abandon`
- `attempt_submission_key`
- `begin`
- `being_answered`
- `cold_now`
- `expose`
- `find`
- `finish_submit`
- `narrow`
- `outcome`
- `prepare_submit`
- `protect_more`
- `protection`
- `reopen`
- `union`
- `veils`

## Internal implementation anchors

- `_now(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 80)
- `_require_tag(vault: Any) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 84)
- `_ref_key(ref: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 91)
- `_window_group(kind: str) -> str` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 166)
- `_check(vault: Any, repository: Any, commitment_id: str, *, clock: Clock | None) -> Any` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 186)
- `_learning_objects(vault: Any, repository: Any, commitment_id: str, candidates: Iterable[str]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 193)
- `_open_in_today(repository: Any, candidates: Iterable[str]) -> bool` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 204) — A Today session shows one of the check's items with an answer being written: the check is being answered there.
- `_require_open(admin: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 322)
- `_opened_for(admin: Mapping[str, Any], repository: Any) -> Opened` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 327)
- `_text_of(repository: Any, ref: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 370) — What an opened veil shows, as the texts measured against the answer keys.
- `_unmeasured(ref: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 403) — The notes an opened veil showed and nothing measured (their ids only; C2: a note is never evidence).
- `_close_veils(connection: Any, token: str, now: str) -> None` ([source](../../../../../../src/learnloop/intent/inline_administration.py), line 545)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]] — imports `module`; statically calls `abandon`, `attempt_submission_key`, `begin`, `expose`, `finish_submit`, `notes_opened`, `outcome`, `preflight`, `prepare_submit`, `protect_more`, `reopen`, `veils`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `inline_checks_on`; calls `inline_checks_on`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal`; calls `record_reveal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`
- [[Reference/Modules/learnloop/db/stores/check_administrations|learnloop.db.stores.check_administrations]] — imports `module`; calls `by_request`, `by_token`, `close`, `insert_administration`, `insert_veil_set`, `open_administration`, `open_commitments`, `set_exposure`, `set_submission`, `veil_sets`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `settle_answered_checks`; calls `settle_answered_checks`
- [[Reference/Modules/learnloop/intent/inline_checks|learnloop.intent.inline_checks]] — imports `_Sections`; calls `_Sections`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `load_snapshots`; calls `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_answer_overlap`; calls `span_answer_overlap`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
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
  - `test_opening_a_veil_that_states_the_answer_primes_the_item_and_the_answer_is_practice`
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
