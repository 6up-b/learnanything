"""Curriculum C0b's RPCs: the scope, the path, the Guide's slice, overrides, "Am I ready?",
"also about…", the kill switch, and RW7a unchanged with the switch off.

Every model is a fake; background work runs inline (``deliverable_inline``).
"""
from __future__ import annotations

import json

import pytest

from learnloop.source_retrieval import deliverables as DL
from learnloop_sidecar.errors import SidecarError
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault
from tests.reading_path_fixtures import call, context, normalized
from tests.section_coverage_fixtures import CoverageJudgeFake, table_counts

RPCS = (
    "curriculum.deliverables", "curriculum.create_deliverable", "curriculum.set_scope", "curriculum.scope",
    "curriculum.scope_decide", "curriculum.set_depth", "curriculum.path", "curriculum.guide_slice",
    "curriculum.path_override", "curriculum.ready", "curriculum.ready_check", "curriculum.also_about",
)


def _ctx(paths, **attrs):
    fake = attrs.pop("fake", None) or DeliverableFake()
    return context(paths.root, deliverable_inline=True, coverage_judge_client=CoverageJudgeFake(),
                   deliverable_scope_client=fake, deliverable_path_client=fake, **attrs)


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.deliverables import DELIVERABLE_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert DELIVERABLE_RPCS == RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RPCS)


def test_switched_off_every_rpc_refuses_and_nothing_is_called_or_written(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[curriculum]\nenabled = false")
    fake = DeliverableFake()
    ctx = _ctx(paths, fake=fake)
    before = table_counts(repository)
    params = {
        "curriculum.deliverables": {}, "curriculum.create_deliverable": {"sentence": "eigenvalues"},
        "curriculum.set_scope": {"goal_id": "g", "kind": "text", "text": "x"}, "curriculum.scope": {"goal_id": "g"},
        "curriculum.scope_decide": {"goal_id": "g", "phrase": "x", "decision": "decline"},
        "curriculum.set_depth": {"goal_id": "g", "depth": "fluency"}, "curriculum.path": {"goal_id": "g"},
        "curriculum.guide_slice": {"extraction_id": "ext_book"},
        "curriculum.path_override": {"goal_id": "g", "learning_object_id": "lo_eigen", "choice": "skip"},
        "curriculum.ready": {"goal_id": "g"}, "curriculum.ready_check": {"goal_id": "g"},
        "curriculum.also_about": {"extraction_id": "ext_book", "section_id": "ch_det", "text": "x"},
    }
    for name in RPCS:
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params[name])
        assert caught.value.code == "curriculum_disabled", name
    assert fake.calls == 0 and table_counts(repository) == before


def test_switched_off_rw7a_is_byte_identical_whatever_the_deliverables(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    plain = context(paths.root)
    before = normalized(call(plain, "reader.reading_path", {"extraction_id": "ext_book", "judge": False}))
    ctx = _ctx(paths)
    created = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})
    call(ctx, "curriculum.set_depth", {"goal_id": created["goalId"], "depth": "learn_to_use_it"})
    with (paths.root / "learnloop.toml").open("a", encoding="utf-8") as handle:
        handle.write("\n[curriculum]\nenabled = false\n")
    after = normalized(call(context(paths.root), "reader.reading_path", {"extraction_id": "ext_book", "judge": False}))
    assert after == before


