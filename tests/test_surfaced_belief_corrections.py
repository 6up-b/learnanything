"""A6: the system must be able to say it was wrong.

``spec_diagnostic_augmentation_v1.md`` §2 A6 / ``implementation_plan_v1.md`` 1.4.
A belief that was SURFACED to the learner and is later demoted/retired/
contradicted/superseded owes the learner an explicit retraction, named in the
words they were shown. A belief nobody saw owes them nothing.

Covers:
  - surfaced → retired yields EXACTLY ONE feed entry, carrying the as-shown
    wording and the typed reason;
  - never-surfaced → retired yields none (the scope guard), including the case
    where the attention budget suppressed the card;
  - re-reading the feed, and re-presenting the claim, never duplicate the entry;
  - each of A6's four reasons maps to its own stated wording;
  - a supersession that hands over a REPLACEMENT belief still narrates the
    withdrawal explicitly, and never restates it as the weaker successor;
  - both production `claim_ref` shapes (bare id from Review, structured dict from
    Feedback) join to the disposition stream.

All deterministic under FrozenClock.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.hypothesis_claims import present_claims
from learnloop.learner.learner_review_feed import build_learner_review_feed
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.learner.surfaced_beliefs import (
    WITHDRAWAL_REASONS,
    BeliefReference,
    SurfacedBeliefError,
    mark_belief_surfaced,
    record_belief_withdrawal,
    resolve_belief_reference,
    surfaced_belief_corrections,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


SHOWN = "You are treating the singular values as eigenvalues of A itself."
LATER = NOW + timedelta(hours=3)


def _seeded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _belief(repository, *, statement: str = SHOWN) -> str:
    return repository.insert_misconception(
        learning_object_id="lo_svd_definition",
        statement=statement,
        facet_ids=["recall"],
        severity=0.7,
        correction_statement="Singular values are eigenvalues of A^T A, square-rooted.",
        clock=FrozenClock(NOW),
    )


def _present(
    repository,
    belief_id,
    *,
    claim_text: str = SHOWN,
    surface: str = "feedback",
    temperature: str = "hot",
    visible: bool = True,
    ref=None,
    at=NOW,
):
    """Present a diagnosis claim exactly as the Tauri ClaimSurface does."""

    return present_claims(
        repository,
        [
            {
                "claim_class": "diagnosis",
                "claim_type": "misconception",
                "claim_ref": ref if ref is not None else belief_id,
                "claim_version": "misconception:active",
                "producer_version": "feedback-f3",
                "surface": surface,
                "temperature": temperature,
                "claim_text": claim_text,
                **({"visible_at": at.isoformat().replace("+00:00", "Z")} if visible else {}),
            }
        ],
        visit_id="visit-1",
        clock=FrozenClock(at),
    )


def _withdrawals(vault, repository) -> list[dict]:
    changelog = build_learner_review_feed(vault, repository)["changelog"]
    return [entry for entry in changelog if entry["kind"] == "belief_withdrawn"]


# ── The core A6 obligation ─────────────────────────────────────────────────


def test_surfaced_then_retired_yields_one_correction_in_the_shown_words(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)

    # The belief's own statement is REWRITTEN before the withdrawal fires — this
    # is the case that makes storing the as-shown wording load-bearing rather
    # than decorative. Quoting the live statement here would put words in the
    # learner's memory that were never on their screen.
    with repository.connection() as connection:
        connection.execute(
            "UPDATE misconceptions SET statement = ? WHERE id = ?",
            ("Re-authored by a later synthesis pass.", belief_id),
        )
        connection.commit()

    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(LATER),
    )

    entries = _withdrawals(vault, repository)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["belief_id"] == belief_id
    assert entry["belief_kind"] == "misconception"
    assert entry["withdrawn_claim_text"] == SHOWN
    assert entry["claim_text_source"] == "as_shown"
    assert entry["withdrawal_reason"] == "retired_misdiagnosed"
    assert entry["disposition"] == "demoted"
    assert entry["at"] == LATER.isoformat().replace("+00:00", "Z")
    assert entry["surfaced_on"] == "feedback"
    assert entry["surfaced_at"] == NOW.isoformat().replace("+00:00", "Z")
    # A6: name the claim, then say it is withdrawn and why.
    assert SHOWN in entry["statement"]
    assert "withdrawn" in entry["statement"]
    assert "misdiagnosis" in entry["statement"]
    assert "Re-authored" not in entry["statement"]
    # System-authored entries carry no per-session belief movement.
    assert entry["attempts_recorded"] == 0
    assert entry["predictions_moved"] == {"up": 0, "down": 0}
    assert entry["facet_ids"] == ["recall"]


def test_withdrawal_drops_the_belief_from_working_hypotheses(tmp_path):
    """The retraction replaces the standing claim; it does not sit beside it."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    assert belief_id in {
        row["id"] for row in build_learner_review_feed(vault, repository)["working_hypotheses"]
    }

    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="contradicted_by_trace",
        clock=FrozenClock(LATER),
    )

    feed = build_learner_review_feed(vault, repository)
    assert belief_id not in {row["id"] for row in feed["working_hypotheses"]}
    assert [entry["belief_id"] for entry in feed["changelog"] if entry["kind"] == "belief_withdrawn"] == [
        belief_id
    ]


