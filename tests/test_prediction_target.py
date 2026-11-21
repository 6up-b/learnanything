"""A prediction target's canonical serialization and ``target_hash`` (``learnloop.db.prediction_target``, EP spec
§7.7.4): independent of member order, sensitive to every typed field (revisions, unit, action, horizon, anchor,
event and resolver versions), free of display text, and round-tripping exactly. The hash itself is pinned in
``tests/goldens/identities.toml`` (site EP0t)."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from learnloop.db.prediction_target import PredictionTarget, TargetMember

ITEM = TargetMember("item", "pi_svd_compute_001", revision="sha256:" + "a" * 64)
LO = TargetMember("learning_object", "lo_svd_compute")
FACET = TargetMember("facet", "setup")
GROUP = TargetMember("surface_group", "svd_compute", source="authored")


def target(**changes) -> PredictionTarget:
    base = dict(kind="item_unassisted_success", members=(ITEM, LO, FACET, GROUP), unit="category3",
                event_version="ad_category@1", resolver_version="ad_resolver@1", action_kind="serve",
                action_id="pi_svd_compute_001", horizon_kind="next_attempt", horizon=None,
                anchor_kind="plan_presentation", anchor_id="pp_01")
    return PredictionTarget(**{**base, **changes})


def test_member_order_does_not_move_the_hash():
    forward = target()
    backward = target(members=(GROUP, FACET, LO, ITEM))
    assert forward == backward
    assert forward.canonical_json() == backward.canonical_json()
    assert forward.target_hash() == backward.target_hash()
    assert [member.kind for member in forward.members] == ["facet", "item", "learning_object", "surface_group"]


def test_canonical_json_is_sorted_and_compact():
    text = target().canonical_json()
    assert text == json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert target().target_hash().startswith("sha256:") and len(target().target_hash()) == 7 + 64


@pytest.mark.parametrize("change", [
    {"members": (replace(ITEM, revision="sha256:" + "b" * 64), LO, FACET, GROUP)},  # the item's revision
    {"members": (ITEM, LO, FACET, replace(GROUP, source="derived"))},  # the surface group's source
    {"members": (ITEM, LO, FACET)},  # a member fewer
    {"members": (ITEM, LO, FACET, GROUP, TargetMember("facet", "result"))},  # a member more
    {"unit": "binary"},
    {"action_kind": None, "action_id": None},  # unconditional
    {"action_id": "pi_svd_compute_002"},
    {"horizon_kind": "duration", "horizon": "P7D"},
    {"horizon": "P1D", "horizon_kind": "duration"},
    {"anchor_id": "pp_02"},
    {"event_version": "ad_category@2"},
    {"resolver_version": "ad_resolver@2"},
    {"kind": "lo_cold_success"},
])
def test_every_typed_field_moves_the_hash(change):
    assert target(**change).target_hash() != target().target_hash()


def test_horizons_differ_from_each_other():
    hashes = {target(horizon_kind="duration", horizon=value).target_hash() for value in ("P1D", "P7D", "P30D")}
    assert len(hashes) == 3


def test_a_missing_revision_differs_from_an_empty_one():
    bare = TargetMember("item", "pi_x")
    empty = TargetMember("item", "pi_x", revision="")
    assert target(members=(bare,)).target_hash() != target(members=(empty,)).target_hash()


def test_round_trip():
    value = target(members=(ITEM, TargetMember("facet", "réponse")), horizon_kind="duration", horizon="P7D")
    assert PredictionTarget.from_json(value.canonical_json()) == value
    assert PredictionTarget.from_dict(value.to_dict()).target_hash() == value.target_hash()


def test_refusals():
    with pytest.raises(ValueError):
        target(members=())
    with pytest.raises(ValueError):
        target(members=(ITEM, ITEM))  # a repeated member is refused, not collapsed
    with pytest.raises(ValueError):
        TargetMember("lesson", "x")
    with pytest.raises(ValueError):
        TargetMember("item", "")
    with pytest.raises(TypeError):
        TargetMember("item", "pi", revision=3)  # no number reaches the hash
    with pytest.raises(TypeError):
        target(horizon=7)
    with pytest.raises(ValueError):
        target(unit="")
    with pytest.raises(ValueError):
        PredictionTarget.from_dict({**target().to_dict(), "schema": "prediction_target/2"})
    # No display text: a statement or title is not a field.
    with pytest.raises(TypeError):
        target(title="SVD")  # type: ignore[call-arg]


def test_the_pinned_target_is_the_identity_pins_fixture():
    from tests.identity_pins_helpers import prediction_target_pin

    pinned = prediction_target_pin()
    assert pinned["target_hash"] == PredictionTarget.from_json(pinned["canonical_json"]).target_hash()
