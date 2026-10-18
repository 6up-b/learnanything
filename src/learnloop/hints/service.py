"""Adaptive hints H2a: the hint service, ``request_hint`` (spec §4.1, §4.5-§4.7, §5, §6.2, §7, §9).

One function every surface calls; none writes hint text of its own. H2a
serves the practice screen (no UI yet: H2b adds the panel).

**The flow.** A request is validated (the hint a reply answers must be a
shown hint of this submission); a "doesn't connect" reply first appends its
``learner_card`` verdict ``different`` on task ``hint_fit`` (its subject the
answered hint's ``help_assists`` row); the state is assembled from local reads
(:mod:`learnloop.hints.state`); the options are built
(:mod:`learnloop.hints.options`); the writer's route is checked BEFORE the
chooser is asked (a Codex, unpriced or capped writer spends nothing and the
item's authored hints serve, saying why, for "More" and for a level-3 reply
an authored hint can honour: a reply never raises the level); the chooser
picks (:mod:`learnloop.hints.chooser`); the writer writes and its contracts
and leak control are checked in code (re-asked once naming the failure, then
a level-3 ``next_step`` downgrade, never for a reply or pick fixed at level 1
or 2; a leak re-asked once, then withheld; a route-directed hint on work
placed on no route and not clearly valid becomes an approach question, or,
for the book's way and worked help, starts from the givens, §4.4); the
``help_assists`` row is written **prepared** (``shown = 0``).

**Shown when delivered.** :func:`deliver_hint` marks the prepared row shown
(once, while its submission has committed no attempt): the moment the
surface receives the hint; any other outcome sends no hint text. A
cancelled request (the screen took the item's own hint instead) or a hint
never delivered stays ``shown = 0`` and counts nothing (G-H3); a withheld one
is never deliverable.

**Help, never evidence** (H1, ``hints-never-write-evidence``). This module
writes ``help_assists``, ``judgment_ledger`` (``hint_choice``, ``hint_fit``)
and receipts. The fold of shown rows into ``hints_used`` / ``primed`` at
submit, and the ``tutor_answer`` reveal of a delivered hint's key overlap,
live in the sidecar's submit and delivery paths with their existing meaning
(§5); nothing here reads or writes an attempt, a reveal, mastery, FSRS or
certification.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field, replace
import json
import logging
import time
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import call_labels, content_key
from learnloop.ai.spend import SpendLimitExceeded, spend_envelopes
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.hints import chooser as chooser_module
from learnloop.hints.chooser import Choice
from learnloop.hints.contracts import (
    Check,
    Target,
    at_givens,
    check_output,
    leak_flags,
    reference_route_id,
    route_distance,
)
from learnloop.hints.discriminating import (
    WEIGHTS_BASIS,
    best_candidate,
    normalize_answer,
    rank_candidates,
    states_a_rival,
)
from learnloop.hints.kinds import (
    AI_WRITTEN,
    FROM_THE_ITEM,
    GRAIN,
    KINDS,
    NO_SEPARATING_QUESTION,
    REQUESTS,
    SHORTCUTS,
    WITHHELD_MESSAGE,
    WORKED_LEVELS,
    labels_for,
    worked_help_picks,
)
from learnloop.hints.options import OptionSet, build_options
from learnloop.hints.state import EarlierHint, HintState, assemble_state, rivals_payload
from learnloop.hints.writer import (
    PROMPT_VERSION as WRITER_PROMPT_VERSION,
    HintWriterOutputV1,
    WriterRoute,
    WriterUnavailable,
    build_prompt,
    models_off,
)
from learnloop.ids import new_ulid
from learnloop.source_retrieval.service_spend import SharedDailyEnvelope, midnight
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import LoadedVault, PracticeItem

LOG = logging.getLogger(__name__)

REQUEST_VERSION = "hint_request.v1"
RESULT_VERSION = "hint_result.v1"
#: The daily cap's envelope in the vault's spend ledger, and the receipts it counts.
ENVELOPE = "hints.max_daily_cost_usd"
OWNER_KINDS = ("hint_chooser", "hint_writer")
#: ``judgment_ledger``: the "doesn't connect" replies (judge ``learner_card``).
FIT_TASK = "hint_fit"
FIT_VERSION = "hint-fit-v1"
SURFACE = "practice"

#: Result statuses. ``ready``: a hint is prepared for delivery. ``withheld``:
#: it would give the answer away (shown never). ``unavailable``: nothing could
#: be served (``reason`` says why). ``disabled``: adaptive hints are off (the
#: surface keeps the item's own hints exactly as before). ``refused``: a
#: diagnostic block (no model call). ``cancelled``: the request was cancelled.
READY, WITHHELD, UNAVAILABLE, DISABLED, REFUSED, CANCELLED = (
    "ready", "withheld", "unavailable", "disabled", "refused", "cancelled")


class HintRequestError(ValueError):
    """A request the service refuses as malformed (``code`` names the field)."""

    def __init__(self, code: str, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.field = field


@dataclass(frozen=True)
class HintRequestV1:
    """One hint request (§4.1). ``work_md`` None: the session checkpoint's draft."""

    practice_item_id: str
    session_id: str
    submission_id: str
    surface: str = SURFACE
    work_md: str | None = None
    #: ``more`` | ``feedback`` | ``book_way`` | ``smaller_step``
    request: str = "more"
    #: The hint a reply or a pick answers (required for all but ``more``).
    answered_assist_id: str | None = None
    feedback_shortcut: str | None = None
    feedback_text: str | None = None
    #: ``not_where_stuck``: the part of the draft the learner means.
    feedback_selection: str | None = None
    #: The worked-help picks: 4 (*work a piece of it for me*) or 5 (*show me the worked answer*).
    taken_level: int | None = None
    seconds_on_item: float | None = None
    version: str = REQUEST_VERSION


