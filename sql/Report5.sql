-- ==========================
-- 帳票➄
-- ==========================
SELECT
    sa.Rpt1ClinDeptID,
    sa.Rpt5ClinDeptID,

    -- 表示用診療科名
    CASE
        WHEN sa.Rpt5ClinDeptID IS NOT NULL THEN rcd.RptClinDeptName
        ELSE cd.ClinDeptName
    END AS ClinDeptName,
    sa.DoctorID,
    d.DoctorName,
    d.EmploymentType,
    sa.CalendarDate,
    STRFTIME('%Y-%m', sa.CalendarDate) AS Year_month, 

    COUNT(*) AS Cnt

FROM V_ScheduleActual sa

LEFT JOIN M_Doctor d
    ON sa.DoctorID = d.DoctorID

LEFT JOIN M_ReportClinicalDepartment rcd
    ON sa.Rpt5ClinDeptID = rcd.RptClinDeptID

LEFT JOIN M_ClinicalDepartment cd
    ON sa.Rpt1ClinDeptID = cd.ClinDeptID

WHERE
    d.EmploymentType IN ('常勤', '非常勤')
    AND (
        (sa.Rpt5ClinDeptID IS NOT NULL AND rcd.ActiveFlag = 1)
        OR
        (sa.Rpt5ClinDeptID IS NULL AND cd.Rpt5Flag = 1)
    )

GROUP BY
    sa.Rpt1ClinDeptID,
    sa.Rpt5ClinDeptID,
    sa.DoctorID,
    ClinDeptName,

    Year_month

ORDER BY
    d.EmploymentType,
    sa.Rpt1ClinDeptID,
    sa.Rpt5ClinDeptID,
    sa.DoctorID,
    sa.CalendarDate;