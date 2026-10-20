"""How many: randomized dose offers in the Reader (spec_adaptive_difficulty_v1 §5.12, D21; switch ``reading_dose_offers``).

A small micro-randomized arm, live by owner decision (D21), outside the
successor: at an eligible section boundary it randomizes whether one *extra*
worked example or in-passage question is offered, within a friction budget,
with exact propensities logged on ``ad_dose_offers`` before anything is shown
(A7). Off: today's Reader exactly (no draw, no offer, no row).

**The decision point**: a section boundary where the existing quick-check
conditions hold (anchor mode with section prompts on), the section maps to at
least one LO, the cue density is not off, the Reader is not in skim mode, the
section is not the passage the learner was restored to, and the budget has
room: at most one extra offer per section and ``dose_daily_offers`` a day (a
function of the logged offers, so which sections were eligible rebuilds).

**The variants**: ``none`` (the Reader as it is); ``extra_worked_example`` (one
more worked example on the section's LO, from the learner's sources, found by
its role, cited by the LO's provenance and not yet studied; no model writes
one); ``extra_question`` (one more in-passage question on the section, from the
existing quick-check producer within its caps: a produced, unanswered question
of the section other than the one already showing). A variant whose content
cannot be had now is infeasible, leaves the support, and both facts are logged.

**The draw** (``reading_dose_v1``): ``π(v) = (1 - k·ε)·base(v) + ε`` over the
``k`` feasible variants (the randomization layer's ``reading_dose`` design),
floor ``ε = dose_floor``, base all on ``none``; seed ``seed_for(visit, section)``.

**Uptake** rows (``delivered``, ``not_delivered``, ``taken``, ``dismissed``)
append and never change the draw. A taken extra becomes an ordinary reading
opportunity of its kind with the offer's id on its receipt (AD1's sweep). A
dismissal is never read as low ability: nothing here touches the state,
evidence or scheduling, and no salience magnitude is read (A12).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.stores import ad_serving as store

from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.successor import dose_offers_on

DOSE_VERSION = "reading_dose_v1"
BASE_VERSION = "reading_dose_base_none_v1"
NONE = "none"
EXTRA_EXAMPLE = "extra_worked_example"
EXTRA_QUESTION = "extra_question"
VARIANTS = (NONE, EXTRA_EXAMPLE, EXTRA_QUESTION)
UPTAKE = ("delivered", "not_delivered", "taken", "dismissed")
OFFER_TEXT = {
    EXTRA_EXAMPLE: "One more worked example on this?",
    EXTRA_QUESTION: "A quick question on this section?",
}
WHY_TEXT = "Offered at random, to learn how much of this helps you"


@dataclass(frozen=True)
class Boundary:
    """What the Reader knows at the section boundary (no magnitude: no dwell, scroll or time)."""

    visit_id: str
    extraction_id: str
    section_id: str
    boundary_checks_available: bool = True
    cue_density_off: bool = False
    skim: bool = False
    restored_section: bool = False
    showing_question_id: str | None = None


@dataclass
class DoseDecision:
    eligible: bool
    reason: str | None = None
    draw_id: str | None = None
    variant: str | None = None
    propensities: Mapping[str, float] = field(default_factory=dict)
    content: Mapping[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        offer = None
        if self.variant not in (None, NONE):
            offer = {"draw_id": self.draw_id, "variant": self.variant, "text": OFFER_TEXT[self.variant],
                     "why": WHY_TEXT, "content": dict(self.content or {})}
        return {"eligible": self.eligible, "reason": self.reason, "draw_id": self.draw_id, "offer": offer}


def _day(stamp: str) -> str:
    parsed = parse_utc(stamp)
    return parsed.date().isoformat() if parsed is not None else str(stamp)[:10]


def budget(connection: Any, *, extraction_id: str, section_id: str, now: str, daily: int) -> str | None:
    """Why the friction budget has no room (None when it has): one extra per section, ``daily`` a day."""

    rows = [row for row in store.dose_rows(connection) if row["row_kind"] == "draw"]
    extras = [row for row in rows if row.get("chosen_variant") not in (None, NONE)]
    if any(row.get("extraction_id") == extraction_id and row.get("section_id") == section_id for row in extras):
        return "section_offered"
    today = _day(now)
    if sum(1 for row in extras if _day(str(row["created_at"])) == today) >= int(daily):
        return "daily_budget"
    return None


def _studied_examples(connection: Any, view: Any, learning_object_ids: Sequence[str]) -> set[str]:
    studied: set[str] = set()
    for row in view.reading_opportunities(connection, learning_object_ids=learning_object_ids):
        if row.get("kind") != "worked_example":
            continue
        # worked_example:<extraction>/<span>:<lo>
        parts = str(row.get("opportunity_key") or "").split(":")
        if len(parts) >= 2:
            studied.add(parts[1])
    return studied


def feasible_variants(vault: Any, repository: Any, connection: Any, boundary: Boundary,
                      learning_object_ids: Sequence[str], *, reading_map: Any = None, view: Any = None
                      ) -> tuple[list[str], dict[str, str], dict[str, dict[str, Any]]]:
    """``(feasible, infeasible with why, each extra's content)``. ``none`` is always feasible.
    Every extra comes through the operation's material view (A8; Codex verify F23): a worked
    example on held-out material, or a question whose section, anchors or cited spans are held
    out, is never offered."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.reading import VaultReadingMap

    view = material_view(vault, repository, view)
    mapping = reading_map or VaultReadingMap(vault, repository, view)
    feasible = [NONE]
    infeasible: dict[str, str] = {}
    content: dict[str, dict[str, Any]] = {}
    studied = _studied_examples(connection, view, learning_object_ids)
    section_spans = set(mapping.section_spans(boundary.extraction_id, boundary.section_id))
    example = None
    for span in sorted(mapping.worked_example_spans(boundary.extraction_id)):
        key = f"{boundary.extraction_id}/{span}"
        if key in studied or span in section_spans or mapping.withheld(boundary.extraction_id, span) \
                or view.material_withheld(boundary.extraction_id, span):
            continue
        if set(mapping.los_for_span(boundary.extraction_id, span)) & set(learning_object_ids):
            example = {"extraction_id": boundary.extraction_id, "span_id": span}
            break
    if example is not None:
        feasible.append(EXTRA_EXAMPLE)
        content[EXTRA_EXAMPLE] = example
    else:
        infeasible[EXTRA_EXAMPLE] = "no_unstudied_example"
    question = None
    for row in view.open_questions(connection, boundary.extraction_id, boundary.section_id):
        if str(row["id"]) == str(boundary.showing_question_id or "") or str(row["question_style"]) == "reconstruct":
            continue
        question = {"question_id": str(row["id"]), "style": str(row["question_style"])}
        break
    if question is not None:
        feasible.append(EXTRA_QUESTION)
        content[EXTRA_QUESTION] = question
    else:
        infeasible[EXTRA_QUESTION] = "no_producer_result"
    return feasible, infeasible, content


def dose_taken(connection: Any, learning_object_ids: Sequence[str], *, view: Any) -> dict[str, int]:
    """The dose of each offered kind already taken in the window at the decision (the moderator of
    the randomized dose-response, §5.12): recorded opportunities on the section's LOs since their
    last graded attempt. A count of facts, never a magnitude.

    Codex verify F26: the window is the replay's, read through the material view: it closes at the
    LOs' last visible attempt that closes a window (graded, not a skip or self-report;
    ``material_view.closes_window``), never at an ungraded, skipped or withheld one, and only
    receipts whose source is visible count."""

    out = {"worked_example": 0, "in_passage_question": 0}
    if not learning_object_ids:
        return out
    last = view.window_cutoff(connection, learning_object_ids) or ""
    for kind in out:
        sources = {str(row.get("source_id")) for row in view.reading_opportunities(
            connection, learning_object_ids=learning_object_ids)
            if row.get("kind") == kind and not str(row.get("subkind") or "").startswith("self_check:")
            and str(row.get("source_written_at") or "") > last}
        out[kind] = len(sources)
    return out


def _forecast(vault: Any, repository: Any, connection: Any, learning_object_id: str, *,
              view: Any) -> float | None:
    """The AD forecast fixed before the draw (a precision covariate, never an input of the draw)."""

    try:
        from learnloop.adaptive_difficulty import predict as PR
        from learnloop.adaptive_difficulty import replay as RP
        from learnloop.adaptive_difficulty.generation import lo_cell_facet

        snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
        facet = lo_cell_facet(view, learning_object_id)
        if facet is None:
            return None
        lo = vault.learning_objects.get(learning_object_id)
        subject = (list(getattr(lo, "subjects", None) or []) or ["default"])[0]
        point = S.entry_point("retrieval")
        spec = PR.point_spec(point or {}, learning_object_id=learning_object_id, subject=subject, facet=facet,
                             capability_name="retrieval")
        return round(PR.predict(snapshot.subject, spec).p_bar, 8)
    except Exception:  # noqa: BLE001 - a missing covariate never blocks the draw
        return None


def decide(vault: Any, repository: Any, boundary: Boundary, *, clock: Clock | None = None,
           reading_map: Any = None, view: Any = None) -> DoseDecision:
    """At a section boundary: eligibility, the budget, the draw, and its row before anything is shown.

    One material view for the decision (``view``: the RPC's, else computed here). With the held-out
    predicate unavailable no draw is made (``protection_unavailable``). A draw made earlier is
    returned only while its extra is still visible; one whose content is withheld now is returned
    with no offer (``withheld``; Codex verify F23)."""

    if not dose_offers_on(vault.config):
        return DoseDecision(False, "switch_off")
    if not boundary.boundary_checks_available:
        return DoseDecision(False, "no_boundary_checks")
    if boundary.cue_density_off:
        return DoseDecision(False, "density_off")
    if boundary.skim:
        return DoseDecision(False, "skim")
    if boundary.restored_section:
        return DoseDecision(False, "restored_section")
    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.reading import VaultReadingMap

    view = material_view(vault, repository, view)
    if not view.available:
        return DoseDecision(False, "protection_unavailable")
    mapping = reading_map or VaultReadingMap(vault, repository, view)
    los = list(mapping.los_for_section(boundary.extraction_id, boundary.section_id))
    if not los:
        return DoseDecision(False, "no_learning_object")
    now = utc_now_iso(clock)
    settings = vault.config.adaptive_difficulty
    with repository.atomic():
        connection = repository.connection()
        if not store.has_table(connection, store.DOSE_OFFERS):
            return DoseDecision(False, "schema")
        key = f"{boundary.visit_id}:{boundary.extraction_id}:{boundary.section_id}"
        existing = store.dose_draw_by_key(connection, key)
        if existing is not None:
            if offer_withheld(connection, view, existing.get("chosen_variant"), existing.get("content")):
                return DoseDecision(True, "withheld", str(existing["id"]), NONE, existing.get("propensities") or {},
                                    None)
            return DoseDecision(True, "drawn", str(existing["id"]), existing.get("chosen_variant"),
                                existing.get("propensities") or {}, existing.get("content"))
        why = budget(connection, extraction_id=boundary.extraction_id, section_id=boundary.section_id, now=now,
                     daily=int(settings.dose_daily_offers))
        if why is not None:
            return DoseDecision(False, why)
        feasible, infeasible, content = feasible_variants(vault, repository, connection, boundary, los,
                                                          reading_map=mapping, view=view)
        from learnloop.scheduling.randomization_layer import READING_DOSE, draw_from, reading_dose_propensities

        pi = reading_dose_propensities(feasible, {NONE: 1.0}, float(settings.dose_floor))
        seed = S.seed_for(DOSE_VERSION, f"{boundary.visit_id}:{boundary.section_id}")
        u = S.uniform(seed)
        chosen = draw_from(pi, u)
        draw_id = store.insert_dose_row(connection, {
            "row_kind": "draw", "draw_key": key, "visit_id": boundary.visit_id,
            "extraction_id": boundary.extraction_id, "section_id": boundary.section_id,
            "learning_object_ids": los, "feasible": feasible, "infeasible": infeasible,
            "base_version": BASE_VERSION, "floor": float(settings.dose_floor),
            "propensities": {v: round(p, 12) for v, p in sorted(pi.items())}, "seed": seed, "u": u,
            "chosen_variant": chosen, "content": content.get(chosen),
            "forecast_p": _forecast(vault, repository, connection, los[0], view=view),
            "detail": {"design": READING_DOSE, "version": DOSE_VERSION, "showing_question_id":
                       boundary.showing_question_id, "dose_taken": dose_taken(connection, los, view=view)},
            "created_at": now,
        })
    return DoseDecision(True, None, draw_id, chosen, pi, content.get(chosen))


def offer_withheld(connection: Any, view: Any, variant: Any, content: Any) -> bool:
    """Whether a drawn extra's content is withheld now (revalidated before it is shown again)."""

    content = content or {}
    if variant == EXTRA_QUESTION:
        return view.question(connection, content.get("question_id")) is None
    if variant == EXTRA_EXAMPLE:
        return view.material_withheld(content.get("extraction_id"), content.get("span_id"))
    return False


def record_uptake(vault: Any, repository: Any, draw_id: str, kind: str, *, clock: Clock | None = None) -> str:
    """Append ``delivered``, ``not_delivered``, ``taken`` or ``dismissed`` (never changing the draw)."""

    if kind not in UPTAKE:
        raise ValueError(f"unknown dose uptake {kind!r}")
    with repository.atomic():
        connection = repository.connection()
        draw = next((row for row in store.dose_rows(connection) if row["id"] == draw_id and row["row_kind"] == "draw"),
                    None)
        if draw is None:
            raise ValueError(f"no dose draw {draw_id!r}")
        if draw.get("chosen_variant") in (None, NONE):
            raise ValueError("the draw offered nothing")
        return store.insert_dose_row(connection, {"row_kind": kind, "draw_id": draw_id,
                                                  "created_at": utc_now_iso(clock)})


def taken_offers(connection: Any) -> dict[str, str]:
    """Each taken extra's content key -> its draw id (a reading opportunity carries the id)."""

    rows = store.dose_rows(connection)
    taken = {row["draw_id"] for row in rows if row["row_kind"] == "taken"}
    out: dict[str, str] = {}
    for row in rows:
        if row["row_kind"] != "draw" or row["id"] not in taken:
            continue
        content = row.get("content") or {}
        if content.get("question_id"):
            out[f"question:{content['question_id']}"] = str(row["id"])
        if content.get("span_id"):
            out[f"span:{content.get('extraction_id')}/{content['span_id']}"] = str(row["id"])
    return out


__all__ = [
    "BASE_VERSION",
    "Boundary",
    "DOSE_VERSION",
    "DoseDecision",
    "EXTRA_EXAMPLE",
    "EXTRA_QUESTION",
    "NONE",
    "OFFER_TEXT",
    "UPTAKE",
    "VARIANTS",
    "WHY_TEXT",
    "budget",
    "decide",
    "dose_taken",
    "feasible_variants",
    "offer_withheld",
    "record_uptake",
    "taken_offers",
]
