"""The canonical projection and the facet evidence timeline fold the same ledger the same way.

Both folds once took the reliability-discounted mass (P0) and the regrade-contract epoch reading only at or
above their tags; refactor D5 removed both tag gates from the two folds together. This pins that, on a vault
at the head, the two agree on the rows those readings exist for: a cold-calibrated self-grade (its mass is
discounted), a grade revised by an adjudication (two epochs, the current one last), a grade written before
contract lineage (rows citing no contract, keyed by their stamp), and a regrade written before regrade
contracts (its current epoch's contract is unrecorded, so replay holds it and both folds bank nothing), also when
the regrade kept every mark, and a regrade under an item retargeted since the grade (the current epoch no longer
names a facet the first one credited)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.attempts.grade_resolution import append_adjudication
from learnloop.attempts.measurement_corrections import create_measurement_correction
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.held_grades import contract_unrecorded_attempts
from learnloop.learner.facet_evidence_timeline import facet_evidence_timeline
from learnloop.substrate.canonical_projection import p0_effective_evidence_mass
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.held_grade_evidence_helpers import T
from tests.helpers import NOW, add_followup_item, create_basic_vault
from tests.km2_write_path_helpers import _attempt as km2_attempt, build_shared_facet_vault
from tests.regrade_contract_replay_helpers import _regrade, _self_graded_apply
from tests.regrade_contract_successor_helpers import as_graded_before_contracts, as_regraded_before_contracts
from tests.route_rules_in_grader_helpers import ITEM
from tests.split_live_helpers import split_vault

ITEMS = ("pi_svd_define_001", "pi_svd_define_002", "pi_svd_define_003", "pi_svd_define_004")


def _attempt(vault, repository, item_id, minutes, points=4):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="U Sigma V transpose.",
                     attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    ).attempt_id


def _flip(repository, attempt_id, minutes):
    """An owner adjudication that flips a full-marks grade: a second, superseding grading epoch."""

    observation = repository.observation_by_attempt(attempt_id)
    raw = repository.raw_grade_events_for_observation(observation["id"])
    result = append_adjudication(
        repository,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw[-1]["id"]],
        adjudicator_source="human_owner",
        resolved_class="other",
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )
    assert result["evidence_revision"]["status"] == "revised", result


def _build(tmp_path, *, held_regrade: bool):
    paths = create_basic_vault(tmp_path / "vault")
    for item_id in ITEMS[1:]:
        add_followup_item(paths.root, item_id)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    cold = _attempt(vault, repository, ITEMS[0], 1)
    revised = _attempt(vault, repository, ITEMS[1], 2)
    _flip(repository, revised, 3)
    uncited = _attempt(vault, repository, ITEMS[2], 4)
    as_graded_before_contracts(repository, uncited)
    attempts = {"cold": cold, "revised": revised, "uncited": uncited}
    if held_regrade:
        held = _attempt(vault, repository, ITEMS[3], 5)
        _flip(repository, held, 6)
        as_regraded_before_contracts(repository, held, supersede_tiers=(1, 3))
        attempts["held"] = held
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))
    return vault, repository, attempts


@pytest.fixture
def ledger(tmp_path):
    return _build(tmp_path, held_regrade=True)


def _assert_the_timeline_ends_at_the_banked_credit(vault, repository):
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    assert sum(banked.values()) > 0.0
    facets = set(banked) | {
        vault.canonical_facet_id(str(facet)) for item in vault.practice_items.values() for facet in item.evidence_facets
    }
    for facet in sorted(facets):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(banked.get(facet, 0.0), abs=1e-12), facet


def test_the_ledger_holds_each_reading_the_folds_share(ledger):
    vault, repository, attempts = ledger
    rows = {row["attempt_id"]: row for row in repository.canonical_observation_ledger_v2()}
    cold = rows[attempts["cold"]]
    type_mass = attempt_evidence_mass(cold["attempt_type"], vault.config.evidence)
    assert 0.0 < p0_effective_evidence_mass(
        repository, interpretation=cold.get("active_interpretation"), attempt_type_mass=type_mass
    ) < type_mass
    assert len({row["grading_revision"] for row in rows[attempts["revised"]]["evidence"]}) == 1
    assert all(row.get("assessment_contract_version_id") is None for row in rows[attempts["uncited"]]["evidence"])
    with repository.connection() as connection:
        assert contract_unrecorded_attempts(connection) == frozenset({attempts["held"]})


def test_the_timeline_ends_at_the_projections_banked_credit(tmp_path):
    vault, repository, _attempts = _build(tmp_path, held_regrade=False)
    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)


def test_the_timeline_drops_what_a_held_uncited_regrade_holds(ledger):
    vault, repository, _attempts = ledger
    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)


def _as_regraded_unchanged_before_contracts(repository, attempt_id, minutes):
    """A regrade that kept every mark, as a regrade before regrade contracts (mvp-0.26) wrote it (test
    construction only): a second set of rows citing no contract, with no grading revision and no observation id,
    written by the self tier, superseding every row of the first grade."""

    stamp = (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id, criterion_id, points_awarded FROM grading_evidence "
            "WHERE attempt_id = ? AND superseded_at IS NULL",
            (attempt_id,),
        ).fetchall()
        for row_id, criterion_id, points in rows:
            new_id = f"{row_id}_regraded"
            connection.execute(
                "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at) "
                "VALUES (?, ?, ?, ?, 3, ?)",
                (new_id, attempt_id, criterion_id, points, stamp),
            )
            connection.execute(
                "UPDATE grading_evidence SET superseded_at = ?, superseded_by_evidence_id = ? WHERE id = ?",
                (stamp, new_id, row_id),
            )
        connection.commit()


def _assert_the_itemization_sums_to_the_banked_credit(vault, repository):
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    for facet in banked:
        latest_by_attempt = {
            point.attempt_id: sum(line.capped_credit for line in point.derivation)
            for point in facet_evidence_timeline(vault, repository, facet)
        }
        assert sum(latest_by_attempt.values()) == pytest.approx(banked[facet], abs=1e-12), facet


def test_a_held_regrade_that_kept_its_marks_takes_its_credit_off_the_curve(tmp_path):
    """The item's criteria name no targets (its contract compiled them), the attempt's first grade cites the
    contract, and a regrade written before regrade contracts kept every mark: replay holds the attempt, so the
    projection banks nothing for it, and the curve has to step down to the same total at the regrade."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    assert not any(criterion.targets for criterion in vault.rubric_for_item(vault.practice_items[ITEMS[0]]).criteria)
    _attempt(vault, repository, ITEMS[0], 1)
    held = _attempt(vault, repository, ITEMS[0], 2 * 24 * 60)
    _as_regraded_unchanged_before_contracts(repository, held, 2 * 24 * 60 + 60)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=3)))
    with repository.connection() as connection:
        assert contract_unrecorded_attempts(connection) == frozenset({held})

    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)
    _assert_the_itemization_sums_to_the_banked_credit(vault, repository)
    series = facet_evidence_timeline(vault, repository, "recall")
    held_points = [point for point in series if point.attempt_id == held]
    assert [point.kind for point in held_points] == ["observation", "correction"]
    assert held_points[0].delta > 0.0
    assert held_points[-1].delta == pytest.approx(-held_points[0].delta, abs=1e-12)


