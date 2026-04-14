SELECT
    sa.CalendarDate AS 日付,
    CASE strftime('%w', sa.CalendarDate)
        WHEN '0' THEN '日'
        WHEN '1' THEN '月'
        WHEN '2' THEN '火'
        WHEN '3' THEN '水'
        WHEN '4' THEN '木'
        WHEN '5' THEN '金'
        WHEN '6' THEN '土'
    END AS 曜日,
    ts.TimeSlotName AS 時間帯,
    cd.ClinDeptName AS 診療科,
    sp.SpecialtyName AS 専門,
    sa.Room AS 診察室,
    d.DoctorName AS 医師,
    sa.Rpt1DisplayDoctorName AS 帳票表示名,
    sa.ChangeDetail AS 変更内容,
    sa.Reason AS 備考,
    CASE WHEN sa.SlotID IS NULL THEN '臨時外来' ELSE '通常枠' END AS 種別,
    sa.SlotID AS SlotID
FROM V_ScheduleActual sa
LEFT JOIN M_TimeSlot ts ON sa.TimeSlotID = ts.TimeSlotID
LEFT JOIN M_ClinicalDepartment cd ON sa.Rpt1ClinDeptID = cd.ClinDeptID
LEFT JOIN M_Specialty sp ON sa.Rpt1SpecialtyID = sp.SpecialtyID
LEFT JOIN M_Doctor d ON sa.DoctorID = d.DoctorID
WHERE sa.CalendarDate BETWEEN ? AND ?
