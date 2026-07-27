"""End-to-end: an unrenderable instrument never reaches a learner, by any route.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3; implementation plan item
6.4, and the Stage 6 adversarial review that found the guard applied at two
boundaries out of seven.

``tests/test_instrument_serving.py`` pins the PREDICATE. These pin the
JOURNEYS, and they are a different claim. The predicate being correct means
nothing if the queue asks it and the retry picker does not — the learner reaches
the same item through a link, a repair episode or an exam, gets the error-hunt
prompt ("correct the worked solution below") with no solution under it, answers
blind, and the grader (which DOES receive the solution) marks every plant
missed. The projection then banks negative facet mass for a repair the learner
was never shown the material to make. That harmful write is manufactured by
whichever serving path forgot to ask, so every serving path is tested here, not
just the predicate they all share.

The items are authored through the ordinary vault path — YAML on disk, loaded by
``load_vault``, synced by ``sync_vault_state`` — and never by monkeypatching
``unservable_reason``. A test that stubs the predicate proves the stub is wired,
not that an authored item is refused, and the authoring prompts actively
commission both of these instruments today.

Two shapes of refusal, and the difference is deliberate:

* **Selection** paths (due queue, probe, primed retry, remediation, exam) choose
  among many. They SKIP the item and pick another, and the skip is visible in
  the path's own reason channel — an invisible skip is indistinguishable from
  the picker being broken.
* **Presentation** paths (direct open by id) have nothing to fall back to. They
  refuse with a typed code carrying the arm and its remedy. Not ``not_found``:
  the item exists, passed every gate, and is in the learner's vault, so
  "not found" is a lie they cannot act on.

DELETION IS THE POINT. When the renderer lands, `unservable_reason` loses an arm
and these tests go red — every one of them, by name, saying which journey just
changed. That is the visible decision the predicate's module docstring promises.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.exam_pool import reserve_exam_pool
from learnloop.services.instrument_serving import UNSERVABLE_REMEDIES
from learnloop.services.probe_episodes import (
    eligible_instruments,
    enter_episode,
    next_probe_item,
)
from learnloop.services.remediation import (
    RemediationError,
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.errors import SidecarError

from tests.helpers import (
    NOW,
    NOW_ISO,
    admit_probe_instrument_card,
    create_basic_vault,
    seed_due_item,
)

CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"

#: The plain item `create_basic_vault` writes. Every journey must land on this
#: one (or on `SERVABLE_SIBLING`) rather than on either instrument below.
BASIC_ITEM = "pi_svd_define_001"
SERVABLE_SIBLING = "pi_svd_define_sibling"

HUNT_ITEM = "pi_hunt_unrenderable"
LADDER_ITEM = "pi_ladder_part_unrenderable"

#: id -> the arm each authored item must trip. Parametrizing on this pair is
#: what stops a journey from being tested for error hunts only; §3.A2 and §3.A3
#: are separate instruments that happen to share a refusal.
UNRENDERABLE = {
    HUNT_ITEM: "error_hunt_solution_not_rendered",
    LADDER_ITEM: "laddered_stem_stimulus_not_rendered",
}


def _base_payload(item_id: str) -> dict:
    """The fields every item in this file shares, so the instrument stands out."""

    return {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
        "difficulty": 0.5,
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
            "fatal_errors": [
                {
                    "id": "conceptual_slip",
                    "description": "Confuses SVD with a different decomposition.",
                    "max_grade": 1,
                }
            ],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _author_vault(tmp_path, *, servable_sibling: bool = True):
    """A vault holding both unrenderable instruments beside ordinary practice.

    Authored the long way on purpose. `upsert_practice_item` is the same writer
    the acceptance path uses, `load_vault` is the same loader the sidecar uses,
    and `seed_due_item` gives the learning object the mastery evidence that lets
    every item on it past the scheduler's cold-start gate — so if these
    instruments are refused, it is the servability rule refusing them and not an
    unrelated filter that would have hidden them anyway.

    ``servable_sibling`` is the control: with it, a selection path has somewhere
    to go and must go there; without it, the path has nothing left and must say
    so in words that name the servability rule.
    """

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)

    if servable_sibling:
        upsert_practice_item(vault_root, _base_payload(SERVABLE_SIBLING), clock=CLOCK)

    # §3.A3: the whole stimulus is the worked solution, and the practice DTO
    # does not carry it.
    upsert_practice_item(
        vault_root,
        _base_payload(HUNT_ITEM)
        | {
            "practice_mode": "constructed_response",
            "prompt": "Correct the worked solution below.",
            "capability": "procedure_execution",
            "surface_family": "worked_repair",
            "error_hunt": {
                "worked_solution_md": (
                    "step 1: A = U S V^T\nstep 2: S is orthogonal\nstep 3: done"
                ),
                "planted_errors": [
                    {
                        "id": "pe_sigma_orthogonal",
                        "step_ref": "step 2",
                        "source": "facet_error_signature",
                        "error_signature": "S is orthogonal",
                        "required_repair": "S is diagonal with non-negative entries",
                        "facet_id": "recall",
                    }
                ],
            },
        },
        clock=CLOCK,
    )

    # §3.A2: the whole stimulus is the shared setup the parts climb, and the
    # practice DTO does not carry that either.
    upsert_practice_item(
        vault_root,
        _base_payload(LADDER_ITEM)
        | {
            "prompt": "Part 2: which factor carries the singular values?",
            "capability": "schema_interpretation",
            "laddered_stem": {
                "stem_id": "stem_svd_ladder",
                "part_index": 1,
                "part_count": 3,
                "stimulus_md": "Let A be the 3x2 matrix given above, with A = U S V^T.",
            },
        },
        clock=CLOCK,
    )

    repository = seed_due_item(paths)
    vault = load_vault(vault_root)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def _sidecar(paths):
    """A loaded sidecar context, the way the app reaches these handlers."""

    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    context = SidecarContext()
    context.load(paths.root)
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _authored(vault) -> None:
    """Both instruments really are in the vault, carrying their contracts.

    Every assertion below is of the form "this id is absent". That family of
    assertion passes trivially if the authoring never happened, so it is checked
    once, explicitly, in each journey.
    """

    assert vault.practice_items[HUNT_ITEM].error_hunt is not None
    assert vault.practice_items[LADDER_ITEM].laddered_stem is not None


# ---------------------------------------------------------------------------
# Journey 1: the due queue
# ---------------------------------------------------------------------------


def test_the_due_queue_never_offers_an_unrenderable_instrument(tmp_path):
    """Through the sidecar, not just the scheduler: the DTO layer is the surface.

    `build_due_queue` is where the guard lives, but the learner meets the queue
    through `get_today_queue`, which reloads the vault, re-syncs state and
    serializes each pick. Asserting on the RPC result is what makes this a
    journey rather than a second unit test of the same function.
    """

    paths, vault, _repository = _author_vault(tmp_path)
    _authored(vault)
    ctx = _sidecar(paths)

    result = _call(ctx, "get_today_queue", {"sessionId": "sess_journey_queue"})

    offered = {
        item["practiceItemId"]
        for section in result["sections"]
        for item in section["items"]
    }
    assert offered, "the queue must offer SOMETHING, or absence proves nothing"
    assert BASIC_ITEM in offered
    assert offered.isdisjoint(UNRENDERABLE)


# ---------------------------------------------------------------------------
# Journey 2: probe selection
# ---------------------------------------------------------------------------


def test_probe_selection_never_offers_an_unrenderable_instrument(tmp_path):
    """A diagnostic episode is the strongest case for the rule, not an exception.

    An admitted Instrument Card makes an item a probe candidate, and nothing in
    admission looks at whether the stimulus renders — the card describes the
    LIKELIHOOD model, the contract describes the stimulus. So an error hunt can
    be a perfectly valid instrument on paper and still be unanswerable on the
    screen, and a probe observation is precisely the write that must not be
    fabricated: it moves a posterior over the learner's beliefs.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    admit_probe_instrument_card(
        repository, items=(BASIC_ITEM, HUNT_ITEM, LADDER_ITEM)
    )
    vault = load_vault(paths.root)

    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    assert episode.status == "in_progress"

    candidates = eligible_instruments(vault, repository, episode)
    eligible_ids = {entry.item.id for entry in candidates}
    assert BASIC_ITEM in eligible_ids
    assert eligible_ids.isdisjoint(UNRENDERABLE)

    # The read-only "what's next in this block" peek is a second door onto the
    # same slate, and the UI jumps straight through it between attempts.
    peek = next_probe_item(vault, repository, LO_ID)
    assert peek is not None
    assert peek.item.id not in UNRENDERABLE


