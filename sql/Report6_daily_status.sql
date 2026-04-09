-- ==========================
-- 帳票⑥ 非常勤医師勤務報告書
-- ==========================
WITH part_time_doctor AS (
    SELECT
        DoctorID,
        DoctorName
    FROM M_Doctor
    WHERE EmploymentType = '非常勤'
      AND COALESCE(ActiveFlag, 1) = 1
),
latest_change AS (
    SELECT
        sc.CalendarDate,
        sc.SlotID,
        sc.ChangeTypeID,
        ROW_NUMBER() OVER (
            PARTITION BY sc.CalendarDate, sc.SlotID
            ORDER BY sc.ChangeID DESC
        ) AS rn
    FROM T_ScheduleChange sc
    WHERE COALESCE(sc.ActiveFlag, 1) = 1
),
actual_rows AS (
    SELECT
        sa.CalendarDate,
        sa.DoctorID,
        d.DoctorName,
        ts.TimeSlotName,
        'ACTUAL' AS RowType
    FROM V_ScheduleActual sa
    JOIN part_time_doctor d
      ON sa.DoctorID = d.DoctorID
    LEFT JOIN M_TimeSlot ts
      ON sa.TimeSlotID = ts.TimeSlotID
    WHERE sa.CalendarDate BETWEEN :start_date AND :end_date
),
rest_rows AS (
    SELECT
        sb.CalendarDate,
        sb.DoctorID,
        d.DoctorName,
        ts.TimeSlotName,
        'REST' AS RowType
    FROM V_ScheduleBase sb
    JOIN part_time_doctor d
      ON sb.DoctorID = d.DoctorID
    JOIN latest_change lc
      ON sb.CalendarDate = lc.CalendarDate
     AND sb.SlotID = lc.SlotID
     AND lc.rn = 1
    LEFT JOIN M_TimeSlot ts
      ON sb.TimeSlotID = ts.TimeSlotID
    WHERE sb.CalendarDate BETWEEN :start_date AND :end_date
      AND lc.ChangeTypeID IN (1, 2)
),
temporary_rows AS (
    SELECT
        tsch.CalendarDate,
        tsch.DoctorID,
        d.DoctorName,
        mt.TimeSlotName,
        'TEMP' AS RowType
    FROM T_TemporarySchedule tsch
    JOIN part_time_doctor d
      ON tsch.DoctorID = d.DoctorID
    LEFT JOIN M_TimeSlot mt
      ON tsch.TimeSlotID = mt.TimeSlotID
    WHERE COALESCE(tsch.ActiveFlag, 1) = 1
      AND tsch.CalendarDate BETWEEN :start_date AND :end_date
)
SELECT * FROM actual_rows
UNION ALL
SELECT * FROM rest_rows
UNION ALL
SELECT * FROM temporary_rows
ORDER BY DoctorName, DoctorID, CalendarDate, RowType;
