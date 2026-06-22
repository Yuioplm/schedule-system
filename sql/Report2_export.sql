-- ==========================
-- 帳票➁-担当医師変更一覧表（Excel出力・履歴比較用）
-- ==========================
WITH LatestChange AS (
    SELECT sc1.*
    FROM T_ScheduleChange sc1
    WHERE sc1.ActiveFlag = 1
      AND sc1.ChangeID = (
          SELECT MAX(sc2.ChangeID)
          FROM T_ScheduleChange sc2
          WHERE sc2.CalendarDate = sc1.CalendarDate
            AND sc2.SlotID = sc1.SlotID
            AND sc2.ActiveFlag = 1
      )
)

SELECT
    '通常変更' AS "登録種別",
    lc.ChangeID AS "レコードID",
    'change:' || lc.CalendarDate || ':' || lc.SlotID AS "差分キー",
    lc.CalendarDate AS "日付",

    CASE strftime('%w', lc.CalendarDate)
        WHEN '0' THEN '日'
        WHEN '1' THEN '月'
        WHEN '2' THEN '火'
        WHEN '3' THEN '水'
        WHEN '4' THEN '木'
        WHEN '5' THEN '金'
        WHEN '6' THEN '土'
    END AS "曜日",

    ts.TimeSlotName AS "時間",

    CASE
        WHEN sb.Rpt2ClinDeptID IS NOT NULL THEN rcd.RptClinDeptName
        ELSE cd.ClinDeptName
    END AS "診療科名",

    sb.Rpt1DisplayDoctorName AS "変更前医師",

    lc.ChangeDetail AS "変更内容",
    lc.Reason AS "備考"

FROM LatestChange lc

LEFT JOIN V_ScheduleBase sb
    ON lc.CalendarDate = sb.CalendarDate
    AND lc.SlotID = sb.SlotID

LEFT JOIN M_TimeSlot ts
    ON COALESCE(lc.NewTimeSlotID, sb.TimeSlotID) = ts.TimeSlotID

LEFT JOIN M_ReportClinicalDepartment rcd
    ON sb.Rpt2ClinDeptID = rcd.RptClinDeptID

LEFT JOIN M_ClinicalDepartment cd
    ON sb.Rpt1ClinDeptID = cd.ClinDeptID

WHERE
    COALESCE(CAST(lc.Rpt2Flag AS INTEGER), 1) = 1
    AND lc.CalendarDate >= :start_date
    AND (
        (sb.Rpt2ClinDeptID IS NOT NULL AND rcd.ActiveFlag = 1)
        OR
        (sb.Rpt2ClinDeptID IS NULL AND cd.Rpt2Flag = 1)
    )

UNION ALL

SELECT
    '臨時外来',
    tsch.TempID,
    'temporary:' || tsch.TempID,
    tsch.CalendarDate,

    CASE strftime('%w', tsch.CalendarDate)
        WHEN '0' THEN '日'
        WHEN '1' THEN '月'
        WHEN '2' THEN '火'
        WHEN '3' THEN '水'
        WHEN '4' THEN '木'
        WHEN '5' THEN '金'
        WHEN '6' THEN '土'
    END,

    mts.TimeSlotName,

    CASE
        WHEN tsch.Rpt2ClinDeptID IS NOT NULL THEN rcd.RptClinDeptName
        ELSE cd.ClinDeptName
    END,

    tsch.Rpt1DisplayDoctorName,

    tsch.ChangeDetail,
    tsch.Reason

FROM T_TemporarySchedule tsch

LEFT JOIN M_TimeSlot mts
    ON tsch.TimeSlotID = mts.TimeSlotID

LEFT JOIN M_ReportClinicalDepartment rcd
    ON tsch.Rpt2ClinDeptID = rcd.RptClinDeptID

LEFT JOIN M_ClinicalDepartment cd
    ON tsch.Rpt1ClinDeptID = cd.ClinDeptID

WHERE
    tsch.ActiveFlag = 1
    AND COALESCE(CAST(tsch.Rpt2Flag AS INTEGER), 1) = 1
    AND tsch.CalendarDate >= :start_date
    AND (
        (tsch.Rpt2ClinDeptID IS NOT NULL AND rcd.ActiveFlag = 1)
        OR
        (tsch.Rpt2ClinDeptID IS NULL AND cd.Rpt2Flag = 1)
    )

ORDER BY
    "日付",
    "時間",
    "診療科名";
