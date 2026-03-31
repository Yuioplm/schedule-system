import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("予定変更入力")
conn = get_conn()

row = st.session_state.get("selected")

tab1, tab2 = st.tabs(["通常枠の予定変更", "臨時外来登録"])

with tab1:
    if row is None:
        st.warning("対象枠が選択されていません（予定検索画面で枠を選択してください）")
    else:
        st.write("対象枠")
        st.write("日付:", row["CalendarDate"])
        st.write("SlotID:", row["SlotID"])
        st.write("部屋:", row["Room"])
        st.write("医師:", row["DoctorName"])
        st.write("診療科:", row["ClinDeptName"])
        st.write("時間:", row["TimeSlotName"])

        change_type_df = pd.read_sql(
            """
            SELECT ChangeTypeID, ChangeTypeName
            FROM M_ScheduleChangeType
            ORDER BY ChangeTypeID
            """,
            conn,
        )

        if change_type_df.empty:
            st.error("M_ScheduleChangeType にデータがありません")
            st.stop()

        change_type_name = st.selectbox(
            "変更種別",
            change_type_df["ChangeTypeName"].tolist(),
        )

        change_type_id = int(
            change_type_df.loc[
                change_type_df["ChangeTypeName"] == change_type_name,
                "ChangeTypeID",
            ].iloc[0]
        )

        doctor_df = pd.read_sql(
            """
            SELECT DoctorID, DoctorName, Department, EmploymentType
            FROM M_Doctor
            ORDER BY DoctorID
            """,
            conn,
        )

        dept_options = [""] + sorted([x for x in doctor_df["Department"].dropna().unique().tolist()])
        selected_department = st.selectbox("代診医検索_部署名", dept_options)

        emp_options = [""] + sorted([x for x in doctor_df["EmploymentType"].dropna().unique().tolist()])
        selected_employment = st.selectbox("代診医検索_勤務形態", emp_options)

        filtered_doctor_df = doctor_df.copy()
        if selected_department != "":
            filtered_doctor_df = filtered_doctor_df[filtered_doctor_df["Department"] == selected_department]
        if selected_employment != "":
            filtered_doctor_df = filtered_doctor_df[filtered_doctor_df["EmploymentType"] == selected_employment]

        doctor_id_options = [None] + filtered_doctor_df["DoctorID"].astype(int).tolist()
        selected_doctor_id = st.selectbox(
            "代診医",
            doctor_id_options,
            format_func=lambda x: "未選択" if x is None else f"{x}: {filtered_doctor_df.loc[filtered_doctor_df['DoctorID'] == x, 'DoctorName'].iloc[0]}",
        )

        new_doctor_id = selected_doctor_id

        new_timeslot_id = None
        new_room = None
        detail = st.text_area("変更内容", help="帳票➁ 予定変更一覧 に出力したい内容を入力してください")
        reason = st.text_area("備考")

        hide_from_report2 = st.checkbox(
            "予定変更一覧にて非表示",
            help="チェックすると帳票➁ 予定変更一覧に表示されません",
        )
        changed_by = st.text_input("ChangedBy")

        if st.button("変更登録"):
            rpt2_flag = 0 if hide_from_report2 else 1
            conn.execute(
                """
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
                    rpt2_flag,
                ),
            )
            conn.commit()
            st.success("変更を登録しました")

with tab2:
    st.caption("臨時外来（T_TemporarySchedule）を登録します")

    dept_df = pd.read_sql(
        "SELECT ClinDeptID, ClinDeptName FROM M_ClinicalDepartment WHERE ActiveFlag = 1 ORDER BY ClinDeptID",
        conn,
    )
    doctor_df = pd.read_sql(
        "SELECT DoctorID, DoctorName, Department, EmploymentType FROM M_Doctor WHERE ActiveFlag = 1 ORDER BY DoctorID",
        conn,
    )
    timeslot_df = pd.read_sql(
        "SELECT TimeSlotID, TimeSlotName FROM M_TimeSlot ORDER BY TimeSlotID",
        conn,
    )

    with st.form("temporary_outpatient_form"):
        cal_date = st.date_input("日付")

        temp_timeslot = st.selectbox(
            "時間帯",
            [None] + timeslot_df["TimeSlotID"].astype(int).tolist(),
            format_func=lambda x: "未選択" if x is None else f"{x}: {timeslot_df.loc[timeslot_df['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
        )

        temp_dept = st.selectbox(
            "診療科",
            [None] + dept_df["ClinDeptID"].astype(int).tolist(),
            format_func=lambda x: "未選択" if x is None else f"{x}: {dept_df.loc[dept_df['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
        )

        dep_options = ["(全て)"] + sorted([x for x in doctor_df["Department"].dropna().unique().tolist()])
        selected_dep = st.selectbox("医師検索_部署", dep_options)
        emp_options = ["(全て)"] + sorted([x for x in doctor_df["EmploymentType"].dropna().unique().tolist()])
        selected_emp = st.selectbox("医師検索_勤務形態", emp_options)

        temp_doctor_df = doctor_df.copy()
        if selected_dep != "(全て)":
            temp_doctor_df = temp_doctor_df[temp_doctor_df["Department"] == selected_dep]
        if selected_emp != "(全て)":
            temp_doctor_df = temp_doctor_df[temp_doctor_df["EmploymentType"] == selected_emp]

        doctor_ids = [None] + temp_doctor_df["DoctorID"].astype(int).tolist()
        temp_doctor_id = st.selectbox(
            "担当医（任意）",
            doctor_ids,
            format_func=lambda x: "未設定" if x is None else f"{x}: {temp_doctor_df.loc[temp_doctor_df['DoctorID'] == x, 'DoctorName'].iloc[0]}",
        )

        temp_display_name = st.text_input("帳票①表示名（任意）", value="")
        temp_room = st.text_input("診察室")
        temp_detail = st.text_area("変更内容")
        temp_reason = st.text_area("備考")
        temp_active = st.checkbox("有効", value=True)

        submitted_temp = st.form_submit_button("臨時外来を登録")
        if submitted_temp:
            if temp_timeslot is None or temp_dept is None:
                st.error("時間帯・診療科は必須です。未選択を解除してください。")
            else:
                conn.execute(
                    """
                    INSERT INTO T_TemporarySchedule
                    (
                        CalendarDate,
                        TimeSlotID,
                        Rpt1ClinDeptID,
                        Rpt1DisplayDoctorName,
                        DoctorID,
                        Room,
                        ChangeDetail,
                        Reason,
                        ActiveFlag
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(cal_date),
                        int(temp_timeslot),
                        int(temp_dept),
                        temp_display_name if temp_display_name != "" else None,
                        temp_doctor_id,
                        temp_room if temp_room != "" else None,
                        temp_detail if temp_detail != "" else None,
                        temp_reason if temp_reason != "" else None,
                        1 if temp_active else 0,
                    ),
                )
                conn.commit()
                st.success("臨時外来を登録しました")
