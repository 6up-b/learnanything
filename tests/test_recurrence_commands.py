"""Slice 2 T1: the guard, the switch, the backlog, the report and rebuild/replay."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.algorithm_versions import (
    DIAGNOSIS_SPLIT_VERSIONS,
    P0_SUCCESSOR_VERSIONS,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    RECURRENCE_GROUP_VERSIONS,
)
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, effective_defaults_fingerprint
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.diagnosis.recurrence.backlog import run_backlog
from learnloop.diagnosis.recurrence.guard import BUILTIN_SUITE, guard_status, run_guard
from learnloop.diagnosis.recurrence.report import m3_report, render_markdown
from learnloop.diagnosis.recurrence.upgrade import upgrade_to_mvp011
from learnloop.ops.doctor import run_doctor
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient
from tests.helpers import set_algorithm_version
from tests.recurrence_fakes import JudgeFake, StatementFake, shares_word
from tests.split_live_helpers import at, drain_jobs, enable_embeddings, split_vault, submit

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_172"
CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))
CAPS = SpendCaps(max_candidates=100, max_pairs=100, max_retries=20, max_calls=100, max_total_tokens=500_000, max_estimated_usd=1.0)
STATEMENTS = {
    "first": "Believes V and V transpose are the same matrix.",
    "second": "Thinks the last SVD factor never needs transposing.",
    "third": "Writes V where the transpose of V belongs.",
}


def _judge_model(vault) -> str:
    from learnloop.diagnosis.recurrence.guard import configured_judge_model

    return configured_judge_model(vault) or "fake-model"


def _guard_judge(false_merge: str | None = None, *, model: str = "fake-model") -> JudgeFake:
    """Says ``different`` on every negative pair (``same`` on positives),
    except a planted false merge on the named case's statements."""

    negatives = {(case.statement_a, case.statement_b) for case in BUILTIN_SUITE if case.expected == "different"}
    target = next((case for case in BUILTIN_SUITE if case.case_id == false_merge), None)

    def decide(left: str, right: str) -> str:
        pair = {(left, right), (right, left)}
        if target is not None and pair & {(target.statement_a, target.statement_b)}:
            return "same"
        return "different" if pair & negatives else "same"

    return JudgeFake(decide, model=model)


def test_successor_vocabulary():
    assert RECURRENCE_GROUP_ALGORITHM_VERSION == "mvp-0.11"
    assert RECURRENCE_GROUP_ALGORITHM_VERSION in P0_SUCCESSOR_VERSIONS
    assert RECURRENCE_GROUP_ALGORITHM_VERSION in DIAGNOSIS_SPLIT_VERSIONS
    assert RECURRENCE_GROUP_VERSIONS == {RECURRENCE_GROUP_ALGORITHM_VERSION}


def test_defaults_fingerprint_is_recorded_for_the_successor():
    import tomllib

    from learnloop.config.schema import LearnLoopConfig
    from learnloop.config.template import DEFAULT_CONFIG_TEXT

    text = DEFAULT_CONFIG_TEXT.replace('algorithm_version = "mvp-0.9"', 'algorithm_version = "mvp-0.11"')
    config = LearnLoopConfig.model_validate(tomllib.loads(text))
    assert effective_defaults_fingerprint(config) == DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.11"]
    assert config.recurrence.blocking_cutoffs == {}, "no cosine cutoff is hand-set"


def test_a_blocking_cutoff_must_be_a_cosine():
    from learnloop.config.schema import RecurrenceConfig

    with pytest.raises(ValueError):
        RecurrenceConfig(blocking_cutoffs={"m": 1.5})
    assert RecurrenceConfig(blocking_cutoffs={"m": 0.31}).blocking_cutoffs == {"m": 0.31}


# -- the guard and the switch -------------------------------------------------------------


