---
title: "learnloop.content.sources.exam_material"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/exam_material.py"
source_paths:
  - "src/learnloop/content/sources/exam_material.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.content.sources.exam_material module"
  - "src/learnloop/content/sources/exam_material.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.exam_material`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.exam_material` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Exam and held-out material: THE predicate (exam-protection stage, 2026-10-13).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py) |
| Source lines | 1669 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_exam_role(role: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 163) — Whether a role's material is exam material (assessment-only).
- `class ExamVerdict` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 170) — Whether one span (or a whole extraction) is exam material, and why.
  - `as_dict(self) -> dict[str, Any]` (line 185; public)
- `class Material` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 213) — Withheld material: whole extractions and single spans (with their reasons).
  - `covers(self, extraction_id: str, span_id: str | None=None) -> bool` (line 221; public) — Whether the span (or, with no span, the whole extraction) is in this material.
  - `covered(self, keys: Iterable[Sequence[str]]) -> frozenset[SpanKey]` (line 228; public) — The keys among ``keys`` this material covers.
  - `touched(self) -> frozenset[str]` (line 235; public) — Every extraction this material covers wholly or in part.
  - `empty(self) -> bool` (line 241; public)
  - `from_acc(cls, acc: _Acc) -> Material` (line 245; public)
  - `union(self, other: Material) -> Material` (line 251; public)
- `class ExamMaterial` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 262) — Exam material vault-wide (rules 1-3), with the held-out part (rule 3) apart.
  - `extractions(self) -> frozenset[str]` (line 271; public)
  - `spans(self) -> frozenset[SpanKey]` (line 275; public)
  - `covers(self, extraction_id: str, span_id: str | None=None) -> bool` (line 278; public) — Whether the span is exam material (held-out included).
  - `is_held_out(self, extraction_id: str, span_id: str | None=None) -> bool` (line 283; public)
  - `withheld(self, keys: Iterable[Sequence[str]]) -> frozenset[SpanKey]` (line 286; public) — The keys among ``keys`` that are exam material.
  - `verdict(self, extraction_id: str, span_id: str | None=None) -> ExamVerdict` (line 291; public) — The span's verdict, with its revision and the pinned revisions behind it.
