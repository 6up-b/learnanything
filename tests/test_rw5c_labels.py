"""Reader RW5c: code-owned, element-scoped labels, option B (spec §7, §8.2; G23d, G23e; F2, F9)."""

from __future__ import annotations

import json
import typing
from typing import Any

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.figures import elements as E
from learnloop.figures import service as FS
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from learnloop.figures.display_format import js_string
from tests.figure_fixtures import AuthorFake, build, call, context
from tests.rw5c_fixtures import EXTRACTION, FLAGSHIP_TEX, build_check_vault, plot

sandboxed = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="needs bubblewrap")
MODEL_WORDS = "matches the book's equation (checked)"


def test_the_frame_and_the_python_labels_are_the_same_words():
    from learnloop.figures import labels as L
    from tests.test_figure_label_wording import _frame

    frame = _frame("FigureInline.tsx", "FIGURE_FRAME")
    assert frame["bookChecked"] == L.BOOK_CHECKED_LABEL == MODEL_WORDS
    assert frame["restIllustration"] == L.REST_ILLUSTRATION_LABEL and frame["derivedFrom"] == L.DERIVED_LABEL
    # The free-text rule reads the claim's words as a label, so a model cannot reproduce them in what it shows.
    assert L.label_like(L.BOOK_CHECKED_LABEL) is not None


def test_g23d_the_walk_covers_every_label_and_text_field_of_the_schema():
    found = E.schema_label_fields()
    assert {(model, name) for model, name, kind in found if kind == "label"} == set(E.LABEL_FIELDS)
    assert {(model, name) for model, name, kind in found if kind == "text"} == set(E.TEXT_FIELDS)


class Gauge(S._Strict):
    kind: typing.Literal["gauge"]
    caption: S.Label
    note: S.Text = ""


class Extended(S._Strict):
    panels: list[Gauge]
    demonstrates: S.Text


def test_g23d_a_new_panel_with_a_label_fails_until_it_is_mapped():
    found = E.schema_label_fields(Extended)
    assert ("Gauge", "caption", "label") in found and ("Gauge", "note", "text") in found
    assert ("Gauge", "caption") not in E.LABEL_FIELDS
    # The instance walk reaches it with no list of kinds, so it is rewritten like any other.
    slots = list(E.label_slots(Extended(panels=[Gauge(kind="gauge", caption="hello")], demonstrates="x")))
    assert ("panels", 0, "caption") in {slot.path for slot in slots}


def _every_panel() -> dict[str, Any]:
    return {
        "spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "free text in the model's voice",
        "assumptions": [{"text": "assume"}],
        "parameters": [{"name": "a", "label": "label of a", "min": 0.5, "max": 1.0, "step": 0.25, "default": 1.0}],
        "definitions": [{"name": "f", "expr": "a*x"}],
        "panels": [
            {"kind": "function_plot", "x": {"var": "x", "min": 0, "max": 1},
             "series": [{"expr": "f", "label": "label of the series"}, {"expr": "2*a*x", "label": "label two"}],
             "markers": [{"x": "a/2", "label": "label of the marker"}],
             "shade": [{"series": "label of the series", "from": "0", "to": "1", "label": "label of the shade"}]},
            {"kind": "pmf_bars", "k": {"var": "x", "min": 0, "max": 2}, "series": [{"expr": "a", "label": "label of bars"}],
             "highlight": {"from": "0", "to": "1", "label": "label of highlight"}},
            {"kind": "linear_map_2d", "matrix": [["a", "0"], ["0", "1"]], "label": "label of the map"},
            {"kind": "readout", "label": "label of the readout", "expr": "integral(f, x, 0, 1)"},
        ],
        "predictions": [{"prompt": "which area?", "observe": {"kind": "area", "expr": "integral(f, x, 0, 1)"}}],
        "annotations": [{"target": "label of the series", "text": "a note"}, {"target": "nothing at all", "text": "b"}],
    }


def _book_labels(compiled: S.CompiledFigure) -> tuple[dict[str, E.BookLabel], dict[str, str]]:
    label = E.BookLabel(lhs="f(x)", latex="f(x)=ax", variable="x", tokens={"a": "a", "x": "x"}, extraction_id="e",
                        span_id="s", page=3, compound=False, plain="f(x)")
    return {"f": label}, {"panels.0.series.0": "f"}


