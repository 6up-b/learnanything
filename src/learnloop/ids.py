from __future__ import annotations

import secrets
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_crockford(value: int, length: int) -> str:
    chars: list[str] = []
    for _ in range(length):
        chars.append(_CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def new_ulid() -> str:
    """Generate a ULID-like sortable identifier without an external runtime dependency."""

    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    randomness = secrets.randbits(80)
    return _encode_crockford(timestamp_ms, 10) + _encode_crockford(randomness, 16)


def kebab_case(value: str) -> str:
    chars: list[str] = []
    previous_dash = False
    for char in value.strip().lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "".join(chars).strip("-")


def snake_case(value: str) -> str:
    return kebab_case(value).replace("-", "_")
