import streamlit as st
import pandas as pd

from scripts.settings import get_conn
from streamlit_app.sql_loader import load_sql

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

query = load_sql("ActualScheduleSearch_base.sql")
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
