"""Delayed cold probe per certified LO, and `false_certification_rate`.

`spec_measurement_efficiency_v1.md` §5.7, plan item 4.2.

    **The delayed cold probe is the ground truth**, and it is wanted anyway for
    retention: one held-out-surface item per certified LO at +2-3 weeks. If it
    passes, the certificate held. In a single-learner vault this is the only
    external validity check available.

and, ordered first on the extended §3 B5 scoreboard for a reason the spec spells
out itself:

    `false_certification_rate`  # certified, then failed a delayed cold probe.
    This is the alpha actually being run at, and it is the only number that
    licenses any speed claim.

    **optimizing time-to-certification without measuring false certification is
    lowering the bar with extra steps.** No Part III change ships without it.

What is generalized rather than added
-------------------------------------
The vault already had a cold-probe lane; it was **repair**-scoped. `remediation
.record_remediation_attempt` queues a `cold_retry` `followup_tasks` row a day
after a primed repair attempt, `causal_orchestrator.cold_verification_context`
resolves the verification inputs NOW and carries them on the task record
(migration 124 §6.2), and `record_cold_verification_from_task` fires when the
retry lands. The delay window, the `not_before` invisibility, serve/consume/
expire, the scheduler's `pending_followup_practice_items` reader and the
unassisted-attempt guard in `attempts._validate` are all already there and are
all exactly what a certification probe needs.

So this module adds a second **kind** to that one scheduler (migration 139),
not a second scheduler:

* `certification_cold_probe` tasks, `case_kind='certification'`, `case_ref` =
  the certificate id, `context` = the certificate receipt.
* The consume-side handler (:func:`record_certification_cold_probe_attempt`)
  runs from `apply_attempt` beside `record_remediation_attempt`.
* The verdict lands in `certification_cold_probe_outcomes`: append-only,
  content-addressed, version-stamped — because unlike a queue row it is a
  **ground-truth label**, and a label a later rebuild can silently rewrite is
  not ground truth.

What a certificate is
---------------------
§5.3 keeps `lo_certification` as the authority: "for some blueprint, every hard
component demonstrated, plus direct integration evidence". There is no durable
certificate table yet — §5.3 receipts are plan item 8.4 — so the certificate is
**derived** here from `goal_certification.recipe_gaps` (the identical predicate
`lo_certification` uses, extracted so the two cannot drift) plus the capability
ledger, and then snapshotted onto the probe task and the outcome row. Its id is
the content hash of (LO, blueprint, recipe, certified cells), which makes
"one probe per certificate, ever" a UNIQUE index rather than a caller
convention, and makes a *re-earned* certificate with different cells a genuinely
new certificate that earns a fresh probe.

What "held out" means
---------------------
The existing surface vocabulary, not a second one. `canonical_projection
.surface_group_id` collapses an item into its `EvidenceFingerprint` group
(shared stimulus / source family / solution-recipe family, falling back to
`surface_family` then the item id), and `facet_capability_evidence
.independent_surface_groups` already records, per certified cell, which groups
the certifying evidence came from. A probe item is held out iff its
`surface_group_id` is not in that union — the same comparison
`causal_activity_policy.assess_near_clone` makes, so the recorded basis reuses
its exact `distinct_surface_group` / `shared_surface_group` / `unknown`
vocabulary (`NEAR_CLONE_BASES`).

Why the verdict is not a boolean
--------------------------------
§5.7's denominator is "certified **and probed**". An unprobed certificate must
never count as a pass, and an administered-but-uninterpretable probe (taken
primed, on a surface that turned out not to be held out, or against a
certificate that had already been withdrawn) is neither a pass nor a failure.
Hence `held` / `failed` / `indeterminate`, and hence a rate over zero scored
probes that reports **unavailable rather than 0.0** — that distinction is the
whole point of the metric.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import UTC, timedelta
from typing import Any, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services.fitted_params import CERTIFICATION_COLD_PROBE_SCOPE
from learnloop.vault.models import LearningObject, LoadedVault

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Versions and closed vocabularies
# ---------------------------------------------------------------------------

#: Bumped when the shape of a stored ground-truth row changes.
COLD_PROBE_STORE_VERSION = "certification_cold_probe_v1"
#: Bumped when the *decision rule* changes (what counts as held-out, which
#: verdict a given probe earns). Stamped on every row so a rate computed across
#: a policy change is sliceable rather than silently mixed.
COLD_PROBE_POLICY_VERSION = "certification_cold_probe_policy_v1"

#: The follow-up lane this module owns (migration 139's widened `kind` CHECK).
COLD_PROBE_TASK_KIND = "certification_cold_probe"
#: ...and its `case_kind`. `case_ref` is the certificate id.
COLD_PROBE_CASE_KIND = "certification"
#: The `context.kind` discriminator, mirroring `causal_cold_verification`.
COLD_PROBE_CONTEXT_KIND = "certification_cold_probe"

#: Verdict vocabulary. `indeterminate` is the abstention arm and it is load
#: bearing: without it a probe the learner took primed would have to be scored
#: as `failed`, and `false_certification_rate` would measure the scheduler's
#: hygiene instead of the certificate's validity.
PROBE_VERDICTS: tuple[str, ...] = ("held", "failed", "indeterminate")
#: The verdicts that enter the rate. THE DENOMINATOR IS EXACTLY THIS SET.
SCORED_VERDICTS = frozenset({"held", "failed"})

#: Why a probe abstained. Required exactly when the verdict is `indeterminate`
#: (migration 139 CHECK): an abstention with no recorded reason is
#: indistinguishable from a missing row.
INDETERMINATE_REASONS: tuple[str, ...] = (
    "assisted_probe",
    "surface_not_held_out",
    "certificate_withdrawn",
    "grade_unavailable",
)

#: The scheduler's per-LO decision vocabulary. `no_held_out_surface` is not an
#: error: it says the certificate is **unmeasurable** with the current item
#: pool, which is strictly worse news than unmeasured and must be visible rather
#: than absent (it is the §5.8.2-shaped finding for the probe lane, and it feeds
#: the same commissioning need).
SCHEDULE_DECISIONS: tuple[str, ...] = (
    "scheduled",
    "already_scheduled",
    "not_certified",
    "withdrawn_probe_cancelled",
    "no_candidate_item",
    "no_held_out_surface",
    # Meas §3.A2/§3.A3: candidates exist on a held-out surface, but every one of
    # them is an instrument the practice surface cannot render. Its own arm and
    # not `no_candidate_item`, because the remedy is different in kind: the pool
    # does not need more authoring, it needs the renderer. Collapsing the two
    # would send someone writing items that already exist.
    "no_servable_item",
    "certificate_recipe_unresolved",
)

#: Held-out bases, borrowed verbatim from `causal_activity_policy.NEAR_CLONE_BASES`
#: so the two lanes cannot grow two notions of surface identity.
HELD_OUT_BASES: tuple[str, ...] = (
    "distinct_surface_group",
    "shared_surface_group",
    "unknown",
)

#: Affordances the certifying evidence had that the delayed probe does not. Same
#: vocabulary shape as `causal_cold_verifications.avoided_affordances_json`, so
#: causal P4 can union the two cold-outcome channels without a translation layer.
_BASE_AVOIDED_AFFORDANCES: tuple[str, ...] = ("certifying_surface_groups", "delay_horizon")


# ---------------------------------------------------------------------------
# Fitted parameters (§5.7's "+2-3 weeks" is a knob, not a constant)
# ---------------------------------------------------------------------------

#: Pinned heuristic defaults. The house rule is that a new tuned parameter goes
#: in the fitted-parameter store, not the TOML config, and this one earns that
#: twice over: the horizon is the *independent variable* of the retention claim
#: §5.7 splits out ("will still have it at horizon H"), and the realized
#: `false_certification_rate` is what will eventually tune it. Nothing about
#: "+2-3 weeks" is a constant of nature.
#:
#: The window is how the spec's *range* is honoured rather than averaged away:
#: the probe becomes due at `horizon_days` (14 = two weeks) and stays takeable
#: for `window_days` (7 more, so it expires at three weeks). "+2-3 weeks" is
#: therefore the interval the probe is live in, not a point estimate someone
#: picked out of it.
COLD_PROBE_POLICY_DEFAULTS: dict[str, float] = {
    "horizon_days": 14.0,
    "window_days": 7.0,
    # Correctness at/above which the certificate is held to have survived.
    # Same default as `causal_probe_coherence`'s
    # `cold_verification_success_correctness`, deliberately a SEPARATE knob:
    # that one is a repair-effect cut, this one is a certification-validity cut,
    # and tying them would mean tuning one silently retunes the alpha §5.7 says
    # is the only number licensing a speed claim.
    "success_correctness": 0.8,
}

_COLD_PROBE_POLICY_BOUNDS: dict[str, tuple[float, float]] = {
    # A zero-day horizon is not a delayed probe, and a horizon past a year is
    # indistinguishable from never scheduling one.
    "horizon_days": (1.0, 365.0),
    "window_days": (1.0, 365.0),
    "success_correctness": (0.0, 1.0),
}


@dataclass(frozen=True)
class ColdProbeParameters:
    """Resolved probe knobs plus their provenance.

    ``lifecycle`` is ``"heuristic_default"`` until `learnloop fit` owns the
    scope. The manifest rides on every ground-truth row so a label can always be
    attributed to the parameters that produced it.
    """

    values: Mapping[str, float]
    lifecycle: str = "heuristic_default"
    fitted_set_id: str | None = None
    invalid_keys: tuple[str, ...] = ()

    def __getitem__(self, key: str) -> float:
        return float(self.values[key])

    @property
    def horizon_days(self) -> float:
        return float(self.values["horizon_days"])

    @property
    def window_days(self) -> float:
        return float(self.values["window_days"])

    @property
    def success_correctness(self) -> float:
        return float(self.values["success_correctness"])

    def manifest(self) -> dict[str, Any]:
        return {
            "scope": CERTIFICATION_COLD_PROBE_SCOPE,
            "lifecycle": self.lifecycle,
            "fitted_set_id": self.fitted_set_id,
            "values": dict(self.values),
            "invalid_keys": list(self.invalid_keys),
        }


def resolve_cold_probe_parameters(repository: Repository | None) -> ColdProbeParameters:
    """Active fitted cold-probe knobs, else the pinned heuristic defaults.

    A malformed fitted value falls back to its default and is reported in
    ``invalid_keys`` rather than crashing the scheduler or, worse, silently
    scheduling a probe at a nonsense horizon.
    """

    values = dict(COLD_PROBE_POLICY_DEFAULTS)
    if repository is None:
        return ColdProbeParameters(values=values)
    record = repository.active_fitted_parameters(CERTIFICATION_COLD_PROBE_SCOPE)
    if record is None:
        return ColdProbeParameters(values=values)
    params = record.get("params") or {}
    invalid: list[str] = []
    for key, _default in COLD_PROBE_POLICY_DEFAULTS.items():
        if key not in params:
            continue
        low, high = _COLD_PROBE_POLICY_BOUNDS[key]
        raw = params[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            invalid.append(key)
            continue
        candidate = float(raw)
        if not math.isfinite(candidate) or not (low <= candidate <= high):
            invalid.append(key)
            continue
        values[key] = candidate
    return ColdProbeParameters(
        values=values,
        lifecycle="fitted",
        fitted_set_id=str(record["id"]),
        invalid_keys=tuple(sorted(invalid)),
    )


# ---------------------------------------------------------------------------
# The certificate (§5.3 receipt, derived until plan 8.4 stores one)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CertifiedCell:
    """One (facet, capability) cell the certificate rests on.

    ``basis`` is §5.3's measured-vs-inferred distinction. Today it is always
    ``direct``: the substitution rule (inference at a wider margin, integration
    never substitutable) is plan item 8.4 and has no producer yet. The field
    exists now because "a certificate that cannot distinguish these is not one"
    (standing constraint 9), and because a probe recorded before 8.4 must still
    be interpretable after it.
    """

    facet_id: str
    capability: str
    role: str  # "component" | "integration"
    basis: str  # "direct" | "inferred"
    certification_credit: float
    surface_groups: tuple[str, ...]
    last_observed_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "facet_id": self.facet_id,
            "capability": self.capability,
            "role": self.role,
            "basis": self.basis,
            "certification_credit": self.certification_credit,
            "surface_groups": list(self.surface_groups),
            "last_observed_at": self.last_observed_at,
        }


@dataclass(frozen=True)
class Certificate:
    """A derived §5.3 certificate: LO + satisfying recipe + the cells it rests on."""

    learning_object_id: str
    blueprint_id: str
    recipe_id: str
    cells: tuple[CertifiedCell, ...]
    certified_at: str | None
    algorithm_version: str | None

    @property
    def certificate_id(self) -> str:
        """Content hash over the certificate's identity.

        Deliberately over the *requirements* (LO, blueprint, recipe, cells) and
        not over the evidence: further practice on an already-certified cell must
        not mint a new certificate and a second probe. A re-earned certificate
        after a withdrawal hashes the same iff it rests on the same recipe and
        cells — in which case it IS the same claim and the one probe already
        recorded against it stands.
        """

        return _content_id(
            "cert",
            {
                "learning_object_id": self.learning_object_id,
                "blueprint_id": self.blueprint_id,
                "recipe_id": self.recipe_id,
                "cells": [
                    [cell.facet_id, cell.capability, cell.role, cell.basis]
                    for cell in self.cells
                ],
            },
        )

    @property
    def integration_cell(self) -> CertifiedCell | None:
        return next((cell for cell in self.cells if cell.role == "integration"), None)

    def used_surface_groups(self) -> tuple[str, ...]:
        """Every surface group the certifying evidence came from.

        This is the exclusion set: a held-out probe must sit outside it.
        """

        groups: set[str] = set()
        for cell in self.cells:
            groups.update(cell.surface_groups)
        return tuple(sorted(groups))

    def as_receipt(self) -> dict[str, Any]:
        """The §5.3 receipt: which cells, at what credit, from which surfaces.

        ``substitutions`` is present-and-empty rather than absent so a reader
        after plan 8.4 does not have to distinguish "no inference was used" from
        "this row predates inference".
        """

        return {
            "certificate_id": self.certificate_id,
            "learning_object_id": self.learning_object_id,
            "blueprint_id": self.blueprint_id,
            "recipe_id": self.recipe_id,
            "certified_at": self.certified_at,
            "algorithm_version": self.algorithm_version,
            "cells": [cell.as_dict() for cell in self.cells],
            "used_surface_groups": list(self.used_surface_groups()),
            "substitutions": [],
            "policy_version": COLD_PROBE_POLICY_VERSION,
        }


def current_certificate(
    vault: LoadedVault, repository: Repository, learning_object: LearningObject
) -> Certificate | None:
    """The certificate this LO currently holds, or None if it holds none.

    `lo_certification` stays the authority on *whether* the LO is certified;
    `recipe_gaps` (its own extracted predicate) names *which* recipe satisfies
    it. When the two disagree — impossible by construction, so this is a
    tripwire, not a branch — nothing is certified rather than something
    approximated.

    "Withdrawn" needs no separate concept: a certificate is withdrawn exactly
    when the ledger no longer satisfies its recipe, and then this returns None.
    """

    from learnloop.services.goal_certification import lo_certification, recipe_gaps

    if not lo_certification(vault, repository, learning_object).demonstrated:
        return None
    satisfying = [
        gaps
        for gaps in recipe_gaps(vault, repository, learning_object)
        if gaps.satisfied
    ]
    if not satisfying:
        return None
    # Deterministic choice among several satisfying recipes: the probe must pick
    # the same one on every run or its certificate id — and therefore its
    # idempotency — is unstable.
    chosen = min(satisfying, key=lambda gaps: (gaps.blueprint_id, gaps.recipe_id))
    recipe = _recipe(learning_object, chosen.blueprint_id, chosen.recipe_id)
    if recipe is None:
        return None

    cells: list[CertifiedCell] = []
    algorithm_versions: set[str] = set()
    observed: list[str] = []
    for component, role in _certified_components(vault, recipe):
        facet_id = vault.canonical_facet_id(component.facet)
        ledger = repository.facet_capability_evidence(facet_id, component.capability)
        recall = repository.canonical_facet_recall_state(facet_id, component.capability)
        if ledger is not None and ledger.algorithm_version:
            algorithm_versions.add(str(ledger.algorithm_version))
        last_observed_at = recall.last_observed_at if recall is not None else None
        if last_observed_at:
            observed.append(str(last_observed_at))
        cells.append(
            CertifiedCell(
                facet_id=facet_id,
                capability=str(component.capability),
                role=role,
                # §5.3 substitution has no producer yet (plan 8.4); every cell a
                # certificate rests on today carries capability-matched direct or
                # embedded credit, which is what `certification_credit` means.
                basis="direct",
                certification_credit=(
                    float(ledger.certification_credit) if ledger is not None else 0.0
                ),
                surface_groups=(
                    tuple(sorted(ledger.independent_surface_groups))
                    if ledger is not None
                    else ()
                ),
                last_observed_at=last_observed_at,
            )
        )
    # The certification date is the newest observation among the certifying
    # cells: the moment the last requirement was met is when the certificate
    # came into being, and it is projected from immutable attempt timestamps
    # rather than from a projection's own `updated_at` (which a rebuild moves).
    certified_at = max(observed) if observed else None
    return Certificate(
        learning_object_id=learning_object.id,
        blueprint_id=chosen.blueprint_id,
        recipe_id=chosen.recipe_id,
        cells=tuple(
            sorted(cells, key=lambda cell: (cell.role, cell.facet_id, cell.capability))
        ),
        certified_at=certified_at,
        algorithm_version=(
            sorted(algorithm_versions)[0] if algorithm_versions else None
        ),
    )


def _recipe(learning_object: LearningObject, blueprint_id: str, recipe_id: str):
    for blueprint in learning_object.blueprints:
        if blueprint.id != blueprint_id:
            continue
        for recipe in blueprint.recipes:
            if recipe.id == recipe_id:
                return recipe
    return None


def _certified_components(vault: LoadedVault, recipe) -> list[tuple[Any, str]]:
    """The components `recipe_gaps` actually gated on, with their roles.

    Mirrors the authority exactly: `all_of` components at `hard` /
    `path_specific` modality, plus the integration component. `any_of` and
    advisory modalities are not part of the certificate's claim, so they are not
    part of what the probe re-tests.
    """

    components: list[tuple[Any, str]] = []
    seen: set[tuple[str, str]] = set()
    for component in recipe.all_of:
        if component.modality not in ("hard", "path_specific"):
            continue
        key = (vault.canonical_facet_id(component.facet), str(component.capability))
        if key in seen:
            continue
        seen.add(key)
        components.append((component, "component"))
    if recipe.integration is not None:
        # Deliberately appended even when the same cell already appears as a
        # component: the roles are different claims (competence vs coordination)
        # and the probe ranks on the integration role, so collapsing them would
        # lose the whole-task preference §5.8.3's revert criterion depends on.
        components.append((recipe.integration, "integration"))
    return components


# ---------------------------------------------------------------------------
# Held-out surface selection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeldOutSelection:
    """The chosen probe item, or the typed reason there is none."""

    practice_item_id: str | None
    surface_group: str | None
    basis: str
    decision: str  # one of SCHEDULE_DECISIONS
    excluded_surface_groups: tuple[str, ...] = ()
    candidates_considered: int = 0
    rejected_as_used_surface: tuple[str, ...] = ()
    covers_integration: bool = False
    #: Candidates dropped because the practice surface cannot render their
    #: stimulus (Meas §3.A2/§3.A3). Same shape as ``rejected_as_used_surface``
    #: and reported beside it: both answer "which items were considered and
    #: thrown away, and under which rule".
    rejected_as_unservable: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "practice_item_id": self.practice_item_id,
            "surface_group": self.surface_group,
            "held_out_basis": self.basis,
            "decision": self.decision,
            "excluded_surface_groups": list(self.excluded_surface_groups),
            "candidates_considered": self.candidates_considered,
            "rejected_as_used_surface": list(self.rejected_as_used_surface),
            "rejected_as_unservable": list(self.rejected_as_unservable),
            "covers_integration": self.covers_integration,
        }


def select_held_out_probe_item(
    vault: LoadedVault,
    repository: Repository,
    certificate: Certificate,
) -> HeldOutSelection:
    """Pick one active item that observes a certified cell on an unused surface.

    Ranking, in order:

    1. **Covers the integration cell.** §5.8.3's revert criterion for dropping
       integration components is "certified LOs failing the §5.7 delayed cold
       probe *on whole-task items specifically*" — so when the certificate has an
       integration claim, the probe preferentially tests it. Integration is the
       coordination claim and §5.3 forbids satisfying it by inference; it is
       exactly the part of a certificate most likely to be false.
    2. Covers more certified cells (a probe that re-tests more of the claim).
    3. Least recently attempted, never-attempted first — the coldest instrument.
    4. Item id, so the choice is deterministic.

    Candidates come from `contract_reachability.build_instrument_pool`, i.e. the
    same "which items can put evidence in this cell?" index the reachability
    check uses, so an item this picks really can fill the cell it is probing.
    """

    from learnloop.services.canonical_projection import surface_group_id
    from learnloop.services.contract_reachability import build_instrument_pool

    excluded = frozenset(certificate.used_surface_groups())
    pool = build_instrument_pool(vault)
    integration = certificate.integration_cell

    cells_by_item: dict[str, set[tuple[str, str]]] = {}
    for cell in certificate.cells:
        for item_id in pool.item_ids(cell.facet_id, cell.capability):
            cells_by_item.setdefault(item_id, set()).add((cell.facet_id, cell.capability))

    from learnloop.services.instrument_serving import unservable_reason

    rejected: list[str] = []
    unservable: list[str] = []
    ranked: list[tuple[tuple[Any, ...], str, str, bool]] = []
    for item_id, covered in cells_by_item.items():
        item = vault.practice_items.get(item_id)
        if item is None:
            continue
        # The certificate is a claim about THIS learning object, integration
        # included. A same-cell item under another LO measures the cell but not
        # this LO's assembly of it, so it is not admitted — the spec asks for one
        # held-out item "per certified LO".
        if item.learning_object_id != certificate.learning_object_id:
            continue
        state = repository.practice_item_state(item_id)
        if state is not None and not state.active:
            continue
        group = surface_group_id(item)
        if group in excluded:
            rejected.append(item_id)
            continue
        # Meas §3.A2/§3.A3, checked AFTER the surface rule so the two buckets are
        # disjoint and each one means what it says: an id in `unservable` cleared
        # the held-out test and was refused only because the practice surface
        # cannot render its stimulus. The §5.7 probe is the ONLY external validity
        # check on a certificate and its verdict is `false_certification`, so an
        # unrenderable probe guarantees a miss and revokes a certified skill on
        # evidence the learner was never shown the material to produce — the
        # harmful write, at its most expensive.
        if unservable_reason(item) is not None:
            unservable.append(item_id)
            continue
        covers_integration = integration is not None and (
            (integration.facet_id, integration.capability) in covered
        )
        last_attempt_at = (state.last_attempt_at or "") if state is not None else ""
        ranked.append(
            (
                (
                    0 if covers_integration else 1,
                    -len(covered),
                    last_attempt_at,
                    item_id,
                ),
                item_id,
                group,
                covers_integration,
            )
        )

    if not ranked:
        # Three different pieces of news, kept apart deliberately. "No candidate
        # at all" is an authoring gap on the cell; "every candidate shares a
        # surface with the certifying evidence" is an authoring gap on *variety*;
        # "a held-out candidate exists but cannot be rendered" is not an authoring
        # gap at all, and the certificate is unmeasurable until the renderer lands
        # rather than until the pool grows.
        #
        # Servability is checked FIRST because a non-empty `unservable` proves a
        # held-out surface was found — reporting `no_held_out_surface` there
        # would send someone authoring the variety they already have.
        if unservable:
            decision, basis = "no_servable_item", "distinct_surface_group"
        elif rejected:
            decision, basis = "no_held_out_surface", "shared_surface_group"
        else:
            decision, basis = "no_candidate_item", "unknown"
        return HeldOutSelection(
            practice_item_id=None,
            surface_group=None,
            basis=basis,
            decision=decision,
            excluded_surface_groups=certificate.used_surface_groups(),
            candidates_considered=len(cells_by_item),
            rejected_as_used_surface=tuple(sorted(rejected)),
            rejected_as_unservable=tuple(sorted(unservable)),
        )

    ranked.sort(key=lambda entry: entry[0])
    _key, item_id, group, covers_integration = ranked[0]
    return HeldOutSelection(
        practice_item_id=item_id,
        surface_group=group,
        basis="distinct_surface_group",
        decision="scheduled",
        excluded_surface_groups=certificate.used_surface_groups(),
        candidates_considered=len(cells_by_item),
        rejected_as_used_surface=tuple(sorted(rejected)),
        rejected_as_unservable=tuple(sorted(unservable)),
        covers_integration=covers_integration,
    )


# ---------------------------------------------------------------------------
# The scheduler
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScheduleDecision:
    """What the scheduler did (or declined to do) for one LO."""

    learning_object_id: str
    decision: str
    certificate_id: str | None = None
    followup_task_id: str | None = None
    not_before: str | None = None
    expires_at: str | None = None
    practice_item_id: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "decision": self.decision,
            "certificate_id": self.certificate_id,
            "followup_task_id": self.followup_task_id,
            "not_before": self.not_before,
            "expires_at": self.expires_at,
            "practice_item_id": self.practice_item_id,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True)
class ScheduleReport:
    decisions: tuple[ScheduleDecision, ...]
    parameters: Mapping[str, Any]

    @property
    def counts(self) -> dict[str, int]:
        counts = {decision: 0 for decision in SCHEDULE_DECISIONS}
        for decision in self.decisions:
            counts[decision.decision] = counts.get(decision.decision, 0) + 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "store_version": COLD_PROBE_STORE_VERSION,
            "policy_version": COLD_PROBE_POLICY_VERSION,
            "parameters": dict(self.parameters),
            "counts": self.counts,
            "decisions": [decision.as_dict() for decision in self.decisions],
        }


def schedule_certification_cold_probes(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str | None = None,
    clock: Clock | None = None,
) -> ScheduleReport:
    """Queue one delayed cold probe per certified LO. Idempotent.

    Idempotency is by **certificate**, not by run: the unique index on
    `followup_tasks(case_ref) WHERE kind='certification_cold_probe'` plus a
    status-blind existence read means a consumed or expired probe still
    suppresses a second one. Re-running this is a no-op.

    A certificate that has since been **withdrawn** (its recipe no longer
    satisfied by the ledger) schedules nothing, and any probe already queued
    against it is expired rather than left to fire — measuring a claim the
    system has already retracted would put a `failed` row in the numerator of a
    metric about *false certification*, which is precisely wrong.
    """

    parameters = resolve_cold_probe_parameters(repository)
    now = clock or SystemClock()
    decisions: list[ScheduleDecision] = []
    learning_objects = _target_learning_objects(vault, learning_object_id)
    from learnloop.services.goal_certification import lo_certification

    for learning_object in learning_objects:
        certificate = current_certificate(vault, repository, learning_object)
        if certificate is None:
            if lo_certification(vault, repository, learning_object).demonstrated:
                # The tripwire, and the producer for this arm of the vocabulary:
                # the authority says certified but no recipe could be named, so
                # nothing is probed and the disagreement is reported rather than
                # filed under "not certified" where it would look like ordinary
                # absence.
                decisions.append(
                    ScheduleDecision(
                        learning_object_id=learning_object.id,
                        decision="certificate_recipe_unresolved",
                    )
                )
                continue
            decisions.append(
                _cancel_stale_probes(repository, learning_object.id, clock=clock)
            )
            continue
        # A recipe change mints a DIFFERENT certificate id, which withdraws the
        # old certificate as surely as losing a cell does. Any probe still queued
        # against the superseded id is retired here, before the new one is
        # scheduled: left alone it would fire, find an id mismatch, and land in
        # the abstention arm having burned a held-out item for nothing.
        superseded = [
            task
            for task in repository.open_followup_tasks_of_kind(
                COLD_PROBE_TASK_KIND, learning_object_id=learning_object.id
            )
            if str(task.get("case_ref")) != certificate.certificate_id
        ]
        for task in superseded:
            repository.expire_followup_task(str(task["id"]), clock=clock)
        if superseded:
            decisions.append(
                ScheduleDecision(
                    learning_object_id=learning_object.id,
                    decision="withdrawn_probe_cancelled",
                    certificate_id=certificate.certificate_id,
                    detail={
                        "cancelled_followup_task_ids": [
                            str(task["id"]) for task in superseded
                        ],
                        "superseded_certificate_ids": sorted(
                            str(task.get("case_ref")) for task in superseded
                        ),
                    },
                )
            )
        existing = repository.followup_task_for_case(
            kind=COLD_PROBE_TASK_KIND, case_ref=certificate.certificate_id
        )
        if existing is not None:
            decisions.append(
                ScheduleDecision(
                    learning_object_id=learning_object.id,
                    decision="already_scheduled",
                    certificate_id=certificate.certificate_id,
                    followup_task_id=str(existing["id"]),
                    not_before=str(existing["not_before"]),
                    expires_at=existing.get("expires_at"),
                    practice_item_id=existing.get("selected_item_id"),
                    detail={"status": existing.get("status")},
                )
            )
            continue
        selection = select_held_out_probe_item(vault, repository, certificate)
        if selection.practice_item_id is None:
            decisions.append(
                ScheduleDecision(
                    learning_object_id=learning_object.id,
                    decision=selection.decision,
                    certificate_id=certificate.certificate_id,
                    detail=selection.as_dict(),
                )
            )
            continue
        not_before, expires_at = probe_window(
            certificate.certified_at, parameters, clock=now
        )
        context = _probe_context(certificate, selection, parameters, not_before, expires_at)
        task = repository.create_followup_task(
            kind=COLD_PROBE_TASK_KIND,
            case_kind=COLD_PROBE_CASE_KIND,
            case_ref=certificate.certificate_id,
            not_before=not_before,
            expires_at=expires_at,
            selected_item_id=selection.practice_item_id,
            context=context,
            learning_object_id=learning_object.id,
            clock=clock,
        )
        decisions.append(
            ScheduleDecision(
                learning_object_id=learning_object.id,
                decision="scheduled",
                certificate_id=certificate.certificate_id,
                followup_task_id=str(task["id"]),
                not_before=not_before,
                expires_at=expires_at,
                practice_item_id=selection.practice_item_id,
                detail=selection.as_dict(),
            )
        )
    return ScheduleReport(
        decisions=tuple(decisions), parameters=parameters.manifest()
    )


def _target_learning_objects(
    vault: LoadedVault, learning_object_id: str | None
) -> list[LearningObject]:
    objects = sorted(vault.learning_objects.values(), key=lambda lo: lo.id)
    if learning_object_id is None:
        return objects
    return [lo for lo in objects if lo.id == learning_object_id]


def _cancel_stale_probes(
    repository: Repository, learning_object_id: str, *, clock: Clock | None = None
) -> ScheduleDecision:
    """Retire probes for an LO that is no longer certified."""

    open_tasks = repository.open_followup_tasks_of_kind(
        COLD_PROBE_TASK_KIND, learning_object_id=learning_object_id
    )
    if not open_tasks:
        return ScheduleDecision(
            learning_object_id=learning_object_id, decision="not_certified"
        )
    cancelled: list[str] = []
    for task in open_tasks:
        repository.expire_followup_task(str(task["id"]), clock=clock)
        cancelled.append(str(task["id"]))
    return ScheduleDecision(
        learning_object_id=learning_object_id,
        decision="withdrawn_probe_cancelled",
        detail={"cancelled_followup_task_ids": cancelled},
    )


def probe_window(
    certified_at: str | None,
    parameters: ColdProbeParameters,
    *,
    clock: Clock | None = None,
) -> tuple[str, str]:
    """``(not_before, expires_at)`` for a certificate earned at ``certified_at``.

    The probe becomes due at ``certified_at + horizon_days`` and expires
    ``window_days`` later — §5.7's "+2-3 weeks" as an interval rather than a
    point. When the ledger cannot date the certificate (a legacy or rebuilt
    vault with no observation timestamp on the certifying cells) the clock's
    "now" stands in: the horizon is then measured from *discovery* rather than
    from certification, which delays the probe but never shortens it, and a
    shortened horizon is the only direction that would flatter the metric.
    """

    anchor = parse_utc(certified_at) or (clock or SystemClock()).now()
    anchor = anchor.astimezone(UTC).replace(microsecond=0)
    not_before = anchor + timedelta(days=parameters.horizon_days)
    expires_at = not_before + timedelta(days=parameters.window_days)
    return _iso(not_before), _iso(expires_at)


def _probe_context(
    certificate: Certificate,
    selection: HeldOutSelection,
    parameters: ColdProbeParameters,
    not_before: str,
    expires_at: str,
) -> dict[str, Any]:
    """Everything the consume side will need, resolved NOW (migration 124's rule).

    Two-to-three weeks after certification the ledger has moved: cells have more
    evidence, surface groups have been reused, the recipe may have been
    re-authored. Reconstructing "which certificate was this probing, and which
    surfaces were already used?" at consume time would measure the certificate
    the learner holds *then*, not the one the probe was scheduled against. So the
    receipt travels on the task, exactly as §6.2 carries the cold-verification
    inputs.
    """

    return {
        "kind": COLD_PROBE_CONTEXT_KIND,
        "store_version": COLD_PROBE_STORE_VERSION,
        "policy_version": COLD_PROBE_POLICY_VERSION,
        "certificate_id": certificate.certificate_id,
        "certificate_receipt": certificate.as_receipt(),
        "learning_object_id": certificate.learning_object_id,
        "blueprint_id": certificate.blueprint_id,
        "recipe_id": certificate.recipe_id,
        "certified_at": certificate.certified_at,
        "excluded_surface_groups": list(certificate.used_surface_groups()),
        "probe_practice_item_id": selection.practice_item_id,
        "probe_surface_group": selection.surface_group,
        "held_out_basis": selection.basis,
        "covers_integration": selection.covers_integration,
        "avoided_affordances": list(_avoided_affordances(certificate, selection)),
        "scheduled_not_before": not_before,
        "scheduled_expires_at": expires_at,
        "horizon_days": parameters.horizon_days,
        "window_days": parameters.window_days,
        "success_threshold": parameters.success_correctness,
        "parameters": parameters.manifest(),
    }


def _avoided_affordances(
    certificate: Certificate, selection: HeldOutSelection
) -> tuple[str, ...]:
    """What the probe gives up relative to the certifying evidence.

    Names the CERTIFYING surface families (the ones the probe is not allowed to
    reuse), never the probe's own — the field answers "what did this attempt not
    have?", and listing the probe's own surface there would make every row claim
    it avoided itself.
    """

    affordances = set(_BASE_AVOIDED_AFFORDANCES)
    for group in certificate.used_surface_groups():
        affordances.add(f"surface_family:{group}")
    if selection.covers_integration:
        # The certifying evidence could satisfy components separately; a
        # whole-task probe cannot (§5.3: integration is never substitutable).
        affordances.add("component_only_evidence")
    return tuple(sorted(affordances))


# ---------------------------------------------------------------------------
# The outcome path
# ---------------------------------------------------------------------------


def record_certification_cold_probe_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: Mapping[str, Any],
    *,
    grading_source: str | None = None,
    grading_agent_run_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Consume a due probe and record whether the certificate held.

    Runs from `apply_attempt`, beside `record_remediation_attempt`, and
    deliberately BEFORE the canonical projection re-runs: the certificate state
    this reads must be the one the probe was administered against, not the one
    the probe's own evidence produces. Reading it after projection would let a
    failing probe withdraw the certificate it just falsified and then record the
    result as `indeterminate` — the numerator of `false_certification_rate`
    would be structurally empty.

    Returns the stored row, or None when this attempt is not a probe. Never
    raises: a bookkeeping failure must not fail an attempt.
    """

    try:
        return _record_probe_outcome(
            vault,
            repository,
            attempt,
            grading_source=grading_source,
            grading_agent_run_id=grading_agent_run_id,
            clock=clock,
        )
    except Exception:  # pragma: no cover - hot path must never fail on bookkeeping
        logger.warning(
            "certification cold probe recording failed for attempt %s",
            attempt.get("id"),
            exc_info=True,
        )
        return None


def _record_probe_outcome(
    vault: LoadedVault,
    repository: Repository,
    attempt: Mapping[str, Any],
    *,
    grading_source: str | None,
    grading_agent_run_id: str | None,
    clock: Clock | None,
) -> dict[str, Any] | None:
    from learnloop.services.canonical_projection import surface_group_id

    practice_item_id = str(attempt.get("practice_item_id") or "")
    attempt_id = str(attempt.get("id") or "")
    if not practice_item_id or not attempt_id:
        return None
    task = repository.active_followup_task_for_item(
        practice_item_id,
        kind=COLD_PROBE_TASK_KIND,
        at=str(attempt.get("created_at") or "") or None,
    )
    if task is None:
        return None
    context = task.get("context")
    if not isinstance(context, Mapping):
        return None
    if context.get("kind") != COLD_PROBE_CONTEXT_KIND:
        return None

    consumed = repository.consume_followup_task(str(task["id"]), attempt_id, clock=clock)
    if consumed is None or consumed.get("status") != "consumed":
        # Somebody else already answered this probe. Exactly-once, as with the
        # repair-scoped cold retry.
        return None

    parameters = resolve_cold_probe_parameters(repository)
    # The threshold, horizon and window come off the TASK, not off the live
    # parameter set: the probe must be scored against the policy it was scheduled
    # under, or a mid-flight `learnloop fit` silently re-scores probes already in
    # the air. `_carried` falls back only when the value is genuinely absent — a
    # stored threshold of 0.0 is degenerate but legal, and `or` would discard it.
    threshold = _carried(context, "success_threshold", parameters.success_correctness)
    excluded = frozenset(str(value) for value in context.get("excluded_surface_groups") or [])

    item = vault.practice_items.get(practice_item_id)
    probe_group = surface_group_id(item) if item is not None else None
    if probe_group is None:
        held_out_basis = "unknown"
    elif probe_group in excluded:
        held_out_basis = "shared_surface_group"
    else:
        held_out_basis = "distinct_surface_group"

    assisted = _attempt_is_assisted(attempt)
    correctness = attempt.get("correctness")
    correctness = None if correctness is None else float(correctness)

    learning_object_id = str(
        context.get("learning_object_id") or attempt.get("learning_object_id") or ""
    )
    certificate_state = _certificate_state_at_probe(
        vault, repository, learning_object_id, str(context.get("certificate_id") or "")
    )

    # The abstention ladder, in precedence order. Each rung is a reason the probe
    # cannot speak to the certificate's validity; none of them is a failure of
    # the certificate, and none of them may enter the rate's denominator.
    verdict = "held"
    reason: str | None = None
    if held_out_basis != "distinct_surface_group":
        verdict, reason = "indeterminate", "surface_not_held_out"
    elif assisted:
        verdict, reason = "indeterminate", "assisted_probe"
    elif certificate_state == "withdrawn":
        verdict, reason = "indeterminate", "certificate_withdrawn"
    elif correctness is None:
        verdict, reason = "indeterminate", "grade_unavailable"
    else:
        verdict = "held" if correctness >= threshold else "failed"

    success = None if verdict == "indeterminate" else verdict == "held"
    receipt = context.get("certificate_receipt")
    receipt = dict(receipt) if isinstance(receipt, Mapping) else {}
    stamp = _grader_stamp(
        repository,
        attempt_id,
        grading_source=grading_source,
        grading_agent_run_id=grading_agent_run_id,
    )
    identity = {
        "certificate_id": context.get("certificate_id"),
        "followup_task_id": str(task["id"]),
        "probe_attempt_id": attempt_id,
    }
    return repository.insert_certification_cold_probe_outcome(
        outcome_id=_content_id("ccp", identity),
        certificate_id=str(context.get("certificate_id") or ""),
        learning_object_id=learning_object_id,
        blueprint_id=str(context.get("blueprint_id") or ""),
        recipe_id=str(context.get("recipe_id") or ""),
        certificate_receipt=receipt,
        certified_at=context.get("certified_at"),
        followup_task_id=str(task["id"]),
        scheduled_not_before=str(
            context.get("scheduled_not_before") or task["not_before"]
        ),
        scheduled_expires_at=context.get("scheduled_expires_at")
        or task.get("expires_at"),
        horizon_days=_carried(context, "horizon_days", parameters.horizon_days),
        window_days=_carried(context, "window_days", parameters.window_days),
        probe_practice_item_id=practice_item_id,
        probe_attempt_id=attempt_id,
        probe_surface_group=probe_group or "",
        excluded_surface_groups=sorted(excluded),
        held_out_basis=held_out_basis,
        avoided_affordances=[
            str(value) for value in context.get("avoided_affordances") or []
        ],
        verdict=verdict,
        indeterminate_reason=reason,
        success=success,
        correctness=correctness,
        success_threshold=threshold,
        assisted=assisted,
        certificate_state_at_probe=certificate_state,
        store_version=COLD_PROBE_STORE_VERSION,
        policy_version=COLD_PROBE_POLICY_VERSION,
        certification_algorithm_version=receipt.get("algorithm_version"),
        parameters=parameters.manifest(),
        clock=clock,
        **stamp,
    )


def _attempt_is_assisted(attempt: Mapping[str, Any]) -> bool:
    """The shared assistance test, not a local re-derivation.

    A cold probe that was primed or hinted is not cold, and `attempts._validate`
    already refuses those on a queued probe item — but replay, a regrade, or a
    future caller can still land one, and the label has to say so rather than
    score it.
    """

    from learnloop.services.causal_activity_policy import attempt_counts_as_assisted

    return attempt_counts_as_assisted(
        attempt_type=str(attempt.get("attempt_type") or "independent_attempt"),
        primed=bool(attempt.get("primed")),
        hints_used=int(attempt.get("hints_used") or 0),
    )


def _certificate_state_at_probe(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    certificate_id: str,
) -> str:
    """``active`` iff the LO still holds the exact certificate being probed."""

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return "withdrawn"
    certificate = current_certificate(vault, repository, learning_object)
    if certificate is None:
        return "withdrawn"
    return "active" if certificate.certificate_id == certificate_id else "withdrawn"


def _grader_stamp(
    repository: Repository,
    attempt_id: str,
    *,
    grading_source: str | None,
    grading_agent_run_id: str | None,
) -> dict[str, Any]:
    """Grader provenance for the label, following `diagnosis_adjudication`.

    "Sliced by §3 B5 (reported per prompt version and per model)". A self-graded
    probe legitimately carries no model — that is recorded as a self grading
    source with null model fields, not silently omitted.
    """

    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    source = grading_source or metadata.get("grading_source")
    run_id = grading_agent_run_id or metadata.get("agent_run_id")
    run = repository.agent_run(str(run_id)) if run_id else None
    run = run or {}
    return {
        "grading_source": str(source) if source else None,
        "grading_prompt_version": (
            str(run["prompt_version"]) if run.get("prompt_version") else None
        ),
        "grader_model": str(run["model"]) if run.get("model") else None,
        "grader_provider": str(run["provider"]) if run.get("provider") else None,
        "grader_provider_revision": (
            str(run["provider_revision"]) if run.get("provider_revision") else None
        ),
        "grading_agent_run_id": str(run_id) if run_id else None,
    }


# ---------------------------------------------------------------------------
# `false_certification_rate` (§5.7 / augmentation §3 B5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FalseCertificationRate:
    """`false_certification_rate` with its denominator and availability arm.

    ``rate`` is ``failed / (held + failed)``. It is ``None`` — never ``0.0`` —
    whenever no probe has produced a scored verdict, and ``available`` says so
    explicitly. A rate of 0.0 over zero probes is the exact claim §5.7 forbids:
    it reads as "no certificate has ever been false" when the truth is "no
    certificate has ever been checked", and every speed claim downstream would
    inherit that lie.

    The three non-denominator arms are counted separately and never folded in:

    * ``awaiting_probe`` — scheduled, horizon not yet reached or not yet taken.
      **Not yet measured is its own arm**, and an unprobed certificate must never
      count as a pass.
    * ``probe_expired`` — the window closed with no attempt. Also unmeasured, but
      distinguishable from still-pending, because a run of expiries means the
      probe is not reaching the learner and the metric is quietly dying.
    * ``indeterminate`` — probed, but the probe could not speak to the
      certificate (assisted, surface not actually held out, certificate already
      withdrawn). Measured-but-uninformative, with the reason recorded.
    """

    rate: float | None
    numerator: int
    denominator: int
    held: int
    failed: int
    indeterminate: int
    awaiting_probe: int
    probe_expired: int
    certificates_with_probe_scheduled: int
    indeterminate_reasons: Mapping[str, int]
    by_horizon_days: Mapping[str, Mapping[str, Any]]
    store_version: str = COLD_PROBE_STORE_VERSION
    policy_version: str = COLD_PROBE_POLICY_VERSION
    unavailable_reason: str | None = None

    @property
    def available(self) -> bool:
        return self.rate is not None

    # -- mapping protocol, for the §3 B5 scoreboard's composition seam --------
    #
    # `services/scoreboard.py` composes this metric rather than reimplementing
    # it, and its documented contract is "a `Metric` or a mapping carrying
    # `numerator`/`denominator`". Supporting `keys()`/`__getitem__` makes
    # ``dict(false_certification_rate(repository))`` the full B5 entry, so the
    # seam needs no adapter and cannot pick up a partial view of the metric.

    def keys(self) -> tuple[str, ...]:
        return tuple(self.as_dict())

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]

    def as_dict(self) -> dict[str, Any]:
        """The §3 B5 scoreboard entry.

        ``value`` is ``None`` and ``status`` is ``"unavailable"`` when nothing
        has been probed; a consumer that reads only ``value`` therefore gets a
        null rather than a flattering zero.
        """

        return {
            "metric": "false_certification_rate",
            "value": self.rate,
            "status": "available" if self.available else "unavailable",
            "unavailable_reason": self.unavailable_reason,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "denominator_definition": (
                "certificates with a scored delayed cold probe (held + failed)"
            ),
            "note": (
                "certified, then failed a delayed held-out-surface cold probe "
                "(measurement §5.7). Unprobed certificates are their own arm and "
                "never count as passes"
            ),
            "arms": {
                "held": self.held,
                "failed": self.failed,
                "indeterminate": self.indeterminate,
                "awaiting_probe": self.awaiting_probe,
                "probe_expired": self.probe_expired,
            },
            "indeterminate_reasons": dict(self.indeterminate_reasons),
            "certificates_with_probe_scheduled": self.certificates_with_probe_scheduled,
            "by_horizon_days": {
                key: dict(value) for key, value in self.by_horizon_days.items()
            },
            "store_version": self.store_version,
            "policy_version": self.policy_version,
        }


