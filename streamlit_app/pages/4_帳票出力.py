import streamlit as st
import sqlite3
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.settings import get_conn

st.title("帳票出力")

report = st.selectbox(
    "帳票選択",
    [
        "月次枠パターン",
        "予定変更一覧",
        "日次医師枠数"
    ]
)

conn = get_conn()

if report == "予定変更一覧":

    df = pd.read_sql("""
    SELECT *
    FROM T_ScheduleChange
    ORDER BY CalendarDate
    """, conn)

elif report == "日次医師枠数":

    df = pd.read_sql("""
    SELECT CalendarDate,DoctorID,COUNT(*) SlotCount
    FROM V_ScheduleActual
    GROUP BY CalendarDate,DoctorID
    """, conn)

else:

    df = pd.read_sql("""
    SELECT *
    FROM T_ConsultationSlot
    """, conn)

st.dataframe(df)

csv = df.to_csv(index=False)

st.download_button(
    "CSVダウンロード",
    csv,
    "report.csv"
)