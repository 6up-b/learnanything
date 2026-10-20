"""Reader workbench RW3b, fix round 5 (docs/reviews/reader-rw3b-codex-review.md).

F16: a source's discovery judge calls a local day stay within
``cues.max_calls_per_source_per_day``, counted from the durable receipts, so
new open ids, a reload and a restart cannot exceed it; F17: a tap that must
create the visit's impression takes the plan the cue was first seen on, never
the current plan, and an unknown plan refuses only the impression part.
Fakes for every model.
"""

from __future__ import annotations

import pytest

from learnloop.db.stores import reader_cue_links as store
from learnloop.source_retrieval import passage_cues as PC
from learnloop_sidecar.errors import SidecarError
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, seed_link, set_config, snake, target
from tests.recap_fixtures import call, context


def _more_targets(repository, count: int) -> None:
    for index in range(count):
        repository.insert_misconception(id=f"mis_day_{index}", learning_object_id="lo_matrices", status="active",
                                        statement=f"Swapping rows of a matrix keeps its determinant, variant {index}")


def _root_receipts(repository) -> int:
    with repository.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'passage_cue_judge' "
            "AND parent_call_id IS NULL").fetchone()[0]


def _discover(ctx, open_id: str) -> dict:
    return snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": open_id}))


# -- F16: the source's daily cap, from durable rows -------------------------------------------------


def test_new_open_ids_a_reload_and_a_restart_never_exceed_the_sources_daily_calls(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 50)  # 51 targets: far more than a day's calls
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    judge = CueJudgeFake()
    ctx.cue_judge_client = judge
    assert loaded(paths).config.cues.max_calls_per_source_per_day == 36
    first = _discover(ctx, "open_1")
    assert first["result"]["calls"] == 12  # the per-open budget is unchanged
    _discover(ctx, "open_2")
    ctx.reload()
    _discover(ctx, "open_3")
    assert len(judge.prompts) == 36
    # A fourth open id: the day's calls for this source are used.
    fourth = _discover(ctx, "open_4")
    assert fourth["result"]["calls"] == 0
    assert {entry.get("reason") for entry in fourth["result"]["targets"]
            if entry["status"] == "capped"} == {PC.DAILY_CAP_REASON}
    # A restart (a fresh sidecar context on the same vault) and yet another open.
    restarted = context(paths.root)
    restarted.cue_discovery_inline = True
    restarted.cue_judge_client = judge
    _discover(restarted, "open_5")
    assert len(judge.prompts) <= 36, f"{len(judge.prompts)} judge calls for one source today (cap 36)"
    assert _root_receipts(repository) == 36
    assert PC.discovery_calls_today(repository, "ext_text") == 36
    assert PC.discovery_calls_today(repository, "ext_tex") == 0  # another source's prefix is not counted


def test_failed_requests_count_against_the_daily_cap_and_the_cli_run_is_held_to_it(tmp_path, monkeypatch):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 6)
    set_config(paths, "cues", max_calls_per_source_per_day=3)
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    failing = CueJudgeFake(fail=True)
    ctx.cue_judge_client = failing
    _discover(ctx, "open_1")
    assert len(failing.prompts) == 3, "failed requests and retries are calls of the day"
    # A direct run (the CLI's) on the same day: refused before any deep retrieval or request.
    deep: list[bool] = []
    real = PC.shortlist

    def watched(*args, **kwargs):
        deep.append(bool(kwargs.get("deep")))
        return real(*args, **kwargs)

    monkeypatch.setattr(PC, "shortlist", watched)
    judge = CueJudgeFake()
    out = PC.discover(loaded(paths), repository, "ext_text", client=judge)
    assert judge.prompts == [] and out["calls"] == 0 and not any(deep)
    assert out["source_calls_today"] == 3


