"""Reader workbench RW2b: symbolic checks of declared step kinds (spec_reader_workbench_v1 §5.3, G9, G38).

The check writer declares, per step it can classify, ONE transformation kind
with stated inputs (sympy-syntax expressions as data). The checks themselves
are fixed code: :data:`HARNESS` below, never model-written, run in the PF-b
sandbox (``learnloop.content.authoring.pf_sandbox``: bubblewrap, no network,
rlimits, a wall-clock timeout), because parsing model text with sympy
evaluates it. Without bubblewrap the sandbox fails closed and every verdict
stays the model's reading.

Each check is trusted only when its **controls behave**: a negative control
(the claimed result perturbed) must be rejected, and, where sympy can compute
the true result, a positive control (that result) must be accepted. Then a
passing claim is *checked* (``✓``) and a failing one *doesn't follow* (``≠``).
Inequalities are sampled numerically and labelled "checked numerically".

Declared kinds (§5.3): ``equivalence``, ``differentiation``, ``integration``
(indefinite, or definite with stated bounds), ``substitution``, ``solving``,
``limit``, ``sum``, ``inequality``, ``boundary``, ``normalization``. Any other
kind is not attempted (the step stays the model's reading).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable

KINDS: tuple[str, ...] = (
    "equivalence", "differentiation", "integration", "substitution", "solving", "limit", "sum", "inequality",
    "boundary", "normalization",
)
#: How a verdict was reached (the label beside the marker, W2).
CHECKED, CHECKED_NUMERICALLY, MODEL = "checked", "checked_numerically", "model"
#: Bounds (prompt-size and runtime only, never judgments).
MAX_CHECKS = 12
MAX_EXPRESSION_CHARS = 400


@dataclass(frozen=True)
class SymbolicClaim:
    """One declared transformation of one step."""

    index: int
    kind: str
    expression: str
    result: str
    variable: str = ""
    value: str = ""
    lower: str = ""
    upper: str = ""
    relation: str = ""

    def payload(self) -> dict[str, Any]:
        return {"index": self.index, "kind": self.kind, "expression": self.expression[:MAX_EXPRESSION_CHARS],
                "result": self.result[:MAX_EXPRESSION_CHARS], "variable": self.variable[:40],
                "value": self.value[:MAX_EXPRESSION_CHARS], "lower": self.lower[:MAX_EXPRESSION_CHARS],
                "upper": self.upper[:MAX_EXPRESSION_CHARS], "relation": self.relation[:4]}


@dataclass(frozen=True)
class SymbolicOutcome:
    """What the sandbox found for one claim. ``method`` is ``checked``,
    ``checked_numerically`` or ``model`` (the controls misbehaved, the parse
    failed, the kind is not declared, or the sandbox did not run); ``holds``
    is the claim's truth only when ``method`` is not ``model``."""

    index: int
    method: str
    holds: bool | None
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "method": self.method, "holds": self.holds, "reason": self.reason}


