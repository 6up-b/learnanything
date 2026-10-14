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


__all__ = [
    "DEFERRALS",
    "DENY_PATTERNS",
    "DETAILS_STAGED",
    "SENTENCES",
    "WHY_VERSION",
    "deferral_sentence",
    "jargon_in",
    "sentence",
    "stop_code",
    "topic_phrase",
]
