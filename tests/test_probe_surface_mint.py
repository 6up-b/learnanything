"""Fresh single-use probe surfaces minted at selection time (owner Task C).

``mint_single_use_probe_surface`` is the full-item sibling of the ephemeral
``diagnostic_microprobe`` dialogue-turn mint: when a probe episode needs a
surface and a provider is routed, one never-before-seen ``diagnostic_probe``
item is minted from the episode's admitted family/card binding. Three
properties are pinned:

* it is served through the probe branch (episode unparks, the scheduler scores
  probe EIG on it);
* it inherits the single-use semantics automatically (its one administration
  deactivates it);
* it respects the freshness gate at mint — no shared surface family/group with
  anything the learner has ever been administered.
"""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from learnloop.clock import FrozenClock
from learnloop.diagnosis.ai_contracts import ProbeInstanceSurface, ProbeInstanceSurfaces
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.probe_episodes import (
    administered_surface_exclusions,
    eligible_instruments,
    enter_episode,
)
from learnloop.diagnosis.probe_families import builtin_family_templates
from learnloop.diagnosis.probe_instance_generation import (
    mint_single_use_probe_surface,
)
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object, upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


class FakeSurfacesClient(StructuredClientFake):
    """AI provider double exposing run_probe_instance_surfaces."""

    model = "fake-model-1"

    def __init__(self, *, surfaces=None):
        self._surfaces = surfaces
        self.calls: list[object] = []

    def run_probe_instance_surfaces(self, context):
        self.calls.append(context)
        if self._surfaces is not None:
            return ProbeInstanceSurfaces(surfaces=self._surfaces)
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


def _setup(tmp_path, *, keep_items: bool = False):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    payload = loaded.learning_objects[LO_ID].model_dump()
    payload["confusables"] = ["eigendecomposition"]
    upsert_learning_object(vault_root, payload, clock=CLOCK)
    repository = Repository(paths.sqlite_path)
    # Trusted families: the §10 trust policy auto-admits the mint so it can
    # serve immediately (a provisional family parks it behind review).
    for template in builtin_family_templates():
        repository.upsert_probe_family_template(
            family_id=template.id,
            version=template.version,
            status="trusted",
            template=template.as_dict(),
            schema_hash=template.schema_hash(),
            clock=CLOCK,
        )
    if not keep_items:
        for item_path in vault_root.rglob("practice-items/*.yaml"):
            item_path.unlink()
    loaded = load_vault(vault_root)
    sync_vault_state(loaded, repository, clock=CLOCK)
    return vault_root, loaded, repository


def _administer(vault, repository, item_id, *, attempt_id, attempt_type):
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type=attempt_type,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points={"correctness": 2.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=CLOCK,
    )


def test_minted_surface_serves_through_the_probe_branch_and_is_single_use(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)
    assert episode.status == "pending_items"

    minted = mint_single_use_probe_surface(
        repository, loaded, episode.id, ai_client=FakeSurfacesClient(), clock=CLOCK
    )

    assert minted is not None
    assert minted.review_status == "auto_admitted_provisional"

    vault = load_vault(vault_root)
    vault.config = loaded.config
    sync_vault_state(vault, repository, clock=CLOCK)
    item = vault.practice_items[minted.practice_item_id]
    # The single-use stamp: the mode carries every freshness rule downstream.
    assert item.practice_mode == "diagnostic_probe"
    assert "diagnostic_probe" in item.attempt_types_allowed

    # Provenance persists through the family link, microprobe-style.
    link = repository.probe_item_family_links(minted.practice_item_id)[0]
    assert link.instance_metadata["single_use_probe_mint"] is True
    assert link.instance_metadata["probe_episode_id"] == episode.id

    # The episode unparked and its queued generation needs resolved.
    refreshed = repository.probe_episode(episode.id)
    assert refreshed is not None and refreshed.status == "in_progress"
    assert repository.probe_generation_needs(
        probe_episode_id=episode.id, status="pending"
    ) == []

    # Probe-branch serving: the minted item is an eligible instrument and the
    # scheduler scores probe EIG on it (it is never ordinary practice).
    assert minted.practice_item_id in {
        entry.item.id
        for entry in eligible_instruments(vault, repository, refreshed)
    }
    queue = build_due_queue(vault, repository, clock=CLOCK, persist_explanations=False)
    scheduled = next(
        (entry for entry in queue if entry.practice_item_id == minted.practice_item_id),
        None,
    )
    assert scheduled is not None
    assert scheduled.components["probe_eig"] > 0.0

    # Single-use: its one administration deactivates it and it leaves the queue.
    _administer(
        vault,
        repository,
        minted.practice_item_id,
        attempt_id="att_minted_consume",
        attempt_type="diagnostic_probe",
    )
    state = repository.practice_item_state(minted.practice_item_id)
    assert state is not None and not state.active
    queue_after = build_due_queue(
        vault, repository, clock=CLOCK, persist_explanations=False
    )
    assert minted.practice_item_id not in {
        entry.practice_item_id for entry in queue_after
    }


def test_mint_refuses_a_surface_group_the_learner_has_seen(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path)
    # An administered ordinary item whose surface GROUP (via its shared-stimulus
    # fingerprint) collides with the first LLM surface the generator would mint.
    # Its own surface_family differs, so the duplicate-surface gate cannot catch
    # the collision — only the administered-group freshness check can.
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_seen_ordinary",
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Seen stimulus prompt.",
            "expected_answer": "V",
            "surface_family": "seen_ordinary_family",
            "evidence_fingerprint": {"shared_stimulus_id": "minimal_recall_llm_shared"},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct."}
                ],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )
    loaded = load_vault(vault_root)
    sync_vault_state(loaded, repository, clock=CLOCK)
    _administer(
        loaded,
        repository,
        "pi_seen_ordinary",
        attempt_id="att_seen_ordinary",
        attempt_type="independent_attempt",
    )
    episode = enter_episode(loaded, repository, LO_ID, trigger="manual", clock=CLOCK)

    client = FakeSurfacesClient(
        surfaces=[
            ProbeInstanceSurface(
                surface_suffix="shared",
                prompt_md=(
                    "Considering Singular Value Decomposition, what does recall "
                    "require here?"
                ),
                expected_answer_md="The decisive reason, shared surface.",
            ),
            ProbeInstanceSurface(
                surface_suffix="fresh",
                prompt_md=(
                    "Considering Singular Value Decomposition, what does recall "
                    "demand in a new setting?"
                ),
                expected_answer_md="The decisive reason, fresh surface.",
            ),
        ]
    )
    minted = mint_single_use_probe_surface(
        repository, loaded, episode.id, ai_client=client, clock=CLOCK
    )

    assert minted is not None
    assert minted.surface_family != "minimal_recall_llm_shared"

    vault = load_vault(vault_root)
    _attempted_ids, attempted_surfaces = administered_surface_exclusions(
        vault, repository
    )
    from learnloop.substrate.canonical_projection import surface_group_id

    minted_item = vault.practice_items[minted.practice_item_id]
    assert surface_group_id(minted_item) not in attempted_surfaces
