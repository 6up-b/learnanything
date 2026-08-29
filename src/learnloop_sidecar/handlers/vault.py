from __future__ import annotations

from typing import Any

from learnloop.bootstrap import BootstrapError, create_vault as bootstrap_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class CreateVaultInput(ParamsModel):
    path: str
    # Optional first subject to seed at creation time (title → kebab-case id).
    # The NewVault wizard uses this so the bootstrap study-map build has a
    # subject to bind to; omit it and the vault is created with no subjects.
    subject: str | None = None
    # Optional declared learner level (closed ordinal,
    # ``learnloop.content.synthesis.brief.STARTING_LEVELS``).
    # Persists profile/learner.yaml and seeds the global init-wizard learner claim
    # so initial mastery/ability/difficulty calibration start from the learner's
    # self-report instead of the uninformative 0.5 prior.
    starting_level: str | None = None
    level_note: str | None = None


@method("create_vault", CreateVaultInput)
def create_vault(ctx: SidecarContext, params: CreateVaultInput) -> dict[str, Any]:
    """Create (or re-initialize) a LearnLoop vault at ``path`` and return its root.

    Delegates to :func:`learnloop.bootstrap.create_vault`, the same validated
    application bootstrap used by the CLI. It does NOT bind the sidecar to the
    new vault; the caller re-selects it after creation.

    A brand-new vault inherits the currently-loaded vault's persisted ``[ai]``
    provider selection (routing + non-codex profiles): the Settings tab writes
    those per-vault, so without this the fresh vault would fall back to the
    template's codex routing even though the user configured e.g. OpenRouter.
    Existing vault AI settings are never touched; with no vault loaded,
    template defaults stand.

    Guard: refuse a directory that already has unrelated content and is not a
    vault, so we never scatter vault scaffolding into someone's populated folder.
    """

    try:
        result = bootstrap_vault(
            params.path,
            subject=params.subject,
            starting_level=params.starting_level,
            level_note=params.level_note,
            inherit_ai_from=ctx.vault.root if ctx.vault is not None else None,
        )
    except BootstrapError as exc:
        # Keep the RPC's existing closed error-code vocabulary. Subject names
        # form a path segment, so their new preflight refusal uses the existing
        # generic invalid_path arm rather than adding a wire-visible code.
        code = "invalid_path" if exc.code == "invalid_subject" else exc.code
        raise SidecarError(code, str(exc)) from exc

    return versioned(
        {"vault_root": str(result.root), "subject_id": result.subject_id}
    )


class SetLearnerProfileInput(ParamsModel):
    starting_level: str
    level_note: str | None = None


@method("get_learner_profile", EmptyParams)
def get_learner_profile(ctx: SidecarContext, params: EmptyParams) -> dict[str, Any]:
    """The vault's declared learner level (profile/learner.yaml), or nulls."""

    from learnloop.learner.learner_profile import read_learner_profile
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

    from learnloop.content.synthesis.brief import STARTING_LEVELS
    from learnloop.learner.learner_profile import seed_global_learner_claim, write_learner_profile
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