def test_under_b_the_delivered_spec_holds_no_model_label_string():
    spec = _every_panel()
    compiled = S.parse_spec(spec)
    raw = compiled.spec.canonical_json()
    delivered, by_label = E.rewrite_spec(raw, compiled)
    labels = [slot.value for slot in E.label_slots(compiled.spec) if slot.kind == "label" and slot.value]
    assert len(labels) > 8
    for label in labels:
        assert label not in delivered, label
    # The free text stays, in the model's voice, outside the panels.
    assert "free text in the model's voice" in delivered and "a note" in delivered
    # And it still compiles, with its references bound.
    again = S.parse_spec(delivered)
    function_plot = again.panels[0].model
    assert function_plot.shade[0].series == function_plot.series[0].label == "panels.0.series.0"
    assert again.spec.annotations[0].target == "panels.0.series.0"
    assert again.spec.annotations[1].target == ""
    assert by_label["label of the shade"] == "panels.0.shade.0"
    assert S.evaluate_figure(again)["panels"][0]["shades"][0]["series"] == "panels.0.series.0"
    assert json.loads(raw)["panels"][0]["series"][0]["label"] == "label of the series"  # never the stored row


def test_the_element_map_gives_every_label_a_closed_role_and_no_model_text():
    spec = _every_panel()
    compiled = S.parse_spec(spec)
    book, drawn = _book_labels(compiled)
    elements = E.element_map(compiled, book, drawn)
    roles = {element["id"]: element["role"] for element in elements}
    assert all(element["role"] in E.ROLES and element["voice"] in E.VOICES for element in elements)
    assert roles["panels.0.series.0"] == "book"
    assert roles["panels.0.series.1"] == "ai"
    assert roles["panels.0.markers.0"] == "ai"
    assert roles["panels.0.shade.0"] == "derived"
    assert roles["panels.1.series.0"] == "ai"
    assert roles["panels.1.highlight"] == "ai"  # it sums an AI-built series
    assert roles["panels.2"] == "ai"
    assert roles["panels.3"] == "derived"
    assert roles["parameters.0"] == "symbol"
    text = json.dumps(elements)
    for slot in E.label_slots(compiled.spec):
        if slot.kind == "label" and slot.value:
            assert slot.value not in text, slot.value
    # A model label that reads as the claim: the walk replaces it like any other label.
    spec["panels"][0]["series"][1]["label"] = MODEL_WORDS
    spec["parameters"][0]["label"] = MODEL_WORDS
    worded = S.parse_spec(spec)
    assert MODEL_WORDS not in E.rewrite_spec(worded.spec.canonical_json(), worded)[0]


def test_a_book_elements_label_is_the_books_left_hand_side_and_its_provenance():
    compiled = S.parse_spec(_every_panel())
    book, drawn = _book_labels(compiled)
    entry = {element["id"]: element for element in E.element_map(compiled, book, drawn)}["panels.0.series.0"]
    assert entry["tex"] == "f(x)" and entry["voice"] == "source" and entry["equation"] == "f(x)=ax"
    assert entry["source"] == {"extraction_id": "e", "span_id": "s", "page": 3}


def test_an_unchecked_definition_renders_as_its_grammar_name_marked_ai_defined():
    compiled = S.parse_spec(plot("x", name="F"))
    entry = E.element_map(compiled, {"G": E.BookLabel("g", "g=1", None, {}, "e", "s", 1, False, "g")}, {})[0]
    assert entry["tag"] == "ai_defined" and entry["role"] == "ai" and entry["tex"] == r"\mathrm{F}(x)"
    assert entry["plain"] == "F(x)"


def _derived(spec: dict[str, Any], element_id: str, params: dict[str, float] | None = None) -> tuple[str, dict[str, Any]]:
    compiled = S.parse_spec(spec)
    elements = {element["id"]: element for element in E.element_map(compiled, {"f": E.BookLabel(
        "f(x)", "f(x)=x", "x", {"x": "x"}, "e", "s", 1, False, "f(x)")}, {"panels.0.series.0": "f"})}
    element = elements[element_id]
    env = {**compiled.defaults, **(params or {})}
    bounds = S.derived_bounds(compiled, element["template"]["panel"], element["template"]["kind"],
                              element["template"]["index"], env)
    return E.template_words(element["template"], bounds, js_string)[1], bounds


