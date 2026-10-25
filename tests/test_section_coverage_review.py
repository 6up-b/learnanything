"""Curriculum C0a, Codex review (docs/reviews/curriculum-c0a-section-coverage-codex-review.md):
the negative tests for F1-F7 and F9 (F8 is in test_section_coverage_rpcs.py).

Every model and embedder is a fake; no test reaches a network.
"""
from __future__ import annotations

import json

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.source_retrieval import section_coverage as SC
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.practice_index_fakes import HashingEmbedder, _learning_object
from tests.section_coverage_fixtures import (
    BOOK_EIGEN,
    CoverageJudgeFake,
    build_coverage_vault,
    hold_out,
    table_counts,
)

#: lay_char's one passage (the section the tests mark held out mid-run).
LAY_CHAR_TEXT = "det(A - tI) = 0"
PRICED = "[source_retrieval]\nquery_embedding_price_per_million = 0.02\nllm_price_per_million = 2.0"


@pytest.fixture
def vault_paths(tmp_path):
    return build_coverage_vault(tmp_path / "vault")


def _rows(repository, lo_id="lo_eigen"):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM section_coverage WHERE learning_object_id = ? ORDER BY candidate_rank, id", (lo_id,))]


def _proposals(repository):
    with repository.connection() as connection:
        return [json.loads(row[0]) for row in connection.execute(
            "SELECT content_json FROM source_object_versions WHERE json_extract(content_json, '$.kind') = "
            "'instructional_role'")]


def _add_lo(paths, lo_id, title, summary):
    lo = _learning_object(lo_id, title)
    lo["summary"] = summary
    write_yaml(paths.learning_object_path("linear-algebra", lo_id), lo)


class HookedJudge(CoverageJudgeFake):
    """Runs ``hook(self)`` after recording each request (before it answers)."""

    def __init__(self, hook, **kwargs):
        super().__init__(**kwargs)
        self.hook = hook

    def complete(self, request):
        answer = super().complete(request)
        self.hook(self)
        return answer


# -- F1: protection that changes during a job -----------------------------------------------------


