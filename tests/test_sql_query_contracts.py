from __future__ import annotations

import sqlite3
from pathlib import Path


SQL_DIR = Path("sql")


def _load_sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


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


def _assert_columns(cursor: sqlite3.Cursor, expected_columns: list[str]) -> None:
    actual = [desc[0] for desc in cursor.description]
    assert actual == expected_columns


def test_schedule_search_base_column_and_count_contract(db_conn: sqlite3.Connection) -> None:
    _insert_base_slot(db_conn, "2026-04-06", slot_id=1)

    cursor = db_conn.execute(
        _load_sql("ScheduleSearch_base.sql"),
        ("2026-04-01", "2026-04-30"),
    )
    rows = cursor.fetchall()

    _assert_columns(
        cursor,
        [
            "CalendarDate",
            "DayOfWeek",
            "ClinDeptName",
            "SpecialtyName",
            "TimeSlotName",
            "Room",
            "DoctorName",
            "DisplayDoctorName",
            "SlotID",
        ],
    )
    assert len(rows) == 1


def test_actual_schedule_search_base_column_and_count_contract(db_conn: sqlite3.Connection) -> None:
    _insert_base_slot(db_conn, "2026-04-06", slot_id=1)

    cursor = db_conn.execute(
        _load_sql("ActualScheduleSearch_base.sql"),
        ("2026-04-01", "2026-04-30"),
    )
    rows = cursor.fetchall()

    _assert_columns(
        cursor,
        [
            "日付",
            "曜日",
            "時間帯",
            "診療科",
            "専門",
            "診察室",
            "医師",
            "帳票表示名",
            "変更内容",
            "備考",
            "種別",
            "SlotID",
        ],
    )
    assert len(rows) == 1


def test_change_history_search_column_and_count_contract(db_conn: sqlite3.Connection) -> None:
    _insert_base_slot(db_conn, "2026-04-06", slot_id=1)
    db_conn.execute(
        """
        INSERT INTO T_ScheduleChange (
            ChangeID, CalendarDate, SlotID, ChangeTypeID, ChangeDetail, Reason,
            NewDoctorID, NewTimeSlotID, ActiveFlag, Rpt2Flag, ChangedBy, CreatedAt
        ) VALUES (
            1, '2026-04-06', 1, 2, '担当変更', 'テスト理由',
            2, 2, 1, 1, 'tester', '2026-04-01 09:00:00'
        )
        """
    )

    cursor = db_conn.execute(
        _load_sql("ChangeHistory_search.sql"),
        ("2026-04-01", "2026-04-30", "2026-04-01", "2026-04-30", 0),
    )
    rows = cursor.fetchall()

    _assert_columns(
        cursor,
        [
            "登録種別",
            "レコードID",
            "日付",
            "SlotID",
            "時間帯",
            "診療科",
            "医師",
            "変更種別",
            "変更内容",
            "備考",
            "帳票②表示",
            "ActiveFlag",
            "登録者",
            "登録日時",
            "変更種別ID",
            "医師ID",
            "時間帯ID",
            "編集日付",
            "診療科ID",
            "部屋",
            "帳票➁変更前",
            "変更届出力者",
            "変更届出力日",
        ],
    )
    assert len(rows) == 1


def test_report2_column_and_count_contract(db_conn: sqlite3.Connection) -> None:
    _insert_base_slot(db_conn, "2026-04-06", slot_id=1)
    db_conn.execute(
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

    cursor = db_conn.execute(_load_sql("Report2.sql"), {"start_date": "2026-04-01"})
    rows = cursor.fetchall()

    _assert_columns(cursor, ["日付", "曜日", "時間", "診療科名", "変更前医師", "変更内容", "備考"])
    assert len(rows) == 1
