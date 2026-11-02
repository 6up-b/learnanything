"""Teacher TE1's successor (spec_teacher_v1 §18.3): the tag, the upgrade, the kill switch's parity,
the shadow rebuild, the defaults snapshot and the desktop RPCs. Every model is a fake; no network.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import (
    DELIVERABLE_PLAN_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_ALGORITHM_VERSION,
    TEACHER_VERSIONS,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import (
    TeacherFake,
    build_teacher_vault,
    check_turn,
    clients,
    landed_and_close_turn,
    plan_turn,
)

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
TAG = TEACHER_ALGORITHM_VERSION


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def test_the_tag_is_the_chains_last_link_after_curriculum_c1():
    from learnloop.teacher_upgrade import PREDECESSOR

    assert SUCCESSOR_CHAIN[-2:] == (DELIVERABLE_PLAN_ALGORITHM_VERSION, TAG) == ("mvp-0.40", "mvp-0.41")
    assert LATEST_ALGORITHM_VERSION == TAG and PREDECESSOR == DELIVERABLE_PLAN_ALGORITHM_VERSION
    assert TEACHER_VERSIONS == frozenset({TAG})


def test_every_defaults_snapshot_drops_to_mains_value_without_the_teacher_keys():
    """G-style parity of the defaults: the new keys and the route are all that moved the
    snapshots recorded before the tag (main's values at 19c72752b3, frozen here)."""

    from learnloop.config.schema import LearnLoopConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, \
        defaults_fingerprint_for_version

    mains = {"mvp-0.9": "2cad7d6f8047d66b7290bc424553de1a66225992389ee4aff27300593001f8de",
             "mvp-0.39": "932fd5c31ebf2945432ce9fae72d928a14ffe3f1a4ad580c404bfc0112fce31f",
             "mvp-0.40": "f3da05902e84b7ba061bb92d77b7994c0ed15633feae4388f6a4e65e6611c587"}
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version)
    for version, main in mains.items():
        config = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(version)))
        dumped = config.model_dump(mode="json", exclude_none=False)
        for key in ("enabled", "weight", "brief", "context", "delayed", "metered_price_per_million",
                    "max_lesson_cost_usd"):
            dumped["teacher"].pop(key)
        dumped["ai"]["routing"].pop("teacher")
        # Reader RW5d P5 (after main's 19c72752b3): its [figures] prefetch keys and route moved them too.
        dumped["figures"].pop("prefetch_enabled")
        dumped["figures"].pop("prefetch")
        dumped["ai"]["routing"].pop("figure_prefetch_judge")
        digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == main, version
    assert TAG in DEFAULTS_SNAPSHOT_BY_ALGORITHM


def _practice(paths, repository, at):
    """A fixed run of ordinary practice: no lesson anywhere."""

    vault = load_vault(paths.root)
    for offset, (item_id, points, tap) in enumerate([("pi_eig_1", 4, 5), ("pi_det_1", 0, 4), ("pi_eig_2", 2, 3)]):
        complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
                         answer_confidence=tap),
            SelfGradeInput(criterion_points={"correctness": points}, confidence=tap),
            clock=FrozenClock(at + timedelta(hours=offset)))


def _state(repository):
    """Every learner-state table's rows, minus surrogate ids and the version label (which names the
    vault's tag, the one thing that differs below it)."""

    tables = ("learning_object_mastery", "facet_recall_state", "practice_item_state", "reveal_events",
              "lesson_weight_state", "confidence_calibration_state", "lessons")
    out = {}
    for table in tables:
        with repository.connection() as connection:
            cursor = connection.execute(f"SELECT * FROM {table} ORDER BY 1")
            names = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
        keep = [i for i, name in enumerate(names) if name not in ("algorithm_version", "id")]
        out[table] = [tuple(row[i] for i in keep) for row in rows]
    return out


@pytest.mark.parametrize("setting", ["teacher_off", "below_tag"])
def test_with_the_switch_off_or_below_the_tag_practice_is_byte_identical(tmp_path, setting):
    from tests.ux_phase1_support import set_config

    on_paths, on_repository = build_teacher_vault(tmp_path / "on")
    if setting == "teacher_off":
        off_paths, off_repository = build_teacher_vault(tmp_path / "off")
        set_config(off_paths.root, {("teacher", "enabled"): False})
    else:
        off_paths, off_repository = build_teacher_vault(tmp_path / "off", version=DELIVERABLE_PLAN_ALGORITHM_VERSION)
    _practice(on_paths, on_repository, T0)
    _practice(off_paths, off_repository, T0)
    on, off = _state(on_repository), _state(off_repository)
    assert on["learning_object_mastery"] == off["learning_object_mastery"]
    assert on["facet_recall_state"] == off["facet_recall_state"]
    assert on["practice_item_state"] == off["practice_item_state"]
    assert on["lesson_weight_state"] == off["lesson_weight_state"] == []
    assert on["lessons"] == off["lessons"] == []


def _whole_lesson(paths, repository):
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                         learning_object_ids=["lo_eigen"], clients=clients(fake), clock=FrozenClock(T0))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply", payload={"text": "go"},
           clients=clients(fake), clock=FrozenClock(T0 + timedelta(minutes=1)))
    fake.turns = [landed_and_close_turn()]
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
           payload={"answer": "det(A - tI) = 0", "tap": 4}, clients=clients(fake),
           clock=FrozenClock(T0 + timedelta(minutes=2)))
    return view["lesson_id"]


