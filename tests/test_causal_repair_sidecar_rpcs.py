"""The P2 causal-repair RPC boundary the Tauri app actually consumes (§6).

`tests/test_causal_orchestrator.py` proves the service decides correctly. This
file guards the *wiring*: that the four learner-facing methods are reachable
over JSON-RPC, that their params models accept exactly the payloads
`apps/learnloop-tauri/src/api/client.ts` sends, and that the camelCased result
carries every field `CausalRepairStatusDto` declares.

Both halves of that contract have failed silently before. `ParamsModel` is
`extra="forbid"`, so one renamed key in the client turns into the app's
"stale sidecar schema" error; and a typed hold used to be raised as
`SidecarError("invalid_request", ...)`, which reached the learner as a toast
reading like a stack trace. A hold is a STATE — it comes back as a result.
"""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from learnloop.clock import FrozenClock
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.services.causal_orchestrator import (
    classify_probe_response,
    pinned_causal_probe,
)
from learnloop.services.causal_probe_coherence import generate_blind_prediction_bundle
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop_sidecar.handlers import practice as practice_handlers
from learnloop_sidecar.handlers.remediation import ProbeOfferInput, RepairStatusInput
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import NOW, admit_probe_instrument_card
from tests.test_causal_orchestrator import (
    CLOCK,
    LO_ID,
    PROBE_ITEM,
    _activate_probe_candidate,
    _seed_factor,
    _vault,
)
from tests.test_sidecar_contract import _rpc

#: Every field `CausalRepairStatusDto` (apps/learnloop-tauri/src/api/dto.ts)
#: declares as required. The Tauri client reads these by name.
REPAIR_STATUS_DTO_KEYS = {
    "status",
    "reason",
    "message",
    "misconceptionId",
    "factorId",
    "learningObjectId",
    "attemptId",
    "probeOffered",
    "probeDecision",
    "probeDecisionReason",
    "decisionReceiptId",
    "candidateId",
    "blindBundleIds",
    "hypothesisSetId",
    "repairClassIds",
    "commonRepairClassId",
    "pendingMachineCheckIds",
    "learnerPreference",
    "actions",
    "episode",
    "parameters",
    "evsiProvenance",
    "decisionPolicyVersion",
}


def _initialize(vault_root, request_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {"vaultPath": str(vault_root)},
    }


def _call(request_id: int, method: str, params: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def test_causal_repair_methods_are_registered_and_accept_the_client_payloads():
    """A renamed key in client.ts must fail here, not in front of a learner."""

    for name in (
        "causal_repair_status",
        "causal_probe_offer_action",
        "causal_probe_defer",
        "causal_teach_me_now",
    ):
        assert name in METHOD_REGISTRY, name

    # Byte-for-byte the payloads `api.causalRepairStatus` / `causalProbeOfferAction`
    # / `causalProbeDefer` / `causalTeachMeNow` send.
    RepairStatusInput.model_validate({"misconceptionId": "mc_1", "sessionId": None})
    ProbeOfferInput.model_validate(
        {
            "factorId": "f_1",
            "misconceptionId": "mc_1",
            "sessionId": None,
            "decisionReceiptId": None,
        }
    )
    ProbeOfferInput.model_validate(
        {"factorId": "f_1", "misconceptionId": "mc_1", "sessionId": None}
    )


def test_start_remediation_returns_the_typed_hold_instead_of_an_error(tmp_path):
    """The dead end this whole lane existed behind, closed.

    Before: `start_remediation` raised, the sidecar answered `invalid_request`,
    and the learner's only contact with P2 was an error toast. Now the hold is
    an ordinary result carrying the §6 message and actions.
    """

    _vault_obj, repository, root = _vault(tmp_path)
    # One hypothesis with no resolvable repair class -> the machine owes a
    # backfill, and principle 8 says machine gaps are bought with machine work.
    _factor_id, first_id, _second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair=None
    )

    responses = _rpc(
        [
            _initialize(root),
            _call(2, "start_remediation", {"misconceptionId": first_id}),
            _call(
                3,
                "causal_repair_status",
                {"misconceptionId": first_id, "sessionId": None},
            ),
        ]
    )

    started = responses[1]
    assert "error" not in started, started
    result = started["result"]
    assert result["episode"] is None
    status = result["repairStatus"]
    assert status["status"] == "deferred_machine_checks"
    # Copy the learner can act on, not a developer string.
    assert "machine-side checks" in status["message"]
    assert status["pendingMachineCheckIds"]
    # Nothing for the learner to do while the machine works.
    assert status["actions"] == []

    # Every field the Tauri DTO declares survives the camelCase boundary.
    assert REPAIR_STATUS_DTO_KEYS <= set(status), REPAIR_STATUS_DTO_KEYS - set(status)

    read = responses[2]["result"]["repairStatus"]
    assert read["status"] == "deferred_machine_checks"
    # A pure read records the decision but must not mint an episode.
    assert read["episode"] is None


def test_not_now_over_rpc_withdraws_the_offer_without_settling_the_ambiguity(tmp_path):
    """"Not now" means stop asking, not stop being ambiguous.

    The state stays `needs_disambiguation`; only the offer is withdrawn, and the
    escape hatch ("Teach me now") remains. The Tauri panel renders exactly what
    comes back in `actions`, so this is the assertion that keeps it from
    re-offering a check the learner declined.
    """

    _vault_obj, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    offered = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_repair_status",
                {"misconceptionId": first_id, "sessionId": None},
            ),
        ]
    )[1]["result"]["repairStatus"]
    assert offered["status"] == "needs_disambiguation"
    assert offered["probeOffered"] is True
    assert [action["id"] for action in offered["actions"]] == [
        "take_quick_check",
        "teach_me_now",
        "not_now",
    ]
    assert offered["actions"][0]["label"] == "Take the quick check"
    assert "two explanations would need different help" in offered["message"]

    responses = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_probe_defer",
                {
                    "factorId": factor_id,
                    "misconceptionId": first_id,
                    "sessionId": None,
                },
            ),
            _call(
                3,
                "causal_repair_status",
                {"misconceptionId": first_id, "sessionId": None},
            ),
        ]
    )
    assert responses[1]["result"]["preference"]["preference"] == "decline"

    again = responses[2]["result"]["repairStatus"]
    assert again["status"] == "needs_disambiguation"
    assert again["probeOffered"] is False
    assert [action["id"] for action in again["actions"]] == ["teach_me_now"]


def test_teach_me_now_over_rpc_lifts_the_hold_and_returns_the_episode(tmp_path):
    """The learner's explicit authorisation to be taught under ambiguity."""

    _vault_obj, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    status = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_teach_me_now",
                {
                    "factorId": factor_id,
                    "misconceptionId": first_id,
                    "sessionId": None,
                },
            ),
        ]
    )[1]["result"]["repairStatus"]
    assert status["status"] == "started"
    assert status["learnerPreference"] == "teach_now"
    # The episode comes back on the same call, so the surface never has to ask
    # again — re-asking would mint a second remediation episode.
    assert status["episode"] is not None
    assert status["episode"]["id"]


def test_the_feedback_to_repair_handoff_mints_exactly_one_episode(tmp_path):
    """One repair, one episode — the handoff calls the orchestrator twice.

    `applyRepairStatus` in FeedbackScreen.tsx opens the repair surface as soon
    as "Teach me now" returns a started episode, and RepairScreen then calls
    `start_remediation` on mount. Both run `causal_repair_status` with
    `start_repair`, and `create_remediation_episode` always INSERTs, so that one
    learner action produced two episodes: the second orphaned the first, and
    prescription/treatment/cold-retry records hung off whichever id the surface
    happened to keep.
    """

    _vault_obj, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    responses = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_teach_me_now",
                {
                    "factorId": factor_id,
                    "misconceptionId": first_id,
                    "sessionId": None,
                },
            ),
            _call(3, "start_remediation", {"misconceptionId": first_id}),
        ]
    )
    taught = responses[1]["result"]["repairStatus"]
    assert taught["status"] == "started"
    started = responses[2]["result"]
    assert started["episode"]["id"] == taught["episode"]["id"]
    # A provisional belief has no `misconceptions` row; the hold and the repair
    # must still name the case they are about.
    assert started["case"]["id"] == first_id
    assert started["case"]["status"] == "candidate"

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id FROM remediation_episodes WHERE case_ref = ?", (first_id,)
        ).fetchall()
    assert len(rows) == 1