@dataclass
class HintResultV1:
    """What the surface shows (§4.1, §4.8)."""

    status: str
    assist_id: str | None = None
    hint_md: str | None = None
    kind: str | None = None
    level: int | None = None
    horizon: int | None = None
    #: The waypoint's horizon in the rubric (0 next step ... 3 the goal).
    horizon_index: int | None = None
    placement: dict[str, Any] | None = None
    labels: dict[str, Any] = field(default_factory=dict)
    #: What the hint carries (§5): ``counts_as_hint`` (levels 1-3) or ``primed`` (4-5).
    evidence: dict[str, Any] = field(default_factory=dict)
    discriminating: dict[str, Any] | None = None
    authored_index: int | None = None
    chooser: str | None = None
    propensity: float | None = None
    reason: str | None = None
    message: str | None = None
    #: The quiet lines under the hint and the worked-help picks (§4.8).
    replies: list[str] = field(default_factory=list)
    picks: list[dict[str, Any]] = field(default_factory=list)
    version: str = RESULT_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def adaptive_enabled(config: Any) -> bool:
    """Adaptive hints are on: their kill switch and the telemetry their rows
    need (a shown hint is counted at submit from its row)."""

    return bool(config.hints.adaptive_enabled) and bool(config.hints.telemetry_enabled)


def hints_envelope(vault: LoadedVault, repository: Repository, *, clock: Clock | None = None) -> SharedDailyEnvelope:
    """``hints.max_daily_cost_usd`` as RW4a/H1's durable daily cap (every
    process), counting the chooser's and writer's metered receipts at
    ``hints.price_per_million``; subscription receipts are ``estimated_only``."""

    return SharedDailyEnvelope(
        vault, repository, day=midnight(clock), cap=float(vault.config.hints.max_daily_cost_usd), clock=clock,
        name=ENVELOPE, owner_kinds=OWNER_KINDS, price_per_million=vault.config.hints.price_per_million)


def default_chooser_client(vault: LoadedVault) -> Any | None:
    """The ready Decider of ``ai.routing.hint_chooser`` (never a chat
    fallback, never ``LEARNLOOP_AI_PROVIDER``), or None."""

    if models_off():
        return None
    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(vault.root, vault.config, "hint_chooser", allow_env=False)
    return resolved.client if resolved.ready else None


def reveal_basis(kind: str, level: int) -> str:
    """The ``reveal_events`` basis of a hint shown on the practice screen (§5)."""

    return f"hint:{kind}:L{level}"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _active_item(vault: LoadedVault, item_id: str) -> PracticeItem:
    item = vault.practice_items.get(item_id)
    if item is None:
        raise HintRequestError("not_found", f"Practice item {item_id} not found.", field="practiceItemId")
    if item.status != "active":
        raise HintRequestError("item_retired", f"Practice item {item_id} is retired.", field="practiceItemId")
    return item


def _answered(state: HintState, request: HintRequestV1) -> EarlierHint | None:
    if request.request == "more":
        return None
    if not request.answered_assist_id:
        raise HintRequestError("validation_error", f"A {request.request} request names the hint it answers.",
                               field="answeredAssistId")
    for hint in state.earlier:
        if hint.assist_id == request.answered_assist_id:
            if hint.assist_kind != "hint" or not hint.shown:
                break
            return hint
    raise HintRequestError("validation_error", "The answered hint is not a shown hint of this attempt.",
                           field="answeredAssistId")


def _validate(request: HintRequestV1) -> None:
    if request.surface != SURFACE:
        raise HintRequestError("validation_error", "H2a serves the practice screen only.", field="surface")
    if request.request not in REQUESTS:
        raise HintRequestError("validation_error", f"Unknown request {request.request!r}.", field="request")
    if request.feedback_shortcut is not None and request.feedback_shortcut not in SHORTCUTS:
        raise HintRequestError("validation_error", f"Unknown shortcut {request.feedback_shortcut!r}.",
                               field="feedbackShortcut")
    if request.feedback_shortcut is not None and request.request != "feedback":
        raise HintRequestError("validation_error", "A shortcut belongs to a feedback reply.",
                               field="feedbackShortcut")
    if request.taken_level is not None:
        if request.taken_level not in WORKED_LEVELS:
            # A Hint press serves levels 1-3; only worked help is taken (D17).
            raise HintRequestError("validation_error", "Only worked help (level 4 or 5) is taken on this surface.",
                                   field="takenLevel")
        if request.request != "more":
            raise HintRequestError("validation_error", "A worked-help pick is its own request.", field="takenLevel")
    if not request.submission_id.strip():
        raise HintRequestError("validation_error", "A hint request needs the attempt's submission key.",
                               field="submissionId")


# ---------------------------------------------------------------------------
# The decision and the writing
# ---------------------------------------------------------------------------

@dataclass
class _Served:
    """What one request produced, before it is written."""

    outcome: str
    kind: str | None = None
    level: int | None = None
    text: str | None = None
    output: HintWriterOutputV1 | None = None
    authored_index: int | None = None
    horizon_index: int | None = None
    rounds: list[dict[str, Any]] = field(default_factory=list)
    leaks: list[str] = field(default_factory=list)
    reason: str | None = None
    message: str | None = None
    discriminating: dict[str, Any] | None = None
    model: str | None = None
    prompt: str | None = None
    latency_ms: int | None = None


