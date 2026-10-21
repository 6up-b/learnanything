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
from learnloop.cli.data import *  # noqa: F401,F403
from learnloop.cli.embeddings import embeddings_app
from learnloop.cli.project import project_app
from learnloop.cli.diagnose import diagnose_app
from learnloop.cli.field import field_app
from learnloop.cli.families import families_app
from learnloop.cli.contamination import contamination_app
from learnloop.cli.evaluation import eval_app
from learnloop.cli.practice_index import practice_index_app
from learnloop.cli.inbox import inbox_app
from learnloop.cli.placement import placement_app
from learnloop.cli.pf import pf_app
from learnloop.cli.recurrence import recurrence_app
from learnloop.cli.sources import sources_app
from learnloop.cli.ai import ai_app
from learnloop.cli.plan import plan_app
from learnloop.cli.router import router_app
from learnloop.cli.reader import reader_app
from learnloop.cli.gaps import gaps_app
from learnloop.cli.hints import hints_app
from learnloop.cli.facets import facets_app
from learnloop.cli.evsi import evsi_app
from learnloop.cli.decider import decider_app
from learnloop.cli.mcp import mcp_app
from learnloop.cli.ad import ad_app
from learnloop.cli.experiments import experiments_app

app.add_typer(config_app, name="config")
app.add_typer(inbox_app, name="inbox")
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
app.add_typer(embeddings_app, name="embeddings")
app.add_typer(project_app, name="project")
app.add_typer(diagnose_app, name="diagnose")
app.add_typer(field_app, name="field")
app.add_typer(families_app, name="families")
app.add_typer(contamination_app, name="contamination")
app.add_typer(eval_app, name="eval")
app.add_typer(practice_index_app, name="practice-index")
app.add_typer(placement_app, name="placement")
app.add_typer(pf_app, name="pf")
app.add_typer(recurrence_app, name="recurrence")
app.add_typer(sources_app, name="sources")
app.add_typer(plan_app, name="plan")
app.add_typer(ai_app, name="ai")
app.add_typer(router_app, name="router")
app.add_typer(reader_app, name="reader")
app.add_typer(gaps_app, name="gaps")
app.add_typer(hints_app, name="hints")
app.add_typer(decider_app, name="decider")
app.add_typer(facets_app, name="facets")
app.add_typer(evsi_app, name="evsi")
app.add_typer(mcp_app, name="mcp")
app.add_typer(ad_app, name="ad")
app.add_typer(experiments_app, name="experiments")

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
