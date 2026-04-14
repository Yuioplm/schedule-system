SELECT
    CalendarDate,
    DayOfWeek,
    ClinDeptName,
    SpecialtyName,
    TimeSlotName,
    Room,
    DoctorName,
    DisplayDoctorName,
    SlotID
FROM V_ScheduleFull
WHERE CalendarDate BETWEEN ? AND ?
