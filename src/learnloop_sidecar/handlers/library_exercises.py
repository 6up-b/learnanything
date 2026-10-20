"""Reader workbench RW4b RPCs: exercises from my sources (spec_reader_workbench_v1 §7.4; UX §4.6).

The Reader's VIEW of the canonical-sources service's textbook-exercise
candidates (its S1), composed from that service's own functions and never
re-implemented here (G53):

* ``reader.exercise_candidates``: for the textbook exercises a
  ``find_practice`` proposal offered the Reader, whether each may still be
  shown, and what the service's exposure rule
  (``instructional/exposure.py:independent_check_eligibility``, §5.4 there)
  says about it. A candidate the rule marks carries the reason's label and is
  never offered as a check on your own (the Reader opens it as practice
  beside the book). Exam and held-out material is dropped (the one exam
  predicate), however old the proposal.
* ``reader.find_exercises``: the learner-initiated fallback when
  ``find_practice`` finds nothing ("find an exercise in my sources"):
  ``find_sources`` under the Reader's caller (``reading``, derived on the
  server, G19) over the question's learning objects, exercise blocks of the
  teaching scope only (never worked examples, whose solution sits beside
  them: the sources spec's D14), each widened to its exercise region (the
  service's ``exercise_regions``). Choosing one runs the Reader's existing
  ``import_exercises`` (``reader.import_exercise``'s request, G34). The shown
  regions are recorded as exposure after their own exposure was read.

**Never on the request path** (W12, as RW4a's library jobs): the exposure
rule's one judge (``worked_example_equivalence``) and the fallback's
retrieval (its query embedding and rewrite) may call a model, so each RPC
validates its request at once and then answers with a library job
(``reader.library_job`` reads it, ``reader.library_job_cancel`` cancels it).

"Use this one" on a proposal's exercise goes through the service's import
(``import_source_exercise``'s helper) inside the workbench (``workbench.open``
with ``source_exercise``). Nothing here writes an attempt, evidence, mastery,
certification, FSRS, scheduler state or a plan; the only writes are the
exposure rows of what the fallback showed. Desktop only (pinned in
tests/test_mobile_allowlist.py). Kill switches: ``library_exercises.enabled``
(the view; off, both RPCs refuse and the prompt contract has no
``library_exercises`` key) and ``library_exercises.fallback_enabled`` (the
fallback; the spec retires it once the service's candidates are live, so it
defaults off).
"""
from __future__ import annotations

from contextlib import closing
from typing import Any

from pydantic import Field

