"""End-to-end: the two retired instrument classes now reach the learner, by every route.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A2/§3.A3; implementation plan item
6.4, and the Stage 6 adversarial review that found the guard applied at two
boundaries out of seven.

WHAT THESE USED TO ASSERT, AND WHY THEY NOW ASSERT THE OPPOSITE. Error hunts
(§3.A3) and laddered-stem parts (§3.A2) were authored, gated, stored and audited
with no renderer at all, so ``instrument_serving.unservable_reason`` refused the
whole class and this file pinned that refusal on every serving path — because a
predicate being correct means nothing if the queue asks it and the retry picker
does not. Serving one produced a *silent* failure: the learner asked to repair
work they could not see, the grader (which does receive the solution) marking
every plant missed, negative facet mass banked for a repair nobody was shown the
material to make.

The renderer landed. ``handlers/serializers.item_presentation`` emits
``laddered_stem_stimulus`` and ``error_hunt_worked_solution`` blocks, and
``components/ItemPresentation.tsx`` frames both on the practice, exam and
golden-path surfaces. That was the one legitimate way to remove the filter, so
the arms are deleted and every journey below is inverted: the same seven routes
must now DELIVER these instruments, not skip them. Inverting rather than deleting
this file is the point — the un-gating is a decision, and a decision needs a
record that the ungated item really is reachable through each door.

What is NOT retired, and is tested here at the end: blank content is still a
typed refusal at the serialization layer. "Renderable class" and "this item
carries its stimulus" are different facts — ``stimulus_md`` is Optional on the
model and ``worked_solution_md`` can be the empty string — and an empty block
rendered as an empty div is the original silent failure wearing the new payload.

The items are authored through the ordinary vault path — YAML on disk, loaded by
``load_vault``, synced by ``sync_vault_state`` — and never by monkeypatching the
predicate. A test that stubs it proves the stub is wired, not that an authored
item is served.
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

#: The plain item `create_basic_vault` writes, and an ordinary sibling. Together
#: they are the control: a route that only ever lands on these would pass the
#: inverted assertions vacuously, so every journey names the instrument it wants.
BASIC_ITEM = "pi_svd_define_001"
SERVABLE_SIBLING = "pi_svd_define_sibling"

HUNT_ITEM = "pi_hunt_error_hunt"
LADDER_ITEM = "pi_ladder_part"

#: id -> the contract each authored item carries. Parametrizing on this pair is
#: what stops a journey from being tested for error hunts only; §3.A2 and §3.A3
#: are separate instruments that happened to share a refusal and now share a
#: renderer.
INSTRUMENTS = {HUNT_ITEM: "error_hunt", LADDER_ITEM: "laddered_stem"}

HUNT_SOLUTION = "step 1: A = U S V^T\nstep 2: S is orthogonal\nstep 3: done"
LADDER_STIMULUS = "Let A be the 3x2 matrix given above, with A = U S V^T."


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


def _hunt_payload(
    item_id: str = HUNT_ITEM,
    *,
    worked_solution_md: str = HUNT_SOLUTION,
    capability: str = "procedure_execution",
) -> dict:
    """§3.A3: the whole stimulus is the worked solution the learner repairs.

    ``capability`` is a parameter because the rung decides which contract cell
    the item can observe, and the cold-probe journey needs its one candidate to
    land on the cell the certificate names.
    """

    return _base_payload(item_id) | {
        "practice_mode": "constructed_response",
        "prompt": "Correct the worked solution below.",
        "surface_family": "worked_repair",
        "capability": capability,
        "error_hunt": {
            "worked_solution_md": worked_solution_md,
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
    }


def _ladder_payload(item_id: str = LADDER_ITEM, *, stimulus_md: str | None = LADDER_STIMULUS) -> dict:
    """§3.A2: the whole stimulus is the shared setup the parts climb."""

    stem: dict = {"stem_id": "stem_svd_ladder", "part_index": 1, "part_count": 3}
    if stimulus_md is not None:
        stem["stimulus_md"] = stimulus_md
    return _base_payload(item_id) | {
        "prompt": "Part 2: which factor carries the singular values?",
        "capability": "schema_interpretation",
        "laddered_stem": stem,
    }


def _author_vault(tmp_path, *, servable_sibling: bool = True):
    """A vault holding both instruments beside ordinary practice.

    Authored the long way on purpose. `upsert_practice_item` is the same writer
    the acceptance path uses, `load_vault` is the same loader the sidecar uses,
    and `seed_due_item` gives the learning object the mastery evidence that lets
    every item on it past the scheduler's cold-start gate — so if these
    instruments now reach a learner, it is because the servability rule stopped
    refusing them and not because some unrelated filter changed.

    ``servable_sibling`` is the control that inverted with the rest: WITHOUT it,
    a selection path has nothing but these two instruments left, and the sharp
    claim is that it now serves one instead of refusing by name.
    """

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)

    if servable_sibling:
        upsert_practice_item(vault_root, _base_payload(SERVABLE_SIBLING), clock=CLOCK)
    upsert_practice_item(vault_root, _hunt_payload(), clock=CLOCK)
    upsert_practice_item(vault_root, _ladder_payload(), clock=CLOCK)

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

    Cheap, and it keeps every "this id is present" assertion below honest about
    what it is measuring: the item has to exist AND carry the contract, or the
    journey is only testing that ordinary practice still works.
    """

    assert vault.practice_items[HUNT_ITEM].error_hunt is not None
    assert vault.practice_items[LADDER_ITEM].laddered_stem is not None


