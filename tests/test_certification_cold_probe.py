"""Delayed cold probe per certified LO + `false_certification_rate`.

`spec_measurement_efficiency_v1.md` §5.7, plan item 4.2. The probe is the only
external validity check a single-learner vault has, and
`false_certification_rate` is "the alpha actually being run at" — so the tests
that matter are the ones pinning what the metric refuses to say: no probe before
the horizon, no second probe per certificate, no probe on a surface the
certifying evidence already used, no probe at all for a withdrawn certificate,
and no 0.0 over an empty denominator.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.certification_cold_probe import (
    COLD_PROBE_TASK_KIND,
    certification_cold_probe_report,
    cold_outcome_labels,
    current_certificate,
    false_certification_rate,
    resolve_cold_probe_parameters,
    schedule_certification_cold_probes,
    select_held_out_probe_item,
)
from learnloop.services.coldness_receipt import (
    record_certification_administration_snapshot,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    create_basic_vault,
    set_algorithm_version,
)

LO_ID = "lo_svd_definition"
CERTIFYING_ITEM = "pi_svd_define_001"
HELD_OUT_ITEM = "pi_svd_define_002"
# The basic vault's only item is `short_answer` on facet "recall", which compiles
# to capability `schema_interpretation` — so a one-component recipe at that cell
# is certifiable by a single full-marks independent attempt, and the certificate
# under test is a real one rather than a hand-written ledger row.
FACET = "recall"
CAPABILITY = "schema_interpretation"


def _blueprint(paths, *, components=None, integration=None):
    components = components or [(FACET, CAPABILITY, "hard")]
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    recipe = {
        "id": "r1",
        "composition": "conjunctive",
        "all_of": [
            {"facet": facet, "capability": capability, "modality": modality}
            for facet, capability, modality in components
        ],
    }
    if integration is not None:
        recipe["integration"] = {
            "facet": integration[0],
            "capability": integration[1],
            "modality": "hard",
        }
    data["blueprints"] = [{"id": "bp1", "weight": 1.0, "recipes": [recipe]}]
    write_yaml(lo_path, data)


def _vault(tmp_path, *, second_item=True, components=None, integration=None):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    _blueprint(paths, components=components, integration=integration)
    if second_item:
        add_followup_item(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _attempt(vault, repository, item_id, *, points=4, clock=None, primed=False, hints=0):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=hints,
            primed=primed,
        ),
        SelfGradeInput(
            criterion_points={"correctness": points}, fatal_errors=[], confidence=4
        ),
        clock=clock or FrozenClock(NOW),
    )


def _certify(tmp_path, **kwargs):
    """Vault whose one LO holds a real certificate from one unassisted attempt."""

    paths, vault, repository = _vault(tmp_path, **kwargs)
    _attempt(vault, repository, CERTIFYING_ITEM)
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None, "fixture must actually certify"
    return paths, vault, repository, certificate


def _tasks(repository):
    return repository.followup_tasks_of_kind(COLD_PROBE_TASK_KIND)


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------


def test_probe_is_due_at_the_horizon_and_invisible_before_it(tmp_path):
    _paths, vault, repository, certificate = _certify(tmp_path)

    report = schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    assert report.counts["scheduled"] == 1

    parameters = resolve_cold_probe_parameters(repository)
    horizon = timedelta(days=parameters.horizon_days)
    task = _tasks(repository)[0]
    opportunity_id = task["measurement_opportunity_id"]
    assert opportunity_id == report.decisions[0].measurement_opportunity_id
    opportunity = repository.cold_measurement_opportunity(opportunity_id)
    assert opportunity["certificate_id"] == certificate.certificate_id
    decision = repository.cold_measurement_opportunity_decision(opportunity_id)
    assert decision["decision"] == "scheduled"
    assert decision["followup_task_id"] == task["id"]
    assert task["case_ref"] == certificate.certificate_id
    assert task["not_before"] == (NOW + horizon).isoformat().replace("+00:00", "Z")
    # "+2-3 weeks" is an interval, not a point: the probe expires window_days
    # after it becomes due.
    assert task["expires_at"] == (
        NOW + horizon + timedelta(days=parameters.window_days)
    ).isoformat().replace("+00:00", "Z")

    # Scheduled today, invisible to the scheduler until the horizon.
    assert HELD_OUT_ITEM not in repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW)
    )
    assert HELD_OUT_ITEM not in repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW + horizon - timedelta(hours=1))
    )
    pending = repository.pending_followup_practice_items(
        clock=FrozenClock(NOW + horizon)
    )
    assert [row["practice_item_id"] for row in pending] == [HELD_OUT_ITEM]
    # The lane travels with the queued item: a certification probe must not reach
    # the scheduler labelled as a repair retry.
    assert pending[0]["action_type"] == COLD_PROBE_TASK_KIND


def test_certificate_id_and_selection_are_deterministic(tmp_path):
    """Idempotency rests on a stable certificate id and a stable choice.

    If either wobbled across reloads the unique index would let a second probe
    through on the next scheduler run, and the "one per certified LO" guarantee
    would hold only within a process.
    """

    paths, vault, repository, certificate = _certify(tmp_path)
    reloaded = load_vault(paths.root)
    again = current_certificate(reloaded, repository, reloaded.learning_objects[LO_ID])
    assert again is not None
    assert again.certificate_id == certificate.certificate_id

    first = select_held_out_probe_item(vault, repository, certificate).as_dict()
    second = select_held_out_probe_item(reloaded, repository, again).as_dict()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)

    report_a = certification_cold_probe_report(vault, repository)
    report_b = certification_cold_probe_report(reloaded, repository)
    assert json.dumps(report_a, sort_keys=True) == json.dumps(report_b, sort_keys=True)


def test_one_probe_per_certified_lo_idempotently(tmp_path):
    _paths, vault, repository, _certificate = _certify(tmp_path)

    first = schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    assert first.counts["scheduled"] == 1
    task_id = _tasks(repository)[0]["id"]

    for day in (0, 1, 30):
        again = schedule_certification_cold_probes(
            vault, repository, clock=FrozenClock(NOW + timedelta(days=day))
        )
        assert again.counts["scheduled"] == 0
        assert again.counts["already_scheduled"] == 1
    assert [task["id"] for task in _tasks(repository)] == [task_id]

    # More practice on an already-certified cell must not mint a new certificate
    # (the id hashes the requirements, not the evidence) and therefore must not
    # buy a second probe.
    _attempt(vault, repository, CERTIFYING_ITEM, clock=FrozenClock(NOW + timedelta(days=1)))
    after = schedule_certification_cold_probes(
        vault, repository, clock=FrozenClock(NOW + timedelta(days=1))
    )
    assert after.counts["scheduled"] == 0
    assert len(_tasks(repository)) == 1


def test_an_uncertified_lo_schedules_nothing(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    # No attempt: nothing is demonstrated, so there is no certificate to probe.
    report = schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    assert report.counts == {**report.counts, "scheduled": 0, "not_certified": 1}
    assert _tasks(repository) == []


# ---------------------------------------------------------------------------
# Held-out surface
# ---------------------------------------------------------------------------


def test_selected_surface_is_never_one_the_certificate_used(tmp_path):
    _paths, vault, repository, certificate = _certify(tmp_path)

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id == HELD_OUT_ITEM
    assert selection.basis == "distinct_surface_group"
    # The exclusion set is the ledger's own `independent_surface_groups` for the
    # certified cells — the existing EvidenceFingerprint vocabulary, not a second
    # notion of surface identity.
    assert selection.excluded_surface_groups == ("item:pi_svd_define_001",)
    assert selection.surface_group not in selection.excluded_surface_groups
    assert CERTIFYING_ITEM in selection.rejected_as_used_surface

    task = schedule_certification_cold_probes(
        vault, repository, clock=FrozenClock(NOW)
    ).decisions[0]
    assert task.practice_item_id != CERTIFYING_ITEM


def test_shared_surface_group_makes_the_certificate_unmeasurable(tmp_path):
    """A clone of the certifying item is not a held-out surface.

    Both items declare the same `shared_stimulus_id`, so `surface_group_id`
    collapses them into one group — the same collapse that stops a clone minting
    a fresh independent surface group for certification. There is then no
    held-out instrument, and that is reported as UNMEASURABLE rather than
    quietly probed on the used surface.
    """

    paths, _vault_before, repository = _vault(tmp_path, second_item=False)
    template = read_yaml(paths.practice_item_path("linear-algebra", CERTIFYING_ITEM))
    for item_id in (CERTIFYING_ITEM, HELD_OUT_ITEM):
        upsert_practice_item(
            paths.root,
            dict(template)
            | {
                "id": item_id,
                "evidence_fingerprint": {"shared_stimulus_id": "stim_svd"},
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
            clock=FrozenClock(NOW),
        )
    vault = load_vault(paths.root)
    _attempt(vault, repository, CERTIFYING_ITEM)
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None
    assert certificate.used_surface_groups() == ("stim_svd",)

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id is None
    assert selection.decision == "no_held_out_surface"
    assert selection.basis == "shared_surface_group"

    report = schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    assert report.counts["no_held_out_surface"] == 1
    assert _tasks(repository) == []
    opportunity_id = report.decisions[-1].measurement_opportunity_id
    decision = repository.cold_measurement_opportunity_decision(opportunity_id)
    assert (decision["decision"], decision["reason"]) == (
        "structurally_refused",
        "no_held_out_surface",
    )
    refusal = repository.coldness_receipt_for_opportunity_stage(
        opportunity_id, "final"
    )
    assert refusal["lane"] == "certification_cold_probe"
    assert refusal["derived"]["outcome"] == "schedule_refused"
    # And the number that bounds the metric says so, so a rate over an
    # unmeasurable vault does not read as clean.
    coverage = certification_cold_probe_report(vault, repository)["coverage"]
    assert coverage == {
        "certificates_active": 1,
        "certificates_unmeasurable": 1,
        "certificates_unscheduled": 1,
    }


def test_the_only_instrument_being_the_certifying_one_is_unmeasurable(tmp_path):
    _paths, vault, repository, certificate = _certify(tmp_path, second_item=False)

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id is None
    # The single instrument on the cell is the one that certified, so its surface
    # is already used: unmeasurable, not merely unscheduled.
    assert selection.decision == "no_held_out_surface"
    assert selection.rejected_as_used_surface == (CERTIFYING_ITEM,)


def test_new_inventory_creates_a_fresh_opportunity_after_structural_refusal(
    tmp_path,
):
    paths, vault, repository, _certificate = _certify(
        tmp_path, second_item=False
    )
    first = schedule_certification_cold_probes(
        vault, repository, clock=FrozenClock(NOW)
    ).decisions[0]
    assert first.decision == "no_held_out_surface"

    # A refusal settles one inventory snapshot; it must not permanently block a
    # later measurement after a genuinely new held-out instrument is authored.
    add_followup_item(paths.root)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    second = schedule_certification_cold_probes(
        vault,
        repository,
        clock=FrozenClock(NOW + timedelta(hours=1)),
    ).decisions[0]

    assert second.decision == "scheduled"
    assert second.measurement_opportunity_id != first.measurement_opportunity_id
    assert repository.cold_measurement_opportunity_decision(
        first.measurement_opportunity_id
    )["decision"] == "structurally_refused"
    assert repository.cold_measurement_opportunity_decision(
        second.measurement_opportunity_id
    )["decision"] == "scheduled"


def _add_diagnostic_cell_item(root, item_id="pi_diag_cert_probe"):
    """A diagnostic_probe item that observes the certified cell.

    The explicit ``capability`` annotation outranks the practice-mode default
    (capability_mapping), so the item lands in the instrument pool for
    (recall, schema_interpretation) despite its diagnostic mode."""

    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "capability": CAPABILITY,
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": [FACET],
            "evidence_weights": {FACET: 1.0},
            "prompt": "Fresh diagnostic surface probing the certified cell.",
            "expected_answer": "U Sigma V transpose.",
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
        clock=FrozenClock(NOW),
    )


def test_selection_never_picks_an_administered_diagnostic_surface(tmp_path):
    """Single-use freshness at task-creation time (owner Task B).

    A ``diagnostic_probe`` surface that already carried its one administration
    must not be selected by the certification probe — the follow-up serving
    door would refuse the task — even in the legacy state shape where the row
    predates deactivate-on-attempt (active=True, last_attempt_at set). The
    ranking falls back to the next held-out ordinary item, and the refusal is
    recorded in its own bucket rather than dropped."""

    paths, vault, repository, _certificate = _certify(tmp_path)
    _add_diagnostic_cell_item(paths.root)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    repository.upsert_practice_item_state(
        "pi_diag_cert_probe", active=True, last_attempt_at=NOW_ISO
    )
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None

    selection = select_held_out_probe_item(vault, repository, certificate)

    assert selection.practice_item_id == HELD_OUT_ITEM
    assert selection.rejected_as_administered_diagnostic == ("pi_diag_cert_probe",)


def test_only_administered_diagnostic_candidates_means_no_held_out_surface(tmp_path):
    """Fallback rule: never create a task the scheduler will refuse.

    When the only held-out candidates are burned diagnostic surfaces, the
    scheduler declines to create the probe task (typed decision, not silence)."""

    paths, vault, repository, _certificate = _certify(tmp_path, second_item=False)
    _add_diagnostic_cell_item(paths.root)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    repository.upsert_practice_item_state(
        "pi_diag_cert_probe", active=True, last_attempt_at=NOW_ISO
    )
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id is None
    assert selection.decision == "no_held_out_surface"
    assert selection.rejected_as_administered_diagnostic == ("pi_diag_cert_probe",)

    report = schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    assert _tasks(repository) == []
    assert report.counts["no_held_out_surface"] == 1


def test_a_fresh_diagnostic_surface_remains_selectable_for_the_probe(tmp_path):
    """Control: freshness is the rule, not the mode — a never-administered
    diagnostic surface is a legitimate held-out probe instrument."""

    paths, vault, repository, _certificate = _certify(tmp_path, second_item=False)
    _add_diagnostic_cell_item(paths.root)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id == "pi_diag_cert_probe"
    assert selection.rejected_as_administered_diagnostic == ()


def test_no_active_instrument_at_all_reports_no_candidate(tmp_path):
    """The other arm: retiring the instrument leaves nothing to reject.

    Distinct from `no_held_out_surface` because the remedy is different — one
    needs a *varied* item authored, the other needs any item at all.
    """

    _paths, vault, repository, certificate = _certify(tmp_path, second_item=False)
    repository.upsert_practice_item_state(CERTIFYING_ITEM, active=False)

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id is None
    assert selection.decision == "no_candidate_item"
    assert selection.rejected_as_used_surface == ()
    assert selection.basis == "unknown"


def test_probe_prefers_the_whole_task_item_that_covers_integration(tmp_path):
    """§5.8.3's revert criterion is stated on whole-task items specifically.

    "certified LOs failing the §5.7 delayed cold probe on whole-task items
    specifically. That is the invariant integration exists to protect." So when
    the certificate carries an integration claim, the probe tests it in
    preference to a component-only item — integration is the coordination claim
    and §5.3 forbids satisfying it by inference, which makes it the part of a
    certificate most likely to be false.
    """

    paths, _vault_before, repository = _vault(
        tmp_path, second_item=False, integration=("assembly", CAPABILITY)
    )
    template = read_yaml(paths.practice_item_path("linear-algebra", CERTIFYING_ITEM))
    # One certifying item per cell (a single item split across both facets splits
    # its credit and certifies neither), then two held-out candidates:
    # `pi_whole_task` observes the integration facet, `pi_component_only` does not.
    for item_id, facets in (
        (CERTIFYING_ITEM, [FACET]),
        ("pi_cert_integration", ["assembly"]),
        ("pi_whole_task", [FACET, "assembly"]),
        ("pi_component_only", [FACET]),
    ):
        upsert_practice_item(
            paths.root,
            dict(template)
            | {
                "id": item_id,
                "evidence_facets": facets,
                "evidence_weights": {facet: 1.0 for facet in facets},
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
            clock=FrozenClock(NOW),
        )
    vault = load_vault(paths.root)
    _attempt(vault, repository, CERTIFYING_ITEM)
    _attempt(vault, repository, "pi_cert_integration")
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None
    assert certificate.integration_cell is not None
    assert certificate.integration_cell.facet_id == "assembly"

    selection = select_held_out_probe_item(vault, repository, certificate)
    assert selection.practice_item_id == "pi_whole_task"
    assert selection.covers_integration is True
    # The affordance the certifying evidence had and a whole-task probe does not.
    task = schedule_certification_cold_probes(
        vault, repository, clock=FrozenClock(NOW)
    ).decisions[0]
    context = repository.followup_task(task.followup_task_id)["context"]
    assert "component_only_evidence" in context["avoided_affordances"]


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------


def test_withdrawn_certificate_schedules_nothing_and_cancels_a_queued_probe(tmp_path):
    paths, vault, repository, certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    task_id = _tasks(repository)[0]["id"]

    # Withdraw it the way §5.3 says a certificate is withdrawn: the contract now
    # requires a cell the ledger does not demonstrate.
    _blueprint(paths, components=[(FACET, "coordination", "hard")])
    vault = load_vault(paths.root)
    assert current_certificate(vault, repository, vault.learning_objects[LO_ID]) is None

    report = schedule_certification_cold_probes(
        vault, repository, clock=FrozenClock(NOW + timedelta(days=1))
    )
    assert report.counts["scheduled"] == 0
    assert report.counts["withdrawn_probe_cancelled"] == 1
    # The queued probe is retired rather than left to fire: measuring a claim the
    # system has already retracted would put a `failed` row in the numerator of a
    # metric about FALSE certification.
    assert repository.followup_task(task_id)["status"] == "expired"
    assert repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW + timedelta(days=30))
    ) == []
    assert certificate.certificate_id not in {
        row["certificate_id"] for row in repository.certification_cold_probe_outcomes()
    }


def test_a_superseded_certificate_has_its_probe_cancelled_and_a_fresh_one_queued(tmp_path):
    """A changed recipe is a different certificate, so the old probe is retired.

    Left queued it would fire against a superseded id, land in the abstention arm
    and burn the one held-out item the certificate had — the metric would lose a
    measurement rather than gain one.
    """

    paths, vault, repository, first = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    stale_task_id = _tasks(repository)[0]["id"]

    # Same cell, different recipe id: still certified, but not the same certificate.
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    data["blueprints"][0]["recipes"][0]["id"] = "r2"
    write_yaml(lo_path, data)
    vault = load_vault(paths.root)
    second = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert second is not None
    assert second.certificate_id != first.certificate_id

    report = schedule_certification_cold_probes(
        vault, repository, clock=FrozenClock(NOW + timedelta(days=1))
    )
    assert report.counts["withdrawn_probe_cancelled"] == 1
    assert report.counts["scheduled"] == 1
    assert repository.followup_task(stale_task_id)["status"] == "expired"
    open_tasks = repository.open_followup_tasks_of_kind(COLD_PROBE_TASK_KIND)
    assert [task["case_ref"] for task in open_tasks] == [second.certificate_id]


def test_probe_against_a_withdrawn_certificate_abstains_rather_than_failing(tmp_path):
    paths, vault, repository, _certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    parameters = resolve_cold_probe_parameters(repository)
    due = FrozenClock(NOW + timedelta(days=parameters.horizon_days))

    # Withdraw the certificate but leave the probe queued (no scheduler run to
    # cancel it), then let the learner take it and fail.
    _blueprint(paths, components=[(FACET, "coordination", "hard")])
    vault = load_vault(paths.root)
    result = _attempt(vault, repository, HELD_OUT_ITEM, points=0, clock=due)

    outcome = repository.certification_cold_probe_outcome_for_attempt(result.attempt_id)
    assert outcome["verdict"] == "indeterminate"
    assert outcome["indeterminate_reason"] == "certificate_withdrawn"
    assert outcome["success"] is None
    assert outcome["certificate_state_at_probe"] == "withdrawn"
    # ...and it stays out of the denominator entirely.
    metric = false_certification_rate(repository)
    assert (metric.rate, metric.denominator, metric.indeterminate) == (None, 0, 1)


# ---------------------------------------------------------------------------
# Outcome labels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("points", "verdict", "success", "correctness"),
    [(4, "held", True, 1.0), (0, "failed", False, 0.0)],
)
def test_probe_records_a_durable_versioned_label(
    tmp_path, points, verdict, success, correctness
):
    _paths, vault, repository, certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    task = _tasks(repository)[0]
    parameters = resolve_cold_probe_parameters(repository)
    due = FrozenClock(NOW + timedelta(days=parameters.horizon_days))
    administration = record_certification_administration_snapshot(
        vault, repository, task=task, clock=due
    )
    assert administration is not None
    assert administration["lane"] == "certification_cold_probe"

    result = _attempt(vault, repository, HELD_OUT_ITEM, points=points, clock=due)
    outcome = repository.certification_cold_probe_outcome_for_attempt(result.attempt_id)

    assert outcome["verdict"] == verdict
    assert outcome["success"] is success
    assert outcome["correctness"] == correctness
    assert outcome["indeterminate_reason"] is None
    assert outcome["certificate_state_at_probe"] == "active"
    assert outcome["assisted"] is False
    assert outcome["held_out_basis"] == "distinct_surface_group"

    # Which certificate, which recipe, which cells, which surfaces were used:
    # the §5.3 receipt travels on the row so it still means something after the
    # ledger moves (and `substitutions` is present-and-empty, not absent).
    assert outcome["certificate_id"] == certificate.certificate_id
    assert (outcome["blueprint_id"], outcome["recipe_id"]) == ("bp1", "r1")
    receipt = outcome["certificate_receipt"]
    assert receipt["substitutions"] == []
    assert [cell["facet_id"] for cell in receipt["cells"]] == [FACET]
    assert receipt["cells"][0]["basis"] == "direct"
    assert outcome["excluded_surface_groups"] == ["item:pi_svd_define_001"]
    assert outcome["probe_surface_group"] == "item:pi_svd_define_002"
    assert outcome["probe_surface_group"] not in outcome["excluded_surface_groups"]

    # Version stamps (the `diagnosis_adjudications` pattern): store, policy,
    # parameters, grader.
    assert outcome["store_version"] == "certification_cold_probe_v1"
    assert outcome["policy_version"] == "certification_cold_probe_policy_v1"
    assert outcome["parameters"]["scope"] == "certification_cold_probe"
    assert outcome["parameters"]["lifecycle"] == "heuristic_default"
    assert outcome["horizon_days"] == parameters.horizon_days
    assert outcome["success_threshold"] == parameters.success_correctness
    assert outcome["grading_source"] == "self"
    assert outcome["grader_model"] is None

    # Consumed exactly once, through the shared follow-up lifecycle.
    consumed = repository.followup_task(task["id"])
    assert consumed["status"] == "consumed"
    assert consumed["consumed_attempt_id"] == result.attempt_id
    final = repository.coldness_receipt_for_task_stage(task["id"], "final")
    assert final is not None
    assert final["lane"] == "certification_cold_probe"
    assert final["measurement_opportunity_id"] == task["measurement_opportunity_id"]
    assert final["cold_attempt_id"] == result.attempt_id
    assert final["derived"]["outcome"] == verdict
    assert final["derived"]["qualifies_as_certificate_validation"] is True
    assert final["derived"]["qualifies_as_repair_effect_verification"] is None
    assert final["derived"]["administration_receipt_id"] == administration["id"]

    # A second attempt on the same item finds no active task and appends nothing.
    later = _attempt(
        vault,
        repository,
        HELD_OUT_ITEM,
        points=points,
        clock=FrozenClock(NOW + timedelta(days=parameters.horizon_days + 1)),
    )
    assert repository.certification_cold_probe_outcome_for_attempt(later.attempt_id) is None
    assert len(repository.certification_cold_probe_outcomes()) == 1


def test_outcome_rows_are_append_only(tmp_path):
    _paths, vault, repository, _certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    parameters = resolve_cold_probe_parameters(repository)
    _attempt(
        vault,
        repository,
        HELD_OUT_ITEM,
        points=0,
        clock=FrozenClock(NOW + timedelta(days=parameters.horizon_days)),
    )
    row = repository.certification_cold_probe_outcomes()[0]

    import sqlite3

    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE certification_cold_probe_outcomes SET verdict = 'held' WHERE id = ?",
                (row["id"],),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM certification_cold_probe_outcomes WHERE id = ?", (row["id"],)
            )


def test_a_queued_probe_refuses_an_assisted_attempt(tmp_path):
    _paths, vault, repository, _certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    parameters = resolve_cold_probe_parameters(repository)
    due = FrozenClock(NOW + timedelta(days=parameters.horizon_days))

    # The shared attempt validator already refuses this: a primed or hinted
    # attempt cannot support the claim "unassisted, on a held-out surface".
    with pytest.raises(AttemptValidationError):
        _attempt(vault, repository, HELD_OUT_ITEM, clock=due, primed=True)
    assert repository.certification_cold_probe_outcomes() == []
    assert repository.followup_task(_tasks(repository)[0]["id"])["status"] in {
        "pending",
        "served",
    }


def test_cold_outcome_labels_expose_the_causal_p4_shape(tmp_path):
    _paths, vault, repository, certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    parameters = resolve_cold_probe_parameters(repository)
    result = _attempt(
        vault,
        repository,
        HELD_OUT_ITEM,
        points=0,
        clock=FrozenClock(NOW + timedelta(days=parameters.horizon_days)),
    )

    labels = cold_outcome_labels(repository)
    assert len(labels) == 1
    label = labels[0]
    # Same key names as `causal_cold_verifications`, so P4 can union the channels.
    assert label["cold_attempt_id"] == result.attempt_id
    assert label["cold_surface_family"] == "item:pi_svd_define_002"
    assert label["source_surface_families"] == ["item:pi_svd_define_001"]
    assert label["success"] is False
    assert label["claim_kind"] == "lo_certificate"
    assert label["claim_ref"] == certificate.certificate_id
    # The probe avoided the CERTIFYING surfaces, not its own.
    assert "surface_family:item:pi_svd_define_001" in label["avoided_affordances"]
    assert "surface_family:item:pi_svd_define_002" not in label["avoided_affordances"]


def test_abstained_probes_are_not_training_labels(tmp_path):
    paths, vault, repository, _certificate = _certify(tmp_path)
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    parameters = resolve_cold_probe_parameters(repository)
    _blueprint(paths, components=[(FACET, "coordination", "hard")])
    vault = load_vault(paths.root)
    _attempt(
        vault,
        repository,
        HELD_OUT_ITEM,
        points=4,
        clock=FrozenClock(NOW + timedelta(days=parameters.horizon_days)),
    )

    assert len(repository.certification_cold_probe_outcomes()) == 1
    # An uninterpretable probe carries no label: a training set that treats "not
    # interpretable" as an outcome is worse than a smaller one.
    assert cold_outcome_labels(repository) == []


# ---------------------------------------------------------------------------
# `false_certification_rate`
# ---------------------------------------------------------------------------


def test_rate_over_zero_probes_is_unavailable_not_zero(tmp_path):
    _paths, vault, repository, _certificate = _certify(tmp_path)

    metric = false_certification_rate(repository)
    assert metric.rate is None
    assert metric.available is False
    assert metric.denominator == 0
    assert metric.unavailable_reason == "no_scored_cold_probe"
    payload = metric.as_dict()
    # The scoreboard entry must be readable by a consumer that only looks at
    # `value`: None, never 0.0. "No certificate has ever been false" and "no
    # certificate has ever been checked" are different claims (§5.7).
    assert payload["value"] is None
    assert payload["status"] == "unavailable"
    assert payload["denominator"] == 0
    assert payload["metric"] == "false_certification_rate"
    # Dict-coercible for the B5 scoreboard seam, unavailable arm included: a
    # composer reading numerator/denominator gets 0/0, never 0.0-as-a-rate.
    assert dict(metric)["value"] is None
    assert (dict(metric)["numerator"], dict(metric)["denominator"]) == (0, 0)

    # Still unavailable once a probe is merely SCHEDULED: an unprobed certificate
    # never counts as a pass.
    schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    scheduled = false_certification_rate(repository, clock=FrozenClock(NOW))
    assert scheduled.rate is None
    assert scheduled.awaiting_probe == 1
    assert scheduled.held == 0

    # ...and still unavailable once the window closes unprobed, in its own arm.
    # Counted against the clock rather than the lazily-flipped task status, so an
    # abandoned probe lane cannot read as "still awaiting" forever.
    parameters = resolve_cold_probe_parameters(repository)
    after_window = FrozenClock(
        NOW + timedelta(days=parameters.horizon_days + parameters.window_days + 1)
    )
    expired = false_certification_rate(repository, clock=after_window)
    assert expired.rate is None
    assert (expired.awaiting_probe, expired.probe_expired) == (0, 1)
    assert repository.followup_task(_tasks(repository)[0]["id"])["status"] == "pending"


def test_rate_is_correct_over_a_mix_of_held_and_failed_certificates(tmp_path):
    """Three certified LOs: one probe holds, one fails, one abstains.

    The rate is failed / (held + failed) = 1/2, and the abstention is visible but
    excluded — if it were folded into the denominator the rate would read 1/3 and
    understate the alpha actually being run at.
    """

    paths, vault, repository = _vault(tmp_path)
    for index in (1, 2, 3):
        _add_lo(paths, index)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for index in (1, 2, 3):
        _attempt(vault, repository, f"pi_extra_{index}_a")

    report = schedule_certification_cold_probes(vault, repository, clock=FrozenClock(NOW))
    assert report.counts["scheduled"] == 3

    parameters = resolve_cold_probe_parameters(repository)
    due = FrozenClock(NOW + timedelta(days=parameters.horizon_days))
    _attempt(vault, repository, "pi_extra_1_b", points=4, clock=due)  # held
    _attempt(vault, repository, "pi_extra_2_b", points=0, clock=due)  # failed
    # LO 3's certificate is withdrawn before its probe lands -> indeterminate.
    _write_lo(paths, 3, capability="coordination")
    vault = load_vault(paths.root)
    _attempt(vault, repository, "pi_extra_3_b", points=0, clock=due)

    metric = false_certification_rate(repository)
    assert (metric.held, metric.failed, metric.indeterminate) == (1, 1, 1)
    assert metric.denominator == 2
    assert metric.numerator == 1
    assert metric.rate == pytest.approx(0.5)
    assert metric.available is True
    assert metric.indeterminate_reasons == {"certificate_withdrawn": 1}
    payload = metric.as_dict()
    assert payload["value"] == pytest.approx(0.5)
    assert payload["denominator_definition"].startswith("certificates with a scored")
    assert payload["by_horizon_days"]["14"]["rate"] == pytest.approx(0.5)
    # The §3 B5 scoreboard COMPOSES this producer rather than reimplementing it,
    # and its contract is "a mapping carrying numerator/denominator". So the
    # result must survive dict() intact, including the unavailable arm.
    assert dict(metric) == payload
    assert dict(metric)["numerator"] == 1
    assert dict(metric)["denominator"] == 2


def _write_lo(paths, index, *, capability=CAPABILITY):
    lo_id = f"lo_extra_{index}"
    write_yaml(
        paths.learning_object_path("linear-algebra", lo_id),
        {
            "schema_version": 1,
            "id": lo_id,
            "title": f"Extra {index}",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "Extra learning object for the probe fixture.",
            "prerequisites": [],
            "confusables": [],
            "blueprints": [
                {
                    "id": "bp1",
                    "weight": 1.0,
                    "recipes": [
                        {
                            "id": "r1",
                            "composition": "conjunctive",
                            "all_of": [
                                {
                                    "facet": f"facet_extra_{index}",
                                    "capability": capability,
                                    "modality": "hard",
                                }
                            ],
                        }
                    ],
                }
            ],
            "difficulty_prior": 0.5,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _add_lo(paths, index):
    """One extra LO with two same-cell items on distinct surface groups."""

    _write_lo(paths, index)
    for suffix in ("a", "b"):
        upsert_practice_item(
            paths.root,
            {
                "id": f"pi_extra_{index}_{suffix}",
                "learning_object_id": f"lo_extra_{index}",
                "subjects": None,
                "practice_mode": "short_answer",
                "attempt_types_allowed": ["independent_attempt"],
                "evidence_facets": [f"facet_extra_{index}"],
                "evidence_weights": {f"facet_extra_{index}": 1.0},
                "prompt": f"Extra {index}{suffix}?",
                "expected_answer": "Yes.",
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
            clock=FrozenClock(NOW),
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_schedules_and_reports_the_unavailable_arm(tmp_path):
    paths, vault, repository, _certificate = _certify(tmp_path)
    runner = CliRunner()

    scheduled = runner.invoke(
        app, ["cold-probe-schedule", "--vault", str(paths.root)]
    )
    assert scheduled.exit_code == 0, scheduled.output
    assert "1 scheduled" in scheduled.output
    assert len(_tasks(repository)) == 1

    audit = runner.invoke(app, ["cold-probe-audit", "--vault", str(paths.root)])
    assert audit.exit_code == 0, audit.output
    assert "false_certification_rate: UNAVAILABLE" in audit.output
    assert "no_scored_cold_probe" in audit.output
    # Never a bare 0.000 over an empty denominator.
    assert "false_certification_rate: 0.000" not in audit.output

    parameters = resolve_cold_probe_parameters(repository)
    _attempt(
        vault,
        repository,
        HELD_OUT_ITEM,
        points=0,
        clock=FrozenClock(NOW + timedelta(days=parameters.horizon_days)),
    )
    after = runner.invoke(app, ["cold-probe-audit", "--vault", str(paths.root)])
    assert after.exit_code == 0, after.output
    assert "false_certification_rate: 1.000 = 1/1" in after.output
    assert "Cold-outcome labels available to causal P4: 1" in after.output
