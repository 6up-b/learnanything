"""AD's forecast of a graded answer, as AD stood before it (``docs/reviews/algorithm-mvp-0.71.md``).

The serve hook records AD's forecast for an answer served through the plan. Every other graded answer (a Reader
check, the tutor's, the phone's, practice opened outside the plan, a probe) has none, so the grade records one: the
subject view's ``p̄`` and its three category probabilities for the item, from AD's state over everything recorded
before the answer (the answer itself is not yet written when this runs), as an append-only receipt of its own kind
(:data:`ITEM_UNASSISTED_SUCCESS_AT_GRADE`) bound to the attempt. Surprise reads it where no serve-time receipt
applies; replay reads the receipt, never AD's state, so a rebuild reproduces the row exactly whatever AD becomes.

Protected material gets none (A8), as at a serve: the view withholds it. Nothing here decides anything.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.forecasters import EVENT
from learnloop.adaptive_difficulty.logs import warn_failure
from learnloop.adaptive_difficulty.material_view import material_view
from learnloop.adaptive_difficulty.operation import entry
from learnloop.adaptive_difficulty.successor import successor_active
from learnloop.ids import keyed_ulid
from learnloop.scheduling.forecast_receipts import ITEM_UNASSISTED_SUCCESS_AT_GRADE, ForecastReceipt
from learnloop.vault.hashes import item_revision

LOG = logging.getLogger(__name__)

GRADE_FORECASTER = "ad_threshold@grade"
GRADE_FORECAST_VERSION = "ad-threshold-grade-v1"
#: The attempt the forecast is about (``forecast_receipts.source_attempt_id``).
GRADED_ATTEMPT = "graded_attempt"

def receipt_id(attempt_id: str) -> str:
    """A grade-time receipt's id, a function of its attempt (:func:`learnloop.ids.keyed_ulid`): drawn from
    ``ids.new_ulid`` it would shift every id the grade mints after it, and drawn from a stream of its own it would
    differ between two runs of the same history."""

    return keyed_ulid(attempt_id, receipt_key(attempt_id))


def receipt_key(attempt_id: str) -> str:
    return f"{ITEM_UNASSISTED_SUCCESS_AT_GRADE}:{GRADED_ATTEMPT}:{attempt_id}:{GRADE_FORECASTER}"


def _evidence_after(events: Any, at: str) -> bool:
    """Whether AD's evidence holds anything dated after the answer's cutoff ``at`` (an attempt, a claim or a reading
    opportunity). Such a forecast would read evidence the learner gave after answering (a retrospective import dated
    before practice already recorded), and AD's state as it stood then cannot be rebuilt here, so the answer gets
    none and its surprise reads mastery, marked. Grade revisions written after the cutoff are checked by the caller,
    outside AD's operation (its guard refuses the grade ledger)."""

    limit = RP.days(at)
    return any(event.at > limit for group in (events.attempts, events.claims, events.opportunities) for event in group)


