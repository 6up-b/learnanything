"""Reader RW5c P1: step 3, "matches the book's equation (checked)" (spec_reader_rw5c_checked_labels_v1 §4-§6, §10).

After steps 1-2 (:mod:`.verify`, unchanged), with ``figures.checked_labels_enabled``
on, code reads the book's equations (:mod:`.book_math`) from the healthy,
non-withheld blocks of the figure's own input spans, and a fixed harness in the
PF-b sandbox (:mod:`.source_check_harness`) compares each definition drawn by
bare reference with them, exactly, on the same domain, runs negative controls and
checks the displayed values to the digits shown. No model writes any part of this:
the author's quote can only point at a candidate, and the check makes no model call.

3a candidates (:func:`read_candidates`): every readable equation in the input spans.
3b binding (:func:`binding_problem`): drawn by bare reference, identical names,
exact literals and conditions, no construct sympy cannot reproduce.
3c-3d the sandbox and the outcome per definition (§6.6's precedence).
3e roles and labels (:mod:`.elements`, option B). 3f one ``figure_source_checks``
row and its ``judgment_ledger`` verdict in one transaction (:func:`record`).

Everything is a deterministic function of the stored spec, the source text, the
block-health analyzer, the reader version and the harness digest, so a stored
figure is rechecked by the same code with no model client (:func:`recheck`).

"Checked" is a property of the figure's content, never evidence, mastery,
certification or help weight: nothing that writes those reads this module
(``evidence-never-reads-figures``; G23h).
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.authoring import pf_sandbox
from learnloop.content.sources import block_health as BH
from learnloop.db.connection import connect
from learnloop.db.stores import figures as store
from learnloop.db.stores.judgments import append_judgment
from learnloop.figure_admission import FiguresChanged, FiguresGate, checked_labels_enabled, figures_enabled
from learnloop.figures import book_math as BM
from learnloop.figures import display_format as DF
from learnloop.figures import elements as E
from learnloop.figures import grammar as G
from learnloop.figures import katex_tree as KT
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.ids import new_ulid
from learnloop.reader.source_render_views import sanitize_source_text

#: The rules a check ran under (the reader's table, the harness, the display
#: format). Bumping it rechecks stored figures, by code, at no paid cost (§10.4).
#: 2: the reader refuses forms the page shows otherwise (\sqrt16 x and its class),
#: so a "checked" stored under 1 is not delivered until code has read it again.
#: 3: the reader reads KaTeX's own tree (\def and e^x^2 and their class).
#: 4: the page's own markdown finds the segments (a reference definition, a link title,
#: a code span could certify an equation the page never shows; and their class).
CERTIFICATION_VERSION = 4
LEDGER_TASK = "figure_source_check"
CHECKED, DIFFERS, UNDECIDED, NOT_CHECKABLE = "checked", "differs", "undecided", "not_checkable"
OUTCOMES = (CHECKED, DIFFERS, UNDECIDED, NOT_CHECKABLE)
#: The reasons a definition or a figure is not ``checked``: closed keys the
#: Reader words itself (``SOURCE_CHECK_COPY``); the report counts them (§12).
REASONS = (*BM.REASONS, "block_health", "block_withheld", "control_accepted", "control_inconclusive", "differs",
           "display_disagrees", "domain", "inexact_condition", "inexact_construct", "names", "no_book_source",
           "no_proof", "no_readable_candidate", "not_bare", "parametric_breakpoint", "quote_across_blocks",
           "sandbox_failed", "sandbox_unavailable", "timeout")
#: RW2b's runtime bounds (workbench/symbolic.py): not judgments (spec §15).
SANDBOX_LIMITS = pf_sandbox.SandboxLimits(cpu_seconds=20, wall_seconds=30)
PER_CHECK_SECONDS = 5
#: What a rejected figure says, in the frame's words (§6.6, Q4).
REJECTED_REASON = "its definition differs from the book's equation it quotes"
_UNICODE_MATH = re.compile("[\U0001d400-\U0001d7ff]")
_RESULTS = ("equal", "different", "undecided")


def _harness_files() -> tuple[str, str]:
    here = Path(__file__).parent
    return ((here / "source_check_harness.py").read_text(encoding="utf-8"),
            Path(DF.__file__).read_text(encoding="utf-8"))


HARNESS, _DISPLAY_FORMAT = _harness_files()
HARNESS_SHA256 = hashlib.sha256((HARNESS + "\n" + _DISPLAY_FORMAT).encode("utf-8")).hexdigest()


def enabled(vault: Any) -> bool:
    """``figures.checked_labels_enabled`` under ``figures.enabled``, as configured now."""

    return checked_labels_enabled(vault)


def recheck_key(vault: Any) -> tuple[Any, ...]:
    """A recheck's gate key (§6.7): it makes no model request, but stops at any switch change."""

    return (str(vault.root), figures_enabled(vault), checked_labels_enabled(vault))


@dataclass(frozen=True)
class Candidate:
    """One readable equation of an input span."""

    extraction_id: str
    span_id: str
    #: How a source claim names this span (``extraction:span`` for a retrieved passage).
    claim_key: str
    page: int | None
    start: int
    end: int
    block_text: str
    relation: BM.Relation
    health: Mapping[str, Any]

    @property
    def key(self) -> str:
        return f"{self.extraction_id}:{self.span_id}:{self.start}"


@dataclass
class Check:
    """The result of one run of steps 3a-3e."""

    outcome: str
    definitions: list[dict[str, Any]] = field(default_factory=list)
    elements: list[dict[str, Any]] = field(default_factory=list)
    reasons: dict[str, int] = field(default_factory=dict)
    #: What the second attempt is told when a stated claim differs (code text).
    problems: list[str] = field(default_factory=list)
    input_hash: str = ""
    sympy_version: str = ""
    duration_ms: int = 0
    rationale: str = ""

    @property
    def book_elements(self) -> list[dict[str, Any]]:
        return [element for element in self.elements if element.get("role") == "book"]


