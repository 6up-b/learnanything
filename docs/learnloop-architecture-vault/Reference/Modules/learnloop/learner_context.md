---
title: "learnloop.learner_context"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner_context.py"
source_paths:
  - "src/learnloop/learner_context.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner_context module"
  - "src/learnloop/learner_context.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.learner_context`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner_context` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The learner's latent state as one read model (spec_mcp_frontend_c1 §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py) |
| Source lines | 1732 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ContextLimits` ([source](../../../../../src/learnloop/learner_context.py), line 165)
- `excerpt(text: Any, limit: int) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 175)
- `class KeyBook` ([source](../../../../../src/learnloop/learner_context.py), line 211) — Every answer key each item is known to have had: today's YAML, every assessment-contract snapshot (an attempt's pinned contract is the key it was graded against) and every practice-item snapshot the scheduler kept.
  - `item(self, item_id: str | None) -> list[Any]` (line 226; public)
  - `lo(self, lo_id: str | None) -> list[Any]` (line 229; public)
  - `los(self, lo_ids: Iterable[str]) -> list[Any]` (line 232; public)
- `key_book(connection: Any, vault: Any, unknowns: list[str]) -> KeyBook` ([source](../../../../../src/learnloop/learner_context.py), line 236) — The :class:`KeyBook` of the vault's items and contract snapshots.
- `leaks_key(text: str, expected_answers: Iterable[Any]) -> bool` ([source](../../../../../src/learnloop/learner_context.py), line 284) — Whether ``text`` reproduces any of ``expected_answers`` (the tutor's filter).
- `class GuardedText(str)` ([source](../../../../../src/learnloop/learner_context.py), line 306) — Text :class:`TextGuard` released, and only it: the constructor takes a module-private token.
  - `__new__(cls, value: str, token: object) -> GuardedText` (line 314; internal)
  - `__reduce__(self) -> tuple[Any, ...]` (line 319; internal)
- `class AuthoredText(GuardedText)` ([source](../../../../../src/learnloop/learner_context.py), line 323) — (a) Authored vault text: a topic's name or id the learner or an authored vault file wrote, or the question as graded.
- `class AnswerText(GuardedText)` ([source](../../../../../src/learnloop/learner_context.py), line 330) — (b) The learner's own answer on a pinned attempt.
- `class RecordedText(GuardedText)` ([source](../../../../../src/learnloop/learner_context.py), line 336) — (c) A derived text whose recorded write-time provenance names only safe inputs.
- `class WriteProvenance` ([source](../../../../../src/learnloop/learner_context.py), line 343) — What one derived text was written from, recorded when it was written.
  - `readable(self) -> bool` (line 381; public) — Complete, every input an id, and at least one input.
- `no_write_provenance(_connection: Any, _kind: str, _record_id: str) -> None` ([source](../../../../../src/learnloop/learner_context.py), line 412) — No record for any text: the narrow rule (the kill switch's state).
- `recorded_write_provenance(connection: Any, kind: str, record_id: str) -> WriteProvenance | None` ([source](../../../../../src/learnloop/learner_context.py), line 418) — THE source: the records writers keep (``db.stores.write_provenance``), every row for the text joined (each writer of a text recorded what it read).
- `default_provenance(vault: Any) -> ProvenanceSource` ([source](../../../../../src/learnloop/learner_context.py), line 446) — The vault's source: the recorded one only when the kill switch ``diagnosis.chat_shows_recorded_text`` is on; off (the default since the landing), or unreadable, none (the narrow rule).
- `lo_alias(lo_id: str, key: bytes | None=None) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 476) — The opaque id that stands for a generated topic while its name is withheld: a keyed digest (HMAC-SHA256 with the vault's alias key), stable for one key, accepted back as a named id (:func:`resolve_scope`; the raw id is not).
- `group_alias(group_key: str, key: bytes | None=None) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 486) — A recurrence group's key as shown: a keyed digest of the stored key (itself a digest of the root's statement, which a client that guessed the statement could recompute: Q13).
- `class TextGuard` ([source](../../../../../src/learnloop/learner_context.py), line 511) — THE renderer of every text the chat frontend shows (spec §4.7 rule 1).
  - `__init__(self, connection: Any, vault: Any, repository: Any=None, *, withheld: Withheld | None=None, book: KeyBook | None=None, unknowns: list[str] | None=None, alias_key: bytes | None=None, provenance: ProvenanceSource | None=None) -> None` (line 548; internal)
  - `withheld(self) -> Withheld` (line 562; public)
  - `book(self) -> KeyBook` (line 566; public)
  - `attempt_reason(self, attempt_id: Any) -> str | None` (line 573; public) — Why this answer, and everything about it, is protected (the shared attempt protection, ``PastWork.attempt_reason``), or None.
  - `_answer_reason(self, attempt_id: Any, text: Any) -> str | None` (line 579; internal) — (b)'s checks, the one predicate: why this answer, with this text, may not leave LearnLoop, or None.
  - `answer(self, attempt_id: Any, text: Any, limit: int) -> tuple[AnswerText | None, str | None]` (line 597; public) — (b) THE renderer of the learner's own answer: ``(text, None)`` released, ``(None, why)``, or ``(None, None)`` for no text.
  - `answer_of(self, attempt_id: Any, limit: int) -> tuple[AnswerText | None, str | None]` (line 608; public) — The answer as the attempt records it (a gap drawn from an answer shows the answer itself, not the excerpt its reader chose).
  - `_authored(self, text: Any, limit: int) -> AuthoredText | None` (line 619; internal)
  - `stem(self, attempt_id: Any, lo_id: Any) -> tuple[GuardedText | None, str | None]` (line 624; public) — The question as graded: the pinned contract's statement, then the instruction of the required method it froze, kept whole within the stem limit (``PinnedContract.question``, the card's rendering too).
  - `question(self, attempt_id: str, lo_id: Any) -> tuple[GuardedText | None, str | None]` (line 647; public) — The chat's text rule for a question: :meth:`stem`.
  - `statement(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any]=(), items: Iterable[Any]=(), los: Iterable[Any]=(), source_text: Any=None) -> tuple[RecordedText | None, str | None]` (line 652; public) — The chat's text rule for a statement: :meth:`derived` ((c) only).
  - `derived(self, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any]=(), items: Iterable[Any]=(), los: Iterable[Any]=(), source_text: Any=None) -> tuple[RecordedText | None, str | None]` (line 662; public) — (c) THE renderer of a derived text: released only by a complete write-time record that covers the text as stored (``source_text``, else ``text``: its hash is the one the latest record keeps) and whose inputs, with the entry's own ``answers``, ``items`` and ``los``, are all safe.
  - `_protected(self, answers: Sequence[str], items: Sequence[str]) -> str | None` (line 712; internal) — Why any of these answers or items is protected (or protection is unreadable), or None: the shared leakage rule (``PastWork.evidence_reason``).
  - `_unsafe(self, record: WriteProvenance, answers: Sequence[str], items: Sequence[str]) -> str | None` (line 719; internal) — Why a record's inputs (with the entry's own) are not all safe, or None.
  - `_lo(self, lo_id: str) -> Any` (line 762; internal)
  - `_generated_ids(self) -> frozenset[str]` (line 765; internal) — Every topic the learner-text pipeline created: by its provenance (``vault.lifecycle.created_from_learner_text``), its id's form, or a gap that records creating it.
  - `generated(self, lo_id: Any) -> bool` (line 786; public)
  - `_name(self, lo_id: str) -> tuple[GuardedText | None, str | None]` (line 790; internal) — A topic's name released, or why not.
  - `_title(self, lo_id: str) -> str` (line 811; internal)
  - `topic(self, lo_id: Any) -> str | None` (line 815; public) — THE renderer of a topic's name: released, or :data:`TOPIC_WITHHELD` and why.
  - `lo_ref(self, lo_id: Any) -> str | None` (line 824; public) — THE renderer of a topic's id: released, or an opaque keyed alias (:func:`lo_alias`) while a generated topic's name is withheld.
  - `aliases(self) -> dict[str, str]` (line 837; public) — ``{alias: topic id}`` for every generated topic (a named id the frontend may send back).
  - `searchable(self, lo_id: Any) -> bool` (line 843; public) — Whether a request may name this topic by its words (a topic search) or by its raw id: not while a generated name is withheld.
  - `group_ref(self, group_key: Any) -> str` (line 852; public) — A recurrence group's key as shown (:func:`group_alias`).