def test_get_remediation_loads_a_diagnosis_kind_episode(tmp_path):
    """`case_ref` is a causal hypothesis id, not a `misconceptions` row.

    Reading it as a durable misconception raised `not_found`, so every causal
    repair episode 404'd the moment the surface tried to read it back.
    """

    _vault_obj, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    responses = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_teach_me_now",
                {
                    "factorId": factor_id,
                    "misconceptionId": first_id,
                    "sessionId": None,
                },
            ),
        ]
    )
    episode_id = responses[1]["result"]["repairStatus"]["episode"]["id"]

    read = _rpc(
        [
            _initialize(root),
            _call(2, "prescribe_remediation", {"episodeId": episode_id}),
            _call(3, "get_remediation", {"episodeId": episode_id}),
        ]
    )
    assert "error" not in read[1], read[1]
    assert "error" not in read[2], read[2]
    case = read[2]["result"]["case"]
    assert case["id"] == first_id
    assert case["statement"]
    # Every key `RemediationCaseDto` declares survives for this kind too.
    assert set(case) == {
        "id",
        "statement",
        "correctionStatement",
        "mechanism",
        "targetFacet",
        "confusedWithFacet",
        "status",
        "history",
    }
    assert case["history"] == []


def _offer_over_rpc(root, factor_id: str, first_id: str) -> dict:
    receipt_id = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_repair_status",
                {"misconceptionId": first_id, "sessionId": None},
            ),
        ]
    )[1]["result"]["repairStatus"]["decisionReceiptId"]
    return _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_probe_offer_action",
                {
                    "factorId": factor_id,
                    "misconceptionId": first_id,
                    "sessionId": None,
                    "decisionReceiptId": receipt_id,
                },
            ),
        ]
    )[1]["result"]["offer"]


def test_take_the_quick_check_over_rpc_pins_the_probe(tmp_path):
    """"Take the quick check" serves a factor-aware episode with pinned bundles.

    Run against the app's real starting state: `initialize` cold-starts a plain
    `initial` diagnostic episode for this learning object, and at most one
    episode may be open per LO. That placement episode has measured nothing, so
    it is relocked onto the cause set rather than refusing the offer — before
    that, this journey was unreachable in the running app.
    """

    _vault_obj, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)
    _rpc([_initialize(root)])
    cold_started = repository.open_probe_episode(LO_ID)
    assert cold_started is not None and cold_started.origin is None

    offer = _offer_over_rpc(root, factor_id, first_id)
    assert offer["accepted"] is True, offer["reason"]
    # The Tauri panel hands this item to the practice loop; without it the
    # accepted offer would have nowhere to go.
    assert offer["practiceItemId"] == PROBE_ITEM
    assert offer["presentationId"]
    assert offer["blindBundleIds"]

    # The SAME episode, now locked onto the causal hypothesis set.
    assert offer["episodeId"] == cold_started.id
    relocked = repository.probe_episode(cold_started.id)
    assert relocked.origin == f"causal_factor:{factor_id}"
    assert relocked.hypothesis_set_id != cold_started.hypothesis_set_id
    labels = {
        value["label"]
        for value in repository.fetch_hypothesis_set(relocked.hypothesis_set_id)[
            "hypotheses"
        ]
    }
    assert labels == {first_id, second_id, "other_or_unknown"}


