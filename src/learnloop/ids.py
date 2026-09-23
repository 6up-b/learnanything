from __future__ import annotations

import secrets
import threading
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_crockford(value: int, length: int) -> str:
    chars: list[str] = []
    for _ in range(length):
        chars.append(_CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))


_TIMESTAMP_MASK = (1 << 48) - 1
_RANDOMNESS_BITS = 80
_RANDOMNESS_MAX = (1 << _RANDOMNESS_BITS) - 1

# Rows are ordered by (created_at, id), and under an injected frozen clock every
# created_at ties, so ids minted in one process must sort in creation order.
# The ULID monotonic rule gives that: within a repeated millisecond the random
# part is incremented rather than redrawn.
_ulid_lock = threading.Lock()
_last_timestamp_ms = -1
_last_randomness = 0


def _wall_clock_ms() -> int:
    return int(time.time() * 1000) & _TIMESTAMP_MASK


def new_ulid() -> str:
    """Generate a ULID that sorts after every ULID this process generated before it."""

    global _last_timestamp_ms, _last_randomness
    with _ulid_lock:
        timestamp_ms = _wall_clock_ms()
        if timestamp_ms <= _last_timestamp_ms:
            # Same millisecond, or the wall clock stepped backwards: keep the
            # previous timestamp so the id cannot sort before its predecessor.
            timestamp_ms = _last_timestamp_ms
            randomness = _last_randomness + 1
            if randomness > _RANDOMNESS_MAX:
                # 2**80 ids in one millisecond cannot happen in practice; moving
                # to the next millisecond keeps the order without raising.
                timestamp_ms = (timestamp_ms + 1) & _TIMESTAMP_MASK
                randomness = secrets.randbits(_RANDOMNESS_BITS - 1)
        else:
            randomness = secrets.randbits(_RANDOMNESS_BITS)
        _last_timestamp_ms = timestamp_ms
        _last_randomness = randomness
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