def false_certification_rate(
    repository: Repository, *, clock: Clock | None = None
) -> FalseCertificationRate:
    """Certified-then-failed over certified-and-probed (§5.7, §3 B5).

    Repository-only by design: the whole metric is readable from the probe queue
    plus the append-only outcome store, so a scoreboard caller does not need a
    loaded vault, and ``clock`` is optional. The one arm that *does* need a vault
    — "certified, but no held-out surface exists to probe with" — lives in
    :func:`certification_cold_probe_report` instead, because it is an authoring
    finding rather than a measurement.
    """

    outcomes = repository.certification_cold_probe_outcomes()
    tasks = repository.followup_tasks_of_kind(COLD_PROBE_TASK_KIND)

    held = failed = indeterminate = 0
    reasons: dict[str, int] = {}
    per_horizon: dict[str, dict[str, int]] = {}
    for row in outcomes:
        verdict = str(row.get("verdict") or "")
        horizon = _horizon_key(row.get("horizon_days"))
        bucket = per_horizon.setdefault(
            horizon, {"held": 0, "failed": 0, "indeterminate": 0}
        )
        if verdict == "held":
            held += 1
            bucket["held"] += 1
        elif verdict == "failed":
            failed += 1
            bucket["failed"] += 1
        else:
            indeterminate += 1
            bucket["indeterminate"] += 1
            reason = str(row.get("indeterminate_reason") or "unrecorded")
            reasons[reason] = reasons.get(reason, 0) + 1

    # `followup_tasks` expires LAZILY (`due_followup_tasks` flips the status only
    # when somebody reads the queue), so a task nobody has looked at since its
    # window closed still carries `status='served'`. Counting that as "awaiting"
    # would let a dead probe lane look alive indefinitely, which is the failure
    # mode this arm exists to expose — so the window is compared against the
    # clock, not against the lazily-maintained status.
    now = utc_now_iso(clock)
    awaiting = expired = 0
    for task in tasks:
        if str(task.get("status")) not in ("pending", "served", "expired"):
            continue
        window_closed = str(task.get("status")) == "expired" or (
            bool(task.get("expires_at")) and str(task["expires_at"]) < now
        )
        if window_closed:
            expired += 1
        else:
            awaiting += 1

    denominator = held + failed
    rate = (failed / denominator) if denominator else None
    return FalseCertificationRate(
        rate=rate,
        numerator=failed,
        denominator=denominator,
        held=held,
        failed=failed,
        indeterminate=indeterminate,
        awaiting_probe=awaiting,
        probe_expired=expired,
        certificates_with_probe_scheduled=len(tasks),
        indeterminate_reasons=dict(sorted(reasons.items())),
        by_horizon_days={
            key: dict(value | {"rate": _rate(value)})
            for key, value in sorted(per_horizon.items())
        },
        unavailable_reason=None if denominator else "no_scored_cold_probe",
    )


