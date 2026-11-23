"""May this figure be built, sent or shown now? The figure package's protection predicates, in one module.

A figure is never built from, sent with or shown over what the learner must not see now: exam or held-out passages
(:func:`withheld_message`, the figure side's door to the one exam predicate,
``content.sources.exam_material.spans_withheld``); what a learner state its author was sent was read from (the
answers, items, questions and passages behind it: ``learner_state.inputs_withheld``); and an item's own passage while
the item is under a live administration or held open by today's stored plan (:func:`item_passages`). Each predicate
reads the protection as it is now, returns why (or None), and fails closed when it cannot read; none sends, stores or
decides anything else.

Which predicate each moment asks, over which inputs:

+----------------------+------------------------------------------+-----------------------------------------------+
| moment               | predicate                                | inputs                                        |
+======================+==========================================+===============================================+
| the request          | :func:`withheld_message`,                | the passage (the selection, a region's block) |
| (``check_request``)  | :func:`keys_withheld`; a revision's      | or, with none, the home's span; the given     |
|                      | base: :func:`show_me_row`,               | grounding keys; the base row, as at delivery  |
|                      | :func:`row_withheld`                     |                                               |
+----------------------+------------------------------------------+-----------------------------------------------+
| grounding            | :func:`keys_withheld`, one key at a time | each retrieved or given passage as it is kept |
+----------------------+------------------------------------------+-----------------------------------------------+
| the build's reuse    | :func:`learner_state_withheld`,          | a rich figure reused alone; another setting's |
|                      | :func:`_learner_inputs_unrecorded`       | figure (a marked row with no record is never  |
|                      |                                          | reused)                                       |
+----------------------+------------------------------------------+-----------------------------------------------+
| the rich job's start | :func:`_withheld`,                       | the saved context (passage, paragraphs around |
|                      | :func:`_inherited_withheld`,             | it, region, retrieved keys, home); inherited  |
|                      | :func:`_learner_state_withheld`; a       | learner states; the saved state; the item     |
|                      | prebuild:                                | passages the saved context names              |
|                      | :func:`rich_base_item_protected`         |                                               |
+----------------------+------------------------------------------+-----------------------------------------------+
| each rich request    | the gate's hold:                         | the saved and inherited learner states; a     |
| and its store        | :func:`_learner_state_withheld`,         | prebuild: the item passages its saved context |
|                      | :func:`_inherited_withheld`; a prebuild: | names                                         |
|                      | :func:`rich_base_item_protected`         |                                               |
+----------------------+------------------------------------------+-----------------------------------------------+
| a rich row recovered | :func:`stored_learner_state_withheld`,   | the stored row's record; the payload's state  |
| or reused by the job | :func:`_learner_state_withheld`,         | and inherited states                          |
|                      | :func:`_inherited_withheld`              |                                               |
+----------------------+------------------------------------------+-----------------------------------------------+
| delivery, a lesson's | :func:`figure_withheld`: the row, the    | the home's spans and every span the author    |
| visual, the hint     | show-me switch (:func:`show_me_row`),    | was sent (:func:`_figure_spans`); retrieved   |
| chooser              | :func:`row_withheld`                     | keys; the homes (:func:`figure_homes`); the   |
|                      |                                          | learner-state lineage                         |
+----------------------+------------------------------------------+-----------------------------------------------+
| a list               | :func:`row_withheld`,                    | as at delivery; a quick figure's rich         |
|                      | :func:`show_me_row`; a rich intent:      | intent's saved context                        |
|                      | :func:`_withheld`                        |                                               |
+----------------------+------------------------------------------+-----------------------------------------------+
| a pre-build filter   | :func:`withheld_message`,                | the candidate's passage; a planned visual's   |
| (``prefetch``)       | :func:`keys_withheld`,                   | grounding keys; the author's whole context    |
|                      | :func:`item_passages`                    | (``prefetch.item_protection``, ``protected``) |
+----------------------+------------------------------------------+-----------------------------------------------+

The learner-state lineage is kept in three places, and :func:`learner_state_withheld` reads all three, for a figure
and every figure it was made from (:func:`_lineage`): a row's own record
(``verification_report[LEARNER_STATE_INPUTS_KEY]``), a quick figure's rich intent
(``verification_report[RICH_INTENT_KEY]``: its job's payload), and a rich job's payload (``author_context`` with
``learner_state_inputs``, and a revision's ``INHERITED_LEARNER_INPUTS_KEY``). A row whose author was sent a state
but that keeps no record of it (:func:`_learner_inputs_unrecorded`) is withheld for good.

The callers' own compositions stay with them: the pre-build pass's (``prefetch.item_protection`` and ``protected``,
over the author's whole context), the hint chooser's (``help.qualifying_figure``: an attempt item's own blocks) and
the sidecar's attempt-host checks. ``figure_admission`` (the switches and the gate) is a leaf below this module, and
this module imports nothing of the build.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import daily_plans as plan_store
from learnloop.db.stores import figures as store
from learnloop.figure_admission import figure_home_keys, figures_enabled
from learnloop.figures import routes as R

_LOG = logging.getLogger(__name__)


#: RW5d P3: the host references that name an attempt (an attempt host's
#: figure has no reading position, so no home: spec §7.2, §13.1).
ATTEMPT_HOST_REFS = ("item_id", "submission_id", "workbench_session_id", "attempt_id")
#: The key a quick figure's verification report keeps its rich job's intent
#: under (Codex review F8): the job's payload, committed with the figure.
RICH_INTENT_KEY = "rich_intent"
#: The rich figure's report key keeping what its author's learner state was
#: read from (``LearnerStateRead.inputs``; Codex re-review F2). Present only
#: when the author was sent a learner state; never shown or sent to a model.
LEARNER_STATE_INPUTS_KEY = "learner_state_inputs"
#: Codex review F4: a rich revision job's record of what the learner states
#: its earlier versions' authors were sent were read from (a list; ``None``
#: for a version with no record, which fails closed). Absent when none was.
INHERITED_LEARNER_INPUTS_KEY = "inherited_learner_state_inputs"


# ---------------------------------------------------------------------------
# Exam material: the one predicate, over everything a figure was built from
# ---------------------------------------------------------------------------

def withheld_message(vault: Any, repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> str | None:
    """The refusal when any of the spans (or the whole reading) is exam or
    held-out material (``exam_material(...).withheld``), else None: the
    shared :func:`~learnloop.content.sources.exam_material.spans_withheld`,
    which learner-text gaps ask too (fix round 2, F1). The set is all exam
    material (rules 1-4), wider than the held-out partition the Reader's Ask
    refuses: a past paper with no marks or signals gets no figure, though Ask
    explains it."""

    from learnloop.content.sources.exam_material import spans_withheld

    return spans_withheld(vault, repository, extraction_id, span_ids)


def _figure_spans(row: Mapping[str, Any]) -> list[str]:
    """Every span a figure was built from: the selection, the region's and
    the crop's block, and the complete manifest of what the author was sent
    (the paragraphs around it too: a figure may show a neighbour's quoted
    assumption; Codex review F1)."""

    spans = [str(span) for span in row.get("span_ids") or ()]
    region = row.get("region") or {}
    if region.get("span_id"):
        spans.append(str(region["span_id"]))
    if row.get("asset_id"):
        spans.append(str(row["asset_id"]))
    spans += [str(span) for span in row.get("input_span_ids") or ()]
    return list(dict.fromkeys(spans))


def keys_withheld(vault: Any, repository: Repository, keys: Sequence[Sequence[str]]) -> str | None:
    """RW5d: the refusal when any ``(extraction_id, span_id)`` (a retrieved
    passage in any source, or its neighbour) is held out now, else None: the
    one predicate, asked per source."""

    by_extraction: dict[str, list[str]] = {}
    for key in keys:
        if len(key) == 2 and key[0]:
            by_extraction.setdefault(str(key[0]), []).append(str(key[1]))
    for extraction_id, spans in by_extraction.items():
        message = withheld_message(vault, repository, extraction_id, spans)
        if message is not None:
            return message
    return None


def row_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None:
    """A stored figure's held-out refusal now, else None: its home's spans and
    (RW5d) every retrieved passage it was built from, across sources. A figure
    with no home (P3's practice hosts) is checked through its keys alone."""

    message = None
    if row.get("extraction_id"):
        message = withheld_message(vault, repository, row["extraction_id"], _figure_spans(row))
    elif not row.get("input_span_keys") and (row.get("grounding") or "anchor") != "none":
        return "That figure has no source to check, so it isn't shown."
    message = message or keys_withheld(vault, repository, row.get("input_span_keys") or ())
    if message is None and row.get("id"):
        # RW5d (Codex review F4): a figure with no passage is also checked at
        # every place it lands (its homes: never sent to the author, so not in
        # its input manifest), as the request itself was.
        homes = figure_homes(repository, row)
        if homes is None:
            return "That figure's place in the book is unreadable, so it isn't shown."
        message = keys_withheld(vault, repository, homes)
    # Learner data-relax 2 (Codex re-review F2): a rich figure whose author
    # was sent the learner's state keeps what that state was read from; it
    # goes out only while none of that is protected now. Follow-ups Nov 2:
    # a quick figure too, and every figure it was made from (its earlier
    # versions, a fuller version's quick figure), read from the current rows.
    return message or learner_state_withheld(vault, repository, row)


# ---------------------------------------------------------------------------
# The learner state a figure's authors were sent, over the figure's lineage
# ---------------------------------------------------------------------------

def learner_state_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None:
    """Why a stored figure may not go out now because of the learner state
    an author of it was sent, or None (follow-ups Nov 2, ruling R1 of learner
    data-relax 2: exam-material protection, not privacy).

    Read from the current rows at presentation time, for the figure and every
    figure it was made from (its earlier versions through ``supersedes_id``,
    whose spec or program a revision's author is sent; a fuller version's
    quick figure through ``fuller_of_id``, whose brief its author is sent):
    each row's own record (quick and rich rows alike keep
    ``learner_state_inputs`` in their report) and a quick figure's rich intent
    (the job's payload, so a fuller version stored with no record of its own
    is checked by what its job carried). A row whose prompt version says its
    author was sent a learner state (``+learner-v1``) but that keeps no record
    and no intent carrying one (a quick figure built before quick rows kept
    the record) has dependencies nobody can name: it is withheld (Codex review
    F3) for good: its dependencies are never inferred (Codex re-review F5), and a
    press of the same input builds a fresh figure with its own record
    (:func:`_recorded_input_key`). A figure no author of which was sent a
    learner state has nothing to check here, exactly as before."""

    lineage = _lineage(repository, row)
    if lineage is None:
        return None
    for found in lineage:
        message = stored_learner_state_withheld(vault, repository, found)
        intent = _rich_intent(found)
        if message is None:
            message = intent_learner_state_withheld(vault, repository, intent)
        if message is None and _learner_inputs_unrecorded(found):
            message = LEARNER_STATE_UNRECORDED
        if message is not None:
            return message
    return None


#: Codex review F3: a figure whose author was sent the learner's state (its
#: prompt version says so) but whose row keeps no record of what that state
#: was read from.
LEARNER_STATE_UNRECORDED = ("That figure was made from what LearnLoop knew about your work then, and what that was "
                            "read from wasn't kept, so it isn't shown; ask for it again.")


def _rich_intent(row: Mapping[str, Any]) -> Any:
    report = row.get("verification_report") or {}
    return report.get(RICH_INTENT_KEY) if isinstance(report, Mapping) else None


def _learner_inputs_unrecorded(row: Mapping[str, Any]) -> bool:
    """Codex review F3: the row's author was sent a learner state (the prompt
    version's ``+learner-v1``) and neither its report nor its rich intent
    keeps what that state was read from. An unmarked row (no learner state
    sent) is never unrecorded."""

    if R.LEARNER_SUFFIX not in str(row.get("prompt_version") or ""):
        return False
    report = row.get("verification_report") or {}
    if isinstance(report, Mapping) and LEARNER_STATE_INPUTS_KEY in report:
        return False
    intent = _rich_intent(row)
    return not (isinstance(intent, Mapping) and LEARNER_STATE_INPUTS_KEY in intent)


def _lineage(repository: Repository, row: Mapping[str, Any]) -> list[Mapping[str, Any]] | None:
    """The figure and every figure it was made from (``supersedes_id``,
    ``fuller_of_id``), read from the current rows; None without the tables."""

    lineage = [row]
    seen = {str(row.get("id") or "")}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return None
        index = 0
        while index < len(lineage):  # each row once (``seen``), so it ends
            current = lineage[index]
            index += 1
            for parent_id in (current.get("supersedes_id"), current.get("fuller_of_id")):
                if parent_id and str(parent_id) not in seen:
                    seen.add(str(parent_id))
                    parent = store.figure(connection, str(parent_id))
                    if parent is not None:
                        lineage.append(parent)
    return lineage


def inherited_learner_inputs(repository: Repository, row: Mapping[str, Any]) -> list[Any]:
    """What every learner state the authors of ``row`` and of the figures it
    was made from were sent was read from (Codex review F4): a revision's rich
    job carries it, so the job checks it at admission, before every request
    and before it stores, though the revision sends no learner state of its
    own (it sends the earlier program). A marked row with no record gives
    ``None``, which the check fails closed on. Empty when none was sent."""

    inherited: list[Any] = []
    for found in _lineage(repository, row) or ():
        report = found.get("verification_report") or {}
        if isinstance(report, Mapping) and LEARNER_STATE_INPUTS_KEY in report:
            inherited.append(report[LEARNER_STATE_INPUTS_KEY])
        intent = _rich_intent(found)
        if isinstance(intent, Mapping) and LEARNER_STATE_INPUTS_KEY in intent:
            inherited.append(intent[LEARNER_STATE_INPUTS_KEY])
        if _learner_inputs_unrecorded(found):
            inherited.append(None)
    return inherited


# ---------------------------------------------------------------------------
# Where a figure lands, and delivery
# ---------------------------------------------------------------------------

def figure_homes(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]] | None:
    """Where a figure with no passage lands (:func:`learnloop.figure_admission.figure_home_keys`):
    every recorded request's reading position; empty for an anchored figure."""

    if row.get("span_ids") or row.get("region"):
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return figure_home_keys(connection, str(row["id"]))


def show_me_row(row: Mapping[str, Any]) -> bool:
    """A figure built from a goal or with no anchor (RW5d): absent while ``figures.enabled`` is off."""

    return row.get("goal_text") is not None or (row.get("grounding") or "anchor") != "anchor"


def figure_withheld(vault: Any, repository: Repository, figure_id: str) -> bool:
    """Whether a stored figure may not go out now (its row is gone, or any
    span it was built from is held out, or (RW5d) it is a show-me figure
    while figures are off). Fails closed."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, figure_id) if store.has_tables(connection) else None
    if row is None:
        return True
    if show_me_row(row) and not figures_enabled(vault):
        return True
    return row_withheld(vault, repository, row) is not None


# ---------------------------------------------------------------------------
# A rich job's saved context
# ---------------------------------------------------------------------------

def _withheld(vault: Any, repository: Repository, base: Mapping[str, Any]) -> str | None:
    message = None
    spans = [*list(base.get("span_ids") or ()), *list(base.get("input_span_ids") or ())]
    if (base.get("region") or {}).get("span_id"):
        spans.append(str(base["region"]["span_id"]))
    if base.get("extraction_id") and spans:
        message = withheld_message(vault, repository, str(base["extraction_id"]), spans)
    keys = [tuple(key) for key in base.get("input_span_keys") or ()]
    home = base.get("home")
    if home and home.get("extraction_id") and home.get("span_id"):
        keys.append((str(home["extraction_id"]), str(home["span_id"])))
    return message or (keys_withheld(vault, repository, keys) if keys else None)


#: A saved learner state something it was read from is protected now.
LEARNER_STATE_PROTECTED = ("Not sent: something this animation was to be told about your work is protected now "
                           "({reason}); ask for it again.")


def _carries_learner_state(payload: Mapping[str, Any]) -> bool:
    return bool((payload.get("author_context") or {}).get("learner_state"))


def _inherits_learner_state(payload: Mapping[str, Any]) -> bool:
    return bool(payload.get(INHERITED_LEARNER_INPUTS_KEY))


def _inherited_withheld(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> str | None:
    """Why a revision job's inherited learner states may not be built on now,
    or None (each against the protection as it is now; no record: fail closed)."""

    from learnloop.figures.learner_state import inputs_withheld

    for inputs in payload.get(INHERITED_LEARNER_INPUTS_KEY) or ():
        reason = inputs_withheld(vault, repository, inputs)
        if reason is not None:
            return LEARNER_STATE_PROTECTED.format(reason=reason)
    return None


def stored_learner_state_withheld(vault: Any, repository: Repository, row: Mapping[str, Any]) -> str | None:
    """Why a stored rich figure whose author was sent the learner's state may
    not go out (be delivered, recovered or reused) now, or None: what that
    state was read from is checked again against the protection as it is now
    (``learner_state.inputs_withheld``; a missing record fails closed). A
    figure whose author was sent no learner state has nothing to check here
    (Codex re-review F2)."""

    report = row.get("verification_report") or {}
    if not isinstance(report, Mapping) or LEARNER_STATE_INPUTS_KEY not in report:
        return None
    return _learner_state_withheld(vault, repository, {LEARNER_STATE_INPUTS_KEY: report[LEARNER_STATE_INPUTS_KEY]})


def intent_learner_state_withheld(vault: Any, repository: Repository, payload: Any) -> str | None:
    """Why a saved rich job payload's learner state (a quick figure's durable
    rich intent) may not go out now, or None when its author was sent no
    learner state (follow-ups Nov 2: a fuller version stored with no record of
    its own is read from its quick figure's intent, the job's payload)."""

    if not isinstance(payload, Mapping) or not _carries_learner_state(payload):
        return None
    return _learner_state_withheld(vault, repository, payload)


def _learner_state_withheld(vault: Any, repository: Repository, payload: Mapping[str, Any]) -> str | None:
    """Why the saved learner state may not be sent now, or None
    (``learner_state.inputs_withheld``: its answers, items, questions and
    passages against the protection as it is now; no record: fail closed)."""

    from learnloop.figures.learner_state import inputs_withheld

    reason = inputs_withheld(vault, repository, payload.get("learner_state_inputs"))
    return None if reason is None else LEARNER_STATE_PROTECTED.format(reason=reason)


# ---------------------------------------------------------------------------
# An item's own passage, under a live administration or held open by the plan
# ---------------------------------------------------------------------------

#: ``learner_protection.withheld_items`` reasons naming an item under a live administration (an
#: open cold check or a repair's cold retry, an assessment reservation, a diagnostic probe). Exam
#: and held-out material is the span filter's (``withheld_message``), on every span; an item a
#: goal's exam pool reserves is read apart (:func:`item_passages`), since its reason is the exam one.
LIVE_ADMINISTRATION_REASONS: tuple[str, ...] = ("WITHHELD_COLD", "WITHHELD_RESERVED", "WITHHELD_PROBE")


def stored_plan_open_items(repository: Repository, *, clock: Clock | None = None) -> list[str]:
    """The ids of the items today's latest stored plan holds open: planned, and not yet done,
    skipped or displaced. The plan's own fold over its own rows (``daily_plan.records``, a pure
    module that imports nothing above it; the engine that writes them is not imported), so there
    is one meaning of "open". Raises when the plan can't be read: the caller fails closed."""

    from learnloop.daily_plan.records import assemble

    # The plan's day (``daily_plan.engine.local_date``): this machine's calendar date.
    day = (clock or SystemClock()).now().astimezone().date().isoformat()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        plans = plan_store.plans_for_date(connection, day) if plan_store.daily_plan_tables_present(connection) else []
        if not plans:
            return []
        blocks = plan_store.plan_blocks(connection, [plans[-1]["id"]])
        events = plan_store.block_events_for(connection, [block["id"] for block in blocks])
    (record,) = assemble(plans[-1:], blocks, events)
    return [str(item.practice_item_id) for item in record.items() if not item.resolved]