# The harness: fixed code. Model text arrives as JSON data and is parsed by
# sympy inside the sandbox only.
HARNESS = r'''
import json, random, signal, sys
workdir = sys.argv[1]
MARKER = "@@PF-SANDBOX-RESULT@@"


class _Timeout(Exception):
    pass


def _alarm(_signum, _frame):
    raise _Timeout()


signal.signal(signal.SIGALRM, _alarm)


def bounded(seconds, function, *args):
    signal.alarm(seconds)
    try:
        return function(*args)
    finally:
        signal.alarm(0)


import sympy
from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application, parse_expr,
                                        standard_transformations)

TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


def parse(text):
    text = str(text or "").strip().replace("$", "")
    if not text:
        raise ValueError("empty expression")
    return parse_expr(text, transformations=TRANSFORMS, evaluate=True)


def equation(text):
    text = str(text or "")
    if "=" in text and "==" not in text and "<" not in text and ">" not in text:
        left, right = text.split("=", 1)
        return parse(left) - parse(right)
    return parse(text)


def zero(value):
    """Identically zero: simplify, else (with free symbols) zero at sampled
    points, else numerically zero."""
    simplified = sympy.simplify(value)
    if simplified == 0:
        return True
    free = sorted(simplified.free_symbols, key=lambda s: s.name)
    if not free:
        return abs(complex(sympy.N(simplified))) < 1e-9
    rng = random.Random(11)
    checked = 0
    for _ in range(12):
        point = {s: rng.uniform(0.3, 2.7) for s in free}
        try:
            number = complex(sympy.N(simplified.subs(point)))
        except (TypeError, ValueError):
            continue
        if number != number:
            continue
        checked += 1
        if abs(number) > 1e-7:
            return False
    return checked >= 3


def symbol(claim, expression):
    name = str(claim.get("variable") or "").strip()
    if name:
        return sympy.Symbol(name)
    free = sorted(expression.free_symbols, key=lambda s: s.name)
    if len(free) != 1:
        raise ValueError("the variable is not stated")
    return free[0]


def truth(claim):
    """The true result where sympy computes one (the positive control), or None."""
    kind = claim["kind"]
    expression = parse(claim["expression"]) if kind not in ("solving",) else equation(claim["expression"])
    if kind == "equivalence":
        return expression
    variable = symbol(claim, expression)
    if kind == "differentiation":
        return sympy.diff(expression, variable)
    if kind == "integration":
        if str(claim.get("lower") or "").strip() and str(claim.get("upper") or "").strip():
            return sympy.integrate(expression, (variable, parse(claim["lower"]), parse(claim["upper"])))
        return sympy.integrate(expression, variable)
    if kind in ("substitution", "boundary"):
        return expression.subs(variable, parse(claim["value"]))
    if kind == "limit":
        return sympy.limit(expression, variable, parse(claim["value"]))
    if kind == "sum":
        return sympy.summation(expression, (variable, parse(claim["lower"]), parse(claim["upper"])))
    if kind == "solving":
        roots = sympy.solve(expression, variable)
        return roots[0] if roots else None
    return None


def holds(claim, result_text):
    """Whether the step's claim holds with ``result_text`` as its result."""
    kind = claim["kind"]
    if kind == "normalization":
        expression = parse(claim["expression"])
        variable = symbol(claim, expression)
        total = sympy.integrate(expression, (variable, parse(claim["lower"]), parse(claim["upper"])))
        return zero(total - parse(result_text or "1"))
    if kind == "solving":
        expression = equation(claim["expression"])
        variable = symbol(claim, expression)
        return zero(expression.subs(variable, parse(result_text)))
    expression = parse(claim["expression"])
    result = parse(result_text)
    if kind == "equivalence":
        return zero(expression - result)
    variable = symbol(claim, expression)
    if kind == "differentiation":
        return zero(sympy.diff(expression, variable) - result)
    if kind == "integration":
        if str(claim.get("lower") or "").strip() and str(claim.get("upper") or "").strip():
            value = sympy.integrate(expression, (variable, parse(claim["lower"]), parse(claim["upper"])))
            return zero(value - result)
        # An antiderivative, up to a constant.
        return zero(sympy.diff(result, variable) - expression)
    if kind in ("substitution", "boundary"):
        return zero(expression.subs(variable, parse(claim["value"])) - result)
    if kind == "limit":
        return zero(sympy.limit(expression, variable, parse(claim["value"])) - result)
    if kind == "sum":
        return zero(sympy.summation(expression, (variable, parse(claim["lower"]), parse(claim["upper"]))) - result)
    raise ValueError("not a declared kind")


RELATIONS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
             ">=": lambda a, b: a >= b}


def inequality(claim, relation):
    """Whether the relation holds at every sampled point, and how many points
    could be evaluated (real values only)."""
    left = parse(claim["expression"])
    right = parse(claim["result"])
    compare = RELATIONS[relation]
    free = sorted((left - right).free_symbols, key=lambda s: s.name)
    lower = float(sympy.N(parse(claim["lower"]))) if str(claim.get("lower") or "").strip() else -10.0
    upper = float(sympy.N(parse(claim["upper"]))) if str(claim.get("upper") or "").strip() else 10.0
    rng = random.Random(7)
    points = 0
    every = True
    for _ in range(200):
        values = {s: rng.uniform(lower, upper) for s in free}
        a = complex(sympy.N(left.subs(values)))
        b = complex(sympy.N(right.subs(values)))
        if abs(a.imag) > 1e-9 or abs(b.imag) > 1e-9:
            continue
        points += 1
        if not compare(a.real, b.real):
            every = False
    return every, points


def perturbed(claim, text):
    """A wrong result the check must reject: one more, and for an
    antiderivative (equal up to a constant) one more times the variable."""
    out = "(" + str(text or "0") + ") + 1"
    indefinite = claim["kind"] == "integration" and not (
        str(claim.get("lower") or "").strip() and str(claim.get("upper") or "").strip())
    if indefinite:
        expression = parse(claim["expression"])
        out += " + " + symbol(claim, expression).name
    return out


def run(claim):
    kind = claim["kind"]
    if kind == "inequality":
        relation = str(claim.get("relation") or "").strip()
        if relation not in RELATIONS:
            return {"method": "model", "holds": None, "reason": "no relation stated"}
        claimed, points = inequality(claim, relation)
        flipped = {"<": ">=", "<=": ">", ">": "<=", ">=": "<"}[relation]
        control, _ = inequality(claim, flipped)
        if points < 20 or (claimed and control):
            return {"method": "model", "holds": None, "reason": "the samples could not tell"}
        return {"method": "checked_numerically", "holds": bool(claimed), "reason": "sampled %d points" % points}
    if kind == "normalization":
        claimed = holds(claim, "1")
        control = holds(claim, "2")
        if control:
            return {"method": "model", "holds": None, "reason": "the negative control was accepted"}
        return {"method": "checked", "holds": bool(claimed), "reason": "the density's integral over the support"}
    true = truth(claim)
    if true is not None:
        # The controls are taken around the TRUE result (sympy's): it must be
        # accepted, and a perturbed one rejected; only then does the claim's
        # verdict mean anything.
        if not holds(claim, str(true)):
            return {"method": "model", "holds": None, "reason": "the positive control was rejected"}
        if holds(claim, perturbed(claim, str(true))):
            return {"method": "model", "holds": None, "reason": "the negative control was accepted"}
    elif holds(claim, perturbed(claim, claim["result"])):
        return {"method": "model", "holds": None, "reason": "the negative control was accepted"}
    return {"method": "checked", "holds": bool(holds(claim, claim["result"])), "reason": ""}


with open(workdir + "/input.json", encoding="utf-8") as handle:
    payload = json.load(handle)
results = []
for claim in payload["claims"]:
    entry = {"index": claim["index"]}
    try:
        entry.update(bounded(payload.get("per_check_seconds", 5), run, claim))
    except BaseException as exc:
        entry.update({"method": "model", "holds": None, "reason": type(exc).__name__})
    results.append(entry)
sys.stdout.write(MARKER + json.dumps({"results": results}, sort_keys=True, default=str))
sys.stdout.flush()
'''