def test_a_shadow_rebuild_after_a_lesson_has_zero_projection_deltas(tmp_path):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, repository = build_teacher_vault(tmp_path / "vault")
    # The fixture's LOs were written as files: a live rebuild first gives them their cold rows, as
    # bootstrap would, so the shadow compares the lesson's effects only.
    rebuild_all_derived_state(load_vault(paths.root), repository)
    _whole_lesson(paths, repository)
    complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id="pi_eig_3", learner_answer_md="cold", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(T0 + timedelta(days=3)))
    result = shadow_rebuild(load_vault(paths.root))
    assert result.live_database_unchanged
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}


def test_the_whole_rebuild_owns_the_lesson_weight_tables_and_reproduces_them(tmp_path):
    from learnloop.learner import lesson_weight as LW
    from learnloop.substrate.rebuild_orchestrator import derived_table_owners, rebuild_all_derived_state

    owners = derived_table_owners()
    for table in LW.DERIVED_TABLES:
        assert owners[table] == ("lesson_weight",)
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _whole_lesson(paths, repository)
    snapshot = {table: _rows(repository, f"SELECT * FROM {table} ORDER BY 1") for table in LW.DERIVED_TABLES}
    rebuild_all_derived_state(load_vault(paths.root), repository)
    again = {table: _rows(repository, f"SELECT * FROM {table} ORDER BY 1") for table in LW.DERIVED_TABLES}
    assert again == snapshot
    receipts = _rows(repository, "SELECT COUNT(*) FROM lesson_receipts")
    assert receipts == [(1,)]  # RECEIPT rows are never cleared by replay


def test_the_upgrade_from_the_predecessor_and_its_refusals(tmp_path):
    from learnloop.teacher_upgrade import upgrade_to_teacher

    paths, repository = build_teacher_vault(tmp_path / "vault", version=DELIVERABLE_PLAN_ALGORITHM_VERSION)
    result = upgrade_to_teacher(paths.root)
    assert result.upgraded and result.from_version == DELIVERABLE_PLAN_ALGORITHM_VERSION and result.to_version == TAG
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_teacher(paths.root)
    assert not again.upgraded and again.problems
    old, _repo = build_teacher_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_teacher(old.root)
    assert not refused.upgraded and "cannot upgrade" in refused.problems[0]


def test_the_cli_installs_this_links_completion():
    import inspect

    from learnloop.cli import runtime

    assert "learnloop.teacher_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)


# --- the desktop RPCs ------------------------------------------------------------------------------


class _Ctx:
    def __init__(self, paths, repository):
        self.paths, self.repository = paths, repository
        self.grading_provider_override = None
        self.reloads = 0

    def require_vault(self):
        return load_vault(self.paths.root), self.repository

    def reload(self, maintenance: bool = True):
        self.reloads += 1


def test_lesson_turn_runs_a_lesson_and_lesson_view_resumes_it(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import lesson as H

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn()])
    monkeypatch.setattr(H, "_clients", lambda ctx, vault: clients(fake))
    ctx = _Ctx(paths, repository)
    opened = H.lesson_turn(ctx, H.LessonTurnInput(action="open", entry="learning_object",
                                                  learning_object_ids=["lo_eigen"]))
    lesson_id = opened["lessonId"]
    posed = H.lesson_turn(ctx, H.LessonTurnInput(action="reply", lesson_id=lesson_id, text="go"))
    assert posed["openCheck"] is not None and ctx.reloads == 1  # the minted item reloads the vault
    resumed = H.lesson_view(ctx, H.LessonViewInput(lesson_id=lesson_id))
    assert resumed["openCheck"]["checkRef"] == posed["openCheck"]["checkRef"]
    assert "committed" not in json.dumps(resumed).lower()


def test_lesson_turn_refuses_with_the_switch_off(tmp_path):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import lesson as H
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault")
    set_config(paths.root, {("teacher", "enabled"): False})
    with pytest.raises(SidecarError) as raised:
        H.lesson_turn(_Ctx(paths, repository), H.LessonTurnInput(action="open", entry="learning_object",
                                                                 learning_object_ids=["lo_eigen"]))
    assert raised.value.code == "teacher_disabled"


def test_no_openrouter_offer_for_a_lesson_until_its_price_is_set():
    from learnloop.ai.plan_fallback import METERED_PRICE_SETTINGS, offer_blocker
    from learnloop.config.schema import LearnLoopConfig

    assert METERED_PRICE_SETTINGS["teacher"] == "teacher.metered_price_per_million"
    assert offer_blocker(LearnLoopConfig(), "teacher") is not None
    priced = LearnLoopConfig.model_validate({"teacher": {"metered_price_per_million": 1.0}})
    assert offer_blocker(priced, "teacher") is None


def test_a_metered_lesson_turn_needs_its_price_and_cap(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")

    class Metered(TeacherFake):
        provider_type = "openrouter"

    with pytest.raises(S.LessonError) as raised:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                      clients=clients(Metered([plan_turn])))
    assert raised.value.code == "plan_unavailable"


def test_a_bare_upgrade_targets_mvp041_through_the_chain(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop import activation_journal
    from learnloop.cli import app
    from learnloop.cli.runtime import _complete_interrupted_activation
    from tests.helpers import create_placement_vault

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)
    paths = create_placement_vault(tmp_path / "v", version="mvp-0.39")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"mvp-0.39 -> {TAG}" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
