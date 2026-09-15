from database.config_database import sqlite3, starting_database, default_database


class Database:
    """
    Wrapper fino sobre sqlite3.Connection/Cursor, expondo apenas o necessário
    para o Model operar (execute, fetchall, commit, rollback, etc).

    Trocar o banco de dados (ex: para PostgreSQL) significa criar uma classe
    alternativa que implemente essa mesma interface pública.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Construtor do Database.

        Args:
            conn: uma conexão sqlite3 já aberta (normalmente vinda de
                starting_database() ou default_database()).
        """
        self._conn = conn
        self._curr = self._conn.cursor()

    @property
    def rowcount(self) -> int:
        """
        Quantidade de linhas afetadas pelo último UPDATE/DELETE executado.
        """
        return self._curr.rowcount

    @property
    def fetchall(self) -> list[sqlite3.Row]:
        """
        Todas as linhas retornadas pelo último SELECT executado.
        """
        return self._curr.fetchall()

    @property
    def lastrowid(self) -> int:
        """
        O id da última linha inserida pelo INSERT mais recente.
        """
        return self._curr.lastrowid

    @property
    def commit(self) -> None:
        """
        Confirma (persiste) a transação atual no banco.
        """
        self._conn.commit()

    @property
    def rollback(self) -> None:
        """
        Desfaz a transação atual, revertendo mudanças não confirmadas.
        """
        self._conn.rollback()

    def execute(self, sql: str, parameters: sqlite3._Parameters = ()) -> "Database":
        """
        Executa uma query sem controle de transação (sem commit automático).

        Args:
            sql: comando SQL a ser executado, com "?" como placeholder de parâmetros.
            parameters: valores a serem inseridos nos placeholders da query.

        Returns:
            A própria instância de Database, permitindo encadear chamadas
            (ex: db.execute(sql).fetchall).
        """
        self._curr.execute(
            sql,
            parameters
        )
        return self

    def safe_execute(self, sql: str, parameters: sqlite3._Parameters = ()) -> "Database":
        """
        Executa uma query com commit automático em caso de sucesso, ou
        rollback automático em caso de erro (via "with self._conn").

        Args:
            sql: comando SQL a ser executado, com "?" como placeholder de parâmetros.
            parameters: valores a serem inseridos nos placeholders da query.

        Returns:
            A própria instância de Database, permitindo encadear chamadas
            (ex: db.safe_execute(sql).fetchall).
        """
        with self._conn:
            self._curr.execute(
                sql,
                parameters
            )
        return self