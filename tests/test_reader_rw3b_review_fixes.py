"""Reader workbench RW3b, Codex review fixes (docs/reviews/reader-rw3b-codex-review.md).

Each test reproduces one finding on the real functions (fakes for every
model): F1 a running discovery stops when its switch is turned off and the
vault reloaded; F2 nothing is retrieved deeply for a judge that cannot run,
and retrieval's metered requests reserve under the cue envelope; F3 failed
requests and retries count against the per-open cap; F4 only a cue the
density budget admits is randomized; F9 holding-pen candidates, recurrence
groups and claims needing an independent check are targets; F11 repeated
impressions of one link are one unit and a repeated outcome is no sample;
F12 "Open" shows the cited answer and the learner's own words; F13 the dry
run carries a spend plan. Tap resolution without a rebuild is pinned too.
"""

from __future__ import annotations

import threading

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.db.stores import reader_cue_links as store
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.reader.reader_report import _holdout_estimate, build_reader_report
from learnloop.source_retrieval import passage_cues as PC
from tests.passage_cue_fakes import (
    CueJudgeFake,
    build_cue_vault,
    guide_cue,
    loaded,
    seed_link,
    set_config,
    snake,
    target,
)
from tests.recap_fixtures import call, context


def _links(repository, extraction_id: str = "ext_text") -> list[dict]:
    with repository.connection() as connection:
        return store.links_for_extraction(connection, extraction_id)


def _more_targets(repository, count: int) -> None:
    for index in range(count):
        repository.insert_misconception(id=f"mis_more_{index}", learning_object_id="lo_matrices", status="active",
                                        statement=f"Swapping rows of a matrix keeps its determinant, variant {index}")


# -- F1: the kill switch stops a running discovery ------------------------------------------------


