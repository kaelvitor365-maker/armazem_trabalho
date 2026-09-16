# Database: Guia de Uso

Esta camada implementa um mini-ORM para o SQLite, inspirado no estilo do Prisma Client: em vez de escrever SQL manualmente em todo lugar, você usa objetos Python (`Client`, `Model`, `Columns`) que geram o SQL por trás dos panos.

## Visão geral da arquitetura

```
config_database.py   → cria/abre o arquivo .db a partir do schema.sql
data_functions/
  atomic_data.py      → classe Database: wrapper fino sobre sqlite3 (execute, fetchall, commit...)
model.py              → classes Model (CRUD genérico) e Columns (condições de busca/join)
client.py             → classe Client: agrupa um Model por tabela
```

O fluxo de dependência é:

```
Client → Model → Database → sqlite3.Connection
```

Cada camada só conhece a camada logo abaixo dela. Isso é o que torna possível trocar o SQLite por outro banco no futuro (ver a seção final).

---

## 1. Inicializando o banco

```python
from database import default_database, Client

conn = default_database()      # cria/abre armazem.db a partir de schema.sql
client = Client()               # já cria a própria conexão internamente
```

`Client.__init__` já chama `default_database()` por conta própria, então na prática basta:

```python
from database import Client

client = Client()
```

Isso te dá acesso a:

```python
client.users
client.produtos
client.tipo_produtos
client.armazem
```

Cada um desses é uma instância de `Model`, já ligada à tabela correspondente.

---

## 2. CRUD básico

### Create

```python
id_user = client.users.create({
    "username": "vitor",
    "token": "abc123"
})
# id_user é um int (o id do registro recém-criado)
```

### Find (leitura)

```python
from database import Columns

# todos os registros
todos = client.produtos.find_all()

# um registro específico
produto = client.produtos.find_one(where=[Columns("id") == 1])

# vários, com filtro
caros = client.produtos.find_many(where=[Columns("price") > 100])

# só algumas colunas
nomes = client.produtos.find_many(columns={"name_produto"})
```

`find_many` sem nenhum argumento retorna tudo. `find_all()` é só um atalho pra isso quando você não precisa de filtro nem de colunas específicas.

### Update

```python
linhas_afetadas = client.armazem.update(
    data={"quantidade": 50},
    where=[Columns("id") == 1]
)
```

### Delete

```python
linhas_apagadas = client.produtos.delete(where=[Columns("id") == 1])
```

Todos os métodos de escrita (`create`, `update`, `delete`) retornam `int`, seja o `id` criado ou o número de linhas afetadas.

---

## 3. `Columns`: construindo condições

`Columns` sobrecarrega os operadores de comparação do Python para gerar condições SQL, sem você escrever SQL na mão:

```python
Columns("quantidade") == 0
Columns("quantidade") > 0
Columns("quantidade") >= 0
Columns("quantidade") < 100
Columns("quantidade") <= 100
Columns("username") != "vitor"
```

Cada uma dessas expressões retorna um objeto `Columns` pronto para entrar numa lista `where=[...]`. Múltiplas condições na lista são combinadas com `AND`:

```python
client.produtos.find_many(where=[
    Columns("price") > 100,
    Columns("id_user") == 1
])
# WHERE price > ? AND id_user = ?
```

### Forma alternativa: sem sobrecarga, direto no construtor

Se preferir não usar os operadores sobrecarregados, é possível passar o valor e o operador diretamente na criação do `Columns`, com o mesmo resultado:

```python
Columns("price", 100, ">")           # equivalente a Columns("price") > 100
Columns("id_user", 1, "=")           # equivalente a Columns("id_user") == 1
```

As duas formas produzem exatamente a mesma condição, então é só questão de preferência de estilo.

> **Não existe suporte a `OR`.** Foi uma decisão deliberada: o projeto é pequeno e as buscas reais são quase todas por `id`, então a complexidade de suportar `OR`/`NOT` genérico (o que exigiria sobrecarregar `&`, `|`, `~` e montar uma árvore de expressões) não se paga. Se precisar de um "OR" pontual (ex: buscar por uma lista de ids), resolva com um método dedicado usando `IN (...)`.

