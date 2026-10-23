"""Reader workbench RW3b, fix round 4 (docs/reviews/reader-rw3b-codex-review.md).

The whole-stage verify's findings, each reproduced on the real functions
(fakes for every model): F16 one source open has one judge call budget,
whatever the targets do mid-open; F17 an impression is resolved against the
plan it was seen on, and an unknown or expired plan is refused with nothing
stored; F18 the stored propensity is the draw's own probability, unrounded;
F19 the holdout report withholds its interval when an outcome attempt counts
in both arms.
"""

from __future__ import annotations

import pytest

from learnloop.db.stores import reader_cue_links as store
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.reader.reader_report import _holdout_estimate
from learnloop.source_retrieval import passage_cues as PC
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import reader_cue_discovery as RCD
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, seed_link, set_config, snake, target
from tests.recap_fixtures import call, context


def _more_targets(repository, count: int, *, prefix: str = "mis_more") -> None:
    for index in range(count):
        repository.insert_misconception(id=f"{prefix}_{index}", learning_object_id="lo_matrices", status="active",
                                        statement=f"Swapping rows of a matrix keeps its determinant, variant {index}")


def _rows(repository) -> list[dict]:
    with repository.connection() as connection:
        return store.impressions(connection)


# -- F16: one call budget per source open ----------------------------------------------------------


def _discover(ctx, open_id: str) -> dict:
    return snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": open_id}))


def test_a_target_change_mid_open_never_refills_the_opens_call_budget(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 12)  # 13 targets with mis_swap
    set_config(paths, "cues", max_calls_per_source_open=12)
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    judge = CueJudgeFake()
    ctx.cue_judge_client = judge
    first = _discover(ctx, "open_1")
    assert first["state"] == "done" and first["result"]["calls"] == 12
    assert [entry["status"] for entry in first["result"]["targets"]].count("capped") == 1
    # A new gap while the source stays open: the targets change, the Reader asks again.
    repository.insert_misconception(id="mis_new_gap", learning_object_id="lo_matrices", status="active",
                                    statement="Swapping rows of a matrix changes its determinant sign, a new gap")
    second = _discover(ctx, "open_1")
    assert second["result"]["targets_key"] != first["result"]["targets_key"]
    # Re-asks of the same open draw on the same budget too.
    third = _discover(ctx, "open_1")
    assert len(judge.prompts) <= 12, f"{len(judge.prompts)} judge calls in one source open (cap 12)"
    assert second["result"]["calls"] == 0 and third["result"]["calls"] == 0
    assert {entry["status"] for entry in second["result"]["targets"] if entry["status"] != "current"} == {"capped"}
    # The next open of the source has a budget of its own.
    fourth = _discover(ctx, "open_2")
    assert fourth["result"]["calls"] == 2 and len(judge.prompts) == 14


def test_failures_and_retries_of_one_open_share_its_budget_across_jobs(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    set_config(paths, "cues", max_calls_per_source_open=2)
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    judge = CueJudgeFake(fail=True)
    ctx.cue_judge_client = judge
    _discover(ctx, "open_1")
    ctx.cue_judge_client = CueJudgeFake()
    again = _discover(ctx, "open_1")
    assert len(judge.prompts) + len(ctx.cue_judge_client.prompts) <= 2
    assert again["result"]["calls"] == 0


def test_a_source_open_id_names_one_source(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake()
    _discover(ctx, "open_1")
    jobs = RCD._jobs(ctx)
    with pytest.raises(SidecarError):
        jobs._open("open_1", "ext_other", loaded(paths))


# -- F17: impressions against the plan they were seen on -------------------------------------------


def _plan_ctx(tmp_path, monkeypatch, *, rate: float = 0.0, density: str = "more"):
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    set_config(paths, "cues", holdout_rate=rate, density=density)
    targets = [target("hypothesis", f"h{index}", p_open=0.9 - index * 0.1) for index in range(3)]
    for t, span in zip(targets, ["t1", "t3", "t5"]):
        seed_link(repository, t, span)
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: list(targets))
    ctx = context(paths.root)
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    return paths, repository, ctx, cues


def test_an_impression_queued_before_a_density_change_is_recorded_against_its_own_plan(tmp_path, monkeypatch):
    _paths, repository, ctx, cues = _plan_ctx(tmp_path, monkeypatch)
    mark = next(mark for mark in cues["marks"] if mark["found_by"] == "model")
    plan_id = cues["discovery"]["plan_id"]
    # Seen and queued; before the flush the learner turns marks off (the vault reloads).
    call(ctx, "reader.set_cue_preferences", {"extraction_id": "ext_text", "density": "off"})
    now = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    assert mark["cue_id"] in {cue["cue_id"] for cue in now["discovery"]["suppressed"]}
    assert now["discovery"]["plan_id"] != plan_id
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": plan_id,
                                         "entries": [{"cue_id": mark["cue_id"], "shown": True}]})
    (row,) = _rows(repository)
    assert (row["shown"], row["suppressed_reason"], row["density"]) == (True, None, "more")
    assert row["propensity"] == mark["propensity"] and row["seed"] == mark["seed"]
    assert row["link_id"] == mark["link_id"]