def sandbox_ready() -> bool:
    from learnloop.content.authoring.pf_sandbox import sandbox_available

    return sandbox_available()


def run_checks(claims: Sequence[SymbolicClaim], *, limits: Any = None,
               run: Callable[..., Any] | None = None) -> tuple[list[SymbolicOutcome], str | None]:
    """Run the declared claims in the sandbox; ``(outcomes, problem)``.
    ``problem`` names why nothing ran (``sandbox_unavailable``,
    ``sandbox_failed``); every outcome is then the model's reading."""

    from learnloop.content.authoring.pf_sandbox import SandboxLimits, SandboxUnavailable, run_sandboxed_python

    declared = [claim for claim in claims if claim.kind in KINDS][:MAX_CHECKS]
    if not declared:
        return [], None
    fallback = [SymbolicOutcome(claim.index, MODEL, None, "not checked") for claim in declared]
    kwargs: dict[str, Any] = {"limits": limits or SandboxLimits(cpu_seconds=20, wall_seconds=30)}
    if run is not None:
        kwargs["run"] = run
    try:
        result = run_sandboxed_python(HARNESS, {"claims": [claim.payload() for claim in declared],
                                                "per_check_seconds": 5}, **kwargs)
    except SandboxUnavailable:
        return fallback, "sandbox_unavailable"
    if not result.ok or not isinstance(result.output, Mapping):
        return fallback, "sandbox_failed"
    found: dict[int, SymbolicOutcome] = {}
    for entry in result.output.get("results") or ():
        try:
            index = int(entry.get("index"))
        except (TypeError, ValueError):
            continue
        method = str(entry.get("method") or MODEL)
        if method not in (CHECKED, CHECKED_NUMERICALLY):
            method = MODEL
        value = entry.get("holds")
        found[index] = SymbolicOutcome(index, method, bool(value) if method != MODEL and isinstance(value, bool)
                                       else None, str(entry.get("reason") or "")[:200])
    return [found.get(claim.index, SymbolicOutcome(claim.index, MODEL, None, "no result")) for claim in declared], None


__all__ = [
    "CHECKED",
    "CHECKED_NUMERICALLY",
    "HARNESS",
    "KINDS",
    "MODEL",
    "SymbolicClaim",
    "SymbolicOutcome",
    "run_checks",
    "sandbox_ready",
]
