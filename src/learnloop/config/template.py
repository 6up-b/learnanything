"""The decision-only configuration template a new vault is written with.

Every other default lives in ``config/schema.py``; ``tests/goldens/effective_defaults.toml`` lists the effective result,
one line per key, so a changed default shows up there in review.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION

#: Where the decision-only template names its ``algorithm_version``.
_ALGORITHM_VERSION_PLACEHOLDER = "@ALGORITHM_VERSION@"

_DEFAULT_CONFIG_TEMPLATE = """schema_version = 2

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "@ALGORITHM_VERSION@"

# AI is optional (manual without it); routes use your ChatGPT plan: learnloop ai signin chatgpt.
# Precedence: explicit flag > LEARNLOOP_AI_PROVIDER > task route > active provider.
# Exception: embeddings use only their own route, never env/active/fallback.
[ai]
active_provider = "chatgpt"
fallback_provider = ""

[ai.providers.chatgpt]
type = "chatgpt_plan"
model = "gpt-5.6-sol"
reasoning_effort = "low"

[ai.providers.openrouter]
type = "openrouter"
model = "deepseek/deepseek-chat"
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"
timeout_seconds = 180
# input_modalities = ["audio", "pdf"]

[ai.providers.openrouter_embedding]
type = "openai_embedding"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
# embedding.model and embedding.dimensions are authoritative for this route.
timeout_seconds = 180

[ai.routing]
grading = "chatgpt_low"
canonical_ingest = "chatgpt_medium"
canonical_ingest_retry = "chatgpt_medium"
authoring = "chatgpt_medium"
tutor_qa = "chatgpt_low"
teach_back = "chatgpt_low"
rung_variant = "chatgpt_low"
animation = "chatgpt_medium"
transcription = ""
video_generation = ""
embedding = "openrouter_embedding"
# project = ""  # project understanding: probe authoring + closed-book check (empty = the grading route)
field_question_classifier = ""

# Embeddings are opt-in: both switches stay off until you enable them.
# Remote embeddings send learner-derived text to OpenRouter and its upstream
# provider, with data_collection=deny. Vectors approximate plaintext: protect
# them like practice attempts in backups/exports/sync; never share across vaults.
[embedding]
enabled = false
backfill_enabled = false
model = "qwen/qwen3-embedding-8b"
dimensions = 4096

[pf]
generation_enabled = false # PF-b publishes only verified items, capped per day

# F1 is offline analysis, not serving. Paid analysis is independently opt-in.
[field]
active_predictor = "mastery_ekf"
legacy_fallback = "exclude"
question_classification_enabled = false
llm_probability_enabled = false

# auto reads with GLM-OCR (a z.ai key in Settings, or glm_ocr.backend = "local"), else Marker, else pypdf
[ingest.pdf]
engine = "auto" # auto | glm_ocr | marker | pypdf | native (send the PDF to the ingest model)

[animation]
renderer = "manim" # manim | video_model (OpenRouter text-to-video, see [ai.routing] video_generation)

# All other policy uses modeled defaults. Inspect it with:
#   learnloop config effective
# Override any modeled key by adding it under the same TOML path.
"""


def default_config_text(algorithm_version: str = LATEST_ALGORITHM_VERSION) -> str:
    """The decision-only template as a vault at ``algorithm_version`` holds it.

    New vaults are written at ``LATEST_ALGORITHM_VERSION``; existing vaults keep
    their version until the owner runs ``learnloop upgrade``, so a successor only
    appends its tag to ``algorithm_versions.SUCCESSOR_CHAIN``.
    """

    return _DEFAULT_CONFIG_TEMPLATE.replace(_ALGORITHM_VERSION_PLACEHOLDER, algorithm_version, 1)


DEFAULT_CONFIG_TEXT = default_config_text()


def write_default_config(path: Path) -> None:
    """Write the decision-only template without replacing an existing file."""

    if path.exists():
        return
    path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")


__all__ = [
    "DEFAULT_CONFIG_TEXT",
    "default_config_text",
    "write_default_config",
]
