"""What other test files use from ``tests/test_roles_judges.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json


def _proposals(repository) -> list[dict]:
    with repository.connection() as connection:
        return [{**dict(row), "content": json.loads(row["content_json"])} for row in connection.execute(
            "SELECT v.source_object_id, v.version_ordinal, v.authorial_role, v.object_type, v.status, "
            "v.content_json, c.span_id FROM source_object_versions v "
            "JOIN source_object_citations c ON c.source_object_version_id = v.id "
            "ORDER BY v.source_object_id, v.version_ordinal")]
