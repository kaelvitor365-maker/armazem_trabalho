import sqlite3

def start_database(dest_path: str, src_path: str) -> sqlite3.Connection:

    conn = sqlite3.connect(dest_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    curr = conn.cursor()

    with open(src_path, "r", encoding="utf-8") as arq:
        curr.executescript(arq.read())

    conn.commit()

    return conn