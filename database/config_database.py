import sqlite3

def starting_database(path: str, dest: str) -> sqlite3.Connection:
    conn = sqlite3.Connection(
        dest
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    curr = conn.cursor()

    curr.executescript(path)

    return conn


default_database = starting_database("schema.sql", "armazem.db")


