"""Reader workbench RW6b part 1: cold follow-ups, the owner's "short unfamiliar
problem" (spec_reader_workbench_v1 §9.3-§9.6; UX §4.8-§4.9, S15; gates G26,
G27, G35, G49).

RW6b builds no valuation of its own (W13). For one reader session it

1. **lists the open questions** (:func:`open_questions`) from RW6a's typed
   summary: the claims needing an independent check (retention: "holds
   unaided" or not), the rival explanations still open on the session's
   learning objects (open probe episodes, the facets' hypothesis marginals,
   gaps learner-text gaps named from the session), and, with
   ``followups.formative_questions_enabled``, the facets the session's
   formative records touched. Records change which questions are asked,
   never a prior's number (W1, tier 2);
2. **asks** ``find_practice`` for each, with the exact filters
   (``unattempted_only``, ``exclude_family_ids`` = the families of every item
   whose answer the session revealed, ``exclude_revealed_families``), the
   value intent (``retention`` or ``discriminate``) and
   ``system_initiated=True``. Inside it the sources spec's relevance judge
   (``practice_rerank``: the only model call, routed and capped as every
   caller's), its exposure rule (``independent_check_eligibility``) and
   ``valuation.value_candidates`` (``robust_composition`` /
   ``evsi.rank_feasible``, greedy conditional selection, the stop rule, no
   count cap) run exactly as they do for any caller. A system-initiated
   check is created only from a licensing regime (``pinned_channel``; the
   sources spec's §20 request): an ``item_point`` value can be shown, never
   dated;
3. **dates each chosen check by its purpose** (:func:`date_for`): a
   discriminating check for the next day's plan; a retention check at the
   practiced item's effective due (DL2 §5.3), or, with no FSRS state yet,
   the scheduler's own first interval for that attempt's rating. Never
   later than ``followups.max_wait_days`` (keep: a time cap) and never today
   (DL1 never grows today's plan);
4. **schedules each as content**: a ``test_me_later`` commitment
   (``one_check_pending``) on its item, ``due_hint`` = the date, provenance
   ``{"via": "reader_followup", "summary_id", "purpose", "novelty",
   "valuation_ref", "inquiry_root_event_ids", "anchor_span_ids", ...}``. DL2's
   "Check once" serves it (cold, its independence re-checked at serve,
   restoration after);
5. **stores the receipt** on the session's ``reader_session_digests`` row.

Before each day's plan (:func:`revalue_pending`), the pending follow-ups are
re-valued against the current state with the same valuation and no model
call; one whose question was answered since (an unaided success on the
claim, the rivals' episode closed) or that no longer clears the stop is
retired with its reason (``commitments.retire(detail=...)``). Undo (with an
optional reason, a ``learner_card`` verdict) and undo all retire the
commitments too. Interaction with mvp-0.38: a claim whose repair cold retry
is pending gets no retention follow-up as well.

A resumed or re-asked search never retires a live check (Codex re-review
round 3): the question's live checks are passed as ``already_chosen``, so the
greedy conditional selection starts from them and adds a check only if it
still clears the stop given them (§9.3 item 3). Rescheduling reads the live
checks, not every ref ever chosen: an item whose check was retired or
satisfied may be scheduled again as a fresh generation (one the learner undid
stays out). A check several questions select is created once, records every
licensing question, and stays live while any of them needs it.

**The successor** ``mvp-0.39`` (§9.3 "Why no successor", whose fallback
the Codex review invoked, F4): automatic dated requests change what the
maintain lane holds and serves, so planning and re-valuation run only at the
tag or later with ``followups.enabled`` on (:func:`followups_enabled`); off
or below it, the predecessor's plan exactly. Nothing here writes evidence.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
import json
from typing import Any, Iterator

from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendLimitExceeded, spend_envelopes
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.curriculum import commitments as C
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import reader_digests as RDG
from learnloop.db.stores.judgments import append_judgment
from learnloop.db.stores.practice_index import judgments_by_ids
from learnloop.instructional.valuation import (
    SCALE_LABEL,
    VALUATION_VERSION,
    recent_assisted_success,
)
from learnloop.reader import reader_sessions as RS
from learnloop.reader import recap as RC
from learnloop.reader.reader_progression import learning_objects_for_span
from learnloop.vault.models import LoadedVault

FOLLOWUPS_VERSION = "rw6b-followups-v1"
VIA = "reader_followup"
#: The followups envelope's name in the sources service's spend ledger.
ENVELOPE = "followups.max_daily_cost_usd"
OWNER_KIND = "reader_followups"
#: The ``judgment_ledger`` task an undo's verdict is filed under.
UNDO_TASK = "reader_followup_undo"
#: Learner text kept with an undo verdict (calibration data, never learner-text gaps).
UNDO_REASON_CHARS = 500
#: D36: the card shows the next three by date, then "later ▸" (a display limit).
NEXT_SHOWN = 3

PURPOSE_DISCRIMINATING = "discriminating"
PURPOSE_RETENTION = "retention"
INTENT_BY_PURPOSE = {PURPOSE_DISCRIMINATING: "discriminate", PURPOSE_RETENTION: "retention"}

NOVELTY_SAME_SURFACE = "same_surface"
NOVELTY_NEW_PROBLEM = "new_problem"
NOVELTY_LABELS = {NOVELTY_SAME_SURFACE: "same idea, new numbers", NOVELTY_NEW_PROBLEM: "a new problem"}

#: Retirement reasons (commitment event detail ``reason``). Only an answered
#: question reads as "no longer needed" on RW6a's "Since last time".
RETIRE_ANSWERED = "no_longer_needed"
RETIRE_BELOW_STOP = "below_stop"
RETIRE_UNDONE = "undone"
#: Exposed since its valuation (the full exposure rule at serve; Codex review
#: F1): no longer a check on your own; the question is asked again.
RETIRE_EXPOSED = "exposed_since_valuation"
#: A repair cold retry now measures the same claim (Codex review F11).
RETIRE_REPAIR_OWNS = "repair_retry_owns"
#: Re-valuation keeps a check whose only exposure is a studied worked example
#: nobody judged yet; the background job asks the judge (Codex review F5).
KEPT_REFRESH = "exposure_refresh_needed"
#: How a question was answered since (re-valuation): an unaided success on
#: the claim, or every probe episode it named closed.
ANSWERED_SOLVED = "solved_on_your_own"
ANSWERED_RIVALS = "rivals_resolved"

#: Verdicts whose checks are created (decision-value §6.5's translation).
CHECK_VERDICTS = ("act", "measure")


class FollowupError(ValueError):
    """A refused follow-up request (nothing was written)."""


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def _config(vault: Any) -> Any:
    return getattr(vault.config, "followups", None)


def followups_enabled(vault: Any) -> bool:
    """Follow-ups are live: the vault is at the successor
    (``READER_FOLLOWUPS_VERSIONS``, mvp-0.39; Codex review F4) and
    ``followups.enabled`` is on (default). Off, or below the tag, nothing is
    planned or re-valued: the predecessor's plan exactly."""

    from learnloop.algorithm_versions import READER_FOLLOWUPS_VERSIONS

    version = getattr(getattr(vault.config, "algorithms", None), "algorithm_version", None)
    return version in READER_FOLLOWUPS_VERSIONS and bool(getattr(_config(vault), "enabled", True))


def formative_questions_enabled(vault: Any) -> bool:
    return bool(getattr(_config(vault), "formative_questions_enabled", True))


def max_wait_days(vault: Any) -> int:
    return int(getattr(_config(vault), "max_wait_days", 14))


# ---------------------------------------------------------------------------
# 1. The open questions (§9.3 item 1): pure reads
# ---------------------------------------------------------------------------

@dataclass
class Question:
    """One open question a later independent attempt could answer."""

    key: str
    purpose: str
    learning_object_ids: list[str]
    facet_ids: list[str] = field(default_factory=list)
    target_hypotheses: list[dict[str, str]] = field(default_factory=list)
    raised_by: list[dict[str, Any]] = field(default_factory=list)
    #: The session's assisted attempts behind a retention question (dating, novelty).
    attempt_ids: list[str] = field(default_factory=list)
    #: A repair decision the rivals bear on (Codex review F7):
    #: ``{"hypothesis_set_id", "action_by_slot"}``, passed to the valuation.
    pending_decision: dict[str, Any] | None = None

    @property
    def intent(self) -> str:
        return INTENT_BY_PURPOSE[self.purpose]

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "intent": self.intent}


def _item_lo(vault: Any, item_id: str | None) -> str | None:
    item = vault.practice_items.get(str(item_id or ""))
    return item.learning_object_id if item is not None else None


