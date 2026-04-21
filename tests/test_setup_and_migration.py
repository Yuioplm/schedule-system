from __future__ import annotations

import importlib
import importlib.util
import sqlite3
import sys
from pathlib import Path


ROOT_DIR = Path(".").resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCRIPTS_DIR = Path("scripts").resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

migrate = importlib.import_module("migrate")


def _load_set_up_module():
    spec = importlib.util.spec_from_file_location("set_up", Path("set_up.py").resolve())
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_setup_main_runs_expected_scripts_in_order(monkeypatch) -> None:
    set_up = _load_set_up_module()

    called: list[str] = []

    def fake_run(script: str) -> None:
        called.append(script)

    monkeypatch.setattr(set_up, "run", fake_run)

    set_up.main()

    assert called == [
        "scripts/init_db.py",
        "scripts/import_master_csv.py",
        "scripts/generate_date_master.py",
        "scripts/generate_holiday_master.py",
        "scripts/import_consultation_slot.py",
        "scripts/fix_date_format.py",
        "scripts/migrate.py",
    ]


def test_migrate_adds_temporary_schedule_rpt2flag_column() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE T_TemporarySchedule (TempID INTEGER PRIMARY KEY)")

        migrate.ensure_temporary_schedule_columns(conn)

        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(T_TemporarySchedule)").fetchall()
        }
        assert "Rpt2Flag" in columns
    finally:
        conn.close()


def test_migrate_creates_change_notice_output_history_table() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        migrate.ensure_output_history_table(conn)

        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'T_ChangeNoticeOutputHistory'
            """
        ).fetchone()

        assert row is not None
    finally:
        conn.close()


def test_migrate_rewrites_legacy_v_schedule_actual_filter() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            """
            CREATE VIEW V_ScheduleActual AS
            SELECT 1 AS x
            WHERE 1 = 1
  AND COALESCE(CAST(ts.Rpt2Flag AS INTEGER), 1) = 1
            """
        )

        migrate.migrate_v_schedule_actual(conn)

        sql = conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'view' AND name = 'V_ScheduleActual'
            """
        ).fetchone()[0]

        assert "COALESCE(CAST(ts.Rpt2Flag AS INTEGER), 1) = 1" not in sql
    finally:
        conn.close()