# ---------------------------------------------------------------------------
# Journey 1: the due queue
# ---------------------------------------------------------------------------


def test_the_due_queue_offers_both_instruments(tmp_path):
    """Through the sidecar, not just the scheduler: the DTO layer is the surface.

    `build_due_queue` is where the filter used to live, but the learner meets the
    queue through `get_today_queue`, which reloads the vault, re-syncs state and
    serializes each pick — and serialization is where the surviving blank-content
    refusal lives. Asserting on the RPC result is what makes this a journey and
    not a second unit test of the predicate.
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
    assert BASIC_ITEM in offered
    assert set(INSTRUMENTS) <= offered


# ---------------------------------------------------------------------------
# Journey 2: probe selection
# ---------------------------------------------------------------------------


def test_probe_selection_offers_both_instruments(tmp_path):
    """A diagnostic episode was the strongest case for the old rule; it is now
    the strongest case for the un-gating.

    An admitted Instrument Card makes an item a probe candidate, and admission
    never looked at the stimulus — the card describes the LIKELIHOOD model, the
    contract describes what the learner sees. With the stimulus on the screen,
    the two agree again: a probe observation moves a posterior over the learner's
    beliefs, and it may now be collected from the instruments §3.A2/§3.A3 were
    designed for.
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
    assert set(INSTRUMENTS) <= eligible_ids

    # The read-only "what's next in this block" peek is a second door onto the
    # same slate, and the UI jumps straight through it between attempts.
    peek = next_probe_item(vault, repository, LO_ID)
    assert peek is not None


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


