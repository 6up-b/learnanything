"""An author's bad prediction costs that prediction, never the figure.

From a real failure (arxiv_v2, Nov 8 2026): the author read the prompt's ``change: {param: value}`` literally on both
attempts, ``{"param": "lam", "value": 1}``, and a figure with nothing else wrong was stored ``failed``.
"""

from __future__ import annotations

import json

import pytest

from learnloop.figures import routes as R
from learnloop.figures import sketch as K
from learnloop.figures import spec as S
from tests import sketch_fixtures as F
from tests.figure_fixtures import AuthorFake, build, build_figure_vault, context, flagship, rows


def _prediction(change, *, prompt="If lam grows, does this rise?", expr="p*lam"):
    return {"prompt": prompt, "change": change, "observe": {"kind": "direction", "expr": expr}}


def _spec(*predictions):
    return flagship(kind="illustrative", predictions=list(predictions))


def _setup(tmp_path, answers, *, sketch=False):
    paths, repository = build_figure_vault(tmp_path / "vault", sketch=sketch)
    author = AuthorFake(answers)
    return repository, context(paths.root, author=author), author


def _stored(repository):
    (row,) = rows(repository, "interactive_figures")
    return row, json.loads(row["verification_report_json"])


def test_the_literal_param_value_shape_from_the_trace_is_read_as_the_parameter():
    compiled, notes = S.parse_author_spec(json.dumps(_spec(_prediction({"param": "lam", "value": 1}))))
    assert compiled.spec.predictions[0].change == {"lam": 1.0}
    assert notes == []


def test_the_right_shape_passes_untouched_and_a_parameter_named_param_is_left_alone():
    compiled, notes = S.parse_author_spec(_spec(_prediction({"lam": 2})))
    assert compiled.spec.predictions[0].change == {"lam": 2.0} and notes == []
    assert S._flat_change({"change": {"param": 2, "value": 1}})["change"] == {"param": 2, "value": 1}
    assert S._flat_change({"change": {"param": "lam", "value": True}})["change"] == {"param": "lam", "value": True}


@pytest.mark.parametrize("bad", [
    _prediction({"param": "lam", "value": "lots"}),  # the schema refuses it
    _prediction({"nothing_called_this": 1}),  # the compiler refuses it: not a parameter
    _prediction({"lam": 400}),  # the compiler refuses it: outside its range
    _prediction({}),  # the compiler refuses it: a direction prediction needs a change
    _prediction({"lam": 2}, expr="not_defined_here"),  # the compiler refuses it: its expression
    "not a prediction",
], ids=["schema", "unknown-parameter", "out-of-range", "no-change", "bad-expression", "not-an-object"])
def test_a_bad_prediction_is_dropped_with_a_note_and_a_good_one_is_kept(bad):
    good = _prediction({"lam": 2}, prompt="the good one")
    compiled, notes = S.parse_author_spec(_spec(bad, good))
    assert [prediction.prompt for prediction in compiled.spec.predictions] == ["the good one"]
    assert len(notes) == 1


def test_every_prediction_bad_still_leaves_the_figure():
    compiled, notes = S.parse_author_spec(_spec(_prediction({"a": 1}), _prediction({"b": 1})))
    assert compiled.spec.predictions == [] and len(notes) == 2


def test_predictions_past_the_cap_are_dropped_and_a_non_list_is_too():
    many = [_prediction({"lam": 2}, prompt=f"q{index}") for index in range(S.MAX_PREDICTIONS + 2)]
    compiled, notes = S.parse_author_spec(_spec(*many))
    assert len(compiled.spec.predictions) == S.MAX_PREDICTIONS and len(notes) == 2
    compiled, notes = S.parse_author_spec(flagship(kind="illustrative", predictions="none"))
    assert compiled.spec.predictions == [] and notes == ["predictions: not a list"]


def test_the_rest_of_the_figure_is_as_strict_as_ever():
    broken = _spec(_prediction({"a": 1}))
    broken["parameters"][0]["min"] = 99
    with pytest.raises(S.SpecError) as raised:
        S.parse_author_spec(broken)
    assert raised.value.problems and not any("prediction" in problem for problem in raised.value.problems)
    with pytest.raises(S.SpecError):
        S.parse_author_spec("not json")
    with pytest.raises(S.SpecError):
        S.parse_author_spec("[1]")


