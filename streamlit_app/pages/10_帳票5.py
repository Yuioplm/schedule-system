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

st.title("帳票➄ 常勤・非常勤月別コマ数")
log_page_open("帳票➄ 常勤・非常勤月別コマ数")
render_page_guide("帳票➄ 常勤・非常勤月別コマ数")

years = _resolve_available_years()
months = list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    default_year = datetime.now().year if datetime.now().year in years else years[-1]
    year = st.selectbox("年", years, index=years.index(default_year))
with col2:
    month = st.selectbox("月", months, index=datetime.now().month - 1)

selected_ym = f"{year}-{month:02d}-01"
fiscal_year = year if month >= 4 else year - 1
start_date = f"{fiscal_year}-04-01"
end_date = pd.to_datetime(selected_ym) + pd.offsets.MonthEnd(1)
end_date = end_date.strftime("%Y-%m-%d")

query = load_sql("Report5.sql")
request_id = log_event(
    "report_generate_start",
    "帳票➄ 常勤・非常勤月別コマ数",
    report_id="report5",
    start_date=start_date,
    end_date=end_date,
)
report_started_at = perf_counter()
try:
    df = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
except Exception as exc:
    log_event(
        "report_generate_failed",
        "帳票➄ 常勤・非常勤月別コマ数",
        request_id=request_id,
        report_id="report5",
        error=type(exc).__name__,
    )
    raise

if not df.empty:
    df["Rpt5ClinDeptID"] = df["Rpt5ClinDeptID"].fillna(0)
    pivot = df.pivot_table(
        index=["EmploymentType", "Rpt1ClinDeptID", "Rpt5ClinDeptID", "ClinDeptName", "DoctorID", "DoctorName"],
        columns="Year_month",
        values="Cnt",
        aggfunc="sum",
        fill_value=0,
    )

    pivot = pivot.sort_index(axis=1)
    pivot["合計"] = pivot.sum(axis=1)
    pivot = pivot.sort_index(level=0).reset_index()
    pivot = pivot.rename(columns={"ClinDeptName": "診療科名"})
    pivot = pivot.drop(columns=["Rpt1ClinDeptID", "Rpt5ClinDeptID", "DoctorID"])

    total_row = {col: "" for col in pivot.columns}
    if "EmploymentType" in pivot.columns:
        total_row["EmploymentType"] = "合計"
    if "診療科名" in pivot.columns:
        total_row["診療科名"] = ""
    if "DoctorName" in pivot.columns:
        total_row["DoctorName"] = ""
    numeric_cols = [col for col in pivot.columns if col not in ["EmploymentType", "診療科名", "DoctorName"]]
    for col in numeric_cols:
        total_row[col] = pivot[col].sum()
    pivot = pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)
    elapsed_ms = int((perf_counter() - report_started_at) * 1000)
    log_event(
        "report_generate_success",
        "帳票➄ 常勤・非常勤月別コマ数",
        request_id=request_id,
        report_id="report5",
        result_count=len(pivot),
        elapsed_ms=elapsed_ms,
    )

    st.dataframe(pivot, use_container_width=True)

    csv = pivot.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票➄_{year}_{month:02d}.csv",
        mime="text/csv",
    )
else:
    elapsed_ms = int((perf_counter() - report_started_at) * 1000)
    log_event(
        "report_generate_success",
        "帳票➄ 常勤・非常勤月別コマ数",
        request_id=request_id,
        report_id="report5",
        result_count=0,
        elapsed_ms=elapsed_ms,
    )
    st.warning("データがありません")