# ── The scope guard: only beliefs the learner actually saw ─────────────────


def test_never_surfaced_belief_yields_no_correction(tmp_path):
    """Retiring an internal provisional hypothesis is housekeeping, not an apology."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(LATER),
    )
    assert _withdrawals(vault, repository) == []
    assert surfaced_belief_corrections(repository) == []


def test_suppressed_card_was_authored_not_shown(tmp_path):
    """A claim the attention budget swallowed never reached the learner."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    # Fill the visit's cold budget so the diagnosis card is suppressed.
    present_claims(
        repository,
        [
            {
                "claim_class": "estimate",
                "claim_type": "ready_estimate",
                "claim_ref": "facet:recall",
                "claim_version": "v1",
                "producer_version": "mvp-0.7",
                "surface": "today",
                "temperature": "cold",
                "visible_at": NOW.isoformat().replace("+00:00", "Z"),
            }
        ],
        visit_id="visit-1",
        clock=FrozenClock(NOW),
    )
    results = _present(repository, belief_id, temperature="cold", surface="today")
    assert results[0]["suppression_reason"] is not None

    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="adjudicated",
        clock=FrozenClock(LATER),
    )
    assert _withdrawals(vault, repository) == []


def test_presented_but_never_visible_is_not_surfaced(tmp_path):
    """`visible_at` is the viewport signal; without it nothing was on screen."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id, visible=False)
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(LATER),
    )
    assert _withdrawals(vault, repository) == []


def test_surfacing_after_the_withdrawal_does_not_retroactively_owe_an_apology(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(NOW),
    )
    _present(repository, belief_id, at=LATER)
    assert _withdrawals(vault, repository) == []


# ── Idempotency ────────────────────────────────────────────────────────────


def test_rereading_the_feed_never_duplicates_the_correction(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    # Present the SAME claim repeatedly (the UI re-presents on every mount and
    # every scroll-in) and from a second surface, so the belief has several
    # surfaced presentations.
    for offset in range(3):
        _present(repository, belief_id, at=NOW + timedelta(minutes=offset))
    _present(repository, belief_id, surface="review_working_hypotheses", temperature="cold")
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(LATER),
    )

    first = _withdrawals(vault, repository)
    second = _withdrawals(vault, repository)
    assert len(first) == 1
    assert [entry["id"] for entry in first] == [entry["id"] for entry in second]
    # One entry per disposition EVENT, keyed on it.
    events = repository.misconception_dispositions(belief_id)
    assert len(events) == 1
    assert first[0]["id"] == f"belief_withdrawn:{events[0]['id']}"


def test_repeated_presentation_keeps_the_first_wording_and_exposure(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    # A later mount with re-worded copy must not rewrite history: A6 quotes what
    # the learner read, and they read the first version.
    _present(repository, belief_id, claim_text="Reworded copy.", at=NOW + timedelta(minutes=5))
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(LATER),
    )
    entry = _withdrawals(vault, repository)[0]
    assert entry["withdrawn_claim_text"] == SHOWN
    assert entry["surfaced_at"] == NOW.isoformat().replace("+00:00", "Z")


def test_mark_belief_surfaced_is_idempotent_on_a_read_path(tmp_path):
    """The Repair surface prints the statement directly and is polled."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    for _ in range(4):
        mark_belief_surfaced(
            repository,
            belief_id=belief_id,
            claim_text=SHOWN,
            surface="repair_case",
            clock=FrozenClock(NOW),
        )
    surfaced = [
        event
        for event in repository.list_hypothesis_events()
        if event["belief_id"] == belief_id and event["surfaced_to_learner"] == 1
    ]
    assert len(surfaced) == 1
    assert surfaced[0]["surface"] == "repair_case"

    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="retired_misdiagnosed",
        clock=FrozenClock(LATER),
    )
    entries = _withdrawals(vault, repository)
    assert len(entries) == 1
    assert entries[0]["surfaced_on"] == "repair_case"


