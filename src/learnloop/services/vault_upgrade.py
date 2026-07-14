"""mvp-0.7 activation: atomic vault upgrade + mixed-version guards (KM §15, §12.7).

`algorithm_version` is vault-global, so activating the KM2 knowledge model is an
atomic per-vault upgrade: validate the vault is contract-complete, then write the
single config field. Mixed legacy/mvp-0.7 content in one vault is forbidden
(there is no per-subject routing), so the upgrade refuses unless the whole vault
is ready, and refuses to upgrade from any version other than the immediate
predecessor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from learnloop.clock import Clock
from learnloop.services.assessment_contracts import KM_ALGORITHM_VERSION
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault

LEGACY_ALGORITHM_VERSION = "mvp-0.6"


@dataclass
class UpgradeResult:
    upgraded: bool
    from_version: str
    to_version: str
    problems: list[str] = field(default_factory=list)


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
    """Atomically activate mvp-0.7 for the vault at ``root`` if it is ready."""

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
    _rewrite_algorithm_version(root / "learnloop.toml", current, KM_ALGORITHM_VERSION)
    return UpgradeResult(
        upgraded=True, from_version=current, to_version=KM_ALGORITHM_VERSION
    )


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
