"""What other test files use from ``tests/test_reader_ca1_astra_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml


def _owned(paths, item_id: str) -> list:
    refs = load_vault(paths.root).practice_items[item_id].provenance.source_refs
    return [ref.model_extra.get("owned") for ref in refs]


def _mark_every_block_owned(paths, item_id: str) -> None:
    """The rule before this fix: a single-item import marked every block it was given."""

    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    for ref in payload["provenance"]["source_refs"]:
        ref["owned"] = True
    write_yaml(path, payload)
