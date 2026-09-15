import sqlite3
from pathlib import Path


def starting_database(schema_path: str | Path, db_path: str | Path) -> sqlite3.Connection:
    """
    Cria (ou sobrescreve) o banco de dados a partir do schema SQL.
    """
    schema_path = Path(schema_path)
    db_path = Path(db_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Arquivo de schema não encontrado: {schema_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.commit()
    return conn


def default_database() -> sqlite3.Connection:
    return starting_database("schema.sql", "armazem.db")