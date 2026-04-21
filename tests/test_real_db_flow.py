from __future__ import annotations

import sqlite3
from pathlib import Path

SQL_DIR = Path("sql")

def _insert_base_slot(conn: sqlite3.Connection, date_text: str, slot_id: int = 1) -> None:
    conn.execute(
        """
        INSERT INTO M_Date (DateID, CalendarDate, DayOfWeek, WeekNumber, YearMonth)
        VALUES (?, ?, 1, 1, '2026-04')
        """,
        (slot_id, date_text),
    )
    conn.execute(
        """
        INSERT INTO T_ConsultationSlot (
            SlotID, Rpt1ClinDeptID, Rpt1SpecialtyID, Rpt1DisplayDoctorName,
            Rpt2ClinDeptID, Rpt3ClinDeptID, Rpt4ClinDeptID, Rpt5ClinDeptID, Rpt6ClinDeptID,
            DoctorID, TimeSlotID, Room, DayOfWeek, WeekPattern, StartDate, EndDate, ActiveFlag
        )
        VALUES (?, 1, 1, '医師A', 1, 1, 1, 1, 1, 1, 1, '101', 1, '12345', '2026-04-01', '2026-04-30', 1)
        """,
        (slot_id,),
    )


def _load_sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


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


def test_file_db_init_migrate_and_core_sqls_run(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_load_sql("create_tables.sql"))
        _seed_master_data(conn)
        _insert_base_slot(conn, "2026-04-06", slot_id=1)
        conn.execute(
            """
            INSERT INTO T_ScheduleChange (
                ChangeID, CalendarDate, SlotID, ChangeTypeID, ChangeDetail, Reason,
                NewDoctorID, NewTimeSlotID, ActiveFlag, Rpt2Flag
            ) VALUES (
                1, '2026-04-06', 1, 2, '担当変更', '備考',
                2, 2, 1, 1
            )
            """
        )
        conn.commit()

        schedule_rows = conn.execute(
            _load_sql("ScheduleSearch_base.sql"),
            ("2026-04-01", "2026-04-30"),
        ).fetchall()
        actual_rows = conn.execute(
            _load_sql("ActualScheduleSearch_base.sql"),
            ("2026-04-01", "2026-04-30"),
        ).fetchall()
        report2_rows = conn.execute(
            _load_sql("Report2.sql"),
            {"start_date": "2026-04-01"},
        ).fetchall()

        assert len(schedule_rows) == 1
        assert len(actual_rows) == 1
        assert len(report2_rows) == 1
    finally:
        conn.close()
