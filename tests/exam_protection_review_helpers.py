"""What other test files use from ``tests/test_exam_protection_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml

from tests.source_retrieval_fakes import seed_source


CLOCK = FrozenClock(datetime(2026, 10, 13, tzinfo=UTC))


def _with_exercise(root, practice_item_id: str, *, source_id: str, extraction_id: str, span_id: str) -> None:
    """Give an item the canonical exercise an import records."""

    vault = load_vault(root)
    path = next(VaultPaths(vault.root, vault.config).root.rglob(f"{practice_item_id}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": source_id, "extraction_id": extraction_id,
                                     "span_ids": [span_id], "relation": "verbatim"}
    upsert_practice_item(root, payload, clock=CLOCK)


def _key_checked(root, repository, practice_item_id: str) -> None:
    """Record a verified key check of an imported exercise's current content.

    From mvp-0.18 (the answer-key gate, owner decision C3) an exercise import whose key is not
    verified never enters an exam pool or a certification cold probe (D2a: the basic vault is
    at the head, so these fixtures verify the key they rely on)."""

    from learnloop.content.authoring.source_exercise_import import LadderResult, record_key_check

    item = load_vault(root).practice_items[practice_item_id]
    record_key_check(repository, item=item, result=LadderResult("checked", "test"), trigger="verify",
                     started_at=CLOCK.now().isoformat().replace("+00:00", "Z"), clock=CLOCK)


def _problem_book(repository) -> None:
    """``ext_problems``: a problems unit (``s1`` header, ``s2`` problem) and a notes unit (``s4``, ``s5``)."""

    seed_source(repository, source_id="src_problems", revision_id="rev_problems", extraction_id="ext_problems",
                title="Problem book", units={"ex": ("Problems", [("Problem 1: compute 7 times 6.", 1)]),
                                             "notes": ("Notes", [("Multiplication is repeated addition.", 2)])})


def _switch_off(root) -> None:
    """``goals.held_out_selection = false`` (under the vault's ``[goals]`` table when it has one)."""

    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "\n[goals]\n" in text:
        text = text.replace("\n[goals]\n", "\n[goals]\nheld_out_selection = false\n", 1)
    else:
        text = text.rstrip("\n") + "\n\n[goals]\nheld_out_selection = false\n"
    config.write_text(text, encoding="utf-8")
    assert load_vault(root).config.goals.held_out_selection is False


def _reserved_pool(tmp_path):
    from learnloop.goals.exam_pool import reserve_exam_pool
    from tests.exam_pool_helpers import NOW, _vault_with_items

    vault, paths, repository = _vault_with_items(tmp_path)
    _problem_book(repository)
    _with_exercise(paths.root, "pi_pool_apply_mid", source_id="src_problems", extraction_id="ext_problems",
                   span_id="s2")
    _key_checked(paths.root, repository, "pi_pool_apply_mid")
    vault = load_vault(paths.root)
    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=3, clock=FrozenClock(NOW))
    assert {"pi_pool_apply_mid", "pi_pool_derive_hard"} <= set(report.reserved_item_ids)
    return paths, repository
