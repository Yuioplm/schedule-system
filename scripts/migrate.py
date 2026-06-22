from settings import DB_PATH
import sqlite3


def migrate_v_schedule_actual(conn: sqlite3.Connection) -> None:
    view_sql_row = conn.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'view' AND name = 'V_ScheduleActual'
        """
    ).fetchone()
    if view_sql_row is None or view_sql_row[0] is None:
        return

    view_sql = view_sql_row[0]
    legacy_filter = "COALESCE(CAST(ts.Rpt2Flag AS INTEGER), 1) = 1"
    if legacy_filter not in view_sql:
        return

    updated_view_sql = view_sql.replace(f"\n  AND {legacy_filter}", "")
    conn.execute("DROP VIEW IF EXISTS V_ScheduleActual")
    conn.execute(updated_view_sql)


def ensure_temporary_schedule_columns(conn: sqlite3.Connection) -> None:
    temp_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(T_TemporarySchedule)").fetchall()
    }
    if "Rpt2Flag" not in temp_columns:
        conn.execute("ALTER TABLE T_TemporarySchedule ADD COLUMN Rpt2Flag INTEGER DEFAULT 1")


def ensure_output_history_table(conn: sqlite3.Connection) -> None:
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


def ensure_report2_output_history_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS T_Report2OutputHistory (
            OutputHistoryID INTEGER PRIMARY KEY,
            OutputMode TEXT NOT NULL,
            OutputStatus TEXT NOT NULL DEFAULT 'active',
            StartDate DATE NOT NULL,
            OutputBy TEXT,
            OutputDate DATE,
            FileName TEXT,
            RecordCount INTEGER DEFAULT 0,
            CreatedAt DATETIME DEFAULT (datetime('now', '+9 hours')),
            CancelledAt DATETIME,
            CancelledBy TEXT,
            CancelReason TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS T_Report2OutputHistoryDetail (
            OutputDetailID INTEGER PRIMARY KEY,
            OutputHistoryID INTEGER NOT NULL,
            DiffKey TEXT NOT NULL,
            TargetType TEXT NOT NULL,
            TargetID INTEGER NOT NULL,
            RowHash TEXT NOT NULL,
            DiffStatus TEXT,
            ReportDate DATE,
            Weekday TEXT,
            TimeSlot TEXT,
            ClinicalDepartmentName TEXT,
            BeforeDoctorName TEXT,
            ChangeDetail TEXT,
            Reason TEXT,
            CreatedAt DATETIME DEFAULT (datetime('now', '+9 hours')),
            FOREIGN KEY (OutputHistoryID)
                REFERENCES T_Report2OutputHistory(OutputHistoryID)
        )
        """
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        migrate_v_schedule_actual(conn)
        ensure_temporary_schedule_columns(conn)
        ensure_output_history_table(conn)
        ensure_report2_output_history_tables(conn)
        conn.commit()
    finally:
        conn.close()

    print("Migration completed")


if __name__ == "__main__":
    main()
