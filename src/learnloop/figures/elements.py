"""Reader RW5c: code-owned, element-scoped labels (spec_reader_rw5c_checked_labels_v1 §7, §8.2; G23d, G23e).

The owner's answer to Q1 is **option B**: on a figure with a checked element,
every label and every number in a label slot is code's. So no model string
reaches a label slot of a figure that carries the claim, by construction, and
no list of forbidden labels is needed.

* :func:`label_slots` is the one generic walk: it finds every ``Label``- and
  ``Text``-typed field of :class:`~learnloop.figures.spec.InteractiveFigureSpecV1`
  by type introspection, at any depth, for every panel kind. A new panel kind or
  field joins it by construction; a ``Label`` nobody mapped (:data:`LABEL_FIELDS`)
  fails G23d's test, and until it is mapped it is still rewritten like any other,
  drawn as a bare ``◇`` (so it can never carry a model string to a slot).
* :func:`element_map` gives each element a closed role: ``book`` (a bare
  reference to a checked definition with display agreement: the book's own
  left-hand side), ``derived`` (computed from a ``book`` element by a closed
  template, over the bounds the evaluator used, §7.2), ``symbol`` (a slider of a
  checked definition's symbol: the book's own token, carrying no claim) or
  ``ai`` (code's own rendering of the element's expression, in the model's voice).
* :func:`rewrite_spec` replaces every label in the delivered spec by its element
  id, references between labels included (``shade.series``,
  ``annotation.target``), so the renderer's binding by label still resolves and
  every slot is drawn from the elements. The stored spec is never changed.

The free text (``demonstrates``, assumptions, annotation text, prediction
prompts) stays where RW5a puts it, in the model's voice outside the panels
(§8.2, Q9): stripping numbers from it would be a deny-list.
"""

from __future__ import annotations

import json
import sys
import typing
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from learnloop.figures import grammar as G
from learnloop.figures import spec as S

#: The closed roles (§7.2; ``symbol`` is a slider's token: it names, and carries no claim).
ROLES = ("book", "derived", "symbol", "ai")
VOICES = ("source", "frame", "model")
#: Every ``Label`` field of the schema and what it is. A new one fails G23d until it is added here.
LABEL_FIELDS: dict[tuple[str, str], str] = {
    ("Parameter", "label"): "parameter", ("Series", "label"): "series", ("Marker", "label"): "marker",
    ("Shade", "label"): "shade", ("Shade", "series"): "reference", ("Highlight", "label"): "highlight",
    ("LinearMap2D", "label"): "panel", ("Readout", "label"): "readout", ("Heatmap2D", "label"): "panel",
    ("FieldHeatmap", "label"): "panel", ("VectorField2D", "label"): "panel", ("Trajectory2D", "label"): "panel",
    ("Iterate2D", "label"): "panel", ("Annotation", "target"): "reference",
}
#: Every ``Text`` field: the model's free text, outside the panels, in the model's voice.
TEXT_FIELDS: frozenset[tuple[str, str]] = frozenset({
    ("InteractiveFigureSpecV1", "demonstrates"), ("Assumption", "text"), ("Prediction", "prompt"),
    ("Annotation", "text"),
})


@dataclass(frozen=True)
class Slot:
    """One ``Label`` or ``Text`` field found by the walk."""

    path: tuple[Any, ...]
    kind: str  # label | text
    owner: str
    field: str
    value: str


def _field_kind(hint: Any) -> str | None:
    if hint is S.Label or hint == S.Label:
        return "label"
    if hint is S.Text or hint == S.Text:
        return "text"
    return None


def _hints(model: type[BaseModel]) -> dict[str, Any]:
    module = sys.modules.get(model.__module__)
    return typing.get_type_hints(model, globalns={**vars(S), **(vars(module) if module else {})}, include_extras=True)


def label_slots(model: BaseModel, path: tuple[Any, ...] = ()) -> Iterator[Slot]:
    """Every ``Label``- and ``Text``-typed field of ``model``, at any depth: one
    walk by type introspection, never a list of element kinds (G23d)."""

    hints = _hints(type(model))
    for name in type(model).model_fields:
        value = getattr(model, name)
        kind = _field_kind(hints.get(name))
        if kind is not None and isinstance(value, str):
            yield Slot((*path, name), kind, type(model).__name__, name, value)
            continue
        yield from _walk_value(value, (*path, name))


