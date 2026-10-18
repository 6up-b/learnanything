"""Adaptive hints H2a: the typed state a hint is chosen and written from (spec §4.5).

Local reads only (§7.1: ~0.1-0.5 s, no model call). Each read is independent
and best-effort: a read that fails leaves its field empty (``None`` or ``[]``)
and is named in ``unread``, so a hint never fails because one input is
missing, and the chooser sees that it is missing rather than a made-up value.

What is read (§4.5's list): the item's LO placement intent and mastery; the
live predictor's P(success) and variance for the item; facet evidence on the
item's facets (unaided certification credit against assisted-only mass);
the learner's recent attempts on the item and its LO; the open rival
explanations of the learner's trouble (:mod:`learnloop.hints.discriminating`);
this attempt's earlier hints and replies (its ``help_assists`` rows under the
submission key); the approach map (:func:`map_builder.current_map`, None with
the maps off); the learner's route preference (the map's learner routes);
whether a worked example or another instance is at hand; the work (the
request's, else the session checkpoint's draft); the help style.

Nothing here writes. The two reads from :mod:`learnloop.placement` are pure
(named ``ignore_imports`` lines of the ``hints-never-write-evidence`` contract).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass, field
import hashlib
import json
import logging
from typing import Any

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as assists_store
from learnloop.hints.discriminating import Rival, open_rivals
from learnloop.vault.models import LoadedVault, PracticeItem

LOG = logging.getLogger(__name__)

STATE_VERSION = "hint_state.v1"
#: How many recent attempts the state carries (a prompt-size bound).
RECENT_ATTEMPTS = 5


@dataclass(frozen=True)
class EarlierHint:
    """One help row of this attempt, as the chooser and writer read it."""

    assist_id: str
    assist_kind: str
    hint_kind: str | None
    level: int | None
    horizon: int | None
    route_id: str | None
    from_node_id: str | None
    target_node_id: str | None
    strategy: str | None
    body_md: str | None
    authored_index: int | None
    request: str | None
    feedback_shortcut: str | None
    feedback_text: str | None
    shown: bool
    counted_by: str | None
    work_hash: str | None
    requested_at: str
    placement: dict[str, Any] | None = None
    rivals: list[dict[str, Any]] | None = None
    #: Never shown because it would give the answer away.
    withheld: bool = False

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "EarlierHint":
        def _json(value: Any) -> Any:
            try:
                return json.loads(value) if value else None
            except (TypeError, ValueError):
                return None

        return cls(
            assist_id=str(row["id"]), assist_kind=str(row["assist_kind"]), hint_kind=row.get("hint_kind"),
            level=row.get("level"), horizon=row.get("horizon"), route_id=row.get("route_id"),
            from_node_id=row.get("from_node_id"), target_node_id=row.get("target_node_id"),
            strategy=row.get("strategy"), body_md=row.get("body_md"), authored_index=row.get("authored_index"),
            request=row.get("request"), feedback_shortcut=row.get("feedback_shortcut"),
            feedback_text=row.get("feedback_text"), shown=bool(row.get("shown")), counted_by=row.get("counted_by"),
            work_hash=row.get("work_hash"), requested_at=str(row.get("requested_at") or ""),
            placement=_json(row.get("placement_json")), rivals=_json(row.get("rivals_json")),
            withheld=not row.get("shown") and bool(row.get("leak_flags_json")),
        )


@dataclass
class HintState:
    """Everything a hint is chosen and written from; ``unread`` names the
    reads that failed (their fields are empty, never guessed)."""

    practice_item_id: str
    learning_object_id: str
    facets: list[str]
    work_md: str
    work_hash: str
    help_style: str
    placement_intent: str | None = None
    mastery: dict[str, float] | None = None
    p_success: float | None = None
    p_success_variance: float | None = None
    facet_evidence: list[dict[str, Any]] = field(default_factory=list)
    recent_item_attempts: list[dict[str, Any]] = field(default_factory=list)
    recent_lo_attempts: dict[str, int] = field(default_factory=dict)
    rivals: list[Rival] = field(default_factory=list)
    earlier: list[EarlierHint] = field(default_factory=list)
    authored_revealed: list[int] = field(default_factory=list)
    map_record: dict[str, Any] | None = None
    route_preference: dict[str, int] = field(default_factory=dict)
    worked_example_at_hand: bool = False
    another_instance_at_hand: bool = False
    #: The learner's own book's worked examples the map was seeded with (T6's
    #: passages as H1 consumed them, read back locally; never retrieved again).
    worked_example_texts: list[str] = field(default_factory=list)
    #: Another instance: a family sibling's question.
    sibling_prompt: str | None = None
    seconds_on_item: float | None = None
    seconds_since_last_hint: float | None = None
    unread: list[str] = field(default_factory=list)

    @property
    def has_work(self) -> bool:
        return bool(self.work_md.strip())

    @property
    def shown_hints(self) -> list[EarlierHint]:
        return [hint for hint in self.earlier if hint.assist_kind == "hint" and hint.shown]

    @property
    def map(self) -> dict[str, Any] | None:
        return (self.map_record or {}).get("map") if self.map_record else None

    def authored_remaining(self, item: PracticeItem) -> list[int]:
        """The item's authored hints not yet shown in this attempt (by the
        client's reveals or the service's own authored rows), in order."""

        taken = set(self.authored_revealed)
        return [index for index in range(len(item.hints)) if index not in taken]

    def answered_discriminating_here(self) -> bool:
        """A discriminating question was answered at this placement: on the
        practice screen, on this same work (its hash), since the placement is
        the draft's (§4.2 "one at a time")."""

        return any(row.assist_kind == "discriminate_answer" and row.work_hash == self.work_hash
                   for row in self.earlier)

    def discriminate_answers(self) -> list[dict[str, Any]]:
        return [{"question_assist_id": (row.placement or {}).get("question_assist_id"),
                 "answer": row.feedback_text or "", "work_unchanged": row.work_hash == self.work_hash}
                for row in self.earlier if row.assist_kind == "discriminate_answer"]

    def decider_state(self) -> dict[str, Any]:
        """The typed, short state the Decider reads (§4.5): never the draft's
        text, the reference solution or the map's states (§7.4)."""

        hints = [{"kind": row.hint_kind, "level": row.level, "request": row.request,
                  "reply": row.feedback_shortcut, "work_changed_since": row.work_hash != self.work_hash}
                 for row in self.shown_hints]
        return {
            "placement_intent": self.placement_intent,
            "mastery_logit_mean": _round(self.mastery.get("logit_mean")) if self.mastery else None,
            "mastery_logit_variance": _round(self.mastery.get("logit_variance")) if self.mastery else None,
            "p_success": _round(self.p_success),
            "p_success_variance": _round(self.p_success_variance),
            "facet_evidence": self.facet_evidence,
            "recent_attempts_on_item": self.recent_item_attempts,
            "attempts_on_topic": self.recent_lo_attempts,
            "open_rivals": len(self.rivals),
            "has_work": self.has_work,
            "work_characters": len(self.work_md),
            "seconds_on_item": _round(self.seconds_on_item),
            "seconds_since_last_hint": _round(self.seconds_since_last_hint),
            "hints_this_attempt": hints,
            "discriminating_answered_here": self.answered_discriminating_here(),
            "approach_map": self.map is not None,
            "route_preference": self.route_preference,
            "help_style": self.help_style,
            "unread": self.unread,
        }

    def state_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.decider_state(), sort_keys=True, default=str).encode()).hexdigest()

    def record(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("work_md", None)
        payload.pop("map_record", None)
        return payload


def _round(value: Any) -> float | None:
    return None if value is None else round(float(value), 4)


def work_digest(work_md: str) -> str:
    return hashlib.sha256(work_md.encode("utf-8")).hexdigest()


def checkpoint_draft(repository: Repository, session_id: str, practice_item_id: str) -> str | None:
    """The session checkpoint's draft of this item (saved within 350 ms of
    typing; the client flushes it before asking), or None."""

    checkpoint = repository.fetch_session_checkpoint(session_id)
    if not checkpoint or checkpoint.get("current_practice_item_id") != practice_item_id:
        return None
    return str(checkpoint.get("current_answer") or "")


def _seconds_between(earlier: str | None, later: str) -> float | None:
    if not earlier:
        return None
    try:
        return max(0.0, (parse_utc(later) - parse_utc(earlier)).total_seconds())
    except ValueError:
        return None


def assemble_state(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    session_id: str,
    submission_id: str,
    work_md: str | None,
    seconds_on_item: float | None = None,
    now_iso: str | None = None,
    map_record: dict[str, Any] | None = None,
    map_loaded: bool = False,
) -> HintState:
    """The hint state for one request (local reads only)."""

    now = now_iso or utc_now_iso()
    unread: list[str] = []
    if work_md is None:
        try:
            work_md = checkpoint_draft(repository, session_id, item.id) or ""
        except Exception:  # noqa: BLE001 - a missing draft places the learner at the givens
            unread.append("draft")
            work_md = ""
    state = HintState(
        practice_item_id=item.id, learning_object_id=item.learning_object_id,
        facets=[vault.canonical_facet_id(facet) for facet in item.evidence_facets],
        work_md=work_md, work_hash=work_digest(work_md), help_style=str(vault.config.hints.help_style),
        seconds_on_item=seconds_on_item, unread=unread,
    )

    def read(name: str, reader: Any) -> None:
        try:
            reader()
        except Exception:  # noqa: BLE001 - one missing input never fails the hint
            LOG.debug("hint state read %s failed", name, exc_info=True)
            state.unread.append(name)

    read("earlier_hints", lambda: _read_earlier(repository, state, submission_id))
    read("placement", lambda: _read_placement(vault, repository, state, now))
    read("prediction", lambda: _read_prediction(vault, repository, item, state, now))
    read("facet_evidence", lambda: _read_facets(repository, state))
    read("attempts", lambda: _read_attempts(repository, item, state))
    read("rivals", lambda: state.rivals.extend(open_rivals(repository, item)))
    if map_loaded:
        state.map_record = map_record
    else:
        read("approach_map", lambda: _read_map(vault, repository, item, state))
    read("route_preference", lambda: _read_route_preference(state))
    read("examples", lambda: _read_examples(vault, repository, item, state))
    last = max((row.requested_at for row in state.earlier if row.assist_kind == "hint"), default=None)
    state.seconds_since_last_hint = _seconds_between(last, now)
    return state


def _read_earlier(repository: Repository, state: HintState, submission_id: str) -> None:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = assists_store.submission_assists(connection, submission_id=submission_id,
                                                practice_item_id=state.practice_item_id)
    state.earlier = [EarlierHint.from_row(row) for row in rows if row.get("attempt_id") is None]
    # Shown (by the screen or the service), or withheld for giving the answer
    # away: never served again in this attempt.
    state.authored_revealed = sorted({
        int(row.authored_index) for row in state.earlier
        if row.assist_kind == "hint" and row.hint_kind == "authored" and (row.shown or row.withheld)
        and row.authored_index is not None
    })


def _read_placement(vault: LoadedVault, repository: Repository, state: HintState, now: str) -> None:
    from learnloop.placement.state import load_placement_state

    placement = load_placement_state(vault, repository, now_iso=now)
    intent = placement.intent_by_lo.get(state.learning_object_id)
    state.placement_intent = str(intent.intent) if intent is not None else None


def _read_prediction(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState,
                     now: str) -> None:
    from learnloop.placement.predictor import active_predictor

    masteries = repository.mastery_states()
    mastery = masteries.get(item.learning_object_id)
    if mastery is not None:
        state.mastery = {"logit_mean": float(mastery.logit_mean), "logit_variance": float(mastery.logit_variance)}
    prediction = active_predictor(vault, repository, mastery_states=masteries, now_iso=now).predict_item(item.id)
    state.p_success = float(prediction.p_success)
    state.p_success_variance = float(prediction.logit_variance)


def _read_facets(repository: Repository, state: HintState) -> None:
    if not state.facets:
        return
    placeholders = ",".join("?" for _ in state.facets)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT facet_id, capability, direct_positive_mass + embedded_positive_mass, "
            "direct_negative_mass + embedded_negative_mass, certification_credit "
            f"FROM facet_capability_evidence WHERE facet_id IN ({placeholders}) ORDER BY facet_id, capability",
            tuple(state.facets),
        ).fetchall()
    state.facet_evidence = [
        {"facet": str(row[0]), "capability": str(row[1]), "positive_mass": _round(row[2]),
         "negative_mass": _round(row[3]), "unaided_credit": _round(row[4]),
         "assisted_only": float(row[2] or 0) > 0 and float(row[4] or 0) <= 0}
        for row in rows
    ]


