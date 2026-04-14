SELECT
    cs.SlotID,
    cs.Rpt1ClinDeptID,
    cd.ClinDeptName,
    cs.Rpt1SpecialtyID,
    sp.SpecialtyName,
    cs.Rpt2ClinDeptID,
    rcd2.RptClinDeptName AS Rpt2ClinDeptName,
    cs.Rpt3ClinDeptID,
    rcd3.RptClinDeptName AS Rpt3ClinDeptName,
    cs.Rpt4ClinDeptID,
    rcd4.RptClinDeptName AS Rpt4ClinDeptName,
    cs.Rpt5ClinDeptID,
    rcd5.RptClinDeptName AS Rpt5ClinDeptName,
    cs.Rpt6ClinDeptID,
    rcd6.RptClinDeptName AS Rpt6ClinDeptName,
    cs.DoctorID,
    d.DoctorName,
    cs.TimeSlotID,
    ts.TimeSlotName,
    cs.Room,
    cs.DayOfWeek,
    cs.WeekPattern,
    cs.StartDate,
    cs.EndDate,
    cs.Rpt1DisplayDoctorName,
    cs.ActiveFlag
FROM T_ConsultationSlot cs
LEFT JOIN M_ClinicalDepartment cd ON cd.ClinDeptID = cs.Rpt1ClinDeptID
LEFT JOIN M_Specialty sp ON sp.SpecialtyID = cs.Rpt1SpecialtyID
LEFT JOIN M_ReportClinicalDepartment rcd2 ON rcd2.RptClinDeptID = cs.Rpt2ClinDeptID
LEFT JOIN M_ReportClinicalDepartment rcd3 ON rcd3.RptClinDeptID = cs.Rpt3ClinDeptID
LEFT JOIN M_ReportClinicalDepartment rcd4 ON rcd4.RptClinDeptID = cs.Rpt4ClinDeptID
LEFT JOIN M_ReportClinicalDepartment rcd5 ON rcd5.RptClinDeptID = cs.Rpt5ClinDeptID
LEFT JOIN M_ReportClinicalDepartment rcd6 ON rcd6.RptClinDeptID = cs.Rpt6ClinDeptID
LEFT JOIN M_Doctor d ON d.DoctorID = cs.DoctorID
LEFT JOIN M_TimeSlot ts ON ts.TimeSlotID = cs.TimeSlotID
ORDER BY cs.SlotID DESC
LIMIT 500
