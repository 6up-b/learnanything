"""Reader workbench RW1c: the Reader tutor's three answer modes (spec_reader_workbench_v1 §4.6).

A tutor that looks things up answers in the Reader in up to three labelled
parts, chosen per answer by the tutor:

1. **"From your books"**: a short verbatim excerpt of one passage it was
   given. Quote-verified here, in code: an excerpt whose text is not in its
   passage (whitespace and Unicode compatibility forms aside), whose passage
   the tutor was not given, that quotes the learner's own selection text,
   that is held-out material, or that reproduces the answer of an item being
   practised is dropped, and the answer falls back to mode 2. The drop is on
   the receipt (the report counts it, §15).
2. **A grounded explanation**: ``answer_md`` with its validated citations
   (today's answer, now with retrieved passages).
3. **A bridge to the learner's work**: ``bridge_md``, kept only when the
   learner's open questions or recent workbench steps were in the context
   (personalized only).

**Abstention** (round 1 §7, round 3 §4): when retrieval's verification ran
and kept no passage, the answer opens with :data:`ABSTENTION_LINE`, the
excerpt is dropped and no citation is shown as the books'.

Nothing here touches evidence, mastery or grading inputs (T6's ruling): the
answer's reveal accounting is ``tutor_qa``'s, unchanged. This package never
imports the retrieval package: the adapter injects the retrieval as
:class:`ReaderTutorRequest.retrieve`.
"""
from __future__ import annotations

import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.tutor.context_delivery import apply_budget, notable

#: The line an answer opens with when the learner's books don't cover it.
ABSTENTION_LINE = "Your books don't cover this directly — this is LearnLoop's model's explanation"
#: "Another way" found no passage the inquiry has not shown: the books did
#: cover the question (the first answer showed it), so the line says what is true.
ALTERNATIVE_ABSTENTION_LINE = ("Your books don't explain this another way — this is LearnLoop's model's "
                               "explanation")
#: Mode names, in the order an answer shows them.
MODES = ("excerpt", "grounded", "bridge")
#: An excerpt shorter than this (normalized characters) is not a quote.
MIN_EXCERPT_CHARS = 8
#: An excerpt longer than this is not "a short cited excerpt".
MAX_EXCERPT_CHARS = 1200
#: The bridge's own bound (it is "a short explanation").
MAX_BRIDGE_CHARS = 1500


@dataclass
class ReaderTutorRequest:
    """What the adapter hands ``tutor_qa.ask_question(reader_tutor=...)``.

    ``retrieve`` returns ``(spans or None, manifest)``: None when nothing was
    retrieved (verification could not run, a cold administration, a failure),
    so the tutor keeps today's delivery and no abstention is claimed; ``[]``
    with ``manifest["books_cover"] is False`` when verification ran and kept
    no passage. ``learner_work`` is the bridge's context (empty unless
    personalized). ``item`` is the practice item a workbench session binds
    the question to (its answer never reaches an excerpt)."""

    retrieve: Callable[[], tuple[list[dict[str, Any]] | None, dict[str, Any]]] | None = None
    intent: str = "explain"
    personalized: bool = True
    learner_work: list[dict[str, Any]] = field(default_factory=list)
    item: Any = None
    #: The caller's derived policy (``reading``, ``assisted_practice`` or
    #: ``cold_attempt``), kept apart from ``item`` so a cold administration
    #: (which binds no exclusion item) is never read as ``reading`` (Codex
    #: review F2).
    policy: str = "reading"
    #: The item a bound workbench session is practising and the practice
    #: session its submit counts in, whatever the policy: the question is
    #: persisted on them, so its hint equivalence and every displayed
    #: component's answer overlap reach the attempt (Codex review F1).
    bound_item: Any = None
    practice_session_id: str | None = None
    #: The client's cold path already records this question as a hint on the
    #: bound item in the bound practice session, the same submission window
    #: (``reader_dialogue._record_cold_hint_equivalent``): the bound question
    #: keeps the item for its reveals and is not counted as a hint a second
    #: time (Codex re-review F1). Never set for a cold row in another session.
    hint_counted_elsewhere: bool = False
    #: Item-bound, the guard every delivered span passes (the selection, its
    #: neighbours, the blocks they cite and the retrieved passages):
    #: ``guard(spans) -> (kept, counts)``. Injected by the adapter (this
    #: package never imports retrieval); None outside a bound session.
    context_guard: Callable[[Sequence[Mapping[str, Any]]], tuple[list[dict[str, Any]], dict[str, int]]] | None = None
    #: "Another way": every passage the inquiry has shown (its exchanges'
    #: selections, citations, excerpts and retrieved passages, and the
    #: passages its pressed offers showed). No new excerpt or citation shown
    #: may be one of them (Codex review F7); they stay in the tutor's context.
    shown_span_keys: Sequence[str] = ()