### Erro comum: esquecer de aplicar uma comparação

```python
Columns("id")  # criado, mas sem == / > / etc aplicado
```

Se você passar isso dentro de `where` sem nunca ter comparado com algo, o `Model` detecta e lança um erro claro:

```
ValueError: A(S) COLUNA(S) id NECESSITAM DE UM OPERADOR
```

---

## 4. `includes`: fazendo joins

Para trazer dados de tabelas relacionadas numa única consulta, use o parâmetro `includes`. Ele espera um dicionário com três chaves: `tables`, `join` e `on`.

### Sintaxe

```python
client.armazem.find_many(
    columns={"quantidade", "produtos.name_produto", "tipo_produtos.typename"},
    includes={
        "tables": ["produtos", "tipo_produtos"],
        "join": ["inner", "inner"],
        "on": [
            Columns("id_produto") == Columns("produtos.id"),
            Columns("id_tipo_produto") == Columns("tipo_produtos.id")
        ]
    }
)
```

### Regras de como isso é interpretado

- **`tables`**: lista de tabelas que vão entrar no `JOIN`.
- **`join`**: o tipo de cada `JOIN`, na mesma ordem de `on`. Valores aceitos: `"inner"`, `"left"`, `"right"`, `"full"` (os dois últimos exigem SQLite 3.39+).
- **`on`**: uma condição `Columns(...) == Columns(...)` por junção. As duas listas (`join` e `on`) precisam ter o mesmo tamanho, já que cada posição `i` forma um `JOIN` completo.
- **Nomes de coluna sem ponto (`.`) são sempre assumidos como sendo da tabela principal** (a tabela do `Model` que você chamou, ex: `armazem`). Só escreva o prefixo quando a coluna for de uma tabela incluída:

  ```python
  Columns("id_produto")            # vira armazem.id_produto (implícito)
  Columns("produtos.id")           # fica como está (explícito)
  ```

  Essa mesma regra vale para `columns`: se você pedir `columns={"quantidade"}` sem include, é sempre a coluna da tabela principal. **Dentro de um `includes`, se quiser trazer colunas de tabelas relacionadas, use o nome qualificado** (`"produtos.name_produto"`).

- **Toda tabela referenciada em `on` precisa também aparecer em `tables`.** Se você esquecer de declarar, o erro avisa exatamente qual tabela falta:

  ```
  ValueError: PRECISA ADICIONAR A(S) TABELA(S): produtos
  ```

### Sobre `columns=None` junto com `includes`

Se você não especificar `columns` ao usar `includes`, o SQL gerado usa `SELECT *`. Como tabelas diferentes têm colunas com nomes repetidos (`id` existe em várias tabelas), isso pode causar **perda silenciosa de dados** ao converter o resultado para dicionário (a última coluna com aquele nome "vence"). **Recomendação:** sempre que usar `includes`, declare `columns` explicitamente com os nomes qualificados que você realmente precisa.

### `where` combinado com `includes`

Funciona normalmente, mas lembre-se: sem prefixo, a coluna é sempre da tabela principal.

```python
client.armazem.find_many(
    columns={"quantidade", "produtos.name_produto"},
    where=[Columns("quantidade") > 0],
    includes={
        "tables": ["produtos"],
        "join": ["inner"],
        "on": [Columns("id_produto") == Columns("produtos.id")]
    }
)
```

---

## 5. Referência rápida dos métodos de `Model`

| Método | Parâmetros | Retorna |
|---|---|---|
| `create(data: dict)` | dicionário coluna → valor | `int` (id criado) |
| `find_many(columns=, where=, includes=)` | todos opcionais | `list[sqlite3.Row]` |
| `find_all(includes=)` | atalho de `find_many` sem filtro | `list[sqlite3.Row]` |
| `find_one(columns=, where=, includes=)` | todos opcionais | `sqlite3.Row \| None` |
| `update(data: dict, where=)` | `data` obrigatório | `int` (linhas afetadas) |
| `delete(where=)` | opcional (sem `where`, apaga tudo) | `int` (linhas apagadas) |