def _walk_value(value: Any, path: tuple[Any, ...]) -> Iterator[Slot]:
    if isinstance(value, BaseModel):
        yield from label_slots(value, path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _walk_value(item, (*path, index))


def schema_label_fields(root: type[BaseModel] = S.InteractiveFigureSpecV1) -> set[tuple[str, str, str]]:
    """``(model, field, kind)`` for every ``Label``/``Text`` field of the schema, from its types alone."""

    found: set[tuple[str, str, str]] = set()
    seen: set[type] = set()

    def visit(hint: Any) -> None:
        origin = typing.get_origin(hint)
        if origin is typing.Annotated:
            visit(typing.get_args(hint)[0])
            return
        if origin is not None:
            for arg in typing.get_args(hint):
                visit(arg)
            return
        if isinstance(hint, type) and issubclass(hint, BaseModel) and hint not in seen:
            seen.add(hint)
            hints = _hints(hint)
            for name in hint.model_fields:
                kind = _field_kind(hints.get(name))
                if kind is not None:
                    found.add((hint.__name__, name, kind))
                else:
                    visit(hints.get(name))

    visit(root)
    return found


def element_id(path: Sequence[Any]) -> str:
    """An element's id: where it is in the spec (a closed alphabet, never model text)."""

    return ".".join(str(part) for part in path)


# ---------------------------------------------------------------------------
# Code's own rendering of a grammar expression
# ---------------------------------------------------------------------------

_GREEK_TEX = frozenset({
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu",
    "xi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega", "Delta", "Theta", "Lambda", "Xi", "Pi",
    "Sigma", "Upsilon", "Psi", "Omega", "Gamma", "Phi",
})
_TEX_FUNCTIONS = {"exp": r"\exp", "log": r"\ln", "sin": r"\sin", "cos": r"\cos", "tan": r"\tan", "atan": r"\arctan",
                  "erf": r"\operatorname{erf}", "Phi": r"\Phi", "floor": r"\operatorname{floor}", "min": r"\min",
                  "max": r"\max"}
_TEX_OPS = {"<": "<", "<=": r"\le", ">": ">", ">=": r"\ge", "==": "=", "!=": r"\ne"}
_PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 4}


def symbol_tex(name: str, *, definition: bool = False) -> str:
    """A grammar name as a symbol. A definition's name is upright, so an
    AI-defined ``F`` can never read as the book's ``F``."""

    if definition:
        return r"\mathrm{" + name + "}"
    if name == "pi":
        return r"\pi"
    if name == "e":
        return r"\mathrm{e}"
    if name in _GREEK_TEX:
        return "\\" + name
    if len(name) == 1:
        return name
    head = name.rstrip("0123456789")
    if head in _GREEK_TEX or len(head) == 1:
        tail = name[len(head):]
        if tail:
            return ("\\" + head if head in _GREEK_TEX else head) + "_{" + tail + "}"
    return r"\mathrm{" + name + "}"


def _number_tex(text: str) -> str:
    mantissa, mark, exponent = text.lower().partition("e")
    if not mark:
        return mantissa
    return f"{mantissa or '1'} \\times 10^{{{int(exponent)}}}"


