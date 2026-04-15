import streamlit as st
import pandas as pd
from time import perf_counter

from scripts.settings import get_conn
from streamlit_app.log_events import log_event, log_page_open
from streamlit_app.sql_loader import load_sql

st.set_page_config(layout="wide")
st.title("帳票➁ 予定変更一覧")
log_page_open("帳票➁ 予定変更一覧")

conn = get_conn()

start_date = st.date_input("検索開始日を選んでください")

query = load_sql("Report2.sql")
request_id = log_event(
    "report_generate_start",
    "帳票➁ 予定変更一覧",
    report_id="report2",
    start_date=str(start_date),
)
report_started_at = perf_counter()
try:
    df = pd.read_sql(query, conn, params={"start_date": str(start_date)})
except Exception as exc:
    log_event(
        "report_generate_failed",
        "帳票➁ 予定変更一覧",
        request_id=request_id,
        report_id="report2",
        error=type(exc).__name__,
    )
    raise

elapsed_ms = int((perf_counter() - report_started_at) * 1000)
log_event(
    "report_generate_success",
    "帳票➁ 予定変更一覧",
    request_id=request_id,
    report_id="report2",
    result_count=len(df),
    elapsed_ms=elapsed_ms,
)

if df.empty:
    st.warning("データがありません")
else:
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name="帳票➁_予定変更一覧.csv",
        mime="text/csv",
    )
