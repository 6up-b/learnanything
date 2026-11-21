"""Evidence packets EPp, first part: prediction snapshots on new forecast receipts (spec §7.7, §8 EPp, §10).

A new receipt carries, inside its existing JSON bodies, the evidence cutoff it honoured, the pinned identity of
what it predicted, its outcome distribution at the precision available (the three category probabilities of
adaptive difficulty's threshold forecasts) and the provenance of its numbers. Evaluation-only: no existing
receipt key, binary value, input digest, score row, id or seed moves, no row is added, and nothing reads the new
fields to decide anything. Fakes only: no network, no model call.
"""

from __future__ import annotations

import math
import sqlite3
from contextlib import closing
from types import SimpleNamespace

import pytest

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty.material_view import detached_view as material_view
from learnloop.db.connection import connect
from learnloop.db.evidence_cutoff import Cutoff
from learnloop.db.prediction_target import PredictionTarget, TargetMember
from learnloop.db.repositories import Repository
from learnloop.db.stores import forecast_receipts as store
from learnloop.scheduling import forecast_receipts as FR
from learnloop.scheduling import prediction_snapshots as PS
from learnloop.scheduling import voi_forecasts as VF
from learnloop.vault.loader import load_vault

from tests.epp_snapshot_helpers import comparable, journey, receipts, table_rows
from tests.helpers import create_basic_vault

ISSUED = "2026-10-12T09:00:00Z"
THRESHOLDS = ("ad_threshold@subject", "ad_threshold@subject_uniform", "ad_threshold@lo")


def _receipt(key: str = "k1", **changes) -> FR.ForecastReceipt:
    base = dict(
        receipt_key=key, kind=FR.ITEM_UNASSISTED_SUCCESS, forecaster="test_forecaster", forecaster_version="v1",
        scope="presentation", decision_kind="serve", binding_kind="plan_presentation", event="unassisted_success",
        forecast={"p": 0.25, "event": "unassisted_success", "p_categories": None}, inputs={"a": 1},
        parameters=[{"name": "x", "value": 1, "provenance": "structural"}], versions={"forecaster": "v1"},
        inputs_as_of="2026-10-12T08:00:00Z", p=0.25,
        columns={"decision_ref": "pp_1", "practice_item_id": "pi_1", "learning_object_id": "lo_1",
                 "plan_presentation_id": "pp_1"},
    )
    base.update(changes)
    return FR.ForecastReceipt(**base)


def _stored(repository: Repository) -> list[dict]:
    with closing(connect(repository.sqlite_path)) as connection:
        return store.list_receipts(connection)


@pytest.fixture
def repository(tmp_path) -> Repository:
    return Repository(create_basic_vault(tmp_path / "vault").sqlite_path)


# -- the writer's snapshot --------------------------------------------------------------------------------------


