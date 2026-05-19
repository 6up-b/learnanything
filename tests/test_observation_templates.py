from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.observations import (
    ObservationTemplateError,
    record_observation,
    register_observation_template,
    validate_template,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault


EMITTING_TEMPLATE = """
schema_version: 1
fields:
  - id: answer
    type: text
  - id: confidence
    type: scale
emits:
  attempt_type: independent_attempt
  answer_field: answer
  criterion_points_field: criterion_points
  confidence_field: confidence
"""

NON_EMITTING_TEMPLATE = """
schema_version: 1
fields:
  - id: reflection
    type: text
"""


def test_valid_template_registers_and_loads(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    template_id = register_observation_template(
        repository,
        domain="linear-algebra",
        version="1",
        title="Free recall",
        template_yaml=NON_EMITTING_TEMPLATE,
        clock=FrozenClock(NOW),
    )

    stored = repository.fetch_observation_template(template_id)
    assert stored is not None
    assert stored["emits_attempt"] is False
    assert stored["active"] is True


def test_invalid_template_is_rejected():
    errors = validate_template({"fields": [], "emits": {"answer_field": "a"}})
    assert errors  # missing fields content and emits.attempt_type


def test_register_rejects_invalid_template(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    with pytest.raises(ObservationTemplateError):
        register_observation_template(
            repository,
            domain="linear-algebra",
            version="1",
            title="Broken",
            template_yaml="schema_version: 1\nemits:\n  answer_field: answer\n",
            clock=FrozenClock(NOW),
        )


def test_emitting_template_creates_attempt_through_attempt_service(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    template_id = register_observation_template(
        repository,
        domain="linear-algebra",
        version="2",
        title="Spoken recall",
        template_yaml=EMITTING_TEMPLATE,
        clock=FrozenClock(NOW),
    )
    loaded = load_vault(vault_root)

    result = record_observation(
        loaded,
        repository,
        template_id=template_id,
        response={"answer": "U, Sigma, V transpose", "criterion_points": {"correctness": 4}, "confidence": 5},
        related_practice_item_id="pi_svd_define_001",
        related_learning_object_id="lo_svd_definition",
        clock=FrozenClock(NOW),
    )

    assert result.binding_mode == "template_fixed"
    assert result.emitted_attempt_id is not None
    # The emitted attempt produced normal side effects through the attempt service.
    attempt = repository.fetch_practice_attempt(result.emitted_attempt_id)
    assert attempt is not None
    assert attempt["practice_item_id"] == "pi_svd_define_001"
    events = repository.observation_events()
    assert events[0]["emitted_attempt_id"] == result.emitted_attempt_id


def test_ambiguous_emitting_binding_lands_pending(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    template_id = register_observation_template(
        repository,
        domain="linear-algebra",
        version="2",
        title="Spoken recall",
        template_yaml=EMITTING_TEMPLATE,
        clock=FrozenClock(NOW),
    )
    loaded = load_vault(vault_root)

    result = record_observation(
        loaded,
        repository,
        template_id=template_id,
        response={"answer": "something"},
        clock=FrozenClock(NOW),
    )

    assert result.binding_mode == "pending"
    assert result.emitted_attempt_id is None
