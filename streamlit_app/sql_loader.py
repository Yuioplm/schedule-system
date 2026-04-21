from pathlib import Path
from time import perf_counter

from streamlit_app.logging_config import setup_logger

logger = setup_logger("streamlit_app.sql_loader")
BASE_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = BASE_DIR / "sql"
ALLOWED_SQL_FILES = frozenset(path.name for path in SQL_DIR.glob("*.sql"))


def _validate_filename(filename: str) -> None:
    candidate = Path(filename)
    if candidate.name != filename:
        raise ValueError(f"Invalid SQL filename: {filename}")
    if filename not in ALLOWED_SQL_FILES:
        raise ValueError(f"SQL file is not allowed: {filename}")


def load_sql(filename: str) -> str:
    _validate_filename(filename)
    sql_path = SQL_DIR / filename
    started_at = perf_counter()
    logger.info("load_sql_start filename=%s", filename)
    try:
        content = sql_path.read_text(encoding="utf-8")
        elapsed_ms = int((perf_counter() - started_at) * 1000)
        logger.info("load_sql_success filename=%s elapsed_ms=%s", filename, elapsed_ms)
        return content
    except Exception:
        elapsed_ms = int((perf_counter() - started_at) * 1000)
        logger.exception(
            "load_sql_failed filename=%s path=%s elapsed_ms=%s",
            filename,
            sql_path,
            elapsed_ms,
        )
        raise