def test_create_scope_cover_path_slice_override_and_ready(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    fake = DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    ctx = _ctx(paths, fake=fake)
    created = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm",
                                                          "due_at": "2026-12-01"})
    goal_id = created["goalId"]
    assert created["status"] == "ready" and [t["learningObjectId"] for t in created["scope"]["topics"]] == ["lo_eigen"]
    # The scope change's coverage ran in the background (inline here): lo_eigen is judged.
    with repository.connection() as connection:
        judged = connection.execute("SELECT COUNT(*) FROM section_coverage WHERE learning_object_id = 'lo_eigen' "
                                    "AND learner_override IS NULL").fetchone()[0]
    assert judged >= 3
    asked = call(ctx, "curriculum.path", {"goal_id": goal_id})
    assert asked["status"] == "ask_depth"
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    assert view["status"] == "ready" and view["lines"][0]["section"]["sectionId"] == "ch_eigen"
    slice_ = call(ctx, "curriculum.guide_slice", {"extraction_id": "ext_book"})
    assert slice_["status"] == "ready" and slice_["goal"]["id"] == goal_id
    assert [line["section"]["sectionId"] for line in slice_["lines"]] == ["ch_eigen"]
    out = call(ctx, "curriculum.path_override", {"goal_id": goal_id, "learning_object_id": "lo_eigen",
                                                  "choice": "check_later"})
    assert out["check"]["commitmentId"] and out["path"]["lines"][0]["effectiveLabel"] == "check_pending"
    ready = call(ctx, "curriculum.ready", {"goal_id": goal_id})
    assert ready["lines"][0]["state"] == "untested" and ready["lines"][0]["checks"]
    assert call(ctx, "curriculum.ready_check", {"goal_id": goal_id})["created"] == []  # one is already waiting
    listed = call(ctx, "curriculum.deliverables", {})
    assert [entry["goalId"] for entry in listed["deliverables"]] == [goal_id]
    # The path judge read no passage text and no exam material.
    path_prompts = [prompt for prompt, purpose in zip(fake.prompts, fake.purposes) if purpose == "path"]
    assert path_prompts and all("Exam question" not in prompt for prompt in path_prompts)


def test_set_scope_refuses_an_exam_passage_and_writes_nothing(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    goal_id = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues"})["goalId"]
    before = table_counts(repository)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "curriculum.set_scope", {"goal_id": goal_id, "kind": "passage", "extraction_id": "ext_exam",
                                           "span_ids": ["s2"]})
    assert caught.value.code == "exam_material" and "protected exam material" in str(caught.value)
    assert table_counts(repository) == before


def test_a_correction_through_set_scope_and_a_decision_on_a_phrase(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    ctx = _ctx(paths, fake=DeliverableFake(unmatched=("jordan form",)))
    goal_id = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues and jordan form"})["goalId"]
    out = call(ctx, "curriculum.set_scope", {"goal_id": goal_id, "kind": "correction",
                                             "text": "also determinants", "context": {"via": "path_line"}})
    assert {t["learningObjectId"] for t in out["scope"]["topics"]} == {"lo_eigen", "lo_det"}
    decided = call(ctx, "curriculum.scope_decide", {"goal_id": goal_id, "phrase": "jordan form", "decision": "create"})
    assert decided["created"]["learningObjectId"].startswith("lo_goal_jordan_form")
    assert decided["created"]["learningObjectId"] in {t["learningObjectId"] for t in decided["scope"]["topics"]}


def test_without_models_the_path_reports_why_and_offers_try_again(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    goal_id = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues"})["goalId"]
    ctx.deliverable_path_client = None  # LEARNLOOP_CURRICULUM_MODELS=off in the suite
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "fluency"})
    assert view["status"] == "failed" and view["reason"] == "models_off"


def test_no_deliverable_slice_is_none_and_also_about_corrects(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    slice_ = call(ctx, "curriculum.guide_slice", {"extraction_id": "ext_book"})
    assert {key: slice_[key] for key in ("extractionId", "status")} == {"extractionId": "ext_book", "status": "none"}
    out = call(ctx, "curriculum.also_about", {"extraction_id": "ext_book", "section_id": "ch_det",
                                              "text": "really about determinants"})
    assert out["status"] == "corrected" and out["learningObjectId"] == "lo_det"
    assert json.loads(json.dumps(out))["correction"]["learnerOverride"] == "is_about"
    assert DL.SCOPE_ROUTE == "deliverable_scope_resolver"


def test_the_report_cli_prints_aggregates_and_refuses_when_off(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    goal_id = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues"})["goalId"]
    call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "fluency"})
    result = CliRunner().invoke(app, ["curriculum", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert set(out) == {"coverage", "choice", "time", "never_success"} and out["choice"]["path_lines"] == 1
    with (paths.root / "learnloop.toml").open("a", encoding="utf-8") as handle:
        handle.write("\n[curriculum]\nenabled = false\n")
    off = CliRunner().invoke(app, ["curriculum", "report", "--vault", str(paths.root)])
    assert off.exit_code == 1 and json.loads(off.output)["status"] == "invalid"