# ---------------------------------------------------------------------------
# Journey 3: the primed retry
# ---------------------------------------------------------------------------


def _missed_attempt(vault, repository, item_id: str = BASIC_ITEM):
    """One self-graded miss, which is what opens the primed-retry offer."""

    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="Something about eigenvalues.",
            attempt_type="independent_attempt",
            hints_used=0,
        ),
        SelfGradeInput(criterion_points={"correctness": 1}, fatal_errors=[], confidence=2),
        clock=CLOCK,
    )


def test_the_primed_retry_skips_unrenderable_siblings_and_serves_a_real_one(tmp_path):
    """Skip and pick another — and say which ones were skipped.

    The retry lands on an attempt the learner just got wrong. Serving an
    unanswerable instrument there does not merely waste the retry; it writes a
    second failure onto the facet that just failed, which is the strongest
    negative evidence the projection can receive.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    attempt = _missed_attempt(vault, repository)
    ctx = _sidecar(paths)

    result = _call(ctx, "start_primed_retry", {"attemptId": attempt.attempt_id})

    assert result["available"] is True
    assert result["generated"] is False
    assert result["practice_item"]["id"] == SERVABLE_SIBLING
    # Visible, on the SUCCESS path: the learner got the retry the picker's
    # second choice produced, and this is the only record of the first choice.
    skipped = {entry["reason"] for entry in result["unservable_skips"]}
    assert skipped == set(UNRENDERABLE.values())
    assert {entry["practice_item_id"] for entry in result["unservable_skips"]} == set(
        UNRENDERABLE
    )


def test_a_primed_retry_with_only_unrenderable_siblings_says_why(tmp_path):
    """No fallback left: the reason the learner sees must name the real cause.

    Without the skip list this path reports "no other item exists for this topic
    yet", which is false — two exist — and sends whoever reads it hunting an
    authoring bug instead of the missing renderer.
    """

    paths, vault, repository = _author_vault(tmp_path, servable_sibling=False)
    _authored(vault)
    attempt = _missed_attempt(vault, repository)
    ctx = _sidecar(paths)

    result = _call(ctx, "start_primed_retry", {"attemptId": attempt.attempt_id})

    assert result["available"] is False
    assert result["practice_item"] is None
    assert {entry["reason"] for entry in result["unservable_skips"]} == set(
        UNRENDERABLE.values()
    )
    assert UNSERVABLE_REMEDIES["error_hunt_solution_not_rendered"] in result["reason"]


# ---------------------------------------------------------------------------
# Journey 4: remediation treatment
# ---------------------------------------------------------------------------


def _repair_episode(vault, repository):
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix; eigendecomposition needs a square one.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=CLOCK,
    )
    episode = start_remediation_episode(repository, misconception_id, clock=CLOCK)
    prescribe_remediation(vault, repository, episode["id"], clock=CLOCK)
    return episode["id"]


def test_remediation_treatment_never_prescribes_an_unrenderable_instrument(tmp_path):
    """The primed/cold pair IS the measurement of whether the repair took.

    Both slots, not just the primed one: the cold retry is the unassisted half
    days later, and an unanswerable cold item records the repair as failed on
    the exact evidence the episode is judged by.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    episode_id = _repair_episode(vault, repository)

    result = start_remediation_treatment(vault, repository, episode_id, clock=CLOCK)

    assert result["primed_item_id"] not in UNRENDERABLE
    assert result["cold_item_id"] not in UNRENDERABLE
    assert {entry["reason"] for entry in result["unservable_skips"]} == set(
        UNRENDERABLE.values()
    )


