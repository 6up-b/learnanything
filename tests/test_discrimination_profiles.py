"""Meas §3.A5 discrimination profiles (implementation plan item 6.4).

The two §10 lines these tests exist for:

    An item whose facet-holder and misconception-holder personas produce the same
    outcome is rejected by the §3.0 gate and never reaches a learner.

    ``no_profile_applies`` is representable, recordable, and appears in the
    two-tailed fill-rate telemetry.

The second is the one worth stating carefully. §3.A5's revert criterion is that
the rejection rate *collapsing toward zero* is the original disease with better
tooling — so the rejection arm has to be a first-class outcome all the way down:
a value in the wire schema, a row in the store, a count in the audit report, and
a denominator in the metric. A design where "none applied" were silence would
leave the watched tail uncomputable, so several of these tests assert on the
absence of silence rather than on a number.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.attempts.ai_contracts import (
    CriterionEvidence,
    DiscriminationProfileMatch,
    GradingProposal,
)
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, complete_codex_graded_attempt
from learnloop.diagnosis.discrimination_profiles import (
    NO_PROFILE_APPLIES_FLOOR,
    PROFILE_REJECTION_METRIC,
    PROFILE_SATURATION_CEILING,
    ProfileMatchOutcome,
    ProfileTailVerdict,
    item_profiles,
    payload_profiles,
    profile_coverage,
    profile_match_fill_rate,
    profile_prior_payload,
    profiles_by_facet,
    validate_profile_match,
)
from learnloop.attempts.grading import build_grading_context, causal_attribution_audit_report
from learnloop.content.authoring.persona_gate import (
    GateDecision,
    GateTier,
    InstrumentClass,
    PersonaGate,
    PersonaGateReason,
    classify_instrument,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets

CLOCK = FrozenClock(NOW)
ITEM = "pi_profile_001"
FACET = "f_coordinate_vector"

FACETS = [
    {
        "id": FACET,
        "kind": "definition",
        "claim": "Qx is the coordinate vector of x in the Q basis.",
    }
]

EXPECTED = "Qx is the coordinate vector"
BELIEF_ANSWER = "Q^T x is the coordinate vector"


def _profile(**overrides) -> dict:
    payload = {
        "id": "dp_reverse_q",
        "hypothesis": "believes Q^T maps standard vectors to basis coordinates",
        "observable_signature": BELIEF_ANSWER,
        "misconception_id": "mc_reverse_q",
        "facet_id": FACET,
        "fails_criteria": ["c1"],
        "distinguishing_features": ["writes Q^T where the answer key writes Q"],
        "source": "misconception_registry",
    }
    payload.update(overrides)
    return payload


def _item_payload(**overrides) -> dict:
    payload = {
        "id": ITEM,
        "learning_object_id": "lo_svd_definition",
        "practice_mode": "constructed_response",
        "prompt": "Which of Qx / Q^T x is the coordinate vector?",
        "expected_answer": EXPECTED,
        "surface_family": "concept_explain",
        "evidence_facets": [FACET],
        "evidence_weights": {FACET: 1.0},
        "discrimination_profiles": [_profile()],
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [],
        },
    }
    payload.update(overrides)
    return payload


def _row(payload, client_item_id="c_0") -> dict:
    return {
        "client_item_id": client_item_id,
        "item_type": "practice_item",
        "operation": "create",
        "payload": payload,
        "audit": None,
        "validation_status": "valid",
        "validation_errors": [],
        "_auto_apply": True,
    }


def _vault(tmp_path, *, profiles=None):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, FACETS)
    write_yaml(
        paths.practice_item_path("linear-algebra", ITEM),
        {
            "schema_version": 1,
            **_item_payload(
                discrimination_profiles=[_profile()] if profiles is None else profiles
            ),
            "attempt_types_allowed": ["independent_attempt"],
            "capability": "retrieval",
            "difficulty": 0.5,
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


# ---------------------------------------------------------------------------
# Authoring: the profile IS the gate's oracle
# ---------------------------------------------------------------------------


def test_authoring_a_profile_promotes_the_item_to_the_hard_tier_structurally():
    """No tag and no mode: carrying profiles is what makes it a profile item.

    The plan requires the tier to be read off the payload rather than passed in
    by whichever route is running, and a tag is closer to a caller flag than to a
    property.
    """

    assert classify_instrument(_item_payload()) is InstrumentClass.DISCRIMINATION_PROFILE
    plain = _item_payload(discrimination_profiles=[])
    assert classify_instrument(plain) is InstrumentClass.PLAIN_PRACTICE


def test_profile_whose_signature_equals_the_answer_key_is_blocked(tmp_path):
    """§10: personas producing the same outcome are rejected by the §3.0 gate.

    The A5 form of ``diagnostic_gate``'s motivating regression: the item claims
    to profile a belief whose holder writes the answer key, so the facet-holder
    and the belief-holder are indistinguishable and the item measures nothing
    about the belief.
    """

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    gate = PersonaGate(vault, repository)
    rows = [_row(_item_payload(discrimination_profiles=[_profile(observable_signature=EXPECTED)]))]

    gate(rows)

    outcome = gate.outcomes[0]
    assert outcome.instrument_class is InstrumentClass.DISCRIMINATION_PROFILE
    assert outcome.tier is GateTier.HARD
    assert outcome.decision is GateDecision.BLOCK
    assert outcome.reason is PersonaGateReason.BELIEF_HOLDER_PASSES
    # Blocked = un-acceptable, not merely noted.
    assert rows[0]["validation_status"] == "invalid"


def test_a_discriminating_profile_passes_and_plants_every_profile(tmp_path):
    """The positive control, plus the multi-profile rule.

    §3.A5 admits several candidate hypotheses per item, so the gate plants ALL of
    them: an item blind to any one of its own declared candidates has not earned
    the claim it makes about that one.
    """

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    gate = PersonaGate(vault, repository)
    two = [
        _profile(),
        _profile(id="dp_blind", observable_signature=EXPECTED, misconception_id=None),
    ]

    gate([_row(_item_payload(discrimination_profiles=[_profile()]))])
    assert gate.outcomes[0].decision is GateDecision.PASS
    assert gate.outcomes[0].reason is PersonaGateReason.PERSONAS_SEPARATE

    gate = PersonaGate(vault, repository)
    gate([_row(_item_payload(discrimination_profiles=two))])
    assert gate.outcomes[0].decision is GateDecision.BLOCK


def test_incomplete_profiles_are_dropped_before_they_reach_the_gate():
    """A profile naming a belief but not what its holder writes is not an oracle.

    Dropped at the reader rather than downstream: letting it through would make
    the gate abstain ("nothing to plant") on an item that looks authored.
    """

    assert payload_profiles(_item_payload()) != ()
    assert payload_profiles(_item_payload(discrimination_profiles=[_profile(observable_signature="  ")])) == ()
    assert payload_profiles(_item_payload(discrimination_profiles=[_profile(hypothesis="")])) == ()


# ---------------------------------------------------------------------------
# The prior handed to the grader
# ---------------------------------------------------------------------------


def test_the_grading_prior_withholds_the_criteria_the_author_expects_to_fail(tmp_path):
    """A prior over causes, not a postdictive claim to confirm.

    ``fails_criteria`` is analysis input for A4's commissioning. Handing it to the
    grader would hand it a list of criteria the author expects a belief-holder to
    fail, which is how a prior becomes a constraint (causal §1 principle 4).
    """

    _paths, vault, _repo = _vault(tmp_path)
    item = vault.practice_items[ITEM]

    prior = profile_prior_payload(item_profiles(item))

    assert prior[0]["profile_id"] == "dp_reverse_q"
    assert prior[0]["observable_signature"] == BELIEF_ANSWER
    assert "fails_criteria" not in prior[0]
    context = build_grading_context(
        vault, item, attempt_id="att_x", learner_answer_md="Q^T x."
    )
    assert context.discrimination_profiles == prior


def test_an_item_with_no_profiles_offers_the_grader_nothing(tmp_path):
    """A grader is never shown a candidate set that does not exist."""

    _paths, vault, _repo = _vault(tmp_path, profiles=[])
    item = vault.practice_items[ITEM]

    context = build_grading_context(
        vault, item, attempt_id="att_x", learner_answer_md="Qx."
    )

    assert context.discrimination_profiles == []


# ---------------------------------------------------------------------------
# Validation: four arms, and rejection is not silence
# ---------------------------------------------------------------------------


def _proposal(match=None, **overrides) -> GradingProposal:
    payload = {
        "attempt_id": "att_1",
        "practice_item_id": ITEM,
        "rubric_score": 0,
        "criterion_evidence": [
            CriterionEvidence(criterion_id="c1", points_awarded=0, evidence="wrong")
        ],
        "grader_confidence": 0.9,
        "discrimination_profile_match": match,
    }
    payload.update(overrides)
    return GradingProposal(**payload)


def test_no_profile_applies_is_representable_in_the_wire_schema():
    """First-class means it is a value, not the absence of one."""

    match = DiscriminationProfileMatch(outcome="no_profile_applies")

    assert match.outcome == "no_profile_applies"
    assert match.profile_id is None
    # And a `matched` arm cannot be built without naming a profile.
    with pytest.raises(ValueError):
        DiscriminationProfileMatch(outcome="matched")


def test_the_four_outcome_arms_are_total_over_one_attempt(tmp_path):
    _paths, vault, _repo = _vault(tmp_path)
    item = vault.practice_items[ITEM]
    unprofiled = vault.practice_items["pi_svd_define_001"]

    matched = validate_profile_match(
        item,
        _proposal(
            DiscriminationProfileMatch(
                outcome="matched", profile_id="dp_reverse_q", evidence="wrote Q^T x"
            )
        ),
    )
    assert matched.outcome is ProfileMatchOutcome.MATCHED
    assert matched.misconception_id == "mc_reverse_q"

    rejected = validate_profile_match(
        item, _proposal(DiscriminationProfileMatch(outcome="no_profile_applies"))
    )
    assert rejected.outcome is ProfileMatchOutcome.NO_PROFILE_APPLIES

    silent = validate_profile_match(item, _proposal(None))
    assert silent.outcome is ProfileMatchOutcome.NOT_REPORTED

    unoffered = validate_profile_match(unprofiled, _proposal(None))
    assert unoffered.outcome is ProfileMatchOutcome.NO_PROFILES_OFFERED


def test_a_match_naming_an_unknown_profile_is_not_coerced_onto_the_nearest(tmp_path):
    """The one place the revert-criterion failure would be easiest to introduce."""

    _paths, vault, _repo = _vault(tmp_path)
    item = vault.practice_items[ITEM]

    resolved = validate_profile_match(
        item,
        _proposal(
            DiscriminationProfileMatch(
                outcome="matched", profile_id="dp_not_authored", evidence="x"
            )
        ),
    )

    assert resolved.outcome is ProfileMatchOutcome.NOT_REPORTED
    assert resolved.rejected_report_reason == "unknown_profile_id"


def test_a_match_without_a_trace_citation_is_refused(tmp_path):
    _paths, vault, _repo = _vault(tmp_path)
    item = vault.practice_items[ITEM]

    resolved = validate_profile_match(
        item,
        _proposal(
            DiscriminationProfileMatch(outcome="matched", profile_id="dp_reverse_q")
        ),
    )

    assert resolved.outcome is ProfileMatchOutcome.NOT_REPORTED
    assert resolved.rejected_report_reason == "match_without_evidence"


# ---------------------------------------------------------------------------
# §10: recordable, and in the two-tailed fill-rate telemetry
# ---------------------------------------------------------------------------


def _graded_attempt(vault, repository, attempt_id: str, *, match, correct: bool):
    return complete_codex_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="Q^T x is the coordinate vector.",
            attempt_type="independent_attempt",
        ),
        GradingProposal(
            attempt_id=attempt_id,
            practice_item_id=ITEM,
            rubric_score=4 if correct else 0,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="c1",
                    points_awarded=4 if correct else 0,
                    evidence="graded",
                )
            ],
            grader_confidence=0.9,
            discrimination_profile_match=match,
        ),
        agent_run_id=None,
        clock=CLOCK,
    )


def test_no_profile_applies_is_recorded_and_reaches_the_audit_report(tmp_path):
    """§10's line, end to end: representable, recordable, and in the telemetry."""

    _paths, vault, repository = _vault(tmp_path)

    _graded_attempt(
        vault,
        repository,
        "att_reject",
        match=DiscriminationProfileMatch(outcome="no_profile_applies"),
        correct=False,
    )

    row = repository.discrimination_profile_match(str("att_reject"))
    assert row is not None
    assert row["outcome"] == "no_profile_applies"
    assert row["profile_id"] is None
    assert row["attempt_failed"] == 1

    report = causal_attribution_audit_report(repository)
    counts = report["groups"][0]["discrimination_profile_counts"]
    assert counts["no_profile_applies"] == 1
    assert counts["matched"] == 0
    # Both tails present as keys even at zero: a tail that vanishes from the
    # report when it is empty cannot be watched.
    assert set(counts) == {str(arm) for arm in ProfileMatchOutcome}


