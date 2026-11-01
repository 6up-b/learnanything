"""RW5d P2b: a Manim figure's declared functions and their checks (spec §9b.1, §9b.4; G-SM26).

* Extraction keeps only the declared top-level defs and the module
  constants they read, with math/numpy imports; the extracted module never
  names manim (the checks run without importing it).
* A function that needs anything else is not checkable: its claim is
  dropped from the check list, never failed.
* A claim that fails (a value off the stated expression, a non-finite value,
  an exception at a grid point, a bound exceeded) is a failure in code's words.
* ``plotted_from`` is AST-checked against the scene's plot calls.
* The hostile extraction corpus: path escapes, /proc probes, network,
  subprocess, fork bombs and dunder tricks never reach the extracted module.

The functions run in this process through a test stand-in for the sandbox
(:class:`tests.rich_fixtures.InProcessRunner`), never Manim or bubblewrap.
"""

from __future__ import annotations

import pytest

from learnloop.figures import manim_figure as M
from tests import rich_fixtures as RF


class _Output:
    def __init__(self, **fields):
        self.__dict__.update(fields)


def _figure(scene=RF.SCENE, declared=None):
    return M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared)))


def test_extraction_keeps_the_declared_defs_and_their_constants_and_never_manim():
    figure = _figure()
    extraction = M.extract_functions(figure.scene_code, figure.functions)
    assert extraction.checkable == ["x"]
    assert "helper_uses_manim" in extraction.dropped
    assert "ValueTracker" in extraction.dropped["helper_uses_manim"]
    assert "manim" not in extraction.source and "Scene" not in extraction.source
    assert "import math" in extraction.source and "import numpy as np" in extraction.source
    assert "def x(t, a, b)" in extraction.source
    assert "DAMPING" not in extraction.source  # read by the scene only, not by x


def test_good_claims_pass_with_scoped_check_lines_and_an_unextractable_claim_is_dropped():
    runner = RF.InProcessRunner()
    report = M.check_claims(_figure(), runner=runner)
    assert not report.failed, report.failures
    assert [(line["kind"], line["function"]) for line in report.checks] == [("equals", "x"), ("invariant", "x")]
    assert report.checks[0]["expr"] == "exp(a*t)*cos(b*t)" and report.checks[0]["settings"] == 27
    assert report.checks[0]["plotted"] is True and report.plotted == ["x"]
    # G-SM26: the claim on the function that needs Manim is dropped, not failed.
    assert report.not_checkable == [{"function": "helper_uses_manim",
                                     "reason": "it needs 'ValueTracker', which is neither math, numpy, a module "
                                               "constant nor another declared function"}]
    assert len(runner.sources) == 1


@pytest.mark.parametrize("claim,expected", [
    ({"kind": "equals", "function": "x", "expr": "exp(a*t)*cos(b*t) + 1"}, "but exp(a*t)*cos(b*t) + 1"),
    ({"kind": "invariant", "function": "x", "property": "nonnegative"}, "is negative"),
    ({"kind": "invariant", "function": "x", "property": "bounded", "bound": 0.5}, "exceeds the stated bound"),
    ({"kind": "equals", "function": "x", "expr": "exp(a*t)*cos(b*t"}, "grammar refuses"),
    ({"kind": "equals", "function": "x", "expr": "exp(q*t)"}, "grammar refuses"),
])
def test_a_wrong_claim_fails_in_codes_words(claim, expected):
    declared = {"functions": RF.DECLARED["functions"][:1], "claims": [claim], "plotted_from": []}
    report = M.check_claims(_figure(declared=declared), runner=RF.InProcessRunner())
    assert report.failed and expected in report.failures[0], report.failures


def test_an_exception_or_a_non_finite_value_at_a_grid_point_fails():
    scene = RF.SCENE.replace("return math.exp(a * t) * math.cos(b * t)", "return 1.0 / (t - 3.0)")
    declared = {"functions": RF.DECLARED["functions"][:1],
                "claims": [{"kind": "invariant", "function": "x", "property": "finite"}], "plotted_from": []}
    report = M.check_claims(_figure(scene=scene, declared=declared), runner=RF.InProcessRunner())
    assert report.failed and "raised ZeroDivisionError" in report.failures[0]


