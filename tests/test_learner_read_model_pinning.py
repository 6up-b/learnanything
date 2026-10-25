"""Learner read models run on one pinned connection and return the same bytes.

The read models make dozens of small repository calls; pinning reuses one
connection for all of them instead of paying a connection open and schema parse
per call. Pinning must not change a result, so each model's serialized output is
compared with the undecorated function (``__wrapped__``) on a copy of the
linear-algebra fixture vault, which has canonical facet state and attempts.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

import learnloop.db.repositories as repositories_module
from learnloop.clock import FrozenClock
from learnloop.learner.capability_grid import capability_grid, lo_blueprint_readiness
from learnloop.learner.facet_diagnostics import mastery_diagnostic_view
from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines
from learnloop.learner.facet_state_reader import facet_recall_state_for_lo, is_canonical_state_vault
from learnloop.learner.learner_review_feed import build_learner_review_feed
from learnloop.learner.recall_coverage import predicted_correctness, predicted_correctness_from_prior
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from tests.owner_vaults import owner_vault, owner_vaults

# A backup-API copy in the owner_vaults lane since S0 (tests/owner_vaults.py).
FIXTURE_VAULT = owner_vault("linear_algebra")
FROZEN = FrozenClock(datetime.datetime(2026, 9, 1, tzinfo=datetime.timezone.utc))


def _serialized(value: Any) -> str:
    def plain(item: Any) -> Any:
        if dataclasses.is_dataclass(item) and not isinstance(item, type):
            return {field.name: plain(getattr(item, field.name)) for field in dataclasses.fields(item)}
        if isinstance(item, BaseModel):
            return item.model_dump(mode="json")
        if isinstance(item, dict):
            return {str(key): plain(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [plain(child) for child in item]
        if isinstance(item, (set, frozenset)):
            return [plain(child) for child in sorted(item, key=repr)]
        return item

    return json.dumps(plain(value), sort_keys=True, default=repr)


@pytest.fixture(scope="module")
def fixture_vault(tmp_path_factory):
    root = tmp_path_factory.mktemp("read_models") / "vault"
    shutil.copytree(FIXTURE_VAULT, root)
    vault = load_vault(root)
    repository = open_vault_repository(vault.root, VaultPaths(vault.root, vault.config).sqlite_path)
    assert is_canonical_state_vault(vault)
    return vault, repository


def _read_models(vault) -> dict[str, Any]:
    learning_objects = sorted(vault.learning_objects)
    facets = sorted(
        {vault.canonical_facet_id(facet) for item in vault.practice_items.values() for facet in item.evidence_facets}
    )
    return {
        "capability_grid": [(capability_grid, (lo,), {}) for lo in learning_objects],
        "lo_blueprint_readiness": [(lo_blueprint_readiness, (lo,), {}) for lo in learning_objects],
        "mastery_diagnostic_view": [(mastery_diagnostic_view, (lo,), {"clock": FROZEN}) for lo in learning_objects],
        "build_learner_review_feed": [(build_learner_review_feed, (), {})],
        "facet_evidence_timelines": [(facet_evidence_timelines, (facets,), {})],
    }


@owner_vaults
@pytest.mark.parametrize(
    "model_name",
    [
        "capability_grid",
        "lo_blueprint_readiness",
        "mastery_diagnostic_view",
        "build_learner_review_feed",
        "facet_evidence_timelines",
    ],
)
def test_pinned_read_model_output_is_byte_identical(fixture_vault, model_name) -> None:
    vault, repository = fixture_vault
    calls = _read_models(vault)[model_name]

    pinned = [_serialized(function(vault, repository, *args, **kwargs)) for function, args, kwargs in calls]
    unpinned = [
        _serialized(function.__wrapped__(vault, repository, *args, **kwargs)) for function, args, kwargs in calls
    ]

    assert pinned == unpinned
    assert any(output not in ("null", "{}", "[]") for output in pinned)


@owner_vaults
@pytest.mark.parametrize(
    "model_name",
    [
        "capability_grid",
        "lo_blueprint_readiness",
        "mastery_diagnostic_view",
        "build_learner_review_feed",
        "facet_evidence_timelines",
    ],
)
def test_read_model_opens_one_connection_per_call(fixture_vault, model_name, monkeypatch) -> None:
    vault, repository = fixture_vault
    function, args, kwargs = _read_models(vault)[model_name][0]
    opened: list[Path] = []
    real_connect = repositories_module.connect

    def counting_connect(*connect_args, **connect_kwargs):
        opened.append(connect_args[0])
        return real_connect(*connect_args, **connect_kwargs)

    monkeypatch.setattr(repositories_module, "connect", counting_connect)

    function(vault, repository, *args, **kwargs)

    assert len(opened) == 1


def _per_facet_prediction(vault, repository, item, mastery) -> tuple[float, dict[str, float]]:
    """The prediction with a separate facet-state reader per facet."""

    facet_states = {
        facet: facet_recall_state_for_lo(vault, repository, item.learning_object_id, facet)
        for facet in item.evidence_facets
    }
    return predicted_correctness_from_prior(
        facet_states,
        item,
        prior_mastery=mastery,
        item_a=1.0,
        item_b=0.0,
        config=vault.config,
    )


@owner_vaults
def test_predicted_correctness_with_one_shared_reader_is_byte_identical(fixture_vault, monkeypatch) -> None:
    vault, repository = fixture_vault
    compared = 0
    for item_id in sorted(vault.practice_items):
        item = vault.practice_items[item_id]
        mastery = repository.mastery_state(item.learning_object_id)
        if mastery is None:
            continue
        shared = predicted_correctness(
            repository,
            item,
            learning_object_id=item.learning_object_id,
            prior_mastery=mastery,
            item_a=1.0,
            item_b=0.0,
            config=vault.config,
            vault=vault,
        )
        assert _serialized(shared) == _serialized(_per_facet_prediction(vault, repository, item, mastery))
        compared += 1
    assert compared > 0

    item = next(item for item in vault.practice_items.values() if len(item.evidence_facets) > 1)
    mastery = repository.mastery_state(item.learning_object_id)
    opened: list[Path] = []
    real_connect = repositories_module.connect

    def counting_connect(*connect_args, **connect_kwargs):
        opened.append(connect_args[0])
        return real_connect(*connect_args, **connect_kwargs)

    monkeypatch.setattr(repositories_module, "connect", counting_connect)
    predicted_correctness(
        repository,
        item,
        learning_object_id=item.learning_object_id,
        prior_mastery=mastery,
        item_a=1.0,
        item_b=0.0,
        config=vault.config,
        vault=vault,
    )
    assert len(opened) == 1
