"""What other test files use from ``tests/test_required_method_items.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import yaml

from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO


def _add_concept_and_lo(paths, concept_id: str, concept_type: str, lo_id: str) -> None:
    concepts = yaml.safe_load(paths.concepts_path.read_text(encoding="utf-8"))
    concepts["concepts"][concept_id] = {
        "title": concept_id.replace("_", " ").title(), "type": concept_type, "aliases": [], "description": "d",
        "tags": [], "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }
    write_yaml(paths.concepts_path, concepts)
    write_yaml(paths.learning_object_path("linear-algebra", lo_id), {
        "schema_version": 1, "id": lo_id, "title": lo_id, "subjects": ["linear-algebra"], "concept": concept_id,
        "knowledge_type": "concept", "status": "active", "summary": "s", "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })
