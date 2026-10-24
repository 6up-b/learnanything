"""Reader RW2c fix round 2 (3): what a resumed problem restores, read by EITHER
the base code (``git archive 7e7bdff1b``) or the tip, from the same vault, so
a test can require both to serialize a problem's RW2c history alike while
RW2c's switches are off (``test_rw2c_fix_round2.py``).

It opens the vault, then reads ``workbench.help_state`` and ``workbench.get``
for the session and prints them as JSON, with ULIDs and timestamps
normalized. Usage: ``python -m tests.rw2c_state_parity <vault-root>
<session-id>``. Only APIs present at ``7e7bdff1b`` are used; nothing is
asked of a model.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

_ULID = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    if isinstance(value, str):
        return _TIME.sub("<ts>", _ULID.sub("<id>", value))
    return value


def main(root: Path, session_id: str) -> dict:
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(root)

    def call(name: str, params: dict[str, Any]) -> Any:
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    return normalize(json.loads(json.dumps({
        "help_state": call("workbench.help_state", {"sessionId": session_id}),
        "problem": call("workbench.get", {"sessionId": session_id}),
    }, sort_keys=True, default=str)))


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]), sys.argv[2]), sort_keys=True))
