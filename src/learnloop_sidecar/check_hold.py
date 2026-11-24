"""While an inline check is open (mvp-0.69, spec §12.6.4), work that would show or send what its veils hold waits.

The desks disable these controls with the reason, but a control is not the boundary: a retry, a deferred job or
another client could still start one. Each job-accepting RPC that could reveal the check's material calls
:func:`refuse_while_check_open` at acceptance: a companion ask, an ink transcription, a figure request (Show me) and
a lesson's opening. The refusal (``check_open``) names the open administration, so the client can say why.
"""
from __future__ import annotations

from typing import Any

from learnloop_sidecar.errors import SidecarError


def open_check(repository: Any) -> str | None:
    """The open inline administration's token, or None."""

    from learnloop.db.stores import check_administrations as store

    with repository.connection() as connection:
        admin = store.open_administration(connection) if store.table_present(connection) else None
    return str(admin["administration_token"]) if admin is not None else None


def refuse_while_check_open(repository: Any) -> None:
    token = open_check(repository)
    if token is not None:
        raise SidecarError("check_open", "This waits until your check is answered.",
                           details={"administration_token": token})


def drain_after_check(ctx: Any, vault: Any, repository: Any) -> None:
    """After an inline check closes: the pad words held back while it was open are emitted (the reconcile a vault's
    open runs). Never fails the close."""

    import logging

    from learnloop.pads import emission

    try:
        if open_check(repository) is None and emission.reconcile(vault, repository).queued:
            ctx.post_attempt_worker.notify()
    except Exception:  # noqa: BLE001 - the close already committed; the next open reconciles
        logging.getLogger(__name__).warning("could not emit the pads' words held during the check", exc_info=True)


__all__ = ["drain_after_check", "open_check", "refuse_while_check_open"]
