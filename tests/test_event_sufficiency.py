"""P1 step 10 -- U-015 event-sufficiency replay prototype + §9.7 deterministic replay
(spec_p1_shared_substrate §1, §9.7, §9.8).

The card-psychometrics projection (difficulty/discrimination/rubric calibration) is a
DEFERRED projection over administration/observation events. These tests prove event
sufficiency: per-card outcome counts stratified by administration context are
computable from ledger events ALONE (no live tables, zero schema changes), in the
U-014 hierarchical-likelihood resume shape.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import card_lineage as CL
from learnloop.services import substrate_cutover as SC
from learnloop.services.fsrs import Rating
from learnloop.services.card_outcome_replay import (
    REPLAY_MANIFEST,
    outcome_class_for_response_posterior,
    replay_card_outcome_counts,
    replay_event_stream,
    u014_resume_shape,
)

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _card(repo, *, tag):
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title=f"fam-{tag}", clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = {"target": "svd", "capability": "retrieval", "tag": tag}
    cv = repo.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash=A._canonical_hash(contract),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    return family_id, card_id, cv


def _surface(repo, cv, *, tag):
    sid = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{tag}", fingerprint=None, surface_json="{}", clock=CLOCK,
    )
    return repo.fetch_surface(sid)


def _raw_grade(repo, *, administration_id, observation_id, observed_class):
    return repo.insert_raw_grade_event(
        values={
            "administration_id": administration_id,
            "observation_id": observation_id,
            "role": "primary",
            "raw_output_json": "{}",
            "observed_class": observed_class,
            "confidence_bucket": "high",
            "response_classifier_version": "rc-v1",
            "context_features_json": "{}",
            "exact_word_count": 3,
            "declared_length_bucket": "1-50",
        },
        clock=CLOCK,
    )


def _submit(repo, *, surface, cv, family_id, lineage_id, tag, context, correct):
    receipt = SC.submit_administration_response(
        repo, surface=surface, card_version_id=cv, family_id=family_id, purpose="practice",
        card_lineage_id=lineage_id, algorithm_version=SC.P0_ALGORITHM_VERSION,
        review_event={"rating": Rating.GOOD if correct else Rating.AGAIN, "elapsed_days": 0.0},
        eligible=True, failed=not correct, attempt_id=f"att-{tag}", admin_context=context, clock=CLOCK,
    )
    obs = repo.observations_for_administration(receipt.administration_id)[0]
    _raw_grade(repo, administration_id=receipt.administration_id, observation_id=obs["id"],
               observed_class="correct" if correct else "incorrect")
    return receipt


# --- pure argmax helper -------------------------------------------------------

def test_outcome_class_argmax_is_deterministic():
    assert outcome_class_for_response_posterior({"correct": 0.7, "incorrect": 0.3}) == "correct"
    # Ties break on the lexicographically smallest class (determinism).
    assert outcome_class_for_response_posterior({"b": 0.5, "a": 0.5}) == "a"
    assert outcome_class_for_response_posterior(None) is None


# --- §9.8 (a): every admin/obs pair carries card version + outcome + context --

def test_every_admin_obs_pair_carries_card_version_outcome_and_context(repo):
    fam, _card_id, cv = _card(repo, tag="s1")
    lineage = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=fam, card_id=_card_id, clock=CLOCK)
    for i in range(4):
        cold = i % 2 == 0
        _submit(repo, surface=_surface(repo, cv, tag=f"s1-{i}"), cv=cv, family_id=fam, lineage_id=lineage,
                tag=f"s1-{i}", context={"cold": cold, "open_book": False}, correct=(i < 3))
    result = replay_card_outcome_counts(repo)
    # No admin/obs pair is missing a required field -- the sufficiency guarantee.
    assert result.administrations_missing_fields == []
    assert result.events_replayed == 4
    # Counts are per-card, stratified by administration context.
    assert cv in result.counts
    strata = result.counts[cv]
    assert len(strata) == 2  # two distinct cold/warm contexts
    total_correct = sum(classes.get("correct", 0) for classes in strata.values())
    total_incorrect = sum(classes.get("incorrect", 0) for classes in strata.values())
    assert total_correct == 3 and total_incorrect == 1


# --- §9.8: reads ledger events ONLY (no live tables) --------------------------

def test_replay_reads_ledger_events_only_no_live_tables(repo):
    fam, _card_id, cv = _card(repo, tag="s2")
    lineage = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=fam, card_id=_card_id, clock=CLOCK)
    _submit(repo, surface=_surface(repo, cv, tag="s2-0"), cv=cv, family_id=fam, lineage_id=lineage,
            tag="s2-0", context={"cold": True}, correct=True)
    # Delete the live scheduling projection entirely; the replay must be unaffected
    # because it reads administrations/observations/grade events, never activity_card_state.
    with repo.connection() as connection:
        connection.execute("DELETE FROM activity_card_state")
        connection.execute("DELETE FROM practice_item_state")
        connection.commit()
    result = replay_card_outcome_counts(repo)
    assert result.counts[cv]  # counts still computed from ledger events alone
    assert result.manifest["reads_live_tables"] is False


# --- §9.8: prefers the grade_interpretations head, falls back to raw ----------

def test_replay_prefers_active_interpretation_head(repo):
    from learnloop.services.outcome_schemas import ensure_builtin_schemas
    from learnloop.services.outcome_schemas import COARSE_RESPONSE_SLUG

    fam, _card_id, cv = _card(repo, tag="s3")
    lineage = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=fam, card_id=_card_id, clock=CLOCK)
    receipt = _submit(repo, surface=_surface(repo, cv, tag="s3-0"), cv=cv, family_id=fam, lineage_id=lineage,
                      tag="s3-0", context={"cold": True}, correct=False)  # raw says 'incorrect'
    obs = repo.observations_for_administration(receipt.administration_id)[0]
    raw_id = repo.raw_grade_events_for_observation(obs["id"])[0]["id"]
    # Attach an interpretation head whose posterior argmax disagrees with the raw class.
    ensure_builtin_schemas(repo, clock=CLOCK)
    version_row = repo.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    model_id = repo.insert_calibration_model(
        model={"semver": "0.1.0", "content_hash": "es-model-1", "scope_level": "global",
               "outcome_schema_id": version_row["schema_id"],
               "outcome_schema_version": int(version_row["version"]),
               "backoff_chain_json": "[]", "status": "heuristic"},
        alphas={"success": {"success|high": 2.0}, "other": {"other|high": 2.0}}, clock=CLOCK,
    )
    interp_id = repo.insert_grade_interpretation(
        values={
            "raw_grade_event_id": raw_id, "observation_id": obs["id"],
            "administration_id": receipt.administration_id, "calibration_model_id": model_id,
            "calibration_model_hash": "es-model-1", "projection_algorithm_version": "mvp-0.8",
            "response_posterior_json": json.dumps({"success": 0.95, "other": 0.05}),
            "certainty_discount": 1.0,
        }, clock=CLOCK,
    )
    repo.set_active_interpretation(observation_id=obs["id"], interpretation_id=interp_id)
    result = replay_card_outcome_counts(repo)
    # The interpretation head (argmax 'success') wins over the raw observed_class.
    strata = result.counts[cv]
    outcomes = {k for classes in strata.values() for k in classes}
    assert outcomes == {"success"}


# --- §9.8 (c): U-014 resume shape ---------------------------------------------

def test_u014_resume_shape_emits_card_level_counts(repo):
    fam, _card_id, cv = _card(repo, tag="s4")
    lineage = CL.start_lineage(repo, genesis_card_version_id=cv, family_id=fam, card_id=_card_id, clock=CLOCK)
    for i in range(3):
        _submit(repo, surface=_surface(repo, cv, tag=f"s4-{i}"), cv=cv, family_id=fam, lineage_id=lineage,
                tag=f"s4-{i}", context={"cold": True}, correct=(i < 2))
    shape = u014_resume_shape(replay_card_outcome_counts(repo))
    assert shape["card_count"] == 1
    card = shape["cards"][cv]
    assert card["n"] == 3
    assert card["outcome_totals"] == {"correct": 2, "incorrect": 1}
    assert "contexts" in card and card["contexts"]
    assert shape["manifest"]["u014_resume_shape_version"] == "v1"


# --- §9.7: deterministic replay of 10,000 synthetic events + manifest ---------

def _synthetic_stream(n):
    events = []
    for i in range(n):
        # A deterministic (seedless, index-driven) synthetic stream.
        card = f"cv-{i % 7}"
        outcome = "correct" if (i * 31 + 7) % 5 != 0 else "incorrect"
        cold = (i % 3) == 0
        events.append({
            "seq": i, "card_version_id": card, "outcome_class": outcome,
            "admin_context": {"cold": cold, "open_book": (i % 4 == 0)},
        })
    return events


def test_ten_thousand_event_replay_is_deterministic_with_manifest():
    stream = _synthetic_stream(10_000)
    first = replay_event_stream(stream)
    second = replay_event_stream(stream)
    assert first.events_replayed == 10_000
    # Deterministic: identical output for the same stream.
    assert first.as_dict()["counts"] == second.as_dict()["counts"]
    # Order-independent: shuffling the input yields the identical fold.
    shuffled = list(reversed(stream))
    assert replay_event_stream(shuffled).as_dict()["counts"] == first.as_dict()["counts"]
    # Reports its algorithm/version manifest (§9.7).
    assert first.manifest["replay_algorithm"] == REPLAY_MANIFEST["replay_algorithm"]
    assert first.manifest["replay_algorithm_version"] == "v1"
    # Total tallies are conserved.
    total = sum(c for strata in first.counts.values() for classes in strata.values() for c in classes.values())
    assert total == 10_000