def item_passages(vault: Any, repository: Repository, *,
                  clock: Clock | None = None) -> tuple[frozenset[tuple[str, str]], frozenset[str]] | None:
    """RW5d P5 (spec §10b.2, G-SM29): the passages no prebuild may send or show now: every passage
    (``corpus.item_exclusions``: its exercise, solution or worked answer, whatever the relation) of
    an item under a live administration (:data:`LIVE_ADMINISTRATION_REASONS`), reserved for a goal's
    exam (an unreleased exam-pool row), or that the stored day plan holds open. Returns ``(spans, whole extractions)``, read fresh on every call; None
    when any of it could not be read (the caller fails closed).

    The one core of ``prefetch.item_protection``, of :func:`prefetch_plan_waits` (the Reader's
    reads and the pass) and of a prebuild's rich job's checks (follow-ups batch 6, Codex review F1).
    Codex verify V1: the stored plan is read here and is no caller's to add, so no path can leave
    it out; a learner's own press never comes here (``rich.run_rich_job``: prebuilds only)."""

    from learnloop import learner_protection as LP
    from learnloop.source_retrieval import corpus

    withheld = LP.withheld_items(vault, repository)
    if not withheld.available:
        return None
    live = {getattr(LP, name) for name in LIVE_ADMINISTRATION_REASONS}
    ids = {item_id for item_id, reason in withheld.reasons.items() if reason in live}
    try:
        # The exam reason also names every item made from exam material, whose spans the span filter
        # already catches; a reserved item from a clean book has no such span, so its exercise and
        # solution would pass both guards. The reservations themselves, not every exam item.
        ids |= {str(item_id) for item_id in repository.reserved_exam_pool_item_ids()}
    except Exception:  # noqa: BLE001 - reservations that can't be read may hold anything: fail closed
        _LOG.warning("figures: the exam pools' reservations could not be read", exc_info=True)
        return None
    try:
        ids |= set(stored_plan_open_items(repository, clock=clock))
    except Exception:  # noqa: BLE001 - a plan that can't be read may hold anything: fail closed
        _LOG.warning("figures: the stored plan's open items could not be read", exc_info=True)
        return None
    spans: set[tuple[str, str]] = set()
    whole: set[str] = set()
    for item_id in sorted(ids):
        item = vault.practice_items.get(item_id)
        if item is None:
            continue  # an item the vault can't read links to no passage it can name
        try:
            own = corpus.item_exclusions(repository, item)
        except Exception:  # noqa: BLE001 - an item whose passages can't be read: fail closed
            _LOG.warning("figures: the passages of item %s could not be read", item_id, exc_info=True)
            return None
        spans |= {(str(key[0]), str(key[1])) for key in own.spans}
        whole |= {str(extraction) for extraction in own.extractions}
    return frozenset(spans), frozenset(whole)


