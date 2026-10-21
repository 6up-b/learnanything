"""The figure grammar's differential property corpus (reader workbench RW5a, fix round 3).

The parity contract between the two evaluators, and between the evaluator and
the SymPy translation, from fix round 3 on: a seeded generator writes a few
thousand random grammar expressions with the Python evaluator's verdict and
value at an environment, and

* ``tests/test_figure_property.py`` checks the file is what this module
  builds, that no value is -0, and that SymPy's reading of every translatable
  accepted expression (``grammar.sympy_problem`` is None) has the evaluator's
  value;
* ``figureGrammar.test.ts`` checks the TypeScript parser gives the same
  verdict and the TypeScript evaluator the same value on every case.

Besides the random expressions it carries fixed families: signed zeros,
empty and fractional sum ranges, reserved-looking identifiers, piecewise
comparisons, and large and small magnitudes. Regenerate after changing it:

    uv run python -m tests.figure_property_corpus --write

(outside pytest only under ``env -i`` with empty HOME, CODEX_HOME and
LEARNLOOP_CONFIG_DIR, the repository's rule for ad-hoc Python).
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures" / "figurePropertyCorpus.json"

SEED = 20261022
RANDOM_CASES = 3000
#: The relative tolerance both checks use, against the case's scale (the
#: largest magnitude any of its subexpressions takes at its environment).
RELATIVE = 1e-9
INTEGRAL = 1e-6
KNOWN = ("x", "p", "lam")
BOUND = ("k", "t")

LITERALS = ("0", "1", "2", "3", "7", "10", "0.5", "0.25", "1.5", "3.25", "0.1", "0.2", "0.3", "2.5e-8",
            "1e15", "1e300", "1e-300", "1e308")
NAMES = ("x", "p", "lam")
UNARY = ("exp", "log", "sqrt", "abs", "sin", "cos", "tan", "atan", "erf", "Phi", "floor")
COMPARISONS = ("<", "<=", ">", ">=", "==", "!=")
#: Sum and integral bodies are tame (no cancellation, moderate magnitudes),
#: so a case's scale bounds the work inside them too.
SUM_BODIES = ("k", "k*x", "0.5^k", "k^2", "(k + p)", "x/(k + 2)", "piecewise((k < 2, 1), k)", "1")
SUM_BOUNDS = ("0", "1", "2", "3", "2.5", "0.5", "-1", "-0.5", "-2.5", "x", "p", "lam", "p*3", "x + 2")
INTEGRAL_BODIES = ("t", "t^2", "exp(-t)", "t*p", "piecewise((t < 0.5, 1), 2)", "1 + t")
INTEGRAL_BOUNDS = ("0", "1", "-1", "0.5", "2", "p")
ENVIRONMENTS = (
    {"x": 0.7, "p": 0.3, "lam": 1.5},
    {"x": -0.0, "p": 0.0, "lam": 1.0},
    {"x": 2.5, "p": -0.0, "lam": 3.0},
    {"x": -1.25, "p": 0.6, "lam": 0.5},
    {"x": 1e-300, "p": 2.0, "lam": 1e15},
    {"x": 1e300, "p": 0.1, "lam": 2.0},
    {"x": 3.0, "p": 1.0, "lam": 1e-8},
    {"x": -7.5, "p": 0.25, "lam": 10.0},
)


def _fixed() -> list[tuple[str, str, dict[str, float]]]:
    env = ENVIRONMENTS[0]
    negative = ENVIRONMENTS[1]
    signed_zero = [
        "-0", "0*-1", "-(x - x)", "min(0, -0)", "max(-0, 0)", "min(-0, 0)", "1/min(0, -0)", "1/max(-0, 0)",
        "1/min(-0, 0)", "1/(0*-1)", "1/-0", "piecewise((1/min(0, -0) < 0, 1), 2)",
        "piecewise((1/max(-0, 0) > 0, 1), 2)", "1/floor(-0)", "floor(-0.5)*0", "1/(floor(-0.5)*0)", "atan(-0)",
        "1/atan(-0)", "1/sin(-0)", "1/tan(-0)", "1/(x - x)", "1/-(x - x)", "1/abs(-0)", "sqrt(-0)", "1/sqrt(-0)",
        "1/((-0)^3)", "(-0)^0.5", "1/((-1)*0)", "exp(-1e300)", "1/exp(-1e300)", "1/(-exp(-1e300))",
        "1/(-1e-300*1e-300)", "1/erf(-0)", "1/(x*-0)", "1/(-x*0)", "sum(-0, k, 1, 3)", "1/sum(-0, k, 1, 3)",
        "1/integral(-0, t, 0, 1)", "1/piecewise((x < 0, -0), -0)",
    ]
    sums = [
        "sum(1, k, 2, 0)", "sum(1, k, 0.5, 2.5)", "sum(k, k, -0.5, 0.5)", "sum(k, k, 3, 3)", "sum(1, k, 3, 2.5)",
        "sum(k^2, k, -2.5, -0.5)", "sum(1, k, 0, 0.9999999999)", "sum(1, k, 2.0000000001, 2)",
        "sum(1, k, 1.9999999999, 2)", "sum(k, k, x, x + 3)", "sum(1, k, p, p)", "sum(1, k, lam, lam - 1)",
        "sum(1, k, 0, 20000)", "sum(1, k, 0, 10000)", "sum(k, k, -3, -5)", "sum(0.5^k, k, 0, 60)",
        "sum(1, k, -0, 0)", "sum(x/(k + 2), k, 0.5, 4.5)", "sum(1, k, 1e300, 1e300)",
    ]
    reserved = [
        "__proto__", "sum(__proto__, __proto__, 1, 3)", "constructor", "toString + 1", "valueOf", "hasOwnProperty",
        "isPrototypeOf(1)", "propertyIsEnumerable", "toLocaleString", "_x", "x_1", "lam_2", "__defineGetter__",
        "sum(k, constructor, 1, 2)", "integral(t, toString, 0, 1)", "sum(valueOf, valueOf, 1, 2)", "prototype",
        "x2 + 1", "Lam", "piecewise((__proto__ < 1, 1), 2)",
    ]
    comparisons = [
        "piecewise((x < x, 1), 2)", "piecewise((x <= x, 1), 2)", "piecewise((0.1 + 0.2 == 0.3, 1), 2)",
        "piecewise((0.1 + 0.2 > 0.3, 1), 2)", "piecewise((x <= 0 and p > 0 or lam != 1, 3), 4)",
        "piecewise((x < 0, -1), (x == 0, 0), 1)", "piecewise((0/0 < 1, 1), (0/0 != 1, 2), 3)",
        "piecewise((1e-300*1e-300 > 0, 1), 2)", "piecewise((1e300*1e300 > 1e308, 1), 2)",
    ]
    magnitudes = [
        "1e300*10", "1e300*1e300", "1e-300*1e-300", "1e-300/1e300", "(1e16 + 1) - 1e16", "1e308 + 1e308",
        "-1e308 - 1e308", "exp(709)", "exp(710)", "log(1e-300)", "2^1023", "2^1024", "0.5^1074", "0.5^1075",
        "atan(1e300)", "Phi(-40)", "Phi(40)", "erf(1e-300)", "sin(1e300)", "cos(1e15)", "tan(1e15)",
        "sqrt(1e308)", "log(1e308)", "(1e-300)^0.5", "1/(1e-300*1e-300)", "atan(1e300*1e300)",
    ]
    cases = []
    for family, expressions in (("signed_zero", signed_zero), ("sum_range", sums), ("reserved", reserved),
                                ("comparison", comparisons), ("magnitude", magnitudes)):
        for index, expr in enumerate(expressions):
            cases.append((f"{family}_{index}", expr, env))
            if family == "signed_zero":
                cases.append((f"{family}_{index}_zero_env", expr, negative))
    return cases


class _Generator:
    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def pick(self, options):
        return options[self.rng.randrange(len(options))]

    def atom(self) -> str:
        return self.pick(LITERALS) if self.rng.random() < 0.5 else self.pick(NAMES)

    def condition(self, depth: int) -> str:
        text = f"{self.expr(depth - 1)} {self.pick(COMPARISONS)} {self.expr(depth - 1)}"
        roll = self.rng.random()
        if roll < 0.15:
            text += f" and {self.expr(depth - 1)} {self.pick(COMPARISONS)} {self.expr(depth - 1)}"
        elif roll < 0.3:
            text += f" or {self.expr(depth - 1)} {self.pick(COMPARISONS)} {self.expr(depth - 1)}"
        return text

    def expr(self, depth: int) -> str:
        if depth <= 0 or self.rng.random() < 0.22:
            return self.atom()
        roll = self.rng.random()
        if roll < 0.36:
            return f"({self.expr(depth - 1)} {self.pick(('+', '-', '*', '/', '^'))} {self.expr(depth - 1)})"
        if roll < 0.44:
            return f"-{self.expr(depth - 1)}"
        if roll < 0.60:
            return f"{self.pick(UNARY)}({self.expr(depth - 1)})"
        if roll < 0.68:
            count = 2 if self.rng.random() < 0.7 else 3
            args = ", ".join(self.expr(depth - 1) for _ in range(count))
            return f"{self.pick(('min', 'max'))}({args})"
        if roll < 0.82:
            branches = "".join(f"({self.condition(depth)}, {self.expr(depth - 1)}), "
                               for _ in range(1 if self.rng.random() < 0.7 else 2))
            return f"piecewise({branches}{self.expr(depth - 1)})"
        if roll < 0.95:
            return f"sum({self.pick(SUM_BODIES)}, k, {self.pick(SUM_BOUNDS)}, {self.pick(SUM_BOUNDS)})"
        return f"integral({self.pick(INTEGRAL_BODIES)}, t, {self.pick(INTEGRAL_BOUNDS)}, {self.pick(INTEGRAL_BOUNDS)})"


def encode(value: float) -> float | str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


def verdict(expr: str):
    """``(node, None)`` for an accepted expression, ``(None, why)`` otherwise."""

    from learnloop.figures import grammar as G
    from learnloop.figures import spec as S

    try:
        node = G.parse(expr)
        G.check_names(node, known=frozenset(KNOWN) | set(BOUND), definitions={})
        if not set(S.expanded_free(node, {})) <= set(KNOWN):
            raise G.GrammarError("unbound")
    except G.GrammarError as exc:
        return None, str(exc)
    return node, None


def scale(node: Any, env: dict[str, float]) -> float:
    """The largest finite magnitude any subexpression takes at ``env`` (a
    subexpression of a sum's or an integral's body, which reads its bound
    variable, is NaN here and ignored), and at least 1."""

    from learnloop.figures import grammar as G

    largest = 1.0
    for sub in G.walk(node):
        if sub.kind in ("cmp", "and", "or"):
            continue
        value = G.evaluate(sub, env)
        if math.isfinite(value):
            largest = max(largest, abs(value))
    return largest


def cases() -> list[tuple[str, str, dict[str, float]]]:
    generator = _Generator(SEED)
    found = _fixed()
    for index in range(RANDOM_CASES):
        env = ENVIRONMENTS[generator.rng.randrange(len(ENVIRONMENTS))]
        found.append((f"random_{index}", generator.expr(generator.rng.randint(1, 4)), env))
    return found


def build() -> dict[str, Any]:
    from learnloop.figures import grammar as G

    rows = []
    for case_id, expr, env in cases():
        node, _why = verdict(expr)
        row: dict[str, Any] = {"id": case_id, "expr": expr, "env": env, "accepted": node is not None}
        if node is not None:
            row["expected"] = encode(G.evaluate(node, env))
            row["scale"] = scale(node, env)
            row["integral"] = any(sub.kind == "integral" for sub in G.walk(node))
        rows.append(row)
    return {
        "version": 1,
        "note": "Generated by tests/figure_property_corpus.py; read by tests/test_figure_property.py and "
                "figureGrammar.test.ts. The parity contract (fix round 3).",
        "tolerance": {"relative": RELATIVE, "integral": INTEGRAL},
        "known": list(KNOWN),
        "bound": list(BOUND),
        "cases": rows,
    }


def render() -> str:
    data = build()
    lines = [json.dumps(row, sort_keys=True, ensure_ascii=False) for row in data.pop("cases")]
    head = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return head[:-1] + ', "cases": [\n' + ",\n".join(lines) + "\n]}\n"


if __name__ == "__main__":
    if "--write" in sys.argv:
        CORPUS_PATH.write_text(render(), encoding="utf-8")
        print(f"wrote {CORPUS_PATH}")
    else:
        sys.stdout.write(render())
