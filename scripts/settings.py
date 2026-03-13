from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
CSV_DIR = BASE_DIR / "csv"
SQL_DIR = BASE_DIR / "sql"

DB_PATH = DATABASE_DIR / "schedule.db"

def get_conn():
    return sqlite3.connect(DB_PATH)