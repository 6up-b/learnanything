"""What a lesson offer's committed check needs from the vault before the router can price it (spec_teacher_v2 §7.4):
whether a question exists for it now, and how long one check takes. Unserved: nothing under ``src`` calls these
until the successor that prices checks (``mvp-0.62``) attaches them to the offer.

* :func:`eligible_now`: the delayed checks' own candidate rule (``delayed_checks.check_available``, the rule the
  lesson brief's "an unseen question exists" reads), with the normal protection view; protection that cannot be
  read, or any failure to read, answers False (fail closed). It reserves nothing, writes nothing and calls no model.
  It is a seed for the delivery estimate, read before the lesson's own exposures: not a promise that the same item
  survives the lesson.
* :func:`dry_check_minutes`: one check's minutes from the plan's own estimator (``daily_plan.estimates``), as the
  plan charges a "Check once" item: the item the delayed picker would choose now (its rule, without its receipt or a
  reservation) at its four-decimal planning estimate, or, with no candidate, the same estimator's estimate for an
  item it knows nothing about (the answer prior plus the feedback prior with no evidence: no new constant). The
  evidence is what was recorded by the decision time. A point estimate: the plan has no estimated variance for a
  Check once duration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: The item the dry estimate prices: the picker's choice (provenance only, never the later real check's item), or
#: none.
ITEM_ESTIMATE = "item_estimate"
UNKNOWN_ITEM_ESTIMATE = "unknown_item_estimate"


@dataclass(frozen=True)
class CheckMinutes:
    """One check's planning minutes, and where they came from."""

    minutes: float
    basis: str
    item_id: str | None
    estimator_version: str
    as_of: str

    def as_dict(self) -> dict[str, Any]:
        return {"minutes": self.minutes, "basis": self.basis, "item_id": self.item_id,
                "estimator_version": self.estimator_version, "as_of": self.as_of}


def eligible_now(vault: Any, repository: Any, learning_object_id: str) -> bool:
    """Whether a delayed check could be committed on the LO now (the shared candidate rule; fail closed)."""

    try:
        from learnloop.delayed_checks import attempted_items, check_available
        from learnloop.learner_protection import withheld_items

        withheld = withheld_items(vault, repository)
        if not getattr(withheld, "available", False):
            return False
        return check_available(vault, repository, learning_object_id, withheld=withheld,
                               attempted=attempted_items(repository))
    except Exception:  # noqa: BLE001 - an unread vault cannot establish a question: no check is credited
        return False


def _evidence_as_of(vault: Any, repository: Any, as_of: str) -> Any:
    """The estimator's duration evidence recorded by ``as_of``: the attempts known by then (the attempt ledger's
    availability rule) and the plan events written by then, read through the estimator's own explicit inputs."""

    from learnloop.daily_plan.estimates import load_duration_evidence
    from learnloop.db.attempt_availability import attempt_time_sql

    known = attempt_time_sql(vault.config)
    with repository.connection() as connection:
        attempts = [dict(row) for row in connection.execute(
            "SELECT practice_item_id, practice_mode, latency_seconds FROM practice_attempts "
            f"WHERE latency_seconds IS NOT NULL AND latency_seconds > 0 AND {known} <= ?", (as_of,))]
        plans = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'daily_plans'").fetchone() is not None
        events = [dict(row) for row in connection.execute(
            "SELECT b.daily_plan_id AS plan_id, e.block_id AS block_id, e.kind AS kind, e.detail_json AS detail, "
            "e.created_at AS created_at "
            "FROM attention_block_events e JOIN attention_blocks b ON b.id = e.block_id "
            "WHERE b.daily_plan_id IS NOT NULL AND b.plan_ordinal IS NOT NULL "
            "AND e.kind IN ('item_done', 'item_served') AND e.created_at <= ? "
            "ORDER BY b.daily_plan_id, e.created_at, e.id", (as_of,))] if plans else []
    return load_duration_evidence(repository, latency_cap_minutes=float(vault.config.plan.latency_cap_minutes),
                                  attempt_rows=attempts, event_rows=events)


def dry_check_minutes(vault: Any, repository: Any, learning_object_id: str, *, as_of: str) -> CheckMinutes:
    """One check's minutes on the LO from the plan's estimator over the evidence recorded by ``as_of``."""

    from learnloop.daily_plan.estimates import ESTIMATE_DECIMALS, Estimator
    from learnloop.delayed_checks import attempted_items, candidates, pick_with_receipt, revealed_items
    from learnloop.learner_protection import withheld_items

    config = vault.config.plan
    estimator = Estimator(evidence=_evidence_as_of(vault, repository, as_of),
                          read_words_per_minute=int(config.read_words_per_minute))
    item = None
    withheld = withheld_items(vault, repository)
    if getattr(withheld, "available", False):
        found = candidates(vault, repository, learning_object_id, exclude=(), withheld=withheld,
                           attempted=attempted_items(repository), revealed=revealed_items(repository, ""))
        item = pick_with_receipt(vault, repository, found, seed_key=f"dry:{learning_object_id}")[0] if found else None
    if item is not None:
        return CheckMinutes(minutes=estimator.item_minutes(vault, str(item.id)), basis=ITEM_ESTIMATE,
                            item_id=str(item.id), estimator_version=estimator.version, as_of=as_of)
    unknown = estimator.estimate("", None, None).minutes
    return CheckMinutes(minutes=round(unknown, ESTIMATE_DECIMALS), basis=UNKNOWN_ITEM_ESTIMATE, item_id=None,
                        estimator_version=estimator.version, as_of=as_of)


__all__ = ["CheckMinutes", "ITEM_ESTIMATE", "UNKNOWN_ITEM_ESTIMATE", "dry_check_minutes", "eligible_now"]
