"""What ``tests/test_normalize_cases.py`` shares: the vaults and answers its cases build, the seeded ULID stream, and
the record of a normalizer result a case compares with its golden file."""

from __future__ import annotations

import dataclasses
import json
import os
import random
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from learnloop.content.synthesis.source_set_synthesis import _collect_inputs, _normalize
from learnloop.vault.loader import load_vault

from tests.facet_authority_helpers import NOW, SUBJECT, _source_set
from tests.source_append_helpers import _bootstrap_and_add

GOLDEN_DIR = Path(__file__).parent / "goldens" / "synthesis_normalize"
WRITE = os.environ.get("NORMALIZE_GOLDEN_WRITE") == "1"
ULID_MS = 1_790_000_000_000


def seed_ids(monkeypatch) -> None:
    """The process's ULID stream seeded and its clock held, so every minted id is reproducible."""

    from learnloop import ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: ULID_MS)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=random.Random(20261113).getrandbits))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)


def world(tmp_path, *, add_role="exam"):
    """A bootstrapped, applied study map with a second member (an exam paper by default): the vault, the inputs the
    normalizer reads, and the repository."""

    root, repo = _bootstrap_and_add(tmp_path, add_role=add_role)
    vault = load_vault(root)
    inputs = _collect_inputs(repo, vault, _source_set(root))
    return vault, inputs, repo


def run(synth, vault, inputs, **kwargs):
    return _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT, **kwargs)


def record(normalized: Any) -> dict[str, Any]:
    """Every field of a ``Normalized``, as plain JSON values (gate items and citations as their dataclass fields)."""

    def plain(value: Any) -> Any:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
        if isinstance(value, dict):
            return {str(key): plain(item) for key, item in value.items()}
        if isinstance(value, list | tuple):
            return [plain(item) for item in value]
        if isinstance(value, set | frozenset):
            return sorted((plain(item) for item in value), key=json.dumps)
        return value

    return plain(normalized)


def check(name: str, normalized: Any) -> None:
    path = GOLDEN_DIR / f"{name}.json"
    text = json.dumps(record(normalized), indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    if WRITE:
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return
    assert path.exists(), f"no golden for {name}: regenerate with NORMALIZE_GOLDEN_WRITE=1"
    assert json.loads(text) == json.loads(path.read_text(encoding="utf-8")), f"{name}: the normalizer's output moved"
