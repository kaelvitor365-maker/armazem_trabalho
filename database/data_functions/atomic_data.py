from database.config_database import sqlite3, starting_database, default_database


class Database:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._curr = self._conn.cursor()



    @property
    def rowcount(self) -> int:
        return self._curr.rowcount

    @property
    def fetchall(self) -> list[sqlite3.Row]:
        return self._curr.fetchall()

    @property
    def lastrowid(self) -> int:
        return self._curr.lastrowid

    @property
    def commit(self) -> None:
        self._conn.commit()

    @property
    def rollback(self) -> None:
        self._conn.rollback()

    def execute(self, sql: str, parameters: sqlite3._Parameters = ()) -> "Database":
        self._curr.execute(
            sql,
            parameters
        )
        return self

    def safe_execute(self, sql: str, parameters: sqlite3._Parameters = ()) -> "Database":
        with self._conn as conn:
            conn.execute(
                sql,
                parameters
            )
        return self
    