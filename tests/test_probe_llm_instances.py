"""LLM-backed instance surfaces and family-gate integration (spec §9.2/§9.4/§9.6)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.codex.client import CodexUnavailable
from learnloop.codex.schemas import (
    ProbeFamilyTrial,
    ProbeFamilyTrials,
    ProbeInstanceSurface,
    ProbeInstanceSurfaces,
)
from learnloop.db.repositories import Repository
from learnloop.services.probe_episodes import enter_episode
from learnloop.services.probe_families import (
    MINIMAL_RECALL_V1,
    builtin_family_templates,
    validate_and_compile_card,
)
from learnloop.services.probe_instance_generation import (
    GENERATOR_ID,
    LLM_GENERATOR_ID,
    LLM_GENERATOR_VERSION,
    ensure_instrument_card,
    generate_instances_for_episode,
    run_llm_family_gate,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


class FakeSurfacesClient:
    """AI provider double exposing run_probe_instance_surfaces."""

    model = "fake-model-1"

    def __init__(self, *, surfaces=None, error=False):
        self._surfaces = surfaces
        self._error = error
        self.calls: list[object] = []

    def run_probe_instance_surfaces(self, context):
        self.calls.append(context)
        if self._error:
            raise CodexUnavailable("provider down")
        if self._surfaces is not None:
            return ProbeInstanceSurfaces(surfaces=self._surfaces)
        # Grounded, leak-free surfaces derived from the bounded context.
        return ProbeInstanceSurfaces(
            surfaces=[
                ProbeInstanceSurface(
                    surface_suffix=f"fake_{index}",
                    prompt_md=(
                        f"Surface {index}: considering {context.learning_object_title}, "
                        f"what does {context.target_facets[0]} require here?"
                    ),
                    expected_answer_md=f"A robust learner states the decisive reason {index}.",
                )
                for index in range(context.count)
            ]
        )


def _setup(tmp_path, *, trust_families: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    payload = loaded.learning_objects[LO_ID].model_dump()
    payload["confusables"] = ["eigendecomposition"]
    upsert_learning_object(vault_root, payload, clock=CLOCK)
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
    for item_path in (vault_root / "linear-algebra" / "practice-items").glob("*.yaml"):
        item_path.unlink()
    loaded = load_vault(vault_root)
    sync_vault_state(loaded, repository, clock=CLOCK)
    return vault_root, loaded, repository


def test_llm_surfaces_generate_with_provenance(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    client = FakeSurfacesClient()

    summary = generate_instances_for_episode(
        repository, loaded, episode.id, clock=CLOCK, seed=3, ai_client=client
    )
    assert summary.generated
    assert client.calls, "the LLM surface generator should be consulted"
    llm_instances = [i for i in summary.generated if i.generator_id == LLM_GENERATOR_ID]
    assert llm_instances, "LLM surfaces should be preferred when the provider succeeds"
    for instance in llm_instances:
        assert "_llm_" in instance.surface_family
        link = repository.probe_item_family_links(instance.practice_item_id)[0]
        assert link.generator_id == LLM_GENERATOR_ID
        assert link.generator_version == LLM_GENERATOR_VERSION
        assert link.instance_metadata["generator_model"] == "fake-model-1"
        assert link.instance_metadata["prompt_version"]


def test_gate_rejected_llm_surfaces_fall_back_to_parametric(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    # Ungrounded prompts (no LO title/concept/facet mention) fail the
    # structural gate; leaky prompt equals its expected answer.
    client = FakeSurfacesClient(
        surfaces=[
            ProbeInstanceSurface(
                surface_suffix="ungrounded",
                prompt_md="What is the answer to this question?",
                expected_answer_md="Some answer.",
            ),
            ProbeInstanceSurface(
                surface_suffix="leaky",
                prompt_md="The decisive reason is X.",
                expected_answer_md="The decisive reason is X.",
            ),
        ]
    )

    summary = generate_instances_for_episode(
        repository, loaded, episode.id, clock=CLOCK, seed=3, ai_client=client
    )
    assert summary.generated, "parametric fallback should top up rejected LLM surfaces"
    assert all(instance.generator_id == GENERATOR_ID for instance in summary.generated)


def test_provider_failure_falls_back_to_parametric(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    client = FakeSurfacesClient(error=True)

    summary = generate_instances_for_episode(
        repository, loaded, episode.id, clock=CLOCK, seed=3, ai_client=client
    )
    assert summary.generated
    assert all(instance.generator_id == GENERATOR_ID for instance in summary.generated)


def test_llm_surfaces_config_disable(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    loaded.config.probe.generation.llm_surfaces = False
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    client = FakeSurfacesClient()

    summary = generate_instances_for_episode(
        repository, loaded, episode.id, clock=CLOCK, seed=3, ai_client=client
    )
    assert summary.generated
    assert not client.calls
    assert all(instance.generator_id == GENERATOR_ID for instance in summary.generated)


class FakeGateClient(FakeSurfacesClient):
    """Adds run_probe_family_trials; outcomes chosen per planted slot."""

    def __init__(self, outcome_for_slot):
        super().__init__()
        self._outcome_for_slot = outcome_for_slot

    def run_probe_family_trials(self, context):
        trials = []
        for slot in context.hypothesis_slots:
            for _ in range(context.trials_per_hypothesis):
                trials.append(
                    ProbeFamilyTrial(
                        hypothesis_slot=slot,
                        answer=f"simulated answer for {slot}",
                        matched_outcome=self._outcome_for_slot(slot),
                    )
                )
        return ProbeFamilyTrials(trials=trials)


def _slot_argmax_outcomes(loaded, repository):
    """The outcome each slot's compiled row most favors (reverse-match target)."""

    card, template = ensure_instrument_card(
        loaded, repository, LO_ID, MINIMAL_RECALL_V1, clock=CLOCK
    )
    instrument = validate_and_compile_card(card, template)
    return {
        slot: max(template.observation_alphabet, key=lambda outcome: instrument.rows[slot][outcome])
        for slot in card.hypotheses
    }


def test_llm_family_gate_accepts_and_records_synthetic_calibration(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    outcomes = _slot_argmax_outcomes(loaded, repository)
    client = FakeGateClient(lambda slot: outcomes[slot])

    gate = run_llm_family_gate(
        loaded, repository, LO_ID, MINIMAL_RECALL_V1, client, trials_per_hypothesis=3, clock=CLOCK
    )
    assert gate is not None
    assert gate.accepted, gate.reasons
    row = repository.probe_family_calibration(
        MINIMAL_RECALL_V1.id,
        MINIMAL_RECALL_V1.version,
        evidence_source="synthetic_gate",
        grader_version=MINIMAL_RECALL_V1.grader_policy,
    )
    assert row is not None
    assert row["parameter_posterior"]["accepted"] is True


def test_llm_family_gate_rejects_indistinct_signatures(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    # Every planted state produces the same outcome: declared signatures
    # cannot be reproduced, so reverse matching must reject the family.
    client = FakeGateClient(lambda slot: "correct_recall")

    gate = run_llm_family_gate(
        loaded, repository, LO_ID, MINIMAL_RECALL_V1, client, trials_per_hypothesis=3, clock=CLOCK
    )
    assert gate is not None
    assert not gate.accepted
    assert any("reverse matching" in reason for reason in gate.reasons)


def test_llm_family_gate_requires_capable_provider(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    client = FakeSurfacesClient()  # no run_probe_family_trials

    gate = run_llm_family_gate(
        loaded, repository, LO_ID, MINIMAL_RECALL_V1, client, clock=CLOCK
    )
    assert gate is None