def _shaded(low: str, high: str, **changes: Any) -> dict[str, Any]:
    return plot("x + 0.25", shades=[{"series": "the book's curve", "from": low, "to": high, "label": "the model's area"}], **changes)


def test_f2_a_shade_states_the_bounds_the_evaluator_used():
    plain, bounds = _derived(_shaded("-1", "2"), "panels.0.shade.0")
    assert bounds["from"] == 0 and bounds["to"] == 1 and bounds["clipped"] is True
    assert plain == "area under f(x) from 0 to 1 · limited to the plotted range"
    assert "-1" not in plain
    compiled = S.parse_spec(_shaded("-1", "2"))
    assert S.evaluate_figure(compiled)["panels"][0]["shades"][0]["value"] == pytest.approx(0.75)


def test_f2_a_slider_that_moves_a_bound_updates_the_label():
    spec = _shaded("0", "a", parameters=[{"name": "a", "label": "a", "min": 0.25, "max": 1.0, "step": 0.25, "default": 0.5}])
    assert _derived(spec, "panels.0.shade.0")[0] == "area under f(x) from 0 to 0.5"
    assert _derived(spec, "panels.0.shade.0", {"a": 0.75})[0] == "area under f(x) from 0 to 0.75"


def _bars(low: str, high: str, axis: tuple[int, int] = (0, 3), expr: str = "1/(k+1)") -> dict[str, Any]:
    spec = plot(expr, variable="k")
    spec["panels"] = [{"kind": "pmf_bars", "k": {"var": "k", "min": axis[0], "max": axis[1]},
                       "series": [{"expr": "f", "label": "m"}], "highlight": {"from": low, "to": high, "label": "the model's sum"}}]
    return spec


def test_f2_a_highlight_states_its_integers_and_says_it_was_limited():
    plain, bounds = _derived(_bars("1.5", "4.2"), "panels.0.highlight")
    assert bounds["integers"] == [2, 3] and bounds["clipped"] is True
    assert plain == "sum for k from 2 to 3 of f(x) · limited to the plotted range"


def test_f2_an_empty_highlight_says_no_terms():
    plain, bounds = _derived(_bars("2.2", "2.8"), "panels.0.highlight")
    assert bounds["integers"] == [3, 2] and "no terms in this range" in plain


def _readout(expr: str, variable: str = "x") -> dict[str, Any]:
    spec = plot("1/(k+1)" if variable == "k" else "x", variable=variable)
    spec["panels"] = [*spec["panels"], {"kind": "readout", "label": "the model's value", "expr": expr}]
    return spec


def test_f2_an_integral_readout_states_its_evaluated_bounds():
    spec = _readout("integral(f, x, 0, 0.5)")
    compiled = S.parse_spec(spec)
    book = {"f": E.BookLabel("f(x)", "f(x)=x", "x", {}, "e", "s", 1, False, "f(x)")}
    element = {item["id"]: item for item in E.element_map(compiled, book, {"panels.0.series.0": "f"})}["panels.1"]
    assert element["role"] == "derived" and element["plain"] == "integral from 0 to 0.5 of f(x) dx"
    assert r"\int_{0}^{0.5} f(x)\,dx" == element["tex"]


def test_a_readout_whose_body_is_not_the_bare_reference_is_not_derived():
    spec = _readout("integral(2*f, x, 0, 0.5)")
    compiled = S.parse_spec(spec)
    book = {"f": E.BookLabel("f(x)", "f(x)=x", "x", {}, "e", "s", 1, False, "f(x)")}
    element = {item["id"]: item for item in E.element_map(compiled, book, {"panels.0.series.0": "f"})}["panels.1"]
    assert element["role"] == "ai" and element["voice"] == "model"


