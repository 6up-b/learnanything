"""Refactor B4 (ADR-017): the figures' decision records, read back through ``learnloop why``.

The strategy's cases 3 and 4 (``docs/specs/refactor_strategy_v3.md`` §3.6), staged with fakes:

* **Case 4, pre-builds after skips:** every candidate decided is a ``figure_prebuild`` record: before any
  measured build latency the rule is ``no_measured_latency`` (no EU, propensity 0), after it
  ``sampled_eu_positive`` with the measured-wait summary (``waits_n``, ``wait_min``, its basis), the
  propensity, the posterior digest and the pass's RNG seed, from which the draws redraw exactly.
* **Filters (S7):** a pass's exclusions are one ``figure_prefetch_filter`` record, counted by rule with up to
  ten request keys each, protection exclusions included (and the fail-closed cut when protection is unreadable).
* **Build stops (S9):** the queue's in-memory notes are also ``figure_prebuild_stop`` records.
* **Case 3, a figure stored failed:** one ``figure_author`` record per attempt with typed problem codes, so the
  first attempt's problems survive the second; a dropped prediction is ``prediction_dropped`` (S10).
* **Never a decision changed:** a pass and a build whose records cannot be built or written decide, store and
  prompt exactly as with them; no record holds a goal, a passage or the author's text.

Fakes only (the judge, the author, the power reader); no model is reached.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.figures import foreground as FG
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_ledger as PL
from learnloop.figures import prefetch_model as PM
from learnloop.figures import records as FR
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from tests.figure_fixtures import (
    DENSITY_TEXT,
    EQUATION_TEXT,
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    context,
    flagship,
    half_density,
    rows,
)
from tests.test_figures_prefetch import TWO, env_for, make_vault, mains, seed_wait  # noqa: F401 - mains: autouse

GOAL = "slide p and watch the mass left of zero move"


def why(root: Path, *args: str) -> dict[str, Any]:
    result = CliRunner().invoke(app, ["why", *args, "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def records(repository: Any, kind: str | None = None) -> list[dict[str, Any]]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        sql = "SELECT * FROM decision_records" + (" WHERE kind = ?" if kind else "") + " ORDER BY created_at, id"
        found = [dict(row) for row in connection.execute(sql, (kind,) if kind else ())]
    for row in found:
        for name in ("alternatives_json", "facts_json", "versions_json"):
            row[name[:-5]] = json.loads(row.pop(name))
    return found


def assert_no_prose(repository: Any, *planted: str) -> None:
    with connect(repository.sqlite_path, read_only=True) as connection:
        dump = json.dumps([list(row) for row in connection.execute("SELECT * FROM decision_records")])
        traces = [row[0] for row in connection.execute("SELECT DISTINCT trace_id FROM decision_records")]
        for trace in traces:
            for record in provenance.read(connection, trace, limit=100000):
                assert provenance.check_no_prose(record) == []
    for text in (DENSITY_TEXT, EQUATION_TEXT, GOAL, *planted):
        assert text not in dump


def unseeded(env: PF.PrefetchEnv) -> PF.PrefetchEnv:
    return replace(env, rng=None)


# ---------------------------------------------------------------------------
# Case 4: figure_prebuild, before and after the first measured latency
# ---------------------------------------------------------------------------

def test_prebuilds_record_no_measured_latency_then_sampled_eu_positive_with_the_wait_and_seed(tmp_path):
    paths, repository, vault = make_vault(tmp_path, wait=False)
    first = PF.run_trigger(unseeded(env_for(vault, repository)),
                           PF.Trigger("offer", "tutor:qe_1", blocks=((EXTRACTION, "p3"),)))
    (skip,) = first.decisions
    assert skip["decision"] == "skip" and skip["sampled_eu"] is None

    seed_wait(repository)  # a measured pressed author call: the quick tiers' wait
    second = PF.run_trigger(unseeded(env_for(vault, repository)),
                            PF.Trigger("offer", "tutor:qe_1", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p5"))))
    (built,) = second.decisions
    assert built["decision"] == "build" and built["sampled_eu"] > 0

    before = why(paths.root, f"decision:{skip['id']}")["records"]
    (record,) = [item for item in before if item["kind"] == FR.KIND_PREBUILD]
    assert record["status"] == "excluded" and record["rule"] == PM.RULE_NO_MEASURED_LATENCY
    assert record["decided_by"] == PM.MODEL_VERSION and record["detail_table"] == "figure_prefetch_decisions"
    facts = record["facts"]
    assert facts["verdict"] == "skip" and facts["eu"] is None and facts["propensity"] == 0.0
    assert facts["waits_n"] == 0 and facts["wait_min"] is None and facts["wait_basis"] == "none"
    assert record["versions"]["posterior_digest"] == skip["posterior_digest"]
    assert record["versions"]["seed"].isdigit()

    after = why(paths.root, f"decision:{built['id']}")["records"]
    (record,) = [item for item in after if item["kind"] == FR.KIND_PREBUILD]
    assert record["status"] == "chosen" and record["rule"] == PM.RULE_SAMPLED_EU_POSITIVE
    assert record["chosen_ref"] == built["request_key"]
    facts = record["facts"]
    assert facts["verdict"] == "build" and facts["waits_n"] == 1 and facts["wait_basis"] == "author_call"
    assert facts["wait_min"] == pytest.approx(40 / 60) and facts["cost_min"] == 0.0
    assert facts["eu"] == pytest.approx(built["sampled_eu"]) and facts["propensity"] == built["propensity"]
    assert facts["p_open"] == pytest.approx(built["sampled_eu"] / facts["wait_min"])
    assert facts["builds_left"] == 10 and facts["on_mains"] is True and facts["plan_waiting"] is False
    # The second pass filtered p3 (decided for this trigger already) and its pass shares one trace.
    latest = why(paths.root, "latest", "--kind", FR.KIND_FILTER)
    (filtered,) = latest["records"]
    ((rule, count),) = filtered["facts"]["excluded_by_rule"].items()
    assert rule in (FR.FILTER_OPEN_HORIZON, FR.FILTER_DECIDED) and count == 1
    assert filtered["alternatives"] == [{"lost_by": rule, "ref": skip["request_key"]}]
    trace = why(paths.root, filtered["trace_id"])
    assert {item["kind"] for item in trace["records"]} >= {FR.KIND_FILTER, FR.KIND_PREBUILD, FR.KIND_AUTHOR}
    # The prebuild's own author call carries the pass's trace.
    assert [call["purpose"] for call in trace["model_calls"]] == ["figure_author"]
    assert_no_prose(repository)


def test_the_recorded_seed_redraws_the_pass_exactly(tmp_path):
    _paths, repository, vault = make_vault(tmp_path, two=True)
    env = unseeded(env_for(vault, repository))
    kept = [PF.Candidate("offer", "tutor:q", EXTRACTION, ["p3"], p_open_content=0.4),
            PF.Candidate("offer", "tutor:q", EXTRACTION, ["p5"]),
            PF.Candidate("offer", "tutor:q", TWO, ["q6"], p_open_content=0.9)]
    result = PF.PassResult("ok", "offer")
    PF.decide_and_log(env, kept, on_mains=True, plan_wait=None, result=result)
    rows_ = {row["id"]: row for row in result.decisions}
    found = records(repository, FR.KIND_PREBUILD)
    assert len(found) == 3 and len({record["versions"]["seed"] for record in found}) == 1
    seed = int(found[0]["versions"]["seed"])
    with connect(repository.sqlite_path, read_only=True) as connection:
        model = PL.load_model(connection, PF.plan_providers(vault), now=env.now(), offset=env.offset())
    assert model.digest() == found[0]["versions"]["posterior_digest"]  # the model the pass read
    rng = np.random.default_rng(seed)
    redrawn = [model.decide(PM.Candidate(item.trigger_kind, PF._source_key(repository, item.extraction_id),
                                         item.p_open_content, model.expected_requests(item.trigger_kind)), rng)
               for item in kept]
    for record in found:
        row = rows_[record["subject_id"]]
        again = redrawn[record["facts"]["draw_index"]]
        assert row["sampled_eu"] == again.sampled_eu and row["propensity"] == again.propensity


def test_drawing_the_seed_once_changes_nothing_statistically():
    """``default_rng()`` builds its generator from one fresh SeedSequence; ``default_rng(entropy)`` with that
    sequence's entropy is the same generator, draw for draw."""

    for _ in range(5):
        sequence = np.random.SeedSequence()
        implicit, explicit = np.random.default_rng(sequence), np.random.default_rng(sequence.entropy)
        assert np.array_equal(implicit.random(256), explicit.random(256))
        assert np.array_equal(implicit.multivariate_normal(np.zeros(3), np.eye(3), size=8, method="cholesky"),
                              explicit.multivariate_normal(np.zeros(3), np.eye(3), size=8, method="cholesky"))


