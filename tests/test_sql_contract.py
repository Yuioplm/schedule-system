from __future__ import annotations

import sqlite3


def _insert_base_slot(conn: sqlite3.Connection, date_text: str) -> None:
    conn.execute(
        """
        INSERT INTO M_Date (DateID, CalendarDate, DayOfWeek, WeekNumber, YearMonth)
        VALUES (1, ?, 1, 1, '2026-04')
        """,
        (date_text,),
    )
    conn.execute(
        """
        INSERT INTO T_ConsultationSlot (
            SlotID, Rpt1ClinDeptID, Rpt1SpecialtyID, Rpt1DisplayDoctorName,
            Rpt2ClinDeptID, Rpt3ClinDeptID, Rpt4ClinDeptID, Rpt5ClinDeptID, Rpt6ClinDeptID,
            DoctorID, TimeSlotID, Room, DayOfWeek, WeekPattern, StartDate, EndDate, ActiveFlag
        )
        VALUES (1, 1, 1, '医師A', 1, 1, 1, 1, 1, 1, 1, '101', 1, '12345', '2026-04-01', '2026-04-30', 1)
        """
    )


def test_v_schedule_actual_uses_latest_active_change(db_conn: sqlite3.Connection) -> None:
    _insert_base_slot(db_conn, "2026-04-06")

    db_conn.execute(
        """
        INSERT INTO T_ScheduleChange (
            ChangeID, CalendarDate, SlotID, ChangeTypeID, NewDoctorID, NewTimeSlotID, NewRoom, ActiveFlag
        ) VALUES (1, '2026-04-06', 1, 2, 2, 2, '201', 1)
        """
    )
    db_conn.execute(
        """
        INSERT INTO T_ScheduleChange (
            ChangeID, CalendarDate, SlotID, ChangeTypeID, NewDoctorID, NewTimeSlotID, NewRoom, ActiveFlag
        ) VALUES (2, '2026-04-06', 1, 2, 3, 1, '301', 1)
        """
    )

    row = db_conn.execute(
        """
        SELECT DoctorID, TimeSlotID, Room
        FROM V_ScheduleActual
        WHERE CalendarDate = '2026-04-06' AND SlotID = 1
        """
    ).fetchone()

    assert row == (3, 1, "301")


def test_v_schedule_actual_excludes_canceled_slot(db_conn: sqlite3.Connection) -> None:
    _insert_base_slot(db_conn, "2026-04-13")

    db_conn.execute(
        """
        INSERT INTO T_ScheduleChange (
            ChangeID, CalendarDate, SlotID, ChangeTypeID, ActiveFlag
        ) VALUES (10, '2026-04-13', 1, 1, 1)
        """
    )

    count = db_conn.execute(
        """
        SELECT COUNT(*)
        FROM V_ScheduleActual
        WHERE CalendarDate = '2026-04-13' AND SlotID = 1
        """
    ).fetchone()[0]

    assert count == 0


def test_v_schedule_actual_includes_active_temporary_schedule(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        """
        INSERT INTO T_TemporarySchedule (
            TempID, CalendarDate, TimeSlotID,
            Rpt1ClinDeptID, Rpt1SpecialtyID, Rpt1DisplayDoctorName,
            Rpt2ClinDeptID, Rpt3ClinDeptID, Rpt4ClinDeptID, Rpt5ClinDeptID, Rpt6ClinDeptID,
            DoctorID, Room, ChangeDetail, Reason, ActiveFlag, Rpt2Flag
        ) VALUES (
            1, '2026-04-20', 1,
            1, 1, '臨時医師',
            1, 1, 1, 1, 1,
            2, '501', '応援', '臨時対応', 1, 1
        )
        """
    )

    row = db_conn.execute(
        """
        SELECT SlotID, DoctorID, Room
        FROM V_ScheduleActual
        WHERE CalendarDate = '2026-04-20' AND SlotID IS NULL
        """
    ).fetchone()

    assert row == (None, 2, "501")
