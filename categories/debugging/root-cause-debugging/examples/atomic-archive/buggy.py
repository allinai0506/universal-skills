"""Synthetic defect: the state is committed before the receipt exists."""
import sqlite3


def archive(db: sqlite3.Connection, archive_id: int, inject_failure: bool = False) -> None:
    db.execute("UPDATE archive SET state = 'ARCHIVED' WHERE id = ?", (archive_id,))
    db.commit()  # Defect: publishes only half of the required state.
    if inject_failure:
        raise RuntimeError("injected interruption before receipt")
    db.execute("INSERT INTO receipt (archive_id) VALUES (?)", (archive_id,))
    db.commit()
