"""The learner's marks on possible causes: the pure parts and the receipts (spec §7).

The learner reads the possible causes and marks them. It is an imperfect sensor, kept for later
measurement. It reaches two places, as the learner's attributed opinion and nothing more: the learner
state card and the history-aware diagnoser's context. It never touches a grade or certification, opens
no belief, resolves no factor and moves no probability. In particular a mark is never forwarded to
``record_unresolved_cause_self_report``, which can open a provisional belief and resolve a factor.

A leaf for the domain packages that read the opinion. What the screen reads and writes is
``learnloop.followup_run.marks``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import hashlib
import json
from typing import Any

from learnloop.db.stores import hypothesis_marks as store

#: How display order is drawn: a new version if the draw ever changes.
ORDER_VERSION = "hypothesis_order_v1"

MY_GAP = "my_gap"
PARTLY = "partly"
NOT_IT = "not_it"
NONE_OF_THESE = "none_of_these"
CLEARED = "cleared"
#: The three marks a hypothesis can carry.
HYPOTHESIS_MARKS: frozenset[str] = frozenset({MY_GAP, PARTLY, NOT_IT})
MARKS: frozenset[str] = HYPOTHESIS_MARKS | {NONE_OF_THESE, CLEARED}
#: The marks as the opinion says them.
MARK_WORDS: Mapping[str, str] = {MY_GAP: "this is my gap", PARTLY: "partly", NOT_IT: "not it", NONE_OF_THESE: "none of these"}
#: Said with the marks wherever a model reads them: an opinion, not a measurement.
ATTRIBUTION = "The learner's own read of this answer's possible causes: their opinion, unmeasured, and it may be wrong."


def display_order(attempt_id: str, factor_id: str | None, keys: Sequence[str]) -> tuple[str, tuple[str, ...]]:
    """(the logged seed, the stable identities in display order).

    Each identity sorts by its own hash under the seed, so the order is the same on every read of
    this list, a later version of a cause keeps its place, and a new cause moves nothing else."""

    seed = hashlib.sha256(f"{ORDER_VERSION}\0{attempt_id}\0{factor_id or ''}".encode("utf-8")).hexdigest()[:32]
    return seed, tuple(sorted(
        dict.fromkeys(keys), key=lambda key: (hashlib.sha256(f"{seed}\0{key}".encode("utf-8")).hexdigest(), key)
    ))


def latest_marks(rows: Iterable[Mapping[str, Any]]) -> dict[str | None, Mapping[str, Any]]:
    """A change of mind appends and the latest counts: per hypothesis identity (None is the None of
    these line), the latest row in ``rows``, oldest first, unless it took the mark back."""

    latest: dict[str | None, Mapping[str, Any]] = {}
    for row in rows:
        latest[row.get("hypothesis_key")] = row
    return {key: row for key, row in latest.items() if row.get("mark") != CLEARED}


def opinion_entries(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """What the diagnoser reads of one attempt's marks: the latest counts. Empty with none."""

    latest = latest_marks(rows)
    entries: list[dict[str, Any]] = []
    for row in sorted(latest.values(), key=lambda value: (str(value.get("created_at") or ""), str(value.get("id") or ""))):
        entry: dict[str, Any] = {"mark": MARK_WORDS[str(row["mark"])], "marked_at": row.get("created_at"),
                                 "after_the_follow_up_question": bool(row.get("probe_answered"))}
        if row.get("hypothesis_statement"):
            entry["cause"] = row["hypothesis_statement"]
        if row.get("free_text"):
            entry["in_their_words"] = row["free_text"]
        entries.append(entry)
    return entries


def opinion_block(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any] | None:
    """The attributed block a context carries for one attempt, or None (it renders as before)."""

    entries = opinion_entries(rows)
    return {"attribution": ATTRIBUTION, "marks": entries} if entries else None


def attempt_opinion(repository: Any, attempt_id: str) -> dict[str, Any] | None:
    """The block for one attempt from the ledger; None below migration 242 or with no marks."""

    with repository.connection() as connection:
        if not store.present(connection):
            return None
        return opinion_block(store.marks_for_attempt(connection, attempt_id))


def probe_state(connection: Any, *, factor_id: str | None, workflow: Mapping[str, Any] | None) -> dict[str, Any]:
    """Whether the attempt's probe has been answered, by which attempt, and its outcome if known.
    A question answered ends in its discriminating-observation receipt, which may not exist yet."""

    observation = store.latest_observation(connection, factor_id) if factor_id else None
    item_id = (workflow or {}).get("practice_item_id")
    answer = store.attempt_of_item(connection, str(item_id)) if item_id and (workflow or {}).get("lane") == "probe" else None
    if observation is None and answer is None:
        return {"answered": False, "attempt_id": None, "outcome": None}
    outcome: dict[str, Any] = {}
    if answer is not None:
        outcome.update(rubric_score=answer.get("rubric_score"), correctness=answer.get("correctness"))
    if observation is not None:
        outcome.update(
            observation_id=observation["id"],
            classification=observation["outcome"],
            classified_as=json.loads(observation["classified_as_json"] or "[]"),
            supports_open_set=bool(observation["supports_open_set"]),
            admitted=bool(observation["admitted"]),
            admissible_as_independent=(None if observation["admissible_as_independent"] is None
                                       else bool(observation["admissible_as_independent"])),
        )
    attempt_id = (observation or {}).get("probe_attempt_id") or (answer or {}).get("id")
    return {"answered": True, "attempt_id": str(attempt_id), "outcome": outcome}


__all__ = [
    "ATTRIBUTION", "CLEARED", "HYPOTHESIS_MARKS", "MARKS", "MARK_WORDS", "MY_GAP", "NONE_OF_THESE", "NOT_IT", "ORDER_VERSION",
    "PARTLY", "attempt_opinion", "display_order", "latest_marks", "opinion_block", "opinion_entries", "probe_state",
]
