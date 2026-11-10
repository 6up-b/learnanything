"""Reader RW5c: the check's one fixed harness, run in the PF-b sandbox (spec §6.2-§6.5).

This file is a program, not a module of the package: :mod:`.source_check` sends
its text to :func:`learnloop.content.authoring.pf_sandbox.run_sandboxed_python`
beside ``display_format.py``, and records the sha256 of the two on every check
row. sympy evaluates what it is given, so it never runs in-process.

**The payload is ASTs, not text.** Both sides of every pair and every control
come as JSON grammar nodes from a closed set of kinds, and sympy objects are
built node by node through an exact table. Nothing here parses text.

**Equality** (§6.3), per pair: the real line is split at both sides'
breakpoints (exact literals). On each open interval each side's branch is
chosen at an exact rational point; the branches must simplify to an identity
and their domains must agree, read from the unsimplified ASTs through exact
definedness conditions. At each breakpoint both sides must be defined with
equal values, or both undefined. A pair is ``equal`` (proved, domains included),
``different`` (proved: disjoint intervals at a rational point, or a point where
one side has a value and the other none) or ``undecided``.

**Controls** (§6.5): each must come back not ``equal``. **Display agreement**
(§6.4): at every displayed sample of every grid point the exact value of the
book's equation, as displayed, equals the string the figure shows.
"""

import json
import os
import signal
import sys
import time

if __name__ == "__main__":
    # In the sandbox ``-I`` leaves the script's directory off the path; display_format.py is beside it.
    sys.path.insert(0, sys.argv[1])
    sys.setrecursionlimit(20000)
MARKER = "@@PF-SANDBOX-RESULT@@"


class _Timeout(BaseException):
    """Past a bound (a BaseException: sympy catches Exception in places)."""


def _alarm(_signum, _frame):
    raise _Timeout()


from fractions import Fraction  # noqa: E402

import mpmath  # noqa: E402
from mpmath import iv  # noqa: E402
import sympy  # noqa: E402

try:
    from display_format import format_value  # noqa: E402
except ImportError:  # imported, not run (a module walk): the package's own copy of the same file
    from learnloop.figures.display_format import format_value  # noqa: E402

CONSTANTS = {"pi": sympy.pi, "e": sympy.E}
TOTAL = {"exp", "sin", "cos", "atan", "erf", "Phi", "abs", "min", "max"}
#: G22's existing parity bound between the two evaluators (spec §6.4, §15).
PARITY = Fraction(1, 10 ** 9)


