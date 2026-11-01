"""Curriculum C0b: curriculum.coverage_on_extract (spec_deliverable_curriculum_v1 §6.3, §12.1).

A completed extraction queues one background job (``curriculum_coverage_on_extract``)
that judges again the LOs already covered, so a new reading's sections join their
coverage. Quiet (plan only: no OpenRouter offer, no grant honoured), coalesced per LO
(a fresh state pays nothing), one live job at a time, behind its kill switch.
"""
from __future__ import annotations

from types import SimpleNamespace

from learnloop.ai import plan_fallback
from learnloop.config.loader import load_config
from learnloop.source_retrieval import section_coverage as SC
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import build_deliverable_vault, cover_all
from tests.section_coverage_fixtures import BIG, CoverageJudgeFake
from tests.source_retrieval_fakes import seed_source


def _queue_ctx(repository):
    queued: list[tuple[str, list]] = []
    ctx = SimpleNamespace(repo=repository, enqueue_batch=lambda kind, jobs: queued.append((kind, jobs)) or f"b{len(queued)}")
    return ctx, queued


def test_an_extraction_queues_the_job_only_while_both_switches_are_on(tmp_path):
    from learnloop.content.pipeline.jobs import queue_coverage_on_extract

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    ctx, queued = _queue_ctx(repository)
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    assert config.curriculum.coverage_on_extract is True
    # Nothing covered yet: nothing to re-judge, nothing queued.
    assert queue_coverage_on_extract(ctx, config, "ext_book") is None and queued == []
    cover_all(paths, repository, "lo_eigen")
    assert queue_coverage_on_extract(ctx, config, "ext_lay") == "b1"
    assert [kind for kind, _jobs in queued] == [SC.ON_EXTRACT_JOB]
    off = config.model_copy(update={"curriculum": config.curriculum.model_copy(update={"coverage_on_extract": False})})
    assert queue_coverage_on_extract(ctx, off, "ext_lay") is None
    disabled = config.model_copy(update={"curriculum": config.curriculum.model_copy(update={"enabled": False})})
    assert queue_coverage_on_extract(ctx, disabled, "ext_lay") is None
    assert len(queued) == 1


def test_one_live_job_at_a_time(tmp_path, monkeypatch):
    from learnloop.content.pipeline.jobs import queue_coverage_on_extract

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    ctx, queued = _queue_ctx(repository)
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    monkeypatch.setattr(repository, "ingest_jobs_by_types",
                        lambda kinds: [{"id": "j1", "job_type": SC.ON_EXTRACT_JOB, "status": "queued"}])
    assert queue_coverage_on_extract(ctx, config, "ext_lay") is None and queued == []


def test_the_job_rejudges_covered_los_a_new_book_joins_and_a_fresh_state_pays_nothing(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    vault = load_vault(paths.root)
    judge = CoverageJudgeFake()
    unchanged = SC.rejudge_on_extract(vault, repository, "ext_book", client=judge)
    assert unchanged["learning_objects"] == ["lo_eigen"] and judge.calls == 0  # fresh: no call
    seed_source(repository, source_id="src_big", revision_id="rev_big", extraction_id="ext_big", title="Big Book",
                units=dict(list(BIG.items())[:2]), furniture=False)
    from learnloop.vault.writer import upsert_source_set
    from learnloop.vault.yaml_io import read_yaml

    current = read_yaml(paths.root / "sources" / "source_sets.yaml") if (paths.root / "sources" / "source_sets.yaml").exists() else None
    members = [{"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
               {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
               {"source_id": "src_lay", "revision_id": "rev_lay", "default_role": "primary_textbook"},
               {"source_id": "src_big", "revision_id": "rev_big", "default_role": "primary_textbook"}]
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
                                   "members": members})
    assert current is None or current
    out = SC.rejudge_on_extract(load_vault(paths.root), repository, "ext_big", client=judge)
    assert judge.calls == 1 and out["results"][0]["status"] == "ready"
    with repository.connection() as connection:
        rows = connection.execute("SELECT DISTINCT extraction_id FROM section_coverage WHERE learning_object_id = "
                                  "'lo_eigen' AND learner_override IS NULL").fetchall()
    assert "ext_big" in {row[0] for row in rows}


def test_the_job_runs_quiet_and_never_offers_openrouter(tmp_path, monkeypatch):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    seen: list[bool] = []
    real = SC.judge

    def spy(*args, **kwargs):
        seen.append(plan_fallback.offers_suppressed())
        return real(*args, **kwargs)

    monkeypatch.setattr(SC, "judge", spy)
    out = SC.rejudge_on_extract(load_vault(paths.root), repository, "ext_lay")
    assert seen == [True]
    # Without a fake the models are off (the suite): the job waits, it never asks.
    assert out["status"] in ("waiting", "done")


def test_the_handler_is_registered_and_known(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs, runner

    assert jobs.DEFAULT_HANDLERS[SC.ON_EXTRACT_JOB] is jobs.handle_curriculum_coverage_on_extract
    assert SC.ON_EXTRACT_JOB in runner.KNOWN_JOB_TYPES
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    calls: list[str] = []
    monkeypatch.setattr(SC, "rejudge_on_extract", lambda vault, repo, extraction_id, **kw: calls.append(extraction_id)
                        or {"job": SC.ON_EXTRACT_JOB, "status": "done", "results": []})
    ctx = SimpleNamespace(payload={"extraction_id": "ext_lay"}, vault_root=paths.root, repo=repository,
                          report=lambda *a, **k: None, cancelled=lambda: False)
    assert jobs.handle_curriculum_coverage_on_extract(ctx)["status"] == "done" and calls == ["ext_lay"]
