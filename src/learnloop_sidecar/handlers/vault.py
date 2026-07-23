from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from learnloop.config import global_ai_defaults_path
from learnloop.ids import kebab_case
from learnloop.services.settings_store import SettingsStoreError, copy_ai_settings
from learnloop.vault.loader import add_subject, init_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

logger = logging.getLogger(__name__)


class CreateVaultInput(ParamsModel):
    path: str
    # Optional first subject to seed at creation time (title → kebab-case id).
    # The NewVault wizard uses this so the bootstrap study-map build has a
    # subject to bind to; omit it and the vault is created with no subjects.
    subject: str | None = None
    # Optional declared learner level (closed ordinal, services.brief.STARTING_LEVELS).
    # Persists profile/learner.yaml and seeds the global init-wizard learner claim
    # so initial mastery/ability/difficulty calibration start from the learner's
    # self-report instead of the uninformative 0.5 prior.
    starting_level: str | None = None
    level_note: str | None = None


@method("create_vault", CreateVaultInput)
def create_vault(ctx: SidecarContext, params: CreateVaultInput) -> dict[str, Any]:
    """Create (or re-initialize) a LearnLoop vault at ``path`` and return its root.

    Wraps :func:`learnloop.vault.loader.init_vault` (the same primitive the
    ``learnloop init`` CLI command uses). ``init_vault`` is idempotent — every
    write is guarded — so pointing it at an existing vault is a safe no-op that
    just returns the root. It does NOT bind the sidecar to the new vault; the
    caller re-selects it (Rust ``select_vault`` respawns against the new path)
    and then ``load_vault``, mirroring how the vault switcher works elsewhere.

    A brand-new vault inherits the currently-loaded vault's persisted ``[ai]``
    provider selection (routing + non-codex profiles): the Settings tab writes
    those per-vault, so without this the fresh vault would fall back to the
    template's codex routing even though the user configured e.g. OpenRouter.
    Existing vaults are never touched; with no vault loaded, template defaults
    stand.

    Guard: refuse a directory that already has unrelated content and is not a
    vault, so we never scatter vault scaffolding into someone's populated folder.
    """

    raw = params.path.strip()
    if not raw:
        raise SidecarError("invalid_path", "A vault directory path is required.")

    target = Path(raw).expanduser()
    was_vault = (target / "learnloop.toml").exists()
    if target.exists():
        if not target.is_dir():
            raise SidecarError("invalid_path", f"{target} exists and is not a directory.")
        if not was_vault and any(target.iterdir()):
            raise SidecarError(
                "vault_dir_not_empty",
                (
                    f"{target} is not empty and is not a LearnLoop vault. "
                    "Choose an empty directory or an existing vault."
                ),
            )

    created = init_vault(target)

    if not was_vault:
        inherited = False
        # First choice: inherit from the vault the user is creating this one from.
        if ctx.vault is not None and ctx.vault.root.resolve() != created:
            try:
                inherited = copy_ai_settings(
                    ctx.vault.root / "learnloop.toml", created / "learnloop.toml"
                )
            except SettingsStoreError as exc:
                logger.warning("new-vault AI inheritance from open vault failed: %s", exc)
        # Fallback: no open vault to inherit from (or it had nothing persisted) —
        # seed from the machine-global provider selection so the new vault adopts
        # the user's configured backend instead of the codex template.
        if not inherited:
            defaults = global_ai_defaults_path()
            if defaults.exists():
                try:
                    copy_ai_settings(defaults, created / "learnloop.toml")
                except SettingsStoreError as exc:
                    logger.warning("new-vault AI inheritance from global defaults failed: %s", exc)

    subject_id: str | None = None
    subject_title = (params.subject or "").strip()
    if subject_title:
        subject_id = kebab_case(subject_title)
        add_subject(created, subject_id, subject_title)

    if params.starting_level:
        _write_learner_level(created, params.starting_level, params.level_note)

    return versioned({"vault_root": str(created), "subject_id": subject_id})


def _write_learner_level(root: Path, starting_level: str, level_note: str | None) -> None:
    """Persist profile/learner.yaml and seed the global learner claim.

    Instantiating Repository applies migrations, so this also creates
    state.sqlite for a brand-new vault — the claim exists before any synthesis
    or state sync runs.
    """

    from learnloop.config import load_config
    from learnloop.db.repositories import Repository
    from learnloop.services.brief import STARTING_LEVELS
    from learnloop.services.learner_profile import seed_global_learner_claim, write_learner_profile
    from learnloop.vault.paths import VaultPaths

    if starting_level not in STARTING_LEVELS:
        raise SidecarError(
            "invalid_starting_level",
            f"Unknown starting level '{starting_level}'. Expected one of: {', '.join(STARTING_LEVELS)}.",
        )
    paths = VaultPaths(root, load_config(root / "learnloop.toml"))
    write_learner_profile(paths, starting_level=starting_level, level_note=level_note)
    repository = Repository(paths.sqlite_path)
    seed_global_learner_claim(repository, starting_level)


class SetLearnerProfileInput(ParamsModel):
    starting_level: str
    level_note: str | None = None


@method("get_learner_profile", EmptyParams)
def get_learner_profile(ctx: SidecarContext, params: EmptyParams) -> dict[str, Any]:
    """The vault's declared learner level (profile/learner.yaml), or nulls."""

    from learnloop.services.learner_profile import read_learner_profile
    from learnloop.vault.paths import VaultPaths

    vault, _repository = ctx.require_vault()
    profile = read_learner_profile(VaultPaths(vault.root, vault.config)) or {}
    return versioned(
        {
            "starting_level": profile.get("starting_level"),
            "level_note": profile.get("level_note"),
            "updated_at": profile.get("updated_at"),
        }
    )


@method("set_learner_profile", SetLearnerProfileInput)
def set_learner_profile(ctx: SidecarContext, params: SetLearnerProfileInput) -> dict[str, Any]:
    """Write profile/learner.yaml and replace the global init-wizard claim.

    Already-materialized mastery states are NOT retro-seeded — the claim only
    informs states created after this point (state_sync fills missing rows).
    """

    from learnloop.services.brief import STARTING_LEVELS
    from learnloop.services.learner_profile import seed_global_learner_claim, write_learner_profile
    from learnloop.vault.paths import VaultPaths

    vault, repository = ctx.require_vault()
    if params.starting_level not in STARTING_LEVELS:
        raise SidecarError(
            "invalid_starting_level",
            f"Unknown starting level '{params.starting_level}'. Expected one of: {', '.join(STARTING_LEVELS)}.",
        )
    profile = write_learner_profile(
        VaultPaths(vault.root, vault.config),
        starting_level=params.starting_level,
        level_note=params.level_note,
    )
    seed_global_learner_claim(repository, params.starting_level)
    return versioned(
        {
            "starting_level": profile["starting_level"],
            "level_note": profile["level_note"],
            "updated_at": profile["updated_at"],
        }
    )
