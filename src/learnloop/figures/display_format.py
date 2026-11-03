"""Reader RW5c: the Python twins of how a figure's numbers are displayed (spec §6.4, §7.2; G22).

``format_value`` is ``formatValue`` of ``FigurePanels.tsx`` (5 significant
digits, exponent form outside [1e-3, 1e5), a percent to 0.1), computed exactly:
it takes a double as the renderer does, or an exact ``Fraction`` (the book's
equation at a sample, §6.4). ``js_string`` is JavaScript's ``String(v)``, the
shortest decimal that reads back as the same double: how a derived label's
continuous bound is written, because ``format_value`` can show two different
numbers alike (Codex re-review F9). Both join G22's golden corpus.

Standard library only, with nothing from the package: the check's harness runs
this same file inside the sandbox.
"""

from fractions import Fraction
import math

_EXPONENT_LOW = Fraction(1e-3)
_EXPONENT_HIGH = Fraction(1e5)
NO_VALUE = "—"


def _floor_log10(value):
    """floor(log10(value)) of a positive Fraction, exactly."""

    guess = len(str(value.numerator)) - len(str(value.denominator))
    while Fraction(10) ** guess > value:
        guess -= 1
    while Fraction(10) ** (guess + 1) <= value:
        guess += 1
    return guess


def _rounded(value, digits):
    """``(n, e)`` with ``n`` the ``digits`` significant digits of a positive
    Fraction, ties to the larger ``n`` (ECMAScript's toPrecision and
    toExponential), and ``e`` its decimal exponent."""

    exponent = _floor_log10(value)
    scaled = value / Fraction(10) ** (exponent - digits + 1)
    whole = math.floor(scaled + Fraction(1, 2))
    if whole == 10 ** digits:
        whole = 10 ** (digits - 1)
        exponent += 1
    return whole, exponent


def _plain(whole, exponent, digits):
    """``String(Number(...))`` of ``whole`` x 10**(exponent - digits + 1), within
    the range where JavaScript writes no exponent: trailing zeros dropped."""

    text = str(whole).rstrip("0") or "0"
    point = exponent + 1
    if point <= 0:
        return "0." + "0" * (-point) + text
    if point >= len(text):
        return text + "0" * (point - len(text))
    return text[:point] + "." + text[point:]


def js_string(value):
    """JavaScript's ``String(value)`` for a finite double."""

    value = float(value)
    if value == 0:
        return "0"
    if math.isinf(value) or math.isnan(value):
        return "Infinity" if value > 0 else ("-Infinity" if value < 0 else "NaN")
    sign = "-" if value < 0 else ""
    mantissa, _, power = repr(abs(value)).partition("e")
    whole, _, fraction = mantissa.partition(".")
    fraction = "" if fraction == "0" else fraction
    digits = (whole + fraction).lstrip("0")
    leading = len(whole + fraction) - len(digits)
    digits = digits.rstrip("0") or "0"
    # n: where the decimal point sits relative to the digits (ECMAScript's n).
    n = len(whole) - leading + int(power or 0)
    k = len(digits)
    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    exponent = n - 1
    mark = "+" if exponent >= 0 else "-"
    if k == 1:
        return f"{sign}{digits}e{mark}{abs(exponent)}"
    return f"{sign}{digits[0]}.{digits[1:]}e{mark}{abs(exponent)}"


def format_value(value, kind="number"):
    """``formatValue``: a double (or an exact Fraction) as the figure displays it."""

    if value is None:
        return NO_VALUE
    exact = isinstance(value, Fraction)
    if not exact and not math.isfinite(value):
        return NO_VALUE
    if kind == "percent":
        # The scaled number is what is shown: a double's product is a double's, guarded too.
        if exact:
            scaled = value * 100
        else:
            product = float(value) * 100
            if not math.isfinite(product):
                return NO_VALUE
            scaled = Fraction(product)
        magnitude = abs(scaled)
        if magnitude >= Fraction(10) ** 21:
            return js_string(float(scaled)) + "%"
        tenths = math.floor(magnitude * 10 + Fraction(1, 2))
        sign = "-" if scaled < 0 else ""
        return f"{sign}{tenths // 10}.{tenths % 10}%"
    number = value if exact else Fraction(float(value))
    if number == 0:
        return "0"
    sign = "-" if number < 0 else ""
    magnitude = abs(number)
    if magnitude >= _EXPONENT_HIGH or magnitude < _EXPONENT_LOW:
        whole, exponent = _rounded(magnitude, 4)
        text = str(whole)
        mark = "+" if exponent >= 0 else "-"
        return f"{sign}{text[0]}.{text[1:]}e{mark}{abs(exponent)}"
    whole, exponent = _rounded(magnitude, 5)
    return sign + _plain(whole, exponent, 5)