def test_the_telemetry_survives_a_derived_state_rebuild(tmp_path):
    """The count is read from the durable store, not from the debug payload.

    `rebuild-derived-state` re-derives the payload from the persisted grade, and
    there is no provider on the replay path — so a payload-sourced count would
    zero itself on the next rebuild, silently, on exactly the tail §3.A5 asks
    readers to watch.
    """

    from learnloop.substrate.replay import rebuild_derived_state

    _paths, vault, repository = _vault(tmp_path)
    _graded_attempt(
        vault,
        repository,
        "att_rebuild",
        match=DiscriminationProfileMatch(outcome="no_profile_applies"),
        correct=False,
    )

    rebuild_derived_state(vault, repository)

    report = causal_attribution_audit_report(repository)
    counts = report["groups"][0]["discrimination_profile_counts"]
    assert counts["no_profile_applies"] == 1
    assert profile_match_fill_rate(repository).denominator == 1.0


def test_the_store_is_append_only_and_one_judgement_per_attempt(tmp_path):
    """A regrade re-reports; the first judgement is the one that happened."""

    _paths, vault, repository = _vault(tmp_path)

    _bare_attempt(repository, "att_manual")
    assert repository.insert_discrimination_profile_match(
        attempt_id="att_manual",
        practice_item_id=ITEM,
        outcome="matched",
        profile_id="dp_reverse_q",
        attempt_failed=True,
    )
    assert (
        repository.insert_discrimination_profile_match(
            attempt_id="att_manual",
            practice_item_id=ITEM,
            outcome="no_profile_applies",
            attempt_failed=True,
        )
        is None
    )
    assert repository.discrimination_profile_match("att_manual")["outcome"] == "matched"
    with pytest.raises(Exception):
        with repository.connection() as connection:
            connection.execute(
                "UPDATE discrimination_profile_matches SET outcome = 'matched'"
            )


