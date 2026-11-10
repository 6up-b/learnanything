"""``why.get``: the glass-box view's read of why a decision went the way it did (ADR-017, refactor B9).

The same reader as ``learnloop why`` (``learnloop.why.reader.answer``), on a read-only connection, returned as ids,
numbers and codes only (``reader.codes_only``): never a prompt, an output, an item's text or a plain-English reason,
and never ``--payload``'s receipts. Desktop only: it is not on the phone host's allowlist.
"""

from __future__ import annotations

from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

WHY_RPCS = ("why.get",)


class WhyInput(ParamsModel):
    target: str = "latest"
    kind: str | None = None
    first_build: bool = False


@method("why.get", WhyInput)
def why_get(ctx: SidecarContext, params: WhyInput) -> dict[str, Any]:
    from learnloop.db.repositories import Repository
    from learnloop.why import reader

    vault, repository = ctx.require_vault()
    read_only = Repository.attach(repository.sqlite_path, read_only=True)
    found = reader.answer(read_only, params.target, kind=params.kind, first_build=params.first_build, loaded=vault)
    if found is None:
        raise SidecarError("why_not_found", f"No decision record or old row answers {params.target!r}.")
    cleaned, withheld = reader.codes_only(found)
    # Not ``versioned``: its camelCasing renames every dict key, and many keys here are data (rule codes in
    # ``excluded_by_rule``, option refs in a mix's chances). The answer keeps ``learnloop why --json``'s exact shape.
    return {"version": 1, "why": cleaned, "withheld": withheld}
