"""Provider-side repair prompts for malformed structured output."""

from __future__ import annotations

import json

from pydantic import BaseModel

from learnloop.ai.strict_schema import strict_output_schema


def structured_output_repair_prompt(
    text: str,
    model_type: type[BaseModel],
    *,
    reason: str = "",
) -> str:
    """Build the bounded second pass used after wire validation fails."""

    schema = json.dumps(strict_output_schema(model_type), sort_keys=True, ensure_ascii=False)
    encoded_output = json.dumps(text, ensure_ascii=True)
    diagnosis = f"Validator diagnosis of the prior output:\n{reason}\n\n" if reason else ""
    return (
        "Repair the prior model output into one JSON object that validates against "
        "the schema below. Preserve its meaning. Return only JSON. In every JSON "
        "string, escape backslashes (including LaTeX commands) correctly, and replace "
        "any lone Unicode surrogate with the intended Unicode scalar or U+FFFD. Emit "
        "only the fields the schema declares: drop any key it does not list rather "
        "than renaming or inventing one.\n\n"
        f"{diagnosis}"
        f"Schema:\n{schema}\n\nPrior output as a JSON string:\n{encoded_output}"
    )


def structured_output_regeneration_prompt(prompt: str) -> str:
    """Retry a turn whose malformed JSON was rejected inside app-server."""

    return (
        f"{prompt}\n\n"
        "The prior attempt was rejected because its structured output was not valid "
        "JSON. Generate the answer again. In every JSON string, double every literal "
        "backslash used by LaTeX or other prose (for example, emit `\\\\in`, not "
        "`\\in`) and never emit a lone Unicode surrogate."
    )


__all__ = ["structured_output_regeneration_prompt", "structured_output_repair_prompt"]
