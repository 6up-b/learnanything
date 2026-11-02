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


def _decode_ulid(value: str) -> tuple[int, int] | None:
    """A ULID's (timestamp ms, randomness), or None for anything that is not one."""

    text = str(value or "").upper()
    if len(text) != 26 or any(char not in _CROCKFORD for char in text):
        return None
    number = 0
    for char in text:
        number = (number << 5) | _CROCKFORD.index(char)
    if number >> 128:
        return None
    return number >> _RANDOMNESS_BITS, number & _RANDOMNESS_MAX


#: How far past a stored floor a ULID's randomness may land (``keep``: spacing only, so two
#: processes lifted to the same floor do not mint the same id; any width short of the 80
#: random bits keeps the order).
_FLOOR_JITTER_BITS = 32


def new_ulid_after(floor: str | None) -> str:
    """A ULID that sorts after every ULID this process generated before it and after
    ``floor``, a ULID read from storage (Codex review F2 of followups-nov1c): process-local
    monotonicity cannot order an id against one a process with a clock running ahead
    persisted before a restart, so a caller that needs that order reads the newest stored
    id and passes it here. Anything that is not a ULID (``""``, None) is no floor."""

    global _last_timestamp_ms, _last_randomness
    parsed = _decode_ulid(floor) if floor else None
    if parsed is not None:
        with _ulid_lock:
            if parsed >= (_last_timestamp_ms, _last_randomness):
                _last_timestamp_ms = parsed[0]
                _last_randomness = min(parsed[1] + secrets.randbits(_FLOOR_JITTER_BITS), _RANDOMNESS_MAX)
    return new_ulid()


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
