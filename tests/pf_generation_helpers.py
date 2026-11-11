"""What other test files use from ``tests/test_pf_generation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.db.stores import pf as store
from learnloop.ops.pf_generation import GenerationOptions, generate_practice
from learnloop.vault.loader import load_vault

from tests.pf_fakes import clients


CAPS = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=2000, max_total_tokens=100_000_000,
                 max_estimated_usd=10_000)
DAY = FrozenClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
NEXT_DAY = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def run(paths, *, path="ensemble", caps=CAPS, price=1.0, fakes=None, clock=DAY, dry_run=False, **options):
    options.setdefault("round", "r1")
    return generate_practice(
        load_vault(paths.root), caps=caps, options=GenerationOptions(path=path, **options),
        dry_run=dry_run, price_per_million=price, clients=fakes if fakes is not None else clients(),
        clock=clock,
    )


def all_calls(fakes) -> int:
    seen, total = set(), 0
    for value in fakes.values():
        for fake in value if isinstance(value, list) else [value]:
            if id(fake) not in seen:
                seen.add(id(fake))
                total += len(fake.calls)
    return total


def rows(repository, where="1=1", params=()):
    with repository.connection() as connection:
        return store.candidates(connection, where=where, params=params)


def ledger(repository, task):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM judgment_ledger WHERE task=?", (task,))]
