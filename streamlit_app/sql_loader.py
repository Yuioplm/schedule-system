from pathlib import Path

from streamlit_app.logging_config import setup_logger

logger = setup_logger("streamlit_app.sql_loader")


def load_sql(filename: str) -> str:
    base_dir = Path(__file__).resolve().parents[1]
    sql_path = base_dir / "sql" / filename
    logger.info("load_sql_start filename=%s", filename)
    try:
        content = sql_path.read_text(encoding="utf-8")
        logger.info("load_sql_success filename=%s", filename)
        return content
    except Exception:
        logger.exception("load_sql_failed filename=%s path=%s", filename, sql_path)
        raise