def to_tex(node: G.Node, definitions: Mapping[str, Any], _outer: int = 0) -> str:
    """The expression as TeX: code's words from a closed alphabet (names are
    ASCII, grammar.py's ``_NAME``), one frame per level of a capped tree."""

    kind = node.kind
    if kind == "num":
        return _number_tex(node.text)
    if kind == "name":
        return symbol_tex(node.text, definition=node.text in definitions)
    if kind == "neg":
        inner = "-" + to_tex(node.args[0], definitions, 3)
        return f"({inner})" if _outer > 1 else inner
    if kind == "bin":
        op = node.op
        left, right = node.args
        level = _PRECEDENCE[op]
        if op == "/":
            text = r"\frac{" + to_tex(left, definitions) + "}{" + to_tex(right, definitions) + "}"
            return text
        if op == "^":
            text = to_tex(left, definitions, 5) + "^{" + to_tex(right, definitions) + "}"
        elif op == "*":
            text = to_tex(left, definitions, level) + r" \cdot " + to_tex(right, definitions, level + 1)
        else:
            text = to_tex(left, definitions, level) + f" {op} " + to_tex(right, definitions, level + 1)
        return f"\\left({text}\\right)" if level < _outer else text
    if kind == "call":
        args = ", ".join(to_tex(child, definitions) for child in node.args)
        if node.text == "sqrt":
            return r"\sqrt{" + args + "}"
        if node.text == "abs":
            return r"\left|" + args + r"\right|"
        return _TEX_FUNCTIONS[node.text] + r"\left(" + args + r"\right)"
    if kind == "piecewise":
        args = node.args
        rows = [to_tex(args[i + 1], definitions) + " & " + to_tex(args[i], definitions)
                for i in range(0, len(args) - 1, 2)]
        rows.append(to_tex(args[-1], definitions) + r" & \text{otherwise}")
        return r"\begin{cases} " + r" \\ ".join(rows) + r" \end{cases}"
    if kind == "cmp":
        return to_tex(node.args[0], definitions) + f" {_TEX_OPS[node.op]} " + to_tex(node.args[1], definitions)
    if kind in ("and", "or"):
        joiner = r" \text{ and } " if kind == "and" else r" \text{ or } "
        return joiner.join(to_tex(child, definitions) for child in node.args)
    if kind in ("integral", "sum"):
        body, lower, upper = node.args
        variable = symbol_tex(node.text)
        if kind == "integral":
            return (r"\int_{" + to_tex(lower, definitions) + "}^{" + to_tex(upper, definitions) + "} "
                    + to_tex(body, definitions, 2) + r"\,d" + variable)
        return (r"\sum_{" + variable + "=" + to_tex(lower, definitions) + "}^{" + to_tex(upper, definitions) + "} "
                + to_tex(body, definitions, 2))
    raise G.GrammarError(f"cannot render a {kind!r} node")


def to_plain(node: G.Node, _outer: int = 0) -> str:
    """The expression as plain text for ``aria-label``s and SVG text: the
    grammar's own infix, rebuilt from the tree."""

    kind = node.kind
    if kind == "num":
        return node.text
    if kind == "name":
        return node.text
    if kind == "neg":
        inner = "-" + to_plain(node.args[0], 3)
        return f"({inner})" if _outer > 1 else inner
    if kind == "bin":
        level = _PRECEDENCE[node.op]
        spaced = f" {node.op} " if node.op in "+-" else node.op
        text = to_plain(node.args[0], level) + spaced + to_plain(node.args[1], level + 1)
        return f"({text})" if level < _outer else text
    if kind == "call":
        return node.text + "(" + ", ".join(to_plain(child) for child in node.args) + ")"
    if kind == "piecewise":
        args = node.args
        rows = [f"{to_plain(args[i + 1])} if {to_plain(args[i])}" for i in range(0, len(args) - 1, 2)]
        return "; ".join([*rows, f"{to_plain(args[-1])} otherwise"])
    if kind == "cmp":
        return f"{to_plain(node.args[0])} {node.op} {to_plain(node.args[1])}"
    if kind in ("and", "or"):
        return f" {kind} ".join(to_plain(child) for child in node.args)
    if kind in ("integral", "sum"):
        body, lower, upper = node.args
        return f"{kind}({to_plain(body)}, {node.text}, {to_plain(lower)}, {to_plain(upper)})"
    raise G.GrammarError(f"cannot render a {kind!r} node")


def detex(latex: str) -> str:
    """A left-hand side as plain text for ``aria-label``s (source text, its markup dropped)."""

    return " ".join(str(latex).replace("\\left", "").replace("\\right", "").replace("\\", "")
                    .replace("{", "").replace("}", "").split())


# ---------------------------------------------------------------------------
# The element map
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BookLabel:
    """A checked definition's candidate: the book's own words for its label."""

    lhs: str
    latex: str
    variable: str | None
    tokens: Mapping[str, str]
    extraction_id: str
    span_id: str
    page: int | None


