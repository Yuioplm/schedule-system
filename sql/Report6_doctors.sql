-- ==========================
-- 帳票⑥ 非常勤医師一覧
-- ==========================
SELECT
    DoctorID,
    DoctorName
FROM M_Doctor
WHERE EmploymentType = '非常勤'
  AND COALESCE(ActiveFlag, 1) = 1
ORDER BY DoctorName, DoctorID;
