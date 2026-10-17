"""RW6a Codex review, round 3 (docs/reviews/reader-rw6a-codex-review.md).

* F1 (round 3) -- "as of the previous session's end" decides the regrade-
  contract replay hold (mvp-0.26, ``grade_contract_unrecorded``) from the
  grading epoch effective at the cutoff: a contract-bearing regrade that
  releases the hold later does not lift it at the cutoff.
* F2 (round 3) -- whether an attempt answers a claim needing an independent
  check is read on the current state: embedded credit that banked only
  beside direct credit a later regrade took away answers nothing.

Everything runs through the production writes (the attempt step, the regrade
door with a deterministic grader fake, the mvp-0.26 upgrade), extraction,
fold, certification and recap; no snapshot or timeline is mocked. Fakes only;
no model call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, METHOD_EXPLICIT_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.goals.goal_certification import lo_certification
from learnloop.grading_epochs import current_epoch
from learnloop.held_grades import attempt_grade_held, contract_unrecorded_attempts
from learnloop.learner.facet_evidence_timeline import (
    facet_evidence_timelines,
    snapshot_as_of,
    vault_timeline_snapshot,
)
from learnloop.reader import recap as RC
from learnloop.regrade_contract_upgrade import upgrade_to_mvp026
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import NOW, set_algorithm_version
from tests.recap_fixtures import at
from tests.split_live_helpers import ReadyRuntime
from tests.test_goal_certification_any_of import COMP_A, LO_ID, _component, _item, build_vault
from tests.test_reader_recap_review_r2 import (
    EMBEDDED_ITEM,
    RECALL_ITEM,
    _assisted_session,
    _claimed,
    _embedded_world,
    _self_graded,
)
from tests.test_regrade_contract_replay import PointsGrader


def _stamp(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _regrade(vault, repository, attempt_id: str, minutes: float, points: float) -> None:
    """The production regrade door (``regrade_attempt``), its grader a fake
    that awards ``points`` on ``c1``."""

    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(attempt_id), runtime=ReadyRuntime(),
        client=PointsGrader({"c1": float(points)}), grading_source="ai",
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )


# -- F1 (round 3): the replay hold as of the cutoff -------------------------------------------------

#: A second instrument for ``COMP_A`` on its own surface, so its credit is not
#: repeat-discounted against the held attempt's.
SECOND_ITEM = "pi_comp_a_second_surface"


def _self_graded_comp(vault, repository, item_id: str, minutes: float, points: float) -> str:
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"c1": points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )
    return str(result.attempt_id)


def _held_then_released(tmp_path):
    """An mvp-0.25 vault (the predecessor's regrade cites no contract):

    * minute 5: attempt H, self-graded 0 of 4 on ``COMP_A``;
    * minute 10: attempt O, self-graded 2 of 4 on a second surface;
    * minute 20: H regraded to 4 of 4 by the predecessor's regrade door,
      which records no contract;
    * minute 30: ``upgrade --to mvp-0.26`` holds H (``grade_contract_unrecorded``);
    * minute 40: the previous session ends (the cutoff);
    * minute 50: H regraded to 4 of 4 again at mvp-0.26, which cites its
      contract and releases the hold.
    """

    paths = build_vault(tmp_path / "vault", {"id": "recipe_main", "composition": "conjunctive",
                                              "all_of": [_component(COMP_A)], "any_of": []})
    write_yaml(paths.practice_item_path("linear-algebra", SECOND_ITEM),
               _item(SECOND_ITEM, facet=COMP_A, capability="procedure_execution", correlation_group="second_surface"))
    set_algorithm_version(paths, METHOD_EXPLICIT_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    held = _self_graded_comp(vault, repository, "pi_comp_a", 5, 0)
    other = _self_graded_comp(vault, repository, SECOND_ITEM, 10, 2)
    _regrade(vault, repository, held, 20, 4)
    epoch = current_epoch(repository.fetch_grading_evidence(held))
    assert epoch is not None and epoch.contract_version_id is None
    result = upgrade_to_mvp026(paths.root, clock=FrozenClock(NOW + timedelta(minutes=30)))
    assert result.upgraded, result.problems
    vault = load_vault(paths.root)
    assert attempt_grade_held(repository, held)
    return paths, vault, repository, held, other


def test_f1_r3_a_hold_released_after_the_cutoff_still_holds_at_the_cutoff(tmp_path):
    paths, vault, repository, held, other = _held_then_released(tmp_path)
    lo = vault.learning_objects[LO_ID]
    # Held, H banks nothing: the LO is not demonstrated.
    assert lo_certification(vault, repository, lo).demonstrated is False
    before_release = facet_evidence_timelines(vault, repository, [COMP_A])[COMP_A]
    credit_held = dict(before_release[-1].capability_credit)["procedure_execution"]

    _regrade(vault, repository, held, 50, 4)
    epoch = current_epoch(repository.fetch_grading_evidence(held))
    assert epoch is not None and epoch.contract_version_id is not None
    with repository.connection() as connection:
        assert held not in contract_unrecorded_attempts(connection)
    assert not attempt_grade_held(repository, held)
    # Released, H banks: the LO is demonstrated now.
    assert lo_certification(vault, repository, lo).demonstrated is True

    # As of the cutoff the epoch then current (the uncited regrade) was held:
    # H's credit then is 0, and the curve is the one that stood then.
    then = facet_evidence_timelines(vault, repository, [COMP_A], as_of=_stamp(40))[COMP_A]
    held_then = [point for point in then if point.attempt_id == held]
    assert held_then and held_then[-1].attempt_credit == 0.0 and held_then[-1].attempt_banked_credit == 0.0
    assert dict(then[-1].capability_credit)["procedure_execution"] == pytest.approx(credit_held)
    assert [point.as_dict() for point in then] == [point.as_dict() for point in before_release]

    # So the release is the gain since the session, dated by H's release.
    gains = RC.demonstrated_since(vault, repository, [LO_ID], after=_stamp(40))
    assert [(row["learning_object_id"], row["demonstrated_on"], row["attempt_id"]) for row in gains] == [
        (LO_ID, _stamp(50), held),
    ]
    snapshot = vault_timeline_snapshot(vault, repository)
    assert held in snapshot_as_of(snapshot, _stamp(40), vault=vault).contract_unrecorded
    # After the release nothing is new; as of a moment after every write the
    # replay is the current curve.
    assert RC.demonstrated_since(vault, repository, [LO_ID], after=_stamp(55)) == []
    now = facet_evidence_timelines(vault, repository, [COMP_A])[COMP_A]
    late = facet_evidence_timelines(vault, repository, [COMP_A], as_of=_stamp(60))[COMP_A]
    assert [point.as_dict() for point in late] == [point.as_dict() for point in now]


def test_f1_r3_the_as_of_hold_is_the_replay_predicate_on_the_ledger(tmp_path):
    """The predicate the cutoff applies, evaluated on every attempt's whole
    ledger, holds exactly the attempts the mvp-0.26 upgrade's replay held:
    the uncited regrades, never a contract-cited grade or an only grade."""

    from learnloop.learner.facet_evidence_timeline import _epoch_held_as_of

    paths, vault, repository, held, other = _held_then_released(tmp_path)
    snapshot = vault_timeline_snapshot(vault, repository)
    items = {str(row["id"]): row.get("practice_item_id") for row in snapshot.attempts}
    predicted = {
        attempt_id for attempt_id, rows in snapshot.grading_by_attempt.items()
        if _epoch_held_as_of(rows, vault, items.get(attempt_id))
    }
    assert predicted == set(snapshot.contract_unrecorded) == {held}


# -- F2 (round 3): a claim is answered on the current state -----------------------------------------


def _versioned_embedded_world(tmp_path, version):
    vault, repo = _embedded_world(tmp_path)
    set_algorithm_version(VaultPaths(vault.root, vault.config), version)
    return load_vault(vault.root), repo


def _direct_then_embedded(vault, repo):
    """D (before the session) banks direct credit on ``recall``; the session
    leaves a claim on it; E (unassisted, after the session starts) adds
    embedded credit on ``recall``, which banks under the default cap beside
    D's direct credit."""

    direct = _self_graded(vault, repo, RECALL_ITEM, -10, "c1", 4)
    session = _assisted_session(vault, repo)
    embedded = _self_graded(vault, repo, EMBEDDED_ITEM, 200, "c1", 4)
    repo.insert_trace_exercised_facets(embedded, [{"facet_id": "recall", "observation_scope": "opportunistic",
                                                   "evidence": "the trace shows it"}], clock=at(200))
    return direct, embedded, session


@pytest.mark.parametrize("version", ["mvp-0.7", LATEST_ALGORITHM_VERSION])
def test_f2_r3_embedded_credit_whose_direct_credit_was_regraded_away_leaves_the_claim_open(tmp_path, version):
    vault, repo = _versioned_embedded_world(tmp_path, version)
    assert vault.config.evidence.certification.max_embedded_credit_share == 0.5
    facet = vault.canonical_facet_id("recall")
    direct, embedded, session = _direct_then_embedded(vault, repo)

    _regrade(vault, repo, direct, 260, 0)
    # The ledger banks nothing in the cell now: embedded credit alone is capped to 0.
    cell = repo.facet_capability_evidence(facet, "recall")
    assert cell is not None and cell.certification_credit == 0.0 and cell.embedded_positive_mass > 0.0
    curve = facet_evidence_timelines(vault, repo, [facet])[facet]
    assert dict(curve[-1].capability_credit)["recall"] == pytest.approx(0.0, abs=1e-9)
    assert _claimed(vault, repo, session) == [facet]
    [e_point] = [point for point in curve if point.attempt_id == embedded]
    assert e_point.attempt_credit > 0.0 and not e_point.assisted
    assert e_point.attempt_banked_credit == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("version", ["mvp-0.7", LATEST_ALGORITHM_VERSION])
def test_f2_r3_embedded_credit_banking_beside_standing_direct_credit_answers_the_claim(tmp_path, version):
    """The inverse control: D still stands, so E's embedded credit banks
    under the cap, and E answers the claim (D itself is before the session)."""

    vault, repo = _versioned_embedded_world(tmp_path, version)
    facet = vault.canonical_facet_id("recall")
    direct, embedded, session = _direct_then_embedded(vault, repo)

    curve = facet_evidence_timelines(vault, repo, [facet])[facet]
    [e_point] = [point for point in curve if point.attempt_id == embedded]
    assert e_point.attempt_banked_credit > 1e-9
    assert _claimed(vault, repo, session) == []


def test_f1_r3_the_as_of_hold_agrees_with_the_upgrade_on_every_shape(tmp_path):
    """The upgrade suite's predecessor vault: a seeded history of only grades,
    ``att_keep`` (cites its contract), ``att_blind`` and ``att_self`` (uncited
    regrades). The predicate holds exactly the two the upgrade's replay held."""

    from learnloop.learner.facet_evidence_timeline import _epoch_held_as_of
    from tests.test_regrade_contract_upgrade import CLOCK, _legacy_vault

    paths, vault, repository = _legacy_vault(tmp_path)
    assert upgrade_to_mvp026(paths.root, clock=CLOCK).upgraded
    vault = load_vault(paths.root)
    snapshot = vault_timeline_snapshot(vault, repository)
    items = {str(row["id"]): row.get("practice_item_id") for row in snapshot.attempts}
    predicted = {
        attempt_id for attempt_id, rows in snapshot.grading_by_attempt.items()
        if _epoch_held_as_of(rows, vault, items.get(attempt_id))
    }
    assert len(snapshot.grading_by_attempt) > 3
    assert predicted == set(snapshot.contract_unrecorded) == {"att_blind", "att_self"}
