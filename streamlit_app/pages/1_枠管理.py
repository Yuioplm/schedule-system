import streamlit as st
import sqlite3
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.settings import get_conn

st.title("枠管理")

conn = get_conn()

df = pd.read_sql("SELECT * FROM T_ConsultationSlot LIMIT 100", conn)

st.dataframe(df)

st.subheader("新規枠追加")

doctor = st.number_input("DoctorID", step=1)
dept = st.number_input("ClinDeptID", step=1)
timeslot = st.number_input("TimeSlotID", step=1)

room = st.text_input("Room")

dow = st.selectbox(
    "曜日",
    ["0","1","2","3","4","5","6"]
)

weekpattern = st.text_input("WeekPattern","11111")

start = st.date_input("StartDate")
end = st.date_input("EndDate")

if st.button("登録"):

    conn.execute("""
    INSERT INTO T_ConsultationSlot
    (DoctorID,ClinDeptID,TimeSlotID,Room,DayOfWeek,WeekPattern,StartDate,EndDate)
    VALUES (?,?,?,?,?,?,?,?)
    """,
    (doctor,dept,timeslot,room,dow,weekpattern,start,end)
    )

    conn.commit()

    st.success("登録しました")