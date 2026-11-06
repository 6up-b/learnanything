"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, owner decision 5): LOs with a pending lesson delayed check join the
objective's population (an objective-definition change point), only at the tag with the switch on.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION, LESSON_OPPORTUNITY_ALGORITHM_VERSION
from learnloop.daily_plan import lesson_offer as LO
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import price as P
from learnloop.router_objective import value as V

from tests.test_ro4_value import EXACT, FIXED, _inputs, _logit

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION

# --- the population -------------------------------------------------------------------------------------------


def _pending_check_vault(tmp_path, version: str):
    """A basic vault with one closed lesson whose receipt committed a retention check (no answer) on an LO outside the
    population before it (no goal, no FSRS memory)."""

    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.vault.loader import load_vault

    from tests.helpers import create_basic_vault, set_algorithm_version
    from learnloop.vault.repository import open_vault_repository
    from learnloop.vault.paths import VaultPaths

    from learnloop.vault.yaml_io import write_yaml

    paths = create_basic_vault(tmp_path / version)
    set_algorithm_version(paths, version)
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})  # no goal scope enrols anything
    vault = load_vault(paths.root)
    repository = open_vault_repository(vault.root, VaultPaths(vault.root, vault.config).sqlite_path)
    with repository.atomic(), repository.connection() as connection:
        # No FSRS memory anywhere (nothing practised), so an LO outside every goal is enrolled by nothing but a
        # lesson's pending check.
        connection.execute("DELETE FROM practice_item_state")
    before = OI.population(vault, repository, "2026-11-06T10:00:00Z")
    lo = next(lo for lo in sorted(vault.learning_objects) if lo not in before)
    item = "pi_lesson_retention_check"  # the committed check's item (never answered here)
    with repository.atomic(), repository.connection() as connection:
        connection.execute(
            "INSERT INTO lessons (id, driver, origin, origin_ref, entry, goal_text, goal_json, learning_object_ids_json,"
            " doctrine_version, brief_version, route, model, algorithm_version, opened_at, closed_at, close_reason) "
            "VALUES ('les_1', 'desktop', 'learner_pick', NULL, 'learning_object', 'g', '{}', ?, 'd', 'b', NULL, NULL,"
            " ?, '2026-11-05T09:00:00Z', '2026-11-05T09:20:00Z', 'goal_reached')", (json.dumps([lo]), version))
        connection.execute(
            "INSERT INTO lesson_receipts (lesson_id, receipt_version, close_reason, receipt_json, created_at) "
            "VALUES ('les_1', 'r', 'goal_reached', ?, '2026-11-05T09:20:00Z')",
            (json.dumps({"delayed_checks": [{"purpose": "retention", "learning_object_id": lo, "item_id": item,
                                             "commitment_id": "cmt_1", "due": "2026-11-08"}]}),))
    return vault, repository, lo


def test_the_population_holds_los_with_a_pending_lesson_check(tmp_path):
    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.db.stores import lessons as lesson_store

    vault, repository, lo = _pending_check_vault(tmp_path, TAG)
    with repository.connection() as connection:
        pending = lesson_store.pending_delayed_checks(connection, at="2026-11-06T10:00:00Z")
        assert [entry["learning_object_id"] for entry in pending] == [lo]
        assert lesson_store.pending_delayed_checks(connection, at="2026-11-05T09:00:00Z") == []
    assert lo in OI.population(vault, repository, "2026-11-06T10:00:00Z")
    old_vault, old_repository, old_lo = _pending_check_vault(tmp_path, OLD)
    assert old_lo not in OI.population(old_vault, old_repository, "2026-11-06T10:00:00Z")


def test_the_population_change_moves_the_objectives_definition_once(tmp_path):
    from learnloop.router_objective import tail_data as TD

    goals = {}
    before = TD.objective_hash(goals, 90.0, {"lo_x": 1 / 90})
    after = TD.objective_hash(goals, 90.0, {"lo_x": 1 / 90, "lo_lesson": 1 / 90})
    assert before != after  # a change point for RO6, once (the population with the lesson's LO)



# --- switched off or below the tag: the same database valued as mvp-0.52 (every part together) ----------------
from typing import Any  # noqa: E402

from learnloop.daily_plan import lesson_suggestion as SG  # noqa: E402
from tests.router_mixture_helpers import mixture_env  # noqa: E402
from tests.router_model_fakes import fake_runtime  # noqa: E402
from tests.test_te3b_offers import _first_decision, offerable  # noqa: E402,F401

def _with(vault, *, version: str | None = None, in_objective: bool | None = None):
    """The same vault (the same database, the same pinned state) under another version or switch."""

    from dataclasses import replace

    config = vault.config.model_copy(deep=True)
    if version is not None:
        config.algorithms.algorithm_version = version
    if in_objective is not None:
        config.router.lesson_suggestions.in_objective = in_objective
    return replace(vault, config=config)


