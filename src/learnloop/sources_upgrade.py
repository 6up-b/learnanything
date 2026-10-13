"""``learnloop upgrade --to mvp-0.15 | mvp-0.16``: the canonical-sources successors.

* ``mvp-0.15`` (spec_source_practice_and_probes_v1 §7.3a): certification
  follows the answer key. New attempts on imported textbook exercises record
  ``practice_attempts.reference_status``; an unverified key schedules and
  teaches but never certifies (C3). Nothing is rewritten: every existing
  attempt keeps ``not_applicable`` and replay reads the stored column, so the
  projection equals its predecessor's (a shadow rebuild shows zero deltas).
* ``mvp-0.16`` (§8.5): intervention needs try the learner's sources before
  generating (kill switch ``source_service.source_first_needs``).

Both change what is served or certified from now on, never the projection's
meaning for recorded history, so each is a tag change plus an idempotent
rebuild of the same projection namespace, prepared before the atomic config
rename (as every successor since mvp-0.9). Each accepts its immediate
predecessor, or anything the earlier links accept through them. This module
sits at the top level beside ``daily_plan_upgrade`` because it composes the
chain's earlier links.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from learnloop.algorithm_versions import (
    DAILY_PLAN_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
    SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.daily_plan_upgrade import upgrade_to_mvp014
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


def _step(root: Path, *, target: str, predecessor: str, chain_up: Callable[..., UpgradeResult], clock: Clock | None) -> UpgradeResult:
    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    earlier = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(predecessor)]
    if original != predecessor and original not in earlier:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[f"cannot upgrade from {original!r}; only {predecessor!r} (or an earlier successor, "
                      f"through it) may activate {target}"],
        )
    notes: list[str] = []
    if original != predecessor:
        chained = chain_up(root, clock=clock)
        notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target,
                problems=[f"{predecessor} step refused: {problem}" for problem in chained.problems],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=notes)


def upgrade_to_mvp015(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.14 (or earlier, through the chain) -> mvp-0.15: the answer-key gate."""

    return _step(root, target=SOURCE_REFERENCE_GATE_ALGORITHM_VERSION, predecessor=DAILY_PLAN_ALGORITHM_VERSION,
                 chain_up=upgrade_to_mvp014, clock=clock)


def upgrade_to_mvp016(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.15 (or earlier, through the chain) -> mvp-0.16: source-first needs."""

    return _step(root, target=SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
                 predecessor=SOURCE_REFERENCE_GATE_ALGORITHM_VERSION, chain_up=upgrade_to_mvp015, clock=clock)


__all__ = ["upgrade_to_mvp015", "upgrade_to_mvp016"]