# ---------------------------------------------------------------------------
# The revert criterion, both tails
# ---------------------------------------------------------------------------


def _bare_attempt(repository, attempt_id: str) -> str:
    """The minimum attempt row the match store's foreign key requires.

    Synthesized rather than graded because these tests are about the METRIC's
    arithmetic over a recorded population, and driving twenty full grading passes
    to produce twenty rows would make the arithmetic the least visible thing in
    the test.
    """

    repository.insert_practice_attempt(
        {
            "id": attempt_id,
            "practice_item_id": ITEM,
            "learning_object_id": "lo_svd_definition",
            "subject": "linear-algebra",
            "concept": "singular_value_decomposition",
            "practice_mode": "constructed_response",
            "attempt_type": "independent_attempt",
            "learner_answer_md": "x",
            "evidence_facets": [FACET],
            "evidence_weights": {FACET: 1.0},
            "rubric_score": 0,
            "correctness": 0.0,
            "confidence": None,
            "latency_seconds": None,
            "hints_used": 0,
            "error_type": None,
            "grader_confidence": 1.0,
            "manual_review": 0,
            "manual_review_reason": None,
            "created_at": NOW_ISO,
        }
    )
    return attempt_id


def _record(repository, index: int, outcome: str, *, profile_id=None, failed=True):
    repository.insert_discrimination_profile_match(
        attempt_id=_bare_attempt(repository, f"att_synth_{index}"),
        practice_item_id=ITEM,
        outcome=outcome,
        profile_id=profile_id,
        attempt_failed=failed,
    )


