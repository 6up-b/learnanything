from datetime import timedelta

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores.ad_serving import insert_selection
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from tests.difficulty_replay_helpers import _iso, _serve
from tests.helpers import NOW, create_placement_vault
from tests.test_surprise_reads_ad_forecast import _surprise


@pytest.mark.parametrize("version", ["mvp-0.73", "mvp-0.74"])
def test_selection_view_and_missing_selection_live_and_rebuilt(tmp_path, monkeypatch, version):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=FrozenClock(NOW))
    item = vault.practice_items["pi_eig_mid"]
    from learnloop.adaptive_difficulty import serve

    write_receipts = serve.record_receipts

    def without_selected(repository, rows, **kwargs):
        return write_receipts(repository, [r for r in rows if r.forecaster != "ad_threshold_repeat@lo"], **kwargs)

    expected = {}
    for i, selected in enumerate(("lo", "subject", "lo", None, "mismatch", "missing_receipt")):
        at = NOW + timedelta(days=i)
        if selected:
            block = f"blk_h3_{i}"
            with repo.connection() as conn:
                insert_selection(conn, dict(kind="serve", block_id=block, slot_position=1,
                    decision_key=f"serve:{block}:1", view="subject" if selected == "subject" else
                    f"lo:{item.learning_object_id}", learning_object_id=item.learning_object_id,
                    chosen_item_id=item.id, mode="band", support=([{"ref": item.id, "p_bar": 0.0}]
                        if selected == "mismatch" else []), excluded=[], constants={}, versions={},
                    seed="seed", state_hash="state", algorithm_version=version, created_at=_iso(at)))
                conn.commit()
        if selected == "missing_receipt":
            monkeypatch.setattr(serve, "record_receipts", without_selected)
        presentation = _serve(vault, repo, item.id, i, at)
        result = complete_self_graded_attempt(vault, repo, AttemptDraft(item.id, "answer", plan_presentation_id=presentation),
            SelfGradeInput({"correctness": 2}, 4), clock=FrozenClock(at + timedelta(seconds=1)))
        view = "subject" if version == "mvp-0.73" else (None if selected in ("mismatch", "missing_receipt") else selected)
        name = ("ad_threshold_repeat@" if i else "ad_threshold@") + view if view else None
        expected[result.attempt_id] = name
    live = _surprise(repo)
    for attempt_id, name in expected.items():
        dist = live[attempt_id]["dist"]
        assert dist["prediction_source"] == ("serve_receipt" if name else "mastery")
        if name:
            assert dist["receipt_key"].endswith(":" + name)
    rebuild_all_derived_state(vault, repo)
    assert _surprise(repo) == live


@pytest.mark.parametrize("version", ["mvp-0.73", "mvp-0.74"])
def test_another_sessions_presentation_is_left_for_its_answer(tmp_path, version):
    paths = create_placement_vault(tmp_path / "vault", version=version)
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=FrozenClock(NOW))
    owner, stranger = repo.create_session(), repo.create_session()
    item_id = "pi_eig_mid"
    with repo.connection() as conn:
        conn.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                     "VALUES ('block', 'practice', 10, 'hash', ?)", (_iso(NOW),))
        conn.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at, session_id) "
                     "VALUES ('served', 'block', ?, 'chooser', ?, ?)", (item_id, _iso(NOW), owner))
        conn.commit()
    result = complete_self_graded_attempt(vault, repo, AttemptDraft(item_id, "answer", session_id=stranger,
        plan_presentation_id="served"), SelfGradeInput({"correctness": 3}, 3), clock=FrozenClock(NOW))
    assert repo.fetch_practice_attempt(result.attempt_id)["plan_presentation_id"] == ("served" if version == "mvp-0.73" else None)
    source = "grade_receipt" if version == "mvp-0.73" else "mastery"
    assert _surprise(repo)[result.attempt_id]["dist"]["prediction_source"] == source
    rebuild_all_derived_state(vault, repo)
    assert _surprise(repo)[result.attempt_id]["dist"]["prediction_source"] == source