from learnloop.content.sources.exercise_statements import (
    ExerciseStatement,
    exercise_region_spans,
    read_exercise_statement,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
LIBRARY_EXERCISE_RPCS: tuple[str, ...] = (
    "reader.exercise_candidates",
    "reader.find_exercises",
)

#: The intent the Reader reads the exposure rule under. A check on your own is
#: the learner's unaided attempt with the book hidden; the rule's
#: ``discriminate`` reading is the one the spec's §7.4 names (its page read, its
#: solution or a revealed sibling seen, an equivalent worked example studied),
#: with a merely related worked example kept as a label, not an exclusion.
EXPOSURE_INTENT = "discriminate"

#: What the learner is told, one honest line per reason the rule gives (§5.4).
EXPOSURE_LABELS: tuple[tuple[str, str], ...] = (
    ("attempted", "you've already tried this one"),
    ("revealed", "you've seen this question's answer"),
    ("family_revealed", "you've seen the answer to a question like this one"),
    ("source_exposed", "you've recently seen this page or its solution"),
    ("seen_in_proposal", "you've already seen this question in an earlier suggestion"),
    ("equivalent_worked_example", "you studied a worked example almost identical to this one"),
    ("worked_example_unjudged",
     "LearnLoop couldn't yet check whether a worked example you studied gives this one away"),
)
RELATED_NOTE = "you read a worked example like this one"
#: Statement characters a fallback candidate carries (display bound, as the arm's).
FALLBACK_LIMIT = 5


def exercises_enabled(vault: Any) -> bool:
    """The candidate view exists: its own switch inside RW4a's library answer."""

    from learnloop.source_retrieval import library_ask as LA

    return LA.library_ask_enabled(vault) and bool(vault.config.library_exercises.enabled)


def fallback_enabled(vault: Any) -> bool:
    return exercises_enabled(vault) and bool(vault.config.library_exercises.fallback_enabled)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW4b (absent while off)."""

    if not exercises_enabled(vault):
        return {}
    return {"library_exercises": {"fallback": fallback_enabled(vault)}}


def _require(ctx: SidecarContext, *, fallback: bool = False):
    vault, repository = ctx.require_vault()
    if not exercises_enabled(vault):
        raise SidecarError("library_exercises_disabled",
                           "Exercises from your sources are switched off (library_exercises.enabled, or the "
                           "library answer they live in).")
    if fallback and not fallback_enabled(vault):
        raise SidecarError("library_exercises_disabled",
                           "Finding exercises in your sources is switched off (library_exercises.fallback_enabled).")
    return vault, repository


def exposure_view(vault: Any, repository: Any, candidate: dict[str, Any], *,
                  proposal_id: str | None, own_listing_event_ids: frozenset[str] = frozenset()) -> dict[str, Any]:
    """The sources service's exposure rule for one exercise, as the Reader shows it.

    ``own_listing_event_ids``: the exposure rows the fallback's own listing of
    this exercise wrote (read back at the pick). They count against it no more
    than a proposal's own impression does (``picked_proposal_id``): the list
    read its exposure before showing it, and showing it is what offered it."""

    from learnloop.instructional.exposure import EXPOSURE_RULE_VERSION, independent_check_eligibility

    verdict = independent_check_eligibility(vault, repository, candidate, intent=EXPOSURE_INTENT,
                                            picked_proposal_id=proposal_id)
    reasons = [str(reason) for reason in verdict.get("reasons") or ()]
    shown = {str(event) for event in (verdict.get("inputs") or {}).get("exposure_event_ids") or ()}
    if "source_exposed" in reasons and shown and shown <= own_listing_event_ids:
        reasons.remove("source_exposed")
    label = next((text for reason, text in EXPOSURE_LABELS if reason in reasons), None)
    if reasons and label is None:
        label = "you've seen this question recently"
    return {
        "exposed": bool(reasons),
        "reasons": reasons,
        "label": label,
        "note": RELATED_NOTE if verdict.get("label") == RELATED_NOTE else None,
        # How "use this one" opens it: an exposed exercise is practice beside
        # the book, never a check on your own (§7.4).
        "offered_as": "practice" if reasons else "check_on_your_own",
        "exposure_rule_version": verdict.get("exposure_rule_version") or EXPOSURE_RULE_VERSION,
    }


def _proposal_lo_ids(found: dict[str, Any]) -> list[str]:
    """The request's learning objects: they scope the rule's studied worked examples."""

    return [str(lo) for lo in ((found.get("constraints") or {}).get("learning_object_ids") or ())]


def _proposal_candidate(entry: dict[str, Any], span_ids: list[str], lo_ids: list[str],
                        read: ExerciseStatement) -> dict[str, Any]:
    """A proposal's exercise as the exposure rule reads it: the same input at
    display, at the pick and at admission, so the rule's one judge answers a
    second reading from its ledger. Its statement is the one reader's (fix
    round 4, R4), bounded as the arm bounds a proposal's."""

    return {"extraction_id": str(entry.get("extraction_id")), "span_ids": list(span_ids), "key": entry.get("key"),
            "statement": _preview(read.text), "learning_object_ids": list(lo_ids)}


def _preview(text: str) -> str:
    """A candidate's statement as a list shows it (the arm's display bound)."""

    from learnloop.instructional.exercises import STATEMENT_CHARS

    return text if len(text) <= STATEMENT_CHARS else text[:STATEMENT_CHARS - 1] + "…"


# -- the one reader of an exercise's statement (fix rounds 4 and 5, R4/R2) -------------------------------
# It lives in ``learnloop.content.sources.exercise_statements`` (shared with
# S1's import worker and its selection); RW4b reads statements only through it.

#: The verdict when the rule could not be read at the pick: practice beside the
#: book (fail closed), never a check on your own.
UNCHECKED_EXPOSURE_LABEL = "LearnLoop couldn't check whether you've seen this one"


