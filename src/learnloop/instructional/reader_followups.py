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

**No successor** (§9.3 "Why no successor"): the serving algorithm is
unchanged (DL2 serves commitments as it defines them); RW6b adds content the
learner can undo, behind ``followups.enabled``. Nothing here writes evidence.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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
    """``followups.enabled`` (default on)."""

    return bool(getattr(_config(vault), "enabled", True))


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
    for the same claim, i.e. on one of the claim's attempts or on an item of
    the claim's learning objects that carries the facet. Its cold measurement
    answers the claim; a retention follow-up would ask it twice."""

    from learnloop.practice_index.catalog import item_facets

    at = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT id, source_attempt_id, selected_item_id, not_before, expires_at FROM followup_tasks "
            "WHERE kind = 'cold_retry' AND status IN ('pending', 'served') "
            "AND (expires_at IS NULL OR expires_at >= ?) ORDER BY not_before, id", (at,)).fetchall()
    facet = vault.canonical_facet_id(facet_id)
    attempts = {str(a) for a in attempt_ids}
    los = set(learning_object_ids)
    for row in rows:
        if row["source_attempt_id"] and str(row["source_attempt_id"]) in attempts:
            return dict(row)
        item = vault.practice_items.get(str(row["selected_item_id"] or ""))
        if item is not None and item.learning_object_id in los and facet in item_facets(vault, item):
            return dict(row)
    return None


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
    if formative_questions_enabled(vault):
        for record in summary.get("observations") or []:
            raised = {"kind": "formative", "record_kind": record.get("kind"),
                      "source_event_ids": list(record.get("source_event_ids") or [])}
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


def constraints_for(question: Question, *, exclude_family_ids: Sequence[str]) -> dict[str, Any]:
    """The ``PracticeConstraints`` mapping for one question (§9.3 item 2, exactly)."""

    return {
        "intent": question.intent,
        "learning_object_ids": list(question.learning_object_ids),
        "facet_ids": list(question.facet_ids),
        "target_hypotheses": [dict(ref) for ref in question.target_hypotheses],
        "unattempted_only": True,
        "exclude_family_ids": list(exclude_family_ids),
        "exclude_revealed_families": True,
    }


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

    def search(query: str, constraints: Mapping[str, Any], *, caller: Mapping[str, Any]) -> Mapping[str, Any]:
        context = caller_for(repository, "reader", str(caller.get("ref") or ""),
                             learning_object_ids=list(constraints.get("learning_object_ids") or []))
        return propose_practice(vault, repository, query, constraints, caller=context, origin="api",
                                rerank_client=rerank_client, clock=clock, system_initiated=True,
                                **dict(injections))

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
    target = view.target_for(practice_item_id) if view is not None else 0.90
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


def _session_spans(vault: Any, repository: Repository, summary: Mapping[str, Any], learning_object_ids: Sequence[str],
                   extraction_id: str) -> tuple[list[str], list[str]]:
    """The session's inquiry roots and anchor spans on these learning objects (§9.3 item 9)."""

    wanted = set(learning_object_ids)
    inquiries = summary.get("inquiries") or {}
    roots: list[str] = []
    spans: list[str] = []
    seen: set[str] = set()
    for line in [*(inquiries.get("opened") or []), *(inquiries.get("still_open") or []),
                 *(inquiries.get("resolved") or [])]:
        root = str(line.get("root_exchange_id") or "")
        if not root or root in seen:
            continue
        seen.add(root)
        line_spans = [str(s) for s in line.get("span_ids") or []]
        los = {lo for span in line_spans
               for lo in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span)}
        if los & wanted:
            roots.append(root)
            spans.extend(s for s in line_spans if s not in spans)
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