def test_f9_endpoints_are_lossless_never_format_value():
    spec = _readout("sum(f, k, 100000, 100001)", "k")
    spec["panels"][0] = {"kind": "pmf_bars", "k": {"var": "k", "min": 0, "max": 3}, "series": [{"expr": "f", "label": "m"}]}
    compiled = S.parse_spec(spec)
    book = {"f": E.BookLabel("f(k)", "f(k)=1/(k+1)", "k", {}, "e", "s", 1, False, "f(k)")}
    element = {item["id"]: item for item in E.element_map(compiled, book, {"panels.0.series.0": "f"})}["panels.1"]
    assert r"\sum_{k=100000}^{100001}" in element["tex"] and "1.000e+5" not in element["tex"]
    plain, bounds = _derived(_bars("100000", "100001", (99990, 100010)), "panels.0.highlight")
    assert bounds["integers"] == [100000, 100001] and "from 100000 to 100001" in plain
    plain, _bounds = _derived(_shaded("0.123456", "0.123457"), "panels.0.shade.0")
    assert "from 0.123456 to 0.123457" in plain


@pytest.mark.parametrize("low, high, shown", [
    (1e-7, 2e-7, r"\int_{1 \times 10^{-7}}^{2 \times 10^{-7}} f(x)\,dx"),
    (-1.5e-7, 2.5e21, r"\int_{-1.5 \times 10^{-7}}^{2.5 \times 10^{21}} f(x)\,dx"),
    (0.5, 1, r"\int_{0.5}^{1} f(x)\,dx"),
])
def test_f3_a_scientific_endpoint_is_written_as_the_power_it_means(low, high, shown):
    """Codex review F3: \\int_{1e-7} is a coefficient, the variable e, and a subtraction (figureLabels.test.tsx renders it)."""

    template = {"kind": "integral", "body_tex": "f(x)", "body_plain": "f(x)", "variable": "x"}
    tex, plain = E.template_words(template, {"from": low, "to": high, "integers": None, "clipped": False}, js_string)
    assert tex == shown
    assert plain == f"integral from {js_string(low)} to {js_string(high)} of f(x) dx"
    shade, _plain = E.template_words({**template, "kind": "shade"}, {"from": low, "to": high, "integers": None, "clipped": False}, js_string)
    assert "e-" not in shade and "e+" not in shade


@pytest.mark.parametrize("expr, tex, plain", [
    ("2*x + 1", r"2 \cdot x + 1", "2*x + 1"),
    ("x^2", "x^{2}", "x^2"),
    ("(a + b)*c", r"\left(a + b\right) \cdot c", "(a + b)*c"),
    ("-x", "-x", "-x"),
    ("exp(-x)", r"\exp\left(-x\right)", "exp(-x)"),
    ("sqrt(x)", r"\sqrt{x}", "sqrt(x)"),
    ("abs(x)", r"\left|x\right|", "abs(x)"),
    ("x/y", r"\frac{x}{y}", "x/y"),
    ("lambda*mu1", r"\lambda \cdot \mu_{1}", "lambda*mu1"),
    ("1e-3*x", r"1 \times 10^{-3} \cdot x", "1e-3*x"),
    ("rate", r"\mathrm{rate}", "rate"),
    ("pi", r"\pi", "pi"),
])
def test_codes_own_rendering_of_an_expression(expr, tex, plain):
    from learnloop.figures import grammar as G

    node = G.parse(expr)
    assert E.to_tex(node, {}) == tex and E.to_plain(node) == plain


# -- through the view ------------------------------------------------------------------------------------

BOOK = [("s1", "Text", f"The density is $${FLAGSHIP_TEX}$$ for a mixture."), ("s5", "Text", "$f(x)=x$"),
        ("s9", "Text", "$f(x)=x + \\frac{1}{4}$")]


def _built(tmp_path, answers: list[Any], span: str) -> tuple[Any, Any, Any]:
    paths, repository = build_check_vault(tmp_path / "vault", BOOK)
    ctx = context(paths.root, author=AuthorFake(answers))
    return build(ctx, {"extractionId": EXTRACTION, "spanIds": [span]})["figure"], ctx, repository


def _worded_spec() -> dict[str, Any]:
    spec = plot("x + 0.25", label=MODEL_WORDS, shades=[{"series": MODEL_WORDS, "from": "-1", "to": "2", "label": MODEL_WORDS + " area"}],
                parameters=[{"name": "a", "label": MODEL_WORDS + " slider", "min": 0.5, "max": 1.0, "step": 0.25, "default": 1.0}])
    spec["panels"].append({"kind": "readout", "label": MODEL_WORDS + " readout", "expr": "a"})
    spec["annotations"] = [{"target": MODEL_WORDS, "text": "see it"}]
    spec["predictions"] = [{"prompt": "which?", "observe": {"kind": "area", "expr": "integral(f, x, 0, 1)"}}]
    return spec


@sandboxed
def test_a_model_label_saying_checked_reaches_no_slot_of_a_checked_figure(tmp_path):
    figure, _ctx, _repository = _built(tmp_path, [_worded_spec()], "s9")
    assert figure["sourceCheck"]["status"] == "checked"
    assert MODEL_WORDS not in figure["specJson"]
    roles = {element["id"]: element["role"] for element in figure["elements"]}
    assert roles["panels.0.series.0"] == "book" and roles["panels.1"] == "ai" and roles["parameters.0"] == "ai"
    assert roles["panels.0.shade.0"] == "derived"
    assert MODEL_WORDS not in json.dumps(figure["elements"])
    assert all(element.get("voice") for element in figure["elements"])
    # An area prediction's choices are the shades' ids, in code's words.
    prediction = figure["predictions"]
    assert all(MODEL_WORDS not in json.dumps(item) for item in prediction)


@sandboxed
def test_an_area_prediction_answers_by_element_id_and_stores_the_shades_label(tmp_path):
    figure, ctx, repository = _built(tmp_path, [_worded_spec()], "s9")
    prediction = figure["predictions"][0]
    assert prediction["choices"] == [{"value": "panels.0.shade.0",
                                      "label": "area under f(x) from 0 to 1 · limited to the plotted range"}]
    answered = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                   "answer": "panels.0.shade.0"})
    assert answered["learnerAnswer"] == "panels.0.shade.0" and answered["answer"] == "panels.0.shade.0"
    assert answered["matched"] is True
    from tests.figure_fixtures import rows

    assert rows(repository, "figure_predictions")[0]["learner_answer"] == MODEL_WORDS + " area"
    again = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]["predictions"][0]["answered"]
    assert again["learnerAnswer"] == "panels.0.shade.0" and MODEL_WORDS not in json.dumps(again)


def test_a_figure_with_no_book_element_is_drawn_exactly_as_before(tmp_path, monkeypatch):
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: False)
    spec = plot("x", label="the model's name")
    figure, _ctx, _repository = _built(tmp_path, [spec], "s5")
    assert figure["elements"] == [] and figure["sourceCheck"]["status"] == "none"
    assert figure["sourceCheck"]["reasons"] == ["sandbox_unavailable"]
    assert "the model's name" in figure["specJson"]


def test_a_sketch_view_has_no_elements_or_source_check():
    assert not SC.grammar_row({"tier": "sketch", "spec_version": "sketch-v1"})
    assert FS.sketch_row({"tier": "sketch"})


# -- every code-owned label's writers (Astra A3, A4): plain parses back to the same value, TeX renders ------

def test_a_power_of_a_power_keeps_its_grouping_in_plain_text():
    """Astra A3: a marker at (2^3)^2 sits at 64; its SVG label said 2^3^2, which is 512."""

    from learnloop.figures import grammar as G

    node = G.parse("(2^3)^2")
    assert G.evaluate(G.parse(E.to_plain(node)), {}, {}) == G.evaluate(node, {}, {}) == 64.0


def test_a_scientific_literal_as_a_base_is_grouped_in_both_writers():
    """Astra A4: 1 \\times 10^{-3}^{2} is a KaTeX error, shown as red raw TeX."""

    from learnloop.figures import grammar as G

    node = G.parse("(1e-3)^2")
    assert E.to_tex(node, {}) == r"\left(1 \times 10^{-3}\right)^{2}"
    assert E.to_plain(node) == "(1e-3)^2"


