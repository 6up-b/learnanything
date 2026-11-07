---
title: "learnloop.adaptive_difficulty.material_view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/material_view.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/material_view.py"
source_commit: "283405f0a5d78fa722adca27f66f4c6c05bff975"
source_commit_timestamp: "2026-11-07T02:53:30-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.material_view module"
  - "src/learnloop/adaptive_difficulty/material_view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.material_view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.material_view` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The one protected material view AD reads through (spec A8; Codex verify F19-F27, fix round 8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py) |
| Source lines | 1921 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `283405f0a5d78fa722adca27f66f4c6c05bff975` |
| Commit timestamp | `2026-11-07T02:53:30-05:00` |

## Public API

- `current_epoch() -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 152) — The epoch of the operation open in this context: what every AD artefact written in it is stamped with (an error outside an operation).
- `stamped(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 159) — A row to append to an AD artefact table with a ``protection_epoch`` column, stamped.
- `class MaterialView` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 262) — One operation's view of what AD may read (see the module docstring).
  - `__init__(self, vault: Any, repository: Any, protected: Protection) -> None` (line 265; internal)
  - `epoch(self) -> str | None` (line 286; public) — A digest of everything this view's projection withholds (the AD23 redesign, E2; round 2, class 3a): the predicate's material (whole extractions and span keys), the exam reservations, the protected current items (``Protection.ids``), the withheld revisions (current items' and sav…
  - `compute_epoch(self) -> str | None` (line 298; public)
  - `rows(self, connection: Any, table: str, where: str='', args: Iterable[Any]=(), *, order: str='', limit: int | None=None) -> list[dict[str, Any]]` (line 328; public) — The rows of a protected table AD may read: every column, the rows any of whose references resolves to a withheld entity left out (:meth:`keep`), a reading receipt's doses without the facets only withheld material names.
  - `filter(self, connection: Any, table: str, rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` (line 344; public) — :meth:`rows`' rule over rows a store already read (decoded JSON columns included).
  - `lookup(self, connection: Any, table: str, where: str, args: Iterable[Any]=(), *, stale_as_missing: bool=False) -> tuple[str, dict[str, Any] | None]` (line 359; public) — An idempotency read of AD's own ledgers: ``("missing", None)``, ``("withheld", None)`` (a row exists that AD may not read: its caller writes nothing and reads nothing of it) or ``("ok", row)``.
  - `_status(self, connection: Any, table: str, found: list[dict[str, Any]], *, stale_as_missing: bool=False) -> tuple[str, dict[str, Any] | None]` (line 373; internal)
  - `stored(self, connection: Any, table: str, reader: Any, *args: Any, **kwargs: Any) -> list[dict[str, Any]]` (line 385; public) — A store's (decoded) rows of a protected table, read by the rules and filtered by the rule: ``reader(connection, *args, **kwargs)`` returns a row, a list of rows or None.
  - `stored_status(self, connection: Any, table: str, reader: Any, *args: Any, **kwargs: Any) -> tuple[str, dict[str, Any] | None]` (line 391; public) — :meth:`lookup` over a store's reader: ``missing``, ``withheld`` (with the row's id only) or ``ok`` and the (first) row.
  - `keep(self, connection: Any, table: str, row: Mapping[str, Any]) -> bool` (line 399; public) — The registry's one rule: a row is withheld when any reference column resolves to a withheld entity (the kinds: ``protected_tables.COLUMNS``).
  - `epoch_current(self, table: str, row: Mapping[str, Any]) -> bool` (line 421; public) — Whether a row of an AD-owned artefact table was computed at the current protection epoch (``protected_tables.EPOCH``; round 2, class 3b).
  - `_ref_withheld(self, connection: Any, table: str, row: Mapping[str, Any], kind: str, value: Any) -> bool` (line 432; internal)
  - `_entity_withheld(self, connection: Any, kind: str, value: Any) -> bool` (line 493; internal) — A reference to a row of another protected table: withheld when that row is (by its own table's rule, in dependency order); a row since deleted is merely absent (not withheld).
  - `_self_withheld(self, connection: Any, table: str, row: Mapping[str, Any]) -> bool` (line 506; internal) — A row's own identity, by its table's rule.
  - `_lesson_record_withheld(self, row: Mapping[str, Any], column: str) -> bool` (line 557; internal) — Teacher TE3a (spec_teacher_v1 §14.2, §14.3; Option B): a lesson's own record (its goal, its outline, its receipt) is withheld when any reading it names (an extraction, a span, a section, a passage's key: a Reader selection's goal above all, and a receipt's ``exposure.readings``:…
  - `_gap_source_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool` (line 586; internal) — Router objective RO2 (Codex review F1): a gap is withheld with the learner text it was named from, by that source's own rule (``protected_tables.GAP_SOURCES``): its words can quote what the source showed.
  - `_figure_prediction_withheld(self, connection: Any, prediction_id: str) -> bool` (line 611; internal) — A figure prediction, for a gap named from it: withheld with its row or its figure's (each a READING row of its extraction), and when its figure has no passage of its own (a figure grounded in retrieved passages, whose keys AD never reads: fail closed) or either row is missing.
  - `_proposal_withheld(self, row: Mapping[str, Any]) -> bool` (line 632; internal) — A proposal is withheld when the item its effective payload (the edit, else the payload) creates or changes is: its id withheld, or its own sources (canonical exercise, provenance refs) in held-out material, or a withheld item among its source refs (round 2, class 2).
  - `_note_ref_withheld(self, connection: Any, note_id: Any) -> bool` (line 665; internal)
  - `administration_item(self, connection: Any, administration_id: Any) -> str | None` (line 671; public) — The legacy practice item an activity administration served (its surface's), or None.
  - `withheld(self, practice_item_id: Any) -> bool` (line 685; public) — Whether an item (by id) is withheld: protected now, or the predicate unavailable.
  - `covers(self, item: Any) -> bool` (line 690; public) — Whether a revision (a current item or a snapshot) is withheld, judged by its own sources.
  - `withheld_item_ids(self) -> frozenset[str]` (line 696; public) — The current items withheld (ids only: a count for a report, never content).
  - `item(self, practice_item_id: Any) -> Any` (line 703; public) — The current item, or None when it is withheld or not in the vault.
  - `items(self, *, learning_object_id: str | None=None, active: bool=False) -> list[Any]` (line 710; public) — The current items AD may read, sorted by id (all of them empty when unavailable).
  - `lo_for_item(self, practice_item_id: Any) -> str | None` (line 726; public)
  - `lo_facets(self, lo: Any) -> list[str]` (line 730; public) — The LO's authored facets, else the facets its visible active items measure (a facet only withheld items name is never AD's: Codex verify F19).
  - `facet_maps(self) -> tuple[dict[str, list[str]], dict[str, list[str]]]` (line 743; public) — ``(facet -> LOs, LO -> facets)`` for the replay's structure and the reading map.
  - `facet_universe(self) -> set[str]` (line 755; public) — Every facet the view names: the LOs' facets and the visible items' own facets.
  - `_withheld_and_visible_revisions(self, connection: Any=None) -> tuple[list[Any], list[Any]]` (line 767; internal) — ``(withheld items and revisions, visible items and revisions)``: the current items, and the saved snapshots when a connection is given (their content judged, never returned).
  - `protected_only_facets(self, connection: Any=None) -> set[str]` (line 786; public) — Facets that only withheld items or revisions name: named by none of the LOs' authored facets, the visible current items or the visible saved revisions (Codex verify F30: a facet merely absent from current content is not withheld).
  - `request_leaks(self, text: str, connection: Any=None) -> list[str]` (line 803; public) — What a serialized model request quotes of withheld material (fix round 9, R2): a withheld item's id or stem, or a facet or surface family only withheld material names.
  - `vault_view(self) -> Any` (line 835; public) — The vault as AD's material view sees it: the same object with only the visible current items, for helpers outside AD that read a whole vault (generation's authoring context, its contract and contrast reachability; fix round 9, R2), and only the visible notes (a source's canonica…
  - `note_extractions(self, connection: Any, note_id: Any) -> list[str]` (line 859; public) — The extraction runs of the source revisions a note is the canonical note of.
  - `note_withheld(self, connection: Any, note_id: Any) -> bool` (line 868; public) — Whether a note may not reach AD (fix round 12, F40): every note while unavailable; a source's canonical note when any of its extractions holds held-out material (the note's body is the source's text, so a held-out span anywhere in it is in the note).
  - `visible_commission_results(self, connection: Any) -> list[dict[str, Any]]` (line 886; public) — ``ad_commission_results`` of visible items, revisions and selections (Codex verify F29).
  - `dose_extra_withheld(self, connection: Any, variant: Any, content: Any) -> bool` (line 893; public) — Whether a drawn dose extra's content is withheld now (its question, or its example span).
  - `dose_draw_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool` (line 907; public) — Whether a dose draw is withheld now (Codex verify F47, fix round 14): its ORIGINATING section (the boundary it was drawn at) is withheld, or its chosen extra is.
  - `dose_rows(self, connection: Any) -> list[dict[str, Any]]` (line 919; public) — ``ad_dose_offers`` rows revalidated now (Codex verify F29, F47): a draw withheld by its originating section or its chosen extra, and that draw's uptake rows, are left out.
  - `_proposal_rule(self, connection: Any) -> Any` (line 927; internal)
  - `open_commissions(self, connection: Any, *, now: str | None=None) -> list[dict[str, Any]]` (line 930; public) — Open commissions as the view sees them: a result on a withheld item does not land, and a commission of a cell whose facet only withheld material names is not open (the same cohort as :meth:`selections`, fix round 11).
  - `landed_after_expiry(self, connection: Any, commission: Mapping[str, Any], landed_at: Any) -> bool` (line 946; public) — Whether a landing came after its commission expired (the store's expiry clock: the job's finish and the review decisions on items proposed for the LO; owner decision 2026-10-19).
  - `revision(self, connection: Any, content_hash: str | None) -> Any` (line 955; public) — A saved revision (``practice_item_snapshots``) as an item, or None when it is missing or withheld (its item withheld now, or its own sources held out).
  - `revisions(self, connection: Any) -> list[tuple[str, Any]]` (line 978; public) — Every visible saved revision, ``(content_hash, item)``, oldest first.
  - `audit_revisions(self, connection: Any) -> tuple[list[tuple[Any, str]], int]` (line 991; public) — ``(item, content_hash)`` for every visible active item's current revision and every visible saved revision, and how many revisions were withheld (a count for the backfill's plan).
  - `revision_withheld(self, connection: Any, content_hash: str | None, practice_item_id: Any=None) -> bool` (line 1035; public) — Whether a revision named by hash (and its item id, when known) is withheld now.
  - `_frozen_revisions(self, connection: Any) -> dict[str, str]` (line 1048; internal) — Each plan presentation's frozen served revision (``item_serve_inputs``).
  - `_answered_revisions(self, connection: Any) -> dict[str, tuple[str, ...]]` (line 1061; internal) — Each attempt's answered revision(s): the presentation's frozen revision and the revision field's own resolution reads (``load_attempt_rows``' ``item_snapshot_hash``).
  - `item_states(self, connection: Any) -> dict[str, Any]` (line 1084; public) — ``practice_item_state`` as AD may read it (fix round 12, F42's audit): visible items only, and only their lifecycle (``active``).
  - `attempt_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool` (line 1106; public) — Whether an attempt is withheld: its item is withheld now, or a revision it answered is (Codex verify F20: a public item's historical revision cut from held-out material).
  - `attempts(self, connection: Any) -> list[dict[str, Any]]` (line 1115; public) — Every visible ``practice_attempts`` row (all columns, latency included), oldest first.
  - `attempted_item_ids(self, connection: Any) -> set[str]` (line 1125; public)
  - `field_rows(self, connection: Any, **kwargs: Any) -> list[Any]` (line 1128; public) — Field's attempt rows derived FROM the view's attempts (``load_attempt_rows`` with ``attempt_rows``; Codex verify F24): a withheld answer never enters the familiarity history or any other cross-attempt derivation of a row kept.
  - `held_for_review(self, connection: Any) -> frozenset[str]` (line 1139; public) — The visible attempts whose grade is held for review now (the incumbent's rule, ``held_grades.held_for_review_attempts``, asked of the visible attempts only).
  - `assessment_contract(self, connection: Any, contract_version_id: Any) -> dict[str, Any] | None` (line 1148; public) — One assessment contract (``assessment_contract_versions``, whose ``contract_json`` holds the item's question, answer and rubric: a content column, ``column_classes``), or None when it is missing or withheld (the AD23 redesign round 5).
  - `worked_example_spans(self, connection: Any, extraction_id: str) -> set[str]` (line 1181; public) — The extraction's worked-example spans, exactly as the incumbent finds them (``source_retrieval.corpus.role_keys``: the stored role through ``effective_hint``), for a reading no withheld block touches; none for any other (round 8).
  - `reading_order(self, extraction_id: str) -> dict[str, int]` (line 1195; public) — The visible reading's spans by their stored ordinal (round 8, F2: candidates are taken in reading order, never by span id); empty for a withheld reading.
  - `protected_reading_counts(self, connection: Any) -> dict[str, int]` (line 1202; public) — What ``ad report`` says Option B leaves out (round 8): the readings the withheld material touches, and the reading events recorded on them that AD does not use.
  - `_names_withheld_reading(self, connection: Any, table: str, row_id: Any) -> bool` (line 1240; internal) — Whether a reading question's recorded anchor or context names a withheld reading.
  - `plan_feedback_events(self, connection: Any) -> list[dict[str, Any]]` (line 1257; public) — The plan's ``item_done`` and ``item_served`` events AD's candidate estimates may pair (the feedback dwell; Codex verify F28): the registry's plan-event rule (an event naming a withheld item, presentation or attempt is absent), in the plan's order.
  - `ledger(self, connection: Any) -> dict[str, Mapping[str, Any]]` (line 1273; public) — The authoritative observation ledger by attempt id (visible attempts only).
  - `measurement_masses(self, connection: Any, ledger: Mapping[str, Mapping[str, Any]]) -> dict[str, float]` (line 1282; public) — Whether each visible graded answer measures anything (``field.outcomes.measurement_masses`` over :meth:`ledger`'s entries), resolved here, in the rules: an interpretation recorded before its shared certainty LCB was is resolved from its raw grade event, its grader model's pooled…
  - `graded_counts(self, connection: Any) -> dict[str, int]` (line 1296; public) — Each LO's visible graded answers (the replay's window-closing cohort): the evidence count AD's commissioned path gives the rung selection instead of the incumbent's (fix round 10).
  - `window_cutoff(self, connection: Any, learning_object_ids: Sequence[str]) -> str | None` (line 1308; public) — When the reading window of these LOs last closed: their last visible attempt that closes a window as the replay reads it (graded, not skipped or a self-report; :func:`closes_window`).
  - `practice_minutes(self, connection: Any) -> list[float]` (line 1321; public) — The practice cohort's answer minutes (Codex verify F27): visible attempts that close a window (graded practice, not a skip or self-report) with a recorded positive latency.
  - `_presentation_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool` (line 1336; internal) — A presentation is withheld with its item, or with the revision it froze.
  - `presentations(self, connection: Any) -> dict[str, dict[str, Any]]` (line 1343; public) — Plan presentations of visible items and revisions, by id.
  - `presentation(self, connection: Any, presentation_id: str) -> dict[str, Any] | None` (line 1348; public)
  - `presentation_status(self, connection: Any, presentation_id: str) -> tuple[str, dict[str, Any] | None]` (line 1352; public) — ``("ok", row)``, ``("withheld", None)`` (its item is withheld now: a caller reports ``protected`` and reads nothing of it) or ``("missing", None)``.
  - `plan_event_visible(self, connection: Any) -> Any` (line 1359; public) — The rule for plan block events AD may read (the feedback dwell of AD's candidate estimates; Codex verify F28, fix round 10): an event naming a withheld item, an event of a withheld presentation (its block and item), or a completion of a withheld attempt, is invisible.
  - `reveals(self, connection: Any) -> list[dict[str, Any]]` (line 1383; public) — ``reveal_events`` rows AD may see (an exposure warms its LO, §5.2): withheld with its item, its attempt, or its tutor question (and so that question's attempt): an attempt withheld for the revision it answered withholds its reveals too (Codex verify F20, fix round 10).
  - `withheld_reveal_ids(self, connection: Any) -> set[str]` (line 1390; public) — The ``reveal_events`` ids AD may not read (every one while unavailable): for a reader outside AD that takes an exclusion list (the recent-reveal exclusion, fix round 11).
  - `_withheld_serves(self, connection: Any) -> set[tuple[str, str]]` (line 1399; internal) — ``(block_id, practice_item_id)`` of every presentation withheld with its frozen revision.
  - `selections(self, connection: Any, *, kind: str | None=None) -> list[dict[str, Any]]` (line 1408; public) — ``ad_selections`` as AD's report may count them (Codex verify F39, fix rounds 11-12): a draw whose chosen item or originating slot item is withheld (or in a presentation withheld with its frozen revision), whatever its kind (an empty-support draw included), or that commissioned…
  - `revision_hash_withheld(self, connection: Any, content_hash: Any) -> bool` (line 1423; public) — Whether a revision named only by its hash is withheld: a saved revision is judged by its own sources, else a current item with that revision by the item.
  - `forecast_receipts(self, connection: Any, *, kind: str) -> list[dict[str, Any]]` (line 1443; public) — Forecast receipts of visible items, revisions, attempts and presentations (Codex verify F24: a calibration fit and a forecaster's history never read a withheld item's forecast, whatever the current target).
  - `material_withheld(self, extraction_id: Any, span_id: Any=None) -> bool` (line 1456; public) — Whether a span (or, with none, the whole extraction) is held out; everything is withheld while the predicate is unavailable.
  - `reading_withheld(self, extraction_id: Any) -> bool` (line 1467; public) — Whether a READING (an extraction) is withheld for AD's reading signals (the AD23 redesign round 8, Option B): the withheld material touches it, wholly or in one block, or the predicate is unavailable (fail closed).
  - `document_ir(self, repository: Any, extraction_id: str) -> Any` (line 1485; public) — An extraction's document IR as AD may read it (the operation repository's loader, the one chokepoint for reading structure): none for a reading the withheld material touches (:meth:`reading_withheld`; the AD23 redesign round 8), else the stored IR exactly as ingest wrote it, whi…
  - `reading_structure_digest(self, extraction_id: str, *, structure: bool=True) -> str | None` (line 1498; public) — Router speed stage 2, item 1: a digest of every stored row AD's section mapping of one reading can read, as this view lets AD read it (:mod:`~learnloop.adaptive_difficulty.reading_cache` keys the held map by it): * every reading's, revision's and source's metadata (``source_extr…
  - `projected_vault(self) -> Any` (line 1566; public) — The vault an AD operation hands its readers (``op.vault``; the AD23 redesign, step 4): only the visible current items and notes (:meth:`vault_view`), no facet only withheld material names, and no LO or facet provenance reference into withheld material (a span list keeps its visi…
  - `_project_vault(self) -> Any` (line 1577; internal)
  - `_visible_ref(self, connection: Any, ref: Any) -> Any` (line 1609; internal) — A provenance reference as AD may read it (None: withheld).
  - `keys_withheld(self, keys: Iterable[tuple[str, str]], whole: Iterable[str]=()) -> bool` (line 1635; public) — Whether any located key (``exam_material.reference_keys``) is withheld: a block key in held-out material, or an extraction named whole that is held out.
  - `span_reanchors(self, repository: Any, from_extraction_id: str, to_extraction_id: str) -> list[dict[str, Any]]` (line 1642; public) — The span aliases AD may use between two readings (the operation repository's ``span_reanchors_between``, so the only set a ``SpanTranslator`` inside an operation sees; the AD23 redesign round 3).
  - `section_spans(self, extraction_id: str, section_id: str) -> list[str]` (line 1674; public) — A Reader section's spans, read only through :meth:`document_ir` (round 8, F3): none for a reading the withheld material touches.
  - `section_withheld(self, extraction_id: str, section_id: str) -> bool` (line 1706; public) — A Reader section is withheld with its reading (round 8): a section of a reading no withheld block touches has none.
  - `question_event_withheld(self, connection: Any, question_id: Any) -> bool` (line 1712; public) — The one protection reader of a tutor question (``question_events``; Codex verify F46, fix round 14), used when the sweep collects it and when its receipt is revalidated.
  - `question_withheld(self, row: Mapping[str, Any]) -> bool` (line 1760; public) — A Reader question is withheld when its extraction, or any span it is anchored on or cites, is held out (Codex verify F23).
  - `answered_questions(self, connection: Any, styles: Sequence[str]) -> list[dict[str, Any]]` (line 1773; public) — Answered, undismissed Reader questions of these styles that are not withheld.
  - `question(self, connection: Any, question_id: Any) -> dict[str, Any] | None` (line 1781; public) — One Reader question's row (every column), or None when it is missing or withheld.
  - `open_questions(self, connection: Any, extraction_id: str, section_id: str) -> list[dict[str, Any]]` (line 1787; public) — A section's produced, unanswered, undismissed Reader questions that are not withheld.
  - `reading_opportunities(self, connection: Any, *, learning_object_ids: Sequence[str] | None=None) -> list[dict[str, Any]]` (line 1794; public) — ``ad_reading_opportunities`` receipts of the current epoch, revalidated now (Codex verify F20): a receipt whose source is withheld is invisible.
  - `_opportunity_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool` (line 1816; internal) — Resolve a receipt's source again against the current predicate: the source row, by its own table's rule.
- `material_view(vault: Any, repository: Any, protected: Any=None) -> MaterialView` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 1872) — The open operation's view (the AD23 redesign): ``protected`` None returns the view of the operation open in this context (:mod:`~learnloop.adaptive_difficulty.operation`); outside an operation that is an error, so no AD reader computes a fresh, unguarded view by accident.
- `current_view() -> MaterialView` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 1891) — The view of the operation open in this context (an error outside one).
- `detached_view(vault: Any, repository: Any, protected: Any=None) -> MaterialView` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 1897) — A view computed here, outside any operation's guard: for the operation itself, the egress guards (which re-read protection afresh by design) and the incumbent's generation boundary (E1).
- `closes_window(attempt: Mapping[str, Any], ledger_entry: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 1910) — Whether a visible attempt closes its LO's reading windows (§5.6): graded (its ledger entry has evidence), and neither a skip nor a self-report (D8).

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 58)
- `UNAVAILABLE` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 61)
- `_UNSET` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 62)
- `_VALUE` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 63)
- `NON_WINDOW_TYPES` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 65)
- `READING_QUESTION_CONTEXTS` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 70)
- `READING_EVENT_PREFIXES` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 72)
- `_ENTITY_TABLES` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 193)
- `_LESSON_RECORDS` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 208)
- `_FIGURE_PREDICTION_PREFIX` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 250)
- `_FIGURE_EXPLANATION_SUFFIX` ([src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 251)

### Explicit exports

`__all__` declares:

- `MaterialView`
- `NON_WINDOW_TYPES`
- `UNAVAILABLE`
- `closes_window`
- `current_view`
- `detached_view`
- `material_view`

## Internal implementation anchors

- `_has_table(connection: Any, table: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 75)
- `_rows(connection: Any, sql: str, args: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 80)
- `_table_rows_digest(connection: Any, table: str, where: str, args: Iterable[Any]=()) -> bytes` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 86) — A digest of every row of ``table`` matching ``where``, every column, in rowid order (router speed stage 2, item 1).
- `_json(raw: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 107)
- `_replaced(vault: Any, **fields: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 116) — A copy of ``vault`` with ``fields`` replaced (a ``LoadedVault``, or a test's stand-in).
- `_select(table: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 131) — A protected table's columns the rules read and hand out: all but the derived ones (``protected_tables.DERIVED``; the guard refuses those outside the derivation scope).
- `_stamp(row: Mapping[str, Any], rule: str) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 141) — A row's protection epoch, by its table's rule (``column:C`` or ``json:C:K``).
- `_as_rows(found: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 165)
- `_columns(table: str) -> Mapping[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 173) — The registry's classification of a protected table's columns (an error for any other).
- `_value(row: Mapping[str, Any], column: str) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 182) — A column's value in a raw row, or in a store's decoded row (``x_json`` decoded as ``x``).
- `_lesson_exposure(record: Any) -> tuple[set[str], bool, list[Mapping[str, Any]]] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 212) — Teacher TE3a (Codex review F1): a lesson receipt's ``exposure`` as ``(the vault items it showed or revealed, whether the receipt cannot be judged, the frozen identities of the revisions it exposed)``; None for a record with no exposure (a goal, an outline).
- `_spans(raw: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 254)
- `_in_rules(method: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 1847) — Run a view reader in the rules' read scope (the AD guard lets the rules read protected tables; their SQL carries the rules marker), through the scope's codec: a failure inside it leaves as a ``ViewFailure`` of its kind and type only (the final round).
- `_wrap_readers(cls: type) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/material_view.py), line 1863)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `detached_view`, `material_view`; statically calls `detached_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `current_view`; statically calls `current_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `detached_view`, `material_view`; statically calls `detached_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `current_view`, `material_view`; statically calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `MaterialView`, `detached_view`; statically calls `detached_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `current_view`, `material_view`; statically calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `current_view`; statically calls `current_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `material_view`; statically calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `MaterialView`; statically calls `MaterialView`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `current_view`, `material_view`; statically calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `current_view`; statically calls `current_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `current_view`, `material_view`; statically calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `detached_view`; statically calls `detached_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `EPOCH_VERSION`, `Scope`, `current`, `scoped`; calls `current`, `scoped`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `LESSON_KIND`
- [[Reference/Modules/learnloop/adaptive_difficulty/projection|learnloop.adaptive_difficulty.projection]] — imports `project_repository`; calls `project_repository`
- [[Reference/Modules/learnloop/adaptive_difficulty/protected_tables|learnloop.adaptive_difficulty.protected_tables]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `Protection`, `module`; calls `guard`, `protection`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading_cache|learnloop.adaptive_difficulty.reading_cache]] — imports `module`; calls `held`, `hold`, `structure_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `lesson_opportunities_on`; calls `lesson_opportunities_on`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `reference_keys`; calls `reference_keys`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `computed_aliases`; calls `computed_aliases`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `commission_results`, `dose_rows`, `landed_after_expiry`, `open_commissions`, `selections`
- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `module`; calls `list_receipts`
- [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] — imports `load_authoritative_observation_ledger`; calls `load_authoritative_observation_ledger`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `load_attempt_rows`, `measurement_masses`; calls `load_attempt_rows`, `measurement_masses`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `MANUAL`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `role_keys`; calls `role_keys`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CanonicalExercise`, `PracticeItem`, `SourceRef`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `copy`, `dataclasses`, `functools`, `hashlib`, `json`, `logging`, `re`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] and 19 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_dose_draw_at_a_protected_origin_is_a_draw_never_made`
  - `test_a_protected_receipt_occupies_no_daily_cap_slot`
  - `test_a_run_whose_quoted_revision_was_replaced_then_protected_is_not_used`
  - `test_a_saved_run_proposed_before_its_subject_was_protected_is_not_used`
  - `test_a_tutor_exchange_on_a_protected_canonical_note_enters_no_prediction`
  - `test_a_tutor_exchange_whose_recorded_context_quotes_a_protected_span_enters_no_prediction`
  - `test_an_empty_support_draw_of_a_protected_slot_leaves_the_report_cohort`
  - `test_feedback_dwell_skips_a_serve_withheld_with_its_presentation`
  - `test_goal_focus_follows_the_live_decision_view_with_promoted_predictor_off`
  - `test_the_replay_cache_never_serves_a_snapshot_across_a_protection_change`
  - `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_a_protected_item_never_steers_the_commissioned_cell_or_readiness`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_report_sensitivity_never_re_forecasts_a_withheld_item`
- [tests/test_ad23_fix_r9.py](../../../../../../tests/test_ad23_fix_r9.py) — direct import
  - `test_an_attempt_on_a_held_out_answered_revision_is_filtered_at_the_source`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_density_lowerings_join_offers_to_their_visits`
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_a_failure_inside_a_scope_leaves_with_no_cause_context_or_text`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_why_this_item_names_the_draw_that_chose_it`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_coupling_is_prediction_only`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_commission_drawn_under_other_protection_is_not_open`
  - `test_a_protected_pending_proposal_never_holds_a_commission_open`
  - `test_any_change_to_the_protection_changes_the_epoch`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
  - `test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows`
  - `test_an_exam_reserved_items_contract_is_read_only_through_the_rules`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_view_labels_the_pick_as_field_does_outside_ad`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
  - `test_every_serving_branch_runs_with_zero_denials_and_fields_labels`
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_a_mixed_reading_reads_exactly_as_if_deleted`
  - `test_attempt_evidence_from_a_visible_span_of_a_mixed_reading_is_unchanged`
  - `test_marking_and_release_flip_the_epoch_and_the_reading_with_it`
  - `test_probe_raw_section_membership_in_the_dose_arm`
- [tests/test_ad_protected_tables.py](../../../../../../tests/test_ad_protected_tables.py) — direct import
  - `test_every_derived_column_has_a_treatment`
- [tests/test_ro2_ad_raw_document_reads.py](../../../../../../tests/test_ro2_ad_raw_document_reads.py) — direct import
  - `test_at_run_time_ad_loads_a_reading_only_through_its_chokepoint`
  - `test_ro4s_reading_action_maps_its_section_through_the_chokepoint`
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_the_registry_restates_the_figure_source_grammar`
- [tests/test_rospeed2_section_map.py](../../../../../../tests/test_rospeed2_section_map.py) — direct import
  - `test_every_ir_load_of_the_held_map_is_inside_the_chokepoint`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_a_lesson_naming_a_withheld_reading_is_absent_and_an_unavailable_predicate_reads_none`
  - `test_codex_f1_a_lesson_whose_shown_items_or_passages_are_withheld_now_is_absent`
  - `test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed`
  - `test_landing_r1_an_item_replaced_before_the_close_is_judged_by_the_revision_the_lesson_revealed`
  - `test_landing_r1_the_receipt_unions_frozen_identities_and_a_display_without_them_fails_closed`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_band_positions_thresholds_p_band_and_reads_the_side_from_expected_success`

## Modification guidance

- Make changes here when the responsibility remains material view within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/material_view.py](../../../../../../src/learnloop/adaptive_difficulty/material_view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
