"""What other test files use from ``tests/test_hint_service.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.hints import service as S
from learnloop.vault.loader import load_vault

from tests.hint_fakes import ITEM, WORK, WriterFake, hint_vault, store_map


SESSION = "sess_1"


def _setup(tmp_path, *, config: str = "", with_map: bool = True, **item):
    paths = hint_vault(tmp_path, config=config, **item)
    if with_map:
        store_map(paths)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _request(**overrides) -> S.HintRequestV1:
    values = {"practice_item_id": ITEM, "session_id": SESSION, "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    return S.HintRequestV1(**values)


def _ask(vault, repository, *, writer=None, chooser=None, seed="seed-1", **overrides) -> S.HintResultV1:
    return S.request_hint(vault, repository, _request(**overrides), writer_client=writer or WriterFake(),
                          chooser_client_factory=(lambda: chooser) if chooser is not None else (lambda: None),
                          seed=seed)