def test_the_primed_retry_skips_nothing_for_servability(tmp_path):
    """The skip channel stays wired and stays empty.

    `unservable_skips` is how the picker's second choice explains the first, and
    it is still built from `unservable_refusal` — so an empty list here is the
    honest statement "nothing was skipped for servability", not a missing field
    that would hide the next renderer-blocked class.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    attempt = _missed_attempt(vault, repository)
    ctx = _sidecar(paths)

    result = _call(ctx, "start_primed_retry", {"attemptId": attempt.attempt_id})

    assert result["available"] is True
    assert result["generated"] is False
    assert result["practice_item"]["id"] in {SERVABLE_SIBLING, *INSTRUMENTS}
    assert result["unservable_skips"] == []


def test_a_primed_retry_whose_only_siblings_are_instruments_serves_one(tmp_path):
    """The inversion at its sharpest.

    This case used to report "unavailable" and name the missing renderer. The two
    siblings it had to refuse are now the two it may serve, so a learner who just
    missed an item gets a real retry on the instrument class designed to localize
    the miss rather than an apology.
    """

    paths, vault, repository = _author_vault(tmp_path, servable_sibling=False)
    _authored(vault)
    attempt = _missed_attempt(vault, repository)
    ctx = _sidecar(paths)

    result = _call(ctx, "start_primed_retry", {"attemptId": attempt.attempt_id})

    assert result["available"] is True
    assert result["practice_item"]["id"] in INSTRUMENTS
    assert result["unservable_skips"] == []


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


def test_remediation_treatment_skips_nothing_for_servability(tmp_path):
    """The primed/cold pair IS the measurement of whether the repair took, and an
    error hunt is a natural instrument for it: the planting location is known, so
    a miss localizes for free."""

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    episode_id = _repair_episode(vault, repository)

    result = start_remediation_treatment(vault, repository, episode_id, clock=CLOCK)

    assert result["primed_item_id"] is not None
    assert result["unservable_skips"] == []


def test_a_repair_whose_only_items_are_instruments_now_prescribes_one(tmp_path):
    """Used to raise `RemediationError("not servable")` with the remedy inline.

    The ordinary item is deactivated rather than deleted, so the ranking has
    nothing but the two instruments left — which is now enough to run the
    episode instead of a reason to refuse it.
    """

    paths, vault, repository = _author_vault(tmp_path, servable_sibling=False)
    _authored(vault)
    repository.upsert_practice_item_state(BASIC_ITEM, active=False)
    episode_id = _repair_episode(vault, repository)

    result = start_remediation_treatment(vault, repository, episode_id, clock=CLOCK)

    assert result["primed_item_id"] in INSTRUMENTS
    assert result["unservable_skips"] == []


# ---------------------------------------------------------------------------
# Journey 5: opening an item directly, by id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("item_id,contract", sorted(INSTRUMENTS.items()))
def test_opening_an_instrument_by_id_serves_its_whole_stimulus(
    tmp_path, item_id: str, contract: str
):
    """A deep link is the route no selection filter ever covered, and the one
    where the refusal was most visible: a restored session, a stale client, a
    bookmark or an inspector jump used to hit `item_not_servable`.

    Asserting the BLOCK, not just the absence of the error: the whole reason the
    class could be un-gated is that the payload now carries the stimulus, so a
    200 with a prompt-only payload would be the original defect with a friendlier
    status.
    """

    paths, vault, _repository = _author_vault(tmp_path)
    _authored(vault)
    ctx = _sidecar(paths)

    detail = _call(ctx, "open_queue_item", {"practiceItemId": item_id})

    assert detail["id"] == item_id
    blocks = {block["kind"]: block["markdown"] for block in detail["presentation"]["blocks"]}
    if contract == "error_hunt":
        assert blocks["error_hunt_worked_solution"] == HUNT_SOLUTION
    else:
        assert blocks["laddered_stem_stimulus"] == LADDER_STIMULUS


def test_opening_an_ordinary_item_by_id_still_works(tmp_path):
    """The control. A guard that refuses nothing must also not break anything."""

    paths, _vault, _repository = _author_vault(tmp_path)
    ctx = _sidecar(paths)

    detail = _call(ctx, "open_queue_item", {"practiceItemId": BASIC_ITEM})

    assert detail["id"] == BASIC_ITEM


def test_an_unknown_item_id_still_reports_not_found(tmp_path):
    """"Does not exist" and "exists but cannot be shown" stay different facts
    with different remedies; the second is now data-level only."""

    paths, _vault, _repository = _author_vault(tmp_path)
    ctx = _sidecar(paths)

    with pytest.raises(SidecarError) as exc:
        _call(ctx, "open_queue_item", {"practiceItemId": "pi_does_not_exist"})

    assert exc.value.code == "not_found"


# ---------------------------------------------------------------------------
# Journey 6: the held-out exam
# ---------------------------------------------------------------------------


def test_exam_reservation_may_reserve_an_instrument(tmp_path):
    """An exam item cannot be skipped mid-sitting, which is why the exam pool was
    the last place anyone wanted an unrenderable reservation — and why it is a
    real gain that a held-out sitting can now be built from these instruments,
    whose §3.A2/§3.A3 cost argument is that they buy several columns per context
    load."""

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    goal = vault.goals[0]

    report = reserve_exam_pool(vault, repository, goal, item_count=4, clock=CLOCK)

    assert report.reserved_item_ids, "an empty pool would pass this test vacuously"
    assert set(report.reserved_item_ids) & set(INSTRUMENTS)


# ---------------------------------------------------------------------------
# Journey 7: the delayed follow-up lane, which re-enters the queue by id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("item_id", sorted(INSTRUMENTS))
def test_a_delayed_followup_can_serve_an_instrument(tmp_path, item_id: str):
    """The second door onto the due queue, and it opens at maximum priority.

    `_insert_pending_followups` rebuilds a `ScheduledItem` by id and pushes it
    ABOVE every ordinary pick, so this lane used to be the way a refused item
    could sneak back to the top of the queue. Now it is simply the cold retry of
    a repair working as designed on the instrument that best localizes it.
    """

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)
    repository.create_followup_task(
        kind="cold_retry",
        case_kind="misconception",
        case_ref="mc_synthetic",
        source_attempt_id=None,
        remediation_episode_id=None,
        # Already ripe: the delay is not what would keep this item out.
        not_before="2026-05-01T00:00:00Z",
        expires_at="2026-12-01T00:00:00Z",
        selected_item_id=item_id,
        clock=CLOCK,
    )
    assert item_id in {
        row["practice_item_id"]
        for row in repository.pending_followup_practice_items(clock=CLOCK)
    }, "the follow-up lane must really be offering this item, or presence proves nothing"

    queue = build_due_queue(
        vault, repository, session=SchedulerSession(session_id="sess_followup"), clock=CLOCK
    )

    assert item_id in {entry.practice_item_id for entry in queue}


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


def test_the_intervention_followup_records_no_servability_skips(tmp_path):
    """The skip list lives on the decision-features row beside `candidate_slate`
    and `misconception_gate_blocked`, because that row is what the gate fitter and
    the follow-up audit read. It stays written and stays empty: a candidate that
    vanished from the slate with no reason is a false negative in both, whichever
    direction the predicate happens to answer."""

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
    assert decision.practice_item_id in {SERVABLE_SIBLING, *INSTRUMENTS}
    features = repository.decision_features(
        decision_id=result.attempt_id, decision_type="followup"
    )
    skips = (features or {}).get("context", {}).get("unservable_skips") or []
    assert skips == []


# ---------------------------------------------------------------------------
# Journey 8: the staged (P4) controller, a whole parallel administration stack
# ---------------------------------------------------------------------------


def test_the_staged_controller_admits_both_instruments(tmp_path):
    """The `stimulus_renderable` constraint stays in the feasible-set pass and
    stops excluding anything.

    It is a constraint rather than a snapshot filter because §16.1 requires every
    exclusion to be written down, and that is worth keeping through the
    retirement: the constraint now records no exclusion, and the candidates reach
    the ranker where their score can be traded like anyone else's.
    """

    from learnloop.services.constraint_engine import feasible_set
    from learnloop.services.controller_snapshot import build_snapshot

    paths, vault, repository = _author_vault(tmp_path)
    _authored(vault)

    snapshot = build_snapshot(vault, repository, clock=CLOCK)
    report = feasible_set(snapshot.candidates, snapshot)

    feasible_ids = {candidate.candidate_ref for candidate in report.feasible}
    assert BASIC_ITEM in feasible_ids
    assert set(INSTRUMENTS) <= feasible_ids
    for item_id in INSTRUMENTS:
        keys = {
            exclusion.constraint_key
            for exclusion in report.per_candidate[item_id].exclusions
        }
        assert "stimulus_renderable" not in keys
    # The snapshot still carries the field the constraint reads, so a future arm
    # reaches the receipt without another plumbing pass.
    by_ref = {candidate.candidate_ref: candidate for candidate in snapshot.candidates}
    assert by_ref[HUNT_ITEM].unservable_reason is None


# ---------------------------------------------------------------------------
# Journey 9: the §5.7 held-out cold probe, whose verdict is `false_certification`
# ---------------------------------------------------------------------------


def test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item(tmp_path):
    """The most expensive route: this probe can REVOKE a certificate.

    §5.7's delayed cold probe is the only external validity check on a
    certificate, so an unrenderable probe guaranteed a miss and would have
    revoked a certified skill on evidence the learner was never shown the
    material to produce — which is why the picker grew a `no_servable_item` arm
    distinct from `no_candidate_item`. That arm survives for the next blocked
    class; what changed is that an error hunt on a held-out surface is now a
    perfectly good probe, and here it is the only candidate.
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
    # The ONLY held-out candidate is an error hunt, on a distinct surface family
    # so the held-out rule admits it, at the rung the certified cell names.
    upsert_practice_item(
        tmp_path / "vault",
        _hunt_payload(capability="schema_interpretation"),
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

    assert selection.practice_item_id == HUNT_ITEM
    assert selection.decision != "no_servable_item"
    assert selection.rejected_as_unservable == ()


# ---------------------------------------------------------------------------
# What did NOT retire: blank content is still a typed refusal
# ---------------------------------------------------------------------------


def _blank_instrument_vault(tmp_path, payload: dict):
    """A vault whose only extra item carries its contract with no content.

    Deliberately its own vault rather than a fourth item in `_author_vault`: a
    blank instrument raises when the queue serializes it, so parking one beside
    the ordinary items would make every other journey in this file fail for the
    wrong reason.
    """

    paths = create_basic_vault(tmp_path / "vault")
    upsert_practice_item(tmp_path / "vault", payload, clock=CLOCK)
    seed_due_item(paths)
    return paths


def test_an_error_hunt_with_a_blank_worked_solution_is_still_refused(tmp_path):
    """The class renders; THIS item has nothing to render.

    `worked_solution_md` is a plain `str` on the model, so the empty string is
    authorable, and an empty block under "correct the worked solution below" is
    the original silent failure wearing the new payload: unanswerable prompt,
    grader marking every plant missed, negative facet mass banked. The data-level
    check is what the class-level arm was never able to do, and it stays.
    """

    blank = "pi_hunt_blank"
    paths = _blank_instrument_vault(tmp_path, _hunt_payload(blank, worked_solution_md="   "))
    ctx = _sidecar(paths)

    with pytest.raises(SidecarError) as exc:
        _call(ctx, "open_queue_item", {"practiceItemId": blank})

    assert exc.value.code == "item_stimulus_unrenderable"
    assert exc.value.details["reason"] == "error_hunt_worked_solution_blank"
    assert exc.value.details["practice_item_id"] == blank


def test_a_stem_part_with_no_stimulus_is_still_refused(tmp_path):
    """`stimulus_md` is Optional on the model, so "present" never implied
    "renderable" — a part met days after part 1, in another session, with no
    setup on the screen is unanswerable no matter how well the renderer works."""

    blank = "pi_ladder_blank"
    paths = _blank_instrument_vault(tmp_path, _ladder_payload(blank, stimulus_md=None))
    ctx = _sidecar(paths)

    with pytest.raises(SidecarError) as exc:
        _call(ctx, "open_queue_item", {"practiceItemId": blank})

    assert exc.value.code == "item_stimulus_unrenderable"
    assert exc.value.details["reason"] == "laddered_stem_stimulus_blank"
    assert exc.value.details["stem_id"] == "stem_svd_ladder"


# ---------------------------------------------------------------------------
# The cross-journey claim
# ---------------------------------------------------------------------------


def test_the_retirement_left_no_arm_behind_and_no_journey_unwritten():
    """Both directions of the file's contract, in one assertion.

    Empty today, and that IS the receipt: the arms were deleted rather than
    disabled. If a future instrument class ships ahead of its renderer, this
    fails and says so — the arm needs a remedy AND a journey above, which is the
    pairing the Stage 6 review found half-done in the first place.
    """

    assert set(UNSERVABLE_REMEDIES) == set()
