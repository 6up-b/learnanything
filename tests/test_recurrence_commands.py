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


def test_a_blocking_cutoff_must_be_a_cosine_and_name_what_it_was_measured_on():
    """Review F7: a bare model -> cosine entry is refused; B3's entry carries
    the width, recipe and prefix it was measured on."""

    from learnloop.config.schema import RecurrenceConfig

    entry = {"cutoff": 0.31, "dims": 4096, "recipe": "hypothesis/statement@v1", "task_prefix": "retrieval-document"}
    with pytest.raises(ValueError):
        RecurrenceConfig(blocking_cutoffs={"m": 0.31})
    with pytest.raises(ValueError):
        RecurrenceConfig(blocking_cutoffs={"m": {**entry, "cutoff": 1.5}})
    with pytest.raises(ValueError):
        RecurrenceConfig(blocking_cutoffs={"m": {"cutoff": 0.31}})
    config = RecurrenceConfig(blocking_cutoffs={"m": entry})
    assert config.blocking_cutoffs["m"].dims == 4096 and config.blocking_cutoffs["m"].cutoff == 0.31


# -- the guard and the switch -------------------------------------------------------------


def _mvp010(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    return paths, load_vault(paths.root), repository


def _route_judge(root: Path, provider: str) -> None:
    """Point ai.routing.same_cause_judge at another configured profile."""

    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    head, marker, tail = text.partition("[ai.routing]\n")
    assert marker, "no [ai.routing] section"
    path.write_text(head + marker + f'same_cause_judge = "{provider}"\n' + tail, encoding="utf-8")


def test_the_guard_dry_run_sends_nothing(tmp_path):
    _paths, vault, repository = _mvp010(tmp_path)
    judge = JudgeFake()
    report = run_guard(vault, repository, caps=CAPS, dry_run=True, judge_client=judge)
    assert report["status"] == "dry_run" and report["pairs_to_judge"] == len(BUILTIN_SUITE)
    assert judge.calls == []
    assert report["current"]["passed"] is False and len(report["current"]["missing"]) == report["negatives"]


def test_a_false_merge_blocks_the_switch_and_a_fixed_judge_reruns_through_the_guard(tmp_path):
    """Review F4: the upgrade's own instruction (change the route, rerun the
    guard) works through the real rerun path: the new model is asked every
    pair; no verdict is inserted by hand."""

    paths, vault, repository = _mvp010(tmp_path)
    refused = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not refused.upgraded and "has not judged" in refused.problems[0]

    bad = BUILTIN_SUITE[0].case_id
    model = _judge_model(vault)
    report = run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(false_merge=bad, model=model))
    assert report["result"]["false_merges"] == [bad]
    blocked = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not blocked.upgraded and "false merge" in blocked.problems[0]

    # The owner moves the judge to another model and reruns the guard.
    _route_judge(paths.root, "deepseek_pro")
    vault = load_vault(paths.root)
    # The producer is the model at its reasoning effort (second review F10).
    assert _judge_model(vault) == "deepseek-v4-pro@high"
    still = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not still.upgraded and "has not judged" in still.problems[0] and model in still.problems[0]
    fixed = _guard_judge(model="deepseek-v4-pro@high")
    # The new route is metered: the owner supplies its price (unknown fails closed).
    rerun = run_guard(vault, repository, caps=CAPS, judge_client=fixed, price_per_million=1.0)
    assert rerun["judged"] == len(BUILTIN_SUITE) and len(fixed.judged) == len(BUILTIN_SUITE)
    assert guard_status(repository, judge_model="deepseek-v4-pro@high")["passed"] is True
    result = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert result.upgraded, result.problems
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.11"
    assert repository.recurrence_state()["active"] is True


def test_an_explicit_rerun_supersedes_the_same_models_false_merge(tmp_path):
    paths, vault, repository = _mvp010(tmp_path)
    model = _judge_model(vault)
    bad = BUILTIN_SUITE[0].case_id
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(false_merge=bad, model=model))
    plain = _guard_judge(model=model)
    assert run_guard(vault, repository, caps=CAPS, judge_client=plain)["judged"] == 0, "a plain run reuses"
    report = run_guard(vault, repository, caps=CAPS, judge_client=plain, rerun=True)
    assert report["judged"] == len(BUILTIN_SUITE)
    assert report["result"]["passed"] is True
    with repository.connection() as connection:
        superseding = connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE left_kind = 'planted_hypothesis' AND supersedes_id IS NOT NULL"
        ).fetchone()[0]
    assert superseding == len(BUILTIN_SUITE)
    assert upgrade_to_mvp011(paths.root, clock=CLOCK).upgraded


