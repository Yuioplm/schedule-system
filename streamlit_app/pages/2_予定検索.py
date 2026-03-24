import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("予定検索")

conn = get_conn()

# ==========================
# 検索条件用の候補取得
# ==========================
dept_df = pd.read_sql("""
SELECT DISTINCT ClinDeptName
FROM V_ScheduleFull
WHERE ClinDeptName IS NOT NULL
ORDER BY ClinDeptName
""", conn)

doctor_df = pd.read_sql("""
SELECT DISTINCT DoctorName
FROM V_ScheduleFull
WHERE DoctorName IS NOT NULL
ORDER BY DoctorName
""", conn)

dept_options = [""] + dept_df["ClinDeptName"].tolist()
doctor_options = [""] + doctor_df["DoctorName"].tolist()

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
    selected_dept = st.selectbox("診療科名", dept_options)
with col4:
    selected_doctor = st.selectbox("医師名", doctor_options)

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

if selected_dept != "":
    query += " AND ClinDeptName = ?"
    params.append(selected_dept)

if selected_doctor != "":
    query += " AND DoctorName = ?"
    params.append(selected_doctor)

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