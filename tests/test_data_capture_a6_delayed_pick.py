"""Data capture A6: the teacher's delayed-check picker reads each item's own prediction.

``lo_prediction`` asks ``item_irt_params(None, ...)``, so every item of an LO gets the same prediction and
the smallest id wins. From mvp-0.44 the prediction is the item's own (the one IRT seam
``resolve_item_irt_params``), and an exact tie is a uniform draw with probability 1/n, on the receipt (its
switch went once every vault was past the tag).
"""

from __future__ import annotations

from collections import Counter
import json

import pytest

from learnloop.algorithm_versions import (
    FORECAST_SCORING_ALGORITHM_VERSION,
    LESSON_WEIGHT_CURVES_ALGORITHM_VERSION,
    DATA_CAPTURE_ALGORITHM_VERSION,
    LABEL_RETIRED_ALGORITHM_VERSION,
    LESSON_WEIGHT_FACTS_ALGORITHM_VERSION,
    OUTCOME_FIXES_ALGORITHM_VERSION,
    PROBE_ROUTER_ALGORITHM_VERSION,
)
from learnloop import delayed_checks as DC
from learnloop.clock import FrozenClock, parse_utc
from learnloop.teacher import brief as B
from learnloop.teacher import delayed as D
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.teacher_fakes import NOW, _item, build_teacher_vault

TAG = DATA_CAPTURE_ALGORITHM_VERSION


def _with_difficulties(paths, **difficulties):
    for item_id, difficulty in difficulties.items():
        payload = _item(item_id, "lo_eigen", f"Question {item_id}.", f"Answer {item_id}.")
        payload["difficulty"] = difficulty
        write_yaml(paths.practice_item_path("linear-algebra", item_id), payload)


# The pick's per-item predictions come from the items' labels; from the difficulty label's retirement mastery reads
# none, so these tests run at the newest tag before it (the retirement's own case is the last test).
LABEL_READ_VERSION = PROBE_ROUTER_ALGORITHM_VERSION


def _vault(tmp_path, *, version=LABEL_READ_VERSION, config="", **difficulties):
    paths, repository = build_teacher_vault(tmp_path / "vault", reserved=False, version=version, config=config)
    _with_difficulties(paths, **difficulties)
    return paths, repository, load_vault(paths.root)


def _candidates(vault, ids):
    return [vault.practice_items[item_id] for item_id in ids]


def test_the_same_lo_has_a_different_prediction_per_item(tmp_path):
    _paths, repository, vault = _vault(tmp_path, pi_a=0.1, pi_b=0.9)
    easy = DC.predicted_item_success(vault, repository, vault.practice_items["pi_a"])
    hard = DC.predicted_item_success(vault, repository, vault.practice_items["pi_b"])
    assert easy > hard
    # The brief's LO prediction stays what it was: the LO's own, one number.
    assert B.lo_prediction(vault, repository, "lo_eigen")["p"] not in (round(easy, 4), round(hard, 4))


def test_the_pick_is_the_item_nearest_the_band_not_the_smallest_id(tmp_path):
    """Reproduced first: below the tag every item gets one prediction, so pi_a wins whatever its pitch."""

    _paths, repository, vault = _vault(tmp_path, pi_a=0.99, pi_b=0.99, pi_mid=0.5)
    items = _candidates(vault, ["pi_a", "pi_b", "pi_mid"])
    predictions = {item.id: DC.predicted_item_success(vault, repository, item) for item in items}
    band = vault.config.adaptive_difficulty.practice_band
    middle = (band[0] + band[1]) / 2.0
    nearest = min(predictions, key=lambda item_id: abs(predictions[item_id] - middle))
    assert predictions["pi_a"] != predictions["pi_mid"]
    item, receipt = D.pick_with_receipt(vault, repository, items, seed_key="k")
    assert item.id == nearest
    assert receipt["tied"] == [nearest] and receipt["n"] == 1 and receipt["propensity"] == 1.0
    assert receipt["draw"] is None
    assert {row["item_id"] for row in receipt["considered"]} == {"pi_a", "pi_b", "pi_mid"}
    assert receipt["version"] == D.PICK_VERSION and receipt["predictor"] == "mastery_ekf_item"


def test_an_exact_tie_is_a_logged_uniform_draw_with_probability_one_over_n(tmp_path):
    _paths, repository, vault = _vault(tmp_path, pi_a=0.5, pi_b=0.5, pi_c=0.5)
    items = _candidates(vault, ["pi_a", "pi_b", "pi_c"])
    item, receipt = D.pick_with_receipt(vault, repository, items, seed_key="lesson:1")
    assert receipt["tied"] == ["pi_a", "pi_b", "pi_c"] and receipt["n"] == 3
    assert receipt["propensity"] == pytest.approx(1 / 3)
    assert receipt["seed"] and 0.0 <= receipt["draw"] < 1.0
    assert item.id == receipt["chosen"] == receipt["tied"][int(receipt["draw"] * 3)]
    # The seed reproduces it; the draw reaches every tied item (no smallest-id win).
    again, _ = D.pick_with_receipt(vault, repository, items, seed_key="lesson:1")
    assert again.id == item.id
    counts = Counter(D.pick_with_receipt(vault, repository, items, seed_key=f"lesson:{i}")[0].id for i in range(300))
    assert set(counts) == {"pi_a", "pi_b", "pi_c"}
    assert min(counts.values()) > 60