def test_deferred_and_capped_decisions_are_deferred_records(tmp_path):
    _paths, repository, vault = make_vault(tmp_path, max_daily_builds=1)
    env = env_for(vault, repository)
    kept = [PF.Candidate("offer", "tutor:q", EXTRACTION, ["p3"]), PF.Candidate("offer", "tutor:q", EXTRACTION, ["p5"])]
    PF.decide_and_log(env, kept, on_mains=True, plan_wait=None, result=PF.PassResult("ok", "offer"))
    PF.decide_and_log(env, [PF.Candidate("offer", "tutor:r", EXTRACTION, ["p6"])], on_mains=False, plan_wait=None,
                      result=PF.PassResult("ok", "offer"))
    by_verdict = {record["facts"]["verdict"]: record for record in records(repository, FR.KIND_PREBUILD)}
    assert set(by_verdict) == {"build", "capped", "deferred_power"}
    assert by_verdict["build"]["status"] == "chosen"
    assert by_verdict["capped"]["status"] == "deferred" and by_verdict["capped"]["facts"]["builds_left"] == 0
    assert by_verdict["capped"]["rule"] == PM.RULE_SAMPLED_EU_POSITIVE
    assert by_verdict["deferred_power"]["status"] == "deferred"
    assert by_verdict["deferred_power"]["facts"]["on_mains"] is False
    assert {record["versions"]["seed"] for record in by_verdict.values()} == {"injected"}


