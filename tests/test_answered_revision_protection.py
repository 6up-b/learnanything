"""Review round 3, class 1: one reader of "which revision did this attempt answer" (``db.stores.answered_revision``)
for the protection view, the grade-time forecaster and its receipt writer. Fakes only; no network, no model call."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_contract_helpers import EXT, LO, T0, _attempt, _base, _hold_out, _iso
from tests.ad23_fakes import SEEDED


def _grade_receipts(paths, attempt_id: str) -> list[tuple]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT receipt_key, item_content_hash, versions_json FROM forecast_receipts "
            "WHERE kind = 'item_unassisted_success_at_grade' AND source_attempt_id = ?", (attempt_id,))]


def test_a_plan_answer_to_a_held_out_served_revision_writes_no_grade_receipt(tmp_path, monkeypatch):
    """FR3-2 (H3-R24/R25): ``pi_hist`` is served at R1, cut from held-out material, then replaced by its public R2; the
    answer names the presentation and no contract. It keeps its link, and the receipt table holds nothing for it: no
    forecast, no snapshot, no hash of either revision (failed before: the R2 forecast and its snapshot were stored)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.vault.models import CanonicalExercise

    paths = _base(tmp_path)
    _hold_out(monkeypatch)
    served = load_vault(paths.root).practice_items["pi_hist"].model_copy(update={
        "prompt": "SENTINEL_HIST_FR3: the held-out revision served by the plan.",
        "canonical_exercise": CanonicalExercise(source_id="src_r9", extraction_id=EXT, span_ids=["h3"])})
    content_hash, item_json = item_revision(served)
    at = T0 - timedelta(hours=1)
    with closing(connect(paths.sqlite_path)) as connection:
        (block_id,) = connection.execute("SELECT id FROM attention_blocks ORDER BY rowid LIMIT 1").fetchone()
        connection.execute("INSERT INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                           "VALUES (?, 'pi_hist', ?, ?)", (content_hash, item_json, _iso(at)))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_fr3', ?, 'pi_hist', 'chooser', ?)", (block_id, _iso(at)))
        connection.execute(
            "INSERT INTO item_serve_inputs(id, receipt_key, presentation_kind, plan_presentation_id, practice_item_id, "
            "learning_object_id, content_hash, served_at, audit_json, signals_json, pre_exposed, resolution_version, "
            "created_at, protection_epoch) VALUES ('isi_fr3', 'plan_presentation:pp_fr3', 'plan_presentation', "
            f"'pp_fr3', 'pi_hist', ?, ?, ?, '{{}}', '{{}}', 0, 'r9', ?, '{SEEDED}')",
            (LO, content_hash, _iso(at), _iso(at)))
        connection.commit()
    attempt = _attempt(paths, "pi_hist", at=T0 - timedelta(minutes=50), latency=90, presentation_id="pp_fr3")
    assert Repository(paths.sqlite_path).fetch_practice_attempt(attempt)["plan_presentation_id"] == "pp_fr3"
    assert _grade_receipts(paths, attempt) == []
    # A public answer graded the same way, beside it, still gets its receipt: the gate is the revision, not the door.
    public = _attempt(paths, "pi_p1", at=T0 - timedelta(minutes=40), latency=90)
    assert len(_grade_receipts(paths, public)) == 1
    assert json.loads(_grade_receipts(paths, public)[0][2])["snapshot"]


def test_a_presentation_after_a_grade_froze_its_contract_saves_the_revision_it_showed(tmp_path):
    """FR3-14 (H3-R25's next presentation): a grade froze the contract of R1 first (citing, not saving, the revision);
    the learner is then shown R1, the item is edited to R2, and the answer on R1's contract is forecast at R1, exactly
    as in a copy where no grade came first (failed before: the presentation found the contract and saved nothing, so
    the forecast was lost)."""

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.clock import FrozenClock
    from learnloop.learner.assessment_contracts import snapshot_for_presentation
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.hashes import item_revision

    from tests.helpers import NOW, create_placement_vault

    def run(root, *, graded_first: bool):
        paths = create_placement_vault(root, version="mvp-0.75")
        vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
        sync_vault_state(vault, repo, clock=FrozenClock(NOW))
        item = vault.practice_items["pi_eig_mid"]
        if graded_first:
            complete_self_graded_attempt(vault, repo, AttemptDraft(item.id, "first"), SelfGradeInput({"correctness": 2}, 3),
                                         clock=FrozenClock(NOW))
        contract = snapshot_for_presentation(repo, vault, item, clock=FrozenClock(NOW + timedelta(minutes=1)))
        vault.practice_items[item.id] = item.model_copy(update={"prompt": "Edited before the answer."})
        result = complete_self_graded_attempt(vault, repo, AttemptDraft(item.id, "answer",
            assessment_contract_version_id=contract), SelfGradeInput({"correctness": 3}, 3),
            clock=FrozenClock(NOW + timedelta(minutes=2)))
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            saved = [tuple(row) for row in connection.execute(
                "SELECT content_hash, item_json, created_at FROM practice_item_snapshots WHERE practice_item_id = ?",
                (item.id,))]
            receipt = connection.execute("SELECT item_content_hash FROM forecast_receipts WHERE source_attempt_id = ? "
                                         "AND kind = 'item_unassisted_success_at_grade'", (result.attempt_id,)).fetchone()
        return item_revision(item)[0], saved, receipt

    shown, saved, receipt = run(tmp_path / "graded_first", graded_first=True)
    alone_shown, alone_saved, alone_receipt = run(tmp_path / "alone", graded_first=False)
    assert shown == alone_shown and saved == alone_saved and [row[0] for row in saved] == [shown]
    assert receipt is not None and receipt[0] == shown and alone_receipt == receipt


@pytest.mark.parametrize("tag", ["mvp-0.75", "mvp-0.76"])
def test_a_later_held_out_grade_does_not_change_an_unrelated_public_answers_forecast(tmp_path, monkeypatch, tag):
    """FR3-5's protection half, at every tag: the grade-time forecast's later-evidence guard reads only what adaptive
    difficulty may see. A held-out item's answer recorded after a public answer's time (its grade is newer than every
    public one) leaves the public answer's grade-time forecast exactly as in a copy without the held-out answer
    (failed before: the guard read the newest raw grade of any item, held-out included, so the public answer got no
    forecast and read mastery)."""

    from tests.ad23_contract_helpers import _copy_item
    from tests.helpers import set_algorithm_version

    def run(root, *, protected: bool):
        paths = _base(root)
        set_algorithm_version(paths, tag)
        _copy_item(paths, "pi_p1", "pi_held_fr3", canonical_exercise={
            "source_id": "src_r9", "extraction_id": EXT, "span_ids": ["h1"]})
        if protected:
            _attempt(paths, "pi_held_fr3", at=T0 + timedelta(hours=1), latency=90)
        public = _attempt(paths, "pi_p1", at=T0 - timedelta(minutes=40), latency=90)
        rows = _grade_receipts(paths, public)
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            (dist,) = connection.execute("SELECT predicted_score_dist_json FROM attempt_surprise WHERE attempt_id = ?",
                                         (public,)).fetchone()
        dist = json.loads(dist)
        return ([(json.loads(versions)["snapshot"] is not None, content_hash) for _key, content_hash, versions in rows],
                dist["prediction_source"], dist.get("p_ad"))

    _hold_out(monkeypatch)
    absent = run(tmp_path / "absent", protected=False)
    assert absent[1] == "grade_receipt" and len(absent[0]) == 1
    assert run(tmp_path / "protected", protected=True) == absent