def _own_listing_events(repository: Any, event_ids: list[str], extraction_id: str, span_ids: list[str]) -> frozenset[str]:
    """Of the ids a fallback candidate came back with, those that really are its
    own listing's exposure rows (``library_exercises``, its spans): anything
    else the client names is ignored."""

    from learnloop.db.connection import connect

    ids = [str(event) for event in event_ids][:80]
    if not ids or not span_ids:
        return frozenset()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            f"SELECT id FROM source_exposure_events WHERE id IN ({','.join('?' for _ in ids)}) "
            f"AND context = 'library' AND entity_type = 'library_exercises' AND extraction_id = ? "
            f"AND span_id IN ({','.join('?' for _ in span_ids)})",
            (*ids, extraction_id, *[str(span) for span in span_ids])).fetchall()
    return frozenset(str(row[0]) for row in rows)


def pick_exposure(vault: Any, repository: Any, pick: dict[str, Any], *,
                  practice_item_id: str | None = None) -> dict[str, Any] | None:
    """The exposure rule read again for a picked exercise (Codex review F3): at
    the pick, which decides how it opens, and at admission, which the problem
    then shows. The same candidate the list read (the judge answers from its
    ledger unless something new was studied since). None when the exercise is
    not one the proposal proposed (its import refuses it anyway); a rule that
    cannot be read fails closed, as practice beside the book.

    ``practice_item_id`` (fix round 5, R3; Codex final verify F11): at
    admission, the item the import wrote and bound. The rule then reads the
    item too (its attempts, its own and its family's revealed answers, its
    impressions) as well as the source spans, with the originating proposal's
    own impression still exempt, so a fresh exercise attached to a family
    whose answer was revealed is practice only."""

    from learnloop.db.connection import connect
    from learnloop.db.stores.practice_index import proposal as stored_proposal
    from learnloop.db.stores.source_service import exercise_key
    from learnloop.instructional.exposure import EXPOSURE_RULE_VERSION
    from learnloop.instructional.practice import proposed_exercise

    extraction_id = str(pick.get("extraction_id") or "")
    span_ids = [str(span) for span in pick.get("span_ids") or ()]
    proposal_id = pick.get("proposal_id")
    try:
        if proposal_id:
            try:
                entry = proposed_exercise(repository, str(proposal_id), extraction_id, span_ids)
            except ValueError:
                return None
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                found = stored_proposal(connection, str(proposal_id)) or {}
            spans = [str(span) for span in entry.get("span_ids") or span_ids]
            proposed = read_exercise_statement(vault, repository, str(entry.get("extraction_id")), spans)
            if proposed is None:
                raise LookupError("withheld or unreadable")  # fail closed, below
            candidate = _proposal_candidate(entry, spans, _proposal_lo_ids(found), proposed)
            if practice_item_id:
                candidate["practice_item_id"] = practice_item_id
            return exposure_view(vault, repository, candidate, proposal_id=str(proposal_id))
        read = read_exercise_statement(vault, repository, extraction_id, span_ids)
        if read is None:
            return None
        candidate = {"key": exercise_key(extraction_id, span_ids), "extraction_id": extraction_id,
                     "span_ids": span_ids, "statement": _preview(read.text),
                     "learning_object_ids": [str(lo) for lo in pick.get("learning_object_ids") or ()]}
        if practice_item_id:
            candidate["practice_item_id"] = practice_item_id
        own = _own_listing_events(repository, list(pick.get("shown_event_ids") or ()), extraction_id, span_ids)
        return exposure_view(vault, repository, candidate, proposal_id=None, own_listing_event_ids=own)
    except Exception:  # noqa: BLE001 - an unreadable rule never opens the book-hidden check
        return {"exposed": True, "reasons": ["exposure_unchecked"], "label": UNCHECKED_EXPOSURE_LABEL, "note": None,
                "offered_as": "practice", "exposure_rule_version": EXPOSURE_RULE_VERSION}


def pick_entry(exposure: dict[str, Any] | None, requested: str) -> str:
    """How a picked exercise opens, from the server's verdict: exposed, as
    practice beside the book (``work_through``); unexposed, as your own
    attempt with the book hidden (``practice_this``). Without a verdict (an
    exercise the import will refuse) the request's entry stands."""

    if exposure is None:
        return requested
    return "work_through" if exposure.get("exposed") else "practice_this"


# -- the view of a proposal's textbook exercises -------------------------------------------------


class CandidateKey(ParamsModel):
    extraction_id: str
    span_ids: list[str] = Field(min_length=1, max_length=40)


