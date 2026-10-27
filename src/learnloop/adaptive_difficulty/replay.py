"""The AD replayer: both views from ledgers and receipts, zero model calls (spec_adaptive_difficulty_v1 §5.6, §11.3).

The AD state is a pure function of the attempt ledger, the
``item_serve_inputs`` and ``ad_reading_opportunities`` receipts (the latter
read only through the reading-signal firewall's carve-out,
``salience_firewall.learning_opportunity_events``), the ``judgment_ledger``
audit and relatedness rows with the adopted coupling versions,
``practice_item_snapshots``, the allowlisted claims, ``ad_priors_v1`` and
``ad_hyper_v1``. Current vault content is read only for a historical attempt
resolved ``reconstructed_current`` under AD's history fallback (§7.5;
``adaptive_difficulty.history_fallback``, ``"current_content"`` by owner decision 2026-10-19),
and for the facet-to-LO map the coupling structure uses. Outside forecasts
and the relatedness proposal are read from their rows, never re-asked.

**Two views** (§5.6): the **subject view** reads every eligible row and every
reading opportunity, with the learned relatedness, one filter per point of the
grid (or only its uniform-sharing points with ``learned_coupling`` off),
mixed by the learned weights; the **LO view** of an LO reads only the eligible
rows on its own items, at the fixed split, with no loadings, couplings or
reading.

**Eligibility** (§5.6 step 1): a graded attempt of an eligible type (deviation
D1: the four the spec lists plus ``hinted_attempt`` and ``dont_know``, which
the practice screen records for a hinted answer and an old "I don't know"),
the first graded attempt on its surface group, not held for review, with a
current grade that assesses something (not wholly PF-c unverified) and
positive effective mass before the item-dependent and assistance discounts
(not quarantined, unassessable, of a zero-mass type or of a grade that
measures nothing: ``field.outcomes.measurement_masses``, on the current grade's
surviving criterion rows), not on held-out material (A8), with usable inputs:
its frozen serve inputs, or a historical resolution that is not ``excluded``.
Assessment is resolved from the ledger whatever the inputs (Codex review F1).
``self_report`` rows never enter (D8). Every graded attempt other than ``self_report`` closes
its facets' reading windows.

**Order**: rows by ``(created_at, attempt id)``; a claim or a reading
opportunity written strictly before a row applies first. Rebuilds are
byte-identical (float64, fixed order).

Never evidence (A2, A12): this module writes only AD's DERIVED tables.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import bisect
import hashlib
import json
import logging
import math
import threading
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from learnloop.attempts.salience_firewall import learning_opportunity_events
from learnloop.clock import parse_utc
from learnloop.db.stores import ad_receipts as receipt_store
from learnloop.db.stores import ad_serving as serving_store

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import relatedness as R
from learnloop.adaptive_difficulty.state import ItemSpec, View, normalized_weights

LOG = logging.getLogger(__name__)

REPLAY_VERSION = "ad_replay_v1"
VIEW_SUBJECT = "subject"
CLAIM_SOURCES = ("init_wizard", "tutor_gap_declaration")
WARMTH_SOURCES = ("attempt", "reveal", "reading")


def lo_view_name(learning_object_id: str) -> str:
    return f"lo:{learning_object_id}"


def days(value: Any) -> float:
    parsed = parse_utc(str(value)) if value else None
    if parsed is None:
        raise ValueError(f"unreadable time {value!r}")
    return parsed.timestamp() / 86400.0


def _logit(p: float) -> float:
    p = min(max(float(p), 0.01), 0.99)
    return math.log(p / (1.0 - p))


# -- settings ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReplaySettings:
    """Which parts of the subject view run (the switches, and the harness arms of §10.4)."""

    coupling: bool = True
    reading: bool = True
    verdicts: bool = True
    hyper: str = P.HYPER_VERSION
    fixed_point: P.HyperPoint | None = None
    rating: bool = False
    timing: bool = False
    outside: bool = False
    updates: bool = True
    #: The report's prior sensitivity (§5.8): ``(coordinate, mean)`` overrides of ``ad_priors_v1``.
    prior_means: tuple[tuple[str, float], ...] = ()

    def key(self) -> str:
        return json.dumps({"coupling": self.coupling, "reading": self.reading, "verdicts": self.verdicts,
                           "hyper": self.hyper, "fixed": self.fixed_point.key() if self.fixed_point else None,
                           "rating": self.rating, "timing": self.timing, "outside": self.outside,
                           "updates": self.updates, "prior_means": [list(p) for p in self.prior_means]},
                          sort_keys=True)

    @classmethod
    def from_config(cls, config: Any) -> "ReplaySettings":
        section = getattr(config, "adaptive_difficulty", None)
        if section is None:
            return cls()
        coupling = bool(getattr(section, "learned_coupling", True))
        reading = bool(getattr(section, "reading_opportunities", True))
        verdicts = reading and bool(getattr(section, "reading_self_check", True))
        return cls(coupling=coupling, reading=reading, verdicts=verdicts)


# -- events -------------------------------------------------------------------------------

@dataclass
class AttemptEvent:
    attempt_id: str
    created_at: str
    at: float
    learning_object_id: str
    practice_item_id: str
    subject: str
    attempt_type: str
    eligible: bool
    reason: str | None
    input_status: str
    spec: ItemSpec | None
    category: int | None
    warmth: float
    served_at: str
    plan_presentation_id: str | None
    content_hash: str | None
    closes: tuple[str, ...]
    rating: str | None = None
    log_latency_ratio: float | None = None
    in_passage_kind: str | None = None
    correctness: float | None = None
    first_surface: bool = False


@dataclass
class ClaimEvent:
    claim_id: str
    created_at: str
    at: float
    scope: str  # "global" | "learning_object"
    learning_object_ids: tuple[str, ...]
    level: float


@dataclass
class OpportunityEvent:
    opportunity_id: str
    created_at: str
    at: float
    kind: str
    subkind: str
    learning_object_id: str
    subject: str
    facet_doses: dict[str, float]


@dataclass
class Events:
    attempts: list[AttemptEvent]
    claims: list[ClaimEvent]
    opportunities: list[OpportunityEvent]
    structure: R.VaultStructure
    lo_subject: dict[str, str]
    lo_facets: dict[str, list[str]]
    summary: dict[str, Any] = field(default_factory=dict)

    def ordered(self) -> list[tuple[str, Any]]:
        stream: list[tuple[tuple[float, int, str], str, Any]] = []
        stream += [((e.at, 0, e.attempt_id), "attempt", e) for e in self.attempts]
        stream += [((e.at, 1, e.claim_id), "claim", e) for e in self.claims]
        stream += [((e.at, 2, e.opportunity_id), "opportunity", e) for e in self.opportunities]
        stream.sort(key=lambda entry: entry[0])
        return [(kind, event) for _key, kind, event in stream]


def _capability(item: Any) -> str:
    capability = getattr(item, "capability", None)
    if capability in P.CAPABILITIES:
        return str(capability)
    try:
        from learnloop.learner.capability_mapping import default_capability_for

        mapped = default_capability_for(str(getattr(item, "practice_mode", "") or ""))
        return mapped if mapped in P.CAPABILITIES else "retrieval"
    except Exception:  # noqa: BLE001
        return "retrieval"


def _guess(vault: Any, item: Any) -> float:
    try:
        from learnloop.learner.blueprint_projection import guess_floor_for_item

        return float(guess_floor_for_item(item, vault.config))
    except Exception:  # noqa: BLE001
        return 0.0


def _facet_weights(vault: Any, item: Any) -> dict[str, float]:
    weights: dict[str, float] = {}
    raw = normalized_weights(getattr(item, "evidence_weights", None), getattr(item, "evidence_facets", None) or ())
    for facet, weight in raw.items():
        canonical = vault.canonical_facet_id(facet)
        weights[canonical] = weights.get(canonical, 0.0) + weight
    return weights


def _historical_signals(item: Any) -> dict[str, float]:
    signals: dict[str, float] = {}
    if getattr(item, "difficulty_source", None) == "llm_estimate" and getattr(item, "difficulty", None) is not None:
        signals["z_llm"] = 2.5 * (2.0 * float(item.difficulty) - 1.0)
    signals["z_origin"] = 0.0 if getattr(item, "canonical_exercise", None) is not None else 1.0
    return signals


def _frozen_signals(row: Mapping[str, Any]) -> dict[str, float]:
    signals: dict[str, float] = {}
    for name, entry in (receipt_store._loads(row.get("signals_json"), {}) or {}).items():
        if isinstance(entry, Mapping) and entry.get("available") and entry.get("value") is not None:
            signals[str(name)] = float(entry["value"])
    return signals


def _audited(connection: Any, item: Any, content_hash: str | None, as_of: str) -> dict[str, Any] | None:
    from learnloop.adaptive_difficulty.feature_audit import canonical_audits

    stamped = dict(item.task_features) if isinstance(getattr(item, "task_features", None), Mapping) else None
    resolved = dict(stamped or {})
    if content_hash:
        for dimension, audit in canonical_audits(connection, content_hash, as_of=as_of).items():
            resolved[dimension] = int(audit["value"]) if dimension == "complexity" else audit["value"]
    return resolved or None


def surface_group(item: Any) -> str:
    """The item's surface group (mirrors ``substrate.canonical_projection.surface_group_id``,
    pinned equal by a test): a shared stimulus, source-example or solution-template family,
    else the legacy surface family, else the item."""

    fp = getattr(item, "evidence_fingerprint", None)
    for candidate in (getattr(fp, "shared_stimulus_id", None), getattr(fp, "source_family", None),
                      getattr(fp, "solution_recipe_family", None), getattr(item, "surface_family", None)):
        if candidate:
            return str(candidate)
    return f"item:{item.id}"


def forced_failure(attempt: Mapping[str, Any]) -> bool:
    """§5.3's "an empty 'I'm stuck'" row (Codex review F2): only an empty stuck submission, or a
    historical "I don't know" answer, is a fail whatever its grade. A stuck learner who still
    wrote an answer is classified by its assessed correctness and help timing like any other."""

    if attempt.get("attempt_type") == "dont_know" or bool(attempt.get("declared_dont_know")):
        return True
    return bool(attempt.get("declared_stuck")) and not str(attempt.get("learner_answer_md") or "").strip()


def _type_mass(vault: Any, attempt_type: str) -> float:
    entry = getattr(getattr(vault.config, "evidence", None), "attempt_types", {}).get(attempt_type)
    return 1.0 if entry is None else float(getattr(entry, "evidence_mass", 1.0))


def _exposures(connection: Any, view: Any) -> dict[str, list[float]]:
    """Each LO's exposure times (attempts and reveals) for warmth, read through the material view:
    an attempt or reveal on a withheld item warms nothing (Codex verify F20)."""

    by_lo: dict[str, list[float]] = {}
    for row in [*view.attempts(connection), *view.reveals(connection)]:
        lo = row.get("learning_object_id")
        if lo:
            try:
                by_lo.setdefault(str(lo), []).append(days(row["created_at"]))
            except ValueError:
                continue
    return by_lo


def _warmth(exposures: Mapping[str, Sequence[float]], lo: str, served: float, own: float | None) -> float:
    """``w_t = exp(-Δh / h_w)`` with ``Δh`` the hours since the last exposure to the LO before the serve."""

    times = exposures.get(lo) or ()
    index = bisect.bisect_left(times, served)
    candidates = [t for t in times[:index] if own is None or t != own]
    if not candidates:
        return 0.0
    hours = (served - max(candidates)) * 24.0
    return float(math.exp(-hours / P.WARMTH_HOURS))


def _current_grade_unassessed(evidence: Sequence[Mapping[str, Any]], wholly_unassessed: Any) -> bool:
    """PF-c over the attempt's current grading epoch (``grading_epochs.current_epoch``), never a
    per-criterion merge of every live epoch (Codex re-review F1): a historical regrade that
    dropped a verified criterion and left its own criteria unverified measures nothing, though
    the dropped criterion's row from the first grade still stands."""

    from learnloop.grading_epochs import current_epoch

    epoch = current_epoch(evidence)
    return epoch is not None and wholly_unassessed(epoch.rows)