def _assisted(row: Mapping[str, Any]) -> bool:
    return int(row.get("hints_used") or 0) > 0 or bool(row.get("primed")) or row.get("attempt_type") in (
        "hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough")


def _read_attempts(repository: Repository, item: PracticeItem, state: HintState) -> None:
    for row in repository.list_recent_attempts_by_practice_item(item.id, limit=RECENT_ATTEMPTS):
        correctness = row.get("correctness")
        state.recent_item_attempts.append({
            "correct": None if correctness is None else float(correctness) >= 0.999,
            "score": _round(correctness), "assisted": _assisted(row), "at": row.get("created_at"),
        })
    lo_rows = repository.list_recent_attempts_by_learning_object(item.learning_object_id, limit=20)
    state.recent_lo_attempts = {
        "attempts": len(lo_rows),
        "correct_unaided": sum(1 for row in lo_rows if not _assisted(row) and (row.get("correctness") or 0) >= 0.999),
        "assisted": sum(1 for row in lo_rows if _assisted(row)),
    }


def _read_map(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState) -> None:
    from learnloop.hints.map_builder import current_map

    state.map_record = current_map(vault, repository, item.id)


def _read_route_preference(state: HintState) -> None:
    current = state.map
    if not current:
        return
    for route in current.get("routes") or ():
        count = len(route.get("learner_attempt_ids") or ())
        if count or str(route.get("origin") or "").startswith("learner"):
            state.route_preference[str(route.get("id"))] = count