- `resolve_scope(vault: Any, *, learning_object_ids: Sequence[str] | None=None, topic: str | None=None, aliases: Mapping[str, str] | None=None, searchable: Callable[[str], bool] | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop/learner_context.py), line 986) — The LOs a context is about: named ids, a topic's matches, or every active LO.
- `retention_risks(vault: Any, repository: Any, los: Iterable[str], *, now: datetime, limit: int=15, unknowns: list[str] | None=None, topic: Callable[[str], Any] | None=None, ref: Callable[[str], Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1537) — Topics whose modelled recall now is below :data:`RETENTION_TARGET`, or due now.
- `learning_context(vault: Any, repository: Any, *, learning_object_ids: Sequence[str] | None=None, topic: str | None=None, now: datetime | None=None, limits: ContextLimits | None=None, withheld: Withheld | None=None, alias_key: bytes | None=None, provenance: ProvenanceSource | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop/learner_context.py), line 1602) — The shared latent-state read model for one scope.

### Module constants

- `_LOG` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 139)
- `CONTEXT_VERSION` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 141)
- `EXCERPT_LIMIT` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 143)
- `STEM_LIMIT` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 144)
- `STATEMENT_LIMIT` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 145)
- `RETENTION_TARGET` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 147)
- `HELD_BACK` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 151)
- `KEY_WITHHELD` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 153)
- `KEYS_UNREADABLE` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 154)
- `REVISION_UNKNOWN` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 155)
- `REVISION_UNKNOWN_BEHIND` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 156)
- `REVISION_CHANGED_BEHIND` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 158)
- `KEY_WITHHELD_BEHIND` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 159)
- `_BEHIND` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 161)
- `_RELEASE` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 303)
- `DERIVED_KINDS` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 400)
- `LO_ALIAS_PREFIX` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 460)
- `GROUP_ALIAS_PREFIX` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 462)
- `TOPIC_WITHHELD` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 464)
- `_ALIAS_HEX` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 465)
- `_PROCESS_ALIAS_KEY` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 468)
- `_ANSWER_SOURCES` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 502)
- `_CHUNK` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 503)
- `_GENERATED_LO_PREFIX` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 506)
- `TITLE_LIMIT` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 507)
- `_ID_LIMIT` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 508)
- `RELEASE_TYPES` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 867)
- `TOPIC_FIELDS` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 872)
- `TOPIC_ID_FIELDS` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 885)
- `DERIVED_FIELDS` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 897)
- `RELEASED_BY` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 908)
- `STRUCTURAL_FIELDS` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 919)
- `_WORD` ([src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py), line 972)

### Explicit exports

`__all__` declares:

- `ANSWER_UNRECORDED`
- `PINS_UNREADABLE`
- `STEM_UNRECORDED`
- `WITHHELD_COLD`
- `WITHHELD_EXAM`
- `WITHHELD_PROBE`
- `WITHHELD_RESERVED`
- `ANSWER`
- `AUTHORED`
- `CONTEXT_VERSION`
- `DERIVED_FIELDS`
- `DERIVED_KINDS`
- `GROUP_ALIAS_PREFIX`
- `HELD_BACK`
- `KEY_WITHHELD`
- `KEY_WITHHELD_BEHIND`
- `LO_ALIAS_PREFIX`
- `PROTECTION_UNKNOWN`
- `QUESTION_UNRECORDED`
- `RECORDED`
- `RELEASED_BY`
- `REVISION_CHANGED_BEHIND`
- `RELEASE_TYPES`
- `RETENTION_TARGET`
- `SNAPSHOT_UNSETTLED`
- `STRUCTURAL_FIELDS`
- `TOPIC_FIELDS`
- `TOPIC_ID_FIELDS`
- `TOPIC_WITHHELD`
- `WITHHELD_SOLUTION_OPEN`
- `WITHHELD_UNKNOWN_ITEM`
- `WITHHELD_UNREADABLE`
- `AnswerText`
- `AuthoredText`
- `ContextLimits`
- `GuardedText`
- `KeyBook`
- `ProvenanceSource`
- `RecordedText`
- `TextGuard`
- `Withheld`
- `WriteProvenance`
- `excerpt`
- `group_alias`
- `key_book`
- `leaks_key`
- `default_provenance`
- `learning_context`
- `lo_alias`
- `no_write_provenance`
- `recorded_write_provenance`
- `protection_issues`
- `resolve_scope`
- `retention_risks`
- `withheld_items`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../src/learnloop/learner_context.py), line 180)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 186)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../src/learnloop/learner_context.py), line 190)
- `_ids(values: Iterable[Any]) -> frozenset[str]` ([source](../../../../../src/learnloop/learner_context.py), line 199)
- `_key_identity(value: Any) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 206)
- `_keyed(key: bytes | None, kind: str, value: str) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 471)
- `_lowered(note: str) -> str` ([source](../../../../../src/learnloop/learner_context.py), line 494)
- `_forms(word: str) -> tuple[str, ...]` ([source](../../../../../src/learnloop/learner_context.py), line 975) — A topic word and its singular (``eigenvalues`` matches ``eigenvalue``).
- `_statement(guard: TextGuard, kind: str, record_id: Any, text: Any, limit: int, *, answers: Iterable[Any]=(), items: Iterable[Any]=(), los: Iterable[Any]=(), source_text: Any=None) -> tuple[GuardedText | None, str | None]` ([source](../../../../../src/learnloop/learner_context.py), line 1035) — A statement through the shared leakage rule (``learner_protection.statement_text``: protected answers or items withhold it, naming why), then this module's text rule (:meth:`TextGuard.statement`).
- `_misconceptions(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard, unknowns: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../src/learnloop/learner_context.py), line 1056)
- `_hypotheses(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard, unknowns: list[str]) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1119) — Open hypotheses: the diagnosed causes, then the unresolved causes (each read on its own, so an LO with unresolved causes and no named hypothesis still shows them).
- `_share_limit(diagnosed: list[dict[str, Any]], unresolved: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1131) — Both kinds under the one ``limit``.
- `_diagnosed_causes(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard, unknowns: list[str]) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1148)
- `_unresolved_causes(connection: Any, los: set[str], guard: TextGuard, unknowns: list[str]) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1235) — Answers whose cause is not settled, per LO (a count; no answer text).
- `_recurrence_groups(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard, unknowns: list[str]) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1265) — Groups touching the scope's LOs.
- `_traces(connection: Any, repository: Any, los: set[str], limits: ContextLimits, guard: TextGuard, now_iso: str, config: Any=None) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1321)
- `_diagnosis(repository: Any, guard: TextGuard, attempt_id: str, lo_id: Any, item_id: Any, *, hidden: bool, hypotheses: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../src/learnloop/learner_context.py), line 1408)
- `_gaps(connection: Any, los: set[str], limits: ContextLimits, guard: TextGuard, unknowns: list[str]) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop/learner_context.py), line 1442)
- `_gap_words(guard: TextGuard, row: Mapping[str, Any]) -> tuple[GuardedText | None, str | None]` ([source](../../../../../src/learnloop/learner_context.py), line 1487) — A gap's words: the pinned answer they are (a diagnosis's or a stuck answer's gap: (b), shown as the attempt records it), else a question the learner asked ((c): the gap's record names the question and the item contract it was asked about, Q10, and the question's item must pass t…
- `_belief(connection: Any, kind: str, record_id: Any) -> tuple[str, Any, Any] | None` ([source](../../../../../src/learnloop/learner_context.py), line 1502) — ``(record kind, statement, topic)`` of the belief a gap was matched to: a recorded misconception (``durable``), or a candidate in the holding pen or the hypothesis it projects (``candidate``).
- `_gap_target(connection: Any, guard: TextGuard, kind: Any, target_id: Any) -> tuple[GuardedText | None, str | None, str | None]` ([source](../../../../../src/learnloop/learner_context.py), line 1518) — What a gap was matched to: ``(statement, note, topic)``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `SNAPSHOT_UNSETTLED`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `TextGuard`, `resolve_scope`, `withheld_items`; statically calls `TextGuard`, `resolve_scope`, `withheld_items`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `HELD_BACK`, `TextGuard`, `protection_issues`, `retention_risks`; statically calls `TextGuard`, `protection_issues`, `retention_risks`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `key_book`, `leaks_key`; statically calls `key_book`, `leaks_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `open_learner_state_hypotheses`; calls `open_learner_state_hypotheses`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `stored_record`, `text_sha256`; calls `stored_record`, `text_sha256`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `plain_summary`; calls `plain_summary`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DONE`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `ANSWER_UNRECORDED`, `PINS_UNREADABLE`, `PROTECTION_UNKNOWN`, `PastWork`, `QUESTION_UNRECORDED`, `SNAPSHOT_UNSETTLED`, `STEM_UNRECORDED`, `WITHHELD_COLD`, `WITHHELD_EXAM`, `WITHHELD_PROBE`, `WITHHELD_RESERVED`, `WITHHELD_SOLUTION_OPEN`, `WITHHELD_UNKNOWN_ITEM`, `WITHHELD_UNREADABLE`, `Withheld`, `attempt_result`, `hypothesis_answers`, `past_work_text`, `protection_issues`, `statement_text`, `withheld_items`; calls `PastWork`, `attempt_result`, `hypothesis_answers`, `past_work_text`, `statement_text`, `withheld_items`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`; calls `attempt_time_sql`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `created_from_learner_text`; calls `created_from_learner_text`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `hmac`, `json`, `logging`, `re`, `secrets`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]], [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]], [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]], [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_input_provenance.py](../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_a_generated_topic_named_in_a_misconception_carries_what_it_was_drafted_from`
  - `test_a_joint_grading_s_inputs_reach_what_is_written_from_it`
  - `test_a_question_that_records_its_contract_is_shown_when_safe`
  - `test_a_recorded_diagnosis_is_released_once_its_question_cannot_be_answered_cold`
  - `test_a_snapshot_diagnosis_records_the_export_entries_it_opened`
  - `test_a_text_rewritten_by_a_writer_that_recorded_nothing_is_held_back`
  - `test_f2_a_diagnosis_folds_a_generated_topic_only_under_the_name_it_was_shown`
  - `test_f3_a_regrade_while_the_diagnoser_runs_never_certifies_what_it_was_shown`
  - `test_f5_the_switch_off_is_the_narrow_rule_exactly`
  - `test_old_rows_stay_held_back_and_a_re_diagnosis_writes_recorded_ones`
  - `test_rereview_f2_a_name_is_checked_although_a_text_read_already_folded_its_topic`
  - `test_rereview_f3_a_regrade_after_the_job_captured_its_gradings_is_unaccountable`
  - `test_the_kill_switch_puts_back_the_narrow_rule`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_a_method_explicit_question_records_the_contract_it_was_presented_with`
  - `test_off_a_fully_recorded_safe_text_is_withheld_in_chat_and_the_writers_still_record`
  - `test_off_f2_a_belief_from_a_renamed_generated_topic_is_withheld`
  - `test_off_f3_a_summary_over_a_regraded_c4_history_attempt_is_withheld`
  - `test_off_the_live_pipeline_records_and_chat_withholds_until_the_switch_is_on`
  - `test_rule_4_and_identity_bound_marks_reach_rule_c_through_learner_protection`
  - `test_the_release_switch_defaults_off_and_the_default_source_is_the_narrow_rule`
- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — direct import
- [tests/test_mcp_c1a_landing.py](../../../../../tests/test_mcp_c1a_landing.py) — direct import
  - `test_no_reader_keeps_a_protection_of_its_own`
  - `test_the_text_rule_is_each_readers_own`
- [tests/test_mcp_c1a_narrow.py](../../../../../tests/test_mcp_c1a_narrow.py) — direct import
  - `test_a_recorded_complete_provenance_with_safe_inputs_releases_a_derived_text`
  - `test_a_recorded_input_answer_that_states_its_key_releases_nothing`
  - `test_a_recorded_provenance_releases_a_generated_topic_s_name`
  - `test_a_recorded_provenance_releases_nothing_unless_complete_and_safe`
  - `test_aliases_are_keyed_per_vault`
  - `test_each_kind_of_released_text_has_exactly_one_renderer`
  - `test_every_text_field_is_authored_an_answer_or_withheld_without_a_record`
- [tests/test_mcp_c1a_review.py](../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_a_diagnosis_receipt_with_an_unreadable_member_releases_nothing`
  - `test_a_diagnosis_s_cause_and_every_belief_drawn_from_it_are_held_back`
  - `test_a_diagnosis_shown_a_belief_on_a_generated_topic_is_held_back`
  - `test_a_diagnosis_shown_an_answer_whose_grading_saw_the_unpinned_one_is_held_back`
  - `test_a_joint_grader_s_cause_is_held_back_with_or_without_its_receipt`
  - `test_a_prerequisite_drafted_from_an_unpinned_answer_shows_neither_its_title_nor_its_id`
  - `test_a_provenance_cycle_releases_nothing`
  - `test_a_provenance_list_with_an_unreadable_member_releases_nothing`
  - `test_a_record_naming_what_a_diagnosis_read_releases_it_only_when_every_answer_is_pinned`
  - `test_a_recurrence_group_rooted_in_a_protected_hypothesis_keeps_no_statement`
  - `test_an_unpinned_answer_shows_no_text_even_when_no_key_change_is_recorded`
  - `test_an_unreadable_practice_item_withholds_its_own_answers_only`
  - `test_answers_and_diagnoses_are_filtered_against_the_key_they_were_graded_by`
  - `test_open_hypotheses_share_one_limit_and_keep_unresolved_only_causes`
  - `test_text_a_model_wrote_on_a_generated_topic_is_held_back`
  - `test_text_drawn_from_an_unpinned_answer_is_withheld_in_every_section`
  - `test_text_whose_provenance_cannot_be_followed_is_withheld`
- [tests/test_mcp_runtime.py](../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_attach_and_every_view_write_nothing`
- [tests/test_mcp_tools.py](../../../../../tests/test_mcp_tools.py) — direct import
  - `test_learning_context_is_the_apps_latent_state`
- [tests/test_notes_c2b_review5.py](../../../../../tests/test_notes_c2b_review5.py) — direct import
- [tests/test_ro1_availability_reads.py](../../../../../tests/test_ro1_availability_reads.py) — direct import
  - `test_the_learner_contexts_traces_exclude_an_exam_not_yet_imported`

## Modification guidance

- Make changes here when the responsibility remains learner context within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/learner_context.py](../../../../../src/learnloop/learner_context.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
