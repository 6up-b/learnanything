"""The figure grammar: a hand-written parser and evaluator (spec_reader_workbench_v1 §8.2, G21, G22).

**No generated code runs.** An expression is parsed by the recursive-descent
parser below into a small tree of :class:`Node` values and evaluated by
walking it; nothing reaches ``eval``, ``exec`` or ``compile``. The grammar:

* numbers (``2``, ``0.5``, ``1e-3``); names (parameters, definitions, the
  panel's variable, a bound integration or summation variable);
* ``+ - * / ^`` (``^`` binds tightest and is right-associative) and unary
  minus; parentheses;
* the functions ``exp log sqrt abs sin cos tan atan erf Phi min max floor``
  (``Phi`` is the standard normal CDF; ``min`` and ``max`` take two or more
  arguments);
* ``piecewise((cond, expr), ..., else)``: the first branch whose condition
  holds, else the last argument; a condition is comparisons
  (``< <= > >= == !=``) joined by ``and`` / ``or`` (``and`` binds tighter);
* the constants ``pi`` and ``e``;
* ``integral(expr, var, a, b)``: one fixed adaptive Simpson rule
  (:func:`adaptive_simpson`, the same depth and tolerance as the TypeScript
  twin) and ``sum(expr, k, a, b)``: exact, term by term over the integers
  ``ceil(a) .. floor(b)``. Bounds are expressions evaluated outside the body;
  the body binds ``var`` (which may shadow the panel's variable, so a CDF is
  ``integral(f, x, -40, x)``).

**Caps** (:data:`MAX_EXPR_CHARS`, :data:`MAX_NODES`, :data:`MAX_DEPTH`): on
length, node count and nesting; no integral or sum inside an integral or sum,
counted after definitions are expanded (:func:`check_names`); at most
:data:`MAX_SUM_TERMS` terms in a sum, whose bounds are integers within
:data:`MAX_SAFE_INTEGER` (a literal past it is refused when parsed, a
computed one sums to NaN); an integral evaluates its body at most
:data:`MAX_INTEGRAND_EVALS` times.

**Arithmetic follows IEEE doubles as JavaScript does** (``1/0`` is
``Infinity``, ``log(0)`` is ``-Infinity``, ``sqrt(-1)`` is ``NaN``), so the
two evaluators agree on every value, finite or not (G22). A value that is not
finite is a value, not an error: the verifier's structural step refuses a
figure whose values are not finite on its parameter grid.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

MAX_EXPR_CHARS = 2_000
MAX_NODES = 400
MAX_DEPTH = 40
#: A definition's body as expanded wherever it is used: a bound on the work
#: one evaluation can do (definitions name only earlier definitions).
MAX_EXPANDED_NODES = 4_000
MAX_NAME_CHARS = 32
MAX_SUM_TERMS = 10_001
#: A sum's bounds and a PMF's support are integers JavaScript counts exactly
#: (Number.MAX_SAFE_INTEGER, as in figureGrammar.ts): past it k + 1 == k in a
#: double, so a loop over them would never end (fix round 2).
MAX_SAFE_INTEGER = 2 ** 53 - 1
#: The adaptive Simpson rule (identical in figureGrammar.ts): the tolerance
#: halves per level; a panel stops at MAX_LEVEL, never before MIN_LEVEL.
SIMPSON_EPS = 1e-10
SIMPSON_MIN_LEVEL = 3
SIMPSON_MAX_LEVEL = 24
#: How far inside its interval each Simpson step reads its endpoints (2**-40 of its width).
SIMPSON_NUDGE = 2.0 ** -40
MAX_INTEGRAND_EVALS = 200_000

FUNCTIONS: dict[str, tuple[int, int | None]] = {
    "exp": (1, 1), "log": (1, 1), "sqrt": (1, 1), "abs": (1, 1), "sin": (1, 1), "cos": (1, 1),
    "tan": (1, 1), "atan": (1, 1), "erf": (1, 1), "Phi": (1, 1), "floor": (1, 1),
    "min": (2, 8), "max": (2, 8),
}
SPECIAL_FORMS = ("piecewise", "integral", "sum")
CONSTANTS = {"pi": math.pi, "e": math.e}
KEYWORDS = ("and", "or")
#: Object.prototype's own names a name may not be, so a name means the same in
#: both evaluators (a JavaScript object would find these on its prototype; fix
#: round 3). Names are letters and digits, starting with a letter: no
#: underscore, so no __proto__ either.
PROTOTYPE_NAMES = frozenset({"constructor", "hasOwnProperty", "isPrototypeOf", "propertyIsEnumerable",
                             "toLocaleString", "toString", "valueOf"})
#: Names nobody may define or bind.
RESERVED = frozenset({*FUNCTIONS, *SPECIAL_FORMS, *CONSTANTS, *KEYWORDS, *PROTOTYPE_NAMES})
COMPARISONS = ("<=", ">=", "==", "!=", "<", ">")

#: ASCII only (digits, letters, the four whitespace characters), as in
#: figureGrammar.ts: a Unicode digit or space is outside the grammar.
_TOKEN = re.compile(
    r"[ \t\r\n]*(?:"
    r"(?P<number>(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)"
    r"|(?P<name>[A-Za-z][A-Za-z0-9]*)"
    r"|(?P<op><=|>=|==|!=|[-+*/^(),<>])"
    r")"
)
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
_BLANK = re.compile(r"[ \t\r\n]*")


class GrammarError(ValueError):
    """An expression outside the grammar or its caps (never evaluated)."""


@dataclass(frozen=True)
class Node:
    """One parsed node. ``kind`` is ``num`` (``value``, ``text``), ``name``
    (``text``), ``neg`` (``args[0]``), ``bin`` (``op``, ``args[0..1]``),
    ``call`` (``text`` the function, ``args``), ``piecewise`` (``args``:
    cond, expr, cond, expr, ..., else), ``integral`` / ``sum`` (``text`` the
    bound variable, ``args``: body, lower, upper), ``cmp`` (``op``,
    ``args[0..1]``), ``and`` / ``or`` (``args``)."""

    kind: str
    text: str = ""
    op: str = ""
    value: float = 0.0
    args: tuple["Node", ...] = field(default_factory=tuple)


def is_name(text: str) -> bool:
    return bool(_NAME.match(text or "")) and len(text) <= MAX_NAME_CHARS and text not in PROTOTYPE_NAMES


def _tokenize(source: str) -> list[tuple[str, str]]:
    if not isinstance(source, str):
        raise GrammarError("an expression must be text")
    if len(source) > MAX_EXPR_CHARS:
        raise GrammarError(f"expression longer than {MAX_EXPR_CHARS} characters")
    tokens: list[tuple[str, str]] = []
    position = 0
    while position < len(source):
        if _BLANK.fullmatch(source, position):
            break
        match = _TOKEN.match(source, position)
        if match is None or match.end() == position:
            raise GrammarError(f"unexpected character {source[position:].lstrip()[:1]!r}")
        kind = match.lastgroup or ""
        text = match.group(kind)
        if kind == "name" and len(text) > MAX_NAME_CHARS:
            raise GrammarError(f"name longer than {MAX_NAME_CHARS} characters")
        if kind == "name" and text in PROTOTYPE_NAMES:
            raise GrammarError(f"{text!r} is a reserved name")
        tokens.append((kind, text))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, source: str) -> None:
        self.tokens = _tokenize(source)
        self.position = 0
        self.nodes = 0

    # -- helpers ------------------------------------------------------------------
    def _peek(self, offset: int = 0) -> tuple[str, str] | None:
        index = self.position + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def _take(self) -> tuple[str, str]:
        token = self._peek()
        if token is None:
            raise GrammarError("unexpected end of expression")
        self.position += 1
        return token

    def _expect(self, text: str) -> None:
        token = self._take()
        if token[1] != text or token[0] == "name":
            raise GrammarError(f"expected {text!r}, found {token[1]!r}")

    def _at(self, text: str) -> bool:
        token = self._peek()
        return token is not None and token[0] == "op" and token[1] == text

    def _node(self, kind: str, depth: int, **values: Any) -> Node:
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise GrammarError(f"expression has more than {MAX_NODES} nodes")
        if depth > MAX_DEPTH:
            raise GrammarError(f"expression nested deeper than {MAX_DEPTH}")
        return Node(kind, **values)

    # -- grammar ------------------------------------------------------------------
    def parse(self) -> Node:
        if not self.tokens:
            raise GrammarError("empty expression")
        node = self.expression(0)
        if self.position != len(self.tokens):
            raise GrammarError(f"unexpected {self.tokens[self.position][1]!r}")
        return node

    def expression(self, depth: int) -> Node:
        if depth > MAX_DEPTH:
            raise GrammarError(f"expression nested deeper than {MAX_DEPTH}")
        node = self.term(depth + 1)
        while self._at("+") or self._at("-"):
            op = self._take()[1]
            node = self._node("bin", depth, op=op, args=(node, self.term(depth + 1)))
        return node

    def term(self, depth: int) -> Node:
        node = self.unary(depth + 1)
        while self._at("*") or self._at("/"):
            op = self._take()[1]
            node = self._node("bin", depth, op=op, args=(node, self.unary(depth + 1)))
        return node

    def unary(self, depth: int) -> Node:
        if depth > MAX_DEPTH:
            raise GrammarError(f"expression nested deeper than {MAX_DEPTH}")
        if self._at("-"):
            self._take()
            return self._node("neg", depth, args=(self.unary(depth + 1),))
        return self.power(depth + 1)

    def power(self, depth: int) -> Node:
        base = self.primary(depth + 1)
        if self._at("^"):
            self._take()
            return self._node("bin", depth, op="^", args=(base, self.unary(depth + 1)))
        return base

    def primary(self, depth: int) -> Node:
        if depth > MAX_DEPTH:
            raise GrammarError(f"expression nested deeper than {MAX_DEPTH}")
        kind, text = self._take()
        if kind == "number":
            value = float(text)
            if not math.isfinite(value):
                raise GrammarError(f"number {text!r} is not finite")
            return self._node("num", depth, text=text, value=value)
        if kind == "op":
            if text == "(":
                node = self.expression(depth + 1)
                self._expect(")")
                return node
            raise GrammarError(f"unexpected {text!r}")
        # A name: a constant, a variable, a function call or a special form.
        if text in KEYWORDS:
            raise GrammarError(f"{text!r} belongs only in a piecewise condition")
        if self._at("("):
            if text in FUNCTIONS:
                return self.call(text, depth)
            if text == "piecewise":
                return self.piecewise(depth)
            if text in ("integral", "sum"):
                return self.bound_form(text, depth)
            raise GrammarError(f"unknown function {text!r}")
        if text in FUNCTIONS or text in SPECIAL_FORMS:
            raise GrammarError(f"{text!r} must be called")
        return self._node("name", depth, text=text)

    def call(self, name: str, depth: int) -> Node:
        self._expect("(")
        args = [self.expression(depth + 1)]
        while self._at(","):
            self._take()
            args.append(self.expression(depth + 1))
        self._expect(")")
        low, high = FUNCTIONS[name]
        if len(args) < low or (high is not None and len(args) > high):
            raise GrammarError(f"{name} takes {low if low == high else f'{low} or more'} argument(s)")
        return self._node("call", depth, text=name, args=tuple(args))

    def piecewise(self, depth: int) -> Node:
        self._expect("(")
        args: list[Node] = []
        while self._at("(") and self._is_branch():
            self._take()
            args.append(self.condition(depth + 1))
            self._expect(",")
            args.append(self.expression(depth + 1))
            self._expect(")")
            self._expect(",")
        if not args:
            raise GrammarError("piecewise needs at least one (condition, value) branch")
        args.append(self.expression(depth + 1))
        self._expect(")")
        return self._node("piecewise", depth, args=tuple(args))

    def _is_branch(self) -> bool:
        """Whether the parenthesis at the cursor opens a (condition, value)
        branch: a comparison before its first top-level comma."""

        level = 0
        index = self.position
        while index < len(self.tokens):
            kind, text = self.tokens[index]
            if kind == "op" and text == "(":
                level += 1
            elif kind == "op" and text == ")":
                level -= 1
                if level == 0:
                    return False
            elif level == 1 and kind == "op" and text == ",":
                return False
            elif level == 1 and ((kind == "op" and text in COMPARISONS) or (kind == "name" and text in KEYWORDS)):
                return True
            index += 1
        return False

    def condition(self, depth: int) -> Node:
        parts = [self.conjunction(depth + 1)]
        while self._peek() == ("name", "or"):
            self._take()
            parts.append(self.conjunction(depth + 1))
        return parts[0] if len(parts) == 1 else self._node("or", depth, args=tuple(parts))

    def conjunction(self, depth: int) -> Node:
        parts = [self.comparison(depth + 1)]
        while self._peek() == ("name", "and"):
            self._take()
            parts.append(self.comparison(depth + 1))
        return parts[0] if len(parts) == 1 else self._node("and", depth, args=tuple(parts))

    def comparison(self, depth: int) -> Node:
        left = self.expression(depth + 1)
        token = self._peek()
        if token is None or token[0] != "op" or token[1] not in COMPARISONS:
            raise GrammarError("a piecewise condition must be a comparison")
        self._take()
        right = self.expression(depth + 1)
        follow = self._peek()
        if follow is not None and follow[0] == "op" and follow[1] in COMPARISONS:
            raise GrammarError("chain comparisons with 'and'")
        return self._node("cmp", depth, op=token[1], args=(left, right))

    def bound_form(self, name: str, depth: int) -> Node:
        self._expect("(")
        body = self.expression(depth + 1)
        self._expect(",")
        kind, variable = self._take()
        if kind != "name" or variable in RESERVED:
            raise GrammarError(f"{name}'s second argument must be a variable name")
        self._expect(",")
        lower = self.expression(depth + 1)
        self._expect(",")
        upper = self.expression(depth + 1)
        self._expect(")")
        if name == "sum":
            for bound in (lower, upper):
                literal = bound.args[0] if bound.kind == "neg" else bound
                if literal.kind == "num" and literal.value > MAX_SAFE_INTEGER:
                    raise GrammarError(f"a sum's bounds must lie within ±{MAX_SAFE_INTEGER}")
        return self._node(name, depth, text=variable, args=(body, lower, upper))


def parse(source: str) -> Node:
    """Parse one expression, or raise :class:`GrammarError` (nothing is evaluated)."""

    return _Parser(source).parse()


# ---------------------------------------------------------------------------
# Static checks over a figure's names
# ---------------------------------------------------------------------------

def walk(node: Node):
    """Every node of ``node`` (no expansion), parent before children, left to
    right. Iterative (fix round 4): no pass over a tree recurses."""

    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.args))


def free_names(node: Node, bound: frozenset[str] = frozenset()) -> set[str]:
    """Names a node reads that it does not bind itself."""

    found: set[str] = set()
    stack = [(node, frozenset(bound))]
    while stack:
        current, scope = stack.pop()
        if current.kind == "name":
            if current.text not in scope and current.text not in CONSTANTS:
                found.add(current.text)
        elif current.kind in ("integral", "sum"):
            body, lower, upper = current.args
            stack += [(body, scope | {current.text}), (lower, scope), (upper, scope)]
        else:
            stack += [(child, scope) for child in current.args]
    return found


#: The deepest an expression may be once its definitions are expanded (fix
#: round 4): every recursive pass (the evaluators, the SymPy translation) is
#: bounded by it, far inside Python's recursion limit. figureGrammar.ts has
#: the same cap.
MAX_EXPANDED_DEPTH = 700


def expansion(node: Node, definitions: Mapping[str, Node], *, limit: int = MAX_EXPANDED_NODES):
    """``(node, depth)`` for every node of ``node`` with definitions expanded
    (a definition's name stands for its body, at the name's depth), parent
    first; iterative, and it stops after ``limit + 1`` nodes (a caller
    comparing against the cap needs no more)."""

    stack: list[tuple[Node, int, tuple[str, ...]]] = [(node, 1, ())]
    count = 0
    while stack:
        current, depth, seen = stack.pop()
        if current.kind == "name" and current.text in definitions and current.text not in seen:
            stack.append((definitions[current.text], depth, (*seen, current.text)))
            continue
        count += 1
        yield current, depth
        if count > limit:
            return
        stack.extend((child, depth + 1, seen) for child in reversed(current.args))


def node_count(node: Node, definitions: Mapping[str, Node]) -> int:
    """Nodes after expanding definitions (a bound on one evaluation's work),
    counted up to ``MAX_EXPANDED_NODES + 1``."""

    return sum(1 for _ in expansion(node, definitions))


def expanded_depth(node: Node, definitions: Mapping[str, Node]) -> int:
    """How deep ``node`` is with definitions expanded (within the node cap)."""

    return max((depth for _node, depth in expansion(node, definitions)), default=0)


def has_bound_form(node: Node, definitions: Mapping[str, Node]) -> bool:
    return any(current.kind in ("integral", "sum") for current, _depth in expansion(node, definitions))


def check_names(node: Node, *, known: frozenset[str], definitions: Mapping[str, Node]) -> None:
    """Every name is known; the expanded expression stays inside the node and
    depth caps (checked first, by iterative passes, fix round 4); no integral
    or sum sits inside another (after expanding definitions)."""

    for name in sorted(free_names(node)):
        if name not in known and name not in definitions:
            raise GrammarError(f"unknown name {name!r}")
    if node_count(node, definitions) > MAX_EXPANDED_NODES:
        raise GrammarError(f"expression expands to more than {MAX_EXPANDED_NODES} nodes")
    if expanded_depth(node, definitions) > MAX_EXPANDED_DEPTH:
        raise GrammarError(f"expression nests deeper than {MAX_EXPANDED_DEPTH} once its definitions are expanded")
    for child in walk(node):
        if child.kind in ("integral", "sum"):
            if child.text in definitions:
                raise GrammarError(f"{child.kind} variable {child.text!r} is a definition's name")
            if has_bound_form(child.args[0], definitions):
                raise GrammarError("no integral or sum inside an integral or sum")
            for bound in child.args[1:]:
                if has_bound_form(bound, definitions):
                    raise GrammarError("no integral or sum inside an integral's or sum's bounds")



# ---------------------------------------------------------------------------
# Evaluation (IEEE doubles, as JavaScript computes them)
# ---------------------------------------------------------------------------

INF = math.inf
NAN = math.nan


def _finite(value: float) -> bool:
    return math.isfinite(value)


def _div(a: float, b: float) -> float:
    if b == 0.0:
        if a == 0.0 or math.isnan(a):
            return NAN
        return INF if (math.copysign(1.0, a) * math.copysign(1.0, b)) > 0 else -INF
    return a / b


def _odd_integer(value: float) -> bool:
    return _finite(value) and value == math.floor(value) and math.fmod(abs(value), 2.0) == 1.0


def _pow(a: float, b: float) -> float:
    if math.isnan(b):
        return NAN
    if b == 0.0:
        return 1.0
    if math.isnan(a):
        return NAN
    if math.isinf(b) and abs(a) == 1.0:
        return NAN
    try:
        return math.pow(a, b)
    except OverflowError:
        return -INF if a < 0 and _odd_integer(b) else INF
    except (ValueError, ZeroDivisionError):
        if a == 0.0 and b < 0:
            return -INF if math.copysign(1.0, a) < 0 and _odd_integer(b) else INF
        return NAN


def _exp(a: float) -> float:
    if math.isnan(a):
        return NAN
    try:
        return math.exp(a)
    except OverflowError:
        return INF


def _log(a: float) -> float:
    if math.isnan(a) or a < 0:
        return NAN
    if a == 0.0:
        return -INF
    return math.log(a)


def _sqrt(a: float) -> float:
    if math.isnan(a) or a < 0:
        return NAN
    return math.sqrt(a)


def _trig(function: Any, a: float) -> float:
    if not _finite(a):
        return NAN
    return function(a)


def _erf(a: float) -> float:
    if math.isnan(a):
        return NAN
    return math.erf(a)


def _phi(a: float) -> float:
    """The standard normal CDF, ``erfc(-a/sqrt 2)/2`` (no cancellation in the left tail)."""

    if math.isnan(a):
        return NAN
    return 0.5 * math.erfc(-a / math.sqrt(2.0))


def _floor(a: float) -> float:
    if not _finite(a):
        return a
    return float(math.floor(a))


def _extreme(values: list[float], pick: Any) -> float:
    if any(math.isnan(value) for value in values):
        return NAN
    return pick(values)


_UNARY = {
    "exp": _exp, "log": _log, "sqrt": _sqrt, "abs": lambda a: abs(a),
    "sin": lambda a: _trig(math.sin, a), "cos": lambda a: _trig(math.cos, a),
    "tan": lambda a: _trig(math.tan, a), "atan": lambda a: NAN if math.isnan(a) else math.atan(a),
    "erf": _erf, "Phi": _phi, "floor": _floor,
}


class _Budget:
    def __init__(self) -> None:
        self.evals = 0


def adaptive_simpson(function: Any, a: float, b: float) -> float:
    """The one integration rule (identical in figureGrammar.ts): adaptive
    Simpson with Richardson's correction, tolerance :data:`SIMPSON_EPS`
    halving per level, at least :data:`SIMPSON_MIN_LEVEL` and at most
    :data:`SIMPSON_MAX_LEVEL` levels, and at most
    :data:`MAX_INTEGRAND_EVALS` evaluations (NaN past it).

    **One-sided endpoint values.** Each interval reads its own endpoints a
    hair inside it (:data:`SIMPSON_NUDGE` of its width), so a ``piecewise``
    jump at an endpoint or at a bisection point (``x < 0`` at 0) is
    integrated from the correct side: the two halves of a split read their
    shared point from their own sides. Smooth integrands are unaffected far
    below the tolerance."""

    if not (_finite(a) and _finite(b)):
        return NAN
    if a == b:
        return 0.0
    budget = _Budget()

    def f(t: float) -> float:
        budget.evals += 1
        return function(t)

    nudge = (b - a) * SIMPSON_NUDGE
    m = (a + b) / 2
    fa, fm, fb = f(a + nudge), f(m), f(b - nudge)
    whole = (b - a) / 6 * (fa + 4 * fm + fb)
    return _simpson_step(f, a, b, fa, fm, fb, whole, SIMPSON_EPS, 0, budget)


def _simpson_step(f: Any, a: float, b: float, fa: float, fm: float, fb: float, whole: float, eps: float,
                  level: int, budget: _Budget) -> float:
    m = (a + b) / 2
    nudge = (m - a) * SIMPSON_NUDGE
    flm = f((a + m) / 2)
    frm = f((m + b) / 2)
    fml = f(m - nudge)
    fmr = f(m + nudge)
    left = (m - a) / 6 * (fa + 4 * flm + fml)
    right = (b - m) / 6 * (fmr + 4 * frm + fb)
    delta = left + right - whole
    if not _finite(delta):
        return NAN
    if level >= SIMPSON_MAX_LEVEL or (level >= SIMPSON_MIN_LEVEL and abs(delta) <= 15 * eps):
        return left + right + delta / 15
    if budget.evals > MAX_INTEGRAND_EVALS:
        return NAN
    return (_simpson_step(f, a, m, fa, flm, fml, left, eps / 2, level + 1, budget)
            + _simpson_step(f, m, b, fmr, frm, fb, right, eps / 2, level + 1, budget))


def exact_sum(function: Any, a: float, b: float) -> float:
    """``function(k)`` summed in order over the integers ``ceil(a) .. floor(b)``
    (a 1e-9 slack on each bound, as in figureGrammar.ts); NaN past
    :data:`MAX_SUM_TERMS` terms, for a bound that is not finite, or for one
    past :data:`MAX_SAFE_INTEGER` (fix round 2). The loop counts its terms."""

    if not (_finite(a) and _finite(b)):
        return NAN
    low = math.ceil(a - 1e-9)
    high = math.floor(b + 1e-9)
    if high < low:
        return 0.0
    if abs(low) > MAX_SAFE_INTEGER or abs(high) > MAX_SAFE_INTEGER:
        return NAN
    count = int(high - low + 1)
    if count > MAX_SUM_TERMS:
        return NAN
    total = 0.0
    # Counted, not stepped: at most MAX_SUM_TERMS terms whatever the bounds.
    for index in range(count):
        total += function(float(low + index))
    return total


def _truth(node: Node, env: Mapping[str, float], definitions: Mapping[str, Node]) -> bool:
    if node.kind == "and":
        return all(_truth(child, env, definitions) for child in node.args)
    if node.kind == "or":
        return any(_truth(child, env, definitions) for child in node.args)
    left = evaluate(node.args[0], env, definitions)
    right = evaluate(node.args[1], env, definitions)
    if math.isnan(left) or math.isnan(right):
        return node.op == "!="
    return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right,
            "==": left == right, "!=": left != right}[node.op]


def canonical(value: float) -> float:
    """``value`` with negative zero as zero: every result either evaluator
    gives (fix round 3; JavaScript's Math.min(0, -0) is -0, Python's min(0.0,
    -0.0) is 0.0, and 1/-0 is -Infinity)."""

    return 0.0 if value == 0 else value


def evaluate(node: Node, env: Mapping[str, float], definitions: Mapping[str, Node] | None = None) -> float:
    """The value of ``node`` with ``env`` (variables and parameters) and
    ``definitions`` (named expressions, evaluated where they are used). An
    unbound name is NaN. Every node's value is :func:`canonical` (no -0).

    One Python frame per level of the expanded expression (fix round 4): the
    compiler caps that depth (:data:`MAX_EXPANDED_DEPTH`), so evaluation never
    reaches the interpreter's recursion limit."""

    defs = definitions or {}
    kind = node.kind
    if kind == "num":
        value = node.value
    elif kind == "name":
        name = node.text
        if name in env:
            value = float(env[name])
        elif name in defs:
            value = evaluate(defs[name], env, defs)
        elif name in CONSTANTS:
            value = CONSTANTS[name]
        else:
            value = NAN
    elif kind == "neg":
        value = -evaluate(node.args[0], env, defs)
    elif kind == "bin":
        a = evaluate(node.args[0], env, defs)
        b = evaluate(node.args[1], env, defs)
        op = node.op
        if op == "+":
            value = a + b
        elif op == "-":
            value = a - b
        elif op == "*":
            value = NAN if (a == 0.0 and math.isinf(b)) or (b == 0.0 and math.isinf(a)) else a * b
        elif op == "/":
            value = _div(a, b)
        else:
            value = _pow(a, b)
    elif kind == "call":
        values = [evaluate(child, env, defs) for child in node.args]
        if node.text == "min":
            value = _extreme(values, min)
        elif node.text == "max":
            value = _extreme(values, max)
        else:
            value = _UNARY[node.text](values[0])
    elif kind == "piecewise":
        args = node.args
        chosen = args[-1]
        for index in range(0, len(args) - 1, 2):
            if _truth(args[index], env, defs):
                chosen = args[index + 1]
                break
        value = evaluate(chosen, env, defs)
    elif kind in ("integral", "sum"):
        body, lower, upper = node.args
        a = evaluate(lower, env, defs)
        b = evaluate(upper, env, defs)
        variable = node.text
        scope = dict(env)

        def at(t: float) -> float:
            scope[variable] = t
            return evaluate(body, scope, defs)

        value = adaptive_simpson(at, a, b) if kind == "integral" else exact_sum(at, a, b)
    else:
        raise GrammarError(f"cannot evaluate a {kind!r} node")
    return 0.0 if value == 0 else value



# ---------------------------------------------------------------------------
# The sympy translation (fixed code; read only inside the sandbox)
# ---------------------------------------------------------------------------

_SYMPY_FUNCTIONS = {"exp": "exp", "log": "log", "sqrt": "sqrt", "abs": "Abs", "sin": "sin", "cos": "cos",
                    "tan": "tan", "atan": "atan", "erf": "erf", "floor": "floor", "min": "Min", "max": "Max"}
_SYMPY_RELATIONS = {"<": "Lt", "<=": "Le", ">": "Gt", ">=": "Ge", "==": "Eq", "!=": "Ne"}
#: The sum's bound slack (:func:`exact_sum`'s 1e-9) in exact form.
SUM_SLACK_SYMPY = "Rational(1, 1000000000)"


def to_sympy(node: Node, definitions: Mapping[str, Node] | None = None) -> str:
    """The expression in sympy syntax, definitions expanded (``E`` for e,
    exact rationals for decimals), for the verifier's sandboxed check. The
    text is parsed only inside the PF-b sandbox, never in-process."""

    defs = definitions or {}
    kind = node.kind
    if kind == "num":
        text = node.text
        return text if re.fullmatch(r"\d+", text) else f"Rational('{text}')"
    if kind == "name":
        if node.text in defs:
            return f"({to_sympy(defs[node.text], defs)})"
        return {"pi": "pi", "e": "E"}.get(node.text, node.text)
    if kind == "neg":
        return f"(-{to_sympy(node.args[0], defs)})"
    if kind == "bin":
        op = "**" if node.op == "^" else node.op
        return f"({to_sympy(node.args[0], defs)} {op} {to_sympy(node.args[1], defs)})"
    if kind == "call":
        args = ", ".join(to_sympy(child, defs) for child in node.args)
        if node.text == "Phi":
            return f"((1 + erf(({args})/sqrt(2)))/2)"
        return f"{_SYMPY_FUNCTIONS[node.text]}({args})"
    if kind == "piecewise":
        args = node.args
        branches = [f"({to_sympy(args[i + 1], defs)}, {to_sympy(args[i], defs)})" for i in range(0, len(args) - 1, 2)]
        branches.append(f"({to_sympy(args[-1], defs)}, True)")
        return f"Piecewise({', '.join(branches)})"
    if kind == "cmp":
        return f"{_SYMPY_RELATIONS[node.op]}({to_sympy(node.args[0], defs)}, {to_sympy(node.args[1], defs)})"
    if kind in ("and", "or"):
        return f"{'And' if kind == 'and' else 'Or'}({', '.join(to_sympy(child, defs) for child in node.args)})"
    if kind == "integral":
        body, lower, upper = node.args
        return f"Integral({to_sympy(body, defs)}, ({node.text}, {to_sympy(lower, defs)}, {to_sympy(upper, defs)}))"
    if kind == "sum":
        # The evaluator's one rule (:func:`exact_sum`): the integers
        # ceil(a - 1e-9) .. floor(b + 1e-9), and an empty range is 0. SymPy's
        # own Sum would sum a reversed range negatively (Karr) and keep
        # fractional bounds, so the rule is written out (fix round 3).
        body, lower, upper = node.args
        low = f"ceiling({to_sympy(lower, defs)} - {SUM_SLACK_SYMPY})"
        high = f"floor({to_sympy(upper, defs)} + {SUM_SLACK_SYMPY})"
        return (f"Piecewise((Sum({to_sympy(body, defs)}, ({node.text}, {low}, {high})), Ge({high}, {low})), "
                f"(0, True))")
    raise GrammarError(f"cannot translate a {kind!r} node")


#: Constructs whose value the evaluator's floating point decides where exact
#: arithmetic decides otherwise, densely and at the renderer's own sample
#: points: an equality test, and floor (an integrality test at every
#: integer). A definition using one is not source-verifiable (fix round 3).
UNVERIFIABLE_COMPARISONS = ("==", "!=")
UNVERIFIABLE_FUNCTIONS = ("floor",)
#: An integral is the fixed adaptive Simpson rule, an approximation SymPy's
#: exact Integral does not reproduce (it parts from it by more than the
#: corpus tolerance at a jump), so a definition with one is not
#: source-verifiable either (fix round 3).
UNVERIFIABLE_FORMS = ("integral",)


def sympy_problem(node: Node, definitions: Mapping[str, Node] | None = None) -> str | None:
    """Why :func:`to_sympy` cannot reproduce the evaluator's value of
    ``node`` (definitions expanded) exactly, or None: what the source match
    may check (fix round 3). Ordered comparisons, sums (by the shared bound
    rule) and every other construct but equality, floor and integral
    translate exactly; a comparison's
    rounding-decided boundary is a set of measure zero the check never
    relies on."""

    defs = definitions or {}
    seen: set[str] = set()
    pending = [node]
    while pending:
        current = pending.pop()
        if current.kind == "name" and current.text in defs and current.text not in seen:
            seen.add(current.text)
            pending.append(defs[current.text])
            continue
        if current.kind == "cmp" and current.op in UNVERIFIABLE_COMPARISONS:
            return (f"the definition tests equality ({current.op}), which floating point decides where the book's "
                    "exact equation does not")
        if current.kind == "call" and current.text in UNVERIFIABLE_FUNCTIONS:
            return (f"the definition uses {current.text}, whose steps floating point places where the book's "
                    "exact equation does not")
        if current.kind in UNVERIFIABLE_FORMS:
            return ("the definition uses an integral, which the figure approximates by a fixed rule where the "
                    "book's equation is exact")
        pending.extend(current.args)
    return None


__all__ = [
    "CONSTANTS",
    "FUNCTIONS",
    "GrammarError",
    "MAX_DEPTH",
    "MAX_EXPANDED_DEPTH",
    "MAX_EXPR_CHARS",
    "MAX_NODES",
    "MAX_SAFE_INTEGER",
    "MAX_SUM_TERMS",
    "PROTOTYPE_NAMES",
    "Node",
    "RESERVED",
    "adaptive_simpson",
    "canonical",
    "check_names",
    "evaluate",
    "exact_sum",
    "expanded_depth",
    "expansion",
    "free_names",
    "has_bound_form",
    "is_name",
    "parse",
    "sympy_problem",
    "to_sympy",
    "walk",
]