def _element(path: Sequence[Any], role: str, tex: str, plain: str, voice: str, **extra: Any) -> dict[str, Any]:
    return {"id": element_id(path), "path": element_id(path), "role": role, "tex": tex, "plain": plain,
            "voice": voice, **extra}


def _source(label: BookLabel) -> dict[str, Any]:
    return {"extraction_id": label.extraction_id, "span_id": label.span_id, "page": label.page}


def _bare(node: G.Node | None, definitions: Mapping[str, Any]) -> str | None:
    return node.text if node is not None and node.kind == "name" and node.text in definitions else None


def _curve(path: Sequence[Any], node: G.Node | None, axis: str | None, compiled: S.CompiledFigure,
           book: Mapping[str, BookLabel], book_elements: Mapping[str, str]) -> dict[str, Any]:
    """A series or a readout's plain value: ``book``, else code's rendering in the model's voice."""

    definitions = compiled.definitions
    name = _bare(node, definitions)
    identity = element_id(path)
    if name is not None and book_elements.get(identity) == name:
        label = book[name]
        return _element(path, "book", label.lhs, detex(label.lhs), "source", definition=name, source=_source(label),
                        equation=label.latex)
    if name is not None:
        # AI-defined, rendered as its grammar name behind the model's glyph:
        # never readable as the book's own F.
        call = f"({symbol_tex(axis)})" if axis else ""
        return _element(path, "ai", symbol_tex(name, definition=True) + call, name + (f"({axis})" if axis else ""),
                        "model", definition=name, tag="ai_defined")
    if node is None:
        return _element(path, "ai", "", "", "model")
    return _element(path, "ai", to_tex(node, definitions), to_plain(node), "model")


def _template(path: Sequence[Any], kind: str, panel: int, index: int, *, body_tex: str, body_plain: str,
              variable: str, role: str, voice: str, compiled: S.CompiledFigure, env: Mapping[str, float],
              **extra: Any) -> dict[str, Any]:
    """A shade, a highlight or a bound readout: its words state the bounds the
    evaluator used (F2) and name them losslessly (F9). The Reader rebuilds them
    from the same evaluation at every slider change; ``tex`` is the defaults'."""

    from learnloop.figures.display_format import js_string

    bounds = S.derived_bounds(compiled, panel, kind, index, env)
    template = {"kind": kind, "panel": panel, "index": index, "body_tex": body_tex, "body_plain": body_plain,
                "variable": variable}
    tex, plain = template_words(template, bounds, js_string)
    return _element(path, role, tex, plain, voice, template=template, **extra)


def template_words(template: Mapping[str, Any], bounds: Mapping[str, Any], number: Any) -> tuple[str, str]:
    """The closed derived-label templates (§7.2), in TeX and in plain text.
    Twin of ``derivedWords`` in the Reader (G22's extension pins the bounds)."""

    kind = str(template["kind"])
    body_tex, body_plain, variable = str(template["body_tex"]), str(template["body_plain"]), str(template["variable"])
    low, high = bounds.get("from"), bounds.get("to")
    if low is None or high is None:
        return body_tex, body_plain
    if bounds.get("integers"):
        first, last = bounds["integers"]
        if last < first:
            return body_tex, f"{body_plain}: no terms in this range"
        low_text, high_text = str(first), str(last)
    else:
        low_text, high_text = number(low), number(high)
    limited = " · limited to the plotted range" if bounds.get("clipped") else ""
    if kind == "shade":
        return (r"\text{area under } " + body_tex + rf" \text{{ from }} {low_text} \text{{ to }} {high_text}",
                f"area under {body_plain} from {low_text} to {high_text}{limited}")
    symbol = symbol_tex(variable)
    if kind == "integral":
        return (rf"\int_{{{low_text}}}^{{{high_text}}} " + body_tex + rf"\,d{symbol}",
                f"integral from {low_text} to {high_text} of {body_plain} d{variable}")
    return (rf"\sum_{{{symbol}={low_text}}}^{{{high_text}}} " + body_tex,
            f"sum for {variable} from {low_text} to {high_text} of {body_plain}{limited}")