class Undecided(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class Different(Exception):
    def __init__(self, witness):
        super().__init__("different")
        self.witness = witness


class Undefined(Exception):
    """A side has no value at this point."""


class Unresolved(Exception):
    """The interval is too wide to say."""


# -- ASTs ---------------------------------------------------------------------

def num_value(node):
    return Fraction(node["t"])


def constant_value(node):
    """A node built only from num, neg and + - * /: its exact value (§6.3 step 3, F8), or None."""

    kind = node["k"]
    if kind == "num":
        return num_value(node)
    if kind == "neg":
        inner = constant_value(node["a"][0])
        return None if inner is None else -inner
    if kind == "bin" and node["o"] in "+-*/":
        left, right = constant_value(node["a"][0]), constant_value(node["a"][1])
        if left is None or right is None:
            return None
        op = node["o"]
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if right == 0:
            raise Undecided("domain")
        return left / right
    return None


def canonical(node):
    """The same tree with + and * flattened and ordered, and each literal's exact value."""

    kind = node["k"]
    if kind == "num":
        return ["num", str(num_value(node))]
    if kind == "name":
        return ["name", node["t"]]
    if kind == "bin" and node["o"] in "+*":
        op = node["o"]
        parts = []
        stack = list(node["a"])
        while stack:
            current = stack.pop()
            if current["k"] == "bin" and current["o"] == op:
                stack.extend(current["a"])
            else:
                parts.append(canonical(current))
        return ["bin", op, sorted(parts, key=lambda part: json.dumps(part))]
    return [kind, node.get("t", ""), node.get("o", ""), [canonical(child) for child in node.get("a", [])]]


def has_piecewise(node):
    stack = [node]
    while stack:
        current = stack.pop()
        if current["k"] == "piecewise":
            return True
        stack.extend(current.get("a", []))
    return False


def literal(node):
    if node["k"] == "num":
        return num_value(node)
    if node["k"] == "neg" and node["a"][0]["k"] == "num":
        return -num_value(node["a"][0])
    return None


def breakpoints(node, variable):
    """Where a side's branches change: every comparison is the variable against
    an exact literal, or the pair is ``parametric_breakpoint`` (P1, §6.3)."""

    found = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current["k"] == "cmp":
            left, right = current["a"]
            value = None
            if left["k"] == "name" and left["t"] == variable:
                value = literal(right)
            elif right["k"] == "name" and right["t"] == variable:
                value = literal(left)
            if value is None:
                raise Undecided("parametric_breakpoint")
            found.add(value)
            continue
        stack.extend(current.get("a", []))
    return found


def holds(condition, variable, point):
    kind = condition["k"]
    if kind == "and":
        return all(holds(child, variable, point) for child in condition["a"])
    if kind == "or":
        return any(holds(child, variable, point) for child in condition["a"])
    left, right = condition["a"]
    op = condition["o"]
    a = point if left["k"] == "name" and left["t"] == variable else literal(left)
    b = point if right["k"] == "name" and right["t"] == variable else literal(right)
    if a is None or b is None:
        raise Undecided("parametric_breakpoint")
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def resolve(node, variable, point):
    """The branch-free AST that holds at ``point`` (exact)."""

    if node["k"] == "piecewise":
        args = node["a"]
        for index in range(0, len(args) - 1, 2):
            if holds(args[index], variable, point):
                return resolve(args[index + 1], variable, point)
        return resolve(args[-1], variable, point)
    if node.get("a"):
        return {**node, "a": [resolve(child, variable, point) for child in node["a"]]}
    return node


# -- sympy, node by node ----------------------------------------------------------

def to_sympy(node, symbols):
    kind = node["k"]
    if kind == "num":
        value = num_value(node)
        return sympy.Rational(value.numerator, value.denominator)
    if kind == "name":
        if node["t"] in CONSTANTS:
            return CONSTANTS[node["t"]]
        return symbols[node["t"]]
    if kind == "neg":
        return -to_sympy(node["a"][0], symbols)
    if kind == "bin":
        left, right = to_sympy(node["a"][0], symbols), to_sympy(node["a"][1], symbols)
        op = node["o"]
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        return left ** right
    if kind == "call":
        args = [to_sympy(child, symbols) for child in node["a"]]
        name = node["t"]
        if name == "exp":
            return sympy.exp(args[0])
        if name == "log":
            return sympy.log(args[0])
        if name == "sqrt":
            return sympy.sqrt(args[0])
        if name == "abs":
            return sympy.Abs(args[0])
        if name == "sin":
            return sympy.sin(args[0])
        if name == "cos":
            return sympy.cos(args[0])
        if name == "tan":
            return sympy.tan(args[0])
        if name == "atan":
            return sympy.atan(args[0])
        if name == "erf":
            return sympy.erf(args[0])
        if name == "Phi":
            return (1 + sympy.erf(args[0] / sympy.sqrt(2))) / 2
        if name == "min":
            return sympy.Min(*args)
        if name == "max":
            return sympy.Max(*args)
    raise Undecided("no_proof")


def make_symbols(payload):
    symbols = {}
    for name, sign in payload["assumptions"].items():
        if sign == "positive":
            symbols[name] = sympy.Symbol(name, positive=True)
        elif sign == "nonnegative":
            symbols[name] = sympy.Symbol(name, nonnegative=True)
        else:
            symbols[name] = sympy.Symbol(name, real=True)
    return symbols


# -- Definedness, read from the unsimplified AST (§6.3 step 3) ------------------------

def proved_true(kind, expression):
    if kind == "gt":
        return expression.is_positive is True
    if kind == "ge":
        return expression.is_nonnegative is True
    if kind == "ne":
        return expression.is_nonzero is True or expression.is_positive is True or expression.is_negative is True
    return False


def conditions(node, symbols):
    """Each node's exact condition on the branch-free AST: a point satisfies all
    of them exactly when the side has a real value there. Any power whose domain
    cannot be stated exactly raises ``domain`` (F8)."""

    found = {}

    def add(kind, expression):
        if proved_true(kind, expression):
            return
        canonical_form = sympy.expand(expression)
        found[(kind, sympy.srepr(canonical_form))] = (kind, expression)

    stack = [node]
    while stack:
        current = stack.pop()
        kind = current["k"]
        stack.extend(current.get("a", []))
        if kind == "bin" and current["o"] == "/":
            add("ne", to_sympy(current["a"][1], symbols))
        elif kind == "bin" and current["o"] == "^":
            base = to_sympy(current["a"][0], symbols)
            if base.is_positive is True:
                continue
            exponent = constant_value(current["a"][1])
            if exponent is None:
                raise Undecided("domain")
            if exponent.denominator == 1:
                if exponent < 0:
                    add("ne", base)
            elif exponent.denominator % 2 == 0:
                add("ge" if exponent > 0 else "gt", base)
            else:
                raise Undecided("domain")
        elif kind == "call":
            name = current["t"]
            if name == "sqrt":
                add("ge", to_sympy(current["a"][0], symbols))
            elif name == "log":
                add("gt", to_sympy(current["a"][0], symbols))
            elif name == "tan":
                add("ne", sympy.cos(to_sympy(current["a"][0], symbols)))
            elif name not in TOTAL:
                raise Undecided("domain")
    return found


def excluded_set(found, variable, domain):
    """Where a side has no value on ``domain``: the union of each negated condition's solution set."""

    parts = []
    for kind, expression in found.values():
        if kind == "ne":
            parts.append(sympy.solveset(sympy.Eq(expression, 0), variable, domain=domain))
        elif kind == "ge":
            parts.append(sympy.solveset(expression < 0, variable, domain=domain))
        else:
            parts.append(sympy.solveset(expression <= 0, variable, domain=domain))
    return sympy.Union(*parts) if parts else sympy.S.EmptySet


def comparable(found_set):
    return isinstance(found_set, (sympy.FiniteSet, sympy.Interval, sympy.Union)) or found_set is sympy.S.EmptySet


def set_point(found_set):
    """An exact point of a non-empty set of the shapes :func:`comparable` allows."""

    if isinstance(found_set, sympy.FiniteSet):
        return next(iter(found_set))
    if isinstance(found_set, sympy.Interval):
        low, high = found_set.start, found_set.end
        if low is sympy.S.NegativeInfinity and high is sympy.S.Infinity:
            return sympy.Integer(0)
        if low is sympy.S.NegativeInfinity:
            return high - 1
        if high is sympy.S.Infinity:
            return low + 1
        return (low + high) / 2
    if isinstance(found_set, sympy.Union):
        return set_point(found_set.args[0])
    raise Undecided("domain")


def domains_agree(a_ast, b_ast, symbols, variable, domain, point_text):
    """Step 3 on one interval: agree, or raise ``different`` with a witness or ``undecided`` (``domain``)."""

    left, right = conditions(a_ast, symbols), conditions(b_ast, symbols)
    if set(left) == set(right):
        return
    symbol = symbols.get(variable) if variable else None
    free = {free_symbol for _kind, expression in (*left.values(), *right.values())
            for free_symbol in expression.free_symbols}
    if symbol is None or free - {symbol}:
        raise Undecided("domain")
    a_excluded = excluded_set(left, symbol, domain)
    b_excluded = excluded_set(right, symbol, domain)
    if not (comparable(a_excluded) and comparable(b_excluded)):
        raise Undecided("domain")
    if a_excluded == b_excluded:
        return
    only_a, only_b = sympy.Complement(a_excluded, b_excluded), sympy.Complement(b_excluded, a_excluded)
    if not (comparable(only_a) and comparable(only_b)):
        raise Undecided("domain")
    if only_a is sympy.S.EmptySet and only_b is sympy.S.EmptySet:
        return
    if only_a is not sympy.S.EmptySet:
        raise Different({"kind": "domain", "at": point_text(set_point(only_a)), "defined": "book"})
    raise Different({"kind": "domain", "at": point_text(set_point(only_b)), "defined": "figure"})


# -- Interval evaluation at exact rational points ---------------------------------------

def exact_interval(value):
    return iv.mpf(value.numerator) / iv.mpf(value.denominator)


def raw_fraction(raw):
    sign, man, exponent, _bc = raw
    value = Fraction(man) * (Fraction(2) ** exponent)
    return -value if sign else value


def endpoints(interval):
    low, high = interval._mpi_
    return raw_fraction(low), raw_fraction(high)


def monotone(function, interval):
    """An enclosure of an increasing function iv has no rule for, from correctly
    computed endpoints widened at the working precision."""

    low, high = endpoints(interval)
    with mpmath.workprec(iv.prec + 32):
        a = function(mpmath.mpf(low.numerator) / mpmath.mpf(low.denominator))
        b = function(mpmath.mpf(high.numerator) / mpmath.mpf(high.denominator))
        slack = mpmath.ldexp(mpmath.mpf(1), -iv.prec) * (1 + max(abs(a), abs(b)))
        return iv.mpf([a - slack, b + slack])


def contains_zero(interval):
    low, high = endpoints(interval)
    return low <= 0 <= high


def exact_zero(interval):
    low, high = endpoints(interval)
    return low == 0 and high == 0


def evaluate(node, env):
    """The interval of a branch-chosen AST at an exact point, or Undefined / Unresolved."""

    kind = node["k"]
    if kind == "num":
        return exact_interval(num_value(node))
    if kind == "name":
        name = node["t"]
        if name == "pi":
            return iv.pi
        if name == "e":
            return iv.e
        return exact_interval(env[name])
    if kind == "neg":
        return -evaluate(node["a"][0], env)
    if kind == "bin":
        op = node["o"]
        left = evaluate(node["a"][0], env)
        if op == "^":
            return power(left, node["a"][1], env)
        right = evaluate(node["a"][1], env)
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if exact_zero(right):
            raise Undefined()
        if contains_zero(right):
            raise Unresolved()
        return left / right
    if kind == "call":
        name = node["t"]
        args = [evaluate(child, env) for child in node["a"]]
        first = args[0]
        if name == "exp":
            return iv.exp(first)
        if name == "log":
            low, high = endpoints(first)
            if high <= 0:
                raise Undefined()
            if low <= 0:
                raise Unresolved()
            return iv.log(first)
        if name == "sqrt":
            low, high = endpoints(first)
            if high < 0:
                raise Undefined()
            if low < 0:
                raise Unresolved()
            return iv.sqrt(first)
        if name == "abs":
            return abs(first)
        if name == "sin":
            return iv.sin(first)
        if name == "cos":
            return iv.cos(first)
        if name == "tan":
            if contains_zero(iv.cos(first)):
                raise Unresolved()
            return iv.tan(first)
        if name == "atan":
            return monotone(mpmath.atan, first)
        if name == "erf":
            return monotone(mpmath.erf, first)
        if name == "Phi":
            return (1 + monotone(mpmath.erf, first / iv.sqrt(iv.mpf(2)))) / 2
        if name in ("min", "max"):
            # Each end is one argument's own end, carried over exactly.
            pick = min if name == "min" else max
            low = pick((arg._mpi_[0] for arg in args), key=raw_fraction)
            high = pick((arg._mpi_[1] for arg in args), key=raw_fraction)
            return iv.make_mpf((low, high))
    raise Unresolved()


def power(base, exponent_node, env):
    exponent = constant_value(exponent_node)
    if exponent is not None and exponent.denominator == 1:
        n = int(exponent)
        if n == 0:
            return iv.mpf(1)
        if n > 0:
            return base ** n
        if exact_zero(base):
            raise Undefined()
        if contains_zero(base):
            raise Unresolved()
        return iv.mpf(1) / (base ** (-n))
    low, high = endpoints(base)
    if exponent is not None:
        if exponent.denominator % 2 == 1:
            raise Unresolved()
        if exact_zero(base):
            if exponent > 0:
                return iv.mpf(0)
            raise Undefined()
        if high < 0:
            raise Undefined()
        if low <= 0:
            raise Unresolved()
        return iv.exp(exact_interval(exponent) * iv.log(base))
    if low > 0:
        return iv.exp(evaluate(exponent_node, env) * iv.log(base))
    raise Unresolved()


def value_at(ast, variable, env):
    """``ast`` at the exact point ``env``: an interval, ``None`` when it has no value."""

    point = env.get(variable) if variable else None
    branch = resolve(ast, variable, point) if has_piecewise(ast) else ast
    try:
        return evaluate(branch, env)
    except Undefined:
        return None


def fraction_text(value):
    return f"{value.numerator}/{value.denominator}" if value.denominator != 1 else str(value.numerator)


def proof_of_difference(a_ast, b_ast, payload, deadline):
    """Two disjoint intervals at an exact point, or a point where only one side
    has a value (§6.3 step 5); None within the bound."""

    variable = payload["variable"]
    for grid_point in payload["points"]:
        env = {name: Fraction(text) for name, text in grid_point.items()}
        for prec in (64, 128, 256, 512, 1024):
            if time.process_time() > deadline:
                raise Undecided("timeout")
            iv.prec = prec
            try:
                left, right = value_at(a_ast, variable, env), value_at(b_ast, variable, env)
            except Unresolved:
                continue
            if left is None and right is None:
                break
            if left is None or right is None:
                return {"kind": "domain", "at": {name: fraction_text(value) for name, value in env.items()},
                        "defined": "figure" if left is None else "book"}
            a_low, a_high = endpoints(left)
            b_low, b_high = endpoints(right)
            if a_high < b_low or b_high < a_low:
                return {"kind": "value", "at": {name: fraction_text(value) for name, value in env.items()}}
    return None


# -- Deciding one pair (§6.3) ----------------------------------------------------------

def decide(figure, book, payload, symbols, deadline, *, control=False):
    """``{"result": equal | different | undecided, ...}``. A control asks only
    whether it would be accepted, so no proof of difference is spent on it."""

    variable = payload["variable"]
    try:
        cuts = sorted(breakpoints(figure, variable) | breakpoints(book, variable)) if (
            has_piecewise(figure) or has_piecewise(book)) else []
        if cuts and not variable:
            raise Undecided("parametric_breakpoint")
        if not variable and (has_piecewise(figure) or has_piecewise(book)):
            raise Undecided("parametric_breakpoint")
        symbol = symbols.get(variable) if variable else None

        def point_text(point):
            value = sympy.Rational(point) if point.is_rational else None
            text = str(value) if value is not None else str(point)
            return {variable: text} if variable else {}

        pieces = []
        if cuts:
            bounds = [sympy.S.NegativeInfinity, *[sympy.Rational(c.numerator, c.denominator) for c in cuts],
                      sympy.S.Infinity]
            inner = [cuts[0] - 1, *[(left + right) / 2 for left, right in zip(cuts, cuts[1:], strict=False)], cuts[-1] + 1]
            pieces = [(sympy.Interval.open(bounds[i], bounds[i + 1]), inner[i]) for i in range(len(inner))]
        else:
            pieces = [(sympy.S.Reals, Fraction(0))]
        proved = True
        for domain, interior in pieces:
            a_branch = resolve(figure, variable, interior) if cuts else figure
            b_branch = resolve(book, variable, interior) if cuts else book
            # Structural equality spares sympy the proof (step 4), never the domain rule:
            # a power whose domain code cannot state exactly stays undecided (F8).
            domains_agree(a_branch, b_branch, symbols, variable, domain, point_text)
            if canonical(a_branch) == canonical(b_branch):
                continue
            difference = to_sympy(a_branch, symbols) - to_sympy(b_branch, symbols)
            if sympy.simplify(difference) != 0:
                proved = False
                break
        if proved:
            for cut in cuts:
                value = sympy.Rational(cut.numerator, cut.denominator)
                a_branch, b_branch = resolve(figure, variable, cut), resolve(book, variable, cut)
                a_defined = defined_at(a_branch, symbols, symbol, value)
                b_defined = defined_at(b_branch, symbols, symbol, value)
                if a_defined != b_defined:
                    raise Different({"kind": "domain", "at": point_text(value),
                                     "defined": "figure" if a_defined else "book"})
                if a_defined and sympy.simplify((to_sympy(a_branch, symbols) - to_sympy(b_branch, symbols))
                                                .subs(symbol, value)) != 0:
                    proved = False
                    break
        if proved:
            return {"result": "equal"}
    except Different as found:
        return {"result": "different", "witness": found.witness}
    if control:
        return {"result": "undecided", "reason": "no_proof"}
    witness = proof_of_difference(figure, book, payload, deadline)
    if witness is not None:
        return {"result": "different", "witness": witness}
    return {"result": "undecided", "reason": "no_proof"}


def defined_at(branch, symbols, symbol, value):
    """Whether a branch-free side has a value at the exact ``value``; parameter-dependent: undecided."""

    for kind, expression in conditions(branch, symbols).values():
        substituted = expression.subs(symbol, value)
        if kind == "ne":
            verdict = substituted.is_nonzero
            if verdict is None and substituted.is_zero is True:
                verdict = False
        elif kind == "ge":
            verdict = substituted.is_nonnegative
        else:
            verdict = substituted.is_positive
        if verdict is None:
            raise Undecided("domain")
        if verdict is False:
            return False
    return True


# -- Display agreement (§6.4) --------------------------------------------------------

def exact_shown(book, variable, env, kind, deadline):
    """The book's value at this exact point as displayed: its interval, widened
    by G22's parity bound, formats to one string (else rounding decides, None);
    no value is the renderer's dash."""

    prec = 64
    while True:
        if time.process_time() > deadline:
            raise Undecided("timeout")
        iv.prec = prec
        try:
            interval = value_at(book, variable, env)
        except Unresolved:
            prec *= 2
            if prec > 16384:
                return None
            continue
        if interval is None:
            return format_value(None)
        low, high = endpoints(interval)
        wide_low = low - abs(low) * PARITY
        wide_high = high + abs(high) * PARITY
        left, right = format_value(wide_low, kind), format_value(wide_high, kind)
        if left == right:
            return left
        if high - low <= (abs(low) + abs(high)) * PARITY or prec > 16384:
            return None
        prec *= 2


def display_agreement(book, element, deadline, per_check):
    """Every displayed sample's string equal to the exact value's, or the first that is not."""

    samples = 0
    kind = element["format"]
    variable = element["variable"]
    for grid in element["grid"]:
        env = {name: Fraction(text) for name, text in grid["params"].items()}
        for sample in grid["samples"]:
            if variable:
                env[variable] = Fraction(sample["at"])
            if time.process_time() > deadline:
                return {"samples": samples, "agreed": False, "reason": "timeout"}
            signal.alarm(per_check)
            try:
                expected = exact_shown(book, variable, env, kind, deadline)
            except Undecided as stopped:
                return {"samples": samples, "agreed": False, "reason": stopped.reason}
            finally:
                signal.alarm(0)
            samples += 1
            if expected is None or expected != sample["shown"]:
                return {"samples": samples, "agreed": False, "reason": "display_disagrees"}
    return {"samples": samples, "agreed": True}


# -- The run ---------------------------------------------------------------------

def run_pair(pair, payload, symbols, deadline, per_check):
    signal.alarm(per_check)
    try:
        found = decide(pair["figure"], pair["book"], payload, symbols, deadline)
    finally:
        signal.alarm(0)
    return found


def main():
    signal.signal(signal.SIGALRM, _alarm)
    with open(os.path.join(sys.argv[1], "input.json"), encoding="utf-8") as handle:
        payload = json.load(handle)
    per_check = int(payload["per_check_seconds"])
    # Stop starting new work while one more unit still fits inside the CPU
    # limit, so what finished is reported (a timeout: undecided for the rest).
    deadline = float(payload["cpu_seconds"]) - per_check
    results = []
    done = set()
    stated_different = set()
    for definition in payload["definitions"]:
        symbols = make_symbols({"assumptions": definition["assumptions"]})
        common = {"variable": definition["variable"], "points": definition["points"]}
        name = definition["name"]
        for pair in definition["pairs"]:
            entry = {"definition": name, "candidate": pair["candidate"]}
            results.append(entry)
            if name in done or (not pair["stated"] and name in stated_different):
                entry.update(result="skipped")
                continue
            if time.process_time() > deadline:
                entry.update(result="undecided", reason="timeout")
                continue
            try:
                entry.update(run_pair(pair, common, symbols, deadline, per_check))
            except Undecided as stopped:
                entry.update(result="undecided", reason=stopped.reason)
            except _Timeout:
                entry.update(result="undecided", reason="timeout")
            except Exception as failure:  # noqa: BLE001 - a harness fault decides nothing
                entry.update(result="undecided", reason="no_proof", error=type(failure).__name__)
            if entry["result"] == "different" and pair["stated"]:
                stated_different.add(name)
            if entry["result"] != "equal":
                continue
            controls = []
            for control in pair["controls"]:
                if time.process_time() > deadline:
                    controls.append("undecided")
                    continue
                signal.alarm(per_check)
                try:
                    controls.append(decide(control, pair["book"], common, symbols, deadline, control=True)["result"])
                except Undecided:
                    controls.append("undecided")
                except _Timeout:
                    controls.append("undecided")
                except Exception:  # noqa: BLE001 - a control that cannot be decided accepts nothing
                    controls.append("undecided")
                finally:
                    signal.alarm(0)
            entry["controls"] = controls
            if any(answer == "equal" for answer in controls):
                continue
            done.add(name)
            entry["display"] = {}
            for element in definition["elements"]:
                try:
                    entry["display"][element["id"]] = display_agreement(pair["book"], element, deadline, per_check)
                except _Timeout:
                    entry["display"][element["id"]] = {"samples": 0, "agreed": False, "reason": "timeout"}
                except Exception as failure:  # noqa: BLE001 - never shown as agreeing
                    entry["display"][element["id"]] = {"samples": 0, "agreed": False, "reason": "display_disagrees",
                                                       "error": type(failure).__name__}
    print(MARKER + json.dumps({"sympy_version": sympy.__version__, "results": results}))



if __name__ == "__main__":
    main()
