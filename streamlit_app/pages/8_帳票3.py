import streamlit as st
import pandas as pd
from datetime import datetime
from time import perf_counter

from scripts import settings
from streamlit_app.log_events import log_event, log_page_open
from streamlit_app.page_support import render_page_guide
from streamlit_app.sql_loader import load_sql

conn = settings.get_conn()


def _resolve_available_years():
    get_years = getattr(settings, "get_available_years", None)
    if callable(get_years):
        return get_years()

    start_year = getattr(settings, "START_FISCAL_YEAR", datetime.now().year)
    end_year = getattr(settings, "END_FISCAL_YEAR", start_year + 5)
    return list(range(start_year, end_year + 2))

st.title("帳票➂ 外来数")
log_page_open("帳票➂ 外来数")
render_page_guide("帳票➂ 外来数")

years = _resolve_available_years()
months = list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    default_year = datetime.now().year if datetime.now().year in years else years[-1]
    year = st.selectbox("年", years, index=years.index(default_year))
with col2:
    month = st.selectbox("月", months, index=datetime.now().month - 1)

start_date = f"{year}-{month:02d}-01"
end_date = pd.to_datetime(start_date) + pd.offsets.MonthEnd(1)
end_date = end_date.strftime("%Y-%m-%d")

query = load_sql("Report3.sql")
request_id = log_event(
    "report_generate_start",
    "帳票➂ 外来数",
    report_id="report3",
    start_date=start_date,
    end_date=end_date,
)
report_started_at = perf_counter()
try:
    df = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
except Exception as exc:
    log_event(
        "report_generate_failed",
        "帳票➂ 外来数",
        request_id=request_id,
        report_id="report3",
        error=type(exc).__name__,
    )
    raise

# DBの日付表現ゆれ対策（文字列比較に依存しないための再フィルタ）
if not df.empty:
    df["CalendarDate"] = pd.to_datetime(df["CalendarDate"], errors="coerce")
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)
    df = df[(df["CalendarDate"] >= start_ts) & (df["CalendarDate"] <= end_ts)]
    df["CalendarDate"] = df["CalendarDate"].dt.strftime("%Y-%m-%d")

if not df.empty:
    df["Rpt3ClinDeptID"] = df["Rpt3ClinDeptID"].fillna(0)
    pivot = df.pivot_table(
        index=["Rpt1ClinDeptID", "Rpt3ClinDeptID", "ClinDeptName"],
        columns="CalendarDate",
        values="Cnt",
        aggfunc="sum",
        fill_value=0,
    )

    pivot = pivot.sort_index(axis=1)
    pivot["合計"] = pivot.sum(axis=1)
    pivot = pivot.sort_index(level=0).reset_index()
    pivot = pivot.rename(columns={"ClinDeptName": "診療科名"})
    pivot = pivot.drop(columns=["Rpt1ClinDeptID", "Rpt3ClinDeptID"])

    new_cols = []
    for col in pivot.columns:
        if isinstance(col, str) and col.startswith(str(year)):
            dt = pd.to_datetime(col)
            new_cols.append(f"{col}\n({dt.strftime('%a')})")
        else:
            new_cols.append(col)
    pivot.columns = new_cols

    total_row = {col: "" for col in pivot.columns}
    total_row["診療科名"] = "合計"
    numeric_cols = [col for col in pivot.columns if col != "診療科名"]
    for col in numeric_cols:
        total_row[col] = pivot[col].sum()
    pivot = pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)
    elapsed_ms = int((perf_counter() - report_started_at) * 1000)
    log_event(
        "report_generate_success",
        "帳票➂ 外来数",
        request_id=request_id,
        report_id="report3",
        result_count=len(pivot),
        elapsed_ms=elapsed_ms,
    )

    st.dataframe(pivot, use_container_width=True)

    csv = pivot.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票③_{year}_{month:02d}.csv",
        mime="text/csv",
    )
else:
    elapsed_ms = int((perf_counter() - report_started_at) * 1000)
    log_event(
        "report_generate_success",
        "帳票➂ 外来数",
        request_id=request_id,
        report_id="report3",
        result_count=0,
        elapsed_ms=elapsed_ms,
    )
    st.warning("データがありません")