@entry(read_only=True)
def grade_receipt(vault: Any, repository: Any, *, practice_item_id: str, attempt_id: str, at: str,
                  answered_item: Any = None, answered_revision: str | None = None, view: Any = None,
                  answered: Any = None) -> ForecastReceipt | None:
    """AD's subject-view forecast for the answer ``attempt_id`` to ``practice_item_id`` at ``at``, from AD's state
    over everything recorded before it; None when AD is off, the item is protected or unknown to AD's view."""

    from learnloop.adaptive_difficulty.serving import _spec, _warmth, served_item
    from learnloop.adaptive_difficulty.snapshot_parts import threshold_snapshot
    from learnloop.db.connection import connect
    from contextlib import closing

    from learnloop.adaptive_difficulty.switches import receipts_enabled

    if not successor_active(vault.config) or not receipts_enabled(vault.config):
        return None
    view = material_view(vault, repository, view)
    if view.withheld(practice_item_id):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        # One read snapshot for the events, the item's inputs and the warmth: a writer committing meanwhile is seen by
        # none of them or, after the read, by none.
        connection.execute("BEGIN")
        try:
            item = view.revision(connection, answered_revision) if answered_revision else answered_item
            if item is None:
                # A contract a grade froze first saved no revision: the item unchanged since is that revision.
                item = view.item(practice_item_id)
                if item is not None and answered_revision and item_revision(item)[0] != answered_revision:
                    item = None
            if item is None or item.id != practice_item_id or view.covers(item):
                return None
            # Every stored fact naming what the answer was shown (its contract, its plan presentation, its selection):
            # one withheld revision among them and there is no forecast, so no receipt, snapshot or hash is written.
            if view.answer_withheld(connection, practice_item_id, contract_revision=answered_revision, at=at,
                                    **dict(answered or {})):
                return None
            snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
            if _evidence_after(snapshot.events, at):
                return None
            spec = _spec(vault, connection, snapshot, item, at, view)
            warmth = _warmth(connection, view, str(item.learning_object_id), at)
        finally:
            connection.rollback()
    constants = S.constants_from_config(vault.config)
    state = snapshot.subject
    prediction = PR.predict(state, spec, warmth=warmth, band=constants.band)
    revision = served_item(vault, item)
    categories, parts = threshold_snapshot(
        revision, name=GRADE_FORECASTER, mixture="bank", state_hash=snapshot.state_hash(),
        categories_of=lambda: PR.category_mixture(state, spec, warmth=warmth),
        presentation_kind=GRADED_ATTEMPT, presentation_id=attempt_id, served_at=at, epoch=view.epoch,
        threshold_version=GRADE_FORECAST_VERSION, replay_version=RP.REPLAY_VERSION)
    if parts is not None:
        from learnloop.db.evidence_cutoff import Cutoff

        parts = replace(parts, cutoff=Cutoff.ad_replay(at),
                        source={"attempt_id": attempt_id, "item_revision": revision.content_hash,
                                "ad_state_hash": snapshot.state_hash(), "replay_version": RP.REPLAY_VERSION,
                                "spec_and_warmth_read_at": at, "protection_epoch": view.epoch},
                        target=replace(parts.target, kind=ITEM_UNASSISTED_SUCCESS_AT_GRADE,
                                       action_kind="grade", action_id=attempt_id, horizon_kind="grade"),
                        provenance={**parts.provenance, "training_cutoff": {"preset": "ad_replay", "as_of": at}})
    from learnloop.scheduling.voi_forecasts import parameter

    return ForecastReceipt(
        receipt_key=receipt_key(attempt_id), kind=ITEM_UNASSISTED_SUCCESS_AT_GRADE, forecaster=GRADE_FORECASTER,
        forecaster_version=f"{GRADE_FORECAST_VERSION}:{P.PRIORS_VERSION}:{P.HYPER_VERSION}",
        scope="attempt", decision_kind="grade", binding_kind=GRADED_ATTEMPT, event=EVENT,
        forecast={"p": round(prediction.p_bar, 8), "event": EVENT, "p_categories": categories,
                  "p_band": round(prediction.p_band, 8)},
        inputs={"practice_item_id": str(item.id), "learning_object_id": item.learning_object_id,
                "state_hash": snapshot.state_hash(), "warmth": round(warmth, 8),
                # The events the forecast read (it runs before the grade's write transaction, so another writer may
                # commit in between): what "AD before this answer" was, recorded, never recomputed.
                "events_fingerprint": RP.events_fingerprint(snapshot.events),
                "features": dict(spec.features or {}), "signals": dict(spec.signals),
                "loadings": dict(spec.loadings)},
        parameters=[parameter("priors", P.PRIORS_VERSION, "structural", source="code")],
        versions={"forecaster": GRADE_FORECAST_VERSION, **P.versions()},
        inputs_as_of=at, p=prediction.p_bar,
        # The answered revision as a column, whatever the snapshot enrichment: surprise reads it live and on replay.
        columns={"decision_ref": attempt_id, "source_attempt_id": attempt_id, "practice_item_id": str(item.id),
                 "learning_object_id": item.learning_object_id, "item_content_hash": revision.content_hash},
        snapshot=parts,
    )


def safe_grade_receipt(vault: Any, repository: Any, **kwargs: Any) -> ForecastReceipt | None:
    """:func:`grade_receipt`, never raising: a forecast never costs the grade."""

    try:
        return grade_receipt(vault, repository, **kwargs)
    except Exception:  # noqa: BLE001 - AD's logging never breaks the grade
        warn_failure(LOG, "AD's grade-time forecast for attempt %s not computed", kwargs.get("attempt_id"))
        return None


__all__ = ["GRADED_ATTEMPT", "GRADE_FORECASTER", "GRADE_FORECAST_VERSION", "grade_receipt",
           "receipt_id", "receipt_key", "safe_grade_receipt"]
