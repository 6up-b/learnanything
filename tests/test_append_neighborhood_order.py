"""The append neighbourhood's record does not follow the process's hash seed.

A new inventory's concept names, aliases and prerequisite hints are sets. When two of them match the same existing
facet or concept, the reason the neighbourhood records names the first one tried; tried in set order, that name
followed ``PYTHONHASHSEED``, and so did the append manifest's scope (its ``neighborhood`` record) and hash. The
request itself never moved: its context carries no reasons, and every name scores the same.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

#: Runs in a fresh interpreter under a given hash seed: one facet and one concept that two names (a name and its
#: alias) and two prerequisite hints all match, with nothing else in the vault or the database.
_SELECT = """
import json
from types import SimpleNamespace

from learnloop.content.synthesis.append_neighborhood import select_neighborhood

facet = SimpleNamespace(
    id="fct_symmetric", concept_id="symmetric_matrix", kind="definition", title="Symmetric matrices",
    claim="A symmetric matrix equals its transpose.",
    aliases=[], preconditions=[], postconditions=[], error_signatures=[], instructional_repairs=[],
    semantic_fingerprint=None,
)
concept = SimpleNamespace(id="symmetric_matrix", title="Symmetric matrix", type="concept",
                          aliases=["symmetric matrices"])
vault = SimpleNamespace(evidence_facets={facet.id: facet}, concepts={concept.id: concept}, learning_objects={},
                        practice_items={})
nothing = lambda *args, **kwargs: []
repository = SimpleNamespace(
    entity_source_links_for_revision=nothing, entity_source_links_for_sources=nothing,
    notation_mappings_for_entity=nothing, source_conflicts_for_entity=nothing, entity_source_links=nothing,
)
inventory = {"inventory": {
    "concept_mentions": [{"name": "symmetric matrix", "aliases": ["symmetric matrices"]}],
    "claims": [{"statement": "Every symmetric matrix is diagonalizable.",
                "prerequisite_hints": ["symmetric transpose", "matrix transpose"]}],
}}
neighborhood = select_neighborhood(vault, repository, [inventory], budget_tokens=24000,
                                   source_ids=["src_alt"], revision_ids=["rev_alt"])
print(json.dumps({"record": neighborhood.as_manifest_record(), "context": neighborhood.as_context()},
                 sort_keys=True))
"""

#: Enough seeds that, with names tried in set order, at least two of them try a different name first.
_SEEDS = ("0", "1", "2", "3", "4", "5", "6", "7")


def _select_under(seed: str) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    completed = subprocess.run(
        [sys.executable, "-c", _SELECT], env=env, capture_output=True, text=True, check=True,
        cwd=Path(__file__).resolve().parents[1], timeout=120,
    )
    return json.loads(completed.stdout)


def test_the_neighbourhood_record_is_the_same_under_every_hash_seed():
    selections = {seed: _select_under(seed) for seed in _SEEDS}
    first = selections[_SEEDS[0]]
    # The case is the one that moved: both names and two hints matched, so a reason had to pick one.
    reasons = first["record"]["match_reasons"]
    assert {reason["kind"] for reasons_of in reasons.values() for reason in reasons_of} >= {
        "concept_name", "prerequisite_hint"}
    for seed, selection in selections.items():
        assert selection == first, f"PYTHONHASHSEED={seed} recorded another neighbourhood"


def test_a_reason_names_the_first_matching_name_in_sorted_order():
    # Under these two seeds set order tried another name (2) and another hint (3) first.
    for seed in ("2", "3"):
        _assert_sorted_reasons(_select_under(seed)["record"]["match_reasons"])


def _assert_sorted_reasons(reasons: dict) -> None:
    assert [reason["detail"] for reason in reasons["facet:fct_symmetric"] if reason["kind"] != "fingerprint"] == [
        "mentions 'symmetric matrices'", "cited prerequisite 'matrix transpose'"]
    assert [reason["detail"] for reason in reasons["concept:symmetric_matrix"]] == [
        "matches concept 'symmetric matrices'"]
