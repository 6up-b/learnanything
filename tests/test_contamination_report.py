"""Slice 2 T4: contamination detectors as shadow flags (spec §7, §13).

Fakes only: a fake judge, hand-placed vectors and no provider. Covers the
record recipes, the three detectors' shortlists, who decides (owner >
verifier > llm; never a score), degradation to the lexical floor, proposals
that are never executed, spend admission and the CLI.
"""
from __future__ import annotations

import hashlib
import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import report_call_usage
from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import put_vector
from learnloop.db.stores.judgments import append_judgment
from learnloop.ops.contamination import report as report_module
from learnloop.ops.contamination.judge import ContaminationJudgment
from learnloop.ops.contamination.recipes import CONTAMINATION_RECIPES
from learnloop.ops.contamination.report import contamination_report
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.substrate.activities import reserve_surface, resolve_legacy_item
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, select_recipes
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import NOW, create_basic_vault

BASIC_ITEM = "pi_svd_define_001"
PARAPHRASE = "It splits any matrix into an orthogonal factor, a diagonal scaling and another orthogonal factor."
LEARNER_QUESTION = "PRIVATE LEARNER QUESTION about my exam"


class Judge:
    provider_name = "fake"
    provider_type = "openai_chat"
    model = "fake-judge"

    def __init__(self, verdict="contaminated", *, fail_at=None):
        self.verdict = verdict
        self.fail_at = fail_at
        self.calls = []

    def supports(self, capability):
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        self.calls.append(request)
        assert request.isolated and request.output_budget_tokens == 1024
        report_call_usage({"input_tokens": 10, "output_tokens": 20, "resolved_model": "fake-resolved"})
        if self.fail_at == len(self.calls):
            raise AIProviderUnavailable("PRIVATE provider detail")
        verdict = self.verdict(request) if callable(self.verdict) else self.verdict
        return ContaminationJudgment(
            verdict=verdict, rationale=f"judged {verdict}",
            revealed="orthogonal factor" if verdict == "contaminated" else "",
        )


def _item(loaded, item_id, *, prompt, expected, origin="codex_proposal"):
    base = loaded.practice_items[BASIC_ITEM]
    item = base.model_copy(update={
        "id": item_id, "prompt": prompt, "expected_answer": expected,
        "provenance": base.provenance.model_copy(update={"origin": origin}),
    })
    upsert_practice_item(loaded.root, item)


def _answer(repository, item_id, answer, *, context="practice", leak_suspected=False, overlap=0.0,
            created_at="2026-05-19T12:00:00+00:00", source_context=None):
    event_id = repository.insert_question_event({
        "context": context, "practice_item_id": item_id, "question_md": LEARNER_QUESTION,
        "answer_md": answer, "question_type": "mechanism", "answer_status": "answered",
        "leak_suspected": leak_suspected, "created_at": created_at,
    })
    repository.update_question_event_answer(
        event_id, answer_md=answer, question_type="mechanism", facets=[], hint_equivalent=True,
        leak_suspected=leak_suspected, answer_status="answered", leak_overlap=overlap,
        source_context=source_context,
    )
    return event_id


def _vectors(loaded, repository, recipe, vectors):
    """Place fake vectors for the CURRENT content hash of each named record."""
    records = {record.record_id: record for record in CONTAMINATION_RECIPES[recipe].records(loaded)}
    with repository.connection() as connection:
        for record_id, vector in vectors.items():
            record = records[record_id]
            put_vector(
                connection, record_kind=record.record_kind, record_id=record_id, field=record.field,
                content_hash=record.content_hash, model_id=loaded.config.embedding.model,
                task_prefix="retrieval-document", vector=vector,
            )


def _db_hash(paths):
    return hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()


def run(loaded, client, **kwargs):
    """No noise-floor repeats unless a test asks: call counts stay per pair."""
    return contamination_report(
        loaded, client=client, caps=kwargs.pop("caps", SpendCaps(max_total_tokens=1_000_000)),
        price_per_million=kwargs.pop("price_per_million", 1.0),
        repeat_sample=kwargs.pop("repeat_sample", 0), **kwargs,
    )


@pytest.fixture
def tutor_vault(tmp_path):
    """Three items; one paraphrased tutor leak the lexical floor misses."""
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    _item(loaded, "pi_trace", prompt="Define the trace.", expected="The sum of the diagonal entries.")
    _item(loaded, "pi_rank", prompt="Define rank.", expected="The dimension of the column space.")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    event = _answer(repository, BASIC_ITEM, PARAPHRASE)
    _vectors(loaded, repository, "item/expected_answer", {
        BASIC_ITEM: [1.0, 0.0, 0.0], "pi_trace": [0.0, 1.0, 0.0], "pi_rank": [0.0, 0.0, 1.0],
    })
    _vectors(loaded, repository, "question_event/answer", {event: [0.9, 0.05, 0.05]})
    return paths, loaded, repository, event


# --- recipes ----------------------------------------------------------------