def test_a_sandbox_that_cannot_run_is_a_failure_never_a_pass():
    report = M.check_claims(_figure(), runner=lambda source, points: {"error": "timed out after 30s"})
    assert report.failed and "timed out" in report.failures[0]


def test_no_claims_means_nothing_runs_and_the_figure_is_not_checked():
    calls = []
    declared = {"functions": RF.DECLARED["functions"][:1], "claims": [], "plotted_from": []}
    report = M.check_claims(_figure(declared=declared), runner=lambda *a: calls.append(a) or {"results": {}})
    assert report.checks == [] and not report.failed and calls == []


def test_plotted_from_is_ast_checked():
    assert M.plotted_from_ok(RF.SCENE, "x")
    assert not M.plotted_from_ok(RF.SCENE, "helper_uses_manim")
    drawn_elsewhere = RF.SCENE.replace("axes.plot(lambda t: x(t, -DAMPING, 2.0), color=BLUE)",
                                       "Dot(point=[x(1, -0.5, 2.0), 0, 0])")
    figure = _figure(scene=drawn_elsewhere)
    report = M.check_claims(figure, runner=RF.InProcessRunner())
    assert report.plotted == [] and report.checks[0]["plotted"] is False


def test_declared_json_problems_are_reported_for_the_second_attempt():
    _f, _c, _p, problems = M.parse_declared({"functions": [{"name": "checked_value", "args": []}],
                                             "claims": [{"kind": "equals", "function": "nope", "expr": "1"}],
                                             "plotted_from": [{"function": "nope"}], "extra": 1})
    joined = " ".join(problems)
    assert "unknown keys" in joined and "not an allowed identifier" in joined  # a name can't impersonate a check
    assert "'nope', which is not a declared scalar function" in joined
    with pytest.raises(M.ManimFigureError):
        M.parse_figure(_Output(scene_code="", scene_class="", title="", narration_md="", declared_json="[]"))


#: Hostile scenes (spec §9b.5's corpus for Manim): each declared function
#: reaches for something outside math/numpy; extraction drops it, so nothing
#: of it reaches the sandboxed run (and the scene validator refuses most of
#: them before the render too).
HOSTILE = {
    "path_escape": "def f(t):\n    return len(open('/etc/passwd').read()) + t\n",
    "proc_probe": "def f(t):\n    return len(__import__('os').listdir('/proc')) + t\n",
    "network": "import socket\n\ndef f(t):\n    socket.create_connection(('1.1.1.1', 53))\n    return t\n",
    "subprocess": "def f(t):\n    import subprocess\n    return subprocess.call(['true']) + t\n",
    "fork_bomb": "import os\n\ndef f(t):\n    while True:\n        os.fork()\n",
    "dunder": "def f(t):\n    return ().__class__.__base__.__subclasses__()[0] and t\n",
    "globals": "def f(t):\n    global g\n    g = t\n    return t\n",
    "home": "from pathlib import Path\n\ndef f(t):\n    return len(list(Path.home().iterdir())) + t\n",
    "eval": "def f(t):\n    return eval('t')\n",
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_hostile_functions_are_never_extracted(name):
    scene = "from manim import *\nimport math\n\n" + HOSTILE[name] + "\nclass S(Scene):\n    def construct(self):\n        pass\n"
    function = M.Function("f", (M.Argument("t", 0.0, 1.0),))
    extraction = M.extract_functions(scene, [function])
    assert extraction.checkable == [] and "f" in extraction.dropped, extraction
    assert extraction.source == ""


def test_the_scene_validator_refuses_the_hostile_imports_before_any_render():
    from learnloop.content.authoring.concept_animation import validate_scene_code

    for name in ("network", "fork_bomb", "home", "path_escape", "dunder", "eval"):
        scene = "from manim import *\n" + HOSTILE[name] + "\nclass S(Scene):\n    def construct(self):\n        pass\n"
        _cls, violations = validate_scene_code(scene)
        assert violations, name


# --- Codex review F4: retained constants must stay what the extraction saw ------

_MUTATING_SCENES = {
    "augmented": "A = 1\nA += 1\n",
    "rebound": "A = 1\nA = 2\n",
    "global": "A = 1\n\ndef bump():\n    global A\n    A = 5\n",
    "item": "import numpy as np\nA = np.array([1.0])\nA[0] = 2.0\n",
    "method": "import numpy as np\nA = np.array([1.0])\nA.fill(2.0)\n",
    "handed": "import numpy as np\nA = np.array([1.0])\nnp.copyto(A, 2.0)\n",
    "out": "import numpy as np\nA = np.array([1.0])\n\ndef g(t):\n    return np.add(A, t, out=A)\n",
}


@pytest.mark.parametrize("prelude", sorted(_MUTATING_SCENES))
def test_a_constant_the_scene_changes_makes_its_function_not_checkable(prelude):
    """F4: ``A = 1; A += 1; def f(t): return A * t`` used to pass ``f(t) = t``."""

    scene = "from manim import *\n" + _MUTATING_SCENES[prelude] + (
        "\n\ndef f(t):\n    return float(A[0]) * t\n" if prelude in ("item", "method", "handed", "out")
        else "\n\ndef f(t):\n    return A * t\n") + (
        "\n\nclass S(Scene):\n    def construct(self):\n        axes = Axes()\n        self.play(Create(axes.plot(f)))\n")
    declared = {"functions": [{"name": "f", "args": [{"name": "t", "min": 0, "max": 2}]}],
                "claims": [{"kind": "equals", "function": "f", "expr": "t"}], "plotted_from": [{"function": "f"}]}
    figure = M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared, scene_class="S")))
    report = M.check_claims(figure, runner=RF.InProcessRunner())
    assert report.checks == [] and not report.failed
    (dropped,) = report.not_checkable
    assert dropped["function"] == "f" and "'A'" in dropped["reason"], dropped