def plan_session(vault: LoadedVault, repository: Repository, *, extraction_id: str, session: RS.ReaderSession,
                 search: Search | None, now: datetime, clock: Clock | None = None) -> dict[str, Any] | None:
    """Plan the follow-ups of one ended reader session; returns its digest row.

    Idempotent per session: a planned session is returned as stored; an
    ``incomplete`` one (a budget or the judge stopped a search) re-asks only
    the questions that did not finish, keeping the commitments it made.
    ``None`` when follow-ups are off or the session had no activity."""

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
    done = {q["key"] for q in previous.get("questions") or [] if not q.get("incomplete")}
    receipt_questions = [q for q in previous.get("questions") or [] if q["key"] in done]
    chosen: list[dict[str, Any]] = list(previous.get("chosen") or [])
    commitment_ids: list[str] = list((existing or {}).get("followup_commitment_ids") or [])
    chosen_refs = {entry["ref"] for entry in chosen}
    worked = [str(line.get("practice_item_id")) for line in summary.get("workbench") or [] if line.get("practice_item_id")]
    attempts = _attempt_rows(repository, [a for q in questions for a in q.attempt_ids])
    source_id = RC._source_id(repository, extraction_id)
    from learnloop.instructional.wiring import disabled_reason

    switched_off = disabled_reason(vault, "discriminating_search")
    incomplete = False
    for question in questions:
        if question.key in done:
            continue
        constraints = constraints_for(question, exclude_family_ids=families)
        entry: dict[str, Any] = {"key": question.key, "question": question.as_dict(), "constraints": constraints}
        if switched_off is not None or search is None:
            entry.update(outcome="unavailable", reason=switched_off or "no_search")
            receipt_questions.append(entry)
            continue
        try:
            with followup_spend(vault, repository, clock):
                result = search(query_for(vault, question), constraints,
                                caller={"kind": VIA, "ref": digest_id})
        except SpendLimitExceeded as exc:
            entry.update(outcome="incomplete", reason="budget", detail=str(exc), incomplete=True)
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
        if _incomplete(result) and not picks:
            entry["incomplete"] = True
            incomplete = True
        if entry.get("outcome") == "no_item":
            entry["generation"] = (
                {"requested": False, "reason": "generate_when_nothing_fits is off"}
                if not getattr(_config(vault), "generate_when_nothing_fits", False)
                else {"requested": False, "reason": "unavailable: PF has no source-anchored request API yet"})
        roots, spans = _session_spans(vault, repository, summary, question.learning_object_ids, extraction_id)
        for section, check in picks:
            ref = str(check["ref"])
            if ref in chosen_refs or ref not in vault.practice_items:
                continue  # licensed by several problems: proposed once
            chosen_refs.add(ref)
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
                             "target_hypotheses": [dict(r) for r in question.target_hypotheses]},
                "followups_version": FOLLOWUPS_VERSION,
            }
            commitment = C.create_commitment(
                repository, action="test_me_later",
                intent_text=purpose_text(vault, question.purpose, lo_ids, novelty),
                targets=[{"target_kind": "legacy_practice_item", "target_ref": ref}],
                depth_preset="keep_in_touch", client_idempotency_key=f"{VIA}:{digest_id}:{ref}",
                author="learnloop", reason=VIA, due_hint=dated["due_hint"], provenance=provenance, clock=clock)
            if commitment.id not in commitment_ids:
                commitment_ids.append(commitment.id)
            chosen.append({
                "ref": ref, "commitment_id": commitment.id, "question": question.key,
                "problem": valuation_ref["problem"], "order": check.get("order"), "purpose": question.purpose,
                "mode": mode, "novelty": novelty, "due_hint": dated["due_hint"], "date_basis": dated["basis"],
                "date_capped": dated["capped"], "regime": check.get("regime"),
                # R1's names (router R3's replay reads both).
                "probe_eig": check.get("robust_eig_nats"), "evsi_assignment": check.get("evsi"),
                "point_eig_nats": check.get("point_eig_nats"), "value_minutes_lcb": check.get("value_minutes_lcb"),
                "expected_minutes": check.get("expected_minutes"),
                "predicted_outcomes": check.get("predicted_outcomes"),
                "why": why_text(question.purpose, check, mode),
            })
        receipt_questions.append(entry)
    valuation = {
        "followups_version": FOLLOWUPS_VERSION, "valuation_version": VALUATION_VERSION,
        "summary_version": summary.get("summary_version"), "scale": SCALE_LABEL,
        "exclude_family_ids": families, "questions": receipt_questions, "notes": notes,
        "chosen": chosen, "chosen_ids": [entry["ref"] for entry in chosen], "planned_at": _iso(now),
    }
    status = "incomplete" if incomplete else "planned"
    stamp = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
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
    if commitment_ids:
        repository.bump_queue_revision(clock=clock)
    with repository.connection() as connection:
        return RDG.digest(connection, digest_id)


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


def revalue_pending(vault: LoadedVault, repository: Repository, *, now: datetime,
                    valuer: Callable[..., Mapping[str, Any]] | None = None, clock: Clock | None = None,
                    force: bool = False) -> dict[str, Any]:
    """Re-value every pending follow-up once a local day, before the plan is
    built. ``valuer(constraints, item_id) -> receipt`` is
    ``discriminating.value_request`` for one item (no model call). Retires a
    follow-up whose question was answered since or that no longer clears the
    stop, with its reason; an excluded or abstaining one is left to DL2
    (which re-checks independence when it serves)."""

    report: dict[str, Any] = {"retired": [], "kept": [], "skipped": None}
    if not followups_enabled(vault):
        report["skipped"] = "followups.enabled is false"
        return report
    today = _today(now)
    with repository.connection() as connection:
        rows = [row for row in RDG.digests(connection) if row.get("followup_commitment_ids")]
    for row in rows:
        if row.get("revalued_on") == today and not force:
            continue
        lines = []
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
            if not question or item_id is None or valuer is None:
                continue
            line = _revaluation_line(vault, repository, commitment_id=commitment_id, item_id=item_id,
                                     provenance=provenance, valuer=valuer, extraction_id=row["extraction_id"],
                                     clock=clock)
            lines.append(line)
            report["retired" if line["retired"] else "kept"].append(line)
        with repository.atomic():
            RDG.update_digest(repository.connection(), row["id"], revaluation_json={
                "revalued_at": _iso(now), "followups_version": FOLLOWUPS_VERSION, "lines": lines},
                revalued_on=today, updated_at=utc_now_iso(clock))
    if report["retired"]:
        repository.bump_queue_revision(clock=clock)
    return report


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