def test_mark_belief_surfaced_declines_to_flag_an_unquotable_claim(tmp_path):
    _vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    assert mark_belief_surfaced(
        repository, belief_id=belief_id, claim_text=None, surface="repair_case"
    ) is None
    assert mark_belief_surfaced(
        repository, belief_id=belief_id, claim_text="   ", surface="repair_case"
    ) is None
    assert repository.list_hypothesis_events() == []


# ── The typed reason vocabulary ────────────────────────────────────────────


@pytest.mark.parametrize(
    ("reason", "disposition", "phrase"),
    [
        ("contradicted_by_trace", "demoted", "your own work contradicted it"),
        ("superseded", "superseded", "a better-supported diagnosis replaced it"),
        ("adjudicated", "demoted", "a review of the diagnosis found it wrong"),
        ("retired_misdiagnosed", "demoted", "it was a misdiagnosis"),
    ],
)
def test_each_reason_maps_to_its_own_stated_wording(tmp_path, reason, disposition, phrase):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    record_belief_withdrawal(
        repository, belief_id=belief_id, reason=reason, clock=FrozenClock(LATER)
    )

    entry = _withdrawals(vault, repository)[0]
    assert entry["withdrawal_reason"] == reason
    assert entry["disposition"] == disposition
    assert phrase in entry["statement"]
    # Every wording says the claim is withdrawn — none of the four softens it.
    assert "withdrawn" in entry["statement"]
    assert SHOWN in entry["statement"]


def test_the_four_reasons_are_exactly_a6s_vocabulary():
    assert set(WITHDRAWAL_REASONS) == {
        "contradicted_by_trace",
        "superseded",
        "adjudicated",
        "retired_misdiagnosed",
    }


def test_an_untyped_reason_is_refused(tmp_path):
    _vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    with pytest.raises(SurfacedBeliefError):
        record_belief_withdrawal(repository, belief_id=belief_id, reason="because")


def test_a_belief_cannot_supersede_itself(tmp_path):
    """In-place replacement is the rewrite A6 forbids: nothing left to withdraw."""

    _vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    with pytest.raises(SurfacedBeliefError):
        record_belief_withdrawal(
            repository,
            belief_id=belief_id,
            reason="superseded",
            replacement_belief_id=belief_id,
        )


