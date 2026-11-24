"""Reader workbench v2 RD6, the goal lens's RPCs (spec §3.4, §12.2-§12.5, §12.8): ``goal.band``,
``goal.lens`` and ``goal.section_choice`` over the real deliverable path and coverage.

Every model is a fake; coverage is C0a's own judge with C0a's fake; nothing here starts background work."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from learnloop.curriculum import commitments as C
from learnloop.curriculum import goal_lens as GL
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import section_coverage as SC
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.deliverable_fixtures import DeliverableFake
from tests.goal_lens_helpers import build_lens_vault, lens_context, levels, scoped_goal, summary
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import CoverageJudgeFake, table_counts

RPCS = ("goal.band", "goal.lens", "goal.section_choice", "goal.choices")


def _lens(ctx, goal_id, extraction_id, **params):
    return call(ctx, "goal.lens", {"goal_id": goal_id, "extraction_id": extraction_id, **params})


def test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.goal_lens import GOAL_LENS_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert GOAL_LENS_RPCS == RPCS
    for name in RPCS:
        assert name in METHOD_REGISTRY and name not in ALLOWLIST
        with pytest.raises(ValidationError):
            METHOD_REGISTRY[name].params_model.model_validate({"goal_id": "g", "extraction_id": "e",
                                                               "section_id": "s", "choice": "none",
                                                               "operation_id": "op_12345678", "surprise": 1})
    lens = METHOD_REGISTRY["goal.lens"].params_model
    for bad in ({"from_span_id": "s1"}, {"t0": 1.0}, {"from_span_id": "s1", "to_span_id": "s2", "t0": 0, "t1": 1}):
        with pytest.raises(ValidationError):
            lens.model_validate({"goal_id": "g", "extraction_id": "e", **bad})


def test_switched_off_every_rpc_refuses_and_nothing_is_called_or_written(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", config="[curriculum]\nenabled = false", cover=())
    fake = DeliverableFake()
    ctx = lens_context(paths, fake=fake)
    before = table_counts(repository)
    params = {"goal.band": {"goal_id": "g"}, "goal.lens": {"goal_id": "g", "extraction_id": "ext_book"},
              "goal.section_choice": {"goal_id": "g", "extraction_id": "ext_book", "section_id": "ch_det",
                                      "choice": "read_anyway", "operation_id": "op_12345678"},
              "goal.choices": {}}
    for name in RPCS:
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params[name])
        assert caught.value.code == "curriculum_disabled", name
    assert fake.calls == 0 and table_counts(repository) == before


def test_the_band_shows_the_goal_its_dots_in_path_order_each_depths_size_and_what_is_next(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", chain=True)
    goal_id = scoped_goal(paths, repository, depth="get_the_idea", due_at="2026-12-20")
    band = call(lens_context(paths), "goal.band", {"goal_id": goal_id})
    assert band["version"] == 1 and band["status"] == "ready"
    goal = band["goal"]
    assert (goal["sentence"], goal["kind"], goal["dueAt"]) == ("eigenvalues", "quest", "2026-12-20T23:59:59Z")
    assert goal["setAt"]
    # Prerequisites before what assumes them; the LO needed only deeper is a dimmed dot after them.
    dots = [(dot["learningObjectId"], dot["kind"], dot["beyondDepth"]) for dot in band["learningObjects"]]
    assert dots == [("lo_det", "prerequisite", False), ("lo_eigen", "needed", False), ("lo_rows", "later", True)]
    assert band["counts"] == {"learningObjects": 2, "demonstrated": 0, "likely": 0, "untested": 2}
    assert band["learningObjects"][1]["primary"]["sectionId"] == "ch_eigen"
    sizes = {depth["id"]: (depth["learningObjects"], depth["sections"]) for depth in band["depths"]}
    assert sizes == {"get_the_idea": (2, 2), "learn_to_use_it": (3, 2), "fluency": (3, 2)}
    assert band["next"]["kind"] == "section" and band["next"]["learningObjectId"] == "lo_det"
    assert band["checks"] == {"dueToday": 0, "answeredToday": 0, "first": None}
    assert band["pace"] is not None and band["pace"]["daysLeft"] is not None
    # The path view's rows are curriculum.path's own lines.
    path = call(lens_context(paths), "curriculum.path", {"goal_id": goal_id, "judge": False})
    assert band["path"]["lines"] == path["lines"]


def test_the_lens_levels_follow_the_real_path_and_coverage(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    book = levels(ctx, goal_id, "ext_book")
    assert summary(book["ch_eigen"]) == ("core", "mapped", "primary", ["lo_eigen"])
    assert summary(book["ch_det"]) == ("supporting", "mapped", "prerequisite", ["lo_det"])
    assert summary(book["ch_orth"]) == ("skippable", "mapped", "not_about", [])
    assert book["ch_orth"]["dim"] and not book["ch_eigen"]["dim"]
    lay = levels(ctx, goal_id, "ext_lay")
    assert summary(lay["lay_eigen"]) == ("supporting", "mapped", "alternate", ["lo_eigen"])
    assert summary(lay["lay_held"]) == ("unmapped", "unmapped", "withheld", [])
    assert summary(lay["lay_ortho"]) == ("unmapped", "unmapped", "unmapped", [])
    # The why is the path's own per-section reason (deliverable_path_sections.reason) where it places one.
    line = next(line for line in DP.path_view(load_vault(paths.root), repository, goal_id)["lines"]
                if line["learning_object_id"] == "lo_eigen")
    assert book["ch_eigen"]["reasonMd"] == line["reason"]
    assert lay["lay_eigen"]["reasonMd"] == "another view in Lay"
    assert book["ch_eigen"]["coverageLine"] == (
        "This section develops “Eigenvalues” · goal topic · main reading")
    assert all(level["judgedPer"] == "section" for level in book.values())
    reply = _lens(ctx, goal_id, "ext_book")
    assert reply["mapping"] == "mapped" and reply["depth"] == "learn_to_use_it"


def test_a_section_about_a_deeper_lo_is_later_and_a_depth_change_re_renders_it(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", chain=True)
    SC.correct(load_vault(paths.root), repository, "ext_book", "ch_orth", "lo_rows", "is_about")
    goal_id = scoped_goal(paths, repository, depth="get_the_idea")
    ctx = lens_context(paths)
    orth = levels(ctx, goal_id, "ext_book")["ch_orth"]
    assert summary(orth) == ("later", "mapped", "deeper_depth", ["lo_rows"]) and orth["dim"]
    assert orth["reasonMd"] == "Needed for “Rows and row swaps” only at a deeper level than get the idea."
    DL.add_input(load_vault(paths.root), repository, goal_id, "depth", text="learn_to_use_it")
    DP.judge(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    orth = levels(ctx, goal_id, "ext_book")["ch_orth"]
    assert summary(orth) == ("supporting", "mapped", "learner_about", ["lo_rows"]) and not orth["dim"]


def test_the_learners_path_choices_move_the_levels(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    call(ctx, "curriculum.path_override", {"goal_id": goal_id, "learning_object_id": "lo_eigen",
                                           "choice": "use_instead", "section_ref": "ext_lay/lay_char"})
    lay, book = levels(ctx, goal_id, "ext_lay"), levels(ctx, goal_id, "ext_book")
    assert summary(lay["lay_char"])[:3] == ("core", "mapped", "primary")
    assert lay["lay_char"]["learnerLine"] == "You chose to read it here."
    assert summary(book["ch_eigen"])[:3] == ("supporting", "mapped", "alternate")
    call(ctx, "curriculum.path_override", {"goal_id": goal_id, "learning_object_id": "lo_eigen", "choice": "skip"})
    book = levels(ctx, goal_id, "ext_book")
    assert summary(book["ch_eigen"]) == ("skippable", "mapped", "you_skipped", ["lo_eigen"]) and book["ch_eigen"]["dim"]
    call(ctx, "curriculum.path_override", {"goal_id": goal_id, "learning_object_id": "lo_det",
                                           "choice": "check_later"})
    det = levels(ctx, goal_id, "ext_book")["ch_det"]
    assert summary(det) == ("already_shown", "mapped", "check_pending", ["lo_det"])
    assert det["learnerLine"] == "You asked for a cold check later."


def test_read_it_anyway_on_a_dimmed_section_is_stored_idempotent_and_clearable(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    params = {"goal_id": goal_id, "extraction_id": "ext_book", "section_id": "ch_orth", "choice": "read_anyway",
              "operation_id": "op_read_1"}
    first = call(ctx, "goal.section_choice", params)["choice"]
    assert (first["choice"], first["replayed"], first["sectionId"]) == ("read_anyway", False, "ch_orth")
    assert call(ctx, "goal.section_choice", params)["choice"]["replayed"] is True
    with pytest.raises(SidecarError) as caught:
        call(ctx, "goal.section_choice", {**params, "section_id": "ch_det"})
    assert caught.value.code == "validation_error"
    orth = levels(ctx, goal_id, "ext_book")["ch_orth"]
    assert (orth["level"], orth["dim"], orth["choice"], orth["learnerLine"]) == (
        "skippable", False, "read_anyway", "You chose to read it anyway.")
    with repository.connection() as connection:
        rows = connection.execute("SELECT judge, verdict FROM judgment_ledger WHERE task = 'goal_lens_section'").fetchall()
    assert [tuple(row) for row in rows] == [("learner_card", "read_anyway")]
    call(ctx, "goal.section_choice", {**params, "choice": "none", "operation_id": "op_read_2"})
    orth = levels(ctx, goal_id, "ext_book")["ch_orth"]
    assert orth["dim"] and orth["choice"] is None
    for bad, code in (({"choice": "skip"}, "validation_error"), ({"section_id": "nowhere"}, "validation_error"),
                      ({"operation_id": "x"}, "validation_error"), ({"goal_id": "goal_linear_algebra_ml"},
                                                                     "validation_error")):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "goal.section_choice", {**params, "operation_id": "op_read_3", **bad})
        assert caught.value.code == code, bad


def test_a_topic_whose_coverage_is_unjudged_keeps_sections_partial_until_it_is_judged(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", cover=("lo_eigen",))
    goal_id = scoped_goal(paths, repository)
    coverage = CoverageJudgeFake()
    ctx = lens_context(paths, coverage=coverage)
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    assert band["coverage"]["unjudged"] == ["lo_det"] and coverage.calls == 0
    book = levels(ctx, goal_id, "ext_book")
    # Core cannot be raised by an unchecked topic; anything else waits for it, and no row is unmapped.
    assert summary(book["ch_eigen"])[:2] == ("core", "mapped")
    assert summary(book["ch_det"])[:3] == ("partial", "partial", "partial_unsettled")
    assert book["ch_det"]["knownLevel"] is None and not book["ch_det"]["dim"]
    lay = levels(ctx, goal_id, "ext_lay")
    assert (lay["lay_eigen"]["level"], lay["lay_eigen"]["knownLevel"]) == ("partial", "supporting")
    # The Guide's read starts the coverage it owes (inline here); then every section settles.
    call(ctx, "curriculum.path", {"goal_id": goal_id})
    assert coverage.calls >= 1
    book = levels(ctx, goal_id, "ext_book")
    assert summary(book["ch_det"])[:2] == ("supporting", "mapped")
    assert call(ctx, "goal.band", {"goal_id": goal_id})["coverage"]["unjudged"] == []


def _due_check(repository, lo_id, *, days_ago=1, begun=True):
    """A due check on the LO, begun inline (the replies mask a check's LO only once it is begun)."""

    from tests.inline_hold_helpers import hold_open

    due = (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    commitment_id = C.create_commitment(
        repository, action="test_me_later", intent_text=f"check {lo_id}", depth_preset=DP.READY_DEPTH_PRESET,
        targets=[{"target_kind": "learning_object", "target_ref": lo_id, "role": "required"}],
        client_idempotency_key=f"rd6a:{lo_id}", due_hint=due, provenance={"via": "deliverable_ready"}).id
    if begun:
        hold_open(repository, commitment_id)
    return commitment_id


def test_a_due_check_hides_its_los_purpose_text_and_comes_first_next(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    commitment_id = _due_check(repository, "lo_eigen")
    ctx = lens_context(paths)
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    dot = next(dot for dot in band["learningObjects"] if dot["learningObjectId"] == "lo_eigen")
    assert (dot["title"], dot["held"], dot["check"], dot["readinessLine"]) == (None, True, "due", None)
    assert band["checks"]["dueToday"] == 1 and band["checks"]["first"]["commitmentId"] == commitment_id
    assert "loId" not in band["checks"]["first"] and band["next"]["kind"] == "checks"
    line = next(line for line in band["path"]["lines"] if line["learningObjectId"] == "lo_eigen")
    assert line["held"] and line["reason"] is None
    eigen = levels(ctx, goal_id, "ext_book")["ch_eigen"]
    assert eigen["held"] and eigen["reasonMd"] == GL.HELD_REASON and eigen["coverageLine"] is None
    # The LO's name is hidden, the section's heading included (it names the LO).
    assert "Eigenvalues" not in json.dumps(eigen)
    # Answered on the learner's own today: the ◇ fills and the purpose text returns.
    C.satisfy_single_check(repository, commitment_id=commitment_id)
    band = call(ctx, "goal.band", {"goal_id": goal_id})
    dot = next(dot for dot in band["learningObjects"] if dot["learningObjectId"] == "lo_eigen")
    assert (dot["title"], dot["held"], dot["check"]) == ("Eigenvalues", False, "answered")
    assert band["checks"]["answeredToday"] == 1 and band["next"]["kind"] == "section"
    eigen = levels(ctx, goal_id, "ext_book")["ch_eigen"]
    assert not eigen["held"] and eigen["learnerLine"] == "You answered its cold check on your own today."


def test_the_replies_are_equal_after_a_rebuild_of_derived_state(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", chain=True)
    goal_id = scoped_goal(paths, repository, depth="get_the_idea")
    _due_check(repository, "lo_det")
    ctx = lens_context(paths)

    def replies():
        return (call(ctx, "goal.band", {"goal_id": goal_id}),
                [_lens(ctx, goal_id, extraction_id) for extraction_id in ("ext_book", "ext_lay")])

    before = replies()
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert replies() == before


def test_band_and_lens_make_no_model_call_and_write_nothing(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", cover=("lo_eigen",))
    goal_id = scoped_goal(paths, repository)
    fake, coverage = DeliverableFake(), CoverageJudgeFake()
    ctx = lens_context(paths, fake=fake, coverage=coverage)
    before = table_counts(repository)
    call(ctx, "goal.band", {"goal_id": goal_id})
    for extraction_id in ("ext_book", "ext_lay"):
        _lens(ctx, goal_id, extraction_id)
    assert (fake.calls, coverage.calls) == (0, 0) and table_counts(repository) == before


def test_the_empty_and_thin_states(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault", cover=())
    unresolved = DL.create_deliverable(load_vault(paths.root), repository, "eigenvalues")["goal_id"]
    asking = scoped_goal(paths, repository, depth=None)
    covered_none = scoped_goal(paths, repository, sentence="eigenvalues again", judge=False)
    ctx = lens_context(paths)
    band = call(ctx, "goal.band", {"goal_id": unresolved})
    assert band["status"] == "no_scope" and band["goal"]["sentence"] == "eigenvalues" and band["learningObjects"] == []
    assert _lens(ctx, unresolved, "ext_book")["levels"] == []
    assert call(ctx, "goal.band", {"goal_id": asking})["status"] == "ask_depth"
    # Nothing covered yet: no section has a mark, and the reading says it is not mapped for this goal.
    reply = _lens(ctx, covered_none, "ext_book")
    assert reply["mapping"] == "unmapped" and {level["level"] for level in reply["levels"]} == {"unmapped"}
    other = call(ctx, "goal.band", {"goal_id": "goal_linear_algebra_ml"})
    assert other["status"] == "not_a_deliverable" and other["goal"]["id"] == "goal_linear_algebra_ml"
    assert _lens(ctx, "goal_linear_algebra_ml", "ext_book")["levels"] == []
    with pytest.raises(SidecarError) as caught:
        call(ctx, "goal.band", {"goal_id": "goal_nowhere"})
    assert caught.value.code == "not_found"


def test_a_range_reads_only_the_sections_it_touches(tmp_path):
    paths, repository = build_lens_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    reply = _lens(ctx, goal_id, "ext_book", from_span_id="s7", to_span_id="s6")
    assert [(level["sectionId"], level["spanIds"]) for level in reply["levels"]] == [("ch_det", ["s6", "s7"])]
    assert _lens(ctx, goal_id, "ext_book", t0=0.0, t1=30.0)["levels"] == []
    with pytest.raises(SidecarError) as caught:
        _lens(ctx, goal_id, "ext_book", from_span_id="s1", to_span_id="s_nowhere")
    assert caught.value.code == "span_not_found"
    with pytest.raises(SidecarError) as caught:
        _lens(ctx, goal_id, "ext_nowhere")
    assert caught.value.code == "extraction_not_found"
