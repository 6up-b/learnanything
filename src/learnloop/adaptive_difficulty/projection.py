"""The projected vault and repository an AD operation hands its readers (the AD23 redesign).

``op.repository`` is the operation's repository facade: every attribute is the raw repository's,
except the document-IR loader, which reads through the material view's rules (the IR tables are
protected: ``protected_tables``). ``op.vault`` is the vault as AD may see it."""

from __future__ import annotations

from typing import Any


class ProjectedRepository:
    """The raw repository, with its document-IR loader read through the operation's view."""

    __slots__ = ("_ad_raw_repository", "_ad_view")

    def __init__(self, repository: Any, view: Any) -> None:
        object.__setattr__(self, "_ad_raw_repository", repository)
        object.__setattr__(self, "_ad_view", view)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ad_raw_repository, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._ad_raw_repository, name, value)

    def __repr__(self) -> str:
        return f"ProjectedRepository({self._ad_raw_repository!r})"

    def load_document_ir(self, extraction_id: str) -> Any:
        return self._ad_view.document_ir(self._ad_raw_repository, extraction_id)


def project_vault(view: Any) -> Any:
    return view.vault


def project_repository(repository: Any, view: Any) -> Any:
    return ProjectedRepository(getattr(repository, "_ad_raw_repository", repository), view)


__all__ = ["ProjectedRepository", "project_repository", "project_vault"]