#: Why a prebuild's rich job is not asked again, or stops before its next request and before its
#: store (follow-ups batch 6, Codex review F1).
ITEM_PASSAGE_PROTECTED = ("Not built ahead of need: something this animation was to be told about belongs to a "
                          "question being checked or served now.")


def rich_base_keys(base: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Every ``(extraction_id, span_id)`` a rich job's saved context names: its passage, the
    paragraphs around it the author was sent, its region, its retrieved passages and its home
    (the spans ``rich._withheld`` checks)."""

    keys: list[tuple[str, str]] = []
    extraction_id = str(base.get("extraction_id") or "")
    if extraction_id:
        spans = [*list(base.get("span_ids") or ()), *list(base.get("input_span_ids") or ())]
        if (base.get("region") or {}).get("span_id"):
            spans.append(str(base["region"]["span_id"]))
        keys += [(extraction_id, str(span)) for span in spans]
    keys += [(str(key[0]), str(key[1])) for key in base.get("input_span_keys") or () if len(key) == 2 and key[0]]
    home = base.get("home") or {}
    if home.get("extraction_id") and home.get("span_id"):
        keys.append((str(home["extraction_id"]), str(home["span_id"])))
    return keys


def rich_base_item_protected(vault: Any, repository: Repository, base: Mapping[str, Any], *,
                             clock: Clock | None = None) -> str | None:
    """:data:`ITEM_PASSAGE_PROTECTED` when a rich job's saved context touches a passage
    :func:`item_passages` protects now, or the protection can't be read (fail closed); else None."""

    found = item_passages(vault, repository, clock=clock)
    if found is None:
        return ITEM_PASSAGE_PROTECTED
    spans, whole = found
    if any(key[0] in whole or key in spans for key in rich_base_keys(base)):
        return ITEM_PASSAGE_PROTECTED
    return None


__all__ = [
    "ATTEMPT_HOST_REFS",
    "INHERITED_LEARNER_INPUTS_KEY",
    "ITEM_PASSAGE_PROTECTED",
    "LEARNER_STATE_INPUTS_KEY",
    "LEARNER_STATE_PROTECTED",
    "LEARNER_STATE_UNRECORDED",
    "LIVE_ADMINISTRATION_REASONS",
    "RICH_INTENT_KEY",
    "figure_homes",
    "figure_withheld",
    "inherited_learner_inputs",
    "intent_learner_state_withheld",
    "item_passages",
    "keys_withheld",
    "learner_state_withheld",
    "rich_base_item_protected",
    "rich_base_keys",
    "row_withheld",
    "show_me_row",
    "stored_learner_state_withheld",
    "stored_plan_open_items",
    "withheld_message",
]