def test_legacy_free_text_reason_is_not_read_as_a_trace_contradiction(tmp_path):
    """Migration 116's backfilled reason contains the word "trace" and means the
    opposite: the first-error promotion had no authority, i.e. a misdiagnosis.
    A substring heuristic would tell the learner their own work refuted a claim
    it never touched."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    repository.insert_misconception_disposition(
        misconception_id=belief_id,
        disposition="demoted",
        reason="first_error_trace_had_no_durable_promotion_authority",
        clock=FrozenClock(LATER),
    )
    entry = _withdrawals(vault, repository)[0]
    assert entry["withdrawal_reason"] == "retired_misdiagnosed"
    assert "your own work contradicted it" not in entry["statement"]


# ── Never quietly re-state it as a weaker belief ───────────────────────────


def test_supersession_with_a_replacement_still_narrates_the_withdrawal(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    weaker = "Sometimes you skip the square root when reading singular values."
    replacement_id = _belief(repository, statement=weaker)

    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="superseded",
        replacement_belief_id=replacement_id,
        clock=FrozenClock(LATER),
    )

    entries = _withdrawals(vault, repository)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["replacement_belief_id"] == replacement_id
    assert entry["replacement_statement"] == weaker
    # The withdrawal is stated explicitly and FIRST; the successor is additional
    # information, never a substitute for the retraction.
    assert entry["withdrawn_claim_text"] == SHOWN
    assert "That is withdrawn" in entry["statement"]
    assert entry["statement"].index(SHOWN) < entry["statement"].index("That is withdrawn")
    assert entry["statement"].index("That is withdrawn") < entry["statement"].index(weaker)
    assert "withdrawn regardless" in entry["statement"]


def test_replacement_belief_is_not_itself_withdrawn(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    replacement_id = _belief(repository, statement="A weaker successor claim.")
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="superseded",
        replacement_belief_id=replacement_id,
        clock=FrozenClock(LATER),
    )
    assert [entry["belief_id"] for entry in _withdrawals(vault, repository)] == [belief_id]


# ── The join: both production claim_ref shapes ────────────────────────────


def test_structured_claim_ref_from_the_feedback_surface_still_joins(tmp_path):
    """FeedbackScreen sends {"misconceptionId", "attemptId"}; `canonical_claim_ref`
    json-encodes it, so an equality join on `claim_ref` would silently miss every
    Feedback presentation. The normalized `belief_id` is what makes it joinable."""

    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(
        repository,
        belief_id,
        ref={"misconceptionId": belief_id, "attemptId": "at_123"},
    )
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="contradicted_by_trace",
        clock=FrozenClock(LATER),
    )
    entries = _withdrawals(vault, repository)
    assert len(entries) == 1
    assert entries[0]["withdrawn_claim_text"] == SHOWN


def test_belief_reference_resolution_covers_the_shapes_in_production():
    expected = BeliefReference(kind="misconception", id="mc_1")
    # Review: a bare misconception id.
    assert resolve_belief_reference("misconception", "mc_1") == expected
    # Feedback: a structured ref, raw or already canonicalized to JSON.
    assert (
        resolve_belief_reference(
            "misconception", {"misconceptionId": "mc_1", "attemptId": "at_1"}
        )
        == expected
    )
    assert (
        resolve_belief_reference(
            "misconception", '{"attemptId":"at_1","misconceptionId":"mc_1"}'
        )
        == expected
    )
    # Non-belief claims resolve to nothing, and that is not an error: A6
    # apologises for diagnoses, not for estimates, policies, or ledger facts.
    assert resolve_belief_reference("ready_estimate", "facet:recall") is None
    assert resolve_belief_reference("schedule_choice", {"itemId": "pi_1"}) is None
    assert resolve_belief_reference("regrade", "at_1") is None
    assert resolve_belief_reference("misconception", "") is None


def test_non_belief_claims_never_record_a_belief_reference(tmp_path):
    _vault, repository = _seeded(tmp_path)
    present_claims(
        repository,
        [
            {
                "claim_class": "policy",
                "claim_type": "schedule_choice",
                "claim_ref": {"itemId": "pi_svd_define_001"},
                "claim_version": "v1",
                "producer_version": "mvp-0.7",
                "surface": "today",
                "temperature": "cold",
                "claim_text": "Chosen next because it is due.",
                "visible_at": NOW.isoformat().replace("+00:00", "Z"),
            }
        ],
        visit_id="visit-1",
        clock=FrozenClock(NOW),
    )
    event = repository.list_hypothesis_events()[0]
    assert event["belief_kind"] is None
    assert event["belief_id"] is None
    # The wording is still captured — it costs nothing and the claim was shown.
    assert event["claim_text_as_shown"] == "Chosen next because it is due."
    assert event["surfaced_to_learner"] == 1


# ── Multiple dispositions ──────────────────────────────────────────────────


def test_a_second_disposition_is_a_second_fact_not_a_re_narration(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    record_belief_withdrawal(
        repository, belief_id=belief_id, reason="contradicted_by_trace", clock=FrozenClock(LATER)
    )
    entries = _withdrawals(vault, repository)
    assert len(entries) == 1

    # A later adjudication of the same belief is new information, recorded once.
    record_belief_withdrawal(
        repository,
        belief_id=belief_id,
        reason="adjudicated",
        clock=FrozenClock(LATER + timedelta(days=1)),
    )
    entries = _withdrawals(vault, repository)
    assert len(entries) == 2
    assert len({entry["id"] for entry in entries}) == 2
    assert {entry["withdrawal_reason"] for entry in entries} == {
        "contradicted_by_trace",
        "adjudicated",
    }
    # ...and still stable across reads.
    assert [entry["id"] for entry in _withdrawals(vault, repository)] == [
        entry["id"] for entry in entries
    ]


def test_withdrawals_interleave_reverse_chronologically(tmp_path):
    vault, repository = _seeded(tmp_path)
    belief_id = _belief(repository)
    _present(repository, belief_id)
    record_belief_withdrawal(
        repository, belief_id=belief_id, reason="retired_misdiagnosed", clock=FrozenClock(LATER)
    )
    repository.record_derived_state_rebuild(
        scope="full",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version="mvp-0.6",
        rebuilt_learning_objects=1,
        replayed_attempts=1,
        clock=FrozenClock(NOW - timedelta(hours=1)),
    )
    repository.record_derived_state_rebuild(
        scope="full",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version="mvp-0.7",
        rebuilt_learning_objects=1,
        replayed_attempts=1,
        clock=FrozenClock(LATER + timedelta(hours=1)),
    )

    changelog = build_learner_review_feed(vault, repository)["changelog"]
    ats = [entry["at"] for entry in changelog]
    assert ats == sorted(ats, reverse=True)
    kinds = [entry["kind"] for entry in changelog]
    assert kinds[0] == "recalibration"
    assert "belief_withdrawn" in kinds
