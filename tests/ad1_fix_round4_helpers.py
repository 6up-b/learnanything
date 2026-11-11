"""What other test files use from ``tests/test_ad1_fix_round4.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

import yaml

from learnloop.vault.loader import load_vault


EXAM_SET = "exam_scope_added"


def _add_exam_scope(paths) -> None:
    """The owner's source-set edit: an exam scope, in the vault's own file."""

    from learnloop.vault.paths import VaultPaths

    target = VaultPaths(paths.root, load_vault(paths.root).config).source_sets_path
    payload = yaml.safe_load(target.read_text(encoding="utf-8")) if target.exists() else None
    payload = payload or {"schema_version": 1, "source_sets": []}
    payload["source_sets"].append({"id": EXAM_SET, "subject_id": "linear-algebra", "title": "The final exam"})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _bulk_vault(paths, count: int):
    real = load_vault(paths.root)
    base = real.practice_items["pi_m1a"]
    items = {f"pi_bulk_{index:04d}": base.model_copy(update={"id": f"pi_bulk_{index:04d}",
                                                             "prompt": f"Imported stem {index}."})
             for index in range(count)}
    return SimpleNamespace(practice_items=items, config=real.config, root=real.root, source_sets=[])


def _builds(paths):
    from learnloop.hints.map_builder import BackgroundBuilds

    builds = BackgroundBuilds()
    builds.bind(paths.sqlite_path)
    return builds
