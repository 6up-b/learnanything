"""What KaTeX's rendered output means (RW5c, the shared test of spec §5.3).

An independent reading of the MathML KaTeX builds for the page: never the parse tree
``book_math`` translates, and never its rules. It reads juxtaposition as a product and
adjacent digits as a numeral, as the page does, and gives a grammar ``Node`` so both
sides are evaluated by one evaluator: a difference is a difference of meaning.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree

from learnloop.content.sources.math_text import GREEK
from learnloop.figures import grammar as G
from learnloop.figures import katex_tree as KT
from learnloop.figures import sketch_engine as SE

_RENDER = """
function view(state, p) {
  try { return {mathml: katex.renderToString(p.tex, {output: "mathml", throwOnError: true, displayMode: p.display})}; }
  catch (error) { if (error && error.name === "ParseError") { return {refused: true}; } throw error; }
}
"""
_FUNCTIONS = {"sin": "sin", "cos": "cos", "tan": "tan", "arctan": "atan", "exp": "exp", "ln": "log", "erf": "erf"}
_APPLY = "⁡"
_OPS = {"+": "+", "−": "-", "⋅": "*", "×": "*", "∗": "*", "/": "/"}
_CLOSE = {"(": ")", "[": "]", "{": "}"}
_RELS = {"<": "<", ">": ">", "≤": "<=", "≥": ">=", "⩽": "<=", "⩾": ">="}


class Renderer:
    """The Reader's KaTeX (the vendored file the pin test ties to its lock) rendering MathML."""

    def __enter__(self) -> "Renderer":
        self.engine = SE.SketchEngine(path=KT.KATEX_ENGINE_PATH, expected=KT.KATEX_ENGINE_SHA256)
        self.engine.load(KT.KATEX_PATH.read_text(encoding="utf-8") + _RENDER)
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.engine.close()

    def mathml(self, tex: str, *, display: bool = False) -> str | None:
        """The ``<semantics>`` contents, as the page's markup holds them; None when KaTeX refuses."""

        answer = self.engine.view({"tex": tex, "display": display}, index=0)
        return None if answer.get("refused") else semantics(answer["mathml"])


def semantics(markup: str) -> str:
    found = re.search(r"<semantics>(?:<mrow>)?([\s\S]*?)(?:</mrow>)?<annotation", markup)
    assert found, markup
    return found.group(1)


