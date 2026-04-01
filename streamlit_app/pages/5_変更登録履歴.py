import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("変更登録履歴検索")
conn = get_conn()

st.caption("予定変更入力・臨時外来登録の入力内容を、非表示設定を含めて確認できます。")

col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("開始日")
with col2:
    date_to = st.date_input("終了日")

show_inactive = st.checkbox("無効化済み(ActiveFlag=0)も表示", value=False)

query = """
WITH NormalChange AS (
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
        sc.CreatedAt AS 登録日時
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
        tsch.CreatedAt AS 登録日時
    FROM T_TemporarySchedule tsch
    LEFT JOIN M_TimeSlot mts
        ON tsch.TimeSlotID = mts.TimeSlotID
    LEFT JOIN M_ClinicalDepartment cd
        ON tsch.Rpt1ClinDeptID = cd.ClinDeptID
    LEFT JOIN M_Doctor d
        ON tsch.DoctorID = d.DoctorID
    WHERE tsch.CalendarDate BETWEEN ? AND ?
)
SELECT *
FROM (
    SELECT * FROM NormalChange
    UNION ALL
    SELECT * FROM TemporaryChange
)
WHERE (? = 1 OR ActiveFlag = 1)
ORDER BY 日付 DESC, 登録種別, レコードID DESC
"""

result_df = pd.read_sql(
    query,
    conn,
    params=[str(date_from), str(date_to), str(date_from), str(date_to), 1 if show_inactive else 0],
)

st.subheader("検索結果")
if result_df.empty:
    st.info("該当データがありません")
else:
    st.dataframe(result_df, use_container_width=True)
    csv = result_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="CSVダウンロード",
        data=csv,
        file_name="変更登録履歴.csv",
        mime="text/csv",
    )
