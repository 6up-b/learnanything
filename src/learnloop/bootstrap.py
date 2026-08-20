"""Application-level vault creation shared by the CLI and sidecar.

Filesystem scaffolding remains in :mod:`learnloop.vault.loader`.  This module
owns the application policy around it: request validation, optional subject and
learner-profile seeding, and AI-settings inheritance for a brand-new vault.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from learnloop.clock import Clock
from learnloop.config import global_ai_defaults_path, load_config
from learnloop.ids import kebab_case
from learnloop.content.synthesis.brief import STARTING_LEVELS
from learnloop.learner.learner_profile import (
    seed_global_learner_claim,
    write_learner_profile,
)
from learnloop.ops.settings_store import SettingsStoreError, copy_ai_settings
from learnloop.vault.loader import add_subject, init_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

logger = logging.getLogger(__name__)


class BootstrapError(ValueError):
    """A validated vault-creation refusal with a stable adapter-facing code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class CreateVaultResult:
    root: Path
    subject_id: str | None


@dataclass(frozen=True)
class _ValidatedRequest:
    root: Path
    was_vault: bool
    subject_title: str | None
    subject_id: str | None
    starting_level: str | None


def create_vault(
    root: Path | str,
    *,
    subject: str | None = None,
    starting_level: str | None = None,
    level_note: str | None = None,
    inherit_ai_from: Path | None = None,
    force: bool = False,
    clock: Clock | None = None,
) -> CreateVaultResult:
    """Create or complete a vault after validating every input.

    ``force`` permits scaffolding inside a populated non-vault directory.  It
    never permits replacing a file and does not overwrite guarded scaffold or
    configuration files.  Existing vaults are completed idempotently and never
    receive inherited AI settings.
    """

    request = _validate_request(
        root,
        subject=subject,
        starting_level=starting_level,
        force=force,
    )

    created = init_vault(request.root, clock=clock)
    if not request.was_vault:
        _inherit_ai_settings(created, inherit_ai_from=inherit_ai_from)

    if request.subject_title is not None and request.subject_id is not None:
        add_subject(
            created,
            request.subject_id,
            request.subject_title,
            clock=clock,
        )

    if request.starting_level is not None:
        paths = VaultPaths(created, load_config(created / "learnloop.toml"))
        write_learner_profile(
            paths,
            starting_level=request.starting_level,
            level_note=level_note,
            clock=clock,
        )
        repository = open_vault_repository(created, paths.sqlite_path)
        seed_global_learner_claim(
            repository,
            request.starting_level,
            clock=clock,
        )

    return CreateVaultResult(root=created, subject_id=request.subject_id)


def _validate_request(
    root: Path | str,
    *,
    subject: str | None,
    starting_level: str | None,
    force: bool,
) -> _ValidatedRequest:
    raw_path = str(root).strip()
    if not raw_path:
        raise BootstrapError("invalid_path", "A vault directory path is required.")

    target = Path(raw_path).expanduser().resolve()
    subject_title = (subject or "").strip() or None
    subject_id = kebab_case(subject_title) if subject_title is not None else None
    if subject_title is not None and not subject_id:
        raise BootstrapError(
            "invalid_subject",
            "The subject name must contain at least one letter or number.",
        )

    normalized_level = starting_level or None
    if normalized_level is not None and normalized_level not in STARTING_LEVELS:
        raise BootstrapError(
            "invalid_starting_level",
            (
                f"Unknown starting level '{normalized_level}'. Expected one of: "
                f"{', '.join(STARTING_LEVELS)}."
            ),
        )

    config_path = target / "learnloop.toml"
    was_vault = config_path.exists()
    if target.exists():
        if not target.is_dir():
            raise BootstrapError(
                "invalid_path", f"{target} exists and is not a directory."
            )
        if was_vault and not config_path.is_file():
            raise BootstrapError(
                "invalid_path", f"{config_path} exists and is not a file."
            )
        if not was_vault and not force and any(target.iterdir()):
            raise BootstrapError(
                "vault_dir_not_empty",
                (
                    f"{target} is not empty and is not a LearnLoop vault. "
                    "Choose an empty directory or an existing vault."
                ),
            )

    return _ValidatedRequest(
        root=target,
        was_vault=was_vault,
        subject_title=subject_title,
        subject_id=subject_id,
        starting_level=normalized_level,
    )


def _inherit_ai_settings(root: Path, *, inherit_ai_from: Path | None) -> None:
    inherited = False
    if inherit_ai_from is not None and inherit_ai_from.resolve() != root:
        try:
            inherited = copy_ai_settings(
                inherit_ai_from.resolve() / "learnloop.toml",
                root / "learnloop.toml",
            )
        except SettingsStoreError as exc:
            logger.warning("new-vault AI inheritance from open vault failed: %s", exc)

    if inherited:
        return
    defaults = global_ai_defaults_path()
    if not defaults.exists():
        return
    try:
        copy_ai_settings(defaults, root / "learnloop.toml")
    except SettingsStoreError as exc:
        logger.warning("new-vault AI inheritance from global defaults failed: %s", exc)