def test_a_repair_with_only_unrenderable_items_refuses_by_name(tmp_path):
    """Deactivate the ordinary items so the ranking has nothing servable left.

    They are deactivated rather than deleted because the point is that the
    learning object HAS items: the error message must not read as "this topic
    has no practice".
    """

    paths, vault, repository = _author_vault(tmp_path, servable_sibling=False)
    _authored(vault)
    repository.upsert_practice_item_state(BASIC_ITEM, active=False)
    episode_id = _repair_episode(vault, repository)

    with pytest.raises(RemediationError) as exc:
        start_remediation_treatment(vault, repository, episode_id, clock=CLOCK)

    assert "not servable" in str(exc.value)
    assert UNSERVABLE_REMEDIES["error_hunt_solution_not_rendered"] in str(exc.value)


# ---------------------------------------------------------------------------
# Journey 5: opening an item directly, by id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("item_id,reason", sorted(UNRENDERABLE.items()))
def test_opening_an_unrenderable_item_by_id_refuses_with_its_reason(
    tmp_path, item_id: str, reason: str
):
    """A deep link is the one route no selection filter can cover.

    `open_queue_item` takes an id, not a queue position: a restored session, a
    stale client, a bookmarked link or an inspector jump all arrive here holding
    an item the queue would never have offered. The refusal is a distinct typed
    code rather than `not_found` because the learner is entitled to know the
    item exists and what is missing — a blank screen or a 404 makes them look
    for a mistake they did not make.
    """

    paths, vault, _repository = _author_vault(tmp_path)
    _authored(vault)
    ctx = _sidecar(paths)

    with pytest.raises(SidecarError) as exc:
        _call(ctx, "open_queue_item", {"practiceItemId": item_id})

    assert exc.value.code == "item_not_servable"
    assert exc.value.code != "not_found"
    assert exc.value.details["reason"] == reason
    assert exc.value.details["practice_item_id"] == item_id
    assert exc.value.details["remedy"] == UNSERVABLE_REMEDIES[reason]
    # The remedy travels in the message too: the toast is what the learner reads.
    assert UNSERVABLE_REMEDIES[reason] in exc.value.message