- `descendants(units: Sequence[UnitRow], roots: set[str]) -> set[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 311) — ``roots`` and every unit nested below them (a chapter's sections).
- `raw_roots(unit_id: str, units: Mapping[str, UnitRow]) -> set[str] | None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 325) — The raw units an effective unit id covers, or None when one is unknown.
- `scope_reading_of(member: Any, run: tuple[str | None, str | None] | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 436) — Whether a member's ``scope_extraction_id`` names a reading its scope can be on: sealed with its entries by the writer (``scope_seal``; an edit made outside the writer breaks it), an extraction of the member's own book, of the revision the member records for it (``scope_revision_…
- `marks_made_on(extraction_id: str, revision_id: str | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 562) — The value of :data:`MARKS_MADE_ON_KEY` a writer records with the marks it makes on ``extraction_id`` (``revision_id``: that extraction's revision).
- `selection_marks_exact(extraction_id: str, metadata: Mapping[str, Any] | None, run: tuple[str | None, str | None] | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 569) — Whether a selection's marks name the reading they sit on: its :data:`MARKS_MADE_ON_KEY` names this extraction and its run's revision.
- `class SourceSetsUnreadable(RuntimeError)` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 961) — The vault's source sets did not load, so rules 1 and 2 cannot be read.
  - `__init__(self, reasons: Sequence[str]=()) -> None` (line 968; internal)
- `protection_issues(vault: Any) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 973) — Why the vault's protection metadata cannot be trusted, or ``[]``.
- `exam_material(vault_or_sets: Any, repository: Any) -> ExamMaterial` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1023) — Exam material vault-wide (rules 1-4): ``vault`` or its ``source_sets``.
- `role_material(vault_or_sets: Any, repository: Any, withheld_role: Callable[[str | None], bool], *, member_reason: str='role_member', unit_reason: str='role_unit') -> Material` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1046) — Members' material whose role ``withheld_role`` names (rules 1 and 2), for callers that withhold more than exams (``corpus.teaching_exclusions``: problem sets, notes and unknown roles).
- `scope_only_material(vault_or_sets: Any, repository: Any) -> Material` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1071) — Curriculum C3 (spec §9.1, §9.3; Q2): the material of members and unit overrides whose role only scopes a deliverable (``role_authority.SCOPE_ONLY_ROLES``: a syllabus), resolved as every role without exam protection is (:func:`role_material`).
- `scope_only_among(vault_or_sets: Any, repository: Any, keys: Iterable[Sequence[str]], whole: Iterable[str]=()) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1082) — Whether any of these blocks (or readings named whole) is scope-only material (:func:`scope_only_material`, Codex review F3), independently of exam protection.
- `exam_withheld(vault_or_sets: Any, repository: Any, keys: Iterable[Sequence[str]]) -> frozenset[SpanKey]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1099) — The keys among ``keys`` that are exam material.
- `class SourceMarks` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1112) — One protected book's readings: where protection is marked exactly, the extractions held back until it is marked on them (rule 4), the kinds of mark that name no reading (``ambiguous``: :data:`AMBIGUOUS_SCOPE`, :data:`AMBIGUOUS_SELECTION`, :data:`AMBIGUOUS_SIGNAL`), and the marks…
- `source_marks(vault_or_sets: Any, repository: Any) -> dict[str, SourceMarks]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1127) — ``{source id: its marks}`` for every protected book (rule 4): what the book's card ("Mark exam material on this reading"), doctor and the marking action read.
- `reading_held_back(vault_or_sets: Any, repository: Any, extraction_id: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1141) — Whether a reading is withheld whole until protection is marked on it (rule 4).
- `protected_spans_by_reading(vault_or_sets: Any, repository: Any, source_id: str) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1149) — ``{reading: spans}`` every mark of a book would protect if it were read on that reading by its own unit ids, exact or not: the owner's marking suggestion's sources (never an authority).
- `held_out_refusal(material: Material, extraction_id: str | None) -> str` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1210) — The plain refusal for a Reader request over ``material``: a reading held back until it is marked says so (rule 4); anything else is held out.
- `spans_withheld(vault_or_sets: Any, repository: Any, extraction_id: str, span_ids: Iterable[str | None]) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1218) — The refusal when any of ``span_ids`` on ``extraction_id`` (or the whole reading) is exam or held-out material now (:func:`exam_material`'s ``covers`` and ``withheld``), else None.
- `held_out_material(vault_or_sets: Any, repository: Any) -> Material` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1236) — The held-out partition (:func:`held_out_partition`, every subject): what the Reader's model contexts refuse and a Reader import never turns into practice.
- `held_out_among(material: Material, extraction_id: str | None, span_ids: Iterable[str | None]) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1247) — The span ids among ``span_ids`` (in order, each once) that ``material`` covers.
- `class HeldOutSpan` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1261) — One held-out span: its identity and block text.
  - `key(self) -> str` (line 1269; public)
- `held_out_partition(vault_or_sets: Any, repository: Any, *, subject_ids: Iterable[str] | None=None) -> Material` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1273) — The held-out partition: every held-out unit (rule 3, any role, on the extraction that marks it), every reading held back until protection is marked on it exactly (rule 4, whole), plus the held-out assessment signals on the marked reading their model run read.
- `held_out_spans(vault_or_sets: Any, repository: Any, *, subject_ids: Iterable[str] | None=None) -> list[HeldOutSpan]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1294) — Every held-out span with its text, in a deterministic order (a span listed once).
- `class ItemExamStatus` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1332) — Why an item is exam material: reserved for a held-out exam, or made from exam material.
  - `as_dict(self) -> dict[str, Any]` (line 1340; public)
- `source_ref_keys(ref: Any) -> tuple[set[SpanKey], set[str]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1352) — One source ref's location, normalized: ``(block keys, extractions it names without a block)``.
- `reference_keys(value: Any, *, extraction_id: str | None=None) -> tuple[set[SpanKey], set[str]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1384) — Every source location a reference of any shape names, placed through :func:`source_ref_keys` (the AD23 redesign round 4: one key function for every shape): ``(block keys, extractions named without a block)``.
- `item_source_keys(item: Any) -> tuple[set[SpanKey], set[str]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1449) — The item's own source: ``(block keys, whole extractions)`` its canonical exercise and its provenance source refs name (:func:`source_ref_keys`).
- `source_ref_protected(material: ExamMaterial, ref: Any, repository: Any) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1466) — Whether a source ref's text (its quote) may be exam or held-out material, so a model context must not carry it (PF's parent quotes; Codex review F4).
- `held_out_item_ids(items: Iterable[Any], held_out: Material) -> frozenset[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1499) — The items whose own source (:func:`item_source_keys`: the canonical exercise, block-level provenance refs, an extraction named whole) lies in ``held_out`` material (Codex review F1: an item imported before its unit was marked held out).
- `held_out_items(vault: Any, repository: Any) -> frozenset[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1516) — The vault's practice items made from held-out material (:func:`held_out_material`).
- `held_out_selection_active(vault: Any) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1525) — ``goals.held_out_selection``: the kill switch of the serving rules (Codex review F6).
- `exposed_items(vault: Any, repository: Any, items: Iterable[Any], *, with_held_out: bool=False) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1545) — ``{item id: reasons}`` for the items among ``items`` that are no longer an independent check: the learner has been shown their own material (``db.stores.source_service.shown_items``: ``revealed``, ``source_exposed``, ``seen_in_proposal``) and, with ``with_held_out``, items made…
- `item_exam_status(item: Any, *, material: ExamMaterial | None=None, reserved: Iterable[str]=()) -> ItemExamStatus | None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1575) — Whether a practice item is exam material, or None.
- `exam_reserved(repository: Any, item_id: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1602) — Whether the item is reserved for a goal's held-out exam (an unreleased exam-pool row).

