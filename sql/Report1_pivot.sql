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
    WHERE d.YearMonth = :target_month
      AND d.DayOfWeek BETWEEN 1 AND 6
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
        COALESCE(cs.Room, '') AS Room,
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
        COALESCE(cd.Category, '') AS CenterCategory,
        cd.ClinDeptName,
        ts.TimeSlotName,
        s.TimeSlotID,
        s.Room,
        s.DayOfWeek,
        COALESCE(cd.Rpt1Sort, 9999) AS DeptSort,
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
        COALESCE(NULLIF(s.Rpt1DisplayDoctorName, ''), d.DoctorName, '―') AS DoctorName,
        CASE
            WHEN s.SourceWeekPattern = '12345' THEN 0
            ELSE CAST(SUBSTR(s.ActiveWeekPattern, 1, 1) AS INTEGER)
        END AS TokenSortKey,
        CASE
            WHEN d.EmploymentType = '常勤' THEN 0
            WHEN d.EmploymentType = '非常勤' THEN 1
            ELSE 2
        END AS EmploymentSortKey,
        COALESCE(s.DoctorID, 999999) AS DoctorSortID
    FROM slot_week_pattern s
    LEFT JOIN M_ClinicalDepartment cd
      ON cd.ClinDeptID = s.Rpt1ClinDeptID
    LEFT JOIN M_TimeSlot ts
      ON ts.TimeSlotID = s.TimeSlotID
    LEFT JOIN M_Doctor d
      ON d.DoctorID = s.DoctorID
    WHERE cd.Rpt1Flag IN ('1', 1)
),
cell_tokens_distinct AS (
    SELECT DISTINCT
        YearMonth,
        CenterCategory,
        ClinDeptName,
        TimeSlotName,
        TimeSlotID,
        Room,
        DayOfWeek,
        DeptSort,
        CASE
            WHEN WeekLabel = '' THEN DoctorName
            ELSE WeekLabel || ' ' || DoctorName
        END AS TokenText,
        TokenSortKey,
        EmploymentSortKey,
        DoctorSortID
    FROM cell_tokens
),
cell_keys AS (
    SELECT DISTINCT
        YearMonth,
        CenterCategory,
        ClinDeptName,
        TimeSlotName,
        TimeSlotID,
        Room,
        DayOfWeek,
        DeptSort
    FROM cell_tokens_distinct
),
src AS (
    SELECT
        k.YearMonth,
        k.CenterCategory,
        k.ClinDeptName,
        k.TimeSlotName,
        k.TimeSlotID,
        k.Room,
        k.DayOfWeek,
        k.DeptSort,
        (
            SELECT GROUP_CONCAT(ordered.TokenText, CHAR(10))
            FROM (
                SELECT t.TokenText
                FROM cell_tokens_distinct t
                WHERE t.YearMonth = k.YearMonth
                  AND t.CenterCategory = k.CenterCategory
                  AND t.ClinDeptName = k.ClinDeptName
                  AND t.TimeSlotName = k.TimeSlotName
                  AND t.TimeSlotID = k.TimeSlotID
                  AND t.Room = k.Room
                  AND t.DayOfWeek = k.DayOfWeek
                ORDER BY t.TokenSortKey, t.EmploymentSortKey, t.DoctorSortID, t.TokenText
            ) ordered
        ) AS CellText
    FROM cell_keys k
)
SELECT
    CenterCategory AS "センター",
    ClinDeptName AS "診療科",
    TimeSlotName AS "時間",
    Room AS "診察室",
    MAX(CASE WHEN DayOfWeek = 1 THEN CellText END) AS "月",
    MAX(CASE WHEN DayOfWeek = 2 THEN CellText END) AS "火",
    MAX(CASE WHEN DayOfWeek = 3 THEN CellText END) AS "水",
    MAX(CASE WHEN DayOfWeek = 4 THEN CellText END) AS "木",
    MAX(CASE WHEN DayOfWeek = 5 THEN CellText END) AS "金",
    MAX(CASE WHEN DayOfWeek = 6 THEN CellText END) AS "土"
FROM src
GROUP BY
    CenterCategory,
    ClinDeptName,
    TimeSlotName,
    TimeSlotID,
    Room,
    DeptSort
ORDER BY
    DeptSort,
    ClinDeptName,
    TimeSlotID,
    Room;