def test_opening_a_servable_item_by_id_still_works(tmp_path):
    """The control. A guard that refuses everything is not a guard."""

    paths, _vault, _repository = _author_vault(tmp_path)
    ctx = _sidecar(paths)

    detail = _call(ctx, "open_queue_item", {"practiceItemId": BASIC_ITEM})

    assert detail["id"] == BASIC_ITEM


def test_an_unknown_item_id_still_reports_not_found(tmp_path):
    """The new code must not swallow the old one.

    "Does not exist" and "exists but cannot be shown" are different facts with
    different remedies, and collapsing them is exactly the confusion this
    boundary was added to end.
    """

    paths, _vault, _repository = _author_vault(tmp_path)
    ctx = _sidecar(paths)

    with pytest.raises(SidecarError) as exc:
        _call(ctx, "open_queue_item", {"practiceItemId": "pi_does_not_exist"})

    assert exc.value.code == "not_found"


# ---------------------------------------------------------------------------
# Journey 6: the held-out exam
# ---------------------------------------------------------------------------


def test_exam_reservation_never_reserves_an_unrenderable_instrument(tmp_path):
    """The last place to serve one: an exam item cannot be skipped mid-sitting.

    A reservation is durable and held out from ordinary practice, so an
    unrenderable reservation both fabricates a failed exam answer and burns the
    item out of the practice pool while doing it.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    goal = vault.goals[0]

    report = reserve_exam_pool(vault, repository, goal, item_count=4, clock=CLOCK)

    assert report.reserved_item_ids, "an empty pool would pass this test vacuously"
    assert set(report.reserved_item_ids).isdisjoint(UNRENDERABLE)


# ---------------------------------------------------------------------------
# Journey 7: the delayed follow-up lane, which re-enters the queue by id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("item_id", sorted(UNRENDERABLE))
def test_a_delayed_followup_cannot_resurrect_a_refused_item(tmp_path, item_id: str):
    """The second door onto the due queue, and it opens at maximum priority.

    `build_due_queue`'s main loop drops unrenderable instruments, and then
    `_insert_pending_followups` rebuilds a `ScheduledItem` for any pending
    follow-up task by id and pushes it ABOVE every ordinary pick. So a cold retry
    of a repair, or a §5.7 held-out check on a certified skill, could serve the
    exact item the loop had just excluded — top of the queue, with the reason
    "unassisted cold retry" printed under it.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    repository.create_followup_task(
        kind="cold_retry",
        case_kind="misconception",
        case_ref="mc_synthetic",
        source_attempt_id=None,
        remediation_episode_id=None,
        # Already ripe: the delay is not what is keeping this item out.
        not_before="2026-05-01T00:00:00Z",
        expires_at="2026-12-01T00:00:00Z",
        selected_item_id=item_id,
        clock=CLOCK,
    )
    assert item_id in {
        row["practice_item_id"]
        for row in repository.pending_followup_practice_items(clock=CLOCK)
    }, "the follow-up lane must really be offering this item, or absence proves nothing"

    queue = build_due_queue(
        vault, repository, session=SchedulerSession(session_id="sess_followup"), clock=CLOCK
    )

    assert item_id not in {entry.practice_item_id for entry in queue}