`sqlite3.Row` se comporta como um dicionário somente-leitura: `linha["coluna"]` funciona, assim como `dict(linha)` para converter de vez.

**Atenção:** `delete()` sem `where` apaga **todas as linhas da tabela**. Não existe uma trava de segurança para isso hoje, então tome cuidado ao chamar sem filtro.

---

## 6. Como usar outro banco de dados (não SQLite)

Toda a camada `Model`/`Client` depende apenas da classe `Database` (em `data_functions/atomic_data.py`), que é a única peça que efetivamente "fala" com o SQLite. Para trocar de banco (PostgreSQL, MySQL, etc.), você precisa criar uma classe alternativa que implemente a **mesma interface pública**, e trocar o que `Client.__init__` instancia.

### A interface que sua classe substituta precisa ter

```python
class MinhaDatabase:
    def execute(self, sql: str, parameters=()) -> "MinhaDatabase":
        """Executa uma query sem controle de transação. Retorna self (para encadear)."""
        ...

    def safe_execute(self, sql: str, parameters=()) -> "MinhaDatabase":
        """Executa uma query com commit/rollback automático. Retorna self."""
        ...

    @property
    def fetchall(self) -> list:
        """Retorna todas as linhas do último SELECT executado."""
        ...

    @property
    def lastrowid(self) -> int:
        """Retorna o id da última linha inserida."""
        ...

    @property
    def rowcount(self) -> int:
        """Retorna quantas linhas foram afetadas pelo último UPDATE/DELETE."""
        ...

    @property
    def commit(self) -> None:
        """Confirma a transação atual."""
        ...

    @property
    def rollback(self) -> None:
        """Desfaz a transação atual."""
        ...
```

Pontos de atenção ao portar para outro banco:

- **Placeholder de parâmetros**: o `Model` sempre usa `?` (estilo SQLite/`qmark`) nas suas queries geradas. Se o driver do banco novo usar outro estilo (ex: `%s` no psycopg2/MySQL, ou `$1` no asyncpg), sua classe `MinhaDatabase` precisa **traduzir** o SQL recebido antes de repassar ao driver, ou então o `Model` precisaria ser ajustado para gerar o placeholder certo, já que hoje isso está fixo como `?` dentro de `model.py`.
- **`PRAGMA foreign_keys = ON`** é específico do SQLite; a maioria dos outros bancos já valida `FOREIGN KEY` por padrão, então essa etapa do `config_database.py` seria removida ou substituída pelo equivalente do banco escolhido.
- **`executescript`** (usado para rodar o `schema.sql` inteiro de uma vez) também é uma API específica do módulo `sqlite3`. Outros drivers normalmente exigem executar os comandos um a um, ou têm seu próprio método equivalente.
- **`Model` não sabe nada sobre SQLite diretamente**, ele só chama `self._conn.safe_execute(...)` e `self._conn.fetchall`. Contanto que sua classe substituta implemente essa interface, o resto do código (`Columns`, `Client`, as rotas) continua funcionando sem alteração.

### Trocando no `Client`

```python
# database/client.py
class Client:
    def __init__(self, conn=None):
        self._conn = conn or Database(default_database())  # troque aqui pela sua classe
        self.users = Model('users', self._conn)
        self.produtos = Model('produtos', self._conn)
        self.tipo_produtos = Model('tipo_produtos', self._conn)
        self.armazem = Model('armazem', self._conn)
        self.log = Model('log', self._conn)
```

Adicionar um parâmetro opcional `conn` no `__init__` (como no exemplo acima) permite injetar qualquer implementação de `Database` de fora, sem precisar editar o `Client` toda vez que trocar de banco.