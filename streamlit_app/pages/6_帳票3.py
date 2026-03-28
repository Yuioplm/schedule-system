import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_app.sql_loader import load_sql

conn = get_conn()

st.title("帳票➂ 外来数")

years = list(range(2025, 2028))
months = list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    year = st.selectbox("年", years, index=1)
with col2:
    month = st.selectbox("月", months, index=datetime.now().month - 1)

start_date = f"{year}-{month:02d}-01"
end_date = pd.to_datetime(start_date) + pd.offsets.MonthEnd(1)
end_date = end_date.strftime("%Y-%m-%d")

query = load_sql("Report3.sql")
df = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})

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

    st.dataframe(pivot, use_container_width=True)

    csv = pivot.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票③_{year}_{month:02d}.csv",
        mime="text/csv",
    )
else:
    st.warning("データがありません")
