"""Curriculum C0b, Codex review (``docs/reviews/curriculum-c0b-scope-path-codex-review.md``).

One test (or a few) per finding, each written to fail on the reviewed head
``b69e03225``: request-time protection on both routes (F1), a resolution published
only over the head it read (F2), the on-extract job's switches read when it runs (F3),
coverage owed by the LO's current statement (F5), coverage failures surfaced with
recovery (F6), coalescing that never loses an extraction (F7), journalled scope
publication (F8), a topic added since the last judgment shown (F9), the primary rule at
display and on *use this one instead* (F10), the learner's context in the judge's
request (F11), the prompt bound (F12), the readiness dates from DL2's parameters (F13)
and the time row (F14). Every model is a fake.
"""
from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.clock import FrozenClock
from learnloop.config.loader import load_config
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import section_coverage as SC
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault, cover_all
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import CoverageJudgeFake, hold_out


class Hooked(DeliverableFake):
    """A DeliverableFake that runs ``hook(fake)`` after answering a request of ``on``."""

    def __init__(self, hook, *, on: str = "path", **kwargs) -> None:
        super().__init__(**kwargs)
        self.hook = hook
        self.on = on

    def complete(self, request):
        answer = super().complete(request)
        if self.purposes[-1] == self.on:
            self.hook(self)
        return answer


def _scoped(paths, repository, sentence="eigenvalues for my midterm", *, depth="learn_to_use_it", due_at=None,
            fake=None):
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, sentence, due_at=due_at)["goal_id"]
    DL.resolve(load_vault(paths.root), repository, goal_id, client=fake or DeliverableFake())
    if depth:
        DL.add_input(load_vault(paths.root), repository, goal_id, "depth", text=depth)
    return goal_id, load_vault(paths.root)


def _count(repository, sql, params=()):
    with repository.connection() as connection:
        return int(connection.execute(sql, params).fetchone()[0])


def _goal_entry(paths, goal_id):
    data = read_yaml(paths.root / "profile" / "goals.yaml")
    return next(goal for goal in data["goals"] if goal["id"] == goal_id)


def _lay_char_span(vault, repository):
    reading = SC.Library(vault, repository).reading("ext_lay")
    return next(span for span, section in reading.all_spans.items()
                if section == "lay_char" and span in reading.texts)


@pytest.fixture
def scoped(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    goal_id, vault = _scoped(paths, repository)
    return paths, repository, goal_id, vault


# -- F1: protection checked at request time on both routes ----------------------------------------


def test_f1_the_path_keeps_nothing_when_a_section_is_held_out_during_its_call(scoped):
    paths, repository, goal_id, vault = scoped
    fake = Hooked(lambda _fake: hold_out(repository, "lay_char"))
    result = DP.judge(vault, repository, goal_id, client=fake)
    assert fake.calls == 1 and result.status == "stale" and result.reason == "protection_changed"
    assert _count(repository, "SELECT COUNT(*) FROM deliverable_path_sections WHERE goal_id = ?", (goal_id,)) == 0


def test_f1_a_path_retry_after_protection_changed_is_never_sent(scoped):
    paths, repository, goal_id, vault = scoped

    def hold_then_fail(fake):
        if fake.calls == 1:
            hold_out(repository, "lay_char")
            raise AIProviderUnavailable("down")

    result = DP.judge(vault, repository, goal_id, client=Hooked(hold_then_fail))
    assert result.status == "stale"
    assert _count(repository, "SELECT COUNT(*) FROM deliverable_path_sections WHERE goal_id = ?", (goal_id,)) == 0


def test_f1_the_resolver_keeps_nothing_when_its_passage_is_held_out_during_the_call(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, "my syllabus")["goal_id"]
    vault = load_vault(paths.root)
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_lay",
                 span_ids=[_lay_char_span(vault, repository)])
    fake = Hooked(lambda _fake: hold_out(repository, "lay_char"), on="scope")
    result = DL.resolve(load_vault(paths.root), repository, goal_id, client=fake)
    assert fake.calls == 1 and result.status == "unavailable" and result.reason == "protection_changed"
    assert DL.latest_resolution(repository, goal_id) is None


