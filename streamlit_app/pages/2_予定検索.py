import streamlit as st
import sqlite3
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.settings import get_conn

st.title("予定検索")

date_from = st.date_input("開始日")
date_to = st.date_input("終了日")

conn = get_conn()

query = f"""
SELECT *
FROM V_ScheduleFull
WHERE CalendarDate BETWEEN '{date_from}' AND '{date_to}'
LIMIT 200
"""

df = pd.read_sql(query, conn)

st.write("検索結果")

for i,row in df.iterrows():

    cols = st.columns([2,2,2,2,2,1])

    cols[0].write(row["CalendarDate"])
    cols[1].write(row["TimeSlotName"])
    cols[2].write(row["ClinDeptName"])
    cols[3].write(row["Room"])
    cols[4].write(row["DoctorName"])

    if cols[5].button("変更",key=i):

        st.session_state.selected = row
        st.switch_page("pages/3_予定変更入力.py")