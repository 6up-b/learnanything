"""Reader RW5a fix round 4 (orchestrator): the verify's findings, each reproduced.

The source-check (spec §8.3 step 3) and admission tests these rounds added were removed
with that machinery by the owner's scope decision of 2026-10-21; their successors
are in tests/test_figures_scope_redesign.py. What stays here still holds.

See docs/reviews/reader-rw5a-codex-review.md, "Fix round 4 (orchestrator)".

"Checked" is certified by display agreement: (a) every literal of the
checked definition is a small exact decimal, (b) SymPy reads it exactly, (c)
the sandboxed check passes, and (d) at every grid point and plotted sample
the figure's DISPLAYED value equals the checked SymPy expression evaluated by
mpmath at 50 digits, every piecewise branch the same. Also: markers are
checkpointed with the reading they describe; every displayed numeric leaf is
finite and a plot's domain is bounded; compilation never recurses
unboundedly. The switch-off of figure-derived learner text is in
tests/test_figures_switch_off.py.
"""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.authoring import pf_sandbox
from learnloop.diagnosis.text_gaps import pipeline as gap_pipeline
from learnloop.diagnosis.text_gaps import sources as gap_sources
from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job, sweep_backlog
from learnloop.figures import grammar as G
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import (
    EQUATION_TEXT,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    sandbox_ready,
)
from tests.test_figures_codex_review import _clients, _equivalence, _gap_jobs, _missed_prediction

needs_sandbox = pytest.mark.skipif(not sandbox_ready(), reason="bubblewrap is not available here")


# ---------------------------------------------------------------------------
# High 1: certified by display agreement
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Medium 3 (F5): the marker is checkpointed with the reading
# ---------------------------------------------------------------------------

def test_f5_an_explanation_after_a_checkpointed_reading_is_its_own_text(tmp_path, monkeypatch):
    """The verify's sequence: the reading is checkpointed, the attempt fails,
    the learner writes "what changed?" while the job waits, the retry reuses
    the reading. The explanation is its own text; the marker says unread."""

    paths, repository, ctx, found = _missed_prediction(tmp_path)
    prediction_id = found["predictionId"]
    llm, clients = _clients()
    real = gap_pipeline.log_reading
    failures = []

    def fail_once(*args, **kwargs):
        if not failures:
            failures.append(True)
            raise RuntimeError("the process stopped after the reading")
        return real(*args, **kwargs)

    monkeypatch.setattr(gap_pipeline, "log_reading", fail_once)
    first = process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    assert first.state == "retry_later"
    with repository.connection() as connection:
        (payload,) = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM learner_text_gap_jobs")]
    assert payload["reading"] and payload["markers"] == {"explanation_read": False}
    call(ctx, "reader.figure_explain", {"predictionId": prediction_id, "text": "p sets the split"})
    explained = prediction_id + gap_sources.FIGURE_EXPLANATION_SUFFIX
    assert ("reader_formative", explained, "queued") in _gap_jobs(repository)
    later = FrozenClock(datetime.now(UTC) + timedelta(days=30))  # past the retry backoff
    while process_next_gap_job(paths.root, repository, owner="t", clients=clients, clock=later) is not None:
        pass
    readings = [payload for purpose, payload in llm.calls if purpose == "learner_gap_reading"]
    assert len(readings) == 2  # the base read once (reused on retry), the explanation once
    with repository.connection() as connection:
        jobs = {row[0]: (row[1], json.loads(row[2])) for row in connection.execute(
            "SELECT source_id, state, payload_json FROM learner_text_gap_jobs")}
    assert jobs[prediction_id][0] == "done", jobs
    assert jobs[prediction_id][1]["markers"] == {"explanation_read": False}
    assert jobs[explained][0] == "done"
    assert sweep_backlog(load_vault(paths.root), repository)["reader_formative"] == 0


# ---------------------------------------------------------------------------
# Medium 4: every displayed numeric leaf finite; the plot's domain bounded
# ---------------------------------------------------------------------------

def test_a_plot_domain_whose_samples_overflow_is_refused():
    spec = {"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "a constant",
            "panels": [{"kind": "function_plot", "x": {"var": "x", "min": -1e308, "max": 1e308},
                        "series": [{"expr": "1", "label": "one"}]}]}
    with pytest.raises(S.SpecError, match="span"):
        S.parse_spec(spec)
    spec["panels"][0]["x"] = {"var": "x", "min": -5e11, "max": 5e11}
    assert V.verify_numerics(S.parse_spec(spec)).outcome == V.ILLUSTRATIVE


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_structure_requires_every_numeric_leaf_finite(monkeypatch, bad):
    compiled = S.parse_spec({"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "a constant",
                             "panels": [{"kind": "function_plot", "x": {"var": "x", "min": 0, "max": 1},
                                         "series": [{"expr": "1", "label": "one"}]}]})
    real = S.evaluate_figure

    def with_a_bad_coordinate(figure, point=None):
        data = real(figure, point)
        data["panels"][0]["x"][5] = bad
        return data

    monkeypatch.setattr(S, "evaluate_figure", with_a_bad_coordinate)
    assert V.structural(compiled, [{}]) == ["panel 1 (function_plot) x[5] is not finite at the defaults"]


# ---------------------------------------------------------------------------
# Medium 5: compilation never recurses unboundedly
# ---------------------------------------------------------------------------

def _chain(levels: int) -> dict:
    zeros = " + 0" * 90
    definitions = [{"name": "f0", "expr": "x" + zeros}]
    definitions += [{"name": f"f{index}", "expr": f"f{index - 1}" + zeros} for index in range(1, levels)]
    return {"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "a chain",
            "definitions": definitions,
            "panels": [{"kind": "function_plot", "x": {"var": "x", "min": -1, "max": 1},
                        "series": [{"expr": f"f{levels - 1}", "label": "f"}]}]}


def test_the_verifys_seven_level_chain_compiles_and_evaluates():
    compiled = S.parse_spec(_chain(7))  # 1,261 nodes, 631 deep once expanded: inside both caps
    assert G.node_count(compiled.definitions["f6"], compiled.definitions) == 7 * 181 - 6
    assert G.expanded_depth(compiled.definitions["f6"], compiled.definitions) == 7 * 90 + 1
    assert V.verify_numerics(compiled).outcome == V.ILLUSTRATIVE
    assert S.evaluate_figure(compiled)["panels"][0]["series"][0]["y"][0] == -1.0


def test_a_chain_past_the_depth_cap_is_a_validation_error():
    with pytest.raises(S.SpecError, match="deeper than 700"):
        S.parse_spec(_chain(9))


def test_the_depth_cap_is_the_same_in_typescript():
    source = (G.__file__.replace("src/learnloop/figures/grammar.py",
                                 "apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts"))
    text = open(source, encoding="utf-8").read()
    assert re.search(rf"export const MAX_EXPANDED_DEPTH = {G.MAX_EXPANDED_DEPTH};", text)