class ExerciseCandidatesInput(ParamsModel):
    proposal_id: str
    keys: list[CandidateKey] = Field(default_factory=list, max_length=20)


def _start_job(ctx: SidecarContext, kind: str, work: Any) -> dict[str, Any]:
    """RW4a's library job runner: the work runs off the request path, on its own repository."""

    from learnloop_sidecar.handlers.library_ask import _job_payload, _jobs

    return _job_payload(_jobs(ctx).start(ctx, kind, None, work))


@method("reader.exercise_candidates", ExerciseCandidatesInput)
def reader_exercise_candidates(ctx: SidecarContext, params: ExerciseCandidatesInput) -> dict[str, Any]:
    """The proposal's textbook exercises the Reader may show, each with its
    exposure (the sources service's rule) and how "use this one" offers it.

    A key the proposal did not propose is refused at once; one that became
    exam or held-out material since is left out (``withheld`` counts it).
    Read-only, apart from the exposure rule's own judge verdicts (its
    ledger). Answers with a library job."""

    from learnloop.db.connection import connect
    from learnloop.db.stores.practice_index import proposal as stored_proposal
    from learnloop.instructional.practice import proposed_exercise

    vault, repository = _require(ctx)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        found = stored_proposal(connection, params.proposal_id)
    if found is None:
        raise SidecarError("validation_error", "Unknown proposal")
    lo_ids = _proposal_lo_ids(found)
    entries: list[tuple[dict[str, Any], list[str]]] = []
    for key in params.keys:
        try:
            entry = proposed_exercise(repository, params.proposal_id, key.extraction_id, key.span_ids)
        except ValueError as exc:
            raise SidecarError("validation_error", str(exc)) from exc
        entries.append((entry, [str(span) for span in entry.get("span_ids") or key.span_ids]))
    proposal_id = params.proposal_id

    def work(worker_repo: Any) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        withheld = 0
        for entry, span_ids in entries:
            extraction_id = str(entry.get("extraction_id"))
            # Read through the one reader (R4): a region held out now, or a
            # predicate that cannot be read, leaves the candidate out.
            read = read_exercise_statement(vault, worker_repo, extraction_id, span_ids)
            if read is None:
                withheld += 1
                continue
            candidate = _proposal_candidate(entry, span_ids, lo_ids, read)
            candidates.append({
                "key": entry.get("key"), "extraction_id": extraction_id, "span_ids": span_ids,
                "source_id": entry.get("source_id"), "revision_id": entry.get("revision_id"),
                "exposure": exposure_view(vault, worker_repo, candidate, proposal_id=proposal_id),
            })
        return {"proposal_id": proposal_id, "candidates": candidates, "withheld": withheld}

    return _start_job(ctx, "exercise_candidates", work)


# -- the fallback: find an exercise in my sources ------------------------------------------------


class FindExercisesInput(ParamsModel):
    query: str = Field(min_length=1, max_length=4000)
    learning_object_ids: list[str] = Field(default_factory=list, max_length=40)
    #: The source the Reader has open (the caller's reference; the policy is derived).
    extraction_id: str | None = None
    limit: int = Field(default=FALLBACK_LIMIT, ge=1, le=10)


@method("reader.find_exercises", FindExercisesInput)
def reader_find_exercises(ctx: SidecarContext, params: FindExercisesInput) -> dict[str, Any]:
    """"Find an exercise in my sources" (§7.4's fallback): exercise regions of
    the teaching scope over the question's learning objects, each with the
    request "use this one" sends to the Reader's own import. Answers with a
    library job."""

    from learnloop.instructional.sources import propose_sources
    from learnloop.source_retrieval.policy import PolicyRefused
    from learnloop_sidecar.handlers.library_ask import reader_caller

    vault, repository = _require(ctx, fallback=True)
    caller = reader_caller(vault, repository, extraction_id=params.extraction_id)
    lo_ids = [lo for lo in dict.fromkeys(params.learning_object_ids) if lo in vault.learning_objects]
    query, limit = params.query, params.limit

    def work(worker_repo: Any) -> dict[str, Any]:
        try:
            hits = propose_sources(
                vault, worker_repo, query, caller=caller, intent="explain", scope="teaching",
                learning_object_ids=lo_ids, roles=["exercise"], verify=False, limit=min(40, limit * 4),
            )
        except PolicyRefused as exc:
            raise SidecarError(exc.code, str(exc)) from exc
        return _fallback_candidates(vault, worker_repo, hits, lo_ids, limit)

    return _start_job(ctx, "find_exercises", work)


