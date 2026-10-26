"""Curriculum C0a's RPCs and CLI: reader.correspondents, curriculum.cover / cover_job / coverage_correct,
the kill switch, T1's offer keyed by curriculum.cover, and `learnloop curriculum cover`.

Every model is a fake; nothing leaves 127.0.0.1.
"""
from __future__ import annotations

import json
import time

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.source_retrieval import section_coverage as SC
from learnloop_sidecar.errors import SidecarError
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import BOOK_EIGEN, CoverageJudgeFake, build_coverage_vault, table_counts

RPCS = ("reader.correspondents", "curriculum.cover", "curriculum.cover_job", "curriculum.coverage_correct")


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
            ("curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}),
            ("curriculum.cover_job", {"job_id": "cov_x"}),
            ("curriculum.coverage_correct", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN,
                                             "learning_object_id": "lo_eigen", "choice": "not_about"})):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "curriculum_disabled", name
    assert judge.calls == 0 and table_counts(repository) == before


def test_a_pressed_check_judges_the_sections_los_then_correspondents_read_them(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    judge = CoverageJudgeFake(treatments={"5.2 The characteristic equation": "introduces"})
    ctx = _ctx(paths, coverage_judge_client=judge)
    quiet = call(ctx, "reader.correspondents", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN,
                                                "search_fallback": False})
    assert quiet["status"] == "none" and quiet["checkableLearningObjectIds"] == ["lo_eigen"]
    started = call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    assert started["status"] == "started" and started["learningObjectIds"] == ["lo_eigen"]
    job = call(ctx, "curriculum.cover_job", {"job_id": started["job"]["jobId"]})["job"]
    assert job["state"] == "done" and job["results"][0]["status"] == "ready" and judge.calls == 1
    view = call(ctx, "reader.correspondents", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    assert view["status"] == "judged" and view["job"]["state"] == "done"
    first = view["learningObjects"][0]["sources"][0]["sections"][0]
    assert first["sectionId"] == "lay_char" and first["treatment"] == "introduces"
    # Pressing again on the same state pays nothing.
    again = call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    call(ctx, "curriculum.cover_job", {"job_id": again["job"]["jobId"]})
    assert judge.calls == 1


def test_a_correction_through_the_rpc(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths, coverage_judge_client=CoverageJudgeFake())
    call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
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


def test_a_check_with_models_off_starts_nothing(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault")
    ctx = _ctx(paths)
    out = call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    assert out["status"] == "unavailable" and out["reason"] == "models_off" and out["job"] is None
    no_lo = call(ctx, "curriculum.cover", {"extraction_id": "ext_lay", "section_id": "lay_ortho"})
    assert no_lo["status"] == "no_learning_objects"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "curriculum.cover", {"extraction_id": "ext_lay", "section_id": "lay_held"})
    assert caught.value.code == "withheld"


def test_a_failed_job_relays_an_openrouter_offer_keyed_by_curriculum_cover(tmp_path, monkeypatch):
    """T1 (redesign D): the background judgment asks as the RPC that started it; nothing is sent."""

    from learnloop.ai import plan_fallback
    from learnloop_sidecar.server import _handle
    from tests.openai_fakes import install_fake_openai

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))  # the plan is signed out
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENAI_API_KEY", "DEEPSEEK_API_KEY",
                 SC.MODELS_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    fake = install_fake_openai(monkeypatch)
    plan_fallback.revoke_all()
    try:
        paths, _repository = build_coverage_vault(
            tmp_path / "vault", config="[source_retrieval]\nllm_price_per_million = 1.0")
        ctx = context(paths.root)

        def rpc(method, params):
            return _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})

        started = rpc("curriculum.cover", {"extractionId": "ext_book", "sectionId": BOOK_EIGEN})
        result = started.get("result") or {}
        job_id = (result.get("job") or {}).get("jobId")
        assert result.get("status") == "started" and job_id, started
        deadline = time.monotonic() + 30
        while True:
            polled = rpc("curriculum.cover_job", {"jobId": job_id})
            if polled["result"]["job"]["state"] != "running" or time.monotonic() > deadline:
                break
            time.sleep(0.05)
        assert polled["result"]["job"]["state"] == "failed"
        assert polled["result"].get("fallbackOrigin") == "curriculum.cover", polled
        # Relayed once: the next read of the failed job shows no banner again.
        assert "fallbackOrigin" not in rpc("curriculum.cover_job", {"jobId": job_id})["result"]
    finally:
        plan_fallback.revoke_all()
    assert all(instance.requests == [] for instance in fake.instances)


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


# -- Codex review F8: jobs belong to their vault ----------------------------------------------------


def test_coverage_jobs_belong_to_the_vault_that_started_them(tmp_path):
    from learnloop_sidecar.handlers import correspondents as HC

    paths_a, _repository_a = build_coverage_vault(tmp_path / "a")
    paths_b, _repository_b = build_coverage_vault(tmp_path / "b")
    judge = CoverageJudgeFake()
    ctx = _ctx(paths_a, coverage_judge_client=judge)
    started = call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    HC._jobs(ctx).running.add("lo_eigen")  # vault A's job is still judging lo_eigen
    ctx.load(paths_b.root)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "curriculum.cover_job", {"job_id": started["job"]["jobId"]})
    assert caught.value.code == "not_found"
    view = call(ctx, "reader.correspondents", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN,
                                               "search_fallback": False})
    assert view["job"] is None
    again = call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    job = call(ctx, "curriculum.cover_job", {"job_id": again["job"]["jobId"]})["job"]
    assert job["results"][0]["status"] == "ready"  # not "held" by vault A's job


def test_a_vault_switch_during_a_job_keeps_nothing_in_the_old_vault(tmp_path):
    paths_a, repository_a = build_coverage_vault(tmp_path / "a")
    paths_b, repository_b = build_coverage_vault(tmp_path / "b")
    holder = {}

    class Switching(CoverageJudgeFake):
        def complete(self, request):
            answer = super().complete(request)
            holder["ctx"].load(paths_b.root)  # the learner opens vault B while A's judgment runs
            return answer

    judge = Switching()
    ctx = _ctx(paths_a, coverage_judge_client=judge)
    holder["ctx"] = ctx
    call(ctx, "curriculum.cover", {"extraction_id": "ext_book", "section_id": BOOK_EIGEN})
    assert judge.calls == 1
    for repository in (repository_a, repository_b):
        with repository.connection() as connection:
            assert connection.execute("SELECT COUNT(*) FROM section_coverage").fetchone()[0] == 0