def test_a_receipt_round_trips_its_cutoff_target_distribution_and_provenance(repository):
    """What a producer states comes back exactly: the cutoff and target equal their originals after the JSON
    round trip, the target hash is the target's, and the bodies the receipt had before keep every key."""

    cutoff = Cutoff.ad_replay("2026-10-12T08:30:00Z")
    target = PredictionTarget(
        kind=FR.ITEM_UNASSISTED_SUCCESS,
        members=(TargetMember("item", "pi_1", "sha256:" + "1" * 64), TargetMember("learning_object", "lo_1"),
                 TargetMember("surface_group", "fam_1", source="source_family"), TargetMember("facet", "f_1")),
        unit="ad_category3", event_version="ad_category:ad_priors_v1", resolver_version="ad_forecast_scores_v1",
        action_kind="serve", action_id="pi_1", horizon_kind="presentation", anchor_kind="plan_presentation",
        anchor_id="pp_1")
    named = PS.categorical_distribution({"0": 0.5, "1": 0.25, "2": 0.25}, unit="ad_category3",
                                        event="unassisted_success", event_outcomes=("2",))
    parts = PS.SnapshotParts(cutoff=cutoff, source={"ad_state_hash": "abc"}, target=target, distribution=named,
                             provenance={"prior": {"version": "ad_priors_v1"}})
    receipt = _receipt(snapshot=parts)
    assert FR.record_receipts(repository, [receipt], created_at=ISSUED)
    [row] = _stored(repository)
    snapshot = row["versions"]["snapshot"]
    assert snapshot["schema"] == PS.SNAPSHOT_SCHEMA
    assert Cutoff.from_dict(snapshot["cutoff"]["cutoff"]) == cutoff
    assert snapshot["cutoff"]["source"] == {"ad_state_hash": "abc"} and snapshot["cutoff"]["absent"] is None
    assert snapshot["cutoff"]["inputs_as_of"] == {"original": "2026-10-12T08:00:00Z",
                                                  "recorded": "2026-10-12T08:00:00Z", "status": "exact"}
    assert PredictionTarget.from_dict(snapshot["target"]["target"]) == target
    assert snapshot["target"]["target_hash"] == target.target_hash() and snapshot["target"]["stated_by"] == "producer"
    assert snapshot["provenance"]["prior"] == {"version": "ad_priors_v1"}
    assert snapshot["provenance"]["forecaster"] == "test_forecaster"
    assert row["forecast"]["distribution"] == named and "reason" not in row["forecast"]
    # The producer's own keys and every column are what the receipt had before snapshots.
    assert {k: v for k, v in row["forecast"].items() if k != "distribution"} == dict(receipt.forecast)
    assert {k: v for k, v in row["versions"].items() if k != "snapshot"} == {
        "receipt_shape_version": FR.RECEIPT_SHAPE_VERSION, "forecaster": "v1"}
    assert row["inputs"] == {"a": 1} and row["inputs_hash"] == FR.inputs_digest({"a": 1})
    assert row["parameters"] == [{"name": "x", "value": 1, "provenance": "structural"}]
    assert row["p"] == 0.25 and row["inputs_as_of"] == "2026-10-12T08:00:00Z"


def test_the_writer_derives_a_target_from_the_receipt_and_names_what_it_could_not_version(repository):
    """A producer that states nothing gets the target its columns name, the event and resolver versions marked
    unversioned rather than invented, the cutoff recorded absent with its reason, and a binary distribution."""

    receipt = _receipt(columns={"decision_ref": "pp_1", "practice_item_id": "pi_1", "item_content_hash": "h1",
                                "learning_object_id": "lo_1", "facet_id": "f_1", "plan_presentation_id": "pp_1"})
    FR.record_receipts(repository, [receipt], created_at=ISSUED)
    [row] = _stored(repository)
    snapshot = row["versions"]["snapshot"]
    target = PredictionTarget.from_dict(snapshot["target"]["target"])
    assert {(m.kind, m.id, m.revision) for m in target.members} == {
        ("item", "pi_1", "h1"), ("learning_object", "lo_1", None), ("facet", "f_1", None)}
    assert (target.unit, target.action_kind, target.action_id, target.horizon, target.anchor_kind,
            target.anchor_id) == ("binary", "serve", "pp_1", "plan_presentation", "plan_presentation", "pp_1")
    assert target.event_version == "unassisted_success@unversioned"
    assert snapshot["target"]["stated_by"] == "writer"
    assert snapshot["target"]["unversioned"] == ["event_version", "resolver_version"]
    assert snapshot["cutoff"]["cutoff"] is None and "does not state" in snapshot["cutoff"]["absent"]
    assert row["forecast"]["distribution"]["outcomes"] == {"event": 0.25, "not_event": 0.75}


@pytest.mark.parametrize(("as_of", "status", "recorded"), [
    ("2026-10-12T08:59:59Z", "exact", "2026-10-12T08:59:59Z"),
    (None, "unknown", ISSUED),
    ("", "unknown", ISSUED),
    ("2026-10-12T09:00:01Z", "invalid", ISSUED),
])
def test_an_unknown_or_invalid_inputs_time_is_named_beside_the_clamp(repository, as_of, status, recorded):
    """The clamp keeps replacing a missing or future time with the issue time (existing readers read it); the
    original and its validity sit beside it, so the replaced time is never read as stated."""

    FR.record_receipts(repository, [_receipt(inputs_as_of=as_of)], created_at=ISSUED)
    [row] = _stored(repository)
    assert row["inputs_as_of"] == recorded
    assert row["versions"]["snapshot"]["cutoff"]["inputs_as_of"] == {
        "original": as_of, "recorded": recorded, "status": status}


