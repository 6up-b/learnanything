"""Router R2a: the learner-facing "why" of a plan block, in plain words.

Plan §7 (docs/specs/plan_router_r2_v1.md) and the UX rules
(docs/specs/ux_learnloop_v1.md): the why is a short plain sentence behind the
block's ``why`` toggle, with the receipts one more click away
(``details``); no lane names, probabilities, ids, versions or internal terms
on the surface (the frictionless principle: quiet, honest, no jargon).

Each block candidate carries a **reason code** the staged frame computed from
its lane and items; this module turns the code into a sentence. DL1's
lane-prefixed reasons (``"maintain: 2 reviews past ..."``) stay as the logged
``reason`` on the candidate; they are never the router's surface copy.

:data:`DENY_PATTERNS` is the server-side twin of the desktop's copy deny-list
(``apps/learnloop-tauri/src/copy/denyList.ts``) plus the router plan's own
terms; a test runs every sentence this module can produce through it.

A leaf module: pure strings, no imports beyond the standard library.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any

WHY_VERSION = "router_why_v1"

#: Reason code -> sentence. ``{topic}`` is the block's topic phrase
#: (:func:`topic_phrase`), ``{section}`` a reading block's section title.
SENTENCES: Mapping[str, str] = {
    "repair_followup": "Following up today's mistakes on {topic}.",
    "repair_open_problem": "Another go at something still unclear in {topic}.",
    "repair_recent_errors": "Another go at {topic}, where recent answers slipped.",
    "review": "{topic} again, before it slips.",
    "assumed_check": "To check you still know {topic}, without hints.",
    "gap_check_added": "A quick check on {topic}, added from your question.",
    "gap_check_sooner": "A check on {topic}, brought forward by your question.",
    "project_check": "A question about your project's code, while it's fresh.",
    "check_once": "Your one check on {topic}.",
    "scheduled_checks": "A few short checks on {topic}.",
    "new_material": "Next: {topic}.",
    "reading": "Next: reading {section}.",
    "goal_step": "A step toward your goal: {topic}.",
    "requested": "You asked for this.",
    "followup_only": "Following up today's mistakes.",
    "stop_minutes_used": "That's today's time.",
    "stop_nothing_fits": "Nothing else worth doing fits today.",
}

#: The ``details`` line of a block the plan's rule chose (no model asked).
DETAILS_STAGED = "Picked by the plan's usual rule; no model was asked."

#: The server-side copy deny-list. Each entry: (reported term, pattern).
DENY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (term, re.compile(pattern, re.IGNORECASE))
    for term, pattern in (
        # The desktop list (denyList.ts, UX §9).
        ("vault", r"\bvault"),
        ("canonical", r"\bcanonical"),
        ("learning object", r"\blearning object"),
        ("LO", r"\bLOs?\b"),
        ("facet", r"\bfacet"),
        ("study map", r"\bstudy map"),
        ("practice item", r"\bpractice item"),
        ("extraction", r"\bextract"),
        ("ingest", r"\bingest"),
        ("inventory", r"\binventory"),
        ("synthesis", r"\bsynthes[ie]s\b|\bsynthesi[sz]e"),
        ("source set", r"\bsource set"),
        ("shard", r"\bshard"),
        ("bootstrap", r"\bbootstrap"),
        ("proposal", r"\bproposal"),
        ("AI inbox", r"\bAI inbox"),
        ("auto_apply", r"auto_apply|review_required"),
        ("primary_textbook", r"primary_textbook|alternate_explanation|problem_set\b"),
        ("token", r"\btoken"),
        ("consent", r"\bconsent"),
        ("registry", r"\bregistry"),
        ("probe", r"\bprobe"),
        ("EVSI", r"\b(EVSI|VOI|EIG)\b"),
        ("entropy", r"\bentropy"),
        ("posterior", r"\bposterior"),
        ("Brier", r"\bBrier"),
        ("calibration", r"\bcalibrat"),
        ("mastery", r"\bmastery"),
        ("certified", r"\bcertif"),
        ("primed", r"\bprimed"),
        ("cold check", r"\bcold check"),
        ("system debt", r"\b(system|content) debt\b"),
        ("misconception", r"\bmisconception"),
        ("hypothesis", r"\bhypothes[ie]s\b"),
        ("rubric", r"\brubric"),
        ("blueprint", r"\bblueprint"),
        ("scheduler", r"\bscheduler"),
        ("overdue", r"\boverdue"),
        ("provenance", r"\bprovenance"),
        ("bbox", r"\bbbox"),
        ("manifest", r"\bmanifest"),
        ("sidecar", r"\bsidecar"),
        ("codex", r"\bcodex"),
        ("mvp-0", r"\bmvp-0"),
        ("adjudication", r"\badjudicat"),
        ("marker", r"\bmarker\b|\bpypdf\b"),
        ("OCR", r"\bOCR\b"),
        # The router plan's own (plan §7 guards).
        ("lane", r"\blanes?\b|^(repair|maintain|new|push):"),
        ("propensity", r"\bpropensit"),
        ("Decider", r"\bdecider"),
        ("staged", r"\bstaged\b"),
        ("queue", r"\bqueue"),
        ("due", r"\bdue\b"),
        ("EVSI cost", r"\bvalue of information"),
        ("chooser", r"\bchooser"),
        ("planner value", r"\bplanner"),
        ("candidate", r"\bcandidate"),
    )
)


def jargon_in(text: str) -> list[str]:
    """The internal terms ``text`` shows, in deny-list order."""

    return [term for term, pattern in DENY_PATTERNS if pattern.search(text or "")]


def topic_phrase(titles: Sequence[str]) -> str:
    """"Eigenvalues", "Eigenvalues and Bases", "Eigenvalues and 2 more topics"."""

    names = [str(title).strip() for title in dict.fromkeys(titles) if str(title or "").strip()]
    if not names:
        return "this topic"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} and {len(names) - 1} more topics"


def sentence(code: str, *, topic: str | None = None, section: str | None = None) -> str:
    """The plain sentence for a reason code ("" for an unknown code)."""

    template = SENTENCES.get(code)
    if template is None:
        return ""
    text = template.format(topic=topic or "this topic", section=section or "the next section")
    # A topic phrase opens some sentences: keep its own capitalisation, but a
    # sentence never starts in lower case.
    return text[:1].upper() + text[1:]


#: A P2 run step the staged rule deferred (D13), by the veto's family.
DEFERRALS: Mapping[str, str] = {
    "hard_exposure_collision": "This step waits for a question you haven't seen yet.",
    "assessment_reservation": "This step waits: the question it needs is kept for your final check.",
    "evsi": "This step waits a little: a fresh question or a short break will make it count.",
    "other": "This step can't run right now; it will be offered again later.",
}


def deferral_sentence(veto_reason: str | None) -> str:
    """The one plain sentence a deferred P2 step shows (``constraint:<key>:<reason>``
    or ``evsi:<reason>`` from ``controller_cutover``)."""

    reason = str(veto_reason or "")
    if reason.startswith("evsi:"):
        return DEFERRALS["evsi"]
    if reason.startswith("constraint:"):
        key = reason.split(":")[1] if reason.count(":") >= 1 else ""
        return DEFERRALS.get(key, DEFERRALS["other"])
    return DEFERRALS["other"]


def stop_code(minutes_left: float, stop_offer_minutes: float) -> str:
    return "stop_minutes_used" if float(minutes_left) < float(stop_offer_minutes) else "stop_nothing_fits"


# -- router R2b: the "why" of a block the mixture chose (plan §7) ---------------------------

#: The version of the mixture's copy (the staged copy keeps ``router_why_v1``).
MIXTURE_WHY_VERSION = "router_why_v2"
#: The model-written mark (UX §1461): a model wrote this text.
MODEL_MARK = "◇"
#: D7, verbatim: the Decider explains nothing, so the label says what happened.
PICKED_BY_MODEL = "LearnLoop's model picked this among {count} close options."
#: Owner Q12 (2026-10-13): an exploration-floor draw.
PICKED_TO_VARY = "Picked to vary the order today."

#: Who chose, in the ``details`` line (plain words; no model names or ids).
DRAWN_DETAILS: Mapping[str, str] = {
    "staged": "This time the usual rule's pick was drawn.",
    "decider": "This time the first model's pick was drawn (that model gives no reasons).",
    "llm": "This time the second model's pick was drawn.",
    "uniform": "This time a random pick was drawn, to vary the order.",
}
WEIGHED_DETAILS = "LearnLoop's two models and the plan's usual rule were weighed."
NOT_READY_DETAILS = "LearnLoop's models aren't set up, so the plan's usual rule chose; no model was asked."
ONLY_RULE_DETAILS = "Only the plan's usual rule may pick this block, so no model was asked."
SINGLE_OPTION_DETAILS = "There was only one sensible option, so no model was asked."
HIDDEN_RATIONALE_DETAILS = "The model's own words are kept with the receipt."
MODEL_NAMES: Mapping[str, str] = {"decider": "first model", "llm": "second model"}
FALLBACK_REASONS: Mapping[str, str] = {
    "timeout": "didn't answer in time",
    "failed": "couldn't be reached",
    "invalid": "gave an answer that couldn't be used",
    "spend": "wasn't asked: today's model budget is used",
    "not_ready": "isn't set up",
    "unreachable": "couldn't be reached",
}
#: The restraint decision's copy (a follow-up that waits for the next block).
FOLLOWUP_WAITS = "A follow-up from your answer waits for the next block, so this one isn't interrupted."


def model_why(
    component: str,
    rule_sentence: str,
    *,
    option_count: int,
    rationale: str | None = None,
    rationale_shown: bool = False,
) -> tuple[str, str]:
    """``(why, why_kind)`` of a block the mixture chose, by the component that drew it.

    * the usual rule: its own sentence (``computed``);
    * the Decider (no rationale, D7): "LearnLoop's model picked this among N
      close options." and the rule's sentence (``model_no_rationale``);
    * the LLM: its rationale, marked as written by a model (``model_written``),
      when the guard passed; else the Decider-style label and the rule's sentence;
    * the exploration floor: "Picked to vary the order today." and the rule's
      sentence (``computed``, owner Q12).
    """

    rule = (rule_sentence or "").strip()
    if component == "llm" and rationale_shown and rationale:
        return f"{MODEL_MARK} {' '.join(rationale.split())}", "model_written"
    if component in ("decider", "llm"):
        label = PICKED_BY_MODEL.format(count=int(option_count))
        return f"{label} {rule}".strip(), "model_no_rationale"
    if component == "uniform":
        return f"{PICKED_TO_VARY} {rule}".strip(), "computed"
    return rule, "computed"


_SENTENCE_END = re.compile(r"[.!?](?:\s|$)")
_PROBABILITY_TEXT = re.compile(r"\b\d+(?:\.\d+)?\s*%|\b0\.\d+\b")


def rationale_guard(
    rationale: str | None,
    evidence_ids: Sequence[str],
    card_evidence_ids: Sequence[str] | set[str] | frozenset[str],
    *,
    max_sentences: int = 3,
) -> str | None:
    """Why the LLM's rationale may not be shown, or None when it may (plan §7 guards).

    Not shown: empty text, more than ``max_sentences`` sentences, an internal
    term (:data:`DENY_PATTERNS`), a number that reads as a probability, or an
    evidence id that is not on the card. The text stays in the payload and the
    block shows the Decider-style label with the rule's reason instead."""

    text = " ".join(str(rationale or "").split())
    if not text:
        return "empty"
    if len(_SENTENCE_END.findall(text + " ")) > max_sentences:
        return "too_long"
    if jargon_in(text):
        return "jargon"
    if _PROBABILITY_TEXT.search(text):
        return "probability"
    allowed = set(card_evidence_ids)
    if any(evidence_id not in allowed for evidence_id in evidence_ids):
        return "unknown_evidence"
    return None


