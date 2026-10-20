"""The figure grammar's golden corpus (reader workbench RW5a; spec §8.2, G21, G22, G45).

One corpus, run by both evaluators: ``tests/test_figure_grammar.py`` (Python)
and ``apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.test.ts``
(TypeScript). This module holds the cases; the JSON file beside the
TypeScript twin is what both suites read. Regenerate it after changing a case:

    uv run python -m tests.figure_corpus --write

Each expression case carries the Python evaluator's value (``expected``) and,
where one exists, an independent reference (a closed form, or mpmath at 30
digits) that the Python test checks the evaluator against. Figure cases carry
:func:`learnloop.figures.spec.evaluate_figure`'s output at each parameter set.
The fuzz cases are random token strings with the Python parser's verdict and
value: the TypeScript parser must agree on each.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures" / "figureGoldenCorpus.json"

RELATIVE = 1e-9
INTEGRAL = 1e-6

#: The dialogue's flagship (spec G45; UX Moment 9 and W11): the two-sided
#: exponential f(x) = p·λe^{λx} for x < 0 and (1−p)·λe^{−λx} for x ≥ 0, so
#: P(X ≤ 0) = p, unchanged by λ.
TWO_SIDED = "piecewise((x < 0, p*lam*exp(lam*x)), (1 - p)*lam*exp(-lam*x))"
#: UX W11's first draft: an extra ½ in each component (total mass ½). The
#: negative control `integrates_to_one` rejects.
TWO_SIDED_HALF = "piecewise((x < 0, p*lam*exp(lam*x)/2), (1 - p)*lam*exp(-lam*x)/2)"


def flagship_spec(density: str = TWO_SIDED) -> dict[str, Any]:
    return {
        "spec_version": "ifs-v1",
        "kind": "reconstructed",
        "source_claims": [{"span_id": "s2", "quote": "f_X(x) = p\\lambda e^{\\lambda x} for x < 0"}],
        "demonstrates": "P(X ≤ 0) is p however λ changes: λ squeezes both sides toward 0, p sets the split.",
        "assumptions": [{"text": "λ > 0 and 0 < p < 1"}],
        "parameters": [
            {"name": "p", "label": "p", "min": 0.05, "max": 0.95, "step": 0.05, "default": 0.3},
            {"name": "lam", "label": "λ", "min": 0.5, "max": 4, "step": 0.1, "default": 1, "animate": True},
        ],
        "definitions": [{"name": "f", "expr": density}],
        "panels": [
            {"kind": "function_plot", "x": {"var": "x", "min": -40, "max": 40},
             "series": [{"expr": "f", "label": "density"}],
             "markers": [{"x": "0", "label": "0"}],
             "shade": [{"series": "density", "from": "-40", "to": "0", "label": "P(X ≤ 0)"},
                       {"series": "density", "from": "0", "to": "40", "label": "P(X > 0)"}]},
            {"kind": "readout", "label": "P(X ≤ 0)", "expr": "integral(f, x, -40, 0)", "format": "percent"},
        ],
        "invariants": [
            {"kind": "nonnegative", "expr": "f", "var": "x", "from": -40, "to": 40},
            {"kind": "integrates_to_one", "expr": "f", "var": "x", "from": -40, "to": 40},
            {"kind": "equals_source", "name": "f"},
        ],
        "predictions": [
            {"prompt": "If λ doubles, what happens to P(X ≤ 0)?", "change": {"lam": 2},
             "observe": {"kind": "direction", "expr": "integral(f, x, -40, 0)"}},
            {"prompt": "Which shaded area is P(X < 0)?", "change": {},
             "observe": {"kind": "area", "expr": "p"}},
        ],
        "annotations": [{"target": "density", "text": "the jump at 0 is p·λ on the left, (1−p)·λ on the right"}],
    }


def binomial_spec() -> dict[str, Any]:
    return {
        "spec_version": "ifs-v1", "kind": "illustrative",
        "demonstrates": "A binomial PMF sums to one; the highlighted bars are P(K ≤ m).",
        "parameters": [
            {"name": "n", "label": "n", "min": 1, "max": 30, "step": 1, "default": 10},
            {"name": "q", "label": "q", "min": 0.05, "max": 0.95, "step": 0.05, "default": 0.4, "animate": True},
            {"name": "m", "label": "m", "min": 0, "max": 30, "step": 1, "default": 3},
        ],
        "definitions": [
            {"name": "lfact", "expr": "sum(log(j), j, 1, k)"},
            {"name": "choose", "expr": "exp(sum(log(j), j, 1, n) - sum(log(j), j, 1, k) - sum(log(j), j, 1, n - k))"},
            {"name": "pmf", "expr": "piecewise((k <= n, choose*q^k*(1 - q)^(n - k)), 0)"},
        ],
        "panels": [
            {"kind": "pmf_bars", "k": {"var": "k", "min": 0, "max": 30},
             "series": [{"expr": "pmf", "label": "P(K = k)"}],
             "highlight": {"from": "0", "to": "m", "label": "P(K ≤ m)"}},
            {"kind": "readout", "label": "P(K ≤ m)",
             "expr": "sum(exp(sum(log(j), j, 1, n) - sum(log(j), j, 1, k) - sum(log(j), j, 1, n - k))*q^k*(1-q)^(n-k), k, 0, m)"},
        ],
        "invariants": [{"kind": "sums_to_one", "expr": "pmf", "var": "k", "from": 0, "to": 30}],
    }


def binomial_spec_flat() -> dict[str, Any]:
    """The binomial without nested sums (a definition's sum used inside a sum
    is refused: no sum inside a sum): the PMF written with Γ-free factorials
    over a bounded k, by a product of ratios kept to a single sum."""

    spec = binomial_spec()
    spec["definitions"] = [
        {"name": "pmf", "expr": "piecewise((k <= n, exp(lg_n - lg_k - lg_nk)*q^k*(1 - q)^(n - k)), 0)"},
    ]
    return spec


def pmf_spec() -> dict[str, Any]:
    """A geometric PMF on 1..40 with a highlighted range and a sum readout."""

    return {
        "spec_version": "ifs-v1", "kind": "illustrative",
        "demonstrates": "The geometric PMF (1−q)^(k−1)·q sums to one; the highlight is P(K ≤ m).",
        "parameters": [
            {"name": "q", "label": "q", "min": 0.2, "max": 0.9, "step": 0.05, "default": 0.5, "animate": True},
            {"name": "m", "label": "m", "min": 1, "max": 10, "step": 1, "default": 3},
        ],
        "definitions": [{"name": "pmf", "expr": "(1 - q)^(k - 1)*q"}],
        "panels": [
            {"kind": "pmf_bars", "k": {"var": "k", "min": 1, "max": 120},
             "series": [{"expr": "pmf", "label": "P(K = k)"}],
             "highlight": {"from": "1", "to": "m", "label": "P(K ≤ m)"}},
            {"kind": "readout", "label": "P(K ≤ m)", "expr": "sum(pmf, k, 1, m)", "format": "percent"},
            {"kind": "readout", "label": "total", "expr": "sum(pmf, k, 1, 120)"},
        ],
        "invariants": [{"kind": "sums_to_one", "expr": "pmf", "var": "k", "from": 1, "to": 120}],
    }


def linear_map_spec() -> dict[str, Any]:
    return {
        "spec_version": "ifs-v1", "kind": "illustrative",
        "demonstrates": "A rotation by θ scaled by s maps the unit square to a square of area s².",
        "parameters": [
            {"name": "theta", "label": "θ", "min": 0, "max": 6.283185307179586, "step": 0.01, "default": 0.5,
             "animate": True},
            {"name": "s", "label": "s", "min": 0.1, "max": 3, "step": 0.1, "default": 1.5},
        ],
        "panels": [
            {"kind": "linear_map_2d", "matrix": [["s*cos(theta)", "-s*sin(theta)"], ["s*sin(theta)", "s*cos(theta)"]],
             "label": "s·R(θ)"},
            {"kind": "readout", "label": "area of the image", "expr": "s^2"},
        ],
        "invariants": [{"kind": "finite", "expr": "s*cos(theta)"}],
    }


def normal_cdf_spec() -> dict[str, Any]:
    """A density and its CDF (an integral with a variable upper bound that
    shadows the panel's variable), checked against Phi."""

    return {
        "spec_version": "ifs-v1", "kind": "illustrative",
        "demonstrates": "The normal CDF is the area under the density to the left of x.",
        "parameters": [
            {"name": "mu", "label": "μ", "min": -2, "max": 2, "step": 0.1, "default": 0},
            {"name": "sigma", "label": "σ", "min": 0.5, "max": 3, "step": 0.1, "default": 1, "animate": True},
        ],
        "definitions": [{"name": "g", "expr": "exp(-((x - mu)/sigma)^2/2)/(sigma*sqrt(2*pi))"}],
        "panels": [
            {"kind": "function_plot", "x": {"var": "x", "min": -8, "max": 8},
             "series": [{"expr": "g", "label": "density"},
                        {"expr": "integral(g, x, -30, x)", "label": "CDF"},
                        {"expr": "Phi((x - mu)/sigma)", "label": "Phi"}],
             "shade": [{"series": "density", "from": "mu - sigma", "to": "mu + sigma", "label": "within one σ"}]},
            {"kind": "readout", "label": "P(|X − μ| < σ)", "expr": "Phi(1) - Phi(-1)", "format": "percent"},
        ],
        "invariants": [
            {"kind": "integrates_to_one", "expr": "g", "var": "x", "from": -30, "to": 30},
            {"kind": "monotone_nondecreasing", "expr": "Phi((x - mu)/sigma)", "var": "x", "from": -8, "to": 8},
        ],
    }


def _expressions() -> list[dict[str, Any]]:
    env = {"x": 0.7, "p": 0.3, "lam": 1.5, "n": 10.0, "a": -2.0, "b": 3.0}
    defs_flag = [{"name": "f", "expr": TWO_SIDED}]
    cases: list[dict[str, Any]] = []

    def add(case_id: str, expr: str, *, reference: float | None = None, definitions: list | None = None,
            integral: bool = False, scope: dict[str, float] | None = None) -> None:
        cases.append({"id": case_id, "expr": expr, "env": scope or env, "definitions": definitions or [],
                      "integral": integral, "reference": reference})

    add("number_int", "2", reference=2.0)
    add("number_decimal", "0.5", reference=0.5)
    add("number_leading_dot", ".25", reference=0.25)
    add("number_trailing_dot", "3.", reference=3.0)
    add("number_exponent", "1e-3", reference=1e-3)
    add("number_exponent_upper", "2.5E+2", reference=250.0)
    add("precedence", "1 + 2*3 - 4/2", reference=5.0)
    add("parentheses", "(1 + 2)*3", reference=9.0)
    add("power_right_assoc", "2^3^2", reference=512.0)
    add("unary_minus_power", "-2^2", reference=-4.0)
    add("power_negative_exponent", "2^-2", reference=0.25)
    add("double_negative", "--x", reference=0.7)
    add("names", "p*lam + x", reference=0.3 * 1.5 + 0.7)
    add("constants", "pi + e", reference=math.pi + math.e)
    add("exp", "exp(x)", reference=math.exp(0.7))
    add("log", "log(x)", reference=math.log(0.7))
    add("sqrt", "sqrt(b)", reference=math.sqrt(3.0))
    add("abs", "abs(a)", reference=2.0)
    add("sin", "sin(x)", reference=math.sin(0.7))
    add("cos", "cos(x)", reference=math.cos(0.7))
    add("tan", "tan(x)", reference=math.tan(0.7))
    add("atan", "atan(b)", reference=math.atan(3.0))
    add("erf", "erf(x)", reference=math.erf(0.7))
    add("erf_large", "erf(4.2)", reference=math.erf(4.2))
    add("erf_negative", "erf(-1)", reference=math.erf(-1.0))
    add("erf_mid", "erf(1.1)", reference=math.erf(1.1))
    add("Phi", "Phi(x)", reference=0.5 * math.erfc(-0.7 / math.sqrt(2)))
    add("Phi_left_tail", "Phi(-9)", reference=0.5 * math.erfc(9 / math.sqrt(2)))
    add("Phi_right", "Phi(2.5)", reference=0.5 * math.erfc(-2.5 / math.sqrt(2)))
    add("floor", "floor(-x)", reference=-1.0)
    add("min", "min(a, b, x)", reference=-2.0)
    add("max", "max(a, b, x)", reference=3.0)
    add("piecewise_first", "piecewise((x < 1, 10), 20)", reference=10.0)
    add("piecewise_else", "piecewise((x > 1, 10), 20)", reference=20.0)
    add("piecewise_many", "piecewise((x < 0, 1), (x < 0.5, 2), (x <= 0.7, 3), 4)", reference=3.0)
    add("piecewise_and", "piecewise((x > 0 and x < 1, 1), 0)", reference=1.0)
    add("piecewise_or", "piecewise((x < 0 or b == 3, 1), 0)", reference=1.0)
    add("piecewise_and_or", "piecewise((x > 5 and b > 1 or a < 0, 1), 0)", reference=1.0)
    add("piecewise_ne_ge", "piecewise((a != b and b >= 3, 7), 0)", reference=7.0)
    add("piecewise_paren_condition", "piecewise(((x + 1) < 2, 5), 6)", reference=5.0)
    add("piecewise_paren_else", "piecewise((x < 0, 5), (x + 1)*2)", reference=3.4)
    add("division_by_zero", "1/(x - x)", reference=math.inf)
    add("negative_division_by_zero", "-1/(x - x)", reference=-math.inf)
    add("zero_over_zero", "(x - x)/(x - x)", reference=math.nan)
    add("log_zero", "log(0)", reference=-math.inf)
    add("log_negative", "log(a)", reference=math.nan)
    add("sqrt_negative", "sqrt(a)", reference=math.nan)
    add("pow_negative_fraction", "a^0.5", reference=math.nan)
    add("pow_zero_negative", "0^-1", reference=math.inf)
    add("pow_nan_zero", "(0/0)^0", reference=1.0)
    add("pow_one_nan", "1^(0/0)", reference=math.nan)
    add("exp_overflow", "exp(1000)", reference=math.inf)
    add("nan_min", "min(0/0, 1)", reference=math.nan)
    add("nan_comparison", "piecewise((0/0 < 1, 1), (0/0 != 1, 2), 3)", reference=2.0)
    add("unbound_name", "zzz + 1", reference=math.nan)
    add("sum_exact", "sum(k^2, k, 1, n)", reference=385.0)
    add("sum_fractional_bounds", "sum(k, k, 0.5, 3.5)", reference=6.0)
    add("sum_empty", "sum(k, k, 3, 1)", reference=0.0)
    add("sum_geometric", "sum(0.5^k, k, 0, 60)", reference=2.0 - 0.5 ** 60)
    add("integral_polynomial", "integral(t^2, t, 0, 3)", reference=9.0, integral=True)
    add("integral_reversed", "integral(t, t, 1, 0)", reference=-0.5, integral=True)
    add("integral_param_bounds", "integral(exp(-t), t, 0, b)", reference=1 - math.exp(-3.0), integral=True)
    add("integral_gaussian", "integral(exp(-t^2/2)/sqrt(2*pi), t, -1, 1)",
        reference=math.erf(1 / math.sqrt(2)), integral=True)
    add("integral_shadowing", "integral(x, x, 0, x)", reference=0.245, integral=True)
    add("integral_jump_inside", "integral(piecewise((t < 0.3, 1), 2), t, 0, 1)", reference=1.7, integral=True)
    add("integral_empty", "integral(t, t, 2, 2)", reference=0.0, integral=True)
    add("two_sided_left", "integral(f, x, -40, 0)", definitions=defs_flag, integral=True,
        reference=0.3 * (1 - math.exp(-1.5 * 40)))
    add("two_sided_right", "integral(f, x, 0, 40)", definitions=defs_flag, integral=True,
        reference=0.7 * (1 - math.exp(-1.5 * 40)))
    add("two_sided_total", "integral(f, x, -40, 40)", definitions=defs_flag, integral=True,
        reference=1 - math.exp(-1.5 * 40))
    add("two_sided_half_total", "integral(f, x, -40, 40)",
        definitions=[{"name": "f", "expr": TWO_SIDED_HALF}], integral=True,
        reference=0.5 * (1 - math.exp(-1.5 * 40)))
    add("two_sided_density_left", "f", definitions=defs_flag, scope={**env, "x": -0.5},
        reference=0.3 * 1.5 * math.exp(-0.75))
    add("two_sided_density_right", "f", definitions=defs_flag,
        reference=0.7 * 1.5 * math.exp(-1.05))
    for p in (0.05, 0.3, 0.95):
        for lam in (0.5, 1.0, 4.0):
            add(f"two_sided_P_le_0_p{p}_lam{lam}", "integral(f, x, -40, 0)", definitions=defs_flag, integral=True,
                scope={"p": p, "lam": lam}, reference=p * (1 - math.exp(-lam * 40)))
    add("definition_chain", "h + 1", definitions=[{"name": "g", "expr": "x^2"}, {"name": "h", "expr": "2*g"}],
        reference=2 * 0.49 + 1)
    return cases


def _rejected() -> list[dict[str, Any]]:
    deep = "(" * 45 + "1" + ")" * 45
    many = "+".join(["1"] * 260)
    cases = [
        ("empty", ""), ("blank", "   "), ("dangling_operator", "1 +"), ("unclosed", "(1"), ("extra_close", "1)"),
        ("subscript", "x[0]"), ("attribute", "a.b"), ("dunder_call", "__import__('os')"), ("eval", "eval(1)"),
        ("lambda_word", "lambda"), ("semicolon", "1;2"), ("string", "'s'"), ("double_star", "x**2"),
        ("unary_plus", "+x"), ("bare_function", "exp"), ("no_args", "exp()"), ("min_one_arg", "min(1)"),
        ("too_many_args", "exp(1, 2)"), ("piecewise_no_branch", "piecewise(1)"),
        ("piecewise_no_else", "piecewise((x < 1, 2))"), ("comparison_outside", "1 < 2"),
        ("chained_comparison", "piecewise((0 < x < 1, 1), 0)"), ("condition_not_comparison", "piecewise((x and 1, 2), 3)"),
        ("integral_number_var", "integral(x, 1, 0, 1)"), ("integral_reserved_var", "integral(x, pi, 0, 1)"),
        ("integral_missing_bound", "integral(x, t, 0)"), ("sum_bare", "sum"), ("keyword_alone", "and"),
        ("unknown_function", "gamma(2)"), ("unicode_digit", "٣"), ("nbsp", "x + 1"), ("tab_ok_but_hash", "1 # 2"),
        ("backslash", "\\frac{1}{2}"), ("braces", "{1}"), ("dollar", "$x"), ("too_long", "1" + "+1" * 1000),
        ("too_deep", deep), ("too_many_nodes", many), ("long_name", "a" * 33), ("implicit_product", "2x"),
        ("double_number", "1 2"), ("comma_top", "1, 2"), ("caret_alone", "^2"), ("nan_literal", "nan"),
    ]
    rows = [{"id": case_id, "expr": expr, "stage": "parse", "known": [], "definitions": []} for case_id, expr in cases]
    # Words that are names parse; they are refused as unknown names.
    for row in rows:
        if row["id"] in ("lambda_word", "nan_literal"):
            row["stage"], row["known"] = "names", ["x"]
    rows += [
        {"id": "nested_integral", "expr": "integral(integral(t, t, 0, 1), s, 0, 1)", "stage": "names",
         "known": [], "definitions": []},
        {"id": "sum_in_integral", "expr": "integral(sum(k, k, 1, 3), t, 0, 1)", "stage": "names", "known": [],
         "definitions": []},
        {"id": "integral_in_bound", "expr": "integral(t, t, 0, integral(s, s, 0, 1))", "stage": "names", "known": [],
         "definitions": []},
        {"id": "nested_through_definition", "expr": "integral(F, x, 0, 1)", "stage": "names", "known": ["x"],
         "definitions": [{"name": "F", "expr": "integral(t, t, 0, x)"}]},
        {"id": "unknown_name", "expr": "x + y", "stage": "names", "known": ["x"], "definitions": []},
    ]
    return rows


def _rejected_figures() -> list[dict[str, Any]]:
    unknown = flagship_spec()
    unknown["panels"][0]["series"][0]["expr"] = "f + zeta"
    nested = flagship_spec()
    nested["definitions"].append({"name": "F", "expr": "integral(f, x, -40, x)"})
    nested["panels"][1]["expr"] = "integral(F, x, 0, 1)"
    reserved = flagship_spec()
    reserved["parameters"][1]["name"] = "exp"
    shade = flagship_spec()
    shade["panels"][0]["shade"][0]["series"] = "no such series"
    axis_in_readout = flagship_spec()
    axis_in_readout["panels"][1]["expr"] = "f"
    return [
        {"id": "unknown_name_in_series", "spec": unknown},
        {"id": "nested_integral_through_definition", "spec": nested},
        {"id": "reserved_parameter_name", "spec": reserved},
        {"id": "shade_names_no_series", "spec": shade},
        {"id": "readout_needs_the_axis", "spec": axis_in_readout},
        {"id": "binomial_nested_sums", "spec": binomial_spec()},
        {"id": "binomial_unknown_names", "spec": binomial_spec_flat()},
    ]


FUZZ_TOKENS = ("x", "p", "lam", "1", "2.5", "0", ".5", "1e3", "+", "-", "*", "/", "^", "(", ")", ",", "<", "<=",
               ">", "==", "!=", "and", "or", "exp", "log", "sqrt", "min", "max", "piecewise", "integral", "sum", "pi",
               "e", "Phi", "erf", "floor", "abs", "t", " ", "@", "[", "]", "'", ";", "import", "__", ".", "x2",
               "é", "\\")


def _fuzz(seed: int = 20261021, count: int = 600) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        length = rng.randint(1, 14)
        joiner = "" if rng.random() < 0.4 else " "
        rows.append({"id": f"fuzz_{index}", "expr": joiner.join(rng.choice(FUZZ_TOKENS) for _ in range(length))})
    # Seeds that are inside the grammar, so the agreement covers accepted text too.
    seeds = ["x + p*lam", "piecewise((x < p, 1), 2)", "integral(t*x, t, 0, 1)", "sum(k*p, k, 1, 3)",
             "min(x, p) ^ 2", "-exp(-x)/lam", "Phi(x) - erf(p)", "floor(x*10)/10", "abs(sqrt(p) - log(lam))"]
    rows += [{"id": f"fuzz_seed_{index}", "expr": expr} for index, expr in enumerate(seeds)]
    return rows


FUZZ_KNOWN = ("x", "p", "lam")
FUZZ_ENV = {"x": 0.7, "p": 0.3, "lam": 1.5}


def _finite_or_none(value: float) -> float | str | None:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


def build() -> dict[str, Any]:
    from learnloop.figures import grammar as G
    from learnloop.figures import spec as S

    expressions = []
    for case in _expressions():
        defs = {d["name"]: G.parse(d["expr"]) for d in case["definitions"]}
        value = G.evaluate(G.parse(case["expr"]), case["env"], defs)
        reference = case.pop("reference")
        expressions.append({**case, "expected": _finite_or_none(value),
                            "reference": None if reference is None else _finite_or_none(reference)})
    fuzz = []
    for case in _fuzz():
        try:
            node = G.parse(case["expr"])
            G.check_names(node, known=frozenset(FUZZ_KNOWN) | {"t", "k"}, definitions={})
            if not set(S.expanded_free(node, {})) <= set(FUZZ_KNOWN):
                raise G.GrammarError("unbound")
            fuzz.append({**case, "accepted": True, "expected": _finite_or_none(G.evaluate(node, FUZZ_ENV))})
        except G.GrammarError:
            fuzz.append({**case, "accepted": False, "expected": None})
    figures = []
    for case_id, spec, params in (
        ("two_sided_exponential", flagship_spec(), [{}, {"p": 0.6, "lam": 2.5}, {"p": 0.05, "lam": 4}]),
        ("two_sided_exponential_half_negative_control", flagship_spec(TWO_SIDED_HALF), [{}]),
        ("geometric_pmf", pmf_spec(), [{}, {"q": 0.8, "m": 7}]),
        ("linear_map", linear_map_spec(), [{}, {"theta": 2.0, "s": 0.5}]),
        ("normal_cdf", normal_cdf_spec(), [{}, {"mu": 1, "sigma": 2}]),
    ):
        compiled = S.parse_spec(spec)
        outputs = [S.evaluate_figure(compiled, values) for values in params]
        outcomes = [S.prediction_outcome(compiled, index) for index in range(len(compiled.predictions))]
        figures.append({"id": case_id, "spec": spec, "params": params, "expected": outputs,
                        "predictions": outcomes})
    return {
        "version": 1,
        "note": "Generated by tests/figure_corpus.py (uv run python -m tests.figure_corpus --write); "
                "read by tests/test_figure_grammar.py and figureGrammar.test.ts.",
        "tolerance": {"relative": RELATIVE, "integral": INTEGRAL},
        "expressions": expressions,
        "rejected": _rejected(),
        "figures": figures,
        "rejected_figures": _rejected_figures(),
        "fuzz": {"known": list(FUZZ_KNOWN), "bound": ["t", "k"], "env": FUZZ_ENV, "cases": fuzz},
    }


def render() -> str:
    return json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    if "--write" in sys.argv:
        CORPUS_PATH.write_text(render(), encoding="utf-8")
        print(f"wrote {CORPUS_PATH}")
    else:
        sys.stdout.write(render())
