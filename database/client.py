import data_functions as data
import sqlite3, typing
from .config_database import start_database

JOIN_TYPES = {"inner": "INNER JOIN", "left": "LEFT JOIN"}

class Model:
    def __init__(self, conn: data.Database, table: str) -> None:
        self._conn = conn
        self._table = str(table)

    def create(self, **dados: typing.Any):
        column = ", ".join(dados.keys())
        placeholders = ", ".join("?" for _ in dados)
        valores = tuple(dados.values())

        self._conn.auto_execute(
            f"INSERT INTO {self._table} ({column}) VALUES ({placeholders})",
            valores
        )

        return self.find_one(id=self._conn.lastrowid())

    def _find_many_includes(self, includes: dict, filtros: dict):
        join_type = JOIN_TYPES.get(includes.get("type", "inner"), "INNER JOIN")
        tabelas = includes["tables"]

        colunas_principais = self._colunas_da_tabela(self._table)
        select_parts = [f"{self._table}.{c} AS {self._table}__{c}" for c in colunas_principais]


        joins_sql = []
        for tabela_relacionada, coluna_local in tabelas.items():
            colunas_relacionadas = self._colunas_da_tabela(tabela_relacionada)
            select_parts += [
                f"{tabela_relacionada}.{c} AS {tabela_relacionada}__{c}"
                for c in colunas_relacionadas
            ]
            joins_sql.append(
                f"{join_type} {tabela_relacionada} "
                f"ON {self._table}.{coluna_local} = {tabela_relacionada}.id"
            )

        select_clause = ", ".join(select_parts)
        join_clause = " ".join(joins_sql)

        sql = f"SELECT {select_clause} FROM {self._table} {join_clause}"
        valores = ()
        if filtros:
            condicoes = " AND ".join(f"{self._table}.{k} = ?" for k in filtros)
            sql += f" WHERE {condicoes}"
            valores = tuple(filtros.values())

        self._conn.execute(sql, valores)
        linhas = self._conn.fetchall()


        resultado = []
        for linha in linhas:
            linha_dict = dict(linha)
            item = {}
            relacionados = {t: {} for t in tabelas}

            for chave, valor in linha_dict.items():
                prefixo, _, coluna = chave.partition("__")
                if prefixo == self._table:
                    item[coluna] = valor
                elif prefixo in relacionados:
                    relacionados[prefixo][coluna] = valor

            item.update(relacionados)
            resultado.append(item)

        return resultado


    def find_many(self, column: set = "*", includes: dict = None, **filtros: typing.Any):
        if includes:
            return self._find_many_includes(includes, filtros)

        column_sql = ", ".join(c for c in column)
        if filtros:
            conditions = " AND ".join(f"{k} = ?" for k in filtros)
            self._conn.execute(
                f"SELECT {column_sql} FROM {self._table} WHERE {conditions}",
                tuple(filtros.values())
            )
        else:
            self._conn.execute(f"SELECT {column_sql} FROM {self._table}")

        return [dict(linha) for linha in self._conn.fetchall()]


    def find_one(self, columns: set = "*", includes: dict = None, **filtros: typing.Any):
        resultados = self.find_many(column=columns, includes=includes, **filtros)
        return resultados[0] if resultados else None
        
    def commit(self) -> None:
        self._conn.commit()

    def update(self,where: dict[str, typing.Any] , **dados: typing.Any) -> int:
        set_clause = ", ".join(f"{k} = ?" for k in dados)
        v_clause = tuple(dados.values())

        where_clause = " AND ".join(f"{k} = ?" for k in where.keys())
        v_where = tuple(where.values())

        self._conn.auto_execute(
            f"UPDATE {self._table} SET {set_clause} WHERE {where_clause}",
            v_clause + v_where
        )

        return self._conn.rowcount()

    def delete(self, **filtros: typing.Any) -> int:
        clause = " AND ".join(f"{k} = ?" for k in filtros)
        self._conn.auto_execute(
            f"DELETE FROM {self._table} WHERE {clause}",
            tuple(filtros.values())
        )

        return self._conn.rowcount()

class DataClient:
    def __init__(self, conn: data.Database):
        self.users = Model(conn, 'users')
        self.tipos_produtos = Model(conn, 'tipos_produtos')
        self.produtos = Model(conn, 'produtos')
        self.armazem = Model(conn, 'armazem')
