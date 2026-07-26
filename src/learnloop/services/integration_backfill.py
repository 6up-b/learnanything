"""D3's integration gate applied to blueprints already persisted (plan item 5.2).

(spec_measurement_efficiency_v1 §5.8.3 / D3, §6 ~line 1080.)

D3 shipped at ingest: ``SynthIntegrationComponent.capability`` is ``| None`` with
no default, an undeclared capability is dropped with a typed diagnostic, and an
explicit ``coordination`` integration is kept and flagged. What it explicitly does
**not** do is repair what is already in the vault — "Blueprints are vault content,
not derived state, so ``rebuild-derived-state`` will not touch the 18 already
persisted. Those need a re-authoring pass or a doctor-flagged manual review — see
Wave 2." This module is that pass. It applies the *same* criterion, retroactively;
it invents no new rule.

**D3's admission criterion**, verbatim: a recipe earns an ``integration``
component only when (1) the **assembly failure is nameable** — "a learner could
hold every ``all_of`` component and still fail, repeatably, observably, and in a
separately repairable way" — **and** (2) its **capability is observable**, i.e. an
instrument at that rung is authorable, where "``coordination`` satisfies this only
behind a reviewed depth envelope, because the default trajectory deliberately
refuses to generate whole-task work". Absent (1), omit the component — "omission
is the correct output, not a gap." Absent (2), the objective is uncertifiable by
construction and must say so.

**How each half is decided here, and why these are the right proxies.** Criterion
1 is a claim about content, so it is tested by the two structural facts that make
it false:

* ``NO_ASSEMBLY_TO_FAIL`` — the recipe has fewer than two *binding* ``all_of``
  components (``contract_reachability.CONTRACT_MODALITIES``; a ``facilitating``
  component never gates anything, so it is not something the learner must hold).
  "Hold every component and still fail to assemble them" presupposes at least two
  parts to assemble. With one, the integration is a second, deeper demand on the
  same single part.
* ``FACET_DUPLICATES_COMPONENT`` — the integration component names a facet the
  same recipe already lists as a component. Then the failure it describes is not
  *separately repairable*: repairing it is repairing that component's facet. This
  is "the same thing, one rung harder" wearing the integration label, which is
  exactly the shape §5.8.3 diagnosed ("it named the capability in the definition
  and implied every recipe should have one").

Criterion 2 is decided by the pool, not by taste: ``coordination`` is observable
when some active instrument actually observes *something* at ``coordination``
(§5.8.2 measured "Zero of 55 items observe ``coordination``", which is why the
answer on this vault is no). Once A1 conjunctive capstones exist (plan 6.1) the
same code stops lowering anything.

When (1) holds and (2) fails there are two honest outcomes, and which one applies
is again structural: lowering to the deepest **authorable** rung is only faithful
to the recipe if that rung is still strictly deeper than every component the
integration assembles — otherwise the "integration" would sit at or below a part,
which no longer claims an assembly at all. So:

* ``LOWER`` — deepest authorable rung (``depth_rungs``' trajectory tip) is deeper
  than every binding component. The assembly claim survives at a rung an
  instrument can reach; §5.8.3's upper-bound table calls this "lowered to an
  observable rung".
* ``KEEP`` with ``owed_capstone`` — a component already sits at the trajectory
  tip, so nothing observable is deeper. This is a *genuine* ``coordination``
  obligation: kept, flagged, and owed an A1 whole-task capstone. §5.8.3 keeps
  these deliberately — "it announces the obligation it creates rather than
  creating it silently."

Everything here is a pure function of vault content. :func:`plan_integration_backfill`
decides and explains; :func:`apply_integration_backfill` is the only thing that
writes, it takes the decisions as an argument, and it emits a per-file diff — the
edit is to *authored files*, so it has to be reviewable line by line.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Sequence

from learnloop.clock import Clock, SystemClock
from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import CANONICAL_PROJECTION_VERSION
from learnloop.services.contract_reachability import (
    CAPABILITY_RANK,
    CONTRACT_MODALITIES,
    build_instrument_pool,
)
from learnloop.services.depth_rungs import DEFAULT_TRAJECTORY, waypoint_slug_for_capability
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml, yaml_to_string

#: The deepest capability the default authoring trajectory can target. Not a knob —
#: it is read off ``depth_rungs.DEFAULT_TRAJECTORY``, so if the trajectory ever
#: gains a coordination waypoint this module stops lowering to a shallower rung on
#: its own.
DEEPEST_AUTHORABLE_CAPABILITY: str = DEFAULT_TRAJECTORY[-1].capability

#: The capability D3 singles out: legitimate, but observable "only behind a
#: reviewed depth envelope".
COORDINATION = "coordination"

#: rank -> capability, for naming the deepest component a recipe declares.
_CAPABILITY_BY_RANK: dict[int, str] = {rank: name for name, rank in CAPABILITY_RANK.items()}


class IntegrationDisposition(StrEnum):
    """What to do with one persisted integration component.

    ``KEEP``
        The component survives D3 unchanged. Either its capability is already
        observable, or the assembly failure is real and no observable rung is
        deeper than its parts — in which case it is owed an A1 whole-task capstone
        and says so (``owed_capstone``).
    ``LOWER``
        D3 criterion 1 holds, criterion 2 fails, and the deepest authorable rung is
        still strictly deeper than every component it assembles. The assembly claim
        is preserved at a rung an instrument can reach.
    ``DROP``
        D3 criterion 1 fails: there is no separately repairable assembly failure to
        name. "Omission is the correct output, not a gap."
    """

    KEEP = "KEEP"
    LOWER = "LOWER"
    DROP = "DROP"


class IntegrationReason(StrEnum):
    """Typed reason per disposition — closed, and never a free-text rationale.

    D2/D3's own discipline ("failure is typed, not silent") applied to the
    retroactive pass, because these rows are the review queue for an edit to
    authored content.
    """

    #: DROP: fewer than two binding ``all_of`` components — nothing to assemble.
    NO_ASSEMBLY_TO_FAIL = "no_assembly_to_fail"
    #: DROP: the integration facet is already a component facet of the same recipe,
    #: so its failure is not separately repairable.
    FACET_DUPLICATES_COMPONENT = "facet_duplicates_component"
    #: LOWER: coordination is unobservable here and a shallower authorable rung is
    #: still deeper than every part.
    LOWERED_TO_DEEPEST_AUTHORABLE = "lowered_to_deepest_authorable"
    #: KEEP: the declared capability already has an authorable instrument path.
    CAPABILITY_OBSERVABLE = "capability_observable"
    #: KEEP: a real assembly at coordination with no observable rung deeper than
    #: its parts. Owed an A1 conjunctive capstone (plan item 6.1).
    OWED_WHOLE_TASK_CAPSTONE = "owed_whole_task_capstone"
    #: KEEP (abstain): a capability here is outside the closed vocabulary — the
    #: integration's own, or every binding component's — so it cannot be placed on
    #: the ladder and no lowering target is defined. This is 3.1's ``INDETERMINATE``
    #: / ``repair_blueprint_capability``, not D3's business; the row is reported so
    #: it is not mistaken for a clean pass.
    CAPABILITY_OUTSIDE_VOCABULARY = "capability_outside_vocabulary"


@dataclass(frozen=True)
class IntegrationVerdict:
    """One persisted integration component, judged under D3, with its evidence."""

    learning_object_id: str
    blueprint_id: str
    recipe_id: str
    facet_id: str            # canonical
    capability: str          # as persisted
    disposition: IntegrationDisposition
    reason: IntegrationReason
    #: Replacement capability — set iff ``disposition is LOWER``.
    lowered_capability: str | None
    #: True when the row leaves a standing whole-task instrument obligation.
    owed_capstone: bool
    # -- the evidence the verdict was read off, so a reviewer can disagree without
    #    re-deriving it --
    binding_component_count: int
    component_facets: tuple[str, ...]
    deepest_component_capability: str | None

    @property
    def changes_content(self) -> bool:
        return self.disposition is not IntegrationDisposition.KEEP

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "blueprint_id": self.blueprint_id,
            "recipe_id": self.recipe_id,
            "facet_id": self.facet_id,
            "capability": self.capability,
            "disposition": str(self.disposition),
            "reason": str(self.reason),
            "lowered_capability": self.lowered_capability,
            "owed_capstone": self.owed_capstone,
            "binding_component_count": self.binding_component_count,
            "component_facets": list(self.component_facets),
            "deepest_component_capability": self.deepest_component_capability,
        }


@dataclass(frozen=True)
class IntegrationBackfillReport:
    verdicts: tuple[IntegrationVerdict, ...]
    #: Whether any active instrument observes ANY facet at ``coordination`` — D3
    #: criterion 2's observability test, measured rather than assumed.
    coordination_observed: bool

    @property
    def changed(self) -> tuple[IntegrationVerdict, ...]:
        return tuple(verdict for verdict in self.verdicts if verdict.changes_content)

    @property
    def owed_capstones(self) -> tuple[IntegrationVerdict, ...]:
        return tuple(verdict for verdict in self.verdicts if verdict.owed_capstone)

    def counts(self) -> dict[str, int]:
        tally = {str(disposition): 0 for disposition in IntegrationDisposition}
        for verdict in self.verdicts:
            tally[str(verdict.disposition)] += 1
        return tally

    def reason_counts(self) -> dict[str, int]:
        tally = {str(reason): 0 for reason in IntegrationReason}
        for verdict in self.verdicts:
            tally[str(verdict.reason)] += 1
        return tally

    def by_learning_object(self) -> dict[str, list[IntegrationVerdict]]:
        grouped: dict[str, list[IntegrationVerdict]] = {}
        for verdict in self.verdicts:
            grouped.setdefault(verdict.learning_object_id, []).append(verdict)
        return grouped

    def summary(self) -> dict[str, Any]:
        return {
            "integration_component_count": len(self.verdicts),
            "coordination_observed": self.coordination_observed,
            "dispositions": self.counts(),
            "reasons": self.reason_counts(),
            "learning_objects": len(self.by_learning_object()),
            "owed_capstones": [verdict.learning_object_id for verdict in self.owed_capstones],
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "summary": self.summary(),
            "verdicts": [verdict.as_dict() for verdict in self.verdicts],
        }


def coordination_is_observable(vault: LoadedVault) -> bool:
    """Does any active instrument observe some facet at ``coordination``?

    D3 criterion 2, measured. §5.8.2: "Zero of 55 items observe ``coordination``,
    and 18 of 19 integration components require it." This is deliberately a
    *vault-level* fact rather than a per-cell one: the question is whether the
    authoring path can produce whole-task work at all, not whether it happened to
    produce it for this facet.
    """

    pool = build_instrument_pool(vault)
    return any(COORDINATION in per_capability for per_capability in pool.by_facet.values())


def _binding(components: Iterable[Any]) -> list[Any]:
    """Components that actually gate — ``hard`` / ``path_specific`` only (§8.2)."""

    return [
        component
        for component in components
        if str(component.modality) in CONTRACT_MODALITIES
    ]


def _judge(
    vault: LoadedVault,
    *,
    learning_object_id: str,
    blueprint_id: str,
    recipe,
    coordination_observed: bool,
) -> IntegrationVerdict:
    integration = recipe.integration
    facet_id = vault.canonical_facet_id(str(integration.facet))
    capability = str(integration.capability)
    all_of = list(recipe.all_of or [])
    any_of = list(recipe.any_of or [])
    binding = _binding(all_of)
    # Facet identity is checked against every declared component, binding or not: a
    # `facilitating` component still names the same knowledge, so an integration
    # duplicating it is still not a *separately* repairable failure.
    component_facets = tuple(
        sorted({vault.canonical_facet_id(str(component.facet)) for component in all_of + any_of})
    )
    ranks = [
        CAPABILITY_RANK[str(component.capability)]
        for component in binding
        if str(component.capability) in CAPABILITY_RANK
    ]
    deepest_component = _CAPABILITY_BY_RANK[max(ranks)] if ranks else None

    def verdict(
        disposition: IntegrationDisposition,
        reason: IntegrationReason,
        *,
        lowered: str | None = None,
        owed: bool = False,
    ) -> IntegrationVerdict:
        return IntegrationVerdict(
            learning_object_id=learning_object_id,
            blueprint_id=blueprint_id,
            recipe_id=str(recipe.id),
            facet_id=facet_id,
            capability=capability,
            disposition=disposition,
            reason=reason,
            lowered_capability=lowered,
            owed_capstone=owed,
            binding_component_count=len(binding),
            component_facets=component_facets,
            deepest_component_capability=deepest_component,
        )

    # -- D3 criterion 1: is the assembly failure nameable? ---------------------
    # Checked first and capability-independently: D3 says "absent (1), omit the
    # component", with no reference to what rung it claimed.
    if len(binding) < 2:
        return verdict(IntegrationDisposition.DROP, IntegrationReason.NO_ASSEMBLY_TO_FAIL)
    if facet_id in component_facets:
        return verdict(IntegrationDisposition.DROP, IntegrationReason.FACET_DUPLICATES_COMPONENT)

    # -- D3 criterion 2: is the capability observable? -------------------------
    # A capability with a default-trajectory waypoint is authorable by definition.
    # `coordination` has none, so it qualifies only once the pool proves it — a
    # reviewed depth envelope's whole-task output lands in the pool as an ordinary
    # item, which is why the pool is the right place to ask.
    if waypoint_slug_for_capability(capability) is not None or (
        capability == COORDINATION and coordination_observed
    ):
        return verdict(IntegrationDisposition.KEEP, IntegrationReason.CAPABILITY_OBSERVABLE)
    if capability not in CAPABILITY_RANK or not ranks:
        # Unplaceable on the ladder — either the integration's own capability or
        # every binding component's — so abstain rather than invent a lowering
        # target. 3.1 already reports this as INDETERMINATE /
        # `repair_blueprint_capability`, which is where the fix belongs.
        return verdict(
            IntegrationDisposition.KEEP, IntegrationReason.CAPABILITY_OUTSIDE_VOCABULARY
        )

    lowered = DEEPEST_AUTHORABLE_CAPABILITY
    deepest_rank = max(ranks)
    if CAPABILITY_RANK[lowered] > deepest_rank:
        return verdict(
            IntegrationDisposition.LOWER,
            IntegrationReason.LOWERED_TO_DEEPEST_AUTHORABLE,
            lowered=lowered,
        )
    # Nothing observable is deeper than the parts, so the coordination requirement
    # is the real content of the recipe. Keep it and record the debt.
    return verdict(
        IntegrationDisposition.KEEP,
        IntegrationReason.OWED_WHOLE_TASK_CAPSTONE,
        owed=True,
    )


def plan_integration_backfill(
    vault: LoadedVault,
    *,
    learning_object_ids: Iterable[str] | None = None,
    capabilities: Iterable[str] | None = None,
) -> IntegrationBackfillReport:
    """Judge every persisted integration component under D3. Writes nothing.

    ``learning_object_ids`` is the pilot seam item 5.2 requires ("pilot on one LO
    first, measure reachable-cell delta, then batch"). ``capabilities`` narrows the
    pass to components declaring one of them — the plan's scope is "the 18
    persisted **coordination** integrations", and applying the criterion to a
    ``method_selection`` integration is a separate decision that should be taken
    explicitly rather than swept in.
    """

    wanted_los = set(learning_object_ids) if learning_object_ids is not None else None
    wanted_caps = {str(capability) for capability in capabilities} if capabilities is not None else None
    coordination_observed = coordination_is_observable(vault)
    verdicts: list[IntegrationVerdict] = []
    for learning_object_id in sorted(vault.learning_objects):
        if wanted_los is not None and learning_object_id not in wanted_los:
            continue
        learning_object = vault.learning_objects[learning_object_id]
        for blueprint in learning_object.blueprints or []:
            for recipe in blueprint.recipes or []:
                if recipe.integration is None:
                    continue
                if wanted_caps is not None and str(recipe.integration.capability) not in wanted_caps:
                    continue
                verdicts.append(
                    _judge(
                        vault,
                        learning_object_id=learning_object_id,
                        blueprint_id=str(blueprint.id),
                        recipe=recipe,
                        coordination_observed=coordination_observed,
                    )
                )
    return IntegrationBackfillReport(
        verdicts=tuple(verdicts), coordination_observed=coordination_observed
    )


# -- the write side ------------------------------------------------------------


@dataclass(frozen=True)
class BackfillFileEdit:
    """One learning-object file's rewrite, with a unified diff for review."""

    learning_object_id: str
    path: Path
    diff: str
    applied_verdicts: tuple[IntegrationVerdict, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_object_id": self.learning_object_id,
            "path": str(self.path),
            "diff": self.diff,
            "applied": [verdict.as_dict() for verdict in self.applied_verdicts],
        }


def _learning_object_path(vault: LoadedVault, learning_object_id: str) -> Path:
    """Resolve the authored YAML for an LO. Primary subject first, then a glob."""

    paths = VaultPaths(vault.root, vault.config)
    learning_object = vault.learning_objects[learning_object_id]
    for subject_id in learning_object.subjects:
        candidate = paths.learning_object_path(subject_id, learning_object_id)
        if candidate.exists():
            return candidate
    matches = sorted(vault.root.glob(f"subjects/*/learning-objects/{learning_object_id}.yaml"))
    if not matches:
        raise FileNotFoundError(f"no authored file for learning object {learning_object_id!r}")
    return matches[0]


def apply_integration_backfill(
    vault: LoadedVault,
    verdicts: Sequence[IntegrationVerdict],
    *,
    dry_run: bool = True,
    clock: Clock | None = None,
) -> tuple[BackfillFileEdit, ...]:
    """Rewrite the authored blueprints for ``verdicts``, or just diff them.

    ``dry_run=True`` (the default, deliberately) produces exactly the diffs a
    write would produce and touches nothing: these are hand-authored files, the
    edit is not regenerable by any rebuild, and a reviewer has to be able to read
    it before it lands. ``KEEP`` verdicts are skipped even when passed, so the
    caller can hand the whole report in without filtering.

    A ``DROP`` writes ``integration:`` as an explicit null rather than deleting the
    key — that is already how a recipe without an integration component is
    persisted in the tree, so the diff shows the *decision* and not an unrelated
    schema change. Round-tripped through ruamel, so comments and layout survive
    and the diff contains only the component and the LO's ``updated_at``.
    """

    now = (clock or SystemClock()).now().strftime("%Y-%m-%dT%H:%M:%SZ")
    by_lo: dict[str, list[IntegrationVerdict]] = {}
    for verdict in verdicts:
        if not verdict.changes_content:
            continue
        by_lo.setdefault(verdict.learning_object_id, []).append(verdict)

    edits: list[BackfillFileEdit] = []
    for learning_object_id in sorted(by_lo):
        path = _learning_object_path(vault, learning_object_id)
        before_text = path.read_text(encoding="utf-8")
        data = read_yaml(path)
        applied: list[IntegrationVerdict] = []
        for verdict in by_lo[learning_object_id]:
            recipe = _find_recipe(data, verdict)
            if recipe is None:
                continue
            if verdict.disposition is IntegrationDisposition.DROP:
                recipe["integration"] = None
            else:
                integration = recipe.get("integration")
                if not isinstance(integration, dict) or verdict.lowered_capability is None:
                    continue
                integration["capability"] = verdict.lowered_capability
            applied.append(verdict)
        if not applied:
            continue
        data["updated_at"] = now
        after_text = yaml_to_string(data)
        # Vault-relative paths in the header, so the emitted diff is a real patch a
        # reviewer can read side by side with the tree (and feed to `git apply -p1`
        # from the vault root) rather than a bare filename.
        try:
            relative = path.relative_to(vault.root).as_posix()
        except ValueError:  # pragma: no cover - path outside the vault root
            relative = path.name
        diff = "".join(
            difflib.unified_diff(
                before_text.splitlines(keepends=True),
                after_text.splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
        if not dry_run:
            write_yaml(path, data)
        edits.append(
            BackfillFileEdit(
                learning_object_id=learning_object_id,
                path=path,
                diff=diff,
                applied_verdicts=tuple(applied),
            )
        )
    return tuple(edits)


@dataclass(frozen=True)
class BackfillApplyResult:
    """A landed backfill: the file edits plus the single recalibration boundary."""

    edits: tuple[BackfillFileEdit, ...]
    rebuilt_learning_object_ids: tuple[str, ...] = ()
    rebuild_marker_id: str | None = None
    coverage_denominator_version: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "edits": [edit.as_dict() for edit in self.edits],
            "rebuilt_learning_object_ids": list(self.rebuilt_learning_object_ids),
            "rebuild_marker_id": self.rebuild_marker_id,
            "coverage_denominator_version": self.coverage_denominator_version,
        }


def apply_integration_backfill_and_recalibrate(
    vault: LoadedVault,
    repository: Repository,
    verdicts: Sequence[IntegrationVerdict],
    *,
    dry_run: bool = True,
    clock: Clock | None = None,
) -> BackfillApplyResult:
    """Land the backfill and narrate the mastery move it causes (§5.2 / A6).

    Dropping an integration component removes cells from the contract frontier,
    which is 3.3's coverage denominator, which drives the mastery variance floor.
    So displayed mastery moves — upward — with **no new evidence**. A6's whole
    argument is that a silent state change the learner has already seen is the
    failure mode; migration 138 exists so this surfaces as one honest "estimates
    recomputed, your evidence unchanged" entry. A vault-content edit would
    otherwise bypass that machinery entirely, because nothing else on the write
    path records a rebuild.

    Order is load-bearing: **every YAML edit first, then reload, then rebuild,
    then one marker.** Reloading between edit and rebuild is what makes the
    rebuild see the new blueprints (the frontier is read from the vault, not the
    database); writing one marker for the batch rather than one per LO is what
    keeps the learner from seeing a per-LO flood they appear to have caused.

    A dry run writes nothing at all — no files and **no boundary**. A rerun is
    idempotent for free: the stamped version is content-addressed on the
    resulting frontier, so a second application recomputes the same value and
    emits no second entry.
    """

    edits = apply_integration_backfill(
        vault, verdicts, dry_run=dry_run, clock=clock
    )
    if dry_run or not edits:
        return BackfillApplyResult(edits=edits)

    from learnloop.services.facet_diagnostics import coverage_denominator_version
    from learnloop.services.replay import replay_learning_object
    from learnloop.vault.loader import load_vault

    # The frontier is derived from authored content, so the rebuild has to run
    # against a vault reloaded from the files just written.
    reloaded = load_vault(vault.root)
    rebuilt: list[str] = []
    replayed_attempts = 0
    for edit in edits:
        if edit.learning_object_id not in reloaded.learning_objects:
            continue
        result = replay_learning_object(
            reloaded, repository, edit.learning_object_id
        )
        rebuilt.append(edit.learning_object_id)
        replayed_attempts += result.replayed_attempts
    version = coverage_denominator_version(reloaded, repository)
    marker_id = repository.record_derived_state_rebuild(
        scope="learning_object",
        learning_object_ids=rebuilt,
        algorithm_version=reloaded.config.algorithms.algorithm_version,
        rebuilt_learning_objects=len(rebuilt),
        replayed_attempts=replayed_attempts,
        canonical_projection_version=CANONICAL_PROJECTION_VERSION,
        coverage_denominator_version=version,
        clock=clock,
    )
    return BackfillApplyResult(
        edits=edits,
        rebuilt_learning_object_ids=tuple(rebuilt),
        rebuild_marker_id=marker_id,
        coverage_denominator_version=version,
    )


def _find_recipe(data: dict[str, Any], verdict: IntegrationVerdict) -> dict[str, Any] | None:
    """The raw recipe mapping this verdict judged, matched by blueprint+recipe id."""

    for blueprint in data.get("blueprints") or []:
        if str(blueprint.get("id")) != verdict.blueprint_id:
            continue
        for recipe in blueprint.get("recipes") or []:
            if str(recipe.get("id")) == verdict.recipe_id:
                return recipe
    return None