def run_retrieval(request: ReaderTutorRequest) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    """The injected retrieval; any failure keeps today's delivery (retrieval is context)."""

    if request.retrieve is None:
        return None, {"status": "not_run", "books_cover": None}
    try:
        spans, manifest = request.retrieve()
    except Exception as exc:  # noqa: BLE001 - never lose the question to retrieval
        return None, {"status": f"failed ({type(exc).__name__})", "books_cover": None}
    return (None if spans is None else [dict(span) for span in spans]), dict(manifest or {})


def deliver(reader_spans: Sequence[Mapping[str, Any]], retrieved: Sequence[Mapping[str, Any]], *,
            budget_tokens: int, withheld: Any = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The selection and its neighbours first, then each retrieved passage not
    already delivered, within the context budget (the citation allowlist keeps
    the selection first, §4.6). A retrieved passage the held-out material
    covers never reaches the tutor (a second guard: the sources service
    already withholds exam and held-out material)."""

    delivered = {(str(span.get("extraction_id")), str(span.get("span_id"))) for span in reader_spans}
    extra: list[dict[str, Any]] = []
    held = 0
    for span in retrieved:
        key = (str(span.get("extraction_id")), str(span.get("span_id")))
        if key in delivered:
            continue
        if withheld is not None and withheld.covers(*key):
            held += 1
            continue
        delivered.add(key)
        extra.append(dict(span))
    kept, receipt = apply_budget([*(dict(span) for span in reader_spans), *extra], budget_tokens)
    receipt["retrieved"] = {"offered": len(retrieved), "added": len(extra), "held_out": held}
    return kept, receipt


def _normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text or "").split())


def verify_excerpt(excerpt: Any, spans: Sequence[Mapping[str, Any]], *, withheld: Any = None,
                   item: Any = None) -> tuple[dict[str, Any] | None, str | None]:
    """``(excerpt, None)`` when it quotes a passage the tutor was given, else ``(None, why)``."""

    from learnloop.tutor.tutor_qa import span_leaks_expected

    if excerpt is None:
        return None, None
    extraction_id = str(getattr(excerpt, "extraction_id", "") or "")
    span_id = str(getattr(excerpt, "span_id", "") or "")
    quote = str(getattr(excerpt, "quote", "") or "").strip()
    wanted = _normalized(quote)
    if len(wanted) < MIN_EXCERPT_CHARS:
        return None, "too short to be a quote"
    if len(quote) > MAX_EXCERPT_CHARS:
        return None, "too long for an excerpt"
    passages = [span for span in spans
                if str(span.get("extraction_id")) == extraction_id and str(span.get("span_id")) == span_id]
    book = [span for span in passages if span.get("relation") != "selected_text"]
    if not book:
        return None, ("it quotes the learner's selection, not the book" if passages
                      else "not a passage the tutor was given")
    found = next((span for span in book if wanted in _normalized(str(span.get("text") or ""))), None)
    if found is None:
        return None, "its text is not in the passage"
    if withheld is not None and withheld.covers(extraction_id, span_id):
        return None, "held-out material"
    if item is not None and (span_leaks_expected(quote, item.expected_answer)
                             or span_leaks_expected(str(found.get("text") or ""), item.expected_answer)):
        # The span guard (Codex review F3): a short key ("2/13") is exposed by
        # a passage that states it, which the long-answer overlap misses.
        return None, "it reproduces the answer to the item being practised"
    return {"extraction_id": extraction_id, "span_id": span_id, "quote": quote,
            "label": found.get("label"), "relation": found.get("relation"),
            "source_id": found.get("source_id")}, None


def finalize(answer: Any, spans: Sequence[Mapping[str, Any]], citations: list[dict[str, Any]], *,
             retrieval: Mapping[str, Any], request: ReaderTutorRequest, withheld: Any = None,
             item: Any = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The answer's modes and the citations shown: ``(view, citations)``.

    ``view`` is what the Reader renders and the receipt keeps; on abstention
    the citations shown are none (the validated ones stay on the receipt)."""

    abstained = retrieval.get("books_cover") is False
    excerpt, dropped = verify_excerpt(getattr(answer, "excerpt", None), spans, withheld=withheld, item=item)
    if abstained and excerpt is not None:
        excerpt, dropped = None, "the books don't cover this, so nothing is quoted as theirs"
    shown = set(request.shown_span_keys) if request.intent == "alternative" else set()
    if excerpt is not None and f"{excerpt['extraction_id']}:{excerpt['span_id']}" in shown:
        # "Another way" never repeats a passage the inquiry showed (G48).
        excerpt, dropped = None, "this inquiry has already shown that passage"
    repeated = [c for c in citations if f"{c.get('extraction_id')}:{c.get('span_id')}" in shown]
    if repeated:
        citations = [c for c in citations if c not in repeated]
    # A citation of a passage from another book carries its source, so the
    # Reader can open it there (Codex review F9).
    sources = {(str(span.get("extraction_id")), str(span.get("span_id"))): span.get("source_id")
               for span in spans if span.get("source_id")}
    citations = [{**c, "source_id": sources[(str(c.get("extraction_id")), str(c.get("span_id")))]}
                 if (str(c.get("extraction_id")), str(c.get("span_id"))) in sources else dict(c)
                 for c in citations]
    bridge: str | None = str(getattr(answer, "bridge_md", None) or "").strip() or None
    bridge_dropped = None
    if bridge and not (request.personalized and request.learner_work):
        bridge, bridge_dropped = None, "no work of the learner's was in context"
    elif bridge and len(bridge) > MAX_BRIDGE_CHARS:
        bridge = bridge[: MAX_BRIDGE_CHARS - 1] + "…"
    modes = [mode for mode, present in (("excerpt", excerpt is not None), ("grounded", True),
                                        ("bridge", bool(bridge))) if present]
    view: dict[str, Any] = {
        "modes": modes,
        "excerpt": excerpt,
        "bridge_md": bridge or None,
        "abstained": abstained,
        "abstention_line": (ALTERNATIVE_ABSTENTION_LINE if request.intent == "alternative" else ABSTENTION_LINE)
        if abstained else None,
        "dropped_excerpt": dropped,
        "dropped_bridge": bridge_dropped,
        "intent": request.intent,
        "personalized": bool(request.personalized),
        "retrieval": {key: retrieval.get(key) for key in (
            "status", "policy", "intent", "label", "passages", "span_keys", "books_cover", "reason")
            if key in retrieval},
    }
    if repeated:
        view["repeated_citations"] = len(repeated)
    displayed = [] if abstained else list(citations)
    if abstained and citations:
        view["withheld_citations"] = len(citations)
    return view, displayed


def displayed_text(answer_md: str | None, view: Mapping[str, Any] | None, *, excerpt: bool = True) -> str:
    """Everything a Reader answer shows as text: the explanation, the excerpt
    and the bridge. ``excerpt=False`` leaves the excerpt out: a bound item's
    ``tutor_answer`` overlap is measured on the explanation and the bridge,
    and the excerpt is debited with the passages it opens (``source_review``),
    so each displayed component is counted once (Codex re-review F11)."""

    view = view or {}
    parts = [str(answer_md or ""), str((view.get("excerpt") or {}).get("quote") or "") if excerpt else "",
             str(view.get("bridge_md") or "")]
    return "\n\n".join(part for part in parts if part.strip())


def delivery_receipt(receipt: Mapping[str, Any]) -> dict[str, Any] | None:
    """The delivery's receipt when it records something (a trim, a drop, a retrieved passage added)."""

    if notable(receipt) or (receipt.get("retrieved") or {}).get("added"):
        return dict(receipt)
    return None


__all__ = [
    "ABSTENTION_LINE",
    "ALTERNATIVE_ABSTENTION_LINE",
    "MAX_BRIDGE_CHARS",
    "MAX_EXCERPT_CHARS",
    "MIN_EXCERPT_CHARS",
    "MODES",
    "ReaderTutorRequest",
    "deliver",
    "delivery_receipt",
    "displayed_text",
    "finalize",
    "run_retrieval",
    "verify_excerpt",
]