@pytest.mark.xfail(strict=True, reason="an unreadable inputs_as_of makes the clamp raise and the whole batch is "
                                       "dropped; queued with the receipt repairs")
def test_an_unreadable_inputs_time_is_recorded_invalid(repository):
    FR.record_receipts(repository, [_receipt(inputs_as_of="not a time"), _receipt("k2")], created_at=ISSUED)
    found = {row["receipt_key"]: row for row in _stored(repository)}
    assert found["k1"]["versions"]["snapshot"]["cutoff"]["inputs_as_of"]["status"] == "invalid"


def test_the_status_check_of_the_unreadable_time(repository):
    """What the batch above does today: nothing is written (characterized until the repair)."""

    assert PS.as_of_status("not a time", ISSUED) == "invalid"
    assert FR.record_receipts(repository, [_receipt(inputs_as_of="not a time"), _receipt("k2")],
                              created_at=ISSUED) == []
    assert _stored(repository) == []


@pytest.mark.parametrize(("status", "reason"), [("failed", "failed"), ("refused_spend", "refused_spend")])
def test_a_failed_or_refused_forecast_is_recorded_with_its_reason(repository, status, reason):
    """A recordable failure is a receipt: no distribution, the reason in the forecast body; the binary columns
    stay as the producer wrote them."""

    receipt = _receipt(forecast={"p": None, "event": "unassisted_success", "p_categories": None}, p=None,
                       columns={"practice_item_id": "pi_1", "plan_presentation_id": "pp_1", "status": status,
                                "received_at": ISSUED})
    assert FR.record_receipts(repository, [receipt], created_at=ISSUED)
    [row] = _stored(repository)
    assert row["status"] == status and row["p"] is None
    assert row["forecast"]["reason"] == reason
    assert row["forecast"]["distribution"] == {"unit": "binary", "event": "unassisted_success", "outcomes": None,
                                               "event_outcomes": [], "reason": reason}
    assert row["forecast"]["p"] is None


def test_an_unbound_forecast_keeps_its_censor_reason_in_the_snapshot(repository):
    receipt = _receipt(binding_kind=FR.NO_BINDING, columns={"practice_item_id": "pi_1",
                                                            "censor_reason": "no_exact_binding"})
    assert FR.record_receipts(repository, [receipt], created_at=ISSUED)
    [row] = _stored(repository)
    assert row["binding_kind"] == "none"
    assert row["versions"]["snapshot"]["binding"] == {"kind": "none", "censor_reason": "no_exact_binding"}
    assert row["forecast"]["distribution"]["outcomes"] == {"event": 0.25, "not_event": 0.75}


def test_where_no_receipt_can_be_persisted_nothing_is_forced(repository, tmp_path):
    """A read-only repository, a database without the table, the kill switch and an invalid receipt write
    nothing: the snapshot never opens another way in."""

    read_only = Repository.attach(repository.sqlite_path, read_only=True)
    assert FR.record_receipts(read_only, [_receipt()], created_at=ISSUED) == []
    off = SimpleNamespace(config=SimpleNamespace(diagnosis=SimpleNamespace(forecast_receipts=False)))
    assert FR.record_receipts(repository, [_receipt()], vault=off, created_at=ISSUED) == []
    assert FR.record_receipts(repository, [_receipt(kind="no_such_kind")], created_at=ISSUED) == []
    assert _stored(repository) == []
    bare = tmp_path / "bare.sqlite"
    sqlite3.connect(bare).close()
    assert FR.record_receipts(Repository.attach(bare), [_receipt()], created_at=ISSUED) == []


