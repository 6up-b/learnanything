"""A due check held open by an inline administration, as ``check.begin_inline`` leaves it, without serving its item:
for tests of what the replies mask, which since the owner's decision on RD7-56 is the begun check's LO only (a check
that is merely due is masked nowhere: masking it would point at it)."""
from __future__ import annotations

from typing import Any

from learnloop.db.stores import check_administrations as store


def hold_open(repository: Any, commitment_id: str, *, item: str = "pi_held", opened_at: str = "2026-01-01T00:00:00Z",
              closed_at: str | None = None, presentation: Any = None) -> str:
    """Open an administration of this check (the one open one), or with ``closed_at`` one already set aside then.
    Returns its token."""

    token = f"adm_{commitment_id}_{opened_at}"
    with repository.connection() as connection:
        store.insert_administration(connection, {
            "administration_token": token, "request_id": f"req_{commitment_id}_{opened_at}", "commitment_id": commitment_id,
            "surface": "reader_inline", "session_id": "ps_held", "practice_item_id": item, "cold": True,
            "protection_method": "test", "opened_at": opened_at, "presentation": {} if presentation is None else presentation})
        if closed_at is not None:
            store.close(connection, token, state="abandoned", now=closed_at)
        connection.commit()
    return token