def _panel_tex(panel: S.CompiledPanel, definitions: Mapping[str, Any]) -> tuple[str, str]:
    """A non-curve panel's own expression, for a label its author gave it."""

    nodes = panel.nodes
    if panel.kind == "linear_map_2d":
        rows = nodes["matrix"]
        tex = r"\begin{pmatrix} " + r" \\ ".join(
            " & ".join(to_tex(cell, definitions) for cell in row) for row in rows) + r" \end{pmatrix}"
        return tex, "[" + "; ".join(", ".join(to_plain(cell) for cell in row) for row in rows) + "]"
    if panel.kind == "heatmap_2d":
        return to_tex(nodes["expr"], definitions), to_plain(nodes["expr"])
    if panel.kind == "vector_field_2d":
        return (r"\left(" + to_tex(nodes["u"], definitions) + ", " + to_tex(nodes["v"], definitions) + r"\right)",
                f"({to_plain(nodes['u'])}, {to_plain(nodes['v'])})")
    if panel.kind == "trajectory_2d":
        return (r"\left(" + to_tex(nodes["dx"], definitions) + ", " + to_tex(nodes["dy"], definitions) + r"\right)",
                f"({to_plain(nodes['dx'])}, {to_plain(nodes['dy'])})")
    return (r"\left(" + to_tex(nodes["fx"], definitions) + ", " + to_tex(nodes["fy"], definitions) + r"\right)",
            f"({to_plain(nodes['fx'])}, {to_plain(nodes['fy'])})")


def element_map(compiled: S.CompiledFigure, book: Mapping[str, BookLabel],
                book_elements: Mapping[str, str]) -> list[dict[str, Any]]:
    """Every label-carrying element and its role (§7.2). ``book`` is the checked
    definitions' labels; ``book_elements`` the element ids with display
    agreement and the definition each draws. No model text enters the result."""

    definitions = compiled.definitions
    env = compiled.defaults
    elements: dict[str, dict[str, Any]] = {}
    # Parameters: the book's own token when a checked definition reads it.
    book_tokens: dict[str, str] = {}
    for name in set(book_elements.values()):
        book_tokens.update({symbol: token for symbol, token in book[name].tokens.items()})
    for index, parameter in enumerate(compiled.parameters):
        path = ("parameters", index)
        token = book_tokens.get(parameter.name)
        if token is not None:
            elements[element_id(path)] = _element(path, "symbol", token, detex(token), "source")
        else:
            elements[element_id(path)] = _element(path, "ai", symbol_tex(parameter.name), parameter.name, "model")
    for panel_index, panel in enumerate(compiled.panels):
        base: tuple[Any, ...] = ("panels", panel_index)
        model = panel.model
        if panel.kind in ("function_plot", "pmf_bars"):
            axis = model.x.var if panel.kind == "function_plot" else model.k.var
            curves: list[dict[str, Any]] = []
            for index, node in enumerate(panel.nodes["series"]):
                entry = _curve((*base, "series", index), node, axis, compiled, book, book_elements)
                curves.append(entry)
                elements[entry["id"]] = entry
            if panel.kind == "function_plot":
                for index, node in enumerate(panel.nodes["markers"]):
                    path = (*base, "markers", index)
                    tex = symbol_tex(axis) + " = " + (to_tex(node, definitions) if node is not None else "")
                    plain = axis + " = " + (to_plain(node) if node is not None else "")
                    elements[element_id(path)] = _element(path, "ai", tex, plain, "model")
                labels = [series.label for series in model.series]
                for index, shade in enumerate(model.shade):
                    parent = curves[labels.index(shade.series)]
                    path = (*base, "shade", index)
                    derived = parent["role"] == "book"
                    elements[element_id(path)] = _template(
                        path, "shade", panel_index, index, body_tex=parent["tex"], body_plain=parent["plain"],
                        variable=axis, role="derived" if derived else "ai", voice="frame" if derived else "model",
                        compiled=compiled, env=env, **({"definition": parent["definition"]} if derived else {}))
            elif model.highlight is not None:
                # The highlight's readout sums the first series (spec.highlight_value).
                parent = curves[0]
                path = (*base, "highlight")
                derived = parent["role"] == "book"
                elements[element_id(path)] = _template(
                    path, "highlight", panel_index, 0, body_tex=parent["tex"], body_plain=parent["plain"],
                    variable=axis, role="derived" if derived else "ai", voice="frame" if derived else "model",
                    compiled=compiled, env=env, **({"definition": parent["definition"]} if derived else {}))
        elif panel.kind == "readout":
            node = panel.nodes["expr"]
            path = (*base,)
            bound = node if node is not None and node.kind in ("integral", "sum") else None
            if bound is not None:
                body, _low, _high = bound.args
                name = _bare(body, definitions)
                carries = name is not None and name in set(book_elements.values()) and name in book \
                    and book[name].variable == bound.text
                if carries:
                    label = book[str(name)]
                    body_tex, body_plain = label.lhs, detex(label.lhs)
                else:
                    body_tex, body_plain = to_tex(body, definitions), to_plain(body)
                elements[element_id(path)] = _template(
                    path, bound.kind, panel_index, 0, body_tex=body_tex, body_plain=body_plain, variable=bound.text,
                    role="derived" if carries else "ai", voice="frame" if carries else "model", compiled=compiled,
                    env=env, **({"definition": name} if carries else {}))
            else:
                entry = _curve(path, node, None, compiled, book, book_elements)
                elements[entry["id"]] = entry
        else:
            tex, plain = _panel_tex(panel, definitions)
            elements[element_id(base)] = _element(base, "ai", tex, plain, "model")
            if panel.kind == "vector_field_2d" and model.heatmap is not None:
                path = (*base, "heatmap")
                node = panel.nodes["heatmap"]
                elements[element_id(path)] = _element(path, "ai", to_tex(node, definitions), to_plain(node), "model")
    return list(elements.values())