def test_a_snapshot_that_cannot_be_built_never_costs_the_receipt(repository, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("snapshot")

    monkeypatch.setattr(PS, "snapshot", broken)
    receipt = _receipt()
    assert FR.record_receipts(repository, [receipt], created_at=ISSUED)
    [row] = _stored(repository)
    assert row["versions"]["snapshot"] == {"schema": PS.SNAPSHOT_SCHEMA, "error": "RuntimeError"}
    assert row["forecast"] == dict(receipt.forecast) and row["p"] == 0.25


def test_writes_are_idempotent_and_roll_back_with_their_transaction(repository):
    first = FR.record_receipts(repository, [_receipt()], created_at=ISSUED)
    assert len(first) == 1
    before = table_rows(repository.sqlite_path, "forecast_receipts")
    assert FR.record_receipts(repository, [_receipt(snapshot=PS.SnapshotParts(cutoff=Cutoff.current()))],
                              created_at="2026-10-12T10:00:00Z") == []
    assert table_rows(repository.sqlite_path, "forecast_receipts") == before
    with pytest.raises(RuntimeError):
        with repository.atomic():
            assert FR.record_receipts(repository, [_receipt("k_rolled_back")], created_at=ISSUED)
            raise RuntimeError("the decision failed")
    assert [row["receipt_key"] for row in _stored(repository)] == ["k1"]


# -- adaptive difficulty's threshold receipts: the category probabilities -----------------------------------------


def test_threshold_receipts_store_categories_whose_category_two_is_the_binary_value(tmp_path, monkeypatch):
    """Each ``ad_threshold@*`` receipt's categories sum to one and category 2 is ``p̄`` itself: at the exact
    view, item spec, warmth and weights the serve used, ``predict`` gives the stored categories' category 2 to
    the bit, in every mixture variant (the bank's weights, the uniform-sharing restriction, the LO view's single
    point), on the first serve's prior state and on a state the first answer moved; the stored ``p`` and
    ``p_band`` are the roundings they always were."""

    calls: list = []
    computed = PR.category_mixture

    def recording(view, spec, *, warmth=0.0, weights=None):
        result = computed(view, spec, warmth=warmth, weights=weights)
        calls.append((view, spec, warmth, weights, result))
        return result

    monkeypatch.setattr(PR, "category_mixture", recording)
    checked: list = []

    def check(paths, step):
        stored = {row["forecaster"]: row for row in receipts(paths.sqlite_path)
                  if row["plan_presentation_id"] == step["presentation_id"]}
        assert len(calls) == 3
        for name, (view, spec, warmth, weights, categories) in zip(THRESHOLDS, calls, strict=True):
            prediction = PR.predict(view, spec, warmth=warmth, weights=weights)
            assert categories[2] == prediction.p_bar
            assert math.isclose(sum(categories), 1.0, rel_tol=0.0, abs_tol=1e-12)
            forecast = stored[name]["forecast"]
            assert [forecast["p_categories"][k] for k in ("0", "1", "2")] == list(categories)
            assert forecast["p"] == round(prediction.p_bar, 8) and stored[name]["p"] == prediction.p_bar
            assert forecast["p_band"] == round(prediction.p_band, 8)
            assert forecast["distribution"]["outcomes"] == forecast["p_categories"]
            assert forecast["distribution"]["event_outcomes"] == ["2"]
            checked.append((name, view.bank.P, weights is None))
        calls.clear()

    journey(tmp_path / "run", monkeypatch, before_answer=check)
    assert len(checked) == 6
    # The subject grid is a mixture of several points; the LO view is one.
    assert {points for name, points, _ in checked if name != "ad_threshold@lo"} != {1}
    assert {points for name, points, _ in checked if name == "ad_threshold@lo"} == {1}


def test_threshold_and_in_process_receipts_state_their_cutoff_target_and_provenance(tmp_path, monkeypatch):
    run = journey(tmp_path / "run", monkeypatch)
    step = run["served"][0]
    vault = load_vault(run["paths"].root)
    item = vault.practice_items[step["practice_item_id"]]
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    stored = {row["forecaster"]: row for row in receipts(run["paths"].sqlite_path)
              if row["plan_presentation_id"] == step["presentation_id"]}
    assert set(THRESHOLDS) | {"mastery_ekf", "lo_general+composite"} <= set(stored)
    for name, row in stored.items():
        snapshot = row["versions"]["snapshot"]
        target = PredictionTarget.from_dict(snapshot["target"]["target"])
        assert snapshot["target"]["stated_by"] == "producer"
        assert ("item", item.id, item_revision(item)[0]) in {(m.kind, m.id, m.revision) for m in target.members}
        assert {m.kind for m in target.members} == {"item", "learning_object", "surface_group", "facet"}
        assert (target.anchor_kind, target.anchor_id) == ("plan_presentation", step["presentation_id"])
        cutoff = Cutoff.from_dict(snapshot["cutoff"]["cutoff"])
        expected = {"mastery_ekf": "current", "lo_general+composite": "completed_by"}.get(name, "ad_replay")
        assert cutoff.preset == expected
        assert snapshot["cutoff"]["inputs_as_of"]["status"] == "exact"
    threshold = stored["ad_threshold@subject"]["versions"]["snapshot"]
    assert threshold["cutoff"]["source"]["ad_state_hash"] == stored["ad_threshold@subject"]["inputs"]["state_hash"]
    assert threshold["cutoff"]["source"]["item_serve_inputs"] == f"plan_presentation:{step['presentation_id']}"
    assert threshold["provenance"]["likelihood"]["source"] == "adaptive_difficulty.model.category_probabilities"
    assert threshold["provenance"]["mixture"] == "bank"
    assert stored["ad_threshold@subject_uniform"]["versions"]["snapshot"]["provenance"]["mixture"] == "uniform"


# -- non-interference ----------------------------------------------------------------------------------------------


def test_snapshots_move_no_id_seed_digest_score_or_state_under_a_frozen_clock(tmp_path, monkeypatch):
    """Two copies of one journey, the second with the enrichment as the identity: every row of every table is
    identical (ids, router decisions and their seeds, AD selections, ``item_serve_inputs`` with its ``z_v1``,
    AD state and trace, the forecast scores) except the keys this part adds to receipts' bodies and the
    threshold receipts' categories. The receipts written are the same rows with the same keys, ``p``,
    ``inputs_hash`` and ids: the id stream after every receipt is consumed exactly as before."""

    with_snapshots = journey(tmp_path / "with", monkeypatch)
    without = journey(tmp_path / "without", monkeypatch, snapshots=False)
    new, old = comparable(with_snapshots["paths"].sqlite_path), comparable(without["paths"].sqlite_path)
    assert new.keys() == old.keys()
    assert {table for table in new if new[table] != old[table]} == set()
    new_receipts = receipts(with_snapshots["paths"].sqlite_path)
    old_receipts = receipts(without["paths"].sqlite_path)
    assert [(r["id"], r["receipt_key"], r["p"], r["inputs_hash"]) for r in new_receipts] == [
        (r["id"], r["receipt_key"], r["p"], r["inputs_hash"]) for r in old_receipts]
    assert all("snapshot" in r["versions"] for r in new_receipts)
    assert not any("snapshot" in r["versions"] for r in old_receipts)
    # Something was compared: receipts, frozen serve inputs with z_v1, AD state, its trace and scored forecasts.
    for table in ("forecast_receipts", "item_serve_inputs", "ad_state", "ad_attempt_trace", "item_forecast_scores",
                  "plan_presentations"):
        assert new[table], table
    assert any("z_v1" in row for row in new["item_serve_inputs"])
    assert any('"status": "scored"' in row for row in new["item_forecast_scores"])


# -- the material view -------------------------------------------------------------------------------------------


def test_a_protected_revision_withholds_the_receipts_whose_snapshot_names_it(tmp_path, monkeypatch):
    """A receipt whose snapshot names a revision (or facet) the view withholds is withheld with it, while the
    same row without a snapshot (every receipt before this part) is judged by its columns as before; an
    unreadable snapshot is withheld (fail closed)."""

    run = journey(tmp_path / "run", monkeypatch)
    paths, step = run["paths"], run["served"][0]
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    revision = item_revision(vault.practice_items[step["practice_item_id"]])[0]
    with closing(connect(paths.sqlite_path)) as connection:
        rows = [row for row in store.list_receipts(connection, kind=FR.ITEM_UNASSISTED_SUCCESS)
                if row["plan_presentation_id"] == step["presentation_id"]]
        assert len(rows) == 5
        view = material_view(vault, repository)
        assert len(view.filter(connection, "forecast_receipts", rows)) == 5
        # The same rows judged by the snapshot alone (no column naming the item or the presentation), with and
        # without a snapshot: only the snapshot's members can withhold these.
        bare = [{**row, "practice_item_id": None, "plan_presentation_id": None} for row in rows]
        old_shape = [{**row, "versions": {k: v for k, v in row["versions"].items() if k != "snapshot"}}
                     for row in bare]
        monkeypatch.setattr(view, "revision_hash_withheld", lambda _connection, value: value == revision)
        assert view.filter(connection, "forecast_receipts", rows) == []
        assert view.filter(connection, "forecast_receipts", bare) == []
        assert len(view.filter(connection, "forecast_receipts", old_shape)) == 5

        fresh = material_view(vault, repository)
        # The epoch digests the protection: read it first, so the rows stay current and only the rule is tested.
        assert fresh.epoch == view.epoch
        facet = next(m["id"] for m in rows[0]["versions"]["snapshot"]["target"]["target"]["members"]
                     if m["kind"] == "facet")
        monkeypatch.setattr(fresh, "protected_only_facets", lambda _connection=None: {facet})
        assert fresh.filter(connection, "forecast_receipts", rows) == []
        assert fresh.filter(connection, "forecast_receipts", bare) == []
        assert len(fresh.filter(connection, "forecast_receipts", old_shape)) == 5

        unreadable = [{**rows[0], "versions": {**rows[0]["versions"], "snapshot": {"target": {"target": 7}}}}]
        assert material_view(vault, repository).filter(connection, "forecast_receipts", unreadable) == []


# -- the native VOI writer ---------------------------------------------------------------------------------------


def test_voi_forecasts_carry_the_snapshot_in_their_own_versions(repository):
    body = {"eig_nats": 0.5, "p_action_change": 0.25, "predicted_outcomes": {"pass": 0.7, "fail": 0.3},
            "forecast_of": "nominal_best", "chosen_ref": "cand_1", "verdict": "stop"}
    forecast_id = VF.record_forecast(repository, site="probe_selection", receipt_key="probe_selection:x",
                                     verdict="stop", forecast=body, parameters=[], learning_object_id="lo_1",
                                     chosen_practice_item_id="pi_1", presentation_id="pp_1")
    assert forecast_id is not None
    from learnloop.db.stores import voi_forecasts as voi_store

    with closing(connect(repository.sqlite_path)) as connection:
        [row] = voi_store.list_forecasts(connection)
    assert row["forecast"] == body and row["receipt_key"] == "probe_selection:x" and row["id"] == forecast_id
    snapshot = row["versions"]["snapshot"]
    assert {k: v for k, v in row["versions"].items() if k != "snapshot"} == {
        "forecast_version": VF.FORECAST_VERSION, "evsi_schema_version": VF.EV.EVSI_SCHEMA_VERSION,
        "loss_table_version": VF.AL.LOSS_TABLE_VERSION}
    target = PredictionTarget.from_dict(snapshot["target"]["target"])
    assert snapshot["target"]["target_hash"] == target.target_hash()
    assert {(m.kind, m.id) for m in target.members} == {("item", "pi_1"), ("learning_object", "lo_1")}
    assert (target.anchor_kind, target.anchor_id, target.action_id) == ("presentation", "pp_1", "cand_1")
    # The ranking's nominal best, never administered: its forecast is kept and marked so.
    assert snapshot["distribution"]["outcomes"] == {"pass": 0.7, "fail": 0.3}
    assert snapshot["distribution"]["administered"] is False
    assert snapshot["cutoff"]["cutoff"] is None and snapshot["cutoff"]["absent"]
