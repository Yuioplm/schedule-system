import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_app.sql_loader import load_sql

conn = get_conn()

st.title("帳票➄ 常勤・非常勤月別コマ数")

years = list(range(2025, 2028))
months = list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    year = st.selectbox("年", years, index=1)
with col2:
    month = st.selectbox("月", months, index=datetime.now().month - 1)

selected_ym = f"{year}-{month:02d}-01"
fiscal_year = year if month >= 4 else year - 1
start_date = f"{fiscal_year}-04-01"
end_date = pd.to_datetime(selected_ym) + pd.offsets.MonthEnd(1)
end_date = end_date.strftime("%Y-%m-%d")

query = load_sql("Report5.sql")
df = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})

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

    st.dataframe(pivot, use_container_width=True)

    csv = pivot.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票➄_{year}_{month:02d}.csv",
        mime="text/csv",
    )
else:
    st.warning("データがありません")