def test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason(
    tmp_path,
):
    """A refusal the learner surface must be able to explain, not swallow.

    A diagnostic episode that has already recorded observations under its own
    locked set cannot host a second, causal hypothesis set: relocking it would
    reinterpret those observations under a set that did not exist when they were
    made. The Tauri panel maps this exact reason to "Another diagnostic is
    already open for this topic — finish that one first." (`PROBE_OFFER_COPY` in
    components/CausalAttribution.tsx); an unmapped reason would degrade to
    generic copy, so the id is part of the contract.
    """

    vault, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)
    _rpc([_initialize(root)])

    # Spend one real observation on the plain episode, through the serving path.
    episode = repository.open_probe_episode(LO_ID)
    assert episode.status == "in_progress"
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = next(
        entry
        for entry in eligible_instruments(
            vault, repository, episode, hypothesis_set=hypothesis_set
        )
        if entry.item.id == PROBE_ITEM
    )
    presentation = commit_presentation(vault, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    # §5.8: only an approved diagnostic grading source yields a qualifying
    # observation, so this goes through `apply_attempt` rather than a self-grade.
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=PROBE_ITEM,
                learner_answer_md="U Sigma V^T",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation.id,
            ),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=4,
                manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
    assert repository.probe_observations_for_episode(episode.id)

    # The status read must WITHDRAW the offer rather than show an action that
    # answers with a refusal.
    status = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "causal_repair_status",
                {"misconceptionId": first_id, "sessionId": None},
            ),
        ]
    )[1]["result"]["repairStatus"]
    assert status["status"] == "blocked_pending_review"
    assert status["reason"] == "another_probe_episode_is_open"
    assert status["probeOffered"] is False
    assert [action["id"] for action in status["actions"]] == ["teach_me_now"]

    # And a stale offer still cannot force the relock.
    offer = _offer_over_rpc(root, factor_id, first_id)
    assert offer["accepted"] is False
    assert offer["reason"] == "another_probe_episode_is_open"


def test_serving_the_pinned_probe_reuses_its_presentation(tmp_path, monkeypatch):
    """The pin must survive being SERVED (§3.4).

    `get_probe_contract` looks a session's assignment up by joining
    `scheduler_slate_candidates`. A causal probe has no scheduler candidate — it
    is minted by a learner action, not the planner — so the join missed it and a
    SECOND presentation was committed for the same item. That silently dropped
    the `causal_probe` selection component, and classification fell back to
    whatever bundles existed at answer time instead of the ones pinned when the
    probe was minted. `blind_bundle_ids` is a required parameter precisely so a
    newer bundle cannot change a replay; a re-committed presentation defeats it
    one layer up.
    """

    vault, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    minted = _activate_probe_candidate(repository, factor_id, first_id, second_id)
    _rpc([_initialize(root)])

    offer = _offer_over_rpc(root, factor_id, first_id)
    assert offer["accepted"] is True, offer["reason"]
    pinned_bundles = set(offer["blindBundleIds"])
    assert pinned_bundles == set(minted["candidate"]["blind_bundle_ids"])

    # §5.8 gates serving on an approved diagnostic grading provider; stub the
    # transport only — every decision below it is the real one.
    monkeypatch.setattr(
        practice_handlers,
        "ready_grading_provider",
        lambda _vault, override=None: (
            "test",
            SimpleNamespace(ready=True),
            object(),
        ),
    )

    served = _rpc(
        [
            _initialize(root),
            _call(
                2,
                "get_probe_contract",
                {"practiceItemId": PROBE_ITEM, "sessionId": "sess_probe"},
            ),
        ]
    )[1]["result"]
    assert served["active"] is True, served.get("reason")
    # THE invariant: serving reuses the pinned presentation, never a fresh one.
    assert served["presentationId"] == offer["presentationId"]
    assert (
        len(repository.probe_presentations_for_episode(offer["episodeId"])) == 1
    )

    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=PROBE_ITEM,
            learner_answer_md="U Sigma Q",
            attempt_type="diagnostic_probe",
            probe_presentation_id=served["presentationId"],
        ),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=CLOCK,
    )

    # A newer bundle for the same hypothesis exists by the time we classify.
    newer = generate_blind_prediction_bundle(
        repository,
        hypothesis_id=first_id,
        item={"id": PROBE_ITEM, "prompt": "Choose the valid final factor."},
        rubric={"criteria": [{"id": "correctness"}]},
        trace_contract=None,
        generator=lambda _safe: {"predicted_features": {"uses_transpose": True}},
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=FrozenClock(NOW + timedelta(days=1)),
    )
    assert newer["id"] not in pinned_bundles

    pinned = pinned_causal_probe(repository, served["presentationId"])
    assert set(pinned["blind_bundle_ids"]) == pinned_bundles
    classified = classify_probe_response(
        repository,
        presentation_id=served["presentationId"],
        observed_features={"uses_transpose": False},
    )
    assert set(classified["blind_bundle_ids"]) == pinned_bundles
    assert classified["outcome"] == "matched_single"
    assert classified["classified_as"] == [first_id]
