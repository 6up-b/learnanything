"""``learnloop upgrade --to mvp-0.18 | mvp-0.19 | mvp-0.20``: the canonical-sources successors, then Tier 1.

The branch sources/canonical-practice built these as ``mvp-0.15`` and
``mvp-0.16`` (placeholder tags) over ``mvp-0.14``; they merged after router
R1's probe ties (``mvp-0.15``), learner-text gaps (``mvp-0.16``) and the proof
route check (``mvp-0.17``), so they are ``mvp-0.18`` and ``mvp-0.19``, the next
links of the linear chain, as every earlier successor was relabelled at its
merge.

* ``mvp-0.18`` (spec_source_practice_and_probes_v1 §7.3a): certification
  follows the answer key. New attempts on imported textbook exercises record
  ``practice_attempts.reference_status``; an unverified key schedules and
  teaches but never certifies (C3). Nothing is rewritten: every existing
  attempt keeps ``not_applicable`` and replay reads the stored column, so the
  projection equals its predecessor's (a shadow rebuild shows zero deltas).
* ``mvp-0.19`` (§8.5): intervention needs try the learner's sources before
  generating (kill switch ``source_service.source_first_needs``).
* ``mvp-0.20`` (Tier 1, the Decider migration, owner decision 2026-10-13):
  the Decider decides the small judgments ``[decider_routes]`` names, each
  with its LLM as fallback and its own kill switch
  (``learnloop.decider_judgments``). It chains here because it is the next
  link of the chain, not a sources change.

Each changes what is served or certified from now on, never the projection's
meaning for recorded history, so each is a tag change plus an idempotent
rebuild of the same projection namespace, prepared before the atomic config
rename (as every successor since mvp-0.9). Each accepts its immediate
predecessor, or anything the earlier links accept through them (``mvp-0.18``
chains :func:`learnloop.proof_check_upgrade.upgrade_to_mvp017`; below
``mvp-0.12`` that runs T1's guarded step, whose advisory guard status comes
back as notes, passed on here, and which refuses only under
``recurrence.require_guard = true``; a refusal there refuses this upgrade too).
This module sits at the top level beside ``proof_check_upgrade`` because it
composes the chain's earlier links.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from learnloop.algorithm_versions import (
    DECIDER_TIER1_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
    SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.proof_check_upgrade import upgrade_to_mvp017
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


#: An earlier link's refusal already names its own step; it passes through
#: unprefixed (as ``proof_check_upgrade`` passes the chain's refusals on).
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


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
    chained_notes: list[str] = []
    if original != predecessor:
        # The earlier links refuse before they take any step of their own; a
        # refusal there leaves the vault where it was.
        chained = chain_up(root, clock=clock)
        # The chain's advisory guard status (owner batch 2) comes back as notes.
        chained_notes = list(chained.notes or [])
        if not chained.upgraded:
            return UpgradeResult(
                upgraded=False, from_version=original, to_version=target, notes=chained_notes,
                problems=[
                    problem if _STEP_REFUSAL.match(problem) else f"{predecessor} step refused: {problem}"
                    for problem in chained.problems
                ],
            )
        vault = load_vault(root)
    current = vault.config.algorithms.algorithm_version
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


def upgrade_to_mvp018(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.17 (or earlier, through the chain) -> mvp-0.18: the answer-key gate."""

    return _step(root, target=SOURCE_REFERENCE_GATE_ALGORITHM_VERSION,
                 predecessor=PROOF_ROUTE_CHECK_ALGORITHM_VERSION, chain_up=upgrade_to_mvp017, clock=clock)


def upgrade_to_mvp019(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.18 (or earlier, through the chain) -> mvp-0.19: source-first needs."""

    return _step(root, target=SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
                 predecessor=SOURCE_REFERENCE_GATE_ALGORITHM_VERSION, chain_up=upgrade_to_mvp018, clock=clock)


def upgrade_to_mvp020(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.19 (or earlier, through the chain) -> mvp-0.20: Tier 1, the Decider's judgments."""

    return _step(root, target=DECIDER_TIER1_ALGORITHM_VERSION,
                 predecessor=SOURCE_FIRST_NEEDS_ALGORITHM_VERSION, chain_up=upgrade_to_mvp019, clock=clock)


__all__ = ["upgrade_to_mvp018", "upgrade_to_mvp019", "upgrade_to_mvp020"]
