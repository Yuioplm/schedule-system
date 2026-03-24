import streamlit as st
import pandas as pd
from pathlib import Path
import sys

from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_app.sql_loader import load_sql

st.set_page_config(layout="wide")
st.title("帳票① 外来担当医表")

conn = get_conn()

col1, col2 = st.columns(2)
with col1:
    year = st.number_input("年", min_value=2020, max_value=2100, value=2026, step=1)
with col2:
    month = st.number_input("月", min_value=1, max_value=12, value=4, step=1)

target_month = f"{int(year)}-{int(month):02d}"

query = load_sql("Report1_pivot.sql")
df = pd.read_sql(query, conn, params={"target_month": target_month})

if df.empty:
    st.warning("対象月のデータがありません")
else:
    display_df = df.rename(columns={
        "ClinDeptName": "診療科",
        "TimeSlotName": "時間",
        "Room": "診察室",
        "Mon": "月",
        "Tue": "火",
        "Wed": "水",
        "Thu": "木",
        "Fri": "金",
        "Sat": "土",
    })

    st.dataframe(display_df, use_container_width=True)

    csv = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Excelダウンロード",
        data=csv,
        file_name=f"帳票①_外来担当医表_{target_month}.csv",
        mime="text/csv",
    )