@entry(read_only=True)
def load_events(connection: Any, vault: Any, repository: Any, *, as_of: str | None = None,
                settings: ReplaySettings = ReplaySettings(), view: Any = None) -> Events:
    """Read every replay input (no model call; current content only for ``reconstructed_current``).

    Everything is read through the operation's material view (``view``; one is computed when the
    caller has none): a withheld item's attempts, reveals and reading receipts are invisible, so
    they train nothing, close no reading window, take no first surface and warm nothing; the
    facet maps name no facet only withheld items name; recorded reading receipts are
    revalidated against the current predicate (A8; Codex verify F19, F20). With the predicate
    unavailable the view is empty and the replay reads no item, attempt or receipt."""

    from learnloop.field.outcomes import wholly_unassessed
    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    structure = R.load_structure(connection, vault, view=view, coupled=settings.coupling)
    live = R.live_judgments(connection, view=view) if view.available else set()
    facet_to_los, lo_to_facets = view.facet_maps()
    lo_subject = {lo.id: R.lo_subject(vault, lo) for lo in vault.learning_objects.values()}
    limit = days(as_of) if as_of else math.inf
    summary: dict[str, Any] = {"input_status": {}, "excluded": {}, "eligible": 0, "attempts": 0}
    if not view.available:
        summary["protection"] = view.reason

    # The revision policy is AD's own (``adaptive_difficulty.history_fallback``, owner decision
    # 2026-10-19: by default a historical attempt is read against today's item text where its
    # exact revision was not saved); field's own default is untouched.
    from learnloop.adaptive_difficulty.successor import history_fallback

    rows = {row.attempt_id: row for row in view.field_rows(
        connection, legacy_fallback=history_fallback(vault.config))}
    # Graded, quarantine and the current epoch from the authoritative ledger itself (never from
    # field's revision resolution: an attempt with frozen serve inputs needs none).
    ledger = view.ledger(connection)
    # Whether the grade measures anything, resolved from the ledger alone (Codex review F1): a
    # frozen-input attempt skips field's revision resolution, never its assessment rule.
    # Read through the view, in the rules (a legacy interpretation's references are the incumbent's).
    masses = view.measurement_masses(connection, ledger)
    held = view.held_for_review(connection)
    serve_inputs: dict[str, dict[str, Any]] = {}
    for row in view.rows(connection, receipt_store.SERVE_INPUTS):
        if row.get("plan_presentation_id"):
            serve_inputs[str(row["plan_presentation_id"])] = row
    presentations = {pid: str(row["served_at"]) for pid, row in view.presentations(connection).items()}
    help_rows: dict[str, list[dict[str, Any]]] = {}
    for attempt_id, context, hint_eq, qtype, progress, seconds in [
            (row["attempt_id"], row["context"], row["hint_equivalent"], row["question_type"], row["attempt_progress"],
             row["seconds_into_attempt"]) for row in view.rows(connection, "question_events", "attempt_id IS NOT NULL")]:
        help_rows.setdefault(str(attempt_id), []).append({
            "context": context, "hint_equivalent": hint_eq, "question_type": qtype, "attempt_progress": progress,
            "seconds_into_attempt": seconds})
    def snapshot(content_hash: str | None) -> Any:
        # A saved revision through the view: None when it is withheld (its item, or its own sources).
        return view.revision(connection, content_hash)

    opportunities: list[OpportunityEvent] = []
    if receipt_store.has_table(connection, receipt_store.READING):
        # The firewall's carve-out is the only path from the receipt to AD's state (A12, §5.11);
        # the receipts reach it revalidated through the view (Codex verify F20).
        for record in learning_opportunity_events(view.reading_opportunities(connection)):
            try:
                at = days(record["source_written_at"])
            except ValueError:
                continue
            if at > limit:
                continue
            lo = record["learning_object_id"]
            opportunities.append(OpportunityEvent(
                record["opportunity_id"], record["source_written_at"], at, record["kind"], record["subkind"], lo,
                lo_subject.get(lo, "default"),
                {vault.canonical_facet_id(f): d for f, d in sorted(record["facet_doses"].items())}))
    exposures = _exposures(connection, view)
    for opportunity in opportunities:
        exposures.setdefault(opportunity.learning_object_id, []).append(opportunity.at)
    for times in exposures.values():
        times.sort()

    attempts: list[AttemptEvent] = []
    surfaces: set[str] = set()
    for attempt in view.attempts(connection):
        attempt_id = str(attempt["id"])
        try:
            at = days(attempt["created_at"])
        except ValueError:
            continue
        if at > limit:
            continue
        summary["attempts"] += 1
        row = rows.get(attempt_id)
        source = ledger.get(attempt_id) or {}
        attempt_type = str(attempt.get("attempt_type") or "")
        if not source.get("evidence") or attempt_type == "skip":
            continue  # ungraded: no window closes, no update
        if attempt_type == "self_report":
            continue  # D8: never read, and it closes no window
        presentation_id = attempt.get("plan_presentation_id")
        frozen = serve_inputs.get(str(presentation_id)) if presentation_id else None
        if frozen is not None:
            content_hash = str(frozen["content_hash"])
            item = snapshot(content_hash)
            status = "frozen" if item is not None else "excluded"
        elif row is None:
            item, content_hash, status = None, None, "excluded"
        elif row.revision_status == "exact":
            content_hash = row.item_snapshot_hash
            item = snapshot(content_hash)
            status = "exact" if item is not None else "excluded"
        elif row.revision_status == "reconstructed_current":
            item = view.item(attempt["practice_item_id"])
            content_hash = None
            status = "reconstructed_current" if item is not None else "excluded"
        else:
            item, content_hash, status = None, row.item_snapshot_hash, "excluded"
        if content_hash and view.revision_withheld(connection, content_hash):
            # The answered revision's own sources are held out now (a revision of a deleted item, or
            # one whose provenance differed): the attempt is invisible, as its item would be.
            summary["attempts"] -= 1
            continue
        lo = str(attempt["learning_object_id"])
        subject = str(attempt.get("subject") or lo_subject.get(lo) or "default")
        if item is not None:
            weights = _facet_weights(vault, item)
        else:
            raw_weights = receipt_store._loads(attempt.get("evidence_weights_json"), {})
            raw_facets = receipt_store._loads(attempt.get("evidence_facets_json"), [])
            weights = {vault.canonical_facet_id(f): w for f, w in normalized_weights(raw_weights, raw_facets).items()}
        if item is not None:
            surface = surface_group(item)
        elif row is not None and row.surface_group_id:
            surface = str(row.surface_group_id)
        else:
            surface = f"item:{attempt['practice_item_id']}"
        first_surface = surface not in surfaces
        surfaces.add(surface)
        served_at = presentations.get(str(presentation_id)) if presentation_id else None
        if served_at is None:
            served_at = str(frozen["served_at"]) if frozen is not None else str(attempt["created_at"])
        served = days(served_at)
        reason: str | None = None
        if attempt_type not in O.ELIGIBLE_TYPES:
            reason = "attempt_type"
        elif not first_surface:
            reason = "repeat_surface"
        elif attempt_id in held:
            reason = "held_for_review"
        elif _current_grade_unassessed(source["evidence"], wholly_unassessed):
            # PF-c: every criterion of the current grade unverified. It may schedule as correct;
            # it measures nothing (owner decision 2026-10-12), so it trains nothing and tests no cell.
            reason = "unassessed"
        elif (source.get("quarantine_state") == "quarantined" or attempt_type == "unassessable"
              or _type_mass(vault, attempt_type) <= 0 or masses.get(attempt_id, 0.0) <= 0):
            reason = "zero_mass"
        elif status == "excluded" or item is None or not weights:
            reason = "inputs_excluded"
        category = None
        if reason is None:
            facts = O.AttemptFacts(
                correctness=(float(attempt["correctness"]) if attempt.get("correctness") is not None
                             else (float(row.outcome) if row is not None else None)),
                hints_used=int(attempt.get("hints_used") or 0),
                first_hint_progress=attempt.get("first_hint_progress"),
                help_questions=O.help_questions_from_rows(help_rows.get(attempt_id, ())),
                primed=bool(attempt.get("primed")),
                pre_exposed=bool(frozen.get("pre_exposed")) if frozen is not None else False,
                bound_presentation=bool(presentation_id),
                stuck=forced_failure(attempt),
            )
            category = O.category(facts)
            if category is None:
                reason = "pre_exposed" if facts.pre_exposed else "primed_unbound"
        spec = None
        if item is not None and weights:
            if frozen is not None:
                features = receipt_store._loads(frozen.get("resolved_features_json"), None)
                signals = _frozen_signals(frozen)
                frozen_loadings = receipt_store._loads(frozen.get("loadings_json"), None)
                # Frozen inputs are read only at the epoch they were frozen under (round 2), so their
                # loadings stand as frozen; they name only judgments of runs in force (E2).
                loadings = ({str(f): float(q) for f, q in (frozen_loadings.get("loadings") or {}).items()}
                            if isinstance(frozen_loadings, Mapping) else structure.loadings(content_hash, -math.inf))
                if isinstance(frozen_loadings, Mapping) and not {
                        str(j) for j in (frozen_loadings.get("judgment_ids") or ())} <= live:
                    loadings = {}
            else:
                features = _audited(connection, item, content_hash, str(attempt["created_at"]))
                signals = _historical_signals(item)
                loadings = structure.loadings(content_hash, -math.inf)
            if not settings.outside:
                signals.pop("z_v1", None)
            spec = ItemSpec(str(attempt["practice_item_id"]), lo, subject, _capability(item), weights,
                            features=features, signals=signals,
                            loadings={vault.canonical_facet_id(g): q for g, q in loadings.items()},
                            guess=_guess(vault, item))
        rating = attempt.get("difficulty_rating")
        latency = attempt.get("latency_seconds")
        ratio = None
        if latency and settings.timing and item is not None:
            expected = float(getattr(item, "expected_minutes", None) or 0.0) * 60.0
            if expected > 0 and float(latency) > 0:
                ratio = math.log(float(latency) / expected)
        attempts.append(AttemptEvent(
            attempt_id, str(attempt["created_at"]), at, lo, str(attempt["practice_item_id"]), subject, attempt_type,
            reason is None, reason, status, spec, category,
            _warmth(exposures, lo, served, at), served_at, str(presentation_id) if presentation_id else None,
            content_hash, tuple(sorted(f for f, w in weights.items() if w > 0)),
            rating=rating if settings.rating else None, log_latency_ratio=ratio,
            correctness=float(attempt["correctness"]) if attempt.get("correctness") is not None else None,
            first_surface=first_surface,
        ))
        summary["input_status"][status] = summary["input_status"].get(status, 0) + 1
        if reason is None:
            summary["eligible"] += 1
        else:
            summary["excluded"][reason] = summary["excluded"].get(reason, 0) + 1

    claims: list[ClaimEvent] = []
    if serving_store.has_table(connection, "learner_claims"):
        cursor = connection.execute(
            "SELECT id, scope_type, scope_id, claimed_level, source, created_at FROM learner_claims "
            "ORDER BY created_at, id")
        concept_los: dict[str, list[str]] = {}
        for lo in vault.learning_objects.values():
            concept_los.setdefault(str(lo.concept), []).append(lo.id)
        for claim_id, scope_type, scope_id, level, source, created_at in cursor.fetchall():
            if source not in CLAIM_SOURCES:
                continue  # D8: rung_variant_request and learner_report claims are never read
            try:
                at = days(created_at)
            except ValueError:
                continue
            if at > limit:
                continue
            if source == "init_wizard" and scope_type == "global":
                claims.append(ClaimEvent(str(claim_id), str(created_at), at, "global", (), float(level)))
            elif source == "tutor_gap_declaration":
                los = ((str(scope_id),) if scope_type == "learning_object" else
                       tuple(concept_los.get(str(scope_id), ())) if scope_type == "concept" else ())
                if los:
                    claims.append(ClaimEvent(str(claim_id), str(created_at), at, "learning_object", los,
                                             float(level)))
    summary["claims"] = len(claims)
    summary["opportunities"] = len(opportunities)
    return Events(attempts, claims, opportunities, structure, lo_subject, lo_to_facets, summary)


