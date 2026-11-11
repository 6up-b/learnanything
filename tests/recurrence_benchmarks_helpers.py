"""What other test files use from ``tests/test_recurrence_benchmarks.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import csv
import json
import types  # noqa: E402

from learnloop.ai.spend import SpendCaps
from learnloop.diagnosis.recurrence.benchmarks import B1_WRITER_ROLE, register_suites
from learnloop.vault.loader import load_vault
from learnloop.ops import embedding_compare as compare
from learnloop.ops import pf_calls

from tests.diagnosis_fakes import FakeEmbeddingClient
from tests.split_live_helpers import enable_embeddings, split_vault


CAPS = SpendCaps(max_candidates=200, max_pairs=0, max_retries=10, max_calls=200, max_total_tokens=2_000_000, max_estimated_usd=1.0)


def _eedi(directory, *, manifest=True):
    directory.mkdir(parents=True, exist_ok=True)
    if manifest:
        (directory / "manifest.json").write_text(json.dumps({
            "sources": [{"name": "Eedi Mining Misconceptions in Mathematics", "version": "2024", "licence": "competition rules"}]
        }), encoding="utf-8")
    with (directory / "misconception_mapping.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MisconceptionId", "MisconceptionName"])
        writer.writerow([0, "Adds the numerators and adds the denominators when adding fractions"])
        writer.writerow([1, "Uses the diameter instead of the radius in the area of a circle"])
        writer.writerow([2, "Believes multiplying two negatives gives a negative"])
    with (directory / "train.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "QuestionId", "ConstructId", "ConstructName", "SubjectId", "SubjectName", "CorrectAnswer", "QuestionText",
            "AnswerAText", "AnswerBText", "AnswerCText", "AnswerDText",
            "MisconceptionAId", "MisconceptionBId", "MisconceptionCId", "MisconceptionDId",
        ])
        writer.writerow([1, 10, "Add fractions", 100, "Fractions", "A", "1/2 + 1/3 = ?", "5/6", "2/5", "1/5", "2/6", "", "0.0", "", ""])
        writer.writerow([2, 11, "Area of a circle", 101, "Circles", "B", "Area with diameter 6?", "36π", "9π", "6π", "12π", "1", "", "", ""])
        writer.writerow([3, 12, "Negative numbers", 102, "Integers", "C", "-2 × -3 = ?", "-6", "-5", "6", "5", "2", "", "", "2"])


def _bench_vault(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    return paths, load_vault(paths.root), repository


QWEN = "qwen/qwen3-embedding-8b"


def _harness(vault, tmp_path, *, out="o1", writer=None, views=("raw", "hypothesis"), dry_run=False,
             writer_output_tokens=None, embedder=None, caps=None, **kwargs):
    register_suites(compare.SUITES, role_tasks=pf_calls.ROLE_TASKS)
    request = compare.CompareRequest(
        suite="b1", output_dir=tmp_path / out, benchmark_dir=tmp_path / "eedi", models=(QWEN,), dims=(16,),
        views=views, dry_run=dry_run, writer_output_tokens=writer_output_tokens,
    )
    caps = caps or SpendCaps(max_candidates=200, max_pairs=10, max_retries=10, max_calls=200,
                             max_total_tokens=2_000_000, max_estimated_usd=1.0)
    clients = {B1_WRITER_ROLE: writer} if writer is not None else None
    return compare.run_compare(vault, request=request, caps=caps, clients=clients,
                               embedding_clients={QWEN: embedder or FakeEmbeddingClient(dims=16)}, **kwargs)


def _openrouter_writer(paths, *, effort="low"):
    """Point the diagnosis route (B1's writer) at a metered OpenRouter profile."""

    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    head, marker, tail = text.partition("[ai.routing]\n")
    text = head + marker + 'diagnosis = "b1_writer"\n' + tail
    text += (
        '\n[ai.providers.b1_writer]\ntype = "openrouter"\nmodel = "openai/gpt-6-luna"\n'
        'api_key_env = "OPENROUTER_API_KEY"\nresponse_format = "json_object"\n'
        + (f'reasoning_effort = "{effort}"\n' if effort else "")
    )
    (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")
    return load_vault(paths.root)


def _completion(content, *, finish_reason="stop", prompt_tokens=120, completion_tokens=30, cost=0.0002):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(finish_reason=finish_reason, message=types.SimpleNamespace(content=content))],
        usage={"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "cost": cost},
        model="openai/gpt-6-luna-20261001",
    )


def _hypothesis_json(text="Adds the numerators and adds the denominators."):
    return json.dumps({"misconception": text})