def test_the_finding_f4_reproduction_issues_no_check_line():
    scene = ("from manim import *\nA = 1\nA += 1\n\ndef f(t):\n    return A * t\n\n"
             "class S(Scene):\n    def construct(self):\n        axes = Axes()\n        self.play(Create(axes.plot(f)))\n")
    declared = {"functions": [{"name": "f", "args": [{"name": "t", "min": 0, "max": 2}]}],
                "claims": [{"kind": "equals", "function": "f", "expr": "t"}], "plotted_from": [{"function": "f"}]}
    report = M.check_claims(M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared,
                                                                      scene_class="S"))),
                            runner=RF.InProcessRunner())
    assert report.checks == [] and report.plotted == []


def test_an_immutable_constant_the_scene_only_reads_is_kept():
    scene = ("from manim import *\nimport math\nK = 2 * math.pi\n\ndef f(t):\n    return K * t\n\n"
             "class S(Scene):\n    def construct(self):\n        self.add(Text(str(K)))\n")
    declared = {"functions": [{"name": "f", "args": [{"name": "t", "min": 0, "max": 1}]}],
                "claims": [{"kind": "equals", "function": "f", "expr": "2*pi*t"}]}
    report = M.check_claims(M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared,
                                                                      scene_class="S"))),
                            runner=RF.InProcessRunner())
    assert not report.failed and [line["function"] for line in report.checks] == ["f"]


def test_a_declared_function_bound_twice_is_not_checkable():
    scene = ("from manim import *\n\ndef f(t):\n    return t\n\nf = lambda t: 100 * t\n\n"
             "class S(Scene):\n    def construct(self):\n        pass\n")
    declared = {"functions": [{"name": "f", "args": [{"name": "t", "min": 0, "max": 1}]}],
                "claims": [{"kind": "equals", "function": "f", "expr": "t"}]}
    report = M.check_claims(M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared,
                                                                      scene_class="S"))),
                            runner=RF.InProcessRunner())
    assert report.checks == [] and report.not_checkable[0]["function"] == "f"


# --- Codex review F5: the plotted function is resolved by binding and argument -----

_F5_HEAD = "from manim import *\n\ndef f(t):\n    return t\n\ndef g(t):\n    return t * t\n\n"


