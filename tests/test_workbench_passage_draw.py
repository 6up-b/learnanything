"""Reader workbench RW2c: the logged draw between equally good passages (spec_reader_workbench_v1 §5.10, G39).

A draw happens only between passages that all passed the judge (a verified
retrieval; for worked examples, the best verdict class, so
``follows_learner_route`` stays first); the logged propensity equals the
draw probability; the seed reproduces the draw; the other options are one
click away ("another passage", a learner pick that is no call). With
``workbench.passage_draw_enabled`` off the first passage is shown and
nothing is logged. Fakes only.
"""

from __future__ import annotations

import json

import pytest

from learnloop.workbench import passage_draw
from learnloop.workbench.check import session_calls
from tests.hint_fakes import WriterFake
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar, wb_answer

SPANS = [{"span_id": f"s{index}", "extraction_id": "ext", "label": f"Book · §5.{index}", "text": "a step"}
         for index in range(1, 4)]


class BridgeFake:
    def __init__(self, spans, basis="retrieved_verified"):
        self.spans = spans
        self.basis = basis
        self.calls = []

    def __call__(self, vault, repository, *, context, question_md, learning_object_ids, item):
        self.calls.append(context)
        # T6's manifest names the spans its judge passed (fix round 2, 4).
        return self.spans, {"basis": self.basis,
                            "span_keys": [f"{span['extraction_id']}/{span['span_id']}" for span in self.spans]}


def test_the_draw_is_uniform_logged_and_reproduces_from_its_seed():
    drawn = passage_draw.draw(SPANS, seed="seed-a")
    assert drawn is not None
    assert drawn.probabilities == (1 / 3, 1 / 3, 1 / 3) and drawn.propensity == pytest.approx(1 / 3)
    # The seed reproduces the draw exactly.
    assert passage_draw.draw(SPANS, seed="seed-a") == drawn
    seen = {passage_draw.draw(SPANS, seed=f"seed-{index}").index for index in range(40)}
    assert seen == {0, 1, 2}
    columns = drawn.columns()
    assert json.loads(columns["drawn_option_json"])["option_id"] == f"ext:s{drawn.index + 1}"
    assert columns["propensity"] == drawn.propensity and columns["seed"] == "seed-a"
    assert sum(json.loads(columns["probabilities_json"]).values()) == pytest.approx(1.0)
    # Fewer than two options: nothing is drawn (the first is shown as before).
    assert passage_draw.draw(SPANS[:1], seed="x") is None


def test_a_worked_example_is_drawn_only_within_the_best_verdict_class():
    hits = [{"span_id": "w1", "extraction_id": "e", "verdict": "worked_example"},
            {"span_id": "r1", "extraction_id": "e", "verdict": "follows_learner_route"},
            {"span_id": "r2", "extraction_id": "e", "verdict": "follows_learner_route"}]
    assert [hit["span_id"] for hit in passage_draw.best_class(hits)] == ["r1", "r2"]
    for seed in range(20):
        assert passage_draw.draw(passage_draw.best_class(hits), seed=str(seed)).drawn["verdict"] == \
            "follows_learner_route"


def _bridge(tmp_path, config="", spans=SPANS, basis="retrieved_verified"):
    paths, ctx, _session = sidecar(tmp_path, config, writer=WriterFake([wb_answer] * 6))
    ctx.workbench_bridge_provider = BridgeFake(spans, basis)
    ctx.passage_draw_seed = "seed-wb"
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    bridge = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]
    return paths, ctx, wb, bridge


def test_the_bridge_logs_its_draw_and_shows_the_drawn_passage(tmp_path):
    paths, _ctx, wb, bridge = _bridge(tmp_path)
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    expected = passage_draw.draw(SPANS, seed="seed-wb")
    assert row["seed"] == "seed-wb" and row["propensity"] == pytest.approx(1 / 3)
    assert row["policy_version"] == passage_draw.POLICY_VERSION
    assert json.loads(row["drawn_option_json"])["span_id"] == expected.drawn["span_id"]
    assert [option["span_id"] for option in json.loads(row["options_json"])] == ["s1", "s2", "s3"]
    assert json.loads(row["cited_span_ids_json"]) == [expected.drawn["span_id"]]
    assert bridge["spanId"] == expected.drawn["span_id"] and bridge["alternatives"] == 2
    assert (row["counted_by"], row["chooser"]) == (None, "none")


def test_another_passage_is_a_learner_pick_one_click_away_and_no_call(tmp_path):
    paths, ctx, wb, bridge = _bridge(tmp_path)
    calls = session_calls(ctx.require_vault()[1], wb)
    first = call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": bridge["assistId"]})["passage"]
    shown = [bridge["spanId"]]
    second = call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": first["assistId"]})["passage"]
    shown += [first["spanId"], second["spanId"]]
    # Each click shows the next option, wrapping round: every option is reachable.
    assert sorted(shown) == ["s1", "s2", "s3"]
    assert first["line"].startswith("§ compare with the book") and first["drawAssistId"] == bridge["assistId"]
    picks = [row for row in help_rows(paths, wb) if row["chooser"] == "learner_pick"]
    assert len(picks) == 2
    assert all(row["propensity"] is None and row["seed"] is None and row["counted_by"] is None for row in picks)
    # No search ran, and the picks are not calls.
    assert session_calls(ctx.require_vault()[1], wb) == calls
    # Resume shows the passage the learner picked last, still with its options.
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert state["hints"][0]["bridge"]["spanId"] == second["spanId"]
    assert state["hints"][0]["bridge"]["alternatives"] == 2


def test_with_the_draw_off_the_first_passage_is_shown_and_nothing_is_logged(tmp_path):
    paths, ctx, wb, bridge = _bridge(tmp_path, "[workbench]\npassage_draw_enabled = false\n")
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    assert bridge["spanId"] == "s1" and "alternatives" not in bridge
    assert (row["options_json"], row["propensity"], row["seed"], row["drawn_option_json"]) == (None, None, None, None)
    with pytest.raises(Exception) as refused:
        call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": bridge["assistId"]})
    assert getattr(refused.value, "code", None) == "no_alternatives"


def test_no_draw_between_passages_that_were_not_judged(tmp_path):
    # Retrieval-rank-only spans (no listwise verification) are never drawn between.
    paths, _ctx, wb, bridge = _bridge(tmp_path, basis="lo_provenance")
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "bridge"]
    assert bridge["spanId"] == "s1" and row["propensity"] is None and row["options_json"] is None
