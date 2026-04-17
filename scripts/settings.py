from pathlib import Path
import sqlite3
from contextlib import contextmanager
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
CSV_DIR = BASE_DIR / "csv"
SQL_DIR = BASE_DIR / "sql"

DB_PATH = DATABASE_DIR / "schedule.db"

# 日付/祝日マスタを生成する会計年度（開始年～終了年）
# 例: START_FISCAL_YEAR=2025, END_FISCAL_YEAR=2030 の場合
# 2025-04-01 ～ 2031-03-31 を対象にする。
def _int_from_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


START_FISCAL_YEAR = _int_from_env("START_FISCAL_YEAR", 2025)
END_FISCAL_YEAR = _int_from_env("END_FISCAL_YEAR", 2030)

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


def fiscal_year_date_range(start_fiscal_year: int = START_FISCAL_YEAR, end_fiscal_year: int = END_FISCAL_YEAR):
    start_date = f"{start_fiscal_year}-04-01"
    end_date = f"{end_fiscal_year + 1}-03-31"
    return start_date, end_date


def get_available_years(default_start: int = START_FISCAL_YEAR, default_end: int = END_FISCAL_YEAR):
    """
    帳票の年プルダウン用に、M_Date の実データから利用可能年を返す。
    M_Date が未生成の場合は設定値を返す。
    """
    with get_conn_context() as conn:
        cur = conn.execute("""
            SELECT DISTINCT CAST(strftime('%Y', CalendarDate) AS INTEGER) AS y
            FROM M_Date
            WHERE CalendarDate IS NOT NULL
            ORDER BY y
        """)
        years = [row[0] for row in cur.fetchall() if row[0] is not None]

    if years:
        return years
    return list(range(default_start, default_end + 2))