def _m1_case(index: int = 0):
    from learnloop.diagnosis.recurrence.guard import PlantedPair

    return PlantedPair(
        case_id=f"m1:run-1:case-{index}", expected="different", topic="lo_svd_compute", problem="pi_svd_compute_001",
        shared_answer="A = U Sigma V", statement_a=f"Believes the factors of an SVD commute ({index}).",
        statement_b=f"Forgets to transpose V because the matrix is symmetric in the example ({index}).",
        source="m1:run-1",
    )


def test_an_m1_case_from_a_run_is_required_and_its_false_merge_blocks_the_switch(tmp_path, monkeypatch):
    """Review F3: cases added with --from-run stay required; the upgrade checks them."""

    paths, vault, repository = _mvp010(tmp_path)
    model = _judge_model(vault)
    m1 = _m1_case()
    monkeypatch.setattr("learnloop.diagnosis.recurrence.guard.suite_from_run", lambda _run: [m1])

    def decide(left: str, right: str) -> str:
        if {left, right} == {m1.statement_a, m1.statement_b}:
            return "same"  # the planted false merge
        return _guard_judge(model=model).decide(left, right)

    report = run_guard(vault, repository, caps=CAPS, from_run=tmp_path / "m1-run", judge_client=JudgeFake(decide, model=model))
    assert report["registered"] == 1 and report["result"]["false_merges"] == [m1.case_id]
    # The built-in suite alone passes, but the registered case is required.
    assert guard_status(repository, suite=BUILTIN_SUITE, judge_model=model)["passed"] is True
    assert [case.case_id for case in repository_cases(repository)] == [m1.case_id]
    blocked = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not blocked.upgraded and "false merge" in blocked.problems[0]


def repository_cases(repository):
    from learnloop.diagnosis.recurrence.guard import registered_cases

    return registered_cases(repository)


def test_a_registered_case_the_judge_never_saw_blocks_the_switch(tmp_path):
    from learnloop.diagnosis.recurrence.guard import register_suite

    paths, vault, repository = _mvp010(tmp_path)
    model = _judge_model(vault)
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model=model))
    assert guard_status(repository, judge_model=model)["passed"] is True  # the built-in suite is judged ...
    register_suite(repository, [_m1_case(1)])  # ... then an M1 run's case is registered, unjudged
    assert guard_status(repository, judge_model=model)["missing"] == [_m1_case(1).case_id]
    blocked = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not blocked.upgraded and "has not judged 1 of" in blocked.problems[0]


def test_verdicts_split_across_two_models_do_not_pass_for_the_configured_one(tmp_path):
    """Review F3: B is configured, B judged only some negatives, A judged the rest."""

    paths, vault, repository = _mvp010(tmp_path)
    negatives = [case for case in BUILTIN_SUITE if case.expected == "different"]
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model="model-a"))
    _route_judge(paths.root, "deepseek_pro")
    vault = load_vault(paths.root)
    from learnloop.diagnosis.recurrence.guard import GUARD_KIND, guard_pairs
    from learnloop.matching.judge import judge_pairs

    class _ModelB:
        producer = "deepseek-v4-pro@high"

        def __call__(self, prompt, result_model, purpose):
            return result_model(verdict="different", rationale="b"), self.producer

    judge_pairs(repository, GUARD_KIND, guard_pairs(negatives[:3]), execute=_ModelB())
    status = guard_status(repository)
    assert "deepseek-v4-pro@high" in status["judge_models_seen"] and status["missing"] == []
    blocked = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not blocked.upgraded
    assert f"has not judged {len(negatives) - 3} of {len(negatives)}" in blocked.problems[0]
    assert "model-a" in blocked.problems[0], "the other model's verdicts are named as not counting"


def _codex_judge(effort: str, decide_from: JudgeFake | None = None) -> JudgeFake:
    """A Codex-like judge client: the model and reasoning effort live on its config."""

    from types import SimpleNamespace

    judge = decide_from or _guard_judge(model="gpt-5.6-sol")
    judge.model = "gpt-5.6-sol"
    judge.config = SimpleNamespace(model="gpt-5.6-sol", reasoning_effort=effort)
    return judge