def _fallback_candidates(vault: Any, repository: Any, hits: Any, lo_ids: list[str], limit: int) -> dict[str, Any]:
    from learnloop.content.authoring.source_exercise_import import selection_for_region
    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import exercise_key
    from learnloop.instructional.exercises import exercise_label, imported_span_keys
    from learnloop.instructional.interventions import record_shown_spans

    imported = imported_span_keys(vault, repository)
    candidates: list[dict[str, Any]] = []
    dropped = {"no_region": 0, "already_imported": 0, "withheld": 0, "duplicate": 0}
    seen: set[tuple[str, tuple[str, ...]]] = set()
    regions: dict[str, list[Any]] = {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for hit in hits.hits:
            extraction_id, span_id = str(hit["extraction_id"]), str(hit["span_id"])
            region_spans = exercise_region_spans(connection, extraction_id, span_id, regions)
            if region_spans is None:
                dropped["no_region"] += 1
                continue
            if (extraction_id, region_spans) in seen:
                dropped["duplicate"] += 1
                continue
            seen.add((extraction_id, region_spans))
            span_ids = list(region_spans)
            if any((extraction_id, span) in imported for span in span_ids):
                dropped["already_imported"] += 1
                continue
            read = read_exercise_statement(vault, repository, extraction_id, span_ids)
            if read is None:
                dropped["withheld"] += 1
                continue
            statement = _preview(read.text)
            key = exercise_key(extraction_id, span_ids)
            candidates.append({
                "key": key, "extraction_id": extraction_id, "span_ids": span_ids,
                "source_id": hit.get("source_id"), "revision_id": hit.get("revision_id"),
                "source_title": hit.get("source_title"), "page": hit.get("page"),
                "label": exercise_label(read.text, hit.get("page")), "statement": statement,
                "learning_object_ids": lo_ids,
            })
            if len(candidates) >= limit:
                break
    for candidate in candidates:
        # The exposure the learner had BEFORE this list showed the statement.
        candidate["exposure"] = exposure_view(vault, repository, candidate, proposal_id=None)
        candidate["import_request"] = {
            "extraction_id": candidate["extraction_id"], "source_id": candidate["source_id"],
            "revision_id": candidate["revision_id"],
            "raw_selection": selection_for_region(repository, candidate["extraction_id"], candidate["span_ids"],
                                                  vault=vault),
            **({"learning_object_id": lo_ids[0]} if len(lo_ids) == 1 else {}),
        }
        candidate.pop("learning_object_ids", None)
    # Reading is never blocked, and what it showed is recorded (the sources
    # spec's §5.1 `reading`): the exposure rule then reads these rows.
    shown = [f"{candidate['extraction_id']}:{span}" for candidate in candidates for span in candidate["span_ids"]]
    recorded: dict[str, str] = {}
    if shown:
        ids = record_shown_spans(repository, shown, context="library", entity_type="library_exercises",
                                 entity_id=str(hits.manifest.get("query_hash") or ""))
        recorded = dict(zip(dict.fromkeys(shown), ids))
    for candidate in candidates:
        # What "use this one" sends back (workbench.open's ``exercise_pick``):
        # this listing's own exposure rows, which never count against the pick
        # (the server checks they are), and the learning objects it was read for.
        candidate["pick"] = {
            "learning_object_ids": lo_ids,
            "shown_event_ids": [recorded[key] for key in
                                (f"{candidate['extraction_id']}:{span}" for span in candidate["span_ids"])
                                if key in recorded],
        }
    return {
        "status": "ok" if candidates else "none_found", "policy": hits.policy, "candidates": candidates,
        "dropped": dropped, "manifest": hits.manifest,
    }


__all__ = [
    "EXPOSURE_INTENT",
    "EXPOSURE_LABELS",
    "LIBRARY_EXERCISE_RPCS",
    "exercises_enabled",
    "exposure_view",
    "fallback_enabled",
    "ExerciseStatement",
    "exercise_region_spans",
    "pick_entry",
    "pick_exposure",
    "prompt_contract_fields",
    "read_exercise_statement",
]