def _check_round(output: HintWriterOutputV1, target: Target, state: HintState, item: PracticeItem
                 ) -> tuple[Check, HintWriterOutputV1, str, dict[str, Any] | None]:
    """Check one writer answer; returns the check, the answer as served (a
    discriminating question's text), the served kind and, for
    ``discriminating``, its ranking."""

    if target.kind != "discriminating":
        return check_output(output, target=target, state=state, item=item), output, target.kind, None
    ranked = rank_candidates([candidate.model_dump() for candidate in output.candidates], state.rivals)
    record: dict[str, Any] = {"weights_basis": WEIGHTS_BASIS, "rivals": rivals_payload(state.rivals),
                              "weights": {rival.id: 1.0 / len(state.rivals) for rival in state.rivals}
                              if state.rivals else {},
                              "candidates": [entry.as_dict() for entry in ranked]}
    positive = [entry for entry in ranked if entry.eig_nats > 0]
    usable = None
    rejected: list[str] = []
    for entry in positive:
        if best_candidate([entry]) is None:
            continue
        if states_a_rival(entry.question_md, state.rivals) is not None:
            rejected.append("discriminating_states_a_rival")
            continue
        if leak_flags([entry.question_md], item=item, current=state.map, level=target.level):
            rejected.append("discriminating_question_leaks")
            continue
        usable = entry
        break
    if usable is not None:
        served = output.model_copy(update={"hint_md": usable.question_md})
        check = check_output(served, target=target, state=state, item=item)
        record.update(chosen_index=usable.index, eig_nats=usable.eig_nats, predictions=usable.predictions)
        return check, served, "discriminating", record
    if positive and rejected:
        check = Check()
        for code in rejected:
            check.fail(code)
        return check, output, "discriminating", record
    # No positive EIG: §4.2's downgrade, saying why.
    served_kind = "approach_question" if target.level == 1 else "next_step"
    why = NO_SEPARATING_QUESTION[1 if target.level == 1 else 3]
    text = f"{why}\n\n{output.fallback_hint_md}".strip()
    served = output.model_copy(update={"hint_md": text if output.fallback_hint_md.strip() else ""})
    # Only the kind changes: every placement constraint of the target (the
    # waypoint's node, the reference route, from the givens) holds for the
    # fallback hint too (round 3, W4).
    downgraded = replace(target, kind=served_kind)
    check = check_output(served.model_copy(update={"hint_md": output.fallback_hint_md}), target=downgraded,
                         state=state, item=item)
    record.update(chosen_index=None, eig_nats=0.0, no_positive_eig=True, served_kind=served_kind)
    return check, served, served_kind, record


def _write(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState, target: Target,
           writer: WriterRoute, *, request: HintRequestV1, assist_id: str,
           cancelled: Callable[[], bool]) -> _Served:
    """Ask, check, re-ask once naming the failure; then the level-3
    ``next_step`` downgrade (§4.6), except where it would raise a fixed level
    (:func:`downgrade_allowed`: then nothing is served); a leak re-asked
    once, then withheld. A checked route-directed answer on unplaceable work
    switches to an approach question, or for ``book_way`` and worked help to
    the same option from the givens on the reference route (§4.4,
    :func:`unplaced_work`), asked and re-asked once (at most four writer
    calls)."""

    started = time.monotonic()
    served = _Served(outcome="failed")
    metadata = {"practice_item_id": item.id, "assist_id": assist_id, "prompt_version": WRITER_PROMPT_VERSION}
    feedback: dict[str, Any] | None = None
    current = target
    downgraded = False
    unplaced = False
    may_downgrade = downgrade_allowed(target, request)
    last_round = 3 if may_downgrade else 2
    round_ = 0
    while round_ < last_round:
        round_ += 1
        if cancelled():
            served.outcome, served.reason = CANCELLED, "cancelled"
            break
        if round_ == 3 and not unplaced and may_downgrade:
            # The re-ask failed a rule (not a leak): a level-3 next step from
            # the last valid checkpoint, without its unverified claims.
            # Every other constraint of the target is kept (round 3, W4).
            current = replace(target, kind="next_step", level=3, horizon_index=None,
                              target_node_id=target.target_node_id if target.level == 3 else None, downgrade=True)
            downgraded = True
            feedback = None
        prompt = build_prompt(vault, item, state, current, request_text=request.feedback_text,
                              selection=request.feedback_selection, feedback=feedback, request_id=assist_id)
        served.prompt = prompt
        with call_labels(judge="llm", question_set_version=WRITER_PROMPT_VERSION, state_hash=state.state_hash()):
            output = writer.ask(prompt, owner_id=assist_id, metadata={**metadata, "round": round_})
        check, as_served, served_kind, record = _check_round(output, current, state, item)
        served.rounds.append({"round": round_, "kind": current.kind, "level": current.level,
                              "failures": list(check.failures), "leaks": list(check.leaks)})
        if record is not None:
            served.discriminating = record
        placement_rule = unplaced_work(as_served, served_kind, current, state, request) \
            if check.ok and not unplaced else None
        if placement_rule == APPROACH_INSTEAD:
            # §4.4: work unlike any route and not clearly valid gets an
            # approach question about what the learner is trying, never a
            # confident hint toward a route they are not on (review F7; for
            # every request, round 2 V3: levels 1-3 count alike, so a reply
            # or a pick is lowered, never raised). The row keeps the drawn
            # option and records the served kind.
            unplaced, downgraded = True, True
            served.rounds[-1]["switched_to"] = "approach_question"
            served.reason = UNPLACED_WORK
            served.message = UNPLACED_MESSAGE
            # An approach question aims at no node and claims no horizon;
            # the request, its reply and route constraints are kept (round 3, W4).
            current = replace(target, kind="approach_question", level=1, horizon_index=None,
                              target_node_id=None, downgrade=False)
            feedback = None
            last_round = min(4, round_ + 2)
            continue
        if placement_rule == AT_GIVENS:
            # Already at the givens: accepted only under the whole from-givens
            # contract (round 3, W3), else re-asked from the givens.
            strict = replace(current, from_givens=True, reference_route=True, downgrade=False)
            strict_round = _check_round(output, strict, state, item)
            served.rounds[-1]["from_givens_failures"] = list(strict_round[0].failures)
            if strict_round[0].ok:
                check, as_served, served_kind, record = strict_round
                if record is not None:
                    served.discriminating = record
                current = strict
                served.reason, served.message = UNPLACED_WORK, FROM_GIVENS_MESSAGE
            else:
                placement_rule = FROM_GIVENS
        if placement_rule == FROM_GIVENS:
            # §4.4 (round 2, V3): the book's way, or worked help the learner
            # took, on unplaceable work starts from the givens on the
            # reference route: the option is kept, its placement is not.
            unplaced = True
            served.rounds[-1]["switched_to"] = "from_givens"
            served.reason = UNPLACED_WORK
            served.message = FROM_GIVENS_MESSAGE
            current = replace(current, from_givens=True, reference_route=True, downgrade=False)
            feedback = None
            last_round = min(4, round_ + 2)
            continue
        if check.ok:
            served.outcome = "downgraded" if downgraded else "served"
            served.kind, served.level, served.output = served_kind, current.level, as_served
            served.text = as_served.hint_md
            served.horizon_index = current.horizon_index
            if (current.level == 3 and served_kind in ("next_step", "waypoint", "subgoal_plan", "error_specific")
                    and 0 <= as_served.authored_index < len(item.hints)
                    and as_served.authored_index not in state.authored_revealed
                    and not leak_flags([item.hints[as_served.authored_index]], item=item, current=state.map,
                                       level=3)):
                # The writer judged one of the item's own hints fits (§4.7):
                # served verbatim, labelled "from the item".
                served.kind, served.authored_index = "authored", as_served.authored_index
                served.text = item.hints[as_served.authored_index]
            break
        if check.leaks and round_ >= 2:
            served.outcome, served.leaks = WITHHELD, list(check.leaks)
            served.kind, served.level, served.output, served.text = served_kind, current.level, as_served, \
                as_served.hint_md
            break
        if round_ == last_round:
            served.outcome, served.reason = "failed", "contract_failed"
            if not may_downgrade and not unplaced:
                served.message = NO_FITTING_HINT_MESSAGE
            break
        feedback = {"failures": list(check.failures), "leaks": list(check.leaks),
                    "previous_answer": output.model_dump(mode="json")}
    served.model = writer.model
    served.latency_ms = int((time.monotonic() - started) * 1000)
    return served


