from pathlib import Path
import sqlite3
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
CSV_DIR = BASE_DIR / "csv"
SQL_DIR = BASE_DIR / "sql"

DB_PATH = DATABASE_DIR / "schedule.db"

# Ensure runtime directories exist even on a fresh clone.
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

def get_conn():
    return sqlite3.connect(DB_PATH)


@contextmanager
def get_conn_context():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
