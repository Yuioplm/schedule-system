-- ==========================
-- 帳票⑥ 対象医師一覧
-- 選択月に「外来予定」または「実績」がある非常勤医師
-- ==========================
WITH part_time_doctor AS (
    SELECT
        DoctorID,
        DoctorName,
        Department
    FROM M_Doctor
    WHERE EmploymentType = '非常勤'
      AND COALESCE(ActiveFlag, 1) = 1
),
plan_doctor AS (
    SELECT DISTINCT
        sb.DoctorID
    FROM V_ScheduleBase sb
    JOIN part_time_doctor d
      ON sb.DoctorID = d.DoctorID
    WHERE sb.CalendarDate BETWEEN :start_date AND :end_date
),
actual_doctor AS (
    SELECT DISTINCT
        sa.DoctorID
    FROM V_ScheduleActual sa
    JOIN part_time_doctor d
      ON sa.DoctorID = d.DoctorID
    WHERE sa.CalendarDate BETWEEN :start_date AND :end_date
)
SELECT
    d.DoctorID,
    d.DoctorName,
    d.Department
FROM part_time_doctor d
LEFT JOIN plan_doctor p
  ON d.DoctorID = p.DoctorID
LEFT JOIN actual_doctor a
  ON d.DoctorID = a.DoctorID
WHERE p.DoctorID IS NOT NULL
   OR a.DoctorID IS NOT NULL
ORDER BY d.DoctorName, d.DoctorID;