def _lesson_activity(env) -> None:
    """A closed lesson whose retention check is pending, and a lesson open now with 20 foreground minutes."""

    now = env.clock.now()
    stamp = lambda moment: moment.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    from datetime import timedelta

    with env.repository.atomic(), env.repository.connection() as connection:
        for lesson_id, opened, closed in (("les_done", now - timedelta(days=1), now - timedelta(days=1, minutes=-20)),
                                          ("les_now", now - timedelta(minutes=30), None)):
            connection.execute(
                "INSERT INTO lessons (id, driver, origin, origin_ref, entry, goal_text, goal_json, "
                "learning_object_ids_json, doctrine_version, brief_version, route, model, algorithm_version, "
                "opened_at, closed_at, close_reason) VALUES (?, 'desktop', 'learner_pick', NULL, 'learning_object', "
                "'g', '{}', '[\"lo_diag\"]', 'd', 'b', NULL, NULL, 'x', ?, ?, ?)",
                (lesson_id, stamp(opened), stamp(closed) if closed else None, "goal_reached" if closed else None))
        connection.execute(
            "INSERT INTO lesson_receipts (lesson_id, receipt_version, close_reason, receipt_json, created_at) "
            "VALUES ('les_done', 'r', 'goal_reached', ?, ?)",
            (json.dumps({"delayed_checks": [{"purpose": "retention", "learning_object_id": "lo_diag",
                                             "item_id": "pi_diag_easy", "commitment_id": "cmt_1",
                                             "due": "2099-01-01"}]}), stamp(now - timedelta(days=1, minutes=-20))))
        for seq, (offset, length) in enumerate(((0, 10), (15, 10)), start=1):
            began = now - timedelta(minutes=30 - offset)
            connection.execute(
                "INSERT INTO lesson_activity_intervals (id, lesson_id, screen_session, seq, started_at, ended_at, "
                "seconds, foreground, occurred_at, received_at, receipt_version) VALUES (?, 'les_now', 's', ?, ?, ?, ?, "
                "1, ?, ?, 'v')", (f"lai_{seq}", seq, stamp(began), stamp(began + timedelta(minutes=length)),
                                  length * 60.0, stamp(now), stamp(now)))


def test_switch_off_or_below_the_tag_values_the_same_database_as_mvp052(tmp_path, offerable, monkeypatch):
    """§24: off, or below the tag, the objective's inputs, its value and its support are mvp-0.52's on the same
    database: the same session minutes (no lesson minutes on the clock), the same population (no pending-check LO),
    the same features version and generator, no offer builder, TE1b's daily gate; on, each one moves."""

    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.daily_plan.policy import policy_for
    from learnloop.router_objective import tail_data as TD
    from learnloop.router_objective import value as V

    captured: dict[str, Any] = {}
    real_build = OI.build

    def recording(vault, repository, **kwargs):
        captured.setdefault("kwargs", kwargs)
        return real_build(vault, repository, **kwargs)

    monkeypatch.setattr(OI, "build", recording)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    _first_decision(env)
    kwargs = dict(captured["kwargs"])
    kwargs["support"] = [ref for ref in kwargs["support"] if not ref.startswith("lesson_offer:")]
    _lesson_activity(env)
    now_iso = env.clock.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    kwargs["now_iso"] = now_iso
    on = env.vault
    off = _with(env.vault, in_objective=False)
    old = _with(env.vault, version=OLD)

    def valued(vault):
        inputs, actions, sources = real_build(vault, env.repository, **kwargs)
        evaluation = V.evaluate(inputs, actions, draws=4, seed="pinned")
        return inputs, sources, {row.ref: row.q_draws for row in evaluation.valued}

    old_inputs, old_sources, old_q = valued(old)
    off_inputs, off_sources, off_q = valued(off)
    on_inputs, on_sources, on_q = valued(on)
    assert off_inputs == old_inputs and off_q == old_q
    assert off_sources["population"] == old_sources["population"] and off_sources["session"] == old_sources["session"]
    # On: the lesson's 20 foreground minutes are on the clock, the pending check's LO is in the population.
    assert on_inputs.session_minutes == pytest.approx(old_inputs.session_minutes + 20.0)
    assert "lo_diag" in on_sources["population"]["los"] and "lo_diag" not in old_sources["population"]["los"]
    assert TD.features_version(off.config) == TD.features_version(old.config) != TD.features_version(on.config)
    assert OI.population(off, env.repository, now_iso) == OI.population(old, env.repository, now_iso)
    assert policy_for(off, env.repository, runtime=fake_runtime()).lesson_offer is None
    assert policy_for(old, env.repository, runtime=fake_runtime()).lesson_offer is None
    assert SG.suggestions_active(off) == SG.suggestions_enabled(off) and SG.suggestions_active(old)


