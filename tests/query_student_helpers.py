"""What other test files use from ``tests/test_query_student.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from learnloop.local_embeddings import student_pins as SP
from learnloop.source_retrieval import query_student as Q
from learnloop.source_retrieval import student_encoder as E

from tests.query_student_fakes import set_up_bases
from tests.source_retrieval_fakes import loaded


# -- synthetic questions -----------------------------------------------------------------------------------
def _space(paths):
    manifest, space, reason = Q.context(loaded(paths))
    assert manifest is not None, reason
    return space


def _adopt(root, space, *, base=SP.PRIMARY_BASE, sha="a" * 64):
    set_up_bases(root)
    directory = E.checkpoint_dir(root, space, sha)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "student.json").write_text(json.dumps({"canaries": {}}), encoding="utf-8")
    E.adoption_path(root, space).write_text(json.dumps({"checkpoint_sha256": sha, "base_name": base}), encoding="utf-8")
    return sha
