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
CREATE TABLE T_Schedule (
    ScheduleID INTEGER PRIMARY KEY,
    CalendarDate DATE,
    SlotID INTEGER,
    DoctorID INTEGER,
    ClinDeptID INTEGER,
    TimeSlotID INTEGER,
    Room TEXT,

    UNIQUE(CalendarDate, TimeSlotID, Room),
    
    FOREIGN KEY (SlotID)
        REFERENCES T_ConsultationSlot(SlotID),

    FOREIGN KEY (DoctorID)
        REFERENCES M_Doctor(DoctorID),

    FOREIGN KEY (ClinDeptID)
        REFERENCES M_ClinicalDepartment(ClinDeptID),

    FOREIGN KEY (TimeSlotID)
        REFERENCES M_TimeSlot(TimeSlotID)
);

-- ==========================
-- 予定変更履歴
-- ==========================
CREATE TABLE T_ScheduleChange (
    ChangeID INTEGER PRIMARY KEY,
    ScheduleID INTEGER,
    ChangeTypeID INTEGER,
    ChangeDetail TEXT,
    NewDoctorID INTEGER,
    NewTimeSlotID INTEGER,
    NewRoom TEXT,
    Reason TEXT,
    ChangeAcceptedDate DATE,
    ChangedBy TEXT,
    ActiveFlag INTEGER DEFAULT 1,

    FOREIGN KEY (ScheduleID)
        REFERENCES T_Schedule(ScheduleID),

    FOREIGN KEY (ChangeTypeID)
        REFERENCES M_ScheduleChangeType(ChangeTypeID),

    FOREIGN KEY (NewDoctorID)
        REFERENCES M_Doctor(DoctorID),

    FOREIGN KEY (NewTimeSlotID)
        REFERENCES M_TimeSlot(TimeSlotID)
);

-- ==========================
-- 予定確認用ビュー
-- ==========================
CREATE VIEW V_ScheduleFull AS

SELECT
    s.ScheduleID,
    s.CalendarDate,

    strftime('%w', s.CalendarDate) AS DayOfWeekNumber,

    CASE strftime('%w', s.CalendarDate)
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

    s.Room,

    d.DoctorID,
    d.DoctorName,

    cs.DisplayDoctorName,

    s.SlotID

FROM T_Schedule s

LEFT JOIN T_ConsultationSlot cs
ON s.SlotID = cs.SlotID

LEFT JOIN M_Doctor d
ON s.DoctorID = d.DoctorID

LEFT JOIN M_ClinicalDepartment cd
ON s.ClinDeptID = cd.ClinDeptID

LEFT JOIN M_TimeSlot ts
ON s.TimeSlotID = ts.TimeSlotID

LEFT JOIN M_Specialty sp
ON cs.SpecialtyID = sp.SpecialtyID

ORDER BY
s.CalendarDate,
ts.TimeSlotID,
s.Room;

-- ==========================
-- 予定変更結果確認用ビュー
-- ==========================
CREATE VIEW V_ScheduleActual AS

SELECT

s.ScheduleID,
s.CalendarDate,

COALESCE(sc.NewDoctorID, s.DoctorID) AS DoctorID,

COALESCE(sc.NewTimeSlotID, s.TimeSlotID) AS TimeSlotID,

COALESCE(sc.NewRoom, s.Room) AS Room,

s.ClinDeptID,

COALESCE(mct.IsCancel, 0) AS IsCancel,

sc.ChangeTypeID,
sc.ChangeDetail,
sc.Reason,

s.SlotID

FROM T_Schedule s

LEFT JOIN T_ScheduleChange sc
ON s.ScheduleID = sc.ScheduleID

LEFT JOIN M_ScheduleChangeType mct
ON sc.ChangeTypeID = mct.ChangeTypeID

ORDER BY
s.CalendarDate,
TimeSlotID,
Room;

--------------------------------------------------
-- インデックス（検索高速化）
--------------------------------------------------

CREATE INDEX idx_schedule_date
ON T_Schedule(CalendarDate);

CREATE INDEX idx_schedule_doctor
ON T_Schedule(DoctorID);

CREATE INDEX idx_slot_day
ON T_ConsultationSlot(DayOfWeek);