def _slot_element_path(slot: Slot) -> tuple[Any, ...]:
    """The element a label slot names: its owner's path (a readout's and a
    panel's own ``label`` name the panel)."""

    return slot.path[:-1]


def rewrite_spec(spec_json: str, compiled: S.CompiledFigure) -> tuple[str, dict[str, str]]:
    """The delivered spec with every label replaced by its element id, references
    too (§7.4, by construction: the walk reaches every ``Label``), and the map
    from each model label a reference may name to its id. An empty optional label
    stays empty (nothing is drawn). The stored spec is never changed."""

    data = json.loads(spec_json)
    # Series and shade labels, per panel (a reference binds within its panel;
    # an annotation's target may name any element).
    by_label: dict[str, str] = {}
    slots = list(label_slots(compiled.spec))
    for slot in slots:
        if slot.kind != "label" or LABEL_FIELDS.get((slot.owner, slot.field)) == "reference":
            continue
        by_label.setdefault(slot.value, element_id(_slot_element_path(slot)))
    for slot in slots:
        # An area prediction answers with a shade's label: a shade's own id wins over a series named alike.
        if slot.owner == "Shade" and slot.field == "label":
            by_label[slot.value] = element_id(_slot_element_path(slot))
    for slot in slots:
        if slot.kind != "label":
            continue
        role = LABEL_FIELDS.get((slot.owner, slot.field))
        identity = element_id(_slot_element_path(slot))
        if role == "reference":
            if slot.field == "series":
                # Within its panel, by the panel's own series.
                panel = slot.path[1]
                labels = [series.label for series in compiled.panels[panel].model.series]
                replacement = element_id(("panels", panel, "series", labels.index(slot.value)))
            else:
                replacement = by_label.get(slot.value, "")
        elif slot.value == "" and role == "panel":
            replacement = ""  # an optional panel label its author left empty: nothing is drawn
        else:
            replacement = identity
        _assign(data, slot.path, replacement)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False), by_label


def _assign(data: Any, path: Sequence[Any], value: str) -> None:
    current = data
    for part in path[:-1]:
        current = current[part]
    key = path[-1]
    # The dumped spec's keys are the schema's aliases (no Label field has one today).
    current[key] = value


__all__ = [
    "BookLabel",
    "LABEL_FIELDS",
    "ROLES",
    "Slot",
    "TEXT_FIELDS",
    "VOICES",
    "detex",
    "element_id",
    "element_map",
    "label_slots",
    "rewrite_spec",
    "schema_label_fields",
    "symbol_tex",
    "template_words",
    "to_plain",
    "to_tex",
]
