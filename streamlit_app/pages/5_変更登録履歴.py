import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from scripts.settings import get_conn

st.title("変更登録履歴検索")
conn = get_conn()

st.caption("予定変更入力・臨時外来登録の入力内容を、非表示設定を含めて確認できます。")

col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("開始日")
with col2:
    date_to = st.date_input("終了日")

show_inactive = st.checkbox("無効化済み(ActiveFlag=0)も表示", value=False)

query = """
WITH NormalChange AS (
    SELECT
        '通常枠変更' AS 登録種別,
        sc.ChangeID AS レコードID,
        sc.CalendarDate AS 日付,
        sb.SlotID AS SlotID,
        ts.TimeSlotName AS 時間帯,
        cd.ClinDeptName AS 診療科,
        COALESCE(d_after.DoctorName, d_before.DoctorName) AS 医師,
        sct.ChangeTypeName AS 変更種別,
        sc.ChangeDetail AS 変更内容,
        sc.Reason AS 備考,
        CASE COALESCE(CAST(sc.Rpt2Flag AS INTEGER), 1)
            WHEN 1 THEN '表示'
            ELSE '非表示'
        END AS 帳票②表示,
        sc.ActiveFlag AS ActiveFlag,
        sc.ChangedBy AS 登録者,
        sc.CreatedAt AS 登録日時,
        sc.ChangeTypeID AS 変更種別ID,
        sc.NewDoctorID AS 医師ID,
        sc.NewTimeSlotID AS 時間帯ID,
        sc.CalendarDate AS 編集日付,
        NULL AS 診療科ID,
        sb.Room AS 部屋,
        sb.Rpt1DisplayDoctorName AS 帳票➁変更前
    FROM T_ScheduleChange sc
    LEFT JOIN V_ScheduleBase sb
        ON sc.CalendarDate = sb.CalendarDate
        AND sc.SlotID = sb.SlotID
    LEFT JOIN M_TimeSlot ts
        ON COALESCE(sc.NewTimeSlotID, sb.TimeSlotID) = ts.TimeSlotID
    LEFT JOIN M_ClinicalDepartment cd
        ON sb.Rpt1ClinDeptID = cd.ClinDeptID
    LEFT JOIN M_Doctor d_before
        ON sb.DoctorID = d_before.DoctorID
    LEFT JOIN M_Doctor d_after
        ON sc.NewDoctorID = d_after.DoctorID
    LEFT JOIN M_ScheduleChangeType sct
        ON sc.ChangeTypeID = sct.ChangeTypeID
    WHERE sc.CalendarDate BETWEEN ? AND ?
),
TemporaryChange AS (
    SELECT
        '臨時外来登録' AS 登録種別,
        tsch.TempID AS レコードID,
        tsch.CalendarDate AS 日付,
        NULL AS SlotID,
        mts.TimeSlotName AS 時間帯,
        cd.ClinDeptName AS 診療科,
        d.DoctorName AS 医師,
        '臨時外来' AS 変更種別,
        tsch.ChangeDetail AS 変更内容,
        tsch.Reason AS 備考,
        CASE COALESCE(CAST(tsch.Rpt2Flag AS INTEGER), 1)
            WHEN 1 THEN '表示'
            ELSE '非表示'
        END AS 帳票②表示,
        tsch.ActiveFlag AS ActiveFlag,
        NULL AS 登録者,
        tsch.CreatedAt AS 登録日時,
        NULL AS 変更種別ID,
        tsch.DoctorID AS 医師ID,
        tsch.TimeSlotID AS 時間帯ID,
        tsch.CalendarDate AS 編集日付,
        tsch.Rpt1ClinDeptID AS 診療科ID,
        tsch.Room AS 部屋,
        tsch.Rpt1DisplayDoctorName AS 帳票➁変更前
    FROM T_TemporarySchedule tsch
    LEFT JOIN M_TimeSlot mts
        ON tsch.TimeSlotID = mts.TimeSlotID
    LEFT JOIN M_ClinicalDepartment cd
        ON tsch.Rpt1ClinDeptID = cd.ClinDeptID
    LEFT JOIN M_Doctor d
        ON tsch.DoctorID = d.DoctorID
    WHERE tsch.CalendarDate BETWEEN ? AND ?
)
SELECT *
FROM (
    SELECT * FROM NormalChange
    UNION ALL
    SELECT * FROM TemporaryChange
)
WHERE (? = 1 OR ActiveFlag = 1)
ORDER BY 日付 DESC, 登録種別, レコードID DESC
"""

