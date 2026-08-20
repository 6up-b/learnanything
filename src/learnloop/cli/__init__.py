from learnloop.cli.app import *  # noqa: F401,F403
from learnloop.cli.config import *  # noqa: F401,F403
from learnloop.cli.claims import *  # noqa: F401,F403
from learnloop.cli.contracts import *  # noqa: F401,F403
from learnloop.cli.goldenpath import *  # noqa: F401,F403
from learnloop.cli.depth import *  # noqa: F401,F403
from learnloop.cli.surfaces import *  # noqa: F401,F403
from learnloop.cli.calibration import *  # noqa: F401,F403
from learnloop.cli.registry import *  # noqa: F401,F403
from learnloop.cli.controller import *  # noqa: F401,F403
from learnloop.cli.grading import *  # noqa: F401,F403
from learnloop.cli.diagnosis import *  # noqa: F401,F403
from learnloop.cli.ingest_batches import *  # noqa: F401,F403
from learnloop.cli.source_set import *  # noqa: F401,F403
from learnloop.cli.clarification import *  # noqa: F401,F403
from learnloop.cli.card import *  # noqa: F401,F403
from learnloop.cli.questions import *  # noqa: F401,F403
from learnloop.cli.exam import *  # noqa: F401,F403
from learnloop.cli.fit import *  # noqa: F401,F403
from learnloop.cli.sim import *  # noqa: F401,F403

app.add_typer(config_app, name="config")
app.add_typer(claims_app, name="claims")
app.add_typer(contracts_app, name="contracts")
app.add_typer(goldenpath_app, name="goldenpath")
app.add_typer(depth_app, name="depth")
app.add_typer(surfaces_app, name="surfaces")
app.add_typer(calibration_app, name="calibration")
app.add_typer(registry_app, name="registry")
app.add_typer(controller_app, name="controller")
app.add_typer(grading_app, name="grading")
app.add_typer(diagnosis_app, name="diagnosis")
app.add_typer(ingest_batches_app, name="ingest-batches")
app.add_typer(source_set_app, name="source-set")
app.add_typer(clarification_app, name="clarification")
app.add_typer(card_app, name="card")
app.add_typer(questions_app, name="questions")
app.add_typer(exam_app, name="exam")
app.add_typer(fit_app, name="fit")
app.add_typer(sim_app, name="sim")

# Preserve the package-level compatibility hooks that callers and tests imported
# from the former monolithic ``learnloop.cli`` module.  Import these last so the
# broad command-module re-exports above cannot replace them with runtime aliases.
from learnloop.cli.app import (  # noqa: E402,F401
    _AsciiSpinner as _AsciiSpinner,
    _client_for_provider as _client_for_provider,
    _parse_mode_mix as _parse_mode_mix,
    _ready_provider_for_task as _ready_provider_for_task,
    _runtime_for_provider as _runtime_for_provider,
)

__all__ = [name for name in globals() if not name.startswith("__")]
