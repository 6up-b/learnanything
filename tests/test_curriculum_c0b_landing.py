"""Curriculum C0b landing onto main: its interactions with Reader CA5a, CA3 and the
mvp-0.38 cold-retry reschedule (docs/reviews/curriculum-c0b-scope-path.md, "Landing onto main").

(i) CA5a's *not about this* (and C0a's corrections) with C0b's *also about…*: a
    dismissal and an *also about* correction on the same section coexist, and both
    stand through a coverage re-judgment and a path re-judgment.
(ii) CA3's ``compare_scope`` Decider and C0b's scope resolver are separate routes
    with separate caps; with ``curriculum.enabled`` off, CA3 reads exactly as with
    no deliverable, CA5a is off (its data is ``curriculum.enabled``'s) and every C0b
    RPC refuses.
(iii) *Check me later* and *Am I ready?* create DL2 Check once commitments that the
    mvp-0.38 cold-retry reschedule never touches (on and off are identical), and a
    shadow rebuild is 0/0/0 with them present.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import timedelta
from typing import Any

import pytest

from learnloop.algorithm_versions import COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.diagnosis.remediation import reschedule_cold_after_assist_active
from learnloop.source_retrieval import compare_scope as CS
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import section_coverage as SC
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault, cover_all
from tests.helpers import NOW
from tests.reading_path_fixtures import call, context, normalized
from tests.section_coverage_fixtures import BOOK_EIGEN, CoverageJudgeFake
from tests.test_reader_ca3_compare_anywhere import BOOKS, ScopeDecider
from tests.ux_phase1_support import set_config

ORIGIN = ("ext_book", BOOK_EIGEN)
TARGET = ("ext_lay", "lay_eigen")


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _newest_corrections(repository) -> dict[tuple[str, str, str], str]:
    with repository.connection() as connection:
        fixes = SC.store.corrections(connection, learning_object_ids=["lo_eigen", "lo_det"])
    return {key: str(row["learner_override"]) for key, row in fixes.items()}


def _path_refs(vault, repository, goal_id) -> dict[str, set[tuple[str, str]]]:
    view = DP.path_view(vault, repository, goal_id)
    out: dict[str, set[tuple[str, str]]] = {}
    for line in view["lines"]:
        refs = {(line["section"]["extraction_id"], line["section"]["section_id"])}
        refs |= {(a["extraction_id"], a["section_id"]) for a in line["alternates"]}
        out[line["learning_object_id"]] = refs
    return out


def _topic_refs(fake: DeliverableFake) -> dict[str, set[str]]:
    context_ = fake.contexts[-1]
    return {topic["id"]: {section["ref"] for section in topic["sections"]} for topic in context_["topics"]}


# -- (i) not about this + also about on one section, through re-judgments --------------------------------


def test_i_a_dismissal_and_an_also_about_on_one_section_coexist_through_path_rejudgments(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    # The 5.1 section "applies" whatever the topic, so an *also about* on it has a judged treatment to keep.
    cover_all(paths, repository, "lo_eigen", "lo_det", treatments={"5.1 Eigenvectors and eigenvalues": "applies"})
    vault = load_vault(paths.root)
    library = SC.Library(vault, repository)
    assert "lo_eigen" in SC.section_learning_objects(vault, repository, library, *ORIGIN)

    # CA5a: *not about this* on the Lay hit of the open Chapter 5 (lo_eigen on lay_eigen).
    SC.dismiss(vault, repository, ORIGIN, TARGET, operation_id="op_landing_0001")
    # C0b: *also about…* on the same section, resolved to Determinants.
    out = DL.also_about(vault, repository, *TARGET, "this one is also about determinants", client=DeliverableFake())
    assert out["status"] == "corrected" and out["learning_object_id"] == "lo_det"
    expected = {(*TARGET, "lo_eigen"): "not_about", (*TARGET, "lo_det"): "is_about"}
    assert {key: value for key, value in _newest_corrections(repository).items() if key[:2] == TARGET} == expected

    # C0a re-judges both LOs (the correction made lo_det's state new); both learner rows still stand.
    cover_all(paths, repository, "lo_eigen", "lo_det", treatments={"5.1 Eigenvectors and eigenvalues": "applies"})
    vault = load_vault(paths.root)
    standing = SC.standing(vault, repository, SC.Library(vault, repository), ["lo_eigen", "lo_det"])
    assert standing["lo_eigen"][TARGET].treatment == "not_about" and standing["lo_eigen"][TARGET].by == "learner"
    assert standing["lo_det"][TARGET].about and standing["lo_det"][TARGET].by == "learner"

    # A deliverable needing both; the path is judged, then judged again at another depth.
    goal_id = DL.create_deliverable(vault, repository, "eigenvalues and determinants for my midterm")["goal_id"]
    vault = load_vault(paths.root)
    DL.resolve(vault, repository, goal_id, client=DeliverableFake())
    vault = load_vault(paths.root)
    for depth in ("learn_to_use_it", "fluency"):
        DL.add_input(vault, repository, goal_id, "depth", text=depth)
        vault = load_vault(paths.root)
        fake = DeliverableFake()
        assert DP.judge(vault, repository, goal_id, client=fake).status == "ready" and fake.calls == 1
        sent = _topic_refs(fake)
        assert "ext_lay/lay_eigen" not in sent["lo_eigen"]  # dismissed: never offered for Eigenvalues
        assert "ext_lay/lay_eigen" in sent["lo_det"]  # also about: offered for Determinants
        refs = _path_refs(vault, repository, goal_id)
        assert TARGET not in refs["lo_eigen"] and TARGET in refs["lo_det"]
        assert {key: value for key, value in _newest_corrections(repository).items() if key[:2] == TARGET} == expected
    depths = _rows(repository, "SELECT DISTINCT depth FROM deliverable_path_sections WHERE goal_id = ? ORDER BY depth",
                   (goal_id,))
    assert depths == [("fluency",), ("learn_to_use_it",)]


# -- (ii) separate routes, separate caps; curriculum.enabled off ------------------------------------------


class MeteredDeliverableFake(DeliverableFake):
    provider_type = "openai_compatible"  # a metered route: held to the curriculum's dollar cap


def test_ii_compare_scope_and_the_scope_resolver_are_separate_routes():
    from typing import get_args

    from learnloop.ai.routing import AITask

    routes = {CS.ROUTE, DL.SCOPE_ROUTE, DL.PATH_ROUTE}
    assert routes == {"compare_scope", "deliverable_scope_resolver", "deliverable_path_judge"}
    assert routes <= set(get_args(AITask))
    assert CS.TASK not in DL.OWNER_KINDS and "compare_scope" not in DL.OWNER_KINDS


def test_ii_compare_scopes_cap_does_not_stop_the_resolver(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[reader_compare]\nscope_max_calls_per_day = 1")
    vault = load_vault(paths.root)
    decider = ScopeDecider(choices={"intent": "compare"})
    first = CS.read(vault.root, vault.config, repository, text="compare Axler and Lay", books=BOOKS,
                    client_factory=lambda: decider)
    capped = CS.read(vault.root, vault.config, repository, text="compare Strang and Lay", books=BOOKS,
                     client_factory=lambda: decider)
    assert first.status == "read" and (capped.status, capped.reason) == ("fallback", "capped")
    fake = DeliverableFake()
    goal_id = DL.create_deliverable(vault, repository, "eigenvalues for my midterm")["goal_id"]
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert result.status == "ready" and fake.calls == 1
    assert CS.calls_today(repository) == 1  # the resolver's call is not counted against CA3's allowance


def test_ii_the_curriculum_cap_does_not_stop_compare_scope(tmp_path):
    paths, repository = build_deliverable_vault(
        tmp_path / "vault", config="[source_retrieval]\nllm_price_per_million = 1000.0\n\n"
                                   "[curriculum]\nmax_daily_cost_usd = 0.0001")
    vault = load_vault(paths.root)
    fake = MeteredDeliverableFake()
    goal_id = DL.create_deliverable(vault, repository, "eigenvalues for my midterm")["goal_id"]
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert result.status != "ready" and fake.calls == 0  # refused before its call: the curriculum's cap
    decider = ScopeDecider(choices={"intent": "compare"})
    reading = CS.read(vault.root, vault.config, repository, text="compare Axler and Lay", books=BOOKS,
                      client_factory=lambda: decider)
    assert reading.status == "read" and len(decider.calls) == 1 and CS.calls_today(repository) == 1


def _contract(paths) -> dict[str, Any]:
    return normalized(call(context(paths.root), "reader.prompt_contract", {}))


def test_ii_curriculum_off_leaves_ca3_and_ca5a_as_with_no_deliverable(tmp_path):
    with_deliverables, repository = build_deliverable_vault(tmp_path / "with")
    plain, plain_repository = build_deliverable_vault(tmp_path / "plain")
    fake = DeliverableFake()
    ctx = context(with_deliverables.root, deliverable_inline=True, coverage_judge_client=CoverageJudgeFake(),
                  deliverable_scope_client=fake, deliverable_path_client=fake)
    created = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})
    call(ctx, "curriculum.set_depth", {"goal_id": created["goalId"], "depth": "learn_to_use_it"})
    for paths in (with_deliverables, plain):
        set_config(paths.root, {("curriculum", "enabled"): False})

    # The Reader's prompt contract (CA3's compareScope, CA5a's correspondence) is the same as with none.
    assert _contract(with_deliverables) == _contract(plain)
    assert "correspondence" not in call(context(plain.root), "reader.prompt_contract", {})  # curriculum's data: off
    # CA3's reading runs exactly as with no deliverable.
    readings = []
    for paths, repo in ((with_deliverables, repository), (plain, plain_repository)):
        vault = load_vault(paths.root)
        decider = ScopeDecider(choices={"intent": "compare"}, named=("Linear Algebra and Its Applications",))
        reading = CS.read(vault.root, vault.config, repo, text="compare Axler and Lay", books=BOOKS,
                          client_factory=lambda decider=decider: decider)
        readings.append((reading.status, reading.intent, reading.source_ids, len(decider.calls)))
    assert readings[0] == readings[1] and readings[0][0] == "read"
    # CA5a is off with the data it reads; every C0b RPC refuses.
    for name, params in (("reader.correspondents", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}),
                         ("curriculum.guide_slice", {"extraction_id": "ext_book"}),
                         ("curriculum.path", {"goal_id": created["goalId"]})):
        with pytest.raises(SidecarError):
            call(context(with_deliverables.root), name, params)


# -- (iii) Check once commitments vs the mvp-0.38 cold-retry reschedule; shadow 0/0/0 -------------------


def _checks(repository) -> list[tuple[Any, ...]]:
    """The Check once commitments as DL2 folds them (ids and times left out)."""

    from learnloop.scheduling.intent.resolution import load_snapshots

    with repository.connection() as connection:
        snapshots = load_snapshots(connection)
    return sorted((s.action, s.depth_preset, s.disposition, s.retired, tuple(sorted(s.item_targets)),
                   tuple(sorted(s.learning_object_targets)), s.via, s.due_hint, s.satisfied_at is not None)
                  for s in snapshots)


def _cold_lane(repository) -> tuple[Any, ...]:
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        tasks = connection.execute("SELECT kind, status FROM followup_tasks ORDER BY kind, status").fetchall()
        assisted = connection.execute("SELECT COUNT(*) FROM cold_measurement_opportunities WHERE trigger_kind = "
                                      "'assisted_cold_retry'").fetchone()[0]
    return tuple(tasks), assisted


def _with_checks(root, *, switch: bool):
    from learnloop.substrate.state_sync import sync_vault_state

    paths, repository = build_deliverable_vault(root)
    set_config(paths.root, {("algorithms", "algorithm_version"): COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
                            ("ask", "cold_help_converts"): True,
                            ("practice", "reschedule_cold_after_assist"): switch})
    clock = FrozenClock(NOW)
    # Synced at the tag, as tests/test_cold_retry_reschedule.py builds its rebuild-equivalent vault.
    sync_vault_state(load_vault(paths.root), repository, clock=clock)
    cover_all(paths, repository, "lo_eigen")
    vault = load_vault(paths.root)
    # *Check me later* on a path line.
    later = DL.create_deliverable(vault, repository, "eigenvalues for my midterm")["goal_id"]
    DL.resolve(load_vault(paths.root), repository, later, client=DeliverableFake())
    DL.add_input(load_vault(paths.root), repository, later, "depth", text="learn_to_use_it")
    vault = load_vault(paths.root)
    DP.judge(vault, repository, later, client=DeliverableFake())
    checked = DP.override(vault, repository, later, "lo_eigen", "check_later", clock=clock)
    # *Am I ready?* on another deliverable.
    ready = DL.create_deliverable(vault, repository, "matrix computations and vector lists",
                                  due_at="2026-12-01")["goal_id"]
    DL.resolve(load_vault(paths.root), repository, ready, client=DeliverableFake())
    DL.add_input(load_vault(paths.root), repository, ready, "depth", text="learn_to_use_it")
    created = DP.ready_checks(load_vault(paths.root), repository, ready, clock=clock)["created"]
    return paths, repository, checked["check"], created


def _help_on_each_check(paths, repository, created) -> None:
    """Help taken on each check's item: an assisted attempt (a hint), a day later."""

    vault = load_vault(paths.root)
    for entry in created:
        complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(practice_item_id=entry["item_id"], learner_answer_md="An answer.",
                         attempt_type="independent_attempt", hints_used=1),
            SelfGradeInput(criterion_points={criterion.id: criterion.points for criterion in
                                             vault.practice_items[entry["item_id"]].grading_rubric.criteria},
                           confidence=4),
            clock=FrozenClock(NOW + timedelta(days=1)))


