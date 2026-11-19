"""Parameterized instance generation from family/card bindings (spec §10)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import eligible_instruments, enter_episode
from learnloop.diagnosis.probe_families import builtin_family_templates
from learnloop.diagnosis.probe_instance_generation import (
    GENERATOR_ID,
    GENERATOR_VERSION,
    approve_probe_instance,
    generate_instances_for_episode,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, append_config_toml, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path, *, trust_families: bool, with_confusable: bool = True, predecessor: bool = False):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if predecessor:
        append_config_toml(vault_root, "[followup]\ngenerate_and_serve = false")
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
    # The predecessor's parametric instance generation. From mvp-0.45 (FG1 §4.3) the model writes
    # the family's question pattern with no parametric fallback; `followup.generate_and_serve` off
    # serves the predecessor exactly. Goes with that switch in D7.
    vault_root, loaded, repository = _setup(tmp_path, trust_families=True, predecessor=True)
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
    # The predecessor's parametric instance generation. From mvp-0.45 (FG1 §4.3) the model writes
    # the family's question pattern with no parametric fallback; `followup.generate_and_serve` off
    # serves the predecessor exactly. Goes with that switch in D7.
    vault_root, loaded, repository = _setup(tmp_path, trust_families=False, predecessor=True)
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
    # The predecessor's parametric instance generation. From mvp-0.45 (FG1 §4.3) the model writes
    # the family's question pattern with no parametric fallback; `followup.generate_and_serve` off
    # serves the predecessor exactly. Goes with that switch in D7.
    vault_root, loaded, repository = _setup(tmp_path, trust_families=True, predecessor=True)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    first = generate_instances_for_episode(repository, loaded, episode.id, clock=CLOCK, seed=7)
    assert first.generated

    refreshed_vault = load_vault(vault_root)
    second = generate_instances_for_episode(repository, refreshed_vault, episode.id, clock=CLOCK, seed=7)
    # The episode already unparked; regeneration produces nothing new.
    assert not second.generated


def test_approving_an_answered_probe_keeps_its_scheduling_state(tmp_path):
    """Approval activates a pending instance; it never rewrites the row. The generic upsert replaced the whole row on
    conflict, so approving an instance that had already been answered cleared its forgetting clock, memory and due
    date with no answer behind it, while a rebuild (which replays the attempt) restored them."""

    from datetime import timedelta

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    vault_root, loaded, repository = _setup(tmp_path, trust_families=False, predecessor=True)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    summary = generate_instances_for_episode(repository, loaded, episode.id, clock=CLOCK, seed=7)
    probe_item = summary.generated[0].practice_item_id
    refreshed_vault = load_vault(vault_root)
    rubric = refreshed_vault.rubric_for_item(refreshed_vault.practice_items[probe_item])
    complete_self_graded_attempt(
        refreshed_vault, repository, AttemptDraft(practice_item_id=probe_item, learner_answer_md="An answer.",
                                                  attempt_type="diagnostic_probe"),
        SelfGradeInput(criterion_points={criterion.id: criterion.points for criterion in rubric.criteria}, confidence=4),
        clock=CLOCK,
    )

    def scheduling(state):
        return (state.last_attempt_at, state.stability, state.difficulty, state.retrievability, state.due_at,
                state.content_hash)

    answered = repository.practice_item_states()[probe_item]
    assert answered.last_attempt_at is not None

    assert approve_probe_instance(repository, refreshed_vault, probe_item, clock=FrozenClock(NOW + timedelta(days=1)))
    approved = repository.practice_item_states()[probe_item]
    assert scheduling(approved) == scheduling(answered)
    assert approved.active

    rebuild_all_derived_state(refreshed_vault, repository, clock=FrozenClock(NOW + timedelta(days=2)))
    rebuilt = repository.practice_item_states()[probe_item]
    assert (scheduling(rebuilt)[:5], rebuilt.active) == (scheduling(approved)[:5], True)
