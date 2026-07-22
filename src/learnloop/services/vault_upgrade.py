"""mvp-0.7 activation: atomic vault upgrade + mixed-version guards (KM §15, §12.7).

`algorithm_version` is vault-global, so activating the KM2 knowledge model is an
atomic per-vault upgrade: validate the vault is contract-complete, then write the
single config field. Mixed legacy/mvp-0.7 content in one vault is forbidden
(there is no per-subject routing), so the upgrade refuses unless the whole vault
is ready, and refuses to upgrade from any version other than the immediate
predecessor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import (
    KM_ALGORITHM_VERSION,
    P0_ALGORITHM_VERSION,
)
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

LEGACY_ALGORITHM_VERSION = "mvp-0.6"

# Persisted next to the vault sqlite when the cutover reinterprets any cell (F2).
COMPATIBILITY_DELTA_FILENAME = "compatibility_projection_delta.json"


@dataclass
class UpgradeResult:
    upgraded: bool
    from_version: str
    to_version: str
    problems: list[str] = field(default_factory=list)
    # The explicit mvp-0.7 -> mvp-0.8 reinterpretation delta over the projected
    # facet-capability cells (F2). None when no cutover happened.
    compatibility_delta: "CompatibilityDelta | None" = None


def validate_mvp07_readiness(vault: LoadedVault) -> list[str]:
    """Blocking reasons a vault cannot activate the mvp-0.7 knowledge model (§3.2).

    Every facet-bearing item must reference a registered canonical facet, and
    every registered facet must carry its ``claim`` and ``kind`` semantic
    contract. These are doctor errors on an already-mvp-0.7 vault; here they gate
    the upgrade so a half-authored registry never activates.
    """

    problems: list[str] = []
    known = set(vault.evidence_facets)
    if not known:
        facet_bearing = [i.id for i in vault.practice_items.values() if i.evidence_facets]
        if facet_bearing:
            problems.append(
                f"facets.yaml registry is empty but {len(facet_bearing)} item(s) declare facets"
            )
    for item in vault.practice_items.values():
        for facet in item.evidence_facets:
            if vault.canonical_facet_id(facet) not in known and facet not in known:
                problems.append(f"{item.id}: unregistered evidence facet {facet!r}")
    for facet in vault.evidence_facets.values():
        if not getattr(facet, "claim", None) or not getattr(facet, "kind", None):
            problems.append(f"facet {facet.id!r}: incomplete semantic contract (needs claim + kind)")
    return sorted(set(problems))


def upgrade_to_mvp07(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """Atomically activate mvp-0.7 and project legacy attempts into its state.

    The immutable attempt/grading ledger is shared by both model versions, but
    mvp-0.7 reads a new canonical facet cache. Build that cache while the config
    on disk still names mvp-0.6, then expose the new model with the final atomic
    config rename. If projection fails, the vault remains visibly legacy.
    """

    vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version
    if current == KM_ALGORITHM_VERSION:
        return UpgradeResult(
            upgraded=False,
            from_version=current,
            to_version=KM_ALGORITHM_VERSION,
            problems=["vault is already mvp-0.7"],
        )
    if current != LEGACY_ALGORITHM_VERSION:
        # Refuse to jump versions or upgrade from an unknown state: mixed-version
        # vaults are forbidden and there is no per-subject routing yet.
        return UpgradeResult(
            upgraded=False,
            from_version=current,
            to_version=KM_ALGORITHM_VERSION,
            problems=[
                f"cannot upgrade from {current!r}; only {LEGACY_ALGORITHM_VERSION!r} may activate mvp-0.7"
            ],
        )
    problems = validate_mvp07_readiness(vault)
    if problems:
        return UpgradeResult(
            upgraded=False,
            from_version=current,
            to_version=KM_ALGORITHM_VERSION,
            problems=problems,
        )

    # Use an in-memory version switch to enable the canonical projection before
    # the durable config flip. Repository construction also applies the additive
    # schema migrations needed by the projection. The old per-LO state and the
    # raw attempts remain untouched for frozen mvp-0.6 replay.
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    vault.config.algorithms.algorithm_version = KM_ALGORITHM_VERSION
    project_canonical_facet_state(vault, repository, clock=clock)
    _rewrite_algorithm_version(root / "learnloop.toml", current, KM_ALGORITHM_VERSION)
    return UpgradeResult(
        upgraded=True, from_version=current, to_version=KM_ALGORITHM_VERSION
    )


def upgrade_to_mvp08(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """Activate the mvp-0.8 authority-propagation projection as the default read
    path (spec §7.2, P0.5 design §7). In the shape of :func:`upgrade_to_mvp07`:

    1. Freeze the mvp-0.6 and mvp-0.7 registry manifests BEFORE the flip so both
       legacy versions have a byte-stable replay manifest (§6, §1.1c);
    2. flip ``algorithm_version`` mvp-0.7 -> mvp-0.8 (in memory, then the atomic
       TOML rename) and build the mvp-0.8 projection cache;
    3. ``activate_p0_projection`` records a ``derived_state_rebuilds`` receipt and
       never rewrites raw history (§7.2/§7.3);
    4. refresh the live ``parameter_registry`` to reflect mvp-0.8 effective values.
    """

    from learnloop.services import parameter_registry as registry_service
    from learnloop.services.p0_projection import activate_p0_projection

    vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version
    if current == P0_ALGORITHM_VERSION:
        return UpgradeResult(
            upgraded=False, from_version=current, to_version=P0_ALGORITHM_VERSION,
            problems=["vault is already mvp-0.8"],
        )
    if current != KM_ALGORITHM_VERSION:
        return UpgradeResult(
            upgraded=False, from_version=current, to_version=P0_ALGORITHM_VERSION,
            problems=[
                f"cannot upgrade from {current!r}; only {KM_ALGORITHM_VERSION!r} may activate mvp-0.8"
            ],
        )

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = Repository(sqlite_path)
    # (1) Freeze legacy manifests while the config still names mvp-0.7. Idempotent.
    registry_service.freeze_manifest(vault, repository, algorithm_version=LEGACY_ALGORITHM_VERSION, clock=clock)
    registry_service.freeze_manifest(vault, repository, algorithm_version=KM_ALGORITHM_VERSION, clock=clock)
    # (1b) Capture the mvp-0.7 compatibility projection cells as the delta baseline
    # (F2). Rebuild under the current (mvp-0.7) config so the baseline is fresh, then
    # snapshot the projected facet-capability cells before the flip.
    project_canonical_facet_state(vault, repository, clock=clock)
    baseline_cells = _projected_cells(repository)
    # (2) In-memory version switch enables the mvp-0.8 projection before the durable
    # config flip (mirrors upgrade_to_mvp07). Raw events + mvp-0.6/0.7 replay untouched.
    vault.config.algorithms.algorithm_version = P0_ALGORITHM_VERSION
    # (3) Build + record the mvp-0.8 projection activation receipt.
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    # (3b) Snapshot the mvp-0.8 cells and compute the explicit reinterpretation delta
    # over the REAL projected cells (F2). Persisted next to the sqlite for audit.
    candidate_cells = _projected_cells(repository)
    delta = compatibility_projection_delta(baseline_cells, candidate_cells)
    _persist_compatibility_delta(sqlite_path, delta, from_version=current)
    # (4) Refresh the live registry projection to the mvp-0.8 namespace.
    registry_service.refresh(vault, repository, clock=clock)
    _rewrite_algorithm_version(root / "learnloop.toml", current, P0_ALGORITHM_VERSION)
    return UpgradeResult(
        upgraded=True,
        from_version=current,
        to_version=P0_ALGORITHM_VERSION,
        compatibility_delta=delta,
    )


def _projected_cells(repository: Repository) -> dict[tuple[str, str], tuple[float, float, float]]:
    """The projected facet-capability cells as ``{(facet, capability): (direct_pos,
    direct_neg, cert_credit)}`` -- the comparable surface for the mvp-0.7 vs mvp-0.8
    compatibility delta. Rounded so float noise never masquerades as a real change."""

    cells: dict[tuple[str, str], tuple[float, float, float]] = {}
    for cell in repository.facet_capability_evidence_all():
        cells[(cell.facet_id, cell.capability)] = (
            round(cell.direct_positive_mass, 9),
            round(cell.direct_negative_mass, 9),
            round(cell.certification_credit, 9),
        )
    return cells


def _persist_compatibility_delta(
    sqlite_path: Path, delta: "CompatibilityDelta", *, from_version: str
) -> Path:
    """Write the inspectable cutover delta as a JSON artifact next to the sqlite."""

    artifact = sqlite_path.parent / COMPATIBILITY_DELTA_FILENAME
    payload = {
        "from_version": from_version,
        "to_version": P0_ALGORITHM_VERSION,
        **delta.as_dict(),
    }
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return artifact


@dataclass
class CompatibilityDelta:
    """Explicit, inspectable mvp-0.7 -> mvp-0.8 reinterpretation delta (§7.2/§9.6).

    ``matches`` is True when the mvp-0.8 projection reproduces the mvp-0.7
    compatibility projection cell-for-cell; otherwise ``changed_cells`` lists the
    inspectable differences (a P0 reinterpretation delta, never a silent rewrite)."""

    matches: bool
    changed_cells: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"matches": self.matches, "changed_cells": self.changed_cells}


def compatibility_projection_delta(
    baseline_cells: dict, candidate_cells: dict
) -> CompatibilityDelta:
    """Compare two projected facet-capability cell maps (``{key: (pos, neg, cred)}``)
    and report the explicit delta. Used by the cutover gate: the mvp-0.7
    compatibility projection either matches mvp-0.8 or produces this delta."""

    changed: list[dict[str, Any]] = []
    for key in sorted(set(baseline_cells) | set(candidate_cells), key=lambda k: str(k)):
        before = baseline_cells.get(key)
        after = candidate_cells.get(key)
        if before != after:
            changed.append({"cell": str(key), "before": before, "after": after})
    return CompatibilityDelta(matches=not changed, changed_cells=changed)


def _rewrite_algorithm_version(config_path: Path, from_version: str, to_version: str) -> None:
    """Atomically flip the single algorithm_version field (write-temp + rename)."""

    text = config_path.read_text(encoding="utf-8")
    needle = f'algorithm_version = "{from_version}"'
    if needle not in text:
        raise ValueError(f"algorithm_version = \"{from_version}\" not found in {config_path}")
    updated = text.replace(needle, f'algorithm_version = "{to_version}"', 1)
    tmp = config_path.with_suffix(config_path.suffix + ".tmp")
    tmp.write_text(updated, encoding="utf-8")
    tmp.replace(config_path)
