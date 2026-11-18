"""Learner probe preferences and conflicts with an already-open probe episode.

The four hard stops across the callers are learner preference, pending blocking
machine checks, a foreign open episode that has already interpreted observations,
and an item whose answer was already shown (checked by accept_probe_offer).
For divergent repairs, causal_repair_status consults machine checks, then learner
preference through decide_probe, then the episode conflict if a probe is offered;
hard_refusal consults preference, machine checks, then the episode conflict.
The order matters because the first applicable stop decides which reason a
decision records. accept_probe_offer checks answer exposure before the conflict
and checks exposure again at presentation commit.

hard_refusal keeps its own copy of the conflict check. For an empty learning-object
id, probe_episode_conflict answers None before looking, while the router looks.
"""

from __future__ import annotations

from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.db.stores.probes import ProbeEpisodeRecord

LEARNER_PREFERENCES = ("allow", "decline", "teach_now", "no_more_diagnostics")


#: Refusal id shared by `accept_probe_offer` and `causal_repair_status`. The
#: Tauri panel maps it to its own copy (`PROBE_OFFER_COPY`), so it is contract.
EPISODE_CONFLICT_REASON = "another_probe_episode_is_open"


EPISODE_CONFLICT_MESSAGE = (
    "I'm holding this targeted repair because two explanations would need "
    "different help. I can't run the check while another diagnostic is open "
    "on this topic — finish that one first."
)


def record_learner_preference(
    repository: Repository,
    *,
    preference: str,
    factor_id: str | None = None,
    learning_object_id: str | None = None,
    session_id: str | None = None,
    source: str = "learner_action",
    expires_at: str | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if preference not in LEARNER_PREFERENCES:
        raise ValueError(f"unknown learner probe preference {preference!r}")
    if factor_id is not None:
        scope, scope_ref = "factor", factor_id
    elif session_id is not None:
        scope, scope_ref = "session", session_id
    elif learning_object_id is not None:
        scope, scope_ref = "learning_object", learning_object_id
    else:
        raise ValueError(
            "a probe preference must be scoped to a factor, session, or "
            "learning object"
        )
    return repository.record_causal_probe_preference(
        scope=scope,
        scope_ref=scope_ref,
        preference=preference,
        source=source,
        session_id=session_id,
        expires_at=expires_at,
        detail=dict(detail) if detail is not None else None,
        clock=clock,
    )


def learner_preference(
    repository: Repository,
    *,
    factor_id: str | None = None,
    learning_object_id: str | None = None,
    session_id: str | None = None,
) -> str:
    record = repository.causal_probe_preference(
        factor_id=factor_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
    )
    if record is None:
        return "allow"
    return str(record["preference"])


def _causal_origin(factor_id: str) -> str:
    return f"causal_factor:{factor_id}"


def causal_origin(factor_id: str) -> str:
    """An episode's origin string for a factor."""

    return _causal_origin(factor_id)


def causal_origin_factor(origin: str) -> str | None:
    """The factor a causal episode's origin names, or None (:func:`_causal_origin`)."""

    prefix = _causal_origin("")
    return origin[len(prefix):] or None if origin.startswith(prefix) else None


def episode_conflict_reason(
    repository: Repository, episode: ProbeEpisodeRecord | None
) -> str | None:
    """Why an already-open probe episode cannot host this causal probe.

    Returns ``None`` when the episode can be relocked onto the cause set (see
    ``probe_episodes.retarget_episode_to_causal_factor``), and the typed refusal
    reason when it cannot — which is exactly when it has already interpreted
    observations under its own locked hypothesis set.

    ONE predicate, consulted by both ``causal_repair_status`` (so the offer is
    withheld rather than shown and then refused) and ``accept_probe_offer`` (so
    a stale offer still cannot force the relock).
    """

    from learnloop.diagnosis.probe_episodes import episode_has_observations

    if episode is None:
        return None
    if episode.status not in ("pending_items", "in_progress"):
        return None
    if episode_has_observations(repository, episode.id):
        return EPISODE_CONFLICT_REASON
    return None


def probe_episode_conflict(
    repository: Repository, *, factor_id: str, learning_object_id: str | None
) -> str | None:
    """The conflict that would make ``accept_probe_offer`` refuse, if any."""

    if not learning_object_id:
        return None
    existing = repository.open_probe_episode(learning_object_id)
    if existing is None or str(existing.origin or "") == _causal_origin(factor_id):
        return None
    return episode_conflict_reason(repository, existing)

