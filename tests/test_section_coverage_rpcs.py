"""Curriculum C0a's RPCs and CLI: reader.correspondents, curriculum.coverage_correct, the kill switch, and
`learnloop curriculum cover`.

Every model is a fake; nothing leaves 127.0.0.1.
"""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.source_retrieval import section_coverage as SC
from learnloop_sidecar.errors import SidecarError
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import (
    BOOK_EIGEN,
    CoverageJudgeFake,
    build_coverage_vault,
    judge_section,
    table_counts,
)

RPCS = ("reader.correspondents", "curriculum.coverage_correct")


def _ctx(paths, **attrs):
    return context(paths.root, coverage_inline=True, **attrs)


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.correspondents import CORRESPONDENT_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert CORRESPONDENT_RPCS == RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RPCS)


def test_switched_off_every_rpc_refuses_and_nothing_is_written(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", config="[curriculum]\nenabled = false")
    judge = CoverageJudgeFake()
    ctx = _ctx(paths, coverage_judge_client=judge)
    before = table_counts(repository)
    for name, params in (
            ("reader.correspondents", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}),
            ("curriculum.coverage_correct", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN,
                                             "learning_object_id": "lo_eigen", "choice": "not_about"})):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "curriculum_disabled", name
    assert judge.calls == 0 and table_counts(repository) == before


def test_a_correction_through_the_rpc(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths, coverage_judge_client=CoverageJudgeFake())
    judge_section(ctx, {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    out = call(ctx, "curriculum.coverage_correct", {"extraction_id": "ext_lay", "section_id": "lay_char",
                                                    "learning_object_id": "lo_eigen", "choice": "not_about"})
    assert out["correction"]["learnerOverride"] == "not_about"
    view = call(ctx, "reader.correspondents", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN,
                                               "search_fallback": False})
    listed = [section["sectionId"] for group in view["learningObjects"] for source in group["sources"]
              for section in source["sections"]]
    assert "lay_char" not in listed
    with pytest.raises(SidecarError) as caught:
        call(ctx, "curriculum.coverage_correct", {"extraction_id": "ext_lay", "section_id": "lay_held",
                                                  "learning_object_id": "lo_eigen", "choice": "is_about"})
    assert caught.value.code == "withheld"


# -- learnloop curriculum cover ------------------------------------------------------------------


def test_the_cli_dry_run_calls_and_writes_nothing(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    before = table_counts(repository)
    result = CliRunner().invoke(app, ["curriculum", "cover", "--vault", str(paths.root), "--source", "src_lay",
                                      "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["status"] == "dry_run" and out["calls"] == 0
    planned = {entry["learning_object_id"]: entry for entry in out["learning_objects"]}
    assert planned["lo_eigen"]["status"] == "planned" and planned["lo_eigen"]["here"] >= 1
    assert table_counts(repository) == before


def test_cover_source_judges_and_caps_a_metered_run(tmp_path):
    from learnloop.vault.loader import load_vault

    paths, repository = build_coverage_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    judge = CoverageJudgeFake()
    out = SC.cover_source(vault, repository, "ext_lay", client=judge)
    assert out["status"] == "done" and judge.calls >= 1
    assert all(entry["status"] in ("ready", "not_in_this_source", "fresh") for entry in out["learning_objects"])
    again = SC.cover_source(vault, repository, "ext_lay", client=judge)
    assert judge.calls == out["calls"] and all(entry["status"] in ("fresh", "not_in_this_source")
                                               for entry in again["learning_objects"])
    # A metered route held to a tiny per-run cap: refused before its first call.
    paths2, repository2 = build_coverage_vault(
        tmp_path / "vault2", config="[source_retrieval]\nllm_price_per_million = 1000.0\n\n"
                                    "[curriculum]\ncover_max_cost_usd = 0.0001")
    metered = CoverageJudgeFake(provider_type="openai_compatible")
    capped = SC.cover_source(load_vault(paths2.root), repository2, "ext_lay", client=metered)
    assert capped["status"] == "capped" and metered.calls == 0


def test_cover_source_refuses_a_withheld_reading(tmp_path):
    from learnloop.vault.loader import load_vault

    paths, repository = build_coverage_vault(tmp_path / "vault")
    out = SC.cover_source(load_vault(paths.root), repository, "ext_exam", client=CoverageJudgeFake())
    assert out["status"] == "withheld" and out["calls"] == 0

