"""A due check held open by an inline administration, as ``check.begin_inline`` leaves it, without serving its item:
for tests of what the replies mask, which since the owner's decision on RD7-56 is the begun check's LO only (a check
that is merely due is masked nowhere: masking it would point at it)."""
from __future__ import annotations

from typing import Any

from learnloop.db.stores import check_administrations as store


def hold_open(repository: Any, commitment_id: str, *, item: str = "pi_held") -> str:
    """Open an administration of this check (the one open one). Returns its token."""

    token = f"adm_{commitment_id}"
    with repository.connection() as connection:
        store.insert_administration(connection, {
            "administration_token": token, "request_id": f"req_{commitment_id}", "commitment_id": commitment_id,
            "surface": "reader_inline", "session_id": "ps_held", "practice_item_id": item, "cold": True,
            "protection_method": "test", "opened_at": "2026-01-01T00:00:00Z", "presentation": {}})
        connection.commit()
    return token
