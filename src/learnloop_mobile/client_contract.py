"""The PWA's copy of the allowlist, generated, never hand-kept (mobile v2 §5.2, §7.2).

Two files in ``apps/learnloop-mobile/src/api/`` come from :data:`ALLOWLIST`:

* ``retryPolicy.json``: the methods the client retries on its own (mobile §6.2);
* ``phoneMethods.ts``: every allowlisted name as a const list, the long ones, and the
  :func:`allowlist_digest` the build embeds, so a stale cached app can tell it is stale.

``tests/test_mobile_phone_contract.py`` fails when a committed file differs from what this
module renders, and rewrites both under ``LEARNLOOP_UPDATE_PHONE_CONTRACT=1``. The PWA's
typed ``call`` takes only a ``PhoneMethod``, so a screen cannot name a method the host
refuses without failing its typecheck.
"""
from __future__ import annotations

import json
from pathlib import Path

from learnloop_mobile.allowlist import ALLOWLIST, allowlist_digest

#: Where the files live, relative to the repository root.
CLIENT_API_DIR = Path("apps") / "learnloop-mobile" / "src" / "api"
RETRY_POLICY = "retryPolicy.json"
PHONE_METHODS = "phoneMethods.ts"


def render_retry_policy() -> str:
    """The retry-safe names in allowlist order, as the client has always read them."""

    retry_safe = [name for name, entry in ALLOWLIST.items() if entry.retry_safe]
    return json.dumps({"retrySafe": retry_safe}, indent=2) + "\n"


def _ts_list(names: list[str]) -> str:
    return "[\n" + "".join(f'  "{name}",\n' for name in names) + "] as const"


def render_phone_methods() -> str:
    names = sorted(ALLOWLIST)
    long_names = sorted(name for name, entry in ALLOWLIST.items() if entry.kind == "long")
    return (
        "// Generated from src/learnloop_mobile/allowlist.py by src/learnloop_mobile/client_contract.py.\n"
        "// Do not edit: tests/test_mobile_phone_contract.py fails on any difference, and rewrites this\n"
        "// file under LEARNLOOP_UPDATE_PHONE_CONTRACT=1.\n"
        "\n"
        "/** What `GET /api/v1/meta` answers when this build and the host agree (spec §5.2). */\n"
        f'export const ALLOWLIST_DIGEST = "{allowlist_digest()}";\n'
        "\n"
        "/** Every method the host lets the phone call. Anything else is a 403. */\n"
        f"export const PHONE_METHODS = {_ts_list(names)};\n"
        "\n"
        "export type PhoneMethod = (typeof PHONE_METHODS)[number];\n"
        "\n"
        "/** Methods that run as durable jobs: a `request_id`, a 15 s wait, then 202 and a poll (§6.3). */\n"
        f"export const LONG_METHODS = {_ts_list(long_names)};\n"
    )


def rendered() -> dict[str, str]:
    """Each generated file's name and its content."""

    return {RETRY_POLICY: render_retry_policy(), PHONE_METHODS: render_phone_methods()}


def write(repository_root: Path) -> list[Path]:
    """Write the files that differ; returns the paths written."""

    written = []
    for name, content in rendered().items():
        path = repository_root / CLIENT_API_DIR / name
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            written.append(path)
    return written