# -- running the views -------------------------------------------------------------------------

@dataclass
class Snapshot:
    """The replay's result: the subject view, each LO's view, the traces."""

    subject: View
    los: dict[str, View]
    trace: list[dict[str, Any]]
    events: Events
    settings: ReplaySettings
    observed_cells: set[tuple[str, str]] = field(default_factory=set)
    observed_los: set[str] = field(default_factory=set)
    observed_facets: set[str] = field(default_factory=set)
    observed_subjects: set[str] = field(default_factory=set)

    def state_hash(self) -> str:
        digest = hashlib.sha256(self.subject.bank.state_hash().encode())
        for lo in sorted(self.los):
            digest.update(lo.encode())
            digest.update(self.los[lo].bank.state_hash().encode())
        return digest.hexdigest()

    def lo_view(self, learning_object_id: str) -> View:
        """The LO's view (a fresh prior view when it has no eligible row yet)."""

        view = self.los.get(learning_object_id)
        if view is None:
            view = _new_lo_view(self.settings)
            _apply_claims_for_lo(view, self.events, learning_object_id, upto=math.inf)
        return view


def _grid(settings: ReplaySettings) -> tuple[P.HyperPoint, ...]:
    if settings.fixed_point is not None:
        return (settings.fixed_point,)
    grid = P.hyper_grid(settings.hyper)
    return P.uniform_points(grid) if not settings.coupling else grid