def test_recipes_embed_only_the_model_text_and_stay_out_of_the_default_backfill(tutor_vault):
    paths, loaded, repository, event = tutor_vault
    _answer(repository, None, "Library answer with no item.", context="library")
    pending = repository.insert_question_event({
        "context": "practice", "practice_item_id": BASIC_ITEM, "question_md": "q", "answer_status": "pending",
    })
    records = {r.record_id: r for r in CONTAMINATION_RECIPES["question_event/answer"].records(loaded)}
    assert set(records) == {event} and pending not in records
    assert records[event].text == PARAPHRASE
    assert all(LEARNER_QUESTION not in r.text for recipe in CONTAMINATION_RECIPES.values() for r in recipe.records(loaded))
    expected = {r.record_id: r.text for r in CONTAMINATION_RECIPES["item/expected_answer"].records(loaded)}
    assert expected["pi_trace"] == "The sum of the diagonal entries."
    # Shared Phase 1 recipe; T4's kinds never join the default backfill.
    assert CONTAMINATION_RECIPES["item/stem"] is EMBEDDING_RECIPES["item/stem"]
    assert set(CONTAMINATION_RECIPES) - {"item/stem"} and not (set(CONTAMINATION_RECIPES) - {"item/stem"}) & set(EMBEDDING_RECIPES)
    assert [r.name for r in select_recipes()] == ["facet/definition", "item/stem"]
    assert all(recipe.text_recipe for recipe in CONTAMINATION_RECIPES.values())


class FakeEmbedder:
    model_id = model = "qwen/qwen3-embedding-8b"
    dims = 3
    modalities = frozenset({"text"})
    max_input_tokens = 32_768
    provider_name = "fake"

    def __init__(self):
        self.inputs = []

    def embed(self, inputs, task_prefix):
        from learnloop.ai.execution import model_call

        with model_call(self, purpose="embedding", prompt=inputs):
            self.inputs.extend(inputs)
            report_call_usage({"input_tokens": len(inputs), "output_tokens": 0})
            return [[1.0, 0.0, 0.0] for _ in inputs]


def test_embed_uses_the_phase_1_backfill_with_the_t4_registry(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    event = _answer(repository, BASIC_ITEM, PARAPHRASE)
    loaded = load_vault(paths.root)
    loaded.config.embedding.enabled = loaded.config.embedding.backfill_enabled = True
    loaded.config.embedding.dimensions = 3
    embedder = FakeEmbedder()
    report = backfill_embeddings(
        loaded, caps=SpendCaps(), registry=CONTAMINATION_RECIPES,
        recipes=("question_event", "item/expected_answer"), client_factory=lambda: embedder,
    )
    assert report["status"] == "complete" and report["embedded"] == 2
    assert report["recipes"] == ["item/expected_answer", "question_event/answer"]
    assert PARAPHRASE in embedder.inputs and LEARNER_QUESTION not in embedder.inputs
    with repository.connection() as connection:
        kinds = {row[0] for row in connection.execute("SELECT record_kind || '/' || field FROM embedding_vectors")}
    assert kinds == {"item/expected_answer", "question_event/answer"}
    assert event


# --- the tutor answer detector ---------------------------------------------


def test_paraphrased_leak_missed_by_the_floor_is_judged_and_only_proposed(tutor_vault):
    paths, loaded, repository, event = tutor_vault
    with repository.connection() as connection:
        reveals_before = connection.execute("SELECT COUNT(*) FROM reveal_events").fetchone()[0]
    judge = Judge()
    report = run(loaded, judge, detectors=("tutor_answer_leak",))
    assert report["status"] == "complete", report
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["embedding"]["status"] == "used"
    assert tutor["lexical_floor"]["flagged_subjects"] == 0
    assert tutor["shortlist"] == {
        "pairs": 1, "by_reason": {"bound": 1, "lexical": 0, "symbolic": 0, "embedding": 1}, "embedding_only": 1,
    }
    assert tutor["decided"]["flags"] == 1 and tutor["agreement"]["shadow_only"] == 1
    assert tutor["flag_rate"] == 1.0
    [proposal] = tutor["proposals"]
    assert proposal["action"] == "reveal_debit" and proposal["question_event_id"] == event
    assert proposal["decided_by"] == "llm"
    [sample] = tutor["samples"]["shadow_only"]
    assert sample["signals"]["embedding"]["rank"] == 1 and sample["decision"]["verdict"] == "reveal"
    assert report["proposals_executed"] == 0
    # Never executed: the live reveal ledger is untouched.
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM reveal_events").fetchone()[0] == reveals_before
        row = connection.execute("SELECT * FROM judgment_ledger WHERE task='reveal'").fetchone()
        receipts = connection.execute(
            "SELECT purpose, owner_kind, resolved_model, budget_json FROM model_call_receipts "
            "WHERE owner_kind='contamination_report'"
        ).fetchall()
    assert (row["judge"], row["verdict"], row["judge_model"]) == ("llm", "reveal", "fake-resolved")
    assert (row["left_kind"], row["left_id"], row["right_kind"], row["right_id"]) == (
        "question_event", event, "practice_item", BASIC_ITEM)
    assert row["prompt_version"] == "contamination-reveal-v1" and row["input_hash"]
    assert [(r[0], r[2]) for r in receipts] == [("contamination_reveal_judgment", "fake-resolved")]
    assert json.loads(receipts[0][3])["contamination_judge"]["prompt_version"] == "contamination-reveal-v1"
    # The judge sees the two texts only: never the learner, never the signals.
    prompt = judge.calls[0].prompt
    assert PARAPHRASE in prompt and LEARNER_QUESTION not in prompt
    assert "embedding" not in prompt and "rank" not in prompt


@pytest.mark.parametrize("primed", [0, 1])
def test_a_reveal_debit_is_proposed_only_when_the_next_attempt_was_recorded_clean(tutor_vault, primed):
    _paths, loaded, repository, _event = tutor_vault
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
            "attempt_type, learner_answer_md, hints_used, created_at, session_id, primed) "
            "VALUES ('att_next', ?, 'lo_svd_definition', 'short_answer', 'independent_attempt', "
            "'my answer', 0, '2026-05-19T13:00:00+00:00', 'sess', ?)",
            (BASIC_ITEM, primed),
        )
        connection.commit()
    tutor = run(loaded, Judge(), detectors=("tutor_answer_leak",))["detectors"]["tutor_answer_leak"]
    assert tutor["decided"]["flags"] == 1
    if primed:
        assert tutor["proposals"] == []
    else:
        [proposal] = tutor["proposals"]
        assert proposal["next_attempt"] == {
            "id": "att_next", "created_at": "2026-05-19T13:00:00+00:00", "primed": False,
        }


