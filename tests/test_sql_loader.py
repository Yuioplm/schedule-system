from __future__ import annotations

import pytest

from streamlit_app.sql_loader import ALLOWED_SQL_FILES, load_sql


def test_load_sql_reads_allowed_file() -> None:
    assert "Report2.sql" in ALLOWED_SQL_FILES
    content = load_sql("Report2.sql")
    assert content.strip()


@pytest.mark.parametrize("filename", ["../sql/Report2.sql", "missing.sql", "subdir/file.sql"])
def test_load_sql_rejects_invalid_filename(filename: str) -> None:
    with pytest.raises(ValueError):
        load_sql(filename)