def _override(bank: M.Bank, settings: ReplaySettings) -> M.Bank:
    for name, mean in settings.prior_means:
        if bank.has(name):
            bank.mu[:, bank.index[name]] = float(mean)
    return bank


def _new_subject_view(settings: ReplaySettings, structure: M.Structure) -> View:
    bank = M.Bank(_grid(settings), structure=structure if settings.coupling else M.Structure(),
                  reading=True, verdict=True, rating=settings.rating, timing=settings.timing,
                  outside=settings.outside)
    return View(_override(bank, settings), subject_view=True, reading=settings.reading, verdicts=settings.verdicts,
                signals=P.BASE_SIGNALS + (("z_v1",) if settings.outside else ()))


def _new_lo_view(settings: ReplaySettings) -> View:
    bank = M.Bank((P.LO_VIEW_POINT,), rating=settings.rating, timing=settings.timing, outside=settings.outside)
    return View(_override(bank, settings), subject_view=False,
                signals=P.BASE_SIGNALS + (("z_v1",) if settings.outside else ()))


def _apply_claim(view: View, claim: ClaimEvent, events: Events, *, observed_subjects: set[str],
                 observed_facets: set[str], los: Iterable[str] | None = None) -> None:
    bank = view.bank
    level = _logit(claim.level)
    if claim.scope == "global":
        targets = sorted({events.lo_subject.get(lo, "default") for lo in (los if los is not None else
                                                                        events.lo_subject)})
        for subject in targets:
            if subject in observed_subjects:
                continue
            bank.ensure_subject(subject, claim.at)
            view.claim(M.subject_name(subject), level, bank.split)
        return
    for lo in claim.learning_object_ids:
        if los is not None and lo not in los:
            continue
        subject = events.lo_subject.get(lo, "default")
        for facet in events.lo_facets.get(lo, ()):
            if facet in observed_facets:
                continue
            bank.ensure_subject(subject, claim.at)
            bank.ensure_facet(facet, claim.at)
            mean = level - bank.mu[:, bank.index[M.subject_name(subject)]]
            view.claim(M.facet_name(facet), mean, (P.COLD_START_VARIANCE - bank.split) / 2.0)