# ---------------------------------------------------------------------------
# Journey 7b: the intervention follow-up chosen after a failed attempt
# ---------------------------------------------------------------------------


def _surprising_miss(vault, repository):
    """A confidently-wrong attempt, which is what fires the follow-up gate."""

    from learnloop.db.repositories import MasteryState

    from tests.helpers import ALGORITHM_VERSION

    repository.upsert_mastery_state(
        MasteryState(LO_ID, 2.0, 1.0, 3, NOW_ISO, ALGORITHM_VERSION, NOW_ISO)
    )
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=BASIC_ITEM, learner_answer_md="x"),
        SelfGradeInput(
            criterion_points={"correctness": 1}, confidence=4, error_type="conceptual_slip"
        ),
        clock=CLOCK,
    )


def test_the_intervention_followup_skips_unrenderable_siblings(tmp_path):
    """The follow-up is queued straight after a failure, so it lands on a raw nerve.

    The skip is recorded on the decision-features row rather than in a log,
    beside `candidate_slate` and `misconception_gate_blocked`: this row is what
    the gate fitter and the follow-up audit read, and a candidate that
    disappeared from the slate with no reason is a false negative in both.
    """

    from learnloop.services.followups import evaluate_negative_surprise_followup

    _paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    result = _surprising_miss(vault, repository)
    assert result.surprise_direction == "negative"

    decision = evaluate_negative_surprise_followup(
        vault,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
        available_minutes=30,
    )

    assert decision.triggered is True
    assert decision.practice_item_id == SERVABLE_SIBLING
    features = repository.decision_features(
        decision_id=result.attempt_id, decision_type="followup"
    )
    skips = (features or {}).get("context", {}).get("unservable_skips") or []
    assert {entry["reason"] for entry in skips} == set(UNRENDERABLE.values())


# ---------------------------------------------------------------------------
# Journey 8: the staged (P4) controller, a whole parallel administration stack
# ---------------------------------------------------------------------------


