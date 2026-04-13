from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
CSV_DIR = BASE_DIR / "csv"
SQL_DIR = BASE_DIR / "sql"

DB_PATH = DATABASE_DIR / "schedule.db"

# Ensure runtime directories exist even on a fresh clone.
DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def _migrate_v_schedule_actual(conn: sqlite3.Connection) -> None:
    view_sql_row = conn.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'view' AND name = 'V_ScheduleActual'
        """
    ).fetchone()
    if view_sql_row is None or view_sql_row[0] is None:
        return

    view_sql = view_sql_row[0]
    legacy_filter = "COALESCE(CAST(ts.Rpt2Flag AS INTEGER), 1) = 1"
    if legacy_filter not in view_sql:
        return

    updated_view_sql = view_sql.replace(f"\n  AND {legacy_filter}", "")
    conn.execute("DROP VIEW IF EXISTS V_ScheduleActual")
    conn.execute(updated_view_sql)
    conn.commit()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    _migrate_v_schedule_actual(conn)
    return conn
