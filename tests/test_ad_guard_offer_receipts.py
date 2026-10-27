"""The AD guard and the incumbent's serving receipts (owner-vault upgrade blocker, 2026-10-27).

An attempt served from a scheduler slate candidate that is not a forced follow-up makes field's
serving attribution (``field.outcomes._serving``) read ``scheduler_offer_receipts`` to label a
learner pick. That read runs inside the AD material view's rules (``MaterialView.field_rows``),
where an unclassified table is refused: before this fix every AD operation over such a vault was
poisoned (AD silently unavailable at serving, ``ad report`` and ``rebuild-derived-state`` failed,
and the mvp-0.35 upgrade chain stopped in its rebuild). The table is the incumbent scheduler's
serving receipt, classified DENIED beside ``scheduler_slate_candidates`` and
``submission_intents``: the rules read it, nothing else inside an operation does.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing, suppress

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import ad23_vault, answer

ITEM = "pi_e1"
AT = "2026-10-01T09:00:00Z"


@pytest.fixture
def observed(monkeypatch):
    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    return seen


def seed_learner_pick(paths, attempt_id: str, item_id: str = ITEM, *, offered: bool = True,
                      components: dict | None = None, tag: str = "") -> str:
    """Bind ``attempt_id`` to a scheduler slate candidate the learner picked from a published offer
    (the shape the owner's probability vault holds): a slate, its candidate (no forced follow-up
    component unless ``components`` says so), the offer receipt (when ``offered``), the submission
    intent naming the candidate, and the attempt's own receipts."""

    slate, candidate, submission = f"slate{tag}", f"cand-{attempt_id}", f"sub-{attempt_id}"
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT OR IGNORE INTO sessions(id, started_at) VALUES ('s1', ?)", (AT,))
        connection.execute(
            "INSERT OR IGNORE INTO scheduler_slates(id, generated_at, selection_policy, session_context_json, "
            "config_snapshot_json, algorithm_version, created_at, updated_at) "
            "VALUES (?, ?, 'policy', '{}', '{}', 'test', ?, ?)", (slate, AT, AT, AT))
        connection.execute(
            "INSERT INTO scheduler_slate_candidates(id, slate_id, practice_item_id, rank, selected_mode, priority, "
            "components_json, algorithm_version, created_at, selection_propensity, was_returned, returned_rank) "
            "VALUES (?, ?, ?, 1, 'practice', 1, ?, 'test', ?, .25, 1, 1)",
            (candidate, slate, item_id, json.dumps(components or {}), AT))
        if offered:
            connection.execute(
                "INSERT INTO scheduler_offer_receipts VALUES (?, ?, 'desktop_queue', 'learnloop-events-v1', ?)",
                (slate, json.dumps([candidate]), AT))
        connection.execute(
            "INSERT INTO submission_intents(submission_id, session_id, practice_item_id, scheduler_candidate_id, "
            "entry_surface, created_at) VALUES (?, 's1', ?, ?, 'desktop_practice', ?)",
            (submission, item_id, candidate, AT))
        connection.execute(
            "UPDATE practice_attempts SET submission_id = ?, scheduler_candidate_id = ?, scheduler_slate_id = ?, "
            "collection_version = 'learnloop-events-v1' WHERE id = ?", (submission, candidate, slate, attempt_id))
        connection.commit()
    return candidate


def _picked_vault(tmp_path, *, version: str | None = None):
    kwargs = {"version": version} if version else {}
    paths = ad23_vault(tmp_path, items=(ITEM, "pi_e2"), **kwargs)
    picked = answer(paths, ITEM)
    seed_learner_pick(paths, picked)
    answer(paths, "pi_e2", correct=False)
    return paths, picked


def _denials(observed) -> list[dict]:
    return [denial for op in observed for denial in op.guard.denials]


def test_rebuild_derived_state_over_a_learner_pick_runs_with_zero_denials(tmp_path, observed):
    """The upgrade chain's step (``rebuild_all_derived_state`` -> ``rebuild_ad_state`` ->
    ``load_events`` -> ``field_rows`` -> ``_serving``'s offer read). Failed before: ``ViewDenied``
    ('denied', 'DatabaseError') from the read of the unclassified ``scheduler_offer_receipts``."""

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, picked = _picked_vault(tmp_path)
    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path))
    assert _denials(observed) == []
    assert O.denial_count(paths.sqlite_path) == 0
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_state").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM ad_attempt_trace WHERE attempt_id = ?",
                                  (picked,)).fetchone()[0] >= 1