def test_rejection_rate_abstains_before_any_judged_failure(tmp_path):
    _paths, _loaded, repository = _vault(tmp_path)

    metric = profile_match_fill_rate(repository)

    assert metric.name == PROFILE_REJECTION_METRIC
    assert metric.availability == "no_data"
    assert metric.value is None
    assert metric.denominator == 0


def test_rejection_rate_collapsing_toward_zero_is_named_as_the_revert_tail(tmp_path):
    """§3.A5's stated revert direction, computed rather than judged."""

    _paths, _loaded, repository = _vault(tmp_path)
    for index in range(20):
        _record(repository, index, "matched", profile_id=f"dp_{index % 4}")

    metric = profile_match_fill_rate(repository)

    assert metric.availability == "available"
    assert metric.value == 0.0
    assert metric.value < NO_PROFILE_APPLIES_FLOOR
    assert metric.detail["verdict"] == str(ProfileTailVerdict.REJECTION_RATE_COLLAPSED)


def test_one_profile_taking_every_match_is_the_other_tail(tmp_path):
    """"A profile that matches ~100% of failures is as suspect as one that never
    matches" — standing constraint 2, both tails.

    The verdict reads the concentration WITHIN the matches, not the share of all
    judged failures: the latter reading is arithmetically the same event as the
    rejection rate collapsing, so an arm defined that way could never fire on its
    own. What this catches is the independent failure — the model rejects
    honestly a fifth of the time, and every time it does not, it names the same
    profile, so a set of three candidates is behaving as one.
    """

    _paths, _loaded, repository = _vault(tmp_path)
    for index in range(19):
        _record(repository, index, "matched", profile_id="dp_catch_all")
    for index in range(19, 25):
        _record(repository, index, "no_profile_applies")

    metric = profile_match_fill_rate(repository)

    assert metric.availability == "available"
    # Rejection is healthy — this is NOT the collapse arm.
    assert metric.value > NO_PROFILE_APPLIES_FLOOR
    assert metric.detail["profile_concentration"]["dp_catch_all"] == 1.0
    assert metric.detail["profile_shares"]["dp_catch_all"] < PROFILE_SATURATION_CEILING
    assert metric.detail["verdict"] == str(ProfileTailVerdict.PROFILE_SATURATED)


