"""UX Phase 1: Add builds questions by itself (docs/specs/ux_learnloop_v1.md §6.4-§6.7).

A source added through Add is extracted, filed under an automatic subject, and
gets a study map for the chapter being read plus the next one, applied when
every gate passes (Q3), with consent asked once per provider (Q4), a cost pause
only when the build is unusually expensive (Q5) and one chapter ahead as the
learner reads (Q6). Every model call is a house fake.
"""

from __future__ import annotations

import pytest

from learnloop.content.pipeline.add_source import (
    AUTO_STUDY_MAP_JOB,
    AddSourceOptions,
    add_source,
    advance_reading_build,
    latest_auto_outcome,
    outline_chapters,
    reading_order_scope,
    request_auto_build,
    source_status_line,
    undo_source_questions,
)
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.vault.loader import load_vault

from tests.ux_phase1_support import (
    CLOCK,
    fake_services,
    fresh_library,
    grant_consent,
    repository,
    route,
    set_config,
    write_book,
)

DENY = (
    "vault", "extraction", "extract", "synthesis", "inventory", "proposal", "token",
    "study map", "facet", "learning object", "canonical", "ingest", "sidecar", "consent",
)


def _jobs(root, services):
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=services)
    return repo, jobs


def _add(root, jobs, source, **options):
    return add_source(load_vault(root), jobs, str(source), AddSourceOptions(**options), clock=CLOCK)


def _auto_jobs(repo):
    return repo.ingest_jobs_by_types((AUTO_STUDY_MAP_JOB,))


def _build_batches(repo):
    return [batch for batch in repo.list_ingest_batches() if batch["workflow_type"] == "bootstrap_synthesis"]


def _chapter_labels(repo, source_id):
    extraction_id = resolve_extraction_id(repo, source_id)
    return {chapter.unit_id: chapter.label for chapter in outline_chapters(build_source_outline(repo, extraction_id))}


def _assert_build_applied(repo, batch_id):
    batch = repo.get_ingest_batch(batch_id)
    assert batch["status"] == "completed", [
        (job["job_type"], job["status"], job.get("error")) for job in repo.ingest_jobs_for_batch(batch_id)
    ]
    synthesis = next(
        job for job in repo.ingest_jobs_for_batch(batch_id)
        if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}
    )
    result = synthesis["result"]
    assert result.get("applied") or result.get("auto_applied_item_ids"), result


def _assert_plain(line):
    assert line is not None
    text = (line["text"] + " " + ((line.get("action") or {}).get("label") or "")).lower()
    for word in DENY:
        assert word not in text, (word, line)


# --------------------------------------------------------------------------
# The happy path: one Add, zero decisions, an applied map for Ch. 1 and Ch. 2
# --------------------------------------------------------------------------


def test_adding_a_book_builds_questions_for_the_first_chapter_and_the_next(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())

    item = _add(root, jobs, write_book(tmp_path))

    assert item["status"] == "added"
    source_id = item["source_id"]
    vault = load_vault(root)
    # An automatic subject, named from the book, with no question asked.
    assert list(vault.subjects) == ["probability-book"]
    # Reading order: the contents page is skipped; Ch. 1 and the next chapter only.
    labels = _chapter_labels(repo, source_id)
    source_set = next(s for s in vault.source_sets if s.id == f"sset_quickadd_{source_id}")
    scoped = [labels.get(entry.unit_id) for entry in source_set.members[0].scope]
    assert scoped == ["1 Probability and counting", "2 Conditional probability"]
    outcome = latest_auto_outcome(repo, source_id)
    assert outcome["outcome"] == "building"
    assert outcome["chapters"] == ["1 Probability and counting", "2 Conditional probability"]
    # The build ran through the same gates and applied itself (Q3).
    builds = _build_batches(repo)
    assert len(builds) == 1 and builds[0]["status"] == "completed"
    synthesis = next(job for job in repo.ingest_jobs_for_batch(builds[0]["id"]) if job["job_type"] == "bootstrap_synthesis")
    assert synthesis["result"]["applied"] is True
    # Questions are built as the learner reads (Q6), not up front.
    assert synthesis["payload"]["brief"]["practice_items"] == "as_you_read"
    line = source_status_line(repo, load_vault(root), source_id)
    assert line["text"] == "Questions for Ch. 1–2 come up as you read"
    assert line["action"] is None  # Undo lives in details (usability round 1, U8)
    _assert_plain(line)