def test_the_staged_controller_excludes_an_unrenderable_instrument_by_name(tmp_path):
    """Excluded with a typed reason in the receipt, not filtered out of existence.

    The staged path's contract is that every candidate is evaluated and every
    exclusion is written down (§16.1 exclusion-reason completeness), so this
    guard is a constraint rather than a snapshot filter — an item that vanished
    from the snapshot would be unexplainable in the decision receipt, which is
    the same invisible refusal the Stage 6 review objected to in the queue.
    """

    from learnloop.services.constraint_engine import feasible_set
    from learnloop.services.controller_snapshot import build_snapshot

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)

    snapshot = build_snapshot(vault, repository, clock=CLOCK)
    report = feasible_set(snapshot.candidates, snapshot)

    feasible_ids = {candidate.candidate_ref for candidate in report.feasible}
    assert BASIC_ITEM in feasible_ids
    assert feasible_ids.isdisjoint(UNRENDERABLE)
    for item_id, reason in UNRENDERABLE.items():
        codes = {
            (exclusion.constraint_key, exclusion.reason)
            for exclusion in report.per_candidate[item_id].exclusions
        }
        assert ("stimulus_renderable", reason) in codes


# ---------------------------------------------------------------------------
# Journey 9: the §5.7 held-out cold probe, whose verdict is `false_certification`
# ---------------------------------------------------------------------------


def test_the_certification_cold_probe_refuses_an_unrenderable_held_out_item(tmp_path):
    """The most expensive place to serve one: this probe can REVOKE a certificate.

    §5.7's delayed cold probe is the only external validity check on a
    certificate. Its verdict is `false_certification`, and an unrenderable probe
    guarantees a miss — so the learner's certified skill would be revoked on
    evidence they were never shown the material to produce.

    The decision arm is its own, not `no_candidate_item`: candidates exist, on a
    held-out surface, and the remedy is the renderer rather than more authoring.
    """

    from learnloop.services.certification_cold_probe import (
        current_certificate,
        select_held_out_probe_item,
    )
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    from tests.helpers import set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    # One-component blueprint at the cell the basic vault's item observes, so a
    # single full-marks unassisted attempt produces a real certificate.
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    data["blueprints"] = [
        {
            "id": "bp1",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "r1",
                    "composition": "conjunctive",
                    "all_of": [
                        {
                            "facet": "recall",
                            "capability": "schema_interpretation",
                            "modality": "hard",
                        }
                    ],
                }
            ],
        }
    ]
    write_yaml(lo_path, data)
    # The ONLY held-out candidate is an error hunt: a distinct surface family
    # (so the surface rule admits it) carrying a contract the screen cannot show.
    upsert_practice_item(
        tmp_path / "vault",
        _base_payload(HUNT_ITEM)
        | {
            "surface_family": "worked_repair",
            "error_hunt": {
                "worked_solution_md": "step 1: A = U S V^T\nstep 2: S is orthogonal",
                "planted_errors": [
                    {
                        "id": "pe_sigma_orthogonal",
                        "step_ref": "step 2",
                        "source": "facet_error_signature",
                        "error_signature": "S is orthogonal",
                        "required_repair": "S is diagonal with non-negative entries",
                        "facet_id": "recall",
                    }
                ],
            },
        },
        clock=CLOCK,
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=BASIC_ITEM,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=0,
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None, "fixture must actually certify"

    selection = select_held_out_probe_item(vault, repository, certificate)

    assert selection.practice_item_id is None
    assert selection.decision == "no_servable_item"
    assert selection.decision != "no_candidate_item"
    assert selection.rejected_as_unservable == (HUNT_ITEM,)
    assert selection.as_dict()["rejected_as_unservable"] == [HUNT_ITEM]


# ---------------------------------------------------------------------------
# The cross-journey claim
# ---------------------------------------------------------------------------


def test_no_journey_in_this_file_leaves_an_arm_untested():
    """Every arm of the predicate is exercised by an authored item above.

    The failure this catches is a third arm being added to `unservable_reason`
    with no journey behind it — the arm would be enforced at the two boundaries
    someone remembered and silently absent from the other five, which is exactly
    the state the Stage 6 review found.
    """

    assert set(UNRENDERABLE.values()) == set(UNSERVABLE_REMEDIES)
