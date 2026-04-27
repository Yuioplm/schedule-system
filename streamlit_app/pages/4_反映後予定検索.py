import streamlit as st
import pandas as pd
from time import perf_counter

from scripts.settings import get_conn
from streamlit_app.log_events import log_event, log_page_open
from streamlit_app.sql_loader import load_sql

st.title("反映後予定検索")
log_page_open("反映後予定検索")
conn = get_conn()

st.caption("V_ScheduleActual をもとに、予定変更・臨時外来を反映済みの一覧を検索します。")

COLUMN_LABEL_RENAMES = {
    "SlotID": "枠ID",
    "DoctorName": "医師名",
    "医師": "医師名",
    "WeekPattern": "週番号",
    "診療科": "診療科名",
    "専門": "帳票①用専門外来名",
    "専門外来名": "帳票①用専門外来名",
    "帳票表示名": "帳票①用医師表示名",
    "帳票①表示名（任意）": "帳票①用医師表示名",
}

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


def _sync_end_date_from_start(start_key: str, end_key: str) -> None:
    st.session_state[end_key] = st.session_state[start_key]


if "actual_schedule_search_date_from" not in st.session_state:
    st.session_state["actual_schedule_search_date_from"] = pd.Timestamp.today().date()
if "actual_schedule_search_date_to" not in st.session_state:
    st.session_state["actual_schedule_search_date_to"] = st.session_state["actual_schedule_search_date_from"]

col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input(
        "開始日",
        key="actual_schedule_search_date_from",
        on_change=_sync_end_date_from_start,
        args=("actual_schedule_search_date_from", "actual_schedule_search_date_to"),
    )
with col2:
    date_to = st.date_input("終了日", key="actual_schedule_search_date_to")

col3, col4, col5 = st.columns(3)
with col3:
    dept_options = [None] + dept_df["ClinDeptID"].astype(int).tolist()
    selected_dept = st.selectbox(
        "診療科名",
        dept_options,
        format_func=lambda x: "(全て)" if x is None else f"{x}: {dept_df.loc[dept_df['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
    )
with col4:
    doctor_options = [None] + doctor_df["DoctorID"].astype(int).tolist()
    selected_doctor = st.selectbox(
        "医師名",
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

request_id = log_event(
    "search_execute",
    "反映後予定検索",
    date_from=str(date_from),
    date_to=str(date_to),
    has_dept_filter=selected_dept is not None,
    has_doctor_filter=selected_doctor is not None,
    has_timeslot_filter=selected_timeslot is not None,
)
search_started_at = perf_counter()
try:
    result_df = pd.read_sql(query, conn, params=params)
except Exception as exc:
    log_event(
        "search_failed",
        "反映後予定検索",
        request_id=request_id,
        error=type(exc).__name__,
    )
    raise

elapsed_ms = int((perf_counter() - search_started_at) * 1000)
log_event(
    "search_result",
    "反映後予定検索",
    request_id=request_id,
    result_count=len(result_df),
    elapsed_ms=elapsed_ms,
)

st.subheader("検索結果")
if result_df.empty:
    st.info("該当データがありません")
else:
    display_df = result_df.rename(columns=COLUMN_LABEL_RENAMES)
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="CSVダウンロード",
        data=csv,
        file_name="反映後予定検索.csv",
        mime="text/csv",
    )
