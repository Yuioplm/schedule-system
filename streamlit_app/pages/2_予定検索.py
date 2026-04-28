import streamlit as st
import pandas as pd
from time import perf_counter

from scripts.settings import get_conn
from streamlit_app.log_events import log_event, log_page_open
from streamlit_app.page_support import render_page_guide
from streamlit_app.sql_loader import load_sql

st.title("予定検索")
log_page_open("予定検索")
render_page_guide("予定検索")

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


def _sync_end_date_from_start(start_key: str, end_key: str) -> None:
    st.session_state[end_key] = st.session_state[start_key]


# ==========================
# 検索条件
# ==========================
if "schedule_search_date_from" not in st.session_state:
    st.session_state["schedule_search_date_from"] = pd.Timestamp.today().date()
if "schedule_search_date_to" not in st.session_state:
    st.session_state["schedule_search_date_to"] = st.session_state["schedule_search_date_from"]

col1, col2 = st.columns(2)

with col1:
    date_from = st.date_input(
        "開始日",
        key="schedule_search_date_from",
        on_change=_sync_end_date_from_start,
        args=("schedule_search_date_from", "schedule_search_date_to"),
    )
with col2:
    date_to = st.date_input("終了日", key="schedule_search_date_to")

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
query = load_sql("ScheduleSearch_base.sql")

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
request_id = log_event(
    "search_execute",
    "予定検索",
    date_from=str(date_from),
    date_to=str(date_to),
    has_dept_filter=selected_dept is not None,
    has_doctor_filter=selected_doctor is not None,
)
search_started_at = perf_counter()
try:
    df = pd.read_sql(query, conn, params=params)
except Exception as exc:
    log_event(
        "search_failed",
        "予定検索",
        request_id=request_id,
        error=type(exc).__name__,
    )
    raise

elapsed_ms = int((perf_counter() - search_started_at) * 1000)
log_event(
    "search_result",
    "予定検索",
    request_id=request_id,
    result_count=len(df),
    elapsed_ms=elapsed_ms,
)

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
