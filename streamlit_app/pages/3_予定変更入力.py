import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("予定変更入力")

row = st.session_state.get("selected")

if row is None:
    st.warning("対象枠が選択されていません")
    st.stop()

conn = get_conn()

st.write("対象枠")
st.write("日付:", row["CalendarDate"])
st.write("SlotID:", row["SlotID"])
st.write("部屋:", row["Room"])
st.write("医師:", row["DoctorName"])
st.write("診療科:", row["ClinDeptName"])
st.write("時間:", row["TimeSlotName"])

# ==========================
# 変更種別マスタ
# ==========================
change_type_df = pd.read_sql("""
SELECT ChangeTypeID, ChangeTypeName
FROM M_ScheduleChangeType
ORDER BY ChangeTypeID
""", conn)

if change_type_df.empty:
    st.error("M_ScheduleChangeType にデータがありません")
    st.stop()

change_type_name = st.selectbox(
    "変更種別",
    change_type_df["ChangeTypeName"].tolist()
)

change_type_id = int(
    change_type_df.loc[
        change_type_df["ChangeTypeName"] == change_type_name,
        "ChangeTypeID"
    ].iloc[0]
)

# ==========================
# 医師絞り込み用マスタ
# ==========================
doctor_df = pd.read_sql("""
SELECT DoctorID, DoctorName, Department, EmploymentType
FROM M_Doctor
ORDER BY Department, EmploymentType, DoctorName
""", conn)

# Department候補
dept_options = [""] + sorted(
    [x for x in doctor_df["Department"].dropna().unique().tolist()]
)

selected_department = st.selectbox(
    "代診医検索_部署名",
    dept_options
)

# EmploymentType候補
emp_options = [""] + sorted(
    [x for x in doctor_df["EmploymentType"].dropna().unique().tolist()]
)

selected_employment = st.selectbox(
    "代診医検索_勤務形態",
    emp_options
)

filtered_doctor_df = doctor_df.copy()

if selected_department != "":
    filtered_doctor_df = filtered_doctor_df[
        filtered_doctor_df["Department"] == selected_department
    ]

if selected_employment != "":
    filtered_doctor_df = filtered_doctor_df[
        filtered_doctor_df["EmploymentType"] == selected_employment
    ]

doctor_name_options = [""] + filtered_doctor_df["DoctorName"].tolist()

selected_doctor_name = st.selectbox(
    "代診医",
    doctor_name_options
)

if selected_doctor_name == "":
    new_doctor_id = None
else:
    new_doctor_id = int(
        filtered_doctor_df.loc[
            filtered_doctor_df["DoctorName"] == selected_doctor_name,
            "DoctorID"
        ].iloc[0]
    )

# ==========================
# 変更後時間帯
# ==========================
# timeslot_df = pd.read_sql("""
# SELECT TimeSlotID, TimeSlotName
# FROM M_TimeSlot
# ORDER BY TimeSlotID
# """, conn)

# timeslot_options = [""] + timeslot_df["TimeSlotName"].tolist()

# selected_timeslot_name = st.selectbox(
#     "変更後時間帯",
#     timeslot_options
# )

# if selected_timeslot_name == "":
#     new_timeslot_id = None
# else:
#     new_timeslot_id = int(
#         timeslot_df.loc[
#             timeslot_df["TimeSlotName"] == selected_timeslot_name,
#             "TimeSlotID"
#         ].iloc[0]
#     )
new_timeslot_id = None

# ==========================
# 部屋・詳細・理由
# ==========================
# new_room = st.text_input("変更後部屋")
new_room = None
detail = st.text_area(
    "変更内容",
    help="帳票➁ 予定変更一覧 に出力したい内容を入力してください"
    )
reason = st.text_area("備考")

# ==========================
# 帳票➁表示制御
# ==========================
hide_from_report2 = st.checkbox(
    "予定変更一覧にて非表示",
    help="チェックすると帳票➁ 予定変更一覧に表示されません"
    )

changed_by = st.text_input("ChangedBy")

if st.button("変更登録"):

    rpt2_flag = 0 if hide_from_report2 else 1

    conn.execute("""
    INSERT INTO T_ScheduleChange
    (
        CalendarDate,
        SlotID,
        ChangeTypeID,
        ChangeDetail,
        NewDoctorID,
        NewTimeSlotID,
        NewRoom,
        Reason,
        ChangedBy,
        Rpt2Flag
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        row["CalendarDate"],
        row["SlotID"],
        change_type_id,
        detail if detail != "" else None,
        new_doctor_id,
        new_timeslot_id,
        new_room if new_room != "" else None,
        reason if reason != "" else None,
        changed_by if changed_by != "" else None,
        rpt2_flag
    ))

    conn.commit()

    st.success("変更を登録しました")