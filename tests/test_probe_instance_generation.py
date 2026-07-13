"""Parameterized instance generation from family/card bindings (spec §10)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_episodes import eligible_instruments, enter_episode
from learnloop.services.probe_families import builtin_family_templates
from learnloop.services.probe_instance_generation import (
    GENERATOR_ID,
    GENERATOR_VERSION,
    approve_probe_instance,
    generate_instances_for_episode,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path, *, trust_families: bool, with_confusable: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if with_confusable:
        loaded = load_vault(vault_root)
        payload = loaded.learning_objects[LO_ID].model_dump()
        payload["confusables"] = ["eigendecomposition"]
        upsert_learning_object(vault_root, payload, clock=CLOCK)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    if trust_families:
        for template in builtin_family_templates():
            repository.upsert_probe_family_template(
                family_id=template.id,
                version=template.version,
                status="trusted",
                template=template.as_dict(),
                schema_hash=template.schema_hash(),
                clock=CLOCK,
            )
    # Remove the authored item so the episode parks in pending_items.
    for item_path in (vault_root / "linear-algebra" / "practice-items").glob("*.yaml"):
        item_path.unlink()
    loaded = load_vault(vault_root)
    sync_vault_state(loaded, repository, clock=CLOCK)
    return vault_root, loaded, repository


def test_trusted_family_generation_unparks_episode_with_provenance(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path, trust_families=True)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    assert episode.status == "pending_items"

    summary = generate_instances_for_episode(repository, loaded, episode.id, clock=CLOCK, seed=7)
    assert summary.generated, "trusted families should generate instances"
    assert summary.episode_unparked
    assert summary.resolved_need_ids
    families = {instance.family_template_id for instance in summary.generated}
    # §9.5: one direct/minimal family plus shifted families.
    assert "minimal_recall" in families
    assert families & {"contrast_confusable", "perturbation", "minimal_counterexample"}

    for instance in summary.generated:
        links = repository.probe_item_family_links(instance.practice_item_id)
        assert len(links) == 1
        link = links[0]
        assert link.generator_id == GENERATOR_ID
        assert link.generator_version == GENERATOR_VERSION
        assert link.generation_seed == "7"
        assert link.instance_metadata["review_status"] == "auto_admitted_provisional"

    refreshed_vault = load_vault(vault_root)
    refreshed = repository.probe_episode(episode.id)
    assert refreshed.status == "in_progress"
    assert eligible_instruments(refreshed_vault, repository, refreshed)


def test_provisional_family_instances_park_behind_review(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path, trust_families=False)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)

    summary = generate_instances_for_episode(repository, loaded, episode.id, clock=CLOCK, seed=7)
    assert summary.generated
    assert not summary.episode_unparked
    assert all(instance.review_status == "pending_review" for instance in summary.generated)

    # Instances are written but inactive; a routine sync must not reactivate them.
    refreshed_vault = load_vault(vault_root)
    sync_vault_state(refreshed_vault, repository, clock=CLOCK)
    states = repository.practice_item_states()
    for instance in summary.generated:
        assert not states[instance.practice_item_id].active
    assert repository.probe_episode(episode.id).status == "pending_items"

    # Reviewer approval activates the instance and unparks the episode.
    first = summary.generated[0]
    assert approve_probe_instance(repository, refreshed_vault, first.practice_item_id, clock=CLOCK)
    assert repository.practice_item_states()[first.practice_item_id].active
    assert repository.probe_episode(episode.id).status == "in_progress"


def test_generation_is_idempotent(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path, trust_families=True)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    first = generate_instances_for_episode(repository, loaded, episode.id, clock=CLOCK, seed=7)
    assert first.generated

    refreshed_vault = load_vault(vault_root)
    second = generate_instances_for_episode(repository, refreshed_vault, episode.id, clock=CLOCK, seed=7)
    # The episode already unparked; regeneration produces nothing new.
    assert not second.generated
