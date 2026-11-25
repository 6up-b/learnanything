"""Exact schema additions made by the grade-curve migration for cross-migration diff tests."""

GRADE_CURVE_OBJECTS = {
    "attempt_grade_curves", "sqlite_autoindex_attempt_grade_curves_1", "attempt_grade_curves_no_update",
    "attempt_grade_curves_no_delete", "attempt_grade_curves_no_replace",
}


def forget_captures(repository) -> None:
    """The ledger as code before the capture left it: no curve rows (an owner's history, graded before mvp-0.72's code
    recorded a curve on every grade). Its append-only guard is set aside for the deletion and put back as it was."""

    with repository.connection() as connection:
        (sql,) = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = 'attempt_grade_curves_no_delete'").fetchone()
        connection.execute("DROP TRIGGER attempt_grade_curves_no_delete")
        connection.execute("DELETE FROM attempt_grade_curves")
        connection.execute(sql)
        connection.commit()
