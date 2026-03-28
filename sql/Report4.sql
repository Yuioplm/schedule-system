-- ==========================
-- 帳票➃
-- ==========================
SELECT
    sa.Rpt1ClinDeptID,
    sa.Rpt4ClinDeptID,

    -- 表示用診療科名
    CASE
        WHEN sa.Rpt4ClinDeptID IS NOT NULL THEN rcd.RptClinDeptName
        ELSE cd.ClinDeptName
    END AS ClinDeptName,
    sa.DoctorID,
    d.DoctorName,
    sa.CalendarDate,

    COUNT(*) AS Cnt

FROM V_ScheduleActual sa

LEFT JOIN M_Doctor d
    ON sa.DoctorID = d.DoctorID

LEFT JOIN M_ReportClinicalDepartment rcd
    ON sa.Rpt4ClinDeptID = rcd.RptClinDeptID

LEFT JOIN M_ClinicalDepartment cd
    ON sa.Rpt1ClinDeptID = cd.ClinDeptID

WHERE
    d.EmploymentType IN ('常勤')
    AND sa.CalendarDate BETWEEN :start_date AND :end_date
    AND (
        (sa.Rpt4ClinDeptID IS NOT NULL AND rcd.ActiveFlag = 1)
        OR
        (sa.Rpt4ClinDeptID IS NULL AND cd.Rpt4Flag = 1)
    )

GROUP BY
    sa.Rpt1ClinDeptID,
    sa.Rpt4ClinDeptID,
    sa.DoctorID,
    ClinDeptName,

    sa.CalendarDate

ORDER BY
    sa.Rpt1ClinDeptID,
    sa.Rpt4ClinDeptID,
    sa.DoctorID,
    sa.CalendarDate;