### Module constants

- `HELD_OUT_EVALUATION` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 125)
- `EXAM_ROLE` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 127)
- `EXAM_MEMBER` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 130)
- `EXAM_UNIT` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 131)
- `HELD_OUT_UNIT` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 132)
- `HELD_OUT_SIGNAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 133)
- `UNRESOLVED_UNIT` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 134)
- `UNMARKED_READING` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 136)
- `AMBIGUOUS_MARK` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 138)
- `EXAM_RESERVED` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 139)
- `EXAM_SOURCE` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 140)
- `PROTECTION_MARK_KEY` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 146)
- `MARKS_MADE_ON_KEY` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 152)
- `REVIEWED_UNPLACED` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 158)
- `_ELSEWHERE_WHOLE` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 461)
- `_ELSEWHERE_LABEL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 463)
- `AMBIGUOUS_SCOPE` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 685)
- `AMBIGUOUS_SELECTION` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 686)
- `AMBIGUOUS_SIGNAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 687)
- `SNAPSHOT_UNSETTLED` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 947)
- `SOURCE_SETS_UNREADABLE_CODE` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 951)
- `SOURCE_SETS_UNREADABLE_MESSAGE` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 954)
- `SCOPE_ONLY_REFUSAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1067)
- `HELD_OUT_REFUSAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1202)
- `HELD_BACK_REFUSAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1206)
- `_LOCATOR_FIELDS` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1381)
- `HELD_OUT_MATERIAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1542)
- `HELD_OUT_ITEM_REFUSAL` ([src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1571)

### Explicit exports

`__all__` declares:

- `AMBIGUOUS_MARK`
- `AMBIGUOUS_SCOPE`
- `AMBIGUOUS_SELECTION`
- `AMBIGUOUS_SIGNAL`
- `EXAM_MEMBER`
- `EXAM_RESERVED`
- `EXAM_ROLE`
- `EXAM_SOURCE`
- `EXAM_UNIT`
- `ExamMaterial`
- `ExamVerdict`
- `HELD_OUT_EVALUATION`
- `HELD_BACK_REFUSAL`
- `HELD_OUT_ITEM_REFUSAL`
- `HELD_OUT_MATERIAL`
- `HELD_OUT_REFUSAL`
- `HELD_OUT_SIGNAL`
- `HELD_OUT_UNIT`
- `HeldOutSpan`
- `ItemExamStatus`
- `MARKS_MADE_ON_KEY`
- `Material`
- `PROTECTION_MARK_KEY`
- `REVIEWED_UNPLACED`
- `SCOPE_ONLY_REFUSAL`
- `SourceMarks`
- `UNMARKED_READING`
- `UNRESOLVED_UNIT`
- `descendants`
- `exam_material`
- `exam_reserved`
- `exam_withheld`
- `exposed_items`
- `held_out_among`
- `held_out_item_ids`
- `held_out_items`
- `held_out_material`
- `held_out_partition`
- `held_out_refusal`
- `held_out_selection_active`
- `held_out_spans`
- `spans_withheld`
- `is_exam_role`
- `item_exam_status`
- `item_source_keys`
- `marks_made_on`
- `protected_spans_by_reading`
- `raw_roots`
- `reading_held_back`
- `role_material`
- `scope_only_among`
- `scope_only_material`
- `scope_reading_of`
- `selection_marks_exact`
- `source_marks`
- `reference_keys`
- `source_ref_keys`
- `source_ref_protected`

## Internal implementation anchors

- `class _Acc` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 192) — What a build has found so far, with its reasons and the pinned revisions behind it.
- `class _Reader` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 341) — One build's database reads, each made once.
- `_origin_units(reader: _Reader, origin: str, narrowing: set[str]) -> tuple[set[str], set[str]] | None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 413) — The scope resolved by unit id on the reading it names: ``(its spans there, the labels of its raw units)``, or None when a unit id does not resolve there.
- `_exact_scope_reading(reader: _Reader, member: Any) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 452) — The reading a member's scope names, when it names one it can be on (else None).
- `_member_units(reader: _Reader, member: Any, narrowing: set[str], acc: _Acc, reason: str, *, elsewhere: str) -> None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 466) — Resolve a member's narrowing units on the reading its scope names (``scope_extraction_id``), by unit id; a unit id that does not resolve there withholds every extraction of the book (fail closed).
- `_exam_narrowing(member: Any) -> set[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 511) — The member's scope units overridden to an exam role (rule 2).
- `_role_material(reader: _Reader, member: Any, withheld_role: Callable[[str | None], bool], acc: _Acc, *, member_reason: str, unit_reason: str) -> None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 517) — A member's material whose role ``withheld_role`` names: the whole source when its default role does (rule 1), else its scope's units on the reading the scope names: exam units with every other extraction whole, the other roles by label.
- `_outline_exam_sources(connection: Any) -> list[tuple[str | None, str | None, str]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 537) — ``(source id, revision id, extraction id)`` of every unit selection whose outline role pick names ``exam`` (the import-batch path, before any source set).
- `_json_value(text: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 554)
- `_reviewed_unplaced(metadata: Mapping[str, Any] | None) -> frozenset[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 585) — The unplaced marks the owner's marking reviewed (:data:`REVIEWED_UNPLACED`); none when it records none (a marking made before it was recorded).
- `_marked_selections(connection: Any) -> list[tuple[str, str | None, str | None, list[str], bool, Mapping[str, Any]]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 594) — ``(extraction id, source id, revision id, held-out unit ids, marked by the owner's action, paper metadata)`` of every unit selection that marks protection: a held-out mark (rule 3) or the owner's "Mark exam material on this reading" (:data:`PROTECTION_MARK_KEY`).
- `_held_out_signal_spans(inventory: Any) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 620)
- `_cache_signal_ledger(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 628) — The ledger migration 204's backfill would write, read from the inventory cache: for a database read before it is migrated (a dry run never migrates).
- `_signal_ledger(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 665) — Every row of the held-out signal ledger with its book (migration 204); on a database not yet migrated, what its backfill would write.
- `_unplaced_scope(unit_id: str) -> str` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 690) — An unplaced legacy exam scope unit, as the owner's marking records it reviewed.
- `_unplaced_signal(inventory_id: str) -> str` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 696) — A held-out signal of unknown reading (by the inventory that made it), as reviewed.
- `class _Marks` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 703) — One book's protection marks, each on the reading it names (rules 2-4).
- `_signal_counts(row: Mapping[str, Any], *, exam_sources: set[str], scoped: set[str], scope_spans: Mapping[str, set[str]]) -> bool` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 772) — Whether a ledger row's held-out signals are protection: made under an exam role, or on a book that is exam material now (rule 1: an exam member of any set, or an outline exam pick), or on spans an exact exam scope names on the same reading, or (a row whose role was not recorded)…
- `_protection_marks(reader: _Reader, vault_or_sets: Any) -> dict[tuple[str, str], _Marks]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 791) — Every book's protection marks, each on the reading it names (rules 2-4), read from the vault's source sets and the database, across every revision and extraction of the book whatever its membership: exam scopes (rule 2), held-out marks and the owner's marking action (rule 3, the…
- `_held_units(reader: _Reader, extraction_id: str, unit_ids: Iterable[str], held: _Acc) -> None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 876) — An extraction's own held-out marks (rule 3), by unit id: a split child withholds its whole raw parent, a merged unit its members; a mark that does not resolve withholds the whole extraction (fail closed).
- `_add_protection(reader: _Reader, vault_or_sets: Any, held: _Acc, exam: _Acc | None=None) -> None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 895) — Rules 2-4 into ``held`` (and the exam scopes' units into ``exam``): on each reading marked exactly, its own exam scope units, held-out marks and signals; every other extraction of a protected book, whole.
- `_runs(connection: Any, extraction_ids: Iterable[str]) -> dict[str, tuple[str | None, str | None]]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 929)
- `_source_sets(vault_or_sets: Any) -> list[Any]` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1006)
- `_require_readable(vault_or_sets: Any) -> None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1011) — Refuse (fail closed) a vault whose source sets did not load: without them rules 1 and 2 vanish and exam material reads as teaching.
- `_parse_block_span(locator: str) -> SpanKey | None` ([source](../../../../../../../src/learnloop/content/sources/exam_material.py), line 1345)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `reference_keys`; statically calls `reference_keys`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `item_source_keys`; statically calls `item_source_keys`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `held_out_item_ids`, `held_out_material`; statically calls `held_out_item_ids`, `held_out_material`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `SCOPE_ONLY_REFUSAL`, `reference_keys`, `scope_only_among`; statically calls `reference_keys`, `scope_only_among`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `HeldOutSpan`, `module`; statically calls `exam_material`, `held_out_spans`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `SCOPE_ONLY_REFUSAL`, `SourceSetsUnreadable`, `exam_material`, `reference_keys`, `scope_only_among`; statically calls `exam_material`, `reference_keys`, `scope_only_among`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; statically calls `exam_material`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `AMBIGUOUS_SCOPE`, `AMBIGUOUS_SELECTION`, `HELD_OUT_EVALUATION`, `MARKS_MADE_ON_KEY`, `PROTECTION_MARK_KEY`, `REVIEWED_UNPLACED`, `SourceMarks`, `marks_made_on`, `protected_spans_by_reading`, `source_marks`; statically calls `marks_made_on`, `protected_spans_by_reading`, `source_marks`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `exam_material`, `held_out_among`, `held_out_material`, `held_out_refusal`, `scope_only_among`; statically calls `exam_material`, `held_out_among`, `held_out_material`, `held_out_refusal`, `scope_only_among`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `MARKS_MADE_ON_KEY`, `PROTECTION_MARK_KEY`, `source_marks`; statically calls `source_marks`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `is_exam_role`; statically calls `is_exam_role`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `module`; statically calls `exam_withheld`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `module`; statically calls `exam_material`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `HELD_OUT_EVALUATION`, `MARKS_MADE_ON_KEY`, `PROTECTION_MARK_KEY`, `marks_made_on`; statically calls `marks_made_on`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `held_out_selection_active`; statically calls `held_out_selection_active`
- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `module`; statically calls `exam_withheld`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `exam_material`, `exposed_items`; statically calls `exam_material`, `exposed_items`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `source_ref_keys`; statically calls `source_ref_keys`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `spans_withheld`; statically calls `spans_withheld`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `module`; statically calls `exam_material`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `exam_material`, `spans_withheld`; statically calls `exam_material`, `spans_withheld`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `exposed_items`; statically calls `exposed_items`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `exposed_items`; statically calls `exposed_items`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `exposed_items`; statically calls `exposed_items`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `exam_reserved`; statically calls `exam_reserved`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `HELD_OUT_ITEM_REFUSAL`, `exam_reserved`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`; statically calls `exam_reserved`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; statically calls `exam_withheld`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `SNAPSHOT_UNSETTLED`, `module`, `protection_issues`, `source_ref_protected`; statically calls `exam_material`, `held_out_items`, `item_exam_status`, `protection_issues`, `source_ref_protected`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `protection_issues`; statically calls `protection_issues`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `exam_material`, `source_ref_protected`; statically calls `exam_material`, `source_ref_protected`
- [[Reference/Modules/learnloop/reader/phone_media|learnloop.reader.phone_media]] — imports `HELD_OUT_REFUSAL`, `exam_material`, `held_out_refusal`; statically calls `exam_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; statically calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; statically calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; statically calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; statically calls `exam_material`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `module`; statically calls `exam_material`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/scheduling/intent/feasibility|learnloop.scheduling.intent.feasibility]] — imports `module`; statically calls `held_out_items`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `held_out_items`, `held_out_selection_active`; statically calls `held_out_items`, `held_out_selection_active`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `is_exam_role`, `module`; statically calls `exam_material`, `exam_withheld`, `is_exam_role`, `role_material`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; statically calls `exam_material`, `role_material`, `scope_only_material`, `source_ref_keys`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `module`; statically calls `exam_withheld`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; statically calls `exam_material`, `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `held_out_material`; statically calls `held_out_material`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `held_out_material`; statically calls `held_out_material`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; statically calls `exam_material`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; statically calls `exam_material`, `source_marks`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `exam_material`; statically calls `exam_material`
- [[Reference/Modules/learnloop/teacher/exposure|learnloop.teacher.exposure]] — imports `item_source_keys`; statically calls `item_source_keys`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; statically calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `exam_material`, `item_exam_status`; statically calls `exam_material`, `item_exam_status`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `exam_reserved`; statically calls `exam_reserved`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `HELD_BACK_REFUSAL`, `HELD_OUT_REFUSAL`, `item_source_keys`, `reading_held_back`, `reference_keys`; statically calls `item_source_keys`, `reading_held_back`, `reference_keys`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `SourceSetsUnreadable`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `HELD_OUT_ITEM_REFUSAL`, `exam_reserved`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`; statically calls `exam_reserved`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `ASSESSMENT_ONLY_ROLES`, `is_scope_only_role`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `effective_unit_spans`; calls `effective_unit_spans`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `UnitRow`, `extraction_units`, `source_extraction_ids`; calls `extraction_units`, `source_extraction_ids`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `shown_items`; calls `shown_items`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/scope_seal|learnloop.vault.scope_seal]] — imports `scope_seal`; calls `scope_seal`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `pathlib`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] and 57 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — direct import
- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/figures_codex_review_helpers.py](../../../../../../../tests/figures_codex_review_helpers.py) — direct import
- [tests/mcp_c1a_landing_helpers.py](../../../../../../../tests/mcp_c1a_landing_helpers.py) — direct import
- [tests/reread_safety_helpers.py](../../../../../../../tests/reread_safety_helpers.py) — direct import
- [tests/reread_safety_landing_helpers.py](../../../../../../../tests/reread_safety_landing_helpers.py) — direct import
- [tests/router_card_helpers.py](../../../../../../../tests/router_card_helpers.py) — direct import
- [tests/router_card_reading_gaps_helpers.py](../../../../../../../tests/router_card_reading_gaps_helpers.py) — direct import
- [tests/test_ad1_fix_round4.py](../../../../../../../tests/test_ad1_fix_round4.py) — direct import
- [tests/test_ad1_fix_round5.py](../../../../../../../tests/test_ad1_fix_round5.py) — direct import
  - `test_a_reload_while_protection_is_built_is_never_judged_by_the_vault_it_replaced`