# ---------------------------------------------------------------------------
# S7: the filter's exclusions
# ---------------------------------------------------------------------------

def _all_candidates() -> list[PF.Candidate]:
    return [PF.Candidate("offer", "tutor:q", EXTRACTION, [span]) for span in ("p1", "p2", "p3", "p4", "p5", "p6")] + [
        PF.Candidate("offer", "tutor:q", TWO, [span]) for span in ("q1", "q2", "q3", "q4", "q5", "q6")]


def test_protection_exclusions_are_counted_by_rule_with_ten_keys(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path, two=True)
    monkeypatch.setattr(FS, "item_passages", lambda *args, **kwargs: (frozenset(), frozenset({EXTRACTION, TWO})))
    found = _all_candidates()
    found.append(found[0])  # a duplicate in the same pass
    assert PF.filter_candidates(env_for(vault, repository), found, open_keys=set()) == []
    (record,) = records(repository, FR.KIND_FILTER)
    assert record["status"] == "excluded" and record["rule"] == "several_rules"
    assert record["facts"]["excluded_by_rule"] == {FR.FILTER_DUPLICATE: 1, FR.FILTER_ITEM_PROTECTED: 12}
    assert record["facts"]["found"] == 13 and record["facts"]["kept"] == 0
    protected = [item for item in record["alternatives"] if item["lost_by"] == FR.FILTER_ITEM_PROTECTED]
    assert len(protected) == FR.MAX_KEYS_PER_RULE
    assert [item["ref"] for item in protected] == [candidate.request_key for candidate in _all_candidates()[:10]]