def _apply_claims_for_lo(view: View, events: Events, lo: str, *, upto: float) -> None:
    for claim in events.claims:
        if claim.at < upto:
            _apply_claim(view, claim, events, observed_subjects=set(), observed_facets=set(), los=[lo])


def _mixture(view: View, record: M.UpdateRecord) -> dict[str, Any]:
    weights = view.bank.weights()[0]
    out = {
        "prior_mean": float(np.dot(weights, record.prior_mean)),
        "prior_var": float(np.dot(weights, record.prior_var + record.prior_mean ** 2)
                           - np.dot(weights, record.prior_mean) ** 2),
        "post_mean": float(np.dot(weights, record.post_mean)),
        "post_var": float(np.dot(weights, record.post_var + record.post_mean ** 2)
                          - np.dot(weights, record.post_mean) ** 2),
        "p_categories": [round(float(v), 12) for v in weights @ record.category_probabilities],
        "information": float(np.dot(weights, record.information)),
    }
    return out


@dataclass(frozen=True)
class Context:
    """What a prequential observer knows about an attempt before its update (the harness, §10.4)."""

    first_attempt_lo: bool
    first_surface_cell: bool
    after_reading: bool
    after_verdict: bool
    #: The verdict class of the latest self-check on the LO since its last answer (D22), if any.
    verdict_class: str | None = None
    #: Each reading kind's dose on the attempt's facets since their last answer (the dose report).
    doses: Mapping[str, float] = field(default_factory=dict)


