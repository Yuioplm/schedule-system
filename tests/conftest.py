from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


def _create_schema(conn: sqlite3.Connection) -> None:
    schema = Path("sql/create_tables.sql").read_text(encoding="utf-8")
    conn.executescript(schema)


def _seed_master_data(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO M_ClinicalDepartment
            (ClinDeptID, Category, ClinDeptName, Rpt2Flag, ActiveFlag)
        VALUES
            (1, '内科系', '内科', 1, 1)
        """
    )
    conn.execute(
        """
        INSERT INTO M_Specialty (SpecialtyID, SpecialtyName, ActiveFlag)
        VALUES (1, '一般', 1)
        """
    )
    conn.execute(
        """
        INSERT INTO M_ReportClinicalDepartment (RptClinDeptID, RptClinDeptName, ActiveFlag)
        VALUES (1, '内科', 1)
        """
    )
    conn.execute("INSERT INTO M_TimeSlot (TimeSlotID, TimeSlotName) VALUES (1, '午前')")
    conn.execute("INSERT INTO M_TimeSlot (TimeSlotID, TimeSlotName) VALUES (2, '午後')")
    conn.execute("INSERT INTO M_Doctor (DoctorID, DoctorName, ActiveFlag) VALUES (1, '医師A', 1)")
    conn.execute("INSERT INTO M_Doctor (DoctorID, DoctorName, ActiveFlag) VALUES (2, '医師B', 1)")
    conn.execute("INSERT INTO M_Doctor (DoctorID, DoctorName, ActiveFlag) VALUES (3, '医師C', 1)")
    conn.execute(
        """
        INSERT INTO M_ScheduleChangeType (ChangeTypeID, ChangeTypeName, IsCancel, ActiveFlag)
        VALUES (1, '取消', 1, 1)
        """
    )
    conn.execute(
        """
        INSERT INTO M_ScheduleChangeType (ChangeTypeID, ChangeTypeName, IsCancel, ActiveFlag)
        VALUES (2, '医師変更', 0, 1)
        """
    )



def _ensure_output_history_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS T_ChangeNoticeOutputHistory (
            OutputHistoryID INTEGER PRIMARY KEY,
            TargetType TEXT NOT NULL,
            TargetID INTEGER NOT NULL,
            OutputBy TEXT,
            OutputDate DATE,
            CreatedAt DATETIME DEFAULT (datetime('now', '+9 hours'))
        )
        """
    )


@pytest.fixture()
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    _create_schema(conn)
    _seed_master_data(conn)
    _ensure_output_history_table(conn)
    yield conn
    conn.close()