def _generated(chance, depth: int = 0):
    """A random expression tree of the figure grammar, with the literals and shapes labels meet."""

    from learnloop.figures import grammar as G

    def literal() -> G.Node:
        text = chance.choice(["2", "3", "0.5", "10", "1e-3", "2.5e3", "1E2", "0.25", ".5", "7"])
        return G.Node("num", text=text, value=float(text))

    def name() -> G.Node:
        return G.Node("name", text=chance.choice(["x", "y", "lambda", "mu1", "a"]))

    if depth >= 4 or chance.random() < 0.2:
        return literal() if chance.random() < 0.5 else name()
    shape = chance.randrange(10)
    if shape < 5:
        op = chance.choice(["+", "-", "*", "/", "^", "^", "^"])
        return G.Node("bin", op=op, args=(_generated(chance, depth + 1), _generated(chance, depth + 1)))
    if shape == 5:
        return G.Node("neg", args=(_generated(chance, depth + 1),))
    if shape < 8:
        function = chance.choice(["sin", "exp", "sqrt", "abs", "log", "erf", "atan"])
        return G.Node("call", text=function, args=(_generated(chance, depth + 1),))
    if shape == 8:
        return G.Node("call", text=chance.choice(["min", "max"]), args=(_generated(chance, depth + 1), _generated(chance, depth + 1)))
    condition = G.Node("cmp", op=chance.choice(["<", "<=", ">", ">="]), args=(name(), literal()))
    return G.Node("piecewise", args=(condition, _generated(chance, depth + 1), _generated(chance, depth + 1)))


_POINTS = [{"x": 0.7, "y": 1.3, "lambda": 2.1, "mu1": 0.4, "a": 3.0}, {"x": -1.2, "y": 0.6, "lambda": 0.3, "mu1": 2.2, "a": 1.5}]


def test_the_plain_writer_parses_back_to_the_same_value_and_the_tex_writer_means_it_in_katex():
    """Class fix for A3 and A4: over generated trees, the plain writer's output through the figure grammar has
    the tree's value, and the TeX writer's output parses in the page's KaTeX and renders the same meaning."""

    import random

    from learnloop.figures import grammar as G
    from learnloop.figures import katex_tree as KT
    from tests import katex_meaning as M

    chance = random.Random(20261104)
    with KT.Trees() as trees, M.Renderer() as renderer:
        for _ in range(1500):
            tree = _generated(chance)
            plain = E.to_plain(tree)
            assert M.same_value(tree, G.parse(plain), _POINTS), plain
            tex = E.to_tex(tree, {})
            trees.parse(tex)  # raises KT.TreeRefused on what the page would show as red raw TeX
            meaning = M.right_hand_side(renderer.mathml("y = " + tex))
            assert M.same_value(tree, meaning, _POINTS), tex


def test_every_other_code_owned_label_template_renders_in_katex():
    """A marker, a shade, a bound readout, every panel's rendering and an AI curve: each parses in the page's KaTeX."""

    import random
    from types import SimpleNamespace

    from learnloop.figures import grammar as G
    from learnloop.figures import katex_tree as KT

    chance = random.Random(20261105)
    with KT.Trees() as trees:
        for _ in range(300):
            tree, other = _generated(chance), _generated(chance)
            body_tex, body_plain = E.to_tex(tree, {}, 2), E.to_plain(tree, 2)
            trees.parse(E.symbol_tex("x") + " = " + E.to_tex(tree, {}))
            for kind in ("shade", "highlight", "integral", "sum"):
                template = {"kind": kind, "panel": 0, "index": 0, "body_tex": body_tex, "body_plain": body_plain, "variable": "mu1"}
                for low, high in ((0, 1), (-1e-7, 2.5e21), (1e21, -0.5)):
                    words, _plain = E.template_words(template, {"from": low, "to": high}, str)
                    trees.parse(words)
                words, _plain = E.template_words(template, {"from": 0, "to": 3, "integers": (0, 3)}, str)
                trees.parse(words)
            nodes = {"matrix": ((tree, other), (other, tree)), "expr": tree, "u": tree, "v": other, "dx": tree, "dy": other, "fx": tree, "fy": other}
            for kind in ("linear_map_2d", "heatmap_2d", "vector_field_2d", "trajectory_2d", "iterate_2d"):
                tex, _plain = E._panel_tex(SimpleNamespace(kind=kind, nodes=nodes), {})
                trees.parse(tex)
            bound = G.Node("integral", text="t", args=(tree, G.Node("num", text="0", value=0.0), G.Node("num", text="1e-3", value=1e-3)))
            trees.parse(E.to_tex(G.Node("bin", op="^", args=(bound, G.Node("num", text="2", value=2.0))), {}))
            trees.parse(E.to_tex(G.Node("bin", op="*", args=(G.Node("call", text="exp", args=(tree,)), bound)), {}))
            assert E.to_plain(bound)  # the grammar's own form