def _mvp010(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    return paths, load_vault(paths.root), repository


def test_the_guard_dry_run_sends_nothing(tmp_path):
    _paths, vault, repository = _mvp010(tmp_path)
    judge = JudgeFake()
    report = run_guard(vault, repository, caps=CAPS, dry_run=True, judge_client=judge)
    assert report["status"] == "dry_run" and report["pairs_to_judge"] == len(BUILTIN_SUITE)
    assert judge.calls == []
    assert report["current"]["passed"] is False and len(report["current"]["missing"]) == report["negatives"]


def test_a_false_merge_blocks_the_switch_and_a_clean_guard_allows_it(tmp_path):
    paths, vault, repository = _mvp010(tmp_path)
    refused = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not refused.upgraded and "has not judged" in refused.problems[0]

    bad = BUILTIN_SUITE[0].case_id
    model = _judge_model(vault)
    report = run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(false_merge=bad, model=model))
    assert report["result"]["false_merges"] == [bad]
    blocked = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not blocked.upgraded and "false merge" in blocked.problems[0]

    # A judge fix needs a new prompt version in production; here a corrected
    # verdict on the same question supersedes the latest one.
    from learnloop.diagnosis.recurrence.guard import GUARD_KIND, guard_pairs
    from learnloop.matching.judge import pair_input_hash

    pair = guard_pairs(BUILTIN_SUITE)[0]
    from learnloop.db.stores.judgments import append_judgment

    with repository.atomic():
        append_judgment(
            repository.connection(), task="same_cause", left_kind=pair.left.kind, left_id=pair.left.id,
            right_kind=pair.right.kind, right_id=pair.right.id, judge="llm", judge_model=model,
            prompt_version=GUARD_KIND.prompt_version, input_hash=pair_input_hash(GUARD_KIND, pair.left, pair.right),
            verdict="different", rationale="rerun",
        )
    assert guard_status(repository)["passed"] is True
    result = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert result.upgraded, result.problems
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.11"
    assert repository.recurrence_state()["active"] is True


def test_the_upgrade_is_immediate_successor_only(tmp_path):
    paths, vault, repository = _mvp010(tmp_path)
    set_algorithm_version(paths, "mvp-0.9")
    assert "only 'mvp-0.10'" in upgrade_to_mvp011(paths.root, clock=CLOCK).problems[0]
    set_algorithm_version(paths, "mvp-0.11")
    assert upgrade_to_mvp011(paths.root, clock=CLOCK).problems == ["vault is already mvp-0.11"]


def test_guard_verdicts_from_another_judge_model_do_not_open_the_switch(tmp_path):
    paths, vault, repository = _mvp010(tmp_path)
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model="some-other-model"))
    assert guard_status(repository)["passed"] is True
    refused = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not refused.upgraded and "rerun `learnloop recurrence guard`" in refused.problems[0]


def test_the_upgrade_command_takes_the_target(tmp_path):
    paths, vault, repository = _mvp010(tmp_path)
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model=_judge_model(vault)))
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", "mvp-0.11"])
    assert result.exit_code == 0, result.output
    assert "mvp-0.10 -> mvp-0.11" in result.output


def test_the_guard_reruns_only_unjudged_pairs(tmp_path):
    _paths, vault, repository = _mvp010(tmp_path)
    judge = _guard_judge()
    first = run_guard(vault, repository, caps=CAPS, judge_client=judge)
    assert first["judged"] == len(BUILTIN_SUITE) and first["result"]["passed"]
    assert first["result"]["positives_merged"] == first["result"]["positives"]
    second = run_guard(vault, repository, caps=CAPS, judge_client=judge)
    assert second["pairs_to_judge"] == 0 and second["judged"] == 0


def test_the_guard_stops_at_its_call_cap(tmp_path):
    _paths, vault, repository = _mvp010(tmp_path)
    caps = SpendCaps(max_candidates=100, max_pairs=100, max_retries=2, max_calls=3, max_total_tokens=500_000, max_estimated_usd=1.0)
    report = run_guard(vault, repository, caps=caps, judge_client=_guard_judge())
    assert report["status"] == "over_budget" and report.get("judged") is None