def test_the_judge_producer_is_model_and_effort_so_codex_tiers_never_share_a_guard_pass(tmp_path):
    """Second review F10: codex_low and codex_medium share gpt-5.6-sol; a guard
    pass from one must not count for the other, nor its verdicts be reused."""

    from learnloop.diagnosis.recurrence.judging import producer_label

    paths, vault, repository = _mvp010(tmp_path)
    low, medium = _codex_judge("low"), _codex_judge("medium")
    assert producer_label(low) != producer_label(medium)
    assert _judge_model(vault) == producer_label(low), "the route resolves to codex_low"
    report = run_guard(vault, repository, caps=CAPS, judge_client=low)
    assert report["result"]["passed"] is True and report["judge_model"] == producer_label(low)
    _route_judge(paths.root, "codex_medium")
    vault = load_vault(paths.root)
    assert _judge_model(vault) == producer_label(medium)
    assert guard_status(repository, judge_model=producer_label(medium))["passed"] is False
    blocked = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not blocked.upgraded and "has not judged" in blocked.problems[0]
    # The medium tier is asked every pair (nothing reused across tiers).
    rerun = run_guard(vault, repository, caps=CAPS, judge_client=medium)
    assert rerun["judged"] == len(BUILTIN_SUITE)
    assert upgrade_to_mvp011(paths.root, clock=CLOCK).upgraded


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
    assert guard_status(repository, judge_model=_judge_model(vault))["passed"] is False
    refused = upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert not refused.upgraded and "rerun `learnloop recurrence guard`" in refused.problems[0]
    assert "some-other-model" in refused.problems[0]


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


# -- prepared vs active groups, and the kill switch (review F2) ----------------------------


def _merged_history(tmp_path, *, version="mvp-0.11"):
    paths, vault, repository, embedder = _history(tmp_path, version=version)
    run_backlog(vault, repository, caps=CAPS, judge_client=JudgeFake(shares_word("transpos")), embedding_client=embedder)
    return paths, load_vault(paths.root), repository


def _keys(repository):
    from learnloop.recurrence import recurrence_key

    groups = repository.recurrence_group_map()
    return {
        recurrence_key(row, groups)
        for row in repository.causal_hypotheses_for_learning_object("lo_svd_compute", statuses=("candidate", "validated"))
        if row.get("cause_scope") == "learner_state"
    }


@pytest.mark.parametrize("failing", [
    "learnloop.diagnosis.recurrence.upgrade.activate_p0_projection",
    "learnloop.diagnosis.recurrence.upgrade.rewrite_algorithm_version",
])
def test_a_failure_after_preparation_leaves_no_group_in_force(tmp_path, monkeypatch, failing):
    """Groups prepared before the config switch are never read until it lands."""

    paths, vault, repository = _merged_history(tmp_path, version="mvp-0.10")
    # Verdicts recorded at mvp-0.10 would merge three classes once active.
    from learnloop.substrate.recurrence_groups import compute_groups

    with repository.connection() as connection:
        assert compute_groups(connection).group_count == 1
    exact = _keys(repository)
    assert len(exact) == 3 and repository.recurrence_group_map() == {}
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model=_judge_model(vault)))

    def boom(*_args, **_kwargs):
        raise RuntimeError("injected failure after preparation")

    monkeypatch.setattr(failing, boom)
    with pytest.raises(RuntimeError, match="injected"):
        upgrade_to_mvp011(paths.root, clock=CLOCK)
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.10"
    state = repository.recurrence_state()
    assert state is not None and state["active"] is False and repository.recurrence_groups(), "prepared, not active"
    assert repository.recurrence_group_map() == {}, "no consumer reads prepared groups"
    assert _keys(repository) == exact
    # The next refresh at mvp-0.10 clears the prepared rows.
    from learnloop.substrate.state_sync import sync_vault_state

    sync_vault_state(load_vault(paths.root), repository)
    assert repository.recurrence_state() is None and repository.recurrence_groups() == []


def test_the_upgrade_activates_its_prepared_groups_after_the_switch(tmp_path):
    paths, vault, repository = _merged_history(tmp_path, version="mvp-0.10")
    run_guard(vault, repository, caps=CAPS, judge_client=_guard_judge(model=_judge_model(vault)))
    assert upgrade_to_mvp011(paths.root, clock=CLOCK).upgraded
    assert repository.recurrence_state()["active"] is True
    assert len(_keys(repository)) == 1, "the three reworded classes are one group now"


def test_the_kill_switch_takes_effect_at_vault_open_with_groups_already_populated(tmp_path):
    from learnloop.substrate.recurrence_groups import active_group_map
    from learnloop.substrate.state_sync import sync_vault_state

    paths, vault, repository = _merged_history(tmp_path)
    assert repository.recurrence_group_map() and len(_keys(repository)) == 1
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("[recurrence]\n", "[recurrence]\nenabled = false\n", 1),
                    encoding="utf-8")
    off = load_vault(paths.root)
    # A consumer holding the vault is gated on the effective config at once.
    assert active_group_map(off, repository) == {}
    # Opening the vault re-syncs the projection: every consumer is exact again.
    sync_vault_state(off, repository)
    assert repository.recurrence_group_map() == {} and repository.recurrence_state() is None
    assert len(_keys(repository)) == 3
