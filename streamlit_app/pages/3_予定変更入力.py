import streamlit as st
import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.settings import get_conn

row = st.session_state.get("selected")

if row is None:
    st.warning("対象枠が選択されていません")
    st.stop()

st.title("予定変更入力")

st.write("対象枠")

st.write("日付:",row["CalendarDate"])
st.write("SlotID:",row["SlotID"])
st.write("部屋:",row["Room"])
st.write("医師:",row["DoctorName"])

change_type = st.number_input("ChangeTypeID",step=1)

new_doctor = st.number_input("NewDoctorID",step=1)

new_room = st.text_input("NewRoom")

detail = st.text_area("ChangeDetail")

reason = st.text_area("Reason")

if st.button("登録"):

    conn = get_conn()

    conn.execute("""
    INSERT INTO T_ScheduleChange
    (CalendarDate,SlotID,ChangeTypeID,NewDoctorID,NewRoom,ChangeDetail,Reason)
    VALUES (?,?,?,?,?,?,?)
    """,
    (
    row["CalendarDate"],
    row["SlotID"],
    change_type,
    new_doctor,
    new_room,
    detail,
    reason
    )
    )

    conn.commit()

    st.success("変更登録しました")