def test_a_regrade_under_a_retargeted_item_takes_the_old_facets_credit_off_the_curve(tmp_path):
    """Between an attempt's grade and its regrade the item's one criterion on ``recall`` is retargeted to another
    facet: the regrade's rows cite a snapshot of the item as it is now, so the current epoch no longer names
    ``recall``. The projection reads the current epoch alone, so ``recall`` banks nothing for the attempt; its
    curve has to step down to that."""

    paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
    item = vault.practice_items[ITEM]
    full = {criterion.id: criterion.points for criterion in vault.rubric_for_item(item).criteria}
    _self_graded_apply(vault, repository, ITEM, full, attempt_id="att_retargeted", when=T)
    data = item.model_dump(mode="json")
    retargeted = [
        criterion for criterion in data["grading_rubric"]["criteria"]
        if [target["facet"] for target in criterion["targets"]] == ["recall"]
    ]
    assert len(retargeted) == 1
    retargeted[0]["targets"] = [{**retargeted[0]["targets"][0], "facet": "facet_the_item_now_targets"}]
    upsert_practice_item(paths.root, data)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_retargeted", full, when=T + timedelta(days=1))
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(T + timedelta(days=2)))

    banked = {cell.facet_id for cell in repository.facet_capability_evidence_all() if cell.certification_credit > 0}
    assert "facet_the_item_now_targets" in banked
    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)
    _assert_the_itemization_sums_to_the_banked_credit(vault, repository)
    points = [point for point in facet_evidence_timeline(vault, repository, "recall")
              if point.attempt_id == "att_retargeted"]
    assert [point.kind for point in points] == ["observation", "correction"]
    assert points[0].attempt_credit > 0.0
    assert points[-1].attempt_credit == 0.0


def test_a_measurement_correction_that_reinterprets_history_reaches_the_curve(tmp_path):
    """An attempted item is corrected for this vault's projection version with historical reinterpretation: its
    one criterion stops measuring the shared facet. The projection reads the attempt's evidence under the corrected
    contract and banks nothing on the facet; the curve has to read the same contract."""

    paths = build_shared_facet_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    km2_attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    km2_attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, FrozenClock(NOW + timedelta(minutes=5)))
    create_measurement_correction(
        paths.root,
        repository,
        source_practice_item_id="pi_svd_define_001",
        corrected_practice_item_id="pi_svd_define_001_measurement_v2",
        corrected_fields={
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{
                    "id": "correctness", "points": 4, "description": "Correct response, an item-local measure.",
                    "measurement_status": "no_canonical_facet", "targets": [],
                }],
                "fatal_errors": [],
            },
            "criterion_facet_weights": {},
        },
        reason="The criterion measured an item-local response.",
        consuming_projection_version=vault.config.algorithms.algorithm_version,
        reinterpret_historical_evidence=True,
        clock=FrozenClock(NOW + timedelta(minutes=10)),
    )
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))

    _assert_the_timeline_ends_at_the_banked_credit(vault, repository)
    _assert_the_itemization_sums_to_the_banked_credit(vault, repository)