#: §4.4's unplaceable work (review F7): the reason and the line it carries.
UNPLACED_WORK = "unplaced_work"
UNPLACED_MESSAGE = "Your work doesn't follow a route I can place yet, so here is a question about your approach."
FROM_GIVENS_MESSAGE = "Your work doesn't follow a route I can place yet, so this starts from the givens."
#: §4.6's downgrade refused for a fixed level 1 or 2 (review round 2, V2).
NO_FITTING_HINT_MESSAGE = "I couldn't write a hint that fits here; press Hint again or use the item's hint."
#: The kinds that point along a route (a goal, a plan, a step, a correction
#: there, the next part, the same move elsewhere): what unplaceable work must
#: not get (§4.4; review F7 and round 2, V3).
ROUTE_DIRECTED_KINDS = frozenset({"waypoint", "subgoal_plan", "next_step", "error_specific", "continuation",
                                  "worked_parallel"})
#: :func:`unplaced_work`'s answers.
APPROACH_INSTEAD, FROM_GIVENS, AT_GIVENS = "approach_question", "from_givens", "at_givens"


def downgrade_allowed(target: Target, request: HintRequestV1) -> bool:
    """Whether §4.6's level-3 ``next_step`` downgrade may answer this request
    (review round 2, V2). A reply or a pick (``feedback``, ``smaller_step``,
    ``book_way``) is answered at the level of the hint it answers (§4.2,
    G-H15), so at a fixed level 1 or 2 the downgrade would raise it: nothing
    is served instead. A fixed level 3 keeps it, a fixed 4-5 is lowered by
    it, and "More" keeps §4.6 as it is. The fixed level is the answered
    hint's, never the chosen target's (round 3, W2: an option fallback may
    already have raised the target)."""

    if request.request == "more":
        return True
    answered = target.answered
    level = int(getattr(answered, "level", None) or 3) if answered is not None else target.level
    return level >= 3


def unplaced_work(output: HintWriterOutputV1, served_kind: str, target: Target, state: HintState,
                  request: HintRequestV1) -> str | None:
    """What a checked answer on work the writer placed on no route and found
    not clearly valid (both flags false), with a map to place it on, becomes
    (§4.4; review F7, round 2 V3), or None when it is served as written.

    No route-directed help (:data:`ROUTE_DIRECTED_KINDS`) is aimed from such
    work for any request. ``book_way`` (the learner asked for the book's way)
    and worked help (levels 4-5, which the learner took) keep their option and
    start from the givens on the reference route: :data:`FROM_GIVENS`, or
    :data:`AT_GIVENS` when the answer already does. Every other request gets
    the approach question at level 1 (:data:`APPROACH_INSTEAD`): levels 1-3
    count alike, so it lowers a reply's level and never raises it."""

    placement = output.placement
    if target.from_givens or not state.has_work or state.map is None:
        return None
    if placement.work_matches_a_route or placement.work_valid_so_far:
        return None
    worked = target.level in WORKED_LEVELS
    if served_kind not in ROUTE_DIRECTED_KINDS and not worked:
        return None
    if request.request == "book_way" or worked:
        reference = reference_route_id(state.map)
        on_reference = not output.route_id or output.route_id == reference
        return AT_GIVENS if on_reference and at_givens(state.map, placement.reached_node_id) else FROM_GIVENS
    return APPROACH_INSTEAD


def _authored(item: PracticeItem, state: HintState, *, index: int | None = None) -> _Served:
    remaining = state.authored_remaining(item)
    chosen = index if index is not None else (remaining[0] if remaining else None)
    if chosen is None or chosen >= len(item.hints):
        return _Served(outcome="failed", reason="no_authored_hint_left")
    text = item.hints[chosen]
    leaks = leak_flags([text], item=item, current=state.map, level=3)
    if leaks:
        return _Served(outcome=WITHHELD, kind="authored", level=3, text=text, authored_index=chosen, leaks=leaks)
    return _Served(outcome="served", kind="authored", level=3, text=text, authored_index=chosen)