# ---------------------------------------------------------------------------
# 3a: the candidates (§5)
# ---------------------------------------------------------------------------

def input_spans(row: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """``(extraction_id, span_id, claim_key)`` of a figure's own input spans: the
    spans that were sent to the author, as stored for every held-out recheck."""

    keys = [tuple(str(part) for part in key) for key in row.get("input_span_keys") or () if len(key) == 2]
    if keys:
        return [(key[0], key[1], f"{key[0]}:{key[1]}") for key in keys]
    extraction = row.get("extraction_id")
    if not extraction:
        return []
    return [(str(extraction), str(span), str(span)) for span in (row.get("input_span_ids") or ())]


def _health(repository: Any, extraction_id: str, block: Any, ir: Any, *, persist: bool) -> dict[str, Any]:
    """The block's health as ``reader.block_health`` computes it: stored when
    computed, never assumed ok (``unknown`` is not ``ok``, §5.2)."""

    found = repository.block_health(extraction_id, block.span_id)
    if found:
        return {"analyzer_version": found.get("analyzer_version"), "status": found.get("status")}
    page_health = None
    if block.page is not None:
        page_health = next((page for page in ir.health.pages if page.page == block.page), None)
    computed = BH.analyze_block_health(block, page_health)
    if persist and not getattr(repository, "_read_only", False):
        repository.upsert_block_health({**computed, "extraction_id": extraction_id})
    return {"analyzer_version": computed.get("analyzer_version"), "status": computed.get("status")}


def read_candidates(vault: Any, repository: Any, spans: Sequence[tuple[str, str, str]], *, persist: bool = True
                    ) -> tuple[list[Candidate], dict[str, int]]:
    """The readable equations of the input spans in reading order, and how many
    were refused by each reason."""

    from learnloop.content.sources.exam_material import exam_material

    material = exam_material(vault, repository)
    reasons: dict[str, int] = {}
    placed: list[tuple[int, int, Candidate]] = []
    documents: dict[str, Any] = {}
    orders: dict[str, int] = {}

    def refuse(reason: str) -> None:
        reasons[reason] = reasons.get(reason, 0) + 1

    # One loaded KaTeX for the whole check; it opens only if a segment needs reading.
    with KT.Trees() as trees:
        for extraction_id, span_id, claim_key in spans:
            if extraction_id not in documents:
                documents[extraction_id] = repository.load_document_ir(extraction_id)
                orders[extraction_id] = len(orders)
            ir = documents[extraction_id]
            block = ir.block_by_span(span_id) if ir is not None else None
            if block is None:
                continue
            if material.covers(extraction_id, span_id):
                refuse("block_withheld")
                continue
            text = block.text or ""
            # The page gets the sanitized text (source_render_views); a block that changes it is refused below.
            shown, sanitized = sanitize_source_text(text)
            try:
                found = BM.segments(shown, trees=trees)
            except BM.Unreadable as refused:
                refuse(refused.reason)
                continue
            if not found:
                if _UNICODE_MATH.search(text):
                    refuse("unicode_math")
                continue
            health = _health(repository, extraction_id, block, ir, persist=persist)
            if health.get("status") != "ok":
                refuse("block_health")
                continue
            if sanitized:
                refuse("block_health")
                continue
            position = next((index for index, item in enumerate(ir.blocks) if item.span_id == span_id), 0)
            for segment in found:
                try:
                    relation = BM.read_relation(segment.latex, display=segment.display, trees=trees)
                except BM.Unreadable as refused:
                    refuse(refused.reason)
                    continue
                placed.append((orders[extraction_id], position, Candidate(
                    extraction_id, span_id, claim_key, block.page, segment.start, segment.end, text, relation, health)))
    placed.sort(key=lambda item: (item[0], item[1], item[2].start))
    return [item[2] for item in placed], reasons


# ---------------------------------------------------------------------------
# 3b: the binding (§6.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Drawn:
    """A bare reference to a definition: an element that draws it, whole."""

    element_id: str
    panel: int
    kind: str  # function_plot | pmf_bars | readout
    variable: str | None
    format: str = "number"


def expand(node: G.Node, definitions: Mapping[str, G.Node], _seen: tuple[str, ...] = ()) -> G.Node:
    """``node`` with definitions written out (the compiler caps the result)."""

    if node.kind == "name" and node.text in definitions and node.text not in _seen:
        return expand(definitions[node.text], definitions, (*_seen, node.text))
    if not node.args:
        return node
    return G.Node(node.kind, text=node.text, op=node.op, value=node.value,
                  args=tuple(expand(child, definitions, _seen) for child in node.args))


def drawn_by_reference(compiled: S.CompiledFigure) -> dict[str, list[Drawn]]:
    """Each definition's elements that draw it by bare reference: the expression
    is exactly ``Node(kind="name", text=d)``. An inline copy is not one."""

    definitions = compiled.definitions
    found: dict[str, list[Drawn]] = {}
    parameters = {parameter.name for parameter in compiled.parameters}
    for panel_index, panel in enumerate(compiled.panels):
        if panel.kind in ("function_plot", "pmf_bars"):
            axis = panel.model.x.var if panel.kind == "function_plot" else panel.model.k.var
            for index, node in enumerate(panel.nodes["series"]):
                if node is None or node.kind != "name" or node.text not in definitions:
                    continue
                free = S.expanded_free(definitions[node.text], definitions) - parameters
                if free == {axis}:
                    found.setdefault(node.text, []).append(Drawn(
                        E.element_id(("panels", panel_index, "series", index)), panel_index, panel.kind, axis))
        elif panel.kind == "readout":
            node = panel.nodes["expr"]
            if node is None or node.kind != "name" or node.text not in definitions:
                continue
            if not S.expanded_free(definitions[node.text], definitions) - parameters:
                found.setdefault(node.text, []).append(Drawn(
                    E.element_id(("panels", panel_index)), panel_index, "readout", None, panel.model.format))
    return found


def _bare_exact(side: G.Node) -> bool:
    literal = side.args[0] if side.kind == "neg" and side.args else side
    return literal.kind == "num" and BM.binary64_exact(literal.text)


def _bare_name(side: G.Node) -> bool:
    return side.kind == "name" and side.text not in G.CONSTANTS


def binding_problem(node: G.Node) -> str | None:
    """Why a definition's expansion cannot be checked (§6.1), as a closed reason."""

    for current in G.walk(node):
        if current.kind in ("integral", "sum"):
            return "inexact_construct"
        if current.kind == "call" and current.text == "floor":
            return "inexact_construct"
        if current.kind == "cmp" and current.op in ("==", "!="):
            return "inexact_construct"
    for current in G.walk(node):
        if current.kind == "num" and not BM.binary64_exact(current.text):
            return "inexact_literal"
    for current in G.walk(node):
        if current.kind == "cmp":
            left, right = current.args
            exact = (_bare_name(left) and (_bare_exact(right) or _bare_name(right))) or (
                _bare_name(right) and _bare_exact(left))
            if not exact:
                return "inexact_condition"
    return None


# ---------------------------------------------------------------------------
# 3c: the payload (ASTs, never text)
# ---------------------------------------------------------------------------

def to_json(node: G.Node) -> dict[str, Any]:
    out: dict[str, Any] = {"k": node.kind}
    if node.text:
        out["t"] = node.text
    if node.op:
        out["o"] = node.op
    if node.args:
        out["a"] = [to_json(child) for child in node.args]
    return out


def _substitute(node: G.Node, name: str, replacement: G.Node) -> G.Node:
    if node.kind == "name" and node.text == name:
        return replacement
    if not node.args:
        return node
    return G.Node(node.kind, text=node.text, op=node.op, value=node.value,
                  args=tuple(_substitute(child, name, replacement) for child in node.args))


def controls(node: G.Node, symbols: Sequence[str]) -> list[G.Node]:
    """§6.5: ``d + 1``, ``2·d`` and ``d`` with each free symbol ``s`` replaced by
    ``s + 1``: exact transformations, structural, tuning nothing."""

    one = G.Node("num", text="1", value=1.0)
    two = G.Node("num", text="2", value=2.0)
    built = [G.Node("bin", op="+", args=(node, one)), G.Node("bin", op="*", args=(two, node))]
    for symbol in symbols:
        built.append(_substitute(node, symbol, G.Node("bin", op="+", args=(G.Node("name", text=symbol), one))))
    return built


def _exact(value: float) -> str:
    fraction = Fraction(float(value))
    return f"{fraction.numerator}/{fraction.denominator}"


def _assumptions(compiled: S.CompiledFigure, names: set[str], variable: str | None) -> dict[str, str]:
    """§6.3 step 1: sign assumptions the sliders' ranges imply, so a proof holds across them."""

    signs = {}
    by_name = {parameter.name: parameter for parameter in compiled.parameters}
    for name in names:
        parameter = by_name.get(name)
        if parameter is None or name == variable:
            signs[name] = "real"
        elif parameter.min > 0:
            signs[name] = "positive"
        elif parameter.min >= 0:
            signs[name] = "nonnegative"
        else:
            signs[name] = "real"
    return signs


def _projected_grid(compiled: S.CompiledFigure, names: set[str]) -> list[dict[str, float]]:
    """The parameter grid on the parameters a definition reads (the others cannot move it)."""

    seen: dict[tuple[tuple[str, float], ...], dict[str, float]] = {}
    for point in V.parameter_grid(compiled):
        key = tuple(sorted((name, value) for name, value in point.items() if name in names))
        seen.setdefault(key, dict(key))
    return list(seen.values())


def _samples(compiled: S.CompiledFigure, drawn: Drawn) -> list[float]:
    model = compiled.panels[drawn.panel].model
    if drawn.kind == "function_plot":
        return S.plot_xs(model.x)
    if drawn.kind == "pmf_bars":
        return S.bar_ks(model.k)
    return []


def _display_payload(compiled: S.CompiledFigure, name: str, drawn: Drawn, grid: Sequence[Mapping[str, float]]
                     ) -> dict[str, Any]:
    """What the figure shows at every displayed sample of every grid point: the
    evaluator's double formatted by the twin of ``formatValue`` (§6.4)."""

    node = G.Node("name", text=name)
    defs = compiled.definitions
    points = []
    samples = _samples(compiled, drawn)
    for point in grid:
        env = {**compiled.defaults, **point}
        shown = []
        if drawn.variable is None:
            value = G.evaluate(node, env, defs)
            shown.append({"shown": DF.format_value(S._num(value), drawn.format)})
        else:
            for sample in samples:
                env[drawn.variable] = sample
                value = G.evaluate(node, env, defs)
                shown.append({"at": _exact(sample), "shown": DF.format_value(S._num(value), drawn.format)})
        points.append({"params": {key: _exact(value) for key, value in point.items()}, "samples": shown})
    return {"id": drawn.element_id, "variable": drawn.variable, "format": drawn.format, "grid": points}


# ---------------------------------------------------------------------------
# 3d: the outcomes (§6.6)
# ---------------------------------------------------------------------------

def _squashed_map(text: str) -> tuple[str, list[int]]:
    """``verify.quote_in``'s whitespace-collapsed text, with each character's place in ``text``."""

    out: list[str] = []
    places: list[int] = []
    pending = False
    for index, char in enumerate(text):
        if char.isspace():
            pending = bool(out)
            continue
        if pending:
            out.append(" ")
            places.append(index)
            pending = False
        out.append(char)
        places.append(index)
    return "".join(out), places


def quote_overlaps(quote: str, candidate: Candidate) -> bool:
    """Whether a quote ``quote_in`` verifies in this block overlaps this segment."""

    needle = " ".join(str(quote or "").split())
    text, places = _squashed_map(candidate.block_text)
    if not needle:
        return False
    start = text.find(needle)
    while start >= 0:
        low, high = places[start], places[start + len(needle) - 1]
        if low < candidate.end and high >= candidate.start:
            return True
        start = text.find(needle, start + 1)
    return False


def _point_words(value: Any) -> str:
    """An exact witness coordinate as its shortest decimal when it is one, else the exact fraction."""

    try:
        exact = Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return str(value)
    if Fraction(float(exact)) == exact:
        return DF.js_string(float(exact)) if exact.denominator > 1 << 20 or exact.denominator == 1 else str(exact)
    return str(exact)


def _witness_words(name: str, witness: Mapping[str, Any]) -> str:
    """The difference, in code's words, for the second attempt and the ledger (§6.6)."""

    at = ", ".join(f"{key} = {_point_words(value)}" for key, value in sorted((witness.get("at") or {}).items()))
    if witness.get("kind") == "domain":
        if witness.get("defined") == "figure":
            return f"your definition {name} has a value at {at}, where the quoted equation has none"
        return f"your definition {name} has no value at {at}, where the quoted equation has one"
    return f"your definition {name} differs from the quoted equation at {at}"


def _count(reasons: dict[str, int], reason: str, amount: int = 1) -> None:
    reasons[reason] = reasons.get(reason, 0) + amount


Sandbox = Callable[..., pf_sandbox.SandboxResult]


def _run_sandbox(payload: Mapping[str, Any], sandbox: Sandbox | None) -> pf_sandbox.SandboxResult:
    run = sandbox or pf_sandbox.run_sandboxed_python
    return run(HARNESS, payload, modules={"display_format": _DISPLAY_FORMAT}, limits=SANDBOX_LIMITS)


def check_figure(vault: Any, repository: Any, compiled: S.CompiledFigure, *, spans: Sequence[tuple[str, str, str]],
                 grounding: str | None, persist: bool = True, sandbox: Sandbox | None = None,
                 sandbox_ready: Callable[[], bool] | None = None) -> Check:
    """Steps 3a-3e on one compiled grammar spec. Never raises for what it cannot
    read or decide: each such thing is a closed reason, and never ``checked``."""

    started = time.monotonic()
    check = _check(vault, repository, compiled, spans=spans, grounding=grounding, persist=persist, sandbox=sandbox,
                   sandbox_ready=sandbox_ready)
    check.duration_ms = int((time.monotonic() - started) * 1000)
    return check


def _check(vault: Any, repository: Any, compiled: S.CompiledFigure, *, spans: Sequence[tuple[str, str, str]],
           grounding: str | None, persist: bool, sandbox: Sandbox | None,
           sandbox_ready: Callable[[], bool] | None) -> Check:
    reasons: dict[str, int] = {}
    if grounding == "none":
        return _finished(compiled, [], [], {"no_book_source": 1}, NOT_CHECKABLE, "")
    candidates, reasons = read_candidates(vault, repository, spans, persist=persist)
    ready = sandbox_ready() if sandbox_ready is not None else (sandbox is not None or pf_sandbox.sandbox_available())
    drawn = drawn_by_reference(compiled)
    definitions = compiled.definitions
    parameters = {parameter.name for parameter in compiled.parameters}
    claims = [claim for claim in compiled.spec.source_claims]
    claimed = {invariant.name for invariant, _node in compiled.invariants
               if invariant.kind == "equals_source" and invariant.name}
    span_texts = {candidate.claim_key: candidate.block_text for candidate in candidates}
    for claim in claims:
        if claim.span_id in span_texts and V.quote_in(claim.quote, span_texts[claim.span_id]):
            continue
        if _across_blocks(claim.quote, spans, repository):
            _count(reasons, "quote_across_blocks")
    entries: dict[str, dict[str, Any]] = {}
    work: list[dict[str, Any]] = []
    asked: dict[str, list[tuple[Candidate, bool]]] = {}
    expanded: dict[str, G.Node] = {}
    for name, node in definitions.items():
        entry: dict[str, Any] = {"name": name, "outcome": NOT_CHECKABLE, "reason": None, "stated": name in claimed}
        entries[name] = entry
        if name not in drawn:
            entry["reason"] = "not_bare"
            continue
        whole = expand(node, definitions)
        problem = binding_problem(whole)
        if problem is not None:
            entry["reason"] = problem
            continue
        expanded[name] = whole
        free = S.expanded_free(node, definitions)
        variable = drawn[name][0].variable
        pairs: list[tuple[Candidate, bool]] = []
        name_refused = False
        for candidate in candidates:
            relation = candidate.relation
            if relation.symbols != free or (relation.args and set(relation.args) != ({variable} if variable else set())):
                name_refused = True
                continue
            stated = name in claimed and any(claim.span_id == candidate.claim_key and quote_overlaps(claim.quote, candidate)
                                             for claim in claims)
            pairs.append((candidate, stated))
        if not pairs:
            entry["reason"] = "names" if name_refused else "no_readable_candidate"
            continue
        pairs.sort(key=lambda pair: 0 if pair[1] else 1)
        asked[name] = pairs
        grid = _projected_grid(compiled, free & parameters)
        elements = [_display_payload(compiled, name, element, grid) for element in drawn[name]]
        symbols = sorted(free)
        points = _difference_points(grid, drawn[name][0], compiled)
        work.append({
            "name": name, "variable": variable, "assumptions": _assumptions(compiled, set(free), variable),
            "points": points, "elements": elements,
            "pairs": [{"candidate": candidate.key, "stated": stated, "figure": to_json(whole),
                       "book": to_json(candidate.relation.rhs),
                       "controls": [to_json(control) for control in controls(whole, symbols)]}
                      for candidate, stated in pairs],
        })
    sympy_version = ""
    results: dict[tuple[str, str], Mapping[str, Any]] = {}
    failure: str | None = None
    if work:
        if not ready:
            failure = "sandbox_unavailable"
        else:
            payload = {"definitions": work, "per_check_seconds": PER_CHECK_SECONDS,
                       "cpu_seconds": SANDBOX_LIMITS.cpu_seconds}
            try:
                run = _run_sandbox(payload, sandbox)
            except pf_sandbox.SandboxUnavailable:
                run, failure = None, "sandbox_unavailable"
            if run is not None:
                if not run.ok or not isinstance(run.output, Mapping):
                    failure = "timeout" if run.timed_out else "sandbox_failed"
                else:
                    sympy_version = str(run.output.get("sympy_version") or "")
                    for item in run.output.get("results") or ():
                        if isinstance(item, Mapping):
                            results[(str(item.get("definition")), str(item.get("candidate")))] = item
    book: dict[str, E.BookLabel] = {}
    book_elements: dict[str, str] = {}
    problems: list[str] = []
    for name in definitions:
        entry = entries[name]
        if name not in asked:
            continue
        _decide_definition(entry, name, asked[name], results, failure, drawn[name], book, book_elements, problems)
    for entry in entries.values():
        reason = entry.get("reason")
        if reason and entry["outcome"] != CHECKED:
            _count(reasons, reason)
        for element in entry.get("display_failures") or ():
            _count(reasons, element)
    outcomes = [entry["outcome"] for entry in entries.values()]
    if DIFFERS in outcomes:
        outcome = DIFFERS
    elif CHECKED in outcomes:
        outcome = CHECKED
    elif UNDECIDED in outcomes:
        outcome = UNDECIDED
    else:
        outcome = NOT_CHECKABLE
    if not candidates and not reasons:
        _count(reasons, "no_readable_candidate")
    if outcome == DIFFERS:
        book, book_elements = {}, {}
    return _finished(compiled, list(entries.values()), candidates, reasons, outcome, sympy_version, book=book,
                     book_elements=book_elements, problems=problems)


def _across_blocks(quote: str, spans: Sequence[tuple[str, str, str]], repository: Any) -> bool:
    """§5.3: a quote that spans two blocks is never one candidate's pointer."""

    documents: dict[str, list[str]] = {}
    for extraction_id, span_id, _key in spans:
        ir = repository.load_document_ir(extraction_id)
        block = ir.block_by_span(span_id) if ir is not None else None
        if block is not None:
            documents.setdefault(extraction_id, []).append(block.text or "")
    return any(V.quote_in(quote, " ".join(texts)) for texts in documents.values())


def _difference_points(grid: Sequence[Mapping[str, float]], drawn: Drawn, compiled: S.CompiledFigure
                       ) -> list[dict[str, str]]:
    """The exact points a difference is looked for at (§6.3 step 5): the grid
    crossed with the variable's displayed samples."""

    samples = _samples(compiled, drawn)
    points = []
    for point in grid:
        base = {key: _exact(value) for key, value in point.items()}
        if drawn.variable is None:
            points.append(base)
        else:
            points.extend({**base, drawn.variable: _exact(sample)} for sample in samples)
    return points


def _decide_definition(entry: dict[str, Any], name: str, pairs: Sequence[tuple[Candidate, bool]],
                       results: Mapping[tuple[str, str], Mapping[str, Any]], failure: str | None,
                       drawn: Sequence[Drawn], book: dict[str, E.BookLabel], book_elements: dict[str, str],
                       problems: list[str]) -> None:
    """§6.6's precedence over this definition's pairs."""

    if failure is not None:
        entry.update(outcome=NOT_CHECKABLE if failure == "sandbox_unavailable" else UNDECIDED, reason=failure)
        return
    answers: list[tuple[Candidate, bool, Mapping[str, Any], str]] = []
    undecided_reason = None
    for candidate, stated in pairs:
        found = results.get((name, candidate.key)) or {}
        raw = found.get("result")
        result = raw if raw in _RESULTS else "undecided"
        reason = str(found.get("reason") or "") if result == "undecided" else ""
        if raw == "skipped":
            continue
        if result == "equal":
            verdict = _controls_verdict(found.get("controls"))
            if verdict is not None:
                result, reason = "undecided", verdict
        if result == "undecided":
            undecided_reason = undecided_reason or (reason if reason in REASONS else "no_proof")
        answers.append((candidate, stated, found, result))
    stated_equal = [answer for answer in answers if answer[1] and answer[3] == "equal"]
    stated_different = [answer for answer in answers if answer[1] and answer[3] == "different"]
    unstated_equal = [answer for answer in answers if not answer[1] and answer[3] == "equal"]
    chosen = (stated_equal or ([] if stated_different else unstated_equal) or [None])[0]
    if chosen is not None:
        candidate, _stated, found, _result = chosen
        relation = candidate.relation
        entry.update(outcome=CHECKED, reason=None, candidate=_provenance(candidate),
                     controls=list(found.get("controls") or ()))
        display = found.get("display") if isinstance(found.get("display"), Mapping) else {}
        shown: dict[str, Any] = {}
        failures: list[str] = []
        for element in drawn:
            agreement = display.get(element.element_id) if isinstance(display, Mapping) else None
            agreed = isinstance(agreement, Mapping) and agreement.get("agreed") is True
            shown[element.element_id] = {"samples": (agreement or {}).get("samples") if isinstance(agreement, Mapping)
                                         else 0, "agreed": agreed}
            if agreed:
                book_elements[element.element_id] = name
            else:
                why = str((agreement or {}).get("reason") or "") if isinstance(agreement, Mapping) else ""
                failures.append(why if why == "timeout" else "display_disagrees")
        entry["display"] = shown
        if failures:
            entry["display_failures"] = failures
        book[name] = E.BookLabel(lhs=relation.lhs, latex=relation.latex, variable=drawn[0].variable,
                                 tokens=dict(relation.tokens), extraction_id=candidate.extraction_id,
                                 span_id=candidate.span_id, page=candidate.page)
        return
    if stated_different:
        candidate, _stated, found, _result = stated_different[0]
        witness = found.get("witness") if isinstance(found.get("witness"), Mapping) else {}
        words = _witness_words(name, witness)
        problems.append(words)
        entry.update(outcome=DIFFERS, reason="differs", candidate=_provenance(candidate), witness=dict(witness))
        return
    if answers:
        entry.update(outcome=UNDECIDED, reason=undecided_reason or "no_proof")
        return
    entry.update(outcome=NOT_CHECKABLE, reason="no_readable_candidate")


def _controls_verdict(answers: Any) -> str | None:
    """§6.5: None when every control was refused. A control proved equal means the
    check is broken for this pair; an answer outside the closed results is inconclusive."""

    if not isinstance(answers, list) or not answers:
        return "control_inconclusive"
    if any(answer == "equal" for answer in answers):
        return "control_accepted"
    if any(answer not in ("different", "undecided") for answer in answers):
        return "control_inconclusive"
    return None


def _provenance(candidate: Candidate) -> dict[str, Any]:
    return {"extraction_id": candidate.extraction_id, "span_id": candidate.span_id, "page": candidate.page,
            "latex": candidate.relation.latex, "lhs": candidate.relation.lhs, "block_health": dict(candidate.health)}


def _finished(compiled: S.CompiledFigure, definitions: list[dict[str, Any]], candidates: Sequence[Candidate],
              reasons: Mapping[str, int], outcome: str, sympy_version: str, *,
              book: Mapping[str, E.BookLabel] | None = None, book_elements: Mapping[str, str] | None = None,
              problems: Sequence[str] = ()) -> Check:
    elements = E.element_map(compiled, book or {}, book_elements or {}) if book_elements else []
    closed = {key: count for key, count in sorted(reasons.items()) if key in REASONS}
    digest = {
        "spec": compiled.spec.canonical_json(),
        "candidates": [[candidate.extraction_id, candidate.span_id, candidate.relation.latex,
                        (candidate.health or {}).get("status")] for candidate in candidates],
        "certification_version": CERTIFICATION_VERSION, "harness_sha256": HARNESS_SHA256,
        "reader_version": BM.READER_VERSION, "sympy_version": sympy_version,
    }
    return Check(outcome=outcome, definitions=definitions, elements=elements, reasons=closed, problems=list(problems),
                 input_hash=hashlib.sha256(json.dumps(digest, sort_keys=True).encode("utf-8")).hexdigest(),
                 sympy_version=sympy_version, rationale=_rationale(definitions, reasons))


def _rationale(definitions: Sequence[Mapping[str, Any]], reasons: Mapping[str, int]) -> str:
    """Code text only, for the ledger: per definition its name, outcome, closed
    reason and a difference's witness. Never model text (a name is the grammar's)."""

    parts = []
    for entry in definitions:
        text = f"{entry['name']}: {entry['outcome']}"
        if entry.get("reason"):
            text += f" ({entry['reason']})"
        if entry.get("witness"):
            text += " at " + ", ".join(f"{key}={value}" for key, value in sorted(
                (entry["witness"].get("at") or {}).items()))
        parts.append(text)
    if not parts:
        parts = [f"{key}: {count}" for key, count in sorted(reasons.items())]
    return "; ".join(parts)[:400]


# ---------------------------------------------------------------------------
# 3f: the row and its verdict
# ---------------------------------------------------------------------------

def record(connection: Any, figure_id: str, check: Check, *, trigger: str, created_at: str) -> str:
    """One ``figure_source_checks`` row and its ``judgment_ledger`` verdict, in the
    caller's transaction (F6, G23i): either both commit or neither. A later check
    supersedes the figure's newest earlier verdict on this question."""

    earlier = store.figure_verdicts(connection, LEDGER_TASK, figure_id)
    judgment_id = append_judgment(
        connection, task=LEDGER_TASK, left_kind="interactive_figure", left_id=figure_id, judge="verifier",
        input_hash=check.input_hash, verdict=check.outcome, rationale=check.rationale,
        supersedes_id=earlier[-1]["id"] if earlier else None, created_at=created_at)
    row_id = "fsc_" + new_ulid()
    store.insert_source_check(connection, {
        "id": row_id, "figure_id": figure_id, "certification_version": CERTIFICATION_VERSION, "trigger": trigger,
        "outcome": check.outcome, "definitions": check.definitions, "elements": check.elements,
        "reasons": check.reasons, "harness_sha256": HARNESS_SHA256, "reader_version": BM.READER_VERSION,
        "sympy_version": check.sympy_version, "duration_ms": check.duration_ms, "judgment_id": judgment_id,
        "created_at": created_at,
    })
    return row_id


def failed_check(compiled: S.CompiledFigure) -> Check:
    """A check that could not run: an honest row, certifying nothing (G23f)."""

    return _finished(compiled, [], [], {"sandbox_failed": 1}, UNDECIDED, "")


def stored_problems(found: Mapping[str, Any]) -> list[str]:
    """The difference a check row records, in code's words, for *rebuild*'s first attempt (§6.6)."""

    return [_witness_words(str(entry.get("name")), entry.get("witness") or {})
            for entry in found.get("definitions") or () if entry.get("outcome") == DIFFERS]


def grammar_row(row: Mapping[str, Any]) -> bool:
    """Only grammar-tier figures are checked (§11.1, N-a): sketch, ``js_animation``
    and ``manim`` keep *not checked against the book*."""

    return (row.get("tier") or "grammar") == "grammar" and row.get("spec_version") == S.SPEC_VERSION


def current_row(repository: Any, figure_id: str) -> dict[str, Any] | None:
    """The newest check of a figure at the current certification version (the one shown)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.latest_source_check(connection, figure_id, CERTIFICATION_VERSION)


def recheck_due(found: Mapping[str, Any] | None) -> bool:
    """No check at the current certification version; or the last found no sandbox
    (a machine that has one now can decide what that one could not)."""

    if found is None:
        return True
    return "sandbox_unavailable" in (found.get("reasons") or {}) and pf_sandbox.sandbox_available()


_RECHECKING: set[str] = set()
_RECHECKING_GUARD = threading.Lock()


def recheck(vault: Any, repository: Any, row: Mapping[str, Any], *, live_vault: Callable[[], Any] | None = None,
            clock: Clock | None = None, dry_run: bool = False, sandbox: Sandbox | None = None,
            sandbox_ready: Callable[[], bool] | None = None) -> Check | None:
    """A stored grammar figure rechecked by code, with no model client (§10.4),
    admitted against the switch as it is now before the sandbox and before the
    write (§6.7). ``dry_run`` reports and writes nothing, the block-health store
    included. None: not a figure this checks, the switch changed, or another
    recheck of it is running here."""

    if not grammar_row(row) or row.get("verification") not in store.SHOWN or not row.get("spec_json"):
        return None
    if not enabled(vault):
        return None
    figure_id = str(row["id"])
    with _RECHECKING_GUARD:
        if figure_id in _RECHECKING:
            return None
        _RECHECKING.add(figure_id)
    try:
        gate = FiguresGate(vault, recheck_key, live_vault=live_vault)
        try:
            gate.check("recheck")
            compiled = S.parse_spec(row["spec_json"])
            check = check_figure(vault, repository, compiled, spans=input_spans(row), grounding=row.get("grounding"),
                                 persist=not dry_run, sandbox=sandbox, sandbox_ready=sandbox_ready)
            if dry_run:
                return check
            gate.check("store")
        except (FiguresChanged, S.SpecError):
            return None
        created_at = utc_now_iso(clock)
        with repository.atomic():
            record(repository.connection(), figure_id, check, trigger="recheck", created_at=created_at)
        return check
    finally:
        with _RECHECKING_GUARD:
            _RECHECKING.discard(figure_id)


# ---------------------------------------------------------------------------
# The n=1 instruments (§12): descriptive, never a decision rule
# ---------------------------------------------------------------------------

def _shown_rows(connection: Any) -> list[dict[str, Any]]:
    rows = store.shown_figures(connection, (S.SPEC_VERSION,), limit=-1)
    return [row for row in rows if grammar_row(row)]


def coverage(vault: Any, repository: Any, *, dry_run: bool, withheld: Callable[[Mapping[str, Any]], bool],
             sandbox: Sandbox | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """``reader figure-checks --recheck``: every stored grammar figure rechecked
    by code, with no model client; ``dry_run`` writes nothing. By outcome and
    closed reason key, with what was checked (§12 item 1). Written rechecks only
    run for figures due one; a dry run looks at all of them."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = _shown_rows(connection)
    outcomes: dict[str, int] = {}
    reasons: dict[str, int] = {}
    elements: dict[str, int] = {}
    checked: list[dict[str, Any]] = []
    durations: list[int] = []
    skipped = {"withheld": 0, "not_due": 0, "unreadable": 0}
    for row in rows:
        if withheld(row):
            skipped["withheld"] += 1
            continue
        if not dry_run and not recheck_due(current_row(repository, str(row["id"]))):
            skipped["not_due"] += 1
            continue
        try:
            result = recheck(vault, repository, row, dry_run=dry_run, sandbox=sandbox, clock=clock)
        except Exception:  # noqa: BLE001 - one figure that cannot be read does not end the report
            result = None
        if result is None:
            skipped["unreadable"] += 1
            continue
        outcomes[result.outcome] = outcomes.get(result.outcome, 0) + 1
        durations.append(result.duration_ms)
        for key, count in result.reasons.items():
            reasons[key] = reasons.get(key, 0) + count
        for element in result.elements:
            role = str(element.get("role"))
            elements[role] = elements.get(role, 0) + 1
        checked.extend(_audit_entries(row, result.definitions, result.elements))
    return {"figures": sum(outcomes.values()), "outcomes": outcomes, "reasons": dict(sorted(reasons.items())),
            "elements": elements, "skipped": skipped, "latency_ms": _latency(durations), "checked": checked,
            "certification_version": CERTIFICATION_VERSION, "reader_version": BM.READER_VERSION,
            "harness_sha256": HARNESS_SHA256, "model_calls": 0}


def _latency(durations: Sequence[int]) -> dict[str, int | None]:
    ordered = sorted(durations)
    return {"median": ordered[len(ordered) // 2] if ordered else None, "max": ordered[-1] if ordered else None}


def _audit_entries(row: Mapping[str, Any], definitions: Sequence[Mapping[str, Any]],
                   elements: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Each element carrying the claim, for the owner's audit (§12 item 2): the
    book's equation as read, its page and the figure's definition, rendered."""

    try:
        compiled = S.parse_spec(row["spec_json"])
    except S.SpecError:
        return []
    by_name = {entry.get("name"): entry for entry in definitions}
    found = []
    for element in elements:
        if element.get("role") != "book":
            continue
        name = str(element.get("definition"))
        node = compiled.definitions.get(name)
        provenance = (by_name.get(name) or {}).get("candidate") or {}
        found.append({
            "figure_id": row["id"], "element": element.get("id"), "definition": name,
            "definition_tex": E.to_tex(expand(node, compiled.definitions), {}) if node is not None else "",
            "book_equation": element.get("equation"), "lhs": element.get("tex"),
            "extraction_id": provenance.get("extraction_id"), "span_id": provenance.get("span_id"),
            "page": provenance.get("page"), "block_health": provenance.get("block_health"),
        })
    return found


def audit(repository: Any, *, withheld: Callable[[Mapping[str, Any]], bool]) -> dict[str, Any]:
    """``reader figure-checks`` with no ``--recheck``: each element carrying the claim,
    from the ledger. A figure withheld now is left out, its equations with it: its
    row keeps its stored ``verification`` when a source is held out later (§11.3)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        checks = store.latest_source_checks(connection, CERTIFICATION_VERSION)
        rows = {str(row["id"]): row for row in _shown_rows(connection)}
    checked: list[dict[str, Any]] = []
    outcomes: dict[str, int] = {}
    skipped = {"withheld": 0}
    for found in checks:
        row = rows.get(str(found["figure_id"]))
        if row is not None and withheld(row):
            skipped["withheld"] += 1
            continue
        outcomes[found["outcome"]] = outcomes.get(found["outcome"], 0) + 1
        if row is not None:
            checked.extend(_audit_entries(row, found["definitions"], found["elements"]))
    return {"figures": sum(outcomes.values()), "outcomes": outcomes, "checked": checked, "skipped": skipped,
            "certification_version": CERTIFICATION_VERSION}


def report_block(connection: Any, *, since: str | None = None) -> dict[str, Any]:
    """The reader report's ``source_checks``: outcomes, reasons, elements, latency, and
    opens and "not right?" notes for figures with a ``book`` element and without (§12 item 4)."""

    latest = store.latest_source_checks(connection, CERTIFICATION_VERSION)
    checks = [found for found in latest if since is None or str(found["created_at"]) >= since]
    outcomes: dict[str, int] = {}
    reasons: dict[str, int] = {}
    elements: dict[str, int] = {}
    for found in checks:
        outcomes[found["outcome"]] = outcomes.get(found["outcome"], 0) + 1
        for key, count in (found.get("reasons") or {}).items():
            reasons[key] = reasons.get(key, 0) + int(count)
        for element in found.get("elements") or ():
            role = str(element.get("role"))
            elements[role] = elements.get(role, 0) + 1
    # Activity goes by its own date, whenever its figure was last checked: a figure
    # checked Oct 1 and opened Nov 2 was opened since Nov 1, and the reverse was not.
    with_book = {str(found["figure_id"]) for found in latest
                 if any(element.get("role") == "book" for element in found.get("elements") or ())}
    opened = {"with_book": 0, "without": 0}
    notes = {"with_book": 0, "without": 0}
    checked_figures = {str(found["figure_id"]) for found in latest}
    for (figure_id, created_at) in connection.execute(
            "SELECT json_extract(payload_json, '$.figure_id'), created_at FROM interaction_events "
            "WHERE kind = 'reader_action_invoked' AND json_extract(payload_json, '$.event') = 'figure_opened'"):
        if str(figure_id) in checked_figures and (since is None or str(created_at) >= since):
            opened["with_book" if str(figure_id) in with_book else "without"] += 1
    for (supersedes_id, created_at) in connection.execute(
            "SELECT supersedes_id, created_at FROM interactive_figures WHERE supersedes_id IS NOT NULL "
            "AND COALESCE(revision_note, '') != ''"):
        if str(supersedes_id) in checked_figures and (since is None or str(created_at) >= since):
            notes["with_book" if str(supersedes_id) in with_book else "without"] += 1
    return {"certification_version": CERTIFICATION_VERSION, "figures": sum(outcomes.values()), "outcomes": outcomes,
            "reasons": dict(sorted(reasons.items())), "elements": elements,
            "latency_ms": _latency([int(found.get("duration_ms") or 0) for found in checks]),
            "opened": opened, "not_right_notes": notes}


def add_report_block(report: dict[str, Any], sqlite_path: Any, *, since: str | None = None) -> dict[str, Any]:
    """Put :func:`report_block` under the reader report's ``figures`` (``learnloop reader
    report`` calls it only with the switch on, so off the report is as before: G23g)."""

    with closing(connect(sqlite_path, read_only=True)) as connection:
        if store.has_source_checks(connection):
            report.setdefault("figures", {})["source_checks"] = report_block(connection, since=since)
    return report


__all__ = [
    "add_report_block",
    "audit",
    "coverage",
    "CERTIFICATION_VERSION",
    "CHECKED",
    "Check",
    "DIFFERS",
    "HARNESS",
    "HARNESS_SHA256",
    "LEDGER_TASK",
    "NOT_CHECKABLE",
    "OUTCOMES",
    "REASONS",
    "REJECTED_REASON",
    "UNDECIDED",
    "check_figure",
    "controls",
    "current_row",
    "drawn_by_reference",
    "enabled",
    "failed_check",
    "grammar_row",
    "input_spans",
    "read_candidates",
    "recheck",
    "recheck_due",
    "recheck_key",
    "record",
    "stored_problems",
]