def _attempt_rows(repository: Repository, attempt_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    wanted = sorted({str(a) for a in attempt_ids if a})
    if not wanted:
        return {}
    marks = ",".join("?" for _ in wanted)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(f"SELECT * FROM practice_attempts WHERE id IN ({marks})", wanted).fetchall()
    return {str(row["id"]): dict(row) for row in rows}


def _facet_los(vault: Any, facet_id: str) -> list[str]:
    from learnloop.practice_index.catalog import item_facets

    canonical = vault.canonical_facet_id(facet_id)
    return sorted({item.learning_object_id for item in vault.practice_items.values()
                   if canonical in item_facets(vault, item)})


def pending_cold_retry(vault: Any, repository: Repository, *, facet_id: str, attempt_ids: Sequence[str],
                       learning_object_ids: Sequence[str], now: datetime) -> dict[str, Any] | None:
    """mvp-0.38's interaction: a repair ``cold_retry`` still pending (or served)
    that owns the claim: the item it measures assesses the claim's facet, on
    one of the claim's attempts or on the claim's learning objects (Codex
    review F11: ownership is by the assessed facets, never the source attempt
    alone). Its cold measurement answers the claim; a retention follow-up would
    ask it twice. The one rule creation, re-valuation and serving use
    (``scheduling.intent.followup_gate.owning_retry``)."""

    from learnloop.scheduling.intent.followup_gate import open_cold_retries, owning_retry

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = open_cold_retries(connection, now=now)
    found = owning_retry(vault, rows, facet_id=facet_id, attempt_ids=attempt_ids,
                         learning_object_ids=learning_object_ids)
    return dict(found) if found is not None else None


def open_questions(vault: LoadedVault, repository: Repository, summary: Mapping[str, Any], *,
                   now: datetime) -> tuple[list[Question], list[dict[str, Any]]]:
    """The session's open questions and the notes on what was not asked (typed)."""

    questions: dict[str, Question] = {}
    notes: list[dict[str, Any]] = []

    def question(key: str, purpose: str, los: Sequence[str], facets: Sequence[str] = ()) -> Question:
        found = questions.get(key)
        if found is None:
            found = questions[key] = Question(key=key, purpose=purpose, learning_object_ids=sorted(set(los)),
                                              facet_ids=list(dict.fromkeys(facets)))
        return found

    # Claims needing an independent check: assisted-only work on a facet.
    claims = list(summary.get("claims_needing_independent_check") or [])
    attempts = _attempt_rows(repository, [a for claim in claims for a in claim.get("attempt_ids") or []])
    for claim in claims:
        facet = vault.canonical_facet_id(str(claim["facet_id"]))
        attempt_ids = [str(a) for a in claim.get("attempt_ids") or []]
        los = sorted({lo for a in attempt_ids if (lo := _item_lo(vault, (attempts.get(a) or {}).get("practice_item_id")))})
        los = los or _facet_los(vault, facet)
        retry = pending_cold_retry(vault, repository, facet_id=facet, attempt_ids=attempt_ids,
                                   learning_object_ids=los, now=now)
        if retry is not None:
            notes.append({"question": f"retention:{facet}", "reason": "cold_retry_pending",
                          "followup_task_id": retry["id"]})
            continue
        q = question(f"retention:{facet}", PURPOSE_RETENTION, los, [facet])
        q.raised_by.append({"kind": "claim", "facet_id": facet, "basis": claim.get("basis"),
                            "attempt_ids": attempt_ids})
        q.attempt_ids = sorted(set(q.attempt_ids) | set(attempt_ids))

    # Rival explanations still open on the session's learning objects.
    session_los = set(summary.get("learning_objects_touched") or [])
    for line in summary.get("workbench") or []:
        if (lo := _item_lo(vault, line.get("practice_item_id"))) is not None:
            session_los.add(lo)
    episodes = repository.open_probe_episodes()
    for lo_id in sorted(session_los):
        episode = episodes.get(lo_id)
        if episode is not None:
            q = question(f"discriminate:{lo_id}", PURPOSE_DISCRIMINATING, [lo_id])
            ref = {"kind": "episode_label", "id": str(episode.id)}
            if ref not in q.target_hypotheses:
                q.target_hypotheses.append(ref)
            q.raised_by.append({"kind": "rival", "source": "probe_episode", "episode_id": str(episode.id)})
    for facet in summary.get("facets_touched") or []:
        canonical = vault.canonical_facet_id(str(facet))
        for lo_id in sorted(set(_facet_los(vault, canonical)) & session_los):
            state = repository.facet_uncertainty_state(lo_id, canonical)
            if state is None or not state.hypothesis_marginal:
                continue
            q = question(f"discriminate:{lo_id}", PURPOSE_DISCRIMINATING, [lo_id])
            ref = {"kind": "facet_state", "id": canonical}
            if ref not in q.target_hypotheses:
                q.target_hypotheses.append(ref)
                q.raised_by.append({"kind": "rival", "source": "facet_marginal", "facet_id": canonical})
    for gap in summary.get("gaps_named") or []:
        gap_id = str(gap.get("gap_id") or "")
        target_lo = gap.get("target_id") if gap.get("target_kind") == "learning_object" else None
        los = [target_lo] if target_lo in vault.learning_objects else sorted(session_los)
        if not gap_id or not los:
            continue
        q = question(f"discriminate:{los[0]}", PURPOSE_DISCRIMINATING, los)
        ref = {"kind": "named_gap", "id": gap_id}
        if ref not in q.target_hypotheses:
            q.target_hypotheses.append(ref)
            q.raised_by.append({"kind": "rival", "source": "named_gap", "gap_id": gap_id})

    # The session's formative records (restored RS3): each adds the facets it
    # touched as a question, and a gap named from it as a rival. Never a prior.
    # Open causal factors with competing repairs on the session's attempts
    # (Codex review F7): each locked hypothesis set is its own decision
    # question (spaces never merged), its pending decision passed through.
    from learnloop.instructional import needs as N

    session_attempts = list(dict.fromkeys(
        [str(line.get("attempt_id")) for line in summary.get("workbench") or [] if line.get("attempt_id")]
        + [str(a) for claim in claims for a in claim.get("attempt_ids") or []]))
    decision_attempts = _attempt_rows(repository, session_attempts)
    for attempt_id in session_attempts:
        decision = N.pending_causal_decision(vault, repository, {"attempt_id": attempt_id})
        if not decision:
            continue
        if decision.get("unavailable") or not decision.get("hypothesis_set_id"):
            notes.append({"question": f"decide:attempt:{attempt_id}", "reason": decision.get("unavailable")
                          or "no_locked_hypothesis_set"})
            continue
        hset = str(decision["hypothesis_set_id"])
        lo = _item_lo(vault, (decision_attempts.get(attempt_id) or {}).get("practice_item_id"))
        q = question(f"decide:{hset}", PURPOSE_DISCRIMINATING, [lo] if lo else sorted(session_los))
        ref = {"kind": "causal_hypothesis", "id": hset}
        if ref not in q.target_hypotheses:
            q.target_hypotheses.append(ref)
        q.pending_decision = {"hypothesis_set_id": hset, "action_by_slot": dict(decision.get("action_by_slot") or {})}
        q.raised_by.append({"kind": "rival", "source": "causal_factor", "attempt_id": attempt_id,
                            "hypothesis_set_id": hset})

    if formative_questions_enabled(vault):
        for record in summary.get("observations") or []:
            raised = {"kind": "formative", "record_kind": record.get("kind"),
                      "source_event_ids": list(record.get("source_event_ids") or []),
                      "span_ids": list(record.get("span_ids") or [])}
            facets = [vault.canonical_facet_id(str(f)) for f in record.get("facet_candidates") or []
                      if vault.canonical_facet_id(str(f)) in vault.evidence_facets]
            for facet in facets:
                los = _facet_los(vault, facet)
                if not los:
                    continue
                key = f"retention:{facet}"
                if key not in questions:
                    if pending_cold_retry(vault, repository, facet_id=facet, attempt_ids=(),
                                          learning_object_ids=los, now=now) is not None:
                        notes.append({"question": key, "reason": "cold_retry_pending"})
                        continue
                question(key, PURPOSE_RETENTION, los, [facet]).raised_by.append(raised)
            for gap_id in record.get("hypotheses") or []:
                lo_targets = sorted(session_los) or sorted({lo for f in facets for lo in _facet_los(vault, f)})
                if not lo_targets:
                    continue
                q = question(f"discriminate:{lo_targets[0]}", PURPOSE_DISCRIMINATING, lo_targets)
                ref = {"kind": "named_gap", "id": str(gap_id)}
                if ref not in q.target_hypotheses:
                    q.target_hypotheses.append(ref)
                q.raised_by.append(raised)
    # A retention question only formative records raised names itself (a
    # ``retention`` ref): the valuation poses it on an item anchor with the
    # active predictor's prior (Codex review F9), never a record's number.
    for q in questions.values():
        if q.purpose == PURPOSE_RETENTION and not any(r.get("kind") == "claim" for r in q.raised_by):
            for facet in q.facet_ids:
                ref = {"kind": "retention", "id": facet}
                if ref not in q.target_hypotheses:
                    q.target_hypotheses.append(ref)
    return list(questions.values()), notes


# ---------------------------------------------------------------------------
# 2. Candidates (§9.3 item 2): the exact filters, the injected search
# ---------------------------------------------------------------------------

def revealed_families(vault: Any, repository: Repository, session: RS.ReaderSession) -> list[str]:
    """The families of every item whose answer the session revealed (the reveal ledger)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT DISTINCT practice_item_id, created_at FROM reveal_events ORDER BY created_at").fetchall()
    families: list[str] = []
    for row in rows:
        if not session.contains(row["created_at"]):
            continue
        item = vault.practice_items.get(str(row["practice_item_id"]))
        if item is not None and item.family_id and item.family_id not in families:
            families.append(item.family_id)
    return sorted(families)


def constraints_for(question: Question, *, exclude_family_ids: Sequence[str],
                    exclude_item_ids: Sequence[str] = ()) -> dict[str, Any]:
    """The ``PracticeConstraints`` mapping for one question (§9.3 item 2,
    exactly), plus ``exclude_item_ids``: the items an explicit learner choice
    decides (Codex review F2), never valued as an automatic check."""

    return {
        "intent": question.intent,
        "learning_object_ids": list(question.learning_object_ids),
        "facet_ids": list(question.facet_ids),
        "target_hypotheses": [dict(ref) for ref in question.target_hypotheses],
        "unattempted_only": True,
        "exclude_family_ids": list(exclude_family_ids),
        "exclude_revealed_families": True,
        "exclude_item_ids": sorted(set(exclude_item_ids)),
    }


def committed_items(vault: Any, connection: Any, *, own: Iterable[str] = ()) -> set[str]:
    """Items some commitment other than ``own`` decides (DL2 §5.3's resolution):
    a learner's Pause, Master, Learn, Keep, reference-only or their own
    "Check once", or another session's follow-up. An automatic follow-up never
    lands there, so it never overrides an explicit choice (Codex review F2)."""

    from learnloop.scheduling.intent.resolution import Resolution, load_snapshots

    mine = set(own)
    covering = [snapshot for snapshot in load_snapshots(connection)
                if not snapshot.retired and snapshot.covers_items and snapshot.id not in mine]
    if not covering:
        return set()
    targets = dict(getattr(getattr(vault.config, "intent", None), "recall_targets", None) or {})
    resolution = Resolution(covering, targets)
    return {item.id for item in vault.practice_items.values()
            if not resolution.for_item(item.id, item.learning_object_id).uncommitted}


def query_for(vault: Any, question: Question) -> str:
    parts = [vault.learning_objects[lo].title for lo in question.learning_object_ids if lo in vault.learning_objects]
    for facet in question.facet_ids:
        record = vault.evidence_facets.get(facet)
        parts.append(str(getattr(record, "title", None) or facet))
    return " · ".join(dict.fromkeys(p for p in parts if p))[:1800] or "practice"


#: ``search(query, constraints, *, caller) -> find_practice result``.
Search = Callable[..., Mapping[str, Any]]


def default_search(vault: LoadedVault, repository: Repository, *, injections: Mapping[str, Any],
                   rerank_client: Any | None = None, clock: Clock | None = None) -> Search:
    """``find_practice`` as every caller runs it (``propose_practice``: the one
    hypothesis-ref contract, the service's daily cap, the Reader's caller
    context), system-initiated. ``injections`` are
    :func:`learnloop.instructional.wiring.find_practice_injections`' (the
    adapter builds the plan's minutes estimator; this module never imports the plan)."""

    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.practice import propose_practice

    from learnloop.instructional.policy import PolicyRefused
    from learnloop.instructional.practice import continuation_cursor
    from learnloop.practice_index.retrieval import ContinuationMismatch

    injected = dict(injections)
    base = injected.get("valuer")
    if base is not None:
        # G35 (Codex review F12): the follow-ups' valuation composes the
        # attempt-familiarity discount into every item's information.
        def valuer(*args: Any, **kwargs: Any) -> Any:
            return base(*args, familiarity=True, **kwargs)

        valuer.estimator = getattr(base, "estimator", None)  # type: ignore[attr-defined]
        injected["valuer"] = valuer

    def search(query: str, constraints: Mapping[str, Any], *, caller: Mapping[str, Any],
               continue_from: str | None = None,
               pending_decision: Mapping[str, Any] | None = None,
               already_chosen: Sequence[str] = ()) -> Mapping[str, Any]:
        context = caller_for(repository, "reader", str(caller.get("ref") or ""),
                             learning_object_ids=list(constraints.get("learning_object_ids") or []))
        extra: dict[str, Any] = {}
        if pending_decision:
            extra["pending_decision"] = dict(pending_decision)
        if already_chosen:
            # Round 3: the question's live checks seed the greedy conditional
            # selection (§9.3 item 3); a re-ask adds a check only if it still
            # clears the stop given them, and never retires one.
            extra["already_chosen"] = list(already_chosen)
        cursor = None
        if continue_from:
            # Codex review F6: an interrupted search resumes where it stopped,
            # its relevant candidates (the checks it chose among them) carried.
            try:
                cursor = continuation_cursor(repository, continue_from, caller=context, query=query,
                                             intent=str(constraints.get("intent") or "practice"))
            except (ValueError, PolicyRefused):
                cursor = None
        if cursor is not None:
            try:
                return propose_practice(vault, repository, query, constraints, caller=context, origin="api",
                                        rerank_client=rerank_client, clock=clock, system_initiated=True,
                                        cursor=cursor, **extra, **injected)
            except ContinuationMismatch:
                pass  # a changed filter is a new search
        return propose_practice(vault, repository, query, constraints, caller=context, origin="api",
                                rerank_client=rerank_client, clock=clock, system_initiated=True,
                                **extra, **injected)

    return search


def _followups_envelope(vault: Any, repository: Repository, clock: Clock | None) -> Any:
    from learnloop.source_retrieval.service_spend import SharedDailyEnvelope, midnight

    return SharedDailyEnvelope(vault, repository, day=midnight(clock), cap=float(_config(vault).max_daily_cost_usd),
                               clock=clock, name=ENVELOPE, owner_kinds=(OWNER_KIND,),
                               price_per_million=vault.config.source_service.llm_price_per_million)


@contextmanager
def followup_spend(vault: Any, repository: Repository, clock: Clock | None = None) -> Iterator[None]:
    """``followups.max_daily_cost_usd`` and ``source_service.max_daily_cost_usd``
    together: a metered relevance call reserves in both, so whichever is
    reached first stops it (§9.3 item 6). Subscription calls reserve nothing."""

    from learnloop.source_retrieval.service_spend import daily_envelope

    with spend_envelopes(daily_envelope(vault, repository, clock), _followups_envelope(vault, repository, clock)):
        yield


# ---------------------------------------------------------------------------
# 3. Dating by purpose (§9.3 item 4)
# ---------------------------------------------------------------------------

def _local_day(moment: datetime) -> date:
    return moment.astimezone().date()


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def retention_due(vault: LoadedVault, repository: Repository, *, practice_item_id: str,
                  attempt: Mapping[str, Any] | None, now: datetime) -> tuple[datetime | None, str]:
    """When forgetting is expected for the practiced item, from FSRS.

    The item's effective due (DL2 §5.3: the stored due at the item's recall
    target, through the intent view when intent is live), else, with no FSRS
    state yet, the scheduler's own first interval for that attempt's rating
    (``fsrs.initial_stability`` at the target retention). No date of its own."""

    from learnloop.params.fitted_params import resolve_fsrs_weights
    from learnloop.scheduling import fsrs as F
    from learnloop.scheduling.intent.recall_targets import STORED_RETENTION
    from learnloop.scheduling.intent.serving import intent_serving

    state = repository.practice_item_state(practice_item_id)
    view = None
    try:
        view = intent_serving(vault, repository, now=now, force=True)
    except Exception:  # noqa: BLE001 - the stored due stands without the intent view
        view = None
    if state is not None and getattr(state, "due_at", None):
        if view is not None:
            effective = view.effective(practice_item_id, state)
            if effective.due is not None:
                return effective.due, "effective_due"
        parsed = parse_utc(state.due_at)
        if parsed is not None:
            return parsed, "fsrs_due"
    if attempt is None:
        return None, "no_fsrs_state"
    item = vault.practice_items.get(practice_item_id)
    rubric = vault.rubric_for_item(item) if item is not None else None
    if item is None or rubric is None or attempt.get("rubric_score") is None:
        return None, "no_fsrs_state"
    from learnloop.attempts.attempts import fsrs_rating_for_attempt

    rating = fsrs_rating_for_attempt(item, int(attempt["rubric_score"]), int(rubric.max_points),
                                     int(attempt.get("hints_used") or 0))
    weights = tuple(resolve_fsrs_weights(repository))
    # The scheduler's own target: the intent view's, else the retention the
    # attempt path stores ``due_at`` at (no number of RW6b's).
    target = view.target_for(practice_item_id) if view is not None else STORED_RETENTION
    days = F.interval_for_retention(F.initial_stability(rating, weights), target, weights)
    anchor = parse_utc(str(attempt.get("created_at") or "")) or now
    return anchor + timedelta(days=days), "fsrs_first_interval"


def date_for(vault: LoadedVault, repository: Repository, *, purpose: str, practice_item_id: str | None,
             attempt: Mapping[str, Any] | None, now: datetime) -> dict[str, Any]:
    """``{"due_hint": YYYY-MM-DD, "basis", "capped"}``: never today, never past the time cap."""

    tomorrow = _local_day(now) + timedelta(days=1)
    cap = _local_day(now) + timedelta(days=max_wait_days(vault))
    if purpose == PURPOSE_DISCRIMINATING:
        return {"due_hint": tomorrow.isoformat(), "basis": "next_day_plan", "capped": False}
    when, basis = (None, "no_practiced_item") if practice_item_id is None else retention_due(
        vault, repository, practice_item_id=practice_item_id, attempt=attempt, now=now)
    if when is None:
        # Nothing to date it from: the time cap is the only bound left.
        return {"due_hint": cap.isoformat(), "basis": basis, "capped": True}
    day = max(_local_day(when), tomorrow)
    capped = day > cap
    return {"due_hint": min(day, cap).isoformat(), "basis": basis, "capped": capped,
            "derived_at": _iso(when)}


# ---------------------------------------------------------------------------
# 4-5. Planning one session
# ---------------------------------------------------------------------------

def digest_id_for(extraction_id: str, session_key: str) -> str:
    return "rsd_" + content_key([extraction_id, session_key])[:32]


def _workbench_spans(repository: Repository, session_ids: Sequence[str]) -> dict[str, list[str]]:
    wanted = sorted({str(s) for s in session_ids if s})
    if not wanted:
        return {}
    marks = ",".join("?" for _ in wanted)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            f"SELECT id, span_ids_json FROM workbench_sessions WHERE id IN ({marks})", wanted).fetchall()
    out: dict[str, list[str]] = {}
    for row in rows:
        try:
            spans = json.loads(row["span_ids_json"] or "[]")
        except (TypeError, ValueError):
            spans = []
        out[str(row["id"])] = [str(span) for span in spans if span] if isinstance(spans, list) else []
    return out


def _section_spans(repository: Repository, extraction_id: str, sections: Sequence[Mapping[str, Any]]) -> list[str]:
    """The first span of the last section the session read (the studied passage)."""

    from learnloop.db.stores.source_block_fts import extraction_units

    ids = [str(row.get("section_id")) for row in sections if row.get("section_id")]
    if not ids:
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        units = {unit.unit_id: list(unit.span_ids) for unit in extraction_units(connection, extraction_id)}
    for section in reversed(ids):
        if units.get(section):
            return [str(units[section][0])]
    return []


def _session_spans(vault: Any, repository: Repository, summary: Mapping[str, Any], learning_object_ids: Sequence[str],
                   extraction_id: str) -> tuple[list[str], list[str]]:
    """The way back (§9.3 item 9; Codex review F10): the session's inquiry
    roots and anchor spans on these learning objects; the spans of the
    workbench sessions that worked an item of them and of the formative
    records that touched them; with none of those, the workbench and formative
    spans of the session, else the first span of the passage it read last."""

    wanted = set(learning_object_ids)
    inquiries = summary.get("inquiries") or {}
    roots: list[str] = []
    spans: list[str] = []
    seen: set[str] = set()

    def span_los(span_ids: Sequence[str]) -> set[str]:
        return {lo for span in span_ids
                for lo in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span)}

    def add(values: Sequence[str]) -> None:
        spans.extend(s for s in values if s not in spans)

    for line in [*(inquiries.get("opened") or []), *(inquiries.get("still_open") or []),
                 *(inquiries.get("resolved") or [])]:
        root = str(line.get("root_exchange_id") or "")
        if not root or root in seen:
            continue
        seen.add(root)
        line_spans = [str(s) for s in line.get("span_ids") or []]
        if span_los(line_spans) & wanted:
            roots.append(root)
            add(line_spans)
    workbench = list(summary.get("workbench") or [])
    by_session = _workbench_spans(repository, [str(line.get("session_id") or "") for line in workbench])
    loose: list[str] = []
    for line in workbench:
        line_spans = by_session.get(str(line.get("session_id") or ""), [])
        if _item_lo(vault, line.get("practice_item_id")) in wanted or span_los(line_spans) & wanted:
            add(line_spans)
        else:
            loose.extend(line_spans)
    for record in summary.get("observations") or []:
        record_spans = [str(s) for s in record.get("span_ids") or [] if s]
        facet_los = {lo for facet in record.get("facet_candidates") or []
                     for lo in _facet_los(vault, str(facet))} if hasattr(vault, "practice_items") else set()
        if span_los(record_spans) & wanted or facet_los & wanted:
            add(record_spans)
        else:
            loose.extend(record_spans)
    if not roots and not spans:
        add(list(dict.fromkeys(loose)) or _section_spans(repository, extraction_id,
                                                          summary.get("sections_read") or []))
    return roots, spans