def test_f1_the_path_worker_reads_the_live_vault_and_checks_against_it(tmp_path):
    from learnloop_sidecar.handlers import deliverables as handler

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    goal_id, vault = _scoped(paths, repository)
    seen: dict[str, object] = {}
    real = DP.judge

    def spy(vault_, repository_, goal_id_, **kwargs):
        seen["vault"], seen["live"] = vault_, kwargs.get("live_vault")
        return real(vault_, repository_, goal_id_, **kwargs)

    ctx = context(paths.root, deliverable_inline=True, deliverable_path_client=DeliverableFake())
    live, _repository = ctx.require_vault()
    import learnloop.source_retrieval.deliverable_path as module

    original = module.judge
    module.judge = spy
    try:
        handler._judge_path(ctx, vault, repository, goal_id, "learn_to_use_it", "key")
    finally:
        module.judge = original
    assert seen["vault"] is live and seen["live"] is not None


# -- F2: an older resolution never overwrites a newer correction -----------------------------------


def test_f2_a_resolution_overtaken_by_a_newer_input_is_kept_but_never_activated(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", prerequisite=False)
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, "eigenvalues and determinants")["goal_id"]

    def correct_meanwhile(_fake):
        vault_b = load_vault(paths.root)
        DL.add_input(vault_b, repository, goal_id, "correction", text="not determinants; we skipped them")
        newer = DL.resolve(load_vault(paths.root), repository, goal_id,
                           client=DeliverableFake(excluded=("Determinants",)))
        assert newer.status == "ready"

    older = DL.resolve(load_vault(paths.root), repository, goal_id, client=Hooked(correct_meanwhile, on="scope"))
    assert older.status == "superseded" and older.message == DL.SUPERSEDED_MESSAGE
    latest = DL.latest_resolution(repository, goal_id)
    assert [entry["learning_object_id"] for entry in latest["learning_objects"]] == ["lo_eigen"]
    assert _goal_entry(paths, goal_id)["facet_scope"] == latest["facet_scope"]
    with repository.connection() as connection:
        verdicts = [row[0] for row in connection.execute(
            "SELECT verdict FROM judgment_ledger WHERE task = 'deliverable_scope' ORDER BY created_at, rowid")]
    assert verdicts.count("superseded") == 1 and verdicts.count("resolved") == 1


# -- F3: the queued on-extract job reads both switches when it runs --------------------------------


@pytest.mark.parametrize("switch", ["enabled", "coverage_on_extract"])
def test_f3_a_switch_turned_off_after_queueing_stops_the_job(tmp_path, switch):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    vault = load_vault(paths.root)  # the job's vault, loaded while on
    before = _count(repository, "SELECT COUNT(*) FROM section_coverage")
    with (paths.root / "learnloop.toml").open("a", encoding="utf-8") as handle:
        handle.write(f"\n[curriculum]\n{switch} = false\n")
    judge = CoverageJudgeFake(treatments={"5.2 The characteristic equation": "introduces"})
    out = SC.rejudge_on_extract(vault, repository, "ext_lay", client=judge)
    assert out["status"] == "switched_off" and judge.calls == 0
    assert _count(repository, "SELECT COUNT(*) FROM section_coverage") == before