def test_a_small_source_is_built_whole(tmp_path):
    root = fresh_library(tmp_path, scope_cap=None)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path, "short_article.md"))
    vault = load_vault(root)
    source_set = next(s for s in vault.source_sets if s.id == f"sset_quickadd_{item['source_id']}")
    assert len(source_set.members[0].scope) == len(_chapter_labels(repo, item["source_id"]))


def test_an_existing_subject_with_the_books_name_is_reused(tmp_path):
    from learnloop.vault.loader import add_subject

    root = fresh_library(tmp_path)
    grant_consent(root)
    add_subject(root, "probability", "Probability", clock=CLOCK)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path, "Probability.md"))
    vault = load_vault(root)
    assert list(vault.subjects) == ["probability"]
    assert latest_auto_outcome(repo, item["source_id"])["subject_id"] == "probability"


# --------------------------------------------------------------------------
# Kill switches ([ingest] auto_build, auto_apply_passing_builds)
# --------------------------------------------------------------------------


def test_auto_build_off_leaves_the_book_readable_only(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "auto_build"): False})
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    assert latest_auto_outcome(repo, item["source_id"]) == {
        "outcome": "skipped", "reason": "auto_build_off", "source_id": item["source_id"],
    }
    assert list(load_vault(root).subjects) == []
    assert _build_batches(repo) == []
    assert resolve_extraction_id(repo, item["source_id"]) is not None
    assert source_status_line(repo, load_vault(root), item["source_id"]) is None


def test_auto_apply_off_leaves_the_build_waiting_for_a_look(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "auto_apply_passing_builds"): False})
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    synthesis = next(
        job for job in repo.ingest_jobs_for_batch(_build_batches(repo)[0]["id"])
        if job["job_type"] == "bootstrap_synthesis"
    )
    assert synthesis["payload"]["apply"] is False
    assert synthesis["result"]["applied"] is False
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Questions for Ch. 1–2 need a look"
    assert line["action"]["kind"] == "open_changes"
    _assert_plain(line)


def test_a_past_exam_builds_nothing(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path, "midterm.md"), problem_set=True)
    assert latest_auto_outcome(repo, item["source_id"])["reason"] == "problem_set"
    assert repo.get_source_artifact(item["source_id"])["reader_enabled"] in (0, False)
    assert _build_batches(repo) == []


# --------------------------------------------------------------------------
# AI connection and consent (Q4)
# --------------------------------------------------------------------------


def test_no_ai_waits_with_a_connect_line(tmp_path):
    root = fresh_library(tmp_path)
    repo, jobs = _jobs(root, fake_services(route(ready=False, message="Codex is not set up")))
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert (outcome["outcome"], outcome["reason"]) == ("waiting", "no_ai")
    assert _build_batches(repo) == []
    assert list(load_vault(root).subjects) == []
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line == {
        "text": "Questions need an AI connection",
        "tone": "quiet",
        "action": {"kind": "connect_ai", "label": "Connect"},
        "details": "Codex is not set up",
    }
    _assert_plain(line)


def test_missing_consent_waits_for_one_ok(tmp_path):
    root = fresh_library(tmp_path)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert (outcome["outcome"], outcome["reason"], outcome["consent_key"]) == ("waiting", "needs_consent", "codex")
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Questions wait for your OK"
    assert line["details"] == "Codex (your ChatGPT account)"
    assert line["action"] == {"kind": "connect_ai", "label": "Review"}
    _assert_plain(line)


def test_a_book_kept_on_this_computer_sends_nothing(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path), keep_local=True)
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert (outcome["outcome"], outcome["reason"]) == ("waiting", "kept_local")
    assert _build_batches(repo) == []


# --------------------------------------------------------------------------
# Money only when unusual (Q5)
# --------------------------------------------------------------------------


