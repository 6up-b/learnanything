"""One retrievability function (refactor RE2; spec_recognition_and_effort_v1 §6).

FSRS-6's forgetting curve has one expression, ``scheduling.fsrs._curve``, under three entry points:
``forgetting_curve`` (plain stability, for FSRS's own update, the weight fit and its evaluation), and the read every
other caller makes, ``retrievability`` (scalar) and ``retrievability_array`` (float64 arrays). RE8's effective
stability changes what a read returns, in one place, only if nothing else computes the curve or calls
``forgetting_curve``: the guard below fails on either.

The two read forms are not equal bit for bit: numpy's ``power`` and the C library's ``pow`` differ in the last bit
on about one input in twenty on a CPU with AVX-512 (ledger RE2-1), so element-wise they agree to one ulp, and
exactly on the edge inputs.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from learnloop.router_objective.memory import Fsrs
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, forgetting_curve, retrievability, retrievability_array
from tests.ast_cache import python_files, source_ast, source_text

ROOT = Path(__file__).resolve().parents[1]
W = FSRS6_DEFAULT_WEIGHTS

#: Modules that may call ``forgetting_curve`` (the curve at plain stability), and why.
FORGETTING_CURVE_CALLERS = {
    "src/learnloop/scheduling/fsrs.py": "defines it; apply_review is FSRS's own update",
    "src/learnloop/scheduling/fsrs_fitting.py": "fits the curve's weights against observed reviews (plain stability)",
    "src/learnloop/scheduling/evaluation.py": "evaluates a weight set's calibration (plain stability)",
}

#: Modules that may write the curve's arithmetic (weight 20, the decay, or FSRS-6's 0.9), and why.
CURVE_ARITHMETIC = {
    "src/learnloop/scheduling/fsrs.py": "the one expression (_curve) and its inverse, interval_for_retention",
    "src/learnloop/scheduling/intent/recall_targets.py": "the inverse curve's interval ratio for a recall target "
                                                         "(days, not a read of recall; RE8's stability cancels in it)",
}

ENTRY_POINTS = {"forgetting_curve", "retrievability_array"}


def _decay_like(node: ast.AST) -> bool:
    """A name, attribute or subscript that reads the decay: ``decay``, ``w[20]``, ``weights[20]``."""

    if isinstance(node, ast.Name):
        return "decay" in node.id.lower()
    if isinstance(node, ast.Attribute):
        return "decay" in node.attr.lower()
    if isinstance(node, ast.Subscript):
        return isinstance(node.slice, ast.Constant) and node.slice.value == 20
    return False


def curve_offences(tree: ast.Module) -> list[tuple[int, str]]:
    """Every place a module reaches for the curve itself: a reference to ``forgetting_curve``, a definition of an
    entry point, weight 20 read, a power whose exponent negates the decay, or FSRS-6's ``0.9 ** …``."""

    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(alias.name == "forgetting_curve" for alias in node.names):
            found.append((node.lineno, "imports forgetting_curve"))
        elif isinstance(node, ast.Name) and node.id == "forgetting_curve":
            found.append((node.lineno, "names forgetting_curve"))
        elif isinstance(node, ast.Attribute) and node.attr == "forgetting_curve":
            found.append((node.lineno, "reads .forgetting_curve"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ENTRY_POINTS:
            found.append((node.lineno, f"defines {node.name}"))
        elif isinstance(node, ast.Subscript) and _decay_like(node) and not isinstance(node.slice, ast.Slice):
            found.append((node.lineno, "reads weight 20 (the decay)"))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if isinstance(node.left, ast.Constant) and node.left.value == 0.9:
                found.append((node.lineno, "raises FSRS-6's 0.9 to a power"))
            elif any(isinstance(sub, ast.UnaryOp) and isinstance(sub.op, ast.USub) and _decay_like(sub.operand)
                     for sub in ast.walk(node.right)):
                found.append((node.lineno, "raises to the negated decay"))
    return found


def _sources() -> list[Path]:
    return [path for top in ("src", "scripts") for path in python_files(ROOT / top) if "__pycache__" not in path.parts]


def test_no_module_computes_the_curve_or_calls_forgetting_curve_outside_the_allowed_ones():
    offences = []
    for path in _sources():
        rel = path.relative_to(ROOT).as_posix()
        for line, what in curve_offences(source_ast(source_text(path))):
            arithmetic = what not in {"imports forgetting_curve", "names forgetting_curve", "reads .forgetting_curve"}
            if arithmetic and rel in CURVE_ARITHMETIC:
                continue
            if not arithmetic and rel in FORGETTING_CURVE_CALLERS:
                continue
            offences.append(f"{rel}:{line}: {what}")
    assert not offences, (
        "The forgetting curve is computed in one place, scheduling/fsrs.py (refactor RE2): a read of a learner's "
        "recall calls fsrs.retrievability (scalar) or fsrs.retrievability_array (arrays), so RE8's effective "
        "stability changes every read at once; forgetting_curve is the plain-stability curve for FSRS's own update, "
        "fit and evaluation only (" + "; ".join(f"{k}: {v}" for k, v in FORGETTING_CURVE_CALLERS.items()) + ").\n"
        + "\n".join(offences))


def test_every_allowance_is_still_used():
    used = {path.relative_to(ROOT).as_posix(): curve_offences(source_ast(source_text(path))) for path in _sources()}
    for rel in FORGETTING_CURVE_CALLERS:
        assert any("forgetting_curve" in what for _line, what in used[rel]), f"{rel} no longer calls forgetting_curve"
    for rel in CURVE_ARITHMETIC:
        assert any("forgetting_curve" not in what for _line, what in used[rel]), f"{rel} no longer needs the allowance"


@pytest.mark.parametrize("snippet", [
    # the router objective's vectorized copy as it stood before RE2
    "def retrievability(self, stability, elapsed):\n    w = self.weights\n    decay = w[20]\n"
    "    factor = 0.9 ** (1 / -decay) - 1\n    return (1 + factor * elapsed / stability) ** (-decay)\n",
    "from learnloop.scheduling.fsrs import forgetting_curve\nr = forgetting_curve(1.0, 2.0)\n",
    "from learnloop.scheduling import fsrs\nr = fsrs.forgetting_curve(1.0, 2.0)\n",
    "r = (1 + f * e / s) ** -weights[20]\n",
])
def test_the_guard_sees_a_copy_and_a_direct_call(snippet):
    assert curve_offences(source_ast(snippet))


def test_the_guard_passes_a_read():
    assert not curve_offences(source_ast(
        "from learnloop.scheduling.fsrs import retrievability\nr = retrievability(1.0, 2.0)\n"
        "m = 2.0 ** (-elapsed / halflife)\nf = w[11] * d ** (-w[12])\n"))


# --- the one function, with plain values -----------------------------------------------------------------------

KNOWN = [  # (stability, elapsed days, weights' decay or None for the defaults, recall), computed at RE2's base
    (10.0, 30.0, None, 0.8093881035731708),
    (2.3065, 1.0, None, 0.9468474993825461),
    (1.2931, 7.0, None, 0.7527794957805253),
    (36.5, 365.25, None, 0.6927602576838463),
    (10.0, 30.0, 0.5, 0.7661308776828738),
]


def _weights(decay: float | None) -> tuple[float, ...]:
    return W if decay is None else (*W[:20], decay)


@pytest.mark.parametrize(("stability", "elapsed", "decay", "recall"), KNOWN)
def test_known_values(stability, elapsed, decay, recall):
    assert retrievability(stability, elapsed, _weights(decay)) == recall
    assert retrievability_array(np.array([stability]), np.array([elapsed]), _weights(decay))[0] == pytest.approx(
        recall, rel=0, abs=math.ulp(recall))


def test_the_curve_passes_0_9_when_elapsed_equals_stability():
    for stability in (0.5, 4.0, 100.0):
        assert retrievability(stability, stability) == pytest.approx(0.9, rel=0, abs=1e-15)


def test_edge_inputs():
    assert retrievability(5.0, 0.0) == 1.0
    assert retrievability(5.0, -3.0) == 1.0  # a clock skew reads as no time passed
    for stability in (None, 0.0, -1.0):
        assert retrievability(stability, 3.0) == 0.0
    assert 0.0 < retrievability(0.001, 1e9) < retrievability(0.001, 1e6) < 0.1  # a power law's long tail
    stability = np.array([5.0, 5.0, 0.0, -1.0, np.nan, 0.001])
    elapsed = np.array([0.0, -3.0, 3.0, 3.0, 3.0, 1e9])
    out = retrievability_array(stability, elapsed, W)
    assert out.dtype == np.float64 and out.shape == (6,)
    assert list(out[:5]) == [1.0, 1.0, 0.0, 0.0, 0.0]
    assert 0.0 < out[5] < 0.1
    assert retrievability_array(np.array([5.0], dtype=np.float32), np.array([0.0], dtype=np.float32), W).dtype == np.float64


def test_the_read_is_the_plain_curve_today():
    rng = np.random.default_rng(1)
    for stability, elapsed in zip(np.exp(rng.uniform(math.log(1e-3), math.log(1e5), 2000)), rng.uniform(0, 3650, 2000), strict=True):
        assert retrievability(float(stability), float(elapsed), W) == forgetting_curve(float(stability), float(elapsed), W)


def test_the_array_form_equals_the_scalar_to_one_ulp_element_by_element():
    rng = np.random.default_rng(2)
    stability = np.exp(rng.uniform(math.log(1e-3), math.log(1e5), 4000))
    elapsed = np.concatenate([np.zeros(100), rng.uniform(0, 1, 1300), rng.uniform(0, 30, 1300), rng.uniform(0, 3650, 1300)])
    for decay in (None, 0.1, 0.5, 0.8):
        weights = _weights(decay)
        out = retrievability_array(stability, elapsed, weights)
        one_by_one = [retrievability_array(np.array([s]), np.array([e]), weights)[0] for s, e in zip(stability, elapsed, strict=True)]
        assert out.tobytes() == np.array(one_by_one).tobytes()  # a value does not depend on the array around it
        scalar = np.array([retrievability(float(s), float(e), weights) for s, e in zip(stability, elapsed, strict=True)])
        assert np.all(np.abs(out - scalar) <= np.spacing(scalar))
        assert np.all(out[:100] == 1.0) and np.all(scalar[:100] == 1.0)


def test_the_memory_models_retrievability_is_the_array_form():
    rng = np.random.default_rng(3)
    stability, elapsed = rng.uniform(0.5, 40, (64, 22)), rng.uniform(0, 30, (64, 22))
    assert Fsrs(W).retrievability(stability, elapsed).tobytes() == retrievability_array(stability, elapsed, W).tobytes()
