from __future__ import annotations

import py_compile
from pathlib import Path


ROOTS = (Path("streamlit_app"), Path("scripts"))


def test_python_sources_are_compilable() -> None:
    py_files = [Path("set_up.py")]
    for root in ROOTS:
        py_files.extend(sorted(root.rglob("*.py")))

    for path in py_files:
        py_compile.compile(str(path), doraise=True)



def test_critical_sql_files_exist_and_non_empty() -> None:
    critical_sql = [
        "create_tables.sql",
        "ScheduleSearch_base.sql",
        "ActualScheduleSearch_base.sql",
        "ChangeHistory_search.sql",
        "Report2.sql",
    ]

    for file_name in critical_sql:
        sql_path = Path("sql") / file_name
        assert sql_path.exists(), f"Missing SQL file: {file_name}"
        assert sql_path.read_text(encoding="utf-8").strip(), f"Empty SQL file: {file_name}"