def test_a_near_tie_is_no_tie(tmp_path):
    """Exact ties only: two pitches a hair apart keep the nearer, whatever their display rounds to."""

    _paths, repository, vault = _vault(tmp_path, pi_a=0.5, pi_b=0.50001)
    _item_chosen, receipt = D.pick_with_receipt(vault, repository, _candidates(vault, ["pi_a", "pi_b"]), seed_key="k")
    assert receipt["n"] == 1 and receipt["draw"] is None


def test_commit_checks_carry_the_delayed_check_receipt_fields(tmp_path):
    paths, repository, vault = _vault(tmp_path, pi_a=0.5, pi_b=0.5)
    out, _warnings = D.commit_checks(vault, repository, lesson_id="les_a6", landed=[{"id": "n1", "lo_id": "lo_eigen"}],
                                     goal_learning_object_ids=["lo_eigen"], lesson_items_by_lo={}, shown_items=[],
                                     clock=FrozenClock(parse_utc(NOW)))
    retention = next(check for check in out if check["purpose"] == "retention")
    assert retention["pick"]["version"] == D.PICK_VERSION
    assert retention["pick"]["chosen"] == retention["item_id"]
    assert retention["pick"]["propensity"] == pytest.approx(1 / retention["pick"]["n"])
    with repository.connection() as connection:
        provenance = json.loads(connection.execute(
            "SELECT provenance_json FROM commitment_versions WHERE commitment_id = ?", (retention["commitment_id"],)
        ).fetchone()[0])
    assert provenance["pick"] == retention["pick"]


def test_the_lessons_forecast_reference_is_the_item_the_check_would_commit(tmp_path):
    """``cold_reference`` asks the same picker with the same seed as the retention check's commit."""

    from learnloop.teacher import checks as CH

    _paths, repository, vault = _vault(tmp_path, pi_a=0.5, pi_b=0.5)
    reference = CH.cold_reference(vault, repository, "lo_eigen", lesson_id="les_same", exclude=[], lesson_item_ids=[])
    out, _warnings = D.commit_checks(vault, repository, lesson_id="les_same", landed=[{"id": "n1", "lo_id": "lo_eigen"}],
                                     goal_learning_object_ids=[], lesson_items_by_lo={}, shown_items=[],
                                     clock=FrozenClock(parse_utc(NOW)))
    assert next(check for check in out if check["purpose"] == "retention")["item_id"] == reference["item_id"]


def test_from_the_label_retirement_an_los_items_tie_and_the_pick_draws(tmp_path):
    """Mastery predicts every item of one LO alike once it reads no label, so the nearest-the-band rule finds a tie
    among them and the pick draws, its receipt recording the draw. AD for selection is a later question."""

    _paths, repository, vault = _vault(tmp_path, version=LABEL_RETIRED_ALGORITHM_VERSION, pi_a=0.1, pi_b=0.9)
    items = _candidates(vault, ["pi_a", "pi_b"])
    predictions = {item.id: DC.predicted_item_success(vault, repository, item) for item in items}
    assert predictions["pi_a"] == predictions["pi_b"]
    _item_chosen, receipt = D.pick_with_receipt(vault, repository, items, seed_key="k")
    assert receipt["n"] == 2 and receipt["draw"] is not None


@pytest.mark.parametrize("version", [LESSON_WEIGHT_CURVES_ALGORITHM_VERSION, FORECAST_SCORING_ALGORITHM_VERSION])
def test_two_landed_nodes_on_one_lo_draw_their_checks_from_their_own_seeds(tmp_path, version):
    """From the fix round's tag each landed node's retention check is seeded on its node: two nodes on one LO no
    longer share one uniform draw, which made the second pick a function of the first (its recorded 1/2 really 1).
    Below the tag, one seed per lesson and LO, as it was."""

    paths, repository, vault = _vault(tmp_path, version=version, pi_a=0.5, pi_b=0.5, pi_mid=0.5)
    out, _warnings = D.commit_checks(
        vault, repository, lesson_id="les_two", landed=[{"id": "n1", "lo_id": "lo_eigen"}, {"id": "n2", "lo_id": "lo_eigen"}],
        goal_learning_object_ids=["lo_eigen"], lesson_items_by_lo={}, shown_items=[], clock=FrozenClock(parse_utc(NOW)))
    seeds = [check["pick"]["seed"] for check in out if check["purpose"] == "retention"]
    assert len(seeds) == 2 and all(seeds)
    assert (seeds[0] != seeds[1]) is (version == FORECAST_SCORING_ALGORITHM_VERSION)


