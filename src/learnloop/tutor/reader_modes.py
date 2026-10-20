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
from collections.abc import Callable, Collection, Mapping, Sequence
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


#: What a bound request's prompt shows in place of an earlier answer that
#: would give the item's answer away (fix round 5, R2).
EARLIER_ANSWER_LEFT_OUT = "[An earlier answer is left out while you work this problem.]"


@dataclass(frozen=True)
class BoundAsk:
    """A Reader question a workbench session binds to a practice item, derived
    on the server and validated (``handlers.reader_tutor.bound_ask``).

    Fix round 5, ruling R1: the binding is its own value, built before and
    apart from the retrieval request, whenever either RW1c switch is on and
    the request names a bound workbench session. Retrieval being off changes
    only whether retrieval runs; it never drops the item, its guards or its
    accounting (rounds 1-4 hung all three off the retrieval request, which
    is None with retrieval off, so an offers-only bound ask lost them).

    * ``item`` and ``practice_session_id``: the row is stored on them, so the
      item window counts its hint (``Repository.count_hint_equivalent_question_events``)
      and the reveal ledger debits what it showed.
    * ``cold``: the restriction's cold status (the client's flag or the
      server's own derivation of a cold administration of the item).
    * ``context_guard``: the item's guard over every span the tutor is given
      (the selection, its neighbours, the blocks they cite, the retrieved
      passages): ``guard(spans) -> (kept, counts)``.
    * ``answer_guard``: the same guard's check for one text
      (``text -> leaks``): earlier answers in the thread, model-written
      learner-work lines and every model-written input to the lookup pass it
      before anything model-visible is built (R2; fix round 6, R1 and R3).
    * ``answer_overlap``: the same matcher's score for one text
      (``text -> 0..1``), which picks the answer to withhold first when only
      their combination gives the item's answer away (fix round 6, R1).

    The guards are injected by the adapter; this package never imports
    retrieval."""

    item: Any
    practice_session_id: str | None = None
    cold: bool = False
    context_guard: Callable[[Sequence[Mapping[str, Any]]], tuple[list[dict[str, Any]], dict[str, int]]] | None = None
    answer_guard: Callable[[str], bool] | None = None
    answer_overlap: Callable[[str], float] | None = None

    def hint_equivalent(self, substantive: bool) -> bool:
        """The bound row's hint flag, the one value stored and returned (R1).

        A cold Ask is a hint under L6 whatever its question type, whether or
        not the client's cold attempt row exists or can be fetched (that row
        only deduplicates: ``reader_dialogue._record_cold_hint_equivalent``
        leaves its flag off when this row carries the hint). A bound Ask
        outside a cold administration uses the ordinary classification
        (``substantive``: its type is in ``tutor_qa.HINT_EQUIVALENT_TYPES``)."""

        return bool(self.cold or substantive)


#: How the texts one prompt carries together are read as one: the matcher
#: sees them as the tutor does, side by side.
_JOIN = "\n\n"


def withhold(texts: Sequence[str], binding: BoundAsk | None, *, placeholders: Sequence[str] | None = None,
             already: Collection[int] = ()) -> set[int]:
    """The indexes of the model-written ``texts`` one model call carries to withhold under the binding.

    A text that gives the item's answer away alone is withheld; then, while
    the texts delivered (each withheld one as its ``placeholders`` entry,
    empty when dropped) still give it away TOGETHER, the kept text with the
    highest individual overlap (ties: the most recent, the highest index) is
    withheld and the whole is checked again (fix round 6, R1). ``already``
    are withheld from the start (another call's decision on the same text).
    Empty texts are ignored."""

    if binding is None or binding.answer_guard is None:
        return set(already)
    leaks = binding.answer_guard
    overlap = binding.answer_overlap or (lambda text: 1.0 if leaks(text) else 0.0)
    stand_in = list(placeholders) if placeholders is not None else [""] * len(texts)
    present = [index for index, text in enumerate(texts) if text]
    out = set(already) | {index for index in present if leaks(texts[index])}

    def combined() -> str:
        return _JOIN.join(stand_in[index] if index in out else texts[index] for index in present)

    while leaks(combined()):
        kept = [index for index in present if index not in out]
        if not kept:
            break
        out.add(max(kept, key=lambda index: (overlap(texts[index]), index)))
    return out


#: One slot of a model call: its name and its delivered ``(index, text)``
#: pairs, in the order the call carries them.
Slot = tuple[str, Sequence[tuple[int, str]]]


def withhold_for_call(slots: Sequence[Slot], binding: BoundAsk | None, *,
                      placeholders: Mapping[str, str] | None = None,
                      already: Mapping[str, Collection[int]] | None = None) -> dict[str, set[int]]:
    """The withheld indexes, per slot, of ONE model call (fix round 7, R1).

    The union of every model-written text the call is given (each slot's
    texts, in delivery order) is read as one by :func:`withhold`, so texts
    that each pass alone (an earlier answer, a gap statement, a
    misconception's correction) are never delivered together when together
    they give the item's answer away. ``placeholders`` is what a withheld
    text of a slot is delivered as (empty: dropped); ``already`` are the
    indexes another call withheld."""

    placeholders, already = dict(placeholders or {}), dict(already or {})
    keys = [(name, index) for name, pairs in slots for index, _text in pairs]
    texts = [text for _name, pairs in slots for _index, text in pairs]
    stand_in = [placeholders.get(name, "") for name, _index in keys]
    seeded = {n for n, (name, index) in enumerate(keys) if index in already.get(name, ())}
    out: dict[str, set[int]] = {name: set(already.get(name, ())) for name, _pairs in slots}
    for n in withhold(texts, binding, placeholders=stand_in, already=seeded):
        name, index = keys[n]
        out[name].add(index)
    return out


#: How many open questions the lookup query and the bridge's work carry
#: (the first ones kept; ``source_retrieval.reader_tutor`` reads it).
QUERY_GAPS = 3


def open_question_work(gaps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The bridge's open-question lines for these gap statements (the first :data:`QUERY_GAPS`)."""

    return [{"kind": "open_question", "statement": entry["statement"], "author": "LearnLoop's reading",
             "learning_object_id": entry.get("learning_object_id")} for entry in list(gaps)[:QUERY_GAPS]]


def _misconception_text(record: Any) -> str:
    # A misconception and its correction both reach the verification's
    # context; the correction can be the item's answer.
    return " ".join(filter(None, [str(getattr(record, "statement", "") or ""),
                                  str(getattr(record, "correction_statement", "") or "")]))


@dataclass(frozen=True)
class BoundDelivery:
    """What a bound request delivers to its model calls, from ONE withheld set (fix round 7, R1).

    ``thread`` is the tutor's thread (a withheld earlier answer replaced by
    the validated placeholder); ``gaps`` and ``misconceptions`` are the lookup's
    inputs (its query, so its rewrite and the verification's question, and
    the verification's context; None: not a lookup, or the service resolves
    them); ``learner_work`` is the bridge's context; ``withheld`` counts what
    each slot left out. The manifest records ``thread``."""

    thread: list[dict[str, Any]]
    gaps: list[Any]
    misconceptions: list[Any] | None
    learner_work: list[dict[str, Any]]
    withheld: dict[str, int]

    @property
    def lookup_inputs(self) -> dict[str, Any]:
        return {"gaps": list(self.gaps), "misconceptions": self.misconceptions}


def plan_bound_delivery(binding: BoundAsk | None, *, thread: Sequence[Mapping[str, Any]],
                        gaps: Sequence[Mapping[str, Any]] = (), misconceptions: Sequence[Any] | None = None,
                        learner_work: Sequence[Mapping[str, Any]] = ()) -> BoundDelivery:
    """Every model-written text a bound request delivers, withheld once (fix round 7, R1).

    Two model calls read them: the lookup's verification (and its query
    rewrite, which reads a prefix of the same query) carries the open-gap
    statements in its question and the misconceptions with their
    corrections in its context; the tutor carries the earlier answers, the
    bridge's open questions (the same gap statements) and the problem line
    of the learner's work. :func:`withhold_for_call` reads each call's union
    as delivered; a text either call withholds is withheld from every slot
    and record, and the calls are read again until nothing changes (the
    lists delivered depend on what is withheld: the first
    :data:`QUERY_GAPS` gap statements KEPT are the ones used). Never
    withheld, never read: the learner's own words (their question, their
    earlier questions, their workbench steps). Unbound, everything is
    delivered as given."""

    turns = [dict(turn) for turn in thread]
    gaps, work = list(gaps), [dict(entry) for entry in learner_work]
    records = list(misconceptions) if misconceptions is not None else None
    others = [entry for entry in work if entry.get("kind") != "open_question"]
    # The bridge's open questions are built from the gap statements (the
    # same lines the query carries), so they are one slot with them.
    bridged = any(entry.get("kind") == "open_question" for entry in work)
    if binding is None or binding.answer_guard is None:
        return BoundDelivery(turns, gaps, records, work, {})
    # The replacement is validated too (round 6, R1): a key that the fixed
    # line itself states gets the empty answer instead.
    placeholder = "" if binding.answer_guard(EARLIER_ANSWER_LEFT_OUT) else EARLIER_ANSWER_LEFT_OUT
    answers = [str(turn.get("answer_md") or "") for turn in turns]
    statements = [str(entry.get("statement") or "") for entry in gaps]
    problems = [str(entry.get("problem") or "") for entry in others]
    withheld: dict[str, set[int]] = {"answers": set(), "gaps": set(), "misconceptions": set(), "problems": set()}

    def calls(answer_stand_in: str) -> list[tuple[list[Slot], dict[str, str]]]:
        kept_gaps = [(i, statements[i]) for i in range(len(gaps)) if i not in withheld["gaps"]][:QUERY_GAPS]
        lookup: list[Slot] = [("gaps", kept_gaps)]
        if records is not None:
            lookup.append(("misconceptions", [(i, _misconception_text(record)) for i, record in enumerate(records)
                                              if i not in withheld["misconceptions"]]))
        # The withheld answers are delivered as the placeholder; the dropped
        # statements and lines are not delivered at all.
        tutor: list[Slot] = [
            ("answers", list(enumerate(answers))),
            ("gaps", kept_gaps if bridged else []),
            ("problems", [(i, text) for i, text in enumerate(problems) if i not in withheld["problems"]]),
        ]
        return [(lookup, {}), (tutor, {"answers": answer_stand_in})]

    changed = True
    while changed:
        changed = False
        for slots, stand_ins in calls(placeholder):
            found = withhold_for_call(slots, binding, placeholders=stand_ins,
                                      already={"answers": withheld["answers"]})
            for name, indexes in found.items():
                if indexes - withheld[name]:
                    withheld[name] |= indexes
                    changed = True
    if placeholder:
        # The placeholders delivered with what is kept must not match either.
        (_lookup, _none), (tutor, _stand_ins) = calls(placeholder)
        delivered = [placeholder if name == "answers" and i in withheld["answers"] else text
                     for name, pairs in tutor for i, text in pairs if text]
        if binding.answer_guard(_JOIN.join(delivered)):
            placeholder = ""
    for index in withheld["answers"]:
        turns[index]["answer_md"] = placeholder
    kept_gaps = [entry for i, entry in enumerate(gaps) if i not in withheld["gaps"]]
    kept_others = []
    for i, entry in enumerate(others):
        if i in withheld["problems"]:
            entry = {**entry, "problem": ""}
        kept_others.append(entry)
    # The bridge's open questions are the kept gap statements, the learner's
    # own steps follow as given (only the problem line, source text, guarded).
    open_questions = open_question_work(kept_gaps) if bridged else []
    return BoundDelivery(
        thread=turns, gaps=kept_gaps,
        misconceptions=None if records is None else [r for i, r in enumerate(records)
                                                     if i not in withheld["misconceptions"]],
        learner_work=[*open_questions, *kept_others],
        withheld={name: len(indexes) for name, indexes in withheld.items() if indexes},
    )


def guard_thread(thread: Sequence[Mapping[str, Any]], binding: BoundAsk | None) -> tuple[list[dict[str, Any]], int]:
    """The thread alone (a call that carries no other model-written text, retrieval off):
    :func:`plan_bound_delivery`'s ``thread`` and how many earlier answers it left out."""

    plan = plan_bound_delivery(binding, thread=thread)
    return plan.thread, plan.withheld.get("answers", 0)


@dataclass
class ReaderTutorRequest:
    """What the adapter hands ``tutor_qa.ask_question(reader_tutor=...)``.

    ``retrieve`` returns ``(spans or None, manifest)``: None when nothing was
    retrieved (verification could not run, a cold administration, a failure),
    so the tutor keeps today's delivery and no abstention is claimed; ``[]``
    with ``manifest["books_cover"] is False`` when verification ran and kept
    no passage. Bound, it is called with the inputs
    :func:`plan_bound_delivery` kept (``inputs``: the gap statements and the
    misconceptions its query and verification use). ``learner_work`` is the
    bridge's context (empty unless personalized); ``gaps`` and
    ``misconceptions`` are the lookup's model-written inputs as read (fix
    round 7: the plan withholds from them, then the lookup builds its query
    from what is kept). The item a workbench session binds the question to,
    its guards and its accounting are NOT here: they are the
    :class:`BoundAsk`, which holds with retrieval off too (fix round 5, R1)."""

    retrieve: Callable[..., tuple[list[dict[str, Any]] | None, dict[str, Any]]] | None = None
    intent: str = "explain"
    personalized: bool = True
    learner_work: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    misconceptions: list[Any] | None = None
    #: The caller's derived policy (``reading``, ``assisted_practice`` or
    #: ``cold_attempt``), kept apart from the binding so a cold
    #: administration is never read as ``reading`` (Codex review F2).
    policy: str = "reading"
    #: "Another way": every passage the inquiry has shown (its exchanges'
    #: selections, citations, excerpts and retrieved passages, and the
    #: passages its pressed offers showed). No new excerpt or citation shown
    #: may be one of them (Codex review F7); they stay in the tutor's context.
    shown_span_keys: Sequence[str] = ()


def run_retrieval(request: ReaderTutorRequest, inputs: Mapping[str, Any] | None = None,
                  ) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    """The injected retrieval; any failure keeps today's delivery (retrieval is context).
    ``inputs`` (bound): the plan's kept gap statements and misconceptions."""

    if request.retrieve is None:
        return None, {"status": "not_run", "books_cover": None}
    try:
        spans, manifest = request.retrieve(inputs=dict(inputs)) if inputs is not None else request.retrieve()
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
    "BoundAsk",
    "EARLIER_ANSWER_LEFT_OUT",
    "MAX_BRIDGE_CHARS",
    "MAX_EXCERPT_CHARS",
    "MIN_EXCERPT_CHARS",
    "MODES",
    "ReaderTutorRequest",
    "deliver",
    "delivery_receipt",
    "displayed_text",
    "finalize",
    "BoundDelivery",
    "QUERY_GAPS",
    "guard_thread",
    "open_question_work",
    "plan_bound_delivery",
    "run_retrieval",
    "verify_excerpt",
    "withhold",
    "withhold_for_call",
]
