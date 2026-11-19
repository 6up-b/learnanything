"""Where every AI route of a walk vault would send a request, in the walk's own environment.

Run by the bridge before the browser opens, with exactly the environment the
sidecar gets. Prints one JSON object: each route's provider, its kind
(``fake``: the walk's local fake model; ``unset``; ``unreachable``: a real
provider with no credential in this environment; ``live``: a real provider
that would answer) and, for a route that is not live, the runtime's own
readiness message (a live route's message can carry the signed-in account's
email address, so only its status is kept). The bridge refuses to start in
fake mode when any route is ``live``.

    python scripts/ux_walk/route_check.py <vault> <fake-profile-name>
"""

from __future__ import annotations

import json
import sys
import typing
from pathlib import Path


def classify(vault: Path, fake_profile: str) -> dict:
    from learnloop.ai.routing import AITask, provider_for_task
    from learnloop.ai.runtime import check_ai_runtime
    from learnloop.config import load_config

    config = load_config(vault / "learnloop.toml")
    routes = {}
    readiness: dict[str, dict] = {}
    for task in typing.get_args(AITask):
        name = provider_for_task(config, task).provider_name or ""
        if not name:
            routes[task] = {"provider": None, "kind": "unset"}
            continue
        if name == fake_profile:
            routes[task] = {"provider": name, "kind": "fake"}
            continue
        if name not in readiness:
            try:
                report = check_ai_runtime(vault, config, provider_name=name)
                readiness[name] = {"ready": report.ready, "status": report.status, "message": report.message}
            except Exception as exc:  # noqa: BLE001 - a profile the runtime cannot judge counts as live
                readiness[name] = {"ready": True, "status": "unknown", "message": f"{type(exc).__name__}: {exc}"}
        state = readiness[name]
        if state["ready"]:
            # A ready route's message can name the signed-in account (its email): keep it out of the walk's files.
            routes[task] = {"provider": name, "kind": "live", "status": state["status"]}
        else:
            routes[task] = {"provider": name, "kind": "unreachable", **state}
    return {"routes": routes, "live": sorted(task for task, route in routes.items() if route["kind"] == "live")}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(classify(Path(argv[0]), argv[1]), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