def run(events: Events, settings: ReplaySettings = ReplaySettings(), *, trace: bool = True,
        observer: Any = None) -> Snapshot:
    """Replay the events into both views (§5.6), in fixed order, float64.

    ``observer(attempt, subject_view, lo_view, context)`` is called before each eligible
    attempt's update (the prequential harness reads its predictions there)."""

    structure = events.structure
    subject = _new_subject_view(settings, structure)
    los: dict[str, View] = {}
    rows: list[dict[str, Any]] = []
    snap = Snapshot(subject, los, rows, events, settings)
    lo_observed_facets: dict[str, set[str]] = {}
    read_since: dict[str, bool] = {}
    verdict_since: dict[str, str] = {}
    dose_since: dict[str, dict[str, float]] = {}
    for kind, event in events.ordered():
        structure.now = event.at
        if kind == "claim":
            _apply_claim(subject, event, events, observed_subjects=snap.observed_subjects,
                         observed_facets=snap.observed_facets)
            for lo, view in los.items():
                _apply_claim(view, event, events, observed_subjects={events.lo_subject.get(lo, "default")},
                             observed_facets=lo_observed_facets.get(lo, set()), los=[lo])
            continue
        if kind == "opportunity":
            read_since[event.learning_object_id] = True
            if event.subkind in P.VERDICT_CLASSES:
                verdict_since[event.learning_object_id] = event.subkind
                subject.verdict(event.subject, event.subkind, event.facet_doses, event.at)
            else:
                bucket = dose_since.setdefault(event.learning_object_id, {})
                dose = sum(event.facet_doses.values())
                # The kind, and kind:subkind (the report's "helps when" moderators, §10.4).
                for key in (event.kind, f"{event.kind}:{event.subkind}"):
                    bucket[key] = bucket.get(key, 0.0) + dose
                subject.reading(event.subject, event.kind, event.facet_doses, event.at)
            continue
        attempt: AttemptEvent = event
        if attempt.eligible and attempt.spec is not None and attempt.category is not None:
            spec = attempt.spec
            if observer is not None:
                lo_now = los.get(attempt.learning_object_id) or snap.lo_view(attempt.learning_object_id)
                observer(attempt, subject, lo_now, Context(
                    first_attempt_lo=attempt.learning_object_id not in snap.observed_los,
                    first_surface_cell=spec.cell() not in snap.observed_cells,
                    after_reading=bool(read_since.get(attempt.learning_object_id)),
                    after_verdict=bool(verdict_since.get(attempt.learning_object_id)),
                    verdict_class=verdict_since.get(attempt.learning_object_id),
                    doses=dict(dose_since.get(attempt.learning_object_id, {}))))
            record = subject.observe(spec, attempt.category, attempt.at, warmth=attempt.warmth,
                                     in_passage_kind=attempt.in_passage_kind, rating=attempt.rating,
                                     log_latency_ratio=attempt.log_latency_ratio, learn=settings.updates) \
                if settings.updates else None
            lo_view = los.get(attempt.learning_object_id)
            if lo_view is None:
                lo_view = _new_lo_view(settings)
                _apply_claims_for_lo(lo_view, events, attempt.learning_object_id, upto=attempt.at)
                los[attempt.learning_object_id] = lo_view
            lo_spec = replace(spec, loadings={})
            lo_record = lo_view.observe(lo_spec, attempt.category, attempt.at, warmth=attempt.warmth,
                                        rating=attempt.rating, log_latency_ratio=attempt.log_latency_ratio,
                                        learn=settings.updates) if settings.updates else None
            snap.observed_subjects.add(spec.subject)
            snap.observed_los.add(attempt.learning_object_id)
            for facet in spec.facet_weights:
                snap.observed_facets.add(facet)
                snap.observed_cells.add((facet, spec.capability))
                lo_observed_facets.setdefault(attempt.learning_object_id, set()).add(facet)
            if trace and record is not None:
                weights = subject.bank.weights()[0]
                points = [{"point": p.key(), "log_z": round(float(record.log_z[i]), 12),
                           "weight": round(float(weights[i]), 12),
                           "prior_mean": round(float(record.prior_mean[i]), 12),
                           "prior_var": round(float(record.prior_var[i]), 12)}
                          for i, p in enumerate(subject.bank.points)]
                rows.append({"attempt_id": attempt.attempt_id, "view": VIEW_SUBJECT,
                             "input_status": attempt.input_status, "category": attempt.category,
                             **_mixture(subject, record), "points": points,
                             "detail": {"warmth": round(attempt.warmth, 12), "cell": list(spec.cell()),
                                        "served_at": attempt.served_at}})
            if trace and lo_record is not None:
                rows.append({"attempt_id": attempt.attempt_id, "view": lo_view_name(attempt.learning_object_id),
                             "input_status": attempt.input_status, "category": attempt.category,
                             **_mixture(lo_view, lo_record), "points": None,
                             "detail": {"warmth": round(attempt.warmth, 12), "cell": list(spec.cell())}})
        elif trace and attempt.reason is not None:
            rows.append({"attempt_id": attempt.attempt_id, "view": VIEW_SUBJECT,
                         "input_status": attempt.input_status, "category": attempt.category,
                         "points": None, "detail": {"excluded": attempt.reason}})
        if attempt.closes:
            subject.close_windows(attempt.closes)
            read_since.pop(attempt.learning_object_id, None)
            verdict_since.pop(attempt.learning_object_id, None)
            dose_since.pop(attempt.learning_object_id, None)
    structure.now = math.inf
    return snap