@pytest.mark.parametrize("version", ["mvp-0.73", "mvp-0.74"])
def test_grade_uses_the_revision_frozen_on_open(tmp_path, version):
    import json
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    paths = create_placement_vault(tmp_path / "vault", version=version)
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=FrozenClock(NOW))
    item = vault.practice_items["pi_eig_mid"]
    frozen = snapshot_for_presentation(repo, vault, item)
    vault.practice_items[item.id] = item.model_copy(update={"prompt": "Edited after opening."})
    result = complete_self_graded_attempt(vault, repo, AttemptDraft(item.id, "answer",
        assessment_contract_version_id=frozen), SelfGradeInput({"correctness": 3}, 3), clock=FrozenClock(NOW))
    with repo.connection() as conn:
        versions = json.loads(conn.execute("SELECT versions_json FROM forecast_receipts WHERE source_attempt_id = ?",
                                          (result.attempt_id,)).fetchone()[0])
    members = versions["snapshot"]["target"]["target"]["members"]
    assert next(m["revision"] for m in members if m["kind"] == "item") == item_revision(
        item if version == "mvp-0.74" else vault.practice_items[item.id])[0]


def test_upgrade_rejects_a_historical_serve_at_a_different_revision(tmp_path):
    from tests.helpers import set_algorithm_version

    paths = create_placement_vault(tmp_path / "old", version="mvp-0.73")
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=FrozenClock(NOW))
    item = vault.practice_items["pi_eig_mid"]
    with repo.connection() as conn:
        insert_selection(conn, dict(kind="serve", block_id="blk_h3_0", slot_position=1,
            decision_key="serve:blk_h3_0:1", view="subject", chosen_item_id=item.id,
            learning_object_id=item.learning_object_id, mode="band", support=[], excluded=[], constants={},
            versions={}, seed="seed", state_hash="state", algorithm_version="mvp-0.73", created_at=_iso(NOW)))
        conn.commit()
    presentation = _serve(vault, repo, item.id, 0, NOW)
    vault.practice_items[item.id] = item.model_copy(update={"prompt": "A different revision."})
    result = complete_self_graded_attempt(vault, repo, AttemptDraft(item.id, "answer", plan_presentation_id=presentation),
        SelfGradeInput({"correctness": 2}, 3), clock=FrozenClock(NOW + timedelta(seconds=1)))
    assert _surprise(repo)[result.attempt_id]["dist"]["prediction_source"] == "serve_receipt"
    set_algorithm_version(paths, "mvp-0.74")
    rebuild_all_derived_state(load_vault(paths.root), repo)
    assert _surprise(repo)[result.attempt_id]["dist"]["prediction_source"] == "mastery"


@pytest.mark.parametrize("promoted", [False, True])
def test_surprise_uses_the_probability_from_the_actual_plan_draw(tmp_path, promoted):
    from learnloop.daily_plan.engine import advance, build_plan
    from tests.ad23_fakes import ad23_vault, answer, env_for, selections

    items = ("pi_h", "pi_e1", "pi_e2")
    paths = ad23_vault(tmp_path, items=items, ad=f"promoted_predictor = {str(promoted).lower()}\n",
                       config="[router]\nenabled = false\n")
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=3, remembered=3, minutes_source="chip")
    _, step = advance(env, serve=True)
    (draw,) = selections(paths, kind="serve")
    item = step["practice_item_id"]
    chosen = next(row for row in draw["support"] if row["ref"] == item)
    attempt_id = answer(paths, item, presentation_id=step["presentation_id"], clock=clock)
    live = _surprise(env.repository)
    dist = live[attempt_id]["dist"]
    assert dist["prediction_source"] == "serve_receipt"
    assert dist["receipt_key"].endswith("@subject" if promoted else "@lo")
    assert round(dist["p_ad"], 12) == chosen["p_bar"]
    rebuild_all_derived_state(env.vault, env.repository)
    assert _surprise(env.repository) == live