def test_iii_check_once_commitments_are_never_touched_by_the_cold_retry_reschedule(tmp_path):
    states = {}
    for switch in (True, False):
        paths, repository, later, created = _with_checks(tmp_path / f"vault_{switch}", switch=switch)
        assert reschedule_cold_after_assist_active(load_vault(paths.root)) is switch
        assert later["commitment_id"] and len(created) == 2 and all(entry["item_id"] for entry in created)
        before = _checks(repository)
        assert [row[0] for row in before] == ["test_me_later"] * 3
        assert {row[6] for row in before} == {"deliverable_path", "deliverable_ready"}
        _help_on_each_check(paths, repository, created)
        after = _checks(repository)
        # Nothing on the cold-retry lane: no cold retry, no assisted reschedule opportunity.
        tasks, assisted = _cold_lane(repository)
        assert not [task for task in tasks if task[0] == "cold_retry"] and assisted == 0
        # The checks keep their targets, action and dates (only DL2's own rule may answer them).
        assert [row[:2] + row[4:8] for row in after] == [row[:2] + row[4:8] for row in before]
        states[switch] = (after, tasks)
    assert states[True] == states[False]  # the reschedule on is exactly the reschedule off


def test_iii_a_shadow_rebuild_is_zero_with_the_checks_present(tmp_path):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, repository, _later, created = _with_checks(tmp_path / "vault", switch=True)
    for stage in ("checks", "help_taken"):
        if stage == "help_taken":
            _help_on_each_check(paths, repository, created)
        result = shadow_rebuild(load_vault(paths.root))
        assert result.live_database_unchanged, stage
        assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}, stage
