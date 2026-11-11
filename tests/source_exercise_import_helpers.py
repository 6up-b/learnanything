"""What other test files use from ``tests/test_source_exercise_import.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.db.stores.source_service import import_row, key_checks_for_item

from tests.source_service_fakes import service_clients


def _import(paths, repository, span, llm, **kwargs):
    return SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text", span_ids=[span],
                                      caller=kwargs.pop("caller", "learner"), clients=service_clients(llm), **kwargs)


class _ProcessDeath(BaseException):
    """Stands for the process exiting: nothing after it runs, nothing catches it."""


def _row(repository, import_id):
    with repository.connection() as connection:
        return import_row(connection, import_id)


def _checks(repository, item_id):
    with repository.connection() as connection:
        return key_checks_for_item(connection, item_id)
