"""``learnloop upgrade --to mvp-0.27``: one serve/administration eligibility decision.

The serve-eligibility stage (queued 2026-10-16;
``docs/reviews/serve-eligibility-decision.md``) took no tag; its Codex review
(F4) required one, because it changes what is served and which new seeded or
simulated attempts are primed. It is the next link of the linear chain:
everything ``mvp-0.26`` means PLUS this:

* every serve path asks the one decision submit asks
  (``learnloop.serve_eligibility``): an item submit would prime is never
  served as a cold check, a probe or a quick-check offer;
* a cold check its item can no longer take cold (the answer shown with no
  lapse, or the item attempted since the check was set) is withdrawn with its
  typed disposition and the item served as ordinary practice, honestly
  labelled; a time-bounded hold (a routine display, a reveal since the check
  was set) defers it, as before;
* exam seeding, an exam's finish and a kept-state sim count only reveals at
  or before their own instant when auto-priming (Q33);
* submit's rule is kept exactly: any primed draft (an auto-primed one
  included) is refused a cold check, and the refusal names its cause.

The upgrade:

* accepts the immediate predecessor (``mvp-0.26``), or ``mvp-0.9`` to
  ``mvp-0.25`` by running :func:`learnloop.regrade_contract_upgrade.upgrade_to_mvp026`
  first (with its own activation, and below ``mvp-0.12`` T1's guarded step,
  whose advisory notes pass through, a refusal's included). If the chained
  steps succeed and this step then fails, the vault is left at the valid
  ``mvp-0.26``. Anything older is refused;
* changes what is SERVED and what NEW attempts persist, never the
  authority-propagation projection, so like the serving successors before it
  it is a tag change plus an idempotent rebuild of the same projection
  namespace, prepared before the atomic config rename.

Nothing is rewritten: recorded attempts keep their ``primed`` flag (replay
reads it), and follow-up tasks keep their rows until a serve acts on them.
Kill switch: ``eligibility.enabled = false`` serves and admits exactly as
``mvp-0.26`` without a downgrade; rolling the version back is restore-only.
"""

from __future__ import annotations

import re
from pathlib import Path

from learnloop.algorithm_versions import (
    ELIGIBILITY_DECISION_ALGORITHM_VERSION,
    REGRADE_CONTRACT_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import Clock
from learnloop.ops.vault_upgrade import UpgradeResult, rewrite_algorithm_version
from learnloop.params import parameter_registry as registry_service
from learnloop.regrade_contract_upgrade import upgrade_to_mvp026
from learnloop.substrate.p0_projection import activate_p0_projection
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

#: Versions the upgrade accepts through the existing chain (mvp-0.26's own
#: upgrade takes them to the immediate predecessor first): mvp-0.9 to mvp-0.25.
_CHAINED_PREDECESSORS = SUCCESSOR_CHAIN[:SUCCESSOR_CHAIN.index(REGRADE_CONTRACT_ALGORITHM_VERSION)]

#: An earlier link's refusal already names its own step; it passes through unprefixed.
_STEP_REFUSAL = re.compile(r"^mvp-0\.\d+ step refused: ")


def upgrade_to_mvp027(root: Path, *, clock: Clock | None = None) -> UpgradeResult:
    """mvp-0.26 (or mvp-0.9 to mvp-0.25, through the chain) -> mvp-0.27: one eligibility decision."""

    vault = load_vault(root)
    original = vault.config.algorithms.algorithm_version
    target = ELIGIBILITY_DECISION_ALGORITHM_VERSION
    predecessor = REGRADE_CONTRACT_ALGORITHM_VERSION
    if original == target:
        return UpgradeResult(upgraded=False, from_version=original, to_version=target,
                             problems=[f"vault is already {target}"])
    if original != predecessor and original not in _CHAINED_PREDECESSORS:
        return UpgradeResult(
            upgraded=False, from_version=original, to_version=target,
            problems=[
                f"cannot upgrade from {original!r}; only {predecessor!r} (or "
                f"{_CHAINED_PREDECESSORS[0]!r} to {_CHAINED_PREDECESSORS[-1]!r}, through it) may activate {target}"
            ],
        )
    chained_notes: list[str] = []
    if original != predecessor:
        # The chain's mvp-0.26 step (with its own activation) refuses before
        # it takes any step of its own; a refusal there leaves the vault where
        # it was.
        chained = upgrade_to_mvp026(root, clock=clock)
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

    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    registry_service.freeze_manifest(vault, repository, algorithm_version=current, clock=clock)
    vault.config.algorithms.algorithm_version = target
    activate_p0_projection(vault, repository, from_version=current, clock=clock)
    registry_service.refresh(vault, repository, clock=clock)
    rewrite_algorithm_version(root / "learnloop.toml", current, target)
    return UpgradeResult(upgraded=True, from_version=original, to_version=target, notes=chained_notes)


#: The successor's descriptive name for the same upgrade.
upgrade_to_eligibility_decision = upgrade_to_mvp027

__all__ = ["upgrade_to_eligibility_decision", "upgrade_to_mvp027"]