def mixture_details(summary: Mapping[str, Any], *, propensity: Any, decision_ref: str | None) -> str:
    """The ``details`` line of a block decided under the mixture: plain words, then the receipt."""

    lines: list[str] = []
    status = summary.get("decided_by")
    if status == "not_ready":
        lines.append(NOT_READY_DETAILS)
    elif status == "irreversible":
        lines.append(ONLY_RULE_DETAILS)
    elif status == "single_option":
        lines.append(SINGLE_OPTION_DETAILS)
    else:
        lines.append(WEIGHED_DETAILS)
        drawn = DRAWN_DETAILS.get(str(summary.get("drawn_component") or ""))
        if drawn:
            lines.append(drawn)
        for name, reason in sorted((summary.get("fallback_reasons") or {}).items()):
            words = FALLBACK_REASONS.get(str(reason))
            if words and name in MODEL_NAMES:
                lines.append(f"The {MODEL_NAMES[name]} {words}, so its share went to the usual rule.")
        if isinstance(propensity, (int, float)) and not isinstance(propensity, bool) and 0 < propensity < 1:
            lines.append(f"This pick had a {max(1, round(100 * float(propensity)))}% chance.")
        if summary.get("rationale_hidden"):
            lines.append(HIDDEN_RATIONALE_DETAILS)
    evidence = [str(label) for label in summary.get("evidence_labels") or () if label]
    if evidence:
        lines.append("Based on " + "; ".join(evidence) + ".")
    if decision_ref:
        lines.append(f"Receipt: learnloop router log --decision {decision_ref}")
    return " ".join(lines)


__all__ = [
    "DEFERRALS",
    "DENY_PATTERNS",
    "DETAILS_STAGED",
    "DRAWN_DETAILS",
    "FALLBACK_REASONS",
    "FOLLOWUP_WAITS",
    "MIXTURE_WHY_VERSION",
    "MODEL_MARK",
    "PICKED_BY_MODEL",
    "PICKED_TO_VARY",
    "SENTENCES",
    "WHY_VERSION",
    "deferral_sentence",
    "jargon_in",
    "mixture_details",
    "model_why",
    "rationale_guard",
    "sentence",
    "stop_code",
    "topic_phrase",
]
