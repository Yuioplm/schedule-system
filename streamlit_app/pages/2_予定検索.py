import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("予定検索")

conn = get_conn()

# ==========================
# 検索条件用の候補取得（ID昇順）
# ==========================
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

dept_options = [None] + dept_df["ClinDeptID"].astype(int).tolist()
doctor_options = [None] + doctor_df["DoctorID"].astype(int).tolist()

# ==========================
# 検索条件
# ==========================
col1, col2 = st.columns(2)

with col1:
    date_from = st.date_input("開始日")
with col2:
    date_to = st.date_input("終了日")

col3, col4 = st.columns(2)

with col3:
    selected_dept = st.selectbox(
        "診療科名",
        dept_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {dept_df.loc[dept_df['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
    )
with col4:
    selected_doctor = st.selectbox(
        "医師名",
        doctor_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {doctor_df.loc[doctor_df['DoctorID'] == x, 'DoctorName'].iloc[0]}",
    )

# ==========================
# SQL組み立て
# ==========================
query = """
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
"""

params = [str(date_from), str(date_to)]

if selected_dept is not None:
    selected_dept_name = dept_df.loc[dept_df["ClinDeptID"] == selected_dept, "ClinDeptName"].iloc[0]
    query += " AND ClinDeptName = ?"
    params.append(selected_dept_name)

if selected_doctor is not None:
    selected_doctor_name = doctor_df.loc[doctor_df["DoctorID"] == selected_doctor, "DoctorName"].iloc[0]
    query += " AND DoctorName = ?"
    params.append(selected_doctor_name)

query += """
ORDER BY
    CalendarDate,
    TimeSlotName,
    ClinDeptName,
    DoctorName
"""

# ==========================
# 実行
# ==========================
df = pd.read_sql(query, conn, params=params)

st.subheader("検索結果")

if df.empty:
    st.info("該当データがありません")
else:
    for i, row in df.iterrows():
        cols = st.columns([2, 1, 2, 2, 1, 2, 2, 1])

        cols[0].write(row["CalendarDate"])
        cols[1].write(row["DayOfWeek"])
        cols[2].write(row["ClinDeptName"])
        cols[3].write(row["SpecialtyName"])
        cols[4].write(row["TimeSlotName"])
        cols[5].write(row["Room"])
        cols[6].write(row["DoctorName"])

        if cols[7].button("変更", key=f"change_{i}"):
            st.session_state.selected = row.to_dict()
            st.switch_page("pages/3_予定変更入力.py")