def _append_fit(repository: Repository, answered: EarlierHint, request: HintRequestV1, *,
                clock: Clock | None) -> str:
    """A "doesn't connect" reply: one ``learner_card`` verdict ``different``
    on ``hint_fit``, its subject the answered hint's row (which carries the
    surface). Its text stays on the next hint's row (learner text, §9)."""

    rationale = {"shortcut": request.feedback_shortcut, "has_text": bool((request.feedback_text or "").strip()),
                 "surface": SURFACE, "answered_kind": answered.hint_kind, "answered_level": answered.level}
    with repository.atomic():
        return append_judgment(
            repository.connection(), task=FIT_TASK, left_kind="help_assist", left_id=answered.assist_id,
            judge="learner_card", input_hash=content_key({"answered": answered.assist_id,
                                                         "shortcut": request.feedback_shortcut,
                                                         "text": request.feedback_text or ""}),
            verdict="different", prompt_version=FIT_VERSION, rationale=json.dumps(rationale, sort_keys=True),
            created_at=utc_now_iso(clock))


def request_hint(
    vault: LoadedVault,
    repository: Repository,
    request: HintRequestV1,
    *,
    writer_client: Any | None = None,
    chooser_client_factory: Callable[[], Any] | None = None,
    seed: str | None = None,
    clock: Clock | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> HintResultV1:
    """One hint request (§4.1). The row is written prepared (``shown = 0``);
    :func:`deliver` shows it. Raises :class:`HintRequestError` on a malformed
    request; a model failure never raises (the fallback serves)."""

    if not adaptive_enabled(vault.config):
        return HintResultV1(status=DISABLED, reason="adaptive_disabled",
                            message="Adaptive hints are off; the item's own hints are shown as before.")
    _validate(request)
    item = _active_item(vault, request.practice_item_id)
    is_cancelled = cancelled or (lambda: False)
    requested_at = utc_now_iso(clock)
    assist_id = "ha_" + new_ulid()
    map_record = None
    try:
        from learnloop.hints.map_builder import current_map

        map_record = current_map(vault, repository, item.id)
    except Exception:  # noqa: BLE001 - hints work without a map (§4.4)
        LOG.debug("hint map read failed", exc_info=True)
    state = assemble_state(vault, repository, item, session_id=request.session_id,
                           submission_id=request.submission_id.strip(), work_md=request.work_md,
                           seconds_on_item=request.seconds_on_item, now_iso=requested_at,
                           map_record=map_record, map_loaded=True)
    answered = _answered(state, request)
    if request.request == "smaller_step" and (answered is None or answered.hint_kind != "waypoint"):
        raise HintRequestError("validation_error", "A smaller step answers a goal to aim for (a waypoint).",
                               field="answeredAssistId")
    fit_id = None
    if request.request == "feedback" and answered is not None:
        fit_id = _append_fit(repository, answered, request, clock=clock)
    option_set = build_options(state, request=request.request, answered=answered,
                               shortcut=request.feedback_shortcut, taken_level=request.taken_level)
    envelope = hints_envelope(vault, repository, clock=clock)
    writer = WriterRoute(vault, repository, client=writer_client, envelope=envelope)
    problem = writer.problem()
    choice: Choice | None
    served: _Served
    if not option_set.options:
        choice, served = None, _Served(outcome="failed", reason="no_option")
        if answered is not None and int(answered.level or 3) < 3:
            # A reply or pick fixed at level 1 or 2 with nothing left at that
            # level: V2's honest answer, never a higher level (round 3, W2).
            served.message = NO_FITTING_HINT_MESSAGE
    elif problem is not None:
        choice = None
        served = _writer_down(item, state, option_set, request, problem.reason, problem.message)
    else:
        choice = _choose(vault, repository, state, option_set, request, assist_id=assist_id, seed=seed,
                         client_factory=chooser_client_factory, envelope=envelope, clock=clock)
        if choice is None:
            served = _Served(outcome="failed", reason="no_option")
        elif choice.kind == "authored":
            served = _authored(item, state, index=choice.authored_index)
        else:
            target = Target(choice.kind, choice.level, choice.horizon_index,
                            target_node_id=option_set.target_node_id if choice.level == 3 else None,
                            reference_route=option_set.reference_route, request=request.request,
                            shortcut=request.feedback_shortcut, answered=answered)
            try:
                served = _write(vault, repository, item, state, target, writer, request=request,
                                assist_id=assist_id, cancelled=is_cancelled)
            except AIInterrupted:
                raise
            except WriterUnavailable as exc:
                served = _writer_down(item, state, option_set, request, exc.reason, exc.message)
            except SpendLimitExceeded as exc:
                served = _writer_down(item, state, option_set, request, "capped", str(exc))
            except (AIProviderUnavailable, AIInvalidOutput, TimeoutError) as exc:
                served = _writer_down(item, state, option_set, request, "writer_failed",
                                      f"{type(exc).__name__}: {exc}"[:300])
    if is_cancelled() and served.outcome not in (WITHHELD,):
        served.outcome, served.reason = CANCELLED, "cancelled"
    row = _row(vault, item, state, request, option_set, choice, served, assist_id=assist_id,
               requested_at=requested_at, map_record=map_record)
    with repository.atomic():
        store.insert_assist(repository.connection(), row)
    return _result(item, state, option_set, choice, served, assist_id=assist_id, fit_id=fit_id)


def _writer_down(item: PracticeItem, state: HintState, option_set: OptionSet, request: HintRequestV1,
                 reason: str, message: str) -> _Served:
    """No hint can be written (D9's Codex refusal, a capped day, an unpriced
    or failing route): the item's authored hints serve while they last, saying
    why; worked help and a reply on a hint with none left get nothing."""

    if authored_fallback_allowed(option_set, request) and state.authored_remaining(item):
        served = _authored(item, state)
        if served.outcome == "served":
            served.reason, served.message = reason, message
            return served
    return _Served(outcome="failed", reason=reason, message=message)


def authored_fallback_allowed(option_set: OptionSet, request: HintRequestV1) -> bool:
    """Whether an authored hint (level 3) may answer this request while the
    writer cannot run (review F5): "More" (levels 1-3 are offered), or a reply
    to a level-3 hint whose shortcut an authored hint can honour. A reply is
    answered at the level of the hint it answers (§4.2, D15), so a reply to a
    level-1 or level-2 hint gets nothing rather than more help; "the notation"
    (the learner's symbols) and "a different approach" (their work quoted)
    ask for what only a written hint does; "too big a jump" needs a finer
    kind than the answered one. Worked help and the learner's picks are never
    an authored hint (deviation 9)."""

    if option_set.taken_level is not None:
        return False
    if request.request == "more":
        return True
    if request.request != "feedback" or option_set.answered is None:
        return False
    answered = option_set.answered
    if int(answered.level or 3) != 3:
        return False
    shortcut = request.feedback_shortcut
    if shortcut in (None, "not_where_stuck"):
        return True
    if shortcut == "too_big":
        return GRAIN["authored"] > GRAIN.get(str(answered.hint_kind or ""), 0)
    return False


def _choose(vault: LoadedVault, repository: Repository, state: HintState, option_set: OptionSet,
            request: HintRequestV1, *, assist_id: str, seed: str | None, client_factory: Callable[[], Any] | None,
            envelope: SharedDailyEnvelope, clock: Clock | None) -> Choice | None:
    item = vault.practice_items[state.practice_item_id]
    if option_set.learner_pick is not None:
        return chooser_module.learner_pick_choice(option_set)
    if len(option_set.options) == 1:
        return chooser_module.single_option_choice(option_set)
    if not vault.config.hints.chooser_enabled:
        return chooser_module.fallback_choice(option_set, state, item, request=request.request,
                                              shortcut=request.feedback_shortcut, reason="chooser_disabled")
    factory = client_factory or (lambda: default_chooser_client(vault))
    with spend_envelopes(envelope):
        choice = chooser_module.ask(config=vault.config, repository=repository, state=state, option_set=option_set,
                                    request=request.request, shortcut=request.feedback_shortcut,
                                    assist_id=assist_id, client_factory=factory, seed=seed, clock=clock)
    if choice.chooser != "fallback":
        return choice
    fallback = chooser_module.fallback_choice(option_set, state, item, request=request.request,
                                              shortcut=request.feedback_shortcut, reason=str(choice.reason))
    if fallback is not None:
        fallback.judgment_id, fallback.model, fallback.latency_ms = choice.judgment_id, choice.model, choice.latency_ms
        fallback.probabilities, fallback.seed = choice.probabilities, choice.seed
    return fallback


def _horizon(state: HintState, served: _Served) -> int | None:
    output = served.output
    if served.kind != "waypoint" or output is None or state.map is None:
        return None
    start = output.placement.reached_node_id
    if not start:
        path = next((route.get("path") for route in state.map.get("routes") or ()
                     if str(route.get("id")) == output.route_id), None)
        start = str(path[0]) if path else ""
    distance = route_distance(state.map, output.route_id, start, output.target_node_id) if start else None
    return distance if distance and distance >= 1 else None


def _json(value: Any) -> str | None:
    return None if value is None else json.dumps(value, sort_keys=True, default=str)


def _row(vault: LoadedVault, item: PracticeItem, state: HintState, request: HintRequestV1, option_set: OptionSet,
         choice: Choice | None, served: _Served, *, assist_id: str, requested_at: str,
         map_record: Mapping[str, Any] | None) -> dict[str, Any]:
    deliverable = served.outcome in ("served", "downgraded")
    output = served.output
    placement = output.placement.model_dump(mode="json") if output is not None else None
    discriminating = served.discriminating
    map_id = map_record.get("id") if map_record else None
    row: dict[str, Any] = {
        "id": assist_id, "surface": SURFACE, "assist_kind": "hint", "practice_item_id": item.id,
        "practice_item_hash": practice_item_hash(item), "practice_session_id": request.session_id,
        "submission_id": request.submission_id.strip(),
        "hint_kind": served.kind if served.kind in KINDS else None,
        "level": served.level,
        "level_source": option_set.level_source if option_set.taken_level is not None else None,
        "horizon": _horizon(state, served),
        "route_id": (output.route_id or None) if output is not None and served.kind != "authored" else None,
        "from_node_id": (output.placement.reached_node_id or None) if output is not None else None,
        "target_node_id": (output.target_node_id or None) if output is not None and served.kind != "authored"
        else None,
        "map_id": map_id,
        "strategy": (output.strategy or None) if output is not None else None,
        "body_md": None if served.kind == "authored" else served.text,
        "authored_index": served.authored_index,
        "work_hash": state.work_hash, "work_chars": len(state.work_md),
        "placement_json": _json(placement),
        "chooser": choice.chooser if choice is not None else "fallback",
        "options_json": _json(option_set.record()),
        "probabilities_json": _json(choice.probabilities) if choice is not None and choice.probabilities else None,
        "drawn_option_json": _json(choice.drawn()) if choice is not None else None,
        "propensity": choice.propensity if choice is not None else None,
        "seed": choice.seed if choice is not None else None,
        "policy_version": f"{chooser_module.POLICY_VERSION}:{choice.policy}" if choice is not None
        else chooser_module.POLICY_VERSION,
        "question_set_version": chooser_module.QUESTION_SET_VERSION if choice is not None and choice.judgment_id
        else None,
        "state_hash": state.state_hash(),
        "request": request.request,
        "feedback_text": (request.feedback_text or None) if request.request == "feedback" else None,
        "feedback_shortcut": request.feedback_shortcut if request.request == "feedback" else None,
        "contract_failures_json": _json({
            "outcome": served.outcome, "reason": served.reason, "rounds": served.rounds,
            "chooser_reason": choice.reason if choice is not None else None,
            "state_unread": state.unread,
            "served_kind": served.kind,
            "drawn_kind": choice.kind if choice is not None else None,
        }),
        "leak_flags_json": _json(served.leaks) if served.leaks else None,
        "shown": 0,
        "counted_by": "server" if deliverable else None,
        "model": served.model or (choice.model if choice is not None else None),
        "prompt_version": WRITER_PROMPT_VERSION if served.prompt else None,
        "input_hash": content_key(served.prompt) if served.prompt else None,
        "latency_ms": served.latency_ms,
        "requested_at": requested_at,
    }
    if discriminating is not None:
        row["rivals_json"] = _json({"rivals": discriminating.get("rivals"), "weights": discriminating.get("weights"),
                                    "weights_basis": discriminating.get("weights_basis")})
        row["predicted_answers_json"] = _json({"candidates": discriminating.get("candidates"),
                                               "chosen_index": discriminating.get("chosen_index")})
        row["eig_nats"] = discriminating.get("eig_nats")
    return row


def _result(item: PracticeItem, state: HintState, option_set: OptionSet, choice: Choice | None, served: _Served,
            *, assist_id: str, fit_id: str | None) -> HintResultV1:
    base = HintResultV1(status=UNAVAILABLE, assist_id=assist_id, chooser=choice.chooser if choice else None,
                        propensity=choice.propensity if choice else None, reason=served.reason,
                        message=served.message, picks=worked_help_picks())
    if served.outcome == CANCELLED:
        base.status = CANCELLED
        return base
    if served.outcome == WITHHELD:
        base.status, base.message = WITHHELD, WITHHELD_MESSAGE
        base.reason = "would_give_answer_away"
        return base
    if served.outcome not in ("served", "downgraded"):
        base.message = served.message or _unavailable_message(served.reason)
        return base
    kind = str(served.kind)
    level = int(served.level or 3)
    output = served.output
    origin = FROM_THE_ITEM if kind == "authored" else AI_WRITTEN
    base.status = READY
    base.hint_md = served.text
    base.kind, base.level = kind, level
    base.horizon_index = served.horizon_index if kind == "waypoint" else None
    base.horizon = _horizon(state, served)
    base.placement = output.placement.model_dump(mode="json") if output is not None and kind != "authored" else None
    base.labels = labels_for(kind, level, origin=origin, has_work=state.has_work,
                             horizon_index=base.horizon_index,
                             source_origin=output.source_origin if output is not None else None)
    base.evidence = {"counts_as_hint": level not in WORKED_LEVELS, "primed": level in WORKED_LEVELS,
                     "level": level}
    base.authored_index = served.authored_index
    replies = ["doesnt_connect", "book_way"]
    if kind == "waypoint":
        replies.insert(0, "smaller_step")
    base.replies = replies
    if served.discriminating is not None and kind == "discriminating":
        base.discriminating = {
            "rivals": [{"id": rival["id"], "status": rival["status"]} for rival in served.discriminating["rivals"]],
            # A list, not a map keyed by rival id: the wire camel-cases keys.
            "predicted_answers": [{"rival_id": rival, "answer": answer} for rival, answer in
                                  (served.discriminating.get("predictions") or {}).items()],
            "eig_nats": served.discriminating.get("eig_nats"),
            "weights_basis": WEIGHTS_BASIS,
            "answer_box": True,
        }
    if served.reason:
        base.reason = served.reason
        base.message = served.message
    return base


def _unavailable_message(reason: str | None) -> str:
    return {
        "codex_refused": "Hints for your work aren't written on Codex (too slow); the item has no hint left.",
        "capped": "Today's hint budget is spent; the item has no hint of its own left.",
        "unpriced": "The hint route has no price set (hints.price_per_million); the item has no hint left.",
        "no_option": "No hint fits this request.",
        "contract_failed": "No hint passed its checks this time; ask again or take a worked piece.",
        "no_authored_hint_left": "The item has no hint of its own left.",
    }.get(str(reason), "No hint could be written right now.")


# ---------------------------------------------------------------------------
# Delivery, cancel, the discriminating answer
# ---------------------------------------------------------------------------

#: Delivery outcomes (:func:`deliver_hint`). ``submission_complete``: the
#: attempt the hint was written for is already committed (H2a review F1),
#: so its count can no longer be taken and the hint is never shown.
#: ``reveal_not_recorded`` (the sidecar's delivery, review round 2, V4): the
#: hint's reveal could not be written, so the shown mark rolled back with it
#: and a later read may deliver it.
SHOWN, SUBMISSION_COMPLETE, NOT_DELIVERABLE = "shown", "submission_complete", "not_deliverable"
REVEAL_NOT_RECORDED = "reveal_not_recorded"
#: The item the hint was written for is gone from the loaded vault or has
#: changed since (round 3, W5): never shown, and not retried.
ITEM_CHANGED = "item_changed"


_UNCHECKED: Any = object()


def deliver_hint(repository: Repository, assist_id: str, *, clock: Clock | None = None,
                 item: Any = _UNCHECKED) -> tuple[str, dict[str, Any] | None]:
    """Show a prepared hint (the surface received it): ``shown = 1`` once, with
    its time, in one transaction with the check that its count is still open.
    Returns ``(SHOWN, row)`` when this call showed it; else
    ``(SUBMISSION_COMPLETE, None)`` when an attempt closed its count (its
    submission's, or a keyless one of its session and item committed after
    it was requested; whichever order the hint and the submit finished in),
    ``(ITEM_CHANGED, None)`` when ``item`` is given and is None or no longer
    the item the row was written for (its ``practice_item_hash``; round 3,
    W5), or ``(NOT_DELIVERABLE, None)`` (already shown, withheld, or
    unknown). The caller must not show the text unless the outcome is
    ``SHOWN``."""

    with repository.atomic():
        connection = repository.connection()
        if item is not _UNCHECKED:
            row = store.assist(connection, assist_id)
            if row is not None and not row.get("shown") and (
                    item is None or practice_item_hash(item) != row.get("practice_item_hash")):
                return ITEM_CHANGED, None
        if store.mark_shown(connection, assist_id, shown_at=utc_now_iso(clock)):
            return SHOWN, store.assist(connection, assist_id)
        row = store.assist(connection, assist_id)
        if row is not None and not row.get("shown") and (
                row.get("attempt_id") or store.count_closed(connection, assist_id)):
            return SUBMISSION_COMPLETE, None
        return NOT_DELIVERABLE, None


def deliver(repository: Repository, assist_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
    """:func:`deliver_hint`'s row when this call showed it, else None."""

    outcome, row = deliver_hint(repository, assist_id, clock=clock)
    return row if outcome == SHOWN else None


def undelivered_result(assist_id: str, outcome: str) -> HintResultV1:
    """What the surface receives for a ready hint that was not delivered: no
    hint text and nothing shown (H2a review F1)."""

    message = {
        SUBMISSION_COMPLETE: "This answer was already submitted, so the hint was not shown.",
        REVEAL_NOT_RECORDED: "The hint couldn't be recorded just now, so it isn't shown yet; try again.",
        ITEM_CHANGED: "This item changed since the hint was written, so it isn't shown; ask again.",
    }.get(outcome, "That hint can no longer be shown; ask again.")
    return HintResultV1(status=UNAVAILABLE, assist_id=assist_id, reason=outcome, message=message)


def reveal_amount(item: PracticeItem, text: str) -> float:
    """How much of the item's answer a shown hint exposes (0..1), for its
    ``tutor_answer`` reveal (§5): the tutor's overlap measure, as the source
    spans' (which also measures a short answer), and a full reveal when the
    text states the exact key (worked help may; leak control keeps it out of
    levels 1-3)."""

    from learnloop.hints.maps import exact_key, gives_away
    from learnloop.tutor.tutor_qa import span_answer_overlap

    expected = item.expected_answer
    return max(span_answer_overlap(text, expected), 1.0 if gives_away(text, expected, exact_key(expected)) else 0.0)


def shown_text(item: PracticeItem, row: Mapping[str, Any]) -> str:
    """The text a delivered row showed (an authored hint's from the item)."""

    if row.get("body_md"):
        return str(row["body_md"])
    index = row.get("authored_index")
    if index is not None and 0 <= int(index) < len(item.hints):
        return item.hints[int(index)]
    return ""


def record_discriminate_answer(
    vault: LoadedVault,
    repository: Repository,
    *,
    practice_item_id: str,
    session_id: str,
    submission_id: str,
    question_assist_id: str,
    answer_md: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The learner's answer to a discriminating question (§4.2, §5): one
    ``help_assists`` row (``assist_kind = 'discriminate_answer'``, counted by
    neither), typed in the question's own box, never the answer draft. It
    moves no posterior and writes no probe observation; the next hint's state
    carries it. It is placed where the question was asked (the question's
    work), so "one at a time" holds at that placement (§4.2). Returns what it
    settled (which rivals predicted this answer)."""

    item = _active_item(vault, practice_item_id)
    with repository.connection() as connection:
        question = store.assist(connection, question_assist_id)
    if (question is None or question.get("submission_id") != submission_id.strip()
            or question.get("practice_item_id") != item.id or question.get("hint_kind") != "discriminating"
            or not question.get("shown")):
        raise HintRequestError("validation_error", "The answered question is not a shown discriminating "
                               "question of this attempt.", field="questionAssistId")
    predictions: dict[str, str] = {}
    try:
        record = json.loads(question.get("predicted_answers_json") or "{}")
        chosen = record.get("chosen_index")
        for candidate in record.get("candidates") or ():
            if candidate.get("index") == chosen:
                predictions = dict(candidate.get("predictions") or {})
    except (TypeError, ValueError):
        predictions = {}
    given = normalize_answer(answer_md)
    consistent = sorted(rival for rival, answer in predictions.items() if normalize_answer(answer) == given)
    settled = bool(consistent) and len(consistent) < len(predictions)
    message = ("That fits one reading more than the other; the next hint uses it." if settled
               else "Both readings still stand; the next hint uses your answer.")
    assist_id = "ha_" + new_ulid()
    now = utc_now_iso(clock)
    row = {
        "id": assist_id, "surface": SURFACE, "assist_kind": "discriminate_answer", "practice_item_id": item.id,
        "practice_item_hash": practice_item_hash(item), "practice_session_id": session_id,
        "submission_id": submission_id.strip(), "work_hash": question.get("work_hash"),
        "work_chars": question.get("work_chars"),
        "placement_json": _json({"question_assist_id": question_assist_id, "consistent_rivals": consistent,
                                 "settled": settled}),
        "chooser": "none", "feedback_text": answer_md, "rivals_json": question.get("rivals_json"),
        "predicted_answers_json": question.get("predicted_answers_json"), "eig_nats": question.get("eig_nats"),
        "shown": 1, "counted_by": None, "requested_at": now, "shown_at": now,
    }
    with repository.atomic():
        store.insert_assist(repository.connection(), row)
    return {"recorded": True, "assist_id": assist_id, "settled": settled, "consistent_rivals": consistent,
            "message": message}


__all__ = [
    "CANCELLED",
    "DISABLED",
    "ENVELOPE",
    "FIT_TASK",
    "HintRequestError",
    "HintRequestV1",
    "HintResultV1",
    "ITEM_CHANGED",
    "OWNER_KINDS",
    "NOT_DELIVERABLE",
    "READY",
    "REFUSED",
    "REQUEST_VERSION",
    "RESULT_VERSION",
    "REVEAL_NOT_RECORDED",
    "SHOWN",
    "SUBMISSION_COMPLETE",
    "UNAVAILABLE",
    "WITHHELD",
    "adaptive_enabled",
    "default_chooser_client",
    "deliver",
    "deliver_hint",
    "hints_envelope",
    "record_discriminate_answer",
    "request_hint",
    "reveal_amount",
    "reveal_basis",
    "shown_text",
    "undelivered_result",
]
