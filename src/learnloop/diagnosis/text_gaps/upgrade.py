"""``learnloop upgrade --to mvp-0.13``: sooner checks from learner-text gaps.

``mvp-0.13`` is the next link of the linear chain: ``mvp-0.12`` (the split,
placement and recurrence groups) PLUS this: a matched prerequisite gap on an
LO assumed known or in maintenance brings its next check forward. It changes
what is served, not the projection, so like ``mvp-0.11`` it is an immediate
successor tag plus an idempotent rebuild of the same projection namespace,
prepared before the atomic config rename.

* accepts ``mvp-0.12``, or an earlier chain member by running
  :func:`~learnloop.diagnosis.recurrence.upgrade.upgrade_to_mvp012` first (its
  guard decides; a refusal there refuses this, and a failure after it leaves
  the vault at the valid ``mvp-0.12``);
* writes nothing else: there is no advance before the switch (below the
  version the pipeline writes none), so the upgrade itself serves the same
  queue. Kill switch: ``learner_text_gaps.sooner_check_enabled``. Rolling the
  version back is restore-only.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import (
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
    RECURRENCE_GROUP_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


def upgrade_to_mvp013(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = LEARNER_TEXT_GAP_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    earlier = SUCCESSOR_CHAIN[: SUCCESSOR_CHAIN.index(RECURRENCE_GROUP_ALGORITHM_VERSION)]
    if original != RECURRENCE_GROUP_ALGORITHM_VERSION and original not in earlier:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {RECURRENCE_GROUP_ALGORITHM_VERSION!r} (or an earlier "
                f"successor through it: {', '.join(earlier)}) may activate {target}"
            ],
        )
    if original != RECURRENCE_GROUP_ALGORITHM_VERSION:
        from learnloop.diagnosis.recurrence.upgrade import upgrade_to_mvp012

        chained = upgrade_to_mvp012(root, clock=clock)
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[f"{RECURRENCE_GROUP_ALGORITHM_VERSION} step refused: {problem}" for problem in chained.problems],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target)


__all__ = ["upgrade_to_mvp013"]