# -- the backlog ---------------------------------------------------------------------------


def _history(tmp_path, *, version="mvp-0.11"):
    """Three reworded diagnosed failures, judged by nobody yet."""

    paths, _vault, repository = split_vault(tmp_path, version=version, seed=False,
                                            config="[recurrence]\njudge_enabled = false")
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    vault = load_vault(paths.root)
    client = StatementFake(STATEMENTS)
    embedder = FakeEmbeddingClient()
    for offset, (item_id, answer) in enumerate((
        ("pi_svd_compute_001", "A = U Sigma V first"),
        ("pi_svd_compute_002", "B = U Sigma V second"),
        ("pi_svd_compute_001", "A = U Sigma V third"),
    )):
        submit(vault, repository, client, item_id=item_id, answer=answer, when=at(10 + 2 * offset))
        drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(11 + 2 * offset)))
    return paths, vault, repository, embedder


def test_the_backlog_dry_run_plans_and_sends_nothing(tmp_path):
    _paths, vault, repository, embedder = _history(tmp_path)
    judge = JudgeFake(shares_word("transpos"))
    calls_before = embedder.calls
    report = run_backlog(vault, repository, caps=CAPS, dry_run=True, judge_client=judge, embedding_client=embedder)
    assert report["status"] == "dry_run"
    plan = report["plan"]
    assert plan["pairs_to_judge"] >= 2 and plan["admissible"]
    assert judge.calls == [] and embedder.calls == calls_before


def test_the_backlog_judges_merges_and_reruns_idempotently(tmp_path):
    _paths, vault, repository, embedder = _history(tmp_path)
    assert repository.recurrence_group_map() == {}
    judge = JudgeFake(shares_word("transpos"))
    report = run_backlog(vault, repository, caps=CAPS, judge_client=judge, embedding_client=embedder)
    assert report["status"] == "complete", report
    assert report["judged"] >= 2 and report["verdicts"]["same"] >= 2
    assert report["groups"]["group_count"] == 1
    with repository.connection() as connection:
        receipted = {
            row[0] for row in connection.execute(
                "SELECT purpose FROM model_call_receipts WHERE owner_kind = 'recurrence_backlog' AND parent_call_id IS NULL"
            )
        }
    assert "same_cause_judgment" in receipted, "every paid judge call is receipted under the command"
    again = run_backlog(vault, repository, caps=CAPS, judge_client=judge, embedding_client=embedder)
    assert again["judged"] == 0 and again["plan"]["pairs_to_judge"] == 0


def test_the_backlog_refuses_over_its_caps(tmp_path):
    _paths, vault, repository, embedder = _history(tmp_path)
    caps = SpendCaps(max_candidates=1, max_pairs=1, max_retries=0, max_calls=1, max_total_tokens=500_000, max_estimated_usd=1.0)
    judge = JudgeFake(shares_word("transpos"))
    report = run_backlog(vault, repository, caps=caps, judge_client=judge, embedding_client=embedder)
    assert report["status"] == "over_budget" and judge.calls == []