def _rate(bucket: Mapping[str, int]) -> float | None:
    denominator = int(bucket.get("held", 0)) + int(bucket.get("failed", 0))
    return (int(bucket.get("failed", 0)) / denominator) if denominator else None


def _horizon_key(value: Any) -> str:
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return "unknown"


def cold_outcome_labels(repository: Repository) -> list[dict[str, Any]]:
    """The certification lane's cold-outcome labels, in the causal P4 shape.

    Causal P4 is parked on "cold-outcome volume from 4.2's delayed probes", and
    its existing training substrate is `causal_cold_verifications` (source
    attempt, cold attempt, surfaces, avoided affordances, success). These rows
    are emitted under the same key names so P4 can union the two channels rather
    than learn a second schema. ``claim_kind`` is what distinguishes them: a
    causal row tests a *repair*, one of these tests a *certificate*.

    Abstained probes are excluded — they carry no label, and a training set that
    treats "not interpretable" as an outcome is worse than a smaller one.
    """

    labels: list[dict[str, Any]] = []
    for row in repository.certification_cold_probe_outcomes():
        if str(row.get("verdict")) not in SCORED_VERDICTS:
            continue
        labels.append(
            {
                "claim_kind": "lo_certificate",
                "claim_ref": row.get("certificate_id"),
                "learning_object_id": row.get("learning_object_id"),
                "cold_attempt_id": row.get("probe_attempt_id"),
                "cold_surface_family": row.get("probe_surface_group"),
                "source_surface_families": list(
                    row.get("excluded_surface_groups") or []
                ),
                "avoided_affordances": list(row.get("avoided_affordances") or []),
                "success": bool(row.get("success")),
                "correctness": row.get("correctness"),
                "success_threshold": row.get("success_threshold"),
                "horizon_days": row.get("horizon_days"),
                "certified_at": row.get("certified_at"),
                "observed_at": row.get("created_at"),
                "policy_version": row.get("policy_version"),
                "store_version": row.get("store_version"),
            }
        )
    return labels


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def certification_cold_probe_report(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> dict[str, Any]:
    """`false_certification_rate` plus the coverage of the probe lane itself.

    A metric whose instrument is not reaching its subjects reads as "nothing
    wrong". So this pairs the rate with the number of certified LOs that have no
    probe and why: unmeasurable (no held-out surface in the pool) is a different
    fact from unscheduled, and both belong next to the number they bound.
    """

    metric = false_certification_rate(repository, clock=clock)
    parameters = resolve_cold_probe_parameters(repository)
    outcomes_by_certificate = {
        str(row.get("certificate_id")): row
        for row in repository.certification_cold_probe_outcomes()
    }
    certified: list[dict[str, Any]] = []
    for learning_object in sorted(vault.learning_objects.values(), key=lambda lo: lo.id):
        certificate = current_certificate(vault, repository, learning_object)
        if certificate is None:
            continue
        task = repository.followup_task_for_case(
            kind=COLD_PROBE_TASK_KIND, case_ref=certificate.certificate_id
        )
        selection = (
            None
            if task is not None
            else select_held_out_probe_item(vault, repository, certificate)
        )
        outcome = outcomes_by_certificate.get(certificate.certificate_id)
        certified.append(
            {
                "learning_object_id": learning_object.id,
                "certificate_id": certificate.certificate_id,
                "blueprint_id": certificate.blueprint_id,
                "recipe_id": certificate.recipe_id,
                "certified_at": certificate.certified_at,
                "certified_cells": len(certificate.cells),
                "used_surface_groups": list(certificate.used_surface_groups()),
                "probe_status": (
                    str(task.get("status")) if task is not None else "unscheduled"
                ),
                "probe_not_before": task.get("not_before") if task is not None else None,
                "probe_practice_item_id": (
                    task.get("selected_item_id") if task is not None else None
                ),
                "unschedulable_reason": (
                    None
                    if selection is None or selection.practice_item_id is not None
                    else selection.decision
                ),
                "verdict": outcome.get("verdict") if outcome is not None else None,
                "indeterminate_reason": (
                    outcome.get("indeterminate_reason") if outcome is not None else None
                ),
            }
        )
    unmeasurable = sum(
        1 for row in certified if row["unschedulable_reason"] is not None
    )
    return {
        "store_version": COLD_PROBE_STORE_VERSION,
        "policy_version": COLD_PROBE_POLICY_VERSION,
        "parameters": parameters.manifest(),
        "false_certification_rate": metric.as_dict(),
        "coverage": {
            "certificates_active": len(certified),
            "certificates_unmeasurable": unmeasurable,
            "certificates_unscheduled": sum(
                1 for row in certified if row["probe_status"] == "unscheduled"
            ),
        },
        "certificates": certified,
        "cold_outcome_labels": len(cold_outcome_labels(repository)),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _carried(context: Mapping[str, Any], key: str, fallback: float) -> float:
    """A numeric knob carried on the task, else the live default.

    Absence falls back; a present-but-zero value does not. The difference matters
    because these are the values the probe is SCORED against, and quietly
    swapping a stored 0.0 for the current default would re-score a probe under a
    policy it was not scheduled under.
    """

    raw = context.get(key)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return float(fallback)
    value = float(raw)
    return value if math.isfinite(value) else float(fallback)


def _content_id(prefix: str, value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:32]}"


def _iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


__all__ = [
    "COLD_PROBE_CASE_KIND",
    "COLD_PROBE_CONTEXT_KIND",
    "COLD_PROBE_POLICY_DEFAULTS",
    "COLD_PROBE_POLICY_VERSION",
    "COLD_PROBE_STORE_VERSION",
    "COLD_PROBE_TASK_KIND",
    "Certificate",
    "CertifiedCell",
    "ColdProbeParameters",
    "FalseCertificationRate",
    "HELD_OUT_BASES",
    "HeldOutSelection",
    "INDETERMINATE_REASONS",
    "PROBE_VERDICTS",
    "SCHEDULE_DECISIONS",
    "SCORED_VERDICTS",
    "ScheduleDecision",
    "ScheduleReport",
    "certification_cold_probe_report",
    "cold_outcome_labels",
    "current_certificate",
    "false_certification_rate",
    "probe_window",
    "record_certification_cold_probe_attempt",
    "resolve_cold_probe_parameters",
    "schedule_certification_cold_probes",
    "select_held_out_probe_item",
]