def _metered(root, price):
    set_config(root, {("ingest", "cost_pause", "prices", "openrouter"): price})
    grant_consent(root, "openrouter")
    return route(provider="openrouter", subscription=False, consent_key="openrouter")


def test_an_expensive_build_pauses_once_with_one_line(tmp_path):
    root = fresh_library(tmp_path)
    authoring = _metered(root, 400_000.0)
    # The threshold's pause alone: the daily guard (5.00 by default since the
    # owner's 2026-10-13 caps direction) is raised out of the way.
    set_config(root, {("ingest", "cost_pause", "daily_cap_usd"): 1_000_000_000.0})
    repo, jobs = _jobs(root, fake_services(authoring))
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert (outcome["outcome"], outcome["reason"]) == ("paused", "cost")
    assert outcome["estimate_usd"] > 1.0
    assert _build_batches(repo) == []
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"].startswith("Building questions for Ch. 1–2 would cost about $")
    assert line["action"] == {"kind": "build_now", "label": "Build them"}
    _assert_plain(line)

    # One explicit "Build them" runs it, past the pause.
    request_auto_build(jobs, item["source_id"], approved=True)
    assert latest_auto_outcome(repo, item["source_id"])["outcome"] == "building"
    assert len(_build_batches(repo)) == 1


def test_a_cheap_metered_build_runs_silently(tmp_path):
    root = fresh_library(tmp_path)
    authoring = _metered(root, 0.01)
    repo, jobs = _jobs(root, fake_services(authoring))
    item = _add(root, jobs, write_book(tmp_path))
    assert latest_auto_outcome(repo, item["source_id"])["outcome"] == "building"


def test_a_quarter_of_the_daily_cap_also_pauses(tmp_path):
    root = fresh_library(tmp_path)
    authoring = _metered(root, 2_000.0)
    set_config(root, {
        ("ingest", "cost_pause", "threshold_usd"): 1000.0,
        ("ingest", "cost_pause", "daily_cap_usd"): 1.0,
    })
    repo, jobs = _jobs(root, fake_services(authoring))
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert (outcome["outcome"], outcome["reason"]) == ("paused", "cost")
    assert 0.25 < outcome["estimate_usd"] < 1000.0


def test_the_subscription_never_pauses_for_cost(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "cost_pause", "threshold_usd"): 0.0})
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert outcome["outcome"] == "building"
    # Billed to the subscription: never paused, never capped, but its cost is
    # kept as a token estimate (Slice A §5 rule 6), not recorded as $0.
    assert outcome["cost_basis"] == "estimated_only"
    assert outcome["estimate_tokens"] > 0
    assert outcome["estimate_usd"] is None
    assert outcome["authorized_usd"] is None


# --------------------------------------------------------------------------
# One chapter ahead as the learner reads (Q6)
# --------------------------------------------------------------------------


