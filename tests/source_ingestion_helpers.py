"""What other test files use from ``tests/test_source_ingestion.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.content.pipeline.source_ingestion import CaptionCue, NormalizedSource

from tests.structured_ai import StructuredClientFake
from tests.helpers import NOW


class _FakeCanonicalClient(StructuredClientFake):
    def __init__(
        self,
        locator: str | None = None,
        *,
        provider_name: str = "codex",
        model: str | None = None,
    ):
        self.locator = locator
        self.provider_name = provider_name
        self.provider_type = "codex_sdk" if provider_name == "codex" else "openai_chat"
        self.model = model
        self.calls: list[CanonicalIngestContext] = []

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        self.calls.append(context)
        locator = self.locator or context.chunks[0].locator
        return AuthoringProposal.model_validate(_proposal_payload(context, locator))

    def run_authoring_proposal(self, context):  # pragma: no cover - unused in these tests
        raise NotImplementedError

    def run_grading_proposal(self, context):  # pragma: no cover - unused in these tests
        raise NotImplementedError


def _source_file(tmp_path):
    text = " ".join(
        [
            "Singular value decomposition factors a matrix into orthogonal matrices and singular values.",
            "It supports low rank approximation, least squares reasoning, and geometric interpretation.",
            "A useful learner should know the definition, identify the factors, and connect singular values to scale.",
        ]
        * 5
    )
    html = tmp_path / "svd.html"
    html.write_text(
        f"""
        <html>
          <head>
            <title>SVD canonical source</title>
            <link rel="canonical" href="https://example.edu/svd" />
          </head>
          <body>
            <h1>Singular Value Decomposition</h1>
            <p>{text}</p>
          </body>
        </html>
        """,
        encoding="utf-8",
    )
    return html


def _youtube_source(second_caption: str = "and in this chapter we dig into attention.") -> NormalizedSource:
    cues = [
        CaptionCue(0.0, 2.0, "Earlier context."),
        CaptionCue(11.0, 15.5, "Attention is All You Need introduced transformers."),
        CaptionCue(15.5, 19.8, second_caption),
        CaptionCue(19.8, 21.7, "visualizing how it processes data."),
        CaptionCue(22.0, 24.0, "Later context."),
    ]
    lines = ["# YouTube video abc123", ""]
    for cue in cues:
        lines.extend([f"[t={cue.start:.1f}-{cue.end:.1f}] {cue.text}", ""])
    return NormalizedSource(
        kind="youtube_video",
        title="YouTube video abc123",
        authors=[],
        canonical_uri="https://www.youtube.com/watch?v=abc123",
        original_uri="https://www.youtube.com/watch?v=abc123",
        markdown="\n".join(lines).strip() + "\n",
        retrieved_at=NOW,
        captions=cues,
    )


def _proposal_payload(context: CanonicalIngestContext, locator: str) -> dict:
    source_ref_id = context.canonical_source["id"]
    return {
        "summary": "Ingested SVD source.",
        "source_refs": [
            {
                "ref_type": "canonical_source",
                "ref_id": source_ref_id,
                "path": context.canonical_source["path"],
                "locator": locator,
            }
        ],
        "items": [
            {
                "client_item_id": "lo_ingested_svd",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_ingested_svd",
                "source_ref_ids": [source_ref_id],
                "rationale": "Extract the canonical definition.",
                "review_route": "auto_apply",
                "payload": {
                    "title": "Ingested SVD definition",
                    "subjects": [context.target_subject],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "definition",
                    "summary": "SVD factors a matrix into orthogonal matrices and singular values.",
                },
            },
            {
                "client_item_id": "pi_ingested_svd",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_ingested_svd_001",
                "source_ref_ids": [source_ref_id],
                "rationale": "Practice the extracted definition.",
                "review_route": "auto_apply",
                "payload": {
                    "learning_object_id": "lo_ingested_svd",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "What does SVD factorize a matrix into?",
                    "expected_answer": "Orthogonal matrices and singular values.",
                    "evidence_facets": ["recall"],
                    "evidence_weights": {"recall": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names the factors."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }
