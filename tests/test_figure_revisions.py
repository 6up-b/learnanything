"""Reader RW5a: "not right?" versions (spec §8.1, round 3 §5D; re-review).

A note asks the figure author for a new version; it is verified like the
first, supersedes it (``supersedes_id``, ``revision_note``), and the earlier
one is kept. The Reader shows the newest shown version of each chain, so a
failed revision leaves the earlier figure in place. The request counts
against the figure caps; ``figures.revisions_enabled`` off refuses it.
"""

from __future__ import annotations

import json

import pytest

from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    half_density,
    rows,
    set_config,
)


def _better() -> dict:
    spec = flagship(kind="illustrative")
    spec["parameters"][1]["default"] = 2.0
    return spec


def test_not_right_makes_a_superseding_version_and_keeps_the_earlier(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative"), _better()])
    ctx = context(paths.root, author=author)
    first = build(ctx)["figure"]
    second = build(ctx, {"figureId": first["figureId"], "note": "the slider for λ should start at 2"},
                   rpc="reader.figure_revise")["figure"]
    assert second["supersedesId"] == first["figureId"]
    assert second["revisionNote"] == "the slider for λ should start at 2"
    assert second["versions"] == 2 and second["verification"] == "illustrative"
    assert json.loads(second["specJson"])["parameters"][1]["default"] == 2.0
    stored = rows(repository, "interactive_figures")
    assert [row["id"] for row in stored] == [first["figureId"], second["figureId"]]
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [figure["figureId"] for figure in listed] == [second["figureId"]] and listed[0]["versions"] == 2
    # The author saw the earlier version and the learner's note, and nothing else of the learner.
    context_ = author.contexts[1]
    assert context_["learner_note"] == "the slider for λ should start at 2"
    assert json.loads(context_["earlier_version"]["spec_json"]) == json.loads(first["specJson"])


def test_a_failed_revision_leaves_the_earlier_version_shown(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative"), half_density(), half_density()])
    ctx = context(paths.root, author=author)
    first = build(ctx)["figure"]
    failed = build(ctx, {"figureId": first["figureId"], "note": "make it nicer"}, rpc="reader.figure_revise")["figure"]
    assert failed["verification"] == "failed" and author.calls == 3
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [figure["figureId"] for figure in listed] == [first["figureId"]]


def test_a_revision_counts_against_the_caps(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative"), "nope", "still nope", _better()])
    ctx = context(paths.root, author=author)
    first = build(ctx)["figure"]
    build(ctx, {"figureId": first["figureId"], "note": "x"}, rpc="reader.figure_revise")
    assert author.calls == 3  # two attempts for the revision, never a third


def test_revisions_switch_off(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    first = build(ctx)["figure"]
    set_config(paths, "figures", revisions_enabled=False)
    ctx = context(paths.root, author=AuthorFake())
    assert call(ctx, "reader.prompt_contract", {})["figures"]["revisions"] is False
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": first["figureId"], "note": "x"})
    assert caught.value.code == "revisions_disabled"


def test_revising_an_unknown_figure_is_refused(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake())
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": "fig_nope", "note": "x"})
    assert caught.value.code == "not_found"


def test_the_same_note_on_the_same_figure_is_reused(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative"), _better()])
    ctx = context(paths.root, author=author)
    first = build(ctx)["figure"]
    params = {"figureId": first["figureId"], "note": "start λ at 0.1"}
    second = build(ctx, params, rpc="reader.figure_revise")
    again = build(ctx, params, rpc="reader.figure_revise")
    assert again["reused"] is True and again["figure"]["figureId"] == second["figure"]["figureId"]
    assert author.calls == 2
