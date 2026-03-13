PRAGMA foreign_keys = ON;

-- ==========================
-- 担当枠マスタ
-- ==========================
CREATE TABLE M_ClinicalDepartment (
    ClinDeptID INTEGER PRIMARY KEY,
    Category TEXT,
    ClinDeptName TEXT NOT NULL,
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 担当枠内の専門マスタ
-- ==========================
CREATE TABLE M_Specialty (
    SpecialtyID INTEGER PRIMARY KEY,
    SpecialtyName TEXT,
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 医師マスタ
-- ==========================
CREATE TABLE M_Doctor (
    DoctorID INTEGER PRIMARY KEY,
    DoctorName TEXT NOT NULL,
    Department TEXT NOT NULL,
    EmploymentType TEXT NOT NULL,
    ActiveFlag INTEGER DEFAULT 1
);

--------------------------------------------------
-- 時間帯マスタ（午前・午後）
--------------------------------------------------
CREATE TABLE M_TimeSlot (
    TimeSlotID INTEGER PRIMARY KEY,
    TimeSlotName TEXT NOT NULL
);

-- ==========================
-- 日付マスタ
-- ==========================
CREATE TABLE M_Date (
    DateID INTEGER PRIMARY KEY,
    CalendarDate DATE UNIQUE,
    DayOfWeek INTEGER,
    WeekNumber INTEGER,
    YearMonth TEXT
);

-- ==========================
-- 祝日マスタ
-- ==========================
CREATE TABLE M_Holiday (
    HolidayID INTEGER PRIMARY KEY,
    HolidayDate DATE,
    HolidayName TEXT
);

-- ==========================
-- 予定変更区分マスタ
-- ==========================
CREATE TABLE M_ScheduleChangeType (
    ChangeTypeID INTEGER PRIMARY KEY,
    ChangeTypeName TEXT,
    IsCancel INTEGER DEFAULT 0;
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 診療枠テンプレート
-- ==========================
CREATE TABLE T_ConsultationSlot (
    SlotID INTEGER PRIMARY KEY,
    ClinDeptID INTEGER,
    SpecialtyID INTEGER,
    DoctorID INTEGER,
    DisplayDoctorName TEXT,
    TimeSlotID INTEGER,
    Room TEXT,
    DayOfWeek INTEGER,
    WeekPattern TEXT,
    StartDate DATE,
    EndDate DATE,
    ActiveFlag INTEGER DEFAULT 1,

    FOREIGN KEY (ClinDeptID)
        REFERENCES M_ClinicalDepartment(ClinDeptID),

    FOREIGN KEY (SpecialtyID)
        REFERENCES M_Specialty(SpecialtyID),

    FOREIGN KEY (DoctorID)
        REFERENCES M_Doctor(DoctorID),

    FOREIGN KEY (TimeSlotID)
        REFERENCES M_TimeSlot(TimeSlotID)
);

-- ==========================
-- スケジュール
-- ==========================
CREATE VIEW V_ScheduleBase AS

SELECT
    d.CalendarDate,
    cs.SlotID,
    cs.ClinDeptID,
    cs.DoctorID,
    cs.TimeSlotID,
    cs.Room,
    cs.DisplayDoctorName,
    cs.SpecialtyID

FROM M_Date d

JOIN T_ConsultationSlot cs
ON strftime('%w', d.CalendarDate) = cs.DayOfWeek

WHERE
    d.CalendarDate >= cs.StartDate
AND d.CalendarDate <= cs.EndDate

AND substr(
        cs.WeekPattern,
        ((CAST(strftime('%d', d.CalendarDate) AS INTEGER) - 1) / 7) + 1,
        1
    ) = '1'

ORDER BY
    d.CalendarDate,
    cs.TimeSlotID,
    cs.ClinDeptID;

-- ==========================
-- 予定確認用ビュー
-- ==========================
CREATE VIEW V_ScheduleFull AS

SELECT
    sb.CalendarDate,
    strftime('%w', sb.CalendarDate) AS DayOfWeekNumber,

    CASE strftime('%w', sb.CalendarDate)
        WHEN '0' THEN 'Sun'
        WHEN '1' THEN 'Mon'
        WHEN '2' THEN 'Tue'
        WHEN '3' THEN 'Wed'
        WHEN '4' THEN 'Thu'
        WHEN '5' THEN 'Fri'
        WHEN '6' THEN 'Sat'
    END AS DayOfWeek,

    cd.ClinDeptName,
    sp.SpecialtyName,
    ts.TimeSlotName,
    sb.Room,
    d.DoctorID,
    d.DoctorName,
    sb.DisplayDoctorName,
    sb.SlotID

FROM V_ScheduleBase sb

LEFT JOIN M_Doctor d
ON sb.DoctorID = d.DoctorID

LEFT JOIN M_ClinicalDepartment cd
ON sb.ClinDeptID = cd.ClinDeptID

LEFT JOIN M_TimeSlot ts
ON sb.TimeSlotID = ts.TimeSlotID

LEFT JOIN M_Specialty sp
ON sb.SpecialtyID = sp.SpecialtyID

ORDER BY
    sb.CalendarDate,
    sb.TimeSlotID,
    sb.ClinDeptID;

-- ==========================
-- 予定変更履歴
-- ==========================
CREATE TABLE T_ScheduleChange (

    ChangeID INTEGER PRIMARY KEY,
    CalendarDate DATE NOT NULL,
    SlotID INTEGER,
    ChangeTypeID INTEGER,
    ChangeDetail TEXT,
    NewDoctorID INTEGER,
    NewTimeSlotID INTEGER,
    NewRoom TEXT,
    Reason TEXT,
    ChangeAcceptedDate DATE,
    ChangedBy TEXT,

    FOREIGN KEY (SlotID)
        REFERENCES T_ConsultationSlot(SlotID),

    FOREIGN KEY (ChangeTypeID)
        REFERENCES M_ScheduleChangeType(ChangeTypeID),

    FOREIGN KEY (NewDoctorID)
        REFERENCES M_Doctor(DoctorID),

    FOREIGN KEY (NewTimeSlotID)
        REFERENCES M_TimeSlot(TimeSlotID)
);

CREATE UNIQUE INDEX idx_schedulechange_unique_slot
ON T_ScheduleChange (CalendarDate, SlotID)
WHERE SlotID IS NOT NULL;

CREATE INDEX idx_schedulechange_date
ON T_ScheduleChange (CalendarDate);

-- ==========================
-- 予定変更結果確認用ビュー
-- ==========================
CREATE VIEW V_ScheduleActual AS

-- 通常枠（変更反映）

SELECT
    sb.CalendarDate,
    sb.SlotID,
    sb.ClinDeptID,
    COALESCE(sc.NewDoctorID, sb.DoctorID) AS DoctorID,
    COALESCE(sc.NewTimeSlotID, sb.TimeSlotID) AS TimeSlotID,
    COALESCE(sc.NewRoom, sb.Room) AS Room,
    sb.DisplayDoctorName,
    sc.ChangeTypeID,
    sc.ChangeDetail,
    sc.Reason

FROM V_ScheduleBase sb

LEFT JOIN T_ScheduleChange sc
ON sb.CalendarDate = sc.CalendarDate
AND sb.SlotID = sc.SlotID

UNION ALL

-- 臨時外来（SlotIDが無い変更）
SELECT
    sc.CalendarDate,
    NULL AS SlotID,
    NULL AS ClinDeptID,
    sc.NewDoctorID AS DoctorID,
    sc.NewTimeSlotID AS TimeSlotID,
    sc.NewRoom AS Room,
    NULL AS DisplayDoctorName,
    sc.ChangeTypeID,
    sc.ChangeDetail,
    sc.Reason

FROM T_ScheduleChange sc

WHERE sc.SlotID IS NULL

ORDER BY
    sc.CalendarDate,
    TimeSlotID,
    ClinDeptID;

--------------------------------------------------
-- インデックス（検索高速化）
--------------------------------------------------

CREATE INDEX idx_schedule_date
ON T_Schedule(CalendarDate);

CREATE INDEX idx_schedule_doctor
ON T_Schedule(DoctorID);

CREATE INDEX idx_slot_day
ON T_ConsultationSlot(DayOfWeek);