def _revaluation_line(vault: Any, repository: Repository, *, commitment_id: str, item_id: str,
                      provenance: Mapping[str, Any], valuer: Callable[..., Mapping[str, Any]],
                      extraction_id: str, clock: Clock | None) -> dict[str, Any]:
    question = provenance.get("question") or {}
    line: dict[str, Any] = {"commitment_id": commitment_id, "item_id": item_id, "retired": False}
    created = str(_first_version(repository, commitment_id).get("created_at") or "")
    answered = answered_since(vault, repository, question, since=created)
    if answered is not None:
        detail = {"reason": RETIRE_ANSWERED, **answered, "extraction_id": extraction_id,
                  "followups_version": FOLLOWUPS_VERSION}
        C.retire(repository, commitment_id=commitment_id, detail=detail, clock=clock)
        line.update(retired=True, reason=RETIRE_ANSWERED, detail=detail)
        return line
    receipt = dict(valuer(question, item_id))
    sections = list(receipt.get("problems") or [])
    line["verdicts"] = sorted({str(s.get("verdict")) for s in sections})
    excluded = (receipt.get("excluded") or {}).get(item_id)
    if not sections:
        line["kept_because"] = sorted({str(u.get("reason")) for u in receipt.get("unavailable") or []}) or [
            "no_problem"]
        return line
    if excluded is not None:
        line["kept_because"] = ["excluded_at_revaluation: DL2 re-checks independence at serve", *excluded]
        return line
    still = any(str(check.get("ref")) == item_id for section in sections
                if section.get("verdict") in CHECK_VERDICTS for check in section.get("checks") or [])
    if still:
        line["kept_because"] = ["clears_the_stop"]
        return line
    if all(section.get("verdict") == "stop" for section in sections):
        detail = {"reason": RETIRE_BELOW_STOP, "extraction_id": extraction_id,
                  "stop_reasons": sorted({str(s.get("reason")) for s in sections}),
                  "followups_version": FOLLOWUPS_VERSION}
        C.retire(repository, commitment_id=commitment_id, detail=detail, clock=clock)
        line.update(retired=True, reason=RETIRE_BELOW_STOP, detail=detail)
        return line
    # An abstention (a flip, no licensing regime now) is not an answer: the
    # check stays the learner's, recorded.
    line["kept_because"] = sorted({str(s.get("reason")) for s in sections if s.get("reason")}) or ["abstain"]
    return line


def default_valuer(vault: LoadedVault, repository: Repository, *, estimator: Any | None = None
                   ) -> Callable[[Mapping[str, Any], str], Mapping[str, Any]]:
    """``discriminating.value_request`` for one committed item, system-initiated,
    on the same switch the search used (no model call: no screen, no judge)."""

    from learnloop.diagnosis.probe_robust import resolve_episode_channel
    from learnloop.instructional.discriminating import value_request
    from learnloop.practice_index.retrieval import PracticeConstraints

    def valuer(question: Mapping[str, Any], item_id: str) -> Mapping[str, Any]:
        constraints = PracticeConstraints.from_mapping({
            "intent": question.get("intent") or "retention",
            "learning_object_ids": list(question.get("learning_object_ids") or []),
            "facet_ids": list(question.get("facet_ids") or []),
            "target_hypotheses": [dict(r) for r in question.get("target_hypotheses") or []],
        })
        return value_request(vault, repository, constraints, items=[item_id], exercises=[],
                             caller_kind=VIA, system_initiated=True, estimator=estimator,
                             channel_resolver=resolve_episode_channel)

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
    check, not the subject). Idempotent: an already retired one is returned."""

    provenance, row = _require_followup(repository, commitment_id)
    disposition = C.resolve_disposition(repository, commitment_id)
    words = " ".join(str(reason or "").split())[:UNDO_REASON_CHARS] or None
    judgment_id = "rfu_" + content_key([commitment_id, "undone"])[:40]
    if disposition == "stopped":
        return {"commitment_id": commitment_id, "disposition": disposition, "judgment_id": judgment_id}
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
    "constraints_for",
    "date_for",
    "default_search",
    "default_valuer",
    "digest_id_for",
    "followup_spend",
    "followups_enabled",
    "open_questions",
    "pending_cold_retry",
    "plan_ended_sessions",
    "plan_session",
    "purpose_text",
    "restore_followup",
    "retention_due",
    "revalue_pending",
    "revealed_families",
    "sessions_to_plan",
    "undo_all",
    "undo_followup",
]
