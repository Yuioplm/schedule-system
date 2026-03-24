-- ==========================================
-- 帳票① 外来担当医表（ピボット後）
-- パラメータ: :target_month (YYYY-MM)
-- ==========================================
WITH month_dates AS (
    SELECT
        d.CalendarDate,
        d.DayOfWeek,
        CAST(((CAST(strftime('%d', d.CalendarDate) AS INTEGER) - 1) / 7) + 1 AS INTEGER) AS WeekNumber,
        d.YearMonth
    FROM M_Date d
    LEFT JOIN M_Holiday h
      ON h.HolidayDate = d.CalendarDate
    WHERE d.YearMonth = :target_month
      AND d.DayOfWeek BETWEEN 1 AND 6
      AND h.HolidayDate IS NULL
),
matched_dates AS (
    SELECT
        md.YearMonth,
        md.DayOfWeek,
        md.WeekNumber,
        cs.SlotID,
        cs.Rpt1ClinDeptID,
        cs.Rpt1DisplayDoctorName,
        cs.DoctorID,
        cs.TimeSlotID,
        cs.Room,
        cs.WeekPattern AS SourceWeekPattern
    FROM month_dates md
    JOIN T_ConsultationSlot cs
      ON cs.DayOfWeek = md.DayOfWeek
     AND md.CalendarDate BETWEEN cs.StartDate AND cs.EndDate
     AND instr(cs.WeekPattern, CAST(md.WeekNumber AS TEXT)) > 0
     AND cs.ActiveFlag = 1
),
slot_week_pattern AS (
    SELECT
        YearMonth,
        SlotID,
        Rpt1ClinDeptID,
        Rpt1DisplayDoctorName,
        DoctorID,
        TimeSlotID,
        Room,
        DayOfWeek,
        SourceWeekPattern,
        (
            CASE WHEN MAX(CASE WHEN WeekNumber = 1 THEN 1 ELSE 0 END) = 1 THEN '1' ELSE '' END ||
            CASE WHEN MAX(CASE WHEN WeekNumber = 2 THEN 1 ELSE 0 END) = 1 THEN '2' ELSE '' END ||
            CASE WHEN MAX(CASE WHEN WeekNumber = 3 THEN 1 ELSE 0 END) = 1 THEN '3' ELSE '' END ||
            CASE WHEN MAX(CASE WHEN WeekNumber = 4 THEN 1 ELSE 0 END) = 1 THEN '4' ELSE '' END ||
            CASE WHEN MAX(CASE WHEN WeekNumber = 5 THEN 1 ELSE 0 END) = 1 THEN '5' ELSE '' END
        ) AS ActiveWeekPattern
    FROM matched_dates
    GROUP BY
        YearMonth,
        SlotID,
        Rpt1ClinDeptID,
        Rpt1DisplayDoctorName,
        DoctorID,
        TimeSlotID,
        Room,
        DayOfWeek,
        SourceWeekPattern
),
cell_tokens AS (
    SELECT
        s.YearMonth,
        cd.ClinDeptName,
        ts.TimeSlotName,
        s.Room,
        s.DayOfWeek,
        s.SourceWeekPattern,
        CASE
            WHEN s.SourceWeekPattern = '12345' THEN ''
            ELSE RTRIM(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(s.ActiveWeekPattern, '1', '1・'),
                            '2', '2・'),
                        '3', '3・'),
                    '4', '4・'),
                '5', '5・')
            , '・')
        END AS WeekLabel,
        COALESCE(NULLIF(s.Rpt1DisplayDoctorName, ''), d.DoctorName, '―') AS DoctorName
    FROM slot_week_pattern s
    LEFT JOIN M_ClinicalDepartment cd
      ON cd.ClinDeptID = s.Rpt1ClinDeptID
    LEFT JOIN M_TimeSlot ts
      ON ts.TimeSlotID = s.TimeSlotID
    LEFT JOIN M_Doctor d
      ON d.DoctorID = s.DoctorID
),
cell_tokens_distinct AS (
    SELECT DISTINCT
        YearMonth,
        ClinDeptName,
        TimeSlotName,
        Room,
        DayOfWeek,
        SourceWeekPattern,
        WeekLabel,
        DoctorName
    FROM cell_tokens
),
src AS (
    SELECT
        YearMonth,
        ClinDeptName,
        TimeSlotName,
        Room,
        DayOfWeek,
        GROUP_CONCAT(
            CASE
                WHEN WeekLabel = '' THEN DoctorName
                ELSE WeekLabel || ' ' || DoctorName
            END,
            CHAR(10)
        ) AS CellText
    FROM cell_tokens_distinct
    GROUP BY
        YearMonth,
        ClinDeptName,
        TimeSlotName,
        Room,
        DayOfWeek
)
SELECT
    YearMonth,
    ClinDeptName,
    TimeSlotName,
    Room,
    MAX(CASE WHEN DayOfWeek = 1 THEN CellText END) AS Mon,
    MAX(CASE WHEN DayOfWeek = 2 THEN CellText END) AS Tue,
    MAX(CASE WHEN DayOfWeek = 3 THEN CellText END) AS Wed,
    MAX(CASE WHEN DayOfWeek = 4 THEN CellText END) AS Thu,
    MAX(CASE WHEN DayOfWeek = 5 THEN CellText END) AS Fri,
    MAX(CASE WHEN DayOfWeek = 6 THEN CellText END) AS Sat
FROM src
GROUP BY
    YearMonth,
    ClinDeptName,
    TimeSlotName,
    Room
ORDER BY
    ClinDeptName,
    TimeSlotName,
    Room;