@pytest.mark.parametrize("version", [LESSON_WEIGHT_FACTS_ALGORITHM_VERSION, OUTCOME_FIXES_ALGORITHM_VERSION])
def test_each_landed_nodes_retention_forecast_targets_the_item_it_is_committed(tmp_path, version):
    """FR3-15: two landed nodes on one LO with tied cold items. At commitment the first node reserves its pick and the
    second draws from those left. From the outcome fixes' tag each node's retention forecast (``cold_reference``, given
    the nodes landed before it) names the item its check is committed and the pick's logged propensity; below the tag
    the second node's forecast drew from every candidate, the first node's item included."""

    from learnloop.teacher import checks as CK

    _paths, repository, vault = _vault(tmp_path, version=version, pi_a=0.5, pi_b=0.5, pi_mid=0.5)
    nodes = [{"id": "n1", "lo_id": "lo_eigen"}, {"id": "n2", "lo_id": "lo_eigen"}]
    references = [CK.cold_reference(vault, repository, "lo_eigen", lesson_id="les_two", exclude=[], lesson_item_ids=[],
                                    node_id=node["id"], prior_nodes=nodes[:index])
                  for index, node in enumerate(nodes)]
    out, _warnings = D.commit_checks(
        vault, repository, lesson_id="les_two", landed=nodes, goal_learning_object_ids=["lo_eigen"],
        lesson_items_by_lo={}, shown_items=[], clock=FrozenClock(parse_utc(NOW)))
    committed = [check for check in out if check["purpose"] == "retention"]
    tied = committed[0]["pick"]["n"]
    assert tied > 2 and committed[1]["pick"]["n"] == tied - 1
    assert committed[0]["item_id"] != committed[1]["item_id"]
    assert references[0]["item_id"] == committed[0]["item_id"]
    if version == OUTCOME_FIXES_ALGORITHM_VERSION:
        assert [reference["item_id"] for reference in references] == [check["item_id"] for check in committed]
        assert [reference["pick"] for reference in references] == [check["pick"] for check in committed]
        assert references[1]["pick"]["propensity"] == pytest.approx(1.0 / (tied - 1))
    else:
        assert "pick" not in references[1]


def test_a_nodes_forecast_is_allocated_after_the_nodes_landed_before_it():
    """FR3-15: the lesson passes each node's forecast the nodes the commitment allocates first: the landed nodes in
    landing order up to the node, or all of them when it has not landed yet."""

    from types import SimpleNamespace

    from learnloop.teacher.service import _landed_before

    state = SimpleNamespace(landed=["n1", "n2", "n1"], node_lo=lambda node: f"lo_{node}")
    assert _landed_before(state, "n1") == []
    assert _landed_before(state, "n2") == [{"id": "n1", "lo_id": "lo_n1"}]
    assert _landed_before(state, "n3") == [{"id": "n1", "lo_id": "lo_n1"}, {"id": "n2", "lo_id": "lo_n2"}]


def test_a_retention_forecasts_item_answered_before_commitment_is_marked_on_the_commitment(tmp_path):
    """Review round 4, R4-S12 (FR3-15's residue): the node's check weighed its mass against the retention forecast of
    item X (``cold_reference``); X is answered elsewhere (the phone) before the lesson closes, so the commitment's
    allocation excludes it and commits another item. The check's recorded mass stands (it entered mastery), and the
    commitment's entry names the forecast's item and the mismatch (failed before: nothing said the forecast was of
    another item)."""

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.teacher import checks as CK

    _paths, repository, vault = _vault(tmp_path, version=OUTCOME_FIXES_ALGORITHM_VERSION, pi_a=0.5, pi_b=0.5,
                                       pi_mid=0.5)
    nodes = [{"id": "n1", "lo_id": "lo_eigen"}]
    reference = CK.cold_reference(vault, repository, "lo_eigen", lesson_id="les_one", exclude=[], lesson_item_ids=[],
                                  node_id="n1", prior_nodes=[])
    complete_self_graded_attempt(vault, repository, AttemptDraft(reference["item_id"], "answered on the phone"),
                                 SelfGradeInput({"correctness": 1}, 3), clock=FrozenClock(parse_utc(NOW)))
    out, warnings = D.commit_checks(
        vault, repository, lesson_id="les_one", landed=nodes, goal_learning_object_ids=["lo_eigen"],
        lesson_items_by_lo={}, shown_items=[], forecast_items={"n1": reference["item_id"]},
        clock=FrozenClock(parse_utc(NOW)))
    [retention] = [check for check in out if check["purpose"] == "retention"]
    assert retention["item_id"] != reference["item_id"]
    assert retention["forecast_item_id"] == reference["item_id"] and retention["forecast_item_mismatch"] is True
    assert any("forecast" in warning for warning in warnings)
