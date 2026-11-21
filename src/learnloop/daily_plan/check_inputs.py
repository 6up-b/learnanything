"""What a lesson offer's committed check needs from the vault before the router can price it (spec_teacher_v2 §7.4):
whether a question exists for it now, and how long one check takes. From ``mvp-0.62`` the offer builder attaches them
to each check of a new offer (:func:`check_sensors`); below it nothing calls them.

* :func:`eligible_now`: the delayed checks' own candidate rule (``delayed_checks.check_available``, the rule the
  lesson brief's "an unseen question exists" reads), with the normal protection view; protection that cannot be
  read, or any failure to read, answers False (fail closed). It reserves nothing, writes nothing and calls no model.
  It is a seed for the delivery estimate, read before the lesson's own exposures: not a promise that the same item
  survives the lesson.
* :func:`check_sensors`: both of the above with the delivery posterior (``daily_plan.check_delivery``: the receipts'
  cold-completion counts as of the decision, seeded by :func:`eligible_now`), as the fields one check's record carries.
  The decision's clock is left out of the record: the record is part of the boundary's identity, which must stay the
  same between a prefetch and its serve unless the evidence itself changed (the counts' digest, the availability or the
  minutes); the trace's replay payload holds the clock.
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


def check_key(learning_object_id: str, purpose: str, ordinal: int) -> str:
    """A committed check's stable key within its offer: its topic, purpose and place, so two checks on one topic draw
    from streams of their own."""

    return f"{learning_object_id}:{purpose}:{ordinal}"


def delivery_group(purpose: str) -> str:
    """The fitted posterior a check shares one propensity draw with: its purpose within the legacy regime."""

    from learnloop.daily_plan.check_delivery import LEGACY_REGIME

    return f"{LEGACY_REGIME}:{purpose}"


def check_sensors(vault: Any, repository: Any, learning_object_id: str, *, purpose: str, ordinal: int, now_iso: str,
                  trials: Any) -> dict[str, Any]:
    """One committed check's record fields at a new decision: its key and group, the delivery posterior (the counts of
    ``purpose`` over ``trials``, classified as of ``now_iso``, seeded by the availability now) and its minutes, with the
    rollout path's versions. ``trials``: ``check_delivery.classify``'s result for the decision, read once per offer, or
    None when it could not be read (then nothing is credited: the posterior is the point mass at zero)."""

    from learnloop.router_objective.check_value import POLICY_VERSION, STREAM_LAYOUT_VERSION
    from learnloop.daily_plan import check_delivery as CD

    eligible = eligible_now(vault, repository, learning_object_id)
    if trials is None:
        delivery: dict[str, Any] = {"status": "unavailable", "eligible_now": eligible, "alpha": 0.0, "beta": 1.0,
                                    "predictive_mean": 0.0}
    else:
        counts = CD.counts(trials, purpose=purpose, as_of=now_iso)
        delivery = CD.posterior(counts, eligible_now=eligible).as_dict()
        delivery.pop("as_of", None)
        delivery["seed_trials"] = CD.SEED_TRIALS
    try:
        minutes = dry_check_minutes(vault, repository, learning_object_id, as_of=now_iso).as_dict()
        minutes.pop("as_of", None)
    except Exception:  # noqa: BLE001 - no estimate: the check still exists, at no minutes, and the record says so
        minutes = {"minutes": 0.0, "basis": "unavailable", "item_id": None, "estimator_version": None}
    return {"key": check_key(learning_object_id, purpose, ordinal), "group": delivery_group(purpose),
            "delivery": delivery, "minutes": minutes, "rollout_policy": POLICY_VERSION,
            "stream_layout": STREAM_LAYOUT_VERSION}


__all__ = ["CheckMinutes", "ITEM_ESTIMATE", "UNKNOWN_ITEM_ESTIMATE", "check_key", "check_sensors", "delivery_group",
           "dry_check_minutes", "eligible_now"]