def _novelty(vault: Any, item_id: str, worked_item_ids: Sequence[str]) -> str:
    """Exact facts only (row 79): a candidate in the family of an item the
    session worked is ``same_surface`` and never transfer; anything else is
    "a new problem" until the relevance step returns ``new_application``."""

    item = vault.practice_items.get(item_id)
    families = {vault.practice_items[w].family_id for w in worked_item_ids
                if w in vault.practice_items and vault.practice_items[w].family_id}
    if item is not None and item.family_id and item.family_id in families:
        return NOVELTY_SAME_SURFACE
    return NOVELTY_NEW_PROBLEM


def _chosen_checks(result: Mapping[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Each section's checks that may be dated: a check verdict, a licensing regime."""

    valuation = result.get("valuation") or {}
    out = []
    for section in valuation.get("problems") or []:
        if section.get("verdict") not in CHECK_VERDICTS:
            continue
        for check in section.get("checks") or []:
            if check.get("licenses_system_check"):
                out.append((section, dict(check)))
    return out


def _marginal(section: Mapping[str, Any], check: Mapping[str, Any]) -> dict[str, float] | None:
    """P(E) under the problem's prior for a later pick, whose receipt values it
    conditionally (S5 records P(E) for every chosen check, §11.4 item 1):
    the sum the valuation's own ``_predicted`` takes, over the persisted
    point table. A record of the receipt's numbers, never a value."""

    prior = (section.get("problem") or {}).get("prior") or {}
    table = check.get("likelihood") or {}
    if not prior or not table:
        return None
    emissions = sorted({e for row in table.values() for e in row})
    return {e: round(sum(float(prior[h]) * float((table.get(h) or {}).get(e, 0.0)) for h in prior), 6)
            for e in emissions}


def _question_outcome(result: Mapping[str, Any], chosen: Sequence[Any]) -> dict[str, Any]:
    if result.get("status") != "ok":
        return {"outcome": "unavailable", "reason": result.get("reason") or result.get("status")}
    valuation = result.get("valuation") or {}
    sections = valuation.get("problems") or []
    paging = (result.get("paging") or {}).get("outcome")
    if chosen:
        return {"outcome": "checks", "paging": paging}
    if not sections:
        reason = valuation.get("verdict") or valuation.get("reason") or valuation.get("status") or "no_problem"
        return {"outcome": "no_question", "reason": reason, "unavailable": valuation.get("unavailable") or []}
    candidates = sum(len((s.get("groups") or {}).get(g) or ()) for s in sections for g in ("valued", "bounded",
                                                                                           "unvalued"))
    if candidates == 0:
        return {"outcome": "no_item", "paging": paging}
    verdicts = sorted({str(s.get("verdict")) for s in sections})
    return {"outcome": "no_check", "verdicts": verdicts,
            "reasons": sorted({str(s.get("reason")) for s in sections if s.get("reason")}), "paging": paging}


def _incomplete(result: Mapping[str, Any]) -> bool:
    paging = (result.get("paging") or {}).get("outcome")
    return paging in ("budget", "judge_unavailable") or result.get("rerank_status") in ("over_budget", "failed")


def purpose_text(vault: Any, purpose: str, learning_object_ids: Sequence[str], novelty: str | None) -> str:
    """Learner-facing purpose wording (G16: never "error" or "mistake" about the learner's work)."""

    title = next((vault.learning_objects[lo].title for lo in learning_object_ids if lo in vault.learning_objects),
                 "this")
    if purpose == PURPOSE_DISCRIMINATING:
        return f"a question that tells apart the explanations still open on {title}"
    label = NOVELTY_LABELS.get(novelty or NOVELTY_NEW_PROBLEM, NOVELTY_LABELS[NOVELTY_NEW_PROBLEM])
    return f"{label} on {title}, on your own"


def why_text(purpose: str, check: Mapping[str, Any], mode: str | None) -> str:
    minutes = check.get("expected_minutes")
    about = f"about {max(1, round(float(minutes)))} min · " if minutes is not None else ""
    if mode == "decision":
        lead = "expected to settle which repair to try"
    elif purpose == PURPOSE_DISCRIMINATING:
        lead = "expected to tell the explanations apart"
    else:
        lead = "expected to show whether this holds without help"
    return f"{lead} · {about}{SCALE_LABEL}"


def _exposure_scope(vault: Any, repository: Repository, learning_object_ids: Sequence[str],
                    extraction_id: str) -> list[str]:
    """The extractions the exposure rule's worked-example shortlist is drawn
    from for these learning objects (``teaching_scope``), plus the session's:
    the serve-time gate reads studied examples in this scope (F1)."""

    from learnloop.source_retrieval.corpus import teaching_scope

    try:
        scope = set(teaching_scope(vault, repository, list(learning_object_ids), item_bound=False).extractions)
    except Exception:  # noqa: BLE001 - no scope reads every extraction (the conservative reading)
        return []
    return sorted(scope | {extraction_id})


def plan_session(vault: LoadedVault, repository: Repository, *, extraction_id: str, session: RS.ReaderSession,
                 search: Search | None, now: datetime, clock: Clock | None = None) -> dict[str, Any] | None:
    """Plan the follow-ups of one ended reader session; returns its digest row.

    Idempotent per session: a planned session is returned as stored; an
    ``incomplete`` one (a budget or the judge stopped a search, or a check was
    exposed since its valuation) re-asks only the questions that did not
    finish, resuming an interrupted search from its continuation and keeping
    the commitments it made (Codex review F6). ``None`` when follow-ups are
    off or the session had no activity.

    Every (paid) search runs first; then ONE transaction re-reads the digest
    (another process may have planned the session meanwhile: its row stands),
    re-checks the learner's intent on each item, and publishes the
    commitments, the digest receipt and the queue revision together, so no
    live check exists outside the digest and re-valuation (Codex review F3)."""

    if not followups_enabled(vault):
        return None
    digest_id = digest_id_for(extraction_id, session.session_id)
    with repository.connection() as connection:
        existing = RDG.digest_for_session(connection, extraction_id, session.session_id)
    if existing is not None and existing["status"] == "planned":
        return existing
    summary = RC.session_summary(vault, repository, extraction_id=extraction_id, session=session, now=now)
    if not summary.get("activity"):
        return None
    questions, notes = open_questions(vault, repository, summary, now=now)
    families = revealed_families(vault, repository, session)
    previous = (existing or {}).get("valuation") or {}
    previous_entries = {q["key"]: q for q in previous.get("questions") or []}
    done = {key for key, q in previous_entries.items() if not q.get("incomplete")}
    receipt_questions = [q for q in previous.get("questions") or [] if q["key"] in done]
    # Copies: the stored row is compared whole at publication (F3), so a
    # licensing question added to a line must never touch ``existing``.
    chosen: list[dict[str, Any]] = [dict(line) for line in previous.get("chosen") or []]
    commitment_ids: list[str] = list((existing or {}).get("followup_commitment_ids") or [])
    # Round 3: rescheduling is decided from the LIVE checks (a pending
    # commitment), never from every ref ever chosen. An item whose earlier
    # check was retired or satisfied may be scheduled again as a fresh
    # generation; one the learner undid is theirs and stays out.
    live = _live_lines(repository, chosen)
    undone = _undone_refs(repository, chosen)
    planned_now: dict[str, dict[str, Any]] = {}
    worked = [str(line.get("practice_item_id")) for line in summary.get("workbench") or [] if line.get("practice_item_id")]
    attempts = _attempt_rows(repository, [a for q in questions for a in q.attempt_ids])
    source_id = RC._source_id(repository, extraction_id)
    with repository.connection() as connection:
        committed = committed_items(vault, connection, own=commitment_ids)
    from learnloop.instructional.wiring import disabled_reason

    switched_off = disabled_reason(vault, "discriminating_search")
    incomplete = False
    intent_excluded: set[str] = set()
    planned: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []  # (entry, creation, chosen line)
    for question in questions:
        if question.key in done:
            continue
        excluded_items = sorted(i for i in committed | undone
                                if _item_lo(vault, i) in set(question.learning_object_ids))
        intent_excluded.update(excluded_items)
        constraints = constraints_for(question, exclude_family_ids=families, exclude_item_ids=excluded_items)
        entry: dict[str, Any] = {"key": question.key, "question": question.as_dict(), "constraints": constraints}
        if switched_off is not None or search is None:
            entry.update(outcome="unavailable", reason=switched_off or "no_search")
            receipt_questions.append(entry)
            continue
        kwargs: dict[str, Any] = {}
        resume = (previous_entries.get(question.key) or {}).get("continue_from")
        if resume:
            kwargs["continue_from"] = resume
        if question.pending_decision:
            kwargs["pending_decision"] = dict(question.pending_decision)
        # §9.3 item 3: checks are added greedily, each valued conditionally on
        # those already chosen; the question's live checks are already chosen.
        already = [ref for ref, index in live.items() if question.key in _licensing(chosen[index])]
        if already:
            kwargs["already_chosen"] = already
            entry["already_chosen"] = list(already)
        try:
            with followup_spend(vault, repository, clock):
                result = search(query_for(vault, question), constraints,
                                caller={"kind": VIA, "ref": digest_id}, **kwargs)
        except SpendLimitExceeded as exc:
            entry.update(outcome="incomplete", reason="budget", detail=str(exc), incomplete=True)
            if resume:
                entry["continue_from"] = resume
            receipt_questions.append(entry)
            incomplete = True
            continue
        except ValueError as exc:  # a refused request (IntentUnavailable, PolicyRefused): typed, kept
            entry.update(outcome="unavailable", reason=getattr(exc, "code", None) or type(exc).__name__,
                         detail=str(exc))
            receipt_questions.append(entry)
            continue
        picks = _chosen_checks(result)
        entry.update(_question_outcome(result, picks))
        entry.update(proposal_id=result.get("proposal_id"), rerank_status=result.get("rerank_status"),
                     valuation=result.get("valuation"))
        if _incomplete(result):
            # Stopped early, with checks or without (F6): the question stays
            # open and the next plan resumes from this search's continuation.
            entry["incomplete"] = True
            incomplete = True
            if (result.get("paging") or {}).get("cursor") and result.get("proposal_id"):
                entry["continue_from"] = str(result["proposal_id"])
        if entry.get("outcome") == "no_item" and not already:
            entry["generation"] = (
                {"requested": False, "reason": "generate_when_nothing_fits is off"}
                if not getattr(_config(vault), "generate_when_nothing_fits", False)
                else {"requested": False, "reason": "unavailable: PF has no source-anchored request API yet"})
        if already and not picks and entry.get("outcome") in ("no_check", "no_item"):
            # Nothing clears the stop beyond the live checks: they answer it.
            entry.update(outcome="checks", search_outcome=entry.get("outcome"))
        roots, spans = _session_spans(vault, repository, summary, question.learning_object_ids, extraction_id)
        scope = _exposure_scope(vault, repository, question.learning_object_ids, extraction_id)
        for section, check in picks:
            ref = str(check["ref"])
            if ref not in vault.practice_items:
                continue
            if ref in undone:
                # Filtered out by the request; never rescheduled over the learner's undo.
                entry.setdefault("skipped", []).append({"ref": ref, "reason": "learner_undid"})
                continue
            # A check another question (or problem) already licenses is
            # proposed once; this question is recorded as licensing it too,
            # and it stays live while any of them needs it (round 3).
            shared = chosen[live[ref]] if ref in live else planned_now.get(ref)
            if shared is not None:
                if question.key not in _licensing(shared):
                    shared["questions"] = [*_licensing(shared), question.key]
                    entry.setdefault("shared", []).append(
                        {"ref": ref, "commitment_id": shared.get("commitment_id"),
                         "first_licensed_by": shared.get("question")})
                continue
            generation = sum(1 for line in chosen if str(line.get("ref")) == ref)
            last_attempt = max((attempts[a] for a in question.attempt_ids if a in attempts),
                               key=lambda row: (str(row.get("created_at")), str(row.get("id"))), default=None)
            practiced = str(last_attempt["practice_item_id"]) if last_attempt else None
            if question.purpose == PURPOSE_RETENTION and practiced is None and question.learning_object_ids:
                success = recent_assisted_success(vault, repository, question.learning_object_ids[0],
                                                  question.facet_ids[0] if question.facet_ids else None)
                if success is not None:
                    practiced = str(success["practice_item_id"])
                    last_attempt = _attempt_rows(repository, [str(success["id"])]).get(str(success["id"]))
            dated = date_for(vault, repository, purpose=question.purpose, practice_item_id=practiced,
                             attempt=last_attempt, now=now)
            novelty = _novelty(vault, ref, worked)
            mode = (section.get("mode") or "information")
            valuation_ref = {"digest_id": digest_id, "question": question.key,
                             "problem": (section.get("problem") or {}).get("key"), "order": check.get("order"),
                             "proposal_id": result.get("proposal_id")}
            lo_ids = list(question.learning_object_ids)
            provenance = {
                "via": VIA, "summary_id": digest_id, "purpose": question.purpose, "novelty": novelty,
                "valuation_ref": valuation_ref, "inquiry_root_event_ids": roots, "anchor_span_ids": spans,
                "extraction_id": extraction_id, "source_id": source_id,
                "restoration_label": next((vault.learning_objects[lo].title for lo in lo_ids
                                           if lo in vault.learning_objects), None),
                "question": {"intent": question.intent, "learning_object_ids": lo_ids,
                             "facet_ids": list(question.facet_ids),
                             "target_hypotheses": [dict(r) for r in question.target_hypotheses],
                             **({"pending_decision": dict(question.pending_decision)}
                                if question.pending_decision else {})},
                "attempt_ids": list(question.attempt_ids),
                "exposure_scope_extraction_ids": scope,
                "followups_version": FOLLOWUPS_VERSION,
            }
            creation = {"ref": ref, "intent_text": purpose_text(vault, question.purpose, lo_ids, novelty),
                        "due_hint": dated["due_hint"], "provenance": provenance,
                        # Idempotent per digest, question, item and generation:
                        # a fresh generation never resolves to a retired check.
                        "idempotency_key": f"{VIA}:{digest_id}:{question.key}:{ref}:{generation}"}
            line = {
                "ref": ref, "commitment_id": None, "question": question.key, "questions": [question.key],
                "generation": generation,
                "problem": valuation_ref["problem"], "order": check.get("order"), "purpose": question.purpose,
                "mode": mode, "novelty": novelty, "due_hint": dated["due_hint"], "date_basis": dated["basis"],
                "date_capped": dated["capped"], "regime": check.get("regime"),
                # R1's names (router R3's replay reads both).
                "probe_eig": check.get("robust_eig_nats"), "evsi_assignment": check.get("evsi"),
                "point_eig_nats": check.get("point_eig_nats"), "value_minutes_lcb": check.get("value_minutes_lcb"),
                "expected_minutes": check.get("expected_minutes"),
                "predicted_outcomes": check.get("predicted_outcomes") or _marginal(section, check),
                "familiarity": check.get("familiarity"),
                "why": why_text(question.purpose, check, mode),
            }
            planned_now[ref] = line
            planned.append((entry, creation, line))
        receipt_questions.append(entry)
    return _publish(vault, repository, digest_id=digest_id, existing=existing, extraction_id=extraction_id,
                    session=session, summary=summary, notes=notes, families=families,
                    receipt_questions=receipt_questions, chosen=chosen, commitment_ids=commitment_ids,
                    planned=planned, incomplete=incomplete,
                    intent_excluded=intent_excluded, now=now, clock=clock)


def _licensing(line: Mapping[str, Any]) -> list[str]:
    """The questions that license a chosen check (round 3; a line written
    before ``questions`` existed names its one question)."""

    return [str(key) for key in (line.get("questions") or [line.get("question")]) if key]


def _live_lines(repository: Repository, chosen: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """``ref -> index`` of each chosen line whose check is live (pending)."""

    out: dict[str, int] = {}
    for index, line in enumerate(chosen):
        commitment_id = line.get("commitment_id")
        if not commitment_id:
            continue
        try:
            if C.resolve_disposition(repository, str(commitment_id)) == "one_check_pending":
                out[str(line["ref"])] = index
        except C.UnknownCommitment:
            continue
    return out


def _undone_refs(repository: Repository, chosen: Sequence[Mapping[str, Any]]) -> set[str]:
    """The items whose check from this digest the learner undid (and did not
    restore): never scheduled again by a later search of the same session."""

    out: set[str] = set()
    for line in chosen:
        commitment_id = line.get("commitment_id")
        if not commitment_id:
            continue
        info = _retirement(repository, str(commitment_id))
        if info is not None and info.get("reason") == RETIRE_UNDONE:
            out.add(str(line["ref"]))
    return out


def _publish(vault: Any, repository: Repository, *, digest_id: str, existing: Mapping[str, Any] | None,
             extraction_id: str, session: RS.ReaderSession, summary: Mapping[str, Any],
             notes: Sequence[Mapping[str, Any]], families: Sequence[str], receipt_questions: list[dict[str, Any]],
             chosen: list[dict[str, Any]], commitment_ids: list[str],
             planned: Sequence[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]], incomplete: bool,
             intent_excluded: set[str], now: datetime, clock: Clock | None) -> dict[str, Any] | None:
    """F3: the commitments, the digest receipt and the queue revision in one
    transaction. Nothing here retires a check (round 3): a re-asked search
    only adds what clears the stop given the question's live checks."""

    stamp = utc_now_iso(clock)
    created_any = False
    with repository.atomic():
        connection = repository.connection()
        current = RDG.digest_for_session(connection, extraction_id, session.session_id)
        # The whole row as this plan read it, not its second-resolution
        # ``updated_at``: two resumptions can publish within one second
        # (Codex re-review F3). Any change since (another plan, a
        # re-valuation) supersedes this one; the digest stays incomplete
        # or planned as the other writer left it.
        superseded = (current is not None and (
            existing is None or current["status"] == "planned" or current != existing))
        if not superseded:
            # The learner's intent as it stands now, inside the publication.
            committed = committed_items(vault, connection, own=commitment_ids)
            for entry, creation, line in planned:
                ref = creation["ref"]
                if ref in committed:
                    entry.setdefault("skipped", []).append({"ref": ref, "reason": "learner_intent"})
                    continue
                commitment = C.create_commitment(
                    repository, action="test_me_later", intent_text=creation["intent_text"],
                    targets=[{"target_kind": "legacy_practice_item", "target_ref": ref}],
                    depth_preset="keep_in_touch", client_idempotency_key=creation["idempotency_key"],
                    author="learnloop", reason=VIA, due_hint=creation["due_hint"],
                    provenance=creation["provenance"], clock=clock)
                created_any = True
                if commitment.id not in commitment_ids:
                    commitment_ids.append(commitment.id)
                chosen.append({**line, "commitment_id": commitment.id})
            valuation = {
                "followups_version": FOLLOWUPS_VERSION, "valuation_version": VALUATION_VERSION,
                "summary_version": summary.get("summary_version"), "scale": SCALE_LABEL,
                "exclude_family_ids": list(families), "questions": receipt_questions, "notes": list(notes),
                "learner_intent_item_ids": sorted(intent_excluded),
                "chosen": chosen, "chosen_ids": [entry["ref"] for entry in chosen], "planned_at": _iso(now),
            }
            status = "incomplete" if incomplete else "planned"
            if existing is None:
                RDG.insert_digest(connection, {
                    "id": digest_id, "extraction_id": extraction_id, "session_key": session.session_id,
                    "visit_ids": list(session.visit_ids), "started_at": session.started_at,
                    "ended_at": session.ended_at, "status": status, "summary": summary,
                    "followup_commitment_ids": commitment_ids, "valuation": valuation, "created_at": stamp})
            else:
                RDG.update_digest(connection, digest_id, status=status, summary_json=summary,
                                  followup_commitment_ids_json=commitment_ids, valuation_json=valuation,
                                  updated_at=stamp)
            if created_any:
                repository.bump_queue_revision(clock=clock)
    with repository.connection() as connection:
        return RDG.digest(connection, digest_id) if not superseded else RDG.digest_for_session(
            connection, extraction_id, session.session_id)


def sessions_to_plan(vault: LoadedVault, repository: Repository, *, now: datetime) -> list[RS.ReaderSession]:
    """Ended reader sessions (no visit for the 30-minute gap) within the time
    cap with no planned digest. Cheap: it reads the envelope and the digests
    only; activity is checked when a session is planned."""

    if not followups_enabled(vault):
        return []
    horizon = now - timedelta(days=max_wait_days(vault))
    with repository.connection() as connection:
        rows = RDG.digests(connection)
    planned = {(row["extraction_id"], row["session_key"]) for row in rows if row["status"] == "planned"}
    out = []
    for session in RS.all_sessions(repository):
        ended = parse_utc(session.ended_at)
        if ended is None or ended + RS.SESSION_GAP > now or ended < horizon:
            continue
        if (session.extraction_id, session.session_id) in planned:
            continue
        out.append(session)
    return out


def plan_ended_sessions(vault: LoadedVault, repository: Repository, *, search: Search | None, now: datetime,
                        clock: Clock | None = None) -> list[dict[str, Any]]:
    """Plan every ended session waiting for its follow-ups (the background job)."""

    planned = []
    for session in sessions_to_plan(vault, repository, now=now):
        row = plan_session(vault, repository, extraction_id=session.extraction_id, session=session,
                           search=search, now=now, clock=clock)
        if row is not None:
            planned.append(row)
    return planned


# ---------------------------------------------------------------------------
# 7. Daily re-valuation (§9.3 item 7): no model call
# ---------------------------------------------------------------------------

def _first_version(repository: Repository, commitment_id: str) -> dict[str, Any]:
    versions = repository.commitment_versions_for(commitment_id)
    return min(versions, key=lambda row: int(row["version"])) if versions else {}


def _provenance(repository: Repository, commitment_id: str) -> dict[str, Any]:
    try:
        return json.loads(_first_version(repository, commitment_id).get("provenance_json") or "{}") or {}
    except (TypeError, ValueError):
        return {}


def _events(repository: Repository, commitment_id: str) -> list[dict[str, Any]]:
    return [dict(row) for row in repository.commitment_events_for(commitment_id)]


def _learner_kept(repository: Repository, commitment_id: str) -> bool:
    """The learner undid a retirement (or restored an undo): re-valuation leaves it alone."""

    for event in _events(repository, commitment_id):
        if event["kind"] == "disposition_changed":
            try:
                detail = json.loads(event.get("detail_json") or "{}")
            except ValueError:
                detail = {}
            if detail.get("reason") == "learner_restored":
                return True
    return False


def _solved_attempt(vault: Any, repository: Repository, *, learning_object_ids: Sequence[str],
                    facet_ids: Sequence[str], since: str) -> dict[str, Any] | None:
    """The unaided success that answered a retention question (the good news's date)."""

    from learnloop.practice_index.catalog import item_facets
    from learnloop.substrate.intervention_outcomes import SUCCESS_CORRECTNESS, is_assisted

    los = set(learning_object_ids)
    facets = {vault.canonical_facet_id(f) for f in facet_ids}
    items = sorted(i.id for i in vault.practice_items.values()
                   if i.learning_object_id in los and (not facets or facets & set(item_facets(vault, i))))
    if not items:
        return None
    marks = ",".join("?" for _ in items)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            f"SELECT id, practice_item_id, created_at, correctness, attempt_type, hints_used, primed "
            f"FROM practice_attempts WHERE practice_item_id IN ({marks}) AND created_at >= ? "
            "AND correctness IS NOT NULL ORDER BY created_at DESC, id DESC", (*items, since)).fetchall()
    for row in rows:
        if float(row["correctness"]) >= SUCCESS_CORRECTNESS and not is_assisted(dict(row)):
            return dict(row)
    return None


def _today(now: datetime) -> str:
    return _local_day(now).isoformat()


def _gate_reasons(vault: Any, repository: Repository, *, item_id: str, provenance: Mapping[str, Any],
                  valued_at: str, now: datetime) -> list[str]:
    """The serve-time gate's reasons now (exposure since valuation, repair
    ownership; ``scheduling.intent.followup_gate``), with no model call."""

    from learnloop.scheduling.intent.followup_gate import followup_gate

    verdict = followup_gate(vault, repository, item_id=item_id, provenance=provenance, valued_at=valued_at, now=now)
    return list((verdict or {}).get("reasons") or [])


def revalue_pending(vault: LoadedVault, repository: Repository, *, now: datetime,
                    valuer: Callable[..., Mapping[str, Any]] | None = None, clock: Clock | None = None,
                    force: bool = False) -> dict[str, Any]:
    """Re-value every pending follow-up once a local day, before the plan is
    built, with no model call (Codex review F5). ``valuer(question, item_id)
    -> receipt`` is ``discriminating.value_request`` for one item with the
    exposure rule applied here instead of its judge (:func:`default_valuer`).

    For each pending check, in order: an answered question retires it (good
    news); the serve-time gate's exposure since valuation retires it and
    re-asks the question (F1), a repair cold retry that now owns the claim
    retires it (F11), and a studied worked example nobody judged yet keeps it
    for the background refresh (:func:`refresh_exposure`); then the valuation
    retires one below the stop. With ``source_service.discriminating_search``
    (or the service) off, nothing is valued and the checks stay."""

    report: dict[str, Any] = {"retired": [], "kept": [], "skipped": None}
    if not followups_enabled(vault):
        report["skipped"] = "followups.enabled is false"
        return report
    from learnloop.instructional.wiring import disabled_reason

    switched_off = disabled_reason(vault, "discriminating_search")
    today = _today(now)
    with repository.connection() as connection:
        rows = [row for row in RDG.digests(connection) if row.get("followup_commitment_ids")]
    for row in rows:
        if row.get("revalued_on") == today and not force:
            continue
        lines = []
        requery: list[str] = []
        stored = row.get("valuation") or {}
        line_by_commitment = {str(line["commitment_id"]): line for line in stored.get("chosen") or []
                              if line.get("commitment_id")}
        entries = {str(entry.get("key")): entry for entry in stored.get("questions") or []}
        for commitment_id in row["followup_commitment_ids"]:
            try:
                disposition = C.resolve_disposition(repository, commitment_id)
            except C.UnknownCommitment:
                continue
            if disposition != "one_check_pending" or _learner_kept(repository, commitment_id):
                continue
            provenance = _provenance(repository, commitment_id)
            question = provenance.get("question") or {}
            item_id = next((t["target_ref"] for t in _targets(repository, commitment_id)
                            if t["target_kind"] == "legacy_practice_item"), None)
            if not question or item_id is None:
                continue
            if switched_off is not None:
                line = {"commitment_id": commitment_id, "item_id": item_id, "retired": False,
                        "kept_because": [switched_off]}
            elif valuer is None:
                continue
            else:
                line = _revaluation_line(vault, repository, commitment_id=commitment_id, item_id=item_id,
                                         provenance=provenance, valuer=valuer, extraction_id=row["extraction_id"],
                                         others=_other_licensing(provenance, line_by_commitment.get(commitment_id),
                                                                 entries),
                                         now=now, clock=clock)
            lines.append(line)
        retired_here = False
        with repository.atomic():
            # F13 (Codex re-review): an exposure retirement, its question's
            # re-ask marker and the queue revision commit together, so a
            # failure between them loses neither the check nor the search.
            connection = repository.connection()
            for line in lines:
                if line.get("reason") != RETIRE_EXPOSED or line.get("retired"):
                    continue
                commitment_id = str(line["commitment_id"])
                if C.resolve_disposition(repository, commitment_id) != "one_check_pending" \
                        or _learner_kept(repository, commitment_id):
                    for key in ("reason", "detail", "question_keys"):
                        line.pop(key, None)
                    line["kept_because"] = ["changed_meanwhile"]
                    continue
                C.retire(repository, commitment_id=commitment_id, detail=line["detail"], clock=clock)
                line["retired"] = True
                # Every question that licensed the exposed check is asked again.
                requery.extend(str(key) for key in line.pop("question_keys", None) or () if key)
            for line in lines:
                line.pop("question_keys", None)
                report["retired" if line["retired"] else "kept"].append(line)
                retired_here = retired_here or bool(line["retired"])
            columns: dict[str, Any] = {}
            if requery:
                # F1: the exposed check's question is asked again (a fresh
                # search; the exposed item is out of its exact filters now).
                # The valuation as it stands now, inside the transaction.
                fresh = RDG.digest(connection, row["id"]) or row
                valuation = dict(fresh.get("valuation") or {})
                questions = []
                for entry in valuation.get("questions") or []:
                    if entry.get("key") in requery:
                        entry = {**entry, "incomplete": True, "reason": RETIRE_EXPOSED}
                        entry.pop("continue_from", None)
                    questions.append(entry)
                valuation["questions"] = questions
                columns.update(status="incomplete", valuation_json=valuation)
            RDG.update_digest(connection, row["id"], revaluation_json={
                "revalued_at": _iso(now), "followups_version": FOLLOWUPS_VERSION, "lines": lines},
                revalued_on=today, updated_at=utc_now_iso(clock), **columns)
            if retired_here:
                repository.bump_queue_revision(clock=clock)
    return report


def exposure_refresh_waiting(repository: Repository) -> bool:
    """Whether the last re-valuation kept a check for the exposure refresh (cheap: the digests only)."""

    with repository.connection() as connection:
        rows = RDG.digests(connection)
    return any(KEPT_REFRESH in (line.get("kept_because") or [])
               for row in rows for line in (row.get("revaluation") or {}).get("lines") or [])


def refresh_exposure(vault: LoadedVault, repository: Repository, *, now: datetime, clock: Clock | None = None,
                     judge_client: Any | None = None) -> list[dict[str, Any]]:
    """The background half of re-valuation (Codex review F5): for each pending
    check the last re-valuation kept only because a worked example studied
    since was never judged against it, ask the exposure rule's judge (route
    ``worked_example_equivalence``) under BOTH daily envelopes
    (:func:`followup_spend`) and the source switches. The verdict lands in
    the ledger, which the serve-time gate and the next re-valuation read. Never
    on the request path."""

    from learnloop.instructional import exposure as E
    from learnloop.instructional.wiring import disabled_reason

    if not followups_enabled(vault) or disabled_reason(vault, "discriminating_search") is not None:
        return []
    with repository.connection() as connection:
        rows = RDG.digests(connection)
    out: list[dict[str, Any]] = []
    for row in rows:
        for line in (row.get("revaluation") or {}).get("lines") or []:
            if KEPT_REFRESH not in (line.get("kept_because") or []):
                continue
            commitment_id = str(line["commitment_id"])
            try:
                if C.resolve_disposition(repository, commitment_id) != "one_check_pending":
                    continue
            except C.UnknownCommitment:
                continue
            intent = str((_provenance(repository, commitment_id).get("question") or {}).get("intent")
                         or "retention")
            try:
                with followup_spend(vault, repository, clock):
                    verdict = E.independent_check_eligibility(
                        vault, repository, {"practice_item_id": line["item_id"]}, intent=intent,
                        judge_client=judge_client, at=now, clock=clock)
            except SpendLimitExceeded:
                return out
            out.append({"commitment_id": commitment_id, "eligible": bool(verdict.get("eligible")),
                        "reasons": list(verdict.get("reasons") or [])})
    return out


def _targets(repository: Repository, commitment_id: str) -> list[dict[str, Any]]:
    head = max(repository.commitment_versions_for(commitment_id), key=lambda r: int(r["version"]))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [dict(r) for r in connection.execute(
            "SELECT target_kind, target_ref FROM commitment_target_versions WHERE commitment_version_id = ?",
            (head["id"],))]


def answered_since(vault: Any, repository: Repository, question: Mapping[str, Any], *,
                   since: str) -> dict[str, Any] | None:
    """How the question was answered since ``since``, or None (still open).

    Retention: the claim's learning objects' latest success is unaided now
    (``recent_assisted_success`` is the valuation's own reading of "assisted
    only") and an unaided success exists since the follow-up was made.
    Discriminate: every probe episode the question named is closed. Any
    other rival is answered only through the valuation's stop."""

    if question.get("intent") == "retention":
        los = list(question.get("learning_object_ids") or [])
        facets = list(question.get("facet_ids") or [])
        if not los or any(recent_assisted_success(vault, repository, lo, facets[0] if facets else None) is not None
                          for lo in los):
            return None
        solved = _solved_attempt(vault, repository, learning_object_ids=los, facet_ids=facets, since=since)
        if solved is None:
            return None
        return {"answered_by": ANSWERED_SOLVED, "solved_attempt_id": solved["id"], "solved_at": solved["created_at"]}
    episodes = [str(ref.get("id")) for ref in question.get("target_hypotheses") or []
                if ref.get("kind") == "episode_label"]
    others = [ref for ref in question.get("target_hypotheses") or [] if ref.get("kind") != "episode_label"]
    if episodes and not others:
        records = [repository.probe_episode(episode_id) for episode_id in episodes]
        if all(record is None or record.status not in ("pending_items", "in_progress") for record in records):
            return {"answered_by": ANSWERED_RIVALS, "episode_ids": episodes}
    return None


def _other_licensing(provenance: Mapping[str, Any], line: Mapping[str, Any] | None,
                     entries: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The other questions that license this check (round 3: a check one
    question chose and another selected too), from the digest receipt, as
    ``{"key", "question", "purpose", "attempt_ids"}``; the provenance's own
    question is the first licensing question and is not repeated."""

    if not line:
        return []
    primary = str((provenance.get("valuation_ref") or {}).get("question") or line.get("question") or "")
    out = []
    for key in _licensing(line):
        found = (entries.get(key) or {}).get("question") or {}
        if key == primary or not found:
            continue
        question = {"intent": found.get("intent") or INTENT_BY_PURPOSE.get(str(found.get("purpose")), "retention"),
                    "learning_object_ids": list(found.get("learning_object_ids") or []),
                    "facet_ids": list(found.get("facet_ids") or []),
                    "target_hypotheses": [dict(r) for r in found.get("target_hypotheses") or []]}
        if found.get("pending_decision"):
            question["pending_decision"] = dict(found["pending_decision"])
        out.append({"key": key, "question": question, "purpose": found.get("purpose"),
                    "attempt_ids": list(found.get("attempt_ids") or [])})
    return out


def _revaluation_line(vault: Any, repository: Repository, *, commitment_id: str, item_id: str,
                      provenance: Mapping[str, Any], valuer: Callable[..., Mapping[str, Any]],
                      extraction_id: str, now: datetime, clock: Clock | None,
                      others: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """One pending check's re-valuation. A check several questions license
    (round 3) stays live while ANY of them still needs it: it is retired as
    answered only when every one is answered, as owned by a repair only when
    a repair owns every open one, and below the stop only when it is below
    the stop for every open one. An exposure is the item's and retires it,
    re-asking every licensing question."""

    from learnloop.scheduling.intent.followup_gate import REPAIR_RETRY_OWNS

    question = provenance.get("question") or {}
    primary_key = str((provenance.get("valuation_ref") or {}).get("question") or "")
    licensing = [{"key": primary_key, "question": question, "purpose": provenance.get("purpose"),
                  "attempt_ids": list(provenance.get("attempt_ids") or []), "primary": True},
                 *({**other, "primary": False} for other in others)]
    line: dict[str, Any] = {"commitment_id": commitment_id, "item_id": item_id, "retired": False}
    if others:
        line["questions"] = [str(q["key"]) for q in licensing]
    created = str(_first_version(repository, commitment_id).get("created_at") or "")
    answers = [(q, answered_since(vault, repository, q["question"], since=created)) for q in licensing]
    open_questions_ = [q for q, answered in answers if answered is None]
    if not open_questions_:
        answered = answers[0][1] or {}
        detail = {"reason": RETIRE_ANSWERED, **answered, "extraction_id": extraction_id,
                  "followups_version": FOLLOWUPS_VERSION}
        C.retire(repository, commitment_id=commitment_id, detail=detail, clock=clock)
        line.update(retired=True, reason=RETIRE_ANSWERED, detail=detail)
        return line
    if len(open_questions_) < len(licensing):
        line["answered_for"] = [str(q["key"]) for q, answered in answers if answered is not None]
    reasons = _gate_reasons(vault, repository, item_id=item_id, provenance=provenance, valued_at=created, now=now)

    def owner_of(q: Mapping[str, Any]) -> dict[str, Any] | None:
        if q["primary"] and REPAIR_RETRY_OWNS not in reasons:
            return None
        if not q["primary"] and q.get("purpose") != PURPOSE_RETENTION:
            return None  # the gate reads repair ownership for retention checks only
        for facet in q["question"].get("facet_ids") or ():
            found = pending_cold_retry(vault, repository, facet_id=str(facet), attempt_ids=q.get("attempt_ids") or (),
                                       learning_object_ids=q["question"].get("learning_object_ids") or (), now=now)
            if found is not None:
                return found
        return {} if q["primary"] else None

    owners = [owner_of(q) for q in open_questions_]
    if all(owner is not None for owner in owners):
        detail = {"reason": RETIRE_REPAIR_OWNS, "extraction_id": extraction_id,
                  "followup_task_id": next((o.get("id") for o in owners if o and o.get("id")), None),
                  "followups_version": FOLLOWUPS_VERSION}
        C.retire(repository, commitment_id=commitment_id, detail=detail, clock=clock)
        line.update(retired=True, reason=RETIRE_REPAIR_OWNS, detail=detail)
        return line
    reasons = [reason for reason in reasons if reason != REPAIR_RETRY_OWNS]
    if reasons and set(reasons) <= {"worked_example_unjudged"}:
        line["kept_because"] = [KEPT_REFRESH]
        return line
    if reasons:
        # Retired by the caller, in one transaction with the questions'
        # re-ask markers (Codex re-review F13).
        detail = {"reason": RETIRE_EXPOSED, "reasons": reasons, "extraction_id": extraction_id,
                  "followups_version": FOLLOWUPS_VERSION}
        line.update(reason=RETIRE_EXPOSED, detail=detail, question_keys=[str(q["key"]) for q in licensing])
        return line
    kept: list[str] = []
    stop_reasons: set[str] = set()
    verdicts: set[str] = set()
    every_stop = True
    for q in open_questions_:
        receipt = dict(valuer(q["question"], item_id))
        sections = list(receipt.get("problems") or [])
        verdicts |= {str(s.get("verdict")) for s in sections}
        excluded = (receipt.get("excluded") or {}).get(item_id)
        if not sections:
            every_stop = False
            kept += sorted({str(u.get("reason")) for u in receipt.get("unavailable") or []}) or ["no_problem"]
            continue
        if excluded is not None:
            # The exposure rule ran above (no exclusion); what is left is the
            # valuation's own (an unverified key): the check stays, labelled.
            every_stop = False
            kept += ["excluded_at_revaluation", *excluded]
            continue
        if any(str(check.get("ref")) == item_id for section in sections
               if section.get("verdict") in CHECK_VERDICTS for check in section.get("checks") or []):
            line["verdicts"] = sorted(verdicts)
            line["kept_because"] = ["clears_the_stop"]
            return line
        if not all(section.get("verdict") == "stop" for section in sections):
            # An abstention (a flip, no licensing regime now) is not an
            # answer: the check stays the learner's, recorded.
            every_stop = False
            kept += sorted({str(s.get("reason")) for s in sections if s.get("reason")}) or ["abstain"]
            continue
        stop_reasons |= {str(s.get("reason")) for s in sections}
    line["verdicts"] = sorted(verdicts)
    if every_stop:
        detail = {"reason": RETIRE_BELOW_STOP, "extraction_id": extraction_id,
                  "stop_reasons": sorted(stop_reasons), "followups_version": FOLLOWUPS_VERSION}
        C.retire(repository, commitment_id=commitment_id, detail=detail, clock=clock)
        line.update(retired=True, reason=RETIRE_BELOW_STOP, detail=detail)
        return line
    line["kept_because"] = list(dict.fromkeys(kept)) or ["abstain"]
    return line


def _applied_exposure(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """Re-valuation's exposure verdict inside ``value_request``: the rule was
    applied by :func:`_gate_reasons` with no model call (F5)."""

    return {"eligible": True, "reasons": [], "checked": "revaluation_gate"}


def default_valuer(vault: LoadedVault, repository: Repository, *, estimator: Any | None = None
                   ) -> Callable[[Mapping[str, Any], str], Mapping[str, Any]]:
    """``discriminating.value_request`` for one committed item, system-initiated,
    with the follow-ups' familiarity discount (G35, F12) and the question's
    pending repair decision (F7). No model call: the exposure rule is applied
    by the re-valuation itself from persisted judgments (F5), and the
    unimported-exercise screen never runs (no exercises)."""

    from learnloop.diagnosis.probe_robust import resolve_episode_channel
    from learnloop.instructional import discriminating as D
    from learnloop.practice_index.retrieval import PracticeConstraints

    def valuer(question: Mapping[str, Any], item_id: str) -> Mapping[str, Any]:
        constraints = PracticeConstraints.from_mapping({
            "intent": question.get("intent") or "retention",
            "learning_object_ids": list(question.get("learning_object_ids") or []),
            "facet_ids": list(question.get("facet_ids") or []),
            "target_hypotheses": [dict(r) for r in question.get("target_hypotheses") or []],
        })
        return D.value_request(vault, repository, constraints, items=[item_id], exercises=[],
                               caller_kind=VIA, system_initiated=True, estimator=estimator,
                               channel_resolver=resolve_episode_channel,
                               pending_decision=question.get("pending_decision") or None,
                               familiarity=True, eligibility=_applied_exposure)

    return valuer


# ---------------------------------------------------------------------------
# Undo (UX §4.8, S15; W5)
# ---------------------------------------------------------------------------

def _require_followup(repository: Repository, commitment_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        provenance = _provenance(repository, commitment_id)
    except Exception as exc:  # noqa: BLE001 - an unknown id is a refusal
        raise FollowupError(f"unknown follow-up {commitment_id!r}") from exc
    if provenance.get("via") != VIA:
        raise FollowupError(f"{commitment_id!r} is not a reader follow-up")
    with repository.connection() as connection:
        row = RDG.digest_for_commitment(connection, commitment_id)
    return provenance, row or {}


def undo_followup(repository: Repository, *, commitment_id: str, reason: str | None = None,
                  clock: Clock | None = None) -> dict[str, Any]:
    """Retire one follow-up the learner undid, with their optional reason.

    The reason is stored on the ``learner_card`` verdict undo appends (task
    ``reader_followup_undo``): direct evidence about λ and the burden for the
    calibration track (§15), never sent to learner-text gaps (it is about the
    check, not the subject). Only a pending check is undone: an already
    retired one is returned as it is (idempotent), and one its attempt
    already answered (``satisfied``) stays answered, with no verdict."""

    provenance, row = _require_followup(repository, commitment_id)
    disposition = C.resolve_disposition(repository, commitment_id)
    words = " ".join(str(reason or "").split())[:UNDO_REASON_CHARS] or None
    judgment_id = "rfu_" + content_key([commitment_id, "undone"])[:40]
    if disposition != "one_check_pending":
        return {"commitment_id": commitment_id, "disposition": disposition,
                "judgment_id": judgment_id if disposition == "stopped" else None}
    detail = {"reason": RETIRE_UNDONE, "extraction_id": provenance.get("extraction_id"),
              "digest_id": row.get("id"), "followups_version": FOLLOWUPS_VERSION}
    with repository.atomic():
        disposition = C.retire(repository, commitment_id=commitment_id, detail=detail, clock=clock)
        connection = repository.connection()
        stamp = utc_now_iso(clock)
        if not judgments_by_ids(connection, [judgment_id]):
            append_judgment(
                connection, id=judgment_id, task=UNDO_TASK, left_kind="commitment", left_id=commitment_id,
                judge="learner_card", input_hash=content_key([commitment_id, provenance.get("valuation_ref")]),
                verdict="undone", created_at=stamp,
                rationale=json.dumps({"text": "learner undo of a reader follow-up", "learner_reason": words,
                                      "purpose": provenance.get("purpose"),
                                      "valuation_ref": provenance.get("valuation_ref")},
                                     ensure_ascii=False, sort_keys=True))
    repository.bump_queue_revision(clock=clock)
    return {"commitment_id": commitment_id, "disposition": disposition, "judgment_id": judgment_id}


def undo_all(repository: Repository, *, digest_id: str, reason: str | None = None,
             clock: Clock | None = None) -> dict[str, Any]:
    """Retire every pending follow-up from one session ("undo all")."""

    with repository.connection() as connection:
        row = RDG.digest(connection, digest_id)
    if row is None:
        raise FollowupError(f"unknown session digest {digest_id!r}")
    undone = []
    for commitment_id in row["followup_commitment_ids"]:
        if C.resolve_disposition(repository, commitment_id) == "one_check_pending":
            undone.append(undo_followup(repository, commitment_id=commitment_id, reason=reason, clock=clock))
    return {"digest_id": digest_id, "undone": undone}


def restore_followup(repository: Repository, *, commitment_id: str, clock: Clock | None = None) -> dict[str, Any]:
    """Undo a retirement (re-valuation's or the learner's own undo): the check
    is pending again, and re-valuation leaves it to the learner from then on."""

    _require_followup(repository, commitment_id)
    disposition = C.resolve_disposition(repository, commitment_id)
    if disposition == "stopped":
        repository.append_commitment_event(
            commitment_id=commitment_id, commitment_version_id=None, kind="disposition_changed",
            detail_json=json.dumps({"disposition": "one_check_pending", "reason": "learner_restored"},
                                   sort_keys=True), clock=clock)
        repository.bump_queue_revision(clock=clock)
        disposition = C.resolve_disposition(repository, commitment_id)
    return {"commitment_id": commitment_id, "disposition": disposition}


# ---------------------------------------------------------------------------
# "Coming up" (UX §4.8, S15, D36): a dated timeline, never a count
# ---------------------------------------------------------------------------

def _retirement(repository: Repository, commitment_id: str) -> dict[str, Any] | None:
    latest = None
    for event in _events(repository, commitment_id):
        if event["kind"] == "retired":
            try:
                detail = json.loads(event.get("detail_json") or "{}")
            except ValueError:
                detail = {}
            latest = {"retired_at": event["created_at"], **detail}
        elif event["kind"] == "disposition_changed":
            latest = None
    return latest


def coming_up(vault: LoadedVault, repository: Repository, *, extraction_id: str | None, now: datetime,
              retired_after: str | None = None) -> dict[str, Any]:
    """The scheduled checks as a dated timeline (next three, then later) and
    the retirements since ``retired_after`` as good news. A pure read."""

    with repository.connection() as connection:
        rows = RDG.digests(connection, extraction_id=extraction_id)
    chosen_by_commitment = {entry["commitment_id"]: (row, entry) for row in rows
                            for entry in (row.get("valuation") or {}).get("chosen") or []
                            if entry.get("commitment_id")}
    lines: list[dict[str, Any]] = []
    retired: list[dict[str, Any]] = []
    for row in rows:
        for commitment_id in row["followup_commitment_ids"]:
            try:
                disposition = C.resolve_disposition(repository, commitment_id)
            except C.UnknownCommitment:
                continue
            provenance = _provenance(repository, commitment_id)
            _row, entry = chosen_by_commitment.get(commitment_id, (row, {}))
            purpose = str(provenance.get("purpose") or entry.get("purpose") or PURPOSE_RETENTION)
            lo_ids = (provenance.get("question") or {}).get("learning_object_ids") or []
            base = {
                "commitment_id": commitment_id, "digest_id": row["id"], "extraction_id": row["extraction_id"],
                "purpose": purpose, "novelty": provenance.get("novelty"),
                "novelty_label": NOVELTY_LABELS.get(str(provenance.get("novelty") or "")),
                "purpose_text": purpose_text(vault, purpose, lo_ids, provenance.get("novelty")),
                "expected_minutes": entry.get("expected_minutes"),
                "why": entry.get("why") or SCALE_LABEL,
            }
            if disposition == "one_check_pending":
                due = _due_hint(repository, commitment_id) or entry.get("due_hint")
                lines.append({**base, "date": due, "actions": ["why", "undo"]})
            elif disposition == "stopped":
                info = _retirement(repository, commitment_id)
                if info is None:
                    continue
                if retired_after is not None and str(info.get("retired_at") or "") <= retired_after:
                    continue
                reason = info.get("reason")
                if reason == RETIRE_UNDONE:
                    text = "Undone"
                elif reason == RETIRE_EXPOSED:
                    text = "No longer a check on your own: you've seen this question since it was suggested"
                elif reason == RETIRE_REPAIR_OWNS:
                    text = "No longer needed: a check on your own is already coming up for this"
                elif reason == RETIRE_ANSWERED and info.get("solved_at"):
                    text = "No longer needed: you solved one like it"
                elif reason == RETIRE_ANSWERED:
                    text = "No longer needed: the explanations it was to tell apart are settled"
                else:
                    text = "No longer needed: LearnLoop's estimate says it would tell you little now"
                retired.append({**base, "retired_at": info.get("retired_at"), "reason": reason,
                                "solved_at": info.get("solved_at"), "text": text, "actions": ["undo"]})
    lines.sort(key=lambda line: (str(line.get("date") or "9999"), line["commitment_id"]))
    retired.sort(key=lambda line: (str(line.get("retired_at") or ""), line["commitment_id"]))
    pending_digests = sorted({line["digest_id"] for line in lines})
    return {"followups_version": FOLLOWUPS_VERSION, "enabled": followups_enabled(vault),
            "next": lines[:NEXT_SHOWN], "later": lines[NEXT_SHOWN:], "retired": retired,
            "undo_all": [{"digest_id": d} for d in pending_digests], "scale": SCALE_LABEL}


def _due_hint(repository: Repository, commitment_id: str) -> str | None:
    versions = sorted(repository.commitment_versions_for(commitment_id), key=lambda r: int(r["version"]))
    return next((str(v["due_hint"]) for v in reversed(versions) if v.get("due_hint")), None)


def now_utc(clock: Clock | None = None) -> datetime:
    return (clock or SystemClock()).now()


__all__ = [
    "ENVELOPE",
    "FOLLOWUPS_VERSION",
    "FollowupError",
    "NOVELTY_LABELS",
    "PURPOSE_DISCRIMINATING",
    "PURPOSE_RETENTION",
    "Question",
    "UNDO_TASK",
    "VIA",
    "coming_up",
    "committed_items",
    "constraints_for",
    "date_for",
    "default_search",
    "default_valuer",
    "digest_id_for",
    "exposure_refresh_waiting",
    "followup_spend",
    "followups_enabled",
    "open_questions",
    "pending_cold_retry",
    "plan_ended_sessions",
    "plan_session",
    "purpose_text",
    "refresh_exposure",
    "restore_followup",
    "retention_due",
    "revalue_pending",
    "revealed_families",
    "sessions_to_plan",
    "undo_all",
    "undo_followup",
]
