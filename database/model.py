from data_functions import Database
from .config_database import default_database, starting_database
import typing, sqlite3 as sql

JOIN_TYPES = {"inner": "INNER JOIN", "left": "LEFT JOIN", "right": "RIGHT JOIN", "full": "FULL JOIN"}
_compare = {
    "=": 1 << 0,
    "<>": 1 << 1,
    ">": 1 << 2,
    "<": 1 << 3,
    ">=": 1 << 4,
    "<=": 1 << 5,
}
_inv_compare = { v: s for s, v in _compare.items()}

class Columns:
    def __init__(self,
                column: str,
                value: typing.Optional[typing.Any] = None, 
                operator: typing.Optional[str] = None
                ):
        self.is_column = False
        self.column = str(column)

        if value is None:
            self.value = -1
        else:
            if isinstance(value, Columns): self.is_column = True
            self.value = value

        if operator is None:
            self.operator = 0
            return
        
        self.operator = _compare.get(operator, -1)
        if self.operator == -1:
            raise ValueError(f"NÃO EXISTE O OPERADOR {operator}")
        

    def _operation(self, operator: str, value: typing.Any) -> "Columns":
        self.operator = _compare[operator]
        self.value = value
        self.is_column = isinstance(value, Columns)
        return self
    
    def __eq__(self, value: typing.Any) -> "Columns":
        return self._operation(
            "=",
            value
        )


    def __ne__(self, value: typing.Any) -> "Columns":
        return self._operation(
            "<>",
            value
        )
    
    def __gt__(self, value: typing.Any) -> "Columns":
        return self._operation(
            ">",
            value
        )

    def __ge__(self, value: typing.Any) -> "Columns":
        return self._operation(
            ">=",
            value
        )

    def __lt__(self, value: typing.Any) -> "Columns":
        return self._operation(
            "<",
            value
        )

    def __le__(self, value: typing.Any):
        return self._operation(
            "<=",
            value
        )
    


