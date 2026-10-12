"""F2 placement through the sidecar: self-reports, labels, map and the quick check."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.helpers import create_placement_vault, set_algorithm_version
from tests.test_graph_editor_reads import _blueprint_ctx, _call
from tests.test_km3_projections import INTEG, LO_ID


def _placement_ctx(root, *, version="mvp-0.10"):
    import learnloop_sidecar.handlers  # noqa: F401 -- registers methods

    paths = create_placement_vault(root, version=version)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    return ctx


def test_self_report_rpc_on_an_item_labels_its_lo_in_the_inspector(tmp_path):
    ctx = _placement_ctx(tmp_path / "vault")
    result = _call(ctx, "placement_self_report", {"report": "know_this", "practiceItemId": "pi_diag_mid"})
    assert [(r["learningObjectId"], r["status"]) for r in result["results"]] == [("lo_diag", "assumed")]
    (row,) = result["placement"]["learningObjects"]
    assert row["assumed"] is True and row["label"] == "assumed (not tested)"
    assert row["firstReviewDue"] and row["firstReviewIsDue"] is False

    entity = _call(ctx, "inspect_entity", {"id": "lo_diag"})
    placement = entity["detail"]["placement"]
    assert placement["active"] is True and placement["assumed"] is True
    assert placement["quickCheckK"] == 4 and placement["quickCheckBudgetMinutes"] == 8

    state = _call(ctx, "get_placement_state", {})
    assert [r["learningObjectId"] for r in state["learningObjects"]] == ["lo_diag"]

    back = _call(ctx, "placement_self_report", {"report": "dont_know_this", "learningObjectIds": ["lo_diag"]})
    assert back["results"][0]["status"] == "returned_to_learning"
    assert back["placement"]["learningObjects"][0]["assumed"] is False


def test_self_report_rpc_refuses_honestly_when_placement_is_off(tmp_path):
    ctx = _placement_ctx(tmp_path / "vault", version="mvp-0.9")
    with pytest.raises(SidecarError) as error:
        _call(ctx, "placement_self_report", {"report": "know_this", "learningObjectIds": ["lo_diag"]})
    assert error.value.code == "placement_inactive"
    entity = _call(ctx, "inspect_entity", {"id": "lo_diag"})
    assert entity["detail"]["placement"]["active"] is False


def test_quick_check_rpcs_carry_the_check_and_withhold_results(tmp_path):
    ctx = _placement_ctx(tmp_path / "vault")
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    progress = _call(ctx, "start_quick_check", {"sessionId": session_id, "learningObjectIds": ["lo_diag"]})
    assert progress["quickCheck"]["k"] == 4 and progress["quickCheck"]["results"] is None
    assert progress["nextTarget"]["selectionObjective"] == "conditional_gain"
    again = _call(ctx, "get_calibration_session", {"calibrationSessionId": progress["calibrationSessionId"]})
    assert again["nextTarget"] == progress["nextTarget"]
    stopped = _call(ctx, "stop_calibration_session", {"calibrationSessionId": progress["calibrationSessionId"]})
    assert stopped["status"] == "stopped" and stopped["quickCheck"]["finished"] is True
    assert stopped["quickCheck"]["results"][0]["learningObjectId"] == "lo_diag"


def test_map_labels_assumed_points_without_changing_depth_or_beads(tmp_path):
    """G4 + G6: the assumed label is separate; geometry never reads it."""

    ctx = _blueprint_ctx(tmp_path / "vault")
    set_algorithm_version(SimpleNamespace(root=ctx.vault.root), "mvp-0.10")
    ctx.reload()
    before = _call(ctx, "get_knowledge_map", {})
    assert before["placement"] == {"active": True, "assumed": []}
    _call(ctx, "placement_self_report", {"report": "know_this", "learningObjectIds": [LO_ID]})
    after = _call(ctx, "get_knowledge_map", {})
    assert after["placement"]["assumed"][0]["learningObjectId"] == LO_ID

    old = {point["id"]: point for point in before["facetField"]["points"]}
    new = {point["id"]: point for point in after["facetField"]["points"]}
    label_keys = {"assumed", "assumedLearningObjectIds"}
    for facet_id, point in new.items():
        assert {k: v for k, v in point.items() if k not in label_keys} == {
            k: v for k, v in old[facet_id].items() if k not in label_keys
        }
        if LO_ID in point["learningObjectIds"]:
            assert point["assumed"] is True and point["assumedLearningObjectIds"] == [LO_ID]
    # An assumed, untested facet stays untested: no Ready is claimed for it.
    assert new[INTEG]["untested"] is True and "ready" not in new[INTEG]