def test_reading_into_the_next_chapter_builds_one_chapter_ahead(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    source_id = item["source_id"]
    extraction_id = resolve_extraction_id(repo, source_id)
    by_label = {label: unit_id for unit_id, label in _chapter_labels(repo, source_id).items()}

    # Still inside the built chapters' lead: nothing new to build.
    assert advance_reading_build(jobs, extraction_id, by_label["1 Probability and counting"]) is None
    assert len(_build_batches(repo)) == 1

    started = advance_reading_build(jobs, extraction_id, by_label["2 Conditional probability"])
    assert started is not None and started["chapters"] == ["3 Random variables"]
    source_set = next(s for s in load_vault(root).source_sets if s.id == f"sset_quickadd_{source_id}")
    labels = _chapter_labels(repo, source_id)
    assert [labels[entry.unit_id] for entry in source_set.members[0].scope] == [
        "1 Probability and counting", "2 Conditional probability", "3 Random variables",
    ]
    newest = _build_batches(repo)[0]
    inventory = next(job for job in repo.ingest_jobs_for_batch(newest["id"]) if job["job_type"] == "inventory")
    assert [unit["unit_id"] for unit in inventory["payload"]["units"]] == [by_label["3 Random variables"]]
    # The chapter really reconciled into the book's map and applied (review:
    # this used to pass while the append lane failed on the bootstrap fake).
    _assert_build_applied(repo, newest["id"])
    line = source_status_line(repo, load_vault(root), source_id)
    # The line names every chapter built so far, not only the newest build
    # (usability round 1: "Questions for Conditional probability" read oddly
    # while the learner was in Ch. 1).
    assert line["text"] == "Questions for Ch. 1–3 come up as you read"


def test_jumping_ahead_builds_the_chapter_jumped_to(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    by_label = {label: unit_id for unit_id, label in _chapter_labels(repo, item["source_id"]).items()}
    started = advance_reading_build(jobs, extraction_id, by_label["4 Expectation"])
    assert started["chapters"] == ["4 Expectation"]
    _assert_build_applied(repo, _build_batches(repo)[0]["id"])


def test_reading_does_nothing_while_auto_build_is_off(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    set_config(root, {("ingest", "auto_build"): False})
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    by_label = {label: unit_id for unit_id, label in _chapter_labels(repo, item["source_id"]).items()}
    assert advance_reading_build(jobs, extraction_id, by_label["2 Conditional probability"]) is None


# --------------------------------------------------------------------------
# One-tap undo (Q3)
# --------------------------------------------------------------------------


def test_undo_takes_the_books_questions_back_out(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    built = [lo_id for lo_id, lo in load_vault(root).learning_objects.items() if lo.status == "active"]
    assert built
    reverted = undo_source_questions(jobs, item["source_id"], clock=CLOCK)
    assert reverted > 0
    # The book's topics stop being served; nothing the learner earned is deleted.
    after = load_vault(root).learning_objects
    assert all(after[lo_id].status == "dormant" for lo_id in built)
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Questions for this book were taken back out"
    assert line["action"] == {"kind": "build_now", "label": "Build them again"}
    _assert_plain(line)


def test_while_the_next_build_is_planned_the_card_says_chapters_found(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    jobs._ensure_worker = lambda: None  # hold the queue: the planner stays queued
    request_auto_build(jobs, item["source_id"])
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line == {"text": "Chapters found", "tone": "working", "action": None, "details": None}


# --------------------------------------------------------------------------
# Plain failure lines (§6.7) and the reading-order scope itself
# --------------------------------------------------------------------------


def test_a_failed_fetch_says_so_in_one_line(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunnerError

    def unreachable(source, category, ctx):
        raise IngestRunnerError("HTTP 503 from example.org", code="fetch_failed", retryable=True)

    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(fetch=unreachable))
    item = add_source(load_vault(root), jobs, "https://example.org/notes", AddSourceOptions(), clock=CLOCK)
    assert item["status"] == "queued"
    line = source_status_line(repo, load_vault(root), None, batch_id=item["batch_id"])
    assert line["text"] == "Couldn't reach the page"
    assert line["action"] == {"kind": "retry", "label": "Try again"}
    assert "503" in line["details"]
    _assert_plain(line)


@pytest.mark.parametrize(
    ("labels", "tokens", "expected"),
    [
        (["Contents", "1 Sets", "2 Maps", "3 Groups"], [5, 30, 30, 30], ["1 Sets", "2 Maps"]),
        (["Preface", "Acknowledgements", "1 Sets", "2 Maps"], [40, 5, 30, 30], ["1 Sets", "2 Maps"]),
        # The first chapter alone is over the cap: it is still built, alone.
        (["1 Sets", "2 Maps"], [90, 30], ["1 Sets"]),
        # Tiny page-like units accumulate up to the floor.
        (["p1", "p2", "p3", "p4", "p5", "p6"], [4, 4, 4, 4, 4, 4], ["p1", "p2", "p3", "p4"]),
    ],
)
def test_reading_order_scope(labels, tokens, expected):
    from learnloop.content.pipeline.add_source import Chapter

    chapters = [
        Chapter(unit_id=f"u{index}", label=label, unit_ids=(f"u{index}",), tokens=count)
        for index, (label, count) in enumerate(zip(labels, tokens), start=1)
    ]
    picked = reading_order_scope(chapters, built=set(), cap_tokens=60, floor_tokens=15)
    assert [chapter.label for chapter in picked] == expected