def test_a_spread_of_matches_across_profiles_is_within_band(tmp_path):
    """The control for the arm above: rejection healthy, no single catch-all."""

    _paths, _loaded, repository = _vault(tmp_path)
    for index in range(18):
        _record(repository, index, "matched", profile_id=f"dp_{index % 3}")
    for index in range(18, 24):
        _record(repository, index, "no_profile_applies")

    metric = profile_match_fill_rate(repository)

    assert metric.detail["verdict"] == str(ProfileTailVerdict.WITHIN_BAND)
    assert max(metric.detail["profile_concentration"].values()) < PROFILE_SATURATION_CEILING


def test_successes_and_unoffered_items_stay_out_of_the_denominator(tmp_path):
    """A profile describes a WRONG answer; a correct attempt is not a case it
    could have applied to. And an item nobody profiled never asked the question."""

    _paths, _loaded, repository = _vault(tmp_path)
    for index in range(6):
        _record(repository, index, "matched", profile_id="dp_a")
    for index in range(6, 12):
        _record(repository, index, "no_profile_applies")
    for index in range(12, 20):
        _record(repository, index, "matched", profile_id="dp_a", failed=False)
    for index in range(20, 30):
        _record(repository, index, "no_profiles_offered", failed=True)
    for index in range(30, 34):
        _record(repository, index, "not_reported", failed=True)

    metric = profile_match_fill_rate(repository)

    assert metric.denominator == 12.0
    assert metric.value == 0.5
    assert metric.detail["verdict"] == str(ProfileTailVerdict.WITHIN_BAND)
    assert metric.detail["outcome_counts"]["no_profiles_offered"] == 10
    assert metric.detail["failed_outcome_counts"]["not_reported"] == 4


# ---------------------------------------------------------------------------
# The companions a rate has to be read against
# ---------------------------------------------------------------------------


def test_coverage_reports_how_much_of_the_pool_is_profiled_at_all(tmp_path):
    _paths, vault, _repo = _vault(tmp_path)

    coverage = profile_coverage(vault)

    assert coverage["items_with_profiles"] == 1
    assert coverage["profiles"] == 1
    assert coverage["profiles_by_source"] == {"misconception_registry": 1}
    assert coverage["unlinked_authored_profiles"] == 0


def test_profiles_group_by_facet_for_a4_commissioning(tmp_path):
    """A4 separates two profiles; it needs them indexed by what they contest."""

    _paths, vault, _repo = _vault(tmp_path)

    grouped = profiles_by_facet(vault)

    assert grouped[FACET][0]["profile_id"] == "dp_reverse_q"
    assert grouped[FACET][0]["practice_item_id"] == ITEM
    assert grouped[FACET][0]["fails_criteria"] == ["c1"]


# ---------------------------------------------------------------------------
# The doctor: the blindness check, on what actually shipped
# ---------------------------------------------------------------------------


def test_the_doctor_catches_a_blind_profile_on_a_hand_authored_item(tmp_path):
    """The persona gate runs on proposals; a hand-edited YAML item skips it."""

    from learnloop.ops.doctor import _check_blueprints_and_criteria

    _paths, vault, _repo = _vault(
        tmp_path,
        profiles=[
            _profile(observable_signature=EXPECTED),
            _profile(id="dp_reverse_q", observable_signature="something else"),
        ],
    )

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)
    codes = {issue.code for issue in issues}

    assert "discrimination_profile:signature_is_the_answer_key" in codes
    # Two profiles sharing an id: a match record could not say which it meant.
    assert "discrimination_profile:duplicate_id" in codes


def test_the_doctor_is_silent_on_a_well_formed_profile(tmp_path):
    from learnloop.ops.doctor import _check_blueprints_and_criteria

    _paths, vault, _repo = _vault(tmp_path)

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)

    assert not any(issue.code.startswith("discrimination_profile:") for issue in issues)
