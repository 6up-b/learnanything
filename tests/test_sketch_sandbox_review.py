"""RW5d P2: the independent sandbox review's findings (gpt-6-astra, fix round 4).

1. **Runtime history.** The verifier loaded a program once and called
   ``init()`` across the grid; the desktop initializes the default first on a
   fresh engine. A program counting its own starts was verified as drawing
   radius 1 at the default while a fresh engine draws 9. Now every
   ``init()`` runs on a freshly loaded program (both hosts), every run reads
   ``view()`` then ``probes()`` at exactly the steps of one read schedule
   (:func:`.sketch.read_steps`: verification, grading and playback), and the
   report carries the digest of every checked read so the desktop compares
   its own and withdraws the checks on any difference.
2. **Off-step predictions.** A prediction's parameter change must be a value
   the controls can be set to: graded at exactly it, played at exactly it.

The desktop half is ``sketchSandboxReview.test.ts`` (the same programs
through the committed engine in the TypeScript host).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.figures import sketch as K
from learnloop.figures import sketch_verify as SV
from learnloop.figures import verify as V
from learnloop.figures.sketch_engine import SketchEngine
from tests import sketch_fixtures as F

CORPUS = (Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures"
          / "sketch" / "sketchHostileCorpus.json")


def _canonical_reads(compiled: K.CompiledSketch, params: dict[str, float], *, seed: int = SV.VERIFY_SEED,
                     upto: int | None = None) -> dict[int, tuple[str, str]]:
    """A run as the desktop plays it: a fresh engine, ``init``, then every
    scheduled step stepped to and read (``view`` then ``probes``)."""

    program = compiled.program
    dt = program.clock.dt if program.clock is not None else 0.0
    reads: dict[int, tuple[str, str]] = {}
    with SketchEngine() as engine:
        engine.load(program.code)
        engine.init(params, seed)
        at = 0
        for step in K.read_steps(compiled):
            if upto is not None and step > upto:
                break
            if step > at:
                engine.step(params, dt, index=at, count=step - at)
                at = step
            reads[step] = (engine.view_text(params, index=step), engine.probes_text(params, index=step))
    return reads


# ---------------------------------------------------------------------------
# Finding 1: runtime history
# ---------------------------------------------------------------------------


def test_the_reviewers_counting_program_fails_verification():
    """The exact repro: radius 9 at the default on a fresh start, 1 on every
    later start. Verified as 'radius equals 1 at three settings' before."""

    report = SV.verify_sketch(K.parse_sketch(F.counting_starts()))
    assert report.outcome == V.FAILED, report.checks
    assert report.failed_step == "claims"
    assert "radius is 9" in report.reason and "a=1" in report.reason


def test_every_init_runs_on_a_freshly_loaded_program():
    with SketchEngine() as engine:
        engine.load(F.COUNTING_STARTS_CODE)
        for params in ({"a": 0.0}, {"a": 2.0}, {"a": 1.0}):
            engine.init(params, 1)
        assert engine.probes({"a": 1.0}, index=0) == {"radius": 9, "starts": 1}
        # Repeated restarts at the same settings: the same first start every time.
        for _ in range(3):
            engine.init({"a": 1.0}, 1)
            assert engine.probes({"a": 1.0}, index=0) == {"radius": 9, "starts": 1}


def test_reads_never_carry_over_into_the_next_run():
    with SketchEngine() as engine:
        engine.load(F.READ_COUNTING_CODE)
        engine.init({}, 1)
        for _ in range(4):
            engine.view({}, index=0)
        assert engine.probes({}, index=0)["reads"] == 5  # within a run, reads are the program's own business
        engine.init({}, 1)
        assert engine.probes({}, index=0)["reads"] == 1  # a new run starts from the loaded program


def test_the_read_schedule_has_plays_ticks_the_samples_and_every_graded_step():
    walk = K.parse_sketch(F.walk(clock={"dt": 1, "t_max": 2000},
                                 predictions=[{"prompt": "?", "change": {"run_to": 5},
                                               "observe": {"kind": "direction", "probe": "msd"}}]))
    steps = K.read_steps(walk)
    assert steps[:4] == [0, 5, 20, 40] and steps[-1] == 2000
    assert set(K.sample_steps(walk)) <= set(steps)
    assert set(K.tick_steps(2000)) <= set(steps) and len(K.tick_steps(2000)) == K.SKETCH_PLAY_TICKS + 1
    assert K.read_steps(K.parse_sketch(F.spiral())) == [0]  # no clock: one read after init
    # Ties go up, as the desktop's Math.round.
    assert K.sample_steps(K.parse_sketch(F.walk())) == [0, 13, 25, 38, 50, 63, 75, 88, 100]
    assert K.round_half_up(2.5) == 3 and K.round_half_up(0.49999999999999994) == 0


def test_the_report_carries_the_schedule_and_the_digest_of_every_checked_read():
    compiled = K.parse_sketch(F.walk())
    report = SV.verify_sketch(compiled)
    assert report.outcome == V.ILLUSTRATIVE, report.reason
    data = report.as_dict()
    assert data["verifier_version"] == SV.VERIFIER_REPORT_VERSION
    assert data["read_steps"] == K.read_steps(compiled)
    tested = data["tested"]
    assert [entry["values"] for entry in tested] == [[100.0], [200.0], [400.0]]
    for entry in tested:
        # The samples, then the walk's graded step (run_to 100: already a sample, not repeated).
        assert entry["steps"] == K.sample_steps(compiled)
        reads = _canonical_reads(compiled, {"walkers": entry["values"][0]})
        assert entry["digests"] == [SV.tested_digest(*reads[step]) for step in entry["steps"]]
        assert all(len(digest) == SV.TESTED_DIGEST_HEX for digest in entry["digests"])


def test_a_program_that_changes_its_state_when_read_is_checked_under_the_playback_schedule():
    """``view()`` marks the state at n = 13 and later steps grow faster
    once marked: what step 50 holds depends on which steps were read. Every
    run reads the schedule, so verification, grading and playback agree."""

    compiled = K.parse_sketch(F.marks_when_read())
    report = SV.verify_sketch(compiled)
    assert report.outcome == V.ILLUSTRATIVE, report.reason
    reads = _canonical_reads(compiled, {})
    (entry,) = report.tested
    assert entry["digests"] == [SV.tested_digest(*reads[step]) for step in entry["steps"]]
    assert json.loads(reads[50][1])["x"] == 13 + 37 * 10
    # Grading walks the same schedule: the answer is what playback shows at step 50.
    with SketchEngine() as engine:
        engine.load(compiled.program.code)
        outcome = SV.prediction_outcome(compiled, engine, 0)
    assert outcome["target_step"] == 50 and outcome["after"] == 13 + 37 * 10 and outcome["answer"] == "rises"


def test_a_program_whose_reads_change_every_later_value_fails_as_not_deterministic():
    program = F.marks_when_read(code=F.MARKS_CODE.replace("if (s.n === 13) s.mark = true;", "s.mark = !s.mark;"))
    report = SV.verify_sketch(K.parse_sketch(program))
    assert report.outcome == V.FAILED and report.failed_step == "deterministic"


# ---------------------------------------------------------------------------
# Finding 2: a prediction's change is one value, graded and played
# ---------------------------------------------------------------------------


def test_an_off_step_prediction_change_is_refused():
    program = F.counting_starts(
        parameters=[{"name": "a", "label": "a", "min": 0, "max": 1, "step": 1, "default": 0}],
        predictions=[{"prompt": "?", "change": {"a": 0.4}, "observe": {"kind": "direction", "probe": "radius"}}])
    with pytest.raises(K.SketchError) as refused:
        K.parse_sketch(program)
    assert "a = 0.4 is not a value its control can be set to" in str(refused.value)
    assert "the nearest is 0" in str(refused.value)


def test_an_on_step_prediction_change_is_graded_at_exactly_that_value():
    program = F.counting_starts(
        code=F.COUNTING_CODE.replace("p.a === 1 && starts === 1 ? 9 : 1", "p.a"),
        parameters=[{"name": "a", "label": "a", "min": 0, "max": 1, "step": 0.1, "default": 0}],
        claims=[], bindings=[],
        predictions=[{"prompt": "?", "change": {"a": 0.3}, "observe": {"kind": "direction", "probe": "radius"}}])
    compiled = K.parse_sketch(program)
    assert K.control_value(compiled.program.parameters[0], 0.3) == 0.3
    with SketchEngine() as engine:
        engine.load(compiled.program.code)
        outcome = SV.prediction_outcome(compiled, engine, 0)
    assert outcome["change"] == {"a": 0.3} and outcome["after"] == 0.3


# ---------------------------------------------------------------------------
# Verify round 2 (Astra): signed zero, and every graded step in ``tested``
# ---------------------------------------------------------------------------


def test_the_signed_zero_program_is_graded_as_the_desktop_draws_it():
    """The verify's repro: parameter a at min/default -0.0. The sidecar sent
    "-0.0" and saw -0 (radius 1 at step 1, graded "same"); the desktop's
    JSON.stringify sends 0 (radius 9 at step 1). Now -0 never reaches either
    host's engine: the program is canonicalized when parsed and both hosts
    serialize -0 as 0, so grading says "rises", as the page shows."""

    import math

    compiled = K.parse_sketch(F.signed_zero())
    (parameter,) = compiled.program.parameters
    assert math.copysign(1.0, parameter.default) == 1.0 and math.copysign(1.0, parameter.min) == 1.0
    stored = json.loads(compiled.program.canonical_json())  # what the desktop is sent as specJson
    stored.pop("code")  # (the program's own text says -0)
    assert "-0" not in json.dumps(stored)
    report = SV.verify_sketch(compiled)
    assert report.outcome == V.ILLUSTRATIVE, report.reason
    with SketchEngine() as engine:
        engine.load(compiled.program.code)
        outcome = SV.prediction_outcome(compiled, engine, 0)
    assert (outcome["before"], outcome["after"], outcome["answer"]) == (1.0, 9.0, "rises")
    # The graded step is a tested state: the desktop compares its digest there.
    entry = next(item for item in report.tested if item["values"] == [0.0])
    assert 1 in entry["steps"]
    reads = _canonical_reads(compiled, {"a": 0.0})
    assert entry["digests"][entry["steps"].index(1)] == SV.tested_digest(*reads[1])
    # A host handed -0.0 anyway sends it as 0: the same reads.
    assert _canonical_reads(compiled, {"a": -0.0}) == reads


def test_neither_host_lets_a_program_see_negative_zero():
    code = ("function init(p){return 0} function step(s,p,dt){return Object.is(dt, -0) ? 1 : 0}"
            " function view(){return {viewport:{x:[0,1],y:[0,1]},elements:[]}}"
            " function probes(s,p){return {negzero: Object.is(p.a, -0), b: Object.is(p.b, -0)}}")
    with SketchEngine() as engine:
        engine.load(code)
        engine.init({"a": -0.0, "b": 0.0}, 1)
        assert engine.probes({"a": -0.0, "b": -0.0}, index=0) == {"negzero": False, "b": False}


def test_every_prediction_records_its_graded_read_in_tested():
    """A parameter-change prediction is graded off the grid (the spiral at
    a = 0.3): its settings get a tested entry, so the desktop's playback of
    the answer is compared too."""

    compiled = K.parse_sketch(F.spiral())
    report = SV.verify_sketch(compiled)
    assert report.outcome == V.ILLUSTRATIVE, report.reason
    entry = next(item for item in report.tested if item["values"] == [0.3, 0.8])
    assert entry["steps"] == [0]
    reads = _canonical_reads(compiled, {"a": 0.3, "b": 0.8})
    assert entry["digests"] == [SV.tested_digest(*reads[0])]
    assert SV.VERIFIER_REPORT_VERSION == "sketch-verify-v4"
    # One entry per setting (the desktop looks up the first match).
    assert len({tuple(item["values"]) for item in report.tested}) == len(report.tested)


# ---------------------------------------------------------------------------
# The hostile corpus's new cases (the desktop runs the same file)
# ---------------------------------------------------------------------------


def test_the_hostile_corpus_has_the_reviews_cases():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    sequences = [case["name"] for case in corpus["cases"] if "calls" in case]
    assert len(sequences) >= 3
    names = {case["name"] for case in corpus["verify_cases"]}
    assert {"counting its own starts", "marks its state when read", "off-step prediction change", "signed zero parameters"} <= names
    assert len(corpus["worker_messages"]) >= 8


def test_the_hostile_corpus_verify_cases_get_their_outcome_in_the_sidecar():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    for case in corpus["verify_cases"]:
        expect = case["expect"]
        try:
            compiled = K.parse_sketch(case["program"])
        except K.SketchError as exc:
            assert expect == {"outcome": "refused", "reason": expect["reason"]}, case["name"]
            assert expect["reason"] in str(exc), case["name"]
            continue
        report = SV.verify_sketch(compiled)
        assert report.outcome == expect["outcome"], (case["name"], report.reason)
        if "failed_step" in expect:
            assert report.failed_step == expect["failed_step"], case["name"]