def _local(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _symbol(text: str) -> str:
    return GREEK.get(text, text)


class _Meaning:
    def __init__(self, tokens: list[tuple]) -> None:
        self.tokens = tokens
        self.position = 0

    def peek(self) -> tuple | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def take(self) -> tuple:
        token = self.peek()
        assert token is not None, "the rendering ended early"
        self.position += 1
        return token

    def expression(self) -> G.Node:
        first = self.peek()
        if first == ("op", "-"):
            self.take()
            node = G.Node("neg", args=(self.term(),))
        else:
            node = self.term()
        while (token := self.peek()) in (("op", "+"), ("op", "-")):
            self.take()
            node = G.Node("bin", op=token[1], args=(node, self.term()))
        return node

    def term(self) -> G.Node:
        node = self.factor()
        while (token := self.peek()) is not None:
            if token[0] == "op" and token[1] in "*/":
                self.take()
                node = G.Node("bin", op=token[1], args=(node, self.factor()))
            elif token[0] in ("value", "open", "bar", "func", "extreme"):
                if token[0] == "bar" and self.in_bar:
                    return node
                node = G.Node("bin", op="*", args=(node, self.factor()))
            else:
                return node
        return node

    in_bar = False

    def factor(self) -> G.Node:
        token = self.take()
        kind = token[0]
        if kind == "value":
            return self.powered(token[1], token[2])
        if kind == "open":
            saved, self.in_bar = self.in_bar, False
            inner = self.expression()
            self.in_bar = saved
            closing = self.take()
            assert closing[0] == "close" and closing[1] == _CLOSE[token[1]], closing
            return self.powered(inner, closing[2])
        if kind == "bar":
            saved, self.in_bar = self.in_bar, True
            inner = self.expression()
            self.in_bar = saved
            closing = self.take()
            assert closing[0] == "bar", closing
            return self.powered(G.Node("call", text="abs", args=(inner,)), closing[1])
        if kind == "func":
            return self.function(token[1])
        if kind == "extreme":
            opening = self.take()
            assert opening[0] == "open", opening
            args = [self.expression()]
            while self.peek() == ("comma",):
                self.take()
                args.append(self.expression())
            closing = self.take()
            assert closing[0] == "close", closing
            return self.powered(G.Node("call", text=token[1], args=tuple(args)), closing[2])
        raise AssertionError(f"no reading of {token}")

    def function(self, name: str) -> G.Node:
        following = self.peek()
        if following is not None and following[0] == "open":
            self.take()
            inner = self.expression()
            closing = self.take()
            assert closing[0] == "close", closing
            return self.powered(G.Node("call", text=name, args=(inner,)), closing[2])
        token = self.take()
        assert token[0] == "value", token
        return G.Node("call", text=name, args=(self.powered(token[1], token[2]),))

    @staticmethod
    def powered(base: G.Node, sup: G.Node | None) -> G.Node:
        if sup is None:
            return base
        if base.kind == "name" and base.text == "e":  # the same number as e**x, without pow's last bit
            return G.Node("call", text="exp", args=(sup,))
        return G.Node("bin", op="^", args=(base, sup))


def _name(element: ElementTree.Element) -> G.Node:
    """A symbol, with its subscript if it has one."""

    if _local(element) == "msub":
        base, sub = list(element)
        return G.Node("name", text=_symbol(base.text or "") + (sub.text or ""))
    return G.Node("name", text=_symbol(element.text or ""))


def _number(text: str) -> G.Node:
    # A sentence's full stop renders inside the numeral: 2. is <mn>2.</mn>.
    text = text.rstrip(".")
    return G.Node("num", text=text, value=float(text))


def _tokens(children: list[ElementTree.Element]) -> list[tuple]:
    """Each rendered element as what it means in the run, with a script on what it sits on."""

    out: list[tuple] = []
    for element in children:
        out.extend(_element_tokens(element, out))
    return out


def _element_tokens(element: ElementTree.Element, before: list[tuple]) -> list[tuple]:
    tag = _local(element)
    if tag in ("mtext", "mspace"):
        return []
    if tag == "mrow":
        return _mrow_tokens(element)
    if tag == "mstyle":
        return _tokens(list(element))
    if tag == "mn":
        return _digits(element.text or "", None, before)
    if tag == "msqrt":
        body = list(element)
        return [("value", G.Node("call", text="sqrt", args=(_meaning(body),)), None)]
    if tag == "mfrac":
        top, bottom = list(element)
        return [("value", G.Node("bin", op="/", args=(_meaning([top]), _meaning([bottom]))), None)]
    if tag == "mi":
        text = element.text or ""
        if text in _FUNCTIONS:
            return [("func", _FUNCTIONS[text])]
        if text in ("min", "max"):
            return [("extreme", text)]
        if text == "/":
            return [("op", "/")]
        if text == "∣":
            return [("bar", None)]
        return [("value", _name(element), None)]
    if tag == "mo":
        text = element.text or ""
        if text == _APPLY:
            return []
        if text in _OPS:
            return [("op", _OPS[text])]
        if text in _CLOSE:
            return [("open", text)]
        if text in _CLOSE.values():
            return [("close", text, None)]
        if text == "∣":
            return [("bar", None)]
        if text == ",":
            return [("comma",)]
        if text in _RELS:
            return [("rel", _RELS[text])]
        raise AssertionError(f"no reading of the operator {text!r}")
    if tag == "msup" or tag == "msub" or tag == "msubsup":
        return _scripted(element, tag, before)
    if tag == "mtable":
        return [("value", _table(element), None)]
    raise AssertionError(f"no reading of <{tag}>")


def _digits(text: str, sup: G.Node | None, before: list[tuple]) -> list[tuple]:
    # The page's numeral is the run: 1 then 2^x is 12^x. A rendered gap (an mtext) is never in this run.
    if before and before[-1][0] == "value" and before[-1][1].kind == "num" and before[-1][2] is None:
        joined = before.pop()[1].text + text
        return [("value", _number(joined), sup)]
    return [("value", _number(text), sup)]


def _mrow_tokens(element: ElementTree.Element) -> list[tuple]:
    children = list(element)
    if children and _local(children[0]) == "mo" and children[0].get("fence") == "true":
        opening = children[0].text or ""
        if len(children) == 2 and _local(children[1]) == "mtable":  # a cases row group, {'s only side
            return [("value", _table(children[1]), None)]
        closing = children[-1].text or ""
        inner = _tokens(children[1:-1])
        if opening == "∣":
            return [("bar", None), *inner, ("bar", None)]
        return [("open", opening), *inner, ("close", closing, None)]
    if children and all(_local(child) == "mi" and child.get("mathvariant") == "normal" for child in children):
        word = "".join(child.text or "" for child in children)
        if word in _FUNCTIONS:
            return [("func", _FUNCTIONS[word])]
    return _tokens(children)


def _scripted(element: ElementTree.Element, tag: str, before: list[tuple]) -> list[tuple]:
    parts = list(element)
    base = parts[0]
    sup = _meaning([parts[-1]]) if tag in ("msup", "msubsup") else None
    sub = parts[1] if tag in ("msub", "msubsup") else None
    base_tag = _local(base)
    if base_tag == "mn":
        assert sub is None, "a numeral with a subscript"
        return _digits(base.text or "", sup, before)
    if base_tag == "mi":
        if sub is not None:
            return [("value", G.Node("name", text=_symbol(base.text or "") + (sub.text or "")), sup)]
        assert sup is not None
        if (base.text or "") == "∣":
            return [("bar", sup)]
        return [("value", _name(base), sup)]
    assert sub is None, "a subscript on a group"
    made = _element_tokens(base, before)
    last = made[-1]
    if last[0] == "close":
        return [*made[:-1], ("close", last[1], sup)]
    if last[0] == "bar":
        return [*made[:-1], ("bar", sup)]
    assert last[0] == "value", last
    return [*made[:-1], ("value", last[1], sup)]


def _strip_punctuation(tokens: list[tuple]) -> list[tuple]:
    while tokens and (tokens[-1] == ("comma",) or (tokens[-1][0] == "value" and tokens[-1][1].kind == "name" and tokens[-1][1].text == ".")):
        tokens = tokens[:-1]
    return tokens


def _cell_tokens(cell: ElementTree.Element) -> tuple[list[tuple], list[str]]:
    words: list[str] = []
    for found in cell.iter():
        if _local(found) == "mtext":
            words.append((found.text or "").strip())
    return _strip_punctuation(_tokens(list(cell))), words


def _table(table: ElementTree.Element) -> G.Node:
    args: list[G.Node] = []
    rows = list(table)
    last: G.Node | None = None
    for index, row in enumerate(rows):
        value_cell, condition_cell = list(row)
        value = _Meaning(_cell_tokens(value_cell)[0]).expression()
        tokens, words = _cell_tokens(condition_cell)
        if "otherwise" in words or index == len(rows) - 1:
            last = value
            break
        args += [_condition(tokens), value]
    assert last is not None
    if not args:
        return last
    return G.Node("piecewise", args=(*args, last))


def _condition(tokens: list[tuple]) -> G.Node:
    parts: list[list[tuple]] = [[]]
    ops: list[str] = []
    for token in tokens:
        if token[0] == "rel":
            ops.append(token[1])
            parts.append([])
        else:
            parts[-1].append(token)
    sides = [_Meaning(part).expression() for part in parts]
    compared = [G.Node("cmp", op=op, args=(left, right)) for op, left, right in zip(ops, sides, sides[1:])]
    return compared[0] if len(compared) == 1 else G.Node("and", args=tuple(compared))


def _meaning(children: list[ElementTree.Element]) -> G.Node:
    reader = _Meaning(_strip_punctuation(_tokens(children)))
    value = reader.expression()
    assert reader.peek() is None, f"left over: {reader.peek()}"
    return value


def right_hand_side(mathml: str) -> G.Node | None:
    """The meaning of what the page shows right of its one top-level ``=``; None when it has none."""

    root = ElementTree.fromstring(f'<mrow xmlns="http://www.w3.org/1998/Math/MathML">{mathml}</mrow>')
    children = list(root)
    equals = [index for index, element in enumerate(children) if _local(element) == "mo" and element.text == "="]
    if not equals:
        return None
    return _meaning(children[equals[-1] + 1:])


def same_value(left: G.Node, right: G.Node, points: list[Mapping[str, float]]) -> bool:
    """Both trees at each point, by the figure grammar's one evaluator."""

    for point in points:
        one, other = _value(left, point), _value(right, point)
        if one is None or other is None:
            if one is not other:
                return False
            continue
        if not math.isclose(one, other, rel_tol=1e-9, abs_tol=1e-12):
            return False
    return True


def _value(node: G.Node, point: Mapping[str, float]) -> float | None:
    try:
        value = G.evaluate(node, dict(point), {})
    except (ValueError, ArithmeticError):
        return None
    return value if isinstance(value, float) and math.isfinite(value) else None