# -- the live cache -------------------------------------------------------------------------------
#
# The cache is keyed by a **semantic** fingerprint (Codex review F3): the digest of the events the
# replay reads, never a table's row count or largest rowid, which a delete-and-insert (SQLite reuses
# the freed rowid), an in-place update or a table the list forgot (the interpretations behind
# quarantine) leave unchanged. Every input reaches the replay only through ``load_events``, so equal
# events give an equal replay: the live state is the fresh rebuild's, whatever wrote the change and
# from whichever connection. What the cache saves is the filter over the events (on the stage's test
# vaults, reading them took longer than the filter did, so the saving was always the smaller part).

_CACHE: dict[tuple[str, int, str | None, str, str | None], tuple[str, Snapshot]] = {}
_CACHE_LOCK = threading.Lock()


def _plain(value: Any) -> Any:
    from dataclasses import asdict, is_dataclass

    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    return repr(value)


def events_fingerprint(events: Events) -> str:
    """The digest of everything the replay reads (attempts with their frozen inputs, claims,
    reading opportunities, the relatedness structure and the vault maps)."""

    from dataclasses import asdict

    structure = events.structure
    payload = {
        "attempts": [asdict(e) for e in events.attempts],
        "claims": [asdict(e) for e in events.claims],
        "opportunities": [asdict(e) for e in events.opportunities],
        "structure": {
            "facet_los": getattr(structure, "facet_los", None),
            "lo_facets": getattr(structure, "lo_facets", None),
            "couplings": {lo: [[p.at, p.values] for p in props]
                          for lo, props in sorted(getattr(structure, "_couplings", {}).items())},
            "loadings": {rev: [[p.at, p.values] for p in props]
                         for rev, props in sorted(getattr(structure, "_loadings", {}).items())},
            "versions": getattr(structure, "versions", None),
        },
        "lo_subject": events.lo_subject,
        "lo_facets": events.lo_facets,
    }
    text = json.dumps(payload, sort_keys=True, default=_plain, allow_nan=True)
    return hashlib.sha256(text.encode()).hexdigest()