class Model:
    def __init__(self, table: str, conn: sql.Connection | Database) -> None:
        self._table = str(table)
        self._conn = conn if isinstance(conn, Database) else Database(conn)


    def find_many(self,
                columns: typing.Optional[set[str]] = None,
                where: typing.Optional[list[Columns]] = None,
                includes: typing.Optional[dict[str, list[str | Columns]]] = None
                ) -> list[sql.Row]:

        columns_sql = "*"
        where_sql = ""
        p_where_sql = ()
        join_sql = ""

        if includes is None:
            if where is not None:
                without_op = [c.column for c in where if c.operator == 0]
                if without_op:
                    raise ValueError(f"A(S) COLUNA(S) {', '.join(without_op)} NECESSITAM DE UM OPERADOR")

                where_sql = " WHERE " + " AND ".join(
                    f"{c.column} {_inv_compare[c.operator]} ?" for c in where
                )
                p_where_sql = tuple(c.value for c in where)

            if columns is not None:
                columns_sql = ", ".join(columns)

            return self._conn.safe_execute(
                f"SELECT {columns_sql} FROM {self._table}{where_sql}",
                p_where_sql
            ).fetchall

        tables = includes.get("tables")
        joins = includes.get("join")
        on = includes.get("on")

        if tables is None:
            raise ValueError("É NESCESSARIO O PARAMETRO 'tables' PARA UTILIZAR O INCLUDE")
        if joins is None:
            raise ValueError("É NESCESSARIO O PARAMETRO 'join' PARA UTILIZAR O INCLUDE")
        if on is None:
            raise ValueError("É NESCESSARIO O PARAMETRO 'on' PARA UTILIZAR O INCLUDE")
        if len(on) != len(joins):
            raise ValueError("O PARAMETRO 'join' DEVE TER A MESMA QUANTIDADE DE ITENS DO PARAMETRO 'on'")
        if not all(join in JOIN_TYPES for join in joins):
            raise ValueError(f"PARAMETRO 'join' ERRADO, OS TIPOS PERMITIDOS SÃO: {', '.join(JOIN_TYPES)}")

        if columns is not None:
            columns_sql = ", ".join(
                f"{self._qualify(c)} AS {self._alias(self._qualify(c))}" for c in columns
            )

        if where is not None:
            without_op = [c.column for c in where if c.operator == 0]
            if without_op:
                raise ValueError(f"A(S) COLUNA(S) {', '.join(without_op)} NECESSITAM DE UM OPERADOR")

            where_sql = " WHERE " + " AND ".join(self._where_parameters(c) for c in where)
            p_where_sql = tuple(c.value for c in where if not c.is_column)

        join_parts = []
        tables_on = set()
        p_join_sql = []

        for parameters, join in zip(on, joins):
            left = self._qualify(parameters.column)

            if parameters.is_column:
                right = self._qualify(parameters.value.column)
                table_left = left.split(".")[0]
                table_right = right.split(".")[0]
                join_table = table_right if table_left == self._table else table_left

                join_parts.append(
                    f"{JOIN_TYPES[join]} {join_table} ON {left} {_inv_compare[parameters.operator]} {right}"
                )
                tables_on.update((table_left, table_right))
            else:
                table_left = left.split(".")[0]
                join_table = table_left if table_left != self._table else None

                if join_table is None:
                    raise ValueError(f"NÃO FOI POSSÍVEL IDENTIFICAR A TABELA DO JOIN NA CONDIÇÃO: {left}")

                join_parts.append(
                    f"{JOIN_TYPES[join]} {join_table} ON {left} {_inv_compare[parameters.operator]} ?"
                )
                tables_on.add(table_left)
                p_join_sql.append(parameters.value)

        need_this_table = tables_on - {self._table} - set(tables)
        if need_this_table:
            raise ValueError(f"PRECISA ADICIONAR A(S) TABELA(S): {', '.join(need_this_table)}")

        join_sql = " " + " ".join(join_parts)
        p_where_sql = tuple(p_join_sql) + p_where_sql

        return self._conn.safe_execute(
            f"SELECT {columns_sql} FROM {self._table}{join_sql}{where_sql}",
            p_where_sql
        ).fetchall

    def find_all(self,
                includes: typing.Optional[dict[str, list[str | Columns]]] = None
                ) -> list[sql.Row]:
        return self.find_many(includes=includes)


    def find_one(self,
                columns: typing.Optional[set[str]] = None,
                where: typing.Optional[list[Columns]] = None,
                includes: typing.Optional[dict[str, list[str | Columns]]] = None
                ) -> sql.Row | None:
        result = self.find_many(columns=columns, where=where, includes=includes)
        return result[0] if result else None

    def create(self, data: dict[str, typing.Any]) -> int:
        if not data:
            raise ValueError("O PARAMETRO 'data' NÃO PODE SER VAZIO")

        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())

        self._conn.safe_execute(
            f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})",
            values
        )
        return self._conn.lastrowid


    def update(self,
            data: dict[str, typing.Any],
            where: typing.Optional[list[Columns]] = None
            ) -> int:

        if not data:
            raise ValueError("O PARAMETRO 'data' NÃO PODE SER VAZIO")

        set_sql = ", ".join(f"{col} = ?" for col in data.keys())
        values = list(data.values())

        where_sql = ""
        if where is not None:
            without_op = [c.column for c in where if c.operator == 0]
            if without_op:
                raise ValueError(f"A(S) COLUNA(S) {', '.join(without_op)} NECESSITAM DE UM OPERADOR")

            where_sql = " WHERE " + " AND ".join(
                f"{c.column} {_inv_compare[c.operator]} ?" for c in where
            )
            values.extend(c.value for c in where)

        self._conn.safe_execute(
            f"UPDATE {self._table} SET {set_sql}{where_sql}",
            tuple(values)
        )
        return self._conn.rowcount


    def delete(self,
            where: typing.Optional[list[Columns]] = None
            ) -> int:

        where_sql = ""
        p_where_sql = ()

        if where is not None:
            without_op = [c.column for c in where if c.operator == 0]
            if without_op:
                raise ValueError(f"A(S) COLUNA(S) {', '.join(without_op)} NECESSITAM DE UM OPERADOR")

            where_sql = " WHERE " + " AND ".join(
                f"{c.column} {_inv_compare[c.operator]} ?" for c in where
            )
            p_where_sql = tuple(c.value for c in where)

        self._conn.safe_execute(
            f"DELETE FROM {self._table}{where_sql}",
            p_where_sql
        )
        return self._conn.rowcount

    def _where_parameters(self, c: Columns) -> bool:
        parameters = "?" if not c.is_column else self._qualify(c.value.column)
        return f"{self._qualify(c.column)} {_inv_compare[c.operator]} {parameters}"

    def _alias(self, s: str) -> str:
        ret = s.split('.')
        return f"{ret[0]}__{ret[1]}"
    

    def _qualify(self, s: str) -> str:
        return s if "." in s else f"{self._table}.{s}"

print("")