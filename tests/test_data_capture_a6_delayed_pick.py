"""Data capture A6: the teacher's delayed-check picker reads each item's own prediction.

``lo_prediction`` asks ``item_irt_params(None, ...)``, so every item of an LO gets the same prediction and
the smallest id wins. From mvp-0.44, with ``data_capture.serving`` on, the prediction is the item's own (the
one IRT seam ``resolve_item_irt_params``), and an exact tie is a uniform draw with probability 1/n, on the
receipt. Below the tag, or switched off, the predecessor's pick exactly.
"""

from __future__ import annotations

from collections import Counter
import json

import pytest

from learnloop.algorithm_versions import DATA_CAPTURE_ALGORITHM_VERSION, LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.clock import FrozenClock, parse_utc
from learnloop.teacher import brief as B
from learnloop.teacher import delayed as D
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.teacher_fakes import NOW, _item, build_teacher_vault

TAG = DATA_CAPTURE_ALGORITHM_VERSION
OLD = LESSON_SUGGESTIONS_ALGORITHM_VERSION
OFF = "[data_capture]\nserving = false\n"


def _with_difficulties(paths, **difficulties):
    for item_id, difficulty in difficulties.items():
        payload = _item(item_id, "lo_eigen", f"Question {item_id}.", f"Answer {item_id}.")
        payload["difficulty"] = difficulty
        write_yaml(paths.practice_item_path("linear-algebra", item_id), payload)


def _vault(tmp_path, *, version=TAG, config="", **difficulties):
    paths, repository = build_teacher_vault(tmp_path / "vault", reserved=False, version=version, config=config)
    _with_difficulties(paths, **difficulties)
    return paths, repository, load_vault(paths.root)


def _candidates(vault, ids):
    return [vault.practice_items[item_id] for item_id in ids]


def test_the_same_lo_has_a_different_prediction_per_item(tmp_path):
    _paths, repository, vault = _vault(tmp_path, pi_a=0.1, pi_b=0.9)
    easy = B.lo_prediction(vault, repository, "lo_eigen", item=vault.practice_items["pi_a"])
    hard = B.lo_prediction(vault, repository, "lo_eigen", item=vault.practice_items["pi_b"])
    assert easy["p"] > hard["p"]
    # With no item it stays the LO's own prediction, as the brief reads it.
    assert B.lo_prediction(vault, repository, "lo_eigen")["item_b"] != easy["item_b"]


def test_the_pick_is_the_item_nearest_the_band_not_the_smallest_id(tmp_path):
    """Reproduced first: below the tag every item gets one prediction, so pi_a wins whatever its pitch."""

    _paths, repository, vault = _vault(tmp_path, pi_a=0.99, pi_b=0.99, pi_mid=0.5)
    items = _candidates(vault, ["pi_a", "pi_b", "pi_mid"])
    predictions = {item.id: B.lo_prediction(vault, repository, "lo_eigen", item=item)["p"] for item in items}
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


@pytest.mark.parametrize("version, config", [(OLD, ""), (TAG, OFF)])
def test_below_the_tag_or_switched_off_the_smallest_id_wins_as_before(tmp_path, version, config):
    paths, repository, vault = _vault(tmp_path, version=version, config=config, pi_a=0.99, pi_mid=0.5)
    items = _candidates(vault, ["pi_a", "pi_mid"])
    assert D.pick(vault, repository, items).id == "pi_a"
    out, _warnings = D.commit_checks(vault, repository, lesson_id="les_old", landed=[{"id": "n1", "lo_id": "lo_eigen"}],
                                     goal_learning_object_ids=["lo_eigen"], lesson_items_by_lo={}, shown_items=[],
                                     clock=FrozenClock(parse_utc(NOW)))
    assert all("pick" not in check for check in out)
    assert next(check for check in out if check["purpose"] == "retention")["item_id"] == "pi_a"


def test_the_lessons_forecast_reference_is_the_item_the_check_would_commit(tmp_path):
    """``cold_reference`` asks the same picker with the same seed as the retention check's commit."""

    from learnloop.teacher import checks as CH

    _paths, repository, vault = _vault(tmp_path, pi_a=0.5, pi_b=0.5)
    reference = CH.cold_reference(vault, repository, "lo_eigen", lesson_id="les_same", exclude=[], lesson_item_ids=[])
    out, _warnings = D.commit_checks(vault, repository, lesson_id="les_same", landed=[{"id": "n1", "lo_id": "lo_eigen"}],
                                     goal_learning_object_ids=[], lesson_items_by_lo={}, shown_items=[],
                                     clock=FrozenClock(parse_utc(NOW)))
    assert next(check for check in out if check["purpose"] == "retention")["item_id"] == reference["item_id"]