def test_the_view_labels_the_pick_as_field_does_outside_ad(tmp_path, observed):
    """Inside the operation the rules read the receipt, so AD's rows carry field's own label
    (``learner_pick``), the same as field's loader outside any operation."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.db.connection import connect
    from learnloop.field.outcomes import load_attempt_rows

    paths, picked = _picked_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        outside = {row.attempt_id: row.serving_origin for row in load_attempt_rows(connection, vault)}
    with O.ad_operation(vault, repository, read_only=True) as op:
        inside = {row.attempt_id: row.serving_origin
                  for row in material_view(op.vault, op.repository).field_rows(repository.connection())}
    assert outside[picked] == "learner_pick"
    assert inside == outside
    assert _denials(observed) == []


def test_the_serving_snapshot_and_the_report_run_with_zero_denials(tmp_path, observed):
    """The live paths: the serve's replay snapshot (AD unavailable before, so the incumbent served)
    and ``ad report`` (crashed before)."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.report import build
    from learnloop.db.connection import connect

    paths, picked = _picked_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    snap = RP.snapshot(vault, repository)
    assert any(event.attempt_id == picked for event in snap.events.attempts)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = build(vault, repository, connection, sensitivity=False)
    assert report["guard"]["denials"] == 0, report["guard"]
    assert _denials(observed) == []


def test_the_receipt_stays_refused_outside_the_rules(tmp_path):
    """Classified, not opened: a raw read inside an operation outside the rules is refused and
    poisons it (DENIED, the incumbent's scheduling state, as its slate candidates are)."""

    from learnloop.adaptive_difficulty import protected_tables as T

    assert T.ROLES["scheduler_offer_receipts"] == T.DENIED == T.ROLES["scheduler_slate_candidates"]
    paths, _picked = _picked_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    with repository.atomic():
        connection = repository.connection()
        with suppress(O.OperationPoisoned), O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match="not authorized|is prohibited"):
                connection.execute("SELECT slate_id FROM scheduler_offer_receipts").fetchall()


# -- Codex review F1: the serving change on the affected shape, and its per-vault rollback ---------


HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
SERVED = ("pi_h", "pi_e1", "pi_e2", "pi_e3")


def _served_over_a_pick(tmp_path, name: str, *, ad: str = "") -> list:
    """The plan's served steps, its records and AD's draws on a vault holding the affected shape
    (an earlier answer picked from a published offer), with a hard slot AD substitutes when it can."""

    from learnloop.daily_plan.engine import advance, build_plan, day_records

    from tests.ad23_fakes import env_for, selections

    paths = ad23_vault(tmp_path / name, items=SERVED, features={"pi_h": HARD}, ad=ad,
                       config="[router]\nenabled = false\n")
    seed_learner_pick(paths, answer(paths, "pi_e3"), "pi_e3")
    env, clock = env_for(paths, items=SERVED)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    sequence = []
    for _ in range(4):
        _record, step = advance(env, serve=True)
        sequence.append({key: step.get(key) for key in ("kind", "practice_item_id", "learning_object_id", "position")})
        if step["kind"] != "item":
            break
        clock.advance(2)
        answer(paths, step["practice_item_id"], presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    records = [{"blocks": [[(i.practice_item_id, i.est_minutes, i.position, i.displaced_reason) for i in b.items]
                           for b in r.blocks], "status": r.status} for r in day_records(env)]
    return [sequence, records, selections(paths)]


def test_the_fix_changes_serving_on_the_affected_shape_and_the_switches_restore_the_refusal_state(
        tmp_path, monkeypatch, observed):
    """F1 reproduced: before the fix (the table unclassified) every AD operation over this vault was
    poisoned, so the incumbent served every slot and AD drew nothing; with the fix AD draws under the
    same tag. The vault's own AD2+AD3 switches (all false) serve exactly what the refusal served,
    so the predecessor's observable serving state stays reachable per vault, without a new tag."""

    from learnloop.adaptive_difficulty import protected_tables as T
    from learnloop.adaptive_difficulty import successor as SC

    restored = _served_over_a_pick(tmp_path, "fixed")
    off = _served_over_a_pick(tmp_path, "off", ad="".join(f"{name} = false\n" for name in SC.SWITCHES))
    assert _denials(observed) == []
    with monkeypatch.context() as patched:
        patched.setattr(T, "ROLES", {table: kind for table, kind in T.ROLES.items()
                                     if table != "scheduler_offer_receipts"})
        refused = _served_over_a_pick(tmp_path, "refused")
    first = [denial for denial in _denials(observed) if denial["why"] != O.POISONED]
    assert first and {(d["table"], d["why"]) for d in first} == {("scheduler_offer_receipts", "an unclassified table")}
    assert refused[2] == [] and off[2] == []
    assert restored[2], "with the fix AD draws on the affected shape"
    assert restored[0][0]["practice_item_id"] != refused[0][0]["practice_item_id"]
    assert off[:2] == refused[:2]
