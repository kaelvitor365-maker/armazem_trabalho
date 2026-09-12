import database.config_database as config, typing

class Database:

    def __init__(self, conn: config.sqlite3.Connection) -> None:
        self._conn = conn
        self._curr = conn.cursor()

    def execute(self, sql: str, parametrers: config.sqlite3._Parameters = ()) -> "Database":
        self._curr.execute(
            sql,
            parametrers
        )
        return self

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def auto_execute(self, sql: str, parametrers: config.sqlite3._Parameters = ()) ->"Database":
        self._curr.execute(
            sql,
            parametrers
        )
        self._conn.commit()
        return self

    def lastrowid(self):
        return self._curr.lastrowid

    def fetchall(self) -> typing.Iterable[dict[str, typing.Any]]:
        return self._curr.fetchall()