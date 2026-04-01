import streamlit as st
import pandas as pd
from pathlib import Path
import sys

from scripts.settings import get_conn

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_app.sql_loader import load_sql

st.set_page_config(layout="wide")
st.title("帳票➁ 予定変更一覧")

conn = get_conn()

start_date = st.date_input("検索開始日を選んでください")

query = load_sql("Report2.sql")
df = pd.read_sql(query, conn, params={"start_date": str(start_date)})

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
