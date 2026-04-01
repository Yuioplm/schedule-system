import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("反映後予定検索")
conn = get_conn()

st.caption("V_ScheduleActual をもとに、予定変更・臨時外来を反映済みの一覧を検索します。")

# 候補データ
dept_df = pd.read_sql(
    """
    SELECT ClinDeptID, ClinDeptName
    FROM M_ClinicalDepartment
    WHERE ActiveFlag = 1
    ORDER BY ClinDeptID
    """,
    conn,
)

doctor_df = pd.read_sql(
    """
    SELECT DoctorID, DoctorName
    FROM M_Doctor
    WHERE ActiveFlag = 1
    ORDER BY DoctorID
    """,
    conn,
)

timeslot_df = pd.read_sql(
    """
    SELECT TimeSlotID, TimeSlotName
    FROM M_TimeSlot
    ORDER BY TimeSlotID
    """,
    conn,
)

col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("開始日")
with col2:
    date_to = st.date_input("終了日")

col3, col4, col5 = st.columns(3)
with col3:
    dept_options = [None] + dept_df["ClinDeptID"].astype(int).tolist()
    selected_dept = st.selectbox(
        "診療科",
        dept_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {dept_df.loc[dept_df['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
    )
with col4:
    doctor_options = [None] + doctor_df["DoctorID"].astype(int).tolist()
    selected_doctor = st.selectbox(
        "医師",
        doctor_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {doctor_df.loc[doctor_df['DoctorID'] == x, 'DoctorName'].iloc[0]}",
    )
with col5:
    timeslot_options = [None] + timeslot_df["TimeSlotID"].astype(int).tolist()
    selected_timeslot = st.selectbox(
        "時間帯",
        timeslot_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {timeslot_df.loc[timeslot_df['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
    )

query = """
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
"""
params = [str(date_from), str(date_to)]

if selected_dept is not None:
    query += " AND sa.Rpt1ClinDeptID = ?"
    params.append(int(selected_dept))
if selected_doctor is not None:
    query += " AND sa.DoctorID = ?"
    params.append(int(selected_doctor))
if selected_timeslot is not None:
    query += " AND sa.TimeSlotID = ?"
    params.append(int(selected_timeslot))

query += " ORDER BY sa.CalendarDate, sa.TimeSlotID, sa.Rpt1ClinDeptID, sa.SlotID"

result_df = pd.read_sql(query, conn, params=params)

st.subheader("検索結果")
if result_df.empty:
    st.info("該当データがありません")
else:
    st.dataframe(result_df, use_container_width=True)
    csv = result_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="CSVダウンロード",
        data=csv,
        file_name="反映後予定検索.csv",
        mime="text/csv",
    )