def test_unreadable_protection_cuts_the_whole_pass_and_says_so(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    monkeypatch.setattr(FS, "item_passages", lambda *args, **kwargs: None)
    found = _all_candidates()[:3]
    assert PF.filter_candidates(env_for(vault, repository), found, open_keys=set()) == []
    (record,) = records(repository, FR.KIND_FILTER)
    assert record["rule"] == FR.FILTER_PROTECTION_UNAVAILABLE
    assert record["facts"]["excluded_by_rule"] == {FR.FILTER_PROTECTION_UNAVAILABLE: 3}


def test_a_pass_that_excludes_nothing_writes_no_filter_record(tmp_path):
    _paths, repository, vault = make_vault(tmp_path)
    kept = PF.filter_candidates(env_for(vault, repository), _all_candidates()[2:3], open_keys=set())
    assert len(kept) == 1 and records(repository, FR.KIND_FILTER) == []


# ---------------------------------------------------------------------------
# S9: the build queue's stops
# ---------------------------------------------------------------------------

def test_a_queue_stopped_by_foreground_work_records_what_waits(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    monkeypatch.setattr(FG, "wait_idle", lambda *args, **kwargs: False)
    result = PF.run_trigger(env_for(vault, repository),
                            PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p5"))))
    assert "yielded to foreground work: the rest wait for the next trigger" in result.notes
    (stop,) = records(repository, FR.KIND_BUILD_STOP)
    ids = [row["id"] for row in result.decisions if row["decision"] == "build"]
    assert stop["rule"] == FR.STOP_FOREGROUND and stop["status"] == "deferred"
    assert stop["subject_id"] == ids[0] and stop["facts"] == {"waiting": len(ids), "waiting_ids": ids}


@pytest.mark.parametrize("raised, rule, status", [
    (FS.FigureRefused("capped", "Today's figure budget is used."), FR.STOP_BUILD_REFUSED, "refused"),
    (RuntimeError("the build blew up"), FR.STOP_BUILD_FAILED, "failed"),
])
def test_a_refused_or_failed_prebuild_is_a_stop_record(tmp_path, monkeypatch, raised, rule, status):
    _paths, repository, vault = make_vault(tmp_path)

    def refuse(*args, **kwargs):
        raise raised

    monkeypatch.setattr(FS, "build_prefetch_figure", refuse)
    result = PF.run_trigger(env_for(vault, repository), PF.Trigger("offer", "tutor:q", blocks=((EXTRACTION, "p3"),)))
    (stop,) = records(repository, FR.KIND_BUILD_STOP)
    assert stop["rule"] == rule and stop["status"] == status and stop["subject_id"] == result.decisions[0]["id"]
    if status == "refused":
        assert stop["facts"]["refusal"] == "capped" and stop["error_type"] is None
    else:
        assert stop["error_type"] == "RuntimeError" and stop["error_where"].split(":")[1] == "refuse"
    assert "the build blew up" not in json.dumps(stop)


# ---------------------------------------------------------------------------
# Case 3: figure_author per attempt
# ---------------------------------------------------------------------------

def _pressed(tmp_path: Path, answers: list[Any]) -> tuple[Path, Any, dict[str, Any]]:
    paths, repository = build_figure_vault(tmp_path / "vault")
    shown = build(context(paths.root, author=AuthorFake(answers)))["figure"]
    return paths.root, repository, shown


def _attempts(root: Path, figure_id: str) -> list[dict[str, Any]]:
    payload = why(root, f"figure:{figure_id}", "--kind", FR.KIND_AUTHOR)
    return sorted(payload["records"], key=lambda record: record["facts"]["attempt"])


def test_a_figure_stored_failed_keeps_both_attempts_problems(tmp_path):
    root, repository, shown = _pressed(tmp_path, [half_density(), half_density()])
    assert shown["verification"] == "failed"
    first, second = _attempts(root, shown["figureId"])
    assert (first["status"], first["rule"]) == ("discarded", FR.VERIFICATION_FAILED)
    assert (second["status"], second["rule"]) == ("failed", FR.VERIFICATION_FAILED)
    for record in (first, second):
        assert record["subject_kind"] == "figure" and record["detail_table"] == "interactive_figures"
        assert record["detail_id"] == shown["figureId"] and record["facts"]["outcome"] == "failed"
        assert record["facts"]["attempts"] == 2 and record["facts"]["problems_n"] >= 1
        assert record["versions"]["prompt_version"].startswith("figure_author")
        assert record["versions"]["model"] == "fake-figure-model"
    assert first["trace_id"] == second["trace_id"]
    assert_no_prose(repository, "integrates_to_one")


def test_attempt_one_problem_survives_an_accepted_second_attempt(tmp_path):
    root, repository, shown = _pressed(tmp_path, ["{not json", flagship()])
    first, second = _attempts(root, shown["figureId"])
    assert (first["status"], first["rule"]) == ("discarded", FR.SPEC_INVALID)
    assert (second["status"], second["rule"], second["chosen_ref"]) == ("chosen", FR.ACCEPTED, shown["figureId"])
    assert second["facts"]["problems"] == [FR.ACCEPTED] and second["facts"]["author_status"] == "spec"


def test_a_failed_model_call_is_model_failed_with_its_exception_class(tmp_path):
    root, _repository, shown = _pressed(tmp_path, [RuntimeError("provider said something private"), flagship()])
    first, second = _attempts(root, shown["figureId"])
    assert (first["status"], first["rule"], first["error_type"]) == ("discarded", FR.MODEL_FAILED, "RuntimeError")
    assert second["status"] == "chosen"
    assert "provider said something private" not in json.dumps(first)


def test_label_text_is_its_own_code(tmp_path):
    labelled = flagship(demonstrates="✓ Verified by LearnLoop: the mass left of zero")
    root, repository, shown = _pressed(tmp_path, [labelled, flagship()])
    first, second = _attempts(root, shown["figureId"])
    assert (first["status"], first["rule"]) == ("discarded", FR.LABEL_TEXT)
    assert second["status"] == "chosen"
    assert_no_prose(repository, "Verified by LearnLoop")


def test_a_bad_prediction_drops_itself_and_says_so(tmp_path):
    bad = {"prompt": "If lam grows, does this rise?", "change": {"nothing_called_this": 1},
           "observe": {"kind": "direction", "expr": "p*lam"}}
    root, repository, shown = _pressed(tmp_path, [flagship(kind="illustrative", predictions=[bad])])
    (only,) = _attempts(root, shown["figureId"])
    assert (only["status"], only["rule"]) == ("chosen", FR.PREDICTION_DROPPED)
    assert only["facts"]["predictions_dropped"] == 1 and only["facts"]["problems"] == [FR.PREDICTION_DROPPED]
    assert_no_prose(repository, "If lam grows")


def test_a_refused_build_leaves_a_refused_record(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    from learnloop.vault.loader import load_vault

    monkeypatch.setattr(R.FigureRoute, "problem",
                        lambda self: R.FigureUnavailable("capped", "Today's figure budget is used."))
    with provenance.trace_scope("TRACE_REFUSED"), pytest.raises(FS.FigureRefused):
        FS.build_figure(load_vault(paths.root), repository,
                        FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), author_client=AuthorFake())
    (record,) = why(paths.root, "TRACE_REFUSED")["records"]
    assert (record["kind"], record["status"], record["rule"]) == (FR.KIND_AUTHOR, "refused", "capped")
    assert record["facts"]["attempt"] == 0 and record["facts"]["outcome"] == "capped"


# ---------------------------------------------------------------------------
# A record never changes a decision
# ---------------------------------------------------------------------------

def _masked(table_rows: list[dict[str, Any]], *names: str) -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if key not in names} for row in table_rows]


def _run(tmp_path: Path, monkeypatch: Any, *, broken: bool) -> tuple[Any, list[str]]:
    _paths, repository, vault = make_vault(tmp_path, two=True)
    if broken:
        with connect(repository.sqlite_path) as connection:
            connection.execute("DROP TABLE decision_records")
            connection.commit()

        def boom(*args, **kwargs):
            raise RuntimeError("no record")

        for name in ("prebuild_record", "build_stop_record"):
            monkeypatch.setattr(FR, name, boom)
        monkeypatch.setattr(FR.FilterLog, "record", boom)
        monkeypatch.setattr(FR.AuthorAttempts, "records", boom)
    # One pass: a later pass would read the first's author receipts, whose wall-clock durations feed W.
    monkeypatch.setattr(FS, "item_passages", lambda *args, **kwargs: (frozenset(), frozenset({TWO})))
    author = AuthorFake(["{not json", flagship(), half_density(), half_density()])
    env = env_for(vault, repository, author=author, seed=7)
    PF.run_trigger(env, PF.Trigger("offer", "tutor:a", blocks=((EXTRACTION, "p3"), (EXTRACTION, "p5"),
                                                               (TWO, "q6"))))
    monkeypatch.undo()
    return repository, author.prompts


def test_records_that_cannot_be_built_or_written_change_no_decision_build_or_prompt(tmp_path, monkeypatch):
    with_records, prompts = _run(tmp_path / "with", monkeypatch, broken=False)
    without, prompts_without = _run(tmp_path / "without", monkeypatch, broken=True)
    kinds = sorted(record["kind"] for record in records(with_records))
    assert kinds == [FR.KIND_AUTHOR] * 4 + [FR.KIND_PREBUILD] * 2 + [FR.KIND_FILTER]
    ids = ("id", "created_at", "request_id", "outcome_at")
    assert _masked(rows(with_records, "figure_prefetch_decisions"), *ids) == \
        _masked(rows(without, "figure_prefetch_decisions"), *ids)
    figure_ids = ("id", "created_at", "request_id", "verification_report_json")
    assert _masked(rows(with_records, "interactive_figures"), *figure_ids) == \
        _masked(rows(without, "interactive_figures"), *figure_ids)
    assert prompts == prompts_without


def test_a_rich_only_build_names_its_job_and_an_interrupted_build_its_error():
    from types import SimpleNamespace

    request = SimpleNamespace(origin="selection", prefetch_decision_id=None)
    rich = FR.AuthorAttempts(prompt_version="figure_author.v3")
    rich.start(1)
    rich.end(FR.BRIEF_INVALID, problems=2)
    rich.start(2)
    (first, second) = rich.records(request=request, request_id="req_1", model="m",
                                   outcome=FS.BuildOutcome(None, reused=False, rich={"rich_job_id": "job_1"}))
    assert (first.status, first.rule, first.facts["problems_n"]) == ("discarded", FR.BRIEF_INVALID, 2)
    assert (second.status, second.rule, second.subject_kind, second.subject_id) == ("chosen", FR.ACCEPTED, "job", "job_1")
    assert second.facts["outcome"] == "rich_pending" and first.trace_id == second.trace_id

    stopped = FR.AuthorAttempts()
    stopped.start(1)
    try:
        raise RuntimeError("the vault was busy: storage said something")
    except Exception as exc:  # noqa: BLE001 - the error the build raised
        error = exc
    (only,) = stopped.records(request=request, request_id="req_2", model="m", error=error)
    assert (only.status, only.rule, only.error_type) == ("failed", "interrupted", type(error).__name__)
    assert only.facts["outcome"] == FR.BUILD_ERROR and "storage said" not in json.dumps(only.as_dict())