def test_a_sum_or_an_integral_written_inside_a_product_is_grouped():
    from learnloop.figures import grammar as G

    tree = G.parse("sum(k^2, k, 1, 3)*x")
    assert E.to_tex(tree, {}).startswith(r"\left(\sum_{k=1}^{3}") and E.to_plain(G.parse(E.to_plain(tree))) == E.to_plain(tree)


def test_a_bound_readouts_body_is_grouped_in_its_template():
    """The words after an integral sign end at dx; a body with a sum in it needs its parentheses."""

    from learnloop.figures import spec as S

    spec = plot("x")
    spec["panels"].append({"kind": "readout", "label": "area", "expr": "integral(x + 1, x, 0, 1)"})
    compiled = S.parse_spec(spec)
    readout = {element["id"]: element for element in E.element_map(compiled, {}, {})}["panels.1"]
    assert readout["tex"].startswith(r"\int_{0}^{1} \left(x + 1\right)\,d")
    assert "of (x + 1) dx" in readout["plain"]


def _tail_bars() -> dict[str, Any]:
    spec = plot("2^(-k)", name="tail", variable="k", low=0.0, high=2.0, label="tail")
    spec["panels"] = [{"kind": "pmf_bars", "k": {"var": "k", "min": 0, "max": 2}, "series": [{"expr": "tail", "label": "tail"}],
                       "highlight": {"from": "0", "to": "1", "label": "first"}},
                      {"kind": "readout", "label": "total", "expr": "sum(tail, k, 0, 2)"}]
    return spec


@sandboxed
def test_a2_a_derived_sum_keeps_a_compound_left_hand_side_whole(tmp_path):
    """Astra A2: the book's 1-F(k)=2^{-k}: the label wrote \\sum 1-F(k) beside 1.75, the sum of the whole left-hand side."""

    from learnloop.vault.loader import load_vault

    paths, repository = build_check_vault(tmp_path / "vault", [("a", "Text", r"The tail is $1-F(k)=2^{-k}$.")])
    result = SC.check_figure(load_vault(paths.root), repository, S.parse_spec(_tail_bars()),
                             spans=[(EXTRACTION, "a", "a")], grounding="anchor")
    assert result.outcome == SC.CHECKED
    elements = {element["id"]: element for element in result.elements}
    assert elements["panels.0.series.0"]["tex"] == "1-F(k)"  # the label itself is the book's own, with no operator beside it
    readout, highlight = elements["panels.1"], elements["panels.0.highlight"]
    assert readout["role"] == "derived" and readout["tex"] == r"\sum_{k=0}^{2} \left(1-F(k)\right)"
    assert readout["plain"] == "sum for k from 0 to 2 of (1-F(k))"
    assert highlight["role"] == "derived" and highlight["tex"] == r"\sum_{k=0}^{1} \left(1-F(k)\right)"


_TERMS = (r"F(k)", r"f_{X}(k)", "p", "2", r"e^{-k}", r"\frac{1-a}{k}", r"\sqrt{1-k}", r"\bar{F}(k)", r"P(X=k)", r"\lvert k-1\rvert",
          r"\sin k", r"\left(1-k\right)", r"(1-k)", r"\text{Var}(k)", "n!", r"(1-k)^{2}", r"\ln(k)")
_SIGNS = ("-", "+", r"\cdot ", r"\times ", r"\pm ", "/")


