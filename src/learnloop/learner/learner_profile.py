"""Per-vault learner profile: ``profile/learner.yaml`` + the init-wizard claim.

The yaml file is the human-editable source of truth for the learner's declared
starting level; the runtime seam is a ``scope_type="global"`` row in
``learner_claims`` (source ``init_wizard``), which flows through
``covering_learner_claim`` → ``initial_mastery_state_for_learning_object`` →
practice-generation ability/difficulty calibration with no further wiring.

Replace semantics: ``seed_global_learner_claim`` replaces prior init-wizard
global rows (deleted below the successor mvp-0.36, kept as replaced rows from
it on, which no live reader reads). Below the claim-fixes successor
``covering_learner_claim`` breaks specificity ties by pseudo-count, then
highest ``claimed_level``, so an edited-DOWN level would never win against a
stale higher row if we appended instead of replacing (from the successor on
the newest claim wins; the replace keeps one init-wizard row either way).
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.synthesis.brief import INIT_CLAIM_PSEUDO_COUNT, STARTING_LEVEL_CLAIMS, STARTING_LEVELS
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

LEARNER_PROFILE_SCHEMA_VERSION = 1


def read_learner_profile(paths: VaultPaths) -> dict[str, Any] | None:
    path = paths.learner_path
    if not path.exists():
        return None
    data = read_yaml(path)
    level = data.get("starting_level")
    if level not in STARTING_LEVELS:
        return None
    return {
        "starting_level": level,
        "level_note": data.get("level_note") or None,
        "updated_at": data.get("updated_at"),
    }


def write_learner_profile(
    paths: VaultPaths,
    *,
    starting_level: str,
    level_note: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if starting_level not in STARTING_LEVELS:
        raise ValueError(f"Unknown starting_level {starting_level!r}; expected one of {STARTING_LEVELS}")
    data = {
        "schema_version": LEARNER_PROFILE_SCHEMA_VERSION,
        "starting_level": starting_level,
        "level_note": level_note or None,
        "updated_at": utc_now_iso(clock),
    }
    write_yaml(paths.learner_path, data)
    return data


def seed_global_learner_claim(
    repository,
    starting_level: str,
    *,
    keep_replaced: bool = False,
    clock: Clock | None = None,
) -> str:
    """Replace the init-wizard global claim with one for ``starting_level``.

    ``keep_replaced`` (the successor mvp-0.36, ``mastery.replaced_claims_kept``
    of the vault): the earlier claim stays as a replaced row, so replay seeds
    an LO first practised before the change from the level in force then.
    Below it the earlier claim is deleted, as before."""

    claimed_level = STARTING_LEVEL_CLAIMS.get(starting_level)
    if claimed_level is None:
        raise ValueError(f"Unknown starting_level {starting_level!r}; expected one of {STARTING_LEVELS}")
    return repository.replace_learner_claim(
        {
            "claim_type": "self_rating",
            "scope_type": "global",
            "claimed_level": claimed_level,
            "prior_pseudo_count": INIT_CLAIM_PSEUDO_COUNT,
            "source": "init_wizard",
        },
        keep_replaced=keep_replaced,
        clock=clock,
    )
