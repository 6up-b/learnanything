"""A grade taken as certain, for tests whose subject needs a cell certified by one answer.

Below ``mvp-0.8`` the canonical projection weighed an answer by its attempt type alone, so one full-marks
independent self-grade banked a whole unit of certification credit and certified its cell. That path is gone
(refactor D5): every vault that opens weighs an answer by its grade's certainty, and a self-grade under the
cold grader calibration is uncertain (its certainty bound is about 0.7), so one answer no longer certifies.

The owner's point adjudication of the grade's own leading class is a live path that makes the grade certain
(bounded trust 1, certainty 1). Its mass is then the attempt type's, exactly what the old path banked, and its
direction is the grade's, so the ledger is not revised. Tests that used the old path only to certify a cell
with one answer reach the same banked credit through it.
"""

from __future__ import annotations

import json

from learnloop.attempts.grade_resolution import append_adjudication
from learnloop.substrate.canonical_projection import project_canonical_facet_state


def make_grade_certain(vault, repository, attempt_id: str, *, clock=None, resolved_class: str | None = None) -> None:
    """Adjudicate ``attempt_id``'s grade as its own leading class (or ``resolved_class``, which must agree
    with the ledger's direction), with full trust, and re-project."""

    observation = repository.observation_by_attempt(str(attempt_id))
    assert observation is not None, "the attempt has no observation to adjudicate"
    head = repository.active_interpretation_for_observation(observation["id"])
    assert head is not None, "the attempt has no interpretation to adjudicate"
    posterior = json.loads(head["response_posterior_json"])
    leading = resolved_class or max(posterior, key=posterior.get)
    raw = repository.raw_grade_events_for_observation(observation["id"])
    append_adjudication(
        repository,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw[-1]["id"]],
        adjudicator_source="human_owner",
        resolved_class=leading,
        vault=vault,
        clock=clock,
    )
    project_canonical_facet_state(vault, repository, clock=clock)
