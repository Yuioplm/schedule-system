PRAGMA foreign_keys = ON;

-- ==========================
-- 診療科名マスタ
-- ==========================
CREATE TABLE M_ClinicalDepartment (
    ClinDeptID INTEGER PRIMARY KEY,
    Category TEXT,
    ClinDeptName TEXT NOT NULL,
    Rpt1Sort INTEGER,
    Rpt1Flag TEXT,
    Rpt2Flag TEXT,
    Rpt3Flag TEXT,
    Rpt4Flag TEXT,
    Rpt5Flag TEXT,
    Rpt6Flag TEXT,
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 専門マスタ
-- ==========================
CREATE TABLE M_Specialty (
    SpecialtyID INTEGER PRIMARY KEY,
    SpecialtyName TEXT,
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 診療科名（帳票用代替名）
-- ==========================
CREATE TABLE M_ReportClinicalDepartment (
    RptClinDeptID INTEGER PRIMARY KEY,
    RptClinDeptName TEXT,
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 医師マスタ
-- ==========================
CREATE TABLE M_Doctor (
    DoctorID INTEGER PRIMARY KEY,
    DoctorName TEXT NOT NULL,
    Department TEXT,
    EmploymentType TEXT,
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
    IsCancel INTEGER DEFAULT 0,
    ActiveFlag INTEGER DEFAULT 1
);

-- ==========================
-- 診療枠テンプレート
-- ==========================
CREATE TABLE T_ConsultationSlot (
    SlotID INTEGER PRIMARY KEY,
    Rpt1ClinDeptID INTEGER,
    Rpt1SpecialtyID INTEGER,
    Rpt1DisplayDoctorName TEXT,
    Rpt2ClinDeptID INTEGER,
    Rpt3ClinDeptID INTEGER,
    Rpt4ClinDeptID INTEGER,
    Rpt5ClinDeptID INTEGER,
    Rpt6ClinDeptID INTEGER,
    DoctorID INTEGER,
    TimeSlotID INTEGER,
    Room TEXT,
    DayOfWeek INTEGER,
    WeekPattern TEXT,
    StartDate DATE,
    EndDate DATE,
    ActiveFlag INTEGER DEFAULT 1,

    FOREIGN KEY (Rpt1ClinDeptID)
        REFERENCES M_ClinicalDepartment(ClinDeptID),

    FOREIGN KEY (Rpt1SpecialtyID)
        REFERENCES M_Specialty(SpecialtyID),

    FOREIGN KEY (Rpt2ClinDeptID)
        REFERENCES M_ReportClinicalDepartment(RptClinDeptID),

    FOREIGN KEY (Rpt3ClinDeptID)
        REFERENCES M_ReportClinicalDepartment(RptClinDeptID),

    FOREIGN KEY (Rpt4ClinDeptID)
        REFERENCES M_ReportClinicalDepartment(RptClinDeptID),

    FOREIGN KEY (Rpt5ClinDeptID)
        REFERENCES M_ReportClinicalDepartment(RptClinDeptID),

    FOREIGN KEY (Rpt6ClinDeptID)
        REFERENCES M_ReportClinicalDepartment(RptClinDeptID),

    FOREIGN KEY (DoctorID)
        REFERENCES M_Doctor(DoctorID),

    FOREIGN KEY (TimeSlotID)
        REFERENCES M_TimeSlot(TimeSlotID)
);

CREATE INDEX idx_slot_day
ON T_ConsultationSlot(DayOfWeek);

-- ==========================
-- スケジュール
-- ==========================
CREATE VIEW V_ScheduleBase AS

SELECT
    d.CalendarDate,
    d.DayOfWeek,
    d.WeekNumber,

    cs.SlotID,

    -- レポート用診療科（帳票ごとに使い分ける前提）
    cs.Rpt1ClinDeptID,
    cs.Rpt1SpecialtyID,
    cs.Rpt1DisplayDoctorName,

    cs.Rpt2ClinDeptID,
    cs.Rpt3ClinDeptID,
    cs.Rpt4ClinDeptID,
    cs.Rpt5ClinDeptID,
    cs.Rpt6ClinDeptID,

    cs.DoctorID,
    cs.TimeSlotID,
    cs.Room

FROM M_Date d

JOIN T_ConsultationSlot cs
    ON d.DayOfWeek = cs.DayOfWeek

LEFT JOIN M_Holiday h
    ON d.CalendarDate = h.HolidayDate

WHERE

    -- 有効期間
    d.CalendarDate BETWEEN cs.StartDate AND cs.EndDate

    -- WeekPattern（例：135）
    AND instr(cs.WeekPattern, CAST(d.WeekNumber AS TEXT)) > 0

    -- 有効フラグ
    AND cs.ActiveFlag = 1

    -- 祝日除外
    AND h.HolidayDate IS NULL

ORDER BY
    d.CalendarDate,
    cs.TimeSlotID,
    cs.Rpt1ClinDeptID;

-- ==========================
-- 予定確認用ビュー
-- ==========================
CREATE VIEW V_ScheduleFull AS

SELECT
    sb.CalendarDate,

    strftime('%w', sb.CalendarDate) AS DayOfWeekNumber,

    CASE strftime('%w', sb.CalendarDate)
        WHEN '0' THEN '日'
        WHEN '1' THEN '月'
        WHEN '2' THEN '火'
        WHEN '3' THEN '水'
        WHEN '4' THEN '木'
        WHEN '5' THEN '金'
        WHEN '6' THEN '土'
    END AS DayOfWeek,

    -- ★ 診療科（Rpt1ベース）
    cd.ClinDeptName,

    -- ★ 専門
    sp.SpecialtyName,

    -- ★ 時間帯
    ts.TimeSlotName,

    sb.Room,

    -- ★ 医師
    d.DoctorID,
    d.DoctorName,

    -- ★ 表示用医師名（帳票①用）
    sb.Rpt1DisplayDoctorName AS DisplayDoctorName,

    sb.SlotID

FROM V_ScheduleBase sb

LEFT JOIN M_Doctor d
    ON sb.DoctorID = d.DoctorID

-- ★ Rpt1ClinDeptIDを使用
LEFT JOIN M_ClinicalDepartment cd
    ON sb.Rpt1ClinDeptID = cd.ClinDeptID

LEFT JOIN M_TimeSlot ts
    ON sb.TimeSlotID = ts.TimeSlotID

-- ★ Rpt1SpecialtyIDを使用
LEFT JOIN M_Specialty sp
    ON sb.Rpt1SpecialtyID = sp.SpecialtyID

ORDER BY
    sb.CalendarDate,
    sb.TimeSlotID,
    sb.Rpt1ClinDeptID;

-- ==========================
-- 予定変更履歴
-- ==========================
CREATE TABLE T_ScheduleChange (

    ChangeID INTEGER PRIMARY KEY,

    -- 対象日
    CalendarDate DATE NOT NULL,

    -- 対象枠
    SlotID INTEGER NOT NULL,

    -- 変更種別
    ChangeTypeID INTEGER NOT NULL,

    -- 変更内容
    ChangeDetail TEXT,

    -- 変更後情報
    NewDoctorID INTEGER,
    NewTimeSlotID INTEGER,
    NewRoom TEXT,

    -- 理由
    Reason TEXT,

    -- 承認日
    ChangeAcceptedDate DATE,

    -- 変更者
    ChangedBy TEXT,

    -- 帳票②対象フラグ
    Rpt2Flag INTEGER DEFAULT 1,

    -- 有効フラグ（★追加）
    ActiveFlag INTEGER DEFAULT 1,

    -- 作成日時（★追加）
    CreatedAt DATETIME DEFAULT  (datetime('now', '+9 hours')),

    FOREIGN KEY (SlotID)
        REFERENCES T_ConsultationSlot(SlotID),

    FOREIGN KEY (ChangeTypeID)
        REFERENCES M_ScheduleChangeType(ChangeTypeID),

    FOREIGN KEY (NewDoctorID)
        REFERENCES M_Doctor(DoctorID),

    FOREIGN KEY (NewTimeSlotID)
        REFERENCES M_TimeSlot(TimeSlotID)
);

-- ==========================
-- 臨時外来
-- ==========================
CREATE TABLE T_TemporarySchedule (

    TempID INTEGER PRIMARY KEY,

    CalendarDate DATE NOT NULL,
    TimeSlotID INTEGER NOT NULL,

    -- ★ Rpt系（必須）
    Rpt1ClinDeptID INTEGER,
    Rpt1SpecialtyID INTEGER,
    Rpt1DisplayDoctorName TEXT,

    Rpt2ClinDeptID INTEGER,
    Rpt3ClinDeptID INTEGER,
    Rpt4ClinDeptID INTEGER,
    Rpt5ClinDeptID INTEGER,
    Rpt6ClinDeptID INTEGER,

    DoctorID INTEGER,
    Room TEXT,

    ChangeDetail TEXT,
    Reason TEXT,

    ActiveFlag INTEGER DEFAULT 1,
    Rpt2Flag INTEGER DEFAULT 1,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (TimeSlotID) REFERENCES M_TimeSlot(TimeSlotID),
    FOREIGN KEY (DoctorID) REFERENCES M_Doctor(DoctorID)
);

-- ==========================
-- 予定変更結果確認用ビュー
-- ==========================
CREATE VIEW V_ScheduleActual AS

-- ==========================
-- ① 通常枠 + 最新変更
-- ==========================
SELECT
    sb.CalendarDate,
    sb.SlotID,

    sb.Rpt1ClinDeptID,
    sb.Rpt1SpecialtyID,
    sb.Rpt1DisplayDoctorName,

    sb.Rpt2ClinDeptID,
    sb.Rpt3ClinDeptID,
    sb.Rpt4ClinDeptID,
    sb.Rpt5ClinDeptID,
    sb.Rpt6ClinDeptID,

    COALESCE(sc.NewDoctorID, sb.DoctorID) AS DoctorID,
    COALESCE(sc.NewTimeSlotID, sb.TimeSlotID) AS TimeSlotID,
    COALESCE(sc.NewRoom, sb.Room) AS Room,

    sc.ChangeTypeID,
    sc.ChangeDetail,
    sc.Reason

FROM V_ScheduleBase sb

LEFT JOIN T_ScheduleChange sc
    ON sb.CalendarDate = sc.CalendarDate
    AND sb.SlotID = sc.SlotID
    AND sc.ActiveFlag = 1
    AND sc.ChangeID = (
        SELECT MAX(sc2.ChangeID)
        FROM T_ScheduleChange sc2
        WHERE sc2.CalendarDate = sb.CalendarDate
          AND sc2.SlotID = sb.SlotID
          AND sc2.ActiveFlag = 1
    )

WHERE (
    sc.ChangeTypeID IS NULL
    OR sc.ChangeTypeID != 1
)

UNION ALL

-- ==========================
-- ② 臨時外来
-- ==========================
SELECT
    ts.CalendarDate,
    NULL AS SlotID,

    ts.Rpt1ClinDeptID,
    ts.Rpt1SpecialtyID,
    ts.Rpt1DisplayDoctorName,

    ts.Rpt2ClinDeptID,
    ts.Rpt3ClinDeptID,
    ts.Rpt4ClinDeptID,
    ts.Rpt5ClinDeptID,
    ts.Rpt6ClinDeptID,

    ts.DoctorID,
    ts.TimeSlotID,
    ts.Room,

    NULL AS ChangeTypeID,
    ts.ChangeDetail,
    ts.Reason

FROM T_TemporarySchedule ts

WHERE ts.ActiveFlag = 1
  AND COALESCE(CAST(ts.Rpt2Flag AS INTEGER), 1) = 1

ORDER BY
    CalendarDate,
    TimeSlotID,
    Rpt1ClinDeptID;