def test_the_backlog_needs_embeddings(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.11", seed=False)
    report = run_backlog(load_vault(paths.root), repository, caps=CAPS, dry_run=True)
    assert report["status"] == "invalid"


# -- rebuild and replay -----------------------------------------------------------------------


@pytest.mark.durability
def test_rebuild_makes_no_model_call_and_is_a_fixed_point(tmp_path, monkeypatch):
    _paths, vault, repository, embedder = _history(tmp_path)
    run_backlog(vault, repository, caps=CAPS, judge_client=JudgeFake(shares_word("transpos")), embedding_client=embedder)
    groups_before = repository.recurrence_groups()
    assert groups_before

    def forbidden(*_args, **_kwargs):  # pragma: no cover - the assertion is that it never runs
        raise AssertionError("replay made a model call")

    # Replay has no client: building one, judging or embedding would fail.
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr("learnloop.diagnosis.recurrence.live._judge_attempt", forbidden)
    monkeypatch.setattr("learnloop.matching.judge.judge_pairs", forbidden)
    monkeypatch.setattr(FakeEmbeddingClient, "embed", forbidden)
    derived = sorted(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')) for table in derived}

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second
    assert repository.recurrence_groups() == groups_before


@pytest.mark.durability
def test_a_vault_with_no_merges_rebuilds_with_an_empty_projection(tmp_path):
    _paths, vault, repository, _embedder = _history(tmp_path)
    result = rebuild_all_derived_state(vault, repository, clock=CLOCK)
    replayer = next(row for row in result.replayers if row.name == "recurrence_groups")
    assert replayer.details["member_count"] == 0
    assert repository.recurrence_groups() == [] and repository.recurrence_review("refused_union") == []


def test_the_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8: upgrade the migration-head fixture, FK check, doctor,
    a second idempotent rebuild."""

    from tests.helpers import _set_algorithm_version_at

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    _set_algorithm_version_at(root, "mvp-0.10")
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model=_judge_model(vault)))
    result = upgrade_to_mvp011(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [issue for issue in run_doctor(root).issues if issue.severity == "error" and issue.code.startswith(("sqlite", "diagnosis", "state"))]
    assert errors == []
    derived = set(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')) for table in sorted(derived)}

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second


# -- the M3 report ---------------------------------------------------------------------------


def test_the_m3_report_reads_ledgers_only(tmp_path, monkeypatch):
    _paths, vault, repository, embedder = _history(tmp_path)
    run_backlog(vault, repository, caps=CAPS, judge_client=JudgeFake(shares_word("transpos")), embedding_client=embedder)

    def forbidden(*_args, **_kwargs):  # pragma: no cover
        raise AssertionError("the report made a model call")

    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr(FakeEmbeddingClient, "embed", forbidden)
    report = m3_report(vault, repository, audit_sample=5)
    assert report["group_precision"]["merged_groups"] == 1
    assert report["group_precision"]["audit_sample"][0]["statements"]
    assert report["review_volume"]["same_cause_verdicts_by_judge"]["llm"]["same"] >= 2
    text = render_markdown(report)
    assert "Audit sample" in text and "Escalation usefulness" in text
    json.dumps(report, default=str)


def test_the_cli_report_and_groups_commands(tmp_path):
    paths, vault, repository, embedder = _history(tmp_path)
    run_backlog(vault, repository, caps=CAPS, judge_client=JudgeFake(shares_word("transpos")), embedding_client=embedder)
    out = tmp_path / "m3.md"
    result = CliRunner().invoke(app, ["recurrence", "report", "--vault", str(paths.root), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists() and out.with_suffix(".json").exists()
    listed = CliRunner().invoke(app, ["recurrence", "groups", "--vault", str(paths.root), "--json"])
    assert listed.exit_code == 0, listed.output
    assert len(json.loads(listed.output)["groups"]) == 1


def test_the_cli_backlog_and_guard_dry_runs(tmp_path):
    paths, _vault, _repository, _embedder = _history(tmp_path)
    backlog = CliRunner().invoke(app, [
        "embeddings", "adjudicate", "--vault", str(paths.root), "--task", "same_cause", "--backlog", "--dry-run", "--json",
    ])
    assert backlog.exit_code == 0, backlog.output
    assert json.loads(backlog.output)["status"] == "dry_run"
    guard = CliRunner().invoke(app, ["recurrence", "guard", "--vault", str(paths.root), "--dry-run", "--json"])
    assert guard.exit_code == 0, guard.output
    assert json.loads(guard.output)["pairs_to_judge"] == len(BUILTIN_SUITE)
    wrong = CliRunner().invoke(app, ["embeddings", "adjudicate", "--vault", str(paths.root), "--task", "isomorph", "--backlog"])
    assert wrong.exit_code == 1