def test_an_unknown_plan_id_is_refused_and_nothing_is_stored(tmp_path, monkeypatch):
    _paths, repository, ctx, cues = _plan_ctx(tmp_path, monkeypatch)
    mark = cues["marks"][0]
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": "cplan_forged",
                                             "entries": [{"cue_id": mark["cue_id"], "shown": True}]})
    assert caught.value.code == "cue_plan_unknown"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": "cplan_x",
                                             "entries": [{"cue_id": mark["cue_id"], "response": "fewer"}]})
    assert caught.value.code == "cue_plan_unknown"
    assert _rows(repository) == []


def test_an_expired_or_dropped_plan_is_refused_and_nothing_is_stored(tmp_path, monkeypatch):
    _paths, repository, ctx, cues = _plan_ctx(tmp_path, monkeypatch)
    mark = cues["marks"][0]
    plan_id = cues["discovery"]["plan_id"]
    real = RCD._clock()
    monkeypatch.setattr(RCD, "_clock", lambda: real + RCD.PLAN_TTL_SECS + 1)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": plan_id,
                                             "entries": [{"cue_id": mark["cue_id"], "shown": True}]})
    assert caught.value.code == "cue_plan_unknown"
    monkeypatch.setattr(RCD, "_clock", lambda: real)
    monkeypatch.setattr(RCD, "MAX_KEPT_PLANS", 1)
    older = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]["discovery"]["plan_id"]
    newer = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]["discovery"]["plan_id"]
    with pytest.raises(SidecarError):
        call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": older,
                                             "entries": [{"cue_id": mark["cue_id"], "shown": True}]})
    assert _rows(repository) == []
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": newer,
                                         "entries": [{"cue_id": mark["cue_id"], "shown": True}]})
    assert len(_rows(repository)) == 1


# -- F18: the stored propensity is the draw's probability ------------------------------------------


RATE = 0.123456789


def test_the_draw_and_its_propensity_use_one_unrounded_rate():
    draw = PC.holdout_draw("plink_0", RATE)
    assert draw["propensity"] == (RATE if draw["held_out"] else 1.0 - RATE)
    assert draw["propensity"] != round(draw["propensity"], 6)
    for index in range(300):
        draw = PC.holdout_draw(f"plink_{index}", RATE)
        assert draw["held_out"] == (int(draw["seed"], 16) / float(1 << 64) < RATE)
        assert draw["propensity"] == (RATE if draw["held_out"] else 1.0 - RATE)


def test_a_logged_impression_stores_the_exact_propensity(tmp_path, monkeypatch):
    paths, repository, ctx, cues = _plan_ctx(tmp_path, monkeypatch, rate=RATE)
    assert PC.holdout_rate(loaded(paths)) == RATE
    vault = loaded(paths)
    direct = PC.merged_cues(vault, repository, extraction_id="ext_text",
                            plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    assert direct["discovery"]["holdout_rate"] == RATE
    discovered = [*[m for m in cues["marks"] if m["found_by"] == "model"], *cues["discovery"]["held_out"]]
    assert discovered
    entries = [{"cue_id": cue["cue_id"], "shown": cue in cues["marks"]} for cue in discovered]
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1",
                                         "plan_id": cues["discovery"]["plan_id"], "entries": entries})
    for row in _rows(repository):
        expected = PC.holdout_draw(row["link_id"], RATE)["propensity"]
        assert row["propensity"] == expected
        assert row["propensity"] in (RATE, 1.0 - RATE)


# -- F19: no interval that ignores shared outcomes --------------------------------------------------


def test_shared_outcome_attempts_withhold_the_interval_and_say_why():
    # The verify's case: two outcome attempts, each counted in both arms, correctness 0 and 1.
    units = [
        {"link_id": "l1", "shown": True, "propensity": 0.9, "outcome": 0.0, "outcome_attempt_id": "a1"},
        {"link_id": "l2", "shown": True, "propensity": 0.9, "outcome": 1.0, "outcome_attempt_id": "a2"},
        {"link_id": "l3", "shown": False, "propensity": 0.1, "outcome": 0.0, "outcome_attempt_id": "a1"},
        {"link_id": "l4", "shown": False, "propensity": 0.1, "outcome": 1.0, "outcome_attempt_id": "a2"},
    ]
    estimate = _holdout_estimate(units)
    assert estimate["shared_outcomes"] == 2
    assert estimate["effect"] == 0.0
    assert estimate["interval_95"] is None
    assert estimate["effect_label"] == "point estimate only"
    assert "can't separate the arms yet" in estimate["interval_withheld"]


def test_without_shared_outcomes_the_interval_is_kept():
    units = [
        {"link_id": "l1", "shown": True, "propensity": 0.9, "outcome": 0.0, "outcome_attempt_id": "a1"},
        {"link_id": "l2", "shown": True, "propensity": 0.9, "outcome": 1.0, "outcome_attempt_id": "a2"},
        {"link_id": "l3", "shown": False, "propensity": 0.1, "outcome": 0.0, "outcome_attempt_id": "a3"},
        {"link_id": "l4", "shown": False, "propensity": 0.1, "outcome": 1.0, "outcome_attempt_id": "a4"},
    ]
    estimate = _holdout_estimate(units)
    assert estimate["shared_outcomes"] == 0 and estimate["interval_withheld"] is None
    assert estimate["interval_95"] == [-0.98, 0.98]
    assert estimate["effect_label"] == "point estimate with a 95% interval"