class _BlockingJudge(CueJudgeFake):
    """Holds its first request until released (the owner's switch flips meanwhile)."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def complete(self, request):
        if not self.entered.is_set():
            self.entered.set()
            assert self.release.wait(10)
        return super().complete(request)


def test_discovery_stops_before_its_next_request_once_switched_off_and_reloaded(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    ctx = context(paths.root)
    judge = _BlockingJudge()
    ctx.cue_judge_client = judge
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert judge.entered.wait(10), "the first judge request was sent"
    set_config(paths, "cues", discovery_enabled=False)
    ctx.reload()
    judge.release.set()
    stored = ctx.cue_discovery_jobs.get(job["job_id"])
    assert stored.done.wait(20)
    assert len(judge.prompts) == 1, "no request after the switch was turned off"
    assert stored.result["status"] == "cancelled"


def test_a_reload_cancels_the_running_job_and_a_new_ask_starts_one_on_the_new_vault(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 2)
    ctx = context(paths.root)
    judge = _BlockingJudge()
    ctx.cue_judge_client = judge
    first = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert judge.entered.wait(10)
    ctx.reload()  # same switches, a new generation: the old job ends at its next check
    second = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert second["job_id"] != first["job_id"]
    judge.release.set()
    old = ctx.cue_discovery_jobs.get(first["job_id"])
    assert old.done.wait(20) and old.result["status"] == "cancelled"
    assert ctx.cue_discovery_jobs.get(second["job_id"]).done.wait(20)


# -- F2: no paid retrieval for a judge that cannot run; retrieval under the cue envelope ----------


def test_nothing_is_retrieved_deeply_for_a_judge_that_cannot_run(tmp_path, monkeypatch):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    deep: list[bool] = []
    real = PC.search_spans

    def spy(*args, **kwargs):
        deep.append(bool(kwargs.get("deep")))
        return real(*args, **kwargs)

    monkeypatch.setattr(PC, "search_spans", spy)
    vault = loaded(paths)
    # No client and LEARNLOOP_CUE_JUDGE_MODELS=off (conftest): the judge is unavailable.
    out = PC.discover(vault, repository, "ext_text")
    assert {entry["status"] for entry in out["targets"]} == {"unavailable"}
    assert deep == [], "no shortlist (and no query embedding) for a judge that cannot run"
    # A metered judge with today's allowance used up: refused before retrieval too.
    set_config(paths, "source_retrieval", llm_price_per_million=1000.0)
    set_config(paths, "cues", max_daily_cost_usd=0.0)
    out = PC.discover(loaded(paths), repository, "ext_text", client=CueJudgeFake(provider_type="openai_chat"))
    assert out["targets"][0]["status"] == "capped" and deep == []


def test_retrievals_metered_requests_reserve_under_the_cue_envelope(tmp_path, monkeypatch):
    """With the cue allowance at $0, a metered request inside retrieval (the
    query embedding) is refused; the Codex judge still runs on keyword lists."""

    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", max_daily_cost_usd=0.0)
    refused: list[str] = []
    real = PC.search_spans

    def metered_step(*args, **kwargs):
        budget = kwargs.get("budget") or SpendBudget(SpendCaps())
        try:
            with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.001)):
                refused.append("admitted")
        except SpendLimitExceeded as exc:
            refused.append(str(exc))
        return real(*args, **kwargs)

    monkeypatch.setattr(PC, "search_spans", metered_step)
    out = PC.discover(loaded(paths), repository, "ext_text", client=CueJudgeFake(provider_type="codex_sdk"))
    assert refused and refused[0].startswith(PC.JUDGE_ENVELOPE)
    assert out["targets"][0]["status"] == "judged" and _links(repository)


def test_a_metered_judge_request_reserves_once_under_the_cue_envelope(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "source_retrieval", llm_price_per_million=1.0)
    set_config(paths, "cues", max_daily_cost_usd=5.0)
    out = PC.discover(loaded(paths), repository, "ext_text", client=CueJudgeFake(provider_type="openai_chat"))
    assert out["targets"][0]["status"] == "judged" and out["calls"] == 1
    with repository.connection() as connection:
        reserved = connection.execute("SELECT COUNT(*) FROM source_service_spend WHERE envelope = ?",
                                      (PC.JUDGE_ENVELOPE,)).fetchone()[0]
    assert reserved == 1, "one reservation for one metered request (never one per active copy of the envelope)"


# -- F3: every admitted request counts, failures and retries included ----------------------------


def test_failed_requests_count_against_the_per_open_cap(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    set_config(paths, "cues", max_calls_per_source_open=1)
    judge = CueJudgeFake(fail=True)
    out = PC.discover(loaded(paths), repository, "ext_text", client=judge)
    assert len(judge.prompts) == 1, "one request in all, its retry refused by the cap"
    assert out["calls"] == 1 and out["usage"]["requests"] == 1 and out["judged"] == 0
    assert [entry["status"] for entry in out["targets"]].count("capped") >= 3


class _FailsOnce(CueJudgeFake):
    def complete(self, request):
        if not self.prompts:
            self.prompts.append(request.prompt)
            raise AIProviderUnavailable("transient")
        return super().complete(request)


def test_a_retry_is_a_second_request_and_reported_apart_from_judgments(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    judge = _FailsOnce()
    out = PC.discover(loaded(paths), repository, "ext_text", client=judge)
    assert len(judge.prompts) == 2
    assert out["calls"] == 2 and out["usage"]["retries"] == 1 and out["judged"] == 1
    assert out["usage"]["cost_basis"] == "estimated_only"  # the subscription stays exempt from the dollar cap


# -- F4: only a cue the budget admits is randomized ------------------------------------------------


def _merged(tmp_path, monkeypatch, *, rate, density, targets, links):
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    set_config(paths, "cues", holdout_rate=rate, density=density)
    ids = [seed_link(repository, t, span) for t, span in links]
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: list(targets))
    vault = loaded(paths)
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    return paths, repository, cues, ids


def test_with_density_off_nothing_is_held_out(tmp_path, monkeypatch):
    targets = [target("hypothesis", f"h{index}", p_open=0.5) for index in range(4)]
    _p, _r, cues, _ids = _merged(tmp_path, monkeypatch, rate=0.95, density="off", targets=targets,
                                 links=list(zip(targets, ["t1", "t3", "t5", "t7"])))
    assert cues["marks"] == [] and cues["discovery"]["held_out"] == []
    assert all("propensity" not in cue for cue in cues["discovery"]["suppressed"])


def test_a_cue_the_budget_cuts_is_never_a_control_and_a_held_out_cue_keeps_its_slot(tmp_path, monkeypatch):
    targets = [target("hypothesis", f"h{index}", p_open=0.9 - 0.1 * index) for index in range(3)]
    _p, _r, cues, ids = _merged(tmp_path, monkeypatch, rate=0.95, density="fewer", targets=targets,
                                links=list(zip(targets, ["t1", "t2", "t3"])))
    # One slot in ch5: the best cue is eligible; the others are density cuts, never held out.
    eligible = [*cues["marks"], *cues["discovery"]["held_out"]]
    assert len([cue for cue in eligible if cue["section_id"] == "ch5"]) == 1
    assert {cue["link_id"] for cue in cues["discovery"]["suppressed"]} == set(ids[1:])
    held = cues["discovery"]["held_out"]
    if held:  # the slot stays empty: no cut cue is promoted into it
        assert not [mark for mark in cues["marks"] if mark["section_id"] == "ch5"]
        assert "rank" in held[0]


def test_a_held_out_cue_the_reader_would_have_spaced_out_is_recorded_as_spacing(tmp_path, monkeypatch):
    targets = [target("hypothesis", f"h{index}", p_open=0.9 - 0.1 * index) for index in range(6)]
    paths, repository, _cues, _ids = _merged(tmp_path, monkeypatch, rate=0.95, density="more", targets=targets,
                                             links=list(zip(targets, ["t1", "t2", "t3", "t5", "t7", "t8"])))
    ctx = context(paths.root)
    plan = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))
    held = plan["cues"]["discovery"]["held_out"]
    assert len(held) >= 2
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1",
                                         "plan_id": plan["cues"]["discovery"]["plan_id"], "entries": [
        {"cue_id": held[0]["cue_id"], "shown": False},
        {"cue_id": held[1]["cue_id"], "shown": False, "reason": "spacing"}]})
    with repository.connection() as connection:
        rows = {row["cue_id"]: row for row in store.impressions(connection)}
    assert rows[held[0]["cue_id"]]["suppressed_reason"] == "holdout"
    assert rows[held[1]["cue_id"]]["suppressed_reason"] == "spacing"


# -- F9: the targets the spec names ----------------------------------------------------------------


def test_holding_pen_candidates_and_recurrence_groups_are_targets(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    repository.insert_misconception_candidate(
        id="cand_once", learning_object_id="lo_matrices", statement="A row swap changes nothing about det",
        statement_normalized="a row swap changes nothing about det", facet_ids=["facet_det"])
    repository.insert_misconception_candidate(
        id="cand_twice", learning_object_id="lo_matrices", statement="Eigenvalues are always the diagonal",
        statement_normalized="eigenvalues are always the diagonal", occurrence_count=2)
    targets = {t.kind: t for t in PC.cue_targets(loaded(paths), repository, "ext_text")}
    assert targets["hypothesis"].statement == "A row swap changes nothing about det"
    assert targets["hypothesis"].p_open_source == "candidate_lifecycle" and targets["hypothesis"].open
    assert targets["hypothesis"].facet_ids == ("facet_det",)
    assert targets["recurrence_group"].statement == "Eigenvalues are always the diagonal"
    assert targets["recurrence_group"].id.startswith("rg_") and targets["recurrence_group"].open


def test_a_candidate_a_durable_misconception_already_states_is_not_a_second_target(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    repository.insert_misconception_candidate(
        id="cand_dup", learning_object_id="lo_matrices", statement=PC.cue_targets(
            loaded(paths), repository, "ext_text")[0].statement, statement_normalized="dup")
    assert [t.kind for t in PC.cue_targets(loaded(paths), repository, "ext_text")] == ["misconception"]


def test_a_claim_needing_an_independent_check_is_a_try_first_target(tmp_path, monkeypatch):
    paths, repository, spans = build_cue_vault(tmp_path / "v", misconception=False)
    vault = loaded(paths)
    lo = vault.learning_objects["lo_matrices"]
    from learnloop.vault.models import learning_object_facet_union

    facet = vault.canonical_facet_id(str(next(iter(learning_object_facet_union(lo)))))
    # RW6a's claims read is tested in test_reader_recap.py; here its answer is given.
    monkeypatch.setattr(PC, "unchecked_claims", lambda *args, **kwargs: [
        {"facet_id": facet, "basis": "source_visible", "attempt_ids": []}])
    (claim,) = [t for t in PC.cue_targets(vault, repository, "ext_text") if t.kind == "unchecked_claim"]
    assert claim.open and claim.facet_ids == (facet,)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(try_first=True, relation="new_application"))
    entry = next(e for e in out["targets"] if e["kind"] == "unchecked_claim")
    kept = [link for link in _links(repository) if link["target_kind"] == "unchecked_claim"]
    assert all(link["relation"] == "try_first" for link in kept)
    assert all(d["reason"] == "a claim needing an independent check offers only try first"
               for d in entry["dropped"] if d["relation"] != "try_first")
    set_config(paths, "cues", try_first_enabled=False)
    switched = loaded(paths)
    assert not [t for t in PC.cue_targets(switched, repository, "ext_text") if t.kind == "unchecked_claim"]


# -- F12: "Open" shows the earlier work ------------------------------------------------------------


def test_open_shows_the_cited_answer_and_the_learners_own_words(tmp_path, monkeypatch):
    from tests.helpers import NOW_ISO

    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    vault = loaded(paths)
    item = next(item for item in vault.practice_items.values() if item.learning_object_id == "lo_matrices")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, created_at) VALUES ('att_cited', ?, 'lo_matrices', 'short_answer', "
            "'independent_attempt', 'Swapping rows keeps the determinant.', 0.0, ?)", (item.id, NOW_ISO))
        connection.commit()
    cited = target("misconception", "m_cited", p_open=1.0, statement="Row swaps leave det unchanged")
    cited = PC.CueTarget(**{**{f: getattr(cited, f) for f in ("kind", "id", "statement", "status",
                                                                "learning_object_ids", "topic", "p_open",
                                                                "p_open_source")},
                            "provenance": {"attempt_id": "att_cited"}})
    asked = PC.CueTarget(kind="learner_text_gap", id="gap_1", statement="Not sure what a cofactor is",
                         status="named:prerequisite", learning_object_ids=("lo_matrices",), topic="Matrices",
                         p_open=1.0, p_open_source="gap_status",
                         provenance={"learner_text": "why do cofactors alternate in sign?",
                                     "learner_text_kind": "tutor_question"})
    seed_link(repository, cited, "t3")
    seed_link(repository, asked, "t1")
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: [cited, asked])
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    vault = loaded(paths)
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    by_target = {mark["target_id"]: mark["earlier"] for mark in cues["marks"]}
    work = by_target["misconception:m_cited"]
    assert work["attempt_id"] == "att_cited" and work["answer"] == "Swapping rows keeps the determinant."
    assert work["practice_item_id"] == item.id and work["answered_on"]
    assert work["statement"] == "Row swaps leave det unchanged"  # the model's voice, apart
    words = by_target["learner_text_gap:gap_1"]
    assert words["learner_text"] == "why do cofactors alternate in sign?"
    assert words["learner_text_kind"] == "tutor_question" and words["attempt_id"] is None


def test_a_misconceptions_cited_answer_is_its_newest_source_events_attempt(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    repository.insert_error_event({"id": "err_src", "learning_object_id": "lo_matrices", "attempt_id": "att_src",
                                   "error_type": "conceptual_slip", "severity": 0.5, "status": "active",
                                   "created_at": "2026-10-01T00:00:00Z"})
    with repository.connection() as connection:
        connection.execute("UPDATE misconceptions SET source_error_event_ids_json = '[\"err_src\"]' "
                           "WHERE id = 'mis_swap'")
        connection.commit()
    (found,) = PC.cue_targets(loaded(paths), repository, "ext_text")
    assert found.provenance.get("attempt_id") == "att_src"


# -- F11: the experimental unit is the randomized link ---------------------------------------------


def test_repeated_visits_never_manufacture_samples():
    units = [
        {"link_id": "l1", "shown": True, "propensity": 0.9, "outcome": 1.0, "outcome_attempt_id": "a1"},
        {"link_id": "l2", "shown": True, "propensity": 0.9, "outcome": 1.0, "outcome_attempt_id": "a1"},
        {"link_id": "l3", "shown": False, "propensity": 0.1, "outcome": 0.0, "outcome_attempt_id": "a2"},
        {"link_id": "l4", "shown": False, "propensity": 0.1, "outcome": 0.0, "outcome_attempt_id": "a2"},
    ]
    estimate = _holdout_estimate(units)
    # One distinct outcome per arm: counts only, never an interval of [1.0, 1.0].
    assert estimate["shown"]["n"] == 1 and estimate["shown"]["links"] == 2
    assert estimate["effect"] is None and estimate["interval_95"] is None


def _impression(connection, impression_id, *, link_id, shown, reason, propensity, visit, at):
    connection.execute(
        "INSERT INTO reader_cue_impressions (id, cue_id, link_id, extraction_id, span_id, learning_object_id, kind, "
        "visit_id, shown, suppressed_reason, propensity, seed, p_open, p_open_source, density, created_at) "
        "VALUES (?, ?, ?, 'ext_text', 't3', 'lo_matrices', 'distinction', ?, ?, ?, ?, 's', 1.0, 'x', 'normal', ?)",
        (impression_id, f"c_{link_id}", link_id, visit, shown, reason, propensity, at))


def test_the_report_counts_one_unit_per_link_and_matches_the_targets_facets(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    item = next(item for item in loaded(paths).practice_items.values() if item.learning_object_id == "lo_matrices")
    with repository.connection() as connection:
        for link, facets in (("plink_a", '["facet_det"]'), ("plink_b", "[]")):
            connection.execute(
                "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
                "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES (?, "
                "'2026-10-01T00:00:00Z', 'passage_cue', 'cue_target', 'x', 'reader_span', 'ext_text/t3', 'llm', "
                "'m', 'v', 'h', 'clarifies_distinction', 1.0, '{}')", (f"pcj_{link}",))
            connection.execute(
                "INSERT INTO passage_links (id, extraction_id, span_id, target_kind, target_id, relation, quote, "
                "pick_rank, target_facets_json, ledger_id, state_key, model, prompt_version, created_at) VALUES "
                "(?, 'ext_text', 't3', 'misconception', ?, 'clarifies_distinction', 'q', 1, ?, ?, 'k', 'm', 'v', "
                "'2026-10-01T00:00:00Z')", (link, link, facets, f"pcj_{link}"))
        # plink_a: shown on two visits before one attempt (one unit).
        _impression(connection, "i1", link_id="plink_a", shown=1, reason=None, propensity=0.9, visit="v1",
                    at="2026-10-10T10:00:00Z")
        _impression(connection, "i2", link_id="plink_a", shown=1, reason=None, propensity=0.9, visit="v2",
                    at="2026-10-10T11:00:00Z")
        _impression(connection, "i3", link_id="plink_b", shown=0, reason="holdout", propensity=0.1, visit="v1",
                    at="2026-10-10T10:00:00Z")
        for attempt, facets, at in (("att_other_facet", '["facet_other"]', "2026-10-10T12:00:00Z"),
                                    ("att_det", '["facet_det"]', "2026-10-10T13:00:00Z")):
            connection.execute(
                "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
                "correctness, evidence_facets_json, created_at) VALUES (?, ?, 'lo_matrices', 'short_answer', "
                "'independent_attempt', 1.0, ?, ?)",
                (attempt, item.id, facets, at))
        connection.commit()
    holdout = build_reader_report(paths.sqlite_path)["cues"]["discovered"]["holdout"]
    assert holdout["shown"]["links"] == 1 and holdout["shown"]["n"] == 1
    assert holdout["held_out"]["links"] == 1


# -- F13: the dry run's spend plan ------------------------------------------------------------------


def test_the_dry_run_names_settled_targets_and_carries_a_spend_plan(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    PC.discover(vault, repository, "ext_text", client=CueJudgeFake())
    _more_targets(repository, 1)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(), dry_run=True)
    statuses = sorted(entry["status"] for entry in out["targets"])
    assert statuses == ["current", "dry_run"], "the settled target is skipped, the new one would be judged"
    plan = out["spend_plan"]
    assert plan["judge"]["calls"] == 1 and plan["judge"]["cost_basis"] == "estimated_only"
    assert plan["judge"]["estimated_tokens"] > 0
    assert plan["caps"]["max_calls_per_source_open"] == 12 and plan["caps"]["subscription_exempt_from_dollar_cap"]
    assert set(plan["query_embeddings"]) >= {"enabled", "requests_at_most", "cost_basis"}


# -- taps resolve through the plan's cues kept for the reading ------------------------------------


def test_a_tap_on_a_drawn_mark_does_not_rebuild_the_plan(tmp_path, monkeypatch):
    paths, repository, spans = build_cue_vault(tmp_path / "v", misconception=False)
    guide_cue(paths, repository, ["t2"])
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    plan = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))
    mark = plan["cues"]["marks"][0]
    from learnloop.reader import reader_guidance as RG

    def refuse(*args, **kwargs):
        raise AssertionError("the plan was rebuilt for a tap")

    monkeypatch.setattr(RG, "build_guide_plan", refuse)
    call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": mark["cue_id"], "action": "opened",
                                 "visit_id": "v1", "plan_id": plan["cues"]["discovery"]["plan_id"]})
    with repository.connection() as connection:
        assert store.impression_for(connection, "v1", mark["cue_id"])["response"] == "opened"


def test_the_plan_says_when_background_work_can_still_name_a_target(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    assert cues["discovery"]["targets_pending"] is False
    from learnloop.diagnosis.text_gaps.jobs import enqueue

    set_config(paths, "learner_text_gaps", enabled=True)
    enqueue(repository, source_kind="tutor_question", source_id="q_1")
    vault = loaded(paths)
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    assert cues["discovery"]["targets_pending"] is True



# -- F15 (re-review): a cached tap follows the vault loaded now ------------------------------------

#: Shares words with the worked example (t5), as tests/test_reader_try_first.py's.
_SOLVE = "Solve for the eigenvalue by subtracting and dividing both sides"


def test_a_cached_try_first_tap_is_refused_once_try_first_is_switched_off_and_reloaded(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    paths, repository, _spans = build_cue_vault(tmp_path / "v", statement=_SOLVE)
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake(try_first=True)
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert job["state"] == "done" and job["result"]["links"] >= 1, job
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    (mark,) = [mark for mark in cues["marks"] if mark["kind"] == "try_first"]
    set_config(paths, "cues", try_first_enabled=False)
    ctx.reload()
    with pytest.raises(SidecarError):
        call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": mark["cue_id"], "action": "try_first",
                                     "visit_id": "v1", "plan_id": cues["discovery"]["plan_id"]})
    with repository.connection() as connection:
        assert store.impression_for(connection, "v1", mark["cue_id"]) is None
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE judge = 'learner_card'").fetchone()[0] == 0


def test_the_kept_cues_are_dropped_on_a_reload_and_kept_within_one(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import reader_cue_discovery as RCD

    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    guide_cue(paths, repository, ["t2"])
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"})
    vault, _repository = ctx.require_vault()
    kept = RCD._cues_now(ctx, vault, repository, "ext_text")
    assert RCD._cues_now(ctx, vault, repository, "ext_text") is kept, "kept within one vault load"
    ctx.reload()
    reloaded, _repository = ctx.require_vault()
    assert RCD._cues_now(ctx, reloaded, repository, "ext_text") is not kept, "rebuilt for the vault loaded now"
