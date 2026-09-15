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
    """
    CRUD genérico para uma tabela do banco, com suporte a filtros (where),
    seleção de colunas (columns) e joins com outras tabelas (includes).

    Cada instância representa uma tabela específica: toda query gerada por
    seus métodos usa self._table como tabela principal.
    """

    def __init__(self, table: str, conn: sql.Connection | Database) -> None:
        """
        Construtor do Model.

        Args:
            table: nome da tabela que este Model vai manipular.
            conn: conexão já pronta (Database) ou uma sqlite3.Connection crua,
                que nesse caso é automaticamente envolvida em um Database.
        """
        self._table = str(table)
        self._conn = conn if isinstance(conn, Database) else Database(conn)

    def find_many(self,
                  columns: typing.Optional[set[str]] = None,
                  where: typing.Optional[list[Columns]] = None,
                  includes: typing.Optional[dict[str, list[str | Columns]]] = None
                  ) -> list[sql.Row]:
        """
        Busca múltiplos registros da tabela, com filtros e joins opcionais.

        Sem "includes", nomes em "columns" e "where" são sempre da tabela
        principal (self._table). Com "includes", colunas sem ponto ("coluna")
        são assumidas como da tabela principal; colunas de tabelas relacionadas
        precisam do prefixo explícito ("tabela.coluna").

        Args:
            columns: colunas a retornar. Se None, retorna todas ("*").
            where: lista de condições (Columns), combinadas sempre com AND.
                Cada Columns precisa ter um operador aplicado (==, >, etc).
            includes: dicionário com as chaves "tables", "join" e "on" para
                montar joins com outras tabelas. "tables" lista as tabelas
                envolvidas, "join" o tipo de cada junção (na mesma ordem de
                "on"), e "on" as condições Columns(...) == Columns(...) que
                definem cada junção.

        Returns:
            Lista de sqlite3.Row com os registros encontrados.

        Raises:
            ValueError: se alguma coluna em "where" não tiver operador aplicado,
                se "includes" estiver incompleto (faltando tables/join/on),
                se "join" e "on" tiverem tamanhos diferentes, se algum tipo de
                join for inválido, se não for possível identificar a tabela de
                uma condição do "on", ou se uma tabela usada no "on" não tiver
                sido declarada em "tables".
        """
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
        """
        Atalho para find_many() sem filtro de colunas nem de where, retornando
        todos os registros da tabela (com joins opcionais).

        Args:
            includes: mesmo formato aceito por find_many().

        Returns:
            Lista de sqlite3.Row com todos os registros encontrados.
        """
        return self.find_many(includes=includes)

    def find_one(self,
                 columns: typing.Optional[set[str]] = None,
                 where: typing.Optional[list[Columns]] = None,
                 includes: typing.Optional[dict[str, list[str | Columns]]] = None
                 ) -> sql.Row | None:
        """
        Busca um único registro, retornando o primeiro resultado encontrado.

        Args:
            columns: mesmo formato aceito por find_many().
            where: mesmo formato aceito por find_many().
            includes: mesmo formato aceito por find_many().

        Returns:
            O primeiro sqlite3.Row encontrado, ou None se nada for encontrado.
        """
        result = self.find_many(columns=columns, where=where, includes=includes)
        return result[0] if result else None

    def create(self, data: dict[str, typing.Any]) -> int:
        """
        Insere um novo registro na tabela.

        Args:
            data: dicionário coluna -> valor a ser inserido.

        Returns:
            O id gerado para o registro recém-criado.

        Raises:
            ValueError: se "data" estiver vazio.
        """
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
        """
        Atualiza registros existentes na tabela.

        Args:
            data: dicionário coluna -> novo valor.
            where: lista de condições (Columns) para filtrar quais registros
                serão atualizados. Sem "where", todos os registros são afetados.

        Returns:
            Quantidade de linhas afetadas pelo update.

        Raises:
            ValueError: se "data" estiver vazio, ou se alguma coluna em "where"
                não tiver operador aplicado.
        """
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
        """
        Remove registros da tabela.

        Args:
            where: lista de condições (Columns) para filtrar quais registros
                serão removidos. Sem "where", todos os registros da tabela
                são apagados.

        Returns:
            Quantidade de linhas removidas.

        Raises:
            ValueError: se alguma coluna em "where" não tiver operador aplicado.
        """
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

    def _where_parameters(self, c: Columns) -> str:
        """
        Monta a condição SQL de uma coluna para uso dentro de um WHERE.

        Se a comparação for contra outra Columns (coluna de outra tabela,
        usado em joins), o valor é escrito literalmente no SQL. Caso
        contrário, usa "?" como placeholder de parâmetro.

        Args:
            c: a condição a ser convertida em texto SQL.

        Returns:
            A condição formatada, pronta para entrar em um WHERE/ON.
        """
        parameters = "?" if not c.is_column else self._qualify(c.value.column)
        return f"{self._qualify(c.column)} {_inv_compare[c.operator]} {parameters}"

    def _alias(self, s: str) -> str:
        """
        Gera o apelido (alias) de uma coluna já qualificada, no formato
        "tabela__coluna", usado para diferenciar colunas de mesmo nome
        vindas de tabelas diferentes num join.

        Args:
            s: coluna já qualificada, no formato "tabela.coluna".

        Returns:
            O alias no formato "tabela__coluna".
        """
        ret = s.split('.')
        return f"{ret[0]}__{ret[1]}"

    def _qualify(self, s: str) -> str:
        """
        Garante que uma coluna esteja qualificada com o nome da tabela.

        Se "s" já contiver um ponto (ex: "produtos.id"), é retornada como
        está. Caso contrário, assume que pertence à tabela principal deste
        Model (self._table).

        Args:
            s: nome da coluna, qualificado ou não.

        Returns:
            A coluna sempre no formato "tabela.coluna".
        """
        return s if "." in s else f"{self._table}.{s}"
