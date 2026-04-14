WITH LatestOutputHistory AS (
    SELECT
        h.TargetType,
        h.TargetID,
        h.OutputBy,
        h.OutputDate
    FROM T_ChangeNoticeOutputHistory h
    INNER JOIN (
        SELECT
            TargetType,
            TargetID,
            MAX(OutputHistoryID) AS MaxHistoryID
        FROM T_ChangeNoticeOutputHistory
        GROUP BY TargetType, TargetID
    ) latest
        ON h.OutputHistoryID = latest.MaxHistoryID
),
NormalChange AS (
    SELECT
        '通常枠変更' AS 登録種別,
        sc.ChangeID AS レコードID,
        sc.CalendarDate AS 日付,
        sb.SlotID AS SlotID,
        ts.TimeSlotName AS 時間帯,
        cd.ClinDeptName AS 診療科,
        COALESCE(d_after.DoctorName, d_before.DoctorName) AS 医師,
        sct.ChangeTypeName AS 変更種別,
        sc.ChangeDetail AS 変更内容,
        sc.Reason AS 備考,
        CASE COALESCE(CAST(sc.Rpt2Flag AS INTEGER), 1)
            WHEN 1 THEN '表示'
            ELSE '非表示'
        END AS 帳票②表示,
        sc.ActiveFlag AS ActiveFlag,
        sc.ChangedBy AS 登録者,
        sc.CreatedAt AS 登録日時,
        sc.ChangeTypeID AS 変更種別ID,
        sc.NewDoctorID AS 医師ID,
        sc.NewTimeSlotID AS 時間帯ID,
        sc.CalendarDate AS 編集日付,
        NULL AS 診療科ID,
        sb.Room AS 部屋,
        sb.Rpt1DisplayDoctorName AS 帳票➁変更前
    FROM T_ScheduleChange sc
    LEFT JOIN V_ScheduleBase sb
        ON sc.CalendarDate = sb.CalendarDate
        AND sc.SlotID = sb.SlotID
    LEFT JOIN M_TimeSlot ts
        ON COALESCE(sc.NewTimeSlotID, sb.TimeSlotID) = ts.TimeSlotID
    LEFT JOIN M_ClinicalDepartment cd
        ON sb.Rpt1ClinDeptID = cd.ClinDeptID
    LEFT JOIN M_Doctor d_before
        ON sb.DoctorID = d_before.DoctorID
    LEFT JOIN M_Doctor d_after
        ON sc.NewDoctorID = d_after.DoctorID
    LEFT JOIN M_ScheduleChangeType sct
        ON sc.ChangeTypeID = sct.ChangeTypeID
    WHERE sc.CalendarDate BETWEEN ? AND ?
),
TemporaryChange AS (
    SELECT
        '臨時外来登録' AS 登録種別,
        tsch.TempID AS レコードID,
        tsch.CalendarDate AS 日付,
        NULL AS SlotID,
        mts.TimeSlotName AS 時間帯,
        cd.ClinDeptName AS 診療科,
        d.DoctorName AS 医師,
        '臨時外来' AS 変更種別,
        tsch.ChangeDetail AS 変更内容,
        tsch.Reason AS 備考,
        CASE COALESCE(CAST(tsch.Rpt2Flag AS INTEGER), 1)
            WHEN 1 THEN '表示'
            ELSE '非表示'
        END AS 帳票②表示,
        tsch.ActiveFlag AS ActiveFlag,
        NULL AS 登録者,
        tsch.CreatedAt AS 登録日時,
        NULL AS 変更種別ID,
        tsch.DoctorID AS 医師ID,
        tsch.TimeSlotID AS 時間帯ID,
        tsch.CalendarDate AS 編集日付,
        tsch.Rpt1ClinDeptID AS 診療科ID,
        tsch.Room AS 部屋,
        tsch.Rpt1DisplayDoctorName AS 帳票➁変更前
    FROM T_TemporarySchedule tsch
    LEFT JOIN M_TimeSlot mts
        ON tsch.TimeSlotID = mts.TimeSlotID
    LEFT JOIN M_ClinicalDepartment cd
        ON tsch.Rpt1ClinDeptID = cd.ClinDeptID
    LEFT JOIN M_Doctor d
        ON tsch.DoctorID = d.DoctorID
    WHERE tsch.CalendarDate BETWEEN ? AND ?
)
SELECT
    src.*,
    oh.OutputBy AS 変更届出力者,
    oh.OutputDate AS 変更届出力日
FROM (
    SELECT * FROM NormalChange
    UNION ALL
    SELECT * FROM TemporaryChange
 ) src
LEFT JOIN LatestOutputHistory oh
    ON src.登録種別 = oh.TargetType
    AND src.レコードID = oh.TargetID
WHERE (? = 1 OR src.ActiveFlag = 1)
ORDER BY 日付 ASC, COALESCE(時間帯ID, SlotID, 9999) ASC, 登録種別, レコードID DESC