def test_f3_a_switch_turned_off_between_los_stops_the_rest(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_det", "lo_eigen")
    asked = {"n": 0}

    def between() -> bool:
        asked["n"] += 1
        if asked["n"] == 2:
            with (paths.root / "learnloop.toml").open("a", encoding="utf-8") as handle:
                handle.write("\n[curriculum]\ncoverage_on_extract = false\n")
        return False

    out = SC.rejudge_on_extract(load_vault(paths.root), repository, "ext_lay", client=CoverageJudgeFake(),
                                cancelled=between)
    assert out["status"] == "switched_off" and len(out["results"]) == 1


def test_f3_judge_itself_refuses_with_the_curriculum_off(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[curriculum]\nenabled = false")
    judge = CoverageJudgeFake()
    result = SC.judge(load_vault(paths.root), repository, "lo_eigen", client=judge)
    assert result.status == "unavailable" and result.reason == "curriculum_disabled" and judge.calls == 0


# -- F5: coverage owed by the LO's current statement -----------------------------------------------


def test_f5_a_changed_statement_owes_coverage_again(scoped):
    paths, repository, goal_id, vault = scoped
    assert DP.coverage_owed(vault, repository, goal_id) == []
    before = DP.coverage_key(vault, "lo_eigen")
    path = paths.learning_object_path("linear-algebra", "lo_eigen")
    data = read_yaml(path)
    data["summary"] = "Eigenvalues: the scalars t with Ax = tx for a nonzero x."
    write_yaml(path, data)
    changed = load_vault(paths.root)
    assert DP.coverage_key(changed, "lo_eigen") != before
    assert DP.coverage_owed(changed, repository, goal_id) == ["lo_eigen"]


# -- F6: a failed first coverage is shown, with try again, and recovers ----------------------------


def test_f6_a_failed_coverage_shows_failed_and_try_again_recovers(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    fake = DeliverableFake()
    ctx = context(paths.root, deliverable_inline=True, deliverable_scope_client=fake, deliverable_path_client=fake,
                  coverage_judge_client=CoverageJudgeFake(fail=AIProviderUnavailable("down")))
    goal_id = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})["goalId"]
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    assert view["status"] == "failed" and view["message"]
    again = call(ctx, "curriculum.path", {"goal_id": goal_id})
    assert again["status"] == "failed"  # held until try again, never a quiet "no sections"
    ctx.coverage_judge_client = CoverageJudgeFake()
    recovered = call(ctx, "curriculum.path", {"goal_id": goal_id, "retry": True})
    assert recovered["status"] == "ready" and recovered["lines"]


def test_f6_a_lifted_coverage_admission_refusal_starts_the_coverage_again(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import deliverables as handler

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    fake = DeliverableFake()
    # Made and resolved without the RPC, so no coverage has run yet.
    goal_id, _vault = _scoped(paths, repository, depth=None, fake=fake)
    ctx = context(paths.root, deliverable_inline=True, deliverable_scope_client=fake, deliverable_path_client=fake,
                  coverage_judge_client=CoverageJudgeFake())
    work = handler._work(ctx)
    with work.lock:  # as a capped coverage run leaves it (the cap since lifted)
        work.covering[goal_id] = {"state": "failed", "reason": "capped", "message": "capped"}
        work.attempted[goal_id] = {("lo_eigen", DP.coverage_key(load_vault(paths.root), "lo_eigen"))}
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    assert view["status"] == "ready" and view["lines"]


# -- F7: an extraction completed while a refresh runs is never lost --------------------------------


def test_f7_a_running_job_does_not_swallow_a_new_extraction(tmp_path, monkeypatch):
    from learnloop.content.pipeline.jobs import queue_coverage_on_extract

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    queued: list[str] = []
    ctx = SimpleNamespace(repo=repository, enqueue_batch=lambda kind, jobs: queued.append(kind) or f"b{len(queued)}")
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    monkeypatch.setattr(repository, "ingest_jobs_by_types",
                        lambda kinds: [{"id": "j1", "job_type": SC.ON_EXTRACT_JOB, "status": "running"}])
    assert queue_coverage_on_extract(ctx, config, "ext_new") == "b1"
    monkeypatch.setattr(repository, "ingest_jobs_by_types", lambda kinds: [
        {"id": "j2", "job_type": SC.ON_EXTRACT_JOB, "status": "queued"},
        {"id": "j1", "job_type": SC.ON_EXTRACT_JOB, "status": "running"}])
    assert queue_coverage_on_extract(ctx, config, "ext_newer") is None  # the queued pass sees it
    assert queued == [SC.ON_EXTRACT_JOB]


# -- F8: goals.yaml and the resolution receipt never split -----------------------------------------


def test_f8_a_stop_after_the_receipt_is_finished_forward(tmp_path, monkeypatch):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, "eigenvalues")["goal_id"]
    real = DL._goal_entry_update

    def stop(*args, **kwargs):
        raise KeyboardInterrupt("the process stops here")

    monkeypatch.setattr(DL, "_goal_entry_update", stop)
    with pytest.raises(KeyboardInterrupt):
        DL.resolve(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    monkeypatch.setattr(DL, "_goal_entry_update", real)
    receipt = DL.latest_resolution(repository, goal_id)
    assert receipt is not None and _goal_entry(paths, goal_id)["facet_scope"] != receipt["facet_scope"]
    assert DL.recover_publications(paths.root, repository) is True
    assert _goal_entry(paths, goal_id)["facet_scope"] == receipt["facet_scope"]
    assert not list(DL._journal_dir(paths.root).glob("*.json"))
    assert DL.recover_publications(paths.root, repository) is False


def test_f8_a_stop_before_the_receipt_publishes_nothing(tmp_path, monkeypatch):
    from learnloop.db.stores import deliverables as store

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, "eigenvalues")["goal_id"]
    before = _goal_entry(paths, goal_id)["facet_scope"]

    def stop(*args, **kwargs):
        raise KeyboardInterrupt("the process stops here")

    monkeypatch.setattr(store, "insert_resolution", stop)
    with pytest.raises(KeyboardInterrupt):
        DL.resolve(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    monkeypatch.undo()
    assert DL.latest_resolution(repository, goal_id) is None
    assert DL.recover_publications(paths.root, repository) is False
    assert _goal_entry(paths, goal_id)["facet_scope"] == before
    assert not list(DL._journal_dir(paths.root).glob("*.json"))


def test_f8_a_goal_whose_first_input_committed_is_recovered_by_the_next_rpc(tmp_path, monkeypatch):
    paths, repository = build_deliverable_vault(tmp_path / "vault")

    def stop(*args, **kwargs):
        raise KeyboardInterrupt("the process stops here")

    monkeypatch.setattr(DL, "_goal_entry_update", stop)
    with pytest.raises(KeyboardInterrupt):
        DL.create_deliverable(load_vault(paths.root), repository, "eigenvalues for my midterm")
    monkeypatch.undo()
    with repository.connection() as connection:
        (goal_id,) = [row[0] for row in connection.execute("SELECT DISTINCT goal_id FROM deliverable_scope_inputs")]
    assert all(goal.id != goal_id for goal in load_vault(paths.root).goals)
    ctx = context(paths.root, deliverable_inline=True, deliverable_scope_client=DeliverableFake())
    scope = call(ctx, "curriculum.scope", {"goal_id": goal_id})
    assert scope["sentence"] == "eigenvalues for my midterm"


# -- F9: a topic added since the last judgment is on the path at once ------------------------------


def test_f9_a_topic_added_since_the_judgment_has_a_line_until_the_next(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen", "lo_det")
    goal_id, vault = _scoped(paths, repository, "eigenvalues")
    DP.judge(vault, repository, goal_id, client=DeliverableFake())
    DL.add_input(vault, repository, goal_id, "text", text="determinants too")
    DL.resolve(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    view = DP.path_view(load_vault(paths.root), repository, goal_id)
    assert view["status"] == "stale"
    lines = {line["learning_object_id"]: line for line in view["lines"]}
    assert set(lines) == {"lo_eigen", "lo_det"} and view["uncovered"] == []
    assert lines["lo_det"]["reason_by"] == "code" and lines["lo_det"]["section"]["treatment"] in DP.PRIMARY_TREATMENTS
    # The learner can choose on it before the next judgment.
    out = DP.override(load_vault(paths.root), repository, goal_id, "lo_det", "skip")
    assert out["override"]["learner_override"] == "skip"


# -- F10: the primary rule at display and on use-instead -------------------------------------------


def _demote(monkeypatch, ref: tuple[str, str], treatment: str = "mentions"):
    real = SC.standing

    def standing(vault, repository, library, ids):
        out = real(vault, repository, library, ids)
        for entries in out.values():
            if ref in entries:
                entries[ref] = dataclasses.replace(entries[ref], treatment=treatment)
        return out

    monkeypatch.setattr(SC, "standing", standing)


def test_f10_a_primary_no_longer_eligible_is_replaced_by_codes_choice(scoped, monkeypatch):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "5.2 The characteristic equation"}))
    _demote(monkeypatch, ("ext_lay", "lay_char"))
    line = DP.path_view(vault, repository, goal_id)["lines"][0]
    assert (line["section"]["extraction_id"], line["section"]["section_id"]) != ("ext_lay", "lay_char")
    assert line["section"]["treatment"] in DP.PRIMARY_TREATMENTS and line["label"] == "core"
    assert line["reason_by"] == "code"


def test_f10_use_instead_refuses_a_section_that_only_mentions_the_topic(scoped, monkeypatch):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"}))
    _demote(monkeypatch, ("ext_lay", "lay_char"))
    view = DP.path_view(vault, repository, goal_id)
    alternate = next(a for a in view["lines"][0]["alternates"] if a["section_id"] == "lay_char")
    assert alternate["can_use_instead"] is False
    with pytest.raises(DL.DeliverableError) as caught:
        DP.override(vault, repository, goal_id, "lo_eigen", "use_instead", section_ref="ext_lay/lay_char")
    assert "can't be the one you read" in str(caught.value)


def test_f10_a_stored_swap_to_a_section_no_longer_eligible_is_not_shown_as_core(scoped, monkeypatch):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"}))
    DP.override(vault, repository, goal_id, "lo_eigen", "use_instead", section_ref="ext_lay/lay_char")
    _demote(monkeypatch, ("ext_lay", "lay_char"))
    line = DP.path_view(vault, repository, goal_id)["lines"][0]
    assert line["section"]["section_id"] != "lay_char" and line["override"] is None


# -- F11: the learner's context reaches the judge ----------------------------------------------------


def test_f11_didnt_help_kept_comparisons_and_minutes_reach_the_judge(scoped):
    paths, repository, goal_id, vault = scoped
    span = _lay_char_span(vault, repository)
    parent = log_interaction_event(repository, kind="reader_answer_submitted", origin="system",
                                   subject_type="reader_span", subject_id=f"span:ext_lay/{span}",
                                   payload={"extraction_id": "ext_lay", "span_id": span, "answer_md": "an answer"})
    log_interaction_event(repository, kind="reader_answer_submitted", origin="system",
                          subject_type="reader_span", subject_id=f"span:ext_lay/{span}",
                          payload={"extraction_id": "ext_lay", "span_id": span, "parent_exchange_id": parent,
                                   "tutor": {"intent": "remediate"}})
    clock = FrozenClock(datetime(2026, 11, 1, 9, tzinfo=UTC))
    inputs = DP.path_inputs(vault, repository, goal_id, clock=clock)
    assert inputs.context["didnt_help"] == [{"ref": "ext_lay/lay_char", "book": "Lay",
                                             "section": "5.2 The characteristic equation"}]
    fake = DeliverableFake()
    DP.judge(vault, repository, goal_id, client=fake, inputs=inputs)
    context_sent = fake.contexts[-1]
    assert context_sent["didnt_help"][0]["ref"] == "ext_lay/lay_char"
    assert "your_comparisons" in context_sent and "minutes_available" in context_sent


def test_f11_minutes_available_are_dl1s_daily_budget_times_the_days_left(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    goal_id, vault = _scoped(paths, repository, due_at="2026-11-10")
    clock = FrozenClock(datetime(2026, 11, 1, 9, tzinfo=UTC))
    inputs = DP.path_inputs(vault, repository, goal_id, clock=clock)
    days = inputs.context["days_left"]
    assert days == 9 and inputs.context["minutes_available"] == DP.daily_minutes(vault, repository) * days
    assert DP.daily_minutes(vault, repository) == vault.config.plan.default_minutes


# -- F12: the path judge's prompt is held to its bound ---------------------------------------------


def _inflated(inputs, *, notation: int = 0, title: int = 0, copies: int = 1):
    los = []
    for entry in inputs.los:
        treatments = []
        for treatment in entry.treatments:
            for index in range(copies):
                treatments.append(dataclasses.replace(
                    treatment, section_id=f"{treatment.section_id}{'' if index == 0 else f'_{index}'}",
                    notation="n" * notation or treatment.notation,
                    title=("t" * title) if title else treatment.title))
        los.append(dataclasses.replace(entry, treatments=tuple(treatments)))
    return dataclasses.replace(inputs, los=tuple(los))


def test_f12_an_oversized_prompt_is_never_sent(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[curriculum]\nmax_prompt_tokens = 2000")
    cover_all(paths, repository, "lo_eigen")
    goal_id, vault = _scoped(paths, repository)
    big = _inflated(DP.path_inputs(vault, repository, goal_id), title=600, copies=6)
    assert len(DP.build_prompt(big, "eligible")) > 2000 * 4
    fake = DeliverableFake()
    result = DP.judge(vault, repository, goal_id, client=fake, inputs=big)
    assert result.status == "unavailable" and result.reason == "too_large" and fake.calls == 0


def test_f12_a_prompt_over_the_bound_drops_notation_before_anything_else(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", config="[curriculum]\nmax_prompt_tokens = 2000")
    cover_all(paths, repository, "lo_eigen")
    goal_id, vault = _scoped(paths, repository)
    wordy = _inflated(DP.path_inputs(vault, repository, goal_id), notation=3000)
    assert len(DP.build_prompt(wordy, "full")) > 2000 * 4
    prompt = DP.bounded_prompt(vault, wordy)
    assert prompt is not None and len(prompt) <= 2000 * 4 and "nnnnnnnn" not in prompt


# -- F13: the readiness dates come from DL2's registered parameters ---------------------------------


def test_f13_the_check_dates_follow_the_vaults_dl2_parameters(tmp_path):
    paths, repository = build_deliverable_vault(
        tmp_path / "vault", config="[capture]\ntest_me_later_days = 2\n\n[intent.recall_targets]\n"
                                   "keep_in_touch = 0.7\nremember_key_ideas = 0.85\nwork_fluently = 0.9\n"
                                   "master_tasks_like_these = 0.92\nuncommitted = 0.9")
    vault = load_vault(paths.root)
    assert DP.ready_parameters(vault) == (0.7, 2)
    clock = FrozenClock(datetime(2026, 10, 31, 9, tzinfo=UTC))
    assert DP.check_due(vault, repository, "lo_eigen", due_at=None, clock=clock) == "2026-11-02"
    from learnloop.params.parameter_registry import classify_config_path

    for path in ("capture.test_me_later_days", "intent.recall_targets.keep_in_touch"):
        assert classify_config_path(path).kind == "decision"  # registered, governed where they live


# -- F14: the time row measures reading against DL1's book-order estimate ---------------------------


def test_f14_the_time_row_counts_each_section_once_and_minutes_read_are_recorded(scoped, monkeypatch):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake())
    goal = DL.goal_of(vault, goal_id)
    row = DP.time_row(vault, repository, goal)
    assert row["minutes_read"] == 0.0 and row["sections_on_path"] == 1
    real = DP.effective_lines

    def doubled(*args, **kwargs):
        lines = real(*args, **kwargs)
        return lines + [dataclasses.replace(line, learning_object_id="lo_twin") for line in lines]

    monkeypatch.setattr(DP, "effective_lines", doubled)
    twice = DP.time_row(vault, repository, goal)
    assert twice["sections_on_path"] == 1 and twice["path_minutes_left"] == row["path_minutes_left"]
    monkeypatch.undo()
    log_interaction_event(repository, kind="reader_view_closed", origin="learner",
                          payload={"visit_id": "v1", "extraction_id": "ext_book", "active_seconds": 600,
                                   "idle_seconds": 0})
    log_interaction_event(repository, kind="reader_view_closed", origin="learner",
                          payload={"visit_id": "v2", "extraction_id": "ext_exam", "active_seconds": 900,
                                   "idle_seconds": 0})
    read = DP.time_row(vault, repository, goal)
    view = DP.path_view(vault, repository, goal_id)
    book = view["lines"][0]["section"]["extraction_id"]
    assert read["minutes_read"] == (10.0 if book == "ext_book" else 0.0)
    assert json.dumps(read)  # aggregates only