def _left_hand_side(chance) -> tuple[str, bool]:
    """A left-hand side, and whether it was built compound: a sign, a slash or a leading sign outside every bracket, perhaps in braces or a font."""

    def term() -> str:
        return chance.choice(_TERMS)

    shape = chance.randrange(6)
    if shape == 0:
        return term(), False
    if shape == 1:
        return term() + " " + term(), False
    if shape == 2:
        return "-" + term(), True
    built = term() + chance.choice(_SIGNS) + term()
    if chance.randrange(3) == 0:
        built += chance.choice(_SIGNS) + term()
    return (f"{{{built}}}" if shape == 3 else built), True


def test_a_generated_left_hand_side_is_whole_in_every_template_in_katexs_own_mathml():
    """A2's class: the real reader, the real templates, and KaTeX's MathML read independently of its tree."""

    import random

    from learnloop.figures import book_math as B
    from learnloop.figures import katex_tree as KT
    from tests import katex_meaning as M

    chance = random.Random(20261102)
    read = {True: 0, False: 0}
    with KT.Trees() as trees, M.Renderer() as renderer:
        for _ in range(500):
            lhs, compound = _left_hand_side(chance)
            try:
                relation = B.read_relation(lhs + "=x", trees=trees)
            except B.Unreadable:
                continue
            assert relation.lhs_compound or not compound, lhs
            read[compound] += 1
            body_tex, body_plain = E.BookLabel(relation.lhs, relation.latex, "k", {}, "e", "s", 1, relation.lhs_compound, relation.lhs_plain).operand
            alone = renderer.mathml(lhs)
            for kind, bounds in (("sum", {"from": 0, "to": 2, "integers": (0, 2)}), ("highlight", {"from": 0, "to": 2, "integers": (0, 2)}),
                                 ("integral", {"from": 0, "to": 1}), ("shade", {"from": 0, "to": 1})):
                template = {"kind": kind, "body_tex": body_tex, "body_plain": body_plain, "variable": "k"}
                words, plain = E.template_words(template, bounds, str)
                assert M.whole_in_scope(renderer.mathml(words), alone, kind), (kind, words)
                assert not compound or f"({relation.lhs_plain})" in plain, (kind, plain)
    assert read[True] > 200 and read[False] > 50


def test_the_scope_reading_refuses_the_label_astra_found():
    """So the property above has teeth: the same words with no group fail it, in every template."""

    from tests import katex_meaning as M

    with M.Renderer() as renderer:
        alone = renderer.mathml("1-F(k)")
        assert not M.whole_in_scope(renderer.mathml(r"\sum_{k=0}^{2} 1-F(k)"), alone, "sum")
        assert not M.whole_in_scope(renderer.mathml(r"\int_{0}^{1} 1-F(k)\,dk"), alone, "integral")
        assert not M.whole_in_scope(renderer.mathml(r"\text{area under } 1-F(k) \text{ from } 0 \text{ to } 1"), alone, "shade")
        assert not M.whole_in_scope(renderer.mathml(r"\sum_{k=0}^{2} 1"), alone, "sum")  # a part in scope is not the whole
        assert M.whole_in_scope(renderer.mathml(r"\sum_{k=0}^{2} \left(1-F(k)\right)"), alone, "sum")


def test_a_shade_or_a_highlight_of_an_ai_curve_groups_code_s_own_rendering():
    """The same two template lines take code's rendering in the model's voice: \\sum k + 1 reads no better there."""

    bars = _bars("0", "1", expr="k + 1")
    bars["definitions"] = []
    bars["panels"][0]["series"][0]["expr"] = "k + 1"
    highlight = {element["id"]: element for element in E.element_map(S.parse_spec(bars), {}, {})}["panels.0.highlight"]
    assert highlight["role"] == "ai" and highlight["tex"] == r"\sum_{k=0}^{1} \left(k + 1\right)" and "of (k + 1)" in highlight["plain"]
    shaded = plot("1 - x", definitions=[], shades=[{"series": "the book's curve", "from": "0", "to": "1", "label": "area"}])
    shaded["panels"][0]["series"][0]["expr"] = "1 - x"
    shade = {element["id"]: element for element in E.element_map(S.parse_spec(shaded), {}, {})}["panels.0.shade.0"]
    assert shade["role"] == "ai" and r"\left(1 - x\right)" in shade["tex"]