def _read_examples(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState) -> None:
    """A worked example at hand: the map was seeded with the learner's own
    book's worked examples (T6's spans, consumed: their texts are read back
    locally, never retrieved again); another instance: a family sibling."""

    seeds = (state.map_record or {}).get("seeds") or {}
    spans = seeds.get("spans") if isinstance(seeds, Mapping) else None
    keys = [(str(span.get("extraction_id")), str(span.get("span_id"))) for span in spans or ()
            if isinstance(span, Mapping) and span.get("extraction_id") and span.get("span_id")]
    if keys:
        from learnloop.db.stores.source_block_fts import blocks_by_key

        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE name = 'source_document_blocks'").fetchone() is not None:
                blocks = blocks_by_key(connection, keys)
                state.worked_example_texts = [blocks[key].text for key in keys
                                              if key in blocks and blocks[key].text.strip()]
    state.worked_example_at_hand = bool(state.worked_example_texts)
    family = getattr(item, "family_id", None)
    sibling = next((other for other in vault.practice_items.values()
                    if family and other.id != item.id and getattr(other, "family_id", None) == family
                    and other.status == "active"), None)
    state.sibling_prompt = sibling.prompt if sibling is not None else None
    state.another_instance_at_hand = sibling is not None


def rivals_payload(rivals: Sequence[Rival]) -> list[dict[str, Any]]:
    return [rival.as_dict() for rival in rivals]


__all__ = [
    "EarlierHint",
    "HintState",
    "RECENT_ATTEMPTS",
    "STATE_VERSION",
    "assemble_state",
    "checkpoint_draft",
    "rivals_payload",
    "work_digest",
]