@pytest.mark.parametrize("body, plotted", [
    ("axes.plot(f)", True),
    ("axes.plot(function=f)", True),
    ("axes.plot(lambda t: f(t))", True),
    ("ParametricFunction(lambda t: np.array([t, f(t), 0]))", True),
    # The finding: construct rebinds f before plotting it.
    ("f = lambda t: 100 * t\n        axes.plot(f)", False),
    # A name in another argument of the plot call is not its function.
    ("axes.plot(g, x_range=[0, f(1)])", False),
    ("axes.plot(g, color=f)", False),
    # A lambda that takes f as its own argument.
    ("axes.plot(lambda f: f)", False),
    # always_redraw's lambda is not a curve's function; the plot inside it is what counts.
    ("always_redraw(lambda: Dot(axes.c2p(1, f(1))))", False),
    ("always_redraw(lambda: axes.plot(f))", True),
])
def test_plotted_from_resolves_the_binding_and_the_function_argument(body, plotted):
    scene = _F5_HEAD + f"class S(Scene):\n    def construct(self):\n        axes = Axes()\n        {body}\n"
    assert M.plotted_from_ok(scene, "f") is plotted


def test_a_rebound_plot_name_keeps_the_function_check_and_drops_the_curve():
    scene = _F5_HEAD + ("class S(Scene):\n    def construct(self):\n        axes = Axes()\n"
                        "        f = lambda t: 100 * t\n        self.play(Create(axes.plot(f)))\n")
    declared = {"functions": [{"name": "f", "args": [{"name": "t", "min": 0, "max": 1}]}],
                "claims": [{"kind": "equals", "function": "f", "expr": "t"}], "plotted_from": [{"function": "f"}]}
    report = M.check_claims(M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared,
                                                                      scene_class="S"))),
                            runner=RF.InProcessRunner())
    (line,) = report.checks
    assert line["function"] == "f" and line["plotted"] is False and report.plotted == []


# --- Codex review F2: the oracle's work and the whole check's wall clock are bounded --

_ZERO_SCENE = "from manim import *\n\ndef f(t):\n    return 0.0\n\nclass S(Scene):\n    def construct(self):\n        pass\n"


def _expensive_figure(claims=8):
    body = "+".join(["(t-t)"] * 32)
    expr = f"sum({body}, k, 0, 10000)"
    assert len(expr) <= 400
    declared = {"functions": [{"name": "f", "args": [{"name": "t", "min": 0, "max": 1}, {"name": "u", "min": 0,
                                                                                         "max": 1},
                                                    {"name": "v", "min": 0, "max": 1}, {"name": "w", "min": 0,
                                                                                         "max": 1}]}],
                "claims": [{"kind": "equals", "function": "f", "expr": expr}] * claims}
    scene = _ZERO_SCENE.replace("def f(t):", "def f(t, u, v, w):")
    return M.parse_figure(_Output(**RF.scene_output(scene=scene, declared=declared, scene_class="S")))


def test_a_claim_set_past_the_work_cap_is_refused_before_the_oracle_runs():
    """F2: 81 settings x 8 claims of a 10,001-term sum (about 823 million steps) used to run unmetered."""

    import time

    started = time.monotonic()
    report = M.check_claims(_expensive_figure(), runner=RF.InProcessRunner())
    assert report.failed and "more computation than checking may do" in report.failures[0]
    assert report.checks == [] and time.monotonic() - started < 10


def test_the_meter_stops_the_oracle_even_when_the_estimate_falls_short(monkeypatch):
    import time

    monkeypatch.setattr(M, "expression_steps", lambda node, ranges: 1)  # an estimate that misses everything
    monkeypatch.setattr(M, "MAX_CLAIM_WORK", 200_000)
    started = time.monotonic()
    report = M.check_claims(_expensive_figure(), runner=RF.InProcessRunner())
    assert report.failed and "more computation than checking may do" in report.failures[0]
    assert time.monotonic() - started < 10


def test_the_whole_check_has_one_deadline(monkeypatch):
    monkeypatch.setattr(M, "expression_steps", lambda node, ranges: 1)
    monkeypatch.setattr(M, "CHECK_SECONDS", 0.0)
    report = M.check_claims(_expensive_figure(claims=1), runner=RF.InProcessRunner())
    assert report.failed and "longer than 0 s to check" in report.failures[0]


def test_a_cancel_reaches_a_long_oracle_phase(monkeypatch):
    class Cancelled(Exception):
        pass

    def interrupt():
        raise Cancelled()

    monkeypatch.setattr(M, "expression_steps", lambda node, ranges: 1)
    monkeypatch.setattr(M, "INTERRUPT_SECONDS", 0.0)
    with pytest.raises(Cancelled):
        M.check_claims(_expensive_figure(claims=1), runner=RF.InProcessRunner(), interrupt=interrupt)
