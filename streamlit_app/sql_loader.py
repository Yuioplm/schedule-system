from pathlib import Path


def load_sql(filename: str) -> str:
    base_dir = Path(__file__).resolve().parents[1]
    sql_path = base_dir / "sql" / filename
    return sql_path.read_text(encoding="utf-8")
