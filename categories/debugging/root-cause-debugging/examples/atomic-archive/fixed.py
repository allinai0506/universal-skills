"""Synthetic repair: both writes succeed or roll back in one transaction."""
import sqlite3


def archive(db: sqlite3.Connection, archive_id: int, inject_failure: bool = False) -> None:
    with db:
        db.execute("UPDATE archive SET state = 'ARCHIVED' WHERE id = ?", (archive_id,))
        if inject_failure:
            raise RuntimeError("injected interruption before receipt")
        db.execute("INSERT INTO receipt (archive_id) VALUES (?)", (archive_id,))