def test_the_daily_cap_refuses_a_retry_that_would_pass_it(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable

    class FailsFirst(CueJudgeFake):
        def complete(self, request):
            if not self.prompts:
                self.prompts.append(request.prompt)
                raise AIProviderUnavailable("transient")
            return super().complete(request)

    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", max_calls_per_source_per_day=1)
    judge = FailsFirst()
    out = PC.discover(loaded(paths), repository, "ext_text", client=judge)
    assert len(judge.prompts) == 1 and out["calls"] == 1 and out["judged"] == 0
    assert _root_receipts(repository) == 1


def test_the_dry_run_names_the_daily_cap(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    out = PC.discover(loaded(paths), repository, "ext_text", client=CueJudgeFake(), dry_run=True)
    caps = out["spend_plan"]["caps"]
    assert caps["max_calls_per_source_per_day"] == 36 and caps["source_calls_today"] == 0


# -- F17: a tap creates an impression only from the plan the cue was seen on -----------------------


RATE = 0.123456789


def _tap_ctx(tmp_path, monkeypatch):
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    set_config(paths, "cues", holdout_rate=RATE, density="more")
    targets = [target("hypothesis", f"h{index}", p_open=0.9 - index * 0.1) for index in range(3)]
    for t, span in zip(targets, ["t1", "t3", "t5"]):
        seed_link(repository, t, span)
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: list(targets))
    ctx = context(paths.root)
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    return paths, repository, ctx, cues


def _impressions(repository) -> list[dict]:
    with repository.connection() as connection:
        return store.impressions(connection)


def test_a_tap_after_the_plan_changed_keeps_the_seen_plans_density_and_propensity(tmp_path, monkeypatch):
    paths, repository, ctx, plan_a = _tap_ctx(tmp_path, monkeypatch)
    mark = next(mark for mark in plan_a["marks"] if mark["found_by"] == "model"
                and not PC.holdout_draw(mark["link_id"], 0.2)["held_out"])
    assert mark["propensity"] == 1.0 - RATE
    # A's impression is queued; before its flush plan B replaces A (rate and density changed) ...
    config = paths.root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(f"holdout_rate = {RATE!r}", "holdout_rate = 0.2"),
                      encoding="utf-8")
    call(ctx, "reader.set_cue_preferences", {"extraction_id": "ext_text", "density": "normal"})  # reloads
    plan_b = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    assert plan_b["discovery"]["plan_id"] != plan_a["discovery"]["plan_id"] and plan_b["density"] == "normal"
    assert plan_b["discovery"]["holdout_rate"] == 0.2
    assert next(m for m in plan_b["marks"] if m["cue_id"] == mark["cue_id"])["propensity"] == 0.8
    # ... and the learner taps the mark: the tap names the plan the cue was first seen on.
    answer = snake(call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": mark["cue_id"],
                                                "action": "opened", "visit_id": "v1",
                                                "plan_id": plan_a["discovery"]["plan_id"]}))
    assert answer["impression"] == "recorded"
    # Then A's queued receipt arrives: the first row stands, and it is A's.
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1",
                                         "plan_id": plan_a["discovery"]["plan_id"],
                                         "entries": [{"cue_id": mark["cue_id"], "shown": True}]})
    (row,) = _impressions(repository)
    assert (row["density"], row["propensity"], row["seed"]) == ("more", 1.0 - RATE, mark["seed"])
    assert row["shown"] is True and row["response"] == "opened"


def test_a_tap_naming_an_unknown_plan_is_recorded_but_writes_no_impression(tmp_path, monkeypatch):
    _paths, repository, ctx, plan_a = _tap_ctx(tmp_path, monkeypatch)
    mark = next(mark for mark in plan_a["marks"] if mark["found_by"] == "model")
    answer = snake(call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": mark["cue_id"],
                                                "action": "opened", "visit_id": "v1", "plan_id": "cplan_gone"}))
    assert answer["impression"] == "refused: cue_plan_unknown"
    assert _impressions(repository) == []
    with repository.connection() as connection:
        events = connection.execute("SELECT COUNT(*) FROM interaction_events WHERE kind = 'reader_action_invoked'"
                                    ).fetchone()[0]
    assert events == 1, "the tap itself is recorded"


def test_a_tap_requires_a_plan_id(tmp_path, monkeypatch):
    _paths, _repository, ctx, plan_a = _tap_ctx(tmp_path, monkeypatch)
    with pytest.raises(Exception):
        call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": plan_a["marks"][0]["cue_id"],
                                     "action": "opened", "visit_id": "v1"})
    with pytest.raises(SidecarError):
        call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": "cplan_gone",
                                             "entries": [{"cue_id": plan_a["marks"][0]["cue_id"], "shown": True}]})
