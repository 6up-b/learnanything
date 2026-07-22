"""P0.3 projection cutover + reinterpretation receipts (spec §4.2, §7.2).

Activating the mvp-0.8 authority-propagation projection records a
``derived_state_rebuilds`` receipt and NEVER rewrites raw history. When a later
reinterpretation (e.g. an appended adjudication) changes the leading actionable
conclusion for an observation, a ``measurement_reinterpretation`` measurement
event is appended and current downstream state is rebuilt -- the immutable
decision-time interpretation rows are untouched (append-only discipline).

The default projection version is NOT flipped here; that cutover is P0.5's job
(design §5). This module builds the activation + reinterpretation machinery.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import (
    KM_ALGORITHM_VERSION,
    P0_ALGORITHM_VERSION,
)
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.vault.models import LoadedVault


def activate_p0_projection(
    vault: LoadedVault,
    repository: Repository,
    *,
    from_version: str = KM_ALGORITHM_VERSION,
    clock: Clock | None = None,
) -> str:
    """Rebuild + record activation of the mvp-0.8 projection (§7.2).

    Runs the (idempotent) canonical projection under mvp-0.8 and writes a
    ``derived_state_rebuilds`` row from ``from_version`` to mvp-0.8. Raw history is
    never rewritten; on a projection failure the last-good named projection stays
    readable and the failed rebuild is surfaced to the caller (§7.3)."""

    if vault.config.algorithms.algorithm_version != P0_ALGORITHM_VERSION:
        raise ValueError(
            "activate_p0_projection requires a vault on the mvp-0.8 projection namespace"
        )
    replayed = len(repository.canonical_observation_ledger_v2())
    learning_object_ids = sorted(
        {row["learning_object_id"] for row in repository.canonical_observation_ledger_v2() if row.get("learning_object_id")}
    )
    project_canonical_facet_state(vault, repository, clock=clock)
    return repository.record_derived_state_rebuild(
        scope="p0_projection_activation",
        learning_object_ids=learning_object_ids,
        algorithm_version=P0_ALGORITHM_VERSION,
        rebuilt_learning_objects=len(learning_object_ids),
        replayed_attempts=replayed,
        clock=clock,
    )


def leading_conclusion(interpretation: Mapping[str, Any] | None) -> str | None:
    """The leading actionable conclusion of an interpretation: the top true class of
    its response posterior (§2.3)."""

    if interpretation is None:
        return None
    posterior = json.loads(interpretation["response_posterior_json"])
    if not posterior:
        return None
    return max(posterior, key=posterior.get)


def record_reinterpretation_if_changed(
    repository: Repository,
    *,
    administration_id: str,
    observation_id: str,
    from_interpretation: Mapping[str, Any] | None,
    to_interpretation: Mapping[str, Any] | None,
    clock: Clock | None = None,
) -> str | None:
    """Append a ``measurement_reinterpretation`` event when the leading actionable
    conclusion changed between two interpretations (§2.3). Returns the event id, or
    None when the conclusion is unchanged. The historical interpretation rows are
    never mutated -- only a new append-only event is written."""

    from_conclusion = leading_conclusion(from_interpretation)
    to_conclusion = leading_conclusion(to_interpretation)
    if from_conclusion == to_conclusion:
        return None
    payload = {
        "episode_id": None,
        "observation_id": observation_id,
        "from_conclusion": from_conclusion,
        "to_conclusion": to_conclusion,
        "from_model_hash": (
            from_interpretation.get("calibration_model_hash") if from_interpretation else None
        ),
        "to_model_hash": (
            to_interpretation.get("calibration_model_hash") if to_interpretation else None
        ),
        "projection_algorithm_version": P0_ALGORITHM_VERSION,
    }
    return repository.append_measurement_event(
        administration_id=administration_id,
        kind="measurement_reinterpretation",
        algorithm_version=P0_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        clock=clock,
    )