def test_the_strict_parser_still_refuses_what_only_the_author_path_forgives():
    with pytest.raises(S.SpecError):
        S.parse_spec(_spec(_prediction({"param": "lam", "value": 1})))
    with pytest.raises(S.SpecError):
        S.parse_spec(_spec(_prediction({"nothing_called_this": 1})))


def test_the_trace_end_to_end_one_call_a_shown_figure_a_working_question(tmp_path):
    repository, ctx, author = _setup(tmp_path, [_spec(_prediction({"param": "lam", "value": 2}))])
    figure = build(ctx)["figure"]
    assert author.calls == 1
    assert figure["verification"] == "illustrative"
    row, report = _stored(repository)
    stored = json.loads(row["spec_json"])
    assert stored["predictions"][0]["change"] == {"lam": 2}
    assert "author_predictions_dropped" not in report
    assert S.parse_spec(row["spec_json"]).spec.predictions[0].change == {"lam": 2.0}  # a stored spec stays strict


def test_a_dropped_prediction_shows_the_figure_and_is_on_its_report(tmp_path):
    repository, ctx, author = _setup(tmp_path, [_spec(_prediction({"nothing_called_this": 1}, prompt="the bad one"))])
    figure = build(ctx)["figure"]
    assert author.calls == 1 and figure["verification"] == "illustrative"
    row, report = _stored(repository)
    assert json.loads(row["spec_json"])["predictions"] == []
    (note,) = report["author_predictions_dropped"]
    assert note.startswith("the bad one: prediction 1:") and "nothing_called_this" in note


def test_a_real_problem_still_gets_the_second_attempt_without_the_predictions_noise(tmp_path):
    broken = _spec(_prediction({"nothing_called_this": 1}))
    broken["parameters"][0]["min"] = 99
    repository, ctx, author = _setup(tmp_path, [broken, _spec(_prediction({"lam": 2}))])
    figure = build(ctx)["figure"]
    assert author.calls == 2 and figure["verification"] == "illustrative"
    told = author.contexts[1]["problems_with_the_last_attempt"]
    assert told and not any("prediction" in problem for problem in told)


def test_a_sketch_gets_the_same_treatment():
    good = {"prompt": "the good one", "change": {"param": "a", "value": 0.3},
            "observe": {"kind": "direction", "probe": "radius"}}
    bad = {"prompt": "the bad one", "change": {"nothing_called_this": 1},
           "observe": {"kind": "direction", "probe": "radius"}}
    compiled, notes = K.parse_author_sketch(json.dumps(F.spiral(predictions=[bad, good])))
    (kept,) = compiled.program.predictions
    assert kept.prompt == "the good one" and kept.change == {"a": 0.3}
    (note,) = notes
    assert note.startswith("the bad one:")
    with pytest.raises(K.SketchError):
        K.parse_sketch(json.dumps(F.spiral(predictions=[bad])))


def test_run_to_is_untouched():
    compiled, notes = K.parse_author_sketch(F.walk())
    assert compiled.program.predictions[0].change == {"run_to": 100.0} and notes == []


def test_a_sketch_end_to_end_keeps_its_note(tmp_path):
    bad = {"prompt": "the bad one", "change": {"nothing_called_this": 1},
           "observe": {"kind": "direction", "probe": "radius"}}
    repository, ctx, author = _setup(tmp_path, [("sketch", F.spiral(predictions=[bad]))], sketch=True)
    figure = build(ctx)["figure"]
    assert author.calls == 1 and figure["verification"] == "illustrative"
    _row, report = _stored(repository)
    assert report["author_predictions_dropped"][0].startswith("the bad one:")


def test_both_prompts_spell_the_shape_out_under_new_versions():
    for instructions in (R.author_instructions(), R.author_instructions(advanced=True),
                         R.author_instructions(sketch=True), R.author_instructions(advanced=True, sketch=True)):
        assert '{"lam": 1}' in instructions and "never {\"param\": \"lam\", \"value\": 1}" in instructions
        assert "{param: value}" not in instructions
    assert R.AUTHOR_PROMPT_VERSION == "figure_author.v1.1"
    assert R.ADVANCED_PROMPT_VERSION == "figure_author.v2.1-panels"