def test_a_judge_that_says_clean_leaves_no_flag_whatever_the_score(tutor_vault):
    _paths, loaded, _repository, _event = tutor_vault
    report = run(loaded, Judge("clean"), detectors=("tutor_answer_leak",))
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["shortlist"]["pairs"] == 1
    assert tutor["decided"] == {"flags": 0, "clean": 1, "unsure": 0, "undecided": 0, "by_judge": {"llm": 1}}
    assert tutor["proposals"] == [] and tutor["flagged_subjects"] == 0
    assert tutor["embedding_scores"]["clean"]["n"] == 1


def test_no_judge_and_no_vectors_degrade_to_the_floor(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    caught = _answer(repository, BASIC_ITEM, "A matrix factorization into U, Sigma, and V transpose.",
                     leak_suspected=True, overlap=1.0)
    paraphrase = _answer(repository, BASIC_ITEM, PARAPHRASE)
    loaded = load_vault(paths.root)
    judge = Judge()
    report = run(loaded, judge, detectors=("tutor_answer_leak",))
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["embedding"]["status"] == "unavailable"
    assert tutor["embedding"]["reason"] == "index item/expected_answer is incomplete"
    assert tutor["embedding"]["index"]["missing"] == 1
    # No vectors: no rank signal, but each bound pair still reaches the judge.
    assert tutor["shortlist"]["pairs"] == 2 and tutor["shortlist"]["by_reason"]["lexical"] == 1
    assert tutor["shortlist"]["by_reason"]["embedding"] == 0
    assert len(judge.calls) == 2 and tutor["agreement"]["floor_and_shadow"] == 1
    assert tutor["samples"]["floor_and_shadow"][0]["question"]["left_id"] == caught
    # The floor already debited the caught answer; only the paraphrase is proposed.
    [proposal] = tutor["proposals"]
    assert proposal["question_event_id"] == paraphrase
    free = run(loaded, Judge(), judge=False)
    assert free["status"] == "complete" and free["judge"]["requests"] == 0
    # No held-out exam material and no live reserve: nothing measured, no rate.
    for name in ("exam_leakage", "reader_reveal"):
        assert free["detectors"][name]["status"] == "no_targets"
        assert free["detectors"][name]["flag_rate"] is None


def test_a_live_debit_that_alone_primes_the_next_attempt_counts_as_the_floor(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    debited = _answer(repository, BASIC_ITEM, "Partly: U and V transpose are involved.", overlap=0.5)
    _answer(repository, BASIC_ITEM, "Think about which factors are orthogonal.", overlap=0.2)

    def verdict(request):
        return "contaminated" if "Partly" in request.prompt else "clean"

    tutor = run(load_vault(paths.root), Judge(verdict), detectors=("tutor_answer_leak",))["detectors"]["tutor_answer_leak"]
    # 0.5 is below the 0.8 leak flag but above the 0.35 auto-prime debit.
    assert tutor["lexical_floor"]["flagged_subjects"] == 1
    assert tutor["agreement"]["floor_and_shadow"] == 1 and tutor["proposals"] == []
    [sample] = tutor["samples"]["floor_and_shadow"]
    assert sample["question"]["left_id"] == debited
    assert sample["signals"]["leak_suspected"] is False and sample["signals"]["live_reveal_amount"] == 0.5


def test_a_turn_from_before_the_reveal_ledger_was_never_debited(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    legacy = repository.insert_question_event({
        "context": "practice", "practice_item_id": BASIC_ITEM, "question_md": LEARNER_QUESTION,
        "answer_md": "A factorization into U, Sigma and V.", "answer_status": "answered",
    })
    tutor = run(load_vault(paths.root), Judge(), detectors=("tutor_answer_leak",))["detectors"]["tutor_answer_leak"]
    assert tutor["lexical_floor"]["flagged_subjects"] == 0
    [proposal] = tutor["proposals"]
    assert proposal["question_event_id"] == legacy and proposal["live_reveal_amount"] == 0.0
    [sample] = tutor["samples"]["shadow_only"]
    assert sample["signals"]["floor_score"] > 0.35  # recomputed for display only


def test_a_subject_without_its_vector_is_counted_and_falls_back(tutor_vault):
    _paths, loaded, repository, _event = tutor_vault
    _answer(repository, "pi_trace", "Add up the main diagonal.")
    report = run(load_vault(loaded.root), Judge(), detectors=("tutor_answer_leak",), judge=False)
    embedding = report["detectors"]["tutor_answer_leak"]["embedding"]
    assert embedding["subjects_with_vectors"] == 1 and embedding["subjects_without_vectors"] == 1


def test_symbolic_verifier_decides_math_reveals_and_outranks_the_llm(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    _item(loaded, "pi_prob", prompt=r"Compute $\frac{1}{3} + \frac{1}{3}$.", expected="2/3")
    repository = Repository(paths.sqlite_path)
    # Works the item's own expression to its answer: the link is established.
    event = _answer(repository, "pi_prob", r"Add the numerators: 1/3 + 1/3 = $\frac{2}{3}$.")
    loaded = load_vault(paths.root)
    report = run(loaded, None, detectors=("tutor_answer_leak",), judge=False)
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["symbolic"] == {"math_pairs": 1, "matches": 1, "verifier_decisions": 1}
    assert tutor["decided"]["flags"] == 1 and tutor["decided"]["by_judge"] == {"verifier": 1}
    assert report["verifier"]["written"] == 1
    report = run(loaded, Judge("clean"), detectors=("tutor_answer_leak",))
    assert report["verifier"]["written"] == 0  # content-addressed: never appended twice
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["decided"]["flags"] == 1 and tutor["proposals"][0]["decided_by"] == "verifier"
    with repository.connection() as connection:
        rows = connection.execute("SELECT judge, verdict, prompt_version FROM judgment_ledger ORDER BY judge").fetchall()
    assert [tuple(r) for r in rows] == [
        ("llm", "clean", "contamination-reveal-v1"), ("verifier", "reveal", "contamination-symbolic-v2"),
    ]
    assert event


def test_owner_verdict_outranks_the_judge(tutor_vault):
    _paths, loaded, repository, event = tutor_vault
    run(loaded, Judge(), detectors=("tutor_answer_leak",))
    with repository.connection() as connection:
        append_judgment(
            connection, task="reveal", left_kind="question_event", left_id=event,
            right_kind="practice_item", right_id=BASIC_ITEM, judge="owner",
            input_hash="owner-review", verdict="clean", rationale="Only names the factors' roles.",
        )
    report = run(loaded, Judge(), detectors=("tutor_answer_leak",))
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["decided"]["by_judge"] == {"owner": 1} and tutor["decided"]["flags"] == 0
    assert tutor["agreement"]["shadow_only"] == 0 and report["judge"]["pending"] == 0


# --- dry run, caps, resume --------------------------------------------------


def test_dry_run_changes_nothing_and_builds_no_client(tutor_vault, monkeypatch):
    paths, loaded, _repository, _event = tutor_vault
    monkeypatch.setattr(report_module, "ready_client_for_task", lambda *a, **k: pytest.fail("client built"))
    before = _db_hash(paths)
    report = contamination_report(loaded, caps=SpendCaps(max_total_tokens=1_000_000), dry_run=True,
                                  price_per_million=1.0)
    assert report["status"] == "dry_run"
    # The default plan includes the noise floor: the one pair is judged twice.
    assert report["judge"]["pending"] == 2 and report["judge"]["estimate"]["calls"] == 2
    assert report["judge"]["repeat_requests"] == 1 and report["repeat_sample"] == 5
    assert report["judge"]["estimate"]["pairs"] == 1
    assert report["judge"]["estimate"]["estimated_usd"] > 0
    assert report["detectors"]["tutor_answer_leak"]["decided"]["undecided"] == 1
    assert _db_hash(paths) == before
    assert not (paths.root / ".learnloop" / "contamination-report.lock").exists()


@pytest.mark.parametrize("caps", [
    SpendCaps(max_candidates=0), SpendCaps(max_pairs=0), SpendCaps(max_calls=0),
    SpendCaps(max_total_tokens=1), SpendCaps(max_estimated_usd=0),
])
def test_caps_admit_before_any_call(tutor_vault, caps):
    _paths, loaded, _repository, _event = tutor_vault
    judge = Judge()
    report = run(loaded, judge, caps=caps)
    assert report["status"] == "over_budget" and not judge.calls
    assert report["detectors"]["tutor_answer_leak"]["shortlist"]["pairs"] == 1


def test_unknown_price_fails_closed_on_a_metered_route(tutor_vault):
    _paths, loaded, _repository, _event = tutor_vault
    judge = Judge()
    report = run(loaded, judge, price_per_million=None,
                 caps=SpendCaps(max_total_tokens=1_000_000, max_estimated_usd=1e9))
    assert report["status"] == "over_budget" and not judge.calls


def test_a_subscription_route_runs_without_a_price_and_records_estimated_cost(tutor_vault):
    _paths, loaded, repository, _event = tutor_vault
    judge = Judge()
    judge.provider_type = "codex_sdk"
    report = run(loaded, judge, price_per_million=None)
    assert report["status"] == "complete" and report["judge"]["billing"] == "subscription"
    with repository.connection() as connection:
        usage = json.loads(connection.execute(
            "SELECT usage_json FROM model_call_receipts WHERE owner_kind='contamination_report'"
        ).fetchone()[0])
    assert usage["cost_basis"] == "estimated_only"
    # The estimate is from the reported token usage (10 in + 20 out). Dollars
    # need an owner price, as for every subscription command (shared helper).
    assert usage["estimated_total_tokens"] == 30 and usage["estimated_token_source"] == "reported_usage"
    assert usage["estimated_usd"] is None and report["judge"]["price_source"] == "unknown"


def test_a_priced_subscription_run_records_a_numeric_estimate(tutor_vault):
    """F7 (rejected; see the review): with an owner price the estimate is numeric."""
    _paths, loaded, repository, _event = tutor_vault
    judge = Judge()
    judge.provider_type = "codex_sdk"
    dry = run(loaded, judge, dry_run=True, price_per_million=2.0)
    planned = dry["judge"]["estimate"]
    assert planned["total_tokens"] > 0 and planned["estimated_usd"] == pytest.approx(planned["total_tokens"] * 2e-6)
    report = run(loaded, judge, price_per_million=2.0)
    assert report["status"] == "complete" and report["judge"]["price_source"] == "owner_override"
    with repository.connection() as connection:
        usage = json.loads(connection.execute(
            "SELECT usage_json FROM model_call_receipts WHERE owner_kind='contamination_report'"
        ).fetchone()[0])
    assert usage["estimated_usd"] == pytest.approx(30 * 2e-6)
    # The command budget keeps the planned reservation (never refunded).
    assert report["judge"]["charged"]["estimated_usd"] == pytest.approx(planned["estimated_usd"])


def test_reruns_are_cached_and_a_new_revision_rejudges(tutor_vault):
    _paths, loaded, _repository, _event = tutor_vault
    first = Judge()
    assert run(loaded, first)["judge"]["completed"] == 1
    second = Judge()
    report = run(loaded, second)
    assert not second.calls and report["judge"]["cached"] == 1 and report["judge"]["charged"]["calls"] == 0
    third = Judge()
    assert run(loaded, third, judge_revision="2")["judge"]["completed"] == 1 and len(third.calls) == 1


def test_provider_errors_retry_within_caps_and_are_never_echoed(tutor_vault):
    _paths, loaded, _repository, _event = tutor_vault
    report = run(loaded, Judge(fail_at=1), caps=SpendCaps(max_total_tokens=1_000_000, max_retries=0))
    assert report["status"] == "provider_failed" and "PRIVATE" not in json.dumps(report)
    report = run(loaded, Judge(fail_at=1))
    assert report["status"] == "complete" and report["judge"]["charged"]["retries"] == 1


def test_the_report_never_calls_an_embedding_provider(tutor_vault, monkeypatch):
    _paths, loaded, _repository, _event = tutor_vault
    loaded.config.embedding.enabled = True
    from learnloop.ai.providers import openai_embedding

    for name in dir(openai_embedding):
        candidate = getattr(openai_embedding, name)
        if isinstance(candidate, type) and hasattr(candidate, "embed"):
            monkeypatch.setattr(candidate, "embed", lambda *a, **k: pytest.fail("embedding call"))
    monkeypatch.setattr(report_module, "ready_client_for_task", lambda *a, **k: pytest.fail("client built"))
    report = run(loaded, Judge())
    assert report["status"] == "complete"
    assert report["detectors"]["tutor_answer_leak"]["embedding"]["status"] == "used"


# --- reader reveal and exam leakage -----------------------------------------


def test_reader_reveal_proposes_a_burn_and_never_executes_it(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    _item(loaded, "pi_trace", prompt="Define the trace.", expected="The sum of the diagonal entries.")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    from learnloop.clock import FrozenClock

    surfaces = {}
    for item_id in (BASIC_ITEM, "pi_trace"):
        resolved = resolve_legacy_item(loaded, repository, loaded.practice_items[item_id],
                                       purpose="assessment", clock=FrozenClock(NOW))
        reserve_surface(repository, surface_id=resolved.surface_id, purpose="assessment", clock=FrozenClock(NOW))
        surfaces[item_id] = resolved.surface_id
    event = _answer(repository, None, PARAPHRASE, context="reader")
    _vectors(loaded, repository, "surface/statement", {
        surfaces[BASIC_ITEM]: [1.0, 0.0, 0.0], surfaces["pi_trace"]: [0.0, 1.0, 0.0],
    })
    _vectors(loaded, repository, "question_event/answer", {event: [0.9, 0.1, 0.0]})
    with repository.connection() as connection:
        exposures = connection.execute("SELECT COUNT(*) FROM activity_exposure_events").fetchone()[0]

    def verdict(request):
        return "contaminated" if "Define SVD" in request.prompt else "clean"

    report = run(loaded, Judge(verdict), detectors=("reader_reveal",), top_k=2)
    reader = report["detectors"]["reader_reveal"]
    assert reader["status"] == "scanned" and reader["targets"] == 2
    assert reader["shortlist"]["pairs"] == 2 and reader["lexical_floor"]["flagged_pairs"] == 0
    assert reader["decided"]["flags"] == 1 and reader["decided"]["clean"] == 1
    [proposal] = reader["proposals"]
    assert proposal == {
        "action": "burn_reserve", "surface_id": surfaces[BASIC_ITEM], "question_event_id": event,
        "asked_at": proposal["asked_at"], "reserved_at": proposal["reserved_at"],
        "decided_by": "llm", "judgment_id": proposal["judgment_id"],
    }
    with repository.connection() as connection:
        statuses = {row[0] for row in connection.execute(
            "SELECT status FROM activity_surface_reservations WHERE purpose='assessment'")}
        assert statuses == {"reserved"}
        assert connection.execute("SELECT COUNT(*) FROM activity_exposure_events").fetchone()[0] == exposures


def test_exam_leakage_shortlists_nearest_held_out_spans_for_the_judge(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

    root, repository = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repository,
                     clock=FrozenClock(NOW), apply=True, brief={"outcome": "exam prep"})
    generated_by_map = len(load_vault(root).practice_items)
    lo_id = "lo_diagonalize_symmetric"
    from learnloop.vault.models import PracticeItem

    for item_id, prompt in (
        ("pi_gen_leak", "Show that any real symmetric matrix can be diagonalized by an orthogonal matrix."),
        ("pi_gen_fresh", "Compute the eigenvalues of a 2x2 rotation matrix."),
    ):
        upsert_practice_item(root, PracticeItem(
            id=item_id, learning_object_id=lo_id, practice_mode="short_answer", prompt=prompt,
            expected_answer="See the spectral theorem.", provenance={"origin": "codex_proposal"},
            created_at=NOW.isoformat(), updated_at=NOW.isoformat(),
        ))
    loaded = load_vault(root)
    [span_key] = [r.record_id for r in CONTAMINATION_RECIPES["exam_span/text"].records(loaded)]
    _vectors(loaded, repository, "exam_span/text", {span_key: [1.0, 0.0, 0.0]})
    _vectors(loaded, repository, "item/stem", {"pi_gen_leak": [0.9, 0.1, 0.0], "pi_gen_fresh": [0.0, 1.0, 0.0]})

    def verdict(request):
        return "contaminated" if "orthogonal matrix" in request.prompt else "clean"

    items_before = {path: path.read_text() for path in (root / "subjects").rglob("*.yaml")}
    report = run(loaded, Judge(verdict), detectors=("exam_leakage",), top_k=1)
    exam = report["detectors"]["exam_leakage"]
    assert exam["status"] == "scanned" and exam["targets"] == 1
    assert exam["subjects"] == generated_by_map + 2
    assert exam["embedding"]["subjects_with_vectors"] == 2
    # Neither paraphrase reproduces a 6-word shingle: the floor sees nothing.
    assert exam["lexical_floor"]["flagged_subjects"] == 0
    assert exam["shortlist"]["by_reason"]["embedding"] == 2
    assert exam["decided"]["flags"] == 1 and exam["agreement"]["shadow_only"] == 1
    [proposal] = exam["proposals"]
    assert proposal["action"] == "review_item" and proposal["practice_item_id"] == "pi_gen_leak"
    assert proposal["source_span"] == span_key and proposal["live_gate_would_block"] is False
    with repository.connection() as connection:
        row = connection.execute("SELECT * FROM judgment_ledger WHERE task='leak' AND verdict='leak'").fetchone()
    assert (row["left_kind"], row["right_kind"], row["right_id"]) == ("practice_item", "source_span", span_key)
    assert items_before == {path: path.read_text() for path in (root / "subjects").rglob("*.yaml")}


# --- CLI ---------------------------------------------------------------------


def test_cli_dry_runs_and_refuses_unknown_detectors(tutor_vault):
    paths, _loaded, _repository, _event = tutor_vault
    runner = CliRunner()
    result = runner.invoke(app, ["contamination", "report", "--vault", str(paths.root), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "dry_run"
    assert json.loads(result.output)["judge"]["repeat_requests"] == 1
    result = runner.invoke(app, ["contamination", "report", "--vault", str(paths.root), "--dry-run",
                                 "--repeat-sample", "0", "--json"])
    assert result.exit_code == 0 and json.loads(result.output)["judge"]["repeat_requests"] == 0
    result = runner.invoke(app, ["contamination", "report", "--vault", str(paths.root), "--detector", "bogus", "--json"])
    assert result.exit_code == 1 and json.loads(result.output)["status"] == "invalid"


def test_cli_embed_dry_run_plans_every_t4_recipe(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _answer(Repository(paths.sqlite_path), BASIC_ITEM, PARAPHRASE)
    before = _db_hash(paths)
    result = CliRunner().invoke(app, ["contamination", "embed", "--vault", str(paths.root), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "dry_run" and report["recipes"] == sorted(CONTAMINATION_RECIPES)
    assert report["pending"] == 3  # item stem, expected answer and the tutor answer
    assert PARAPHRASE not in result.output and _db_hash(paths) == before


# --- Codex review fixes (F1-F7) ---------------------------------------------


def test_identical_answers_on_distinct_pairs_each_get_their_own_ledger_verdict(tutor_vault):
    """F1: the judgment id names the pair, not only the texts and settings."""
    _paths, loaded, repository, event = tutor_vault
    twin = _answer(repository, BASIC_ITEM, PARAPHRASE, created_at="2026-05-19T12:30:00+00:00")
    _vectors(loaded, repository, "question_event/answer", {twin: [0.9, 0.05, 0.05]})
    judge = Judge()
    report = run(loaded, judge, detectors=("tutor_answer_leak",), repeat_sample=0)
    assert report["status"] == "complete", report
    assert len(judge.calls) == 2 and report["judge"]["completed"] == 2
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id, left_id, input_hash FROM judgment_ledger WHERE judge='llm' ORDER BY left_id"
        ).fetchall()
    assert sorted(row["left_id"] for row in rows) == sorted([event, twin])
    assert len({row["id"] for row in rows}) == 2 and len({row["input_hash"] for row in rows}) == 1
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["decided"]["flags"] == 2 and len(tutor["proposals"]) == 2
    again = Judge()
    report = run(loaded, again, detectors=("tutor_answer_leak",), repeat_sample=0)
    assert not again.calls and report["judge"]["cached"] == 2


def test_identical_answers_resume_without_reusing_the_other_pairs_verdict(tutor_vault):
    """F1 across runs: an interrupted run judges only the missing pair on resume."""
    _paths, loaded, repository, event = tutor_vault
    twin = _answer(repository, BASIC_ITEM, PARAPHRASE, created_at="2026-05-19T12:30:00+00:00")
    _vectors(loaded, repository, "question_event/answer", {twin: [0.9, 0.05, 0.05]})
    first = Judge(fail_at=2)
    report = run(loaded, first, detectors=("tutor_answer_leak",), repeat_sample=0,
                 caps=SpendCaps(max_total_tokens=1_000_000, max_retries=0))
    assert report["status"] == "provider_failed" and report["judge"]["completed"] == 1
    resumed = Judge()
    report = run(loaded, resumed, detectors=("tutor_answer_leak",), repeat_sample=0)
    assert report["status"] == "complete" and len(resumed.calls) == 1
    assert report["judge"]["cached"] == 1 and report["judge"]["completed"] == 1
    with repository.connection() as connection:
        judged = sorted(row[0] for row in connection.execute(
            "SELECT left_id FROM judgment_ledger WHERE judge='llm'"))
    assert judged == sorted([event, twin])


def test_incidental_math_shortlists_but_never_decides_a_reveal(tmp_path):
    """F2: "page 144" is not a link to the answer 144; the judge decides."""
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    _item(loaded, "pi_square", prompt="Compute 12 * 12.", expected="144")
    repository = Repository(paths.sqlite_path)
    event = _answer(repository, "pi_square", "Read page 144 for the method.")
    loaded = load_vault(paths.root)
    report = run(loaded, Judge("clean"), detectors=("tutor_answer_leak",), repeat_sample=0)
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["symbolic"]["matches"] == 1 and tutor["symbolic"]["verifier_decisions"] == 0
    assert report["verifier"]["written"] == 0
    assert tutor["decided"]["flags"] == 0 and tutor["decided"]["by_judge"] == {"llm": 1}
    assert tutor["proposals"] == []
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE judge='verifier'").fetchone()[0] == 0
    assert event


def test_a_bound_tutor_pair_is_judged_however_many_items_share_its_answer(tmp_path):
    """F3: four items with one expected answer tie on rank; the bound pair is never dropped."""
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    twins = ("pi_a", "pi_b", "pi_c", "pi_d")
    for item_id in twins:
        _item(loaded, item_id, prompt=f"Define the trace ({item_id}).", expected="The sum of the diagonal entries.")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    event = _answer(repository, "pi_d", "Add up what sits on the main slant, top-left to bottom-right.")
    _vectors(loaded, repository, "item/expected_answer", {
        BASIC_ITEM: [1.0, 0.0, 0.0], **{item_id: [0.0, 1.0, 0.0] for item_id in twins},
    })
    _vectors(loaded, repository, "question_event/answer", {event: [0.0, 0.9, 0.1]})
    judge = Judge()
    report = run(loaded, judge, detectors=("tutor_answer_leak",), top_k=3, repeat_sample=0)
    tutor = report["detectors"]["tutor_answer_leak"]
    assert tutor["lexical_floor"]["flagged_subjects"] == 0
    assert tutor["shortlist"]["pairs"] == 1 and len(judge.calls) == 1
    assert tutor["decided"]["flags"] == 1
    [sample] = tutor["samples"]["shadow_only"]
    # Tied with three other items: rank 1, not an arbitrary 4 by item id.
    assert sample["signals"]["embedding"]["rank"] == 1
    assert sample["question"]["right_id"] == "pi_d"


def _render(repository, loaded, resolved, reservation, at):
    from learnloop.clock import FrozenClock
    from learnloop.substrate.activities import open_administration

    return open_administration(repository, resolved=resolved, reservation=reservation, clock=FrozenClock(at))


def test_a_reader_reveal_before_the_assessment_was_taken_stays_in_the_report(tmp_path):
    """F4: reserve -> reader reply -> assessment rendered; the reveal is still found."""
    from datetime import timedelta

    from learnloop.clock import FrozenClock

    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    _item(loaded, "pi_trace", prompt="Define the trace.", expected="The sum of the diagonal entries.")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    resolved, reservations = {}, {}
    for item_id in (BASIC_ITEM, "pi_trace"):
        resolved[item_id] = resolve_legacy_item(loaded, repository, loaded.practice_items[item_id],
                                                purpose="assessment", clock=FrozenClock(NOW))
        reservations[item_id] = reserve_surface(repository, surface_id=resolved[item_id].surface_id,
                                                purpose="assessment", clock=FrozenClock(NOW))
    surfaces = {item_id: value.surface_id for item_id, value in resolved.items()}
    before = _answer(repository, None, PARAPHRASE, context="reader",
                     created_at=(NOW + timedelta(hours=1)).isoformat())
    # The learner then takes the SVD assessment: its reservation is rendered.
    _render(repository, loaded, resolved[BASIC_ITEM], reservations[BASIC_ITEM], NOW + timedelta(hours=2))
    after = _answer(repository, None, PARAPHRASE, context="reader",
                    created_at=(NOW + timedelta(hours=3)).isoformat())
    _vectors(loaded, repository, "surface/statement", {
        surfaces[BASIC_ITEM]: [1.0, 0.0, 0.0], surfaces["pi_trace"]: [0.0, 1.0, 0.0],
    })
    _vectors(loaded, repository, "question_event/answer", {before: [0.9, 0.1, 0.0], after: [0.9, 0.1, 0.0]})

    def verdict(request):
        return "contaminated" if "Define SVD" in request.prompt else "clean"

    report = run(loaded, Judge(verdict), detectors=("reader_reveal",), top_k=2, repeat_sample=0)
    reader = report["detectors"]["reader_reveal"]
    assert reader["status"] == "scanned" and reader["targets"] == 2
    assert reader["embedding"]["status"] == "used"
    pairs = {(s["question"]["left_id"], s["question"]["right_id"])
             for category in reader["samples"].values() for s in category}
    # The reply after the render is not paired with the taken assessment.
    assert (after, surfaces[BASIC_ITEM]) not in pairs
    assert reader["decided"]["flags"] == 1
    [proposal] = reader["proposals"]
    # Already taken: nothing to burn; its cold evidence goes for review.
    assert proposal["action"] == "review_assessment"
    assert proposal["surface_id"] == surfaces[BASIC_ITEM] and proposal["question_event_id"] == before
    assert proposal["reservation_status"] == "rendered" and proposal["administration_id"]
    [sample] = reader["samples"]["shadow_only"]
    assert sample["signals"]["reservation_status"] == "rendered"


def test_a_reserve_already_burned_by_an_exposure_gets_no_burn_proposal(tmp_path):
    """F4: burn proposals only for currently eligible reserves."""
    from learnloop.clock import FrozenClock
    from learnloop.substrate.activities import append_exposure

    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    resolved = resolve_legacy_item(loaded, repository, loaded.practice_items[BASIC_ITEM],
                                   purpose="assessment", clock=FrozenClock(NOW))
    reserve_surface(repository, surface_id=resolved.surface_id, purpose="assessment", clock=FrozenClock(NOW))
    event = _answer(repository, None, PARAPHRASE, context="reader")
    _vectors(loaded, repository, "surface/statement", {resolved.surface_id: [1.0, 0.0, 0.0]})
    _vectors(loaded, repository, "question_event/answer", {event: [0.9, 0.1, 0.0]})
    report = run(loaded, Judge(), detectors=("reader_reveal",), repeat_sample=0)
    [proposal] = report["detectors"]["reader_reveal"]["proposals"]
    assert proposal["action"] == "burn_reserve" and proposal["question_event_id"] == event
    # Another reader answer burned it the way the live floor does: an exposure.
    append_exposure(repository, surface=repository.fetch_surface(resolved.surface_id), administration_id=None,
                    kind="externally_reported", purpose="instructional", consumes_unseen=False,
                    detail={"reason": "reader_answer_revealed_cue"}, clock=FrozenClock(NOW))
    report = run(loaded, Judge(), detectors=("reader_reveal",), repeat_sample=0)
    reader = report["detectors"]["reader_reveal"]
    assert reader["decided"]["flags"] == 1 and reader["proposals"] == []


def test_the_report_carries_a_repeated_judgment_noise_floor_and_owner_audits(tutor_vault):
    """F6: a bounded second pass, ledgered as its own row, planned in the dry run."""
    _paths, loaded, repository, event = tutor_vault
    _answer(repository, "pi_trace", "Add up the main diagonal.")
    dry = contamination_report(loaded, caps=SpendCaps(max_total_tokens=1_000_000), dry_run=True,
                               price_per_million=1.0, detectors=("tutor_answer_leak",), repeat_sample=1)
    assert dry["judge"]["pending"] == 3 and dry["judge"]["repeat_requests"] == 1
    assert dry["judge"]["estimate"]["calls"] == 3

    flips = {"n": 0}

    def flaky(request):
        flips["n"] += 1
        return "contaminated" if flips["n"] != 3 else "clean"

    judge = Judge(flaky)
    report = run(loaded, judge, detectors=("tutor_answer_leak",), repeat_sample=1)
    assert report["status"] == "complete" and len(judge.calls) == 3
    tutor = report["detectors"]["tutor_answer_leak"]
    floor = tutor["noise_floor"]
    assert floor["repeat_pairs"] == 1 and floor["compared"] == 1
    assert floor["disagree"] == 1 and floor["disagreement_rate"] == 1.0
    # The repeat never decides: decisions come from the first pass.
    assert tutor["decided"]["flags"] == 2
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT id, left_id, input_hash, rationale FROM judgment_ledger WHERE judge='llm'"
        ).fetchall()
    passes = sorted(json.loads(row["rationale"])["pass"] for row in rows)
    assert passes == [1, 1, 2] and len({row["id"] for row in rows}) == 3
    # Owner audits are the independent baseline: reported beside the floor.
    with repository.connection() as connection:
        append_judgment(
            connection, task="reveal", left_kind="question_event", left_id=event,
            right_kind="practice_item", right_id=BASIC_ITEM, judge="owner",
            input_hash="owner-audit", verdict="clean", rationale="Names roles only.",
        )
        connection.commit()
    again = Judge()
    report = run(loaded, again, detectors=("tutor_answer_leak",), repeat_sample=1)
    assert not again.calls
    audit = report["detectors"]["tutor_answer_leak"]["owner_audit"]
    assert audit["audited_pairs"] == 1
    assert audit["llm"] == {"compared": 1, "agree": 0, "disagree": 1}
    assert audit["verifier"] == {"compared": 0, "agree": 0, "disagree": 0}