def test_f1_protection_marked_during_the_call_keeps_nothing(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    judge = HookedJudge(lambda fake: hold_out(repository, "lay_char"))
    result = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert any(LAY_CHAR_TEXT in prompt for prompt in judge.prompts)  # it was a candidate when sent
    assert judge.calls == 1 and result.status == "stale"
    assert _rows(repository) == [] and _proposals(repository) == []


def test_f1_a_retry_after_protection_changed_is_never_sent(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)

    def hold_then_fail(fake):
        if fake.calls == 1:
            hold_out(repository, "lay_char")
            raise AIProviderUnavailable("down")

    judge = HookedJudge(hold_then_fail)
    result = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert judge.calls == 1 and result.status == "stale" and _rows(repository) == []


def test_f1_a_batch_reads_protection_again_before_each_lo(vault_paths, tmp_path):
    # Control: unprotected, lay_char is one of lo_char's candidates.
    control_paths, control_repository = build_coverage_vault(tmp_path / "control")
    _add_lo(control_paths, "lo_char", "Characteristic equation",
            "The eigenvalues of A are the roots of the characteristic equation.")
    control = CoverageJudgeFake()
    SC.cover(load_vault(control_paths.root), control_repository, ["lo_eigen", "lo_char"], client=control)
    assert LAY_CHAR_TEXT in control.prompts[1]

    paths, repository = vault_paths
    _add_lo(paths, "lo_char", "Characteristic equation",
            "The eigenvalues of A are the roots of the characteristic equation.")
    vault = load_vault(paths.root)
    asked = {"n": 0}

    def between() -> bool:
        asked["n"] += 1
        if asked["n"] == 2:  # after lo_eigen's judgment, before lo_char's
            hold_out(repository, "lay_char")
        return False

    judge = CoverageJudgeFake()
    results = SC.cover(vault, repository, ["lo_eigen", "lo_char"], client=judge, cancelled=between)
    assert [result.status for result in results] == ["ready", "ready"] and judge.calls == 2
    assert LAY_CHAR_TEXT in judge.prompts[0] and LAY_CHAR_TEXT not in judge.prompts[1]
    assert all(row["section_id"] != "lay_char" for row in _rows(repository, "lo_char"))


# -- F2: query embeddings inside the command's caps ------------------------------------------------


def test_f2_query_embeddings_are_held_to_the_curriculum_caps(tmp_path):
    paths, repository = build_coverage_vault(
        tmp_path / "vault", embeddings=True,
        config=PRICED + "\n\n[curriculum]\nmax_daily_cost_usd = 0.0\ncover_max_cost_usd = 0.0")
    embedder = HashingEmbedder()
    judge = CoverageJudgeFake()  # the subscription: exempt from the dollar caps
    out = SC.cover_source(load_vault(paths.root), repository, "ext_lay", client=judge, embedder=embedder)
    assert embedder.calls == [] and judge.calls >= 1 and out["status"] == "done"
    # Generous caps: the same run embeds its queries (the test above is not vacuous).
    paths2, repository2 = build_coverage_vault(tmp_path / "vault2", embeddings=True, config=PRICED)
    embedder2 = HashingEmbedder()
    out2 = SC.cover_source(load_vault(paths2.root), repository2, "ext_lay", client=CoverageJudgeFake(),
                           embedder=embedder2)
    assert embedder2.calls and out2["usage"]["metered_usd"] > 0


def test_f2_the_dry_run_estimates_the_query_embeddings(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", embeddings=True, config=PRICED)
    before = table_counts(repository)
    embedder = HashingEmbedder()
    out = SC.cover_source(load_vault(paths.root), repository, "ext_lay", dry_run=True, embedder=embedder)
    planned = {entry["learning_object_id"]: entry for entry in out["learning_objects"]}
    plan = planned["lo_eigen"]["query_embedding"]
    assert plan["pending"] == 1 and plan["estimated_tokens"] > 0 and plan["estimated_usd"] > 0
    assert embedder.calls == [] and table_counts(repository) == before


# -- F3: a failed Qwen query keeps the deep search ---------------------------------------------------


def test_f3_a_failed_qwen_query_still_searches_deep(tmp_path, monkeypatch):
    from learnloop.source_retrieval import search as S

    paths, repository = build_coverage_vault(tmp_path / "vault", embeddings=True, config=PRICED)
    vault = load_vault(paths.root)
    seen = []
    real = S.search_spans

    def spy(*args, **kwargs):
        seen.append((kwargs.get("deep"), kwargs.get("query_vectors")))
        return real(*args, **kwargs)

    class Failing(HashingEmbedder):
        def embed(self, inputs, task_prefix):
            self.calls.append((list(inputs), task_prefix))
            raise AIProviderUnavailable("down")

    monkeypatch.setattr(S, "search_spans", spy)
    embedder = Failing()
    SC.search_sections(vault, repository, SC.Library(vault, repository), "eigenvalues of a matrix",
                       embedder=embedder)
    assert seen and all(deep is True and vectors == {} for deep, vectors in seen)
    assert len(embedder.calls) == 1  # one attempt for the LO, never one per source


# -- F4: a state judged before is current again --------------------------------------------------------


def test_f4_returning_to_a_judged_state_reads_its_rows_again(vault_paths):
    paths, repository = vault_paths
    path = paths.learning_object_path("linear-algebra", "lo_eigen")
    original = read_yaml(path)
    judge = CoverageJudgeFake()
    assert SC.judge(load_vault(paths.root), repository, "lo_eigen", client=judge).status == "ready"
    changed = dict(original, summary="An eigenvalue t of A has a nonzero x with Ax = tx.")
    write_yaml(path, changed)
    assert SC.judge(load_vault(paths.root), repository, "lo_eigen", client=judge).status == "ready"
    write_yaml(path, original)
    vault = load_vault(paths.root)
    assert SC.judge(vault, repository, "lo_eigen", client=judge).status == "fresh" and judge.calls == 2
    rows = SC.standing(vault, repository, SC.Library(vault, repository), ["lo_eigen"])["lo_eigen"]
    assert rows and ("ext_book", BOOK_EIGEN) in rows


# -- F5: the role proposals survive a crash ------------------------------------------------------------


def test_f5_a_crash_before_the_proposals_is_recovered_without_a_call(vault_paths, monkeypatch):
    from learnloop.reader import source_roles as RS

    paths, repository = vault_paths
    vault = load_vault(paths.root)
    real = RS.propose_roles

    def crash(*args, **kwargs):
        raise RuntimeError("the process died here")

    monkeypatch.setattr(RS, "propose_roles", crash)
    judge = CoverageJudgeFake()
    with pytest.raises(RuntimeError):
        SC.judge(vault, repository, "lo_eigen", client=judge)
    assert _proposals(repository) == []
    monkeypatch.setattr(RS, "propose_roles", real)
    result = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert judge.calls == 1 and result.status in ("ready", "fresh")
    assert _rows(repository) and {entry["judge"] for entry in _proposals(repository)} == {"section_coverage_judge"}
    with repository.connection() as connection:
        rationales = [json.loads(row[0]) for row in connection.execute(
            "SELECT rationale FROM judgment_ledger WHERE task = 'section_coverage' AND judge = 'llm'")]
    assert all(isinstance(entry.get("passages"), list) for entry in rationales)


# -- F6: a kept relation names its own pair ----------------------------------------------------------


def test_f6_kept_relations_join_only_their_own_endpoints(vault_paths, monkeypatch):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    library = SC.Library(vault, repository)
    origin = library.section("ext_book", BOOK_EIGEN)
    eigen, char = library.section("ext_lay", "lay_eigen"), library.section("ext_lay", "lay_char")
    entry = {"ask_id": "ask_1", "kept_at": "2026-10-25T00:00:00Z", "sources": [
        {"key": f"ext_book:{origin.span_ids[0]}", "source_object_id": "so_a"},
        {"key": f"ext_lay:{eigen.span_ids[0]}", "source_object_id": "so_b"},
        {"key": f"ext_lay:{char.span_ids[0]}", "source_object_id": "so_c"}],
        "relations": [
            {"fine": "different_notation", "left_source_object_id": "so_a", "right_source_object_id": "so_b"},
            {"fine": "disagreement", "left_source_object_id": "so_b", "right_source_object_id": "so_c"}]}
    monkeypatch.setattr(SC, "_kept_keys", lambda *args, **kwargs: [entry])
    kept = SC._kept_between(vault, repository, library, origin, ["lo_eigen"])
    assert kept[eigen.key][0]["relations"] == ["different_notation"]
    assert kept[char.key][0]["relations"] == []  # kept together, but no relation joins it to the origin


# -- F7: the read API stays read-only with embeddings on -------------------------------------------------


def test_f7_the_search_fallback_embeds_and_logs_nothing(tmp_path, monkeypatch):
    from learnloop.source_retrieval import feedback

    paths, repository = build_coverage_vault(
        tmp_path / "vault", embeddings=True, config=PRICED + "\n\n[embedding.source_space]\nlog_feedback = true")
    vault = load_vault(paths.root)
    monkeypatch.setattr(feedback, "deliver", lambda *args, **kwargs: pytest.fail("the read API logged a delivery"))
    embedder = HashingEmbedder()
    before = table_counts(repository)
    view = SC.correspondents(vault, repository, "ext_book", BOOK_EIGEN, embedder=embedder)
    assert view["status"] == "unchecked" and view["search"]["sources"]
    assert embedder.calls == [] and table_counts(repository) == before


# -- F9: a subscription run reports its token-based estimate ---------------------------------------------


def test_f9_a_subscription_run_reports_tokens_and_estimated_dollars(tmp_path):
    paths, repository = build_coverage_vault(tmp_path / "vault", config=PRICED)
    out = SC.cover_source(load_vault(paths.root), repository, "ext_lay", client=CoverageJudgeFake())
    usage = out["usage"]
    assert usage["cost_basis"] == "estimated_only" and usage["estimated_tokens"] > 0
    assert usage["estimated_usd"] == pytest.approx(usage["estimated_tokens"] * 2.0 / 1_000_000)
    assert usage["marginal_usd"] == 0.0


# -- Re-review F1: source-set protection read afresh (the CLI) and generation-bound (the sidecar) ------


def _make_exam(paths, source_id="src_lay"):
    """Change ``source_id``'s role to exam in the vault's files (as the sidecar's sources RPC does)."""

    from learnloop.vault.writer import upsert_source_set

    members = [{"source_id": source, "revision_id": revision,
                "default_role": "exam" if source in (source_id, "src_exam") else "primary_textbook"}
               for source, revision in (("src_book", "rev_book"), ("src_exam", "rev_exam"), ("src_lay", "rev_lay"))]
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": members})


def test_rr_f1_a_role_changed_on_disk_during_a_cli_judgment_keeps_nothing(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)  # the CLI's vault, loaded before the change
    judge = HookedJudge(lambda fake: _make_exam(paths))
    result = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert any(LAY_CHAR_TEXT in prompt for prompt in judge.prompts)  # sendable when it was sent
    assert judge.calls == 1 and result.status == "stale" and result.reason == "protection_changed"
    assert _rows(repository) == [] and _proposals(repository) == []


def test_rr_f1_a_retry_after_a_role_changed_on_disk_is_never_sent(vault_paths):
    paths, repository = vault_paths
    vault = load_vault(paths.root)

    def exam_then_fail(fake):
        if fake.calls == 1:
            _make_exam(paths)
            raise AIProviderUnavailable("down")

    judge = HookedJudge(exam_then_fail)
    result = SC.judge(vault, repository, "lo_eigen", client=judge)
    assert judge.calls == 1 and result.status == "stale" and _rows(repository) == []


def test_rr_f1_the_cli_batch_reads_source_sets_from_disk_before_each_lo(tmp_path):
    def run(paths, repository, change):
        _add_lo(paths, "lo_char", "Characteristic equation",
                "The eigenvalues of A are the roots of the characteristic equation.")
        vault = load_vault(paths.root)
        asked = {"n": 0}

        def between() -> bool:
            asked["n"] += 1
            if change and asked["n"] == 2:  # after the first LO's judgment, before the next
                _make_exam(paths)
            return False

        judge = CoverageJudgeFake()
        out = SC.cover_source(vault, repository, "ext_book", client=judge, cancelled=between)
        return judge, out

    control, _ = run(*build_coverage_vault(tmp_path / "control"), change=False)
    assert len(control.prompts) >= 2 and any(LAY_CHAR_TEXT in prompt for prompt in control.prompts[1:])
    paths, repository = build_coverage_vault(tmp_path / "vault")
    judge, out = run(paths, repository, change=True)
    assert out["status"] == "done" and len(judge.prompts) >= 2
    assert all("det(A - tI) = 0" not in prompt for prompt in judge.prompts[1:])
    judged = [entry["learning_object_id"] for entry in out["learning_objects"] if entry.get("status") == "ready"]
    with repository.connection() as connection:
        late = connection.execute(
            "SELECT COUNT(*) FROM section_coverage WHERE extraction_id = 'ext_lay' AND learning_object_id IN "
            f"({','.join('?' * len(judged[1:]))})", judged[1:]).fetchone()[0] if judged[1:] else 0
    assert late == 0


class ReloadingProvider:
    """The sidecar's loaded-vault provider (snapshot, generation, admit), which
    publishes ``reload`` (a same-vault reload) right after the next snapshot is
    read, i.e. while the guard is reading protection from the snapshot."""

    def __init__(self, vault):
        self.vault, self.gen, self.reload = vault, 0, None

    def snapshot(self):
        out = (self.vault, self.gen)
        if self.reload is not None:
            self.vault, self.gen, self.reload = self.reload, self.gen + 1, None
        return out

    def __call__(self):
        return self.snapshot()[0]

    def generation(self):
        return self.gen

    def admit(self, generation):
        return generation == self.gen


@pytest.mark.parametrize("when", ["request", "record"])
def test_rr_f1_a_reload_published_during_the_protection_read_is_never_admitted(vault_paths, when):
    paths, repository = vault_paths
    vault = load_vault(paths.root)
    _make_exam(paths)
    reloaded = load_vault(paths.root)  # the same vault with src_lay as exam
    provider = ReloadingProvider(vault)

    def arm(fake):
        if when == "record":
            provider.reload = reloaded  # published during the record's protection read

    if when == "request":
        provider.reload = reloaded  # published during the first attempt's protection read
    judge = HookedJudge(arm)
    result = SC.judge(vault, repository, "lo_eigen", client=judge, live_vault=provider)
    assert result.status == "stale" and _rows(repository) == [] and _proposals(repository) == []
    if when == "request":
        assert judge.calls == 0  # nothing was sent under the replaced snapshot


# -- Re-review F10: the role proposals and the rows commit together ----------------------------------------


def test_rr_f10_a_crash_after_the_proposals_is_recovered_from_the_ledger(vault_paths, monkeypatch):
    from learnloop.db.stores import section_coverage as store

    paths, repository = vault_paths
    real = store.insert

    def crash(*args, **kwargs):
        raise RuntimeError("the process died here")

    monkeypatch.setattr(store, "insert", crash)
    judge = CoverageJudgeFake(roles=("worked_example",))
    with pytest.raises(RuntimeError):
        SC.judge(load_vault(paths.root), repository, "lo_eigen", client=judge)
    assert judge.calls == 1 and _rows(repository) == []
    monkeypatch.setattr(store, "insert", real)
    # A restart: a new vault and library, which read every proposal that was committed.
    result = SC.judge(load_vault(paths.root), repository, "lo_eigen", client=judge)
    assert judge.calls == 1 and result.status in ("ready", "fresh")
    assert _rows(repository) and {entry["judge"] for entry in _proposals(repository)} == {"section_coverage_judge"}