- [tests/test_ad1_fix_round6.py](../../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_a_publication_paused_between_assignment_and_bump_is_never_admitted`
- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`
- [tests/test_ad23_fix_r7.py](../../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_with_the_predicate_unavailable_nothing_is_reconciled`
- [tests/test_ad23_fix_r8.py](../../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_the_dose_arm_never_offers_or_returns_a_held_out_question`
- [tests/test_ad_epoch.py](../../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_frozen_outside_state_is_sent_only_at_its_epoch`
  - `test_a_reading_receipt_recorded_under_other_protection_is_mapped_again`
  - `test_any_change_to_the_protection_changes_the_epoch`
- [tests/test_ad_projection.py](../../../../../../../tests/test_ad_projection.py) — direct import
  - `test_a_whole_extraction_held_out_reads_as_no_extraction`
  - `test_every_recorded_reference_shape_is_located_through_the_shared_key_function`
- [tests/test_compare_methods.py](../../../../../../../tests/test_compare_methods.py) — direct import
  - `test_never_offered_for_exam_material`
- [tests/test_compare_sources_keep.py](../../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_source_objects_fail_closed`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_a_syllabus_exercise_is_refused_before_any_model_call`
  - `test_a_syllabus_made_during_the_import_writes_nothing`
  - `test_a_unit_override_leaves_the_rest_of_the_book_practice`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_an_unreadable_predicate_contributes_nothing`
  - `test_the_fixture_holds_every_kind_of_exam_material`
  - `test_the_syllabus_role_scopes_only_assessment_alignment_never_semantic_never_exam`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_rule_4_and_identity_bound_marks_reach_rule_c_through_learner_protection`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
  - `test_an_item_made_from_held_out_material_is_exam_material`
  - `test_an_unresolvable_held_out_mark_fingerprints_its_whole_extraction`
  - `test_exam_material_in_any_revision_of_an_exam_source_is_exam_to_every_reader`
  - `test_held_out_and_exam_role_picks_count_outside_any_source_set`
- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_a_held_out_mark_copied_onto_another_reading_is_never_exact`
  - `test_a_legacy_held_out_mark_withholds_every_reading_until_marked_exactly`
  - `test_a_scope_edited_outside_the_writer_names_no_reading`
  - `test_a_scope_naming_a_reading_it_cannot_be_on_fails_closed`
  - `test_a_textbook_with_held_out_signals_made_as_a_textbook_is_unaffected`
  - `test_an_exact_held_out_mark_under_a_legacy_scope_waits_for_the_owners_marking`
  - `test_an_exact_mark_never_resolves_a_reading_a_legacy_mark_may_also_be_about`
  - `test_f12_a_legacy_scope_never_follows_creation_order`
  - `test_f12_a_legacy_scope_over_reversed_unit_ids_withholds_every_reading`
  - `test_f12_a_scope_stays_on_its_reading_when_an_older_one_completes_later`
  - `test_f12_an_exact_scope_protects_the_units_of_the_reading_it_names`
  - `test_f13_a_confirmation_made_for_another_reading_returns_a_fresh_one`
  - `test_f13_the_confirmed_proposal_is_applied_exactly_and_bound_to_its_reading`
  - `test_f14_a_refresh_never_drops_signal_only_protection`
  - `test_f14_a_signal_made_on_an_exam_unit_protects_after_its_member_leaves`
  - `test_f2_a_reused_inventory_never_releases_duplicate_or_fragment_copies`
  - `test_f2_reuse_never_erases_the_origins_signal`
  - `test_f3_final_a_cli_open_changes_nothing_else`
  - `test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit`
  - `test_identity_rereview_f3_a_hand_edit_never_releases_a_signal_its_membership_qualified`
  - `test_identity_rereview_f3_exam_membership_the_writer_adds_survives_a_hand_edit`
  - `test_identity_rereview_f3_the_running_app_records_hand_edited_exam_membership`
  - `test_identity_rereview_f7_an_assessment_profile_is_not_an_exam_role`
  - `test_identity_review_a_signal_of_unknown_reading_is_named_plainly`
  - `test_identity_review_f1_a_confirmation_never_covers_an_ambiguous_mark_made_after_it`
  - `test_identity_review_f2_an_unbound_signal_never_lets_a_known_one_mark_its_origin`
  - `test_identity_review_f3_a_legacy_signal_survives_its_exam_membership_changing`
  - `test_identity_review_f3_an_upgraded_exam_signal_survives_its_qualification_leaving`
  - `test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on`
- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_the_automatic_build_scope_is_the_one_predicate`
- [tests/test_exam_protection_review.py](../../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_held_out_assessment_signal_is_held_out_for_the_reader_and_the_gate_alike`
  - `test_a_second_extraction_marked_by_the_owner_is_held_by_its_own_marks_only`
  - `test_an_unresolvable_mark_withholds_every_extraction_of_its_source`
  - `test_held_out_marks_in_two_extractions_each_hold_their_own_extraction_exactly`
  - `test_the_same_unit_marked_in_two_extractions_withholds_only_that_unit`
- [tests/test_figures_show_me.py](../../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_missed_predictions_text_rechecks_the_retrieved_passages`
  - `test_a_retrieved_passage_held_out_later_withholds_the_figure`
- [tests/test_figures_show_me_codex_review.py](../../../../../../../tests/test_figures_show_me_codex_review.py) — direct import
- [tests/test_intent_fix_round6.py](../../../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../../../tests/test_intent_fix_round7.py) — direct import
  - `test_f22_a_protected_set_error_names_its_input`
- [tests/test_k1_source_sets_gate.py](../../../../../../../tests/test_k1_source_sets_gate.py) — direct import
  - `test_a_valid_file_still_reads_the_exam_member_as_exam_material`
  - `test_a_vault_double_without_a_root_is_not_gated`
  - `test_every_shared_reader_refuses_unloaded_source_sets`
  - `test_the_exercise_import_and_the_facet_resolver_refuse`
  - `test_the_premise_the_corrupt_file_is_unreadable`
  - `test_the_readers_that_already_asked_still_refuse_and_ask_once`
  - `test_the_tutor_figures_and_phone_withhold_when_source_sets_did_not_load`
- [tests/test_k1_unreadable_adapters.py](../../../../../../../tests/test_k1_unreadable_adapters.py) — direct import
  - `test_the_chat_host_gets_the_same_code_and_message`
  - `test_the_message_names_the_file_the_cause_and_the_fix`
- [tests/test_learner_blindness_relax_codex_review.py](../../../../../../../tests/test_learner_blindness_relax_codex_review.py) — direct import
- [tests/test_library_ask_review.py](../../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_a_held_out_selection_is_refused_before_any_retrieval`
- [tests/test_mcp_c1a_review.py](../../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_a_recurrence_group_rooted_in_a_protected_hypothesis_keeps_no_statement`
- [tests/test_mcp_tools.py](../../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_learning_context_fails_closed_when_protection_cannot_be_read`
- [tests/test_plan_follows_path.py](../../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_an_exam_reading_plans_nothing_through_its_path`
- [tests/test_reader_digest_narrative.py](../../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_a_session_on_exam_material_is_never_sent`
- [tests/test_reader_pdf_selection.py](../../../../../../../tests/test_reader_pdf_selection.py) — direct import
  - `test_a_reading_held_back_by_rule_4_is_withheld_whole`
  - `test_the_reader_is_told_which_passages_are_held_out`
- [tests/test_reading_hardening_landing.py](../../../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_asking_for_a_held_out_sections_check_is_refused_before_anything_is_queued`
- [tests/test_reading_paths.py](../../../../../../../tests/test_reading_paths.py) — direct import
  - `test_a_stored_exercise_held_out_later_is_not_named`
  - `test_an_exam_or_held_out_exercise_is_never_named`
  - `test_an_exam_reading_has_no_path_and_no_call`
  - `test_an_unreadable_exam_predicate_shows_no_path`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_f1_reused_unit_ids_never_release_a_source_set_exam_scope`
  - `test_f2_a_held_out_signal_that_matches_nowhere_withholds_the_reading`
  - `test_f2_held_out_signals_stay_on_the_passage_they_name_after_a_reread`
  - `test_held_out_material_stays_withheld_on_the_new_reading`
  - `test_redesign_a_reading_of_a_new_revision_is_held_back_until_marked`
  - `test_redesign_a_refresh_keeps_an_exam_scoped_member_on_its_revision`
  - `test_redesign_a_signal_a_build_makes_on_a_held_back_reading_never_releases_it`
  - `test_redesign_a_study_map_save_keeps_the_owners_marks`
  - `test_redesign_an_unprotected_book_is_unaffected`
  - `test_redesign_f11_operators_are_never_erased_into_a_release`
  - `test_redesign_f1_a_moved_question_on_a_new_revisions_reread_is_never_unprotected`
  - `test_redesign_f1_a_moved_question_under_a_held_out_mark_is_never_unprotected`
  - `test_redesign_f2_duplicate_and_fragment_copies_are_never_unprotected`
  - `test_redesign_marking_the_new_reading_makes_it_usable`
  - `test_rereview_f1_a_held_out_mark_follows_its_question_not_its_label`
  - `test_rereview_f1_a_reused_unit_id_with_the_question_moved_out_keeps_it_withheld`
  - `test_rereview_f1_a_scope_whose_question_the_reread_reworded_withholds_the_reread`
  - `test_rereview_f2_a_half_moved_past_another_passage_withholds_the_reading`
  - `test_rereview_f2_a_held_out_passage_merged_with_its_neighbour_holds_out_the_merged_block`
  - `test_rereview_f2_a_held_out_passage_split_in_two_protects_both_halves`
  - `test_rereview_f2_a_held_out_unit_split_across_units_protects_both_halves`
  - `test_rereview_f2_a_long_block_between_the_parts_of_a_split_withholds_the_reading`
  - `test_the_reread_keeps_the_page_scope_and_carries_the_selection`
- [tests/test_reread_safety_landing.py](../../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path`
- [tests/test_rospeed2_section_map.py](../../../../../../../tests/test_rospeed2_section_map.py) — direct import
- [tests/test_router_card.py](../../../../../../../tests/test_router_card.py) — direct import
  - `test_the_exam_predicate_failing_withholds_every_question_and_answer`
- [tests/test_router_card_reading_gaps.py](../../../../../../../tests/test_router_card_reading_gaps.py) — direct import
  - `test_a_delivered_span_without_an_extraction_is_placed_or_fails_closed`
  - `test_an_unreadable_exam_predicate_withholds_a_reading_gaps_words`
- [tests/test_router_reader_activity.py](../../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_an_exam_anchored_inquiry_keeps_its_entry_and_never_its_words`
- [tests/test_secondary_attach.py](../../../../../../../tests/test_secondary_attach.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_codex_rereview_f1_a_lesson_is_judged_by_the_revision_it_showed_not_the_items_current_one`
  - `test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed`
  - `test_landing_r1_an_item_replaced_before_the_close_is_judged_by_the_revision_the_lesson_revealed`
- [tests/test_tutor_delivery_fixes.py](../../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_the_expanded_delivery_kill_switch_restores_the_predecessors_reader_window`

## Modification guidance

- Change exam material policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/exam_material.py](../../../../../../../src/learnloop/content/sources/exam_material.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
