---
title: "learnloop.db.stores.judgment_claims"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/judgment_claims.py"
source_paths:
  - "src/learnloop/db/stores/judgment_claims.py"
source_commit: "257fc889975d6903ededf88016ad914f087559a7"
source_commit_timestamp: "2026-10-18T03:23:33-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.judgment_claims module"
  - "src/learnloop/db/stores/judgment_claims.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.judgment_claims`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.judgment_claims` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Work claims of the shared "same or different?" judge (Slice 2 T1, migration 176).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/judgment_claims.py](../../../../../../../src/learnloop/db/stores/judgment_claims.py) |
| Source lines | 200 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `257fc889975d6903ededf88016ad914f087559a7` |
| Commit timestamp | `2026-10-18T03:23:33-04:00` |

## Public API

- `claim_work(connection: sqlite3.Connection, *, claim_key: str, task: str, producer: str, prompt_version: str | None, input_hash: str, owner: str, now: str, lease_seconds: int, rerun: bool=False) -> tuple[str, int | None]` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 37) — Claim one question; returns (``claimed``, epoch), (``held``, None) or (``done``, None).
- `holds_claim(connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, now: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 84) — True while this worker's lease (owner and epoch) is the claim's current one; with ``now``, also only while that lease has not expired (a lapsed lease is no one's until it is re-claimed, so its holder's late commit is fenced out; hints H1 fix round 2, M3).
- `complete_claim(connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, judgment_id: str, now: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 103) — Mark the question answered; False (and no change) when fenced out.
- `lease_holder(connection: sqlite3.Connection, *, claim_key: str) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 117) — The owner of the claim's live or lapsed lease (None unless it is leased).
- `take_over_claim(connection: sqlite3.Connection, *, claim_key: str, from_owner: str, owner: str, now: str, lease_seconds: int) -> int | None` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 126) — Take a lease from ``from_owner`` before it expires, when the caller knows that owner has ended (its job finished without completing or releasing the claim).
- `renew_claim(connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, now: str, lease_seconds: int) -> bool` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 153) — Extend a live lease (a heartbeat); False (and no change) when it is no longer this worker's or has already expired: a lapsed lease is never revived, because another worker may have judged it free (hints H1 fix round 2, M3).
- `live_lease(connection: sqlite3.Connection, *, claim_key: str, now: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 174) — True when someone holds an unexpired lease on the claim (read-only).
- `release_claim(connection: sqlite3.Connection, *, claim_key: str, owner: str, epoch: int, now: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 186) — Give an unanswered claim back (a failed or refused call) so another run may take it.

### Explicit exports

`__all__` declares:

- `CLAIMED`
- `DONE`
- `HELD`
- `claim_work`
- `complete_claim`
- `holds_claim`
- `lease_holder`
- `live_lease`
- `release_claim`
- `renew_claim`
- `take_over_claim`

## Internal implementation anchors

- `_row(connection: sqlite3.Connection, claim_key: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/judgment_claims.py), line 25)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `CLAIMED`, `DONE`, `HELD`, `claim_work`, `complete_claim`, `holds_claim`, `live_lease`, `release_claim`, `renew_claim`; statically calls `claim_work`, `complete_claim`, `holds_claim`, `live_lease`, `release_claim`, `renew_claim`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `CLAIMED`, `claim_work`, `holds_claim`, `release_claim`, `renew_claim`; statically calls `claim_work`, `holds_claim`, `release_claim`, `renew_claim`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `CLAIMED`, `HELD`, `claim_work`, `complete_claim`, `holds_claim`, `release_claim`; statically calls `claim_work`, `complete_claim`, `holds_claim`, `release_claim`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `claim_work`, `complete_claim`, `release_claim`; statically calls `claim_work`, `complete_claim`, `release_claim`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `CLAIMED`, `DONE`, `HELD`, `claim_work`, `complete_claim`, `holds_claim`, `lease_holder`, `release_claim`, `take_over_claim`; statically calls `claim_work`, `complete_claim`, `holds_claim`, `lease_holder`, `release_claim`, `take_over_claim`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `claim_work`, `complete_claim`, `release_claim`; statically calls `claim_work`, `complete_claim`, `release_claim`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `CLAIMED`, `claim_work`, `complete_claim`, `holds_claim`, `release_claim`, `renew_claim`; statically calls `claim_work`, `complete_claim`, `holds_claim`, `release_claim`, `renew_claim`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]], [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]], [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]], [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_review_fixes.py](../../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_claim_held_by_another_process_is_skipped`
- [tests/test_approach_maps.py](../../../../../../../tests/test_approach_maps.py) — direct import
  - `test_f3_a_lapsed_claim_of_a_dead_process_is_taken_over_and_fences_its_commit`
  - `test_m3_a_takeover_while_awaiting_a_response_pays_writes_and_stores_nothing_more`
  - `test_m3_holds_claim_checks_expiry_and_renewal_never_revives_a_lapsed_lease`
- [tests/test_reader_digest_narrative.py](../../../../../../../tests/test_reader_digest_narrative.py) — direct import
- [tests/test_reader_passage_check.py](../../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_check_held_by_a_live_job_waits_for_it_and_returns_its_question`
  - `test_a_check_held_past_the_wait_fails_retryably_and_never_completes_without_a_question`
  - `test_a_claim_left_by_a_crashed_job_is_taken_over_by_the_next_job_at_once`
  - `test_a_crashed_claim_from_another_job_is_taken_over_after_its_lease`
  - `test_a_crashed_claim_is_recovered_by_its_own_job_at_once_and_by_others_after_its_lease`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/judgment_claims.py](../../../../../../../src/learnloop/db/stores/judgment_claims.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