@entry(read_only=True)
def snapshot(vault: Any, repository: Any, *, settings: ReplaySettings | None = None, connection: Any = None,
             as_of: str | None = None, view: Any = None) -> Snapshot:
    """The current state (cached per database, vault and settings while the replay's events are unchanged).
    ``view``: the operation's material view (one is computed when the caller has none)."""

    settings = settings or ReplaySettings.from_config(vault.config)
    own = connection is None
    if own:
        from learnloop.db.connection import connect

        connection = connect(repository.sqlite_path, read_only=True)
    try:
        from learnloop.adaptive_difficulty.material_view import material_view
        from learnloop.adaptive_difficulty.operation import epoch_of

        view = material_view(vault, repository, view)
        # The vault as loaded (an operation hands a projection of it) and the protection epoch: a
        # snapshot is never served across a protection change (the AD23 redesign, E2).
        key = (str(repository.sqlite_path), id(getattr(vault, "_ad_raw_vault", vault)), epoch_of(view),
               settings.key(), as_of)
        events = load_events(connection, vault, repository, as_of=as_of, settings=settings, view=view)
        stamp = events_fingerprint(events)
        with _CACHE_LOCK:
            cached = _CACHE.get(key)
        if cached is not None and cached[0] == stamp:
            return cached[1]
        result = run(events, settings)
        with _CACHE_LOCK:
            _CACHE[key] = (stamp, result)
        return result
    finally:
        if own:
            connection.close()


def clear_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


# -- the DERIVED tables (one replayer) ----------------------------------------------------------------

def _summary_payload(view: View, *, uniform_mask: np.ndarray | None = None) -> dict[str, Any]:
    bank = view.bank
    weights = bank.weights()[0]
    means = weights @ bank.mu
    second = weights @ (np.diagonal(bank.S, axis1=1, axis2=2) + bank.mu ** 2)
    out = {
        "coordinates": list(bank.names),
        "mean": [round(float(v), 12) for v in means],
        "variance": [round(float(v), 12) for v in second - means ** 2],
        "points": [p.as_dict() for p in bank.points],
        "weights": [round(float(w), 12) for w in weights],
    }
    if uniform_mask is not None and uniform_mask.any():
        out["uniform_weights"] = [round(float(w), 12) for w in bank.restricted_weights(uniform_mask)[0]]
    return out


def state_rows(snap: Snapshot, *, as_of: str | None) -> list[dict[str, Any]]:
    versions = {**P.versions(), "replay": REPLAY_VERSION, "coupling": dict(snap.events.structure.versions)}
    mask = np.array([p.uniform for p in snap.subject.bank.points])
    rows = [{"view": VIEW_SUBJECT, "part": "summary", "payload": _summary_payload(snap.subject, uniform_mask=mask),
             "state_hash": snap.subject.bank.state_hash(), "as_of": as_of, "versions": versions}]
    for lo in sorted(snap.los):
        rows.append({"view": lo_view_name(lo), "part": "summary", "payload": _summary_payload(snap.los[lo]),
                     "state_hash": snap.los[lo].bank.state_hash(), "as_of": as_of, "versions": versions})
    return rows


def rebuild(vault: Any, repository: Any) -> dict[str, Any]:
    """The AD replayer (``ad_state``, ``ad_attempt_trace``): clear and rebuild, zero model calls."""

    from learnloop.adaptive_difficulty.successor import successor_active

    with repository.atomic():
        connection = repository.connection()
        if not serving_store.has_table(connection, serving_store.STATE):
            return {"written": 0, "skipped": "schema"}
        if not successor_active(vault.config):
            # Below the tag (or with AD off) nothing reads AD's state: the tables stay empty, so a
            # rebuild is the predecessor's exactly (a rolled-back vault's rows are cleared).
            serving_store.clear_derived(connection, (serving_store.STATE, serving_store.TRACE))
            return {"written": 0, "skipped": "below_successor", "accounted_attempt_ids": []}
        settings = ReplaySettings.from_config(vault.config)
        events = load_events(connection, vault, repository, settings=settings)
        snap = run(events, settings)
        serving_store.clear_derived(connection, (serving_store.STATE, serving_store.TRACE))
        latest = max((e.created_at for e in events.attempts), default=None)
        written = serving_store.write_state(connection, state_rows(snap, as_of=latest))
        written += serving_store.write_trace(connection, snap.trace)
    return {"written": written, "eligible": events.summary.get("eligible", 0),
            "input_status": events.summary.get("input_status", {}),
            "accounted_attempt_ids": sorted(e.attempt_id for e in events.attempts)}


__all__ = [
    "AttemptEvent",
    "ClaimEvent",
    "Events",
    "OpportunityEvent",
    "REPLAY_VERSION",
    "ReplaySettings",
    "Snapshot",
    "VIEW_SUBJECT",
    "clear_cache",
    "days",
    "events_fingerprint",
    "forced_failure",
    "load_events",
    "lo_view_name",
    "rebuild",
    "run",
    "snapshot",
    "state_rows",
]
