"""Symbol-level guard for the incumbent adapter's one legacy-module exception."""
import ast
import inspect


def test_predictor_mastery_import_is_arithmetic_only():
    from learnloop.field import predictors

    tree = ast.parse(inspect.getsource(predictors))
    allowed = {"MasteryObservation", "initial_mastery_state", "update_mastery"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "learnloop.learner.mastery":
            assert {alias.name for alias in node.names} <= allowed
        if isinstance(node, ast.Import):
            assert not any(
                alias.name in {"sqlite3", "importlib", "learnloop.learner.mastery"}
                for alias in node.names
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"__import__", "exec", "eval", "open"}