result_df = pd.read_sql(
    query,
    conn,
    params=[str(date_from), str(date_to), str(date_from), str(date_to), 1 if show_inactive else 0],
)

st.subheader("検索結果")
if result_df.empty:
    st.info("該当データがありません")
else:
    st.dataframe(result_df, use_container_width=True)
    csv = result_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="CSVダウンロード",
        data=csv,
        file_name="変更登録履歴.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("登録内容の編集")

    edit_df = result_df.copy()
    edit_df["選択表示"] = edit_df.apply(
        lambda r: f"{r['登録種別']} / {r['日付']} / ID:{int(r['レコードID'])} / {r['変更種別'] or '-'}",
        axis=1,
    )

    selected_label = st.selectbox("編集対象", edit_df["選択表示"].tolist())
    selected_row = edit_df.loc[edit_df["選択表示"] == selected_label].iloc[0]

    is_visible_report2 = selected_row["帳票②表示"] == "表示"
    is_normal_change = selected_row["登録種別"] == "通常枠変更"

    change_type_df = pd.read_sql(
        """
        SELECT ChangeTypeID, ChangeTypeName
        FROM M_ScheduleChangeType
        WHERE ActiveFlag = 1
        ORDER BY ChangeTypeID
        """,
        conn,
    )
    doctor_df = pd.read_sql(
        """
        SELECT DoctorID, DoctorName
        FROM M_Doctor
        WHERE ActiveFlag = 1
        ORDER BY DoctorID
        """,
        conn,
    )
    timeslot_df = pd.read_sql(
        """
        SELECT TimeSlotID, TimeSlotName
        FROM M_TimeSlot
        ORDER BY TimeSlotID
        """,
        conn,
    )
    clin_dept_df = pd.read_sql(
        """
        SELECT ClinDeptID, ClinDeptName
        FROM M_ClinicalDepartment
        WHERE ActiveFlag = 1
        ORDER BY ClinDeptID
        """,
        conn,
    )

    with st.form("history_edit_form"):
        if is_normal_change:
            current_change_type = selected_row["変更種別ID"]
            change_type_options = change_type_df["ChangeTypeID"].astype(int).tolist()
            change_type_index = 0
            if pd.notna(current_change_type) and int(current_change_type) in change_type_options:
                change_type_index = change_type_options.index(int(current_change_type))
            edit_change_type_id = st.selectbox(
                "変更種別",
                change_type_options,
                index=change_type_index,
                format_func=lambda x: f"{x}: {change_type_df.loc[change_type_df['ChangeTypeID'] == x, 'ChangeTypeName'].iloc[0]}",
            )

            current_doctor = selected_row["医師ID"]
            doctor_options = [None] + doctor_df["DoctorID"].astype(int).tolist()
            doctor_index = 0
            if pd.notna(current_doctor) and int(current_doctor) in doctor_options:
                doctor_index = doctor_options.index(int(current_doctor))
            edit_doctor_id = st.selectbox(
                "代診医（任意）",
                doctor_options,
                index=doctor_index,
                format_func=lambda x: "未設定" if x is None else f"{x}: {doctor_df.loc[doctor_df['DoctorID'] == x, 'DoctorName'].iloc[0]}",
            )
            edit_changed_by = st.text_input("ChangedBy", value=selected_row["登録者"] or "")
        else:
            edit_date = st.date_input("日付", value=pd.to_datetime(selected_row["編集日付"]).date())

            current_timeslot = int(selected_row["時間帯ID"]) if pd.notna(selected_row["時間帯ID"]) else None
            timeslot_options = timeslot_df["TimeSlotID"].astype(int).tolist()
            timeslot_index = 0
            if current_timeslot in timeslot_options:
                timeslot_index = timeslot_options.index(current_timeslot)
            edit_timeslot_id = st.selectbox(
                "時間帯",
                timeslot_options,
                index=timeslot_index,
                format_func=lambda x: f"{x}: {timeslot_df.loc[timeslot_df['TimeSlotID'] == x, 'TimeSlotName'].iloc[0]}",
            )

            current_dept = int(selected_row["診療科ID"]) if pd.notna(selected_row["診療科ID"]) else None
            dept_options = clin_dept_df["ClinDeptID"].astype(int).tolist()
            dept_index = 0
            if current_dept in dept_options:
                dept_index = dept_options.index(current_dept)
            edit_dept_id = st.selectbox(
                "診療科",
                dept_options,
                index=dept_index,
                format_func=lambda x: f"{x}: {clin_dept_df.loc[clin_dept_df['ClinDeptID'] == x, 'ClinDeptName'].iloc[0]}",
            )

            current_doctor = selected_row["医師ID"]
            doctor_options = [None] + doctor_df["DoctorID"].astype(int).tolist()
            doctor_index = 0
            if pd.notna(current_doctor) and int(current_doctor) in doctor_options:
                doctor_index = doctor_options.index(int(current_doctor))
            edit_doctor_id = st.selectbox(
                "担当医（任意）",
                doctor_options,
                index=doctor_index,
                format_func=lambda x: "未設定" if x is None else f"{x}: {doctor_df.loc[doctor_df['DoctorID'] == x, 'DoctorName'].iloc[0]}",
            )

            edit_room = st.text_input("診察室", value=selected_row["部屋"] or "")
            edit_rpt2_before_doctor = st.text_input("帳票➁変更前（任意）", value=selected_row["帳票➁変更前"] or "")

        edit_detail = st.text_area("変更内容", value=selected_row["変更内容"] or "")
        edit_reason = st.text_area("備考", value=selected_row["備考"] or "")
        edit_visible_report2 = st.checkbox("予定変更一覧に表示", value=is_visible_report2)
        edit_active = st.checkbox("有効", value=bool(selected_row["ActiveFlag"]))

        submitted_edit = st.form_submit_button("更新")

        if submitted_edit:
            if is_normal_change:
                conn.execute(
                    """
                    UPDATE T_ScheduleChange
                    SET
                        ChangeTypeID = ?,
                        NewDoctorID = ?,
                        ChangeDetail = ?,
                        Reason = ?,
                        ChangedBy = ?,
                        Rpt2Flag = ?,
                        ActiveFlag = ?
                    WHERE ChangeID = ?
                    """,
                    (
                        int(edit_change_type_id),
                        edit_doctor_id,
                        edit_detail if edit_detail != "" else None,
                        edit_reason if edit_reason != "" else None,
                        edit_changed_by if edit_changed_by != "" else None,
                        1 if edit_visible_report2 else 0,
                        1 if edit_active else 0,
                        int(selected_row["レコードID"]),
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE T_TemporarySchedule
                    SET
                        CalendarDate = ?,
                        TimeSlotID = ?,
                        Rpt1ClinDeptID = ?,
                        DoctorID = ?,
                        Room = ?,
                        Rpt1DisplayDoctorName = ?,
                        ChangeDetail = ?,
                        Reason = ?,
                        Rpt2Flag = ?,
                        ActiveFlag = ?
                    WHERE TempID = ?
                    """,
                    (
                        str(edit_date),
                        int(edit_timeslot_id),
                        int(edit_dept_id),
                        edit_doctor_id,
                        edit_room if edit_room != "" else None,
                        edit_rpt2_before_doctor if edit_rpt2_before_doctor != "" else None,
                        edit_detail if edit_detail != "" else None,
                        edit_reason if edit_reason != "" else None,
                        1 if edit_visible_report2 else 0,
                        1 if edit_active else 0,
                        int(selected_row["レコードID"]),
                    ),
                )

            conn.commit()
            st.success("登録内容を更新しました。再検索して最新状態を確認してください。")
